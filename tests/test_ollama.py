from chronofact_agentbench.ollama import (
    normalize_model_label,
    parse_json_object,
    predict_text_only,
    predict_tool_agent,
)


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)

    def chat(self, messages):
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
