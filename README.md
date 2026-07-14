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

- **Contamination.** This repo is public, so its fixed assets enter future training corpora. A production version would rely on procedural generation from known data-generating processes: fresh instances per run, public generator, no fixed answers. *(To be expanded.)*
- **Sample size.** Task count is deliberately small and narrow. Scores reported here are task-level diagnostics, not model rankings. *(To be expanded.)*
- **Judge reliability.** Where rubric scoring is unavoidable, judge-model agreement and circularity are open issues. *(To be expanded.)*

## Tasks

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

The orbital tasks use the same host-side generation, sandbox isolation, and oracle-anchored interval scoring as the ballistic task; their naive baseline (`-T baseline=true`) is a harmonic (Fourier) regression that does not use Kepler's laws. For alpha only the period, eccentricity, orientation, and periapsis time matter (the direction to the star is radius-independent); beta also depends on the orbit size ratio, but that is fixed by the period ratio through Kepler's third law, so nothing external is needed. Kepler's equation is solved in pure numpy, so no extra dependency.

```
inspect eval pereval/tasks/orbit/task.py@twobody --model <provider/model>     # needs Docker
inspect eval pereval/tasks/orbit/task.py@threebody -T baseline=true --model mockllm/model
```

See [docs/setup.md](docs/setup.md) for the Python environment, Docker install (required only for the sandboxed evaluation), and model credentials.

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

Same caveats: a single instance (N = 1, seed 1) per task, no error bars, not a ranking. Lower Winkler regret is better; coverage targets 0.95. "Harmonic baseline" is the naive Fourier reference (`-T baseline=true`), not a model. "fail" means the model did not produce predictions within its message budget and was penalty-scored.

| Model | Two-body regret | Two-body coverage | Three-body regret | Three-body coverage |
| --- | --- | --- | --- | --- |
| GLM-5 | 0.04 | 0.95 | 57.9 | 1.00 |
| GLM-5.1 | 0.04 | 0.95 | 14.9 | 0.92 |
| Kimi-k2.6 | 1258 | 0.50 | fail | — |
| Kimi-k2.7-code | 0.02 | 0.95 | 139.2 | 0.70 |
| Harmonic baseline | 12.1 | 0.69 | 66.0 | 1.00 |

The two-body signal is strictly periodic, and three of the four models effectively solve it (regret near 0, coverage near 0.95, well below the naive harmonic baseline at 12.1); the fourth produced badly miscalibrated output. The three-body target is the apparent, retrograde inter-planet angle coupled to alpha, and it is much harder: models range from a partial success (GLM-5.1) through over-hedging with tens-of-degrees-wide intervals to force coverage (GLM-5 and the baseline both reach coverage 1.00 that way) to plain wrong (Kimi-k2.7-code) to failing to submit. Across all three tasks the intended difficulty gradient holds: two-body (near-solved) is easier than ballistic, which is easier than three-body.

## Layout

```
pereval/            Python package: Inspect tasks and scorers
  tasks/ballistic/  generator, Inspect task, Docker sandbox, quadratic baseline
  tasks/orbit/      two-body and three-body generators, tasks, harmonic baseline
  scorers/          shared oracle-anchored interval scorer (linear and circular)
tests/              scorer validation suite + generator/scorer integration
```

## License

MIT for this repository's own code. The ballistic task depends on [py-ballisticcalc](https://github.com/o-murphy/py-ballisticcalc) (LGPL-3.0), used as an unmodified installed dependency and not redistributed here, so it imposes no obligations on this code.

-------

[^1]: *pereval* (Russian: перевал, "mountain pass"): the hard route through, not around. It also happens to end in `eval`.

