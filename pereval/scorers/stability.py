"""Within-instance stability: repeated agent runs on one fixed instance.

Every other measurement in this suite varies the instance between runs, so its
spread mixes two things: how hard the drawn instance was, and how much the agent's
method wanders. Those have different consequences and only one of them is the
agent's fault.

This reducer measures the second alone. Set `-T repeats=k` on any task and Inspect
runs the agent k times on each sample, on byte-identical inputs, and this reducer
collapses the k scores into one record that keeps the dispersion:

    regret_worst    the worst of the k runs, the suite's pessimistic statistic
    regret_spread   max - min across the k runs, pure method variance
    runs            k, so a table can show what the spread was measured over

Why it is the headline number rather than a diagnostic. SR 26-2 makes validation
frequency a function of, among other things, the "frequency and scope of model
changes" (Model Validation and Monitoring, page 7 of the guidance attached to
https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm). If an agent
hands back a materially different analysis every time it is run on the same data,
then every invocation is a model change, and validation cannot be discharged once
before first use: it recurs at the invocation rate. regret_spread prices that. A
spread near zero means one validation covers every future run of the same
pipeline; a large spread means each run needs its own review, and that is a
governance cost denominated in validator hours rather than an eval curiosity.

The suite's own reproducibility experiment (docs/limitations.md) found this spread
to be large for capable models and near zero only for models that had collapsed to
a fixed deterministic method, which is the worst behaviour the tasks exist to
expose. That inversion is the reason this is worth measuring on every task rather
than once as a side study.
"""

from __future__ import annotations

import numpy as np
from inspect_ai.scorer import Score, ScoreReducer, score_reducer

# The primary regret key differs by scorer; both are checked.
_REGRET_KEYS = ("winkler_regret", "pinball_regret")


def _primary(value: dict) -> str | None:
    return next((k for k in _REGRET_KEYS if k in value), None)


@score_reducer(name="stability")
def stability() -> ScoreReducer:
    """Reduce k same-instance runs to their mean, worst case, and spread."""

    def reduce(scores: list[Score]) -> Score:
        values = [s.value for s in scores if isinstance(s.value, dict)]
        if not values:
            return scores[0]
        key = _primary(values[0])
        keys = {k for v in values for k, x in v.items() if isinstance(x, int | float)}
        out: dict[str, float] = {}
        for k in keys:
            xs = [float(v[k]) for v in values if k in v and np.isfinite(float(v[k]))]
            out[k] = float(np.mean(xs)) if xs else float("nan")
        if key is not None:
            regrets = [float(v[key]) for v in values
                       if key in v and np.isfinite(float(v[key]))]
            if regrets:
                out["regret_worst"] = float(np.max(regrets))
                out["regret_spread"] = float(np.max(regrets) - np.min(regrets))
        out["runs"] = float(len(values))
        n = len(values)
        detail = ", ".join(f"{float(v[key]):.4g}" for v in values) if key else ""
        return Score(
            value=out,
            explanation=(
                f"{n} same-instance runs; mean {out.get(key, float('nan')):.4g}, "
                f"worst {out.get('regret_worst', float('nan')):.4g}, "
                f"spread {out.get('regret_spread', float('nan')):.4g}"
                + (f" [{detail}]" if detail else "")
            ),
            metadata={"per_run": [s.value for s in scores]},
        )

    return reduce


def epochs(repeats: int):
    """Inspect Epochs for `repeats` same-instance runs, or None for a single run."""
    if repeats is None or repeats <= 1:
        return None
    from inspect_ai import Epochs

    return Epochs(int(repeats), [stability()])
