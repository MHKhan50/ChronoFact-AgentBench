# Limitations and ethics

## Dataset limitations

- TimeStress is English-only and focuses on popular facts.
- Its facts are historical and were selected from a Wikidata snapshot; Wikidata is collaborative and may contain errors, omissions, or contested interpretations.
- The natural-language questions were generated with GPT-4o and manually inspected on a small sample, as described by the dataset authors. Generated wording may introduce artifacts.
- The benchmark supplies validity intervals. It does not independently verify the evidence used to create those intervals.
- The data card reports three semantic classes, but software normalizes case and whitespace and rejects unrecognized labels rather than silently coercing them.

## Model limitations

- Local model behavior depends on model tag, quantization, Ollama version, prompt formatting, and machine load.
- A small local model may fail to follow the JSON tool protocol. Invalid actions and abstentions are measured, not hidden.
- Tool access exposes the date interval already present in the dataset. It tests structured temporal reasoning, not open-web retrieval or provenance discovery.
- The deterministic interval-rule policy is a reference derived directly from the task definition; it is not evidence that a learned agent has solved historical fact checking.

## Ethical use

- Use the output as a research diagnostic, not as an authoritative historical verdict.
- For disputed or culturally sensitive history, consult primary sources and qualified historians.
- Do not use the benchmark to rank cultures, ethnicities, religions, or political communities.
- The dataset contains public knowledge-graph facts and generated statements; no personal user data is required.
- Attribute TimeStress and preserve its CC BY-SA 4.0 terms when redistributing modified dataset material. The project source code is separately licensed under MIT.
