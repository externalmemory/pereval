# Small-Sample Tail Quantile Estimation

> **Status: implemented, not yet benchmarked.** The generator, scorer, baselines
> and Inspect wrapper are in place and validated end to end under mockllm; no
> model results exist yet. The baseline table below is real, the leaderboard is
> empty.

The suite's second realistic domain task, and the only one whose ground truth is
empirical rather than generated from a known DGP. Implementation notes and the
build plan are in [../quantile-task-plan.md](../quantile-task-plan.md).

```
inspect eval pereval/tasks/quantile/task.py --model <provider/model>            # needs Docker
inspect eval pereval/tasks/quantile/task.py -T baseline=wei8 --model mockllm/model
```

## The Task

Each instance presents 40 independent problems. Each is 10 values drawn uniformly without replacement from a population of m year-over-year percent changes of one undisclosed macroeconomic series over an undisclosed window (m >= 250). The agent estimates that population's 90th, 95th and 99th percentiles, plus a 95% interval for the 95th.

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

So no published estimator adapts to tail shape: they all scale the tail by one order-statistic gap. Summing over three tau captures that in a single scalar, because getting all three right requires the right shape. The reported `spread_ratio` diagnostic makes the behaviour legible directly: 0.0 means type 8, 0.36 means `np.percentile`, a constant 1.6 means the published estimator, and something that varies with the sample means the model is doing better than all of them.

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

`-T baseline=type7|type8|hd|t6|wei8|normal`. The reference is `wei8`: the tail extrapolation of Wei, Wang and Hutson (Commun. Stat. Theory Methods, DOI 10.1080/03610926.2013.775304) around a Hyndman-Fan type-8 interior, which does extrapolate past the sample maximum. `t6` is the same extrapolation around the type-6 interior used in the paper. Intervals are the paper's smoothed bootstrap with a BCa correction.

Lower regret is better. One generated instance, 40 blocks, seed 1.

| Baseline | Pinball regret | p90 | p95 | p99 | Hit rate | MAE | Coverage | Spread |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PERFECT (population quantile) | 0.0000 | | | | | | | |
| normal (moment-matched) | 0.0677 | 0.0233 | 0.0216 | 0.0228 | 0.450 | 0.527 | 0.850 | 2.485 |
| wei8 (published reference) | 0.0891 | 0.0343 | 0.0279 | 0.0269 | 0.525 | 0.714 | 0.875 | 1.609 |
| t6 (paper's variant) | 0.0931 | 0.0367 | 0.0299 | 0.0265 | 0.550 | 0.789 | 0.900 | 1.609 |
| type8 | 0.1121 | 0.0343 | 0.0289 | 0.0489 | 0.475 | 0.640 | 0.425 | 0.000 |
| hd (Harrell-Davis) | 0.1130 | 0.0322 | 0.0310 | 0.0498 | 0.350 | 0.616 | 0.225 | 0.197 |
| type7 (`np.percentile` default) | 0.1339 | 0.0434 | 0.0384 | 0.0521 | 0.275 | 0.652 | 0.250 | 0.360 |

The p99 column does the work: bounded rules 0.049-0.052, extrapolating rules 0.027. The naive moment-matched normal beating the published estimator is a real result, not a bug, and it is the kind of criterion-dependent inversion the task is meant to surface.

## Criterion Disagreement

Four defensible criteria rank the same estimators in incompatible orders:

| Criterion | Winner | wei8's position |
| --- | --- | --- |
| point accuracy (MAE) | type7 | worst |
| point centring (hit rate) | wei8 | best |
| interval coverage | wei8 / t6 | best |
| interval Winkler | normal | fourth of five |

This is not a defect to be resolved before shipping. It is the most interesting thing the task produces, and it is the model-risk point in miniature: whoever picks the criterion picks the winner.

## Acknowledgement

Built on a prior proof of concept comparing these estimators on 12 quarterly FRED series, which established the reference implementations (validated bit-identical against the original R), their properties, and the screening rules carried over here.
