# openai-api/macmini/mlx-community/Qwen3.6-35B-A3B-4bit-DWQ — ccar (id=instance-2-vasicek-legacy-seed-1320224556)

- 9/9 points predicted; Winkler regret 0.057 (agent 0.164 vs oracle 0.107, degenerate 1.593); MAE 0.007; coverage 0.818; mean width 0.065.
- messages 54 | limit None | seed None

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

> Let me start by exploring the data to understand what we're working with, then build a model and generate predictions.
> 





**tool call: bash**

```
ls data/ && head -30 data/train.csv && echo "---" && cat data/scenario.csv
```

## [3] tool

scenario.csv
train.csv
quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi,default_rate
1,119.6078,9.3006,,,,,482.5013,,125.0936,0.037574
2,120.193,9.2327,,,,,472.2537,,124.6449,0.092997
3,121.4081,8.9567,,,,,473.2188,,124.2013,0.044043
4,122.696,7.7753,,,,,460.8373,,124.3421,0.0553
5,124.3541,7.5383,,,,,488.6292,,123.595,0.027578
6,125.4937,6.1933,,,,,468.9426,,123.3352,0.05634
7,126.8252,5.8049,,,,,452.5544,,125.6511,0.05553
8,125.6757,6.9903,,,,,439.4541,,126.3409,0.046841
9,127.8999,7.2261,,,,,430.6951,,130.5078,0.024827
10,130.368,6.5486,,2.312,,,475.6062,,133.1867,0.037517
11,132.8822,4.7786,130.2162,2.2942,,,453.496,,134.3274,0.062589
12,134.5581,4.5812,131.7227,2.0665,,,486.9473,,137.6586,0.046627
13,136.5672,4.3997,131.6034,2.362,,,450.8673,,137.5078,0.091239
14,137.341,4.685,130.3511,2.4073,,,454.6545,,137.2484,0.031165
15,136.1427,5.1278,130.2293,2.1696,,,451.3413,18.7723,136.5711,0.03707
16,138.6284,4.5457,134.3467,1.8625,,,483.0283,12.5571,137.2853,0.0288
17,140.7996,4.3764,135.4868,1.5486,,,513.6946,11.7583,137.595,0.018319
18,144.9464,3.7483,133.3157,1.2207,,,541.9742,10.4754,138.8976,0.011119
19,147.0564,3.3086,131.2107,1.006,,,603.4066,11.16,137.3273,0.014964
20,148.1185,3.4694,126.9878,1.0213,,,623.4161,11.7784,135.685,0.014131
21,151.4481,3.3028,121.5787,0.8715,,,681.6251,11.5809,133.462,0.018416
22,152.1047,3.495,117.4353,0.3203,,,806.4173,8.2986,132.9649,0.012228
23,153.8001,3.6274,116.1,0.4931,,,853.8381,8.9819,132.8235,0.013846
24,153.9876,3.7517,115.9586,0.5321,,,928.1901,11.8507,131.1635,0.023696
25,154.5526,4.0713,116.1664,0.4988,,,978.6965,15.2632,131.1917,0.018347
26,157.0382,3.9464,116.1157,1.0001,,,998.819,17.7833,131.2004,0.045869
27,158.6411,4.5389,117.6327,1.3173,,,1047.8272,12.8578,132.7303,0.024714
28,159.9937,4.6163,118.5903,1.2834,,,1084.7152,14.7849,133.886,0.036092
29,161.9034,4.6914,123.1754,1.2059,,,1119.0811,13.8116,135.5326,0.024433
---
quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi
81,254.9245,4.264,304.5785,1.1336,4249.5134,3315.2177,8924.8129,20.0202,283.5362
82,250.1431,4.7169,294.4782,1.4777,4001.9196,3228.4191,7920.9354,21.7443,280.6296
83,245.4513,5.218,284.7128,1.8218,3843.7911,3160.2868,7029.9756,23.6169,277.7529
84,240.8475,5.7723,275.2712,2.166,3626.5569,3069.3175,6239.2325,25.6508,274.9056
85,236.3301,6.3854,266.1428,2.5101,3513.6282,3052.2929,5537.4334,27.8598,272.0875
86,231.8975,7.0637,257.317,2.8542,3534.1022,2841.0291,4914.5738,30.2591,269.2984
87,227.5479,7.814,248.7839,3.1983,3505.0011,2765.4737,4361.7745,32.865,266.5378
88,223.28,8.644,240.5339,3.5425,3385.4376,2614.3972,3871.155,35.6953,263.8055
89,219.0921,9.5622,232.5573,3.8866,3316.4024,2616.6436,3435.7212,38.7693,261.1012


## [4] assistant

**[reasoning]**

> Let me examine the data more closely to understand the patterns, missing values, and relationships.
> 





**tool call: bash**

```
wc -l data/train.csv data/scenario.csv && echo "---" && python3 -c "
import pandas as pd
train = pd.read_csv('data/train.csv')
print('Train shape:', train.shape)
print('Columns:', list(train.columns))
print()
print('Missing values per column:')
print(train.isnull().sum())
print()
print('Default rate stats:')
print(train['default_rate'].describe())
print()
print('Scenario shape:', pd.read_csv('data/scenario.csv').shape)
"

```

## [5] tool

  81 data/train.csv
  10 data/scenario.csv
  91 total
---
Train shape: (80, 11)
Columns: ['quarter', 'gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi', 'default_rate']

Missing values per column:
quarter          0
gdp              0
unemployment     0
hpi             10
bbb_spread       9
sp500           35
djia            35
nasdaq           0
vix             14
cpi              0
default_rate     0
dtype: int64

Default rate stats:
count    80.000000
mean      0.040185
std       0.025036
min       0.009106
25%       0.023325
50%       0.036581
75%       0.054794
max       0.145322
Name: default_rate, dtype: float64

Scenario shape: (9, 10)


## [6] assistant

**tool call: bash**

```
python3 -c "
import pandas as pd
train = pd.read_csv('data/train.csv')

# Check correlations with default_rate
features = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
corr = train[features].corrwith(train['default_rate'])
print('Correlations with default_rate:')
for f, c in corr.items():
    print(f'  {f}: {c:.4f}')

print()
# Check which features have data in early quarters (when they start being recorded)
for f in features:
    mask = train[f].notna()
    first_na = train[~mask].index.min() if mask.sum() < len(train) else 'none'
    last_avail = train[mask].index.max()
    print(f'{f}: starts at row {train[mask].index.min()}, ends at row {last_avail}')
"

```

## [7] tool

Correlations with default_rate:
  gdp: 0.0367
  unemployment: 0.1732
  hpi: 0.1480
  bbb_spread: 0.4287
  sp500: -0.0795
  djia: -0.0914
  nasdaq: -0.0145
  vix: 0.8839
  cpi: 0.0963

gdp: starts at row 0, ends at row 79
unemployment: starts at row 0, ends at row 79
hpi: starts at row 10, ends at row 79
bbb_spread: starts at row 9, ends at row 79
sp500: starts at row 35, ends at row 79
djia: starts at row 35, ends at row 79
nasdaq: starts at row 0, ends at row 79
vix: starts at row 14, ends at row 79
cpi: starts at row 0, ends at row 79


## [8] assistant

**[reasoning]**

> Let me explore the data more carefully and build a robust model. I'll investigate transformations, feature engineering, and then fit a model with prediction intervals.
> 





**tool call: bash**

```
python3 -c "
import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')

# Check data patterns
print('VIX range:', train['vix'].notna().sum(), 'values')
print('bbb_spread range:', train['bbb_spread'].notna().sum(), 'values')
print('nasdaq range:', train['nasdaq'].notna().sum(), 'values')
print('cpi range:', train['cpi'].notna().sum(), 'values')

# Look at scenario values vs training ranges
scenario = pd.read_csv('data/scenario.csv')

for col in ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']:
    if col in train.columns:
        t_min, t_max = train[col].min(), train[col].max()
        if col in scenario.columns:
            s_min, s_max = scenario[col].min(), scenario[col].max()
            print(f'{col}: train=[{t_min:.2f}, {t_max:.2f}], scenario=[{s_min:.2f}, {s_max:.2f}]')
            print(f'  scenario beyond train? min: {s_min < t_min}, max: {s_max > t_max}')

# Natural gas prices (nasdaq in this context seems to be something else - check values)
print()
print('Nasdaq sample:', train['nasdaq'].head(20).tolist())
print()
print('Scenario nasdaq:', scenario['nasdaq'].tolist())
"

```

## [9] tool

VIX range: 66 values
bbb_spread range: 71 values
nasdaq range: 80 values
cpi range: 80 values
gdp: train=[119.61, 259.80], scenario=[219.09, 254.92]
  scenario beyond train? min: False, max: False
unemployment: train=[3.30, 12.56], scenario=[4.26, 9.56]
  scenario beyond train? min: False, max: False
hpi: train=[115.96, 315.03], scenario=[232.56, 304.58]
  scenario beyond train? min: False, max: False
bbb_spread: train=[0.32, 3.06], scenario=[1.13, 3.89]
  scenario beyond train? min: False, max: True
sp500: train=[836.60, 4388.75], scenario=[3316.40, 4249.51]
  scenario beyond train? min: False, max: False
djia: train=[715.16, 3233.31], scenario=[2614.40, 3315.22]
  scenario beyond train? min: False, max: True
nasdaq: train=[430.70, 10055.92], scenario=[3435.72, 8924.81]
  scenario beyond train? min: False, max: False
vix: train=[8.30, 35.33], scenario=[20.02, 38.77]
  scenario beyond train? min: False, max: True
cpi: train=[123.34, 286.47], scenario=[261.10, 283.54]
  scenario beyond train? min: False, max: False

Nasdaq sample: [482.5013, 472.2537, 473.2188, 460.8373, 488.6292, 468.9426, 452.5544, 439.4541, 430.6951, 475.6062, 453.496, 486.9473, 450.8673, 454.6545, 451.3413, 483.0283, 513.6946, 541.9742, 603.4066, 623.4161]

Scenario nasdaq: [8924.8129, 7920.9354, 7029.9756, 6239.2325, 5537.4334, 4914.5738, 4361.7745, 3871.155, 3435.7212]


## [10] assistant

**[reasoning]**

> Now I have a good understanding of the data. Let me analyze it:
> 
> 1. The strongest correlator is VIX (0.884), followed by bbb_spread (0.429)
> 2. Several features have missing values in early quarters - I need to handle this
> 3. The scenario goes beyond training ranges for vix, bbb_spread, and djia
> 4. Nasdaq has interesting behavior - it's 0/missing for early quarters and appears in later ones
> 
> Let me look more carefully at the data patterns and build a robust model.
> 





**tool call: bash**

```
python3 -c "
import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Let's check what nasdaq looks like - it has values throughout
print('nasdaq missing per row:', train['nasdaq'].isnull().sum())
print('djia missing per row:', train['djia'].isnull().sum())
print('sp500 missing per row:', train['sp500'].isnull().sum())
print()

# Let's see if nasdaq and sp500 are related
available = train[['nasdaq', 'sp500']].dropna()
if len(available) > 1:
    print('nasdaq vs sp500 correlation:', available.corr()['nasdaq']['sp500'])
    
# Check time patterns - maybe there are lags that matter
print()
print('Training quarters:', train['quarter'].min(), '-', train['quarter'].max())
print('Scenario quarters:', scenario['quarter'].min(), '-', scenario['quarter'].max())

# Let's see if there are any obvious transformation that works well
# E.g. delta/changes in variables, or ratios
for col in ['gdp', 'unemployment', 'vix', 'bbb_spread']:
    if col in train.columns:
        diff = train[col].diff()
        corr = np.corrcoef(train[col].dropna(), train['default_rate'].iloc[1:].values[:len(diff.dropna())])[0,1]
        diff_corr = np.corrcoef(diff.dropna(), train['default_rate'].iloc[1:].dropna().values[:len(diff.dropna())])[0,1]
        print(f'{col}: level corr={corr:.4f}, diff corr={diff_corr:.4f}')
"

```

## [11] tool

Traceback (most recent call last):
  File "<string>", line 29, in <module>
  File "/usr/local/lib/python3.12/site-packages/numpy/lib/_function_base_impl.py", line 3028, in corrcoef
    c = cov(x, y, rowvar, dtype=dtype)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/numpy/lib/_function_base_impl.py", line 2836, in cov
    X = np.concatenate((X, y), axis=0)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: all the input array dimensions except for the concatenation axis must match exactly, but along dimension 1, the array at index 0 has size 80 and the array at index 1 has size 79

nasdaq missing per row: 0
djia missing per row: 35
sp500 missing per row: 35

nasdaq vs sp500 correlation: 0.9891622359223342

Training quarters: 1 - 80
Scenario quarters: 81 - 89


## [12] assistant

**[reasoning]**

> Let me fix the correlation calculation and explore more deeply. The nasdaq values jump dramatically from ~500-1000 to 3000-8000 in the scenario, which is a huge jump. Let me investigate more.
> 





**tool call: bash**

```
python3 << 'EOF'
import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Check lagged correlations
for lag in range(1, 5):
    df = train.dropna(subset=['vix']).copy()
    if len(df) > lag:
        vix_lag = df['vix'].shift(lag).dropna()
        dr_lag = df['default_rate'].iloc[lag:].values[:len(vix_lag)]
        corr = np.corrcoef(vix_lag.values, dr_lag)[0, 1]
        print(f'vix lag {lag}: corr with dr = {corr:.4f}')

# Check bbb_spread lags
for lag in range(1, 5):
    df = train.dropna(subset=['bbb_spread']).copy()
    if len(df) > lag:
        bbb_lag = df['bbb_spread'].shift(lag).dropna()
        dr_lag = df['default_rate'].iloc[lag:].values[:len(bbb_lag)]
        corr = np.corrcoef(bbb_lag.values, dr_lag)[0, 1]
        print(f'bbb_spread lag {lag}: corr with dr = {corr:.4f}')

# Check unemployment lags
for lag in range(1, 5):
    df = train.copy()
    if len(df) > lag:
        unemp_lag = df['unemployment'].shift(lag).dropna()
        dr_lag = df['default_rate'].iloc[lag:].values[:len(unemp_lag)]
        corr = np.corrcoef(unemp_lag.values, dr_lag)[0, 1]
        print(f'unemployment lag {lag}: corr with dr = {corr:.4f}')

# Also check: maybe default rate is correlated with VIX * bbb_spread (interaction)
# Or some economic cycle indicator
# Let's look at current VIX vs current DR (with available data)
vix_avail = train.dropna(subset=['vix'])
print(f"\nVIX vs DR current: corr = {np.corrcoef(vix_avail['vix'], vix_avail['default_rate'])[0,1]:.4f}")

bbb_avail = train.dropna(subset=['bbb_spread'])
print(f"bbb_spread vs DR current: corr = {np.corrcoef(bbb_avail['bbb_spread'], bbb_avail['default_rate'])[0,1]:.4f}")

# What about change in VIX?
vix_avail2 = train.dropna(subset=['vix'])
if len(vix_avail2) > 1:
    vix_diff = vix_avail2['vix'].diff().iloc[1:]
    dr_vals = vix_avail2['default_rate'].iloc[1:].values[:len(vix_diff)]
    print(f"dVIX vs DR: corr = {np.corrcoef(vix_diff.values, dr_vals)[0,1]:.4f}")

# Check: is nasdaq something totally different? Like natural gas price?
print(f"\nNasdaq train mean: {train['nasdaq'].mean():.2f}")
print(f"Scenario nasdaq mean: {scenario['nasdaq'].mean():.2f}")
# The scenario nasdaq is 3000-8000 range vs train 430-10055... hmm
# Actually looking at the data again, nasdaq seems to be in a different scale
# Let's check if it's possibly gas price or something

# Check hpi correlation
hpi_avail = train.dropna(subset=['hpi'])
print(f"hpi vs DR: corr = {np.corrcoef(hpi_avail['hpi'], hpi_avail['default_rate'])[0,1]:.4f}")

# cpi 
print(f"cpi vs DR: corr = {np.corrcoef(train['cpi'], train['default_rate'])[0,1]:.4f}")
EOF

```

## [13] tool

vix lag 1: corr with dr = 0.6655
vix lag 2: corr with dr = 0.5395
vix lag 3: corr with dr = 0.3069
vix lag 4: corr with dr = 0.1936
bbb_spread lag 1: corr with dr = 0.2648
bbb_spread lag 2: corr with dr = 0.0958
bbb_spread lag 3: corr with dr = -0.0076
bbb_spread lag 4: corr with dr = -0.1543
unemployment lag 1: corr with dr = 0.1340
unemployment lag 2: corr with dr = 0.0152
unemployment lag 3: corr with dr = 0.0260
unemployment lag 4: corr with dr = -0.0196

VIX vs DR current: corr = 0.8839
bbb_spread vs DR current: corr = 0.4287
dVIX vs DR: corr = 0.3269

Nasdaq train mean: 2735.91
Scenario nasdaq mean: 5803.96
hpi vs DR: corr = 0.1480
cpi vs DR: corr = 0.0963


## [14] assistant

**[reasoning]**

> VIX is clearly the dominant predictor with 0.88 correlation. The scenario has VIX values beyond the training range (up to 38.77 vs max ~35). Let me build a robust model using VIX as the primary predictor, possibly with some other variables, and handle extrapolation carefully.
> 
> Let me think about this more carefully:
> 1. VIX is very strongly correlated with default rate (0.88)
> 2. BBB spread also has moderate correlation (0.43)
> 3. The scenario pushes VIX and BBB spread beyond training ranges
> 4. I need prediction intervals that reflect extrapolation uncertainty
> 
> Let me try multiple approaches:
> - Linear regression on VIX (primary driver)
> - Maybe include log transformations or other features
> - Use bootstrap or quantile regression for prediction intervals
> - Consider the fact that VIX is a volatility index and defaults are related to stress
> 
> Since VIX dominates, let me explore this relationship more deeply, then build intervals.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
import statsmodels.api as sm

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Focus on the most important features: VIX, bbb_spread, and others
# With available data for all features

# Let's create a comprehensive feature set
def build_features(df):
    features = df[['gdp', 'unemployment', 'nasdaq', 'cpi']].copy()
    if 'vix' in df.columns:
        features['vix'] = df['vix']
    if 'bbb_spread' in df.columns:
        features['bbb_spread'] = df['bbb_spread']
    if 'hpi' in df.columns:
        features['hpi'] = df['hpi']
    if 'sp500' in df.columns:
        features['sp500'] = df['sp500']
    if 'djia' in df.columns:
        features['djia'] = df['djia']
    return features

# Prepare training data - keep all available columns
train_feat = build_features(train)

# Let's also add derived features
for col in ['gdp', 'unemployment', 'vix', 'bbb_spread']:
    if col in train_feat.columns:
        train_feat[f'{col}_log'] = np.log(train_feat[col].clip(lower=1e-6))
        train_feat[f'{col}_diff'] = train_feat[col].diff()
        
train_feat['vix_x_bbb'] = train_feat.get('vix', pd.Series(np.nan)) * train_feat.get('bbb_spread', pd.Series(np.nan))
train_feat['vix_sq'] = train_feat.get('vix', pd.Series(np.nan)) ** 2

print("Feature matrix shape:", train_feat.shape)
print("Columns:", list(train_feat.columns))

# Now let's see which features have least missing values
print("\nMissing per feature:")
print(train_feat.isnull().sum().sort_values())

# Try different model approaches with cross-validation on the full available data
# First, use only VIX (simplest)
y = train['default_rate']

# Model 1: Simple VIX only
mask_vix = train_feat['vix'].notna()
X_vix = train_feat.loc[mask_vix, ['vix']]
y_vix = y.loc[mask_vix]

print(f"\nVIX-only: n={len(X_vix)}, R2 (CV):")
for alpha in [0, 0.1, 1, 10, 100]:
    model = Ridge(alpha=alpha)
    scores = cross_val_score(model, X_vix, y_vix, cv=5, scoring='r2')
    print(f"  Ridge(alpha={alpha}): mean R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# Model 2: VIX + BBB (only rows where both available)
mask_vix_bbb = X_vix['vix'].notna() & (train_feat['bbb_spread'].notna())
X2 = train_feat.loc[mask_vix_bbb, ['vix', 'bbb_spread']]
y2 = y.loc[mask_vix_bbb]
print(f"\nVIX+BBB: n={len(X2)}")
for alpha in [0, 0.1, 1]:
    model = Ridge(alpha=alpha)
    scores = cross_val_score(model, X2, y2, cv=5, scoring='r2')
    print(f"  Ridge(alpha={alpha}): mean R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# Model 3: VIX + bbb + unemployment
mask3 = (train_feat['vix'].notna()) & (train_feat['bbb_spread'].notna()) & (train_feat['unemployment'].notna())
X3 = train_feat.loc[mask3, ['vix', 'bbb_spread', 'unemployment']]
y3 = y.loc[mask3]
print(f"\nVIX+BBB+UNEMP: n={len(X3)}")
for alpha in [0, 0.1, 1]:
    model = Ridge(alpha=alpha)
    scores = cross_val_score(model, X3, y3, cv=5, scoring='r2')
    print(f"  Ridge(alpha={alpha}): mean R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# Model 4: Try log transform of vix
mask3b = (train_feat['vix_log'].notna()) & (train_feat['bbb_spread'].notna())
X4 = train_feat.loc[mask3b, ['vix_log', 'bbb_spread']]
y4 = y.loc[mask3b]
print(f"\nlog(VIX)+BBB: n={len(X4)}")
for alpha in [0, 0.1, 1]:
    model = Ridge(alpha=alpha)
    scores = cross_val_score(model, X4, y4, cv=5, scoring='r2')
    print(f"  Ridge(alpha={alpha}): mean R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# Model 5: VIX + bbb_spread + unemployment (all available)
mask5 = (train_feat['vix'].notna()) & (train_feat['bbb_spread'].notna())
X5 = train_feat.loc[mask5, ['vix', 'bbb_spread']]
y5 = y.loc[mask5]
print(f"\nVIX+BBB (2 features): n={len(X5)}")
model = LinearRegression()
model.fit(X5, y5)
print(f"  Coefficients: {dict(zip(['vix', 'bbb_spread'], model.coef_))}, intercept: {model.intercept_:.4f}")
print(f"  R2 (in-sample): {model.score(X5, y5):.4f}")
print(f"  Residual std: {np.std(y5 - model.predict(X5)):.4f}")

# Try polynomial features
from sklearn.preprocessing import PolynomialFeatures
X_vix_poly = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X_vix[['vix']])
for alpha in [0, 1, 10]:
    model = Ridge(alpha=alpha)
    model.fit(X_vix_poly, y_vix)
    scores = cross_val_score(model, X_vix_poly, y_vix, cv=5, scoring='r2')
    print(f"  VIX poly degree 2 (alpha={alpha}): mean R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

PYEOF

```

## [15] tool

Feature matrix shape: (80, 19)
Columns: ['gdp', 'unemployment', 'nasdaq', 'cpi', 'vix', 'bbb_spread', 'hpi', 'sp500', 'djia', 'gdp_log', 'gdp_diff', 'unemployment_log', 'unemployment_diff', 'vix_log', 'vix_diff', 'bbb_spread_log', 'bbb_spread_diff', 'vix_x_bbb', 'vix_sq']

Missing per feature:
gdp                   0
unemployment          0
nasdaq                0
cpi                   0
unemployment_log      0
gdp_log               0
unemployment_diff     1
gdp_diff              1
bbb_spread_log        9
bbb_spread            9
hpi                  10
bbb_spread_diff      10
vix_log              14
vix_sq               14
vix_x_bbb            14
vix                  14
vix_diff             15
sp500                35
djia                 35
dtype: int64

VIX-only: n=66, R2 (CV):
  Ridge(alpha=0): mean R2 = 0.5944 +/- 0.1493
  Ridge(alpha=0.1): mean R2 = 0.5944 +/- 0.1493
  Ridge(alpha=1): mean R2 = 0.5945 +/- 0.1491
  Ridge(alpha=10): mean R2 = 0.5954 +/- 0.1474
  Ridge(alpha=100): mean R2 = 0.5980 +/- 0.1324

VIX+BBB: n=66
  Ridge(alpha=0): mean R2 = 0.6042 +/- 0.1367
  Ridge(alpha=0.1): mean R2 = 0.6042 +/- 0.1367
  Ridge(alpha=1): mean R2 = 0.6045 +/- 0.1374

VIX+BBB+UNEMP: n=66
  Ridge(alpha=0): mean R2 = 0.5731 +/- 0.1946
  Ridge(alpha=0.1): mean R2 = 0.5735 +/- 0.1942
  Ridge(alpha=1): mean R2 = 0.5763 +/- 0.1907

log(VIX)+BBB: n=66
  Ridge(alpha=0): mean R2 = 0.4452 +/- 0.1709
  Ridge(alpha=0.1): mean R2 = 0.4501 +/- 0.1603
  Ridge(alpha=1): mean R2 = 0.4421 +/- 0.1600

VIX+BBB (2 features): n=66
  Coefficients: {'vix': np.float64(0.004175694426880082), 'bbb_spread': np.float64(-0.003147127372388274)}, intercept: -0.0262
  R2 (in-sample): 0.7854
  Residual std: 0.0117
  VIX poly degree 2 (alpha=0): mean R2 = 0.6302 +/- 0.1594
  VIX poly degree 2 (alpha=1): mean R2 = 0.6304 +/- 0.1594
  VIX poly degree 2 (alpha=10): mean R2 = 0.6323 +/- 0.1596


## [16] assistant

**[reasoning]**

> The VIX-only model seems quite strong with R2 ~0.6 in cross-validation. Let me explore more features and transformations to see if I can improve the model, especially considering the extrapolation issue mentioned in the prompt.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
import statsmodels.api as sm

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Let's try a broader feature set and model exploration
y = train['default_rate']

# Key features with lots of data: gdp, unemployment, nasdaq, cpi
# VIX has 66 obs, bbb_spread has 71 obs

# Let's try many feature combinations
features_full = ['gdp', 'unemployment', 'nasdaq', 'cpi', 'vix', 'bbb_spread']

# Since vix and bbb_spread have fewer observations, 
# let's also try with only the fully available features
features_available = ['gdp', 'unemployment', 'nasdaq', 'cpi']

# Also try transformations
for transform in ['', '_log', '_pct_change']:
    for f in features_full:
        if transform == '_log':
            print(f"{f}: scale check - {train[f].notna().sum()} non-null")
        elif transform == '_pct_change':
            print(f"{f}_diff: {train[f].diff().notna().sum()} non-null")

# Try with different model types on VIX-only (best so far)
mask = train['vix'].notna()
X_vix = train.loc[mask, ['vix']]
y_vix = y.loc[mask]

# GBR
for n_est in [50, 100, 200]:
    for lr_val in [0.05, 0.1]:
        model = GradientBoostingRegressor(n_estimators=n_est, learning_rate=lr_val, max_depth=3, random_state=42)
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(model, X_vix, y_vix, cv=kf, scoring='r2')
        print(f"GBR(n={n_est},lr={lr_val}): mean R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# RandomForest
for n_est in [50, 100]:
    model = RandomForestRegressor(n_estimators=n_est, max_depth=5, random_state=42)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X_vix, y_vix, cv=kf, scoring='r2')
    print(f"RF(n={n_est}): mean R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# Now try VIX + bbb_spread (both available for 66 obs)
mask2 = train['vix'].notna() & train['bbb_spread'].notna()
X2 = train.loc[mask2, ['vix', 'bbb_spread']]
y2 = y.loc[mask2]

# GBR on 2 features
for n_est in [50, 100]:
    for lr_val in [0.05, 0.1]:
        model = GradientBoostingRegressor(n_estimators=n_est, learning_rate=lr_val, max_depth=3, random_state=42)
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(model, X2, y2, cv=kf, scoring='r2')
        print(f"GBR(n={n_est},lr={lr_val}, vix+bbb): mean R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# Try with interaction features
X2_ext = X2.copy()
X2_ext['vix_x_bbb'] = X2_ext['vix'] * X2_ext['bbb_spread']
X2_ext['vix_sq'] = X2_ext['vix'] ** 2

for n_est in [50, 100]:
    model = GradientBoostingRegressor(n_estimators=n_est, learning_rate=0.1, max_depth=3, random_state=42)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X2_ext, y2, cv=kf, scoring='r2')
    print(f"GBR(n={n_est}, vix+bbb+interact): mean R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

PYEOF

```

## [17] tool

gdp: scale check - 80 non-null
unemployment: scale check - 80 non-null
nasdaq: scale check - 80 non-null
cpi: scale check - 80 non-null
vix: scale check - 66 non-null
bbb_spread: scale check - 71 non-null
gdp_diff: 79 non-null
unemployment_diff: 79 non-null
nasdaq_diff: 79 non-null
cpi_diff: 79 non-null
vix_diff: 65 non-null
bbb_spread_diff: 70 non-null
GBR(n=50,lr=0.05): mean R2 = 0.6394 +/- 0.0958
GBR(n=50,lr=0.1): mean R2 = 0.6022 +/- 0.1480
GBR(n=100,lr=0.05): mean R2 = 0.6044 +/- 0.1449
GBR(n=100,lr=0.1): mean R2 = 0.5505 +/- 0.1576
GBR(n=200,lr=0.05): mean R2 = 0.5639 +/- 0.1553
GBR(n=200,lr=0.1): mean R2 = 0.5086 +/- 0.1765
RF(n=50): mean R2 = 0.6282 +/- 0.1432
RF(n=100): mean R2 = 0.6296 +/- 0.1498
GBR(n=50,lr=0.05, vix+bbb): mean R2 = 0.5727 +/- 0.1295
GBR(n=50,lr=0.1, vix+bbb): mean R2 = 0.5322 +/- 0.1734
GBR(n=100,lr=0.05, vix+bbb): mean R2 = 0.5322 +/- 0.1667
GBR(n=100,lr=0.1, vix+bbb): mean R2 = 0.5066 +/- 0.1910
GBR(n=50, vix+bbb+interact): mean R2 = 0.5186 +/- 0.1894
GBR(n=100, vix+bbb+interact): mean R2 = 0.4983 +/- 0.1900


## [18] assistant

**[reasoning]**

> The VIX-only model is the best so far. Let me explore more transformations and try to get a better model, especially considering extrapolation concerns with the scenario data.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
import statsmodels.api as sm

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# The best model so far is VIX-only with GBR(n=50,lr=0.05)
# Let's explore more transformations of VIX
mask = train['vix'].notna()
X_vix_all = train.loc[mask].copy()
y_vix_all = y.loc[mask]

# Look at VIX distribution vs default rate more carefully
print("VIX stats:")
print(f"  mean={X_vix_all['vix'].mean():.2f}, std={X_vix_all['vix'].std():.2f}")
print(f"  min={X_vix_all['vix'].min():.2f}, max={X_vix_all['vix'].max():.2f}")
print(f"  scenario vix range: {scenario['vix'].min():.2f} to {scenario['vix'].max():.2f}")

# Let's try more transformation approaches
# 1. VIX squared (to capture non-linearity)
for func_name, transform in [
    ('vix', lambda x: x),
    ('log(vix)', np.log),
    ('sqrt(vix)', np.sqrt),
    ('vix^2', lambda x: x**2),
    ('1/vix', lambda x: 1/x),
]:
    X_tr = transform(X_vix_all['vix'])
    corr = np.corrcoef(X_tr, y_vix_all)[0, 1]
    print(f"  {func_name}: corr={corr:.4f}")

# Try VIX with other features that have broad coverage
# gdp, unemployment, nasdaq, cpi are available for all 80 quarters
X_full = train[['gdp', 'unemployment', 'nasdaq', 'cpi']].copy()
y_full = y.copy()

# Add VIX where available (with NaN interpolation or just use a model with missing handling)
# Instead, let's build models on different subsets

# Model A: All 80 obs with gdp, unemployment, nasdaq, cpi
print("\n--- Models on 80 obs (gdp, unemployment, nasdaq, cpi) ---")
for name, features in [
    ('base', ['gdp', 'unemployment', 'nasdaq', 'cpi']),
    ('log', ['gdp_log', 'unemployment_log', 'cpi_log']),
    ('combined', ['gdp', 'unemployment', 'cpi']),
]:
    X = train[features].copy()
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    for alpha in [0, 1, 10]:
        model = Ridge(alpha=alpha)
        scores = cross_val_score(model, X, y, cv=kf, scoring='r2')
        print(f"  {name} Ridge(a={alpha}): R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# Now let's also try GBR on the full 80
kf = KFold(n_splits=5, shuffle=True, random_state=42)
for n_est in [30, 50, 100]:
    for lr_val in [0.05, 0.1]:
        model = GradientBoostingRegressor(n_estimators=n_est, learning_rate=lr_val, max_depth=3, random_state=42)
        scores = cross_val_score(model, X_full, y, cv=kf, scoring='r2')
        print(f"  GBR(n={n_est},lr={lr_val}, full): R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# VIX + nasdaq (since nasdaq is fully available too)
mask_vix_nas = train['vix'].notna() & train['nasdaq'].notna()
X_vn = train.loc[mask_vix_nas, ['vix', 'nasdaq']]
y_vn = y.loc[mask_vix_nas]

print("\n--- VIX + nasdaq ---")
for alpha in [0, 1]:
    model = Ridge(alpha=alpha)
    kf2 = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X_vn, y_vn, cv=kf2, scoring='r2')
    print(f"  Ridge(a={alpha}): R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# Maybe the best approach is to use all available features with careful handling
# Let's try: use VIX when available, otherwise fill from model

PYEOF

```

## [19] tool

Traceback (most recent call last):
  File "<stdin>", line 52, in <module>
  File "/usr/local/lib/python3.12/site-packages/pandas/core/frame.py", line 4384, in __getitem__
    indexer = self.columns._get_indexer_strict(key, "columns")[1]
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6302, in _get_indexer_strict
    self._raise_if_missing(keyarr, indexer, axis_name)
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6352, in _raise_if_missing
    raise KeyError(f"None of [{key}] are in the [{axis_name}]")
KeyError: "None of [Index(['gdp_log', 'unemployment_log', 'cpi_log'], dtype='str')] are in the [columns]"

VIX stats:
  mean=16.54, std=5.63
  min=8.30, max=35.33
  scenario vix range: 20.02 to 38.77
  vix: corr=0.8839
  log(vix): corr=0.8389
  sqrt(vix): corr=0.8642
  vix^2: corr=0.9029
  1/vix: corr=-0.7757

--- Models on 80 obs (gdp, unemployment, nasdaq, cpi) ---
  base Ridge(a=0): R2 = 0.2718 +/- 0.0669
  base Ridge(a=1): R2 = 0.2722 +/- 0.0659
  base Ridge(a=10): R2 = 0.2754 +/- 0.0578


## [20] assistant

**[reasoning]**

> OK, the log features weren't created yet. Let me fix that and try a more comprehensive approach. The best model so far is VIX-only with GBR. Let me now focus on building a proper model with good prediction intervals, especially since the scenario pushes VIX beyond training range (up to 38.77 vs max of 35.33 in training).
> 
> Let me think about what transformation works best:
> - VIX^2 has the highest correlation (0.90)
> - But GBR on raw VIX also works well
> 
> Since the scenario pushes VIX beyond training range, I need to be careful about extrapolation. Let me try polynomial/Ridge approaches that handle extrapolation better, and also consider quantile regression for prediction intervals.
> 
> Let me build the final model:
> 1. Use VIX as the main predictor (possibly with transformation)
> 2. Consider adding bbb_spread for some additional signal
> 3. For prediction intervals, I'll use residual-based methods or quantile regression
> 4. Account for extrapolation uncertainty since scenario VIX goes beyond training range
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression, QuantileRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# Key insight: VIX^2 has highest correlation (0.90)
# Scenario VIX goes up to 38.77 vs train max 35.33 - moderate extrapolation

# Let's try multiple approaches systematically
mask = train['vix'].notna()
X_vix_raw = train.loc[mask, ['vix']]
y_vix = y.loc[mask]

# 1. Polynomial Ridge on VIX
print("=== Polynomial features ===")
for degree in [2, 3]:
    X_poly = PolynomialFeatures(degree=degree, include_bias=False).fit_transform(X_vix_raw[['vix']])
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    for alpha in [0.1, 1, 10]:
        model = Ridge(alpha=alpha)
        scores = cross_val_score(model, X_poly, y_vix, cv=kf, scoring='r2')
        print(f"  poly(d={degree}, a={alpha}): R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# 2. GBR with VIX
print("\n=== GBR ===")
for n_est in [30, 50, 100]:
    model = GradientBoostingRegressor(n_estimators=n_est, learning_rate=0.05, max_depth=2, random_state=42)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X_vix_raw, y_vix, cv=kf, scoring='r2')
    print(f"  GBR(n={n_est}): R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# 3. Simple linear regression (VIX only)
print("\n=== Linear Regression ===")
model = LinearRegression()
model.fit(X_vix_raw, y_vix)
print(f"  Coeff: {model.coef_[0]:.6f}, Intercept: {model.intercept_:.6f}")
y_pred_train = model.predict(X_vix_raw)
residuals = y_vix.values - y_pred_train
print(f"  In-sample R2: {model.score(X_vix_raw, y_vix):.4f}")
print(f"  Residual std: {np.std(residuals):.6f}")

# Fit statsmodels for detailed inference
y_sm = sm.add_constant(X_vix_raw['vix'].values)
ols_model = sm.OLS(y_vix.values, y_sm).fit()
print(f"\n  OLS summary:")
print(ols_model.summary().as_text())

# 4. Try VIX + bbb with GBR
mask2 = train['vix'].notna() & train['bbb_spread'].notna()
X2 = train.loc[mask2, ['vix', 'bbb_spread']]
y2 = y.loc[mask2]

print("\n=== VIX + BBB ===")
for n_est in [30, 50]:
    model = GradientBoostingRegressor(n_estimators=n_est, learning_rate=0.05, max_depth=2, random_state=42)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X2, y2, cv=kf, scoring='r2')
    print(f"  GBR(n={n_est}): R2 = {scores.mean():.4f} +/- {scores.std():.4f}")

# 5. Quantile regression for intervals
print("\n=== Quantile Regression (VIX) ===")
for q in [0.025, 0.5, 0.975]:
    model = QuantileRegressor(quantile=q, alpha=1, solver='highs')
    model.fit(X_vix_raw, y_vix)
    pred = model.predict(X_vix_raw[['vix']])
    mae = np.mean(np.abs(y_vix.values - pred))
    print(f"  Q{q}: MAE = {mae:.6f}, R2 = {1 - np.sum((y_vix.values - pred)**2)/np.sum((y_vix.values - y_vix.mean())**2):.4f}")

PYEOF

```

## [21] tool

=== Polynomial features ===
  poly(d=2, a=0.1): R2 = 0.7240 +/- 0.1672
  poly(d=2, a=1): R2 = 0.7244 +/- 0.1674
  poly(d=2, a=10): R2 = 0.7271 +/- 0.1694
  poly(d=3, a=0.1): R2 = 0.7240 +/- 0.1635
  poly(d=3, a=1): R2 = 0.7233 +/- 0.1621
  poly(d=3, a=10): R2 = 0.7224 +/- 0.1614

=== GBR ===
  GBR(n=30): R2 = 0.6508 +/- 0.0759
  GBR(n=50): R2 = 0.6645 +/- 0.0812
  GBR(n=100): R2 = 0.6420 +/- 0.1125

=== Linear Regression ===
  Coeff: 0.003993, Intercept: -0.028084
  In-sample R2: 0.7812
  Residual std: 0.011796

  OLS summary:
                            OLS Regression Results                            
==============================================================================
Dep. Variable:                      y   R-squared:                       0.781
Model:                            OLS   Adj. R-squared:                  0.778
Method:                 Least Squares   F-statistic:                     228.5
Date:                Tue, 10 Nov 2026   Prob (F-statistic):           8.51e-23
Time:                        07:45:41   Log-Likelihood:                 199.39
No. Observations:                  66   AIC:                            -394.8
Df Residuals:                      64   BIC:                            -390.4
Df Model:                           1                                         
Covariance Type:            nonrobust                                         
==============================================================================
                 coef    std err          t      P>|t|      [0.025      0.975]
------------------------------------------------------------------------------
const         -0.0281      0.005     -6.092      0.000      -0.037      -0.019
x1             0.0040      0.000     15.117      0.000       0.003       0.005
==============================================================================
Omnibus:                        2.691   Durbin-Watson:                   2.041
Prob(Omnibus):                  0.260   Jarque-Bera (JB):                2.060
Skew:                           0.182   Prob(JB):                        0.357
Kurtosis:                       3.786   Cond. No.                         54.7
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.

=== VIX + BBB ===
  GBR(n=30): R2 = 0.6383 +/- 0.0693
  GBR(n=50): R2 = 0.6322 +/- 0.0858

=== Quantile Regression (VIX) ===
  Q0.025: MAE = 0.027722, R2 = -1.2054
  Q0.5: MAE = 0.009167, R2 = 0.7069
  Q0.975: MAE = 0.071127, R2 = -7.7035


## [22] assistant

**[reasoning]**

> Let me now build the complete model and predictions. The VIX-only linear regression looks promising with R² = 0.78. However, I need to:
> 
> 1. Handle the extrapolation issue (scenario VIX goes up to 38.77 vs train max 35.33)
> 2. Get proper prediction intervals that account for extrapolation uncertainty
> 3. Consider using additional features where available
> 
> Let me think about a good approach:
> 
> 1. Use VIX as the primary predictor (strongest correlation)
> 2. Add bbb_spread as a secondary predictor where available
> 3. Build a model that captures non-linearity (maybe VIX^2 or polynomial)
> 4. For prediction intervals, I should:
>    - Use the residual distribution from training
>    - Account for parameter uncertainty
>    - Add extra uncertainty for extrapolation (scenario VIX goes beyond training range)
> 
> Let me also think about whether we can use more data. The issue is VIX and bbb_spread don't have complete coverage. But perhaps I can use a multi-stage approach or imputation.
> 
> Actually, let me reconsider. The best R² in cross-validation is around 0.72 with polynomial features on VIX. Let me try to build a more robust model and create proper prediction intervals.
> 
> For the prediction intervals, I should:
> 1. Use the residual standard error from training
> 2. Account for uncertainty in predictions (t-distribution based)
> 3. Add extra margin for extrapolation beyond training range
> 
> Let me build this properly now.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
from scipy import stats

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# Strategy: Build a model using VIX as the main driver
# VIX has strongest correlation (0.88-0.90)
# Also explore using VIX + bbb_spread (71 rows)

# Best approach: OLS with VIX, possibly polynomial
# For extrapolation: add extra uncertainty

mask_vix = train['vix'].notna()
X_vix = train.loc[mask_vix, ['vix']].values
y_vix = y.loc[mask_vix].values

# Try various models on VIX and select best by CV R2
print("=== Model Selection ===")

# 1. Linear OLS
model_ols = sm.OLS(y_vix, sm.add_constant(X_vix)).fit()
print(f"Linear OLS: R2={model_ols.rsquared:.4f}, RMSE={np.sqrt(model_ols.mse_resid):.6f}")

# 2. Quadratic (VIX + VIX^2)
X_quad = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X_vix)
model_quad = sm.OLS(y_vix, sm.add_constant(X_quad)).fit()
print(f"Quadratic OLS: R2={model_quad.rsquared:.4f}, RMSE={np.sqrt(model_quad.mse_resid):.6f}")

# 3. Cubic OLS
X_cub = PolynomialFeatures(degree=3, include_bias=False).fit_transform(X_vix)
model_cub = sm.OLS(y_vix, sm.add_constant(X_cub)).fit()
print(f"Cubic OLS: R2={model_cub.rsquared:.4f}, RMSE={np.sqrt(model_cub.mse_resid):.6f}")

# CV for polynomial models
for degree in [1, 2, 3]:
    X_poly = PolynomialFeatures(degree=degree, include_bias=False).fit_transform(X_vix)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    preds = []
    for train_idx, test_idx in kf.split(X_poly):
        X_tr, X_te = X_poly[train_idx], X_poly[test_idx]
        y_tr, y_te = y_vix[train_idx], y_vix[test_idx]
        model_cv = sm.OLS(y_tr, sm.add_constant(X_te)).fit()  # Bug - should use X_te
        model_cv = sm.OLS(y_tr, sm.add_constant(X_tr)).fit()
        preds.append(y_te - model_cv.predict(sm.add_constant(X_te)))
    res = np.concatenate(preds)
    print(f"  CV degree {degree}: RMSE={np.std(res):.6f}")

# Let's also try VIX + bbb_spread
mask2 = train['vix'].notna() & train['bbb_spread'].notna()
X2 = train.loc[mask2, ['vix', 'bbb_spread']].values
y2 = y.loc[mask2].values

model2 = sm.OLS(y2, sm.add_constant(X2)).fit()
print(f"\nVIX+BBB OLS: R2={model2.rsquared:.4f}, RMSE={np.sqrt(model2.mse_resid):.6f}")

# Polynomial with 2 features
X2_poly = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X2)
model2_poly = sm.OLS(y2, sm.add_constant(X2_poly)).fit()
print(f"VIX+BBB Poly OLS: R2={model2_poly.rsquared:.4f}, RMSE={np.sqrt(model2_poly.mse_resid):.6f}")

# GBR on VIX+BBB
for n_est in [30, 50]:
    model_gbr = GradientBoostingRegressor(n_estimators=n_est, learning_rate=0.05, 
                                           max_depth=3, random_state=42)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model_gbr, X2, y2, cv=kf, scoring='r2')
    print(f"GBR VIX+BBB(n={n_est}): R2={scores.mean():.4f} +/- {scores.std():.4f}")

# Compare predictions on VIX range
print("\n=== Prediction at scenario VIX values ===")
vix_train_min, vix_train_max = X_vix.min(), X_vix.max()
vix_scenario = scenario['vix'].values

print(f"VIX train range: [{vix_train_min:.2f}, {vix_train_max:.2f}]")
print(f"VIX scenario range: [{vix_scenario.min():.2f}, {vix_scenario.max():.2f}]")
print(f"Extrapolation: VIX goes {vix_scenario.max() - vix_train_max:.2f} beyond training max")

# Show predictions at different VIX levels
vix_test = np.linspace(vix_train_min - 2, vix_train_max + 5, 30)
y_pred_ols = model_ols.predict(sm.add_constant(vix_test.reshape(-1, 1)))
y_pred_quad = model_quad.predict(sm.add_constant(PolynomialFeatures(degree=2, include_bias=False).fit_transform(vix_test.reshape(-1, 1))))

print("\nVIX | LinearPred | QuadPred")
for i in range(0, len(vix_test), 5):
    print(f"{vix_test[i]:.2f} | {y_pred_ols[i]:.4f} | {y_pred_quad[i]:.4f}")

PYEOF

```

## [23] tool

Traceback (most recent call last):
  File "<stdin>", line 50, in <module>
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 921, in __init__
    super().__init__(endog, exog, missing=missing,
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 746, in __init__
    super().__init__(endog, exog, missing=missing,
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 200, in __init__
    super().__init__(endog, exog, **kwargs)
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 270, in __init__
    super().__init__(endog, exog, **kwargs)
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 95, in __init__
    self.data = self._handle_data(endog, exog, missing, hasconst,
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 135, in _handle_data
    data = handle_data(endog, exog, missing, hasconst, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/data.py", line 694, in handle_data
    return klass(endog, exog=exog, missing=missing, hasconst=hasconst, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/data.py", line 91, in __init__
    self._check_integrity()
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/data.py", line 450, in _check_integrity
    raise ValueError("endog and exog matrices are different sizes")
ValueError: endog and exog matrices are different sizes

=== Model Selection ===
Linear OLS: R2=0.7812, RMSE=0.011979
Quadratic OLS: R2=0.8157, RMSE=0.011082
Cubic OLS: R2=0.8186, RMSE=0.011083


## [24] assistant

**[reasoning]**

> Let me fix the bug and explore more. The linear VIX model is good (R2=0.78), quadratic is better (R2=0.82). Let me build the final model now.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# Best model so far: Quadratic OLS on VIX (R2=0.8157, RMSE=0.011)
mask_vix = train['vix'].notna()
X_vix = train.loc[mask_vix, ['vix']].values
y_vix = y.loc[mask_vix].values

# Fit quadratic model
X_quad_full = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X_vix)
model_quad = sm.OLS(y_vix, sm.add_constant(X_quad_full)).fit()

# Also fit VIX+BBB model (71 obs)
mask2 = train['vix'].notna() & train['bbb_spread'].notna()
X2 = train.loc[mask2, ['vix', 'bbb_spread']].values
y2 = y.loc[mask2].values

# Quadratic for 2 features
X2_poly = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X2)
model2_poly = sm.OLS(y2, sm.add_constant(X2_poly)).fit()

print("=== Model comparison ===")
print(f"VIX quadratic: R2={model_quad.rsquared:.4f}, adj_R2={model_quad.rsquared_adj:.4f}, RMSE={np.sqrt(model_quad.mse_resid):.6f}")
print(f"VIX+BBB quadratic: R2={model2_poly.rsquared:.4f}, adj_R2={model2_poly.rsquared_adj:.4f}, RMSE={np.sqrt(model2_poly.mse_resid):.6f}")

# Cross-validation with proper implementation
print("\n=== Proper CV ===")
for name, X_data, y_data in [("VIX quad", X_quad_full, y_vix), ("VIX+BBB quad", X2_poly, y2)]:
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    oos_preds = np.zeros(len(y_data))
    for fold, (train_idx, test_idx) in enumerate(kf.split(X_data)):
        X_tr, X_te = X_data[train_idx], X_data[test_idx]
        y_tr, y_te = y_data[train_idx], y_data[test_idx]
        m = sm.OLS(y_tr, sm.add_constant(X_te)).fit()
        # Bug fix: need X_te properly for prediction
        pass
    
    # Let's do it right
    oos_preds = np.zeros(len(y_data))
    for fold, (train_idx, test_idx) in enumerate(kf.split(X_data)):
        X_tr, X_te = X_data[train_idx], X_data[test_idx]
        y_tr, y_te = y_data[train_idx], y_data[test_idx]
        m = sm.OLS(y_tr, sm.add_constant(X_tr)).fit()
        oos_preds[test_idx] = m.predict(sm.add_constant(X_te))
    
    residuals = y_data - oos_preds
    rmse_cv = np.sqrt(np.mean(residuals**2))
    r2_cv = 1 - np.sum(residuals**2) / np.sum((y_data - y_data.mean())**2)
    print(f"{name}: CV R2={r2_cv:.4f}, CV RMSE={rmse_cv:.6f}")

# Check residuals of VIX+BBB model
y2_pred = model2_poly.predict(sm.add_constant(X2_poly))
resid2 = y2 - y2_pred
print(f"\nVIX+BBB residual stats:")
print(f"  Mean: {np.mean(resid2):.6f}, Std: {np.std(resid2):.6f}")
print(f"  Min: {np.min(resid2):.6f}, Max: {np.max(resid2):.6f}")

# Now let's also check: do residuals correlate with anything (like time trend)?
vix_train_df = train.loc[mask2, ['vix', 'bbb_spread']].reset_index()
y2_pred_full = model2_poly.predict(sm.add_constant(X2_poly))
resid_full = y2 - y2_pred_full
print(f"  Residual vs quarter corr: {np.corrcoef(train.loc[mask2, 'quarter'].values, resid_full)[0,1]:.4f}")
print(f"  Residual vs VIX corr: {np.corrcoef(X_vix, resid_full)[0,1]:.4f}")

# Check if residuals show any pattern
print("\n  Residuals distribution (sorted by VIX):")
sort_idx = np.argsort(X_vix.flatten())
for i in range(0, len(sort_idx), 10):
    print(f"    VIX={X_vix[sort_idx[i]][0]:.2f}, resid={resid_full[sort_idx[i]]:.4f}")

PYEOF

```

## [25] tool

Traceback (most recent call last):
  File "<stdin>", line 43, in <module>
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 921, in __init__
    super().__init__(endog, exog, missing=missing,
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 746, in __init__
    super().__init__(endog, exog, missing=missing,
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 200, in __init__
    super().__init__(endog, exog, **kwargs)
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 270, in __init__
    super().__init__(endog, exog, **kwargs)
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 95, in __init__
    self.data = self._handle_data(endog, exog, missing, hasconst,
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 135, in _handle_data
    data = handle_data(endog, exog, missing, hasconst, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/data.py", line 694, in handle_data
    return klass(endog, exog=exog, missing=missing, hasconst=hasconst, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/data.py", line 91, in __init__
    self._check_integrity()
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/data.py", line 450, in _check_integrity
    raise ValueError("endog and exog matrices are different sizes")
ValueError: endog and exog matrices are different sizes

=== Model comparison ===
VIX quadratic: R2=0.8157, adj_R2=0.8098, RMSE=0.011082
VIX+BBB quadratic: R2=0.8196, adj_R2=0.8046, RMSE=0.011234

=== Proper CV ===


## [26] assistant

**[reasoning]**

> The CV code has an issue. Let me fix and continue the analysis.
> 
> The VIX+BBB quadratic model gives slightly better R2 than VIX-only (0.8196 vs 0.8157), with similar RMSE. Let me think about what model to use.
> 
> Key observations:
> - VIX has correlation ~0.88 with default rate
> - VIX^2 has correlation ~0.90 
> - Quadratic OLS on VIX gives R2=0.8157, RMSE=0.011
> - Adding bbb_spread improves slightly to R2=0.8196, RMSE=0.011
> 
> For the scenario, VIX goes up to 38.77 (vs train max 35.33). That's moderate extrapolation.
> 
> I need to:
> 1. Build the best model
> 2. Make predictions for scenario quarters
> 3. Calculate 95% prediction intervals that account for:
>    - Model parameter uncertainty
>    - Residual variance
>    - Extrapolation uncertainty
> 
> Let me think about the prediction interval. For OLS with new x values:
> - Prediction variance = σ² * (1 + x'*(X'X)^(-1)*x)
> - But this doesn't account for extrapolation uncertainty well
> 
> A simpler approach: use the residual standard error as the main component of the interval, plus some margin for extrapolation.
> 
> Let me proceed with a complete solution using statsmodels and proper prediction intervals.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# Strategy: Use VIX + bbb_spread as predictors
# Both are important macroeconomic indicators for default rates
# VIX (volatility) and BBB spread (credit risk premium)

mask = train['vix'].notna() & train['bbb_spread'].notna()
X_data = train.loc[mask, ['vix', 'bbb_spread']].values
y_data = y.loc[mask].values

# Quadratic model with VIX and BBB spread
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X_data)

# Fit OLS model
model = sm.OLS(y_data, sm.add_constant(X_poly)).fit()
print("VIX + BBB Spread (Quadratic) Model:")
print(model.summary())

# Get prediction interval for training data
y_pred_train = model.predict(sm.add_constant(X_poly))
residuals = y_data - y_pred_train
sigma_resid = np.std(residuals, ddof=1)
print(f"\nResidual std: {sigma_resid:.6f}")

# Check residual patterns
print(f"Residuals vs VIX correlation: {np.corrcoef(X_data[:, 0], residuals)[0, 1]:.4f}")
print(f"Residuals vs BBB spread correlation: {np.corrcoef(X_data[:, 1], residuals)[0, 1]:.4f}")
print(f"Residuals vs quarter correlation: {np.corrcoef(train.loc[mask, 'quarter'].values, residuals)[0, 1]:.4f}")

# Now check: what does the scenario look like in terms of extrapolation?
scenario_mask = (scenario['vix'].notna()) & (scenario['bbb_spread'].notna())
X_scen = scenario.loc[scenario_mask, ['vix', 'bbb_spread']].values
y_scen_pred = model.predict(sm.add_constant(poly.transform(X_scen)))

print(f"\n=== Scenario Predictions ===")
for i in range(len(scenario)):
    vix_s = scenario['vix'].iloc[i]
    bbb_s = scenario['bbb_spread'].iloc[i]
    pred_i = y_scen_pred[i] if i < len(y_scen_pred) else np.nan
    vix_tr_min, vix_tr_max = X_data[:, 0].min(), X_data[:, 0].max()
    bbb_tr_min, bbb_tr_max = X_data[:, 1].min(), X_data[:, 1].max()
    extrapolation = f"VIX:{'above' if vix_s > vix_tr_max else 'ok'}, BBB:{'above' if bbb_s > bbb_tr_max else 'ok'}"
    print(f"  Q{i}: VIX={vix_s:.2f}, BBB={bbb_s:.4f}, pred={pred_i:.4f} [{extrapolation}]")

# Try different model specifications
print("\n=== Alternative models ===")

# Just VIX quadratic
mask_vix = train['vix'].notna()
X_vix = train.loc[mask_vix, ['vix']].values
y_vix_data = y.loc[mask_vix].values

X_vix_quad = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X_vix)
model_vix = sm.OLS(y_vix_data, sm.add_constant(X_vix_quad)).fit()
print(f"VIX quadratic: R2={model_vix.rsquared:.4f}, RMSE={np.sqrt(model_vix.mse_resid):.6f}")

# VIX only - check CV
from sklearn.model_selection import cross_val_predict
for n_split in [5, 10]:
    kf = KFold(n_splits=n_split, shuffle=True, random_state=42)
    cv_pred = cross_val_predict(sm.OLS(), X_vix, y_vix_data, cv=kf)
    resid = y_vix_data - cv_pred
    print(f"VIX quad CV(n_splits={n_split}): RMSE={np.std(resid, ddof=1):.6f}, R2={1 - np.sum(resid**2)/np.sum((y_vix_data-y_vix_data.mean())**2):.4f}")

# Compare: does adding BBB help out-of-sample?
kf = KFold(n_splits=5, shuffle=True, random_state=42)
X_poly2 = poly.transform(X_data)
cv_pred_2 = cross_val_predict(model, sm.add_constant(X_poly2), y_data, cv=kf)
resid_2 = y_data - cv_pred_2
print(f"VIX+BBB quad CV: RMSE={np.std(resid_2, ddof=1):.6f}, R2={1 - np.sum(resid_2**2)/np.sum((y_data-y_data.mean())**2):.4f}")

# Try cubic for VIX
X_vix_cub = PolynomialFeatures(degree=3, include_bias=False).fit_transform(X_vix)
model_vix_cub = sm.OLS(y_vix_data, sm.add_constant(X_vix_cub)).fit()
print(f"\nVIX cubic: R2={model_vix_cub.rsquared:.4f}, adj_R2={model_vix_cub.rsquared_adj:.4f}")
print(f"VIX+BBB cubic:")
poly2 = PolynomialFeatures(degree=3, include_bias=False)
X_poly3 = poly2.transform(X_data)
model3 = sm.OLS(y_data, sm.add_constant(X_poly3)).fit()
print(f"  R2={model3.rsquared:.4f}, adj_R2={model3.rsquared_adj:.4f}")

# CV for cubic
cv_pred_vix_cub = cross_val_predict(model_vix_cub, sm.add_constant(X_vix_cub), y_vix_data, cv=kf)
resid_vix_cub = y_vix_data - cv_pred_vix_cub
cv_pred3 = cross_val_predict(model3, sm.add_constant(X_poly3), y_data, cv=kf)
resid3 = y_data - cv_pred3
print(f"\nVIX cubic CV: RMSE={np.std(resid_vix_cub, ddof=1):.6f}")
print(f"VIX+BBB cubic CV: RMSE={np.std(resid3, ddof=1):.6f}")

PYEOF

```

## [27] tool

Traceback (most recent call last):
  File "<stdin>", line 71, in <module>
TypeError: OLS.__init__() missing 1 required positional argument: 'endog'

VIX + BBB Spread (Quadratic) Model:
                            OLS Regression Results                            
==============================================================================
Dep. Variable:                      y   R-squared:                       0.820
Model:                            OLS   Adj. R-squared:                  0.805
Method:                 Least Squares   F-statistic:                     54.52
Date:                Tue, 10 Nov 2026   Prob (F-statistic):           4.79e-21
Time:                        07:47:40   Log-Likelihood:                 205.76
No. Observations:                  66   AIC:                            -399.5
Df Residuals:                      60   BIC:                            -386.4
Df Model:                           5                                         
Covariance Type:            nonrobust                                         
==============================================================================
                 coef    std err          t      P>|t|      [0.025      0.975]
------------------------------------------------------------------------------
const          0.0126      0.015      0.866      0.390      -0.016       0.042
x1            -0.0005      0.001     -0.361      0.720      -0.003       0.002
x2            -0.0013      0.011     -0.125      0.901      -0.023       0.020
x3          8.162e-05   4.64e-05      1.757      0.084   -1.13e-05       0.000
x4             0.0008      0.001      1.005      0.319      -0.001       0.003
x5            -0.0043      0.005     -0.940      0.351      -0.013       0.005
==============================================================================
Omnibus:                        2.086   Durbin-Watson:                   1.991
Prob(Omnibus):                  0.352   Jarque-Bera (JB):                1.329
Skew:                           0.264   Prob(JB):                        0.515
Kurtosis:                       3.451   Cond. No.                     4.33e+03
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
[2] The condition number is large, 4.33e+03. This might indicate that there are
strong multicollinearity or other numerical problems.

Residual std: 0.010793
Residuals vs VIX correlation: 0.0000
Residuals vs BBB spread correlation: 0.0000
Residuals vs quarter correlation: 0.1093

=== Scenario Predictions ===
  Q0: VIX=20.02, BBB=1.1336, pred=0.0470 [VIX:ok, BBB:ok]
  Q1: VIX=21.74, BBB=1.4777, pred=0.0556 [VIX:ok, BBB:ok]
  Q2: VIX=23.62, BBB=1.8218, pred=0.0654 [VIX:ok, BBB:ok]
  Q3: VIX=25.65, BBB=2.1660, pred=0.0767 [VIX:ok, BBB:ok]
  Q4: VIX=27.86, BBB=2.5101, pred=0.0899 [VIX:ok, BBB:ok]
  Q5: VIX=30.26, BBB=2.8542, pred=0.1054 [VIX:ok, BBB:ok]
  Q6: VIX=32.87, BBB=3.1983, pred=0.1239 [VIX:ok, BBB:above]
  Q7: VIX=35.70, BBB=3.5425, pred=0.1457 [VIX:above, BBB:above]
  Q8: VIX=38.77, BBB=3.8866, pred=0.1717 [VIX:above, BBB:above]

=== Alternative models ===
VIX quadratic: R2=0.8157, RMSE=0.011082


## [28] assistant

**[reasoning]**

> The quadratic VIX+BBB model looks good. The predictions increase monotonically as VIX and BBB spread increase, which makes economic sense. The scenario has extrapolation at the higher end (VIX up to 38.77 vs max ~35, BBB up to 3.89 vs max ~3).
> 
> Now I need to:
> 1. Build a robust model
> 2. Create proper prediction intervals that account for extrapolation uncertainty
> 3. Write predictions.csv
> 
> Key observations:
> - The model has good in-sample fit (R2=0.82)
> - Residuals are well-behaved (no correlation with predictors or time)
> - Scenario has moderate extrapolation at the high end
> - Need to account for parameter uncertainty AND extra uncertainty for extrapolation
> 
> For prediction intervals, I should use:
> 1. Standard statistical prediction interval from the model (accounts for parameter + residual uncertainty)
> 2. Possibly inflate the interval to account for extrapolation beyond training range
> 
> Let me also check if there's a time trend or autocorrelation in the residuals that might affect uncertainty.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
from scipy import stats

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# Use VIX + bbb_spread quadratic model
mask = train['vix'].notna() & train['bbb_spread'].notna()
X_data = train.loc[mask, ['vix', 'bbb_spread']].values
y_data = y.loc[mask].values

poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X_data)

# Fit OLS model
model = sm.OLS(y_data, sm.add_constant(X_poly)).fit()

# Residuals and diagnostics
residuals = y_data - model.predict(sm.add_constant(X_poly))
sigma_hat = np.sqrt(model.mse_resid)
print(f"Residual std (sigma): {sigma_hat:.6f}")

# Check for autocorrelation in residuals
acf_vals = np.correlate(residuals, residuals, mode='full')
acf_vals = acf_vals[acf_vals.shape[0]//2:] / acf_vals[acf_vals.shape[0]//2]
print(f"\nACF lag 1: {acf_vals[1]:.4f}, lag 2: {acf_vals[2]:.4f}, lag 3: {acf_vals[3]:.4f}")

# Breusch-Godfrey test for autocorrelation
from statsmodels.stats.diagnostic import acorr_breusch_godfrey
bg_test = acorr_breusch_godfrey(model.resid, model.model.exog, lags=1)
print(f"BG test (lag 1): F-stat={bg_test[0]:.4f}, p-value={bg_test[1]:.4f}")

# Check Cook's distance for influential points
influence = model.get_influence()
cooks_d = influence.cooks_distance[0]
print(f"\nCook's D max: {np.max(cooks_d):.4f}")
# Points with Cook's D > 4/n are potentially influential
threshold = 4 / len(y_data)
print(f"Influential threshold (4/n): {threshold:.4f}")
influential = np.where(cooks_d > threshold)[0]
print(f"Influential points: {influential}")

# Get standard errors for prediction at new points
X_scen = scenario[['vix', 'bbb_spread']].values
X_poly_scen = poly.transform(X_scen)

# Point predictions
y_pred = model.predict(sm.add_constant(X_poly_scen))
print(f"\nPoint predictions:")
for i in range(len(scenario)):
    print(f"  Q{scenario['quarter'].iloc[i]}: {y_pred[i]:.4f}")

# Prediction intervals
# Standard error of prediction = sqrt(sigma^2 * (1 + x^T (X^T X)^-1 x))
# But we need to account for extrapolation

# Get leverage values and prediction SEs
X_scen_full = sm.add_constant(X_poly_scen)
cov_beta = model.cov_params()

se_pred = []
for i in range(len(X_scen_full)):
    x_i = X_scen_full.iloc[i].values if hasattr(X_scen_full, 'iloc') else X_scen_full[i]
    # Actually need to use numpy array
    pred_var = sigma_hat**2 * (1 + x_i @ cov_beta.values @ x_i)
    se_pred.append(np.sqrt(pred_var))

se_pred = np.array(se_pred)
t_crit = stats.t.ppf(0.975, df=model.df_resid)

# Standard prediction intervals
lower_std = y_pred - t_crit * se_pred
upper_std = y_pred + t_crit * se_pred

print(f"\n=== Standard 95% Prediction Intervals ===")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    print(f"  Q{q}: [{lower_std[i]:.4f}, {y_pred[i]:.4f}, {upper_std[i]:.4f}]")

# Check what fraction of scenario is extrapolation
vix_train = X_data[:, 0]
bbb_train = X_data[:, 1]

for i in range(len(scenario)):
    vix_s = X_scen[i, 0]
    bbb_s = X_scen[i, 1]
    dist_vix = max(0, vix_s - vix_train.max()) / (vix_train.max() - vix_train.min())
    dist_bbb = max(0, bbb_s - bbb_train.max()) / (bbb_train.max() - bbb_train.min())
    max_dist = max(dist_vix, dist_bbb)
    print(f"\n  Q{i}: extrapolation distance (normalized): VIX={dist_vix:.3f}, BBB={dist_bbb:.3f}, max={max_dist:.3f}")

# Let's also try a simpler approach - use quantile regression or 
# inflation factor for extrapolation

# Approach: inflate prediction interval by (1 + extrapolation_factor)
# This accounts for increased uncertainty when extrapolating

print("\n=== Inflated Prediction Intervals ===")
for inflation in [1.0, 1.2, 1.5, 2.0]:
    for i in range(len(scenario)):
        q = scenario['quarter'].iloc[i]
        half_width = t_crit * se_pred[i] * inflation
        lower_i = y_pred[i] - half_width
        upper_i = y_pred[i] + half_width
        print(f"  Q{q} (infl={inflation}): [{lower_i:.4f}, {y_pred[i]:.4f}, {upper_i:.4f}]")
    print()

PYEOF

```

## [29] tool

Traceback (most recent call last):
  File "<stdin>", line 36, in <module>
  File "/usr/local/lib/python3.12/site-packages/pandas/util/_decorators.py", line 220, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
TypeError: acorr_breusch_godfrey() got an unexpected keyword argument 'lags'

Residual std (sigma): 0.011234

ACF lag 1: -0.0009, lag 2: 0.1113, lag 3: -0.1985


## [30] assistant

**[reasoning]**

> The model is giving reasonable predictions and intervals. Let me now think about the prediction interval more carefully.
> 
> Looking at the data:
> - The VIX+BBB quadratic model has good fit (R²=0.82)
> - The residual std is about 1.1% 
> - The scenario has some extrapolation: VIX goes up to 38.77 (beyond train max of ~35), BBB goes up to 3.89 (beyond train max of ~3.06)
> 
> Key considerations for the prediction interval:
> 1. Standard error from the model (accounts for parameter uncertainty and residual variance)
> 2. Extrapolation uncertainty - when predicting outside the training range
> 
> Let me think about this more carefully:
> - The quadratic model will extrapolate as a parabola beyond the training range
> - Since we're going past VIX=35 and BBB=3, the quadratic term might cause overly aggressive predictions
> - We should account for model misspecification under extrapolation
> 
> A good approach:
> 1. Use the parametric prediction intervals from the model as a base
> 2. Inflate them to account for extrapolation uncertainty
> 3. Alternatively, use a bootstrap/resampling approach
> 
> Let me also check if there are better features to include that could improve predictions, particularly ones available for all 80 quarters.
> 
> Actually, let me reconsider the approach. The problem says:
> - "Some macro series are blank for early quarters (they began later)" - we've handled this
> - "Not all nine series necessarily matter" - confirmed, VIX and BBB are key
> - "the ones that do may enter through a transformation rather than as a raw level" - we're using quadratic transforms
> 
> Let me refine the model and create proper prediction intervals that account for:
> 1. Residual variability (σ)
> 2. Parameter uncertainty  
> 3. Extrapolation uncertainty
> 
> I'll use a comprehensive approach with bootstrap resampling for the intervals.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# Use VIX + bbb_spread quadratic model (best combination)
mask = train['vix'].notna() & train['bbb_spread'].notna()
X_data = train.loc[mask, ['vix', 'bbb_spread']].values
y_data = y.loc[mask].values

poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X_data)

# Fit OLS model  
model = sm.OLS(y_data, sm.add_constant(X_poly)).fit()

print(f"Model R²: {model.rsquared:.4f}, Adjusted R²: {model.rsquared_adj:.4f}")
print(f"Residual std: {np.sqrt(model.mse_resid):.6f}")
print(f"n observations: {len(y_data)}")

# Get prediction at scenario points
X_scen = scenario[['vix', 'bbb_spread']].values
X_poly_scen = poly.transform(X_scen)

# Point predictions
y_pred = model.predict(sm.add_constant(X_poly_scen))

print(f"\n=== Point Predictions ===")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    print(f"  Q{q}: {y_pred[i]:.6f}")

# === Prediction Intervals ===
# Method: Bootstrap residuals approach + extrapolation adjustment

# Step 1: Get model parameter distribution via bootstrap
n_boot = 5000
np.random.seed(42)

# Store predictions and intervals for each bootstrap sample
boot_preds = np.zeros((n_boot, len(scenario)))

for b in range(n_boot):
    # Resample residuals with replacement
    resid_boot = np.random.choice(model.resid, size=len(y_data))
    
    # Create bootstrap responses
    y_boot = model.predict(sm.add_constant(X_poly)) + resid_boot
    
    # Refit model
    try:
        model_boot = sm.OLS(y_boot, sm.add_constant(X_poly)).fit()
        boot_preds[b, :] = model_boot.predict(sm.add_constant(X_poly_scen))
    except:
        boot_preds[b, :] = y_pred

# Compute prediction intervals from bootstrap distribution
y_lower_boot = np.percentile(boot_preds, 2.5, axis=0)
y_upper_boot = np.percentile(boot_preds, 97.5, axis=0)
y_mean_boot = np.mean(boot_preds, axis=0)

print(f"\n=== Bootstrap 95% Prediction Intervals (parameter uncertainty only) ===")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    print(f"  Q{q}: [{y_lower_boot[i]:.4f}, {y_mean_boot[i]:.4f}, {y_upper_boot[i]:.4f}]")

# Step 2: Add residual (noise) to intervals
# Total prediction interval = sqrt(bootstrap_var + sigma^2)
sigma_resid = np.sqrt(model.mse_resid)
boot_std = np.std(boot_preds, axis=0)

# Total uncertainty: parameter + observation
total_std = np.sqrt(boot_std**2 + sigma_resid**2)

# Using t-distribution
t_crit = stats.t.ppf(0.975, df=model.df_resid)
lower_t = y_pred - t_crit * total_std
upper_t = y_pred + t_crit * total_std

print(f"\n=== Combined Prediction Intervals (param + noise) ===")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    print(f"  Q{q}: [{lower_t[i]:.4f}, {y_pred[i]:.4f}, {upper_t[i]:.4f}]")

# Also check: what fraction of scenario is extrapolation?
vix_train = X_data[:, 0]
bbb_train = X_data[:, 1]

print(f"\n=== Extrapolation Analysis ===")
for i in range(len(scenario)):
    vix_s = X_scen[i, 0]
    bbb_s = X_scen[i, 1]
    
    # Max distance in Mahalanobis-like sense (max of individual distances)
    vix_min, vix_max = vix_train.min(), vix_train.max()
    bbb_min, bbb_max = bbb_train.min(), bbb_train.max()
    
    vix_margin = max(0, vix_s - vix_max) / (vix_max - vix_min)
    bbb_margin = max(0, bbb_s - bbb_max) / (bbb_max - bbb_min)
    max_margin = max(vix_margin, bbb_margin)
    
    # How extreme is each feature relative to training range
    vix_z = (vix_s - np.mean(vix_train)) / np.std(vix_train)
    bbb_z = (bbb_s - np.mean(bbb_train)) / np.std(bbb_train)
    
    print(f"  Q{i}: vix={vix_s:.2f} (z={vix_z:.2f}), bbb={bbb_s:.4f} (z={bbb_z:.2f})")
    print(f"        extrapolation: vix={vix_margin:.2%}, bbb={bbb_margin:.2%}")

PYEOF

```

## [31] tool

Model R²: 0.8196, Adjusted R²: 0.8046
Residual std: 0.011234
n observations: 66

=== Point Predictions ===
  Q81: 0.046989
  Q82: 0.055587
  Q83: 0.065370
  Q84: 0.076673
  Q85: 0.089880
  Q86: 0.105439
  Q87: 0.123860
  Q88: 0.145734
  Q89: 0.171743

=== Bootstrap 95% Prediction Intervals (parameter uncertainty only) ===
  Q81: [0.0409, 0.0471, 0.0532]
  Q82: [0.0506, 0.0557, 0.0609]
  Q83: [0.0604, 0.0654, 0.0708]
  Q84: [0.0706, 0.0767, 0.0832]
  Q85: [0.0810, 0.0900, 0.0993]
  Q86: [0.0918, 0.1056, 0.1203]
  Q87: [0.1034, 0.1240, 0.1458]
  Q88: [0.1165, 0.1459, 0.1772]
  Q89: [0.1316, 0.1720, 0.2154]

=== Combined Prediction Intervals (param + noise) ===
  Q81: [0.0237, 0.0470, 0.0703]
  Q82: [0.0325, 0.0556, 0.0787]
  Q83: [0.0423, 0.0654, 0.0885]
  Q84: [0.0533, 0.0767, 0.1001]
  Q85: [0.0655, 0.0899, 0.1143]
  Q86: [0.0787, 0.1054, 0.1322]
  Q87: [0.0926, 0.1239, 0.1551]
  Q88: [0.1074, 0.1457, 0.1841]
  Q89: [0.1232, 0.1717, 0.2202]

=== Extrapolation Analysis ===
  Q0: vix=20.02 (z=0.62), bbb=1.1336 (z=-0.70)
        extrapolation: vix=0.00%, bbb=0.00%
  Q1: vix=21.74 (z=0.93), bbb=1.4777 (z=-0.14)
        extrapolation: vix=0.00%, bbb=0.00%
  Q2: vix=23.62 (z=1.27), bbb=1.8218 (z=0.42)
        extrapolation: vix=0.00%, bbb=0.00%
  Q3: vix=25.65 (z=1.63), bbb=2.1660 (z=0.99)
        extrapolation: vix=0.00%, bbb=0.00%
  Q4: vix=27.86 (z=2.03), bbb=2.5101 (z=1.55)
        extrapolation: vix=0.00%, bbb=0.00%
  Q5: vix=30.26 (z=2.46), bbb=2.8542 (z=2.11)
        extrapolation: vix=0.00%, bbb=0.00%
  Q6: vix=32.87 (z=2.92), bbb=3.1983 (z=2.68)
        extrapolation: vix=0.00%, bbb=5.09%
  Q7: vix=35.70 (z=3.43), bbb=3.5425 (z=3.24)
        extrapolation: vix=1.37%, bbb=17.66%
  Q8: vix=38.77 (z=3.98), bbb=3.8866 (z=3.80)
        extrapolation: vix=12.74%, bbb=30.23%


## [32] assistant

**[reasoning]**

> Now I need to finalize the approach and write predictions.csv. Let me think about the best model:
> 
> 1. VIX + BBB spread quadratic model has good R² (0.82)
> 2. The residuals have minimal autocorrelation
> 3. Some scenario points are extrapolating (Q87-Q89), especially VIX going above training range
> 
> For prediction intervals, I should account for:
> - Parameter uncertainty (bootstrap)
> - Residual (noise) uncertainty  
> - Extrapolation uncertainty
> 
> The combined approach seems reasonable. Let me also check if adding more features or using a different model would be better. But since VIX has the strongest correlation and adding BBB doesn't dramatically improve, I'll stick with the VIX+BBB quadratic model.
> 
> However, I need to think more carefully about extrapolation uncertainty for Q87-Q89 where VIX goes above the training range. The quadratic model might not extrapolate well because:
> - Quadratic curves have inflection points and can behave unpredictably outside the training range
> - The predicted default rates for Q87-Q89 are quite high (0.12-0.17)
> 
> Let me also check whether the model's extrapolation is reasonable and adjust intervals accordingly. A multiplicative inflation factor for extrapolated points might be appropriate.
> 
> Actually, looking at the predictions more carefully:
> - Q81-Q86 are within VIX range but some BBB extrapolation at Q87+
> - The default rate increases as VIX increases, which makes economic sense
> 
> For the final predictions.csv, I should:
> 1. Use VIX + BBB quadratic model as the base
> 2. Use bootstrap-based prediction intervals with residual uncertainty
> 3. Consider inflating intervals for extrapolation
> 
> Let me also explore whether a simpler VIX-only model might be more robust to extrapolation, since it's easier to justify polynomial behavior for a single variable.
> 
> Actually, let me reconsider - the VIX+BBB quadratic has slightly better R² but with multicollinearity issues (condition number warning). Let me check if a simpler model works better for extrapolation.
> 
> I think the best approach is:
> 1. Use VIX + BBB quadratic model  
> 2. Bootstrap for parameter uncertainty
> 3. Add residual noise for prediction interval
> 4. Possibly inflate intervals slightly more for extrapolation
> 
> Let me write the final script.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# Final model: VIX + BBB spread quadratic (best R2 of 0.82)
mask = train['vix'].notna() & train['bbb_spread'].notna()
X_data = train.loc[mask, ['vix', 'bbb_spread']].values
y_data = y.loc[mask].values

poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X_data)

# Fit OLS model  
model = sm.OLS(y_data, sm.add_constant(X_poly)).fit()
sigma_hat = np.sqrt(model.mse_resid)

# Scenario predictions
X_scen = scenario[['vix', 'bbb_spread']].values
X_poly_scen = poly.transform(X_scen)

# Cross-validation to estimate OOS RMSE
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_preds = np.zeros(len(y_data))
for train_idx, test_idx in kf.split(X_poly):
    X_tr = sm.add_constant(X_poly[train_idx])
    y_tr = y_data[train_idx]
    X_te = sm.add_constant(X_poly[test_idx])
    m = sm.OLS(y_tr, X_tr).fit()
    cv_preds[test_idx] = m.predict(X_te)

cv_resid = y_data - cv_preds
cv_rmse = np.sqrt(np.mean(cv_resid**2))
print(f"CV RMSE: {cv_rmse:.6f}")
print(f"In-sample residual std: {sigma_hat:.6f}")

# Bootstrap for parameter uncertainty
n_boot = 10000
np.random.seed(42)

boot_preds = np.zeros((n_boot, len(scenario)))
resid_sample = model.resid.values

for b in range(n_boot):
    # Resample residuals
    resid_boot = np.random.choice(resid_sample, size=len(y_data))
    y_boot = model.predict(sm.add_constant(X_poly)) + resid_boot
    
    try:
        model_boot = sm.OLS(y_boot, sm.add_constant(X_poly)).fit()
        boot_preds[b, :] = model_boot.predict(sm.add_constant(X_poly_scen))
    except:
        # If fit fails, use point prediction
        boot_preds[b, :] = model.predict(sm.add_constant(X_poly_scen))

# Compute statistics
y_pred = model.predict(sm.add_constant(X_poly_scen))
boot_std = np.std(boot_preds, axis=0)

# Total prediction uncertainty: sqrt(param_uncertainty^2 + residual_std^2)
# Then multiply by t_crit for the interval
t_crit = stats.t.ppf(0.975, df=model.df_resid)

# Also add extrapolation factor
vix_train = X_data[:, 0]
bbb_train = X_data[:, 1]

for i in range(len(scenario)):
    vix_s = X_scen[i, 0]
    bbb_s = X_scen[i, 1]
    vix_max = vix_train.max()
    bbb_max = bbb_train.max()
    
    # Simple extrapolation factor based on how far beyond training range
    total_extra = max(0, vix_s - vix_max) / (vix_max - vix_train.min()) + \
                  max(0, bbb_s - bbb_max) / (bbb_max - bbb_train.min())
    
    if i == 8 or total_extra > 0.1:
        print(f"Q{i}: extrapolation factor = {total_extra:.4f}")

# Simple approach: bootstrap quantiles + residual noise
# For each point, the prediction interval should contain ~95% of future observations
# Total variance = var(bootstrap predictions) + sigma^2 (residual variance)
total_std = np.sqrt(boot_std**2 + sigma_hat**2)

# For extrapolation, inflate the standard error
# Use a factor that increases with distance beyond training range
extrapolation_factors = []
for i in range(len(scenario)):
    vix_s = X_scen[i, 0]
    bbb_s = X_scen[i, 1]
    
    vix_ext = max(0, (vix_s - vix_train.max()) / (vix_train.std()))
    bbb_ext = max(0, (bbb_s - bbb_train.max()) / (bbb_train.std()))
    max_ext = max(vix_ext, bbb_ext)
    
    # Inflate by sqrt(1 + 2*ext) to account for model misspecification at extremes
    factor = np.sqrt(1 + 2 * max_ext)
    extrapolation_factors.append(factor)
    
print(f"\nExtrapolation inflation factors: {extrapolation_factors}")

total_std_inflated = total_std * np.array(extrapolation_factors)

# Final prediction intervals
y_lower = y_pred - t_crit * total_std_inflated
y_upper = y_pred + t_crit * total_std_inflated

print(f"\n=== Final Predictions with 95% Prediction Intervals ===")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    print(f"  Q{q}: [{y_lower[i]:.6f}, {y_pred[i]:.6f}, {y_upper[i]:.6f}]")

# Write predictions
results = pd.DataFrame({
    'quarter': scenario['quarter'].values,
    'y_pred': y_pred,
    'y_lower': y_lower,
    'y_upper': y_upper
})

results.to_csv('predictions.csv', index=False)
print("\nWrote predictions.csv")
print(f"Rows: {len(results)}")
print(results.to_string())

PYEOF

```

## [33] tool

Traceback (most recent call last):
  File "<stdin>", line 50, in <module>
AttributeError: 'numpy.ndarray' object has no attribute 'values'

CV RMSE: 0.012896
In-sample residual std: 0.011234


## [34] assistant

**[reasoning]**

> The residual_sample assignment failed. Let me fix that.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# Final model: VIX + BBB spread quadratic (best R2 of 0.82)
mask = train['vix'].notna() & train['bbb_spread'].notna()
X_data = train.loc[mask, ['vix', 'bbb_spread']].values
y_data = y.loc[mask].values

poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X_data)

# Fit OLS model  
model = sm.OLS(y_data, sm.add_constant(X_poly)).fit()
sigma_hat = np.sqrt(model.mse_resid)

# Scenario predictions
X_scen = scenario[['vix', 'bbb_spread']].values
X_poly_scen = poly.transform(X_scen)

# Cross-validation to estimate OOS RMSE
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_preds = np.zeros(len(y_data))
for train_idx, test_idx in kf.split(X_poly):
    X_tr = sm.add_constant(X_poly[train_idx])
    y_tr = y_data[train_idx]
    X_te = sm.add_constant(X_poly[test_idx])
    m = sm.OLS(y_tr, X_tr).fit()
    cv_preds[test_idx] = m.predict(X_te)

cv_resid = y_data - cv_preds
cv_rmse = np.sqrt(np.mean(cv_resid**2))
print(f"CV RMSE: {cv_rmse:.6f}")
print(f"In-sample residual std: {sigma_hat:.6f}")

# Bootstrap for parameter uncertainty
n_boot = 10000
np.random.seed(42)

boot_preds = np.zeros((n_boot, len(scenario)))
resid_sample = model.resid  # This returns a pandas Series; use .array or .values

for b in range(n_boot):
    # Resample residuals with replacement
    resid_boot = np.random.choice(model.resid, size=len(y_data))
    y_boot = model.predict(sm.add_constant(X_poly)) + resid_boot
    
    try:
        model_boot = sm.OLS(y_boot, sm.add_constant(X_poly)).fit()
        boot_preds[b, :] = model_boot.predict(sm.add_constant(X_poly_scen))
    except Exception as e:
        # If fit fails, use point prediction
        boot_preds[b, :] = model.predict(sm.add_constant(X_poly_scen))

# Compute statistics
y_pred = model.predict(sm.add_constant(X_poly_scen))
boot_std = np.std(boot_preds, axis=0)

print(f"\nBootstrap std per quarter: {boot_std}")
print(f"Residual std: {sigma_hat}")

# Total prediction uncertainty: sqrt(param_uncertainty^2 + residual_std^2)
total_std = np.sqrt(boot_std**2 + sigma_hat**2)

# For extrapolation, inflate the standard error
extrapolation_factors = []
for i in range(len(scenario)):
    vix_s = X_scen[i, 0]
    bbb_s = X_scen[i, 1]
    
    vix_ext = max(0, (vix_s - X_data[:, 0].max()) / X_data[:, 0].std())
    bbb_ext = max(0, (bbb_s - X_data[:, 1].max()) / X_data[:, 1].std())
    max_ext = max(vix_ext, bbb_ext)
    
    # Inflate by sqrt(1 + 2*ext) to account for model misspecification at extremes
    factor = np.sqrt(1 + 2 * max_ext)
    extrapolation_factors.append(factor)

print(f"\nExtrapolation inflation factors: {extrapolation_factors}")

total_std_inflated = total_std * np.array(extrapolation_factors)

# Final prediction intervals using t-distribution
t_crit = stats.t.ppf(0.975, df=model.df_resid)

y_lower = y_pred - t_crit * total_std_inflated
y_upper = y_pred + t_crit * total_std_inflated

print(f"\n=== Final Predictions with 95% Prediction Intervals ===")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    print(f"  Q{q}: [{y_lower[i]:.6f}, {y_pred[i]:.6f}, {y_upper[i]:.6f}]")

# Write predictions
results = pd.DataFrame({
    'quarter': scenario['quarter'].values,
    'y_pred': y_pred,
    'y_lower': y_lower,
    'y_upper': y_upper
})

results.to_csv('predictions.csv', index=False)
print("\nWrote predictions.csv")
print(f"Rows: {len(results)}")
print(results.to_string())

PYEOF

```

## [35] tool

CV RMSE: 0.012896
In-sample residual std: 0.011234

Bootstrap std per quarter: [0.00312376 0.0026268  0.00264061 0.0032397  0.00471979 0.00722297
 0.01078422 0.01545697 0.02133213]
Residual std: 0.011233981134022462

Extrapolation inflation factors: [np.float64(1.0), np.float64(1.0), np.float64(1.0), np.float64(1.0), np.float64(1.0), np.float64(1.0), np.float64(1.2069295178019457), np.float64(1.607320986286427), np.float64(1.92612441877798)]

=== Final Predictions with 95% Prediction Intervals ===
  Q81: [0.023665, 0.046989, 0.070313]
  Q82: [0.032510, 0.055587, 0.078665]
  Q83: [0.042286, 0.065370, 0.088454]
  Q84: [0.053286, 0.076673, 0.100060]
  Q85: [0.065506, 0.089880, 0.114254]
  Q86: [0.078724, 0.105439, 0.132154]
  Q87: [0.086265, 0.123860, 0.161455]
  Q88: [0.084299, 0.145734, 0.207169]
  Q89: [0.078854, 0.171743, 0.264632]

Wrote predictions.csv
Rows: 9
   quarter    y_pred   y_lower   y_upper
0       81  0.046989  0.023665  0.070313
1       82  0.055587  0.032510  0.078665
2       83  0.065370  0.042286  0.088454
3       84  0.076673  0.053286  0.100060
4       85  0.089880  0.065506  0.114254
5       86  0.105439  0.078724  0.132154
6       87  0.123860  0.086265  0.161455
7       88  0.145734  0.084299  0.207169
8       89  0.171743  0.078854  0.264632


## [36] assistant

**[reasoning]**

> Looking at the results, I'm concerned about:
> 
> 1. The lower bounds getting too small/negative-like behavior - Q88 has y_lower=0.084 which is below y_pred=0.146, and Q89 has y_lower=0.079 which is far below y_pred=0.172. The inflation factors are very aggressive for extrapolation quarters (Q87-Q89).
> 
> 2. The bootstrap std grows dramatically at the extrapolation end, which makes sense but might be over-inflating.
> 
> 3. Let me reconsider the approach. The model is:
>    - default_rate = f(VIX, bbb_spread) using quadratic terms
>    - R² ≈ 0.82 on training data
>    - CV RMSE ≈ 0.013
> 
> 4. The scenario has VIX going from 20 to 39 (training max was ~35.3) and bbb_spread going from 1.1 to 3.9 (training max was ~3.06).
> 
> 5. The quadratic model might be overfitting with the high-degree polynomial terms when extrapolating. Let me try a simpler model - just VIX linear or quadratic without bbb_spread interaction, since that might extrapolate better.
> 
> Actually, let me reconsider. The quadratic terms for VIX alone have good fit (R²=0.8157). Let me use just VIX quadratic since it has more data points (66 vs 66 for VIX+BBB) and might extrapolate more smoothly.
> 
> But wait - the issue with the bootstrap is that for extrapolation points, the quadratic terms (x²) create very high leverage points, leading to huge parameter uncertainty. This is causing the wide intervals.
> 
> Let me try a different approach:
> 1. Use VIX + BBB as main features but with simpler model (linear or interaction only)
> 2. Or use bootstrap but cap the parameter uncertainty
> 3. Or use a different method to estimate prediction intervals
> 
> Let me also reconsider whether the default rate could exceed 1.0 (probability). The max in training is 0.145, so the model should be reasonable as long as we're not too far beyond.
> 
> Let me try a cleaner approach: use the bootstrap but also ensure intervals are sensible. I'll cap lower bound at 0 and check if the interval width makes sense.
> 
> Actually, let me re-examine - maybe I should use VIX only (simpler model, less extrapolation risk) and get a better estimate of the residual std from CV.
> 
> Let me also try: fit on all available features using multiple imputation for missing values, to use more data.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_predict, LeaveOneOut
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# Let me explore a multi-model approach and see which extrapolates best
# 1. VIX only (most available data, simple relationship)
# 2. VIX + bbb_spread (stronger correlation but less data)

print("=== Analysis: VIX vs VIX+BBB for extrapolation ===\n")

# Check the actual relationship more carefully
mask_vix = train['vix'].notna()
X_vix_raw = train.loc[mask_vix, ['vix']].values
y_vix_data = y.loc[mask_vix].values

# Check residuals of VIX model to see if there's a systematic pattern
X_vix_quad = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X_vix_raw)
model_vix = sm.OLS(y_vix_data, sm.add_constant(X_vix_quad)).fit()

# Fit a simple linear model
model_lin = sm.OLS(y_vix_data, sm.add_constant(X_vix_raw)).fit()

# Let's look at the training data more carefully
train_with_vix = train.loc[mask_vix].copy()

# Plot-like analysis: residuals by BBI spread
if 'bbb_spread' in train.columns:
    bbb_avail = train_with_vix['bbb_spread'].notna()
    df_bbb = train_with_vix[bbb_avail]
    
    # VIX-only residuals for BBB-available subset
    X_bbb = df_bbb[['vix']].values
    X_bbb_quad = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X_bbb)
    y_bbb = df_bbb['default_rate'].values
    
    resid_vix = y_bbb - model_vix.predict(sm.add_constant(X_bbb_quad))
    
    print("Residuals of VIX model (at points where BBB is also available):")
    print(f"  Mean: {np.mean(resid_vix):.6f}")
    print(f"  Std: {np.std(resid_vix):.6f}")
    
    # Do residuals correlate with BBB spread?
    corr = np.corrcoef(resid_vix, df_bbb['bbb_spread'].values)[0, 1]
    print(f"  Correlation with BBB spread: {corr:.4f}")
    
    # If there's remaining structure, maybe BBB adds value
    # But if the correlation is small, VIX alone might be enough

# Let's compare in-sample performance
mask2 = train['vix'].notna() & train['bbb_spread'].notna()
X2 = train.loc[mask2, ['vix', 'bbb_spread']].values
y2 = y.loc[mask2].values

poly2 = PolynomialFeatures(degree=2, include_bias=False)
X2_poly = poly2.fit_transform(X2)

model_2feat = sm.OLS(y2, sm.add_constant(X2_poly)).fit()

# Use leave-one-out to compare
loo = LeaveOneOut()
cv_pred_vix = np.zeros(len(y2))
cv_pred_2feat = np.zeros(len(y2))

for train_idx, test_idx in loo.split(X2):
    # VIX-only model (but we need to train on BBB as well since they're same rows)
    # For fair comparison, use same training subset
    X_tr = X2[train_idx]
    X_te = X2[test_idx]
    
    # VIX only
    X_vix_tr = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X_tr[:, :1])
    X_vix_te = PolynomialFeatures(degree=2, include_bias=False).fit_transform(X_te[:, :1])
    m_vix = sm.OLS(y2[train_idx], sm.add_constant(X_vix_tr)).fit()
    cv_pred_vix[test_idx] = m_vix.predict(sm.add_constant(X_vix_te))
    
    # VIX + BBB quadratic
    m_2f = sm.OLS(y2[train_idx], sm.add_constant(poly2.transform(X_tr))).fit()
    cv_pred_2feat[test_idx] = m_2f.predict(sm.add_constant(poly2.transform(X_te)))

resid_vix_loo = y2 - cv_pred_vix
resid_2f_loo = y2 - cv_pred_2feat

print(f"\nLOO comparison:")
print(f"  VIX quad LOO RMSE: {np.sqrt(np.mean(resid_vix_loo**2)):.6f}")
print(f"  VIX+BBB quad LOO RMSE: {np.sqrt(np.mean(resid_2f_loo**2)):.6f}")
print(f"  VIX quad LOO R2: {1 - np.sum(resid_vix_loo**2)/np.sum((y2-y2.mean())**2):.4f}")
print(f"  VIX+BBB quad LOO R2: {1 - np.sum(resid_2f_loo**2)/np.sum((y2-y2.mean())**2):.4f}")

# Which model is better for extrapolation?
# Let's look at coefficient stability with LOO
print(f"\nCoefficient stability:")

for train_idx, test_idx in KFold(n_splits=5, shuffle=True, random_state=42).split(X2):
    X_tr = sm.add_constant(poly2.transform(X2[train_idx]))
    m = sm.OLS(y2[train_idx], X_tr).fit()
    print(f"  Coefficients (const, vix, bbb, vix^2, vix*bbb, bbb^2): {m.params.values}")

PYEOF

```

## [37] tool

Traceback (most recent call last):
  File "<stdin>", line 85, in <module>
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 1174, in predict
    predict_results = self.model.predict(self.params, exog, *args,
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 409, in predict
    return np.dot(exog, params)
           ^^^^^^^^^^^^^^^^^^^^
ValueError: shapes (1,2) and (3,) not aligned: 2 (dim 1) != 3 (dim 0)

=== Analysis: VIX vs VIX+BBB for extrapolation ===

Residuals of VIX model (at points where BBB is also available):
  Mean: 0.000000
  Std: 0.010827
  Correlation with BBB spread: -0.0504


## [38] assistant

**[reasoning]**

> The VIX-only model has very small residuals correlated with BBB (-0.05), suggesting BBB adds little value beyond VIX. The LOO comparison would be useful but I ran into a bug. Let me simplify and focus on producing good predictions.
> 
> Let me verify the current predictions.csv is correct, then consider if any improvements are needed.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np

# Verify current predictions
df = pd.read_csv('predictions.csv')
print("Current predictions:")
print(df)
print(f"\nNumber of rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

# Check that quarters match scenario
scenario = pd.read_csv('data/scenario.csv')
print(f"\nScenario quarters: {sorted(scenario['quarter'].tolist())}")
print(f"Prediction quarters: {sorted(df['quarter'].tolist())}")

# All intervals should have y_lower <= y_pred <= y_upper
print(f"\nAll y_lower <= y_pred: {(df['y_lower'] <= df['y_pred']).all()}")
print(f"All y_pred <= y_upper: {(df['y_pred'] <= df['y_upper']).all()}")

# All default rates should be non-negative
print(f"All y_pred >= 0: {(df['y_pred'] >= 0).all()}")
print(f"All y_lower >= 0: {(df['y_lower'] >= 0).all()}")
print(f"All y_upper >= 0: {(df['y_upper'] >= 0).all()}")

PYEOF

```

## [39] tool

Current predictions:
   quarter    y_pred   y_lower   y_upper
0       81  0.046989  0.023665  0.070313
1       82  0.055587  0.032510  0.078665
2       83  0.065370  0.042286  0.088454
3       84  0.076673  0.053286  0.100060
4       85  0.089880  0.065506  0.114254
5       86  0.105439  0.078724  0.132154
6       87  0.123860  0.086265  0.161455
7       88  0.145734  0.084299  0.207169
8       89  0.171743  0.078854  0.264632

Number of rows: 9
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']

Scenario quarters: [81, 82, 83, 84, 85, 86, 87, 88, 89]
Prediction quarters: [81, 82, 83, 84, 85, 86, 87, 88, 89]

All y_lower <= y_pred: True
All y_pred <= y_upper: True
All y_pred >= 0: True
All y_lower >= 0: True
All y_upper >= 0: True


## [40] assistant

**[reasoning]**

> Let me reconsider the approach. The current predictions are from a VIX+BBB quadratic model with bootstrap prediction intervals and extrapolation adjustment. Let me think about whether this is the best approach.
> 
> Key observations:
> 1. VIX has the strongest correlation (0.88-0.90) with default rate
> 2. VIX+BBB quadratic model has R²=0.82, which is good
> 3. The scenario VIX goes from 20 to 38.77, which is moderate extrapolation beyond training max of ~35
> 4. BBB spread also extrapolates moderately
> 
> However, looking at the predictions more carefully:
> - Q89 (VIX=38.77) has a very wide interval [0.079, 0.265], which seems reasonable for extrapolation
> - But Q87 (VIX=32.87, BBB=3.198) has lower bound 0.086 which seems a bit tight
> - The interval widths increase as we go further from training data
> 
> Actually, let me reconsider. I should try a more robust approach. Let me:
> 1. Use an ensemble of models for better predictions
> 2. Better handle extrapolation uncertainty
> 3. Consider whether there are other predictive features
> 
> Let me also check if using GBR (which was competitive) gives better OOS performance, and whether I should consider a simpler linear model which might extrapolate better.
> 
> Actually, the current approach seems reasonable. But let me refine it by:
> 1. Using multiple models and averaging predictions
> 2. Better calibration of prediction intervals via bootstrapping the full pipeline
> 3. Ensuring proper handling of extrapolation
> 
> Let me also try a different approach: using the linear VIX model only, which is simpler and may extrapolate more reliably.
> 
> Actually wait - let me reconsider the problem. The task says "the scenario pushes the drivers beyond the range seen in training." Let me check how far beyond:
> - VIX train max ~35.33, scenario max 38.77 (about 10% beyond)
> - BBB spread train max ~3.06, scenario max 3.89 (about 27% beyond)
> 
> These are moderate extrapolations, so the model should still work reasonably well. The bootstrap + inflation approach is appropriate.
> 
> Let me refine the solution and make sure everything is solid. I'll use a cleaner approach:
> 1. Main model: VIX+BBB quadratic OLS
> 2. Prediction intervals: Bootstrap + residual noise + extrapolation inflation
> 3. Cross-validate to check interval coverage
> 
> Let me also consider: should I use a simpler model? Linear VIX might extrapolate better (no quadratic term that could diverge). Let me check the fit.
> 
> Looking at the coefficients for VIX+BBB quadratic:
> - const: 0.0126
> - vix (x1): -0.0005 
> - bbb (x2): -0.0013
> - vix^2 (x3): 8.16e-5
> - vix*bbb (x4): 0.0008
> - bbb^2 (x5): -0.0043
> 
> The quadratic terms are present but relatively small compared to the linear relationship through VIX.
> 
> Actually, I think I should try a few more things:
> 1. Check if log-transform or power transform of VIX works better
> 2. Try a GBR model that doesn't extrapolate as poorly
> 3. Use an ensemble approach
> 
> Let me write a final comprehensive solution.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_predict, LeaveOneOut
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# === Comprehensive Model Building ===

mask_vix = train['vix'].notna()
X_vix_raw = train.loc[mask_vix, ['vix']].values
y_vix_data = y.loc[mask_vix].values

# Compare linear vs quadratic VIX
print("=== VIX Model Comparison ===")
for degree in [1, 2]:
    X_poly = PolynomialFeatures(degree=degree, include_bias=False).fit_transform(X_vix_raw)
    model = sm.OLS(y_vix_data, sm.add_constant(X_poly)).fit()
    
    # LOO CV
    loo = LeaveOneOut()
    cv_preds = np.zeros(len(y_vix_data))
    for train_idx, test_idx in loo.split(X_poly):
        X_tr = sm.add_constant(X_poly[train_idx])
        X_te = sm.add_constant(X_poly[test_idx])
        m = sm.OLS(y_vix_data[train_idx], X_tr).fit()
        cv_preds[test_idx] = m.predict(X_te)
    
    resid = y_vix_data - cv_preds
    rmse_loo = np.sqrt(np.mean(resid**2))
    
    print(f"Degree {degree}: R2={model.rsquared:.4f}, LOO RMSE={rmse_loo:.6f}")

# VIX+BBB comparison
mask2 = train['vix'].notna() & train['bbb_spread'].notna()
X2 = train.loc[mask2, ['vix', 'bbb_spread']].values
y2 = y.loc[mask2].values

print("\n=== VIX+BBB Model Comparison ===")
for degree in [1, 2]:
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(X2)
    
    model = sm.OLS(y2, sm.add_constant(X_poly)).fit()
    
    loo = LeaveOneOut()
    cv_preds = np.zeros(len(y2))
    for train_idx, test_idx in loo.split(X_poly):
        X_tr = sm.add_constant(X_poly[train_idx])
        X_te = sm.add_constant(X_poly[test_idx])
        m = sm.OLS(y2[train_idx], X_tr).fit()
        cv_preds[test_idx] = m.predict(X_te)
    
    resid = y2 - cv_preds
    rmse_loo = np.sqrt(np.mean(resid**2))
    
    print(f"Degree {degree}: R2={model.rsquared:.4f}, LOO RMSE={rmse_loo:.6f}")

# GBR comparison on VIX
print("\n=== GBR Comparison (VIX) ===")
for n_est in [30, 50, 100]:
    for lr in [0.05, 0.1]:
        model = GradientBoostingRegressor(n_estimators=n_est, learning_rate=lr, 
                                          max_depth=3, random_state=42)
        loo = LeaveOneOut()
        cv_preds = np.zeros(len(y_vix_data))
        for train_idx, test_idx in loo.split(X_vix_raw):
            model.fit(X_vix_raw[train_idx], y_vix_data[train_idx])
            cv_preds[test_idx] = model.predict(X_vix_raw[test_idx])
        resid = y_vix_data - cv_preds
        rmse_loo = np.sqrt(np.mean(resid**2))
        
print("GRB done")

PYEOF

```

## [41] tool

Traceback (most recent call last):
  File "<stdin>", line 35, in <module>
  File "/usr/local/lib/python3.12/site-packages/statsmodels/base/model.py", line 1174, in predict
    predict_results = self.model.predict(self.params, exog, *args,
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/statsmodels/regression/linear_model.py", line 409, in predict
    return np.dot(exog, params)
           ^^^^^^^^^^^^^^^^^^^^
ValueError: shapes (1,1) and (2,) not aligned: 1 (dim 1) != 2 (dim 0)

=== VIX Model Comparison ===


## [42] assistant

**[reasoning]**

> The LOO loop has an issue with shape mismatch. Let me fix and continue building the final model. The quadratic VIX model has been performing well (R2 ~0.82). Let me create the final robust script that builds the model and produces predictions.csv.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# === Build the best model: VIX + BBB Spread (Quadratic) ===
# This uses 66 observations where both vix and bbb_spread are available

mask = train['vix'].notna() & train['bbb_spread'].notna()
X_data = train.loc[mask, ['vix', 'bbb_spread']].values
y_data = y.loc[mask].values

# Polynomial features (degree 2): vix, bbb, vix^2, vix*bbb, bbb^2
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X_data)

# Fit OLS model
X_full = sm.add_constant(X_poly)
model = sm.OLS(y_data, X_full).fit()

print("Model Summary:")
print(f"  R²: {model.rsquared:.4f}")
print(f"  Adj. R²: {model.rsquared_adj:.4f}")
print(f"  Residual std (sigma): {np.sqrt(model.mse_resid):.6f}")
print(f"  Observations: {len(y_data)}")
print(f"  Degrees of freedom: {model.df_resid}")
print()

# Feature names for interpretation
feat_names = ['const', 'vix', 'bbb_spread', 'vix^2', 'vix*bbb', 'bbb^2']
print("Coefficients:")
for name, coef in zip(feat_names, model.params.values):
    print(f"  {name:12s}: {coef:+.6f} (se={model.bse[list(feat_names).index(name)]:.6f})")
print()

# === Predictions for scenario ===
X_scen = scenario[['vix', 'bbb_spread']].values
X_poly_scen = poly.transform(X_scen)

# Point predictions
y_pred = model.predict(sm.add_constant(X_poly_scen))

print("Point Predictions:")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    print(f"  Q{q}: {y_pred[i]:.6f}")

# === Prediction Intervals ===
# 1. Parameter uncertainty via bootstrap
n_boot = 20000
np.random.seed(42)

boot_preds = np.full((n_boot, len(scenario)), np.nan)
resid_array = model.resid.values

for b in range(n_boot):
    # Resample residuals with replacement
    idx = np.random.choice(len(y_data), size=len(y_data))
    resid_boot = resid_array[idx]
    y_boot = model.predict(X_full) + resid_boot
    
    try:
        model_boot = sm.OLS(y_boot, X_full).fit()
        boot_preds[b, :] = model_boot.predict(sm.add_constant(X_poly_scen))
    except:
        pass  # Keep NaN, will handle below

# Compute bootstrap statistics
valid_boot = boot_preds[~np.isnan(boot_preds)]
if len(valid_boot) > 0:
    boot_mean = np.nanmean(boot_preds, axis=0)
    boot_std = np.nanstd(boot_preds, axis=0, ddof=1)
else:
    boot_mean = y_pred
    boot_std = np.zeros(len(scenario))

print(f"\nBootstrap successful: {len(valid_boot)} / {n_boot} iterations")
print(f"Bootstrap std per quarter: {boot_std}")

# 2. Residual (observation) uncertainty
sigma_hat = np.sqrt(model.mse_resid)

# 3. Extrapolation factor
vix_max = X_data[:, 0].max()
bbb_max = X_data[:, 1].max()
vix_range = X_data[:, 0].max() - X_data[:, 0].min()
bbb_range = X_data[:, 1].max() - X_data[:, 1].min()

extrapolation_factors = np.ones(len(scenario))
for i in range(len(scenario)):
    vix_s = X_scen[i, 0]
    bbb_s = X_scen[i, 1]
    
    vix_ext_frac = max(0, (vix_s - vix_max) / vix_range)
    bbb_ext_frac = max(0, (bbb_s - bbb_max) / bbb_range)
    max_ext = max(vix_ext_frac, bbb_ext_frac)
    
    # Inflate by sqrt(1 + 3*max_ext) for moderate extrapolation adjustment
    if max_ext > 0:
        extrapolation_factors[i] = np.sqrt(1 + 3 * max_ext)

print(f"\nExtrapolation factors: {extrapolation_factors}")

# 4. Total prediction standard error
total_se = np.sqrt(boot_std**2 + sigma_hat**2) * extrapolation_factors

# 5. 95% prediction interval using t-distribution
t_crit = stats.t.ppf(0.975, df=model.df_resid)
y_lower = y_pred - t_crit * total_se
y_upper = y_pred + t_crit * total_se

# Ensure lower bound doesn't go below 0 (default rate can't be negative)
y_lower = np.maximum(y_lower, 0.0)

print("\n=== Final Predictions with 95% Prediction Intervals ===")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    vix_s = X_scen[i, 0]
    bbb_s = X_scen[i, 1]
    print(f"  Q{q}: [{y_lower[i]:.6f}, {y_pred[i]:.6f}, {y_upper[i]:.6f}]")

# === Write predictions.csv ===
results = pd.DataFrame({
    'quarter': scenario['quarter'].values,
    'y_pred': y_pred,
    'y_lower': y_lower,
    'y_upper': y_upper
})

results.to_csv('predictions.csv', index=False)
print(f"\nWrote predictions.csv with {len(results)} rows")

# Final validation
assert len(results) == 9, f"Expected 9 rows, got {len(results)}"
assert list(results.columns) == ['quarter', 'y_pred', 'y_lower', 'y_upper'], f"Wrong columns: {list(results.columns)}"
assert (results['y_lower'] <= results['y_pred']).all(), "y_lower > y_pred"
assert (results['y_pred'] <= results['y_upper']).all(), "y_pred > y_upper"
assert (results['y_lower'] >= 0).all(), "Negative lower bound"

print("\nAll validations passed!")
PYEOF

```

## [43] tool

Traceback (most recent call last):
  File "<stdin>", line 42, in <module>
AttributeError: 'numpy.ndarray' object has no attribute 'values'

Model Summary:
  R²: 0.8196
  Adj. R²: 0.8046
  Residual std (sigma): 0.011234
  Observations: 66
  Degrees of freedom: 60.0

Coefficients:


## [44] assistant

**[reasoning]**

> The issue is that `model.resid` returns a pandas Series and accessing it via `.values` may fail. Let me fix this by being more careful with how I access the residuals and coefficients.
> 
> Let me also reconsider the approach. The model R² is 0.82 which is good. But I need to verify that the prediction intervals are reasonable, especially given the extrapolation into territory beyond what's seen in training data (VIX goes up to 38.77 vs train max of ~35, and BBB spread goes to 3.89 vs train max of ~3.06).
> 
> Let me fix the script and also try to validate the predictions more carefully.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
y = train['default_rate']

# === Build the best model: VIX + BBB Spread (Quadratic) ===
mask = train['vix'].notna() & train['bbb_spread'].notna()
X_data = train.loc[mask, ['vix', 'bbb_spread']].values
y_data = y.loc[mask].values

# Polynomial features (degree 2)
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X_data)

# Fit OLS model
const_col = np.ones((len(X_poly), 1))
X_full_matrix = np.hstack([const_col, X_poly])

model = sm.OLS(y_data, X_full_matrix).fit()

print("Model Summary:")
print(f"  R²: {model.rsquared:.4f}")
print(f"  Adj. R²: {model.rsquared_adj:.4f}")
sigma_hat = np.sqrt(model.mse_resid)
print(f"  Residual std (sigma): {sigma_hat:.6f}")
print(f"  Observations: {len(y_data)}")
df_resid = model.df_resid
print(f"  Degrees of freedom: {df_resid}")
print()

# Feature names for interpretation
feat_names = ['const', 'vix', 'bbb_spread', 'vix^2', 'vix*bbb', 'bbb^2']
print("Coefficients:")
for name, coef in zip(feat_names, model.params):
    print(f"  {name:12s}: {coef:+.6f}")
print()

# === Predictions for scenario ===
X_scen = scenario[['vix', 'bbb_spread']].values
X_poly_scen = poly.transform(X_scen)

# Point predictions
y_pred = model.predict(np.hstack([np.ones((len(X_poly_scen), 1)), X_poly_scen]))

print("Point Predictions:")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    print(f"  Q{q}: {y_pred[i]:.6f}")

# === Prediction Intervals via Bootstrap ===
n_boot = 20000
np.random.seed(42)

# Get residuals as a plain numpy array
resid_array = np.array(model.resid)

boot_preds = []
for b in range(n_boot):
    # Resample residuals with replacement
    idx = np.random.choice(len(y_data), size=len(y_data))
    resid_boot = resid_array[idx]
    y_boot = model.predict(X_full_matrix) + resid_boot
    
    try:
        model_boot = sm.OLS(y_boot, X_full_matrix).fit()
        pred_i = model_boot.predict(np.hstack([np.ones((len(X_poly_scen), 1)), X_poly_scen]))
        boot_preds.append(pred_i)
    except Exception as e:
        pass

boot_preds = np.array(boot_preds)  # Shape: (n_success, n_scenarios)
n_success = len(boot_preds)
print(f"\nBootstrap successful: {n_success} / {n_boot} iterations")

# Compute bootstrap statistics
boot_mean = np.mean(boot_preds, axis=0)
boot_std = np.std(boot_preds, axis=0, ddof=1)

print(f"Bootstrap std per quarter: {boot_std}")

# Residual (observation) uncertainty
print(f"Residual std: {sigma_hat:.6f}")

# Extrapolation factor
vix_max = X_data[:, 0].max()
bbb_max = X_data[:, 1].max()
vix_range = X_data[:, 0].max() - X_data[:, 0].min()
bbb_range = X_data[:, 1].max() - X_data[:, 1].min()

extrapolation_factors = np.ones(len(scenario))
for i in range(len(scenario)):
    vix_s = X_scen[i, 0]
    bbb_s = X_scen[i, 1]
    
    vix_ext_frac = max(0, (vix_s - vix_max) / vix_range)
    bbb_ext_frac = max(0, (bbb_s - bbb_max) / bbb_range)
    max_ext = max(vix_ext_frac, bbb_ext_frac)
    
    if max_ext > 0:
        extrapolation_factors[i] = np.sqrt(1 + 3 * max_ext)

print(f"\nExtrapolation factors: {extrapolation_factors}")

# Total prediction standard error
total_se = np.sqrt(boot_std**2 + sigma_hat**2) * extrapolation_factors

# 95% prediction interval using t-distribution
t_crit = stats.t.ppf(0.975, df=df_resid)
y_lower = y_pred - t_crit * total_se
y_upper = y_pred + t_crit * total_se

# Ensure lower bound doesn't go below 0 (default rate can't be negative)
y_lower = np.maximum(y_lower, 0.0)

print("\n=== Final Predictions with 95% Prediction Intervals ===")
for i in range(len(scenario)):
    q = scenario['quarter'].iloc[i]
    print(f"  Q{q}: [{y_lower[i]:.6f}, {y_pred[i]:.6f}, {y_upper[i]:.6f}]")

# === Write predictions.csv ===
results = pd.DataFrame({
    'quarter': scenario['quarter'].values,
    'y_pred': y_pred,
    'y_lower': y_lower,
    'y_upper': y_upper
})

results.to_csv('predictions.csv', index=False)
print(f"\nWrote predictions.csv with {len(results)} rows")

# Final validation
assert len(results) == 9, f"Expected 9 rows, got {len(results)}"
assert list(results.columns) == ['quarter', 'y_pred', 'y_lower', 'y_upper'], f"Wrong columns: {list(results.columns)}"
assert (results['y_lower'] <= results['y_pred']).all(), "y_lower > y_pred"
assert (results['y_pred'] <= results['y_upper']).all(), "y_pred > y_upper"
assert (results['y_lower'] >= 0).all(), "Negative lower bound"

print("\nAll validations passed!")

# Print final CSV
print("\n=== predictions.csv content ===")
with open('predictions.csv') as f:
    print(f.read())

PYEOF

```

## [45] tool

Model Summary:
  R²: 0.8196
  Adj. R²: 0.8046
  Residual std (sigma): 0.011234
  Observations: 66
  Degrees of freedom: 60.0

Coefficients:
  const       : +0.012565
  vix         : -0.000517
  bbb_spread  : -0.001324
  vix^2       : +0.000082
  vix*bbb     : +0.000842
  bbb^2       : -0.004312

Point Predictions:
  Q81: 0.046989
  Q82: 0.055587
  Q83: 0.065370
  Q84: 0.076673
  Q85: 0.089880
  Q86: 0.105439
  Q87: 0.123860
  Q88: 0.145734
  Q89: 0.171743

Bootstrap successful: 20000 / 20000 iterations
Bootstrap std per quarter: [0.00312191 0.00262159 0.00264711 0.00326321 0.00474665 0.00723652
 0.0107725  0.01541047 0.02124186]
Residual std: 0.011234

Extrapolation factors: [1.         1.         1.         1.         1.         1.
 1.07369497 1.23688667 1.38088624]

=== Final Predictions with 95% Prediction Intervals ===
  Q81: [0.023666, 0.046989, 0.070312]
  Q82: [0.032512, 0.055587, 0.078662]
  Q83: [0.042283, 0.065370, 0.088457]
  Q84: [0.053272, 0.076673, 0.100073]
  Q85: [0.065486, 0.089880, 0.114275]
  Q86: [0.078709, 0.105439, 0.132169]
  Q87: [0.090432, 0.123860, 0.157288]
  Q88: [0.098551, 0.145734, 0.192917]
  Q89: [0.105369, 0.171743, 0.238117]

Wrote predictions.csv with 9 rows

All validations passed!

=== predictions.csv content ===
quarter,y_pred,y_lower,y_upper
81,0.0469890052433961,0.023666128387043118,0.07031188209974909
82,0.05558729921140322,0.03251223168589988,0.07866236673690656
83,0.06536993981905936,0.04228321465783476,0.08845666498028397
84,0.07667258990174225,0.05327244799085428,0.10007273181263021
85,0.08988038942609408,0.06548552740508848,0.11427525144709968
86,0.10543889399910364,0.0787089273977809,0.13216886060042637
87,0.12385991698842197,0.09043219932666743,0.1572876346501765
88,0.1457339888961382,0.09855080656641493,0.19291717122586147
89,0.1717426972017349,0.10536867971291633,0.23811671469055348



## [46] assistant

**[reasoning]**

> Let me now think about whether this approach is solid and consider some refinements:
> 
> 1. The model uses VIX + bbb_spread with a quadratic fit, achieving R²=0.82
> 2. Prediction intervals account for parameter uncertainty (bootstrap), residual variance, and extrapolation distance
> 3. The scenario shows increasing VIX and bbb_spread over time, with default rates rising - which makes sense economically
> 
> However, I should consider:
> - The quadratic model might not extrapolate well. A simple linear VIX-only model might be more robust for extrapolation
> - Should I try multiple models and average predictions (ensemble)?
> - The residuals might show some autocorrelation that should be addressed
> 
> Let me also verify the approach is sound by checking if a simpler model might be better for this extrapolation task. The VIX-only quadratic model has R²=0.8157, which is almost as good as VIX+BBB (0.8196), and uses the same data subset effectively since BBB doesn't add much (its coefficient is small and not significant).
> 
> Actually, looking at the results more carefully:
> - The scenario VIX goes from 20 to 39, while training range was ~8-35
> - The scenario bbb_spread goes from 1.13 to 3.89, while training range was ~0.32 to ~3
> - Both are extrapolating beyond training, but not dramatically
> 
> The current approach seems reasonable. Let me also consider if I should use an ensemble of models for better robustness, or try a different approach entirely.
> 
> Let me also verify that the predictions are in reasonable ranges. The default rates go from ~0.047 to ~0.17, which are plausible quarterly annualized default rates.
> 
> I think the current approach is good. Let me finalize and submit.
> 
> Actually, wait - let me reconsider. The problem says "the scenario pushes the drivers beyond the range seen in training". Let me check which features are actually beyond the range:
> - VIX training max: 35.33, scenario max: 38.77 → moderate extrapolation
> - bbb_spread training max: depends on when it started. Let me check...
> 
> Looking at the data again:
> - bbb_spread starts at quarter 9 (rows 0-8 have NaN), so it has values from row 9 to 79
> - The max bbb_spread in training is probably around 3.06
> 
> The scenario pushes beyond training on VIX and bbb_spread in the later quarters. The extrapolation adjustment I'm making seems appropriate.
> 
> One thing I want to double-check: the predictions should be fractions (between 0 and 1), which they are.
> 
> Let me finalize with the current approach. The predictions look reasonable and the intervals properly account for uncertainty.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np

# Final verification of predictions.csv
df = pd.read_csv('predictions.csv')
scenario = pd.read_csv('data/scenario.csv')

print("=== Final Verification ===")
print(f"Number of rows: {len(df)} (expected 9)")
print(f"Columns: {list(df.columns)} (expected ['quarter', 'y_pred', 'y_lower', 'y_upper'])")
print(f"Quarters match: {sorted(df['quarter'].tolist()) == sorted(scenario['quarter'].tolist())}")
print(f"All y_lower <= y_pred: {(df['y_lower'] <= df['y_pred']).all()}")
print(f"All y_pred <= y_upper: {(df['y_pred'] <= df['y_upper']).all()}")
print(f"All values >= 0: {(df[['y_pred', 'y_lower', 'y_upper']] >= 0).all().all()}")
print(f"All values <= 1: {(df[['y_pred', 'y_lower', 'y_upper']] <= 1).all().all()}")

print(f"\nSummary stats:")
print(f"  y_pred: min={df['y_pred'].min():.4f}, max={df['y_pred'].max():.4f}")
print(f"  Interval width: min={df['y_upper'] - df['y_lower']}.min():.4f}, max={(df['y_upper'] - df['y_lower']).max():.4f}")

# Verify file is properly formatted
with open('predictions.csv') as f:
    content = f.read()
lines = content.strip().split('\n')
print(f"\nFile has {len(lines)} lines (1 header + {len(lines)-1} data rows)")
print(f"Header: {lines[0]}")

print("\n=== Final predictions.csv ===")
print(content)

PYEOF

```

## [47] tool

  File "<stdin>", line 19
    print(f"  Interval width: min={df['y_upper'] - df['y_lower']}.min():.4f}, max={(df['y_upper'] - df['y_lower']).max():.4f}")
                                                                           ^
SyntaxError: f-string: single '}' is not allowed



## [48] assistant

**[reasoning]**

> I have a syntax error in the f-string. Let me fix it and run verification again.
> 





**tool call: bash**

```
python3 << 'PYEOF'
import pandas as pd
import numpy as np

# Final verification of predictions.csv
df = pd.read_csv('predictions.csv')
scenario = pd.read_csv('data/scenario.csv')

print("=== Final Verification ===")
print(f"Number of rows: {len(df)} (expected 9)")
print(f"Columns: {list(df.columns)} (expected ['quarter', 'y_pred', 'y_lower', 'y_upper'])")
print(f"Quarters match: {sorted(df['quarter'].tolist()) == sorted(scenario['quarter'].tolist())}")
print(f"All y_lower <= y_pred: {(df['y_lower'] <= df['y_pred']).all()}")
print(f"All y_pred <= y_upper: {(df['y_pred'] <= df['y_upper']).all()}")
print(f"All values >= 0: {(df[['y_pred', 'y_lower', 'y_upper']] >= 0).all().all()}")
print(f"All values <= 1: {(df[['y_pred', 'y_lower', 'y_upper']] <= 1).all().all()}")

print(f"\nSummary stats:")
print(f"  y_pred: min={df['y_pred'].min():.4f}, max={df['y_pred'].max():.4f}")
interval_widths = df['y_upper'] - df['y_lower']
print(f"  Interval widths: min={interval_widths.min():.4f}, max={interval_widths.max():.4f}")

# Verify file is properly formatted
with open('predictions.csv') as f:
    content = f.read()
lines = content.strip().split('\n')
print(f"\nFile has {len(lines)} lines (1 header + {len(lines)-1} data rows)")
print(f"Header: {lines[0]}")

print("\n=== Final predictions.csv ===")
print(content)

PYEOF

```

## [49] tool

=== Final Verification ===
Number of rows: 9 (expected 9)
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper'] (expected ['quarter', 'y_pred', 'y_lower', 'y_upper'])
Quarters match: True
All y_lower <= y_pred: True
All y_pred <= y_upper: True
All values >= 0: True
All values <= 1: True

Summary stats:
  y_pred: min=0.0470, max=0.1717
  Interval widths: min=0.0462, max=0.1327

File has 10 lines (1 header + 9 data rows)
Header: quarter,y_pred,y_lower,y_upper

=== Final predictions.csv ===
quarter,y_pred,y_lower,y_upper
81,0.0469890052433961,0.023666128387043118,0.07031188209974909
82,0.05558729921140322,0.03251223168589988,0.07866236673690656
83,0.06536993981905936,0.04228321465783476,0.08845666498028397
84,0.07667258990174225,0.05327244799085428,0.10007273181263021
85,0.08988038942609408,0.06548552740508848,0.11427525144709968
86,0.10543889399910364,0.0787089273977809,0.13216886060042637
87,0.12385991698842197,0.09043219932666743,0.1572876346501765
88,0.1457339888961382,0.09855080656641493,0.19291717122586147
89,0.1717426972017349,0.10536867971291633,0.23811671469055348



## [50] assistant

**[reasoning]**

> The predictions.csv file has been generated and verified. Let me summarize what was done:
> 
> 1. **Data exploration**: Analyzed the training data with 80 quarters, noting missing values in several macroeconomic series (hpi: 10, bbb_spread: 9, vix: 14, sp500/djia: 35). The scenario has 9 quarters (81-89) where VIX and bbb_spread go beyond the training range.
> 
> 2. **Model selection**: The strongest predictor of default rate is VIX (correlation 0.88), followed by bbb_spread (correlation 0.43). A quadratic polynomial model on VIX + bbb_spread achieved R²=0.82 with 66 observations (where both are available).
> 
> 3. **Prediction intervals**: 
>    - Bootstrap resampling (20,000 iterations) for parameter uncertainty
>    - Residual noise (σ=0.0112) for observation uncertainty
>    - Extrapolation inflation factor for quarters 87-89 where scenario VIX/BBB exceed training ranges
>    - Combined using t-distribution with df=60
> 
> 4. **Output**: 9 rows, one per scenario quarter, with point estimates ranging from ~0.047 to ~0.172 and widening prediction intervals reflecting increasing extrapolation uncertainty.
> 
> All validations pass: correct columns, correct number of rows, proper ordering (lower ≤ pred ≤ upper), non-negative values, and quarters matching the scenario.
> 



The `predictions.csv` file has been successfully generated and verified. Here's a summary of the approach:

**Model**: Quadratic polynomial regression on VIX and BBB spread (R² = 0.82), using the 66 quarters where both features are available in training data.

**Why these features**: 
- VIX (market volatility) has the strongest correlation with default rate (r = 0.88)
- BBB spread (credit risk premium) adds incremental explanatory power

**Prediction intervals**: 
- **Parameter uncertainty**: 20,000 bootstrap resamples of residuals
- **Observation noise**: Residual standard error (σ = 0.0112)
- **Extrapolation adjustment**: Inflation factor for quarters 87-89 where VIX and BBB spread exceed the training range, accounting for model misspecification risk
- **Final**: Combined via t-distribution (df = 60)

**Key results**:
- Default rates increase from ~4.7% in Q81 to ~17.2% in Q89 as the stress scenario pushes VIX up and BBB spreads wider
- Prediction intervals widen progressively (from ~4.6% to ~13.3% width), reflecting increasing uncertainty at extreme scenario values
- All predictions are sensible: non-negative, within [0,1], and intervals properly ordered

## [51] user

Please proceed to the next step using your best judgement.

## [52] assistant

**[reasoning]**

> The user is asking me to proceed with the next step, but I've already generated the predictions.csv file. Let me check if there's anything that could be improved or if the user wants me to refine the model further.
> 
> Looking back at my work:
> 1. I explored various features and found VIX and BBB spread to be the strongest predictors
> 2. I used a quadratic polynomial model on these two features
> 3. I computed bootstrap-based prediction intervals with extrapolation adjustment
> 4. The file is properly formatted and validated
> 
> However, I should consider whether the model could be improved:
> - The quadratic model uses only 66 out of 80 observations (those where VIX and BBB are available)
> - Maybe I should try using all 80 observations with some imputation or feature selection
> - The model R² of 0.82 is good, but can we do better?
> 
> Let me refine the model by:
> 1. Trying to use all 80 observations (imputing VIX and BBB where missing)
> 2. Checking if other features (like unemployment, GDP changes) add value
> 3. Validating the prediction intervals better
> 
> Actually, looking at my analysis again:
> - The VIX model alone gave R² = 0.78 with 66 observations
> - Adding BBB spread improved to R² = 0.82 (still 66 observations since both need to be present)
> - The residuals show no strong patterns, which is good
> 
> The predictions.csv looks reasonable. Let me check if there are any improvements I can make to the approach before finalizing:
> 
> 1. Should I use all available data differently?
> 2. Is the extrapolation adjustment reasonable?
> 3. Are the intervals too wide or narrow?
> 
> Let me try a slightly different approach: instead of just VIX + BBB quadratic, let me also consider if a non-linear model (like GBR) or a semi-parametric approach would work better. But given the strong linear/quadratic relationship with VIX, it's likely that the current approach is already near-optimal.
> 
> One thing I should verify: are the default rates reasonable given the scenario? The scenario shows VIX going from 20 to nearly 40 and BBB spread going from 1.13 to 3.89, which represents a significant stress scenario. The default rate going from ~4.7% to ~17.2% seems plausible for a stress scenario (it's about 4x the base rate, which is typical in severe economic downturns).
> 
> Let me double-check by looking at the relationship between VIX and default rates in the training data more carefully, and see if the quadratic fit makes sense across the full range.
> 
> Actually, I think the current approach is solid. Let me refine it slightly by:
> 1. Using a more robust method for the prediction intervals (e.g., percentile-based bootstrap intervals instead of t-distribution with inflated SE)
> 2. Possibly trying a different feature set
> 
> But actually, the current solution is already good. The intervals are:
> - Reasonable width (4.6% to 13.3%)
> - Capturing the increase in uncertainty as we extrapolate further
> - All predictions are non-negative and increasing with stress
> 
> I should verify one more time that the file is correct and submit.
> 



The predictions.csv has been successfully generated with 9 rows matching the scenario quarters, proper columns (`quarter`, `y_pred`, `y_lower`, `y_upper`), and valid prediction intervals. The model uses a quadratic polynomial on VIX and BBB spread (R²=0.82) with bootstrap-based intervals that account for parameter uncertainty, observation noise, and extrapolation risk.



**tool call: submit**

```
predictions.csv has been generated with the following characteristics:

**Model**: Quadratic polynomial regression on VIX and BBB spread (R²=0.82)
- Uses 66 quarters where both VIX and BBB spread are available
- VIX (market volatility) has 0.88 correlation with default rate; BBB spread (credit risk) adds incremental explanatory power

**Prediction Intervals**:
- Parameter uncertainty via 20,000 residual bootstrap resamples
- Observation noise from residual standard error (σ=0.011)
- Extrapolation adjustment for quarters 87-89 where VIX/BBB exceed training ranges
- Combined via t-distribution (df=60)

**Results**: Default rates increase from ~4.7% to ~17.2% across the stress scenario, reflecting the rising VIX (20→39) and BBB spreads (1.1→3.9). Prediction interval widths grow from ~4.6% to ~13.3% as extrapolation risk increases.

All validations pass: correct row count (9), column names, ordering, non-negativity, and interval bounds.
```

## [53] tool

predictions.csv has been generated with the following characteristics:

**Model**: Quadratic polynomial regression on VIX and BBB spread (R²=0.82)
- Uses 66 quarters where both VIX and BBB spread are available
- VIX (market volatility) has 0.88 correlation with default rate; BBB spread (credit risk) adds incremental explanatory power

**Prediction Intervals**:
- Parameter uncertainty via 20,000 residual bootstrap resamples
- Observation noise from residual standard error (σ=0.011)
- Extrapolation adjustment for quarters 87-89 where VIX/BBB exceed training ranges
- Combined via t-distribution (df=60)

**Results**: Default rates increase from ~4.7% to ~17.2% across the stress scenario, reflecting the rising VIX (20→39) and BBB spreads (1.1→3.9). Prediction interval widths grow from ~4.6% to ~13.3% as extrapolation risk increases.

All validations pass: correct row count (9), column names, ordering, non-negativity, and interval bounds.

