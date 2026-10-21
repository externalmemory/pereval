"""Generator, scorer and reference invariants for the rating-migration task.

Several of these pin measurements that drove design choices, so that a later
change cannot quietly remove the property the choice was made for.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
from scipy.linalg import fractional_matrix_power

from pereval.scorers.migration import (
    CHECK_KEYS,
    ORDER,
    _downgrade_mass,
    _row_weights,
    ks_distance,
    model_checks,
    score_predictions,
)
from pereval.tasks.migration.baselines import predict
from pereval.tasks.migration.generator import (
    BASE_MIX,
    CHECKPOINTS,
    D,
    LIVE,
    MACRO_COLUMNS,
    N_OBLIGORS,
    SEVERITY_CAP,
    _withdrawal_adjusted_annual,
    conditional_matrix,
    expected_distributions,
    generate,
    holdout_mix,
    public_files,
    quarterly_base,
)

SEEDS = (1, 2, 3)
SCEN = ("baseline", "adverse", "severe")


@pytest.fixture(scope="module")
def bundle():
    return generate(1, n_years=20)


def test_deterministic():
    a = generate(3, n_years=12)
    b = generate(3, n_years=12)
    assert a["annual_counts"] == b["annual_counts"]
    assert a["truth"] == b["truth"]


def test_quarterly_base_is_stochastic_and_default_absorbing():
    q = quarterly_base()
    assert (q >= 0).all()
    assert np.allclose(q.sum(axis=1), 1.0)
    assert q[D, D] == 1.0 and q[D, :D].sum() == 0.0


def test_portfolio_mix_carries_about_one_percent_annual_default():
    """The calibration target: a large bank's wholesale book, not S&P's universe."""
    pd_annual = _withdrawal_adjusted_annual()[:D, D]
    assert float(BASE_MIX @ pd_annual) == pytest.approx(0.0099, abs=0.0015)
    assert BASE_MIX.sum() == pytest.approx(1.0)


def test_conditional_matrix_preserves_rows_and_monotonicity():
    """A threshold shift cannot invert the rating ordering; a multiplier could."""
    base = quarterly_base()
    for z in (-2.0, -0.5, 0.0, 0.5, 2.0):
        m = conditional_matrix(base, z, 0.15)
        assert np.allclose(m.sum(axis=1), 1.0)
        assert (m >= 0).all()
        # default probability is monotone in the grade at every factor value
        pd = m[:D, D]
        assert np.all(np.diff(pd) >= -1e-12), (z, pd)


def test_worse_factor_raises_default_probability_for_every_grade():
    base = quarterly_base()
    lo, hi = conditional_matrix(base, -1.0, 0.15), conditional_matrix(base, 1.0, 0.15)
    # AAA's default probability is no longer zero: the published annual entry is
    # 0.00%, an absence of observations rather than of risk, so the base floors
    # it at the regulatory minimum. It therefore responds to the factor like any
    # other grade.
    assert hi[0, D] > lo[0, D] > 0.0
    assert np.all(hi[:D, D] > lo[:D, D])


def test_holdout_mix_is_shifted_toward_speculative_grade():
    """Without a shifted mix an aggregate macro fit scores well with no migration
    model, which would make the rating structure decoration."""
    h = holdout_mix(0.3)
    assert h.sum() == pytest.approx(1.0)
    cum_base = np.cumsum(BASE_MIX)
    cum_h = np.cumsum(h)
    # the shifted cohort is stochastically worse: its CDF lies below at every grade
    assert np.all(cum_h[:-1] <= cum_base[:-1] + 1e-12)
    assert ks_distance(h, BASE_MIX) > 0.02


def test_annual_counts_are_whole_cohorts_and_only_public_files_leak(bundle):
    rows = bundle["annual_counts"]
    years = {r["year"] for r in rows}
    assert len(rows) == len(years) * len(LIVE)
    files = public_files(bundle)
    assert set(files) == {"data/transitions.csv", "data/macro_history.csv",
                          "data/scenario.csv", "data/portfolio.csv",
                          "data/policy.json"}
    blob = "\n".join(files.values())
    for key in ("driver_up", "driver_down", "weight_up", "rho", "mix_tilt"):
        assert key not in blob
    for value in (bundle["dgp"]["driver_up"], bundle["dgp"]["driver_down"]):
        # driver NAMES are column headers, so only the drawn numbers must not leak
        assert isinstance(value, str)
    assert f"{bundle['dgp']['rho']:.6f}" not in blob
    policy = json.loads(files["data/policy.json"])
    assert policy["checkpoints"] == list(CHECKPOINTS)
    assert policy["scenarios"] == list(SCEN)


def test_history_and_scenario_ship_the_same_nine_series(bundle):
    """The prompt promises nine macro series, so exactly nine must arrive.

    The history rows are adopted from the CCAR generator, which appends a tenth
    column holding the default rate of ITS portfolio. Passed through, it named a
    series `default_rate` that this portfolio did not produce: eight times too
    large, and correlated 0.03 to 0.78 with the shipped counts depending on the
    instance, so an agent regressing on it chased noise or found a shortcut by
    luck of the draw. Both files now carry the same nine.
    """
    files = public_files(bundle)
    header = {name: files[f"data/{name}.csv"].splitlines()[0].split(",")
              for name in ("macro_history", "scenario")}
    assert header["scenario"] == ["scenario", *header["macro_history"]]
    assert header["macro_history"] == ["quarter", *MACRO_COLUMNS]
    assert len(MACRO_COLUMNS) == 9
    assert "default_rate" not in files["data/macro_history.csv"]
    assert all("default_rate" not in row for row in bundle["history_rows"])


def test_truth_distributions_are_cohort_shares_including_default(bundle):
    for name in SCEN:
        dist = bundle["truth"]["scenarios"][name]["rating_distribution"]
        for q in CHECKPOINTS:
            d = dist[str(q)]
            assert set(d) == set(ORDER)
            assert sum(d.values()) == pytest.approx(1.0, abs=1e-9)
        early = dist[str(min(CHECKPOINTS))]
        late = dist[str(max(CHECKPOINTS))]
        # default is absorbing, so its share cannot fall between checkpoints
        assert late["D"] >= early["D"]


def test_default_is_visible_to_ks_only_in_the_cohort_view():
    """The measurement behind the scored object.

    Two submissions with identical live-grade shares but different default rates
    are indistinguishable once the seven live grades are renormalised to one,
    because the cumulative distribution then reaches one on both sides. With
    default as a terminal bin the error appears directly, equal to the default
    share that was omitted.
    """
    truth = np.array([0.002, 0.0134, 0.1063, 0.3153, 0.2617, 0.1865, 0.0385, 0.0763])
    zero_default = np.concatenate([truth[:7] / truth[:7].sum(), [0.0]])

    def live(v):
        return v[:7] / v[:7].sum()

    assert ks_distance(live(zero_default), live(truth)) == pytest.approx(0.0, abs=1e-12)
    assert ks_distance(zero_default, truth) == pytest.approx(0.0763, abs=1e-6)


def _oracle_csv(truth):
    rows = ["scenario,quarter,state,share"]
    for name in truth["scenario_names"]:
        dist = truth["scenarios"][name]["rating_distribution"]
        for q in CHECKPOINTS:
            for s in ORDER:
                rows.append(f"{name},{q},{s},{dist[str(q)][s]}")
    return "\n".join(rows) + "\n"


def test_oracle_scores_exactly_zero_and_missing_scores_one(bundle):
    """The degenerate answer is 1.0 by construction, so the scale reads directly."""
    truth = bundle["truth"]
    perfect = score_predictions(truth, _oracle_csv(truth))
    assert perfect["score"] == pytest.approx(0.0, abs=1e-12)
    assert perfect["completion"] == 1.0
    missing = score_predictions(truth, None)
    assert missing["completion"] == 0.0
    assert missing["score"] == pytest.approx(1.0)


def test_each_component_is_a_fraction_of_the_degenerate(bundle):
    """Equal weighting comes from the normalisation, not from chosen constants."""
    truth = bundle["truth"]
    perfect = score_predictions(truth, _oracle_csv(truth))
    keys = [f"{c}_{n}_q{q}" for n in SCEN for c in ("ks", "default") for q in (4, 9)]
    assert len(keys) == 12
    for k in keys:
        assert perfect[f"{k}_norm"] == pytest.approx(0.0, abs=1e-9)
    missing = score_predictions(truth, None)
    for k in keys:
        assert missing[f"{k}_norm"] == pytest.approx(1.0)


def test_shape_and_default_are_scored_independently(bundle):
    """Getting the grades right while claiming no defaults must not score well."""
    truth = bundle["truth"]
    rows = ["scenario,quarter,state,share"]
    for name in SCEN:
        dist = truth["scenarios"][name]["rating_distribution"]
        for q in CHECKPOINTS:
            d = dist[str(q)]
            live_total = sum(d[s] for s in ORDER[:-1])
            for s in ORDER:
                share = 0.0 if s == "D" else d[s] / live_total
                rows.append(f"{name},{q},{s},{share}")
    r = score_predictions(truth, "\n".join(rows) + "\n")
    for name in SCEN:
        # the live-grade shape is exact, so both KS components vanish
        assert r[f"ks_{name}_q4_norm"] == pytest.approx(0.0, abs=1e-9)
        assert r[f"ks_{name}_q9_norm"] == pytest.approx(0.0, abs=1e-9)
        # but both default components are maximally wrong
        assert r[f"default_{name}_q4_norm"] == pytest.approx(1.0, rel=1e-6)
        assert r[f"default_{name}_q9_norm"] == pytest.approx(1.0, rel=1e-6)
        assert r[f"score_{name}"] == pytest.approx(0.5, abs=1e-6)
    # twelve components, half of them exact, so the composite pins at 0.5
    assert r["score"] == pytest.approx(0.5, abs=1e-6)


HEAD = "scenario,quarter,state,share\n"


@pytest.mark.parametrize("text", [
    HEAD + "adverse,4,AAA,0.5\n",                            # incomplete states
    HEAD + "adverse,4,AAA,-0.1\n" + "\n".join(
        f"adverse,4,{s},0.2" for s in ORDER[1:]),             # negative share
    HEAD + "\n".join(f"adverse,4,{s},50" for s in ORDER),     # percent, not share
    HEAD + "\n".join(f"adverse,4,{s},0.125" for s in ORDER) * 2,  # duplicates
    "quarter,state,share\n" + "\n".join(                     # no scenario column
        f"4,{s},0.125" for s in ORDER),
])
def test_malformed_submissions_cannot_gain_credit(bundle, text):
    r = score_predictions(bundle["truth"], text)
    assert r["completion"] == 0.0
    assert r["score"] == pytest.approx(1.0)


def test_reference_beats_the_degenerate_by_a_wide_margin():
    """The anchor that makes the column readable.

    Measured at 0.309 against the degenerate's 1.000 over these six instances,
    a separation of 3.2x, at the task's shipped n_years=20. Over twelve it is
    0.285 and 3.5x. The bar is deliberately looser than the measurement so
    ordinary generator drift does not fail it, but a change that collapses the
    separation will.

    Six seeds rather than the module's three, because seed 3 is the worst of the
    first eight and a three-seed sample containing it reads high. Each instance
    now carries all three scenarios, so six seeds is eighteen projections.

    Twenty years is where the shrinkage earns its place. Unshrunk, the reference
    loses to the degenerate on five of twenty-four draws, reaching 1.48. See
    `project_factor` for why the fix is shrinkage and not a bound on the
    projection.
    """
    ref, deg = [], []
    for seed in (1, 2, 3, 4, 5, 6):
        b = generate(seed, n_years=20)
        f = public_files(b)
        ref.append(score_predictions(b["truth"], predict(f, "onefactor")[0])["score"])
        deg.append(score_predictions(b["truth"], predict(f, "no_migration")[0])["score"])
    assert np.mean(ref) < 0.5 * np.mean(deg)
    assert np.mean(ref) > 0.0          # the reference is not the oracle


def test_reference_can_project_beyond_its_estimation_sample():
    """A stress model has to answer a scenario worse than anything it has seen.

    This is the opposite of a sanity clip. Bounding the projection to the range
    of the estimated annual factors scores slightly better and is wrong, because
    it makes the model structurally unable to price the severely adverse
    scenario, which is the only question it exists to answer.
    """
    from pereval.tasks.migration.baselines import project_factor

    rng = np.random.default_rng(0)
    n = 20
    x = rng.standard_normal((n, 6))
    X = np.column_stack([np.ones(n), x])
    zhat = x @ np.array([1.0, 0.5, -0.3, 0.2, -0.4, 0.1]) + rng.standard_normal(n)
    # a scenario far past anything in the estimation window
    Xs = np.column_stack([np.ones(9), np.tile([6.0, 6.0, 6.0, -6.0, -6.0, -6.0], (9, 1))])
    assert project_factor(X, Xs, zhat).max() > zhat.max()


def test_reference_response_to_extreme_macros_is_monotone_and_finite():
    """The review question about extreme inputs, which is behaviour not refusal.

    Push the scenario to three times its distance from the historical mean and
    the projected factor must rise, stay finite, and not reverse sign.
    """
    from pereval.tasks.migration.baselines import factor_response_diagnostics

    rng = np.random.default_rng(0)
    for n in (12, 20, 40):
        x = rng.standard_normal((n, 6))
        X = np.column_stack([np.ones(n), x])
        Xs = np.column_stack([np.ones(9), rng.standard_normal((9, 6)) + 1.5])
        zhat = x @ np.array([1.0, 0.5, -0.3, 0.2, -0.4, 0.1]) + rng.standard_normal(n)
        d = factor_response_diagnostics(X, Xs, zhat)
        assert d["monotone_in_severity"]
        assert d["finite"]


def test_reference_shrinks_harder_on_a_shorter_history():
    """The penalty is a rule, so it adapts without anyone retuning it."""
    from pereval.tasks.migration.baselines import DF_DIVISOR, _lambda_for_df

    rng = np.random.default_rng(1)
    lams = []
    for n in (20, 40):
        X = np.column_stack([np.ones(n), rng.standard_normal((n, 6))])
        lams.append(_lambda_for_df(X, 1.0 + n / DF_DIVISOR))
    assert lams[0] > lams[1] > 0.0


def test_no_migration_baseline_reproduces_the_anchor_exactly():
    """The anchor must be reachable from the integer counts the agent can see."""
    b = generate(2, n_years=20)
    r = score_predictions(b["truth"], predict(public_files(b), "no_migration")[0])
    assert r["score"] == pytest.approx(1.0, rel=1e-6)
    assert r["completion"] == 1.0


def test_annual_matrix_from_a_moving_factor_resists_a_stochastic_root():
    """The trap the task turns on, measured rather than asserted.

    A constant factor gives an annual matrix that is a fourth power, whose
    principal fourth root is clean. A factor that moves within the year gives a
    product of four different matrices, whose principal root is not stochastic.
    """
    base = quarterly_base()
    constant = np.linalg.matrix_power(conditional_matrix(base, 0.5, 0.15), 4)
    assert np.real(fractional_matrix_power(constant, 0.25)).min() > -1e-10

    moving = np.eye(D + 1)
    for z in (0.5, 1.0, 1.5, 2.0):
        moving = moving @ conditional_matrix(base, z, 0.15)
    # Flooring the base's four exact zeros makes it marginally more embeddable,
    # so this threshold is looser than it was: the exact-arithmetic pathology is
    # now around -3e-08. It is immaterial, because finite-portfolio sampling
    # contributes about -7e-03, five orders of magnitude more, as the next test
    # measures.
    assert np.real(fractional_matrix_power(moving, 0.25)).min() < -1e-9


def test_finite_portfolio_sampling_dominates_the_non_embeddability():
    """Why the trap is robust: the portfolio, not the macro path, drives it."""
    rng = np.random.default_rng(0)
    base = quarterly_base()
    moving = np.eye(D + 1)
    for z in (0.5, 1.0, 1.5, 2.0):
        moving = moving @ conditional_matrix(base, z, 0.15)
    start = np.round(BASE_MIX * N_OBLIGORS).astype(int)
    emp = np.zeros((D + 1, D + 1))
    for i in range(D):
        emp[i] = rng.multinomial(int(start[i]), moving[i])
    emp[:D] /= np.maximum(emp[:D].sum(axis=1, keepdims=True), 1)
    emp[D, D] = 1.0
    sampled_min = np.real(fractional_matrix_power(emp, 0.25)).min()
    exact_min = np.real(fractional_matrix_power(moving, 0.25)).min()
    assert sampled_min < exact_min      # sampling makes it worse, not better
    assert sampled_min < -1e-4


def test_expected_distributions_match_a_direct_propagation(bundle):
    base = quarterly_base()
    dgp = bundle["dgp"]
    z = bundle["truth"]["scenarios"]["adverse"]["z_scenario"]
    mix = np.array([bundle["holdout_mix"][r] for r in LIVE])
    got = expected_distributions(base, dgp, z, mix, CHECKPOINTS)
    v = np.concatenate([mix, [0.0]])
    for t in range(max(CHECKPOINTS)):
        v = v @ conditional_matrix(base, float(z[t]), dgp["rho"])
        if t + 1 in CHECKPOINTS:
            assert np.allclose([got[t + 1][s] for s in ORDER], v)

def test_matrix_diagnostics_are_clean_for_the_reference():
    """The competent reference produces admissible matrices, so a nonzero count
    on an agent run means the agent's matrices, not the harness.

    This is the test that caught the reference asserting AAA riskier than AA,
    once flooring made those two grades equal in truth and left their estimates
    to sampling noise. The reference now imposes the ordering.
    """
    import numpy as np

    from pereval.scorers.migration import (
        matrix_diagnostics,
        parse_predictions,
    )

    b = generate(1, n_years=20)
    f = public_files(b)
    preds, mats, _ = predict(f, "onefactor")
    start = np.array([b["truth"]["start_mix"].get(s, 0.0) for s in ORDER], float)
    cps = list(CHECKPOINTS)
    d = matrix_diagnostics(mats, start, parse_predictions(preds), cps)
    assert d["matrix_provided"] == 1.0
    assert d["matrix_rows_off_one"] == 0.0
    assert d["matrix_negative_cells"] == 0.0
    assert d["matrix_zero_cells"] == 0.0
    assert d["matrix_default_monotonicity_violations"] == 0.0
    # the documented model reproduces the reported projection
    assert d["matrix_submission_gap"] < 1e-9


def test_matrix_diagnostics_detect_each_pathology():
    """An inadmissible matrix is measured, not rejected, and never changes `score`."""
    import numpy as np

    from pereval.scorers.migration import (
        matrix_diagnostics,
        parse_matrices,
        score_predictions,
    )

    b = generate(1, n_years=20)
    preds, mats, _ = predict(public_files(b), "onefactor")
    rows = mats.splitlines()
    header, body = rows[0], rows[1:]
    # break the first live row: negative mass, rows off one, and a default
    # probability that improves as credit quality worsens
    broken = header + "\n" + "\n".join(
        ["baseline,1,AAA," + ",".join(
            ["0.5", "0.6", "-0.2", "0.0", "0.0", "0.0", "0.0", "0.9"]),
         "baseline,1,AA," + ",".join(["0.0"] * 7 + ["0.1"])] + body[2:])
    start = np.array([b["truth"]["start_mix"].get(s, 0.0) for s in ORDER], float)
    cps = list(CHECKPOINTS)
    d = matrix_diagnostics(broken, start, {}, cps)
    assert parse_matrices(broken)          # parsed, not rejected
    assert d["matrix_negative_cells"] >= 1
    assert d["matrix_most_negative"] < 0
    assert d["matrix_rows_off_one"] >= 1
    assert d["matrix_zero_cells"] >= 1
    # AAA default 0.9 against AA default 0.1 is the ordering inversion
    assert d["matrix_default_monotonicity_violations"] >= 1
    # and none of it touched the headline score
    clean = score_predictions(b["truth"], preds)
    assert "matrix_negative_cells" not in clean
    assert clean["score"] == pytest.approx(
        score_predictions(b["truth"], preds)["score"])


def test_missing_matrices_are_recorded_without_affecting_score():
    import numpy as np

    from pereval.scorers.migration import matrix_diagnostics

    b = generate(1, n_years=20)
    start = np.array([b["truth"]["start_mix"].get(s, 0.0) for s in ORDER], float)
    d = matrix_diagnostics(None, start, {}, [4, 9])
    assert d == {"matrix_provided": 0.0}


def test_admissibility_is_immaterial_to_accuracy_so_it_breaks_ties_only():
    """Pins the measurement behind keeping admissibility out of `score`.

    Degrading only the reference's matrices, leaving exact zeros and letting the
    default ordering invert, changes the score by a fraction of a percent. If a future change makes admissibility material, this
    test fails and the tie-breaker treatment has to be revisited rather than
    silently kept.
    """
    import numpy as np
    from scipy.linalg import fractional_matrix_power

    from pereval.scorers.migration import (
        matrix_diagnostics,
        parse_predictions,
        score_predictions,
    )
    from pereval.tasks.migration import baselines as B

    def raw_base(mats):
        tot = sum(mats.values())
        ann = np.zeros((D + 1, D + 1))
        ann[:D] = tot / np.maximum(tot.sum(axis=1, keepdims=True), 1.0)
        ann[D, D] = 1.0
        q = np.clip(np.real(fractional_matrix_power(ann, 0.25)), 0.0, None)
        q[D, :] = 0.0
        q[D, D] = 1.0
        q[:D] /= q[:D].sum(axis=1, keepdims=True)
        return q

    b = generate(1, n_years=20)
    f, t = public_files(b), b["truth"]
    start = np.array([t["start_mix"].get(s, 0.0) for s in ORDER], float)
    cps = list(CHECKPOINTS)

    good_preds, good_mats, _ = predict(f, "onefactor")
    original = B.pooled_quarterly_base
    B.pooled_quarterly_base = raw_base
    try:
        bad_preds, bad_mats, _ = predict(f, "onefactor")
    finally:
        B.pooled_quarterly_base = original

    good = matrix_diagnostics(good_mats, start, parse_predictions(good_preds), cps)
    bad = matrix_diagnostics(bad_mats, start, parse_predictions(bad_preds), cps)
    assert good["matrix_admissible"] == 1.0
    assert bad["matrix_admissible"] == 0.0
    assert bad["matrix_zero_cells"] > 0

    s_good = score_predictions(t, good_preds)["score"]
    s_bad = score_predictions(t, bad_preds)["score"]
    # Orthogonal: wholly different admissibility, indistinguishable accuracy.
    # Measured at 0.15% of the score on this instance, 0.03% averaged over
    # twelve and 0.18% at worst over those twelve. The bound is 5%,
    # which is still far inside the factor-of-a-few resolution this suite
    # claims, so the test fails only if admissibility becomes genuinely
    # material rather than on ordinary instance variation.
    assert abs(s_bad - s_good) < 0.05 * s_good


def test_row_sums_are_a_hard_failure_but_negatives_are_only_flagged():
    """The tiers, and the measurement that justifies separating them.

    Rows not summing to one make the matrix unable to have produced the
    projection, and the breach compounds: scaling every row to 1.2 drives the
    submission gap from 0.0000 to above 2. A single small negative leaves mass
    conserved and moves the gap by 1e-4, so clipping it is defensible and the
    defect is flagged rather than failed.
    """
    import numpy as np

    from pereval.scorers.migration import matrix_diagnostics, parse_predictions

    b = generate(1, n_years=20)
    f, t = public_files(b), b["truth"]
    start = np.array([t["start_mix"].get(s, 0.0) for s in ORDER], float)
    cps = list(CHECKPOINTS)
    preds, mats, _ = predict(f, "onefactor")
    head, *body = mats.splitlines()

    good = matrix_diagnostics(mats, start, parse_predictions(preds), cps)
    assert good["matrix_rows_valid"] == 1.0
    assert good["matrix_nonnegative"] == 1.0
    assert good["matrix_admissible"] == 1.0

    def scaled(line, k):
        parts = line.split(",")
        return ",".join(parts[:3] + [repr(float(x) * k) for x in parts[3:]])

    off = matrix_diagnostics(head + "\n" + "\n".join(scaled(x, 1.2) for x in body),
                             start, parse_predictions(preds), cps)
    assert off["matrix_rows_valid"] == 0.0
    assert off["matrix_row_sum_error"] == pytest.approx(0.2, abs=0.01)
    assert off["matrix_submission_gap"] > 1.0      # mass loss compounds

    parts = body[0].split(",")
    parts[3] = repr(float(parts[3]) + 0.05)
    parts[10] = repr(float(parts[10]) - 0.05)
    neg = matrix_diagnostics(head + "\n" + "\n".join([",".join(parts)] + body[1:]),
                             start, parse_predictions(preds), cps)
    assert neg["matrix_rows_valid"] == 1.0         # mass still conserved
    assert neg["matrix_nonnegative"] == 0.0
    assert neg["matrix_admissible"] == 0.0
    assert neg["matrix_submission_gap"] < 0.01     # and numerically near-harmless


def test_backtest_diagnostics_detect_insufficient_macro_sensitivity():
    """The one-sided check, measured against a sensitivity sweep.

    Scaling the reference's macro response down must drive the stress-year fit
    ratio down monotonically, because that is the whole purpose: a model too
    insensitive to macros understates losses in the bad years and so
    under-reserves. Nothing here is two-sided; a ratio above one is conservative
    rather than wrong.
    """
    import csv as _csv
    import io as _io


    from pereval.scorers.migration import fit_diagnostics
    from pereval.tasks.migration import baselines as _B

    b = generate(1, n_years=20)
    f = public_files(b)
    mats = _B._annual_matrices(f["data/transitions.csv"])
    base = _B.pooled_quarterly_base(mats)
    years = sorted(mats)
    zhat = np.array([_B.factor_mle(mats[y], base) for y in years])
    X, _ = _B._macro_features(_B._rows(f["data/macro_history.csv"]),
                              _B._rows(f["data/scenario.csv"]), len(years))
    lam = _B._lambda_for_df(X, 1.0 + X.shape[0] / _B.DF_DIVISOR)
    zfit = X @ _B._ridge(X, zhat, lam)
    level = zfit.mean()

    ratios = []
    for k in (0.0, 0.5, 1.0):
        rates = _B._fitted_annual_rates(mats, base, level + k * (zfit - level))
        buf = _io.StringIO()
        w = _csv.DictWriter(buf, fieldnames=["year", "default_rate"])
        w.writeheader()
        for y, v in zip(years, rates):
            w.writerow({"year": y, "default_rate": v})
        d = fit_diagnostics(buf.getvalue(), b["truth"]["observed_annual_default_rate"])
        ratios.append(d["fit_peak_prominence"])
    # retargeted from fit_stress_mean_ratio, which was removed: a statistic the
    # shipped reference cannot clear reports the bias-variance trade every
    # estimator on twenty years has to make as though it were a defect. Peak
    # prominence is monotone in macro response over the same sweep and spans
    # 0.09 to 1.17 against the removed ratio's 0.26 to 1.07.
    assert ratios[0] < ratios[1] < ratios[2]


def test_shipped_reference_is_flagged_for_damped_macro_response():
    """The anchor fails its own stress check, and that is recorded not hidden.

    The shrinkage that stops the reference blowing out on the projection also
    damps its macro response, so it under-fits the stressed years by about a
    third: 0.695 on this instance and 0.637 averaged over twelve. An agent that
    beats the reference's 0.285 composite while keeping this ratio near one is
    doing something the score alone cannot see.
    """
    from pereval.tasks.migration.baselines import backtest_diagnostics

    d = backtest_diagnostics(public_files(generate(1, n_years=20)))
    assert 0.5 < d["stress_mean_ratio"] < 0.85
    assert d["factor_swing_retained"] < 0.9
    # the band still clears the worst observed year for a correctly specified fit
    assert d["peak_over_bound"] < 1.0


def test_degenerate_floors_every_one_sided_statistic():
    """No migration means no defaults, so every stress ratio must read zero."""
    from pereval.scorers.migration import (
        fit_diagnostics, parse_predictions, stress_diagnostics,
    )

    b = generate(2, n_years=20)
    f, t = public_files(b), b["truth"]
    preds, mats, back = predict(f, "no_migration")
    start = np.array([t["start_mix"].get(s, 0.0) for s in ORDER], float)
    s = stress_diagnostics(mats, start, parse_predictions(preds), t)
    d = fit_diagnostics(back, t["observed_annual_default_rate"])
    assert s["stress_mean_ratio"] == 0.0
    assert s["stress_peak_ratio"] == 0.0
    assert d["fit_peak_ratio"] == 0.0
    assert "fit_peak_lag" not in d          # a flat series has no peak


def test_true_loss_path_reconciles_with_the_scored_checkpoint():
    """The quarterly increments must sum to the cohort default share at quarter 9."""
    t = generate(1, n_years=20)["truth"]
    for name in SCEN:
        ts = t["scenarios"][name]
        assert sum(ts["default_increments"]) == pytest.approx(
            ts["rating_distribution"]["9"]["D"], abs=1e-9)
    # one history, so one observed series shared by all three
    assert len(t["observed_annual_default_rate"]) == 20


def test_top_of_scale_is_estimated_and_leaves_the_grades_ordered():
    """The capital floor used to pin AAA and AA to one number. It is gone.

    A 0.03% annual PD floor annualises to 7.5e-05 a quarter, which bound both of
    the top two grades and made them exactly equal in the generator's own truth,
    overwriting AA's observed value upward by about a factor of two. Capital
    floors are long-run through-the-cycle figures; these are point-in-time
    macro-conditional probabilities, so no floor belongs here at all.
    """
    from pereval.tasks.migration.generator import (
        TOP_OF_SCALE_QUARTERLY, quarterly_base,
    )
    from pereval.tasks.migration.reference import PD_FLOORS, top_of_scale_annual

    col = quarterly_base()[:len(LIVE), D]
    assert np.all(np.diff(col) > 0.0), "the default column must be strictly ordered"
    assert col[0] > 0.0, "AAA must carry positive risk, Cromwell's rule"
    assert col[0] == pytest.approx(TOP_OF_SCALE_QUARTERLY)
    # and it sits below the floors that used to be imposed, which is the point
    for floor in PD_FLOORS.values():
        assert top_of_scale_annual() < floor
    # AA keeps the value its own observed defaults imply, not a floored one
    assert col[1] > col[0]


def test_peak_prominence_beats_the_lag_and_suppresses_it_when_flat():
    """A flat fitted series has no peak, so its argmax is noise.

    Measured over twenty-four instances at the shipped fit, the one instance
    with prominence 0.17 reported a sixteen year lag while the other
    twenty-three, all above 0.39, reported exactly zero. So the lag is withheld
    below the prominence floor rather than published as a finding.
    """
    from pereval.scorers.migration import PROMINENCE_FLOOR, fit_diagnostics
    from pereval.tasks.migration.baselines import _backtest_csv

    obs = [0.004, 0.005, 0.004, 0.030, 0.012, 0.005, 0.004, 0.006]
    flat = _backtest_csv(range(2000, 2008), [0.007] * 8, ["baseline"])
    d = fit_diagnostics(flat, obs)
    assert d["fit_peak_prominence"] == pytest.approx(0.0)
    assert "fit_peak_lag" not in d

    # a series that tracks the observed peak is prominent and correctly timed
    sharp = _backtest_csv(range(2000, 2008), obs, ["baseline"])
    d = fit_diagnostics(sharp, obs)
    assert d["fit_peak_prominence"] == pytest.approx(1.0)
    assert d["fit_peak_prominence"] >= PROMINENCE_FLOOR
    assert d["fit_peak_lag"] == 0.0


def test_every_reported_key_survives_aggregation():
    """A key left out of one sample's dict fails the eval after all the scoring.

    Inspect averages a keyed metric by pulling that key from every sample's
    score value, raising if it is absent and skipping it if it is NaN. Every
    diagnostic here is conditional on something, so the scorer fills what does
    not apply with NaN. This pins that contract, which was found the hard way:
    one submission without `matrices.csv` failed a whole run at aggregation.
    """
    import math

    from pereval.scorers.migration import REPORTED_KEYS, score_value

    b = generate(1, n_years=20)
    t = b["truth"]
    preds, mats, back = predict(public_files(b), "onefactor")
    cases = {
        "nothing submitted": (None, None, None),
        "predictions only": (preds, None, None),   # the shape that crashed a run
        "no backtest": (preds, mats, None),
        "everything": (preds, mats, back),
    }
    for label, (text, m, bk) in cases.items():
        v = score_value(t, text, m, bk)
        missing = [k for k in REPORTED_KEYS if k not in v]
        assert not missing, f"{label}: absent at aggregation: {missing}"
        assert not math.isnan(v["score"]), f"{label}: the score itself is never NaN"


# --- one history, three scenarios -------------------------------------------

def test_one_history_is_shared_by_every_scenario():
    """The property the task's shape exists for.

    A bank fits one model to one history and runs it under each supervisory
    scenario. So everything the agent estimates on has to be identical across
    the three, and only the future path may differ. Generating with one scenario
    or another must therefore leave the counts, the macro history and the
    holdout cohort untouched.
    """
    a = generate(1, n_years=20, scenarios=("baseline",))
    b = generate(1, n_years=20, scenarios=("severe",))
    assert a["annual_counts"] == b["annual_counts"]
    assert a["history_rows"] == b["history_rows"]
    assert a["holdout_counts"] == b["holdout_counts"]
    assert (a["truth"]["observed_annual_default_rate"]
            == b["truth"]["observed_annual_default_rate"])
    # and the future does differ, otherwise there would be nothing to compare
    assert a["scenario_rows"] != b["scenario_rows"]

    full = generate(1, n_years=20)
    rows = {name: [r for r in full["scenario_rows"] if r["scenario"] == name]
            for name in SCEN}
    assert all(len(v) == 9 for v in rows.values())
    assert rows["baseline"] != rows["adverse"] != rows["severe"]
    # the single history is the one the single-scenario bundles carry
    assert full["history_rows"] == a["history_rows"]
    assert full["annual_counts"] == a["annual_counts"]


def test_severity_is_ordered_within_an_instance():
    """Baseline, adverse and severe must get worse in that order, every instance.

    The severity bands the CCAR generator draws from are disjoint, so this holds
    by construction rather than by luck, and the test is here because the hump
    reshaping draws its own peak and recovery per scenario and could in principle
    undo the ordering.
    """
    for seed in (1, 2, 3, 4, 5, 6):
        t = generate(seed, n_years=20)["truth"]["scenarios"]
        pdr = [t[name]["portfolio_default_rate"] for name in SCEN]
        assert pdr[0] < pdr[1] < pdr[2], f"seed {seed} out of order: {pdr}"
        # and the factor itself is pushed further out of sample each time
        peak = [max(t[name]["z_scenario"]) for name in SCEN]
        assert peak[0] < peak[1] < peak[2], f"seed {seed} factor order: {peak}"


def test_the_scenario_leak_through_the_equity_siblings_is_closed():
    """One history is not constructible on the shipped CCAR sibling setting.

    sp500 and djia are built by standardising NASDAQ returns, and on the default
    setting that standardisation runs over the whole path, so the stress
    window's own volatility reaches back into the historical values of two
    published columns. Holding the seed and changing only the scenario moved 49
    of 80 history rows. Migration therefore asks for pre-stress standardisation,
    and this pins both halves: the leak exists, and the setting closes it.
    """
    from pereval.tasks.ccar.generator import _simulate

    leaky = [_simulate(1835504127, 80, 50, None, s)["train_rows"]
             for s in ("baseline", "severe")]
    assert leaky[0] != leaky[1], "the leak this setting exists for is gone"
    differing = [i for i, (x, y) in enumerate(zip(*leaky)) if x != y]
    assert len(differing) > 10
    # only the siblings move, which is why it went unnoticed
    changed = {k for i in differing for k in leaky[0][i]
               if leaky[0][i][k] != leaky[1][i][k]}
    assert changed == {"sp500", "djia"}

    clean = [_simulate(1835504127, 80, 50, None, s, sibling_ref="pre_stress")
             ["train_rows"] for s in ("baseline", "severe")]
    assert clean[0] == clean[1]


def test_rating_monotonicity_is_checked_inside_each_scenario():
    """PD must rise as the grade worsens, within a scenario quarter.

    The check cannot pool grades across scenarios: a severe quarter's AAA can
    carry more default risk than a baseline quarter's CCC/C, and that is correct
    rather than a violation. So a submission that is monotone inside every
    matrix reads zero even when its levels overlap across scenarios, and an
    inversion inside one matrix is counted once.
    """
    from pereval.scorers.migration import matrix_diagnostics

    cols = ["scenario", "quarter", "from_rating"] + [
        f"to_{s.replace('/', '_')}" for s in ORDER]

    def rows(scen, pds):
        out = []
        for grade, pd in zip(LIVE, pds):
            cells = [0.0] * len(ORDER)
            cells[LIVE.index(grade)] = 1.0 - pd
            cells[-1] = pd
            out.append(",".join([scen, "1", grade] + [repr(c) for c in cells]))
        return out

    # severe sits entirely above baseline, and each is internally ordered
    ordered = [0.001, 0.002, 0.004, 0.008, 0.02, 0.06, 0.2]
    severe = [0.3 + x for x in ordered]
    text = ",".join(cols) + "\n" + "\n".join(
        rows("baseline", ordered) + rows("severe", severe))
    start = np.full(len(ORDER), 1.0 / len(ORDER))
    d = matrix_diagnostics(text, start, {}, list(CHECKPOINTS))
    assert d["matrix_default_monotonicity_violations"] == 0.0
    assert d["matrix_monotonicity_checks"] == 2 * (len(LIVE) - 1)

    # one inversion inside the baseline matrix, and only one
    swapped = list(ordered)
    swapped[4], swapped[5] = swapped[5], swapped[4]
    text = ",".join(cols) + "\n" + "\n".join(
        rows("baseline", swapped) + rows("severe", severe))
    d = matrix_diagnostics(text, start, {}, list(CHECKPOINTS))
    assert d["matrix_default_monotonicity_violations"] == 1.0


def _matrices_text(by_scen: dict[str, dict[int, np.ndarray]]) -> str:
    """A matrices.csv for a dict of {scenario: {quarter: 8x8}}."""
    cols = ["scenario", "quarter", "from_rating"] + [
        f"to_{s.replace('/', '_')}" for s in ORDER]
    out = [",".join(cols)]
    for scen in sorted(by_scen):
        for q in sorted(by_scen[scen]):
            for i, grade in enumerate(LIVE):
                out.append(",".join([scen, str(q), grade]
                                    + [repr(float(x)) for x in by_scen[scen][q][i]]))
    return "\n".join(out) + "\n"


def _oracle_matrices(bundle: dict) -> dict[str, dict[int, np.ndarray]]:
    """The exact conditional law, scenario by scenario, from truth."""
    t = bundle["truth"]
    base = quarterly_base()
    return {n: {q + 1: conditional_matrix(base, float(z), t["rho"])
                for q, z in enumerate(t["scenarios"][n]["z_scenario"])}
            for n in t["scenario_names"]}


def _thin_far(m: np.ndarray, keep: float) -> np.ndarray:
    """Keep `keep` of the three-or-worse notch mass, fold the rest in at two.

    Rows still sum to one and the default column is untouched, so this isolates
    the far corner from every other property the scorer looks at.
    """
    out = m.copy()
    for i in range(D - 3):
        far = out[i, i + 3:D].copy()
        out[i, i + 3:D] = far * keep
        out[i, i + 2] += far.sum() * (1.0 - keep)
    return out


def _freeze_body(m: np.ndarray, base: np.ndarray) -> np.ndarray:
    """Unconditional migration shape, with only the default column conditioned.

    What a model does when it fits a PD by rating and leaves the rest of the
    matrix at its long-run average. One real submission recovered from an agent
    transcript had exactly this structure: its live block varied by 0.0001
    relative across the nine quarters of a severe path while its default column
    moved by a factor of five.
    """
    out = base.copy()
    out[D, D] = 1.0
    for i in range(D):
        out[i, D] = m[i, D]
        live = base[i, :D].copy()
        live *= (1.0 - m[i, D]) / live.sum()
        out[i, :D] = live
    return out


def test_the_far_downgrade_corner_is_measured_exactly():
    """`matrix_down3_ratio` reads back the fraction of far mass retained.

    The point of the diagnostic is that it is a measurement, not a proxy: a
    submission that keeps a quarter of its three-notch-or-worse mass reads 0.25,
    and the adjacent-grade control stays at one so the distortion cannot be
    mistaken for a model that is uniformly too mild.
    """
    from pereval.scorers.migration import notch_diagnostics

    b = generate(1, n_years=20)
    start = np.array([b["truth"]["start_mix"].get(s, 0.0) for s in ORDER], float)
    orc = _oracle_matrices(b)

    for keep in (1.0, 0.5, 0.25, 0.0):
        mats = {n: {q: _thin_far(m, keep) for q, m in v.items()}
                for n, v in orc.items()}
        d = notch_diagnostics(_matrices_text(mats), start, b["truth"])
        assert d["matrix_down3_ratio"] == pytest.approx(keep, abs=1e-9)
        assert d["matrix_down3_shape"] == pytest.approx(keep, abs=1e-9)
        assert d["matrix_down1_ratio"] == pytest.approx(1.0, abs=1e-9)


def test_collapsing_the_far_corner_is_invisible_to_the_score():
    """Why the far corner needs a diagnostic of its own rather than a component.

    Abolishing every three-notch-or-worse downgrade, with the factor path and
    the default column exactly right, costs almost nothing in the twelve scored
    components. It has to stay below the reference composite by a wide margin,
    because that gap is the whole argument for reporting the shape separately.
    """
    from pereval.scorers.migration import score_value

    b = generate(1, n_years=20)
    t = b["truth"]
    start = np.array([t["start_mix"].get(s, 0.0) for s in ORDER], float)
    mix = start[:D] / start[:D].sum()
    orc = _oracle_matrices(b)
    cps = [int(q) for q in t["scenarios"][t["scenario_names"][0]]["rating_distribution"]]

    def submission(mats):
        rows = ["scenario,quarter,state,share"]
        for scen in sorted(mats):
            v = np.concatenate([mix, [0.0]])
            for q in sorted(mats[scen]):
                v = v @ mats[scen][q]
                if q in cps:
                    rows += [f"{scen},{q},{s},{float(x)!r}"
                             for s, x in zip(ORDER, v)]
        return "\n".join(rows) + "\n"

    flat = {n: {q: _thin_far(m, 0.0) for q, m in v.items()} for n, v in orc.items()}
    clean = score_value(t, submission(orc), _matrices_text(orc), None)
    thin = score_value(t, submission(flat), _matrices_text(flat), None)
    assert clean["score"] < 0.01
    assert thin["score"] < 0.05           # far below the reference's 0.285
    assert thin["matrix_down3_ratio"] == pytest.approx(0.0, abs=1e-9)


def test_a_frozen_migration_body_reads_zero_concordance():
    """The second diagnostic catches what the first cannot, and the reverse.

    A model that moves only its default column keeps the far corner's shape
    roughly intact, so the shape ratio does not convict it. Its downgrade mass,
    default excluded, does not respond to the factor at all, so concordance is
    exactly zero and the elasticity is flat. Folding multi-notch mass into the
    adjacent grade is the mirror image: total downgrade mass is conserved, so
    the response statistics are untouched while the far ratio reads zero.
    """
    from pereval.scorers.migration import notch_diagnostics

    b = generate(1, n_years=20)
    start = np.array([b["truth"]["start_mix"].get(s, 0.0) for s in ORDER], float)
    orc = _oracle_matrices(b)
    base = quarterly_base()

    d = notch_diagnostics(_matrices_text(orc), start, b["truth"])
    assert d["matrix_downgrade_concordance"] == 1.0
    assert d["matrix_downgrade_slope"] > 0.5
    assert d["matrix_downgrade_pairs"] > 300

    frozen = {n: {q: _freeze_body(m, base) for q, m in v.items()}
              for n, v in orc.items()}
    f = notch_diagnostics(_matrices_text(frozen), start, b["truth"])
    assert f["matrix_downgrade_concordance"] == 0.0
    assert abs(f["matrix_downgrade_slope"]) < 0.05
    assert f["matrix_downgrade_response"] == pytest.approx(1.0, abs=0.1)
    # and the far corner alone would have let it through
    assert f["matrix_down3_shape"] > 0.3

    folded = {n: {q: _thin_far(m, 0.0) for q, m in v.items()}
              for n, v in orc.items()}
    g = notch_diagnostics(_matrices_text(folded), start, b["truth"])
    assert g["matrix_downgrade_concordance"] == 1.0
    assert g["matrix_downgrade_slope"] == pytest.approx(
        d["matrix_downgrade_slope_oracle"], rel=1e-9)
    assert g["matrix_down3_ratio"] == 0.0


def test_the_reference_responds_to_the_macros_in_the_right_direction():
    """The anchor has to pass its own diagnostics, and it does, unevenly.

    Concordance is high but not one, because the reference's estimated factor
    orders the quarters slightly differently from the true one. The far corner
    comes out FATTER than the oracle's rather than thinner, since the base is
    pooled over twenty years that contain stressed ones. Both are recorded here
    so that a later change to the reference cannot quietly invert either sign.
    """
    from pereval.scorers.migration import notch_diagnostics

    for seed in SEEDS:
        b = generate(seed, n_years=20)
        start = np.array([b["truth"]["start_mix"].get(s, 0.0) for s in ORDER], float)
        d = notch_diagnostics(predict(public_files(b), "onefactor")[1],
                              start, b["truth"])
        assert d["matrix_downgrade_concordance"] > 0.8
        assert d["matrix_downgrade_slope"] > 0.5
        assert d["matrix_down3_ratio"] > 0.5
        assert d["matrix_down1_ratio"] > 0.5


def test_the_shape_diagnostics_survive_a_rounded_submission():
    """Four decimal places must not invent a far-corner or response finding.

    The far cells are of order 1e-4 at a mild factor, so rounding is the obvious
    way this could break. Rounding the oracle's own matrices and re-measuring,
    the far ratio reads 1.0000 at eight decimals, 0.9999 at six, 1.0035 at four
    and 0.6393 at three. Six is therefore what the instructions ask for, and the
    case for asking is this measurement: at three decimals the statistic would
    convict a correct submission of a 36% thinning that is entirely the
    formatting.
    """
    from pereval.scorers.migration import notch_diagnostics

    b = generate(1, n_years=20)
    start = np.array([b["truth"]["start_mix"].get(s, 0.0) for s in ORDER], float)
    orc = _oracle_matrices(b)

    for dp in (6, 8, 10):
        rounded = {n: {q: np.round(m, dp) for q, m in v.items()}
                   for n, v in orc.items()}
        d = notch_diagnostics(_matrices_text(rounded), start, b["truth"])
        assert d["matrix_down3_ratio"] == pytest.approx(1.0, abs=0.02)
        assert d["matrix_downgrade_concordance"] == 1.0


# ---------------------------------------------------------------------------
# The binary checks
# ---------------------------------------------------------------------------


def _served_seeds(n: int, base: int = 1) -> list[int]:
    """The seeds the task actually serves, as `_samples` draws them.

    The documented convention, `generate(seed=k)` for small k, is NOT what an
    agent is given, and the two have now hidden two separate defects. Sweeps
    that are about the generator rather than about a worked example use this.
    """
    return [int(x) for x in
            np.random.SeedSequence(base).generate_state(n, dtype=np.uint32)]


def _start_vec(bundle) -> np.ndarray:
    return np.array([bundle["truth"]["start_mix"].get(s, 0.0) for s in ORDER],
                    dtype=float)


def _preds_text(mats, bundle) -> str:
    """predictions.csv propagated from the given matrices, cohort convention."""
    t = bundle["truth"]
    mix = np.array([t["start_mix"].get(s, 0.0) for s in LIVE], dtype=float)
    cps = sorted(int(q) for q in t["scenarios"][t["scenario_names"][0]]
                 ["rating_distribution"])
    rows = ["scenario,quarter,state,share"]
    for scen in sorted(mats):
        v = np.concatenate([mix, [0.0]])
        for k in range(max(cps)):
            v = v @ mats[scen][k + 1]
            if k + 1 in cps:
                for st, x in zip(ORDER, v):
                    rows.append(f"{scen},{k + 1},{st},{float(x)!r}")
    return "\n".join(rows) + "\n"


def _one_model_backtest(bundle) -> str:
    """A compliant backtest: one estimated series, written under each scenario.

    This is what a model estimated once produces, so it is the right default for
    a test about some other property. `historical_fit_identical_across_scenarios`
    has its own test and passes its own inputs.
    """
    t = bundle["truth"]
    years = range(2005, 2005 + len(t["observed_annual_default_rate"]))
    return "scenario,year,default_rate\n" + "".join(
        f"{scen},{y},{v!r}\n" for scen in t["scenario_names"]
        for y, v in zip(years, t["expected_annual_default_rate"]))


_COMPLIANT = "__compliant__"


def _checks(mtext, ptext, bundle, btext=_COMPLIANT) -> dict[str, float]:
    if btext == _COMPLIANT:
        btext = _one_model_backtest(bundle)
    return model_checks(mtext, ptext, btext, _start_vec(bundle), bundle["truth"])


def test_the_answer_key_and_the_reference_fail_no_check():
    """The property that makes every threshold here defensible.

    A check that the true generating model trips is not a statement about the
    submission, it is a bug in the check. Finding one is not hypothetical: the
    unrestricted form of `stay_is_the_most_likely_outcome` failed the oracle on
    three of these twelve instances, because a CCC/C obligor in a severe quarter
    is genuinely likelier to default than to stay CCC/C, and the rule had to be
    narrowed to live destinations. The shipped reference passing too is the
    second half of it: a competent estimate must be able to clear every bar,
    or the count measures distance from the oracle rather than defect.

    The served seeds are swept as well as the documented ones, because the two
    conventions disagree and the disagreement has already hidden a bug. An
    earlier form of `pd_rises_with_severity` compared every checkpoint, which
    holds on `generate(seed=k)` for k from one to twelve and fails the answer
    key on the served draw: the severe scenario has a trough, so at quarter four
    it can be milder than the adverse path while quarter nine is far worse. At
    base seed 1, instance 4 puts severe at 0.92% against adverse's 1.04% at
    quarter four and 3.63% against 2.57% at quarter nine. The severity checks
    now read the terminal checkpoint only.
    """
    served = np.random.SeedSequence(1).generate_state(12, dtype=np.uint32)
    for seed in [*range(1, 13), *(int(x) for x in served)]:
        b = generate(seed, n_years=20)
        orc = _oracle_matrices(b)
        assert _checks(_matrices_text(orc), _preds_text(orc, b), b)[
            "checks_failed"] == 0.0, f"oracle failed a check on seed {seed}"
        files = public_files(b)
        p, m, _ = predict(files, "onefactor")
        assert _checks(m, p, b)["checks_failed"] == 0.0, (
            f"reference failed a check on seed {seed}")


def test_each_known_defect_trips_exactly_its_own_check():
    """Separation, and the absence of collateral failures.

    A thinned far corner and a frozen migration body are different modelling
    errors and each trips one check and only one, so the count says which. Both
    were invisible to the composite score: collapsing the far corner moves it by
    about fifteen thousandths against a reference of 0.285.
    """
    base = quarterly_base()
    for seed in _served_seeds(12):
        b = generate(seed, n_years=20)
        orc = _oracle_matrices(b)
        thin = {k: {q: _thin_far(m, 0.0) for q, m in v.items()}
                for k, v in orc.items()}
        froz = {k: {q: _freeze_body(m, base) for q, m in v.items()}
                for k, v in orc.items()}

        t = _checks(_matrices_text(thin), _preds_text(thin, b), b)
        assert t["fail_multinotch_downgrade_possible"] == 1.0
        assert t["checks_failed"] == 1.0

        f = _checks(_matrices_text(froz), _preds_text(froz, b), b)
        assert f["fail_downgrades_rise_with_severity"] == 1.0
        assert f["checks_failed"] == 1.0


def test_a_nan_where_a_probability_belongs_is_a_counted_failure():
    """NaN is a hard failure, not a missing value.

    `parse_matrices` discards a whole file holding one non-finite cell, which
    makes "wrote NaN" indistinguishable from "wrote nothing" to everything
    downstream. The checks read the raw cells so that the finiteness failure is
    counted once, as itself, rather than silently becoming an absent file.
    """
    b = generate(1, n_years=20)
    orc = _oracle_matrices(b)
    text = _matrices_text(orc)
    preds = _preds_text(orc, b)
    assert _checks(text, preds, b)["checks_failed"] == 0.0

    broken = text.replace(text.split("\n")[1].split(",")[3], "nan", 1)
    v = _checks(broken, preds, b)
    assert v["fail_matrix_cells_finite"] == 1.0
    assert v["fail_matrices_readable"] == 0.0, "a NaN is not an unreadable file"


def test_nothing_submitted_fails_every_check():
    """An artefact nobody can inspect has demonstrated no property at all.

    Excusing it would let a missing file outrank a bad answer on the count,
    which is backwards. This also pins the no-not-applicable rule: there is no
    third state, so the count stays monotone in how much is wrong.
    """
    b = generate(1, n_years=20)
    v = _checks(None, None, b, btext=None)
    assert v["checks_failed"] == float(len(CHECK_KEYS))
    assert all(v[f"fail_{k}"] == 1.0 for k in CHECK_KEYS)


def test_no_check_can_return_nan():
    """A ratio with a zero denominator is a badly designed diagnostic.

    Every check is an ordering or a count, never a quotient, so there is no
    submission on which one of them is undefined. This test is the guard on
    that: it sweeps the submissions that broke the old ratio diagnostics, the
    degenerate among them, on which the removed `matrix_one_model_discordance`
    returned NaN because identical matrices leave no comparable pairs.
    """
    base = quarterly_base()
    for seed in _served_seeds(3):
        b = generate(seed, n_years=20)
        files = public_files(b)
        orc = _oracle_matrices(b)
        cases = [(None, None),
                 ("", ""),
                 ("scenario,quarter,from_rating\n", "scenario,quarter,state,share\n"),
                 predict(files, "no_migration")[:2][::-1],
                 predict(files, "onefactor")[:2][::-1],
                 (_matrices_text({k: {q: _freeze_body(m, base) for q, m in v.items()}
                                  for k, v in orc.items()}), None)]
        for mtext, ptext in cases:
            v = _checks(mtext, ptext, b)
            for k in CHECK_KEYS:
                x = v[f"fail_{k}"]
                assert x in (0.0, 1.0), f"{k} returned {x}"
            assert not np.isnan(v["checks_failed"])


def test_refitting_per_scenario_shows_up_in_the_historical_fit():
    """One model is testable where refitting cannot hide it.

    The history does not depend on which future scenario is being run, so a
    model estimated once implies one fitted historical series and writes it
    three times. A model refitted per scenario writes three different ones. The
    comparison is an exact equality to CSV precision: no threshold to calibrate,
    no denominator to go to zero, and nothing taken from the answer key.

    This replaces `matrix_one_model_discordance`, now removed, which tried to do
    the same job from the matrices alone. That statistic returned NaN on a
    submission whose scenarios are identical, because identical matrices leave
    no comparable pairs, which is precisely the submission it most needed a
    verdict on, and it was blind to a per-scenario refit that stayed inside the
    one-factor family, which is the likeliest form such a refit takes.

    The prompt no longer says there is one history so there is one backtest.
    That sentence handed over the answer; the file is now asked for per scenario
    with no explanation of why the three should agree.
    """
    key = "fail_historical_fit_identical_across_scenarios"
    for seed in _served_seeds(3):
        b = generate(seed, n_years=20)
        files = public_files(b)
        p, m, refb = predict(files, "onefactor")

        assert _checks(m, p, b, btext=refb)[key] == 0.0, "reference refit?"
        assert _checks(m, p, b, btext=_one_model_backtest(b))[key] == 0.0

        rows = refb.strip().split("\n")
        bumped = [rows[0]]
        for r in rows[1:]:
            scen, year, val = r.split(",")
            mult = {"baseline": 1.0, "adverse": 1.01, "severe": 1.02}[scen]
            bumped.append(f"{scen},{year},{float(val) * mult!r}")
        assert _checks(m, p, b, btext="\n".join(bumped) + "\n")[key] == 1.0

        # a floating point difference is not a refit
        jitter = [rows[0]]
        for r in rows[1:]:
            scen, year, val = r.split(",")
            jitter.append(f"{scen},{year},{float(val) * (1 + 1e-9)!r}")
        assert _checks(m, p, b, btext="\n".join(jitter) + "\n")[key] == 0.0

        # one shared series is the correct answer, not a format failure
        one = "year,default_rate\n" + "\n".join(
            ",".join(r.split(",")[1:]) for r in rows[1:21]) + "\n"
        assert _checks(m, p, b, btext=one)[key] == 0.0


def test_the_degenerate_answer_trips_the_ordering_checks():
    """Predicting no defaults at all has to be a finding, which needs strictness.

    The degenerate submits the starting cohort unchanged, so its cohort default
    share is exactly zero under every scenario at every checkpoint. Weak
    orderings pass it: zero does not rise with severity, but neither does it
    fall. Strictness is what makes "losses are higher in stress" say anything,
    and the margin shows it costs nothing. At the terminal checkpoint, which is
    the only one the severity checks ask about, the oracle's smallest gap
    between adjacent severities is 0.0104 and the reference's is 0.0113 over
    192 comparisons, against a relative tie tolerance of 1e-6.
    """
    for seed in _served_seeds(3):
        b = generate(seed, n_years=20)
        p, m, bt = predict(public_files(b), "no_migration")
        v = _checks(m, p, b, btext=bt)
        for k in ("pd_rises_with_severity", "implied_pd_rises_with_severity",
                  "pd_rises_with_horizon", "downgrades_rise_with_severity",
                  "multinotch_downgrade_possible"):
            assert v[f"fail_{k}"] == 1.0, k
        assert v["checks_failed"] == 5.0
        # and it is still a readable, well formed submission
        for k in ("matrices_readable", "matrix_rows_sum_to_one",
                  "prediction_shares_sum_to_one", "pd_rises_as_rating_falls",
                  "historical_fit_identical_across_scenarios"):
            assert v[f"fail_{k}"] == 0.0, k


def test_the_published_history_shows_downgrades_rising_in_stress():
    """The evidence `downgrades_rise_with_severity` stands on.

    The check asserts a property of a submitted model. It is only defensible if
    the data the agent was given shows that property, otherwise it convicts an
    agent for fitting what it was handed. Read from data/transitions.csv alone,
    with no access to the latent factor.

    Measured over the twelve instances served at base seed 1: the annual
    downgrade frequency correlates +0.918 to +0.988 with the annual default
    rate, and downgrades are 2.6 to 5.7 times more frequent in the stressed
    quarter of years. It holds from every grade with room to fall, 3.6x from AAA
    through 4.5x from BBB to 2.9x from B, and it is not thin: one instance
    carries about 3,700 downgrades from a single grade.

    The far corner carries it most. The three-or-worse band is 13.6x more
    frequent in stressed years against 3.3x for the adjacent notch, which is why
    `multinotch_downgrade_possible` is a check about discarded evidence rather
    than a quibble about a structural zero.

    This test exists so that a change to the generating law cannot silently
    remove the ground the checks stand on.
    """
    import csv as _csv
    import io as _io

    cols = [f"to_{s.replace('/', '_')}" for s in LIVE] + ["to_D"]
    lifts, corrs, far_lifts = [], [], []
    for seed in _served_seeds(12):
        b = generate(seed, n_years=20)
        by: dict[int, np.ndarray] = {}
        for row in _csv.DictReader(_io.StringIO(
                public_files(b)["data/transitions.csv"])):
            y = int(row["year"])
            by.setdefault(y, np.zeros((D, D + 1)))[LIVE.index(row["from_rating"])] = \
                [float(row[c]) for c in cols]
        years = sorted(by)
        tot = np.array([by[y].sum() for y in years])
        dflt = np.array([by[y][:, D].sum() for y in years]) / tot
        down = np.array([by[y][:, :D][np.triu_indices(D, 1)].sum()
                         for y in years]) / tot
        far = np.array([sum(by[y][i, i + 3:D].sum() for i in range(D - 3))
                        for y in years]) / tot
        stressed = dflt >= np.quantile(dflt, 0.75)

        corrs.append(float(np.corrcoef(dflt, down)[0, 1]))
        lifts.append(float(down[stressed].mean() / down[~stressed].mean()))
        far_lifts.append(float(far[stressed].mean() / far[~stressed].mean()))

    assert min(corrs) > 0.9, f"weakest correlation {min(corrs):.3f}"
    assert min(lifts) > 2.0, f"weakest downgrade lift {min(lifts):.2f}x"
    assert min(far_lifts) > min(lifts), (
        "the far band should be the more stress-sensitive one: "
        f"far {min(far_lifts):.2f}x vs all {min(lifts):.2f}x")


def test_an_out_of_order_middle_scenario_is_caught():
    """Severity ordering is asked of every adjacent pair, not just the ends.

    Comparing only the mildest scenario with the worst passes a submission whose
    adverse projection is no worse than its baseline one, which is the same
    defect as a severe projection no worse than adverse. The construction here
    copies the baseline matrices into the adverse block and leaves severe alone,
    so the ends-only comparison still reads strictly increasing, as the test
    asserts directly, while the pair that is wrong is wrong.
    """
    for seed in _served_seeds(3):
        b = generate(seed, n_years=20)
        orc = _oracle_matrices(b)
        order = list(b["truth"]["scenario_names"])
        bent = {k: {q: m.copy() for q, m in v.items()} for k, v in orc.items()}
        bent[order[1]] = {q: m.copy() for q, m in orc[order[0]].items()}

        w = _row_weights(_start_vec(b))
        total = {n: sum(_downgrade_mass(bent[n][q], w) for q in sorted(bent[n]))
                 for n in order}
        assert total[order[-1]] > total[order[0]], (
            "the ends-only comparison must still pass, or this proves nothing")

        v = _checks(_matrices_text(bent), _preds_text(bent, b), b)
        assert v["fail_downgrades_rise_with_severity"] == 1.0


def test_matrices_out_of_order_in_severity_hide_behind_a_monotone_projection():
    """The projection and the matrices are two claims, and both are checked.

    `pd_rises_with_severity` reads predictions.csv. A submission can file a
    perfectly ordered projection computed by some other route while the matrices
    it documents imply the opposite, and nothing else here would catch that:
    `matrix_submission_gap` is reported rather than checked, and it is a
    distance, not an ordering. So the same question is asked of the matrices by
    propagating the published cohort mix through them.

    The construction moves 95% of the severe scenario's default column into the
    worst live grade, which keeps every row summing to one, keeps the default
    column monotone in rating, and RAISES downgrade mass, so the matrix-side
    defect is isolated from the three checks that would otherwise cover it.
    Checked across 36 instances on three seed sets: this construction trips
    exactly one check and it is this one. The fraction has to be large because
    severe sits well clear of adverse on most draws, and 0.75 inverts the
    ordering on some instances and not others.
    """
    ccc = len(LIVE) - 1
    for seed in _served_seeds(3):
        b = generate(seed, n_years=20)
        orc = _oracle_matrices(b)
        order = list(b["truth"]["scenario_names"])
        damped = {k: {q: m.copy() for q, m in v.items()} for k, v in orc.items()}
        for m in damped[order[-1]].values():
            moved = m[:len(LIVE), len(LIVE)] * 0.95
            m[:len(LIVE), len(LIVE)] -= moved
            m[:len(LIVE), ccc] += moved

        honest = _preds_text(orc, b)
        v = _checks(_matrices_text(damped), honest, b)
        assert v["fail_pd_rises_with_severity"] == 0.0, (
            "the filed projection is the oracle's own and must pass")
        assert v["fail_implied_pd_rises_with_severity"] == 1.0
        assert v["fail_downgrades_rise_with_severity"] == 0.0
        assert v["checks_failed"] == 1.0, (
            {k: v[f"fail_{k}"] for k in CHECK_KEYS if v[f"fail_{k}"]})


def test_no_scenario_is_more_than_ten_times_the_portfolio_s_own_history():
    """A 1%-a-year book does not lose a tenth of itself in a realistic scenario.

    Before the cap, one draw put 98.9% of the cohort in default by quarter nine
    under severe, 71.2% under adverse and 12.9% under its own BASELINE, against
    an observed history of 1.12% a year. That is not a stress test, and it is
    close to free marks besides: when the truth is nearly a point mass on
    default, predicting total ruin scores well and the twelve components stop
    discriminating.

    The anchor is the observed annual default rate scaled to the horizon, not
    the drawn baseline scenario. The instance above is only 7.7x ITS baseline
    and would have passed a ratio rule, because the baseline is a draw too and
    was itself elevated.

    The ordering assertion is the other half: one damping factor is applied to
    all three scenarios, so damping must not be able to collapse them onto each
    other, which the severity checks would read, correctly, as a defect.
    """
    for seed in [*range(1, 25), *_served_seeds(24), *_served_seeds(24, base=7)]:
        b = generate(seed, n_years=20)
        t = b["truth"]
        anchor = SEVERITY_CAP * float(np.mean(
            t["observed_annual_default_rate"])) * t["horizon_quarters"] / 4.0
        pds = {n: t["scenarios"][n]["rating_distribution"][
            str(max(t["checkpoints"]))]["D"] for n in t["scenario_names"]}
        for name, pd in pds.items():
            assert pd <= anchor * (1 + 1e-6), (
                f"seed {seed}: {name} at {pd:.4f} exceeds {anchor:.4f}")
        ordered = [pds[n] for n in t["scenario_names"]]
        assert ordered == sorted(ordered) and len(set(ordered)) == len(ordered), (
            f"seed {seed}: damping collapsed the severity ordering, {pds}")
        assert 0.0 < b["dgp"]["severity_damping"] <= 1.0


def test_an_instance_the_cap_does_not_bind_on_is_left_exactly_alone():
    """The damping is a remedy, not a tax: it must be inert where it is not needed.

    A factor of exactly 1.0 means the hump weights are multiplied by one, so the
    published macro rows and the factor path are bit-identical to what the
    generator produced before the cap existed.
    """
    untouched = 0
    for seed in _served_seeds(24):
        b = generate(seed, n_years=20)
        t = b["truth"]
        anchor = SEVERITY_CAP * float(np.mean(
            t["observed_annual_default_rate"])) * t["horizon_quarters"] / 4.0
        worst = max(t["scenarios"][n]["rating_distribution"][
            str(max(t["checkpoints"]))]["D"] for n in t["scenario_names"])
        if worst < anchor * 0.999:
            assert b["dgp"]["severity_damping"] == 1.0, seed
            untouched += 1
    assert untouched >= 12, f"only {untouched} of 24 instances were left alone"
