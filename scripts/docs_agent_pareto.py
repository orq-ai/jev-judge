"""Pareto charts for the docs-agent judge study: quality against speed, quality against cost.

Reads the same `<judge>__rep<NN>.jsonl` files as `scripts/docs_agent_analysis.py`, asks
`jev_judge.repeat.summarise` for the numbers, and draws two scatter plots with the
non-dominated set (higher quality, lower x) filled and joined by a teal staircase. `--dir` can be
repeated, each optionally labelled with a `:suffix` so two runs can share the same axes.

    uv run python scripts/docs_agent_pareto.py --dir results/docs_rag
    uv run python scripts/docs_agent_pareto.py \
        --dir results/docs_rag --dir results/docs_rag_matched:matched
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import matplotlib as mpl

mpl.use('Agg')  # never pop a window; this runs headless next to the experiment
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import typer
from loguru import logger
from matplotlib.lines import Line2D

from jev_judge.repeat import BASELINE_JUDGE, cells_of, majority_baseline, summarise

if TYPE_CHECKING:
    from collections.abc import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling script, not a package
from docs_agent_analysis import load_judges, order_judges

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / 'results' / 'docs_rag'

TEAL = '#025558'  # Orq deep teal — Jev and the Pareto staircase
ORANGES = ('#ff8f34', '#df5325', '#f2b600')  # Pulse orange and friends — the LLM judges
GREY = '#9a9a9a'  # dominated points and the baseline line
METRICS = {
    'signal': ('signal', 'Signal value (accuracy x repeatability, all evals)'),
    'accuracy': ('accuracy', 'Accuracy over all evals (a failed call counts wrong)'),
    'modal': ('modal', 'Modal-verdict accuracy (all evals)'),
}


def pareto_front(points: list[tuple[float, float]]) -> list[int]:
    """Indices of the non-dominated points of `(x, y)`, cheapest x first.

    `a` dominates `b` when it is at least as good on both axes (lower x, higher y) and strictly better
    on one. Points that tie on both axes all stay on the front.
    """
    keep = [
        i for i, (x, y) in enumerate(points) if not any(ox <= x and oy >= y and (ox, oy) != (x, y) for ox, oy in points)
    ]
    return sorted(keep, key=lambda i: points[i][0])


def quality(summary: dict, metric: str) -> float:
    """The selected y-metric of a judge, pooled over every eval."""
    if metric == 'signal':
        return summary['signal']['all']
    return summary[{'accuracy': 'accuracy', 'modal': 'modal_accuracy'}[metric]]['all']['value']


def seconds_per_call(summary: dict) -> float:
    """p50 latency of a physical call, falling back to the mean for runs that stored no percentiles."""
    return summary['cost'].get('latency_p50_s') or summary['cost']['latency_per_call_s']


def collect(specs: list[str]) -> tuple[dict[str, dict], dict]:
    """Per-judge summaries over every `--dir` (suffixed by its label), plus the majority baseline."""
    summaries: dict[str, dict] = {}
    baseline = None
    for spec in specs:
        raw, _, label = spec.rpartition(':') if ':' in spec else (spec, '', '')
        path = Path(raw or spec)
        by_rows = load_judges(path)
        for judge in order_judges(list(by_rows)):
            name = f'{judge} ({label})' if label else judge
            summaries[name] = summarise(judge, by_rows[judge])
        if baseline is None:
            cells = majority_baseline(cells_of(next(iter(by_rows.values()))))
            baseline = summarise(BASELINE_JUDGE, [r for cell in cells.values() for r in cell])
    if not summaries:
        raise typer.BadParameter('no --dir produced any judge rows')
    return summaries, baseline


def styles(names: list[str]) -> dict[str, tuple[str, str]]:
    """(colour, marker) per judge: Jev teal, LLM judges orange shades, labelled variants as triangles.

    The shade follows the base judge name, so `gpt-5.6-luna` and `gpt-5.6-luna (matched)` share a colour
    and differ only in marker.
    """
    bases = sorted({n.split(' (')[0] for n in names if not n.startswith('jev')})
    return {
        n: (
            TEAL if n.startswith('jev') else ORANGES[bases.index(n.split(' (')[0]) % len(ORANGES)],
            '^' if ' (' in n else 'o',
        )
        for n in names
    }


def chart(
    names: list[str],
    points: list[tuple[float, float]],
    front: list[int],
    baseline_y: float,
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    footnote: str,
    tick: Callable[[float], str],
    out: Path,
) -> None:
    """One Pareto scatter: filled markers on the front joined by a teal staircase, hollow grey behind."""
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.set_xscale('log')

    front_points = [points[i] for i in front]
    if len(front_points) > 1:
        ax.plot(
            [p[0] for p in front_points],
            [p[1] for p in front_points],
            drawstyle='steps-post',
            color=TEAL,
            linewidth=1.8,
            alpha=0.7,
            zorder=2,
        )
    ax.axhline(baseline_y, color=GREY, linestyle='--', linewidth=1.4, zorder=1)
    ax.annotate(
        f'always-majority baseline ({baseline_y:.3f})',
        xy=(0.012, baseline_y),
        xycoords=('axes fraction', 'data'),
        xytext=(0, 6),
        textcoords='offset points',
        ha='left',
        fontsize=10,
        color=GREY,
    )

    marks = styles(names)
    for i, (name, (x, y)) in enumerate(zip(names, points, strict=True)):
        colour, marker = marks[name]
        on_front = i in front
        ax.scatter(
            x,
            y,
            s=170,
            marker=marker,
            facecolor=colour if on_front else 'none',
            edgecolor=colour if on_front else GREY,
            linewidths=1.8,
            zorder=3,
        )
        ax.annotate(
            name,
            xy=(x, y),
            xytext=(0, 14 if on_front else -20),
            textcoords='offset points',
            ha='center',
            fontsize=11,
            fontweight='bold' if on_front else 'normal',
            color=colour if on_front else '#55555f',
        )

    ax.set_xlabel(xlabel, fontsize=13, fontweight='bold', color='black')
    ax.set_ylabel(ylabel, fontsize=13, fontweight='bold', color='black')
    ax.set_title(title, fontsize=14, fontweight='bold', color='black', pad=14)
    ax.tick_params(axis='both', colors='black', labelsize=11)
    ax.xaxis.set_major_locator(mticker.LogLocator(base=10, subs=(1.0, 2.0, 5.0), numticks=20))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: tick(v)))
    ax.grid(visible=True, which='major', linestyle='--', alpha=0.25, color=TEAL)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.margins(x=0.22, y=0.24)
    ax.legend(
        handles=[
            Line2D([], [], marker='o', color=TEAL, linestyle='', markersize=11, label='on the Pareto front'),
            Line2D(
                [],
                [],
                marker='o',
                color=GREY,
                linestyle='',
                markersize=11,
                markerfacecolor='none',
                label='dominated',
            ),
        ],
        loc='upper right',
        fontsize=10,
        frameon=False,
    )
    if footnote:
        # parse_math=False keeps the dollar signs literal instead of opening mathtext
        fig.text(0.02, 0.005, footnote, fontsize=9.5, color='#55555f', ha='left', va='bottom', parse_math=False)
    fig.tight_layout(rect=(0, 0.05 if footnote else 0, 1, 1))
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def cost_footnote(summaries: dict[str, dict]) -> str:
    """Per-call price of Jev next to the cheapest LLM judge — the reason the two cost axes differ."""
    per_call = {name: s['cost']['cost_per_call_usd'] for name, s in summaries.items()}
    jev = next((n for n in per_call if n.startswith('jev')), None)
    others = {n: c for n, c in per_call.items() if n != jev}
    cheapest = min(others, key=lambda n: others[n]) if others else None
    prices = [f'{n} ${per_call[n]:.5f}' for n in (jev, cheapest) if n]
    return (
        'Jev answers the three evals of a case in one call; LLM judges make one call per eval. '
        'Per-call cost: ' + ', '.join(prices) + '.'
    )


def table(summaries: dict[str, dict], baseline: dict, metric: str, speed: list[int], cost: list[int]) -> str:
    """Markdown table behind the two charts; the last two columns say which front a judge sits on."""
    names = list(summaries)
    header = [
        'judge',
        'signal',
        'modal acc',
        's/call p50',
        'USD/call',
        'USD/decision',
        'on front (speed)',
        'on front (cost)',
    ]
    rows = [
        [
            name,
            f'{s["signal"]["all"]:.3f}',
            f'{s["modal_accuracy"]["all"]["value"]:.3f}',
            f'{seconds_per_call(s):.2f}',
            f'{s["cost"]["cost_per_call_usd"]:.5f}',
            f'{s["cost"]["cost_per_decision_usd"]:.5f}',
            'yes' if i in speed else 'no',
            'yes' if i in cost else 'no',
        ]
        for i, (name, s) in enumerate(summaries.items())
    ]
    rows.append([
        BASELINE_JUDGE,
        f'{baseline["signal"]["all"]:.3f}',
        f'{baseline["modal_accuracy"]["all"]["value"]:.3f}',
        '0.00',
        '0.00000',
        '0.00000',
        'reference line',
        'reference line',
    ])
    md = [
        f'# Docs-agent judge Pareto — y = {METRICS[metric][1]}\n',
        (
            f'{len(names)} judges over {summaries[names[0]]["reps"]} repetitions x '
            f'{len(summaries[names[0]]["cases"])} cases. A judge is on a front when no other judge is at least as '
            'good on quality and at least as cheap (or fast). The majority baseline costs nothing and takes no '
            'time, so it is a reference line rather than a point.\n'
        ),
        cost_footnote(summaries) + '\n',
        '| ' + ' | '.join(header) + ' |',
        '|' + '|'.join(['---'] * len(header)) + '|',
        *['| ' + ' | '.join(r) + ' |' for r in rows],
    ]
    return '\n'.join(md) + '\n'


def main(
    directory: Annotated[
        list[str] | None,
        typer.Option('--dir', help='Run dir with *__rep*.jsonl, optionally `path:label` to suffix its judges'),
    ] = None,
    out: Annotated[Path | None, typer.Option('--out', help='Where the PNGs go; default the first --dir')] = None,
    metric: Annotated[str, typer.Option('--metric', help='y-axis: signal | accuracy | modal')] = 'signal',
) -> None:
    """Write `pareto_quality_vs_speed.png`, `pareto_quality_vs_cost.png` and `pareto.md`."""
    if metric not in METRICS:
        raise typer.BadParameter(f'--metric must be one of {", ".join(METRICS)}')
    specs = directory or [str(DEFAULT_DIR)]
    summaries, baseline = collect(specs)
    out = out or Path(specs[0].rpartition(':')[0] if ':' in specs[0] else specs[0])
    out.mkdir(parents=True, exist_ok=True)

    names = list(summaries)
    ys = [quality(s, metric) for s in summaries.values()]
    speed_points = [(seconds_per_call(s), y) for s, y in zip(summaries.values(), ys, strict=True)]
    cost_points = [(s['cost']['cost_per_decision_usd'], y) for s, y in zip(summaries.values(), ys, strict=True)]
    speed_front, cost_front = pareto_front(speed_points), pareto_front(cost_points)
    baseline_y = quality(baseline, metric)
    ylabel = METRICS[metric][1]

    chart(
        names,
        speed_points,
        speed_front,
        baseline_y,
        xlabel='Seconds per call (p50, log scale)',
        ylabel=ylabel,
        title='Docs-agent judges: quality vs speed',
        footnote='Latency was measured from one laptop with the LLM judges at 6 in-flight calls each.',
        tick=lambda v: f'{v:g}s',
        out=out / 'pareto_quality_vs_speed.png',
    )
    chart(
        names,
        cost_points,
        cost_front,
        baseline_y,
        xlabel='USD per decision (log scale)',
        ylabel=ylabel,
        title='Docs-agent judges: quality vs cost',
        footnote=cost_footnote(summaries),
        tick=lambda v: f'${v:.4f}'.rstrip('0'),
        out=out / 'pareto_quality_vs_cost.png',
    )
    (out / 'pareto.md').write_text(table(summaries, baseline, metric, speed_front, cost_front))

    logger.info('✓ speed front: ' + ', '.join(names[i] for i in speed_front))
    logger.info('✓ cost front: ' + ', '.join(names[i] for i in cost_front))
    logger.info(f'✓ wrote {out}/pareto_quality_vs_speed.png, {out}/pareto_quality_vs_cost.png, {out}/pareto.md')


if __name__ == '__main__':
    typer.run(main)
