"""Pareto charts for the docs-agent judge study: quality against speed, quality against cost.

Reads the same `<judge>.jsonl` files as `scripts/docs_agent_analysis.py`, asks
`jev_judge.repeat.summarise` for the numbers, and draws two scatter plots with the
non-dominated set (higher quality, lower x) filled and joined by a teal staircase. `--dir` can be
repeated, each optionally labelled with a `:suffix` so two runs can share the same axes.

    uv run python scripts/docs_agent_pareto.py --dir results/docs_rag
    uv run python scripts/docs_agent_pareto.py \
        --dir results/docs_rag --dir results/docs_rag_matched:matched
"""

from __future__ import annotations

import math
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
from jev_judge.chart_style import DISPLAY, DPI, ORQ_GREY, ORQ_INK, ORQ_ORANGE, ORQ_TEAL, setup_style, style_axis

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / 'results' / 'docs_rag'

# own palette: the blog's line-chart colours (bright cyan, pale gold) do not read as filled markers on white.
# One saturated hue per judge; arm variants share the hue and change the marker.
COLOURS = {
    'jev': ORQ_TEAL,
    'gemini-3.8-flash': '#1f9e89',
    'gpt-5.6-luna': ORQ_ORANGE,
    'deepseek-v4.1-flash': '#1e6fb8',
    'claude-opus-5': '#c8371f',
    'gpt-5.6-sol': '#e0a800',
    'laya-en': '#9b7fc4',
    'laya-td': '#5a3d8a',
    'semif': '#6e6e6e',
    'kev-0.8b': '#d4a017',
    'kev-4b': '#9a6b12',
    'kev-9b': '#5f3f0a',
    'jpt-4b': '#3175a8',
    'decider-4b': '#b25d22',
    'djev': '#d6338c',
    'clm': '#5b8c00',
}
DISPLAY = {
    **DISPLAY,
    'laya-en': 'Laya EN',
    'laya-td': 'Laya TD',
    'semif': 'SemIf',
    'kev-0.8b': 'Kev 0.8B',
    'kev-4b': 'Kev 4B',
    'kev-9b': 'Kev 9B',
    'jpt-4b': 'JPT 4B',
    'decider-4b': 'Decider 4B',
    'djev': 'djev 26B-A4B',
    'clm': 'CLM 8B',
}
FIGSIZE = (9.5, 6)
# label offsets in points, nearest first; a label takes the first slot that overlaps nothing already drawn
LABEL_SLOTS = [
    (10, 7),
    (10, -13),
    (-10, 7),
    (-10, -13),
    (0, 13),
    (0, -16),
    (14, 20),
    (-14, 20),
    (14, -26),
    (-14, -26),
    (0, 28),
    (0, -32),
    (30, 12),
    (-30, 12),
    (30, -16),
    (-30, -16),
    (0, 44),
    (0, -48),
    (44, 30),
    (-44, 30),
    (44, -34),
    (-44, -34),
    (0, 62),
    (0, -66),
    (60, 48),
    (-60, 48),
    (60, -52),
    (-60, -52),
]

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
            if label and judge == 'jev':  # Jev has no settings to vary; its rerun in each arm is the same judge
                continue
            name = f'{judge} ({label})' if label else judge
            if name in summaries:
                raise typer.BadParameter(f'{name} appears in more than one --dir; give each a distinct `:label`')
            summaries[name] = summarise(judge, by_rows[judge])
        if baseline is None:
            cells = majority_baseline(cells_of(next(iter(by_rows.values()))))
            baseline = summarise(BASELINE_JUDGE, [r for cell in cells.values() for r in cell])
    if not summaries:
        raise typer.BadParameter('no --dir produced any judge rows')
    return summaries, baseline


def styles(names: list[str]) -> dict[str, tuple[str, str]]:
    """(colour, marker) per judge: the blog palette by base judge name; arm variants change marker only."""
    return {
        n: (
            COLOURS[n.split(' (')[0]],
            's' if '(local' in n else '^' if ' (' in n else 'o',
        )
        for n in names
    }


def label(name: str) -> str:
    base, _, arm = name.partition(' (')
    return DISPLAY.get(base, base) + (f' ({arm}' if arm else '')


def place_labels(fig: plt.Figure, ax: plt.Axes, items: list[tuple[str, float, float, bool]]) -> None:
    """Greedy no-overlap labels: front points first, each label in the nearest free slot, a leader line when far."""
    from matplotlib.transforms import Bbox

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    axes_box = ax.get_window_extent(renderer)
    taken = [
        Bbox.from_extents(px - 9, py - 9, px + 9, py + 9)
        for px, py in (ax.transData.transform((x, y)) for _, x, y, _ in items)
    ]
    if ax.get_legend() is not None:
        taken.append(ax.get_legend().get_window_extent(renderer))
    order = sorted(range(len(items)), key=lambda i: (not items[i][3], -items[i][2]))
    for i in order:
        text, x, y, bold = items[i]
        ann = None
        for dx, dy in LABEL_SLOTS:
            if ann is not None:
                ann.remove()
            far = (dx * dx + dy * dy) ** 0.5 > 24
            ann = ax.annotate(
                text,
                xy=(x, y),
                xytext=(dx, dy),
                textcoords='offset points',
                ha='left' if dx > 0 else 'right' if dx < 0 else 'center',
                va='center' if dy == 0 else 'bottom' if dy > 0 else 'top',
                fontsize=7.5,
                fontweight='bold' if bold else 'normal',
                color=ORQ_INK,
                zorder=4,
                arrowprops={'arrowstyle': '-', 'color': ORQ_GREY, 'linewidth': 0.6, 'shrinkB': 4} if far else None,
            )
            box = ann.get_window_extent(renderer).expanded(1.08, 1.25)
            inside = axes_box.x0 <= box.x0 and box.x1 <= axes_box.x1 and axes_box.y0 <= box.y0 and box.y1 <= axes_box.y1
            if inside and not any(box.overlaps(t) for t in taken):
                break
        taken.append(ann.get_window_extent(renderer).expanded(1.08, 1.25))


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
    """One Pareto scatter: every judge a filled marker in its own colour, front points ringed and joined by a staircase."""
    setup_style()
    fig, ax = plt.subplots(figsize=FIGSIZE, constrained_layout=True)
    ax.set_xscale('log')

    front_points = [points[i] for i in front]
    if len(front_points) > 1:
        ax.plot(
            [p[0] for p in front_points],
            [p[1] for p in front_points],
            drawstyle='steps-post',
            color=ORQ_TEAL,
            linewidth=1.4,
            alpha=0.5,
            zorder=2,
        )
    ax.axhline(baseline_y, color=ORQ_GREY, linestyle='--', linewidth=1.1, zorder=1)
    ax.annotate(
        f'always-majority baseline ({baseline_y:.3f})',
        xy=(0.99, baseline_y),
        xycoords=('axes fraction', 'data'),
        xytext=(0, -4),
        textcoords='offset points',
        ha='right',
        va='top',
        fontsize=7.5,
        color=ORQ_GREY,
    )

    marks = styles(names)
    for i, (name, (x, y)) in enumerate(zip(names, points, strict=True)):
        colour, marker = marks[name]
        on_front = i in front
        ax.scatter(
            x,
            y,
            s=150 if on_front else 80,
            marker=marker,
            facecolor=colour,
            edgecolor=ORQ_INK if on_front else 'white',
            linewidths=1.8 if on_front else 0.8,
            zorder=3,
        )

    ax.set_xlabel(xlabel, fontweight='bold')
    ax.set_ylabel(ylabel, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
    ax.xaxis.set_major_locator(mticker.LogLocator(base=10, subs=(1.0, 2.0, 5.0), numticks=20))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: tick(v)))
    style_axis(ax, grid='both')
    ax.margins(x=0.2, y=0.28)
    ax.legend(
        handles=[
            Line2D(
                [],
                [],
                marker='o',
                color=ORQ_GREY,
                markeredgecolor=ORQ_INK,
                markeredgewidth=1.8,
                linestyle='',
                markersize=9,
                label='on the Pareto front',
            ),
            Line2D(
                [],
                [],
                marker='o',
                color=ORQ_GREY,
                markeredgecolor='white',
                linestyle='',
                markersize=7,
                label='dominated',
            ),
            *[
                Line2D([], [], marker=m, color=ORQ_GREY, markeredgecolor='white', linestyle='', markersize=7, label=lbl)
                for m, lbl, hit in (
                    ('^', 'matched / sota arm', any(' (' in n and '(local' not in n for n in names)),
                    ('s', 'open local model', any('(local' in n for n in names)),
                )
                if hit
            ],
        ],
        loc='upper center',
        bbox_to_anchor=(0.5, -0.14),
        ncol=4,
        fontsize=7.5,
        handletextpad=0.4,
        columnspacing=1.6,
    )
    if footnote:
        # parse_math=False keeps the dollar signs literal instead of opening mathtext
        fig.text(0.01, 0.005, footnote, fontsize=7, color=ORQ_GREY, ha='left', va='bottom', parse_math=False)
        fig.get_layout_engine().set(rect=(0, 0.04, 1, 0.96))
    place_labels(
        fig, ax, [(label(n), x, y, i in front) for i, (n, (x, y)) in enumerate(zip(names, points, strict=True))]
    )
    fig.savefig(out, dpi=DPI, facecolor='white')
    plt.close(fig)


SPEED_FOOTNOTE = (
    'Latency: LLM judges and Jev from one laptop, 6 in-flight calls per LLM judge; '
    '(local) models served per case on Modal (Kev, JPT, Decider and CLM A100, SemIf and Laya A10G, djev B200); '
    'Decider scores each question separately.'
)
MARKER_SYMBOL = {'o': 'circle', '^': 'triangle-up', 's': 'square'}


def html_chart(
    names: list[str],
    points: list[tuple[float, float]],
    front: list[int],
    baseline_y: float,
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    footnote: str,
    xfmt: str,
    tick: Callable[[float], str],
    out: Path,
) -> None:
    """Interactive twin of `chart`: one legend entry per judge (outside the axes), hover for the numbers."""
    import plotly.graph_objects as go

    marks = styles(names)
    fig = go.Figure()
    front_points = [points[i] for i in front]
    if len(front_points) > 1:
        fig.add_trace(
            go.Scatter(
                x=[p[0] for p in front_points],
                y=[p[1] for p in front_points],
                mode='lines',
                line={'shape': 'hv', 'color': ORQ_TEAL, 'width': 1.5},
                opacity=0.5,
                hoverinfo='skip',
                showlegend=False,
            )
        )
    fig.add_hline(y=baseline_y, line={'color': ORQ_GREY, 'dash': 'dash', 'width': 1.2})
    lo, hi = math.log10(min(x for x, _ in points)) - 0.35, math.log10(max(x for x, _ in points)) + 0.35
    tickvals = [
        m * 10**k
        for k in range(math.floor(lo), math.ceil(hi) + 1)
        for m in (1, 2, 5)
        if lo <= math.log10(m * 10**k) <= hi
    ]
    for i, (name, (x, y)) in enumerate(zip(names, points, strict=True)):
        colour, marker = marks[name]
        on_front = i in front
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode='markers+text' if on_front else 'markers',
                name=label(name) + (' \u2605' if on_front else ''),
                text=[label(name)] if on_front else None,
                textposition='top center',
                textfont={'size': 11, 'color': ORQ_INK, 'family': 'Arial Black, Arial, sans-serif'},
                marker={
                    'symbol': MARKER_SYMBOL[marker],
                    'size': 16 if on_front else 11,
                    'color': colour,
                    'line': {'color': ORQ_INK if on_front else 'white', 'width': 2 if on_front else 1},
                },
                hovertemplate=f'<b>{label(name)}</b><br>signal %{{y:.3f}}<br>{xlabel.split(" (")[0]}: %{{x{xfmt}}}'
                + ('<br>on the Pareto front' if on_front else '')
                + '<extra></extra>',
            )
        )
    fig.update_layout(
        title={'text': title, 'font': {'size': 18, 'color': ORQ_INK}, 'x': 0.5},
        xaxis={
            'title': xlabel,
            'type': 'log',
            'range': [lo, hi],
            'tickvals': tickvals,
            'ticktext': [tick(v) for v in tickvals],
            'gridcolor': 'rgba(2,85,88,0.15)',
        },
        yaxis={
            'title': ylabel,
            'range': [min([baseline_y, *(y for _, y in points)]) - 0.06, max(y for _, y in points) + 0.06],
            'gridcolor': 'rgba(2,85,88,0.15)',
        },
        legend={'orientation': 'v', 'x': 1.02, 'y': 1, 'font': {'size': 11}, 'title': {'text': '\u2605 on the front'}},
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'family': 'Arial, sans-serif', 'color': ORQ_INK},
        margin={'l': 70, 'r': 20, 't': 60, 'b': 95},
        annotations=[
            {
                'text': footnote,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0,
                'y': -0.19,
                'showarrow': False,
                'font': {'size': 10, 'color': ORQ_GREY},
                'xanchor': 'left',
                'yanchor': 'top',
            },
            {
                'text': f'always-majority baseline ({baseline_y:.3f})',
                'xref': 'paper',
                'yref': 'y',
                'x': 1,
                'y': baseline_y,
                'showarrow': False,
                'font': {'size': 11, 'color': ORQ_GREY},
                'xanchor': 'right',
                'yanchor': 'top',
                'yshift': -3,
            },
        ],
        height=560,
    )
    out.write_text(
        fig.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True, 'displaylogo': False})
    )


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
        'USD/decision (list price)',
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
            f'{s["cost"]["list_cost_per_decision_usd"]:.5f}',
            'yes' if i in speed else 'no',
            'yes' if i in cost else 'no',
        ]
        for i, (name, s) in enumerate(summaries.items())
    ]
    rows.append(
        [
            BASELINE_JUDGE,
            f'{baseline["signal"]["all"]:.3f}',
            f'{baseline["modal_accuracy"]["all"]["value"]:.3f}',
            '0.00',
            '0.00000',
            '0.00000',
            'reference line',
            'reference line',
        ]
    )
    reps = sorted({summaries[n]['reps'] for n in names})
    reps_text = f'{reps[0]}' if len(reps) == 1 else f'{reps[0]} to {reps[-1]}'
    md = [
        f'# Docs-agent judge Pareto — y = {METRICS[metric][1]}\n',
        (
            f'{len(names)} judges over {reps_text} repetitions x '
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
        typer.Option('--dir', help='Run dir with <judge>.jsonl, optionally `path:label` to suffix its judges'),
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
    # local models cost nothing per call here (no metered price), so they are on the speed chart only
    priced = [n for n, s in summaries.items() if s['cost']['list_cost_per_decision_usd'] > 0]
    cost_points = [(summaries[n]['cost']['list_cost_per_decision_usd'], quality(summaries[n], metric)) for n in priced]
    speed_front, cost_front = pareto_front(speed_points), pareto_front(cost_points)
    cost_front_summary = [names.index(priced[i]) for i in cost_front]
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
        footnote=SPEED_FOOTNOTE,
        tick=lambda v: f'{v:g}s',
        out=out / 'pareto_quality_vs_speed.png',
    )
    speed_kwargs = {
        'xlabel': 'Seconds per call (p50, log scale)',
        'ylabel': ylabel,
        'title': 'Docs-agent judges: quality vs speed',
        'footnote': SPEED_FOOTNOTE,
    }
    html_chart(
        names,
        speed_points,
        speed_front,
        baseline_y,
        xfmt=':.2f',
        tick=lambda v: f'{v:g}s',
        out=out / 'pareto_quality_vs_speed.html',
        **speed_kwargs,
    )
    html_chart(
        priced,
        cost_points,
        cost_front,
        baseline_y,
        xlabel='USD per decision at list price (log scale)',
        ylabel=ylabel,
        title='Docs-agent judges: quality vs cost',
        footnote=cost_footnote({n: summaries[n] for n in priced}),
        xfmt=':$.5f',
        tick=lambda v: f'${v:.5f}'.rstrip('0'),
        out=out / 'pareto_quality_vs_cost.html',
    )
    chart(
        priced,
        cost_points,
        cost_front,
        baseline_y,
        xlabel='USD per decision at list price (log scale)',
        ylabel=ylabel,
        title='Docs-agent judges: quality vs cost',
        footnote=cost_footnote({n: summaries[n] for n in priced}),
        tick=lambda v: f'${v:.5f}'.rstrip('0'),
        out=out / 'pareto_quality_vs_cost.png',
    )
    (out / 'pareto.md').write_text(table(summaries, baseline, metric, speed_front, cost_front_summary))

    logger.info('✓ speed front: ' + ', '.join(names[i] for i in speed_front))
    logger.info('✓ cost front: ' + ', '.join(names[i] for i in cost_front_summary))
    logger.info(f'✓ wrote {out}/pareto_quality_vs_{{speed,cost}}.{{png,html}}, {out}/pareto.md')


if __name__ == '__main__':
    typer.run(main)
