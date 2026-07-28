# Known Limitations and Design Decisions

This is a demonstration of eval construction, not a production benchmark.
Corners deliberately cut are documented here rather than hidden.

## Contamination

The repo is public, so anything fixed in it can enter training corpora. The four generated tasks (CCAR, ballistic, orbital) therefore draw fresh instances per run from a seeded, public generator with per-run randomized parameters (orbital elements, ballistic loads, macro and Vasicek draws), so there are no fixed answers to memorize and every score is computed against freshly drawn ground truth. The residual exposure is structural: a model could learn the generator's functional form from the source. That is largely defanged by design, because knowing the form does not reveal an instance's parameters, which must still be estimated from the provided data, which is the task itself.

The quantile task is the exception and needs its own argument, because its data is real and public. It relies on a randomized observation window (the population quantile of an undisclosed span is not recallable even if the series is recognized), an independent random scale factor per block, and reduced precision. See [tasks/quantile.md](tasks/quantile.md).

## Sample Size

Every score table now reports at least three runs per model — CCAR over eight instances, the other tasks over three — as mean ± 2 SD, after the repeated-run standard was adopted. Single-run exploratory results are quarantined in the per-task docs' provisional sections. The bands are still wide relative to the mean gaps (regret is heavy-right-tailed), so only coarse contrasts are established: the reference at the top, the models that fall through the naive baseline at the bottom, and the two-axis statistical-vs-physics split. Mid-field orderings are not resolved at n=3, and the next honest step is tens of instances with the paired, task-clustered error analysis described in [task-design.md](task-design.md).

## Run-to-Run Reproducibility

The reason three runs is a floor rather than a nicety: **on this suite an LLM agent's score is dominated by sampling temperature, not by the data.** A controlled experiment reran four free models on byte-identical inputs — the same seeds, the same generated instances, a second time — and compared each cell to its first run.

The results barely reproduce. Of 48 paired mechanism-task instances, **37 (77%) differed materially on the rerun**, and the swings are enormous: nemotron-3-super's three-body score went 2744 → 133, mimo's flyby went 89 → 2601, nemotron-3-ultra's three-body went 1579 → 3726 — up to a 30× change on identical data. On the quantile task the same pattern held, most sharply where it matters: nemotron-3-ultra's *best* run (0.077) reran to 0.142, so the tight ± 0.022 band that made it look like the most reliable model was an artifact of three lucky draws, not a stable method.

Only a small minority of instances reproduced bit-for-bit — 4 of 48 on the mechanism tasks, plus one quantile cell. Every one of them is a **deterministic-method collapse**: the model degenerated to a fixed computation with no free choices — a per-category linear least-squares fit on ballistic, a bare `np.percentile` (Hyndman-Fan type 7) on quantile — which reproduces exactly because there is nothing stochastic left. The paradox is that the only reproducible behaviour is the *worst* behaviour (the naive method the tasks are built to expose); everything a capable model does is a dice roll.

Two consequences follow. First, "method-switching" is not the model reading the data and choosing an approach — it is stochastic method *sampling*, confirmed by the fact that the data is held constant. A model that fits a GPD on one run and a kitchen sink of skew-normal, Weibull and KDE on the next is not responding to the sample; it is rolling dice over its own repertoire. Second, this is itself a model-risk finding worth more than any single score: for these agentic modelling tasks, **a deployed model would hand you a materially different analysis each time you ran it on the same data**, and only a repeated-run harness makes that visible. A mean-only or single-shot leaderboard would report one of those draws as *the* number and hide the fact that the next draw is 30× worse.

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
