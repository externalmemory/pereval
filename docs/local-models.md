# Running the Suite on Local Hardware

The question here is not how a local model ranks. It is whether a model running on one desktop machine can **complete** the tasks at all, and if not, what stops it. That is a different question from the one the score table answers, so these results live here and no local model appears in the main table. A row there needs a cell in all eight columns to earn a mean rank.

The short answer, after two models and three context sweeps: **all eight tasks run on 48 GB**, and the thing that looked like a hardware ceiling was a server default. `mlx_lm.server` prefills a prompt in chunks of `--prefill-step-size`, and lowering it from the default 2048 to 256 moved the measured ceiling from 89,601 tokens to past 298,658 on the same machine, the same model and the same memory. On six of the eight tasks what is left is a capability question rather than a deployability one, and the capability that fails is interval calibration. On the two heaviest it is still both: real agent loops survived 216,198 tokens and died at both 231,531 and 199,374, well short of what the probe reported and not reproducible to better than about 15%, and migration has only ever finished with its instances truncated.

An earlier version of this document concluded the opposite: that the binding constraint was context rather than capability, that the limit was set by RAM, and that four of the tasks could not run at all. Every part of that was wrong. The sections below keep the measurements that refuted it rather than quietly replacing the conclusion.

## Rationale

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

That table covers the three rows in the results below, all served by `mlx_lm.server`. A fourth model is served by LM Studio on the same machine and has its own setup, findings and caveats under [A Second Serving Stack, LM Studio Instead of MLX](#a-second-serving-stack-lm-studio-instead-of-mlx), because nothing about the server behaviour carries across.

### The Weights Are Pinned By Commit, Not By Name

A Hugging Face repo name does not identify a set of tensors. `mlx-community` and `unsloth` re-quantize in place, so "the same model" re-downloaded later can be different weights, and a published cell measured against the old ones stops being reproducible without anyone touching this repository.

That is not a hypothetical. Of the five models pulled to this machine, one moved during the project: `mlx-community/Qwen3.6-27B-OptiQ-4bit` went from `7575c79a` to `3413c683` on 2026-10-30, after it was downloaded here. No published cell rests on it, so it cost nothing, but the next one might.

Every revision actually used, verified against `main` on 2026-11-09, and the Nemotron row on 2026-11-16:

| Model | Revision used | Still `main`? | Repo last modified |
| --- | --- | --- | --- |
| `mlx-community/gemma-4-26B-A4B-it-qat-4bit` | `0e3cbab38ce568cf6e23543010d08d03b731910c` | yes | 2026-06-05 |
| `mlx-community/Qwen3.6-35B-A3B-4bit-DWQ` | `73c707af4243243b18193444467872d20cff9399` | yes | 2026-04-17 |
| `unsloth/gemma-4-26B-A4B-it-qat-GGUF` | `7b92b5b28818151e8669af2e45e88d6086f490dd` | yes | 2026-07-17 |
| `mlx-community/Qwen3.6-27B-OptiQ-4bit` | `7575c79af388aa16ce4722fe6c3fd0d3a8e964d2` | **no**, now `3413c683` | 2026-10-30 |
| `mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit` | `55ac8c89261109b36c04371cd3f479a4594208c8` | yes | 2026-08-11 |

The first row is the one that matters: it backs the `gemma-4-26B-A4B (local)` row of the main table, and its local weights have since been deleted from the machine to reclaim disk. The row is still reproducible, because that revision is still what `main` points at and the repo has not changed since June. The Nemotron weights were reclaimed the same way, and that row has the strongest provenance of the five: the repo was last modified on 2026-08-11, three months before the runs, and had not moved when checked again a week after them, so `main` was the same set of tensors on both sides of the measurement. Pass the revision explicitly rather than trusting the name:

```bash
hf download mlx-community/gemma-4-26B-A4B-it-qat-4bit \
  --revision 0e3cbab38ce568cf6e23543010d08d03b731910c
```

Since `Qwen3.6-35B-A3B-4bit-DWQ` has not moved since April, the greedy October runs and any re-run at corrected sampling use identical tensors, so the sampler and `--prefill-step-size` are the only variables between them.

Inspect reaches any OpenAI-compatible endpoint through `openai-api/<service>/<model>`, where `<service>` names the `<SERVICE>_BASE_URL` and `<SERVICE>_API_KEY` pair to read. The base URL must stop at `/v1`, because Inspect appends the route itself. Model ids containing slashes survive, since only the first path segment is stripped to find the service.

Everything in the plumbing worked on the first try: tool calling through the Inspect agent loop, the Docker sandbox, reasoning returned as a proper content block, and the transcript archive. Nothing in the harness needed changing to point it at a machine on the LAN.

## Results

All three local rows now complete all eight columns on the archived convention: one draw per instance over the same instances every hosted row uses, three instances per task and eight for CCAR, with quantile as three paired single-instance runs on the archived seeds. Their cells are therefore plain maxima and need no matched-convention adjustment.

| Task | Qwen3.6-35B-A3B | gemma-4-26B-A4B | Nemotron-3.5-Lightning | Column context for the Qwen cell |
| --- | --- | --- | --- | --- |
| CCAR | **0.366** | 2.9 | 0.828 | mid-field, between deepseek-v4-flash-0731 (0.30) and Claude Haiku 4.5 (0.37) |
| CECL | 0.001945 | **0.000571** | 0.00905 | between nemotron-3-super (0.00056) and ling-3.0-flash (0.0087) |
| Migration | **1.267** | 6.746 | 7.648 | worse than the degenerate answer (1.000) and than the naive baseline (0.765) |
| Ballistic | **14** | 58 | 60 | between Kimi K3 (14) and nemotron-3-ultra (16) |
| Two-body | 1193 | **1138** | 3431 | worse than the naive baseline (17), better than the degenerate answer (2861) |
| Three-body | 2925 | **166** | 1526 | inside the degenerate answer (3019) only just, and worse than the naive fit (332) |
| Flyby | 916 | 4353 | **681** | worse than the degenerate answer (138) by nearly seven times |
| Quantile | 3.8e12 | 3.6e6 | **0.077** | last in the column, six orders of magnitude past gemma |

Qwen takes three of the eight cells, gemma three and Nemotron two. The mean ranks are 11.06, 11.75 and 11.50, against the naive baseline's 10.75, so **all three local rows are now below the baseline**. gemma took none of the eight when its row was a maximum over mixed decoder settings and takes three now that it is sampled throughout, which is a statement about what the old row's provenance was costing it rather than about the model changing. The split does not follow the statistical and physics axes: Qwen wins CCAR, migration and ballistic, gemma wins CECL, two-body and three-body, and Nemotron wins the flyby and quantile.

**The best local result in the table is gemma's three-body 166, which places 4th of fifteen**, behind Claude Opus 5.5 (0.039), Kimi K3 (3.3) and minimax-m3.1-flash (164), and ahead of deepseek-v4-flash-0731 and the naive baseline. A 26B model at 4-bit on a Mac Mini lands 1% behind minimax-m3.1-flash, which is the second best row in the table overall. One cell is not a result, and the same row is last of fifteen overall, but it is the clearest evidence on this page that the ceiling for local hardware on these tasks is not set by parameter count.

**The medians tell a different story from the cells, and the gap between them is the point.** Qwen's per-column medians are 0.134, 0.00015, 0.482, 12.1, 2.34, 331, 330 and 0.075. Seven of the eight beat gemma's published cell, the exception being three-body, where Qwen's median of 331 is worse than gemma's cell of 166, and most would place mid-table. The published row does not, because three of its twenty six instances blew up numerically and a maximum convention promotes exactly those three. This is not an argument against the convention, which is the whole premise of the suite, but it is the clearest demonstration in the repository of what a worst-case cell does and does not describe.

Pooling all nine same-convention migration instances per model, Qwen is genuinely the better model on that column (Mann-Whitney p = 0.020), and the difference is not visible in the cells: 6.746 against 5.453 on the two worst draws is no difference at all. Where the two models differ unambiguously is in finishing at all. Qwen submitted on 9 of 9 migration instances and on all 26 instances of the full row; gemma submitted on 5 of 9, scoring the degenerate 1.000 by default on the other four (Fisher exact p = 0.082, suggestive rather than significant at this sample size).

**The instance count is not a detail.** CCAR was first run on three instances by mistake, giving a maximum of 0.154. On the full eight it is 0.313 for that earlier partial run, so the short run understated the cell by a factor of two and would have placed the model three ranks too high. A maximum over fewer draws is biased low, and on this column the bias was large enough to change the conclusion from "near-competitive" to "mid-field".

**What the comparison set is.** The ranked rows in the main table are mid-tier open-weight models plus Claude Haiku 4.5 and Claude Opus 5.5, selected on cost and free-endpoint availability rather than on capability. That makes the table the right yardstick for a local candidate, since most rows are the same class of model, and the wrong yardstick for absolute task difficulty: nothing here establishes that these tasks are hard for the strongest models available, only that they discriminate sharply within this tier.

Size is not the axis they respond to. The largest model in the table, nemotron-3-ultra at 550B total and 55B active parameters, scores 1.214 on migration, which is worse than the degenerate answer, and 2429 on two-body against a degenerate 2861. A local candidate at 26B to 35B is therefore not disqualified by parameter count, and a larger local model would not be qualified by it either.

### The Failures Are Specific, Not Diffuse

**Uncertainty quantification is the systematic failure, not point estimation.** Across the orbital columns Qwen's intervals are far too narrow at every difficulty. On the flyby, all three instances score worse than the degenerate answer (181 against 138.5, 330 against 127.0, 916 against 107.8) with interval coverage of 11.4%, 6.0% and 6.1% against a nominal 90%. Ballistic covers 38% to 57% and still beats the degenerate by four to nine times, because the point estimates are good enough to carry it. Three-body covers 90%, 1% and 57% on its three instances. A model that can locate the answer and cannot say how sure it is will pass the columns scored mostly on accuracy and fail the ones scored on calibration, which is exactly the pattern.

**Three instances of twenty six blew up numerically, and they set three of the eight cells.** The quantile cell is the clearest case. On seed 1, one block of one hundred fit a Student's t with an unconstrained location, the optimizer diverged to `loc = 15824746916060.2`, and that block's q99 came out at 3.76e12. The same seed's q90 was 0.0944, essentially sound, and the other two seeds scored 0.061 and 0.075. The agent's own verification step checked row count, column names, the absence of NaNs and that q95 fell inside its interval, and never checked magnitude. Two-body instance 2 (1193 against 1.73 and 2.34) and three-body instance 1 (2925 against 76.9 and 331) fail the same way.

**gemma's failure is different and worse: it often submits nothing.** Four of its nine migration instances never produced an answer. That is a failure of the agent loop rather than of the statistics, and it is why four of those nine draws score the degenerate 1.000 by default rather than on their statistics.

### Reproducibility Was Near-Perfect, and That Was an Artifact

Three CCAR instances were run twice during the early greedy work, once in a three-instance run and again inside the eight. Two of the three reproduced **bit-identically**, to every digit of the regret and the same call count:

| CCAR instance | First run | Second run | Calls |
| --- | --- | --- | --- |
| 1 | 0.010952054156700877 | 0.010952054156700877 | 27, 27 |
| 2 | 0.1536092188756754 | 0.1536092188756754 | 31, 31 |
| 0 | 0.08701395118909286 | 0.07517589998792479 | 59, 46 |

That looked like a sharp contrast with the archived hosted rows, where re-running the same model on byte-identical instances moved cells by 7.4x ([detail](limitations.md#run-to-run-reproducibility)). It was not a property of local serving. It was greedy decoding, which `mlx_lm.server` defaults to and which nobody chose. Switching the local rows to sampling removed most of it but not all, for a second reason given in the next section. The published local rows carry the same run-to-run noise as every hosted row, and on migration they carry more: two Qwen runs at near-identical samplers produced worst cells of 1.267 and 5.453, a factor of four apart.

The one instance that diverged even under greedy decoding is the one whose first run hit the token limit, at 59 calls against 46. The divergence originates in the sandbox rather than the model: the agent writes and runs its own Python, and anything time-dependent or unseeded in that code changes the tool output, which changes the next prompt and forks the trajectory. Determinism in the server never bought determinism in the loop.

### Identical Transcripts Across Runs Are a Server Artifact

**Setting `temperature: 1.0` does not guarantee that two runs of the same instance are two draws.** Hashing the concatenated message text of all 160 archived local sample transcripts finds seven groups that are bit-identical. Two are the greedy CCAR pairs above. Five come from runs that sent `temperature: 1.0`:

| Task | Instance | Messages | Runs that are bit-identical |
| --- | --- | --- | --- |
| CECL | instance-0-baseline | 500 | 2026-10-30, 11-02, 11-03, 11-04 |
| CECL | instance-1-adverse | 500 | 2026-11-03, 11-04 |
| Migration | instance-0 | 500 | 2026-11-05, 11-07 |
| Migration | instance-1 | 492 | 2026-11-05, 11-07 |
| Migration | instance-2 | 2 | 2026-11-08, 11-11 |

The last row is a crash two messages in and is not a run. The other four are complete agent loops of 492 to 500 messages reproducing to the byte, which sampling at temperature 1.0 cannot produce.

The cause is in the server, and it is a close cousin of the greedy default. In `mlx_lm` 0.32.2, `server.py` seeds the RNG only when the request body carries a `seed` field, and Inspect sends none. Nothing anywhere else in the package reseeds at model load. So MLX's global RNG runs from whatever state the process started in, and **the first conversation served after a server restart draws the same stream every time.** That is exactly where these duplicates sit: each is the first eval of a row on a freshly restarted server, and within one eval the determinism carries into the second instance as well.

One link in that chain is read from the source rather than measured, namely that MLX's default global seed is fixed at import rather than drawn from entropy. The decisive test is two identical requests to a freshly restarted server, which has not been run here because it needs the machine idle.

The consequence for every count on this page is that **repeats of one instance are not independent draws unless the server generated something else first**, and any tally of draws has to dedupe by transcript hash rather than by run. One of the five archived submitted draws of gemma's migration instance 0 is such a duplicate, which is why [the gemma migration spread](#the-gemma-rows-individual-cells) is quoted over four draws rather than five.

## The Decoder Settings, And Where They Differ Between the Rows

`mlx_lm.server` defaults `--temp` to **0.0** and Inspect sends no temperature unless one is configured, so the early local work here decoded greedily while every hosted row ran at its provider's default. That asymmetry sat in the setup unnoticed, and the three rows resolved it differently.

Verified rather than assumed: four identical prompts at `temperature 1.0, top_p 0.95, top_k 64` returned four different sentences, and the same prompt at the server's default returned the same sentence twice. The request body's temperature is honoured, and the default really is greedy.

**The Qwen row is one sampler throughout**, Qwen3.6's own recommended preset: `temperature 1.0`, `top_p 0.95`, `presence_penalty 1.5`, `top_k 20`, `min_p 0.0`. Inspect forwards temperature, top_p and presence_penalty natively; `top_k` and `min_p` are not forwarded by the OpenAI-compatible provider and must ride in `extra_body` or they are dropped silently.

**The gemma row was a maximum over two different decoder settings, and is not any more.** It is now sampled throughout at `temperature 1.0`, `top_p 0.95`, `top_k 64` and nothing else, one draw per instance, taken from the most recent complete sampled run of each task, with CECL assembled from three single-sample runs. The row it replaced mixed ten greedy runs with eleven sampled ones and took maxima across both, which no other row in the table did.

Seven of the eight cells moved: CCAR 0.44 to 2.9, CECL 0.001948 to 0.000571, migration 6.179 to 6.746, two-body 3377 to 1138, three-body 2550 to 166, the flyby 1327 to 4353 and quantile 0.078 to 3.6e6. Ballistic moved from 59.3197 to 58.3283, which the table shows as 59 and 58.

**An earlier version of this page predicted that the restriction would move only three cells**, to CCAR 0.42, quantile 0.074 and two-body 3177. That was right about the sampled runs in hand when it was written, which were all from late October, and a second sampled pass in November changed every part of the answer: the restriction moves seven cells, and the quantile prediction was wrong by seven orders of magnitude. A forecast of what a convention change will cost is worth no more than the draws available when it is made.

**The replacement is not an improvement, it is a different model.** Three-body improves 15x and two-body 3x while the flyby gets 3.3x worse and quantile goes from 0.078 to 3.6e6, and the mean rank moves from 11.62 to 11.75, which is last of the fifteen ranked rows.

### Sampling and the Presence Penalty

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

`mlx-community/gemma-4-26B-A4B-it-qat-4bit` at revision `0e3cbab38ce568cf6e23543010d08d03b731910c`, under `mlx_lm.server` 0.32.2 with `--prompt-cache-size 1`. Seven columns were served at `--prefill-step-size 256`; two of the three CECL draws were served at 64, for the reason given under [The CECL Column Cost Sixty-Nine Hours of Crashes](#the-cecl-column-cost-sixty-nine-hours-of-crashes-and-then-twenty-five-minutes).

**Its CCAR 2.917 is now worse than the degenerate answer**, which the cell it replaced was not. Instance 7 predicted all nine points and put intervals of mean width 0.714 around a default-rate path it missed by 0.255, for coverage of 0.095, against an oracle that scores 0.085. A mean width of 0.71 on a quantity bounded by 1 is not a narrow-interval failure; it is a wide interval in the wrong place, which is the one failure mode the Winkler score punishes from both sides at once.

**Its migration 6.746 is the second worst cell in the suite**, behind the local Nemotron row's 7.648, and it fails six of the sixteen checks including `matrices_readable` ([which six, and what family they are](tasks/migration.md#results)). The cell is set by instance 0 of the run of 2026-11-14, which submitted (`completion` 1.0) rather than running out of room.

That byte-identical instance has now been run seven times under sampling. Discarding one bit-identical repeat as not a draw ([why](#identical-transcripts-across-runs-are-a-server-artifact)), its independent submitted draws are **0.315, 0.643, 0.976, 6.179 and 6.746**, a spread of 21.4x, and three of the five are better than the degenerate 1.000 rather than worse. Two further runs produced no submission at all. The conclusion the old cell supported survives the new one unchanged: the cell describes the tail of this model's behaviour on one instance rather than its standing on the column, and the 0.315 draw would place third of fifteen, between Kimi K3 (0.301) and GLM-5.1 (0.523).

Neither truncation nor a transport defect explains it. A separate serving path was tried to rule out the latter: `mlx_lm.server` silently discards a tool call whose arguments its `gemma4` parser cannot parse, 9 of 100 attempts in the archived runs, and llama.cpp's grammar-constrained parser removes that defect completely (853 model calls, zero discarded). It did not improve the task.

**Its ballistic 58.33 is the score of a straight line**, which is the cleanest single explanation of a published cell on this page. The submitted code fits `y = a + b*x` per category, while the naive baseline fits a per-category parabola and scores 21.77, and the rows at the top of the column fit a power law with a free exponent between 2.0 and 3.3. The cell is not a model failing to compute; it is a model choosing the bottom rung of the functional-form ladder, and the column pricing that choice at 2.7x the baseline. The same value, by the same recipe, is what the local Nemotron row submitted on that instance.

**Its flyby 4353 is a total coverage failure**, set by instance 1 at coverage **0.000**, with intervals of mean width 17.4 placed around a trajectory missed by 117.2. The cell it replaced failed the same way by the opposite route, coverage 0.00055 at a near-zero width. Narrow and wrong, or wide and wrong, both score as not knowing where the object is.

**Its quantile 3.6e6 is a single blown-up draw, and it is the second one in this table.** Seed 3 reports pinball regret 3,588,379 against a degenerate 0.1149, with the damage escalating by tail level: 288 at p90, 8,439 at p95 and 3,579,653 at p99. The other two sampled seeds scored 0.0765 and 0.2558, and the 0.0765 is the moment-matched normal reference's score to four decimals, the same recipe the local Nemotron row submitted on all three of its instances. So both local MoE rows now carry a quantile cell set by one numerically divergent draw out of three, which is the same failure mode twice in two unrelated models and so a property of the task's tail estimation rather than of either model.

The consequence is not the same for both, though, and that is worth separating. Qwen's median of 0.075 would place **3rd of fifteen** in that column, so for Qwen the blowup is the entire story of the cell. gemma's median of 0.2558 would place **14th**, behind GLM-5.1 and still worse than the naive baseline's 0.14, so for gemma the blowup costs one rank and the underlying tail estimation is weak on its own.

**Its three-body 166 is by a wide margin the best-calibrated cell in this row**, at coverage 0.900 against a nominal 0.90, mean width 125.2 and a point error of 33.4, where the row's other interval-scored cells cover 0.095, 0.000 and 0.300. It is quoted here because the rest of this page is a catalogue of coverage collapse, and one cell in one column got it exactly right.

**One column now carries a recorded exception to the rule that a cell is reported only if none of its runs failed outside the agent's control.** CECL's three draws come from three logs, and in one of them the other two samples ended with the server returning `{'error': 'generation thread died'}`. The draw that contributes to the cell completed and scored cleanly, so the cell is kept with the failure recorded. The migration column carried the same exception under the old row and no longer does: its cell now comes from a run in which all three samples completed without error.

### The Qwen Row's Individual Cells

`mlx-community/Qwen3.6-35B-A3B-4bit-DWQ` at revision `73c707af`, untouched since 2026-04-17, under the same server and flags. Nine evals back to back, 14h44m, every one exiting 0: twenty six instances, all of which submitted, zero dropped tool calls, zero API errors, and three `max_tokens` runaways, all three in CECL.

**Nothing in this row was context-limited.** The model's `max_position_embeddings` is 262,144 and the highest peak input anywhere in the row was 124,380 tokens, on three-body instance 2. Quantile, which the hosted rows reach at roughly 264k and which was expected to be the one unreachable column, peaked at 46k to 58k: that figure is a property of how hosted models approach the task, not an intrinsic requirement of it.

**Its quantile 3.8e12 is a single diverged optimizer**, described under failures above. It is published as measured, on the convention this suite reports, and it is the cell most worth reading alongside that column's median of 0.075.

### The Nemotron Row's Individual Cells

`mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit` at revision `55ac8c89`, 30B total and 3B active. It is the only row in the table measured at its own `generation_config.json` and nothing else, `temperature 1.0` and `top_p 0.95` with no `top_k`, `min_p` or presence penalty, which is the local equivalent of running a hosted row at its provider's default.

**All eight of its columns come from logs with no sample error**, which neither other local row can claim.

**Its migration 7.648 is the worst cell in the suite**, and it is the most expensive single sample in the archive. Instance 0 made 246 model calls, peaked at 136,305 tokens of context and submitted; the three-sample run behind it moved 31.4M input tokens. Its two sibling instances scored 0.420 and 0.883, both better than the degenerate answer, so the column's worst cell sits beside two draws that are unremarkable, on one model, in one run.

**Its ballistic instance-0 draw matches gemma's published ballistic cell to fifteen significant digits**, 58.32831841879476 from both, and the submitted code says why without any need for a coincidence. Both fitted a per-category ordinary least-squares **straight line** and built the textbook t-based 95% prediction interval around it, `sigma * sqrt(1 + 1/n + (x - xbar)**2 / Sxx)` at `stats.t.ppf(0.975, n - 2)`. gemma reached the coefficients through `np.linalg.lstsq` on `column_stack((ones, x))` and Nemotron through the closed-form `b = Sxy / Sxx`, which is one estimator by two routes: the regrets agree to every digit the record carries and the mean widths differ by a single unit in the last place, 0.6067844736556112 against 0.6067844736556114. That last-place difference is the evidence that these are independent implementations rather than a copied artefact.

A deterministic estimator on a fixed dataset returns the same answer to whoever picks it, so a shared value here is the expected result and not a defect. What the shared values do document is the **resolution** of the column: ballistic has a discrete ladder of textbook recipes, and any two rows on the same rung are indistinguishable by construction. The archive has at least five such values on instance 0 alone, and they are different recipes rather than the same one: the pair at 12.420615385817205, deepseek-v4-flash and hy3, got there through per-category `np.polyfit(x, y, 2)` with a residual-standard-deviation interval, a rung above the straight line ([the same point, made on a different pair](limitations.md#mean-rank-is-computed-from-the-cells)).

**Its quantile 0.0765 is the best local cell in that column by six orders of magnitude**, and the only local quantile cell not set by a divergent optimizer. It is also, exactly, the moment-matched normal reference estimator's score: all three of its draws match that baseline on every statistic the scorer records, and on one instance they match on coverage and spread as well ([detail](tasks/quantile.md)). The cell measures which textbook recipe the model picked rather than how well it estimated a tail, and the recipe it picked is the strongest one in the reference set. Its flyby 681 is likewise the best of the three, though still five times the degenerate answer.

**Its serving numbers are missing, and that is a lesson rather than an oversight.** The weights were reclaimed before anyone thought to probe decode speed, prefill speed or the context ceiling, so filling those cells now means re-downloading 17.8 GB and restarting the server on a machine that is running another row. The 136,305-token figure quoted in the candidates table is the largest context the agent loop actually reached, which is a floor on the ceiling and not a measurement of it.

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

### Memory Arithmetic

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

### Measuring the Ceiling

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

## Throughput

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

## The CECL Column Cost Sixty-Nine Hours of Crashes and Then Twenty-Five Minutes

Completing the sampled gemma row needed one clean draw on each of CECL's three instances. Instance 0 landed on 2026-11-13. Instances 1 and 2 took four more days, five crashed attempts and 69.2 hours of machine time, and then both landed inside twenty-five minutes. One of the five crashes was on instance 0, in a sweep that took the other two down with it at zero model calls.

| Attempt | Instance | Calls | Peak context | Duration | Outcome |
| --- | --- | --- | --- | --- | --- |
| 11-13 05:02 | 1 | 171 | 206,188 | 15h01m | crash |
| 11-15 10:10 | 0 | 114 | 192,481 | 8h42m | crash |
| 11-15 19:15 | 1 | 158 | 212,734 | 18h59m | crash |
| 11-16 14:34 | 2 | 124 | 199,500 | 12h35m | crash |
| 11-17 03:15 | 1 | 130 | 184,205 | 13h53m | crash |
| 11-17 18:27 | 1 | **5** | **17,700** | **9m** | clean |
| 11-17 18:37 | 2 | **11** | **20,770** | **16m** | clean |

Three further samples recorded zero model calls, because they were siblings in a run whose server had already died and failed fast through their retries. The crash signature is always the same: the server returns `{'error': 'generation thread died'}` and the worker is gone.

**These eleven samples reproduce, on a second task and with a much larger sample, what [The Probe Ceiling Overstates What an Agent Loop Reaches](#the-probe-ceiling-overstates-what-an-agent-loop-reaches) already concluded from three migration runs: there is no single survival ceiling.** Pooling every gemma CECL sample ever run, no sample peaking below 148,000 tokens has ever crashed, 0 of 6, while 8 of the 11 that went above it did (Fisher exact p = 0.009), so context is a strong predictor. It is not a threshold. One instance-1 run reached **215,446 tokens and finished**, higher than any of the five crashes above, while another died at 184,205. Across both tasks the archive now holds ten deaths spanning 147,973 to 231,531 tokens and four survivals spanning 150,763 to 216,198, and the highest survival sits above eight of the ten deaths. No figure here can be quoted as a safe maximum, the 298,658 probe included.

**`--kv-bits 8` is not available for this model at all**, which is the one mitigation that looked obvious. See [KV Quantization Does Not Help](#kv-quantization-does-not-help): the flag raises `NotImplementedError` before the server will serve a request.

**The two clean draws did not clear the wall, they went around it.** They took 5 and 11 model calls where the four sampled attempts before them on the same byte-identical instances took 124 to 171, and they peaked at a tenth of the crash band. The deployability problem is untouched: a long-path draw on this task on this hardware still cannot finish, and the cell exists because two draws happened to be short.

**The cell's value is not an artifact of that, though.** Two of the crashed instance-1 attempts had already written a submission to disk when the server died, and `score_on_error` salvaged them at 0.002001 and 0.000535. Those are inadmissible as clean draws, but they bracket the 0.000571 that the short path produced, so the short trajectory did not win the cell by answering an easier question. A greedy draw from 2026-10-27 points the same way: it also finished short, 25 calls at a 19,313-token peak, and scored 0.000574, which is 0.6% from the sampled short draw's value. Both serving configurations are recorded rather than reconciled: instance 0 was served at `--prefill-step-size 256` and the two short draws at 64, and since neither short draw came near the ceiling, the smaller step size earns no credit for them.

## KV Quantization Does Not Help

`--kv-bits 8` is the obvious lever for the memory ceiling. On gemma it cannot be used at all, and on Qwen, where it can, it costs more than it buys.

**On `gemma-4-26B-A4B` the flag is refused by the architecture.** The server raises `NotImplementedError: RotatingKVCache Quantization NYI`. Of that checkpoint's 30 layers, 25 are `sliding_attention` with a 1024-token window and get a `RotatingKVCache`, whose `to_quantized` raises unconditionally in `mlx_lm` 0.32.2, so no amount of flag tuning reaches a working server. The irony is in the arithmetic: with 8 KV heads at head_dim 256, those 25 rotating layers are capped at 1024 tokens each and hold 0.21 GB in total, while the 5 `full_attention` layers that grow without bound hold 8.7 GB at a 212,734-token context. The flag is blocked by the layers that were never the problem.

The A/B below was run on Qwen, which has no sliding-window layers and accepts the flag. Greedy decoding on this server is bit-reproducible, so repeated calls in one arm give an identical hash and the noise floor is exactly zero. That makes the A/B clean.

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

**It is not truncation and it is not the server.** Four of 248 calls hit `max_tokens`; the rest stopped normally at a median of 1,692 tokens. Every POST returned `HTTP/1.0 200 OK`. The model produces fluent, normal-length prose, `basic_agent` re-prompts it because there is no tool call to execute, and the cycle repeats at two to twenty-six minutes a turn until the message limit ends the sample. This is the same family as the repetition loop under [The Decoder Settings](#the-decoder-settings-and-where-they-differ-between-the-rows), and greedy decoding is the obvious suspect, but that is inferred rather than tested. Low confidence on the cause, high confidence on the shape.

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

## A Second Serving Stack, LM Studio Instead of MLX

Everything above was served by `mlx_lm.server`. Recursive's Flint ships as GGUF rather than MLX, so it is served by LM Studio on the same machine, which is llama.cpp underneath. None of the server findings above transfer, because the allocator, the prefill path and the overflow behaviour are all different code. The findings below are that stack's, measured on 2026-11-17 and 2026-11-18, and each is a single probe unless it says otherwise.

| | |
| --- | --- |
| Machine | the same Mac Mini, 48 GB unified memory |
| Server | LM Studio, OpenAI-compatible endpoint on the same host and port the mlx server used, so `MACMINI_BASE_URL` needed no change |
| Model | `recursivesi/flint`, GGUF `Q4_K_M`, Apache 2.0 |
| Shape | 39.8B total and about 2.5B active, 49 layers as 2 dense plus 47 MoE, 256 routed experts with 6 per token and one shared, 32 query heads and 4 KV heads at head dimension 128 |
| Attention | 35 sliding-window layers at a 513-token window, 14 full-attention layers |
| Context | declares 262,144, and **loads at 8,192 unless the load says otherwise** |
| Inspect model string | `openai-api/macmini/recursivesi/flint` |

The shape figures come from the model card by way of aggregator pages rather than from the file served here, so treat them as the basis of the arithmetic below rather than as independently verified.

### The Ceiling Is the Configured Window, Not the Memory

One growing conversation at 10k resolution reached **260,722 tokens served intact**, at turn 26 of 30, with no out-of-memory death and no dead worker. This is the first local model on this page whose full declared window is reachable in a real growing conversation rather than in a probe: Gemma reached 298,658 under a probe but its agent loops died at 231,531 and 199,374, and the gap between those two numbers is the subject of [The Probe Ceiling Overstates What an Agent Loop Reaches](#the-probe-ceiling-overstates-what-an-agent-loop-reaches). Here there is no gap to explain, because nothing died.

The arithmetic says why, and it is the sliding-window geometry rather than the quantization. At fp16 a full-attention layer holds `2 * 4 * 128 * 2 = 2,048` bytes per token, so the 14 full-attention layers hold 28 KiB per token and **7.0 GiB at the full 262,144**. The 35 sliding layers are capped at their own window, `35 * 513 * 2 KiB`, which is 37 MB and rounds to nothing. Against about 24 GB of weights that is 31 GB of 48, which is why it never came close to failing. Gemma, by contrast, held 8.7 GB across 5 full-attention layers at 212,734 tokens, because it has 16 KV heads where this model has 4.

Turn cost is linear in the prompt, fitting `t = 4.3s + prompt / 4,073 tok/s` across all 26 turns: predicted against measured is 36.3s against 35.4s at turn 13, 53.5s against 53.0s at turn 20, and 68.3s against 68.3s at turn 26. The apparent prefill rate therefore rises with context, from 1,491 tok/s on a 10k prompt to 3,819 tok/s on a 260k one, because the fixed 4.3s dominates the small end.

### There Is No Prefix Cache, and Every Turn Pays for the Whole Conversation

That linear fit is itself the finding. A turn served from a prefix cache would prefill only its own new 10k and stay roughly flat; these turns scale with the total, and the implied full-prompt rate is constant. LM Studio does not report `prompt_tokens_details`, so there is no `cached_tokens` figure to read directly, and the timing is the proxy.

The agent loop confirms it at scale. One eight-instance quantile run moved **61,878,964 input tokens against 498,005 output**, a ratio of 124 to 1, and its worst sample moved 45,562,632 input tokens by itself across 338 model calls. Total prefill is quadratic in turn count, so the cost of a long agent loop here is set by how many calls it makes rather than by how deep it goes. This is the one place where this stack is clearly worse than `mlx_lm.server`, which did cache prefixes and reported the hit rate per turn.

### Overflow Truncated Silently Until the Policy Changed

The dangerous finding, and it is a validity problem rather than a performance one. A 280,836-token conversation, past the configured window, originally returned **HTTP 200 after 258 seconds with `prompt_tokens` of 130,499**. It did not error. It discarded roughly half the conversation and answered on the remainder, which is llama.cpp context shift: keep the head, drop half the rest. Four successive turns of a growing conversation all came back pinned near 130,470, so it re-truncated every time.

A sample that overflowed would therefore have been scored on a conversation that had quietly lost half its history, and it would have looked like a completed sample rather than a failure. `score_on_error` cannot catch it, because there is no error.

Setting the Context Overflow Policy to **Stop at Limit** on the machine fixes it. The same request now returns `400 exceed_context_size_error` with `n_prompt_tokens 280836, n_ctx 262144`, in one second rather than 258. Two things worth recording about that setting:

- It is **not a request field**. Sending `context_overflow_policy` and `contextOverflowPolicy` in the body changes nothing; the server ignores unknown fields silently and returns 200. The control, with both fields stripped, behaves identically to the request carrying them.
- Because it is machine-side, **it does not appear in the eval log**, so a run's validity depends on unrecorded machine state. Every run here therefore fires one over-window request immediately before the sweep and records the response beside it, so the log carries its own proof that the policy was active.

### The Backend Is Not Deterministic at Temperature Zero

The same instance was run twice at `temperature=0`, once alone and once inside the eight-instance row:

| | pinball regret | coverage | calls | peak context |
| --- | --- | --- | --- | --- |
| First run | 0.09755739 | 0.540 | 39 | 144,725 |
| Second run | 0.09755739 | **0.720** | 36 | 111,454 |

Identical regret to eight significant figures and a coverage difference of 0.18. MoE routing or batching is the likely cause and neither was tested. Single draws on this stack therefore carry run-to-run variance that greedy decoding does not remove, which is the opposite of the artifact recorded under [Identical Transcripts Across Runs Are a Server Artifact](#identical-transcripts-across-runs-are-a-server-artifact).

**The matching regret is not the determinism evidence, and reading it as such would be a mistake.** Both runs submitted the `type7` answer on this dataset, numerically, so their point estimates came out of a deterministic `np.quantile` call inside the sandbox rather than out of the model. What differs run to run is everything the model actually decided: 39 calls against 36, a peak context of 144,725 against 111,454, and an interval covering 0.540 against 0.720. The claim rests on those three and not on the score.

What the pair does show cleanly is that pinball regret cannot see the interval: one model, one dataset, two runs, the same score to eight digits and materially different intervals. The cross-model version of that argument is in [the quantile task page](tasks/quantile.md).

### What Has Been Measured So Far

Two columns on the published conventions, both on 2026-11-18: quantile as three single-instance runs at seeds 1, 2 and 3, and CECL as three instances under `-T seed=1`. The other six tasks are untouched, so there is no row and no rank.

**Quantile is 0.098 (0.115).** The three draws, each beside the `type7` reference the scorer computes from ground truth on the same data:

| Seed | Dataset | Flint | `type7` on the same data | Ratio | Coverage | Calls |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1835504127 | 0.09755739 | 0.09755739 | 1.0000 | 0.540 | 39 |
| 2 | 2834126987 | 0.06989644 | 0.11375944 | 0.614 | 0.730 | 37 |
| 3 | 1576890651 | 0.11452052 | 0.11491507 | 0.9966 | 0.380 | 25 |

**It is submitting `np.quantile` output rather than estimating a tail.** On seed 1 the two columns agree to sixteen digits and differ only in the last bit, which is a floating-point tie and not a close call. The cell-setting draw on seed 3 improves on `type7` by 0.34 percent. Across all eleven quantile draws taken on this model, on ten distinct datasets, **seven are numerically identical to `type7`** and cover six of those datasets; one more is the 0.9966 above, one is 1.79x worse, and only two carry real information, at 0.614x and 0.641x. It is the third row on this suite to land exactly on a reference estimator in that column, after the two that landed on the moment-matched normal, and the first to land on `type7`.

That also reframes the two-run split above. The point estimates come out of a library call and do not vary; the interval the model reasons about varies from 0.380 to 0.880 across these draws. A column scored on point estimates alone would record this model as mid-table and would be recording numpy's behaviour.

**CECL is 0.00057**, set by the adverse instance exactly as the 10-of-14 pattern below predicts.

| Instance | Regret | Coverage | Mean width | Loss-rate MAE |
| --- | --- | --- | --- | --- |
| 0 baseline | 1.54e-05 | 0.910 | 0.033 | 31.2 bps |
| **1 adverse** | **0.000567046** | 0.691 | 0.053 | 201.7 bps |
| 2 benign | 7.78e-08 | 0.950 | 0.020 | 2.5 bps |

1h53m for 6.70M tokens, 49, 48 and 60 calls, no sample errored and none hit a limit.

**The adverse instance is an attractor too, and the tightest one found anywhere in this suite.** Flint's 0.000567046 sits on gpt-6-luna's 0.000567030, agreeing to five significant figures, with a loss-rate MAE of 201.75 bps against 201.83. Two further rows land in the same place, nemotron-3-super at 0.000561840 and gemma at 0.000571262, so four models on three serving stacks fall inside a 1.7 percent band on one instance and coverage is the only thing that separates them, at 0.675 to 0.691. The published CECL column reads 0.00056, 0.00057 and 0.00057 as three ranked rows at the top of its second group; this makes four samples of one shared answer. It is also the first attractor found outside the quantile column. Whatever that estimator is, it misses the adverse loss rate by about 201 bps with intervals too narrow, which is what failing to condition on the stressed macro path would look like, but the transcripts have not been read and that mechanism is unconfirmed.

**Two deliberate deviations from the protocol paragraph at the end of this page**, both in the quantile draws. The time limit was 86,400 rather than the 5,000 the seed-1 draw used, which never bound, since the three draws took 51, 28 and 31 minutes. And no `--token-limit 2500000` was set, because that limit does not transfer to a backend with no prefix cache: seed 1 alone moved 2,449,208 cumulative tokens and would have died about 2 percent short of finishing.

**An eight-instance quantile run** was made before the convention was checked, and it is kept as a dispersion measurement rather than as a row. Its instances 1 through 7 are datasets no other model has been scored on, and five of its eight samples exceeded the 2,500,000 figure in that protocol paragraph. Read only as spread, those eight draws run 0.0554 to 0.2094 with a median of 0.1226, a factor of 3.8 between best and worst on the same task and the same model. Seven of the eight are also where most of the `type7` ties above come from.

### Two Invocation Traps Found by Running It

Neither is specific to this model, and both cost a run here.

**`cecl` does not pin its instances by default.** Its signature is `seed: int | None = None`, so `SeedSequence(None)` draws from OS entropy and every invocation without `-T seed=1` generates a fresh portfolio. All 81 CECL samples in `logs/` before this one used the three seeds that `SeedSequence(1).generate_state(3)` produces, so the archive is consistent and the one deviation is recorded here. `quantile` is unaffected because its default is `seed=1`.

That matters more than it looks, because the CECL cell is the worst of three scenarios and the scenarios are not equally hard. Taking each row's worst draw per instance, **the cell is set by instance-1-adverse in 10 of the 14 ranked rows**, by instance-0-baseline in 3 and by instance-2-benign in 1. For the ten set by the adverse instance, that instance's regret runs 5x to 537x the same row's baseline regret: 1.6e-05 against 0.000567 for gpt-6-luna, 8.9e-07 against 5.9e-05 for GLM-5.1, 1.61e-05 against 0.00865 for ling-3.0-flash. A draw on the baseline scenario alone understates the cell by one to two orders of magnitude for the typical row, which is the real reason a single-instance CECL run cannot be published, rather than anything about reproducibility.

**`quantile` is three runs of one instance, not one run of three instances.** Every prior quantile log is `n=1` with sample id `quantile-0`. Passing `-T n_instances=8` produces `quantile-0` through `quantile-7`, which are seven datasets outside the comparison set and one that is inside it.

## Remaining Levers

The gap is no longer context, and the fix was never a better model. One server flag moved the measured ceiling from 89,601 tokens to past 298,658, which settles six of the eight tasks outright, so for those the levers that remain are all about the scores. CCAR, migration and CECL are not settled. CCAR and migration reached 216,198 and 231,531 tokens, 72% and 78% of a ceiling that is itself optimistic, and migration crashed the server at that figure and again at 199,374. CECL is the worst of the three and the best measured: eight of its samples have crashed the server between 147,973 and 212,734 tokens, and the two draws that completed the column did so by taking 5 and 11 model calls rather than by surviving a long path ([detail](#the-cecl-column-cost-sixty-nine-hours-of-crashes-and-then-twenty-five-minutes)).

**Sampling is the first lever, and it was set wrong by default.** See [The Decoder Settings](#the-decoder-settings-and-where-they-differ-between-the-rows). Greedy decoding is what put the migration agent into a repetition loop, and it is also the reason the local rows are not strictly comparable with the hosted ones.

**Calibration is the second, and nothing here says it is cheap.** Coverage is the component that collapses, on every task where an interval is scored, on all three local models tested, the one exception being gemma's three-body cell at coverage 0.900. The point estimates stay in a credible range while the intervals are narrow and misplaced, which is a prompting and scoring-feedback problem as much as a model one. Nothing in the serving setup touches it.

**More memory is no longer on the list.** The ceiling turned out to be transient prefill workspace rather than a persistent allocation, so buying RAM buys a smaller multiple of what a flag already gave for free. Moderate confidence: the mechanism is inferred from a 16.8 GiB residual and from the response to `--prefill-step-size`, not from an allocator trace.

**Cutting context demand is still available and still a harness change.** The agent loop's context is dominated by accumulated tool output, so trimming or summarizing it would move every task at once, and it would change what the archived columns mean. That makes it a change to the harness rather than to the serving setup, and out of scope here.

## Candidates Still To Test

Tested so far, all 4-bit on the same 48 GB machine, the first four under `mlx_lm.server` and the last under LM Studio:

| Model | Ceiling at step 2048 | Weights | Decode | Prefill at 10k | Cells |
| --- | --- | --- | --- | --- | --- |
| Qwen3.6-35B-A3B-4bit-DWQ | 113k observed | 19.5 GB | 41 tok/s | 2,453 tok/s | four tasks, one an upper bound |
| Qwen3.6-27B-OptiQ | 39,744 to 49,744 | 20.4 GB | 14 tok/s | 374 tok/s | none, screened out on the ceiling |
| Gemma 4 26B A4B QAT | 89,601 to 99,601 | 15.6 GB | 74 tok/s | 2,100 tok/s | all eight tasks |
| NVIDIA Nemotron 3.5 Lightning 30B A3B | 136,305 reached, not probed | 17.8 GB | not measured | not measured | all eight tasks |
| Flint 39.8B A2.5B, GGUF | 260,722 served, no failure | about 24 GB | 71 tok/s | 1,491 tok/s | quantile and CECL, both on convention |

The Flint row's ceiling is not comparable to the four above it. Those are `--prefill-step-size 2048` figures on `mlx_lm.server`, where the setting was the binding constraint; Flint is served by llama.cpp, which has no such setting, and its figure is the largest prompt a growing conversation served without failing. Its decode and prefill numbers are single probes at short context, and its apparent prefill rate rises to 3,819 tok/s at 260k for the reason given under [The Ceiling Is the Configured Window, Not the Memory](#the-ceiling-is-the-configured-window-not-the-memory).

The Nemotron row is the one entry whose serving numbers are missing, and they are missing for a reason worth recording: its weights were reclaimed before anyone thought to probe it, so filling those three cells now means re-downloading 17.8 GB and restarting the server on a machine that is running another row. The ceiling figure given is not a probe but the largest context the agent loop actually reached, on migration instance 0, which is a floor on the ceiling rather than a measurement of it. The screening question those columns exist to answer was in any case answered by the row itself: the model completed all eight columns without hitting a context wall.

The 27B was screened out before any task ran: the smallest ceiling of the three despite being the smallest model by parameter count, because `OptiQ` mixed precision puts it near 6 bits per weight and its KV geometry is 3.2x the 35B's per token. It is also the slowest of the three by a factor of three on decode, which is the one axis where a local model has no margin to give away.

Still queued:

- Qwen3.8-27B

The thing to watch is interval coverage rather than the point estimates, because that is the component that has failed on all three models measured across the full suite and it is the component a model risk function will not waive. Flint is not yet one of those three, and the two columns it has under-cover as well: its three quantile draws cover 0.380, 0.540 and 0.730 where the reference estimator on that task reaches 0.840, and its CECL cell is set by the one instance of three whose coverage falls to 0.691 against 0.950 on the benign pool.

The protocol for each: `--prefill-step-size 256 --prompt-cache-size 1` on the server, a real completion as the health check rather than `/v1/models`, and on the Inspect side `-T n_instances=3 -T seed=1 --max-tokens 16384 --max-connections 1 --token-limit 2500000 --time-limit 86400`, eight instances for CCAR, three single-instance runs at seeds 1, 2 and 3 for quantile, and a transcript saved to `runs/` per sample. Sampling goes in a `--generate-config` file, because Inspect's OpenAI provider forwards `temperature` and `top_p` but silently drops `top_k`, which has to ride in `extra_body` instead. Measure the ceiling first and report it alongside the cells, because a ceiling reached mid-suite costs a human restart and a ceiling measured first costs 15 minutes. Watch progress on `~/.local/share/inspect_ai/traces/trace-<pid>.log` rather than on the `.eval` file, for the reason given under [A Working Run and a Dead One Look Identical](#a-working-run-and-a-dead-one-look-identical).
