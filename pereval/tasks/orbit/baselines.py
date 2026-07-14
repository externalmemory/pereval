"""Baselines for the orbital-angle tasks.

Two references that bracket each task:

harmonic_baseline: the naive one. It does not use Kepler's laws, only generic
periodic structure: unwrap the target angle, estimate the fundamental period from
the linear trend, fit a linear term plus a few Fourier harmonics, and extrapolate.
This is the epicycles approach, and it fails badly on three-body, whose apparent
inter-planet angle is not a clean Fourier series (retrograde, synodic-period), so
its score there is a floor, not a target.

kepler_baseline: the reference solution. It fits the actual generative model,
elliptical orbits, by nonlinear least squares (inner orbit from alpha, then the
outer orbit from beta given the inner one), and predicts from the fit. Because it
uses the right model class it recovers the signal to the noise floor and scores
near the oracle, which is what shows the tasks are well posed and separates "wrong
basis" from "hard problem". A model's distance from this reference measures how far
it is from the right approach.

Both use a homoscedastic 95% interval from the training residual SD.
"""

from __future__ import annotations

import csv
import io

import numpy as np
from inspect_ai.solver import Generate, TaskState, solver
from inspect_ai.util import sandbox
from scipy.optimize import least_squares

Z95 = 1.959964
N_HARMONICS = 3


def _design(t: np.ndarray, period: float) -> np.ndarray:
    cols = [np.ones_like(t), t]
    for k in range(1, N_HARMONICS + 1):
        w = 2.0 * np.pi * k * t / period
        cols += [np.cos(w), np.sin(w)]
    return np.vstack(cols).T


def _fit_and_predict(train_text: str, test_text: str, target: str) -> str:
    tr = list(csv.DictReader(io.StringIO(train_text)))
    t = np.array([float(r["t"]) for r in tr])
    y = np.array([float(r[target]) for r in tr])
    order = np.argsort(t)
    t, y = t[order], y[order]

    yu = np.degrees(np.unwrap(np.radians(y)))  # continuous longitude
    slope = np.polyfit(t, yu, 1)[0]  # mean motion, deg/day
    period = 360.0 / slope if slope > 1e-9 else (t[-1] - t[0])

    X = _design(t, period)
    coef, *_ = np.linalg.lstsq(X, yu, rcond=None)
    resid = yu - X @ coef
    dof = max(1, len(yu) - X.shape[1])
    s = float(np.sqrt(np.sum(resid**2) / dof))
    half = Z95 * s

    test_t = np.array([float(r["t"]) for r in csv.DictReader(io.StringIO(test_text))])
    yhat = _design(test_t, period) @ coef  # continuous; scorer localizes onto the circle

    lines = ["t,y_pred,y_lower,y_upper"]
    for tt, yh in zip(test_t, yhat):
        lines.append(f"{tt},{yh},{yh - half},{yh + half}")
    return "\n".join(lines) + "\n"


@solver
def harmonic_baseline(target: str):
    """Fit a linear-plus-harmonics model of the target angle and extrapolate."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        train_text = await sandbox().read_file("data/train.csv")
        test_text = await sandbox().read_file("data/test.csv")
        await sandbox().write_file("predictions.csv", _fit_and_predict(train_text, test_text, target))
        return state

    return solve


# --- Kepler reference: fit elliptical orbits ------------------------------

def _state(t, P, e, om_deg, t0, a):
    M = 2.0 * np.pi * (t - t0) / P
    E = M.copy()
    for _ in range(60):
        E = E - (E - e * np.sin(E) - M) / (1.0 - e * np.cos(E))
    nu = 2.0 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2))
    return np.radians(om_deg) + nu, a * (1.0 - e * np.cos(E))


def _kepler_longitude(t, p):
    th, _ = _state(t, p[0], p[1], p[2], p[3], 1.0)
    return np.degrees(th) % 360.0


def _apparent_longitude(t, ip, op):
    a2 = (op[0] / ip[0]) ** (2.0 / 3.0)
    th1, r1 = _state(t, ip[0], ip[1], ip[2], ip[3], 1.0)
    th2, r2 = _state(t, op[0], op[1], op[2], op[3], a2)
    return np.degrees(np.arctan2(r2 * np.sin(th2) - r1 * np.sin(th1),
                                 r2 * np.cos(th2) - r1 * np.cos(th1))) % 360.0


def _wrapdiff(a, b):
    return ((a - b + 180.0) % 360.0) - 180.0


def _period_guess(t, angle):
    yu = np.degrees(np.unwrap(np.radians(angle)))
    slope = np.polyfit(t, yu, 1)[0]
    return 360.0 / slope if abs(slope) > 1e-9 else (t[-1] - t[0])


def _fit_orbit(t, obs, forward, p0):
    """Least-squares fit of orbital elements to an observed angle, multi-started
    over eccentricity and orientation to avoid local minima."""
    best = None
    lo = [0.6 * p0, 0.0, -360.0, -2.0 * p0]
    hi = [1.5 * p0, 0.55, 720.0, 2.0 * p0]
    for e0 in (0.05, 0.2, 0.35):
        for om0 in (0.0, 90.0, 180.0, 270.0):
            try:
                res = least_squares(
                    lambda p: _wrapdiff(obs, forward(t, p)),
                    [p0, e0, om0, 0.0], bounds=(lo, hi), max_nfev=4000,
                )
            except Exception:
                continue
            cost = float(np.sum(res.fun**2))
            if best is None or cost < best[0]:
                best = (cost, res.x)
    return best[1]


def _kepler_fit_and_predict(train_text: str, test_text: str, target: str) -> str:
    tr = list(csv.DictReader(io.StringIO(train_text)))
    t = np.array([float(r["t"]) for r in tr])
    alpha = np.array([float(r["alpha"]) for r in tr])
    inner = _fit_orbit(t, alpha, _kepler_longitude, _period_guess(t, alpha))

    if target == "alpha":
        resid = _wrapdiff(alpha, _kepler_longitude(t, inner))
        predict = lambda tt: _kepler_longitude(tt, inner)  # noqa: E731
    else:
        beta = np.array([float(r["beta"]) for r in tr])
        outer = _fit_orbit(t, beta, lambda tt, p: _apparent_longitude(tt, inner, p), _period_guess(t, beta))
        resid = _wrapdiff(beta, _apparent_longitude(t, inner, outer))
        predict = lambda tt: _apparent_longitude(tt, inner, outer)  # noqa: E731

    s = float(np.sqrt(np.mean(resid**2)))
    half = Z95 * s
    test_t = np.array([float(r["t"]) for r in csv.DictReader(io.StringIO(test_text))])
    yhat = predict(test_t)
    lines = ["t,y_pred,y_lower,y_upper"]
    for tt, yh in zip(test_t, yhat):
        lines.append(f"{tt},{yh},{yh - half},{yh + half}")
    return "\n".join(lines) + "\n"


@solver
def kepler_baseline(target: str):
    """Fit elliptical orbits (inner from alpha, outer from beta) and predict."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        train_text = await sandbox().read_file("data/train.csv")
        test_text = await sandbox().read_file("data/test.csv")
        await sandbox().write_file("predictions.csv", _kepler_fit_and_predict(train_text, test_text, target))
        return state

    return solve
