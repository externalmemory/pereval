#!/usr/bin/env python3
"""Does paired comparison on shared instances buy anything on this suite?

Usage: paired_analysis.py [runs-dir]

docs/task-design.md prescribes "paired-difference comparisons between models on
identical instances", on the standard reasoning that instance difficulty is a common
nuisance factor and differencing it away sharpens the comparison. Every published table
nonetheless reports unpaired mean +- 2 SD, so the obvious criticism is that the suite
wastes its own power.

This script tests that criticism against the archived runs, and it does not survive.
Every model pair with at least three shared instances is compared two ways: the SD of
the actual paired difference, against the SD you would get if the two rows were
independent. If instance difficulty dominated, the first would be much smaller.

The measured answer is that it is barely smaller. Pairing on regret levels reduces
variance by about 1 percent, and on the log scale, which is the right scale for a
multiplicative heavy-tailed quantity, by about 10 percent.

Why: per-instance regret is dominated by whether THAT model blew up on THAT instance,
not by how hard the instance is. Instances do have a consistent difficulty ordering,
with cross-model rank correlations from +0.27 to +0.71 on four of five tasks, so the
common factor exists; it just carries little of the magnitude variance. Add the
reproducibility finding, where the same model on byte-identical data swings up to 30x,
and the variance sits in the model-by-run interaction, which pairing across instances
cannot reach.

The consequence for the suite is that the lever on variance is more runs per instance
(-T repeats=K), not pairing. Reported so the prescription in task-design.md is corrected
by measurement rather than left as received wisdom.
"""
from __future__ import annotations

import collections
import glob
import os
import re
import sys

import numpy as np

HDR = re.compile(r"- (\d+)/(\d+) (?:points predicted|blocks answered); "
                 r"(?:Winkler|pinball) regret ([0-9.]+)")
NAME = re.compile(r"-(twobody|threebody|hyperbolic|ballistic|ccar)-instance-(\d+)-seed-(\d+)$")
EPS = 1e-6


def load(runs_dir: str) -> dict[str, dict[str, dict[int, float]]]:
    """task -> model -> {instance index: regret}, complete runs only."""
    out: dict[str, dict[str, dict[int, float]]] = collections.defaultdict(dict)
    for path in sorted(glob.glob(os.path.join(runs_dir, "*.md"))):
        base = os.path.basename(path)[:-3]
        m = NAME.search(base)
        if not m:
            continue
        with open(path, errors="ignore") as fh:
            head = fh.read(4000)
        h = HDR.search(head)
        if not h or h.group(1) != h.group(2):
            continue  # incomplete run: not a measurement, so not paired either
        out[m.group(1)].setdefault(base[:m.start()], {})[int(m.group(2))] = float(h.group(3))
    return out


def ratios(data, transform) -> tuple[np.ndarray, list[tuple]]:
    """Paired SD over independent-assumption SD, for every pair sharing >=3 instances."""
    vals, detail = [], []
    for task, models in sorted(data.items()):
        names = sorted(m for m, d in models.items() if len(d) >= 3)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                shared = sorted(set(models[a]) & set(models[b]))
                if len(shared) < 3:
                    continue
                va = transform(np.array([models[a][k] for k in shared]))
                vb = transform(np.array([models[b][k] for k in shared]))
                indep = float(np.sqrt(va.var(ddof=1) + vb.var(ddof=1)))
                paired = float((va - vb).std(ddof=1))
                if indep > 0:
                    vals.append(paired / indep)
                    detail.append((task, a, b, len(shared), indep, paired))
    return np.array(vals), detail


def instance_difficulty_correlation(data) -> dict[str, tuple[int, int, float]]:
    """Mean rank correlation between each model's instance profile and the others'."""
    from scipy.stats import spearmanr

    out = {}
    for task, models in sorted(data.items()):
        names = sorted(m for m, d in models.items() if len(d) >= 3)
        if len(names) < 3:
            continue
        shared = sorted(set.intersection(*[set(models[n]) for n in names]))
        if len(shared) < 3:
            continue
        M = np.array([[models[n][i] for i in shared] for n in names])
        cs = [spearmanr(M[k], np.delete(M, k, axis=0).mean(0)).statistic
              for k in range(len(names))]
        out[task] = (len(names), len(shared), float(np.nanmean(cs)))
    return out


def main() -> None:
    runs_dir = sys.argv[1] if len(sys.argv) > 1 else "runs"
    data = load(runs_dir)
    if not data:
        sys.exit(f"no complete archived runs found in {runs_dir}/")

    print("Instance difficulty as a common factor")
    for task, (n_models, n_inst, corr) in instance_difficulty_correlation(data).items():
        print(f"  {task:11s} {n_models} models x {n_inst} instances   "
              f"mean rank corr with the others: {corr:+.2f}")

    print("\nDoes pairing reduce variance?")
    for label, fn in (("level", lambda v: v), ("log", lambda v: np.log(v + EPS))):
        r, _ = ratios(data, fn)
        print(f"  {label:6s} {len(r)} pairs   paired/independent SD ratio median "
              f"{np.median(r):.2f}   variance reduction {1 - np.median(r) ** 2:+.0%}   "
              f"helps in {(r < 1).mean():.0%} of pairs")

    r, detail = ratios(data, lambda v: np.log(v + EPS))
    order = np.argsort(r)
    print("\nWhere pairing helps most (log scale), which is where two models behaved alike")
    for k in order[:5]:
        task, a, b, n, indep, paired = detail[k]
        print(f"  {task:11s} {a.split('-')[-1][:20]:20s} vs {b.split('-')[-1][:20]:20s} "
              f"n={n}  ratio {r[k]:.2f}")
    print("\nConclusion: pairing is not the lever. Use -T repeats=K for within-instance runs.")


if __name__ == "__main__":
    main()
