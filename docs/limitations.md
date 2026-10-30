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

Nor are they set aside. The archived CCAR runs sit in the same column as any run on the current generator, because the fix changed the answer key rather than the question: no agent was told which macros were the drivers, so the problem it faced is unchanged, and the parameter draws are centred tightly on the old calibration so the scale is preserved (oracle 0.082 against 0.070, with overlapping ranges across seed sets).

Getting there took discarding most of what had been built on top of the fix. Rotating the functional form and splitting scenario severity into baseline, adverse and severe are improvements to the task, not repairs to the defect, and enabling them by default would have stranded eight instances by eight models of paid-for measurement for no security benefit. They are opt-in. The parameter ranges were also loosened three times wider than needed, putting mean rho at 0.030 against the old fixed 0.020 and moving the oracle from 0.070 to 0.100, which rescaled the units every archived number was reported in.

One residual is accepted rather than closed. Fully suppressing the exploit needs coefficient spreads wider than the estimation error of a fit on 80 quarters, and trying that dropped the reference, handed the true drivers, to 0.52 interval coverage: a wide coefficient amplifies any standardization difference several sd out along the scenario path, and a generator whose own correctly specified reference cannot cover is not a better generator. So a model that memorized these published ranges and guessed their midpoints would edge an honest fit. That is a reduction of roughly 400x from the fixed-constant exploit and a future risk rather than a present one, since every model measured here predates this repository.

Two caveats do survive the concession. With drivers and coefficients fixed across instances, every CCAR instance posed the *same* feature-selection problem, so a good score demonstrated solving one law rather than an ability to recover a law: a narrower claim, not a wrong one. And the exposure was live for any *future* model, which is why the fix still had to happen; a fixed public law is a landmine with a delayed fuse, harmless until the first model trained after publication is tested and then silently rewarding memorization.

Separately, the old "near-oracle" reference turned out to be near-oracle partly because it was handed the answer to the feature-selection step, which is now its own measured quantity; see [tasks/ccar.md](tasks/ccar.md).

### Circular Intervals Were Rewritten by the Scorer

On the two circular tasks the scorer localized the two endpoints of a submitted interval to the branch nearest the true value **independently**, then swapped them if they came out inverted. That silently replaced the agent's interval with a different one. With a true value of 10 and a submission of `[100, 200]`, the upper endpoint wrapped to -160, the pair was swapped, and the agent was scored on `[-160, 100]`: 260 degrees wide and covering the truth it had missed by 90 degrees. The Winkler score fell from 3700 to 260, so the scorer credited coverage for an arc nobody submitted.

A submitted interval is now localized as a unit, preserving its width, by placing the midpoint of the arc from `lo` counterclockwise to `hi` on the nearest branch. Wrapping intervals such as `[350, 30]` still read as the 40-degree arc through zero, which is what an agent writing that means, and claiming the whole circle now costs the full period instead of collapsing to a point.

The guarded property is not monotonicity in width. Winkler is deliberately not monotone in width, since widening buys coverage, and on a circle growing an arc from a fixed lower endpoint brings its far end round toward the truth, so a penalty can legitimately fall. The property is that coverage is credited exactly when the true value lies on the submitted arc, checked across a grid of positions and widths.

Re-scoring the archived predictions was tried, since that would fix the column without spending anything: `scripts/rescore_threebody.py`. It identifies which `predictions.csv` was actually on disk by scoring every candidate block in a transcript with the OLD scorer and keeping the one that reproduces the recorded regret, so the identification is checked rather than guessed. Thirteen of twenty-one runs are recoverable that way, and eight of those re-score to exactly their archived value, which confirms both the extraction and the reimplementation of the superseded rule.

It is not enough to rebuild the column. Four of the six cell-defining maxima are among the eight that cannot be identified, because a transcript records the conversation and not the sandbox filesystem: an agent that writes `predictions.csv` from a script without echoing it leaves no copy to score. Seven of the eight failures are on one instance, seed 1320224556, where most agents happened to write the file silently. The naive baseline row needs no transcript at all and is unchanged at 332, since it runs host-side and can simply be recomputed.

What the recoverable runs do show is that the correction is not uniform. Claude Haiku 4.5 moves 574.7 to 1849.8 and 342.9 to 1086.2, laguna moves 889.1 to 802.2, and the rest are unchanged, so the bug bit hard on a few runs and not at all on most. deepseek's three-body penalties move 225x to 669x, from 4.5 to 3019 on one instance, but those cells are unmeasured for an unrelated reason and stay that way.

This one was not latent. Re-scoring the predictions recorded in `runs/` shows 121 affected rows and moves whole runs in both directions: nemotron-3-super's three-body instance from 2744 to 726, which was the worst cell in the summary matrix, and Claude Haiku 4.5's from 343 to 1086. The three-body column is therefore labelled as scored by a superseded scorer, on the same reasoning as the superseded CCAR generator: valid measurements under the rule that produced them, not comparable across the change. Two-body is verified unaffected, because every wide interval in its recorded runs wraps through zero with the truth inside the arc, which both the old and the new rule read identically.

Re-scoring from the archived predictions was only possible because `runs/` and `logs/` are committed. It reproduces 11 of 15 unaffected runs exactly and mismatches on 4, where an agent wrote several versions of `predictions.csv` and the transcript does not identify which one was on disk at scoring time. That is enough to establish which cells move and not enough to publish corrected values, so no corrected values are published.

### Same-Instance Stability

Every measurement in the suite varied the instance between runs, so its spread mixed instance difficulty with method instability. Those have different consequences and only one of them is the agent's fault. `-T repeats=K` now runs the agent K times per instance on byte-identical inputs and reports the worst case and the spread separately.

This is a headline number rather than a diagnostic, because it decides how far process-level evidence carries. A tight spread means the artifact in front of a validator is close to what the process reliably produces; a wide one means it is a draw, and the evidence has to be about that artifact rather than about the pipeline that emitted it.

The problem is reproducibility, not change control. Rerunning a development tool is not a model change: a model change is a change to what runs in production, and exercising a model during development or validation is not one. What instability costs is developmental evidence, which SR 26-2 puts at the centre of conceptual soundness, asking for "the quality and extent of developmental evidence" (Conceptual Soundness, in the [guidance attached to SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm)). A specification that cannot be re-derived cannot be replicated by an independent team either.

The reproducibility study below already measured this once by hand and found the spread large for capable models and near zero only for models that had collapsed to a fixed deterministic method, which is the worst behaviour the tasks exist to expose. Making it a first-class mode on every task is what turns that observation into a reportable property.

## What the Re-Run Actually Cost

Nine free runs were spent re-measuring the four `n/m` cells. One cell came back. The rest is a record of how much of an eval's effort goes into establishing that a number is not a measurement.

**nemotron-3-ultra two-body is now measured**, at a worst case of 2429. No run hit a cap (38, 36 and 66 messages against a limit of 150), and the failing instance produced nothing usable after 36 messages of genuine work, which under the rule in [task-design.md](task-design.md#anchoring-and-non-response) is capability rather than infrastructure. The row is complete, so it enters the ranking, where it lands third of seven.

**deepseek two-body failed twice, in two different ways.** At the default limit of 150 all three runs terminated exactly at the cap. Re-run at 500 all three returned two messages and no assistant turn, which the endpoint explained on a direct probe: `FreeUsageLimitError`, the free-tier quota exhausted by the earlier runs. Neither attempt is a measurement.

**deepseek Flyby is budget-limited**, which is not what it looked like at first. Two of its three runs hit the 2400 second time cap, including the one that produced no predictions after 86 messages and 31,105 output tokens of real analysis. Only the third finished clean.

Three things follow that are worth more than the cell would have been.

The rate-limit diagnosis retires the "upstream outage" reading of the July failures and replaces it with something specific: free-tier quota exhaustion, which arrives silently. Inspect recorded those samples with `error: None`, `usage: {}` and no assistant turn, so nothing in the log says the provider refused. That is precisely the condition under which a penalty gets mistaken for a score, and it is why the rule keys on cap and provider terminations rather than on whether output appeared.

A free tier cannot support the repeated-run standard. The quota that survived one three-instance task did not survive four, so measuring one model on one task can consume the budget that the next measurement needs. Any free-tier row is therefore contingent on what was run before it, which is not a property a benchmark should have.

And the one clean Flyby run is the most interesting number in the batch: 103.9 against a degenerate anchor of 112.1, the only case so far of an agent carrying more information than a constant on that task. At n=1 it is an observation, not a result, and it is recorded as one.

## Re-Measuring Three-Body

The circular scorer fix stranded that column: archived cells were produced by a rule that rewrote submitted intervals wider than half the circle, and `scripts/rescore_threebody.py` could identify only 13 of 21 archived runs, missing four of the six cell-defining maxima. The column has now been rebuilt by re-running six models, re-scoring Claude Haiku 4.5 (whose three runs all proved identifiable), and recomputing the naive baseline host-side, which returns 332 unchanged.

The re-runs move cells hard, and mostly not because of the scorer:

| Model | Archived | Re-measured |
| --- | --- | --- |
| nemotron-3-super | 2744 | **370** |
| nemotron-3-ultra | 1579 | **817** |
| Claude Haiku 4.5 | 575 | **1850** (re-scored, not re-run) |
| GLM-5.1 | 321 | **436** |
| mimo-v2.5 | 2438 | 2426 |
| ling-3.0-flash | n/a | 3309 |

nemotron-3-super improving 7.4x on byte-identical instances is not a scoring correction; it is the same run-to-run instability the reproducibility study measured, reappearing in the column that was supposed to be getting cleaner. Only Haiku's move is attributable to the scorer, because it was re-scored rather than re-run. The lesson is that re-running to fix a scoring defect also resamples the agent, so it cannot separate the two, and a column rebuilt this way inherits the instability along with the fix.

Two rows could not be brought current. laguna kept an archived value because `poolside/laguna-m.1` is no longer served in any form and only one of its three runs is identifiable, not the one that sets the cell; its row has since been dropped from the summary table, for the reason given under Dropping a Row Costs Aggregate Power below. deepseek-v4-flash-free stayed unmeasured and its row has since been dropped from the summary table, replaced by a complete row for the later `deepseek-v4-flash-0731`. That replacement does not recover the missing measurements: it is a different model version, so the old row's failures are not repaired by it, only superseded. GLM-5.1 needed a second run at 400 messages after two of three hit the 150 default, which is the budget confound catching a paid model this time.

## Cost Estimates Do Not Survive a Change of Limits

Running Kimi K3 on three tasks was estimated at $8.46 from its own archived token counts. It spent **$17.87** and returned one usable cell.

| Task | Estimated | Actual | Outcome |
| --- | --- | --- | --- |
| flyby | $2.40 | $9.98 | two of three hit the time cap; the third is valid at 8.2 |
| ballistic | $4.08 | $3.46 | clean, max 13.991 |
| three-body | $1.98 | $4.43 | died on HTTP 402, out of credit, nothing |

The correction was applied on the next paid row and worked. deepseek-v4-flash-0731 was run across all six tasks against a $2.67 balance with a guard that re-derived cost per message from **measured** spend after each task rather than from an up-front estimate, and stopped the batch if the balance fell below 1.6x the next task's projection. It never had to fire: the row cost **$1.28** against a $1.30 to $3.50 estimate. The measured rate varied from $0.00023 to $0.00124 per message across the six tasks, a 5x range within one model, which is the spread an up-front per-message estimate cannot capture and the reason the guard has to recalibrate rather than project.

The error was not in the arithmetic. Per-instance cost was treated as a property of the model and the task, and it is mostly a property of the **limits**. K3's archived flyby run used 52 messages and 55k input tokens under a 250-message cap. Re-run under a 400-message cap it used 92 to 126 messages and 980k input tokens, eighteen times the input for the same task and model.

The cap was raised deliberately, to stop a binding limit forcing a paid re-run after GLM-5.1 had just cost $3.56 that way. That reasoning inverted: raising the ceiling to avoid paying twice instead paid four times, and on flyby bought nothing at all, because the runs then grew long enough to hit the wall-clock limit and be discarded as budget-limited anyway. Both limits have to move together or neither should.

A second attempt with $15.90 applied those rules and still stopped short. At default limits Kimi K3 completed two-body ($1.10) and three-body ($7.38), then one quantile seed at $3.59 against a budget of $2 for it. The balance guard that was supposed to prevent this was set from the same discredited estimate as everything else, so it waved through a seed that could not be afforded, and stopping the run mid-seed cost $0.91 for nothing. Completing quantile needed $10.77 with $3.58 in hand. K3 finishes with five of six cells and the last $2.67 unspent, because spending it could not have produced a reportable cell.

The orbital results make the stranded budget worth recording rather than embarrassing. Three-body: 3.3 against an oracle of 0.039, 130x ahead of the next model. Flyby: 8.2 against a next-best of 292 and a degenerate answer of 138, the only model in the suite to beat a constant there, and robust to which run is quoted since the two wall-clocked runs scored 5.5 and 150.7. Those are the size of gap this suite can actually resolve. Everything finer is noise: re-running models on byte-identical instances moved cells by up to 7.4x in the same session. The one frontier model in the cast is the only one that comes close to solving the suite's hardest task, and the table cannot rank it, which is a sharper statement about this leaderboard's coverage than any of its mean ranks.

Two rules follow for any future paid run. Estimate from a run under the **same** limits, not from the archives, and treat any estimate carried across a limit change as unusable. And check the remaining balance against the estimate before each task rather than only before the batch, since the failure mode is not overspending gradually but a mid-run 402 that discards work already paid for.

## A Time-Limited Run Still Produces a Score

minimax-m3.1-flash was run on the migration task at three instances, seed 1, under `--time-limit 21600`. Two of the three instances were **cut off by that limit before the agent submitted**, and both still carry a score.

| Instance | Score | Checks failed | Messages | Terminated by |
| --- | --- | --- | --- | --- |
| 0 | 0.6291 | 1 | 470 | 6h time limit |
| 1 | 0.1078 | 0 | 479 | 6h time limit |
| 2 | 0.2284 | 1 | 234 | submitted normally |

The scorer reads the submission out of the sandbox, so a run that is killed mid-work is scored on whatever files it had already written. All three instances look complete by every artifact flag the scorer reports: `completion` 1.0, `matrix_quarters` 9, `fit_years` 20. Nothing in the score, and nothing in the reported metrics, distinguishes a finished run from a truncated one. The truncation is visible only in `sample.limit` on the eval log.

That makes instance 1 the awkward case rather than the clearly broken one. At 0.1078 with all sixteen checks passing it is the second best single result the task has produced, behind Kimi K3's 0.0885, and it is a cheap model reaching the same place by the same route: a multinomial logit whose four quarterly matrices multiply to the year's annual matrix, fit by multinomial likelihood on the annual counts. It is a real result on a run that was not allowed to finish, and whether the model would have improved it, left it alone or broken it in the next twenty messages is unknowable.

It was also close to a second wall. 479 messages against the default `message_limit` of 500, so the run had 21 messages of headroom on a limit that would have truncated it in a different way, and instance 0 had 30. Any future re-run has to move both limits, which is the rule the section above already states and this is the second instance of it.

The cost of the attempt is not small. The eval spent **122.6M total tokens**, of which 121.0M were cache reads, plus 455k reasoning tokens, 950k fresh input and 721k output, and took the full six hours. Every other model in the same batch finished three instances well inside it: ling-3.0-flash in 10m, deepseek-v4-flash-0731 in 52m, mimo-v2.5 in 1h44m. Kimi K3 took 78m for a single instance and submitted. So the limit is generous for the rest of the cast and binding for exactly one model.

**The cell will be reported with a footnote rather than re-run.** minimax's migration maximum is 0.6291, set by instance 0, one of the two truncated instances, so the figure stands on a run that was cut off. Reporting it is the conservative direction: a truncated agent had less time to improve a regret that is lower-is-better, so 0.6291 bounds its regret from above rather than flattering it. That is the same treatment footnote 6 already gives its quantile cell, where seven of nine samples were clock-bound and 0.070 is recorded as an upper bound rather than a measurement. A re-run would cost another 122.6M tokens and six hours to lower a number that is already pessimistic, which is not worth the budget. The footnote has to say which instances were truncated, that the maximum is set by one of them, and that no reported metric reveals it.

The suite is not consistent about this, though: the flyby runs recorded above were **discarded** as budget-limited when they hit the wall clock, while these were scored, because that task's wall-clock failure left nothing to read and this one's did not. Whether a time-limited run is reportable currently depends on whether the task happens to leave a readable artifact behind, which is not a decision anyone made.

## What Completing One Row Did to the Aggregate

Until Kimi K3's row was finished, the mean-rank column was indistinguishable from randomly permuting each column independently: p = 0.57 on the spread of mean ranks. Completing K3 took it to p = 0.037, and adding a complete deepseek-v4-flash-0731 row took it to p = 0.004 on the spread and p = 0.007 on the range, measured over the six columns the table then had. Adding the CECL column took the spread to p = 0.001 and the range to p = 0.016, and completing a minimax-m3.1-flash:free row took them to p < 0.0001 on the spread and p = 0.002 on the range over ten ranked rows and seven columns. Adding the migration column as the eighth takes them to **p < 0.00001 on the spread and p = 0.001 on the range**.

That is not the aggregate becoming trustworthy. Dropping rows one at a time shows where the signal lives:

| Rows tested | p (spread), seven columns | p (spread), eight columns |
| --- | ---: | ---: |
| all ten | < 0.0001 | < 0.00001 |
| without minimax-m3.1-flash | 0.0015 | 0.00011 |
| without deepseek-0731 | 0.0001 | 0.00002 |
| without Kimi K3 | 0.0003 | 0.00006 |
| without minimax and K3 | 0.052 | 0.011 |
| without all three of the top rows | 0.558 | 0.266 |

Dropping any single row leaves a detectable signal, which is a change from the six-column table where K3 carried it almost alone. **The eighth column moved the boundary by one row.** Dropping the top two used to take the spread to the edge of significance at 0.052 and now leaves it at 0.011, so deepseek-v4-flash-0731 carries detectable signal of its own rather than only the two rows above it; dropping the top three still returns the remaining seven rows to noise, though at 0.266 rather than 0.558. So the column detects that the top three models are genuinely different, not that anything below them is ranked. Read as a ranking of the seven rows beneath them, it is still noise.

Migration is also the column that most compresses the top. minimax-m3.1-flash goes from 1.71 to 2.13 and Kimi K3 from 2.71 to 2.50, cutting the gap between first and second from 1.00 to 0.38, because migration is the one column where the frontier model wins outright and minimax lands mid-field at rank 5 of 10. The aggregate's leader did not change, and the margin that made it look settled did.

Ranks are recomputed from the cells for each subset rather than deleted from a fixed rank matrix, since dropping a row re-ranks the rows beneath it. Ties are given the average of the ranks they span, which is the rule the published mean-rank column was computed with.

**One of the table's displayed ties is not a real one, and the mean ranks use the underlying cells.** The ballistic column shows Kimi K3 and deepseek-v4-flash-0731 both at 14, but the cells behind them are 13.991 and 14.135, so Kimi takes rank 4 and deepseek rank 5 rather than 4.5 each. GLM-5.1 and mimo-v2.5 both show 12 and are ranked as a genuine tie at 2.5. A reader recomputing the column from the displayed figures alone will therefore get 2.79 and 3.64 for those two rows against the published 2.71 and 3.71 on seven columns, or 2.56 and 3.69 against 2.50 and 3.75 on eight. The published numbers are the ones computed from the cells.

Mean ranks over eight columns are multiples of one eighth, or of one sixteenth where a column tie splits a rank, so eight of the eleven land exactly on a two-decimal rounding boundary: 23/8, 27/8, 37/8, 61/8, 63/8, 67/8, 69/8 and 73/8. They are rounded half up. Round half to even, the other common convention, would print four of those eight differently, giving 4.62, 7.62, 8.62 and 9.12 in place of 4.63, 7.63, 8.63 and 9.13.

The positive finding is that the suite has resolving power at the top of the range, which was not previously demonstrable. Every model measured before this clustered within a factor of a few on the orbital tasks and none beat the degenerate answer on flyby. K3 is 3.3 on three-body against a next-best of 164, and 50 on flyby against 292, beating the degenerate answer on all three of its flyby runs. Those are gaps this suite can resolve, and until now nothing had produced one.

That the same model is unremarkable on CCAR and quantile is not a limitation and not news. CCAR was built tractable on purpose, "included deliberately as a contrast to three-body", and the per-task doc has recorded since the first cast that "CCAR is tractable even for cheap models". A frontier model failing to separate on a task designed to be solvable by cheap ones is the difficulty gradient working as intended. The genuine caveat about the aggregate leaning on the physics tasks is a property of the task mix, and is covered under [The Overall Rank Depends on the Task Mix](#the-overall-rank-depends-on-the-task-mix).

## What the Eleventh Row Did to the Aggregate

Adding Claude Opus 5.5 as the eleventh ranked row moves the range of mean ranks from p = 0.001 to **p = 0.00005**. The spread cannot move, because it was already below what a million permutations can resolve at ten rows and still is, so the range is the only place an eleventh row can register, and there it moved by a factor of twenty.

The boundary between signal and noise moved by one row, which is what the eighth column had done:

| Rows tested | p (spread) | p (range) |
| --- | ---: | ---: |
| all eleven | < 0.00001 | 0.00005 |
| without Claude Opus 5.5 | < 0.00001 | 0.00098 |
| without minimax-m3.1-flash | < 0.00001 | 0.00007 |
| without Kimi K3 | < 0.00001 | 0.00014 |
| without Opus and minimax | 0.00009 | 0.0015 |
| without the top three | 0.012 | 0.025 |
| without the top four | 0.267 | 0.219 |

One million permutations for each subset, with ranks recomputed from the cells rather than deleted from a fixed rank matrix, since dropping a row re-ranks those beneath it. **No single row now carries the result**, which is a change: dropping any one of the top three leaves the range detectable, and it takes three deletions to reach the edge and four to return to noise. The seven rows beneath the top four are as unordered as they were, at p = 0.27, so the only thing the eleventh row bought is one more row above the line.

It also reopened the margin at the top that migration had closed. Adding the migration column cut the gap between first and second from 1.00 to 0.38; Opus puts it at 1.13, 1.75 against minimax-m3.1-flash's 2.88. That number is not a measure of how much better the model is, and cannot be: a rank is a placement, so beating the field by 73x on three-body and by 1.2x on CECL each contribute exactly one rank point. The gap says how often Opus placed first, not by how far, and it would read the same if every margin were a hundredth of what it is.

### The Row's Own Variance Is Larger Than the Gaps It Wins By

Three passes over the same instances, 87 samples, every one completing with no limit hit. The per-instance draws:

| Column | Instance | Pass 1 | Pass 2 | Pass 3 | spread |
| --- | --- | ---: | ---: | ---: | ---: |
| CCAR | 0 | 0.00867 | 0.00911 | 0.00672 | 1.4x |
|  | 1 | 0.00729 | 0.0127 | 0.0307 | 4.2x |
|  | 2 | 0.07 | 0.0581 | 0.0741 | 1.3x |
|  | 3 | 0.0154 | 0.0154 | 0.0117 | 1.3x |
|  | 4 | 0.0101 | 0.0114 | 0.00853 | 1.3x |
|  | 5 | 0.0152 | 0.032 | 0.0343 | 2.3x |
|  | 6 | 0.0115 | 0.0228 | 0.0224 | 2.0x |
|  | 7 | 0.0948 | 0.0586 | 0.0586 | 1.6x |
| CECL | 0 | 6.53e-07 | 8.05e-07 | 8.05e-07 | 1.2x |
|  | 1 | 4.47e-06 | 1.91e-06 | 1.87e-06 | 2.4x |
|  | 2 | 2.29e-07 | 2.29e-07 | 2.64e-07 | 1.2x |
| Migration | 0 | 0.0362 | 0.084 | 0.0365 | 2.3x |
|  | 1 | 0.0748 | 0.204 | 0.0611 | 3.3x |
|  | 2 | 0.0315 | 0.0779 | 0.0238 | 3.3x |
| Ballistic | 0 | 4.81 | 6.74 | 3.28 | 2.1x |
|  | 1 | 0.958 | 0.85 | 0.595 | 1.6x |
|  | 2 | 2.29 | 2.29 | 2.28 | 1.0x |
| Two-body | 0 | 0.00635 | 0.0862 | 0.0125 | 13.6x |
|  | 1 | 0.00822 | 0.00778 | 0.003 | 2.7x |
|  | 2 | 0.0891 | 0.0626 | 0.00447 | 19.9x |
| Three-body | 0 | 0.0388 | 0.0155 | 0.0388 | 2.5x |
|  | 1 | 0.0116 | 0.0143 | 0.0143 | 1.2x |
|  | 2 | 0.0345 | 0.0432 | 0.0345 | 1.3x |
| Flyby | 0 | 0.0163 | 0.0164 | 0.129 | 7.9x |
|  | 1 | 0.375 | 69.7 | 0.161 | 434.2x |
|  | 2 | 0.515 | 0.669 | 0.443 | 1.5x |
| Quantile | seed 1 | 0.0732 | 0.0788 | 0.0984 | 1.3x |
|  | seed 2 | 0.056 | 0.0576 | 0.0563 | 1.0x |
|  | seed 3 | 0.0561 | 0.0608 | 0.073 | 1.3x |

Read down the spread column rather than across the passes. The suite's assumption that a cell is a stable property of a model holds on CCAR, CECL, three-body and parts of ballistic, where repeat draws move by a factor of one to four, and fails on the flyby, where instance 1 moves by 434x between draws of 0.375, 69.75 and 0.161. Ballistic instance 2 is the opposite extreme: two of its three draws agree to five significant figures.

**The flyby cell is the one number in the Opus row that should not be read as a measurement.** The distribution is two-valued, not spread: eight of nine draws land under 0.67 and the ninth is 69.75. The published cell of 24 is the mean of the maximum under the matched convention, which is the right statistic for comparability and a poor description of what happened, and the two-standard-deviation band of ±66 implies a negative lower bound on a non-negative quantity. The failing draw was not truncated and did not run short of effort: it used 29 tool calls against the 13 and 10 of the two good draws, reached a mean absolute error of 4.53 against 0.34 and 0.24, and put intervals of mean width 6.1 around the wrong answer, for coverage of 0.205. That is convergence on a wrong orbit in an angles-only determination, confidently reported, and it is the failure mode this suite was built to catch.

Two defects in the row are reproducible rather than sampled, so no number of further draws will remove them:

- **Migration instance 2 fails `fail_pd_rises_as_rating_falls` in three draws of three.** Those three are the only failures among the row's 144 migration checks. The regrets on that instance are 0.031, 0.078 and 0.024, among the best in the column, so a model can lead the column and still submit a term structure whose default probability does not rise monotonically as the rating falls. A composite regret that averages four distributional distances does not see this; only the check does.
- **Ballistic instance 0 under-covers in three draws of three**, at 0.877, 0.849 and 0.875 against a nominal 0.95. It is simultaneously that column's worst cell, its widest mean interval and its worst point error in every draw, so the intervals are not too narrow, they are centred in the wrong place. Instance 2 joined it in the third pass at 0.826 while scoring 2.278, a cell indistinguishable from its other two draws, so coverage and regret are not tracking each other here.

Coverage is reported on 78 of the 87 samples, since migration has no interval metric. Sixty-six are at or above 0.931, six are below 0.90, and the six are the four listed above plus the flyby draw at 0.205 and one quantile draw at 0.890.

## Serving Provenance Is Not Controlled

A model id is not a guarantee of which weights answered. Kimi K3's row was measured across two serving paths: CCAR, ballistic, two-body and three-body on OpenRouter's paid endpoint, and flyby and quantile on tokenrouter's free `kimi-k3-free`, after the paid budget ran out. The two were compared on one matched instance, two-body instance-0, scoring 0.023 free against 0.024 paid, which is consistent with the same model but is a single comparison rather than a proof.

**Pinning the serving path was considered and rejected.** OpenRouter accepts a `provider.order` preference that would hold every instance of a row to one upstream, and it was raised twice while the migration column was being filled. It is not being adopted. It would fix one uncontrolled variable out of several and would not touch the others on this list: quantisation under the same name, a silently changed sampling default, a provider's own build drift, or the retirement of the endpoint a row was measured on. A pin would also narrow the set of servable endpoints at a time when free tiers are being withdrawn mid-column, which is the constraint that actually threatens the table. The honest position is that serving provenance is recorded per row and not controlled, rather than controlled on one axis and silently uncontrolled on four.

Nothing in the harness detects a provider silently substituting a quantized or distilled variant, changing a default sampling parameter, or routing to a different build under the same name. Cells assembled from more than one endpoint are therefore weaker evidence than cells from one, and the split is recorded per row rather than averaged away. This is a general property of evaluating through aggregators, not a defect of any particular one.

**The free tier has since collapsed, and the row labels no longer name it.** Checked on 2026-10-22 against OpenRouter's catalog and with a one-token request to each endpoint: of the five rows originally measured on a `:free` variant, `minimax/minimax-m3.1-flash:free` was retired that same day, and `inclusionai/ling-3.0-flash:free`, `xiaomi/mimo-v2.5:free` and `moonshotai/kimi-k3:free` no longer appear at all. `nvidia/nemotron-3-super-120b-a12b:free` is still listed at $0.00 but its provider answers 404, `Function not found for account`, so a catalog listing is not an availability check. `nvidia/nemotron-3-ultra-550b-a55b:free` answers a one-token probe and then returns 503 `provider_overloaded` under a real workload, which is the same failure recorded for it below.

The table therefore names models rather than endpoints. This loses nothing that was being claimed: the suffix was never a ranking axis, and the one direct comparison available, Kimi free 0.023 against paid 0.024, is consistent with the same weights. What it costs is reproducibility of the archived cells on the path that produced them, which is the same standing problem recorded in the paragraph below, now general rather than confined to one row.

**One of those two endpoints no longer exists.** As of 2026-10-19, `moonshotai/kimi-k3-free` returns 503 `model_not_found` on tokenrouter: it has been dropped from the catalog. The flyby and quantile cells in Kimi K3's row are therefore not reproducible on the path that produced them, and the single matched comparison that justified mixing the two paths cannot be repeated or extended. Nothing about those two cells changes, but their standing does: they are now an archived measurement rather than a checkable one, and the right response if they are ever disputed is to re-measure the whole row on one surviving endpoint rather than to defend the mix.

**Free tiers are a scheduling constraint as well as a provenance one.** The same probe found every tokenrouter model, including the ids that advertise themselves as free, returning 403 `insufficient_user_quota` against an account at $0.00. A free model id does not imply a servable model id, so the practical consequence is that a model can be listed, be free, and still be unusable for a row, and the surviving path has to be found by a live call rather than from a price list.

## Dropping a Row Costs Aggregate Power

laguna-m.1 was removed from the summary table when CECL was added as a seventh column. The reason is mechanical rather than editorial: the mean-rank column is a Borda count, which needs a value in every ranked row, and `poolside/laguna-m.1` is no longer listed by any provider, so its CECL cell can never be measured. The choice was between dropping the row and leaving a permanently unranked one, which removes it from the aggregate anyway.

The removal is not free, and the direction is worth stating because it is the opposite of what tidying usually implies. laguna was the bottom anchor on five of six columns, so deleting it compresses the spread of mean ranks and weakens the permutation test:

| Rows | p (spread) | p (range) |
| --- | ---: | ---: |
| ten, with laguna | 0.004 | 0.007 |
| nine, without laguna | 0.014 | 0.055 |

p on the range crosses from 0.007 to 0.055, so on that statistic the column is no longer distinguishable from chance at a conventional bar. The leave-one-out structure also shifts: on nine rows, dropping Kimi K3 gives p = 0.202 and dropping deepseek-0731 gives p = 0.079, against 0.090 and 0.037 before, so each of the top two now carries more of the remaining signal than it did.

None of this is evidence about any model. It is a property of the estimator: a rank statistic computed over a hand-assembled roster is sensitive to which rows exist, and removing a row for an availability reason changes a number that reads like a result. That is the same weakness recorded under The Overall Rank Depends on the Task Mix, appearing on the row axis rather than the column axis, and it is the strongest argument for treating the aggregate as a detector of outliers rather than a ranking.

The archived laguna measurements are kept in the per-task documents. Only its summary row is gone.

## The Transcript Archive Was Hollow

Every reported number in this repository is auditable from `runs/`, which is the point of saving a markdown transcript for each sample rather than only a score. For most of the project's life that archive was missing the thing it exists to preserve.

`scripts/save_transcript.py` read a tool call's body from `code`, `cmd` or `answer`. Inspect's own `bash()` and `python()` tools name that argument `command`, which was not on the list, and the lookup fell through to the empty string without complaint. In one migration run, 259 of 281 calls archived as an empty code block. Swept across the whole archive, **291 of 365 transcripts** were affected, on every task. What survived was each model's reasoning with the work it actually did deleted, which reads as a complete record and is not one.

The defect was found by trying to answer a question the archive was supposed to answer, namely which modelling approaches the agents used, and discovering the answer had to be rebuilt from the `.eval` logs instead.

| | transcripts |
| --- | ---: |
| reserialized from a surviving log | 151 |
| already complete | 41 |
| still hollow, source log deleted | 144 |

The 151 were overwritten in place rather than saved as a new generation, which is a deliberate exception to the no-clobber rule in that script. The rule exists because model, task, instance and seed identify a cell and not a run, so re-saving could destroy the record of a different attempt. That risk does not apply when the input is the same `.eval` file and the output differs only by containing more of it; each rewrite was matched to its log by comparing content with tool bodies blanked, not by trusting the filename. The repaired files grew from 20.0M to 24.6M, so about a fifth of each run had been missing.

The 144 that remain are unrecoverable, and they are concentrated in the older tasks: 39 CCAR, 26 quantile, 22 ballistic, 19 two-body, 19 flyby, 18 three-body, 1 CECL. No migration transcript is among them. For those cells the archived reasoning is all there is, and a claim about what the agent computed cannot be checked against the code it ran.

## The Flyby Task Discarded Its Repeats Argument

`pereval/tasks/orbit/task.py@hyperbolic` accepted `-T repeats=3` and built its `Task` without `epochs`. Two-body and three-body get theirs from a shared `_build` helper; the flyby constructs its own `Task` and omitted the line, so the argument was accepted, documented in its own docstring, and then thrown away.

The failure was silent in every channel a run reports through. The dataset was the right length for a single draw, the eval finished with `status: success`, and the stability reducer still emitted `runs` and `regret_spread` from one score each, so the summary read `runs 1.000, regret_spread 0.000`. A spread of zero is the signature of a model that has collapsed to a deterministic method, which is the worst behaviour these tasks exist to expose, and here it meant the opposite: nothing had been repeated at all. The only unambiguous witness is `eval.config.epochs` in the log header, which read 1 where the three completed runs beside it read 3.

It cost a seven hour run, 363M tokens, five samples that are valid single draws and void as a cell. No archived number is affected, because no flyby cell in this repository was ever measured with `repeats`: the column was always three separate instances at one draw each, which is the convention discussed in the next section. The regression test is a cross-task invariant rather than a test of this task, since the defect was a task building its own `Task` and forgetting a shared argument, and nothing stops the next task from doing the same.

## The Worst Case Needs the Same Sample Count in Every Row of a Column

Nothing in the scores table is compared across columns, and it says so: the cells are not commensurable and the mean rank is a Borda count computed within each column. So a difference in how two columns were measured costs nothing. A difference between two rows of the **same** column is the whole ranking.

That is what the MiniMax row introduced. The table's rule is the worst-case regret over at least three runs, which is not a definition, because the maximum of a heavy-tailed sample grows with the size of the sample. Every archived row in the mechanism columns is the maximum over **three samples**, three instances at one draw each, which is what the per-task docs mean by their `runs` column; CCAR's is the maximum over eight, one per instance. The MiniMax row was measured with `-T repeats=3` on five instances, so its maximum is over fifteen, and twenty four on CCAR. Same rule, three to eight times the exposure, and the bias runs one way.

Three draws per instance are enough to measure the size of it, because the old convention can be reconstructed from the new measurement: average the maximum over one draw per instance across every combination of draws, and the result estimates what a three-sample run would have produced.

| | over every sample | three-sample convention | ratio | samples |
| --- | ---: | ---: | ---: | ---: |
| CCAR | 0.0910 | 0.0802 | 1.13 | 24 |
| CECL | 1.16e-05 | 6.53e-06 | 1.78 | 9 |
| Ballistic | 11.04 | 4.31 | 2.56 | 15 |
| Two-body | 0.1017 | 0.0694 | 1.47 | 15 |
| Three-body | 361.2 | 164.2 | 2.20 | 15 |
| Flyby | 1891 | 361.2 | 5.24 | 15 |
| Quantile | 0.0756 | 0.0699 | 1.08 | 9 |

The size of the correction is not uniform and is not predictable from the column: it runs from 1.08 on quantile, where the three draws of an instance sit within a few percent of each other, to 5.24 on the flyby, where one instance returned 1891 on its second draw against 367 and 271 on its other two, and a second instance spread 648, 88 and 101 across its three.

Two columns would have been ranked wrongly. On two-body the raw maximum sits third in the column behind GLM-5.1 and Kimi K3, and the matched cell is first ahead of both. On the flyby the raw 1891 would have placed ninth of ten ranked rows, worse than every model but the naive baseline, where the matched 361 places third. A rank inversion caused by sample count alone is not a caveat, it is a wrong answer, and it lands in the mean rank because the Borda count is within-column.

**So the cells are published on the three-sample convention, matched to the rows they sit beside, with the raw count and the full-sample maximum in the row's footnote.** The alternative, publishing the fifteen-sample maximum because the stated rule technically permits it, would have been a measurement artifact dressed as a result. The repeated draws are not wasted: they are what makes the correction possible and what the `regret_spread` column reports.

The quantile column needed more than a rescaling. Its archived runs are three separate evals at `-T n_instances=1` on base seeds 1, 2 and 3, which the ids in `runs/` confirm: `quantile-0-seed-1835504127`, `-2834126987` and `-1576890651` are the first instance of `SeedSequence(1)`, `(2)` and `(3)`. A run at `-T n_instances=8` on base seed 1 draws eight instances of which exactly one is in that set, so it is not an over-sampled version of the column, it is a different population. It was relaunched as three one-sample runs on the archived seeds, which completed 9 of 9 and produced the matched cell above. The eight-instance design is the better one and a future column should use it, but it cannot be mixed into this one.

That relaunch cost the comparison something else. All three runs were given a four-hour per-sample wall clock, and seven of the nine samples hit it, including the one that sets the raw maximum, whereas none of the archived quantile runs was clock-bound: their limits were 7200, 36000, 72000 and 108000 seconds and no sample reached them. So the quantile cell is an upper bound on this model's regret rather than a measurement of it, and it is the one cell in the row whose caveat is about the budget rather than the sample count. The flyby needs no such note: it time-capped three of fifteen samples and archived flyby rows time-capped too, and the sample that sets its raw maximum ran to completion.

The general repair is to re-measure the whole table at a fixed instance count and a fixed draw count, which is ten models by seven tasks and is not affordable here. Until then the rule in the table header carries its sample count explicitly, so a row measured any other way is visibly a different statistic rather than silently one.

## A Lookahead Is Left in Place in the CCAR Macro Columns

The CCAR generator builds `sp500` and `djia` by standardising NASDAQ returns, and that standardisation runs over the whole simulated path, stress window included. So the severity of the future scenario sets the scale of two macro columns throughout the published history. Holding the seed and changing only the scenario label moves 49 of 80 history rows.

It is a lookahead defect: a published historical series depends on data from after the history ends. Nothing in the CCAR task can exploit it, because an instance there carries one scenario and an agent has nothing to compare against, and the two columns are collinear distractors rather than drivers of the response law. But it is the kind of thing that, found in a bank's feature pipeline, would be a finding regardless of whether anyone could trade on it.

It is fixed only where it bites. The migration task publishes one history alongside three scenario paths, and there the defect is a contradiction rather than an inefficiency: the three would disagree about the past, and the size of the discontinuity at the join would encode the severity. `_simulate` therefore takes a `sibling_ref` argument and migration passes `pre_stress`, while the default stays at the whole-path behaviour.

The reason the default stays is archive preservation, not a judgement that the lookahead is acceptable. Flipping it moves two published columns on every archived CCAR instance, which would void the completed CCAR column of the README table and buy that task nothing. The cost of that choice is that a reader of CCAR's macro history is reading a file with a known defect in two of its nine columns, and that this page is the only place saying so.

## Contamination

The repo is public, so anything fixed in it can enter training corpora. The four generated tasks (CCAR, ballistic, orbital) therefore draw fresh instances per run from a seeded, public generator with per-run randomized parameters (orbital elements, ballistic loads, macro draws, and the CCAR response law including which macros drive it), so there are no fixed answers to memorize and every score is computed against freshly drawn ground truth. The residual exposure is structural: a model could learn the generator's functional form from the source. That is largely defanged by design, because knowing the form does not reveal an instance's parameters, which must still be estimated from the provided data, which is the task itself.

That argument is only as good as its weakest task, and it was false for CCAR until the response law was randomized; see [The CCAR Response Law Was Public](#the-ccar-response-law-was-public) above. The lesson generalizes: this defense has to be re-checked per task rather than asserted for the suite, because it fails silently. Nothing about the fixed-constant CCAR task looked wrong from the outside, and its scores were plausible.

The quantile task is the exception and needs its own argument, because its data is real and public. It relies on a randomized observation window (the population quantile of an undisclosed span is not recallable even if the series is recognized), an independent random scale factor per block, and reduced precision. See [tasks/quantile.md](tasks/quantile.md).

## Sample Size

Every score table reports at least three runs per model as mean ± 2 SD, after the repeated-run standard was adopted, and no longer reports any cell whose runs did not all complete. The bands are still wide relative to the mean gaps (regret is heavy-right-tailed), so only coarse contrasts are established: the reference at the top, the models that fall through the naive baseline at the bottom, and the two-axis statistical-vs-physics split. Mid-field orderings are not resolved at n=3. The aggregate rank is now distinguishable from chance (permutation p < 0.00001 on the spread of mean ranks over eight columns), but only because the top four rows separate from the field; the ordering beneath them remains unresolved, as the leave-one-out table under [What the Eleventh Row Did to the Aggregate](#what-the-eleventh-row-did-to-the-aggregate) shows. Paired-difference comparison, the standard remedy and the one this project's own design doc prescribes, was measured and does not help here: 1% variance reduction on regret levels and 10% on logs, because the variance is model-by-instance interaction rather than instance difficulty. See [task-design.md](task-design.md#pairing-is-not-the-lever), and the next honest step is tens of instances with the paired, task-clustered error analysis described in [task-design.md](task-design.md).

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

"Generously" was aspirational until it was measured. The original defaults (150 for ballistic, two-body, three-body and CCAR, 250 for flyby, 300 for quantile) bound on five separate occasions: deepseek on two-body, GLM-5.1 on three-body, deepseek on CCAR, and Kimi K3 on both flyby and quantile. Three of those wasted paid API credit on runs that were then discarded and had to be bought again.

The raised defaults then bound once more, which is the useful part of the story. deepseek-v4-flash-0731 hit the new 500-message three-body ceiling on one instance of three. Re-run at 1200 the same model on the same instance finished in **190 messages**, well under even the old 500, and scored 269 rather than the truncated 340. So the cap was not binding on the work the task requires; it was binding on one run that had gone into a loop, and the re-run did not go into it. That is the same pattern as Kimi K3's quantile seed, which finished in 39 messages under a raised ceiling after hitting 300 under the old one. The lesson is not that these tasks need ever larger budgets. It is that message count is dominated by which path a run happens to take, so a cap set near the typical run silently converts a bad draw into a bad score, and a cap set far above it costs nothing on the runs that never approach it.

The defaults are set from the observed distribution rather than guessed, at between three and nine times the p90. The table counts only **natural stopping points**: runs that ended on their own, excluding runs that hit a message or wall-clock limit, whose message count measures the limit rather than the work, and excluding upstream non-responses of two messages or fewer. The recipe is stated explicitly because an earlier version of this table could not be reproduced from the archive, and a figure nobody can recompute is not evidence.

| Task | runs | median | p90 | max | new default |
| --- | --- | --- | --- | --- | --- |
| ballistic | 66 | 31 | 54 | 114 | 500 |
| two-body | 59 | 32 | 56 | 76 | 500 |
| three-body | 34 | 72 | 130 | 190 | 500 |
| flyby | 13 | 64 | 171 | 194 | 600 |
| quantile | 10 | 42 | 110 | 250 | 800 |
| CCAR | 59 | 42 | 145 | 189 | 500 |

The excluded population is the more informative one. 23 of 57 three-body runs and 22 of 88 ballistic runs ended at a limit, most of them at the low experimental ceilings used early on, and a further 16 ballistic and 19 two-body samples were upstream non-responses that never produced a message count at all. The largest natural stopping point anywhere in the archive is the 190-message three-body run described above, which is why 500 is not a tight ceiling on any task.

The asymmetry is what makes this close to free. A ceiling costs nothing for a model that stops on its own, which is most of them: raising it does not make a 43-message ballistic run any longer. It only binds on the runs that would otherwise be truncated, and a truncated run costs nearly as much as a completed one while yielding nothing at all. Running long is a wall-clock problem; hitting a cap is a wasted measurement.

Two riders. The wall-clock limit has to move with the message limit or the failure simply relocates, which is exactly what happened when K3's flyby ceiling went to 400 without touching the clock and two of three runs were then discarded on time instead. And archived rows whose runs came close to their old caps, notably GLM-5.1's three-body at 140 of 150, may improve under the new ceiling for budget reasons rather than capability ones; message counts are recorded per run so that can be checked rather than assumed.

## Metric Choice Is Not Neutral

The quantile task makes this explicit: four defensible criteria (point accuracy, point centring, interval coverage, interval score) rank the same five reference estimators in incompatible orders. A single headline number always encodes a choice about what matters. Where that choice is contestable, the alternatives are reported alongside rather than buried.

## The Overall Rank Depends on the Task Mix

The README's mean-rank column is a Borda count over the seven tasks currently in the suite: four physics/mechanism tasks (ballistic, two-body, three-body, flyby) and three statistical-modelling tasks (CCAR, quantile, CECL). That is not a neutral portfolio: the physics axis still carries the majority of the votes, so the aggregate tilts toward physics-capable models, though adding CECL moved the balance from four against two to four against three.
Adding CECL as a seventh column also recovered the significance that dropping laguna cost, which is worth recording because the two changes landed together and could otherwise be confused. On six columns the nine remaining rows gave p = 0.014 on the spread and p = 0.055 on the range. On seven columns they give p = 0.001 and p = 0.016. So the column count and the row count both move this statistic materially, in opposite directions here, which is the same point as the section above: the number responds to the shape of the roster at least as much as to the models in it.


Permuting the ranks within each column independently, the null of no cross-task skill, now reproduces the observed dispersion at p = 0.004 (spread) and p = 0.007 (range). That clears a conventional bar, but it establishes only that the top of the column is real. Six columns remains very few votes, and the six are not six independent axes: the rank-correlation matrix has a participation ratio of 3.5 effective dimensions. The fix for a weak aggregate is more tasks, not more interpretation of this one.

The tilt no longer changes who leads, which is itself a change: Kimi K3 is first on all six, first on the two statistical tasks and first on the four physics tasks, so its position does not depend on the mix. Below it the mix reorders the field substantially:

- **ling-3.0-flash is 2nd of ten on the statistical tasks and 8th on the physics tasks.** nemotron-3-ultra shows the same split, 4th against 9th.
- mimo-v2.5 runs the other way, 4th on physics and 8th on statistical, as does GLM-5.1, 2nd against 5th.
- Weighting the two axes equally rather than by column count moves GLM-5.1 from 3rd to 3rd but lifts ling from 5th to 4th and drops mimo from 4th to 6th.

So the overall rank is a property of the task portfolio, not of the models in isolation. It is meaningful only relative to the stated task set, and this suite makes no claim that its mix is canonical or balanced; it is simply the tasks that exist so far. A different or larger mix would reorder the field, and the more honest reading of the matrix is the per-axis story (who is good at statistical modelling, who at physics reconstruction) rather than the single aggregate, which the mean-rank column exposes precisely by ranking two models below the naive baseline.
