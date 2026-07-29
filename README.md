# perEval[^1]

**An [Inspect](https://inspect.aisi.org.uk/)-based evaluation suite for quantitative model development tasks.**

> **Status: working prototype.** Example tasks, baselines, and tests are in place; the results shown here are for illustration only due to small sample size. Corners deliberately cut are documented in [docs/limitations.md](docs/limitations.md) rather than hidden.

## Summary

Generic coding and Q&A benchmarks don't test whether an LLM agent can *develop, estimate, and validate a statistical model*. perEval probes that corner with tasks drawn from diverse areas including credit risk and macroeconomic loss modeling.

### Design Principles

1. **Objective verification.** Tasks are designed to have an objectively verifiable target. See [docs/task-design.md](docs/task-design.md) for details.
2. **Scalar regret.** Each task scores a continuous regret against an oracle or reference. A scalar carries more information than a single bit (pass/fail). A task keeps discriminating even when every LLM agent does well on it, or every LLM agent struggles: the regret *magnitudes* separate them.
3. **Pessimistic assessment.** As of mid-2026, credit risk and stress testing models are well within the capabilities of most LLM agents. The question is not whether LLMs can do it at all or how well they do it on average, but whether the *worst case* result is still good enough. Maximum regret (worst result across several runs) is used for ranking.

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

| Task | Type | Challenge |
| --- | --- | --- |
| [CCAR stress loss](docs/tasks/ccar.md) | realistic domain | feature selection under collinearity, transform discovery, bounded functional form, stress extrapolation |
| [Macro tail quantiles](docs/tasks/quantile.md) | realistic domain | population vs sample quantile, tail extrapolation from 10 observations |
| [Ballistic extrapolation](docs/tasks/ballistic.md) | controlled mechanism | out-of-range extrapolation against velocity-dependent drag |
| [Orbital: two-body, three-body, hyperbolic flyby](docs/tasks/orbital.md) | controlled mechanism | periodic signal recovery, coupled retrograde geometry, angles-only orbit determination |

The two domain tasks are the realistic ones. The mechanism tasks calibrate the harness across a difficulty gradient with exactly known ground truth.

## Summary Scores

> **Not a leaderboard, and not comparable across columns.** Every column is Winkler
> regret except Quantile, which is pinball regret, and the scales differ by orders
> of magnitude, so a number in one column says nothing about another.

Each cell is the **worst-case (maximum) regret across the runs**: a single, always-positive number that reads more cleanly than a band and reports the worst any run did. It is measured over at least three runs (CCAR over 8 instances, all other columns over 3). Lower is better everywhere. More details on exploratory results live in the per-task docs behind the links above.

The last column is the **mean rank** (a Borda count). Within each task the eight rows below (seven models plus the naive baseline) are ranked 1 = best on that task's regret, and the ranks are averaged across the six tasks. This is deliberately the *only* aggregate. The cells are not comparable across columns, so magnitudes cannot be averaged, and the reproducibility experiment showed the magnitudes are unstable anyway (up to 30× on a rerun). Rows are ordered by mean rank.

| Model | CCAR | Ballistic | Two-body | Three-body | Flyby | Quantile | Mean rank |
| --- | --- | --- | --- | --- | --- | --- | --- |
| *Reference (true model)* | 0.031 | — | 0.005 | 0.039 | 0.31 | — | *oracle* |
| GLM-5.1 | 0.055 | 12 | 0.092 | 321 | 899 | 0.25 | **2.75** |
| deepseek-v4-flash-free | 0.14 | 75 | 5.3 | 13 | 17 | 0.17 | 3.50 |
| mimo-v2.5-free | 0.57 | 12 | 0.19 | 2438 | 292 | 0.15 | 3.92 |
| nemotron-3-ultra:free | 0.27 | 16 | 1525 | 1579 | 1356 | 0.099 | 4.50 |
| Claude Haiku 4.5 | 0.37 | 83 | 105 | 575 | 1348 | 0.10 | 5.00 |
| *Naive baseline* | 0.85 | 22 | 17 | 332 | 20037 | 0.14 | *5.00* |
| nemotron-3-super:free | 0.45 | 60 | 106 | 2744 | 918 | 0.12 | 5.42 |
| laguna-m.1:free | 1.1 | 60 | 78 | 2067 | 1014 | 0.16 | 5.92 |

The reference row is not the same kind of thing in every column. For CCAR and the orbital tasks it is the true generating model, an oracle nothing can beat. Ballistic and quantile have no true-model reference because of the task design. Ballistic's only anchor is the naive parabola, and quantile's floor is 0 by construction with the naive row being `np.percentile` (type 7).

Three of the seven models sit at or below the naive baseline overall. Haiku ties it, nemotron-3-super and laguna fall below it. Being excellent on some tasks does not save a model that is catastrophic on others, because averaging ranks across a balanced task set is unforgiving of a blind spot. Only GLM-5.1 is a genuine generalist (mean rank 2.75, top or near-top on five of six tasks, weak only on quantile). The naive baseline outranking a third of the cast is the honest headline of the whole exercise: a linear regression that does nothing clever beats several LLM agents once you score them across tasks instead of cherry-picking the one they happen to win.

The mean rank is a Borda count over this particular task mix, so it tilts toward physics-capable models. On the statistical tasks alone nemotron-3-ultra leads and GLM-5.1 drops out of the top four. The rank is a property of the task portfolio, not the models; see [docs/limitations.md](docs/limitations.md#the-overall-rank-depends-on-the-task-mix).

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

[^1]: *pereval* (Russian: перевал, "mountain pass"): the hard route through, not around. It also happens to end in `eval`.
