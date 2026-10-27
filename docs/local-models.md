# Running the Suite on Local Hardware

The question here is not how a local model ranks. It is whether a model running on one desktop machine can **complete** the tasks at all, and if not, what stops it. That is a different question from the one the score table answers, so these results live here and no local model appears in the main table. A row there needs a cell in all eight columns to earn a mean rank, and the first local model tested can only run three of them.

The short answer from the first attempt: the binding constraint is **context, not capability**, and the limit is set by RAM rather than by the model. On 48 GB, three of the seven tasks run and four do not, for reasons that have nothing to do with how good the model is at credit modelling.

## Why Local Serving Is the Point

The reason to care about a local model is not this suite. It is the work the suite stands in for. A bank building its own CCAR or CECL models has to hand the agent loan-level history, current portfolio composition, internal rating definitions and scenario overlays, and much of that is material non-public information about the institution's own balance sheet. Sending it to a hosted endpoint means sending it to a third party's infrastructure under that party's retention and training terms, and for a lot of institutions that ends the conversation regardless of what the model can do.

So the question a local run answers is a deployability question: can an agent that never leaves the building do this class of work. The tasks here are synthetic on purpose, which is what makes them usable as a proxy. They pose the modelling problem without posing the data problem, so the ceiling and calibration findings transfer even though the data does not need protecting.

Two consequences follow, and they point in opposite directions.

**The context finding gets worse, not better, under a real deployment.** A real CCAR exercise has more history, more segments, more scenarios and more documentation than a synthetic three-scenario instance, so its agent loop is longer than the ones measured here, not shorter. A ceiling that already blocks four of seven synthetic tasks blocks more of the real thing.

**The hardware finding gets better.** The constraint turned out to be RAM rather than model quality, and a bank is not deploying on a 48 GB desktop. On-prem hardware with several hundred GB of accelerator memory removes the ceiling entirely and leaves only the calibration question, which is the one the scores here actually speak to. Read that way, the result is encouraging: the thing that broke was the thing money fixes, and the thing that cannot be fixed with money is still open.

## Setup

| | |
| --- | --- |
| Machine | Mac Mini, 48 GB unified memory, same LAN, static IP |
| Server | `caffeinate -i mlx_lm.server --model mlx-community/Qwen3.6-35B-A3B-4bit-DWQ --host 0.0.0.0 --port 8081` |
| Server build | mlx_lm 0.32.2, macOS 27.0.1, arm64, applegpu_g17s |
| Inspect model string | `openai-api/macmini/mlx-community/Qwen3.6-35B-A3B-4bit-DWQ` |
| Credentials | `MACMINI_BASE_URL=http://<ip>:8081/v1` and `MACMINI_API_KEY` in `.env` |

Inspect reaches any OpenAI-compatible endpoint through `openai-api/<service>/<model>`, where `<service>` names the `<SERVICE>_BASE_URL` and `<SERVICE>_API_KEY` pair to read. The base URL must stop at `/v1`, because Inspect appends the route itself. Model ids containing slashes survive, since only the first path segment is stripped to find the service.

Everything in the plumbing worked on the first try: tool calling through the Inspect agent loop, the Docker sandbox, reasoning returned as a proper content block, and the transcript archive. Nothing in the harness needed changing to point it at a machine on the LAN.

## What Ran, and What It Scored

| Task | Ran | Cell (worst of its instances) | Column context |
| --- | --- | --- | --- |
| Two-body | yes | **814.9** | worse than the naive baseline (17), better than the degenerate answer (2861) |
| Migration | yes, truncated | **0.796** | worse than the naive baseline (0.765), better than the degenerate answer (1.000) |
| CECL | yes | **7.5e-03** | bottom group, between nemotron-3-super (5.6e-04) and ling-3.0-flash (8.7e-03) |
| CCAR | yes | **0.313** | mid-field, between deepseek-v4-flash-0731 (0.30) and Claude Haiku 4.5 (0.37) |
| Ballistic | no | | median peak context 176k against a ~113k ceiling |
| Three-body | no | | median peak context 182k |
| Quantile | no | | median peak context 264k |

Each cell is a single run of three instances on the archived seeds (`-T n_instances=3 -T seed=1`), except CCAR, which uses eight as the published convention requires. These are not published-standard cells and are not meant to be: a single run cannot be a worst case over at least three runs.

**The instance count is not a detail.** CCAR was first run on three instances by mistake, giving a maximum of 0.154. On the full eight it is **0.313**, so the short run understated the cell by a factor of two and would have placed the model fourth in the column instead of seventh, three ranks too high. A maximum over fewer draws is biased low, and on this column the bias was large enough to change the conclusion from "near-competitive" to "mid-field".

**What the comparison set is.** The ranked rows in the main table are mid-tier open-weight models plus Claude Haiku 4.5, selected on cost and free-endpoint availability rather than on capability. No frontier model is ranked in any column. That makes the table the right yardstick for a local candidate, since the rows are the same class of model, and the wrong yardstick for absolute task difficulty: nothing here establishes that these tasks are hard for the strongest models available, only that they discriminate sharply within this tier.

Size is not the axis they respond to. The largest model in the table, nemotron-3-ultra at 550B total and 55B active parameters, scores 1.214 on migration, which is worse than the degenerate answer, and 2429 on two-body against a degenerate 2861. It is the third-worst ranked row. A local candidate at 26B to 35B is therefore not disqualified by parameter count, and a larger local model would not be qualified by it either.

### The Failures Are Specific, Not Diffuse

**CECL under-reserves, systematically.** On the adverse instance the model predicted $3.38M of lifetime loss against a true $8.67M, a **61% shortfall**, with interval coverage of 0.197 and a Winkler regret of 2.189 against the degenerate answer's 2.299. The intervals were not merely wrong, they were confident and wrong. `portfolio_bias` is negative on all three instances (-$0.59M, -$5.29M, -$0.89M), so the direction is consistent: it priced the adverse scenario roughly as if it were the benign one.

| CECL instance | ecl_regret | Loss rate MAE (bps) | Coverage | Portfolio bias |
| --- | --- | --- | --- | --- |
| 0 baseline | 1.5e-04 | 96.3 | 0.805 | -$0.59M |
| 1 adverse | 7.5e-03 | 743.9 | 0.197 | -$5.29M |
| 2 benign | 2.4e-04 | 111.7 | 0.547 | -$0.89M |

**Migration fails the sign of the stress response, on one instance of three.** Instances 0 and 2 lost one of sixteen checks and have positive downgrade slopes (0.209 and 0.786 against oracle 0.754 and 0.949). Instance 1 lost six checks, including `prediction_shares_sum_to_one`, `downgrades_rise_with_severity` and `pd_rises_with_horizon`, and its `matrix_downgrade_slope` is **negative** at -0.395 against an oracle 0.719, with `stress_peak_lag` at -5 quarters. It built a transition matrix in which stress improves credit quality. That is the kind of error a reviewer catches in one glance at a monotonicity table, and it is the error that sets the cell.

**Two-body produced tight intervals around wrong answers on two instances of three.** Instance 2 scored 0.0194, which would be the best non-oracle cell in that column (the published best is 0.069, the oracle 0.005). Instances 0 and 1 scored 814.9 and 762.1, with coverage 0.000 and 0.201 and mean absolute error near 21 degrees on both. The problem is not that it cannot do the task. It did the task on one instance and then failed to notice it had failed on the other two.

| Two-body instance | winkler_regret | MAE (deg) | Coverage | Mean width |
| --- | --- | --- | --- | --- |
| 0 | 814.9 | 21.27 | 0.000 | 1.82 |
| 1 | 762.1 | 21.02 | 0.201 | 4.61 |
| 2 | 0.0194 | 0.043 | 0.953 | 1.66 |

**CCAR is the task it comes closest on, and its eight instances prove the diagnosis.** Every instance beat the degenerate answer (0.57), and the worst of them beat the naive baseline (0.85) by a factor of nearly three. One of the eight, instance 5, tripped the token limit at a peak prompt of 80,827; it scored 0.0305 and does not set the cell, so the truncation changes nothing here.

| CCAR instance | winkler_regret | MAE | Coverage | Mean width | Calls | Peak prompt |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.0752 | 0.0103 | 0.761 | 0.0370 | 46 | 49,392 |
| 1 | **0.0110** | 0.0193 | 0.951 | 0.0777 | 27 | 52,377 |
| 2 | 0.1536 | 0.0096 | 0.676 | 0.0446 | 31 | 33,849 |
| 3 | 0.0303 | 0.0159 | 0.930 | 0.0611 | 33 | 47,060 |
| 4 | 0.0612 | 0.0157 | 0.905 | 0.0888 | 44 | 93,561 |
| 5 | 0.0305 | 0.0258 | 0.886 | 0.0664 | 67 | 80,827 |
| 6 | **0.3130** | 0.0153 | 0.485 | 0.0248 | 24 | 28,142 |
| 7 | 0.1810 | 0.0183 | 0.649 | 0.0471 | 31 | 62,520 |

Across those eight instances, **coverage explains the score almost completely and point accuracy explains none of it**:

| Component | Spearman against winkler_regret | p |
| --- | --- | --- |
| Coverage | **-0.976** | 0.00002 |
| Mean width | -0.738 | 0.037 |
| MAE | -0.548 | 0.16 |

Instance 1 has the **highest** point error of all eight (MAE 0.0193) and the **lowest** regret (0.0110), because its coverage is 0.951. Instance 6 has mid-range point error (0.0153) and the worst regret (0.3130), because it submitted the narrowest intervals in the set (width 0.0248) and covered 0.485 of the truth. The model's point estimates are uniformly decent. What varies, and what the score tracks, is whether it had any idea how uncertain they were.

That is the common thread across all four tasks: **miscalibration rather than incompetence**. Two-body MAE of 21 degrees inside intervals 1.8 degrees wide. CECL coverage of 0.197 while under-reserving 61%. Migration intervals internally inconsistent in sign. CCAR regret rank-correlated with coverage at -0.976 and uncorrelated with accuracy. This model knows how to fit. It does not know what it does not know, which is the one thing a model risk function will not waive.

### Reproducibility Is Near-Perfect, Unlike the Hosted Rows

Three CCAR instances were run twice, once in the three-instance run and again inside the eight. Two of the three reproduced **bit-identically**, to every digit of the regret and the same call count:

| CCAR instance | First run | Second run | Calls |
| --- | --- | --- | --- |
| 1 | 0.010952054156700877 | 0.010952054156700877 | 27, 27 |
| 2 | 0.1536092188756754 | 0.1536092188756754 | 31, 31 |
| 0 | 0.08701395118909286 | 0.07517589998792479 | 59, 46 |

That is a sharp contrast with the archived hosted rows, where re-running the same model on byte-identical instances moved cells by 7.4x and the reproducibility study found swings up to 30x ([detail](limitations.md#run-to-run-reproducibility)). Greedy decoding on this server is deterministic, so an agent loop over it is deterministic too, and the usual run-to-run noise disappears.

The one instance that diverged is the one whose first run hit the token limit, at 59 calls against 46. The divergence therefore originates in the sandbox rather than the model: the agent writes and runs its own Python, and anything time-dependent or unseeded in that code changes the tool output, which changes the next prompt and forks the trajectory. Determinism in the server does not buy determinism in the loop, but it removes the model as a source of variance, which makes a single local run worth more than a single hosted run.

## The Binding Constraint Is Context

Peak prompt length per sample, measured over the four most recent archived runs of each task, local runs excluded. Prompt size is `input_tokens` plus the cached halves, because a provider that caches reports only the uncached remainder in `input_tokens` and reading that field alone understates a long agent loop by orders of magnitude.

| Task | Median peak context | Max peak context | Runs on 48 GB |
| --- | --- | --- | --- |
| Two-body | 38,536 | 82,791 | yes |
| CECL | 82,251 | 418,234 | yes |
| Migration | 91,925 | 168,810 | only with a token limit |
| CCAR | 108,312 | 604,889 | yes, one of eight truncated |
| Ballistic | 175,942 | 440,026 | no |
| Three-body | 181,814 | 511,297 | no |
| Quantile | 264,388 | 331,177 | no |

Against that, the measured ceiling for this model on this machine is **113k to 120k tokens**. Past it the server does not degrade, it dies: the worker thread exits and every subsequent request returns `404 {"error": "generation thread died"}` while `/v1/models` keeps answering 200, so a health check on the models route reports a healthy server that cannot generate.

### How the Ceiling Was Measured

Three times, because the first two answers were wrong.

A one-shot prefill probe reached 149,426 tokens successfully and failed at 250,000, which suggested a ceiling somewhere between. That was confounded: the earlier prompts in the same probe were still held in the prompt cache, so the 250k call ran with roughly 212k already resident. The number was a total-KV budget, not a per-prompt ceiling.

Growing a **single** conversation in 30k-token chunks then served 119,326 tokens and died on the next call at approximately 149k, which is lower than the cold 149,426 that had succeeded. So the two measurements disagree, and the one that matters for an agent is the lower one, because an agent loop is exactly a single growing conversation.

The live run settled it. Migration instance 1 grew in exact 3,260-token increments, reached a prompt of **113,021 tokens**, and killed the worker on the next call. That is the operational ceiling: not a published spec, not a flag, just where this model on this machine stops.

The arithmetic behind it, with **low confidence** on the coefficient: the 4-bit 35B holds roughly 19.5 GB of weights, and KV plus activations cost roughly 0.12 to 0.15 GB per 1k tokens of context. `vmmap <pid> | grep -i "physical footprint"` is the way to read this on macOS, since Activity Monitor has no peak column and `phys_footprint` counts Metal buffers in unified memory where plain RSS does not. Observed during a heavy run: `Physical footprint: 29.2G`, `Physical footprint (peak): 38.5G`.

### The Context Numbers Are Behavior, Not Requirements

The median peaks above are what hosted models used, not what the tasks demand, and the difference is large. Qwen3.6 completed CECL with a peak prompt of **20,502 tokens** against a hosted median of 82,251, because it wrote long single scripts instead of iterating in many short tool calls. It spent 549k output tokens on instance 0 and only 634k prompt tokens in total.

That cuts both ways. It means a 176k median does not prove ballistic needs 176k, and a model with a different working style might fit it in half that. It also means a local model's context demand cannot be predicted from the hosted column at all.

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

## A Token Limit Converts a Crash Into a Score

The useful mitigation turned out to be a limit on the Inspect side, not the server side. The question is which limit discriminates a healthy long run from a runaway one, and output tokens do not: a healthy two-body instance scored at 268,492 output tokens while the migration instance that crashed the server was at 275,120. Total tokens do discriminate, with the healthy maximum at 2,108,703 against 3,014,518 on the crashed run.

`--token-limit 2500000` therefore trips at roughly 100k of context, below the ceiling, and turns a fatal server crash into a recorded `sample.limit` on a sample that still gets scored. Migration instances 0 and 1 both tripped it, at peak prompts of 93,129 and 106,285, as did CCAR instance 5 at 80,827, and all three runs completed with status `success` where the unguarded migration attempt the night before had killed the server mid-sample. Three of fourteen samples across the four tasks were truncated by it, and only one of those three sets its task's cell.

The cost is that a truncated cell is an upper bound rather than a measurement, exactly as it is for the archived minimax migration row, and that **nothing in the score distinguishes the two**. `completion`, `matrix_quarters` and `fit_years` all read as complete on the truncated instances. Only `sample.limit` on the eval log shows it, which is the same trap recorded under [A Time-Limited Run Still Produces a Score](limitations.md#a-time-limited-run-still-produces-a-score).

## What Would Close the Gap

Four of seven tasks are blocked, and the fix is not a better model. Going from the 35B-A3B to a 27B at the same quantization frees roughly 5 to 6 GB of weights, which at 0.12 to 0.15 GB per 1k buys roughly **40k to 50k more context**, for a ceiling near 155k to 170k. That brackets ballistic (176k median) from below, misses three-body (182k), and is nowhere near quantile (264k). **Moderate confidence on the direction, low on the magnitude**, since the coefficient was revised three times.

More memory is the lever that actually works, because the ceiling is close to linear in whatever is left after the weights. The other lever is to cut context demand rather than raise the ceiling: the agent loop's context is dominated by accumulated tool output, so trimming or summarizing it would move every blocked task at once, and it would change what the archived columns mean, so it is a change to the harness rather than to the serving setup.

## Candidates Still To Test

Queued, all at 4-bit on the same 48 GB machine:

- Qwen3.6-27B
- Qwen3.8-27B
- Gemma 4 26B A4B

All three are smaller than the 35B-A3B tested, so all three should raise the context ceiling and lower the capability margin. Given that the three runnable tasks already show miscalibration rather than a modelling failure, and that coverage is the component that collapses, the thing to watch on a smaller model is interval coverage rather than the point estimates.

The protocol for each: `-T n_instances=3 -T seed=1 --max-tokens 16384 --max-connections 1 --token-limit 2500000 --time-limit 10800`, eight instances for CCAR, and a transcript saved to `runs/` per sample. Report the ceiling measurement alongside the cells, because on this hardware the ceiling is the result.
