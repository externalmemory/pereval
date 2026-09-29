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
    COUNT_ROWS,
    HORIZONS,
    PD_FLOORS,
    RATINGS,
    REGIONS,
    STATES,
    below_floor,
    default_rates,
    global_average,
    regional_counts,
    regional_published_pct,
)


def test_every_region_has_every_count_row():
    counts = regional_counts()
    assert set(counts) == set(REGIONS)
    for region, rows in counts.items():
        assert set(rows) == set(COUNT_ROWS), region


def test_counts_sum_to_cohort_size():
    for region, rows in regional_counts().items():
        for rating, rec in rows.items():
            assert sum(rec["counts"]) == rec["cohort_size"], (region, rating)


def test_counts_reproduce_the_published_percentages():
    """The reconstruction is only trustworthy if it round-trips to 2dp."""
    counts, pub = regional_counts(), regional_published_pct()
    for region in REGIONS:
        for rating in COUNT_ROWS:
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


def test_aaa_is_in_the_rating_scale_at_every_horizon():
    """AAA has no recoverable 2024 count row, but it is not missing from the data."""
    assert "AAA" in RATINGS
    assert "AAA" not in COUNT_ROWS
    for horizon in HORIZONS:
        assert "AAA" in global_average(horizon)
        assert "AAA" in global_average(horizon, "sd")


def test_long_run_average_rows_sum_to_one_hundred():
    """Tolerance is the rounding bound, not a fudge: nine entries at 2dp can
    accumulate 9 * 0.005 = 0.045. The observed worst case is 0.02, on 5y AA."""
    for horizon in HORIZONS:
        for rating, pct in global_average(horizon).items():
            assert sum(pct) == pytest.approx(100.0, abs=0.045), (horizon, rating)


def test_zero_one_year_aaa_default_rate_is_a_sample_artefact():
    """The same published table gives AAA positive default risk at longer horizons.

    One-year AAA to default rounds to 0.00% over 44 static pools, but three-year
    is 0.13% and five-year 0.34%. So the zero is an absence of observations, not
    an absence of risk, and a model that carries it through as an exact zero
    assigns no allowance to a live exposure.
    """
    rates = default_rates()
    assert rates["1y"]["AAA"] == 0.0
    assert rates["3y"]["AAA"] > 0.0
    assert rates["5y"]["AAA"] > rates["3y"]["AAA"]


def test_top_grades_fall_below_the_regulatory_pd_floor():
    """Two grades sit under the US floor, so the data cannot be used unfloored.

    12 CFR 217.131(d)(2) sets 0.03% for wholesale obligors, sovereigns excepted.
    Published long-run one-year rates are 0.00% for AAA and 0.02% for AA, so an
    IRB-consistent model has to override the observed rate at the top of the
    scale rather than reproduce it.
    """
    assert PD_FLOORS["us"] == 0.0003
    assert PD_FLOORS["basel"] > PD_FLOORS["us"]
    assert below_floor("1y", "us") == ("AAA", "AA")
    # the Basel figure binds one grade further up the scale
    assert "A" in below_floor("1y", "basel") or default_rates()["1y"]["A"] >= PD_FLOORS["basel"]


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


def test_markov_cube_also_understates_aaa_default_risk():
    """AAA is the worst case for the Markov assumption, not an exception to it.

    Because the one-year AAA default entry is exactly zero, a cubed one-year
    matrix reaches default only by migrating down first, giving roughly a third
    of the published three-year rate.
    """
    rows = global_average("1y")
    m = np.zeros((9, 9))
    for i, r in enumerate(STATES[:7]):
        m[i] = np.array(rows[r]) / 100.0
    m[7, 7] = m[8, 8] = 1.0
    m[:7] /= m[:7].sum(axis=1, keepdims=True)
    d = STATES.index("D")
    cubed_aaa = np.linalg.matrix_power(m, 3)[0, d]
    published_aaa = default_rates()["3y"]["AAA"]
    assert 0.0 < cubed_aaa < 0.5 * published_aaa
