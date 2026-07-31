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

4. On circular targets the two endpoints of a submitted interval were localized to the
   branch nearest the truth independently, which rewrote the interval. Widening an
   equally wrong answer could cut its penalty 14-fold, so the score was not monotone in
   how wrong the answer was.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from pereval.scorers.interval import (
    MISSING_PENALTY_FLOOR,
    degenerate_answer,
    localize_interval,
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


def test_drivers_rotate_by_default_and_families_only_on_request():
    """Drivers rotate by default because that is the security fix. The functional form
    does not, because rotating it changes the task rather than protecting it, and
    switching it on by default would strand the archived CCAR results."""
    seeds = np.random.SeedSequence(6).generate_state(40, dtype=np.uint32)
    dgps = [ccar_gen.generate(seed=int(s), oracle_n=20)["dgp"] for s in seeds]
    assert {d["family"] for d in dgps} == {ccar_gen.DEFAULT_FAMILY}
    rotated = [ccar_gen.generate(seed=int(s), oracle_n=20, family="rotate")["dgp"]
               for s in seeds]
    assert {d["family"] for d in rotated} == set(ccar_gen.FAMILIES)
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
    rotating the family would not be rotating anything.

    Pinned to a severe scenario because the family factor is INERT under a benign one by
    construction: a kink acts only above its threshold and a cross term only when both
    drivers are far from their means, so under `baseline` all three families coincide
    (measured: 11 of 12 seeds show both deviations below 0.01). That is the trap working
    as intended, not a defect, and it is why family and scenario are crossed rather than
    varied independently."""
    paths = {f: [p["true_mean"] for p in
                 ccar_gen.generate(seed=13, family=f, scenario="severe", oracle_n=20)["points"]]
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


# --- 4. circular interval localization -------------------------------------

def _circular_points(true_mean=10.0, sd=1.0, n_mc=20000, seed=0):
    rng = np.random.default_rng(seed)
    return [{"key": (1.0,), "class": None, "true_mean": true_mean,
             "mc": (true_mean + rng.normal(0.0, sd, n_mc)) % 360.0}]


def _winkler(pred, true_mean=10.0):
    return score_points(_circular_points(true_mean), {(1.0,): pred}, 360.0)["winkler_agent"]


def test_a_wrapping_interval_keeps_its_width():
    """[350, 30] means the 40-degree arc through zero, not a 320-degree arc."""
    lo, hi = localize_interval(350.0, 30.0, 10.0, 360.0)
    assert hi - lo == pytest.approx(40.0)
    assert lo == pytest.approx(-10.0)


def test_an_unwrapped_prediction_is_placed_on_the_right_branch():
    """The harmonic baseline emits continuous longitudes in the thousands."""
    lo, hi = localize_interval(4990.0, 5010.0, 10.0, 360.0)
    assert hi - lo == pytest.approx(20.0)
    assert abs(((lo + hi) / 2.0) - 10.0) < 180.0


def test_coverage_is_claimed_exactly_when_the_truth_is_on_the_submitted_arc():
    """The real invariant, and the one the old code broke.

    Winkler is deliberately NOT monotone in width: widening an interval eventually buys
    coverage, and on a circle growing an arc from a fixed lower endpoint brings its far
    end round toward the truth, so the penalty can legitimately fall. What must never
    happen is the scorer crediting coverage for an arc the agent did not submit, which
    is what independent endpoint localization did.
    """
    tm, sd = 10.0, 0.05
    for lo in range(0, 360, 10):
        for width in (5.0, 40.0, 100.0, 200.0, 350.0):
            offset = float(np.mod(tm - lo, 360.0))
            agg = score_points(_circular_points(tm, sd=sd),
                               {(1.0,): (lo + width / 2.0, float(lo), lo + width)}, 360.0)
            assert agg["mean_width"] == pytest.approx(width), (lo, width)
            # Skip arcs whose endpoint sits on the true value: the noisy draws straddle
            # it there, so a coverage near 0.5 is correct rather than a defect.
            if min(offset, abs(offset - width)) < 10.0 * sd:
                continue
            assert (agg["coverage"] > 0.5) == (offset <= width), (lo, width, agg["coverage"])


def test_the_regression_case_that_scored_260():
    """True value 10, submission [100, 200]: a 90-degree miss. The old scorer wrapped the
    upper endpoint to -160, swapped the pair, and scored [-160, 100]: 260 wide and
    covering the truth, for a Winkler of 260 against 3610 for the same miss held tight."""
    agg = score_points(_circular_points(), {(1.0,): (150.0, 100.0, 200.0)}, 360.0)
    assert agg["coverage"] == 0.0
    assert agg["mean_width"] == pytest.approx(100.0)
    assert agg["winkler_agent"] == pytest.approx(100.0 + 40.0 * 90.0, rel=0.02)


def test_claiming_the_whole_circle_costs_the_period():
    """An honest refusal to localize should cost its width, not collapse to a point."""
    agg = score_points(_circular_points(), {(1.0,): (10.0, 0.0, 359.999)}, 360.0)
    assert agg["coverage"] == pytest.approx(1.0)
    assert 355.0 < agg["mean_width"] <= 360.0


def test_a_correct_circular_interval_is_unaffected():
    """The fix must not move the cases the old code got right."""
    agg = score_points(_circular_points(), {(1.0,): (10.0, 8.0, 12.0)}, 360.0)
    assert agg["coverage"] > 0.9
    assert agg["mean_width"] == pytest.approx(4.0)
    assert agg["mae"] == pytest.approx(0.0, abs=1e-9)


def test_linear_targets_still_swap_inverted_endpoints():
    assert localize_interval(5.0, 1.0, 0.0, None) == (1.0, 5.0)
    assert localize_interval(1.0, 5.0, 0.0, None) == (1.0, 5.0)


# --- 6. scenario severity as a designed factor ------------------------------

def test_scenario_severity_orders_the_stress_path():
    """baseline must be genuinely benign, not merely milder."""
    peaks = {}
    for scen in ccar_gen.SCENARIO_NAMES:
        b = ccar_gen.generate(seed=5, scenario=scen, family="vasicek", oracle_n=20)
        base = float(np.mean(b["default_rate"][b["intime_slice"]]))
        peaks[scen] = max(p["true_mean"] for p in b["points"]) / base
    assert peaks["baseline"] < 1.2 < peaks["adverse"] < peaks["severe"]


def test_benign_scenarios_make_over_prediction_expensive():
    """The point of keeping benign scenarios: a model that always leans adverse must pay
    for it somewhere. Conservatism is not a substitute for accuracy."""
    from scipy.stats import norm as _norm

    def lean(text, bump):
        import csv as _csv
        import io as _io
        rows = list(_csv.DictReader(_io.StringIO(text)))
        out = ["quarter,y_pred,y_lower,y_upper"]
        for r in rows:
            f = lambda k: _norm.cdf(_norm.ppf(min(max(float(r[k]), 1e-9), 1 - 1e-9)) + bump)  # noqa: E731
            out.append(f"{int(float(r['quarter']))},{f('y_pred')},{f('y_lower')},{f('y_upper')}")
        return "\n".join(out) + "\n"

    seeds = np.random.SeedSequence(21).generate_state(4, dtype=np.uint32)
    honest, leaning = [], []
    for s in seeds:
        b = ccar_gen.generate(seed=int(s), scenario="baseline", oracle_n=300)
        tr, sc = ccar_gen.train_csv_text(b), ccar_gen.scenario_csv_text(b)
        pts = ccar_gen.truth_to_points(ccar_gen.build_truth(b))
        base = _vasicek_fit_predict(tr, sc)
        honest.append(score_points(pts, parse_predictions(base, ["quarter"]))["winkler_regret"])
        leaning.append(score_points(pts, parse_predictions(lean(base, 0.5), ["quarter"]))["winkler_regret"])
    assert np.mean(leaning) > 3.0 * np.mean(honest)


def test_scenario_and_family_are_crossed_in_a_shipped_dataset():
    from pereval.tasks.ccar.task import _samples
    ids = [s.id for s in _samples(9, 1, 20, 80, "rotate", "rotate")]
    combos = {(i.split("-")[2], i.split("-")[3]) for i in ids}
    assert len(combos) == 9  # every family x scenario pair exactly once


# --- 5. flyby selection on the reference's own success ----------------------

@pytest.fixture(scope="module")
def flyby():
    """One filtered flyby instance. Module-scoped because each draw runs a multistart
    least-squares orbit determination, which is the expensive part of this file."""
    from pereval.tasks.orbit import hyperbolic as H
    return H, H.generate_hyperbolic(seed=1000, oracle_n=60, max_tries=3)


def test_flyby_records_which_instance_it_actually_drew(flyby):
    """The filter advances the seed, so a bare seed does not identify the data. The
    recorded offset has to close that gap or a published id names the wrong instance."""
    H, b = flyby
    off = b["meta"]["seed_offset"]
    direct = H._draw_instance(1000 + off, 60)
    assert H.train_csv_text(b) == H.train_csv_text(direct)
    assert b["meta"]["tries"] == off + 1


def test_flyby_reference_regret_is_bounded_by_the_acceptance_threshold(flyby):
    """Which is exactly why the reference row is definitional and not a measurement:
    it cannot exceed the threshold unless the search gave up."""
    H, b = flyby
    assert b["meta"]["reference_filtered"] is True
    assert (b["meta"]["reference_regret"] < H.MAX_REFERENCE_REGRET
            or b["meta"]["tries"] == 3)


def test_flyby_filter_can_be_disabled(flyby):
    H, _ = flyby
    b = H.generate_hyperbolic(seed=1000, oracle_n=60, max_reference_regret=None)
    assert b["meta"]["seed_offset"] == 0
    assert b["meta"]["tries"] == 1
    assert b["meta"]["reference_filtered"] is False


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
