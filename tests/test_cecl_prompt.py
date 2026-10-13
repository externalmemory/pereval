"""Guards the per-pool interval wording in the CECL simulation prompt.

A free-model smoke run produced a complete, correctly-implemented submission that
still scored coverage 0.461 against a nominal 0.95, because the prompt asked for
"a central 95% interval for aggregate lifetime loss" and the model read
"aggregate" as across pools rather than across loans within a pool. It built a
portfolio interval and allocated it, which is too narrow per pool because pool
losses do not diversify away.

Reproducing that reading on the same instance gave width 0.0174 against the
model's observed 0.0166, so the wording accounted for the narrowness almost
exactly. These tests pin the disambiguation so the defect cannot return
silently, and quantify why it mattered.
"""

from __future__ import annotations

import numpy as np
import pytest

from pereval.scorers.cecl import score_predictions
from pereval.tasks.cecl.generator import (
    _rates,
    csv_text,
    default_paths,
    extend_rates,
    generate,
    path_losses,
)
from pereval.tasks.cecl.task import SIMULATION_INSTRUCTIONS

# the instance the task actually builds for `-T seed=1`, via SeedSequence
SEED = 1835504127


def test_prompt_asks_for_per_pool_intervals_and_forbids_allocation():
    text = SIMULATION_INSTRUCTIONS.lower()
    assert "that\npool's own lifetime loss" in text or "pool's own lifetime loss" in text
    assert "scored on its own" in text
    # the specific wrong construction is named, not merely omitted
    assert "portfolio-wide" in text and "split it across pools" in text
    assert "no portfolio-level interval is requested or scored" in text


def test_prompt_pins_the_meaning_of_aggregate():
    """The word still appears, because the response law needs it, so it is defined."""
    text = SIMULATION_INSTRUCTIONS
    assert "aggregate" in text
    assert "aggregated over the many loans inside one pool, never" in text
    assert "aggregated across pools" in text


def _pool_loss_paths(bundle, n=4000):
    """Correct per-pool loss paths: shared shocks within a segment, independent across."""
    x = np.zeros((80, 2))
    rng = np.random.default_rng(SEED)
    for t in range(1, 80):
        x[t] = 0.65 * x[t - 1] + 0.6 * rng.multivariate_normal(
            [0, 0], [[1, -0.5], [-0.5, 1]]
        )
    fut = np.array(
        [
            [r["unemployment"] - 5, (r["hpi_growth"] - 0.03) / 0.04]
            for r in bundle["forecast"]
        ]
    )
    policy = bundle["policy"]
    pools = {p["pool_id"]: p for p in bundle["truth"]}
    out = {}
    for si, seg in enumerate(("A", "B", "C")):
        coef = np.array(bundle["parameters"][seg])
        hist = _rates(x, coef).mean(axis=0)
        full = extend_rates(_rates(fut, coef), hist, 40, policy["reversion_quarters"])
        draws = default_paths(
            full[:, 0], n, np.random.default_rng(500 + si),
            policy["rho"], policy["persistence"],
        )
        for j, term in enumerate((4, 12, 24, 40)):
            pid = f"{seg}{j + 1}"
            path = extend_rates(
                _rates(fut, coef), hist, term, policy["reversion_quarters"]
            )
            out[pid] = path_losses(pools[pid]["balance"], path, draws[:, :term])
    return out


def test_allocated_portfolio_interval_is_materially_too_narrow():
    """Why the wording mattered: the wrong reading roughly halves the width.

    Both submissions use the same correct simulation and the same means, so the
    only difference is which quantity the interval bounds.
    """
    bundle = generate(SEED, 80, 8, 4, "baseline", simulation=True, oracle_n=2000)
    paths = _pool_loss_paths(bundle)
    ids = list(paths)
    losses = np.column_stack([paths[p] for p in ids])
    means = losses.mean(axis=0)

    per_pool = [
        {
            "pool_id": p,
            "ecl": means[i],
            "ecl_lower": np.quantile(losses[:, i], 0.025),
            "ecl_upper": np.quantile(losses[:, i], 0.975),
        }
        for i, p in enumerate(ids)
    ]
    total = losses.sum(axis=1)
    lo, hi = np.quantile(total, 0.025), np.quantile(total, 0.975)
    share = means / means.sum()
    allocated = [
        {
            "pool_id": p,
            "ecl": means[i],
            "ecl_lower": lo * share[i],
            "ecl_upper": hi * share[i],
        }
        for i, p in enumerate(ids)
    ]

    right = score_predictions(bundle["truth"], csv_text(per_pool))
    wrong = score_predictions(bundle["truth"], csv_text(allocated))

    # the intended reading is near the oracle and covers at nominal
    assert right["coverage"] == pytest.approx(0.95, abs=0.03)
    # the allocated reading is far too narrow and under-covers badly
    assert wrong["mean_width"] < 0.7 * right["mean_width"]
    assert wrong["coverage"] < 0.80
    assert wrong["winkler_regret"] > 20 * right["winkler_regret"]


def test_summing_per_pool_bounds_exceeds_the_portfolio_band():
    """The arithmetic behind the warning, independent of any scoring."""
    bundle = generate(SEED, 80, 8, 4, "baseline", simulation=True, oracle_n=2000)
    paths = _pool_loss_paths(bundle)
    losses = np.column_stack([paths[p] for p in paths])
    total = losses.sum(axis=1)
    summed_width = sum(
        np.quantile(losses[:, i], 0.975) - np.quantile(losses[:, i], 0.025)
        for i in range(losses.shape[1])
    )
    portfolio_width = np.quantile(total, 0.975) - np.quantile(total, 0.025)
    assert summed_width > portfolio_width
