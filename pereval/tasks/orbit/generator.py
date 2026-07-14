"""Orbital angle task generators (two-body and three-body).

Two-body: a planet on a fixed elliptical (Keplerian) orbit around a star. Once
per day the angle alpha (degrees, in the orbital plane) between the direction to
the star and a fixed distant-star reference is recorded, for a run of consecutive
days covering several orbits. The agent predicts alpha at future days. Because
the signal is strictly periodic, this is the easier task: the structure is a
repeating pattern to identify, not an open-ended extrapolation.

Three-body: a second, slower outer planet is added. The observer stays on the
inner planet and also records beta, the angle to the outer planet. Masses are
negligible, so each planet follows its own Keplerian orbit; "three-body" refers
only to the observed configuration. beta is the APPARENT direction to the outer
planet as seen from the inner one (the angle of the vector between them), so it
depends on both planets' positions and shows retrograde motion, like Mars seen
from Earth. The agent is given t, alpha, and beta and must predict beta at future
days. This is the harder task: beta is not a simple Keplerian angle but a coupled,
retrograde, synodic-period signal, and alpha is essential rather than a
distractor, since it pins the observer's (inner planet's) position, which is half
the geometry needed to reconstruct beta.

For alpha, only P (period), e (eccentricity), orientation, and periapsis time
matter; the orbit size and star mass do not, since the direction to the star is
radius-independent. For beta the size ratio matters too, but it is fixed by the
period ratio through Kepler's third law, so still nothing external is needed.
Angular motion follows Kepler's second law (fast near periapsis, slow near
apoapsis). Measurement noise is added to the recorded angles.

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


def _orbit_state(t, P: float, e: float, omega_deg: float, t0: float, a: float):
    """Heliocentric longitude (radians) and radius at times t for a Keplerian orbit."""
    t = np.asarray(t, dtype=float)
    M = 2.0 * np.pi * (t - t0) / P  # mean anomaly
    E = M.copy()
    for _ in range(_NEWTON_ITERS):
        E = E - (E - e * np.sin(E) - M) / (1.0 - e * np.cos(E))
    nu = 2.0 * np.arctan2(np.sqrt(1.0 + e) * np.sin(E / 2.0), np.sqrt(1.0 - e) * np.cos(E / 2.0))
    theta = np.radians(omega_deg) + nu
    r = a * (1.0 - e * np.cos(E))
    return theta, r


def _kepler_longitude(t, P: float, e: float, omega_deg: float, t0: float) -> np.ndarray:
    """Heliocentric longitude (degrees, mod 360). Direction to the star from the
    planet is this plus 180; the constant is absorbed into the random orientation.
    Radius-independent, which is why alpha does not need the orbit size."""
    theta, _ = _orbit_state(t, P, e, omega_deg, t0, 1.0)
    return np.degrees(theta) % 360.0


def _apparent_longitude(t, inner: dict, outer: dict) -> np.ndarray:
    """Apparent longitude (degrees, mod 360) of the outer planet as seen from the
    inner planet: the angle of the vector (r_outer - r_inner). This depends on both
    planets' positions, so it is coupled to the inner planet's phase (alpha) and
    shows retrograde motion. Only the size ratio matters, fixed by Kepler's third
    law from the period ratio (a_inner = 1, a_outer = (P_outer/P_inner)^(2/3))."""
    a_outer = (outer["P"] / inner["P"]) ** (2.0 / 3.0)
    th1, r1 = _orbit_state(t, inner["P"], inner["e"], inner["omega_deg"], inner["t0"], 1.0)
    th2, r2 = _orbit_state(t, outer["P"], outer["e"], outer["omega_deg"], outer["t0"], a_outer)
    dx = r2 * np.cos(th2) - r1 * np.cos(th1)
    dy = r2 * np.sin(th2) - r1 * np.sin(th1)
    return np.degrees(np.arctan2(dy, dx)) % 360.0


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


def _oracle_points(rng_oracle, target_true_fn, test_days: list[int],
                   noise_sd: float, oracle_n: int) -> list[dict]:
    points = []
    for d in test_days:
        true = float(target_true_fn(np.array([float(d)]))[0])
        mc = (true + rng_oracle.normal(0.0, noise_sd, oracle_n)) % 360.0
        points.append(
            {"t": float(d), "true_mean": true, "mc_samples": [round(float(v), 4) for v in mc]}
        )
    return points


def _generate(seed: int, two_body: bool, noise_sd: float | None, oracle_n: int) -> dict:
    ss = np.random.SeedSequence(seed)
    rng_struct, rng_noise, rng_oracle = (np.random.default_rng(s) for s in ss.spawn(3))

    inner = _draw_orbit(rng_struct, (300.0, 450.0), (0.15, 0.35))
    inner["t0"] = _uni(rng_struct, 0.0, inner["P"])
    inner["key"] = "alpha"
    planets = [inner]
    if not two_body:
        # Draw the outer planet with a clear radial gap outside the inner orbit, so
        # the orbits do not cross and the apparent angle stays well sampled daily.
        for _ in range(500):
            outer = _draw_orbit(rng_struct, (1000.0, 1800.0), (0.05, 0.25))
            a_outer = (outer["P"] / inner["P"]) ** (2.0 / 3.0)
            if a_outer * (1.0 - outer["e"]) > (1.0 + inner["e"]) * 1.15:
                break
        outer["t0"] = _uni(rng_struct, 0.0, outer["P"])
        outer["key"] = "beta"
        planets.append(outer)

    sd = _uni(rng_struct, 0.2, 1.0) if noise_sd is None else noise_sd

    # alpha is the inner planet's heliocentric longitude; for three-body beta is the
    # apparent longitude of the outer planet as seen from the inner one, which is
    # coupled to alpha and shows retrograde motion. The window covers several orbits
    # of the target planet (the slow outer planet for three-body, so beta is observed
    # over only a few orbits), with a longer prediction horizon for three-body.
    if two_body:
        target_true_fn = lambda tt: _kepler_longitude(tt, inner["P"], inner["e"], inner["omega_deg"], inner["t0"])  # noqa: E731
        target_key = "alpha"
        target_period = inner["P"]
        n_orbits_target = _uni(rng_struct, 4.0, 8.0)
        horizon_factor = 1.2
    else:
        target_true_fn = lambda tt: _apparent_longitude(tt, inner, outer)  # noqa: E731
        target_key = "beta"
        target_period = outer["P"]
        n_orbits_target = _uni(rng_struct, 2.5, 3.5)
        horizon_factor = 1.5
    total_days = int(round(n_orbits_target * target_period))
    train_t = np.arange(0, total_days, dtype=float)

    # Agent-visible training rows, with independent measurement noise per recorded angle.
    alpha_true = _kepler_longitude(train_t, inner["P"], inner["e"], inner["omega_deg"], inner["t0"])
    alpha_obs = (alpha_true + rng_noise.normal(0.0, sd, len(train_t))) % 360.0
    if two_body:
        header = ["t", "alpha"]
        train_rows = [(int(t), round(float(alpha_obs[i]), 4)) for i, t in enumerate(train_t)]
    else:
        beta_true = _apparent_longitude(train_t, inner, outer)
        beta_obs = (beta_true + rng_noise.normal(0.0, sd, len(train_t))) % 360.0
        header = ["t", "alpha", "beta"]
        train_rows = [
            (int(t), round(float(alpha_obs[i]), 4), round(float(beta_obs[i]), 4))
            for i, t in enumerate(train_t)
        ]

    test_days = _future_days(total_days, horizon_factor * target_period, 10)
    points = _oracle_points(rng_oracle, target_true_fn, test_days, sd, oracle_n)

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
