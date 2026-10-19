"""Reference solvers for the rating-migration task, using only the public files.

`onefactor` is the competent anchor: pool the annual counts into an
unconditional matrix, take its fourth root for a quarterly base, estimate each
year's systematic factor by maximum likelihood against that year's counts,
regress the factor on a parsimonious macro feature set, project it over the
scenario and propagate the holdout cohort.

It is a reference, not an oracle. It assumes the factor is constant within each
year, which it is not, it assumes an asset correlation rather than estimating
one, and its base matrix is a fourth root of a product of four different
matrices. Those three approximations are precisely the annual-to-quarterly
problem the task poses, so this solver lands near the target without reaching
it, which is what an anchor is for.

The factor regression is shrunk, because the task ships twenty annual
observations against seven parameters, which is the data sparsity a real
portfolio has. It is not bounded: a stress model has to answer scenarios more
severe than its own history. See `project_factor`.

`no_migration` submits the starting cohort unchanged. It is the degenerate
answer the scorer computes anyway, provided here so a run can produce it.
"""

from __future__ import annotations

import csv
import io
import json

import numpy as np
from scipy.linalg import fractional_matrix_power
from scipy.optimize import brentq, minimize_scalar

from pereval.scorers.migration import ORDER
from pereval.tasks.migration.generator import (
    CELL_FLOOR,
    D,
    LIVE,
    PD_FLOOR_QUARTERLY,
    RHO_RANGE,
    conditional_matrix,
)

#: The reference does not know the drawn asset correlation and assumes the
#: midpoint of the range. Seeds whose true value sits at an end of the range are
#: where most of its residual error comes from.
RHO_ASSUMED = float(np.mean(RHO_RANGE))

#: Levels for the recession-up candidates, year-over-year change for the
#: recession-down candidates, because the latter are trending series.
FEATURES = (("unemployment", False), ("bbb_spread", False), ("vix", False),
            ("gdp", True), ("hpi", True), ("nasdaq", True))

#: The ridge penalty is set so the factor regression spends an effective
#: dimension of 1 + n / DF_DIVISOR on n annual observations: 3.5 at the shipped
#: twenty years, 6.0 at forty. A rule, not a constant, so a shorter history
#: shrinks harder on its own.
DF_DIVISOR = 8.0


def _rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def _annual_matrices(text):
    out = {}
    for r in _rows(text):
        y = int(r["year"])
        m = out.setdefault(y, np.zeros((D, D + 1)))
        i = LIVE.index(r["from_rating"])
        for j, s in enumerate(list(LIVE) + ["D"]):
            m[i, j] = float(r[f"to_{s.replace('/', '_')}"])
    return out


def pooled_quarterly_base(mats):
    """Unconditional quarterly matrix from the pooled counts, made admissible.

    Three corrections a competent modeller applies and the raw fourth root does
    not. No cell is left at exactly zero, since a reachable transition assigned
    zero probability can never be revised by evidence and allocates no reserve.
    The default column is floored at the quarterly equivalent of the 0.03% annual
    PD minimum. And the default column is forced non-decreasing across grades,
    because thin counts in the top grades otherwise invert the ordering and leave
    the model asserting that AAA is riskier than AA.

    The last two interact: once AAA and AA are both floored they are equal in
    truth, so sampling noise alone will invert their estimates about half the
    time unless the ordering is imposed.
    """
    tot = sum(mats.values())
    ann = np.zeros((D + 1, D + 1))
    ann[:D] = tot / np.maximum(tot.sum(axis=1, keepdims=True), 1.0)
    ann[D, D] = 1.0
    q = np.clip(np.real(fractional_matrix_power(ann, 0.25)), CELL_FLOOR, None)
    q[D, :] = 0.0
    q[D, D] = 1.0
    live = q[:D]
    pd = np.maximum(live[:, D], PD_FLOOR_QUARTERLY)
    live[:, D] = np.maximum.accumulate(pd)        # non-decreasing in grade
    rest = live[:, :D]
    rest *= ((1.0 - live[:, D]) / rest.sum(axis=1))[:, None]
    q[:D] = live
    return q


def factor_mle(counts, base, rho=RHO_ASSUMED):
    """One year's systematic factor, assuming it is constant across the four quarters."""
    def negll(z):
        ann = np.linalg.matrix_power(conditional_matrix(base, float(z), rho), 4)
        return -float((counts * np.log(np.clip(ann[:D], 1e-12, 1.0))).sum())

    return float(minimize_scalar(negll, bounds=(-4.0, 4.0), method="bounded").x)


def _ridge(X, y, lam):
    """Penalised least squares, intercept left unpenalised, features standardised."""
    n, p = X.shape
    pen = lam * n * np.diag([0.0] + [1.0] * (p - 1))
    return np.linalg.solve(X.T @ X + pen, X.T @ y)


def _lambda_for_df(X, target):
    """The penalty whose hat matrix has the target effective dimension."""
    n, p = X.shape
    pen = np.diag([0.0] + [1.0] * (p - 1))

    def df(log_lam):
        a = X.T @ X + float(np.exp(log_lam)) * n * pen
        return float(np.trace(X @ np.linalg.solve(a, X.T)))

    if df(-14.0) <= target:                 # already below target unpenalised
        return 0.0
    return float(np.exp(brentq(lambda L: df(L) - target, -14.0, 8.0, xtol=1e-4)))


def project_factor(X, Xs, zhat):
    """The scenario factor path, from a shrunk regression and nothing else.

    Twenty annual observations against seven parameters overfits, and the
    symptom is a projection of +6.4 where the truth is +3.4. The cause is
    coefficient inflation across six collinear drivers when the data-generating
    process uses two: the loadings offset each other inside the historical
    range and stop offsetting once the scenario moves the drivers differently.
    So the penalty comes from the sample-size rule in DF_DIVISOR.

    What is deliberately NOT here is any bound on how far the projection may go.
    A stress model must answer a scenario more severe than anything observed;
    that is the only reason it exists. The Federal Reserve's own scenario design
    framework specifies a severely adverse unemployment path that exceeds most
    of the historical record by construction, and the generator's
    `systematic_factor` says the same thing from the other side: the scenario
    window is where the factor is supposed to go out of range. Clipping the
    projection to the estimated range was tried and scores slightly better, and
    it is still wrong, because it makes the model structurally incapable of the
    one question it is asked. The correct review of extreme inputs is whether
    the response stays monotone and finite out there, which is what
    `factor_response_diagnostics` reports.

    Two other fixes were tried and do not work. Leave-one-out cross-validation
    picks almost no penalty, because every held-out year lies inside the
    historical range while the scenario lies outside it, so in-time validation
    is blind to extrapolation error by construction. Economic sign constraints
    on the loadings, a standard review checklist item, leave the failure rate
    unchanged: the blow-up draws have correctly signed loadings that are simply
    too large.
    """
    lam = _lambda_for_df(X, 1.0 + X.shape[0] / DF_DIVISOR)
    return Xs @ _ridge(X, zhat, lam)


def factor_response_diagnostics(X, Xs, zhat, multiples=(1.0, 1.5, 2.0, 3.0)):
    """How the projection behaves as the scenario is pushed past the record.

    The review question about extreme macro inputs is not whether the model
    refuses them but whether its response is well behaved: monotone in severity,
    finite, and with no sign reversal. Severity is scaled in standardised
    feature space, where zero is the historical mean, so a multiple of three is
    a scenario three times as far from normal as the one supplied.
    """
    lam = _lambda_for_df(X, 1.0 + X.shape[0] / DF_DIVISOR)
    coef = _ridge(X, zhat, lam)
    out = {}
    for m in multiples:
        scaled = Xs.copy()
        scaled[:, 1:] *= m
        out[m] = float(np.max(scaled @ coef))
    peaks = [out[m] for m in multiples]
    return {
        "peak_by_multiple": out,
        "monotone_in_severity": all(b >= a - 1e-9 for a, b in zip(peaks, peaks[1:])),
        "finite": bool(np.all(np.isfinite(peaks))),
        "exceeds_history_at_1x": bool(peaks[0] > zhat.max()),
    }


def _macro_features(history, scenario, n_years):
    def series(rows, name):
        return np.array([float(r[name]) if r[name] not in ("", None) else np.nan
                         for r in rows], dtype=float)

    hist, scen = [], []
    for name, as_change in FEATURES:
        h = series(history, name)
        s = series(scenario, name)
        if np.isnan(h).any():                 # ragged start: back-fill
            first = np.flatnonzero(~np.isnan(h))[0]
            h[:first] = h[first]
        if as_change:
            joined = np.concatenate([h, s])
            y = np.empty(len(joined))
            y[4:] = joined[4:] / joined[:-4] - 1.0
            y[:4] = y[4]
            h, s = y[:len(h)], y[len(h):]
        yr = h.reshape(n_years, 4).mean(axis=1)
        mu, sd = yr.mean(), yr.std(ddof=1) + 1e-12
        hist.append((yr - mu) / sd)
        scen.append((s - mu) / sd)
    n_scen = len(scenario)
    return (np.column_stack([np.ones(n_years)] + hist),
            np.column_stack([np.ones(n_scen)] + scen))


def matrices_csv(mats: dict[int, np.ndarray]) -> str:
    """The quarterly matrices the solver actually used, in the requested layout."""
    cols = ["quarter", "from_rating"] + [f"to_{s.replace('/', '_')}" for s in ORDER]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    for q in sorted(mats):
        for i, frm in enumerate(LIVE):
            row = {"quarter": q, "from_rating": frm}
            for j, s in enumerate(ORDER):
                row[f"to_{s.replace('/', '_')}"] = float(mats[q][i, j])
            w.writerow(row)
    return buf.getvalue()


def predict(files: dict[str, str], method: str = "onefactor") -> str:
    if method not in ("onefactor", "no_migration"):
        raise ValueError("method must be 'onefactor' or 'no_migration'")
    portfolio = _rows(files["data/portfolio.csv"])
    counts = np.array([float(r["obligors"]) for r in portfolio])
    mix = counts / counts.sum()
    checkpoints = json.loads(files["data/policy.json"])["checkpoints"]

    quarterlies: dict[int, np.ndarray] = {}
    if method == "no_migration":
        dists = {q: np.concatenate([mix, [0.0]]) for q in checkpoints}
        # the model is that nothing happens, so the matrices are the identity
        for q in range(1, max(checkpoints) + 1):
            quarterlies[q] = np.eye(len(ORDER))
    else:
        mats = _annual_matrices(files["data/transitions.csv"])
        base = pooled_quarterly_base(mats)
        years = sorted(mats)
        zhat = np.array([factor_mle(mats[y], base) for y in years])
        history = _rows(files["data/macro_history.csv"])
        scenario = _rows(files["data/scenario.csv"])
        X, Xs = _macro_features(history, scenario, len(years))
        z = project_factor(X, Xs, zhat)
        v = np.concatenate([mix, [0.0]])
        dists = {}
        for t in range(max(checkpoints)):
            m = conditional_matrix(base, float(z[t]), RHO_ASSUMED)
            quarterlies[t + 1] = m
            v = v @ m
            if t + 1 in checkpoints:
                dists[t + 1] = v.copy()

    out = [{"quarter": q, "state": s, "share": float(dists[q][i])}
           for q in sorted(dists) for i, s in enumerate(ORDER)]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["quarter", "state", "share"])
    w.writeheader()
    w.writerows(out)
    return buf.getvalue(), matrices_csv(quarterlies)


def reference_solver(method: str):
    from inspect_ai.solver import solver
    from inspect_ai.util import sandbox

    @solver(name=f"migration_{method}")
    def _ref():
        async def solve(state, generate):
            files = {
                f"data/{n}": await sandbox().read_file(f"data/{n}")
                for n in ("transitions.csv", "macro_history.csv",
                          "scenario.csv", "portfolio.csv", "policy.json")
            }
            preds, mats = predict(files, method)
            await sandbox().write_file("predictions.csv", preds)
            await sandbox().write_file("matrices.csv", mats)
            return state

        return solve

    return _ref()
