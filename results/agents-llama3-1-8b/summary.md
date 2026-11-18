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
                  ollama_text        150         150  1.000000  0.460000            0.460000           0.460000  0.416173    0.496350      0.588235         0.163934       0.304878        0.647059      0.647059              0.0                0
            ollama_tool_dates        150          71  0.473333  0.300000            0.633803           0.300000  0.360501    0.557692      0.111111         0.412698       0.317073        0.352941      0.205882              2.0               79
          ollama_tool_overlap        150         133  0.886667  0.886667            1.000000           0.886667  0.931727    1.000000      0.795181         1.000000       0.926829        0.823529      0.852941              2.0               17
interval_rule_on_agent_sample        150         150  1.000000  1.000000            1.000000           1.000000  1.000000    1.000000      1.000000         1.000000       1.000000        1.000000      1.000000              0.0                0

## Interpretation boundary

The target is the TimeStress temporal-context label. It is not an independent fact-check of the underlying historical claim.