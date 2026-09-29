"""Published rating-migration reference data, loaded from CSV.

This module carries measured inputs only. It is calibration material for a task
that does not exist yet: there is no generator, scorer or Inspect task in this
package, deliberately. See docs/tasks/migration.md for provenance and for why
the counts are reconstructed rather than published directly.

Nothing here enters an agent sandbox. These are host-side reference numbers.
"""

from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).parent / "data"

#: Column order used by every matrix here. NR is "not rated", i.e. withdrawn.
STATES = ("AAA", "AA", "A", "BBB", "BB", "B", "CCC/C", "D", "NR")

#: Rows available in the 2024 regional cohorts. AAA is absent: its published row
#: is 100% on the diagonal, which carries no information about the cohort size,
#: so the count cannot be recovered. See docs/tasks/migration.md.
COHORT_ROWS = ("AA", "A", "BBB", "BB", "B", "CCC/C")

REGIONS = ("Global", "U.S.", "Europe", "EM")

_COUNT_COLS = ("to_AAA", "to_AA", "to_A", "to_BBB", "to_BB", "to_B",
               "to_CCC_C", "to_D", "to_NR")
_PCT_COLS = ("AAA", "AA", "A", "BBB", "BB", "B", "CCC_C", "D", "NR")


def _rows(name: str) -> list[dict]:
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def regional_counts() -> dict[str, dict[str, dict]]:
    """{region: {from_rating: {"cohort_size": int, "counts": [int x 9]}}}.

    Integer transition counts for the 2024 one-year static pool, reconstructed
    from the published percentages. Counts are exact integers, not estimates,
    but the cohort size is identified only up to the smallest consistent value;
    see docs/tasks/migration.md.
    """
    out: dict[str, dict[str, dict]] = {r: {} for r in REGIONS}
    for row in _rows("sp2024_regional_counts.csv"):
        out[row["region"]][row["from_rating"]] = {
            "cohort_size": int(row["cohort_size"]),
            "counts": [int(row[c]) for c in _COUNT_COLS],
        }
    return out


def regional_published_pct() -> dict[str, dict[str, list[float]]]:
    """The percentages exactly as printed in the source, for round-trip checks."""
    out: dict[str, dict[str, list[float]]] = {r: {} for r in REGIONS}
    for row in _rows("sp2024_regional_published_pct.csv"):
        out[row["region"]][row["from_rating"]] = [float(row[c]) for c in _PCT_COLS]
    return out


def global_average(horizon: str = "1y", stat: str = "mean") -> dict[str, list[float]]:
    """Long-run global average transition percentages, 1981-2024.

    horizon is "1y" or "3y"; stat is "mean" or "sd". These are averages over 44
    annual static pools, so they do NOT invert to integer counts: there is no
    single cohort size behind them. They are for calibrating a generator's
    plausible range, not for reconstructing a cohort.
    """
    if horizon not in ("1y", "3y"):
        raise ValueError("horizon must be '1y' or '3y'")
    if stat not in ("mean", "sd"):
        raise ValueError("stat must be 'mean' or 'sd'")
    return {
        row["from_rating"]: [float(row[c]) for c in _PCT_COLS]
        for row in _rows("sp_global_average_1981_2024.csv")
        if row["horizon"] == horizon and row["stat"] == stat
    }
