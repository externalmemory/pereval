"""Published rating-migration reference data, loaded from CSV.

This module carries measured inputs only. It is calibration material for a task
that does not exist yet: there is no generator, scorer or Inspect task in this
package, deliberately. See docs/tasks/migration.md for provenance and for why
the 2024 counts are reconstructed rather than published directly.

Nothing here enters an agent sandbox. These are host-side reference numbers.
"""

from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).parent / "data"

#: Column order used by every matrix here. NR is "not rated", i.e. withdrawn.
STATES = ("AAA", "AA", "A", "BBB", "BB", "B", "CCC/C", "D", "NR")

#: The rating grades an obligor can occupy, AAA included. Use this for a state
#: space. AAA carries real default risk even though no AAA issuer has defaulted
#: within one year in the published history; see PD_FLOORS and
#: docs/tasks/migration.md.
RATINGS = ("AAA", "AA", "A", "BBB", "BB", "B", "CCC/C")

#: Rows of the 2024 regional cohorts for which integer counts are recoverable.
#: AAA is excluded because its published 2024 row is 100% on the diagonal, which
#: fixes no cohort size. That is a gap in the counts, NOT a statement that AAA
#: is riskless: the AAA row is present at every horizon in global_average().
COUNT_ROWS = ("AA", "A", "BBB", "BB", "B", "CCC/C")

REGIONS = ("Global", "U.S.", "Europe", "EM")

HORIZONS = ("1y", "3y", "5y")

#: Regulatory floors on assigned PD, as fractions (not percent).
#:
#: "us": 12 CFR 217.131(d)(2) (Board of Governors, Regulation Q, advanced
#: approaches), "Floor on PD assignment": the PD for each wholesale obligor or
#: retail segment may not be less than 0.03 percent. Exempt are exposures to, or
#: directly and unconditionally guaranteed by, a sovereign entity, the BIS, the
#: IMF, the European Commission, the ECB, the ESM, the EFSF, or a multilateral
#: development bank. This is the operative floor for a US institution.
#:
#: "basel": CRE32.4 of the consolidated Basel Framework, in force 1 January
#: 2023, sets 0.05 percent for every asset class except sovereign. The US has
#: not adopted that figure here; it is recorded for contrast only.
#:
#: The floors are why a model must not report zero PD for a top grade. A zero PD
#: implies zero expected loss and therefore zero allowance on a live exposure,
#: which is a modelling defect independent of any regulatory requirement.
PD_FLOORS = {"us": 0.0003, "basel": 0.0005}

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
    see docs/tasks/migration.md. Covers COUNT_ROWS, so no AAA row.
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
    """Long-run global average transition percentages, 1981-2024, AAA included.

    horizon is "1y", "3y" or "5y"; stat is "mean" or "sd". These are averages
    over annual static pools, so they do NOT invert to integer counts: there is
    no single cohort size behind them. They are for calibrating a generator's
    plausible range, not for reconstructing a cohort.
    """
    if horizon not in HORIZONS:
        raise ValueError(f"horizon must be one of {HORIZONS}")
    if stat not in ("mean", "sd"):
        raise ValueError("stat must be 'mean' or 'sd'")
    return {
        row["from_rating"]: [float(row[c]) for c in _PCT_COLS]
        for row in _rows("sp_global_average_1981_2024.csv")
        if row["horizon"] == horizon and row["stat"] == stat
    }


def default_rates(stat: str = "mean") -> dict[str, dict[str, float]]:
    """{horizon: {rating: default rate as a fraction}} from the long-run averages.

    Shows why a zero one-year AAA rate cannot be taken at face value: the same
    published table gives AAA a positive default rate at three and five years,
    so the one-year zero is an absence of observations in 44 pools rather than
    an absence of risk.
    """
    d = STATES.index("D")
    return {
        h: {r: pct[d] / 100.0 for r, pct in global_average(h, stat).items()}
        for h in HORIZONS
    }


def below_floor(horizon: str = "1y", regime: str = "us") -> tuple[str, ...]:
    """Grades whose published default rate sits under the regulatory PD floor."""
    if regime not in PD_FLOORS:
        raise ValueError(f"regime must be one of {tuple(PD_FLOORS)}")
    rates = default_rates()[horizon]
    return tuple(r for r in RATINGS if rates[r] < PD_FLOORS[regime])
