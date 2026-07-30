"""Regression tests for three defects found by independent review.

Each test names the defect it guards. They are the tests that would have caught the
problems, which is the only useful kind.

1. Non-response was cheaper than a bad answer. Missing predictions were charged five
   times the ORACLE score, so on most tasks emitting nothing beat both the naive
   baseline and every model, and one published leaderboard row was in fact a provider
   outage scored as a result.

2. The CCAR response law was eight hard-coded constants in a public file, so the whole
   instance was solvable in closed form with no estimation.

3. Repeated runs varied the instance as well as the agent, so method instability and
   instance difficulty were not separable, even though instability is the thing a
   validator has to price.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from pereval.scorers.interval import (
    MISSING_PENALTY_FLOOR,
    degenerate_answer,
    score_points,
)
from pereval.scorers.stability import epochs, stability
from pereval.tasks.ccar import generator as ccar_gen
from pereval.tasks.ccar.baselines import _naive_fit_predict, _vasicek_fit_predict
from pereval.scorers.interval import parse_predictions


# --- 1. non-response pricing ------------------------------------------------

def _gauss_points(true_means, sd=1.0, n_mc=4000, seed=0):
    rng = np.random.default_rng(seed)
    return [
        {"key": (float(i),), "class": None, "true_mean": float(tm),
         "mc": tm + rng.normal(0.0, sd, n_mc)}
        for i, tm in enumerate(true_means)
    ]


def test_missing_is_priced_at_the_degenerate_answer_not_the_oracle():
    """A missing point costs what the least informative answer costs."""
    points = _gauss_points([0.0, 10.0, 20.0, 30.0], sd=1.0)
    agg = score_points(points, {})
    _, deg = degenerate_answer(points, None)
    assert agg["n_missing"] == 4
    assert agg["completion"] == 0.0
    # The whole submission is missing, so the agent score is the degenerate score.
    assert agg["winkler_agent"] == pytest.approx(float(np.mean(deg)), rel=1e-9)
    # And that is far above the old rule, which charged a multiple of the oracle.
    assert agg["winkler_agent"] > MISSING_PENALTY_FLOOR * agg["winkler_oracle"]


def test_missing_price_is_the_max_of_degenerate_and_the_oracle_floor():
    """Even with a flat target the degenerate answer is expensive, because it submits no
    interval at all and so pays the full miss penalty. So the oracle-multiple floor is a
    guard that in practice never binds, and the test pins the max() rather than pretending
    either branch always wins."""
    for true_means in ([5.0, 5.0, 5.0], [0.0, 10.0, 20.0]):
        points = _gauss_points(true_means, sd=1.0)
        agg = score_points(points, {})
        _, deg = degenerate_answer(points, None)
        expected = np.mean([max(d, MISSING_PENALTY_FLOOR * agg["winkler_oracle"]) for d in deg])
        assert agg["winkler_agent"] == pytest.approx(float(expected), rel=1e-6)
        assert agg["winkler_agent"] >= MISSING_PENALTY_FLOOR * agg["winkler_oracle"]


def test_abstaining_is_worse_than_a_bad_but_informative_answer():
    """The defect in one line: a wide, badly centred, but real answer must beat silence."""
    points = _gauss_points([0.0, 10.0, 20.0, 30.0], sd=1.0)
    sloppy = {(float(i),): (tm + 3.0, tm - 8.0, tm + 14.0)
              for i, tm in enumerate([0.0, 10.0, 20.0, 30.0])}
    assert score_points(points, sloppy)["winkler_regret"] < score_points(points, {})["winkler_regret"]


def test_partial_submission_is_penalized_only_on_the_missing_points():
    points = _gauss_points([0.0, 10.0, 20.0, 30.0], sd=1.0)
    exact = {(float(i),): (tm, tm - 1.96, tm + 1.96)
             for i, tm in enumerate([0.0, 10.0, 20.0, 30.0])}
    partial = {k: v for k, v in list(exact.items())[:2]}
    full, half, none = (score_points(points, p) for p in (exact, partial, {}))
    assert full["completion"] == 1.0
    assert half["completion"] == 0.5
    assert full["winkler_regret"] < half["winkler_regret"] < none["winkler_regret"]


def test_degenerate_regret_is_reported_so_worse_than_useless_is_visible():
    points = _gauss_points([0.0, 10.0, 20.0, 30.0], sd=1.0)
    awful = {(float(i),): (tm + 200.0, tm + 199.0, tm + 201.0)
             for i, tm in enumerate([0.0, 10.0, 20.0, 30.0])}
    agg = score_points(points, awful)
    assert agg["degenerate_regret"] > 0
    assert agg["winkler_regret"] > agg["degenerate_regret"]


def test_circular_degenerate_uses_the_circular_mean():
    """On a circular target the constant answer must be a circular mean, or two angles
    either side of the seam would average to the far side of the circle."""
    c, _ = degenerate_answer(
        [{"key": (0.0,), "class": None, "true_mean": 350.0, "mc": np.array([350.0])},
         {"key": (1.0,), "class": None, "true_mean": 10.0, "mc": np.array([10.0])}],
        360.0)
    assert min(abs(c - 0.0), abs(c - 360.0)) < 1e-6


def test_ccar_abstention_is_worse_than_the_naive_baseline():
    """The end-to-end version on the real task, which is where it went wrong."""
    seeds = np.random.SeedSequence(1).generate_state(3, dtype=np.uint32)
    naive, silent = [], []
    for s in seeds:
        b = ccar_gen.generate(seed=int(s), oracle_n=300)
        points = ccar_gen.truth_to_points(ccar_gen.build_truth(b))
        preds = parse_predictions(
            _naive_fit_predict(ccar_gen.train_csv_text(b), ccar_gen.scenario_csv_text(b)),
            ["quarter"])
        naive.append(score_points(points, preds)["winkler_regret"])
        silent.append(score_points(points, {})["winkler_regret"])
    assert np.mean(silent) > np.mean(naive)


# --- 2. CCAR data-generating process ---------------------------------------

def test_response_law_varies_across_seeds():
    seeds = np.random.SeedSequence(5).generate_state(12, dtype=np.uint32)
    dgps = [ccar_gen.generate(seed=int(s), oracle_n=20)["dgp"] for s in seeds]
    for key in ("p", "rho", "k1", "k2"):
        assert len({round(d[key], 9) for d in dgps}) > 1, f"{key} is constant across seeds"
    assert len({(d["family"], d["d1"], d["d2"]) for d in dgps}) > 1


def test_drivers_and_families_both_rotate():
    seeds = np.random.SeedSequence(6).generate_state(40, dtype=np.uint32)
    dgps = [ccar_gen.generate(seed=int(s), oracle_n=20)["dgp"] for s in seeds]
    assert {d["family"] for d in dgps} == set(ccar_gen.FAMILIES)
    assert len({d["d1"] for d in dgps}) > 1
    assert len({d["d2"] for d in dgps}) > 1
    assert all(d["d1"] in ccar_gen.DRIVERS_UP for d in dgps)
    assert all(d["d2"] in ccar_gen.DRIVERS_DOWN for d in dgps)


def test_published_constants_no_longer_solve_an_instance():
    """The exploit, verbatim: the eight constants that used to be module-level in the
    generator, applied in closed form with no estimation.

    It used to score 0.0001 mean regret, 90x better than the fitted reference and 200x
    better than the best measured model. It must now be beaten even by a fit that is
    handed the true drivers, which is the strongest honest reference the suite has.

    Compared on medians over nine balanced instances rather than means: per-instance
    regret is heavy-right-tailed here, and a four-instance mean comparison was not
    stable enough to assert. Measured over 18 instances the means are 0.648 for the
    exploit against 0.271 informed and 0.346 competent; the medians are 0.324, 0.072
    and 0.112.
    """
    old = dict(p=0.028, rho=0.02, k1=0.13, k2=-0.07,
               u_mean=5.66, u_sd=1.72, y_mean=0.0442, y_sd=0.0580)
    seeds = np.random.SeedSequence(1).generate_state(9, dtype=np.uint32)
    cheat, reference = [], []
    for i, s in enumerate(seeds):
        b = ccar_gen.generate(seed=int(s), family=ccar_gen.FAMILIES[i % 3], oracle_n=300)
        tr, sc = ccar_gen.train_csv_text(b), ccar_gen.scenario_csv_text(b)
        points = ccar_gen.truth_to_points(ccar_gen.build_truth(b))
        dgp = b["dgp"]

        import csv
        import io
        trr = list(csv.DictReader(io.StringIO(tr)))
        scr = list(csv.DictReader(io.StringIO(sc)))
        hpi = np.array([float(r["hpi"]) if r["hpi"] else np.nan for r in trr]
                       + [float(r["hpi"]) for r in scr])
        yoy = np.full(len(hpi), np.nan)
        yoy[4:] = hpi[4:] / hpi[:-4] - 1.0
        u = np.array([float(r["unemployment"]) for r in scr])
        lin = (norm.ppf(old["p"])
               + old["k1"] * (u - old["u_mean"]) / old["u_sd"]
               + old["k2"] * (yoy[len(trr):] - old["y_mean"]) / old["y_sd"])
        a = lin / np.sqrt(1 - old["rho"])
        sr = np.sqrt(old["rho"]) / np.sqrt(1 - old["rho"])
        text = "\n".join(
            ["quarter,y_pred,y_lower,y_upper"]
            + [f"{int(float(r['quarter']))},{p},{lo},{hi}" for r, p, lo, hi in zip(
                scr, norm.cdf(lin), norm.cdf(a - 1.96 * sr), norm.cdf(a + 1.96 * sr))])
        cheat.append(score_points(points, parse_predictions(text, ["quarter"]))["winkler_regret"])
        informed = _vasicek_fit_predict(tr, sc, [f"{dgp['d1']}:level", f"{dgp['d2']}:yoy"])
        reference.append(score_points(
            points, parse_predictions(informed, ["quarter"]))["winkler_regret"])
    assert np.median(cheat) > 2.0 * np.median(reference)
    assert np.median(cheat) > 0.05  # nowhere near the oracle it used to sit on


@pytest.mark.parametrize("family", ccar_gen.FAMILIES)
def test_oracle_true_mean_matches_the_law_by_monte_carlo(family):
    """E[dr] = Phi(lin) must hold for every family, or the oracle is not the oracle."""
    b = ccar_gen.generate(seed=11, family=family, oracle_n=40000)
    for p in b["points"]:
        assert p["true_mean"] == pytest.approx(float(np.mean(p["mc_samples"])), abs=0.004)


@pytest.mark.parametrize("family", ccar_gen.FAMILIES)
def test_every_family_produces_a_rising_stress_path(family):
    b = ccar_gen.generate(seed=13, family=family, oracle_n=20)
    means = [p["true_mean"] for p in b["points"]]
    assert means[-1] > means[0]
    assert all(0.0 < m < 0.75 for m in means)


def test_families_are_materially_different_on_the_same_seed():
    """Same macros, same severity, different law: the stressed paths must diverge, or
    rotating the family would not be rotating anything."""
    paths = {f: [p["true_mean"] for p in
                 ccar_gen.generate(seed=13, family=f, oracle_n=20)["points"]]
             for f in ccar_gen.FAMILIES}
    base = np.array(paths["vasicek"])
    for f in ("threshold", "interaction"):
        assert np.max(np.abs(np.array(paths[f]) - base)) > 0.01


def test_standardization_ignores_the_stress_window():
    """The DGP must not peek at the scenario, so extending the stress path cannot move
    the in-time default rates."""
    a = ccar_gen.generate(seed=21, family="vasicek", oracle_n=20)
    b = ccar_gen.generate(seed=21, family="vasicek", oracle_n=20, n_intime=80)
    np.testing.assert_allclose(a["default_rate"][:104], b["default_rate"][:104])


def test_truth_records_the_law_for_audit():
    truth = ccar_gen.build_truth(ccar_gen.generate(seed=3, oracle_n=20))
    dgp = truth["meta"]["dgp"]
    assert dgp["family"] in ccar_gen.FAMILIES
    assert {"p", "rho", "k1", "k2", "d1", "d2"} <= set(dgp)


# --- 3. same-instance stability --------------------------------------------

def _score(value):
    from inspect_ai.scorer import Score
    return Score(value=value)


def test_stability_reducer_reports_worst_and_spread():
    reduce = stability()
    out = reduce([_score({"winkler_regret": r, "coverage": 0.5, "completion": 1.0})
                  for r in (1.0, 5.0, 3.0)]).value
    assert out["runs"] == 3.0
    assert out["winkler_regret"] == pytest.approx(3.0)   # mean
    assert out["regret_worst"] == pytest.approx(5.0)
    assert out["regret_spread"] == pytest.approx(4.0)
    assert out["coverage"] == pytest.approx(0.5)


def test_stability_reducer_handles_the_pinball_key():
    reduce = stability()
    out = reduce([_score({"pinball_regret": r}) for r in (0.10, 0.20)]).value
    assert out["regret_worst"] == pytest.approx(0.20)
    assert out["regret_spread"] == pytest.approx(0.10)


def test_a_fixed_method_shows_zero_spread():
    """The interpretation that matters: no spread means one validation covers every run."""
    reduce = stability()
    out = reduce([_score({"winkler_regret": 2.0}) for _ in range(4)]).value
    assert out["regret_spread"] == pytest.approx(0.0)
    assert out["regret_worst"] == pytest.approx(2.0)


def test_single_run_scores_already_carry_the_stability_keys():
    """So a table can read the same fields whether or not repeats was used."""
    agg = score_points(_gauss_points([0.0, 5.0]), {})
    from pereval.scorers.interval import score_value_and_explanation
    value, _ = score_value_and_explanation(agg)
    assert value["runs"] == 1.0
    assert value["regret_spread"] == 0.0
    assert value["regret_worst"] == pytest.approx(value["winkler_regret"])


def test_epochs_helper_is_inert_for_a_single_run():
    assert epochs(1) is None
    assert epochs(0) is None
    assert epochs(None) is None
    e = epochs(5)
    assert e is not None and e.epochs == 5
