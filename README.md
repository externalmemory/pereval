# perEval[^1]

**An [Inspect](https://inspect.aisi.org.uk/)-based evaluation suite for quantitative model development tasks.**

> **Status: working prototype.** Multiple tasks, baselines, and tests are in place; scoring is still evolving and the results shown here are illustrative, not a usable benchmark yet.

## What This Is

Generic coding and Q&A benchmarks don't test whether an LLM agent can *develop, estimate, and validate a statistical model*. perEval probes that corner with tasks drawn from diverse areas including credit risk and macroeconomic loss modeling.

Macro history is a single realized path (N = 1), so goodness-of-fit on real data can never be the verification target: a model that backtests well on the one path that happened proves little about the next one. Every perEval task is instead constructed so that objective verification exists *by design*: a known data-generating process planted on real covariates, a mathematical identity the solution must satisfy, a statistical guarantee whose coverage is measurable by simulation, or a planted data defect whose detection is mechanically checkable. See [docs/task-design.md](docs/task-design.md) for the full taxonomy.

### Design Principles

1. **Hard to find, easy to verify.** Every task has an objectively checkable target (e.g., recovery of known data-generating-process parameters), not a vibes-based judge.
2. **Headroom over impossibility.** Tasks target the 20–70% frontier-model pass band, where an eval actually discriminates. Item information is p(1−p): tasks every model fails are as uninformative as tasks every model solves.
3. **Validated scorers.** Each scorer ships with its own tests: it must separate a planted-correct solution, a planted-subtly-flawed solution, and a planted-degenerate solution before it is trusted to score a model.
4. **Statistical honesty.** Repeated runs per task, paired-difference comparisons, clustered standard errors. No leaderboards with error bars the sample size can't support.

Corners deliberately cut are documented in [docs/limitations.md](docs/limitations.md) rather than hidden.

## Quick Start

```bash
pip install -e .
inspect eval pereval/tasks/ccar/task.py --model <provider/model>        # needs Docker
```

Every task also ships reference solvers that run without a model and bracket the score from both ends:

```bash
inspect eval pereval/tasks/ccar/task.py -T baseline=vasicek --model mockllm/model   # near-oracle
inspect eval pereval/tasks/ccar/task.py -T baseline=naive   --model mockllm/model   # floor
```

Use `-T n_instances=N` for many fresh instances with standard errors. See [docs/setup.md](docs/setup.md) for the Python environment, Docker install (required only for the sandboxed evaluation), and model credentials.

## Tasks

| Task | Kind | What it tests |
| --- | --- | --- |
| [CCAR stress loss](docs/tasks/ccar.md) | realistic domain | feature selection under collinearity, transform discovery, bounded functional form, stress extrapolation |
| [Macro tail quantiles](docs/tasks/quantile.md) | realistic domain | population vs sample quantile, tail extrapolation from 10 observations |
| [Ballistic extrapolation](docs/tasks/ballistic.md) | controlled mechanism | out-of-range extrapolation against velocity-dependent drag |
| [Orbital: two-body, three-body, hyperbolic flyby](docs/tasks/orbital.md) | controlled mechanism | periodic signal recovery, coupled retrograde geometry, angles-only orbit determination |

The two domain tasks are the realistic ones. The mechanism tasks calibrate the harness across a difficulty gradient with exactly known ground truth.

## Summary Scores

> **This is a placeholder, not a leaderboard.** Cells are not comparable across
> columns (different metrics on different scales), most are single instances with
> no error bars, blanks mean not run rather than failed, and no column has enough
> instances to support an ordering. It exists to show coverage and that the
> harness discriminates. Per-task tables with the actual caveats are behind the
> links above.

Lower is better everywhere. CCAR is Winkler regret over 8 paired instances; ballistic and orbital are Winkler regret on one instance (seed 1); quantile has no model results yet.

| Model | CCAR | Ballistic | Two-body | Three-body | Flyby | Quantile |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi K3 | 0.033 ± 0.014 | 6.00 | 0.02 | 0.03 | 0.012 | |
| Claude Fable 5 | | 6.16 | | 0.03 | | |
| GPT-5.6 Sol | | | | 14.2 | | |
| GLM-5.1 | | 3.34 | 0.04 | 14.9 | | |
| GLM-5 | | 11.53 | 0.04 | 57.9 | | |
| Kimi-k2.7-code | | 28.26 | 0.02 | 139.2 | | |
| Kimi-k2.6 | | 8.49 | 1258 | fail | | |
| Claude Haiku 4.5 | | 58.40 | | | | |
| hy3-free | 0.036 ± 0.011 | | | | | |
| deepseek-v4-flash-free | 0.043 ± 0.018 | | | | | |
| mimo-v2.5-free | 0.131 ± 0.061 | | | | | |
| *reference* | *0.013 ± 0.004* | | *0.01* | *0.03* | | *0.089* |
| *naive baseline* | *0.200 ± 0.090* | *21.77* | *12.1* | *66.0* | | *0.134* |

The reference row is not the same kind of thing in every column. For CCAR and the orbital tasks it is the true generating model, so it marks the oracle. For quantile there is no true model: the floor is exactly 0 by construction and the reference shown is the best published estimator, which a model beating it would genuinely improve on.

Two observations survive the caveats. Three-body separates models that reconstruct the physics from those that curve-fit and hedge, by two orders of magnitude, and more reasoning effort does not fix it: GPT-5.6 Sol got *worse* at high effort (276.2 versus 14.2) by committing harder to the wrong model. And CCAR is tractable for cheap models, with three of them clustering just above the near-oracle reference, which is why the suite needs the harder tasks to discriminate at the top.

## Layout

```
pereval/            Python package: Inspect tasks and scorers
  tasks/ccar/       FRED-calibrated macro + Vasicek generator, task, OLS + Vasicek baselines
  tasks/quantile/   screened FRED YoY snapshot, generator, task, six reference estimators
  tasks/ballistic/  generator, Inspect task, Docker sandbox, quadratic baseline
  tasks/orbit/      two-body, three-body, and hyperbolic-flyby generators, tasks, baselines
  scorers/          oracle-anchored interval scorer (linear and circular), pinball regret
scripts/            FRED enumeration and screening, transcript export
tests/              scorer validation suite + generator/scorer integration
docs/tasks/         per-task documentation and scores
```

## License

MIT for this repository's own code. The ballistic task depends on [py-ballisticcalc](https://github.com/o-murphy/py-ballisticcalc) (LGPL-3.0), used as an unmodified installed dependency and not redistributed here, so it imposes no obligations on this code.

-------

[^1]: *pereval* (Russian: перевал, "mountain pass"): the hard route through, not around. It also happens to end in `eval`.
