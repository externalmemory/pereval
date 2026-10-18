"""Synthetic rating-migration portfolio with an exact expected-loss oracle.

Design notes, because several choices here are load-bearing.

The response law is a one-factor ordered-probit threshold shift, the
CreditMetrics / Belkin-Suchower-Forest construction. A systematic factor z,
drawn from the macro path, shifts every rating row's thresholds at once. That
preserves row sums exactly, moves downgrades and defaults up while moving
upgrades down coherently, and cannot produce a non-monotone row. Scaling
downgrade and upgrade probabilities by separate multipliers does none of those
things reliably, which is why it is not used.

Macro paths come from the CCAR generator, so the history, the ragged starts and
the nine-quarter supervisory scenario overlay are the ones that task already
calibrates to FRED. Only the response law is new.

Observed transitions are published as ANNUAL counts, while the portfolio
actually migrates QUARTERLY under a factor that moves every quarter. The annual
matrix for a year is therefore a product of four different quarterly matrices,
not the fourth power of one, so no quarterly matrix reproduces it and a
principal fourth root is not generally stochastic. Finite portfolio sampling
makes that worse. Both effects are measured in tests.

The holdout portfolio's rating mix differs from the history's on purpose. With
the same mix, a direct regression of the portfolio default rate on macros scores
well without any transition model, which would make the rating structure
decoration. A shifted mix only transfers if per-rating migration is modelled.

Withdrawals (the published NR column) are dropped and rows renormalised, the
usual withdrawal-adjusted convention, so portfolio size is constant apart from
default and replacement. Treating withdrawal as a competing risk is left out of
this version.
"""

from __future__ import annotations

import csv
import io
import json

import numpy as np
from scipy.linalg import fractional_matrix_power
from scipy.stats import norm

from pereval.tasks.ccar.generator import MACRO_COLUMNS, N_STRESS
from pereval.tasks.ccar.generator import _simulate as _ccar_macros
from pereval.tasks.migration.reference import RATINGS, STATES, global_average

#: Rating states plus default. Withdrawals are dropped; see the module docstring.
LIVE = tuple(RATINGS)                       # 7 rating grades, best to worst
D = len(LIVE)                               # index of the absorbing default state
N_STATE = D + 1

#: Macros that rise in a recession, and those that fall. A drawn law uses one of
#: each, so the sign is not guessable from the column name alone.
UP = ("unemployment", "bbb_spread", "vix")
DOWN = ("hpi", "gdp", "nasdaq")

#: Asset-correlation range. Basel's corporate band is 0.12 to 0.24; the lower
#: half is used so a single year still carries information about the factor.
RHO_RANGE = (0.08, 0.20)

#: Obligors in the portfolio, and the published cohort mix it is built from.
N_OBLIGORS = 10_000

#: Rating mix of the history portfolio, calibrated so the unconditional annual
#: portfolio default rate is 0.99%, the order of magnitude a large bank's
#: wholesale book carries. S&P's own rated-issuer cohort is far more speculative
#: (26.5% B, 5.3% CCC/C, giving 2.7% annual) because it is a ratings universe
#: rather than a loan book, so the published mix is not used directly.
#:
#: AAA has a small share because a real portfolio holds some. Its one-step
#: default probability is exactly zero, which is realistic rather than a defect:
#: no AAA issuer has defaulted within one year in the published history. Over
#: nine quarters AAA obligors still default, by migrating down first.
BASE_MIX = np.array([0.010, 0.040, 0.200, 0.395, 0.250, 0.090, 0.015])


def _withdrawal_adjusted_annual() -> np.ndarray:
    """Published long-run one-year matrix, NR dropped, rows renormalised."""
    rows = global_average("1y")
    m = np.zeros((N_STATE, N_STATE))
    nr = STATES.index("NR")
    keep = [i for i in range(len(STATES)) if i != nr]
    for i, r in enumerate(LIVE):
        full = np.array(rows[r]) / 100.0
        m[i] = full[keep]
    m[D, D] = 1.0
    m[:D] /= m[:D].sum(axis=1, keepdims=True)
    return m


#: Cromwell floor on any live transition: nothing physically reachable is
#: assigned exactly zero. Immaterial in size, load-bearing in principle.
CELL_FLOOR = 1e-9

#: Floor on the default column, the quarterly equivalent of the 0.03% annual PD
#: floor at 12 CFR 217.131(d)(2). Set here rather than left to the data because
#: the published AAA default rate is 0.00%, an absence of observations in 44
#: static pools rather than an absence of risk, and a fourth root of zero is
#: still zero. A projection of exactly zero default allocates no reserve to a
#: live exposure, which is imprudent whatever the long-run average works out to.
PD_FLOOR_QUARTERLY = 1.0 - (1.0 - 0.0003) ** 0.25


def quarterly_base() -> np.ndarray:
    """Unconditional quarterly matrix: the principal fourth root, made admissible.

    The fourth root of the published annual average needs clipping only at the
    1e-16 level, but it inherits four exact zeros, one of them AAA to default.
    Those are floored here so the generator obeys the rule it tests for: the
    oracle has to be achievable by a model that assigns no impossible
    certainties. The non-embeddability this task turns on arises later, from a
    factor that moves within the year and from finite sampling, not here.

    The default column is floored first and held fixed while the rest of each row
    is rescaled, so renormalisation cannot push a default probability back under
    the regulatory minimum.
    """
    q = np.real(fractional_matrix_power(_withdrawal_adjusted_annual(), 0.25))
    q = np.clip(q, CELL_FLOOR, None)
    q[D, :] = 0.0
    q[D, D] = 1.0
    live = q[:D]
    live[:, D] = np.maximum(live[:, D], PD_FLOOR_QUARTERLY)
    # hold the default column, rescale the surviving states to close each row
    rest = live[:, :D]
    target = 1.0 - live[:, D]
    rest *= (target / rest.sum(axis=1))[:, None]
    q[:D] = live
    return q


def conditional_matrix(base: np.ndarray, z: float, rho: float) -> np.ndarray:
    """Shift ordered-probit thresholds by sqrt(rho)*z. Positive z means worse.

    Cumulating from the worst state means a positive shift moves probability
    mass toward default for every grade at once, which is what a systematic
    credit factor does.
    """
    if not 0.0 <= rho < 1.0:
        raise ValueError("rho must be in [0, 1)")
    out = np.zeros_like(base)
    for i in range(D):
        cum = np.cumsum(base[i][::-1])[::-1]
        thr = norm.ppf(np.clip(cum, 1e-15, 1 - 1e-15))
        shifted = norm.cdf((thr + np.sqrt(rho) * z) / np.sqrt(1.0 - rho))
        shifted[0] = 1.0
        row = -np.diff(np.append(shifted, 0.0))
        out[i] = np.clip(row, 0.0, None)
        out[i] /= out[i].sum()
    out[D, D] = 1.0
    return out


#: How long conditions deteriorate before recovery begins, in quarters, by
#: scenario. Published supervisory scenarios deteriorate for a few quarters and
#: then recover; they do not worsen monotonically for the whole horizon. Two to
#: six quarters covers the range, with severe stress lasting longer.
STRESS_QUARTERS = {"baseline": (2, 3), "adverse": (3, 5), "severe": (4, 6)}

#: Fraction of the peak stress still present at the end of the horizon. Recovery
#: is partial: nine quarters is not long enough to return to normal after a
#: severe downturn.
RECOVERY_FRACTION = {"baseline": (0.0, 0.3), "adverse": (0.2, 0.45),
                     "severe": (0.35, 0.6)}

#: Series that trend, so their stressed path is reshaped through the growth rate
#: rather than the level. sp500 and djia are derived from nasdaq and share its
#: kind.
_TRENDING = {"gdp", "hpi", "cpi", "nasdaq", "sp500", "djia"}
_LOG_LEVEL = {"unemployment", "vix"}


def hump_shape(n: int, peak: int, recovery: float) -> np.ndarray:
    """Severity weights over the horizon: rise to 1.0 at `peak`, then partially back.

    Quarter indices are 1-based in the description and 0-based here. The weight
    reaches its maximum at the peak quarter and decays linearly to `recovery` by
    the final quarter, so the path deteriorates, turns, and improves without
    returning to normal.
    """
    if not 1 <= peak <= n:
        raise ValueError("peak must fall inside the horizon")
    if not 0.0 <= recovery <= 1.0:
        raise ValueError("recovery fraction must be in [0, 1]")
    w = np.empty(n)
    w[:peak] = np.linspace(1.0 / peak, 1.0, peak)
    if peak < n:
        w[peak:] = np.linspace(1.0, recovery, n - peak + 1)[1:]
    return w


def reshape_scenario(levels: dict, intime: slice, stress: slice,
                     w: np.ndarray) -> dict:
    """Replace the inherited monotone ramp over the horizon with a hump.

    The CCAR overlay ramps level series linearly to a target and holds growth
    series at a constant stressed rate, so every published series is monotone
    across the horizon. That is not what a supervisory scenario looks like. The
    reshaping is applied here rather than in the CCAR generator so that task's
    archived measurements are untouched.

    Each series is reshaped in the space its overlay acts on: the level for a
    level series, the log level for a log-level series, and the quarter-on-quarter
    growth rate for a trending one, which is then recumulated from the last
    historical value.
    """
    out = {n: np.asarray(v, dtype=float).copy() for n, v in levels.items()}
    last = stress.start - 1
    n_h = stress.stop - stress.start
    if len(w) != n_h:
        raise ValueError("weight vector must match the horizon length")
    for name, x in out.items():
        if name in _TRENDING:
            g = np.diff(np.log(x[last:stress.stop]))
            base = float(np.diff(np.log(x[intime]))[-8:].mean())
            dev = float(g[0]) - base
            lvl = x[last]
            for k in range(n_h):
                lvl *= np.exp(base + dev * w[k])
                x[stress.start + k] = lvl
        elif name in _LOG_LEVEL:
            lx = np.log(x)
            a, b = lx[last], lx[stress.stop - 1]
            lx[stress] = a + (b - a) * w
            x[:] = np.exp(lx)
        else:
            a, b = x[last], x[stress.stop - 1]
            x[stress] = a + (b - a) * w
    return out


def draw_dgp(rng: np.random.Generator) -> dict:
    """The per-instance response law. Nothing about it is in any public file."""
    return {
        "driver_up": str(UP[rng.integers(len(UP))]),
        "driver_down": str(DOWN[rng.integers(len(DOWN))]),
        "weight_up": float(rng.uniform(0.5, 1.0)),
        "weight_down": float(rng.uniform(0.3, 0.8)),
        "rho": float(rng.uniform(*RHO_RANGE)),
        "mix_tilt": float(rng.uniform(0.15, 0.40)),
    }


def _yoy(level: np.ndarray) -> np.ndarray:
    """Four-quarter fractional change, back-filled over the first year."""
    y = np.empty(len(level))
    y[4:] = level[4:] / level[:-4] - 1.0
    y[:4] = y[4]
    return y


def systematic_factor(dgp: dict, levels: dict, calib: slice) -> np.ndarray:
    """Standardise the two drivers on the history window, then combine into z.

    The recession-up driver enters as a level and the recession-down driver as a
    year-over-year change, matching the CCAR reference fit. That is not cosmetic:
    gdp, hpi and nasdaq are trending level series, so standardising them against
    a forty-year mean is dominated by the trend and leaves a stressed scenario
    sitting two standard deviations ABOVE its own history. Entering them as a
    change removes the trend and restores the sign.

    Standardising on history rather than on the full path is deliberate: the
    scenario window is where the factor is supposed to go out of range, so it
    must not be allowed to shrink its own scale.
    """
    def norm_series(name, as_change=False):
        x = np.asarray(levels[name], dtype=float)
        if as_change:
            x = _yoy(x)
        ref = x[calib]
        sd = ref.std(ddof=1)
        return (x - ref.mean()) / (sd if sd > 1e-12 else 1.0)

    z = (dgp["weight_up"] * norm_series(dgp["driver_up"])
         - dgp["weight_down"] * norm_series(dgp["driver_down"], as_change=True))
    ref = z[calib]
    return (z - ref.mean()) / (ref.std(ddof=1) if ref.std(ddof=1) > 1e-12 else 1.0)


def holdout_mix(tilt: float) -> np.ndarray:
    """BASE_MIX tilted toward speculative grade, so an aggregate-only fit fails."""
    w = BASE_MIX * np.exp(tilt * np.arange(len(LIVE)))
    return w / w.sum()


def _multinomial_states(rng, counts_by_state, matrix):
    """One quarter of migration for a vector of per-state obligor counts."""
    out = np.zeros(N_STATE, dtype=np.int64)
    for i in range(D):
        n = int(counts_by_state[i])
        if n:
            out += rng.multinomial(n, matrix[i])
    out[D] += int(counts_by_state[D])
    return out


def simulate_history(base, dgp, z, n_years, rng, mix=None):
    """Quarterly migration with replacement, published as annual cohort counts.

    Annual counts follow the static-pool convention the published data uses: an
    obligor is recorded against the rating it held at the start of the year, and
    an obligor that defaults during the year is recorded as a default and then
    replaced in the live portfolio by a new one drawn from the initial mix. The
    replacement is not part of that year's cohort.
    """
    mix = BASE_MIX if mix is None else mix
    live = rng.multinomial(N_OBLIGORS, mix).astype(np.int64)
    annual, q = [], 0
    for _ in range(n_years):
        cohort = np.zeros((D, N_STATE), dtype=np.int64)
        for i in range(D):
            cohort[i, i] = live[i]
        for _ in range(4):
            m = conditional_matrix(base, float(z[q]), dgp["rho"])
            q += 1
            nxt = np.zeros_like(cohort)
            for i in range(D):
                nxt[i] = _multinomial_states(rng, cohort[i], m)
            cohort = nxt
            # replacements keep the live portfolio at N_OBLIGORS but join no cohort
            defaults = int(cohort[:, D].sum())
            live = cohort[:, :D].sum(axis=0)
            if defaults:
                live = live + rng.multinomial(defaults, mix)
        annual.append(cohort.copy())
    return annual, live


CHECKPOINTS = (4, 9)


def expected_distributions(base, dgp, z, mix, checkpoints=CHECKPOINTS):
    """Exact expected cohort distribution at each checkpoint: grades plus default.

    This is the scored object, and it is the ORIGINAL COHORT rather than the live
    portfolio: default is absorbing here and replacements are excluded. Two
    reasons. The live portfolio's grade shares renormalise to one, so its
    cumulative distribution ends at one by construction and a sup-norm distance
    cannot see the default rate at all. And the agent observes static-pool annual
    counts, so predicting a static-pool outcome keeps observation and target on
    one convention.

    Replacement still governs the history simulation, where it keeps the book at
    N_OBLIGORS and so keeps the observed counts realistic. It simply does not
    enter the scored quantity.

    Deterministic propagation, so the oracle carries no Monte Carlo error and is
    exactly achievable.
    """
    v = np.concatenate([mix, [0.0]])
    out = {}
    for t in range(max(checkpoints)):
        v = v @ conditional_matrix(base, float(z[t]), dgp["rho"])
        if t + 1 in checkpoints:
            out[t + 1] = {s: float(x) for s, x in zip(list(LIVE) + ["D"], v)}
    return out


def expected_default_path(base, dgp, z, mix):
    """Exact expected cumulative default fraction by rating over the horizon.

    Deterministic linear recursion, so the oracle is exactly achievable and
    carries no Monte Carlo error. Each rating's cohort is propagated separately
    to give a per-rating answer; replacement is applied to the portfolio total
    only, which is what the scored quantity is defined on.
    """
    per_rating, horizon = {}, len(z)
    for i, r in enumerate(LIVE):
        v = np.zeros(N_STATE)
        v[i] = 1.0
        for t in range(horizon):
            v = v @ conditional_matrix(base, float(z[t]), dgp["rho"])
        per_rating[r] = float(v[D])
    v = np.concatenate([mix, [0.0]])
    cumulative = 0.0
    for t in range(horizon):
        v = v @ conditional_matrix(base, float(z[t]), dgp["rho"])
        d = float(v[D])
        cumulative += d
        v[D] = 0.0
        v[:D] += d * mix          # replace defaults from the initial mix
    return per_rating, cumulative


def annual_counts_rows(annual):
    """Long-format annual transition counts, the agent's main observation."""
    rows = []
    for year, c in enumerate(annual, start=1):
        for i, r in enumerate(LIVE):
            row = {"year": year, "from_rating": r}
            for j, s in enumerate(list(LIVE) + ["D"]):
                row[f"to_{s.replace('/', '_')}"] = int(c[i, j])
            rows.append(row)
    return rows


def generate(seed: int = 1, n_years: int = 40, scenario: str = "adverse") -> dict:
    """One instance. n_years of annual counts, then a nine-quarter scenario."""
    if n_years < 10:
        raise ValueError("need at least 10 years of annual counts")
    n_intime = 4 * n_years
    ss = np.random.SeedSequence([seed, 7717])
    rng_law, rng_port = (np.random.default_rng(s) for s in ss.spawn(2))
    dgp = draw_dgp(rng_law)
    macros = _ccar_macros(seed, n_intime, 50, None, scenario)
    calib, stress = macros["intime_slice"], macros["stress_slice"]
    # Give the horizon a realistic shape: deteriorate for a few quarters, turn,
    # then recover partly. The inherited overlay is monotone across all nine.
    peak = int(rng_law.integers(*STRESS_QUARTERS[macros["scenario"]], endpoint=True))
    recovery = float(rng_law.uniform(*RECOVERY_FRACTION[macros["scenario"]]))
    dgp["peak_quarter"], dgp["recovery_fraction"] = peak, recovery
    levels = reshape_scenario(macros["levels"], calib, stress,
                              hump_shape(stress.stop - stress.start, peak, recovery))
    scenario_rows = [
        {"quarter": n_intime + 1 + k,
         **{n: round(float(levels[n][stress.start + k]), 4) for n in MACRO_COLUMNS}}
        for k in range(stress.stop - stress.start)
    ]
    z = systematic_factor(dgp, levels, calib)
    base = quarterly_base()

    annual, _ = simulate_history(base, dgp, z[calib], n_years, rng_port)
    mix = holdout_mix(dgp["mix_tilt"])
    z_scen = z[stress]
    counts = {r: int(v) for r, v in
              zip(LIVE, np.round(mix * N_OBLIGORS).astype(int))}
    per_rating, total = expected_default_path(base, dgp, z_scen, mix)
    dists = expected_distributions(base, dgp, z_scen, mix)

    # one realized holdout path, reported as a diagnostic rather than scored
    realized, _ = simulate_history(base, dgp, np.repeat(z_scen, 1), 2, rng_port, mix)
    return {
        "dgp": dgp,
        "annual_counts": annual_counts_rows(annual),
        "history_rows": macros["train_rows"],
        "scenario_rows": scenario_rows,
        "holdout_mix": {r: float(v) for r, v in zip(LIVE, mix)},
        "holdout_counts": counts,
        "truth": {
            "per_rating_default_rate": per_rating,
            "portfolio_default_rate": total,
            "rating_distribution": {str(k): v for k, v in dists.items()},
            # Derived from the ROUNDED obligor counts in data/portfolio.csv, not
            # from the unrounded mix: the degenerate anchor has to be reachable
            # from public data, and integer counts are all the agent can see.
            "start_mix": {**{r: float(n) / sum(counts.values())
                             for r, n in counts.items()}, "D": 0.0},
            "checkpoints": list(CHECKPOINTS),
            "horizon_quarters": N_STRESS,
            "z_scenario": [float(v) for v in z_scen],
        },
        "scenario": macros["scenario"],
        "seed": seed,
    }


def _csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def public_files(bundle: dict) -> dict[str, str]:
    """Only these four files enter the sandbox."""
    mix = bundle["holdout_counts"]
    return {
        "data/transitions.csv": _csv(bundle["annual_counts"]),
        "data/macro_history.csv": _csv(bundle["history_rows"]),
        "data/scenario.csv": _csv(bundle["scenario_rows"]),
        "data/portfolio.csv": _csv(
            [{"rating": r, "obligors": n} for r, n in mix.items()]),
        "data/policy.json": json.dumps(
            {"checkpoints": list(CHECKPOINTS), "horizon_quarters": N_STRESS,
             "obligors": int(sum(mix.values()))}),
    }


__all__ = [
    "BASE_MIX", "D", "LIVE", "MACRO_COLUMNS", "N_OBLIGORS", "RHO_RANGE",
    "CELL_FLOOR", "CHECKPOINTS", "PD_FLOOR_QUARTERLY", "RECOVERY_FRACTION",
    "STRESS_QUARTERS", "conditional_matrix", "hump_shape", "reshape_scenario",
    "draw_dgp", "expected_default_path",
    "expected_distributions", "generate",
    "holdout_mix", "public_files", "quarterly_base", "simulate_history",
    "systematic_factor",
]
