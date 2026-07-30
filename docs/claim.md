# perEval Claim

Instead of validating a specific model, perEval qualifies a model *development process* by
running that process on problems where the answer is known and measuring regret against
it. This page states the claim it supports, the claims it does not, and how its coverage
maps onto supervisory expectations.

## The N = 1 Problem

A nine-quarter stress projection cannot be validated against outcomes. The actuals arrive
nine quarters late and only along the one macro path that actually happened, which is not
the scenario path the model was asked about. The usable history was consumed in
development. There is one realized macro path, so backtesting on it, however the holdout
is carved, measures fit to a single draw and cannot separate a sound model from a lucky
one. This is the N = 1 problem, and it is the founding constraint of the whole suite; see
[task-design.md](task-design.md).

SR 26-2 defines outcomes analysis as comparing "model outputs to corresponding real-world
outcomes" and notes that the approach "depends on the model's objectives, methodology, and
data availability" (Model Validation and Monitoring, in the guidance attached to
[SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm)). For a
stress projection the corresponding real-world outcome does not exist and never will.

So the object that can be tested is not the model but the process that produced it. The
guidance's own words for the target are close: "When a model's design relies substantially
on expert judgment, quantitative outcomes analysis helps to evaluate the quality of that
judgment."

## Independence Across Runs

Process validation of a human modeller was difficult and expensive rather than impossible.
Independent replication by a second team can discover discrepancies between model
documentation and code, but not necessarily conceptual errors. Some information sharing
between the developers of champion and challenger models is inevitable, so challenger
models are not completely independent and might share weaknesses. Human model developers
remember. Asked to repeat a task, their second attempt is anchored on the first, so it is
not an independent draw. A developer qualification review is necessarily subjective.

What is new when the developer is an LLM agent is the ability to run the entire model
development process multiple times with no information sharing between runs.

## Interpreting the Results

The outcome is a claim about the **distribution of outputs** an LLM agent produces on
problems of these families, at the sample size actually run.

That is weaker than the statement "this agent's models can be trusted", and this project's
own measurements quantify it. The same agent on byte-identical data may produce materially
different analyses run to run, up to 30x apart in score
([reproducibility](limitations.md#run-to-run-reproducibility)). A good aggregate therefore
says the *draw* is usually decent, not that the *one artifact in front of the validator*
is. The honest form is:

> Agent A's output distribution on tasks of this family has median regret X and worst-case
> Z over K runs. A single unreconciled invocation should be treated as a draw from that
> distribution.

That implies the unit being qualified is an agent **plus a protocol**. Agent A run once is
not qualified. Agent A run K times with a reconciliation step might be. `-T repeats=K`
exists to measure exactly that, and it is the number a validator should ask for first,
because SR 26-2 ties validation frequency to the "frequency and scope of model changes":
an agent whose output moves every run makes every invocation a model change.

## Claims Not Supported

- **A ranking of models.** The aggregate mean rank is reproduced by independently permuting
  each column at p = 0.25, so it describes the table rather than separating the models.
- **A claim about conceptual soundness.** Only the numeric prediction is scored, never the
  reasoning. An agent that reaches a well-calibrated answer for a bad reason is not
  penalized except where the flaw surfaces out of sample.
- **A transfer claim to deployment.** Whether a perEval score predicts the quality of a
  model that the agent builds on a real portfolio is **unmeasured**. No such study exists
  here.

## Relation to SR 26-2

Footnote 3 in SR 26-2 places generative and agentic AI outside its scope, but the half of
that footnote often left unquoted is also important:

> "Nonetheless, a banking organization's risk management and governance practices should
> guide the determination of appropriate governance and controls for any tools, processes,
> or systems not covered in this document. However, the principles described in this
> guidance apply to traditional statistical and quantitative models and non-generative,
> non-agentic AI models."

That is a delegation, not a gap, and it has a sharp consequence: a CCAR model an agent
builds is a traditional statistical model and is fully in scope no matter what built it.
The bank owes a control determination for the tool, and the guidance prescribes no method
for it. perEval is a candidate method, not a compliance artifact; the guidance "does not
set forth enforceable standards or prescriptive requirements".

Model testing in SR 26-2 runs "from out-of-sample and out-of-time testing, to a comparison
of alternative assumptions and methodologies, to a critical assessment of data quality,
relevance, and inputs". perEval covers one of those three.

| SR 26-2 element | perEval |
| --- | --- |
| Out-of-sample and out-of-time testing | **Covered.** Every task scores a held-out regime beyond the training range; the CCAR scenario is literally out-of-time. |
| Benchmarking to other models | **Covered** where a competent anchor exists. Ballistic has only naive and degenerate anchors, [deliberately](tasks/ballistic.md). |
| Comparison of alternative assumptions and methodologies | **Not measured.** Buildable judge-free: an instance where two methods fit in sample equally well and diverge out of sample. |
| Critical assessment of data quality, relevance, inputs | **Not measured.** Every task hands over clean curated data with the target already chosen. The largest gap. |
| Conceptual soundness: design, assumptions, qualitative judgments, data selection | **Not measured, by construction.** Scoring is numeric and judge-free, which is what buys the absence of judge-circularity problems. |
| Outcomes analysis against real-world outcomes | **Not applicable.** See the N = 1 argument above. |
| Effective challenge | **Not performed by perEval.** SR 26-2 has it "performed by individuals" with "organizational standing and influence to effect any change", which a tool structurally cannot have. perEval produces evidence *for* a human challenger. |

