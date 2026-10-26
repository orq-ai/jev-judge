"""Shared chart styling for the Pareto charts: Orq palette, judge display names, axis treatment."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl

from jev_judge.repeat import BASELINE_JUDGE

if TYPE_CHECKING:
    import matplotlib.pyplot as plt

ORQ_TEAL = '#025558'
ORQ_ORANGE = '#ff8f34'
ORQ_INK = '#25232e'
ORQ_GREY = '#77747e'

DISPLAY = {
    'jev': 'Jev',
    'gpt-5.6-luna': 'Luna',
    'gemini-3.8-flash': 'Gemini Flash',
    'deepseek-v4.1-flash': 'DeepSeek Flash',
    'claude-opus-5': 'Claude Opus',
    'gpt-5.6-sol': 'GPT Sol',
    BASELINE_JUDGE: 'Always-majority',
}

DPI = 200


def setup_style() -> None:
    """Shared typography and white-background Orq chart styling."""
    mpl.rcParams.update(
        {
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.edgecolor': ORQ_INK,
            'axes.labelcolor': ORQ_INK,
            'axes.titlecolor': ORQ_INK,
            'font.size': 9,
            'text.color': ORQ_INK,
            'xtick.color': ORQ_INK,
            'ytick.color': ORQ_INK,
            'legend.frameon': False,
            'savefig.facecolor': 'white',
        }
    )


def style_axis(ax: plt.Axes, *, grid: str = 'y') -> None:
    """Apply the shared axis treatment without changing scales or limits."""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if grid:
        ax.grid(axis=grid, linestyle='--', linewidth=0.7, alpha=0.25, color=ORQ_TEAL)
        ax.set_axisbelow(True)
    ax.tick_params(labelsize=8)
