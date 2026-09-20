# Docs-agent judge benchmark — `docs_rag_matched`

12 frozen cases x 100 repetitions (every cell has the same repetition count), 3 judges, evals: abstain_ok, grounded, quality.

### Table A — Binary accuracy vs the labels

Correct decisions over all (case x repetition) decisions. A failed call counts as incorrect. `baseline(majority)` always answers the most common gold value of the eval.

Gold distribution over the 12 cases — **abstain_ok**: 11 true / 1 false; **grounded**: 11 true / 1 false; **quality**: 7 level 4 / 4 level 3 / 1 level 1.

| Judge | abstain_ok | grounded | pooled | failed calls (all evals) |
|---|---|---|---|---|
| jev | 99.7% (1196/1200) | 100.0% (1200/1200) | 99.8% (2396/2400) | 0 |
| gemini-3.8-flash | 91.8% (1102/1200) | 91.7% (1100/1200) | 91.8% (2202/2400) | 0 |
| gpt-5.6-luna | 90.8% (1089/1200) | 89.8% (1078/1200) | 90.3% (2167/2400) | 0 |
| baseline(majority) | 91.7% (1100/1200) | 91.7% (1100/1200) | 91.7% (2200/2400) | 0 |

### Table A1 — Modal-verdict accuracy (cases whose most common answer matches the label)

One vote per case: the modal answer over repetitions, scored against the label. This is what a single production draw most likely returns; Table A charges every unstable repetition against accuracy, which flatters a judge that is stable and wrong.

| Judge | abstain_ok | grounded | quality |
|---|---|---|---|
| jev | 12/12 | 12/12 | 8/12 |
| gemini-3.8-flash | 11/12 | 11/12 | 7/12 |
| gpt-5.6-luna | 11/12 | 12/12 | 7/12 |
| baseline(majority) | 11/12 | 11/12 | 7/12 |

### Table A2 — Failed calls per eval

A failed call returned no prediction (retries exhausted, or the reasoning overflowed `max_tokens`).

| Judge | abstain_ok | grounded | quality | total |
|---|---|---|---|---|
| jev | 0 | 0 | 0 | 0 |
| gemini-3.8-flash | 0 | 0 | 0 | 0 |
| gpt-5.6-luna | 0 | 0 | 0 | 0 |

### Table B — quality variance across repetitions

`quality` normalised to 0-1 (pred/4), population variance per case, averaged over cases. Failed calls are excluded from the values and reported in the last column. A judge with zero variance has no worst case, so the column reads `-`.

| Judge | mean per-case variance | x Jev | worst case | worst-case variance | failed calls |
|---|---|---|---|---|---|
| jev | 0.00000 | n/a (Jev variance 0) | - | 0.00000 | 0.0% |
| gemini-3.8-flash | 0.00206 | n/a (Jev variance 0) | q06 | 0.01473 | 0.0% |
| gpt-5.6-luna | 0.00527 | n/a (Jev variance 0) | q07 | 0.01882 | 0.0% |

### Table B2 — per-case quality variance

| Case | jev | gemini-3.8-flash | gpt-5.6-luna |
|---|---|---|---|
| q01 | 0.00000 | 0.00000 | 0.00660 |
| q02 | 0.00000 | 0.00000 | 0.00000 |
| q03 | 0.00000 | 0.00000 | 0.00000 |
| q04 | 0.00000 | 0.00000 | 0.00000 |
| q05 | 0.00000 | 0.00000 | 0.00062 |
| q05v1 | 0.00000 | 0.01000 | 0.01162 |
| q06 | 0.00000 | 0.01473 | 0.00000 |
| q07 | 0.00000 | 0.00000 | 0.01882 |
| q08 | 0.00000 | 0.00000 | 0.00000 |
| q09 | 0.00000 | 0.00000 | 0.00122 |
| q10 | 0.00000 | 0.00000 | 0.01532 |
| q11 | 0.00000 | 0.00000 | 0.00907 |

### Table C — Cost per call and per decision, latency per call

A decision is one (case, eval, repetition). The LLM judges make one call per decision; Jev answers all evals of a case in one classify call, so its calls are a third of its decisions. Latency is measured per request, so mean, p50 and p95 are over physical calls — but runs recorded before 2026-09-20 stored the per-cell mean on every repetition row, and their percentiles are percentiles of those means. Latency was measured with the three LLM judges at 6 in-flight calls each and Jev on an 8-thread pool, all from one laptop.

| Judge | physical calls | decisions | USD/call | USD/decision | s/call | s/call p50 | s/call p95 | total USD |
|---|---|---|---|---|---|---|---|---|
| jev | 1200 | 3600 | 0.00049 | 0.00016 | 0.47 | 0.39 | 1.22 | 0.5875 |
| gemini-3.8-flash | 3600 | 3600 | 0.00377 | 0.00377 | 1.89 | 1.42 | 4.23 | 13.5724 |
| gpt-5.6-luna | 3600 | 3600 | 0.00042 | 0.00042 | 2.88 | 2.65 | 4.83 | 1.5257 |

### Table C2 — Cost per 1,000 traces (extrapolated from this run)

A trace is one frozen agent run judged on all 3 evals once; the frozen states average 30,018 characters of parsed conversation and search results. USD/trace is this run's total spend divided by its (case x repetition) count and multiplied out linearly, so it assumes the same trace length and the same prices. Repeating one state many times is what a provider prompt cache rewards, so the billed figure understates a judge whose input was largely cached (`cached input`); the list-price column reprices the mean tokens per call at the model's uncached USD per million and is the number to use for 1,000 distinct traces. Wall time per trace is the mean latency of one call, since the LLM judges' 3 calls per trace run in parallel; serial is the sum. Token columns are `-` on runs recorded before per-call token usage was stored. List prices (USD per million input / output tokens, Orq router, 2026-09-20): gpt-5.6-luna 0.2 / 1.2, gpt-5.6-sol 4 / 20, claude-opus-5 5 / 25, gemini-3.8-flash 0.75 / 3.75, deepseek-v4.1-flash 0.3 / 1.2.

| Judge | calls/trace | USD/trace | USD/1,000 traces (billed) | USD/1,000 traces (list price) | cached input | wall s/trace | serial s/trace | input tokens/call |
|---|---|---|---|---|---|---|---|---|
| jev | 1 | 0.00049 | 0.49 | - | - | 0.47 | 0.47 | - |
| gemini-3.8-flash | 3 | 0.01131 | 11.31 | 26.36 | 65.4% | 1.89 | 5.66 | 11,373 |
| gpt-5.6-luna | 3 | 0.00127 | 1.27 | 6.56 | 99.5% | 2.88 | 8.65 | 9,850 |

### Table D — Signal value (label agreement x repeatability)

Repeatability = share of repetitions matching the modal answer, averaged over cases; a failed call is a non-modal vote. Score evals are treated as exact-match categorical. `baseline(majority)` is constant, so its repeatability is 100% by construction.

| Judge | Eval | label agreement | repeatability | signal value |
|---|---|---|---|---|
| jev | abstain_ok | 99.7% | 99.7% | 0.993 |
| jev | grounded | 100.0% | 100.0% | 1.000 |
| jev | binary_pooled | 99.8% | 99.8% | 0.997 |
| jev | quality | 66.7% | 100.0% | 0.667 |
| gemini-3.8-flash | abstain_ok | 91.8% | 99.8% | 0.917 |
| gemini-3.8-flash | grounded | 91.7% | 100.0% | 0.917 |
| gemini-3.8-flash | binary_pooled | 91.8% | 99.9% | 0.917 |
| gemini-3.8-flash | quality | 61.5% | 95.2% | 0.585 |
| gpt-5.6-luna | abstain_ok | 90.8% | 93.1% | 0.845 |
| gpt-5.6-luna | grounded | 89.8% | 89.8% | 0.807 |
| gpt-5.6-luna | binary_pooled | 90.3% | 91.5% | 0.826 |
| gpt-5.6-luna | quality | 54.8% | 89.6% | 0.491 |
| baseline(majority) | abstain_ok | 91.7% | 100.0% | 0.917 |
| baseline(majority) | grounded | 91.7% | 100.0% | 0.917 |
| baseline(majority) | binary_pooled | 91.7% | 100.0% | 0.917 |
| baseline(majority) | quality | 58.3% | 100.0% | 0.583 |

### Table E — Unstable cases (modal answer below 100% of reps)

Vote counts sum to the 100 repetitions; `failed:N` is a call that returned no prediction.

| Judge | Eval | unstable cases | vote distribution |
|---|---|---|---|
| jev | abstain_ok | 1 | q05v1 {false:96, true:4} |
| jev | grounded | 0 | - |
| jev | quality | 0 | - |
| gemini-3.8-flash | abstain_ok | 1 | q05v1 {true:98, false:2} |
| gemini-3.8-flash | grounded | 0 | - |
| gemini-3.8-flash | quality | 2 | q05v1 {3:80, 4:20}, q06 {4:62, 3:38} |
| gpt-5.6-luna | abstain_ok | 2 | q05v1 {true:64, false:36}, q07 {true:53, false:47} |
| gpt-5.6-luna | grounded | 5 | q05v1 {false:52, true:48}, q06 {true:93, false:7}, q07 {true:71, false:29}, q10 {true:97, false:3}, q11 {true:65, false:35} |
| gpt-5.6-luna | quality | 7 | q01 {4:88, 3:12}, q05 {4:99, 3:1}, q05v1 {2:77, 3:22, 1:1}, q07 {2:71, 3:25, 4:4}, q09 {4:98, 3:2}, q10 {3:57, 4:43}, q11 {2:85, 3:11, 1:4} |

### Table F — Per-case verdicts (modal answer and agreement)

`modal (agreement, votes)`; vote counts sum to the 100 repetitions.

| Case | Eval | gold | jev | gemini-3.8-flash | gpt-5.6-luna |
|---|---|---|---|---|---|
| q01 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q01 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q01 | quality | 4 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (88.0%, 4:88, 3:12) |
| q02 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q02 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q02 | quality | 4 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) |
| q03 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q03 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q03 | quality | 4 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) |
| q04 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q04 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q04 | quality | 3 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) |
| q05 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q05 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q05 | quality | 4 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (99.0%, 4:99, 3:1) |
| q05v1 | abstain_ok | false | false (96.0%, false:96, true:4) | true (98.0%, true:98, false:2) | true (64.0%, true:64, false:36) |
| q05v1 | grounded | false | false (100.0%, false:100) | true (100.0%, true:100) | false (52.0%, false:52, true:48) |
| q05v1 | quality | 1 | 3 (100.0%, 3:100) | 3 (80.0%, 3:80, 4:20) | 2 (77.0%, 2:77, 3:22, 1:1) |
| q06 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q06 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (93.0%, true:93, false:7) |
| q06 | quality | 3 | 2 (100.0%, 2:100) | 4 (62.0%, 4:62, 3:38) | 2 (100.0%, 2:100) |
| q07 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (53.0%, true:53, false:47) |
| q07 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (71.0%, true:71, false:29) |
| q07 | quality | 4 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 2 (71.0%, 2:71, 3:25, 4:4) |
| q08 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q08 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q08 | quality | 4 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) |
| q09 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q09 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q09 | quality | 4 | 4 (100.0%, 4:100) | 4 (100.0%, 4:100) | 4 (98.0%, 4:98, 3:2) |
| q10 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q10 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (97.0%, true:97, false:3) |
| q10 | quality | 3 | 3 (100.0%, 3:100) | 4 (100.0%, 4:100) | 3 (57.0%, 3:57, 4:43) |
| q11 | abstain_ok | true | true (100.0%, true:100) | true (100.0%, true:100) | true (100.0%, true:100) |
| q11 | grounded | true | true (100.0%, true:100) | true (100.0%, true:100) | true (65.0%, true:65, false:35) |
| q11 | quality | 3 | 2 (100.0%, 2:100) | 4 (100.0%, 4:100) | 2 (85.0%, 2:85, 3:11, 1:4) |
