# Orbital Tasks

Three controlled mechanism tasks on a difficulty gradient: two-body (easy),
three-body (the suite's hardest for models), and the hyperbolic flyby (the most
structurally complex).

```
inspect eval pereval/tasks/orbit/task.py@twobody --model <provider/model>            # needs Docker
inspect eval pereval/tasks/orbit/task.py@threebody -T baseline=kepler --model mockllm/model
inspect eval pereval/tasks/orbit/task.py@hyperbolic -T baseline=od --model mockllm/model
```

All three use the same host-side generation, sandbox isolation, and oracle-anchored interval scoring as the ballistic task (period=360 for the circular angles alpha and beta, period=None for the bounded elevation gamma). Each has two reference solvers that bracket it: a naive baseline that ignores the physics and a reference that fits the true orbits by least squares. For alpha only the period, eccentricity, orientation, and periapsis time matter (the direction to the star is radius-independent); beta and the flyby geometry also depend on orbit size ratios, fixed by the period ratios through Kepler's third law. The generators are pure numpy; the reference solvers use scipy for the fits.

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

## Scores (Harness Functionality Check, Not a Model Ranking)

A single instance (N = 1, seed 1) per task, no error bars, not a ranking. Lower Winkler regret is better; coverage targets 0.95. The two reference rows are not models: "Harmonic baseline" is the naive Fourier fit and "Kepler reference" fits the true elliptical-orbit model. "fail" means the model did not produce predictions within its message budget and was penalty-scored.

| Row | Two-body regret | Two-body coverage | Three-body regret | Three-body coverage |
| --- | --- | --- | --- | --- |
| GLM-5 | 0.04 | 0.95 | 57.9 | 1.00 |
| GLM-5.1 | 0.04 | 0.95 | 14.9 | 0.92 |
| Kimi-k2.6 | 1258 | 0.50 | fail | — |
| Kimi-k2.7-code | 0.02 | 0.95 | 139.2 | 0.70 |
| GPT-5.6 Sol (frontier, default effort) | — | — | 14.2 | 1.00 |
| GPT-5.6 Sol (frontier, high effort) | — | — | 276.2 | 0.90 |
| Kimi K3 (frontier, default effort) | 0.02 | 0.95 | 0.03 | 0.95 |
| Claude Fable 5 (frontier, default effort) | — | — | 0.03 | 0.95 |
| Harmonic baseline (naive) | 12.1 | 0.69 | 66.0 | 1.00 |
| Kepler reference (true model) | 0.01 | 0.94 | 0.03 | 0.95 |

The two references bracket each task and show what the score means. The Kepler reference reaches the oracle on both tasks (regret 0.01 and 0.03), so both are well posed: the signal is fully recoverable by the right model class. The naive harmonic fit does fine on the periodic two-body signal (12.1, still far above Kepler) but fails badly on three-body (66.0), because the apparent, retrograde inter-planet angle is not a Fourier series in the wrong period, the epicycles mistake. Three-body's difficulty is therefore real headroom, not ill-posedness.

Two-body is nearly solved by three of the four cheap models. Three-body produces an enormous spread that comes down to one thing: whether a model reconstructs the physics or curve-fits and hedges. The cheap models and GPT-5.6 Sol (at default reasoning effort) do the latter, scoring 14 to 139, mostly over-hedging to force coverage toward 1.00; Sol never attempted any orbital modeling in its 24 messages. Claude Fable 5 and Kimi K3, both at default effort, do the former and reach the reference (regret 0.03, coverage 0.95). Fable found the periodicity by FFT, fit two coupled Kepler orbits by least squares, and reconstructed the apparent inter-planet angle; K3 derived the generative geometry from scratch in its reasoning trace, recovering the exact bearing identity beta = theta1 + atan2(r2 sin phi, r2 cos phi - r1), the synodic period, and the observer-on-the-inner-body configuration, then fit and extrapolated it.

So three-body is not beyond the frontier, but it cleanly separates models that recognize and model the coupled retrograde geometry from those that treat it as a generic regression.

Re-running Sol at high reasoning effort made it worse, not better (276.2 versus 14.2): with more effort it committed to an elaborate Fourier extrapolation of beta as an autonomous circa-933-day signal, exactly the epicycle mistake the naive harmonic baseline makes, but with far tighter, more confident intervals. Its point estimates were often within a few to a couple dozen degrees, but the intervals were miscalibrated (roughly ten to twenty-five times too wide against the oracle) and one test day fell 58 degrees outside its interval, where the interval score's tail penalty alone contributed about 1565 of the total. So effort did not buy the missing conceptual leap; it bought a more confident wrong model.

Two frontier models make the leap (Fable 5 and K3) and one does not (Sol, at either effort); every row here is a single instance (N = 1, seed 1).
