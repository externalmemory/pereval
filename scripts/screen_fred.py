#!/usr/bin/env python3
"""Screen FRED series for use as quantile-task populations.

Two stages. Metadata filtering (frequency, seasonal adjustment, units) needs the
FRED API and happens in `metadata_ok`; the numeric screen below works on
observations alone and is the part that carries the validity risk.

The numeric rules were calibrated against the 12 accepted and 7 rejected series
from the proof of concept in /mnt/hostshare/quantiles.
"""
import numpy as np

MIN_YOY = 250          # observations required after differencing
JUMP = 2.0             # period-over-period ratio that flags a candidate break
PERSIST = 1.5          # post/pre median ratio above which a break is persistent
TIE_RATE = 0.01        # tolerated tie rate among upper order statistics
TIE_TOP = 3            # how many upper order statistics the tie check covers

# FRED `units` strings that make a YoY percent change meaningless or explosive.
# A rate near zero (FEDFUNDS bottoms at 0.06) produces unbounded ratios, and a
# percent-of-percent is a different quantity from a growth rate.
BAD_UNITS = ("percent", "rate", "ratio", "basis point")


def metadata_ok(meta):
    """meta: a FRED /fred/series record. Requires an API key upstream."""
    if meta.get("frequency_short") != "M":
        return False, "not monthly"
    if "Not Seasonally Adjusted" not in meta.get("seasonal_adjustment", ""):
        return False, "seasonally adjusted"
    u = meta.get("units", "").lower()
    if any(b in u for b in BAD_UNITS):
        return False, f"units={meta.get('units')}"
    return True, "ok"


def month_index(d):
    return int(d[:4]) * 12 + int(d[5:7]) - 1


def yoy(levels, lag=12):
    """100 * (x_t / x_{t-lag} - 1). Simple, not log: see preprocess.py."""
    return 100.0 * (levels[lag:] / levels[:-lag] - 1.0)


def persistent_break(levels, ppy=12, jump=JUMP, persist=PERSIST):
    """True if a large jump never reverts.

    Magnitude alone does not separate an artifact from data. M1NS jumped 4.48x
    on a 2020 savings reclassification and never reverted; LNU03000000 jumped
    3.56x on COVID and returned to baseline. Only persistence separates them.
    """
    win = max(4, ppy // 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.abs(np.log(levels[1:] / levels[:-1]))
    for t in np.where(r > np.log(jump))[0] + 1:
        if t - win < 0 or t + 3 * ppy > len(levels):
            continue
        pre = np.median(levels[t - win:t])
        post = np.median(levels[t + ppy:t + 3 * ppy])   # 1 to 3 years later
        if pre > 0 and abs(np.log(post / pre)) > np.log(persist):
            return True
    return False


def tie_rate_upper(pop, top=TIE_TOP):
    """Fraction of adjacent-equal pairs among the top `top` order statistics.

    wei8's tail branch is proportional to x_(n) - x_(n-1); a tie there collapses
    the extrapolation to the sample maximum and silently degrades the reference
    estimator toward type 7. The cause is quantisation of the source levels, not
    a ceiling on the growth rate.
    """
    s = np.sort(pop)[-(top + 1):]
    return float(np.mean(np.diff(s) == 0))


def trim_nan(dates, levels):
    """Drop leading/trailing NaN padding. FRED pads CSVs to a common date grid,
    so edge NaNs are formatting; only an interior NaN is a real gap."""
    good = np.where(~np.isnan(levels))[0]
    if len(good) == 0:
        return [], np.array([])
    lo, hi = good[0], good[-1] + 1
    return list(dates[lo:hi]), levels[lo:hi]


def screen(dates, levels, ppy=12):
    """-> (accepted, reason, stats). `levels` may carry NaN padding."""
    lag = ppy
    dates, levels = trim_nan(dates, levels)
    if len(levels) == 0:
        return False, "no observations", {}
    if np.isnan(levels).any():
        return False, "interior gap in level series", {}
    idx = np.array([month_index(d) for d in dates]) if ppy == 12 else None
    if idx is not None and not np.all(np.diff(idx) == 1):
        return False, "non-contiguous date grid", {}
    if not np.all(levels > 0):
        return False, "non-positive levels", {}
    if persistent_break(levels, ppy):
        return False, "persistent definitional break", {}

    pop = yoy(levels, lag)
    if len(pop) < MIN_YOY:
        return False, f"only {len(pop)} YoY observations", {}
    tr = tie_rate_upper(pop)
    if tr > TIE_RATE:
        return False, f"upper tie rate {tr:.3f}", {}

    c = pop - pop.mean()
    sd = pop.std()
    stats = dict(n=len(pop), sd=float(sd),
                 skew=float((c ** 3).mean() / sd ** 3),
                 exkurt=float((c ** 4).mean() / sd ** 4 - 3.0),
                 tie_rate=tr)
    return True, "ok", stats
