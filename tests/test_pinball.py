"""Pinball scorer: properness, regret floor, penalties, and parsing."""

from __future__ import annotations

import numpy as np
import pytest

from pereval.scorers.pinball import (
    TAUS,
    aggregate,
    parse_predictions,
    pinball_loss,
    pinball_regret,
    score_block,
    type7,
)


@pytest.fixture(scope="module")
def pop():
    """Right-skewed population, standing in for a macro YoY series."""
    rng = np.random.default_rng(0)
    return np.sort(rng.lognormal(1.0, 0.8, 400) - 2.0)


def _block(pop, rng=None):
    rng = rng or np.random.default_rng(3)
    x = np.sort(rng.choice(pop, 10, replace=False))
    return dict(pop=pop, sd=float(pop.std()), x=x)


# --- properness ------------------------------------------------------------

@pytest.mark.parametrize("tau", TAUS)
def test_regret_zero_at_population_quantile(pop, tau):
    assert pinball_regret(float(np.quantile(pop, tau)), pop, tau) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("tau", TAUS)
def test_regret_nonnegative_everywhere(pop, tau):
    grid = np.linspace(pop.min() - 5, pop.max() + 5, 2000)
    assert min(pinball_regret(q, pop, tau) for q in grid) >= -1e-12


@pytest.mark.parametrize("tau", TAUS)
def test_minimiser_is_the_population_quantile(pop, tau):
    """The whole design rests on this: the population supplies its own floor."""
    grid = np.linspace(pop.min(), pop.max(), 4000)
    best = grid[np.argmin([pinball_loss(q, pop, tau) for q in grid])]
    assert best == pytest.approx(float(np.quantile(pop, tau)), abs=2 * (grid[1] - grid[0]))


def test_underestimation_costs_more_than_equal_overestimation(pop):
    """Why type 7's downward bias is penalised and a mean-based loss misses it.

    The ratio at a finite displacement is modest on a heavy right tail, because
    F barely moves above q95. The 19:1 figure is asymptotic, not local.
    """
    q = float(np.quantile(pop, 0.95))
    d = 0.5 * pop.std()
    assert pinball_regret(q - d, pop, 0.95) > pinball_regret(q + d, pop, 0.95)


def test_asymptotic_slope_ratio_is_tau_over_one_minus_tau(pop):
    """dL/dq = F(q) - tau, so far below the support the slope is -tau and far
    above it is 1-tau. At tau=0.95 that is a 19:1 ratio in the limit."""
    q = float(np.quantile(pop, 0.95))
    D = 500.0 * pop.std()
    ratio = pinball_regret(q - D, pop, 0.95) / pinball_regret(q + D, pop, 0.95)
    assert ratio == pytest.approx(0.95 / 0.05, rel=0.02)


# --- block scoring ---------------------------------------------------------

def test_perfect_answer_scores_zero(pop):
    b = _block(pop)
    truth = {t: float(np.quantile(pop, t)) for t in TAUS}
    r = score_block(b, dict(q90=truth[0.90], q95=truth[0.95], q99=truth[0.99],
                            lo=truth[0.95] - 1, hi=truth[0.95] + 1))
    assert r["regret"] == pytest.approx(0.0, abs=1e-12)
    assert r["coverage"] == 1.0 and r["monotonic"] and not r["missing"]


def test_type7_scores_worse_than_perfect(pop):
    b = _block(pop)
    r = score_block(b, dict(q90=type7(b["x"], 0.90), q95=type7(b["x"], 0.95),
                            q99=type7(b["x"], 0.99), lo=0.0, hi=1.0))
    assert r["regret"] > 0


def test_type7_p99_p95_spread_is_the_known_constant(pop):
    """type 7 at n=10 puts p95 at h=9.55 and p99 at h=9.91, so the spread is
    exactly 0.36 of one order-statistic gap for every population."""
    b = _block(pop)
    r = score_block(b, dict(q90=type7(b["x"], 0.90), q95=type7(b["x"], 0.95),
                            q99=type7(b["x"], 0.99), lo=0.0, hi=1.0))
    assert r["spread"] == pytest.approx(0.36, abs=1e-9)


def test_missing_block_penalised_above_type7(pop):
    b = _block(pop)
    got = score_block(b, None)
    ref = score_block(b, dict(q90=type7(b["x"], 0.90), q95=type7(b["x"], 0.95),
                              q99=type7(b["x"], 0.99), lo=0.0, hi=1.0))
    assert got["missing"] and got["regret"] > ref["regret"]


def test_nonfinite_prediction_treated_as_missing(pop):
    assert score_block(_block(pop), dict(q90=1.0, q95=float("nan"), q99=3.0,
                                         lo=0.0, hi=1.0))["missing"]


def test_nonmonotonic_flagged_not_silently_sorted(pop):
    r = score_block(_block(pop), dict(q90=9.0, q95=5.0, q99=1.0, lo=0.0, hi=1.0))
    assert not r["monotonic"]


def test_reversed_interval_is_normalised(pop):
    b = _block(pop)
    t = float(np.quantile(pop, 0.95))
    a = score_block(b, dict(q90=1.0, q95=t, q99=2.0, lo=t + 1, hi=t - 1))
    assert a["coverage"] == 1.0


# --- aggregation and parsing ----------------------------------------------

def test_aggregate_counts_missing_and_keeps_regret(pop):
    recs = [score_block(_block(pop, np.random.default_rng(i)), None if i % 2 else
                        dict(q90=1.0, q95=2.0, q99=3.0, lo=1.0, hi=4.0))
            for i in range(6)]
    agg = aggregate(recs)
    assert agg["n_blocks"] == 6 and agg["n_missing"] == 3
    assert np.isfinite(agg["pinball_regret"])
    assert sum(agg[f"regret_p{int(t * 100)}"] for t in TAUS) == pytest.approx(
        agg["pinball_regret"], rel=1e-12)


def test_parse_predictions_roundtrip():
    txt = "block,q90,q95,q99,lo,hi\n1,1.0,2.0,3.0,1.5,2.5\n2,4,5,6,4.5,5.5\n"
    p = parse_predictions(txt)
    assert set(p) == {1, 2} and p[1]["q95"] == 2.0 and p[2]["hi"] == 5.5


def test_parse_predictions_tolerates_junk():
    assert parse_predictions(None) == {}
    assert parse_predictions("") == {}
    assert parse_predictions("wrong,header\n1,2\n") == {}
    good = parse_predictions("block,q90,q95,q99,lo,hi\n1,1,2,3,1,3\nx,y,z,w,v,u\n")
    assert set(good) == {1}
