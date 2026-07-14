"""Scorer for the ballistic trajectory task.

Thin adapter over the shared, task-generic core in pereval.scorers.interval. The
ballistic target is linear (drop in meters, no wrapping), so period is None.
Points are keyed by (category, x). See interval.py for the scoring math and
pereval/tasks/ballistic for the task.

The pure names re-exported here (interval_score, score_instance,
parse_predictions) are what the scorer validation suite exercises directly.
"""

from __future__ import annotations

import numpy as np

from pereval.scorers.interval import (
    interval_score,  # re-exported
    make_interval_scorer,
    parse_predictions as _parse,
    score_points,
)

__all__ = ["interval_score", "parse_predictions", "score_instance", "ballistic_scorer"]

_KEYS = ["category", "x"]


def _points(truth: dict) -> list[dict]:
    cats = truth["categories"]
    return [
        {
            "key": (tp["category"], float(tp["x_m"])),
            "class": cats[tp["category"]]["class"],
            "true_mean": tp["true_mean_y_m"],
            "mc": np.asarray(tp["mc_samples_m"], dtype=float),
        }
        for tp in truth["test"]
    ]


def parse_predictions(text: str | None):
    return _parse(text, _KEYS)


def score_instance(truth: dict, preds: dict) -> dict:
    return score_points(_points(truth), preds, period=None)


def ballistic_scorer():
    return make_interval_scorer("ballistic", _KEYS, None, _points)
