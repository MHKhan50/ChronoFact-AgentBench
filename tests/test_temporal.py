from datetime import date

import pytest

from chronofact_agentbench.temporal import (
    classify_interval_evidence,
    compare_intervals,
    compare_time_to_fact,
    infer_granularity,
    parse_temporal_interval,
)


def test_year_precision_expands_to_full_calendar_year():
    start, end, precision = parse_temporal_interval("2001")
    assert start == date(2001, 1, 1)
    assert end == date(2001, 12, 31)
    assert precision == "year"


def test_month_precision_handles_leap_year():
    start, end, precision = parse_temporal_interval("2020-02")
    assert start == date(2020, 2, 1)
    assert end == date(2020, 2, 29)
    assert precision == "month"


def test_day_precision_is_single_day():
    start, end, precision = parse_temporal_interval("2024-04-15")
    assert start == end == date(2024, 4, 15)
    assert precision == "day"


def test_invalid_date_is_rejected():
    with pytest.raises(ValueError):
        parse_temporal_interval("2023-02-29")


def test_interval_classification_all_three_classes():
    valid = compare_time_to_fact("2002", "2000-01-01", "2004-12-31")
    invalid = compare_time_to_fact("1999", "2000-01-01", "2004-12-31")
    transitional = compare_time_to_fact("2010", "2010-06-15", "2012-03-10")
    assert classify_interval_evidence(valid) == "correct"
    assert classify_interval_evidence(invalid) == "incorrect"
    assert classify_interval_evidence(transitional) == "transitional"


def test_boundary_touching_is_transitional_when_only_partly_overlapping():
    evidence = compare_time_to_fact("2010", "2010-06-15", "2012-03-10")
    assert evidence["partial_overlap"] is True
    assert evidence["overlap_days"] > 0


def test_invalid_interval_order_is_rejected():
    with pytest.raises(ValueError):
        compare_intervals(date(2020, 2, 1), date(2020, 1, 1), date(2019, 1, 1), date(2021, 1, 1))


def test_granularity_inference():
    assert infer_granularity("1998") == "year"
    assert infer_granularity("1998-06") == "month"
    assert infer_granularity("1998-06-12") == "day"
