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

The core (score_points, interval_score, parse_predictions) is pure and unit
tested against planted solutions.
"""

from __future__ import annotations

import csv
import io

import numpy as np

ALPHA = 0.05  # 95% intervals
PENALTY_FACTOR = 5.0  # missing/invalid predictions penalized at this multiple of oracle


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


def _aggregate(records: list[dict]) -> dict:
    ws_agent = np.array([r["ws_agent"] for r in records])
    ws_oracle = np.array([r["ws_oracle"] for r in records])
    return {
        "winkler_agent": float(ws_agent.mean()),
        "winkler_oracle": float(ws_oracle.mean()),
        "winkler_regret": float(ws_agent.mean() - ws_oracle.mean()),
        "mae": float(np.mean([r["abs_err"] for r in records])),
        "coverage": float(np.mean([r["coverage"] for r in records])),
        "mean_width": float(np.mean([r["width"] for r in records])),
        "n_points": len(records),
        "n_missing": int(sum(r["missing"] for r in records)),
    }


def score_points(points: list[dict], preds: dict[tuple, tuple[float, float, float]],
                 period: float | None = None) -> dict:
    """Score held-out points against predictions.

    points: list of {"key": tuple, "class": str|None, "true_mean": float,
    "mc": sequence of predictive Monte-Carlo draws}. preds: {key: (point, lo, hi)}.
    Returns overall aggregates plus a per-class breakdown when classes are present.
    """
    records = []
    for p in points:
        tm = float(p["true_mean"])
        mc = _localize(p["mc"], tm, period)
        pi_lo = float(np.quantile(mc, 0.025))
        pi_hi = float(np.quantile(mc, 0.975))
        oracle_width = pi_hi - pi_lo
        ws_oracle = float(interval_score(pi_lo, pi_hi, mc).mean())
        rec = {"class": p.get("class"), "ws_oracle": ws_oracle, "oracle_width": oracle_width}

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
            rec.update(
                missing=True,
                ws_agent=PENALTY_FACTOR * ws_oracle,
                abs_err=PENALTY_FACTOR * oracle_width / 2.0,
                coverage=0.0,
                width=PENALTY_FACTOR * oracle_width,
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
    value = {k: agg[k] for k in ("winkler_regret", "winkler_agent", "mae", "coverage", "mean_width")}
    explanation = (
        f"{agg['n_points'] - agg['n_missing']}/{agg['n_points']} points predicted; "
        f"Winkler regret {agg['winkler_regret']:.3f} "
        f"(agent {agg['winkler_agent']:.3f} vs oracle {agg['winkler_oracle']:.3f}); "
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
            "mae": [mean(), stderr()],
            "coverage": [mean()],
            "mean_width": [mean()],
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
