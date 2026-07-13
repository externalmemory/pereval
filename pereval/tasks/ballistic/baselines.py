"""Non-agentic baseline solvers for the ballistic task.

A baseline anchors model scores: a frontier model that cannot beat a naive
per-category parabola is not demonstrating the capability the task probes. The
parabola baseline uses only the agent-visible data (never the ground-truth
oracle), reading train.csv/test.csv from the sandbox and writing predictions.csv
by the same path a real agent would, so running it also exercises the full
sandbox-to-scorer plumbing.

It is deliberately naive: a quadratic (parabola) fit per category, extrapolated
to the held-out distances, with a homoscedastic 95% interval from the training
residual standard deviation. Both choices are expected to fail on this task,
extrapolating a parabola misses the drag curvature, and a constant-width interval
ignores the growth of predictive uncertainty beyond the training range, so its
score is a floor an honest model should clear. The degree is fixed at 2: a
higher-order polynomial diverges even faster out of range, and is not a baseline
anyone would defend.
"""

from __future__ import annotations

import csv
import io

import numpy as np
from inspect_ai.solver import Generate, TaskState, solver
from inspect_ai.util import sandbox

Z95 = 1.959964  # standard normal 97.5th percentile
DEGREE = 2  # quadratic (parabola); higher orders diverge faster out of range


def _fit_and_predict(train_text: str, test_text: str) -> str:
    train: dict[str, list[tuple[float, float]]] = {}
    for row in csv.DictReader(io.StringIO(train_text)):
        train.setdefault(row["category"], []).append((float(row["x"]), float(row["y"])))

    models: dict[str, tuple[np.ndarray, float]] = {}
    for cid, pts in train.items():
        xs = np.array([p[0] for p in pts])
        ys = np.array([p[1] for p in pts])
        # Fall back below quadratic only if a category has too few distinct x to
        # fit one; never go above.
        deg = min(DEGREE, max(1, len(np.unique(xs)) - 1))
        coeffs = np.polyfit(xs, ys, deg)
        resid = ys - np.polyval(coeffs, xs)
        dof = max(1, len(ys) - (deg + 1))  # residual SD with dof correction
        s = float(np.sqrt(np.sum(resid**2) / dof))
        models[cid] = (coeffs, s)

    lines = ["category,x,y_pred,y_lower,y_upper"]
    for row in csv.DictReader(io.StringIO(test_text)):
        cid = row["category"]
        x = float(row["x"])
        coeffs, s = models[cid]
        yhat = float(np.polyval(coeffs, x))
        half = Z95 * s
        lines.append(f"{cid},{x},{yhat},{yhat - half},{yhat + half}")
    return "\n".join(lines) + "\n"


@solver
def parabola_baseline():
    """Fit one quadratic per category and extrapolate to the held-out distances."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        train_text = await sandbox().read_file("data/train.csv")
        test_text = await sandbox().read_file("data/test.csv")
        await sandbox().write_file("predictions.csv", _fit_and_predict(train_text, test_text))
        return state

    return solve
