# Rating Migration

**Status: built, not measured.** The generator, the four-component scorer, two reference solvers and the Inspect task exist. One smoke test has been run against free models; the task does not appear in the README's score table and will not until there is a cell for every ranked row.

The task gives an agent twenty years of annual rating transition counts for a 10,000-obligor portfolio, quarterly macroeconomic history, a nine-quarter supervisory scenario, and a holdout cohort whose rating mix differs from the historical one. It must project where that cohort stands at quarters 4 and 9, record the quarterly transition matrices it used, and report the annual default rate its model projects for each historical year.

The intended difficulty is annual-to-quarterly conversion. A quarterly matrix obtained by rooting an annual one can be inadmissible: negative or complex migration probabilities, and a non-monotonic relationship between rating and default probability. That is the Markov embedding problem, and the standard references are Israel, Rosenthal and Wei (2001) on when a generator exists, Kreinin and Sidelnikova (2001) on regularising an invalid root, and Higham and Lin on pth roots of stochastic matrices.

The trap is real and it is not tuned. Because the systematic factor moves every quarter, the annual matrix for a year is a product of four different quarterly matrices rather than the fourth power of one, so no quarterly matrix reproduces it. Measured on the exact arithmetic the principal fourth root reaches about -3e-08; with the finite 10,000-obligor portfolio it reaches -7e-03, five orders of magnitude worse, which is what an agent actually meets. Both free models in the smoke test found the negative entries, called them numerical issues, and clipped them.

Bracket: oracle 0.000, one-factor reference 0.287, degenerate 1.000, measured over twenty-four instances at the shipped settings.

## Provenance

All figures come from one document:

S&P Global Ratings, *Default, Transition, and Recovery: 2024 Annual Global Corporate Default And Rating Transition Study*, published 27 March 2025. The document's own sources line reads "S&P Global Market Intelligence's CreditPro and S&P Global Ratings Credit Research & Insights."

Retrieved 29 September 2026 as a 6,632,395 byte PDF (internal modification date 31 March 2025) from `https://maalot.co.il/Publications/FTS20250331162126.pdf`, the site of S&P Global Ratings Maalot, S&P's Israeli affiliate, which hosts the global study. The same study is listed on spglobal.com under the regulatory-disclosure path, where automated retrieval returns HTTP 403.

Two tables were used:

- **Table 20, "2024 one-year corporate transition rates by region (%)"**, four panels: Global, U.S., Europe, and emerging and frontier markets. This is a single-year static pool, which is what makes integer counts recoverable.
- **Table 21, "Global corporate average transition rates, 1981-2024 (%)"**, the one-year and three-year panels, each with a standard deviation beneath every mean.

The PDF itself is not committed. The CSVs hold extracted factual figures with the source cited here.

## How the Counts Were Derived

The study publishes percentages, not counts. For a single-year static pool every entry of a row is an integer count divided by one cohort size, so the counts are recoverable: search cohort size upward and keep the first value for which all nine published entries match an integer count to two decimal places and the counts sum to the cohort size.

`scripts/migration_invert_counts.py` performs that derivation from the committed percentages and checks it against the committed counts, so the chain from source to CSV is reproducible rather than asserted. `tests/test_migration.py` pins the same round trip.

**The cohort size is identified only up to a positive integer multiple**, since a count over a cohort equals twice that count over twice that cohort. The smallest consistent value is used throughout.

**For the Global panel that ambiguity is closed by an external figure.** The reconstructed global default column sums to exactly 130, and the study states separately, in prose rather than in any transition table, that "of the 145 total defaulters in 2024, 130 were rated at the start of the year." Doubling every cohort would imply 260. So the global scale is pinned by a number the reconstruction did not use. This is the strongest single piece of evidence that the counts are the real ones.

For the three regional panels there is no equivalent check and their scale rests on the smallest-cohort choice alone. There is a soft consistency check: the reconstruction gives 86 U.S. defaults from the rated cohort against the study's statement that 97 of the 145 defaulters were U.S. companies, and the 11 difference sits inside the 15 defaulters who were not rated at the start of the year.

## What the Files Contain

| File | Contents |
| --- | --- |
| `data/sp2024_regional_counts.csv` | Reconstructed integer counts and cohort sizes, four regions, six rating rows |
| `data/sp2024_regional_published_pct.csv` | The percentages exactly as printed, for round-trip validation |
| `data/sp_global_average_1981_2024.csv` | Long-run global averages, one, three and five year, mean and standard deviation, AAA included |

`reference.py` loads all three. Nothing in this package enters an agent sandbox; these are host-side calibration numbers.

The global 2024 rated cohort totals 6,496 issuers across the six recoverable rows.

## Default Risk at the Top of the Scale

The point of a transition matrix is to estimate losses, and a bank with exposure to a AAA obligor still has to hold a reserve against it. A model that assigns zero default probability to its best grade implies zero expected loss and therefore zero allowance on a live exposure. That is a defect on its own terms, before any regulator is consulted.

The published data invites exactly that defect. Global AAA to default over 1981 to 2024 is **0.00%** at one year. Taken at face value it says a AAA obligor cannot default. The same table refutes that two rows further down:

| Grade | 1 year | 3 year | 5 year |
| --- | ---: | ---: | ---: |
| AAA | 0.00% | 0.13% | 0.34% |
| AA | 0.02% | 0.11% | 0.28% |
| A | 0.05% | 0.20% | 0.41% |
| BBB | 0.14% | 0.67% | 1.42% |

AAA default risk is positive at three and five years, and at five years it exceeds AA's. So the one-year 0.00% is an absence of observations across 44 static pools, not an absence of risk, and it should be read as a small-sample zero rather than a parameter.

**The regulatory floor names a number for this.** For a US institution the operative one is 12 CFR 217.131(d)(2) (Regulation Q, advanced approaches), "Floor on PD assignment": the PD for each wholesale obligor or retail segment may not be less than **0.03 percent**. The exemptions are exposures to, or directly and unconditionally guaranteed by, a sovereign entity, the BIS, the IMF, the European Commission, the ECB, the ESM, the EFSF, or a multilateral development bank. The Basel Committee's consolidated framework sets a higher 0.05% at CRE32.4, in force 1 January 2023, for every asset class except sovereign; the US has not adopted that figure here, and the March 2026 US proposal would remove the internal-ratings stack rather than raise the floor. Both are recorded in `PD_FLOORS`, with the US value as operative.

**The floor is not a rounding adjustment, it rewrites the top of the scale.** Two of the seven published grades sit strictly below the US floor, AAA at 0.00% and AA at 0.02%, and A sits at 0.05%. So an IRB-consistent model must override the observed rate for its two best grades rather than reproduce it, and flooring AAA at 0.03% puts it between the observed rates for AA and A. Any calibration built from this data has to make that override explicit, and any scoring of a candidate matrix should treat an exact zero in the default column as inadmissible rather than as a good fit.

Extrapolating the top of the scale from grades where defaults are actually observed is the standard remedy, and it is worth recording what it does and does not fix. Fitting the log of the one-year default rate against grade over BBB, BB, B and CCC/C gives a good fit, R-squared 0.989 at 5.66 times per notch, and projecting upward yields 0.004% for AA and 0.001% for AAA. That removes the exact zero, which is the defect, but it lands an order of magnitude **below** the 0.03% floor, so the floor still binds and remains the operative constraint rather than a formality.

The same fit also understates a grade where defaults are observed: it projects 0.020% for A against 0.050% actual. The reason is that the notch multiplier is not constant, it steepens down the scale, running roughly 2.8 times from A to BBB, 4.0 from BBB to BB, 5.2 from BB to B and 8.9 from B to CCC/C. A single log-linear slope fitted on speculative grades is therefore too steep to extrapolate into investment grade and will push the top of the scale too low. Any candidate method for the top grades has to be checked against both the floor and the observed A and BBB rates, not just fitted to the tail.

## The Data Rejects a Time-Homogeneous Markov Chain

This matters more than any calibration detail, because it is the empirical premise of the task. The study publishes both a one-year and a three-year average matrix over the same 44 static pools. If rating migration were a time-homogeneous Markov chain then the three-year matrix would be the cube of the one-year matrix. It is not. Treating default and withdrawal as absorbing, the cube understates the published three-year default probability:

| From | Cubed one-year | Published three-year | Ratio |
| --- | ---: | ---: | ---: |
| AAA | 0.042% | 0.130% | 0.32 |
| AA | 0.085% | 0.110% | 0.77 |
| A | 0.176% | 0.200% | 0.88 |
| BBB | 0.523% | 0.670% | 0.78 |

The direction is the same under either treatment of withdrawals, absorbing or dropped and renormalised, so it is not an artefact of that choice. It is consistent with the documented tendency of downgraded issuers to keep migrating downward, which a memoryless chain cannot represent.

The consequence for the task is that rooting an annual matrix is not merely numerically awkward, it is fitting a model the data rejects. An agent that produces a clean quarterly matrix by taking a principal root has not solved the problem, it has assumed away the part that makes multi-period default rates come out right. `tests/test_migration.py` asserts this gap so that a later edit to the reference data cannot quietly remove it.

## Limitations of the Reference Data

- **AAA has no recoverable 2024 count row**, because its published 2024 row is 100% on the diagonal, which fixes no cohort size. That is a gap in the counts only. AAA is in `RATINGS` and is present at all three horizons in the long-run averages, and it must stay in any state space; see Default Risk at the Top of the Scale below.
- **The long-run averages do not invert.** They are averages over 44 annual static pools, so there is no single cohort size behind them. They are for calibrating a plausible range, not for reconstructing a cohort.
- **2024 was a benign year for investment grade and a harsh one for CCC.** Global BBB to default was 1 of 1,848, or 0.05%, against a long-run mean of 0.14%, while CCC/C to default was 28.36% against a long-run 26.12%. A single year is not representative in either direction, which is why both the year and the long-run averages are stored.
- **Withdrawals are a column, not a nuisance.** `NR` carries 3% to 19% of each cohort. How it is treated, absorbing, dropped and renormalised, or modelled as a competing risk, changes implied default probabilities materially, and the naive choice biases them. This is a modelling decision the task will have to take a position on.
- **One agency, one asset class.** Corporate issuer ratings from a single agency. Cohort sizes are small at the ends of the scale: 27 issuers in Europe AA, 48 in EM CCC/C.

ESMA's CEREP publishes transition matrices as counts directly, including a withdrawals column, filterable by agency, asset class and region, with CSV export. That is the better source for published rather than reconstructed counts, and the route to a second agency for cross-checking. Its interface is a JSF application that is not practical to script, so anything from it would be pulled by hand.

## Admissibility Is a Tie-Breaker, Not a Weight or a Gate

The agent is asked for the quarterly transition matrices it used, in `matrices.csv`, and the prompt says only that this documents how the projection was produced. It does not say what is examined. The point of the silence is to test whether an agent raises, unprompted, the questions a review function would: that a transition matrix needs non-negative entries and rows summing to one, that default probability must not improve as credit quality worsens, and that the documented model must actually reproduce the reported projection. Telling the agent what is checked would turn that into a compliance exercise.

Zero probabilities are the interesting case. A projection of exactly zero defaults allocates no reserve to a live exposure, which is imprudent whatever the long-run average works out to, and it cannot be revised by evidence. A portfolio of ten obligors at 1% should project 0.1 expected defaults, not 0, even though no one ever observes 0.1 defaults. This is a known weakness of the Kreinin and Sidelnikova style remedy for an invalid matrix root: clipping negatives to zero and renormalising produces exact zeros, which violates Cromwell's rule.

The generator was guilty of it. The fourth root of the published annual average inherited four exact zeros, one of them AAA to default, because the published AAA one-year rate is 0.00% and a root of zero is still zero. The oracle would have failed the check the task poses. Every live cell is now floored at 1e-9 and the default column at the quarterly equivalent of the 0.03% annual minimum from 12 CFR 217.131(d)(2), with the default column held fixed while the rest of each row rescales.

**How it affects the score: it does not.** Holding the generator fixed and degrading only the reference's own matrices:

| Reference variant | Score | Exact zero cells | Ordering inversions |
| --- | ---: | ---: | ---: |
| floors and imposes ordering | 0.1585 | 0 | 0 |
| leaves the fourth root's zeros | 0.1584 | 26.8 | 4.5 |
| floors but leaves ordering to noise | 0.1584 | 0 | 4.5 |

Twenty-seven exact zeros and four and a half ordering inversions per instance cost under half a percent of the score on a single instance and under a hundredth of a percent averaged over twelve, against the reference's own error of 0.158. The defect is orthogonal to accuracy rather than merely small.

That rules out two treatments and leaves one. A weight would be fiat, because there is no accuracy cost to calibrate it against, and putting it in the number recreates the materiality argument inside the metric instead of avoiding it. A gate would disqualify a model whose accuracy is unaffected, which is not what a review function does: it assesses materiality, finds it small, issues a model limitation and approves. All models are wrong and some are useful, and here there are far larger error sources than a probability that is almost rather than exactly zero.

So admissibility breaks ties. But the defects are not all of one kind, and the measurement separates them into three tiers rather than one flag.

**Rows must sum to one. This is the hard one.** A matrix whose rows do not is not a collection of probability distributions, so it cannot be the model that produced the projection, and the breach is consequential rather than cosmetic. Scaling every row to 1.2 drives the gap between the submitted distribution and what the submitted matrices actually propagate to from 0.0000 to 2.5163, because mass non-conservation compounds over nine quarters. `matrix_rows_valid` records it, and a failure there is incomplete documentation rather than an accuracy penalty: the agent was asked to record its model and did not.

**Negative cells sit in the middle.** They also mean the object is not a distribution, but clipping them to zero is a defensible remedy that Kreinin and Sidelnikova use, and a single small negative is numerically near-harmless: the same gap moves only to 0.0001, because mass is still conserved. `matrix_nonnegative` flags it rather than failing it.

**Exact zeros and a non-monotone default ordering are soft.** They leave a perfectly valid distribution that is imprudent or odd, and they cost nothing measurable in accuracy. Tie-breaker only.

`matrix_admissible` is the flag for the tie-break and requires all three tiers to be clean. Where two cells sit within the resolution this suite claims, a factor of a few, prefer the admissible one. The component counts stay reported for diagnosis. `tests/test_migration_task.py` pins both the immateriality measurement and the tier separation, so a later change that makes admissibility material, or that collapses the tiers, fails the test rather than quietly surviving.

One limit worth stating. A clean submitted matrix cannot distinguish an agent that reasoned about admissibility from one that clipped silently and got lucky. Both free models in the smoke runs found the negative entries and still called them numerical issues. That reasoning lives in the transcript, and grading it would need a judge, which this suite does not use.

## The Scenario Has a Trough, Which Cost Something

The horizon was initially monotone. Every macro series deteriorated for all nine quarters without turning, because the inherited CCAR overlay ramps level series linearly to a target and holds growth series at a constant stressed rate, and neither construction can reverse. In `severe` unemployment ran from -0.22 to +1.24 standard deviations in a straight line.

Published supervisory scenarios are not shaped like that. They deteriorate for a few quarters, turn, and recover partly; the stress phase typically lasts two to six quarters rather than the whole horizon. The horizon is now reshaped accordingly, in this generator rather than CCAR's so that task's archived measurements are untouched. A severity weight rises to its peak at a drawn quarter and decays linearly to a drawn residual, with the peak quarter and residual both scenario-dependent: two to three quarters and up to 30% residual for `baseline`, three to five and 20 to 45% for `adverse`, four to six and 35 to 60% for `severe`.

The systematic factor peaks one to two quarters after the macro path does, which is not a defect: credit deteriorates after the economy does.

| Scenario | 9-quarter portfolio default | Annualised |
| --- | ---: | ---: |
| baseline | 2.66% (1.43 to 5.42) | 1.19% |
| adverse | 7.22% (3.14 to 12.24) | 3.29% |
| severe | 17.22% (6.13 to 31.16) | 8.20% |

Baseline annualises to 1.19% against the 0.99% the portfolio mix was calibrated for, which is the holdout cohort being deliberately riskier than the history.

**Two things the change cost, recorded because one of them contradicts a prediction made before it.**

The trap is unaffected, and the reasoning that suggested it would improve was wrong. A realistic hump makes the annual matrix MORE embeddable, not less: the principal fourth root reaches -3.5e-09 under a trough against -1.0e-07 under the monotone ramp. Only a violent reversal, a factor swinging plus and minus two within a year, strengthens it, by a factor of five thousand. All of it is immaterial anyway, because finite-portfolio sampling contributes about -7e-03, four to six orders of magnitude more, and that is what an agent actually meets.

The checkpoints became less independent, not more. The expectation was that a turn between quarter 4 and quarter 9 would make them distinct tests. The opposite happened: correlation between the two shape components rose from 0.59 to 0.65 and between the two default components from 0.64 to 0.78, taking the four-component score from 2.74 to 2.44 effective dimensions. The reason is that the default target is cumulative and absorbing, so quarter 9 contains quarter 4. Front-loading the stress means most defaults have already occurred by the first checkpoint and the second adds only a thinning tail. A monotone ramp puts the heaviest stress last, so its second checkpoint carries proportionally more new information.

Realism and checkpoint independence pull in opposite directions here. Realism won, because the task's claim is to resemble a supervisory exercise and a one-way ramp does not.

The bracket moved slightly: reference 0.179, degenerate 1.000, separation 5.6x, against 0.158 and 6.3x under the monotone ramp.

## Twenty Years of History, Not Forty

The task ships `n_years=20`. The choice is about what a bank actually has, and it turned out to sharpen the trap as well.

Calibration data for a stress model has to span benign and stressed conditions and has to be relevant to the portfolio. Twenty years covers two downturns, 2008 and 2020. Going further back buys observations from a different policy regime: NBER peaks from 1948 to 1982 come one every 4.3 years, since 1982 one every 11, and the variance break is conventionally dated to 1984Q1 (McConnell and Perez-Quiros, *American Economic Review* 2000; Kim and Nelson, *Journal of Business & Economic Statistics* 1999). Rating transition data itself goes back to 1981, so availability is not the binding constraint; portfolio relevance is. A bank's own rating scale rarely survives forty years intact through scale redefinitions, model replacements and acquired books. Twenty years is still four times the five-year minimum for wholesale PD estimation in 12 CFR 217.122.

Shortening the history strengthens the embedding problem, because the pooled counts halve and the principal fourth root of a noisier annual matrix is further from admissible.

| | Most negative root entry | Mean over instances | Count cells with no observations |
| --- | ---: | ---: | ---: |
| twenty years | -1.38e-04 | -7.63e-05 | 5.4 of 56 |
| forty years | -6.28e-05 | -2.23e-05 | 3.5 of 56 |

Two to three times stronger, and half again as many cells where a transition was never observed, which is the Cromwell's-rule problem arriving on its own rather than by construction.

### It Broke the Reference, Which Had to Be Fixed Rather Than Avoided

The reference's factor regression has seven parameters. On forty annual observations that is fine. On twenty it overfits badly: over eight seeds and three scenarios it loses to the degenerate on five of twenty-four draws and reaches 1.479.

| | Mean | Median | Max | Loses to degenerate |
| --- | ---: | ---: | ---: | ---: |
| twenty years, unshrunk | 0.453 | 0.194 | 1.479 | 5 of 24 |
| forty years, unshrunk | 0.210 | 0.193 | 0.393 | 0 of 24 |

The identical medians say this is not a uniform loss of information but a tail of blow-ups. The symptom is a projection of +6.40 where the truth is +3.44 and the worst year in the estimation sample was +2.70. The cause is coefficient inflation across six collinear drivers when the data-generating process uses two: at twenty years the loadings on the failing draws sum to 2.18 in absolute value against 1.48 at forty. They offset each other inside the historical range and stop offsetting once the scenario moves the drivers differently.

### What Does Not Fix It

**Bounding the projection is not available, even though it works.** Clipping the projected factor to the range of the estimated annual factors scores 0.246 against 0.287 and never fails. It is still wrong. A stress model exists to answer scenarios more severe than anything observed. The Federal Reserve's scenario design framework for the severely adverse scenario specifies an unemployment path that rises by three to five percentage points or to ten percent, whichever is higher, without reference to whether that has happened before, and this generator's `systematic_factor` says the same thing from the other side: the scenario window is where the factor is supposed to go out of range. A model that cannot go there fails the only question it is asked, and handling of extreme macro inputs is a review checklist item about whether the response stays monotone and finite out there, not about refusing to compute it. The reference therefore projects without a bound and reports `factor_response_diagnostics` instead, which pushes the scenario to three times its distance from the historical mean and checks monotonicity and finiteness. It still projects past its own historical maximum on eight of twenty-four draws, which is the behaviour being preserved.

**Dropping features is worse than shrinking them.** Cutting to the three recession-up levels, four parameters instead of seven, gives 0.565 against 0.453 and still fails five of twenty-four. Collapsing all six drivers into one signed composite index gives 0.652, and fails three of twenty-four even at forty years. The drivers carry separate signal, so the problem is the size of the coefficients and not their number.

**Selecting one driver of each sign by BIC trades the mean for a tail.** It gives the best median of any variant, 0.144, and still fails two of twenty-four, because when the selection picks the wrong pair it is badly wrong with no shrinkage left to absorb it.

**Economic sign constraints are a no-op here.** Requiring unemployment, the BBB spread and the VIX to load non-negatively on stress and GDP, HPI and NASDAQ growth to load non-positively is a standard review checklist item, and it changes nothing: 0.286 against 0.287, same failures. The blow-up draws have correctly signed loadings that are simply too large. Worth recording as a negative result, since the intuitive diagnosis is wrong.

**Leave-one-out cross-validation does not work**, and this is the finding worth keeping. It picks a penalty of 0 to 0.3 and still fails three of twenty-four. Every held-out year lies inside the historical range while the scenario lies outside it, so in-time validation is blind to extrapolation error by construction. That is not an artefact of this generator; it is why stress projections get bounded by judgment in practice rather than validated in sample.

### What Ships

Shrinkage alone, with the penalty from a sample-size rule.

| Twenty years | Mean | Median | Max | Loses to degenerate | Penalty | Projects past history |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| unshrunk | 0.453 | 0.194 | 1.479 | 5 of 24 | 0 | 10 of 24 |
| sign constraints only | 0.442 | 0.287 | 1.168 | 5 of 24 | 0 | 10 of 24 |
| BIC-selected pair | 0.298 | 0.144 | 1.047 | 2 of 24 | 0 | 10 of 24 |
| **shrinkage, shipped** | **0.287** | 0.256 | 0.662 | 0 of 24 | 0.847 | 8 of 24 |
| shrinkage and sign constraints | 0.286 | 0.256 | 0.662 | 0 of 24 | 0.847 | 9 of 24 |
| clipped to history, rejected | 0.246 | 0.243 | 0.517 | 0 of 24 | 0.847 | 0 of 24 |

The penalty is set so the regression spends an effective dimension of `1 + n/8`: 0.847 at twenty annual observations and 0.104 at forty. It is a rule rather than a tuned constant, so a shorter history shrinks harder without anyone retuning it. Tuning the penalty directly against the score wanted 1.0; that the rule independently lands at 0.847 is the reassurance that the rule is not arbitrary, and the tuned value is not what ships because it was chosen by looking at the target.

At forty years the same rule picks a light penalty and still helps, 0.190 against 0.210, so nothing here is specific to the short history.

Bracket at the shipped settings: reference 0.287 over twenty-four instances, 0.303 over the eighteen the test uses, degenerate 1.000, separation 3.5x and 3.3x, against 4.8x at forty years unshrunk. Refusing the clip costs 0.041 of that, which is the price of a reference that can answer the question the task asks.

Nothing in the prompt mentions sample size or overfitting. Recognising that twenty annual observations will not support an unshrunk macro regression is part of what the task measures.

## Backtesting Against the Stressed Years

The task asks for a third file, `backtest.csv`: the annual default rate the model projects for each HISTORICAL year, against the portfolio that year actually started with. That is the backtest a developer draws before anyone else sees the model, and it is the one output here that is asked for because a reviewer would ask for it rather than because the scorer needs it.

Three design choices, all measured.

**One-sided.** A stress test is asked one question: how large are losses under a given scenario. Understating them is the failure that matters, because a bank survives its benign years whatever the model says about them, and overstating them is conservative rather than wrong. So every statistic is a ratio of projected to observed, only values below one are findings, and there is no upper limit and no two-sided test.

**No confidence interval is requested.** An actual stress test requires point estimates of expected losses under given scenarios; the interval is an implementation detail left to the developer. The reference computes one anyway, in `backtest_diagnostics`, because the chart a reviewer reads has a band on it, but nothing asks the agent for one and nothing scores one.

**The projections are asked for rather than reverse engineered.** An earlier design tried to infer the historical fit from the submitted scenario matrices. There is nothing to infer it from, and asking is what a reviewer does.

### What the Statistic Detects

Scaling the reference's macro response by a factor k, holding the mean factor level fixed, over twenty-four instances:

| k | 0.00 | 0.25 | 0.50 | 0.75 | 1.00 | 1.50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| projected / observed, stressed years | 0.26 | 0.32 | 0.40 | 0.51 | 0.66 | 1.07 |
| band's upper edge misses the peak | 75% | 75% | 50% | 50% | 25% | 12% |

The ratio is monotone over a factor of four and needs no interval construction at all. The band is for the chart; the ratio carries the signal. A model with half the right macro sensitivity under-projects the nine-quarter loss by 32%, and one with none under-projects by 60%.

The contrast between the stressed years and all years is itself informative: the shipped reference reads 0.69 over the stressed quarter of its history against 0.84 over all of it, so the under-prediction is concentrated exactly where it matters.

### The Upper Bound Is at the 97.5th Percentile

The residual is `logit(observed) - logit(fitted)`, assumed logistic and moment-matched, divided by `n` minus the effective degrees of freedom rather than by `n`, which widens it about thirteen percent for free. Three candidate bounds, by the fraction of instances where the band misses the observed peak:

| Upper bound | k = 0, no macro response | k = 1, correct | k = 1.5 |
| --- | ---: | ---: | ---: |
| 95th percentile, 1.623 SD | 88% | 50% | 12% |
| 97.5th percentile, 2.020 SD | 75% | 25% | 12% |
| 99th percentile, 2.533 SD | 12% | 25% | 0% |

The 95th flags half of all correctly specified models. The 99th inverts: an insensitive model's residuals are so large that its own band swallows the peak and discrimination dies. Only the 97.5th both fires on under-sensitivity and mostly spares a correct fit. Going one-sided does not license a tighter bound; it relabels a two-sided 95% interval as the one-sided 97.5% bound it already was.

The logistic assumption is not load-bearing. A normal's 1.960 standard deviations against the logistic's 2.019 is three percent, and forward coverage came out identical at 91.7% either way. The quantile task's finding that a moment-matched logistic beats a moment-matched normal is located at tau = 0.99; at 0.975 the families are indistinguishable.

### What It Cannot Do, Measured

The band is computed from the residuals of the fit it is drawn around, so it shrinks as the fit tightens and **cannot detect overfitting**. The unshrunk reference covers the observed peak on every instance, covers its stressed years at 97.5% against the shrunk fit's 85.0%, and draws a band thirty percent tighter, while its actual forward coverage is 75% against a nominal 95%. On the chart the overfit model looks better calibrated than the correct one.

Leave-one-out residuals move it the right way and not far enough: the overfit model's forward coverage rises to 83.3%, and it still reports the narrower band, 0.443 against the shrunk fit's 0.561, so the chart still prefers it. Jackknife+ and conformal guarantees hold under exchangeability, and a severely adverse scenario denies exchangeability by construction, which is the same blindness that disqualified cross-validation for the ridge penalty.

Detecting underfitting is what this is for, and at that it works.

"Did the band cover the peak" also must not be read as a pass/fail test. A perfectly calibrated pointwise 95% band excludes the largest of twenty draws with probability `1 - 0.975**20 = 40%`, and the correct model measures 25% here. The continuous ratio is the statistic; the binary version is noise.

### The Reference Fails Its Own Check

| | projected / observed, stressed years | factor swing retained | under-projects forward |
| --- | ---: | ---: | ---: |
| shrunk, shipped | **0.66** | 73% | 33% of instances |
| unshrunk | 1.02 | 97% | 4% of instances |

**The shrinkage that stops the reference blowing out on the projection also damps its macro response, so it under-fits the stressed years by about a third.** Ridge shrinks coefficient magnitude, and coefficient magnitude is the macro response. There is no reparameterisation out of it. Variance matching, rescaling the fitted deviation so its spread matches the annual factor estimates, restores the sensitivity exactly and brings the blow-ups back worse than before:

| | Score | Max | Loses to degenerate | Projected / observed, stressed years |
| --- | ---: | ---: | ---: | ---: |
| unshrunk | 0.453 | 1.479 | 5 of 24 | 1.02 |
| shrunk, shipped | 0.287 | 0.662 | 0 of 24 | 0.66 |
| variance-matched | 0.705 | 2.002 | 5 of 24 | 1.01 |
| half-matched | 0.430 | 1.232 | 3 of 24 | 0.81 |

The damping and the stability are the same quantity. The score, being an accuracy measure, rewards the damping; a stress reviewer would reject it and issue a finding for insufficient macro sensitivity.

This is recorded rather than fixed, and it sharpens what the task measures. The anchor is competent and challengeable rather than a target: an agent that beats 0.287 while keeping its stress ratio near one is doing something the score alone cannot see.

### Diagnostics Reported

From `backtest.csv`, against the observed annual rates: `fit_stress_mean_ratio` over the worst quartile of years, `fit_peak_ratio` at the single worst year, `fit_all_years_ratio` for the contrast, and `fit_peak_lag` for timing, suppressed when the projected series is flat and so has no peak. From `matrices.csv` and the truth: `stress_mean_ratio` and `stress_peak_ratio` on the nine-quarter loss path, `stress_peak_lag`, and `default_ratio_q4` and `default_ratio_q9`. None of it enters `score`.

## What the Silent Check Measured

The first run under the prompt that asks for `matrices.csv`, two free models over the same three instances, with both reference solvers for comparison.

**These scores are stale.** They were produced before the scenario was given a trough and before the history was shortened to twenty years, so the numbers below do not describe instances the task now generates. What survives is the qualitative finding in the last column, since the prompt and the diagnostics did not change. The run has to be repeated before migration can become a reported column.

| Row | Mean score | Worst | Rows sum to one | Negative cells | Submission gap | Monotonicity violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| one-factor reference | 0.302 | 0.436 | 5 of 5 | 0 | 0.0000 | 0 |
| nemotron-3-super (free) | 0.629 | 0.965 | 2 of 2 supplied | 0 | 0.0000 | 9, 0 |
| nemotron-3-ultra (free) | 0.772 | 1.215 | 3 of 3 | 0 | 0.0000 | 10, 18, 26 |
| degenerate | 1.000 | 1.000 | — | — | — | 0 |

Ultra's severe instance at 1.215 is the first model result on this task worse than predicting that nothing happens.

**The hard constraint was respected without being asked for.** Every supplied matrix has rows summing to one, no negative cell survived, and the submission gap is 0.0000 in every case, so each agent's documented matrices reproduce its own reported projection exactly. The matrices are genuinely the models used, not decoration.

**The judgment-dependent constraint was not noticed at all.** Default monotonicity is violated 9, 0, 10, 18 and 26 times against 54 adjacent-pair checks per instance. Ultra's severe matrix inverts 48% of adjacent pairs: it asserts that better-rated obligors default more often. Across six transcripts, "rows sum", "sum to one" and "renormalise" appear between 5 and 19 times each, while "monotonic" appears once, referring to a bisection converging in a scalar rather than to the rating ordering, and "prudent", "reserve" and "implausible" appear not at all.

The split is explained by whether the constraint is self-enforcing. Rows summing to one has a mechanical consequence: mass leaks and the projection misbehaves, and scaling rows to 1.2 drives the submission gap from 0.0000 to 2.5163. An agent is dragged to it by the arithmetic. Monotonicity has no mechanical consequence and costs under half a percent of the score, so it matters only to someone who already knows a transition matrix should have it. That is the domain judgment a review function supplies, and neither model supplied it.

This is also the evidence for the tie-breaker treatment rather than a gate. Gating on monotonicity would have disqualified both models for a defect costing nothing measurable, which is the over-reaction the materiality argument rules out. Reporting it lets the defect be seen without pretending it drove the score.

One operational gap. nemotron-3-super produced no parseable `matrices.csv` on one of three instances, which is also its worst-scoring one, so `matrix_provided` is 0.67 for that row and the other diagnostics are absent rather than zero for that sample. Aggregating a row whose matrix is sometimes missing needs a convention before this becomes a reported column.

## How the Open Design Questions Were Resolved

These were the questions this page listed while nothing was built. They are kept because the answers are the design, and because two of them were answered differently from the way they were posed.

1. **Where the oracle comes from.** Handing an agent a real published annual matrix and asking for the quarterly one has no verifiable answer, because a stochastic root need not be unique and most empirical annual matrices are not embeddable at all. The target has to be something generated forward from a hidden quarterly law, or a downstream economic quantity, rather than the matrix itself.

   *Resolved as posed.* The oracle is the exact expected cohort distribution under the hidden quarterly law, propagated deterministically, so it is exactly zero and carries no Monte Carlo error.
2. **What is scored.** Scoring a matrix entrywise forces arbitrary choices of norm and of how to weight the default column against the diagonal. A scalar economic output, such as cumulative default probability by initial rating over a horizon, fits the rest of this suite better and makes an inadmissible intermediate matrix show up as a bad score rather than being the scored object.

   *Resolved as posed, then split.* One scalar was not enough: the nine-quarter default rate alone leaves the rating distribution untested. The score is four components, a Kolmogorov-Smirnov distance on the seven live grades and the cumulative default share, at quarters 4 and 9, each divided by what the degenerate scores on it so the four are commensurable.
3. **Admissibility as a separate diagnostic.** Negative entries, rows not summing to one, and violations of rating monotonicity belong alongside the regret, in the way `completion` sits alongside the CECL score, rather than inside it.

   *Resolved differently.* Reporting alongside was right, but one tier was not enough. Rows summing to one is a hard validity condition a scorer may penalise; negative cells clipped to zero are defensible, as Kreinin and Sidelnikova do; and exact zeros and non-monotone default columns are soft tie-breakers, because materiality is small and model risk management issues a limitation rather than a rejection. Three tiers, not one, and none of them a gate.
4. **How macros enter.** The conventional form is a systematic credit-cycle factor shifting ordered-probit thresholds, which would give a per-instance hidden response law of the kind the CCAR generator now draws.

   *Resolved as posed, with one correction.* The factor shifts cumulated thresholds, which preserves row sums and monotonicity by construction. The correction was that recession-down drivers must enter as year-over-year change rather than as levels: standardised against their own trending history, a stressed scenario otherwise sits two standard deviations on the wrong side of it.

5. **What the scenario path looks like.** Not on the original list, and it should have been. The inherited overlay deteriorated monotonically across all nine quarters, which no published supervisory scenario does. It now has a trough.

6. **Whether the model's response to macros is strong enough.** Also not on the original list. The score is an accuracy measure and cannot see the difference between a model that is right on average and one that is too insensitive to stress, which is the direction that under-reserves. That is what `backtest.csv` and the one-sided ratios are for, and the shipped reference fails them.
