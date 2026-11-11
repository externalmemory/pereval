# CCAR Stress Loss Model

The suite's realistic domain task. A regression under noisy data with a response law drawn per instance, included deliberately as a contrast to three-body.

```
inspect eval pereval/tasks/ccar/task.py --model <provider/model>                 # needs Docker
inspect eval pereval/tasks/ccar/task.py -T baseline=vasicek --model mockllm/model
inspect eval pereval/tasks/ccar/task.py -T family=threshold                      # pin the form
inspect eval pereval/tasks/ccar/task.py -T n_instances=1 -T repeats=5            # stability
python -m pereval.tasks.ccar.generator --out-dir runs/ccar --seed 1 --family interaction
```

## Task

The agent gets a quarterly panel of nine macroeconomic drivers (GDP, unemployment, home price index, BBB spread, S&P 500, DJIA, NASDAQ, VIX, CPI) together with a portfolio default rate over an in-time window, plus a nine-quarter forward stress scenario for the same drivers. It must project the default rate, point estimate and 95% interval, for each stressed quarter.

## Data

The generating process is documented here and in the source but never placed in the agent's context, which sees only the two CSVs.

Macros come from a diagonal-AR(1)-plus-correlated-innovations generator calibrated to real FRED series, matching persistence, marginal moments, cross-correlations and heavy-tailed crises. The default rate is an extended-Vasicek function of just two of the nine drivers, so a solution has to do feature selection under heavy collinearity (three of the nine are near-duplicate equity indices), discover a transform, choose a bounded functional form, and calibrate systematic uncertainty for the interval.

Which two drivers, with what coefficients, in what functional form, are drawn per instance:

- **Drivers.** One macro that rises in a recession (unemployment, BBB spread or VIX) enters as a level; one that falls (HPI, GDP or NASDAQ) enters as a year-over-year change. Nine pairs.
- **Parameters.** `p`, `rho`, `k1` and `k2` are drawn from ranges bracketing the FRED calibration. Standardisation is on the pre-stress window, so it is instance-specific and is absorbed by any fitted model.
- **Family**, rotated across instances. `vasicek` is probit-linear. `threshold` adds slope above a kink placed at the 80th to 95th percentile of the in-time driver distribution, so only a handful of in-time quarters sit above it and the nonlinearity is nearly invisible to an in-sample fit while the whole stress path is above it. `interaction` adds a `u1*u2` cross term, close to invisible in sample where both drivers sit near their means and decisive under a scenario that pushes them adversely together.

Twenty-seven laws, none of them in the source.

The scenario overlay ramps each level driver to a target anchored on its marginal mean rather than adding an increment to its last observed value, which is what a supervisory scenario does. A rare one-quarter systemic crisis, a contaminated-normal COVID- or GFC-like event, is added to the **observed macros only**: the default rate is generated from the fundamental drivers, so an unemployment spike appears in the data and the defaults do not follow it. A model that fits that quarter naively attenuates its unemployment sensitivity and pays for it under stress. Early quarters carry ragged missing data, as on FRED, and the scenario pushes the fundamentals past the in-time range, where linear-in-level fits and flipped signs are punished out of sample.

**Scenario severity is a factor, not a residual.** Each instance draws `baseline`, `adverse` or `severe`, crossed with the response family so a nine-instance dataset covers every combination once. Benign scenarios are there on purpose: over-predicting losses in benign conditions is an error, not a safe choice, and keeping only adverse scenarios would test whether a model is pessimistic rather than whether it is right. Taking the probit-linear reference and shifting it adverse by a fixed amount, which is what a habitually conservative model does, gives mean Winkler regret over ten instances per scenario:

| Scenario | accurate fit | +0.15 probit | +0.30 | +0.50 |
| --- | --- | --- | --- | --- |
| baseline | **0.037** | 0.041 | 0.092 | 0.348 |
| adverse | 0.200 | 0.083 | **0.070** | 0.205 |
| severe | 1.452 | 1.020 | 0.698 | **0.499** |

Leaning adverse improves severe-scenario regret by 2.9x, because a linear fit under-predicts a nonlinear response out of range and the bias partly cancels the misspecification. The same habit costs 9.4x on benign scenarios. The two factors interact by construction: a kink acts only above its threshold and a cross term only when both drivers are far from their means, so under `baseline` all three families coincide, and over twelve seeds eleven show both nonlinear families within 0.01 of `vasicek`, against none under `severe`.

## Scoring

The same oracle-anchored **Winkler interval regret** as the [ballistic task](ballistic.md#scoring), averaged over the nine stressed quarters, with MAE, coverage and width reported alongside.

Four anchors bracket it (`-T baseline=naive|vasicek|informed`, plus the degenerate answer the scorer computes on every run):

- **`naive`**: OLS of the default rate on all nine macro levels. Fragile under stress extrapolation, and measurably worse than the degenerate answer, so it is a floor in the strict sense.
- **`vasicek`**: the competent reference. Probit-transforms the default rate, builds eighteen candidate drivers (all nine macros as levels and as YoY changes), selects among them by backward elimination on sign plausibility and significance, then fits the probit-linear extended-Vasicek model in closed form with robust outlier handling ([estimator](https://CRAN.R-project.org/package=vasicekfit)).
- **`informed`**: the same fit handed the true drivers from hidden truth. Not a competitor but a decomposition, since no agent has this information.
- **Degenerate**: one constant point estimate, no interval.

Mean Winkler regret over eight instances per family:

| Anchor | vasicek | threshold | interaction | All |
| --- | --- | --- | --- | --- |
| `informed` (true drivers) | 0.038 | 0.097 | 0.185 | 0.107 |
| `vasicek` (selects drivers) | 0.058 | 0.134 | 0.227 | 0.140 |
| Degenerate answer | 0.869 | 1.505 | 1.312 | 1.229 |
| `naive` OLS on nine levels | 0.947 | 1.358 | 1.392 | 1.233 |

`informed` degrades from 0.038 to 0.185 across the families because it stays probit-linear by design, so it is near-oracle on `vasicek` and competent-but-misspecified on the other two. A reference exact on every instance would only measure whether the agent guessed one fixed law, so read the reference per family rather than pooled.

## Results

Worst-case regret over eight instances. Lower is better.

<!-- scores:begin (generated by scripts/render_scores.py; do not edit by hand) -->

| Model | CCAR |
| --- | --- |
| *Oracle (true model)* | *0.031* |
| GLM-5.1 | **0.055** |
| Claude Opus 5.5 | 0.077 |
| minimax-m3.1-flash | 0.080 |
| gpt-6-luna | 0.117 |
| Kimi K3 | 0.12 |
| ling-3.0-flash | 0.193 |
| nemotron-3-ultra | 0.27 |
| deepseek-v4-flash-0731 | 0.30 |
| Qwen3.6-35B-A3B (local) | 0.366 |
| Claude Haiku 4.5 | 0.37 |
| gemma-4-26B-A4B (local) | 0.44 |
| nemotron-3-super | 0.45 |
| mimo-v2.5 | 0.57 |
| *Degenerate answer* | *0.57* |
| *Naive baseline* | *0.85* |

<!-- scores:end -->

The gap from `informed` to `vasicek`, 0.107 to 0.140, is the measured cost of feature selection, and it is small next to the gap down to the naive floor at 1.23. CCAR is the suite's most tractable column: most of the cast beats OLS-on-levels and the leaders approach the competent reference, which is the difficulty gradient working as intended at the easy end of the realistic tasks.

Per-instance regret is heavy-right-tailed, because one badly missed scenario dominates the average, so instance-to-instance spread is large next to the gaps between leading rows.

## Solutions

The approach at the top of this column is consistent across instances, and it is four decisions.

**Transform first.** Every strong submission models `logit(default_rate)` or `log(default_rate)` rather than the rate itself, which keeps predictions inside (0, 1) and makes the response approximately linear in the drivers. Fitting the rate directly is the single most expensive omission, because the scenario pushes the drivers past the in-time range and an untransformed linear fit leaves the unit interval.

**Build changes as candidates, not just levels.** The true law pairs a level with a year-over-year change, so a candidate set of levels only cannot contain the answer. Strong runs construct four-quarter differences and log changes alongside the levels and screen them on correlation and sign.

**Throw out the planted crisis quarters.** The strongest row identifies the one-quarter macro spikes where the default rate did not respond, and excludes or repairs them before fitting, in five of eight instances explicitly, naming them by a VIX or unemployment screen. This is the trap the generator plants, and handling it is most of the separation between a careful fit and a mechanical one.

**Take the interval from the fit and widen it for model disagreement.** The better runs use OLS prediction intervals on the transformed scale, including parameter uncertainty, back-transformed to the rate, and some average several near-equivalent specifications and widen the interval by their disagreement.

**Recovering the true drivers is not achievable and does not need to be.** Backward elimination recovers the exact true pair in 3 of 24 instances. Nine heavily collinear macros over eighty quarters do not identify a pair, and the surviving driver is usually a correlated proxy that moves the same way under the scenario, so the path is still predicted well. Recovering the right variable and predicting the right path are different achievements and only the second is scored. Alternatives measured over the same 24 instances: exhaustive search over all 153 sign-plausible pairs 0.490, ridge over all eighteen candidates 0.606, lasso 0.669, against backward elimination's 0.430. Shrinkage over the full candidate set does worse than selection, which is what the collinear equity distractors produce: a fit that keeps all of them gets large offsetting coefficients that cancel in sample and stop cancelling once the scenario leaves the observed range.

## Limitations

**A pooled CCAR number rewards leaning adverse.** Averaged over all three scenarios, raw regret is minimised by a fixed +0.30 adverse bump (0.287 against 0.563 for the accurate fit), because severe instances carry far larger absolute regret and dominate the mean. Normalising each instance by its own degenerate anchor pulls the optimum back to +0.15 but not to zero. The scenario factor makes conservatism detectable only if results are read per scenario, so the single pooled cell in the score table should not be quoted on its own.

**The column mixes two generator variants.** The response law used to be eight constants hard-coded in the public generator, which made every instance solvable in closed form with no estimation. It is now drawn per instance, including which two macros are non-zero. That changed the answer key rather than the question, since no agent was ever told the drivers, and the parameter draws are centred tightly enough on the old calibration to preserve the scale (oracle 0.082 against 0.070, overlapping across seed sets), so archived runs stay in the column ([detail](../limitations.md#the-ccar-response-law-was-public)). Optional extras that would break that, rotating the functional form and splitting scenario severity, are off by default.

**A fourth response family was built and dropped.** `lagged` left the linear reference at 0.0174 against 0.0173 on `vasicek`, because the level drivers are persistent enough and the stress ramp smooth enough that a one or two quarter lag is nearly unidentifiable. It added a family without adding a distinction.
