# ChronoFact-AgentBench experiment summary

Generated from the actual run. No performance results are pre-filled.

- Rows used: 500108
- Unique fact groups: 1982
- Seed: 17
- Ollama included: True

## Metrics

                       policy  n_samples  n_answered  coverage  accuracy  selective_accuracy  balanced_accuracy  macro_f1  correct_f1  incorrect_f1  transitional_f1  accuracy_year  accuracy_month  accuracy_day  mean_tool_calls  invalid_actions
                     majority     500108      500108  1.000000  0.863699            0.863699           0.333333  0.308955    0.000000      0.926866         0.000000       0.858501        0.866322      0.866322         0.000000                0
                interval_rule     500108      500108  1.000000  1.000000            1.000000           1.000000  1.000000    1.000000      1.000000         1.000000       1.000000        1.000000      1.000000         0.000000                0
                  ollama_text        150         150  1.000000  0.353333            0.353333           0.353333  0.223976    0.161290      0.510638         0.000000       0.207317        0.529412      0.529412         0.000000                0
            ollama_tool_dates        150         149  0.993333  0.413333            0.416107           0.413333  0.315140    0.327869      0.543478         0.074074       0.268293        0.617647      0.558824         1.993333                1
          ollama_tool_overlap        150         149  0.993333  0.986667            0.993289           0.986667  0.989966    0.989899      0.990099         0.989899       0.987805        0.970588      1.000000         1.993333                1
interval_rule_on_agent_sample        150         150  1.000000  1.000000            1.000000           1.000000  1.000000    1.000000      1.000000         1.000000       1.000000        1.000000      1.000000         0.000000                0

## Interpretation boundary

The target is the TimeStress temporal-context label. It is not an independent fact-check of the underlying historical claim.