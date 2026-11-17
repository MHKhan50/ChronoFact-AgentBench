# Methodology

## 1. Task definition

Each TimeStress row represents a temporal fact `(subject, relation, object)` with a validity interval `[StartDate, EndDate]` and a query context `Time`. The target `Status` has three documented values:

- `correct`: the entire context interval is contained in the fact interval;
- `incorrect`: the context interval does not overlap the fact interval;
- `transitional`: the context interval partially overlaps the fact interval.

The benchmark expands a year to 1 January–31 December, a year-month to the first–last day of that month, and a day to a single calendar day. Intervals are inclusive.

## 2. Agent tools

The optional local agent uses a constrained plan-act-observe-finalize loop:

1. `get_fact_interval` retrieves the fact's declared start and end dates from the benchmark row.
2. `compare_context` parses the context precision and returns interval endpoints, duration, overlap days, containment flags, and gap days.
3. The model returns one of the three labels with a confidence value.

The tool observation deliberately omits `Status` and `Alpha`. The agent must not receive the target label or the dataset's relative-position feature.

## 3. Baselines

### Majority baseline

Predicts the most frequent class in the evaluation frame. It is an in-sample class-prior reference, not a deployable predictor or learned model; report it only as a weak prevalence reference.

### Interval-rule reference

Uses only the date fields and exact inclusive interval arithmetic. Since the TimeStress labels are defined from interval relationships, this is an algorithmic reference and may be close to a deterministic ceiling. It is not presented as a learned AI system.

### Text-only local model

An optional Ollama model receives only the natural-language statement and must classify from its learned knowledge. It has no interval tools.

### Tool-using local agent

The same local model is asked to use the two structured tools before classifying. Invalid tool actions and abstentions are retained in the metrics.

## 4. Leakage controls

- `Status` is the target and is never included in prompts.
- `Alpha` is a derived relative-position value and is excluded from all model inputs.
- `SubjectID`, `RelationID`, and `ObjectID` are used only to construct `fact_id` for grouping and audit trails.
- The text-only model sees the statement text only.
- The tool agent sees the statement and stable identifiers first; interval values are returned only through the tool interface.

## 5. Analysis dimensions

Results are reported overall and by temporal precision (`year`, `month`, `day`). The `transitional` class is reported separately because partial overlap is a distinct boundary condition. Rows sharing the same `(SubjectID, RelationID, ObjectID)` are treated as repeated contexts for one fact; they are not independent facts.

## 6. Metrics

Accuracy counts abstentions as incorrect. Selective accuracy is computed only among answered cases, while coverage is the proportion receiving a valid label. Balanced accuracy and macro-F1 prevent the most common class from dominating the report. Tool-call and invalid-action counts measure agent overhead and protocol adherence.

## 7. What the benchmark does not establish

It does not verify the historical correctness of the underlying Wikidata statement, assess source quality, resolve disputed dates, or test open-domain retrieval. It evaluates consistency with the validity interval supplied in TimeStress.
