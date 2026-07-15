"""Hyperbolic interstellar-object flyby task (the hardest orbital variant).

An observer on an inner planet watches an interstellar object (ISO) on a
hyperbolic, unbound trajectory whose plane is inclined to the planet's orbit.
Each day the observer records three angles: alpha (direction to the star, which
pins the planet's own position), beta (apparent azimuth of the ISO), and gamma
(apparent elevation of the ISO above the planet's orbital plane). The in-sample
window covers the approach through perihelion; the agent must predict gamma over
the departure arc.

Harder than the two-body and three-body tasks on three counts:

- Non-periodic. A flyby happens once, so there is no period to find; the model
  must fit an open trajectory from a partial arc and extrapolate it.
- Three-dimensional. The inclined plane means recovering inclination and node,
  not a coplanar ellipse; gamma is driven entirely by the out-of-plane geometry.
- Angles-only orbit determination. The reference is a full six-element hyperbolic
  fit, with the observer's parallax (from the planet's motion) breaking the
  range degeneracy.

Ground truth is owned: the exact 3D Keplerian geometry and the measurement-noise
law are known, so the Monte-Carlo oracle is exact. gamma is a bounded elevation
in [-90, 90] (it does not wrap), so it is scored with the shared interval scorer
at period=None. Pure numpy/scipy, no new dependency.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

_NEWTON = 60


def _solve_E(M, e):
    E = M.copy()
    for _ in range(_NEWTON):
        E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    return E


def _solve_H(M, e):
    H = np.arcsinh(M / e)
    for _ in range(80):
        H = H - (e * np.sinh(H) - H - M) / (e * np.cosh(H) - 1.0)
    return H


def _ellipse_pos(t, P, e, om_deg, t0, a=1.0):
    """3D position of the inner planet (in its z=0 orbital plane)."""
    t = np.asarray(t, dtype=float)
    M = 2 * np.pi * (t - t0) / P
    E = _solve_E(M, e)
    nu = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2))
    r = a * (1 - e * np.cos(E))
    th = np.radians(om_deg) + nu
    return np.stack([r * np.cos(th), r * np.sin(th), np.zeros_like(t)], -1)


def _rot(i_deg, Om_deg, w_deg):
    i, Om, w = np.radians([i_deg, Om_deg, w_deg])
    cO, sO, ci, si, cw, sw = np.cos(Om), np.sin(Om), np.cos(i), np.sin(i), np.cos(w), np.sin(w)
    return np.array([
        [cO * cw - sO * sw * ci, -cO * sw - sO * cw * ci, sO * si],
        [sO * cw + cO * sw * ci, -sO * sw + cO * cw * ci, -cO * si],
        [sw * si, cw * si, ci],
    ])


def _hyperbola_pos(t, q, e, i, Om, w, tp, mu):
    """3D position of the ISO on its inclined hyperbolic orbit."""
    t = np.asarray(t, dtype=float)
    a = q / (1 - e)  # negative
    n = np.sqrt(mu / (-a) ** 3)
    H = _solve_H(n * (t - tp), e)
    nu = 2 * np.arctan2(np.sqrt(e + 1) * np.sinh(H / 2), np.sqrt(e - 1) * np.cosh(H / 2))
    r = a * (1 - e * np.cosh(H))
    xp = np.stack([r * np.cos(nu), r * np.sin(nu), np.zeros_like(t)], -1)
    return xp @ _rot(i, Om, w).T


def _angles(r1, riso):
    """Observer angles: alpha (to star), beta (ISO azimuth), gamma (ISO elevation)."""
    alpha = (np.degrees(np.arctan2(-r1[:, 1], -r1[:, 0]))) % 360.0
    rel = riso - r1
    beta = np.degrees(np.arctan2(rel[:, 1], rel[:, 0])) % 360.0
    gamma = np.degrees(np.arctan2(rel[:, 2], np.hypot(rel[:, 0], rel[:, 1])))
    return alpha, beta, gamma


def _uni(rng, lo, hi):
    return float(rng.uniform(lo, hi))


def _draw_instance(seed: int, oracle_n: int) -> dict:
    ss = np.random.SeedSequence(seed)
    rng_s, rng_n, rng_o = (np.random.default_rng(x) for x in ss.spawn(3))

    P1 = _uni(rng_s, 300.0, 450.0)
    planet = dict(P=P1, e=_uni(rng_s, 0.05, 0.2), om=_uni(rng_s, 0, 360), t0=_uni(rng_s, 0, P1))
    mu = 4 * np.pi**2 / P1**2
    # Eccentricity capped at 2.0 so angles-only determination stays well conditioned
    # (the deepest, fastest flybys, e>2.2 with small perihelion, defeat the reference).
    iso = dict(q=_uni(rng_s, 0.5, 1.5), e=_uni(rng_s, 1.15, 2.0), i=_uni(rng_s, 20.0, 60.0),
               Om=_uni(rng_s, 0, 360), w=_uni(rng_s, 0, 360))
    sd = _uni(rng_s, 0.2, 1.0)

    a_iso = iso["q"] / (1 - iso["e"])
    n_iso = np.sqrt(mu / (-a_iso) ** 3)
    # Perihelion is placed at least ~1.2 planet periods in, so alpha covers enough
    # of the planet's orbit to determine it (the parallax baseline) no matter how
    # fast the flyby is. In-sample covers the planet orbit and the ISO approach
    # through perihelion (mean anomaly up to 0.7); the prediction arc is the
    # departure (mean anomaly 0.7 to 2.5).
    tp = max(1.2 * P1, 2.5 / n_iso)
    t_split = tp + 0.7 / n_iso
    t_end = tp + 2.5 / n_iso
    iso["tp"] = tp

    train_t = np.arange(0.0, np.floor(t_split), 1.0)
    test_t = np.round(np.linspace(t_split + 1, t_end, 10))
    test_t = np.array(sorted(set(test_t[test_t > train_t[-1]])))

    def truth_gamma(tt):
        r1 = _ellipse_pos(tt, planet["P"], planet["e"], planet["om"], planet["t0"])
        ri = _hyperbola_pos(tt, iso["q"], iso["e"], iso["i"], iso["Om"], iso["w"], iso["tp"], mu)
        return _angles(r1, ri)

    # The ISO is only observable near its passage; beta/gamma are blank when it is
    # too far out (mean anomaly < -2.5). alpha (the planet) is always recorded.
    visible = n_iso * (train_t - tp) >= -2.5
    a_tr, b_tr, g_tr = truth_gamma(train_t)
    a_obs = (a_tr + rng_n.normal(0, sd, len(train_t))) % 360.0
    b_obs = (b_tr + rng_n.normal(0, sd, len(train_t))) % 360.0
    g_obs = g_tr + rng_n.normal(0, sd, len(train_t))
    train_rows = []
    for k in range(len(train_t)):
        bv = round(float(b_obs[k]), 4) if visible[k] else ""
        gv = round(float(g_obs[k]), 4) if visible[k] else ""
        train_rows.append((int(train_t[k]), round(float(a_obs[k]), 4), bv, gv))

    _, _, g_test_true = truth_gamma(test_t)
    points = []
    for k, tt in enumerate(test_t):
        mc = g_test_true[k] + rng_o.normal(0, sd, oracle_n)
        points.append({"t": float(tt), "true_mean": float(g_test_true[k]),
                       "mc_samples": [round(float(v), 5) for v in mc]})

    return {
        "meta": {"seed": seed, "noise_sd_deg": round(sd, 4), "planet": planet, "iso": iso, "mu": mu,
                 "n_train": len(train_rows)},
        "train_rows": train_rows,
        "test_t": [int(x) for x in test_t],
        "points": points,
    }


def generate_hyperbolic(seed: int, oracle_n: int = 2000, max_tries: int = 30) -> dict:
    """Keep the first seed offset whose 3D hyperbolic-OD reference reaches the noise
    floor, so every shipped instance has a solvable competent anchor (angles-only
    determination defeats the reference on a few percent of the fastest flybys).
    Deterministic in `seed`, so still reproducible."""
    from pereval.scorers.interval import parse_predictions, score_points

    last = None
    for off in range(max_tries):
        b = _draw_instance(seed + off, oracle_n)
        preds = parse_predictions(_od_fit_predict(train_csv_text(b), test_csv_text(b)), ["t"])
        regret = score_points(truth_to_points(build_truth(b)), preds, period=None)["winkler_regret"]
        b["meta"]["seed_offset"] = off
        b["meta"]["reference_regret"] = round(float(regret), 4)
        if np.isfinite(regret) and regret < 0.5:
            return b
        last = b
    return last


# --- serialization ---------------------------------------------------------

def train_csv_text(bundle):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["t", "alpha", "beta", "gamma"])
    w.writerows(bundle["train_rows"])
    return buf.getvalue()


def test_csv_text(bundle):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["t"])
    w.writerows([(t,) for t in bundle["test_t"]])
    return buf.getvalue()


def build_truth(bundle):
    return {"meta": bundle["meta"], "points": bundle["points"]}


def truth_to_points(truth):
    return [{"key": (float(p["t"]),), "class": None, "true_mean": p["true_mean"],
             "mc": np.asarray(p["mc_samples"], dtype=float)} for p in truth["points"]]


def write_outputs(bundle, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "train.csv").write_text(train_csv_text(bundle))
    (out_dir / "test.csv").write_text(test_csv_text(bundle))
    with (out_dir / "truth.json").open("w") as f:
        json.dump(build_truth(bundle), f, indent=2)


def main():
    ap = argparse.ArgumentParser(description="Generate a perEval hyperbolic-flyby task instance.")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--oracle-n", type=int, default=2000)
    args = ap.parse_args()
    seed = args.seed if args.seed is not None else int(np.random.SeedSequence().generate_state(1)[0])
    bundle = generate_hyperbolic(seed=seed, oracle_n=args.oracle_n)
    write_outputs(bundle, args.out_dir)
    m = bundle["meta"]
    print(f"seed={seed} noise_sd={m['noise_sd_deg']} n_train={m['n_train']} n_test={len(bundle['test_t'])}")
    print(f"ISO: q={m['iso']['q']:.2f} e={m['iso']['e']:.2f} i={m['iso']['i']:.1f}deg")
    print("gamma at test points: " + " ".join(f"{p['true_mean']:.1f}" for p in bundle["points"]))


if __name__ == "__main__":
    main()


# --- baselines: naive polynomial vs 3D hyperbolic orbit determination -------

from inspect_ai.solver import Generate, TaskState, solver  # noqa: E402
from inspect_ai.util import sandbox  # noqa: E402

Z95 = 1.959964


def _col(rows, name):
    return np.array([float(r[name]) if r[name] not in ("", None) else np.nan for r in rows])


def _read(train_text, test_text):
    tr = list(csv.DictReader(io.StringIO(train_text)))
    t = np.array([float(r["t"]) for r in tr])
    a, b, g = _col(tr, "alpha"), _col(tr, "beta"), _col(tr, "gamma")
    tt = np.array([float(r["t"]) for r in csv.DictReader(io.StringIO(test_text))])
    return t, a, b, g, tt


def _write(test_t, point, half):
    lines = ["t,y_pred,y_lower,y_upper"]
    for x, p in zip(test_t, point):
        lines.append(f"{int(x)},{p},{p - half},{p + half}")
    return "\n".join(lines) + "\n"


def _wrap(d):
    return ((d + 180) % 360) - 180


def _poly_fit_predict(train_text, test_text, degree=4):
    t, _, _, gamma, test_t = _read(train_text, test_text)
    v = np.isfinite(gamma)
    c = np.polyfit(t[v], gamma[v], degree)
    s = float(np.sqrt(np.mean((gamma[v] - np.polyval(c, t[v])) ** 2)))
    return _write(test_t, np.polyval(c, test_t), Z95 * s)


def _lon_of(t, P, e, om, t0):
    r = _ellipse_pos(t, P, e, om, t0)
    return np.degrees(np.arctan2(r[:, 1], r[:, 0])) % 360.0


def _fit_planet(t, alpha):
    lon = (alpha - 180.0) % 360.0
    slope = np.polyfit(t, np.degrees(np.unwrap(np.radians(lon))), 1)[0]
    P0 = 360.0 / slope
    best = None
    for e0 in (0.05, 0.15):
        for om0 in (0.0, 120.0, 240.0):
            try:
                r = least_squares(lambda p: _wrap(lon - _lon_of(t, *p)), [P0, e0, om0, 0.0],
                                  bounds=([0.6 * P0, 0, -360, -2 * P0], [1.5 * P0, 0.5, 720, 2 * P0]), max_nfev=3000)
                if best is None or r.cost < best.cost:
                    best = r
            except Exception:
                pass
    return best.x


def _iso_angles(t, p, planet, mu):
    r1 = _ellipse_pos(t, planet[0], planet[1], planet[2], planet[3])
    ri = _hyperbola_pos(t, p[0], p[1], p[2], p[3], p[4], p[5], mu)
    _, b, g = _angles(r1, ri)
    return b, g


def _fit_iso(t, beta, gamma, planet, mu):
    span = float(t.max() - t.min())
    # data-driven perihelion guess: the ISO's apparent angular speed peaks there
    dt = np.diff(t)
    speed = np.hypot(_wrap(np.diff(beta)) / dt, np.diff(gamma) / dt)
    tp0 = float(t[1 + int(np.argmax(speed))])
    lo = [0.1, 1.05, 0, -180, -180, t.min() - 2 * span]
    hi = [4.0, 3.5, 90, 540, 540, t.max() + span]

    def resid(p):
        b, g = _iso_angles(t, p, planet, mu)
        return np.concatenate([_wrap(beta - b), gamma - g])

    def run(starts):
        best = None
        for s in starts:
            try:
                r = least_squares(resid, s, bounds=(lo, hi), max_nfev=4000)
                if best is None or r.cost < best.cost:
                    best = r
            except Exception:
                pass
        return best

    best = run([[q, e, i, 0.0, 0.0, tp0]
                for q in (0.4, 0.9, 1.4) for e in (1.3, 1.7) for i in (25.0, 45.0)])
    # If the best fit is nowhere near noise level it is a local minimum: retry with
    # a denser grid that also varies the orbit orientation (Omega, omega).
    if np.sqrt(np.mean(best.fun**2)) > 3.0:
        dense = run([[q, e, i, Om, w, tp0]
                     for q in (0.5, 1.0, 1.5) for e in (1.3, 1.7) for i in (30.0, 50.0)
                     for Om in (0.0, 120.0, 240.0) for w in (0.0, 180.0)])
        if dense is not None and dense.cost < best.cost:
            best = dense
    return best.x


def _od_fit_predict(train_text, test_text):
    t, alpha, beta, gamma, test_t = _read(train_text, test_text)
    planet = _fit_planet(t, alpha)  # alpha spans the full window
    mu = 4 * np.pi**2 / planet[0] ** 2
    v = np.isfinite(beta) & np.isfinite(gamma)  # ISO fit uses only the observed flyby arc
    iso = _fit_iso(t[v], beta[v], gamma[v], planet, mu)
    _, g_in = _iso_angles(t[v], iso, planet, mu)
    s = float(np.sqrt(np.mean((gamma[v] - g_in) ** 2)))
    _, g_test = _iso_angles(test_t, iso, planet, mu)
    return _write(test_t, g_test, Z95 * s)


@solver
def polynomial_baseline():
    """Naive: extrapolate a polynomial in t; a flyby is not a polynomial."""
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        tr = await sandbox().read_file("data/train.csv")
        te = await sandbox().read_file("data/test.csv")
        await sandbox().write_file("predictions.csv", _poly_fit_predict(tr, te))
        return state
    return solve


@solver
def hyperbolic_od_baseline():
    """Reference: fit the planet orbit from alpha, then the 3D hyperbolic ISO orbit."""
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        tr = await sandbox().read_file("data/train.csv")
        te = await sandbox().read_file("data/test.csv")
        await sandbox().write_file("predictions.csv", _od_fit_predict(tr, te))
        return state
    return solve
