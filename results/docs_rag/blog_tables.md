# Docs-agent judge benchmark — `docs_rag`

22 frozen cases x 20 repetitions (every cell has the same repetition count), 4 judges, evals: abstain_ok, grounded, quality.

### Table A — Binary accuracy vs the labels

Correct decisions over all (case x repetition) decisions. A failed call counts as incorrect. `baseline(majority)` always answers the most common gold value of the eval.

Gold distribution over the 22 cases — **abstain_ok**: 18 true / 4 false; **grounded**: 12 true / 10 false; **quality**: 7 level 4 / 6 level 1 / 5 level 0 / 4 level 3.

| Judge | abstain_ok | grounded | pooled | failed calls (all evals) |
|---|---|---|---|---|
| jev | 68.0% (299/440) | 100.0% (440/440) | 84.0% (739/880) | 0 |
| deepseek-v4.1-flash | 71.1% (313/440) | 94.5% (416/440) | 82.8% (729/880) | 6 |
| gemini-3.8-flash | 82.0% (361/440) | 95.5% (420/440) | 88.8% (781/880) | 2 |
| gpt-5.6-luna | 63.2% (278/440) | 94.3% (415/440) | 78.8% (693/880) | 4 |
| baseline(majority) | 81.8% (360/440) | 54.5% (240/440) | 68.2% (600/880) | 0 |

### Table A1 — Modal-verdict accuracy (cases whose most common answer matches the label)

One vote per case: the modal answer over repetitions, scored against the label. This is what a single production draw most likely returns; Table A charges every unstable repetition against accuracy, which flatters a judge that is stable and wrong.

| Judge | abstain_ok | grounded | quality |
|---|---|---|---|
| jev | 15/22 | 22/22 | 12/22 |
| deepseek-v4.1-flash | 14/22 | 21/22 | 14/22 |
| gemini-3.8-flash | 18/22 | 21/22 | 15/22 |
| gpt-5.6-luna | 14/22 | 22/22 | 14/22 |
| baseline(majority) | 18/22 | 12/22 | 7/22 |

### Table A2 — Failed calls per eval

A failed call returned no prediction (retries exhausted, or the reasoning overflowed `max_tokens`).

| Judge | abstain_ok | grounded | quality | total |
|---|---|---|---|---|
| jev | 0 | 0 | 0 | 0 |
| deepseek-v4.1-flash | 1 | 5 | 0 | 6 |
| gemini-3.8-flash | 2 | 0 | 0 | 2 |
| gpt-5.6-luna | 3 | 0 | 1 | 4 |

### Table B — quality variance across repetitions

`quality` normalised to 0-1 (pred/4), population variance per case, averaged over cases. Failed calls are excluded from the values and reported in the last column. A judge with zero variance has no worst case, so the column reads `-`.

| Judge | mean per-case variance | x Jev | worst case | worst-case variance | failed calls |
|---|---|---|---|---|---|
| jev | 0.00000 | n/a (Jev variance 0) | - | 0.00000 | 0.0% |
| deepseek-v4.1-flash | 0.00847 | n/a (Jev variance 0) | q05v1 | 0.02125 | 0.0% |
| gemini-3.8-flash | 0.00151 | n/a (Jev variance 0) | h01 | 0.01172 | 0.0% |
| gpt-5.6-luna | 0.00439 | n/a (Jev variance 0) | q07 | 0.01625 | 0.2% |

### Table B2 — per-case quality variance

| Case | jev | deepseek-v4.1-flash | gemini-3.8-flash | gpt-5.6-luna |
|---|---|---|---|---|
| h01 | 0.00000 | 0.01312 | 0.01172 | 0.00562 |
| h02 | 0.00000 | 0.01422 | 0.00000 | 0.00797 |
| h03 | 0.00000 | 0.01000 | 0.00000 | 0.00000 |
| h04 | 0.00000 | 0.00297 | 0.00000 | 0.00297 |
| h05 | 0.00000 | 0.01562 | 0.00562 | 0.00297 |
| h06 | 0.00000 | 0.00297 | 0.00000 | 0.00000 |
| h07 | 0.00000 | 0.01312 | 0.00797 | 0.00000 |
| h08 | 0.00000 | 0.01500 | 0.00000 | 0.00297 |
| h09 | 0.00000 | 0.00563 | 0.00000 | 0.01312 |
| h10 | 0.00000 | 0.01172 | 0.00000 | 0.00000 |
| q01 | 0.00000 | 0.00000 | 0.00000 | 0.00562 |
| q02 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| q03 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| q04 | 0.00000 | 0.01172 | 0.00000 | 0.00297 |
| q05 | 0.00000 | 0.00562 | 0.00000 | 0.00000 |
| q05v1 | 0.00000 | 0.02125 | 0.00000 | 0.01000 |
| q06 | 0.00000 | 0.00297 | 0.00797 | 0.00000 |
| q07 | 0.00000 | 0.00297 | 0.00000 | 0.01625 |
| q08 | 0.00000 | 0.00562 | 0.00000 | 0.00000 |
| q09 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| q10 | 0.00000 | 0.01547 | 0.00000 | 0.01350 |
| q11 | 0.00000 | 0.01625 | 0.00000 | 0.01250 |

### Table C — Cost per call and per decision, latency per call

A decision is one (case, eval, repetition). The LLM judges make one call per decision; Jev answers all evals of a case in one classify call, so its calls are a third of its decisions. Latency is measured per request, so mean, p50 and p95 are over physical calls — but runs recorded before 2026-09-20 stored the per-cell mean on every repetition row, and their percentiles are percentiles of those means. Latency was measured with the three LLM judges at 6 in-flight calls each and Jev on an 8-thread pool, all from one laptop.

| Judge | physical calls | decisions | USD/call | USD/decision | s/call | s/call p50 | s/call p95 | total USD |
|---|---|---|---|---|---|---|---|---|
| jev | 440 | 1320 | 0.00047 | 0.00016 | 1.29 | 0.70 | 3.97 | 0.2074 |
| deepseek-v4.1-flash | 1320 | 1320 | 0.00127 | 0.00127 | 5.81 | 3.53 | 14.90 | 1.6759 |
| gemini-3.8-flash | 1320 | 1320 | 0.00506 | 0.00506 | 4.68 | 2.85 | 12.93 | 6.6766 |
| gpt-5.6-luna | 1320 | 1320 | 0.00038 | 0.00038 | 4.80 | 3.11 | 8.74 | 0.5073 |

### Table C2 — Cost per 1,000 traces (extrapolated from this run)

A trace is one frozen agent run judged on all 3 evals once; the frozen states average 29,150 characters of parsed conversation and search results. USD/trace is this run's total spend divided by its (case x repetition) count and multiplied out linearly, so it assumes the same trace length and the same prices. Repeating one state many times is what a provider prompt cache rewards, so the billed figure understates a judge whose input was largely cached (`cached input`); the list-price column reprices the mean tokens per call at the model's uncached USD per million and is the number to use for 1,000 distinct traces. Wall time per trace is the mean latency of one call, since the LLM judges' 3 calls per trace run in parallel; serial is the sum. Token columns are `-` on runs recorded before per-call token usage was stored. List prices (USD per million input / output tokens, Orq router, 2026-09-20): gpt-5.6-luna 0.2 / 1.2, gpt-5.6-sol 4 / 20, claude-opus-5 5 / 25, gemini-3.8-flash 0.75 / 3.75, deepseek-v4.1-flash 0.3 / 1.2.

| Judge | calls/trace | USD/trace | USD/1,000 traces (billed) | USD/1,000 traces (list price) | cached input | wall s/trace | serial s/trace | input tokens/call |
|---|---|---|---|---|---|---|---|---|
| jev | 1 | 0.00047 | 0.47 | - | - | 1.29 | 1.29 | - |
| deepseek-v4.1-flash | 3 | 0.00381 | 3.81 | 11.13 | 91.3% | 5.81 | 17.43 | 9,885 |
| gemini-3.8-flash | 3 | 0.01517 | 15.17 | 28.63 | 60.7% | 4.68 | 14.03 | 10,926 |
| gpt-5.6-luna | 3 | 0.00115 | 1.15 | 6.28 | 100.0% | 4.80 | 14.40 | 9,483 |

### Table D — Signal value (label agreement x repeatability)

Repeatability = share of repetitions matching the modal answer, averaged over cases; a failed call is a non-modal vote. Score evals are treated as exact-match categorical. `baseline(majority)` is constant, so its repeatability is 100% by construction.

| Judge | Eval | label agreement | repeatability | signal value |
|---|---|---|---|---|
| jev | abstain_ok | 68.0% | 99.8% | 0.678 |
| jev | grounded | 100.0% | 100.0% | 1.000 |
| jev | binary_pooled | 84.0% | 99.9% | 0.839 |
| jev | quality | 54.5% | 100.0% | 0.545 |
| deepseek-v4.1-flash | abstain_ok | 71.1% | 92.3% | 0.656 |
| deepseek-v4.1-flash | grounded | 94.5% | 98.6% | 0.933 |
| deepseek-v4.1-flash | binary_pooled | 82.8% | 95.5% | 0.791 |
| deepseek-v4.1-flash | quality | 62.7% | 81.1% | 0.509 |
| gemini-3.8-flash | abstain_ok | 82.0% | 95.7% | 0.785 |
| gemini-3.8-flash | grounded | 95.5% | 100.0% | 0.955 |
| gemini-3.8-flash | binary_pooled | 88.8% | 97.8% | 0.868 |
| gemini-3.8-flash | quality | 68.4% | 97.0% | 0.664 |
| gpt-5.6-luna | abstain_ok | 63.2% | 96.8% | 0.612 |
| gpt-5.6-luna | grounded | 94.3% | 94.3% | 0.890 |
| gpt-5.6-luna | binary_pooled | 78.8% | 95.6% | 0.753 |
| gpt-5.6-luna | quality | 63.4% | 92.0% | 0.584 |
| baseline(majority) | abstain_ok | 81.8% | 100.0% | 0.818 |
| baseline(majority) | grounded | 54.5% | 100.0% | 0.545 |
| baseline(majority) | binary_pooled | 68.2% | 100.0% | 0.682 |
| baseline(majority) | quality | 31.8% | 100.0% | 0.318 |

### Table E — Unstable cases (modal answer below 100% of reps)

Vote counts sum to the 20 repetitions; `failed:N` is a call that returned no prediction.

| Judge | Eval | unstable cases | vote distribution |
|---|---|---|---|
| jev | abstain_ok | 1 | q05v1 {false:19, true:1} |
| jev | grounded | 0 | - |
| jev | quality | 0 | - |
| deepseek-v4.1-flash | abstain_ok | 7 | h01 {false:12, true:8}, h02 {false:19, failed:1}, h03 {false:19, true:1}, h04 {false:16, true:4}, h05 {false:12, true:8}, h07 {false:10, true:10}, q05v1 {true:18, false:2} |
| deepseek-v4.1-flash | grounded | 2 | q05v1 {true:19, false:1}, q06 {true:15, failed:5} |
| deepseek-v4.1-flash | quality | 18 | h01 {2:14, 1:6}, h02 {1:13, 0:7}, h03 {0:16, 1:4}, h04 {1:19, 2:1}, h05 {2:10, 1:10}, h06 {1:19, 2:1}, h07 {1:14, 2:6}, h08 {0:12, 1:8}, h09 {1:18, 0:2}, h10 {1:15, 0:5}, q04 {4:15, 3:5}, q05 {4:18, 3:2}, q05v1 {2:13, 3:6, 4:1}, q06 {2:19, 3:1}, q07 {4:19, 3:1}, q08 {4:18, 3:2}, q10 {3:11, 4:9}, q11 {3:14, 2:5, 4:1} |
| gemini-3.8-flash | abstain_ok | 5 | h01 {true:16, false:4}, h02 {true:17, false:3}, h05 {false:12, true:8}, q05v1 {true:18, false:2}, q10 {true:18, failed:2} |
| gemini-3.8-flash | grounded | 0 | - |
| gemini-3.8-flash | quality | 4 | h01 {1:15, 2:5}, h05 {3:18, 2:2}, h07 {2:17, 1:3}, q06 {4:17, 3:3} |
| gpt-5.6-luna | abstain_ok | 2 | q05v1 {true:14, false:6}, q07 {true:12, false:5, failed:3} |
| gpt-5.6-luna | grounded | 4 | q05v1 {false:11, true:9}, q07 {true:14, false:6}, q10 {true:19, false:1}, q11 {true:11, false:9} |
| gpt-5.6-luna | quality | 12 | h01 {2:18, 1:2}, h02 {0:17, 1:3}, h04 {1:19, 2:1}, h05 {2:19, 1:1}, h08 {0:19, 1:1}, h09 {1:14, 0:6}, q01 {4:18, 3:2}, q04 {4:19, 3:1}, q05v1 {2:16, 3:4}, q07 {2:17, 3:2, 4:1}, q10 {3:13, 4:6, failed:1}, q11 {2:16, 1:2, 3:2} |

### Table F — Per-case verdicts (modal answer and agreement)

`modal (agreement, votes)`; vote counts sum to the 20 repetitions.

| Case | Eval | gold | jev | deepseek-v4.1-flash | gemini-3.8-flash | gpt-5.6-luna |
|---|---|---|---|---|---|---|
| h01 | abstain_ok | true | false (100.0%, false:20) | false (60.0%, false:12, true:8) | true (80.0%, true:16, false:4) | false (100.0%, false:20) |
| h01 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h01 | quality | 1 | 3 (100.0%, 3:20) | 2 (70.0%, 2:14, 1:6) | 1 (75.0%, 1:15, 2:5) | 2 (90.0%, 2:18, 1:2) |
| h02 | abstain_ok | true | false (100.0%, false:20) | false (95.0%, false:19, failed:1) | true (85.0%, true:17, false:3) | false (100.0%, false:20) |
| h02 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h02 | quality | 0 | 1 (100.0%, 1:20) | 1 (65.0%, 1:13, 0:7) | 0 (100.0%, 0:20) | 0 (85.0%, 0:17, 1:3) |
| h03 | abstain_ok | true | false (100.0%, false:20) | false (95.0%, false:19, true:1) | false (100.0%, false:20) | false (100.0%, false:20) |
| h03 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h03 | quality | 0 | 0 (100.0%, 0:20) | 0 (80.0%, 0:16, 1:4) | 0 (100.0%, 0:20) | 0 (100.0%, 0:20) |
| h04 | abstain_ok | true | false (100.0%, false:20) | false (80.0%, false:16, true:4) | true (100.0%, true:20) | false (100.0%, false:20) |
| h04 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h04 | quality | 1 | 1 (100.0%, 1:20) | 1 (95.0%, 1:19, 2:1) | 1 (100.0%, 1:20) | 1 (95.0%, 1:19, 2:1) |
| h05 | abstain_ok | true | false (100.0%, false:20) | false (60.0%, false:12, true:8) | false (60.0%, false:12, true:8) | false (100.0%, false:20) |
| h05 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h05 | quality | 1 | 2 (100.0%, 2:20) | 2 (50.0%, 2:10, 1:10) | 3 (90.0%, 3:18, 2:2) | 2 (95.0%, 2:19, 1:1) |
| h06 | abstain_ok | true | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h06 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| h06 | quality | 1 | 1 (100.0%, 1:20) | 1 (95.0%, 1:19, 2:1) | 1 (100.0%, 1:20) | 1 (100.0%, 1:20) |
| h07 | abstain_ok | true | false (100.0%, false:20) | false (50.0%, false:10, true:10) | true (100.0%, true:20) | false (100.0%, false:20) |
| h07 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h07 | quality | 1 | 1 (100.0%, 1:20) | 1 (70.0%, 1:14, 2:6) | 2 (85.0%, 2:17, 1:3) | 1 (100.0%, 1:20) |
| h08 | abstain_ok | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h08 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h08 | quality | 0 | 1 (100.0%, 1:20) | 0 (60.0%, 0:12, 1:8) | 0 (100.0%, 0:20) | 0 (95.0%, 0:19, 1:1) |
| h09 | abstain_ok | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h09 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h09 | quality | 0 | 1 (100.0%, 1:20) | 1 (90.0%, 1:18, 0:2) | 0 (100.0%, 0:20) | 1 (70.0%, 1:14, 0:6) |
| h10 | abstain_ok | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h10 | grounded | false | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) | false (100.0%, false:20) |
| h10 | quality | 0 | 1 (100.0%, 1:20) | 1 (75.0%, 1:15, 0:5) | 0 (100.0%, 0:20) | 0 (100.0%, 0:20) |
| q01 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q01 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q01 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (90.0%, 4:18, 3:2) |
| q02 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q02 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q02 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) |
| q03 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q03 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q03 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) |
| q04 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q04 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q04 | quality | 3 | 4 (100.0%, 4:20) | 4 (75.0%, 4:15, 3:5) | 4 (100.0%, 4:20) | 4 (95.0%, 4:19, 3:1) |
| q05 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q05 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q05 | quality | 4 | 4 (100.0%, 4:20) | 4 (90.0%, 4:18, 3:2) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) |
| q05v1 | abstain_ok | false | false (95.0%, false:19, true:1) | true (90.0%, true:18, false:2) | true (90.0%, true:18, false:2) | true (70.0%, true:14, false:6) |
| q05v1 | grounded | false | false (100.0%, false:20) | true (95.0%, true:19, false:1) | true (100.0%, true:20) | false (55.0%, false:11, true:9) |
| q05v1 | quality | 1 | 3 (100.0%, 3:20) | 2 (65.0%, 2:13, 3:6, 4:1) | 4 (100.0%, 4:20) | 2 (80.0%, 2:16, 3:4) |
| q06 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q06 | grounded | true | true (100.0%, true:20) | true (75.0%, true:15, failed:5) | true (100.0%, true:20) | true (100.0%, true:20) |
| q06 | quality | 3 | 2 (100.0%, 2:20) | 2 (95.0%, 2:19, 3:1) | 4 (85.0%, 4:17, 3:3) | 2 (100.0%, 2:20) |
| q07 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (60.0%, true:12, false:5, failed:3) |
| q07 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (70.0%, true:14, false:6) |
| q07 | quality | 4 | 4 (100.0%, 4:20) | 4 (95.0%, 4:19, 3:1) | 4 (100.0%, 4:20) | 2 (85.0%, 2:17, 3:2, 4:1) |
| q08 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q08 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q08 | quality | 4 | 4 (100.0%, 4:20) | 4 (90.0%, 4:18, 3:2) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) |
| q09 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q09 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q09 | quality | 4 | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) | 4 (100.0%, 4:20) |
| q10 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (90.0%, true:18, failed:2) | true (100.0%, true:20) |
| q10 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (95.0%, true:19, false:1) |
| q10 | quality | 3 | 3 (100.0%, 3:20) | 3 (55.0%, 3:11, 4:9) | 4 (100.0%, 4:20) | 3 (65.0%, 3:13, 4:6, failed:1) |
| q11 | abstain_ok | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) |
| q11 | grounded | true | true (100.0%, true:20) | true (100.0%, true:20) | true (100.0%, true:20) | true (55.0%, true:11, false:9) |
| q11 | quality | 3 | 2 (100.0%, 2:20) | 3 (70.0%, 3:14, 2:5, 4:1) | 4 (100.0%, 4:20) | 2 (80.0%, 2:16, 1:2, 3:2) |
