#!/usr/bin/env python3
"""Score every quantile eval log against the baselines on its own instance.

Usage: quantile_table.py <log-dir>

Each model row is compared to reference estimators computed on the *same*
generated blocks, so the comparison is paired even though different runs may
use different instances.
"""
import glob
import os
import sys

import numpy as np
from inspect_ai.log import read_eval_log

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..")))
from pereval.scorers.pinball import (  # noqa: E402
    aggregate, parse_predictions, score_block)
from pereval.tasks.quantile.baselines import predictions_csv  # noqa: E402
from pereval.tasks.quantile.generator import generate  # noqa: E402
from pereval.tasks.quantile.task import _blocks_csv  # noqa: E402

REFS = ["normal", "wei8", "t6", "type8", "hd", "type7"]
HDR = (f'{"row":42s} {"regret":>7s} {"p90":>7s} {"p95":>7s} {"p99":>7s} '
       f'{"hit":>6s} {"MAE":>6s} {"cov":>5s} {"spread":>7s} {"msgs":>5s} {"n":>6s}')


def line(name, a, msgs="", n=""):
    return (f'{name:42s} {a["pinball_regret"]:7.4f} {a["regret_p90"]:7.4f} '
            f'{a["regret_p95"]:7.4f} {a["regret_p99"]:7.4f} {a["hit_rate"]:6.3f} '
            f'{a["mae"]:6.3f} {a["coverage"]:5.3f} {a["spread_ratio"]:7.3f} '
            f'{str(msgs):>5s} {str(n):>6s}')


def main(logdir):
    rows, seeds, failed = [], set(), []
    for f in sorted(glob.glob(os.path.join(logdir, "*.eval"))):
        log = read_eval_log(f)
        model = log.eval.model
        if log.status != "success" or not log.samples:
            failed.append((model, str(getattr(log.error, "message", "")).strip()[-90:]))
            continue
        for s in log.samples:
            sc = (s.scores or {}).get("quantile")
            if not sc:
                failed.append((model, "no score"))
                continue
            a = dict(sc.metadata)
            rows.append((model, a, len(s.messages),
                         f'{a["n_blocks"] - a["n_missing"]}/{a["n_blocks"]}'))
            seeds.add(s.metadata["seed"])

    print(HDR)
    for seed in sorted(seeds):
        blocks = generate(seed)
        txt = _blocks_csv(blocks)
        for nm in REFS:
            p = parse_predictions(predictions_csv(nm, txt))
            a = aggregate([score_block(dict(pop=b["pop"], norm=b["norm"], x=b["x"]),
                                       p.get(b["block"])) for b in blocks])
            rows.append((f"[{nm}]", a, "", f'{len(blocks)}/{len(blocks)}'))

    for name, a, msgs, n in sorted(rows, key=lambda r: r[1]["pinball_regret"]):
        print(line(name, a, msgs, n))
    if failed:
        print("\nfailed runs:")
        for m, e in failed:
            print(f"  {m:44s} {e}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "logs")
