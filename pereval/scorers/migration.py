"""Score a projected rating-migration cohort on four equally weighted components.

The submission is the original cohort's distribution over seven rating grades
plus default, at two checkpoint quarters. From it the scorer derives four
components:

    KS on the live grades at quarter 4 and at quarter 9
    the cumulative default rate at quarter 4 and at quarter 9

Two components for migration shape, two for loss, and both checkpoints, so the
trajectory is tested rather than just the endpoint.

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

Measured on the one-factor reference over twelve instances, the four components
come out at 0.159, 0.104, 0.131 and 0.167, so the normalisation does equalise
them in practice and no single component drives the composite.

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


def parse_predictions(text: str | None) -> dict[int, np.ndarray]:
    """quarter,state,share rows into normalised 8-vectors, or {} if unusable."""
    if not text:
        return {}
    raw: dict[int, dict[str, float]] = {}
    seen: set[tuple[int, str]] = set()
    for row in csv.DictReader(io.StringIO(text)):
        try:
            q = int(float(row["quarter"]))
            state = str(row["state"]).strip()
            share = float(row["share"])
        except (KeyError, TypeError, ValueError):
            return {}
        if (q, state) in seen or state not in ORDER:
            return {}
        seen.add((q, state))
        raw.setdefault(q, {})[state] = share
    out = {}
    for q, d in raw.items():
        if set(d) != set(ORDER):
            return {}
        v = np.array([d[s] for s in ORDER], dtype=float)
        if not np.isfinite(v).all() or (v < 0).any():
            return {}
        total = v.sum()
        if not 0.5 <= total <= 1.5:
            return {}
        out[q] = v / total
    return out


def score_predictions(truth: dict, text: str | None) -> dict[str, float]:
    """truth needs rating_distribution (per checkpoint, 8 states) and start_mix."""
    dists = {int(q): np.array([v[s] for s in ORDER], dtype=float)
             for q, v in truth["rating_distribution"].items()}
    start = np.array([truth["start_mix"].get(s, 0.0) for s in ORDER], dtype=float)
    preds = parse_predictions(text)
    quarters = sorted(dists)

    raw, degen, norm = {}, {}, {}
    for q in quarters:
        t = dists[q]
        d_true = float(t[D_INDEX])
        degen[f"ks_q{q}"] = max(ks_distance(_live(start), _live(t)), DEGENERATE_FLOOR)
        degen[f"default_q{q}"] = max(abs(0.0 - d_true), DEGENERATE_FLOOR)
        p = preds.get(q)
        if p is None:
            raw[f"ks_q{q}"] = degen[f"ks_q{q}"]
            raw[f"default_q{q}"] = degen[f"default_q{q}"]
        else:
            raw[f"ks_q{q}"] = ks_distance(_live(p), _live(t))
            raw[f"default_q{q}"] = abs(float(p[D_INDEX]) - d_true)

    for k, v in raw.items():
        norm[k] = min(v / degen[k], COMPONENT_CAP)

    missing = sum(1 for q in quarters if q not in preds)
    result = {
        "score": float(np.mean(list(norm.values()))),
        "score_degenerate": 1.0,
        "completion": 1.0 - missing / len(quarters),
        "runs": 1.0,
        "regret_spread": 0.0,
    }
    result["regret_worst"] = result["score"]
    for k in raw:
        result[f"{k}_norm"] = norm[k]
        result[f"{k}_raw"] = raw[k]
    if not missing:
        last = max(quarters)
        result["default_rate_predicted"] = float(preds[last][D_INDEX])
        result["default_rate_true"] = float(dists[last][D_INDEX])
        result["default_rate_bias"] = (result["default_rate_predicted"]
                                       - result["default_rate_true"])
        result["hosmer_lemeshow"] = float(np.mean(
            [hosmer_lemeshow(_live(preds[q]), _live(dists[q])) for q in quarters]))
    return result


#: Column order of a submitted quarterly matrix, matching data/transitions.csv.
MATRIX_COLS = tuple(f"to_{s.replace('/', '_')}" for s in ORDER)


def parse_matrices(text: str | None) -> dict[int, np.ndarray]:
    """quarter,from_rating,to_* rows into {quarter: 8x8}. Permissive on purpose.

    This parser does NOT reject a matrix for being inadmissible. Negative mass,
    rows that miss one, exact zeros and non-monotone default are exactly what the
    diagnostics measure, so rejecting them here would destroy the measurement.
    Only structurally unreadable input returns {}.
    """
    if not text:
        return {}
    raw: dict[int, dict[str, np.ndarray]] = {}
    for row in csv.DictReader(io.StringIO(text)):
        try:
            q = int(float(row["quarter"]))
            frm = str(row["from_rating"]).strip()
            vals = np.array([float(row[c]) for c in MATRIX_COLS], dtype=float)
        except (KeyError, TypeError, ValueError):
            return {}
        if frm not in LIVE_STATES or not np.isfinite(vals).all():
            return {}
        raw.setdefault(q, {})[frm] = vals
    out = {}
    for q, rows in raw.items():
        if set(rows) != set(LIVE_STATES):
            continue
        m = np.zeros((len(ORDER), len(ORDER)))
        for i, st in enumerate(LIVE_STATES):
            m[i] = rows[st]
        m[D_INDEX, D_INDEX] = 1.0
        out[q] = m
    return out


def matrix_diagnostics(text: str | None, start: np.ndarray,
                       submitted: dict[int, np.ndarray],
                       checkpoints) -> dict[str, float]:
    """Admissibility of the submitted quarterly matrices, reported not scored.

    The agent is asked for its matrices without being told what is examined. The
    question is whether it volunteers, unprompted, the checks a risk function
    would raise: that a transition matrix must have non-negative entries and rows
    summing to one, that default probability must not improve as credit quality
    worsens, and that the documented model must actually reproduce the reported
    projection.

    None of this enters `score`. It is measurement, pending a decision on whether
    and how admissibility should affect the headline number.
    """
    mats = parse_matrices(text)
    if not mats:
        return {"matrix_provided": 0.0}
    quarters = sorted(mats)
    live = [mats[q][:D_INDEX] for q in quarters]
    stacked = np.concatenate(live, axis=0)

    row_err = float(np.max(np.abs(stacked.sum(axis=1) - 1.0)))
    negatives = int((stacked < 0).sum())
    most_negative = float(stacked.min())
    # an exact zero anywhere off the AAA default cell is suspicious: under a
    # threshold-shift law every other transition carries positive mass
    zero_mask = stacked == 0.0
    zeros = int(zero_mask.sum())
    smallest_positive = float(stacked[stacked > 0].min()) if (stacked > 0).any() else 0.0

    # default probability must not fall as credit quality worsens
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
    out = {
        "matrix_provided": 1.0,
        "matrix_rows_valid": float(rows_valid),
        "matrix_nonnegative": float(nonneg),
        "matrix_admissible": float(admissible),
        "matrix_quarters": float(len(quarters)),
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
    if submitted and len(quarters) >= max(checkpoints):
        v = start.copy()
        gaps = []
        for t, q in enumerate(quarters, start=1):
            v = v @ mats[q]
            if t in checkpoints and t in submitted:
                gaps.append(ks_distance(v, submitted[t]))
        if gaps:
            out["matrix_submission_gap"] = float(np.mean(gaps))
    return out


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
                       submitted: dict[int, np.ndarray],
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

    `stress_peak_ratio` compares the peaks, and `stress_peak_lag` the timing: a
    model may get the level right and put the peak in the wrong quarter, which a
    reviewer reads off the chart immediately and no distance metric at a
    checkpoint can see.

    The checkpoint ratios come from `predictions.csv` alone, so they survive a
    submission that omits the matrices.
    """
    out: dict[str, float] = {}
    true_cum = {int(q): float(v["D"]) for q, v in truth["rating_distribution"].items()}
    for q, cum in sorted(true_cum.items()):
        if q in submitted and cum > 0.0:
            out[f"default_ratio_q{q}"] = float(submitted[q][D_INDEX] / cum)

    inc_true = np.asarray(truth.get("default_increments", ()), dtype=float)
    mats = parse_matrices(text)
    if inc_true.size == 0 or not mats or len(mats) < inc_true.size:
        return out

    v, inc_sub = start.copy(), []
    prev = float(start[D_INDEX])
    for q in sorted(mats)[:inc_true.size]:
        v = v @ mats[q]
        inc_sub.append(float(v[D_INDEX]) - prev)
        prev = float(v[D_INDEX])
    inc_sub = np.asarray(inc_sub, dtype=float)

    # the stressed half of the horizon, chosen on the truth so that a model
    # cannot define its own stress window
    stressed = inc_true >= np.median(inc_true)
    denom_mean = float(inc_true[stressed].mean())
    denom_peak = float(inc_true.max())
    if denom_mean > 0.0:
        out["stress_mean_ratio"] = float(inc_sub[stressed].mean() / denom_mean)
    if denom_peak > 0.0:
        out["stress_peak_ratio"] = float(inc_sub.max() / denom_peak)
    if float(np.ptp(inc_sub)) > 0.0:     # a flat path has no peak to be early or late
        out["stress_peak_lag"] = float(
            int(np.argmax(inc_sub)) - int(np.argmax(inc_true)))
    return out


#: Every key reported for this task, which is the contract with aggregation.
#: Inspect averages a keyed metric by pulling the key from each sample's score
#: value: absent raises, NaN is skipped. Since every diagnostic is conditional
#: on something, `score_value` fills what does not apply with NaN.
REPORTED_KEYS = (
    "score_degenerate", "ks_q4_norm", "ks_q9_norm", "default_q4_norm",
    "default_q9_norm", "default_rate_bias", "hosmer_lemeshow",
    "completion", "runs", "regret_worst", "regret_spread",
    # diagnostics only: deliberately excluded from `score`
    "matrix_provided", "matrix_rows_valid", "matrix_nonnegative",
    "matrix_admissible", "matrix_row_sum_error", "matrix_rows_off_one",
    "matrix_negative_cells", "matrix_most_negative", "matrix_zero_cells",
    "matrix_smallest_positive", "matrix_default_monotonicity_violations",
    "matrix_submission_gap",
    # one-sided stress response, also diagnostics only
    "default_ratio_q4", "default_ratio_q9", "stress_mean_ratio",
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
    v.update(matrix_diagnostics(mtext, start, submitted,
                                [int(q) for q in truth["rating_distribution"]]))
    v.update(stress_diagnostics(mtext, start, submitted, truth))
    v.update(fit_diagnostics(btext, truth.get("observed_annual_default_rate", ())))
    for k in REPORTED_KEYS:
        v.setdefault(k, float("nan"))
    return v


def explain(v: dict[str, float]) -> str:
    """The one line a reader sees per sample, skipping what did not apply."""
    import math

    bits = [f"score {v['score']:.4f} (1.0 = no migration)",
            "components " + "/".join(
                f"{v[f'{k}_norm']:.3f}" for k in
                ("ks_q4", "ks_q9", "default_q4", "default_q9")),
            f"completion {v['completion']:.0%}"]
    for key, label, fmt in (("default_rate_bias", "default bias", "+.3%"),
                            ("stress_mean_ratio", "stress response", ".2f"),
                            ("fit_stress_mean_ratio", "backtest stress", ".2f")):
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
