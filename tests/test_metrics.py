from chronofact_agentbench.metrics import classification_metrics


def test_metrics_report_abstention_coverage_and_precision_slices():
    result = classification_metrics(
        ["correct", "incorrect", "transitional"],
        ["correct", "abstain", "transitional"],
        ["year", "month", "day"],
        [0, 0, 2],
        [0, 1, 0],
    )
    assert result["n_samples"] == 3
    assert result["n_answered"] == 2
    assert result["coverage"] == 2.0 / 3.0
    assert result["accuracy"] == 2.0 / 3.0
    assert result["accuracy_by_granularity"]["day"] == 1.0
    assert result["mean_tool_calls"] == 2.0 / 3.0
