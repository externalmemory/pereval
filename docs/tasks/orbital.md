# Orbital Tasks

Three controlled mechanism tasks on a difficulty gradient: two-body (easy), three-body (the suite's hardest for models), and the hyperbolic flyby (the most structurally complex).

```
inspect eval pereval/tasks/orbit/task.py@twobody --model <provider/model>            # needs Docker
inspect eval pereval/tasks/orbit/task.py@threebody -T baseline=kepler --model mockllm/model
inspect eval pereval/tasks/orbit/task.py@hyperbolic -T baseline=od --model mockllm/model
```

## Task

An observer on a planet records angles once per day over a run of consecutive days, and the agent predicts one of those angles for future days, with a 95% prediction interval for a new noisy observation at each one.

**Two-body.** A planet on a fixed elliptical orbit around a star. The recorded angle alpha is the in-plane direction to the star against a fixed distant-star reference. The agent predicts alpha. The signal is strictly periodic and obeys Kepler's second law, fast near periapsis and slow near apoapsis, so an elliptical fit extrapolates it almost exactly.

**Three-body.** A slower outer planet is added and the observer also records beta, its apparent direction as seen from the inner planet. Masses are negligible, so each planet follows its own Kepler orbit and "three-body" names the observed configuration rather than the dynamics. The agent is given t, alpha and beta, and predicts beta. beta is not a Keplerian angle: it is a coupled signal on the synodic period that goes retrograde, like Mars seen from Earth. alpha is essential rather than a distractor, because it pins the observer's position, which is half the geometry needed to reconstruct beta.

**Hyperbolic flyby.** An interstellar object passes through on an unbound trajectory inclined to the planet's orbit. The observer records alpha, beta (the object's apparent azimuth) and gamma (its apparent elevation out of the planet's plane); the object is observable only near passage, so beta and gamma are blank early. The agent predicts gamma over the departure arc. It is non-periodic, so there is no period to find and the FFT that helps on three-body is useless; it is three-dimensional, so inclination and node must be recovered; and it is angles-only orbit determination, a classically ill-conditioned problem in which the observer's own parallax is what breaks the range degeneracy.

Structural complexity is not the same as difficulty for a model. The flyby is mechanical once recognised, so a capable model can grind through it given budget. Three-body is structurally simpler and needs a conceptual leap that fewer models make, and it is the harder of the two in practice.

## Data

Instances are generated host-side by pure-numpy generators; only the observation CSVs enter the sandbox. Measurement noise is added to every recorded angle, and its magnitude is not disclosed. Angles alpha and beta are circular and wrap at 360 degrees; gamma is a bounded elevation and is not.

Only ratios are identifiable from angles alone. For alpha, the period, eccentricity, orientation and periapsis time matter but orbit size does not, since the direction to the star is radius-independent. beta and the flyby geometry additionally depend on orbit size ratios, which Kepler's third law fixes from the period ratios.

Each task ships two reference solvers that bracket it: a naive baseline that ignores the physics (`harmonic` for the orbits, `poly` for the flyby) and a competent reference that fits the true orbits by least squares (`kepler`, `od`). The reference solvers use scipy.

**Flyby instances are selected on the reference succeeding.** A few percent of the fastest, deepest flybys defeat the `od` reference's global fit, so `generate_hyperbolic` advances the seed offset until the reference reaches the noise floor. That is selection on an outcome. Measured over 60 unfiltered draws:

| median | p75 | p90 | max | accepted below 0.5 |
| --- | --- | --- | --- | --- |
| 0.050 | 0.153 | 0.859 | 38.4 | 87% |

The reference row is therefore bounded below the acceptance threshold by construction, though the bound rarely binds, since 87% of draws pass unfiltered. The discarded eighth matters more, because it is not a random eighth: it is the fast, deep flybys this least-squares implementation fails to solve. Whether those are also the instances that best separate agents is unknown, so this column describes agent performance on flybys a competent classical method can handle, which is narrower than "flybys". Draw unfiltered with `-T filter_reference=False`. Each instance records `seed_offset`, `tries`, `reference_regret` and `reference_filtered` in its truth metadata, and the sample id carries the offset, because the instance comes from `seed + offset` and a bare seed does not identify it.

## Scoring

All three tasks use the same oracle-anchored interval scoring as the [ballistic task](ballistic.md#scoring): **Winkler regret** against a Monte Carlo oracle, with MAE, coverage and mean width reported alongside, and a degenerate constant as the non-response anchor. The circular targets are scored on the circle, with the submitted interval localised as a unit so its width survives the move to the branch nearest the true value.

## Results

Worst-case regret over three instances per task, ordered by the two-body column. Lower is better.

<!-- scores:begin (generated by scripts/render_scores.py; do not edit by hand) -->

| Model | Two-body | Three-body | Flyby |
| --- | --- | --- | --- |
| *Oracle (true model)* | *0.005* | *0.039* | *0.31* |
| Claude Opus 5.5 | **0.065** | **0.0393** | **24** |
| minimax-m3.1-flash | 0.069 | 164 | 361 |
| GLM-5.1 | 0.092 | 436 | 899 |
| Kimi K3 | 0.094 | 3.3 | 50 |
| mimo-v2.5 | 0.19 | 2426 | 292 |
| gpt-6-luna | 0.222 | 408 | 45 |
| deepseek-v4-flash-0731 | 0.30 | 269 | 522 |
| *Naive baseline* | *17* | *332* | *20037* |
| Claude Haiku 4.5 | 105 | 1850 | 1348 |
| nemotron-3-super | 106 | 370 | 918 |
| Qwen3.6-35B-A3B (local) | 1193 | 2925 | 916 |
| ling-3.0-flash | 1556 | 3309 | 591 |
| nemotron-3-ultra | 2429 | 817 | 1356 |
| *Degenerate answer* | *2861* | *3019* | *138* |
| gemma-4-26B-A4B (local) | 3377 | 2550 | 1327 |

<!-- scores:end -->

**Two-body is solved, and that is its job.** Most of the cast lands within a small multiple of the oracle, so what the column separates is the models that recover a periodic signal at all from those that do not, and the failures are total rather than marginal.

**Three-body has a ceiling rather than headroom.** Claude Opus 5.5 sits on the oracle, so there is nothing left to win, and the next row is two orders of magnitude behind it. Most of the field is still worse than the naive harmonic fit, which is the shape of a task that needs a leap rather than more effort.

**The flyby is the column where leading it is not solving it.** Eleven of the fourteen ranked rows are worse than the degenerate constant. The leader's cell averages three draws of 0.52, 70 and 0.44, so it is a model that usually solves the task and occasionally fails it outright, reported under a convention that keeps the failure. gpt-6-luna reaches a comparable cell by the opposite route, buying coverage with interval width rather than accuracy ([detail](../models.md#gpt-6-luna)).

A low regret at a coverage near 1.00 is the signature to watch for: it means enormously wide intervals that always contain the truth and are crushed by the width penalty, rather than a fitted orbit.

## Solutions

All three are solved the same way, by writing down the generative geometry and fitting its parameters, and the differences are in what the parameter vector has to hold.

**Two-body:** solve Kepler's equation for the eccentric anomaly, fit period, eccentricity, orientation and periapsis time by least squares, and wrap the residuals on the circle so a 359-to-1 crossing does not read as a 358-degree error. The period is initialised from an FFT or Lomb-Scargle periodogram rather than searched blind.

**Three-body:** fit both planets jointly, nine parameters, with the inner orbit's semimajor axis fixed at 1 because only the ratio is identifiable from angles. alpha constrains the inner orbit and beta the relative geometry, and both residual blocks go into one least-squares objective. Fitting beta alone does not work, which is the leap most rows do not make.

**Flyby:** stage it. Fit the planet's orbit from alpha first, which pins the observer, then fit the object's six elements from beta and gamma with the planet held fixed. Parameterise the hyperbola by perihelion distance and eccentricity rather than semimajor axis, which is negative for an unbound orbit, and use a bounded multistart, because angles-only determination has local minima that a single start falls into.

**Intervals** come from the residual scale of the converged fit, with a robust scale estimate rather than a plain standard deviation, since a multistart that lands badly on one arc leaves outliers behind.

## Limitations

**Three-body cells were produced under a superseded circular scorer** that rewrote submitted intervals wider than half the circle. Re-scoring archived predictions moves affected runs in both directions, 2744 to 726 and 343 to 1086 in two measured cases, so those cells are valid under the rule that produced them and do not compare to new runs. Two-body is verified unaffected ([detail](../limitations.md#circular-intervals-were-rewritten-by-the-scorer)). Re-running under the corrected scorer moved cells hard in both directions on identical instances, so the column carries run-to-run instability along with the fix ([detail](../limitations.md#re-measuring-three-body)).

**Some archived rows cannot be recomputed**, because their `.eval` logs are not in `logs/`. Those cells stand at their published values and were not re-derived.

**The flyby column is conditioned on a solvable anchor**, as described under Data. It is the one place in the suite where instance selection depends on an outcome.
