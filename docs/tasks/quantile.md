# Small-Sample Tail Quantile Estimation

The suite's second realistic domain task, and the only one whose ground truth is empirical rather than generated from a known data-generating process.

```
inspect eval pereval/tasks/quantile/task.py --model <provider/model>            # needs Docker
inspect eval pereval/tasks/quantile/task.py -T baseline=wei8 --model mockllm/model
```

## Task

Each instance presents 100 independent problems. Each problem is 10 values drawn uniformly without replacement from a population of at least 250 year-over-year percent changes of one undisclosed macroeconomic series over an undisclosed window. The agent estimates that population's 90th, 95th and 99th percentiles, plus a 95% interval for the 95th.

The estimand is stated explicitly in the prompt. Leaving "the 95th percentile" ambiguous would make this a reading-comprehension test whose result flips on a paraphrase, and naming the target costs nothing: knowing that the population quantile is wanted does not tell you how to extrapolate a tail from ten points.

The failure mode the task exists to expose is quiet and plausible-looking. `np.percentile(x, 95)` is Hyndman-Fan type 7, which can never exceed the sample maximum and puts the true p95 above its own estimate roughly three times in four. It is the natural thing to reach for and it is wrong.

## Data

1,503 monthly not-seasonally-adjusted FRED series, lag-12 simple percent change, frozen as a snapshot in `pereval/tasks/quantile/data/`. FRED revises, so the snapshot must not be refetched without rerunning every published result.

They were selected from 28,263 metadata-passing candidates, capped at five per title prefix before fetching, because five prefixes (HICP, All Employees, PPI by Industry and by Commodity, Consumer Price Indices) account for more than half the pool, and forty blocks drawn from forty PPI commodity codes would not be forty independent problems.

A numeric screen rejects interior gaps, non-positive levels, persistent definitional breaks and upper-tail ties. Two of those rules are not obvious:

- **Persistence, not magnitude, separates artifacts from data.** M1NS jumped 4.5x on a 2020 savings reclassification and never reverted, and is rejected; LNU03000000 jumped 3.6x on COVID and returned to baseline, and is kept.
- **Ties are real and are screened, not jittered.** 43 of 3,275 fetched series carry tie rates of 0.33 to 1.00 among their top order statistics, from quantisation of the source levels rather than any ceiling on growth. A tie in the top two collapses the reference estimator's tail extrapolation to the sample maximum. Jittering is not the fix, because the jitter magnitude would then set the tail scale the reference extrapolates from.

Shape coverage across the snapshot runs from skew -2.03 to +26.26 and excess kurtosis -0.86 to +690.

Three disguises are applied per block, each doing a different job. A **random window**, which is the one that matters: even perfect recognition of a series does not give you the p95 of a span whose endpoints you do not know. A **random scale**, log-uniform in [0.1, 10] and independent per block, which removes absolute magnitude; a positive factor maps zero to zero, so the sign structure survives and the legitimate prior that macro growth rates have fat right tails is still usable. No location shift is applied, because every estimator here is location-scale equivariant and a shift would be invisible to the score. And **rounding to four significant figures**, which defeats exact matching against a memorised table and is weak on its own. Blocks come from distinct series and are independently scaled, so they cannot be pooled.

## Scoring

```
regret(tau) = E_pop[rho_tau(X - qhat)] - min_q E_pop[rho_tau(X - q)]
rho_tau(d)  = d * (tau - 1[d < 0])
```

Summed over tau in {0.90, 0.95, 0.99} and normalised by the population interquartile range. `E_pop` is a plain average over all population values, the ten shown and the rest not shown.

**This task has no oracle row, and does not need one.** The minimiser of the pinball loss is exactly the population tau-quantile, so the population supplies the truth and the achievable floor at once. Regret is non-negative and zero only for a perfect answer, with no Harrell-Davis target, no oracle tuning and no Monte Carlo. That is what replaces the generated-DGP oracle the other tasks have.

Two properties of the metric matter:

- **Asymmetry.** `dL/dq = F(q) - tau`, so the slope tends to `-tau` far below the support and `1 - tau` far above it, a 19:1 ratio at tau = 0.95. Underestimating a tail quantile is expensive, which is the pressure type 7 fails under. At finite displacement on a heavy right tail the ratio is much smaller, because F barely moves above q95.
- **Robustness.** Regret is exactly invariant to the values of observations below the estimate, since each contributes `(1-tau)(qhat - q_tau)/m`, which depends on their count and not their magnitude. Replacing a population's minimum with -1e6 leaves it bit-for-bit unchanged. Normalising by standard deviation would throw that away, which is why the normaliser is the IQR.

**Winkler regret is reported as a diagnostic and is deliberately not the headline.** Grafting one fixed interval shape onto every candidate rule's point estimate collapses the whole Winkler spread from 3.44-20.62 to 3.07-4.02, so it ranks almost purely on interval width. Sliding a point estimate from type-7 behaviour (hit rate 0.239) to median-unbiasedness (0.494) moves Winkler by 4% and its optimum sits at hit rate 0.370, meaning it actively prefers an underestimator. Pinball moves 37% over the same range and bottoms out at 0.494.

Three tau levels are summed because getting all three right requires getting the tail *shape* right, and the `spread_ratio` diagnostic makes a submission's behaviour legible directly: 0.0 means type 8 or a degenerate q99 = q95, 0.36 means a bare `np.percentile` call, a constant 1.6 means one of the two extrapolating rules, and a spread that varies block to block means the rule is reading shape out of the sample.

## Results

Worst-case regret over three instances. Lower is better.

<!-- scores:begin (generated by scripts/render_scores.py; do not edit by hand) -->

| Model | Quantile |
| --- | --- |
| deepseek-v4-flash-0731 | **0.067** |
| minimax-m3.1-flash | 0.070 |
| ling-3.0-flash | 0.076 |
| Kimi K3 | 0.077 |
| gemma-4-26B-A4B (local) | 0.078 |
| Claude Opus 5.5 | 0.083 |
| nemotron-3-ultra | 0.099 |
| Claude Haiku 4.5 | 0.10 |
| nemotron-3-super | 0.12 |
| *Degenerate answer* | *0.12* |
| gpt-6-luna | 0.128 |
| *Naive baseline* | *0.14* |
| mimo-v2.5 | 0.15 |
| GLM-5.1 | 0.25 |
| Qwen3.6-35B-A3B (local) | 3.8e12 |
| *Oracle (true model)* | *none* |

<!-- scores:end -->

The reference estimators are the thing to read this column against, because on this task they are strong. One instance, 40 blocks, seed 1:

| Baseline | Pinball regret | p99 | Spread ratio |
| --- | --- | --- | --- |
| logistic (moment-matched) | 0.0661 | 0.0203 | 3.318 |
| normal (moment-matched) | 0.0677 | 0.0228 | 2.485 |
| wei8 (type-8 variant) | 0.0891 | 0.0269 | 1.609 |
| t6 (literature construction) | 0.0931 | 0.0265 | 1.609 |
| type8 | 0.1121 | 0.0489 | 0.000 |
| hd (Harrell-Davis) | 0.1130 | 0.0498 | 0.197 |
| type7 (`np.percentile` default) | 0.1339 | 0.0521 | 0.360 |

The p99 column does the work: bounded rules score 0.049 to 0.052 there, extrapolating rules 0.027. "Adapting to tail shape" is two separate abilities and the rules split differently on each. **Placing a quantile above the sample maximum:** type7, type8 and Harrell-Davis are weighted averages of order statistics with non-negative weights, so they are structurally bounded by the observed maximum and exceed it in 0% of blocks; wei8, t6 and the normal fit do so in 100%, 100% and about 87%. **Varying the p99 - p95 spread with the sample:** by rank correlation against the truth, the normal scores 0.637 and Harrell-Davis 0.504, while type7, type8, wei8 and t6 are exact constants. wei8 and t6 are the instructive case, since they do adapt tail *scale* to the top gap but pin the ratio at exactly log 5 = 1.609 regardless of shape, against a truth that runs from 1.25 to 4.15. Only the normal does both, which is most of why it wins here.

That a naive moment-matched normal leads the reference set is a real result rather than a bug, and the reason to be careful with any single column.

Note on resolution: the block-sampling floor at 100 blocks is about ±0.03, and differences finer than roughly 0.005 cannot be read across rows at all.

## Solutions

**The standing finding is that moment-matched families are hard to beat here, and the rows at the top of the column are the two ways of arriving at that.**

The first way is to land on one. The best-scoring open model fits a moment-matched normal on two of its three seeds and a t distribution on the third, reaching that by search rather than assumption, having tried GPD, KDE, lognormal and bootstrap along the way. It ties the `normal` baseline to four decimal places on two seeds and loses to `logistic` on all three, so the score belongs to the task rather than to the model.

The second way is to construct something better by argument, and it lands in the same place. deepseek-v4-flash-0731, which sets the column's best cell, runs its own Monte Carlo study over candidate truth families (t2 through t5, normal, Johnson SU skew, a GPD upper tail) scored by simulated pinball loss, tests and rejects a skew-t fit, and submits a **predictive t with df = 5**. That is not in the reference set, and the plug-in `t6` row scores 0.119, so the predictive shift rather than the t family is what puts it level with `logistic`. Recomputed on its own three instances it wins one by 0.0068, ties one to 0.0002 and loses one by 0.0010, a mean edge of 0.0020, which is inside the sampling floor. The honest reading is a tie with the best baseline, not a win over it.

A model that searches carefully arrives back at the naive construction's performance level by a different route. That is what a genuine frontier looks like rather than a scoring artefact.

**Quantile is also the one task where collapsing to the naive method is the right move** rather than the failure the rest of the suite is built to expose, which is worth remembering before reading a tight run-to-run band here as a virtue.

## Limitations

**Four defensible criteria rank the same estimators in incompatible orders.**

| Criterion | Winner | wei8's position |
| --- | --- | --- |
| point accuracy (MAE) | type7 | worst |
| point centring (hit rate) | wei8 | best |
| interval coverage | wei8 / t6 | best |
| interval Winkler | normal | fourth of five |
| pinball regret (this task's metric) | normal | second of six |

This is not a defect to be resolved. It is the most interesting thing the task produces, and it is the model-risk point in miniature: whoever picks the criterion picks the winner.

**A tight band means the score is stable, not that the method is.** Transcripts show models using materially different approaches across seeds that all land in a similar score range, and a same-seed repeat settled which it is: rerunning on byte-identical data still moved the score, so the method variation is sampling temperature rather than a response to the data ([detail](../limitations.md#run-to-run-reproducibility)).

**The reference estimators are being judged on a criterion they were not designed for.** `t6` is the construction of Wei, Wang and Hutson (Commun. Stat. Theory Methods, DOI 10.1080/03610926.2013.775304), whose Q^L is exactly Hyndman-Fan type 6; `wei8` is the same extrapolation around a type-8 interior, a substitution the paper did not test. The paper evaluated 95% confidence-interval coverage, not point accuracy and not pinball regret. None of these rules is "the best" estimator and the table above should not be read as crowning one.

**Cells of different estimand generations are not finely comparable.** Scores measured before the estimand was corrected to include the ten drawn values sit about 0.002 high. That is far inside the sampling floor and changes no ordering, but it is why differences finer than about 0.005 cannot be read across rows. An earlier claim on this page that one model beat every reference estimator was wrong for exactly this reason: it compared corrected model scores against uncorrected baselines.
