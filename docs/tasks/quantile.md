# Small-Sample Tail Quantile Estimation

> **Status: benchmarked on a free-model cast.** Generator, scorer, baselines and
> Inspect wrapper are in place and validated end to end. Four free models have a
> 3-run mean ± 2 SD result at 100 blocks with the metric disclosed (see
> [Stability Across Seeds](#stability-across-seeds-100-blocks-metric-disclosed)).
> A paid-model cast is still pending.

The suite's second realistic domain task, and the only one whose ground truth is
empirical rather than generated from a known DGP. Implementation notes and the
build plan are in [../quantile-task-plan.md](../quantile-task-plan.md).

```
inspect eval pereval/tasks/quantile/task.py --model <provider/model>            # needs Docker
inspect eval pereval/tasks/quantile/task.py -T baseline=wei8 --model mockllm/model
```

## The Task

Each instance presents 100 independent problems (the results tables below predate this and used 40). Each is 10 values drawn uniformly without replacement from a population of m year-over-year percent changes of one undisclosed macroeconomic series over an undisclosed window (m >= 250). The agent estimates that population's 90th, 95th and 99th percentiles, plus a 95% interval for the 95th.

The estimand is stated explicitly in the prompt, because leaving "the 95th percentile" ambiguous would make this a reading-comprehension test whose result flips on a paraphrase. Naming the target costs nothing: knowing that the population quantile is wanted does not tell you how to extrapolate a tail from ten points.

The failure mode this task exists to expose is quiet and plausible-looking. `np.percentile(x, 95)` on ten observations is Hyndman-Fan type 7, which can never exceed the sample maximum and puts the true p95 above its own estimate roughly three times in four. It is the natural thing to reach for and it is wrong.

## Scoring: Pinball Regret

```
regret(tau) = E_pop[rho_tau(X - qhat)] - min_q E_pop[rho_tau(X - q)]
rho_tau(d)  = d * (tau - 1[d < 0])
```

Summed over tau in {0.90, 0.95, 0.99} and normalised by the population interquartile range. `E_pop` is a plain average over the m - 10 population values the agent did not see.

The minimiser of the pinball loss is exactly the population tau-quantile, so the population supplies both the truth and the achievable floor. Regret is non-negative and zero only for a perfect answer, with no Harrell-Davis target, no oracle tuning, and no Monte-Carlo simulation. This is what replaces the generated-DGP oracle the other tasks have.

Two properties matter:

- **Asymmetry.** `dL/dq = F(q) - tau`, so the slope tends to `-tau` far below the support and `1 - tau` far above it: a 19:1 ratio at tau = 0.95. Underestimating a tail quantile is expensive, which is the pressure type 7 fails under. The ratio at finite displacement is much smaller on a heavy right tail, because F barely moves above q95.
- **Robustness.** The regret is exactly invariant to the values of observations lying below the estimate, since each contributes `(1-tau)(qhat - q_tau)/m`, which depends on their count and not their magnitude. Replacing a population's minimum with -1e6 leaves the regret bit-for-bit unchanged. Normalising by standard deviation would throw this away (sd explodes, the score collapses toward zero, and the block is silently deleted from the average), which is why the normaliser is the IQR.

## Why Not Winkler

The rest of the suite scores Winkler interval regret. It is the wrong headline here, and the pilot measured why.

Grafting one fixed interval shape onto every candidate rule's own point estimate collapses the entire Winkler spread from 3.44-20.62 down to 3.07-4.02. Winkler ranks almost purely on interval width. Sliding a point estimate across the range that spans type-7 behaviour (hit rate 0.239) to median-unbiasedness (hit rate 0.494) moves Winkler by 4%, and its optimum sits at hit rate 0.370, so it actively prefers an underestimator. Pinball moves 37% over the same range and bottoms out at 0.494. Adding tau = 0.99 makes Winkler flatter still, because the optimal interval widens from 3.75 to 6.50 sample sd and absorbs even more centring error.

Winkler is still reported as a diagnostic, because interval calibration is worth measuring. It is just not what this task is about.

## Why Three Quantile Levels

At tau = 0.90 the reference estimators are indistinguishable. At tau = 0.99 the bounded ones are structurally stuck. In units of the sample top gap `x_(10) - x_(9)`, the p99 - p95 spread is an exact constant for type7 (0.360), type8 (0.000, both levels clip to the sample maximum at n = 10) and both extrapolators (1.609), and varies only mildly for Harrell-Davis (about 0.16 to 0.20). The truth varies 1.25 to 4.15 across series.

So the four rules that touch nothing but the top two order statistics are structurally incapable of adapting to tail shape. The normal fit and Harrell-Davis do vary, because they use all ten points; measured by rank correlation between a rule's per-block spread and the truth's, the naive normal scores 0.637 and HD 0.504, while type7, type8, wei8 and t6 are exact constants and have no correlation at all. That the naive rule is the *most* adaptive of the baselines is part of why it wins.

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

`-T baseline=type7|type8|hd|t6|wei8|normal`.

`t6` is the literature construction: the tail extrapolation of Wei, Wang and Hutson (Commun. Stat. Theory Methods, DOI 10.1080/03610926.2013.775304) around the interior their paper uses, whose Q^L is exactly Hyndman-Fan type 6. `wei8` is the same extrapolation around a type-8 interior, a substitution the paper did not test. What matters for this task is the property they share: both extrapolate past the sample maximum, and none of the other rules can. Intervals are the paper's smoothed bootstrap with a BCa correction.

None of these is "the best" estimator, and the comparison below should not be read as crowning one. The paper evaluated on 95% confidence-interval coverage, not on point accuracy and not on pinball regret, so it is being judged here on a criterion it was not designed for.

Lower regret is better. One generated instance, 40 blocks, seed 1.

| Baseline | Pinball regret | p90 | p95 | p99 | Hit rate | MAE | Coverage | Spread |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PERFECT (population quantile) | 0.0000 | | | | | | | |
| normal (moment-matched) | 0.0677 | 0.0233 | 0.0216 | 0.0228 | 0.450 | 0.527 | 0.850 | 2.485 |
| wei8 (type-8 variant) | 0.0891 | 0.0343 | 0.0279 | 0.0269 | 0.525 | 0.714 | 0.875 | 1.609 |
| t6 (literature construction) | 0.0931 | 0.0367 | 0.0299 | 0.0265 | 0.550 | 0.789 | 0.900 | 1.609 |
| type8 | 0.1121 | 0.0343 | 0.0289 | 0.0489 | 0.475 | 0.640 | 0.425 | 0.000 |
| hd (Harrell-Davis) | 0.1130 | 0.0322 | 0.0310 | 0.0498 | 0.350 | 0.616 | 0.225 | 0.197 |
| type7 (`np.percentile` default) | 0.1339 | 0.0434 | 0.0384 | 0.0521 | 0.275 | 0.652 | 0.250 | 0.360 |

The p99 column does the work: bounded rules 0.049-0.052, extrapolating rules 0.027. The naive moment-matched normal leading the table is a real result, not a bug. It is exactly the kind of criterion-dependent inversion this task is meant to surface, and a caution against reading any single column as a verdict.

## Stability Across Seeds (100 blocks, metric disclosed)

The primary result. Free models, three seeds each (base seeds 1, 2, 3, so a
near-disjoint 100-series draw per seed), 100 blocks per instance, scoring metric
disclosed in the prompt. Reported as **mean ± 2 SD** over the runs (2× the
sample standard deviation, not a confidence interval), ordered by the upper end
mean + 2 SD, so the ranking rewards consistency rather than a lucky low mean.
Lower is better. Every reported number has at least three valid runs behind it;
a model that could not reach three is excluded with its failure rate noted
rather than reported on thin data.

The four reference estimators are deterministic given the blocks, so their spread
is **pure block-sampling noise** — the irreducible floor at 100 blocks (about
± 0.03). A model tighter than that floor has negligible run-to-run method
variance; a model wider than it is switching methods between runs, which no
increase in block count can fix.

| Row | runs | per-run regret | mean ± 2 SD |
| --- | --- | --- | --- |
| `[normal]` | 3 | 0.0796, 0.0907, 0.0638 | 0.078 ± 0.027 |
| **nemotron-3-ultra-550b** | 3 | 0.0767, 0.0987, 0.0875 | **0.088 ± 0.022** |
| nemotron-3-super-120b | 3 | 0.1024, 0.1182, 0.0983 | 0.106 ± 0.021 |
| `[wei8]` | 3 | 0.0975, 0.1242, 0.1001 | 0.107 ± 0.029 |
| `[t6]` | 3 | 0.1089, 0.1389, 0.1157 | 0.121 ± 0.032 |
| `[type7]` | 3 | 0.1168, 0.1375, 0.1040 | 0.119 ± 0.034 |
| mimo-v2.5-free | 3 | 0.1218, 0.0945, 0.1507 | 0.122 ± 0.056 |
| laguna-m.1 | 3 | 0.1568, 0.1209, 0.0641 | 0.114 ± 0.093 |

**gpt-oss-20b is excluded, and the exclusion is the finding.** It produced valid
output on only 2 of 6 attempts (seeds 1 and 2 succeeded at 0.122 and 0.118; seed
3 failed twice and seeds 4 and 5 once each, every failure running the full agent
loop for 84 to 296 messages and then emitting no parseable predictions.csv). A
~67% rate of answering nothing is worse than an unstable answer, and it cannot
meet the three-run bar, so no regret number is reported for it.

Two models sit at or below the block-sampling floor: **nemotron-3-ultra (± 0.022)
and nemotron-3-super (± 0.021) are as stable as the deterministic baselines**, so
their method is fixed across runs and their single-run numbers are trustworthy.
nemotron-ultra is the only model that beats every reference estimator on the
conservative bound (upper 0.110 vs wei8's 0.137), edged only by the naive normal.

Two models sit far above the floor: **mimo at ± 0.056 (about 2× the floor) and
laguna at ± 0.093 (about 3×)**. Roughly two-thirds of laguna's variance is
method-switching, not block-sampling. Its per-run values run 0.157, 0.121, 0.064
— worst in the table on seed 1, best on seed 3. A single run of laguna is a coin
flip, and more blocks would not change that. This is the empirical case for the
suite's repeated-run standard: for method-switching models no single number
means anything, and the *stability itself* is a reported property.

## First Model Runs (provisional, pre-disclosure, 40 blocks)

> Provisional and superseded by the table above. These predate the metric
> disclosure now in the prompt and used 40 blocks, so they measure a different,
> now-retired configuration. Retained as evidence the harness discriminates, not
> as results.

Six free models, one instance each (40 blocks, seed 1835504127), all rows paired against reference estimators computed on the identical blocks. Lower regret is better; `LIMIT` marks a run that hit a budget cap.

| Row | Regret | p90 | p95 | p99 | Hit | MAE | Cov | Spread | Msgs | Answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-31b-it `LIMIT` | **0.0929** | 0.0333 | 0.0278 | 0.0318 | 0.550 | 0.947 | 0.475 | 3.690 | 6 | 40/40 |
| `[normal]` | 0.0995 | 0.0320 | 0.0293 | 0.0382 | 0.450 | 0.911 | 0.725 | 2.545 | | 40/40 |
| nemotron-3-ultra-550b | 0.1127 | 0.0348 | 0.0385 | 0.0394 | 0.375 | 0.890 | 0.750 | 3.553 | 44 | 40/40 |
| `[wei8]` | 0.1145 | 0.0433 | 0.0346 | 0.0366 | 0.650 | 1.084 | 0.800 | 1.609 | | 40/40 |
| mimo-v2.5-free | 0.1160 | 0.0363 | 0.0348 | 0.0449 | 0.375 | 0.939 | 0.825 | 6.103 | 23 | 40/40 |
| `[t6]` | 0.1240 | 0.0494 | 0.0384 | 0.0362 | 0.675 | 1.228 | 0.825 | 1.609 | | 40/40 |
| laguna-m.1 | 0.1291 | 0.0494 | 0.0454 | 0.0343 | **0.750** | 1.405 | 0.725 | 5.800 | 74 | 40/40 |
| `[hd]` | 0.1333 | 0.0400 | 0.0345 | 0.0588 | 0.375 | 0.960 | 0.125 | 0.214 | | 40/40 |
| `[type8]` | 0.1345 | 0.0433 | 0.0333 | 0.0579 | 0.475 | 0.987 | 0.350 | 0.000 | | 40/40 |
| nemotron-3-super-120b | 0.1429 | 0.0424 | 0.0394 | 0.0611 | 0.350 | 0.960 | 0.450 | **0.360** | 52 | 40/40 |
| `[type7]` | 0.1429 | 0.0424 | 0.0394 | 0.0611 | 0.350 | 0.960 | 0.250 | 0.360 | | 40/40 |
| gpt-oss-20b `LIMIT` | 1.1312 | 0.2943 | 0.3687 | 0.4682 | 0.075 | 1.866 | 0.000 | 0.000 | 300 | 40/40 |

The task discriminates across its whole intended range, and the `spread_ratio` column reads out method directly.

**nemotron-3-super-120b reproduced `np.percentile` exactly.** Its row matches `[type7]` on every point metric including the 0.360 spread constant, after 52 messages of work. That is the failure mode the task exists to expose, and it is invisible in the regret column alone: 0.1429 looks merely mediocre until you see it is the same 0.1429.

**gpt-oss-20b failed differently and worse.** Spread 0.000 means it set q99 = q95, coverage 0.000 means not one of its forty intervals contained the truth, and it exhausted all 300 messages getting there.

**laguna-m.1 is the only model that overestimates**, at hit rate 0.750 against everyone else's 0.35 to 0.55, with the worst MAE of any completing model (1.405). Over-extrapolation is a real failure mode too, and the hit-rate diagnostic is what separates it from under-extrapolation, since both show up as an unremarkable regret.

**gemma-4-31b-it led while hitting the time limit after 6 messages**, throttled by the free tier. It still scored 40/40 only because it wrote a complete predictions.csv early, which is the instruction added after an earlier run failed by building state across fresh interpreters.

### One Post-Disclosure Run

The rows above predate the metric disclosure now in the prompt. Claude Haiku 4.5 was run once *after* disclosure, on the same instance (seed 1835504127), so it is comparable on data but not on instructions. A single sense-check of a midrange model, not a result.

| Row | Regret | p90 | p95 | p99 | Hit | MAE | Cov | Spread | Msgs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `[normal]` | 0.0995 | 0.0320 | 0.0293 | 0.0382 | 0.450 | 0.911 | 0.725 | 2.545 | |
| Claude Haiku 4.5 (post-disclosure) | 0.1060 | 0.0346 | 0.0307 | 0.0407 | 0.400 | **0.904** | **0.200** | 2.414 | 58 |
| `[wei8]` | 0.1145 | 0.0433 | 0.0346 | 0.0366 | 0.650 | 1.084 | 0.800 | 1.609 | |

Haiku is the sharpest illustration of the task's premise so far, because it split its method. For the point estimates it fit parametric distributions (normal, lognormal, t) to each 10-point sample, which extrapolate past the sample maximum and adapt their shape per block: the best MAE of any completing model (0.904) and an adaptive spread (2.414). For the interval it used a nonparametric bootstrap of the sample quantile, resampling the 10 points and taking bootstrap percentiles.

That interval method is the one the source literature singles out as failing. A nonparametric bootstrap of a sample quantile is bounded by the sample maximum, so the resampled q95 can never exceed the largest of the ten points and the interval structurally undercovers a tail quantile. The proof of concept measured bootstrap coverage of 0.28 for type7 and 0.18 for HD for exactly this reason; Haiku's 0.200 lands in that band. It is a fluent, competent-looking analysis that picked a good method for the point and a provably wrong one for the tail interval, miscalibrated precisely where it matters. On this task Haiku would rank near the top on point accuracy and near the bottom on interval calibration, which is the criterion disagreement below made concrete in one model.

### Environment Notes

Zen's free tier is not a usable validation surface: three of four models failed environmentally (two HTTP 400s, one response with no `choices` field). OpenRouter ran five of five and offers 13 tool-capable free models. `nemotron-3-ultra` failed on Zen and succeeded on OpenRouter, confirming the gateway rather than the model was at fault. Zen's paid tier is reliable; Claude Haiku 4.5 ran there without issue.

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

## Acknowledgement

Built on a prior proof of concept comparing these estimators on 12 quarterly FRED series, which established the reference implementations (validated bit-identical against the original R), their properties, and the screening rules carried over here.
