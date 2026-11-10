"""Render the README score matrix: one swatch image per rank, plus the markdown table.

Usage: python scripts/render_scores.py
  writes docs/images/sw/{01..14,na}.png
  rewrites the table in README.md between the scores:begin / scores:end markers

Why swatches and not a rendered picture of the table. GitHub's markdown
sanitizer allows none of style, class, bgcolor, color or <font>, so a table cell
cannot be given a background. The allowlist does pass <img> with src, alt, width
and height, so each cell carries a small solid swatch next to its number. That
keeps one table rather than a markdown copy and a PNG copy of the same numbers,
and the numbers stay selectable, greppable and diffable.

The ROWS table below is the single source for the figures and the README. Edit
it here when a row is added and re-run.

Colour encodes RANK WITHIN A COLUMN, not the value. The columns are not
comparable with each other and the README's own preamble says only
order-of-magnitude gaps mean anything inside one, so shading by value would
imply a precision the numbers do not carry.

The ramp. A swatch has to read on all four surfaces GitHub puts behind a table
cell, because its markdown tables are zebra-striped and it has two themes:
#ffffff, #f6f8fa, #0d1117 and #161b22. Clearing WCAG 3:1 for graphical objects
against all four at once confines the steps to roughly OKLCH L 0.53 to 0.64,
which is far too narrow for the green-yellow-red ramp this figure used to
carry: yellow at that lightness is olive, and the far end came out brick rather
than red. The ramp is therefore diverging in the orthodox form, two hues around
a neutral midpoint, with lightness monotone decreasing across all fourteen
steps so the order survives greyscale and colour-vision deficiency.

Measured by scripts/check_ramp.py: every step at or above 3.04:1 on all four
surfaces, L monotone from 0.636 to 0.530, and pole separation of OKLab dE 25.8
normal, 20.7 protan, 9.8 deutan against a target of 8. Adjacent steps sit
0.0066 apart in L and are NOT separable by eye. That is deliberate and it is
also unavoidable: thirteen gaps at the 0.06 ordinal floor would need a span of
0.78, and the dual-surface band is 0.106 wide, so a fourteen-step ramp that
works in both themes cannot have distinguishable neighbours. Only the gradient
across the column reads; the exact rank is in each image's alt text and the
value is printed beside it.
"""
import numpy as np
from PIL import Image
from pathlib import Path

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

# Diverging green -> neutral -> red, OKLCH L 0.635 down to 0.529, chroma 0.135 at
# the poles through 0.015 at the midpoint. Validated by scripts/check_ramp.py.
# Unranked rows carry no swatch at all rather than a neutral one, because a grey
# swatch would be indistinguishable from the ramp's own neutral midpoint.
RAMP = ["#4fa054","#579b5a","#5e9660","#659065","#6b8b6b","#718570","#777f77",
        "#837675","#8d6f6c","#956763","#9c605b","#a25852","#a74f4a","#ac4642"]

SWDIR = Path("docs/images/sw")
PX = 16               # source pixels; displayed at 11
DISPLAY = 11
README = Path("README.md")
BEGIN = "<!-- scores:begin (generated by scripts/render_scores.py; do not edit by hand) -->"
END = "<!-- scores:end -->"

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


def write_swatches():
    """One opaque square per rank, plus a neutral one.

    Opaque and square on purpose: GitHub's markdown CSS paints the theme's
    default canvas behind every <img>, so a transparent or rounded swatch would
    show a pale halo on the zebra-striped rows.
    """
    SWDIR.mkdir(parents=True, exist_ok=True)
    out = []
    for n, hexv in enumerate(RAMP, start=1):
        p = SWDIR / f"{n:02d}.png"
        Image.new("RGB", (PX, PX), hexv).save(p, optimize=True)
        out.append(p)
    print(f"wrote {len(out)} swatches to {SWDIR}/ "
          f"({sum(q.stat().st_size for q in out)} bytes total)")


def swatch(rank):
    """<img> for a rank. Unranked cells get nothing, not a neutral swatch."""
    if rank is None:
        return ""
    idx = max(1, min(len(RAMP), int(round(rank))))
    return (f'<img src="{SWDIR}/{idx:02d}.png" width="{DISPLAY}" height="{DISPLAY}"'
            f' alt="rank {rank:g}">')


def markdown_table():
    lines = ["| Model | " + " | ".join(COLS) + " | Mean rank |",
             "| --- |" + " --- |" * (len(COLS) + 1)]
    for i, (name, mr, cells, disp) in enumerate(ROWS):
        em = "*" if name in ITALIC else ""
        is_ranked = mr is not None
        out = [f"{em}{name}{em}"]
        for j in range(len(COLS)):
            r = RANKS[j][i] if (is_ranked and np.isfinite(cells[j])) else None
            txt = disp[j]
            if r == 1:
                txt = f"**{txt}**"
            elif em:
                txt = f"*{txt}*"
            sw = swatch(r)
            out.append(f"{sw} {txt}" if sw else txt)
        rtxt = "floor" if mr is None and i == 0 else ("not ranked" if mr is None else f"{mr:.2f}")
        out.append(f"{em}{rtxt}{em}" if em else rtxt)
        lines.append("| " + " | ".join(out) + " |")
    unranked = " and ".join(f"*{r[0]}*" for r in ROWS if r[1] is None)
    legend = (f"Swatch is rank within that column, {swatch(1)} best through "
              f"{swatch(len(RAMP))} worst; the {unranked} rows are unranked and carry none. "
              "Each swatch repeats its rank in the image alt text, so the ordering does not rest "
              "on colour alone. "
              "**Bold** marks the best cell in a column. Mean rank is a Borda count within each "
              "column and is deliberately the only aggregate, since the cells are not comparable "
              "across columns.")
    return "\n".join(lines) + "\n\n" + legend


def splice_readme(table):
    src = README.read_text()
    a, b = src.find(BEGIN), src.find(END)
    if a < 0 or b < 0:
        raise SystemExit(f"markers not found in {README}; expected {BEGIN} and {END}")
    new = src[:a] + BEGIN + "\n\n" + table + "\n\n" + src[b:]
    if new == src:
        print(f"{README} already current")
    else:
        README.write_text(new)
        print(f"rewrote the table in {README} ({len(ROWS)} rows, {len(COLS)} columns)")


if __name__ == "__main__":
    write_swatches()
    splice_readme(markdown_table())
