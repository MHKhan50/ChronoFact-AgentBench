| Model | Condition | Accuracy % [95% CI] | Coverage % | Selective acc. % | Lenient acc. % |
|---|---|---|---|---|---|
| qwen2.5:3b | Text only | 35.3 [22.8, 47.2] | 100.0 | 35.3 | 35.3 |
| qwen2.5:3b | Tool: dates | 41.3 [29.2, 52.7] | 99.3 | 41.6 | 41.3 |
| qwen2.5:3b | Tool: dates + overlap flags | 98.7 [96.6, 100.0] | 99.3 | 99.3 | 98.7 |
| llama3.1:8b | Text only | 46.0 [33.8, 57.7] | 100.0 | 46.0 | 46.0 |
| llama3.1:8b | Tool: dates | 30.0 [21.0, 39.7] | 47.3 | 63.4 | 72.0 |
| llama3.1:8b | Tool: dates + overlap flags | 88.7 [80.9, 95.6] | 88.7 | 100.0 | 100.0 |

| Model | Comparison | Only first right | Only second right | McNemar p |
|---|---|---|---|---|
| qwen2.5:3b | tool_dates vs text | 11 | 2 | 0.022 |
| qwen2.5:3b | tool_overlap vs tool_dates | 86 | 0 | 2.6e-26 |
| qwen2.5:3b | tool_overlap vs text | 95 | 0 | 5e-29 |
| llama3.1:8b | tool_dates vs text | 22 | 46 | 0.0049 |
| llama3.1:8b | tool_overlap vs tool_dates | 88 | 0 | 6.5e-27 |
| llama3.1:8b | tool_overlap vs text | 74 | 10 | 3.3e-13 |

Lenient scoring:

| Model | Comparison | Only first right | Only second right | McNemar p |
|---|---|---|---|---|
| qwen2.5:3b | tool_dates vs text | 11 | 2 | 0.022 |
| qwen2.5:3b | tool_overlap vs tool_dates | 86 | 0 | 2.6e-26 |
| qwen2.5:3b | tool_overlap vs text | 95 | 0 | 5e-29 |
| llama3.1:8b | tool_dates vs text | 47 | 8 | 8.1e-08 |
| llama3.1:8b | tool_overlap vs tool_dates | 42 | 0 | 4.5e-13 |
| llama3.1:8b | tool_overlap vs text | 81 | 0 | 8.3e-25 |
