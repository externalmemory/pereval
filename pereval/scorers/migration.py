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

#: Floor on a degenerate value before dividing, for instances where the
#: uninformative answer happens to be nearly right on one component.
DEGENERATE_FLOOR = 1e-4

#: Near-tie tolerance wherever an ordering is read off submitted numbers,
#: relative plus absolute. An agent writes its matrices to a CSV at whatever
#: precision it chooses, and six decimals on a default probability of 1e-3
#: leaves differences between adjacent quarters at the rounding step. Without a
#: relative floor those rounded ties flip at random and a compliant submission
#: is credited with distinctions it never made.
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

#: The scenario label the fitted HISTORICAL matrices are submitted under. There
#: is one history, so it is written once rather than once per scenario. The
#: oracle-relative diagnostics are built against the nine scenario quarters and
#: would be corrupted by eighty more, so `parse_matrices` drops this block and
#: only the checks, which need no oracle, read it.
HISTORY_SCENARIO = "history"


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

    The `history` block is dropped here. Every diagnostic downstream of this
    parser is measured against the oracle over the nine scenario quarters, and
    eighty historical quarters with no oracle behind them would be pooled into
    the same sums. `_raw_matrix_blocks` keeps it for the checks.
    """
    if not text:
        return {}
    raw: dict[tuple[str, int], dict[str, np.ndarray]] = {}
    for row in csv.DictReader(io.StringIO(text)):
        try:
            scen = str(row["scenario"]).strip()
            if scen == HISTORY_SCENARIO:
                continue
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
        return {}
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

    # Counts and magnitudes only. The verdicts that used to live here, one
    # boolean per tier plus a conjunction over all of them, have been removed as
    # duplicates of the binary checks, which ask the same questions of the RAW
    # blocks rather than of this repaired parse and are therefore the stricter
    # reading: see `matrix_rows_sum_to_one`, `matrix_cells_are_probabilities`
    # and `matrices_readable`. The conjunction was worse than redundant. It
    # included "no exact zero anywhere", which almost every submission trips,
    # so it read 0.0 on eight of the nine submissions of the first live run,
    # two of which failed no check at all.
    #
    # The tiers themselves still matter and are still pinned by the tests. Rows
    # not summing to one is the consequential defect: scaling every row to 1.2
    # drives the submission gap from 0.0000 to 2.5163, because mass
    # non-conservation compounds over the horizon. A single small negative
    # leaves mass conserved and moves the same gap to 0.0001, so clipping it is
    # a defensible remedy. Exact zeros and a non-monotone default ordering leave
    # a valid distribution that is imprudent or odd.
    quarters_per = {len(v) for v in per_scenario.values()}
    out = {
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
    1..12, and over the twenty four the task draws at base seed 1 the reference
    reads 0.301 to 5.107 with median 1.039, dipping below 0.5 on four of them.
    See docs/tasks/migration.md.

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
    factor. A near-tie counts as DISCORDANT here, which is
    deliberate: a frozen body is the failure being looked for, so it has to read
    zero rather than drop out for want of comparable pairs. `matrix_downgrade_slope` separates a flat body from
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


def parse_backtest_by_scenario(text: str | None) -> dict[str, dict[int, float]]:
    """`backtest.csv` keyed by scenario, then year.

    The file carries a `scenario` column so that the three historical fits can
    be compared with each other. A file written without one is read as a single
    series under the key "", which is what archived submissions look like.
    """
    if not text:
        return {}
    out: dict[str, dict[int, float]] = {}
    for row in csv.DictReader(io.StringIO(text)):
        try:
            year = int(float(row["year"]))
            rate = float(row["default_rate"])
        except (KeyError, TypeError, ValueError):
            continue
        scen = str(row.get("scenario") or "").strip()
        out.setdefault(scen, {})[year] = rate
    return out


def parse_backtest(text: str | None) -> dict[int, float]:
    """`backtest.csv` as one series, for the statistics that need only one.

    When the file carries three scenarios they should be identical, and whether
    they are is the whole point of `historical_fit_identical_across_scenarios`.
    This returns the first by name so that the fit statistics read a definite
    series rather than an average of three disagreeing ones, which would hide
    the disagreement in exactly the statistic least able to show it.
    """
    by_scen = parse_backtest_by_scenario(text)
    if not by_scen:
        return {}
    return by_scen[sorted(by_scen)[0]]


def fit_diagnostics(text: str | None, observed) -> dict[str, float]:
    """One-sided check on the model's fit to the stressed part of its own history.

    This is the backtest a developer draws before anyone else sees the model:
    observed annual default rate against the rate the model says those years
    should have had. The agent reports its own fitted rates, so nothing is
    reverse engineered from its projection.

    `fit_stress_mean_ratio` was reported here and has been REMOVED. It was the
    mean fitted rate over the worst quartile of observed years divided by the
    mean observed rate over the same years, read one-sided, and it was dropped
    for a reason worth recording rather than a doubt about whether it measured
    something.

    The statistic was sound. Built from the true factor path and the true
    correlation, a perfectly specified model reads 0.966 to 1.029 over twelve
    instances, mean 0.992, so selecting the worst quartile of observed years
    biases it by about one percent and no more. The shipped reference reads 0.480
    to 0.781, mean 0.637, with no overlap: the shrinkage that stops it blowing
    out on the projection is the same parameter that damps its macro response.

    That is what made it unusable as a check rather than what saved it. A
    diagnostic has to be one a competent estimate can clear, or it reports the
    bias-variance trade every estimator on twenty years of history has to make
    as though it were a defect. Reading it one-sided below one needs a threshold
    nobody can defend, and a denominator-free restatement does not help: the
    number of stressed years in which the fit falls below observed convicts the
    reference on six of twelve instances and the true model on none. The
    `fail_*` checks cover what remains testable here without a threshold.

    It cannot detect the opposite failure. The fit is in sample, so a model that
    overfits history scores well here. That is deliberate: this is a check for
    insufficient macro sensitivity, and the forward statistics in
    `stress_diagnostics` cover the other direction.

    One blind spot is worth naming precisely, because an agent walked into it.
    A backtest has no power at all against a model that interpolates history and
    cannot extrapolate past it, since that model's only defect lies outside the
    period the backtest covers. Asked for nine quarters whose peak volatility
    exceeded anything in its sample, a nearest-neighbour submission scored
    `fit_all_years_ratio` 1.0004 and `fit_peak_ratio` 1.0003 here while
    projecting 13% of the true stress response forward. So these statistics are
    read as a pair with `stress_mean_ratio`, and their disagreement is itself the
    diagnosis: both low is a weak model, high here and low forward is a model
    that cannot leave its own sample.

    `fit_peak_prominence` is the height of the fitted peak above the fitted
    median over the height of the observed peak above the observed median, so a
    level bias cancels and only the peak's size relative to a typical year
    counts. Over the same sweep it runs 0.09, 0.12, 0.19, 0.32, 0.51, 1.17, a
    span of thirteen against the stress ratio's four, and at zero sensitivity it
    reads 0.09 rather than leaving the reviewer to infer flatness.

    `fit_peak_lag` has been REMOVED, and the reason is worth keeping. It was the
    signed year distance between the two argmaxes, gated on a prominence of
    0.25 so that a flat series was not timed. The gate was not the problem. An
    argmax is, because shrinkage compresses the worst few fitted years toward
    each other and the argmax of a competent estimate on twenty years of
    history is then near-arbitrary among them. The shipped reference read a
    nonzero lag on eight of twenty four served instances, up to eleven years.
    On the worst of those its fitted values at the two years being compared
    differ by 0.04 percentage points, two percent of the fitted peak, and the
    lag reported that coin flip as an eleven year mistiming; across the eight
    the fitted gap runs 1.7% to 41.3% of the fitted peak, half of it under 20%.
    The observed side is no better: six of twenty four instances have an
    observed peak within 25% of its runner-up and two within 10%, and on one of
    those the two worst years are seventeen years apart, so the sign of the
    statistic turns on a tie. What the lag was reporting is shrinkage, which
    `fit_peak_ratio` already reports directly: on the same eight instances it
    runs 0.24 to 0.60. A diagnostic has to be one a competent estimate can
    clear, which is the rule that removed `fit_stress_mean_ratio` as well.
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
    if obs.max() > 0.0:
        out["fit_peak_ratio"] = float(pred[int(np.argmax(obs))] / obs.max())
    if obs.mean() > 0.0:
        out["fit_all_years_ratio"] = float(pred.mean() / obs.mean())
    spread = obs.max() - float(np.median(obs))
    if spread > 0.0:
        out["fit_peak_prominence"] = float(
            (pred.max() - float(np.median(pred))) / spread)
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


#: Tolerance on an identity a submission must satisfy exactly in principle: a
#: row of probabilities summing to one, a set of shares summing to one. The task
#: asks for at least six decimal places, so a row inside this is a rounded
#: correct answer and a row outside it is a real error rather than formatting.
IDENTITY_TOL = 1e-4

#: Every check, in report order. Each is a property a credit risk reviewer would
#: assert without argument, and the value reported for it is one when it FAILS,
#: so the mean over samples is the fraction of submissions carrying that finding.
#:
#: Three rules govern what is allowed to be a check.
#:
#: It must be defensible without the answer key. A statistic measured against
#: the oracle cannot be a check, because its threshold would have to be
#: calibrated against the spread of a competent estimate, and that spread is
#: wide: the shipped reference's far-corner ratio runs 0.301 to 5.107 across the
#: twenty four instances the task draws at base seed 1, dipping below 0.5 on
#: four of them, so no cut on it separates a thinned submission from an honest
#: one. The same failure stated as "the model gives a three notch
#: downgrade zero probability" needs neither the oracle nor a threshold.
#:
#: It must be computable on every submission. A ratio whose denominator can be
#: zero, or a rank correlation whose comparable pairs can all be ties, returns
#: NaN, and NaN is neither a pass nor a fail. Where the measured diagnostics
#: produced one, the check is restated as an ordering, which always exists.
#:
#: An absent or unreadable artefact fails every check that reads it rather than
#: being excused from it. A model nobody can inspect has demonstrated none of
#: these properties, and excusing it would let a missing file outrank a bad
#: answer. The count is then monotone in how much is wrong.
CHECK_KEYS = (
    "matrices_readable",
    "matrix_cells_finite",
    "matrix_cells_are_probabilities",
    "matrix_rows_sum_to_one",
    "predictions_readable",
    "prediction_shares_finite",
    "prediction_shares_sum_to_one",
    "pd_rises_as_rating_falls",
    "stay_is_the_most_likely_outcome",
    "multinotch_downgrade_possible",
    "downgrades_rise_with_severity",
    "pd_rises_with_severity",
    "implied_pd_rises_with_severity",
    "pd_rises_with_horizon",
    "fitted_downgrades_rise_in_bad_years",
    "historical_fit_identical_across_scenarios",
)


def _raw_matrix_blocks(text: str | None) -> dict[str, dict[int, np.ndarray]]:
    """Submitted matrix cells with nothing repaired.

    `parse_matrices` discards a whole file that holds one non-finite cell, which
    makes "wrote NaN where a probability belongs" indistinguishable from "wrote
    no file at all". A NaN is a hard failure and has to be counted as one, so
    this keeps the values exactly as submitted and leaves judging them to the
    checks. Returns {} only when the CSV cannot be read as the requested shape.
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
        if frm not in LIVE_STATES:
            return {}
        raw.setdefault((scen, q), {})[frm] = vals
    out: dict[str, dict[int, np.ndarray]] = {}
    for (scen, q), rows in raw.items():
        if set(rows) != set(LIVE_STATES):
            return {}
        m = np.zeros((len(ORDER), len(ORDER)))
        for i, st in enumerate(LIVE_STATES):
            m[i] = rows[st]
        m[D_INDEX, D_INDEX] = 1.0
        out.setdefault(scen, {})[q] = m
    return out


def _raw_prediction_blocks(text: str | None) -> dict[str, dict[int, np.ndarray]]:
    """Submitted shares with nothing repaired, for the same reason.

    `parse_predictions` renormalises a block that sums to anything between 0.5
    and 1.5, which is right for scoring and wrong for checking, since it hides
    the very error `prediction_shares_sum_to_one` exists to find.
    """
    if not text:
        return {}
    raw: dict[tuple[str, int], dict[str, float]] = {}
    for row in csv.DictReader(io.StringIO(text)):
        try:
            scen = str(row["scenario"]).strip()
            q = int(float(row["quarter"]))
            state = str(row["state"]).strip()
            share = float(row["share"])
        except (KeyError, TypeError, ValueError):
            return {}
        if state not in ORDER:
            return {}
        raw.setdefault((scen, q), {})[state] = share
    out: dict[str, dict[int, np.ndarray]] = {}
    for (scen, q), d in raw.items():
        if set(d) != set(ORDER):
            return {}
        out.setdefault(scen, {})[q] = np.array([d[st] for st in ORDER], dtype=float)
    return out



def model_checks(mtext: str | None, ptext: str | None, btext: str | None,
                 start: np.ndarray, truth: dict) -> dict[str, float]:
    """One pass or fail per check, plus the count of failures.

    Reported as `fail_<name>` equal to one when the check fails, so that
    Inspect's mean over samples reads as the share of submissions carrying that
    finding, and `checks_failed` is how many of the fifteen this submission
    tripped.
    """
    names = list(truth.get("scenario_names") or truth.get("scenarios") or ())
    order = [n for n in SCENARIO_KEYS if n in names] or names
    mats = _raw_matrix_blocks(mtext)
    preds = _raw_prediction_blocks(ptext)
    w = _row_weights(start)
    checkpoints = sorted(int(q) for q in
                         (truth["scenarios"][names[0]]["rating_distribution"]
                          if names else {}))

    m_all = [m for scen in mats.values() for m in scen.values()]
    fail: dict[str, bool] = {}

    # Artefact integrity. Each of these is a hard failure: the submission is not
    # a set of probabilities, so nothing downstream of it can be believed.
    fail["matrices_readable"] = (not mats or len(mats) < len(order)
                                 or HISTORY_SCENARIO not in mats)
    fail["matrix_cells_finite"] = (not m_all
                                   or not all(np.isfinite(m).all() for m in m_all))
    fail["matrix_cells_are_probabilities"] = (
        not m_all or not all(np.all((np.nan_to_num(m, nan=-1.0) >= 0.0)
                                    & (np.nan_to_num(m, nan=2.0) <= 1.0))
                             for m in m_all))
    fail["matrix_rows_sum_to_one"] = (
        not m_all or not all(abs(m[i].sum() - 1.0) <= IDENTITY_TOL
                             for m in m_all for i in range(D_INDEX)))

    p_all = [v for scen in preds.values() for v in scen.values()]
    fail["predictions_readable"] = not preds or len(preds) < len(order)
    fail["prediction_shares_finite"] = (not p_all
                                        or not all(np.isfinite(v).all() for v in p_all))
    fail["prediction_shares_sum_to_one"] = (
        not p_all or not all(abs(np.nansum(v) - 1.0) <= IDENTITY_TOL
                             and np.all(np.nan_to_num(v, nan=-1.0) >= 0.0)
                             for v in p_all))

    # A lower rated obligor defaults more often. Weak, because two adjacent
    # grades carrying the same estimated probability is not a modelling error.
    fail["pd_rises_as_rating_falls"] = not m_all or any(
        m[i + 1, D_INDEX] < m[i, D_INDEX] - TIE_TOL_ABS
        for m in m_all for i in range(D_INDEX - 1))

    # Over one quarter a grade is likelier to persist than to migrate to any one
    # other grade. Two restrictions, both forced by the answer key breaking the
    # unrestricted rule, and both measured rather than assumed.
    #
    # Default is excluded as a destination: the oracle breaks dominance there,
    # because a CCC/C obligor in a severe quarter really is likelier to default
    # than to stay CCC/C. The only violations of the unrestricted rule are CCC/C
    # into default, nine of them on one instance, reaching stay 0.283 against
    # default 0.717.
    #
    # The HISTORY block is excluded as a source: the scenarios are bounded by
    # SEVERITY_CAP, the published history is not. Over 960 historical quarters
    # of the true model there is exactly one quarter that breaks dominance, at a
    # factor of +5.92, where AAA is likelier to be cut to AA than to stay AAA.
    # That is the law behaving correctly at an extreme, not a defect. Worse, the
    # shipped reference never reaches it, because its fitted factor is shrunk,
    # so checking the history here would convict a model whose historical fit is
    # MORE faithful than the anchor's. The check is about the matrices a model
    # projects, which is what a reviewer reviews.
    scen_m = [m for k, v in mats.items() if k != HISTORY_SCENARIO
              for m in v.values()]
    fail["stay_is_the_most_likely_outcome"] = not scen_m or any(
        m[i, i] < m[i, j] - TIE_TOL_ABS
        for m in scen_m for i in range(D_INDEX) for j in range(D_INDEX) if j != i)

    # Zero is not an estimate, it is an assertion that a three notch downgrade
    # cannot happen. This is the failure a tridiagonal or diffusion construction
    # produces, and it needs no oracle to state.
    #
    # The published history is not quiet about these cells. Measured on
    # data/transitions.csv over the twelve instances the task serves at base
    # seed 1, the three-or-worse band is 13.6x more frequent in the stressed
    # quarter of years than the benign ones (range 3.6 to 53.5, on all twelve),
    # against 3.3x for the adjacent notch.
    # The far corner is the MOST macro-sensitive region of the matrix, not a
    # structural detail the data is silent about, so a model that sets it to zero
    # is discarding its most responsive evidence.
    fail["multinotch_downgrade_possible"] = not m_all or any(
        m[i, i + FAR_NOTCHES:D_INDEX].sum() <= 0.0
        for m in m_all for i in range(D_INDEX - FAR_NOTCHES))

    # Stress makes downgrades more likely, default excluded so that a default
    # column fitted on its own cannot carry a frozen migration body. Strict,
    # because equality IS the frozen body.
    #
    # This asks for nothing the agent cannot see. In data/transitions.csv the
    # annual downgrade frequency correlates +0.918 to +0.988 with the annual
    # default rate over the twenty published years, and downgrades are 2.6 to
    # 5.7 times more frequent in the stressed quarter of years, on every one of
    # the twelve instances served at base seed 1 and from every starting grade
    # that has room to fall: 3.6x from AAA, 3.7x from AA, 4.1x from A, 4.5x from
    # BBB, 3.4x from BB and 2.9x from B, as means over the twelve. Upgrades move
    # the other way, to 0.15 to 0.66x. A submission that trips this check
    # contradicts its own history.
    # EVERY adjacent pair, not just the ends. Comparing only the mildest with
    # the worst passes a model whose middle scenario is out of order, and an
    # adverse projection that is not worse than baseline is the same defect as a
    # severe one that is not worse than adverse.
    if len(order) >= 2 and all(n in mats for n in order):
        def _down(scen, quarters):
            return sum(_downgrade_mass(mats[scen][q], w) for q in quarters)
        shared = sorted(set.intersection(*(set(mats[n]) for n in order)))
        fail["downgrades_rise_with_severity"] = not shared or any(
            not _down(b, shared) > _down(a, shared) + TIE_TOL_ABS
            for a, b in zip(order, order[1:]))
    else:
        fail["downgrades_rise_with_severity"] = True

    # Stress raises losses. Read off the scored artefact rather than the
    # matrices, so a model whose projection contradicts its own matrices is
    # caught by whichever of the two is wrong.
    def _pd(scen, q):
        v = preds.get(scen, {}).get(q)
        return None if v is None else float(v[D_INDEX])

    # Read at the LAST checkpoint only, which is the nine quarter cumulative
    # default rate, and not at every checkpoint. The severe scenario has a
    # trough by design, so its early quarters can be milder than the adverse
    # path's while its late quarters are far worse, and the ordering genuinely
    # inverts at quarter four. Measured on the true generating model over three
    # scans of forty eight instances, the quarter four comparison fails on 14 of
    # 288 pairs, by as much as 0.0100, while the quarter nine comparison never
    # fails once in the same 288. One of those quarter four inversions is on the
    # served draw at base seed 1: instance 4 puts severe at 0.92% against
    # adverse's 1.04% at quarter four and 3.63% against 2.57% at quarter nine.
    # A check the answer key breaks is a bug in the check, so the early
    # checkpoint is not asked about.
    #
    # Strict at the checkpoint that is asked, and the margin says it is
    # affordable: over four scans of twelve and twenty four instances, 192
    # comparisons, neither the oracle nor the reference fails once. The smallest
    # gap is 0.0104 for the oracle and 0.0113 for the reference, against a
    # relative tie tolerance of 1e-6. Weak inequalities
    # would pass a submission
    # predicting the same loss under every scenario, and would pass the
    # degenerate, whose cohort default share is exactly zero everywhere and so
    # satisfies every weak ordering that exists.
    pairs = [(a, b) for a, b in zip(order, order[1:])]
    terminal = [max(checkpoints)] if checkpoints else []
    vals = [(_pd(a, q), _pd(b, q)) for a, b in pairs for q in terminal]
    fail["pd_rises_with_severity"] = (
        not vals or any(x is None or y is None or _tied(x, y) or y < x
                        for x, y in vals))

    # Default is absorbing in the scored cohort, so its share cannot fall as the
    # horizon lengthens, and over five further quarters it cannot stand still
    # either unless the model predicts no defaults at all. Strict for the same
    # reason: over two scans of twenty four instances the oracle's smallest step
    # from quarter four to quarter nine is 0.0052 and the reference's is 0.0064,
    # on 288 comparisons with no failures. This one is within a scenario, so the
    # trough that disqualifies the early severity comparison does not touch it.
    steps = [(_pd(n, a), _pd(n, b)) for n in order
             for a, b in zip(checkpoints, checkpoints[1:])]
    fail["pd_rises_with_horizon"] = (
        not steps or any(x is None or y is None or _tied(x, y) or y < x
                         for x, y in steps))

    # The same ordering, asked of the MATRICES rather than the projection, by
    # propagating the published cohort mix through the submitted matrices and
    # reading the cumulative default share at the last checkpoint. The two are
    # not the same question. `pd_rises_with_severity` reads predictions.csv, and
    # a submission can file a monotone projection computed by some other route
    # while the matrices it documents are out of order in severity; nothing else
    # here would catch that, because `matrix_submission_gap` is reported rather
    # than checked and is a distance, not an ordering. Strict, and NaN or a
    # missing quarter fails rather than dropping out. Terminal checkpoint only,
    # for the trough reason given above.
    cum: dict[str, dict[int, float]] = {}
    horizon = max(checkpoints) if checkpoints else 0
    for scen in order:
        quarters = sorted(mats.get(scen, {}))
        if len(quarters) < horizon:
            continue
        v = np.concatenate([_row_weights(start), [0.0]])
        for t, q in enumerate(quarters, start=1):
            v = v @ mats[scen][q]
            if t in checkpoints:
                cum.setdefault(scen, {})[t] = float(v[D_INDEX])
    icum = [(cum.get(a, {}).get(q), cum.get(b, {}).get(q))
            for a, b in zip(order, order[1:]) for q in terminal]
    fail["implied_pd_rises_with_severity"] = (
        not icum or any(x is None or y is None
                        or not np.isfinite(x) or not np.isfinite(y)
                        or _tied(x, y) or y < x
                        for x, y in icum))

    # The fitted migration BODY has to move with the observed cycle. Everything
    # else about the history is checked through the default column alone, which
    # is one column of a seven by eight matrix: a model can reproduce twenty
    # years of default rates to five parts in ten thousand and still carry a
    # frozen body, and that is a failure this task has already seen twice. The
    # comparison is the five worst observed years against the five best, by the
    # observed annual default rate in data/transitions.csv, so it needs no
    # oracle.
    #
    # Three details earn their place, each measured rather than argued.
    #
    # A CORRELATION cannot be used. A time-homogeneous body has zero variance,
    # so the correlation is NaN on precisely the submission most in need of a
    # verdict, which is the defect that disqualified two statistics already.
    #
    # The years are split by RANK, not by quantile value. `obs >= quantile(.75)`
    # and `obs <= quantile(.25)` can overlap on a tied history, and an overlap
    # drives a correct model's gap to zero and fails it. Five highest against
    # five lowest is disjoint by construction.
    #
    # Every year is weighted by ONE fixed mix, so the statistic is a statement
    # about the matrices and not about portfolio drift. Weighting each year by
    # its own starting portfolio lets a constant body cross the split on
    # composition alone, measured passing on 4 of 24 instances. On a fixed mix a
    # constant body reads exactly zero and fails on all 24.
    #
    # Margins over 24 served instances, against a tie tolerance of 1e-9: the
    # oracle 1.41e-02, a fit to the observed default rates 1.91e-02, the shipped
    # reference, whose factor comes from macro and so never sees the sampling
    # noise that helped choose the split, 1.09e-02. A model keeping only five
    # percent of the reference's macro response still clears by 4.6e-04. A
    # constant body reads 0 and a sign-flipped one -1.91e-02. Resampling each
    # year's default count binomially and re-deriving the split, 8 instances by
    # 2000 draws, the reference's gap never fell below 9.3e-03 in 16,000 tries.
    hist = mats.get(HISTORY_SCENARIO, {})
    obs_annual = [float(x) for x in
                  (truth.get("observed_annual_default_rate") or ())]
    hq = sorted(hist)
    k = len(obs_annual) // 4
    if k < 1 or len(hq) != 4 * len(obs_annual):
        fail["fitted_downgrades_rise_in_bad_years"] = True
    else:
        per_year = np.array([
            float(np.mean([_downgrade_mass(hist[q], w) for q in hq[4 * y:4 * y + 4]]))
            for y in range(len(obs_annual))])
        ranked = np.argsort(np.asarray(obs_annual), kind="stable")
        worst, best = ranked[-k:], ranked[:k]
        fail["fitted_downgrades_rise_in_bad_years"] = (
            not np.isfinite(per_year).all()
            or not per_year[worst].mean() > per_year[best].mean() + TIE_TOL_ABS)

    # One model, tested where refitting cannot hide. The history does not depend
    # on which future scenario is being run, so a model estimated once implies
    # ONE fitted historical series and writes it three times. A model refitted
    # per scenario writes three different ones, and the difference is exact
    # rather than a matter of degree: no threshold, no denominator, and nothing
    # from the answer key. A submission that reports a single shared series
    # passes, because a single shared series is the correct answer.
    hist = parse_backtest_by_scenario(btext)
    series = [hist[k] for k in sorted(hist)]
    if len(series) < 2:
        fail["historical_fit_identical_across_scenarios"] = not series
    else:
        first = series[0]
        # `_tied` rather than IDENTITY_TOL: the question is whether two numbers
        # are the same to the precision a rounded CSV can carry, which is what
        # `_tied` already answers everywhere else in this module. IDENTITY_TOL is
        # an absolute 1e-4, and against an annual default rate of 0.017 that
        # would let a sixth of a percent of drift through as identical.
        fail["historical_fit_identical_across_scenarios"] = any(
            set(s) != set(first) or any(not _tied(s[y], first[y]) for y in first)
            for s in series[1:])

    out = {f"fail_{k}": float(bool(fail[k])) for k in CHECK_KEYS}
    out["checks_failed"] = float(sum(bool(fail[k]) for k in CHECK_KEYS))
    out["checks_total"] = float(len(CHECK_KEYS))
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
    "matrix_scenarios", "matrix_row_sum_error",
    "matrix_rows_off_one", "matrix_negative_cells", "matrix_most_negative",
    "matrix_zero_cells", "matrix_smallest_positive",
    "matrix_default_monotonicity_violations",
    "matrix_submission_gap",
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
    "fit_provided", "fit_years", "fit_peak_ratio",
    "fit_all_years_ratio", "fit_peak_prominence",
    # binary checks: one per defensible property, one when it FAILS, and the
    # count of failures. See CHECK_KEYS for what may be a check here.
    "checks_failed", "checks_total",
    *(f"fail_{k}" for k in CHECK_KEYS),
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
    v.update(model_checks(mtext, text, btext, start, truth))
    for k in REPORTED_KEYS:
        v.setdefault(k, float("nan"))
    return v


def explain(v: dict[str, float]) -> str:
    """The one line a reader sees per sample, skipping what did not apply."""
    import math

    nfail = v.get("checks_failed", float("nan"))
    failed = [k for k in CHECK_KEYS if v.get(f"fail_{k}", 0.0) >= 1.0]
    bits = [f"score {v['score']:.4f} (1.0 = no migration)"]
    if not math.isnan(nfail):
        bits.append(f"{int(nfail)}/{int(v['checks_total'])} checks failed"
                    + (": " + ", ".join(failed) if failed else ""))
    bits += [
            "by scenario " + "/".join(
                f"{v[f'score_{n}']:.3f}" for n in SCENARIO_KEYS
                if f"score_{n}" in v),
            f"completion {v['completion']:.0%}"]
    # No ratios are stated here any more. A line reading "far-corner shape 1.07x"
    # or "severe stress response 0.41x" asks the reader to decide whether a
    # number is a problem, and there is no reader of this line who can: these are
    # agent submissions in an eval, not models going to a review committee. What
    # replaced them is a count and the names of the properties that failed, which
    # is a finding rather than a measurement. The ratios stay in the score dict
    # as the evidence behind a flag, and `REPORTED_KEYS` still carries them.
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
            # The submitted artefacts are kept on the Score, not just the numbers
            # computed from them. Every diagnostic added after a run was scored
            # has so far required re-running the model, because the submission
            # existed only in the sandbox and the sandbox is gone: the binary
            # checks could not be applied to the runs already in logs/. About
            # 25 KB a sample buys the ability to answer the next question of this
            # shape off the archive instead of off the budget.
            return Score(value=v, explanation=explain(v), metadata=files)

        return score

    return factory()
