from chronofact_agentbench.ollama import (
    normalize_model_label,
    parse_json_object,
    predict_text_only,
    predict_tool_agent,
)


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)

    def chat(self, messages, schema=None):
        self.schemas = getattr(self, "schemas", []) + [schema]
        return self.responses.pop(0)


def test_json_parser_accepts_clean_json_and_wrapped_json():
    assert parse_json_object('{"label":"correct"}') == {"label": "correct"}
    assert parse_json_object('Result: {"label":"incorrect"}') == {"label": "incorrect"}


def test_model_label_normalization():
    assert normalize_model_label("Correct") == "correct"
    assert normalize_model_label("partial") == "transitional"
    assert normalize_model_label("unknown") is None


def test_text_only_policy_records_no_tool_calls(toy_frame):
    client = FakeClient(['{"label":"correct","confidence":0.91}'])
    result = predict_text_only(client, toy_frame.iloc[0])
    assert result["label"] == "correct"
    assert result["tool_calls"] == 0
    assert result["confidence"] == 0.91


def test_tool_agent_executes_two_tools_before_final_label(toy_frame):
    client = FakeClient(
        [
            '{"action":"get_fact_interval"}',
            '{"action":"compare_context"}',
            '{"action":"final","label":"correct","confidence":0.94}',
        ]
    )
    result = predict_tool_agent(client, toy_frame.iloc[0])
    assert result["label"] == "correct"
    assert result["tool_calls"] == 2
    assert result["invalid_actions"] == 0
    assert len(result["trace"]) == 3


def test_tool_agent_abstains_on_invalid_action(toy_frame):
    client = FakeClient(['{"action":"delete_database"}'])
    result = predict_tool_agent(client, toy_frame.iloc[0])
    assert result["label"] == "abstain"
    assert result["invalid_actions"] == 1


def test_structured_output_sends_one_allowed_action_per_step(toy_frame):
    client = FakeClient(
        [
            '{"action":"get_fact_interval"}',
            '{"action":"compare_context"}',
            '{"action":"final","label":"correct","confidence":0.9}',
        ]
    )
    result = predict_tool_agent(client, toy_frame.iloc[0], evidence_level="dates", structured=True)
    assert result["label"] == "correct"
    actions = [schema["properties"]["action"]["enum"] for schema in client.schemas]
    assert actions == [["get_fact_interval"], ["compare_context"], ["final"]]
    assert client.schemas[-1]["properties"]["label"]["enum"] == ["correct", "incorrect", "transitional"]


def test_code_agent_label_comes_from_the_evaluated_expression(toy_frame):
    from chronofact_agentbench.policies import interval_rule_policy

    expression = (
        '"correct" if fs <= cs and ce <= fe else ("incorrect" if ce < fs or cs > fe else "transitional")'
    )
    row = toy_frame.iloc[0]
    client = FakeClient(
        [
            '{"action":"get_fact_interval"}',
            '{"action":"compare_context"}',
            '{"action":"final_code","expression":' + __import__("json").dumps(expression) + '}',
        ]
    )
    result = predict_tool_agent(client, row, evidence_level="dates", write_code=True)
    assert result["label"] == interval_rule_policy(row.to_dict())
    assert result["trace"][-1]["stage"] == "final_code"


def test_code_agent_rejects_unsafe_expression(toy_frame):
    client = FakeClient(
        [
            '{"action":"get_fact_interval"}',
            '{"action":"compare_context"}',
            '{"action":"final_code","expression":"__import__(\'os\').system(\'ls\')"}',
        ]
    )
    result = predict_tool_agent(client, toy_frame.iloc[0], evidence_level="dates", write_code=True)
    assert result["label"] == "abstain"
    assert result["invalid_actions"] == 1


def test_repair_agent_gets_one_corrected_expression_after_an_error(toy_frame):
    import json

    from chronofact_agentbench.policies import interval_rule_policy

    good = '"correct" if fs <= cs and ce <= fe else ("incorrect" if ce < fs or cs > fe else "transitional")'
    row = toy_frame.iloc[0]
    client = FakeClient(
        [
            '{"action":"get_fact_interval"}',
            '{"action":"compare_context"}',
            '{"action":"final_code","expression":"cs <= fe"}',
            '{"action":"final_code","expression":' + json.dumps(good) + '}',
        ]
    )
    result = predict_tool_agent(client, row, evidence_level="dates", write_code=True, repair=True)
    assert result["label"] == interval_rule_policy(row.to_dict())
    assert [t.get("stage") for t in result["trace"]][-2:] == ["final_code", "repair_code"]
    assert result["trace"][-2]["error"] == "Expression did not return a label"
    assert result["invalid_actions"] == 1


def test_repair_agent_abstains_after_two_failures_and_plain_code_agent_gets_no_retry(toy_frame):
    replies = [
        '{"action":"get_fact_interval"}',
        '{"action":"compare_context"}',
        '{"action":"final_code","expression":"cs <= fe"}',
        '{"action":"final_code","expression":"2007-01-01 < fe"}',
    ]
    repaired = predict_tool_agent(FakeClient(replies), toy_frame.iloc[0], evidence_level="dates",
                                  write_code=True, repair=True)
    assert repaired["label"] == "abstain" and repaired["invalid_actions"] == 2
    plain_client = FakeClient(replies)
    plain = predict_tool_agent(plain_client, toy_frame.iloc[0], evidence_level="dates", write_code=True)
    assert plain["label"] == "abstain" and plain["invalid_actions"] == 1
    assert len(plain_client.responses) == 1  # no retry was requested


def test_timeout_in_one_episode_is_an_abstention_not_a_crash(toy_frame, tmp_path, monkeypatch):
    from chronofact_agentbench import evaluate
    from chronofact_agentbench.ollama import OllamaTimeout

    class SlowClient:
        def __init__(self, *args, **kwargs):
            pass

        def chat(self, messages, schema=None):
            raise OllamaTimeout("timed out")

    monkeypatch.setattr(evaluate, "OllamaClient", SlowClient)
    frame = toy_frame.copy()
    outputs = evaluate.run_experiment(frame, str(tmp_path), include_ollama=True, ollama_sample_limit=3,
                                      conditions=("text",))
    import json
    meta = json.loads(open(outputs["metadata"]).read())
    assert meta["ollama_timeouts"] >= 1 and meta["ollama_error"] is None
