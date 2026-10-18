# Rating Migration

**Status: built, not measured.** The generator, the four-component scorer, two reference solvers and the Inspect task exist. One smoke test has been run against free models; the task does not appear in the README's score table and will not until there is a cell for every ranked row.

The task gives an agent forty years of annual rating transition counts for a 10,000-obligor portfolio, quarterly macroeconomic history, a nine-quarter supervisory scenario, and a holdout cohort whose rating mix differs from the historical one. It must project where that cohort stands at quarters 4 and 9, and separately record the quarterly transition matrices it used.

The intended difficulty is annual-to-quarterly conversion. A quarterly matrix obtained by rooting an annual one can be inadmissible: negative or complex migration probabilities, and a non-monotonic relationship between rating and default probability. That is the Markov embedding problem, and the standard references are Israel, Rosenthal and Wei (2001) on when a generator exists, Kreinin and Sidelnikova (2001) on regularising an invalid root, and Higham and Lin on pth roots of stochastic matrices.

The trap is real and it is not tuned. Because the systematic factor moves every quarter, the annual matrix for a year is a product of four different quarterly matrices rather than the fourth power of one, so no quarterly matrix reproduces it. Measured on the exact arithmetic the principal fourth root reaches about -3e-08; with the finite 10,000-obligor portfolio it reaches -7e-03, five orders of magnitude worse, which is what an agent actually meets. Both free models in the smoke test found the negative entries, called them numerical issues, and clipped them.

Bracket: oracle 0.000, one-factor reference 0.158, degenerate 1.000.

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

So admissibility breaks ties. `matrix_admissible` is the single flag, set when rows sum to one, no cell is negative, no reachable cell is exactly zero and default is non-decreasing in grade. Where two cells sit within the resolution this suite claims, a factor of a few, prefer the admissible one. The component counts stay reported for diagnosis. `tests/test_migration_task.py` pins the immateriality measurement, so a later change that makes admissibility material fails the test rather than quietly surviving.

One limit worth stating. A clean submitted matrix cannot distinguish an agent that reasoned about admissibility from one that clipped silently and got lucky. Both free models in the smoke runs found the negative entries and still called them numerical issues. That reasoning lives in the transcript, and grading it would need a judge, which this suite does not use.

## What Is Deliberately Absent

No generator, no scorer, no task wrapper, no agent results. The open design questions, in the order they need answering:

1. **Where the oracle comes from.** Handing an agent a real published annual matrix and asking for the quarterly one has no verifiable answer, because a stochastic root need not be unique and most empirical annual matrices are not embeddable at all. The target has to be something generated forward from a hidden quarterly law, or a downstream economic quantity, rather than the matrix itself.
2. **What is scored.** Scoring a matrix entrywise forces arbitrary choices of norm and of how to weight the default column against the diagonal. A scalar economic output, such as cumulative default probability by initial rating over a horizon, fits the rest of this suite better and makes an inadmissible intermediate matrix show up as a bad score rather than being the scored object.
3. **Admissibility as a separate diagnostic.** Negative entries, rows not summing to one, and violations of rating monotonicity belong alongside the regret, in the way `completion` sits alongside the CECL score, rather than inside it.
4. **How macros enter.** The conventional form is a systematic credit-cycle factor shifting ordered-probit thresholds, which would give a per-instance hidden response law of the kind the CCAR generator now draws.
