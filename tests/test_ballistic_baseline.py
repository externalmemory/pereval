"""Unit tests for the parabola baseline's pure fit-and-predict core."""

from __future__ import annotations

import numpy as np

from pereval.scorers.ballistic import parse_predictions
from pereval.tasks.ballistic.baselines import _fit_and_predict


def test_recovers_known_quadratic_in_interpolation():
    xs = np.arange(0.0, 401.0, 25.0)
    ys = 3.0 - 0.001 * xs - 5e-6 * xs**2  # exact quadratic, no noise
    train = "category,x,y\n" + "\n".join(f"G,{x},{y}" for x, y in zip(xs, ys))
    test = "category,x\nG,300.0\n"
    preds = parse_predictions(_fit_and_predict(train, test))
    point, lo, hi = preds[("G", 300.0)]
    expected = 3.0 - 0.001 * 300.0 - 5e-6 * 300.0**2
    assert abs(point - expected) < 1e-6  # recovers the generating quadratic
    assert lo <= point <= hi


def test_noise_free_interval_is_degenerate():
    xs = np.arange(0.0, 401.0, 25.0)
    ys = -1e-5 * xs**2
    train = "category,x,y\n" + "\n".join(f"G,{x},{y}" for x, y in zip(xs, ys))
    test = "category,x\nG,500.0\n"
    point, lo, hi = parse_predictions(_fit_and_predict(train, test))[("G", 500.0)]
    assert hi - lo < 1e-6  # zero residual -> zero-width interval


def test_per_category_independent_fits():
    rows = ["category,x,y"]
    for x in np.arange(0.0, 201.0, 25.0):
        rows.append(f"A,{x},{2.0 * x}")     # linear up
        rows.append(f"B,{x},{-2.0 * x}")    # linear down
    train = "\n".join(rows)
    test = "category,x\nA,300.0\nB,300.0\n"
    preds = parse_predictions(_fit_and_predict(train, test))
    assert preds[("A", 300.0)][0] > 500.0
    assert preds[("B", 300.0)][0] < -500.0


def test_interval_widens_with_residual_noise():
    rng = np.random.default_rng(0)
    xs = np.repeat(np.arange(0.0, 201.0, 25.0), 5)
    base = -1e-5 * xs**2
    train_quiet = "category,x,y\n" + "\n".join(f"G,{x},{y}" for x, y in zip(xs, base))
    train_noisy = "category,x,y\n" + "\n".join(
        f"G,{x},{y}" for x, y in zip(xs, base + rng.normal(0, 0.5, len(xs)))
    )
    test = "category,x\nG,250.0\n"
    _, lo_q, hi_q = parse_predictions(_fit_and_predict(train_quiet, test))[("G", 250.0)]
    _, lo_n, hi_n = parse_predictions(_fit_and_predict(train_noisy, test))[("G", 250.0)]
    assert (hi_n - lo_n) > (hi_q - lo_q)
