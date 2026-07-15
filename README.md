# perEval[^1]

**An [Inspect](https://inspect.aisi.org.uk/)-based evaluation suite for quantitative model development tasks.**

> **Status: early scaffold.** Tasks and scorers are under development; nothing here is a usable benchmark yet.

## Summary

Generic coding and Q&A benchmarks don't test whether an LLM agent can *develop, estimate, and validate a statistical model*. perEval probes that corner with tasks drawn from diverse areas including credit risk and macroeconomic loss modeling.

Macro history is a single realized path (N = 1), so goodness-of-fit on real data can never be the verification target: a model that backtests well on the one path that happened proves little about the next one. Every perEval task is instead constructed so that objective verification exists *by design*: a known data-generating process planted on real covariates, a mathematical identity the solution must satisfy, a statistical guarantee whose coverage is measurable by simulation, or a planted data defect whose detection is mechanically checkable. See [docs/task-design.md](docs/task-design.md) for the full taxonomy.

Planned task themes:

- **Out-of-time discipline**: building models that must be validated on data the agent never sees, with harness-level holdout hygiene.
- **Data vintage traps**: real-time vs. revised macroeconomic series; a legitimate backtest must not use data that didn't exist yet.
- **False summits**: datasets with structural breaks, leakage, or survivorship bias where a fluent, confident, wrong analysis is the natural failure mode.

## Design Principles

1. **Hard to find, easy to verify.** Every task has an objectively checkable target (e.g., recovery of known data-generating-process parameters), not a vibes-based judge.
2. **Headroom over impossibility.** Tasks target the 20–70% frontier-model pass band, where an eval actually discriminates. Item information is p(1−p): tasks every model fails are as uninformative as tasks every model solves.
3. **Validated scorers.** Each scorer ships with its own tests: it must separate a planted-correct solution, a planted-subtly-flawed solution, and a planted-degenerate solution before it is trusted to score a model.
4. **Statistical honesty.** Repeated runs per task, paired-difference comparisons, clustered standard errors. No leaderboards with error bars the sample size can't support.

## Known Limitations and Design Decisions

This is a demonstration of eval construction, not a production benchmark. Corners deliberately cut are documented here rather than hidden.

- **Contamination.** The repo is public, so anything fixed in it can enter training corpora. Every task therefore generates fresh instances per run from a seeded, public generator with per-run randomized parameters (orbital elements, ballistic loads, macro and Vasicek draws), so there are no fixed answers to memorize and every score is computed against freshly drawn ground truth. The residual exposure is structural: a model could learn the generator's functional form from the source. That is largely defanged by design, because knowing the form does not reveal an instance's parameters, which must still be estimated from the provided data, which is the task itself.
- **Sample size.** The example-score tables are single-instance (N = 1) harness checks, not model rankings, and are labeled as such. The harness already supports the honest version: `-T n_instances=N` draws many fresh instances and the scorer emits per-metric means with standard errors. A real comparison would run tens of instances per model with the paired, instance-matched, task-clustered error analysis described in [docs/task-design.md](docs/task-design.md); the mid-field orderings shown here are explicitly not robust to that.
- **Objective scoring, no judge.** All scoring is objective and oracle-anchored (a Winkler interval score against a Monte-Carlo predictive distribution with known parameters), so there is no LLM judge and none of the judge-agreement or judge-circularity problems that dog rubric-based evals. The deliberate cost is that only the numeric prediction is scored, not the reasoning behind it: a model that reaches a well-calibrated answer for the wrong reason is not penalized except insofar as the flaw surfaces out of sample. Rubric scoring of methodology (did it check signs, handle the outlier, justify the transform) would need a judge and is out of scope here by choice.

## Tasks

The CCAR stress loss model is the realistic, domain task. The ballistic and orbital tasks are controlled mechanism tasks that calibrate the harness across a difficulty gradient (easy to hard) with exactly known ground truth.

### CCAR Stress Loss Model

The agent gets a quarterly panel of nine macroeconomic drivers (GDP, unemployment, home price index, BBB spread, S&P 500, DJIA, NASDAQ, VIX, CPI) plus a portfolio default rate over an in-time window, and a 9-quarter forward stress scenario for the same drivers, and must project the default rate (point plus 95% interval) for the stressed quarters. It scores the same oracle-anchored Winkler interval, averaged over the nine quarters.

The data-generating process (documented here and in the source, but never placed in the agent's context, which sees only the two CSVs) is built to reward sound out-of-sample judgment rather than recovering any particular model. Macros come from a diagonal-AR(1)-plus-correlated-innovations generator calibrated to real FRED series (matched persistence, marginal moments, cross-correlations, heavy-tailed crises). The default rate is an extended-Vasicek function of just two of the nine drivers, standardized unemployment level and standardized year-over-year HPI change, so the model must do feature selection under heavy collinearity (three of the nine are near-duplicate equity indices), discover a transform, choose a bounded functional form, and calibrate the systematic uncertainty for the interval. A rare one-quarter systemic crisis (a contaminated-normal COVID/GFC-like event) is added to the observed macros only: the default rate is generated from the fundamental drivers, so a COVID-style unemployment spike appears in the data but the default does not follow it, and a model that fits that quarter naively attenuates its unemployment sensitivity and pays for it under stress. Early quarters have ragged missing data, as on FRED. The scenario pushes the fundamentals past the in-time range, where linear-in-level fits and flipped signs get punished out of sample.

Two references bracket it (`-T baseline=naive|vasicek`): a naive OLS on all nine levels (fragile under stress extrapolation) and a closed-form extended-Vasicek reference with robust outlier handling (near-oracle up to finite-sample error). See [the vasicekfit paper](https://CRAN.R-project.org/package=vasicekfit) for the estimator.

```
inspect eval pereval/tasks/ccar/task.py --model <provider/model>                 # needs Docker
inspect eval pereval/tasks/ccar/task.py -T baseline=vasicek --model mockllm/model
python -m pereval.tasks.ccar.generator --out-dir runs/ccar --seed 1              # inspect one instance
```

### Ballistic Trajectory Extrapolation

The agent receives (category, x, y) training rows and must predict y with 95% prediction intervals at held-out distances beyond the training range. y is projectile drop simulated by py-ballisticcalc with noise on muzzle velocity and launch angle; the held-out window for rifle categories is kept supersonic, so the extrapolation trap is pure velocity-dependent drag. It scores point accuracy (MAE vs the true conditional mean), interval calibration (coverage), and sharpness (width), combined into an oracle-anchored Winkler interval score.

Each instance is generated host-side and only neutral CSVs enter the agent's sandbox: the ballistics engine, the generator, and the ground-truth oracle stay out. What forces the agent to model the data rather than re-simulate it is that category identifiers are opaque and the ballistic parameters are randomized per run, so there is no known load to look up, and any simulation would first require estimating each category's parameters from the training data, which is the task itself. The sandbox additionally has no network, which blocks the weaker shortcuts of installing the exact engine, downloading its drag tables, or querying an online calculator. It does not prevent the agent from recognizing the physics from the data, which is legitimate.

```
inspect eval pereval/tasks/ballistic/task.py --model <provider/model>   # needs Docker
python -m pereval.tasks.ballistic.generator --out-dir runs/demo --seed 1   # inspect one instance
```

### Two-Body Orbit (Angle Prediction)

A planet on a fixed elliptical orbit around a star. Once per day the angle alpha (degrees, in the orbital plane) between the direction to the star and a fixed distant-star reference is recorded, over a run of consecutive days spanning several orbits. The agent predicts alpha for future days. The signal is strictly periodic and follows Kepler's second law (fast near periapsis, slow near apoapsis), so this is the easiest of the three tasks: the structure is a repeating pattern to identify, and a precise elliptical-orbit fit extrapolates it almost exactly. Measurement noise is added to the recorded angles. The target is circular (wraps at 360, so 359 and 1 are two degrees apart) and scored accordingly.

### Three-Body Orbit (Angle Prediction)

A second, slower outer planet is added, and the observer (still on the inner planet) also records beta, the angle to that outer planet. Masses are negligible, so each planet follows its own Kepler orbit; "three-body" refers only to the observed configuration. beta is the apparent direction to the outer planet as seen from the inner one, so it depends on both planets' positions and shows retrograde motion, like Mars seen from Earth. The agent is given t, alpha, and beta and must predict beta for future days. It is harder than the two-body task because beta is not a simple Keplerian angle but a coupled, retrograde signal on the synodic period, and alpha is essential rather than a distractor: it pins the observer's position, which is half the geometry needed to reconstruct beta.

### Hyperbolic Interstellar Flyby (the most complex orbital task)

An interstellar object passes through on a hyperbolic, unbound trajectory whose plane is inclined to the planet's orbit. The observer records alpha (the star, pinning the planet), beta (the object's apparent azimuth), and gamma (its apparent elevation above the planet's plane); the object is only observable near its passage, so beta and gamma are blank early. The agent predicts gamma over the departure arc. It is the most structurally complex of the orbital tasks on three counts: the flyby is non-periodic (no period to find, so the FFT trick that helps on three-body is useless), it is three-dimensional (inclination and node must be recovered), and it is angles-only orbit determination, a classically ill-conditioned problem where the observer's parallax from the planet's motion breaks the range degeneracy. Structural complexity is not the same as difficulty for a model, though: this task is mechanical, recognize the flyby and then grind the orbit determination, so a capable model can work through it given enough budget (a midrange model engaged the correct physics and failed only on its message budget). Three-body, structurally simpler, needs a conceptual leap (recognizing the retrograde coupling) that fewer models make, and so far it is the harder task for models. The flyby's baselines are a naive `poly` extrapolation (a flyby is not a polynomial) and an `od` reference that fits the planet from alpha and then the six-element 3D hyperbolic orbit from beta and gamma. Because a few percent of the fastest flybys defeat the reference's global fit, instances are rejection-sampled: the generator keeps the first seed offset whose reference reaches the noise floor, so every instance has a solvable anchor and generation stays deterministic.

The orbital tasks use the same host-side generation, sandbox isolation, and oracle-anchored interval scoring as the ballistic task (period=360 for the circular angles alpha and beta, period=None for the bounded elevation gamma). Each has two reference solvers that bracket it: a naive baseline that ignores the physics and a reference that fits the true orbits by least squares. For alpha only the period, eccentricity, orientation, and periapsis time matter (the direction to the star is radius-independent); beta and the flyby geometry also depend on orbit size ratios, fixed by the period ratios through Kepler's third law. The generators are pure numpy; the reference solvers use scipy for the fits.

```
inspect eval pereval/tasks/orbit/task.py@twobody --model <provider/model>            # needs Docker
inspect eval pereval/tasks/orbit/task.py@threebody -T baseline=kepler --model mockllm/model
inspect eval pereval/tasks/orbit/task.py@hyperbolic -T baseline=od --model mockllm/model
```

See [docs/setup.md](docs/setup.md) for the Python environment, Docker install (required only for the sandboxed evaluation), and model credentials.

### Example Scores (CCAR Task; Eight Instances, Free Models)

Unlike the single-instance tables below, these are means over eight generated instances with standard errors, so the ordering is more robust (still a small, free-models-only sample). Lower Winkler regret is better; coverage targets 0.95. The Vasicek reference and naive OLS baseline (`-T baseline=vasicek|naive`) bracket the task.

| Row | Winkler regret ± SE | Coverage | Note |
| --- | --- | --- | --- |
| Vasicek reference (true model) | 0.013 ± 0.004 | 0.93 | closed-form extended Vasicek |
| hy3-free | 0.036 ± 0.011 | 0.92 | best free model |
| deepseek-v4-flash-free | 0.084 ± 0.029 | 0.67 | 18 points unpredicted (hit message limit) |
| mimo-v2.5-free | 0.131 ± 0.061 | 0.79 | |
| Naive OLS baseline | 0.200 ± 0.090 | 0.63 | OLS on all nine levels |

Every free model that completed beats the naive OLS baseline, and the best (hy3-free) approaches the near-oracle Vasicek reference, so CCAR is tractable for cheap models: a straightforward regression under noisy data. The task still discriminates the right way, with the fragile linear-on-levels approach worst and the physics-informed reference best. It is the suite's easy realistic task, in deliberate contrast to three-body. (nemotron-3-ultra-free and north-mini-code-free errored on this run and are omitted.)

### Example Scores (Ballistic Task; Harness Functionality Check, Not a Model Ranking)

The numbers below come from a single generated instance (N = 1, seed 1) of the ballistic task and exist only to show that the harness runs end to end and that the scorer discriminates. They are not a ranking of these models. With one instance there are no error bars, so the mid-field ordering is not robust and would likely reorder on another draw. Lower Winkler regret is better; coverage targets 0.95. "Parabola baseline" is the naive quadratic reference (`-T baseline=true`), not a model.

| Model | Winkler regret | MAE (m) | Coverage | Width (m) | Rifle regret | Pistol regret |
| --- | --- | --- | --- | --- | --- | --- |
| GLM-5.1 | 3.34 | 0.76 | 0.87 | 2.86 | 0.93 | 9.66 |
| Kimi-k2.6 | 8.49 | 0.60 | 0.55 | 1.24 | 10.32 | 3.69 |
| GLM-5 | 11.53 | 0.62 | 0.49 | 1.21 | 15.55 | 0.99 |
| Parabola baseline | 21.77 | 0.67 | 0.12 | 0.25 | 19.28 | 28.31 |
| Kimi-k2.7-code | 28.26 | 1.70 | 0.42 | 2.78 | 37.97 | 2.77 |
| Claude Haiku 4.5 | 58.40 | 1.72 | 0.15 | 0.61 | 78.19 | 6.43 |

The only claim is that the harness produces separable, interpretable scores: the spread is dominated by the supersonic rifle sub-task, where overconfident narrow intervals with near-zero coverage are penalized heavily, and the per-class split localizes each model's failure. Turning this into an actual comparison would require many instances per model and the paired, clustered error analysis described in [docs/task-design.md](docs/task-design.md).

### Example Scores (Orbital Tasks; Harness Functionality Check, Not a Model Ranking)

Same caveats: a single instance (N = 1, seed 1) per task, no error bars, not a ranking. Lower Winkler regret is better; coverage targets 0.95. The two reference rows are not models: "Harmonic baseline" is the naive Fourier fit and "Kepler reference" fits the true elliptical-orbit model. "fail" means the model did not produce predictions within its message budget and was penalty-scored.

| Row | Two-body regret | Two-body coverage | Three-body regret | Three-body coverage |
| --- | --- | --- | --- | --- |
| GLM-5 | 0.04 | 0.95 | 57.9 | 1.00 |
| GLM-5.1 | 0.04 | 0.95 | 14.9 | 0.92 |
| Kimi-k2.6 | 1258 | 0.50 | fail | — |
| Kimi-k2.7-code | 0.02 | 0.95 | 139.2 | 0.70 |
| GPT-5.6 Sol (frontier, default effort) | — | — | 14.2 | 1.00 |
| Claude Fable 5 (frontier, default effort) | — | — | 0.03 | 0.95 |
| Harmonic baseline (naive) | 12.1 | 0.69 | 66.0 | 1.00 |
| Kepler reference (true model) | 0.01 | 0.94 | 0.03 | 0.95 |

The two references bracket each task and show what the score means. The Kepler reference reaches the oracle on both tasks (regret 0.01 and 0.03), so both are well posed: the signal is fully recoverable by the right model class. The naive harmonic fit does fine on the periodic two-body signal (12.1, still far above Kepler) but fails badly on three-body (66.0), because the apparent, retrograde inter-planet angle is not a Fourier series in the wrong period, the epicycles mistake. Three-body's difficulty is therefore real headroom, not ill-posedness.

Two-body is nearly solved by three of the four cheap models. Three-body produces an enormous spread that comes down to one thing: whether a model reconstructs the physics or curve-fits and hedges. The cheap models and GPT-5.6 Sol (at default reasoning effort) do the latter, scoring 14 to 139, mostly over-hedging to force coverage toward 1.00; Sol never attempted any orbital modeling in its 24 messages. Claude Fable 5, also at default effort, does the former: it found the periodicity by FFT, fit two coupled Kepler orbits by least squares, reconstructed the apparent inter-planet angle, and reached the reference (regret 0.03, coverage 0.95). So three-body is not beyond the frontier, but it cleanly separates models that recognize and model the coupled retrograde geometry from those that treat it as a generic regression. (Both frontier rows are single instances at default effort; whether higher effort would lift Sol is untested.)

## Layout

```
pereval/            Python package: Inspect tasks and scorers
  tasks/ccar/       FRED-calibrated macro + Vasicek generator, task, OLS + Vasicek baselines
  tasks/ballistic/  generator, Inspect task, Docker sandbox, quadratic baseline
  tasks/orbit/      two-body, three-body, and hyperbolic-flyby generators, tasks, baselines
  scorers/          shared oracle-anchored interval scorer (linear and circular)
tests/              scorer validation suite + generator/scorer integration
```

## License

MIT for this repository's own code. The ballistic task depends on [py-ballisticcalc](https://github.com/o-murphy/py-ballisticcalc) (LGPL-3.0), used as an unmodified installed dependency and not redistributed here, so it imposes no obligations on this code.

-------

[^1]: *pereval* (Russian: перевал, "mountain pass"): the hard route through, not around. It also happens to end in `eval`.

