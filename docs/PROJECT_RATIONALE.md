# Project rationale and portfolio-overlap check

## Selected domain

Digital humanities / temporal knowledge representation / Agentic AI.

## Research problem

A factual relation can be true only during a bounded period. Language models may remember a subject-relation-object association but fail to respect the date attached to a question. TimeStress was designed to measure this temporal-context weakness. ChronoFact-AgentBench asks a narrower systems question: does an agent that calls explicit date and interval tools classify temporal contexts more reliably than a text-only model, and how does that behavior vary by date precision and partial boundary overlap?

## Portfolio-overlap review

The known portfolio includes agent memory integrity and security, tool-policy/reliability work, cancellation and retry propagation, decomposition granularity, healthcare operations, Pakistan flood/heat projects, and ExoVet-AgentBench's budgeted evidence acquisition for Kepler candidate vetting.

ChronoFact-AgentBench does not extend those systems. It uses a separate historical knowledge-graph task and a different evaluation axis: temporal interval semantics, precision, and partial overlap. It does not perform memory-security testing, generic tool-policy testing, resource allocation, exoplanet classification, healthcare workflow management, or cross-lingual retrieval.

## Literature and dataset fit

- TimeStress directly measures language-model consistency under date-context variation and supplies labeled year/month/day contexts.
- MusTQ demonstrates that temporal knowledge-graph QA includes multi-step temporal reasoning beyond static fact lookup.
- WhenFactsExpire supplies another temporal fact-validation dataset derived from Wikidata, showing that temporal validity is an established research problem.

The selected project is an agentic evaluation harness built on these foundations. No claim is made that temporal fact validation itself is new, or that this project is the first temporal agent benchmark.

## Feasibility

The TimeStress Parquet file is reported at approximately 11.5 MB. The core benchmark requires pandas and PyArrow, and its deterministic interval policy runs on CPU. Ollama is optional and restricted to a small sample to fit a 16 GB MacBook Air. The source data is not bundled in the ZIP; the downloader pins a file revision and verifies its SHA-256.
