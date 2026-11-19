# Changelog

## 0.3.0 — unreleased

- `--structured-output`: every model reply is constrained by an Ollama JSON schema that allows only the action
  expected at that step, so a misnamed final action can no longer end an episode.
- New agent condition `tool_code` (program-aided): after receiving the two date spans, the model writes one
  expression over `cs`, `ce`, `fs`, `fe` that computes the label; `safe_expr.py` evaluates it without `eval`,
  allowing only comparisons, boolean operators, conditional expressions and the three label strings.
- `--agent-conditions` selects the conditions to run.
- `pytest` runs from a fresh clone without installing the package (`pythonpath = ["src"]`).

## 0.2.0 — 2026-11-18

- Agent runs for `qwen2.5:3b` and `llama3.1:8b` on 150 balanced claims, three conditions each, with per-row
  predictions and tool traces in `results/`.
- `scripts/analyse_agents.py`: fact-level bootstrap intervals, exact McNemar tests, confusion matrices and a lenient
  score that separates protocol errors from wrong labels.
- Paper in `paper/`.

## 0.1.0 — 2026-11-17

- Initial reproducible release.
- Pinned TimeStress downloader with SHA-256 verification.
- Date-granularity normalization and interval arithmetic.
- Majority and deterministic interval-rule baselines.
- Optional Ollama text-only and tool-using agent evaluations.
- Metrics, prediction exports, tool traces, manifests, tests, and research documentation.
