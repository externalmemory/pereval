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

## No Competent Anchor, Deliberately

The other tasks bracket a model between a naive floor and a competent reference: CCAR
has the probit-linear Vasicek fit, the orbital tasks have the Kepler fit. Ballistic has
only the naive parabola and the degenerate answer, so a score of 12 cannot be read as
"near the achievable frontier" or "ten times off it". That gap is a real limitation on
what this column supports, and it is accepted rather than closed.

A competent reference here would have to fit a drag model, which means it would have to
know the data is ballistic. The task withholds exactly that: category identifiers are
opaque so the agent cannot invert a label into a known load. Disclosing the domain in
the prompt to make a fair reference possible would change the task, invalidate every run
already recorded, and hand over the isolation property that the design is built on. For
a task whose job is calibrating the harness across a difficulty gradient rather than
carrying a domain claim, that is a bad trade.

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

The bottom of the table is more interesting than a mean ranking shows. **Claude Haiku 4.5's mean (37.8) is lower than laguna's and nemotron-3-super's (59.1), yet it ranks last**, because its ± 79.8 band (one instance blew out to 83) pushes its upper bound to 118 against their 60. Ordering by the worst case rewards the consistent-but-mediocre over the erratic, which is the intended behaviour.

**laguna and nemotron-3-super score bit-for-bit identically (59.1 ± 1.3).** That is not a duplicate: both weak models independently fell back to the same deterministic per-category *linear* least-squares fit, which produces identical predictions and is simply wrong for nonlinear velocity-dependent drop (a straight line where the drag curve bends). Two different models converging on the same naive method is itself a finding, and the near-zero ± 1.3 band confirms it: a fixed method has no run-to-run method variance, only the small block-sampling wobble.

