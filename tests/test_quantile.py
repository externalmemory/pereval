"""Quantile task: generator invariants, disguise integrity, baseline constants."""

from __future__ import annotations

import numpy as np
import pytest

from pereval.scorers.pinball import aggregate, parse_predictions, score_block
from pereval.tasks.quantile.baselines import point_estimate, predictions_csv
from pereval.tasks.quantile.generator import (
    M_MIN,
    N_DRAW,
    generate,
    load_series,
    prompt_text,
    sigfig,
)
from pereval.tasks.quantile.task import _blocks_csv


@pytest.fixture(scope="module")
def blocks():
    return generate(1, n_blocks=12)


# --- generator invariants --------------------------------------------------

def test_deterministic():
    a, b = generate(7, n_blocks=6), generate(7, n_blocks=6)
    assert [x["series"] for x in a] == [x["series"] for x in b]
    for x, y in zip(a, b):
        assert np.array_equal(x["shown"], y["shown"])
        assert np.array_equal(x["pop"], y["pop"])


def test_different_seeds_differ():
    assert generate(1, n_blocks=6)[0]["series"] != generate(999, n_blocks=6)[0]["series"] \
        or not np.array_equal(generate(1, n_blocks=6)[0]["shown"],
                              generate(999, n_blocks=6)[0]["shown"])


def test_blocks_come_from_distinct_series(blocks):
    """Load-bearing: repeated series would let the model pool across blocks."""
    assert len({b["series"] for b in blocks}) == len(blocks)


def test_population_excludes_the_drawn_values(blocks):
    for b in blocks:
        assert len(b["pop"]) == b["m"] - N_DRAW
        assert len(b["shown"]) == N_DRAW


def test_window_is_large_enough(blocks):
    assert all(b["m"] >= M_MIN for b in blocks)


def test_shown_and_x_hold_the_same_values(blocks):
    for b in blocks:
        assert np.array_equal(np.sort(b["shown"]), b["x"])


def test_shown_is_not_in_sorted_order(blocks):
    """The display order must not encode anything; sorted output would mean the
    draw order was lost and could tempt a chronological ordering later."""
    assert any(not np.all(np.diff(b["shown"]) > 0) for b in blocks)


def test_drawn_values_and_population_share_one_window_and_scale(blocks):
    """pop and x must be the same window under the same scale, minus the draw."""
    series = load_series()
    for b in blocks:
        w = series[b["series"]][b["start"]:b["start"] + b["m"]] * b["scale"]
        merged = np.sort(np.concatenate([b["pop"], b["x"]]))
        assert np.allclose(merged, np.sort(w), rtol=0, atol=5e-3 * np.abs(w).max())


def test_sigfig_rounds_to_four_significant_figures():
    got = sigfig(np.array([123456.0, 0.000123456, -1.234567, 0.0]))
    assert got == pytest.approx([123500.0, 0.0001235, -1.235, 0.0], rel=1e-9)


def test_scales_vary_across_blocks(blocks):
    s = np.array([b["scale"] for b in blocks])
    assert s.min() > 0 and s.max() / s.min() > 2.0


# --- disguise integrity ----------------------------------------------------

def test_prompt_leaks_neither_series_names_nor_population(blocks):
    """Only the drawn values and m may appear: no series id, no window, and
    exactly N_DRAW numbers per block rather than any part of the population."""
    text = prompt_text(blocks)
    assert "series.npz" not in text
    for b in blocks:
        assert b["series"] not in text
    body = text.split("Block 1")[1]
    for line in body.split("\n"):
        if line.startswith("  ") and "," in line:
            assert len(line.split(",")) == N_DRAW


def test_prompt_states_the_estimand_explicitly(blocks):
    """Leaving 'the 95th percentile' ambiguous would make this a reading test."""
    t = prompt_text(blocks).lower()
    assert "of the population" in t and "without" in t and "replacement" in t


def test_blocks_csv_round_trips(blocks):
    txt = _blocks_csv(blocks)
    rows = [r.split(",") for r in txt.strip().split("\n")[1:]]
    assert len(rows) == len(blocks) * N_DRAW
    got = {}
    for b, x in rows:
        got.setdefault(int(b), []).append(float(x))
    for b in blocks:
        assert np.allclose(np.sort(got[b["block"]]), b["x"], rtol=1e-6)


# --- baseline constants ----------------------------------------------------

@pytest.mark.parametrize("name,expected", [
    ("type7", 0.360), ("type8", 0.000), ("wei8", 1.6094), ("t6", 1.6094)])
def test_p99_p95_spread_constants(blocks, name, expected):
    """These rules touch only the top two order statistics at these tau, so the
    spread is an exact multiple of the top gap regardless of the population."""
    xs = np.stack([b["x"] for b in blocks])
    spread = (point_estimate(name, xs, 0.99) - point_estimate(name, xs, 0.95)) \
        / (xs[:, -1] - xs[:, -2])
    assert spread == pytest.approx(expected, abs=1e-3)


def test_extrapolators_exceed_the_sample_max_and_bounded_rules_do_not(blocks):
    xs = np.stack([b["x"] for b in blocks])
    assert np.all(point_estimate("wei8", xs, 0.99) > xs[:, -1])
    assert np.all(point_estimate("type7", xs, 0.99) <= xs[:, -1] + 1e-9)


def test_baselines_produce_scoreable_predictions(blocks):
    preds = parse_predictions(predictions_csv("wei8", _blocks_csv(blocks)))
    recs = [score_block(dict(pop=b["pop"], norm=b["norm"], x=b["x"]),
                        preds.get(b["block"])) for b in blocks]
    agg = aggregate(recs)
    assert agg["n_missing"] == 0 and agg["n_nonmonotonic"] == 0
    assert agg["pinball_regret"] > 0


def test_perfect_answer_beats_every_baseline(blocks):
    perfect = {b["block"]: dict(
        q90=float(np.quantile(b["pop"], 0.90)),
        q95=float(np.quantile(b["pop"], 0.95)),
        q99=float(np.quantile(b["pop"], 0.99)),
        lo=float(np.quantile(b["pop"], 0.95)) - 1e-9,
        hi=float(np.quantile(b["pop"], 0.95)) + 1e-9) for b in blocks}
    best = aggregate([score_block(dict(pop=b["pop"], norm=b["norm"], x=b["x"]),
                                  perfect[b["block"]]) for b in blocks])
    assert best["pinball_regret"] == pytest.approx(0.0, abs=1e-12)
    for name in ("type7", "type8", "hd", "wei8", "normal"):
        preds = parse_predictions(predictions_csv(name, _blocks_csv(blocks)))
        agg = aggregate([score_block(dict(pop=b["pop"], norm=b["norm"], x=b["x"]),
                                     preds.get(b["block"])) for b in blocks])
        assert agg["pinball_regret"] > best["pinball_regret"]


# --- metric disclosure -----------------------------------------------------

def test_disclosure_states_the_loss_and_its_asymmetry(blocks):
    """Without a stated loss, "estimate the p95" is underspecified: an
    essentially median-unbiased rule still loses on expected pinball loss, so a
    model aiming at unbiasedness would be scored against a target it was never
    given."""
    t = prompt_text(blocks)
    assert "pinball" in t.lower() and "rho_tau" in t
    assert "19 times" in t          # the tau/(1-tau) asymmetry at tau=0.95
    assert "perfect answer scores zero" in t


def test_disclosure_does_not_reveal_the_normaliser_or_the_population(blocks):
    """The IQR normaliser is a per-block constant and cannot change the optimal
    answer, so it stays out; nothing about the held-out values may appear."""
    t = prompt_text(blocks)
    assert "IQR" not in t and "interquartile" not in t.lower()
    for b in blocks:
        assert b["series"] not in t


def test_interval_is_specified_by_nominal_coverage_not_by_winkler(blocks):
    """Winkler's optimum on this task sits near 0.81 coverage, so disclosing it
    would invite deliberately undercovering intervals. Coverage is stated."""
    t = prompt_text(blocks).lower()
    assert "winkler" not in t
    assert "nominal 95%" in t


def test_disclosure_can_be_switched_off_for_an_ab_test(blocks):
    on, off = prompt_text(blocks, True), prompt_text(blocks, False)
    assert "pinball" not in off.lower()
    assert len(on) > len(off)
    # the data and the estimand must be identical in both arms
    for b in blocks:
        assert ", ".join(f"{v:g}" for v in b["shown"]) in off
    assert "OF THE POPULATION" in off
