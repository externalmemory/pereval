"""CCAR-style stress loss task generator.

The agent gets a quarterly panel of nine macroeconomic drivers plus a portfolio
default rate over an in-time window, and a 9-quarter forward stress scenario for
the same nine drivers, and must project the default rate (point plus 95% interval)
for the nine stressed quarters. It is the realistic analog of the toy tasks: the
in-time fit is easy to overfit, and the out-of-time path is where a sound model separates
from a fragile one. Not because the drivers necessarily leave their observed range, which
they do for only about 15% of the nine on a typical instance, but because the scenario
describes a joint configuration the history need not contain, and because the response is
nonlinear in two of the three families.

Data-generating process, none of which is disclosed to the agent:

- Macros: a diagonal AR(1)-plus-correlated-innovations vector calibrated to real
  FRED series (Phase 0). Persistence, marginal moments, and the cross-correlation
  of innovations are matched. Unemployment and VIX are generated in log space
  (positive, right-skewed); GDP/HPI/CPI as growth, equities as returns, BBB spread
  as a level. S&P 500 and DJIA are near-duplicate siblings of NASDAQ (collinear
  distractors). Levels are reconstructed from the stationary transforms.

- Contamination: a rare, one-quarter, systemic crisis (COVID/GFC-like) is added to
  the OBSERVED macros only, as a common correlated spike (unemployment/spread/VIX
  up, GDP/equities down). It is transient and reverts next quarter.

- Default rate: extended-Vasicek, dr = Phi((lin + sqrt(rho)*eps)/sqrt(1-rho)) with
  eps ~ N(0,1) i.i.d., where lin is a probit-scale conditional mean built from two
  standardized drivers: u1, one macro that rises in a recession, as a level, and u2,
  one that falls, as a year-over-year change. Crucially the default uses the
  FUNDAMENTAL (pre-crisis) drivers, so a COVID-style spike appears in the data but
  the default rate does not follow it; only persistent moves in the fundamental drive
  defaults. The other seven macros are correlated distractors.

  Every parameter of that law (p, rho, k1, k2), WHICH two macros are the drivers, and
  the functional form of lin, rotated over three families, are all DRAWN PER
  INSTANCE. This
  is load-bearing rather than cosmetic. When the coefficients were fixed module
  constants they were also published in this file, so the whole instance was
  solvable in closed form from the repo without estimating anything: that exploit
  scored 0.0001 mean regret against 0.013 for the fitted reference and 0.029 for
  the best measured model, and it defeated the contamination argument in
  docs/limitations.md, which rests on parameters not being recoverable from the
  source. Rotating the family does the second half of the job. A single fixed form
  means a good score can only demonstrate that the agent recovers THIS law; the
  inference the suite wants to support is that it can recover A law, which requires
  the form to vary. docs/task-design.md names both mitigations (per-instance
  parameters, rotate DGP families) as obligations of the plasmode family.

- Stress scenario: the 9 out-of-time quarters ramp the FUNDAMENTAL drivers toward a
  target anchored on each series' marginal mean (unemployment, spreads and VIX up, GDP,
  HPI and equities down), so the default rate rises whichever pair was drawn. Anchoring
  the TARGET rather than an increment is what a supervisory scenario does: the Fed
  specifies that unemployment reaches a level, and how severe that is relative to recent
  history depends on where the starting point happens to be. Severity therefore still
  varies across instances, and some scenarios are mild, which is a property of scenarios
  and not a defect: CCAR runs a baseline alongside its adverse ones. Realized severity is
  recorded per instance in the truth metadata so a result can be conditioned on it. Unlike the transient crisis, this is a real deterioration
  and the default responds. A model that attenuated its sensitivity to fit the COVID
  quarter, or flipped a sign under collinearity, will misproject here and pay for it
  in Winkler regret.

- Missing data: the later-starting series (HPI, VIX, BBB spread, S&P, DJIA) are
  NaN for the early quarters, as on FRED, so the agent must handle ragged history.

The angle-free target is linear, scored with pereval.scorers.interval at
period=None, keyed by quarter, averaged over the 9 stressed quarters.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

import numpy as np
from scipy.stats import norm

# --- calibrated constants (Phase 0, from FRED) ---------------------------

# name: (kind, m, s, phi, crisis_load)  in the stationary/log space of that kind
#   kind: "growth" (log growth), "ret" (log return), "level", "loglevel"
#   m, s: marginal mean and sd of the stationary transform; phi: AR(1)
#   crisis_load: one-quarter observed spike, in marginal-sd units (systemic recession signs)
CORE = {
    "gdp": ("growth", 0.0076, 0.0111, 0.13, -6.0),
    "unemployment": ("loglevel", 1.6885, 0.2977, 0.882, +3.0),
    "hpi": ("growth", 0.0105, 0.0185, 0.58, -0.5),
    "bbb_spread": ("level", 2.2649, 0.6784, 0.89, +5.0),
    "nasdaq": ("ret", 0.0249, 0.0905, 0.26, -4.0),
    "vix": ("loglevel", 2.9161, 0.3102, 0.79, +4.0),
    "cpi": ("growth", 0.0078, 0.0142, 0.67, -3.0),
}
CORE_NAMES = list(CORE)

# innovation correlation of the seven core series, in CORE_NAMES order
R = np.array([
    [1.00, -0.74, 0.08, -0.40, 0.22, -0.29, 0.23],
    [-0.74, 1.00, -0.13, 0.21, 0.04, 0.10, -0.10],
    [0.08, -0.13, 1.00, -0.26, 0.05, -0.16, 0.44],
    [-0.40, 0.21, -0.26, 1.00, -0.53, 0.58, -0.44],
    [0.22, 0.04, 0.05, -0.53, 1.00, -0.53, 0.18],
    [-0.29, 0.10, -0.16, 0.58, -0.53, 1.00, -0.32],
    [0.23, -0.10, 0.44, -0.44, 0.18, -0.32, 1.00],
])

# S&P 500 and DJIA as collinear siblings of NASDAQ: return moments and sibling corr
SIBLINGS = {"sp500": (0.0311, 0.0467, 0.91), "djia": (0.0263, 0.0427, 0.80)}
MACRO_COLUMNS = ["gdp", "unemployment", "hpi", "bbb_spread", "sp500", "djia", "nasdaq", "vix", "cpi"]

# Extended-Vasicek default parameters, drawn per instance. The ranges bracket the
# FRED / vasicekfit calibration that these were previously fixed at (p 0.028,
# rho 0.02, k1 0.13, k2 -0.07, unemployment 5.66/1.72, HPI YoY 0.0442/0.0580), so
# a drawn instance is as plausible as the old fixed one; it is just not knowable in
# advance. The standardizations are absorbed by any fitted model and are randomized
# only to close constant-matching; the coefficients and the family are what matter.
DGP_RANGES = {
    # Centred on the FRED / vasicekfit calibration these were fixed at (p 0.028, rho 0.02,
    # k1 0.13, k2 -0.07) and kept tight around it, so the drawn task has the same scale as
    # the published one rather than merely bracketing it. An earlier version used ranges
    # roughly three times wider, which put mean rho at 0.030 against the old 0.020 and
    # moved the oracle from 0.070 to 0.100, changing the units every archived CCAR number
    # was reported in for no gain: the exploit is closed by the draw existing, not by its
    # width, and it is the driver pair that carries most of that.
    # Centred tightly on the calibration these were fixed at (p 0.028, rho 0.02, k1 0.13,
    # k2 -0.07), so the drawn task keeps the scale of the published one.
    #
    # Width was deliberately NOT pushed further, and the tradeoff is worth recording. The
    # exploit works while guessing a coefficient's midpoint beats estimating it from 80
    # noisy quarters, so suppressing it entirely needs a spread wider than that estimation
    # error. Trying that (k1 over [0.08, 0.20]) damaged the task: the reference fit, handed
    # the true drivers, fell to 0.52 interval coverage, because a wide k1 amplifies any
    # standardization difference three standard deviations out along the scenario path. A
    # generator whose own correctly specified reference cannot cover is not a better task.
    #
    # So a residual remains: a model that memorized these published ranges and guessed
    # their midpoints would score a little better than an honest fit. That is a reduction
    # of roughly 400x from the fixed-constant exploit, which scored 0.00014 against an
    # oracle, and it is a future risk rather than a present one, since every model measured
    # here has a knowledge cutoff predating this repository. Closing it further costs more
    # than it buys.
    "p": (0.020, 0.038),
    "rho": (0.014, 0.028),
    "k1": (0.100, 0.170),
    "k2": (-0.100, -0.045),
    # threshold family: the kink sits at this quantile of the IN-TIME u1 distribution,
    # not at a fixed number of sd. Placing it near the top of the observed range is what
    # makes the trap sharp: only a handful of in-time quarters sit above it, so the
    # nonlinearity is nearly invisible to an in-sample fit, while the whole stress path
    # is above it. A fixed sd threshold left some instances where u1 never crossed the
    # kink until the final quarter, making the family indistinguishable from `vasicek`.
    "thresh_q": (0.80, 0.95),
    "thresh_extra": (0.08, 0.22),  # threshold family: added slope above the kink
    # interaction family: coefficient on u1*u2. Kept small because the cross term is
    # the product of two drivers that each reach about 3 sd under a severe scenario,
    # so it moves the probit mean by roughly 9*|k3| at the end of the path; wider than
    # this and the stressed default rate leaves any plausible range.
    "inter_k3": (-0.045, -0.020),
}

# Which macros are the true drivers also rotates. One driver is taken from the
# series that rise in a recession and enters as a level; the other from the series
# that fall and enters as a year-over-year change, so the transform-discovery step
# survives while the identity of the driver stops being memorizable. Nine pairs
# times three families is twenty-seven distinct laws, none of them in this file.
DRIVERS_UP = ("unemployment", "bbb_spread", "vix")
DRIVERS_DOWN = ("hpi", "gdp", "nasdaq")

# Scenario severity is a designed factor, not a residual. CCAR runs a baseline alongside
# its adverse and severely adverse scenarios, and a loss model has to be accurate across
# all of them: over-predicting losses in benign conditions is an error, not a safe choice,
# because conservatism is not a substitute for accuracy. Severity scales how far the
# drivers ramp, in marginal-sd units, so `baseline` leaves them at their unconditional
# means and `severe` drives them well past.
#
# This is what makes over-prediction detectable. A model that always projects a deep
# downturn scores well on `severe` and badly on `baseline`, and only a model that tracks
# the scenario scores well on both.
SCENARIOS = {"baseline": (0.0, 0.3), "adverse": (0.8, 1.2), "severe": (1.4, 1.8)}
SCENARIO_NAMES = tuple(SCENARIOS)

# The DEFAULT is the legacy range, not the three-point factor, and the default family is
# the probit-linear one. Only the response law needed to change: the exploit was that the
# coefficients were published, and drawing which two are non-zero and what they are closes
# it. Rotating the functional form and splitting scenario severity are improvements to the
# task, not fixes to the defect, and switching them on by default would discard the
# archived CCAR results for no security benefit. They are opt-in via -T family=rotate and
# -T scenario=rotate, or by pinning a single value.
LEGACY_SEVERITY = (1.0, 1.8)
DEFAULT_FAMILY = "vasicek"

# Response families. All three keep the probit link and the systematic factor, so
# rho and the interval math are recoverable in every one; what rotates is the shape
# of the macro dependence.
#
#   vasicek      probit-linear in u1 and u2. The classic form.
#   threshold    u1 gains extra sensitivity above a kink, so the driver bites harder
#                in a deep recession than a linear fit calibrated in normal times
#                predicts. Regime asymmetry, and outside the obvious model class.
#   interaction  a u1*u2 cross term. Nearly invisible in sample, where the two
#                drivers are both near their means, and decisive under a scenario
#                that pushes them adversely at the same time. The purest form of the
#                trap this task exists to set.
#
# `lagged` (the driver entering one or two quarters back) was tried and dropped: the
# level drivers are persistent enough (AR(1) 0.79 to 0.89) and the stress ramp smooth
# enough that a short lag is nearly unidentifiable, and it left the linear reference
# at 0.0174 against 0.0173 on `vasicek`, so it added a family without adding a
# distinction.
#
# The shipped vasicek_baseline fits the `vasicek` form. It is therefore a near-oracle
# reference on that family and a COMPETENT BUT MISSPECIFIED reference on the other
# two, which is the intended bracketing: see docs/tasks/ccar.md.
FAMILIES = ("vasicek", "threshold", "interaction")

CRISIS_P = 2.0 / 80.0  # ~2 systemic crises per 20-year window (GFC + COVID scale)
N_STRESS = 9
_WARMUP = 24  # discarded burn-in, also covers the 4-quarter HPI YoY lag


def _uni(rng, lo, hi):
    return float(rng.uniform(lo, hi))


def _to_level(kind, x, base_index=100.0):
    if kind == "level":
        return x
    if kind == "loglevel":
        return np.exp(x)
    if kind in ("growth", "ret"):
        return base_index * np.exp(np.cumsum(x))
    raise ValueError(kind)


def _hpi_yoy(level):
    y = np.full(len(level), np.nan)
    y[4:] = level[4:] / level[:-4] - 1.0
    return y


def draw_dgp(rng, family: str | None = None) -> dict:
    """Draw the response law for one instance: family, drivers, and every parameter."""
    d = {k: _uni(rng, *v) for k, v in DGP_RANGES.items()}
    if family is None:
        d["family"] = DEFAULT_FAMILY
    elif family == "rotate":
        d["family"] = FAMILIES[int(rng.integers(len(FAMILIES)))]
    else:
        d["family"] = family
    if d["family"] not in FAMILIES:
        raise ValueError(f"unknown family {d['family']!r}, expected one of {FAMILIES}")
    d["d1"] = DRIVERS_UP[int(rng.integers(len(DRIVERS_UP)))]
    d["d2"] = DRIVERS_DOWN[int(rng.integers(len(DRIVERS_DOWN)))]
    return d


def _standardize(x, pre_stress: slice):
    """Standardize by PRE-STRESS moments only, so nothing depends on the scenario.

    The window is warmup plus in-time rather than in-time alone. The level drivers are
    persistent (AR(1) 0.79 to 0.89), so the sample sd of an 80-quarter stretch of one
    is itself noisy and biased low, and standardizing on the shorter window let that
    artifact drive how severe the stressed default path came out. A model fitted by the
    agent sees only the in-time window and absorbs any constant rescaling into its own
    coefficient, so the longer window costs it nothing.
    """
    ref = np.asarray(x, dtype=float)[pre_stress]
    ref = ref[np.isfinite(ref)]
    return (np.asarray(x, dtype=float) - ref.mean()) / ref.std()


def probit_mean(dgp: dict, fund_levels: dict, pre_stress: slice):
    """The probit-scale conditional mean `lin`, so that E[dr | macros] = Phi(lin).

    Single source of truth for the response law: the observed default rate and the
    scorer's oracle both go through here, so they cannot drift apart. Standardizing
    on the in-time window rather than on published constants means the scale of each
    driver is instance-specific and absorbed by any fitted model, which is one less
    thing recoverable from this file.
    """
    u1 = _standardize(fund_levels[dgp["d1"]], pre_stress)
    u2 = _standardize(_hpi_yoy(fund_levels[dgp["d2"]]), pre_stress)
    lin = norm.ppf(dgp["p"]) + dgp["k1"] * u1 + dgp["k2"] * u2
    if dgp["family"] == "vasicek":
        return lin
    if dgp["family"] == "threshold":
        ref = u1[pre_stress]
        c = float(np.quantile(ref[np.isfinite(ref)], dgp["thresh_q"]))
        return lin + dgp["thresh_extra"] * np.maximum(u1 - c, 0.0)
    if dgp["family"] == "interaction":
        return lin + dgp["inter_k3"] * u1 * u2
    raise ValueError(dgp["family"])


def _default_rate(dgp, fund_levels, pre_stress, rng):
    lin = probit_mean(dgp, fund_levels, pre_stress)
    eps = rng.standard_normal(len(lin))
    z = (lin + np.sqrt(dgp["rho"]) * eps) / np.sqrt(1.0 - dgp["rho"])
    return norm.cdf(z)


def _simulate(seed: int, n_intime: int, oracle_n: int, family: str | None,
              scenario: str | None) -> dict:
    ss = np.random.SeedSequence(seed)
    rng_struct, rng_default, rng_oracle = (np.random.default_rng(s) for s in ss.spawn(3))

    # Drawn first, off rng_struct, so the response law is a function of the seed and
    # nothing about it is knowable from this file.
    dgp = draw_dgp(rng_struct, family)

    total = _WARMUP + n_intime + N_STRESS
    L = np.linalg.cholesky(R)

    # correlated fundamental innovations for the core series
    fund = {n: np.empty(total) for n in CORE_NAMES}
    for n in CORE_NAMES:
        fund[n][0] = CORE[n][1]
    innov_sd = {n: CORE[n][2] * np.sqrt(1 - CORE[n][3] ** 2) for n in CORE_NAMES}
    for t in range(1, total):
        z = L @ rng_struct.standard_normal(len(CORE_NAMES))
        for i, n in enumerate(CORE_NAMES):
            _, m, s, phi, _ = CORE[n]
            fund[n][t] = m + phi * (fund[n][t - 1] - m) + innov_sd[n] * z[i]

    # Sustained recession over the stress window (deterministic scenario overlay).
    # Level series ramp from the last in-time value to a TARGET anchored on the
    # marginal mean; growth/return series take a stressed constant, likewise anchored.
    # Anchoring on the mean rather than adding an increment to the last value is what a
    # supervisory scenario actually does ("unemployment reaches 10 percent", not "rises
    # by four points from wherever it is"), and it fixes a real defect: with an
    # increment, how adverse the scenario was in standardized units depended on where
    # the series happened to sit, so a series that started low could end barely above
    # its own in-time mean. Fundamental deterioration, so the default responds.
    stress = slice(_WARMUP + n_intime, total)
    last = _WARMUP + n_intime - 1
    if scenario is None:
        scen, band = "legacy", LEGACY_SEVERITY
    elif scenario == "rotate":
        scen = SCENARIO_NAMES[int(rng_struct.integers(len(SCENARIO_NAMES)))]
        band = SCENARIOS[scen]
    elif scenario in SCENARIOS:
        scen, band = scenario, SCENARIOS[scenario]
    else:
        raise ValueError(f"unknown scenario {scenario!r}; expected 'rotate', "
                         f"one of {SCENARIO_NAMES}, or None for the legacy range")
    severity = _uni(rng_struct, *band)
    ramp = np.arange(1, N_STRESS + 1) / N_STRESS
    level_target = {"unemployment": 1.2, "bbb_spread": 1.5, "vix": 1.5}
    growth_shift = {"gdp": -1.5, "hpi": -1.5, "cpi": -0.8, "nasdaq": -1.0}
    for n in CORE_NAMES:
        kind, m, s, phi, _ = CORE[n]
        if kind in ("level", "loglevel"):
            target = m + level_target[n] * s * severity
            fund[n][stress] = fund[n][last] + (target - fund[n][last]) * ramp
        else:
            fund[n][stress] = m + growth_shift[n] * s * severity

    # observed = fundamental + one-quarter transient crisis (in-time only, common shock)
    crisis = np.zeros(total)
    for t in range(_WARMUP, _WARMUP + n_intime):
        if rng_struct.random() < CRISIS_P:
            crisis[t] = 0.8 + 0.4 * rng_struct.random()
    obs = {}
    for n in CORE_NAMES:
        _, m, s, phi, load = CORE[n]
        obs[n] = fund[n] + load * s * crisis

    # equity siblings of NASDAQ (collinear distractors), on observed returns
    nas_ret = np.diff(np.log(_to_level("ret", obs["nasdaq"])), prepend=np.log(100.0))
    for name, (sm, ssd, corr) in SIBLINGS.items():
        eps_sib = rng_struct.standard_normal(total)
        r = corr * (nas_ret - nas_ret.mean()) / (nas_ret.std() + 1e-9) * ssd + np.sqrt(1 - corr**2) * ssd * eps_sib + sm
        obs[name] = r  # stored as return series; level built below

    # default rate from FUNDAMENTAL drivers (crisis does not propagate)
    pre_stress = slice(0, _WARMUP + n_intime)
    fund_levels = {n: _to_level(CORE[n][0], fund[n]) for n in CORE_NAMES}
    dr = _default_rate(dgp, fund_levels, pre_stress, rng_default)

    # observed levels for all nine macros
    levels = {}
    for n in CORE_NAMES:
        levels[n] = _to_level(CORE[n][0], obs[n])
    for name in SIBLINGS:
        levels[name] = _to_level("ret", obs[name])

    # oracle over the stress window: predictive distribution of dr from eps. Same
    # probit_mean call as the observed data, so the oracle cannot drift from the DGP.
    xs = list(range(_WARMUP + n_intime, total))
    lin = probit_mean(dgp, fund_levels, pre_stress)[stress]
    center = lin / np.sqrt(1.0 - dgp["rho"])
    scale = np.sqrt(dgp["rho"]) / np.sqrt(1.0 - dgp["rho"])
    points = []
    for j, t in enumerate(xs):
        mc = norm.cdf(center[j] + scale * rng_oracle.standard_normal(oracle_n))
        points.append({
            "quarter": t - _WARMUP + 1,
            "true_mean": float(norm.cdf(lin[j])),  # closed-form E[dr | macros]
            "mc_samples": [round(float(v), 6) for v in mc],
        })

    # ragged history: later-starting series are missing for the early quarters
    starts = {n: 0 for n in MACRO_COLUMNS}
    starts["bbb_spread"] = int(rng_struct.integers(4, 14))
    starts["hpi"] = int(rng_struct.integers(8, 18))
    starts["vix"] = int(rng_struct.integers(8, 18))
    starts["sp500"] = int(rng_struct.integers(20, 40))
    starts["djia"] = starts["sp500"]

    it0 = _WARMUP
    train_rows = []
    for q in range(n_intime):
        row = {"quarter": q + 1}
        for n in MACRO_COLUMNS:
            v = levels[n][it0 + q]
            row[n] = "" if q < starts[n] else round(float(v), 4)
        row["default_rate"] = round(float(dr[it0 + q]), 6)
        train_rows.append(row)

    scenario_rows = []
    for k in range(N_STRESS):
        t = _WARMUP + n_intime + k
        row = {"quarter": n_intime + 1 + k}
        for n in MACRO_COLUMNS:
            row[n] = round(float(levels[n][t]), 4)
        scenario_rows.append(row)

    return {
        "levels": levels,
        "default_rate": dr,
        "n_intime": n_intime,
        "intime_slice": slice(_WARMUP, _WARMUP + n_intime),
        "stress_slice": stress,
        "crisis": crisis,
        "points": points,
        "train_rows": train_rows,
        "scenario_rows": scenario_rows,
        "starts": starts,
        "seed": seed,
        "severity": severity,
        "scenario": scen,
        "dgp": dgp,
    }


def generate(seed: int, n_intime: int = 80, oracle_n: int = 2000,
             family: str | None = None, scenario: str | None = None) -> dict:
    """One instance. family/scenario default to a draw from the seed."""
    return _simulate(seed, n_intime, oracle_n, family, scenario)


# --- serialization ---------------------------------------------------------

_TRAIN_COLS = ["quarter", *MACRO_COLUMNS, "default_rate"]
_SCENARIO_COLS = ["quarter", *MACRO_COLUMNS]


def _csv_text(cols, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def train_csv_text(bundle):
    return _csv_text(_TRAIN_COLS, bundle["train_rows"])


def scenario_csv_text(bundle):
    return _csv_text(_SCENARIO_COLS, bundle["scenario_rows"])


def build_truth(bundle):
    # Realized severity, so a published cell can be conditioned on how adverse its
    # scenario actually was. `severity` is the drawn multiplier; these are what it came
    # out as. Scenario severity varies by design and some scenarios are benign, exactly
    # as CCAR runs a baseline alongside its adverse ones, so it is a factor to record
    # rather than a defect to remove.
    it, st = bundle["intime_slice"], bundle["stress_slice"]
    excursion, left_range = {}, 0
    for m in MACRO_COLUMNS:
        lv = bundle["levels"][m]
        ref = lv[it]
        z = (lv[st] - ref.mean()) / (ref.std() or 1.0)
        excursion[m] = round(float(np.max(np.abs(z))), 3)
        if lv[st].max() > ref.max() or lv[st].min() < ref.min():
            left_range += 1
    return {
        "meta": {"seed": bundle["seed"], "n_intime": bundle["n_intime"],
                 "severity": bundle["severity"], "scenario": bundle["scenario"],
                 "starts": bundle["starts"],
                 "max_driver_excursion_sd": excursion,
                 "n_macros_leaving_intime_range": left_range,
                 # Recorded so a published result is auditable after the fact. It
                 # never enters the agent's sandbox; only train.csv and scenario.csv do.
                 "dgp": bundle["dgp"]},
        "points": bundle["points"],
    }


def truth_to_points(truth):
    return [
        {"key": (float(p["quarter"]),), "class": None,
         "true_mean": p["true_mean"], "mc": np.asarray(p["mc_samples"], dtype=float)}
        for p in truth["points"]
    ]


def write_outputs(bundle, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "train.csv").write_text(train_csv_text(bundle))
    (out_dir / "scenario.csv").write_text(scenario_csv_text(bundle))
    with (out_dir / "truth.json").open("w") as f:
        json.dump(build_truth(bundle), f, indent=2)


def main():
    ap = argparse.ArgumentParser(description="Generate a perEval CCAR stress-loss task instance.")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--n-intime", type=int, default=80)
    ap.add_argument("--oracle-n", type=int, default=2000)
    ap.add_argument("--family", choices=FAMILIES, default=None,
                    help="pin the response family; default draws one from the seed")
    args = ap.parse_args()
    seed = args.seed if args.seed is not None else int(np.random.SeedSequence().generate_state(1)[0])
    bundle = generate(seed=seed, n_intime=args.n_intime, oracle_n=args.oracle_n, family=args.family)
    write_outputs(bundle, args.out_dir)
    d = bundle["dgp"]
    print(f"seed={seed} n_intime={args.n_intime} severity={bundle['severity']:.2f}")
    print(f"dgp: family={d['family']} drivers={d['d1']} (level), {d['d2']} (YoY) "
          f"p={d['p']:.4f} rho={d['rho']:.4f} k1={d['k1']:.4f} k2={d['k2']:.4f}"
          + (f" kink_q={d['thresh_q']:.2f} extra={d['thresh_extra']:.3f}"
             if d["family"] == "threshold" else "")
          + (f" k3={d['inter_k3']:.4f}" if d["family"] == "interaction" else ""))
    print("stress default means: " + " ".join(f"{p['true_mean']*100:.1f}" for p in bundle["points"]))


if __name__ == "__main__":
    main()
