# Docs RAG judge-repeatability set

Frozen runs of the Orq managed agent `docs-agent` (search tool over docs.orq.ai), used to measure judge
repeatability the way LangChain's "Jev-as-a-Judge for Agent Evals" post does:
agent outputs are generated once, labelled once by a human, and only the judges are rerun.

| File | What |
|------|------|
| `questions.jsonl` | 12 rows: 11 user questions plus `q05v1`, the v1 agent run of q05 kept as the ungrounded negative case, `kind` = how-to / comparison / yes-no / what-is / unanswerable |
| `frozen.jsonl` | one row per question: `raw` = the verbatim `/v3/router/responses` payload (trace id, usage, every tool call and result, final message). Never regenerate after labelling |
| `annotation_sheet.md` | human-readable view of `frozen.jsonl`, derived locally |
| `labels.jsonl` | human gold per case. Prefilled by the agent author as a proposal; edit in place |

Label fields (judged against the tool results inside `raw`, not against the live docs):

- `grounded`: `true` when every factual claim in the answer is supported by the retrieved pages.
- `abstain_ok`: `true` when the answer answers if the pages cover the question and says the docs do not cover it otherwise.
- `quality`: `0`..`4`, five levels from useless to excellent.

Judges see the search results as parsed pages (`title`, `url`, `content`), not the raw MCP JSON. An
earlier 20-repetition run fed them the raw payload truncated at 20k chars per item and every judge landed
at 58-67% on `grounded`, because the evidence a claim needs was often in the part that was cut; that run
is not shipped here.

Freeze new questions (already-frozen ids are skipped, labels kept):

    uv run python scripts/docs_agent_freeze.py
