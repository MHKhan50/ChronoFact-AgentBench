from chronofact_agentbench.policies import interval_rule_policy, majority_policy, tool_observation


def test_interval_rule_policy_matches_three_expected_classes(toy_frame):
    labels = [interval_rule_policy(row) for _, row in toy_frame.iterrows()]
    assert labels == ["correct", "incorrect", "transitional", "correct"]


def test_tool_observation_does_not_expose_target_or_alpha(toy_frame):
    observation = tool_observation(toy_frame.iloc[0])
    assert "label" not in observation
    assert "Status" not in observation
    assert "Alpha" not in observation
    assert observation["fully_contained"] is True


def test_majority_policy_rejects_unknown_class():
    assert majority_policy("correct") == "correct"
    try:
        majority_policy("maybe")
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown majority label should be rejected")


def test_dates_evidence_hides_overlap_flags():
    from chronofact_agentbench.policies import tool_observation

    row = {"Time": "2001", "StartDate": "1999-05-01", "EndDate": "2001-06-30"}
    dates = tool_observation(row, "dates")
    assert set(dates) == {"time_granularity", "context_start", "context_end", "fact_start", "fact_end"}
    full = tool_observation(row, "overlap")
    assert full["partial_overlap"] is True and "overlap_days" in full
