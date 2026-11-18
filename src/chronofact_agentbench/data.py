
"""Dataset download, validation, preparation, and provenance manifests."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import pandas as pd

from .temporal import infer_granularity, parse_temporal_interval

DATASET_NAME = "Orange/TimeStress"
DATASET_REVISION = "f90d17c"
DATASET_URL = (
    "https://huggingface.co/datasets/Orange/TimeStress/resolve/"
    + DATASET_REVISION
    + "/train.parquet"
)
DATASET_SHA256 = (
    "93df1d4782f770b38d1eda00acb5aa9d97c9a863fd6921fecb6f310052ffa59a"
)

REQUIRED_COLUMNS = [
    "SubjectID",
    "SubjectLabel",
    "RelationID",
    "RelationLabel",
    "ObjectID",
    "ObjectLabel",
    "StartDate",
    "EndDate",
    "Time",
    "Status",
    "Statement",
]

STATUS_ALIASES = {
    "correct": "correct",
    "valid": "correct",
    "true": "correct",
    "incorrect": "incorrect",
    "invalid": "incorrect",
    "false": "incorrect",
    "transitional": "transitional",
    "partial": "transitional",
}

EXCLUDED_STATUSES = {"no context", "discarded"}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calculate SHA-256 without loading the entire file into memory."""
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def normalize_status(value: object) -> str:
    """Normalize supported benchmark labels; reject unknown values."""
    normalized = str(value).strip().lower()

    if normalized not in STATUS_ALIASES:
        raise ValueError(
            "Unknown TimeStress Status value: {!r}".format(value)
        )

    return STATUS_ALIASES[normalized]


def download_dataset(output_path: str, timeout: int = 90) -> Dict[str, object]:
    """Download the pinned TimeStress Parquet file and verify SHA-256."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    temporary = output.with_suffix(output.suffix + ".part")

    request = urllib.request.Request(
        DATASET_URL,
        headers={"User-Agent": "ChronoFact-AgentBench/0.1.0"},
    )

    digest = hashlib.sha256()

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            with temporary.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)

                    if not chunk:
                        break

                    handle.write(chunk)
                    digest.update(chunk)

        actual_sha256 = digest.hexdigest()

        if actual_sha256 != DATASET_SHA256:
            raise ValueError(
                "Dataset checksum mismatch: expected {}, received {}".format(
                    DATASET_SHA256, actual_sha256
                )
            )

        os.replace(str(temporary), str(output))

    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    manifest = {
        "dataset": DATASET_NAME,
        "revision": DATASET_REVISION,
        "source_url": DATASET_URL,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "file": str(output),
        "sha256": actual_sha256,
        "expected_sha256": DATASET_SHA256,
        "checksum_verified": True,
        "license": "CC BY-SA 4.0",
        "note": "The dataset is not redistributed in the project ZIP.",
    }

    manifest_path = output.with_suffix(
        output.suffix + ".manifest.json"
    )

    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    return manifest


def _parses(value: object) -> bool:
    """True when a date is in a supported form (years 0001-9999; BCE dates are not supported)."""
    try:
        parse_temporal_interval(str(value))
        return True
    except (ValueError, TypeError):
        return False


def _fact_id(frame: pd.DataFrame) -> pd.Series:
    """Construct a stable subject-relation-object group identifier."""
    return (
        frame["SubjectID"].astype(str)
        + "|"
        + frame["RelationID"].astype(str)
        + "|"
        + frame["ObjectID"].astype(str)
    )


def prepare_dataset(input_path: str, output_path: str) -> Dict[str, object]:
    """Prepare eligible TimeStress rows and record exclusions transparently."""

    source = Path(input_path)

    if not source.exists():
        raise FileNotFoundError(
            "Raw dataset not found: {}".format(source)
        )

    frame = pd.read_parquet(source)

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in frame.columns
    ]

    if missing:
        raise ValueError(
            "Dataset is missing required columns: {}".format(missing)
        )

    # Normalize source labels before filtering.
    normalized_status = (
        frame["Status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    # Retain only the three supported supervised target classes.
    eligible_mask = normalized_status.isin(STATUS_ALIASES)

    # Record excluded source labels and their counts.
    excluded_status_counts = {
        str(key): int(value)
        for key, value in (
            frame.loc[~eligible_mask, "Status"]
            .value_counts(dropna=False)
            .items()
        )
    }

    # Preserve original values and all eligible source columns.
    prepared = frame.loc[eligible_mask].copy()

    if prepared.empty:
        raise ValueError(
            "No eligible Correct, Incorrect, or Transitional records found."
        )

    # Python dates cannot hold years before 0001, so rows with BCE or otherwise unparseable
    # dates are excluded and counted.
    date_ok = (
        prepared["Time"].map(_parses)
        & prepared["StartDate"].map(_parses)
        & prepared["EndDate"].map(_parses)
    )
    unparseable_date_rows = int((~date_ok).sum())
    prepared = prepared.loc[date_ok].copy()

    # Canonical three-class labels.
    prepared["label"] = prepared["Status"].map(normalize_status)

    # Temporal granularity and grouping metadata.
    prepared["granularity"] = prepared["Time"].map(infer_granularity)
    prepared["fact_id"] = _fact_id(prepared)

    # Retained for stratified analysis only, never as model inputs.
    if "Alpha" in prepared.columns:
        prepared["Alpha"] = pd.to_numeric(
            prepared["Alpha"],
            errors="coerce",
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    prepared.to_csv(output, index=False)

    manifest = {
        "source_dataset": DATASET_NAME,
        "source_revision": DATASET_REVISION,
        "source_raw_file": str(source),
        "source_raw_sha256": sha256_file(source),
        "prepared_file": str(output),
        "prepared_sha256": sha256_file(output),

        # Dataset accounting.
        "source_rows": int(len(frame)),
        "rows": int(len(prepared)),
        "eligible_rows": int(len(prepared)),
        "excluded_rows": int(len(frame) - len(prepared)),
        "excluded_status_counts": excluded_status_counts,
        "excluded_unparseable_date_rows": unparseable_date_rows,

        # Explicit exclusion methodology.
        "exclusion_policy": (
            "No context and Discarded records are excluded "
            "from the three-class supervised benchmark. "
            "Original raw records are preserved. Rows whose Time, StartDate or "
            "EndDate is before year 0001 (BCE) or not in YYYY, YYYY-MM or "
            "YYYY-MM-DD form are also excluded and counted."
        ),

        # Prepared dataset statistics.
        "unique_facts": int(prepared["fact_id"].nunique()),
        "unique_subjects": int(prepared["SubjectID"].nunique()),

        "class_counts": {
            str(key): int(value)
            for key, value in (
                prepared["label"].value_counts().sort_index().items()
            )
        },

        "granularity_counts": {
            str(key): int(value)
            for key, value in (
                prepared["granularity"]
                .value_counts()
                .sort_index()
                .items()
            )
        },

        "target_column": "label",
        "target_classes": [
            "correct",
            "incorrect",
            "transitional",
        ],
        "excluded_from_model_inputs": [
            "Status",
            "Alpha",
            "label",
        ],
        "group_key": "fact_id = SubjectID|RelationID|ObjectID",
        "note": (
            "No train/test split is implied; "
            "this is an evaluation dataset."
        ),
    }

    manifest_path = output.with_suffix(
        output.suffix + ".manifest.json"
    )

    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    return manifest


def load_prepared_dataset(path: str) -> pd.DataFrame:
    """Load and validate a prepared CSV dataset."""

    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(
            "Prepared dataset not found: {}".format(source)
        )

    frame = pd.read_csv(source)

    required = [
        "StartDate",
        "EndDate",
        "Time",
        "label",
        "granularity",
        "fact_id",
        "Statement",
    ]

    missing = [
        column
        for column in required
        if column not in frame.columns
    ]

    if missing:
        raise ValueError(
            "Prepared dataset is missing columns: {}".format(missing)
        )

    if frame.empty:
        raise ValueError(
            "Prepared dataset contains no rows"
        )

    frame["label"] = frame["label"].map(normalize_status)

    return frame
