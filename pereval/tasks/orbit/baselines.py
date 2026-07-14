"""Naive baseline for the orbital-angle tasks: harmonic regression.

A baseline that does not use Kepler's laws, only generic periodic structure. It
unwraps the target angle, estimates the fundamental period from the linear trend
(the mean motion), fits a linear term plus a few Fourier harmonics of that
period, and predicts by extrapolating the fit. Intervals use the training
residual SD (homoscedastic), which ignores period-estimate error accumulating
over the prediction horizon, so it is expected to undercover the further-out
points. It anchors the model scores and exercises the sandbox-to-scorer path.

For three-body the target is beta and alpha is ignored, so this baseline also
sets the bar for correctly treating alpha as an irrelevant distractor.
"""

from __future__ import annotations

import csv
import io

import numpy as np
from inspect_ai.solver import Generate, TaskState, solver
from inspect_ai.util import sandbox

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
