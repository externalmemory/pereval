"""Inspect task wrapper for the ballistic trajectory model-building task.

Sandbox isolation is the point: each instance is generated host-side (where
py-ballisticcalc lives) and only the neutral train.csv / test.csv are injected
into the agent's container. The generator, the ground-truth oracle, and the
ballistics engine never enter the sandbox, and the container has no network, so
the agent cannot recognize the domain and re-simulate it. The ground truth
travels host-side in sample metadata, read only by the scorer.

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
not have internet access. When predictions.csv is written and complete, submit.
"""


@task
def ballistic(
    n_instances: int = 5,
    seed: int | None = None,
    oracle_n: int = 2000,
    message_limit: int = 40,
) -> Task:
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

    return Task(
        dataset=samples,
        solver=basic_agent(
            init=system_message(INSTRUCTIONS),
            tools=[bash(timeout=180), python(timeout=180)],
            message_limit=message_limit,
        ),
        scorer=ballistic_scorer(),
        sandbox=("docker", COMPOSE),
    )
