"""Render the README score matrix as a rank-shaded table, light and dark.

Usage: python scripts/plot_scores.py   (writes docs/images/scores-{light,dark}.png)

The ROWS table below is the single source for both this figure and the README's
markdown table. Edit it here when a row is added, re-run, and copy the cells
across, so the two cannot drift apart.

Colour encodes RANK WITHIN A COLUMN, not the value. The columns are not
comparable with each other and the README's own preamble says only
order-of-magnitude gaps mean anything inside one, so shading by value would
imply a precision the numbers do not carry. Every cell also prints its number,
so colour is a second channel rather than the only one: that is what lets a
green-to-red ramp be used here at all, since green and red of equal chroma sit
at nearly the same lightness and cannot be told apart by lightness alone.

Ramp steps were checked with the dataviz skill's own APCA and WCAG functions;
all fourteen clear APCA 60 and WCAG 4.5 against the ink used on them, in both
modes.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap

COLS = ["CCAR", "CECL", "Migration", "Ballistic", "Two-body", "Three-body", "Flyby", "Quantile"]
NAN = float("nan")

# name, mean rank or None for a reference row, cells, display overrides
ROWS = [
 ("Oracle (true model)",      None, [0.031, 0.0, 0.0, NAN, 0.005, 0.039, 0.31, NAN],
   ["0.031","0","0","none","0.005","0.039","0.31","none"]),
 ("Claude Opus 5.5",          1.88, [0.077, 2.8e-06, 0.118, 4.9, 0.065, 0.0393, 24, 0.083],
   ["0.077","0.0000028","0.118","4.9","0.065","0.0393","24","0.083"]),
 ("minimax-m3.1-flash",       3.00, [0.080, 6.5e-06, 0.629, 4.3, 0.069, 164, 361, 0.070],
   ["0.080","0.0000065","0.629","4.3","0.069","164","361","0.070"]),
 ("Kimi K3",                  3.75, [0.12, 1.5e-05, 0.301, 14, 0.094, 3.3, 50, 0.077],
   ["0.12","0.000015","0.301","14","0.094","3.3","50","0.077"]),
 ("deepseek-v4-flash-0731",   5.13, [0.30, 1.4e-05, 0.625, 14, 0.30, 269, 522, 0.067],
   ["0.30","0.000014","0.625","14","0.30","269","522","0.067"]),
 ("GLM-5.1",                  5.82, [0.055, 5.9e-05, 0.523, 12, 0.092, 436, 899, 0.25],
   ["0.055","0.000059","0.523","12","0.092","436","899","0.25"]),
 ("gpt-6-luna",               6.38, [0.117, 5.7e-04, 1.094, 12, 0.222, 408, 45, 0.128],
   ["0.117","0.00057","1.094","12","0.222","408","45","0.128"]),
 ("mimo-v2.5",                7.32, [0.57, 2.9e-05, 0.556, 12, 0.19, 2426, 292, 0.15],
   ["0.57","0.000029","0.556","12","0.19","2426","292","0.15"]),
 ("nemotron-3-ultra",         9.01, [0.27, 1.6e-05, 1.214, 16, 2429, 817, 1356, 0.099],
   ["0.27","0.000016","1.214","16","2429","817","1356","0.099"]),
 ("ling-3.0-flash",           9.62, [0.193, 8.7e-03, 1.612, 43, 1556, 3309, 591, 0.076],
   ["0.193","0.0087","1.612","43","1556","3309","591","0.076"]),
 ("nemotron-3-super",         9.88, [0.45, 5.6e-04, 1.400, 60, 106, 370, 918, 0.12],
   ["0.45","0.00056","1.400","60","106","370","918","0.12"]),
 ("Naive baseline",          10.38, [0.85, 0.071, 0.765, 22, 17, 332, 20037, 0.14],
   ["0.85","0.071","0.765","22","17","332","20037","0.14"]),
 ("Qwen3.6-35B-A3B (local)", 10.50, [0.3662, 0.001945, 1.267, 14.13, 1193, 2925, 915.7, 3.758e12],
   ["0.366","0.001945","1.267","14","1193","2925","916","3.8e12"]),
 ("Claude Haiku 4.5",        11.12, [0.37, 9.9e-03, 4.068, 83, 105, 1850, 1348, 0.10],
   ["0.37","0.0099","4.068","83","105","1850","1348","0.10"]),
 ("gemma-4-26B-A4B (local)", 11.25, [0.4377, 0.001948, 6.179, 59.32, 3377, 2550, 1327, 0.07751],
   ["0.44","0.001948","6.179","59","3377","2550","1327","0.078"]),
 ("Degenerate answer",        None, [0.57, 0.019, 1.000, 61, 2861, 3019, 138, 0.12],
   ["0.57","0.019","1.000","61","2861","3019","138","0.12"]),
]

LIGHT_RAMP = ["#d8efd6","#e4f2d8","#eef5db","#f6f6dd","#fbf2d6","#fdeacd","#fde1c4",
              "#fbd7bc","#f8cdb5","#f4c3af","#efb9aa","#ebb2a9","#e6ada8","#e1a7a8"]
DARK_RAMP  = ["#1e3a22","#24401f","#2b451e","#33491e","#3c4a1e","#45481f","#4d4420",
              "#543f21","#5a3a22","#5f3423","#632e24","#662826","#682228","#6a1c2a"]

THEME = {
 "light": dict(ramp=LIGHT_RAMP, surface="#fcfcfb", ink="#1a1a19", muted="#6b6b67",
               ref="#f0efec", grid="#fcfcfb", rankbg="#eceae6"),
 "dark":  dict(ramp=DARK_RAMP,  surface="#1a1a19", ink="#fcfcfb", muted="#9a9a95",
               ref="#2a2a28", grid="#1a1a19", rankbg="#303030"),
}

ranked = [i for i, r in enumerate(ROWS) if r[1] is not None]
M = np.array([r[2] for r in ROWS], dtype=float)

def rank_in_col(j):
    """Rank among ranked rows only; lower value is better. Average ties."""
    vals = np.array([M[i, j] for i in ranked])
    order = np.argsort(vals, kind="mergesort")
    rk = np.empty(len(vals))
    rk[order] = np.arange(1, len(vals) + 1)
    for v in set(vals):
        m = vals == v
        if m.sum() > 1:
            rk[m] = rk[m].mean()
    return dict(zip(ranked, rk))

RANKS = {j: rank_in_col(j) for j in range(len(COLS))}

def render(mode, path):
    t = THEME[mode]
    n = len(LIGHT_RAMP)
    nrow, ncol = len(ROWS), len(COLS)
    CW, RH = 1.22, 1.0
    LBL = 3.5          # label column width, in cell units
    RANKW = 1.15
    fig_w = (LBL + ncol * CW + RANKW) * 0.78
    fig_h = (nrow + 3.4) * 0.34
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=200)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])
    ax.set_xlim(0, LBL + ncol * CW + RANKW)
    ax.set_ylim(-1.35, nrow + 1.5)
    ax.axis("off")

    def y(i):
        return nrow - 1 - i + 0.5

    # column headers
    for j, c in enumerate(COLS):
        ax.text(LBL + j * CW + CW / 2, nrow + 0.65, c, ha="center", va="center",
                fontsize=7.1, color=t["ink"], fontweight="bold", rotation=0)
    ax.text(LBL + ncol * CW + RANKW / 2, nrow + 0.65, "Mean\nrank", ha="center", va="center",
            fontsize=7.0, color=t["ink"], fontweight="bold", linespacing=1.15)

    for i, (name, mr, cells, disp) in enumerate(ROWS):
        is_ref = mr is None
        ax.text(LBL - 0.18, y(i), name, ha="right", va="center", fontsize=7.4,
                color=t["muted"] if is_ref else t["ink"],
                style="italic" if is_ref else "normal")
        for j in range(ncol):
            v = cells[j]
            if is_ref or not np.isfinite(v):
                fc = t["ref"]
            else:
                r = RANKS[j][i]
                idx = int(round((r - 1) / (len(ranked) - 1) * (n - 1)))
                fc = t["ramp"][max(0, min(n - 1, idx))]
            ax.add_patch(Rectangle((LBL + j * CW + 0.012, y(i) - RH / 2 + 0.012),
                                   CW - 0.024, RH - 0.024, facecolor=fc,
                                   edgecolor=t["grid"], linewidth=0.9))
            ax.text(LBL + j * CW + CW / 2, y(i), disp[j], ha="center", va="center",
                    fontsize=6.9, color=t["muted"] if is_ref else t["ink"],
                    style="italic" if is_ref else "normal")
        rtxt = "floor" if i == 0 else ("not ranked" if is_ref else f"{mr:.2f}")
        ax.add_patch(Rectangle((LBL + ncol * CW + 0.012, y(i) - RH / 2 + 0.012),
                               RANKW - 0.024, RH - 0.024, facecolor=t["rankbg"],
                               edgecolor=t["grid"], linewidth=0.9))
        ax.text(LBL + ncol * CW + RANKW / 2, y(i), rtxt, ha="center", va="center",
                fontsize=6.4 if is_ref else 7.2, color=t["muted"] if is_ref else t["ink"],
                style="italic" if is_ref else "normal",
                fontweight="normal" if is_ref else "bold")

    ax.text(0, -0.78,
            "Shading is rank within each column, best to worst; the columns are not comparable "
            "with each other.\nEvery cell is worst-case regret over at least three runs. Lower is better.",
            ha="left", va="center", fontsize=6.4, color=t["muted"], linespacing=1.5)
    fig.savefig(path, facecolor=t["surface"], bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)
    print("wrote", path)

render("light", "docs/images/scores-light.png")
render("dark", "docs/images/scores-dark.png")
