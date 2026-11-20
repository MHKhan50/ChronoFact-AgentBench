# ChronoFact-AgentBench experiment summary

Generated from the actual run. No performance results are pre-filled.

- Rows used: 500108
- Unique fact groups: 1982
- Seed: 17
- Ollama included: True

## Metrics

                       policy  n_samples  n_answered  coverage  accuracy  selective_accuracy  balanced_accuracy  macro_f1  correct_f1  incorrect_f1  transitional_f1  accuracy_year  accuracy_month  accuracy_day  mean_tool_calls  invalid_actions
                     majority     500108      500108  1.000000  0.863699            0.863699           0.333333  0.308955    0.000000      0.926866         0.000000       0.858501        0.866322      0.866322              0.0                0
                interval_rule     500108      500108  1.000000  1.000000            1.000000           1.000000  1.000000    1.000000      1.000000         1.000000       1.000000        1.000000      1.000000              0.0                0
      ollama_tool_code_repair        150         110  0.733333  0.313333            0.427273           0.313333  0.358030    0.428571      0.346667         0.298851       0.292683        0.294118      0.382353              2.0              185
interval_rule_on_agent_sample        150         150  1.000000  1.000000            1.000000           1.000000  1.000000    1.000000      1.000000         1.000000       1.000000        1.000000      1.000000              0.0                0

## Interpretation boundary

The target is the TimeStress temporal-context label. It is not an independent fact-check of the underlying historical claim.