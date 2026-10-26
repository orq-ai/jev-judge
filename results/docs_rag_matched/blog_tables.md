# Docs-agent judge benchmark — `docs_rag_matched`

22 frozen cases x 20 repetitions (every cell has the same repetition count), 3 judges, evals: abstain_ok, grounded, quality.

### Table A — Binary accuracy vs the labels

Correct decisions over all (case x repetition) decisions. A failed call counts as incorrect. `baseline(majority)` always answers the most common gold value of the eval.

Gold distribution over the 22 cases — **abstain_ok**: 18 true / 4 false; **grounded**: 12 true / 10 false; **quality**: 7 level 4 / 6 level 1 / 5 level 0 / 4 level 3.

| Judge | abstain_ok | grounded | pooled | failed calls (all evals) |
|---|---|---|---|---|
| jev | 67.7% (298/440) | 100.0% (440/440) | 83.9% (738/880) | 0 |
| gemini-3.8-flash | 68.4% (301/440) | 95.5% (420/440) | 81.9% (721/880) | 2 |
| gpt-5.6-luna | 64.8% (285/440) | 92.0% (405/440) | 78.4% (690/880) | 8 |
| baseline(majority) | 81.8% (360/440) | 54.5% (240/440) | 68.2% (600/880) | 0 |

### Table A1 — Modal-verdict accuracy (cases whose most common answer matches the label)

One vote per case: the modal answer over repetitions, scored against the label. This is what a single production draw most likely returns; Table A charges every unstable repetition against accuracy, which flatters a judge that is stable and wrong.

| Judge | abstain_ok | grounded | quality |
|---|---|---|---|
| jev | 15/22 | 22/22 | 12/22 |
| gemini-3.8-flash | 15/22 | 21/22 | 14/22 |
| gpt-5.6-luna | 14/22 | 21/22 | 14/22 |
| baseline(majority) | 18/22 | 12/22 | 7/22 |

### Table A2 — Failed calls per eval

A failed call returned no prediction (retries exhausted, or the reasoning overflowed `max_tokens`).

| Judge | abstain_ok | grounded | quality | total |
|---|---|---|---|---|
| jev | 0 | 0 | 0 | 0 |
| gemini-3.8-flash | 0 | 0 | 2 | 2 |
| gpt-5.6-luna | 0 | 8 | 0 | 8 |

### Table B — quality variance across repetitions

`quality` normalised to 0-1 (pred/4), population variance per case, averaged over cases. Failed calls are excluded from the values and reported in the last column. A judge with zero variance has no worst case, so the column reads `-`.

| Judge | mean per-case variance | x Jev | worst case | worst-case variance | failed calls |
|---|---|---|---|---|---|
| jev | 0.00000 | n/a (Jev variance 0) | - | 0.00000 | 0.0% |
| gemini-3.8-flash | 0.00181 | n/a (Jev variance 0) | q05v1 | 0.01562 | 0.5% |
| gpt-5.6-luna | 0.00516 | n/a (Jev variance 0) | q07 | 0.04047 | 0.0% |

### Table B2 — per-case quality variance

| Case | jev | gemini-3.8-flash | gpt-5.6-luna |
|---|---|---|---|
| h01 | 0.00000 | 0.00000 | 0.00297 |
| h02 | 0.00000 | 0.00297 | 0.00563 |
| h03 | 0.00000 | 0.00000 | 0.00000 |
| h04 | 0.00000 | 0.00000 | 0.00000 |
| h05 | 0.00000 | 0.01558 | 0.00562 |
| h06 | 0.00000 | 0.00000 | 0.00000 |
| h07 | 0.00000 | 0.00000 | 0.00000 |
| h08 | 0.00000 | 0.00000 | 0.00000 |
| h09 | 0.00000 | 0.00000 | 0.01422 |
| h10 | 0.00000 | 0.00000 | 0.00797 |
| q01 | 0.00000 | 0.00000 | 0.00297 |
| q02 | 0.00000 | 0.00000 | 0.00000 |
| q03 | 0.00000 | 0.00000 | 0.00000 |
| q04 | 0.00000 | 0.00000 | 0.00000 |
| q05 | 0.00000 | 0.00000 | 0.00297 |
| q05v1 | 0.00000 | 0.01562 | 0.01000 |
| q06 | 0.00000 | 0.00562 | 0.00000 |
| q07 | 0.00000 | 0.00000 | 0.04047 |
| q08 | 0.00000 | 0.00000 | 0.00000 |
| q09 | 0.00000 | 0.00000 | 0.00562 |
| q10 | 0.00000 | 0.00000 | 0.01500 |
| q11 | 0.00000 | 0.00000 | 0.00000 |

### Table C — Cost per call and per decision, latency per call

A decision is one (case, eval, repetition). The LLM judges make one call per decision; Jev answers all evals of a case in one classify call, so its calls are a third of its decisions. Latency is measured per request, so mean, p50 and p95 are over physical calls — but runs recorded before 2026-09-20 stored the per-cell mean on every repetition row, and their percentiles are percentiles of those means. Latency was measured with the three LLM judges at 6 in-flight calls each and Jev on an 8-thread pool, all from one laptop.

| Judge | physical calls | decisions | USD/call | USD/decision | s/call | s/call p50 | s/call p95 | total USD |
|---|---|---|---|---|---|---|---|---|
| jev | 440 | 1320 | 0.00047 | 0.00016 | 3.91 | 0.95 | 20.79 | 0.2074 |
| gemini-3.8-flash | 1320 | 1320 | 0.00415 | 0.00415 | 4.21 | 2.30 | 12.49 | 5.4805 |
| gpt-5.6-luna | 1320 | 1320 | 0.00047 | 0.00047 | 6.15 | 3.48 | 14.17 | 0.6141 |

### Table C2 — Cost per 1,000 traces (extrapolated from this run)

A trace is one frozen agent run judged on all 3 evals once; the frozen states average 29,150 characters of parsed conversation and search results. USD/trace is this run's total spend divided by its (case x repetition) count and multiplied out linearly, so it assumes the same trace length and the same prices. Repeating one state many times is what a provider prompt cache rewards, so the billed figure understates a judge whose input was largely cached (`cached input`); the list-price column reprices the mean tokens per call at the model's uncached USD per million and is the number to use for 1,000 distinct traces. Wall time per trace is the mean latency of one call, since the LLM judges' 3 calls per trace run in parallel; serial is the sum. Token columns are `-` on runs recorded before per-call token usage was stored. List prices (USD per million input / output tokens, Orq router, 2026-09-20): gpt-5.6-luna 0.2 / 1.2, gpt-5.6-sol 4 / 20, claude-opus-5 5 / 25, gemini-3.8-flash 0.75 / 3.75, deepseek-v4.1-flash 0.3 / 1.2.

| Judge | calls/trace | USD/trace | USD/1,000 traces (billed) | USD/1,000 traces (list price) | cached input | wall s/trace | serial s/trace | input tokens/call |
|---|---|---|---|---|---|---|---|---|
| jev | 1 | 0.00047 | 0.47 | - | - | 3.91 | 3.91 | - |
| gemini-3.8-flash | 3 | 0.01246 | 12.46 | 25.57 | 59.2% | 4.21 | 12.62 | 10,925 |
| gpt-5.6-luna | 3 | 0.00140 | 1.40 | 6.27 | 94.9% | 6.15 | 18.46 | 9,488 |

### Table D — Signal value (label agreement x repeatability)

Repeatability = share of repetitions matching the modal answer, averaged over cases; a failed call is a non-modal vote. Score evals are treated as exact-match categorical. `baseline(majority)` is constant, so its repeatability is 100% by construction.

| Judge | Eval | label agreement | repeatability | signal value |
|---|---|---|---|---|
| jev | abstain_ok | 67.7% | 99.5% | 0.674 |
| jev | grounded | 100.0% | 100.0% | 1.000 |
| jev | binary_pooled | 83.9% | 99.8% | 0.837 |
| jev | quality | 54.5% | 100.0% | 0.545 |
| gemini-3.8-flash | abstain_ok | 68.4% | 98.9% | 0.676 |
| gemini-3.8-flash | grounded | 95.5% | 100.0% | 0.955 |
| gemini-3.8-flash | binary_pooled | 81.9% | 99.4% | 0.815 |
| gemini-3.8-flash | quality | 63.6% | 94.5% | 0.602 |
| gpt-5.6-luna | abstain_ok | 64.8% | 97.0% | 0.629 |
| gpt-5.6-luna | grounded | 92.0% | 92.5% | 0.851 |
| gpt-5.6-luna | binary_pooled | 78.4% | 94.8% | 0.743 |
| gpt-5.6-luna | quality | 63.0% | 91.4% | 0.575 |
| baseline(majority) | abstain_ok | 81.8% | 100.0% | 0.818 |
| baseline(majority) | grounded | 54.5% | 100.0% | 0.545 |
| baseline(majority) | binary_pooled | 68.2% | 100.0% | 0.682 |
| baseline(majority) | quality | 31.8% | 100.0% | 0.318 |

### Table E — Unstable cases (modal answer below 100% of reps)

Vote counts sum to the 20 repetitions; `failed:N` is a call that returned no prediction.

| Judge | Eval | unstable cases | vote distribution |
|---|---|---|---|
| jev | abstain_ok | 1 | q05v1 {false:18, true:2} |
| jev | grounded | 0 | - |
| jev | quality | 0 | - |
| gemini-3.8-flash | abstain_ok | 2 | h04 {false:17, true:3}, h07 {true:18, false:2} |
| gemini-3.8-flash | grounded | 0 | - |
| gemini-3.8-flash | quality | 5 | h02 {0:19, 1:1}, h05 {2:10, 3:9, failed:1}, q02 {4:19, failed:1}, q05v1 {3:10, 4:10}, q06 {4:18, 3:2} |
| gpt-5.6-luna | abstain_ok | 2 | q05v1 {true:11, false:9}, q07 {true:16, false:4} |
| gpt-5.6-luna | grounded | 7 | h06 {true:14, failed:6}, q02 {true:18, failed:2}, q05v1 {true:11, false:9}, q06 {true:18, false:2}, q07 {true:14, false:6}, q10 {true:19, false:1}, q11 {true:13, false:7} |
| gpt-5.6-luna | quality | 11 | h01 {2:19, 1:1}, h02 {0:18, 1:2}, h05 {2:18, 1:2}, h09 {1:13, 0:7}, h10 {0:17, 1:3}, q01 {4:19, 3:1}, q05 {4:19, 3:1}, q05v1 {2:16, 3:4}, q07 {2:13, 4:4, 3:3}, q09 {4:18, 3:2}, q10 {3:12, 4:8} |

### Table F — Per-case verdicts (modal answer and agreement)

`modal (agreement, votes)`; vote counts sum to the 20 repetitions.

| Case | Eval | gold | jev | gemini-3.8-flash | gpt-5.6-luna |
|---|---|---|---|---|---|
| h01 | abstain_ok | true | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h01 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h01 | quality | 1 | 3 (100.0%, 3:20) | 2 (100.0%, 2:20) | 2 (95.0%, 2:19, 1:1) |
| h02 | abstain_ok | true | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h02 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h02 | quality | 0 | 1 (100.0%, 1:20) | 0 (95.0%, 0:19, 1:1) | 0 (90.0%, 0:18, 1:2) |
| h03 | abstain_ok | true | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h03 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h03 | quality | 0 | 0 (100.0%, 0:20) | 0 (100.0%, 0:20) | 0 (100.0%, 0:20) |
| h04 | abstain_ok | true | false (100.0%, false:20) | false (85.0%, false:17, true:3) | false (100.0%, false:20) |
| h04 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h04 | quality | 1 | 1 (100.0%, 1:20) | 1 (100.0%, 1:20) | 1 (100.0%, 1:20) |
| h05 | abstain_ok | true | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h05 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h05 | quality | 1 | 2 (100.0%, 2:20) | 2 (50.0%, 2:10, 3:9, failed:1) | 2 (90.0%, 2:18, 1:2) |
| h06 | abstain_ok | true | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h06 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (70.0%, true:14, failed:6) |
| h06 | quality | 1 | 1 (100.0%, 1:20) | 1 (100.0%, 1:20) | 1 (100.0%, 1:20) |
| h07 | abstain_ok | true | false (100.0%, false:20) | true (90.0%, true:18, false:2) | false (100.0%, false:20) |
| h07 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h07 | quality | 1 | 1 (100.0%, 1:20) | 2 (100.0%, 2:20) | 1 (100.0%, 1:20) |
| h08 | abstain_ok | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h08 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h08 | quality | 0 | 1 (100.0%, 1:20) | 0 (100.0%, 0:20) | 0 (100.0%, 0:20) |
| h09 | abstain_ok | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h09 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h09 | quality | 0 | 1 (100.0%, 1:20) | 0 (100.0%, 0:20) | 1 (65.0%, 1:13, 0:7) |
| h10 | abstain_ok | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h10 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h10 | quality | 0 | 1 (100.0%, 1:20) | 0 (100.0%, 0:20) | 0 (85.0%, 0:17, 1:3) |
| q01 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q01 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q01 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (95.0%, 4:19, 3:1) |
| q02 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q02 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (90.0%, true:18, failed:2) |
| q02 | quality | 4 | 4 (100.0%, 4:20) | 4 (95.0%, 4:19, failed:1) | 4 (100.0%, 4:20) |
| q03 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q03 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q03 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) |
| q04 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q04 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q04 | quality | 3 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) |
| q05 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q05 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q05 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (95.0%, 4:19, 3:1) |
| q05v1 | abstain_ok | false | false (90.0%, false:18, true:2) | true (100.0%, true:20) | true (55.0%, true:11, false:9) |
| q05v1 | grounded | false | false (100.0%, false:20) | true (100.0%, true:20) | true (55.0%, true:11, false:9) |
| q05v1 | quality | 1 | 3 (100.0%, 3:20) | 3 (50.0%, 3:10, 4:10) | 2 (80.0%, 2:16, 3:4) |
| q06 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q06 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (90.0%, true:18, false:2) |
| q06 | quality | 3 | 2 (100.0%, 2:20) | 4 (90.0%, 4:18, 3:2) | 2 (100.0%, 2:20) |
| q07 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (80.0%, true:16, false:4) |
| q07 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (70.0%, true:14, false:6) |
| q07 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 2 (65.0%, 2:13, 4:4, 3:3) |
| q08 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q08 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q08 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) |
| q09 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q09 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q09 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (90.0%, 4:18, 3:2) |
| q10 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q10 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (95.0%, true:19, false:1) |
| q10 | quality | 3 | 3 (100.0%, 3:20) | 4 (100.0%, 4:20) | 3 (60.0%, 3:12, 4:8) |
| q11 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q11 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (65.0%, true:13, false:7) |
| q11 | quality | 3 | 2 (100.0%, 2:20) | 4 (100.0%, 4:20) | 2 (100.0%, 2:20) |

### Table G — `docs_rag` vs `docs_rag_matched`

| Judge | Eval | accuracy docs_rag | accuracy docs_rag_matched | repeatability docs_rag | repeatability docs_rag_matched |
|---|---|---|---|---|---|
| jev | abstain_ok | 68.0% | 67.7% | 99.8% | 99.5% |
| jev | grounded | 100.0% | 100.0% | 100.0% | 100.0% |
| jev | binary_pooled | 84.0% | 83.9% | 99.9% | 99.8% |
| jev | quality | 54.5% | 54.5% | 100.0% | 100.0% |
| gemini-3.8-flash | abstain_ok | 82.0% | 68.4% | 95.7% | 98.9% |
| gemini-3.8-flash | grounded | 95.5% | 95.5% | 100.0% | 100.0% |
| gemini-3.8-flash | binary_pooled | 88.8% | 81.9% | 97.8% | 99.4% |
| gemini-3.8-flash | quality | 68.4% | 63.6% | 97.0% | 94.5% |
| gpt-5.6-luna | abstain_ok | 63.2% | 64.8% | 96.8% | 97.0% |
| gpt-5.6-luna | grounded | 94.3% | 92.0% | 94.3% | 92.5% |
| gpt-5.6-luna | binary_pooled | 78.8% | 78.4% | 95.6% | 94.8% |
| gpt-5.6-luna | quality | 63.4% | 63.0% | 92.0% | 91.4% |
