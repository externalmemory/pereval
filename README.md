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
| [CECL lifetime losses](docs/tasks/cecl.md) | synthetic credit portfolio | lifetime allowance, amortization, defaults and prepayments, recoveries, forecast reversion; simulated lifetime-loss prediction intervals |
| [Rating migration under stress](docs/tasks/migration.md) | synthetic credit portfolio | annual-to-quarterly matrix decomposition against the Markov embedding problem, macro-conditional transition matrices, one model projected over three supervisory scenarios |
| [Macro tail quantiles](docs/tasks/quantile.md) | realistic domain | population vs sample quantile, tail extrapolation from 10 observations |
| [Ballistic extrapolation](docs/tasks/ballistic.md) | controlled mechanism | out-of-range extrapolation against velocity-dependent drag |
| [Orbital: two-body, three-body, hyperbolic flyby](docs/tasks/orbital.md) | controlled mechanism | periodic signal recovery, coupled retrograde geometry, angles-only orbit determination |

CCAR and quantile are the original realistic domain tasks. CECL adds a synthetic lifetime-credit-loss task with expected-loss regret as its headline and simulated intervals as diagnostics. Migration is the newest and the hardest of the credit tasks, and the only column where four models score worse than the degenerate answer. All three are in the score table below. The mechanism tasks calibrate the harness across a difficulty gradient with exactly known ground truth.

## Summary Scores

> **Not a leaderboard, and not comparable across columns.** Every column is Winkler regret except Quantile, which is pinball regret, CECL, which is balance-weighted squared error in pool lifetime loss rates, and Migration, which is a distributional distance normalised so that the degenerate answer scores 1.000. The scales differ by orders of magnitude, so a number in one column says nothing about another.
>
> **Within a column, only order-of-magnitude gaps mean anything.** Re-running the same model on byte-identical instances moved cells by 7.4x, and the reproducibility study found swings up to 30x, so any two cells within a factor of a few are the same cell.

Row labels name the model, not the endpoint that served it. A `:free` variant is the same weights under a different serving tier, and where the two have been compared directly they agree: Kimi K3 scored 0.023 free against 0.024 paid on one matched instance. Most of the free endpoints these rows were originally measured on have since been retired, so a cell is reproducible on the paid path and not on the one that produced it ([detail](docs/limitations.md#serving-provenance-is-not-controlled)).

Each cell is the **worst-case (maximum) regret** over at least three runs, CCAR over eight instances. Two rows were measured with three draws per instance instead of one and are reported on a matched convention that keeps them comparable with the rest, footnotes 6 and 8. Lower is better everywhere, and a cell is reported only if none of its runs failed for reasons outside the agent's control. The last column is the **mean rank** (a Borda count within each column), deliberately the only aggregate, since the cells are not comparable across columns. Per-task detail is in the docs linked above, and the caveats behind every number are in [docs/limitations.md](docs/limitations.md).

Every row was served by a hosted provider. A separate attempt to run the suite on one 48 GB desktop machine is written up in [docs/local-models.md](docs/local-models.md) and deliberately kept out of this table: it completes three of the seven tasks, and what stops the other four is the context ceiling of the hardware rather than anything about the model.

| Model | CCAR | CECL⁵ | Migration⁷ | Ballistic | Two-body | Three-body¹ | Flyby | Quantile | Mean rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| *Oracle (true model)* | 0.031 | 0 | *0* | *none* | 0.005 | 0.039 | 0.31 | *none* | *floor* |
| Claude Opus 5.5⁸ | 0.077 | **2.8e-06** | **0.118** | 4.9 | **0.065** | **0.0393** | **24** | 0.083 | **1.75** |
| minimax-m3.1-flash⁶ | 0.080 | 6.5e-06 | 0.629 | **4.3** | 0.069 | 164 | 361 | 0.070 | 2.88 |
| Kimi K3³ | 0.12 | 1.5e-05 | 0.301 | 14 | 0.094 | 3.3 | 50 | 0.077 | 3.38 |
| deepseek-v4-flash-0731⁴ | 0.30 | 1.4e-05 | 0.625 | 14 | 0.30 | 269 | 522 | 0.067 | 4.63 |
| GLM-5.1 | 0.055 | 5.9e-05 | 0.523 | 12 | 0.092 | 436 | 899 | 0.25 | 5.31 |
| mimo-v2.5 | 0.57 | 2.9e-05 | 0.556 | 12 | 0.19 | 2426 | 292 | 0.15 | 6.44 |
| nemotron-3-ultra | 0.27 | 1.6e-05 | 1.214 | 16 | 2429 | 817 | 1356 | 0.099 | 7.63 |
| ling-3.0-flash | 0.193 | 8.7e-03 | 1.612 | 43 | 1556 | 3309 | 591 | 0.076² | 7.88 |
| nemotron-3-super | 0.45 | 5.6e-04 | 1.400 | 60 | 106 | 370 | 918 | 0.12 | 8.38 |
| *Naive baseline* | 0.85 | *0.071* | 0.765 | 22 | 17 | 332 | 20037 | 0.14 | *8.63* |
| Claude Haiku 4.5 | 0.37 | 9.9e-03 | 4.068 | 83 | 105 | 1850 | 1348 | 0.10 | 9.13 |
| *Degenerate answer* | *0.57* | *0.019* | *1.000* | *61* | *2861* | *3019* | *138* | *0.12* | *not ranked* |

**The top of the column separates from the field, and nothing below it is ordered.** Permuting ranks within each column reproduces the observed spread at p < 0.00001 and the observed range at p = 0.00005 over eleven ranked rows and eight columns. Dropping the top three rows still leaves the spread at p = 0.012, and only dropping the top four returns it to noise at p = 0.27, so the eleventh row moved that boundary by one row exactly as the eighth column did: the aggregate now detects that the top four models are genuinely different from the field rather than the top three, and still says nothing about the ordering of the seven rows beneath them ([detail](docs/limitations.md#what-the-eleventh-row-did-to-the-aggregate)).

**Three-body is closed, migration is cut to two-fifths of the previous best, and the flyby is the one column where leading it is not the same as solving it.** On three-body, Opus's 0.0393 sits on the oracle's 0.039 against a next-best of K3's 3.3, and six of the ten ranked models are still worse than the naive harmonic fit, so the column has a ceiling now rather than headroom. On migration, Opus's 0.118 and K3's 0.301 are the only cells inside the competent one-factor reference's 0.368, while four of the ten ranked models score worse than the degenerate answer and Claude Haiku is worse than it by a factor of four. The flyby is the exception: Opus leads it at 24 against K3's 50 and nine of the eleven ranked rows remain worse than the degenerate answer, but the lead rests on three draws of 0.52, 70 and 0.44, so the column is led by a model that fails it outright one pass in three. Two-body, CCAR and CECL, by contrast, are solved by most of the cast, which is the difficulty gradient working as designed.

**The Opus row is three passes over the archived instances, and the variance across them is the finding.** Claude Opus 5.5 ran all eight columns three times at epochs=1 on the same seeds, 29 problems per pass and 87 samples in all, every sample completing and none hitting a limit, for $18.36. It takes five of the eight columns and the aggregate, loses CCAR and ballistic narrowly, and loses quantile outright. Judged on its worst pass rather than its mean, which is the pessimistic reading this suite is built around, only three of those five leads survive: three-body at 0.0432 against 3.3, CECL at 4.47e-06 against 6.5e-06, and migration at 0.204 against 0.301, so a 76x margin and two of roughly 1.5x measured on three instances. The columns are not one distribution. Three-body is the most stable cell the suite has measured, three pass maxima of 0.0388, 0.0432 and 0.0388, while the flyby spans 434x on a single instance, 0.375 then 69.75 then 0.161, with no limit hit in any of the three. Averaging that into one cell is the table's convention and not a description of it: eight of the nine flyby draws land under 0.67 and the ninth is 69.75, which is a model that usually solves the task rather than one that solves it, and the failing draw spent 29 tool calls against the 13 and 10 of the other two to get there. Two defects are reproducible rather than sampled. Migration instance 2 fails `fail_pd_rises_as_rating_falls` in three draws of three, and those are the only three of the row's 144 migration checks to fail; ballistic instance 0 under-covers in three of three, at 0.877, 0.849 and 0.875, and it is simultaneously that column's worst cell, widest interval and worst point error, so it is off-centre rather than narrow. Coverage is reported on 78 of the 87 samples, 66 of them at or above 0.931 against a nominal 0.95 and six below 0.90.

**The three reference rows are the point of the table.** The *oracle* is the true generating model, the floor a perfect answer reaches (ballistic and quantile have none by design). The *naive baseline* is the obvious wrong method, and Claude Haiku falls through it: with migration added it is no longer tied with that row on the aggregate but strictly below it, 9.13 against 8.63. The *degenerate answer* is a single constant with no interval, and it reads differently in every column on purpose: ling is within a few percent of the lowest quantile score in the table and is still worse than a constant on three-body.

CCAR's response law is now drawn per instance rather than fixed and published. That changed the answer key, not the question, so archived runs stay in the column ([detail](docs/limitations.md#the-ccar-response-law-was-public)).

¹ Three-body was re-measured under the corrected circular scorer. Re-running moved cells hard and in both directions on identical instances, so the column inherits run-to-run instability along with the fix ([detail](docs/limitations.md#re-measuring-three-body)).

² ling's 0.076 is among the lowest model scores in that column but is not a better method: on two of three seeds it reproduces the moment-matched normal baseline to four decimal places ([detail](docs/tasks/quantile.md)).

³ Kimi K3 is the only frontier model here and is not the only paid one (Claude Haiku 4.5 is also paid). Its cells come from two serving endpoints, compared on one matched instance ([detail](docs/limitations.md#serving-provenance-is-not-controlled)).

⁴ deepseek-v4-flash-0731 replaces deepseek-v4-flash-free, a different and now-superseded model version whose row had three unmeasured cells. It beats the degenerate constant on every run of every task except two of three on the flyby ([detail](docs/limitations.md#budget-confounds)).

⁵ CECL is reported as `ecl_regret`, balance-weighted squared error in pool lifetime loss rates, which is its headline metric; the simulated prediction intervals are diagnostics rather than a ranking axis, because the shock law is disclosed to the agent ([detail](docs/tasks/cecl.md)). **The column is two groups and a gap, not a gradient.** Six models land between 6.5e-06 and 5.9e-05 with interval coverage 0.93 to 0.96, then nothing until nemotron-3-super at 5.6e-04, ling at 8.7e-03 and Claude Haiku at 9.9e-03, whose coverage falls to 0.84, 0.67 and 0.48. Claude Haiku is also the one model worse than the degenerate answer here. Within the leading six the spread is a factor of nine on three instances, which this suite cannot resolve, so read the column as whether a model built the simulation and calibrated to it. Two rows come from a different serving path than their other cells: mimo-v2.5 and ling-3.0-flash no longer have free endpoints, and nemotron-3-ultra's free endpoint returned HTTP 503 on five consecutive attempts while the paid one completed in three minutes.

⁶ minimax-m3.1-flash was measured with three draws per instance rather than one, so a maximum over its raw samples is taken over fifteen or twenty four draws rather than three and is not the same statistic as the archived cells. Each of its cells is therefore reported on the matched convention: the mean, over every way of drawing one sample per instance, of the maximum across the same instances the other rows use (three for the orbital, ballistic and CECL columns, eight for CCAR, and for quantile three paired single-instance runs on the archived seeds). Its as-measured maxima over all draws are higher, and are CCAR 0.091, CECL 1.2e-05, ballistic 11, two-body 0.102, three-body 361, flyby 1891 and quantile 0.076. Those range over all five orbital instances, two of which are outside the convention. On the archived instances alone the spread reads, as **median (worst)**, CCAR 0.090 (0.091), CECL 4.33e-06 (1.16e-05), ballistic 4.49 (4.64), two-body 0.085 (0.102), three-body 108 (361), flyby 388 (648) and quantile 0.068 (0.076); migration has one draw per instance and so has no spread to report. The median is the median of the same combination distribution the cell averages, so it does not depend on which draw is labelled which pass, and the worst carries the caveat in [docs/limitations.md](docs/limitations.md#three-runs-cannot-support-a-two-sd-band). No sample errored in any column. Its quantile row is weaker evidence than the rest: seven of its nine samples hit the four-hour wall clock, including the one that sets the as-measured maximum, while no archived quantile run was clock-bound, so 0.070 is an upper bound on its regret rather than a measurement of it. Its flyby run time-capped three of fifteen samples, as archived flyby rows also did, and the sample that sets the as-measured 1891 ran to completion uncapped. Its migration cell is outside the matched convention, because that run took one draw per instance like every other row: it is a plain maximum over the same three instances, and 0.629 is the weaker evidence in that column for a different reason. Two of its three instances were cut off by the six-hour wall clock before submitting, instance 0 at 470 messages and instance 1 at 479, and the cell is set by instance 0. Truncation can only have denied a lower-is-better regret more time to improve, so 0.629 bounds its regret from above. Nothing the scorer reports distinguishes a truncated run from a finished one here, since `completion`, `matrix_quarters` and `fit_years` all read as complete on all three; only `sample.limit` on the eval log shows it ([detail](docs/limitations.md#a-time-limited-run-still-produces-a-score)). **This row is two serving paths and the split was not recorded before.** Its migration cell comes from the paid `minimax/minimax-m3.1-flash` endpoint on 2026-10-22, the day `:free` was retired, while its seven other cells come from `:free`. Two further migration runs exist on the free path and are not the published cell: a single-draw run scoring 0.558 and a three-draw run whose matched-convention cell is 0.456.

⁷ Migration is reported as the composite regret the scorer calls `score`: the mean of four components, a Kolmogorov-Smirnov distance over the seven live grades and the cumulative default share, at quarters 4 and 9, each divided by what the degenerate answer scores on it ([detail](docs/tasks/migration.md)). **Both of this column's bracket rows are definitions rather than measurements.** The oracle is exactly 0 because the target is the exact expected cohort distribution under the hidden quarterly law rather than a realized draw, and the degenerate answer is exactly 1.000 because every component is normalised by it. The informative bracket is therefore the *competent* reference, a shrunk one-factor model that scores 0.368 on these three instances and 0.285 over twelve, against the degenerate 1.000. Read on that scale, Claude Opus 5.5 and Kimi K3 are the only rows inside the reference and four ranked models are outside the degenerate answer, which is the most of any column. The *Naive baseline* cell is a single-driver model, the same annual factor estimates regressed on the unemployment level alone and unpenalised; it is worse than the reference on nine of twelve instances, never worse than the degenerate on any, and understates stress in the direction that under-reserves, projecting a severely adverse peak factor below the worst year in its own estimation sample on ten of twelve. One further caveat belongs to the agents rather than the task: the submission contract spells one rating two ways, state `CCC/C` in `predictions.csv` and column `to_CCC_C` in `matrices.csv`, and three of the six nemotron instances lost between ten and fifteen of the sixteen checks to that one character while seven other models handled it.

⁸ Claude Opus 5.5 was measured with three draws per instance rather than one, so its cells use the matched convention of footnote 6: the mean, over every way of drawing one sample per instance, of the maximum across the same instances the other rows use (three for the orbital, ballistic, CECL and migration columns, eight for CCAR, and for quantile three paired single-instance runs on the archived seeds). The spread across the three passes is reported as **median (worst)**, not as a mean with a band, for the reason given in [docs/limitations.md](docs/limitations.md#three-runs-cannot-support-a-two-sd-band). In column order: CCAR 0.074 (0.095), CECL 1.91e-06 (4.47e-06), migration 0.075 (0.204), ballistic 4.81 (6.74), two-body 0.086 (0.089), three-body 0.0388 (0.0432), flyby 0.67 (70), quantile 0.079 (0.098). The median is the median of the same combination distribution the cell averages, so it does not depend on which draw is labelled which pass, and both figures are observations rather than extrapolations. The worst carries one caveat, in [docs/limitations.md](docs/limitations.md#three-runs-cannot-support-a-two-sd-band). The three per-pass maxima behind them, in pass order, are CCAR 0.095 / 0.059 / 0.074, CECL 4.47e-06 / 1.91e-06 / 1.87e-06, migration 0.075 / 0.204 / 0.061, ballistic 4.81 / 6.74 / 3.28, two-body 0.089 / 0.086 / 0.013, three-body 0.0388 / 0.0432 / 0.0388, flyby 0.52 / 69.75 / 0.44, quantile 0.073 / 0.079 / 0.098. Two deviations from the archived convention were applied to every column: `--max-tokens 24000`, because thinking is always on and counts against that limit, and `--token-limit 5000000` as a cost guard rather than a context guard. This is also the only row served by a first-party endpoint rather than an aggregator, so the serving caveat above does not apply to it and it is not evidence that the others are wrong.

## Layout

```
pereval/            Python package: Inspect tasks and scorers
  tasks/ccar/       FRED-calibrated macro + Vasicek generator, task, OLS + Vasicek baselines
  tasks/cecl/       synthetic lifetime loss generator, task, cohort + naive baselines
  tasks/migration/  rating transition generator, task, one-factor + single-driver + no-migration baselines
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

