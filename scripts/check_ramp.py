"""Check the figure's two rank ramps against the ink printed on them.

Usage: python scripts/check_ramp.py   (exit 0 if every check passes, 1 otherwise)

Every cell of the figure prints its number on the fill, so the binding
constraint is text contrast against that fill, not mark contrast against a
surface: APCA 60 and WCAG 4.5, each ramp in its own mode, plus the neutral fill
the unranked rows use with its muted ink.

Lightness monotonicity is a gate, not a nicety. Both ramps are diverging, green
through a neutral midpoint to red, and the lightness gradient is what carries
the order for a red-green colourblind reader. The ramps these replaced were
near-constant-lightness hue sweeps: the dark one measured OKLab dE 3.9 between
its poles under simulated protanopia, so its gradient conveyed nothing. Pole
separation under simulated CVD is therefore a gate as well.

Colour maths: sRGB transfer function and WCAG 2 relative luminance; OKLab per
Ottosson (2020); APCA per the WCAG 3 draft; CVD simulation per Machado,
Oliveira and Fernandes (2009) at severity 1.0, the model the OKLab dE
thresholds in common use are calibrated to.
"""
import math
import sys

from render_scores import LIGHT_RAMP, DARK_RAMP, THEME

APCA_MIN = 60.0             # absolute Lc, text on fill
WCAG_MIN = 4.5              # WCAG 2 ratio, text on fill
CVD_TARGET = 8.0            # OKLab dE x100 between a ramp's poles, worst of protan/deutan

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


def apca(text, background):
    """APCA Lc, signed; compare absolute values. Light text on dark reads negative."""
    def y(h):
        r, g, b = (c ** 2.4 for c in hex2srgb(h))
        return 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    ytxt, ybg = y(text), y(background)
    ytxt = 0.0 if ytxt <= 0.022 else ytxt
    ybg = 0.0 if ybg <= 0.022 else ybg
    ytxt = ytxt if ytxt > 0.022 else ytxt + (0.022 - ytxt) ** 1.414
    ybg = ybg if ybg > 0.022 else ybg + (0.022 - ybg) ** 1.414
    if ybg > ytxt:
        sapc = (ybg ** 0.56 - ytxt ** 0.57) * 1.14
        lc = 0.0 if sapc < 0.1 else sapc - 0.027
    else:
        sapc = (ybg ** 0.65 - ytxt ** 0.62) * 1.14
        lc = 0.0 if sapc > -0.1 else sapc + 0.027
    return lc * 100


def check_ramp(label, ramp, ink, ref, muted):
    ok = True
    print(f"\n{label}: {len(ramp)} steps, ink {ink}\n")
    print("  step  fill      OKL     C      APCA         WCAG")
    for n, hexv in enumerate(list(ramp) + [ref], start=1):
        is_ref = n > len(ramp)
        txt = muted if is_ref else ink
        L, C, _ = oklch(hexv)
        a, w = abs(apca(txt, hexv)), contrast(txt, hexv)
        good = a >= APCA_MIN and w >= WCAG_MIN
        ok = ok and good
        print(f"  {'  ref' if is_ref else f'{n:>4}'}  {hexv}  {L:.3f}  {C:.3f}  "
              f"{a:6.1f} {'ok  ' if a >= APCA_MIN else 'FAIL'}  "
              f"{w:.2f}:1 {'ok' if w >= WCAG_MIN else 'FAIL'}")
    Ls = [oklch(h)[0] for h in ramp]
    gaps = [Ls[i + 1] - Ls[i] for i in range(len(Ls) - 1)]
    mono = all(g > 0 for g in gaps) or all(g < 0 for g in gaps)
    ok = ok and mono
    print(f"\n  [{'PASS' if mono else 'FAIL'}] lightness monotone   {Ls[0]:.3f} to {Ls[-1]:.3f},"
          f" smallest adjacent gap {min(abs(g) for g in gaps):.4f}")

    poles = (ramp[0], ramp[-1])
    worst = min(deltaE(*poles, k) for k in ("protan", "deutan"))
    ok = ok and worst >= CVD_TARGET
    print(f"  [{'PASS' if worst >= CVD_TARGET else 'FAIL'}] pole separation      normal "
          f"{deltaE(*poles):.1f}, protan {deltaE(*poles, 'protan'):.1f}, deutan "
          f"{deltaE(*poles, 'deutan'):.1f}, tritan {deltaE(*poles, 'tritan'):.1f}"
          f"   (target {CVD_TARGET:g})")
    return ok


def main():
    ok = True
    for mode, ramp in (("light", LIGHT_RAMP), ("dark", DARK_RAMP)):
        t = THEME[mode]
        ok &= check_ramp(f"{mode} ramp", ramp, t["ink"], t["ref"], t["muted"])
    print(f"\n  -> {'ALL CHECKS PASS' if ok else 'FAILED, fix the marked checks'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    sys.exit(main())
