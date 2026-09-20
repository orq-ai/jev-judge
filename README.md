# jev-judge — how repeatable is your judge?

A reproduction kit for a small, complete judge-repeatability study.

Twelve runs of a documentation agent (a search tool over docs.orq.ai) were generated once and frozen
verbatim. One human labelled them once. Then four judges scored the same frozen runs **100 times each**,
so every difference between repetitions is judge noise and nothing else.

* **12 frozen cases** — `data/docs_rag/frozen.jsonl`, raw `/v3/router/responses` payloads with every tool
  call, every search result and the final answer.
* **3 evals per case** — `grounded` (boolean), `abstain_ok` (boolean), `quality` (a 0-4 level).
* **4 judges** — Jev (`typesafe/jev-latest` through the Orq Classify endpoint) and three LLM judges at
  temperature 1: `deepseek-v4.1-flash`, `gemini-3.8-flash`, `gpt-5.6-luna`.
* **100 repetitions** — 12 x 3 x 4 x 100 = 14,400 decisions from 12,000 physical calls. Jev answers all
  three evals of a case in one classify call, which is why calls and decisions differ.
* **a matched arm** — the same run with every LLM judge pinned to the least-sampled regime the router
  allows (`temperature: 0` for luna, `reasoning.effort: none` for gemini and deepseek), to check whether
  the variance is just the sampler. `deepseek-v4.1-flash` is **excluded from the matched tables and
  charts**: with reasoning off, the provider returned server errors on most calls, so its numbers measure
  the outage and not the judge. Its rows are kept, unused, in
  `results/docs_rag_matched/excluded_deepseek/`.
* **a frontier arm** — the same 12 cases and the same three evals judged by `claude-opus-5` and
  `gpt-5.6-sol` (`anthropic/claude-opus-5` and `openai/gpt-5.6-sol` on the router), 3 repetitions instead
  of 100, so 108 calls per judge. It is in `results/docs_rag_sota/`.

The results of all three runs are committed, so you can read the tables and redraw the charts without
spending anything.

## Headline

`results/docs_rag/blog_tables.md` and `results/docs_rag/pareto.md` hold the full numbers. The short
version: Jev repeats itself, the LLM judges do not, and on these 12 cases none of the LLM judges beats
an always-answer-the-majority-class baseline on the binary evals. Turning sampling off does not fix the
instability — `gpt-5.6-luna` at temperature 0 still disagrees with itself across repetitions.

Judging the same 12 states over and over is what a provider prompt cache rewards, so the billed LLM cost
in these runs is lower than the same judge would cost on 1,000 distinct traces. The share of input tokens
the provider served from cache was 100% for `gpt-5.6-sol`, 99.5% for `gpt-5.6-luna`, 65.4% for
`gemini-3.8-flash` and 0% for `claude-opus-5`. Table C2 in each `blog_tables.md` therefore reports cost
per 1,000 traces twice: as billed, and at the model's list price for uncached input. At list price the
LLM judges cost $6.56 (`gpt-5.6-luna`), $26.36 (`gemini-3.8-flash`), $125.45 (`gpt-5.6-sol`) and $259.70
(`claude-opus-5`) per 1,000 traces, against $0.49 for Jev, which is billed per input token with no cache
discount to lose. The main run predates per-call token accounting, so its list-price column is `-`; the
matched and frontier arms carry the token counts.

Read the caveats at the bottom before quoting any of it.

## Layout

```
data/docs_rag/
  questions.jsonl      12 rows: 11 user questions plus q05v1, an earlier agent run kept as a negative case
  frozen.jsonl         one row per question; `raw` is the verbatim responses payload. Never regenerate after labelling
  labels.jsonl         the human gold: grounded, abstain_ok, quality, note
  annotation_sheet.md  human-readable view of frozen.jsonl (searches, retrieved pages, answer)
  README.md            what each field means and how the labels were decided
results/docs_rag/          the main run (100 reps, temperature 1)
results/docs_rag_matched/  the matched arm (100 reps, sampling off where the router allows it)
results/docs_rag_sota/     the frontier arm (3 reps, claude-opus-5 and gpt-5.6-sol)
  excluded_deepseek/       the matched deepseek rows, excluded from that arm's tables and charts
  <judge>__rep<NN>.jsonl   one file per judge and repetition; one row per decision
  repeat_summary.json      every metric per judge
  blog_tables.md           accuracy, variance, cost, signal value, unstable cases, per-case verdicts
  blog_metrics.json        the same numbers as JSON
  pareto*.png, pareto.md   quality against speed and against cost
  run.log                  the console log of the run that produced the files
src/jev_judge/
  tasks.py     the three evals and the frozen-run loader
  models.py    the Jev adapter over the Classify endpoint
  repeat.py    every metric, defined once
  results.py   reading and writing prediction rows
scripts/       freeze, experiment, analysis, pareto
```

## Setup

```bash
uv sync
export ORQ_API_KEY=...   # the only credential anything here reads
```

`ORQ_API_KEY` is needed to *run* the judges. Re-analysing the committed results needs no key.

## Commands

**Freeze the agent outputs** (optional — `data/docs_rag/frozen.jsonl` is already committed, and
regenerating it after labelling would invalidate the labels). Needs an Orq managed agent called
`docs-agent` in your workspace:

```bash
uv run python scripts/docs_agent_freeze.py
```

**Run the judges.** This costs money and takes time (see below):

```bash
uv run python scripts/docs_agent_experiment.py --reps 100
uv run python scripts/docs_agent_experiment.py --reps 100 --matched --out results/docs_rag_matched
```

`--judges` takes a comma-separated list of router model ids to run beside Jev, which is how the frontier
arm was produced:

```bash
uv run python scripts/docs_agent_experiment.py --reps 3 \
    --judges anthropic/claude-opus-5,openai/gpt-5.6-sol \
    --out results/docs_rag_sota
```

Add `--no-send` to keep the results local instead of uploading them to an Orq experiment, and
`--reps 1 --out /tmp/smoke` for a cheap smoke test.

**Analyse** (free, no network — rewrites `blog_tables.md`, `blog_metrics.json` and `repeat_summary.json`
in place):

```bash
uv run python scripts/docs_agent_analysis.py --dir results/docs_rag
uv run python scripts/docs_agent_analysis.py --dir results/docs_rag_matched --compare results/docs_rag
uv run python scripts/docs_agent_analysis.py --dir results/docs_rag_sota --compare results/docs_rag
```

`--dir` reads every `*__rep*.jsonl` directly inside it, which is why the excluded deepseek rows sit one
level down in `excluded_deepseek/` and never reach the matched tables.

**Pareto charts** (free), all runs on one pair of axes:

```bash
uv run python scripts/docs_agent_pareto.py --dir results/docs_rag                      # the main run alone
uv run python scripts/docs_agent_pareto.py \
    --dir results/docs_rag --dir results/docs_rag_matched:matched \
    --dir results/docs_rag_sota:sota \
    --out results/docs_rag_matched                                                     # all three, one axis
```

Without `--out` the charts land in the first `--dir`, which would overwrite the single-run charts there.

**Tests** (free, fixture-only):

```bash
uv run pytest -q
uv run ruff check .
```

## Cost and wall clock

| Run | Wall clock | Spend |
|-----|-----------|-------|
| main, 100 reps | ~46 min | ~$23 (gemini $16.38, deepseek $4.23, luna $1.53, Jev $0.59) |
| matched, 100 reps | ~47 min | ~$18 (gemini $13.57, deepseek $1.91, luna $1.53, Jev $0.59) |
| frontier, 3 reps | ~3 min | ~$10 (opus $9.35, sol $0.69, Jev $0.02) |

The matched deepseek spend bought nothing usable — see the exclusion note above.

`JUDGE_CONCURRENCY` in `scripts/docs_agent_experiment.py` is 6 in-flight calls per judge model. Firing
all 720 repetitions of a cell at once earned 500s, 429s and timeouts; at 6 the run is slow but clean.
Four calls failed outright in the main run (all deepseek: three retries-exhausted `InternalServerError`,
one reasoning overflow against `max_tokens=8000`). They are kept as `pred: null` rows and counted
everywhere — wrong for accuracy, a non-modal vote for repeatability, excluded from the variance values
with the failure rate reported next to them.

## How failures and calls are counted

`src/jev_judge/repeat.py` is the single definition of every metric; both the experiment and the analysis
script import from it.

* **accuracy** — share of (case, eval, repetition) decisions matching the label; a failed call is wrong.
* **modal accuracy** — one vote per case, the modal answer over repetitions. What a single production
  draw most likely returns.
* **repeatability** — share of repetitions agreeing with the modal answer, averaged over cases; a failed
  call is a non-modal vote.
* **signal value** — accuracy x repeatability. A judge that is stable and wrong scores badly, as does one
  that is right on average and wobbles.
* **cost and latency** — split per *physical call* and per *decision*, because Jev makes one call per case
  and the LLM judges make one per (case, eval).

## Caveats

* **The labels are one person's reading of 12 cases.** Nobody adjudicated a second opinion.
* **The label column is nearly constant.** 11 of 12 cases are positive on both binary evals, so a judge
  that always answers `true` scores 91.7% pooled. That majority-class baseline is a row in the tables and
  a reference line in the charts.
* **Latencies are not a benchmark.** Each judge ran under its own concurrency regime against a shared
  router, from one laptop. Read the seconds as an order of magnitude. Rows from the matched arm carry
  per-call latency; the main run stored the per-cell mean on every repetition row, so its percentiles are
  percentiles of means.
* **`deepseek-v4.1-flash` with `reasoning.effort: none` is a failed arm, not a floor.** Through this
  provider it produced 1,166 first-attempt `InternalServerError`s and 22 exhausted retries, so it is
  excluded from the matched tables and charts. Nothing in that run should be read as this model's
  no-reasoning quality; the raw rows are in `results/docs_rag_matched/excluded_deepseek/` for anyone who
  wants to see the damage.

## Licence

MIT — see `LICENSE`.
