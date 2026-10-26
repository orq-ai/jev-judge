# Docs RAG judge-repeatability set

Frozen runs of the Orq managed agent `docs-agent` (search tool over docs.orq.ai), used to measure judge
repeatability the way LangChain's "Jev-as-a-Judge for Agent Evals" post does:
agent outputs are generated once, labelled once by a human, and only the judges are rerun.

| File | What |
|------|------|
| `questions.jsonl` | 22 rows: 11 user questions, `q05v1` (the v1 agent run of q05, the one natural ungrounded case) and `h01`..`h10`, handcrafted negatives (`from` = the frozen case whose searches they keep); `kind` = how-to / comparison / yes-no / what-is / unanswerable |
| `frozen.jsonl` | one row per case: `raw` = the verbatim `/v3/router/responses` payload (trace id, usage, every tool call and result, final message). Never regenerate after labelling. Handcrafted rows are a copy of their `from` row with only the final message text replaced and a `perturbation` field saying what changed |
| `handcrafted.jsonl` | source of the `h*` rows: replacement answer, perturbation, proposed labels. `scripts/docs_agent_handcraft.py` merges it (existing ids untouched) |
| `annotation_sheet.md` | human-readable view of `frozen.jsonl`, derived locally |
| `labels.jsonl` | human gold per case. Prefilled by the agent author as a proposal; edit in place |

Label fields (judged against the tool results inside `raw`, not against the live docs):

- `grounded`: `true` when every factual claim in the answer is supported by the retrieved pages.
- `abstain_ok`: `true` when the answer answers if the pages cover the question and says the docs do not cover it otherwise.
- `quality`: `0`..`4`, five levels from useless to excellent.

Judges see the search results as parsed pages (`title`, `url`, `content`), not the raw MCP JSON, capped at
60,000 characters per tool result (`DOCS_RAG_ITEM_CAP` in `src/jev_judge/tasks.py`).

Why handcrafted negatives: the agent (gpt-5.6-luna, up to three searches, told to abstain) produced one ungrounded
answer in 23 frozen runs (v1 + v2), and gpt-5-mini with a single search produced about two more in 11, so the
label distribution was 11 positive to 1 negative and a judge that always answered `true` scored 91.7% on the
binary evals. The ten `h*` cases
keep the real retrieved pages and replace the answer with a specific failure: a fabricated setting, swapped
definitions, a contradicted page, wrong details in a right answer, invented rows in a right table, a grounded but
useless answer, an unjustified abstain, and confident answers to the two unanswerable questions. Gold is now 12
grounded / 10 not, 18 / 4 on abstain, quality 7-4-6-5 over levels 4/3/1/0.

Freeze new questions (already-frozen ids are skipped, labels kept; needs `ORQ_API_KEY` and an Orq managed agent
called `docs-agent`, or set `DOCS_AGENT`; `DOCS_RAG_DIR` points the script at another directory):

    uv run python scripts/docs_agent_freeze.py

Add handcrafted cases (edit `handcrafted.jsonl`, then; existing ids are skipped):

    uv run python scripts/docs_agent_handcraft.py
