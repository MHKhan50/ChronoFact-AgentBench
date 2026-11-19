"""Optional local Ollama baselines: text-only and tool-using temporal agent."""

from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request
from typing import Dict, List, Mapping, Optional

from .policies import EVIDENCE_LEVELS, LABELS, tool_observation
from .safe_expr import UnsafeExpression, evaluate_label_expression
from .temporal import parse_temporal_interval

LABEL_DEFINITIONS = (
    "Labels: correct = the time in the statement lies entirely inside the period when the fact held; "
    "incorrect = the time does not overlap that period at all; "
    "transitional = the time partly overlaps that period."
)


class OllamaError(RuntimeError):
    pass


class OllamaTimeout(OllamaError):
    """One request took too long; the episode is recorded as an abstention and the run continues."""


class OllamaClient:
    def __init__(self, model: str = "qwen2.5:3b", base_url: str = "http://localhost:11434", timeout: int = 300):
        self.timeout = timeout
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: List[Dict[str, str]], schema: Optional[Dict[str, object]] = None) -> str:
        """Send a chat request. With ``schema``, Ollama constrains the reply to that JSON schema."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": schema if schema is not None else "json",
            # num_predict caps one reply; a JSON action or a label expression needs far fewer tokens.
            "options": {"temperature": 0, "num_predict": 256},
        }
        request = urllib.request.Request(
            self.base_url + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (socket.timeout, TimeoutError) as exc:
            raise OllamaTimeout("Ollama request timed out after {} s".format(self.timeout)) from exc
        except (urllib.error.URLError, ValueError) as exc:
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


def _schema(actions, final: bool = False, code: bool = False) -> Dict[str, object]:
    """JSON schema for one agent step: the allowed action names, plus the answer fields if final."""
    properties: Dict[str, object] = {"action": {"type": "string", "enum": list(actions)}}
    required = ["action"]
    if final:
        properties["label"] = {"type": "string", "enum": list(LABELS)}
        properties["confidence"] = {"type": "number", "minimum": 0, "maximum": 1}
        required += ["label", "confidence"]
    if code:
        properties["expression"] = {"type": "string"}
        required.append("expression")
    return {"type": "object", "properties": properties, "required": required}


TEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": list(LABELS)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["label", "confidence"],
}


def _chat(client, messages, schema: Optional[Dict[str, object]]) -> str:
    return client.chat(messages) if schema is None else client.chat(messages, schema=schema)


def predict_text_only(
    client: OllamaClient, row: Mapping[str, object], structured: bool = False
) -> Dict[str, object]:
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
    response = _chat(client, messages, TEXT_SCHEMA if structured else None)
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


CODE_INSTRUCTIONS = (
    "After compare_context, do not give the label directly. Write one Python expression that computes it from "
    "four dates: cs and ce are the first and last day of the statement's time, fs and fe the first and last day of "
    "the fact's validity period (all inclusive, comparable with < <= > >= == !=). Use only these names, the "
    "strings \"correct\", \"incorrect\" and \"transitional\", comparisons, and/or/not and "
    "x if condition else y. Return JSON {\"action\":\"final_code\",\"expression\":\"...\"}."
)


def predict_tool_agent(
    client: OllamaClient,
    row: Mapping[str, object],
    evidence_level: str = "overlap",
    structured: bool = False,
    write_code: bool = False,
) -> Dict[str, object]:
    """Run a small plan-act-observe-finalize loop using deterministic date tools.

    ``evidence_level`` sets what compare_context returns (see ``tool_observation``).
    ``structured`` constrains every reply to a JSON schema with only the action allowed at that step.
    ``write_code`` asks the model for an expression that computes the label from the dates, which
    is then evaluated by ``safe_expr`` (a program-aided variant of the dates condition).
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
                + (" " + CODE_INSTRUCTIONS if write_code else "")
            ),
        },
        {"role": "user", "content": json.dumps(base_context, ensure_ascii=False)},
    ]

    fact_interval = None
    evidence = None
    final_action = "final_code" if write_code else "final"
    for step in range(3):
        schema = None
        if structured:
            if fact_interval is None:
                schema = _schema(["get_fact_interval"])
            elif evidence is None:
                schema = _schema(["compare_context"])
            else:
                schema = _schema([final_action], final=not write_code, code=write_code)
        response = _chat(client, messages, schema)
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

        if write_code and name == "final_code" and evidence is not None:
            expression = action.get("expression")
            try:
                context_start, context_end, _ = parse_temporal_interval(str(row["Time"]))
                fact_start, _, _ = parse_temporal_interval(str(row["StartDate"]))
                _, fact_end, _ = parse_temporal_interval(str(row["EndDate"]))
                value = evaluate_label_expression(
                    expression, {"cs": context_start, "ce": context_end, "fs": fact_start, "fe": fact_end}
                )
                label = normalize_model_label(value) or "abstain"
                error = None if label != "abstain" else "expression returned an unknown label"
            except UnsafeExpression as exc:
                label, error = "abstain", str(exc)
            if label == "abstain":
                invalid_actions += 1
            trace.append({"stage": "final_code", "response": action, "result": label, "error": error})
            return {
                "label": label,
                "confidence": None,
                "tool_calls": tool_calls,
                "invalid_actions": invalid_actions,
                "fallback_actions": 0,
                "trace": trace,
            }

        if name == "final" and evidence is not None and not write_code:
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
