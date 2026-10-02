"""Distribution, lifetime accounting and held-out interval scoring checks."""

import numpy as np
import pytest
from scipy.special import ndtri

from pereval.scorers.cecl import evaluation_losses, score_predictions
from pereval.tasks.cecl.baselines import predict
from pereval.tasks.cecl.generator import (
    csv_text,
    default_paths,
    generate,
    lifetime_loss,
    path_losses,
    public_files,
)


def test_marginal_means_and_latent_persistence():
    means = np.array([0.01, 0.04, 0.1, 0.2])
    draws = default_paths(means, 150000, np.random.default_rng(4), persistence=0.7)
    se = draws.std(axis=0) / np.sqrt(len(draws))
    assert np.all(abs(draws.mean(axis=0) - means) < 5 * se)
    latent = ndtri(draws)
    assert np.corrcoef(latent[:, 0], latent[:, 1])[0, 1] == pytest.approx(0.7, abs=0.01)


def test_zero_noise_and_endpoint_probabilities():
    rates = np.tile([0.03, 0.4, 0.05], (12, 1))
    draws = default_paths(rates[:, 0], 100, np.random.default_rng(1), rho=0)
    np.testing.assert_allclose(
        path_losses(100, rates, draws), lifetime_loss(100, 12, rates)
    )
    edges = default_paths([0, 1], 10, np.random.default_rng(1))
    np.testing.assert_array_equal(edges, np.tile([0, 1], (10, 1)))


def test_path_accounting_and_survivor_selection():
    rates = np.array([[0.1, 0.5, 0.2], [0.2, 0.25, 0]])
    assert path_losses(100, rates, [[0.1, 0.2]])[0] == pytest.approx(6.8)
    rates = np.tile([0.08, 0.5, 0], (40, 1))
    losses = []
    for persistence in (0, 0.8):
        pd = default_paths(
            rates[:, 0],
            100000,
            np.random.default_rng(2),
            rho=0.1,
            persistence=persistence,
        )
        losses.append(path_losses(100, rates, pd))
    assert losses[0].mean() == pytest.approx(lifetime_loss(100, 40, rates), abs=0.03)
    assert losses[1].mean() < losses[0].mean() - 0.2
    assert losses[1].std() > losses[0].std()


def test_reproducible_independent_oracle_and_public_isolation():
    b = generate(8, simulation=True)
    assert b == generate(8, simulation=True)
    old = generate(8)
    assert b["history"] == old["history"]
    assert b["pools"] == old["pools"]
    text = "".join(public_files(b).values())
    assert "loss_samples" not in text and "ecl_mc_se" not in text
    assert "aggregate_probit_ar1_v1" in text
    for p in b["truth"]:
        draws = evaluation_losses(p)
        assert 0 <= draws.min() <= draws.max() <= p["balance"]
        assert abs(draws.mean() - p["ecl"]) < 6 * p["ecl_mc_se"]
        assert 0.93 < np.mean((draws >= p["lower"]) & (draws <= p["upper"])) < 0.97
        assert p["lower"] != np.quantile(draws, 0.025)


def test_interval_oracle_missing_and_invalid_submissions():
    truth = generate(2, simulation=True)["truth"]
    rows = [
        {
            "pool_id": p["pool_id"],
            "ecl": p["ecl"],
            "ecl_lower": p["lower"],
            "ecl_upper": p["upper"],
        }
        for p in truth
    ]
    exact = score_predictions(truth, csv_text(rows))
    assert exact["ecl_regret"] == 0
    assert exact["winkler_regret"] == pytest.approx(0)
    assert exact["completion"] == pytest.approx(1)
    assert 0.93 < exact["coverage"] < 0.97
    missing = score_predictions(truth, None)
    assert missing["winkler_agent"] >= missing["winkler_degenerate"]
    assert missing["completion"] == 0
    for lo, hi in [(10, 1), (-1, 10), (0, float("inf")), (0, float("nan"))]:
        bad = [dict(r, ecl_lower=lo, ecl_upper=hi) for r in rows]
        assert score_predictions(truth, csv_text(bad))["interval_completion"] == 0
    assert score_predictions(truth, csv_text(rows + rows))["completion"] == 0
    point_only = csv_text([{"pool_id": p["pool_id"], "ecl": p["ecl"]} for p in truth])
    score = score_predictions(truth, point_only)
    assert score["point_completion"] == 1 and score["completion"] == 1
    assert score["submission_completion"] == 0


@pytest.mark.parametrize("scenario", ["baseline", "adverse", "benign"])
def test_public_reference_and_task_wiring(scenario):
    from pereval.tasks.cecl.task import SIMULATION_INSTRUCTIONS, cecl

    b = generate(3, scenario=scenario, simulation=True)
    score = score_predictions(b["truth"], predict(public_files(b)))
    naive = score_predictions(b["truth"], predict(public_files(b), "naive"))
    assert score["completion"] == pytest.approx(1)
    assert score["winkler_regret"] < naive["winkler_regret"]
    assert score["ecl_regret"] < score["zero_regret"]
    assert 0.85 < score["coverage"] < 1
    task = cecl(
        n_instances=1, seed=3, simulation=True, baseline="cohort", oracle_n=1000
    )
    assert "evaluation" in task.dataset[0].metadata["truth"][0]
    assert "pool_id,ecl,ecl_lower,ecl_upper" in SIMULATION_INSTRUCTIONS


@pytest.mark.parametrize("kwargs", [{"rho": 1}, {"persistence": 1}, {"n_paths": 0}])
def test_invalid_simulation_parameters(kwargs):
    args = {"n_paths": 100, "rng": np.random.default_rng(1)}
    args.update(kwargs)
    with pytest.raises(ValueError):
        default_paths([0.1], **args)


def test_default_task_requires_intervals_and_legacy_is_explicit():
    from inspect_ai.scorer._scorer import scorer_metrics

    from pereval.tasks.cecl.task import SIMULATION_INSTRUCTIONS, cecl

    default = cecl(n_instances=1, seed=4, baseline="cohort", oracle_n=100)
    legacy = cecl(n_instances=1, seed=4, baseline="cohort", simulation=False)
    assert "evaluation" in default.dataset[0].metadata["truth"][0]
    assert "loss_samples" not in legacy.dataset[0].metadata["truth"][0]
    assert "95% prediction intervals" in default.dataset[0].input
    assert "weighted squared error" in SIMULATION_INSTRUCTIONS
    assert next(iter(scorer_metrics(default.scorer[0]))) == "ecl_regret"
    assert next(iter(scorer_metrics(legacy.scorer[0]))) == "ecl_regret"


def test_compact_metadata_matches_archived_samples_and_mean_constant_anchor():
    import json

    truth = generate(7, simulation=True)["truth"]
    assert len(json.dumps(truth)) < 100_000
    archived = [dict(p, loss_samples=evaluation_losses(p).tolist()) for p in truth]
    assert score_predictions(truth, None) == score_predictions(archived, None)
    constant_rate = sum(p["ecl"] for p in truth) / sum(p["balance"] for p in truth)
    rows = [
        {
            "pool_id": p["pool_id"],
            "ecl": p["ecl"],
            "ecl_lower": constant_rate * p["balance"],
            "ecl_upper": constant_rate * p["balance"],
        }
        for p in truth
    ]
    result = score_predictions(truth, csv_text(rows))
    assert result["winkler_agent"] == pytest.approx(result["winkler_degenerate"])


def test_repeated_runs_rank_mean_error_even_with_interval_diagnostics():
    from inspect_ai.scorer import Score

    from pereval.scorers.stability import stability

    result = stability()(
        [
            Score(value={"ecl_regret": 0.1, "winkler_regret": 8.0}),
            Score(value={"ecl_regret": 0.3, "winkler_regret": 1.0}),
        ]
    )
    assert result.value["regret_worst"] == 0.3
    assert result.value["regret_spread"] == pytest.approx(0.2)


def test_negative_interval_difference_is_preserved_and_clipped():
    truth = [
        {
            "pool_id": "a",
            "balance": 100,
            "ecl": 50,
            "lower": 0,
            "upper": 100,
            "loss_samples": [50] * 100,
        }
    ]
    rows = [{"pool_id": "a", "ecl": 50, "ecl_lower": 50, "ecl_upper": 50}]
    result = score_predictions(truth, csv_text(rows))
    assert result["winkler_regret_raw"] < 0
    assert result["winkler_regret"] == 0
    assert result["regret_worst"] == result["ecl_regret"] == 0
