"""Inspect task wrappers for the orbital-angle tasks (two-body and three-body).

Same isolation and scoring model as the ballistic task: instances are generated
host-side, only neutral CSVs enter the agent's sandbox, ground truth travels in
sample metadata, and predictions are scored with the shared oracle-anchored
interval scorer at period=360 (the target is a circular angle in degrees). The
sandbox is the shared general modeling image (no simulator, no network).

Run (requires Docker and a model):
    inspect eval pereval/tasks/orbit/task.py@twobody --model openai-api/zen/<id>
    inspect eval pereval/tasks/orbit/task.py@threebody -T n_instances=8
    inspect eval pereval/tasks/orbit/task.py@twobody -T baseline=true --model mockllm/model
"""

from __future__ import annotations

import numpy as np
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.solver import basic_agent, system_message
from inspect_ai.tool import bash, python

from pereval.scorers.interval import make_interval_scorer
from pereval.tasks.ballistic.task import COMPOSE  # shared general modeling sandbox
from pereval.tasks.orbit.baselines import harmonic_baseline
from pereval.tasks.orbit.generator import (
    build_truth,
    generate_threebody,
    generate_twobody,
    test_csv_text,
    train_csv_text,
    truth_to_points,
)

_TAIL = """\
The measurements contain observation noise, and the test days lie BEYOND the
range of days seen in training.

Build a predictive model. For every row in `data/test.csv`, produce a point
estimate of {target} and a 95% prediction interval [lower, upper] for a NEW noisy
measurement of {target} at that t. {target} is an angle in degrees and wraps at
360 (359 and 1 are two degrees apart, not 358). The interval is for a fresh noisy
measurement, so it must account for the observation noise.

Write your predictions to `predictions.csv` in the working directory with columns
exactly:

    t,y_pred,y_lower,y_upper

one row per test input, with t copied exactly from data/test.csv, and the angle
columns in degrees.

You have Python with numpy, pandas, scikit-learn, statsmodels, and scipy. You do
not have internet access. Each code execution runs in a FRESH interpreter, so
write a single self-contained script (save it to a file and run it) rather than
relying on state carrying over between executions. Produce a complete
predictions.csv early, even from a rough model, and keep a valid one on disk;
refine it after. Verify it has one row per test input before submitting.
"""

TWOBODY = (
    """\
You are given a time series in the `data/` directory:

- `data/train.csv` with columns t,alpha: t is time in days, alpha is a measured
  angle in degrees (0 to 360).
- `data/test.csv` with a column t: future days for which you must predict alpha.
"""
    + _TAIL.format(target="alpha")
)

THREEBODY = (
    """\
You are given a time series in the `data/` directory:

- `data/train.csv` with columns t,alpha,beta: t is time in days, alpha and beta
  are two measured angles in degrees (0 to 360).
- `data/test.csv` with a column t: future days for which you must predict beta.

The two angles are recorded from the same moving vantage point, so they are
related; alpha may carry information useful for predicting beta.
"""
    + _TAIL.format(target="beta")
)


def _samples(generate, instructions, n_instances, seed, oracle_n):
    base = seed if seed is not None else int(np.random.SeedSequence().generate_state(1)[0])
    seeds = np.random.SeedSequence(base).generate_state(n_instances, dtype=np.uint32)
    samples = []
    for i, s in enumerate(seeds):
        bundle = generate(seed=int(s), oracle_n=oracle_n)
        samples.append(
            Sample(
                input=instructions,
                id=f"instance-{i}-seed-{int(s)}",
                files={
                    "data/train.csv": train_csv_text(bundle),
                    "data/test.csv": test_csv_text(bundle),
                },
                metadata={"truth": build_truth(bundle)},
            )
        )
    return samples


def _build(generate, instructions, name, target, n_instances, seed, oracle_n, message_limit, baseline):
    if baseline:
        solver = harmonic_baseline(target=target)
    else:
        solver = basic_agent(
            init=system_message(instructions),
            tools=[bash(timeout=180), python(timeout=180)],
            message_limit=message_limit,
        )
    return Task(
        dataset=_samples(generate, instructions, n_instances, seed, oracle_n),
        solver=solver,
        scorer=make_interval_scorer(name, ["t"], 360.0, truth_to_points),
        sandbox=("docker", COMPOSE),
    )


@task
def twobody(
    n_instances: int = 5,
    seed: int | None = None,
    oracle_n: int = 2000,
    message_limit: int = 80,
    baseline: bool = False,
) -> Task:
    """Two-body: predict a planet's angle alpha at future days (the easier task)."""
    return _build(generate_twobody, TWOBODY, "twobody", "alpha",
                  n_instances, seed, oracle_n, message_limit, baseline)


@task
def threebody(
    n_instances: int = 5,
    seed: int | None = None,
    oracle_n: int = 2000,
    message_limit: int = 80,
    baseline: bool = False,
) -> Task:
    """Three-body: predict the outer planet's angle beta, with alpha as a distractor."""
    return _build(generate_threebody, THREEBODY, "threebody", "beta",
                  n_instances, seed, oracle_n, message_limit, baseline)
