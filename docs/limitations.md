# Known Limitations and Design Decisions

This is a demonstration of eval construction, not a production benchmark.
Corners deliberately cut are documented here rather than hidden.

## Contamination

The repo is public, so anything fixed in it can enter training corpora. The four generated tasks (CCAR, ballistic, orbital) therefore draw fresh instances per run from a seeded, public generator with per-run randomized parameters (orbital elements, ballistic loads, macro and Vasicek draws), so there are no fixed answers to memorize and every score is computed against freshly drawn ground truth. The residual exposure is structural: a model could learn the generator's functional form from the source. That is largely defanged by design, because knowing the form does not reveal an instance's parameters, which must still be estimated from the provided data, which is the task itself.

The quantile task is the exception and needs its own argument, because its data is real and public. It relies on a randomized observation window (the population quantile of an undisclosed span is not recallable even if the series is recognized), an independent random scale factor per block, and reduced precision. See [tasks/quantile.md](tasks/quantile.md).

## Sample Size

Most example-score tables are single-instance (N = 1) harness checks, not model rankings, and are labeled as such. The exception is CCAR, which reports eight paired instances with standard errors.

The harness already supports the honest version: `-T n_instances=N` draws many fresh instances and the scorer emits per-metric means with standard errors. A real comparison would run tens of instances per model with the paired, instance-matched, task-clustered error analysis described in [task-design.md](task-design.md); the mid-field orderings shown are explicitly not robust to that.

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
