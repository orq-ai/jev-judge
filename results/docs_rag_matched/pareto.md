# Docs-agent judge Pareto — y = Signal value (accuracy x repeatability, all evals)

7 judges over 100 repetitions x 12 cases. A judge is on a front when no other judge is at least as good on quality and at least as cheap (or fast). The majority baseline costs nothing and takes no time, so it is a reference line rather than a point.

Jev answers the three evals of a case in one call; LLM judges make one call per eval. Per-call cost: jev $0.00049, gpt-5.6-luna (matched) $0.00042.

| judge | signal | modal acc | s/call p50 | USD/call | USD/decision | on front (speed) | on front (cost) |
|---|---|---|---|---|---|---|---|
| jev | 0.887 | 0.889 | 0.43 | 0.00049 | 0.00016 | yes | yes |
| deepseek-v4.1-flash | 0.787 | 0.861 | 3.59 | 0.00117 | 0.00117 | no | no |
| gemini-3.8-flash | 0.806 | 0.806 | 2.06 | 0.00455 | 0.00455 | no | no |
| gpt-5.6-luna | 0.705 | 0.778 | 2.80 | 0.00042 | 0.00042 | no | no |
| jev (matched) | 0.887 | 0.889 | 0.39 | 0.00049 | 0.00016 | yes | no |
| gemini-3.8-flash (matched) | 0.803 | 0.806 | 1.42 | 0.00377 | 0.00377 | no | no |
| gpt-5.6-luna (matched) | 0.713 | 0.833 | 2.65 | 0.00042 | 0.00042 | no | no |
| baseline(majority) | 0.806 | 0.806 | 0.00 | 0.00000 | 0.00000 | reference line | reference line |
