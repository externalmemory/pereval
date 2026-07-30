"""Baselines that bracket the CCAR stress-loss task.

naive_baseline: ordinary least squares of the default rate on all nine macro
LEVELS (complete cases), extrapolated to the stress scenario, with a homoscedastic
interval from the training residual SD. It overfits collinear distractors, uses a
linear link that misses the probit curvature out of range, includes the COVID
anomaly without noticing, and mis-sizes the interval. The floor.

vasicek_baseline: the competent reference. It probit-transforms the default rate,
builds eighteen candidate drivers (all nine macros as levels and as YoY changes),
selects among them by backward elimination on sign plausibility and significance, and
fits the probit-LINEAR extended-Vasicek model by its closed form (probit OLS plus an
algebraic recovery of p, kappa, rho), with iterative outlier exclusion so the COVID
quarters (where the observed spike did not move the default) do not attenuate the
sensitivity. It projects the stress path with a proper probit predictive interval.

It is near the oracle on the `vasicek` family and competent-but-misspecified on
`threshold` and `interaction`, whose macro dependence is not linear. That is
intentional: a reference exact on every instance would only be measuring whether the
agent guessed one fixed law. Read its score per family, not pooled.

informed_baseline: the same fit, handed the true drivers from hidden truth. Not a
competitor, a decomposition. See its docstring.

Only informed_baseline touches hidden truth. The other two read train.csv and
scenario.csv and write predictions.csv, exercising the same sandbox path an agent uses.
"""

from __future__ import annotations

import csv
import io

import numpy as np
from inspect_ai.solver import Generate, TaskState, solver
from inspect_ai.util import sandbox
from scipy.stats import norm

MACROS = ["gdp", "unemployment", "hpi", "bbb_spread", "sp500", "djia", "nasdaq", "vix", "cpi"]
Z95 = 1.959964


def _read(text: str) -> dict[str, np.ndarray]:
    rows = list(csv.DictReader(io.StringIO(text)))
    cols = rows[0].keys() if rows else []
    out = {}
    for c in cols:
        out[c] = np.array([float(r[c]) if r[c] not in ("", None) else np.nan for r in rows])
    return out


def _yoy(level: np.ndarray) -> np.ndarray:
    y = np.full(len(level), np.nan)
    y[4:] = level[4:] / level[:-4] - 1.0
    return y


def _write(quarters, point, lo, hi) -> str:
    lines = ["quarter,y_pred,y_lower,y_upper"]
    for q, p, a, b in zip(quarters, point, lo, hi):
        lines.append(f"{int(q)},{p},{a},{b}")
    return "\n".join(lines) + "\n"


# --- naive OLS on all nine macro levels ------------------------------------

def _naive_fit_predict(train_text: str, scenario_text: str) -> str:
    tr = _read(train_text)
    sc = _read(scenario_text)
    X = np.column_stack([tr[m] for m in MACROS])
    y = tr["default_rate"]
    ok = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    Xo = np.column_stack([np.ones(ok.sum()), X[ok]])
    beta, *_ = np.linalg.lstsq(Xo, y[ok], rcond=None)
    s = float(np.std(y[ok] - Xo @ beta))
    Xs = np.column_stack([np.ones(len(sc["quarter"])), np.column_stack([sc[m] for m in MACROS])])
    yhat = Xs @ beta
    half = Z95 * s
    return _write(sc["quarter"], yhat, yhat - half, yhat + half)


# --- extended-Vasicek closed-form reference --------------------------------

def _robust_probit_ols(X, y, thresh=3.0, n_iter=3):
    mask = np.ones(len(y), dtype=bool)
    beta = np.zeros(X.shape[1])
    for _ in range(n_iter):
        beta, *_ = np.linalg.lstsq(X[mask], y[mask], rcond=None)
        resid = y - X @ beta
        s = resid[mask].std()
        new = np.abs(resid) <= thresh * s
        if new.sum() < X.shape[1] + 2 or np.array_equal(new, mask):
            mask = new if new.sum() >= X.shape[1] + 2 else mask
            break
        mask = new
    sigma2 = float(np.var(y[mask] - X[mask] @ beta))
    return beta, sigma2


def _candidates(tr: dict, sc: dict) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Eighteen candidate drivers: every macro as a level and as a YoY change.

    Each is returned as (in-time series, scenario series), standardized together on
    in-time moments. The YoY transforms are built on the concatenated path so the
    first scenario quarters can look back across the boundary, which is what a
    competent modeller would do and what the naive alternative gets wrong.
    """
    out = {}
    for m in MACROS:
        both = np.concatenate([tr[m], sc[m]])
        n = len(tr[m])
        for label, series in (("level", both), ("yoy", _yoy(both))):
            ref = series[:n][np.isfinite(series[:n])]
            if len(ref) < 8 or ref.std() == 0:
                continue
            z = (series - ref.mean()) / ref.std()
            out[f"{m}:{label}"] = (z[:n], z[n:])
    return out


# Macros that rise in a recession. Textbook domain knowledge, not an answer key: the
# reference uses it only to reject sign-implausible fits, which is the sign check any
# credit modeller applies before believing a coefficient.
_RECESSION_UP = {"unemployment", "bbb_spread", "vix"}


def _expected_sign(candidate: str) -> float:
    return 1.0 if candidate.split(":")[0] in _RECESSION_UP else -1.0


MAX_DRIVERS = 2  # the DGP uses two; keeping more only invites collinear blowup
T_MIN = 2.0      # significance bar for retaining a driver


def _backward_select(X: np.ndarray, y: np.ndarray, names: list[str]) -> list[int]:
    """Fit every candidate, then drop wrong-signed and insignificant ones one at a time.

    Standard credit-modelling practice, and empirically the best of the procedures
    tried. Measured pooled Winkler regret over 24 instances, three families:

        informed (told the true drivers)   0.276
        backward elimination, this one     0.430
        exhaustive pair search             0.490
        ridge over all 18 candidates       0.606
        lasso over all 18 candidates       0.669
        OLS on all nine levels (naive)     1.794
        degenerate answer                  1.390

    Shrinkage over the full candidate set does worse than selection, which is the
    point of the collinear distractors: three of the nine macros are near-duplicate
    equity indices, so a fit that keeps all of them gets large offsetting coefficients
    that cancel in sample and stop cancelling once the scenario leaves the observed
    range. Elimination keeps 1.6 variables on average, so the MAX_DRIVERS cap rarely
    binds; it is there to bound the model's dimension, not to do the work.

    None of this identifies the true pair reliably (3 of 24 exactly), and it does not
    need to: the surviving driver is usually a correlated proxy that moves the same way
    under the scenario. Recovering the right variable and predicting the right path are
    different achievements, and only the second one is scored.
    """
    live = list(range(X.shape[1]))
    while live:
        A = np.column_stack([np.ones(len(y))] + [X[:, j] for j in live])
        beta, sigma2 = _robust_probit_ols(A, y)
        se = np.sqrt(np.maximum(np.diag(sigma2 * np.linalg.pinv(A.T @ A)), 1e-30))
        t = beta / se
        wrong = [(k, j) for k, j in enumerate(live, 1)
                 if np.sign(beta[k]) != _expected_sign(names[j])]
        weak = [(k, j) for k, j in enumerate(live, 1) if abs(t[k]) < T_MIN]
        drop = wrong or weak
        if not drop and len(live) <= MAX_DRIVERS:
            break
        if not drop:  # all admissible but too many: shed the weakest
            drop = [(k, j) for k, j in enumerate(live, 1)]
        live.remove(min(drop, key=lambda kj: abs(t[kj[0]]))[1])
    return live


def _fit_selected(cands: dict, yv: np.ndarray, live: list[str]) -> tuple | None:
    """Fit the probit-linear model on named drivers, returning the scenario design."""
    live = [n for n in live if n in cands]
    if not live:
        return None
    cols = [cands[n][0] for n in live]
    ok = np.isfinite(yv) & np.all(np.isfinite(np.column_stack(cols)), axis=1)
    if ok.sum() < 20:
        return None
    X = np.column_stack([np.ones(ok.sum())] + [c[ok] for c in cols])
    beta, sigma2 = _robust_probit_ols(X, yv[ok])
    n_sc = len(cands[live[0]][1])
    Xs = np.column_stack([np.ones(n_sc)] + [cands[n][1] for n in live])
    return (sigma2, beta, Xs, live)


def _vasicek_fit_predict(train_text: str, scenario_text: str,
                         drivers: list[str] | None = None) -> str:
    """Probit-linear extended-Vasicek reference.

    With `drivers=None` it selects its own (see _backward_select), which is the honest
    competent anchor: the generator rotates which macros drive the response, so a
    reference exempt from feature selection would not be a fair comparison. Passing
    `drivers` forces the true ones and produces the informed anchor instead. The gap
    between the two is the measured cost of feature selection on this task.

    It remains probit-LINEAR by design, so even the informed variant is near-oracle
    only on the `vasicek` family and competent-but-misspecified on `threshold` and
    `interaction`.
    """
    tr = _read(train_text)
    sc = _read(scenario_text)
    yv = norm.ppf(np.clip(tr["default_rate"], 1e-6, 1 - 1e-6))
    cands = _candidates(tr, sc)

    if drivers is None:
        names = sorted(cands)
        Xin = np.column_stack([cands[n][0] for n in names])
        ok = np.isfinite(yv) & np.all(np.isfinite(Xin), axis=1)
        drivers = [names[j] for j in _backward_select(Xin[ok], yv[ok], names)]
    fit = _fit_selected(cands, yv, drivers)
    if fit is None:
        return _naive_fit_predict(train_text, scenario_text)

    sigma2, beta, Xs, _ = fit
    # Algebraic recovery of the Vasicek parameters from the probit-scale OLS fit:
    # dividing by sqrt(1 + sigma2) converts the fitted mean to the Phi^-1(p) + sum k*u
    # scale, and rho follows from the residual variance.
    scal = np.sqrt(1.0 + sigma2)
    rho = sigma2 / (1.0 + sigma2)
    lin = (Xs @ beta) / scal
    sr = np.sqrt(rho) / np.sqrt(1.0 - rho)
    a = lin / np.sqrt(1.0 - rho)
    point = norm.cdf(lin)  # E[dr | macros] = Phi(Phi^-1(p) + sum k*u)
    return _write(sc["quarter"], point, norm.cdf(a - Z95 * sr), norm.cdf(a + Z95 * sr))


@solver
def naive_baseline():
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        train = await sandbox().read_file("data/train.csv")
        scenario = await sandbox().read_file("data/scenario.csv")
        await sandbox().write_file("predictions.csv", _naive_fit_predict(train, scenario))
        return state

    return solve


@solver
def vasicek_baseline():
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        train = await sandbox().read_file("data/train.csv")
        scenario = await sandbox().read_file("data/scenario.csv")
        await sandbox().write_file("predictions.csv", _vasicek_fit_predict(train, scenario))
        return state

    return solve


@solver
def informed_baseline():
    """The same probit-linear fit, told which macros are the true drivers.

    This one READS HIDDEN TRUTH from the sample metadata, so it is a diagnostic anchor
    and not a competitor: no agent has this information. Its purpose is to split the
    task's difficulty in two. The gap from the oracle is estimation error plus, on the
    non-vasicek families, the cost of assuming a linear form; the gap from
    vasicek_baseline up to this row is the cost of feature selection alone.
    """

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        train = await sandbox().read_file("data/train.csv")
        scenario = await sandbox().read_file("data/scenario.csv")
        dgp = state.metadata["truth"]["meta"]["dgp"]
        drivers = [f"{dgp['d1']}:level", f"{dgp['d2']}:yoy"]
        await sandbox().write_file(
            "predictions.csv", _vasicek_fit_predict(train, scenario, drivers))
        return state

    return solve
