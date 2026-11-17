# ChronoFact-AgentBench v0.1.0

**Tool-Augmented Temporal Verification of Time-Qualified Knowledge Claims**

ChronoFact-AgentBench is a reproducible evaluation harness for comparing a text-only language-model baseline with a tool-using agent on historical claims whose validity changes over time. It uses the public **TimeStress** dataset and its three documented labels: `correct`, `incorrect`, and `transitional`.

> **Scope boundary:** the benchmark evaluates whether a supplied time context overlaps a supplied Wikidata-derived validity interval. It does **not** independently establish that the underlying historical fact is true, resolve historiographical disputes, or verify the original source.

## Research question

Does access to explicit date-interval tools improve a local language model's classification of time-qualified claims, especially for month/day precision and partially overlapping boundary contexts, compared with text-only prompting?

The project does not claim a new dataset or a new temporal-reasoning algorithm. Its contribution is a reproducible agent-evaluation protocol with explicit tool traces, abstention accounting, and granularity-specific metrics.

## Why this is a distinct portfolio topic

This project concerns temporal reasoning over historical knowledge claims. It is not an upgrade of an earlier agent-reliability, memory-integrity, healthcare-operations, allocation, decomposition, astronomy, or cross-lingual retrieval project. The agent's tools perform calendar interval inspection and overlap analysis; they do not retrieve multilingual evidence or acquire scientific features sequentially.

## Dataset

- **Dataset:** [Orange/TimeStress](https://huggingface.co/datasets/Orange/TimeStress)
- **Pinned file:** `train.parquet`, revision `f90d17c`
- **Published file SHA-256:** `93df1d4782f770b38d1eda00acb5aa9d97c9a863fd6921fecb6f310052ffa59a`
- **Reported scale:** 523,764 rows, 2,003 temporal facts, 1,883 entities, 86 relations
- **Context precision:** year, year-month, year-month-day
- **License:** CC BY-SA 4.0; dataset is downloaded separately and is not included in this ZIP

TimeStress contains repeated temporal contexts for the same underlying fact. The pipeline therefore creates `fact_id = SubjectID|RelationID|ObjectID` and retains it for cluster-aware analysis. There is no official train/validation/test split in TimeStress; this project does not invent one or train on the evaluation rows.

## Policies and baselines

| Policy | Description |
|---|---|
| `majority` | In-sample class-prior reference; weak descriptive baseline, not deployable |
| `interval_rule` | Deterministic inclusive interval arithmetic; an algorithmic reference, not a learned model |
| `ollama_text_only` | Optional local Ollama model classifies the natural-language statement without tools |
| `ollama_tool_agent` | Optional local Ollama model follows a plan-act-observe-finalize loop using date and interval tools |

The interval-rule baseline uses only `Time`, `StartDate`, and `EndDate`. `Status` is the target. `Alpha` is retained only for descriptive analysis and is never sent to a model or used as a prediction feature.

## Metrics

- Accuracy (abstentions count as incorrect)
- Selective accuracy and answer coverage
- Balanced accuracy and macro-F1
- Per-class F1, including the `transitional` class
- Accuracy by year, month, and day context precision
- Tool-call count and invalid-action count

No pre-filled scientific results are supplied. The experiment creates its own reports from the downloaded data and selected model.

## Requirements

- Python 3.9 or later
- Internet connection for the one-time dataset download
- Approximately 12 MB for the pinned Parquet file, plus the processed CSV and reports
- Optional: Ollama running locally with `qwen2.5:3b` or another compatible chat model

Dependencies are intentionally small: pandas, PyArrow, and pytest for development. No GPU is required for the deterministic benchmark.

## VS Code integrated-terminal setup

Open the extracted `ChronoFact-AgentBench-v0.1.0` folder in VS Code. In its integrated terminal, run these commands in order:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest -q
```

Expected test result: all included unit and pipeline tests pass. These tests validate software behavior only; they are not research findings.

## Run the data pipeline

Download the pinned TimeStress file and verify its published checksum:

```bash
python -m chronofact_agentbench download --output data/raw/timestress_train.parquet
```

Prepare the CSV used by the benchmark:

```bash
python -m chronofact_agentbench prepare --input data/raw/timestress_train.parquet --output data/processed/timestress_prepared.csv
```

Run the full deterministic benchmark (no row cap):

```bash
python -m chronofact_agentbench run --input data/processed/timestress_prepared.csv --output reports/run-01
```

The full deterministic pass evaluates all prepared rows. For a quick software pilot only, add `--max-samples 2000`; do not report a capped pilot as a full-dataset result.

## Optional local Ollama evaluation

First confirm Ollama is running and that the selected model is installed:

```bash
ollama list
```

Then run a small paired comparison on up to 50 stratified rows:

```bash
python -m chronofact_agentbench run --input data/processed/timestress_prepared.csv --output reports/ollama-qwen25-3b --include-ollama --ollama-model qwen2.5:3b --ollama-sample-limit 50
```

The LLM comparison is optional and may be slow. An invalid or unparseable response is recorded as an abstention; it is not silently replaced by the interval-rule answer.

## Outputs

Each run writes:

- `metrics.csv` — policy-level metrics
- `predictions.csv` — row-level predictions and analysis metadata
- `tool_traces.jsonl` — local-agent tool observations (empty when Ollama is disabled)
- `run_metadata.json` — versions, seed, input checksum, row counts, and limitations
- `summary.md` — concise generated report

## Repository layout

```text
ChronoFact-AgentBench-v0.1.0/
├── docs/
├── src/chronofact_agentbench/
├── tests/
├── CITATION.cff
├── LICENSE
├── README.md
└── pyproject.toml
```

## Reproducibility and interpretation

1. Use the pinned TimeStress file and verify the SHA-256 before preparation.
2. Record the prepared-file checksum in the run metadata.
3. Keep `seed=17` when comparing runs.
4. Do not expose `Status` or `Alpha` to the model.
5. Report text-only and tool-agent sample size, coverage, model tag, and Ollama version with results.
6. Treat the interval-rule policy as a deterministic reference because the label definition itself is interval-based.
7. Do not infer that an interval-correct result proves the underlying historical claim.

See `DATA_LICENSE.md`, `docs/METHODOLOGY.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/DATA_DICTIONARY.md`, `docs/LIMITATIONS_ETHICS.md`, and `docs/REFERENCES.md` before writing a paper or public article.

## Repository name

Recommended GitHub repository: **`chronofact-agentbench`**.
