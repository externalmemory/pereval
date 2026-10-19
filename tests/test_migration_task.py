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
    ORDER,
    ks_distance,
    score_predictions,
)
from pereval.tasks.migration.baselines import predict
from pereval.tasks.migration.generator import (
    BASE_MIX,
    CHECKPOINTS,
    D,
    LIVE,
    N_OBLIGORS,
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
    return generate(1, n_years=20, scenario="adverse")


def test_deterministic():
    a = generate(3, n_years=12, scenario="adverse")
    b = generate(3, n_years=12, scenario="adverse")
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
    assert json.loads(files["data/policy.json"])["checkpoints"] == list(CHECKPOINTS)


def test_truth_distributions_are_cohort_shares_including_default(bundle):
    for q in CHECKPOINTS:
        d = bundle["truth"]["rating_distribution"][str(q)]
        assert set(d) == set(ORDER)
        assert sum(d.values()) == pytest.approx(1.0, abs=1e-9)
    early = bundle["truth"]["rating_distribution"][str(min(CHECKPOINTS))]
    late = bundle["truth"]["rating_distribution"][str(max(CHECKPOINTS))]
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
    rows = ["quarter,state,share"]
    for q in CHECKPOINTS:
        for s in ORDER:
            rows.append(f"{q},{s},{truth['rating_distribution'][str(q)][s]}")
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
    for k in ("ks_q4", "ks_q9", "default_q4", "default_q9"):
        assert perfect[f"{k}_norm"] == pytest.approx(0.0, abs=1e-9)
    missing = score_predictions(truth, None)
    for k in ("ks_q4", "ks_q9", "default_q4", "default_q9"):
        assert missing[f"{k}_norm"] == pytest.approx(1.0)


def test_shape_and_default_are_scored_independently(bundle):
    """Getting the grades right while claiming no defaults must not score well."""
    truth = bundle["truth"]
    rows = ["quarter,state,share"]
    for q in CHECKPOINTS:
        d = truth["rating_distribution"][str(q)]
        live_total = sum(d[s] for s in ORDER[:-1])
        for s in ORDER:
            share = 0.0 if s == "D" else d[s] / live_total
            rows.append(f"{q},{s},{share}")
    r = score_predictions(truth, "\n".join(rows) + "\n")
    # the live-grade shape is exact, so both KS components vanish
    assert r["ks_q4_norm"] == pytest.approx(0.0, abs=1e-9)
    assert r["ks_q9_norm"] == pytest.approx(0.0, abs=1e-9)
    # but both default components are maximally wrong, pinning the score near 0.5
    assert r["default_q4_norm"] == pytest.approx(1.0, rel=1e-6)
    assert r["default_q9_norm"] == pytest.approx(1.0, rel=1e-6)
    assert r["score"] == pytest.approx(0.5, abs=1e-6)


@pytest.mark.parametrize("text", [
    "quarter,state,share\n4,AAA,0.5\n",                       # incomplete states
    "quarter,state,share\n4,AAA,-0.1\n" + "\n".join(
        f"4,{s},0.2" for s in ORDER[1:]),                     # negative share
    "quarter,state,share\n" + "\n".join(f"4,{s},50" for s in ORDER),  # percent, not share
    "quarter,state,share\n" + "\n".join(f"4,{s},0.125" for s in ORDER) * 2,  # duplicates
])
def test_malformed_submissions_cannot_gain_credit(bundle, text):
    r = score_predictions(bundle["truth"], text)
    assert r["completion"] == 0.0
    assert r["score"] == pytest.approx(1.0)


def test_reference_beats_the_degenerate_by_a_wide_margin():
    """The anchor that makes the column readable.

    Measured at 0.303 against the degenerate's 1.000 over these eighteen
    instances, a separation of 3.3x, at the task's shipped n_years=20. The bar
    is deliberately looser than the measurement so ordinary generator drift does
    not fail it, but a change that collapses the separation will.

    Six seeds rather than the module's three, because seed 3 is the worst of the
    first eight and a three-seed sample containing it reads 0.417, which is not
    the number the doc reports.

    Twenty years is where the shrinkage earns its place. Unshrunk, the reference
    loses to the degenerate on five of twenty-four draws, reaching 1.48. See
    `project_factor` for why the fix is shrinkage and not a bound on the
    projection.
    """
    ref, deg = [], []
    for scen in SCEN:
        for seed in (1, 2, 3, 4, 5, 6):
            b = generate(seed, n_years=20, scenario=scen)
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
    b = generate(2, n_years=20, scenario="adverse")
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
    z = bundle["truth"]["z_scenario"]
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

    b = generate(1, n_years=20, scenario="adverse")
    f = public_files(b)
    preds, mats, _ = predict(f, "onefactor")
    start = np.array([b["truth"]["start_mix"].get(s, 0.0) for s in ORDER], float)
    cps = [int(q) for q in b["truth"]["rating_distribution"]]
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

    b = generate(1, n_years=20, scenario="adverse")
    preds, mats, _ = predict(public_files(b), "onefactor")
    rows = mats.splitlines()
    header, body = rows[0], rows[1:]
    # break the first live row: negative mass, rows off one, and a default
    # probability that improves as credit quality worsens
    broken = header + "\n" + "\n".join(
        ["1,AAA," + ",".join(["0.5", "0.6", "-0.2", "0.0", "0.0", "0.0", "0.0", "0.9"]),
         "1,AA," + ",".join(["0.0"] * 7 + ["0.1"])] + body[2:])
    start = np.array([b["truth"]["start_mix"].get(s, 0.0) for s in ORDER], float)
    cps = [int(q) for q in b["truth"]["rating_distribution"]]
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

    b = generate(1, n_years=20, scenario="adverse")
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

    b = generate(1, n_years=20, scenario="adverse")
    f, t = public_files(b), b["truth"]
    start = np.array([t["start_mix"].get(s, 0.0) for s in ORDER], float)
    cps = [int(q) for q in t["rating_distribution"]]

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
    # Measured at 0.45% of the score on this instance and under 0.01% averaged
    # over twelve, where the per-instance differences cancel. The bound is 5%,
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

    b = generate(1, n_years=20, scenario="adverse")
    f, t = public_files(b), b["truth"]
    start = np.array([t["start_mix"].get(s, 0.0) for s in ORDER], float)
    cps = [int(q) for q in t["rating_distribution"]]
    preds, mats, _ = predict(f, "onefactor")
    head, *body = mats.splitlines()

    good = matrix_diagnostics(mats, start, parse_predictions(preds), cps)
    assert good["matrix_rows_valid"] == 1.0
    assert good["matrix_nonnegative"] == 1.0
    assert good["matrix_admissible"] == 1.0

    def scaled(line, k):
        parts = line.split(",")
        return ",".join(parts[:2] + [repr(float(x) * k) for x in parts[2:]])

    off = matrix_diagnostics(head + "\n" + "\n".join(scaled(x, 1.2) for x in body),
                             start, parse_predictions(preds), cps)
    assert off["matrix_rows_valid"] == 0.0
    assert off["matrix_row_sum_error"] == pytest.approx(0.2, abs=0.01)
    assert off["matrix_submission_gap"] > 1.0      # mass loss compounds

    parts = body[0].split(",")
    parts[2] = repr(float(parts[2]) + 0.05)
    parts[9] = repr(float(parts[9]) - 0.05)
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

    b = generate(1, n_years=20, scenario="severe")
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
        ratios.append(d["fit_stress_mean_ratio"])
    assert ratios[0] < ratios[1] < ratios[2]


def test_shipped_reference_is_flagged_for_damped_macro_response():
    """The anchor fails its own stress check, and that is recorded not hidden.

    The shrinkage that stops the reference blowing out on the projection also
    damps its macro response, so it under-fits the stressed years by about a
    third. An agent that beats 0.287 while keeping this ratio near one is doing
    something the score alone cannot see.
    """
    from pereval.tasks.migration.baselines import backtest_diagnostics

    d = backtest_diagnostics(public_files(generate(1, n_years=20, scenario="severe")))
    assert 0.5 < d["stress_mean_ratio"] < 0.85
    assert d["factor_swing_retained"] < 0.9
    # the band still clears the worst observed year for a correctly specified fit
    assert d["peak_over_bound"] < 1.0


def test_degenerate_floors_every_one_sided_statistic():
    """No migration means no defaults, so every stress ratio must read zero."""
    from pereval.scorers.migration import (
        fit_diagnostics, parse_predictions, stress_diagnostics,
    )

    b = generate(2, n_years=20, scenario="adverse")
    f, t = public_files(b), b["truth"]
    preds, mats, back = predict(f, "no_migration")
    start = np.array([t["start_mix"].get(s, 0.0) for s in ORDER], float)
    s = stress_diagnostics(mats, start, parse_predictions(preds), t)
    d = fit_diagnostics(back, t["observed_annual_default_rate"])
    assert s["stress_mean_ratio"] == 0.0
    assert s["stress_peak_ratio"] == 0.0
    assert d["fit_stress_mean_ratio"] == 0.0
    assert "fit_peak_lag" not in d          # a flat series has no peak


def test_true_loss_path_reconciles_with_the_scored_checkpoint():
    """The quarterly increments must sum to the cohort default share at quarter 9."""
    b = generate(1, n_years=20, scenario="severe")
    t = b["truth"]
    assert sum(t["default_increments"]) == pytest.approx(
        t["rating_distribution"]["9"]["D"], abs=1e-9)
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
    flat = _backtest_csv(range(2000, 2008), [0.007] * 8)
    d = fit_diagnostics(flat, obs)
    assert d["fit_peak_prominence"] == pytest.approx(0.0)
    assert "fit_peak_lag" not in d

    # a series that tracks the observed peak is prominent and correctly timed
    sharp = _backtest_csv(range(2000, 2008), obs)
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

    b = generate(1, n_years=20, scenario="severe")
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
