# Docs-agent judge benchmark — `docs_rag_sota`

12 frozen cases x 3 repetitions (every cell has the same repetition count), 3 judges, evals: abstain_ok, grounded, quality.

### Table A — Binary accuracy vs the labels

Correct decisions over all (case x repetition) decisions. A failed call counts as incorrect. `baseline(majority)` always answers the most common gold value of the eval.

Gold distribution over the 12 cases — **abstain_ok**: 11 true / 1 false; **grounded**: 11 true / 1 false; **quality**: 7 level 4 / 4 level 3 / 1 level 1.

| Judge | abstain_ok | grounded | pooled | failed calls (all evals) |
|---|---|---|---|---|
| jev | 100.0% (36/36) | 100.0% (36/36) | 100.0% (72/72) | 0 |
| claude-opus-5 | 100.0% (36/36) | 100.0% (36/36) | 100.0% (72/72) | 0 |
| gpt-5.6-sol | 91.7% (33/36) | 94.4% (34/36) | 93.1% (67/72) | 0 |
| baseline(majority) | 91.7% (33/36) | 91.7% (33/36) | 91.7% (66/72) | 0 |

### Table A1 — Modal-verdict accuracy (cases whose most common answer matches the label)

One vote per case: the modal answer over repetitions, scored against the label. This is what a single production draw most likely returns; Table A charges every unstable repetition against accuracy, which flatters a judge that is stable and wrong.

| Judge | abstain_ok | grounded | quality |
|---|---|---|---|
| jev | 12/12 | 12/12 | 8/12 |
| claude-opus-5 | 12/12 | 12/12 | 6/12 |
| gpt-5.6-sol | 11/12 | 11/12 | 7/12 |
| baseline(majority) | 11/12 | 11/12 | 7/12 |

### Table A2 — Failed calls per eval

A failed call returned no prediction (retries exhausted, or the reasoning overflowed `max_tokens`).

| Judge | abstain_ok | grounded | quality | total |
|---|---|---|---|---|
| jev | 0 | 0 | 0 | 0 |
| claude-opus-5 | 0 | 0 | 0 | 0 |
| gpt-5.6-sol | 0 | 0 | 0 | 0 |

### Table B — quality variance across repetitions

`quality` normalised to 0-1 (pred/4), population variance per case, averaged over cases. Failed calls are excluded from the values and reported in the last column. A judge with zero variance has no worst case, so the column reads `-`.

| Judge | mean per-case variance | x Jev | worst case | worst-case variance | failed calls |
|---|---|---|---|---|---|
| jev | 0.00000 | n/a (Jev variance 0) | - | 0.00000 | 0.0% |
| claude-opus-5 | 0.00116 | n/a (Jev variance 0) | q07 | 0.01389 | 0.0% |
| gpt-5.6-sol | 0.00347 | n/a (Jev variance 0) | q05v1 | 0.01389 | 0.0% |

### Table B2 — per-case quality variance

| Case | jev | claude-opus-5 | gpt-5.6-sol |
|---|---|---|---|
| q01 | 0.00000 | 0.00000 | 0.00000 |
| q02 | 0.00000 | 0.00000 | 0.00000 |
| q03 | 0.00000 | 0.00000 | 0.00000 |
| q04 | 0.00000 | 0.00000 | 0.00000 |
| q05 | 0.00000 | 0.00000 | 0.00000 |
| q05v1 | 0.00000 | 0.00000 | 0.01389 |
| q06 | 0.00000 | 0.00000 | 0.00000 |
| q07 | 0.00000 | 0.01389 | 0.00000 |
| q08 | 0.00000 | 0.00000 | 0.00000 |
| q09 | 0.00000 | 0.00000 | 0.00000 |
| q10 | 0.00000 | 0.00000 | 0.01389 |
| q11 | 0.00000 | 0.00000 | 0.01389 |

### Table C — Cost per call and per decision, latency per call

A decision is one (case, eval, repetition). The LLM judges make one call per decision; Jev answers all evals of a case in one classify call, so its calls are a third of its decisions. Latency is measured per request, so mean, p50 and p95 are over physical calls — but runs recorded before 2026-09-20 stored the per-cell mean on every repetition row, and their percentiles are percentiles of those means. Latency was measured with the three LLM judges at 6 in-flight calls each and Jev on an 8-thread pool, all from one laptop.

| Judge | physical calls | decisions | USD/call | USD/decision | s/call | s/call p50 | s/call p95 | total USD |
|---|---|---|---|---|---|---|---|---|
| jev | 36 | 108 | 0.00049 | 0.00016 | 1.00 | 0.82 | 1.88 | 0.0176 |
| claude-opus-5 | 108 | 108 | 0.08657 | 0.08657 | 6.54 | 6.20 | 11.12 | 9.3491 |
| gpt-5.6-sol | 108 | 108 | 0.00636 | 0.00636 | 4.52 | 3.68 | 6.72 | 0.6874 |

### Table C2 — Cost per 1,000 traces (extrapolated from this run)

A trace is one frozen agent run judged on all 3 evals once; the frozen states average 30,018 characters of parsed conversation and search results. USD/trace is this run's total spend divided by its (case x repetition) count and multiplied out linearly, so it assumes the same trace length and the same prices. Repeating one state many times is what a provider prompt cache rewards, so the billed figure understates a judge whose input was largely cached (`cached input`); the list-price column reprices the mean tokens per call at the model's uncached USD per million and is the number to use for 1,000 distinct traces. Wall time per trace is the mean latency of one call, since the LLM judges' 3 calls per trace run in parallel; serial is the sum. Token columns are `-` on runs recorded before per-call token usage was stored. List prices (USD per million input / output tokens, Orq router, 2026-09-20): gpt-5.6-luna 0.2 / 1.2, gpt-5.6-sol 4 / 20, claude-opus-5 5 / 25, gemini-3.8-flash 0.75 / 3.75, deepseek-v4.1-flash 0.3 / 1.2.

| Judge | calls/trace | USD/trace | USD/1,000 traces (billed) | USD/1,000 traces (list price) | cached input | wall s/trace | serial s/trace | input tokens/call |
|---|---|---|---|---|---|---|---|---|
| jev | 1 | 0.00049 | 0.49 | - | - | 1.00 | 1.00 | - |
| claude-opus-5 | 3 | 0.25970 | 259.70 | 259.70 | 0.0% | 6.54 | 19.63 | 15,255 |
| gpt-5.6-sol | 3 | 0.01909 | 19.09 | 125.45 | 100.0% | 4.52 | 13.55 | 9,850 |

### Table D — Signal value (label agreement x repeatability)

Repeatability = share of repetitions matching the modal answer, averaged over cases; a failed call is a non-modal vote. Score evals are treated as exact-match categorical. `baseline(majority)` is constant, so its repeatability is 100% by construction.

| Judge | Eval | label agreement | repeatability | signal value |
|---|---|---|---|---|
| jev | abstain_ok | 100.0% | 100.0% | 1.000 |
| jev | grounded | 100.0% | 100.0% | 1.000 |
| jev | binary_pooled | 100.0% | 100.0% | 1.000 |
| jev | quality | 66.7% | 100.0% | 0.667 |
| claude-opus-5 | abstain_ok | 100.0% | 100.0% | 1.000 |
| claude-opus-5 | grounded | 100.0% | 100.0% | 1.000 |
| claude-opus-5 | binary_pooled | 100.0% | 100.0% | 1.000 |
| claude-opus-5 | quality | 47.2% | 97.2% | 0.459 |
| gpt-5.6-sol | abstain_ok | 91.7% | 100.0% | 0.917 |
| gpt-5.6-sol | grounded | 94.4% | 97.2% | 0.918 |
| gpt-5.6-sol | binary_pooled | 93.1% | 98.6% | 0.918 |
| gpt-5.6-sol | quality | 63.9% | 91.7% | 0.586 |
| baseline(majority) | abstain_ok | 91.7% | 100.0% | 0.917 |
| baseline(majority) | grounded | 91.7% | 100.0% | 0.917 |
| baseline(majority) | binary_pooled | 91.7% | 100.0% | 0.917 |
| baseline(majority) | quality | 58.3% | 100.0% | 0.583 |

### Table E — Unstable cases (modal answer below 100% of reps)

Vote counts sum to the 3 repetitions; `failed:N` is a call that returned no prediction.

| Judge | Eval | unstable cases | vote distribution |
|---|---|---|---|
| jev | abstain_ok | 0 | - |
| jev | grounded | 0 | - |
| jev | quality | 0 | - |
| claude-opus-5 | abstain_ok | 0 | - |
| claude-opus-5 | grounded | 0 | - |
| claude-opus-5 | quality | 1 | q07 {4:2, 3:1} |
| gpt-5.6-sol | abstain_ok | 0 | - |
| gpt-5.6-sol | grounded | 1 | q11 {false:2, true:1} |
| gpt-5.6-sol | quality | 3 | q05v1 {2:2, 3:1}, q10 {4:2, 3:1}, q11 {4:2, 3:1} |

### Table F — Per-case verdicts (modal answer and agreement)

`modal (agreement, votes)`; vote counts sum to the 3 repetitions.

| Case | Eval | gold | jev | claude-opus-5 | gpt-5.6-sol |
|---|---|---|---|---|---|
| q01 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q01 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q01 | quality | 4 | 4 (100.0%, 4:3) | 3 (100.0%, 3:3) | 4 (100.0%, 4:3) |
| q02 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q02 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q02 | quality | 4 | 4 (100.0%, 4:3) | 3 (100.0%, 3:3) | 4 (100.0%, 4:3) |
| q03 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q03 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q03 | quality | 4 | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) |
| q04 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q04 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q04 | quality | 3 | 4 (100.0%, 4:3) | 3 (100.0%, 3:3) | 4 (100.0%, 4:3) |
| q05 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q05 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q05 | quality | 4 | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) | 4 (100.0%, 4:3) |
| q05v1 | abstain_ok | false | false (100.0%, false:3) | false (100.0%, false:3) | true (100.0%, true:3) |
| q05v1 | grounded | false | false (100.0%, false:3) | false (100.0%, false:3) | false (100.0%, false:3) |
| q05v1 | quality | 1 | 3 (100.0%, 3:3) | 2 (100.0%, 2:3) | 2 (66.7%, 2:2, 3:1) |
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
| q10 | quality | 3 | 3 (100.0%, 3:3) | 4 (100.0%, 4:3) | 4 (66.7%, 4:2, 3:1) |
| q11 | abstain_ok | true | true (100.0%, true:3) | true (100.0%, true:3) | true (100.0%, true:3) |
| q11 | grounded | true | true (100.0%, true:3) | true (100.0%, true:3) | false (66.7%, false:2, true:1) |
| q11 | quality | 3 | 2 (100.0%, 2:3) | 3 (100.0%, 3:3) | 4 (66.7%, 4:2, 3:1) |
