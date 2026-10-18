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


def migration_scorer():
    from inspect_ai.scorer import Score, mean, scorer, stderr
    from inspect_ai.util import sandbox

    keys = ("score_degenerate", "ks_q4_norm", "ks_q9_norm", "default_q4_norm",
            "default_q9_norm", "default_rate_bias", "hosmer_lemeshow",
            "completion", "runs", "regret_worst", "regret_spread",
            # diagnostics only: deliberately excluded from `score`
            "matrix_provided", "matrix_rows_valid", "matrix_nonnegative",
            "matrix_admissible", "matrix_row_sum_error", "matrix_rows_off_one",
            "matrix_negative_cells", "matrix_most_negative", "matrix_zero_cells",
            "matrix_smallest_positive", "matrix_default_monotonicity_violations",
            "matrix_submission_gap")

    @scorer(name="migration",
            metrics={"score": [mean(), stderr()], **{k: [mean()] for k in keys}})
    def factory():
        async def score(state, target):
            try:
                text = await sandbox().read_file("predictions.csv")
            except FileNotFoundError:
                text = None
            try:
                mtext = await sandbox().read_file("matrices.csv")
            except FileNotFoundError:
                mtext = None
            truth = state.metadata["truth"]
            v = score_predictions(truth, text)
            start = np.array([truth["start_mix"].get(s_, 0.0) for s_ in ORDER],
                             dtype=float)
            v.update(matrix_diagnostics(
                mtext, start, parse_predictions(text),
                [int(q) for q in truth["rating_distribution"]]))
            bits = [f"score {v['score']:.4f} (1.0 = no migration)",
                    "components " + "/".join(
                        f"{v[f'{k}_norm']:.3f}" for k in
                        ("ks_q4", "ks_q9", "default_q4", "default_q9")),
                    f"completion {v['completion']:.0%}"]
            if "default_rate_bias" in v:
                bits.append(f"default bias {v['default_rate_bias']:+.3%}")
            return Score(value=v, explanation="; ".join(bits))

        return score

    return factory()
