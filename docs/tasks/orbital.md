# Orbital Tasks

> **Three-body scores below were produced by a superseded scorer** that rewrote submitted intervals wider than half the circle. Re-scoring the archived predictions moves affected runs in both directions (2744 to 726, 343 to 1086), so they are valid under the rule that produced them but do not compare to new runs. Two-body is verified unaffected. See [limitations](../limitations.md#circular-intervals-were-rewritten-by-the-scorer).

Three controlled mechanism tasks on a difficulty gradient: two-body (easy), three-body (the suite's hardest for models), and the hyperbolic flyby (the most structurally complex).

```
inspect eval pereval/tasks/orbit/task.py@twobody --model <provider/model>            # needs Docker
inspect eval pereval/tasks/orbit/task.py@threebody -T baseline=kepler --model mockllm/model
inspect eval pereval/tasks/orbit/task.py@hyperbolic -T baseline=od --model mockllm/model
```

All three use the same host-side generation, sandbox isolation, and oracle-anchored interval scoring as the ballistic task (period=360 for the circular angles alpha and beta, period=None for the bounded elevation gamma). Each has two reference solvers that bracket it: a naive baseline that ignores the physics, and a reference that fits the true orbits by least squares. For alpha only the period, eccentricity, orientation, and periapsis time matter (the direction to the star is radius-independent); beta and the flyby geometry also depend on orbit size ratios, fixed by the period ratios through Kepler's third law. The generators are pure numpy; the reference solvers use scipy for the fits.

## Two-Body Orbit (Angle Prediction)

A planet on a fixed elliptical orbit around a star. Once per day the angle alpha (degrees, in the orbital plane) between the direction to the star and a fixed distant-star reference is recorded, over a run of consecutive days spanning several orbits. The agent predicts alpha for future days.

The signal is strictly periodic and follows Kepler's second law (fast near periapsis, slow near apoapsis), so this is the easiest of the three: the structure is a repeating pattern to identify, and a precise elliptical-orbit fit extrapolates it almost exactly. Measurement noise is added to the recorded angles. The target is circular (wraps at 360, so 359 and 1 are two degrees apart) and scored accordingly.

## Three-Body Orbit (Angle Prediction)

A second, slower outer planet is added, and the observer (still on the inner planet) also records beta, the angle to that outer planet. Masses are negligible, so each planet follows its own Kepler orbit; "three-body" refers only to the observed configuration. beta is the apparent direction to the outer planet as seen from the inner one, so it depends on both planets' positions and shows retrograde motion, like Mars seen from Earth.

The agent is given t, alpha, and beta and must predict beta for future days. It is harder than the two-body task because beta is not a simple Keplerian angle but a coupled, retrograde signal on the synodic period, and alpha is essential rather than a distractor: it pins the observer's position, which is half the geometry needed to reconstruct beta.

## Hyperbolic Interstellar Flyby

An interstellar object passes through on a hyperbolic, unbound trajectory whose plane is inclined to the planet's orbit. The observer records alpha (the star, pinning the planet), beta (the object's apparent azimuth), and gamma (its apparent elevation above the planet's plane); the object is only observable near its passage, so beta and gamma are blank early. The agent predicts gamma over the departure arc.

It is the most structurally complex of the orbital tasks on three counts: the flyby is non-periodic (no period to find, so the FFT trick that helps on three-body is useless), it is three-dimensional (inclination and node must be recovered), and it is angles-only orbit determination, a classically ill-conditioned problem where the observer's parallax from the planet's motion breaks the range degeneracy.

Structural complexity is not the same as difficulty for a model, though: this task is mechanical, recognize the flyby and then grind the orbit determination, so a capable model can work through it given enough budget. An earlier midrange model engaged the correct physics and failed only on its message budget; Kimi K3 completed the full angles-only orbit determination and reached the reference (regret 0.012 at coverage 0.95, single instance seed 1, in 52 messages). Three-body, structurally simpler, needs a conceptual leap that fewer models make, and so far it is the harder task for models.

The flyby's baselines are a naive `poly` extrapolation (a flyby is not a polynomial) and an `od` reference that fits the planet from alpha and then the six-element 3D hyperbolic orbit from beta and gamma. Because a few percent of the fastest flybys defeat the reference's global fit, instances are rejection-sampled: the generator keeps the first seed offset whose reference reaches the noise floor, so every instance has a solvable anchor and generation stays deterministic.

## Flyby Instances Are Selected on the Reference Succeeding

`generate_hyperbolic` advances the seed until the 3D orbit-determination reference reaches the noise floor, so every shipped instance has a working competent anchor. That is selection on an outcome, and it is disclosed here with its measured size rather than left in the source.

Over 60 unfiltered draws the reference regret runs:

| median | p75 | p90 | max | accepted below 0.5 |
| --- | --- | --- | --- | --- |
| 0.050 | 0.153 | 0.859 | 38.4 | 87% |

Two consequences, in order of how much they matter.

The reference row is bounded below the acceptance threshold by construction, so strictly it reports the criterion rather than an observation. In practice the bound rarely binds: 87% of draws pass unfiltered, and the published 0.31 is an ordinary value for an unfiltered draw. This part is real but minor.

The discarded eighth is the part to take seriously, because it is not a random eighth. It is the flybys that this least-squares implementation, with this multistart grid, fails to solve, which are the fast, deep ones. Whether those are also the instances that best separate agents is unknown, so the flyby column describes agent performance on flybys that a competent classical method can handle, which is a narrower population than "flybys".

Draw unfiltered with `-T filter_reference=False` to measure into that tail. Each instance records `seed_offset`, `tries`, `reference_regret` and `reference_filtered` in its truth metadata, and the sample id carries the offset, since the instance comes from `seed + offset` and a bare seed does not identify it.

## Scores (three runs, mean ± 2 SD)

Three instances per task (seed 1, `n_instances=3`), reported as **mean ± 2 SD** across the runs, ordered by the upper end mean + 2 SD, paired on the same three instances. Lower Winkler regret is better; coverage targets 0.95. The reference and naive rows (`-T baseline=kepler|harmonic` for two/three-body, `od|poly` for the flyby) are solvers, not models.

Every row below was recomputed from the archived `.eval` logs under the corrected circular scorer. The baseline and reference rows were re-run host-side and reproduce their previously published values exactly, which is the check that the scorer correction did not move the anchors. Rows whose logs are not in `logs/` could not be recomputed and are listed under each table rather than carried at their superseded values.

**Two-body** (the easy task):

| Row | runs | Winkler regret (mean ± 2 SD) | Coverage |
| --- | --- | --- | --- |
| Kepler reference | 3 | 0.004 ± 0.002 | 0.95 |
| Kimi K3 | 3 | 0.044 ± 0.087 | 0.96 |
| deepseek-v4-flash-0731 | 3 | 0.112 ± 0.328 | 0.94 |
| Harmonic baseline (naive) | 3 | 9.86 ± 16.26 | 0.78 |
| ling-3.0-flash (free) | 3 | 524 ± 1787 | 0.72 |
| nemotron-3-ultra (free) | 3 | 906 ± 2639 | 0.47 |

Not recomputable, worst-case cells from the [README](../../README.md): GLM-5.1 0.092, mimo-v2.5 0.19, laguna-m.1 78, Claude Haiku 4.5 105, nemotron-3-super 106.

**Three-body** (the hard leap):

| Row | runs | Winkler regret (mean ± 2 SD) | Coverage |
| --- | --- | --- | --- |
| Kepler reference | 3 | 0.018 ± 0.037 | 0.95 |
| Kimi K3 | 3 | 1.12 ± 3.81 | 0.89 |
| deepseek-v4-flash-0731 | 3 | 116 ± 273 | 0.72 |
| Harmonic baseline (naive) | 3 | 140 ± 336 | 0.78 |
| nemotron-3-super (free) | 3 | 276 ± 251 | 0.90 |
| GLM-5.1 | 3 | 183 ± 451 | 0.72 |
| nemotron-3-ultra (free) | 3 | 416 ± 788 | 0.49 |
| mimo-v2.5 (free) | 3 | 904 ± 2640 | 0.60 |
| ling-3.0-flash (free) | 3 | 2005 ± 2341 | 0.20 |

Not recomputable, worst-case cells from the README: Claude Haiku 4.5 1850 (re-scored from archived predictions, not re-run), laguna-m.1 2067 (archived on the superseded scorer; the model is no longer served).

**Hyperbolic flyby** (most structurally complex):

| Row | runs | Winkler regret (mean ± 2 SD) | Coverage |
| --- | --- | --- | --- |
| OD reference | 3 | 0.175 ± 0.308 | 0.94 |
| Kimi K3 | 3 | 26.4 ± 41.1 | 0.95 |
| ling-3.0-flash (free) | 3 | 291 ± 550 | 0.53 |
| deepseek-v4-flash-0731 | 3 | 340 ± 536 | 0.43 |
| Polynomial baseline (naive) | 3 | 9571 ± 18872 | 0.15 |

Not recomputable, worst-case cells from the README: mimo-v2.5 292, GLM-5.1 899, nemotron-3-super 918, laguna-m.1 1014, Claude Haiku 4.5 1348, nemotron-3-ultra 1356.

Two-body is solved. Kimi K3 (0.044) and deepseek-0731 (0.112) sit within two orders of magnitude of the Kepler reference and roughly a hundred times better than the naive harmonic fit, and the archived GLM-5.1 and mimo cells are in the same band. The task's job is to be the easy end of the gradient and it does that: what it separates is the models that recover a periodic signal at all from those that do not, and the failures are total rather than marginal, ling and nemotron-3-ultra landing in the hundreds.

The two hard tasks are where the suite still has headroom. **Kimi K3 is the only row that makes the three-body leap**, at 1.12 ± 3.81 against a Kepler reference of 0.018, and the next row is two orders of magnitude behind it. deepseek-0731 at 116 is second and is the only other model to beat the naive harmonic baseline's 140, which most of the cast does not. Everything from nemotron-3-super down is at or beyond the naive fit, and ling at 2005 is worse than answering with a constant.

On the flyby only Kimi K3 (26.4) clears the degenerate answer as a cell. deepseek-0731's 340 mean hides the spread that matters: its three runs were 31.9, 464 and 522, so it beat its instance's constant anchor once and lost to it badly twice. The OD reference reaches 0.175, so the gap between the best agent and a competent solver is about 150x here against about 60x on three-body. This remains the task no model solves.

The baselines behave as designed: the OD and Kepler references reach the oracle, and the naive polynomial flyby fit is astronomically bad (9571 ± 18872, its ± 2 SD exceeding its own mean in the heavy-tailed-regret pattern), confirming a flyby is nothing like a polynomial.

Haiku's two-body failure has a specific signature: coverage 1.00 at a worst case of 105 means it hedges with enormously wide intervals that always contain the truth but are crushed by the width penalty, rather than fitting the orbit, the fast-model reflex of buying coverage with sharpness. That row is one of the archived ones, so the signature is recorded here but not reproducible from the logs.
