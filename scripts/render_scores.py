"""Render the README score matrix: the figure, the numbers as text, and the CSV.

Usage: python scripts/render_scores.py
  writes docs/images/scores-{light,dark}.png   the figure the README shows
         docs/scores.csv                       the same cells, machine readable
  rewrites README.md between the scores:begin / scores:end markers

Why a figure and not a coloured markdown table. GitHub's markdown sanitizer
allows none of style, class, bgcolor, color or <font>, so a table cell cannot be
given a background. Per-cell <img> swatches were tried (commit b7b8a5e) and
dropped: they read worse than a rendered table, and the four surfaces GitHub
puts behind a table cell, two themes times zebra striping, confine a swatch
ramp to OKLCH L 0.53 to 0.64, too narrow for fourteen separable steps.

What the figure costs, and how that is paid back. An image cannot be selected,
copied, grepped, read by a screen reader or diffed when a number changes, and
alt text substitutes for none of those: it is not selectable in any browser.
So the README carries the same table as text inside a collapsed <details>
block, which is on the allowlist, and this script also writes docs/scores.csv
so a score change shows up as a reviewable text diff rather than a new PNG.

ROWS below is the single source for all three outputs. Edit it here when a row
is added and re-run.

Colour encodes RANK WITHIN A COLUMN, not the value. The columns are not
comparable with each other and the README's own preamble says only
order-of-magnitude gaps mean anything inside one, so shading by value would
imply a precision the numbers do not carry.

Both ramps are diverging in the orthodox form, green through a neutral
midpoint to red, with lightness monotone across all fourteen steps. The
lightness gradient is what carries the order for a red-green colourblind
reader, and it is not decoration: the ramps these replaced were
near-constant-lightness hue sweeps, and the dark one collapsed to OKLab dE 3.9
between its poles under simulated protanopia, which is no signal at all.

scripts/check_ramp.py gates all of it: APCA 60 and WCAG 4.5 for the ink printed
on every step, lightness monotone, and pole separation under simulated
colour-vision deficiency.
"""
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

COLS = ["CCAR", "CECL", "Migration", "Ballistic", "Two-body", "Three-body", "Flyby", "Quantile"]
NAN = float("nan")

# name, mean rank or None if unranked, cells, display strings
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

# Rows set in italics: reference points rather than models under test. The naive
# baseline is italic and also ranked, since it is a method an agent could choose.
ITALIC = {"Oracle (true model)", "Naive baseline", "Degenerate answer"}

# Diverging: green through a neutral midpoint to red, lightness monotone across
# all fourteen steps so the order survives greyscale and colour-vision
# deficiency. Each mode has its own ramp against its own surface and ink.
LIGHT_RAMP = ["#befabf","#c0f4c0","#c2eec2","#c4e7c4","#c6e1c6","#c8dac8","#cbd3cb",
              "#d5cac8","#dcc2bf","#e2bab6","#e6b3ad","#eaaba5","#eda49d","#ef9d95"]
DARK_RAMP  = ["#003b0a","#003f0b","#104216","#1f4421","#2b462c","#364836","#414941",
              "#534746","#614744","#6e4643","#7a4642","#864541","#914440","#9c433f"]

THEME = {
 "light": dict(ramp=LIGHT_RAMP, surface="#fcfcfb", ink="#1a1a19", muted="#6b6b67",
               ref="#f0efec", grid="#fcfcfb", rankbg="#eceae6"),
 "dark":  dict(ramp=DARK_RAMP,  surface="#1a1a19", ink="#fcfcfb", muted="#b3b3ae",
               ref="#2a2a28", grid="#1a1a19", rankbg="#303030"),
}

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
            best = not is_ref and np.isfinite(v) and RANKS[j][i] == 1
            ax.text(LBL + j * CW + CW / 2, y(i), disp[j], ha="center", va="center",
                    fontsize=6.9, color=t["muted"] if is_ref else t["ink"],
                    style="italic" if is_ref else "normal",
                    fontweight="bold" if best else "normal")
        rtxt = "floor" if i == 0 else ("not ranked" if is_ref else f"{mr:.2f}")
        ax.add_patch(Rectangle((LBL + ncol * CW + 0.012, y(i) - RH / 2 + 0.012),
                               RANKW - 0.024, RH - 0.024, facecolor=t["rankbg"],
                               edgecolor=t["grid"], linewidth=0.9))
        ax.text(LBL + ncol * CW + RANKW / 2, y(i), rtxt, ha="center", va="center",
                fontsize=6.4 if is_ref else 7.2, color=t["muted"] if is_ref else t["ink"],
                style="italic" if is_ref else "normal",
                fontweight="bold" if (not is_ref and mr == BEST_MR) else "normal")

    ax.text(0, -0.78,
            "Shading is rank within each column, best to worst; the columns are not comparable "
            "with each other. Bold is the best cell in a column.\nEvery cell is worst-case regret "
            "over at least three runs. Lower is better.",
            ha="left", va="center", fontsize=6.4, color=t["muted"], linespacing=1.5)
    fig.savefig(path, facecolor=t["surface"], bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)
    print("wrote", path)
ranked = [i for i, r in enumerate(ROWS) if r[1] is not None]
M = np.array([r[2] for r in ROWS], dtype=float)


def rank_in_col(j):
    """Rank among ranked rows only; lower value is better. Ties take the average."""
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
BEST_MR = min(ROWS[i][1] for i in ranked)




# Which task doc owns which column, for the generated per-task results tables.
TASK_DOCS = {
    "docs/tasks/ccar.md": ["CCAR"],
    "docs/tasks/cecl.md": ["CECL"],
    "docs/tasks/migration.md": ["Migration"],
    "docs/tasks/ballistic.md": ["Ballistic"],
    "docs/tasks/orbital.md": ["Two-body", "Three-body", "Flyby"],
    "docs/tasks/quantile.md": ["Quantile"],
}

CSV = Path("docs/scores.csv")
README = Path("README.md")
BEGIN = "<!-- scores:begin (generated by scripts/render_scores.py; do not edit by hand) -->"
END = "<!-- scores:end -->"

FIGURE = """<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/scores-dark.png">
  <img alt="Score matrix: {nrow} rows across {ncol} tasks, {nranked} of the rows ranked, each \
cell shaded by its rank within that column, green for best through to red for worst. The same numbers are in the collapsed \
block below and in docs/scores.csv." src="docs/images/scores-light.png">
</picture>"""


def mean_rank_text(i):
    mr = ROWS[i][1]
    if mr is not None:
        return f"{mr:.2f}"
    return "floor" if i == 0 else "not ranked"


def markdown_table():
    lines = ["| Model | " + " | ".join(COLS) + " | Mean rank |",
             "| --- |" + " --- |" * (len(COLS) + 1)]
    for i, (name, mr, cells, disp) in enumerate(ROWS):
        em = "*" if name in ITALIC else ""
        out = [f"{em}{name}{em}"]
        for j in range(len(COLS)):
            txt = disp[j]
            if mr is not None and np.isfinite(cells[j]) and RANKS[j][i] == 1:
                txt = f"**{txt}**"
            elif em:
                txt = f"*{txt}*"
            out.append(txt)
        rt = mean_rank_text(i)
        if mr is not None and mr == BEST_MR:
            rt = f"**{rt}**"
        out.append(f"{em}{rt}{em}" if em else rt)
        lines.append("| " + " | ".join(out) + " |")
    return "\n".join(lines)


def write_csv():
    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "ranked"] + [c.lower().replace("-", "_") for c in COLS]
                   + [f"{c.lower().replace('-', '_')}_rank" for c in COLS] + ["mean_rank"])
        for i, (name, mr, cells, disp) in enumerate(ROWS):
            ranks = [f"{RANKS[j][i]:g}" if mr is not None and np.isfinite(cells[j]) else ""
                     for j in range(len(COLS))]
            vals = ["" if not np.isfinite(v) else repr(v) for v in cells]
            w.writerow([name, "yes" if mr is not None else "no"] + vals + ranks
                       + [mean_rank_text(i)])
    print(f"wrote {CSV} ({len(ROWS)} rows)")


def task_table(cols):
    """The published column(s) for one task doc, ordered by the first column."""
    js = [COLS.index(c) for c in cols]
    order = sorted(range(len(ROWS)),
                   key=lambda i: float("inf") if not np.isfinite(ROWS[i][2][js[0]])
                   else ROWS[i][2][js[0]])
    lines = ["| Model | " + " | ".join(cols) + " |", "| --- |" + " --- |" * len(cols)]
    for i in order:
        name, mr, cells, disp = ROWS[i]
        em = "*" if name in ITALIC else ""
        out = [f"{em}{name}{em}"]
        for j in js:
            txt = disp[j]
            if mr is not None and np.isfinite(cells[j]) and RANKS[j][i] == 1:
                txt = f"**{txt}**"
            elif em:
                txt = f"*{txt}*"
            out.append(txt)
        lines.append("| " + " | ".join(out) + " |")
    return "\n".join(lines)


def splice(path, block):
    src = Path(path).read_text()
    a, b = src.find(BEGIN), src.find(END)
    if a < 0 or b < 0:
        raise SystemExit(f"markers not found in {path}; expected {BEGIN} and {END}")
    new = src[:a] + BEGIN + "\n\n" + block + "\n\n" + src[b:]
    if new != src:
        Path(path).write_text(new)
        return True
    return False


def write_task_tables():
    for path, cols in TASK_DOCS.items():
        if not Path(path).exists():
            print(f"skipped {path}, not present")
            continue
        if BEGIN not in Path(path).read_text():
            print(f"skipped {path}, no markers yet")
            continue
        changed = splice(path, task_table(cols))
        print(f"{'rewrote' if changed else 'already current'} the table in {path}")


def splice_readme(block):
    src = README.read_text()
    a, b = src.find(BEGIN), src.find(END)
    if a < 0 or b < 0:
        raise SystemExit(f"markers not found in {README}; expected {BEGIN} and {END}")
    new = src[:a] + BEGIN + "\n\n" + block + "\n\n" + src[b:]
    if new == src:
        print(f"{README} already current")
    else:
        README.write_text(new)
        print(f"rewrote the scores block in {README}")


def readme_block():
    return "\n\n".join([
        FIGURE.format(nrow=len(ROWS), ncol=len(COLS), nranked=len(ranked)),
        "Shading is rank within that column, green best through red worst; the "
        + " and ".join(f"*{r[0]}*" for r in ROWS if r[1] is None)
        + " rows are unranked and are shaded neutral. **Bold** marks the best cell in a "
          "column. Mean rank is a Borda count within each column and is deliberately the only "
          "aggregate, since the cells are not comparable across columns.",
        "<details>",
        "<summary>The same table as text, to read, copy or search</summary>",
        markdown_table(),
        "Also in [docs/scores.csv](docs/scores.csv), which carries the per-column ranks as well "
        "and makes a changed score a reviewable diff rather than a new image.",
        "</details>",
    ])


if __name__ == "__main__":
    Path("docs/images").mkdir(parents=True, exist_ok=True)
    render("light", "docs/images/scores-light.png")
    render("dark", "docs/images/scores-dark.png")
    write_csv()
    splice_readme(readme_block())
    write_task_tables()
