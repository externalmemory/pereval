"""Inspect task wrapper for the small-sample quantile task.

Same isolation model as the rest of the suite: instances are generated
host-side, only the drawn numbers enter the sandbox, and ground truth travels in
sample metadata. Unlike the other tasks there is no generated DGP, so there is
no Monte-Carlo oracle; the population supplies its own floor through the pinball
loss, whose minimiser is exactly the population quantile.

The sandbox matters more here than the prompt length suggests. A pilot run
without one had a frontier model spend 63,997 of 64,000 output tokens doing
probability-plot regression arithmetic longhand and never reach an answer. The
method was sound; it had no calculator. Give the agent numpy and that failure
disappears.

Run (requires Docker and a model):
    inspect eval pereval/tasks/quantile/task.py --model openai-api/zen/<id>
    inspect eval pereval/tasks/quantile/task.py -T baseline=type7 --model mockllm/model
    inspect eval pereval/tasks/quantile/task.py -T baseline=wei8 --model mockllm/model

Validate plumbing with the baseline solvers under mockllm before spending any
model budget: they exercise generation, sandbox file delivery, the
predictions.csv round trip and scoring, at zero cost.
"""

from __future__ import annotations

import numpy as np
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, mean, scorer, stderr
from inspect_ai.solver import basic_agent, system_message
from inspect_ai.tool import bash, python
from inspect_ai.util import sandbox

from pereval.scorers.pinball import (
    aggregate,
    parse_predictions,
    score_block,
    score_value_and_explanation,
)
from pereval.tasks.ballistic.task import COMPOSE  # shared general modeling sandbox
from pereval.tasks.quantile.generator import N_BLOCKS, generate, prompt_text

INSTRUCTIONS = """\
You are estimating tail quantiles of a population from a very small sample.

`data/task.txt` states the problem in full: it gives the population size m for
each block and defines exactly what is being asked. Read it first.
`data/blocks.csv` has the same numbers in tabular form, with columns `block`
and `x`, ten rows per block.

You have Python with numpy, scipy, pandas, statsmodels and scikit-learn, and no
internet access. Use it: the arithmetic is not worth doing by hand. Each code
execution runs in a FRESH interpreter, so write a single self-contained script
(save it to a file and run it) rather than relying on state carrying over
between executions. Do not print the whole data file; read it programmatically.

Write your answers to `predictions.csv` in the working directory with columns
exactly:

    block,q90,q95,q99,lo,hi

one row per block, no other columns, no commentary. `q90`, `q95` and `q99` are
point estimates of the population percentiles; `lo` and `hi` are a 95% interval
for the population 95th percentile.

Produce a complete predictions.csv early, even from a rough method, and keep a
valid one on disk; refine it after. Verify it has one row per block before
submitting.
"""


def _blocks_csv(blocks: list[dict]) -> str:
    rows = ["block,x"]
    for b in blocks:
        rows += [f"{b['block']},{v:g}" for v in b["shown"]]
    return "\n".join(rows) + "\n"


def _samples(n_instances: int, seed: int | None, n_blocks: int):
    """Instances from child seeds of one base seed, as in the other tasks."""
    base = seed if seed is not None else int(
        np.random.SeedSequence().generate_state(1)[0])
    seeds = np.random.SeedSequence(base).generate_state(n_instances, dtype=np.uint32)
    for i, s in enumerate(seeds):
        blocks = generate(int(s), n_blocks=n_blocks)
        truth = [
            dict(block=b["block"], series=b["series"], m=b["m"], start=b["start"],
                 scale=b["scale"], norm=b["norm"], sd=b["sd"], x=b["x"].tolist(),
                 pop=b["pop"].tolist())
            for b in blocks
        ]
        yield Sample(
            input=f"Estimate the population tail quantiles for all {len(blocks)} "
                  f"blocks described in data/task.txt.",
            target="see metadata",
            id=f"quantile-{i}",
            metadata={"truth": truth, "instance": i, "seed": int(s)},
            files={
                "data/blocks.csv": _blocks_csv(blocks),
                "data/task.txt": prompt_text(blocks),
            },
        )


@scorer(
    name="quantile",
    metrics={
        "pinball_regret": [mean(), stderr()],
        "hit_rate": [mean(), stderr()],
        "mae": [mean(), stderr()],
        "coverage": [mean()],
        "winkler": [mean()],
        "spread_ratio": [mean()],
    },
)
def quantile_scorer():
    async def score(state, target):
        truth = state.metadata["truth"]
        try:
            text = await sandbox().read_file("predictions.csv")
        except FileNotFoundError:
            text = None
        preds = parse_predictions(text)
        records = [
            score_block(
                dict(pop=np.asarray(t["pop"], float), norm=t["norm"],
                     x=np.asarray(t["x"], float)),
                preds.get(t["block"]),
            )
            for t in truth
        ]
        agg = aggregate(records)
        agg["true_spread"] = [
            float((np.quantile(np.asarray(t["pop"], float), 0.99)
                   - np.quantile(np.asarray(t["pop"], float), 0.95))
                  / max(t["x"][-1] - t["x"][-2], 1e-12)) for t in truth]
        value, explanation = score_value_and_explanation(agg)
        return Score(value=value, metadata=agg, explanation=explanation)

    return score


@task
def quantile(n_instances: int = 8, seed: int | None = 1,
             n_blocks: int = N_BLOCKS, message_limit: int = 300,
             baseline: str = ""):
    """Small-sample population tail quantile estimation from FRED YoY data.

    baseline: "" runs the agent; a named estimator ("type7", "type8", "hd",
    "wei8", "t6", "normal") runs that reference solver under mockllm to produce
    the README baseline rows and to validate plumbing without model spend.
    """
    method = str(baseline).lower()
    if method:
        from pereval.tasks.quantile.baselines import baseline_solver
        solver = baseline_solver(method)
    else:
        solver = basic_agent(
            init=system_message(INSTRUCTIONS),
            tools=[bash(timeout=300), python(timeout=300)],
            message_limit=message_limit,
        )
    return Task(
        dataset=list(_samples(n_instances, seed, n_blocks)),
        solver=solver,
        scorer=quantile_scorer(),
        sandbox=("docker", COMPOSE),
    )
