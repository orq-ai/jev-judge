# Docs-agent judge benchmark — `docs_rag_sota`

22 frozen cases x 3 repetitions (every cell has the same repetition count), 3 judges, evals: abstain_ok, grounded, quality.

### Table A — Binary accuracy vs the labels

Correct decisions over all (case x repetition) decisions. A failed call counts as incorrect. `baseline(majority)` always answers the most common gold value of the eval.

Gold distribution over the 22 cases — **abstain_ok**: 18 true / 4 false; **grounded**: 12 true / 10 false; **quality**: 7 level 4 / 6 level 1 / 5 level 0 / 4 level 3.

| Judge | abstain_ok | grounded | pooled | failed calls (all evals) |
|---|---|---|---|---|
| jev | 68.2% (45/66) | 100.0% (66/66) | 84.1% (111/132) | 0 |
| claude-opus-5 | 78.8% (52/66) | 100.0% (66/66) | 89.4% (118/132) | 0 |
| gpt-5.6-sol | 65.2% (43/66) | 89.4% (59/66) | 77.3% (102/132) | 3 |
| baseline(majority) | 81.8% (54/66) | 54.5% (36/66) | 68.2% (90/132) | 0 |

### Table A1 — Modal-verdict accuracy (cases whose most common answer matches the label)

One vote per case: the modal answer over repetitions, scored against the label. This is what a single production draw most likely returns; Table A charges every unstable repetition against accuracy, which flatters a judge that is stable and wrong.

| Judge | abstain_ok | grounded | quality |
|---|---|---|---|
| jev | 15/22 | 22/22 | 12/22 |
| claude-opus-5 | 18/22 | 22/22 | 15/22 |
| gpt-5.6-sol | 14/22 | 21/22 | 15/22 |
| baseline(majority) | 18/22 | 12/22 | 7/22 |

### Table A2 — Failed calls per eval

A failed call returned no prediction (retries exhausted, or the reasoning overflowed `max_tokens`).

| Judge | abstain_ok | grounded | quality | total |
|---|---|---|---|---|
| jev | 0 | 0 | 0 | 0 |
| claude-opus-5 | 0 | 0 | 0 | 0 |
| gpt-5.6-sol | 1 | 2 | 0 | 3 |

### Table B — quality variance across repetitions

`quality` normalised to 0-1 (pred/4), population variance per case, averaged over cases. Failed calls are excluded from the values and reported in the last column. A judge with zero variance has no worst case, so the column reads `-`.

| Judge | mean per-case variance | x Jev | worst case | worst-case variance | failed calls |
|---|---|---|---|---|---|
| jev | 0.00000 | n/a (Jev variance 0) | - | 0.00000 | 0.0% |
| claude-opus-5 | 0.00189 | n/a (Jev variance 0) | q04 | 0.01389 | 0.0% |
| gpt-5.6-sol | 0.00189 | n/a (Jev variance 0) | h09 | 0.01389 | 0.0% |

### Table B2 — per-case quality variance

| Case | jev | claude-opus-5 | gpt-5.6-sol |
|---|---|---|---|
| h01 | 0.00000 | 0.00000 | 0.01389 |
| h02 | 0.00000 | 0.00000 | 0.00000 |
| h03 | 0.00000 | 0.00000 | 0.00000 |
| h04 | 0.00000 | 0.00000 | 0.00000 |
| h05 | 0.00000 | 0.00000 | 0.00000 |
| h06 | 0.00000 | 0.00000 | 0.00000 |
| h07 | 0.00000 | 0.00000 | 0.00000 |
| h08 | 0.00000 | 0.00000 | 0.00000 |
| h09 | 0.00000 | 0.00000 | 0.01389 |
| h10 | 0.00000 | 0.00000 | 0.00000 |
| q01 | 0.00000 | 0.00000 | 0.00000 |
| q02 | 0.00000 | 0.00000 | 0.00000 |
| q03 | 0.00000 | 0.00000 | 0.00000 |
| q04 | 0.00000 | 0.01389 | 0.00000 |
| q05 | 0.00000 | 0.00000 | 0.00000 |
| q05v1 | 0.00000 | 0.00000 | 0.01389 |
| q06 | 0.00000 | 0.00000 | 0.00000 |
| q07 | 0.00000 | 0.01389 | 0.00000 |
| q08 | 0.00000 | 0.00000 | 0.00000 |
| q09 | 0.00000 | 0.00000 | 0.00000 |
| q10 | 0.00000 | 0.01389 | 0.00000 |
| q11 | 0.00000 | 0.00000 | 0.00000 |

### Table C — Cost per call and per decision, latency per call

A decision is one (case, eval, repetition). The LLM judges make one call per decision; Jev answers all evals of a case in one classify call, so its calls are a third of its decisions. Latency is measured per request, so mean, p50 and p95 are over physical calls — but runs recorded before 2026-09-20 stored the per-cell mean on every repetition row, and their percentiles are percentiles of those means. Latency was measured with the three LLM judges at 6 in-flight calls each and Jev on an 8-thread pool, all from one laptop.

| Judge | physical calls | decisions | USD/call | USD/decision | s/call | s/call p50 | s/call p95 | total USD |
|---|---|---|---|---|---|---|---|---|
| jev | 66 | 198 | 0.00047 | 0.00016 | 4.79 | 2.27 | 18.65 | 0.0311 |
| claude-opus-5 | 198 | 198 | 0.08222 | 0.08222 | 8.96 | 6.70 | 25.20 | 16.2794 |
| gpt-5.6-sol | 198 | 198 | 0.01782 | 0.01782 | 10.09 | 5.41 | 28.11 | 3.5292 |

### Table C2 — Cost per 1,000 traces (extrapolated from this run)

A trace is one frozen agent run judged on all 3 evals once; the frozen states average 29,150 characters of parsed conversation and search results. USD/trace is this run's total spend divided by its (case x repetition) count and multiplied out linearly, so it assumes the same trace length and the same prices. Repeating one state many times is what a provider prompt cache rewards, so the billed figure understates a judge whose input was largely cached (`cached input`); the list-price column reprices the mean tokens per call at the model's uncached USD per million and is the number to use for 1,000 distinct traces. Wall time per trace is the mean latency of one call, since the LLM judges' 3 calls per trace run in parallel; serial is the sum. Token columns are `-` on runs recorded before per-call token usage was stored. List prices (USD per million input / output tokens, Orq router, 2026-09-20): gpt-5.6-luna 0.2 / 1.2, gpt-5.6-sol 4 / 20, claude-opus-5 5 / 25, gemini-3.8-flash 0.75 / 3.75, deepseek-v4.1-flash 0.3 / 1.2.

| Judge | calls/trace | USD/trace | USD/1,000 traces (billed) | USD/1,000 traces (list price) | cached input | wall s/trace | serial s/trace | input tokens/call |
|---|---|---|---|---|---|---|---|---|
| jev | 1 | 0.00047 | 0.47 | - | - | 4.79 | 4.79 | - |
| claude-opus-5 | 3 | 0.24666 | 246.66 | 246.66 | 0.0% | 8.96 | 26.89 | 14,692 |
| gpt-5.6-sol | 3 | 0.05347 | 53.47 | 120.43 | 64.7% | 10.09 | 30.27 | 9,472 |

### Table D — Signal value (label agreement x repeatability)

Repeatability = share of repetitions matching the modal answer, averaged over cases; a failed call is a non-modal vote. Score evals are treated as exact-match categorical. `baseline(majority)` is constant, so its repeatability is 100% by construction.

| Judge | Eval | label agreement | repeatability | signal value |
|---|---|---|---|---|
| jev | abstain_ok | 68.2% | 100.0% | 0.682 |
| jev | grounded | 100.0% | 100.0% | 1.000 |
| jev | binary_pooled | 84.1% | 100.0% | 0.841 |
| jev | quality | 54.5% | 100.0% | 0.545 |
| claude-opus-5 | abstain_ok | 78.8% | 97.0% | 0.764 |
| claude-opus-5 | grounded | 100.0% | 100.0% | 1.000 |
| claude-opus-5 | binary_pooled | 89.4% | 98.5% | 0.880 |
| claude-opus-5 | quality | 66.7% | 95.5% | 0.636 |
| gpt-5.6-sol | abstain_ok | 65.2% | 97.0% | 0.632 |
| gpt-5.6-sol | grounded | 89.4% | 93.9% | 0.840 |
| gpt-5.6-sol | binary_pooled | 77.3% | 95.5% | 0.738 |
| gpt-5.6-sol | quality | 71.2% | 95.5% | 0.680 |
| baseline(majority) | abstain_ok | 81.8% | 100.0% | 0.818 |
| baseline(majority) | grounded | 54.5% | 100.0% | 0.545 |
| baseline(majority) | binary_pooled | 68.2% | 100.0% | 0.682 |
| baseline(majority) | quality | 31.8% | 100.0% | 0.318 |

### Table E — Unstable cases (modal answer below 100% of reps)

Vote counts sum to the 3 repetitions; `failed:N` is a call that returned no prediction.

| Judge | Eval | unstable cases | vote distribution |
|---|---|---|---|
| jev | abstain_ok | 0 | - |
| jev | grounded | 0 | - |
| jev | quality | 0 | - |
| claude-opus-5 | abstain_ok | 2 | h01 {true:2, false:1}, h04 {true:2, false:1} |
| claude-opus-5 | grounded | 0 | - |
| claude-opus-5 | quality | 3 | q04 {3:2, 2:1}, q07 {4:2, 3:1}, q10 {4:2, 3:1} |
| gpt-5.6-sol | abstain_ok | 2 | h04 {false:2, true:1}, h07 {false:2, failed:1} |
| gpt-5.6-sol | grounded | 3 | h07 {failed:2, false:1}, q02 {true:2, false:1}, q11 {true:2, false:1} |
| gpt-5.6-sol | quality | 3 | h01 {2:2, 1:1}, h09 {1:2, 0:1}, q05v1 {3:2, 2:1} |

### Table F — Per-case verdicts (modal answer and agreement)

`modal (agreement, votes)`; vote counts sum to the 3 repetitions.

| Case | Eval | gold | jev | claude-opus-5 | gpt-5.6-sol |
|---|---|---|---|---|---|
| h01 | abstain_ok | true | false (100.0%, false:3) | true (66.7%, true:2, false:1) | false (100.0%, false:3) |
| h01 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h01 | quality | 1 | 3 (100.0%, 3:3) | 1 (100.0%, 1:3) | 2 (66.7%, 2:2, 1:1) |
| h02 | abstain_ok | true | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h02 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h02 | quality | 0 | 1 (100.0%, 1:3) | 0 (100.0%, 0:3) | 0 (100.0%, 0:3) |
| h03 | abstain_ok | true | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h03 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h03 | quality | 0 | 0 (100.0%, 0:3) | 0 (100.0%, 0:3) | 0 (100.0%, 0:3) |
| h04 | abstain_ok | true | false (100.0%, false:3) | true (66.7%, true:2, false:1) | false (66.7%, false:2, true:1) |
| h04 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h04 | quality | 1 | 1 (100.0%, 1:3) | 1 (100.0%, 1:3) | 1 (100.0%, 1:3) |
| h05 | abstain_ok | true | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h05 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h05 | quality | 1 | 2 (100.0%, 2:3) | 2 (100.0%, 2:3) | 2 (100.0%, 2:3) |
| h06 | abstain_ok | true | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h06 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| h06 | quality | 1 | 1 (100.0%, 1:3) | 1 (100.0%, 1:3) | 1 (100.0%, 1:3) |
| h07 | abstain_ok | true | false (100.0%, false:3) | true (100.0%, true:3) | false (66.7%, false:2, failed:1) |
| h07 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (33.3%, failed:2, false:1) |
| h07 | quality | 1 | 1 (100.0%, 1:3) | 1 (100.0%, 1:3) | 1 (100.0%, 1:3) |
| h08 | abstain_ok | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h08 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h08 | quality | 0 | 1 (100.0%, 1:3) | 0 (100.0%, 0:3) | 0 (100.0%, 0:3) |
| h09 | abstain_ok | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h09 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h09 | quality | 0 | 1 (100.0%, 1:3) | 0 (100.0%, 0:3) | 1 (66.7%, 1:2, 0:1) |
| h10 | abstain_ok | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h10 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| h10 | quality | 0 | 1 (100.0%, 1:3) | 0 (100.0%, 0:3) | 0 (100.0%, 0:3) |
| q01 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q01 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q01 | quality | 4 | 4 (100.0%, 4:3) | 3 (100.0%, 3:3) | 4 (100.0%, 4:3) |
| q02 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q02 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (66.7%, true:2, false:1) |
| q02 | quality | 4 | 4 (100.0%, 4:3) | 3 (100.0%, 3:3) | 4 (100.0%, 4:3) |
| q03 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q03 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q03 | quality | 4 | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) |
| q04 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q04 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q04 | quality | 3 | 4 (100.0%, 4:3) | 3 (66.7%, 3:2, 2:1) | 4 (100.0%, 4:3) |
| q05 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q05 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q05 | quality | 4 | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) |
| q05v1 | abstain_ok | false | false (100.0%, false:3) | false (100.0%, false:3) | true (100.0%, true:3) |
| q05v1 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | true (100.0%, true:3) |
| q05v1 | quality | 1 | 3 (100.0%, 3:3) | 2 (100.0%, 2:3) | 3 (66.7%, 3:2, 2:1) |
| q06 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q06 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q06 | quality | 3 | 2 (100.0%, 2:3) | 2 (100.0%, 2:3) | 2 (100.0%, 2:3) |
| q07 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q07 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q07 | quality | 4 | 4 (100.0%, 4:3) | 4 (66.7%, 4:2, 3:1) | 4 (100.0%, 4:3) |
| q08 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q08 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q08 | quality | 4 | 4 (100.0%, 4:3) | 3 (100.0%, 3:3) | 4 (100.0%, 4:3) |
| q09 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q09 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q09 | quality | 4 | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) |
| q10 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q10 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q10 | quality | 3 | 3 (100.0%, 3:3) | 4 (66.7%, 4:2, 3:1) | 4 (100.0%, 4:3) |
| q11 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q11 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (66.7%, true:2, false:1) |
| q11 | quality | 3 | 2 (100.0%, 2:3) | 3 (100.0%, 3:3) | 3 (100.0%, 3:3) |
