"""Optional local Ollama baselines: text-only and tool-using temporal agent."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Dict, List, Mapping, Optional

from .policies import EVIDENCE_LEVELS, LABELS, tool_observation

LABEL_DEFINITIONS = (
    "Labels: correct = the time in the statement lies entirely inside the period when the fact held; "
    "incorrect = the time does not overlap that period at all; "
    "transitional = the time partly overlaps that period."
)


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, model: str = "qwen2.5:3b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }
        request = urllib.request.Request(
            self.base_url + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise OllamaError("Ollama request failed: {}".format(exc))
        message = result.get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise OllamaError("Ollama returned no message content")
        return content


def parse_json_object(text: str) -> Dict[str, object]:
    """Parse a JSON object, tolerating short surrounding prose or code fences."""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except (TypeError, ValueError):
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object in model response")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Model response JSON is not an object")
    return parsed


def normalize_model_label(value: object) -> Optional[str]:
    label = str(value).strip().lower()
    aliases = {
        "correct": "correct",
        "valid": "correct",
        "incorrect": "incorrect",
        "invalid": "incorrect",
        "transitional": "transitional",
        "partial": "transitional",
    }
    return aliases.get(label)


def _confidence(payload: Mapping[str, object]) -> Optional[float]:
    try:
        value = float(payload.get("confidence"))
    except (TypeError, ValueError):
        return None
    if value < 0.0 or value > 1.0:
        return None
    return value


def predict_text_only(client: OllamaClient, row: Mapping[str, object]) -> Dict[str, object]:
    """Ask the model to judge only the natural-language statement."""
    messages = [
        {
            "role": "system",
            "content": (
                "Classify the time-qualified historical statement using your learned knowledge only. "
                "Do not use external tools. " + LABEL_DEFINITIONS + " Return JSON with keys label and confidence. "
                "label must be correct, incorrect, or transitional. Confidence must be 0 to 1."
            ),
        },
        {"role": "user", "content": str(row["Statement"])},
    ]
    response = client.chat(messages)
    try:
        payload = parse_json_object(response)
    except ValueError:
        return {
            "label": "abstain",
            "confidence": None,
            "tool_calls": 0,
            "invalid_actions": 1,
            "fallback_actions": 0,
            "trace": [{"stage": "text_only_parse_error", "raw": response}],
        }
    label = normalize_model_label(payload.get("label")) or "abstain"
    return {
        "label": label,
        "confidence": _confidence(payload),
        "tool_calls": 0,
        "invalid_actions": 0 if label in LABELS else 1,
        "fallback_actions": 0,
        "trace": [{"stage": "text_only", "response": payload}],
    }


def predict_tool_agent(
    client: OllamaClient, row: Mapping[str, object], evidence_level: str = "overlap"
) -> Dict[str, object]:
    """Run a small plan-act-observe-finalize loop using deterministic date tools.

    ``evidence_level`` sets what compare_context returns (see ``tool_observation``).
    """
    if evidence_level not in EVIDENCE_LEVELS:
        raise ValueError("Unsupported evidence level: {!r}".format(evidence_level))
    trace = []
    invalid_actions = 0
    tool_calls = 0
    base_context = {
        "statement": str(row["Statement"]),
        "time": str(row["Time"]),
        "subject_id": str(row.get("SubjectID", "")),
        "relation_id": str(row.get("RelationID", "")),
        "object_id": str(row.get("ObjectID", "")),
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are a temporal fact verification agent. Do not guess from memory. "
                "Use the available tools in order: first request get_fact_interval, then "
                "request compare_context, then classify from the returned interval evidence. "
                + LABEL_DEFINITIONS + " "
                "For tool requests return JSON {\"action\":\"get_fact_interval\"} or "
                "{\"action\":\"compare_context\"}. For the final answer return JSON "
                "{\"action\":\"final\",\"label\":\"correct|incorrect|transitional\","
                "\"confidence\":0.0}. Never invent dates."
            ),
        },
        {"role": "user", "content": json.dumps(base_context, ensure_ascii=False)},
    ]

    fact_interval = None
    evidence = None
    for step in range(3):
        response = client.chat(messages)
        try:
            action = parse_json_object(response)
        except ValueError:
            invalid_actions += 1
            trace.append({"stage": "action_parse_error", "raw": response})
            return _abstain(trace, tool_calls, invalid_actions)

        name = str(action.get("action", "")).strip()
        if name == "get_fact_interval" and fact_interval is None:
            fact_interval = {
                "start_date": str(row["StartDate"]),
                "end_date": str(row["EndDate"]),
            }
            tool_calls += 1
            observation = {"tool": name, "observation": fact_interval}
            trace.append(observation)
            messages.append({"role": "assistant", "content": json.dumps(action)})
            messages.append({"role": "user", "content": "Tool result: " + json.dumps(observation)})
            continue

        if name == "compare_context" and fact_interval is not None and evidence is None:
            evidence = tool_observation(row, evidence_level)
            tool_calls += 1
            observation = {"tool": name, "observation": evidence}
            trace.append(observation)
            messages.append({"role": "assistant", "content": json.dumps(action)})
            messages.append({"role": "user", "content": "Tool result: " + json.dumps(observation)})
            continue

        if name == "final" and evidence is not None:
            label = normalize_model_label(action.get("label")) or "abstain"
            if label == "abstain":
                invalid_actions += 1
            trace.append({"stage": "final", "response": action})
            return {
                "label": label,
                "confidence": _confidence(action),
                "tool_calls": tool_calls,
                "invalid_actions": invalid_actions,
                "fallback_actions": 0,
                "trace": trace,
            }

        invalid_actions += 1
        trace.append({"stage": "invalid_action", "response": action})
        return _abstain(trace, tool_calls, invalid_actions)

    return _abstain(trace, tool_calls, invalid_actions + 1)


def _abstain(trace: List[Dict[str, object]], tool_calls: int, invalid_actions: int) -> Dict[str, object]:
    return {
        "label": "abstain",
        "confidence": None,
        "tool_calls": tool_calls,
        "invalid_actions": invalid_actions,
        "fallback_actions": 0,
        "trace": trace,
    }
