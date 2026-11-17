"""Evaluation metrics with explicit abstention coverage reporting."""

from __future__ import annotations

from typing import Dict, Sequence

LABELS = ["correct", "incorrect", "transitional"]


def _safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def classification_metrics(
    truth: Sequence[str],
    predictions: Sequence[str],
    granularities: Sequence[str],
    tool_calls: Sequence[int] = None,
    invalid_actions: Sequence[int] = None,
) -> Dict[str, object]:
    """Compute macro metrics, coverage, and granularity-specific accuracy."""
    if not (len(truth) == len(predictions) == len(granularities)):
        raise ValueError("truth, predictions, and granularities must have equal lengths")
    total = len(truth)
    if total == 0:
        raise ValueError("Cannot score an empty prediction set")

    answered_indices = [i for i, value in enumerate(predictions) if value in LABELS]
    answered = len(answered_indices)
    correct_count = sum(1 for i in range(total) if predictions[i] == truth[i])
    per_class = {}
    f1_values = []
    for label in LABELS:
        tp = sum(1 for i in range(total) if truth[i] == label and predictions[i] == label)
        fp = sum(1 for i in range(total) if truth[i] != label and predictions[i] == label)
        fn = sum(1 for i in range(total) if truth[i] == label and predictions[i] != label)
        precision = _safe_divide(tp, tp + fp)
        recall = _safe_divide(tp, tp + fn)
        f1 = _safe_divide(2 * precision * recall, precision + recall)
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1}
        f1_values.append(f1)

    balanced_accuracy = sum(per_class[label]["recall"] for label in LABELS) / float(len(LABELS))
    result = {
        "n_samples": total,
        "n_answered": answered,
        "coverage": _safe_divide(answered, total),
        "accuracy": _safe_divide(correct_count, total),
        "selective_accuracy": _safe_divide(
            sum(1 for i in answered_indices if predictions[i] == truth[i]), answered
        ),
        "balanced_accuracy": balanced_accuracy,
        "macro_f1": sum(f1_values) / float(len(f1_values)),
        "per_class": per_class,
        "accuracy_by_granularity": {},
        "mean_tool_calls": (
            sum(tool_calls) / float(len(tool_calls)) if tool_calls else 0.0
        ),
        "invalid_actions": sum(invalid_actions) if invalid_actions else 0,
    }
    for granularity in ("year", "month", "day"):
        indices = [i for i, value in enumerate(granularities) if value == granularity]
        if indices:
            result["accuracy_by_granularity"][granularity] = _safe_divide(
                sum(1 for i in indices if predictions[i] == truth[i]), len(indices)
            )
    return result
