#!/usr/bin/env python3
"""Reconstruct integer transition counts from published one-year percentages.

The audit trail for pereval/tasks/migration/data/sp2024_regional_counts.csv.
Reads the published percentages committed beside it and re-derives the counts,
so the CSV can be checked against the source document rather than trusted.

A single-year static pool means every entry of a row is k_j / N for one cohort
size N. Searching N upward and requiring that all nine entries match to two
decimal places and that the counts sum to N recovers the integers.

N is identified only up to a positive integer multiple, since k/N equals 2k/2N.
The smallest N is reported. For the Global panel that ambiguity is closed by an
external figure: see docs/tasks/migration.md.

Usage: python -m scripts.migration_invert_counts
"""

from __future__ import annotations

import sys

from pereval.tasks.migration.reference import (
    COHORT_ROWS,
    REGIONS,
    STATES,
    regional_counts,
    regional_published_pct,
)

TOL = 0.005 + 1e-9


def invert(pct: list[float], nmax: int = 20000) -> tuple[int, list[int]] | None:
    """Smallest cohort size whose integer counts reproduce pct to 2dp."""
    for n in range(1, nmax + 1):
        counts = []
        for p in pct:
            k = round(p * n / 100.0)
            if abs(k * 100.0 / n - p) > TOL:
                break
            counts.append(k)
        else:
            if sum(counts) == n:
                return n, counts
    return None


def main() -> int:
    published, committed = regional_published_pct(), regional_counts()
    width = max(len(s) for s in STATES)
    bad = 0
    for region in REGIONS:
        print(f"\n### {region}")
        print(f"{'from':6s} {'N':>6s}  " + " ".join(f"{s:>{width}s}" for s in STATES))
        for rating in COHORT_ROWS:
            got = invert(published[region][rating])
            if got is None:
                print(f"{rating:6s} {'--':>6s}  no consistent cohort size")
                bad += 1
                continue
            n, counts = got
            print(f"{rating:6s} {n:6d}  " + " ".join(f"{k:>{width}d}" for k in counts))
            rec = committed[region][rating]
            if (n, counts) != (rec["cohort_size"], rec["counts"]):
                print(f"       MISMATCH against committed CSV: {rec}")
                bad += 1
    d = STATES.index("D")
    total = sum(r["counts"][d] for r in committed["Global"].values())
    print(f"\nGlobal defaults from the rated cohort: {total} "
          f"(source states 130 of 145 2024 defaulters were rated at the start of the year)")
    if total != 130:
        bad += 1
    print("OK" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
