"""Baselines that bracket the CCAR stress-loss task.

naive_baseline: ordinary least squares of the default rate on all nine macro
LEVELS (complete cases), extrapolated to the stress scenario, with a homoscedastic
interval from the training residual SD. It overfits collinear distractors, uses a
linear link that misses the probit curvature out of range, includes the COVID
anomaly without noticing, and mis-sizes the interval. The floor.

vasicek_baseline: the competent reference. It builds the two true drivers
(standardized unemployment level and standardized HPI YoY), probit-transforms the
default rate, and fits the extended-Vasicek model by its closed form (probit OLS
plus an algebraic recovery of p, kappa, rho), with iterative outlier exclusion so
the COVID quarters (where the observed unemployment spike did not move the default)
do not attenuate the unemployment sensitivity. It projects the stress path with a
proper probit predictive interval. Near the oracle up to finite-sample error.

Neither uses the hidden parameters; both read only train.csv and scenario.csv and
write predictions.csv, exercising the same sandbox path an agent uses.
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


def _vasicek_fit_predict(train_text: str, scenario_text: str) -> str:
    tr = _read(train_text)
    sc = _read(scenario_text)

    unemp = tr["unemployment"]
    hpi_yoy = _yoy(tr["hpi"])
    u_m, u_s = np.nanmean(unemp), np.nanstd(unemp)
    y_m, y_s = np.nanmean(hpi_yoy), np.nanstd(hpi_yoy)
    u1 = (unemp - u_m) / u_s
    u2 = (hpi_yoy - y_m) / y_s
    dr = np.clip(tr["default_rate"], 1e-6, 1 - 1e-6)
    yv = norm.ppf(dr)

    ok = np.isfinite(u1) & np.isfinite(u2) & np.isfinite(yv)
    X = np.column_stack([np.ones(ok.sum()), u1[ok], u2[ok]])
    beta, sigma2 = _robust_probit_ols(X, yv[ok])
    scal = np.sqrt(1.0 + sigma2)
    p = beta[0] / scal
    k1, k2 = beta[1] / scal, beta[2] / scal
    rho = sigma2 / (1.0 + sigma2)

    # scenario drivers: HPI YoY spans the in-time/scenario boundary
    hpi_all = np.concatenate([tr["hpi"], sc["hpi"]])
    yoy_all = _yoy(hpi_all)[len(tr["hpi"]):]
    u1s = (sc["unemployment"] - u_m) / u_s
    u2s = (yoy_all - y_m) / y_s

    lin = p + k1 * u1s + k2 * u2s  # p here is beta0/scal = Phi^-1(p_hat)
    sr = np.sqrt(rho) / np.sqrt(1.0 - rho)
    a = lin / np.sqrt(1.0 - rho)
    point = norm.cdf(lin)  # E[dr | macros] = Phi(Phi^-1(p) + k1 u1 + k2 u2)
    lo = norm.cdf(a - Z95 * sr)
    hi = norm.cdf(a + Z95 * sr)
    return _write(sc["quarter"], point, lo, hi)


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
