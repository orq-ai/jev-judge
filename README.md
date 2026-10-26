# jev-judge — how repeatable is your judge?

The reproduction kit for Orq's "Jev as a judge" repeatability study on a documentation agent.

Twelve runs of a docs agent (an Orq managed agent with one search tool over docs.orq.ai) were generated
once and frozen verbatim, and ten more were written by hand, each carrying one specific failure. Labels are
fixed. Then six judges scored the same 22 frozen cases over and over, so every difference between
repetitions is judge noise and nothing else.

* **22 frozen cases** in `data/docs_rag/frozen.jsonl`:
  * 11 user questions (how-to, comparison, yes/no, what-is, and two the documentation does not cover);
  * `q05v1`, an earlier agent version's answer to q05 that invents a comparison no retrieved page makes.
    It is the only failure the agent produced on its own;
  * `h01`..`h10`, handcrafted negatives. Each keeps a frozen run's question and retrieved pages and replaces
    only the final message (`data/docs_rag/handcrafted.jsonl`, merged by `scripts/docs_agent_handcraft.py`).
* **3 evals per case**: `grounded` (boolean), `abstain_ok` (boolean) and `quality` (level 0-4). Gold over
  the 22 cases: 12 grounded / 10 not; 18 / 4 on `abstain_ok`; quality 7 x 4, 4 x 3, 6 x 1, 5 x 0.
* **Three arms**, all with Jev (`typesafe/jev-latest` through the Orq Classify endpoint) as one of the judges:
  * **main**, 20 repetitions: Jev, `gpt-5.6-luna`, `gemini-3.8-flash`, `deepseek-v4.1-flash`, with the LLM
    judges at temperature 1.0. 1,320 decisions per judge (22 cases x 3 evals x 20).
  * **matched**, 20 repetitions: Jev, luna at `temperature: 0` and gemini with `reasoning.effort: none`, to
    check whether the variance is just the sampler. Deepseek is not in this arm.
  * **frontier**, 3 repetitions: Jev, `claude-opus-5` and `gpt-5.6-sol`, 198 calls per LLM judge.

Every raw per-repetition prediction is committed, so you can rebuild every table and chart without an API
key and without spending anything.

## Headline numbers

All from the committed results; the commands under [Reproduce the tables](#reproduce-the-tables) regenerate
them.

**Binary accuracy against the labels, main run** (`results/docs_rag/blog_tables.md`, Table A; 880 binary
decisions per judge, a failed call counts as wrong):

| Judge | abstain_ok | grounded | pooled | failed calls (all evals) |
|---|---|---|---|---|
| gemini-3.8-flash | 82.0% | 95.5% | 88.8% (781/880) | 2 |
| jev | 68.0% | 100.0% | 84.0% (739/880) | 0 |
| deepseek-v4.1-flash | 71.1% | 94.5% | 82.8% (729/880) | 6 |
| gpt-5.6-luna | 63.2% | 94.3% | 78.8% (693/880) | 4 |
| baseline(majority) | 81.8% | 54.5% | 68.2% | 0 |

**Signal value** (accuracy x repeatability over all three evals, `results/docs_rag/pareto.md`): gemini
0.800, opus 0.798 (3 repetitions), Jev 0.741, sol 0.718 (3 repetitions), luna 0.695, deepseek 0.690,
always-majority baseline 0.561. In the matched arm gemini drops to 0.742 and luna to 0.686.

**Cost per 1,000 traces** (Table C2 of each run's `blog_tables.md`). A trace is one agent run judged on
all three evals once: one classify call for Jev, three calls for an LLM judge. Judging the same 22 states
again and again is what a provider prompt cache rewards, so the billed figure understates what 1,000
distinct traces would cost. The list-price column reprices the mean tokens per call at the router's
uncached rate.

| Judge | arm | billed | list price | cached input |
|---|---|---|---|---|
| jev | main | $0.47 | $0.47 (billed; token usage not stored) | – |
| gpt-5.6-luna | main | $1.15 | $6.28 | 100.0% |
| deepseek-v4.1-flash | main | $3.81 | $11.13 | 91.3% |
| gemini-3.8-flash | main | $15.17 | $28.63 | 60.7% |
| gpt-5.6-sol | frontier | $53.47 | $120.43 | 64.7% |
| claude-opus-5 | frontier | $246.66 | $246.66 | 0.0% |

The case that separates the judges is `q05v1`, the agent's own hallucination: Jev and opus call it not
grounded on every repetition, luna on 11 of 20, deepseek on 1 of 20, gemini and sol on none. All nine
ungrounded handcrafted cases are called not grounded by every judge on every completed repetition.

## Caveats

Read these before quoting any number.

* **The abstention labels are disputed.** On `h01`..`h07` the retrieved pages cover the question and the
  assistant answered (wrongly on six, with a grounded but useless non-answer on `h06`), so we labelled all
  seven `abstain_ok: true`. Most judges read the criterion as "answered correctly" and say `false`. Jev and
  luna say `false` on all seven, on every repetition. Flipping those seven labels would take Jev's modal
  `abstain_ok` matches from 15 to 22 of 22 and gemini's from 18 to 17, so the overall signal-value ranking
  depends on this column.
* **`h06` is hard to defend.** It is labelled grounded, so nothing charges the non-answer, and every
  20-repetition judge and opus read it as `abstain_ok: false` on every repetition.
* **One real negative carries the grounding result.** `q05v1` is the only ungrounded answer the agent
  produced itself (one in 23 frozen runs of two agent versions).
* **Handcrafted negatives are easy.** Every judge rejects all nine ungrounded handcrafted cases on every
  completed repetition. They balance the label column without separating the judges.
* **The labels are one reviewer's.** Claude proposed the labels for the frozen runs; one person reviewed and
  edited every one in a single pass. Handcrafted labels follow from construction. The quality column
  measures agreement with us.
* **Billed cost is a prompt-cache price.** Every LLM cost except opus's was billed with a cache discount.
  The list-price column is the correction, and it relies on the router's token counts and posted rates
  (2026-09-20). Jev is billed per input token with no cache discount.
* **Latencies are an order of magnitude.** Several arms ran against the same router at the same time from
  one laptop, with 6 calls in flight per LLM judge and Jev on an 8-thread pool.
* **The two judge paths differ.** Jev answers all three evals in one classify call; each LLM judge sees one
  eval per call. The input rendering differs too. Read the comparison as Jev as shipped against an LLM judge
  as shipped.
* **Model aliases float.** `typesafe/jev-latest`, `gpt-5.6-luna`, `gemini-3.8-flash`, `deepseek-v4.1-flash`,
  `claude-opus-5` and `gpt-5.6-sol` are unpinned. Rerunning the judges may hit different services.
* **Three repetitions say little about repeatability.** The frontier arm is for accuracy, cost and latency.
* **Opus ran through chat completions.** It cannot use the responses endpoint with the integer-range
  schema, so evaluatorq fell back to chat completions with a JSON object format. Every quality value it
  returned was in 0-4.

## Layout

```
data/docs_rag/
  questions.jsonl      22 rows: 11 questions, q05v1, h01..h10 (`from` = the case whose searches they keep)
  frozen.jsonl         one row per case; `raw` is the verbatim /v3/router/responses payload. Never regenerate after labelling
  handcrafted.jsonl    the source of the h* rows: replacement answer, perturbation, labels
  labels.jsonl         the gold: grounded, abstain_ok, quality, note
  annotation_sheet.md  human-readable view of frozen.jsonl (searches, retrieved pages, answer)
  README.md            what each field means and how the labels were decided
results/docs_rag/          main arm (20 reps, temperature 1.0), plus the all-arm pareto.md and charts
results/docs_rag_matched/  matched arm (20 reps, sampling off where the router allows it)
results/docs_rag_sota/     frontier arm (3 reps, claude-opus-5 and gpt-5.6-sol)
  <judge>.jsonl            every repetition of one judge; one row per decision, rows carry `rep`
  repeat_summary.json      every metric per judge
  blog_tables.md           accuracy, modal accuracy, variance, cost, signal value, unstable cells, per-case votes
  blog_metrics.json        the same numbers as JSON
  pareto.md, pareto_*.png, pareto_*.html   signal value against latency and against cost, all arms
src/jev_judge/
  tasks.py        the three evals and the frozen-run loader
  models.py       the Jev adapter over the Classify endpoint
  repeat.py       every metric, defined once
  results.py      writing prediction rows
  chart_style.py  palette and axis styling for the Pareto charts
scripts/
  docs_agent_freeze.py      invoke the agent and freeze its responses
  docs_agent_handcraft.py   merge handcrafted.jsonl into the frozen set
  docs_agent_experiment.py  run the judges (paid)
  docs_agent_analysis.py    tables and JSON from a results dir (free)
  docs_agent_pareto.py      Pareto charts across results dirs (free)
```

## Setup

```bash
uv sync
```

Regenerating the tables needs no key. Running the judges or freezing new agent runs needs
`export ORQ_API_KEY=...`, the only credential anything here reads.

## Reproduce the tables

Free, no network. These rewrite `blog_tables.md`, `blog_metrics.json` and `repeat_summary.json` in each
directory, then the Pareto charts and `pareto.md` in `results/docs_rag/`:

```bash
uv run python scripts/docs_agent_analysis.py --dir results/docs_rag
uv run python scripts/docs_agent_analysis.py --dir results/docs_rag_matched --compare results/docs_rag
uv run python scripts/docs_agent_analysis.py --dir results/docs_rag_sota
uv run python scripts/docs_agent_pareto.py \
  --dir results/docs_rag --dir results/docs_rag_matched:matched --dir results/docs_rag_sota:sota
git status --short results/   # only the two pareto_*.html files change: plotly assigns random element ids
```

`--compare` adds Table G, a before/after of the two runs. A `:label` suffix on `--dir` keeps judges that
appear in several runs apart on the charts. `--out` picks another directory for the charts.

Spot-check the headline numbers:

```bash
grep -A7 '^| Judge | abstain_ok | grounded | pooled' results/docs_rag/blog_tables.md
grep -E '^\| (jev|gemini|deepseek|gpt|claude|baseline)' results/docs_rag/pareto.md
grep -h -A9 'Table C2' results/docs_rag/blog_tables.md results/docs_rag_sota/blog_tables.md | grep -E '^\| [a-z]'
```

## Rerun the judges

These make paid calls through Orq. They reuse the committed frozen cases and labels; nothing regenerates
the agent runs.

```bash
# main arm: 22 cases x 3 evals x 20 reps x 4 judges
uv run python scripts/docs_agent_experiment.py --reps 20
# matched arm
uv run python scripts/docs_agent_experiment.py --reps 20 --matched \
  --judges google-ai/gemini-3.8-flash,openai/gpt-5.6-luna --out results/docs_rag_matched
# frontier arm
uv run python scripts/docs_agent_experiment.py --reps 3 \
  --judges anthropic/claude-opus-5,openai/gpt-5.6-sol --out results/docs_rag_sota
```

Add `--no-send` to keep results local instead of uploading them to an Orq experiment, and
`--reps 1 --out /tmp/smoke` for a cheap smoke test. Our runs cost $9.07 (main: gemini $6.68, deepseek
$1.68, luna $0.51, Jev $0.21), $6.30 (matched: gemini $5.48, luna $0.61, Jev $0.21) and $19.84 (frontier:
opus $16.28, sol $3.53, Jev $0.03). The main arm took about 24 minutes for luna, deepseek and Jev together
and 17 more for gemini.

`JUDGE_CONCURRENCY` in `scripts/docs_agent_experiment.py` is 6 in-flight calls per judge model; higher
fan-out earned 500s, 429s and timeouts. A call that still fails after retries is kept as a `pred: null`
row and counted everywhere: wrong for accuracy, a non-modal vote for repeatability, left out of the
quality variance.

To rebuild the dataset from scratch instead: `scripts/docs_agent_freeze.py` invokes an Orq managed agent
called `docs-agent` for every question not yet in `frozen.jsonl`, and `scripts/docs_agent_handcraft.py`
appends the handcrafted cases. Both skip ids that already exist, so running them on the committed data
changes nothing.

## How the metrics are defined

`src/jev_judge/repeat.py` is the single definition of every metric; the experiment, the analysis and the
Pareto script all import from it. The definitions follow LangChain's "Jev-as-a-Judge for Agent Evals".

* **accuracy**: share of (case, eval, repetition) decisions matching the label; a failed call is wrong.
* **modal accuracy**: one vote per case, the most common answer over repetitions. A tie goes to the value
  seen first in repetition order, so a 10-10 split is not a majority.
* **repeatability**: share of repetitions agreeing with the case's modal answer, averaged over cases; a
  failed call is a non-modal vote.
* **signal value**: accuracy x repeatability. A judge that is stable and wrong scores badly, as does one
  that is right on average and wobbles.
* **variance**: per-case population variance of the quality level, normalised to 0-1.
* **cost and latency**: split per physical call and per decision, because Jev makes one call per case and
  the LLM judges one per (case, eval).

## Tests

Fixture-only, no network:

```bash
uv run pytest -q
uv run ruff check .
```

## Licence

MIT, see `LICENSE`.
