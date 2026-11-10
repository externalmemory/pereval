# Running the Suite on Local Hardware

The question here is not how a local model ranks. It is whether a model running on one desktop machine can **complete** the tasks at all, and if not, what stops it. That is a different question from the one the score table answers, so these results live here and no local model appears in the main table. A row there needs a cell in all eight columns to earn a mean rank.

The short answer, after two models and three context sweeps: **all eight tasks run on 48 GB**, and the thing that looked like a hardware ceiling was a server default. `mlx_lm.server` prefills a prompt in chunks of `--prefill-step-size`, and lowering it from the default 2048 to 256 moved the measured ceiling from 89,601 tokens to past 298,658 on the same machine, the same model and the same memory. On six of the eight tasks what is left is a capability question rather than a deployability one, and the capability that fails is interval calibration. On the two heaviest it is still both: real agent loops survived 216,198 tokens and died at both 231,531 and 199,374, well short of what the probe reported and not reproducible to better than about 15%, and migration has only ever finished with its instances truncated.

An earlier version of this document concluded the opposite: that the binding constraint was context rather than capability, that the limit was set by RAM, and that four of the tasks could not run at all. Every part of that was wrong. The sections below keep the measurements that refuted it rather than quietly replacing the conclusion.

## Why Local Serving Is the Point

The reason to care about a local model is not this suite. It is the work the suite stands in for. A bank building its own CCAR or CECL models has to hand the agent loan-level history, current portfolio composition, internal rating definitions and scenario overlays, and much of that is material non-public information about the institution's own balance sheet. Sending it to a hosted endpoint means sending it to a third party's infrastructure under that party's retention and training terms, and for a lot of institutions that ends the conversation regardless of what the model can do.

So the question a local run answers is a deployability question: can an agent that never leaves the building do this class of work. The tasks here are synthetic on purpose, which is what makes them usable as a proxy. They pose the modelling problem without posing the data problem, so the ceiling and calibration findings transfer even though the data does not need protecting.

Two consequences follow.

**The deployability answer is yes, and on a desktop rather than on a cluster.** A real CCAR exercise carries more history, more segments, more scenarios and more documentation than a synthetic three-scenario instance, so its agent loop is longer than the ones measured here. The relevant number is therefore not what these tasks used but what the machine serves: a single growing conversation past 298,658 tokens on 48 GB of unified memory. That figure is an upper bound on a favourable workload rather than a budget a task can spend, because unguarded migration loops killed the server at 231,531 and at 199,374 tokens, 78% and 67% of it, as recorded under [The Probe Ceiling Overstates What an Agent Loop Reaches](#the-probe-ceiling-overstates-what-an-agent-loop-reaches). A bank with on-prem accelerators has more headroom than that, and this says it does not need it to start.

**The capability answer is not yes.** What is left after the ceiling is removed is what the scores speak to, and it is one specific failure rather than a diffuse one: interval coverage collapses while the point estimates stay in a credible range. A model risk function will waive a slow model. It will not waive intervals that are confident and wrong.

## Setup

| | |
| --- | --- |
| Machine | Mac Mini, 48 GB unified memory, same LAN, static IP |
| Server, first attempt | `caffeinate -i mlx_lm.server --model mlx-community/Qwen3.6-35B-A3B-4bit-DWQ --host 0.0.0.0 --port 8081` |
| Server, tuned | the same plus `--prefill-step-size 256 --prompt-cache-size 1`, which is what lifted the context ceiling past every task |
| Server build | mlx_lm 0.32.2, macOS 27.0.1, arm64, applegpu_g17s |
| Inspect model string | `openai-api/macmini/<repo>/<model>`, for example `openai-api/macmini/mlx-community/gemma-4-26B-A4B-it-qat-4bit` |
| Credentials | `MACMINI_BASE_URL=http://<ip>:8081/v1` and `MACMINI_API_KEY` in `.env` |
| Weight revisions | pinned below, because a repo name is not a version |

### The Weights Are Pinned By Commit, Not By Name

A Hugging Face repo name does not identify a set of tensors. `mlx-community` and `unsloth` re-quantize in place, so "the same model" re-downloaded later can be different weights, and a published cell measured against the old ones stops being reproducible without anyone touching this repository.

That is not a hypothetical. Of the four models pulled to this machine, one moved during the project: `mlx-community/Qwen3.6-27B-OptiQ-4bit` went from `7575c79a` to `3413c683` on 2026-10-30, after it was downloaded here. No published cell rests on it, so it cost nothing, but the next one might.

Every revision actually used, verified against `main` on 2026-11-09:

| Model | Revision used | Still `main`? | Repo last modified |
| --- | --- | --- | --- |
| `mlx-community/gemma-4-26B-A4B-it-qat-4bit` | `0e3cbab38ce568cf6e23543010d08d03b731910c` | yes | 2026-06-05 |
| `mlx-community/Qwen3.6-35B-A3B-4bit-DWQ` | `73c707af4243243b18193444467872d20cff9399` | yes | 2026-04-17 |
| `unsloth/gemma-4-26B-A4B-it-qat-GGUF` | `7b92b5b28818151e8669af2e45e88d6086f490dd` | yes | 2026-07-17 |
| `mlx-community/Qwen3.6-27B-OptiQ-4bit` | `7575c79af388aa16ce4722fe6c3fd0d3a8e964d2` | **no**, now `3413c683` | 2026-10-30 |

The first row is the one that matters: it backs the `gemma-4-26B-A4B (local)` row of the main table, and its local weights have since been deleted from the machine to reclaim disk. The row is still reproducible, because that revision is still what `main` points at and the repo has not changed since June. Pass the revision explicitly rather than trusting the name:

```bash
hf download mlx-community/gemma-4-26B-A4B-it-qat-4bit \
  --revision 0e3cbab38ce568cf6e23543010d08d03b731910c
```

Since `Qwen3.6-35B-A3B-4bit-DWQ` has not moved since April, the greedy October runs and any re-run at corrected sampling use identical tensors, so the sampler and `--prefill-step-size` are the only variables between them.

Inspect reaches any OpenAI-compatible endpoint through `openai-api/<service>/<model>`, where `<service>` names the `<SERVICE>_BASE_URL` and `<SERVICE>_API_KEY` pair to read. The base URL must stop at `/v1`, because Inspect appends the route itself. Model ids containing slashes survive, since only the first path segment is stripped to find the service.

Everything in the plumbing worked on the first try: tool calling through the Inspect agent loop, the Docker sandbox, reasoning returned as a proper content block, and the transcript archive. Nothing in the harness needed changing to point it at a machine on the LAN.

## What Ran, and What It Scored

Both local rows now complete all eight columns on the archived convention: one draw per instance over the same instances every hosted row uses, three instances per task and eight for CCAR, with quantile as three paired single-instance runs on the archived seeds. Their cells are therefore plain maxima and need no matched-convention adjustment.

| Task | Qwen3.6-35B-A3B | gemma-4-26B-A4B | Column context for the Qwen cell |
| --- | --- | --- | --- |
| CCAR | **0.366** | 0.44 | mid-field, between deepseek-v4-flash-0731 (0.30) and Claude Haiku 4.5 (0.37) |
| CECL | **0.001945** | 0.001948 | between nemotron-3-super (0.00056) and ling-3.0-flash (0.0087) |
| Migration | **1.267** | 6.179 | worse than the degenerate answer (1.000) and than the naive baseline (0.765) |
| Ballistic | **14** | 59 | between Kimi K3 (14) and nemotron-3-ultra (16) |
| Two-body | **1193** | 3377 | worse than the naive baseline (17), better than the degenerate answer (2861) |
| Three-body | 2925 | **2550** | inside the degenerate answer (3019) only just, and worse than the naive fit (332) |
| Flyby | **916** | 1327 | worse than the degenerate answer (138) by nearly seven times |
| Quantile | 3.8e12 | **0.078** | last in the column by thirteen orders of magnitude |

Qwen takes six of the eight cells. Its mean rank is 10.50 against gemma's 11.25, and both sit below the naive baseline's 10.38.

**The medians tell a different story from the cells, and the gap between them is the point.** Qwen's per-column medians are 0.134, 0.00015, 0.482, 12.1, 2.34, 331, 330 and 0.075. Every one of those beats gemma's published cell, and most would place mid-table. The published row does not, because three of its twenty six instances blew up numerically and a maximum convention promotes exactly those three. This is not an argument against the convention, which is the whole premise of the suite, but it is the clearest demonstration in the repository of what a worst-case cell does and does not describe.

Pooling all nine same-convention migration instances per model, Qwen is genuinely the better model on that column (Mann-Whitney p = 0.020), and the difference is not visible in the cells: 6.179 against 5.453 on the two worst draws is no difference at all. Where the two models differ unambiguously is in finishing at all. Qwen submitted on 9 of 9 migration instances and on all 26 instances of the full row; gemma submitted on 5 of 9, scoring the degenerate 1.000 by default on the other four (Fisher exact p = 0.082, suggestive rather than significant at this sample size).

**The instance count is not a detail.** CCAR was first run on three instances by mistake, giving a maximum of 0.154. On the full eight it is 0.313 for that earlier partial run, so the short run understated the cell by a factor of two and would have placed the model three ranks too high. A maximum over fewer draws is biased low, and on this column the bias was large enough to change the conclusion from "near-competitive" to "mid-field".

**What the comparison set is.** The ranked rows in the main table are mid-tier open-weight models plus Claude Haiku 4.5 and Claude Opus 5.5, selected on cost and free-endpoint availability rather than on capability. That makes the table the right yardstick for a local candidate, since most rows are the same class of model, and the wrong yardstick for absolute task difficulty: nothing here establishes that these tasks are hard for the strongest models available, only that they discriminate sharply within this tier.

Size is not the axis they respond to. The largest model in the table, nemotron-3-ultra at 550B total and 55B active parameters, scores 1.214 on migration, which is worse than the degenerate answer, and 2429 on two-body against a degenerate 2861. A local candidate at 26B to 35B is therefore not disqualified by parameter count, and a larger local model would not be qualified by it either.

### The Failures Are Specific, Not Diffuse

**Uncertainty quantification is the systematic failure, not point estimation.** Across the orbital columns Qwen's intervals are far too narrow at every difficulty. On the flyby, all three instances score worse than the degenerate answer (181 against 138.5, 330 against 127.0, 916 against 107.8) with interval coverage of 11.4%, 6.0% and 6.1% against a nominal 90%. Ballistic covers 38% to 57% and still beats the degenerate by four to nine times, because the point estimates are good enough to carry it. Three-body covers 90%, 1% and 57% on its three instances. A model that can locate the answer and cannot say how sure it is will pass the columns scored mostly on accuracy and fail the ones scored on calibration, which is exactly the pattern.

**Three instances of twenty six blew up numerically, and they set three of the eight cells.** The quantile cell is the clearest case. On seed 1, one block of one hundred fit a Student's t with an unconstrained location, the optimizer diverged to `loc = 15824746916060.2`, and that block's q99 came out at 3.76e12. The same seed's q90 was 0.0944, essentially sound, and the other two seeds scored 0.061 and 0.075. The agent's own verification step checked row count, column names, the absence of NaNs and that q95 fell inside its interval, and never checked magnitude. Two-body instance 2 (1193 against 1.73 and 2.34) and three-body instance 1 (2925 against 76.9 and 331) fail the same way.

**gemma's failure is different and worse: it often submits nothing.** Four of its nine migration instances never produced an answer. That is a failure of the agent loop rather than of the statistics, and it is why its migration cell is a degenerate 1.000 on four draws and 6.179 on the one that did submit.

### Reproducibility Was Near-Perfect, and That Was an Artifact

Three CCAR instances were run twice during the early greedy work, once in a three-instance run and again inside the eight. Two of the three reproduced **bit-identically**, to every digit of the regret and the same call count:

| CCAR instance | First run | Second run | Calls |
| --- | --- | --- | --- |
| 1 | 0.010952054156700877 | 0.010952054156700877 | 27, 27 |
| 2 | 0.1536092188756754 | 0.1536092188756754 | 31, 31 |
| 0 | 0.08701395118909286 | 0.07517589998792479 | 59, 46 |

That looked like a sharp contrast with the archived hosted rows, where re-running the same model on byte-identical instances moved cells by 7.4x ([detail](limitations.md#run-to-run-reproducibility)). It was not a property of local serving. It was greedy decoding, which `mlx_lm.server` defaults to and which nobody chose, and **it does not hold for either published row**, because both now decode with sampling. The published local rows carry the same run-to-run noise as every hosted row, and on migration they carry more: two Qwen runs at near-identical samplers produced worst cells of 1.267 and 5.453, a factor of four apart.

The one instance that diverged even under greedy decoding is the one whose first run hit the token limit, at 59 calls against 46. The divergence originates in the sandbox rather than the model: the agent writes and runs its own Python, and anything time-dependent or unseeded in that code changes the tool output, which changes the next prompt and forks the trajectory. Determinism in the server never bought determinism in the loop.

## The Decoder Settings, And Where They Differ Between the Two Rows

`mlx_lm.server` defaults `--temp` to **0.0** and Inspect sends no temperature unless one is configured, so the early local work here decoded greedily while every hosted row ran at its provider's default. That asymmetry sat in the setup unnoticed, and the two rows resolved it differently.

Verified rather than assumed: four identical prompts at `temperature 1.0, top_p 0.95, top_k 64` returned four different sentences, and the same prompt at the server's default returned the same sentence twice. The request body's temperature is honoured, and the default really is greedy.

**The Qwen row is one sampler throughout**, Qwen3.6's own recommended preset: `temperature 1.0`, `top_p 0.95`, `presence_penalty 1.5`, `top_k 20`, `min_p 0.0`. Inspect forwards temperature, top_p and presence_penalty natively; `top_k` and `min_p` are not forwarded by the OpenAI-compatible provider and must ride in `extra_body` or they are dropped silently.

**The gemma row is a maximum over two different decoder settings, which no other row in the table is.** Ten of the twenty one successful runs behind it were greedy and eleven were sampled at `temperature 1.0`, `top_p 0.95`, `top_k 64`, and the cells are maxima across both. Three cells are set by a greedy run (CCAR, quantile and two-body) and five by a sampled one (ballistic, CECL, flyby, migration and three-body). It is recorded rather than hidden because restricting the cells to the sampled runs alone moves only three of them: CCAR to 0.42, quantile to 0.074 and two-body to 3177. This is a provenance defect in that row rather than a property of local serving.

### What Sampling Bought, and What the Presence Penalty Did Not

Three migration runs on identical weights separate the two changes:

| Arm | `max_tokens` runaways | Turns | Median | Worst |
| --- | --- | --- | --- | --- |
| greedy, `--prefill-step-size 2048` | 14 / 16 / 8 | 55 / 49 / 36 | 0.347 | 0.796 |
| sampled, `presence_penalty 1.5` | 0 / 0 / 0 | 22 / 53 / 19 | 0.482 | 1.267 |
| sampled, `presence_penalty 0` | 1 / 0 / 0 | 39 / 25 / 31 | 0.728 | 5.453 |

**Sampling did almost all of the runaway suppression, not the penalty**: 38 runaways under greedy decoding, 1 with sampling alone, 0 with the penalty on top. Greedy decoding is the classic cause of repetition loops and that is what the 16,384-token runaways were.

The penalty also cannot do what it first appeared to do. `mlx_lm`'s `presence_penalty` is not OpenAI's whole-context semantics: `make_presence_penalty` in `sample_utils.py` subtracts the penalty only from tokens occurring in the last `presence_context_size` tokens, which both the sampler and the server default to **20**. It is a twenty-token sliding anti-repetition window with no memory of the transcript, so it cannot influence a judgment at turn 22 about whether the work is finished. Mean turn counts bear that out: 31.3 with the penalty against 31.7 without.

The penalty is kept because it wins on both median and worst and removes the last runaway, not because it changes how long the agent works.

### The gemma Row's Individual Cells

`mlx-community/gemma-4-26B-A4B-it-qat-4bit` at revision `0e3cbab38ce568cf6e23543010d08d03b731910c`, under `mlx_lm.server` 0.32.2 with `--prefill-step-size 256 --prompt-cache-size 1`.

**Its migration 6.179 is the worst cell in the table, and neither truncation nor greedy decoding explains it.** It is set by instance 0 of the run of 2026-10-28, which submitted (`completion` 1.0) rather than running out of room, and which decoded at temperature 1.0 rather than greedily. It is 6.2x the degenerate answer. A separate serving path was tried to rule out a transport defect behind it: `mlx_lm.server` silently discards a tool call whose arguments its `gemma4` parser cannot parse, 9 of 100 attempts in the archived runs, and llama.cpp's grammar-constrained parser removes that defect completely (853 model calls, zero discarded). It did not improve the task, so the cell stands and the defect is not its cause.

**Its flyby 1327 is a coverage failure**, set by instance 2 at coverage 0.00055, a near-zero-width interval that misses.

**Two cells carry a recorded exception to the rule that a cell is reported only if none of its runs failed outside the agent's control.** The CECL and migration columns each have sibling runs that ended with the server returning `{'error': 'generation thread died'}`, a crash outside the agent's control, which would make those two cells unreportable as written. They are kept with the failure recorded, because the successful runs behind them are complete and the crash is a property of the server rather than of the attempt. Both columns' cells come only from runs that completed.

### The Qwen Row's Individual Cells

`mlx-community/Qwen3.6-35B-A3B-4bit-DWQ` at revision `73c707af`, untouched since 2026-04-17, under the same server and flags. Nine evals back to back, 14h44m, every one exiting 0: twenty six instances, all of which submitted, zero dropped tool calls, zero API errors, and three `max_tokens` runaways, all three in CECL.

**Nothing in this row was context-limited.** The model's `max_position_embeddings` is 262,144 and the highest peak input anywhere in the row was 124,380 tokens, on three-body instance 2. Quantile, which the hosted rows reach at roughly 264k and which was expected to be the one unreachable column, peaked at 46k to 58k: that figure is a property of how hosted models approach the task, not an intrinsic requirement of it.

**Its quantile 3.8e12 is a single diverged optimizer**, described under failures above. It is published as measured, on the convention this suite reports, and it is the cell most worth reading alongside that column's median of 0.075.

## The Context Ceiling Was a Server Default

This section previously concluded that four of the eight tasks were unreachable because a 48 GB machine cannot hold enough context. That conclusion was wrong, and the error was mine rather than the hardware's.

`mlx_lm.server` prefills a prompt in chunks of `--prefill-step-size`, default 2048, and peak memory during prefill scales with that chunk size against the full context. Shrinking it moves the ceiling by more than a factor of three, at a cost of nothing that matters:

| Prefill step | Ceiling, one growing conversation | Prefill at 89.6k | Prefill at 9.9k |
| --- | --- | --- | --- |
| 2048 (default) | 89,601 to 99,601 | 726 tok/s | 2,154 tok/s |
| 512 | 139,308 to 149,308 | 776 tok/s | 1,992 tok/s |
| 256 | **above 298,658, no failure** | 743 tok/s | 1,751 tok/s |

All three rows are Gemma 4 26B A4B on the same machine, measured by growing one conversation in 10k chunks until the worker died. At 256 the probe ran out of turns at 298,658 tokens without the server dying, which is past the model's declared 262,144 window, so `max_position_embeddings` is not enforced and RoPE extrapolates instead. Serving a prompt that long is not the same as attending to it usefully, and nothing here tests the latter. The three settings are within 7% of each other on prefill throughput at 89.6k, and the 19% penalty at small contexts falls on calls that take five seconds. The setting is free.

A second default matters for the eval rather than for the probe. `--prompt-cache-size` retains 10 distinct KV caches, so under sequential sampling a finished sample's cache stays resident while the next one grows. At Gemma's 40 KiB per token a single 100k conversation is 4 GiB of retained cache, and ten of them is more than the machine has. `--prompt-cache-size 1` keeps the live conversation's prefix cache, measured at 96 to 97% hit rate throughout the sweep, and drops only the finished ones.

### Why the Memory Arithmetic Did Not Predict It

Weights plus KV cache at each model's failure point, computed from each `config.json`:

| | Weights | KV per token | Ceiling at step 2048 | KV at ceiling | Weights + KV |
| --- | --- | --- | --- | --- | --- |
| Qwen3.6-35B-A3B | 19.5 GB | 20 KiB, 10 full-attention layers x 2 KV heads | 113k observed | 2.2 GiB | 21.7 GiB |
| Qwen3.6-27B-OptiQ | 20.4 GB | 64 KiB, 16 x 4 | 39,744 to 49,744 | 2.7 GiB | 23.1 GiB |
| Gemma 4 26B A4B | 15.6 GB | 40 KiB, 5 x 8, plus 0.2 GiB constant | 89,601 to 99,601 | 3.8 GiB | 19.4 GiB |

Three models spanning 3.2x in KV geometry and 4.8 GB in weights all die with 19 to 23 GiB committed, and the one using the least memory is not the one that reaches furthest. The persistent allocations do not explain the ceiling.

What does is transient. `iogpu.wired_limit_mb` is 40960 on this machine against `hw.memsize` of exactly 48 GiB, and a heavy 35B run reported `Physical footprint (peak): 38.5G`, which is 1.5 GiB under that cap. Subtracting the 21.7 GiB of weights and KV leaves **16.8 GiB of transient allocation**, live only while a prompt is being prefilled. That is the quantity `--prefill-step-size` controls, and it is why the ceiling responded to a flag and not to a smaller model.

KV geometry still explains the ranking of the three, and only the ranking. The 27B is worst because it carries both the largest weights and 3.2x the 35B's KV per token, and its mixed-precision `OptiQ` quantization is the reason the weights are large: 8-bit embeddings, `lm_head`, `k_proj`, `v_proj`, `o_proj` and all of layers 0 and 63 put it near 6 bits per weight rather than 4.

### Five Wrong Predictions, For The Record

The ceiling was predicted five times from memory arithmetic and missed every time, including once in the wrong direction. Predicted 155k to 170k for the 27B against a measured 44.7k. Predicted 270k for Gemma at step 512 against a measured 144k, then 235k at step 256 under one fit and 161k under another, against a measured figure above 298k. The direction was right three times out of five and the magnitude never. The lesson recorded here is that on this hardware the ceiling is cheap to measure and not worth predicting: one sweep costs 15 minutes and one server restart.

### Past the Ceiling the Server Dies Rather Than Degrades

The failure mode is abrupt and it lies. The worker thread exits, every subsequent generation request returns `404 {"error": "generation thread died"}`, and `/v1/models` keeps answering 200, so a health check on the models route reports a healthy server that cannot generate. Every runner here therefore health-checks with a real two-token completion instead.

`vmmap <pid> | grep -i "physical footprint"` is the way to read memory on macOS, since Activity Monitor has no peak column and `phys_footprint` counts Metal buffers in unified memory where plain RSS does not. Observed during a heavy 35B run: `Physical footprint: 29.2G`, `Physical footprint (peak): 38.5G`.

### How the Ceiling Was Measured, and Why the First Two Answers Were Wrong

Three times for the 35B, all at the default prefill step, and the method rather than the number is what the later sweeps reused.

A one-shot prefill probe reached 149,426 tokens successfully and failed at 250,000, which suggested a ceiling somewhere between. That was confounded: the earlier prompts in the same probe were still held in the prompt cache, so the 250k call ran with roughly 212k already resident. The number was a total-KV budget, not a per-prompt ceiling.

Growing a **single** conversation in 30k-token chunks then served 119,326 tokens and died on the next call at approximately 149k, which is lower than the cold 149,426 that had succeeded. So the two measurements disagree, and the one that matters for an agent is the lower one, because an agent loop is exactly a single growing conversation.

The live run settled it. Migration instance 1 grew in exact 3,260-token increments, reached a prompt of **113,021 tokens**, and killed the worker on the next call. That is the operational ceiling for that model at the default step: not a published spec, not a flag, just where this model on this machine stopped.

The method that survived is the third one, run deliberately instead of by accident: one conversation, grown in fixed chunks, with the prefix cache carrying the shared part. It costs about 15 minutes and one server restart per setting, which is why predicting it was never worth the error bars.

### The Hosted Context Table Was Not Predictive

The earlier version of this section sized the local ceiling against hosted peak contexts drawn from the four most recent runs of each task. That sample was biased, and it was biased in the direction that made the conclusion look inevitable: the most recent runs are small fast iterative models, the class a local candidate belongs to, and within-task spread across all archived runs is 10x to 100x. Over every archived hosted sample instead, local runs excluded. Prompt size is `input_tokens` plus the cached halves, because a provider that caches reports only the uncached remainder in `input_tokens` and reading that field alone understates a long agent loop by orders of magnitude.

| Task | Runs | Samples | Min peak | Median peak | Max peak | Under 89.6k | Under 298k |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Two-body | 31 | 88 | 2,444 | 29,992 | 138,039 | 99% | 100% |
| CECL | 19 | 43 | 1,524 | 40,778 | 418,234 | 77% | 95% |
| Ballistic | 31 | 103 | 11,298 | 49,448 | 440,026 | 79% | 97% |
| Three-body | 34 | 72 | 12,410 | 55,811 | 511,297 | 58% | 93% |
| CCAR | 21 | 91 | 1,434 | 73,548 | 604,889 | 62% | 92% |
| Migration | 48 | 76 | 2,016 | 78,827 | 486,893 | 53% | 92% |
| Quantile | 14 | 20 | 25,584 | 148,841 | 331,177 | 30% | 80% |
| Flyby | 13 | 38 | 22,315 | 175,004 | 752,480 | 37% | 74% |

Two things follow. The four-run medians overstated the all-sample median by 2x to 3.5x on exactly the three tasks the document declared unrunnable: ballistic 175,942 against 49,448, three-body 181,814 against 55,811, quantile 264,388 against 148,841. And even at the untuned 89,601 ceiling, the majority of hosted samples of every task except quantile and flyby would have fit, which should have been enough to question the conclusion before a server flag did.

Peak context is behaviour, not requirement, and the 10x to 100x within-task spread is the proof. Qwen3.6 completed CECL with a peak prompt of **20,502 tokens** against a hosted median of 40,778, because it wrote long single scripts instead of iterating in many short tool calls. It spent 549k output tokens on instance 0 and only 634k prompt tokens in total.

That cuts both ways. A 49k median does not prove ballistic needs 49k, and a model with a different working style might need triple it. It also means a local model's context demand cannot be predicted from the hosted column at all, in either direction.

## What Makes the Endpoint Fast Enough

**Prefix caching is the reason the agent loop is viable.** Extending a conversation by a new turn pair costs almost nothing:

| Call at ~55k tokens | Time |
| --- | --- |
| Cold, first sight | 32.73s |
| Extended by one turn pair | **0.50s** |
| Different prompt, same size (control) | 1.055x the cold call |

The control matters. A same-length prompt with a different prefix costs the full cold price, so the saving is genuine prefix matching and not a size artifact. In the live two-body run, **78% of all prompt tokens were served from cache, on 100% of calls**. Retention is not slot-limited: interleaving two, three and four separate conversations gave 100% reuse on every warm call, so the default `--prompt-cache-size` needs no tuning.

An earlier probe suggested prefix reuse did **not** work, and that probe was wrong. It appended the new text inside the existing user message, which places new tokens before `<|im_end|>` and breaks the common prefix. No agent does that. Extending the message list, which is what an agent actually does, reuses the prefix completely.

**Prefill rate falls off hard with length.**

| Prompt | Seconds | Rate | Marginal rate over previous size |
| --- | --- | --- | --- |
| 1,983 | 7.14 | 278 tok/s | overhead-dominated |
| 10,033 | 4.09 | 2,453 tok/s | |
| 49,734 | 28.15 | 1,767 tok/s | 1,650 tok/s |
| 149,426 | 151.40 | 987 tok/s | 809 tok/s |

**Concurrency is close to free**, which is what a 3B-active MoE should do: 41 tok/s on a single stream, 40.5 tok/s per stream at three concurrent, roughly 122 tok/s aggregate. Concurrency was still not used for the suite runs, because three concurrent samples multiply the KV footprint by three and the ceiling is the binding constraint. `--max-connections 1` throughout.

**Reasoning suppression.** `chat_template_kwargs: {"enable_thinking": false}` works through Inspect's `GenerateConfig(extra_body=...)`. `reasoning_effort` is silently ignored. Worth knowing because the very first call returned `content: null` with `finish_reason: length`, having spent the entire token budget inside the reasoning block.

## KV Quantization Does Not Help

`--kv-bits 8` is the obvious lever for the memory ceiling, and it costs more than it buys. Greedy decoding on this server is bit-reproducible, so repeated calls in one arm give an identical hash and the noise floor is exactly zero. That makes the A/B clean.

| Prompt tokens | Same arm reproducible | fp16 vs kv8 char similarity | fp16 repeat time | kv8 repeat time |
| --- | --- | --- | --- | --- |
| 9,971 | yes, both arms | 0.668 | 2.10s | 5.91s |
| 52,529 | yes, both arms | 0.791 | 2.40s | 36.53s |
| 87,891 | yes, both arms | 0.787 | 3.02s | 82.68s |

Two findings, and the second is the disqualifying one.

Output changes at every context length, at paraphrase level rather than token level. Against a zero noise floor that is a real perturbation, not sampling variance.

And `--kv-bits 8` **disables the prompt cache entirely**. Look at the repeat times: the fp16 arm serves a repeated prompt in 2 to 3 seconds, while the kv8 arm pays 6 to 83 seconds to prefill it again, rising with length. `cached_tokens` was 0 on every call of a four-call prefix test under kv8. Trading an 80x speedup on every turn of an agent loop for a fraction of the KV footprint is not a trade worth making.

`--prompt-cache-bytes 20000000000` was also tried as a crash guard, on the theory that capping the cache would make the allocator fail gracefully instead of killing the worker. It does not work. The worker still died with the flag set.

## A Token Limit Converts a Crash Into a Score, and It Was Still the Wrong Fix

**This section used to open by saying the useful mitigation was a limit on the Inspect side rather than the server side, and that is backwards.** The server side is where the fix was: `--prefill-step-size 256` moved the measured ceiling from 89,601 tokens to past 298,658, and from 29 Oct onward every local run dropped `--token-limit` entirely, with eight completing at status `success`. The Inspect-side limit was a stopgap that bought finished runs at the price of truncated cells. It is recorded here because the truncation is still inside the archived numbers, not because it is the setting to use.

The discriminating-metric finding is the part that stands. Output tokens do not separate a healthy long run from a runaway one: a healthy two-body instance reached 268,492 output tokens while the migration instance that killed the server was at 275,120. Total tokens do separate them, 2,108,703 against 3,014,518.

`--token-limit 2500000` trips at roughly 100k of context and converts a fatal server crash into a recorded `sample.limit` on a sample that still gets scored. On the 35B it caught migration instances 0 and 1 at peak contexts of 93,129 and 106,285, and CCAR instance 5 at 80,827, and those runs completed at status `success` where the unguarded migration attempt the night before had killed the server mid-sample. Three of fourteen samples were truncated, and only one of those three sets its task's cell.

**Peak context means fresh prompt tokens plus the cached prefix, and the distinction matters more than it looks.** `mlx_lm.server` reports only the uncached portion in `input_tokens`, so reading that field alone understates the true context by 3x to 5x: the same three samples read as 18,745, 35,102 and 21,325 on fresh tokens against the 93,129, 106,285 and 80,827 above. Any ceiling analysis built on `input_tokens` will conclude a task fits when it does not.

**On Gemma the guard was not selective at all.** Both migration runs had all three instances truncated, six samples out of six, at peak contexts of 122,081 across the board on 28 Oct and 103,661, 105,790 and 47,830 on the rerun. The published Gemma migration cell is therefore an upper bound on every instance behind it, not on one of three.

The cost is that a truncated cell is an upper bound rather than a measurement, exactly as it is for the archived minimax migration row, and that **nothing in the score distinguishes the two**. `completion`, `matrix_quarters` and `fit_years` all read as complete on the truncated instances. Only `sample.limit` on the eval log shows it, which is the same trap recorded under [A Time-Limited Run Still Produces a Score](limitations.md#a-time-limited-run-still-produces-a-score).

### The Probe Ceiling Overstates What an Agent Loop Reaches

**Dropping the token limit brought the crash back, and it came back below the measured ceiling.** The unguarded migration run on 28 Oct reached a peak context of 231,531 tokens across 110 model calls and 223 messages, and the server died with `generation thread died`. The 256-step sweep had run the previous evening and reached 298,658 tokens without a failure, so the flag was in place. Moderate confidence on that last point: it rests on the sweep's timestamp and on every Gemma task run after it hitting the same server, not on a recorded restart.

The probe and the agent loop are not the same workload. The probe grows one conversation against a warm prompt cache with a stable prefix. An agent loop interleaves tool output, forks its prefix at every sandbox result, and shares the machine with a Docker container. So **298,658 is an upper bound on a favourable workload rather than a ceiling a task can spend**, and the true figure for migration sits somewhere below 199,374, the lower of its two deaths.

**There is no single survival ceiling, and it took a third run to show it.** Three unguarded runs on the same machine and the same model reached peak contexts of 199,374, 216,198 and 231,531 tokens. The middle one is the survivor: CCAR instance 6 completed at status `success` at 216,198 on 30 Oct, while migration died at 231,531 on 28 Oct and again at 199,374 on 1 Nov. A survival sitting between two deaths is not a band with edges. The earlier reading of these numbers as a narrow bracket between 216,198 and 231,531 was two points that happened to land close together, and the third broke the ordering rather than tightening it. Read as a spread, the three span 32,157 tokens, **15% of their midpoint**, so the ceiling is not reproducible to better than that and no single figure, the 298,658 probe included, is a budget a task can be given.

The server flag is not the explanation. The measured ceilings are 89,601 tokens at the default `--prefill-step-size` of 2048 and 144,000 at 512, and the 199,374 death is above both, so that server cannot have been running either and 256 or finer is the only setting consistent with it. What did differ between the runs is how long the server had been up: the 231,531 death came on a server restarted the previous evening, the 199,374 one after sixteen and a half hours and 208 calls on a single growing conversation. Allocator fragmentation is the first candidate and it is not a demonstrated one. Low confidence on the mechanism, high confidence that the spread is real, because all three figures are the same statistic computed the same way, fresh prompt tokens plus the cached prefix.

Peak context reached per task, from completed runs:

| Task | Peak context | Share of the 298,658 probe ceiling | Token limit in force |
| --- | --- | --- | --- |
| CCAR | **216,198** | 72% | none |
| migration | 122,081 | 41% | 2,500,000, all instances truncated |
| CECL | 47,573 | 16% | 2,500,000 |
| three-body | 39,040 | 13% | 2,500,000 |
| two-body | 31,069 | 10% | none |
| flyby | 27,298 | 9% | 2,500,000 |
| quantile | 25,455 | 9% | 2,500,000 |
| ballistic | 20,991 | 7% | 2,500,000 |

Migration's 122,081 is the truncated figure, not what the task wants; unguarded it reached 231,531 and 199,374 and died at both. CCAR's 216,198 is the honest number for the heaviest task that has ever completed, and it is 10x the ballistic figure, so the spread across tasks is far wider than any headroom claim that quotes a single number can carry. This qualifies the headroom claim made twice elsewhere in this document: six tasks are settled by a wide margin, CCAR completed at a context higher than one that killed the server under migration, and migration has never completed unguarded at all.

The no-submit loop makes this worse rather than better, because thrashing turns keep growing the context. The CECL sample described in the next section passed 136,558 tokens while producing no tool calls, against 47,573 for the whole completed CECL run, so a sample can be driven toward the ceiling by a failure mode that has nothing to do with the task's real context demand. The 1 Nov migration run is the same shape at full size: 418 messages and 208 calls to 199,374 tokens over sixteen and a half hours, ending with the model announcing `[PROJECT STATUS: TERMINATED - SUCCESSFUL DEPLOYMENT]` and never submitting. Nothing after the first few thousand tokens bought anything, and the last of them killed the worker.

## The Message Limit Is the Guard That Actually Binds

**The runaway mode that costs the most is not a crash and not a context overflow. It is the agent finishing the work and then refusing to submit.** CECL instance 0 wrote a complete `predictions.csv`, all twelve pools with point estimates and bounds, eleven minutes into the run. It then spent the next seventeen hours producing replies that contained no tool call.

| Signal, CECL instance 0 | Value |
| --- | --- |
| Wall clock | 17.2 hours, sample still unfinished |
| Cumulative model time | 16.69 hours, so the server was 97% busy |
| Generate calls | 250, of which 248 returned |
| Call duration | median 162s, p90 520s, max 1,572s |
| Messages | 263 of the task's `message_limit=500` |
| Assistant turns | 248 |
| Tool calls | **12** |
| Stop reasons | 733 `stop`, 12 `tool_calls`, 4 `max_tokens` |
| Output tokens | median 1,692 per call, 630,313 in total |

**It is not truncation and it is not the server.** Four of 248 calls hit `max_tokens`; the rest stopped normally at a median of 1,692 tokens. Every POST returned `HTTP/1.0 200 OK`. The model produces fluent, normal-length prose, `basic_agent` re-prompts it because there is no tool call to execute, and the cycle repeats at two to twenty-six minutes a turn until the message limit ends the sample. This is the same family as the repetition loop under [Every Local Run Was Greedy and No Hosted Run Was](#every-local-run-was-greedy-and-no-hosted-run-was), and greedy decoding is the obvious suspect, but that is inferred rather than tested. Low confidence on the cause, high confidence on the shape.

**It is intermittent, which is why it went unnoticed.** Per-sample message counts, same tasks, same instance counts:

| Run | Messages per sample |
| --- | --- |
| CCAR, 28 Oct | 32, 62, 24, 24, 30, 34, 12, 10 |
| CCAR, 30 Oct | 32, 30, **218**, 34, 28, 24, **500**, 24 |
| CECL, 27 Oct | **170**, 52, 28 |

Two samples out of eight account for the 30 Oct CCAR run taking 511.6 minutes against 64.0 minutes for the same eight instances two days earlier. An 8x difference in run time that presents as server degradation is two thrashing samples, and the decode rate that appears to fall from 51.6 to 22.1 tok/s is confounded with prefill on their long contexts. Nothing was wrong with the server.

**A message-limit hit still produces a scored cell.** This is measured, not assumed: the 30 Oct CCAR sample that hit 500 messages ended with `sample.limit` set, the run completed with status `success`, and the run produced a cell of 0.1718. The scorer reads `predictions.csv` out of the sandbox, and by the time the loop starts thrashing that file has long since been written. The same caveat applies as for the token limit above, that a truncated cell is an upper bound and **nothing in the score distinguishes the two**: only `sample.limit` on the eval log shows it.

**The default message limit is therefore a cost driver, not a safety net.** It is 500 on six of the eight tasks, 600 on the flyby and 800 on quantile, and at a median 162s per turn 500 licenses a single sample to burn eleven hours after its work is complete. `-T message_limit=100` would bound a thrashing sample to about four hours and would have cost nothing on any run recorded here, because no sample has ever recovered and submitted after turn 100 and the worst healthy sample used 170. It is a deviation from the convention the archived rows were measured under, so it belongs in its own experiment rather than mid-row.

### A Working Run and a Dead One Look Identical

**The `.eval` file's modification time is not a liveness signal, and treating it as one destroyed a working run.** Inspect writes running samples to a SQLite sample buffer under `~/.local/share/inspect_ai/samplebuffer/` and only touches the `.eval` when a sample completes. A run that is 97% busy on a sample taking seventeen hours leaves the `.eval` untouched for seventeen hours, exactly as a dead run would. An `ESTAB` socket to the server with empty queues is likewise not evidence of an abandoned request: the server speaks HTTP/1.0 and opens one connection per request, so a long request in flight looks like that for its whole duration.

The signals that do work, in order of cost:

- `~/.local/share/inspect_ai/traces/trace-<pid>.log` records every `generate` enter and exit with a duration, and its modification time moves every few minutes on a healthy run. This is the one to watch, and the one that settled the diagnosis here.
- The sample buffer database holds the running sample's messages, events and tool calls, and is readable with `sqlite3` while the run is live.
- `py-spy dump --pid <pid>` shows only that the event loop is idle in `select`, which is what a healthy async client looks like between I/O completions. It does not discriminate, and on this box it needs `sudo`, because `ptrace_scope` is 1 and a backgrounded chain reparents to init.

Two Gemma runs were killed on the strength of the `.eval` mtime, at 13 and 17 hours. Both were working. The first had completed 324 generate calls and was on its second instance when it was killed, and its trace log ends with a successful response seconds before the kill.

## What Would Close the Gap

The gap is no longer context, and the fix was never a better model. One server flag moved the measured ceiling from 89,601 tokens to past 298,658, which settles six of the eight tasks outright, so for those the levers that remain are all about the scores. CCAR and migration are not settled: they reached 216,198 and 231,531 tokens, 72% and 78% of a ceiling that is itself optimistic, and migration crashed the server at that figure and again at 199,374.

**Sampling is the first lever, and it was set wrong by default.** See [Every Local Run Was Greedy and No Hosted Run Was](#every-local-run-was-greedy-and-no-hosted-run-was). Greedy decoding is what put the migration agent into a repetition loop, and it is also the reason the local rows are not strictly comparable with the hosted ones.

**Calibration is the second, and nothing here says it is cheap.** Coverage is the component that collapses, on every task where an interval is scored, on both local models tested. The point estimates stay in a credible range while the intervals are narrow and misplaced, which is a prompting and scoring-feedback problem as much as a model one. Nothing in the serving setup touches it.

**More memory is no longer on the list.** The ceiling turned out to be transient prefill workspace rather than a persistent allocation, so buying RAM buys a smaller multiple of what a flag already gave for free. Moderate confidence: the mechanism is inferred from a 16.8 GiB residual and from the response to `--prefill-step-size`, not from an allocator trace.

**Cutting context demand is still available and still a harness change.** The agent loop's context is dominated by accumulated tool output, so trimming or summarizing it would move every task at once, and it would change what the archived columns mean. That makes it a change to the harness rather than to the serving setup, and out of scope here.

## Candidates Still To Test

Tested so far, all at 4-bit on the same 48 GB machine:

| Model | Ceiling at step 2048 | Weights | Decode | Prefill at 10k | Cells |
| --- | --- | --- | --- | --- | --- |
| Qwen3.6-35B-A3B-4bit-DWQ | 113k observed | 19.5 GB | 41 tok/s | 2,453 tok/s | four tasks, one an upper bound |
| Qwen3.6-27B-OptiQ | 39,744 to 49,744 | 20.4 GB | 14 tok/s | 374 tok/s | none, screened out on the ceiling |
| Gemma 4 26B A4B QAT | 89,601 to 99,601 | 15.6 GB | 74 tok/s | 2,100 tok/s | all eight tasks |

The 27B was screened out before any task ran: the smallest ceiling of the three despite being the smallest model by parameter count, because `OptiQ` mixed precision puts it near 6 bits per weight and its KV geometry is 3.2x the 35B's per token. It is also the slowest of the three by a factor of three on decode, which is the one axis where a local model has no margin to give away.

Still queued:

- Qwen3.8-27B

The thing to watch is interval coverage rather than the point estimates, because that is the component that has failed on both models tested and it is the component a model risk function will not waive.

The protocol for each: `--prefill-step-size 256 --prompt-cache-size 1` on the server, a real completion as the health check rather than `/v1/models`, and on the Inspect side `-T n_instances=3 -T seed=1 --max-tokens 16384 --max-connections 1 --token-limit 2500000 --time-limit 86400`, eight instances for CCAR, three single-instance runs at seeds 1, 2 and 3 for quantile, and a transcript saved to `runs/` per sample. Sampling goes in a `--generate-config` file, because Inspect's OpenAI provider forwards `temperature` and `top_p` but silently drops `top_k`, which has to ride in `extra_body` instead. Measure the ceiling first and report it alongside the cells, because a ceiling reached mid-suite costs a human restart and a ceiling measured first costs 15 minutes. Watch progress on `~/.local/share/inspect_ai/traces/trace-<pid>.log` rather than on the `.eval` file, for the reason given under [A Working Run and a Dead One Look Identical](#a-working-run-and-a-dead-one-look-identical).
