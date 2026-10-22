#!/usr/bin/env python3
"""Write a backtest-and-projection PNG to runs/ for each sample in an eval log.

Usage: plot_backtest.py <log.eval> [more.eval ...]

`save_transcript.py` calls `render_png` as it archives each sample, so a run
leaves its figures beside its transcripts without a second command. Running this
file directly backfills figures for logs whose transcripts are already saved.

One PNG per sample, named like the sample's markdown transcript so the two sit
side by side. Four panels. On the left, a wide view of the whole quarterly axis
from -79 to 9, the submission on top and the shipped one-factor reference below,
so the eye can compare the two fits to the same history and the same scenario.
On the right, a narrow view of the horizon alone with all three scenarios drawn,
on one shared y axis, so the severity ordering and the shape of each path can be
read without the eighty quarters of history compressing them.

Everything is in QUARTERLY hazard, the share of the live portfolio at the start
of a quarter that defaults during it.

The published history is ANNUAL, so each annual rate `a` is plotted as the
quarterly hazard `1 - (1 - a) ** 0.25` at the last quarter of its year, and the
points are joined by straight lines. The timing within a year is unknown and
this is a stand-in for it, which matters when reading the join at quarter 0: on
the twelve instances measured, the TRUE hazard of a year's last quarter runs
0.42 to 3.53 times the annual stand-in plotted there, above 1.5 times on 15% of
years. A step between quarter 0 and quarter 1 is therefore not evidence that the
scenario starts with a jump. The factor itself does not: across twenty four
instances the largest change from the last historical quarter to the first
scenario quarter is 0.85 standard deviations against a within-history quarterly
change whose own 90th percentile is 1.01 and whose maximum is 6.26, and not one
of the seventy two joins exceeds that 90th percentile.

The band is the 95% interval of the same construction the reference's own
backtest uses: residuals `logit(observed) - logit(fitted)`, assumed logistic and
moment-matched, divided by n minus the effective degrees of freedom, at 2.020
standard deviations. Two notes on reading it. It is drawn from the residuals of
the fit it surrounds, so it shrinks as the fit tightens and cannot detect
overfitting, which is measured under What It Cannot Do in the task document. And
the agent's degrees of freedom are unknowable from its submission, so both
panels use the reference's effective df: the two bands are then constructed
identically, which is what makes the panels comparable, and neither is a claim
about the agent's model complexity.
"""
import os
import sys

import numpy as np
from scipy.special import expit, logit

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, ROOT)
RUNS = os.path.join(ROOT, "runs")

#: 97.5th percentile of the moment-matched logistic, as in the reference's band.
UPPER_SD = 2.020

#: The scenario the wide panels project. One line keeps the comparison between
#: the two fits readable; the narrow panels carry all three.
SCENARIO = "adverse"

#: Severity as a darkening ramp, so the ordering is legible before the legend is.
SCENARIO_STYLE = {
    "baseline": ("#74c476", ":"),
    "adverse": ("#2b9348", "--"),
    "severe": ("#14532d", "-"),
}


def annual_to_quarterly(a):
    """The flat quarterly hazard whose four quarters compound to the annual rate."""
    a = np.clip(np.asarray(a, dtype=float), 0.0, 1 - 1e-12)
    return 1.0 - (1.0 - a) ** 0.25


def annual_x(n_years):
    """Each annual value sits at the LAST quarter of its year, so the final one
    lands on quarter 0 and joins the horizon without a gap."""
    return np.arange(-4 * n_years + 4, 1, 4)


def forward_hazard(mats, start, d_index):
    """Per-quarter default hazard of the cohort as it runs down the scenario.

    The hazard, not the cumulative share: what fraction of the obligors still
    alive at the start of a quarter default during it, which is the same
    quantity the historical panel plots and so the only one that can share a
    y axis with it.
    """
    v = np.asarray(start, dtype=float).copy()
    out = []
    for q in sorted(mats):
        m = mats[q]
        live = v[:d_index]
        tot = live.sum()
        out.append(float((live / tot) @ m[:d_index, d_index])
                   if tot > 0 else float("nan"))
        v = v @ m
    return np.array(out)


def residual_sd(obs_q, fit_q, dof):
    o = np.clip(obs_q, 1e-9, 1 - 1e-9)
    f = np.clip(fit_q, 1e-9, 1 - 1e-9)
    resid = logit(o) - logit(f)
    sd = float(np.sqrt(resid @ resid / max(len(resid) - dof, 1.0)))
    return sd, float(resid.mean())


def envelope(values, sd, shift=0.0):
    c = logit(np.clip(values, 1e-9, 1 - 1e-9)) + shift
    return expit(c - UPPER_SD * sd), expit(c + UPPER_SD * sd)


def shape_stats(obs_annual, fit_annual):
    """The two numbers this picture is about, so the eye and the key agree.

    `prominence` is the height of the fitted peak above its own median over the
    same height for the observed series, which is what the damping of a peak
    looks like. `stress ratio` is the fitted mean over the worst quarter of
    years divided by the observed mean over those same years.
    """
    if fit_annual is None:
        return None, None
    o, f = np.asarray(obs_annual, float), np.asarray(fit_annual, float)
    spread = o.max() - float(np.median(o))
    prom = ((f.max() - float(np.median(f))) / spread) if spread > 0 else float("nan")
    st = o >= np.quantile(o, 0.75)
    ratio = float(f[st].mean() / o[st].mean()) if o[st].mean() > 0 else float("nan")
    return float(prom), ratio


def wide_panel(ax, title, obs_annual, fit_annual, fwd, dof, n_years, horizon):
    hx = annual_x(n_years)
    obs_y = annual_to_quarterly(obs_annual)
    ax.plot(hx, obs_y, color="tab:blue", lw=1.6, zorder=3,
            label="observed (annual, at its year's last quarter)")

    sd = None
    top = float(np.max(obs_y))
    if fit_annual is not None:
        fit_y = annual_to_quarterly(fit_annual)
        sd, shift = residual_sd(obs_y, fit_y, dof)
        lo, hi = envelope(fit_y, sd, shift)
        ax.fill_between(hx, lo, hi, color="0.72", alpha=0.5, lw=0, zorder=1,
                        label="95% band from the fit's own residuals "
                              "(may run past the top of the axis)")
        ax.plot(hx, fit_y, color="tab:green", lw=1.7, ls="--", zorder=4,
                label=f"model's fitted rate, and its {SCENARIO} projection")
        top = max(top, float(np.max(fit_y)))

        if fwd is not None and len(fwd):
            # the join is drawn, not implied: quarter 0 is the model's own
            # fitted level, so any step into quarter 1 is the model's step
            fx = np.concatenate([[0], np.arange(1, len(fwd) + 1)])
            fy = np.concatenate([[fit_y[-1]], fwd])
            flo, fhi = envelope(fy, sd)
            ax.fill_between(fx, flo, fhi, color="0.72", alpha=0.5, lw=0, zorder=1)
            ax.plot(fx, fy, color="tab:green", lw=1.7, ls="--", zorder=4)
            ax.plot(fx[1:], fy[1:], "o", color="tab:green", ms=3.0, zorder=5)
            top = max(top, float(np.nanmax(fwd)))

    prom, ratio = shape_stats(obs_annual, fit_annual)
    if prom is not None:
        ax.text(0.995, 0.94, f"peak prominence {prom:.2f}   "
                             f"stressed-year ratio {ratio:.2f}",
                transform=ax.transAxes, ha="right", va="top", fontsize=8,
                bbox=dict(fc="white", ec="0.7", lw=0.5, pad=2.5))

    ax.axvline(0.5, color="0.4", lw=0.8, ls=":")
    ax.set_xlim(-4 * n_years + 1, horizon)
    ax.set_ylabel("quarterly default rate")
    ax.set_title(title, fontsize=9, loc="left")
    ax.grid(alpha=0.25, lw=0.5)
    return sd, top


def horizon_panel(ax, title, paths, anchor, obs_last):
    """All three scenarios over the horizon alone, anchored at quarter 0.

    Quarter 0 carries the model's own last fitted quarter, so the step into
    quarter 1 that each scenario takes is visible and is the model's own.
    """
    top = 0.0
    for name in ("baseline", "adverse", "severe"):
        fwd = paths.get(name)
        if fwd is None or not len(fwd):
            continue
        colour, ls = SCENARIO_STYLE[name]
        x = np.concatenate([[0], np.arange(1, len(fwd) + 1)])
        y = np.concatenate([[anchor], fwd])
        ax.plot(x, y, color=colour, ls=ls, lw=1.8, label=name, zorder=4)
        ax.plot(x[1:], y[1:], "o", color=colour, ms=2.8, zorder=5)
        top = max(top, float(np.nanmax(fwd)))
    if obs_last is not None:
        # named in the panel title rather than the legend, which is already
        # carrying six entries and has one row to carry them in
        ax.plot([0], [obs_last], "o", color="tab:blue", ms=4.5, zorder=6)
    ax.axvline(0.5, color="0.4", lw=0.8, ls=":")
    ax.set_xlim(-0.3, 9.3)
    ax.set_xticks(range(0, 10, 2))
    ax.set_title(title, fontsize=9, loc="left")
    ax.grid(alpha=0.25, lw=0.5)
    return top


def figure(path, sid, model, obs, agent, ref, dof, n_years, horizon):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(14, 7.6), sharex="col",
                             gridspec_kw=dict(width_ratios=[3.1, 1.0]))
    obs_y = annual_to_quarterly(obs)

    rows = ((f"submission: {model} — {sid}", agent, axes[0]),
            ("reference: one-factor, ridge-shrunk", ref, axes[1]))
    wide_top, nar_top = [], []
    for title, sub, (wax, nax) in rows:
        _, t = wide_panel(wax, title, obs, sub["fit"], sub["paths"].get(SCENARIO),
                          dof, n_years, horizon)
        wide_top.append(t)
        anchor = (annual_to_quarterly(sub["fit"])[-1]
                  if sub["fit"] is not None else float(obs_y[-1]))
        nar_top.append(horizon_panel(
            nax, "horizon: three scenarios (dot = last observed)",
            sub["paths"], anchor, float(obs_y[-1])))

    axes[0][0].sharey(axes[1][0])
    axes[0][1].sharey(axes[1][1])
    axes[0][0].set_ylim(0.0, 1.35 * max(wide_top))
    axes[0][1].set_ylim(0.0, 1.15 * max(nar_top + [float(obs_y[-1])]))
    axes[1][0].set_xlabel(f"quarter, relative to the projection "
                          f"(0 is the last historical quarter; "
                          f"1 to {horizon} are the {SCENARIO} scenario)")
    axes[1][1].set_xlabel("quarter of the horizon")

    h1, l1 = axes[0][0].get_legend_handles_labels()
    h2, l2 = axes[0][1].get_legend_handles_labels()
    fig.legend(h1 + h2, l1 + l2, loc="lower center", ncol=len(h1) + len(h2),
               fontsize=7.5, frameon=False, bbox_to_anchor=(0.5, 0.0),
               columnspacing=1.4, handlelength=2.4)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(path, dpi=140)
    plt.close(fig)


#: The only task whose submission this file knows how to draw. A log from any
#: other task is skipped rather than guessed at.
TASK = "migration"


def render_png(log, sample, path) -> bool:
    """Draw one sample's figure to `path`. False when there is nothing to draw.

    Rebuilding the instance from its seed costs a second or two per sample,
    which is why this is called once per archived transcript rather than from
    inside the scorer.
    """
    if log.eval.task != TASK:
        return False

    from pereval.scorers.migration import (
        D_INDEX, ORDER, parse_backtest, parse_matrices,
    )
    from pereval.tasks.migration.baselines import backtest_diagnostics, predict
    from pereval.tasks.migration.generator import generate
    from pereval.tasks.migration.task import public_files

    sid = str(sample.id)
    truth = (sample.metadata or {}).get("truth")
    scores = sample.scores or {}
    sc = scores.get(log.eval.task) or (next(iter(scores.values())) if scores else None)
    if not truth or sc is None or "seed-" not in sid:
        return False

    n_years = int((log.eval.task_args or {}).get("n_years", 20))
    obs = np.asarray(truth["observed_annual_default_rate"], dtype=float)
    start = np.array([truth["start_mix"].get(g, 0.0) for g in ORDER], float)
    horizon = int(truth.get("horizon_quarters") or 9)

    files = public_files(generate(int(sid.rsplit("seed-", 1)[-1]), n_years=n_years))
    dof = float(backtest_diagnostics(files)["effective_df"])
    md = sc.metadata or {}

    def submission(btext, mtext):
        fit = parse_backtest(btext)
        years = sorted(fit)
        fa = np.array([fit[y] for y in years]) if len(years) == len(obs) else None
        return {"fit": fa,
                "paths": {n: forward_hazard(m, start, D_INDEX)
                          for n, m in parse_matrices(mtext).items() if m}}

    agent = submission(md.get("backtest.csv"), md.get("matrices.csv"))
    _, rm, rb = predict(files, "onefactor")
    figure(path, sid, log.eval.model, obs, agent, submission(rb, rm),
           dof, n_years, horizon)
    return True


def main(paths):
    from inspect_ai.log import read_eval_log

    from save_transcript import sample_stem

    for p in paths:
        log = read_eval_log(p)
        for s in (log.samples or []):
            out = os.path.join(RUNS, f"{sample_stem(log, s)}.png")
            if render_png(log, s, out):
                print(out)


if __name__ == "__main__":
    main(sys.argv[1:])
