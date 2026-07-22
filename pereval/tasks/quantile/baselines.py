"""Reference estimators that bracket the quantile task.

Each reads data/blocks.csv from the sandbox and writes predictions.csv, taking
the same path an agent takes, so they double as a zero-cost plumbing check under
mockllm.

The floor and the ceiling are not the ones you would guess:

  type7  numpy's default. Cannot exceed the sample maximum, so it puts the true
         p95 above its own estimate roughly three times in four. The do-nothing
         answer, and the one a model reproduces by calling np.percentile.
  type8  median-unbiased plotting position. At n=10 its index exceeds n for both
         p95 (h=10.15) and p99 (h=10.56), so both clip to the sample maximum and
         its p99-p95 spread is exactly zero.
  hd     Harrell-Davis, a convex combination of order statistics. Also bounded.
  wei8   Wei, Wang and Hutson's tail extrapolation (Eq. 2.1) around a type-8
         interior. The published reference: it does extrapolate past the sample
         maximum, and it is the best centred of the classical rules.
  t6     the same extrapolation around a type-6 interior, as in the paper.
  normal moment-matched normal, mu + z_tau * s. Naive, and better than it has any
         right to be.

Their p99-p95 spreads, in units of the sample top gap x_(n) - x_(n-1), are
exact constants for type7 (0.360), type8 (0.000) and both extrapolators (1.609),
because those rules touch only the top two order statistics at these tau. HD is
a weighted combination of all ten, so its spread varies mildly with shape
(around 0.16 to 0.20). The truth varies 1.25 to 4.15 across series. Essentially
none of them adapts to tail shape; that is where the headroom is.

Intervals are the smoothed bootstrap of the source paper: draw U ~ Uniform(0,1)^n,
set X* = Qhat(U) from the estimator fitted to the ten points, refit, and take a
BCa interval over B replicates.
"""

from __future__ import annotations

import csv
import io

import numpy as np
from inspect_ai.solver import Generate, TaskState, solver
from inspect_ai.util import sandbox
from scipy.stats import norm

TAUS = (0.90, 0.95, 0.99)
ALPHA = 0.05
BOOT = 2000

# Hyndman-Fan interior rules as h(u), 1 <= h <= n
_H = {6: lambda n, u: (n + 1) * u,
      7: lambda n, u: (n - 1) * u + 1,
      8: lambda n, u: (n + 1 / 3) * u + 1 / 3}


def hf_qf(xs: np.ndarray, u, typ: int) -> np.ndarray:
    """Hyndman-Fan type `typ` quantile function. xs sorted, shape (K, n)."""
    n = xs.shape[1]
    h = np.clip(_H[typ](n, np.asarray(u, dtype=float)), 1.0, float(n))
    lo = np.floor(h).astype(np.intp)
    hi = np.minimum(lo + 1, n)
    g = h - lo
    xlo = np.take_along_axis(xs, lo - 1, axis=1)
    xhi = np.take_along_axis(xs, hi - 1, axis=1)
    return xlo + g * (xhi - xlo)


def tail_qf(xs: np.ndarray, u, typ: int) -> np.ndarray:
    """Wei-Wang-Hutson Eq. 2.1: exponential extrapolation outside [1/n', n/n'].

        Q(u) = Q_i(1/n')  + (x_2 - x_1)     * log(n'u)      , u <= 1/n'
             = Q_i(u)                                        , interior
             = Q_i(n/n') - (x_n - x_{n-1}) * log(n'(1-u))   , u >= n/n'
    """
    n = xs.shape[1]
    u = np.asarray(u, dtype=float)
    npr = n + 1.0
    out = hf_qf(xs, np.clip(u, 1.0 / npr, n / npr), typ)

    lowm = u < 1.0 / npr
    if lowm.any():
        anchor = hf_qf(xs, np.full_like(u, 1.0 / npr), typ)
        gap = (xs[:, 1] - xs[:, 0])[:, None]
        out = np.where(lowm, anchor + gap * np.log(npr * np.maximum(u, 1e-300)), out)

    him = u > n / npr
    if him.any():
        anchor = hf_qf(xs, np.full_like(u, n / npr), typ)
        gap = (xs[:, -1] - xs[:, -2])[:, None]
        out = np.where(him, anchor - gap * np.log(npr * np.maximum(1.0 - u, 1e-300)), out)
    return out


def hd_weights(n: int, tau: float) -> np.ndarray:
    from scipy.special import betainc
    a, b = (n + 1) * tau, (n + 1) * (1 - tau)
    e = np.arange(n + 1) / n
    c = betainc(a, b, e)
    return np.diff(c)


def _qf(name: str):
    """Vectorised Qhat(u) for the smoothed bootstrap."""
    if name == "type7":
        return lambda xs, u: hf_qf(xs, u, 7)
    if name == "type8":
        return lambda xs, u: hf_qf(xs, u, 8)
    if name == "wei8":
        return lambda xs, u: tail_qf(xs, u, 8)
    if name == "t6":
        return lambda xs, u: tail_qf(xs, u, 6)
    if name == "hd":
        def f(xs, u):
            out = np.empty_like(np.asarray(u, float))
            for j in range(out.shape[1]):
                for i in range(out.shape[0]):
                    out[i, j] = xs[i] @ hd_weights(xs.shape[1], float(np.clip(u[i, j], 1e-6, 1 - 1e-6)))
            return out
        return f
    if name == "normal":
        return lambda xs, u: (xs.mean(1)[:, None]
                              + norm.ppf(np.clip(u, 1e-12, 1 - 1e-12))
                              * xs.std(1, ddof=1)[:, None])
    raise KeyError(name)


def point_estimate(name: str, xs: np.ndarray, tau: float) -> np.ndarray:
    return _qf(name)(xs, np.full((len(xs), 1), tau))[:, 0]


def bca_interval(name: str, xs: np.ndarray, tau: float, rng, boot: int = BOOT):
    """Smoothed-bootstrap BCa interval for the tau-quantile estimate."""
    b, n = xs.shape
    qf = _qf(name)
    theta_hat = point_estimate(name, xs, tau)

    star = qf(xs, rng.random((b, boot * n))).reshape(b * boot, n)
    star.sort(axis=1)
    theta = np.sort(point_estimate(name, star, tau).reshape(b, boot), axis=1)

    prop = np.clip((theta < theta_hat[:, None]).mean(axis=1), 1 / (2 * boot),
                   1 - 1 / (2 * boot))
    z0 = norm.ppf(prop)

    jk = np.stack([np.delete(xs, j, axis=1) for j in range(n)], axis=1)
    jkest = point_estimate(name, jk.reshape(b * n, n - 1), tau).reshape(b, n)
    d = jkest.mean(axis=1, keepdims=True) - jkest
    den = 6.0 * (d ** 2).sum(axis=1) ** 1.5
    a = np.divide((d ** 3).sum(axis=1), den, out=np.zeros(b), where=den > 0)

    zl, zu = norm.ppf(ALPHA / 2), norm.ppf(1 - ALPHA / 2)
    out = []
    for z in (zl, zu):
        adj = z0 + (z0 + z) / (1 - a * (z0 + z))
        h = np.clip(norm.cdf(adj), 0.0, 1.0) * (boot - 1)
        lo = np.floor(h).astype(np.intp)
        hi = np.minimum(lo + 1, boot - 1)
        g = h - lo
        r = np.arange(b)
        out.append(theta[r, lo] + g * (theta[r, hi] - theta[r, lo]))
    return out[0], out[1]


def _read_blocks(text: str) -> tuple[list[int], np.ndarray]:
    rows = list(csv.DictReader(io.StringIO(text)))
    by: dict[int, list[float]] = {}
    for r in rows:
        by.setdefault(int(float(r["block"])), []).append(float(r["x"]))
    keys = sorted(by)
    return keys, np.array([np.sort(by[k]) for k in keys], dtype=float)


def predictions_csv(name: str, blocks_text: str, seed: int = 7) -> str:
    keys, xs = _read_blocks(blocks_text)
    rng = np.random.default_rng(seed)
    q = {t: point_estimate(name, xs, t) for t in TAUS}
    lo, hi = bca_interval(name, xs, 0.95, rng)
    lines = ["block,q90,q95,q99,lo,hi"]
    for i, k in enumerate(keys):
        lines.append(f"{k},{q[0.90][i]},{q[0.95][i]},{q[0.99][i]},{lo[i]},{hi[i]}")
    return "\n".join(lines) + "\n"


def baseline_solver(name: str):
    @solver
    def _s():
        async def solve(state: TaskState, generate: Generate) -> TaskState:
            text = await sandbox().read_file("data/blocks.csv")
            await sandbox().write_file("predictions.csv", predictions_csv(name, text))
            return state
        return solve
    return _s()
