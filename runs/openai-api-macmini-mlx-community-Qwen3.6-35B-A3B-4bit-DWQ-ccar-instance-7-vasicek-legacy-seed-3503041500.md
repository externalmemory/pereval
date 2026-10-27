# openai-api/macmini/mlx-community/Qwen3.6-35B-A3B-4bit-DWQ — ccar (id=instance-7-vasicek-legacy-seed-3503041500)

- 9/9 points predicted; Winkler regret 0.181 (agent 0.266 vs oracle 0.085, degenerate 0.762); MAE 0.018; coverage 0.649; mean width 0.047.
- messages 64 | limit None | seed None

---

## [0] system

You are building a stress loss model. In the `data/` directory:

- `data/train.csv`: a quarterly history with columns `quarter`, nine macroeconomic
  series (gdp, unemployment, hpi, bbb_spread, sp500, djia, nasdaq, vix, cpi), and
  `default_rate` (the portfolio's quarterly annualized default rate, a fraction).
  Some macro series are blank for early quarters (they began later); handle the
  missing values as you see fit.
- `data/scenario.csv`: the same nine macro series for nine future quarters under a
  forward stress scenario. It has no default_rate; that is what you predict.

Build a model of the default rate from the macro history, then apply it to the
scenario. For every row in `data/scenario.csv`, produce a point estimate of the
default rate and a 95% prediction interval [lower, upper] for that quarter. The
scenario pushes the drivers beyond the range seen in training, so a model that
only fits in-sample may extrapolate poorly. Not all nine series necessarily
matter, and the ones that do may enter through a transformation rather than as a
raw level. The interval should reflect genuine forecast uncertainty.

Write your predictions to `predictions.csv` in the working directory with columns
exactly:

    quarter,y_pred,y_lower,y_upper

one row per scenario quarter, with quarter copied from data/scenario.csv, and the
default-rate columns as fractions.

You have Python with numpy, pandas, scikit-learn, statsmodels, and scipy. You do
not have internet access. Each code execution runs in a FRESH interpreter, so
write a single self-contained script (save it to a file and run it) rather than
relying on state carrying over between executions. Produce a complete
predictions.csv early, even from a rough model, and keep a valid one on disk;
refine it after. Verify it has one row per scenario quarter before submitting.


## [1] user

Project the default rate with a 95% interval for every quarter in data/scenario.csv and write predictions.csv, as specified in the system instructions.

## [2] assistant

**[reasoning]**

> Let me start by examining the data to understand the structure and then build a model to predict default rates.
> 
> First, I'll look at the training data and scenario data to understand what we're working with.
> 





**tool call: bash**

```
ls data/
```

## [3] tool

scenario.csv
train.csv


## [4] assistant

**tool call: bash**

```
head -20 data/train.csv
```

## [5] tool

quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi,default_rate
1,106.7792,6.5587,,,,,216.04,,114.8357,0.014464
2,107.3173,6.211,,,,,232.2141,,114.1514,0.023817
3,107.2908,6.5566,,,,,244.3976,,113.4655,0.035626
4,107.9102,5.7155,,,,,254.654,,112.3306,0.034708
5,108.8015,5.4866,,,,,228.0949,,111.0805,0.025799
6,112.4629,4.1431,,,,,237.5686,,111.3932,0.026587
7,112.7942,4.3695,,,,,252.8706,,111.8978,0.03563
8,113.5143,4.5434,,,,,251.8586,,112.7259,0.038652
9,116.1373,4.7767,,,,,255.9874,,116.0849,0.020768
10,116.5498,5.8003,,,,,241.1175,,119.2593,0.018346
11,119.6975,4.2726,190.6755,,,,246.4009,15.0916,123.9355,0.022356
12,120.524,4.0918,196.1593,,,,255.8827,15.0915,126.1279,0.024936
13,123.3443,3.3843,201.1923,,,,240.3577,12.4405,129.171,0.016281
14,124.2311,4.3787,205.4341,1.4837,,,248.5812,12.5775,131.5464,0.015649
15,126.5799,3.3761,207.1471,1.5201,,,256.4671,10.7253,133.1051,0.027385
16,127.5252,3.1887,206.5315,2.1435,,,236.6533,16.1514,131.8445,0.029105
17,130.7242,3.0721,208.2695,1.9055,,,286.4874,12.8162,133.019,0.023324
18,130.0696,3.9279,210.7141,2.0401,,,315.3445,13.7046,135.2357,0.023393
19,128.9369,4.8628,212.3144,2.0732,,,321.1473,14.7021,135.3913,0.027004


## [6] assistant

**[reasoning]**

> <think>
> 
> 





**tool call: bash**

```
wc -l data/train.csv data/scenario.csv
```

## [7] tool

  81 data/train.csv
  10 data/scenario.csv
  91 total


## [8] assistant

**[reasoning]**

> Let me look at the full data to understand the structure better.
> 





**tool call: bash**

```
cat data/train.csv
```

## [9] tool

quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi,default_rate
1,106.7792,6.5587,,,,,216.04,,114.8357,0.014464
2,107.3173,6.211,,,,,232.2141,,114.1514,0.023817
3,107.2908,6.5566,,,,,244.3976,,113.4655,0.035626
4,107.9102,5.7155,,,,,254.654,,112.3306,0.034708
5,108.8015,5.4866,,,,,228.0949,,111.0805,0.025799
6,112.4629,4.1431,,,,,237.5686,,111.3932,0.026587
7,112.7942,4.3695,,,,,252.8706,,111.8978,0.03563
8,113.5143,4.5434,,,,,251.8586,,112.7259,0.038652
9,116.1373,4.7767,,,,,255.9874,,116.0849,0.020768
10,116.5498,5.8003,,,,,241.1175,,119.2593,0.018346
11,119.6975,4.2726,190.6755,,,,246.4009,15.0916,123.9355,0.022356
12,120.524,4.0918,196.1593,,,,255.8827,15.0915,126.1279,0.024936
13,123.3443,3.3843,201.1923,,,,240.3577,12.4405,129.171,0.016281
14,124.2311,4.3787,205.4341,1.4837,,,248.5812,12.5775,131.5464,0.015649
15,126.5799,3.3761,207.1471,1.5201,,,256.4671,10.7253,133.1051,0.027385
16,127.5252,3.1887,206.5315,2.1435,,,236.6533,16.1514,131.8445,0.029105
17,130.7242,3.0721,208.2695,1.9055,,,286.4874,12.8162,133.019,0.023324
18,130.0696,3.9279,210.7141,2.0401,,,315.3445,13.7046,135.2357,0.023393
19,128.9369,4.8628,212.3144,2.0732,,,321.1473,14.7021,135.3913,0.027004
20,132.2058,3.7845,214.907,1.8811,,,354.4852,14.2471,134.6312,0.034035
21,132.8657,4.015,219.4262,1.9861,,,383.3521,16.4304,135.6712,0.030886
22,133.6942,4.7301,220.4751,2.1256,,,444.0092,11.0718,135.7488,0.030442
23,133.6142,4.9959,221.2851,1.9355,,,507.9225,12.7084,135.7449,0.036021
24,137.2047,4.4765,225.0412,1.8266,,,540.6817,14.1439,137.8942,0.019758
25,137.7362,5.1695,224.8968,1.7421,,,531.1975,13.0079,139.1022,0.048528
26,141.7477,4.77,222.6638,1.4848,,,628.5672,10.5946,143.7763,0.021485
27,139.7397,5.5581,223.1406,2.7465,,,467.6736,20.2383,145.3663,0.040471
28,141.8332,5.6519,224.0967,2.5791,,,451.8053,19.5562,146.1233,0.025568
29,140.556,6.0016,226.5984,2.6025,,,444.7448,16.6099,147.1496,0.028208
30,137.9541,7.7376,226.6321,3.1667,,,420.9829,19.9069,147.8794,0.071345
31,137.6954,7.6841,221.8316,3.0956,,,437.2535,18.275,148.7163,0.067755
32,140.4208,7.5298,220.3625,2.3225,699.1576,379.2005,497.9559,14.2705,150.1311,0.038397
33,141.7968,6.8179,219.7204,2.4746,722.6926,386.5604,536.6448,14.8595,152.4452,0.093801
34,143.1425,6.9084,219.0684,2.6476,727.9204,384.4,545.3977,12.0751,154.8498,0.039183
35,145.2794,6.2292,219.5922,2.4148,748.6508,420.0449,566.2626,15.1074,158.5532,0.020585
36,145.9589,6.797,212.4368,2.5162,834.5796,438.8524,647.3695,13.003,158.5667,0.039314
37,146.0182,6.6692,208.3547,2.8061,900.9862,469.5279,727.2808,15.9416,157.6373,0.029808
38,147.5495,6.5571,210.558,2.692,960.3086,479.309,760.1684,16.7738,157.816,0.028506
39,148.2031,6.5519,211.8134,2.4934,925.5479,481.9437,713.2095,19.7568,160.0053,0.034197
40,148.788,6.6703,217.7854,2.9393,887.9841,465.7122,635.5718,23.7567,160.9077,0.055747
41,151.0289,6.3628,222.2572,3.1166,930.1941,483.2429,666.7207,25.737,161.0139,0.027688
42,153.2037,5.0657,228.9983,2.9171,928.0099,483.5023,639.5457,25.475,162.6335,0.063802
43,156.5139,4.6021,227.4807,2.8793,996.6388,526.6167,713.1262,31.1506,160.3578,0.029266
44,157.4862,4.9745,224.7926,3.1146,1079.5999,528.71,758.3808,32.6723,158.5487,0.055362
45,155.9372,6.4946,226.834,2.7994,1115.8467,520.743,766.1709,24.4061,158.9474,0.058522
46,157.8888,6.1299,230.1764,2.705,1168.5681,528.1947,845.3776,20.3506,163.1623,0.034834
47,159.5735,6.5394,232.9844,2.1276,1271.3948,554.0425,951.775,14.6771,168.0691,0.042134
48,161.0253,5.8929,234.9877,1.7303,1419.4201,598.5821,1119.9621,16.4523,172.8103,0.030518
49,164.6855,5.4739,237.4468,1.7379,1489.4276,634.1788,1179.5027,18.866,174.6532,0.025847
50,166.4792,5.7967,243.8297,1.2457,1619.3585,678.6327,1358.5403,13.0997,178.0811,0.025781
51,169.1784,5.7373,254.315,0.4279,1842.7641,776.8526,1706.6656,14.0321,182.1938,0.025103
52,171.9914,5.4454,267.4991,0.6102,2029.512,842.4646,1972.5934,13.0609,186.5535,0.018803
53,173.4151,5.8078,281.3343,0.8189,2086.8417,902.142,2090.7308,12.6682,190.1207,0.010688
54,176.4134,6.6394,298.5655,0.235,2407.8481,968.3028,2703.4383,12.1486,196.8828,0.017925
55,179.8228,7.1568,315.2935,0.3273,2570.743,1041.6686,2931.451,10.5366,203.4846,0.013309
56,181.6651,7.0224,328.7579,0.4403,2609.1663,1069.5651,2982.8733,12.4572,208.2104,0.010868
57,188.4214,5.0396,342.0763,0.3678,2731.9821,1166.7876,3243.134,8.4591,211.1335,0.003167
58,188.2322,5.7208,345.2596,0.3919,2832.6137,1176.8525,3388.5722,8.4388,210.0668,0.013323
59,185.6556,8.0391,354.7336,0.6706,3043.9779,1259.7834,3789.6473,9.8167,209.745,0.019504
60,185.7093,7.0822,363.2817,0.5274,3164.8504,1328.401,3940.4594,11.0885,208.9261,0.018305
61,188.8994,5.9238,367.7659,0.5713,3188.3811,1301.6902,3687.2159,10.3863,206.5387,0.020338
62,190.7145,5.2585,367.8223,0.5996,3238.8148,1297.348,3498.8074,10.6945,204.4288,0.020969
63,195.5919,4.2725,373.1077,1.4513,3177.2026,1277.4362,3286.4155,17.8125,202.9739,0.023876
64,198.0576,4.3485,374.7753,1.3573,3226.76,1361.8358,3483.2915,18.3089,204.3091,0.024165
65,197.3332,4.7488,384.6181,1.5637,3207.0425,1356.2787,3135.3767,21.943,205.3258,0.02174
66,200.5243,4.6084,394.0602,1.921,3452.8465,1393.1119,3345.4958,19.4996,208.0275,0.031111
67,201.8125,5.1432,400.7245,1.6569,3594.3757,1402.9839,3410.9373,21.5474,206.6083,0.022281
68,203.796,5.9289,412.8727,1.5693,3888.5687,1477.9458,3899.1902,20.6658,209.9593,0.02155
69,203.7102,6.1861,426.6341,1.9158,4070.291,1557.0456,4135.1036,23.2343,212.1362,0.023914
70,205.3309,5.9247,427.6425,2.2019,4389.914,1611.4291,4577.2326,22.8746,213.7665,0.040675
71,208.3179,4.9977,420.8723,2.2162,4768.6725,1641.2476,5099.4202,25.7911,215.5904,0.035226
72,208.1749,5.0747,425.5104,2.4506,4828.9541,1731.8316,5157.32,24.0432,221.034,0.039063
73,209.0963,5.3416,428.1503,3.1947,4850.2452,1711.7005,4784.3551,39.7151,224.2367,0.030419
74,211.2324,5.198,433.6664,3.5698,4942.1141,1669.9386,4609.53,40.4841,228.816,0.046877
75,212.1405,4.5908,458.575,3.3852,5237.4799,1647.9995,4647.2827,41.868,234.5375,0.062629
76,209.7082,5.4432,473.1483,3.3837,5222.3301,1602.395,4245.7835,38.7796,235.4873,0.056602
77,214.687,3.8653,482.3472,2.7929,5229.9215,1586.15,4133.9481,28.0366,240.1483,0.038994
78,213.4634,5.674,487.2512,2.1535,5806.6989,1694.7221,4926.413,15.4102,246.0318,0.03719
79,217.1785,5.6034,497.5598,2.2403,6259.0599,1821.3289,5670.5256,15.8578,250.5153,0.033047
80,217.3644,5.995,504.0317,2.2462,6584.2818,1868.3201,5878.3625,17.5185,253.6925,0.042252


## [10] assistant

**tool call: bash**

```
cat data/scenario.csv
```

## [11] tool

quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi
81,213.6347,6.2898,488.6401,2.4174,6471.0612,1816.8254,5263.4876,19.0387,251.3708
82,209.969,6.5991,473.7185,2.5886,6316.2625,1810.9421,4712.9285,20.6907,249.0702
83,206.3662,6.9235,459.2526,2.7598,5988.2246,1807.1616,4219.9577,22.4861,246.7907
84,202.8252,7.264,445.2285,2.9311,5825.0968,1703.4189,3778.5514,24.4373,244.5321
85,199.3449,7.6211,431.6326,3.1023,5669.9475,1628.6432,3383.3162,26.5577,242.2942
86,195.9244,7.9958,418.4518,3.2735,5616.132,1587.6158,3029.4224,28.8622,240.0767
87,192.5626,8.389,405.6736,3.4447,5366.9263,1538.8038,2712.5457,31.3667,237.8795
88,189.2584,8.8015,393.2856,3.616,5184.4867,1525.9457,2428.8143,34.0884,235.7025
89,186.011,9.2342,381.2758,3.7872,5049.0716,1518.033,2174.7611,37.0464,233.5453


## [12] assistant

**[reasoning]**

> <think>
> 
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from scipy import stats

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

print("Train shape:", train.shape)
print("Scenario shape:", scenario.shape)
print("\nTrain columns:", train.columns.tolist())
print("\nTrain missing values:")
print(train.isnull().sum())
print("\nScenario missing values:")
print(scenario.isnull().sum())

```

## [13] tool

Train shape: (80, 11)
Scenario shape: (9, 10)

Train columns: ['quarter', 'gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi', 'default_rate']

Train missing values:
quarter          0
gdp              0
unemployment     0
hpi             10
bbb_spread      13
sp500           31
djia            31
nasdaq           0
vix             10
cpi              0
default_rate     0
dtype: int64

Scenario missing values:
quarter         0
gdp             0
unemployment    0
hpi             0
bbb_spread      0
sp500           0
djia            0
nasdaq          0
vix             0
cpi             0
dtype: int64


## [14] assistant

**[reasoning]**

> Let me analyze the data more carefully. Some macro series have missing values in early quarters. Let me understand the patterns and build a robust model.
> 
> Key observations:
> 1. hpi is missing for quarters 1-10 (10 missing)
> 2. bbb_spread is missing for quarters 1-13 (13 missing)
> 3. sp500 and djia are missing for quarters 1-31 (31 missing)
> 4. vix is missing for quarters 1-10 (10 missing)
> 5. nasdaq, gdp, unemployment, cpi are always present
> 
> Let me explore the data more and build a model.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from scipy import stats

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Explore the data
print("Default rate stats:")
print(train['default_rate'].describe())
print("\nDefault rate range:", train['default_rate'].min(), "to", train['default_rate'].max())

# Check correlations with default_rate
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# For each macro series, check correlation where data is available
print("\nCorrelations with default_rate (where data available):")
for col in macro_cols:
    valid = train.dropna(subset=[col])
    if len(valid) > 5:
        corr = valid[col].corr(valid['default_rate'])
        print(f"  {col}: {corr:.4f} (n={len(valid)})")

# Check scenario ranges vs training ranges
print("\nTraining ranges:")
for col in macro_cols:
    valid = train[col].dropna()
    print(f"  {col}: [{valid.min():.2f}, {valid.max():.2f}]")

print("\nScenario ranges:")
for col in macro_cols:
    print(f"  {col}: [{scenario[col].min():.2f}, {scenario[col].max():.2f}]")

```

## [15] tool

Default rate stats:
count    80.000000
mean      0.031694
std       0.015259
min       0.003167
25%       0.021692
50%       0.028357
75%       0.038461
max       0.093801
Name: default_rate, dtype: float64

Default rate range: 0.003167 to 0.093801

Correlations with default_rate (where data available):
  gdp: 0.0138 (n=80)
  unemployment: 0.2015 (n=80)
  hpi: -0.0268 (n=70)
  bbb_spread: 0.6995 (n=67)
  sp500: -0.0420 (n=49)
  djia: -0.1548 (n=49)
  nasdaq: -0.0542 (n=80)
  vix: 0.4747 (n=70)
  cpi: 0.0084 (n=80)

Training ranges:
  gdp: [106.78, 217.36]
  unemployment: [3.07, 8.04]
  hpi: [190.68, 504.03]
  bbb_spread: [0.23, 3.57]
  sp500: [699.16, 6584.28]
  djia: [379.20, 1868.32]
  nasdaq: [216.04, 5878.36]
  vix: [8.44, 41.87]
  cpi: [111.08, 253.69]

Scenario ranges:
  gdp: [186.01, 213.63]
  unemployment: [6.29, 9.23]
  hpi: [381.28, 488.64]
  bbb_spread: [2.42, 3.79]
  sp500: [5049.07, 6471.06]
  djia: [1518.03, 1816.83]
  nasdaq: [2174.76, 5263.49]
  vix: [19.04, 37.05]
  cpi: [233.55, 251.37]


## [16] assistant

**[reasoning]**

> Let me analyze the data more carefully. The key predictors seem to be `bbb_spread` (correlation 0.70) and `vix` (correlation 0.47). The scenario pushes unemployment beyond the training range (up to 9.23 vs max 8.04) and bbb_spread beyond (up to 3.79 vs max 3.57).
> 
> Let me think about what transformations might help. The default rate is a fraction, so I could use a logit transformation. Also, I should consider lagged effects and interactions.
> 
> Let me build a more sophisticated model.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
# Key insight: bbb_spread and vix are the strongest predictors
# Let's also try transformations

# Logit transform of default rate (to handle bounded [0,1])
y = train['default_rate'].values
y_clipped = np.clip(y, 0.001, 0.999)  # avoid logit issues
y_logit = np.log(y_clipped / (1 - y_clipped))

# Create feature matrix
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].fillna(method='ffill').fillna(method='bfill')

# Create features
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).fillna(method='bfill')
X['unemployment_lag1'] = X['unemployment'].shift(1).fillna(method='bfill')
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).fillna(method='bfill')
X['vix_lag1'] = X['vix'].shift(1).fillna(method='bfill')
X['default_rate_lag1'] = train['default_rate'].shift(1).fillna(method='bfill')
X['default_rate_lag2'] = train['default_rate'].shift(2).fillna(method='bfill')
X['default_rate_lag3'] = train['default_rate'].shift(3).fillna(method='bfill')

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y_logit = y_logit[drop_idx]

feature_names = X.columns.tolist()
print("Features:", feature_names)
print("Sample size:", len(X))

# Try different feature subsets and models
from sklearn.linear_model import LinearRegression

# First, let's try a simple OLS with key features
key_features = ['bbb_spread', 'vix', 'unemployment']
X_simple = X[key_features]

model_simple = sm.OLS(y_logit, sm.add_constant(X_simple)).fit()
print("\nSimple model (bbb_spread, vix, unemployment):")
print(model_simple.summary().as_csv())

# Check residuals
residuals = model_simple.resid
print("\nResidual std:", residuals.std())
print("Residual mean:", residuals.mean())

# Check for heteroskedasticity
from scipy.stats import shapiro
print("\nResidual normality test (Shapiro):")
stat, p = shapiro(residuals)
print(f"  stat={stat:.4f}, p={p:.4f}")

```

## [17] tool

Traceback (most recent call last):
  File "<stdin>", line 30, in <module>
TypeError: NDFrame.fillna() got an unexpected keyword argument 'method'



## [18] assistant

**[reasoning]**

> The pandas version doesn't support the `method` argument in `fillna`. Let me fix that.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y_logit = np.log(np.clip(train['default_rate'].values[drop_idx], 0.001, 0.999) / 
                 (1 - np.clip(train['default_rate'].values[drop_idx], 0.001, 0.999)))

feature_names = X.columns.tolist()
print("Features:", feature_names)
print("Sample size:", len(X))

# Try different feature subsets and models
# First, let's try a simple OLS with key features
key_features = ['bbb_spread', 'vix', 'unemployment']
X_simple = X[key_features]

model_simple = sm.OLS(y_logit, sm.add_constant(X_simple)).fit()
print("\nSimple model (bbb_spread, vix, unemployment):")
print(model_simple.summary().as_csv())

# Check residuals
residuals = model_simple.resid
print("\nResidual std:", residuals.std())
print("Residual mean:", residuals.mean())

# Check for heteroskedasticity
from scipy.stats import shapiro
print("\nResidual normality test (Shapiro):")
stat, p = shapiro(residuals)
print(f"  stat={stat:.4f}, p={p:.4f}")

```

## [19] tool

Features: ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi', 'unemployment_sq', 'bbb_spread_sq', 'vix_sq', 'gdp_growth', 'unemployment_diff', 'bbb_spread_diff', 'vix_diff', 'gdp_lag1', 'unemployment_lag1', 'bbb_spread_lag1', 'vix_lag1', 'default_rate_lag1', 'default_rate_lag2', 'default_rate_lag3']
Sample size: 80

Simple model (bbb_spread, vix, unemployment):
                      OLS Regression Results                     
Dep. Variable:   ,y               ,  R-squared:         ,   0.557
Model:           ,OLS             ,  Adj. R-squared:    ,   0.539
Method:          ,Least Squares   ,  F-statistic:       ,   31.81
Date:            ,Tue, 27 Oct 2026,  Prob (F-statistic):,1.99e-13
Time:            ,14:33:58        ,  Log-Likelihood:    , -26.648
No. Observations:,    80          ,  AIC:               ,   61.30
Df Residuals:    ,    76          ,  BIC:               ,   70.82
Df Model:        ,     3          ,                     ,        
Covariance Type: ,nonrobust       ,                     ,        
            ,   coef   , std err ,    t    ,P>|t| ,  [0.025 ,  0.975] 
const       ,   -4.6096,    0.226,  -20.407, 0.000,   -5.059,   -4.160
bbb_spread  ,    0.4728,    0.068,    6.959, 0.000,    0.337,    0.608
vix         ,   -0.0031,    0.008,   -0.398, 0.692,   -0.019,    0.013
unemployment,    0.0425,    0.035,    1.202, 0.233,   -0.028,    0.113
Omnibus:      ,23.708,  Durbin-Watson:     ,   1.773
Prob(Omnibus):, 0.000,  Jarque-Bera (JB):  ,  59.753
Skew:         ,-0.934,  Prob(JB):          ,1.06e-13
Kurtosis:     , 6.799,  Cond. No.          ,    117.

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.

Residual std: 0.3397475391070818
Residual mean: 1.1879386363489174e-15

Residual normality test (Shapiro):
  stat=0.9388, p=0.0008


## [20] assistant

**[reasoning]**

> The simple model with bbb_spread, vix, and unemployment shows that bbb_spread is the strongest predictor. The residuals are not normally distributed (Shapiro test p=0.0008), which is expected with financial data. Let me try a more comprehensive approach with feature selection and a robust model.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()
print("Features:", feature_names)
print("Sample size:", len(X))

# Try different feature subsets using Lasso for feature selection
# Use logit transform
y_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))

# Try Lasso for feature selection
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

lasso = Lasso(alpha=0.1, max_iter=10000)
lasso.fit(X_scaled, y_logit)

print("\nLasso coefficients:")
for name, coef in zip(feature_names, lasso.coef_):
    if abs(coef) > 0.01:
        print(f"  {name}: {coef:.4f}")

# Try Ridge regression
ridge = Ridge(alpha=1.0)
ridge.fit(X_scaled, y_logit)

print("\nRidge coefficients:")
for name, coef in zip(feature_names, ridge.coef_):
    if abs(coef) > 0.01:
        print(f"  {name}: {coef:.4f}")

# Try Gradient Boosting
gb = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.1, random_state=42)
gb.fit(X_scaled, y_logit)

print("\nGradient Boosting feature importances:")
for name, imp in sorted(zip(feature_names, gb.feature_importances_), key=lambda x: -x[1]):
    if imp > 0.01:
        print(f"  {name}: {imp:.4f}")

# Cross-validation for different models
cv = KFold(n_splits=5, shuffle=True, random_state=42)

# Ridge CV
ridge_scores = cross_val_score(ridge, X_scaled, y_logit, cv=cv, scoring='r2')
print(f"\nRidge R2 CV: {ridge_scores.mean():.4f} (+/- {ridge_scores.std():.4f})")

# GB CV
gb_scores = cross_val_score(gb, X_scaled, y_logit, cv=cv, scoring='r2')
print(f"GB R2 CV: {gb_scores.mean():.4f} (+/- {gb_scores.std():.4f})")

# Lasso CV
lasso_scores = cross_val_score(lasso, X_scaled, y_logit, cv=cv, scoring='r2')
print(f"Lasso R2 CV: {lasso_scores.mean():.4f} (+/- {lasso_scores.std():.4f})")

```

## [21] tool

Features: ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi', 'unemployment_sq', 'bbb_spread_sq', 'vix_sq', 'gdp_growth', 'unemployment_diff', 'bbb_spread_diff', 'vix_diff', 'gdp_lag1', 'unemployment_lag1', 'bbb_spread_lag1', 'vix_lag1', 'default_rate_lag1', 'default_rate_lag2', 'default_rate_lag3']
Sample size: 80

Lasso coefficients:
  bbb_spread: 0.1892
  gdp_growth: -0.0280
  bbb_spread_lag1: 0.0848

Ridge coefficients:
  gdp: 0.1071
  unemployment: -0.1397
  hpi: 0.0279
  bbb_spread: 0.0736
  sp500: 0.1444
  djia: -0.1482
  nasdaq: 0.0982
  vix: 0.1205
  cpi: -0.3571
  unemployment_sq: 0.2230
  bbb_spread_sq: 0.0636
  vix_sq: -0.1797
  gdp_growth: -0.1725
  unemployment_diff: -0.1186
  vix_diff: 0.0376
  gdp_lag1: 0.1168
  unemployment_lag1: -0.0568
  bbb_spread_lag1: 0.0721
  vix_lag1: 0.1004
  default_rate_lag1: 0.0172
  default_rate_lag2: 0.0463
  default_rate_lag3: 0.0960

Gradient Boosting feature importances:
  bbb_spread: 0.2597
  default_rate_lag1: 0.1444
  cpi: 0.0938
  bbb_spread_lag1: 0.0893
  gdp_growth: 0.0646
  unemployment_diff: 0.0593
  bbb_spread_sq: 0.0407
  vix_lag1: 0.0293
  unemployment_sq: 0.0280
  default_rate_lag3: 0.0238
  vix: 0.0232
  hpi: 0.0213
  vix_diff: 0.0205
  unemployment: 0.0183
  nasdaq: 0.0164
  default_rate_lag2: 0.0163
  unemployment_lag1: 0.0161
  bbb_spread_diff: 0.0104
  djia: 0.0103

Ridge R2 CV: 0.2760 (+/- 0.2327)
GB R2 CV: 0.1668 (+/- 0.1398)
Lasso R2 CV: 0.4103 (+/- 0.1539)


## [22] assistant

**[reasoning]**

> Let me think more carefully about this. The key predictors seem to be bbb_spread and vix based on correlations. Let me try a more focused approach with better feature engineering and model selection. I should also think about the extrapolation problem - the scenario pushes bbb_spread and unemployment beyond training ranges.
> 
> Let me try a more systematic approach:
> 1. Focus on the most important features
> 2. Try different transformations
> 3. Use proper cross-validation
> 4. Build prediction intervals properly
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()

# Try logit transform
y_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))

# Try different feature subsets
# Focus on bbb_spread, vix, unemployment as they have highest correlations
# Also try with lags

# Model 1: bbb_spread + vix + unemployment (no lags)
features_1 = ['bbb_spread', 'vix', 'unemployment']
X1 = X[features_1]
model1 = sm.OLS(y_logit, sm.add_constant(X1)).fit()
print("Model 1 (bbb_spread, vix, unemployment):")
print(f"  R2: {model1.rsquared:.4f}, Adj R2: {model1.rsquared_adj:.4f}")
print(f"  Residual std: {model1.resid.std():.4f}")

# Model 2: bbb_spread + vix + unemployment + lags
features_2 = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_lag1', 'vix_lag1', 'unemployment_lag1', 
              'default_rate_lag1', 'default_rate_lag2', 'default_rate_lag3']
X2 = X[features_2]
model2 = sm.OLS(y_logit, sm.add_constant(X2)).fit()
print("\nModel 2 (with lags):")
print(f"  R2: {model2.rsquared:.4f}, Adj R2: {model2.rsquared_adj:.4f}")
print(f"  Residual std: {model2.resid.std():.4f}")

# Model 3: bbb_spread + vix + unemployment + bbb_spread_sq
features_3 = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq']
X3 = X[features_3]
model3 = sm.OLS(y_logit, sm.add_constant(X3)).fit()
print("\nModel 3 (with bbb_spread_sq):")
print(f"  R2: {model3.rsquared:.4f}, Adj R2: {model3.rsquared_adj:.4f}")
print(f"  Residual std: {model3.resid.std():.4f}")

# Model 4: bbb_spread + vix + unemployment + bbb_spread_sq + unemployment_sq
features_4 = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq']
X4 = X[features_4]
model4 = sm.OLS(y_logit, sm.add_constant(X4)).fit()
print("\nModel 4 (with sq terms):")
print(f"  R2: {model4.rsquared:.4f}, Adj R2: {model4.rsquared_adj:.4f}")
print(f"  Residual std: {model4.resid.std():.4f}")

# Model 5: bbb_spread + vix + unemployment + bbb_spread_sq + unemployment_sq + lags
features_5 = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq',
              'bbb_spread_lag1', 'vix_lag1', 'unemployment_lag1', 
              'default_rate_lag1', 'default_rate_lag2', 'default_rate_lag3']
X5 = X[features_5]
model5 = sm.OLS(y_logit, sm.add_constant(X5)).fit()
print("\nModel 5 (with sq + lags):")
print(f"  R2: {model5.rsquared:.4f}, Adj R2: {model5.rsquared_adj:.4f}")
print(f"  Residual std: {model5.resid.std():.4f}")

# Model 6: bbb_spread + vix + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth
features_6 = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth']
X6 = X[features_6]
model6 = sm.OLS(y_logit, sm.add_constant(X6)).fit()
print("\nModel 6 (with sq + gdp_growth):")
print(f"  R2: {model6.rsquared:.4f}, Adj R2: {model6.rsquared_adj:.4f}")
print(f"  Residual std: {model6.resid.std():.4f}")

# Model 7: bbb_spread + vix + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + lags
features_7 = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth',
              'bbb_spread_lag1', 'vix_lag1', 'unemployment_lag1', 
              'default_rate_lag1', 'default_rate_lag2', 'default_rate_lag3']
X7 = X[features_7]
model7 = sm.OLS(y_logit, sm.add_constant(X7)).fit()
print("\nModel 7 (with sq + gdp_growth + lags):")
print(f"  R2: {model7.rsquared:.4f}, Adj R2: {model7.rsquared_adj:.4f}")
print(f"  Residual std: {model7.resid.std():.4f}")

# Compare AIC/BIC
print("\nModel comparison:")
for i, (name, model) in enumerate([('1', model1), ('2', model2), ('3', model3), ('4', model4), 
                                     ('5', model5), ('6', model6), ('7', model7)], 1):
    print(f"  Model {name}: AIC={model.aic:.2f}, BIC={model.bic:.2f}, Adj R2={model.rsquared_adj:.4f}")

```

## [23] tool

Model 1 (bbb_spread, vix, unemployment):
  R2: 0.5567, Adj R2: 0.5392
  Residual std: 0.3397

Model 2 (with lags):
  R2: 0.5768, Adj R2: 0.5224
  Residual std: 0.3319

Model 3 (with bbb_spread_sq):
  R2: 0.5681, Adj R2: 0.5451
  Residual std: 0.3353

Model 4 (with sq terms):
  R2: 0.5738, Adj R2: 0.5450
  Residual std: 0.3331

Model 5 (with sq + lags):
  R2: 0.5962, Adj R2: 0.5308
  Residual std: 0.3243

Model 6 (with sq + gdp_growth):
  R2: 0.5955, Adj R2: 0.5623
  Residual std: 0.3245

Model 7 (with sq + gdp_growth + lags):
  R2: 0.6472, Adj R2: 0.5840
  Residual std: 0.3031

Model comparison:
  Model 1: AIC=61.30, BIC=70.82, Adj R2=0.5392
  Model 2: AIC=69.57, BIC=93.39, Adj R2=0.5224
  Model 3: AIC=61.21, BIC=73.12, Adj R2=0.5451
  Model 4: AIC=62.15, BIC=76.44, Adj R2=0.5450
  Model 5: AIC=69.84, BIC=98.42, Adj R2=0.5308
  Model 6: AIC=59.96, BIC=76.64, Adj R2=0.5623
  Model 7: AIC=61.04, BIC=92.00, Adj R2=0.5840


## [24] assistant

**[reasoning]**

> Model 7 has the best adjusted R2 (0.5840) and lowest AIC among the more complex models. Let me now build a comprehensive prediction script that:
> 
> 1. Uses the best model (Model 7)
> 2. Handles the scenario data properly
> 3. Generates prediction intervals
> 4. Handles extrapolation concerns
> 
> Let me also think about the prediction interval. Since we're predicting in logit space, I need to:
> 1. Predict in logit space
> 2. Add uncertainty (residual std)
> 3. Transform back to probability space
> 
> For the prediction interval, I should account for:
> - Parameter uncertainty
> - Residual variance
> - Extrapolation uncertainty (since scenario values are outside training range)
> 
> Let me also check if the scenario values are indeed outside the training range for key features.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()

# Model 7 features
features_7 = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth',
              'bbb_spread_lag1', 'vix_lag1', 'unemployment_lag1', 
              'default_rate_lag1', 'default_rate_lag2', 'default_rate_lag3']

X7 = X[features_7]
y_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))

model7 = sm.OLS(y_logit, sm.add_constant(X7)).fit()
print("Model 7 summary:")
print(model7.summary().as_csv())

# Check residuals
residuals = model7.resid
print(f"\nResidual std: {residuals.std():.4f}")
print(f"Residual mean: {residuals.mean():.4f}")

# Check for autocorrelation (Durbin-Watson)
print(f"Durbin-Watson: {model7.dw_stat:.4f}")

# Check for heteroskedasticity
from scipy.stats import shapiro
stat, p = shapiro(residuals)
print(f"Shapiro normality: stat={stat:.4f}, p={p:.4f}")

# Check scenario feature values vs training
print("\nScenario feature values vs training ranges:")
for feat in features_7:
    train_vals = X7[feat].values
    scenario_vals = []
    # Need to compute scenario features
    print(f"  {feat}: train=[{train_vals.min():.4f}, {train_vals.max():.4f}]")

```

## [25] tool

Traceback (most recent call last):
  File "<stdin>", line 67, in <module>
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/wrapper.py", line 34, in __getattribute__
    obj = getattr(results, attr)
          ^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'OLSResults' object has no attribute 'dw_stat'

Model 7 summary:
                      OLS Regression Results                     
Dep. Variable:   ,y               ,  R-squared:         ,   0.647
Model:           ,OLS             ,  Adj. R-squared:    ,   0.584
Method:          ,Least Squares   ,  F-statistic:       ,   10.24
Date:            ,Tue, 27 Oct 2026,  Prob (F-statistic):,4.62e-11
Time:            ,14:35:18        ,  Log-Likelihood:    , -17.519
No. Observations:,    80          ,  AIC:               ,   61.04
Df Residuals:    ,    67          ,  BIC:               ,   92.00
Df Model:        ,    12          ,                     ,        
Covariance Type: ,nonrobust       ,                     ,        
                 ,   coef   , std err ,    t    ,P>|t| ,  [0.025 ,  0.975] 
const            ,   -3.3984,    0.828,   -4.104, 0.000,   -5.051,   -1.745
bbb_spread       ,    0.4461,    0.273,    1.634, 0.107,   -0.099,    0.991
vix              ,    0.0107,    0.015,    0.730, 0.468,   -0.019,    0.040
unemployment     ,   -0.6051,    0.325,   -1.859, 0.067,   -1.255,    0.045
bbb_spread_sq    ,   -0.0796,    0.064,   -1.248, 0.217,   -0.207,    0.048
unemployment_sq  ,    0.0469,    0.029,    1.641, 0.105,   -0.010,    0.104
gdp_growth       ,   -0.1076,    0.035,   -3.112, 0.003,   -0.177,   -0.039
bbb_spread_lag1  ,    0.0543,    0.166,    0.327, 0.745,   -0.277,    0.386
vix_lag1         ,    0.0057,    0.014,    0.420, 0.676,   -0.021,    0.033
unemployment_lag1,    0.1162,    0.073,    1.584, 0.118,   -0.030,    0.263
default_rate_lag1,    1.1045,    3.559,    0.310, 0.757,   -6.000,    8.209
default_rate_lag2,    3.3200,    3.301,    1.006, 0.318,   -3.269,    9.909
default_rate_lag3,    6.1845,    3.195,    1.936, 0.057,   -0.193,   12.562
Omnibus:      , 6.490,  Durbin-Watson:     ,   1.815
Prob(Omnibus):, 0.039,  Jarque-Bera (JB):  ,   6.384
Skew:         ,-0.470,  Prob(JB):          ,  0.0411
Kurtosis:     , 4.015,  Cond. No.          ,4.22e+03

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
[2] The condition number is large, 4.22e+03. This might indicate that there are
strong multicollinearity or other numerical problems.

Residual std: 0.3031
Residual mean: -0.0000


## [26] assistant

**[reasoning]**

> The model has a high condition number (4.22e+03) indicating multicollinearity. The default_rate_lag coefficients are very large and unstable. Let me try a simpler approach - focus on the most important features without too many lags, and use a more robust approach.
> 
> Let me think about this differently. The key drivers seem to be:
> 1. bbb_spread (strong positive correlation)
> 2. vix (positive correlation)
> 3. unemployment (positive correlation)
> 
> The scenario pushes these beyond training ranges:
> - bbb_spread: [2.42, 3.79] vs training [0.23, 3.57] - slightly beyond
> - unemployment: [6.29, 9.23] vs training [3.07, 8.04] - beyond
> - vix: [19.04, 37.05] vs training [8.44, 41.87] - within range
> 
> Let me try a simpler model with just the key features and their transformations, and use cross-validation to select the best model. I should also consider using the raw default_rate (not logit) with a model that handles bounded outputs.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()

# Let's try a simpler approach - just bbb_spread and vix as primary drivers
# These have the strongest correlations
# Also try with unemployment

# Model A: bbb_spread + vix
features_a = ['bbb_spread', 'vix']
Xa = X[features_a]
ya_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))
model_a = sm.OLS(ya_logit, sm.add_constant(Xa)).fit()
print("Model A (bbb_spread, vix):")
print(f"  R2: {model_a.rsquared:.4f}, Adj R2: {model_a.rsquared_adj:.4f}")
print(f"  Residual std: {model_a.resid.std():.4f}")
print(model_a.summary().as_csv())

# Model B: bbb_spread + vix + unemployment
features_b = ['bbb_spread', 'vix', 'unemployment']
Xb = X[features_b]
model_b = sm.OLS(ya_logit, sm.add_constant(Xb)).fit()
print("\nModel B (bbb_spread, vix, unemployment):")
print(f"  R2: {model_b.rsquared:.4f}, Adj R2: {model_b.rsquared_adj:.4f}")
print(f"  Residual std: {model_b.resid.std():.4f}")

# Model C: bbb_spread + vix + unemployment + bbb_spread_sq
features_c = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq']
Xc = X[features_c]
model_c = sm.OLS(ya_logit, sm.add_constant(Xc)).fit()
print("\nModel C (bbb_spread, vix, unemployment, bbb_spread_sq):")
print(f"  R2: {model_c.rsquared:.4f}, Adj R2: {model_c.rsquared_adj:.4f}")
print(f"  Residual std: {model_c.resid.std():.4f}")

# Model D: bbb_spread + vix + unemployment + bbb_spread_sq + unemployment_sq
features_d = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq']
Xd = X[features_d]
model_d = sm.OLS(ya_logit, sm.add_constant(Xd)).fit()
print("\nModel D (bbb_spread, vix, unemployment, bbb_spread_sq, unemployment_sq):")
print(f"  R2: {model_d.rsquared:.4f}, Adj R2: {model_d.rsquared_adj:.4f}")
print(f"  Residual std: {model_d.resid.std():.4f}")

# Model E: bbb_spread + vix + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth
features_e = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth']
Xe = X[features_e]
model_e = sm.OLS(ya_logit, sm.add_constant(Xe)).fit()
print("\nModel E (bbb_spread, vix, unemployment, bbb_spread_sq, unemployment_sq, gdp_growth):")
print(f"  R2: {model_e.rsquared:.4f}, Adj R2: {model_e.rsquared_adj:.4f}")
print(f"  Residual std: {model_e.resid.std():.4f}")

# Model F: bbb_spread + vix + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1
features_f = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1']
Xf = X[features_f]
model_f = sm.OLS(ya_logit, sm.add_constant(Xf)).fit()
print("\nModel F (with default_rate_lag1):")
print(f"  R2: {model_f.rsquared:.4f}, Adj R2: {model_f.rsquared_adj:.4f}")
print(f"  Residual std: {model_f.resid.std():.4f}")

# Model G: bbb_spread + vix + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1 + default_rate_lag2
features_g = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1', 'default_rate_lag2']
Xg = X[features_g]
model_g = sm.OLS(ya_logit, sm.add_constant(Xg)).fit()
print("\nModel G (with default_rate_lag1, default_rate_lag2):")
print(f"  R2: {model_g.rsquared:.4f}, Adj R2: {model_g.rsquared_adj:.4f}")
print(f"  Residual std: {model_g.resid.std():.4f}")

# Compare AIC/BIC
print("\nModel comparison:")
for i, (name, model) in enumerate([('A', model_a), ('B', model_b), ('C', model_c), ('D', model_d), 
                                     ('E', model_e), ('F', model_f), ('G', model_g)], 1):
    print(f"  Model {name}: AIC={model.aic:.2f}, BIC={model.bic:.2f}, Adj R2={model.rsquared_adj:.4f}")

```

## [27] tool

Model A (bbb_spread, vix):
  R2: 0.5483, Adj R2: 0.5365
  Residual std: 0.3430
                      OLS Regression Results                     
Dep. Variable:   ,y               ,  R-squared:         ,   0.548
Model:           ,OLS             ,  Adj. R-squared:    ,   0.537
Method:          ,Least Squares   ,  F-statistic:       ,   46.73
Date:            ,Tue, 27 Oct 2026,  Prob (F-statistic):,5.17e-14
Time:            ,14:35:56        ,  Log-Likelihood:    , -27.401
No. Observations:,    80          ,  AIC:               ,   60.80
Df Residuals:    ,    77          ,  BIC:               ,   67.95
Df Model:        ,     2          ,                     ,        
Covariance Type: ,nonrobust       ,                     ,        
          ,   coef   , std err ,    t    ,P>|t| ,  [0.025 ,  0.975] 
const     ,   -4.3710,    0.108,  -40.399, 0.000,   -4.586,   -4.156
bbb_spread,    0.4832,    0.068,    7.149, 0.000,    0.349,    0.618
vix       ,   -0.0045,    0.008,   -0.582, 0.562,   -0.020,    0.011
Omnibus:      ,22.587,  Durbin-Watson:     ,   1.790
Prob(Omnibus):, 0.000,  Jarque-Bera (JB):  ,  58.911
Skew:         ,-0.866,  Prob(JB):          ,1.61e-13
Kurtosis:     , 6.831,  Cond. No.          ,    54.7

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.

Model B (bbb_spread, vix, unemployment):
  R2: 0.5567, Adj R2: 0.5392
  Residual std: 0.3397

Model C (bbb_spread, vix, unemployment, bbb_spread_sq):
  R2: 0.5681, Adj R2: 0.5451
  Residual std: 0.3353

Model D (bbb_spread, vix, unemployment, bbb_spread_sq, unemployment_sq):
  R2: 0.5738, Adj R2: 0.5450
  Residual std: 0.3331

Model E (bbb_spread, vix, unemployment, bbb_spread_sq, unemployment_sq, gdp_growth):
  R2: 0.5955, Adj R2: 0.5623
  Residual std: 0.3245

Model F (with default_rate_lag1):
  R2: 0.6029, Adj R2: 0.5643
  Residual std: 0.3216

Model G (with default_rate_lag1, default_rate_lag2):
  R2: 0.6149, Adj R2: 0.5715
  Residual std: 0.3167

Model comparison:
  Model A: AIC=60.80, BIC=67.95, Adj R2=0.5365
  Model B: AIC=61.30, BIC=70.82, Adj R2=0.5392
  Model C: AIC=61.21, BIC=73.12, Adj R2=0.5451
  Model D: AIC=62.15, BIC=76.44, Adj R2=0.5450
  Model E: AIC=59.96, BIC=76.64, Adj R2=0.5623
  Model F: AIC=60.49, BIC=79.55, Adj R2=0.5643
  Model G: AIC=60.04, BIC=81.48, Adj R2=0.5715


## [28] assistant

**[reasoning]**

> Now let me think about the best approach. The scenario pushes drivers beyond training ranges. Key observations:
> 
> 1. bbb_spread is the strongest predictor (correlation 0.70)
> 2. vix is the second strongest (correlation 0.47)
> 3. unemployment has moderate correlation (0.20)
> 4. The scenario has bbb_spread going up to 3.79 (training max was 3.57)
> 5. The scenario has unemployment going up to 9.23 (training max was 8.04)
> 6. The scenario has vix going up to 37.05 (training max was 41.87)
> 
> For extrapolation, I should use a model that's robust. Let me try:
> 1. A simpler model with just bbb_spread (most important)
> 2. Use the residual std from cross-validation for prediction intervals
> 3. Consider using a non-parametric approach or a model that handles extrapolation better
> 
> Let me also think about the prediction interval. The residual std in logit space is about 0.32. When I transform back to probability space, the interval will be asymmetric.
> 
> Let me build a comprehensive solution:
> 1. Use a model with bbb_spread as the primary driver
> 2. Add unemployment and vix as secondary drivers
> 3. Use cross-validation to estimate prediction error
> 4. Generate prediction intervals using the residual distribution
> 
> Let me also try a different approach - using the raw default rate (not logit) with a model that can handle the bounded nature better, or use a beta regression approach.
> 
> Actually, let me think more carefully. The key issue is extrapolation. The scenario has:
> - bbb_spread: 2.42 to 3.79 (training: 0.23 to 3.57) - slightly beyond
> - unemployment: 6.29 to 9.23 (training: 3.07 to 8.04) - beyond
> - vix: 19.04 to 37.05 (training: 8.44 to 41.87) - within range
> 
> So the main extrapolation is in unemployment and bbb_spread.
> 
> Let me try a few approaches:
> 1. Simple linear model with bbb_spread + unemployment
> 2. Try to use the training data to understand the relationship
> 3. Use cross-validation for robust error estimation
> 
> Let me also try a different approach - using the raw default rate with a model that constrains predictions to [0,1].
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()

# Let's try a different approach - use raw default rate with a model
# that handles bounded outputs better

# Model H: bbb_spread + unemployment (raw, no logit)
features_h = ['bbb_spread', 'unemployment']
Xh = X[features_h]
model_h = sm.OLS(y, sm.add_constant(Xh)).fit()
print("Model H (bbb_spread, unemployment, raw):")
print(f"  R2: {model_h.rsquared:.4f}, Adj R2: {model_h.rsquared_adj:.4f}")
print(f"  Residual std: {model_h.resid.std():.4f}")
print(model_h.summary().as_csv())

# Model I: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq (raw)
features_i = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq']
Xi = X[features_i]
model_i = sm.OLS(y, sm.add_constant(Xi)).fit()
print("\nModel I (bbb_spread, unemployment, sq terms, raw):")
print(f"  R2: {model_i.rsquared:.4f}, Adj R2: {model_i.rsquared_adj:.4f}")
print(f"  Residual std: {model_i.resid.std():.4f}")

# Model J: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth (raw)
features_j = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth']
Xj = X[features_j]
model_j = sm.OLS(y, sm.add_constant(Xj)).fit()
print("\nModel J (with gdp_growth, raw):")
print(f"  R2: {model_j.rsquared:.4f}, Adj R2: {model_j.rsquared_adj:.4f}")
print(f"  Residual std: {model_j.resid.std():.4f}")

# Model K: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1 (raw)
features_k = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1']
Xk = X[features_k]
model_k = sm.OLS(y, sm.add_constant(Xk)).fit()
print("\nModel K (with default_rate_lag1, raw):")
print(f"  R2: {model_k.rsquared:.4f}, Adj R2: {model_k.rsquared_adj:.4f}")
print(f"  Residual std: {model_k.resid.std():.4f}")

# Model L: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1 + default_rate_lag2 (raw)
features_l = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1', 'default_rate_lag2']
Xl = X[features_l]
model_l = sm.OLS(y, sm.add_constant(Xl)).fit()
print("\nModel L (with default_rate_lag1, lag2, raw):")
print(f"  R2: {model_l.rsquared:.4f}, Adj R2: {model_l.rsquared_adj:.4f}")
print(f"  Residual std: {model_l.resid.std():.4f}")

# Compare AIC/BIC
print("\nModel comparison (raw):")
for i, (name, model) in enumerate([('H', model_h), ('I', model_i), ('J', model_j), ('K', model_k), 
                                     ('L', model_l)], 1):
    print(f"  Model {name}: AIC={model.aic:.2f}, BIC={model.bic:.2f}, Adj R2={model.rsquared_adj:.4f}")

```

## [29] tool

Model H (bbb_spread, unemployment, raw):
  R2: 0.5162, Adj R2: 0.5036
  Residual std: 0.0106
                      OLS Regression Results                     
Dep. Variable:   ,y               ,  R-squared:         ,   0.516
Model:           ,OLS             ,  Adj. R-squared:    ,   0.504
Method:          ,Least Squares   ,  F-statistic:       ,   41.07
Date:            ,Tue, 27 Oct 2026,  Prob (F-statistic):,7.26e-13
Time:            ,14:36:33        ,  Log-Likelihood:    ,  250.63
No. Observations:,    80          ,  AIC:               ,  -495.3
Df Residuals:    ,    77          ,  BIC:               ,  -488.1
Df Model:        ,     2          ,                     ,        
Covariance Type: ,nonrobust       ,                     ,        
            ,   coef   , std err ,    t    ,P>|t| ,  [0.025 ,  0.975] 
const       ,   -0.0062,    0.007,   -0.935, 0.353,   -0.019,    0.007
bbb_spread  ,    0.0127,    0.001,    8.700, 0.000,    0.010,    0.016
unemployment,    0.0025,    0.001,    2.292, 0.025,    0.000,    0.005
Omnibus:      ,37.142,  Durbin-Watson:     ,   2.094
Prob(Omnibus):, 0.000,  Jarque-Bera (JB):  , 131.277
Skew:         , 1.389,  Prob(JB):          ,3.12e-29
Kurtosis:     , 8.627,  Cond. No.          ,    33.5

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.

Model I (bbb_spread, unemployment, sq terms, raw):
  R2: 0.5249, Adj R2: 0.4995
  Residual std: 0.0105

Model J (with gdp_growth, raw):
  R2: 0.5339, Adj R2: 0.5024
  Residual std: 0.0104

Model K (with default_rate_lag1, raw):
  R2: 0.5348, Adj R2: 0.4965
  Residual std: 0.0104

Model L (with default_rate_lag1, lag2, raw):
  R2: 0.5537, Adj R2: 0.5103
  Residual std: 0.0102

Model comparison (raw):
  Model H: AIC=-495.27, BIC=-488.12, Adj R2=0.5036
  Model I: AIC=-492.72, BIC=-480.81, Adj R2=0.4995
  Model J: AIC=-492.26, BIC=-477.97, Adj R2=0.5024
  Model K: AIC=-490.40, BIC=-473.73, Adj R2=0.4965
  Model L: AIC=-491.72, BIC=-472.67, Adj R2=0.5103


## [30] assistant

**[reasoning]**

> Now let me think about the best approach. The logit-transformed models have better AIC/BIC and the residuals are more interpretable. Let me focus on the best models and think about prediction intervals.
> 
> Key observations:
> 1. bbb_spread is the strongest predictor (correlation 0.70 with default_rate)
> 2. vix has moderate correlation (0.47)
> 3. unemployment has weak correlation (0.20)
> 4. The scenario pushes bbb_spread beyond training range (up to 3.79 vs max 3.57)
> 5. The scenario pushes unemployment beyond training range (up to 9.23 vs max 8.04)
> 
> For prediction intervals, I need to account for:
> 1. Model uncertainty (parameter uncertainty)
> 2. Residual variance (process uncertainty)
> 3. Extrapolation uncertainty (since scenario is out of sample)
> 
> Let me build a comprehensive model and generate predictions.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()

# Use the best logit model: Model G
features_g = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1', 'default_rate_lag2']
Xg = X[features_g]
y_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))

model_g = sm.OLS(y_logit, sm.add_constant(Xg)).fit()
print("Model G summary:")
print(model_g.summary().as_csv())

# Check residuals
residuals = model_g.resid
print(f"\nResidual std: {residuals.std():.4f}")
print(f"Residual mean: {residuals.mean():.4f}")

# Now let's also try a non-parametric approach
# Use Gradient Boosting on the logit-transformed target
scaler = StandardScaler()
Xg_scaled = scaler.fit_transform(Xg)

gb = GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, 
                                min_samples_leaf=5, random_state=42)
gb.fit(Xg_scaled, y_logit)

# Check feature importances
print("\nGB feature importances:")
for name, imp in sorted(zip(features_g, gb.feature_importances_), key=lambda x: -x[1]):
    print(f"  {name}: {imp:.4f}")

# Cross-validation for GB
cv = KFold(n_splits=5, shuffle=True, random_state=42)
gb_scores = cross_val_score(gb, Xg_scaled, y_logit, cv=cv, scoring='r2')
print(f"\nGB R2 CV: {gb_scores.mean():.4f} (+/- {gb_scores.std():.4f})")

# Also try with raw default rate
gb_raw = GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, 
                                    min_samples_leaf=5, random_state=42)
gb_raw.fit(Xg_scaled, y)
gb_raw_scores = cross_val_score(gb_raw, Xg_scaled, y, cv=cv, scoring='r2')
print(f"GB (raw) R2 CV: {gb_raw_scores.mean():.4f} (+/- {gb_raw_scores.std():.4f})")

```

## [31] tool

Model G summary:
                      OLS Regression Results                     
Dep. Variable:   ,y               ,  R-squared:         ,   0.615
Model:           ,OLS             ,  Adj. R-squared:    ,   0.571
Method:          ,Least Squares   ,  F-statistic:       ,   14.17
Date:            ,Tue, 27 Oct 2026,  Prob (F-statistic):,4.18e-12
Time:            ,14:36:59        ,  Log-Likelihood:    , -21.019
No. Observations:,    80          ,  AIC:               ,   60.04
Df Residuals:    ,    71          ,  BIC:               ,   81.48
Df Model:        ,     8          ,                     ,        
Covariance Type: ,nonrobust       ,                     ,        
                 ,   coef   , std err ,    t    ,P>|t| ,  [0.025 ,  0.975] 
const            ,   -3.7924,    0.815,   -4.652, 0.000,   -5.418,   -2.167
bbb_spread       ,    0.5539,    0.224,    2.476, 0.016,    0.108,    1.000
vix              ,    0.0106,    0.010,    1.038, 0.303,   -0.010,    0.031
unemployment     ,   -0.3340,    0.306,   -1.091, 0.279,   -0.944,    0.277
bbb_spread_sq    ,   -0.0781,    0.064,   -1.223, 0.226,   -0.205,    0.049
unemployment_sq  ,    0.0327,    0.028,    1.162, 0.249,   -0.023,    0.089
gdp_growth       ,   -0.0647,    0.026,   -2.533, 0.014,   -0.116,   -0.014
default_rate_lag1,    3.2958,    3.363,    0.980, 0.330,   -3.411,   10.002
default_rate_lag2,    4.7394,    3.185,    1.488, 0.141,   -1.611,   11.090
Omnibus:      , 4.041,  Durbin-Watson:     ,   1.972
Prob(Omnibus):, 0.133,  Jarque-Bera (JB):  ,   3.575
Skew:         ,-0.309,  Prob(JB):          ,   0.167
Kurtosis:     , 3.831,  Cond. No.          ,3.58e+03

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
[2] The condition number is large, 3.58e+03. This might indicate that there are
strong multicollinearity or other numerical problems.

Residual std: 0.3167
Residual mean: 0.0000

GB feature importances:
  bbb_spread: 0.2840
  bbb_spread_sq: 0.1871
  default_rate_lag1: 0.1681
  vix: 0.1257
  gdp_growth: 0.0923
  default_rate_lag2: 0.0541
  unemployment_sq: 0.0524
  unemployment: 0.0363

GB R2 CV: -0.0318 (+/- 0.2850)
GB (raw) R2 CV: 0.1689 (+/- 0.1880)


## [32] assistant

**[reasoning]**

> The cross-validation scores are poor, especially for GB. This suggests overfitting. Let me try a simpler approach with better feature selection and focus on the most important predictors. The key insight is that bbb_spread is the strongest predictor. Let me also think about the scenario - it pushes drivers beyond training range, so I need to be careful about extrapolation.
> 
> Let me try a more robust approach:
> 1. Use a simpler model with fewer features
> 2. Use cross-validation to select the best model
> 3. Compute prediction intervals properly
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()

# Let's try a comprehensive approach with many feature subsets
# and use Leave-One-Out CV for small dataset

# Key features to try
base_features = ['bbb_spread', 'vix', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 
                 'gdp_growth', 'default_rate_lag1', 'default_rate_lag2', 'default_rate_lag3',
                 'bbb_spread_lag1', 'vix_lag1', 'unemployment_lag1']

# Try different subsets with LOO CV
from sklearn.linear_model import Ridge

# First, let's try just bbb_spread + unemployment (simplest meaningful model)
features_simple = ['bbb_spread', 'unemployment']
X_simple = X[features_simple]
y_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))

# LOO CV for simple model
loo = LeaveOneOut()
simple_errors = []
for train_idx, test_idx in loo.split(X_simple):
    X_train, X_test = X_simple.iloc[train_idx], X_simple.iloc[test_idx]
    y_train = y_logit[train_idx]
    
    model = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    pred = model.predict(sm.add_constant(X_test))
    simple_errors.append((y_logit[test_idx] - pred) ** 2)

simple_mse = np.mean(simple_errors)
print(f"Simple model (bbb_spread, unemployment) LOO MSE (logit): {simple_mse:.4f}")
print(f"Simple model LOO RMSE (logit): {np.sqrt(simple_mse):.4f}")

# Now try with more features
# Model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth
features_med = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth']
X_med = X[features_med]

med_errors = []
for train_idx, test_idx in loo.split(X_med):
    X_train, X_test = X_med.iloc[train_idx], X_med.iloc[test_idx]
    y_train = y_logit[train_idx]
    
    model = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    pred = model.predict(sm.add_constant(X_test))
    med_errors.append((y_logit[test_idx] - pred) ** 2)

med_mse = np.mean(med_errors)
print(f"Medium model LOO MSE (logit): {med_mse:.4f}")
print(f"Medium model LOO RMSE (logit): {np.sqrt(med_mse):.4f}")

# Model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1
features_full = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1']
X_full = X[features_full]

full_errors = []
for train_idx, test_idx in loo.split(X_full):
    X_train, X_test = X_full.iloc[train_idx], X_full.iloc[test_idx]
    y_train = y_logit[train_idx]
    
    model = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    pred = model.predict(sm.add_constant(X_test))
    full_errors.append((y_logit[test_idx] - pred) ** 2)

full_mse = np.mean(full_errors)
print(f"Full model LOO MSE (logit): {full_mse:.4f}")
print(f"Full model LOO RMSE (logit): {np.sqrt(full_mse):.4f}")

# Model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1 + default_rate_lag2
features_full2 = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1', 'default_rate_lag2']
X_full2 = X[features_full2]

full2_errors = []
for train_idx, test_idx in loo.split(X_full2):
    X_train, X_test = X_full2.iloc[train_idx], X_full2.iloc[test_idx]
    y_train = y_logit[train_idx]
    
    model = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    pred = model.predict(sm.add_constant(X_test))
    full2_errors.append((y_logit[test_idx] - pred) ** 2)

full2_mse = np.mean(full2_errors)
print(f"Full2 model LOO MSE (logit): {full2_mse:.4f}")
print(f"Full2 model LOO RMSE (logit): {np.sqrt(full2_mse):.4f}")

# Also try with raw default rate
print("\n--- Raw default rate models ---")

# Simple raw
simple_raw_errors = []
for train_idx, test_idx in loo.split(X_simple):
    X_train, X_test = X_simple.iloc[train_idx], X_simple.iloc[test_idx]
    y_train = y[train_idx]
    
    model = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    pred = model.predict(sm.add_constant(X_test))
    simple_raw_errors.append((y[test_idx] - pred) ** 2)

simple_raw_mse = np.mean(simple_raw_errors)
print(f"Simple raw LOO MSE: {simple_raw_mse:.6f}")
print(f"Simple raw LOO RMSE: {np.sqrt(simple_raw_mse):.6f}")

# Medium raw
med_raw_errors = []
for train_idx, test_idx in loo.split(X_med):
    X_train, X_test = X_med.iloc[train_idx], X_med.iloc[test_idx]
    y_train = y[train_idx]
    
    model = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    pred = model.predict(sm.add_constant(X_test))
    med_raw_errors.append((y[test_idx] - pred) ** 2)

med_raw_mse = np.mean(med_raw_errors)
print(f"Medium raw LOO MSE: {med_raw_mse:.6f}")
print(f"Medium raw LOO RMSE: {np.sqrt(med_raw_mse):.6f}")

# Full raw
full_raw_errors = []
for train_idx, test_idx in loo.split(X_full):
    X_train, X_test = X_full.iloc[train_idx], X_full.iloc[test_idx]
    y_train = y[train_idx]
    
    model = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    pred = model.predict(sm.add_constant(X_test))
    full_raw_errors.append((y[test_idx] - pred) ** 2)

full_raw_mse = np.mean(full_raw_errors)
print(f"Full raw LOO MSE: {full_raw_mse:.6f}")
print(f"Full raw LOO RMSE: {np.sqrt(full_raw_mse):.6f}")

# Full2 raw
full2_raw_errors = []
for train_idx, test_idx in loo.split(X_full2):
    X_train, X_test = X_full2.iloc[train_idx], X_full2.iloc[test_idx]
    y_train = y[train_idx]
    
    model = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    pred = model.predict(sm.add_constant(X_test))
    full2_raw_errors.append((y[test_idx] - pred) ** 2)

full2_raw_mse = np.mean(full2_raw_errors)
print(f"Full2 raw LOO MSE: {full2_raw_mse:.6f}")
print(f"Full2 raw LOO RMSE: {np.sqrt(full2_raw_mse):.6f}")

```

## [33] tool

Traceback (most recent call last):
  File "<stdin>", line 73, in <module>
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 1174, in predict
    predict_results = self.model.predict(self.params, exog, *args,
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 409, in predict
    return np.dot(exog, params)
           ^^^^^^^^^^^^^^^^^^^^
ValueError: shapes (1,2) and (3,) not aligned: 2 (dim 1) != 3 (dim 0)



## [34] assistant

**[reasoning]**

> The issue is that when we have a single test sample, the constant column isn't being added properly. Let me fix this.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()

# Use LOO CV with proper constant handling
loo = LeaveOneOut()

# Model: bbb_spread + unemployment (simple)
features_simple = ['bbb_spread', 'unemployment']
X_simple = X[features_simple]
y_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))

simple_errors = []
for train_idx, test_idx in loo.split(X_simple):
    X_train, X_test = X_simple.iloc[train_idx], X_simple.iloc[test_idx]
    y_train = y_logit[train_idx]
    
    X_train_c = sm.add_constant(X_train)
    X_test_c = sm.add_constant(X_test)
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    simple_errors.append((y_logit[test_idx] - pred) ** 2)

simple_mse = np.mean(simple_errors)
print(f"Simple model (bbb_spread, unemployment) LOO MSE (logit): {simple_mse:.4f}")
print(f"Simple model LOO RMSE (logit): {np.sqrt(simple_mse):.4f}")

# Model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth
features_med = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth']
X_med = X[features_med]

med_errors = []
for train_idx, test_idx in loo.split(X_med):
    X_train, X_test = X_med.iloc[train_idx], X_med.iloc[test_idx]
    y_train = y_logit[train_idx]
    
    X_train_c = sm.add_constant(X_train)
    X_test_c = sm.add_constant(X_test)
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    med_errors.append((y_logit[test_idx] - pred) ** 2)

med_mse = np.mean(med_errors)
print(f"Medium model LOO MSE (logit): {med_mse:.4f}")
print(f"Medium model LOO RMSE (logit): {np.sqrt(med_mse):.4f}")

# Model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1
features_full = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1']
X_full = X[features_full]

full_errors = []
for train_idx, test_idx in loo.split(X_full):
    X_train, X_test = X_full.iloc[train_idx], X_full.iloc[test_idx]
    y_train = y_logit[train_idx]
    
    X_train_c = sm.add_constant(X_train)
    X_test_c = sm.add_constant(X_test)
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    full_errors.append((y_logit[test_idx] - pred) ** 2)

full_mse = np.mean(full_errors)
print(f"Full model LOO MSE (logit): {full_mse:.4f}")
print(f"Full model LOO RMSE (logit): {np.sqrt(full_mse):.4f}")

# Model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1 + default_rate_lag2
features_full2 = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1', 'default_rate_lag2']
X_full2 = X[features_full2]

full2_errors = []
for train_idx, test_idx in loo.split(X_full2):
    X_train, X_test = X_full2.iloc[train_idx], X_full2.iloc[test_idx]
    y_train = y_logit[train_idx]
    
    X_train_c = sm.add_constant(X_train)
    X_test_c = sm.add_constant(X_test)
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    full2_errors.append((y_logit[test_idx] - pred) ** 2)

full2_mse = np.mean(full2_errors)
print(f"Full2 model LOO MSE (logit): {full2_mse:.4f}")
print(f"Full2 model LOO RMSE (logit): {np.sqrt(full2_mse):.4f}")

# Also try with raw default rate
print("\n--- Raw default rate models ---")

# Simple raw
simple_raw_errors = []
for train_idx, test_idx in loo.split(X_simple):
    X_train, X_test = X_simple.iloc[train_idx], X_simple.iloc[test_idx]
    y_train = y[train_idx]
    
    X_train_c = sm.add_constant(X_train)
    X_test_c = sm.add_constant(X_test)
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    simple_raw_errors.append((y[test_idx] - pred) ** 2)

simple_raw_mse = np.mean(simple_raw_errors)
print(f"Simple raw LOO MSE: {simple_raw_mse:.6f}")
print(f"Simple raw LOO RMSE: {np.sqrt(simple_raw_mse):.6f}")

# Medium raw
med_raw_errors = []
for train_idx, test_idx in loo.split(X_med):
    X_train, X_test = X_med.iloc[train_idx], X_med.iloc[test_idx]
    y_train = y[train_idx]
    
    X_train_c = sm.add_constant(X_train)
    X_test_c = sm.add_constant(X_test)
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    med_raw_errors.append((y[test_idx] - pred) ** 2)

med_raw_mse = np.mean(med_raw_errors)
print(f"Medium raw LOO MSE: {med_raw_mse:.6f}")
print(f"Medium raw LOO RMSE: {np.sqrt(med_raw_mse):.6f}")

# Full raw
full_raw_errors = []
for train_idx, test_idx in loo.split(X_full):
    X_train, X_test = X_full.iloc[train_idx], X_full.iloc[test_idx]
    y_train = y[train_idx]
    
    X_train_c = sm.add_constant(X_train)
    X_test_c = sm.add_constant(X_test)
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    full_raw_errors.append((y[test_idx] - pred) ** 2)

full_raw_mse = np.mean(full_raw_errors)
print(f"Full raw LOO MSE: {full_raw_mse:.6f}")
print(f"Full raw LOO RMSE: {np.sqrt(full_raw_mse):.6f}")

# Full2 raw
full2_raw_errors = []
for train_idx, test_idx in loo.split(X_full2):
    X_train, X_test = X_full2.iloc[train_idx], X_full2.iloc[test_idx]
    y_train = y[train_idx]
    
    X_train_c = sm.add_constant(X_train)
    X_test_c = sm.add_constant(X_test)
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    full2_raw_errors.append((y[test_idx] - pred) ** 2)

full2_raw_mse = np.mean(full2_raw_errors)
print(f"Full2 raw LOO MSE: {full2_raw_mse:.6f}")
print(f"Full2 raw LOO RMSE: {np.sqrt(full2_raw_mse):.6f}")

```

## [35] tool

Traceback (most recent call last):
  File "<stdin>", line 66, in <module>
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 1174, in predict
    predict_results = self.model.predict(self.params, exog, *args,
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 409, in predict
    return np.dot(exog, params)
           ^^^^^^^^^^^^^^^^^^^^
ValueError: shapes (1,2) and (3,) not aligned: 2 (dim 1) != 3 (dim 0)



## [36] assistant

**[reasoning]**

> The issue is that when we drop a row for LOO, the remaining rows still have the same index, but the constant column is being added correctly. Let me debug this.
> 
> Actually, the issue might be that when we use `sm.add_constant(X_test)` where X_test is a single row DataFrame, it creates a 2-column constant + feature, but the model was fit with 3 parameters (const + 2 features). Wait, that should be fine...
> 
> Let me check - the issue might be that X_test is a DataFrame with index, and when we do sm.add_constant, it might not work correctly. Let me use numpy arrays instead.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()

# Use LOO CV with numpy arrays
loo = LeaveOneOut()

# Model: bbb_spread + unemployment (simple)
features_simple = ['bbb_spread', 'unemployment']
X_simple = X[features_simple].values
y_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))

simple_errors = []
for train_idx, test_idx in loo.split(X_simple):
    X_train, X_test = X_simple[train_idx], X_simple[test_idx]
    y_train = y_logit[train_idx]
    
    X_train_c = np.column_stack([np.ones(len(X_train)), X_train])
    X_test_c = np.column_stack([np.ones(len(X_test)), X_test])
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    simple_errors.append((y_logit[test_idx] - pred) ** 2)

simple_mse = np.mean(simple_errors)
print(f"Simple model (bbb_spread, unemployment) LOO MSE (logit): {simple_mse:.4f}")
print(f"Simple model LOO RMSE (logit): {np.sqrt(simple_mse):.4f}")

# Model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth
features_med = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth']
X_med = X[features_med].values

med_errors = []
for train_idx, test_idx in loo.split(X_med):
    X_train, X_test = X_med[train_idx], X_med[test_idx]
    y_train = y_logit[train_idx]
    
    X_train_c = np.column_stack([np.ones(len(X_train)), X_train])
    X_test_c = np.column_stack([np.ones(len(X_test)), X_test])
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    med_errors.append((y_logit[test_idx] - pred) ** 2)

med_mse = np.mean(med_errors)
print(f"Medium model LOO MSE (logit): {med_mse:.4f}")
print(f"Medium model LOO RMSE (logit): {np.sqrt(med_mse):.4f}")

# Model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1
features_full = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1']
X_full = X[features_full].values

full_errors = []
for train_idx, test_idx in loo.split(X_full):
    X_train, X_test = X_full[train_idx], X_full[test_idx]
    y_train = y_logit[train_idx]
    
    X_train_c = np.column_stack([np.ones(len(X_train)), X_train])
    X_test_c = np.column_stack([np.ones(len(X_test)), X_test])
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    full_errors.append((y_logit[test_idx] - pred) ** 2)

full_mse = np.mean(full_errors)
print(f"Full model LOO MSE (logit): {full_mse:.4f}")
print(f"Full model LOO RMSE (logit): {np.sqrt(full_mse):.4f}")

# Model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth + default_rate_lag1 + default_rate_lag2
features_full2 = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth', 'default_rate_lag1', 'default_rate_lag2']
X_full2 = X[features_full2].values

full2_errors = []
for train_idx, test_idx in loo.split(X_full2):
    X_train, X_test = X_full2[train_idx], X_full2[test_idx]
    y_train = y_logit[train_idx]
    
    X_train_c = np.column_stack([np.ones(len(X_train)), X_train])
    X_test_c = np.column_stack([np.ones(len(X_test)), X_test])
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    full2_errors.append((y_logit[test_idx] - pred) ** 2)

full2_mse = np.mean(full2_errors)
print(f"Full2 model LOO MSE (logit): {full2_mse:.4f}")
print(f"Full2 model LOO RMSE (logit): {np.sqrt(full2_mse):.4f}")

# Also try with raw default rate
print("\n--- Raw default rate models ---")

# Simple raw
simple_raw_errors = []
for train_idx, test_idx in loo.split(X_simple):
    X_train, X_test = X_simple[train_idx], X_simple[test_idx]
    y_train = y[train_idx]
    
    X_train_c = np.column_stack([np.ones(len(X_train)), X_train])
    X_test_c = np.column_stack([np.ones(len(X_test)), X_test])
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    simple_raw_errors.append((y[test_idx] - pred) ** 2)

simple_raw_mse = np.mean(simple_raw_errors)
print(f"Simple raw LOO MSE: {simple_raw_mse:.6f}")
print(f"Simple raw LOO RMSE: {np.sqrt(simple_raw_mse):.6f}")

# Medium raw
med_raw_errors = []
for train_idx, test_idx in loo.split(X_med):
    X_train, X_test = X_med[train_idx], X_med[test_idx]
    y_train = y[train_idx]
    
    X_train_c = np.column_stack([np.ones(len(X_train)), X_train])
    X_test_c = np.column_stack([np.ones(len(X_test)), X_test])
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    med_raw_errors.append((y[test_idx] - pred) ** 2)

med_raw_mse = np.mean(med_raw_errors)
print(f"Medium raw LOO MSE: {med_raw_mse:.6f}")
print(f"Medium raw LOO RMSE: {np.sqrt(med_raw_mse):.6f}")

# Full raw
full_raw_errors = []
for train_idx, test_idx in loo.split(X_full):
    X_train, X_test = X_full[train_idx], X_full[test_idx]
    y_train = y[train_idx]
    
    X_train_c = np.column_stack([np.ones(len(X_train)), X_train])
    X_test_c = np.column_stack([np.ones(len(X_test)), X_test])
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    full_raw_errors.append((y[test_idx] - pred) ** 2)

full_raw_mse = np.mean(full_raw_errors)
print(f"Full raw LOO MSE: {full_raw_mse:.6f}")
print(f"Full raw LOO RMSE: {np.sqrt(full_raw_mse):.6f}")

# Full2 raw
full2_raw_errors = []
for train_idx, test_idx in loo.split(X_full2):
    X_train, X_test = X_full2[train_idx], X_full2[test_idx]
    y_train = y[train_idx]
    
    X_train_c = np.column_stack([np.ones(len(X_train)), X_train])
    X_test_c = np.column_stack([np.ones(len(X_test)), X_test])
    
    model = sm.OLS(y_train, X_train_c).fit()
    pred = model.predict(X_test_c)
    full2_raw_errors.append((y[test_idx] - pred) ** 2)

full2_raw_mse = np.mean(full2_raw_errors)
print(f"Full2 raw LOO MSE: {full2_raw_mse:.6f}")
print(f"Full2 raw LOO RMSE: {np.sqrt(full2_raw_mse):.6f}")

```

## [37] tool

Simple model (bbb_spread, unemployment) LOO MSE (logit): 0.1243
Simple model LOO RMSE (logit): 0.3526
Medium model LOO MSE (logit): 0.1267
Medium model LOO RMSE (logit): 0.3559
Full model LOO MSE (logit): 0.1270
Full model LOO RMSE (logit): 0.3563
Full2 model LOO MSE (logit): 0.1328
Full2 model LOO RMSE (logit): 0.3644

--- Raw default rate models ---
Simple raw LOO MSE: 0.000120
Simple raw LOO RMSE: 0.010970
Medium raw LOO MSE: 0.000124
Medium raw LOO RMSE: 0.011119
Full raw LOO MSE: 0.000126
Full raw LOO RMSE: 0.011231
Full2 raw LOO MSE: 0.000135
Full2 raw LOO RMSE: 0.011629


## [38] assistant

**[reasoning]**

> The LOO CV results show that the simple model (bbb_spread, unemployment) is actually the best performing. The logit-transformed models have similar performance, and the raw models are comparable. Let me now build the final model and generate predictions.
> 
> The key insight is:
> 1. bbb_spread is the strongest predictor (correlation 0.70 with default_rate)
> 2. unemployment is the second strongest (correlation 0.20)
> 3. vix has moderate correlation (0.47) but isn't significant in the logit model
> 
> For the scenario, the bbb_spread goes up to 3.79 (beyond training max of 3.57) and unemployment goes to 9.23 (beyond training max of 8.04). This is extrapolation.
> 
> Let me use the simple raw model (bbb_spread + unemployment) as it has the best LOO CV performance and is most robust to extrapolation. I'll also try the logit version.
> 
> For prediction intervals, I need to account for:
> 1. Model uncertainty (parameter uncertainty)
> 2. Residual uncertainty (noise)
> 3. Extrapolation uncertainty (since scenario is beyond training range)
> 
> Let me build the final model and generate predictions.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

# Use the best model: bbb_spread + unemployment (raw)
features = ['bbb_spread', 'unemployment']
X_train = X[features].values
X_train_c = np.column_stack([np.ones(len(X_train)), X_train])

# Fit model
model = sm.OLS(y, X_train_c).fit()
print("Final model summary:")
print(model.summary().as_csv())

# Get residuals
residuals = model.resid
residual_std = residuals.std()
print(f"\nResidual std: {residual_std:.6f}")

# Check residuals for patterns
print(f"Residual mean: {residuals.mean():.6f}")
print(f"Residual min: {residuals.min():.6f}")
print(f"Residual max: {residuals.max():.6f}")

# Check for heteroskedasticity - plot residual vs predicted
y_pred_train = model.predict(X_train_c)
print(f"\nPredicted range: [{y_pred_train.min():.6f}, {y_pred_train.max():.6f}]")
print(f"Actual range: [{y.min():.6f}, {y.max():.6f}]")

# Check if residuals are heteroskedastic
from scipy.stats import spearmanr
corr, pval = spearmanr(y_pred_train, np.abs(residuals))
print(f"\nSpearman correlation (predicted vs |residual|): {corr:.4f}, p={pval:.4f}")

# Now prepare scenario features
# For scenario, we need to compute the same features
# bbb_spread and unemployment are directly available
scenario_features = scenario[['bbb_spread', 'unemployment']].values
scenario_c = np.column_stack([np.ones(len(scenario_features)), scenario_features])

# Generate predictions
y_pred = model.predict(scenario_c)
print(f"\nScenario predictions (raw):")
for i, (q, pred) in enumerate(zip(scenario['quarter'], y_pred)):
    print(f"  Quarter {q}: {pred:.6f}")

# Generate 95% prediction intervals
# For each prediction, the interval is: y_pred +/- t * sqrt(MSE * (1 + x' (X'X)^-1 x))
# But for extrapolation, we should widen the interval

# Get the covariance matrix of coefficients
cov_matrix = model.cov_params()
t_stat = stats.t.ppf(0.975, model.df_resid)

print(f"\nT-statistic (95%): {t_stat:.4f}")
print(f"Residual std: {residual_std:.6f}")

# For each scenario point, compute prediction interval
predictions = []
for i in range(len(scenario)):
    x = scenario_c[i]
    # Standard error of prediction
    se_pred = np.sqrt(residual_std**2 * (1 + x @ cov_matrix @ x))
    
    # For extrapolation, widen the interval
    # Check how far the scenario is from training data
    bbb_spread_val = scenario['bbb_spread'].iloc[i]
    unemployment_val = scenario['unemployment'].iloc[i]
    
    bbb_train_min, bbb_train_max = X['bbb_spread'].min(), X['bbb_spread'].max()
    unemp_train_min, unemp_train_max = X['unemployment'].min(), X['unemployment'].max()
    
    # Compute extrapolation factor
    bbb_extrap = max(0, bbb_spread_val - bbb_train_max) / (bbb_train_max - bbb_train_min) if bbb_train_max > bbb_train_min else 0
    unemp_extrap = max(0, unemployment_val - unemp_train_max) / (unemp_train_max - unemp_train_min) if unemp_train_max > unemp_train_min else 0
    
    # Extrapolation factor: 1 + some penalty for being outside range
    # Use a moderate penalty
    extrapolation_penalty = 1 + 0.5 * (bbb_extrap + unemp_extrap)
    
    se_pred_wide = se_pred * extrapolation_penalty
    
    y_lower = y_pred[i] - t_stat * se_pred_wide
    y_upper = y_pred[i] + t_stat * se_pred_wide
    
    # Clip to [0, 1]
    y_lower = max(0, y_lower)
    y_upper = min(1, y_upper)
    
    predictions.append({
        'quarter': scenario['quarter'].iloc[i],
        'y_pred': y_pred[i],
        'y_lower': y_lower,
        'y_upper': y_upper,
        'se_pred': se_pred,
        'se_pred_wide': se_pred_wide,
        'extrapolation_penalty': extrapolation_penalty
    })
    
    print(f"\nQuarter {scenario['quarter'].iloc[i]}:")
    print(f"  bbb_spread: {bbb_spread_val:.4f} (train range: [{bbb_train_min:.2f}, {bbb_train_max:.2f}])")
    print(f"  unemployment: {unemployment_val:.4f} (train range: [{unemp_train_min:.2f}, {unemp_train_max:.2f}])")
    print(f"  y_pred: {y_pred[i]:.6f}")
    print(f"  se_pred: {se_pred:.6f}")
    print(f"  extrapolation_penalty: {extrapolation_penalty:.4f}")
    print(f"  y_lower: {y_lower:.6f}")
    print(f"  y_upper: {y_upper:.6f}")

# Save predictions
pred_df = pd.DataFrame(predictions)
pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']].to_csv('predictions.csv', index=False)
print("\n\nSaved predictions.csv")
print(pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']])

```

## [39] tool

Final model summary:
                      OLS Regression Results                     
Dep. Variable:   ,y               ,  R-squared:         ,   0.516
Model:           ,OLS             ,  Adj. R-squared:    ,   0.504
Method:          ,Least Squares   ,  F-statistic:       ,   41.07
Date:            ,Tue, 27 Oct 2026,  Prob (F-statistic):,7.26e-13
Time:            ,14:40:01        ,  Log-Likelihood:    ,  250.63
No. Observations:,    80          ,  AIC:               ,  -495.3
Df Residuals:    ,    77          ,  BIC:               ,  -488.1
Df Model:        ,     2          ,                     ,        
Covariance Type: ,nonrobust       ,                     ,        
     ,   coef   , std err ,    t    ,P>|t| ,  [0.025 ,  0.975] 
const,   -0.0062,    0.007,   -0.935, 0.353,   -0.019,    0.007
x1   ,    0.0127,    0.001,    8.700, 0.000,    0.010,    0.016
x2   ,    0.0025,    0.001,    2.292, 0.025,    0.000,    0.005
Omnibus:      ,37.142,  Durbin-Watson:     ,   2.094
Prob(Omnibus):, 0.000,  Jarque-Bera (JB):  , 131.277
Skew:         , 1.389,  Prob(JB):          ,3.12e-29
Kurtosis:     , 8.627,  Cond. No.          ,    33.5

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.

Residual std: 0.010547
Residual mean: -0.000000
Residual min: -0.021541
Residual max: 0.051594

Predicted range: [0.011024, 0.053286]
Actual range: [0.003167, 0.093801]

Spearman correlation (predicted vs |residual|): 0.3864, p=0.0004

Scenario predictions (raw):
  Quarter 81: 0.040167
  Quarter 82: 0.043111
  Quarter 83: 0.046093
  Quarter 84: 0.049115
  Quarter 85: 0.052178
  Quarter 86: 0.055285
  Quarter 87: 0.058438
  Quarter 88: 0.061640
  Quarter 89: 0.064891

T-statistic (95%): 1.9913
Residual std: 0.010547

Quarter 81:
  bbb_spread: 2.4174 (train range: [0.23, 3.57])
  unemployment: 6.2898 (train range: [3.07, 8.04])
  y_pred: 0.040167
  se_pred: 0.010547
  extrapolation_penalty: 1.0000
  y_lower: 0.019164
  y_upper: 0.061170

Quarter 82:
  bbb_spread: 2.5886 (train range: [0.23, 3.57])
  unemployment: 6.5991 (train range: [3.07, 8.04])
  y_pred: 0.043111
  se_pred: 0.010547
  extrapolation_penalty: 1.0000
  y_lower: 0.022108
  y_upper: 0.064114

Quarter 83:
  bbb_spread: 2.7598 (train range: [0.23, 3.57])
  unemployment: 6.9235 (train range: [3.07, 8.04])
  y_pred: 0.046093
  se_pred: 0.010547
  extrapolation_penalty: 1.0000
  y_lower: 0.025090
  y_upper: 0.067095

Quarter 84:
  bbb_spread: 2.9311 (train range: [0.23, 3.57])
  unemployment: 7.2640 (train range: [3.07, 8.04])
  y_pred: 0.049115
  se_pred: 0.010547
  extrapolation_penalty: 1.0000
  y_lower: 0.028113
  y_upper: 0.070118

Quarter 85:
  bbb_spread: 3.1023 (train range: [0.23, 3.57])
  unemployment: 7.6211 (train range: [3.07, 8.04])
  y_pred: 0.052178
  se_pred: 0.010547
  extrapolation_penalty: 1.0000
  y_lower: 0.031176
  y_upper: 0.073181

Quarter 86:
  bbb_spread: 3.2735 (train range: [0.23, 3.57])
  unemployment: 7.9958 (train range: [3.07, 8.04])
  y_pred: 0.055285
  se_pred: 0.010548
  extrapolation_penalty: 1.0000
  y_lower: 0.034282
  y_upper: 0.076288

Quarter 87:
  bbb_spread: 3.4447 (train range: [0.23, 3.57])
  unemployment: 8.3890 (train range: [3.07, 8.04])
  y_pred: 0.058438
  se_pred: 0.010548
  extrapolation_penalty: 1.0352
  y_lower: 0.036695
  y_upper: 0.080180

Quarter 88:
  bbb_spread: 3.6160 (train range: [0.23, 3.57])
  unemployment: 8.8015 (train range: [3.07, 8.04])
  y_pred: 0.061640
  se_pred: 0.010548
  extrapolation_penalty: 1.0837
  y_lower: 0.038880
  y_upper: 0.084400

Quarter 89:
  bbb_spread: 3.7872 (train range: [0.23, 3.57])
  unemployment: 9.2342 (train range: [3.07, 8.04])
  y_pred: 0.064891
  se_pred: 0.010548
  extrapolation_penalty: 1.1529
  y_lower: 0.040677
  y_upper: 0.089105


Saved predictions.csv
   quarter    y_pred   y_lower   y_upper
0       81  0.040167  0.019164  0.061170
1       82  0.043111  0.022108  0.064114
2       83  0.046093  0.025090  0.067095
3       84  0.049115  0.028113  0.070118
4       85  0.052178  0.031176  0.073181
5       86  0.055285  0.034282  0.076288
6       87  0.058438  0.036695  0.080180
7       88  0.061640  0.038880  0.084400
8       89  0.064891  0.040677  0.089105


## [40] assistant

**[reasoning]**

> The simple model works but I should try to improve it. Let me think about what model would be best:
> 
> 1. The scenario pushes bbb_spread beyond the training range (up to 3.79 vs max 3.57)
> 2. The scenario pushes unemployment beyond the training range (up to 9.23 vs max 8.04)
> 3. The model should capture the relationship well
> 
> Let me try a more sophisticated approach:
> - Use the logit-transformed model with bbb_spread as the main driver
> - Add quadratic terms for better fit
> - Use a more robust extrapolation strategy
> 
> Actually, let me reconsider. The simple model (bbb_spread + unemployment) has good LOO CV performance. But I should try to improve the model and the prediction intervals.
> 
> Key issues:
> 1. The residuals are heteroskedastic (correlation between predicted and |residual|)
> 2. The scenario pushes beyond training ranges
> 3. Need better prediction intervals
> 
> Let me try a more comprehensive approach with:
> 1. Better feature engineering
> 2. Logit transform for bounded predictions
> 3. Better extrapolation handling
> 4. Bootstrap-based prediction intervals
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix
X = train_filled[macro_cols].copy()

# Add transformations
X['unemployment_sq'] = X['unemployment'] ** 2
X['bbb_spread_sq'] = X['bbb_spread'] ** 2
X['vix_sq'] = X['vix'] ** 2
X['gdp_growth'] = X['gdp'].diff().fillna(0)
X['unemployment_diff'] = X['unemployment'].diff().fillna(0)
X['bbb_spread_diff'] = X['bbb_spread'].diff().fillna(0)
X['vix_diff'] = X['vix'].diff().fillna(0)
X['gdp_lag1'] = X['gdp'].shift(1).bfill()
X['unemployment_lag1'] = X['unemployment'].shift(1).bfill()
X['bbb_spread_lag1'] = X['bbb_spread'].shift(1).bfill()
X['vix_lag1'] = X['vix'].shift(1).bfill()
X['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X.dropna().index
X = X.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

feature_names = X.columns.tolist()

# Let's try a comprehensive approach with multiple models and ensemble
# Use logit transform for bounded predictions

y_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))

# Key features
features = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth']
X_main = X[features].values

# Fit model on logit scale
X_main_c = np.column_stack([np.ones(len(X_main)), X_main])
model_logit = sm.OLS(y_logit, X_main_c).fit()

print("Logit model summary:")
print(model_logit.summary().as_csv())

# Convert predictions back to probability scale
y_pred_logit = model_logit.predict(X_main_c)
y_pred_prob = 1 / (1 + np.exp(-y_pred_logit))

print(f"\nPredicted probability range: [{y_pred_prob.min():.6f}, {y_pred_prob.max():.6f}]")
print(f"Actual range: [{y.min():.6f}, {y.max():.6f}]")

# Check residuals on probability scale
residuals_prob = y - y_pred_prob
residual_std_prob = residuals_prob.std()
print(f"\nResidual std (prob scale): {residual_std_prob:.6f}")

# Check residuals on logit scale
residuals_logit = model_logit.resid
residual_std_logit = residuals_logit.std()
print(f"Residual std (logit scale): {residual_std_logit:.6f}")

# Now let's try a different approach - use the logit model for prediction
# and compute prediction intervals using the logit residuals

# Get covariance matrix
cov_matrix = model_logit.cov_params()
t_stat = stats.t.ppf(0.975, model_logit.df_resid)

# Prepare scenario features
scenario_features = scenario[['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth']].values
scenario_c = np.column_stack([np.ones(len(scenario_features)), scenario_features])

# Generate logit predictions
y_logit_pred = model_logit.predict(scenario_c)
y_prob_pred = 1 / (1 + np.exp(-y_logit_pred))

print(f"\nScenario predictions (logit -> prob):")
for i, (q, pred) in enumerate(zip(scenario['quarter'], y_prob_pred)):
    print(f"  Quarter {q}: {pred:.6f}")

# Compute prediction intervals
# For extrapolation, we need to account for:
# 1. Model uncertainty (covariance of coefficients)
# 2. Residual variance
# 3. Extrapolation uncertainty

# Get training ranges
bbb_train_min, bbb_train_max = X['bbb_spread'].min(), X['bbb_spread'].max()
unemp_train_min, unemp_train_max = X['unemployment'].min(), X['unemployment'].max()

predictions = []
for i in range(len(scenario)):
    x = scenario_c[i]
    
    # Standard error of prediction (model + residual)
    se_pred = np.sqrt(residual_std_logit**2 * (1 + x @ cov_matrix @ x))
    
    # Extrapolation penalty
    bbb_val = scenario['bbb_spread'].iloc[i]
    unemp_val = scenario['unemployment'].iloc[i]
    
    bbb_range = bbb_train_max - bbb_train_min
    unemp_range = unemp_train_max - unemp_train_min
    
    # How far beyond training range?
    bbb_extrap = max(0, bbb_val - bbb_train_max) / bbb_range if bbb_range > 0 else 0
    unemp_extrap = max(0, unemp_val - unemp_train_max) / unemp_range if unemp_range > 0 else 0
    
    # Extrapolation factor - more aggressive for more extrapolation
    # Use a factor that grows with extrapolation distance
    extrapolation_factor = 1 + 2 * (bbb_extrap + unemp_extrap)
    
    se_pred_wide = se_pred * extrapolation_factor
    
    # Prediction interval on logit scale
    y_logit_lower = y_logit_pred[i] - t_stat * se_pred_wide
    y_logit_upper = y_logit_pred[i] + t_stat * se_pred_wide
    
    # Convert to probability scale
    y_lower = 1 / (1 + np.exp(-y_logit_lower))
    y_upper = 1 / (1 + np.exp(-y_logit_upper))
    
    # Clip to [0, 1]
    y_lower = max(0, y_lower)
    y_upper = min(1, y_upper)
    
    predictions.append({
        'quarter': scenario['quarter'].iloc[i],
        'y_pred': y_prob_pred[i],
        'y_lower': y_lower,
        'y_upper': y_upper,
        'se_pred': se_pred,
        'se_pred_wide': se_pred_wide,
        'extrapolation_factor': extrapolation_factor,
        'bbb_extrap': bbb_extrap,
        'unemp_extrap': unemp_extrap
    })
    
    print(f"\nQuarter {scenario['quarter'].iloc[i]}:")
    print(f"  bbb_spread: {bbb_val:.4f} (train: [{bbb_train_min:.2f}, {bbb_train_max:.2f}])")
    print(f"  unemployment: {unemp_val:.4f} (train: [{unemp_train_min:.2f}, {unemp_train_max:.2f}])")
    print(f"  y_pred: {y_prob_pred[i]:.6f}")
    print(f"  se_pred: {se_pred:.6f}")
    print(f"  extrapolation_factor: {extrapolation_factor:.4f}")
    print(f"  y_lower: {y_lower:.6f}")
    print(f"  y_upper: {y_upper:.6f}")

# Save predictions
pred_df = pd.DataFrame(predictions)
pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']].to_csv('predictions.csv', index=False)
print("\n\nSaved predictions.csv")
print(pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']])

```

## [41] tool

Traceback (most recent call last):
  File "<stdin>", line 90, in <module>
  File "/usr/local/lib/python3.12/site-packages/pandas/core/frame.py", line 4384, in __getitem__
    indexer = self.columns._get_indexer_strict(key, "columns")[1]
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6302, in _get_indexer_strict
    self._raise_if_missing(keyarr, indexer, axis_name)
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6355, in _raise_if_missing
    raise KeyError(f"{not_found} not in index")
KeyError: "['bbb_spread_sq', 'unemployment_sq', 'gdp_growth'] not in index"

Logit model summary:
                      OLS Regression Results                     
Dep. Variable:   ,y               ,  R-squared:         ,   0.592
Model:           ,OLS             ,  Adj. R-squared:    ,   0.565
Method:          ,Least Squares   ,  F-statistic:       ,   21.51
Date:            ,Tue, 27 Oct 2026,  Prob (F-statistic):,3.15e-13
Time:            ,14:40:46        ,  Log-Likelihood:    , -23.284
No. Observations:,    80          ,  AIC:               ,   58.57
Df Residuals:    ,    74          ,  BIC:               ,   72.86
Df Model:        ,     5          ,                     ,        
Covariance Type: ,nonrobust       ,                     ,        
     ,   coef   , std err ,    t    ,P>|t| ,  [0.025 ,  0.975] 
const,   -4.1732,    0.787,   -5.302, 0.000,   -5.742,   -2.605
x1   ,    0.6393,    0.196,    3.259, 0.002,    0.248,    1.030
x2   ,   -0.1344,    0.277,   -0.486, 0.629,   -0.686,    0.417
x3   ,   -0.0579,    0.051,   -1.128, 0.263,   -0.160,    0.044
x4   ,    0.0153,    0.025,    0.610, 0.544,   -0.035,    0.065
x5   ,   -0.0483,    0.024,   -2.026, 0.046,   -0.096,   -0.001
Omnibus:      , 7.457,  Durbin-Watson:     ,   1.705
Prob(Omnibus):, 0.024,  Jarque-Bera (JB):  ,   9.825
Skew:         ,-0.374,  Prob(JB):          , 0.00735
Kurtosis:     , 4.545,  Cond. No.          ,    762.

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.

Predicted probability range: [0.010335, 0.061197]
Actual range: [0.003167, 0.093801]

Residual std (prob scale): 0.010238
Residual std (logit scale): 0.323717


## [42] assistant

**[reasoning]**

> The issue is that the scenario dataframe doesn't have the computed features. I need to compute them from the raw scenario data. Let me fix this and also refine the model.
> 
> Let me write a complete, self-contained script that:
> 1. Loads data
> 2. Creates features for training
> 3. Fits the best model
> 4. Computes features for scenario
> 5. Generates predictions with intervals
> 6. Saves to predictions.csv
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix for training
X_train = train_filled[macro_cols].copy()

# Add transformations
X_train['unemployment_sq'] = X_train['unemployment'] ** 2
X_train['bbb_spread_sq'] = X_train['bbb_spread'] ** 2
X_train['vix_sq'] = X_train['vix'] ** 2
X_train['gdp_growth'] = X_train['gdp'].diff().fillna(0)
X_train['unemployment_diff'] = X_train['unemployment'].diff().fillna(0)
X_train['bbb_spread_diff'] = X_train['bbb_spread'].diff().fillna(0)
X_train['vix_diff'] = X_train['vix'].diff().fillna(0)
X_train['gdp_lag1'] = X_train['gdp'].shift(1).bfill()
X_train['unemployment_lag1'] = X_train['unemployment'].shift(1).bfill()
X_train['bbb_spread_lag1'] = X_train['bbb_spread'].shift(1).bfill()
X_train['vix_lag1'] = X_train['vix'].shift(1).bfill()
X_train['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X_train['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X_train['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X_train.dropna().index
X_train = X_train.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

# Use logit transform
y_logit = np.log(np.clip(y, 0.001, 0.999) / (1 - np.clip(y, 0.001, 0.999)))

# Best model: bbb_spread + unemployment + bbb_spread_sq + unemployment_sq + gdp_growth
features = ['bbb_spread', 'unemployment', 'bbb_spread_sq', 'unemployment_sq', 'gdp_growth']
X_main = X_train[features].values
X_main_c = np.column_stack([np.ones(len(X_main)), X_main])

# Fit model
model = sm.OLS(y_logit, X_main_c).fit()

print("Final model summary:")
print(model.summary().as_csv())

# Get residuals
residuals = model.resid
residual_std = residuals.std()
print(f"\nResidual std (logit): {residual_std:.6f}")

# Get covariance matrix
cov_matrix = model.cov_params()
t_stat = stats.t.ppf(0.975, model.df_resid)

# Get training ranges for extrapolation detection
bbb_train_min, bbb_train_max = X_train['bbb_spread'].min(), X_train['bbb_spread'].max()
unemp_train_min, unemp_train_max = X_train['unemployment'].min(), X_train['unemployment'].max()
gdp_train_min, gdp_train_max = X_train['gdp'].min(), X_train['gdp'].max()

print(f"\nTraining ranges:")
print(f"  bbb_spread: [{bbb_train_min:.2f}, {bbb_train_max:.2f}]")
print(f"  unemployment: [{unemp_train_min:.2f}, {unemp_train_max:.2f}]")
print(f"  gdp: [{gdp_train_min:.2f}, {gdp_train_max:.2f}]")

# Prepare scenario features
# Compute the same transformations for scenario
scenario_features = scenario.copy()
scenario_features['bbb_spread_sq'] = scenario_features['bbb_spread'] ** 2
scenario_features['unemployment_sq'] = scenario_features['unemployment'] ** 2
scenario_features['gdp_growth'] = scenario_features['gdp'].diff()
# For the first scenario quarter, gdp_growth is NaN since we don't have previous quarter
# Use the last training gdp_growth or 0
scenario_features['gdp_growth'] = scenario_features['gdp_growth'].fillna(0)

X_scenario = scenario_features[features].values
X_scenario_c = np.column_stack([np.ones(len(X_scenario)), X_scenario])

# Generate logit predictions
y_logit_pred = model.predict(X_scenario_c)
y_prob_pred = 1 / (1 + np.exp(-y_logit_pred))

print(f"\nScenario predictions (logit -> prob):")
for i, (q, pred) in enumerate(zip(scenario['quarter'], y_prob_pred)):
    print(f"  Quarter {q}: {pred:.6f}")

# Compute prediction intervals
predictions = []
for i in range(len(scenario)):
    x = X_scenario_c[i]
    
    # Standard error of prediction (model + residual)
    se_pred = np.sqrt(residual_std**2 * (1 + x @ cov_matrix @ x))
    
    # Extrapolation penalty
    bbb_val = scenario['bbb_spread'].iloc[i]
    unemp_val = scenario['unemployment'].iloc[i]
    gdp_val = scenario['gdp'].iloc[i]
    
    bbb_range = bbb_train_max - bbb_train_min
    unemp_range = unemp_train_max - unemp_train_min
    gdp_range = gdp_train_max - gdp_train_min
    
    # How far beyond training range?
    bbb_extrap = max(0, bbb_val - bbb_train_max) / bbb_range if bbb_range > 0 else 0
    unemp_extrap = max(0, unemp_val - unemp_train_max) / unemp_range if unemp_range > 0 else 0
    gdp_extrap = max(0, gdp_train_min - gdp_val) / gdp_range if gdp_range > 0 else 0
    
    # Extrapolation factor - more aggressive for more extrapolation
    extrapolation_factor = 1 + 2 * (bbb_extrap + unemp_extrap + gdp_extrap)
    
    se_pred_wide = se_pred * extrapolation_factor
    
    # Prediction interval on logit scale
    y_logit_lower = y_logit_pred[i] - t_stat * se_pred_wide
    y_logit_upper = y_logit_pred[i] + t_stat * se_pred_wide
    
    # Convert to probability scale
    y_lower = 1 / (1 + np.exp(-y_logit_lower))
    y_upper = 1 / (1 + np.exp(-y_logit_upper))
    
    # Clip to [0, 1]
    y_lower = max(0, y_lower)
    y_upper = min(1, y_upper)
    
    predictions.append({
        'quarter': scenario['quarter'].iloc[i],
        'y_pred': y_prob_pred[i],
        'y_lower': y_lower,
        'y_upper': y_upper,
    })
    
    print(f"\nQuarter {scenario['quarter'].iloc[i]}:")
    print(f"  bbb_spread: {bbb_val:.4f} (train: [{bbb_train_min:.2f}, {bbb_train_max:.2f}])")
    print(f"  unemployment: {unemp_val:.4f} (train: [{unemp_train_min:.2f}, {unemp_train_max:.2f}])")
    print(f"  gdp: {gdp_val:.4f} (train: [{gdp_train_min:.2f}, {gdp_train_max:.2f}])")
    print(f"  bbb_extrap: {bbb_extrap:.4f}, unemp_extrap: {unemp_extrap:.4f}, gdp_extrap: {gdp_extrap:.4f}")
    print(f"  extrapolation_factor: {extrapolation_factor:.4f}")
    print(f"  y_pred: {y_prob_pred[i]:.6f}")
    print(f"  y_lower: {y_lower:.6f}")
    print(f"  y_upper: {y_upper:.6f}")

# Save predictions
pred_df = pd.DataFrame(predictions)
pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']].to_csv('predictions.csv', index=False)
print("\n\nSaved predictions.csv")
print(pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']])

# Verify
print(f"\nNumber of rows: {len(pred_df)}")
print(f"Columns: {pred_df.columns.tolist()}")

```

## [43] tool

Final model summary:
                      OLS Regression Results                     
Dep. Variable:   ,y               ,  R-squared:         ,   0.592
Model:           ,OLS             ,  Adj. R-squared:    ,   0.565
Method:          ,Least Squares   ,  F-statistic:       ,   21.51
Date:            ,Tue, 27 Oct 2026,  Prob (F-statistic):,3.15e-13
Time:            ,14:41:31        ,  Log-Likelihood:    , -23.284
No. Observations:,    80          ,  AIC:               ,   58.57
Df Residuals:    ,    74          ,  BIC:               ,   72.86
Df Model:        ,     5          ,                     ,        
Covariance Type: ,nonrobust       ,                     ,        
     ,   coef   , std err ,    t    ,P>|t| ,  [0.025 ,  0.975] 
const,   -4.1732,    0.787,   -5.302, 0.000,   -5.742,   -2.605
x1   ,    0.6393,    0.196,    3.259, 0.002,    0.248,    1.030
x2   ,   -0.1344,    0.277,   -0.486, 0.629,   -0.686,    0.417
x3   ,   -0.0579,    0.051,   -1.128, 0.263,   -0.160,    0.044
x4   ,    0.0153,    0.025,    0.610, 0.544,   -0.035,    0.065
x5   ,   -0.0483,    0.024,   -2.026, 0.046,   -0.096,   -0.001
Omnibus:      , 7.457,  Durbin-Watson:     ,   1.705
Prob(Omnibus):, 0.024,  Jarque-Bera (JB):  ,   9.825
Skew:         ,-0.374,  Prob(JB):          , 0.00735
Kurtosis:     , 4.545,  Cond. No.          ,    762.

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.

Residual std (logit): 0.323717

Training ranges:
  bbb_spread: [0.23, 3.57]
  unemployment: [3.07, 8.04]
  gdp: [106.78, 217.36]

Scenario predictions (logit -> prob):
  Quarter 81: 0.038865
  Quarter 82: 0.049640
  Quarter 83: 0.053387
  Quarter 84: 0.057469
  Quarter 85: 0.061947
  Quarter 86: 0.066902
  Quarter 87: 0.072437
  Quarter 88: 0.078680
  Quarter 89: 0.085785

Quarter 81:
  bbb_spread: 2.4174 (train: [0.23, 3.57])
  unemployment: 6.2898 (train: [3.07, 8.04])
  gdp: 213.6347 (train: [106.78, 217.36])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000, gdp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.038865
  y_lower: 0.020750
  y_upper: 0.071640

Quarter 82:
  bbb_spread: 2.5886 (train: [0.23, 3.57])
  unemployment: 6.5991 (train: [3.07, 8.04])
  gdp: 209.9690 (train: [106.78, 217.36])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000, gdp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.049640
  y_lower: 0.026565
  y_upper: 0.090888

Quarter 83:
  bbb_spread: 2.7598 (train: [0.23, 3.57])
  unemployment: 6.9235 (train: [3.07, 8.04])
  gdp: 206.3662 (train: [106.78, 217.36])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000, gdp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.053387
  y_lower: 0.028621
  y_upper: 0.097433

Quarter 84:
  bbb_spread: 2.9311 (train: [0.23, 3.57])
  unemployment: 7.2640 (train: [3.07, 8.04])
  gdp: 202.8252 (train: [106.78, 217.36])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000, gdp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.057469
  y_lower: 0.030848
  y_upper: 0.104583

Quarter 85:
  bbb_spread: 3.1023 (train: [0.23, 3.57])
  unemployment: 7.6211 (train: [3.07, 8.04])
  gdp: 199.3449 (train: [106.78, 217.36])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000, gdp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.061947
  y_lower: 0.033262
  y_upper: 0.112489

Quarter 86:
  bbb_spread: 3.2735 (train: [0.23, 3.57])
  unemployment: 7.9958 (train: [3.07, 8.04])
  gdp: 195.9244 (train: [106.78, 217.36])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000, gdp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.066902
  y_lower: 0.035879
  y_upper: 0.121372

Quarter 87:
  bbb_spread: 3.4447 (train: [0.23, 3.57])
  unemployment: 8.3890 (train: [3.07, 8.04])
  gdp: 192.5626 (train: [106.78, 217.36])
  bbb_extrap: 0.0000, unemp_extrap: 0.0704, gdp_extrap: 0.0000
  extrapolation_factor: 1.1409
  y_pred: 0.072437
  y_lower: 0.035382
  y_upper: 0.142563

Quarter 88:
  bbb_spread: 3.6160 (train: [0.23, 3.57])
  unemployment: 8.8015 (train: [3.07, 8.04])
  gdp: 189.2584 (train: [106.78, 217.36])
  bbb_extrap: 0.0139, unemp_extrap: 0.1535, gdp_extrap: 0.0000
  extrapolation_factor: 1.3347
  y_pred: 0.078680
  y_lower: 0.033616
  y_upper: 0.173319

Quarter 89:
  bbb_spread: 3.7872 (train: [0.23, 3.57])
  unemployment: 9.2342 (train: [3.07, 8.04])
  gdp: 186.0110 (train: [106.78, 217.36])
  bbb_extrap: 0.0652, unemp_extrap: 0.2406, gdp_extrap: 0.0000
  extrapolation_factor: 1.6116
  y_pred: 0.085785
  y_lower: 0.029988
  y_upper: 0.221675


Saved predictions.csv
   quarter    y_pred   y_lower   y_upper
0       81  0.038865  0.020750  0.071640
1       82  0.049640  0.026565  0.090888
2       83  0.053387  0.028621  0.097433
3       84  0.057469  0.030848  0.104583
4       85  0.061947  0.033262  0.112489
5       86  0.066902  0.035879  0.121372
6       87  0.072437  0.035382  0.142563
7       88  0.078680  0.033616  0.173319
8       89  0.085785  0.029988  0.221675

Number of rows: 9
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']


## [44] assistant

**[reasoning]**

> The predictions look reasonable. Let me verify the output file and make sure everything is correct. The model uses bbb_spread, unemployment, and their squared terms plus gdp_growth as features. The predictions show increasing default rates as the stress scenario worsens (higher unemployment, higher bbb_spread, lower GDP). The prediction intervals widen as we extrapolate further from the training data.
> 
> Let me verify the file is correct and complete.
> 





**tool call: bash**

```
cat predictions.csv
```

## [45] tool

quarter,y_pred,y_lower,y_upper
81,0.038865237692159035,0.02074950686715066,0.07164014516295618
82,0.049640339705440795,0.026564957481157038,0.0908884180207819
83,0.0533865831012561,0.028620648041380436,0.09743334834747547
84,0.05746880471319826,0.030848103605354827,0.10458310382772859
85,0.06194659875192873,0.033262359355972194,0.11248878682463158
86,0.06690212765033939,0.03587937886362076,0.12137161879703035
87,0.07243725586365722,0.03538237398000242,0.1425632828514046
88,0.07867986740327637,0.03361613618758494,0.17331892496834497
89,0.08578508730041631,0.02998801848133553,0.22167523228873612


## [46] assistant

**[reasoning]**

> The predictions look reasonable - default rates increase as the stress scenario worsens (higher unemployment, higher bbb_spread, lower GDP). The intervals widen as we extrapolate further.
> 
> However, I notice the lower bounds are getting quite low for later quarters, which seems odd. Let me reconsider the approach. The issue is that the logit transformation creates asymmetric intervals when mapped back to probability space. Also, the extrapolation penalty is making the upper bounds very wide.
> 
> Let me refine the model and make sure the predictions are sensible. I should also consider that the scenario is a stress scenario where default rates should be higher than normal, and the intervals should reflect genuine uncertainty.
> 
> Let me also try a different approach - use the raw default rate model (which gave better LOO CV) and compute intervals more carefully.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix for training
X_train = train_filled[macro_cols].copy()

# Add transformations
X_train['unemployment_sq'] = X_train['unemployment'] ** 2
X_train['bbb_spread_sq'] = X_train['bbb_spread'] ** 2
X_train['vix_sq'] = X_train['vix'] ** 2
X_train['gdp_growth'] = X_train['gdp'].diff().fillna(0)
X_train['unemployment_diff'] = X_train['unemployment'].diff().fillna(0)
X_train['bbb_spread_diff'] = X_train['bbb_spread'].diff().fillna(0)
X_train['vix_diff'] = X_train['vix'].diff().fillna(0)
X_train['gdp_lag1'] = X_train['gdp'].shift(1).bfill()
X_train['unemployment_lag1'] = X_train['unemployment'].shift(1).bfill()
X_train['bbb_spread_lag1'] = X_train['bbb_spread'].shift(1).bfill()
X_train['vix_lag1'] = X_train['vix'].shift(1).bfill()
X_train['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X_train['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X_train['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X_train.dropna().index
X_train = X_train.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

# Use the best model: bbb_spread + unemployment (raw)
# This had the best LOO CV performance
features = ['bbb_spread', 'unemployment']
X_main = X_train[features].values
X_main_c = np.column_stack([np.ones(len(X_main)), X_main])

# Fit model
model = sm.OLS(y, X_main_c).fit()

print("Final model summary:")
print(model.summary().as_csv())

# Get residuals
residuals = model.resid
residual_std = residuals.std()
print(f"\nResidual std: {residual_std:.6f}")

# Check residuals for patterns
y_pred_train = model.predict(X_main_c)
print(f"Predicted range: [{y_pred_train.min():.6f}, {y_pred_train.max():.6f}]")
print(f"Actual range: [{y.min():.6f}, {y.max():.6f}]")

# Check for heteroskedasticity
from scipy.stats import spearmanr
corr, pval = spearmanr(y_pred_train, np.abs(residuals))
print(f"Spearman correlation (predicted vs |residual|): {corr:.4f}, p={pval:.4f}")

# Get covariance matrix
cov_matrix = model.cov_params()
t_stat = stats.t.ppf(0.975, model.df_resid)

# Get training ranges for extrapolation detection
bbb_train_min, bbb_train_max = X_train['bbb_spread'].min(), X_train['bbb_spread'].max()
unemp_train_min, unemp_train_max = X_train['unemployment'].min(), X_train['unemployment'].max()

print(f"\nTraining ranges:")
print(f"  bbb_spread: [{bbb_train_min:.2f}, {bbb_train_max:.2f}]")
print(f"  unemployment: [{unemp_train_min:.2f}, {unemp_train_max:.2f}]")

# Prepare scenario features
scenario_features = scenario[['bbb_spread', 'unemployment']].values
scenario_c = np.column_stack([np.ones(len(scenario_features)), scenario_features])

# Generate predictions
y_pred = model.predict(scenario_c)

print(f"\nScenario predictions:")
for i, (q, pred) in enumerate(zip(scenario['quarter'], y_pred)):
    print(f"  Quarter {q}: {pred:.6f}")

# Compute prediction intervals
# Use a more robust approach:
# 1. Compute the standard prediction interval
# 2. Widen it for extrapolation
# 3. Also consider using the empirical distribution of residuals

# Get empirical residual quantiles
residual_sorted = np.sort(residuals)
emp_lower = np.percentile(residuals, 2.5)
emp_upper = np.percentile(residuals, 97.5)
print(f"\nEmpirical residual 2.5th percentile: {emp_lower:.6f}")
print(f"Empirical residual 97.5th percentile: {emp_upper:.6f}")

predictions = []
for i in range(len(scenario)):
    x = scenario_c[i]
    
    # Standard error of prediction
    se_pred = np.sqrt(residual_std**2 * (1 + x @ cov_matrix @ x))
    
    # Extrapolation penalty
    bbb_val = scenario['bbb_spread'].iloc[i]
    unemp_val = scenario['unemployment'].iloc[i]
    
    bbb_range = bbb_train_max - bbb_train_min
    unemp_range = unemp_train_max - unemp_train_min
    
    # How far beyond training range?
    bbb_extrap = max(0, bbb_val - bbb_train_max) / bbb_range if bbb_range > 0 else 0
    unemp_extrap = max(0, unemp_val - unemp_train_max) / unemp_range if unemp_range > 0 else 0
    
    # Extrapolation factor
    extrapolation_factor = 1 + 2 * (bbb_extrap + unemp_extrap)
    
    se_pred_wide = se_pred * extrapolation_factor
    
    # Prediction interval on raw scale
    y_lower = y_pred[i] - t_stat * se_pred_wide
    y_upper = y_pred[i] + t_stat * se_pred_wide
    
    # Clip to [0, 1]
    y_lower = max(0, y_lower)
    y_upper = min(1, y_upper)
    
    predictions.append({
        'quarter': scenario['quarter'].iloc[i],
        'y_pred': y_pred[i],
        'y_lower': y_lower,
        'y_upper': y_upper,
    })
    
    print(f"\nQuarter {scenario['quarter'].iloc[i]}:")
    print(f"  bbb_spread: {bbb_val:.4f} (train: [{bbb_train_min:.2f}, {bbb_train_max:.2f}])")
    print(f"  unemployment: {unemp_val:.4f} (train: [{unemp_train_min:.2f}, {unemp_train_max:.2f}])")
    print(f"  bbb_extrap: {bbb_extrap:.4f}, unemp_extrap: {unemp_extrap:.4f}")
    print(f"  extrapolation_factor: {extrapolation_factor:.4f}")
    print(f"  y_pred: {y_pred[i]:.6f}")
    print(f"  y_lower: {y_lower:.6f}")
    print(f"  y_upper: {y_upper:.6f}")

# Save predictions
pred_df = pd.DataFrame(predictions)
pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']].to_csv('predictions.csv', index=False)
print("\n\nSaved predictions.csv")
print(pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']])

# Verify
print(f"\nNumber of rows: {len(pred_df)}")
print(f"Columns: {pred_df.columns.tolist()}")

```

## [47] tool

Final model summary:
                      OLS Regression Results                     
Dep. Variable:   ,y               ,  R-squared:         ,   0.516
Model:           ,OLS             ,  Adj. R-squared:    ,   0.504
Method:          ,Least Squares   ,  F-statistic:       ,   41.07
Date:            ,Tue, 27 Oct 2026,  Prob (F-statistic):,7.26e-13
Time:            ,14:42:20        ,  Log-Likelihood:    ,  250.63
No. Observations:,    80          ,  AIC:               ,  -495.3
Df Residuals:    ,    77          ,  BIC:               ,  -488.1
Df Model:        ,     2          ,                     ,        
Covariance Type: ,nonrobust       ,                     ,        
     ,   coef   , std err ,    t    ,P>|t| ,  [0.025 ,  0.975] 
const,   -0.0062,    0.007,   -0.935, 0.353,   -0.019,    0.007
x1   ,    0.0127,    0.001,    8.700, 0.000,    0.010,    0.016
x2   ,    0.0025,    0.001,    2.292, 0.025,    0.000,    0.005
Omnibus:      ,37.142,  Durbin-Watson:     ,   2.094
Prob(Omnibus):, 0.000,  Jarque-Bera (JB):  , 131.277
Skew:         , 1.389,  Prob(JB):          ,3.12e-29
Kurtosis:     , 8.627,  Cond. No.          ,    33.5

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.

Residual std: 0.010547
Predicted range: [0.011024, 0.053286]
Actual range: [0.003167, 0.093801]
Spearman correlation (predicted vs |residual|): 0.3864, p=0.0004

Training ranges:
  bbb_spread: [0.23, 3.57]
  unemployment: [3.07, 8.04]

Scenario predictions:
  Quarter 81: 0.040167
  Quarter 82: 0.043111
  Quarter 83: 0.046093
  Quarter 84: 0.049115
  Quarter 85: 0.052178
  Quarter 86: 0.055285
  Quarter 87: 0.058438
  Quarter 88: 0.061640
  Quarter 89: 0.064891

Empirical residual 2.5th percentile: -0.017315
Empirical residual 97.5th percentile: 0.019741

Quarter 81:
  bbb_spread: 2.4174 (train: [0.23, 3.57])
  unemployment: 6.2898 (train: [3.07, 8.04])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.040167
  y_lower: 0.019164
  y_upper: 0.061170

Quarter 82:
  bbb_spread: 2.5886 (train: [0.23, 3.57])
  unemployment: 6.5991 (train: [3.07, 8.04])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.043111
  y_lower: 0.022108
  y_upper: 0.064114

Quarter 83:
  bbb_spread: 2.7598 (train: [0.23, 3.57])
  unemployment: 6.9235 (train: [3.07, 8.04])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.046093
  y_lower: 0.025090
  y_upper: 0.067095

Quarter 84:
  bbb_spread: 2.9311 (train: [0.23, 3.57])
  unemployment: 7.2640 (train: [3.07, 8.04])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.049115
  y_lower: 0.028113
  y_upper: 0.070118

Quarter 85:
  bbb_spread: 3.1023 (train: [0.23, 3.57])
  unemployment: 7.6211 (train: [3.07, 8.04])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.052178
  y_lower: 0.031176
  y_upper: 0.073181

Quarter 86:
  bbb_spread: 3.2735 (train: [0.23, 3.57])
  unemployment: 7.9958 (train: [3.07, 8.04])
  bbb_extrap: 0.0000, unemp_extrap: 0.0000
  extrapolation_factor: 1.0000
  y_pred: 0.055285
  y_lower: 0.034282
  y_upper: 0.076288

Quarter 87:
  bbb_spread: 3.4447 (train: [0.23, 3.57])
  unemployment: 8.3890 (train: [3.07, 8.04])
  bbb_extrap: 0.0000, unemp_extrap: 0.0704
  extrapolation_factor: 1.1409
  y_pred: 0.058438
  y_lower: 0.034476
  y_upper: 0.082400

Quarter 88:
  bbb_spread: 3.6160 (train: [0.23, 3.57])
  unemployment: 8.8015 (train: [3.07, 8.04])
  bbb_extrap: 0.0139, unemp_extrap: 0.1535
  extrapolation_factor: 1.3347
  y_pred: 0.061640
  y_lower: 0.033608
  y_upper: 0.089672

Quarter 89:
  bbb_spread: 3.7872 (train: [0.23, 3.57])
  unemployment: 9.2342 (train: [3.07, 8.04])
  bbb_extrap: 0.0652, unemp_extrap: 0.2406
  extrapolation_factor: 1.6116
  y_pred: 0.064891
  y_lower: 0.031043
  y_upper: 0.098739


Saved predictions.csv
   quarter    y_pred   y_lower   y_upper
0       81  0.040167  0.019164  0.061170
1       82  0.043111  0.022108  0.064114
2       83  0.046093  0.025090  0.067095
3       84  0.049115  0.028113  0.070118
4       85  0.052178  0.031176  0.073181
5       86  0.055285  0.034282  0.076288
6       87  0.058438  0.034476  0.082400
7       88  0.061640  0.033608  0.089672
8       89  0.064891  0.031043  0.098739

Number of rows: 9
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']


## [48] assistant

**[reasoning]**

> The current model is a simple linear model with bbb_spread and unemployment. The residuals show heteroskedasticity (Spearman correlation of 0.3864, p=0.0004), meaning the residual variance increases with the predicted value. This is a problem for prediction intervals.
> 
> Let me think about this more carefully. The scenario pushes unemployment beyond the training range (up to 9.23 vs max 8.04) and bbb_spread beyond (up to 3.79 vs max 3.57). The model needs to handle this extrapolation.
> 
> Let me also consider that the residuals are skewed (skew=1.389, kurtosis=8.627), which means the normality assumption is violated. This could affect the prediction intervals.
> 
> Let me try a more robust approach:
> 1. Use a model that better captures the relationship (maybe with transformations)
> 2. Use bootstrap or empirical residuals for prediction intervals
> 3. Account for extrapolation uncertainty
> 
> Let me also reconsider the model. The bbb_spread has the strongest correlation (0.6995) with default_rate. Let me try a model that focuses on this relationship more carefully.
> 
> Also, I should consider that the scenario is a stress scenario where unemployment is rising and bbb_spread is widening - both of which should increase default rates. The model should reflect this.
> 
> Let me try a more comprehensive approach with:
> 1. Better feature engineering
> 2. Bootstrap-based prediction intervals
> 3. More careful extrapolation handling
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix for training
X_train = train_filled[macro_cols].copy()

# Add transformations
X_train['unemployment_sq'] = X_train['unemployment'] ** 2
X_train['bbb_spread_sq'] = X_train['bbb_spread'] ** 2
X_train['vix_sq'] = X_train['vix'] ** 2
X_train['gdp_growth'] = X_train['gdp'].diff().fillna(0)
X_train['unemployment_diff'] = X_train['unemployment'].diff().fillna(0)
X_train['bbb_spread_diff'] = X_train['bbb_spread'].diff().fillna(0)
X_train['vix_diff'] = X_train['vix'].diff().fillna(0)
X_train['gdp_lag1'] = X_train['gdp'].shift(1).bfill()
X_train['unemployment_lag1'] = X_train['unemployment'].shift(1).bfill()
X_train['bbb_spread_lag1'] = X_train['bbb_spread'].shift(1).bfill()
X_train['vix_lag1'] = X_train['vix'].shift(1).bfill()
X_train['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X_train['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X_train['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X_train.dropna().index
X_train = X_train.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

# Use the best model: bbb_spread + unemployment (raw)
features = ['bbb_spread', 'unemployment']
X_main = X_train[features].values
X_main_c = np.column_stack([np.ones(len(X_main)), X_main])

# Fit model
model = sm.OLS(y, X_main_c).fit()

# Get residuals
residuals = model.resid
residual_std = residuals.std()

# Get covariance matrix
cov_matrix = model.cov_params()
t_stat = stats.t.ppf(0.975, model.df_resid)

# Get training ranges
bbb_train_min, bbb_train_max = X_train['bbb_spread'].min(), X_train['bbb_spread'].max()
unemp_train_min, unemp_train_max = X_train['unemployment'].min(), X_train['unemployment'].max()

# Prepare scenario features
scenario_features = scenario[['bbb_spread', 'unemployment']].values
scenario_c = np.column_stack([np.ones(len(scenario_features)), scenario_features])

# Generate predictions
y_pred = model.predict(scenario_c)

# Bootstrap-based prediction intervals
# This accounts for both model uncertainty and residual uncertainty
np.random.seed(42)
n_bootstrap = 5000

# For each bootstrap sample, fit the model and predict
bootstrap_preds = np.zeros((n_bootstrap, len(scenario)))

for b in range(n_bootstrap):
    # Resample residuals
    boot_residuals = np.random.choice(residuals, size=len(y), replace=True)
    
    # Generate bootstrap y values
    y_boot = model.predict(X_main_c) + boot_residuals
    
    # Refit model
    model_boot = sm.OLS(y_boot, X_main_c).fit()
    
    # Predict on scenario
    boot_pred = model_boot.predict(scenario_c)
    bootstrap_preds[b] = boot_pred

# Compute percentiles
y_lower = np.percentile(bootstrap_preds, 2.5, axis=0)
y_upper = np.percentile(bootstrap_preds, 97.5, axis=0)
y_pred_bootstrap = np.median(bootstrap_preds, axis=0)

print("Bootstrap predictions:")
for i, q in enumerate(scenario['quarter']):
    print(f"  Quarter {q}: pred={y_pred_bootstrap[i]:.6f}, [{y_lower[i]:.6f}, {y_upper[i]:.6f}]")

# Also compute analytical prediction intervals for comparison
predictions_analytical = []
for i in range(len(scenario)):
    x = scenario_c[i]
    se_pred = np.sqrt(residual_std**2 * (1 + x @ cov_matrix @ x))
    
    # Extrapolation penalty
    bbb_val = scenario['bbb_spread'].iloc[i]
    unemp_val = scenario['unemployment'].iloc[i]
    
    bbb_range = bbb_train_max - bbb_train_min
    unemp_range = unemp_train_max - unemp_train_min
    
    bbb_extrap = max(0, bbb_val - bbb_train_max) / bbb_range if bbb_range > 0 else 0
    unemp_extrap = max(0, unemp_val - unemp_train_max) / unemp_range if unemp_range > 0 else 0
    
    extrapolation_factor = 1 + 2 * (bbb_extrap + unemp_extrap)
    se_pred_wide = se_pred * extrapolation_factor
    
    y_lower_a = y_pred[i] - t_stat * se_pred_wide
    y_upper_a = y_pred[i] + t_stat * se_pred_wide
    
    y_lower_a = max(0, y_lower_a)
    y_upper_a = min(1, y_upper_a)
    
    predictions_analytical.append({
        'quarter': scenario['quarter'].iloc[i],
        'y_pred': y_pred[i],
        'y_lower': y_lower_a,
        'y_upper': y_upper_a,
    })

print("\nAnalytical predictions:")
for p in predictions_analytical:
    print(f"  Quarter {p['quarter']}: pred={p['y_pred']:.6f}, [{p['y_lower']:.6f}, {p['y_upper']:.6f}]")

# Use bootstrap intervals as they better capture the non-normality of residuals
predictions = []
for i in range(len(scenario)):
    predictions.append({
        'quarter': scenario['quarter'].iloc[i],
        'y_pred': y_pred[i],
        'y_lower': max(0, y_lower[i]),
        'y_upper': min(1, y_upper[i]),
    })

# Save predictions
pred_df = pd.DataFrame(predictions)
pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']].to_csv('predictions.csv', index=False)
print("\n\nSaved predictions.csv")
print(pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']])

# Verify
print(f"\nNumber of rows: {len(pred_df)}")
print(f"Columns: {pred_df.columns.tolist()}")

```

## [49] tool

Bootstrap predictions:
  Quarter 81: pred=0.040097, [0.037122, 0.043613]
  Quarter 82: pred=0.043015, [0.039538, 0.047128]
  Quarter 83: pred=0.045990, [0.041864, 0.050811]
  Quarter 84: pred=0.049006, [0.044164, 0.054644]
  Quarter 85: pred=0.052039, [0.046378, 0.058563]
  Quarter 86: pred=0.055133, [0.048604, 0.062578]
  Quarter 87: pred=0.058265, [0.050868, 0.066652]
  Quarter 88: pred=0.061450, [0.053144, 0.070849]
  Quarter 89: pred=0.064702, [0.055453, 0.075073]

Analytical predictions:
  Quarter 81: pred=0.040167, [0.019164, 0.061170]
  Quarter 82: pred=0.043111, [0.022108, 0.064114]
  Quarter 83: pred=0.046093, [0.025090, 0.067095]
  Quarter 84: pred=0.049115, [0.028113, 0.070118]
  Quarter 85: pred=0.052178, [0.031176, 0.073181]
  Quarter 86: pred=0.055285, [0.034282, 0.076288]
  Quarter 87: pred=0.058438, [0.034476, 0.082400]
  Quarter 88: pred=0.061640, [0.033608, 0.089672]
  Quarter 89: pred=0.064891, [0.031043, 0.098739]


Saved predictions.csv
   quarter    y_pred   y_lower   y_upper
0       81  0.040167  0.037122  0.043613
1       82  0.043111  0.039538  0.047128
2       83  0.046093  0.041864  0.050811
3       84  0.049115  0.044164  0.054644
4       85  0.052178  0.046378  0.058563
5       86  0.055285  0.048604  0.062578
6       87  0.058438  0.050868  0.066652
7       88  0.061640  0.053144  0.070849
8       89  0.064891  0.055453  0.075073

Number of rows: 9
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']


## [50] assistant

**[reasoning]**

> The bootstrap intervals are too narrow - they only capture model uncertainty, not the full prediction uncertainty (which should include residual variance). Let me fix this by adding the residual variance to the bootstrap predictions.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from scipy import stats
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix for training
X_train = train_filled[macro_cols].copy()

# Add transformations
X_train['unemployment_sq'] = X_train['unemployment'] ** 2
X_train['bbb_spread_sq'] = X_train['bbb_spread'] ** 2
X_train['vix_sq'] = X_train['vix'] ** 2
X_train['gdp_growth'] = X_train['gdp'].diff().fillna(0)
X_train['unemployment_diff'] = X_train['unemployment'].diff().fillna(0)
X_train['bbb_spread_diff'] = X_train['bbb_spread'].diff().fillna(0)
X_train['vix_diff'] = X_train['vix'].diff().fillna(0)
X_train['gdp_lag1'] = X_train['gdp'].shift(1).bfill()
X_train['unemployment_lag1'] = X_train['unemployment'].shift(1).bfill()
X_train['bbb_spread_lag1'] = X_train['bbb_spread'].shift(1).bfill()
X_train['vix_lag1'] = X_train['vix'].shift(1).bfill()
X_train['default_rate_lag1'] = train['default_rate'].shift(1).bfill()
X_train['default_rate_lag2'] = train['default_rate'].shift(2).bfill()
X_train['default_rate_lag3'] = train['default_rate'].shift(3).bfill()

# Drop rows with NaN in features (from lags)
drop_idx = X_train.dropna().index
X_train = X_train.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

# Use the best model: bbb_spread + unemployment (raw)
features = ['bbb_spread', 'unemployment']
X_main = X_train[features].values
X_main_c = np.column_stack([np.ones(len(X_main)), X_main])

# Fit model
model = sm.OLS(y, X_main_c).fit()

# Get residuals
residuals = model.resid
residual_std = residuals.std()

# Get covariance matrix
cov_matrix = model.cov_params()
t_stat = stats.t.ppf(0.975, model.df_resid)

# Get training ranges
bbb_train_min, bbb_train_max = X_train['bbb_spread'].min(), X_train['bbb_spread'].max()
unemp_train_min, unemp_train_max = X_train['unemployment'].min(), X_train['unemployment'].max()

# Prepare scenario features
scenario_features = scenario[['bbb_spread', 'unemployment']].values
scenario_c = np.column_stack([np.ones(len(scenario_features)), scenario_features])

# Generate predictions
y_pred = model.predict(scenario_c)

# Bootstrap-based prediction intervals
# This accounts for both model uncertainty and residual uncertainty
np.random.seed(42)
n_bootstrap = 5000

# For each bootstrap sample, fit the model and predict
bootstrap_preds = np.zeros((n_bootstrap, len(scenario)))

for b in range(n_bootstrap):
    # Resample residuals
    boot_residuals = np.random.choice(residuals, size=len(y), replace=True)
    
    # Generate bootstrap y values
    y_boot = model.predict(X_main_c) + boot_residuals
    
    # Refit model
    model_boot = sm.OLS(y_boot, X_main_c).fit()
    
    # Predict on scenario AND add a new residual for the prediction
    boot_pred = model_boot.predict(scenario_c) + np.random.choice(residuals, size=len(scenario), replace=True)
    bootstrap_preds[b] = boot_pred

# Compute percentiles
y_lower = np.percentile(bootstrap_preds, 2.5, axis=0)
y_upper = np.percentile(bootstrap_preds, 97.5, axis=0)
y_pred_bootstrap = np.median(bootstrap_preds, axis=0)

print("Bootstrap predictions (with residual uncertainty):")
for i, q in enumerate(scenario['quarter']):
    print(f"  Quarter {q}: pred={y_pred_bootstrap[i]:.6f}, [{y_lower[i]:.6f}, {y_upper[i]:.6f}]")

# Also compute analytical prediction intervals for comparison
predictions_analytical = []
for i in range(len(scenario)):
    x = scenario_c[i]
    se_pred = np.sqrt(residual_std**2 * (1 + x @ cov_matrix @ x))
    
    # Extrapolation penalty
    bbb_val = scenario['bbb_spread'].iloc[i]
    unemp_val = scenario['unemployment'].iloc[i]
    
    bbb_range = bbb_train_max - bbb_train_min
    unemp_range = unemp_train_max - unemp_train_min
    
    bbb_extrap = max(0, bbb_val - bbb_train_max) / bbb_range if bbb_range > 0 else 0
    unemp_extrap = max(0, unemp_val - unemp_train_max) / unemp_range if unemp_range > 0 else 0
    
    extrapolation_factor = 1 + 2 * (bbb_extrap + unemp_extrap)
    se_pred_wide = se_pred * extrapolation_factor
    
    y_lower_a = y_pred[i] - t_stat * se_pred_wide
    y_upper_a = y_pred[i] + t_stat * se_pred_wide
    
    y_lower_a = max(0, y_lower_a)
    y_upper_a = min(1, y_upper_a)
    
    predictions_analytical.append({
        'quarter': scenario['quarter'].iloc[i],
        'y_pred': y_pred[i],
        'y_lower': y_lower_a,
        'y_upper': y_upper_a,
    })

print("\nAnalytical predictions:")
for p in predictions_analytical:
    print(f"  Quarter {p['quarter']}: pred={p['y_pred']:.6f}, [{p['y_lower']:.6f}, {p['y_upper']:.6f}]")

# Use bootstrap intervals
predictions = []
for i in range(len(scenario)):
    predictions.append({
        'quarter': scenario['quarter'].iloc[i],
        'y_pred': y_pred[i],
        'y_lower': max(0, y_lower[i]),
        'y_upper': min(1, y_upper[i]),
    })

# Save predictions
pred_df = pd.DataFrame(predictions)
pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']].to_csv('predictions.csv', index=False)
print("\n\nSaved predictions.csv")
print(pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']])

# Verify
print(f"\nNumber of rows: {len(pred_df)}")
print(f"Columns: {pred_df.columns.tolist()}")

```

## [51] tool

Bootstrap predictions (with residual uncertainty):
  Quarter 81: pred=0.039577, [0.021980, 0.060532]
  Quarter 82: pred=0.042407, [0.024228, 0.063814]
  Quarter 83: pred=0.045418, [0.027207, 0.066606]
  Quarter 84: pred=0.048565, [0.030096, 0.070035]
  Quarter 85: pred=0.051424, [0.032870, 0.072712]
  Quarter 86: pred=0.054414, [0.036109, 0.075563]
  Quarter 87: pred=0.057512, [0.038686, 0.079775]
  Quarter 88: pred=0.060977, [0.041984, 0.083614]
  Quarter 89: pred=0.064490, [0.044048, 0.087528]

Analytical predictions:
  Quarter 81: pred=0.040167, [0.019164, 0.061170]
  Quarter 82: pred=0.043111, [0.022108, 0.064114]
  Quarter 83: pred=0.046093, [0.025090, 0.067095]
  Quarter 84: pred=0.049115, [0.028113, 0.070118]
  Quarter 85: pred=0.052178, [0.031176, 0.073181]
  Quarter 86: pred=0.055285, [0.034282, 0.076288]
  Quarter 87: pred=0.058438, [0.034476, 0.082400]
  Quarter 88: pred=0.061640, [0.033608, 0.089672]
  Quarter 89: pred=0.064891, [0.031043, 0.098739]


Saved predictions.csv
   quarter    y_pred   y_lower   y_upper
0       81  0.040167  0.021980  0.060532
1       82  0.043111  0.024228  0.063814
2       83  0.046093  0.027207  0.066606
3       84  0.049115  0.030096  0.070035
4       85  0.052178  0.032870  0.072712
5       86  0.055285  0.036109  0.075563
6       87  0.058438  0.038686  0.079775
7       88  0.061640  0.041984  0.083614
8       89  0.064891  0.044048  0.087528

Number of rows: 9
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']


## [52] assistant

**[reasoning]**

> The bootstrap intervals are reasonable but a bit narrow. Let me also consider using the analytical approach with extrapolation penalty, which gives wider intervals for the more extreme scenario quarters. Let me combine both approaches - use the analytical intervals with extrapolation penalty since the scenario pushes beyond training ranges.
> 
> Actually, looking at the results more carefully:
> - The bootstrap intervals (with residual uncertainty) are reasonable
> - The analytical intervals with extrapolation penalty are wider for extreme quarters
> 
> Let me use the analytical approach with extrapolation penalty since it better accounts for the fact that the scenario pushes beyond training ranges. The bootstrap approach doesn't account for extrapolation uncertainty.
> 
> Let me finalize with the analytical approach with extrapolation penalty.
> 





**tool call: python**

```

import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats

# Load data
train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Create features
macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

# Fill missing values with forward fill then backward fill
train_filled = train.copy()
for col in macro_cols:
    train_filled[col] = train_filled[col].ffill().bfill()

# Create feature matrix for training
X_train = train_filled[macro_cols].copy()

# Drop rows with NaN in features (from lags)
drop_idx = X_train.dropna().index
X_train = X_train.loc[drop_idx]
y = train['default_rate'].values[drop_idx]

# Use the best model: bbb_spread + unemployment (raw)
features = ['bbb_spread', 'unemployment']
X_main = X_train[features].values
X_main_c = np.column_stack([np.ones(len(X_main)), X_main])

# Fit model
model = sm.OLS(y, X_main_c).fit()

# Get residuals
residuals = model.resid
residual_std = residuals.std()

# Get covariance matrix
cov_matrix = model.cov_params()
t_stat = stats.t.ppf(0.975, model.df_resid)

# Get training ranges
bbb_train_min, bbb_train_max = X_train['bbb_spread'].min(), X_train['bbb_spread'].max()
unemp_train_min, unemp_train_max = X_train['unemployment'].min(), X_train['unemployment'].max()

# Prepare scenario features
scenario_features = scenario[['bbb_spread', 'unemployment']].values
scenario_c = np.column_stack([np.ones(len(scenario_features)), scenario_features])

# Generate predictions
y_pred = model.predict(scenario_c)

# Compute prediction intervals with extrapolation penalty
predictions = []
for i in range(len(scenario)):
    x = scenario_c[i]
    se_pred = np.sqrt(residual_std**2 * (1 + x @ cov_matrix @ x))
    
    # Extrapolation penalty
    bbb_val = scenario['bbb_spread'].iloc[i]
    unemp_val = scenario['unemployment'].iloc[i]
    
    bbb_range = bbb_train_max - bbb_train_min
    unemp_range = unemp_train_max - unemp_train_min
    
    bbb_extrap = max(0, bbb_val - bbb_train_max) / bbb_range if bbb_range > 0 else 0
    unemp_extrap = max(0, unemp_val - unemp_train_max) / unemp_range if unemp_range > 0 else 0
    
    # Extrapolation factor - moderate penalty
    extrapolation_factor = 1 + 2 * (bbb_extrap + unemp_extrap)
    se_pred_wide = se_pred * extrapolation_factor
    
    y_lower = y_pred[i] - t_stat * se_pred_wide
    y_upper = y_pred[i] + t_stat * se_pred_wide
    
    # Clip to [0, 1]
    y_lower = max(0, y_lower)
    y_upper = min(1, y_upper)
    
    predictions.append({
        'quarter': scenario['quarter'].iloc[i],
        'y_pred': y_pred[i],
        'y_lower': y_lower,
        'y_upper': y_upper,
    })

# Save predictions
pred_df = pd.DataFrame(predictions)
pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']].to_csv('predictions.csv', index=False)

# Verify
print("Final predictions.csv:")
print(pred_df[['quarter', 'y_pred', 'y_lower', 'y_upper']])
print(f"\nNumber of rows: {len(pred_df)}")
print(f"Columns: {pred_df.columns.tolist()}")

# Verify all values are valid fractions
assert all(pred_df['y_pred'] >= 0) and all(pred_df['y_pred'] <= 1), "y_pred out of range"
assert all(pred_df['y_lower'] >= 0) and all(pred_df['y_lower'] <= 1), "y_lower out of range"
assert all(pred_df['y_upper'] >= 0) and all(pred_df['y_upper'] <= 1), "y_upper out of range"
assert all(pred_df['y_lower'] <= pred_df['y_pred']), "y_lower > y_pred"
assert all(pred_df['y_pred'] <= pred_df['y_upper']), "y_pred > y_upper"
assert len(pred_df) == 9, "Wrong number of rows"

print("\nAll validations passed!")

```

## [53] tool

Final predictions.csv:
   quarter    y_pred   y_lower   y_upper
0       81  0.040167  0.019164  0.061170
1       82  0.043111  0.022108  0.064114
2       83  0.046093  0.025090  0.067095
3       84  0.049115  0.028113  0.070118
4       85  0.052178  0.031176  0.073181
5       86  0.055285  0.034282  0.076288
6       87  0.058438  0.034476  0.082400
7       88  0.061640  0.033608  0.089672
8       89  0.064891  0.031043  0.098739

Number of rows: 9
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']

All validations passed!


## [54] assistant

**[reasoning]**

> The predictions look reasonable. Let me verify the file one more time and make sure everything is correct.
> 
> The model uses bbb_spread and unemployment as predictors, which makes economic sense:
> - bbb_spread (BBB bond spread) is a strong indicator of credit risk
> - unemployment is a classic macroeconomic indicator of economic stress
> 
> The predictions show increasing default rates as the scenario worsens (higher unemployment, higher bbb_spread), which is economically sensible.
> 
> The prediction intervals widen as we extrapolate further beyond the training data range, which is appropriate.
> 
> Let me verify the file is correct.
> 





**tool call: bash**

```
cat predictions.csv
```

## [55] tool

quarter,y_pred,y_lower,y_upper
81,0.04016697486666247,0.019164310017220982,0.061169639716103966
82,0.04311098747165082,0.02210831107998038,0.06411366386332126
83,0.04609256871206838,0.025089876679664735,0.06709526074447202
84,0.04911547671578742,0.02811276454068452,0.07011818889089032
85,0.0521784151998166,0.031175677963397253,0.07318115243623595
86,0.055285142292028175,0.03428237457951726,0.07628791000453909
87,0.05843789718261329,0.03447601062283506,0.08239978374239151
88,0.06163994040162399,0.033607568082208925,0.08967231272103905
89,0.06489097086170936,0.031042729691252352,0.09873921203216637


## [56] assistant

**[reasoning]**

> The predictions look reasonable. Let me verify the file is correct and complete.
> 
> The model uses:
> - bbb_spread and unemployment as predictors (the two strongest correlates with default rate)
> - OLS regression on raw default rate
> - 95% prediction intervals with extrapolation penalty for values outside training range
> - The scenario pushes unemployment beyond the training range (up to 9.23 vs max 8.04) and bbb_spread slightly beyond (3.79 vs max 3.57)
> 
> The predictions show:
> - Increasing default rate as the stress scenario worsens (higher unemployment, higher bbb_spread)
> - Wider intervals for later quarters where extrapolation is more severe
> - All values are valid fractions in [0, 1]
> - 9 rows, one per scenario quarter
> 
> This looks good. Let me submit.
> 



The predictions are complete and valid. Let me verify the final output:



**tool call: bash**

```
python3 -c "
import pandas as pd
df = pd.read_csv('predictions.csv')
print('Shape:', df.shape)
print('Columns:', df.columns.tolist())
print()
print(df.to_string(index=False))
print()
print('All y_pred in [0,1]:', df['y_pred'].between(0,1).all())
print('All y_lower in [0,1]:', df['y_lower'].between(0,1).all())
print('All y_upper in [0,1]:', df['y_upper'].between(0,1).all())
print('y_lower <= y_pred:', (df['y_lower'] <= df['y_pred']).all())
print('y_pred <= y_upper:', (df['y_pred'] <= df['y_upper']).all())
print('Rows match scenario:', len(df) == 9)
"

```

## [57] tool

Shape: (9, 4)
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']

 quarter   y_pred  y_lower  y_upper
      81 0.040167 0.019164 0.061170
      82 0.043111 0.022108 0.064114
      83 0.046093 0.025090 0.067095
      84 0.049115 0.028113 0.070118
      85 0.052178 0.031176 0.073181
      86 0.055285 0.034282 0.076288
      87 0.058438 0.034476 0.082400
      88 0.061640 0.033608 0.089672
      89 0.064891 0.031043 0.098739

All y_pred in [0,1]: True
All y_lower in [0,1]: True
All y_upper in [0,1]: True
y_lower <= y_pred: True
y_pred <= y_upper: True
Rows match scenario: True


## [58] assistant

**[reasoning]**

> The predictions are complete and valid. Let me summarize what was done:
> 
> 1. **Data exploration**: Found that `bbb_spread` and `unemployment` are the strongest predictors of default rate (correlations of 0.70 and 0.20 respectively). Some macro series have missing values in early quarters.
> 
> 2. **Model selection**: After trying many feature combinations and models, the best simple model was `default_rate ~ bbb_spread + unemployment` using raw (non-logit) OLS. This model:
>    - Has R² = 0.516
>    - Both coefficients are statistically significant
>    - Had the best Leave-One-Out CV performance
>    - Is simple and interpretable
> 
> 3. **Prediction intervals**: Used analytical prediction intervals with:
>    - Standard error accounting for both model uncertainty (covariance matrix) and residual variance
>    - Extrapolation penalty factor that widens intervals when scenario values exceed training ranges
>    - The scenario pushes unemployment and bbb_spread beyond training ranges, so intervals widen accordingly
> 
> 4. **Output**: 9 rows with quarter, y_pred, y_lower, y_upper - all valid fractions in [0,1] with proper ordering.
> 
> The model predicts increasing default rates from ~4% to ~6.5% over the stress scenario quarters, reflecting the worsening macroeconomic conditions (rising unemployment, widening bbb spreads).
> 



The predictions have been successfully generated and saved to `predictions.csv`. Here's a summary of the approach:

**Model**: Linear regression of default rate on `bbb_spread` and `unemployment` (the two strongest predictors with correlations of 0.70 and 0.20 respectively).

**Key findings**:
- `bbb_spread` has a strong positive relationship with default rates (coefficient: 0.0127)
- `unemployment` also positively affects defaults (coefficient: 0.0025)
- The model explains ~52% of variance (R² = 0.516)

**Prediction intervals**:
- Computed using analytical formula: `y_pred ± t × SE_pred`
- SE accounts for both model parameter uncertainty (via covariance matrix) and residual variance
- Extrapolation penalty widens intervals when scenario values exceed training ranges (quarters 87-89 show unemployment and bbb_spread beyond training ranges)

**Results**: Default rates are predicted to increase from ~4.0% in quarter 81 to ~6.5% in quarter 89, reflecting the deteriorating macroeconomic conditions in the stress scenario (rising unemployment, widening credit spreads).

## [59] user

Please proceed to the next step using your best judgement.

## [60] assistant

**[reasoning]**

> The user wants me to proceed to the next step. Looking at the conversation, I have already:
> 1. Explored the data
> 2. Built a model (linear regression with bbb_spread and unemployment)
> 3. Generated predictions with 95% prediction intervals
> 4. Saved predictions.csv
> 
> The predictions.csv file has been created with the correct format:
> - quarter, y_pred, y_lower, y_upper
> - 9 rows (one per scenario quarter)
> - All values are valid fractions in [0, 1]
> - y_lower <= y_pred <= y_upper
> 
> The task is complete. The user said "Please proceed to the next step using your best judgement." Since the predictions.csv has been created and verified, I should submit the answer.
> 
> Let me verify once more that the file is correct and complete.
> 





**tool call: bash**

```
cat predictions.csv
```

## [61] tool

quarter,y_pred,y_lower,y_upper
81,0.04016697486666247,0.019164310017220982,0.061169639716103966
82,0.04311098747165082,0.02210831107998038,0.06411366386332126
83,0.04609256871206838,0.025089876679664735,0.06709526074447202
84,0.04911547671578742,0.02811276454068452,0.07011818889089032
85,0.0521784151998166,0.031175677963397253,0.07318115243623595
86,0.055285142292028175,0.03428237457951726,0.07628791000453909
87,0.05843789718261329,0.03447601062283506,0.08239978374239151
88,0.06163994040162399,0.033607568082208925,0.08967231272103905
89,0.06489097086170936,0.031042729691252352,0.09873921203216637


## [62] assistant

**[reasoning]**

> The predictions.csv file is already saved and valid. Let me verify it one more time and then submit.
> 



The `predictions.csv` file is already complete and valid with:
- 9 rows (one per scenario quarter)
- Columns: `quarter`, `y_pred`, `y_lower`, `y_upper`
- All values are valid fractions in [0, 1]
- Prediction intervals are properly ordered (lower ≤ pred ≤ upper)
- Extrapolation uncertainty is accounted for in the widening intervals for quarters 87-89



**tool call: submit**

```
predictions.csv has been generated with 9 rows (one per scenario quarter), containing point estimates and 95% prediction intervals for the default rate. The model uses bbb_spread and unemployment as predictors (the two strongest macroeconomic drivers of defaults), with prediction intervals that widen for quarters where scenario values exceed training ranges (quarters 87-89).
```

## [63] tool

predictions.csv has been generated with 9 rows (one per scenario quarter), containing point estimates and 95% prediction intervals for the default rate. The model uses bbb_spread and unemployment as predictors (the two strongest macroeconomic drivers of defaults), with prediction intervals that widen for quarters where scenario values exceed training ranges (quarters 87-89).

