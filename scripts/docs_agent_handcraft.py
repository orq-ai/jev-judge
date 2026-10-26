"""Add the handcrafted negative cases to the docs-agent set.

`data/docs_rag/handcrafted.jsonl` holds one row per case: `id`, `from` (the frozen case whose searches it keeps),
`perturbation` (what was changed), `answer` (the replacement final message) and proposed labels. Each case is the
frozen `from` row with only the final message text replaced, so the judges see the same retrieved pages and a
different answer. Appends to `frozen.jsonl`, `questions.jsonl` and `labels.jsonl` (existing ids untouched) and
regenerates `annotation_sheet.md`.

    uv run python scripts/docs_agent_handcraft.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loguru import logger

from docs_agent_freeze import DATA, LABEL_FIELDS, sheet


def read(name: str) -> list[dict]:
    return [json.loads(line) for line in (DATA / name).read_text().splitlines() if line]


def write(name: str, rows: list[dict]) -> None:
    (DATA / name).write_text(''.join(json.dumps(r) + '\n' for r in rows))


def main() -> None:
    frozen, questions, labels = read('frozen.jsonl'), read('questions.jsonl'), read('labels.jsonl')
    by_id = {r['id']: r for r in frozen}
    have = {r['id'] for r in frozen}
    for c in read('handcrafted.jsonl'):
        if c['id'] in have:
            continue
        row = copy.deepcopy(by_id[c['from']])
        row['id'] = c['id']
        row['perturbation'] = c['perturbation']
        messages = [o for o in row['raw']['output'] if o.get('type') == 'message']
        messages[0]['content'] = [{'type': 'output_text', 'text': c['answer']}]
        row['raw']['output'] = [o for o in row['raw']['output'] if o.get('type') != 'message' or o is messages[0]]
        frozen.append(row)
        questions.append({'id': c['id'], 'question': row['question'], 'kind': row['kind'], 'from': c['from']})
        labels.append({'id': c['id'], **{k: c[k] for k in LABEL_FIELDS}, 'note': c['note']})
        logger.info(f'✓ {c["id"]} from {c["from"]}: {c["perturbation"]}')
    write('frozen.jsonl', frozen)
    write('questions.jsonl', questions)
    write('labels.jsonl', labels)
    (DATA / 'annotation_sheet.md').write_text(sheet(frozen))


if __name__ == '__main__':
    main()
