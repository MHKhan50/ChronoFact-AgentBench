# ChronoFact-AgentBench

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24356041.svg)](https://doi.org/10.5281/zenodo.24356041)

**Tool-Augmented Temporal Verification of Time-Qualified Knowledge Claims**

ChronoFact-AgentBench is a reproducible evaluation harness for comparing a text-only language-model baseline with a tool-using agent on historical claims whose validity changes over time. It uses the public **TimeStress** dataset and its three documented labels: `correct`, `incorrect`, and `transitional`.

> **Scope boundary:** the benchmark evaluates whether a supplied time context overlaps a supplied Wikidata-derived validity interval. It does **not** independently establish that the underlying historical fact is true, resolve historiographical disputes, or verify the original source.

## Research question

Does access to explicit date-interval tools improve a local language model's classification of time-qualified claims, especially for month/day precision and partially overlapping boundary contexts, compared with text-only prompting?

The project does not claim a new dataset or a new temporal-reasoning algorithm. Its contribution is a reproducible agent-evaluation protocol with explicit tool traces, abstention accounting, and granularity-specific metrics.

## Dataset

- **Dataset:** [Orange/TimeStress](https://huggingface.co/datasets/Orange/TimeStress)
- **Pinned file:** `train.parquet`, revision `f90d17c`
- **Published file SHA-256:** `93df1d4782f770b38d1eda00acb5aa9d97c9a863fd6921fecb6f310052ffa59a`
- **Reported scale:** 523,764 rows, 2,003 temporal facts, 1,883 entities, 86 relations
- **Context precision:** year, year-month, year-month-day
- **License:** CC BY-SA 4.0; the dataset is downloaded separately and is not redistributed in this repository

TimeStress contains repeated temporal contexts for the same underlying fact. The pipeline therefore creates `fact_id = SubjectID|RelationID|ObjectID` and retains it for cluster-aware analysis. There is no official train/validation/test split in TimeStress; this project does not invent one or train on the evaluation rows.

## Policies and baselines

| Policy | Description |
|---|---|
| `majority` | In-sample class-prior reference; weak descriptive baseline, not deployable |
| `interval_rule` | Deterministic inclusive interval arithmetic; an algorithmic reference, not a learned model |
| `ollama_text` | Local model classifies the statement from memory, with the label definitions but no tools |
| `ollama_tool_dates` | Local model calls the tools and receives only the two date intervals; it must compare them itself |
| `ollama_tool_overlap` | Local model also receives overlap counts and containment flags |

The interval rule applies the same definition that produced the TimeStress labels, so it is a ceiling, not a competitor. The three agent conditions separate where errors come from: memory (`text`), date reasoning (`tool_dates`), or copying a label that the flags already imply (`tool_overlap`). All three see the same label definitions.

The interval-rule baseline uses only `Time`, `StartDate`, and `EndDate`. `Status` is the target. `Alpha` is retained only for descriptive analysis and is never sent to a model or used as a prediction feature.

## Metrics

- Accuracy (abstentions count as incorrect)
- Selective accuracy and answer coverage
- Balanced accuracy and macro-F1
- Per-class F1, including the `transitional` class
- Accuracy by year, month, and day context precision
- Tool-call count and invalid-action count

Every number below was produced by the pipeline from the downloaded data; the per-row predictions and tool traces are in `results/`.

## Results (v0.3.0)

Two local models (Ollama, temperature 0) on 150 TimeStress claims, 50 per label, from 82 facts. Abstentions count as
wrong; 95% intervals from a bootstrap over facts. "Lenient" also accepts a valid label given with a misnamed final
action (`classify` instead of `final`) after both tools were called.

| Model | Condition | Accuracy % [95% CI] | Abstained | Lenient % |
|---|---|---|---|---|
| qwen2.5:3b | Text only | 35.3 [22.8, 47.2] | 0 | 35.3 |
| qwen2.5:3b | Tool: dates | 41.3 [29.2, 52.7] | 1 | 41.3 |
| qwen2.5:3b | Tool: dates + overlap flags | 98.7 [96.6, 100.0] | 1 | 98.7 |
| llama3.1:8b | Text only | 46.0 [33.8, 57.7] | 0 | 46.0 |
| llama3.1:8b | Tool: dates | 30.0 [21.0, 39.7] | 79 | 72.0 |
| llama3.1:8b | Tool: dates + overlap flags | 88.7 [80.9, 95.6] | 17 | 100.0 |

Model writes the comparison as a Python expression (schema-constrained replies; restricted evaluator):

| Model | Condition | Accuracy % [95% CI] | Abstained |
|---|---|---|---|
| qwen2.5:3b | Tool: dates, write code | 0.0 | 150 |
| qwen2.5:3b | … with one repair | 1.3 [0.0, 3.4] | 144 |
| llama3.1:8b | Tool: dates, write code | 2.7 | 144 |
| llama3.1:8b | … with one repair | 31.3 [23.3, 39.5] | 40 |

- From memory both models are close to guessing (33.3%); neither recognises partial overlap.
- Given only the two date spans, `qwen2.5:3b` still calls 37 of 50 correct claims incorrect, and `llama3.1:8b`
  (leniently scored) gets only 18 of 50 partly overlapping claims right.
- When the tool also returns overlap flags, both models reach 98.7–100%.
- Asked to write the comparison in code, the models fail at syntax; after one repair `llama3.1:8b` runs code on 110
  claims but its interval logic is right on only 47. With schema-constrained replies the protocol errors disappear
  and `llama3.1:8b` scores 72.7% (dates) and 100% (overlap flags), matching its lenient scores.
  Outputs: `results/structured-*` and `results/repair-*`.

On all 500,108 rows the majority label scores 86.4% and the interval rule 100% (it applies the label definition).
Paired McNemar tests and confusion matrices: `results/analysis/tables.md` and `analysis.json`. Reproduce with
`python scripts/analyse_agents.py`.

**Paper:** *Give the Model the Overlap, Not the Dates: Tool Evidence for Checking Time-Qualified Claims with Small
Local Models* — [`paper/main.pdf`](paper/main.pdf).

## Requirements

- Python 3.9 or later
- Internet connection for the one-time dataset download
- Approximately 12 MB for the pinned Parquet file, plus the processed CSV and reports
- Optional: Ollama running locally with `qwen2.5:3b` or another compatible chat model

Dependencies are intentionally small: pandas, PyArrow, and pytest for development. No GPU is required for the deterministic benchmark.

## VS Code integrated-terminal setup

Open the repository folder in VS Code. In its integrated terminal, run these commands in order:

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

Then run a paired comparison of the three agent conditions on stratified rows (150 rows, 50 per label, so 450 agent episodes per model):

```bash
python -m chronofact_agentbench run --input data/processed/timestress_prepared.csv --output reports/qwen25-3b --include-ollama --ollama-model qwen2.5:3b --ollama-sample-limit 150
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
ChronoFact-AgentBench/
├── docs/
├── paper/                 # LaTeX source and PDF of the paper
├── results/               # agent predictions, tool traces and the paired analysis
├── scripts/analyse_agents.py
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

## How to cite

```bibtex
@misc{hussain2026chronofact,
  author    = {Hussain, Muzammal},
  title     = {{Give the Model the Overlap, Not the Dates: Tool Evidence for Checking Time-Qualified Claims with Small Local Models}},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.24468882},
  url       = {https://doi.org/10.5281/zenodo.24468882}
}
```

Software (code, notebooks, results): [doi:10.5281/zenodo.24356041](https://doi.org/10.5281/zenodo.24356041).

