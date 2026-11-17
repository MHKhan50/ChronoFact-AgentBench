import pandas as pd
import pytest

from chronofact_agentbench.data import normalize_status, prepare_dataset


def test_status_normalization_is_case_insensitive():
    assert normalize_status("Correct") == "correct"
    assert normalize_status("INCORRECT") == "incorrect"
    assert normalize_status(" Transitional ") == "transitional"


def test_unknown_status_is_not_silently_mapped():
    with pytest.raises(ValueError):
        normalize_status("unknown")


def test_prepare_dataset_writes_manifest_and_fact_groups(tmp_path, toy_frame, monkeypatch):
    raw = tmp_path / "raw.parquet"
    output = tmp_path / "processed.csv"
    raw.write_bytes(b"test-only placeholder; parquet reader is mocked")
    monkeypatch.setattr(pd, "read_parquet", lambda path: toy_frame.copy())
    manifest = prepare_dataset(str(raw), str(output))
    prepared = pd.read_csv(output)
    assert manifest["rows"] == 4
    assert manifest["unique_facts"] == 3
    assert "fact_id" in prepared.columns
    assert output.with_suffix(".csv.manifest.json").exists()


def test_download_dataset_verifies_checksum_and_writes_manifest(tmp_path, monkeypatch):
    import hashlib
    import io
    import json
    import chronofact_agentbench.data as data_module

    payload = b"deterministic test payload"
    expected = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(data_module, "DATASET_SHA256", expected)
    monkeypatch.setattr(
        data_module.urllib.request,
        "urlopen",
        lambda request, timeout: io.BytesIO(payload),
    )
    output = tmp_path / "raw" / "dataset.parquet"
    manifest = data_module.download_dataset(str(output))
    assert output.read_bytes() == payload
    assert manifest["checksum_verified"] is True
    assert manifest["sha256"] == expected
    saved = json.loads(output.with_suffix(".parquet.manifest.json").read_text())
    assert saved["checksum_verified"] is True


def test_real_parquet_round_trip_when_pyarrow_is_available(tmp_path, toy_frame):
    pytest.importorskip("pyarrow")
    raw = tmp_path / "roundtrip.parquet"
    output = tmp_path / "roundtrip.csv"
    toy_frame.to_parquet(raw, index=False)
    manifest = prepare_dataset(str(raw), str(output))
    assert manifest["rows"] == len(toy_frame)
