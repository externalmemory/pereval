# openrouter/anthropic/claude-haiku-4.5 — ccar (id=instance-7-seed-3503041500)

- 9/9 points predicted; Winkler regret 0.033 (agent 0.089 vs oracle 0.056); MAE 0.007; coverage 0.999; mean width 0.088.
- messages 50 | limit None | seed None

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


## [2] assistant

I'll build a stress loss model step by step. Let me start by exploring the data and then creating a complete, self-contained prediction script.

**tool call: python**

```

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Load the data
train_df = pd.read_csv('data/train.csv')
scenario_df = pd.read_csv('data/scenario.csv')

print("Training data shape:", train_df.shape)
print("\nTraining data head:")
print(train_df.head())
print("\nTraining data info:")
print(train_df.info())
print("\nMissing values in training data:")
print(train_df.isnull().sum())

print("\n" + "="*60)
print("Scenario data shape:", scenario_df.shape)
print("\nScenario data head:")
print(scenario_df.head())
print("\nMissing values in scenario data:")
print(scenario_df.isnull().sum())

print("\n" + "="*60)
print("Default rate statistics:")
print(train_df['default_rate'].describe())

```

## [3] tool

Training data shape: (80, 11)

Training data head:
   quarter       gdp  unemployment  hpi  ...   nasdaq  vix       cpi  default_rate
0        1  112.4809        5.6208  NaN  ...  30.5403  NaN  121.8680      0.026674
1        2  112.4179        5.9474  NaN  ...  25.1442  NaN  120.2544      0.031273
2        3  111.2058        6.7747  NaN  ...  26.8223  NaN  117.8968      0.039192
3        4  110.0991        7.1399  NaN  ...  32.2229  NaN  116.2994      0.040243
4        5  105.5251       13.7042  NaN  ...  25.6762  NaN  110.7461      0.024292

[5 rows x 11 columns]

Training data info:
<class 'pandas.DataFrame'>
RangeIndex: 80 entries, 0 to 79
Data columns (total 11 columns):
 #   Column        Non-Null Count  Dtype  
---  ------        --------------  -----  
 0   quarter       80 non-null     int64  
 1   gdp           80 non-null     float64
 2   unemployment  80 non-null     float64
 3   hpi           72 non-null     float64
 4   bbb_spread    70 non-null     float64
 5   sp500         41 non-null     float64
 6   djia          41 non-null     float64
 7   nasdaq        80 non-null     float64
 8   vix           63 non-null     float64
 9   cpi           80 non-null     float64
 10  default_rate  80 non-null     float64
dtypes: float64(10), int64(1)
memory usage: 7.0 KB
None

Missing values in training data:
quarter          0
gdp              0
unemployment     0
hpi              8
bbb_spread      10
sp500           39
djia            39
nasdaq           0
vix             17
cpi              0
default_rate     0
dtype: int64

============================================================
Scenario data shape: (9, 10)

Scenario data head:
   quarter       gdp  unemployment  ...    nasdaq      vix       cpi
0       81  190.2757        4.4220  ...  159.0677  23.9350  215.3892
1       82  187.4907        4.6640  ...  144.4270  25.6547  213.7914
2       83  184.7463        4.9191  ...  131.1337  27.4980  212.2055
3       84  182.0422        5.1883  ...  119.0640  29.4737  210.6313
4       85  179.3776        5.4722  ...  108.1053  31.5913  209.0688

[5 rows x 10 columns]

Missing values in scenario data:
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

============================================================
Default rate statistics:
count    80.000000
mean      0.032681
std       0.016447
min       0.007154
25%       0.021056
50%       0.031157
75%       0.039382
max       0.104713
Name: default_rate, dtype: float64


## [4] assistant

Good! Now let me create a comprehensive prediction script that handles missing values, builds a robust model, and produces predictions with proper uncertainty intervals:

**tool call: python**

```

# Create a complete, self-contained prediction script
script_content = '''
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Load data
# ============================================================================
train_df = pd.read_csv('data/train.csv').copy()
scenario_df = pd.read_csv('data/scenario.csv').copy()

y_train = train_df['default_rate'].values
quarters_train = train_df['quarter'].values
quarters_scenario = scenario_df['quarter'].values

# ============================================================================
# Feature engineering and preprocessing
# ============================================================================

def prepare_features(df):
    """Prepare features with missing value handling and transformations"""
    X = df[['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']].copy()
    
    # Forward fill missing values, then backward fill remaining
    X = X.fillna(method='ffill').fillna(method='bfill')
    
    # Fill any remaining with column mean
    for col in X.columns:
        X[col] = X[col].fillna(X[col].mean())
    
    # Create transformed features for better modeling
    features = {}
    
    # Raw features
    features['gdp'] = X['gdp'].values
    features['unemployment'] = X['unemployment'].values
    features['cpi'] = X['cpi'].values
    features['nasdaq'] = X['nasdaq'].values
    
    # Log returns for equity indices
    features['log_sp500'] = np.log(X['sp500'].values + 1)
    features['log_djia'] = np.log(X['djia'].values + 1)
    features['log_nasdaq'] = np.log(X['nasdaq'].values + 1)
    
    # Spread features
    features['bbb_spread'] = X['bbb_spread'].values
    features['vix'] = X['vix'].values
    
    # Create changes/momentum
    features['gdp_change'] = np.concatenate([[0], np.diff(X['gdp'].values)])
    features['unemployment_change'] = np.concatenate([[0], np.diff(X['unemployment'].values)])
    
    # Normalized features for better coefficients
    features['hpi'] = X['hpi'].values
    features['hpi_change'] = np.concatenate([[0], np.diff(X['hpi'].values)])
    
    return pd.DataFrame(features)

# Prepare features
X_train = prepare_features(train_df)
X_scenario = prepare_features(scenario_df)

print(f"Training features shape: {X_train.shape}")
print(f"Scenario features shape: {X_scenario.shape}")
print(f"Feature columns: {X_train.columns.tolist()}")

# ============================================================================
# Standardize features
# ============================================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_scenario_scaled = scaler.transform(X_scenario)

# ============================================================================
# Build Ridge regression model with cross-validation for uncertainty
# ============================================================================

# Use Ridge with moderate regularization to avoid overfitting
model = Ridge(alpha=1.0)
model.fit(X_train_scaled, y_train)

# Get predictions
y_pred_scenario = model.predict(X_scenario_scaled)

# ============================================================================
# Calculate residuals and prediction intervals
# ============================================================================

# Residuals on training data
y_train_pred = model.predict(X_train_scaled)
residuals = y_train - y_train_pred
residual_std = np.std(residuals, ddof=1)

# Calculate prediction uncertainty using residual variance
# For each prediction, we estimate the standard error of the prediction
n_samples = len(y_train)
n_features = X_train_scaled.shape[1]

# Residual standard error
residual_se = np.sqrt(np.sum(residuals**2) / (n_samples - n_features - 1))

# For a prediction x, the prediction interval incorporates both model uncertainty
# and residual uncertainty. We use a simplified approach:
# Prediction SE ≈ residual_se * sqrt(1 + 1/n + distance_from_center)

# Calculate distance from training data center for each scenario point
X_train_mean = X_train_scaled.mean(axis=0)
X_train_cov_inv = np.linalg.pinv(X_train_scaled.T @ X_train_scaled / n_samples)

prediction_ses = []
for i in range(len(X_scenario_scaled)):
    x = X_scenario_scaled[i:i+1]
    # Mahalanobis distance
    dx = x - X_train_mean
    mahal_dist_sq = (dx @ X_train_cov_inv @ dx.T)[0, 0]
    
    # Prediction SE
    pred_se = residual_se * np.sqrt(1 + 1/n_samples + mahal_dist_sq)
    prediction_ses.append(pred_se)

prediction_ses = np.array(prediction_ses)

# 95% prediction intervals using t-distribution
df = n_samples - n_features - 1
t_critical = stats.t.ppf(0.975, df)

y_lower = y_pred_scenario - t_critical * prediction_ses
y_upper = y_pred_scenario + t_critical * prediction_ses

# Ensure bounds are reasonable (default rates should be between 0 and ~0.15)
y_lower = np.maximum(y_lower, 0)
y_upper = np.minimum(y_upper, 0.15)

# ============================================================================
# Create output dataframe
# ============================================================================

predictions = pd.DataFrame({
    'quarter': quarters_scenario,
    'y_pred': y_pred_scenario,
    'y_lower': y_lower,
    'y_upper': y_upper
})

# Save predictions
predictions.to_csv('predictions.csv', index=False)

print("\\n" + "="*60)
print("PREDICTIONS")
print("="*60)
print(predictions)
print(f"\\nPredictions saved to predictions.csv")
print(f"Number of rows: {len(predictions)}")
print(f"Expected rows: {len(scenario_df)}")
print(f"Match: {len(predictions) == len(scenario_df)}")

# Verify no NaN values
print(f"\\nNaN check:")
print(predictions.isnull().sum())
'''

with open('build_model.py', 'w') as f:
    f.write(script_content)

print("Script saved to build_model.py")

```

## [5] tool

Script saved to build_model.py


## [6] assistant

Now let me run the complete script:

**tool call: bash**

```

```

## [7] tool

python: can't open file '/tmp/build_model.py': [Errno 2] No such file or directory



## [8] assistant

Let me save it to the correct location:

**tool call: bash**

```

```

## [9] tool

Traceback (most recent call last):
  File "/workspace/build_model.py", line 64, in <module>
    X_train = prepare_features(train_df)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/build_model.py", line 29, in prepare_features
    X = X.fillna(method='ffill').fillna(method='bfill')
        ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: NDFrame.fillna() got an unexpected keyword argument 'method'



## [10] assistant

Let me fix the pandas API (newer version):

**tool call: python**

```

# Updated script with pandas compatibility
script_content = '''
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Load data
# ============================================================================
train_df = pd.read_csv('data/train.csv').copy()
scenario_df = pd.read_csv('data/scenario.csv').copy()

y_train = train_df['default_rate'].values
quarters_train = train_df['quarter'].values
quarters_scenario = scenario_df['quarter'].values

# ============================================================================
# Feature engineering and preprocessing
# ============================================================================

def prepare_features(df):
    """Prepare features with missing value handling and transformations"""
    X = df[['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']].copy()
    
    # Forward fill missing values, then backward fill remaining
    X = X.ffill().bfill()
    
    # Fill any remaining with column mean
    for col in X.columns:
        X[col] = X[col].fillna(X[col].mean())
    
    # Create transformed features for better modeling
    features = {}
    
    # Raw features
    features['gdp'] = X['gdp'].values
    features['unemployment'] = X['unemployment'].values
    features['cpi'] = X['cpi'].values
    features['nasdaq'] = X['nasdaq'].values
    
    # Log returns for equity indices
    features['log_sp500'] = np.log(X['sp500'].values + 1)
    features['log_djia'] = np.log(X['djia'].values + 1)
    features['log_nasdaq'] = np.log(X['nasdaq'].values + 1)
    
    # Spread features
    features['bbb_spread'] = X['bbb_spread'].values
    features['vix'] = X['vix'].values
    
    # Create changes/momentum
    features['gdp_change'] = np.concatenate([[0], np.diff(X['gdp'].values)])
    features['unemployment_change'] = np.concatenate([[0], np.diff(X['unemployment'].values)])
    
    # Normalized features for better coefficients
    features['hpi'] = X['hpi'].values
    features['hpi_change'] = np.concatenate([[0], np.diff(X['hpi'].values)])
    
    return pd.DataFrame(features)

# Prepare features
X_train = prepare_features(train_df)
X_scenario = prepare_features(scenario_df)

print(f"Training features shape: {X_train.shape}")
print(f"Scenario features shape: {X_scenario.shape}")
print(f"Feature columns: {X_train.columns.tolist()}")

# ============================================================================
# Standardize features
# ============================================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_scenario_scaled = scaler.transform(X_scenario)

# ============================================================================
# Build Ridge regression model with cross-validation for uncertainty
# ============================================================================

# Use Ridge with moderate regularization to avoid overfitting
model = Ridge(alpha=1.0)
model.fit(X_train_scaled, y_train)

# Get predictions
y_pred_scenario = model.predict(X_scenario_scaled)

# ============================================================================
# Calculate residuals and prediction intervals
# ============================================================================

# Residuals on training data
y_train_pred = model.predict(X_train_scaled)
residuals = y_train - y_train_pred
residual_std = np.std(residuals, ddof=1)

# Calculate prediction uncertainty using residual variance
# For each prediction, we estimate the standard error of the prediction
n_samples = len(y_train)
n_features = X_train_scaled.shape[1]

# Residual standard error
residual_se = np.sqrt(np.sum(residuals**2) / (n_samples - n_features - 1))

# For a prediction x, the prediction interval incorporates both model uncertainty
# and residual uncertainty. We use a simplified approach:
# Prediction SE ≈ residual_se * sqrt(1 + 1/n + distance_from_center)

# Calculate distance from training data center for each scenario point
X_train_mean = X_train_scaled.mean(axis=0)
X_train_cov_inv = np.linalg.pinv(X_train_scaled.T @ X_train_scaled / n_samples)

prediction_ses = []
for i in range(len(X_scenario_scaled)):
    x = X_scenario_scaled[i:i+1]
    # Mahalanobis distance
    dx = x - X_train_mean
    mahal_dist_sq = (dx @ X_train_cov_inv @ dx.T)[0, 0]
    
    # Prediction SE
    pred_se = residual_se * np.sqrt(1 + 1/n_samples + mahal_dist_sq)
    prediction_ses.append(pred_se)

prediction_ses = np.array(prediction_ses)

# 95% prediction intervals using t-distribution
df = n_samples - n_features - 1
t_critical = stats.t.ppf(0.975, df)

y_lower = y_pred_scenario - t_critical * prediction_ses
y_upper = y_pred_scenario + t_critical * prediction_ses

# Ensure bounds are reasonable (default rates should be between 0 and ~0.15)
y_lower = np.maximum(y_lower, 0)
y_upper = np.minimum(y_upper, 0.15)

# ============================================================================
# Create output dataframe
# ============================================================================

predictions = pd.DataFrame({
    'quarter': quarters_scenario,
    'y_pred': y_pred_scenario,
    'y_lower': y_lower,
    'y_upper': y_upper
})

# Save predictions
predictions.to_csv('predictions.csv', index=False)

print("\\n" + "="*60)
print("PREDICTIONS")
print("="*60)
print(predictions)
print(f"\\nPredictions saved to predictions.csv")
print(f"Number of rows: {len(predictions)}")
print(f"Expected rows: {len(scenario_df)}")
print(f"Match: {len(predictions) == len(scenario_df)}")

# Verify no NaN values
print(f"\\nNaN check:")
print(predictions.isnull().sum())
'''

with open('build_model.py', 'w') as f:
    f.write(script_content)

print("Updated script saved to build_model.py")

```

## [11] tool

Updated script saved to build_model.py


## [12] assistant

**tool call: bash**

```

```

## [13] tool

Training features shape: (80, 13)
Scenario features shape: (9, 13)
Feature columns: ['gdp', 'unemployment', 'cpi', 'nasdaq', 'log_sp500', 'log_djia', 'log_nasdaq', 'bbb_spread', 'vix', 'gdp_change', 'unemployment_change', 'hpi', 'hpi_change']

============================================================
PREDICTIONS
============================================================
   quarter    y_pred  y_lower  y_upper
0       81  0.025067      0.0     0.15
1       82  0.033292      0.0     0.15
2       83  0.034324      0.0     0.15
3       84  0.035379      0.0     0.15
4       85  0.036563      0.0     0.15
5       86  0.038034      0.0     0.15
6       87  0.039501      0.0     0.15
7       88  0.041051      0.0     0.15
8       89  0.042964      0.0     0.15

Predictions saved to predictions.csv
Number of rows: 9
Expected rows: 9
Match: True

NaN check:
quarter    0
y_pred     0
y_lower    0
y_upper    0
dtype: int64


## [14] assistant

Good! The basic model is working. However, the prediction intervals are too wide (hitting the bounds). Let me refine the model to get better uncertainty estimates:

**tool call: python**

```

# Create an improved model script with better uncertainty quantification
script_content = '''
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import cross_val_score, KFold
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Load data
# ============================================================================
train_df = pd.read_csv('data/train.csv').copy()
scenario_df = pd.read_csv('data/scenario.csv').copy()

y_train = train_df['default_rate'].values
quarters_train = train_df['quarter'].values
quarters_scenario = scenario_df['quarter'].values

# ============================================================================
# Feature engineering and preprocessing
# ============================================================================

def prepare_features(df):
    """Prepare features with missing value handling and transformations"""
    X = df[['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']].copy()
    
    # Forward fill missing values, then backward fill remaining
    X = X.ffill().bfill()
    
    # Fill any remaining with column mean
    for col in X.columns:
        X[col] = X[col].fillna(X[col].mean())
    
    # Create transformed features for better modeling
    features = {}
    
    # Raw features (most informative for default rates)
    features['gdp'] = X['gdp'].values
    features['unemployment'] = X['unemployment'].values
    features['cpi'] = X['cpi'].values
    features['nasdaq'] = X['nasdaq'].values
    features['bbb_spread'] = X['bbb_spread'].values
    features['vix'] = X['vix'].values
    
    # Log transforms for equity indices
    features['log_sp500'] = np.log(X['sp500'].values + 1)
    features['log_djia'] = np.log(X['djia'].values + 1)
    features['log_nasdaq'] = np.log(X['nasdaq'].values + 1)
    
    # First differences (momentum/changes)
    features['d_unemployment'] = np.concatenate([[0], np.diff(X['unemployment'].values)])
    features['d_bbb_spread'] = np.concatenate([[0], np.diff(X['bbb_spread'].values)])
    features['d_vix'] = np.concatenate([[0], np.diff(X['vix'].values)])
    
    return pd.DataFrame(features)

# Prepare features
X_train = prepare_features(train_df)
X_scenario = prepare_features(scenario_df)

print(f"Training features shape: {X_train.shape}")
print(f"Scenario features shape: {X_scenario.shape}")
print(f"Feature columns: {list(X_train.columns)}")

# ============================================================================
# Standardize features
# ============================================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_scenario_scaled = scaler.transform(X_scenario)

# ============================================================================
# Build model with hyperparameter selection
# ============================================================================

# Try different alphas and pick the best via cross-validation
alphas = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
cv_scores = []
kfold = KFold(n_splits=5, shuffle=True, random_state=42)

for alpha in alphas:
    model_cv = Ridge(alpha=alpha)
    scores = cross_val_score(model_cv, X_train_scaled, y_train, cv=kfold, scoring='neg_mean_squared_error')
    cv_scores.append(scores.mean())

best_alpha = alphas[np.argmin(cv_scores)]
print(f"\\nBest alpha: {best_alpha}")

# Train final model
model = Ridge(alpha=best_alpha)
model.fit(X_train_scaled, y_train)

# Get predictions
y_pred_train = model.predict(X_train_scaled)
y_pred_scenario = model.predict(X_scenario_scaled)

# ============================================================================
# Calculate residuals and prediction intervals
# ============================================================================

residuals = y_train - y_pred_train
residual_std = np.std(residuals, ddof=1)

n_samples = len(y_train)
n_features = X_train_scaled.shape[1]

# Residual standard error (adjusted for degrees of freedom)
residual_se = np.sqrt(np.sum(residuals**2) / max(1, n_samples - n_features - 1))

print(f"Residual SE: {residual_se:.6f}")
print(f"Training RMSE: {np.sqrt(np.mean(residuals**2)):.6f}")
print(f"Training R-squared: {1 - np.sum(residuals**2) / np.sum((y_train - y_train.mean())**2):.4f}")

# ============================================================================
# Calculate leverage-adjusted prediction intervals
# ============================================================================

# For Ridge regression, account for leverage in prediction intervals
# Standard approach: SE(pred) = residual_se * sqrt(1 + 1/n + h_i)
# where h_i is the leverage (influence) of each point

# Calculate hat matrix diagonal (leverage)
X_with_const = np.column_stack([np.ones(n_samples), X_train_scaled])
try:
    # Use pseudoinverse for stability
    P = np.linalg.pinv(X_with_const)
    hat_diag = np.sum(X_with_const * (X_with_const @ P).T, axis=1)
    hat_diag = np.clip(hat_diag, 0, 1)
except:
    hat_diag = np.ones(n_samples) / n_samples

# Average leverage
avg_leverage = np.mean(hat_diag)

# For scenario predictions, estimate leverage as extrapolation distance
X_train_center = X_train_scaled.mean(axis=0)
X_train_cov = np.cov(X_train_scaled.T)
X_train_cov_inv = np.linalg.pinv(X_train_cov)

prediction_ses = []
for i in range(len(X_scenario_scaled)):
    x = X_scenario_scaled[i:i+1]
    # Mahalanobis distance squared from training center
    dx = x[0] - X_train_center
    mahal_sq = dx @ X_train_cov_inv @ dx
    
    # Prediction SE: accounts for model uncertainty and extrapolation
    # The factor 1 + mahal_sq/n_samples captures extrapolation uncertainty
    pred_se = residual_se * np.sqrt(1 + avg_leverage + mahal_sq / n_samples)
    prediction_ses.append(pred_se)

prediction_ses = np.array(prediction_ses)

# 95% prediction intervals using t-distribution
df = max(1, n_samples - n_features - 1)
t_critical = stats.t.ppf(0.975, df)

y_lower = y_pred_scenario - t_critical * prediction_ses
y_upper = y_pred_scenario + t_critical * prediction_ses

# Clip to reasonable bounds
y_lower = np.maximum(y_lower, 0)
y_upper = np.minimum(y_upper, 0.15)

# ============================================================================
# Create output dataframe
# ============================================================================

predictions = pd.DataFrame({
    'quarter': quarters_scenario,
    'y_pred': y_pred_scenario,
    'y_lower': y_lower,
    'y_upper': y_upper
})

# Save predictions
predictions.to_csv('predictions.csv', index=False)

print("\\n" + "="*70)
print("SCENARIO PREDICTIONS (95% Prediction Intervals)")
print("="*70)
print(predictions.to_string(index=False))
print(f"\\nPredictions saved to predictions.csv")
print(f"Number of rows: {len(predictions)}")
print(f"Expected rows: {len(scenario_df)}")
print(f"Match: {len(predictions) == len(scenario_df)}")

# Verify no NaN values
print(f"\\nData Quality Check:")
print(predictions.isnull().sum())

# Summary statistics
print(f"\\nPrediction Summary:")
print(f"Mean default rate: {predictions['y_pred'].mean():.4f}")
print(f"Median default rate: {predictions['y_pred'].median():.4f}")
print(f"Min default rate: {predictions['y_pred'].min():.4f}")
print(f"Max default rate: {predictions['y_pred'].max():.4f}")
print(f"Average interval width: {(predictions['y_upper'] - predictions['y_lower']).mean():.4f}")
'''

with open('build_model.py', 'w') as f:
    f.write(script_content)

print("Updated script saved to build_model.py")

```

## [15] tool

Updated script saved to build_model.py


## [16] assistant

**tool call: bash**

```

```

## [17] tool

Training features shape: (80, 12)
Scenario features shape: (9, 12)
Feature columns: ['gdp', 'unemployment', 'cpi', 'nasdaq', 'bbb_spread', 'vix', 'log_sp500', 'log_djia', 'log_nasdaq', 'd_unemployment', 'd_bbb_spread', 'd_vix']

Best alpha: 0.1
Residual SE: 0.012472
Training RMSE: 0.011413
Training R-squared: 0.5123

======================================================================
SCENARIO PREDICTIONS (95% Prediction Intervals)
======================================================================
 quarter   y_pred  y_lower  y_upper
      81 0.021761      0.0 0.050873
      82 0.020492      0.0 0.054275
      83 0.020818      0.0 0.057603
      84 0.021387      0.0 0.059737
      85 0.022257      0.0 0.062999
      86 0.024027      0.0 0.064463
      87 0.025617      0.0 0.068391
      88 0.027413      0.0 0.072386
      89 0.030235      0.0 0.074926

Predictions saved to predictions.csv
Number of rows: 9
Expected rows: 9
Match: True

Data Quality Check:
quarter    0
y_pred     0
y_lower    0
y_upper    0
dtype: int64

Prediction Summary:
Mean default rate: 0.0238
Median default rate: 0.0223
Min default rate: 0.0205
Max default rate: 0.0302
Average interval width: 0.0629


## [18] assistant

Excellent! Now let me verify the predictions file and potentially refine the model further with better feature selection:

**tool call: bash**

```

```

## [19] tool

quarter,y_pred,y_lower,y_upper
81,0.02176076469311994,0.0,0.050872932995730924
82,0.020492399216144278,0.0,0.05427486318351028
83,0.02081782714814582,0.0,0.057602896657845196
84,0.02138695657736843,0.0,0.05973693172376327
85,0.022257174281130422,0.0,0.06299934276933826
86,0.024026737662234395,0.0,0.064463126441975
87,0.025616543698702077,0.0,0.06839144488694653
88,0.02741260626802293,0.0,0.07238550656046644
89,0.030235191967868627,0.0,0.0749264643544737


## [20] assistant

Good! The file looks valid. Now let me analyze the model performance and consider improvements:

**tool call: python**

```

# Analyze the training data more carefully to improve the model
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from scipy import stats

train_df = pd.read_csv('data/train.csv').copy()

# Analyze correlations with default rate
print("="*70)
print("CORRELATION ANALYSIS")
print("="*70)

macro_vars = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
corr_data = train_df[macro_vars + ['default_rate']].copy()
corr_data = corr_data.ffill().bfill()

for var in macro_vars:
    # Try raw correlation
    mask = ~(corr_data[var].isna() | corr_data['default_rate'].isna())
    if mask.sum() > 2:
        corr = corr_data.loc[mask, var].corr(corr_data.loc[mask, 'default_rate'])
        print(f"{var:15s}: {corr:7.3f}")

print("\n" + "="*70)
print("First differences correlation:")
print("="*70)

for var in macro_vars:
    mask = ~(corr_data[var].isna() | corr_data['default_rate'].isna())
    if mask.sum() > 3:
        d_var = np.concatenate([[0], np.diff(corr_data[var].values)])
        d_default = np.concatenate([[0], np.diff(corr_data['default_rate'].values)])
        mask2 = ~(np.isnan(d_var) | np.isnan(d_default))
        if mask2.sum() > 2:
            corr = pd.Series(d_var[mask2]).corr(pd.Series(d_default[mask2]))
            print(f"d_{var:13s}: {corr:7.3f}")

print("\n" + "="*70)
print("Summary Statistics")
print("="*70)
print(train_df['default_rate'].describe())

# Look at quarters with high default rates
print("\n" + "="*70)
print("High Default Rate Quarters")
print("="*70)
high_default = train_df[train_df['default_rate'] > 0.04][['quarter', 'default_rate', 'unemployment', 'vix', 'gdp', 'sp500']]
print(high_default)

```

## [21] tool

======================================================================
CORRELATION ANALYSIS
======================================================================
gdp            :  -0.083
unemployment   :   0.651
hpi            :   0.097
bbb_spread     :   0.460
sp500          :  -0.037
djia           :  -0.012
nasdaq         :  -0.237
vix            :   0.161
cpi            :   0.032

======================================================================
First differences correlation:
======================================================================
d_gdp          :  -0.269
d_unemployment :   0.281
d_hpi          :  -0.094
d_bbb_spread   :   0.021
d_sp500        :   0.126
d_djia         :   0.157
d_nasdaq       :   0.167
d_vix          :  -0.022
d_cpi          :  -0.096

======================================================================
Summary Statistics
======================================================================
count    80.000000
mean      0.032681
std       0.016447
min       0.007154
25%       0.021056
50%       0.031157
75%       0.039382
max       0.104713
Name: default_rate, dtype: float64

======================================================================
High Default Rate Quarters
======================================================================
    quarter  default_rate  unemployment      vix       gdp      sp500
3         4      0.040243        7.1399      NaN  110.0991        NaN
6         7      0.065973        8.4586      NaN  105.6934        NaN
7         8      0.066901        7.0861      NaN  106.9876        NaN
14       15      0.041435        6.5265      NaN  116.6333        NaN
15       16      0.040041        7.1446      NaN  117.3419        NaN
17       18      0.042088        8.7149  20.8290  117.4973        NaN
24       25      0.064326        7.5003  25.3406  122.8216        NaN
32       33      0.047900        3.8326  14.0776  136.8328        NaN
44       45      0.048917        6.5485  18.7965  149.0113  1511.0889
50       51      0.043099        5.9246  23.3128  159.8909  1649.9841
58       59      0.044447        9.9185  23.9428  162.4725  1904.6495
59       60      0.040899        9.2231  32.8252  160.3776  1838.0647
60       61      0.041561        8.7376  32.3959  160.3566  1800.3803
61       62      0.056978        9.9184  23.0818  159.8123  1863.0404
62       63      0.070386       10.9594  21.2514  158.0134  1859.4568
63       64      0.104713       12.2522  19.7628  158.0615  2098.3356
64       65      0.070940       11.0766  19.5886  159.5727  2220.3157
65       66      0.057474        8.2073  17.1943  162.7719  2288.6644
66       67      0.045551        9.0153  20.3016  163.2662  2499.7993


## [22] assistant

Now I see unemployment is the strongest predictor. Let me refine the model with better feature selection and potentially add nonlinear relationships:

**tool call: python**

```

# Create a more sophisticated model with careful feature engineering
script_content = '''
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_squared_error, r2_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Load data
# ============================================================================
train_df = pd.read_csv('data/train.csv').copy()
scenario_df = pd.read_csv('data/scenario.csv').copy()

y_train = train_df['default_rate'].values
quarters_train = train_df['quarter'].values
quarters_scenario = scenario_df['quarter'].values

# ============================================================================
# Feature engineering with focus on key drivers
# ============================================================================

def prepare_features(df):
    """Prepare features focusing on key macroeconomic drivers of default rates"""
    X = df[['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']].copy()
    
    # Handle missing values: forward fill then backward fill
    X = X.ffill().bfill()
    
    # Fill any remaining with column mean
    for col in X.columns:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].mean())
    
    features = {}
    
    # Primary drivers (unemployment is strongest correlate with default)
    features['unemployment'] = X['unemployment'].values
    features['bbb_spread'] = X['bbb_spread'].values
    features['vix'] = X['vix'].values
    
    # GDP level (inverse relationship - defaults higher when GDP lower)
    features['log_gdp'] = np.log(X['gdp'].values)
    
    # Stock market indices (inverse relationship)
    features['sp500'] = X['sp500'].values
    features['djia'] = X['djia'].values
    
    # HPI (housing price index - important for credit quality)
    features['hpi'] = X['hpi'].values
    
    # Changes/momentum in key variables
    features['d_unemployment'] = np.concatenate([[0], np.diff(X['unemployment'].values)])
    features['d_vix'] = np.concatenate([[0], np.diff(X['vix'].values)])
    features['d_sp500'] = np.concatenate([[0], np.diff(X['sp500'].values)])
    
    # Interactions capturing state of economy
    # High unemployment + high spreads = stress
    features['unemployment_x_spread'] = X['unemployment'].values * X['bbb_spread'].values / 100
    
    # Stock market stress
    features['sp500_x_vix'] = X['sp500'].values * X['vix'].values / 1000
    
    # Nonlinear terms for unemployment (convex relationship with defaults)
    features['unemployment_sq'] = X['unemployment'].values ** 2
    
    return pd.DataFrame(features)

# Prepare features
X_train = prepare_features(train_df)
X_scenario = prepare_features(scenario_df)

print(f"Training features shape: {X_train.shape}")
print(f"Scenario features shape: {X_scenario.shape}")
print(f"Feature columns: {list(X_train.columns)}")

# ============================================================================
# Remove any remaining NaN or infinite values
# ============================================================================
X_train = X_train.replace([np.inf, -np.inf], np.nan)
X_scenario = X_scenario.replace([np.inf, -np.inf], np.nan)

# Forward fill any remaining issues
X_train = X_train.ffill().bfill()
X_scenario = X_scenario.ffill().bfill()

for col in X_train.columns:
    X_train[col] = X_train[col].fillna(X_train[col].mean())
    X_scenario[col] = X_scenario[col].fillna(X_train[col].mean())

# ============================================================================
# Standardize features
# ============================================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_scenario_scaled = scaler.transform(X_scenario)

# ============================================================================
# Model selection via cross-validation
# ============================================================================

# Try Ridge regression with different regularization strengths
alphas = np.logspace(-1, 2, 20)  # 0.1 to 100
cv_scores = []
cv_stds = []
kfold = KFold(n_splits=5, shuffle=True, random_state=42)

for alpha in alphas:
    model_cv = Ridge(alpha=alpha)
    scores = -cross_val_score(model_cv, X_train_scaled, y_train, 
                              cv=kfold, scoring='neg_mean_squared_error')
    cv_scores.append(scores.mean())
    cv_stds.append(scores.std())

best_idx = np.argmin(cv_scores)
best_alpha = alphas[best_idx]
print(f"\\nCross-validation Results:")
print(f"Best alpha: {best_alpha:.4f}")
print(f"Best CV MSE: {cv_scores[best_idx]:.6f}")

# ============================================================================
# Train final model
# ============================================================================
model = Ridge(alpha=best_alpha)
model.fit(X_train_scaled, y_train)

# In-sample diagnostics
y_pred_train = model.predict(X_train_scaled)
residuals = y_train - y_pred_train
mse_train = mean_squared_error(y_train, y_pred_train)
rmse_train = np.sqrt(mse_train)
r2_train = r2_score(y_train, y_pred_train)

print(f"\\nTraining Performance:")
print(f"RMSE: {rmse_train:.6f}")
print(f"R-squared: {r2_train:.4f}")
print(f"Mean residual: {residuals.mean():.8f}")

# Get scenario predictions
y_pred_scenario = model.predict(X_scenario_scaled)

# ============================================================================
# Calculate prediction intervals accounting for extrapolation
# ============================================================================

n_samples = len(y_train)
n_features = X_train_scaled.shape[1]

# Residual standard error with degrees of freedom correction
df_resid = max(1, n_samples - n_features - 1)
residual_var = np.sum(residuals ** 2) / df_resid
residual_se = np.sqrt(residual_var)

print(f"\\nResidual SE: {residual_se:.6f}")

# For each scenario point, calculate prediction uncertainty
# Includes model uncertainty (residual SE) and leverage/extrapolation

# Calculate training data statistics for leverage
X_train_mean = X_train_scaled.mean(axis=0)
X_train_cov = np.cov(X_train_scaled.T)

# Use pseudoinverse for numerical stability
try:
    X_train_cov_inv = np.linalg.inv(X_train_cov)
except np.linalg.LinAlgError:
    X_train_cov_inv = np.linalg.pinv(X_train_cov)

# Leverage from training data (average)
X_with_const = np.column_stack([np.ones(n_samples), X_train_scaled])
try:
    xtx_inv = np.linalg.pinv(X_with_const.T @ X_with_const)
    avg_leverage = np.trace(xtx_inv @ X_with_const.T @ X_with_const) / n_samples
except:
    avg_leverage = (n_features + 1) / n_samples

prediction_ses = []
mahal_distances = []

for i in range(len(X_scenario_scaled)):
    x_scenario = X_scenario_scaled[i]
    
    # Distance from training center (Mahalanobis distance)
    dx = x_scenario - X_train_mean
    try:
        mahal_sq = dx @ X_train_cov_inv @ dx
    except:
        # Fallback to Euclidean if covariance singular
        mahal_sq = np.sum(dx ** 2)
    
    mahal_distances.append(np.sqrt(mahal_sq))
    
    # Prediction SE combining residual uncertainty and extrapolation
    # For Ridge: SE(pred) ≈ SE * sqrt(1 + 1/n + normalized_mahal_distance)
    pred_se = residual_se * np.sqrt(1 + 1/n_samples + mahal_sq / n_features)
    prediction_ses.append(pred_se)

prediction_ses = np.array(prediction_ses)
mahal_distances = np.array(mahal_distances)

# 95% prediction intervals using t-distribution
t_crit = stats.t.ppf(0.975, df_resid)

y_lower = y_pred_scenario - t_crit * prediction_ses
y_upper = y_pred_scenario + t_crit * prediction_ses

# Clip to reasonable bounds [0, 0.12] for default rates
y_lower = np.maximum(y_lower, 0)
y_upper = np.minimum(y_upper, 0.12)

# ============================================================================
# Create and save predictions
# ============================================================================

predictions = pd.DataFrame({
    'quarter': quarters_scenario,
    'y_pred': y_pred_scenario,
    'y_lower': y_lower,
    'y_upper': y_upper
})

# Save to CSV
predictions.to_csv('predictions.csv', index=False)

# ============================================================================
# Display results
# ============================================================================

print(f"\\n{'='*70}")
print(f"SCENARIO PREDICTIONS (95% Prediction Intervals)")
print(f"{'='*70}")
print(predictions.to_string(index=False))

print(f"\\n{'='*70}")
print(f"DIAGNOSTICS")
print(f"{'='*70}")
print(f"Mean prediction: {y_pred_scenario.mean():.4f}")
print(f"Min prediction: {y_pred_scenario.min():.4f}")
print(f"Max prediction: {y_pred_scenario.max():.4f}")
print(f"Mean interval width: {(y_upper - y_lower).mean():.4f}")
print(f"Mean Mahalanobis distance: {mahal_distances.mean():.4f}")
print(f"Max Mahalanobis distance: {mahal_distances.max():.4f}")

print(f"\\nFile saved to predictions.csv")
print(f"Number of predictions: {len(predictions)}")
print(f"Expected: {len(scenario_df)}")

# Check for invalid values
print(f"\\nData Quality:")
print(predictions.isnull().sum())
print(f"All values finite: {np.all(np.isfinite(predictions.values))}")
'''

with open('build_model.py', 'w') as f:
    f.write(script_content)

print("Refined model script created")

```

## [23] tool

Refined model script created


## [24] assistant

**tool call: bash**

```

```

## [25] tool

Training features shape: (80, 13)
Scenario features shape: (9, 13)
Feature columns: ['unemployment', 'bbb_spread', 'vix', 'log_gdp', 'sp500', 'djia', 'hpi', 'd_unemployment', 'd_vix', 'd_sp500', 'unemployment_x_spread', 'sp500_x_vix', 'unemployment_sq']

Cross-validation Results:
Best alpha: 100.0000
Best CV MSE: 0.000203

Training Performance:
RMSE: 0.012697
R-squared: 0.3965
Mean residual: 0.00000000

Residual SE: 0.013979

======================================================================
SCENARIO PREDICTIONS (95% Prediction Intervals)
======================================================================
 quarter   y_pred  y_lower  y_upper
      81 0.025020      0.0 0.092408
      82 0.026342      0.0 0.120000
      83 0.026810      0.0 0.120000
      84 0.027216      0.0 0.120000
      85 0.028470      0.0 0.120000
      86 0.029228      0.0 0.120000
      87 0.030783      0.0 0.120000
      88 0.031849      0.0 0.120000
      89 0.032913      0.0 0.120000

======================================================================
DIAGNOSTICS
======================================================================
Mean prediction: 0.0287
Min prediction: 0.0250
Max prediction: 0.0329
Mean interval width: 0.1169
Mean Mahalanobis distance: 22.7691
Max Mahalanobis distance: 38.9424

File saved to predictions.csv
Number of predictions: 9
Expected: 9

Data Quality:
quarter    0
y_pred     0
y_lower    0
y_upper    0
dtype: int64
All values finite: True


## [26] assistant

I see the scenario points are heavily extrapolated (high Mahalanobis distances). The upper bounds are hitting the ceiling because the scenario pushes beyond training data. Let me use a more robust quantile-based approach for prediction intervals that handles extrapolation better:

**tool call: python**

```

# Final refined model with better handling of extrapolation and quantile-based intervals
script_content = '''
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Load data
# ============================================================================
train_df = pd.read_csv('data/train.csv').copy()
scenario_df = pd.read_csv('data/scenario.csv').copy()

y_train = train_df['default_rate'].values
quarters_scenario = scenario_df['quarter'].values

# ============================================================================
# Feature engineering - focus on key credit cycle drivers
# ============================================================================

def prepare_features(df):
    """Prepare features with focus on macroeconomic drivers"""
    X = df[['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']].copy()
    
    # Handle missing values
    X = X.ffill().bfill()
    for col in X.columns:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].mean())
    
    features = {}
    
    # Key credit cycle drivers
    features['unemployment'] = X['unemployment'].values
    features['bbb_spread'] = X['bbb_spread'].values
    features['vix'] = X['vix'].values
    features['gdp'] = X['gdp'].values
    features['hpi'] = X['hpi'].values
    
    # Equity market stress
    features['sp500'] = X['sp500'].values
    features['djia'] = X['djia'].values
    features['nasdaq'] = X['nasdaq'].values
    
    # Price level
    features['cpi'] = X['cpi'].values
    
    # First differences capture momentum
    features['d_unemployment'] = np.concatenate([[0], np.diff(X['unemployment'].values)])
    features['d_bbb_spread'] = np.concatenate([[0], np.diff(X['bbb_spread'].values)])
    features['d_vix'] = np.concatenate([[0], np.diff(X['vix'].values)])
    features['d_sp500'] = np.concatenate([[0], np.diff(X['sp500'].values)])
    
    # Interaction: unemployment stress with market stress
    features['unemp_vix_interaction'] = X['unemployment'].values * X['vix'].values / 50
    
    # Nonlinear unemployment (defaults convex in unemployment)
    features['unemployment_squared'] = X['unemployment'].values ** 2 / 50
    
    return pd.DataFrame(features)

# Prepare features
X_train = prepare_features(train_df)
X_scenario = prepare_features(scenario_df)

# Clean up any inf/nan
X_train = X_train.replace([np.inf, -np.inf], np.nan).fillna(0)
X_scenario = X_scenario.replace([np.inf, -np.inf], np.nan).fillna(0)

print(f"Training features shape: {X_train.shape}")
print(f"Number of features: {X_train.shape[1]}")

# ============================================================================
# Standardize features
# ============================================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_scenario_scaled = scaler.transform(X_scenario)

# ============================================================================
# Build ensemble model for robustness
# ============================================================================

# Use Ridge with cross-validation for alpha selection
alphas = np.logspace(-2, 2, 15)
kfold = KFold(n_splits=5, shuffle=True, random_state=42)

cv_scores = []
for alpha in alphas:
    model_cv = Ridge(alpha=alpha)
    scores = -cross_val_score(model_cv, X_train_scaled, y_train, 
                              cv=kfold, scoring='neg_mean_squared_error')
    cv_scores.append(scores.mean())

best_alpha = alphas[np.argmin(cv_scores)]
print(f"Optimal alpha: {best_alpha:.4f}")

# Fit main model
model = Ridge(alpha=best_alpha)
model.fit(X_train_scaled, y_train)

# Get in-sample predictions for calibration
y_pred_train = model.predict(X_train_scaled)
residuals = y_train - y_pred_train

# Get scenario predictions
y_pred_scenario = model.predict(X_scenario_scaled)

# ============================================================================
# Calculate prediction intervals using residual bootstrap approach
# ============================================================================

n_samples = len(y_train)
n_features = X_train_scaled.shape[1]

# Residual statistics
residual_mean = residuals.mean()
residual_std = residuals.std(ddof=1)

# Calculate leverage for each training point
X_with_const = np.column_stack([np.ones(n_samples), X_train_scaled])
try:
    xtx = X_with_const.T @ X_with_const
    xtx_inv = np.linalg.pinv(xtx)
    leverage = np.array([X_with_const[i] @ xtx_inv @ X_with_const[i] for i in range(n_samples)])
except:
    leverage = np.ones(n_samples) * (n_features + 1) / n_samples

avg_leverage = leverage.mean()

# Calculate MSE for prediction interval
mse = np.sum(residuals ** 2) / max(1, n_samples - n_features - 1)
se_residual = np.sqrt(mse)

# For each scenario prediction, estimate prediction interval width
# considering both residual uncertainty and extrapolation distance

X_train_mean = X_train_scaled.mean(axis=0)
X_train_std = X_train_scaled.std(axis=0)

prediction_intervals = []
for i in range(len(X_scenario_scaled)):
    x = X_scenario_scaled[i]
    
    # Normalized distance from training center
    normalized_dist = np.sum(((x - X_train_mean) / (X_train_std + 1e-8)) ** 2) / n_features
    
    # Prediction SE accounting for extrapolation
    # Standard error increases with distance from training data
    pred_se = se_residual * np.sqrt(1 + avg_leverage + 0.5 * normalized_dist)
    
    # 95% CI using t-distribution
    df = max(1, n_samples - n_features - 1)
    t_crit = stats.t.ppf(0.975, df)
    
    lower = y_pred_scenario[i] - t_crit * pred_se
    upper = y_pred_scenario[i] + t_crit * pred_se
    
    # Add additional uncertainty for severe extrapolation
    if normalized_dist > 2:
        # Add residual quantile uncertainty for extrapolation
        residual_lower_q = np.percentile(residuals, 5)
        residual_upper_q = np.percentile(residuals, 95)
        
        # Blend model-based intervals with empirical residual quantiles
        lower = 0.7 * lower + 0.3 * (y_pred_scenario[i] + residual_lower_q)
        upper = 0.7 * upper + 0.3 * (y_pred_scenario[i] + residual_upper_q)
    
    # Bound to realistic range
    lower = np.maximum(lower, 0)
    upper = np.minimum(upper, 0.12)
    
    prediction_intervals.append((lower, upper))

y_lower, y_upper = zip(*prediction_intervals)
y_lower = np.array(y_lower)
y_upper = np.array(y_upper)

# ============================================================================
# Save predictions
# ============================================================================

predictions = pd.DataFrame({
    'quarter': quarters_scenario,
    'y_pred': y_pred_scenario,
    'y_lower': y_lower,
    'y_upper': y_upper
})

predictions.to_csv('predictions.csv', index=False)

# ============================================================================
# Output results
# ============================================================================

print(f"\\n{'='*70}")
print(f"PREDICTIONS WITH 95% CONFIDENCE INTERVALS")
print(f"{'='*70}")
print(predictions.to_string(index=False))

print(f"\\n{'='*70}")
print(f"Model Performance and Diagnostics")
print(f"{'='*70}")
print(f"Training RMSE: {np.sqrt(mse):.6f}")
print(f"Residual Std: {residual_std:.6f}")
print(f"Residual Min: {residuals.min():.6f}")
print(f"Residual Max: {residuals.max():.6f}")
print(f"Average prediction: {y_pred_scenario.mean():.6f}")
print(f"Min prediction: {y_pred_scenario.min():.6f}")
print(f"Max prediction: {y_pred_scenario.max():.6f}")
print(f"Average interval width: {(y_upper - y_lower).mean():.6f}")

print(f"\\nFile saved to predictions.csv")
print(f"Predictions: {len(predictions)} rows (expected {len(scenario_df)})")
print(f"Data valid: {predictions.isnull().sum().sum() == 0}")
'''

with open('build_model.py', 'w') as f:
    f.write(script_content)

print("Model script updated")

```

## [27] tool

Model script updated


## [28] assistant

**tool call: bash**

```

```

## [29] tool

Training features shape: (80, 15)
Number of features: 15
Optimal alpha: 100.0000

======================================================================
PREDICTIONS WITH 95% CONFIDENCE INTERVALS
======================================================================
 quarter   y_pred  y_lower  y_upper
      81 0.026005      0.0 0.063623
      82 0.027506      0.0 0.065076
      83 0.028267      0.0 0.065562
      84 0.028897      0.0 0.066282
      85 0.030488      0.0 0.067891
      86 0.031516      0.0 0.069538
      87 0.033500      0.0 0.072080
      88 0.034979      0.0 0.074632
      89 0.036470      0.0 0.077602

======================================================================
Model Performance and Diagnostics
======================================================================
Training RMSE: 0.014409
Residual Std: 0.012969
Residual Min: -0.032109
Residual Max: 0.051782
Average prediction: 0.030848
Min prediction: 0.026005
Max prediction: 0.036470
Average interval width: 0.069143

File saved to predictions.csv
Predictions: 9 rows (expected 9)
Data valid: True


## [30] assistant

Excellent! Now let me verify the predictions file format and content:

**tool call: bash**

```

```

## [31] tool

quarter,y_pred,y_lower,y_upper
81,0.026005365824799523,0.0,0.06362310997834672
82,0.027506274702923703,0.0,0.06507593072671206
83,0.028267297279947715,0.0,0.0655619416040721
84,0.02889669711376142,0.0,0.06628207082484877
85,0.03048817201315613,0.0,0.06789135858764027
86,0.03151647023269929,0.0,0.06953773502669933
87,0.03349999317554154,0.0,0.07207957991265705
88,0.03497872911549833,0.0,0.0746315664293729
89,0.036470156526758876,0.0,0.07760170048084183


## [32] assistant

Perfect! The file is valid. Now let me do a few final checks and create a summary to ensure everything is correct:

**tool call: python**

```

import pandas as pd
import numpy as np

# Load and verify predictions
pred_df = pd.read_csv('predictions.csv')
scenario_df = pd.read_csv('data/scenario.csv')

print("="*70)
print("FINAL VERIFICATION")
print("="*70)

print(f"\nFile: predictions.csv")
print(f"Shape: {pred_df.shape}")
print(f"Columns: {list(pred_df.columns)}")
print(f"Expected columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']")
print(f"Columns match: {list(pred_df.columns) == ['quarter', 'y_pred', 'y_lower', 'y_upper']}")

print(f"\n{'='*70}")
print("Data Validation:")
print(f"{'='*70}")
print(f"Number of rows: {len(pred_df)}")
print(f"Rows match scenario: {len(pred_df) == len(scenario_df)}")
print(f"No null values: {pred_df.isnull().sum().sum() == 0}")
print(f"All finite values: {np.all(np.isfinite(pred_df.values))}")
print(f"Quarters match: {np.all(pred_df['quarter'].values == scenario_df['quarter'].values)}")

print(f"\n{'='*70}")
print("Predictions Statistics:")
print(f"{'='*70}")
print(f"y_pred - Mean: {pred_df['y_pred'].mean():.6f}")
print(f"y_pred - Std:  {pred_df['y_pred'].std():.6f}")
print(f"y_pred - Min:  {pred_df['y_pred'].min():.6f}")
print(f"y_pred - Max:  {pred_df['y_pred'].max():.6f}")

print(f"\ny_lower - Mean: {pred_df['y_lower'].mean():.6f}")
print(f"y_lower - Min:  {pred_df['y_lower'].min():.6f}")
print(f"y_lower - Max:  {pred_df['y_lower'].max():.6f}")

print(f"\ny_upper - Mean: {pred_df['y_upper'].mean():.6f}")
print(f"y_upper - Min:  {pred_df['y_upper'].min():.6f}")
print(f"y_upper - Max:  {pred_df['y_upper'].max():.6f}")

print(f"\nInterval Width - Mean: {(pred_df['y_upper'] - pred_df['y_lower']).mean():.6f}")
print(f"Interval Width - Min:  {(pred_df['y_upper'] - pred_df['y_lower']).min():.6f}")
print(f"Interval Width - Max:  {(pred_df['y_upper'] - pred_df['y_lower']).max():.6f}")

print(f"\nConsistency checks:")
print(f"y_lower <= y_pred: {np.all(pred_df['y_lower'] <= pred_df['y_pred'])}")
print(f"y_pred <= y_upper: {np.all(pred_df['y_pred'] <= pred_df['y_upper'])}")

print(f"\n{'='*70}")
print("Detailed Predictions:")
print(f"{'='*70}")
print(pred_df.to_string(index=False))

print(f"\n{'='*70}")
print("✓ All validations passed!")
print(f"{'='*70}")

```

## [33] tool

======================================================================
FINAL VERIFICATION
======================================================================

File: predictions.csv
Shape: (9, 4)
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']
Expected columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']
Columns match: True

======================================================================
Data Validation:
======================================================================
Number of rows: 9
Rows match scenario: True
No null values: True
All finite values: True
Quarters match: True

======================================================================
Predictions Statistics:
======================================================================
y_pred - Mean: 0.030848
y_pred - Std:  0.003560
y_pred - Min:  0.026005
y_pred - Max:  0.036470

y_lower - Mean: 0.000000
y_lower - Min:  0.000000
y_lower - Max:  0.000000

y_upper - Mean: 0.069143
y_upper - Min:  0.063623
y_upper - Max:  0.077602

Interval Width - Mean: 0.069143
Interval Width - Min:  0.063623
Interval Width - Max:  0.077602

Consistency checks:
y_lower <= y_pred: True
y_pred <= y_upper: True

======================================================================
Detailed Predictions:
======================================================================
 quarter   y_pred  y_lower  y_upper
      81 0.026005      0.0 0.063623
      82 0.027506      0.0 0.065076
      83 0.028267      0.0 0.065562
      84 0.028897      0.0 0.066282
      85 0.030488      0.0 0.067891
      86 0.031516      0.0 0.069538
      87 0.033500      0.0 0.072080
      88 0.034979      0.0 0.074632
      89 0.036470      0.0 0.077602

======================================================================
✓ All validations passed!
======================================================================


## [34] assistant

Perfect! I notice the lower bounds are all zero. This is expected behavior - the model is showing asymmetric confidence intervals because the scenario is pushing into unexplored territory with high extrapolation. Let me refine once more to get better lower bounds that reflect genuine uncertainty without being artificially constrained:

**tool call: python**

```

# Final refinement to get better lower bounds while keeping predictions realistic
script_content = '''
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score, KFold
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Load data
# ============================================================================
train_df = pd.read_csv('data/train.csv').copy()
scenario_df = pd.read_csv('data/scenario.csv').copy()

y_train = train_df['default_rate'].values
quarters_scenario = scenario_df['quarter'].values

# ============================================================================
# Feature engineering - streamlined to most important drivers
# ============================================================================

def prepare_features(df):
    """Prepare key credit cycle and macro features"""
    X = df[['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']].copy()
    
    # Handle missing values
    X = X.ffill().bfill()
    for col in X.columns:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].mean())
    
    features = {}
    
    # Level variables (most important)
    features['unemployment'] = X['unemployment'].values
    features['bbb_spread'] = X['bbb_spread'].values
    features['vix'] = X['vix'].values
    features['gdp'] = X['gdp'].values
    features['hpi'] = X['hpi'].values
    
    # Equity markets
    features['sp500'] = X['sp500'].values
    features['djia'] = X['djia'].values
    features['nasdaq'] = X['nasdaq'].values
    features['cpi'] = X['cpi'].values
    
    # First differences (momentum)
    features['d_unemployment'] = np.concatenate([[0], np.diff(X['unemployment'].values)])
    features['d_bbb_spread'] = np.concatenate([[0], np.diff(X['bbb_spread'].values)])
    features['d_vix'] = np.concatenate([[0], np.diff(X['vix'].values)])
    
    # Stress interaction
    features['stress_index'] = (X['unemployment'].values * X['vix'].values) / 100
    
    # Nonlinearity in unemployment
    features['unemployment_sq'] = X['unemployment'].values ** 2 / 100
    
    return pd.DataFrame(features)

# Prepare features
X_train = prepare_features(train_df)
X_scenario = prepare_features(scenario_df)

# Clean
X_train = X_train.replace([np.inf, -np.inf], np.nan).fillna(0)
X_scenario = X_scenario.replace([np.inf, -np.inf], np.nan).fillna(0)

print(f"Features: {X_train.shape[1]}, Training samples: {len(X_train)}")

# ============================================================================
# Standardize
# ============================================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_scenario_scaled = scaler.transform(X_scenario)

# ============================================================================
# Model: Ridge regression with CV
# ============================================================================

alphas = np.logspace(-1, 2, 12)
kfold = KFold(n_splits=5, shuffle=True, random_state=42)

cv_scores = []
for alpha in alphas:
    model_cv = Ridge(alpha=alpha)
    scores = -cross_val_score(model_cv, X_train_scaled, y_train, 
                              cv=kfold, scoring='neg_mean_squared_error')
    cv_scores.append(scores.mean())

best_alpha = alphas[np.argmin(cv_scores)]

# Fit model
model = Ridge(alpha=best_alpha)
model.fit(X_train_scaled, y_train)

# Predictions
y_pred_train = model.predict(X_train_scaled)
y_pred_scenario = model.predict(X_scenario_scaled)
residuals = y_train - y_pred_train

# ============================================================================
# Residual-based prediction intervals
# ============================================================================

n_samples = len(y_train)
n_features = X_train_scaled.shape[1]
df_resid = max(1, n_samples - n_features - 1)

# Compute residual metrics
mse = np.sum(residuals ** 2) / df_resid
rmse = np.sqrt(mse)

# Residual quantiles for asymmetric bounds
residual_lower_q = np.percentile(residuals, 2.5)  # 2.5th percentile
residual_upper_q = np.percentile(residuals, 97.5)  # 97.5th percentile

# Leverage calculations
X_with_const = np.column_stack([np.ones(n_samples), X_train_scaled])
try:
    xtx = X_with_const.T @ X_with_const
    xtx_inv = np.linalg.pinv(xtx)
    leverage_diag = np.array([X_with_const[i] @ xtx_inv @ X_with_const[i] for i in range(n_samples)])
    avg_leverage = leverage_diag.mean()
except:
    avg_leverage = (n_features + 1) / n_samples

# Distance metrics for extrapolation
X_train_mean = X_train_scaled.mean(axis=0)
X_train_cov = np.cov(X_train_scaled.T)
X_train_cov_inv = np.linalg.pinv(X_train_cov)

# ============================================================================
# Generate prediction intervals
# ============================================================================

y_lower_list = []
y_upper_list = []

for i in range(len(X_scenario_scaled)):
    x = X_scenario_scaled[i]
    pred = y_pred_scenario[i]
    
    # Mahalanobis distance
    dx = x - X_train_mean
    mahal_sq = dx @ X_train_cov_inv @ dx
    mahal_dist = np.sqrt(mahal_sq)
    
    # Standard error of prediction
    se_pred = rmse * np.sqrt(1 + avg_leverage + 0.1 * mahal_sq)
    
    # For severe extrapolation, use empirical residual quantiles with higher weight
    if mahal_dist > 1.5:
        # More extreme extrapolation: blend empirical with model-based
        weight_empirical = min(0.6, 0.3 + 0.1 * (mahal_dist - 1.5))
    else:
        weight_empirical = 0.3
    
    # Asymmetric intervals incorporating residual quantiles
    lower = (1 - weight_empirical) * (pred - 1.96 * se_pred) + weight_empirical * (pred + residual_lower_q)
    upper = (1 - weight_empirical) * (pred + 1.96 * se_pred) + weight_empirical * (pred + residual_upper_q)
    
    # Bounds
    lower = np.maximum(lower, 0.005)  # Don't go to zero
    upper = np.minimum(upper, 0.11)
    
    y_lower_list.append(lower)
    y_upper_list.append(upper)

y_lower = np.array(y_lower_list)
y_upper = np.array(y_upper_list)

# ============================================================================
# Save
# ============================================================================

predictions = pd.DataFrame({
    'quarter': quarters_scenario,
    'y_pred': y_pred_scenario,
    'y_lower': y_lower,
    'y_upper': y_upper
})

predictions.to_csv('predictions.csv', index=False)

# ============================================================================
# Output
# ============================================================================

print(f"\\n{'='*70}")
print(f"STRESS SCENARIO PREDICTIONS - 95% CONFIDENCE INTERVALS")
print(f"{'='*70}")
print(predictions.to_string(index=False))

print(f"\\nModel: Ridge regression (alpha={best_alpha:.1f})")
print(f"Training RMSE: {rmse:.6f}")
print(f"Mean prediction: {y_pred_scenario.mean():.6f}")
print(f"Average interval width: {(y_upper - y_lower).mean():.6f}")
print(f"\\nSaved to: predictions.csv")
print(f"Rows: {len(predictions)} (expected {len(scenario_df)})")
print(f"Valid: {predictions.isnull().sum().sum() == 0 and np.all(np.isfinite(predictions.values))}")
'''

with open('build_model.py', 'w') as f:
    f.write(script_content)

print("Final model script created")

```

## [35] tool

Final model script created


## [36] assistant

**tool call: bash**

```

```

## [37] tool

Features: 14, Training samples: 80

======================================================================
STRESS SCENARIO PREDICTIONS - 95% CONFIDENCE INTERVALS
======================================================================
 quarter   y_pred  y_lower  y_upper
      81 0.026843    0.005 0.070257
      82 0.027582    0.005 0.084516
      83 0.028705    0.005 0.091763
      84 0.029882    0.005 0.094160
      85 0.031124    0.005 0.098587
      86 0.032454    0.005 0.095610
      87 0.033859    0.005 0.099680
      88 0.035358    0.005 0.103323
      89 0.036985    0.005 0.101403

Model: Ridge regression (alpha=100.0)
Training RMSE: 0.014334
Mean prediction: 0.031421
Average interval width: 0.088256

Saved to: predictions.csv
Rows: 9 (expected 9)
Valid: True


## [38] assistant

Great! Now I have more reasonable lower bounds. Let me verify the final CSV one more time:

**tool call: bash**

```

```

## [39] tool

quarter,y_pred,y_lower,y_upper
81,0.02684316449279954,0.005,0.07025749407325987
82,0.027582267900379737,0.005,0.084515608019189
83,0.028705316544783015,0.005,0.09176344258367113
84,0.029882137902878143,0.005,0.09415987454552706
85,0.03112384035526636,0.005,0.09858655951695608
86,0.03245420359180537,0.005,0.0956101536776493
87,0.03385876219127381,0.005,0.09968032981684534
88,0.03535803720268691,0.005,0.10332319967723916
89,0.03698465231570748,0.005,0.10140313701308273


## [40] assistant

Excellent! Let me do a final comprehensive validation:

**tool call: python**

```

import pandas as pd
import numpy as np

# Final comprehensive check
pred_df = pd.read_csv('predictions.csv')
scenario_df = pd.read_csv('data/scenario.csv')
train_df = pd.read_csv('data/train.csv')

print("="*70)
print("FINAL SUBMISSION VALIDATION")
print("="*70)

# File format
print("\n1. FILE FORMAT CHECK:")
print(f"   ✓ Filename: predictions.csv")
print(f"   ✓ Columns: {list(pred_df.columns)}")
print(f"   ✓ Column order correct: {list(pred_df.columns) == ['quarter', 'y_pred', 'y_lower', 'y_upper']}")

# Data integrity
print("\n2. DATA INTEGRITY:")
print(f"   ✓ Rows: {len(pred_df)} (expected {len(scenario_df)})")
print(f"   ✓ No missing values: {pred_df.isnull().sum().sum() == 0}")
print(f"   ✓ All finite values: {np.all(np.isfinite(pred_df.values))}")
print(f"   ✓ Quarters match scenario: {np.array_equal(pred_df['quarter'].values, scenario_df['quarter'].values)}")

# Logical constraints
print("\n3. LOGICAL CONSTRAINTS:")
print(f"   ✓ y_lower ≤ y_pred: {np.all(pred_df['y_lower'] <= pred_df['y_pred'])}")
print(f"   ✓ y_pred ≤ y_upper: {np.all(pred_df['y_pred'] <= pred_df['y_upper'])}")
print(f"   ✓ y_lower ≥ 0: {np.all(pred_df['y_lower'] >= 0)}")
print(f"   ✓ y_upper ≤ 0.15: {np.all(pred_df['y_upper'] <= 0.15)}")

# Reasonableness checks
print("\n4. REASONABLENESS CHECKS:")
train_mean = train_df['default_rate'].mean()
train_std = train_df['default_rate'].std()
train_max = train_df['default_rate'].max()

print(f"   Training default rate statistics:")
print(f"   - Mean: {train_mean:.6f}")
print(f"   - Std:  {train_std:.6f}")
print(f"   - Max:  {train_max:.6f}")
print(f"\\n   Scenario predictions statistics:")
print(f"   - Mean: {pred_df['y_pred'].mean():.6f}")
print(f"   - Std:  {pred_df['y_pred'].std():.6f}")
print(f"   - Max:  {pred_df['y_pred'].max():.6f}")
print(f"   - Range: [{pred_df['y_pred'].min():.6f}, {pred_df['y_pred'].max():.6f}]")

print(f"\\n   Interval characteristics:")
print(f"   - Mean width: {(pred_df['y_upper'] - pred_df['y_lower']).mean():.6f}")
print(f"   - Min width:  {(pred_df['y_upper'] - pred_df['y_lower']).min():.6f}")
print(f"   - Max width:  {(pred_df['y_upper'] - pred_df['y_lower']).max():.6f}")

print("\n5. SCENARIO ANALYSIS:")
print(f"   Scenario quarters: {pred_df['quarter'].min()} to {pred_df['quarter'].max()}")
print(f"   Stress scenario: Increasing unemployment and VIX")
print(f"   Default rate trend: {'↑ increasing' if pred_df['y_pred'].iloc[-1] > pred_df['y_pred'].iloc[0] else '↓ decreasing'}")

# Show results
print("\n" + "="*70)
print("PREDICTIONS TABLE")
print("="*70)
for idx, row in pred_df.iterrows():
    print(f"Q{int(row['quarter']):02d}: pred={row['y_pred']:.6f}  "
          f"[{row['y_lower']:.6f}, {row['y_upper']:.6f}]  "
          f"width={row['y_upper']-row['y_lower']:.6f}")

print("\n" + "="*70)
print("✓ ALL VALIDATION CHECKS PASSED - READY FOR SUBMISSION")
print("="*70)

```

## [41] tool

======================================================================
FINAL SUBMISSION VALIDATION
======================================================================

1. FILE FORMAT CHECK:
   ✓ Filename: predictions.csv
   ✓ Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']
   ✓ Column order correct: True

2. DATA INTEGRITY:
   ✓ Rows: 9 (expected 9)
   ✓ No missing values: True
   ✓ All finite values: True
   ✓ Quarters match scenario: True

3. LOGICAL CONSTRAINTS:
   ✓ y_lower ≤ y_pred: True
   ✓ y_pred ≤ y_upper: True
   ✓ y_lower ≥ 0: True
   ✓ y_upper ≤ 0.15: True

4. REASONABLENESS CHECKS:
   Training default rate statistics:
   - Mean: 0.032681
   - Std:  0.016447
   - Max:  0.104713
\n   Scenario predictions statistics:
   - Mean: 0.031421
   - Std:  0.003518
   - Max:  0.036985
   - Range: [0.026843, 0.036985]
\n   Interval characteristics:
   - Mean width: 0.088256
   - Min width:  0.065257
   - Max width:  0.098323

5. SCENARIO ANALYSIS:
   Scenario quarters: 81 to 89
   Stress scenario: Increasing unemployment and VIX
   Default rate trend: ↑ increasing

======================================================================
PREDICTIONS TABLE
======================================================================
Q81: pred=0.026843  [0.005000, 0.070257]  width=0.065257
Q82: pred=0.027582  [0.005000, 0.084516]  width=0.079516
Q83: pred=0.028705  [0.005000, 0.091763]  width=0.086763
Q84: pred=0.029882  [0.005000, 0.094160]  width=0.089160
Q85: pred=0.031124  [0.005000, 0.098587]  width=0.093587
Q86: pred=0.032454  [0.005000, 0.095610]  width=0.090610
Q87: pred=0.033859  [0.005000, 0.099680]  width=0.094680
Q88: pred=0.035358  [0.005000, 0.103323]  width=0.098323
Q89: pred=0.036985  [0.005000, 0.101403]  width=0.096403

======================================================================
✓ ALL VALIDATION CHECKS PASSED - READY FOR SUBMISSION
======================================================================


## [42] assistant

Perfect! The model and predictions look good. Let me create one final documentation of the approach:

**tool call: python**

```

# Create a summary document
summary = """
STRESS LOSS MODEL - DOCUMENTATION
==================================

PROJECT GOAL:
Build a model of portfolio default rate from 80 quarters of historical 
macroeconomic data, then predict default rates for 9 quarters under a 
forward stress scenario with 95% prediction intervals.

MODEL APPROACH:
==============

1. FEATURE ENGINEERING:
   - Input: 9 macroeconomic variables (GDP, unemployment, HPI, BBB spread, 
     S&P500, DJIA, NASDAQ, VIX, CPI)
   - Handled missing values via forward fill, backward fill, then mean imputation
   - Created 14 features including:
     * Level variables (unemployment, spreads, VIX, equity indices)
     * First differences (momentum in unemployment, spreads, VIX)
     * Nonlinear terms (unemployment squared)
     * Interaction terms (stress index = unemployment × VIX)

2. MODEL SELECTION:
   - Ridge regression with cross-validation for hyperparameter tuning
   - 5-fold CV tested alphas from 0.1 to 100
   - Selected alpha=100 (strong regularization for out-of-sample stability)
   - Rationale: Portfolio default rates show moderate correlation with macro 
     variables; regularized regression prevents overfitting on limited data

3. PREDICTION INTERVALS:
   - Residual-based approach accounting for:
     a) Model uncertainty (residual MSE)
     b) Leverage effects (average training influence)
     c) Extrapolation distance (Mahalanobis distance from training center)
   - Asymmetric bounds using blended approach:
     * For low extrapolation: model-based t-intervals
     * For high extrapolation: weight empirical residual quantiles more heavily
   - 95% confidence level with asymmetric bands reflecting different tail risks

4. KEY FINDINGS:
   - Unemployment is the strongest driver of default rates (correlation: 0.651)
   - BBB spreads also significant (correlation: 0.460)
   - Scenario shows 2.6% baseline (Q81) rising to 3.7% (Q89)
   - Wide intervals (6.5% - 9.8% width) reflect genuine uncertainty in 
     extrapolation region

5. DATA QUALITY:
   - Training: 80 quarterly observations, complete target variable
   - Scenario: 9 quarters, all macro variables available
   - No missing values in final predictions
   - All predictions in [0.005, 0.110] range (realistic for portfolio defaults)

VALIDATION SUMMARY:
===================
✓ 9 predictions generated (one per scenario quarter)
✓ Correct CSV format with columns: quarter, y_pred, y_lower, y_upper
✓ All logical constraints satisfied:
  - y_lower ≤ y_pred ≤ y_upper for all rows
  - Predictions monotonic with stress scenario
  - Intervals capture asymmetric uncertainty (wider upper tails)
✓ Predictions reasonable relative to training data:
  - Scenario predictions in range [2.7%, 3.7%]
  - Training average: 3.3%, max: 10.5%
  - Stress scenario predictions below training max but show deterioration trend

RECOMMENDATIONS FOR USE:
========================
- These predictions represent a baseline stress scenario
- Model is most reliable for scenarios resembling training distribution
- For extreme scenarios beyond current extrapolation, treat intervals 
  as conservative lower bounds on uncertainty
- Periodic retraining recommended as new data becomes available
"""

print(summary)

# Save to file
with open('MODEL_DOCUMENTATION.txt', 'w') as f:
    f.write(summary)

print("\nDocumentation saved to MODEL_DOCUMENTATION.txt")

```

## [43] tool


STRESS LOSS MODEL - DOCUMENTATION
==================================

PROJECT GOAL:
Build a model of portfolio default rate from 80 quarters of historical 
macroeconomic data, then predict default rates for 9 quarters under a 
forward stress scenario with 95% prediction intervals.

MODEL APPROACH:
==============

1. FEATURE ENGINEERING:
   - Input: 9 macroeconomic variables (GDP, unemployment, HPI, BBB spread, 
     S&P500, DJIA, NASDAQ, VIX, CPI)
   - Handled missing values via forward fill, backward fill, then mean imputation
   - Created 14 features including:
     * Level variables (unemployment, spreads, VIX, equity indices)
     * First differences (momentum in unemployment, spreads, VIX)
     * Nonlinear terms (unemployment squared)
     * Interaction terms (stress index = unemployment × VIX)

2. MODEL SELECTION:
   - Ridge regression with cross-validation for hyperparameter tuning
   - 5-fold CV tested alphas from 0.1 to 100
   - Selected alpha=100 (strong regularization for out-of-sample stability)
   - Rationale: Portfolio default rates show moderate correlation with macro 
     variables; regularized regression prevents overfitting on limited data

3. PREDICTION INTERVALS:
   - Residual-based approach accounting for:
     a) Model uncertainty (residual MSE)
     b) Leverage effects (average training influence)
     c) Extrapolation distance (Mahalanobis distance from training center)
   - Asymmetric bounds using blended approach:
     * For low extrapolation: model-based t-intervals
     * For high extrapolation: weight empirical residual quantiles more heavily
   - 95% confidence level with asymmetric bands reflecting different tail risks

4. KEY FINDINGS:
   - Unemployment is the strongest driver of default rates (correlation: 0.651)
   - BBB spreads also significant (correlation: 0.460)
   - Scenario shows 2.6% baseline (Q81) rising to 3.7% (Q89)
   - Wide intervals (6.5% - 9.8% width) reflect genuine uncertainty in 
     extrapolation region

5. DATA QUALITY:
   - Training: 80 quarterly observations, complete target variable
   - Scenario: 9 quarters, all macro variables available
   - No missing values in final predictions
   - All predictions in [0.005, 0.110] range (realistic for portfolio defaults)

VALIDATION SUMMARY:
===================
✓ 9 predictions generated (one per scenario quarter)
✓ Correct CSV format with columns: quarter, y_pred, y_lower, y_upper
✓ All logical constraints satisfied:
  - y_lower ≤ y_pred ≤ y_upper for all rows
  - Predictions monotonic with stress scenario
  - Intervals capture asymmetric uncertainty (wider upper tails)
✓ Predictions reasonable relative to training data:
  - Scenario predictions in range [2.7%, 3.7%]
  - Training average: 3.3%, max: 10.5%
  - Stress scenario predictions below training max but show deterioration trend

RECOMMENDATIONS FOR USE:
========================
- These predictions represent a baseline stress scenario
- Model is most reliable for scenarios resembling training distribution
- For extreme scenarios beyond current extrapolation, treat intervals 
  as conservative lower bounds on uncertainty
- Periodic retraining recommended as new data becomes available


Documentation saved to MODEL_DOCUMENTATION.txt


## [44] assistant

Perfect! Now let me verify once more that predictions.csv is in the current working directory and ready for submission:

**tool call: bash**

```

```

## [45] tool

-rw-r--r-- 1 root root 472 Jul 28 00:23 predictions.csv
10 predictions.csv
quarter,y_pred,y_lower,y_upper
89,0.03698465231570748,0.005,0.10140313701308273


## [46] assistant

Excellent! Everything is ready. Let me do one final check of the exact format:

**tool call: bash**

```

```

## [47] tool

✓ File: predictions.csv
✓ Shape: (9, 4)
✓ Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']
✓ Data types:
quarter      int64
y_pred     float64
y_lower    float64
y_upper    float64
dtype: object

✓ Summary statistics:
         quarter    y_pred  y_lower   y_upper
count   9.000000  9.000000    9.000  9.000000
mean   85.000000  0.031421    0.005  0.093256
std     2.738613  0.003518    0.000  0.010316
min    81.000000  0.026843    0.005  0.070257
25%    83.000000  0.028705    0.005  0.091763
50%    85.000000  0.031124    0.005  0.095610
75%    87.000000  0.033859    0.005  0.099680
max    89.000000  0.036985    0.005  0.103323

✓ First 3 rows:
   quarter    y_pred  y_lower   y_upper
0       81  0.026843    0.005  0.070257
1       82  0.027582    0.005  0.084516
2       83  0.028705    0.005  0.091763

✓ Last 3 rows:
   quarter    y_pred  y_lower   y_upper
6       87  0.033859    0.005  0.099680
7       88  0.035358    0.005  0.103323
8       89  0.036985    0.005  0.101403

✓ Validation:
  - No NaNs: True
  - All finite: True
  - Lower ≤ Pred: True
  - Pred ≤ Upper: True

✓ READY FOR SUBMISSION


## [48] assistant

Perfect! Now let me submit the predictions:

**tool call: submit**

```
quarter,y_pred,y_lower,y_upper
81,0.02684316449279954,0.005,0.07025749407325987
82,0.027582267900379737,0.005,0.084515608019189
83,0.028705316544783015,0.005,0.09176344258367113
84,0.029882137902878143,0.005,0.09415987454552706
85,0.03112384035526636,0.005,0.09858655951695608
86,0.03245420359180537,0.005,0.0956101536776493
87,0.03385876219127381,0.005,0.09968032981684534
88,0.03535803720268691,0.005,0.10332319967723916
89,0.03698465231570748,0.005,0.10140313701308273
```

## [49] tool

quarter,y_pred,y_lower,y_upper
81,0.02684316449279954,0.005,0.07025749407325987
82,0.027582267900379737,0.005,0.084515608019189
83,0.028705316544783015,0.005,0.09176344258367113
84,0.029882137902878143,0.005,0.09415987454552706
85,0.03112384035526636,0.005,0.09858655951695608
86,0.03245420359180537,0.005,0.0956101536776493
87,0.03385876219127381,0.005,0.09968032981684534
88,0.03535803720268691,0.005,0.10332319967723916
89,0.03698465231570748,0.005,0.10140313701308273

