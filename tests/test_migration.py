"""Provenance tests for the published rating-migration reference data.

These do not test a task, because the task does not exist yet. They pin the
chain from the source document to the CSVs: the reconstructed counts must
reproduce the published percentages, and the reconstructed default column must
match a figure the source states independently of the transition tables.
"""

from __future__ import annotations

import numpy as np
import pytest

from pereval.tasks.migration.reference import (
    COHORT_ROWS,
    REGIONS,
    STATES,
    global_average,
    regional_counts,
    regional_published_pct,
)


def test_every_region_has_every_cohort_row():
    counts = regional_counts()
    assert set(counts) == set(REGIONS)
    for region, rows in counts.items():
        assert set(rows) == set(COHORT_ROWS), region


def test_counts_sum_to_cohort_size():
    for region, rows in regional_counts().items():
        for rating, rec in rows.items():
            assert sum(rec["counts"]) == rec["cohort_size"], (region, rating)


def test_counts_reproduce_the_published_percentages():
    """The reconstruction is only trustworthy if it round-trips to 2dp."""
    counts, pub = regional_counts(), regional_published_pct()
    for region in REGIONS:
        for rating in COHORT_ROWS:
            rec = counts[region][rating]
            n = rec["cohort_size"]
            back = [round(k * 100.0 / n, 2) for k in rec["counts"]]
            assert back == pytest.approx(pub[region][rating], abs=0.005), (region, rating)


def test_global_default_column_matches_the_studys_own_tally():
    """Independent check on the reconstruction.

    The source states that of 145 total 2024 defaulters, 130 were rated at the
    start of the year. The default column of the reconstructed global cohort is
    exactly those 130, and nothing in the transition tables says so, so this
    confirms the inverted cohort sizes rather than restating them.
    """
    d = STATES.index("D")
    total = sum(rec["counts"][d] for rec in regional_counts()["Global"].values())
    assert total == 130


def test_regional_defaults_do_not_exceed_the_global_cohort():
    d = STATES.index("D")
    counts = regional_counts()
    glob = sum(rec["counts"][d] for rec in counts["Global"].values())
    for region in ("U.S.", "Europe", "EM"):
        n = sum(rec["counts"][d] for rec in counts[region].values())
        assert n <= glob, region


def test_long_run_average_rows_sum_to_one_hundred():
    for horizon in ("1y", "3y"):
        for rating, pct in global_average(horizon).items():
            assert sum(pct) == pytest.approx(100.0, abs=0.02), (horizon, rating)


def test_long_run_matrix_is_not_markov_consistent():
    """Cubing the one-year average understates the published three-year default rate.

    This is the empirical premise of the planned task: rating migration is not a
    time-homogeneous Markov chain, so a quarterly matrix obtained by rooting an
    annual one is fitting a model the data rejects. The gap is measured here so
    that a later change to the reference data cannot quietly remove it. D and NR
    are treated as absorbing.
    """
    def closed(horizon):
        rows = global_average(horizon)
        m = np.zeros((9, 9))
        for i, r in enumerate(STATES[:7]):
            m[i] = np.array(rows[r]) / 100.0
        m[7, 7] = m[8, 8] = 1.0
        m[:7] /= m[:7].sum(axis=1, keepdims=True)
        return m

    cubed = np.linalg.matrix_power(closed("1y"), 3)
    published = closed("3y")
    d = STATES.index("D")
    for rating in ("AA", "A", "BBB"):
        i = STATES.index(rating)
        assert cubed[i, d] < published[i, d], rating
        # the shortfall is material, not a rounding artefact
        assert cubed[i, d] / published[i, d] < 0.95, rating
