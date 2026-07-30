# Small-Sample Tail Quantile Estimation

The suite's second realistic domain task, and the only one whose ground truth is empirical rather than generated from a known DGP.

```
inspect eval pereval/tasks/quantile/task.py --model <provider/model>            # needs Docker
inspect eval pereval/tasks/quantile/task.py -T baseline=wei8 --model mockllm/model
```

## The Task

Each instance presents 100 independent problems (the single-instance baseline illustration further down still uses 40). Each is 10 values drawn uniformly without replacement from a population of m year-over-year percent changes of one undisclosed macroeconomic series over an undisclosed window (m >= 250). The agent estimates that population's 90th, 95th and 99th percentiles, plus a 95% interval for the 95th.

The estimand is stated explicitly in the prompt, because leaving "the 95th percentile" ambiguous would make this a reading-comprehension test whose result flips on a paraphrase. Naming the target costs nothing: knowing that the population quantile is wanted does not tell you how to extrapolate a tail from ten points.

The failure mode this task exists to expose is quiet and plausible-looking. `np.percentile(x, 95)` on ten observations is Hyndman-Fan type 7, which can never exceed the sample maximum and puts the true p95 above its own estimate roughly three times in four. It is the natural thing to reach for and it is wrong.

## Scoring: Pinball Regret

```
regret(tau) = E_pop[rho_tau(X - qhat)] - min_q E_pop[rho_tau(X - q)]
rho_tau(d)  = d * (tau - 1[d < 0])
```

Summed over tau in {0.90, 0.95, 0.99} and normalised by the population interquartile range. `E_pop` is a plain average over all m population values, the ten shown and the m - 10 not shown.

Until this was corrected the scored population excluded the ten drawn values, so the scorer measured a different estimand from the one the prompt states and the exactly correct answer to the question as asked carried a small penalty. Immaterial in size but wrong in kind: switching to the full population moves every baseline down by 0.0017 to 0.0028, which is ten to seventeen times below the +-0.03 block-sampling floor, so the scores below remain comparable. The population holds unrounded values; the rounding to four significant figures is a disguise on the observation, not on the population.

The minimiser of the pinball loss is exactly the population tau-quantile, so the population supplies both the truth and the achievable floor. Regret is non-negative and zero only for a perfect answer, with no Harrell-Davis target, no oracle tuning, and no Monte-Carlo simulation. This is what replaces the generated-DGP oracle the other tasks have.

Two properties matter:

- **Asymmetry.** `dL/dq = F(q) - tau`, so the slope tends to `-tau` far below the support and `1 - tau` far above it: a 19:1 ratio at tau = 0.95. Underestimating a tail quantile is expensive, which is the pressure type 7 fails under. The ratio at finite displacement is much smaller on a heavy right tail, because F barely moves above q95.
- **Robustness.** The regret is exactly invariant to the values of observations lying below the estimate, since each contributes `(1-tau)(qhat - q_tau)/m`, which depends on their count and not their magnitude. Replacing a population's minimum with -1e6 leaves the regret bit-for-bit unchanged. Normalising by standard deviation would throw this away (sd explodes, the score collapses toward zero, and the block is silently deleted from the average), which is why the normaliser is the IQR.

## Target Metric

The rest of the suite scores Winkler interval regret. It is the wrong headline here, and the pilot measured why.

Grafting one fixed interval shape onto every candidate rule's own point estimate collapses the entire Winkler spread from 3.44-20.62 down to 3.07-4.02. Winkler ranks almost purely on interval width. Sliding a point estimate across the range that spans type-7 behaviour (hit rate 0.239) to median-unbiasedness (hit rate 0.494) moves Winkler by 4%, and its optimum sits at hit rate 0.370, so it actively prefers an underestimator. Pinball moves 37% over the same range and bottoms out at 0.494. Adding tau = 0.99 makes Winkler flatter still, because the optimal interval widens from 3.75 to 6.50 sample sd and absorbs even more centring error.

Winkler is still reported as a diagnostic, because interval calibration is worth measuring. It is just not what this task is about.

## Quantile Levels

At tau = 0.90 the reference estimators are indistinguishable. At tau = 0.99 the bounded ones are structurally stuck. In units of the sample top gap `x_(10) - x_(9)`, the p99 - p95 spread is an exact constant for type7 (0.360), type8 (0.000, both levels clip to the sample maximum at n = 10) and both extrapolators (1.609). Harrell-Davis alone among the bounded rules is not a fixed constant: its ratio is typically low (median 0.16) but has a long right tail (up to ~3). The truth varies 1.25 to 4.15 across series.

"Adapting to tail shape" is really two separate abilities, and the reference rules split differently on each.

First, can a rule place the tail quantile *above the sample maximum*? type7, type8 and Harrell-Davis cannot: each is a weighted average of order statistics with non-negative weights, so it is structurally bounded by the observed maximum and systematically undershoots a tail that runs past the data (q99 exceeds the sample max in 0% of blocks for all three). wei8, t6 and the normal fit can and do exceed it (100%, 100% and ~87% of blocks).

Second, does the p99 − p95 spread *vary with the sample*? Measured by rank correlation between a rule's per-block spread ratio and the truth's, the normal scores 0.637 and Harrell-Davis 0.504, while type7, type8, wei8 and t6 are exact constants. wei8 and t6 are the instructive case: they extrapolate, and their absolute tail width scales with the top gap x_(10) − x_(9), so they *do* adapt tail scale, but they pin the ratio (q99 − q95) / gap at exactly log 5 = 1.609 regardless of shape, so they cannot match the shape variation the truth shows (ratio 1.25 to 4.15). Harrell-Davis is the mirror image: its ratio varies with the sample, but being bounded by the maximum it cannot extrapolate at all.

Only the normal does both (extrapolate and vary its ratio), which is part of why it wins on this data.

Summing over three tau captures shape in a single scalar, because getting all three levels right requires getting the shape right. The reported `spread_ratio` diagnostic makes behaviour legible directly: 0.0 means type 8 or a degenerate q99 = q95, 0.36 means a bare `np.percentile` call, a constant 1.6 means one of the two extrapolating rules, and a spread that varies block to block means the rule is reading shape out of the sample.

## Data

1,503 monthly not-seasonally-adjusted FRED series, lag-12 simple percent change, frozen as a snapshot in `pereval/tasks/quantile/data/`. FRED revises, so the snapshot must not be refetched without rerunning every published result.

Selected from 28,263 metadata-passing candidates, capped to 5 per title prefix before fetching because five prefixes (HICP, All Employees, PPI by Industry and by Commodity, Consumer Price Indices) account for more than half the pool and forty blocks drawn from forty PPI commodity codes would not be forty independent problems.

The numeric screen rejects interior gaps, non-positive levels, persistent definitional breaks, and upper-tail ties. Two rules are not obvious:

- **Persistence, not magnitude, separates artifacts from data.** M1NS jumped 4.5x on a 2020 savings reclassification and never reverted (rejected); LNU03000000 jumped 3.6x on COVID and returned to baseline (kept).
- **Ties are real.** 43 of 3,275 fetched series carry tie rates of 0.33 to 1.00 among their top order statistics, from quantisation of the source levels rather than any ceiling on growth. A tie in the top two collapses the reference estimator's tail extrapolation to the sample maximum. They are screened out, not jittered: jitter magnitude would set the tail scale the reference extrapolates from.

Shape coverage: skew -2.03 to +26.26, excess kurtosis -0.86 to +690.

## Disguises

Three, each doing a different job:

- **Random window** (the one that matters). Even perfect recognition of a series does not give you the p95 of a span whose endpoints you do not know.
- **Random scale**, log-uniform in [0.1, 10], independent per block. Removes absolute magnitude. A positive factor maps 0 to 0, so the sign structure and the meaning of zero survive and a model may still use the legitimate prior that macro growth rates have fat right tails. No location shift is applied: every estimator here is location-scale equivariant so a shift would be invisible to the score, but it would close that channel.
- **Four significant figures.** Defeats exact matching against a memorised table. Weak on its own.

Blocks come from distinct series and are independently scaled, so they cannot be pooled.

## Baselines

`-T baseline=type7|type8|hd|t6|wei8|normal|logistic`.

The `logistic` baseline is the moment-matched normal's heavier-tailed sibling: same construction, `mu + (sd sqrt(3)/pi) * logit(tau)`, but a family with excess kurtosis 1.2 against the normal's 0. It edges out the normal to lead the baselines (0.076 ± 0.027 vs 0.078 ± 0.027 over the three 100-block seeds), and the win is located exactly where the heavier tail should help: at tau = 0.99 it scores 0.026 against the normal's 0.029, while at tau = 0.90 it is marginally worse (it over-reaches for a mild quantile).

`t6` is the literature construction: the tail extrapolation of Wei, Wang and Hutson (Commun. Stat. Theory Methods, DOI 10.1080/03610926.2013.775304) around the interior their paper uses, whose Q^L is exactly Hyndman-Fan type 6. `wei8` is the same extrapolation around a type-8 interior, a substitution the paper did not test. What matters for this task is the property they share: both extrapolate past the sample maximum, and none of the other rules can. Intervals are the paper's smoothed bootstrap with a BCa correction.

None of these is "the best" estimator, and the comparison below should not be read as crowning one. The paper evaluated on 95% confidence-interval coverage, not on point accuracy and not on pinball regret, so it is being judged here on a criterion it was not designed for.

Lower regret is better. One generated instance, 40 blocks, seed 1.

| Baseline | Pinball regret | p90 | p95 | p99 | Hit rate | MAE | Coverage | Spread |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PERFECT (population quantile) | 0.0000 | | | | | | | |
| logistic (moment-matched) | 0.0661 | 0.0239 | 0.0219 | 0.0203 | 0.450 | 0.526 | 0.850 | 3.318 |
| normal (moment-matched) | 0.0677 | 0.0233 | 0.0216 | 0.0228 | 0.450 | 0.527 | 0.850 | 2.485 |
| wei8 (type-8 variant) | 0.0891 | 0.0343 | 0.0279 | 0.0269 | 0.525 | 0.714 | 0.875 | 1.609 |
| t6 (literature construction) | 0.0931 | 0.0367 | 0.0299 | 0.0265 | 0.550 | 0.789 | 0.900 | 1.609 |
| type8 | 0.1121 | 0.0343 | 0.0289 | 0.0489 | 0.475 | 0.640 | 0.425 | 0.000 |
| hd (Harrell-Davis) | 0.1130 | 0.0322 | 0.0310 | 0.0498 | 0.350 | 0.616 | 0.225 | 0.197 |
| type7 (`np.percentile` default) | 0.1339 | 0.0434 | 0.0384 | 0.0521 | 0.275 | 0.652 | 0.250 | 0.360 |

The p99 column does the work: bounded rules 0.049-0.052, extrapolating rules 0.027. The naive moment-matched normal leading the table is a real result, not a bug. It is exactly the kind of criterion-dependent inversion this task is meant to surface, and a caution against reading any single column as a verdict.

## Stability Across Seeds (100 blocks, metric disclosed)

The primary result. Free models, three seeds each (base seeds 1, 2, 3, so a near-disjoint 100-series draw per seed), 100 blocks per instance, scoring metric disclosed in the prompt. Reported as **mean ± 2 SD** over the runs (2× the sample standard deviation, not a confidence interval), ordered by the upper end mean + 2 SD, so the ranking rewards consistency rather than a lucky low mean. Lower is better. Every reported number has at least three valid runs behind it; a model that could not reach three is excluded with its failure rate noted rather than reported on thin data.

The four reference estimators are deterministic given the blocks, so their spread is **pure block-sampling noise**: the irreducible floor at 100 blocks (about ± 0.03). A model tighter than that floor has negligible run-to-run method variance; a model wider than it is switching methods between runs, which no increase in block count can fix.

| Row | runs | per-run regret | mean ± 2 SD |
| --- | --- | --- | --- |
| `[logistic]` | 3 | 0.0775, 0.0881, 0.0617 | 0.076 ± 0.027 |
| `[normal]` | 3 | 0.0796, 0.0907, 0.0638 | 0.078 ± 0.027 |
| **nemotron-3-ultra-550b** | 3 | 0.0767, 0.0987, 0.0875 | **0.088 ± 0.022** |
| Claude Haiku 4.5 | 3 | 0.0808, 0.0784, 0.1021 | 0.087 ± 0.026 |
| nemotron-3-super-120b | 3 | 0.1024, 0.1182, 0.0983 | 0.106 ± 0.021 |
| `[wei8]` | 3 | 0.0975, 0.1242, 0.1001 | 0.107 ± 0.029 |
| `[t6]` | 3 | 0.1089, 0.1389, 0.1157 | 0.121 ± 0.032 |
| `[type7]` | 3 | 0.1168, 0.1375, 0.1040 | 0.119 ± 0.034 |
| deepseek-v4-flash (free) | 3 | 0.1668, 0.0704, 0.1140 | 0.117 ± 0.097 |
| mimo-v2.5-free | 3 | 0.1218, 0.0945, 0.1507 | 0.122 ± 0.056 |
| laguna-m.1 | 3 | 0.1568, 0.1209, 0.0641 | 0.114 ± 0.093 |
| GLM-5.1 | 3 | 0.2456, 0.1486, 0.0760 | 0.157 ± 0.170 |

**gpt-oss-20b is excluded, and the exclusion is the finding.** It produced valid output on only 2 of 6 attempts (seeds 1 and 2 succeeded at 0.122 and 0.118; seed 3 failed twice and seeds 4 and 5 once each, every failure running the full agent loop for 84 to 296 messages and then emitting no parseable predictions.csv). A ~67% rate of answering nothing is worse than an unstable answer, and it cannot meet the three-run bar, so no regret number is reported for it.

Two models sit at or below the block-sampling floor: **nemotron-3-ultra (± 0.022) and nemotron-3-super (± 0.021) score as consistently as the deterministic baselines**, and nemotron-ultra is the only model that beats every reference estimator on the conservative bound (upper 0.110 vs wei8's 0.137), edged only by the naive normal.

A tight band means the *score* is stable, not that the *method* is. The transcripts show nemotron-3-ultra using materially different approaches across the three seeds (GPD-plus-t with bootstrap on one, a kitchen sink of logistic, gennorm, skew-normal, Weibull, gamma and KDE on another) that all happen to land in a similar score range. So its trustworthiness is empirical (its varying methods all scored well here) rather than structural (one fixed method), and a single run is trustworthy only in the weak sense that any one of its methods would have scored similarly. A same-seed repeat experiment settled which it is: rerunning on byte-identical data still moved the score. nemotron-3-ultra's best run (0.077) reran to 0.142, so the method variation is **sampling temperature, not a response to the data**. See [Run-to-Run Reproducibility](../limitations.md#run-to-run-reproducibility).

Two models sit far above the floor: **mimo at ± 0.056 (about 2× the floor) and laguna at ± 0.093 (about 3×)**. Roughly two-thirds of laguna's variance is method-switching, not block-sampling. Its per-run values run 0.157, 0.121, 0.064: worst in the table on seed 1, best on seed 3. A single run of laguna is a coin flip, and more blocks would not change that. This is the empirical case for the suite's repeated-run standard: for method-switching models no single number means anything, and the *stability itself* is a reported property.

## Criterion Disagreement

Four defensible criteria rank the same estimators in incompatible orders:

| Criterion | Winner | wei8's position |
| --- | --- | --- |
| point accuracy (MAE) | type7 | worst |
| point centring (hit rate) | wei8 | best |
| interval coverage | wei8 / t6 | best |
| interval Winkler | normal | fourth of five |
| pinball regret (this task's metric) | normal | second of six |

This is not a defect to be resolved before shipping. It is the most interesting thing the task produces, and it is the model-risk point in miniature: whoever picks the criterion picks the winner.
