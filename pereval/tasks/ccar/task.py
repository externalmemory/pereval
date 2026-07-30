"""Inspect task wrapper for the CCAR stress-loss task.

Same isolation and scoring model as the other tasks: each instance is generated
host-side, only neutral CSVs enter the sandbox, ground truth travels in sample
metadata, and the 9 stressed quarters are scored with the shared oracle-anchored
interval scorer (linear, keyed by quarter). Nothing about the data-generating
process (the drivers, the transforms, the functional form, the crisis mechanism)
is disclosed.

The response law is drawn per instance and its functional form rotates over three
families, so nothing about it is recoverable from this repository; see the generator
docstring for why that is load-bearing rather than cosmetic.

Run (requires Docker and a model):
    inspect eval pereval/tasks/ccar/task.py --model openai-api/zen/<id>
    inspect eval pereval/tasks/ccar/task.py -T baseline=vasicek --model mockllm/model
    inspect eval pereval/tasks/ccar/task.py -T baseline=naive --model mockllm/model
    inspect eval pereval/tasks/ccar/task.py -T family=threshold      # pin the form
    inspect eval pereval/tasks/ccar/task.py -T n_instances=1 -T repeats=5  # stability
"""

from __future__ import annotations

import numpy as np
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.solver import basic_agent, system_message
from inspect_ai.tool import bash, python

from pereval.scorers.interval import make_interval_scorer
from pereval.scorers.stability import epochs as _epochs
from pereval.tasks.ballistic.task import COMPOSE  # shared general modeling sandbox
from pereval.tasks.ccar.baselines import informed_baseline, naive_baseline, vasicek_baseline
from pereval.tasks.ccar.generator import (
    FAMILIES,
    build_truth,
    generate,
    scenario_csv_text,
    train_csv_text,
    truth_to_points,
)

INSTRUCTIONS = """\
You are building a stress loss model. In the `data/` directory:

- `data/train.csv`: a quarterly history with columns `quarter`, nine macroeconomic
  series (gdp, unemployment, hpi, bbb_spread, sp500, djia, nasdaq, vix, cpi), and
  `default_rate` (the portfolio's quarterly annualized default rate, a fraction).
  Some macro series are blank for early quarters (they began later); handle the
  missing values as you see fit.
- `data/scenario.csv`: the same nine macro series for nine future quarters under a
  forward stress scenario. It has no default_rate; that is what you predict.

Build a model of the default rate from the macro history, then apply it to the
scenario. For every row in `data/scenario.csv`, produce a point estimate of the
default rate and a 95% prediction interval [lower, upper] for that quarter. The
scenario pushes the drivers beyond the range seen in training, so a model that
only fits in-sample may extrapolate poorly. Not all nine series necessarily
matter, and the ones that do may enter through a transformation rather than as a
raw level. The interval should reflect genuine forecast uncertainty.

Write your predictions to `predictions.csv` in the working directory with columns
exactly:

    quarter,y_pred,y_lower,y_upper

one row per scenario quarter, with quarter copied from data/scenario.csv, and the
default-rate columns as fractions.

You have Python with numpy, pandas, scikit-learn, statsmodels, and scipy. You do
not have internet access. Each code execution runs in a FRESH interpreter, so
write a single self-contained script (save it to a file and run it) rather than
relying on state carrying over between executions. Produce a complete
predictions.csv early, even from a rough model, and keep a valid one on disk;
refine it after. Verify it has one row per scenario quarter before submitting.
"""


def _samples(n_instances, seed, oracle_n, n_intime, family):
    base = seed if seed is not None else int(np.random.SeedSequence().generate_state(1)[0])
    seeds = np.random.SeedSequence(base).generate_state(n_instances, dtype=np.uint32)
    samples = []
    for i, s in enumerate(seeds):
        # Rotate the response family across instances rather than drawing it, so a
        # shipped dataset is balanced over FAMILIES instead of balanced in
        # expectation. Pinning `family` overrides this.
        fam = family or FAMILIES[i % len(FAMILIES)]
        bundle = generate(seed=int(s), n_intime=n_intime, oracle_n=oracle_n, family=fam)
        samples.append(
            Sample(
                input=INSTRUCTIONS,
                id=f"instance-{i}-{fam}-seed-{int(s)}",
                files={
                    "data/train.csv": train_csv_text(bundle),
                    "data/scenario.csv": scenario_csv_text(bundle),
                },
                metadata={"truth": build_truth(bundle)},
            )
        )
    return samples


@task
def ccar(
    n_instances: int = 5,
    seed: int | None = None,
    oracle_n: int = 2000,
    n_intime: int = 80,
    message_limit: int = 150,
    baseline: str = "",
    family: str = "",
    repeats: int = 1,
) -> Task:
    """CCAR-style stress-loss projection.

    baseline: "" runs the agent; "naive" (OLS on all nine levels), "vasicek"
    (probit-linear reference that selects its own drivers) or "informed" (the same
    fit handed the true drivers from hidden truth, a diagnostic anchor rather than a
    competitor) run those solvers with mockllm.
    family: "" rotates the response family across instances; pin one of
    "vasicek", "threshold", "interaction" to hold the functional form fixed.
    repeats>1 runs the agent that many times per instance on byte-identical inputs
    and reports the worst case and the spread; see pereval.scorers.stability.
    """
    method = str(baseline).lower()
    if method == "naive":
        solver = naive_baseline()
    elif method == "vasicek":
        solver = vasicek_baseline()
    elif method == "informed":
        solver = informed_baseline()
    else:
        solver = basic_agent(
            init=system_message(INSTRUCTIONS),
            tools=[bash(timeout=240), python(timeout=240)],
            message_limit=message_limit,
        )
    return Task(
        dataset=_samples(n_instances, seed, oracle_n, n_intime, str(family).lower()),
        solver=solver,
        scorer=make_interval_scorer("ccar", ["quarter"], None, truth_to_points),
        sandbox=("docker", COMPOSE),
        epochs=_epochs(repeats),
    )
