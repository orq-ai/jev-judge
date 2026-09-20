"""The Pareto-front helper behind `scripts/docs_agent_pareto.py` — pure geometry, no plotting."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from docs_agent_pareto import pareto_front


def test_a_point_that_is_slower_and_worse_drops_off_the_front():
    """Cheap-and-good and expensive-but-best survive; the middle point is beaten on both axes."""
    fast_ok, slow_bad, slow_best = (0.5, 0.80), (3.0, 0.70), (4.0, 0.95)

    assert pareto_front([fast_ok, slow_bad, slow_best]) == [0, 2]
