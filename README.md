# perEval[^1]

**An [Inspect](https://inspect.aisi.org.uk/)-based evaluation suite for quantitative model development tasks.**

> **Status: working prototype.** Multiple tasks, baselines, and tests are in place; scoring is still evolving and the results shown here are illustrative, not a usable benchmark yet.

## What This Is

Generic coding and Q&A benchmarks don't test whether an LLM agent can *develop, estimate, and validate a statistical model*. perEval probes that corner with tasks drawn from diverse areas including credit risk and macroeconomic loss modeling.

Macro history is a single realized path (N = 1), so goodness-of-fit on real data can never be the verification target: a model that backtests well on the one path that happened proves little about the next one. Every perEval task is instead constructed so that objective verification exists *by design*: a known data-generating process planted on real covariates, a mathematical identity the solution must satisfy, a statistical guarantee whose coverage is measurable by simulation, or a planted data defect whose detection is mechanically checkable. See [docs/task-design.md](docs/task-design.md) for the full taxonomy.

### Design Principles

1. **Hard to find, easy to verify.** Every task has an objectively checkable target (e.g., recovery of known data-generating-process parameters), not a vibes-based judge.
2. **Scalar regret, not pass/fail.** Each task scores a continuous regret against an oracle or reference and reports its run-to-run variability, rather than a one-bit pass. A scalar carries far more than a single bit, so a task keeps discriminating even when every model clears it or every model struggles: the regret *magnitudes* separate them, and so do their *stabilities* — a model that answers consistently and one that gives a different answer each run are distinguishable even at the same mean. Headroom still matters (a task where everything sits on the oracle floor says nothing), but it is headroom in the regret distribution, not a target pass rate.
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

> **Not a leaderboard, and not comparable across columns.** Every column is Winkler
> regret except Quantile, which is pinball regret, and the scales differ by orders
> of magnitude, so a number in one column says nothing about another. What the
> matrix shows is coverage and within-column contrast. Blank means not yet measured
> at three runs, not a failure; single-run exploratory results live in the per-task
> docs behind the links above.

Each cell is the **worst-case (maximum) regret across the runs** — a single, always-positive number that reads more cleanly than a band and reports the worst any run did. It is measured over at least three runs (CCAR over 8 instances, all other columns over 3). Lower is better everywhere. The per-task pages carry the full mean ± 2 SD; single-run-only cells are dropped and live there too.

| Model | CCAR | Ballistic | Two-body | Three-body | Flyby | Quantile |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi K3 | 0.12 | | | | | |
| deepseek-v4-flash-free | 0.14 | | | | | |
| GLM-5.1 | | 12 | 0.092 | | | |
| Claude Haiku 4.5 | 0.37 | 83 | 105 | 575 | 1348 | 0.10 |
| nemotron-3-ultra:free | 0.27 | 16 | 1525 | 1579 | 1356 | 0.099 |
| nemotron-3-super:free | 0.45 | 60 | 106 | 2744 | 918 | 0.12 |
| laguna-m.1:free | 1.1 | 60 | 78 | 2067 | 1014 | 0.16 |
| mimo-v2.5-free | 0.57 | 12 | 0.19 | 2438 | 292 | 0.15 |
| *reference (true model)* | 0.031 | — | 0.005 | 0.039 | 0.31 | — |
| *naive baseline* | 0.85 | 22 | 17 | 332 | 20037 | 0.14 |

The reference row is not the same kind of thing in every column. For CCAR and the orbital tasks it is the true generating model, an oracle nothing can beat. Ballistic and quantile have no true-model reference (a `—`): ballistic's only anchor is the naive parabola, and quantile's floor is 0 by construction with the naive row being `np.percentile` (type 7).

Several findings survive even this worst-case view. **GLM-5.1 solves two-body** (worst run 0.092, against the naive baseline's 17) and clears the naive baseline on ballistic; **mimo-v2.5 (free) also solves it** (0.19), the only free model to. **Claude Haiku 4.5 fails every orbital task**, worse than the naive baseline on two- and three-body. And the axes are not one capability: **nemotron-3-ultra is the best free model on CCAR and quantile yet nearly the worst on two-body** (worst run 1525) — the statistical-modelling tasks and the physics tasks rank models differently, which a single number would erase. The three-body physics-vs-curve-fit split and the GPT-5.6 Sol effort-hurts result sit at n=1, so they live in [the orbital doc](docs/tasks/orbital.md) rather than here, along with the run-to-run stability that a worst-case cell cannot show.

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
