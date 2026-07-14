"""Orbital angle task generators (two-body and three-body).

Two-body: a planet on a fixed elliptical (Keplerian) orbit around a star. Once
per day the angle alpha (degrees, in the orbital plane) between the direction to
the star and a fixed distant-star reference is recorded, for a run of consecutive
days covering several orbits. The agent predicts alpha at future days. Because
the signal is strictly periodic, this is the easier task: the structure is a
repeating pattern to identify, not an open-ended extrapolation.

Three-body: a second, slower planet (Mars-like) is added, with its own angle
beta. Masses are negligible, so the two planets do not interact and each follows
an independent Keplerian orbit; "three-body" refers only to the observed
configuration. The agent is given t, alpha, and beta and must predict beta at
future days. This is the harder task: beta belongs to the outer planet, which
completes fewer orbits in the observation window (so its period and shape are
less constrained), and alpha is an independent distractor that must be recognized
as irrelevant to beta rather than used as a spurious predictor.

Only P (period), e (eccentricity), the orbit orientation, and the time of
periapsis affect the observed angle; the orbit size and the star mass do not, so
they are not modeled. The angular motion follows Kepler's second law (fast near
periapsis, slow near apoapsis), which is what a naive elliptical-orbit fit
recovers. Measurement noise is added to the recorded angles.

Ground truth is owned by construction (the exact Keplerian angle and the noise
law are known), so the scorer's Monte-Carlo oracle is exact. The angle is a
circular target (period 360), scored with pereval.scorers.interval at period=360.

Outputs (train.csv / test.csv given to the agent, truth.json scorer-only) mirror
the ballistic task. No new dependency: Kepler's equation is solved with Newton
iteration in numpy.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

import numpy as np

_NEWTON_ITERS = 60


def _kepler_longitude(t, P: float, e: float, omega_deg: float, t0: float) -> np.ndarray:
    """Heliocentric longitude (degrees, mod 360) at times t for a Keplerian orbit."""
    t = np.asarray(t, dtype=float)
    M = 2.0 * np.pi * (t - t0) / P  # mean anomaly
    E = M.copy()
    for _ in range(_NEWTON_ITERS):
        E = E - (E - e * np.sin(E) - M) / (1.0 - e * np.cos(E))
    nu = 2.0 * np.arctan2(np.sqrt(1.0 + e) * np.sin(E / 2.0), np.sqrt(1.0 - e) * np.cos(E / 2.0))
    theta = np.radians(omega_deg) + nu
    return np.degrees(theta) % 360.0


def _uni(rng, lo, hi):
    return float(rng.uniform(lo, hi))


def _draw_orbit(rng, p_range, e_range) -> dict:
    return {
        "P": _uni(rng, *p_range),
        "e": _uni(rng, *e_range),
        "omega_deg": _uni(rng, 0.0, 360.0),
        # t0 set after P is known
    }


def _future_days(total_days: int, horizon_days: float, k: int) -> list[int]:
    raw = np.linspace(total_days + 1, total_days + horizon_days, k)
    days = sorted(set(int(round(d)) for d in raw))
    return [d for d in days if d > total_days]


def _oracle_points(rng_oracle, planets: list[dict], target_key: str, test_days: list[int],
                   noise_sd: float, oracle_n: int) -> list[dict]:
    target = next(pl for pl in planets if pl["key"] == target_key)
    points = []
    for d in test_days:
        true = float(_kepler_longitude(d, target["P"], target["e"], target["omega_deg"], target["t0"]))
        mc = (true + rng_oracle.normal(0.0, noise_sd, oracle_n)) % 360.0
        points.append(
            {"t": float(d), "true_mean": true, "mc_samples": [round(float(v), 4) for v in mc]}
        )
    return points


def _generate(seed: int, two_body: bool, noise_sd: float | None, oracle_n: int) -> dict:
    ss = np.random.SeedSequence(seed)
    rng_struct, rng_noise, rng_oracle = (np.random.default_rng(s) for s in ss.spawn(3))

    inner = _draw_orbit(rng_struct, (300.0, 450.0), (0.2, 0.4))
    inner["t0"] = _uni(rng_struct, 0.0, inner["P"])
    inner["key"] = "alpha"
    planets = [inner]
    if not two_body:
        outer = _draw_orbit(rng_struct, (650.0, 950.0), (0.2, 0.4))
        outer["t0"] = _uni(rng_struct, 0.0, outer["P"])
        outer["key"] = "beta"
        planets.append(outer)

    sd = _uni(rng_struct, 0.2, 1.0) if noise_sd is None else noise_sd

    # The window covers several orbits of the TARGET planet. For three-body the
    # target is the slow outer planet, observed for only a few orbits (its period
    # and shape are less constrained), while the inner planet alpha is observed
    # many times over as an irrelevant distractor. The prediction horizon is also
    # longer for three-body, so accumulated period error bites harder.
    target = inner if two_body else planets[1]
    if two_body:
        n_orbits_target = _uni(rng_struct, 4.0, 8.0)
        horizon_factor = 1.2
    else:
        n_orbits_target = _uni(rng_struct, 2.5, 3.5)
        horizon_factor = 1.5
    total_days = int(round(n_orbits_target * target["P"]))
    train_t = np.arange(0, total_days, dtype=float)

    # Agent-visible training rows, with measurement noise on each recorded angle.
    cols = {}
    for pl in planets:
        true = _kepler_longitude(train_t, pl["P"], pl["e"], pl["omega_deg"], pl["t0"])
        cols[pl["key"]] = (true + rng_noise.normal(0.0, sd, len(train_t))) % 360.0

    if two_body:
        header = ["t", "alpha"]
        train_rows = [(int(t), round(float(cols["alpha"][i]), 4)) for i, t in enumerate(train_t)]
    else:
        header = ["t", "alpha", "beta"]
        train_rows = [
            (int(t), round(float(cols["alpha"][i]), 4), round(float(cols["beta"][i]), 4))
            for i, t in enumerate(train_t)
        ]
    target_key = target["key"]
    test_days = _future_days(total_days, horizon_factor * target["P"], 10)
    points = _oracle_points(rng_oracle, planets, target_key, test_days, sd, oracle_n)

    meta = {
        "seed": seed,
        "regenerable": True,
        "task": "twobody" if two_body else "threebody",
        "oracle_n": oracle_n,
        "noise_sd_deg": round(sd, 4),
        "target": target_key,
        "total_days": total_days,
        "orbits": {pl["key"]: {k: round(pl[k], 4) for k in ("P", "e", "omega_deg", "t0")} for pl in planets},
    }
    return {
        "meta": meta,
        "header": header,
        "train_rows": train_rows,
        "test_days": test_days,
        "points": points,
    }


def generate_twobody(seed: int, noise_sd: float | None = None, oracle_n: int = 2000) -> dict:
    return _generate(seed, two_body=True, noise_sd=noise_sd, oracle_n=oracle_n)


def generate_threebody(seed: int, noise_sd: float | None = None, oracle_n: int = 2000) -> dict:
    return _generate(seed, two_body=False, noise_sd=noise_sd, oracle_n=oracle_n)


# --- serialization (shared with the Inspect task and the CLI) --------------

def _csv_text(header, rows) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def train_csv_text(bundle: dict) -> str:
    return _csv_text(bundle["header"], bundle["train_rows"])


def test_csv_text(bundle: dict) -> str:
    return _csv_text(["t"], [(d,) for d in bundle["test_days"]])


def build_truth(bundle: dict) -> dict:
    return {"meta": bundle["meta"], "points": bundle["points"]}


def truth_to_points(truth: dict) -> list[dict]:
    """Adapt stored truth to the scorer's point list (key by t, no class)."""
    return [
        {
            "key": (float(p["t"]),),
            "class": None,
            "true_mean": p["true_mean"],
            "mc": np.asarray(p["mc_samples"], dtype=float),
        }
        for p in truth["points"]
    ]


def write_outputs(bundle: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "train.csv").write_text(train_csv_text(bundle))
    (out_dir / "test.csv").write_text(test_csv_text(bundle))
    with (out_dir / "truth.json").open("w") as f:
        json.dump(build_truth(bundle), f, indent=2)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate a perEval orbital-angle task instance.")
    ap.add_argument("--task", choices=["twobody", "threebody"], required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--noise-sd", type=float, default=None, help="pin measurement noise SD (deg); default randomized")
    ap.add_argument("--oracle-n", type=int, default=2000)
    args = ap.parse_args()

    seed = args.seed if args.seed is not None else int(np.random.SeedSequence().generate_state(1)[0])
    gen = generate_twobody if args.task == "twobody" else generate_threebody
    bundle = gen(seed=seed, noise_sd=args.noise_sd, oracle_n=args.oracle_n)
    write_outputs(bundle, args.out_dir)

    m = bundle["meta"]
    print(f"task={m['task']} seed={seed} noise_sd={m['noise_sd_deg']} deg target={m['target']}")
    print(f"train days=0..{m['total_days'] - 1} ({len(bundle['train_rows'])} rows), test points={len(bundle['test_days'])}")
    for k, o in m["orbits"].items():
        print(f"  {k}: P={o['P']:.1f} d  e={o['e']:.3f}  orbits_in_window={m['total_days'] / o['P']:.1f}")


if __name__ == "__main__":
    main()
