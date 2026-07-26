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

Every cell is **mean ± 2 SD** over at least three runs (CCAR and its baselines over 8 instances; all other columns over 3). Lower is better everywhere. Cells that had only a single run have been dropped from this matrix and remain in the per-task docs.

| Model | CCAR | Ballistic | Two-body | Three-body | Flyby | Quantile |
| --- | --- | --- | --- | --- | --- | --- |
| Kimi K3 | 0.033 ± 0.082 | | | | | |
| deepseek-v4-flash-free | 0.043 ± 0.102 | | | | | |
| GLM-5.1 | | 7.97 ± 12.79 | 0.04 ± 0.09 | | | |
| Claude Haiku 4.5 | | 37.84 ± 79.83 | 81.20 ± 45.65 | 370 ± 384 | 501 ± 1469 | |
| nemotron-3-ultra:free | | 10.97 ± 10.77 | 653 ± 1568 | 878 ± 1428 | 895 ± 935 | 0.088 ± 0.022 |
| nemotron-3-super:free | | 59.1 ± 1.3 | 75.8 ± 51.8 | 1029 ± 2976 | 522 ± 809 | 0.106 ± 0.021 |
| laguna-m.1:free | | 59.1 ± 1.3 | 33.5 ± 80.3 | 1239 ± 1439 | 783 ± 399 | 0.114 ± 0.093 |
| mimo-v2.5-free | 0.131 ± 0.371 | 10.5 ± 4.0 | 0.07 ± 0.21 | 1150 ± 2445 | 171 ± 215 | 0.122 ± 0.056 |
| *reference (true model)* | *0.013 ± 0.022* | *—* | *0.004 ± 0.002* | *0.018 ± 0.037* | *0.175 ± 0.308* | *—* |
| *naive baseline* | *0.200 ± 0.544* | *17.19 ± 9.33* | *9.86 ± 16.26* | *139.8 ± 336* | *9571 ± 18872* | *0.119 ± 0.034* |

The reference row is not the same kind of thing in every column. For CCAR and the orbital tasks it is the true generating model, an oracle nothing can beat. Ballistic and quantile have no true-model reference (a `—`): ballistic's only anchor is the naive parabola, and quantile's floor is 0 by construction with the naive row being `np.percentile` (type 7).

Several findings survive the caveats and the wide bands. **GLM-5.1 solves two-body at reference level** (0.04, band clear of the naive baseline's 9.86) and clears the naive baseline on ballistic. **Claude Haiku 4.5 fails every orbital task** — worse than the naive baseline on two- and three-body across all three runs. mimo-v2.5 (free) matches GLM-5.1 on two-body (0.07 vs 0.04), the only free model to solve it. And the axes are not one capability: **nemotron-3-ultra is the best model on quantile (± 0.022, tight) yet nearly the worst on two-body (653), coverage 0.08** — a single "capability" number would hide exactly this. On quantile itself, nemotron-3-ultra's tight band and laguna's wide one (± 0.093, a coin flip) mean their similar means are not equally trustworthy. The three-body physics-vs-curve-fit split and the GPT-5.6 Sol effort-hurts result are still real but sit at n=1, so they live in [the orbital doc](docs/tasks/orbital.md) rather than here.

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
