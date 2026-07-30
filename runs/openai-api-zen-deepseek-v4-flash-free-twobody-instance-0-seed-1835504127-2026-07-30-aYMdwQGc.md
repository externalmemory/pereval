# openai-api/zen/deepseek-v4-flash-free — twobody (id=instance-0-seed-1835504127)

- 0/10 points predicted; Winkler regret 2861.031 (agent 2862.457 vs oracle 1.426, degenerate 2862.457); MAE 71.561; coverage 0.000; mean width 0.000.
- messages 2 | limit type='time' limit=3600.0 | seed None

---

## [0] system

You are given a time series in the `data/` directory:

- `data/train.csv` with columns t,alpha: t is time in days, alpha is a measured
  angle in degrees (0 to 360).
- `data/test.csv` with a column t: future days for which you must predict alpha.
The measurements contain observation noise, and the test days lie BEYOND the
range of days seen in training.

Build a predictive model. For every row in `data/test.csv`, produce a point
estimate of alpha and a 95% prediction interval [lower, upper] for a NEW noisy
measurement of alpha at that t. alpha is an angle in degrees and wraps at
360 (359 and 1 are two degrees apart, not 358). The interval is for a fresh noisy
measurement, so it must account for the observation noise.

Write your predictions to `predictions.csv` in the working directory with columns
exactly:

    t,y_pred,y_lower,y_upper

one row per test input, with t copied exactly from data/test.csv, and the angle
columns in degrees.

You have Python with numpy, pandas, scikit-learn, statsmodels, and scipy. You do
not have internet access. Each code execution runs in a FRESH interpreter, so
write a single self-contained script (save it to a file and run it) rather than
relying on state carrying over between executions. Produce a complete
predictions.csv early, even from a rough model, and keep a valid one on disk;
refine it after. Verify it has one row per test input before submitting.


## [1] user

Predict alpha with a 95% interval for every t in data/test.csv and write predictions.csv, as specified in the system instructions.

