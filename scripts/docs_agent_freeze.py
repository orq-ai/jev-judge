"""Freeze docs-agent outputs: one responses call per question, the raw payload saved verbatim under `raw`.

Everything else (answer text, searches, trace id, cost) is derived locally from `raw` via `docs_rag_answer()`
and `searches()`, which share the MCP-unwrap helper `docs_rag_pages()` with the judges' view in `tasks.py`.
Writes `frozen.jsonl` (what every judge sees), `annotation_sheet.md` (what the human reads) and `labels.jsonl`
(blank rows for new cases, existing labels kept). Questions already frozen are never regenerated, so adding a
question and rerunning is safe.

    uv run python scripts/docs_agent_freeze.py
    DOCS_AGENT=agent/docs-agent-mini DOCS_RAG_DIR=data/docs_rag/mini_gpt5 uv run python scripts/docs_agent_freeze.py
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from loguru import logger

from jev_judge.models import api_key, remote_retry
from jev_judge.tasks import docs_rag_answer, docs_rag_pages

AGENT = os.environ.get('DOCS_AGENT', 'agent/docs-agent')
RESPONSES_URL = 'https://my.orq.ai/v3/router/responses'
DATA = Path(os.environ.get('DOCS_RAG_DIR') or Path(__file__).resolve().parents[1] / 'data' / 'docs_rag').resolve()
LABEL_FIELDS = ('grounded', 'abstain_ok', 'quality')


@remote_retry
def invoke(question: str) -> dict:
    r = httpx.post(
        RESPONSES_URL,
        json={'model': AGENT, 'input': question},
        headers={'Authorization': f'Bearer {api_key()}'},
        timeout=180,
    )
    r.raise_for_status()
    return r.json()


def searches(raw: dict) -> list[dict]:
    """Best-effort view of the search_orq_docs calls in a raw responses payload: query, raw result, parsed pages."""
    return [
        {
            'query': json.loads(o['arguments']).get('query'),
            'result': o.get('result'),
            'results': docs_rag_pages(o.get('result')) or [],
        }
        for o in raw['output']
        if o.get('type') == 'orq:search_orq_docs'
    ]


def sheet(rows: list[dict]) -> str:
    md = [
        '# docs-agent annotation sheet',
        '',
        'Fill `labels.jsonl`: `grounded` true/false, `abstain_ok` true/false, `quality` 0-4, free-text `note`.',
        'Judge against the retrieved pages listed under each search, not against the live docs.',
        '',
    ]
    for r in rows:
        md += [
            f'## {r["id"]} [{r["kind"]}] {r["question"]}',
            '',
            f'trace `{r["raw"]["telemetry"]["trace_id"]}`, ${r["raw"]["usage"]["total_cost"]:.4f}',
            '',
        ]
        for s in searches(r['raw']):
            hits = (
                ', '.join(f'[{p["title"]}]({p["url"]})' for p in s['results'])
                or f'no pages parsed: `{str(s["result"])[:120]}`'
            )
            md += [f'**search** `{s["query"]}`: {hits}', '']
        md += ['**answer**', '', docs_rag_answer(r['raw']), '', '---', '']
    return '\n'.join(md)


def main() -> None:
    questions = [json.loads(line) for line in (DATA / 'questions.jsonl').read_text().splitlines() if line]
    frozen_path = DATA / 'frozen.jsonl'
    done = (
        {json.loads(line)['id']: json.loads(line) for line in frozen_path.read_text().splitlines()}
        if frozen_path.exists()
        else {}
    )
    labels_path = DATA / 'labels.jsonl'
    labels = (
        {json.loads(line)['id']: json.loads(line) for line in labels_path.read_text().splitlines()}
        if labels_path.exists()
        else {}
    )
    todo = [q for q in questions if q['id'] not in done]  # already frozen and possibly labelled: never regenerate
    with ThreadPoolExecutor(max_workers=len(todo) or 1) as pool:
        fresh = dict(zip([q['id'] for q in todo], pool.map(lambda q: invoke(q['question']), todo), strict=False))
    rows = []
    for q in questions:
        row = done.get(q['id']) or {**q, 'raw': fresh[q['id']]}
        rows.append(row)
        if q['id'] in fresh:
            hits = [len(s['results']) for s in searches(row['raw'])]
            logger.info(
                f'✓ {q["id"]} search hits {hits}, ${row["raw"]["usage"]["total_cost"]:.4f}, {len(docs_rag_answer(row["raw"]))} chars'
            )
    frozen_path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    (DATA / 'annotation_sheet.md').write_text(sheet(rows))
    merged = [labels.get(r['id'], {'id': r['id'], **dict.fromkeys(LABEL_FIELDS, ''), 'note': ''}) for r in rows]
    labels_path.write_text(''.join(json.dumps(b) + '\n' for b in merged))
    logger.info(f'✓ wrote frozen.jsonl, annotation_sheet.md, labels.jsonl -> {DATA}')


if __name__ == '__main__':
    main()
