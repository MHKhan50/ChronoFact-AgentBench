from chronofact_agentbench.evaluate import run_experiment


def test_tiny_experiment_writes_reproducible_outputs(tmp_path, toy_frame):
    outputs = run_experiment(
        frame=toy_frame,
        output_dir=str(tmp_path / "run"),
        seed=13,
        max_samples=None,
        include_ollama=False,
    )
    for key in ("metrics", "predictions", "traces", "metadata", "summary"):
        assert (tmp_path / "run" / {
            "metrics": "metrics.csv",
            "predictions": "predictions.csv",
            "traces": "tool_traces.jsonl",
            "metadata": "run_metadata.json",
            "summary": "summary.md",
        }[key]).exists()
        assert outputs[key]

    import pandas as pd
    metrics = pd.read_csv(outputs["metrics"])
    assert set(metrics["policy"]) == {"majority", "interval_rule"}


def test_invalid_sample_limits_are_rejected(tmp_path, toy_frame):
    import pytest

    with pytest.raises(ValueError):
        run_experiment(
            frame=toy_frame,
            output_dir=str(tmp_path / "bad-run"),
            max_samples=0,
        )

    with pytest.raises(ValueError):
        run_experiment(
            frame=toy_frame,
            output_dir=str(tmp_path / "bad-ollama-run"),
            include_ollama=True,
            ollama_sample_limit=0,
        )
