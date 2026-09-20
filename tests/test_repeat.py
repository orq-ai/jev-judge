"""Repeatability metrics on a hand-computed 2-case x 3-rep fixture — no network, no models."""

from __future__ import annotations

import pytest

from jev_judge.repeat import (
    FAILED,
    cells_of,
    economics,
    majority_baseline,
    rep_count,
    summarise,
    vote_distribution,
)

CALL_COST = 0.009  # one Jev classify call answering three questions
ROW_COST = CALL_COST / 3  # what the experiment records per decision
LATENCY_MS = 300.0

# case -> eval -> (gold, the three repetitions). c1/abstain_ok has one failed call; quality never moves.
FIXTURE = {
    'c1': {
        'grounded': ('true', ['true', 'true', 'true']),
        'abstain_ok': ('true', ['true', 'true', None]),
        'quality': ('4', ['4', '4', '4']),
    },
    'c2': {
        'grounded': ('true', ['true', 'false', 'true']),
        'abstain_ok': ('true', ['true', 'true', 'true']),
        'quality': ('4', ['4', '4', '4']),
    },
}


def rows_of(fixture: dict[str, dict[str, tuple[str, list[str | None]]]] = FIXTURE) -> list[dict]:
    return [
        {
            'id': case,
            'qid': qid,
            'type': 'score' if qid == 'quality' else 'noul',
            'gold': gold,
            'pred': pred,
            'rep': rep,
            'cost': ROW_COST,
            'latency_ms': LATENCY_MS,
        }
        for case, evals in fixture.items()
        for qid, (gold, preds) in evals.items()
        for rep, pred in enumerate(preds)
    ]


def approx(value: float) -> object:
    return pytest.approx(value, abs=1e-9)


def test_failed_prediction_is_wrong_for_accuracy_and_non_modal_for_repeatability():
    s = summarise('jev', rows_of())
    assert s['accuracy']['abstain_ok'] == {'correct': 5, 'total': 6, 'failed': 1, 'value': approx(5 / 6)}
    # c1 votes true/true/failed -> 2 of 3 reps agree with the modal answer; c2 is unanimous
    assert s['repeatability']['abstain_ok'] == approx((2 / 3 + 1.0) / 2)
    assert s['failures'] == {'total': 1, 'per_eval': {'abstain_ok': 1, 'grounded': 0, 'quality': 0}}


def test_vote_distribution_sums_to_the_rep_count_and_names_the_failure():
    cells = cells_of(rows_of())
    votes = vote_distribution(cells['abstain_ok', 'c1'])
    assert votes == {'true': 2, FAILED: 1}
    assert sum(votes.values()) == rep_count(cells)


def test_failed_prediction_is_excluded_from_the_variance_values_but_reported_next_to_them():
    failing = {
        'c1': {**FIXTURE['c1'], 'quality': ('4', ['4', '4', None])},
        'c2': FIXTURE['c2'],
    }
    s = summarise('jev', rows_of(failing))
    assert s['quality_variance']['quality']['mean'] == approx(0.0)  # the two answered reps still agree
    assert s['quality_variance']['quality']['failure_rate'] == approx(1 / 6)


def test_zero_variance_judge_has_no_worst_case():
    s = summarise('jev', rows_of())
    per_case = s['quality_variance']['quality']['per_case']
    assert per_case == {'c1': approx(0.0), 'c2': approx(0.0)}
    assert max(per_case.values()) == 0  # the condition Table B prints `-` for


def test_three_questions_per_call_judge_splits_cost_and_latency_per_call_and_per_decision():
    cells = cells_of(rows_of())
    jev = economics(cells, 'jev')
    assert (jev['calls'], jev['decisions'], jev['decisions_per_call']) == (6, 18, approx(3.0))
    assert jev['total_cost_usd'] == approx(18 * ROW_COST)
    assert jev['cost_per_call_usd'] == approx(CALL_COST)
    assert jev['cost_per_decision_usd'] == approx(ROW_COST)
    assert jev['latency_per_call_s'] == approx(LATENCY_MS / 1000)
    assert jev['latency_per_decision_s'] == approx(6 * LATENCY_MS / 1000 / 18)


def test_latency_percentiles_run_over_physical_calls_not_decisions():
    # per-call latencies, one per (case, rep) Jev call: 100, 200, ..., 600 ms, repeated on that call's three rows
    rows = rows_of()
    per_call = {
        (case, rep): 100.0 * (i + 1)
        for i, (case, rep) in enumerate([('c1', r) for r in range(3)] + [('c2', r) for r in range(3)])
    }
    rows = [{**r, 'latency_ms': per_call[r['id'], r['rep']]} for r in rows]
    jev = economics(cells_of(rows), 'jev')
    assert jev['calls'] == 6
    assert jev['latency_per_call_s'] == approx(0.35)
    assert jev['latency_p50_s'] == approx(0.35)
    assert jev['latency_p95_s'] == approx(0.575)  # numpy linear interpolation between 500 and 600 ms


def test_one_call_per_decision_judge_counts_every_row_as_a_call():
    llm = economics(cells_of(rows_of()), 'gemini-3.8-flash')
    assert (llm['calls'], llm['decisions']) == (18, 18)
    assert llm['cost_per_call_usd'] == approx(llm['cost_per_decision_usd'])


def test_recorded_call_id_overrides_the_per_judge_convention():
    rows = [{**r, 'call_id': f'{r["id"]}:{r["rep"]}'} for r in rows_of()]
    assert economics(cells_of(rows), 'gemini-3.8-flash')['calls'] == 6


def test_majority_baseline_answers_the_most_common_gold_and_never_wavers():
    # a third case breaks the ties a two-case gold column would leave: grounded is 2 true / 1 false
    three = {**FIXTURE, 'c3': {**FIXTURE['c2'], 'grounded': ('false', ['false', 'false', 'false'])}}
    baseline = majority_baseline(cells_of(rows_of(three)))
    s = summarise('baseline(majority)', [r for cell in baseline.values() for r in cell])
    assert {r['pred'] for cell in baseline.values() for r in cell if r['qid'] == 'grounded'} == {'true'}
    assert s['accuracy']['grounded']['value'] == approx(2 / 3)  # wrong on c3, right on c1 and c2
    assert s['repeatability']['grounded'] == approx(1.0)  # constant by construction
    assert s['cost']['total_cost_usd'] == approx(0.0)


def test_rep_count_rejects_a_ragged_run():
    rows = [r for r in rows_of() if not (r['id'] == 'c1' and r['qid'] == 'grounded' and r['rep'] == 2)]
    with pytest.raises(ValueError, match='unequal repetition counts'):
        rep_count(cells_of(rows))
