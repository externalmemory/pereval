"""Shared oracle-anchored interval scoring for perEval prediction tasks.

Every prediction task here asks for a point estimate plus a 95% prediction
interval for a new noisy observation, at each held-out input. This module scores
that against a Monte-Carlo oracle: point accuracy (MAE vs the true conditional
mean), interval coverage (target 0.95), sharpness (width), and the Winkler
interval score (Gneiting and Raftery, 2007) reported as regret against the oracle.

It is generic in two ways so the ballistic and orbital tasks can share it:

  - key columns: predictions are matched to held-out points by an arbitrary tuple
    of key columns (for example (category, x), or (t,)).
  - circular targets: pass period=360 when the target is an angle in degrees. The
    scorer then measures errors, coverage, and interval width on the circle,
    localizing every quantity to the branch nearest the known true value before
    applying the linear scoring math. This is correct while intervals and noise
    are small relative to the period, which holds here.

Three anchors, not two. Besides the Monte-Carlo oracle (the achievable floor) the
scorer also computes the DEGENERATE anchor: the score of the least informative
admissible answer, one constant point estimate for the whole instance with a
zero-width interval. It costs nothing to compute from truth and it does two jobs.

First, it prices non-response. Charging a missing prediction a multiple of the
ORACLE score, as this scorer originally did, anchors the penalty to the
irreducible measurement noise rather than to the difficulty of the task, and on
these tasks the noise floor is one to four degrees while a bad answer costs
hundreds. Submitting nothing therefore scored better than trying and failing, and
better than the naive baseline, on most of the suite. A missing point is now
scored as though the degenerate answer had been submitted, so abstention can
never earn credit for information it did not supply.

Second, it makes "worse than useless" measurable. A model whose regret exceeds
degenerate_regret carries less information than a constant, which on some tasks
is where every model in the cast currently sits, and which no oracle-anchored
number alone reveals.

The core (score_points, interval_score, parse_predictions) is pure and unit
tested against planted solutions.
"""

from __future__ import annotations

import csv
import io

import numpy as np

ALPHA = 0.05  # 95% intervals
# A missing point is charged the degenerate answer's score, floored at this
# multiple of the oracle so that instances with almost no signal in the target
# still price abstention above the achievable floor.
MISSING_PENALTY_FLOOR = 5.0


def interval_score(lo: float, hi: float, y, alpha: float = ALPHA):
    """Winkler interval score for [lo, hi] and observation(s) y. Lower is better."""
    y = np.asarray(y, dtype=float)
    return (hi - lo) + (2.0 / alpha) * (lo - y) * (y < lo) + (2.0 / alpha) * (y - hi) * (y > hi)


def _wrap(d, period: float):
    """Map differences into [-period/2, period/2]."""
    return (np.asarray(d, dtype=float) + period / 2.0) % period - period / 2.0


def _localize(values, ref: float, period: float | None):
    """Express values on the branch nearest ref (identity when not circular)."""
    if period is None:
        return np.asarray(values, dtype=float)
    return ref + _wrap(np.asarray(values, dtype=float) - ref, period)


def _circular_mean(values, period: float) -> float:
    ang = 2.0 * np.pi * np.asarray(values, dtype=float) / period
    mean_ang = np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())
    return float((period * mean_ang / (2.0 * np.pi)) % period)


def degenerate_answer(points: list[dict], period: float | None):
    """The least informative admissible answer and its per-point Winkler scores.

    One constant point estimate for the whole instance, taken as the (circular)
    mean of the true means, with a zero-width interval. It uses no information
    about which held-out point is which, so it is the floor any answer that
    carries information should beat.
    """
    tms = [float(p["true_mean"]) for p in points]
    c = _circular_mean(tms, period) if period is not None else float(np.mean(tms))
    scores = []
    for p in points:
        tm = float(p["true_mean"])
        mc = _localize(p["mc"], tm, period)
        cc = float(_localize([c], tm, period)[0])
        scores.append(float(interval_score(cc, cc, mc).mean()))
    return c, scores


def _aggregate(records: list[dict]) -> dict:
    ws_agent = np.array([r["ws_agent"] for r in records])
    ws_oracle = np.array([r["ws_oracle"] for r in records])
    ws_degen = np.array([r["ws_degenerate"] for r in records])
    n_missing = int(sum(r["missing"] for r in records))
    return {
        "winkler_agent": float(ws_agent.mean()),
        "winkler_oracle": float(ws_oracle.mean()),
        "winkler_degenerate": float(ws_degen.mean()),
        "winkler_regret": float(ws_agent.mean() - ws_oracle.mean()),
        "degenerate_regret": float(ws_degen.mean() - ws_oracle.mean()),
        "mae": float(np.mean([r["abs_err"] for r in records])),
        "coverage": float(np.mean([r["coverage"] for r in records])),
        "mean_width": float(np.mean([r["width"] for r in records])),
        "n_points": len(records),
        "n_missing": n_missing,
        "completion": float(1.0 - n_missing / len(records)) if records else 0.0,
    }


def score_points(points: list[dict], preds: dict[tuple, tuple[float, float, float]],
                 period: float | None = None) -> dict:
    """Score held-out points against predictions.

    points: list of {"key": tuple, "class": str|None, "true_mean": float,
    "mc": sequence of predictive Monte-Carlo draws}. preds: {key: (point, lo, hi)}.
    Returns overall aggregates plus a per-class breakdown when classes are present.
    """
    records = []
    c_degen, ws_degen = degenerate_answer(points, period)
    for p, ws_deg in zip(points, ws_degen):
        tm = float(p["true_mean"])
        mc = _localize(p["mc"], tm, period)
        pi_lo = float(np.quantile(mc, 0.025))
        pi_hi = float(np.quantile(mc, 0.975))
        oracle_width = pi_hi - pi_lo
        ws_oracle = float(interval_score(pi_lo, pi_hi, mc).mean())
        rec = {"class": p.get("class"), "ws_oracle": ws_oracle, "oracle_width": oracle_width,
               "ws_degenerate": ws_deg}

        pred = preds.get(p["key"])
        valid = pred is not None and all(np.isfinite(v) for v in pred)
        if valid:
            point, lo, hi = pred
            point = float(_localize([point], tm, period)[0])
            lo = float(_localize([lo], tm, period)[0])
            hi = float(_localize([hi], tm, period)[0])
            if lo > hi:
                lo, hi = hi, lo
            rec.update(
                missing=False,
                ws_agent=float(interval_score(lo, hi, mc).mean()),
                abs_err=abs(point - tm),
                coverage=float(((mc >= lo) & (mc <= hi)).mean()),
                width=hi - lo,
            )
        else:
            # Scored as though the degenerate answer had been submitted: a constant
            # point estimate and no interval. Floored at a multiple of the oracle so
            # that a target with almost no variation across held-out points cannot
            # make abstention cheap.
            cc = float(_localize([c_degen], tm, period)[0])
            rec.update(
                missing=True,
                ws_agent=max(ws_deg, MISSING_PENALTY_FLOOR * ws_oracle),
                abs_err=abs(cc - tm),
                coverage=0.0,
                width=0.0,
            )
        records.append(rec)

    result = _aggregate(records)
    classes = sorted({r["class"] for r in records if r["class"] is not None})
    result["per_class"] = {c: _aggregate([r for r in records if r["class"] == c]) for c in classes}
    return result


def parse_predictions(text: str | None, key_columns: list[str]) -> dict[tuple, tuple[float, float, float]]:
    """Parse predictions.csv (key columns + y_pred,y_lower,y_upper) into {key: (point, lo, hi)}.

    Key values are parsed as float where possible, else kept as stripped strings,
    matching how truth keys are built. Rows with unparseable numbers are skipped.
    """
    preds: dict[tuple, tuple[float, float, float]] = {}
    if not text or not text.strip():
        return preds
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return preds
    fields = {name.strip().lower(): name for name in reader.fieldnames}
    required = list(key_columns) + ["y_pred", "y_lower", "y_upper"]
    if not all(k in fields for k in required):
        return preds
    for row in reader:
        try:
            key = tuple(_coerce(row[fields[k]]) for k in key_columns)
            point = float(row[fields["y_pred"]])
            lo = float(row[fields["y_lower"]])
            hi = float(row[fields["y_upper"]])
        except (ValueError, TypeError, AttributeError):
            continue
        preds[key] = (point, lo, hi)
    return preds


def _coerce(v: str):
    s = v.strip()
    try:
        return float(s)
    except ValueError:
        return s


def score_value_and_explanation(agg: dict) -> tuple[dict, str]:
    value = {k: agg[k] for k in ("winkler_regret", "winkler_agent", "degenerate_regret",
                                 "mae", "coverage", "mean_width", "completion")}
    # Stability keys are always present so the epoch reducer only has to overwrite
    # them; for a single run the worst case is the run and the spread is zero. See
    # pereval.scorers.stability.
    value.update(runs=1.0, regret_worst=agg["winkler_regret"], regret_spread=0.0)
    worse = " WORSE THAN DEGENERATE;" if agg["winkler_regret"] > agg["degenerate_regret"] else ""
    explanation = (
        f"{agg['n_points'] - agg['n_missing']}/{agg['n_points']} points predicted; "
        f"Winkler regret {agg['winkler_regret']:.3f} "
        f"(agent {agg['winkler_agent']:.3f} vs oracle {agg['winkler_oracle']:.3f}, "
        f"degenerate {agg['winkler_degenerate']:.3f});{worse} "
        f"MAE {agg['mae']:.3f}; coverage {agg['coverage']:.3f}; "
        f"mean width {agg['mean_width']:.3f}."
    )
    return value, explanation


def make_interval_scorer(name: str, key_columns: list[str], period: float | None, truth_to_points):
    """Build an Inspect scorer that reads predictions.csv from the sandbox and
    scores it against points extracted from sample metadata by truth_to_points."""
    from inspect_ai.scorer import Score, mean, scorer, stderr
    from inspect_ai.util import sandbox

    @scorer(
        name=name,
        metrics={
            "winkler_regret": [mean(), stderr()],
            "winkler_agent": [mean()],
            "degenerate_regret": [mean()],
            "mae": [mean(), stderr()],
            "coverage": [mean()],
            "mean_width": [mean()],
            "completion": [mean()],
            "runs": [mean()],
            "regret_worst": [mean()],
            "regret_spread": [mean()],
        },
    )
    def _scorer():
        async def score(state, target):
            points = truth_to_points(state.metadata["truth"])
            try:
                text = await sandbox().read_file("predictions.csv")
            except FileNotFoundError:
                text = None
            preds = parse_predictions(text, key_columns)
            agg = score_points(points, preds, period)
            value, explanation = score_value_and_explanation(agg)
            return Score(value=value, metadata=agg, explanation=explanation)

        return score

    return _scorer()
