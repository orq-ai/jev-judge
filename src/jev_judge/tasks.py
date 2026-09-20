"""The docs-agent judge task: the three evals, and the frozen agent runs every judge sees.

Questions use the Orq Classify / TypeSafe shape verbatim:
  noul:   {"type": "noul",  "instructions": str, "criteria": {"true": ..., "false": ...}}
  score:  {"type": "score", "instructions": str, "criteria": [level description, ...]}
Gold is a string per question: "true"/"false", or a level index.

`build_docs_rag()` reads `data/docs_rag/frozen.jsonl` (raw `/v3/router/responses` payloads) and
`labels.jsonl` (the human gold) and returns one row per case: `{id, state, questions, gold, meta}`.
The `state` is what Jev is asked about; `meta.raw` is the same run, which the experiment reshapes
into evaluatorq output items for the LLM judges. Both views share the MCP-unwrap helper below, so
every judge reads the same search results.
"""

from __future__ import annotations

import json
from pathlib import Path

DOCS_RAG_DIR = Path(__file__).resolve().parents[2] / 'data' / 'docs_rag'


def _noul(instructions: str) -> dict:
    return {
        'type': 'noul',
        'instructions': instructions,
        'criteria': {'true': 'Yes, this happened in the conversation.', 'false': 'No, this did not happen.'},
    }


DOCS_RAG_QUESTIONS = {
    'grounded': _noul('Every factual claim in the assistant answer is supported by the retrieved excerpts.'),
    'abstain_ok': _noul(
        'The assistant answered the question when the excerpts cover it, and said the documentation '
        'does not cover it when they do not.'
    ),
    'quality': {
        'type': 'score',
        'instructions': 'Overall quality of the assistant answer for the user who asked the question.',
        'criteria': [
            'Useless: wrong, empty or answers a different question.',
            'Poor: partly relevant but misleading, incomplete or hard to act on.',
            'Acceptable: correct on the main point, with gaps or minor errors.',
            'Good: correct, complete and actionable, with minor polish issues.',
            'Excellent: correct, complete, concise and cites the right pages.',
        ],
    },
}
DOCS_RAG_ITEM_CAP = 60000  # chars per tool-result item: Jev rejects states past ~100k chars (max_tokens_exceeded)


def docs_rag_pages(result: object) -> list[dict] | None:
    """Parsed pages ({title, description, content, url}) from a search_orq_docs result; None when the search failed."""
    node = result
    for _ in range(6):  # unwrap JSON-RPC / MCP content nesting until a {"results": [...]} appears
        if isinstance(node, str):
            try:
                node = json.loads(node)
            except json.JSONDecodeError:
                return None
        elif isinstance(node, dict) and 'results' not in node:
            node = node.get('result') or (node.get('content') or [{}])[0].get('text')
        else:
            break
    return node['results'] if isinstance(node, dict) and 'results' in node else None


def docs_rag_answer(raw: dict) -> str:
    """The assistant answer text of a raw responses payload: every `message` item's text, concatenated."""
    return ''.join(c.get('text', '') for o in raw['output'] if o.get('type') == 'message' for c in o.get('content', []))


def docs_rag_search_result(item: dict) -> str:
    """Tool result as the judges see it: parsed pages when the search worked, the raw error text otherwise."""
    pages = docs_rag_pages(item.get('result'))
    payload = {'results': pages} if pages is not None else {'error': str(item.get('result'))[:2000]}
    text = json.dumps(payload)
    if len(text) > DOCS_RAG_ITEM_CAP:
        text = text[:DOCS_RAG_ITEM_CAP] + f' ...[truncated, {len(text) - DOCS_RAG_ITEM_CAP} more chars]'
    return text


def _docs_rag_run(raw: dict) -> str:
    """The `output` items as JSON, one per line; reasoning dropped, search results replaced by their parsed pages."""
    lines = []
    for item in raw['output']:
        if item.get('type') == 'reasoning':
            continue
        if item.get('type') == 'orq:search_orq_docs':
            item = {**item, 'result': docs_rag_search_result(item)}
        lines.append(json.dumps(item))
    return '\n'.join(lines)


def build_docs_rag() -> list[dict]:
    """Frozen docs-agent runs (`data/docs_rag/frozen.jsonl`, raw responses payloads) with human labels as gold."""
    labels = {r['id']: r for r in map(json.loads, (DOCS_RAG_DIR / 'labels.jsonl').read_text().splitlines()) if r}
    out = []
    for line in (DOCS_RAG_DIR / 'frozen.jsonl').read_text().splitlines():
        r = json.loads(line)
        state = (
            f'USER QUESTION:\n{r["question"]}\n\nAGENT RUN (responses API output items, verbatim):\n'
            f'{_docs_rag_run(r["raw"])}'
        )
        out.append({
            'id': r['id'],
            'state': state,
            'questions': DOCS_RAG_QUESTIONS,
            'gold': {qid: labels[r['id']][qid] for qid in DOCS_RAG_QUESTIONS},
            'meta': {
                'kind': r['kind'],
                'note': labels[r['id']].get('note', ''),
                'question': r['question'],
                'trace_id': r['raw']['telemetry']['trace_id'],
                'raw': r['raw'],
            },
        })
    return out
