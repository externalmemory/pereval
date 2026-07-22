# Quantile Task: Implementation Plan

Small-sample tail quantile estimation from real macroeconomic data. Fifth task in
the suite, and the only one whose ground truth is empirical rather than generated
from a known DGP.

Built on a prior proof of concept in `/mnt/hostshare/quantiles` (see its
`FINDINGS.md`), which established the reference estimators, their properties on
12 quarterly FRED series, and the Wei-Wang-Hutson tail extrapolation this task
benchmarks against.

## The Problem

Given 10 observations drawn from a population of m macroeconomic year-over-year
percent changes, estimate the population's 90th, 95th and 99th percentiles. The
sample quantile is not the estimand: Hyndman-Fan type 7, the `np.percentile`
default, can never exceed the sample maximum and puts the true p95 above its own
estimate roughly three times in four.

## Settled Design

Each instance presents 40 sub-samples, each 10 values drawn uniformly without
replacement from a distinct FRED series' YoY population over a randomised window
of m >= 250, independently scaled by a log-uniform factor in [0.1, 10] with no
location shift, rounded to 4 significant figures, presented unordered. The model
returns per sub-sample point estimates of q90, q95 and q99, plus a 95% interval
for q95.

Score: pinball regret, summed over tau in {0.90, 0.95, 0.99}, normalised by
population IQR, averaged over sub-samples, reported mean +/- SE clustered by
instance.

```
regret(tau) = E_pop[rho_tau(X - qhat)] - min_q E_pop[rho_tau(X - q)]
```

The minimiser is exactly the population tau-quantile, so regret is non-negative
and zero only for a perfect answer. The population is the truth: there is no
Harrell-Davis target, no oracle tuning, and no ambiguity between HD and the
empirical quantile.

Diagnostics reported alongside: hit rate P(qhat95 > population q95), MAE/IQR,
interval coverage, Winkler/IQR, and the spread ratio
`(qhat99 - qhat95) / (x_(10) - x_(9))`.

### Why IQR And Not Standard Deviation

The regret is exactly invariant to the values of observations below the estimate:
each contributes `(1-tau)(qhat - q_tau)/m`, which depends on their count and not
their magnitude. Replacing a population's minimum with -1e6 leaves it unchanged.
Dividing by sd throws that away: the same substitution drives sd from 3.63 to
57735 and the normalised score from 0.0118 to 0.000001, silently deleting the
block from the average, and it would do so precisely on the fat-tailed blocks the
task exists for. IQR depends only on ranks 25-75 and is immune to both tails.

### Why Not Winkler As The Headline

Measured on the pilot: grafting a single fixed interval shape onto every rule's
own point estimate collapses the entire Winkler spread from 3.44-20.62 down to
3.07-4.02. Winkler ranks models almost purely on interval width choice and is
insensitive to the estimand insight the task exists to measure. Shifting a point
estimate across the range spanning type-7 behaviour (hit 0.239) to
median-unbiasedness (hit 0.494) moves Winkler by 4%, and its optimum sits at hit
0.370, so it actively prefers an underestimator. Pinball moves 37% over the same
range and bottoms out at hit 0.494.

### Why Three Quantile Levels

At tau=0.90 the reference estimators are indistinguishable. At tau=0.99 the
bounded ones are structurally stuck while the extrapolating ones pull away. The
p99 - p95 spread, in units of the sample top gap, is a constant for every
reference rule (type8 0.00, HD 0.16, type7 0.36, T8 1.61) while the truth
varies 1.25 to 4.15 across series. Summing over tau captures tail-shape
adaptivity in one scalar, because no fixed multiple of `x_(10) - x_(9)` can get
all three levels right.

## Phase 1: Universe Construction

Gate on this phase before investing in anything else.

`scripts/screen_fred.py`, run offline, output vendored.

1. Enumerate monthly NSA FRED series; compute lag-12 simple percent change.
   Lag 12 is the one operator that removes trend and seasonality together on
   monthly NSA data, exactly as lag 4 does for quarterly.
2. Screen: strictly positive levels; >= 250 YoY observations (about 22 years);
   contiguous monthly grid with no internal gaps; no *persistent* definitional
   break; tie rate among the top 3 order statistics of any 250-window under 1%.
3. Hand-audit a random 20 accepts and 20 rejects.
4. Freeze to `pereval/tasks/quantile/data/series.npz` (float64, about 3 MB for
   500 series, no Git LFS needed) plus a manifest carrying n, skew, exkurt,
   kurt3, sd.
5. Gate: the surviving universe must span the shape box of the 12 quarterly
   series (skew -1.55 to +3.24, exkurt 0.30 to 18.86) and supply >= 40 distinct
   series per instance without reuse. Under about 100 series, stop and
   reconsider.

### Screening Rules That Are Not Obvious

Two rules from the proof of concept were validated the hard way and must be
carried over:

- A period-over-period jump threshold is a *seasonality* detector on NSA data,
  not a redefinition detector. It wrongly rejects genuine seasonal series.
- Magnitude does not separate artifacts from data. Persistence does. M1NS jumped
  4.48x and never reverted (a 2020 savings reclassification, correctly dropped).
  LNU03000000 jumped 3.56x and returned to baseline (real COVID, correctly kept).

### Why Ties Matter

wei8's tail branch is proportional to `x_(n) - x_(n-1)`. If the top two of the
ten drawn values are equal the gap is zero, the extrapolation collapses to the
sample maximum, and the reference estimator silently degrades toward type 7. The
mechanism is quantisation of the source levels, not a ceiling on the YoY change,
so it appears in coarsely published series and would never have surfaced on the
12 large finely-published aggregates the proof of concept used. Screen on it;
do not fix it with jitter, because jitter magnitude would directly set the tail
scale the reference extrapolates from.

## Phase 2: Generator, Estimators, Scorer

- `generator.py` derives per-instance seeds via
  `SeedSequence(base).generate_state(n_instances)`, matching the existing
  `_samples` pattern in `orbit/task.py` and `ccar/task.py`. Data never enters the
  sandbox; only the 400 numbers reach the prompt.
- `estimators.py` ports HF types 6/7/8, Harrell-Davis and wei8 from the proof of
  concept, whose Python port is bit-identical to the R original.
- `pereval/scorers/pinball.py`, alongside the existing `interval.py`.
- Assert monotonicity q90 <= q95 <= q99 and report violations rather than
  silently sorting.

### Regression Test Fixtures

All reproduced independently this session and safe to pin:

| quantity | values |
|---|---|
| hit rate P(est > truth) | T8 0.480, T6 0.540, type7 0.238, HD 0.343 |
| MAE ratio vs type7 | T8 1.208, type8 1.054, HD 1.007 |
| BCa coverage | T8 0.813, T6 0.813, type7 0.284, HD 0.181 |
| BCa length / sd | T8 6.71, T6 6.48, type7 0.64, HD 0.39 |
| p99-p95 spread / top gap | type8 0.00, HD 0.16, type7 0.36, T8 1.61 |

The spread constants are exact and make particularly good fixtures.

One implementation trap worth a test of its own: Harrell-Davis and every HF type
are functionals of the *order* statistics, so the population must be sorted
before any weight vector is applied. Applying HD weights in time order silently
returns a number near the mean and makes every estimator look like it beats the
truth 95% of the time.

## Phase 3: Inspect Task

- `task.py` using `basic_agent` with a submit tool, reusing
  `pereval.tasks.ballistic.task.COMPOSE` (numpy, scipy, statsmodels already
  provisioned, `network_mode: none`).
- Generous message and time limits from the first run, with actual message counts
  recorded. Three of six pilot models produced no answer under a single-turn
  format: one emitted 79k characters of reasoning without reaching its answer,
  one returned an empty completion. That failure class has already corrupted two
  tasks in this suite.
- Missing or unparseable sub-samples are counted and reported as missing, never
  scored as bad estimates.
- The prompt states the estimand precisely: a population of m values, 10 drawn
  uniformly without replacement, the target is the population quantile and not
  the sample's, blocks are different series with different unknown scales and
  cannot be pooled, values are YoY percent changes times an undisclosed positive
  constant.

## Phase 4: Baselines, Runs, README

- `baselines.py`: type7, type8, HD, T6, T8, naive normal theory, and PERFECT
  (the population quantile, regret 0 by construction) as the floor row.
- Run the suite's model cast, transcripts to `runs/`.
- README section with the pinball leaderboard plus the five diagnostic columns,
  and an explicit note that the criteria disagree: type7 wins MAE, T8 wins
  centring and coverage, naive normal theory wins Winkler, and a tuned
  two-parameter oracle beats every reference estimator on Winkler by 2.3x.
  None of these rules is "best": the criteria disagree, and the paper's own
  criterion was interval coverage rather than either of these.

## Open Risks

| risk | check | when |
|---|---|---|
| Universe too small after screening | count survivors, gate at about 100 series | Phase 1, first |
| Monthly YoY shapes differ from quarterly | compare skew and exkurt distributions | Phase 1 |
| Automated screen admits definitional breaks | hand-audit 40 series | Phase 1 |
| Models fail on format, not statistics | agent plus submit tool, generous limits, missing-count reporting | Phase 3 |
| 40 sub-samples still too noisy | SE at 12 sub-samples was 3.07 on Winkler; 320 draws should give about 0.6 | Phase 4 |
| tau=0.99 dominated by target noise | resolved: pinball scores against the population directly, so the HD boundary-squeeze that makes a p99 *target* untenable does not arise | resolved |

## Pilot Evidence

Single-turn, 12 sub-samples drawn from the proof of concept's 12 quarterly
series, seed 1. Not a substitute for a real run, but it established that the task
discriminates.

| model / baseline | pinball(.95) | hit | MAE | Winkler | cov |
|---|---|---|---|---|---|
| PERFECT | 0.0000 | | 0.054 | | |
| naive normal | 0.0157 | 0.333 | 0.515 | 7.04 | 0.833 |
| gpt-5.5 | 0.0164 | 0.500 | 0.468 | 5.63 | 0.917 |
| gpt-5-nano | 0.0177 | 0.250 | 0.538 | 16.42 | 0.417 |
| deepseek-v4-flash-free | 0.0190 | 0.333 | 0.544 | 8.62 | 0.750 |
| T6 | 0.0208 | 0.417 | 0.628 | 9.86 | 0.667 |
| T8 | 0.0215 | 0.417 | 0.594 | 9.54 | 0.667 |
| type8 | 0.0234 | 0.333 | 0.568 | | |
| HD | 0.0255 | 0.167 | 0.567 | 20.62 | 0.250 |
| type7 | 0.0301 | 0.083 | 0.645 | 20.33 | 0.250 |

gpt-5.5 posted a hit rate of exactly 0.500 and the best MAE in the table,
reference estimators included. gpt-5-nano's point estimates matched the
normal-theory rule to 0.075 sd yet it scored 16.42 on Winkler, because its
intervals were wrong.
