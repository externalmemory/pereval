"""Oracle-anchored scorer for the ballistic trajectory task.

The agent predicts, for each held-out (category, x), a point estimate and a 95%
prediction interval for a new noisy observation of y. We score three things
against the Monte-Carlo oracle owned by the generator:

  - point accuracy: mean absolute error of the point estimate vs the true
    conditional mean E[y | category, x];
  - interval calibration: empirical coverage of the predicted interval under the
    true predictive distribution (target 0.95);
  - sharpness: interval width (narrower is better, subject to coverage).

The headline metric is the Winkler (interval) score (Gneiting and Raftery,
2007), the proper scoring rule that combines width and calibration into one
number that cannot be gamed by reporting an interval you do not believe. We
report it as regret against the oracle: the oracle uses the true 95% predictive
interval, so its expected interval score is the minimum achievable, and
winkler_regret = agent - oracle is >= 0 with 0 meaning oracle-equivalent.

The scoring core (interval_score, score_instance) is pure and has no Inspect
dependency, so it is unit-tested directly against planted correct / flawed /
degenerate solutions in tests/test_ballistic_scorer.py.
"""

from __future__ import annotations

import numpy as np

ALPHA = 0.05  # 95% intervals
PENALTY_FACTOR = 5.0  # missing/invalid predictions penalized at this multiple of oracle


def interval_score(lo: float, hi: float, y, alpha: float = ALPHA):
    """Winkler interval score for interval [lo, hi] and observation(s) y.

    Lower is better: interval width plus a 2/alpha penalty per unit the
    observation falls outside the interval. Vectorized over y.
    """
    y = np.asarray(y, dtype=float)
    return (hi - lo) + (2.0 / alpha) * (lo - y) * (y < lo) + (2.0 / alpha) * (y - hi) * (y > hi)


def _point_records(truth: dict, preds: dict[tuple[str, float], tuple[float, float, float]]):
    cats = truth["categories"]
    for tp in truth["test"]:
        cid = tp["category"]
        x = float(tp["x_m"])
        cls = cats[cid]["class"]
        mc = np.asarray(tp["mc_samples_m"], dtype=float)
        true_mean = float(tp["true_mean_y_m"])
        pi_lo, pi_hi = tp["predictive_pi95_m"]
        oracle_width = float(pi_hi - pi_lo)
        oracle_halfwidth = oracle_width / 2.0
        ws_oracle = float(interval_score(pi_lo, pi_hi, mc).mean())

        rec = {
            "cid": cid,
            "x": x,
            "class": cls,
            "ws_oracle": ws_oracle,
            "oracle_width": oracle_width,
        }
        pred = preds.get((cid, x))
        valid = pred is not None and all(np.isfinite(v) for v in pred)
        if valid:
            point, lo, hi = pred
            if lo > hi:
                lo, hi = hi, lo
            rec.update(
                missing=False,
                ws_agent=float(interval_score(lo, hi, mc).mean()),
                abs_err=abs(point - true_mean),
                coverage=float(((mc >= lo) & (mc <= hi)).mean()),
                width=float(hi - lo),
            )
        else:
            # Penalize missing/invalid points finitely in every metric so a failed
            # sample cannot poison the aggregate with NaN, and monotonically hurts.
            rec.update(
                missing=True,
                ws_agent=PENALTY_FACTOR * ws_oracle,
                abs_err=PENALTY_FACTOR * oracle_halfwidth,
                coverage=0.0,
                width=PENALTY_FACTOR * oracle_width,
            )
        yield rec


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


def score_instance(truth: dict, preds: dict[tuple[str, float], tuple[float, float, float]]) -> dict:
    """Score one task instance. Pure: no Inspect dependency.

    truth is the generator's build_truth() output; preds maps (category, x) to
    (point, lower, upper). Returns overall aggregates plus a per-class breakdown.
    """
    records = list(_point_records(truth, preds))
    result = _aggregate(records)
    per_class = {}
    for cls in sorted({r["class"] for r in records}):
        per_class[cls] = _aggregate([r for r in records if r["class"] == cls])
    result["per_class"] = per_class
    return result


def parse_predictions(text: str | None) -> dict[tuple[str, float], tuple[float, float, float]]:
    """Parse a predictions.csv with header category,x,y_pred,y_lower,y_upper.

    Tolerant of whitespace and column order (by header name). Rows with
    unparseable numbers are skipped (treated as missing by the scorer).
    """
    import csv
    import io

    preds: dict[tuple[str, float], tuple[float, float, float]] = {}
    if not text or not text.strip():
        return preds
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return preds
    fields = {name.strip().lower(): name for name in reader.fieldnames}
    required = ("category", "x", "y_pred", "y_lower", "y_upper")
    if not all(k in fields for k in required):
        return preds
    for row in reader:
        try:
            cid = row[fields["category"]].strip()
            x = float(row[fields["x"]])
            point = float(row[fields["y_pred"]])
            lo = float(row[fields["y_lower"]])
            hi = float(row[fields["y_upper"]])
        except (ValueError, TypeError, AttributeError):
            continue
        preds[(cid, x)] = (point, lo, hi)
    return preds


# --- Inspect wrapper -------------------------------------------------------

def ballistic_scorer():
    from inspect_ai.scorer import Score, mean, scorer, stderr
    from inspect_ai.util import sandbox

    @scorer(
        metrics={
            "winkler_regret": [mean(), stderr()],
            "winkler_agent": [mean()],
            "mae": [mean(), stderr()],
            "coverage": [mean()],
            "mean_width": [mean()],
        }
    )
    def _ballistic_scorer():
        async def score(state, target):
            truth = state.metadata["truth"]
            try:
                text = await sandbox().read_file("predictions.csv")
            except FileNotFoundError:
                text = None
            preds = parse_predictions(text)
            agg = score_instance(truth, preds)
            value = {
                "winkler_regret": agg["winkler_regret"],
                "winkler_agent": agg["winkler_agent"],
                "mae": agg["mae"],
                "coverage": agg["coverage"],
                "mean_width": agg["mean_width"],
            }
            explanation = (
                f"{agg['n_points'] - agg['n_missing']}/{agg['n_points']} points predicted; "
                f"Winkler regret {agg['winkler_regret']:.3f} "
                f"(agent {agg['winkler_agent']:.3f} vs oracle {agg['winkler_oracle']:.3f}); "
                f"MAE {agg['mae']:.3f} m; coverage {agg['coverage']:.3f}; "
                f"mean width {agg['mean_width']:.3f} m."
            )
            return Score(value=value, metadata=agg, explanation=explanation)

        return score

    return _ballistic_scorer()
