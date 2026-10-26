# Docs-agent judge Pareto — y = Signal value (accuracy x repeatability, all evals)

8 judges over 3 to 20 repetitions x 22 cases. A judge is on a front when no other judge is at least as good on quality and at least as cheap (or fast). The majority baseline costs nothing and takes no time, so it is a reference line rather than a point.

Jev answers the three evals of a case in one call; LLM judges make one call per eval. Per-call cost: jev $0.00047, gpt-5.6-luna $0.00038.

| judge | signal | modal acc | s/call p50 | USD/call | USD/decision (list price) | on front (speed) | on front (cost) |
|---|---|---|---|---|---|---|---|
| jev | 0.741 | 0.742 | 0.70 | 0.00047 | 0.00016 | yes | yes |
| deepseek-v4.1-flash | 0.690 | 0.742 | 3.53 | 0.00127 | 0.00371 | no | no |
| gemini-3.8-flash | 0.800 | 0.818 | 2.85 | 0.00506 | 0.00954 | yes | yes |
| gpt-5.6-luna | 0.695 | 0.758 | 3.11 | 0.00038 | 0.00209 | no | no |
| gemini-3.8-flash (matched) | 0.742 | 0.758 | 2.30 | 0.00415 | 0.00852 | yes | yes |
| gpt-5.6-luna (matched) | 0.686 | 0.742 | 3.48 | 0.00047 | 0.00209 | no | no |
| claude-opus-5 (sota) | 0.798 | 0.833 | 6.70 | 0.08222 | 0.08222 | no | no |
| gpt-5.6-sol (sota) | 0.718 | 0.758 | 5.41 | 0.01782 | 0.04014 | no | no |
| baseline(majority) | 0.561 | 0.561 | 0.00 | 0.00000 | 0.00000 | reference line | reference line |
