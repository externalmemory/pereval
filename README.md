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
>
> **Within a column, only order-of-magnitude gaps mean anything.** The question these tasks answer is whether a model can solve the problem at all, not how it ranks. Re-running the same model on byte-identical instances moved cells by 7.4x (nemotron-3-super, 2744 to 370) and the reproducibility study found swings up to 30x, so any two cells within a factor of a few are the same cell. What separates the cases is Kimi K3's 3.3 against everything else's 370 and up on three-body, or a model landing either side of the degenerate answer.

Each cell is the **worst-case (maximum) regret** over at least three runs, CCAR over eight instances. Lower is better everywhere, and a cell is reported only if none of its runs failed for reasons outside the agent's control. The last column is the **mean rank** (a Borda count within each column), deliberately the only aggregate, since the cells are not comparable across columns. Per-task detail is in the docs linked above.

| Model | CCAR | Ballistic | Two-body | Three-body¹ | Flyby | Quantile | Mean rank |
| --- | --- | --- | --- | --- | --- | --- | --- |
| *Oracle (true model)* | 0.031 | — | 0.005 | 0.039 | 0.31 | — | *floor* |
| Kimi K3⁴ | 0.12 | 14 | 0.094 | **3.3** | **50** | 0.077 | **1.83** |
| GLM-5.1 | 0.055 | 12 | 0.092 | 436 | 899 | 0.25 | 3.42 |
| mimo-v2.5-free | 0.57 | 12 | 0.19 | 2426 | 292 | 0.15 | 4.75 |
| ling-3.0-flash:free | 0.193 | 43 | 1556 | 3309 | 591 | 0.076³ | 5.00 |
| nemotron-3-ultra:free | 0.27 | 16 | 2429 | 817 | 1356 | 0.099 | 5.50 |
| nemotron-3-super:free | 0.45 | 60 | 106 | 370 | 918 | 0.12 | 5.58 |
| *Naive baseline* | 0.85 | 22 | 17 | 332 | 20037 | 0.14 | *5.67* |
| Claude Haiku 4.5 | 0.37 | 83 | 105 | 1850 | 1348 | 0.10 | 6.17 |
| laguna-m.1:free | 1.1 | 60 | 78 | 2067 | 1014 | 0.16 | 7.08 |
| *Degenerate answer* | *0.57* | *61* | *2861* | *3019* | *138* | *0.12* | *not ranked* |
| deepseek-v4-flash-free | 0.14 | 75 | n/m | n/m | n/m⁵ | 0.17 | *not ranked* |

¹ Three-body has been **re-measured** under the corrected circular scorer. Six models were re-run (GLM-5.1 uncapped at 400 messages after two of three hit the 150 default), Claude Haiku 4.5 was re-scored from its archived predictions, which all three proved identifiable, and the naive baseline recomputed host-side to 332 unchanged. Re-running moved cells hard and in both directions on identical instances: nemotron-3-super 2744 to 370, nemotron-3-ultra 1579 to 817, Haiku 575 to 1850, mimo 2438 to 2426. Most of that is run-to-run instability rather than the scorer fix, which is the [reproducibility finding](docs/limitations.md#run-to-run-reproducibility) reappearing in the column meant to be getting cleaner.

² laguna keeps its archived value, on the superseded scorer. `poolside/laguna-m.1` is no longer served in any form, so it cannot be re-run, and only one of its three archived runs is identifiable, not the one that sets the cell. Re-scoring moves runs both ways, so this could sit either side of the 3019 degenerate anchor; it does not change laguna's position, which is last on any reading.

³ ling's 0.076 is the lowest model score in that column, but it is not a better method, and the gaps to its neighbours are far inside the noise anyway. The substantive point is an identity rather than a ranking: on two of three seeds it reproduces the moment-matched normal baseline to four decimal places. The task's standing finding is that those naive families beat every literature construction here, and a model that lands on one inherits the result ([detail](docs/tasks/quantile.md)).

⁴ Kimi K3 is the only **frontier** model in the table, and it is not the only paid one: Claude Haiku 4.5 is also paid. It separates from the rest of the cast by an order of magnitude on both hard orbital tasks, which is the only kind of gap this suite can resolve. Three-body: **3.3** against an oracle of 0.039, where the next model is GLM-5.1 at 436. Flyby: worst case **50** over three uncapped runs (49.9, 11.7, 17.6) against a next-best of 292, and every one of the three beats its instance's degenerate answer, which no other model manages once.

Its cells come from two serving paths. CCAR, ballistic, two-body and three-body ran on OpenRouter's paid endpoint; flyby and quantile ran on tokenrouter's free `kimi-k3-free`, after the paid budget was exhausted. The two were checked against each other on one matched instance, two-body instance-0, scoring 0.023 free against 0.024 paid, so they appear to serve the same model; that is one comparison, not a proof.

Quantile is now a complete cell at **0.077** (0.0773, 0.0604, 0.0568). The third seed first ran to the 300-message cap and was discarded; re-run under the raised 600 ceiling it finished in **39 messages** and scored better, so the message count on this task is dominated by which path a run happens to take, not by the ceiling. Two-body (0.094) is level with GLM's 0.092, and quantile is level with ling's 0.076: neither gap is resolvable. The cost post-mortem for the paid half is in [docs/limitations.md](docs/limitations.md#cost-estimates-do-not-survive-a-change-of-limits).

⁵ deepseek's Flyby runs were re-measured and remain unreported, for a different reason from the other two: two of the three terminated at the 2400 second time cap, so the cell is budget-limited rather than unattempted. The one run that finished clean scored **103.9 against a degenerate anchor of 112.1**, the only sign so far of any agent carrying more information than a constant on that task. At n=1 it is an observation, not a cell.

**CCAR is no longer frozen.** Its response law had fixed, published coefficients, which made every instance solvable in closed form; the fix is that the law is now drawn per instance, including which two macros are non-zero. That is a change to the answer key, not to the question: no agent was ever told the drivers, so the problem an agent faces is the one it always faced, and the archived runs measure it. The parameter draws are centred tightly on the old calibration so the scale is preserved (oracle 0.082 against 0.070, overlapping across seed sets). The optional extras that would have broken comparability, rotating the functional form and splitting scenario severity, are off by default and available via `-T family=rotate` and `-T scenario=rotate`.

- **`n/m`**: at least one run failed for reasons outside the agent's control, so the cell is unmeasured rather than scored. An agent that works inside its budget and still produces nothing usable is scored, at the degenerate answer. This cost deepseek-v4-flash-free its previously best-in-suite three-body and flyby figures, which were penalties from an upstream failure ([detail](docs/limitations.md#non-response-was-cheaper-than-failure)).
- **Degenerate answer**: one constant point estimate, no interval. It reads differently by column, and that is the point of having it. Every one of the eight ranked rows is worse than a constant on Flyby, and ling is worse than one on three-body too (3309 against 3019) despite posting the lowest quantile score. The single exception anywhere in the Flyby column is Kimi K3, whose three runs beat their instances' anchors by 2.8x, 10.8x and 6.1x. In the Quantile column it is the same estimator as the naive row, `np.percentile`.
- **Mean rank**: Kimi K3 leads at 1.83 and the naive baseline is seventh of nine. This is the first version of the table where the aggregate is distinguishable from chance: permuting ranks within each column, the null of no cross-task skill, reproduces the observed spread at p = 0.037 and the observed range at p = 0.013. That is down from p = 0.57 before K3's row was complete, but it is one row carrying the signal: remove K3 and the other eight are as unordered as before, so read this as detecting one genuinely different model rather than as a ranking of the rest ([why the aggregate is weak](docs/limitations.md#the-overall-rank-depends-on-the-task-mix)).
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
