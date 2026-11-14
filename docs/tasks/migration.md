# Rating Migration Under Stress

The hardest column in the suite. An agent must take twenty years of annual rating transitions and a quarterly macro history, estimate one macro-conditional migration model, and project a cohort over nine quarters under three supervisory scenarios.

```
inspect eval pereval/tasks/migration/task.py --model <provider/model>            # needs Docker
inspect eval pereval/tasks/migration/task.py -T baseline=onefactor --model mockllm/model
inspect eval pereval/tasks/migration/task.py -T n_instances=3 -T seed=1 --model <provider/model>
```

## Task

The agent is given four files and writes three.

| Given | Contents |
| --- | --- |
| `data/transitions.csv` | observed rating transitions for this portfolio, annual counts by from-grade and to-grade, twenty years |
| `data/macro_history.csv` | nine quarterly macro series over the same period |
| `data/scenario.csv` | the same nine series for nine future quarters, under each of `baseline`, `adverse` and `severe` |
| `data/portfolio.csv` | the cohort to project, as obligor counts by rating |

| Written | Contents |
| --- | --- |
| `predictions.csv` | the cohort's distribution over seven live grades plus default, at quarters 4 and 9, under each scenario. 48 rows |
| `matrices.csv` | the quarterly transition matrices the model used, per scenario, plus one per historical year under the reserved scenario name `history`. 329 rows |
| `backtest.csv` | the annual default rate the model projects for each historical year, against the portfolio that year actually started with |

**One history, three scenarios.** The instance carries one set of counts, one macro history, one holdout cohort and three paths over the same future quarters. The prompt asks for one model estimated on the history and three projections through it. That shape is what makes per-scenario refitting observable: a model estimated once implies one fitted historical series and writes it three times, and a model refitted per scenario writes three different ones.

The central difficulty is that the observations are annual and the projection is quarterly, so a quarterly law has to be produced from annual data. The prompt does not say how.

## Data

### Provenance

All calibration figures come from S&P Global Ratings, *Default, Transition, and Recovery: 2024 Annual Global Corporate Default And Rating Transition Study*, published 27 March 2025, retrieved 29 September 2026 from the S&P Global Ratings Maalot site. Two tables are used: Table 20, 2024 one-year corporate transition rates by region, four panels; and Table 21, global corporate average transition rates 1981-2024, at one and three years with a standard deviation beneath every mean. The PDF is not committed.

| File | Contents |
| --- | --- |
| `data/sp2024_regional_counts.csv` | reconstructed integer counts and cohort sizes, four regions, six rating rows |
| `data/sp2024_regional_published_pct.csv` | the percentages exactly as printed, for round-trip validation |
| `data/sp_global_average_1981_2024.csv` | long-run global averages at one, three and five years, mean and standard deviation |

The study publishes percentages, not counts. For a single-year static pool every entry of a row is an integer count over one cohort size, so counts are recoverable by searching cohort size upward and keeping the first value for which all nine published entries match an integer count to two decimal places and sum to the cohort size. `scripts/migration_invert_counts.py` performs that derivation and checks it against the committed counts, and `tests/test_migration.py` pins the round trip.

Cohort size is identified only up to a positive integer multiple, and the smallest consistent value is used. For the Global panel an external figure closes that: the reconstructed default column sums to exactly 130, and the study states separately, in prose rather than in any table, that of the 145 total defaulters in 2024, 130 were rated at the start of the year. The global 2024 rated cohort totals 6,496 issuers. The three regional panels have no equivalent check.

### The Data Rejects a Time-Homogeneous Markov Chain

This is the empirical premise of the task. The study publishes a one-year and a three-year average matrix over the same 44 static pools. Under a time-homogeneous chain the three-year matrix would be the cube of the one-year matrix. It is not, and the cube understates published three-year default probability:

| From | Cubed one-year | Published three-year | Ratio |
| --- | ---: | ---: | ---: |
| AAA | 0.042% | 0.130% | 0.32 |
| AA | 0.085% | 0.110% | 0.77 |
| A | 0.176% | 0.200% | 0.88 |
| BBB | 0.523% | 0.670% | 0.78 |

The direction holds whether withdrawals are treated as absorbing or dropped and renormalised, and it is consistent with the documented tendency of downgraded issuers to keep migrating downward, which a memoryless chain cannot represent. So taking a principal fourth root of an annual matrix is not merely awkward numerically, it fits a model the data rejects. `tests/test_migration.py` asserts the gap so a later edit to the reference data cannot quietly remove it.

### The Generator

Instances are drawn from those calibrations: a synthetic portfolio, twenty years of annual transition counts generated under a one-factor threshold model with a drawn asset correlation, a quarterly macro history, and three nine-quarter scenario paths.

Scenario paths are humped rather than monotone, because published supervisory scenarios deteriorate for a few quarters, turn, and partly recover. A severity weight rises to a drawn peak quarter and decays to a drawn residual: two to three quarters and up to 30% residual for `baseline`, three to five and 20 to 45% for `adverse`, four to six and 35 to 60% for `severe`. The systematic factor peaks one to two quarters after the macro path, because credit deteriorates after the economy does.

**No scenario may exceed ten times the portfolio's own historical loss rate** over the horizon (`SEVERITY_CAP = 10.0`). Without it the generator drew scenarios that were not stress tests but the portfolio ceasing to exist: one seed put 98.9% of the book in default by quarter nine under severe and 12.9% under its own baseline, against an observed history of 1.12% a year. The bound is stated against the observed annual default rate in `data/transitions.csv`, not against the drawn baseline, because the baseline is itself a draw and is itself elevated. It binds on about one instance in eight and only at the top of the distribution, leaving a typical severe scenario at roughly four times the historical rate. Damping is applied to the macro hump weights rather than to the factor, so the published `scenario.csv` still implies the factor path the answer key uses. One instance in sixty cannot be damped at all, because its history ends in a crisis, and is redrawn from a derived seed.

### The Top of the Scale

Global AAA to default over 1981-2024 is published as 0.00% at one year. A frequency of zero is not a probability of zero: Cromwell's rule says a grade assigned zero can never be revised by evidence, and a logistic or ordered-logit link maps any finite score into the open interval, so zero is outside the estimator's range by construction. A grade carrying zero default probability also carries zero allowance on a live exposure.

So `top_of_scale_annual` extends the notch ratio from where defaults are observed. A over AA is 0.05% over 0.02%, a factor of 2.50, and one notch further gives AAA 0.008% annual. Only AAA is replaced; every other grade keeps what the root gives it. The obvious alternative, a log-linear fit over BBB through CCC/C, is rejected because the notch multiplier steepens down the scale and a slope fitted on speculative grades understates a grade where defaults are observed, projecting 0.020% for A against 0.050% actual.

**No regulatory capital floor is applied.** 12 CFR 217.131(d)(2) sets 0.03% and Basel CRE32.4 sets 0.05%; both are recorded in `PD_FLOORS` as reference facts and neither is used. A capital floor constrains a long-run through-the-cycle PD, and this task produces the opposite object, point-in-time macro-conditional probabilities, where a benign quarter can legitimately sit far below a through-the-cycle floor. A top grade pinned at a floor also has no macro sensitivity left in it, which is the defect the rest of this task is built to detect.

## Scoring

The composite is **twelve equally weighted components**: for each of the three scenarios, a KS distance over the seven live grades and the cumulative default rate, each at quarter 4 and quarter 9.

Default is scored separately from the live grades because a sup-norm over the whole eight-state distribution hides it: the supremum is usually attained mid-distribution where cumulative mass is large, so a one point error in defaults disappears behind a three point error in BBB.

Each component is divided by what the **degenerate answer** scores on it, namely submitting the starting cohort unchanged, so every component reads as a fraction of the uninformative answer. 1.0 is no better than predicting no migration and 0.5 is twice as good. The composite is the plain mean, which gives equal weight by construction rather than by a chosen constant. On the one-factor reference over twelve instances the twelve components run 0.160 to 0.384, and the per-scenario composites run 0.228, 0.284 and 0.343, monotone in severity.

### Checks

Sixteen binary checks, each reported as `fail_<name>`, plus `checks_failed` and `checks_total`. `checks_failed` is published beside the score in [Results](#results). Averaged over samples each reads as the share of submissions carrying that finding, and the count is the number of findings a reviewer would write up. Nothing about a continuous distance tells a reviewer whether to send a model back, which is what these are for.

Three rules govern what is allowed in: a check must be **defensible without the answer key**, must be **computable on every submission** (a NaN is neither pass nor fail, so ratios whose denominators can vanish are restated as orderings), and an **absent or unreadable artefact fails every check that reads it**.

**Integrity, seven.** `matrices_readable` and `predictions_readable`, `matrix_cells_finite` and `prediction_shares_finite`, `matrix_cells_are_probabilities`, `matrix_rows_sum_to_one` and `prediction_shares_sum_to_one`. Nothing is repaired before these run: the parser used by the score coerces and fills, so a NaN there becomes a number, while these read the raw blocks and count it.

**Shape, three.** `pd_rises_as_rating_falls`, `stay_is_the_most_likely_outcome`, and `multinotch_downgrade_possible`, which asks that the three-or-worse band is not identically zero, because zero is not an estimate but an assertion that the move cannot happen.

**Macro response, four.** `downgrades_rise_with_severity`, `pd_rises_with_severity`, `implied_pd_rises_with_severity` (the same question asked of the matrices, by propagating the published cohort mix through them), and `pd_rises_with_horizon`. The severity checks compare every adjacent pair, because an adverse projection no worse than baseline is the same defect as a severe one no worse than adverse. The projection and the matrices are separate claims, which is why severity ordering is asked of both: a submission can file a perfectly ordered projection computed by some other route while the matrices it documents imply the opposite.

**Historical fit, two.** `historical_fit_identical_across_scenarios` is an exact equality to CSV precision, with no threshold and nothing taken from the answer key. `fitted_downgrades_rise_in_bad_years` asks that the migration body the model implies for its own historical quarters moves with the cycle it was fitted to.

The prompt says only that `matrices.csv` documents how the projection was produced, and does not say what is examined. The silence is the point: it tests whether an agent raises these questions unprompted, as a review function would.

**Admissibility breaks ties rather than entering the score, and that is measured.** Holding the generator fixed and degrading only the reference's own matrices, leaving the fourth root's 43 exact zeros and 2.2 ordering inversions per submission costs a third of a basis point against the reference's own error of 0.292. The defect is orthogonal to accuracy rather than merely small. A weight would be fiat, with no accuracy cost to calibrate against; a gate would disqualify a model whose accuracy is unaffected, which is not what a review function does. The defects separate into three tiers: rows not summing to one is consequential, because mass non-conservation compounds over nine quarters and drives the gap between the submitted distribution and what the matrices propagate to from 0.0000 to 2.5163; negative cells are middling, since clipping is a defensible remedy and the same gap moves only to 0.0001; exact zeros and a non-monotone default ordering are soft.

### Diagnostics

Reported, never scored. From `backtest.csv`: `fit_peak_ratio` at the single worst year, `fit_all_years_ratio` as its control, and `fit_peak_prominence`. From `matrices.csv` and the truth: `stress_mean_ratio`, `stress_peak_ratio`, `stress_peak_lag`, `default_ratio_q4` and `default_ratio_q9`. Against the rebuilt oracle: `matrix_down3_ratio`, `matrix_down1_ratio` and `matrix_down3_shape` on the far downgrade corner, and `matrix_downgrade_concordance`, `matrix_downgrade_slope` and `matrix_downgrade_response` on whether the migration body answers the macro path.

Rows are weighted by the published cohort mix throughout, because the question is how much of this portfolio the matrix sends three grades down, not how distorted the thinly populated AAA row is. Default is excluded from all of them, since including it would let a correct default column hide a collapsed migration body.

**The two groups are each blind where the other sees.** Folding multi-notch mass into the adjacent grade conserves total downgrade mass, so concordance reads 1.000 while the far ratio reads zero. A frozen body leaves the far corner's shape roughly intact while concordance reads exactly zero. The backtest statistics and the forward stress ratios are a similar pair, and their **disagreement** is the diagnosis: both low is a model with too little macro sensitivity; high in the backtest and low forward is a model that cannot leave its own sample.

The backtest is one-sided. A stress test is asked one question, how large are losses under a given scenario, so understating is the failure that matters and overstating is conservative rather than wrong. Every statistic is a ratio of projected to observed and only values below one are findings. Scaling the reference's macro response by k over twenty-four instances moves the stressed-year ratio monotonically from 0.26 at k=0 to 1.07 at k=1.5, so a model with half the right sensitivity under-projects by 32% and one with none under-projects by 60%.

## Results

Worst-case regret over three instances, where 1.0 is the degenerate answer, beside the failed [checks](#checks) of the one submission that sets that cell. Lower is better in both.

<!-- scores:begin (generated by scripts/render_scores.py; do not edit by hand) -->

| Model | Score | Checks failed |
| --- | --- | --- |
| *Oracle (true model)* | *0* | *none* |
| Claude Opus 5.5 | **0.118** | 1 / 16 |
| Kimi K3 | 0.301 | 0 / 16 |
| GLM-5.1 | 0.523 | 0 / 16 |
| mimo-v2.5 | 0.556 | 1 / 16 |
| deepseek-v4-flash-0731 | 0.625 | 10 / 16 |
| minimax-m3.1-flash | 0.629 | 1 / 16 |
| *Naive baseline* | *0.765* | *0 / 16* |
| *Degenerate answer* | *1.000* | *none* |
| gpt-6-luna | 1.094 | 0 / 16 |
| nemotron-3-ultra | 1.214 | 10 / 16 |
| Qwen3.6-35B-A3B (local) | 1.267 | 2 / 16 |
| nemotron-3-super | 1.400 | 10 / 16 |
| ling-3.0-flash | 1.612 | 1 / 16 |
| Claude Haiku 4.5 | 4.068 | 5 / 16 |
| gemma-4-26B-A4B (local) | 6.179 | 4 / 16 |

<!-- scores:end -->

Read against two lines. The **competent one-factor reference scores 0.368**, and only two rows land inside it. The **degenerate answer is 1.000** by construction, and seven of the fourteen ranked rows are outside it, the most of any column in the suite.

That is the headline: on the suite's hardest column, half the field does worse than predicting that nothing migrates at all.

**The two columns disagree, and that is why both are here.** gpt-6-luna's 1.094 is worse than the degenerate answer and passes all sixteen checks: a fully admissible model, correctly documented, beaten by assuming nothing migrates. deepseek's 0.625 is the column's fifth-best score and fails ten. gemma's 6.179, the worst cell in the suite, fails four. The naive baseline passes all sixteen. Over the thirteen ranked rows the two columns rank together at 0.79, so admissibility tracks accuracy loosely overall and not at all at the top, which is the measured form of what the [checks](#checks) argue from degrading the reference's own matrices.

**Ten of sixteen is one omission rather than ten findings.** The three rows at ten fail the identical ten checks, and the first of them is `matrices_readable`. An absent or unreadable artefact fails every check that reads it, so those rows filed a projection and never filed the matrices that document it. Read ten as no `matrices.csv`, and sixteen, which no published cell carries, as no submission at all.

**The modal finding is a single check.** `pd_rises_as_rating_falls` fails in nine of the thirteen ranked rows, inside all three of the tens, and it is the only check Opus ever fails. On the suite's hardest column the most common defect is not a failure to answer the macro path but a submitted scenario whose default probability does not rise monotonically down the rating scale.

**gemma fails a different family, and it is the coherent one.** Its four are `downgrades_rise_with_severity`, `pd_rises_with_severity`, `implied_pd_rises_with_severity` and `fitted_downgrades_rise_in_bad_years`, which is three of the four macro-response checks and one of the two historical-fit checks, with every integrity and shape check passing. The worst cell in the suite is a well-formed, internally monotone matrix that does not answer the macro path in either direction, forward or in its own history, which is what a regret six times the degenerate answer should look like.

A count flattens the three severity tiers the checks separate into, so it is a pointer to the named checks in the log rather than a severity score. Nothing here enters the score, by the argument in [Checks](#checks).

Two cells are weaker evidence than the rest. minimax's is set by one of two instances the six-hour wall clock truncated, so it bounds its regret from above rather than measuring it, and Opus is reported on the [matched convention](../models.md#the-matched-convention) rather than as a plain maximum ([detail](../models.md)).

Same-instance spread is wide enough to matter here. On one measured set, three draws of a byte-identical instance ran 0.237 to 0.634, wider than the gap between most adjacent rows.

## Solutions

**The construction that wins is an ordered-probit threshold model with one latent factor, and it sidesteps the matrix-root problem entirely rather than solving it.**

The strongest submission builds it in five steps. Pool the twenty years of counts into an unconditional matrix and convert each row to cumulative thresholds from default upward, which is the CreditMetrics representation. Make the whole matrix a function of one scalar by shifting those thresholds, `P(state >= j | z) = Phi((Phi^-1(c_j) - sqrt(rho) z) / sqrt(1 - rho))`. Estimate one latent factor per historical year by maximum likelihood on that year's counts. Regress the factor on the macro series, with a ridge penalty, finding house-price change dominant at correlation -0.97 and unemployment adding materially while spread, VIX, GDP growth and inflation add almost nothing once those two are in. Then project the factor over the scenario quarters and apply the same threshold shift at a quarterly base chosen so that four quarters reproduce the year's modelled default rate.

Three details carry weight. **One shared macro sensitivity across grades** beat letting grades respond at different strengths, which did not improve the fit. **The quarterly base is calibrated, not rooted**, which is what avoids fitting the time-homogeneous chain the data rejects. And the best submission **named its own extrapolation risk**, noting that the severe path pushes house-price falls to about 12% against a historical worst of 5 to 8%, so that path relies on the model extrapolating.

**Estimating a continuous-time generator instead is a sound diagnosis and costs about half again.** Forcing a generator onto the true law is nearly free: pushing the true quarterly matrices through their closest generator leaves a worst case of 0.36% of the degenerate error, against the reference's 28.5%. What the route imports is a choice the probit parameterisation never has to make, namely how stress enters the intensities. Under the true threshold shift the implied generator does not scale, it splits into blocks moving in opposite directions, graded by notch distance:

| Cell class | n | Median log2 shift | As a factor |
| --- | ---: | ---: | ---: |
| Upgrade | 15 | -7.43 | divided by 173 |
| Downgrade, one notch | 6 | +4.36 | times 21 |
| Downgrade, two or more notches | 13 | +6.26 | times 77 |
| To default | 6 | +6.30 | times 79 |

A single time change scaling every intensity by one multiplier can represent none of that. The penalty is measured rather than argued: on one instance, a submission that fitted a full forty-nine-intensity generator with direction-based multipliers recovered the hidden latent factor at correlation 0.9989, better than any other submission on that instance, and scored 0.1029, while a plain ordered probit with free cutpoints on the same instance scored 0.0688. The gap is the functional form. Twenty annual observations cannot identify how stress is apportioned between upgrades, downgrades and defaults, so a well-run maximum likelihood on them drifts toward the one form that is wrong out of sample. The probit parameterisation gets the two-signed, notch-graded response from structure rather than from data the task does not supply.

**The characteristic failure is a frozen migration body.** One reconstructed submission attached a scenario-sensitive default probability to a single unconditional migration matrix and left the body alone: its live block is identical to four decimal places in every quarter, a maximum relative range of 0.0001 for AAA against 3.8 to 7.9 for the truth, while its default column moves by a relative range of 2.4 to 5.4. At the trough the truth sends 11.1% of AAA obligors down two grades or more and the submission sends 0.57%. Renormalising a row to absorb a rising default probability shrinks every migration cell in it, so a model that conditions only its default column makes downgrades very slightly *less* likely in stress, which is the wrong sign.

**Inversions at the top of the scale are the most common finding.** On one nine-submission run, `pd_rises_as_rating_falls` fired on six, with 181 inverted cells, 47 of them larger than 1e-4, and the worst asserting that AAA carried three times AA's default probability. Every inversion was in the top two pairs and none anywhere below, spread evenly across scenarios, so it is a property of the estimated model rather than of the stress overlay: the top grades have almost no observed defaults, an unconstrained estimate is noise there, and nothing in the fitting imposes the ordering.

## Limitations

**The shipped reference fails its own backtest check.** The ridge shrinkage that stops it blowing out on the projection also damps its macro response, so it under-projects the stressed years by about a third, 0.66 projected over observed against the unshrunk fit's 1.02. There is no reparameterisation out of it, because coefficient magnitude *is* the macro response. Two alternative explanations were ruled out: substituting a per-year maximum-likelihood factor takes the ratio to 1.03-1.10, so within-year variation is not what is being detected, and the observed peak sits within 1.1 to 3.5 binomial standard errors of that fit, so the model is not being penalised for declining to chase noise. The score rewards the damping and a stress reviewer would issue a finding for it. That makes the anchor competent and challengeable rather than a target: an agent that beats 0.285 while keeping its stress ratio near one is doing something the score cannot see.

**The backtest cannot detect overfitting, and is blind to a model that cannot extrapolate.** The band is computed from the residuals of the fit it is drawn around, so it shrinks as the fit tightens: an unshrunk reference covers its stressed years at 97.5% against the shipped fit's 85.0% and draws a band thirty percent tighter, while its actual forward coverage is 75% against a nominal 95%. Leave-one-out residuals move it the right way and not far enough. Separately, a backtest has no power against a model that interpolates its history: one submission returned a backtest correct to five parts in ten thousand while projecting 13.3% of the true stress response, and its own reasoning named the defect before submitting. No truth-free check for that was found; the candidate internal-consistency test was measured and does not separate, and is recorded as a negative result.

**The far-corner diagnostics need the oracle and scatter widely.** The reference's own far ratio runs 0.301 to 5.107 over the twenty-four instances the task draws at base seed 1, dipping below 0.5 on four of them, so no threshold separates a thinned submission from an honest one and the statistic is reported rather than scored. It also needs the submission written to enough precision: rounding the oracle's own matrices, the ratio reads 1.0000 at eight decimals and 0.6393 at three, so the instructions ask for at least six.

**The scale is seven rating categories, not twenty notches**, so a two-grade move is already A to BB and the far corner holds only ten cells. Nothing here transfers directly to a notch-level scale.

**The reference data is one agency and one asset class.** Corporate issuer ratings from a single agency, with small cohorts at the ends of the scale, 27 issuers in Europe AA and 48 in EM CCC/C. 2024 was benign for investment grade and harsh for CCC, which is why both the single year and the long-run averages are stored. Withdrawals are a column, not a nuisance: `NR` carries 3% to 19% of each cohort and how it is treated changes implied default probabilities materially. The long-run averages do not invert to counts, having no single cohort size behind them. ESMA's CEREP publishes transition matrices as counts directly, including withdrawals, filterable by agency and region, and is the better source for a second agency; its interface is not practical to script.

**AAA has no recoverable 2024 count row**, because its published row is 100% on the diagonal, which fixes no cohort size. That is a gap in the counts only; AAA is present at all three horizons in the long-run averages and must stay in any state space.

**A clean submitted matrix cannot distinguish reasoning from luck.** An agent that thought about admissibility and one that clipped silently look identical in the file. That reasoning lives in the transcript, and grading it would need a judge, which this suite does not use.
