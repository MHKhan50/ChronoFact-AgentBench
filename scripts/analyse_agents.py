"""Paired analysis of the three local-model agent conditions on the balanced agent sample.

Reads results/agents-<model>/agent_predictions.csv and tool_traces.jsonl for each model and writes
results/analysis/analysis.json, results/analysis/tables.md and the paper figure.

* Accuracy counts abstentions as wrong. 95% intervals come from a bootstrap that resamples
  whole facts (fact_id), because the 150 rows come from 82 facts.
* Conditions are compared on the same rows with an exact McNemar test.
* "Lenient" rescoring: when the agent broke the tool protocol (for example answered with
  action "classify" instead of "final") but still gave a valid label, that label is used. This
  separates protocol errors from wrong answers; the strict score stays the main result.

Usage: python scripts/analyse_agents.py
"""
from __future__ import annotations

import json
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = RESULTS / "analysis"
MODELS = {"qwen2.5:3b": "agents-qwen2-5-3b", "llama3.1:8b": "agents-llama3-1-8b"}
CONDITIONS = {"text": "Text only", "tool_dates": "Tool: dates", "tool_overlap": "Tool: dates + overlap flags"}
LABELS = ("correct", "incorrect", "transitional")
ALIASES = {"correct": "correct", "valid": "correct", "incorrect": "incorrect", "invalid": "incorrect",
           "transitional": "transitional", "partial": "transitional"}
N_BOOT = 10_000
SEED = 17
COLOURS = {"text": "#1F4E9C", "tool_dates": "#E3A800", "tool_overlap": "#5FA65A"}


def mcnemar_exact(a_right: np.ndarray, b_right: np.ndarray) -> dict:
    a_only = int(np.sum(a_right & ~b_right))
    b_only = int(np.sum(~a_right & b_right))
    n = a_only + b_only
    if n == 0:
        return {"a_only": 0, "b_only": 0, "p_value": 1.0}
    k = min(a_only, b_only)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
    return {"a_only": a_only, "b_only": b_only, "p_value": p}


def cluster_bootstrap(right: np.ndarray, clusters: np.ndarray, rng: np.random.Generator) -> list:
    ids = np.unique(clusters)
    index = {c: np.flatnonzero(clusters == c) for c in ids}
    stats = []
    for _ in range(N_BOOT):
        pick = rng.choice(ids, size=len(ids), replace=True)
        rows = np.concatenate([index[c] for c in pick])
        stats.append(right[rows].mean())
    return [float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))]


def lenient_labels(traces: list, condition: str) -> dict:
    """row_id -> label taken from a protocol-breaking final step that still names a valid label."""
    out = {}
    for item in traces:
        for step in item.get(condition, []):
            if step.get("stage") == "invalid_action":
                label = ALIASES.get(str(step.get("response", {}).get("label", "")).strip().lower())
                if label:
                    out[item["row_id"]] = label
    return out


def analyse_model(name: str, folder: str, rng: np.random.Generator) -> dict:
    frame = pd.read_csv(RESULTS / folder / "agent_predictions.csv")
    traces = [json.loads(line) for line in open(RESULTS / folder / "tool_traces.jsonl")]
    truth = frame["label"].to_numpy()
    clusters = frame["fact_id"].to_numpy()
    result = {"rows": int(len(frame)), "facts": int(frame["fact_id"].nunique()),
              "label_counts": frame["label"].value_counts().to_dict(),
              "granularity_counts": frame["granularity"].value_counts().to_dict(), "conditions": {}}
    right, right_lenient = {}, {}
    for cond in CONDITIONS:
        pred = frame[f"ollama_{cond}_prediction"].fillna("abstain").astype(str).to_numpy()
        ok = pred == truth
        right[cond] = ok
        answered = pred != "abstain"
        lenient = lenient_labels(traces, cond)
        pred_len = np.array([lenient.get(r, p) if p == "abstain" else p for r, p in zip(frame["row_id"], pred)])
        right_lenient[cond] = pred_len == truth
        confusion = pd.crosstab(pd.Series(truth, name="label"), pd.Series(pred, name="prediction"))
        result["conditions"][cond] = {
            "accuracy": float(ok.mean()),
            "accuracy_ci95": cluster_bootstrap(ok, clusters, rng),
            "coverage": float(answered.mean()),
            "selective_accuracy": float(ok[answered].mean()) if answered.any() else None,
            "abstentions": int((~answered).sum()),
            "lenient_accuracy": float((pred_len == truth).mean()),
            "lenient_accuracy_ci95": cluster_bootstrap(pred_len == truth, clusters, rng),
            "lenient_recall_by_label": {lab: float((pred_len == truth)[truth == lab].mean()) for lab in LABELS},
            "lenient_recovered": int(sum(1 for p in pred if p == "abstain") - int((pred_len == "abstain").sum())),
            "recall_by_label": {lab: float(ok[truth == lab].mean()) for lab in LABELS},
            "accuracy_by_granularity": {g: float(ok[frame["granularity"].to_numpy() == g].mean())
                                        for g in ("year", "month", "day")},
            "confusion": {str(k): {str(c): int(v) for c, v in row.items()} for k, row in confusion.iterrows()},
        }
    pairs = [("tool_dates", "text"), ("tool_overlap", "tool_dates"), ("tool_overlap", "text")]
    result["mcnemar"] = {f"{a} vs {b}": mcnemar_exact(right[a], right[b]) for a, b in pairs}
    result["mcnemar_lenient"] = {f"{a} vs {b}": mcnemar_exact(right_lenient[a], right_lenient[b]) for a, b in pairs}
    return result


def figure(results: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    width, x = 0.26, np.arange(len(results))
    for i, cond in enumerate(CONDITIONS):
        acc = [results[m]["conditions"][cond]["accuracy"] * 100 for m in results]
        lo = [results[m]["conditions"][cond]["accuracy_ci95"][0] * 100 for m in results]
        hi = [results[m]["conditions"][cond]["accuracy_ci95"][1] * 100 for m in results]
        err = [np.subtract(acc, lo), np.subtract(hi, acc)]
        ax.bar(x + (i - 1) * width, acc, width, yerr=err, capsize=3, color=COLOURS[cond],
               label=CONDITIONS[cond], edgecolor="white", linewidth=1)
        lenient = [results[m]["conditions"][cond]["lenient_accuracy"] * 100 for m in results]
        ax.scatter(x + (i - 1) * width, lenient, marker="D", s=18, color="black", zorder=3,
                   label="Lenient scoring (protocol errors forgiven)" if i == 0 else None)
    ax.axhline(100 / 3, color="#C8102E", linestyle="--", linewidth=1, label="Chance (balanced labels)")
    ax.set_xticks(x, list(results))
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 105)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_agent_accuracy.{ext}", dpi=200)


def tables(results: dict) -> str:
    lines = ["| Model | Condition | Accuracy % [95% CI] | Coverage % | Selective acc. % | Lenient acc. % |",
             "|---|---|---|---|---|---|"]
    for m, r in results.items():
        for cond, label in CONDITIONS.items():
            c = r["conditions"][cond]
            sel = "--" if c["selective_accuracy"] is None else f"{c['selective_accuracy'] * 100:.1f}"
            lines.append(f"| {m} | {label} | {c['accuracy'] * 100:.1f} [{c['accuracy_ci95'][0] * 100:.1f}, "
                         f"{c['accuracy_ci95'][1] * 100:.1f}] | {c['coverage'] * 100:.1f} | {sel} | "
                         f"{c['lenient_accuracy'] * 100:.1f} |")
    lines += ["", "| Model | Comparison | Only first right | Only second right | McNemar p |", "|---|---|---|---|---|"]
    for m, r in results.items():
        for key, t in r["mcnemar"].items():
            lines.append(f"| {m} | {key} | {t['a_only']} | {t['b_only']} | {t['p_value']:.2g} |")
    lines += ["", "Lenient scoring:", "", "| Model | Comparison | Only first right | Only second right | McNemar p |",
              "|---|---|---|---|---|"]
    for m, r in results.items():
        for key, t in r["mcnemar_lenient"].items():
            lines.append(f"| {m} | {key} | {t['a_only']} | {t['b_only']} | {t['p_value']:.2g} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    results = {m: analyse_model(m, folder, rng) for m, folder in MODELS.items()}
    (OUT / "analysis.json").write_text(json.dumps(results, indent=2))
    (OUT / "tables.md").write_text(tables(results))
    figure(results)
    print(tables(results))


if __name__ == "__main__":
    main()
