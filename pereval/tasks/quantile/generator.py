"""Instance generation for the quantile task.

One instance is N_BLOCKS independent estimation problems. Each draws a distinct
FRED series, takes a random contiguous window of that series' year-over-year
percent changes as the population, draws 10 values from it uniformly without
replacement, scales them by an independent log-uniform factor, rounds to 4
significant figures and shuffles the order.

Three disguises, each doing a different job:

  - random window: even perfect recognition of the series does not give you the
    p95 of a span whose endpoints you do not know. This is the one that matters.
  - random scale: removes absolute magnitude, so "12 percent is historically
    extreme" is unavailable. A positive factor maps 0 to 0, so the sign
    structure and the meaning of zero survive, and a model may still use the
    legitimate prior that macro growth rates have fat right tails.
  - 4 significant figures: defeats exact matching against a memorised table.
    On its own it is weak; it is the scale factor that does the work.

No location shift is applied. Every estimator under comparison is location-scale
equivariant, so a shift would be invisible to the score, but it would destroy
zero as a reference point and close the tail-shape prior channel above.

Ground truth never leaves the host: only the 400 numbers reach the prompt.
"""

from __future__ import annotations

import os

import numpy as np

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
N_BLOCKS = 40
N_DRAW = 10
M_MIN = 250          # below this, HD at p95 is squeezed against the sample max
M_MAX = 600
SCALE_LO, SCALE_HI = 0.1, 10.0
SIGFIG = 4

_CACHE: dict[str, np.ndarray] | None = None


def load_series(path: str | None = None) -> dict[str, np.ndarray]:
    """series_id -> 1-d array of YoY percent changes, in time order."""
    global _CACHE
    if _CACHE is None or path is not None:
        with np.load(path or os.path.join(DATA, "series.npz")) as z:
            data = {k: z[k].astype(float) for k in z.files}
        if path is not None:
            return data
        _CACHE = data
    return _CACHE


def sigfig(x, digits: int = SIGFIG):
    """Round to `digits` significant figures, elementwise."""
    x = np.asarray(x, dtype=float)
    out = np.zeros_like(x)
    nz = x != 0
    mag = 10.0 ** np.floor(np.log10(np.abs(x[nz])))
    out[nz] = np.round(x[nz] / mag, digits - 1) * mag
    return out


def draw_block(pop_full: np.ndarray, rng: np.random.Generator) -> dict:
    """Take a random window, draw N_DRAW from it, scale, round, shuffle."""
    n = len(pop_full)
    m = int(rng.integers(M_MIN, min(n, M_MAX) + 1))
    start = int(rng.integers(0, n - m + 1))
    window = pop_full[start:start + m]

    # choice(replace=False) returns a uniformly random permutation of the chosen
    # subset, independent of the values, so the draw order already carries no
    # time information. Do NOT np.sort(idx) for readability: the window is a
    # serially correlated series, and time order would leak structure the
    # estimand (an unordered population) does not reward.
    idx = rng.choice(m, N_DRAW, replace=False)
    mask = np.ones(m, bool)
    mask[idx] = False
    scale = float(np.exp(rng.uniform(np.log(SCALE_LO), np.log(SCALE_HI))))

    shown = sigfig(window[idx] * scale)
    return dict(
        m=m, start=start, scale=scale,
        pop=np.sort(window[mask]) * scale,   # population excluding the drawn 10
        sd=float(window[mask].std(ddof=1) * scale),
        x=np.sort(shown),                    # ascending, host side
        shown=shown,                         # draw order, already random
    )


def generate(seed: int, n_blocks: int = N_BLOCKS,
             series: dict[str, np.ndarray] | None = None) -> list[dict]:
    """One instance: n_blocks blocks, each from a DIFFERENT series.

    Distinct series per block is load-bearing. Forty windows of one series would
    hand the model most of that population across the prompt, and it could pool
    them despite the per-block scaling.
    """
    series = series if series is not None else load_series()
    names = sorted(series)
    usable = [s for s in names if len(series[s]) >= M_MIN]
    if len(usable) < n_blocks:
        raise ValueError(f"need {n_blocks} series with >= {M_MIN} observations, "
                         f"have {len(usable)}")

    rng = np.random.default_rng(seed)
    chosen = [usable[i] for i in rng.choice(len(usable), n_blocks, replace=False)]
    blocks = []
    for i, sid in enumerate(chosen, 1):
        b = draw_block(series[sid], rng)
        b.update(block=i, series=sid)
        blocks.append(b)
    return blocks


def prompt_text(blocks: list[dict]) -> str:
    """The task statement. States the estimand explicitly.

    Leaving "the 95th percentile" ambiguous would make this a reading test whose
    result flips on a paraphrase. Naming the estimand costs nothing: knowing
    that the population quantile is the target does not tell you how to
    extrapolate a tail from ten points.
    """
    ms = sorted({b["m"] for b in blocks})
    body = "\n\n".join(
        f"Block {b['block']} (population size m = {b['m']}):\n  "
        + ", ".join(f"{v:g}" for v in b["shown"]) for b in blocks)
    return f"""You are given {len(blocks)} independent estimation problems.

Each block below is a SAMPLE of {N_DRAW} values drawn uniformly at random, WITHOUT
replacement, from a POPULATION of m values (m is given per block, and ranges
{ms[0]} to {ms[-1]}). Each population is the set of year-over-year percent changes of
one undisclosed macroeconomic time series over an undisclosed date range,
multiplied by an undisclosed positive constant that differs from block to block.
Values are rounded to {SIGFIG} significant figures and listed in random order.

The blocks come from DIFFERENT series with DIFFERENT unknown scale factors, so
they cannot be pooled. Treat each as a separate problem.

For each block, estimate the 90th, 95th and 99th percentiles OF THE POPULATION
the {N_DRAW} values were drawn from. These are not the percentiles of the {N_DRAW} values
you can see, and you should not assume they lie within their range. Also give a
95% interval for the population 95th percentile.

{body}

Write your answers to predictions.csv with exactly this header:

block,q90,q95,q99,lo,hi

one row per block, {len(blocks)} rows, no other columns and no commentary.
"""
