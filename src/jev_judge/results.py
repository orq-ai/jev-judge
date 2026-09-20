"""Prediction-row files.

A prediction row is one decision: `{id, qid, type, gold, pred, rep, call_id, cost, latency_ms, ...}`.
One `<judge>__rep<NN>.jsonl` per judge and repetition; `jev_judge.repeat` turns them into metrics.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from pathlib import Path


def write_results(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    logger.info(f'✓ wrote {len(rows)} rows -> {path}')


def read_results(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]
