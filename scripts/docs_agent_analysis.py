"""Blog-style tables over the docs-agent judge-repeatability run (LangChain "Jev-as-a-Judge" replication).

Reads every `<judge>__rep<NN>.jsonl` in a results dir and writes `blog_tables.md` + `blog_metrics.json`
next to them: binary accuracy, quality variance, cost/latency, signal value, unstable cases and per-case
verdicts. `--compare` puts two run dirs side by side (accuracy and repeatability per eval per judge).

Every metric comes from `jev_judge.repeat`; this script only lays the numbers out.

    uv run python scripts/docs_agent_analysis.py --dir results/docs_rag
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Annotated

import numpy as np
import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from jev_judge.repeat import (
    BASELINE_JUDGE,
    SCORE_MAX,
    cells_of,
    majority_baseline,
    summarise,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / 'results' / 'docs_rag'
console = Console(width=200)


def load_judges(path: Path) -> dict[str, list[dict]]:
    """Flat rows per judge, read from every rep file in `path`."""
    rows: dict[str, list[dict]] = defaultdict(list)
    for f in sorted(path.glob('*__rep*.jsonl')):
        judge = f.name.split('__rep')[0]
        rows[judge].extend(json.loads(line) for line in f.read_text().splitlines() if line.strip())
    if not rows:
        raise typer.BadParameter(f'no *__rep*.jsonl files in {path}')
    return dict(rows)


def order_judges(judges: list[str]) -> list[str]:
    return sorted(judges, key=lambda j: (j != 'jev', j))


def pct(x: float) -> str:
    return 'n/a' if np.isnan(x) else f'{x * 100:.1f}%'


def emit(md: list[str], title: str, headers: list[str], rows: list[list[str]], note: str = '') -> None:
    md.append(f'### {title}\n')
    if note:
        md.append(f'{note}\n')
    md.extend(['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|'])
    md.extend('| ' + ' | '.join(r) + ' |' for r in rows)
    md.append('')
    table = Table(title=title, header_style='bold cyan')
    for h in headers:
        table.add_column(h)
    for r in rows:
        table.add_row(*r)
    console.print(table)


def analyse(path: Path) -> dict:
    """Every metric for one run dir, keyed by judge, plus the synthetic majority-class baseline."""
    by_rows = load_judges(path)
    judges = order_judges(list(by_rows))
    per_judge = {judge: summarise(judge, by_rows[judge]) for judge in judges}

    baseline_cells = majority_baseline(cells_of(by_rows[judges[0]]))
    baseline = summarise(BASELINE_JUDGE, [r for cell in baseline_cells.values() for r in cell])

    reps = {j: per_judge[j]['reps'] for j in judges}
    if len(set(reps.values())) != 1:
        raise ValueError(f'judges disagree on repetition count: {reps}')
    score_qids = per_judge[judges[0]]['score_evals']

    jev_var = per_judge.get('jev', {}).get('quality_variance', {})
    for qid in score_qids:
        base = jev_var.get(qid, {}).get('mean')
        for judge in judges:
            entry = per_judge[judge]['quality_variance'][qid]
            entry['x_jev'] = (entry['mean'] / base) if base else None

    return {
        'dir': str(path),
        'judges': judges,
        'cases': per_judge[judges[0]]['cases'],
        'binary_evals': per_judge[judges[0]]['binary_evals'],
        'score_evals': score_qids,
        'reps': next(iter(reps.values())),
        'gold_distribution': per_judge[judges[0]]['gold_distribution'],
        'per_judge': per_judge,
        'baseline': baseline,
    }


def gold_line(data: dict) -> str:
    """One-line gold distribution over cases, e.g. `grounded: 11 true / 1 false`."""
    parts = []
    for qid, dist in data['gold_distribution'].items():
        label = 'level ' if qid in data['score_evals'] else ''
        parts.append(f'**{qid}**: ' + ' / '.join(f'{n} {label}{value}' for value, n in dist.items()))
    return f'Gold distribution over the {len(data["cases"])} cases — ' + '; '.join(parts) + '.'


def write_tables(path: Path, data: dict, compare: dict | None) -> str:
    judges, cases = data['judges'], data['cases']
    binary_qids, score_qids = data['binary_evals'], data['score_evals']
    per_judge = data['per_judge']
    rows_of = {**per_judge, BASELINE_JUDGE: data['baseline']}
    md = [f'# Docs-agent judge benchmark — `{path.name}`\n']
    md.append(
        f'{len(cases)} frozen cases x {data["reps"]} repetitions (every cell has the same repetition count), '
        f'{len(judges)} judges, evals: {", ".join([*binary_qids, *score_qids])}.\n'
    )

    def cell_pct(acc: dict) -> str:
        return f'{pct(acc["value"])} ({acc["correct"]}/{acc["total"]})'

    emit(
        md,
        'Table A — Binary accuracy vs the labels',
        ['Judge', *binary_qids, 'pooled', 'failed calls (all evals)'],
        [
            [
                judge,
                *[cell_pct(rows_of[judge]['accuracy'][q]) for q in binary_qids],
                cell_pct(rows_of[judge]['accuracy']['binary_pooled']),
                str(rows_of[judge]['failures']['total']),
            ]
            for judge in [*judges, BASELINE_JUDGE]
        ],
        note='Correct decisions over all (case x repetition) decisions. A failed call counts as incorrect. '
        '`baseline(majority)` always answers the most common gold value of the eval.\n\n' + gold_line(data),
    )

    emit(
        md,
        'Table A1 — Modal-verdict accuracy (cases whose most common answer matches the label)',
        ['Judge', *binary_qids, *score_qids],
        [
            [
                judge,
                *[
                    f'{rows_of[judge]["modal_accuracy"][q]["correct"]}/{rows_of[judge]["modal_accuracy"][q]["total"]}'
                    for q in [*binary_qids, *score_qids]
                ],
            ]
            for judge in [*judges, BASELINE_JUDGE]
        ],
        note='One vote per case: the modal answer over repetitions, scored against the label. This is what a single '
        'production draw most likely returns; Table A charges every unstable repetition against accuracy, which '
        'flatters a judge that is stable and wrong.',
    )

    emit(
        md,
        'Table A2 — Failed calls per eval',
        ['Judge', *binary_qids, *score_qids, 'total'],
        [
            [
                judge,
                *[str(per_judge[judge]['failures']['per_eval'][q]) for q in [*binary_qids, *score_qids]],
                str(per_judge[judge]['failures']['total']),
            ]
            for judge in judges
        ],
        note='A failed call returned no prediction (retries exhausted, or the reasoning overflowed `max_tokens`).',
    )

    for qid in score_qids:
        emit(
            md,
            f'Table B — {qid} variance across repetitions',
            ['Judge', 'mean per-case variance', 'x Jev', 'worst case', 'worst-case variance', 'failed calls'],
            [
                [
                    judge,
                    f'{per_judge[judge]["quality_variance"][qid]["mean"]:.5f}',
                    'n/a (Jev variance 0)'
                    if per_judge[judge]['quality_variance'][qid]['x_jev'] is None
                    else f'{per_judge[judge]["quality_variance"][qid]["x_jev"]:.1f}x',
                    '-'
                    if max(per_judge[judge]['quality_variance'][qid]['per_case'].values()) == 0
                    else max(
                        per_judge[judge]['quality_variance'][qid]['per_case'],
                        key=lambda c, j=judge: per_judge[j]['quality_variance'][qid]['per_case'][c],
                    ),
                    f'{max(per_judge[judge]["quality_variance"][qid]["per_case"].values()):.5f}',
                    f'{pct(per_judge[judge]["quality_variance"][qid]["failure_rate"])}',
                ]
                for judge in judges
            ],
            note=f'`{qid}` normalised to 0-1 (pred/{SCORE_MAX:.0f}), population variance per case, averaged over '
            'cases. Failed calls are excluded from the values and reported in the last column. A judge with zero '
            'variance has no worst case, so the column reads `-`.',
        )
        emit(
            md,
            f'Table B2 — per-case {qid} variance',
            ['Case', *judges],
            [
                [
                    case,
                    *[
                        f'{per_judge[j]["quality_variance"][qid]["per_case"].get(case, float("nan")):.5f}'
                        for j in judges
                    ],
                ]
                for case in cases
            ],
        )

    emit(
        md,
        'Table C — Cost per call and per decision, latency per call',
        [
            'Judge',
            'physical calls',
            'decisions',
            'USD/call',
            'USD/decision',
            's/call',
            's/call p50',
            's/call p95',
            'total USD',
        ],
        [
            [
                judge,
                str(per_judge[judge]['cost']['calls']),
                str(per_judge[judge]['cost']['decisions']),
                f'{per_judge[judge]["cost"]["cost_per_call_usd"]:.5f}',
                f'{per_judge[judge]["cost"]["cost_per_decision_usd"]:.5f}',
                f'{per_judge[judge]["cost"]["latency_per_call_s"]:.2f}',
                f'{per_judge[judge]["cost"]["latency_p50_s"]:.2f}',
                f'{per_judge[judge]["cost"]["latency_p95_s"]:.2f}',
                f'{per_judge[judge]["cost"]["total_cost_usd"]:.4f}',
            ]
            for judge in judges
        ],
        note='A decision is one (case, eval, repetition). The LLM judges make one call per decision; Jev answers '
        'all evals of a case in one classify call, so its calls are a third of its decisions. Latency is measured '
        'per request, so mean, p50 and p95 are over physical calls — but runs recorded before 2026-09-20 stored '
        'the per-cell mean on every repetition row, and their percentiles are percentiles of those means. Latency '
        'was measured with the three LLM judges at 6 in-flight calls each and Jev on an 8-thread pool, all from '
        'one laptop.',
    )

    emit(
        md,
        'Table D — Signal value (label agreement x repeatability)',
        ['Judge', 'Eval', 'label agreement', 'repeatability', 'signal value'],
        [
            [
                judge,
                qid,
                pct(rows_of[judge]['accuracy'][qid]['value']),
                pct(rows_of[judge]['repeatability'][qid]),
                f'{rows_of[judge]["signal"][qid]:.3f}',
            ]
            for judge in [*judges, BASELINE_JUDGE]
            for qid in [*binary_qids, 'binary_pooled', *score_qids]
        ],
        note='Repeatability = share of repetitions matching the modal answer, averaged over cases; a failed call '
        'is a non-modal vote. Score evals are treated as exact-match categorical. `baseline(majority)` is constant, '
        'so its repeatability is 100% by construction.',
    )

    unstable_rows = [
        [
            judge,
            qid,
            str(len(per_judge[judge]['unstable'][qid])),
            ', '.join(
                f'{case} {{{", ".join(f"{k}:{v}" for k, v in votes.items())}}}'
                for case, votes in per_judge[judge]['unstable'][qid].items()
            )
            or '-',
        ]
        for judge in judges
        for qid in [*binary_qids, *score_qids]
    ]
    emit(
        md,
        'Table E — Unstable cases (modal answer below 100% of reps)',
        ['Judge', 'Eval', 'unstable cases', 'vote distribution'],
        unstable_rows,
        note=f'Vote counts sum to the {data["reps"]} repetitions; `failed:N` is a call that returned no prediction.',
    )

    emit(
        md,
        'Table F — Per-case verdicts (modal answer and agreement)',
        ['Case', 'Eval', 'gold', *judges],
        [
            [
                case,
                qid,
                str(per_judge[judges[0]]['modal'][f'{qid}|{case}']['gold']),
                *[
                    f'{per_judge[j]["modal"][f"{qid}|{case}"]["modal"]} '
                    f'({pct(per_judge[j]["modal"][f"{qid}|{case}"]["agreement"])}, '
                    f'{", ".join(f"{k}:{v}" for k, v in per_judge[j]["modal"][f"{qid}|{case}"]["votes"].items())})'
                    for j in judges
                ],
            ]
            for case in cases
            for qid in [*binary_qids, *score_qids]
            if f'{qid}|{case}' in per_judge[judges[0]]['modal']
        ],
        note=f'`modal (agreement, votes)`; vote counts sum to the {data["reps"]} repetitions.',
    )

    if compare:
        a, b = Path(data['dir']).name, Path(compare['dir']).name
        shared = [j for j in judges if j in compare['per_judge']]
        emit(
            md,
            f'Table G — `{b}` vs `{a}`',
            ['Judge', 'Eval', f'accuracy {b}', f'accuracy {a}', f'repeatability {b}', f'repeatability {a}'],
            [
                [
                    judge,
                    qid,
                    pct(compare['per_judge'][judge]['accuracy'][qid]['value']),
                    pct(per_judge[judge]['accuracy'][qid]['value']),
                    pct(compare['per_judge'][judge]['repeatability'][qid]),
                    pct(per_judge[judge]['repeatability'][qid]),
                ]
                for judge in shared
                for qid in [*binary_qids, 'binary_pooled', *score_qids]
            ],
        )
    return '\n'.join(md) + '\n'


def main(
    directory: Annotated[Path, typer.Option('--dir', help='Run dir holding *__rep*.jsonl files')] = DEFAULT_DIR,
    compare: Annotated[Path | None, typer.Option('--compare', help='Second run dir for a before/after table')] = None,
    *,
    summary: Annotated[bool, typer.Option(help='Also rewrite repeat_summary.json from the same functions')] = True,
) -> None:
    data = analyse(directory)
    other = analyse(compare) if compare else None
    markdown = write_tables(directory, data, other)
    (directory / 'blog_tables.md').write_text(markdown)
    payload = {'run': data} | ({'compare': other} if other else {})
    (directory / 'blog_metrics.json').write_text(json.dumps(payload, indent=2))
    written = [directory / 'blog_tables.md', directory / 'blog_metrics.json']
    if summary:
        summaries = [data['per_judge'][j] for j in data['judges']]
        (directory / 'repeat_summary.json').write_text(json.dumps(summaries, indent=2))
        written.append(directory / 'repeat_summary.json')
    logger.info('✓ wrote ' + ', '.join(str(p) for p in written))


if __name__ == '__main__':
    typer.run(main)
