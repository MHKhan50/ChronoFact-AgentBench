"""Deterministic baselines and tool evidence construction."""

from __future__ import annotations

from typing import Dict, Mapping

from .temporal import classify_interval_evidence, row_interval_evidence

LABELS = ("correct", "incorrect", "transitional")


def interval_rule_policy(row: Mapping[str, object]) -> str:
    """Exact interval-arithmetic baseline using no learned model."""
    return classify_interval_evidence(row_interval_evidence(row))


def majority_policy(majority_label: str) -> str:
    """Return a constant class-prior baseline label."""
    if majority_label not in LABELS:
        raise ValueError("Unsupported majority label: {!r}".format(majority_label))
    return majority_label


EVIDENCE_LEVELS = ("dates", "overlap")


def tool_observation(row: Mapping[str, object], level: str = "overlap") -> Dict[str, object]:
    """Return interval evidence for an agent, without the target label.

    ``dates``: the parsed context and fact intervals only; the agent must compare them itself.
    ``overlap``: also the overlap counts and containment flags, from which the label follows by rule.
    """
    if level not in EVIDENCE_LEVELS:
        raise ValueError("Unsupported evidence level: {!r}".format(level))
    evidence = row_interval_evidence(row)
    if level == "dates":
        return {
            "time_granularity": evidence["granularity"],
            "context_start": evidence["context_start"],
            "context_end": evidence["context_end"],
            "fact_start": evidence["fact_start"],
            "fact_end": evidence["fact_end"],
        }
    return {
        "time_granularity": evidence["granularity"],
        "context_start": evidence["context_start"],
        "context_end": evidence["context_end"],
        "fact_start": evidence["fact_start"],
        "fact_end": evidence["fact_end"],
        "context_days": evidence["context_days"],
        "fact_days": evidence["fact_days"],
        "overlap_days": evidence["overlap_days"],
        "fully_contained": evidence["fully_contained"],
        "no_overlap": evidence["no_overlap"],
        "partial_overlap": evidence["partial_overlap"],
        "gap_days": evidence["gap_days"],
    }
