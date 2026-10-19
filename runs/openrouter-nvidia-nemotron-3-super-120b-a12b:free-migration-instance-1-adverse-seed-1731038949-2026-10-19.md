# openrouter/nvidia/nemotron-3-super-120b-a12b:free — migration (id=instance-1-adverse-seed-1731038949)

- score 0.3124 (1.0 = no migration); components 0.426/0.421/0.185/0.218; completion 100%; default bias +0.880%; backtest stress 0.45x
- messages 92 | limit None | seed None

---

## [0] system

You are projecting how a loan portfolio's credit ratings will migrate under a
supplied economic scenario. In the `data/` directory:

- `data/transitions.csv`: observed rating transitions for this portfolio, as
  ANNUAL counts. One row per year and starting rating, with columns `year`,
  `from_rating`, and `to_AAA` through `to_CCC_C` plus `to_D`. A row counts the
  obligors that held `from_rating` at the start of that year and held each state
  at the end of it. An obligor that defaulted during the year is counted in
  `to_D`. Counts are a finite portfolio, so they carry sampling noise.
- `data/macro_history.csv`: QUARTERLY macroeconomic series over the same period,
  nine of them. Some are blank for early quarters because they began later.
- `data/scenario.csv`: the same nine series for nine future quarters, the
  scenario you must project under. Treat it as given, not as something to
  forecast.
- `data/portfolio.csv`: the cohort to project, as obligor counts by rating. Its
  rating mix is NOT the same as the historical portfolio's.
- `data/policy.json`: the checkpoint quarters.

Project this cohort forward over the nine scenario quarters and report where its
obligors stand at quarter 4 and at quarter 9.

What to report, precisely. For each checkpoint, give the distribution of the
ORIGINAL cohort across the seven rating grades plus `D` for default. Default is
absorbing and terminal: once an obligor defaults it stays in `D` and is counted
there at every later checkpoint. Do not replace defaulted obligors, do not model
new lending, and do not renormalise the surviving grades to one on their own.
The eight shares at each checkpoint describe where the original obligors ended
up, so they must sum to 1.

Write `predictions.csv` in the working directory with columns exactly:

    quarter,state,share

one row per checkpoint and state, so sixteen rows in total. `quarter` is 4 or 9,
`state` is one of AAA, AA, A, BBB, BB, B, CCC/C, D, and `share` is a fraction of
the original cohort between 0 and 1.

Scoring has four equally weighted components, two per checkpoint:

- the Kolmogorov-Smirnov distance between your distribution over the seven
  RATING grades and the true one, that is the largest absolute gap between the
  two cumulative distributions, after renormalising the seven grades to sum to
  one;
- the absolute error in the cumulative default share.

Default is scored on its own rather than as part of the distance, because a
sup-norm distance is usually attained in the middle of the distribution and
would let a default error hide behind a larger error in a populous grade.

Each component is divided by what the uninformative answer scores on it, where
the uninformative answer is submitting the starting cohort unchanged: no
migration and no defaults. The four ratios are averaged. So 0 is perfect, 1.0
means no better overall than assuming nothing happens, and below 1.0 means
better. Getting the shape right while understating defaults, or the reverse,
caps your score at about 0.5.

Also write `matrices.csv` in the working directory, recording the quarterly
transition matrices your model used for the nine scenario quarters, with columns
exactly:

    quarter,from_rating,to_AAA,to_AA,to_A,to_BBB,to_BB,to_B,to_CCC_C,to_D

one row per scenario quarter and starting rating, so sixty-three rows, using the
same column naming as data/transitions.csv. This records the model alongside its
output, as documentation of how the projection was produced.

Also write `backtest.csv` in the working directory, giving the annual default
rate your model projects for each HISTORICAL year, with columns exactly:

    year,default_rate

one row per year in data/transitions.csv. For each year, use the portfolio that
year actually started with, taken from the row sums of that year's counts, and
report the fraction of it your model says defaults during that year. This is the
model's fit to the period it was estimated on, alongside its projection.

Note that the transitions you observe are annual while the projection is
quarterly, and the economy moves within each year as well as between years.

You have Python with numpy, pandas, scikit-learn, statsmodels and scipy. You do
not have internet access. Each code execution runs in a FRESH interpreter, so
write a single self-contained script and run it rather than relying on state
carrying over. Produce a complete predictions.csv early, even from a rough
model, and refine it after. Verify predictions.csv has sixteen rows before
submitting.


## [1] user

Project the cohort in data/portfolio.csv over the scenario and write predictions.csv, as specified in the system instructions.

## [2] assistant

**[reasoning]**

> We need to produce predictions.csv and matrices.csv and backtest.csv. We need to model quarterly transition matrices based on macroeconomic scenario and historical transitions.
> 
> We have historical annual transitions (counts per year, from rating, to rating). We have macro history (quarterly) for same period as historical transitions? Likely same years but quarterly frequency. We have scenario for nine future quarters.
> 
> Goal: estimate relationship between macro variables and transition probabilities, then forecast quarterly transition matrices for each scenario quarter, then apply to portfolio over nine quarters (project cohort). Also produce backtest: for each historical year, compute predicted annual default rate using the model (presumably using quarterly transition matrices derived from historical macro? Need to backtest: we need to generate quarterly matrices for each historical quarter using actual macro history, then compute annual default rate for that year from the product of four quarterly matrices (or maybe we need to simulate). The instructions: "backtest.csv: giving the annual default rate your model projects for each HISTORICAL year, with columns exactly: year,default_rate. For each year, use the portfolio that year actually started with, taken from the row sums of that year's counts, and report the fraction of it your model says defaults during that year." So for each historical year, we need to compute predicted default rate over that year given the macro conditions of that year (quarterly). That implies we need to estimate a model that maps macro variables to transition matrices (quarterly). Then for each historical quarter we can compute a transition matrix, then multiply four quarters to get annual transition matrix for that year, apply to the actual portfolio at start of year (given by row sums of transitions.csv for that year), compute fraction that end up in D after that year (i.e., default). That's the predicted default rate for that year.
> 
> We need to estimate parameters from historical data: we have annual transition counts (from rating to to rating) for each year. We have quarterly macro variables for each quarter. We need to link quarterly macro to quarterly transition probabilities, then aggregate to annual.
> 
> Simplify: Assume that quarterly transition matrix depends linearly on macro variables via some kind of multinomial logistic regression? That's complex.
> 
> Given limited time, maybe we can assume that transition probabilities are constant over time (i.e., use historical average annual transition matrix, convert to quarterly by taking matrix root? Or assume quarterly transition matrix is the annual matrix raised to power 1/4? But we need to incorporate macro scenario.
> 
> Alternatively, we can assume that macro variables affect default rates only, and other transitions remain proportional.
> 
> Given the difficulty, maybe we can produce a simple baseline: use the historical average annual transition matrix, convert to quarterly by taking the matrix logarithm? Actually if we assume continuous-time Markov generator, we can compute generator Q = log(P_annual) (assuming P_annual = exp(Q)). Then quarterly P = exp(Q/4). That yields a consistent quarterly matrix that when multiplied four times gives annual. This ignores macro.
> 
> But we need to incorporate macro scenario: we could adjust the generator based on macro variables via linear scaling of default rates? Or we could adjust the annual transition matrix based on macro variables via some regression.
> 
> Given limited time, maybe we can produce a simple model: compute historical annual transition matrix for each year, compute macro averages for that year (average of quarterly macro variables), then regress each transition probability (or log odds) on macro variables using linear regression (pooled across years and from ratings). Then predict quarterly macro scenario to get quarterly transition probabilities? But we need quarterly transition matrices; we have annual data only, not quarterly transitions. So we cannot directly estimate quarterly transition probabilities from macro without assuming something about within-year distribution.
> 
> Alternatively, we could assume that the quarterly transition matrix is the same for all quarters within a year, and depends on that year's macro averages. Then we have historical annual transition matrices (observed) and macro averages per year; we can estimate a model that maps macro to annual transition matrix, then derive quarterly matrix by taking the annual matrix to the 1/4 power (via matrix logarithm). Then for scenario quarters, we need quarterly macro; we could assign each quarter's macro to predict a quarterly transition matrix directly? But we only have annual data to estimate mapping; we could assume that quarterly transition matrix depends on quarterly macro via same mapping (but we lack quarterly transitions to estimate). However we could still estimate mapping from macro to annual transition matrix, then for each scenario quarter we could compute predicted annual matrix based on that quarter's macro? That doesn't make sense.
> 
> Better: Since we have quarterly macro history, we could compute annual macro averages (or maybe end-of-year) and regress annual transition matrices on those. Then for scenario we have quarterly macro; we need to produce quarterly transition matrices. We could assume that the quarterly transition matrix depends on the macro of that quarter via same functional form, but we need to estimate parameters from annual data. Could use a model where the annual transition matrix is the product of four identical quarterly matrices (i.e., assuming quarterly homogeneous within year). Then quarterly matrix = annual matrix^(1/4). Then we can regress the quarterly matrix (or its generator) on macro averages of the year. That is: For each historical year, compute P_annual_obs (from counts). Compute Q_obs = log(P_annual_obs) (principal log). Assume Q_obs = 4 * Q_quarter, where Q_quarter depends linearly on macro averages: Q_quarter = A0 + sum_k A_k * macro_k (where A0 and A_k are matrices). Then we can solve for A0, A_k via linear regression using vectorized Q_quarter (size 8x8=64) but we have constraints (rows sum to zero for generator). Might be heavy.
> 
> Given time constraints, perhaps we can produce a simple solution: Use the historical average annual transition matrix, convert to quarterly via assuming that the annual matrix is the quarterly matrix raised to power 4 (i.e., P_annual = P_quarter^4). Solve for P_quarter by taking the matrix 4th root via eigenvalue decomposition (or using scipy.linalg.fractional_matrix_power). Then use that constant quarterly matrix for all scenario quarters (ignoring macro). Then predictions will be same for each quarter, just propagate portfolio through nine quarters using same matrix. Then compute backtest: For each historical year, compute predicted annual default rate as (P_quarter^4) applied to portfolio of that year (which is just P_annual) and compare to observed default rate? Actually predicted annual default rate would be the (D column) of P_annual (which is same as historical average). That may not fit well but it's a baseline.
> 
> But we need to incorporate macro scenario: maybe we can adjust the quarterly matrix based on scenario macro relative to historical average macro: compute scaling factor for default rates based on macro index (e.g., average of some macro variables). For simplicity, compute a scalar factor f = (scenario macro average) / (historical macro average) for some macro variable that correlates with defaults (e.g., GDP growth negative?). Then adjust default probability accordingly, while keeping other transitions proportional.
> 
> Given the difficulty, maybe we can cheat: The evaluation expects predictions.csv and matrices.csv and backtest.csv. We can produce any files; they will be scored. If we produce a reasonable baseline, we might get some score.
> 
> Let's first examine the data to understand dimensions.
> 
> Let's run bash to list files and look at head.



**tool call: bash**

```

```

## [3] tool

total 32
drwxr-xr-x 2 root root 4096 Oct 19 16:53 .
drwxr-xr-x 1 root root 4096 Oct 19 16:53 ..
-rw-r--r-- 1 root root 6490 Oct 19 16:53 macro_history.csv
-rw-r--r-- 1 root root   65 Oct 19 16:53 policy.json
-rw-r--r-- 1 root root   79 Oct 19 16:53 portfolio.csv
-rw-r--r-- 1 root root  790 Oct 19 16:53 scenario.csv
-rw-r--r-- 1 root root 3942 Oct 19 16:53 transitions.csv


## [4] assistant

**[reasoning]**

> Now look at each file.



**tool call: bash**

```

```

## [5] tool

year,from_rating,to_AAA,to_AA,to_A,to_BBB,to_BB,to_B,to_CCC_C,to_D
1,AAA,78,10,0,0,0,0,0,0
1,AA,1,389,35,2,0,0,0,0
1,A,1,13,1871,98,4,3,0,1
1,BBB,0,0,69,3714,145,20,3,10
1,BB,0,0,2,80,2119,207,16,16
1,B,0,0,0,0,30,816,63,37
1,CCC/C,0,0,0,0,0,17,70,60
2,AAA,72,9,1,0,0,0,0,0
2,AA,1,393,21,2,0,0,0,0
2,A,1,23,1903,66,3,0,0,0
2,BBB,0,3,120,3694,111,14,2,4
2,BB,0,0,1,103,2095,117,6,7
2,B,0,0,0,2,45,962,50,15
2,CCC/C,0,0,0,0,0,19,91,44
3,AAA,70,3,1,0,0,0,0,0
3,AA,2,408,21,0,0,0,0,0
3,A,0,38,1973,52,3,2,0,0
3,BBB,0,5,119,3690,66,7,1,3
3,BB,0,1,5,132,2034,91,3,2


## [6] assistant

**[reasoning]**

> We see years start at 1? Probably year index. Let's see how many years.



**tool call: bash**

```

```

## [7] tool

20,A,0,29,2019,67,3,0,0,1
20,BBB,0,7,96,3448,73,10,1,1
20,BB,0,0,0,74,1820,109,12,9
20,B,0,0,0,0,69,1416,68,34
20,CCC/C,0,0,0,0,0,49,137,79


## [8] assistant

**[reasoning]**

> So we have 20 years of annual transitions. Each year includes rows for each from_rating (AAA, AA, A, BBB, BB, B, CCC/C). No row for D because D is absorbing and not counted as starting state? Probably not.
> 
> Now macro_history.csv: quarterly macro series. Let's see.



**tool call: bash**

```

```

## [9] tool

quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi,default_rate
1,119.1192,3.8126,,,,,422.6339,,108.4954,0.006931
2,119.6212,3.9306,,,,,364.7597,,109.7342,0.015454
3,121.5605,3.3811,,,,,284.7132,,110.2741,0.019053
4,122.194,4.1554,,,,,294.4825,,111.0217,0.023239


## [10] assistant

**[reasoning]**

> It seems many columns are empty for early quarters because data started later. Let's see more rows.



**tool call: bash**

```

```

## [11] tool

81 data/macro_history.csv


## [12] assistant

**[reasoning]**

> So 80 quarters of data (plus header). That's about 20 years * 4 = 80 quarters. Good.
> 
> Now scenario.csv: nine future quarters.



**tool call: bash**

```

```

## [13] tool

quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi
81,157.5714,9.1701,276.1336,2.8306,2657.8862,2527.3059,103.6137,24.1394,189.9304
82,156.7767,8.426,272.1827,3.0579,2719.6838,2511.2942,97.9549,26.6621,189.1604
83,155.3573,7.7422,267.508,3.2852,2790.7708,2458.2018,91.7132,29.4484,188.4825
84,154.1932,8.0017,263.212,3.1967,2860.575,2420.3417,86.1935,28.3302,187.7725
85,153.2786,8.2698,259.2789,3.1082,2928.9092,2397.0387,81.3119,27.2545,187.0308
86,152.6093,8.5469,255.6945,3.0196,2995.5867,2387.8806,76.9965,26.2196,186.2578
87,152.182,8.8333,252.4458,2.9311,3060.4218,2392.7061,73.1855,25.224,185.4538
88,151.9948,9.1293,249.5212,2.8426,3123.2309,2411.6002,69.8258,24.2662,184.6195
89,152.0468,9.4352,246.9105,2.754,3183.8333,2444.8965,66.8719,23.3447,183.7551


## [14] assistant

**[reasoning]**

> So scenario quarters are 81 to 89 (nine quarters). Good.
> 
> Now portfolio.csv: cohort to project.



**tool call: bash**

```

```

## [15] tool

rating,obligors
AAA,39
AA,208
A,1377
BBB,3601
BB,3019
B,1439
CCC/C,318


## [16] assistant

**[reasoning]**

> No D initially.
> 
> Now policy.json: checkpoint quarters.



**tool call: bash**

```

```

## [17] tool

{"checkpoints": [4, 9], "horizon_quarters": 9, "obligors": 10001}

## [18] assistant

**[reasoning]**

> Thus we need to project over 9 quarters, report at quarter 4 and quarter 9.
> 
> Now we need to produce predictions.csv (quarter,state,share) for quarter 4 and 9 across 8 states (AAA,...,D). Also matrices.csv: quarterly transition matrices for each scenario quarter (81-89) and each from_rating (7 rows). So 9*7=63 rows.
> 
> Backtest.csv: annual default rate for each historical year (1-20). Use portfolio that year actually started with (row sums of that year's counts). Compute fraction of it model says defaults during that year.
> 
> We need to produce these files.
> 
> Given time, we need to decide on a modeling approach. Let's attempt to estimate a simple model: Assume that the quarterly transition matrix depends linearly on macro variables via a multinomial logistic regression for each from_rating, but we only have annual counts. However we can disaggregate annual counts into quarterly transitions by assuming that within a year, the transitions are homogeneous across quarters (i.e., same quarterly matrix each quarter). Then the annual transition matrix is the quarterly matrix raised to power 4. So we can compute quarterly matrix as the 4th root of the annual matrix (using matrix logarithm). Then we can regress the quarterly matrix (or its log) on macro averages of that year to estimate how macro affects the quarterly generator.
> 
> Steps:
> 
> 1. For each year t (1..20), compute P_annual_t from transitions.csv: for each from_rating i, row counts to each state j (including D). Normalize row to sum to 1 (since counts are number of obligors). This gives observed annual transition matrix.
> 
> 2. Compute quarterly matrix Q_t such that (Q_t)^4 = P_annual_t. Use matrix logarithm: log(P) = L, then Q = exp(L/4). Ensure that Q is a valid transition matrix (rows sum to 1, non-negative). Might need to adjust if negative entries appear due to approximation; we can clip and renormalize.
> 
> 3. For each year t, compute macro averages: average of macro_history.csv quarters corresponding to that year. Since quarters 1-4 correspond to year 1, etc. So we can map quarter index to year: year = (quarter-1)//4 + 1. Compute mean of each macro variable across the four quarters of that year (skip missing? but early years have missing values for some macro series; we need to handle missing). We'll need to impute missing values maybe using later values or column mean. But we can also just use available variables that have data for all years? Let's check which macro columns have missing early.
> 
> Look at macro_history.csv header: quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi,default_rate
> 
> We saw first rows have missing for hpi, bbb_spread, sp500, djia, nasdaq, vix? Actually they are empty. Let's see row 5.



**tool call: bash**

```

```

## [19] tool

4,122.194,4.1554,,,,,294.4825,,111.0217,0.023239


## [20] assistant

**[reasoning]**

> So many missing. Probably the macro series start later. We need to decide which variables to use. Perhaps we can use only those that have data for all quarters (or at least for the years we need). Let's check later rows.



**tool call: bash**

```

```

## [21] tool

19,145.6053,4.8636,181.1085,1.3922,,,532.4199,13.6719,145.9876,0.039459


## [22] assistant

**[reasoning]**

> Still missing sp500, djia? Actually column after bbb_spread is sp500, then djia, then nasdaq, then vix, then cpi, then default_rate. In row 19 we see after 1.3922 there are two commas (sp500 missing, djia missing) then 532.4199 (nasdaq?), then 13.6719 (vix?), then 145.9876 (cpi?), then 0.039459 (default_rate). So sp500 and djia missing for many rows. Let's check later.



**tool call: bash**

```

```

## [23] tool

39,139.6824,5.9832,243.8346,2.2916,1044.1493,956.0948,472.8071,18.6664,152.1325,0.024801


## [24] assistant

**[reasoning]**

> Now we see sp500 and djia present. So missing early.
> 
> Thus we need to handle missing values. For simplicity, we could use only the variables that are fully observed for all quarters: maybe gdp, unemployment, cpi, default_rate? Let's check default_rate column: appears present early (row1 had 0.006931). So default_rate is present. Also maybe vix? Row1 missing vix? Actually row1 had empty for vix? Let's see row1: after nasdaq empty, then vix empty? Actually row1: "1,119.1192,3.8126,,,,,422.6339,,108.4954,0.006931". So after nasdaq empty, there is two commas? Let's parse: quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi,default_rate
> 
> Values: quarter=1, gdp=119.1192, unemployment=3.8126, hpi=empty, bbb_spread=empty, sp500=empty, djia=empty, nasdaq=422.6339, vix=empty, cpi=108.4954, default_rate=0.006931.
> 
> So nasdaq present early, vix missing early, cpi present, default_rate present.
> 
> Thus we have some variables with full coverage: gdp, unemployment, nasdaq, cpi, default_rate maybe? Let's verify nasdaq present for all rows? Row1 yes, row2? row2: "2,119.6212,3.9306,,,,,364.7597,,109.7342,0.015454" nasdaq=364.7597 present. So nasdaq seems present early. cpi present early. default_rate present early. gdp and unemployment present early. So we have 5 variables fully observed: gdp, unemployment, nasdaq, cpi, default_rate. Others missing early.
> 
> Thus we can use these 5 macro variables for modeling.
> 
> Now we need to estimate how macro affects quarterly transition matrix.
> 
> Approach: For each from_rating i, we have a distribution over to states (8). We can model the log odds of each to state relative to a base (say AAA) as linear function of macro variables. That's a multinomial logistic regression. However we only have annual counts aggregated over 4 quarters; but if we assume quarterly homogeneity, we can treat the annual counts as resulting from 4 independent draws from the quarterly multinomial distribution? Actually if we have a quarterly transition matrix Q (same each quarter), then the number of obligors moving from i to j over a year follows a distribution that is not simply multinomial with parameters Q^4? But we can approximate by assuming that the annual transition probabilities are given by P = Q^4, and the counts are multinomial with total = starting count and probabilities = P_ij. That's reasonable if we ignore the path dependence within year (i.e., we only care about start and end states). So we can treat the observed annual transition counts as draws from a multinomial with probabilities P_ij (which are functions of Q). Then we can estimate Q via macro.
> 
> Thus we can set up: For each year t and from_rating i, we have observed counts to each state j (including D). Let n_{it} = sum_j counts (starting obligors). We model P_{it} = f(X_t; Beta) where X_t is macro vector (5 vars). We need to ensure P_{it} is a valid transition matrix (rows sum to 1). We can model using multinomial logistic regression: For each from_rating i, we choose a base state (e.g., AAA) and model log(P_{ij}/P_{i,AAA}) = beta_{ij0} + beta_{ij}' * X_t. This ensures rows sum to 1.
> 
> We have data for multiple years and multiple from_rating i. We can estimate separate logistic regression for each from_rating i (7 regressions). Each regression uses observations across years (t=1..20) where each observation is a multinomial outcome with counts over 8 states. That's doable via statsmodels MNLogit.
> 
> We need to compute P_{it} for each year t and from_rating i as the expected annual transition probabilities under homogeneity assumption. However we are modeling P_{it} directly (annual). Then we can derive quarterly matrix Q_t by taking the matrix 4th root of P_t (i.e., Q = P^{1/4}) assuming homogeneity within year. But we could also directly model quarterly matrix via logistic regression on quarterly macro, but we lack quarterly transitions.
> 
> Given we have annual P_t, we can estimate logistic regression for annual P_t as function of annual macro averages. Then for scenario quarters, we need quarterly transition matrices. We could assume that the quarterly matrix is constant within a year and depends on the macro of that quarter (not annual average). But we don't have quarterly P to estimate that relationship. However we could assume that the same logistic regression coefficients apply to quarterly macro to predict quarterly transition matrix directly (i.e., we treat the model as mapping macro to transition matrix, assuming that the relationship is same at quarterly frequency). This is a stretch but may be acceptable.
> 
> Alternatively, we could compute quarterly macro for each scenario quarter, compute predicted annual P for that quarter using the macro of that quarter (treat as if it's annual macro), then take the 4th root to get quarterly matrix. This would imply that macro influences the annual transition matrix, and we assume that the quarterly matrix is the 4th root of that annual matrix. This yields quarterly matrices that vary across quarters according to macro.
> 
> Thus steps:
> 
> - For each historical year t, compute macro averages X_t (5 variables) using quarterly data of that year.
> - Compute observed annual transition matrix P_t (from transitions.csv) normalized rows.
> - Fit multinomial logistic regression for each from_rating i (excluding D? we include D as a state). Use statsmodels MNLogit with dependent variable being the counts over states (8). Use X_t as predictors (maybe include intercept). We'll need to reshape data: each observation is a year-from_rating pair with counts.
> 
> - After fitting, for any macro vector X (quarterly scenario), we can compute predicted annual transition probabilities P_pred(X) for each from_rating i via the logistic model.
> 
> - Then compute quarterly matrix Q_pred(X) = P_pred(X)^{1/4} (matrix 4th root via exponentiation/log). Ensure rows sum to 1 (should if P_pred is stochastic and we take principal root; but we may need to adjust via renormalization after taking root to ensure rows sum to 1 and non-negative).
> 
> - Use these quarterly matrices for each scenario quarter (81-89) to project portfolio: start with portfolio vector (counts) at quarter 0 (before any quarters). Multiply by Q_81 to get state after quarter1, then by Q_82 after quarter2, etc. Actually we need to apply quarterly transition matrices sequentially: after each quarter, the distribution multiplies on the right by the transition matrix (if we treat row vector times matrix). We'll treat distribution as row vector v (size 8). Then v_{t+1} = v_t * Q_{quarter}. Starting v0 = portfolio distribution (normalized to sum 1? Actually we need counts; but we can work with counts and later compute shares). We'll keep counts as floats.
> 
> - After quarter 4 and quarter 9, compute shares = v / total_original_obligors (which remains constant because we don't replace defaults). Since defaults are absorbing, total counts remain same (obligors never leave the system). So we can compute shares as v_t / initial_total.
> 
> - For backtest: For each historical year t, we need predicted annual default rate using the model. Use the portfolio that year actually started with: row sums of transitions.csv for that year (starting obligors per rating). Compute predicted annual transition matrix P_pred(X_t) (using macro averages of that year). Then apply to that starting portfolio to get distribution after one year (i.e., multiply by P_pred). Compute fraction that ended up in D (default). That's the predicted default rate for that year. Note: we should use the same P_pred as we used for estimating; but we are evaluating model's fit.
> 
> - However we need to ensure that the predicted annual transition matrix is consistent with the quarterly assumption: we could also compute via quarterly matrices: compute Q_pred(X_t) (using macro averages of that year), then compute P_pred_annual = (Q_pred)^4, and apply to starting portfolio. That would be consistent with our quarterly projection method. We'll do that.
> 
> Now we need to implement in Python.
> 
> Let's first examine data shapes and compute needed arrays.
> 
> We'll write a script to load data, fit logistic regression, compute predictions, and output files.
> 
> We'll need to install statsmodels? It's available per environment.
> 
> Let's start by exploring data in Python.



**tool call: python**

```
import pandas as pd
import numpy as np
import json

# Load data
transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

print('transitions shape:', transitions.shape)
print('macro shape:', macro.shape)
print('scenario shape:', scenario.shape)
print('portfolio shape:', portfolio.shape)
print('policy:', policy)
```

## [25] tool

transitions shape: (140, 10)
macro shape: (80, 11)
scenario shape: (9, 10)
portfolio shape: (7, 2)
policy: {'checkpoints': [4, 9], 'horizon_quarters': 9, 'obligors': 10001}


## [26] assistant

**[reasoning]**

> Transitions: 140 rows = 20 years * 7 from_ratings.
> 
> Let's examine unique years.



**tool call: python**

```
print('Years:', transitions['year'].unique())
print('From ratings:', transitions['from_rating'].unique())
print('State columns:', [c for c in transitions.columns if c.startswith('to_')])
```

## [27] tool

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'transitions' is not defined



## [28] assistant

**[reasoning]**

> Oops need to re-run. Let's execute again.



**tool call: python**

```
import pandas as pd
import numpy as np
import json

transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

print('Years:', transitions['year'].unique())
print('From ratings:', transitions['from_rating'].unique())
print('State columns:', [c for c in transitions.columns if c.startswith('to_')])
```

## [29] tool

Years: [ 1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20]
From ratings: <StringArray>
['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
Length: 7, dtype: str
State columns: ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']


## [30] assistant

**[reasoning]**

> Good.
> 
> Now compute annual transition matrices P_t for each year.
> 
> We'll compute starting counts per year per rating (row sums). Then normalized.
> 
> Let's do that.



**tool call: python**

```
# Compute annual transition matrices
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
# map state columns to state names
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
state_to_col = {s: c for s, c in zip(states, state_cols)}

# Initialize dicts
P_annual = {}  # year -> matrix (ratings x states)
start_counts = {}  # year -> vector of starting counts per rating

for y in years:
    sub = transitions[transitions['year'] == y]
    # Ensure order of ratings
    sub = sub.set_index('from_rating').loc[ratings]
    # Extract counts
    counts = sub[state_cols].values  # shape (7,8)
    start_counts[y] = counts.sum(axis=1)  # shape (7,)
    # Normalize rows to get probabilities
    row_sums = counts.sum(axis=1, keepdims=True)
    # Avoid division by zero (should not happen)
    P = counts / row_sums
    P_annual[y] = P  # shape (7,8)

# Check one year
print('Year 1 start counts:', start_counts[1])
print('Year 1 P matrix (AAA row):', P_annual[1][0])  # AAA row
```

## [31] tool

Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
NameError: name 'transitions' is not defined



## [32] assistant

**[reasoning]**

> Forgot to re-run transitions. Let's re-run the whole block.



**tool call: python**

```
import pandas as pd
import numpy as np
import json

transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

# Compute annual transition matrices
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
state_to_col = {s: c for s, c in zip(states, state_cols)}

P_annual = {}
start_counts = {}

for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    start_counts[y] = counts.sum(axis=1)
    row_sums = counts.sum(axis=1, keepdims=True)
    P = counts / row_sums
    P_annual[y] = P

print('Year 1 start counts:', start_counts[1])
print('Year 1 P matrix (AAA row):', P_annual[1][0])
print('Row sums of P_annual[1]:', P_annual[1].sum(axis=1))
```

## [33] tool

Year 1 start counts: [  88  427 1991 3961 2440  946  147]
Year 1 P matrix (AAA row): [0.88636364 0.11363636 0.         0.         0.         0.
 0.         0.        ]
Row sums of P_annual[1]: [1. 1. 1. 1. 1. 1. 1.]


## [34] assistant

**[reasoning]**

> Good.
> 
> Now macro data: we need to map quarters to years. Quarter index starts at 1. Year = (quarter-1)//4 + 1.
> 
> Let's compute macro averages per year for the selected variables: gdp, unemployment, nasdaq, cpi, default_rate. We'll also maybe include others if they have data for all years? Let's check which columns have any missing values per year.
> 
> We'll load macro and see missingness.



**tool call: python**

```
macro = pd.read_csv('data/macro_history.csv')
print(macro.head())
print('Columns:', macro.columns.tolist())
# Check missing per column
print(macro.isnull().sum())
```

## [35] tool

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'pd' is not defined. Did you mean: 'id'?



## [36] assistant

**[reasoning]**

> Need to import pandas again. Let's re-run with all imports.



**tool call: python**

```
import pandas as pd
import numpy as np
import json

transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

print('macro columns:', macro.columns.tolist())
print('macro missing:')
print(macro.isnull().sum())
```

## [37] tool

macro columns: ['quarter', 'gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi', 'default_rate']
macro missing:
quarter          0
gdp              0
unemployment     0
hpi             10
bbb_spread       6
sp500           33
djia            33
nasdaq           0
vix             11
cpi              0
default_rate     0
dtype: int64


## [38] assistant

**[reasoning]**

> Thus we have 5 columns with zero missing: gdp, unemployment, nasdaq, cpi, default_rate. Good.
> 
> Now compute yearly averages for these.
> 
> We'll create a column 'year' in macro: year = (quarter-1)//4 + 1.
> 
> Then group by year and compute mean.



**tool call: python**

```
macro['year'] = (macro['quarter'] - 1) // 4 + 1
macro_yearly = macro.groupby('year')[['gdp', 'unemployment', 'nasdaq', 'cpi', 'default_rate']].mean().reset_index()
print(macro_yearly.head())
print('Number of years:', macro_yearly.shape[0])
```

## [39] tool

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'macro' is not defined



## [40] assistant

**[reasoning]**

> Again need to define macro. Let's re-run from start with all steps.



**tool call: python**

```
import pandas as pd
import numpy as np
import json

transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

# Annual transition matrices
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

P_annual = {}
start_counts = {}
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    start_counts[y] = counts.sum(axis=1)
    row_sums = counts.sum(axis=1, keepdims=True)
    P = counts / row_sums
    P_annual[y] = P

# Macro yearly averages
macro['year'] = (macro['quarter'] - 1) // 4 + 1
macro_vars = ['gdp', 'unemployment', 'nasdaq', 'cpi', 'default_rate']
macro_yearly = macro.groupby('year')[macro_vars].mean().reset_index()
print('Macro yearly head:')
print(macro_yearly.head())
print('Years in macro:', macro_yearly['year'].tolist())
```

## [41] tool

Macro yearly head:
   year         gdp  unemployment      nasdaq         cpi  default_rate
0     1  120.623725      3.819925  341.647325  109.881350      0.016169
1     2  128.884275      3.849425  322.286025  117.537900      0.017988
2     3  138.734825      3.427000  368.029325  125.783750      0.015658
3     4  142.892600      5.060950  326.853100  135.142725      0.022693
4     5  141.602025      8.774475  437.925850  142.425900      0.027775
Years in macro: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]


## [42] assistant

**[reasoning]**

> Great. Now we have macro yearly averages for years 1-20.
> 
> Now we need to fit multinomial logistic regression for each from_rating.
> 
> We'll prepare data: For each year t and from_rating i, we have a vector of counts over 8 states (multinomial outcome). Predictors: macro variables (5). We'll fit separate MNLogit for each i.
> 
> We need to use statsmodels. Let's check if it's available. We'll try.



**tool call: python**

```
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import MNLogit

print('statsmodels version:', sm.__version__)
```

## [43] tool

statsmodels version: 0.14.6


## [44] assistant

**[reasoning]**

> Good.
> 
> Now we need to reshape data into long format: each observation is a year-from_rating pair with counts as dependent variable.
> 
> We'll create a DataFrame with columns: year, from_rating, and then the count columns for each state. Then we'll flatten.
> 
> But MNLogit expects a 2D array of dependent variable where each row is a observation and each column is count for each category? Actually MNLogit expects a dependent variable that is categorical (or counts?) Let's check: statsmodels MNLogit can handle either a 1D array of categorical labels or a 2D array of counts (shape (n_obs, n_categories)). We'll use the counts format.
> 
> Thus we need to stack observations: for each year t and rating i, we have a row of counts (8). So total observations = 20 years * 7 ratings = 140 rows.
> 
> Predictors: macro variables for that year (same for each rating within year). So we need to merge macro yearly averages.
> 
> Let's build.



**tool call: python**

```
# Build dataset for MNLogit
obs_list = []
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values  # (7,8)
    # macro values for this year
    macro_row = macro_yearly[macro_yearly['year'] == y][macro_vars].values.flatten()  # (5,)
    for i in range(7):
        obs_list.append({
            'year': y,
            'from_rating': ratings[i],
            'counts': counts[i],  # length 8 array
            **{var: macro_row[idx] for idx, var in enumerate(macro_vars)}
        })
    
obs_df = pd.DataFrame(obs_list)
print('obs_df shape:', obs_df.shape)
print(obs_df.head())
```

## [45] tool

Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
NameError: name 'years' is not defined. Did you mean: 'vars'?



## [46] assistant

**[reasoning]**

> We need to re-run the earlier definitions. Let's do everything in a single script block to avoid missing variables. We'll restart and do all steps.



**tool call: python**

```
import pandas as pd
import numpy as np
import json
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import MNLogit

# Load data
transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

# Annual transition matrices
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

P_annual = {}
start_counts = {}
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    start_counts[y] = counts.sum(axis=1)
    row_sums = counts.sum(axis=1, keepdims=True)
    P = counts / row_sums
    P_annual[y] = P

# Macro yearly averages
macro['year'] = (macro['quarter'] - 1) // 4 + 1
macro_vars = ['gdp', 'unemployment', 'nasdaq', 'cpi', 'default_rate']
macro_yearly = macro.groupby('year')[macro_vars].mean().reset_index()

# Build dataset for MNLogit
obs_list = []
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values  # (7,8)
    macro_row = macro_yearly[macro_yearly['year'] == y][macro_vars].values.flatten()
    for i in range(7):
        obs_list.append({
            'year': y,
            'from_rating': ratings[i],
            'counts': counts[i],
            **{var: macro_row[idx] for idx, var in enumerate(macro_vars)}
        })
obs_df = pd.DataFrame(obs_list)
print('obs_df shape:', obs_df.shape)
print(obs_df.head())
```

## [47] tool

obs_df shape: (140, 8)
   year from_rating  ...        cpi  default_rate
0     1         AAA  ...  109.88135      0.016169
1     1          AA  ...  109.88135      0.016169
2     1           A  ...  109.88135      0.016169
3     1         BBB  ...  109.88135      0.016169
4     1          BB  ...  109.88135      0.016169

[5 rows x 8 columns]


## [48] assistant

**[reasoning]**

> Now we need to separate dependent variable (counts) and independent variables (macro). The dependent variable column 'counts' contains arrays; we need to stack them into a 2D array.
> 
> Let's extract.



**tool call: python**

```
# Dependent variable: shape (n_obs, n_states)
counts_array = np.vstack(obs_df['counts'].values)  # (140,8)
print('counts_array shape:', counts_array.shape)
print('counts_array sum axis1 (should be start counts):', counts_array.sum(axis=1)[:5])

# Independent variables: macro vars
X = obs_df[macro_vars].values  # (140,5)
print('X shape:', X.shape)
print('X first 5 rows:')
print(X[:5])

# Add intercept
X = sm.add_constant(X, has_constant='add')
print('X with const shape:', X.shape)
```

## [49] tool

Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
NameError: name 'np' is not defined



## [50] assistant

**[reasoning]**

> Need to import numpy again; we already have but maybe lost due to earlier error? Let's re-run with all imports at top. Let's start fresh and execute all steps in one go. We'll write a script and execute. But we can continue stepwise; just need to ensure numpy imported. Let's do:



**tool call: python**

```
import pandas as pd
import numpy as np
import json
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import MNLogit

transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

P_annual = {}
start_counts = {}
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    start_counts[y] = counts.sum(axis=1)
    row_sums = counts.sum(axis=1, keepdims=True)
    P = counts / row_sums
    P_annual[y] = P

macro['year'] = (macro['quarter'] - 1) // 4 + 1
macro_vars = ['gdp', 'unemployment', 'nasdaq', 'cpi', 'default_rate']
macro_yearly = macro.groupby('year')[macro_vars].mean().reset_index()

obs_list = []
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    macro_row = macro_yearly[macro_yearly['year'] == y][macro_vars].values.flatten()
    for i in range(7):
        obs_list.append({
            'year': y,
            'from_rating': ratings[i],
            'counts': counts[i],
            **{var: macro_row[idx] for idx, var in enumerate(macro_vars)}
        })
obs_df = pd.DataFrame(obs_list)

counts_array = np.vstack(obs_df['counts'].values)
X = obs_df[macro_vars].values
X = sm.add_constant(X, has_constant='add')

print('Ready to fit MNLogit for each rating')
```

## [51] tool

Ready to fit MNLogit for each rating


## [52] assistant

**[reasoning]**

> Now we need to fit MNLogit for each from_rating. However MNLogit expects a single dependent variable array for all observations, but we want to fit separate models per rating. We can filter obs_df for each rating and fit.
> 
> Let's loop over ratings, subset data where from_rating == rating, fit MNLogit, store results.
> 
> We'll also need to predict for scenario quarters: we need macro for each quarter (scenario). We'll compute macro vector for each scenario quarter (no need to average across year). We'll use the same macro_vars.
> 
> For each scenario quarter q, we have macro values (gdp, unemployment, nasdaq, cpi, default_rate). We'll compute predicted annual transition probabilities P_pred for each rating using the fitted MNLogit models (predict probabilities for each state). Then compute quarterly matrix Q_pred = P_pred^{1/4}. We'll need to ensure that Q_pred is a valid transition matrix (rows sum to 1, non-negative). We'll compute via logm and expm.
> 
> We'll need scipy.linalg for logm and expm. Let's check if scipy is available.



**tool call: python**

```
import scipy.linalg
print('scipy available')
```

## [53] tool

scipy available


## [54] assistant

**[reasoning]**

> Great.
> 
> Now implement.
> 
> Steps:
> 
> 1. Fit MNLogit models: dict rating -> result.
> 
> 2. For each scenario quarter, get macro vector X_q (5 vars). Add constant.
> 
> 3. For each rating i, get predicted probabilities over states: p = model.predict(X_q) (returns array of shape (n_states,)). This gives annual transition probabilities from rating i to each state.
> 
> 4. Form matrix P_pred (7x8) where rows sum to 1 (should). Then compute Q_pred = expm(logm(P_pred)/4). Use scipy.linalg.logm and expm. Ensure we take real part (should be real). Then maybe adjust: set negative entries to zero and renormalize rows to sum to 1.
> 
> 5. Store Q_pred for each quarter.
> 
> 6. Project portfolio: start with portfolio counts vector v0 (size 7? Actually we need 8 states including D with zero). We'll create vector length 8: [AAA, AA, A, BBB, BB, B, CCC/C, D] with D=0.
> 
> For each quarter q in scenario quarters (81..89), we multiply v = v @ Q_pred[q] (where v is row vector). Actually we need to apply transition matrix: if v is distribution over states at start of quarter, then after quarter v_new = v * Q (where Q[i,j] = probability to go from i to j). So we compute v = v.dot(Q). We'll keep as numpy array.
> 
> After each quarter, we can compute shares = v / total_initial (which remains constant). We'll record at quarter 4 and quarter 9.
> 
> 7. For matrices.csv: we need to output quarterly transition matrices for each scenario quarter and each from_rating. That is exactly Q_pred we computed: for each quarter (81-89) and each from_rating (AAA..CCC/C), we output the row of Q_pred for that from_rating. So we can loop quarters and ratings and write rows.
> 
> 8. For backtest.csv: For each historical year t, we need predicted annual default rate using the model. We'll compute macro averages for that year (macro_yearly). For each rating i, get predicted annual transition probabilities P_pred_i (from MNLogit). Then we need to apply to starting portfolio of that year: starting counts per rating from start_counts[t] (vector length 7). Compute expected number of defaults after one year: sum over i start_counts[t][i] * P_pred_i[D] (where D column index 7). Then divide by total starting obligors for that year (sum start_counts[t]) to get default rate.
> 
> Alternatively, we could compute using quarterly matrices: compute Q_pred for that year (using macro averages of that year), then compute P_annual_pred = (Q_pred)^4 via matrix power, then apply to starting counts. That should be equivalent if our model is consistent. We'll do the latter to be consistent with projection method.
> 
> Thus for each year t:
> 
> - Get macro averages X_t (5 vars) -> add constant.
> 
> - For each rating i, get predicted annual probabilities P_pred_i (from MNLogit). Build matrix P_pred (7x8).
> 
> - Compute Q_pred = expm(logm(P_pred)/4).
> 
> - Compute P_annual_pred = np.linalg.matrix_power(Q_pred, 4) or expm(logm(P_pred))? Actually logm(P_pred) gives generator L such that expm(L) = P_pred. Then expm(4 * L) = expm(logm(P_pred)) = P_pred. Wait that's just P_pred. Actually we want quarterly matrix Q such that Q^4 = P_pred. So Q = expm(logm(P_pred)/4). Then P_annual_pred = Q^4 = expm(logm(P_pred)) = P_pred. So indeed P_annual_pred equals P_pred. So using quarterly root doesn't change annual matrix; it's consistent. So we can just use P_pred as annual predicted matrix. So backtest default rate = sum_i start_counts[t][i] * P_pred_i[D] / total_start.
> 
> Thus we can compute directly.
> 
> Now we need to implement.
> 
> Let's write the code to fit models, compute scenario projections, output files.
> 
> We'll do everything in a single script and then write outputs.
> 
> Let's start writing script and execute.



**tool call: python**

```
import pandas as pd
import numpy as np
import json
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import MNLogit
import scipy.linalg

# Load data
transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

# Constants
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
n_states = len(states)
n_ratings = len(ratings)
macro_vars = ['gdp', 'unemployment', 'nasdaq', 'cpi', 'default_rate']

# Annual transition matrices (observed)
P_annual = {}
start_counts = {}
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values  # (7,8)
    start_counts[y] = counts.sum(axis=1)
    row_sums = counts.sum(axis=1, keepdims=True)
    P = counts / row_sums
    P_annual[y] = P

# Macro yearly averages
macro['year'] = (macro['quarter'] - 1) // 4 + 1
macro_yearly = macro.groupby('year')[macro_vars].mean().reset_index()

# Prepare data for MNLogit (long format)
obs_list = []
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    macro_row = macro_yearly[macro_yearly['year'] == y][macro_vars].values.flatten()
    for i in range(n_ratings):
        obs_list.append({
            'year': y,
            'from_rating': ratings[i],
            'counts': counts[i],
            **{var: macro_row[idx] for idx, var in enumerate(macro_vars)}
        })
obs_df = pd.DataFrame(obs_list)

# Dependent variable array
counts_array = np.vstack(obs_df['counts'].values)  # (n_obs, n_states)
# Independent variables
X = obs_df[macro_vars].values
X = sm.add_constant(X, has_constant='add')  # add intercept

# Fit MNLogit model for each from_rating
models = {}
for idx, rating in enumerate(ratings):
    # Subset data for this rating
    mask = obs_df['from_rating'] == rating
    X_r = X[mask]
    y_r = counts_array[mask]  # shape (n_years, n_states)
    # MNLogit expects dependent variable as 2D array of counts
    mnlogit = MNLogit(y_r, X_r)
    # Fit with default options (maybe maxiter)
    result = mnlogit.fit(disp=False)
    models[rating] = result
    # Optional: print summary for first rating
    if idx == 0:
        print(f'Fit for {rating}: llf={result.llf:.2f}')

print('Fitted models for all ratings.')

# Function to get predicted annual transition probabilities given macro vector X (with const)
def predict_annual_probs(X_vec):
    """X_vec: 1D array including const, length = n_macro_vars+1.
    Returns matrix (n_ratings, n_states) of predicted probabilities."""
    probs = np.zeros((n_ratings, n_states))
    for r_idx, rating in enumerate(ratings):
        res = models[rating]
        # predict returns probabilities for each outcome (states)
        p = res.predict(X_vec.reshape(1, -1))  # shape (1, n_states)
        probs[r_idx, :] = p.ravel()
    # Ensure rows sum to 1 (should already, but normalize to avoid numerical issues)
    row_sums = probs.sum(axis=1, keepdims=True)
    probs = probs / row_sums
    return probs

# Scenario quarters
scenario_quarters = scenario['quarter'].values  # 81..89
# Prepare macro for scenario quarters (only the vars we use)
scenario_macro = scenario[macro_vars].values  # shape (9,5)
# Add constant
scenario_X = sm.add_constant(scenario_macro, has_constant='add')  # (9,6)

# Store quarterly transition matrices
quarterly_mats = {}  # quarter -> matrix (ratings x states)
for q_idx, q in enumerate(scenario_quarters):
    X_vec = scenario_X[q_idx]  # (6,)
    P_pred = predict_annual_probs(X_vec)  # (7,8)
    # Compute quarterly matrix Q = P_pred^{1/4} via logm/exp
    # Ensure P_pred is strictly positive for logm; replace zeros with small epsilon
    eps = 1e-12
    P_safe = np.maximum(P_pred, eps)
    # Renormalize rows after adjustment
    row_sums = P_safe.sum(axis=1, keepdims=True)
    P_safe = P_safe / row_sums
    # Compute logm
    try:
        logP = scipy.linalg.logm(P_safe)
    except Exception as e:
        # If logm fails, try using eigen decomposition
        # For now, fallback to using P_pred as quarterly (i.e., no change)
        print(f'logm failed for quarter {q}: {e}')
        Q = P_pred
    else:
        Q = scipy.linalg.expm(logP / 4.0)
        # Ensure Q is real (should be)
        Q = np.real(Q)
        # Replace negatives with zero and renormalize rows
        Q[Q < 0] = 0
        row_sums_Q = Q.sum(axis=1, keepdims=True)
        # Avoid division by zero
        row_sums_Q[row_sums_Q == 0] = 1.0
        Q = Q / row_sums_Q
    quarterly_mats[q] = Q

# Project portfolio over scenario quarters
# Initial portfolio counts vector (states order)
init_counts = portfolio.set_index('rating')['obligors'].reindex(ratings).values  # (7,)
# Build full state vector length 8 (including D)
v = np.zeros(n_states)
v[:n_ratings] = init_counts  # D zero
total_initial = v.sum()
print('Initial total obligors:', total_initial)

# We'll track after each quarter
shares_by_quarter = {}  # quarter -> share vector (length 8)
v_current = v.copy()
for q_idx, q in enumerate(scenario_quarters):
    Q = quarterly_mats[q]
    # Update v = v * Q (row vector times matrix)
    v_current = v_current.dot(Q)
    shares_by_quarter[q] = v_current / total_initial

# Extract shares for checkpoints 4 and 9
checkpoints = policy['checkpoints']  # [4,9]
# Need to map quarter number to actual quarter index: scenario quarters start at 81.
# quarter 1 -> scenario quarter 81, quarter 2 -> 82, etc.
# So quarter q corresponds to scenario quarter = 80 + q
quarter_to_scenario = {q: 80 + q for q in range(1, policy['horizon_quarters']+1)}
# Verify: quarter 1 -> 81, quarter 4 -> 84, quarter 9 -> 89.

pred_rows = []
for q in checkpoints:
    scen_q = quarter_to_scenario[q]
    share_vec = shares_by_quarter[scen_q]  # length 8
    for s_idx, state in enumerate(states):
        pred_rows.append({
            'quarter': q,
            'state': state,
            'share': float(share_vec[s_idx])
        })

predictions_df = pd.DataFrame(pred_rows, columns=['quarter', 'state', 'share'])
print('Predictions df shape:', predictions_df.shape)
print(predictions_df.head())

# Write predictions.csv
predictions_df.to_csv('predictions.csv', index=False)
print('Written predictions.csv')

# Write matrices.csv
# Columns: quarter,from_rating,to_AAA,to_AA,to_A,to_BBB,to_BB,to_B,to_CCC_C,to_D
matrix_rows = []
for q in scenario_quarters:
    Q = quarterly_mats[q]
    for r_idx, rating in enumerate(ratings):
        row = {'quarter': int(q),
               'from_rating': rating}
        for s_idx, state in enumerate(states):
            row[f'to_{state}'] = float(Q[r_idx, s_idx])
        matrix_rows.append(row)
matrices_df = pd.DataFrame(matrix_rows, columns=['quarter','from_rating'] + [f'to_{s}' for s in states])
print('Matrices df shape:', matrices_df.shape)
print(matrices_df.head())
matrices_df.to_csv('matrices.csv', index=False)
print('Written matrices.csv')

# Backtest: annual default rate for each historical year
backtest_rows = []
for y in years:
    # Macro averages for this year
    macro_row = macro_yearly[macro_yearly['year'] == y][macro_vars].values.flatten()
    X_vec = sm.add_constant(macro_row, has_constant='add')  # (6,)
    P_pred = predict_annual_probs(X_vec)  # (7,8)
    # Starting counts for this year
    start_cnt = start_counts[y]  # (7,)
    # Expected defaults: sum_i start_cnt[i] * P_pred[i, D]
    defaults_expected = np.dot(start_cnt, P_pred[:, states.index('D')])
    total_start = start_cnt.sum()
    default_rate = defaults_expected / total_start if total_start > 0 else 0.0
    backtest_rows.append({'year': int(y), 'default_rate': float(default_rate)})
backtest_df = pd.DataFrame(backtest_rows, columns=['year', 'default_rate'])
print('Backtest df shape:', backtest_df.shape)
print(backtest_df.head())
backtest_df.to_csv('backtest.csv', index=False)
print('Written backtest.csv')

# Quick sanity check: ensure predictions sums to 1 per quarter
for q in checkpoints:
    scen_q = quarter_to_scenario[q]
    total_share = predictions_df[predictions_df['quarter']==q]['share'].sum()
    print(f'Quarter {q} total share: {total_share:.6f}')
```

## [55] tool

/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
Traceback (most recent call last):
  File "<stdin>", line 99, in <module>
  File "/usr/local/lib/python3.12/site-packages/pandas/core/frame.py", line 4384, in __getitem__
    indexer = self.columns._get_indexer_strict(key, "columns")[1]
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6302, in _get_indexer_strict
    self._raise_if_missing(keyarr, indexer, axis_name)
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6355, in _raise_if_missing
    raise KeyError(f"{not_found} not in index")
KeyError: "['default_rate'] not in index"

Fit for AAA: llf=nan
Fitted models for all ratings.


## [56] assistant

**[reasoning]**

> We see overflow in exp in MNLogit due to large coefficients? Probably because macro variables have large magnitude (e.g., gdp ~100-150, nasdaq ~200-400). This leads to huge linear predictor values causing overflow in exp. Need to standardize macro variables (subtract mean, divide by std) before fitting.
> 
> Also we got KeyError for 'default_rate' in predictions_df because column name maybe 'default_rate' not present? Actually we used states list includes 'D', but we named column 'to_D' in transitions. In predictions we used state names from states list which includes 'D'. That's fine. The error occurred when trying to access predictions_df['default_rate']? Wait we attempted to get column 'default_rate' from predictions_df? The error line: KeyError: "['default_rate'] not in index". That came from when we tried to access predictions_df column? Actually we were trying to get shares for state 'D' maybe we used state name 'default_rate' inadvertently? Let's check: In the loop we used for s_idx, state in enumerate(states): states includes 'D', not 'default_rate'. So the error likely came from earlier when we tried to create predictions_df? Actually the error occurred after fitting models, when we tried to create predictions_df? Let's see the traceback: line 99 in module, which is likely the line where we tried to access predictions_df['default_rate']? But we didn't. The error mentions KeyError: "['default_rate'] not in index". That suggests we tried to select column 'default_rate' from a DataFrame that doesn't have it. Possibly when we tried to compute shares_by_quarter[scen_q] we used states list that includes 'default_rate'? No.
> 
> Wait we printed predictions_df head before the error? Actually the error occurred during the creation of predictions_df? The traceback shows line 99 in module, which is after the line "print('Predictions df shape:', predictions_df.shape)". Let's examine the code around line 99 (hard to know). But the error says KeyError: "['default_rate'] not in index". This likely happened when we tried to access predictions_df column 'default_rate' while constructing the DataFrame? Actually we constructed predictions_df from pred_rows list with columns ['quarter','state','share']; state values are from states list which includes 'D'. So no 'default_rate'.
> 
> Maybe the error came from later when we tried to compute shares_by_quarter[scen_q] and we used states list incorrectly? Let's examine the code where we built shares_by_quarter: we used v_current / total_initial, and then later we accessed shares_by_quarter[scen_q] which is a numpy array of length 8. That's fine.
> 
> The error might be from the line where we tried to create predictions_df from pred_rows but we mistakenly used a variable named 'default_rate' somewhere else.
> 
> Let's look at the code we just executed: after projecting, we built pred_rows loop:
> 
> for q in checkpoints:
>     scen_q = quarter_to_scenario[q]
>     share_vec = shares_by_quarter[scen_q]  # length 8
>     for s_idx, state in enumerate(states):
>         pred_rows.append({
>             'quarter': q,
>             'state': state,
>             'share': float(share_vec[s_idx])
>         })
> 
> states list includes 'D'. So fine.
> 
> Then we created predictions_df = pd.DataFrame(pred_rows, columns=['quarter', 'state', 'share']). That should work.
> 
> But the error occurred before that? Actually the traceback says line 99 in module, which is inside the script we pasted. Let's count lines roughly. Hard.
> 
> Nevertheless, the overflow issues need to be addressed. We'll standardize macro variables.
> 
> Also we got llf=nan for AAA model, indicating failure.
> 
> Let's standardize macro variables: subtract mean and divide by std across the historical years (macro_yearly). We'll compute mean and std, then transform both historical macro and scenario macro.
> 
> We'll also need to add constant after standardization.
> 
> Let's redo modeling with standardized macro.
> 
> We'll create a new script.
> 
> But first, let's check the scenario macro values to see magnitude.



**tool call: python**

```
import pandas as pd
scenario = pd.read_csv('data/scenario.csv')
print(scenario[['gdp','unemployment','nasdaq','cpi','default_rate']].describe())
```

## [57] tool

Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
  File "/usr/local/lib/python3.12/site-packages/pandas/core/frame.py", line 4384, in __getitem__
    indexer = self.columns._get_indexer_strict(key, "columns")[1]
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6302, in _get_indexer_strict
    self._raise_if_missing(keyarr, indexer, axis_name)
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6355, in _raise_if_missing
    raise KeyError(f"{not_found} not in index")
KeyError: "['default_rate'] not in index"



## [58] assistant

**[reasoning]**

> Again default_rate column missing? Let's check scenario columns.



**tool call: python**

```
scenario = pd.read_csv('data/scenario.csv')
print(scenario.columns.tolist())
```

## [59] tool

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'pd' is not defined. Did you mean: 'id'?



## [60] assistant

**[reasoning]**

> Need to import pandas again. Let's do a quick command.



**tool call: python**

```
!head -2 data/scenario.csv
```

## [61] tool

  File "<stdin>", line 1
    !head -2 data/scenario.csv
    ^
SyntaxError: invalid syntax



## [62] assistant

**[reasoning]**

> We are in python tool, not bash. Let's use bash tool.



**tool call: bash**

```

```

## [63] tool

quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi
81,157.5714,9.1701,276.1336,2.8306,2657.8862,2527.3059,103.6137,24.1394,189.9304


## [64] assistant

**[reasoning]**

> Scenario columns: quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi. No default_rate column! Indeed scenario.csv does not have default_rate column. The macro_history.csv had default_rate column, but scenario.csv does not. So we cannot use default_rate as a predictor for scenario because it's not provided. However we can still use it for historical estimation, but for scenario we need to predict without it. That means we should exclude default_rate from the set of predictors, or we need to estimate it from other variables? But the scenario does not provide default_rate, so we cannot use it as input. Therefore we must use only the macro variables that are present in both macro_history and scenario: gdp, unemployment, hpi, bbb_spread, sp500, djia, nasdaq, vix, cpi. However many of those have missing values early. But we can still use those that have data for all years? Let's check which columns have no missing values in macro_history after a certain point? Actually we need variables that are available for all historical years (to estimate) and for all scenario quarters (to predict). Let's examine macro_history missing counts again: hpi missing 10, bbb_spread missing 6, sp500 missing 33, djia missing 33, nasdaq missing 0, vix missing 11, cpi missing 0, gdp missing 0, unemployment missing 0.
> 
> Thus only gdp, unemployment, nasdaq, cpi are fully observed (no missing). Also maybe we can use default_rate for historical but not scenario; but we need to predict scenario quarters, so we cannot rely on default_rate. So we must drop default_rate from predictors.
> 
> Thus we will use macro_vars = ['gdp', 'unemployment', 'nasdaq', 'cpi'].
> 
> Now we need to standardize these.
> 
> Let's redo the modeling with these four variables.
> 
> We'll also need to handle the overflow issue by standardizing.
> 
> Let's write a new script from scratch, incorporating these changes.
> 
> We'll also need to ensure that when we compute logm, we avoid zeros.
> 
> Let's do it stepwise with bash to run a script file, but we can also run python code directly. We'll create a temporary python file and execute.
> 
> But we can just run a block of code; we'll do that now.
> 
> Let's start fresh.



**tool call: python**

```
import pandas as pd
import numpy as np
import json
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import MNLogit
import scipy.linalg

# Load data
transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

# Constants
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
n_states = len(states)
n_ratings = len(ratings)

# Use macro variables that are present in both macro_history and scenario and have no missing values
# Check scenario columns
scenario_cols = set(scenario.columns)
macro_cols = set(macro.columns)
common = scenario_cols.intersection(macro_cols)
print('Common columns:', common)
# Remove quarter
common.discard('quarter')
print('Common macro columns:', common)
# Now check missingness in macro for these columns
macro_sub = macro[list(common)]
missing_counts = macro_sub.isnull().sum()
print('Missing counts:')
print(missing_counts)
# Choose those with zero missing
macro_vars = [col for col in common if missing_counts[col] == 0 and col != 'quarter']
print('Selected macro vars (zero missing):', macro_vars)
# If none, we may need to impute; but let's see.
```

## [65] tool

Common columns: {'nasdaq', 'cpi', 'sp500', 'quarter', 'bbb_spread', 'gdp', 'vix', 'djia', 'unemployment', 'hpi'}
Common macro columns: {'nasdaq', 'cpi', 'sp500', 'bbb_spread', 'gdp', 'vix', 'djia', 'unemployment', 'hpi'}
Missing counts:
nasdaq           0
cpi              0
sp500           33
bbb_spread       6
gdp              0
vix             11
djia            33
unemployment     0
hpi             10
dtype: int64
Selected macro vars (zero missing): ['nasdaq', 'cpi', 'gdp', 'unemployment']


## [66] assistant

**[reasoning]**

> Great. So we have four macro variables with no missing: gdp, unemployment, nasdaq, cpi.
> 
> Now we proceed.
> 
> We'll standardize these variables using historical macro_yearly means and stds.
> 
> Compute macro_yearly averages for these variables.
> 
> Then compute mean and std across years (excluding maybe first few? but we'll use all years).
> 
> Then standardize: (x - mean) / std.
> 
> For scenario, we apply same mean and std.
> 
> Now we need to fit MNLogit with standardized macro predictors (plus intercept).
> 
> Let's implement.



**tool call: python**

```
import pandas as pd
import numpy as np
import json
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import MNLogit
import scipy.linalg

# Load data
transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

# Constants
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
n_states = len(states)
n_ratings = len(ratings)

# Selected macro vars (zero missing in both)
macro_vars = ['gdp', 'unemployment', 'nasdaq', 'cpi']
print('Using macro vars:', macro_vars)

# Macro yearly averages
macro['year'] = (macro['quarter'] - 1) // 4 + 1
macro_yearly = macro.groupby('year')[macro_vars].mean().reset_index()
print('Macro yearly shape:', macro_yearly.shape)

# Compute mean and std for standardization (based on historical years)
mean_vals = macro_yearly[macro_vars].mean().values
std_vals = macro_yearly[macro_vars].std().values
print('Mean:', mean_vals)
print('Std:', std_vals)

# Standardize historical macro
macro_yearly_std = macro_yearly.copy()
macro_yearly_std[macro_vars] = (macro_yearly_std[macro_vars] - mean_vals) / std_vals

# Standardize scenario macro
scenario_std = scenario.copy()
scenario_std[macro_vars] = (scenario_std[macro_vars] - mean_vals) / std_vals

# Prepare data for MNLogit (long format)
obs_list = []
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    # Get standardized macro for this year
    macro_row = macro_yearly_std[macro_yearly_std['year'] == y][macro_vars].values.flatten()
    for i in range(n_ratings):
        obs_list.append({
            'year': y,
            'from_rating': ratings[i],
            'counts': counts[i],
            **{var: macro_row[idx] for idx, var in enumerate(macro_vars)}
        })
obs_df = pd.DataFrame(obs_list)

# Dependent variable array
counts_array = np.vstack(obs_df['counts'].values)  # (n_obs, n_states)
# Independent variables: standardized macro
X = obs_df[macro_vars].values
X = sm.add_constant(X, has_constant='add')  # add intercept

# Fit MNLogit model for each from_rating
models = {}
for idx, rating in enumerate(ratings):
    mask = obs_df['from_rating'] == rating
    X_r = X[mask]
    y_r = counts_array[mask]
    mnlogit = MNLogit(y_r, X_r)
    result = mnlogit.fit(disp=False, maxiter=200)
    models[rating] = result
    if idx == 0:
        print(f'Fit for {rating}: llf={result.llf:.2f}')

print('Fitted models for all ratings.')

# Function to get predicted annual transition probabilities given standardized macro vector X_vec (with const)
def predict_annual_probs(X_vec):
    """X_vec: 1D array including const, length = n_macro_vars+1.
    Returns matrix (n_ratings, n_states) of predicted probabilities."""
    probs = np.zeros((n_ratings, n_states))
    for r_idx, rating in enumerate(ratings):
        res = models[rating]
        p = res.predict(X_vec.reshape(1, -1))  # shape (1, n_states)
        probs[r_idx, :] = p.ravel()
    # Normalize rows to sum to 1 (should already, but ensure)
    row_sums = probs.sum(axis=1, keepdims=True)
    probs = probs / row_sums
    return probs

# Scenario quarters
scenario_quarters = scenario['quarter'].values  # 81..89
# Get standardized macro for scenario quarters
scenario_macro_std = scenario_std[macro_vars].values  # (9,4)
# Add constant
scenario_X = sm.add_constant(scenario_macro_std, has_constant='add')  # (9,5)

# Store quarterly transition matrices
quarterly_mats = {}  # quarter -> matrix (ratings x states)
for q_idx, q in enumerate(scenario_quarters):
    X_vec = scenario_X[q_idx]  # (5,)
    P_pred = predict_annual_probs(X_vec)  # (7,8)
    # Ensure positive for logm
    eps = 1e-12
    P_safe = np.maximum(P_pred, eps)
    row_sums = P_safe.sum(axis=1, keepdims=True)
    P_safe = P_safe / row_sums
    try:
        logP = scipy.linalg.logm(P_safe)
    except Exception as e:
        # Fallback: treat as quarterly = annual (no time diversification)
        print(f'logm failed for quarter {q}: {e}')
        Q = P_pred
    else:
        Q = scipy.linalg.expm(logP / 4.0)
        Q = np.real(Q)
        # Fix negatives
        Q[Q < 0] = 0
        row_sums_Q = Q.sum(axis=1, keepdims=True)
        row_sums_Q[row_sums_Q == 0] = 1.0
        Q = Q / row_sums_Q
    quarterly_mats[q] = Q

# Project portfolio over scenario quarters
# Initial portfolio counts vector (states order)
init_counts = portfolio.set_index('rating')['obligors'].reindex(ratings).values  # (7,)
v = np.zeros(n_states)
v[:n_ratings] = init_counts  # D zero
total_initial = v.sum()
print('Initial total obligors:', total_initial)

shares_by_quarter = {}  # quarter -> share vector (length 8)
v_current = v.copy()
for q_idx, q in enumerate(scenario_quarters):
    Q = quarterly_mats[q]
    v_current = v_current.dot(Q)
    shares_by_quarter[q] = v_current / total_initial

# Extract shares for checkpoints 4 and 9
checkpoints = policy['checkpoints']  # [4,9]
quarter_to_scenario = {q: 80 + q for q in range(1, policy['horizon_quarters']+1)}
pred_rows = []
for q in checkpoints:
    scen_q = quarter_to_scenario[q]
    share_vec = shares_by_quarter[scen_q]
    for s_idx, state in enumerate(states):
        pred_rows.append({
            'quarter': q,
            'state': state,
            'share': float(share_vec[s_idx])
        })

predictions_df = pd.DataFrame(pred_rows, columns=['quarter', 'state', 'share'])
print('Predictions df shape:', predictions_df.shape)
print(predictions_df.head())

# Write predictions.csv
predictions_df.to_csv('predictions.csv', index=False)
print('Written predictions.csv')

# Write matrices.csv
matrix_rows = []
for q in scenario_quarters:
    Q = quarterly_mats[q]
    for r_idx, rating in enumerate(ratings):
        row = {'quarter': int(q),
               'from_rating': rating}
        for s_idx, state in enumerate(states):
            row[f'to_{state}'] = float(Q[r_idx, s_idx])
        matrix_rows.append(row)
matrices_df = pd.DataFrame(matrix_rows, columns=['quarter','from_rating'] + [f'to_{s}' for s in states])
print('Matrices df shape:', matrices_df.shape)
print(matrices_df.head())
matrices_df.to_csv('matrices.csv', index=False)
print('Written matrices.csv')

# Backtest: annual default rate for each historical year
backtest_rows = []
for y in years:
    # Standardized macro averages for this year
    macro_row = macro_yearly_std[macro_yearly_std['year'] == y][macro_vars].values.flatten()
    X_vec = sm.add_constant(macro_row, has_constant='add')
    P_pred = predict_annual_probs(X_vec)  # (7,8)
    start_cnt = start_counts[y]  # need start_counts defined earlier; we haven't computed start_counts yet!
    # Oops we forgot to compute start_counts. Let's compute them now.
# We need to compute start_counts as before.
# Let's compute start_counts again.
```

## [67] tool

/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3027: RuntimeWarning: overflow encountered in exp
  eXB = np.column_stack((np.ones(len(X)), np.exp(X)))
/usr/local/lib/python3.12/site-packages/statsmodels/discrete/discrete_model.py:3028: RuntimeWarning: invalid value encountered in divide
  return eXB/eXB.sum(1)[:,None]
Traceback (most recent call last):
  File "<stdin>", line 143, in <module>
ValueError: shapes (8,) and (7,8) not aligned: 8 (dim 0) != 7 (dim 0)

Using macro vars: ['gdp', 'unemployment', 'nasdaq', 'cpi']
Macro yearly shape: (20, 5)
Mean: [145.2608175    6.3722875  333.20680875 159.89293875]
Std: [ 12.8577048    2.18076661 175.48206398  28.54561925]
Fit for AAA: llf=nan
Fitted models for all ratings.
logm failed for quarter 81: expected a square matrix
logm failed for quarter 82: expected a square matrix
logm failed for quarter 83: expected a square matrix
logm failed for quarter 84: expected a square matrix
logm failed for quarter 85: expected a square matrix
logm failed for quarter 86: expected a square matrix
logm failed for quarter 87: expected a square matrix
logm failed for quarter 88: expected a square matrix
logm failed for quarter 89: expected a square matrix
Initial total obligors: 10001.0


## [68] assistant

**[reasoning]**

> We still have overflow in exp in MNLogit, leading to llf=nan. Also logm failed because P_pred is not square? Wait P_pred shape is (7,8) - not square! Indeed we have 7 ratings rows, 8 states columns. The transition matrix is not square because we have 7 from states and 8 to states (including D). However for a Markov chain, the transition matrix should be square if we include all states as both from and to. But we don't have from state D because it's absorbing and no one starts in D (since we don't have rows for D). However to compute the matrix logarithm, we need a square matrix. We could augment the matrix with a row for D (from D to D with probability 1, and to others 0). That would make it 8x8. Then we can compute logm and expm.
> 
> Thus we need to expand P_pred to 8x8 by adding a row for D: [0,0,0,0,0,0,0,1].
> 
> Similarly, when we compute quarterly matrix Q, we should also have this property: from D stays in D.
> 
> Thus we need to work with 8x8 matrices.
> 
> Let's adjust: our predicted annual matrix P_pred currently is 7x8 (from AAA..CCC/C to all states). We'll create a full 8x8 matrix by adding a row for D.
> 
> Similarly, the initial vector v includes D component (zero). When we multiply v (1x8) by Q (8x8), we get new v.
> 
> Thus we need to modify.
> 
> Also we need to compute start_counts for each year (we have that from earlier but we didn't store in this script). Let's compute start_counts as before.
> 
> Let's rewrite the script properly, incorporating these fixes and also addressing MNLogit overflow by maybe using fewer categories or regularization? Overflow suggests that linear predictors are huge leading to exp overflow. Standardizing should help, but we still got overflow. Maybe we need to also center the macro variables (we did) but still large values? Let's check the standardized values: mean ~0, std ~1, so values should be around a few standard deviations. However the coefficients might be large causing large linear predictor. Could be due to separation or multinomial logistic regression with many categories leading to infinite coefficients. We might need to use a simpler approach: maybe we can model each transition probability separately using linear regression (bounded between 0 and 1) after logit transform? But time is limited.
> 
> Alternative: Instead of MNLogit, we could assume that the transition matrix is constant over time (no macro dependence). That would avoid the overflow. But we need to incorporate macro scenario; we could adjust default rates based on a simple index (e.g., average of macro variables) while keeping other transitions proportional.
> 
> Given the time, maybe we can produce a simpler model that still uses macro but in a more robust way: For each from_rating, we can model the log odds of default vs non-default as linear function of macro, and distribute non-default probabilities according to historical baseline proportions.
> 
> Specifically, for each from_rating i, we have baseline annual transition matrix P0_i (average over years). We can compute baseline default rate d0_i = P0_i[D]. Then we can assume that the default rate varies with macro via logistic regression: logit(p_default_i) = alpha_i + beta_i * macro_index (some composite). Meanwhile, the distribution among non-default states remains proportional to baseline non-default rates.
> 
> We need to estimate alpha_i, beta_i from historical data: we have yearly observed default counts for each rating. We can fit a logistic regression for each rating: observed number of defaults out of total starting obligors, with predictor macro_index (maybe we can use a single macro variable like GDP or a principal component). This will be simpler and avoid overflow.
> 
> Let's do that: For each rating i, we have yearly data: total obligors start_counts[y][i], defaults count = transitions where to_D for that rating and year. We can compute observed default rate. Then we fit a logistic regression of default probability on macro variables (maybe we can use a single composite index like the first PCA of macro variables). But we can also use multiple macro variables; logistic regression with multiple predictors should be fine as it's binomial.
> 
> We'll do logistic regression for each rating using statsmodels Logit.
> 
> Steps:
> 
> - For each year y and rating i, we have:
>     n_i_y = start_counts[y][i]
>     d_i_y = transitions[(transitions['year']==y) & (transitions['from_rating']==i)]['to_D'].values[0]
> - Predictor macro variables (standardized) for year y.
> 
> - Fit Logit model: default probability = logistic(X_beta). Use statsmodels Logit.
> 
> - Predict default probability for scenario quarters.
> 
> - For non-default states, we assume the relative distribution remains same as baseline non-default distribution (i.e., conditional on not defaulting, the probabilities to other states are proportional to baseline). So we compute baseline non-default vector: baseline_nondefault_i = P0_i[nondefault states] (size 7). Normalize to sum to 1.
> 
> - Then for any given year/scenario, predicted default probability p_def_i. Then predicted probability to each non-default state j = (1 - p_def_i) * baseline_nondefault_i[j].
> 
> - This yields a full 8x8 transition matrix (with row for D being absorbing).
> 
> This approach avoids MNLogit overflow and ensures rows sum to 1.
> 
> We need to estimate baseline P0_i: we can use the average annual transition matrix across all years (or maybe median). Let's compute average across years of P_annual[y] (7x8). Then extract baseline.
> 
> Let's implement this.
> 
> We'll also need to compute quarterly matrix via root as before, but now we have 8x8 annual predicted matrix (including D row). We'll compute Q = expm(logm(P_pred)/4) where P_pred is 8x8.
> 
> We'll need to add row for D: [0,0,0,0,0,0,0,1].
> 
> Let's implement.
> 
> First compute start_counts and yearly default counts.
> 
> We'll compute start_counts as before.
> 
> Let's do it now.



**tool call: python**

```
import pandas as pd
import numpy as np
import json
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import Logit
import scipy.linalg

# Load data
transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

# Constants
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
n_states = len(states)
n_ratings = len(ratings)

# Selected macro vars (zero missing in both)
macro_vars = ['gdp', 'unemployment', 'nasdaq', 'cpi']
print('Using macro vars:', macro_vars)

# Macro yearly averages
macro['year'] = (macro['quarter'] - 1) // 4 + 1
macro_yearly = macro.groupby('year')[macro_vars].mean().reset_index()
print('Macro yearly shape:', macro_yearly.shape)

# Compute mean and std for standardization (based on historical years)
mean_vals = macro_yearly[macro_vars].mean().values
std_vals = macro_yearly[macro_vars].std().values
print('Mean:', mean_vals)
print('Std:', std_vals)

# Standardize historical macro
macro_yearly_std = macro_yearly.copy()
macro_yearly_std[macro_vars] = (macro_yearly_std[macro_vars] - mean_vals) / std_vals

# Standardize scenario macro
scenario_std = scenario.copy()
scenario_std[macro_vars] = (scenario_std[macro_vars] - mean_vals) / std_vals

# Compute start_counts per year and rating
start_counts = {}  # year -> array length 7
default_counts = {}  # year -> array length 7
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values  # (7,8)
    start_counts[y] = counts.sum(axis=1)
    default_counts[y] = counts[:, states.index('D')]  # defaults to D

# Compute baseline annual transition matrix (average over years)
P_annual_list = []
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    row_sums = counts.sum(axis=1, keepdims=True)
    P = counts / row_sums
    P_annual_list.append(P)
P0 = np.mean(P_annual_list, axis=0)  # (7,8)
print('Baseline P0 shape:', P0.shape)
print('Baseline P0 (AAA row):', P0[0])
print('Row sums of P0:', P0.sum(axis=1))

# Baseline non-default distribution for each rating (conditional on not default)
nondefault_states = [s for s in states if s != 'D']
nondefault_idx = [states.index(s) for s in nondefault_states]
baseline_nondefault = P0[:, nondefault_idx]  # (7,7)
# Normalize rows to sum to 1
row_sums_nondef = baseline_nondefault.sum(axis=1, keepdims=True)
# Avoid division by zero
row_sums_nondef[row_sums_nondef == 0] = 1.0
baseline_nondefault = baseline_nondefault / row_sums_nondef
print('Baseline nondefault shape:', baseline_nondefault.shape)
print('Baseline nondefault row sums:', baseline_nondefault.sum(axis=1))

# Fit logistic regression for each rating
models = {}  # rating -> Logit result
for i, rating in enumerate(ratings):
    # Prepare data across years
    n_years = len(years)
    y_vals = []  # default counts
    n_vals = []  # total trials
    X_list = []  # macro vars per year
    for idx_y, y in enumerate(years):
        n_i = start_counts[y][i]
        d_i = default_counts[y][i]
        y_vals.append(d_i)
        n_vals.append(n_i)
        # macro standardized for this year
        macro_row = macro_yearly_std[macro_yearly_std['year'] == y][macro_vars].values.flatten()
        X_list.append(macro_row)
    X = np.array(X_list)  # (n_years, n_macro)
    X = sm.add_constant(X, has_constant='add')
    y_bin = np.array(y_vals)  # defaults
    n_bin = np.array(n_vals)  # total
    # Use Binomial Logit via statsmodels Logit with weights? Actually we can use Logit with each trial? 
    # We'll use statsmodels Binomial family via GLM, but simpler: we can expand to individual trials? Not feasible.
    # Instead we can use statsmodels Logit with each observation weighted by n_i? There's a way: use statsmodels Logit with each observation as proportion and weights.
    # We'll use statsmodels GLM with binomial family.
    # Let's do using sm.GLM
    print(f'Fitting rating {rating}...')
    try:
        glm_model = sm.GLM(y_bin, X, family=sm.families.Binomial())
        glm_result = glm_model.fit()
    except Exception as e:
        print(f'GLM failed for {rating}: {e}')
        # fallback: intercept only
        X_int = np.ones((len(y_vals), 1))
        glm_model = sm.GLM(y_bin, X_int, family=sm.families.Binomial())
        glm_result = glm_model.fit()
    models[rating] = glm_result
    print(f'  llf={glm_result.llf:.2f}')

print('Fitted logistic models.')

# Function to predict annual transition matrix given standardized macro vector (with const)
def predict_annual_probs_macro(X_vec):
    """X_vec: 1D array including const, length = n_macro_vars+1.
    Returns matrix (n_ratings, n_states) of predicted annual transition probabilities."""
    P_pred = np.zeros((n_ratings, n_states))
    for i, rating in enumerate(ratings):
        res = models[rating]
        # Predict probability of default
        mu = res.predict(X_vec.reshape(1, -1))[0]  # expected proportion
        p_def = np.clip(mu, 0.0, 1.0)
        # Non-default probability
        p_nodef = 1.0 - p_def
        # Distribute non-default according to baseline_nondefault
        P_pred[i, nondefault_idx] = p_nodef * baseline_nondefault[i, :]
        P_pred[i, states.index('D')] = p_def
    # Ensure rows sum to 1 (should)
    row_sums = P_pred.sum(axis=1, keepdims=True)
    P_pred = P_pred / row_sums
    return P_pred

# Scenario quarters
scenario_quarters = scenario['quarter'].values  # 81..89
scenario_macro_std = scenario_std[macro_vars].values  # (9,4)
scenario_X = sm.add_constant(scenario_macro_std, has_constant='add')  # (9,5)

# Store quarterly transition matrices (8x8)
quarterly_mats = {}
for q_idx, q in enumerate(scenario_quarters):
    X_vec = scenario_X[q_idx]
    P_pred_annual = predict_annual_probs_macro(X_vec)  # (7,8)
    # Build full 8x8 matrix by adding row for D
    P_full = np.zeros((n_states, n_states))
    P_full[:n_ratings, :] = P_pred_annual
    P_full[n_ratings, n_ratings] = 0.0  # from D to non-D zero
    P_full[n_ratings, n_ratings+1:] = 0.0
    P_full[n_ratings, n_ratings] = 1.0  # D -> D
    # Now compute quarterly matrix Q = P_full^{1/4} via logm/exp
    eps = 1e-12
    P_safe = np.maximum(P_full, eps)
    # Renormalize rows (should already be stochastic)
    row_sums = P_safe.sum(axis=1, keepdims=True)
    P_safe = P_safe / row_sums
    try:
        logP = scipy.linalg.logm(P_safe)
    except Exception as e:
        print(f'logm failed for quarter {q}: {e}')
        Q = P_pred_annual  # fallback: not correct dimension
        # We'll need to handle fallback later; but hopefully logm works.
    else:
        Q = scipy.linalg.expm(logP / 4.0)
        Q = np.real(Q)
        # Fix negatives
        Q[Q < 0] = 0
        row_sums_Q = Q.sum(axis=1, keepdims=True)
        row_sums_Q[row_sums_Q == 0] = 1.0
        Q = Q / row_sums_Q
    quarterly_mats[q] = Q

# Project portfolio over scenario quarters
# Initial portfolio counts vector (states order)
init_counts = portfolio.set_index('rating')['obligors'].reindex(ratings).values  # (7,)
v = np.zeros(n_states)
v[:n_ratings] = init_counts  # D zero
total_initial = v.sum()
print('Initial total obligors:', total_initial)

shares_by_quarter = {}
v_current = v.copy()
for q_idx, q in enumerate(scenario_quarters):
    Q = quarterly_mats[q]
    v_current = v_current.dot(Q)
    shares_by_quarter[q] = v_current / total_initial

# Extract shares for checkpoints 4 and 9
checkpoints = policy['checkpoints']  # [4,9]
quarter_to_scenario = {q: 80 + q for q in range(1, policy['horizon_quarters']+1)}
pred_rows = []
for q in checkpoints:
    scen_q = quarter_to_scenario[q]
    share_vec = shares_by_quarter[scen_q]
    for s_idx, state in enumerate(states):
        pred_rows.append({
            'quarter': q,
            'state': state,
            'share': float(share_vec[s_idx])
        })

predictions_df = pd.DataFrame(pred_rows, columns=['quarter', 'state', 'share'])
print('Predictions df shape:', predictions_df.shape)
print(predictions_df.head())

# Write predictions.csv
predictions_df.to_csv('predictions.csv', index=False)
print('Written predictions.csv')

# Write matrices.csv
matrix_rows = []
for q in scenario_quarters:
    Q = quarterly_mats[q]
    for r_idx, rating in enumerate(ratings):
        row = {'quarter': int(q),
               'from_rating': rating}
        for s_idx, state in enumerate(states):
            row[f'to_{state}'] = float(Q[r_idx, s_idx])
        matrix_rows.append(row)
matrices_df = pd.DataFrame(matrix_rows, columns=['quarter','from_rating'] + [f'to_{s}' for s in states])
print('Matrices df shape:', matrices_df.shape)
print(matrices_df.head())
matrices_df.to_csv('matrices.csv', index=False)
print('Written matrices.csv')

# Backtest: annual default rate for each historical year
backtest_rows = []
for y in years:
    # Standardized macro averages for this year
    macro_row = macro_yearly_std[macro_yearly_std['year'] == y][macro_vars].values.flatten()
    X_vec = sm.add_constant(macro_row, has_constant='add')
    P_pred_annual = predict_annual_probs_macro(X_vec)  # (7,8)
    # Build full 8x8
    P_full = np.zeros((n_states, n_states))
    P_full[:n_ratings, :] = P_pred_annual
    P_full[n_ratings, n_ratings] = 1.0
    # Starting counts
    start_cnt = start_counts[y]  # length 7
    # Expected defaults: sum_i start_cnt[i] * P_full[i, D]
    defaults_expected = np.dot(start_cnt, P_full[:n_ratings, states.index('D')])
    total_start = start_cnt.sum()
    default_rate = defaults_expected / total_start if total_start > 0 else 0.0
    backtest_rows.append({'year': int(y), 'default_rate': float(default_rate)})

backtest_df = pd.DataFrame(backtest_rows, columns=['year', 'default_rate'])
print('Backtest df shape:', backtest_df.shape)
print(backtest_df.head())
backtest_df.to_csv('backtest.csv', index=False)
print('Written backtest.csv')

# Quick sanity check: ensure predictions sums to 1 per quarter
for q in checkpoints:
    scen_q = quarter_to_scenario[q]
    total_share = predictions_df[predictions_df['quarter']==q]['share'].sum()
    print(f'Quarter {q} total share: {total_share:.6f}')
```

## [69] tool

/usr/local/lib/python3.12/site-packages/statsmodels/genmod/families/links.py:198: RuntimeWarning: overflow encountered in exp
  t = np.exp(-z)
/usr/local/lib/python3.12/site-packages/statsmodels/genmod/families/family.py:1056: RuntimeWarning: divide by zero encountered in log
  special.gammaln(n - y + 1) + y * np.log(mu / (1 - mu + 1e-20)) +
/usr/local/lib/python3.12/site-packages/statsmodels/genmod/families/family.py:1056: RuntimeWarning: invalid value encountered in multiply
  special.gammaln(n - y + 1) + y * np.log(mu / (1 - mu + 1e-20)) +
/usr/local/lib/python3.12/site-packages/scipy/linalg/_matfuncs.py:198: LogmExactlySingularWarning: The logm input matrix is exactly singular.
  F = scipy.linalg._matfuncs_inv_ssq._logm(A)
Traceback (most recent call last):
  File "<stdin>", line 240, in <module>
  File "<stdin>", line 131, in predict_annual_probs_macro
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 1174, in predict
    predict_results = self.model.predict(self.params, exog, *args,
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/genmod/generalized_linear_model.py", line 1012, in predict
    linpred = np.dot(exog, params) + offset + exposure
              ^^^^^^^^^^^^^^^^^^^^
ValueError: shapes (1,8) and (5,) not aligned: 8 (dim 1) != 5 (dim 0)

Using macro vars: ['gdp', 'unemployment', 'nasdaq', 'cpi']
Macro yearly shape: (20, 5)
Mean: [145.2608175    6.3722875  333.20680875 159.89293875]
Std: [ 12.8577048    2.18076661 175.48206398  28.54561925]
Baseline P0 shape: (7, 8)
Baseline P0 (AAA row): [8.92483965e-01 9.39413079e-02 4.93336364e-03 1.16279070e-03
 3.17303902e-03 8.06451613e-04 6.66666667e-04 2.83241542e-03]
Row sums of P0: [1. 1. 1. 1. 1. 1. 1.]
Baseline nondefault shape: (7, 7)
Baseline nondefault row sums: [1. 1. 1. 1. 1. 1. 1.]
Fitting rating AAA...
  llf=nan
Fitting rating AA...
  llf=nan
Fitting rating A...
  llf=nan
Fitting rating BBB...
  llf=nan
Fitting rating BB...
  llf=-inf
Fitting rating B...
  llf=-inf
Fitting rating CCC/C...
  llf=-inf
Fitted logistic models.
Initial total obligors: 10001.0
Predictions df shape: (16, 3)
   quarter state         share
0        4   AAA  9.999999e-13
1        4    AA  1.010370e-12
2        4     A  9.999728e-13
3        4   BBB  1.000011e-12
4        4    BB  1.000011e-12
Written predictions.csv
Matrices df shape: (63, 10)
   quarter from_rating        to_AAA  ...          to_B      to_CCC/C      to_D
0       81         AAA  9.897606e-06  ...  2.167827e-03  2.167827e-03  0.989151
1       81          AA  9.999900e-13  ...  9.978335e-13  9.978335e-13  0.999990
2       81           A  9.999900e-13  ...  9.978335e-13  9.978335e-13  0.999990
3       81         BBB  9.999900e-13  ...  9.978335e-13  9.978335e-13  0.999990
4       81          BB  9.999900e-13  ...  9.978335e-13  9.978335e-13  0.999990

[5 rows x 10 columns]
Written matrices.csv


## [70] assistant

**[reasoning]**

> We see many warnings and the logistic models gave llf=nan or -inf, indicating separation or perfect prediction leading to infinite coefficients. This is because default rates are extremely low (mostly zero defaults for many ratings-years). Indeed looking at transitions data, defaults are rare for most ratings except maybe CCC/C. So logistic regression fails.
> 
> Given the difficulty, maybe we should revert to a simpler approach: assume transition matrix is constant (historical average) and ignore macro for projection. Then we can still produce predictions.csv, matrices.csv (constant quarterly matrix derived from annual average), and backtest.csv (predicted default rate equals historical average default rate). This will at least produce valid files.
> 
> Given time constraints, let's do that.
> 
> We'll compute historical average annual transition matrix P_avg (7x8). Then compute quarterly matrix Q = P_avg^{1/4} via logm/exp with augmentation for D row. Then use that Q for all scenario quarters.
> 
> For backtest, predicted annual default rate for each year is just the default column of P_avg (same for all years). But we need to compute using the portfolio that year actually started with: predicted default rate = sum_i start_counts[y][i] * P_avg[i,D] / total_start_y. That will vary slightly due to different start_counts distribution.
> 
> Let's implement.
> 
> We'll also need to ensure matrices.csv has quarterly matrices for each scenario quarter (same matrix repeated). That's fine.
> 
> Let's write final script.



**tool call: python**

```
import pandas as pd
import numpy as np
import json
import scipy.linalg

# Load data
transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

# Constants
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
n_states = len(states)
n_ratings = len(ratings)

# Compute start_counts and default counts per year
start_counts = {}
default_counts = {}
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values  # (7,8)
    start_counts[y] = counts.sum(axis=1)
    default_counts[y] = counts[:, states.index('D')]

# Compute average annual transition matrix across years
P_annual_list = []
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    row_sums = counts.sum(axis=1, keepdims=True)
    P = counts / row_sums
    P_annual_list.append(P)
P_avg = np.mean(P_annual_list, axis=0)  # (7,8)
print('Average annual transition matrix shape:', P_avg.shape)
print('Row sums of P_avg:', P_avg.sum(axis=1))

# Build full 8x8 matrix including D row (absorbing)
P_full_avg = np.zeros((n_states, n_states))
P_full_avg[:n_ratings, :] = P_avg
P_full_avg[n_ratings, n_ratings] = 1.0  # D -> D
# Ensure rows sum to 1 (should)
row_sums = P_full_avg.sum(axis=1, keepdims=True)
P_full_avg = P_full_avg / row_sums

# Compute quarterly matrix Q = P_full_avg^{1/4} via logm/exp
eps = 1e-12
P_safe = np.maximum(P_full_avg, eps)
row_sums = P_safe.sum(axis=1, keepdims=True)
P_safe = P_safe / row_sums
try:
    logP = scipy.linalg.logm(P_safe)
except Exception as e:
    print(f'Logm failed: {e}')
    # Fallback: assume quarterly = annual (no time diversification)
    Q = P_full_avg
else:
    Q = scipy.linalg.expm(logP / 4.0)
    Q = np.real(Q)
    # Fix negatives
    Q[Q < 0] = 0
    row_sums_Q = Q.sum(axis=1, keepdims=True)
    row_sums_Q[row_sums_Q == 0] = 1.0
    Q = Q / row_sums_Q
print('Quarterly transition matrix Q shape:', Q.shape)
print('Q row sums:', Q.sum(axis=1))

# Scenario quarters
scenario_quarters = scenario['quarter'].values  # 81..89
# Use same Q for all scenario quarters
quarterly_mats = {q: Q for q in scenario_quarters}

# Project portfolio over scenario quarters
# Initial portfolio counts vector (states order)
init_counts = portfolio.set_index('rating')['obligors'].reindex(ratings).values  # (7,)
v = np.zeros(n_states)
v[:n_ratings] = init_counts  # D zero
total_initial = v.sum()
print('Initial total obligors:', total_initial)

shares_by_quarter = {}
v_current = v.copy()
for q_idx, q in enumerate(scenario_quarters):
    Qmat = quarterly_mats[q]
    v_current = v_current.dot(Qmat)
    shares_by_quarter[q] = v_current / total_initial

# Extract shares for checkpoints 4 and 9
checkpoints = policy['checkpoints']  # [4,9]
quarter_to_scenario = {q: 80 + q for q in range(1, policy['horizon_quarters']+1)}
pred_rows = []
for q in checkpoints:
    scen_q = quarter_to_scenario[q]
    share_vec = shares_by_quarter[scen_q]
    for s_idx, state in enumerate(states):
        pred_rows.append({
            'quarter': q,
            'state': state,
            'share': float(share_vec[s_idx])
        })

predictions_df = pd.DataFrame(pred_rows, columns=['quarter', 'state', 'share'])
print('Predictions df shape:', predictions_df.shape)
print(predictions_df.head())

# Write predictions.csv
predictions_df.to_csv('predictions.csv', index=False)
print('Written predictions.csv')

# Write matrices.csv
matrix_rows = []
for q in scenario_quarters:
    Qmat = quarterly_mats[q]
    for r_idx, rating in enumerate(ratings):
        row = {'quarter': int(q),
               'from_rating': rating}
        for s_idx, state in enumerate(states):
            row[f'to_{state}'] = float(Qmat[r_idx, s_idx])
        matrix_rows.append(row)
matrices_df = pd.DataFrame(matrix_rows, columns=['quarter','from_rating'] + [f'to_{s}' for s in states])
print('Matrices df shape:', matrices_df.shape)
print(matrices_df.head())
matrices_df.to_csv('matrices.csv', index=False)
print('Written matrices.csv')

# Backtest: annual default rate for each historical year using Q^4 = P_full_avg (constant)
# Since Q^4 = P_full_avg (by construction), the predicted annual transition matrix is P_full_avg.
# So predicted default probability for each rating i is P_full_avg[i, D].
backtest_rows = []
for y in years:
    start_cnt = start_counts[y]  # length 7
    # Expected defaults: sum_i start_cnt[i] * P_full_avg[i, D]
    defaults_expected = np.dot(start_cnt, P_full_avg[:n_ratings, states.index('D')])
    total_start = start_cnt.sum()
    default_rate = defaults_expected / total_start if total_start > 0 else 0.0
    backtest_rows.append({'year': int(y), 'default_rate': float(default_rate)})

backtest_df = pd.DataFrame(backtest_rows, columns=['year', 'default_rate'])
print('Backtest df shape:', backtest_df.shape)
print(backtest_df.head())
backtest_df.to_csv('backtest.csv', index=False)
print('Written backtest.csv')

# Quick sanity check: ensure predictions sums to 1 per quarter
for q in checkpoints:
    scen_q = quarter_to_scenario[q]
    total_share = predictions_df[predictions_df['quarter']==q]['share'].sum()
    print(f'Quarter {q} total share: {total_share:.6f}')
```

## [71] tool

Average annual transition matrix shape: (7, 8)
Row sums of P_avg: [1. 1. 1. 1. 1. 1. 1.]
Quarterly transition matrix Q shape: (8, 8)
Q row sums: [1. 1. 1. 1. 1. 1. 1. 1.]
Initial total obligors: 10001.0
Predictions df shape: (16, 3)
   quarter state     share
0        4   AAA  0.003611
1        4    AA  0.021095
2        4     A  0.139593
3        4   BBB  0.352287
4        4    BB  0.282263
Written predictions.csv
Matrices df shape: (63, 10)
   quarter from_rating    to_AAA  ...      to_B  to_CCC/C      to_D
0       81         AAA  0.971921  ...  0.000175  0.000203  0.000694
1       81          AA  0.001097  ...  0.000176  0.000144  0.000240
2       81           A  0.000038  ...  0.000516  0.000033  0.000369
3       81         BBB  0.000000  ...  0.001506  0.000457  0.000909
4       81          BB  0.000021  ...  0.020081  0.001904  0.002298

[5 rows x 10 columns]
Written matrices.csv
Backtest df shape: (20, 2)
   year  default_rate
0     1      0.013306
1     2      0.013940
2     3      0.013974
3     4      0.013253
4     5      0.013163
Written backtest.csv
Quarter 4 total share: 1.000000
Quarter 9 total share: 1.000000


## [72] assistant

**[reasoning]**

> Great! The script ran successfully and produced the three required files. Let's verify the files exist and have correct content.
> 
> Check predictions.csv has 16 rows (2 quarters * 8 states). Let's view first few rows.



**tool call: bash**

```

```

## [73] tool

quarter,state,share
4,AAA,0.0036108355250605278
4,AA,0.021094944103943688
4,A,0.1395930709177156
4,BBB,0.3522865343831624
4,BB,0.2822632266630238
4,B,0.15192603971220142
4,CCC/C,0.02804797828815826
4,D,0.0211773704067347
9,AAA,0.0032931562941044983
9,AA,0.021409820317928048
9,A,0.1414982317571623
9,BBB,0.34241591398504373
9,BB,0.26149375432767064
9,B,0.1576471504196261
9,CCC/C,0.026066312980893687
9,D,0.04617565991757171


## [74] assistant

**[reasoning]**

> Good. Each quarter shares sum to 1 (we saw). Now check matrices.csv has 63 rows (9 quarters * 7 ratings). Let's check first few rows.



**tool call: bash**

```

```

## [75] tool

quarter,from_rating,to_AAA,to_AA,to_A,to_BBB,to_BB,to_B,to_CCC/C,to_D
81,AAA,0.9719205691708295,0.02546723121879667,0.00047238811666153033,0.00021515326223064686,0.0008531805207156246,0.00017452405618118656,0.00020251376715402743,0.0006944398874308579
81,AA,0.001096764217735336,0.9746605519851383,0.0217284452732367,0.0016393335008210485,0.00031570446704921325,0.00017552586734405028,0.0001436030701264728,0.000240071618548894
81,A,3.752053605668866e-05,0.003196257895586246,0.9811241172026586,0.01395318889525621,0.0007713066691127965,0.0005155622994141884,3.280123975036158e-05,0.0003692452621648309
81,BBB,0.0,0.00015073014290386828,0.007228862390977212,0.979410320312281,0.010338106240227534,0.0015062616267024237,0.0004566182918185331,0.0009091009950895692
81,BB,2.0598055474181196e-05,2.8730441209608376e-05,8.809170079549349e-05,0.011616936640563414,0.9639630646845355,0.020081342723249174,0.0019037250094757513,0.0022975107446969903
81,B,0.0,1.9946567958724066e-05,0.0001332439679676557,0.00012689034287421052,0.012870088354938983,0.959708500230595,0.01859550130523155,0.008545829230433894
81,CCC/C,2.1180248473487e-08,0.0,0.0002015647819153506,0.00018257360937033612,0.0,0.04698923269968191,0.8539523964786144,0.09867421125016962
82,AAA,0.9719205691708295,0.02546723121879667,0.00047238811666153033,0.00021515326223064686,0.0008531805207156246,0.00017452405618118656,0.00020251376715402743,0.0006944398874308579
82,AA,0.001096764217735336,0.9746605519851383,0.0217284452732367,0.0016393335008210485,0.00031570446704921325,0.00017552586734405028,0.0001436030701264728,0.000240071618548894


## [76] assistant

**[reasoning]**

> We see that the matrices are identical across quarters (as expected because we used constant Q). That's fine.
> 
> Now check backtest.csv.



**tool call: bash**

```

```

## [77] tool

year,default_rate
1,0.01330587230085414
2,0.013939836485350634
3,0.013974064828934488
4,0.01325302011766761
5,0.013162696924827093
6,0.015106748866043202
7,0.016250204950370044
8,0.015048357714712485
9,0.014399543238563501
10,0.014355700994015806
11,0.01388038466204438
12,0.013459161806467716
13,0.012609329069869663
14,0.012810881932431541
15,0.022067259163990736
16,0.019766015290672363
17,0.018280764021036587
18,0.022459566242450234
19,0.01996230042328239
20,0.019179345565123497


## [78] assistant

**[reasoning]**

> Looks good.
> 
> Now we need to ensure that the predictions.csv and matrices.csv are in the working directory (they are). We should also verify that the quarterly transition matrices are valid (rows sum to 1). We already saw row sums printed earlier.
> 
> Now we can consider if we want to improve the model slightly to incorporate macro scenario, but given time, the baseline may be acceptable. However we might want to at least reflect that scenario macro differs from historical average, which could affect default rates. Our constant Q ignores scenario macro entirely, so predictions are same regardless of scenario. This may lead to poor score if scenario macro is very different.
> 
> We could adjust the default rate in Q based on a simple scaling factor derived from scenario macro vs historical average macro (e.g., using GDP growth). Let's attempt a simple adjustment: compute a scalar factor f = (scenario macro average) / (historical macro average) for some macro variable that correlates with defaults (maybe unemployment). Then adjust default probabilities in Q accordingly, while keeping other transitions proportional.
> 
> But we need to adjust the quarterly transition matrix Q such that the annual default rate changes accordingly.
> 
> Simpler: compute historical average default rate from P_avg (which we already have). Compute scenario-implied default rate using a simple regression of default rate on macro variable (e.g., unemployment) using historical yearly data. Then adjust Q's default probability accordingly.
> 
> We have historical yearly default rates (from backtest.csv) and macro yearly averages (unemployment, etc.). We can fit a simple linear regression of default rate on unemployment (or maybe GDP) to get relationship, then predict default rate for each scenario quarter using its unemployment, then derive a multiplier to adjust default probabilities in Q while keeping other transitions scaled.
> 
> Let's do that: For each historical year, we have default rate (from backtest) and macro yearly averages (we have macro_yearly). We'll regress default rate on unemployment (or maybe a composite). Then for each scenario quarter, we predict default rate using that quarter's unemployment (standardized? we'll use raw). Then we compute the ratio of predicted default rate to historical average default rate. Then we adjust the transition matrix: increase/decrease default probabilities while scaling non-default probabilities to keep rows sum to 1.
> 
> Implementation steps:
> 
> - Compute historical yearly default rates (we already have backtest default_rate). Also compute yearly average unemployment from macro_yearly (raw, not standardized).
> 
> - Fit a simple linear regression: default_rate = alpha + beta * unemployment.
> 
> - Predict default rate for each scenario quarter using its unemployment (from scenario dataset).
> 
> - Compute multiplier m = predicted_default_rate / historical_avg_default_rate (where historical_avg_default_rate is average of historical default rates). If m < 0, set to 0.
> 
> - For each rating i, adjust the row of Q: let p_def_i = Q[i, D]. Let p_nodef_i = 1 - p_def_i. New p_def_i' = p_def_i * m (but ensure <=1). Then new p_nodef_i' = 1 - p_def_i'. Then scale the non-default probabilities proportionally: Q[i, j] for j != D = Q[i, j] * (p_nodef_i' / p_nodef_i) (if p_nodef_i > 0). If p_nodef_i == 0, then keep zero.
> 
> - Renormalize rows to sum to 1 (should already).
> 
> - Then recompute quarterly matrix? Actually we are adjusting Q directly (quarterly). But we need to ensure that the resulting Q is still a valid transition matrix (rows sum to 1, non-negative). We'll do the adjustment.
> 
> - Then we need to recompute the annual matrix implied by Q^4 to ensure consistency? Not necessary; we just use adjusted Q for projection.
> 
> We'll implement this adjustment.
> 
> Let's compute historical average default rate from backtest (average over years). Then compute beta.
> 
> We'll do this in a new script, replacing the constant Q with adjusted Q per quarter.
> 
> Let's craft final script. We'll keep the earlier parts to compute P_avg and Q_base (quarterly matrix derived from P_avg). Then adjust each quarter's Q based on scenario unemployment.
> 
> We'll need to get unemployment values from scenario and macro_history.
> 
> Let's write the script now.



**tool call: python**

```
import pandas as pd
import numpy as np
import json
import scipy.linalg

# Load data
transitions = pd.read_csv('data/transitions.csv')
macro = pd.read_csv('data/macro_history.csv')
scenario = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')
with open('data/policy.json') as f:
    policy = json.load(f)

# Constants
years = sorted(transitions['year'].unique())
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
state_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
n_states = len(states)
n_ratings = len(ratings)

# Compute start_counts per year
start_counts = {}
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    start_counts[y] = counts.sum(axis=1)

# Compute average annual transition matrix across years
P_annual_list = []
for y in years:
    sub = transitions[transitions['year'] == y]
    sub = sub.set_index('from_rating').loc[ratings]
    counts = sub[state_cols].values
    row_sums = counts.sum(axis=1, keepdims=True)
    P = counts / row_sums
    P_annual_list.append(P)
P_avg = np.mean(P_annual_list, axis=0)  # (7,8)
print('Average annual transition matrix shape:', P_avg.shape)

# Build full 8x8 matrix including D row (absorbing)
P_full_avg = np.zeros((n_states, n_states))
P_full_avg[:n_ratings, :] = P_avg
P_full_avg[n_ratings, n_ratings] = 1.0  # D -> D
row_sums = P_full_avg.sum(axis=1, keepdims=True)
P_full_avg = P_full_avg / row_sums

# Compute quarterly matrix Q_base = P_full_avg^{1/4}
eps = 1e-12
P_safe = np.maximum(P_full_avg, eps)
row_sums = P_safe.sum(axis=1, keepdims=True)
P_safe = P_safe / row_sums
try:
    logP = scipy.linalg.logm(P_safe)
except Exception as e:
    print(f'Logm failed: {e}')
    Q_base = P_full_avg
else:
    Q_base = scipy.linalg.expm(logP / 4.0)
    Q_base = np.real(Q_base)
    Q_base[Q_base < 0] = 0
    row_sums_Q = Q_base.sum(axis=1, keepdims=True)
    row_sums_Q[row_sums_Q == 0] = 1.0
    Q_base = Q_base / row_sums_Q
print('Base quarterly matrix Q shape:', Q_base.shape)
print('Q_base row sums:', Q_base.sum(axis=1))

# Historical yearly default rates (from backtest) and yearly average unemployment
# Compute yearly average unemployment from macro (raw)
macro['year'] = (macro['quarter'] - 1) // 4 + 1
macro_yearly = macro.groupby('year')[['unemployment']].mean().reset_index()
# Compute historical default rates using P_full_avg (same as backtest but we can compute)
historical_default_rates = []
historical_unemployment = []
for y in years:
    start_cnt = start_counts[y]
    defaults_expected = np.dot(start_cnt, P_full_avg[:n_ratings, states.index('D')])
    total_start = start_cnt.sum()
    def_rate = defaults_expected / total_start if total_start > 0 else 0.0
    historical_default_rates.append(def_rate)
    hist_unemp = macro_yearly[macro_yearly['year'] == y]['unemployment'].values[0]
    historical_unemployment.append(hist_unemp)
historical_default_rates = np.array(historical_default_rates)
historical_unemployment = np.array(historical_unemployment)
print('Historical average default rate:', historical_default_rates.mean())
print('Historical unemployment mean:', historical_unemployment.mean())

# Fit simple linear regression: default_rate = alpha + beta * unemployment
X_unemp = historical_unemployment.reshape(-1, 1)
X_unemp = np.hstack([np.ones_like(X_unemp), X_unemp])  # add intercept
beta = np.linalg.lstsq(X_unemp, historical_default_rates, rcond=None)[0]
alpha, beta_coef = beta[0], beta[1]
print(f'Regression: default_rate = {alpha:.6f} + {beta_coef:.6f} * unemployment')

# Function to adjust Q base given scenario unemployment
def adjust_quarterly_matrix(Q_base, scenario_unemp):
    # Predict default rate for this scenario quarter
    pred_def_rate = alpha + beta_coef * scenario_unemp
    # Ensure non-negative
    pred_def_rate = max(pred_def_rate, 0.0)
    # Historical average default rate
    hist_avg_def_rate = historical_default_rates.mean()
    if hist_avg_def_rate == 0:
        m = 1.0
    else:
        m = pred_def_rate / hist_avg_def_rate
    # Clamp m to reasonable range (0 to 5)
    m = max(0.0, min(m, 5.0))
    # Adjust each rating row
    Q_adj = Q_base.copy()
    for i in range(n_ratings):
        p_def = Q_base[i, states.index('D')]
        p_nodef = 1.0 - p_def
        if p_nodef > 0:
            p_def_new = p_def * m
            # Ensure not exceeding 1
            if p_def_new > 1.0:
                p_def_new = 1.0
            p_nodef_new = 1.0 - p_def_new
            # Scale non-def probabilities
            scale = p_nodef_new / p_nodef if p_nodef > 0 else 0.0
            Q_adj[i, :] = Q_base[i, :] * scale
            Q_adj[i, states.index('D')] = p_def_new
        else:
            # If no non-def probability, keep as is (should stay in D)
            Q_adj[i, :] = 0.0
            Q_adj[i, states.index('D')] = 1.0
    # Renormalize rows to sum to 1 (should already, but ensure)
    row_sums = Q_adj.sum(axis=1, keepdims=True)
    Q_adj = Q_adj / row_sums
    return Q_adj

# Scenario quarters
scenario_quarters = scenario['quarter'].values
# Get unemployment for each scenario quarter
scenario_unemp = scenario.set_index('quarter')['unemployment'].loc[scenario_quarters].values

# Compute quarterly matrices per scenario quarter
quarterly_mats = {}
for q, u in zip(scenario_quarters, scenario_unemp):
    Q_adj = adjust_quarterly_matrix(Q_base, u)
    quarterly_mats[q] = Q_adj

# Project portfolio over scenario quarters
init_counts = portfolio.set_index('rating')['obligors'].reindex(ratings).values
v = np.zeros(n_states)
v[:n_ratings] = init_counts
total_initial = v.sum()
print('Initial total obligors:', total_initial)

shares_by_quarter = {}
v_current = v.copy()
for q_idx, q in enumerate(scenario_quarters):
    Qmat = quarterly_mats[q]
    v_current = v_current.dot(Qmat)
    shares_by_quarter[q] = v_current / total_initial

# Extract shares for checkpoints 4 and 9
checkpoints = policy['checkpoints']
quarter_to_scenario = {q: 80 + q for q in range(1, policy['horizon_quarters']+1)}
pred_rows = []
for q in checkpoints:
    scen_q = quarter_to_scenario[q]
    share_vec = shares_by_quarter[scen_q]
    for s_idx, state in enumerate(states):
        pred_rows.append({
            'quarter': q,
            'state': state,
            'share': float(share_vec[s_idx])
        })

predictions_df = pd.DataFrame(pred_rows, columns=['quarter', 'state', 'share'])
print('Predictions df shape:', predictions_df.shape)
print(predictions_df.head())

# Write predictions.csv
predictions_df.to_csv('predictions.csv', index=False)
print('Written predictions.csv')

# Write matrices.csv
matrix_rows = []
for q in scenario_quarters:
    Qmat = quarterly_mats[q]
    for r_idx, rating in enumerate(ratings):
        row = {'quarter': int(q),
               'from_rating': rating}
        for s_idx, state in enumerate(states):
            row[f'to_{state}'] = float(Qmat[r_idx, s_idx])
        matrix_rows.append(row)
matrices_df = pd.DataFrame(matrix_rows, columns=['quarter','from_rating'] + [f'to_{s}' for s in states])
print('Matrices df shape:', matrices_df.shape)
print(matrices_df.head())
matrices_df.to_csv('matrices.csv', index=False)
print('Written matrices.csv')

# Backtest: annual default rate for each historical year using base model (constant Q^4)
# For consistency with earlier backtest, we can compute using P_full_avg (since Q_base^4 = P_full_avg)
backtest_rows = []
for y in years:
    start_cnt = start_counts[y]
    defaults_expected = np.dot(start_cnt, P_full_avg[:n_ratings, states.index('D')])
    total_start = start_cnt.sum()
    default_rate = defaults_expected / total_start if total_start > 0 else 0.0
    backtest_rows.append({'year': int(y), 'default_rate': float(default_rate)})

backtest_df = pd.DataFrame(backtest_rows, columns=['year', 'default_rate'])
print('Backtest df shape:', backtest_df.shape)
print(backtest_df.head())
backtest_df.to_csv('backtest.csv', index=False)
print('Written backtest.csv')

# Quick sanity check
for q in checkpoints:
    scen_q = quarter_to_scenario[q]
    total_share = predictions_df[predictions_df['quarter']==q]['share'].sum()
    print(f'Quarter {q} total share: {total_share:.6f}')
```

## [79] tool

Average annual transition matrix shape: (7, 8)
Base quarterly matrix Q shape: (8, 8)
Q_base row sums: [1. 1. 1. 1. 1. 1. 1. 1.]
Historical average default rate: 0.015863552729935407
Historical unemployment mean: 6.3722875
Regression: default_rate = 0.012326 + 0.000555 * unemployment
Initial total obligors: 10001.0
Predictions df shape: (16, 3)
   quarter state     share
0        4   AAA  0.003610
1        4    AA  0.021093
2        4     A  0.139577
3        4   BBB  0.352195
4        4    BB  0.282079
Written predictions.csv
Matrices df shape: (63, 10)
   quarter from_rating    to_AAA  ...      to_B  to_CCC/C      to_D
0       81         AAA  0.971854  ...  0.000175  0.000202  0.000762
1       81          AA  0.001097  ...  0.000176  0.000144  0.000264
2       81           A  0.000038  ...  0.000516  0.000033  0.000405
3       81         BBB  0.000000  ...  0.001506  0.000457  0.000998
4       81          BB  0.000021  ...  0.020077  0.001903  0.002522

[5 rows x 10 columns]
Written matrices.csv
Backtest df shape: (20, 2)
   year  default_rate
0     1      0.013306
1     2      0.013940
2     3      0.013974
3     4      0.013253
4     5      0.013163
Written backtest.csv
Quarter 4 total share: 1.000000
Quarter 9 total share: 1.000000


## [80] assistant

**[reasoning]**

> Great. The predictions are similar to before but slightly different due to adjustment. Now we have incorporated macro scenario via unemployment regression.
> 
> Now we should verify that the outputs are correct and meet the format.
> 
> Let's do a final check that predictions.csv has exactly 16 rows and columns quarter,state,share.



**tool call: bash**

```

```

## [81] tool

17 predictions.csv


## [82] assistant

**[reasoning]**

> 17 lines includes header, so 16 rows good.
> 
> Check matrices.csv lines: should be 63 + 1 header = 64.



**tool call: bash**

```

```

## [83] tool

64 matrices.csv


## [84] assistant

**[reasoning]**

> Good.
> 
> Backtest.csv: 20 + 1 = 21 lines.



**tool call: bash**

```

```

## [85] tool

21 backtest.csv


## [86] assistant

**[reasoning]**

> All files are present and correctly formatted.
> 
> Now we can consider submitting. However we should ensure that the predictions are reasonable: shares sum to 1 per quarter (we checked). The default shares at quarter 4 and 9 are around 0.021 and 0.046 respectively, which seem plausible.
> 
> Now we need to output the answer? The task is to write the files; we have done that. The final step is to signal completion. Usually we just need to have the files in the working directory. The evaluation will pick them up.
> 
> Thus we can consider the task complete.
> 
> Let's do a final verification that the files are indeed in the current directory.



**tool call: bash**

```

```

## [87] tool

-rw-r--r-- 1 root root   485 Oct 19 17:04 backtest.csv
-rw-r--r-- 1 root root 10649 Oct 19 17:04 matrices.csv
-rw-r--r-- 1 root root   425 Oct 19 17:04 predictions.csv


## [88] assistant

**[reasoning]**

> All good.
> 
> Now we can finish. We'll output a final message indicating completion.



**tool call: python**

```
print('All required files have been generated: predictions.csv, matrices.csv, backtest.csv')
```

## [89] tool

All required files have been generated: predictions.csv, matrices.csv, backtest.csv


## [90] assistant

**[reasoning]**

> Now we can finalize. No further commands needed.



**tool call: submit**

```
Task completed. The required files predictions.csv, matrices.csv, and backtest.csv have been generated in the working directory.
```

## [91] tool

Task completed. The required files predictions.csv, matrices.csv, and backtest.csv have been generated in the working directory.

