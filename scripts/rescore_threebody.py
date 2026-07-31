#!/usr/bin/env python3
"""Re-score archived three-body predictions with the corrected circular scorer.

Usage: rescore_threebody.py [runs-dir]

The three-body column was produced by a scorer that localized the two endpoints of a
submitted interval to the branch nearest the truth independently, which rewrote intervals
wider than half the circle. The fix is in pereval.scorers.interval.localize_interval.
Re-running the models would cost budget and would not reproduce those runs anyway, so the
question is whether the archived predictions can simply be scored again.

They can, but only for runs whose predictions.csv can be IDENTIFIED. A transcript often
contains several candidate blocks, because the agent wrote the file more than once, and
nothing in it says which version was on disk when the scorer read it. Guessing "the last
complete block" reproduced only 11 of 15 unaffected runs.

The limit is that a transcript records the conversation, not the sandbox filesystem. An
agent that writes predictions.csv from a script without echoing it leaves no copy to
score, and no amount of care recovers one.

The archived score settles it. Each candidate is scored with the OLD scorer, reimplemented
here; the candidate that reproduces the regret recorded in the transcript header is the
file that was scored. Where the matching candidates all re-score to the same value the identification is
checked rather than assumed. Where none matches, or the matches disagree, the run is
reported unrecoverable and no number is published.
"""
from __future__ import annotations

import glob
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from pereval.scorers.interval import (  # noqa: E402
    ALPHA,
    MISSING_PENALTY_FLOOR,
    _localize,
    interval_score,
    parse_predictions,
    score_points,
)
from pereval.tasks.orbit.generator import (  # noqa: E402
    build_truth,
    generate_threebody,
    truth_to_points,
)

HDR = re.compile(r"- (\d+)/(\d+) points predicted; Winkler regret ([0-9.]+)")
NAME = re.compile(r"-threebody-instance-(\d+)-seed-(\d+)$")
BLOCK = re.compile(r"t,y_pred,y_lower,y_upper\n((?:\s*[-\d.,eE+]+\s*\n)+)")


def old_score(points, preds, period=360.0) -> float:
    """The superseded scorer: endpoints localized separately, then swapped if inverted."""
    agent, oracle = [], []
    for p in points:
        tm = float(p["true_mean"])
        mc = _localize(p["mc"], tm, period)
        lo_o, hi_o = float(np.quantile(mc, 0.025)), float(np.quantile(mc, 0.975))
        ws_o = float(interval_score(lo_o, hi_o, mc, ALPHA).mean())
        oracle.append(ws_o)
        pred = preds.get(p["key"])
        if pred is None or not all(np.isfinite(v) for v in pred):
            agent.append(MISSING_PENALTY_FLOOR * ws_o)  # the old missing-point price
            continue
        _, lo, hi = pred
        lo = float(_localize([lo], tm, period)[0])
        hi = float(_localize([hi], tm, period)[0])
        if lo > hi:
            lo, hi = hi, lo
        agent.append(float(interval_score(lo, hi, mc, ALPHA).mean()))
    return float(np.mean(agent) - np.mean(oracle))


def candidates(text: str):
    return ["t,y_pred,y_lower,y_upper\n" + m.group(1) for m in BLOCK.finditer(text)]


def main() -> None:
    runs = sys.argv[1] if len(sys.argv) > 1 else "runs"
    cache: dict[int, list] = {}
    rows, unrecoverable = [], []

    for path in sorted(glob.glob(os.path.join(runs, "*-threebody-instance-*.md"))):
        base = os.path.basename(path)[:-3]
        m = NAME.search(base)
        if not m:
            continue
        seed = int(m.group(2))
        text = open(path, errors="ignore").read()
        h = HDR.search(text)
        if not h:
            continue
        recorded = float(h.group(3))
        model = base[: m.start()]

        if seed not in cache:
            cache[seed] = truth_to_points(build_truth(generate_threebody(seed=seed)))
        points = cache[seed]

        hits = []
        for c in candidates(text):
            preds = parse_predictions(c, ["t"])
            if not preds:
                continue
            if abs(old_score(points, preds) - recorded) <= 0.002 * max(1.0, recorded):
                hits.append(preds)
        # a run with no predictions at all is identified by its own penalty
        if not hits and int(h.group(1)) == 0:
            hits = [{}]

        # Several candidates can match because the agent wrote the same file more than
        # once. That is only ambiguous if they disagree after re-scoring.
        news = [score_points(points, cand, 360.0)["winkler_regret"] for cand in hits]
        if not news or (max(news) - min(news)) > 1e-6 * max(1.0, max(news)):
            unrecoverable.append((model, seed, recorded, len(hits)))
            continue
        rows.append((model, seed, recorded, news[0]))

    print(f"{'model':44s} {'seed':>10s} {'archived':>10s} {'rescored':>10s} {'change':>9s}")
    for model, seed, old, new in rows:
        ratio = new / old if old else float("inf")
        print(f"{model[:44]:44s} {seed:>10d} {old:10.3f} {new:10.3f} {ratio:8.2f}x")
    print(f"\nidentified and re-scored: {len(rows)}")
    if unrecoverable:
        print(f"unrecoverable ({len(unrecoverable)}): predictions.csv could not be pinned down")
        for model, seed, old, n in unrecoverable:
            print(f"   {model[:44]:44s} seed {seed} archived {old:.3f}  candidates matching: {n}")


if __name__ == "__main__":
    main()
