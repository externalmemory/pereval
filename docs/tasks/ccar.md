# CCAR Stress Loss Model

The suite's realistic domain task. A regression under noisy data with a response law that is drawn per instance, included deliberately as a contrast to three-body.

```
inspect eval pereval/tasks/ccar/task.py --model <provider/model>                 # needs Docker
inspect eval pereval/tasks/ccar/task.py -T baseline=vasicek --model mockllm/model
inspect eval pereval/tasks/ccar/task.py -T family=threshold                      # pin the form
inspect eval pereval/tasks/ccar/task.py -T n_instances=1 -T repeats=5            # stability
python -m pereval.tasks.ccar.generator --out-dir runs/ccar --seed 1 --family interaction
```

> **These scores stand.** The response law used to be eight constants hard-coded in the
> public generator, which made every instance solvable in closed form with no estimation:
> that exploit scored 0.00014 mean regret against 0.013 for the reference. The law is now
> drawn per instance, including which two macros are non-zero.
>
> That is a change to the answer key, not to the question. No agent was ever told the
> drivers, so the problem an agent faces is unchanged, and the archived runs measure it.
> The parameter draws are centred tightly on the old calibration, so the scale is preserved
> (oracle 0.082 against 0.070, overlapping across seed sets) and old and new runs sit in
> one column. Optional extras that would break that, rotating the functional form and
> splitting scenario severity, are off by default.

## The Task

The agent gets a quarterly panel of nine macroeconomic drivers (GDP, unemployment, home price index, BBB spread, S&P 500, DJIA, NASDAQ, VIX, CPI) plus a portfolio default rate over an in-time window, and a 9-quarter forward stress scenario for the same drivers, and must project the default rate (point plus 95% interval) for the stressed quarters. It scores the same oracle-anchored Winkler interval, averaged over the nine quarters.

## The Data-Generating Process

Documented here and in the source, but never placed in the agent's context, which sees only the two CSVs. It is built to reward sound out-of-sample judgment rather than recovering any particular model.

Macros come from a diagonal-AR(1)-plus-correlated-innovations generator calibrated to real FRED series (matched persistence, marginal moments, cross-correlations, heavy-tailed crises). The default rate is an extended-Vasicek function of just two of the nine drivers, so the model must do feature selection under heavy collinearity (three of the nine are near-duplicate equity indices), discover a transform, choose a bounded functional form, and calibrate the systematic uncertainty for the interval.

Which two drivers, with what coefficients, and in what functional form are all drawn per instance:

- **Drivers.** One macro that rises in a recession (unemployment, BBB spread or VIX) enters as a level; one that falls (HPI, GDP or NASDAQ) enters as a year-over-year change. Nine pairs.
- **Parameters.** `p`, `rho`, `k1` and `k2` are drawn from ranges bracketing the FRED calibration. Standardization is on the pre-stress window, so it is instance-specific and absorbed by any fitted model.
- **Family**, rotated across instances, three of them. `vasicek` is probit-linear. `threshold` adds slope above a kink placed at the 80th to 95th percentile of the in-time driver distribution, so only a handful of in-time quarters sit above it and the nonlinearity is nearly invisible to an in-sample fit while the whole stress path is above it. `interaction` adds a `u1*u2` cross term, which is close to invisible in sample where both drivers sit near their means and decisive under a scenario that pushes them adversely together.

Twenty-seven laws, none of them in the source. A fourth family, `lagged`, was built and dropped: the level drivers are persistent enough and the stress ramp smooth enough that a one or two quarter lag is nearly unidentifiable, and it left the linear reference at 0.0174 against 0.0173 on `vasicek`, so it added a family without adding a distinction.

The scenario overlay ramps each level driver to a target anchored on its marginal mean rather than adding an increment to its last observed value. That is what a supervisory scenario does, and it fixes a defect: with an increment, how adverse the scenario was in standardized terms depended on where the series happened to sit, so a driver that started low could end barely above its own in-time mean and a `threshold` instance could be identical to a `vasicek` one.

A rare one-quarter systemic crisis (a contaminated-normal COVID/GFC-like event) is added to the observed macros only: the default rate is generated from the fundamental drivers, so a COVID-style unemployment spike appears in the data but the default does not follow it, and a model that fits that quarter naively attenuates its unemployment sensitivity and pays for it under stress. Early quarters have ragged missing data, as on FRED. The scenario pushes the fundamentals past the in-time range, where linear-in-level fits and flipped signs get punished out of sample.

## Scenario Severity Is a Factor, Not a Residual

Each instance draws a scenario type, crossed with the response family so a nine-instance dataset covers every combination once: `baseline` leaves the drivers at their unconditional means, `adverse` and `severe` ramp them progressively further. Pin one with `-T scenario=baseline`.

Benign scenarios are there on purpose. A loss model has to be accurate across the whole range, and over-predicting losses in benign conditions is an error rather than a safe choice, because conservatism is not a substitute for accuracy. Keeping only adverse scenarios would test whether a model is pessimistic, not whether it is right.

That is measurable rather than rhetorical. Taking the probit-linear reference and shifting it adverse by a fixed amount, which is what a habitually conservative model does, gives mean Winkler regret over ten instances per scenario:

| Scenario | accurate fit | +0.15 probit | +0.30 | +0.50 |
| --- | --- | --- | --- | --- |
| baseline | **0.037** | 0.041 | 0.092 | 0.348 |
| adverse | 0.200 | 0.083 | **0.070** | 0.205 |
| severe | 1.452 | 1.020 | 0.698 | **0.499** |

On severe scenarios leaning adverse *improves* regret by 2.9x, because a linear fit under-predicts a nonlinear response out of range and the bias partly cancels the misspecification. On benign scenarios the same habit costs 9.4x. A suite scored only on stress would read that first column as skill.

The two factors interact, by construction rather than by accident. A kink acts only above its threshold and a cross term only when both drivers are far from their means, so under `baseline` all three families coincide: over twelve seeds, eleven show both nonlinear families deviating from `vasicek` by less than 0.01, against none under `severe`. That is the trap working. The nonlinearity is invisible in benign conditions and in sample, and decisive exactly where the projection is being relied on.

**Pooling defeats it, which matters more than the table above.** Averaged over all three scenarios, raw regret is *minimised* by a bump of +0.30 (0.287 against 0.563 for the accurate fit), because severe instances carry far larger absolute regret and dominate the mean. Normalising each instance by its own degenerate anchor pulls the optimum back to +0.15 but does not reach zero. So the scenario factor makes conservatism detectable only if the results are read per scenario; a single pooled CCAR number still rewards leaning adverse, and should not be quoted on its own.

## Baselines and Anchors

Four anchors (`-T baseline=naive|vasicek|informed`, plus the degenerate answer computed by the scorer):

- **`naive`**: OLS of the default rate on all nine macro levels. Fragile under stress extrapolation, and now measurably *worse than the degenerate answer*, so it is a floor in the strict sense.
- **`vasicek`**: the competent reference. Probit-transforms the default rate, builds eighteen candidate drivers (all nine macros as levels and as YoY changes), selects among them by backward elimination on sign plausibility and significance, then fits the probit-linear extended-Vasicek model by its closed form with robust outlier handling. See [the vasicekfit paper](https://CRAN.R-project.org/package=vasicekfit) for the estimator.
- **`informed`**: the same fit, handed the true drivers from hidden truth. Not a competitor, a decomposition: no agent has this information.
- **Degenerate**: one constant point estimate, no interval. Reported by the scorer on every run as `degenerate_regret`.

The gap from `informed` up to `vasicek` is the measured cost of feature selection, and it is small relative to the gap down to `naive`. Mean Winkler regret over eight instances per family:

| Anchor | vasicek | threshold | interaction | All |
| --- | --- | --- | --- | --- |
| `informed` (true drivers) | 0.038 | 0.097 | 0.185 | 0.107 |
| `vasicek` (selects drivers) | 0.058 | 0.134 | 0.227 | 0.140 |
| Degenerate answer | 0.869 | 1.505 | 1.312 | 1.229 |
| `naive` OLS on nine levels | 0.947 | 1.358 | 1.392 | 1.233 |

`informed` degrades from 0.038 to 0.185 across the families because it stays probit-linear by design, so it is near-oracle on `vasicek` and competent-but-misspecified on the other two. A reference exact on every instance would only be measuring whether the agent guessed one fixed law. Read the reference per family, not pooled.

**Selecting the right drivers is not achievable and does not need to be.** Backward elimination recovers the exact true pair in 3 of 24 instances. Nine heavily collinear macros over eighty quarters do not identify a pair, and the surviving driver is usually a correlated proxy that moves the same way under the scenario, so the path is still predicted well. Recovering the right variable and predicting the right path are different achievements and only the second is scored. Alternatives measured and rejected, pooled regret over the same 24 instances: exhaustive search over all 153 sign-plausible pairs 0.490, ridge over all eighteen candidates 0.606, lasso 0.669, against backward elimination's 0.430. Shrinkage over the full candidate set does worse than selection, which is what the collinear equity distractors are there to produce: a fit that keeps all of them gets large offsetting coefficients that cancel in sample and stop cancelling once the scenario leaves the observed range.

## Scores (Eight Instances, Fixed-Law Variant)

> **These rows measured the fixed-law task.** They are valid measurements, not contaminated ones, and they stand as a result for that variant. They do not compare to results from the current generator, which is harder. A rerun is pending.
>
> All rows were n=8. The cast was partial (no paid frontier models beyond Kimi K3, no full free roster), and a row for `hy3-free` was removed because the model is no longer served and cannot be reproduced.

Means over eight generated instances, reported as **mean ± 2 SD** (2× the sample standard deviation across the instances, not a confidence interval), ordered by the upper end mean + 2 SD so consistency is rewarded, matching the quantile table. Every row runs the same eight instances (seed 1), so the comparison is paired. Lower is better; coverage targets 0.95.

| Row | Winkler regret (mean ± 2 SD) | Coverage | Note |
| --- | --- | --- | --- |
| Vasicek reference (true model) | 0.013 ± 0.022 | 0.93 | closed-form extended Vasicek |
| GLM-5.1 | 0.029 ± 0.035 | 0.92 | best model, near the reference; tightest band of any model |
| Kimi K3 | 0.033 ± 0.082 | 0.90 | frontier (not free) |
| deepseek-v4-flash-free | 0.043 ± 0.102 | 0.89 | message limit 300 (at 120 it left 18 points unpredicted and scored 0.084) |
| nemotron-3-ultra (free) | 0.085 ± 0.161 | 0.76 | best of the newly-added free models |
| Claude Haiku 4.5 | 0.137 ± 0.274 | 0.74 | strong here despite failing every orbital task |
| nemotron-3-super (free) | 0.136 ± 0.303 | 0.73 | |
| mimo-v2.5 (free) | 0.131 ± 0.371 | 0.79 | one scenario at 0.567 dominates its spread |
| Naive OLS baseline | 0.200 ± 0.544 | 0.63 | OLS on all nine levels |
| laguna-m.1 (free) | 0.216 ± 0.694 | 0.67 | the only model worse than the naive baseline |

Seven of eight models beat the naive OLS baseline, and the best of them approach the near-oracle Vasicek reference, so CCAR is tractable even for cheap models. The task still discriminates the right way, with the fragile linear-on-levels approach near the bottom and the physics-informed reference at the top. The one model that lands *below* the naive baseline is laguna (0.216 vs 0.200), and by the upper-bound ordering it ranks last. The naive regression is a real floor that a weak enough model can fall through.

nemotron-3-ultra is the best of the free models here (0.085), consistent with it being the strongest free model on the quantile task too, though on the orbital tasks it was among the worst, so CCAR and quantile (both statistical-modelling tasks) track together while the physics tasks do not.

The ± 2 SD bands are wide, and honestly so: per-instance regret is heavy-right-tailed because a single badly-missed scenario dominates the Winkler score, so the instance-to-instance spread dwarfs the mean gaps. At n=8 the leading model rows (GLM-5.1 0.029 ± 0.035, Kimi K3 0.033 ± 0.082, deepseek 0.043 ± 0.102, nemotron-3-ultra 0.085 ± 0.161) overlap each other and the Vasicek reference; GLM-5.1's is the tightest band and the only one that clearly separates from the naive baseline, but even it overlaps K3 and deepseek (eight instances do not resolve them). The mean ordering is suggestive; the bands say only the extremes (the reference at the top, laguna at the bottom) are established at this sample size, the same repeated-run lesson the quantile study makes explicit.

deepseek illustrates the budget caveat directly: at message limit 120 it ran out on several instances and scored a penalty-inflated 0.084 at coverage 0.67, but at limit 300 it finishes all eight (130 to 189 messages each) and drops to 0.043, so its earlier row reflected budget, not capability. Most rows here finish well under 120 messages; only deepseek needed the higher cap, and raising it does not advantage the others, which were never budget-constrained. (nemotron-3-ultra-free and north-mini-code-free errored on this run and are omitted.)
