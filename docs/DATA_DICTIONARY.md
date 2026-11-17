# Data dictionary

The source dataset is `Orange/TimeStress`, distributed as a Parquet file under CC BY-SA 4.0. The project ZIP does not redistribute the data.

| Field | Meaning | Use in this project |
|---|---|---|
| `SubjectID` | Wikidata subject identifier | Fact grouping and audit only |
| `SubjectLabel` | Human-readable subject label | Descriptive metadata |
| `RelationID` | Wikidata property identifier | Fact grouping and audit only |
| `RelationLabel` | Human-readable relation | Descriptive metadata |
| `ObjectID` | Wikidata object identifier | Fact grouping and audit only |
| `ObjectLabel` | Human-readable object label | Descriptive metadata |
| `StartDate` | Start of the fact validity interval | Tool input |
| `EndDate` | End of the fact validity interval | Tool input |
| `FactPop` | Popularity index reported by dataset authors | Descriptive analysis only |
| `Time` | Context date, year, year-month, or day | Tool input |
| `Alpha` | Relative temporal position feature | Excluded from prediction inputs; analysis only |
| `Status` | Original target label | Normalized into `label`; not a model input |
| `Statement` | Generated natural-language question/answer with temporal context | Text-only model input |
| `label` | Canonical lower-case target: correct/incorrect/transitional | Evaluation target |
| `granularity` | year/month/day inferred from `Time` | Subgroup metric |
| `fact_id` | `SubjectID|RelationID|ObjectID` | Repeated-fact grouping key |

The source dataset card states 523,764 rows, 2,003 temporal facts, 1,883 unique entities, and 86 relations. Counts from the downloaded file are re-computed and written to the preparation manifest rather than hard-coded as experimental output.
