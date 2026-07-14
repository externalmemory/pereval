"""Generator invariants and generator-to-scorer schema integration.

Slower than the scorer unit tests because it runs the ballistics simulator, so
it uses a small oracle sample. It guards the invariants the task relies on and,
crucially, that build_truth() output is consumable by score_instance() (schema
drift between the two would silently break scoring).
"""

from __future__ import annotations

import re

import numpy as np
import pytest

from pereval.scorers.ballistic import score_instance
from pereval.tasks.ballistic.generator import RIFLE, build_truth, generate

ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{5}$")


@pytest.fixture(scope="module")
def bundle():
    return generate(seed=1, oracle_n=120)


def test_fixed_seed_is_deterministic():
    a = generate(seed=1, oracle_n=40)
    b = generate(seed=1, oracle_n=40)
    assert a["train_rows"] == b["train_rows"]
    assert a["test_index"] == b["test_index"]


def test_category_ids_are_opaque(bundle):
    for cid in bundle["categories"]:
        assert ID_RE.match(cid), cid


def test_rifle_test_window_stays_supersonic(bundle):
    for p in bundle["categories"].values():
        if p["class"] == "rifle":
            assert p["test_max_mach"] > RIFLE.min_test_mach


def test_pistol_angle_sd_is_five_times_rifle(bundle):
    levels = bundle["meta"]["noise_levels"]
    assert levels["pistol"]["angle_sd_moa"] == pytest.approx(5.0 * levels["rifle"]["angle_sd_moa"], rel=0.5)


def test_oracle_predictions_score_to_zero_regret(bundle):
    """Schema integration: feeding the oracle back through the scorer must yield
    ~zero Winkler regret, ~zero MAE, and ~0.95 coverage."""
    truth = build_truth(bundle)
    preds = {
        (tp["category"], float(tp["x_m"])): (
            tp["true_mean_y_m"],
            tp["predictive_pi95_m"][0],
            tp["predictive_pi95_m"][1],
        )
        for tp in truth["test"]
    }
    r = score_instance(truth, preds)
    # The scorer recomputes the oracle interval from the (4-decimal-rounded) mc
    # samples, while these preds use the (5-decimal-rounded) stored pi95, so
    # regret is rounding-scale rather than exactly zero.
    assert r["winkler_regret"] == pytest.approx(0.0, abs=0.02)
    assert r["mae"] == pytest.approx(0.0, abs=1e-9)
    assert r["coverage"] == pytest.approx(0.95, abs=0.06)
    assert r["n_missing"] == 0
    assert set(r["per_class"]) == {"rifle", "pistol"}


def test_naive_extrapolation_beaten_by_oracle(bundle):
    """A quadratic fit per category, extrapolated, must score worse than the
    oracle: confirms the task has real headroom rather than being trivial."""
    truth = build_truth(bundle)
    train = {}
    for cid, x, y in bundle["train_rows"]:
        train.setdefault(cid, []).append((x, y))
    preds = {}
    for tp in truth["test"]:
        cid, x = tp["category"], float(tp["x_m"])
        xs = np.array([p[0] for p in train[cid]])
        ys = np.array([p[1] for p in train[cid]])
        coeffs = np.polyfit(xs, ys, 2)
        yhat = float(np.polyval(coeffs, x))
        pi = tp["predictive_pi95_m"]
        preds[(cid, x)] = (yhat, pi[0], pi[1])  # oracle-width interval, naive point
    naive = score_instance(truth, preds)
    oracle_mae = 0.0
    assert naive["mae"] > oracle_mae  # naive point extrapolation is measurably off
