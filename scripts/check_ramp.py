"""Check the README swatch ramp against the four surfaces GitHub puts behind a table cell.

Usage: python scripts/check_ramp.py   (exit 0 if every check passes, 1 otherwise)

A swatch is a graphical object that carries meaning, so WCAG 1.4.11 asks 3:1
against its background. GitHub zebra-stripes markdown tables and ships two
themes, so there are four backgrounds, not one. The other two checks are the
ones that apply to a ramp rather than to a categorical palette: lightness
monotone across the steps, and pole separation under simulated colour-vision
deficiency.

Colour maths: sRGB transfer function and WCAG 2 relative luminance; OKLab per
Ottosson (2020); CVD simulation per Machado, Oliveira and Fernandes (2009) at
severity 1.0, the model the OKLab dE thresholds in common use are calibrated to.
"""
import math
import sys

from render_scores import RAMP

SURFACES = {"github light": "#ffffff", "github light zebra": "#f6f8fa",
            "github dark": "#0d1117", "github dark zebra": "#161b22"}
CONTRAST_MIN = 3.0          # WCAG 1.4.11, non-text contrast
CVD_TARGET = 8.0            # OKLab dE x100 between the ramp's poles

MACHADO = {
    "protan": [[0.152286, 1.052583, -0.204868],
               [0.114503, 0.786281, 0.099216],
               [-0.003882, -0.048116, 1.051998]],
    "deutan": [[0.367322, 0.860646, -0.227968],
               [0.280085, 0.672501, 0.047413],
               [-0.011820, 0.042940, 0.968881]],
    "tritan": [[1.255528, -0.076749, -0.178779],
               [-0.078411, 0.930809, 0.147602],
               [0.004733, 0.691367, 0.303900]]}


def hex2srgb(h):
    h = h.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def s2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin2s(c):
    c = min(1.0, max(0.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def lin(h):
    return tuple(s2lin(c) for c in hex2srgb(h))


def contrast(a, b):
    def y(h):
        r, g, bl = lin(h)
        return 0.2126 * r + 0.7152 * g + 0.0722 * bl
    ya, yb = y(a), y(b)
    lo, hi = min(ya, yb), max(ya, yb)
    return (hi + 0.05) / (lo + 0.05)


def lin2oklab(r, g, b):
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (v ** (1 / 3) if v > 0 else -((-v) ** (1 / 3)) for v in (l, m, s))
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def oklch(h):
    L, a, b = lin2oklab(*lin(h))
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def simulate(h, kind):
    r, g, b = lin(h)
    m = MACHADO[kind]
    out = [m[i][0] * r + m[i][1] * g + m[i][2] * b for i in range(3)]
    return "#%02x%02x%02x" % tuple(round(lin2s(v) * 255) for v in out)


def deltaE(h1, h2, kind=None):
    if kind:
        h1, h2 = simulate(h1, kind), simulate(h2, kind)
    a, b = lin2oklab(*lin(h1)), lin2oklab(*lin(h2))
    return math.dist(a, b) * 100


def main():
    ok = True
    print(f"\nRamp: {len(RAMP)} steps\n")
    print("  step  hex       OKL     C      " + "".join(f"{k:<20}" for k in SURFACES))
    for n, hexv in enumerate(RAMP, start=1):
        label = f"{n:>4}"
        L, C, _ = oklch(hexv)
        cells = []
        for s in SURFACES.values():
            cr = contrast(hexv, s)
            if cr < CONTRAST_MIN:
                ok = False
            cells.append(f"{cr:.2f}:1 {'ok ' if cr >= CONTRAST_MIN else 'FAIL'}".ljust(20))
        print(f"  {label}  {hexv}  {L:.3f}  {C:.3f}  " + "".join(cells))

    Ls = [oklch(h)[0] for h in RAMP]
    gaps = [Ls[i] - Ls[i + 1] for i in range(len(Ls) - 1)]
    mono = all(g > 0 for g in gaps)
    ok = ok and mono
    print(f"\n  [{'PASS' if mono else 'FAIL'}] lightness monotone decreasing"
          f"   span {Ls[0]:.3f} to {Ls[-1]:.3f}, smallest adjacent gap {min(gaps):.4f}")
    print("         adjacent steps are below the 0.06 separation floor by design: the exact")
    print("         rank is in each swatch's alt text and the value is printed beside it")

    poles = (RAMP[0], RAMP[-1])
    worst = min(deltaE(*poles, k) for k in ("protan", "deutan"))
    ok = ok and worst >= CVD_TARGET
    print(f"\n  [{'PASS' if worst >= CVD_TARGET else 'FAIL'}] pole separation"
          f"   normal {deltaE(*poles):.1f}, protan {deltaE(*poles, 'protan'):.1f},"
          f" deutan {deltaE(*poles, 'deutan'):.1f}, tritan {deltaE(*poles, 'tritan'):.1f}"
          f"   (target {CVD_TARGET:g})")

    print(f"\n  -> {'ALL CHECKS PASS' if ok else 'FAILED, fix the marked checks'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    sys.exit(main())
