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

Why it is a headline number rather than a diagnostic: it decides how far evidence
about the process carries to the artifact. A spread near zero means the model in
front of a validator is close to what the pipeline reliably produces, so evidence
about the pipeline is evidence about it. A large spread means it is a draw, and has
to be judged on its own terms.

The problem is reproducibility, not change control. Rerunning a development tool is
not a model change: a model change is a change to what runs in production, and
exercising a model during development or validation is not one. What instability
costs is developmental evidence, which SR 26-2 puts at the centre of conceptual
soundness when it asks for "the quality and extent of developmental evidence"
(Conceptual Soundness, page 8 of the guidance attached to
https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm). A specification
that cannot be re-derived cannot be replicated by an independent team either.

The suite's own reproducibility experiment (docs/limitations.md) found this spread
to be large for capable models and near zero only for models that had collapsed to
a fixed deterministic method, which is the worst behaviour the tasks exist to
expose. That inversion is the reason this is worth measuring on every task rather
than once as a side study.
"""

from __future__ import annotations

import numpy as np
from inspect_ai.scorer import Score, ScoreReducer, score_reducer

# The primary regret key differs by scorer, so this lists every task family, in
# priority order. CECL emits `winkler_regret` as a secondary diagnostic alongside
# `ecl_regret`, so `ecl_regret` has to come first or CECL would be reduced on the
# wrong metric. `score` comes last for the same reason: migration's primary is
# `score`, but a scorer that emits both a named regret and a `score` should be
# reduced on the named one.
#
# Migration was missing from this tuple for its first three weeks, and nothing
# caught it, because every scorer also emits a per-run `regret_worst` and
# `regret_spread`. With no primary key recognised, the generic averaging loop
# below filled those two fields with the MEAN of the per-run values: `regret_worst`
# became the mean of the k runs rather than their maximum, and `regret_spread`
# became the mean of k zeros, which is zero. So three runs that scored 0.487,
# 0.2367 and 0.6343 were reported as a worst case of 0.4527 with a spread of
# exactly zero, which is a claim of perfect reproducibility manufactured from
# wandering runs. That is the one failure mode this reducer exists to detect, and
# it is also the pessimistic direction inverted. The real run it happened on is
# recorded in docs/limitations.md.
_REGRET_KEYS = ("ecl_regret", "winkler_regret", "pinball_regret", "score")


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
        if key is None:
            # Fail closed rather than emit a stable-looking record. Averaging the
            # per-run `regret_worst` and `regret_spread` is worse than no number:
            # it reports a worst case that is really a mean and a spread of zero,
            # and a reader cannot tell it apart from a genuinely reproducible run.
            # A new task family has to be added to _REGRET_KEYS deliberately.
            raise ValueError(
                "stability() cannot identify a primary regret metric. Add this "
                "scorer's primary key to pereval.scorers.stability._REGRET_KEYS. "
                f"Recognised: {_REGRET_KEYS}. Emitted: {tuple(sorted(values[0]))}."
            )
        keys = {k for v in values for k, x in v.items() if isinstance(x, int | float)}
        out: dict[str, float] = {}
        for k in keys:
            xs = [float(v[k]) for v in values if k in v and np.isfinite(float(v[k]))]
            out[k] = float(np.mean(xs)) if xs else float("nan")
        regrets = [float(v[key]) for v in values
                   if key in v and np.isfinite(float(v[key]))]
        if regrets:
            out["regret_worst"] = float(np.max(regrets))
            out["regret_spread"] = float(np.max(regrets) - np.min(regrets))
        else:
            # The primary metric is recognised but unreadable in every run. The
            # averaged per-run values left in `out` by the loop above are the mean
            # masquerading as the worst case, so overwrite them rather than ship
            # them: nan says no measurement, which is the honest answer.
            out["regret_worst"] = float("nan")
            out["regret_spread"] = float("nan")
        out["runs"] = float(len(values))
        n = len(values)
        detail = ", ".join(f"{float(v[key]):.4g}" if key in v else "-"
                           for v in values)
        return Score(
            value=out,
            explanation=(
                f"{n} same-instance runs on {key}; "
                f"mean {out.get(key, float('nan')):.4g}, "
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
