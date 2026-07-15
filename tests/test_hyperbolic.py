"""Hyperbolic-flyby generator invariants, rejection determinism, and baselines."""

from __future__ import annotations

import numpy as np
import pytest

from pereval.scorers.interval import parse_predictions, score_points
from pereval.tasks.orbit.hyperbolic import (
    _draw_instance,
    _od_fit_predict,
    _poly_fit_predict,
    build_truth,
    generate_hyperbolic,
    test_csv_text,
    train_csv_text,
    truth_to_points,
)


@pytest.fixture(scope="module")
def bundle():
    return generate_hyperbolic(seed=1000, oracle_n=500)


def test_deterministic_including_rejection():
    a = generate_hyperbolic(seed=9000, oracle_n=60)
    b = generate_hyperbolic(seed=9000, oracle_n=60)
    assert a["train_rows"] == b["train_rows"]
    assert a["meta"]["seed_offset"] == b["meta"]["seed_offset"]


def test_shapes_and_columns(bundle):
    assert len(bundle["points"]) == len(bundle["test_t"]) >= 8
    rows = train_csv_text(bundle).splitlines()
    assert rows[0] == "t,alpha,beta,gamma"
    data = [r.split(",") for r in rows[1:]]
    assert all(r[1] != "" for r in data)  # alpha (the planet) always observed
    assert data[-1][2] != "" and data[-1][3] != ""  # ISO observed near perihelion


def test_missing_data_occurs_for_fast_flybys():
    """Fast flybys leave the ISO unobservable early: beta/gamma blank while alpha
    stays present. Uses the raw generator (no rejection) to stay fast."""
    found = False
    for seed in range(30):
        data = [r.split(",") for r in train_csv_text(_draw_instance(seed, 20)).splitlines()[1:]]
        assert all(r[1] != "" for r in data)  # alpha always present
        if any(r[2] == "" for r in data):
            found = True
    assert found


def test_rejection_guarantees_solvable_reference(bundle):
    # by construction the shipped instance's reference reaches near the oracle
    assert bundle["meta"]["reference_regret"] < 0.5


def test_od_reference_beats_naive_polynomial(bundle):
    pts = truth_to_points(build_truth(bundle))
    tr, te = train_csv_text(bundle), test_csv_text(bundle)
    od = score_points(pts, parse_predictions(_od_fit_predict(tr, te), ["t"]), period=None)
    poly = score_points(pts, parse_predictions(_poly_fit_predict(tr, te), ["t"]), period=None)
    assert od["winkler_regret"] < 0.5  # near-oracle
    assert od["coverage"] > 0.85
    assert poly["winkler_regret"] > 10 * od["winkler_regret"]  # a flyby is not a polynomial


def test_oracle_round_trips_to_zero_regret(bundle):
    truth = build_truth(bundle)
    preds = {}
    for p in truth["points"]:
        mc = np.asarray(p["mc_samples"])
        preds[(float(p["t"]),)] = (p["true_mean"], float(np.quantile(mc, 0.025)), float(np.quantile(mc, 0.975)))
    r = score_points(truth_to_points(truth), preds, period=None)
    assert r["winkler_regret"] == pytest.approx(0.0, abs=1e-4)
    assert r["coverage"] == pytest.approx(0.95, abs=0.06)
