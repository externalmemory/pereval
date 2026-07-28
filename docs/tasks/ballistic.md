# Ballistic Trajectory Extrapolation

A controlled mechanism task with exactly known ground truth, used to calibrate
the harness at the easy end of the difficulty gradient.

```
inspect eval pereval/tasks/ballistic/task.py --model <provider/model>      # needs Docker
python -m pereval.tasks.ballistic.generator --out-dir runs/demo --seed 1   # inspect one instance
```

## The Task

The agent receives (category, x, y) training rows and must predict y with 95% prediction intervals at held-out distances beyond the training range. y is projectile drop simulated by py-ballisticcalc with noise on muzzle velocity and launch angle; the held-out window for rifle categories is kept supersonic, so the extrapolation trap is pure velocity-dependent drag. It scores point accuracy (MAE vs the true conditional mean), interval calibration (coverage), and sharpness (width), combined into an oracle-anchored Winkler interval score.

## Isolation

Each instance is generated host-side and only neutral CSVs enter the agent's sandbox: the ballistics engine, the generator, and the ground-truth oracle stay out. What forces the agent to model the data rather than re-simulate it is that category identifiers are opaque and the ballistic parameters are randomized per run, so there is no known load to look up, and any simulation would first require estimating each category's parameters from the training data, which is the task itself. The sandbox additionally has no network, which blocks the weaker shortcuts of installing the exact engine, downloading its drag tables, or querying an online calculator. It does not prevent the agent from recognizing the physics from the data, which is legitimate.

## Scores (three runs, mean ± 2 SD)

Three instances (seed 1, `n_instances=3`), reported as **mean ± 2 SD** across the runs, ordered by the upper end mean + 2 SD. Every row is paired on the same three instances. Lower Winkler regret is better; coverage targets 0.95. The parabola baseline (`-T baseline=true`) is the naive quadratic reference, not a model.

| Row | runs | Winkler regret (mean ± 2 SD) | Coverage |
| --- | --- | --- | --- |
| mimo-v2.5 (free) | 3 | 10.5 ± 4.0 | 0.39 |
| GLM-5.1 | 3 | 8.0 ± 12.8 | 0.56 |
| nemotron-3-ultra (free) | 3 | 11.0 ± 10.8 | 0.42 |
| Parabola baseline (naive) | 3 | 17.2 ± 9.3 | 0.23 |
| nemotron-3-super (free) | 3 | 59.1 ± 1.3 | 0.13 |
| laguna-m.1 (free) | 3 | 59.1 ± 1.3 | 0.13 |
| deepseek-v4-flash (free) | 3 | 30.5 ± 77.2 | 0.14 |
| Claude Haiku 4.5 | 3 | 37.8 ± 79.8 | 0.22 |

Three rows clear the naive parabola baseline: mimo-v2.5, GLM-5.1 and nemotron-3-ultra (upper bounds 14.5, 20.8, 21.8 vs the baseline's 26.5). mimo is the tightest of them (± 4.0), which is why it leads on the upper-bound ordering despite not having the lowest mean.

The bottom of the table is more interesting than a mean ranking shows. **Claude Haiku 4.5's mean (37.8) is lower than laguna's and nemotron-3-super's (59.1), yet it ranks last**, because its ± 79.8 band — one instance blew out to 83 — pushes its upper bound to 118 against their 60. Ordering by the worst case rewards the consistent-but-mediocre over the erratic, which is the intended behaviour.

**laguna and nemotron-3-super score bit-for-bit identically (59.1 ± 1.3).** That is not a duplicate: both weak models independently fell back to the same deterministic per-category *linear* least-squares fit, which produces identical predictions and is simply wrong for nonlinear velocity-dependent drop (a straight line where the drag curve bends). Two different models converging on the same naive method is itself a finding, and the near-zero ± 1.3 band confirms it — a fixed method has no run-to-run method variance, only the small block-sampling wobble.

## Earlier single-run exploration (provisional, N = 1)

> Superseded for GLM-5.1 and Haiku by the three-run table above. The other rows are still single instances and are kept only as an illustration that the scorer discriminates and localises failure by sub-task. The single-run GLM-5.1 (3.34) and Haiku (58.40) numbers here both differ materially from their three-run means (7.97, 37.84), which is exactly why single runs are not reported as results.

The numbers below come from a single generated instance (N = 1, seed 1). With one instance there are no error bars, so the mid-field ordering is not robust and would likely reorder on another draw. Lower Winkler regret is better; coverage targets 0.95. "Parabola baseline" is the naive quadratic reference (`-T baseline=true`), not a model.

| Model | Winkler regret | MAE (m) | Coverage | Width (m) | Rifle regret | Pistol regret |
| --- | --- | --- | --- | --- | --- | --- |
| GLM-5.1 | 3.34 | 0.76 | 0.87 | 2.86 | 0.93 | 9.66 |
| Kimi K3 | 6.00 | 0.97 | 0.81 | 2.91 | 2.02 | 16.44 |
| Claude Fable 5 | 6.16 | 1.08 | 0.76 | 3.69 | 2.99 | 14.49 |
| Kimi-k2.6 | 8.49 | 0.60 | 0.55 | 1.24 | 10.32 | 3.69 |
| GLM-5 | 11.53 | 0.62 | 0.49 | 1.21 | 15.55 | 0.99 |
| Parabola baseline | 21.77 | 0.67 | 0.12 | 0.25 | 19.28 | 28.31 |
| Kimi-k2.7-code | 28.26 | 1.70 | 0.42 | 2.78 | 37.97 | 2.77 |
| Claude Haiku 4.5 | 58.40 | 1.72 | 0.15 | 0.61 | 78.19 | 6.43 |

The only claim is that the harness produces separable, interpretable scores: the spread is dominated by the supersonic rifle sub-task, where overconfident narrow intervals with near-zero coverage are penalized heavily, and the per-class split localizes each model's failure.

Claude Fable 5 lands near the top (6.16), nailing that hard rifle sub-task (rifle 2.99), so Claude Haiku 4.5's row at the bottom is not a Claude-family verdict: Haiku is tuned for fast answers to simple questions and likely runs at a low default effort here. Kimi K3 inverts the usual failure: it posts the best rifle score in the table (2.02, beating Fable) but is the only strong model that stumbles on pistols (16.44, coverage 0.59), the opposite of the typical supersonic-rifle weakness.

All are real single-instance results. Turning any of this into an actual comparison would require many instances per model and the paired, clustered error analysis described in [../task-design.md](../task-design.md).
