# CCAR Stress Loss Model

The suite's realistic domain task, and its easiest. A straightforward regression
under noisy data, included deliberately as a contrast to three-body.

```
inspect eval pereval/tasks/ccar/task.py --model <provider/model>                 # needs Docker
inspect eval pereval/tasks/ccar/task.py -T baseline=vasicek --model mockllm/model
python -m pereval.tasks.ccar.generator --out-dir runs/ccar --seed 1              # inspect one instance
```

## The Task

The agent gets a quarterly panel of nine macroeconomic drivers (GDP, unemployment, home price index, BBB spread, S&P 500, DJIA, NASDAQ, VIX, CPI) plus a portfolio default rate over an in-time window, and a 9-quarter forward stress scenario for the same drivers, and must project the default rate (point plus 95% interval) for the stressed quarters. It scores the same oracle-anchored Winkler interval, averaged over the nine quarters.

## The Data-Generating Process

Documented here and in the source, but never placed in the agent's context, which sees only the two CSVs. It is built to reward sound out-of-sample judgment rather than recovering any particular model.

Macros come from a diagonal-AR(1)-plus-correlated-innovations generator calibrated to real FRED series (matched persistence, marginal moments, cross-correlations, heavy-tailed crises). The default rate is an extended-Vasicek function of just two of the nine drivers, standardized unemployment level and standardized year-over-year HPI change, so the model must do feature selection under heavy collinearity (three of the nine are near-duplicate equity indices), discover a transform, choose a bounded functional form, and calibrate the systematic uncertainty for the interval.

A rare one-quarter systemic crisis (a contaminated-normal COVID/GFC-like event) is added to the observed macros only: the default rate is generated from the fundamental drivers, so a COVID-style unemployment spike appears in the data but the default does not follow it, and a model that fits that quarter naively attenuates its unemployment sensitivity and pays for it under stress. Early quarters have ragged missing data, as on FRED. The scenario pushes the fundamentals past the in-time range, where linear-in-level fits and flipped signs get punished out of sample.

## Baselines

Two references bracket it (`-T baseline=naive|vasicek`): a naive OLS on all nine levels (fragile under stress extrapolation) and a closed-form extended-Vasicek reference with robust outlier handling (near-oracle up to finite-sample error). See [the vasicekfit paper](https://CRAN.R-project.org/package=vasicekfit) for the estimator.

## Scores (Eight Instances)

> Provisional. These predate the current task set and will be regenerated once
> the suite is finalised. A row for `hy3-free` was removed because the model is
> no longer served and the result cannot be reproduced.

Unlike the single-instance tables for the other tasks, these are means over eight generated instances with standard errors, so the ordering is more robust (still a small sample). Every row runs the same eight instances (seed 1), so the comparison is paired. Lower Winkler regret is better; coverage targets 0.95.

| Row | Winkler regret ± SE | Coverage | Note |
| --- | --- | --- | --- |
| Vasicek reference (true model) | 0.013 ± 0.004 | 0.93 | closed-form extended Vasicek |
| Kimi K3 | 0.033 ± 0.014 | 0.90 | frontier (not free); best model |
| deepseek-v4-flash-free | 0.043 ± 0.018 | 0.89 | message limit 300 (at 120 it left 18 points unpredicted and scored 0.084) |
| mimo-v2.5-free | 0.131 ± 0.061 | 0.79 | |
| Naive OLS baseline | 0.200 ± 0.090 | 0.63 | OLS on all nine levels |

Every model that completed beats the naive OLS baseline, and the best of them approach the near-oracle Vasicek reference, so CCAR is tractable even for cheap models. The task still discriminates the right way, with the fragile linear-on-levels approach worst and the physics-informed reference best.

The two non-reference model rows (Kimi K3 0.033, deepseek-v4-flash-free 0.043) cluster just above the Vasicek reference and are statistically indistinguishable from one another. K3, the one frontier model here, is nominally best, and its coverage (0.90) dips slightly below target, dragged by one of the eight scenarios where it was overconfident (regret 0.12, coverage 0.68).

deepseek illustrates the budget caveat directly: at message limit 120 it ran out on several instances and scored a penalty-inflated 0.084 at coverage 0.67, but at limit 300 it finishes all eight (130 to 189 messages each) and drops to 0.043, so its earlier row reflected budget, not capability. Most rows here finish well under 120 messages; only deepseek needed the higher cap, and raising it does not advantage the others, which were never budget-constrained. (nemotron-3-ultra-free and north-mini-code-free errored on this run and are omitted.)
