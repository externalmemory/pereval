# perEval[^1]

**An [Inspect](https://inspect.aisi.org.uk/)-based evaluation suite for quantitative model development tasks.**

> **Status: working prototype.** Example tasks, baselines, and tests are in place; the results shown here are for illustration only due to small sample size. Corners deliberately cut are documented in [docs/limitations.md](docs/limitations.md) rather than hidden.

## Summary

Generic coding and Q&A benchmarks don't test whether an LLM agent can *develop and estimate a statistical model*. perEval probes that corner with tasks drawn from diverse areas including credit risk and macroeconomic loss modeling.

It qualifies a development *process*, not a model. A nine-quarter stress projection cannot be validated against outcomes, because the actuals arrive nine quarters late on a path that is not the scenario path, so the testable object is the process that produced it. [docs/claim.md](docs/claim.md) states what a score supports, what it does not, and how the coverage maps onto SR 26-2.

### Design Principles

1. **Objective verification.** Tasks are designed to have an objectively verifiable target. See [docs/task-design.md](docs/task-design.md) for details.
2. **Scalar regret.** Each task scores a continuous regret against an oracle or reference. A scalar carries more information than a single bit (pass/fail). A task keeps discriminating even when every LLM agent does well on it, or every LLM agent struggles: the regret *magnitudes* separate them.
3. **Pessimistic assessment.** As of mid-2026, credit risk and stress testing models are well within the capabilities of most LLM agents. The question is not whether LLMs can do it at all or how well they do it on average, but whether the *worst case* result is still good enough. Maximum regret (worst result across several runs) is used for ranking.

Scores are anchored against three references rather than one, and a run that failed for reasons outside the agent's control is reported as unmeasured rather than scored. Both rules are set out in [docs/task-design.md](docs/task-design.md#anchoring-and-non-response).

## Quick Start

```bash
pip install -e .
inspect eval pereval/tasks/ccar/task.py --model <provider/model>        # needs Docker
```

Every task also ships reference solvers that run without a model and bracket the score from both ends:

```bash
inspect eval pereval/tasks/ccar/task.py -T baseline=vasicek --model mockllm/model   # competent
inspect eval pereval/tasks/ccar/task.py -T baseline=naive   --model mockllm/model   # floor
```

Use `-T n_instances=N` for many fresh instances with standard errors, and `-T repeats=K` to rerun the agent on the *same* instance, which separates method instability from instance difficulty ([why that is the number to watch](docs/limitations.md#same-instance-stability)). See [docs/setup.md](docs/setup.md) for the Python environment, Docker install (required only for the sandboxed evaluation), and model credentials.

## Tasks

| Task | Type | Challenge |
| --- | --- | --- |
| [CCAR stress loss](docs/tasks/ccar.md) | realistic domain | feature selection under collinearity, transform discovery, bounded functional form, stress extrapolation |
| [Macro tail quantiles](docs/tasks/quantile.md) | realistic domain | population vs sample quantile, tail extrapolation from 10 observations |
| [Ballistic extrapolation](docs/tasks/ballistic.md) | controlled mechanism | out-of-range extrapolation against velocity-dependent drag |
| [Orbital: two-body, three-body, hyperbolic flyby](docs/tasks/orbital.md) | controlled mechanism | periodic signal recovery, coupled retrograde geometry, angles-only orbit determination |

The two domain tasks are the realistic ones. The mechanism tasks calibrate the harness across a difficulty gradient with exactly known ground truth.

## Summary Scores

> **Not a leaderboard, and not comparable across columns.** Every column is Winkler regret except Quantile, which is pinball regret, and the scales differ by orders of magnitude, so a number in one column says nothing about another.

Each cell is the **worst-case (maximum) regret** over at least three runs, CCAR over eight instances. Lower is better everywhere, and a cell is reported only if none of its runs failed for reasons outside the agent's control. The last column is the **mean rank** (a Borda count within each column), deliberately the only aggregate, since the cells are not comparable across columns. Per-task detail is in the docs linked above.

| Model | CCAR¹ | Ballistic | Two-body | Three-body² | Flyby | Quantile | Mean rank |
| --- | --- | --- | --- | --- | --- | --- | --- |
| *Oracle (true model)* | 0.031 | — | 0.005 | 0.039 | 0.31 | — | *floor* |
| GLM-5.1 | 0.055 | 12 | 0.092 | 321 | 899 | 0.25 | **2.25** |
| mimo-v2.5-free | 0.57 | 12 | 0.19 | 2438 | 292 | 0.15 | 3.42 |
| nemotron-3-ultra:free | 0.27 | 16 | 2429 | 1579 | 1356 | 0.099 | 3.83 |
| Claude Haiku 4.5 | 0.37 | 83 | 105 | 575 | 1348 | 0.10 | 4.17 |
| *Naive baseline* | 0.85 | 22 | 17 | 332 | 20037 | 0.14 | *4.33* |
| nemotron-3-super:free | 0.45 | 60 | 106 | 2744 | 918 | 0.12 | 4.75 |
| laguna-m.1:free | 1.1 | 60 | 78 | 2067 | 1014 | 0.16 | 5.25 |
| *Degenerate answer* | *0.57* | *61* | *2861* | *3019* | *138* | *0.12* | *not ranked* |
| ling-3.0-flash:free | n/c⁴ | 43 | 1556 | n/c⁴ | 591 | 0.076⁵ | *not ranked* |
| deepseek-v4-flash-free | 0.14 | 75 | n/m | n/m | n/m³ | 0.17 | *not ranked* |

¹ CCAR measures a **superseded variant**: its response law was fixed and published. The runs are valid, and no agent could have exploited the fixed drivers since none was told them. They are not comparable to current CCAR runs because the replacement also widened the parameter draws and made two of three instances nonlinear ([decomposition](docs/limitations.md#the-ccar-response-law-was-public)).

⁵ ling's 0.076 is the best model score in that column, but it is not a better method: on two of three seeds it reproduces the moment-matched normal baseline to four decimals, and the moment-matched logistic beats it on all three. The task's standing finding is that those naive families beat every literature construction here, and a model that lands on one inherits the result ([detail](docs/tasks/quantile.md)).

⁴ **`n/c` means not comparable, not missing.** ling was added after the CCAR generator and the circular scorer were corrected, so a run today measures the current task while those two columns hold values from the superseded ones. The cell cannot be filled without re-measuring the whole cast, which is why ling is unranked despite being the only model in the table whose every run finished cleanly, well inside its caps (17 to 82 messages), on all four columns it can occupy.

³ deepseek's Flyby runs were re-measured and remain unreported, for a different reason from the other two: two of the three terminated at the 2400 second time cap, so the cell is budget-limited rather than unattempted. The one run that finished clean scored **103.9 against a degenerate anchor of 112.1**, the only sign so far of any agent carrying more information than a constant on that task. At n=1 it is an observation, not a cell.

² Three-body was scored by a **superseded scorer**, which rewrote submitted intervals wider than half the circle. Re-scoring the recorded predictions moves affected runs in both directions, including the matrix's worst cell (nemotron-3-super 2744 to 726) and Haiku's (343 to 1086), so this column does not compare to future runs either ([detail](docs/limitations.md#circular-intervals-were-rewritten-by-the-scorer)). Two-body is verified unaffected: its wide intervals all wrap through zero with the truth inside the arc, which both scorers read identically.

- **`n/m`**: at least one run failed for reasons outside the agent's control, so the cell is unmeasured rather than scored. An agent that works inside its budget and still produces nothing usable is scored, at the degenerate answer. This cost deepseek-v4-flash-free its previously best-in-suite three-body and flyby figures, which were penalties from an upstream failure ([detail](docs/limitations.md#non-response-was-cheaper-than-failure)).
- **Degenerate answer**: one constant point estimate, no interval. It reads differently by column, and that is the point of having it. On Flyby every model with a reportable cell is worse than a constant (292 to 20037 against 138), though see note 3; on two-body and three-body the reverse, by a wide margin. In the Quantile column it is the same estimator as the naive row, `np.percentile`.
- **Mean rank**: GLM-5.1 leads and the naive baseline is fifth of seven. Permuting ranks within each column, the null of no cross-task skill, reproduces the observed spread at p = 0.30, so read this as a description of the table and not a separation of the models ([why the aggregate is weak](docs/limitations.md#the-overall-rank-depends-on-the-task-mix)).
- **Oracle**: the true generating model for CCAR and the orbital tasks. Ballistic and quantile have no true-model reference by design; ballistic is anchored by the naive parabola and quantile's floor is 0 by construction.

## Layout

```
pereval/            Python package: Inspect tasks and scorers
  tasks/ccar/       FRED-calibrated macro + Vasicek generator, task, OLS + Vasicek baselines
  tasks/quantile/   screened FRED YoY snapshot, generator, task, six reference estimators
  tasks/ballistic/  generator, Inspect task, Docker sandbox, quadratic baseline
  tasks/orbit/      two-body, three-body, and hyperbolic-flyby generators, tasks, baselines
  scorers/          oracle-anchored interval scorer (linear and circular), pinball regret
scripts/            FRED enumeration and screening, transcript export, paired analysis
tests/              scorer validation suite + generator/scorer integration
runs/, logs/        archived transcripts and Inspect logs behind every published table
docs/               claim and scope, task design, limitations, per-task scores
```

## License

MIT for this repository's own code. The ballistic task depends on [py-ballisticcalc](https://github.com/o-murphy/py-ballisticcalc) (LGPL-3.0), used as an unmodified installed dependency and not redistributed here, so it imposes no obligations on this code.

[^1]: *pereval* (Russian: перевал, "mountain pass"): the hard route through, not around. It also happens to end in `eval`.
