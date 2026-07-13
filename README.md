# perEval[^1]

**An [Inspect](https://inspect.aisi.org.uk/)-based evaluation suite for quantitative model development tasks.**

> **Status: early scaffold.** Tasks and scorers are under development; nothing here is a usable benchmark yet.

## Summary

Generic coding and Q&A benchmarks don't test whether an LLM agent can *develop, estimate, and validate a statistical model*. perEval probes that corner with tasks drawn from diverse areas including credit risk and macroeconomic loss modeling.

Macro history is a single realized path (N = 1), so goodness-of-fit on real data can never be the verification target: a model that backtests well on the one path that happened proves little about the next one. Every perEval task is instead constructed so that objective verification exists *by design*: a known data-generating process planted on real covariates, a mathematical identity the solution must satisfy, a statistical guarantee whose coverage is measurable by simulation, or a planted data defect whose detection is mechanically checkable. See [docs/task-design.md](docs/task-design.md) for the full taxonomy.

Planned task themes:

- **Out-of-time discipline**: building models that must be validated on data the agent never sees, with harness-level holdout hygiene.
- **Data vintage traps**: real-time vs. revised macroeconomic series; a legitimate backtest must not use data that didn't exist yet.
- **False summits**: datasets with structural breaks, leakage, or survivorship bias where a fluent, confident, wrong analysis is the natural failure mode.

## Design Principles

1. **Hard to find, easy to verify.** Every task has an objectively checkable target (e.g., recovery of known data-generating-process parameters), not a vibes-based judge.
2. **Headroom over impossibility.** Tasks target the 20–70% frontier-model pass band, where an eval actually discriminates. Item information is p(1−p): tasks every model fails are as uninformative as tasks every model solves.
3. **Validated scorers.** Each scorer ships with its own tests: it must separate a planted-correct solution, a planted-subtly-flawed solution, and a planted-degenerate solution before it is trusted to score a model.
4. **Statistical honesty.** Repeated runs per task, paired-difference comparisons, clustered standard errors. No leaderboards with error bars the sample size can't support.

## Known Limitations and Design Decisions

This is a demonstration of eval construction, not a production benchmark. Corners deliberately cut are documented here rather than hidden.

- **Contamination.** This repo is public, so its fixed assets enter future training corpora. A production version would rely on procedural generation from known data-generating processes: fresh instances per run, public generator, no fixed answers. *(To be expanded.)*
- **Sample size.** Task count is deliberately small and narrow. Scores reported here are task-level diagnostics, not model rankings. *(To be expanded.)*
- **Judge reliability.** Where rubric scoring is unavoidable, judge-model agreement and circularity are open issues. *(To be expanded.)*

## Layout

```
pereval/            Python package: Inspect tasks and scorers
  tasks/            task definitions (@task entry points)
  scorers/          custom scorers + their validation tests
tests/              scorer and harness tests
```

## License

MIT for this repository's own code. The ballistic task depends on [py-ballisticcalc](https://github.com/o-murphy/py-ballisticcalc) (LGPL-3.0), used as an unmodified installed dependency and not redistributed here, so it imposes no obligations on this code.

-------

[^1]: *pereval* (Russian: перевал, "mountain pass"): the hard route through, not around. It also happens to end in `eval`.

