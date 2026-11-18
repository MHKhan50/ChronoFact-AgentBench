"""Reproducible evaluation of interval baselines and optional Ollama agents."""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from . import __version__
from .data import sha256_file
from .metrics import classification_metrics
from .ollama import OllamaClient, OllamaError, predict_text_only, predict_tool_agent
from .policies import interval_rule_policy, majority_policy

# Agent conditions, from least to most help: memory only, the two date intervals, and the
# intervals plus overlap counts and containment flags (from which the label follows by rule).
AGENT_CONDITIONS = {
    "text": predict_text_only,
    "tool_dates": lambda client, row: predict_tool_agent(client, row, evidence_level="dates"),
    "tool_overlap": lambda client, row: predict_tool_agent(client, row, evidence_level="overlap"),
}


def _stratified_sample(frame: pd.DataFrame, limit: int, seed: int) -> pd.DataFrame:
    """Sample proportionally by class and precision while preserving source indices."""
    if limit <= 0:
        raise ValueError("Sample limit must be a positive integer")
    if len(frame) <= limit:
        return frame.copy()
    groups = [group for _, group in frame.groupby(["label", "granularity"], sort=True)]
    pieces = []
    for group in groups:
        take = max(1, int(round(limit * len(group) / float(len(frame)))))
        take = min(take, len(group))
        pieces.append(group.sample(n=take, random_state=seed))
    sampled = pd.concat(pieces)
    if len(sampled) > limit:
        sampled = sampled.sample(n=limit, random_state=seed)
    elif len(sampled) < limit:
        remaining = frame.loc[~frame.index.isin(sampled.index)]
        extra_count = min(limit - len(sampled), len(remaining))
        if extra_count:
            sampled = pd.concat([sampled, remaining.sample(n=extra_count, random_state=seed)])
    return sampled.sample(frac=1.0, random_state=seed)


def _metric_row(policy: str, subset: pd.DataFrame, prediction_column: str) -> Dict[str, object]:
    metrics = classification_metrics(
        subset["label"].astype(str).tolist(),
        subset[prediction_column].fillna("abstain").astype(str).tolist(),
        subset["granularity"].astype(str).tolist(),
        subset.get("tool_calls", pd.Series([0] * len(subset))).astype(int).tolist(),
        subset.get("invalid_actions", pd.Series([0] * len(subset))).astype(int).tolist(),
    )
    return {
        "policy": policy,
        "n_samples": metrics["n_samples"],
        "n_answered": metrics["n_answered"],
        "coverage": metrics["coverage"],
        "accuracy": metrics["accuracy"],
        "selective_accuracy": metrics["selective_accuracy"],
        "balanced_accuracy": metrics["balanced_accuracy"],
        "macro_f1": metrics["macro_f1"],
        "correct_f1": metrics["per_class"]["correct"]["f1"],
        "incorrect_f1": metrics["per_class"]["incorrect"]["f1"],
        "transitional_f1": metrics["per_class"]["transitional"]["f1"],
        "accuracy_year": metrics["accuracy_by_granularity"].get("year"),
        "accuracy_month": metrics["accuracy_by_granularity"].get("month"),
        "accuracy_day": metrics["accuracy_by_granularity"].get("day"),
        "mean_tool_calls": metrics["mean_tool_calls"],
        "invalid_actions": metrics["invalid_actions"],
    }


def run_experiment(
    frame: pd.DataFrame,
    output_dir: str,
    seed: int = 17,
    max_samples: Optional[int] = None,
    include_ollama: bool = False,
    ollama_model: str = "qwen2.5:3b",
    ollama_sample_limit: int = 50,
    ollama_base_url: str = "http://localhost:11434",
    input_sha256: Optional[str] = None,
) -> Dict[str, str]:
    """Run the full interval baseline and optional small local-model evaluation."""
    if "label" not in frame.columns or "granularity" not in frame.columns:
        raise ValueError("Input frame must be prepared with label and granularity columns")
    data = frame.copy().reset_index(drop=True)
    if max_samples is not None:
        if int(max_samples) <= 0:
            raise ValueError("max_samples must be a positive integer when supplied")
        data = _stratified_sample(data, int(max_samples), seed).reset_index(drop=True)
    if include_ollama and int(ollama_sample_limit) <= 0:
        raise ValueError("ollama_sample_limit must be positive when Ollama is enabled")
    if data.empty:
        raise ValueError("Experiment input contains no rows")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    majority_label = data["label"].value_counts().idxmax()

    prediction_rows: List[Dict[str, object]] = []
    for index, row in data.iterrows():
        record = row.to_dict()
        prediction_rows.append(
            {
                "row_id": index,
                "fact_id": str(row.get("fact_id", "")),
                "subject_id": str(row.get("SubjectID", "")),
                "relation_id": str(row.get("RelationID", "")),
                "object_id": str(row.get("ObjectID", "")),
                "label": str(row["label"]),
                "granularity": str(row["granularity"]),
                "alpha_for_analysis_only": row.get("Alpha"),
                "majority_prediction": majority_policy(str(majority_label)),
                "interval_rule_prediction": interval_rule_policy(record),
            }
        )
        for condition in AGENT_CONDITIONS:
            prediction_rows[-1].update(
                {
                    "ollama_{}_prediction".format(condition): None,
                    "ollama_{}_confidence".format(condition): None,
                    "ollama_{}_tool_calls".format(condition): 0,
                    "ollama_{}_invalid_actions".format(condition): 0,
                }
            )

    traces = []
    ollama_error = None
    if include_ollama:
        client = OllamaClient(model=ollama_model, base_url=ollama_base_url)
        sample = _stratified_sample(data, int(ollama_sample_limit), seed + 1)
        sampled_indices = set(sample.index.tolist())
        for row_index in sorted(sampled_indices):
            row = data.iloc[row_index]
            results = {}
            try:
                for condition, runner in AGENT_CONDITIONS.items():
                    results[condition] = runner(client, row)
            except OllamaError as exc:
                ollama_error = str(exc)
                break
            for condition, result in results.items():
                prediction_rows[row_index]["ollama_{}_prediction".format(condition)] = result["label"]
                prediction_rows[row_index]["ollama_{}_confidence".format(condition)] = result["confidence"]
                prediction_rows[row_index]["ollama_{}_tool_calls".format(condition)] = result["tool_calls"]
                prediction_rows[row_index]["ollama_{}_invalid_actions".format(condition)] = result["invalid_actions"]
            traces.append(
                {
                    "row_id": row_index,
                    "fact_id": str(row.get("fact_id", "")),
                    **{condition: result["trace"] for condition, result in results.items()},
                }
            )

    predictions = pd.DataFrame(prediction_rows)
    metrics_rows = [
        _metric_row("majority", predictions, "majority_prediction"),
        _metric_row("interval_rule", predictions, "interval_rule_prediction"),
    ]
    if include_ollama:
        ollama_subset = predictions[predictions["ollama_text_prediction"].notna()].copy()
        if not ollama_subset.empty:
            for condition in AGENT_CONDITIONS:
                metrics_rows.append(
                    _metric_row("ollama_" + condition, ollama_subset, "ollama_{}_prediction".format(condition))
                )
                calls = ollama_subset["ollama_{}_tool_calls".format(condition)].astype(int).tolist()
                invalid = ollama_subset["ollama_{}_invalid_actions".format(condition)].astype(int).tolist()
                metrics_rows[-1]["mean_tool_calls"] = sum(calls) / float(len(calls))
                metrics_rows[-1]["invalid_actions"] = sum(invalid)
            metrics_rows.append(
                _metric_row("interval_rule_on_agent_sample", ollama_subset, "interval_rule_prediction")
            )

    metrics = pd.DataFrame(metrics_rows)
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "predictions.csv", index=False)
    with (out / "tool_traces.jsonl").open("w", encoding="utf-8") as handle:
        for item in traces:
            handle.write(json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n")

    metadata = {
        "project": "ChronoFact-AgentBench",
        "version": __version__,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "rows_used": int(len(data)),
        "unique_facts": int(data.get("fact_id", pd.Series(dtype=str)).nunique()),
        "class_counts": {str(k): int(v) for k, v in data["label"].value_counts().items()},
        "granularity_counts": {
            str(k): int(v) for k, v in data["granularity"].value_counts().items()
        },
        "grouping_note": "Rows are repeated contexts for the same fact; fact_id is retained for cluster-aware analysis.",
        "target": "label (Correct / Incorrect / Transitional)",
        "model_input_exclusions": ["Status", "Alpha", "label"],
        "include_ollama": include_ollama,
        "ollama_model": ollama_model if include_ollama else None,
        "ollama_sample_limit": int(ollama_sample_limit) if include_ollama else 0,
        "ollama_error": ollama_error,
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "input_sha256": input_sha256,
        "interpretation": "This evaluates temporal validity labels from TimeStress, not independent historical truth or source reliability.",
    }
    (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    summary = [
        "# ChronoFact-AgentBench experiment summary",
        "",
        "Generated from the actual run. No performance results are pre-filled.",
        "",
        "- Rows used: {}".format(len(data)),
        "- Unique fact groups: {}".format(metadata["unique_facts"]),
        "- Seed: {}".format(seed),
        "- Ollama included: {}".format(include_ollama),
        "",
        "## Metrics",
        "",
        metrics.to_string(index=False),
        "",
        "## Interpretation boundary",
        "",
        "The target is the TimeStress temporal-context label. It is not an independent fact-check of the underlying historical claim.",
    ]
    (out / "summary.md").write_text("\n".join(summary), encoding="utf-8")

    return {
        "metrics": str(out / "metrics.csv"),
        "predictions": str(out / "predictions.csv"),
        "traces": str(out / "tool_traces.jsonl"),
        "metadata": str(out / "run_metadata.json"),
        "summary": str(out / "summary.md"),
    }
