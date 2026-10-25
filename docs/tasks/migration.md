# Rating Migration

**Status: measured and published.** The generator, the scorer, three reference solvers and the Inspect task exist, and the one-history, three-scenario shape described below has been run against all nine models in the README's score table, three instances each at `-T seed=1`, with a cell for every ranked row. It is the eighth column of that table.

Worst-case regret per model, lower better: Kimi K3 **0.301**, GLM-5.1 0.523, mimo-v2.5 0.556, deepseek-v4-flash-0731 0.625, minimax-m3.1-flash 0.629, nemotron-3-ultra 1.214, nemotron-3-super 1.400, ling-3.0-flash 1.612, Claude Haiku 4.5 **4.068**, against the competent reference's 0.368 and the degenerate answer's 1.000. Only Kimi K3 is inside the reference and four models are outside the degenerate, the most of any column in the suite. Two cells are weaker evidence than the rest: minimax's 0.629 is set by one of two instances the six-hour clock truncated, and is an upper bound rather than a measurement, and Claude Haiku's instances 1 and 2 are the first runs in this repo to have working prompt caching.

The free-model smoke tests and the earlier MiniMax run were taken under the earlier rotated shape and their scores are not comparable to anything this version produces.

The task gives an agent twenty years of annual rating transition counts for a 10,000-obligor portfolio, quarterly macroeconomic history, three nine-quarter supervisory scenarios over the same future quarters, and a holdout cohort whose rating mix differs from the historical one. It must estimate one model, project where that cohort stands at quarters 4 and 9 under each scenario, record the quarterly transition matrices it used, and report the annual default rate its model projects for each historical year.

The intended difficulty is annual-to-quarterly conversion. A quarterly matrix obtained by rooting an annual one can be inadmissible: negative or complex migration probabilities, and a non-monotonic relationship between rating and default probability. That is the Markov embedding problem, and the standard references are Israel, Rosenthal and Wei (2001) on when a generator exists, Kreinin and Sidelnikova (2001) on regularising an invalid root, and Higham and Lin on pth roots of stochastic matrices.

The trap is real and it is not tuned. Because the systematic factor moves every quarter, the annual matrix for a year is a product of four different quarterly matrices rather than the fourth power of one, so no quarterly matrix reproduces it. Measured on the exact arithmetic the principal fourth root reaches about -3e-08; with the finite 10,000-obligor portfolio it reaches -7e-03, five orders of magnitude worse, which is what an agent actually meets. Both free models in the smoke test found the negative entries, called them numerical issues, and clipped them.

Bracket: oracle 0.000, one-factor reference 0.285, single-driver naive 0.487, degenerate 1.000, measured over twelve instances at the shipped settings, each instance carrying all three scenarios. The reference's per-scenario composites are 0.228 baseline, 0.284 adverse, 0.343 severe, monotone in severity.

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

The published data invites exactly that defect. Global AAA to default over 1981 to 2024 is **0.00%** at one year. Taken at face value it says a AAA obligor cannot default.

It says no such thing, and the reason is not in the data. A frequency of zero is not a probability of zero. Cromwell's rule is the direct objection: assigning probability zero to an event that is not logically impossible fixes it there permanently, because Bayes multiplies and no quantity of later evidence can move a zero. A grade carrying a zero default probability is a grade that cannot be revised downward by anything that subsequently happens, which is the opposite of what a rating is for. The second objection is that the estimator assigning the rating cannot produce the number anyway: a logistic or ordered-logit link maps any finite score into the open interval (0, 1), so zero is outside its range by construction. The published 0.00% is a count of what happened in 44 static pools, not a parameter.

| Grade | 1 year | 3 year | 5 year |
| --- | ---: | ---: | ---: |
| AAA | 0.00% | 0.13% | 0.34% |
| AA | 0.02% | 0.11% | 0.28% |
| A | 0.05% | 0.20% | 0.41% |
| BBB | 0.14% | 0.67% | 1.42% |

The longer horizons are consistent with that reading but do not establish it, and an earlier version of this section claimed they did. AAA cumulative default risk is positive at three and five years, and at five years it exceeds AA's, but these are cohort rates for issuers *initially* rated AAA: they count obligors downgraded in an early year that defaulted later from a lower grade. A one-year AAA to D probability of exactly zero is entirely compatible with them, so they cannot refute it. The one-year 0.00% is a small-sample zero rather than a parameter, and the argument for that comes from Cromwell's rule and from the form of the estimator rather than from the table.

**A regulatory floor names a number, and it is the wrong number for this task.** For a US institution the operative floor is 12 CFR 217.131(d)(2) (Regulation Q, advanced approaches), "Floor on PD assignment": the PD for each wholesale obligor or retail segment may not be less than **0.03 percent**. The exemptions are exposures to, or directly and unconditionally guaranteed by, a sovereign entity, the BIS, the IMF, the European Commission, the ECB, the ESM, the EFSF, or a multilateral development bank. The Basel Committee's consolidated framework sets a higher 0.05% at CRE32.4, in force 1 January 2023, for every asset class except sovereign; the US has not adopted that figure here, and the March 2026 US proposal would remove the internal-ratings stack rather than raise the floor. Both are recorded in `PD_FLOORS` as reference facts and **neither is applied** to the generator or the solvers.

**Why not.** A capital floor constrains a regulatory PD estimate, which is a long-run through-the-cycle average and so insensitive to the macroeconomy by construction. What this task produces is the opposite object: point-in-time, macro-conditional quarterly transition probabilities for a stress projection, the CCAR and CECL regime rather than the Basel one. A conditional PD in a benign quarter can legitimately sit far below a through-the-cycle floor, and that is not a modelling error to be corrected. Worse, a top grade pinned at a floor has no macro sensitivity left in it at all, which is precisely the defect the rest of this document is built to detect.

**The floor did real damage before it was removed.** Annualised, 0.03% becomes 7.500844e-05 a quarter, and that value bound not one grade but two. It pinned AAA and AA to the identical number and overwrote AA's own rooted value of 3.939e-05 upward by about a factor of two, so the generator's hidden truth asserted that its two best grades carried exactly equal risk. A tie is a weaker defect than an inversion and easier to miss, since no ordering check fires on it, but a truth that says AAA and AA are equally risky is still wrong about the portfolio the task is built on.

**What replaces it is an estimate, not an imposition.** The one-year AAA rate needs replacing for a reason that has nothing to do with capital: it is 0.00%, the fourth root of zero is still zero, and a grade assigned zero default probability carries zero allowance on a live exposure and can never be revised by evidence. So `top_of_scale_annual` extends the notch ratio from the top of the scale where defaults **are** observed. A over AA is 0.05% over 0.02%, a factor of 2.50, and one more notch up gives AAA **0.008%** annual, 2.0e-05 a quarter. Only AAA is replaced; every other grade keeps what the root gives it.

| grade | before, with the floor | after |
| --- | ---: | ---: |
| AAA | 0.0300% | **0.0080%** |
| AA | 0.0300% | **0.0158%** |
| A | 0.0483% | 0.0483% |

The ordering of the top two grades now comes out of the data instead of out of a constant, which is the whole point.

**Why that estimate and not the obvious alternative.** Fitting the log of the one-year rate against grade over BBB, BB, B and CCC/C fits well, R-squared 0.989 at 5.66 times per notch, and extrapolates to 0.004% for AA and 0.001% for AAA. It is rejected because the notch multiplier is not constant, it steepens down the scale, running roughly 2.8 times from A to BBB, 4.0 from BBB to BB, 5.2 from BB to B and 8.9 from B to CCC/C. A slope fitted on speculative grades is too steep for investment grade, and the test is that it understates a grade where defaults **are** observed: it projects 0.020% for A against 0.050% actual, wrong by a factor of 2.4. The single-notch extension uses only the ratio adjacent to the grade it is estimating, so it is not exposed to that curvature.

The result also sits inside the bounds available. Below AA's observed 0.02%, so the top-two ordering is data. Above zero. And below the loosest upper bounds, the constant-hazard reads of the three and five year AAA rates at 0.043% and 0.068% per year, which overstate the first year because a cumulative multi-year figure counts obligors downgraded before defaulting.

One caveat recorded rather than smoothed over: at three and five years the published AAA rate **exceeds** AA's, 0.13% against 0.11% and 0.34% against 0.28%. That inversion is a small-sample artefact of thin AAA pools, and it is why those two figures are used only as loose upper bounds above. They are not evidence that the one-year rate is positive, for the reason given at the top of this section: a cumulative cohort rate counts obligors that defaulted from a lower grade, so it is compatible with a one-year AAA to D probability of exactly zero. Positivity rests on Cromwell's rule and on the estimator's range, not on this table.

**What the correction cost.** Nothing measurable, which is the right outcome for a fix to the two grades that contribute least to a cohort default rate. On the pinned three-instance set the reference moved 0.3581 to 0.3596, 0.3840 to 0.3688 and 0.4998 to 0.4999, and the degenerate stayed at exactly 1.000 since identity matrices cannot be floored. Over the twenty-four instance bracket the reference went from 0.287 to 0.292 mean, 0.256 to 0.276 median, 0.662 to 0.632 max, with 0 of 24 losses to the degenerate either way and separation 3.5x to 3.4x. The task did not get easier or harder; the hidden truth got correct.

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

The generator was guilty of it. The fourth root of the published annual average inherited four exact zeros, one of them AAA to default, because the published AAA one-year rate is 0.00% and a root of zero is still zero. The oracle would have failed the check the task poses. Every live cell is now floored at 1e-9, and the AAA default probability alone is replaced by the estimate in `top_of_scale_annual`, held fixed while the rest of its row rescales. No capital floor is applied, for the reasons given under Default Risk at the Top of the Scale.

**How it affects the score: it does not.** Holding the generator fixed and degrading only the reference's own matrices:

| Reference variant | Score | Exact zero cells | Ordering inversions |
| --- | ---: | ---: | ---: |
| replaces zeros and imposes ordering | 0.2920 | 0.1 | 0.0 |
| leaves the fourth root's zeros | 0.2919 | 42.8 | 2.2 |
| replaces zeros, leaves ordering to noise | 0.2919 | 0.1 | 2.2 |

Forty-three exact zeros and two and a bit ordering inversions per submission cost a third of a basis point of score, against the reference's own error of 0.292. The defect is orthogonal to accuracy rather than merely small. The inversion count is across the whole nine-quarter submission, so it is roughly a quarter of a violation per matrix.

**Every one of those inversions is AAA against AA, and removing the capital floor did not change the count.** That is worth stating because the opposite is easy to assume. While the floor was in place it pinned AAA and AA to the identical value, and identical values do not invert, so the floor did not create inversions; it created ties, and the tie was the defect, since the truth then asserted that the two best grades carried equal risk. With the floor gone the two differ by a factor of two in the base matrix, and AAA's rooted value still lands above AA's on six of twenty-four instances because AAA holds too few obligors to pin down. So the imposed ordering is doing what it was always for, correcting a thin-count artefact at the top of the scale, and it was never a workaround for the floor.

That rules out two treatments and leaves one. A weight would be fiat, because there is no accuracy cost to calibrate it against, and putting it in the number recreates the materiality argument inside the metric instead of avoiding it. A gate would disqualify a model whose accuracy is unaffected, which is not what a review function does: it assesses materiality, finds it small, issues a model limitation and approves. All models are wrong and some are useful, and here there are far larger error sources than a probability that is almost rather than exactly zero.

So admissibility breaks ties. But the defects are not all of one kind, and the measurement separates them into three tiers rather than one flag.

**Rows must sum to one. This is the hard one.** A matrix whose rows do not is not a collection of probability distributions, so it cannot be the model that produced the projection, and the breach is consequential rather than cosmetic. Scaling every row to 1.2 drives the gap between the submitted distribution and what the submitted matrices actually propagate to from 0.0000 to 2.5163, because mass non-conservation compounds over nine quarters. `matrix_row_sum_error` and `matrix_rows_off_one` record it, and a failure there is incomplete documentation rather than an accuracy penalty: the agent was asked to record its model and did not.

**Negative cells sit in the middle.** They also mean the object is not a distribution, but clipping them to zero is a defensible remedy that Kreinin and Sidelnikova use, and a single small negative is numerically near-harmless: the same gap moves only to 0.0001, because mass is still conserved. `matrix_negative_cells` and `matrix_most_negative` flag it rather than failing it.

**Exact zeros and a non-monotone default ordering are soft.** They leave a perfectly valid distribution that is imprudent or odd, and they cost nothing measurable in accuracy. Tie-breaker only.

Where two cells sit within the resolution this suite claims, a factor of a few, prefer the one with the cleaner tiers. `tests/test_migration_task.py` pins both the immateriality measurement and the tier separation, so a later change that makes admissibility material, or that collapses the tiers, fails the test rather than quietly surviving.

**A `from_rating` of D used to void the whole matrix file, and that cost a real submission ten of its sixteen checks.** Both matrix parsers rejected any starting rating outside the seven live grades, which is right for a typo and wrong for the absorbing row. ling-3.0-flash wrote eight rows per matrix instead of seven, `D` with `to_D` of one, and read as having submitted no matrices at all: `matrices_readable`, `matrix_cells_finite`, `matrix_cells_are_probabilities` and `matrix_rows_sum_to_one` all fired, and six more checks that depend on a parsed matrix went with them. Ten findings against a matrix file that was clean. Writing the absorbing row is the more complete answer, the prompt's column list includes `to_D` and nothing in it says to leave the row out. The row is now skipped rather than rejected, and D stays the identity row the parser imposes, because the prompt states default is absorbing and terminal, so that row is not a degree of freedom. An unknown label is still a hard rejection. The corrected checks were recomputed from the archived submission on the `Score`, with no second API call, which is the first time keeping the submitted files has paid for itself.

**There was a single boolean for this, `matrix_admissible`, and it has been removed along with `matrix_provided`, `matrix_rows_valid` and `matrix_nonnegative`.** The first three duplicate binary checks that ask the same questions of the raw blocks rather than of the repaired parse, which makes the checks the stricter reading of each: `matrices_readable`, `matrix_rows_sum_to_one` and `matrix_cells_are_probabilities`. The conjunction was worse than redundant. It required all three tiers clean, including "no exact zero anywhere in any matrix", which almost every submission trips, so on the first live run it read 0.0 on eight of nine submissions, two of which failed none of the sixteen checks. A key that convicts a clean submission is worse than no key. Every component survives as a count or a magnitude, which is the form a reviewer can act on, and the score is unchanged because none of these ever entered it.

One limit worth stating. A clean submitted matrix cannot distinguish an agent that reasoned about admissibility from one that clipped silently and got lucky. Both free models in the smoke runs found the negative entries and still called them numerical issues. That reasoning lives in the transcript, and grading it would need a judge, which this suite does not use.

## A Scenario Is Capped at Ten Times the Portfolio's Own History

A book that defaults at 1% a year does not lose a tenth of itself in a realistic supervisory scenario, however severe the draw. Left alone the generator produced scenarios that did, and they are worth describing before the fix, because they are not simply "hard instances".

**The worst draw was not a stress test, it was the portfolio ceasing to exist.** On the documented convention, seed 21 put 98.9% of the book in default by quarter nine under severe, 71.2% under adverse, and 12.9% under its own *baseline*, against an observed history of 1.12% a year. That is also close to free marks: when the truth is nearly a point mass on `D`, predicting total ruin scores well and the twelve components stop discriminating. Before the cap, the severe path reached 31.7 times the portfolio's own historical loss rate over the horizon on the worst of 120 instances.

**The bound is stated against the history, not against the drawn baseline scenario.** The obvious rule, "no scenario more than ten times worse than baseline", does not catch that instance: severe is only 7.7x *its* baseline, because the baseline is itself a draw and is itself elevated. So the anchor is the observed annual default rate in `data/transitions.csv`, scaled to the nine-quarter horizon, and no scenario's cumulative default share may exceed ten times it. That is the anchor a reviewer would use, and it is public data the agent can compute for itself.

`SEVERITY_CAP = 10.0`. What it costs, over three scans of sixty instances:

| | served, base 1 | served, base 7 | `generate(seed=k)` |
| --- | ---: | ---: | ---: |
| instances damped | 8 of 60 | 5 of 60 | 10 of 60 |
| median damping factor, where it binds | 0.75 | 0.95 | 0.76 |
| severe, median multiple of the historical rate | 3.8x | 3.9x | 3.9x |
| severe, 90th percentile | 10.0x | 7.4x | 10.0x |
| baseline, worst instance | 3.1x | 8.0x | 7.2x |

So it binds on about one instance in eight and only at the top of the distribution. A typical severe scenario still quadruples the portfolio's historical loss rate, which is a realistic supervisory severity, and the baseline never reaches the cap on its own, so the damping is a statement about stress calibration rather than about the instance's underlying risk.

**The damping is applied to the macro paths, not to the factor.** It multiplies the hump weights, and the weights are what the overlay scales the stress-window deviation by, so every series is pulled proportionally back toward its last historical value with its shape and turn quarter intact. Scaling the factor directly would have been far simpler and would have published a `scenario.csv` that no longer implies the factor path the answer key uses, which is a leak in the agent's disfavour: it could fit the macro-to-factor link correctly and still miss. One damping factor is used for all three scenarios, so the severity ordering between them is preserved by construction rather than checked afterwards.

**One instance in sixty cannot be damped at all, and is redrawn.** Damping to zero does not mean "no stress", it means holding the last historical quarter flat across the horizon, and on a history that *ends* in a crisis that quarter is the crisis. One such draw carried a final observed year at 17.5% default with the historical factor at +5.5 standard deviations, and every scenario landed on 98% regardless of the overlay. Flattening it further would also have collapsed the three scenarios onto each other, which the severity checks read, correctly, as a defect. Those instances are rejected and redrawn from a derived seed, deterministically, up to twenty attempts.

**The cap made the check margins wider, not narrower.** The tightest severity gap over 192 comparisons went from 0.0026 to 0.0104 for the oracle and from 0.0016 to 0.0113 for the reference, because the instance that set the old minimum was one of the ones the cap damps. Every figure in this document measured from `data/transitions.csv` moved slightly, since about one instance in sixty is now a different draw, and the figures quoted here are the post-cap ones.

## Sixteen Checks a Reviewer Would Actually Make

The numeric diagnostics below answer "how far from the oracle", and nothing about a continuous distance tells a reviewer whether to send the model back. No reviewer reads "severe stress response 0.41x" and reaches a verdict. So the primary diagnostic layer is sixteen binary checks, each reported as `fail_<name>` equal to one when it fails, plus `checks_failed` and `checks_total`. Averaged over samples, each key reads as the share of submissions carrying that finding, and the count is the number of findings a reviewer would write up.

Three rules govern what is allowed in.

**It must be defensible without the answer key.** A statistic measured against the oracle cannot be a check, because its cut has to be calibrated against the spread of a competent estimate, and that spread is wide: the shipped reference's far-corner ratio runs 0.301 to 5.107 over the twenty-four instances this task draws at base seed 1, dipping below 0.5 on four of them, so no threshold on it separates a thinned submission from an honest one. The same defect stated as "the model gives a three-notch downgrade zero probability" needs neither the oracle nor a threshold.

**It must be computable on every submission.** A ratio whose denominator can vanish, or a rank correlation whose comparable pairs can all be ties, returns NaN, and NaN is neither a pass nor a fail. Where a measured diagnostic produced one, the check is restated as an ordering, which always exists. A NaN *in the submission* is the opposite case: it is a hard, counted failure, not a missing measurement.

**An absent or unreadable artefact fails every check that reads it.** A model nobody can inspect has demonstrated none of these properties, and excusing it would let a missing file outrank a bad answer. The count stays monotone in how much is wrong.

### The Sixteen

**Integrity, seven.** `matrices_readable` and `predictions_readable` (both files parse, and all three scenarios are present); `matrix_cells_finite` and `prediction_shares_finite`; `matrix_cells_are_probabilities` (every cell in [0, 1]); `matrix_rows_sum_to_one` and `prediction_shares_sum_to_one`, to 1e-4. Nothing is repaired before these run, which is the point: the parser used by the score coerces and fills, so a NaN there becomes a number, while these read the raw blocks and count it.

**Shape, three.** `pd_rises_as_rating_falls`: a lower-rated obligor's default probability is not below a higher-rated one's. `stay_is_the_most_likely_outcome`: over one quarter a grade is likelier to persist than to land in any one other live grade. `multinotch_downgrade_possible`: the three-or-worse band is not identically zero, because zero is not an estimate, it is an assertion that the move cannot happen.

`stay_is_the_most_likely_outcome` reads the three scenario blocks and not the fitted history, and that exclusion is measured rather than defensive. One of the 960 true historical quarters across twelve instances sits at a factor of +5.92 standard deviations, where the oracle's own AAA row puts 0.2955 on staying against 0.4532 on a one-notch fall, three violating cells. The answer key tripping a check is a bug in the check, and the decisive argument is that the shipped reference never trips it, because its ridge-shrunk factor never reaches that far: checking the history would convict exactly those submissions whose historical fit is *more* faithful than the reference's. The property is a statement about a quarterly migration matrix in a plausible macro state, and a six-sigma quarter is not one.

**Macro response, four.** `downgrades_rise_with_severity`: portfolio-weighted downgrade mass, summed over the nine quarters, rises strictly with severity. `pd_rises_with_severity`: the projected nine-quarter cumulative default share rises strictly with severity. `implied_pd_rises_with_severity`: the same question asked of the matrices, by propagating the published cohort mix through them. `pd_rises_with_horizon`: in the absorbing cohort the default share rises strictly from quarter four to quarter nine.

The three severity checks compare *every adjacent pair*, severe against adverse and adverse against baseline, and fail if either comparison fails. Comparing only the mildest with the worst would pass a submission whose middle scenario is out of order, and an adverse projection no worse than baseline is the same defect as a severe one no worse than adverse. All three read the nine-quarter total or the terminal checkpoint rather than every checkpoint, for a reason measured below: the severe scenario's trough makes the early quarters genuinely non-monotone in severity in the answer key itself.

The projection and the matrices are two separate claims, which is why the severity ordering is asked of both. A submission can file a perfectly ordered projection computed by some other route while the matrices it documents imply the opposite, and nothing else here catches that: `matrix_submission_gap` is reported rather than checked, and it is a distance rather than an ordering.

**Historical fit, two.** `historical_fit_identical_across_scenarios`, described under One History, Three Scenarios. `fitted_downgrades_rise_in_bad_years`: the migration body the model implies for its own historical quarters moves with the cycle it was fitted to, described below.

### The Fitted Body Has to Move With the Cycle

`fitted_downgrades_rise_in_bad_years` is the one check that reads the fitted history rather than the projection. Take the portfolio-weighted one-notch-or-worse downgrade mass of each fitted historical year, rank the twenty years by the observed annual default rate in `data/transitions.csv`, and require the mean over the five worst years to exceed the mean over the five best. Nothing in it touches the answer key: the ranking variable is published data, and the quantity ranked is the submission's own output.

It exists because every other statement about the history is made through the default column. A model can reproduce twenty years of observed default rates to five parts in ten thousand while carrying a migration body that never moves, and that is not a hypothetical: this task has seen that failure twice. The question the check asks is the one a reviewer asks of any such model, which is whether the thing it claims to have estimated responds to the cycle it was estimated on.

Three details in the construction earn their place, each settled by measurement rather than by argument.

**It cannot be a correlation.** A time-homogeneous body has zero variance across quarters, so a correlation against the observed series is NaN exactly on the submission most in need of a verdict. That is the same failure mode that disqualified `matrix_one_model_discordance`, which returned NaN on a submission whose three scenarios were identical, and restating the question as an ordering between two group means removes it: both means always exist.

**The split is by rank, not by quantile value.** `obs >= quantile(.75)` and `obs <= quantile(.25)` can select overlapping sets on a history with ties, and an overlap drives a correct model's gap toward zero and fails it. Five highest against five lowest is disjoint by construction, whatever the history looks like.

**It is top quartile against bottom quartile, not top against the rest.** Both forms work, and the narrower one is better on every axis measured. On the shipped reference's own submission the smallest margin over twenty-four served instances is 1.12e-02 for quartile-against-quartile and 7.61e-03 for quartile-against-rest; a sign-flipped body, which is the most adversarial near-miss, reads -1.94e-02 rather than -1.11e-02. The intuition that the wider comparison must be more noise-robust because it averages more years is wrong here: the middle two quartiles are the years whose ranking is least determined by the signal and most by sampling noise, and including them in the comparison group dilutes the contrast more than it stabilises the mean. Resampling each year's default count binomially and re-deriving the split, eight instances by two thousand draws each, the reference's gap never fell below 9.48e-03 in 16,000 tries against 6.22e-03 for the wider form.

**Every year is weighted by one fixed starting mix.** Weighting each year by the portfolio that year actually began with turns the statistic into a statement about composition drift as well as about the matrices, and that is enough to let a constant body cross the split on drift alone: measured, it passes on 4 of 24 instances. Against one fixed mix a constant body reads exactly zero, to 3.5e-18, and fails on all 24.

**The margins, over twenty-four served instances, against an absolute tie tolerance of 1e-9.** The oracle clears by 1.55e-02 and a direct per-year fit to the counts by 2.00e-02. The shipped reference clears by 1.12e-02, and it is the demanding case, because its factor is built from macro data and so never sees the sampling noise in the default counts that helped choose the split. A model retaining only five percent of the reference's macro response, scaled about its own mean, still clears by 4.67e-04. The check is therefore not a test of whether the response is well calibrated, which is what the numeric diagnostics are for; it is a test of whether there is one at all.

### It Separates, and Nothing Is Marginal

Twelve instances, the ones the task serves at base seed 1, one line per known submission shape, count of instances on which each check fails. The documented `generate(seed=k)` convention produces the identical table:

| Submission | `checks_failed` of 192 | Which checks |
| --- | ---: | --- |
| oracle (true model) | 0 | none |
| one-factor reference | 0 | none |
| oracle with the far band thinned to zero | 12 | `multinotch_downgrade_possible` 12 |
| oracle with the migration body frozen | 24 | `downgrades_rise_with_severity`, `fitted_downgrades_rise_in_bad_years`, 12 each |
| oracle refitted per scenario | 12 | `historical_fit_identical_across_scenarios` 12 |
| degenerate (no migration) | 72 | `multinotch_downgrade_possible`, `downgrades_rise_with_severity`, `pd_rises_with_severity`, `implied_pd_rises_with_severity`, `pd_rises_with_horizon`, `fitted_downgrades_rise_in_bad_years`, 12 each |
| nothing submitted | 192 | all sixteen, 12 each |

Every cell is 0 or 12. No check is near its boundary on any instance, which is what makes the binary form honest rather than a threshold in disguise: a defect either is or is not present, on all twelve draws.

**The oracle and the reference fail nothing, and that is a requirement rather than a result.** A check the true generating model trips is a bug in the check. Finding one was not hypothetical. The unrestricted form of `stay_is_the_most_likely_outcome`, which included default among the destinations, failed the oracle on three of twelve instances: nine violations on one of them, reaching stay 0.283 against default 0.717, because a CCC/C obligor in a severe quarter really is likelier to default than to stay CCC/C. The destination set now stops at the live grades and the default column is left to `pd_rises_as_rating_falls`. Two measured numeric diagnostics were removed under the same rule, recorded under The One-Model Instruction and Diagnostics Reported.

**A second bug, found the same way, and it had shipped.** The severity checks first compared every checkpoint. That holds on `generate(seed=k)` for k from one to twelve, which is the convention this document uses, and it fails the answer key on the draw an agent is actually served. The severe scenario has a trough by design, so its early quarters can be milder than the adverse path's while its late quarters are far worse, and the ordering genuinely inverts at quarter four. Over three scans of forty eight instances the quarter-four comparison fails on 14 of 288 pairs, by as much as 0.0100, while the quarter-nine comparison never fails once in the same 288. At base seed 1, instance 4 puts severe at 0.92% against adverse's 1.04% at quarter four and 3.63% against 2.57% at quarter nine. The severity checks now read the terminal checkpoint only, which is the nine-quarter cumulative default rate, and the test that sweeps the oracle and the reference now sweeps both seed conventions. Two conventions that disagree have now hidden a defect twice in this document, which is reason enough to name the convention beside every figure.

**`near_downgrade_exceeds_far` was proposed and dropped.** It asked that the adjacent-notch cell carry at least as much mass as the whole three-or-worse band behind it, and it compares unlike quantities: one cell against the sum of up to four. It is also wrong on the merits at the bottom of the scale. An agency that is confident an obligor is about to default has nowhere worse to put it than the lowest non-default grade, so mass piles into a far cell for a reason that is about the scale having an end rather than about the migration law, and a model that reproduces that behaviour would be convicted of it.

### The Strict Inequalities Are Affordable, and the Data Supports Them

Four checks are strict rather than weak. Weak inequalities would pass a submission predicting the same loss under every scenario, and would pass the degenerate, whose cohort default share is exactly zero everywhere and therefore satisfies every weak ordering there is. For `downgrades_rise_with_severity`, equality *is* the frozen body, which is the defect being looked for. Each has a measured margin, against a relative tie tolerance of 1e-6:

| Check | Comparisons | Oracle's smallest gap | Reference's | Failures |
| --- | ---: | ---: | ---: | ---: |
| `pd_rises_with_severity` | 192 | 0.0104 | 0.0113 | 0 |
| `implied_pd_rises_with_severity` | 192 | 0.0104 | 0.0113 | 0 |
| `pd_rises_with_horizon` | 288 | 0.0052 | 0.0064 | 0 |
| `downgrades_rise_with_severity` | 144 | 0.0444 | n/a | 0 |

Four scans for the severity pair (twelve and twenty-four instances on the documented convention, twenty-four each on two served draws), two for the horizon, three for the downgrade mass. The projected and implied gaps are identical on the oracle and on the reference, because both compute their projection from their own matrices, which is the point: the two checks only separate when a submission's two artefacts disagree.

**None of this asks for anything the agent cannot see in its own data.** Measured on the twelve instances the task serves at base seed 1, in `data/transitions.csv`, annual downgrade frequency correlates +0.918 to +0.988 with the annual default rate over the twenty published years, and downgrades are 2.6 to 5.7 times more frequent in the stressed quarter of years, on all twelve and from every starting grade with room to fall: 3.6x from AAA, 3.7x from AA, 4.1x from A, 4.5x from BBB, 3.4x from BB, 2.9x from B, as means over the twelve. Upgrades move the other way, 0.15x to 0.66x. The three-or-worse band is the most macro-sensitive region of the matrix, 13.6x between the stressed and benign quarters of years (range 3.6 to 53.5) against 3.3x for the adjacent notch, so a model that zeroes it is discarding its most responsive evidence. A submission that trips a response check contradicts its own history.

**The checks do not enter `score`.** The score stayed bit-identical through the whole of this work, so archived cells remain comparable.

## The Far Downgrade Corner and the Macro Response

Two diagnostics measure the shape of the submitted matrices rather than their admissibility. These are oracle-relative magnitudes, so they are measurements and not verdicts: the verdict form of the same two defects is `multinotch_downgrade_possible` and `downgrades_rise_with_severity` in the check layer above, which is what a reviewer is handed. Both groups here are reported and neither is scored, for the same reason as the admissibility tiers: they are orthogonal to accuracy as the score defines it, and the measurement below is what establishes that.

The question they answer is whether the matrix moves for the right reason. Getting the quarterly scale right is a time-scaling problem and the literature hands an agent the tools for it. Getting the matrix to respond to a macro path is a conditioning problem, and the two are separable in a way that the score cannot see.

### What Agent Submissions Actually Looked Like

The scorer kept only summary statistics of `matrices.csv`, so the submitted matrices from the smoke runs are not recoverable from the eval logs. One near-complete set was reconstructed from what an agent printed into its own transcript, nemotron-3-ultra-550b on a severe instance, and it shows the failure in its strongest form. The share of its downgrade mass travelling two grades or more:

| Quarter | Factor | AAA submitted | AAA true | BBB submitted | BBB true |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.17 | 0.0602 | 0.0267 | 0.1569 | 0.0875 |
| 3 | 1.82 | 0.0602 | 0.0643 | 0.1569 | 0.1471 |
| 6 | 4.64 | 0.0602 | 0.2798 | 0.1569 | 0.3467 |
| 9 | 2.55 | 0.0602 | 0.0945 | 0.1569 | 0.1843 |

Identical to four decimal places in every quarter. Its whole live block is frozen: the maximum relative range across the nine quarters is 0.0001 for AAA, 0.0055 for A and 0.095 for BBB, against 3.8 to 7.9 for the truth, while its default column moves by a relative range of 2.4 to 5.4. It built one unconditional migration matrix, attached a scenario-sensitive default probability to it, and left the body alone. At the trough the truth sends 11.1% of AAA obligors down two grades or more and the submission sends 0.57%, a factor of nineteen, while in the first quarter the same submission overstates the tail. That asymmetry is the signature: not a thinned tail, but a matrix that does not condition at all.

It is one submission, so it is evidence of existence rather than frequency. Two further fragments agree on the pattern in one case and disagree in the other, where the body does move and the far cells run seven to thirteen times above the oracle. The point of adding the diagnostics is that the next run will not need reconstructing from transcripts.

### What the Diagnostics Are

Rows are weighted by the published cohort mix throughout, because the question is how much of this portfolio the matrix sends three grades down, not how distorted the AAA row is on its own. AAA holds 1% of the book and BBB 40%. Default is excluded from every statistic in both groups: it is an absorbing state at the bottom of the scale rather than a grade three notches down, it is already scored directly in two of the twelve components, and including it would let a correct default column hide a collapsed migration body.

**`matrix_down3_ratio`** is the submitted three-notch-or-worse downgrade mass over the oracle's, pooled over every scenario and quarter. Summing the two totals rather than averaging their ratios means the stressed quarters dominate the denominator, so no stress window has to be chosen. **`matrix_down1_ratio`** is the same ratio on the adjacent-grade band over the same four rows and serves as the control, since a model that is uniformly too mild reads low on both. **`matrix_down3_shape`** divides the first by the second and is therefore blind to a uniform error of level.

**`matrix_downgrade_concordance`** is the fraction of matrix pairs, ordered by the true factor, whose submitted downgrade mass moves the same way as the factor. A near-tie counts as discordant, which is deliberate: a frozen body is the failure being looked for, so it has to read zero rather than drop out for want of comparable pairs. **`matrix_downgrade_slope`** separates a flat body from a perverse one, since both read zero on concordance, and is reported beside the oracle's own slope for scale.

The oracle is rebuilt in the scorer from `quarterly_base`, the factor path and the drawn correlation, which is why `rho` now travels in `truth`. It never reaches a public file.

### The Far Ratio Is a Measurement, Not a Proxy

Thinning the oracle's far corner to a fixed fraction of itself and folding the remainder into the two-notch cell, so that rows still close and the default column is untouched:

| Far mass retained | `down3_ratio` | `down1_ratio` | Composite score |
| ---: | ---: | ---: | ---: |
| 1.00 | 1.000 | 1.000 | 0.000 to 0.003 |
| 0.75 | 0.750 | 1.000 | 0.003 to 0.005 |
| 0.50 | 0.500 | 1.000 | 0.005 to 0.010 |
| 0.25 | 0.250 | 1.000 | 0.008 to 0.015 |
| 0.10 | 0.100 | 1.000 | 0.010 to 0.018 |
| 0.00 | 0.000 | 1.000 | 0.011 to 0.020 |

The ratio reads the retained fraction back exactly, identically on all twelve instances, and the control does not move. The score column is the argument for reporting this separately: abolishing every three-notch downgrade, with the factor path and the default column exactly right, moves the composite by about fifteen thousandths against a reference composite of 0.285. A submission can collapse the entire far corner and still score two orders of magnitude better than the anchor.

### The Two Groups Are Each Blind Where the Other Sees

Over twelve instances, on 351 comparable pairs each:

| Submission | `down1_ratio` | `down3_ratio` | `down3_shape` | Concordance | Slope |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.72 to 1.12 |
| no three-notch moves | 1.000 | 0.000 | 0.000 | 1.000 | 0.72 to 1.12 |
| no multi-notch moves at all | 1.08 to 1.19 | 0.000 | 0.000 | 1.000 | 0.72 to 1.12 |
| body frozen, default column only | 0.11 to 1.06 | 0.04 to 1.27 | 0.39 to 1.19 | 0.000 | -0.022 to -0.0015 |
| shipped reference | 0.60 to 1.46 | 0.55 to 4.09 | 0.74 to 3.42 | 0.85 to 0.99 | 0.66 to 1.25 |

Folding multi-notch mass into the adjacent grade conserves total downgrade mass, so it reads concordance 1.000 and the oracle's own slope while the far ratio reads zero. A frozen body leaves the far corner's shape roughly intact, overlapping the reference's honest range, while concordance reads exactly zero. Neither group alone catches both failures, which is why there are two.

The frozen body's faintly negative slope is not noise. Renormalising a row to absorb a rising default probability shrinks every migration cell in it, so a model that conditions only its default column makes downgrades very slightly less likely in stress, which is the wrong sign.

### The Reference Overstates the Far Corner, and That Sets the Threshold

The anchor reads 0.55 to 4.09 on the far ratio, median 1.31, and 0.74 to 3.42 on the shape, median 1.57. It is biased upward because it estimates its base matrix from twenty years that contain stressed ones, so it inherits a far corner fattened by the cycle. That scatter, not the statistic, is what bounds the usable sensitivity: a reading below about 0.5 is a finding and a reading above one is not, the same one-sided convention the stress diagnostics use. A model that thins its far corner by a quarter reads 0.75 and is indistinguishable from an honest estimate.

Concordance is tighter. The reference reads 0.846 to 0.994 because its estimated factor orders the quarters slightly differently from the true one, and it never approaches zero. So concordance separates no response from an imperfect response by a clear margin, and makes no claim to grade the quality of a response that exists.

### Limits Worth Stating

The scale is seven rating categories, not twenty notches, so a two-grade move is already A to BB and the far corner holds only ten cells: four from AAA, three from AA, two from A and one from BBB. Nothing here transfers directly to a notch-level scale.

The evidence available to an agent for those ten cells is thin but not absent. Pooled over the twenty published years on the first instance, the three-notch-or-worse counts are 7 from AAA, 32 from AA, 120 from A and 107 from BBB, with one empty cell in the AAA row, and the observed shares run 1.5 to 2.4 times the unconditional annual matrix because the history contains stressed years. So an agent estimating cell by cell gets a noisy and upward-biased far corner rather than a set of sampling zeros. Thin counts are a reason the reference scatters; they are not the mechanism behind a frozen body.

Every figure in this section is measured over `generate(seed=k)` for k from one to twelve, and predates both the severity cap and the move of the tests to the served draw, so it is a record of what was measured rather than a current reading. The task itself draws its instance seeds differently, from `SeedSequence(base).generate_state(n_instances)`, and that set is harsher on the anchor: over its first twenty-four instances the reference's far ratio runs 0.301 to 5.107 with median 1.039, and falls below 0.5 on four of them. So the one-sided reading above is calibrated on a seed set that is not the one an agent is served, and on the served set it would record a finding against the reference itself about one time in six. The diagnostic is reported rather than scored, so this costs nothing beyond knowing it. It was not promoted to a gate, and this scatter is why: `multinotch_downgrade_possible` asks instead whether the far band is identically zero, which needs no calibration and reads 0 on the reference across both seed conventions.

The far ratio needs the oracle, so it is not a statistic an agent could compute for itself, and it is not a candidate for the score for that reason among others. It also needs the submission written to enough precision. Rounding the oracle's own matrices and re-measuring, the far ratio reads 1.0000 at eight decimals, 0.9999 at six, 1.0035 at four and 0.6393 at three. The instructions now ask for at least six decimal places, because at three the statistic would convict a correct submission of a 36% thinning that is entirely formatting.

## One History, Three Scenarios

An instance carries one set of annual counts, one macro history, one holdout cohort and three nine-quarter paths over the same future quarters, named `baseline`, `adverse` and `severe` in a `scenario` column of `data/scenario.csv`. The prompt asks for one model estimated on the history and three projections through it. `predictions.csv` and `matrices.csv` carry the same column, at forty-eight and three hundred and twenty-nine rows.

`matrices.csv` also carries the fitted history. Under the reserved scenario name `history` the model writes the quarterly matrix it implies for each of the twenty historical years, labelled at the last quarter of its year so that quarters -76, -72 and so on through 0 carry one matrix each, once rather than once per scenario, since there is one history. That block exists because the alternative is to take the historical fit on trust: `backtest.csv` reports the default column alone, which is one column of a seven by eight matrix, and the two defects this task has actually caught in its own reference both lived in the body rather than the column. The block is a diagnostic rather than part of the answer, so the parser used by `score` drops it before anything oracle-relative is computed, and the score is bit-identical with and without it.

**It is one matrix per year because the first version asked for one per quarter, and that broke a live run.** Eighty quarterly matrices took `matrices.csv` to 141 KB, and the check that reads the block averaged each year's four before comparing, so three rows in four never reached any comparison. The cost was not theoretical. Agents write the file by printing it into their own message rather than only to disk, and on the first live run under the quarterly form two of three ling-3.0-flash samples died at the API with `input (262244 tokens) is longer than the model's context length (262144)`, one of them on a single 99,057 character assistant message. At one matrix per year the file is 62 KB and 329 rows. Nothing is lost by the change: the history carries one annual observation per year, so a within-year factor path is not identified from it, and the reference wrote the same matrix four times over for every quarter of a year, so averaging the four returned that same matrix's mass. Every figure quoted above is measured on the shipped annual form.

This is a correction. An earlier version drew one scenario per instance and rotated the three across instances, which was wrong in two ways.

**It made severity inseparable from everything else.** Under rotation the instance index fixed both the scenario label and the drawn response law, so no difference between a baseline run and a severe one could be attributed to severity: the scenario, the seed, the latent drivers, the history and the agent session all moved together. The question "does a severe scenario change the functional form the agent reaches for" was unanswerable by construction, and a nine-run crossed design would have been the only way to ask it. Varying severity inside the instance answers it in one run.

**It made the failure that matters unobservable.** An agent that sees one scenario cannot re-estimate per scenario, so nothing in its submission could reveal whether it would have. Per-scenario refitting, retuning and scenario-specific overlays are standard audit findings in this space, and the old shape could not produce the evidence for one.

It also costs nothing in sample count and buys a gradient. Three projections from one fit are not three observations of modelling skill: they share the estimation, so their errors are strongly correlated and averaging them is noise reduction on one draw. What the breakdown shows is where a model fails. The severe path drives the systematic factor outside the range the model was estimated on, so a model that interpolates its own sample scores well on baseline and badly on severe. The reference does exactly that, 0.228 against 0.343, and under the old shape the aggregate hid it.

### It Required Closing a Leak in the CCAR Macro Generator

"One history" was not constructible on the shipped settings. The equity siblings `sp500` and `djia` are built by standardising NASDAQ returns, and that standardisation ran over the whole path, so the stress window's own volatility reached back into the historical values of two published columns. Holding the seed and changing only the scenario label moved 49 of 80 history rows. Under rotation this was inert, since an instance carried one scenario; with three scenarios sharing one history it is a contradiction, and the size of the jump at the join would have encoded severity.

`_simulate` now takes `sibling_ref`, and migration passes `pre_stress`. The default stays at the whole-path behaviour, because changing it moves two published columns on every archived CCAR instance for no benefit to that task. Standardising on a window that includes the future was a lookahead defect either way; it is fixed where it mattered and recorded where it did not.

### The One-Model Instruction Was Checked Weakly, and Is Now Checked Exactly

**`matrix_one_model_discordance` has been removed, and what replaced it is `historical_fit_identical_across_scenarios`.** The history does not depend on which future scenario is being run, so a model estimated once implies one fitted historical series and writes it three times, and a model refitted per scenario writes three different ones. `backtest.csv` now carries a `scenario` column for that reason, and the prompt no longer says there is one history so there is one backtest, which was handing over the answer. The comparison is an exact equality to the precision a CSV carries: no threshold, no denominator that can vanish, and nothing taken from the answer key. It catches a per-scenario difference of a hundredth of a percent and passes a floating point difference of 1e-7.

The rest of this section records what the removed statistic did and why it was not enough, because the blind spot it had is the reason the replacement exists.

`matrix_one_model_discordance` asked whether the submitted matrices could have come from a single one-factor model. Under any threshold-shift law the whole matrix is a monotone function of one scalar, so if one quarter is worse than another for the portfolio it is worse for every grade at once and the grades cannot cross. Ordering the submitted matrices by their portfolio-weighted default probability and checking each grade against that order is model-free and costs nothing.

Read as zero against non-zero rather than as a magnitude. The reference reads exactly 0.0 over 2,457 comparable pairs, so any violation is a finding, and the magnitudes are small: re-estimating the base matrix on the severe scenario alone reads 0.77%, an overlay applied to the speculative grades 0.81%, a flat one point add-on 0.12%.

**The blind spot is the likeliest case, and it is not fixable this way.** A model re-estimated per scenario that stays inside the same one-factor family, so that only the macro coefficients and hence the factor path differ, reads exactly 0.00%. Scaling the severe path's factor by 0.6 leaves every grade's ordering intact, because the family is comonotone whatever the factor does. So the statistic detected a change of form, not a change of fit, and a submission reading zero had not been shown to use one model. It was also NaN on a submission whose three scenarios were identical, because identical matrices leave no comparable pairs, which is precisely the submission most in need of a verdict. The historical-fit equality has neither weakness: a refit inside the one-factor family still has to produce a different historical fit, because it is a different fit.

### A Severe Draw Could Wipe Out the Book, and Now Cannot

**This is the open question that the severity cap closed.** The two paragraphs below record it as it stood; what was done about it is under A Scenario Is Capped at Ten Times the Portfolio's Own History.

The severity bands are disjoint, so baseline, adverse and severe come out ordered on every instance measured, and the factor is pushed further out of sample at each step. The tail is the problem. Over twenty-four seeds the severe cohort default share at quarter 9 has a median of 0.123 and a maximum of 0.989: seed 21 draws both weights near one and an asset correlation of 0.173, and its severe factor reaches 7.9 standard deviations, which no supervisory scenario resembles. One instance in twenty-four is affected at that extreme and one more exceeds 0.70.

Rotation hid the frequency rather than reducing it: a severe path was drawn on one instance in three, so a bad draw cost one instance in roughly seventy. Now every instance carries one, so a bad draw damages one column of three. The scoring still behaves, since the degenerate is normalised per scenario and reads 1.000 either way, but an instance whose severe truth is total wipeout is not measuring the annual-to-quarterly problem the task exists for. This was a generator calibration issue that predated the redesign and was deliberately left open here, because bounding the drawn severity changes the task's difficulty and that was a separate decision from the shape of the instance. It has since been taken: no scenario may exceed ten times the portfolio's own historical loss rate over the horizon.

## The Scenario Has a Trough, Which Cost Something

The horizon was initially monotone. Every macro series deteriorated for all nine quarters without turning, because the inherited CCAR overlay ramps level series linearly to a target and holds growth series at a constant stressed rate, and neither construction can reverse. In `severe` unemployment ran from -0.22 to +1.24 standard deviations in a straight line.

Published supervisory scenarios are not shaped like that. They deteriorate for a few quarters, turn, and recover partly; the stress phase typically lasts two to six quarters rather than the whole horizon. The horizon is now reshaped accordingly, in this generator rather than CCAR's so that task's archived measurements are untouched. A severity weight rises to its peak at a drawn quarter and decays linearly to a drawn residual, with the peak quarter and residual both scenario-dependent: two to three quarters and up to 30% residual for `baseline`, three to five and 20 to 45% for `adverse`, four to six and 35 to 60% for `severe`.

The systematic factor peaks one to two quarters after the macro path does, which is not a defect: credit deteriorates after the economy does.

Re-measured within the instance rather than across instances, over twenty-four seeds. The flow measure replaces defaults from the starting mix each quarter, so it is a fraction of a replenished book and can exceed one on an extreme draw.

| Scenario | 9-quarter portfolio default | Annualised | Cohort share at q9, median |
| --- | ---: | ---: | ---: |
| baseline | 4.41% (0.77 to 15.91) | 1.98% | 0.029 |
| adverse | 14.29% (2.89 to 99.67) | 6.62% | 0.066 |
| severe | 33.40% (4.09 to 247.48) | 16.53% | 0.123 |

The means are higher than the figures this table carried under rotation, because every instance now contributes to every row instead of one row, so the heavy upper tail is no longer diluted by which scenario an instance happened to draw. The medians are the number to read. Baseline annualises above the 0.99% the portfolio mix was calibrated for, which is the holdout cohort being deliberately riskier than the history.

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

Bracket at the shipped settings: reference 0.285 over twelve instances, 0.309 over the six the test uses, degenerate 1.000, separation 3.5x and 3.2x, against 4.8x at forty years unshrunk. Refusing the clip costs about 0.04 of that, which is the price of a reference that can answer the question the task asks.

**Every variant figure in this section was measured under the earlier shape, where each instance drew one scenario and the three rotated across instances.** The numbers are left as they were taken, and the conclusions carry over unchanged, because the estimation is identical in both shapes: `base`, the annual factor estimates and the ridge coefficients are computed from the history alone, and the redesign only changed how many paths are pushed through them afterwards. That the headline barely moved, 0.287 under rotation against 0.285 now, is the arithmetic of the same thing being averaged inside the instance instead of across instances. Re-measured on the new shape over eight seeds, shrinkage reads 0.297 mean with 0 of 8 losses to the degenerate against unshrunk 0.458 and 2 of 8, so the decision that section records stands.

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

**There is a second blind spot, and an agent found it before I did.** A backtest has no power at all against a model that interpolates its history and cannot extrapolate past it, because that model's only defect lies outside the period the backtest covers. Asked for a scenario whose peak volatility exceeded anything in its sample, `nemotron-3-ultra-550b` submitted a nearest-neighbour model and scored `fit_stress_mean_ratio` 1.0004 (a statistic since removed, see Diagnostics Reported), `fit_peak_ratio` 1.0003 and `fit_all_years_ratio` 1.0005, a backtest correct to five parts in ten thousand, while projecting 13.3% of the true stress response and 18.7% of the true quarter-nine default share. Its own reasoning named the defect and submitted anyway:

> The backtest shows nearly perfect fit because the KNN is essentially interpolating within the training data. [...] The scenario VIX goes up to 41, while historical max is 34. [...] So the model might underestimate the severity.

This is the same blindness that disqualified cross-validation for the ridge penalty, arriving by a different route: every year a backtest scores lies inside the historical range, and the scenario does not.

**No truth-free check for it was found.** The obvious candidate is internal consistency: a severely adverse scenario that projects no worse than the model's own worst fitted year is contradicting itself, and that comparison needs no answer key. Measured over twenty-four instances it does not separate. Pushing the historical average mix through the submitted first four quarterly matrices, the nearest-neighbour model reads below one on 21 of 24 against the reference's 17 of 24; restricting to the severe scenario and taking the worst rolling four-quarter window instead improves it to 6 of 8 against 3 of 8, with a spread of plus or minus 6.3 on the reference side. Directional and useless as a flag. It is recorded as a negative result rather than shipped.

What works is reading the two families together. `fit_*` and `stress_mean_ratio` are a pair, and their **disagreement** is the diagnosis: both low is a model with too little macro sensitivity, high in the backtest and low forward is a model that cannot leave its own sample. Neither statistic alone distinguishes those, and a reviewer handed only one of them would misattribute the failure.

**The flat-model case, for contrast, is caught cleanly.** `nemotron-3-super-120b` returned `fit_all_years_ratio` of 0.996, 1.015 and 0.861 across three instances with `fit_stress_mean_ratio`, since removed, of 0.527, 0.454 and 0.329 and `fit_peak_ratio` of 0.229, 0.148 and 0.214. Its unconditional level is right and its macro response is a third to a half of what it should be, which is exactly the target failure, and the all-years ratio is the control that rules out the alternative reading that its level is simply too low. Where its forward path was measurable it projected 4.3% of the true stress response.

"Did the band cover the peak" also must not be read as a pass/fail test. A perfectly calibrated pointwise 95% band excludes the largest of twenty draws with probability `1 - 0.975**20 = 40%`, and the correct model measures 25% here. The continuous ratio is the statistic; the binary version is noise.

### The Reference Fails Its Own Check

| | projected / observed, stressed years | factor swing retained | under-projects forward |
| --- | ---: | ---: | ---: |
| shrunk, shipped | **0.66** | 73% | 33% of instances |
| unshrunk | 1.02 | 97% | 4% of instances |

**The shrinkage that stops the reference blowing out on the projection also damps its macro response, so it under-fits the stressed years by about a third.** Ridge shrinks coefficient magnitude, and coefficient magnitude is the macro response. There is no reparameterisation out of it.

Two alternative explanations were ruled out rather than argued away. It is not the annual-constant-factor approximation: substituting the per-year maximum-likelihood factor, which keeps one constant factor per year but removes all regression and shrinkage error, takes the stressed-year ratio to 1.03 to 1.10 across twelve instances. So within-year variation is not what the backtest is detecting. And the observed peak is real signal rather than sampling noise in a 10,000-obligor portfolio: it sits within 1.1 to 3.5 binomial standard errors of that maximum-likelihood fit, so a model is not being penalised for declining to chase noise. What the statistic measures is the macro regression, both the part of the factor it cannot explain and the part the penalty damps. Variance matching, rescaling the fitted deviation so its spread matches the annual factor estimates, restores the sensitivity exactly and brings the blow-ups back worse than before:

| | Score | Max | Loses to degenerate | Projected / observed, stressed years |
| --- | ---: | ---: | ---: | ---: |
| unshrunk | 0.453 | 1.479 | 5 of 24 | 1.02 |
| shrunk, shipped | 0.287 | 0.662 | 0 of 24 | 0.66 |
| variance-matched | 0.705 | 2.002 | 5 of 24 | 1.01 |
| half-matched | 0.430 | 1.232 | 3 of 24 | 0.81 |

The damping and the stability are the same quantity. The score, being an accuracy measure, rewards the damping; a stress reviewer would reject it and issue a finding for insufficient macro sensitivity.

This is recorded rather than fixed, and it sharpens what the task measures. The anchor is competent and challengeable rather than a target: an agent that beats 0.285 while keeping its stress ratio near one is doing something the score alone cannot see.

### Diagnostics Reported

From `backtest.csv`, against the observed annual rates: `fit_peak_ratio` at the single worst year, `fit_all_years_ratio` for the contrast, and `fit_peak_prominence` for whether there is a peak at all. From `matrices.csv` and the truth: `stress_mean_ratio` and `stress_peak_ratio` on the nine-quarter loss path, `stress_peak_lag`, and `default_ratio_q4` and `default_ratio_q9`. From `matrices.csv` against the rebuilt oracle: `matrix_down3_ratio`, `matrix_down1_ratio` and `matrix_down3_shape` on the far downgrade corner, and `matrix_downgrade_concordance`, `matrix_downgrade_slope` and `matrix_downgrade_response` on whether the migration body answers the macro path, all described under The Far Downgrade Corner and the Macro Response. None of it enters `score`.

**`fit_stress_mean_ratio` was removed, and figures for it survive in the tables below as the record of what was measured.** It was the mean fitted rate over the worst quartile of observed years divided by the mean observed rate over the same years. The statistic was sound: built from the true factor path and the true correlation, a perfectly specified model reads 0.966 to 1.029 over twelve instances, mean 0.992, so selecting on the observed outcome biases it by about one percent. The shipped reference reads 0.480 to 0.781, mean 0.637, with no overlap. That is what disqualified it rather than what saved it. A diagnostic has to be one a competent estimate can clear, or it reports the bias-variance trade every estimator on twenty years of history must make as though it were a defect, and the one-sided reading below one needs a threshold nobody can defend. A denominator-free restatement does not help: counting the stressed years in which the fit falls below observed convicts the reference on six of twelve instances and the true model on none.

**`fit_peak_lag` shipped before it was checked, was patched, and has now been removed.** It read nine years on one instance and minus sixteen on another, because a damped fitted series is almost flat and the argmax of an almost flat series lands anywhere. Over the sensitivity sweep its absolute value ran 2.88, 3.00, 2.38, 2.12, 2.00, 0.75, non-monotone with a spread of plus or minus 10.8, which is no information. The patch was a companion measure of whether the series has a peak to time at all, `(fitted peak - fitted median) / (observed peak - observed median)`, with the lag withheld below 0.25:

| macro response | `fit_stress_mean_ratio` (removed) | `fit_peak_prominence` |
| ---: | ---: | ---: |
| 0.00 | 0.263 +- 0.088 | 0.092 +- 0.103 |
| 0.25 | 0.323 +- 0.103 | 0.123 +- 0.144 |
| 0.50 | 0.403 +- 0.119 | 0.194 +- 0.181 |
| 0.75 | 0.510 +- 0.138 | 0.319 +- 0.227 |
| 1.00 | 0.655 +- 0.173 | 0.514 +- 0.334 |
| 1.50 | 1.104 +- 0.392 | 1.171 +- 0.818 |

Prominence spans a factor of thirteen against the stress ratio's four, and at zero macro response it reads 0.09 rather than leaving a reviewer to infer flatness from a missing value. It is the statistic that survives. The gate worked as designed, and at the shipped fit exactly one of twenty-four instances fell below it, at 0.17, reporting a lag of sixteen years while the other twenty-three all sat above 0.39 and reported zero.

**The gate was never the problem. An argmax was.** Shrinkage compresses the worst few fitted years toward each other, so the argmax of a competent estimate on twenty years of history is near-arbitrary among them. Measured on the shipped reference over twenty-four served instances, a nonzero lag appears on eight, with values of -4, +1, +7, +8, +9 and +11 years.

| Instance | Observed | The reference's fit | Lag |
| ---: | --- | --- | ---: |
| 7 | y7 **3.31%**, y18 2.27% | y7 1.98%, y18 **2.02%** | +11 |
| 21 | y9 **2.96%**, y18 2.82% | y9 1.29%, y18 **2.20%** | +9 |
| 6 | y9 **6.78%**, y17 5.33% | y9 2.87%, y17 **3.56%** | +8 |

Instance 7 is the statistic indicting itself: the two years it compares differ by 0.04 percentage points in the fit, two percent of the fitted peak, and that coin flip is published as an eleven-year mistiming. Across the eight instances the fitted gap between the compared years runs 1.7%, 2.2%, 11.6%, 12.3%, 19.3%, 20.5%, 25.1% and 41.3% of the fitted peak. What the lag reports is shrinkage, and `fit_peak_ratio` reports that directly: on the same eight it runs 0.24 to 0.60.

The observed side is no better, and the prominence gate says nothing about it. Measuring each instance's observed peak margin over its runner-up as a fraction of the peak's height above the median, six of twenty-four instances fall below 0.25 and two below 0.10. The worst has its two worst years within 22% of each other and seventeen years apart, so a correct model reports either 0 or 17 depending on how it resolves a tie. The obvious repair, treating every observed year within 25% of the peak as a tied peak set and reporting the distance to the nearest member, was built and measured: it cuts the reference from eight instances to five and the mean absolute lag from 1.88 to 0.88, and the surviving five include the +11. A smaller version of the same artefact for a new free parameter is not worth having. The rule that removed `fit_stress_mean_ratio` applies unchanged: a diagnostic has to be one a competent estimate can clear.

**One bug worth recording, because it failed a whole run.** Inspect aggregates a keyed metric by pulling that key from every sample's score dictionary: an absent key raises, a NaN is skipped. Every diagnostic here is conditional on something, the matrices being submitted, the backtest having the right length, a denominator being positive, so a submission without `matrices.csv` left a matrix key out and ended a completed three-sample run with a TypeError after all the scoring work was done. The keys are now one module-level tuple, `REPORTED_KEYS`, and `score_value` fills anything inapplicable with NaN, which is the sentinel Inspect already understands. A test pins the contract over four submission shapes.

## What the Check Layer Found on Its First Live Run

Three instances at `-T seed=1`, three draws each, `minimax-m3.1-flash:free`, against both reference anchors on the same instances. Nine samples, all scored, no errors. This is the first measurement on the capped generator and the fifteen-check scorer.

| Row | per instance, mean +- 2 SD | worst | `checks_failed` |
| --- | --- | ---: | --- |
| one-factor reference | 0.365, 0.335, 0.368 (one draw each) | 0.368 | 0, 0, 0 |
| minimax-m3.1-flash | 0.453 +- 0.402, 0.162 +- 0.062, 0.232 +- 0.067 | 0.634 | 1,1,0 / 0,1,0 / 1,1,2 |
| degenerate | 1.000 | 1.000 | 5, 5, 5 |

On the worst-case convention this repository reports, the agent loses to the reference, 0.634 against 0.368, entirely on the first instance. On means it beats the reference on two of three. The first instance's own spread, 0.237 to 0.634 across three draws of a byte-identical instance, is wider than the gap between any two rows here, which is the same same-instance instability the rest of the suite reports.

### The Score Did Not See the Defect, and That Was the Point

**`pd_rises_as_rating_falls` fired on six of nine submissions.** Somewhere in the submitted matrices, a better-rated grade carried a higher default probability than a worse-rated one.

It is not rounding. Over the nine submissions there are 181 inverted cells, 166 of them larger than 1e-6, which is the printing floor the instructions impose, and 47 larger than 1e-4. The worst single case is unambiguous: on the severe path at quarter nine of one submission, AAA carries a default probability of 0.0647 against AA's 0.0211, so the model asserts the best grade on the scale is three times riskier than the second best.

**Every inversion is in the top two pairs**, AAA above AA on 87 cells and AA above A on 94, and none anywhere below. That is the same region described under Default Risk at the Top of the Scale: the top grades have almost no observed defaults, so an unconstrained estimate is noise there, and nothing in the fitting imposes the ordering. The failure is evenly spread across scenarios, 66 baseline, 60 adverse, 55 severe, so it is a property of the estimated model rather than of the stress overlay.

**The composite score is blind to it.** Over the nine samples the correlation between `score` and `checks_failed` is **-0.230**: the samples carrying findings score slightly *better* on average, 0.258 against 0.331 for the clean ones. The best score in the whole run, 0.634, is a clean sample and the second worst, 0.127, carries a finding. A reviewer reading only the column would have ranked these submissions in an order unrelated to whether their matrices are coherent.

That is the case for the count existing. Not that it correlates with quality, but that it does not.

### Other Findings

`multinotch_downgrade_possible` fired once, on the submission that also carried the most inversions. The other thirteen checks never fired on any of the nine, and the reference tripped nothing on any of its three, which is the separation the tests predict, now reproduced through the Inspect path on live instances rather than in process.

Four of nine samples were capped, three on the wall clock and one on messages, and all four still produced a scored submission. **Two quarter-labelling conventions appeared, and the prompt was at fault.** Six submissions numbered the horizon 81 to 89 and three numbered it 1 to 9, which is exactly what the published files invited: `data/macro_history.csv` ran 1 to 80 and `data/scenario.csv` ran 81 to 89, so "the nine quarters of each scenario" had two defensible readings. Both parsed, because the scorer orders the submitted quarters rather than assuming a numbering, and all nine submissions happened to key `predictions.csv` by 4 and 9, where the prompt is explicit. Had any of them carried its matrices convention across and written 84 and 89 there, it would have scored as though it submitted nothing. Every file now numbers quarters relative to the projection: the last historical quarter is 0, earlier history runs negative, the horizon is 1 through 9, and the prompt says so.

Run cost: thirteen and three quarter hours wall clock for the nine samples at two concurrent sandboxes, against about a minute for both reference anchors.

## What the Silent Check Measured

Three free models and both reference solvers over the same three instances, pinned with `-T seed=1` so the rows are comparable. This replaces an earlier run made before the scenario had a trough and before the history was shortened, and it is the first on the configuration the task now generates.

| Row | Mean score | Worst | Rows sum to one | Negative cells | Submission gap | Monotonicity violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| one-factor reference | 0.409 | 0.500 | 3 of 3 | 0 | 0.0000 | 0 |
| minimax-m3.1-flash (free) | 0.408 | 0.558 | 3 of 3 | 0 | 0.0000 | 0, 0, 10 |
| nemotron-3-super (free) | 0.527 | 0.873 | 3 of 3 | 0 | 0.0000 | 0, 0, 9 |
| nemotron-3-ultra (free) | 0.897 | 1.055 | 2 of 2 supplied | 0 | 0.0000 | 0, 16 |
| degenerate | 1.000 | 1.000 | n/a | n/a | n/a | 0 |

Ultra's adverse instance at 1.055 is worse than predicting that nothing happens, and it omitted `matrices.csv` entirely on the baseline instance.

**A column that should not have been there.** All nine of these runs saw a `data/macro_history.csv` carrying ten series rather than the nine the prompt promises. The history rows are adopted wholesale from the CCAR generator, which appends the default rate of ITS portfolio, while the scenario rows are built locally from the nine, so only the history had it. Measured against the counts in the same instance's `transitions.csv` it runs eight times too large, and its correlation with them is 0.601 on baseline, **0.033** on adverse and 0.776 on severe. It was noise on one instance and a shortcut on the next, and minimax leaned on it: 39 references on severe, where it correlated 0.776 and helped, and 12 on adverse, where it correlated 0.033. The column is now stripped where the CCAR bundle is adopted, and a test asserts both files ship the same nine headers. Every number in this section was measured with it present, so none of them is strictly comparable with anything measured after. The bias runs in the generous direction, which is the one worth stating: minimax's 0.408 was flattered on the instance where the spurious series was informative, not penalised.

**One free model reaches the reference, which had not happened before.** minimax-m3.1-flash means 0.408 against the reference's 0.409 on byte-identical instances, and it beats the reference on two of the three: 0.213 against 0.369 on adverse and 0.454 against 0.500 on severe. It loses the baseline instance 0.558 against 0.360. On the worst-case convention this repository reports, 0.558 against 0.500, it is still behind, and on one draw per cell that ordering is not resolved either way. What is new is that the gap between the best free model and the shipped reference on this task is no longer a gap.

**These three instances are harder than average.** The reference reads 0.409 on them against 0.292 over the twenty-four instance bracket, so the model rows should be read against 0.409 rather than against the bracket.

**The free-model rows cannot be compared across runs, and the measurement says so.** Rerunning both models on the same pinned instances with byte-identical data moved ultra's mean from 0.617 to 0.897, with one instance moving 0.758, while the deterministic reference moved at most 0.015 on the same instances. Sampling variation is fifty times the size of a real change to the generator. Any free-model number here is one draw, not an estimate.

### The Backtest Separates Two Failures the Score Cannot

| Row | `fit_all_years_ratio` | `fit_stress_mean_ratio` (removed) | `fit_peak_prominence` | forward stress ratio |
| --- | ---: | ---: | ---: | ---: |
| one-factor reference | 0.81, 0.74, 0.82 | 0.64, 0.56, 0.63 | 0.38, 0.42, 0.62 | 0.73, 1.18, 0.41 |
| minimax-m3.1-flash | 1.00, 1.00, 1.00 | 0.80, 0.97, 0.85 | 0.94, 1.02, 1.19 | 0.63, 0.86, 0.28 |
| nemotron-3-super | 0.99, 1.00, 1.00 | 0.54, 0.45, 0.41 | 0.14, 0.09, 0.14 | 0.72, 1.04, 0.04 |
| nemotron-3-ultra | 0.99, 0.98, 0.96 | 0.98, 0.80, 0.54 | 1.80, 0.63, 0.89 | n/a, 1.58, 0.06 |
| degenerate | 0.00 | 0.00 | 0.00 | 0.00 |

Super and the reference score 0.527 against 0.409, close enough that the score alone says only that one is somewhat better. The backtest says they fail in different ways. The reference under-predicts its whole history, all-years 0.74 to 0.82, because ridge shrinkage damps the level along with the response. Super gets the unconditional level exactly right, all-years 0.99 to 1.00, and has almost no macro response at all: prominence 0.09 to 0.14 means its fitted series is nearly flat, and all three instances fall below the 0.25 threshold at which a peak can be timed. That is the pure form of the failure this diagnostic was built for, and it is invisible in the score.

The prominence column separates them by a factor of four where the score separates them by 1.3. Forward confirms it: super's severe instance projects 4% of the true stress response.

Ultra fails a third way. A near-perfect backtest on the first two instances, all-years 0.99 and 0.98 with prominence 1.80 and 0.63, beside a forward response of 0.06 on the third. It is the interpolation failure described above, and only the pair of columns identifies it.

**minimax-m3.1-flash is the case that settles what the backtest is worth.** It has the best backtest in the table by every column: the level exact at 1.00 on all three, the stressed years at 0.80 to 0.97 where the reference manages 0.56 to 0.64, and a peak at 0.94 to 1.19 of the observed one. If a good backtest implied a good forward response, this row would be the proof. Its forward severe response is 0.28. A model can reproduce twenty years of history including the peaks and still propagate under a third of the stress response into a scenario it has not seen, which is precisely why the forward ratio is reported beside the backtest rather than in place of it.

**Every row in the table under-responds on the severe instance, and only on that one.** Forward stress reads 0.04 for super, 0.06 for ultra, 0.28 for minimax and 0.41 for the reference, against 1.04, 1.58, 0.86 and 1.18 on adverse. Four independent solvers, one of them deterministic, fail in the same direction on the same instance and are unbiased or over-responsive one instance away. The failure is not a property of any model: severity itself is what breaks extrapolation, and the direction it breaks in is the one that under-reserves. The reference's own 0.41 is documented above as a known failure of its own check, so the generator is not being graded here by a solver that passes.

**The hard constraint was respected without being asked for.** Every supplied matrix has rows summing to one, no negative cell survived, and the submission gap is 0.0000 in every case, so each agent's documented matrices reproduce its own reported projection exactly. The matrices are genuinely the models used, not decoration.

**The judgment-dependent constraint was not noticed at all.** Default monotonicity is violated 0, 0 and 9 times by super, 0 and 16 times by ultra, and 0, 0 and 10 times by minimax, against 54 adjacent-pair checks per instance, nine quarters by six notches. Ultra's severe matrix inverts 30% of adjacent pairs, minimax's 19% and super's 17%: they assert that better-rated obligors default more often. All three break it on the severe instance and nowhere else, which is the same instance every one of them under-responds to, so the two defects arrive together.

The vocabulary count says why. Across the nine transcripts, excluding the prompt itself, "rows sum" and "renormalise" appear one to twenty-one times each, while "prudent", "reserve" and "implausible" appear **not once**. minimax is the first model in this task to use the word "monotone" at all, six to nine times per instance, and not once about the rating ordering: it means monotone in the default rate across ratings as a clue to identifying the generator, and monotone convexity of the stress response. The word arrives as a tool for reverse-engineering the hidden law, never as a condition its own answer should satisfy. The earlier run on the previous configuration found the same substitution, with "monotonic" referring to a bisection converging in a scalar.

The split is explained by whether the constraint is self-enforcing. Rows summing to one has a mechanical consequence: mass leaks and the projection misbehaves, and scaling rows to 1.2 drives the submission gap from 0.0000 to 2.5163. An agent is dragged to it by the arithmetic. Monotonicity has no mechanical consequence and costs a third of a basis point of score, so it matters only to someone who already knows a transition matrix should have it. That is the domain judgment a review function supplies, and neither model supplied it.

This is also the evidence for the tie-breaker treatment rather than a gate. Gating on monotonicity would have disqualified both models for a defect costing nothing measurable, which is the over-reaction the materiality argument rules out. Reporting it lets the defect be seen without pretending it drove the score.

One operational gap. nemotron-3-ultra produced no parseable `matrices.csv` on the baseline instance, so the matrix diagnostics are absent rather than zero for that sample, and under the check layer that absence reads as a `matrices_readable` finding rather than as a clean zero. That absence crashed the aggregation step until the scorer was taught to fill every reported key, which is recorded under the diagnostics above. super and minimax supplied all three. Aggregating a row whose matrix is sometimes missing still needs a convention before this becomes a reported column, because 0.67 and "two of two supplied were clean" are different claims.

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

7. **What the naive baseline is.** Not on the original list either, and it only became a question when the README table needed a *Naive baseline* cell for this column. The row is ranked in the Borda count, so it cannot be left unmeasured without averaging that row over seven columns while every other ranked row uses eight.

   *Resolved after rejecting four candidates, and the rejections are the content.* The first was through-the-cycle: pool the counts into one unconditional matrix and apply it in every scenario. It scores 0.673 over twelve instances and is the wrong reference, because answering all three scenarios identically makes it fail four checks that are a strict **subset** of the six the degenerate answer fails. A naive row whose defects nest inside the row below it adds no axis to the table, so a naive baseline here has to get the macro response wrong rather than omit it.

   The second was the CCAR naive transplanted literally, ordinary least squares of the annual default rate on all six macro levels. On the three instances the column is reported on it looked ideal, 0.442, 0.571 and 0.350 with all sixteen checks passing, and it is a trap: over twelve instances it runs 1.263 mean, 4.435 max, and is worse than the degenerate answer on five of them. Unpenalised least squares on six collinear levels is heavy-tailed, three draws cannot see a tail, and the figure a three-instance column would have reported is the benign end of a distribution that reaches past the worst model in the table. Stress by analogy to a historical year fails the same way at 1.201 mean and 3.264 max, and removing the ridge from the reference reaches 0.409 mean but beats every model in the column on some instances, which is not a floor.

   *What ships* is `single_driver`: the same factor estimates regressed on the unemployment **level** alone, unpenalised, projected over the scenario. Two parameters on twenty observations needs no penalty, which is why it is stable where the six-driver version is not, and its error is the omitted variables instead.

   | Twelve instances | Mean | Median | Max | Worse than degenerate | Checks failed |
   | --- | ---: | ---: | ---: | ---: | ---: |
   | one-factor reference | 0.286 | 0.266 | 0.621 | 0 of 12 | 0 |
   | **single-driver, shipped** | **0.487** | 0.478 | **0.843** | **0 of 12** | **0** |
   | scale the default column | 0.698 | 0.699 | 0.857 | 0 of 12 | 2 to 3 |
   | through-the-cycle, rejected | 0.673 | 0.648 | 1.001 | 1 of 12 | 4 |
   | unshrunk six-driver, rejected | 0.409 | 0.349 | 1.105 | 1 of 12 | 0 to 1 |
   | rate on six levels, rejected | 1.263 | 0.516 | 4.435 | 5 of 12 | 0 |
   | worst-year analogy, rejected | 1.201 | 0.821 | 3.264 | 5 of 12 | 0 |
   | degenerate answer | 1.000 | 1.000 | 1.000 | 12 of 12 | 6 |

   The defect it carries is the one worth carrying. Unemployment alone explains 0.35 of the variance of the annual factor, so the fitted slope is diluted and the severe-scenario peak factor comes out at 0.54 of the reference's. The naive solver projects a severely adverse peak **below the worst year in its own estimation sample on ten of twelve instances**, against the reference's eight, which is the under-reserving direction `backtest_diagnostics` is one-sided about. It does that while passing all sixteen checks, so nothing in the check layer catches it and only the score and the backtest ratios can.
