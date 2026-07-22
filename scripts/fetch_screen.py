#!/usr/bin/env python3
"""Stage 2: fetch observations for candidate series and apply the numeric screen.

Diversity, not count, is the binding constraint. The metadata stage leaves 28k
candidates but they are heavily concentrated: five title prefixes (HICP, All
Employees, PPI by Industry and Commodity, Consumer Price Indices) account for
more than half. Forty sub-samples drawn from forty PPI commodity codes would not
be forty independent problems. So candidates are capped per title prefix before
anything is fetched.

Output: pereval/tasks/quantile/data/series.npz plus manifest.csv.
"""
import csv
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from screen_fred import screen, trim_nan   # noqa: E402

KEY = os.environ["FRED_API_KEY"]
PER_PREFIX = 5
SEED = 1
SLEEP = 0.55              # FRED allows 120 requests/minute
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "pereval", "tasks", "quantile", "data"))


def prefix(title):
    return re.split(r"[:,(]", title)[0].strip()[:45]


def observations(sid):
    url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
           f"&api_key={KEY}&file_type=json")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                obs = json.load(r)["observations"]
            d = [o["date"] for o in obs]
            v = np.array([np.nan if o["value"] in (".", "") else float(o["value"])
                          for o in obs], dtype=float)
            return d, v
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
            if attempt == 3:
                return None, None
            time.sleep(2 ** attempt)


def main():
    cands = json.load(open(f"{HERE}/out/candidates.json"))
    by_pre = {}
    for c in cands:
        by_pre.setdefault(prefix(c["title"]), []).append(c)
    rng = random.Random(SEED)
    pool = []
    for p, group in sorted(by_pre.items()):
        rng.shuffle(group)
        pool.extend(group[:PER_PREFIX])
    rng.shuffle(pool)
    print(f"{len(cands)} candidates -> {len(pool)} after capping "
          f"{PER_PREFIX}/prefix over {len(by_pre)} prefixes", flush=True)

    os.makedirs(OUT, exist_ok=True)
    kept, rows, reasons = {}, [], {}
    for i, c in enumerate(pool, 1):
        d, v = observations(c["id"])
        time.sleep(SLEEP)
        if d is None:
            reasons["fetch failed"] = reasons.get("fetch failed", 0) + 1
            continue
        ok, why, st = screen(d, v, ppy=12)
        if not ok:
            k = why.split(" (")[0][:34]
            reasons[k] = reasons.get(k, 0) + 1
            continue
        dd, vv = trim_nan(d, v)
        pop = 100.0 * (vv[12:] / vv[:-12] - 1.0)
        kept[c["id"]] = pop.astype(np.float64)
        rows.append(dict(series_id=c["id"], n=st["n"], sd=round(st["sd"], 6),
                         skew=round(st["skew"], 4), exkurt=round(st["exkurt"], 4),
                         tie_rate=st["tie_rate"], units=c["units"],
                         start=dd[12], end=dd[-1], title=c["title"][:110]))
        if i % 200 == 0:
            print(f"  {i}/{len(pool)}  kept {len(kept)}", flush=True)

    np.savez_compressed(f"{OUT}/series.npz", **kept)
    with open(f"{OUT}/manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(f"{OUT}/PROVENANCE.txt", "w") as f:
        f.write(f"FRED monthly NSA, lag-12 simple percent change.\n"
                f"Fetched {time.strftime('%Y-%m-%d')}. FRED revises: this is a "
                f"frozen snapshot and must not be refetched without rerunning "
                f"every published result.\n"
                f"Screen: scripts/screen_fred.py. Enumeration: "
                f"scripts/enumerate_fred.py. Cap {PER_PREFIX}/title prefix, "
                f"seed {SEED}.\n")

    print(f"\nkept {len(kept)} series")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  rejected {v:5d}  {k}")


if __name__ == "__main__":
    main()
