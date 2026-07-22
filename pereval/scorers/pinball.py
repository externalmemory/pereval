"""Pinball-regret scoring for the quantile task.

The agent sees 10 values drawn without replacement from a population of m and
estimates that population's tail quantiles. Unlike the other perEval tasks there
is no generated DGP, so there is no Monte-Carlo oracle. There does not need to be
one: the pinball loss

    L(q, tau) = E_pop[rho_tau(X - q)],   rho_tau(d) = d * (tau - 1[d < 0])

is minimised exactly at the population tau-quantile, so the population itself
supplies both the truth and the achievable floor. Regret is therefore
non-negative and zero only for a perfect answer, with no truth estimator, no
Harrell-Davis target, and no tuning.

Why not the Winkler interval score used elsewhere in this suite: measured on a
pilot, grafting one fixed interval shape onto every candidate rule's own point
estimate collapsed the whole Winkler spread from 3.44-20.62 down to 3.07-4.02.
Winkler ranks almost purely on interval width and is nearly flat in the point
estimate, with its optimum at hit rate 0.370 rather than 0.500. It is still
reported, as a diagnostic, because interval calibration is worth measuring; it is
just not what this task is about.

Three tau levels are scored because the reference estimators are indistinguishable
at 0.90 and separate sharply at 0.99, where bounded interpolation is structurally
stuck: in units of the sample top gap, the p99-p95 spread is an exact constant
for type7 (0.360), type8 (0.000) and both extrapolators (1.609), and varies only
mildly for HD (about 0.16 to 0.20), while the truth varies 1.25 to 4.15 across
series. No reference rule adapts to tail shape; all of them scale it by one
order-statistic gap.
"""

from __future__ import annotations

import csv
import io

import numpy as np

TAUS = (0.90, 0.95, 0.99)
ALPHA = 0.05          # the interval requested alongside the point estimates
PENALTY_FACTOR = 5.0  # missing answers cost this multiple of the type-7 regret


def pinball_loss(qhat: float, pop, tau: float) -> float:
    """Mean rho_tau(X - qhat) over the population."""
    d = np.asarray(pop, dtype=float) - float(qhat)
    return float(np.where(d >= 0, tau * d, (tau - 1.0) * d).mean())


def pinball_regret(qhat: float, pop, tau: float) -> float:
    """Excess pinball loss over the population's own tau-quantile. Zero is perfect."""
    pop = np.asarray(pop, dtype=float)
    return pinball_loss(qhat, pop, tau) - pinball_loss(
        float(np.quantile(pop, tau)), pop, tau)


def interval_score(lo: float, hi: float, y: float, alpha: float = ALPHA) -> float:
    """Winkler score for a scalar target. Diagnostic only."""
    return (hi - lo) + (2.0 / alpha) * (max(0.0, lo - y) + max(0.0, y - hi))


def type7(x, tau: float) -> float:
    """numpy/pandas default quantile: the do-nothing answer, used as the penalty scale."""
    return float(np.quantile(np.asarray(x, dtype=float), tau, method="linear"))


def _blank(block: dict) -> dict:
    """Penalty record for a block the agent did not answer."""
    pop, norm, x = block["pop"], block["norm"], block["x"]
    per = {t: PENALTY_FACTOR * pinball_regret(type7(x, t), pop, t) / norm for t in TAUS}
    return dict(missing=True, per_tau=per, regret=sum(per.values()),
                hit=0.0, mae=float("nan"), coverage=0.0,
                winkler=float("nan"), spread=float("nan"), monotonic=True)


def score_block(block: dict, pred: dict | None) -> dict:
    """block: {"pop", "norm", "x"}; pred: {"q90","q95","q99","lo","hi"} or None.

    `norm` is the population IQR, not its standard deviation. See the note in
    generator.draw_block: the regret is invariant to lower-tail outliers but sd
    is not, so sd normalisation would silently mute exactly the hardest blocks.
    """
    pop, norm, x = np.asarray(block["pop"], float), block["norm"], np.sort(block["x"])
    needed = ("q90", "q95", "q99", "lo", "hi")
    if pred is None or not all(np.isfinite(pred.get(k, np.nan)) for k in needed):
        return _blank(block)

    q = {t: float(pred[f"q{int(t * 100)}"]) for t in TAUS}
    lo, hi = sorted((float(pred["lo"]), float(pred["hi"])))
    truth95 = float(np.quantile(pop, 0.95))
    per = {t: pinball_regret(q[t], pop, t) / norm for t in TAUS}
    gap = x[-1] - x[-2]

    return dict(
        missing=False,
        per_tau=per,
        regret=sum(per.values()),
        hit=float(q[0.95] > truth95),
        mae=abs(q[0.95] - truth95) / norm,
        coverage=float(lo <= truth95 <= hi),
        winkler=interval_score(lo, hi, truth95) / norm,
        spread=(q[0.99] - q[0.95]) / gap if gap > 0 else float("nan"),
        monotonic=q[0.90] <= q[0.95] <= q[0.99],
    )


def aggregate(records: list[dict]) -> dict:
    def m(key):
        v = [r[key] for r in records if not r["missing"] and np.isfinite(r[key])]
        return float(np.mean(v)) if v else float("nan")

    out = {
        "pinball_regret": float(np.mean([r["regret"] for r in records])),
        "hit_rate": float(np.mean([r["hit"] for r in records if not r["missing"]]))
        if any(not r["missing"] for r in records) else float("nan"),
        "mae": m("mae"),
        "coverage": m("coverage"),
        "winkler": m("winkler"),
        "spread_ratio": m("spread"),
        "n_blocks": len(records),
        "n_missing": int(sum(r["missing"] for r in records)),
        "n_nonmonotonic": int(sum(not r["monotonic"] for r in records)),
    }
    for t in TAUS:
        out[f"regret_p{int(t * 100)}"] = float(
            np.mean([r["per_tau"][t] for r in records]))
    return out


def parse_predictions(text: str | None) -> dict[int, dict]:
    """predictions.csv with columns block,q90,q95,q99,lo,hi -> {block: {...}}."""
    preds: dict[int, dict] = {}
    if not text or not text.strip():
        return preds
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return preds
    f = {n.strip().lower(): n for n in reader.fieldnames}
    if not all(k in f for k in ("block", "q90", "q95", "q99", "lo", "hi")):
        return preds
    for row in reader:
        try:
            preds[int(float(row[f["block"]]))] = {
                k: float(row[f[k]]) for k in ("q90", "q95", "q99", "lo", "hi")}
        except (ValueError, TypeError, AttributeError):
            continue
    return preds


def score_value_and_explanation(agg: dict) -> tuple[dict, str]:
    value = {k: agg[k] for k in ("pinball_regret", "hit_rate", "mae",
                                 "coverage", "winkler", "spread_ratio")}
    explanation = (
        f"{agg['n_blocks'] - agg['n_missing']}/{agg['n_blocks']} blocks answered; "
        f"pinball regret {agg['pinball_regret']:.4f} "
        f"(p90 {agg['regret_p90']:.4f}, p95 {agg['regret_p95']:.4f}, "
        f"p99 {agg['regret_p99']:.4f}); hit rate {agg['hit_rate']:.3f}; "
        f"MAE {agg['mae']:.3f}; coverage {agg['coverage']:.3f}; "
        f"Winkler {agg['winkler']:.2f}; spread {agg['spread_ratio']:.2f}"
        + (f"; {agg['n_nonmonotonic']} non-monotonic" if agg["n_nonmonotonic"] else "")
    )
    return value, explanation
