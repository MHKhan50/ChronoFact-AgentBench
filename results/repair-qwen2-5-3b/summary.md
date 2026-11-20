# ChronoFact-AgentBench experiment summary

Generated from the actual run. No performance results are pre-filled.

- Rows used: 500108
- Unique fact groups: 1982
- Seed: 17
- Ollama included: True

## Metrics

                       policy  n_samples  n_answered  coverage  accuracy  selective_accuracy  balanced_accuracy  macro_f1  correct_f1  incorrect_f1  transitional_f1  accuracy_year  accuracy_month  accuracy_day  mean_tool_calls  invalid_actions
                     majority     500108      500108      1.00  0.863699            0.863699           0.333333  0.308955    0.000000      0.926866         0.000000       0.858501        0.866322      0.866322              0.0                0
                interval_rule     500108      500108      1.00  1.000000            1.000000           1.000000  1.000000    1.000000      1.000000         1.000000       1.000000        1.000000      1.000000              0.0                0
      ollama_tool_code_repair        150           6      0.04  0.013333            0.333333           0.013333  0.025892    0.039216      0.000000         0.038462       0.024390        0.000000      0.000000              2.0              213
interval_rule_on_agent_sample        150         150      1.00  1.000000            1.000000           1.000000  1.000000    1.000000      1.000000         1.000000       1.000000        1.000000      1.000000              0.0                0

## Interpretation boundary

The target is the TimeStress temporal-context label. It is not an independent fact-check of the underlying historical claim.