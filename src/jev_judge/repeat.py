"""Judge-repeatability metrics over repeated prediction rows (LangChain "Jev-as-a-Judge" style).

One definition of every metric in the repo: `scripts/docs_agent_analysis.py` (blog tables) and
`scripts/docs_agent_experiment.py` (console table, `repeat_summary.json`) both import from here.

A *row* is one decision: `{id, qid, type, gold, pred, rep, cost, latency_ms}`, optionally `call_id` and the
per-call `explanation` / `probs` / `token_usage` the experiment records. Runs from 2026-09-20 on carry that
call's own `latency_ms`; older runs repeated the cell mean on every row, which makes their percentiles flat.
A *cell* is the list of rows for one (eval, case) across repetitions.

A failed call (`pred is None`) is a first-class category:

* **accuracy** — counted as wrong (it is a decision the judge owed and did not deliver);
* **repeatability** — counted as a non-modal vote, so 99 identical answers + 1 failure is 99%;
* **variance** — excluded from the values, with the failure rate reported next to it.

One *call* is not one decision: LLM judges answer one question per call, Jev answers all questions of a
case in a single classify call, so cost and latency have to be divided differently. `call_id` (written by
newer runs) groups rows into calls; older files fall back to `(id, rep)` for Jev and `(id, qid, rep)` for
everyone else.
"""

from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np

SCORE_MAX = 4.0  # top level of the `score` evals; variance is reported on pred/SCORE_MAX
FAILED = 'failed'  # vote label for a call that returned no prediction
JEV_JUDGE = 'jev'  # answers every question of a case in one classify call
BASELINE_JUDGE = 'baseline(majority)'

Cells = dict[tuple[str, str], list[dict]]  # (qid, case id) -> rows, one per repetition


def cells_of(rows: list[dict]) -> Cells:
    """Rows grouped into (eval, case) cells."""
    out: Cells = defaultdict(list)
    for r in rows:
        out[r['qid'], r['id']].append(r)
    return dict(out)


def eval_ids(rows: list[dict]) -> tuple[list[str], list[str]]:
    """(binary eval ids, score eval ids), sorted."""
    return (
        sorted({r['qid'] for r in rows if r['type'] != 'score'}),
        sorted({r['qid'] for r in rows if r['type'] == 'score'}),
    )


def rep_count(cells: Cells) -> int:
    """The repetition count every cell shares; raises when the run is ragged (a partial run is not summarisable)."""
    sizes = {len(cell) for cell in cells.values()}
    if len(sizes) != 1:
        counts = {f'{q}|{case}': len(cell) for (q, case), cell in sorted(cells.items())}
        raise ValueError(f'cells have unequal repetition counts {sorted(sizes)}: {counts}')
    return sizes.pop()


def votes(cell: list[dict]) -> list[str]:
    """One vote per repetition, failed calls included as `FAILED`; always as long as the cell."""
    return [FAILED if r['pred'] is None else r['pred'] for r in cell]


def values(cell: list[dict]) -> list[str]:
    """The non-failed predictions of a cell."""
    return [r['pred'] for r in cell if r['pred'] is not None]


def modal(cell: list[dict]) -> tuple[str | None, float]:
    """Most common non-failed prediction and the share of *all* repetitions that agree with it."""
    ok = values(cell)
    if not ok:
        return None, 0.0
    value, count = Counter(ok).most_common(1)[0]
    return value, count / len(cell)


def vote_distribution(cell: list[dict]) -> dict[str, int]:
    """Vote counts including `failed:N`; sums to the repetition count."""
    return dict(Counter(votes(cell)).most_common())


def counts(cells: Cells, qids: list[str]) -> tuple[int, int, int]:
    """(correct, decisions, failed calls) over every (case, rep) of `qids`; a failed call is never correct."""
    rows = [r for (qid, _), cell in cells.items() if qid in qids for r in cell]
    return (
        sum(r['pred'] is not None and r['pred'] == r['gold'] for r in rows),
        len(rows),
        sum(r['pred'] is None for r in rows),
    )


def accuracy(cells: Cells, qids: list[str]) -> dict:
    """Share of decisions matching gold, failures counted wrong."""
    correct, total, failed = counts(cells, qids)
    return {
        'correct': correct,
        'total': total,
        'failed': failed,
        'value': correct / total if total else float('nan'),
    }


def modal_accuracy(cells: Cells, qids: list[str]) -> dict:
    """Share of cells whose modal answer matches gold: the verdict a single production draw would most likely give."""
    hits = [modal(cell)[0] == cell[0]['gold'] for (qid, _), cell in cells.items() if qid in qids]
    return {'correct': sum(hits), 'total': len(hits), 'value': sum(hits) / len(hits) if hits else float('nan')}


def repeatability(cells: Cells, qids: list[str]) -> float:
    """Mean over cells of the share of repetitions agreeing with the modal answer; failures are non-modal."""
    agree = [modal(cell)[1] for (qid, _), cell in cells.items() if qid in qids]
    return float(np.mean(agree)) if agree else float('nan')


def case_variances(cells: Cells, qid: str) -> dict[str, float]:
    """Population variance of the 0-1 normalised score across repetitions, per case; failures excluded."""
    out = {}
    for (q, case), cell in cells.items():
        if q != qid:
            continue
        vals = [int(p) / SCORE_MAX for p in values(cell)]
        out[case] = float(np.var(vals)) if vals else float('nan')
    return dict(sorted(out.items()))


def gold_distribution(cells: Cells, qid: str) -> dict[str, int]:
    """Gold labels of `qid` counted over cases (not over repetitions)."""
    golds = [cell[0]['gold'] for (q, _), cell in sorted(cells.items()) if q == qid]
    return dict(Counter(golds).most_common())


def call_id(row: dict, judge: str) -> tuple:
    """Which physical call a row belongs to; `call_id` when the run recorded it, else the per-judge convention."""
    if row.get('call_id'):
        return (row['call_id'],)
    if judge == JEV_JUDGE:  # one classify call answers every question of the case
        return (row['id'], row['rep'])
    return (row['id'], row['qid'], row['rep'])


def economics(cells: Cells, judge: str) -> dict:
    """Cost and latency split per physical call and per decision, with latency percentiles over calls.

    One `latency_ms` per physical call (rows of a shared call repeat it, so the first row of each group is
    taken). Runs before 2026-09-20 recorded the per-cell mean on every row; their percentiles are means of
    means, not request samples.
    """
    rows = [r for cell in cells.values() for r in cell]
    by_call: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_call[call_id(r, judge)].append(r)
    call_latencies = [group[0]['latency_ms'] / 1000 for group in by_call.values()]
    total = float(sum(r['cost'] for r in rows))
    calls, decisions = len(by_call), len(rows)
    return {
        'calls': calls,
        'decisions': decisions,
        'decisions_per_call': decisions / calls if calls else float('nan'),
        'cost_per_call_usd': total / calls if calls else float('nan'),
        'cost_per_decision_usd': total / decisions if decisions else float('nan'),
        'total_cost_usd': total,
        'latency_per_call_s': float(np.mean(call_latencies)) if call_latencies else float('nan'),
        'latency_p50_s': float(np.percentile(call_latencies, 50)) if call_latencies else float('nan'),
        'latency_p95_s': float(np.percentile(call_latencies, 95)) if call_latencies else float('nan'),
        'latency_per_decision_s': float(sum(call_latencies) / decisions) if decisions else float('nan'),
    }


def majority_baseline(cells: Cells) -> Cells:
    """Synthetic judge that always answers the most common gold value of the eval (the majority-class baseline)."""
    majority = {qid: next(iter(gold_distribution(cells, qid))) for qid in {q for q, _ in cells}}
    return {
        key: [{**r, 'pred': majority[key[0]], 'cost': 0.0, 'latency_ms': 0.0} for r in cell]
        for key, cell in cells.items()
    }


def summarise(judge: str, rows: list[dict]) -> dict:
    """Every metric for one judge's rows: accuracy, repeatability, signal, variance, failures, economics."""
    cells = cells_of(rows)
    binary_qids, score_qids = eval_ids(rows)
    qids = [*binary_qids, *score_qids]
    groups = {**{q: [q] for q in qids}, 'binary_pooled': binary_qids, 'all': qids}

    acc = {name: accuracy(cells, group) for name, group in groups.items()}
    rep = {name: repeatability(cells, group) for name, group in groups.items()}
    modal_acc = {name: modal_accuracy(cells, group) for name, group in groups.items()}
    variance = {}
    for qid in score_qids:
        per_case = case_variances(cells, qid)
        variance[qid] = {
            'per_case': per_case,
            'mean': float(np.nanmean(list(per_case.values()) or [float('nan')])),
            'failure_rate': acc[qid]['failed'] / max(acc[qid]['total'], 1),
        }
    unstable = {
        qid: {
            case: vote_distribution(cell)
            for (q, case), cell in sorted(cells.items())
            if q == qid and modal(cell)[1] < 1.0
        }
        for qid in qids
    }
    return {
        'judge': judge,
        'model': judge,  # legacy key kept so older readers of repeat_summary.json still work
        'reps': rep_count(cells),
        'cases': sorted({r['id'] for r in rows}),
        'binary_evals': binary_qids,
        'score_evals': score_qids,
        'accuracy': acc,
        'modal_accuracy': modal_acc,
        'repeatability': rep,
        'signal': {name: acc[name]['value'] * rep[name] for name in groups},
        'quality_variance': variance,
        'failures': {'total': acc['all']['failed'], 'per_eval': {qid: acc[qid]['failed'] for qid in qids}},
        'unstable': unstable,
        'modal': {
            f'{q}|{case}': {
                'gold': cell[0]['gold'],
                'modal': modal(cell)[0],
                'agreement': modal(cell)[1],
                'votes': vote_distribution(cell),
            }
            for (q, case), cell in cells.items()
        },
        'gold_distribution': {qid: gold_distribution(cells, qid) for qid in qids},
        'cost': economics(cells, judge),
    }
