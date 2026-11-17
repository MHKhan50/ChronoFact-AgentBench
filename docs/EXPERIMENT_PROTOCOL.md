# Experiment protocol

## Primary run

1. Download the pinned `Orange/TimeStress` `train.parquet` file using the CLI.
2. Verify the expected SHA-256 (`93df1d4782f770b38d1eda00acb5aa9d97c9a863fd6921fecb6f310052ffa59a`).
3. Prepare the CSV; preserve the generated manifest.
4. Run the full deterministic benchmark with seed 17 and no `--max-samples` cap.
5. Archive `metrics.csv`, `predictions.csv`, `run_metadata.json`, and `summary.md`.

## Optional local-model run

1. Record `ollama --version` and `ollama list` output separately.
2. Run the paired text-only and tool-agent evaluation with the same model tag and a sample limit of 50 initially.
3. Report the actual number of successfully evaluated rows. If the Ollama endpoint fails, retain the error in metadata; do not present missing LLM results as successful evaluations.
4. If increasing the sample limit, report the exact limit and model tag. Do not compare runs with different sample compositions as if they were paired.

## Statistical reporting

- Report row count and unique `fact_id` count.
- Report all three class counts and all three precision groups.
- Report coverage and selective accuracy together for any LLM policy.
- Report `transitional` F1 separately.
- Do not treat repeated contexts for one fact as independent observations in inferential tests. If confidence intervals are added later, resample at the `fact_id` cluster level.
- Keep the interval-rule policy clearly labeled as a deterministic reference.

## Reproducibility record

Retain the raw dataset SHA-256, prepared CSV SHA-256, project version, Python version, pandas version, seed, Ollama model tag, and Ollama version. Do not overwrite a prior run directory; use a new output directory for a new configuration.
