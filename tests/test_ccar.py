"""CCAR generator invariants, scorer integration, and baseline bracketing."""

from __future__ import annotations

import numpy as np
import pytest

from pereval.scorers.interval import parse_predictions, score_points
from pereval.tasks.ccar.baselines import _naive_fit_predict, _vasicek_fit_predict
from pereval.tasks.ccar.generator import (
    MACRO_COLUMNS,
    build_truth,
    generate,
    scenario_csv_text,
    train_csv_text,
    truth_to_points,
)


@pytest.fixture(scope="module")
def bundle():
    return generate(seed=7, n_intime=80, oracle_n=500)


def test_deterministic():
    a = generate(seed=3, n_intime=80, oracle_n=50)
    b = generate(seed=3, n_intime=80, oracle_n=50)
    assert a["train_rows"] == b["train_rows"]
    assert a["scenario_rows"] == b["scenario_rows"]


def test_shapes_and_columns(bundle):
    assert len(bundle["train_rows"]) == 80
    assert len(bundle["scenario_rows"]) == 9
    assert len(bundle["points"]) == 9
    assert set(bundle["train_rows"][0]) == {"quarter", *MACRO_COLUMNS, "default_rate"}
    assert "default_rate" not in bundle["scenario_rows"][0]  # scenario hides the target


def test_ragged_missing_present(bundle):
    # the later-starting series are blank for at least the first quarter
    first = bundle["train_rows"][0]
    assert any(first[m] == "" for m in ["hpi", "vix", "bbb_spread", "sp500", "djia"])
    # gdp / unemployment / cpi / nasdaq present from the start
    assert all(first[m] != "" for m in ["gdp", "unemployment", "cpi", "nasdaq"])


def test_stress_default_rises(bundle):
    means = [p["true_mean"] for p in bundle["points"]]
    assert means[-1] > means[0]  # the scenario is a stress path
    assert means[-1] > 0.03  # rises above the ~2.8% baseline


def test_crisis_disconnect_exists():
    # find an instance with a crisis, and confirm the observed unemployment spike
    # does not move the default rate (uses the fundamental)
    for seed in range(10):
        b = generate(seed=seed, n_intime=80, oracle_n=20)
        ci = np.where(b["crisis"] > 0)[0]
        if not len(ci):
            continue
        c = ci[0]
        dr, unemp = b["default_rate"], b["levels"]["unemployment"]
        spike = unemp[c] - 0.5 * (unemp[c - 1] + unemp[c + 1])
        dr_jump = abs(dr[c] - 0.5 * (dr[c - 1] + dr[c + 1]))
        if spike > 3.0:  # a real observed unemployment spike (percentage points)
            assert dr_jump < 0.01  # default barely moves
            return
    pytest.skip("no suitable crisis instance in the first 10 seeds")


def test_oracle_round_trips_to_zero_regret(bundle):
    truth = build_truth(bundle)
    points = truth_to_points(truth)
    preds = {}
    for p in truth["points"]:
        mc = np.asarray(p["mc_samples"])
        preds[(float(p["quarter"]),)] = (p["true_mean"], float(np.quantile(mc, 0.025)), float(np.quantile(mc, 0.975)))
    r = score_points(points, preds, period=None)
    assert r["winkler_regret"] == pytest.approx(0.0, abs=1e-4)
    assert r["mae"] == pytest.approx(0.0, abs=1e-6)
    assert r["coverage"] == pytest.approx(0.95, abs=0.05)
    assert r["n_missing"] == 0


def _score(bundle, fit_fn):
    truth = build_truth(bundle)
    preds = parse_predictions(fit_fn(train_csv_text(bundle), scenario_csv_text(bundle)), ["quarter"])
    return score_points(truth_to_points(truth), preds, period=None)


def test_vasicek_reference_near_oracle(bundle):
    r = _score(bundle, _vasicek_fit_predict)
    assert r["n_missing"] == 0
    assert r["winkler_regret"] < 0.1  # fits the true model class up to finite-sample error
    assert r["coverage"] > 0.8


def test_naive_baseline_beaten_by_reference_on_average():
    """Over several instances the reference should clearly beat the naive
    OLS-on-levels, which is fragile under stress extrapolation."""
    naive, vas = [], []
    for seed in [1, 2, 3, 7, 11]:
        b = generate(seed=seed, n_intime=80, oracle_n=400)
        naive.append(_score(b, _naive_fit_predict)["winkler_regret"])
        vas.append(_score(b, _vasicek_fit_predict)["winkler_regret"])
    assert np.mean(vas) < np.mean(naive)
    assert all(np.isfinite(naive))  # naive still produces complete predictions
