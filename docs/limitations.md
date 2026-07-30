# Known Limitations and Design Decisions

This is a demonstration of eval construction, not a production benchmark. Corners deliberately cut are documented here rather than hidden.

## Four Defects Found by Independent Review

An independent review of the suite found four problems that each changed a published conclusion. They are recorded here in full, because a suite whose selling point is auditable reporting has to survive its own effective challenge, and because the fixes are the most interesting design work in the project.

### Non-Response Was Cheaper Than Failure

`pereval/scorers/interval.py` charged a missing prediction five times the **oracle** score. That anchors the penalty to the irreducible measurement noise rather than to the difficulty of the task, and on these tasks the noise floor is one to four degrees while a bad answer costs hundreds. Submitting nothing therefore scored better than trying and failing on most of the suite, and better than the naive baseline:

| Task | Cost of emitting nothing, old rule | Naive baseline | Best model |
| --- | --- | --- | --- |
| Ballistic | 3.84 | 22 | 12 |
| Two-body | 6.23 | 17 | 0.092 |
| Three-body | 9.63 | 332 | 13 |
| Flyby | 13.62 | 20037 | 17 |
| CCAR | 0.257 | 0.85 | 0.055 |
| Quantile | 0.570 | 0.14 | 0.099 |

Added to the summary matrix as a row, an agent that produces no output at all took **mean rank 3.17 against GLM-5.1's 3.25**, so it won the suite. This was not hypothetical: deepseek-v4-flash-free's three-body (13) and flyby (17) were the best figures in both columns, were pure non-response penalties from an upstream failure, and were what ranked it second overall.

Two things were wrong and both are fixed. The penalty is now the score of the **degenerate answer**, one constant point estimate with no interval, floored at the old oracle multiple; the quantile scorer already did the equivalent by pricing a blank at five times `np.percentile`, so the two scorers now agree in convention. And a cell with any incomplete run is reported as unmeasured rather than as a number, which was already the stated policy under Budget Confounds below and was the policy applied when gpt-oss-20b was excluded from the quantile table. It just had not been applied here.

### The CCAR Response Law Was Public

The contamination argument below rests on instance parameters not being recoverable from the source. For CCAR that was false. `P, RHO, K1, K2 = 0.028, 0.02, 0.13, -0.07` and the two standardizations were module-level constants in a public file, and nothing about the response law was drawn per instance, so the entire task was solvable in closed form with no estimation:

| Solver | Mean Winkler regret over the published eight instances |
| --- | --- |
| Closed form from the repo's constants | **0.00014** |
| Vasicek reference, then called near-oracle | 0.0126 |
| Best measured model (GLM-5.1) | 0.029 |
| Naive OLS baseline | 0.197 |

Ninety times better than the reference, two hundred times better than the best model, deterministic, and indistinguishable from excellent feature selection.

The response law is now drawn per instance: `p`, `rho`, `k1`, `k2`, **which two macros are the true drivers** (nine pairs), and the functional form, rotated over three families (`vasicek`, `threshold`, `interaction`). Twenty-seven distinct laws, none of them in the source. The same exploit now scores a median 0.32 against 0.07 for a fit handed the true drivers.

Rotating the form matters as much as randomizing the numbers, and for a different reason. With one fixed law a good score can only demonstrate that the agent recovers *that* law. The inference this suite exists to support is that the agent can recover *a* law, and that requires the form to vary. `task-design.md` listed both mitigations as obligations of the plasmode family and neither had been implemented.

**The published CCAR numbers are kept, not withdrawn.** The exploit was a vulnerability, not a realized contamination, and conflating the two would have thrown away valid measurements. Every model tested has a knowledge cutoff long before this repository existed (first commit 9 July 2026, runs 13 to 28 July), the sandbox has no network, and the generator source never enters it, so the channel was closed by dates alone. The direct evidence agrees: the closed form scores 0.00014, so a model that had recalled the constants would show a cell indistinguishable from the oracle, and the best measured cell is 0.055. Nobody used it.

What those numbers cannot do is compare across the change, because the replacement made the task harder rather than merely safe: the reference moved from 0.013 to 0.140 and the naive baseline from 0.20 to 1.23. They are labelled as the fixed-law variant and a fresh column starts at the rerun.

Two caveats do survive the concession. With drivers and coefficients fixed across instances, every CCAR instance posed the *same* feature-selection problem, so a good score demonstrated solving one law rather than an ability to recover a law: a narrower claim, not a wrong one. And the exposure was live for any *future* model, which is why the fix still had to happen; a fixed public law is a landmine with a delayed fuse, harmless until the first model trained after publication is tested and then silently rewarding memorization.

Separately, the old "near-oracle" reference turned out to be near-oracle partly because it was handed the answer to the feature-selection step, which is now its own measured quantity; see [tasks/ccar.md](tasks/ccar.md).

### Circular Intervals Were Rewritten by the Scorer

On the two circular tasks the scorer localized the two endpoints of a submitted interval to the branch nearest the true value **independently**, then swapped them if they came out inverted. That silently replaced the agent's interval with a different one. With a true value of 10 and a submission of `[100, 200]`, the upper endpoint wrapped to -160, the pair was swapped, and the agent was scored on `[-160, 100]`: 260 degrees wide and covering the truth it had missed by 90 degrees. The Winkler score fell from 3700 to 260, so the scorer credited coverage for an arc nobody submitted.

A submitted interval is now localized as a unit, preserving its width, by placing the midpoint of the arc from `lo` counterclockwise to `hi` on the nearest branch. Wrapping intervals such as `[350, 30]` still read as the 40-degree arc through zero, which is what an agent writing that means, and claiming the whole circle now costs the full period instead of collapsing to a point.

The guarded property is not monotonicity in width. Winkler is deliberately not monotone in width, since widening buys coverage, and on a circle growing an arc from a fixed lower endpoint brings its far end round toward the truth, so a penalty can legitimately fall. The property is that coverage is credited exactly when the true value lies on the submitted arc, checked across a grid of positions and widths.

This one was not latent. Re-scoring the predictions recorded in `runs/` shows 121 affected rows and moves whole runs in both directions: nemotron-3-super's three-body instance from 2744 to 726, which was the worst cell in the summary matrix, and Claude Haiku 4.5's from 343 to 1086. The three-body column is therefore labelled as scored by a superseded scorer, on the same reasoning as the superseded CCAR generator: valid measurements under the rule that produced them, not comparable across the change. Two-body is verified unaffected, because every wide interval in its recorded runs wraps through zero with the truth inside the arc, which both the old and the new rule read identically.

Re-scoring from the archived predictions was only possible because `runs/` and `logs/` are committed. It reproduces 11 of 15 unaffected runs exactly and mismatches on 4, where an agent wrote several versions of `predictions.csv` and the transcript does not identify which one was on disk at scoring time. That is enough to establish which cells move and not enough to publish corrected values, so no corrected values are published.

### Same-Instance Stability

Every measurement in the suite varied the instance between runs, so its spread mixed instance difficulty with method instability. Those have different consequences and only one of them is the agent's fault. `-T repeats=K` now runs the agent K times per instance on byte-identical inputs and reports the worst case and the spread separately.

This is the headline number rather than a diagnostic, and the reason is regulatory. SR 26-2 makes the frequency of validation a function of, among other things, the "frequency and scope of model changes" (Model Validation and Monitoring, in the [guidance attached to SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm)). An agent that hands back a materially different analysis every time it is run on the same data makes every invocation a model change, so validation cannot be discharged once before first use: it recurs at the invocation rate. That is a cost denominated in validator hours, and the spread is what prices it.

The reproducibility study below already measured this once by hand and found the spread large for capable models and near zero only for models that had collapsed to a fixed deterministic method, which is the worst behaviour the tasks exist to expose. Making it a first-class mode on every task is what turns that observation into a reportable property.

## Contamination

The repo is public, so anything fixed in it can enter training corpora. The four generated tasks (CCAR, ballistic, orbital) therefore draw fresh instances per run from a seeded, public generator with per-run randomized parameters (orbital elements, ballistic loads, macro draws, and the CCAR response law including which macros drive it), so there are no fixed answers to memorize and every score is computed against freshly drawn ground truth. The residual exposure is structural: a model could learn the generator's functional form from the source. That is largely defanged by design, because knowing the form does not reveal an instance's parameters, which must still be estimated from the provided data, which is the task itself.

That argument is only as good as its weakest task, and it was false for CCAR until the response law was randomized; see [The CCAR Response Law Was Public](#the-ccar-response-law-was-public) above. The lesson generalizes: this defense has to be re-checked per task rather than asserted for the suite, because it fails silently. Nothing about the fixed-constant CCAR task looked wrong from the outside, and its scores were plausible.

The quantile task is the exception and needs its own argument, because its data is real and public. It relies on a randomized observation window (the population quantile of an undisclosed span is not recallable even if the series is recognized), an independent random scale factor per block, and reduced precision. See [tasks/quantile.md](tasks/quantile.md).

## Sample Size

Every score table reports at least three runs per model as mean ± 2 SD, after the repeated-run standard was adopted, and no longer reports any cell whose runs did not all complete. The bands are still wide relative to the mean gaps (regret is heavy-right-tailed), so only coarse contrasts are established: the reference at the top, the models that fall through the naive baseline at the bottom, and the two-axis statistical-vs-physics split. Mid-field orderings are not resolved at n=3, and the aggregate rank is not resolved at six tasks either: an independent permutation test puts the observed spread of mean ranks at p = 0.25 against the null of no cross-task skill. Paired-difference comparison, the standard remedy and the one this project's own design doc prescribes, was measured and does not help here: 1% variance reduction on regret levels and 10% on logs, because the variance is model-by-instance interaction rather than instance difficulty. See [task-design.md](task-design.md#pairing-is-not-the-lever), and the next honest step is tens of instances with the paired, task-clustered error analysis described in [task-design.md](task-design.md).

## Run-to-Run Reproducibility

The reason three runs is a floor rather than a nicety: **on this suite an LLM agent's score is dominated by sampling temperature, not by the data.** A controlled experiment reran four free models on byte-identical inputs (the same seeds, the same generated instances, a second time) and compared each cell to its first run.

The results barely reproduce. Of 48 paired mechanism-task instances, **37 (77%) differed materially on the rerun**, and the swings are enormous: nemotron-3-super's three-body score went 2744 → 133, mimo's flyby went 89 → 2601, nemotron-3-ultra's three-body went 1579 → 3726, up to a 30× change on identical data. On the quantile task the same pattern held, most sharply where it matters: nemotron-3-ultra's *best* run (0.077) reran to 0.142, so the tight ± 0.022 band that made it look like the most reliable model was an artifact of three lucky draws, not a stable method.

Only a small minority of instances reproduced bit-for-bit (4 of 48 on the mechanism tasks, plus one quantile cell). Every one of them is a **deterministic-method collapse**: the model degenerated to a fixed computation with no free choices (a per-category linear least-squares fit on ballistic, a bare `np.percentile` on quantile) which reproduces exactly because there is nothing stochastic left. The paradox is that the only reproducible behaviour is the *worst* behaviour (the naive method the tasks are built to expose); everything a capable model does is a dice roll.

Two consequences follow. First, "method-switching" is stochastic method *sampling*, confirmed by the fact that the data is held constant. A model that fits a GPD on one run and a kitchen sink of skew-normal, Weibull and KDE on the next is not responding to the sample; it is rolling dice over its own repertoire. Second, this is itself a model-risk finding worth more than any single score: for these agentic modelling tasks, **a deployed model would hand you a materially different analysis each time you ran it on the same data**, and only a repeated-run harness makes that visible. A mean-only or single-shot leaderboard would report one of those draws as *the* number and hide the fact that the next draw is 30× worse.

## Objective Scoring, No Judge

All scoring is objective and anchored to a known target: a Winkler interval score against a Monte-Carlo predictive distribution with known parameters for the generated tasks, and pinball regret against the population itself for the quantile task. There is no LLM judge and none of the judge-agreement or judge-circularity problems that dog rubric-based evals.

The deliberate cost is that only the numeric prediction is scored, not the reasoning behind it: a model that reaches a well-calibrated answer for the wrong reason is not penalized except insofar as the flaw surfaces out of sample. Rubric scoring of methodology (did it check signs, handle the outlier, justify the transform) would need a judge and is out of scope here by choice.

## Budget Confounds

A tight message or time limit silently truncates slow or verbose models and produces penalty-scored results that misrepresent capability rather than measuring it. This has bitten this project repeatedly:

- A CCAR row for deepseek-v4-flash-free read 0.084 at message limit 120 and 0.043 at limit 300, the same eight paired instances. The first number measured the budget, not the model.
- A three-body run scored as a failure until it was re-run without a 30-minute cap, at which point it reached the reference.
- In a sandbox-free quantile pilot, a frontier model spent 63,997 of 64,000 output tokens doing regression arithmetic longhand and emitted nothing.

Limits are therefore set generously by default, actual message counts are recorded, and any row near its cap is treated as unmeasured rather than as a score.

## Metric Choice Is Not Neutral

The quantile task makes this explicit: four defensible criteria (point accuracy, point centring, interval coverage, interval score) rank the same five reference estimators in incompatible orders. A single headline number always encodes a choice about what matters. Where that choice is contestable, the alternatives are reported alongside rather than buried.

## The Overall Rank Depends on the Task Mix

The README's mean-rank column is a Borda count over the six tasks currently in the suite: four physics/mechanism tasks (ballistic, two-body, three-body, flyby) and two statistical-modelling tasks (CCAR, quantile). That is not a neutral portfolio: the physics axis carries two thirds of the votes, so the aggregate tilts toward physics-capable models.

Before reading anything into the ordering, note how little of it is resolved. Permuting the ranks within each column independently, which is the null of no cross-task skill whatsoever, reproduces the observed dispersion of mean ranks at p = 0.25 (spread) and p = 0.22 (range) over 200,000 draws. That is not significant at any conventional bar. Two structural reasons compound it. Six columns is very few votes: dropping one, as happened while the CCAR column was briefly withheld, weakens the same test to p = 0.41 and p = 0.58. And the six are not six independent axes anyway, since the rank-correlation matrix across tasks has a participation ratio of 3.1 effective dimensions, with two-body against quantile at -0.86. The fix for a weak aggregate is more tasks, not more interpretation of this one.

The tilt is also large enough to change who leads. GLM-5.1 tops the all-six ranking, but that is partly an artifact of the mix:

- **On the two statistical tasks alone, nemotron-3-ultra ranks first and GLM-5.1 falls out of the top four.**
- On the four physics tasks alone, GLM-5.1 leads and nemotron-3-ultra sinks near the bottom.
- Weighting the two axes equally (average the statistical-task ranks and the physics-task ranks, then average those) still puts GLM-5.1 first but lifts nemotron-3-ultra from fourth to third.

So the overall rank is a property of the task portfolio, not of the models in isolation. It is meaningful only relative to the stated task set, and this suite makes no claim that its mix is canonical or balanced; it is simply the tasks that exist so far. A different or larger mix would reorder the field, and the more honest reading of the matrix is the per-axis story (who is good at statistical modelling, who at physics reconstruction) rather than the single aggregate, which the mean-rank column exposes precisely by ranking three models at or below the naive baseline.
