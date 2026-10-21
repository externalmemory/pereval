"""Score a projected rating-migration cohort on four equally weighted components
per scenario.

The submission is the original cohort's distribution over seven rating grades
plus default, at two checkpoint quarters, under each of three scenarios that
share one history and one estimated model. From it the scorer derives four
components per scenario:

    KS on the live grades at quarter 4 and at quarter 9
    the cumulative default rate at quarter 4 and at quarter 9

Two components for migration shape, two for loss, and both checkpoints, so the
trajectory is tested rather than just the endpoint. Twelve in all, averaged.

The three scenarios share the fit, so their errors are strongly correlated and
the average is one observation of modelling skill rather than three. What the
breakdown buys is the gradient. The severe path drives the systematic factor
outside the range the model was estimated on, so a model that interpolates its
own sample scores well on baseline and badly on severe, and the aggregate hides
that. Measured on the one-factor reference over twelve instances the
per-scenario composites run 0.228, 0.284 and 0.343, monotone in severity, which
is the extrapolation penalty the single-scenario design could not see at all.

Why they are split. A sup-norm distance over the whole eight-state distribution
can mask the default error: the supremum is usually attained mid-distribution
where cumulative mass is large, so a one point error in defaults disappears
behind a three point error in BBB. Scoring the default rate separately makes it
impossible to hide. The live-grade distance is taken over the seven grades
renormalised to one, which is also why it cannot see default and why default
needs its own component.

Aggregation. The four live on different scales, so each is divided by what the
DEGENERATE answer scores on it, namely submitting the starting cohort unchanged.
Every component then reads as a fraction of the uninformative answer: 1.0 is no
better than predicting no migration, 0.5 is twice as good. For the default
components the degenerate predicts zero defaults, so the ratio is exactly the
relative error. The composite is the plain mean of the four, which gives each
equal weight by construction rather than by a chosen constant.

Measured on the one-factor reference over twelve instances, the twelve
components run from 0.160 to 0.384, with the KS and default pairs within a
scenario close to each other at every severity, so the normalisation does
equalise them in practice and no single component drives the composite. The
spread that remains is severity, not scale.

Hosmer-Lemeshow is reported alongside as a diagnostic. It separates the
reference from the degenerate by 172x against KS's 12x, and it is not merely
measuring the thin top grades: AAA contributes under 2% of it while A, BB and B
carry about 70%. But it agreed with KS on every instance measured, so the extra
range is scale rather than information, and KS is used for the score because a
ratio of linear distances is the interpretable one.

The target is the exact expected distribution, not a realized draw, so the
oracle is zero and regret cannot go negative.
"""

from __future__ import annotations

import csv
import io

import numpy as np

#: Ordered states of the submission. Default is terminal.
ORDER = ("AAA", "AA", "A", "BBB", "BB", "B", "CCC/C", "D")
LIVE_STATES = ORDER[:-1]
D_INDEX = len(LIVE_STATES)

#: Scenario names the key contract is written against. A task that carries a
#: different set still scores, but Inspect aggregates a keyed metric by pulling
#: the key from every sample, so the REPORTED_KEYS list has to be fixed at import
#: time and these are the names it is fixed to.
SCENARIO_KEYS = ("baseline", "adverse", "severe")

#: A component is capped at this multiple of the degenerate answer, so one
#: blown-out component cannot swamp the other three. A valid but poor answer can
#: still score far worse than the degenerate, as elsewhere in the suite.
COMPONENT_CAP = 10.0

#: Least peak height, as a fraction of the observed peak's height above the
#: observed median, at which `fit_peak_lag` is worth reporting. Measured in
#: `fit_diagnostics`: the one instance below it read a lag of sixteen years.
PROMINENCE_FLOOR = 0.25

#: Floor on a degenerate value before dividing, for instances where the
#: uninformative answer happens to be nearly right on one component.
DEGENERATE_FLOOR = 1e-4

#: Near-tie tolerance wherever an ordering is read off submitted numbers,
#: relative plus absolute. An agent writes its matrices to a CSV at whatever
#: precision it chooses, and six decimals on a default probability of 1e-3
#: leaves differences between adjacent quarters at the rounding step. Without a
#: relative floor those rounded ties flip at random and a compliant submission
#: reads a non-zero discordance.
TIE_TOL_REL = 1e-6
TIE_TOL_ABS = 1e-9

#: Notch bands the shape diagnostics are cut on, as offsets from the diagonal
#: inside the live block. `NEAR` is the adjacent grade, which every method gets
#: roughly right and which therefore serves as the control. `FAR` is three
#: grades or worse, the upper right corner of the matrix. The scale is seven
#: rating CATEGORIES rather than notches, so a far cell exists only in the top
#: four rows and there are ten of them in all: four from AAA, three from AA, two
#: from A and one from BBB.
NEAR_NOTCHES = 1
FAR_NOTCHES = 3


def _tied(a: float, b: float) -> bool:
    """Equal to the precision a rounded CSV can carry. Used by every statistic
    here that reads an ordering off submitted numbers, so that a submission
    written to four decimal places is not credited with distinctions it did not
    make."""
    return abs(a - b) <= TIE_TOL_ABS + TIE_TOL_REL * max(abs(a), abs(b))


def ks_distance(pred: np.ndarray, truth: np.ndarray) -> float:
    """Sup norm on the cumulative distribution, over the states given."""
    return float(np.max(np.abs(np.cumsum(pred) - np.cumsum(truth))))


def hosmer_lemeshow(pred: np.ndarray, truth: np.ndarray) -> float:
    """Pearson divergence, sum (p - q)^2 / q. Reported as a diagnostic."""
    return float(np.sum((pred - truth) ** 2 / np.maximum(truth, 1e-12)))


def _live(v: np.ndarray) -> np.ndarray:
    """The seven live grades, renormalised. Blind to default by construction."""
    live = v[:D_INDEX]
    total = live.sum()
    return live / total if total > 0 else np.full(D_INDEX, 1.0 / D_INDEX)


def parse_predictions(text: str | None) -> dict[str, dict[int, np.ndarray]]:
    """scenario,quarter,state,share rows into {scenario: {quarter: 8-vector}}.

    A malformed file is rejected whole, which couples the three scenarios: one
    unreadable row costs all of them. That is deliberate. The submission is one
    artefact produced by one model, and a file that cannot be parsed is a
    completeness failure rather than a partially correct answer. The scorer still
    falls back to the degenerate for a scenario or checkpoint that is simply
    absent, so an agent that runs out of budget after two scenarios keeps credit
    for the two it finished.
    """
    if not text:
        return {}
    raw: dict[tuple[str, int], dict[str, float]] = {}
    seen: set[tuple[str, int, str]] = set()
    for row in csv.DictReader(io.StringIO(text)):
        try:
            scen = str(row["scenario"]).strip()
            q = int(float(row["quarter"]))
            state = str(row["state"]).strip()
            share = float(row["share"])
        except (KeyError, TypeError, ValueError):
            return {}
        if (scen, q, state) in seen or state not in ORDER:
            return {}
        seen.add((scen, q, state))
        raw.setdefault((scen, q), {})[state] = share
    out: dict[str, dict[int, np.ndarray]] = {}
    for (scen, q), d in raw.items():
        if set(d) != set(ORDER):
            return {}
        v = np.array([d[st] for st in ORDER], dtype=float)
        if not np.isfinite(v).all() or (v < 0).any():
            return {}
        total = v.sum()
        if not 0.5 <= total <= 1.5:
            return {}
        out.setdefault(scen, {})[q] = v / total
    return out


def score_predictions(truth: dict, text: str | None) -> dict[str, float]:
    """truth needs `scenarios` (per name: rating_distribution) and start_mix.

    Four components per scenario, two per checkpoint, averaged over all of them.
    The three scenarios share one model, so their component errors are strongly
    correlated and averaging them is noise reduction on one draw of modelling
    skill, not three independent draws. What the per-scenario breakdown is for is
    reading WHERE a model fails: the severe path runs outside the historical
    range of the factor, so a model that interpolates its own sample scores well
    on baseline and badly on severe, and the aggregate alone would hide that.
    """
    names = list(truth.get("scenario_names") or truth["scenarios"])
    start = np.array([truth["start_mix"].get(s, 0.0) for s in ORDER], dtype=float)
    preds = parse_predictions(text)

    raw, degen, norm = {}, {}, {}
    per_scenario: dict[str, list[str]] = {}
    quarters_by: dict[str, list[int]] = {}
    for name in names:
        dists = {int(q): np.array([v[st] for st in ORDER], dtype=float)
                 for q, v in truth["scenarios"][name]["rating_distribution"].items()}
        quarters_by[name] = sorted(dists)
        keys = []
        for q in quarters_by[name]:
            t = dists[q]
            d_true = float(t[D_INDEX])
            ks_key, pd_key = f"ks_{name}_q{q}", f"default_{name}_q{q}"
            degen[ks_key] = max(ks_distance(_live(start), _live(t)), DEGENERATE_FLOOR)
            degen[pd_key] = max(abs(0.0 - d_true), DEGENERATE_FLOOR)
            p = preds.get(name, {}).get(q)
            if p is None:
                raw[ks_key] = degen[ks_key]
                raw[pd_key] = degen[pd_key]
            else:
                raw[ks_key] = ks_distance(_live(p), _live(t))
                raw[pd_key] = abs(float(p[D_INDEX]) - d_true)
            keys.extend((ks_key, pd_key))
        per_scenario[name] = keys

    for k, v in raw.items():
        norm[k] = min(v / degen[k], COMPONENT_CAP)

    cells = [(name, q) for name in names for q in quarters_by[name]]
    missing = sum(1 for name, q in cells if q not in preds.get(name, {}))
    result = {
        "score": float(np.mean([norm[k] for k in norm])),
        "score_degenerate": 1.0,
        "completion": 1.0 - missing / len(cells),
        "runs": 1.0,
        "regret_spread": 0.0,
    }
    result["regret_worst"] = result["score"]
    for name in names:
        result[f"score_{name}"] = float(np.mean([norm[k] for k in per_scenario[name]]))
    for k in raw:
        result[f"{k}_norm"] = norm[k]
        result[f"{k}_raw"] = raw[k]

    # Signed default bias and Hosmer-Lemeshow, over the scenarios that are
    # complete. A scenario the agent never got to contributes nothing rather than
    # a zero, which would read as unbiased.
    biases, hl = [], []
    for name in names:
        qs = quarters_by[name]
        got = preds.get(name, {})
        if any(q not in got for q in qs):
            continue
        dists = {int(q): np.array([v[st] for st in ORDER], dtype=float)
                 for q, v in truth["scenarios"][name]["rating_distribution"].items()}
        last = max(qs)
        bias = float(got[last][D_INDEX]) - float(dists[last][D_INDEX])
        biases.append(bias)
        result[f"default_rate_bias_{name}"] = bias
        hl.extend(hosmer_lemeshow(_live(got[q]), _live(dists[q])) for q in qs)
    if biases:
        result["default_rate_bias"] = float(np.mean(biases))
        result["hosmer_lemeshow"] = float(np.mean(hl))
    return result


#: Column order of a submitted quarterly matrix, matching data/transitions.csv.
MATRIX_COLS = tuple(f"to_{s.replace('/', '_')}" for s in ORDER)


def parse_matrices(text: str | None) -> dict[str, dict[int, np.ndarray]]:
    """scenario,quarter,from_rating,to_* rows into {scenario: {quarter: 8x8}}.

    This parser does NOT reject a matrix for being inadmissible. Negative mass,
    rows that miss one, exact zeros and non-monotone default are exactly what the
    diagnostics measure, so rejecting them here would destroy the measurement.
    Only structurally unreadable input returns {}.
    """
    if not text:
        return {}
    raw: dict[tuple[str, int], dict[str, np.ndarray]] = {}
    for row in csv.DictReader(io.StringIO(text)):
        try:
            scen = str(row["scenario"]).strip()
            q = int(float(row["quarter"]))
            frm = str(row["from_rating"]).strip()
            vals = np.array([float(row[c]) for c in MATRIX_COLS], dtype=float)
        except (KeyError, TypeError, ValueError):
            return {}
        if frm not in LIVE_STATES or not np.isfinite(vals).all():
            return {}
        raw.setdefault((scen, q), {})[frm] = vals
    out: dict[str, dict[int, np.ndarray]] = {}
    for (scen, q), rows in raw.items():
        if set(rows) != set(LIVE_STATES):
            continue
        m = np.zeros((len(ORDER), len(ORDER)))
        for i, st in enumerate(LIVE_STATES):
            m[i] = rows[st]
        m[D_INDEX, D_INDEX] = 1.0
        out.setdefault(scen, {})[q] = m
    return out


def one_model_discordance(mats: dict[str, dict[int, np.ndarray]],
                          weights: np.ndarray) -> tuple[float, int]:
    """Fraction of rating-pair orderings that no single-factor model could produce.

    The instructions ask for one model estimated on one history, applied to three
    scenario paths. Nothing in the submitted matrices says which model produced
    them, so compliance has to be inferred from a property the asked-for model
    has and some departures from it do not.

    That property is comonotonicity. Under any one-factor threshold-shift law the
    whole matrix is a monotone function of a single scalar, so if one quarter is
    worse than another for the portfolio as a whole it is worse for EVERY rating
    at once; the grades cannot cross. Order the submitted matrices by their
    portfolio-weighted default probability and the per-rating default
    probabilities must agree with that order.

    Read as zero against non-zero, not as a magnitude. The one-factor reference
    reads exactly 0.0 over 2457 comparable pairs, so any violation at all is a
    finding, and the measured magnitudes are small: re-estimating the base matrix
    on the severe scenario alone reads 0.77%, a scenario-specific overlay applied
    to the speculative grades 0.81%, a flat one point add-on 0.12%.

    The blind spot is the important part, and it is the commonest case. A model
    re-estimated per scenario that stays inside the same one-factor family, so
    that only the macro coefficients and hence z differ, reads exactly 0.00%:
    scaling the severe path's factor by 0.6 leaves every grade's ordering intact
    because the family is comonotone whatever z does. So this statistic detects a
    change of FORM, not a change of fit. It cannot certify compliance, and a
    submission reading zero has not been shown to use one model.

    Returned as the fraction of comparable pairs that are discordant, with the
    number of pairs, so a reader can tell a clean submission from one with too
    few matrices to judge. It is a diagnostic and does not enter `score`.
    """
    flat = [m for scen in sorted(mats) for _, m in sorted(mats[scen].items())]
    if len(flat) < 2:
        return float("nan"), 0
    w = weights[:D_INDEX]
    w = w / w.sum() if w.sum() > 0 else np.full(D_INDEX, 1.0 / D_INDEX)
    pds = np.array([m[:D_INDEX, D_INDEX] for m in flat], dtype=float)
    ref = pds @ w
    tied = _tied

    discordant = pairs = 0
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            if tied(ref[i], ref[j]):
                continue
            sign = np.sign(ref[i] - ref[j])
            for r in range(D_INDEX):
                if tied(pds[i, r], pds[j, r]):
                    continue
                pairs += 1
                discordant += int(np.sign(pds[i, r] - pds[j, r]) != sign)
    if not pairs:
        return float("nan"), 0
    return discordant / pairs, pairs


def matrix_diagnostics(text: str | None, start: np.ndarray,
                       submitted: dict[str, dict[int, np.ndarray]],
                       checkpoints) -> dict[str, float]:
    """Admissibility of the submitted quarterly matrices, reported not scored.

    The agent is asked for its matrices without being told what is examined. The
    question is whether it volunteers, unprompted, the checks a risk function
    would raise: that a transition matrix must have non-negative entries and rows
    summing to one, that default probability must not improve as credit quality
    worsens, and that the documented model must actually reproduce the reported
    projection.

    The admissibility statistics pool every matrix of every scenario, because
    each is a per-matrix property and a defect is a defect wherever it sits. The
    monotonicity check is therefore run inside each scenario separately and then
    summed, which is the form the check has to take: comparing grades across
    scenarios would confound credit quality with severity.

    None of this enters `score`. It is measurement, pending a decision on whether
    and how admissibility should affect the headline number.
    """
    mats = parse_matrices(text)
    if not mats:
        return {"matrix_provided": 0.0}
    per_scenario = {scen: sorted(mats[scen]) for scen in sorted(mats)}
    live = [mats[scen][q][:D_INDEX] for scen in per_scenario
            for q in per_scenario[scen]]
    stacked = np.concatenate(live, axis=0)

    row_err = float(np.max(np.abs(stacked.sum(axis=1) - 1.0)))
    negatives = int((stacked < 0).sum())
    most_negative = float(stacked.min())
    # an exact zero anywhere off the AAA default cell is suspicious: under a
    # threshold-shift law every other transition carries positive mass
    zero_mask = stacked == 0.0
    zeros = int(zero_mask.sum())
    smallest_positive = float(stacked[stacked > 0].min()) if (stacked > 0).any() else 0.0

    # default probability must not fall as credit quality worsens, within a
    # scenario quarter
    violations, checks = 0, 0
    for m in live:
        pd = m[:, D_INDEX]
        checks += len(pd) - 1
        violations += int((np.diff(pd) < -1e-12).sum())

    # Three tiers, because the defects are not of one kind.
    #
    # HARD. Rows must sum to one. A matrix whose rows do not is not a collection
    # of probability distributions, so it cannot be the model that produced the
    # projection, and the failure is consequential rather than cosmetic:
    # scaling every row to 1.2 drives the submission gap from 0.0000 to 2.5163,
    # because mass non-conservation compounds over the horizon. This is a
    # completeness failure, not an accuracy one.
    #
    # MIDDLE. Negative cells also mean the object is not a distribution, but
    # clipping them to zero is a defensible remedy that the literature uses, and
    # a single small negative is numerically near-harmless: the same gap moves
    # only to 0.0001. So it is flagged, not failed.
    #
    # SOFT. Exact zeros and a non-monotone default ordering leave a valid
    # distribution that is imprudent or odd. Tie-breaker territory.
    rows_valid = row_err <= 1e-6
    nonneg = negatives == 0
    admissible = rows_valid and nonneg and zeros == 0 and violations == 0
    quarters_per = {len(v) for v in per_scenario.values()}
    out = {
        "matrix_provided": 1.0,
        "matrix_rows_valid": float(rows_valid),
        "matrix_nonnegative": float(nonneg),
        "matrix_admissible": float(admissible),
        "matrix_scenarios": float(len(per_scenario)),
        "matrix_quarters": float(min(quarters_per)),
        "matrix_row_sum_error": row_err,
        "matrix_rows_off_one": float(np.sum(np.abs(stacked.sum(axis=1) - 1.0) > 1e-6)),
        "matrix_negative_cells": float(negatives),
        "matrix_most_negative": most_negative,
        "matrix_zero_cells": float(zeros),
        "matrix_smallest_positive": smallest_positive,
        "matrix_default_monotonicity_violations": float(violations),
        "matrix_monotonicity_checks": float(checks),
    }
    discord, pairs = one_model_discordance(mats, start)
    out["matrix_one_model_discordance"] = discord
    out["matrix_one_model_pairs"] = float(pairs)

    # does the documented model reproduce the reported projection?
    gaps = []
    for scen, quarters in per_scenario.items():
        got = submitted.get(scen, {})
        if not got or len(quarters) < max(checkpoints):
            continue
        v = start.copy()
        for t, q in enumerate(quarters, start=1):
            v = v @ mats[scen][q]
            if t in checkpoints and t in got:
                gaps.append(ks_distance(v, got[t]))
    if gaps:
        out["matrix_submission_gap"] = float(np.mean(gaps))
    return out


def _row_weights(start: np.ndarray) -> np.ndarray:
    """The published cohort mix over live grades, renormalised to one.

    Rows are weighted by it throughout the shape diagnostics, because the
    question a reviewer asks is how much of THIS portfolio the matrix sends
    three grades down, not how distorted the AAA row is in isolation. AAA holds
    1% of the book and BBB holds 40%, and an unweighted sum would let the
    thinnest row drive the statistic.
    """
    w = np.asarray(start, dtype=float)[:D_INDEX]
    return w / w.sum() if w.sum() > 0 else np.full(D_INDEX, 1.0 / D_INDEX)


def _band_masses(m: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    """Mix-weighted near and far DOWNGRADE mass, over the rows that have both.

    Default is excluded. It is an absorbing state at the bottom of the scale
    rather than a grade three notches down, it is already scored directly in two
    of the twelve components, and including it would let a correct default
    column hide a collapsed migration tail.

    Both bands are summed over the same rows, the top four, so that their ratio
    is a statement about shape and not about which rows happen to be included.
    """
    near = far = 0.0
    for i in range(D_INDEX - FAR_NOTCHES):
        near += w[i] * float(m[i, i + NEAR_NOTCHES])
        far += w[i] * float(m[i, i + FAR_NOTCHES:D_INDEX].sum())
    return near, far


def _downgrade_mass(m: np.ndarray, w: np.ndarray) -> float:
    """Mix-weighted probability of any downgrade, default excluded.

    Over every row that has a worse grade to move to, so CCC/C contributes
    nothing. Default is excluded deliberately: the point of the statistic is to
    ask whether the MIGRATION body responds to the macro path, and a model that
    moves only its default column would otherwise pass on the strength of the
    one column that is already scored.
    """
    return float(sum(w[i] * m[i, i + 1:D_INDEX].sum() for i in range(D_INDEX - 1)))


def notch_diagnostics(text: str | None, start: np.ndarray,
                      truth: dict) -> dict[str, float]:
    """Shape of the submitted matrices: the far corner, and the macro response.

    Two questions that nothing else here asks, both reported and neither scored.

    FIRST, the upper right corner. A quarterly matrix obtained by rooting or
    exponentiating an annual one carries multi-grade mass correctly, because that
    operation is the exact inverse of compounding. What does not survive is the
    CONDITIONING: under the threshold-shift law that generates these instances,
    a worse factor moves every threshold at once, so the far cells grow faster
    than the near ones. Measured on the oracle at rho 0.109, the share of AAA
    downgrade mass that travels two grades or more runs 0.033 at z = 0 and 0.147
    at z = 4, and the absolute three-grade-or-worse mass grows by more than an
    order of magnitude over the same range. A model that freezes its migration
    body and moves only the default column keeps that share fixed, and the
    distortion is concentrated exactly where the user of a stress test looks:
    the investment-grade rows, in the trough quarters.

    `matrix_down3_ratio` is the submitted far mass over the oracle's, pooled over
    every scenario and quarter. Pooling the two sums rather than averaging their
    ratios is deliberate: the denominator is largest in the stressed quarters, so
    those quarters dominate without any need to choose a stress window.

    `matrix_down1_ratio` is the same ratio on the adjacent-grade band, over the
    same rows, and it is the control. A model that is uniformly too mild reads
    low on both. `matrix_down3_shape` divides the far ratio by the near ratio and
    is therefore blind to a uniform error of level: it reads about one when the
    far corner is no more distorted than the body, and well below one when the
    tail specifically has been thinned.

    The far ratio is an exact measurement rather than a proxy. Thinning the
    oracle's far corner to a fixed fraction of itself and folding the remainder
    into the two-notch cell, so that rows still close and the default column is
    untouched, makes it read that fraction back: 0.750, 0.500, 0.250, 0.100 and
    0.000 for those five submissions, identically on all twelve instances. What
    bounds the usable sensitivity is not the statistic but the scatter of an
    honest estimate. Over twelve instances the shipped one-factor reference reads
    0.55 to 4.09 on the far ratio and 0.74 to 3.42 on the shape, with medians
    1.31 and 1.57; it OVERSTATES the far corner, because it estimates its base
    from twenty years that contain stressed ones and so inherits a tail fattened
    by the cycle. So a reading below about 0.5 is a finding and a reading above
    one is not, which is the same one-sided convention the stress diagnostics
    use. That calibration is seed-set dependent and should not be promoted to a
    gate as it stands: these twelve instances are `generate(seed=k)` for k in
    1..12, and over the first twelve the task actually draws the reference reads
    0.354 to 5.079 with median 1.043, dipping below 0.5 on one of them. See
    docs/tasks/migration.md.

    The score cannot do this work. Collapsing the far corner entirely moves the
    composite from 0.000-0.003 to 0.011-0.020 over those twelve instances,
    against a reference composite of 0.285. A submission can abolish every
    three-notch downgrade and still score two orders of magnitude better than the
    anchor, which is why this is measured separately and why it is measured
    against the oracle rather than inferred from the projection.

    SECOND, whether the migration body moves with the macros at all. Default is
    excluded from every statistic in this group, so a model cannot pass on the
    strength of a default column it fitted separately.

    `matrix_downgrade_concordance` is the fraction of matrix pairs, ordered by
    the true factor, whose submitted downgrade mass moves the same way as the
    factor. A near-tie counts as DISCORDANT here, which is the opposite of the
    convention in `one_model_discordance` and is the point: a frozen body is the
    failure being looked for, so it has to read zero rather than drop out for
    want of comparable pairs. `matrix_downgrade_slope` separates a flat body from
    a perverse one, since both read zero on concordance; it is the slope of log
    downgrade mass on the factor, an elasticity, with the oracle's slope reported
    beside it for scale. `matrix_downgrade_response` is the cruder version a
    reviewer can check by hand, the downgrade mass in the worst quarter divided
    by the mass in the mildest.

    Measured over twelve instances on 351 comparable pairs each: the oracle reads
    concordance 1.000 and a slope of 0.72 to 1.12. A model that holds its
    migration body at the long-run average and moves only the default column
    reads concordance 0.000 on every instance, with a slope of -0.022 to -0.0015,
    flat to within noise and faintly perverse because renormalising the row to
    absorb a rising default probability shrinks every migration cell. The shipped
    reference reads 0.846 to 0.994, median 0.963, and a slope of 0.66 to 1.25
    against the oracle's 0.72 to 1.12: it responds, with the ordering errors its
    estimated factor makes. So concordance separates no response at all from an
    imperfect one by a clear margin, and it does not pretend to grade the quality
    of a response that exists.

    The two groups are deliberately independent, and each is blind where the
    other sees. Folding all multi-notch mass into the adjacent grade leaves the
    total downgrade mass unchanged, so it reads concordance 1.000 and the
    oracle's own slope while the far ratio reads 0.000. A frozen body leaves the
    far corner's SHAPE roughly intact, reading 0.39 to 1.19 on the shape ratio
    and so overlapping the reference's honest range, while concordance reads
    exactly 0.000. Neither group alone would catch both failures.

    The oracle is rebuilt here from `quarterly_base`, the factor path in truth
    and the drawn correlation, so these are comparisons against the exact
    conditional law rather than against a convention. Submitted quarters are
    paired with the factor path positionally after sorting, as in
    `matrix_submission_gap`, so a submission that numbers its quarters from the
    end of the history rather than from one is still read correctly.

    Everything returns an empty dict rather than a NaN-filled one when there is
    nothing to measure, so `score_value` can fill the keys itself.
    """
    from pereval.tasks.migration.generator import conditional_matrix, quarterly_base

    mats = parse_matrices(text)
    rho = truth.get("rho")
    scenarios = truth.get("scenarios") or {}
    if not mats or rho is None:
        return {}

    w = _row_weights(start)
    base = quarterly_base()
    rows: list[tuple[float, float, float, float, float, float]] = []
    for name in sorted(mats):
        z_path = (scenarios.get(name) or {}).get("z_scenario")
        if not z_path:
            continue
        for q, z in zip(sorted(mats[name]), [float(x) for x in z_path]):
            sub = mats[name][q]
            orc = conditional_matrix(base, z, float(rho))
            near_s, far_s = _band_masses(sub, w)
            near_o, far_o = _band_masses(orc, w)
            rows.append((z, near_s, far_s, near_o, far_o,
                         _downgrade_mass(sub, w)))
    if not rows:
        return {}

    z = np.array([r[0] for r in rows])
    near_s, far_s = sum(r[1] for r in rows), sum(r[2] for r in rows)
    near_o, far_o = sum(r[3] for r in rows), sum(r[4] for r in rows)
    down = np.array([r[5] for r in rows])
    down_o = np.array([_downgrade_mass(conditional_matrix(base, zz, float(rho)), w)
                       for zz in z])

    out = {
        "matrix_down3_mass": far_s / len(rows),
        "matrix_down3_mass_oracle": far_o / len(rows),
        "matrix_down1_ratio": float(near_s / near_o) if near_o > 0 else float("nan"),
        "matrix_down3_ratio": float(far_s / far_o) if far_o > 0 else float("nan"),
    }
    if near_o > 0 and far_o > 0 and near_s > 0:
        out["matrix_down3_shape"] = float((far_s / far_o) / (near_s / near_o))
    else:
        out["matrix_down3_shape"] = float("nan")

    order = np.argsort(z)
    concordant = pairs = 0
    for a in range(len(order)):
        for b in range(a + 1, len(order)):
            i, j = order[a], order[b]
            if _tied(z[i], z[j]):
                continue
            pairs += 1
            concordant += int(not _tied(down[i], down[j])
                              and (down[j] - down[i]) * (z[j] - z[i]) > 0)
    out["matrix_downgrade_pairs"] = float(pairs)
    out["matrix_downgrade_concordance"] = (concordant / pairs if pairs
                                           else float("nan"))
    out["matrix_downgrade_response"] = float(
        down[int(np.argmax(z))] / down[int(np.argmin(z))]
        if down[int(np.argmin(z))] > 0 else float("nan"))
    out["matrix_downgrade_response_oracle"] = float(
        down_o[int(np.argmax(z))] / down_o[int(np.argmin(z))])
    out["matrix_downgrade_slope"] = _log_slope(z, down)
    out["matrix_downgrade_slope_oracle"] = _log_slope(z, down_o)
    return out


def _log_slope(x: np.ndarray, y: np.ndarray) -> float:
    """Least-squares slope of log y on x. NaN when it cannot be formed.

    The log is taken because the oracle's response is multiplicative: a threshold
    shift scales the far cells by a factor rather than adding to them. A floor
    keeps a submitted zero from taking the whole statistic to negative infinity,
    at the cost of reading such a submission as merely very small.
    """
    if len(x) < 2 or float(np.ptp(x)) <= 0.0:
        return float("nan")
    ly = np.log(np.maximum(np.asarray(y, dtype=float), 1e-15))
    xc = np.asarray(x, dtype=float) - np.mean(x)
    return float(np.dot(xc, ly - ly.mean()) / np.dot(xc, xc))


def parse_backtest(text: str | None) -> dict[int, float]:
    """`backtest.csv`: the model's own fitted annual default rate, by year."""
    if not text:
        return {}
    out: dict[int, float] = {}
    for row in csv.DictReader(io.StringIO(text)):
        try:
            out[int(float(row["year"]))] = float(row["default_rate"])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def fit_diagnostics(text: str | None, observed) -> dict[str, float]:
    """One-sided check on the model's fit to the stressed part of its own history.

    This is the backtest a developer draws before anyone else sees the model:
    observed annual default rate against the rate the model says those years
    should have had. The agent reports its own fitted rates, so nothing is
    reverse engineered from its projection.

    Read one-sided, on the stressed quarter of the historical years. Understating
    losses in the bad years is the failure that matters; overstating them is
    conservative, and a bank survives its benign years whatever the model claims
    about them. So a ratio below one is a finding and a ratio above one is not.

    On a sensitivity sweep of the reference, scaling its macro response by 0,
    0.25, 0.5, 0.75, 1.0 and 1.5, `fit_stress_mean_ratio` runs 0.26, 0.32, 0.40,
    0.51, 0.66 and 1.07. Monotone, a factor of four across the sweep, and it
    requires no interval. The shipped reference itself reads 0.66, because the
    shrinkage that stops it blowing out on the projection also damps its macro
    response; that is a real limitation of the anchor rather than a scoring
    artefact, which is the clearest evidence that this diagnostic bites.

    It cannot detect the opposite failure. The fit is in sample, so a model that
    overfits history scores well here. That is deliberate: this is a check for
    insufficient macro sensitivity, and the forward statistics in
    `stress_diagnostics` cover the other direction.

    One blind spot is worth naming precisely, because an agent walked into it.
    A backtest has no power at all against a model that interpolates history and
    cannot extrapolate past it, since that model's only defect lies outside the
    period the backtest covers. Asked for nine quarters whose peak volatility
    exceeded anything in its sample, a nearest-neighbour submission scored
    `fit_stress_mean_ratio` 1.0004 and `fit_peak_ratio` 1.0003 here while
    projecting 13% of the true stress response forward. So these statistics are
    read as a pair with `stress_mean_ratio`, and their disagreement is itself the
    diagnosis: both low is a weak model, high here and low forward is a model
    that cannot leave its own sample.

    `fit_peak_prominence` is the statistic to read rather than `fit_peak_lag`.
    Over the same sweep it runs 0.09, 0.12, 0.19, 0.32, 0.51, 1.17, a span of
    thirteen against the stress ratio's four, and at zero sensitivity it reads
    0.09 instead of leaving the reviewer to infer flatness. The lag is kept
    because mistiming a peak is a real finding, but it is suppressed below a
    prominence of 0.25: of twenty-four instances the one with prominence 0.17
    reported a lag of sixteen years, and the other twenty-three, all above 0.39,
    reported exactly zero. A series with no peak has no peak to time.
    """
    obs = np.asarray(list(observed), dtype=float)
    fit = parse_backtest(text)
    if obs.size == 0 or not fit:
        return {"fit_provided": 0.0}
    years = sorted(fit)
    pred = np.array([fit[y] for y in years], dtype=float)
    out = {"fit_provided": 1.0, "fit_years": float(len(years))}
    if pred.size != obs.size:
        return out                      # wrong length: nothing comparable
    stressed = obs >= np.quantile(obs, 0.75)
    if obs[stressed].mean() > 0.0:
        out["fit_stress_mean_ratio"] = float(pred[stressed].mean()
                                             / obs[stressed].mean())
    if obs.max() > 0.0:
        out["fit_peak_ratio"] = float(pred[int(np.argmax(obs))] / obs.max())
    if obs.mean() > 0.0:
        out["fit_all_years_ratio"] = float(pred.mean() / obs.mean())
    spread = obs.max() - float(np.median(obs))
    if spread > 0.0:
        prom = (pred.max() - float(np.median(pred))) / spread
        out["fit_peak_prominence"] = float(prom)
        if prom >= PROMINENCE_FLOOR:     # below this there is no peak to time
            out["fit_peak_lag"] = float(int(np.argmax(pred)) - int(np.argmax(obs)))
    return out


def stress_diagnostics(text: str | None, start: np.ndarray,
                       submitted: dict[str, dict[int, np.ndarray]],
                       truth: dict) -> dict[str, float]:
    """One-sided check on the model's response under stress, reported not scored.

    A stress test is asked one question: how large are losses under a given
    scenario. Understating them is the failure that matters, because a bank
    survives benign quarters whatever the model says about them and an
    overstatement is conservative rather than wrong. So every statistic here is
    a ratio of submitted to true, and only values below one are findings. There
    is no upper limit and no two-sided band.

    The headline is `stress_mean_ratio`, the submitted mean quarterly loss over
    the stressed half of the horizon divided by the true mean over those same
    quarters. On a sensitivity sweep of the reference, scaling its macro
    response from zero to one and a half, this ratio runs 0.26, 0.32, 0.40,
    0.51, 0.66, 1.07. It is monotone, it spans a factor of four, and it needs no
    interval construction.

    The headline is taken from the MOST SEVERE scenario the instance carries,
    not averaged over the three. Two reasons. The severe path is the one that
    pushes the systematic factor outside its historical range, so it is the only
    one that tests extrapolation rather than interpolation, and a model that
    cannot leave its own sample reads near one on baseline and low here. And
    averaging would let a conservative baseline offset an understated severe,
    which is exactly the trade a stress reviewer refuses. The per-scenario
    ratios are reported alongside so the gradient is visible.

    `stress_peak_ratio` compares the peaks, and `stress_peak_lag` the timing: a
    model may get the level right and put the peak in the wrong quarter, which a
    reviewer reads off the chart immediately and no distance metric at a
    checkpoint can see.

    The checkpoint ratios come from `predictions.csv` alone, so they survive a
    submission that omits the matrices.
    """
    names = list(truth.get("scenario_names") or truth["scenarios"])
    headline = names[-1]
    mats = parse_matrices(text)
    out: dict[str, float] = {}
    for name in names:
        tscen = truth["scenarios"][name]
        got = submitted.get(name, {})
        true_cum = {int(q): float(v["D"])
                    for q, v in tscen["rating_distribution"].items()}
        for q, cum in sorted(true_cum.items()):
            if q in got and cum > 0.0:
                ratio = float(got[q][D_INDEX] / cum)
                if name == headline:
                    out[f"default_ratio_q{q}"] = ratio

        inc_true = np.asarray(tscen.get("default_increments", ()), dtype=float)
        scen_mats = mats.get(name, {})
        if inc_true.size == 0 or len(scen_mats) < inc_true.size:
            continue
        v, inc_sub = start.copy(), []
        prev = float(start[D_INDEX])
        for q in sorted(scen_mats)[:inc_true.size]:
            v = v @ scen_mats[q]
            inc_sub.append(float(v[D_INDEX]) - prev)
            prev = float(v[D_INDEX])
        inc_sub = np.asarray(inc_sub, dtype=float)

        # the stressed half of the horizon, chosen on the truth so that a model
        # cannot define its own stress window
        stressed = inc_true >= np.median(inc_true)
        denom_mean = float(inc_true[stressed].mean())
        denom_peak = float(inc_true.max())
        if denom_mean > 0.0:
            mean_ratio = float(inc_sub[stressed].mean() / denom_mean)
            out[f"stress_mean_ratio_{name}"] = mean_ratio
            if name == headline:
                out["stress_mean_ratio"] = mean_ratio
        if denom_peak > 0.0 and name == headline:
            out["stress_peak_ratio"] = float(inc_sub.max() / denom_peak)
        # a flat path has no peak to be early or late
        if name == headline and float(np.ptp(inc_sub)) > 0.0:
            out["stress_peak_lag"] = float(
                int(np.argmax(inc_sub)) - int(np.argmax(inc_true)))
    return out


#: Every key reported for this task, which is the contract with aggregation.
#: Inspect averages a keyed metric by pulling the key from each sample's score
#: value: absent raises, NaN is skipped. Since every diagnostic is conditional
#: on something, `score_value` fills what does not apply with NaN.
REPORTED_KEYS = (
    "score_degenerate",
    *(f"score_{n}" for n in SCENARIO_KEYS),
    *(f"{c}_{n}_q{q}_norm" for n in SCENARIO_KEYS
      for c in ("ks", "default") for q in (4, 9)),
    "default_rate_bias", "hosmer_lemeshow",
    "completion", "runs", "regret_worst", "regret_spread",
    # diagnostics only: deliberately excluded from `score`
    "matrix_provided", "matrix_rows_valid", "matrix_nonnegative",
    "matrix_admissible", "matrix_scenarios", "matrix_row_sum_error",
    "matrix_rows_off_one", "matrix_negative_cells", "matrix_most_negative",
    "matrix_zero_cells", "matrix_smallest_positive",
    "matrix_default_monotonicity_violations",
    "matrix_one_model_discordance", "matrix_submission_gap",
    # shape of the matrices: the far downgrade corner, and whether the
    # migration body responds to the macro path at all
    "matrix_down3_mass", "matrix_down3_mass_oracle",
    "matrix_down1_ratio", "matrix_down3_ratio", "matrix_down3_shape",
    "matrix_downgrade_pairs", "matrix_downgrade_concordance",
    "matrix_downgrade_response", "matrix_downgrade_response_oracle",
    "matrix_downgrade_slope", "matrix_downgrade_slope_oracle",
    # one-sided stress response, also diagnostics only
    "default_ratio_q4", "default_ratio_q9", "stress_mean_ratio",
    *(f"stress_mean_ratio_{n}" for n in SCENARIO_KEYS),
    "stress_peak_ratio", "stress_peak_lag",
    "fit_provided", "fit_years", "fit_stress_mean_ratio", "fit_peak_ratio",
    "fit_all_years_ratio", "fit_peak_prominence", "fit_peak_lag",
)


def score_value(truth: dict, text: str | None, mtext: str | None,
                btext: str | None) -> dict[str, float]:
    """The whole score dictionary, so it can be built without a sandbox."""
    v = score_predictions(truth, text)
    start = np.array([truth["start_mix"].get(s, 0.0) for s in ORDER], dtype=float)
    submitted = parse_predictions(text)
    names = list(truth.get("scenario_names") or truth["scenarios"])
    checkpoints = [int(q) for q in
                   truth["scenarios"][names[0]]["rating_distribution"]]
    v.update(matrix_diagnostics(mtext, start, submitted, checkpoints))
    v.update(notch_diagnostics(mtext, start, truth))
    v.update(stress_diagnostics(mtext, start, submitted, truth))
    v.update(fit_diagnostics(btext, truth.get("observed_annual_default_rate", ())))
    for k in REPORTED_KEYS:
        v.setdefault(k, float("nan"))
    return v


def explain(v: dict[str, float]) -> str:
    """The one line a reader sees per sample, skipping what did not apply."""
    import math

    bits = [f"score {v['score']:.4f} (1.0 = no migration)",
            "by scenario " + "/".join(
                f"{v[f'score_{n}']:.3f}" for n in SCENARIO_KEYS
                if f"score_{n}" in v),
            f"completion {v['completion']:.0%}"]
    for key, label, fmt in (("matrix_down3_shape", "far-corner shape", ".2f"),
                            ("matrix_downgrade_concordance", "macro response", ".1%"),
                            ("default_rate_bias", "default bias", "+.3%"),
                            ("stress_mean_ratio", "severe stress response", ".2f"),
                            ("fit_stress_mean_ratio", "backtest stress", ".2f"),
                            ("matrix_one_model_discordance", "cross-scenario discordance",
                             ".1%")):
        x = v.get(key, float("nan"))
        if not math.isnan(x):
            suffix = "x" if fmt == ".2f" else ""
            bits.append(f"{label} {x:{fmt}}{suffix}")
    return "; ".join(bits)


def migration_scorer():
    from inspect_ai.scorer import Score, mean, scorer, stderr
    from inspect_ai.util import sandbox

    @scorer(name="migration",
            metrics={"score": [mean(), stderr()],
                     **{k: [mean()] for k in REPORTED_KEYS}})
    def factory():
        async def score(state, target):
            files = {}
            for name in ("predictions.csv", "matrices.csv", "backtest.csv"):
                try:
                    files[name] = await sandbox().read_file(name)
                except FileNotFoundError:
                    files[name] = None
            v = score_value(state.metadata["truth"], files["predictions.csv"],
                            files["matrices.csv"], files["backtest.csv"])
            return Score(value=v, explanation=explain(v))

        return score

    return factory()
