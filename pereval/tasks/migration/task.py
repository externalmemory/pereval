"""Inspect task wrapper for the rating-migration task.

Same isolation model as the rest of the suite: instances are generated
host-side, only neutral CSVs enter the sandbox, the response law travels in
sample metadata and never into the prompt.

Run (requires Docker and a model):
    inspect eval pereval/tasks/migration/task.py --model <provider/model>
    inspect eval pereval/tasks/migration/task.py -T baseline=onefactor --model mockllm/model
    inspect eval pereval/tasks/migration/task.py -T baseline=no_migration --model mockllm/model
    inspect eval pereval/tasks/migration/task.py -T n_instances=9 -T seed=1
"""

from __future__ import annotations

import numpy as np
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.solver import basic_agent, system_message
from inspect_ai.tool import bash, python

from pereval.scorers.migration import migration_scorer
from pereval.scorers.stability import epochs as _epochs
from pereval.tasks.ballistic.task import COMPOSE
from pereval.tasks.migration.baselines import reference_solver
from pereval.tasks.migration.generator import CHECKPOINTS, generate, public_files

SCENARIOS = ("baseline", "adverse", "severe")

INSTRUCTIONS = """\
You are projecting how a loan portfolio's credit ratings will migrate under a
supplied economic scenario. In the `data/` directory:

- `data/transitions.csv`: observed rating transitions for this portfolio, as
  ANNUAL counts. One row per year and starting rating, with columns `year`,
  `from_rating`, and `to_AAA` through `to_CCC_C` plus `to_D`. A row counts the
  obligors that held `from_rating` at the start of that year and held each state
  at the end of it. An obligor that defaulted during the year is counted in
  `to_D`. Counts are a finite portfolio, so they carry sampling noise.
- `data/macro_history.csv`: QUARTERLY macroeconomic series over the same period,
  nine of them. Some are blank for early quarters because they began later.
- `data/scenario.csv`: the same nine series for nine future quarters, the
  scenario you must project under. Treat it as given, not as something to
  forecast.
- `data/portfolio.csv`: the cohort to project, as obligor counts by rating. Its
  rating mix is NOT the same as the historical portfolio's.
- `data/policy.json`: the checkpoint quarters.

Project this cohort forward over the nine scenario quarters and report where its
obligors stand at quarter 4 and at quarter 9.

What to report, precisely. For each checkpoint, give the distribution of the
ORIGINAL cohort across the seven rating grades plus `D` for default. Default is
absorbing and terminal: once an obligor defaults it stays in `D` and is counted
there at every later checkpoint. Do not replace defaulted obligors, do not model
new lending, and do not renormalise the surviving grades to one on their own.
The eight shares at each checkpoint describe where the original obligors ended
up, so they must sum to 1.

Write `predictions.csv` in the working directory with columns exactly:

    quarter,state,share

one row per checkpoint and state, so sixteen rows in total. `quarter` is 4 or 9,
`state` is one of AAA, AA, A, BBB, BB, B, CCC/C, D, and `share` is a fraction of
the original cohort between 0 and 1.

Scoring has four equally weighted components, two per checkpoint:

- the Kolmogorov-Smirnov distance between your distribution over the seven
  RATING grades and the true one, that is the largest absolute gap between the
  two cumulative distributions, after renormalising the seven grades to sum to
  one;
- the absolute error in the cumulative default share.

Default is scored on its own rather than as part of the distance, because a
sup-norm distance is usually attained in the middle of the distribution and
would let a default error hide behind a larger error in a populous grade.

Each component is divided by what the uninformative answer scores on it, where
the uninformative answer is submitting the starting cohort unchanged: no
migration and no defaults. The four ratios are averaged. So 0 is perfect, 1.0
means no better overall than assuming nothing happens, and below 1.0 means
better. Getting the shape right while understating defaults, or the reverse,
caps your score at about 0.5.

Also write `matrices.csv` in the working directory, recording the quarterly
transition matrices your model used for the nine scenario quarters, with columns
exactly:

    quarter,from_rating,to_AAA,to_AA,to_A,to_BBB,to_BB,to_B,to_CCC_C,to_D

one row per scenario quarter and starting rating, so sixty-three rows, using the
same column naming as data/transitions.csv. This records the model alongside its
output, as documentation of how the projection was produced.

Also write `backtest.csv` in the working directory, giving the annual default
rate your model projects for each HISTORICAL year, with columns exactly:

    year,default_rate

one row per year in data/transitions.csv. For each year, use the portfolio that
year actually started with, taken from the row sums of that year's counts, and
report the fraction of it your model says defaults during that year. This is the
model's fit to the period it was estimated on, alongside its projection.

Note that the transitions you observe are annual while the projection is
quarterly, and the economy moves within each year as well as between years.

You have Python with numpy, pandas, scikit-learn, statsmodels and scipy. You do
not have internet access. Each code execution runs in a FRESH interpreter, so
write a single self-contained script and run it rather than relying on state
carrying over. Produce a complete predictions.csv early, even from a rough
model, and refine it after. Verify predictions.csv has sixteen rows before
submitting.
"""

SAMPLE_INPUT = ("Project the cohort in data/portfolio.csv over the scenario and write "
                "predictions.csv, as specified in the system instructions.")


def _samples(n_instances, seed, n_years, scenario):
    base = seed if seed is not None else int(np.random.SeedSequence().generate_state(1)[0])
    seeds = np.random.SeedSequence(base).generate_state(n_instances, dtype=np.uint32)
    samples = []
    for i, s in enumerate(seeds):
        scen = SCENARIOS[i % len(SCENARIOS)] if scenario == "rotate" else scenario
        bundle = generate(int(s), n_years=n_years, scenario=scen)
        samples.append(
            Sample(
                input=SAMPLE_INPUT,
                id=f"instance-{i}-{scen}-seed-{int(s)}",
                files=public_files(bundle),
                metadata={"truth": bundle["truth"]},
            )
        )
    return samples


@task
def migration(
    n_instances: int = 3,
    seed: int | None = None,
    n_years: int = 20,
    scenario: str = "rotate",
    baseline: str = "",
    repeats: int = 1,
    message_limit: int = 500,
) -> Task:
    """Rating migration under a supplied scenario, scored on four equal components.

    baseline: "" runs the agent; "onefactor" is the competent reference and
    "no_migration" submits the starting mix, which is the degenerate answer.
    scenario: "rotate" cycles baseline, adverse and severe across instances, or
    pin one of those three.
    n_years: twenty by default, which is the history a bank plausibly has for a
    portfolio under its current rating scale. Working out that twenty annual
    observations will not support an unshrunk macro regression is part of the
    task, so nothing in the prompt says so.
    repeats>1 measures same-instance stability; see pereval.scorers.stability.
    """
    if n_instances < 1 or repeats < 1:
        raise ValueError("n_instances and repeats must be positive")
    if baseline not in ("", "onefactor", "no_migration"):
        raise ValueError("baseline must be empty, 'onefactor' or 'no_migration'")
    if scenario not in ("rotate", *SCENARIOS):
        raise ValueError(f"scenario must be 'rotate' or one of {SCENARIOS}")
    solver = (
        reference_solver(baseline)
        if baseline
        else basic_agent(
            init=system_message(INSTRUCTIONS),
            tools=[bash(timeout=240), python(timeout=240)],
            message_limit=message_limit,
        )
    )
    return Task(
        dataset=_samples(n_instances, seed, n_years, scenario),
        solver=solver,
        scorer=migration_scorer(),
        sandbox=("docker", COMPOSE),
        epochs=_epochs(repeats),
    )


__all__ = ["CHECKPOINTS", "INSTRUCTIONS", "SCENARIOS", "migration"]
