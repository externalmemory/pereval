"""Ballistic trajectory task generator for perEval.

The agent receives a training CSV of (category, x, y) rows, where y is the
vertical impact coordinate in meters of a projectile at horizontal distance x in
meters, and must predict y with 95% intervals for a held-out set of longer
distances. Ground truth is owned by construction: each opaque category is a
projectile class (rifle or pistol) with per-run randomized ballistic parameters,
and y is produced by the py-ballisticcalc point-mass simulator (LGPL-3.0) with
Gaussian noise injected into muzzle velocity and launch angle.

The held-out distances lie beyond the training range, so a model that fits the
training shape and extrapolates it (a polynomial, or a non-extrapolating tree
ensemble) misses the drag-driven curvature. For rifle categories the held-out
window is kept supersonic (Mach > 1.2), so the trap does not depend on any
transonic effect; it is pure velocity-dependent drag.

"Regenerable" means every run redraws the per-category ballistic truth, the noise
levels, and all per-shot noise from a single seed. A fixed seed reproduces a run
exactly (to isolate the effect of model temperature); noise levels can be pinned
independently of the seed via --angle-sd-moa and --mv-sd-pct.

Outputs (written to --out-dir):
  train.csv   columns category,x,y     given to the agent
  test.csv    columns category,x       given to the agent (predict y + 95% CI)
  truth.json  scorer-only: seed, noise levels, per-category true parameters, and
              a Monte-Carlo oracle (true mean and predictive distribution) at
              each held-out point.

Category identifiers are random alphanumerics beginning with a letter, so the
field reads as categorical in a typeless CSV and an agent cannot invert the label
to recover the real projectile/load and look up or re-simulate its ballistics.
The noise model is independent-per-row: every training row is its own shot with
its own muzzle-velocity and angle draw, so observations are conditionally i.i.d.
given (category, x).

Noise injection helps only point estimates, not intervals: the agent is never
told the noise magnitude, so calibrated intervals must be estimated from the data.
"""

from __future__ import annotations

import argparse
import csv
import json
import string
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from py_ballisticcalc import (
    Ammo,
    Angular,
    Calculator,
    Distance,
    DragModel,
    Shot,
    TableG1,
    Unit,
    Weapon,
    loadMetricUnits,
)

loadMetricUnits()

WEAPON = Weapon(sight_height=Unit.Centimeter(5), zero_elevation=Angular.Degree(0))
CALC = Calculator()


@dataclass(frozen=True)
class ClassSpec:
    name: str
    n_categories: int
    mv_range_mps: tuple[float, float]
    bc_range_g1: tuple[float, float]
    weight_range_g: tuple[float, float]
    diameter_range_mm: tuple[float, float]
    train_max_m: float
    test_min_m: float
    test_max_m: float
    train_step_m: float
    test_step_m: float
    replicate_range: tuple[int, int]
    angle_sd_moa_range: tuple[float, float]
    mv_sd_pct_range: tuple[float, float]
    min_test_mach: float | None  # rifle: stay supersonic with margin
    max_muzzle_mach: float | None  # pistol: subsonic from the muzzle


RIFLE = ClassSpec(
    name="rifle",
    n_categories=3,
    mv_range_mps=(790.0, 940.0),
    bc_range_g1=(0.42, 0.58),
    weight_range_g=(7.0, 13.0),
    diameter_range_mm=(5.5, 8.0),
    train_max_m=400.0,
    test_min_m=500.0,
    test_max_m=800.0,
    train_step_m=25.0,
    test_step_m=50.0,
    replicate_range=(1, 7),
    angle_sd_moa_range=(0.5, 1.5),
    mv_sd_pct_range=(0.3, 0.8),
    min_test_mach=1.2,
    max_muzzle_mach=None,
)

PISTOL = ClassSpec(
    name="pistol",
    n_categories=2,
    mv_range_mps=(280.0, 330.0),
    bc_range_g1=(0.12, 0.22),
    weight_range_g=(7.0, 15.0),
    diameter_range_mm=(9.0, 11.5),
    train_max_m=100.0,
    test_min_m=125.0,
    test_max_m=200.0,
    train_step_m=25.0,
    test_step_m=25.0,
    replicate_range=(1, 7),
    angle_sd_moa_range=(2.5, 7.5),  # 5x the rifle range
    mv_sd_pct_range=(0.7, 1.7),
    min_test_mach=None,
    max_muzzle_mach=1.0,
)

CLASSES = (RIFLE, PISTOL)
_REJECTION_LIMIT = 500
_STEP_M = 25.0
_FIRE_MARGIN_M = 60.0  # > 2 * _STEP_M, so the deepest read distance is strictly interior


def _uni(rng: np.random.Generator, lo: float, hi: float) -> float:
    return float(rng.uniform(lo, hi))


def _grid(step: float, lo: float, hi: float) -> list[float]:
    n = int(round((hi - lo) / step))
    return [round(lo + i * step, 6) for i in range(n + 1)]


def _make_id(rng: np.random.Generator, taken: set[str]) -> str:
    first = string.ascii_uppercase
    rest = string.ascii_letters + string.digits
    while True:
        cid = rng.choice(list(first)) + "".join(rng.choice(list(rest), size=5))
        if cid not in taken:
            taken.add(cid)
            return cid


def _drag(bc: float, weight_g: float, diameter_mm: float) -> DragModel:
    return DragModel(
        bc, TableG1, weight=Unit.Gram(weight_g), diameter=Unit.Millimeter(diameter_mm)
    )


def _fire(dm: DragModel, mv_mps: float, angle_moa: float, read_to_m: float):
    """Fire past read_to_m by a margin so read_to_m is interior to the interpolant."""
    ammo = Ammo(dm, mv=Unit.MPS(mv_mps))
    shot = Shot(weapon=WEAPON, ammo=ammo, relative_angle=Angular.MOA(angle_moa))
    return CALC.fire(
        shot,
        trajectory_range=Distance.Meter(read_to_m + _FIRE_MARGIN_M),
        trajectory_step=Distance.Meter(_STEP_M),
        dense_output=True,
        raise_range_error=False,
    )


def _y_at(result, x_m: float) -> float:
    return result.get_at("distance", Distance.Meter(x_m)).height >> Unit.Meter


def _mach_at(result, x_m: float) -> float:
    return result.get_at("distance", Distance.Meter(x_m)).mach


def _draw_category(rng: np.random.Generator, spec: ClassSpec) -> dict:
    """Rejection-sample ballistic parameters until the regime constraint holds."""
    for _ in range(_REJECTION_LIMIT):
        mv = _uni(rng, *spec.mv_range_mps)
        bc = _uni(rng, *spec.bc_range_g1)
        weight = _uni(rng, *spec.weight_range_g)
        diameter = _uni(rng, *spec.diameter_range_mm)
        dm = _drag(bc, weight, diameter)
        nominal = _fire(dm, mv, 0.0, spec.test_max_m)
        if spec.min_test_mach is not None:
            if _mach_at(nominal, spec.test_max_m) <= spec.min_test_mach:
                continue
        if spec.max_muzzle_mach is not None:
            if _mach_at(nominal, 1.0) >= spec.max_muzzle_mach:
                continue
        return {
            "class": spec.name,
            "nominal_mv_mps": round(mv, 3),
            "bc_g1": round(bc, 4),
            "weight_g": round(weight, 3),
            "diameter_mm": round(diameter, 3),
            "test_max_mach": round(_mach_at(nominal, spec.test_max_m), 3),
            "_dm": dm,
        }
    raise RuntimeError(f"could not satisfy {spec.name} regime constraint in {_REJECTION_LIMIT} draws")


def generate(
    seed: int,
    angle_sd_moa: float | None = None,
    mv_sd_pct: float | None = None,
    oracle_n: int = 2000,
) -> dict:
    ss = np.random.SeedSequence(seed)
    rng_struct, rng_noise, rng_oracle = (np.random.default_rng(s) for s in ss.spawn(3))

    # Noise levels are always drawn (so RNG consumption is stable), then overridden.
    noise_levels = {}
    for spec in CLASSES:
        noise_levels[spec.name] = {
            "angle_sd_moa": _uni(rng_struct, *spec.angle_sd_moa_range),
            "mv_sd_pct": _uni(rng_struct, *spec.mv_sd_pct_range),
        }
    if angle_sd_moa is not None:
        noise_levels["rifle"]["angle_sd_moa"] = angle_sd_moa
        noise_levels["pistol"]["angle_sd_moa"] = 5.0 * angle_sd_moa
    if mv_sd_pct is not None:
        noise_levels["rifle"]["mv_sd_pct"] = mv_sd_pct
        noise_levels["pistol"]["mv_sd_pct"] = mv_sd_pct

    taken: set[str] = set()
    categories: dict[str, dict] = {}
    for spec in CLASSES:
        for _ in range(spec.n_categories):
            params = _draw_category(rng_struct, spec)
            cid = _make_id(rng_struct, taken)
            nl = noise_levels[spec.name]
            params["angle_sd_moa"] = round(nl["angle_sd_moa"], 4)
            params["mv_sd_mps"] = round(nl["mv_sd_pct"] / 100.0 * params["nominal_mv_mps"], 4)
            params["n_replicates"] = int(rng_struct.integers(spec.replicate_range[0], spec.replicate_range[1] + 1))
            params["_spec"] = spec
            categories[cid] = params

    train_rows: list[tuple[str, float, float]] = []
    for cid, p in categories.items():
        spec: ClassSpec = p["_spec"]
        dm: DragModel = p["_dm"]
        for x in _grid(spec.train_step_m, spec.train_step_m, spec.train_max_m):
            for _ in range(p["n_replicates"]):
                mv = p["nominal_mv_mps"] + rng_noise.normal(0.0, p["mv_sd_mps"])
                angle = rng_noise.normal(0.0, p["angle_sd_moa"])
                y = _y_at(_fire(dm, mv, angle, x), x)
                train_rows.append((cid, x, round(y, 4)))
    train_rows.sort(key=lambda r: (r[0], r[1]))

    test_index: list[tuple[str, float]] = []
    for cid, p in categories.items():
        spec = p["_spec"]
        for x in _grid(spec.test_step_m, spec.test_min_m, spec.test_max_m):
            test_index.append((cid, x))
    test_index.sort()

    # Oracle: per category fire oracle_n independent shots to test_max and read the
    # predictive marginal of y at each held-out x. Marginals are correct even though
    # readings within one shot are correlated.
    oracle: dict[tuple[str, float], dict] = {}
    for cid, p in categories.items():
        spec = p["_spec"]
        dm = p["_dm"]
        xs = _grid(spec.test_step_m, spec.test_min_m, spec.test_max_m)
        samples = np.empty((oracle_n, len(xs)))
        for i in range(oracle_n):
            mv = p["nominal_mv_mps"] + rng_oracle.normal(0.0, p["mv_sd_mps"])
            angle = rng_oracle.normal(0.0, p["angle_sd_moa"])
            res = _fire(dm, mv, angle, spec.test_max_m)
            for j, x in enumerate(xs):
                samples[i, j] = _y_at(res, x)
        for j, x in enumerate(xs):
            col = np.sort(samples[:, j])
            mean = float(col.mean())
            oracle[(cid, x)] = {
                "true_mean_y_m": round(mean, 5),
                "predictive_pi95_m": [round(float(np.quantile(col, 0.025)), 5),
                                      round(float(np.quantile(col, 0.975)), 5)],
                "irreducible_mae_m": round(float(np.abs(col - mean).mean()), 5),
                "mc_samples_m": [round(float(v), 4) for v in col],
            }

    return {
        "meta": {
            "seed": seed,
            "regenerable": True,
            "oracle_n": oracle_n,
            "noise_levels": {
                k: {"angle_sd_moa": round(v["angle_sd_moa"], 4), "mv_sd_pct": round(v["mv_sd_pct"], 4)}
                for k, v in noise_levels.items()
            },
        },
        "categories": {
            cid: {k: v for k, v in p.items() if not k.startswith("_")}
            for cid, p in categories.items()
        },
        "train_rows": train_rows,
        "test_index": test_index,
        "oracle": oracle,
    }


def write_outputs(bundle: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "train.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category", "x", "y"])
        w.writerows(bundle["train_rows"])

    with (out_dir / "test.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category", "x"])
        w.writerows(bundle["test_index"])

    truth = {
        "meta": bundle["meta"],
        "categories": bundle["categories"],
        "test": [
            {"category": cid, "x_m": x, **bundle["oracle"][(cid, x)]}
            for (cid, x) in bundle["test_index"]
        ],
    }
    with (out_dir / "truth.json").open("w") as f:
        json.dump(truth, f, indent=2)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate a perEval ballistic trajectory task instance.")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=None, help="fix for exact reproducibility; default draws from OS entropy")
    ap.add_argument("--angle-sd-moa", type=float, default=None, help="pin rifle launch-angle SD (pistol = 5x); default randomized per run")
    ap.add_argument("--mv-sd-pct", type=float, default=None, help="pin muzzle-velocity SD as %% of nominal for both classes; default randomized")
    ap.add_argument("--oracle-n", type=int, default=2000, help="Monte-Carlo draws per held-out point")
    args = ap.parse_args()

    seed = args.seed if args.seed is not None else int(np.random.SeedSequence().generate_state(1)[0])
    bundle = generate(seed=seed, angle_sd_moa=args.angle_sd_moa, mv_sd_pct=args.mv_sd_pct, oracle_n=args.oracle_n)
    write_outputs(bundle, args.out_dir)

    meta = bundle["meta"]
    print(f"seed={seed}  oracle_n={meta['oracle_n']}")
    print(f"noise levels: {meta['noise_levels']}")
    print(f"{len(bundle['train_rows'])} train rows, {len(bundle['test_index'])} test points, {len(bundle['categories'])} categories")
    for cid, p in bundle["categories"].items():
        tail = f"test_max_mach={p['test_max_mach']}" if p["class"] == "rifle" else ""
        print(f"  {cid}  {p['class']:6s} mv={p['nominal_mv_mps']:.0f} bc={p['bc_g1']} reps={p['n_replicates']} {tail}")


if __name__ == "__main__":
    main()
