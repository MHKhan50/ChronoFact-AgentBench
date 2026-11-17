"""Date-granularity parsing and interval arithmetic for temporal fact checks."""

from __future__ import annotations

import calendar
import re
from datetime import date
from typing import Dict, Tuple


_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")


def parse_temporal_interval(value: str) -> Tuple[date, date, str]:
    """Parse YYYY, YYYY-MM, or YYYY-MM-DD as an inclusive date interval."""
    if value is None:
        raise ValueError("Temporal value cannot be null")
    value = str(value).strip()
    match = _DATE_RE.match(value)
    if not match:
        raise ValueError("Unsupported date format: {!r}".format(value))

    year = int(match.group(1))
    month_text = match.group(2)
    day_text = match.group(3)

    if year < 1 or year > 9999:
        raise ValueError("Year must be between 0001 and 9999: {!r}".format(value))

    if month_text is None:
        return date(year, 1, 1), date(year, 12, 31), "year"

    month = int(month_text)
    if day_text is None:
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last_day), "month"

    day = int(day_text)
    exact = date(year, month, day)
    return exact, exact, "day"


def infer_granularity(value: str) -> str:
    """Return year, month, or day for a supported ISO-like context."""
    return parse_temporal_interval(value)[2]


def compare_intervals(
    context_start: date,
    context_end: date,
    fact_start: date,
    fact_end: date,
) -> Dict[str, object]:
    """Return transparent overlap evidence without returning a class label."""
    if context_start > context_end:
        raise ValueError("Context interval starts after it ends")
    if fact_start > fact_end:
        raise ValueError("Fact interval starts after it ends")

    overlap_start = max(context_start, fact_start)
    overlap_end = min(context_end, fact_end)
    if overlap_start <= overlap_end:
        overlap_days = (overlap_end - overlap_start).days + 1
    else:
        overlap_days = 0

    context_days = (context_end - context_start).days + 1
    fact_days = (fact_end - fact_start).days + 1
    return {
        "context_start": context_start.isoformat(),
        "context_end": context_end.isoformat(),
        "fact_start": fact_start.isoformat(),
        "fact_end": fact_end.isoformat(),
        "context_days": context_days,
        "fact_days": fact_days,
        "overlap_days": overlap_days,
        "fully_contained": context_start >= fact_start and context_end <= fact_end,
        "no_overlap": overlap_days == 0,
        "partial_overlap": overlap_days > 0
        and not (context_start >= fact_start and context_end <= fact_end),
    }


def classify_interval_evidence(evidence: Dict[str, object]) -> str:
    """Map interval evidence to the TimeStress three-way status taxonomy."""
    if bool(evidence["fully_contained"]):
        return "correct"
    if bool(evidence["no_overlap"]):
        return "incorrect"
    return "transitional"


def compare_time_to_fact(time_value: str, start_value: str, end_value: str) -> Dict[str, object]:
    """Parse the three dates and calculate overlap evidence."""
    context_start, context_end, granularity = parse_temporal_interval(time_value)
    fact_start, _, _ = parse_temporal_interval(start_value)
    _, fact_end, _ = parse_temporal_interval(end_value)
    evidence = compare_intervals(context_start, context_end, fact_start, fact_end)
    evidence["granularity"] = granularity
    evidence["gap_days"] = _gap_days(context_start, context_end, fact_start, fact_end)
    return evidence


def _gap_days(
    context_start: date,
    context_end: date,
    fact_start: date,
    fact_end: date,
) -> int:
    """Return zero for overlap, otherwise the number of whole days between intervals."""
    if context_end < fact_start:
        return (fact_start - context_end).days - 1
    if context_start > fact_end:
        return (context_start - fact_end).days - 1
    return 0


def row_interval_evidence(row: Dict[str, object]) -> Dict[str, object]:
    """Convenience wrapper for a mapping-like dataset row."""
    return compare_time_to_fact(
        str(row["Time"]), str(row["StartDate"]), str(row["EndDate"])
    )
