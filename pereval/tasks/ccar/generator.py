"""CCAR-style stress loss task generator.

The agent gets a quarterly panel of nine macroeconomic drivers plus a portfolio
default rate over an in-time window, and a 9-quarter forward stress scenario for
the same nine drivers, and must project the default rate (point plus 95% interval)
for the nine stressed quarters. It is the realistic analog of the toy tasks: the
in-time fit is easy to overfit, and the stressed out-of-time path (drivers pushed
beyond the observed range) is where a sound model separates from a fragile one.

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

- Default rate: extended-Vasicek, dr = Phi((Phi^-1(p) + k1*u1 + k2*u2 +
  sqrt(rho)*eps)/sqrt(1-rho)), with u1 = standardized unemployment level, u2 =
  standardized YoY change in HPI, p=0.028, rho=0.02, k1=0.13, k2=-0.07, eps ~ N(0,1)
  i.i.d. Crucially the default uses the FUNDAMENTAL (pre-crisis) drivers, so a COVID
  unemployment spike appears in the data but the default rate does not follow it;
  only persistent moves in the fundamental drive defaults. The other seven macros
  are correlated distractors.

- Stress scenario: the 9 out-of-time quarters apply a sustained recession drift to
  the FUNDAMENTAL (unemployment up, HPI down, and the rest co-moving), pushing the
  drivers past the in-time range, so the default rate rises. Unlike the transient
  crisis, this is a real deterioration and the default responds. A model that
  attenuated its unemployment sensitivity to fit the COVID quarter, or flipped a
  sign under collinearity, will misproject here and pay for it in Winkler regret.

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

# extended-Vasicek default parameters and predictor standardization (from FRED / vasicekfit)
P, RHO, K1, K2 = 0.028, 0.02, 0.13, -0.07
U_MEAN, U_SD = 5.66, 1.72  # unemployment raw-level standardization
YM, YS = 0.0442, 0.0580  # HPI YoY standardization

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


def _default_rate(unemp_level, hpi_level, rng):
    u1 = (unemp_level - U_MEAN) / U_SD
    u2 = (_hpi_yoy(hpi_level) - YM) / YS
    eps = rng.standard_normal(len(unemp_level))
    z = (norm.ppf(P) + K1 * u1 + K2 * u2 + np.sqrt(RHO) * eps) / np.sqrt(1.0 - RHO)
    return norm.cdf(z)


def _simulate(seed: int, n_intime: int, oracle_n: int) -> dict:
    ss = np.random.SeedSequence(seed)
    rng_struct, rng_default, rng_oracle = (np.random.default_rng(s) for s in ss.spawn(3))

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

    # sustained recession over the stress window (deterministic scenario overlay):
    # level series ramp from the last in-time value; growth/return series take a
    # stressed constant. Fundamental deterioration, so the default responds.
    stress = slice(_WARMUP + n_intime, total)
    last = _WARMUP + n_intime - 1
    severity = _uni(rng_struct, 1.0, 1.8)
    ramp = np.arange(1, N_STRESS + 1) / N_STRESS
    level_target = {"unemployment": 1.2, "bbb_spread": 1.5, "vix": 1.5}
    growth_shift = {"gdp": -1.5, "hpi": -1.5, "cpi": -0.8, "nasdaq": -1.0}
    for n in CORE_NAMES:
        kind, m, s, phi, _ = CORE[n]
        if kind in ("level", "loglevel"):
            fund[n][stress] = fund[n][last] + level_target[n] * s * severity * ramp
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
    unemp_fund_level = _to_level("loglevel", fund["unemployment"])
    hpi_fund_level = _to_level("growth", fund["hpi"])
    dr = _default_rate(unemp_fund_level, hpi_fund_level, rng_default)

    # observed levels for all nine macros
    levels = {}
    for n in CORE_NAMES:
        levels[n] = _to_level(CORE[n][0], obs[n])
    for name in SIBLINGS:
        levels[name] = _to_level("ret", obs[name])

    # oracle over the stress window: predictive distribution of dr from eps
    xs = list(range(_WARMUP + n_intime, total))
    u1_s = (unemp_fund_level[stress] - U_MEAN) / U_SD
    u2_s = (_hpi_yoy(hpi_fund_level)[stress] - YM) / YS
    lin = norm.ppf(P) + K1 * u1_s + K2 * u2_s  # macro part on the probit scale
    center = lin / np.sqrt(1.0 - RHO)
    scale = np.sqrt(RHO) / np.sqrt(1.0 - RHO)
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
    }


def generate(seed: int, n_intime: int = 80, oracle_n: int = 2000) -> dict:
    return _simulate(seed, n_intime, oracle_n)


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
    return {
        "meta": {"seed": bundle["seed"], "n_intime": bundle["n_intime"],
                 "severity": bundle["severity"], "starts": bundle["starts"]},
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
    args = ap.parse_args()
    seed = args.seed if args.seed is not None else int(np.random.SeedSequence().generate_state(1)[0])
    bundle = generate(seed=seed, n_intime=args.n_intime, oracle_n=args.oracle_n)
    write_outputs(bundle, args.out_dir)
    print(f"seed={seed} n_intime={args.n_intime} severity={bundle['severity']:.2f}")
    print("stress default means: " + " ".join(f"{p['true_mean']*100:.1f}" for p in bundle["points"]))


if __name__ == "__main__":
    main()
