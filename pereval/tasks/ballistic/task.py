"""Inspect task wrapper for the ballistic trajectory model-building task.

Each instance is generated host-side (where py-ballisticcalc lives) and only the
neutral train.csv / test.csv are injected into the agent's container. The
generator, the ground-truth oracle, and the ballistics engine never enter the
sandbox, and the ground truth travels host-side in sample metadata, read only by
the scorer.

What forces the agent to model the data rather than re-simulate it is that
category identifiers are opaque and the ballistic parameters are randomized per
run: there is no known load to look up, and any simulation would first require
estimating each category's parameters from the training data, which is the task
itself. The sandbox additionally has no network, which blocks the weaker
shortcuts of installing the exact engine, downloading its drag tables, or
querying an online calculator. It does not prevent the agent from recognizing the
physics from the data, which is legitimate.

Run (requires Docker and a model):
    inspect eval pereval/tasks/ballistic/task.py --model openai-api/zen/<id>
    inspect eval pereval/tasks/ballistic/task.py -T n_instances=8 -T seed=123
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.solver import basic_agent, system_message
from inspect_ai.tool import bash, python

from pereval.scorers.ballistic import ballistic_scorer
from pereval.tasks.ballistic.baselines import parabola_baseline
from pereval.tasks.ballistic.generator import (
    build_truth,
    generate,
    test_csv_text,
    train_csv_text,
)

COMPOSE = (Path(__file__).parent / "compose.yaml").as_posix()

INSTRUCTIONS = """\
You are given a regression dataset in the `data/` directory:

- `data/train.csv` with columns category,x,y: labeled training observations.
- `data/test.csv` with columns category,x: inputs for which you must predict y.

`category` is a categorical group identifier (an opaque string). Different
categories may follow different relationships between x and y. For each category,
the test inputs include x values BEYOND the range seen in training, so naive
interpolation or non-extrapolating models (for example tree ensembles) will do
poorly on them. The training y values contain observation noise.

Build a predictive model. For every row in `data/test.csv`, produce:
- a point estimate of y, and
- a 95% prediction interval [lower, upper] for a NEW noisy observation of y at
  that (category, x). This is a predictive interval for a fresh observation, not
  a confidence interval for the mean, so it must account for the observation
  noise, not only estimation uncertainty.

Write your predictions to `predictions.csv` in the working directory with columns
exactly:

    category,x,y_pred,y_lower,y_upper

one row per test input, with category and x copied exactly from data/test.csv.

You have Python with numpy, pandas, scikit-learn, statsmodels, and scipy. You do
not have internet access.

Each code execution runs in a FRESH interpreter: variables, imports, and loaded
data do NOT carry over between executions. So do not build up state across
several small snippets. Instead write a single self-contained script that imports
what it needs, reads both CSVs, fits your model, and writes predictions.csv in
one run. The reliable workflow is to save that script to a file (for example
`solution.py`) and run it with `python solution.py`, then edit the file and rerun
until predictions.csv is complete and correct.

Produce output early. As soon as possible, write a COMPLETE predictions.csv with
a simple model covering every test row, even a rough one, and only then refine
it. Always keep a valid, complete predictions.csv on disk, so that a usable
submission exists at any point. Do not spend your whole budget exploring models
before writing any predictions. Verify predictions.csv exists and has one row per
test input before submitting.
"""


def _build_samples(n_instances: int, seed: int | None, oracle_n: int) -> list[Sample]:
    base = seed if seed is not None else int(np.random.SeedSequence().generate_state(1)[0])
    seeds = np.random.SeedSequence(base).generate_state(n_instances, dtype=np.uint32)
    samples = []
    for i, s in enumerate(seeds):
        bundle = generate(seed=int(s), oracle_n=oracle_n)
        samples.append(
            Sample(
                input=INSTRUCTIONS,
                id=f"instance-{i}-seed-{int(s)}",
                files={
                    "data/train.csv": train_csv_text(bundle),
                    "data/test.csv": test_csv_text(bundle),
                },
                metadata={"truth": build_truth(bundle)},
            )
        )
    return samples


@task
def ballistic(
    n_instances: int = 5,
    seed: int | None = None,
    oracle_n: int = 2000,
    message_limit: int = 150,
    baseline: bool = False,
) -> Task:
    """The ballistic extrapolation task.

    baseline=True swaps the agent for the naive per-category parabola baseline
    (no model calls), producing the reference score models must beat. Run it with
    any placeholder model, e.g. --model mockllm/model.
    """
    if baseline:
        solver = parabola_baseline()
    else:
        solver = basic_agent(
            init=system_message(INSTRUCTIONS),
            tools=[bash(timeout=180), python(timeout=180)],
            message_limit=message_limit,
        )

    return Task(
        dataset=_build_samples(n_instances, seed, oracle_n),
        solver=solver,
        scorer=ballistic_scorer(),
        sandbox=("docker", COMPOSE),
    )
