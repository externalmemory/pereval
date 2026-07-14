"""Orbit generator invariants, circular scoring, and baseline sanity."""

from __future__ import annotations

import numpy as np
import pytest

from pereval.scorers.interval import _localize, interval_score, score_points
from pereval.tasks.orbit.baselines import _fit_and_predict
from pereval.scorers.interval import parse_predictions
from pereval.tasks.orbit.generator import (
    _kepler_longitude,
    build_truth,
    generate_threebody,
    generate_twobody,
    truth_to_points,
)


# --- circular scoring primitives -------------------------------------------

def test_localize_handles_wrap():
    # 359 relative to a true value of 1 is -1 (two degrees apart, across 0/360)
    assert float(_localize([359.0], 1.0, 360.0)[0]) == pytest.approx(-1.0)
    assert float(_localize([1.0], 359.0, 360.0)[0]) == pytest.approx(361.0)


def test_circular_coverage_not_fooled_by_wrap():
    # truth ~1 deg, mc spread across the 0/360 seam; an interval [-3,5] should cover ~all
    tm = 1.0
    mc = (tm + np.random.default_rng(0).normal(0, 1.0, 4000)) % 360.0
    pts = [{"key": (10.0,), "class": None, "true_mean": tm, "mc": mc}]
    good = score_points(pts, {(10.0,): (1.0, -3.0, 5.0)}, period=360.0)
    assert good["coverage"] > 0.99
    # a linear scorer (period=None) would miscount the wrapped samples
    linear = score_points(pts, {(10.0,): (1.0, -3.0, 5.0)}, period=None)
    assert linear["coverage"] < good["coverage"]


def test_interval_score_primitive():
    assert interval_score(0.0, 1.0, 0.5) == pytest.approx(1.0)
    assert interval_score(0.0, 1.0, 2.0) == pytest.approx(1.0 + 40.0)


# --- generator invariants ---------------------------------------------------

def test_kepler_longitude_periodic():
    P, e, w, t0 = 400.0, 0.3, 45.0, 12.0
    a = _kepler_longitude(np.array([100.0]), P, e, w, t0)[0]
    b = _kepler_longitude(np.array([100.0 + P]), P, e, w, t0)[0]
    assert abs(((a - b + 180) % 360) - 180) < 1e-6  # same angle one period later


def test_twobody_deterministic_and_covers_orbits():
    a = generate_twobody(seed=3, oracle_n=30)
    b = generate_twobody(seed=3, oracle_n=30)
    assert a["train_rows"] == b["train_rows"]
    m = a["meta"]
    assert m["total_days"] / m["orbits"]["alpha"]["P"] >= 3.5  # several orbits observed
    assert all(d > m["total_days"] for d in a["test_days"])  # held out in the future


def test_threebody_target_is_undersampled_outer_planet():
    b = generate_threebody(seed=3, oracle_n=30)
    m = b["meta"]
    assert m["target"] == "beta"
    assert b["header"] == ["t", "alpha", "beta"]
    inner = m["total_days"] / m["orbits"]["alpha"]["P"]
    outer = m["total_days"] / m["orbits"]["beta"]["P"]
    assert outer < inner  # beta (outer) completes fewer orbits, the harder target


@pytest.mark.parametrize("gen", [generate_twobody, generate_threebody])
def test_oracle_scores_to_zero_regret(gen):
    bundle = gen(seed=2, oracle_n=300)
    truth = build_truth(bundle)
    points = truth_to_points(truth)
    preds = {}
    for p in truth["points"]:
        mc = _localize(np.asarray(p["mc_samples"]), p["true_mean"], 360.0)
        preds[(float(p["t"]),)] = (p["true_mean"], float(np.quantile(mc, 0.025)), float(np.quantile(mc, 0.975)))
    r = score_points(points, preds, period=360.0)
    assert r["winkler_regret"] == pytest.approx(0.0, abs=0.05)
    assert r["mae"] == pytest.approx(0.0, abs=1e-9)
    assert r["coverage"] == pytest.approx(0.95, abs=0.06)
    assert r["n_missing"] == 0


# --- baseline ---------------------------------------------------------------

def test_harmonic_baseline_produces_reasonable_predictions():
    """The naive periodic fit should predict every test point with a small point
    error, leaving interval calibration (undercoverage from period drift over the
    horizon) as the headroom a capable model closes."""
    bundle = generate_twobody(seed=5, oracle_n=300)
    truth = build_truth(bundle)
    points = truth_to_points(truth)
    train = "t,alpha\n" + "\n".join(f"{t},{a}" for t, a in bundle["train_rows"])
    test = "t\n" + "\n".join(str(d) for d in bundle["test_days"])
    preds = parse_predictions(_fit_and_predict(train, test, "alpha"), ["t"])
    r = score_points(points, preds, period=360.0)
    assert r["n_missing"] == 0
    assert r["mae"] < 5.0  # points within a few degrees on the easy periodic signal
    assert r["coverage"] > 0.3  # produces genuine (if undercovering) intervals
