# Docs-agent judge benchmark — `docs_rag`

12 frozen cases x 100 repetitions (every cell has the same repetition count), 4 judges, evals: abstain_ok, grounded, quality.

### Table A — Binary accuracy vs the labels

Correct decisions over all (case x repetition) decisions. A failed call counts as incorrect. `baseline(majority)` always answers the most common gold value of the eval.

Gold distribution over the 12 cases — **abstain_ok**: 11 true / 1 false; **grounded**: 11 true / 1 false; **quality**: 7 level 4 / 4 level 3 / 1 level 1.

| Judge | abstain_ok | grounded | pooled | failed calls (all evals) |
|---|---|---|---|---|
| jev | 99.8% (1197/1200) | 100.0% (1200/1200) | 99.9% (2397/2400) | 0 |
| deepseek-v4.1-flash | 91.7% (1100/1200) | 90.5% (1086/1200) | 91.1% (2186/2400) | 4 |
| gemini-3.8-flash | 92.1% (1105/1200) | 91.6% (1099/1200) | 91.8% (2204/2400) | 0 |
| gpt-5.6-luna | 90.8% (1090/1200) | 86.7% (1040/1200) | 88.8% (2130/2400) | 0 |
| baseline(majority) | 91.7% (1100/1200) | 91.7% (1100/1200) | 91.7% (2200/2400) | 0 |

### Table A1 — Modal-verdict accuracy (cases whose most common answer matches the label)

One vote per case: the modal answer over repetitions, scored against the label. This is what a single production draw most likely returns; Table A charges every unstable repetition against accuracy, which flatters a judge that is stable and wrong.

| Judge | abstain_ok | grounded | quality |
|---|---|---|---|
| jev | 12/12 | 12/12 | 8/12 |
| deepseek-v4.1-flash | 11/12 | 11/12 | 9/12 |
| gemini-3.8-flash | 11/12 | 11/12 | 7/12 |
| gpt-5.6-luna | 10/12 | 11/12 | 7/12 |
| baseline(majority) | 11/12 | 11/12 | 7/12 |

### Table A2 — Failed calls per eval

A failed call returned no prediction (retries exhausted, or the reasoning overflowed `max_tokens`).

| Judge | abstain_ok | grounded | quality | total |
|---|---|---|---|---|
| jev | 0 | 0 | 0 | 0 |
| deepseek-v4.1-flash | 1 | 1 | 2 | 4 |
| gemini-3.8-flash | 0 | 0 | 0 | 0 |
| gpt-5.6-luna | 0 | 0 | 0 | 0 |

### Table B — quality variance across repetitions

`quality` normalised to 0-1 (pred/4), population variance per case, averaged over cases. Failed calls are excluded from the values and reported in the last column. A judge with zero variance has no worst case, so the column reads `-`.

| Judge | mean per-case variance | x Jev | worst case | worst-case variance | failed calls |
|---|---|---|---|---|---|
| jev | 0.00000 | n/a (Jev variance 0) | - | 0.00000 | 0.0% |
| deepseek-v4.1-flash | 0.00653 | n/a (Jev variance 0) | q11 | 0.01742 | 0.2% |
| gemini-3.8-flash | 0.00066 | n/a (Jev variance 0) | q06 | 0.00797 | 0.0% |
| gpt-5.6-luna | 0.00670 | n/a (Jev variance 0) | q07 | 0.04107 | 0.0% |

### Table B2 — per-case quality variance

| Case | jev | deepseek-v4.1-flash | gemini-3.8-flash | gpt-5.6-luna |
|---|---|---|---|---|
| q01 | 0.00000 | 0.00122 | 0.00000 | 0.00297 |
| q02 | 0.00000 | 0.00182 | 0.00000 | 0.00000 |
| q03 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| q04 | 0.00000 | 0.00562 | 0.00000 | 0.00122 |
| q05 | 0.00000 | 0.01000 | 0.00000 | 0.00122 |
| q05v1 | 0.00000 | 0.01482 | 0.00000 | 0.01382 |
| q06 | 0.00000 | 0.00478 | 0.00797 | 0.00182 |
| q07 | 0.00000 | 0.00352 | 0.00000 | 0.04107 |
| q08 | 0.00000 | 0.00352 | 0.00000 | 0.00122 |
| q09 | 0.00000 | 0.00000 | 0.00000 | 0.00122 |
| q10 | 0.00000 | 0.01562 | 0.00000 | 0.01202 |
| q11 | 0.00000 | 0.01742 | 0.00000 | 0.00375 |

### Table C — Cost per call and per decision, latency per call

A decision is one (case, eval, repetition). The LLM judges make one call per decision; Jev answers all evals of a case in one classify call, so its calls are a third of its decisions. Latency is measured per request, so mean, p50 and p95 are over physical calls — but runs recorded before 2026-09-20 stored the per-cell mean on every repetition row, and their percentiles are percentiles of those means. Latency was measured with the three LLM judges at 6 in-flight calls each and Jev on an 8-thread pool, all from one laptop.

| Judge | physical calls | decisions | USD/call | USD/decision | s/call | s/call p50 | s/call p95 | total USD |
|---|---|---|---|---|---|---|---|---|
| jev | 1200 | 3600 | 0.00049 | 0.00016 | 0.44 | 0.43 | 0.61 | 0.5875 |
| deepseek-v4.1-flash | 3600 | 3600 | 0.00117 | 0.00117 | 4.59 | 3.59 | 8.79 | 4.2267 |
| gemini-3.8-flash | 3600 | 3600 | 0.00455 | 0.00455 | 2.09 | 2.06 | 2.91 | 16.3827 |
| gpt-5.6-luna | 3600 | 3600 | 0.00042 | 0.00042 | 2.96 | 2.80 | 4.18 | 1.5289 |

### Table C2 — Cost per 1,000 traces (extrapolated from this run)

A trace is one frozen agent run judged on all 3 evals once; the frozen states average 30,018 characters of parsed conversation and search results. USD/trace is this run's total spend divided by its (case x repetition) count and multiplied out linearly, so it assumes the same trace length and the same prices. Repeating one state many times is what a provider prompt cache rewards, so the billed figure understates a judge whose input was largely cached (`cached input`); the list-price column reprices the mean tokens per call at the model's uncached USD per million and is the number to use for 1,000 distinct traces. Wall time per trace is the mean latency of one call, since the LLM judges' 3 calls per trace run in parallel; serial is the sum. Token columns are `-` on runs recorded before per-call token usage was stored. List prices (USD per million input / output tokens, Orq router, 2026-09-20): gpt-5.6-luna 0.2 / 1.2, gpt-5.6-sol 4 / 20, claude-opus-5 5 / 25, gemini-3.8-flash 0.75 / 3.75, deepseek-v4.1-flash 0.3 / 1.2.

| Judge | calls/trace | USD/trace | USD/1,000 traces (billed) | USD/1,000 traces (list price) | cached input | wall s/trace | serial s/trace | input tokens/call |
|---|---|---|---|---|---|---|---|---|
| jev | 1 | 0.00049 | 0.49 | - | - | 0.44 | 0.44 | - |
| deepseek-v4.1-flash | 3 | 0.00352 | 3.52 | - | - | 4.59 | 13.76 | - |
| gemini-3.8-flash | 3 | 0.01365 | 13.65 | - | - | 2.09 | 6.27 | - |
| gpt-5.6-luna | 3 | 0.00127 | 1.27 | - | - | 2.96 | 8.88 | - |

### Table D — Signal value (label agreement x repeatability)

Repeatability = share of repetitions matching the modal answer, averaged over cases; a failed call is a non-modal vote. Score evals are treated as exact-match categorical. `baseline(majority)` is constant, so its repeatability is 100% by construction.

| Judge | Eval | label agreement | repeatability | signal value |
|---|---|---|---|---|
| jev | abstain_ok | 99.8% | 99.8% | 0.995 |
| jev | grounded | 100.0% | 100.0% | 1.000 |
| jev | binary_pooled | 99.9% | 99.9% | 0.998 |
| jev | quality | 66.7% | 100.0% | 0.667 |
| deepseek-v4.1-flash | abstain_ok | 91.7% | 99.8% | 0.915 |
| deepseek-v4.1-flash | grounded | 90.5% | 98.4% | 0.891 |
| deepseek-v4.1-flash | binary_pooled | 91.1% | 99.1% | 0.903 |
| deepseek-v4.1-flash | quality | 66.6% | 86.3% | 0.575 |
| gemini-3.8-flash | abstain_ok | 92.1% | 99.6% | 0.917 |
| gemini-3.8-flash | grounded | 91.6% | 99.9% | 0.915 |
| gemini-3.8-flash | binary_pooled | 91.8% | 99.8% | 0.916 |
| gemini-3.8-flash | quality | 59.6% | 98.8% | 0.588 |
| gpt-5.6-luna | abstain_ok | 90.8% | 92.5% | 0.840 |
| gpt-5.6-luna | grounded | 86.7% | 88.0% | 0.763 |
| gpt-5.6-luna | binary_pooled | 88.8% | 90.2% | 0.801 |
| gpt-5.6-luna | quality | 57.9% | 88.8% | 0.514 |
| baseline(majority) | abstain_ok | 91.7% | 100.0% | 0.917 |
| baseline(majority) | grounded | 91.7% | 100.0% | 0.917 |
| baseline(majority) | binary_pooled | 91.7% | 100.0% | 0.917 |
| baseline(majority) | quality | 58.3% | 100.0% | 0.583 |

### Table E — Unstable cases (modal answer below 100% of reps)

Vote counts sum to the 100 repetitions; `failed:N` is a call that returned no prediction.

| Judge | Eval | unstable cases | vote distribution |
|---|---|---|---|
| jev | abstain_ok | 1 | q05v1 {false:97, true:3} |
| jev | grounded | 0 | - |
| jev | quality | 0 | - |
| deepseek-v4.1-flash | abstain_ok | 2 | q05v1 {true:99, false:1}, q06 {true:99, failed:1} |
| deepseek-v4.1-flash | grounded | 6 | q05v1 {true:97, false:2, failed:1}, q06 {true:91, false:9}, q07 {true:98, false:2}, q08 {true:99, false:1}, q10 {true:99, false:1}, q11 {true:97, false:3} |
| deepseek-v4.1-flash | quality | 10 | q01 {4:98, 3:2}, q02 {4:97, 3:3}, q04 {4:90, 3:10}, q05 {4:80, 3:20}, q05v1 {2:74, 3:23, 1:2, 4:1}, q06 {2:92, 3:7, 1:1}, q07 {4:94, 3:6}, q08 {4:94, 3:6}, q10 {3:50, 4:50}, q11 {3:67, 2:25, 4:6, failed:2} |
| gemini-3.8-flash | abstain_ok | 1 | q05v1 {true:95, false:5} |
| gemini-3.8-flash | grounded | 1 | q11 {true:99, false:1} |
| gemini-3.8-flash | quality | 1 | q06 {4:85, 3:15} |
| gpt-5.6-luna | abstain_ok | 2 | q05v1 {true:55, false:45}, q07 {false:55, true:45} |
| gpt-5.6-luna | grounded | 7 | q02 {true:98, false:2}, q04 {true:99, false:1}, q05v1 {true:58, false:42}, q06 {true:96, false:4}, q07 {true:57, false:43}, q10 {true:98, false:2}, q11 {true:50, false:50} |
| gpt-5.6-luna | quality | 10 | q01 {4:95, 3:5}, q04 {4:98, 3:2}, q05 {4:98, 3:2}, q05v1 {2:67, 3:33}, q06 {2:97, 3:3}, q07 {2:47, 3:29, 4:24}, q08 {4:98, 3:2}, q09 {4:98, 3:2}, q10 {3:74, 4:26}, q11 {2:94, 1:3, 3:3} |

### Table F — Per-case verdicts (modal answer and agreement)

`modal (agreement, votes)`; vote counts sum to the 100 repetitions.

| Case | Eval | gold | jev | deepseek-v4.1-flash | gemini-3.8-flash | gpt-5.6-luna |
|---|---|---|---|---|---|---|
| q01 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q01 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q01 | quality | 4 | 4 (100.0%, 4:100) | 4 (98.0%, 4:98, 3:2) | 4 (100.0%, 4:100) | 4 (95.0%, 4:95, 3:5) |
| q02 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q02 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (98.0%, true:98, false:2) |
| q02 | quality | 4 | 4 (100.0%, 4:100) | 4 (97.0%, 4:97, 3:3) | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) |
| q03 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q03 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q03 | quality | 4 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) |
| q04 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q04 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (99.0%, true:99, false:1) |
| q04 | quality | 3 | 4 (100.0%, 4:100) | 4 (90.0%, 4:90, 3:10) | 4 (100.0%, 4:100) | 4 (98.0%, 4:98, 3:2) |
| q05 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q05 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q05 | quality | 4 | 4 (100.0%, 4:100) | 4 (80.0%, 4:80, 3:20) | 4 (100.0%, 4:100) | 4 (98.0%, 4:98, 3:2) |
| q05v1 | abstain_ok | false | false (97.0%, false:97, true:3) | true (99.0%, true:99, false:1) | true (95.0%, true:95, false:5) | true (55.0%, true:55, false:45) |
| q05v1 | grounded | false | false (100.0%, false:100) | true (97.0%, true:97, false:2, failed:1) | true (100.0%, true:100) | true (58.0%, true:58, false:42) |
| q05v1 | quality | 1 | 3 (100.0%, 3:100) | 2 (74.0%, 2:74, 3:23, 1:2, 4:1) | 4 (100.0%, 4:100) | 2 (67.0%, 2:67, 3:33) |
| q06 | abstain_ok | true | true (100.0%, true:100) | true (99.0%, true:99, failed:1) | true (100.0%, true:100) | true (100.0%, true:100) |
| q06 | grounded | true | true (100.0%, true:100) | true (91.0%, true:91, false:9) | true (100.0%, true:100) | true (96.0%, true:96, false:4) |
| q06 | quality | 3 | 2 (100.0%, 2:100) | 2 (92.0%, 2:92, 3:7, 1:1) | 4 (85.0%, 4:85, 3:15) | 2 (97.0%, 2:97, 3:3) |
| q07 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | false (55.0%, false:55, true:45) |
| q07 | grounded | true | true (100.0%, true:100) | true (98.0%, true:98, false:2) | true (100.0%, true:100) | true (57.0%, true:57, false:43) |
| q07 | quality | 4 | 4 (100.0%, 4:100) | 4 (94.0%, 4:94, 3:6) | 4 (100.0%, 4:100) | 2 (47.0%, 2:47, 3:29, 4:24) |
| q08 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q08 | grounded | true | true (100.0%, true:100) | true (99.0%, true:99, false:1) | true (100.0%, true:100) | true (100.0%, true:100) |
| q08 | quality | 4 | 4 (100.0%, 4:100) | 4 (94.0%, 4:94, 3:6) | 4 (100.0%, 4:100) | 4 (98.0%, 4:98, 3:2) |
| q09 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q09 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q09 | quality | 4 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (98.0%, 4:98, 3:2) |
| q10 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q10 | grounded | true | true (100.0%, true:100) | true (99.0%, true:99, false:1) | true (100.0%, true:100) | true (98.0%, true:98, false:2) |
| q10 | quality | 3 | 3 (100.0%, 3:100) | 3 (50.0%, 3:50, 4:50) | 4 (100.0%, 4:100) | 3 (74.0%, 3:74, 4:26) |
| q11 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q11 | grounded | true | true (100.0%, true:100) | true (97.0%, true:97, false:3) | true (99.0%, true:99, false:1) | true (50.0%, true:50, false:50) |
| q11 | quality | 3 | 2 (100.0%, 2:100) | 3 (67.0%, 3:67, 2:25, 4:6, failed:2) | 4 (100.0%, 4:100) | 2 (94.0%, 2:94, 1:3, 3:3) |
