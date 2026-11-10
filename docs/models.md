# Row Provenance

Everything about *how a row was measured* rather than *what a task asks*. The README's table carries the numbers; this file carries the conditions they were produced under, the places where one row's convention differs from another's, and the individual cells that need a caveat.

Task-level scoring definitions live with the tasks: [CECL](tasks/cecl.md), [migration](tasks/migration.md), [quantile](tasks/quantile.md), [orbital](tasks/orbital.md). The two local rows are in [local-models.md](local-models.md). Known defects and unresolved questions are in [limitations.md](limitations.md).

## Conventions That Apply To Every Row

Each cell is the **worst-case (maximum) regret** over at least three runs, CCAR over eight instances. Lower is better everywhere.

A cell is reported only if none of its runs failed for reasons outside the agent's control. Two columns of the gemma row are a recorded exception to that rule, documented in [local-models.md](local-models.md).

The **mean rank** column is a Borda count within each column. It is the only aggregate, because the cells are not comparable across columns. Note that the published mean ranks cannot be recomputed from the table's rounded cells: GLM-5.1's and mimo-v2.5's unrounded ballistic cells are not recoverable from this repository's logs, and the resulting three-way tie at 12 was broken pessimistically by hand. When a row is added, existing rows are incremented rather than re-ranked, which preserves that hand resolution.

Row labels name the model, not the endpoint that served it. A `:free` variant is the same weights under a different serving tier, and where the two have been compared directly they agree: Kimi K3 scored 0.023 free against 0.024 paid on one matched instance. Most of the free endpoints these rows were originally measured on have since been retired, so a cell is reproducible on the paid path and not on the one that produced it ([detail](limitations.md#serving-provenance-is-not-controlled)).

### The Matched Convention

Two rows, minimax-m3.1-flash and Claude Opus 5.5, were measured with three draws per instance rather than one. A maximum over their raw samples would be taken over fifteen or twenty four draws rather than three, which is not the same statistic as the archived cells. Both are therefore reported as **the mean, over every way of drawing one sample per instance, of the maximum across the same instances the other rows use**: three for the orbital, ballistic and CECL columns, eight for CCAR, and for quantile three paired single-instance runs on the archived seeds. Migration is three instances for Opus and outside the convention for minimax, noted below.

Spreads for these rows are reported as **median (worst)**, not as a mean with a band, for the reason given in [limitations.md](limitations.md#three-runs-cannot-support-a-two-sd-band). The median is the median of the same combination distribution the cell averages, so it does not depend on which draw is labelled which pass.

## Claude Opus 5.5

Three passes over the archived instances at `epochs=1` on the same seeds, 29 problems per pass and 87 samples in all, every sample completing and none hitting a limit, for $18.36. Reported on the matched convention above.

Spread across the three passes, as median (worst), in column order: CCAR 0.074 (0.095), CECL 1.91e-06 (4.47e-06), migration 0.075 (0.204), ballistic 4.81 (6.74), two-body 0.086 (0.089), three-body 0.0388 (0.0432), flyby 0.67 (70), quantile 0.079 (0.098). The three per-pass maxima behind them, in pass order, are CCAR 0.095 / 0.059 / 0.074, CECL 4.47e-06 / 1.91e-06 / 1.87e-06, migration 0.075 / 0.204 / 0.061, ballistic 4.81 / 6.74 / 3.28, two-body 0.089 / 0.086 / 0.013, three-body 0.0388 / 0.0432 / 0.0388, flyby 0.52 / 69.75 / 0.44, quantile 0.073 / 0.079 / 0.098.

**The variance across passes is the finding.** The row takes five of eight columns and the aggregate, loses CCAR and ballistic narrowly, and loses quantile outright. Judged on its worst pass rather than its mean, which is the pessimistic reading this suite is built around, only three of those five leads survive: three-body at 0.0432 against 3.3, CECL at 4.47e-06 against 6.5e-06, and migration at 0.204 against 0.301, so a 76x margin and two of roughly 1.5x measured on three instances.

The columns are not one distribution. Three-body is the most stable cell the suite has measured, three pass maxima of 0.0388, 0.0432 and 0.0388. The flyby spans 434x on a single instance, 0.375 then 69.75 then 0.161, with no limit hit in any of the three. Averaging that into one cell is the table's convention and not a description of it: eight of the nine flyby draws land under 0.67 and the ninth is 69.75, which is a model that usually solves the task rather than one that solves it, and the failing draw spent 29 tool calls against the 13 and 10 of the other two.

**Two defects are reproducible rather than sampled.** Migration instance 2 fails `fail_pd_rises_as_rating_falls` in three draws of three, and those are the only three of the row's 144 migration checks to fail. Ballistic instance 0 under-covers in three of three, at 0.877, 0.849 and 0.875, and it is simultaneously that column's worst cell, widest interval and worst point error, so it is off-centre rather than narrow. Coverage is reported on 78 of the 87 samples, 66 of them at or above 0.931 against a nominal 0.95 and six below 0.90.

Two deviations from the archived convention were applied to every column: `--max-tokens 24000`, because thinking is always on and counts against that limit, and `--token-limit 5000000` as a cost guard rather than a context guard. This is the only row served by a first-party endpoint rather than an aggregator, so the serving caveat above does not apply to it, and that is not evidence the others are wrong.

## minimax-m3.1-flash

Three draws per instance, reported on the matched convention above. Its as-measured maxima over all draws are higher, and are CCAR 0.091, CECL 1.2e-05, ballistic 11, two-body 0.102, three-body 361, flyby 1891 and quantile 0.076. Those range over all five orbital instances, two of which are outside the convention.

On the archived instances alone the spread reads, as median (worst), CCAR 0.090 (0.091), CECL 4.33e-06 (1.16e-05), ballistic 4.49 (4.64), two-body 0.085 (0.102), three-body 108 (361), flyby 388 (648) and quantile 0.068 (0.076). Migration has one draw per instance and so has no spread to report. No sample errored in any column.

**Its quantile row is weaker evidence than the rest.** Seven of its nine samples hit the four-hour wall clock, including the one that sets the as-measured maximum, while no archived quantile run was clock-bound, so 0.070 is an upper bound on its regret rather than a measurement of it. Its flyby run time-capped three of fifteen samples, as archived flyby rows also did, and the sample that sets the as-measured 1891 ran to completion uncapped.

**Its migration cell is outside the matched convention**, because that run took one draw per instance like every other row: it is a plain maximum over the same three instances. 0.629 is weaker evidence for a different reason. Two of its three instances were cut off by the six-hour wall clock before submitting, instance 0 at 470 messages and instance 1 at 479, and the cell is set by instance 0. Truncation can only have denied a lower-is-better regret more time to improve, so 0.629 bounds its regret from above. Nothing the scorer reports distinguishes a truncated run from a finished one here, since `completion`, `matrix_quarters` and `fit_years` all read as complete on all three; only `sample.limit` on the eval log shows it ([detail](limitations.md#a-time-limited-run-still-produces-a-score)).

**This row is two serving paths and the split was not recorded before.** Its migration cell comes from the paid `minimax/minimax-m3.1-flash` endpoint on 2026-10-22, the day `:free` was retired, while its seven other cells come from `:free`. Two further migration runs exist on the free path, and neither is a substitute for the published cell, because both predate the task revision the whole column was measured under. A three-draw run on 2026-10-21 has a matched-convention cell of 0.456 and a spread of 0.487 (0.634), but its system prompt is 739 characters shorter than the one every published cell was measured under: it asks for the 189 rows of `matrices.csv` covering the three scenarios and not the 329 that also carry twenty fitted historical years, and it does not state the quarter numbering, because the macro files it served still ran 1 to 80 and 81 to 89 rather than relative to the projection. It also ran under a four-hour limit rather than six. A single-draw run on 2026-10-19 scoring 0.558 is three task revisions further back again and on differently named instances. The two scorer commits in between left the headline `score` untouched, so neither figure is wrong; neither is a cell in this column ([detail](limitations.md#a-time-limited-run-still-produces-a-score)).

## gpt-6-luna

Measured on the archived convention, one draw per instance over the same instances every other row uses, so its cells are plain maxima and need no matched-convention adjustment. One pass, eight columns, 29 samples, every sample completing at `status=success` and none errored, 3h31m of wall clock for 38.4M tokens. Four samples hit the task message limit of 500 (CECL instances 0 and 2, CCAR instance 1, migration instance 1) and **none of them sets its column's cell**, so no number in this row rests on a truncated run.

**The flyby cell is the row's only genuinely good result, and it is good in a different way from Opus.** 45 against Opus's 24 makes it one of three rows inside the degenerate answer's 138 in the column where nine of fourteen are worse than a constant, and its three instances read 30.4, 15.7 and 44.8 where Opus's three draws of one instance read 0.52, 70 and 0.44. Opus usually solves the flyby and occasionally fails it outright; this row never does either. The mechanism is visible in the diagnostics: coverage 1.0, 0.9996 and 1.0 against mean widths of 32, 20 and 49 and point errors of 6.8, 4.7 and 4.7, so it buys coverage with width rather than accuracy, which is what keeps it mid-column rather than near the oracle's 0.31.

**Its migration cell is worse than the degenerate answer, and not because it ran out of room.** 1.094 is set by instance 0, which submitted after 23 messages with no limit hit, while instance 1 ran into the 500-message limit and scored 0.309 and instance 2 scored 0.202 in 56 messages. The worst cell in the column's weakest group is the instance the agent tried least on, which is a different failure from the truncation that bounds minimax's 0.629 from above.

**Its three-body cell is worse than the naive harmonic fit**, 408 against 332, driven by instance 2 narrowing to a width of 31.6 at coverage 0.656.

**Its CECL cell is one instance of three, not a weak column.** 0.00057 comes entirely from instance 1, the adverse pool, at coverage 0.686; instances 0 and 2 scored 1.6e-05 and 2.7e-07, the latter the lowest single-instance CECL figure measured anywhere in this suite. A maximum convention is the right way to report that and a poor way to describe it.

**Its ballistic instance 0 is a reproducible defect rather than a sampled one.** Two independent runs ninety minutes apart returned `winkler_regret` 12.365336039551813 and 12.365336039551858 with identical coverage of 0.285 in 20 messages each, differing only in the last bits of floating-point accumulation, which is the same shape as the Opus row's under-coverage on that instance in three of three.

**One rank in this row is not determined.** Its ballistic 12.37 falls inside the three-way tie at 12 with GLM-5.1 and mimo-v2.5, whose unrounded cells are not recoverable from this repository's logs ([detail](limitations.md#serving-provenance-is-not-controlled)); the rank used here is the pessimistic 5, and if 12.37 in fact beats both then this row's ballistic rank is 3 and its mean rank 6.13 rather than 6.38.

Served by the OpenCode Go subscription at provider default sampling, with a custom `user-agent` and a per-conversation `x-opencode-session` header, which that endpoint requires of direct callers. Cost is metered rather than estimated, from the provider's own `/inference/go/v1/usage` endpoint: the pass moved the rolling five-hour window from 0 to 25 percent, the weekly from 15 to 25 and the monthly from 57 to 62, so a full eight-column row is about five points of a monthly allowance.

## Kimi K3

The only frontier model here and not the only paid one, since Claude Haiku 4.5 is also paid. Its cells come from two serving endpoints, compared on one matched instance ([detail](limitations.md#serving-provenance-is-not-controlled)).

## deepseek-v4-flash-0731

Replaces deepseek-v4-flash-free, a different and now-superseded model version whose row had three unmeasured cells. It beats the degenerate constant on every run of every task except two of three on the flyby ([detail](limitations.md#budget-confounds)).

## Qwen3.6-35B-A3B and gemma-4-26B-A4B

Both local rows, served from one 48 GB Mac Mini rather than a hosted provider. Their weights, serving configuration, decoder settings and per-cell caveats are in [local-models.md](local-models.md).
