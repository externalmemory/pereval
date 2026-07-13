"""Validation suite for the ballistic scorer.

A scorer is only trustworthy if it separates good solutions from bad ones, so we
plant solutions of known quality and assert the scorer ranks them correctly.
These tests are hermetic: they build a synthetic ground-truth fixture with known
Gaussian predictive distributions and do not run the ballistics simulator.
"""

from __future__ import annotations

import numpy as np
import pytest

from pereval.scorers.ballistic import (
    interval_score,
    parse_predictions,
    score_instance,
)


def _make_truth(n_mc: int = 6000) -> dict:
    """Two categories (one per class), a few points each, Gaussian predictive law."""
    rng = np.random.default_rng(0)
    specs = [
        ("Ra1aaa", "rifle", 500.0, -2.0, 0.30),
        ("Ra1aaa", "rifle", 800.0, -8.0, 0.55),
        ("Pb2bbb", "pistol", 125.0, -0.8, 0.20),
        ("Pb2bbb", "pistol", 200.0, -2.4, 0.40),
    ]
    test = []
    for cid, _cls, x, mean, sd in specs:
        mc = rng.normal(mean, sd, n_mc)
        test.append(
            {
                "category": cid,
                "x_m": x,
                "true_mean_y_m": float(mc.mean()),
                "predictive_pi95_m": [float(np.quantile(mc, 0.025)), float(np.quantile(mc, 0.975))],
                "mc_samples_m": mc.tolist(),
            }
        )
    categories = {"Ra1aaa": {"class": "rifle"}, "Pb2bbb": {"class": "pistol"}}
    return {"meta": {}, "categories": categories, "test": test}


def _preds_from(truth, point_fn, interval_fn):
    preds = {}
    for tp in truth["test"]:
        key = (tp["category"], float(tp["x_m"]))
        tm = tp["true_mean_y_m"]
        lo, hi = tp["predictive_pi95_m"]
        preds[key] = (point_fn(tm), *interval_fn(tm, lo, hi))
    return preds


# --- interval_score primitive ---------------------------------------------

def test_interval_score_inside_is_width():
    assert interval_score(0.0, 1.0, 0.5) == pytest.approx(1.0)


def test_interval_score_outside_penalized():
    # width 1 plus (2/0.05) * distance-outside
    assert interval_score(0.0, 1.0, 2.0) == pytest.approx(1.0 + 40.0 * 1.0)
    assert interval_score(0.0, 1.0, -1.0) == pytest.approx(1.0 + 40.0 * 1.0)


# --- planted solutions of known quality ------------------------------------

def test_oracle_solution_scores_near_zero_regret():
    truth = _make_truth()
    oracle = _preds_from(truth, lambda tm: tm, lambda tm, lo, hi: (lo, hi))
    r = score_instance(truth, oracle)
    assert r["winkler_regret"] == pytest.approx(0.0, abs=1e-9)
    assert r["mae"] == pytest.approx(0.0, abs=1e-9)
    assert r["coverage"] == pytest.approx(0.95, abs=0.02)
    assert r["n_missing"] == 0


def test_biased_point_hurts_mae_not_interval():
    """Winkler scores the interval; MAE scores the point. They are orthogonal."""
    truth = _make_truth()
    biased = _preds_from(truth, lambda tm: tm + 3.0, lambda tm, lo, hi: (lo, hi))
    r = score_instance(truth, biased)
    assert r["mae"] == pytest.approx(3.0, abs=1e-9)
    assert r["winkler_regret"] == pytest.approx(0.0, abs=1e-9)


def test_too_narrow_interval_undercovers_and_is_penalized():
    truth = _make_truth()
    narrow = _preds_from(truth, lambda tm: tm, lambda tm, lo, hi: (tm - 0.001, tm + 0.001))
    r = score_instance(truth, narrow)
    assert r["coverage"] < 0.2
    assert r["winkler_regret"] > 5.0  # several times the oracle interval score
    assert r["mean_width"] < 0.01


def test_too_wide_interval_overcovers_and_is_penalized():
    truth = _make_truth()
    wide = _preds_from(truth, lambda tm: tm, lambda tm, lo, hi: (tm - 1000.0, tm + 1000.0))
    r = score_instance(truth, wide)
    assert r["coverage"] > 0.99
    assert r["winkler_regret"] > 10.0
    assert r["mean_width"] > 100.0


def test_scorer_orders_solutions_correctly():
    """The whole point: oracle beats both degenerate extremes on the headline."""
    truth = _make_truth()
    oracle = _preds_from(truth, lambda tm: tm, lambda tm, lo, hi: (lo, hi))
    narrow = _preds_from(truth, lambda tm: tm, lambda tm, lo, hi: (tm - 0.001, tm + 0.001))
    wide = _preds_from(truth, lambda tm: tm, lambda tm, lo, hi: (tm - 1000.0, tm + 1000.0))
    o = score_instance(truth, oracle)["winkler_regret"]
    n = score_instance(truth, narrow)["winkler_regret"]
    w = score_instance(truth, wide)["winkler_regret"]
    assert o < n
    assert o < w


def test_swapped_bounds_are_repaired():
    truth = _make_truth()
    swapped = _preds_from(truth, lambda tm: tm, lambda tm, lo, hi: (hi, lo))  # hi/lo reversed
    r = score_instance(truth, swapped)
    assert r["winkler_regret"] == pytest.approx(0.0, abs=1e-9)


def test_missing_predictions_penalized_finitely():
    truth = _make_truth()
    r = score_instance(truth, {})
    assert r["n_missing"] == r["n_points"]
    assert np.isfinite(r["winkler_regret"]) and r["winkler_regret"] > 0
    assert np.isfinite(r["mae"]) and r["mae"] > 0
    assert r["coverage"] == 0.0


def test_partial_predictions_penalize_only_missing():
    truth = _make_truth()
    full = _preds_from(truth, lambda tm: tm, lambda tm, lo, hi: (lo, hi))
    partial = dict(list(full.items())[:2])  # drop half the points
    r = score_instance(truth, partial)
    assert r["n_missing"] == 2
    assert r["winkler_regret"] > 0.0


def test_per_class_breakdown_present():
    truth = _make_truth()
    oracle = _preds_from(truth, lambda tm: tm, lambda tm, lo, hi: (lo, hi))
    r = score_instance(truth, oracle)
    assert set(r["per_class"]) == {"rifle", "pistol"}
    assert r["per_class"]["rifle"]["winkler_regret"] == pytest.approx(0.0, abs=1e-9)


# --- prediction parsing -----------------------------------------------------

def test_parse_predictions_basic_and_reordered_columns():
    text = "y_upper,category,x,y_pred,y_lower\n-1.0,Ra1aaa,500.0,-2.0,-3.0\n"
    preds = parse_predictions(text)
    assert preds[("Ra1aaa", 500.0)] == (-2.0, -3.0, -1.0)


def test_parse_predictions_rejects_missing_columns_and_bad_rows():
    assert parse_predictions("category,x,y_pred\nRa1aaa,500,-2\n") == {}
    assert parse_predictions(None) == {}
    assert parse_predictions("") == {}
    good = "category,x,y_pred,y_lower,y_upper\nRa1aaa,500,-2,-3,-1\nRa1aaa,bad,x,y,z\n"
    preds = parse_predictions(good)
    assert list(preds) == [("Ra1aaa", 500.0)]
