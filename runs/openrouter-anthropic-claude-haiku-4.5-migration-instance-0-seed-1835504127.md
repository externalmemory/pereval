# openrouter/anthropic/claude-haiku-4.5 — migration (id=instance-0-seed-1835504127)

- score 0.9016 (1.0 = no migration); 2/16 checks failed: pd_rises_as_rating_falls, multinotch_downgrade_possible; by scenario 1.124/0.814/0.767; completion 100%
- messages 62 | limit None | seed None

---

## [0] system

You are projecting how a loan portfolio's credit ratings will migrate under
three supplied economic scenarios. In the `data/` directory:

- `data/transitions.csv`: observed rating transitions for this portfolio, as
  ANNUAL counts. One row per year and starting rating, with columns `year`,
  `from_rating`, and `to_AAA` through `to_CCC_C` plus `to_D`. A row counts the
  obligors that held `from_rating` at the start of that year and held each state
  at the end of it. An obligor that defaulted during the year is counted in
  `to_D`. Counts are a finite portfolio, so they carry sampling noise.
- `data/macro_history.csv`: QUARTERLY macroeconomic series over the same period,
  nine of them. Some are blank for early quarters because they began later.
- `data/scenario.csv`: the same nine series for nine future quarters, under each
  of three scenarios, named `baseline`, `adverse` and `severe` in the `scenario`
  column. Twenty-seven rows. The three share the same history and differ only in
  the future path. Treat the paths as given, not as something to forecast.
- `data/portfolio.csv`: the cohort to project, as obligor counts by rating. Its
  rating mix is NOT the same as the historical portfolio's.
- `data/policy.json`: the checkpoint quarters and the scenario names.

Quarters are numbered relative to the projection throughout, in every file you
read and every file you write. The last quarter of history is 0, earlier
historical quarters run negative, and the nine scenario quarters are 1 through
9. So the checkpoints are quarters 4 and 9 of the horizon.

Estimate ONE model on the history and use that single model to produce all three
projections. The scenarios differ only in the macro path you feed it, which is
what a supervisory submission is: one estimated model, three paths through it. Do
not re-estimate, retune or adjust the model per scenario, and do not apply a
scenario-specific overlay or add-on.

Project this cohort forward over the nine scenario quarters, under each
scenario, and report where its obligors stand at quarter 4 and at quarter 9.

What to report, precisely. For each scenario and checkpoint, give the
distribution of the ORIGINAL cohort across the seven rating grades plus `D` for
default. Default is absorbing and terminal: once an obligor defaults it stays in
`D` and is counted there at every later checkpoint. Do not replace defaulted
obligors, do not model new lending, and do not renormalise the surviving grades
to one on their own. The eight shares at each scenario and checkpoint describe
where the original obligors ended up, so they must sum to 1.

Write `predictions.csv` in the working directory with columns exactly:

    scenario,quarter,state,share

one row per scenario, checkpoint and state, so forty-eight rows in total.
`scenario` is baseline, adverse or severe, `quarter` is 4 or 9, `state` is one of
AAA, AA, A, BBB, BB, B, CCC/C, D, and `share` is a fraction of the original
cohort between 0 and 1.

Scoring has four equally weighted components per scenario, two per checkpoint,
so twelve in all:

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
migration and no defaults. The twelve ratios are averaged. So 0 is perfect, 1.0
means no better overall than assuming nothing happens, and below 1.0 means
better. Getting the shape right while understating defaults, or the reverse,
caps your score at about 0.5.

Also write `matrices.csv` in the working directory, recording the quarterly
transition matrices your model used for the nine quarters of each scenario,
numbered 1 through 9 as above, with columns exactly:

    scenario,quarter,from_rating,to_AAA,to_AA,to_A,to_BBB,to_BB,to_B,to_CCC_C,to_D

one row per scenario, quarter and starting rating, using the same column naming
as data/transitions.csv.

In the same file, also record the quarterly transition matrix your fitted model
implies for each HISTORICAL YEAR, under the scenario name `history`. Label each
one with the last quarter of its year, so quarters -76, -72, -68 and so on
through 0, twenty in all. There is one history, so write it once rather than
once per scenario. That is twenty years of history and nine quarters of each of
the three scenarios, so three hundred and twenty-nine rows.

Write at least six decimal places: the cells far from the diagonal are small, and three
decimals is not enough to record them. This records the model alongside its
output, as documentation of how the projection was produced.

Also write `backtest.csv` in the working directory, giving, under each
scenario, the annual default rate your model projects for each HISTORICAL year,
with columns exactly:

    scenario,year,default_rate

one row per scenario and year in data/transitions.csv, so sixty rows. For each
year, use the portfolio that year actually started with, taken from the row sums
of that year's counts, and report the fraction of it your model says defaults
during that year. This is the model's fit to the period it was estimated on,
alongside its projection.

Note that the transitions you observe are annual while the projection is
quarterly, and the economy moves within each year as well as between years.

You have Python with numpy, pandas, scikit-learn, statsmodels and scipy. You do
not have internet access. Each code execution runs in a FRESH interpreter, so
write a single self-contained script and run it rather than relying on state
carrying over. Produce a complete predictions.csv early, even from a rough
model, and refine it after. Verify predictions.csv has forty-eight rows before
submitting.


## [1] user

Project the cohort in data/portfolio.csv over each of the three scenarios and write predictions.csv, as specified in the system instructions.

## [2] assistant

I'll start by exploring the data files to understand the structure and then build the model.

**tool call: python**

```

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import json
import warnings
warnings.filterwarnings('ignore')

# Load all data files
transitions = pd.read_csv('data/transitions.csv')
macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')

with open('data/policy.json', 'r') as f:
    policy = json.load(f)

print("Transitions shape:", transitions.shape)
print(transitions.head(10))
print("\nMacro history shape:", macro_history.shape)
print(macro_history.head())
print("\nScenario data shape:", scenario_data.shape)
print(scenario_data.head())
print("\nPortfolio:")
print(portfolio)
print("\nPolicy:")
print(policy)

```

## [3] tool

Transitions shape: (140, 10)
   year from_rating  to_AAA  to_AA  to_A  to_BBB  to_BB  to_B  to_CCC_C  to_D
0     1         AAA      88     11     0       0      0     0         0     0
1     1          AA       1    357    40       2      1     1         1     0
2     1           A       0     11  1875     120      8     1         0     0
3     1         BBB       0      0    55    3730    136    13         4    12
4     1          BB       0      1     1      48   2152   229        14    26
5     1           B       0      0     0       0     22   791        70    39
6     1       CCC/C       0      0     0       0      0    12        56    72
7     2         AAA      82      8     1       0      0     0         0     0
8     2          AA       2    354    28       1      0     0         0     0
9     2           A       0     12  1851     112     14     3         0     0

Macro history shape: (80, 10)
   quarter       gdp  unemployment  hpi  ...  djia    nasdaq  vix       cpi
0      -79  136.7405        4.2750  NaN  ...   NaN  162.1009  NaN  135.1871
1      -78  136.0426        4.6353  NaN  ...   NaN  171.5735  NaN  134.7073
2      -77  136.7923        4.8230  NaN  ...   NaN  168.6532  NaN  134.3463
3      -76  135.8043        6.2531  NaN  ...   NaN  175.5857  NaN  136.1648
4      -75  137.6612        5.5272  NaN  ...   NaN  169.6977  NaN  138.5816

[5 rows x 10 columns]

Scenario data shape: (27, 11)
   scenario  quarter       gdp  ...   nasdaq      vix       cpi
0  baseline        1  184.8771  ...  47.3783  21.0125  211.5660
1  baseline        2  185.5255  ...  46.7328  20.0682  212.2874
2  baseline        3  186.6932  ...  47.5669  19.1664  213.7563
3  baseline        4  187.6458  ...  47.7710  19.5464  214.9147
4  baseline        5  188.3802  ...  47.3368  19.9339  215.7575

[5 rows x 11 columns]

Portfolio:
  rating  obligors
0    AAA        44
1     AA       227
2      A      1450
3    BBB      3662
4     BB      2963
5      B      1363
6  CCC/C       290

Policy:
{'checkpoints': [4, 9], 'horizon_quarters': 9, 'obligors': 9999, 'scenarios': ['baseline', 'adverse', 'severe']}


## [4] assistant

Good! Now let me understand the structure better and start building the model.

**tool call: python**

```

# Get rating grades and default states
ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
to_columns = [f'to_{r}' for r in ratings] + ['to_D']

print("Years in transition data:", transitions['year'].unique())
print("Number of years:", len(transitions['year'].unique()))
print("From ratings:", transitions['from_rating'].unique())

# Check macro variables available
print("\nMacro columns:", macro_history.columns.tolist())
print("Macro availability by column:")
for col in macro_history.columns[1:]:
    non_null = macro_history[col].notna().sum()
    print(f"  {col}: {non_null} non-null values out of {len(macro_history)}")

# Quarters in history (0 is last historical quarter, negative are earlier)
print("\nHistorical quarters:", macro_history['quarter'].min(), "to", macro_history['quarter'].max())

# Scenarios
print("\nScenarios:")
for scenario in scenario_data['scenario'].unique():
    print(f"  {scenario}: quarters", scenario_data[scenario_data['scenario'] == scenario]['quarter'].unique())

```

## [5] tool

Traceback (most recent call last):
  File "<stdin>", line 6, in <module>
NameError: name 'transitions' is not defined



## [6] assistant

The interpreter state was cleared. Let me write a complete self-contained script:

**tool call: python**

```

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# LOAD DATA
# ============================================================================
transitions = pd.read_csv('data/transitions.csv')
macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')

with open('data/policy.json', 'r') as f:
    policy = json.load(f)

ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']

# ============================================================================
# CONVERT ANNUAL TRANSITIONS TO QUARTERLY
# ============================================================================
# The transitions are annual counts. We need to model quarterly transitions.
# Strategy: estimate a model that relates quarterly macro conditions to 
# credit transitions, then predict for each scenario.

# Each year in the transition data covers 4 quarters.
# Map years to their ending quarters: year 1 -> quarter 0, 1, 2, 3 (but we only know end-of-year)
# Actually, the transitions show annual flows, so year Y spans 4 quarters.
# We need to align them with macro history.

# Year 1 should correspond to quarters -3, -2, -1, 0 (Q4 of previous year through Q3 of year 1)
# But we don't know exactly. Let's assume year Y ends at quarter 4*Y (approximately).
# Year 1 -> quarters 1-4, Year 2 -> quarters 5-8, etc.
# But in the data, quarters are relative: 0 is last historical quarter.

# Let me check: macro_history has quarters from -79 to 0 (80 quarters = 20 years)
# Transitions has 140 rows = 7 ratings × 20 years, so 20 years
# Perfect alignment!

years_in_data = sorted(transitions['year'].unique())
num_years = len(years_in_data)
print(f"Years in transition data: {num_years} years")
print(f"Historical quarters available: {macro_history['quarter'].min()} to {macro_history['quarter'].max()}")

# Map each year to its end quarter
year_to_end_quarter = {}
for i, year in enumerate(years_in_data):
    # Year 1 ends at quarter (1-20)*4 - 1 = -76 to 0
    end_quarter = (i - num_years) * 4 + 3  # 0 is the last quarter
    year_to_end_quarter[year] = end_quarter
    
print("\nYear to end quarter mapping:")
print(year_to_end_quarter)

```

## [7] tool

Years in transition data: 20 years
Historical quarters available: -79 to 0

Year to end quarter mapping:
{np.int64(1): -77, np.int64(2): -73, np.int64(3): -69, np.int64(4): -65, np.int64(5): -61, np.int64(6): -57, np.int64(7): -53, np.int64(8): -49, np.int64(9): -45, np.int64(10): -41, np.int64(11): -37, np.int64(12): -33, np.int64(13): -29, np.int64(14): -25, np.int64(15): -21, np.int64(16): -17, np.int64(17): -13, np.int64(18): -9, np.int64(19): -5, np.int64(20): -1}


## [8] assistant

**tool call: python**

```

# Actually, let me recalculate. Quarters are -79, -78, -77, ... -1, 0
# That's 80 quarters. 80/4 = 20 years exactly.
# If quarter 0 is end of year 20, then:
# Year 20 ends at quarter 0
# Year 19 ends at quarter -4
# Year 18 ends at quarter -8
# etc.

year_to_end_quarter = {}
for i, year in enumerate(years_in_data):
    # year goes from 1 to 20
    # Calculate which quarter ends year Y
    end_quarter = 0 - (20 - year) * 4
    year_to_end_quarter[year] = end_quarter

print("Corrected Year to end quarter mapping:")
for year in sorted(years_in_data):
    print(f"Year {year}: quarter {year_to_end_quarter[year]}")

# Now create training data: for each year, get average macro conditions during that year
# Year Y spans 4 quarters ending at quarter end_quarter
training_data = []

for year in sorted(years_in_data):
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3  # 4 quarters (end_q - 3, ..., end_q)
    
    year_trans = transitions[transitions['year'] == year].copy()
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)].copy()
    
    print(f"\nYear {year}: quarters {start_q} to {end_q}")
    print(f"  Macro rows: {len(year_macro)}")
    
    if len(year_macro) > 0:
        # Average macro conditions over the year
        macro_cols = [c for c in year_macro.columns if c != 'quarter']
        macro_avg = year_macro[macro_cols].mean()
        
        for _, trans_row in year_trans.iterrows():
            from_rating = trans_row['from_rating']
            total = trans_row[['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']].sum()
            
            if total > 0:
                training_data.append({
                    'year': year,
                    'from_rating': from_rating,
                    'total': total,
                    **{col: trans_row[col] for col in ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']},
                    **macro_avg.to_dict()
                })

training_df = pd.DataFrame(training_data)
print(f"\nTraining data shape: {training_df.shape}")
print(training_df.head(10))

```

## [9] tool

Traceback (most recent call last):
  File "<stdin>", line 11, in <module>
NameError: name 'years_in_data' is not defined



## [10] assistant

Let me write the complete script again more carefully:

**tool call: python**

```

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# LOAD DATA
# ============================================================================
transitions = pd.read_csv('data/transitions.csv')
macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')

with open('data/policy.json', 'r') as f:
    policy = json.load(f)

ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ratings + ['D']

print(f"Portfolio total: {portfolio['obligors'].sum()}")
print(f"Historical quarters: {macro_history['quarter'].min()} to {macro_history['quarter'].max()}")
print(f"Years: {len(transitions['year'].unique())}")

# ============================================================================
# BUILD TRAINING DATA
# ============================================================================

years = sorted(transitions['year'].unique())
num_years = len(years)

# Map years to their ending quarters
# Quarter 0 is end of year 20, quarter -4 is end of year 19, etc.
year_to_end_quarter = {}
for i, year in enumerate(years):
    end_quarter = 0 - (20 - year) * 4
    year_to_end_quarter[year] = end_quarter

training_data = []

for year in years:
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3  # 4 quarters in the year
    
    year_trans = transitions[transitions['year'] == year]
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    # Average macro conditions over the year
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        to_cols = [f'to_{r}' for r in ratings] + ['to_D']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'year': year,
                'from_rating': from_rating,
                'total': total,
            }
            # Add transitions
            for col in to_cols:
                row_dict[col] = trans_row[col]
            # Add macro averages
            for col in macro_cols:
                row_dict[col] = macro_avg[col]
            
            training_data.append(row_dict)

training_df = pd.DataFrame(training_data)
print(f"\nTraining data shape: {training_df.shape}")
print(training_df.head())
print("\nMacro columns:", [c for c in training_df.columns if c not in 
                          ['year', 'from_rating', 'total'] + [f'to_{r}' for r in ratings] + ['to_D']])

```

## [11] tool

Traceback (most recent call last):
  File "<stdin>", line 61, in <module>
  File "/usr/local/lib/python3.12/site-packages/pandas/core/series.py", line 991, in __getitem__
    return self._get_with(key)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/series.py", line 1003, in _get_with
    return self.loc[key]
           ~~~~~~~~^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexing.py", line 1207, in __getitem__
    return self._getitem_axis(maybe_callable, axis=axis)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexing.py", line 1438, in _getitem_axis
    return self._getitem_iterable(key, axis=axis)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexing.py", line 1378, in _getitem_iterable
    keyarr, indexer = self._get_listlike_indexer(key, axis)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexing.py", line 1576, in _get_listlike_indexer
    keyarr, indexer = ax._get_indexer_strict(key, axis_name)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6302, in _get_indexer_strict
    self._raise_if_missing(keyarr, indexer, axis_name)
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 6355, in _raise_if_missing
    raise KeyError(f"{not_found} not in index")
KeyError: "['to_CCC/C'] not in index"

Portfolio total: 9999
Historical quarters: -79 to 0
Years: 20


## [12] assistant

The rating name has a slash. Let me fix that:

**tool call: python**

```

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# LOAD DATA
# ============================================================================
transitions = pd.read_csv('data/transitions.csv')
macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')

with open('data/policy.json', 'r') as f:
    policy = json.load(f)

ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ratings + ['D']

print(f"Portfolio total: {portfolio['obligors'].sum()}")
print(f"Transitions columns:", transitions.columns.tolist())

# ============================================================================
# BUILD TRAINING DATA
# ============================================================================

years = sorted(transitions['year'].unique())
num_years = len(years)

# Map years to their ending quarters
year_to_end_quarter = {}
for i, year in enumerate(years):
    end_quarter = 0 - (20 - year) * 4
    year_to_end_quarter[year] = end_quarter

training_data = []

for year in years:
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3  # 4 quarters in the year
    
    year_trans = transitions[transitions['year'] == year]
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    # Average macro conditions over the year
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        to_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'year': year,
                'from_rating': from_rating,
                'total': total,
            }
            # Add transitions
            for col in to_cols:
                row_dict[col] = trans_row[col]
            # Add macro averages
            for col in macro_cols:
                row_dict[col] = macro_avg[col]
            
            training_data.append(row_dict)

training_df = pd.DataFrame(training_data)
print(f"\nTraining data shape: {training_df.shape}")
print(training_df.head())

# Find macro columns (those with NaN, meaning they started later)
macro_features = [c for c in macro_history.columns if c != 'quarter']
print(f"\nMacro features: {macro_features}")

# Check which ones have enough data
for col in macro_features:
    null_count = training_df[col].isna().sum()
    print(f"  {col}: {null_count} nulls out of {len(training_df)}")

```

## [13] tool

Portfolio total: 9999
Transitions columns: ['year', 'from_rating', 'to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

Training data shape: (140, 20)
   year from_rating  total  to_AAA  ...  djia      nasdaq  vix         cpi
0     1         AAA     99      88  ...   NaN  169.478325  NaN  135.101375
1     1          AA    403       1  ...   NaN  169.478325  NaN  135.101375
2     1           A   2015       0  ...   NaN  169.478325  NaN  135.101375
3     1         BBB   3950       0  ...   NaN  169.478325  NaN  135.101375
4     1          BB   2471       0  ...   NaN  169.478325  NaN  135.101375

[5 rows x 20 columns]

Macro features: ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
  gdp: 0 nulls out of 140
  unemployment: 0 nulls out of 140
  hpi: 28 nulls out of 140
  bbb_spread: 7 nulls out of 140
  sp500: 49 nulls out of 140
  djia: 49 nulls out of 140
  nasdaq: 0 nulls out of 140
  vix: 21 nulls out of 140
  cpi: 0 nulls out of 140


## [14] assistant

**tool call: python**

```

# Use macro features that have good coverage
# Drop early years with too many missing values, or impute
# Let's use features with minimal missingness: gdp, unemployment, nasdaq, cpi
# and those with some missingness we can work with

macro_features_to_use = ['gdp', 'unemployment', 'nasdaq', 'cpi']

# For features with more missingness, we could use forward fill or mean
# But let's start simple with the complete ones

print("Features to use:", macro_features_to_use)

# Calculate transition probabilities and model default rates
# Model approach: 
# 1. For each from_rating and to_state, estimate a logistic regression using macro features
# 2. Predict quarterly transitions using scenario macro paths

# Let's model this more simply:
# For each from_rating, we'll model the transition matrix conditional on macro factors
# We'll fit a multinomial logit or separate logits for each destination state

# First, let's normalize transitions to get probabilities
training_df['total_check'] = training_df[['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']].sum(axis=1)

for to_state in ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']:
    training_df[f'p_{to_state}'] = training_df[to_state] / training_df['total']

print("\nSample probabilities:")
print(training_df[['from_rating', 'to_D', 'p_to_D', 'total']].head(20))

# For each rating, calculate average annual default rate and other stats
print("\nDefault rates by rating:")
for rating in ratings:
    subset = training_df[training_df['from_rating'] == rating]
    total_obligors = subset['total'].sum()
    total_defaults = subset['to_D'].sum()
    default_rate = total_defaults / total_obligors if total_obligors > 0 else 0
    print(f"  {rating}: {default_rate:.6f} ({total_defaults}/{total_obligors})")

```

## [15] tool

Traceback (most recent call last):
  File "<stdin>", line 24, in <module>
NameError: name 'training_df' is not defined

Features to use: ['gdp', 'unemployment', 'nasdaq', 'cpi']


## [16] assistant

I need to keep everything in one script. Let me write a comprehensive unified script:

**tool call: python**

```

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# LOAD DATA
# ============================================================================
transitions = pd.read_csv('data/transitions.csv')
macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')

with open('data/policy.json', 'r') as f:
    policy = json.load(f)

ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ratings + ['D']
to_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

# ============================================================================
# BUILD TRAINING DATA
# ============================================================================

years = sorted(transitions['year'].unique())

# Map years to their ending quarters
year_to_end_quarter = {}
for year in years:
    end_quarter = 0 - (20 - year) * 4
    year_to_end_quarter[year] = end_quarter

training_data = []

for year in years:
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_trans = transitions[transitions['year'] == year]
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'year': year,
                'from_rating': from_rating,
                'total': total,
            }
            for col in to_cols:
                row_dict[col] = trans_row[col]
            for col in macro_cols:
                row_dict[col] = macro_avg[col]
            
            training_data.append(row_dict)

training_df = pd.DataFrame(training_data)

# Calculate probabilities
for to_state in to_cols:
    training_df[f'p_{to_state}'] = training_df[to_state] / training_df['total']

print("Training data loaded")
print(f"  Shape: {training_df.shape}")
print(f"  Years: {training_df['year'].min()} to {training_df['year'].max()}")
print(f"  Ratings: {training_df['from_rating'].unique()}")

# Calculate average default rates by rating to understand the data
print("\nDefault rates by rating (annual):")
for rating in ratings:
    subset = training_df[training_df['from_rating'] == rating]
    total_obligors = subset['total'].sum()
    total_defaults = subset['to_D'].sum()
    default_rate = total_defaults / total_obligors if total_obligors > 0 else 0
    print(f"  {rating}: {default_rate:.6f}")

# ============================================================================
# SIMPLE MODEL: ESTIMATE TRANSITION MATRICES BASED ON MACRO CONDITIONS
# ============================================================================
# Strategy: Use multivariate logistic regression to model each destination state
# for each source rating, conditional on macro variables

# Features to use
macro_features = ['gdp', 'unemployment', 'nasdaq', 'cpi']

# Standardize macro features for modeling
scaler = StandardScaler()
training_df_scaled = training_df.copy()
training_df_scaled[macro_features] = scaler.fit_transform(training_df[macro_features])

print(f"\nMacro feature scaling complete")
print(f"  Mean: {training_df[macro_features].mean().to_dict()}")
print(f"  Std: {training_df[macro_features].std().to_dict()}")

# Store scaler info for later
scaler_means = training_df[macro_features].mean().to_dict()
scaler_stds = training_df[macro_features].std().to_dict()

# Fit logistic regression models for each rating and each destination
# For efficiency, we'll estimate a model that maps standardized macros to each transition probability

models = {}  # {from_rating: {to_state: model}}

for rating in ratings:
    subset = training_df_scaled[training_df_scaled['from_rating'] == rating].copy()
    
    if len(subset) == 0:
        continue
    
    models[rating] = {}
    X = subset[macro_features].values
    
    for to_state in to_cols:
        y = subset[f'p_{to_state}'].values
        
        # Fit a simple linear regression (bounded logit would be better)
        # Use LogisticRegression for default specifically
        if to_state == 'to_D':
            # For default, use binomial outcomes
            y_binary = subset[to_state].values  # counts
            n = subset['total'].values  # denominators
            
            # Fit weighted logistic regression
            model = LogisticRegression(fit_intercept=True, max_iter=1000, C=1.0)
            
            # Create binary outcomes with weights
            # This is a rough approach: for now, use average probability
            y_probs = subset[f'p_to_D'].values
            
            try:
                model.fit(X, y_binary > 0, sample_weight=n)
                models[rating][to_state] = ('logistic', model)
            except:
                # If fitting fails, use the mean
                models[rating][to_state] = ('mean', subset[f'p_{to_state}'].mean())
        else:
            # For non-default states, use linear regression
            # (probabilities should be non-negative and sum to 1)
            from sklearn.linear_model import Ridge
            model = Ridge(alpha=1.0)
            model.fit(X, y)
            models[rating][to_state] = ('linear', model)

print(f"\nFitted models for {len(models)} ratings")
for rating in sorted(models.keys()):
    print(f"  {rating}: {len(models[rating])} destination states")

```

## [17] tool

Training data loaded
  Shape: (140, 28)
  Years: 1 to 20
  Ratings: <StringArray>
['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
Length: 7, dtype: str

Default rates by rating (annual):
  AAA: 0.000000
  AA: 0.000210
  A: 0.000713
  BBB: 0.002233
  BB: 0.007834
  B: 0.035861
  CCC/C: 0.320114

Macro feature scaling complete
  Mean: {'gdp': 153.91815874999998, 'unemployment': 6.0721637500000005, 'nasdaq': 107.21525000000001, 'cpi': 174.0688325}
  Std: {'gdp': 21.35549929239306, 'unemployment': 1.756089834470191, 'nasdaq': 31.066767149741523, 'cpi': 29.231299587416192}

Fitted models for 7 ratings
  A: 8 destination states
  AA: 8 destination states
  AAA: 8 destination states
  B: 8 destination states
  BB: 8 destination states
  BBB: 8 destination states
  CCC/C: 8 destination states


## [18] assistant

Good! Now let me create predictions for each scenario:

**tool call: python**

```

# ============================================================================
# PREPARE SCENARIO PATHS
# ============================================================================

# The scenario_data has quarters 1 through 9
scenarios_list = sorted(scenario_data['scenario'].unique())
print(f"Scenarios: {scenarios_list}")

# For each scenario and quarter, we need to get the macro conditions
scenario_macro_data = {}
for scenario in scenarios_list:
    scenario_macro_data[scenario] = scenario_data[scenario_data['scenario'] == scenario].copy()
    scenario_macro_data[scenario].set_index('quarter', inplace=True)
    print(f"\n{scenario}:")
    print(scenario_macro_data[scenario][[m for m in macro_features if m in scenario_macro_data[scenario].columns]])

# ============================================================================
# PROJECT COHORT THROUGH SCENARIOS
# ============================================================================

def predict_quarterly_transitions(macro_values_dict, models, scaler_means, scaler_stds, macro_features):
    """
    Given macro conditions for a quarter, predict transition matrix
    macro_values_dict: dict of {feature: value}
    Returns: dict of {from_rating: {to_state: probability}}
    """
    
    # Standardize the macro values
    macro_array = np.array([macro_values_dict[f] for f in macro_features]).reshape(1, -1)
    macro_scaled = (macro_array - np.array([scaler_means[f] for f in macro_features])) / \
                   np.array([scaler_stds[f] for f in macro_features])
    
    transitions_pred = {}
    
    for from_rating in models:
        transitions_pred[from_rating] = {}
        X_test = macro_scaled
        
        probs = {}
        for to_state in to_cols:
            if to_state not in models[from_rating]:
                probs[to_state] = 0.0
                continue
            
            model_type, model = models[from_rating][to_state]
            
            if model_type == 'linear':
                pred = model.predict(X_test)[0]
                probs[to_state] = max(0, pred)  # Clip to non-negative
            elif model_type == 'logistic':
                pred_prob = model.predict_proba(X_test)[0, 1]  # P(default=True)
                probs[to_state] = pred_prob
            else:  # mean
                probs[to_state] = model
        
        # Normalize to sum to 1
        total_prob = sum(probs.values())
        if total_prob > 0:
            for to_state in probs:
                probs[to_state] /= total_prob
        else:
            # Fallback: equal distribution
            for to_state in to_cols:
                probs[to_state] = 1.0 / len(to_cols)
        
        transitions_pred[from_rating] = probs
    
    return transitions_pred

# Initial portfolio
initial_cohort = {}
for _, row in portfolio.iterrows():
    initial_cohort[row['rating']] = row['obligors']

print("\nInitial portfolio:")
for rating in ratings:
    print(f"  {rating}: {initial_cohort.get(rating, 0)}")

total_initial = sum(initial_cohort.values())
print(f"  Total: {total_initial}")

# Project forward for each scenario
checkpoints = policy['checkpoints']
predictions_list = []

for scenario in scenarios_list:
    print(f"\n\n{'='*60}")
    print(f"Projecting {scenario}")
    print(f"{'='*60}")
    
    # Start with initial cohort
    current_cohort = initial_cohort.copy()
    
    # Track cumulative defaults
    cumulative_defaults = 0
    
    for quarter in range(1, 10):
        # Get macro conditions for this quarter
        if quarter in scenario_macro_data[scenario].index:
            macro_q = scenario_macro_data[scenario].loc[quarter]
            macro_dict = {f: macro_q[f] for f in macro_features}
        else:
            print(f"  Warning: Quarter {quarter} not found")
            continue
        
        # Predict transition matrix for this quarter
        trans_matrix = predict_quarterly_transitions(macro_dict, models, 
                                                      scaler_means, scaler_stds, macro_features)
        
        # Apply transitions
        new_cohort = {rating: 0 for rating in ratings}
        quarterly_defaults = 0
        
        for from_rating in ratings:
            if from_rating not in current_cohort or current_cohort[from_rating] == 0:
                continue
            
            cohort_size = current_cohort[from_rating]
            
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                
                for to_state in to_cols:
                    prob = trans_probs.get(to_state, 0.0)
                    count = cohort_size * prob
                    
                    if to_state == 'to_D':
                        quarterly_defaults += count
                    else:
                        # Extract rating from to_state
                        to_rating = to_state.replace('to_', '')
                        new_cohort[to_rating] += count
        
        cumulative_defaults += quarterly_defaults
        current_cohort = new_cohort
        
        # Record at checkpoints
        if quarter in checkpoints:
            print(f"\nQuarter {quarter}:")
            print(f"  Cumulative defaults: {cumulative_defaults:.1f}")
            print(f"  Remaining in ratings:")
            for rating in ratings:
                count = current_cohort.get(rating, 0)
                share = count / total_initial
                print(f"    {rating}: {count:.1f} ({share:.6f})")
            
            # Add to predictions
            for rating in ratings:
                count = current_cohort.get(rating, 0)
                share = count / total_initial
                predictions_list.append({
                    'scenario': scenario,
                    'quarter': quarter,
                    'state': rating,
                    'share': share
                })
            
            # Add defaults
            default_share = cumulative_defaults / total_initial
            predictions_list.append({
                'scenario': scenario,
                'quarter': quarter,
                'state': 'D',
                'share': default_share
            })

predictions_df = pd.DataFrame(predictions_list)
print("\n\nPredictions shape:", predictions_df.shape)
print(predictions_df.head(20))

# Verify we have 48 rows: 3 scenarios * 2 checkpoints * 8 states
print(f"\nTotal prediction rows: {len(predictions_df)}")
print("Expected: 3 scenarios * 2 checkpoints * 8 states = 48")

```

## [19] tool

Traceback (most recent call last):
  File "<stdin>", line 7, in <module>
NameError: name 'scenario_data' is not defined



## [20] assistant

I need to keep the entire computation in one execution. Let me write a complete end-to-end script:

**tool call: bash**

```
cat > /tmp/full_model.py << 'EOF'
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# LOAD DATA
# ============================================================================
transitions = pd.read_csv('data/transitions.csv')
macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')

with open('data/policy.json', 'r') as f:
    policy = json.load(f)

ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ratings + ['D']
to_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

# ============================================================================
# BUILD TRAINING DATA
# ============================================================================

years = sorted(transitions['year'].unique())

# Map years to their ending quarters
year_to_end_quarter = {}
for year in years:
    end_quarter = 0 - (20 - year) * 4
    year_to_end_quarter[year] = end_quarter

training_data = []

for year in years:
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_trans = transitions[transitions['year'] == year]
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'year': year,
                'from_rating': from_rating,
                'total': total,
            }
            for col in to_cols:
                row_dict[col] = trans_row[col]
            for col in macro_cols:
                row_dict[col] = macro_avg[col]
            
            training_data.append(row_dict)

training_df = pd.DataFrame(training_data)

# Calculate probabilities
for to_state in to_cols:
    training_df[f'p_{to_state}'] = training_df[to_state] / training_df['total']

print("Training data loaded")

# ============================================================================
# FIT MODEL
# ============================================================================

macro_features = ['gdp', 'unemployment', 'nasdaq', 'cpi']

# Standardize
scaler = StandardScaler()
training_df_scaled = training_df.copy()
training_df_scaled[macro_features] = scaler.fit_transform(training_df[macro_features])

scaler_means = training_df[macro_features].mean().to_dict()
scaler_stds = training_df[macro_features].std().to_dict()

# Fit models
models = {}

for rating in ratings:
    subset = training_df_scaled[training_df_scaled['from_rating'] == rating].copy()
    
    if len(subset) == 0:
        continue
    
    models[rating] = {}
    X = subset[macro_features].values
    
    for to_state in to_cols:
        y = subset[f'p_{to_state}'].values
        
        if to_state == 'to_D':
            # For default
            y_binary = subset[to_state].values  # counts
            n = subset['total'].values
            
            model = LogisticRegression(fit_intercept=True, max_iter=1000, C=1.0, random_state=42)
            
            try:
                model.fit(X, y_binary > 0, sample_weight=n)
                models[rating][to_state] = ('logistic', model)
            except:
                models[rating][to_state] = ('mean', subset[f'p_{to_state}'].mean())
        else:
            # For non-default
            model = Ridge(alpha=1.0)
            model.fit(X, y)
            models[rating][to_state] = ('linear', model)

print(f"Fitted models for {len(models)} ratings")

# ============================================================================
# PREPARE SCENARIOS
# ============================================================================

scenario_macro_data = {}
scenarios_list = sorted(scenario_data['scenario'].unique())

for scenario in scenarios_list:
    scenario_macro_data[scenario] = scenario_data[scenario_data['scenario'] == scenario].copy()
    scenario_macro_data[scenario].set_index('quarter', inplace=True)

print(f"Loaded {len(scenarios_list)} scenarios")

# ============================================================================
# PREDICTION FUNCTION
# ============================================================================

def predict_quarterly_transitions(macro_values_dict, models, scaler_means, scaler_stds, macro_features):
    """
    Given macro conditions for a quarter, predict transition matrix
    """
    
    macro_array = np.array([macro_values_dict[f] for f in macro_features]).reshape(1, -1)
    macro_scaled = (macro_array - np.array([scaler_means[f] for f in macro_features])) / \
                   np.array([scaler_stds[f] for f in macro_features])
    
    transitions_pred = {}
    
    for from_rating in models:
        transitions_pred[from_rating] = {}
        X_test = macro_scaled
        
        probs = {}
        for to_state in to_cols:
            if to_state not in models[from_rating]:
                probs[to_state] = 0.0
                continue
            
            model_type, model = models[from_rating][to_state]
            
            if model_type == 'linear':
                pred = model.predict(X_test)[0]
                probs[to_state] = max(0, pred)
            elif model_type == 'logistic':
                pred_prob = model.predict_proba(X_test)[0, 1]
                probs[to_state] = pred_prob
            else:  # mean
                probs[to_state] = model
        
        # Normalize
        total_prob = sum(probs.values())
        if total_prob > 0:
            for to_state in probs:
                probs[to_state] /= total_prob
        else:
            for to_state in to_cols:
                probs[to_state] = 1.0 / len(to_cols)
        
        transitions_pred[from_rating] = probs
    
    return transitions_pred

# ============================================================================
# PROJECT COHORT
# ============================================================================

initial_cohort = {}
for _, row in portfolio.iterrows():
    initial_cohort[row['rating']] = row['obligors']

total_initial = sum(initial_cohort.values())

checkpoints = policy['checkpoints']
predictions_list = []
matrices_list = []

for scenario in scenarios_list:
    print(f"\nProjecting {scenario}...")
    
    current_cohort = {r: initial_cohort.get(r, 0) for r in ratings}
    cumulative_defaults = 0
    
    for quarter in range(1, 10):
        # Get macro for this quarter
        if quarter in scenario_macro_data[scenario].index:
            macro_q = scenario_macro_data[scenario].loc[quarter]
            macro_dict = {f: macro_q[f] for f in macro_features}
        else:
            continue
        
        # Predict transitions
        trans_matrix = predict_quarterly_transitions(macro_dict, models, 
                                                      scaler_means, scaler_stds, macro_features)
        
        # Record matrix for this quarter
        for from_rating in ratings:
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                row_dict = {
                    'scenario': scenario,
                    'quarter': quarter,
                    'from_rating': from_rating,
                }
                for to_state in to_cols:
                    row_dict[to_state[3:]] = trans_probs.get(to_state, 0.0)
                
                # Rename CCC_C back to CCC/C for output
                if 'CCC_C' in row_dict:
                    row_dict['CCC/C'] = row_dict.pop('CCC_C')
                
                matrices_list.append(row_dict)
        
        # Apply transitions to cohort
        new_cohort = {r: 0.0 for r in ratings}
        quarterly_defaults = 0
        
        for from_rating in ratings:
            if current_cohort[from_rating] == 0:
                continue
            
            cohort_size = current_cohort[from_rating]
            
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                
                for to_state in to_cols:
                    prob = trans_probs.get(to_state, 0.0)
                    count = cohort_size * prob
                    
                    if to_state == 'to_D':
                        quarterly_defaults += count
                    else:
                        to_rating = to_state.replace('to_', '')
                        if to_rating == 'CCC_C':
                            to_rating = 'CCC/C'
                        new_cohort[to_rating] += count
        
        cumulative_defaults += quarterly_defaults
        current_cohort = new_cohort
        
        # Record at checkpoints
        if quarter in checkpoints:
            for rating in ratings:
                count = current_cohort.get(rating, 0)
                share = count / total_initial
                predictions_list.append({
                    'scenario': scenario,
                    'quarter': quarter,
                    'state': rating,
                    'share': share
                })
            
            default_share = cumulative_defaults / total_initial
            predictions_list.append({
                'scenario': scenario,
                'quarter': quarter,
                'state': 'D',
                'share': default_share
            })

# ============================================================================
# OUTPUT PREDICTIONS
# ============================================================================

predictions_df = pd.DataFrame(predictions_list)
predictions_df.to_csv('predictions.csv', index=False)

print(f"\nWrote predictions.csv: {len(predictions_df)} rows")
print(f"Expected: 48 rows (3 scenarios * 2 checkpoints * 8 states)")

# ============================================================================
# OUTPUT MATRICES
# ============================================================================

matrices_df = pd.DataFrame(matrices_list)

# Rename columns
col_mapping = {
    'AAA': 'to_AAA',
    'AA': 'to_AA',
    'A': 'to_A',
    'BBB': 'to_BBB',
    'BB': 'to_BB',
    'B': 'to_B',
    'CCC/C': 'to_CCC_C',
    'D': 'to_D'
}

matrices_df = matrices_df.rename(columns=col_mapping)

# Also add historical matrices
history_matrices_list = []

for year in sorted(years):
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_trans = transitions[transitions['year'] == year]
    
    # Calculate transition probabilities for this year
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'scenario': 'history',
                'quarter': end_q,  # Use end quarter
                'from_rating': from_rating,
            }
            for to_state in to_cols:
                prob = trans_row[to_state] / total
                state_name = to_state.replace('to_', '')
                row_dict[state_name] = prob
            
            history_matrices_list.append(row_dict)

history_matrices_df = pd.DataFrame(history_matrices_list)
history_matrices_df = history_matrices_df.rename(columns=col_mapping)

# Combine
all_matrices = pd.concat([matrices_df, history_matrices_df], ignore_index=True)
all_matrices.to_csv('matrices.csv', index=False)

print(f"Wrote matrices.csv: {len(all_matrices)} rows")
print(f"  Scenarios: {len(matrices_df)} rows")
print(f"  History: {len(history_matrices_df)} rows")

# ============================================================================
# OUTPUT BACKTEST
# ============================================================================

backtest_list = []

for year in sorted(years):
    year_trans = transitions[transitions['year'] == year]
    
    # Total obligors in this year
    total_obligors_year = year_trans['total'].sum()
    
    # Total defaults this year
    total_defaults_year = year_trans['to_D'].sum()
    
    # Annual default rate
    annual_default_rate = total_defaults_year / total_obligors_year if total_obligors_year > 0 else 0
    
    # Now predict using the model for this year
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    macro_dict = {f: macro_avg[f] for f in macro_features}
    
    # Get transition matrix for this quarter (use end quarter macro)
    trans_matrix = predict_quarterly_transitions(macro_dict, models, 
                                                  scaler_means, scaler_stds, macro_features)
    
    # Calculate model's predicted annual default rate
    # For this, use the year-starting cohort and 4 quarterly transitions
    model_cohort = {r: 0 for r in ratings}
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        cohort_count = trans_row[to_cols].sum()
        if cohort_count > 0:
            model_cohort[from_rating] = cohort_count
    
    # Apply 4 quarterly transitions
    cumulative_defaults_model = 0
    for q in range(4):
        new_cohort = {r: 0.0 for r in ratings}
        
        for from_rating in ratings:
            if model_cohort[from_rating] == 0:
                continue
            
            cohort_size = model_cohort[from_rating]
            
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                
                for to_state in to_cols:
                    prob = trans_probs.get(to_state, 0.0)
                    count = cohort_size * prob
                    
                    if to_state == 'to_D':
                        cumulative_defaults_model += count
                    else:
                        to_rating = to_state.replace('to_', '')
                        if to_rating == 'CCC_C':
                            to_rating = 'CCC/C'
                        new_cohort[to_rating] += count
        
        model_cohort = new_cohort
    
    model_default_rate = cumulative_defaults_model / total_obligors_year if total_obligors_year > 0 else 0
    
    # Add to backtest for all three scenarios (same model)
    for scenario in scenarios_list:
        backtest_list.append({
            'scenario': scenario,
            'year': year,
            'default_rate': model_default_rate
        })

backtest_df = pd.DataFrame(backtest_list)
backtest_df.to_csv('backtest.csv', index=False)

print(f"Wrote backtest.csv: {len(backtest_df)} rows")

print("\nDone!")
EOF
python /tmp/full_model.py

```

## [21] tool

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 3641, in get_loc
    return self._engine.get_loc(casted_key)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "pandas/_libs/index.pyx", line 168, in pandas._libs.index.IndexEngine.get_loc
  File "pandas/_libs/index.pyx", line 197, in pandas._libs.index.IndexEngine.get_loc
  File "pandas/_libs/hashtable_class_helper.pxi", line 7668, in pandas._libs.hashtable.PyObjectHashTable.get_item
  File "pandas/_libs/hashtable_class_helper.pxi", line 7676, in pandas._libs.hashtable.PyObjectHashTable.get_item
KeyError: 'total'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/tmp/full_model.py", line 362, in <module>
    total_obligors_year = year_trans['total'].sum()
                          ~~~~~~~~~~^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/frame.py", line 4378, in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/core/indexes/base.py", line 3648, in get_loc
    raise KeyError(key) from err
KeyError: 'total'

Training data loaded
Fitted models for 7 ratings
Loaded 3 scenarios

Projecting adverse...

Projecting baseline...

Projecting severe...

Wrote predictions.csv: 48 rows
Expected: 48 rows (3 scenarios * 2 checkpoints * 8 states)
Wrote matrices.csv: 329 rows
  Scenarios: 189 rows
  History: 140 rows


## [22] assistant

The backtest calculation has a small issue. Let me fix it:

**tool call: bash**

```
cat > /tmp/full_model.py << 'EOF'
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# LOAD DATA
# ============================================================================
transitions = pd.read_csv('data/transitions.csv')
macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')

with open('data/policy.json', 'r') as f:
    policy = json.load(f)

ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ratings + ['D']
to_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

# ============================================================================
# BUILD TRAINING DATA
# ============================================================================

years = sorted(transitions['year'].unique())

# Map years to their ending quarters
year_to_end_quarter = {}
for year in years:
    end_quarter = 0 - (20 - year) * 4
    year_to_end_quarter[year] = end_quarter

training_data = []

for year in years:
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_trans = transitions[transitions['year'] == year]
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'year': year,
                'from_rating': from_rating,
                'total': total,
            }
            for col in to_cols:
                row_dict[col] = trans_row[col]
            for col in macro_cols:
                row_dict[col] = macro_avg[col]
            
            training_data.append(row_dict)

training_df = pd.DataFrame(training_data)

# Calculate probabilities
for to_state in to_cols:
    training_df[f'p_{to_state}'] = training_df[to_state] / training_df['total']

print("Training data loaded")

# ============================================================================
# FIT MODEL
# ============================================================================

macro_features = ['gdp', 'unemployment', 'nasdaq', 'cpi']

# Standardize
scaler = StandardScaler()
training_df_scaled = training_df.copy()
training_df_scaled[macro_features] = scaler.fit_transform(training_df[macro_features])

scaler_means = training_df[macro_features].mean().to_dict()
scaler_stds = training_df[macro_features].std().to_dict()

# Fit models
models = {}

for rating in ratings:
    subset = training_df_scaled[training_df_scaled['from_rating'] == rating].copy()
    
    if len(subset) == 0:
        continue
    
    models[rating] = {}
    X = subset[macro_features].values
    
    for to_state in to_cols:
        y = subset[f'p_{to_state}'].values
        
        if to_state == 'to_D':
            # For default
            y_binary = subset[to_state].values  # counts
            n = subset['total'].values
            
            model = LogisticRegression(fit_intercept=True, max_iter=1000, C=1.0, random_state=42)
            
            try:
                model.fit(X, y_binary > 0, sample_weight=n)
                models[rating][to_state] = ('logistic', model)
            except:
                models[rating][to_state] = ('mean', subset[f'p_{to_state}'].mean())
        else:
            # For non-default
            model = Ridge(alpha=1.0)
            model.fit(X, y)
            models[rating][to_state] = ('linear', model)

print(f"Fitted models for {len(models)} ratings")

# ============================================================================
# PREPARE SCENARIOS
# ============================================================================

scenario_macro_data = {}
scenarios_list = sorted(scenario_data['scenario'].unique())

for scenario in scenarios_list:
    scenario_macro_data[scenario] = scenario_data[scenario_data['scenario'] == scenario].copy()
    scenario_macro_data[scenario].set_index('quarter', inplace=True)

print(f"Loaded {len(scenarios_list)} scenarios")

# ============================================================================
# PREDICTION FUNCTION
# ============================================================================

def predict_quarterly_transitions(macro_values_dict, models, scaler_means, scaler_stds, macro_features):
    """
    Given macro conditions for a quarter, predict transition matrix
    """
    
    macro_array = np.array([macro_values_dict[f] for f in macro_features]).reshape(1, -1)
    macro_scaled = (macro_array - np.array([scaler_means[f] for f in macro_features])) / \
                   np.array([scaler_stds[f] for f in macro_features])
    
    transitions_pred = {}
    
    for from_rating in models:
        transitions_pred[from_rating] = {}
        X_test = macro_scaled
        
        probs = {}
        for to_state in to_cols:
            if to_state not in models[from_rating]:
                probs[to_state] = 0.0
                continue
            
            model_type, model = models[from_rating][to_state]
            
            if model_type == 'linear':
                pred = model.predict(X_test)[0]
                probs[to_state] = max(0, pred)
            elif model_type == 'logistic':
                pred_prob = model.predict_proba(X_test)[0, 1]
                probs[to_state] = pred_prob
            else:  # mean
                probs[to_state] = model
        
        # Normalize
        total_prob = sum(probs.values())
        if total_prob > 0:
            for to_state in probs:
                probs[to_state] /= total_prob
        else:
            for to_state in to_cols:
                probs[to_state] = 1.0 / len(to_cols)
        
        transitions_pred[from_rating] = probs
    
    return transitions_pred

# ============================================================================
# PROJECT COHORT
# ============================================================================

initial_cohort = {}
for _, row in portfolio.iterrows():
    initial_cohort[row['rating']] = row['obligors']

total_initial = sum(initial_cohort.values())

checkpoints = policy['checkpoints']
predictions_list = []
matrices_list = []

for scenario in scenarios_list:
    print(f"\nProjecting {scenario}...")
    
    current_cohort = {r: initial_cohort.get(r, 0) for r in ratings}
    cumulative_defaults = 0
    
    for quarter in range(1, 10):
        # Get macro for this quarter
        if quarter in scenario_macro_data[scenario].index:
            macro_q = scenario_macro_data[scenario].loc[quarter]
            macro_dict = {f: macro_q[f] for f in macro_features}
        else:
            continue
        
        # Predict transitions
        trans_matrix = predict_quarterly_transitions(macro_dict, models, 
                                                      scaler_means, scaler_stds, macro_features)
        
        # Record matrix for this quarter
        for from_rating in ratings:
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                row_dict = {
                    'scenario': scenario,
                    'quarter': quarter,
                    'from_rating': from_rating,
                }
                for to_state in to_cols:
                    row_dict[to_state[3:]] = trans_probs.get(to_state, 0.0)
                
                # Rename CCC_C back to CCC/C for output
                if 'CCC_C' in row_dict:
                    row_dict['CCC/C'] = row_dict.pop('CCC_C')
                
                matrices_list.append(row_dict)
        
        # Apply transitions to cohort
        new_cohort = {r: 0.0 for r in ratings}
        quarterly_defaults = 0
        
        for from_rating in ratings:
            if current_cohort[from_rating] == 0:
                continue
            
            cohort_size = current_cohort[from_rating]
            
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                
                for to_state in to_cols:
                    prob = trans_probs.get(to_state, 0.0)
                    count = cohort_size * prob
                    
                    if to_state == 'to_D':
                        quarterly_defaults += count
                    else:
                        to_rating = to_state.replace('to_', '')
                        if to_rating == 'CCC_C':
                            to_rating = 'CCC/C'
                        new_cohort[to_rating] += count
        
        cumulative_defaults += quarterly_defaults
        current_cohort = new_cohort
        
        # Record at checkpoints
        if quarter in checkpoints:
            for rating in ratings:
                count = current_cohort.get(rating, 0)
                share = count / total_initial
                predictions_list.append({
                    'scenario': scenario,
                    'quarter': quarter,
                    'state': rating,
                    'share': share
                })
            
            default_share = cumulative_defaults / total_initial
            predictions_list.append({
                'scenario': scenario,
                'quarter': quarter,
                'state': 'D',
                'share': default_share
            })

# ============================================================================
# OUTPUT PREDICTIONS
# ============================================================================

predictions_df = pd.DataFrame(predictions_list)
predictions_df.to_csv('predictions.csv', index=False)

print(f"\nWrote predictions.csv: {len(predictions_df)} rows")
print(f"Expected: 48 rows (3 scenarios * 2 checkpoints * 8 states)")

# ============================================================================
# OUTPUT MATRICES
# ============================================================================

matrices_df = pd.DataFrame(matrices_list)

# Rename columns
col_mapping = {
    'AAA': 'to_AAA',
    'AA': 'to_AA',
    'A': 'to_A',
    'BBB': 'to_BBB',
    'BB': 'to_BB',
    'B': 'to_B',
    'CCC/C': 'to_CCC_C',
    'D': 'to_D'
}

matrices_df = matrices_df.rename(columns=col_mapping)

# Also add historical matrices
history_matrices_list = []

for year in sorted(years):
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_trans = transitions[transitions['year'] == year]
    
    # Calculate transition probabilities for this year
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'scenario': 'history',
                'quarter': end_q,  # Use end quarter
                'from_rating': from_rating,
            }
            for to_state in to_cols:
                prob = trans_row[to_state] / total
                state_name = to_state.replace('to_', '')
                row_dict[state_name] = prob
            
            history_matrices_list.append(row_dict)

history_matrices_df = pd.DataFrame(history_matrices_list)
history_matrices_df = history_matrices_df.rename(columns=col_mapping)

# Combine
all_matrices = pd.concat([matrices_df, history_matrices_df], ignore_index=True)
all_matrices.to_csv('matrices.csv', index=False)

print(f"Wrote matrices.csv: {len(all_matrices)} rows")
print(f"  Scenarios: {len(matrices_df)} rows")
print(f"  History: {len(history_matrices_df)} rows")

# ============================================================================
# OUTPUT BACKTEST
# ============================================================================

backtest_list = []

for year in sorted(years):
    year_trans = transitions[transitions['year'] == year]
    
    # Total obligors in this year (sum of row totals)
    total_obligors_year = year_trans[to_cols].sum().sum()
    
    # Total defaults this year
    total_defaults_year = year_trans['to_D'].sum()
    
    # Now predict using the model for this year
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    macro_dict = {f: macro_avg[f] for f in macro_features}
    
    # Get transition matrix for this quarter (use end quarter macro)
    trans_matrix = predict_quarterly_transitions(macro_dict, models, 
                                                  scaler_means, scaler_stds, macro_features)
    
    # Calculate model's predicted annual default rate
    # For this, use the year-starting cohort and 4 quarterly transitions
    model_cohort = {r: 0 for r in ratings}
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        cohort_count = trans_row[to_cols].sum()
        if cohort_count > 0:
            model_cohort[from_rating] = cohort_count
    
    # Apply 4 quarterly transitions
    cumulative_defaults_model = 0
    for q in range(4):
        new_cohort = {r: 0.0 for r in ratings}
        
        for from_rating in ratings:
            if model_cohort[from_rating] == 0:
                continue
            
            cohort_size = model_cohort[from_rating]
            
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                
                for to_state in to_cols:
                    prob = trans_probs.get(to_state, 0.0)
                    count = cohort_size * prob
                    
                    if to_state == 'to_D':
                        cumulative_defaults_model += count
                    else:
                        to_rating = to_state.replace('to_', '')
                        if to_rating == 'CCC_C':
                            to_rating = 'CCC/C'
                        new_cohort[to_rating] += count
        
        model_cohort = new_cohort
    
    model_default_rate = cumulative_defaults_model / total_obligors_year if total_obligors_year > 0 else 0
    
    # Add to backtest for all three scenarios (same model)
    for scenario in scenarios_list:
        backtest_list.append({
            'scenario': scenario,
            'year': year,
            'default_rate': model_default_rate
        })

backtest_df = pd.DataFrame(backtest_list)
backtest_df.to_csv('backtest.csv', index=False)

print(f"Wrote backtest.csv: {len(backtest_df)} rows")

print("\nDone!")
EOF
python /tmp/full_model.py

```

## [23] tool

Training data loaded
Fitted models for 7 ratings
Loaded 3 scenarios

Projecting adverse...

Projecting baseline...

Projecting severe...

Wrote predictions.csv: 48 rows
Expected: 48 rows (3 scenarios * 2 checkpoints * 8 states)
Wrote matrices.csv: 329 rows
  Scenarios: 189 rows
  History: 140 rows
Wrote backtest.csv: 60 rows

Done!


## [24] assistant

Excellent! Let me verify the output files:

**tool call: python**

```

import pandas as pd

# Check predictions
pred = pd.read_csv('predictions.csv')
print("PREDICTIONS.CSV:")
print(f"Shape: {pred.shape}")
print(f"Scenarios: {pred['scenario'].unique()}")
print(f"Quarters: {pred['quarter'].unique()}")
print(f"States: {pred['state'].unique()}")
print(f"\nFirst 10 rows:")
print(pred.head(10))
print(f"\nLast 10 rows:")
print(pred.tail(10))

# Verify sums to 1
for scenario in pred['scenario'].unique():
    for quarter in pred['quarter'].unique():
        subset = pred[(pred['scenario'] == scenario) & (pred['quarter'] == quarter)]
        total = subset['share'].sum()
        print(f"\n{scenario} Q{quarter}: sum = {total:.6f}")
        if abs(total - 1.0) > 0.01:
            print("  WARNING: Sum not close to 1!")

```

## [25] tool

PREDICTIONS.CSV:
Shape: (48, 4)
Scenarios: <StringArray>
['adverse', 'baseline', 'severe']
Length: 3, dtype: str
Quarters: [4 9]
States: <StringArray>
['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C', 'D']
Length: 8, dtype: str

First 10 rows:
  scenario  quarter  state     share
0  adverse        4    AAA  0.002340
1  adverse        4     AA  0.007850
2  adverse        4      A  0.011968
3  adverse        4    BBB  0.021445
4  adverse        4     BB  0.021075
5  adverse        4      B  0.100795
6  adverse        4  CCC/C  0.022108
7  adverse        4      D  0.812419
8  adverse        9    AAA  0.001071
9  adverse        9     AA  0.001930

Last 10 rows:
   scenario  quarter  state     share
38   severe        4  CCC/C  0.026027
39   severe        4      D  0.815246
40   severe        9    AAA  0.000737
41   severe        9     AA  0.000813
42   severe        9      A  0.000698
43   severe        9    BBB  0.000970
44   severe        9     BB  0.004911
45   severe        9      B  0.052823
46   severe        9  CCC/C  0.013021
47   severe        9      D  0.926026

adverse Q4: sum = 1.000000

adverse Q9: sum = 1.000000

baseline Q4: sum = 1.000000

baseline Q9: sum = 1.000000

severe Q4: sum = 1.000000

severe Q9: sum = 1.000000


## [26] assistant

Perfect! Now let me check the matrices file:

**tool call: python**

```

# Check matrices
matrices = pd.read_csv('matrices.csv')
print("MATRICES.CSV:")
print(f"Shape: {matrices.shape}")
print(f"Columns: {matrices.columns.tolist()}")
print(f"Scenarios: {matrices['scenario'].unique()}")
print(f"Quarters (sample): {sorted(matrices['quarter'].unique())[:10]}")
print(f"From ratings: {matrices['from_rating'].unique()}")

# Check structure
print(f"\nHistory rows: {len(matrices[matrices['scenario'] == 'history'])}")
print(f"Baseline rows: {len(matrices[matrices['scenario'] == 'baseline'])}")
print(f"Adverse rows: {len(matrices[matrices['scenario'] == 'adverse'])}")
print(f"Severe rows: {len(matrices[matrices['scenario'] == 'severe'])}")

# Verify rows sum to 1
print("\nVerifying rows sum to 1:")
probability_cols = [c for c in matrices.columns if c.startswith('to_')]
sample_rows = matrices.sample(min(5, len(matrices)))
for idx, row in sample_rows.iterrows():
    total = row[probability_cols].sum()
    print(f"  {row['scenario']} Q{row['quarter']} {row['from_rating']}: {total:.6f}")

# Check a historical row
hist_rows = matrices[matrices['scenario'] == 'history']
print(f"\nSample historical rows:")
print(hist_rows.head(5))

```

## [27] tool

Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
NameError: name 'pd' is not defined. Did you mean: 'id'?



## [28] assistant

**tool call: bash**

```
cd / && python3 << 'EOF'
import pandas as pd

# Check matrices
matrices = pd.read_csv('matrices.csv')
print("MATRICES.CSV:")
print(f"Shape: {matrices.shape}")
print(f"Columns: {matrices.columns.tolist()}")
print(f"Scenarios: {matrices['scenario'].unique()}")
print(f"Quarters (sample): {sorted(matrices['quarter'].unique())[:10]}")

# Check structure
print(f"\nHistory rows: {len(matrices[matrices['scenario'] == 'history'])}")
print(f"Baseline rows: {len(matrices[matrices['scenario'] == 'baseline'])}")
print(f"Adverse rows: {len(matrices[matrices['scenario'] == 'adverse'])}")
print(f"Severe rows: {len(matrices[matrices['scenario'] == 'severe'])}")

# Verify rows sum to 1
print("\nVerifying sample rows sum to 1:")
probability_cols = [c for c in matrices.columns if c.startswith('to_')]
sample_rows = matrices.sample(min(5, len(matrices)))
for idx, row in sample_rows.iterrows():
    total = row[probability_cols].sum()
    print(f"  {row['scenario']} Q{row['quarter']} {row['from_rating']}: {total:.6f}")

# Check backtest
backtest = pd.read_csv('backtest.csv')
print("\n\nBACKTEST.CSV:")
print(f"Shape: {backtest.shape}")
print(f"Scenarios: {backtest['scenario'].unique()}")
print(f"Years: {sorted(backtest['year'].unique())}")
print(f"\nFirst 10 rows:")
print(backtest.head(10))
print(f"\nLast 10 rows:")
print(backtest.tail(10))

EOF

```

## [29] tool

Traceback (most recent call last):
  File "<stdin>", line 4, in <module>
  File "/usr/local/lib/python3.12/site-packages/pandas/io/parsers/readers.py", line 873, in read_csv
    return _read(filepath_or_buffer, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/io/parsers/readers.py", line 1645, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/io/parsers/readers.py", line 1904, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'matrices.csv'



## [30] assistant

The script ran but the files are in the working directory. Let me check:

**tool call: bash**

```
ls -lh predictions.csv matrices.csv backtest.csv 2>/dev/null && head -5 predictions.csv && echo "---" && head -5 matrices.csv && echo "---" && head -5 backtest.csv
```

## [31] tool

-rw-r--r-- 1 root root 1.8K Oct 22 22:54 backtest.csv
-rw-r--r-- 1 root root  46K Oct 22 22:54 matrices.csv
-rw-r--r-- 1 root root 1.7K Oct 22 22:54 predictions.csv
scenario,quarter,state,share
adverse,4,AAA,0.0023396814991312794
adverse,4,AA,0.00785040528683515
adverse,4,A,0.011968048209248601
adverse,4,BBB,0.021445097226308833
---
scenario,quarter,from_rating,to_AAA,to_AA,to_A,to_BBB,to_BB,to_B,to_D,to_CCC_C,CCC_C
adverse,1,AAA,0.8488040121965571,0.12957356572045536,0.016007507415760465,0.0,0.004024021059830976,0.0,0.0,0.0015908936073960216,
adverse,1,AA,0.0017909256387090902,0.7280130165343001,0.08688980665795357,0.009585045379868158,0.0004744082184526846,0.00029927530482813907,0.17256820760834043,0.0003793146575477569,
adverse,1,A,0.0,0.004962143625317138,0.48462865621331386,0.03539476177611434,0.002262341144795166,0.0013548793405576333,0.4712292194809138,0.0001679984189881114,
adverse,1,BBB,0.0,0.00013533586348318845,0.011236160815831385,0.4592781331785438,0.023136044716407345,0.004171144738494042,0.5010103072563514,0.0010328734308887489,
---
scenario,year,default_rate
adverse,1,0.6865539761217017
baseline,1,0.6865539761217017
severe,1,0.6865539761217017
adverse,2,0.7113371918022638


## [32] assistant

I notice the matrices file has an extra empty column "CCC_C". Let me check and fix that:

**tool call: bash**

```
python3 << 'EOF'
import pandas as pd

matrices = pd.read_csv('matrices.csv')
print("Columns:", matrices.columns.tolist())
print(f"Shape: {matrices.shape}")
print(matrices.iloc[0])

# Check if there's an extra CCC_C column
if 'CCC_C' in matrices.columns:
    print("\nFound extra CCC_C column - need to fix")
    
# The issue is in the dataframe construction. Let me regenerate
EOF

```

## [33] tool

Columns: ['scenario', 'quarter', 'from_rating', 'to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_D', 'to_CCC_C', 'CCC_C']
Shape: (329, 12)
scenario        adverse
quarter               1
from_rating         AAA
to_AAA         0.848804
to_AA          0.129574
to_A           0.016008
to_BBB              0.0
to_BB          0.004024
to_B                0.0
to_D                0.0
to_CCC_C       0.001591
CCC_C               NaN
Name: 0, dtype: object

Found extra CCC_C column - need to fix


## [34] assistant

Let me fix the script to avoid that spurious column:

**tool call: bash**

```
cat > /tmp/full_model.py << 'EOF'
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# LOAD DATA
# ============================================================================
transitions = pd.read_csv('data/transitions.csv')
macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')

with open('data/policy.json', 'r') as f:
    policy = json.load(f)

ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ratings + ['D']
to_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

# ============================================================================
# BUILD TRAINING DATA
# ============================================================================

years = sorted(transitions['year'].unique())

# Map years to their ending quarters
year_to_end_quarter = {}
for year in years:
    end_quarter = 0 - (20 - year) * 4
    year_to_end_quarter[year] = end_quarter

training_data = []

for year in years:
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_trans = transitions[transitions['year'] == year]
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'year': year,
                'from_rating': from_rating,
                'total': total,
            }
            for col in to_cols:
                row_dict[col] = trans_row[col]
            for col in macro_cols:
                row_dict[col] = macro_avg[col]
            
            training_data.append(row_dict)

training_df = pd.DataFrame(training_data)

# Calculate probabilities
for to_state in to_cols:
    training_df[f'p_{to_state}'] = training_df[to_state] / training_df['total']

print("Training data loaded")

# ============================================================================
# FIT MODEL
# ============================================================================

macro_features = ['gdp', 'unemployment', 'nasdaq', 'cpi']

# Standardize
scaler = StandardScaler()
training_df_scaled = training_df.copy()
training_df_scaled[macro_features] = scaler.fit_transform(training_df[macro_features])

scaler_means = training_df[macro_features].mean().to_dict()
scaler_stds = training_df[macro_features].std().to_dict()

# Fit models
models = {}

for rating in ratings:
    subset = training_df_scaled[training_df_scaled['from_rating'] == rating].copy()
    
    if len(subset) == 0:
        continue
    
    models[rating] = {}
    X = subset[macro_features].values
    
    for to_state in to_cols:
        y = subset[f'p_{to_state}'].values
        
        if to_state == 'to_D':
            # For default
            y_binary = subset[to_state].values  # counts
            n = subset['total'].values
            
            model = LogisticRegression(fit_intercept=True, max_iter=1000, C=1.0, random_state=42)
            
            try:
                model.fit(X, y_binary > 0, sample_weight=n)
                models[rating][to_state] = ('logistic', model)
            except:
                models[rating][to_state] = ('mean', subset[f'p_{to_state}'].mean())
        else:
            # For non-default
            model = Ridge(alpha=1.0)
            model.fit(X, y)
            models[rating][to_state] = ('linear', model)

print(f"Fitted models for {len(models)} ratings")

# ============================================================================
# PREPARE SCENARIOS
# ============================================================================

scenario_macro_data = {}
scenarios_list = sorted(scenario_data['scenario'].unique())

for scenario in scenarios_list:
    scenario_macro_data[scenario] = scenario_data[scenario_data['scenario'] == scenario].copy()
    scenario_macro_data[scenario].set_index('quarter', inplace=True)

print(f"Loaded {len(scenarios_list)} scenarios")

# ============================================================================
# PREDICTION FUNCTION
# ============================================================================

def predict_quarterly_transitions(macro_values_dict, models, scaler_means, scaler_stds, macro_features):
    """
    Given macro conditions for a quarter, predict transition matrix
    """
    
    macro_array = np.array([macro_values_dict[f] for f in macro_features]).reshape(1, -1)
    macro_scaled = (macro_array - np.array([scaler_means[f] for f in macro_features])) / \
                   np.array([scaler_stds[f] for f in macro_features])
    
    transitions_pred = {}
    
    for from_rating in models:
        transitions_pred[from_rating] = {}
        X_test = macro_scaled
        
        probs = {}
        for to_state in to_cols:
            if to_state not in models[from_rating]:
                probs[to_state] = 0.0
                continue
            
            model_type, model = models[from_rating][to_state]
            
            if model_type == 'linear':
                pred = model.predict(X_test)[0]
                probs[to_state] = max(0, pred)
            elif model_type == 'logistic':
                pred_prob = model.predict_proba(X_test)[0, 1]
                probs[to_state] = pred_prob
            else:  # mean
                probs[to_state] = model
        
        # Normalize
        total_prob = sum(probs.values())
        if total_prob > 0:
            for to_state in probs:
                probs[to_state] /= total_prob
        else:
            for to_state in to_cols:
                probs[to_state] = 1.0 / len(to_cols)
        
        transitions_pred[from_rating] = probs
    
    return transitions_pred

# ============================================================================
# PROJECT COHORT
# ============================================================================

initial_cohort = {}
for _, row in portfolio.iterrows():
    initial_cohort[row['rating']] = row['obligors']

total_initial = sum(initial_cohort.values())

checkpoints = policy['checkpoints']
predictions_list = []
matrices_list = []

for scenario in scenarios_list:
    print(f"\nProjecting {scenario}...")
    
    current_cohort = {r: initial_cohort.get(r, 0) for r in ratings}
    cumulative_defaults = 0
    
    for quarter in range(1, 10):
        # Get macro for this quarter
        if quarter in scenario_macro_data[scenario].index:
            macro_q = scenario_macro_data[scenario].loc[quarter]
            macro_dict = {f: macro_q[f] for f in macro_features}
        else:
            continue
        
        # Predict transitions
        trans_matrix = predict_quarterly_transitions(macro_dict, models, 
                                                      scaler_means, scaler_stds, macro_features)
        
        # Record matrix for this quarter
        for from_rating in ratings:
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                row_dict = {
                    'scenario': scenario,
                    'quarter': quarter,
                    'from_rating': from_rating,
                    'to_AAA': trans_probs.get('to_AAA', 0.0),
                    'to_AA': trans_probs.get('to_AA', 0.0),
                    'to_A': trans_probs.get('to_A', 0.0),
                    'to_BBB': trans_probs.get('to_BBB', 0.0),
                    'to_BB': trans_probs.get('to_BB', 0.0),
                    'to_B': trans_probs.get('to_B', 0.0),
                    'to_CCC_C': trans_probs.get('to_CCC_C', 0.0),
                    'to_D': trans_probs.get('to_D', 0.0),
                }
                
                matrices_list.append(row_dict)
        
        # Apply transitions to cohort
        new_cohort = {r: 0.0 for r in ratings}
        quarterly_defaults = 0
        
        for from_rating in ratings:
            if current_cohort[from_rating] == 0:
                continue
            
            cohort_size = current_cohort[from_rating]
            
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                
                for to_state in to_cols:
                    prob = trans_probs.get(to_state, 0.0)
                    count = cohort_size * prob
                    
                    if to_state == 'to_D':
                        quarterly_defaults += count
                    else:
                        to_rating = to_state.replace('to_', '')
                        if to_rating == 'CCC_C':
                            to_rating = 'CCC/C'
                        new_cohort[to_rating] += count
        
        cumulative_defaults += quarterly_defaults
        current_cohort = new_cohort
        
        # Record at checkpoints
        if quarter in checkpoints:
            for rating in ratings:
                count = current_cohort.get(rating, 0)
                share = count / total_initial
                predictions_list.append({
                    'scenario': scenario,
                    'quarter': quarter,
                    'state': rating,
                    'share': share
                })
            
            default_share = cumulative_defaults / total_initial
            predictions_list.append({
                'scenario': scenario,
                'quarter': quarter,
                'state': 'D',
                'share': default_share
            })

# ============================================================================
# OUTPUT PREDICTIONS
# ============================================================================

predictions_df = pd.DataFrame(predictions_list)
predictions_df.to_csv('predictions.csv', index=False)

print(f"\nWrote predictions.csv: {len(predictions_df)} rows")

# ============================================================================
# OUTPUT MATRICES
# ============================================================================

matrices_df = pd.DataFrame(matrices_list)

# Also add historical matrices
history_matrices_list = []

for year in sorted(years):
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_trans = transitions[transitions['year'] == year]
    
    # Calculate transition probabilities for this year
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'scenario': 'history',
                'quarter': end_q,
                'from_rating': from_rating,
                'to_AAA': trans_row['to_AAA'] / total,
                'to_AA': trans_row['to_AA'] / total,
                'to_A': trans_row['to_A'] / total,
                'to_BBB': trans_row['to_BBB'] / total,
                'to_BB': trans_row['to_BB'] / total,
                'to_B': trans_row['to_B'] / total,
                'to_CCC_C': trans_row['to_CCC_C'] / total,
                'to_D': trans_row['to_D'] / total,
            }
            
            history_matrices_list.append(row_dict)

history_matrices_df = pd.DataFrame(history_matrices_list)

# Combine
all_matrices = pd.concat([matrices_df, history_matrices_df], ignore_index=True)
all_matrices.to_csv('matrices.csv', index=False)

print(f"Wrote matrices.csv: {len(all_matrices)} rows")

# ============================================================================
# OUTPUT BACKTEST
# ============================================================================

backtest_list = []

for year in sorted(years):
    year_trans = transitions[transitions['year'] == year]
    
    # Total obligors in this year (sum of row totals)
    total_obligors_year = year_trans[to_cols].sum().sum()
    
    # Total defaults this year
    total_defaults_year = year_trans['to_D'].sum()
    
    # Now predict using the model for this year
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    macro_dict = {f: macro_avg[f] for f in macro_features}
    
    # Get transition matrix for this quarter (use end quarter macro)
    trans_matrix = predict_quarterly_transitions(macro_dict, models, 
                                                  scaler_means, scaler_stds, macro_features)
    
    # Calculate model's predicted annual default rate
    # For this, use the year-starting cohort and 4 quarterly transitions
    model_cohort = {r: 0 for r in ratings}
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        cohort_count = trans_row[to_cols].sum()
        if cohort_count > 0:
            model_cohort[from_rating] = cohort_count
    
    # Apply 4 quarterly transitions
    cumulative_defaults_model = 0
    for q in range(4):
        new_cohort = {r: 0.0 for r in ratings}
        
        for from_rating in ratings:
            if model_cohort[from_rating] == 0:
                continue
            
            cohort_size = model_cohort[from_rating]
            
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                
                for to_state in to_cols:
                    prob = trans_probs.get(to_state, 0.0)
                    count = cohort_size * prob
                    
                    if to_state == 'to_D':
                        cumulative_defaults_model += count
                    else:
                        to_rating = to_state.replace('to_', '')
                        if to_rating == 'CCC_C':
                            to_rating = 'CCC/C'
                        new_cohort[to_rating] += count
        
        model_cohort = new_cohort
    
    model_default_rate = cumulative_defaults_model / total_obligors_year if total_obligors_year > 0 else 0
    
    # Add to backtest for all three scenarios (same model)
    for scenario in scenarios_list:
        backtest_list.append({
            'scenario': scenario,
            'year': year,
            'default_rate': model_default_rate
        })

backtest_df = pd.DataFrame(backtest_list)
backtest_df.to_csv('backtest.csv', index=False)

print(f"Wrote backtest.csv: {len(backtest_df)} rows")

print("\nDone!")
EOF
python /tmp/full_model.py

```

## [35] tool

Training data loaded
Fitted models for 7 ratings
Loaded 3 scenarios

Projecting adverse...

Projecting baseline...

Projecting severe...

Wrote predictions.csv: 48 rows
Wrote matrices.csv: 329 rows
Wrote backtest.csv: 60 rows

Done!


## [36] assistant

Perfect! Now let me verify the final outputs:

**tool call: bash**

```
cd / && python3 << 'EOF'
import pandas as pd

print("="*70)
print("VERIFYING OUTPUT FILES")
print("="*70)

# Check predictions
pred = pd.read_csv('predictions.csv')
print("\n1. PREDICTIONS.CSV")
print(f"   Shape: {pred.shape} (expected: 48 rows, 4 cols)")
print(f"   Columns: {pred.columns.tolist()}")
print(f"   Scenarios: {sorted(pred['scenario'].unique())}")
print(f"   Quarters: {sorted(pred['quarter'].unique())}")
print(f"   States: {sorted(pred['state'].unique())}")

# Verify sums to 1
print("\n   Verification - sum by scenario and quarter:")
for scenario in sorted(pred['scenario'].unique()):
    for quarter in sorted(pred['quarter'].unique()):
        subset = pred[(pred['scenario'] == scenario) & (pred['quarter'] == quarter)]
        total = subset['share'].sum()
        print(f"      {scenario} Q{quarter}: {total:.10f}")

# Check matrices
matrices = pd.read_csv('matrices.csv')
print("\n2. MATRICES.CSV")
print(f"   Shape: {matrices.shape}")
print(f"   Columns: {matrices.columns.tolist()}")

# Count rows by type
print("\n   Rows by scenario:")
for scenario in sorted(matrices['scenario'].unique()):
    count = len(matrices[matrices['scenario'] == scenario])
    print(f"      {scenario}: {count} rows")

# Verify a few rows sum to 1
prob_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
print("\n   Sample row verification (should sum to 1.0):")
for idx in [0, 50, 100, 200, 300]:
    if idx < len(matrices):
        row = matrices.iloc[idx]
        total = row[prob_cols].sum()
        print(f"      Row {idx} ({row['scenario']} Q{row['quarter']} {row['from_rating']}): {total:.10f}")

# Check backtest
backtest = pd.read_csv('backtest.csv')
print("\n3. BACKTEST.CSV")
print(f"   Shape: {backtest.shape} (expected: 60 rows, 3 cols)")
print(f"   Columns: {backtest.columns.tolist()}")
print(f"   Scenarios: {sorted(backtest['scenario'].unique())}")
print(f"   Years: {sorted(backtest['year'].unique())}")
print(f"   Sample rows:")
print(backtest.head(5))

print("\n" + "="*70)
print("VERIFICATION COMPLETE - All files ready!")
print("="*70)
EOF

```

## [37] tool

Traceback (most recent call last):
  File "<stdin>", line 8, in <module>
  File "/usr/local/lib/python3.12/site-packages/pandas/io/parsers/readers.py", line 873, in read_csv
    return _read(filepath_or_buffer, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/io/parsers/readers.py", line 1645, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/io/parsers/readers.py", line 1904, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'predictions.csv'

======================================================================
VERIFYING OUTPUT FILES
======================================================================


## [38] assistant

The files are in the working directory. Let me check there:

**tool call: bash**

```
ls -lh *.csv && echo "---" && python3 << 'EOF'
import pandas as pd

print("="*70)
print("VERIFYING OUTPUT FILES")
print("="*70)

# Check predictions
pred = pd.read_csv('predictions.csv')
print("\n1. PREDICTIONS.CSV")
print(f"   Shape: {pred.shape} (expected: 48 rows, 4 cols)")
print(f"   Columns: {pred.columns.tolist()}")
print(f"   Scenarios: {sorted(pred['scenario'].unique())}")
print(f"   Quarters: {sorted(pred['quarter'].unique())}")
print(f"   States: {sorted(pred['state'].unique())}")

# Verify sums to 1
print("\n   Verification - sum by scenario and quarter:")
for scenario in sorted(pred['scenario'].unique()):
    for quarter in sorted(pred['quarter'].unique()):
        subset = pred[(pred['scenario'] == scenario) & (pred['quarter'] == quarter)]
        total = subset['share'].sum()
        print(f"      {scenario} Q{quarter}: {total:.10f}")

# Check matrices
matrices = pd.read_csv('matrices.csv')
print("\n2. MATRICES.CSV")
print(f"   Shape: {matrices.shape}")
print(f"   Columns: {matrices.columns.tolist()}")

# Count rows by type
print("\n   Rows by scenario:")
for scenario in sorted(matrices['scenario'].unique()):
    count = len(matrices[matrices['scenario'] == scenario])
    print(f"      {scenario}: {count} rows")

# Verify a few rows sum to 1
prob_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
print("\n   Sample row verification (should sum to 1.0):")
for idx in [0, 50, 100, 200, 300]:
    if idx < len(matrices):
        row = matrices.iloc[idx]
        total = row[prob_cols].sum()
        print(f"      Row {idx} ({row['scenario']} Q{row['quarter']} {row['from_rating']}): {total:.10f}")

# Check backtest
backtest = pd.read_csv('backtest.csv')
print("\n3. BACKTEST.CSV")
print(f"   Shape: {backtest.shape} (expected: 60 rows, 3 cols)")
print(f"   Columns: {backtest.columns.tolist()}")
print(f"   Scenarios: {sorted(backtest['scenario'].unique())}")
print(f"   Years: {sorted(backtest['year'].unique())}")
print(f"   Sample rows:")
print(backtest.head(5))

print("\n" + "="*70)
print("VERIFICATION COMPLETE - All files ready!")
print("="*70)
EOF

```

## [39] tool

-rw-r--r-- 1 root root 1.8K Oct 22 22:55 backtest.csv
-rw-r--r-- 1 root root  46K Oct 22 22:55 matrices.csv
-rw-r--r-- 1 root root 1.7K Oct 22 22:55 predictions.csv
---
======================================================================
VERIFYING OUTPUT FILES
======================================================================

1. PREDICTIONS.CSV
   Shape: (48, 4) (expected: 48 rows, 4 cols)
   Columns: ['scenario', 'quarter', 'state', 'share']
   Scenarios: ['adverse', 'baseline', 'severe']
   Quarters: [np.int64(4), np.int64(9)]
   States: ['A', 'AA', 'AAA', 'B', 'BB', 'BBB', 'CCC/C', 'D']

   Verification - sum by scenario and quarter:
      adverse Q4: 1.0000000000
      adverse Q9: 1.0000000000
      baseline Q4: 1.0000000000
      baseline Q9: 1.0000000000
      severe Q4: 1.0000000000
      severe Q9: 1.0000000000

2. MATRICES.CSV
   Shape: (329, 11)
   Columns: ['scenario', 'quarter', 'from_rating', 'to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

   Rows by scenario:
      adverse: 63 rows
      baseline: 63 rows
      history: 140 rows
      severe: 63 rows

   Sample row verification (should sum to 1.0):
      Row 0 (adverse Q1 AAA): 1.0000000000
      Row 50 (adverse Q8 AA): 1.0000000000
      Row 100 (baseline Q6 A): 1.0000000000
      Row 200 (history Q-72 BB): 1.0000000000
      Row 300 (history Q-16 CCC/C): 1.0000000000

3. BACKTEST.CSV
   Shape: (60, 3) (expected: 60 rows, 3 cols)
   Columns: ['scenario', 'year', 'default_rate']
   Scenarios: ['adverse', 'baseline', 'severe']
   Years: [np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5), np.int64(6), np.int64(7), np.int64(8), np.int64(9), np.int64(10), np.int64(11), np.int64(12), np.int64(13), np.int64(14), np.int64(15), np.int64(16), np.int64(17), np.int64(18), np.int64(19), np.int64(20)]
   Sample rows:
   scenario  year  default_rate
0   adverse     1      0.686554
1  baseline     1      0.686554
2    severe     1      0.686554
3   adverse     2      0.711337
4  baseline     2      0.711337

======================================================================
VERIFICATION COMPLETE - All files ready!
======================================================================


## [40] assistant

Perfect! All files are correct. Let me examine some of the predictions to make sure they look reasonable:

**tool call: bash**

```
python3 << 'EOF'
import pandas as pd

pred = pd.read_csv('predictions.csv')

print("="*70)
print("PREDICTIONS SUMMARY")
print("="*70)

# Show each scenario's predictions
for scenario in sorted(pred['scenario'].unique()):
    scenario_data = pred[pred['scenario'] == scenario]
    
    print(f"\n{scenario.upper()}")
    print("-" * 70)
    
    for quarter in sorted(scenario_data['quarter'].unique()):
        q_data = scenario_data[scenario_data['quarter'] == quarter]
        print(f"\n  Quarter {quarter}:")
        
        # Show non-default states
        for state in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']:
            share = q_data[q_data['state'] == state]['share'].values
            if len(share) > 0:
                pct = share[0] * 100
                print(f"    {state:8s}: {pct:7.2f}%")
        
        # Show default
        d_share = q_data[q_data['state'] == 'D']['share'].values[0]
        d_pct = d_share * 100
        print(f"    {'D':8s}: {d_pct:7.2f}%")
        
        # Sum check
        total = q_data['share'].sum()
        print(f"    {'TOTAL':8s}: {total*100:7.2f}%")

print("\n" + "="*70)
print("Key observations:")
print("="*70)

# Compare scenarios at Q9
q9_data = pred[pred['quarter'] == 9]

print("\nDefault rates at Quarter 9:")
for scenario in sorted(q9_data['scenario'].unique()):
    d_rate = q9_data[(q9_data['scenario'] == scenario) & (q9_data['state'] == 'D')]['share'].values[0]
    print(f"  {scenario:10s}: {d_rate*100:.2f}%")

# Rating distribution at Q4 for baseline
q4_baseline = pred[(pred['scenario'] == 'baseline') & (pred['quarter'] == 4)]
remaining = q4_baseline[q4_baseline['state'] != 'D']['share'].sum()
print(f"\nBaseline Q4: {remaining*100:.2f}% still in ratings (not defaulted)")

EOF

```

## [41] tool

======================================================================
PREDICTIONS SUMMARY
======================================================================

ADVERSE
----------------------------------------------------------------------

  Quarter 4:
    AAA     :    0.23%
    AA      :    0.79%
    A       :    1.20%
    BBB     :    2.14%
    BB      :    2.11%
    B       :   10.08%
    CCC/C   :    2.21%
    D       :   81.24%
    TOTAL   :  100.00%

  Quarter 9:
    AAA     :    0.11%
    AA      :    0.19%
    A       :    0.10%
    BBB     :    0.11%
    BB      :    0.56%
    B       :    5.43%
    CCC/C   :    1.14%
    D       :   92.34%
    TOTAL   :  100.00%

BASELINE
----------------------------------------------------------------------

  Quarter 4:
    AAA     :    0.29%
    AA      :    1.21%
    A       :    1.45%
    BBB     :    2.26%
    BB      :    2.36%
    B       :    9.90%
    CCC/C   :    1.69%
    D       :   80.84%
    TOTAL   :  100.00%

  Quarter 9:
    AAA     :    0.15%
    AA      :    0.42%
    A       :    0.17%
    BBB     :    0.12%
    BB      :    0.51%
    B       :    5.40%
    CCC/C   :    1.09%
    D       :   92.14%
    TOTAL   :  100.00%

SEVERE
----------------------------------------------------------------------

  Quarter 4:
    AAA     :    0.20%
    AA      :    0.55%
    A       :    1.06%
    BBB     :    2.07%
    BB      :    1.89%
    B       :   10.10%
    CCC/C   :    2.60%
    D       :   81.52%
    TOTAL   :  100.00%

  Quarter 9:
    AAA     :    0.07%
    AA      :    0.08%
    A       :    0.07%
    BBB     :    0.10%
    BB      :    0.49%
    B       :    5.28%
    CCC/C   :    1.30%
    D       :   92.60%
    TOTAL   :  100.00%

======================================================================
Key observations:
======================================================================

Default rates at Quarter 9:
  adverse   : 92.34%
  baseline  : 92.14%
  severe    : 92.60%

Baseline Q4: 19.16% still in ratings (not defaulted)


## [42] assistant

The predictions show very high default rates (80-93%), which seems extreme. Let me check the historical data to understand if this is reasonable:

**tool call: bash**

```
python3 << 'EOF'
import pandas as pd
import numpy as np

transitions = pd.read_csv('data/transitions.csv')
portfolio = pd.read_csv('data/portfolio.csv')

# Analyze historical defaults
print("="*70)
print("HISTORICAL ANALYSIS")
print("="*70)

# Portfolio composition
print("\nInitial Portfolio:")
total = portfolio['obligors'].sum()
for _, row in portfolio.iterrows():
    pct = row['obligors'] / total * 100
    print(f"  {row['rating']:8s}: {row['obligors']:5d} ({pct:6.2f}%)")
print(f"  {'Total':8s}: {total:5d} (100.00%)")

# Historical annual defaults by rating
print("\nHistorical Annual Default Rates by Rating:")
for rating in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']:
    subset = transitions[transitions['from_rating'] == rating]
    total_obligors = subset[['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']].sum().sum()
    total_defaults = subset['to_D'].sum()
    if total_obligors > 0:
        rate = total_defaults / total_obligors
        print(f"  {rating:8s}: {rate:8.4f} ({total_defaults:5d}/{total_obligors:5d})")

# Historical portfolio-level annual default rate
total_obligors_all = transitions[['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']].sum().sum()
total_defaults_all = transitions['to_D'].sum()
overall_rate = total_defaults_all / total_obligors_all
print(f"\nHistorical Overall Annual Default Rate: {overall_rate:.4f}")

# What's the composition of historical portfolio?
print("\nHistorical Portfolio Composition (average):")
for rating in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']:
    subset = transitions[transitions['from_rating'] == rating]
    obligors = subset[['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']].sum().sum()
    pct = obligors / total_obligors_all * 100
    print(f"  {rating:8s}: {obligors:7.0f} ({pct:6.2f}%)")

# The projection cohort has lots of B and CCC/C grades
# Let me check if 9 quarters (2.25 years) of 80%+ defaults makes sense

# If annual rate for CCC/C is 0.32, what's quarterly?
# Roughly, if we assume it's constant: (1-0.32)^(1/4) = 0.78^0.25 = 0.939
# So ~6% survival per quarter, or ~94% default per quarter??
# That seems wrong. Let me recalculate.

# Actually, the annual rate of 0.32 means 32% default rate in one year
# For quarterly, roughly: 1 - (1-0.32)^(1/4) = 1 - 0.68^0.25 ≈ 1 - 0.908 = 0.092 ≈ 9%
# So about 9% default per quarter for CCC/C if rates stay constant

print("\n" + "="*70)
print("QUARTERLY DEFAULT ESTIMATE (assuming constant annual rates):")
print("="*70)

for rating in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']:
    subset = transitions[transitions['from_rating'] == rating]
    total_obligors = subset[['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']].sum().sum()
    total_defaults = subset['to_D'].sum()
    if total_obligors > 0:
        annual_rate = total_defaults / total_obligors
        # Quarterly rate assuming constant: 1 - (1-r)^(1/4)
        quarterly_rate = 1 - (1 - annual_rate) ** (0.25)
        # After 9 quarters (4 years): (1-q)^9
        survivor_rate_9q = (1 - quarterly_rate) ** 9
        default_rate_9q = 1 - survivor_rate_9q
        print(f"  {rating:8s}: annual={annual_rate:.4f}, quarterly≈{quarterly_rate:.4f}, default_9q={default_rate_9q:.4f}")

# Portfolio weighted average
portfolio_set = set(portfolio['rating'].values)
print(f"\nPortfolio ratings: {sorted(portfolio_set)}")

# Calculate expected 9-quarter default rate for this portfolio
total_expected_defaults = 0
total_obligors = 0
for _, p_row in portfolio.iterrows():
    rating = p_row['rating']
    obligors = p_row['obligors']
    
    # Get historical rate for this rating
    subset = transitions[transitions['from_rating'] == rating]
    hist_obligors = subset[['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']].sum().sum()
    hist_defaults = subset['to_D'].sum()
    
    if hist_obligors > 0:
        annual_rate = hist_defaults / hist_obligors
        quarterly_rate = 1 - (1 - annual_rate) ** (0.25)
        default_rate_9q = 1 - (1 - quarterly_rate) ** 9
        
        expected_defaults = obligors * default_rate_9q
        total_expected_defaults += expected_defaults
        total_obligors += obligors
        
        print(f"  {rating}: {obligors} obligors × {default_rate_9q:.4f} = {expected_defaults:.1f}")

expected_rate = total_expected_defaults / total_obligors
print(f"\nExpected portfolio default rate over 9 quarters: {expected_rate:.4f} ({expected_rate*100:.2f}%)")

EOF

```

## [43] tool

======================================================================
HISTORICAL ANALYSIS
======================================================================

Initial Portfolio:
  AAA     :    44 (  0.44%)
  AA      :   227 (  2.27%)
  A       :  1450 ( 14.50%)
  BBB     :  3662 ( 36.62%)
  BB      :  2963 ( 29.63%)
  B       :  1363 ( 13.63%)
  CCC/C   :   290 (  2.90%)
  Total   :  9999 (100.00%)

Historical Annual Default Rates by Rating:
  AAA     :   0.0000 (    0/ 1309)
  AA      :   0.0002 (    2/ 9543)
  A       :   0.0007 (   32/44866)
  BBB     :   0.0022 (  167/74799)
  BB      :   0.0078 (  317/40463)
  B       :   0.0359 (  915/25515)
  CCC/C   :   0.3201 ( 1122/ 3505)

Historical Overall Annual Default Rate: 0.0128

Historical Portfolio Composition (average):
  AAA     :    1309 (  0.65%)
  AA      :    9543 (  4.77%)
  A       :   44866 ( 22.43%)
  BBB     :   74799 ( 37.40%)
  BB      :   40463 ( 20.23%)
  B       :   25515 ( 12.76%)
  CCC/C   :    3505 (  1.75%)

======================================================================
QUARTERLY DEFAULT ESTIMATE (assuming constant annual rates):
======================================================================
  AAA     : annual=0.0000, quarterly≈0.0000, default_9q=0.0000
  AA      : annual=0.0002, quarterly≈0.0001, default_9q=0.0005
  A       : annual=0.0007, quarterly≈0.0002, default_9q=0.0016
  BBB     : annual=0.0022, quarterly≈0.0006, default_9q=0.0050
  BB      : annual=0.0078, quarterly≈0.0020, default_9q=0.0175
  B       : annual=0.0359, quarterly≈0.0091, default_9q=0.0789
  CCC/C   : annual=0.3201, quarterly≈0.0920, default_9q=0.5803

Portfolio ratings: ['A', 'AA', 'AAA', 'B', 'BB', 'BBB', 'CCC/C']
  AAA: 44 obligors × 0.0000 = 0.0
  AA: 227 obligors × 0.0005 = 0.1
  A: 1450 obligors × 0.0016 = 2.3
  BBB: 3662 obligors × 0.0050 = 18.4
  BB: 2963 obligors × 0.0175 = 52.0
  B: 1363 obligors × 0.0789 = 107.5
  CCC/C: 290 obligors × 0.5803 = 168.3

Expected portfolio default rate over 9 quarters: 0.0349 (3.49%)


## [44] assistant

I see a major issue! My model is predicting way too high default rates. The simple constant-rate extrapolation suggests ~3.5% over 9 quarters, but my model predicts 92%+. The issue is that I'm using the same transition matrix for all 4 quarters of the year, which means I'm accumulating defaults incorrectly.

Let me reconsider my approach. The problem is:
1. I fit the model using ANNUAL transitions
2. But I need to model QUARTERLY transitions
3. My current approach is inferring quarterly rates from annual data, but defaulting should not be cumulative in the same way

Let me rethink this. For CCC/C with 32% annual default rate, if I model this as 4 identical quarters, I get (1-0.32)^(1/4) = 0.909 survival per quarter, meaning ~9.1% quarterly default. But applying this 9 times gives 1-(0.909)^9 = 58%, which is closer to the simple calculation above.

Wait, let me trace through my code... The issue is I'm not handling defaults correctly. Once an obligor defaults, they should stay in D. Let me check my implementation:

Actually, looking at my code, I AM accumulating defaults correctly:
```python
cumulative_defaults += quarterly_defaults
...
cumulative_defaults / total_initial
```

So the issue must be with the model itself. Let me examine what transition probabilities the model is predicting:

**tool call: bash**

```
python3 << 'EOF'
import pandas as pd

matrices = pd.read_csv('matrices.csv')

print("="*70)
print("MODEL PREDICTED TRANSITION MATRICES - SAMPLE")
print("="*70)

# Show Q1 for baseline
baseline_q1 = matrices[(matrices['scenario'] == 'baseline') & (matrices['quarter'] == 1)]

print("\nBaseline Quarter 1:")
print(baseline_q1[['from_rating', 'to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']])

# Compare with historical
history = matrices[matrices['scenario'] == 'history'].iloc[-7:]  # Last 7 rows (Q0, last rating)
print("\nHistory Quarter 0 (most recent):")
print(history[['from_rating', 'to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']])

# Check Q9 for baseline
baseline_q9 = matrices[(matrices['scenario'] == 'baseline') & (matrices['quarter'] == 9)]
print("\nBaseline Quarter 9:")
print(baseline_q9[['from_rating', 'to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']])

# Look at default rates specifically
print("\n" + "="*70)
print("DEFAULT RATES (to_D) OVER TIME")
print("="*70)

for scenario in ['baseline']:
    print(f"\n{scenario}:")
    for rating in ['BBB', 'BB', 'B', 'CCC/C']:
        rates = []
        for quarter in range(1, 10):
            subset = matrices[(matrices['scenario'] == scenario) & 
                            (matrices['quarter'] == quarter) & 
                            (matrices['from_rating'] == rating)]
            if len(subset) > 0:
                rate = subset['to_D'].values[0]
                rates.append(rate)
        
        if rates:
            print(f"  {rating}: {rates}")
            # Compute cumulative default over quarters
            survivor = 1.0
            for r in rates:
                survivor *= (1 - r)
            cumulative_default = 1 - survivor
            print(f"    -> 9-quarter cumulative: {cumulative_default:.4f}")

EOF

```

## [45] tool

======================================================================
MODEL PREDICTED TRANSITION MATRICES - SAMPLE
======================================================================

Baseline Quarter 1:
   from_rating    to_AAA     to_AA  ...      to_B  to_CCC_C      to_D
63         AAA  0.866670  0.115094  ...  0.000000  0.001783  0.000000
64          AA  0.002688  0.771197  ...  0.000115  0.000216  0.137960
65           A  0.000000  0.006273  ...  0.001101  0.000115  0.465930
66         BBB  0.000000  0.000247  ...  0.003358  0.000763  0.500763
67          BB  0.000040  0.000209  ...  0.036475  0.003064  0.502388
68           B  0.000000  0.000080  ...  0.855918  0.063782  0.036872
69       CCC/C  0.000000  0.000000  ...  0.129296  0.560712  0.306840

[7 rows x 9 columns]

History Quarter 0 (most recent):
    from_rating    to_AAA     to_AA  ...      to_B  to_CCC_C      to_D
322         AAA  0.865385  0.134615  ...  0.000000  0.000000  0.000000
323          AA  0.000000  0.869347  ...  0.000000  0.000000  0.000000
324           A  0.000000  0.003754  ...  0.002628  0.000000  0.000751
325         BBB  0.000000  0.000277  ...  0.008599  0.001110  0.003606
326          BB  0.000000  0.000000  ...  0.096275  0.006304  0.010888
327           B  0.000000  0.000000  ...  0.826012  0.103359  0.053402
328       CCC/C  0.000000  0.000000  ...  0.073864  0.556818  0.369318

[7 rows x 9 columns]

Baseline Quarter 9:
    from_rating    to_AAA     to_AA  ...      to_B  to_CCC_C      to_D
119         AAA  0.855083  0.124587  ...  0.000000  0.001715  0.000000
120          AA  0.002000  0.743876  ...  0.000144  0.000260  0.160780
121           A  0.000000  0.005246  ...  0.001235  0.000138  0.475150
122         BBB  0.000000  0.000157  ...  0.003806  0.000885  0.500887
123          BB  0.000022  0.000201  ...  0.039334  0.003418  0.502747
124           B  0.000000  0.000032  ...  0.855574  0.068485  0.037057
125       CCC/C  0.000000  0.000000  ...  0.119997  0.566807  0.310731

[7 rows x 9 columns]

======================================================================
DEFAULT RATES (to_D) OVER TIME
======================================================================

baseline:
  BBB: [np.float64(0.5007625038653333), np.float64(0.500570326911385), np.float64(0.5003958467575916), np.float64(0.5004751735447716), np.float64(0.5005553228335528), np.float64(0.5006363904872321), np.float64(0.5007185039721317), np.float64(0.5008018605051064), np.float64(0.5008865979031956)]
    -> 9-quarter cumulative: 0.9981
  BB: [np.float64(0.502387828132876), np.float64(0.5017852199133009), np.float64(0.5012479924143446), np.float64(0.5014990106738041), np.float64(0.5017487958947618), np.float64(0.5019977246881345), np.float64(0.5022463913111902), np.float64(0.5024957211462859), np.float64(0.5027465475030363)]
    -> 9-quarter cumulative: 0.9981
  B: [np.float64(0.036872492672335), np.float64(0.0366170319785059), np.float64(0.0363895054027514), np.float64(0.0364973367675464), np.float64(0.0366063161154565), np.float64(0.0367165759996934), np.float64(0.0368282985342894), np.float64(0.0369417641341781), np.float64(0.0370571812321901)]
    -> 9-quarter cumulative: 0.2859
  CCC/C: [np.float64(0.3068400166183857), np.float64(0.2989060419394029), np.float64(0.2922934404317649), np.float64(0.2953862044797068), np.float64(0.298460905374626), np.float64(0.3015221401613688), np.float64(0.3045819574087199), np.float64(0.307648531086321), np.float64(0.3107313040122991)]
    -> 9-quarter cumulative: 0.9606


## [46] assistant

Aha! There's the problem! The model is predicting ~50% quarterly default rates for BBB and BB grades, which is WAY too high! The historical annual default rate for BBB is only 0.22%, which should be ~0.06% per quarter, not 50%!

The issue is in how I'm estimating the quarterly model from annual data. When I average the macro conditions over a year, I'm losing information about how conditions change within the year. More importantly, I'm fitting directly to annual *counts* but treating them as quarterly rates.

The core issue: I need to recognize that the transition counts are ANNUAL aggregates. To get quarterly rates, I can't just divide the annual rate by 4 - that would be overly simplistic. Instead, I should either:
1. Assume stationary quarterly rates and decompose the annual into 4 equal quarterly rates (geometric)
2. Model the relationship between macro variables and the ANNUAL default rate, then assume quarterly rate is constant within the year

Let me implement approach 2, which is more sound:

**tool call: bash**

```
cat > /tmp/full_model_v2.py << 'EOF'
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import PolynomialFeatures
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# LOAD DATA
# ============================================================================
transitions = pd.read_csv('data/transitions.csv')
macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')
portfolio = pd.read_csv('data/portfolio.csv')

with open('data/policy.json', 'r') as f:
    policy = json.load(f)

ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']
states = ratings + ['D']
to_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']

# ============================================================================
# BUILD TRAINING DATA - Annual Level
# ============================================================================

years = sorted(transitions['year'].unique())

year_to_end_quarter = {}
for year in years:
    end_quarter = 0 - (20 - year) * 4
    year_to_end_quarter[year] = end_quarter

training_data = []

for year in years:
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_trans = transitions[transitions['year'] == year]
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            row_dict = {
                'year': year,
                'from_rating': from_rating,
                'total': total,
                'end_q': end_q,
            }
            for col in to_cols:
                row_dict[col] = trans_row[col]
                row_dict[f'{col}_rate'] = trans_row[col] / total
            for col in macro_cols:
                row_dict[col] = macro_avg[col]
            
            training_data.append(row_dict)

training_df = pd.DataFrame(training_data)

print("Training data loaded")
print(f"  Rows: {len(training_df)}")

# ============================================================================
# FIT MODEL TO ANNUAL DEFAULT RATES
# ============================================================================

macro_features = ['gdp', 'unemployment', 'nasdaq', 'cpi']

# Standardize
scaler = StandardScaler()
training_df_scaled = training_df.copy()
training_df_scaled[macro_features] = scaler.fit_transform(training_df[macro_features])

scaler_means = training_df[macro_features].mean().to_dict()
scaler_stds = training_df[macro_features].std().to_dict()

# For each rating, fit models for:
# 1. Annual default probability
# 2. Migration proportions (non-default)

models = {}

for rating in ratings:
    subset = training_df_scaled[training_df_scaled['from_rating'] == rating].copy()
    
    if len(subset) == 0:
        continue
    
    models[rating] = {}
    X = subset[macro_features].values
    
    # Model 1: Annual default rate
    y_default = subset['to_D_rate'].values
    
    model_default = Ridge(alpha=1.0)
    model_default.fit(X, y_default)
    models[rating]['default'] = model_default
    
    # Model 2: For each non-default destination, given no default occurs
    # Calculate conditional migration probabilities
    
    non_default_cols = [col for col in to_cols if col != 'to_D']
    
    for to_state in non_default_cols:
        # Conditional probability: P(go to this state | don't default)
        y_migration = (subset[f'{to_state}_rate'] / (1 - subset['to_D_rate'])).fillna(0).clip(0, 1)
        
        model_mig = Ridge(alpha=1.0)
        model_mig.fit(X, y_migration)
        models[rating][to_state] = model_mig

print(f"Fitted models for {len(models)} ratings")

# ============================================================================
# PREPARE SCENARIOS
# ============================================================================

scenario_macro_data = {}
scenarios_list = sorted(scenario_data['scenario'].unique())

for scenario in scenarios_list:
    scenario_macro_data[scenario] = scenario_data[scenario_data['scenario'] == scenario].copy()
    scenario_macro_data[scenario].set_index('quarter', inplace=True)

print(f"Loaded {len(scenarios_list)} scenarios")

# ============================================================================
# PREDICTION FUNCTION
# ============================================================================

def predict_quarterly_transitions(macro_values_dict, models, scaler_means, scaler_stds, macro_features):
    """
    Predict quarterly transition matrix from annual model
    Strategy: Model predicts ANNUAL rates. Convert to quarterly assuming
    stationary quarterly rates within the year.
    
    If annual default rate is r_a, then quarterly is:
    r_q = 1 - (1 - r_a)^(1/4)
    """
    
    macro_array = np.array([macro_values_dict[f] for f in macro_features]).reshape(1, -1)
    macro_scaled = (macro_array - np.array([scaler_means[f] for f in macro_features])) / \
                   np.array([scaler_stds[f] for f in macro_features])
    
    transitions_pred = {}
    
    for from_rating in models:
        transitions_pred[from_rating] = {}
        X_test = macro_scaled
        
        # Predict annual default rate
        annual_default_prob = models[from_rating]['default'].predict(X_test)[0]
        annual_default_prob = np.clip(annual_default_prob, 0, 0.99)
        
        # Convert to quarterly: assuming geometric/stationary quarterly rates
        # If annual survival is (1-r_a), then quarterly survival is (1-r_a)^(1/4)
        # So quarterly default is 1 - (1-r_a)^(1/4)
        quarterly_default_prob = 1 - (1 - annual_default_prob) ** (0.25)
        
        # Predict migration probabilities (conditional on not defaulting)
        non_default_cols = [col for col in to_cols if col != 'to_D']
        
        migration_probs = {}
        for to_state in non_default_cols:
            pred = models[from_rating][to_state].predict(X_test)[0]
            migration_probs[to_state] = np.clip(pred, 0, 1)
        
        # Normalize migration probabilities to sum to 1
        total_migration = sum(migration_probs.values())
        if total_migration > 0:
            for to_state in migration_probs:
                migration_probs[to_state] /= total_migration
        else:
            # Fallback: equal distribution
            for to_state in non_default_cols:
                migration_probs[to_state] = 1.0 / len(non_default_cols)
        
        # Final quarterly transition probabilities
        probs = {}
        for to_state in non_default_cols:
            probs[to_state] = migration_probs[to_state] * (1 - quarterly_default_prob)
        probs['to_D'] = quarterly_default_prob
        
        transitions_pred[from_rating] = probs
    
    return transitions_pred

# ============================================================================
# PROJECT COHORT
# ============================================================================

initial_cohort = {}
for _, row in portfolio.iterrows():
    initial_cohort[row['rating']] = row['obligors']

total_initial = sum(initial_cohort.values())

checkpoints = policy['checkpoints']
predictions_list = []
matrices_list = []

for scenario in scenarios_list:
    print(f"\nProjecting {scenario}...")
    
    current_cohort = {r: initial_cohort.get(r, 0) for r in ratings}
    cumulative_defaults = 0
    
    for quarter in range(1, 10):
        # Get macro for this quarter
        if quarter in scenario_macro_data[scenario].index:
            macro_q = scenario_macro_data[scenario].loc[quarter]
            macro_dict = {f: macro_q[f] for f in macro_features}
        else:
            continue
        
        # Predict transitions
        trans_matrix = predict_quarterly_transitions(macro_dict, models, 
                                                      scaler_means, scaler_stds, macro_features)
        
        # Record matrix for this quarter
        for from_rating in ratings:
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                row_dict = {
                    'scenario': scenario,
                    'quarter': quarter,
                    'from_rating': from_rating,
                    'to_AAA': trans_probs.get('to_AAA', 0.0),
                    'to_AA': trans_probs.get('to_AA', 0.0),
                    'to_A': trans_probs.get('to_A', 0.0),
                    'to_BBB': trans_probs.get('to_BBB', 0.0),
                    'to_BB': trans_probs.get('to_BB', 0.0),
                    'to_B': trans_probs.get('to_B', 0.0),
                    'to_CCC_C': trans_probs.get('to_CCC_C', 0.0),
                    'to_D': trans_probs.get('to_D', 0.0),
                }
                
                matrices_list.append(row_dict)
        
        # Apply transitions to cohort
        new_cohort = {r: 0.0 for r in ratings}
        quarterly_defaults = 0
        
        for from_rating in ratings:
            if current_cohort[from_rating] == 0:
                continue
            
            cohort_size = current_cohort[from_rating]
            
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                
                for to_state in to_cols:
                    prob = trans_probs.get(to_state, 0.0)
                    count = cohort_size * prob
                    
                    if to_state == 'to_D':
                        quarterly_defaults += count
                    else:
                        to_rating = to_state.replace('to_', '')
                        if to_rating == 'CCC_C':
                            to_rating = 'CCC/C'
                        new_cohort[to_rating] += count
        
        cumulative_defaults += quarterly_defaults
        current_cohort = new_cohort
        
        # Record at checkpoints
        if quarter in checkpoints:
            for rating in ratings:
                count = current_cohort.get(rating, 0)
                share = count / total_initial
                predictions_list.append({
                    'scenario': scenario,
                    'quarter': quarter,
                    'state': rating,
                    'share': share
                })
            
            default_share = cumulative_defaults / total_initial
            predictions_list.append({
                'scenario': scenario,
                'quarter': quarter,
                'state': 'D',
                'share': default_share
            })

# ============================================================================
# OUTPUT PREDICTIONS
# ============================================================================

predictions_df = pd.DataFrame(predictions_list)
predictions_df.to_csv('predictions.csv', index=False)

print(f"\nWrote predictions.csv: {len(predictions_df)} rows")

# ============================================================================
# OUTPUT MATRICES
# ============================================================================

matrices_df = pd.DataFrame(matrices_list)

# Also add historical matrices
history_matrices_list = []

for year in sorted(years):
    year_trans = transitions[transitions['year'] == year]
    
    # Calculate annual transition probabilities
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        total = trans_row[to_cols].sum()
        
        if total > 0:
            annual_rates = {}
            for to_state in to_cols:
                annual_rates[to_state] = trans_row[to_state] / total
            
            # Convert annual to quarterly
            end_q = year_to_end_quarter[year]
            
            annual_default_prob = annual_rates['to_D']
            quarterly_default_prob = 1 - (1 - annual_default_prob) ** (0.25)
            
            # Non-default rates stay as fractions of survivors
            quarterly_rates = {}
            for to_state in non_default_cols:
                # This is P(go to this state | survive)
                survival_prob = 1 - annual_default_prob
                if survival_prob > 0:
                    quarterly_rates[to_state] = annual_rates[to_state] / survival_prob
                else:
                    quarterly_rates[to_state] = 0
            quarterly_rates['to_D'] = quarterly_default_prob
            
            # Hmm, this doesn't work for history because we're recording
            # the annual transition, not quarterly. Let me record the annual directly.
            
            row_dict = {
                'scenario': 'history',
                'quarter': end_q,
                'from_rating': from_rating,
                'to_AAA': annual_rates['to_AAA'],
                'to_AA': annual_rates['to_AA'],
                'to_A': annual_rates['to_A'],
                'to_BBB': annual_rates['to_BBB'],
                'to_BB': annual_rates['to_BB'],
                'to_B': annual_rates['to_B'],
                'to_CCC_C': annual_rates['to_CCC_C'],
                'to_D': annual_rates['to_D'],
            }
            
            history_matrices_list.append(row_dict)

history_matrices_df = pd.DataFrame(history_matrices_list)

# Combine
all_matrices = pd.concat([matrices_df, history_matrices_df], ignore_index=True)
all_matrices.to_csv('matrices.csv', index=False)

print(f"Wrote matrices.csv: {len(all_matrices)} rows")

# ============================================================================
# OUTPUT BACKTEST
# ============================================================================

backtest_list = []

for year in sorted(years):
    year_trans = transitions[transitions['year'] == year]
    
    # Total obligors in this year (sum of row totals)
    total_obligors_year = year_trans[to_cols].sum().sum()
    
    # Now predict using the model for this year
    end_q = year_to_end_quarter[year]
    start_q = end_q - 3
    
    year_macro = macro_history[(macro_history['quarter'] >= start_q) & 
                                (macro_history['quarter'] <= end_q)]
    
    macro_cols = [c for c in year_macro.columns if c != 'quarter']
    macro_avg = year_macro[macro_cols].mean()
    macro_dict = {f: macro_avg[f] for f in macro_features}
    
    # Get transition matrix for this quarter (use end quarter macro)
    trans_matrix = predict_quarterly_transitions(macro_dict, models, 
                                                  scaler_means, scaler_stds, macro_features)
    
    # Calculate model's predicted annual default rate
    # For this, use the year-starting cohort and 4 quarterly transitions
    model_cohort = {r: 0 for r in ratings}
    
    for _, trans_row in year_trans.iterrows():
        from_rating = trans_row['from_rating']
        cohort_count = trans_row[to_cols].sum()
        if cohort_count > 0:
            model_cohort[from_rating] = cohort_count
    
    # Apply 4 quarterly transitions
    cumulative_defaults_model = 0
    for q in range(4):
        new_cohort = {r: 0.0 for r in ratings}
        
        for from_rating in ratings:
            if model_cohort[from_rating] == 0:
                continue
            
            cohort_size = model_cohort[from_rating]
            
            if from_rating in trans_matrix:
                trans_probs = trans_matrix[from_rating]
                
                for to_state in to_cols:
                    prob = trans_probs.get(to_state, 0.0)
                    count = cohort_size * prob
                    
                    if to_state == 'to_D':
                        cumulative_defaults_model += count
                    else:
                        to_rating = to_state.replace('to_', '')
                        if to_rating == 'CCC_C':
                            to_rating = 'CCC/C'
                        new_cohort[to_rating] += count
        
        model_cohort = new_cohort
    
    model_default_rate = cumulative_defaults_model / total_obligors_year if total_obligors_year > 0 else 0
    
    # Add to backtest for all three scenarios (same model)
    for scenario in scenarios_list:
        backtest_list.append({
            'scenario': scenario,
            'year': year,
            'default_rate': model_default_rate
        })

backtest_df = pd.DataFrame(backtest_list)
backtest_df.to_csv('backtest.csv', index=False)

print(f"Wrote backtest.csv: {len(backtest_df)} rows")

print("\nDone!")
EOF
python /tmp/full_model_v2.py

```

## [47] tool

Training data loaded
  Rows: 140
Fitted models for 7 ratings
Loaded 3 scenarios

Projecting adverse...

Projecting baseline...

Projecting severe...

Wrote predictions.csv: 48 rows
Wrote matrices.csv: 329 rows
Wrote backtest.csv: 60 rows

Done!


## [48] assistant

Good! Now let me verify the new predictions are more reasonable:

**tool call: bash**

```
python3 << 'EOF'
import pandas as pd

pred = pd.read_csv('predictions.csv')

print("="*70)
print("PREDICTIONS SUMMARY - VERSION 2")
print("="*70)

# Show each scenario's predictions
for scenario in sorted(pred['scenario'].unique()):
    scenario_data = pred[pred['scenario'] == scenario]
    
    print(f"\n{scenario.upper()}")
    print("-" * 70)
    
    for quarter in sorted(scenario_data['quarter'].unique()):
        q_data = scenario_data[scenario_data['quarter'] == quarter]
        print(f"\n  Quarter {quarter}:")
        
        # Show non-default states
        for state in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC/C']:
            share = q_data[q_data['state'] == state]['share'].values
            if len(share) > 0:
                pct = share[0] * 100
                print(f"    {state:8s}: {pct:7.3f}%")
        
        # Show default
        d_share = q_data[q_data['state'] == 'D']['share'].values[0]
        d_pct = d_share * 100
        print(f"    {'D':8s}: {d_pct:7.3f}%")
        
        # Sum check
        total = q_data['share'].sum()
        print(f"    {'TOTAL':8s}: {total*100:7.3f}%")

print("\n" + "="*70)
print("Key observations:")
print("="*70)

# Compare scenarios at Q9
q9_data = pred[pred['quarter'] == 9]

print("\nDefault rates at Quarter 9:")
for scenario in sorted(q9_data['scenario'].unique()):
    d_rate = q9_data[(q9_data['scenario'] == scenario) & (q9_data['state'] == 'D')]['share'].values[0]
    print(f"  {scenario:10s}: {d_rate*100:.2f}%")

# Quarterly default rates from matrices
matrices = pd.read_csv('matrices.csv')

print("\nModel Predicted Quarterly Default Rates (Baseline Q1-Q9):")
for rating in ['BBB', 'BB', 'B', 'CCC/C']:
    baseline_q1 = matrices[(matrices['scenario'] == 'baseline') & 
                          (matrices['quarter'] == 1) & 
                          (matrices['from_rating'] == rating)]
    if len(baseline_q1) > 0:
        rate = baseline_q1['to_D'].values[0]
        print(f"  {rating}: {rate*100:.3f}%")

EOF

```

## [49] tool

======================================================================
PREDICTIONS SUMMARY - VERSION 2
======================================================================

ADVERSE
----------------------------------------------------------------------

  Quarter 4:
    AAA     :   0.241%
    AA      :   2.002%
    A       :  13.839%
    BBB     :  33.016%
    BB      :  23.928%
    B       :  18.813%
    CCC/C   :   5.216%
    D       :   2.945%
    TOTAL   : 100.000%

  Quarter 9:
    AAA     :   0.130%
    AA      :   1.863%
    A       :  13.209%
    BBB     :  29.058%
    BB      :  20.160%
    B       :  21.479%
    CCC/C   :   6.423%
    D       :   7.679%
    TOTAL   : 100.000%

BASELINE
----------------------------------------------------------------------

  Quarter 4:
    AAA     :   0.310%
    AA      :   2.537%
    A       :  15.911%
    BBB     :  34.453%
    BB      :  24.522%
    B       :  16.590%
    CCC/C   :   3.790%
    D       :   1.887%
    TOTAL   : 100.000%

  Quarter 9:
    AAA     :   0.188%
    AA      :   2.439%
    A       :  15.962%
    BBB     :  31.480%
    BB      :  20.812%
    B       :  18.817%
    CCC/C   :   5.227%
    D       :   5.075%
    TOTAL   : 100.000%

SEVERE
----------------------------------------------------------------------

  Quarter 4:
    AAA     :   0.205%
    AA      :   1.684%
    A       :  12.510%
    BBB     :  32.034%
    BB      :  23.464%
    B       :  20.153%
    CCC/C   :   6.226%
    D       :   3.724%
    TOTAL   : 100.000%

  Quarter 9:
    AAA     :   0.080%
    AA      :   1.235%
    A       :  10.200%
    BBB     :  26.315%
    BB      :  19.046%
    B       :  23.903%
    CCC/C   :   8.237%
    D       :  10.983%
    TOTAL   : 100.000%

======================================================================
Key observations:
======================================================================

Default rates at Quarter 9:
  adverse   : 7.68%
  baseline  : 5.08%
  severe    : 10.98%

Model Predicted Quarterly Default Rates (Baseline Q1-Q9):
  BBB: 0.076%
  BB: 0.238%
  B: 1.198%
  CCC/C: 8.414%


## [50] assistant

Much better! These predictions are now in a reasonable range. Let me double-check they match our simple calculation:

**tool call: bash**

```
python3 << 'EOF'
import pandas as pd
import numpy as np

transitions = pd.read_csv('data/transitions.csv')
portfolio = pd.read_csv('data/portfolio.csv')

print("Comparing model predictions to simple calculation:\n")

# For each rating, compare
for rating in ['BBB', 'BB', 'B', 'CCC/C']:
    subset = transitions[transitions['from_rating'] == rating]
    total_obligors = subset[['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']].sum().sum()
    total_defaults = subset['to_D'].sum()
    annual_rate = total_defaults / total_obligors if total_obligors > 0 else 0
    
    # Simple quarterly calculation
    quarterly_rate_simple = 1 - (1 - annual_rate) ** (0.25)
    
    # After 9 quarters
    survivor_9q = (1 - quarterly_rate_simple) ** 9
    default_9q = 1 - survivor_9q
    
    print(f"{rating}:")
    print(f"  Historical annual default rate: {annual_rate:.4f}")
    print(f"  Implied quarterly rate:  {quarterly_rate_simple:.4f}")
    print(f"  Expected default over 9 quarters: {default_9q:.4f}")
    
    # From matrices
    matrices = pd.read_csv('matrices.csv')
    baseline_q1 = matrices[(matrices['scenario'] == 'baseline') & 
                          (matrices['quarter'] == 1) & 
                          (matrices['from_rating'] == rating)]
    if len(baseline_q1) > 0:
        model_q_rate = baseline_q1['to_D'].values[0]
        # Compute 9-quarter default from model
        model_9q = 1 - (1 - model_q_rate) ** 9
        print(f"  Model quarterly rate: {model_q_rate:.4f}")
        print(f"  Model 9-quarter default: {model_9q:.4f}")
    print()

# Portfolio-level calculation
print("Portfolio-level expected default rate over 9 quarters:")
total_expected_defaults = 0
total_obligors = 0
for _, p_row in portfolio.iterrows():
    rating = p_row['rating']
    obligors = p_row['obligors']
    
    # Get historical rate for this rating
    subset = transitions[transitions['from_rating'] == rating]
    hist_obligors = subset[['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']].sum().sum()
    hist_defaults = subset['to_D'].sum()
    
    if hist_obligors > 0:
        annual_rate = hist_defaults / hist_obligors
        quarterly_rate = 1 - (1 - annual_rate) ** (0.25)
        default_rate_9q = 1 - (1 - quarterly_rate) ** 9
        
        expected_defaults = obligors * default_rate_9q
        total_expected_defaults += expected_defaults
        total_obligors += obligors

expected_rate = total_expected_defaults / total_obligors
print(f"Simple model: {expected_rate:.4f} ({expected_rate*100:.2f}%)")

pred = pd.read_csv('predictions.csv')
for scenario in ['baseline']:
    baseline_q9 = pred[(pred['scenario'] == scenario) & (pred['quarter'] == 9)]
    d_rate = baseline_q9[baseline_q9['state'] == 'D']['share'].values[0]
    print(f"{scenario} model: {d_rate:.4f} ({d_rate*100:.2f}%)")

EOF

```

## [51] tool

Comparing model predictions to simple calculation:

BBB:
  Historical annual default rate: 0.0022
  Implied quarterly rate:  0.0006
  Expected default over 9 quarters: 0.0050
  Model quarterly rate: 0.0008
  Model 9-quarter default: 0.0068

BB:
  Historical annual default rate: 0.0078
  Implied quarterly rate:  0.0020
  Expected default over 9 quarters: 0.0175
  Model quarterly rate: 0.0024
  Model 9-quarter default: 0.0213

B:
  Historical annual default rate: 0.0359
  Implied quarterly rate:  0.0091
  Expected default over 9 quarters: 0.0789
  Model quarterly rate: 0.0120
  Model 9-quarter default: 0.1028

CCC/C:
  Historical annual default rate: 0.3201
  Implied quarterly rate:  0.0920
  Expected default over 9 quarters: 0.5803
  Model quarterly rate: 0.0841
  Model 9-quarter default: 0.5466

Portfolio-level expected default rate over 9 quarters:
Simple model: 0.0349 (3.49%)
baseline model: 0.0508 (5.08%)


## [52] assistant

The model's 5.08% is somewhat higher than the simple 3.49% estimate, which could be due to:
1. Correlations in the data that the model is capturing
2. Different macro conditions in the scenarios vs. the historical average

Let me check what macro conditions the model is seeing:

**tool call: bash**

```
python3 << 'EOF'
import pandas as pd

macro_history = pd.read_csv('data/macro_history.csv')
scenario_data = pd.read_csv('data/scenario.csv')

features = ['gdp', 'unemployment', 'nasdaq', 'cpi']

print("="*70)
print("MACRO CONDITIONS COMPARISON")
print("="*70)

# Historical average
hist_avg = macro_history[features].mean()
hist_std = macro_history[features].std()

print("\nHistorical (all quarters):")
for f in features:
    print(f"  {f:12s}: {hist_avg[f]:9.2f} ± {hist_std[f]:6.2f}")

# Scenario averages (Q1-Q9)
print("\nScenario averages (Q1-Q9):")
for scenario in sorted(scenario_data['scenario'].unique()):
    scenario_subset = scenario_data[scenario_data['scenario'] == scenario]
    scenario_avg = scenario_subset[features].mean()
    print(f"\n{scenario}:")
    for f in features:
        diff = scenario_avg[f] - hist_avg[f]
        pct_diff = diff / hist_avg[f] * 100 if hist_avg[f] != 0 else 0
        print(f"  {f:12s}: {scenario_avg[f]:9.2f} ({diff:+7.2f}, {pct_diff:+6.2f}%)")

# Most recent historical quarter
recent = macro_history[macro_history['quarter'] == 0]
print(f"\nMost recent historical quarter (Q0):")
for f in features:
    val = recent[f].values[0]
    print(f"  {f:12s}: {val:9.2f}")

# First scenario quarter
scenario_q1_baseline = scenario_data[(scenario_data['scenario'] == 'baseline') & 
                                   (scenario_data['quarter'] == 1)]
print(f"\nBaseline scenario Q1:")
for f in features:
    val = scenario_q1_baseline[f].values[0]
    print(f"  {f:12s}: {val:9.2f}")

EOF

```

## [53] tool

======================================================================
MACRO CONDITIONS COMPARISON
======================================================================

Historical (all quarters):
  gdp         :    153.92 ±  21.52
  unemployment:      6.07 ±   2.56
  nasdaq      :    107.22 ±  32.49
  cpi         :    174.07 ±  29.45

Scenario averages (Q1-Q9):

adverse:
  gdp         :    180.07 ( +26.15, +16.99%)
  unemployment:      7.26 (  +1.19, +19.58%)
  nasdaq      :     36.20 ( -71.01, -66.23%)
  cpi         :    208.48 ( +34.41, +19.77%)

baseline:
  gdp         :    187.73 ( +33.81, +21.97%)
  unemployment:      6.15 (  +0.08,  +1.36%)
  nasdaq      :     45.57 ( -61.65, -57.50%)
  cpi         :    214.81 ( +40.75, +23.41%)

severe:
  gdp         :    174.75 ( +20.83, +13.53%)
  unemployment:      8.42 (  +2.35, +38.68%)
  nasdaq      :     31.56 ( -75.66, -70.57%)
  cpi         :    204.35 ( +30.28, +17.40%)

Most recent historical quarter (Q0):
  gdp         :    184.74
  unemployment:      6.95
  nasdaq      :     49.57
  cpi         :    211.58

Baseline scenario Q1:
  gdp         :    184.88
  unemployment:      6.46
  nasdaq      :     47.38
  cpi         :    211.57


## [54] assistant

I see - NASDAQ drops significantly in all scenarios (by 55-70%), which likely drives up default rates. The model is capturing this macro-default relationship. The predictions look reasonable now. Let me verify the final files are complete and correct:

**tool call: bash**

```
wc -l *.csv && echo "---" && head -3 predictions.csv && echo "..." && tail -3 predictions.csv && echo "---" && head -3 matrices.csv && echo "..." && tail -3 matrices.csv && echo "---" && head -3 backtest.csv && echo "..." && tail -3 backtest.csv

```

## [55] tool

   61 backtest.csv
  330 matrices.csv
   49 predictions.csv
  440 total
---
scenario,quarter,state,share
adverse,4,AAA,0.002413276530531968
adverse,4,AA,0.020016965282723644
...
severe,9,B,0.23902572329954977
severe,9,CCC/C,0.08237292702447543
severe,9,D,0.10983469343496392
---
scenario,quarter,from_rating,to_AAA,to_AA,to_A,to_BBB,to_BB,to_B,to_CCC_C,to_D
adverse,1,AAA,0.8488040121965571,0.12957356572045536,0.016007507415760465,0.0,0.004024021059830976,0.0,0.0015908936073960216,0.0
adverse,1,AA,0.0021643967721638947,0.8796790638759732,0.1050335045636922,0.01158926610903886,0.000575071135196833,0.00036285303541273324,0.00045988219356461247,0.00013596231495782707
...
history,0,BB,0.0,0.0,0.0,0.018911174785100286,0.867621776504298,0.09627507163323783,0.006303724928366762,0.010888252148997135
history,0,B,0.0,0.0,0.0,0.0,0.017226528854435832,0.8260120585701981,0.10335917312661498,0.053402239448751075
history,0,CCC/C,0.0,0.0,0.0,0.0,0.0,0.07386363636363637,0.5568181818181818,0.3693181818181818
---
scenario,year,default_rate
adverse,1,0.009145273909879644
baseline,1,0.009145273909879644
...
adverse,20,0.022889726596656598
baseline,20,0.022889726596656598
severe,20,0.022889726596656598


## [56] assistant

Perfect! All files are correctly formatted. Let me do a final comprehensive check:

**tool call: bash**

```
python3 << 'EOF'
import pandas as pd
import numpy as np

print("="*70)
print("FINAL VALIDATION")
print("="*70)

# 1. Predictions file
print("\n1. PREDICTIONS.CSV")
pred = pd.read_csv('predictions.csv')
print(f"   Rows: {len(pred)} (expected 48)")
print(f"   Expected: 3 scenarios × 2 checkpoints × 8 states")
assert len(pred) == 48, "Wrong number of rows"

# Check each scenario-quarter sums to 1
for scenario in pred['scenario'].unique():
    for quarter in pred['quarter'].unique():
        subset = pred[(pred['scenario'] == scenario) & (pred['quarter'] == quarter)]
        total = subset['share'].sum()
        assert abs(total - 1.0) < 1e-6, f"{scenario} Q{quarter} sums to {total}"
        print(f"   ✓ {scenario} Q{quarter}: sum = {total:.10f}")

# 2. Matrices file
print("\n2. MATRICES.CSV")
matrices = pd.read_csv('matrices.csv')
print(f"   Rows: {len(matrices)} (expected 329)")

# Count by scenario
for scenario in sorted(matrices['scenario'].unique()):
    count = len(matrices[matrices['scenario'] == scenario])
    if scenario == 'history':
        expected = 20 * 7  # 20 years × 7 ratings
    else:
        expected = 9 * 7   # 9 quarters × 7 ratings
    print(f"   {scenario:10s}: {count} rows (expected {expected})")
    assert count == expected, f"Wrong count for {scenario}"

# Verify each row sums to 1
prob_cols = ['to_AAA', 'to_AA', 'to_A', 'to_BBB', 'to_BB', 'to_B', 'to_CCC_C', 'to_D']
for idx in range(0, len(matrices), 50):
    row = matrices.iloc[idx]
    total = row[prob_cols].sum()
    assert abs(total - 1.0) < 1e-6, f"Row {idx} sums to {total}"
print(f"   ✓ Spot check: 7 rows sum to 1.0")

# 3. Backtest file
print("\n3. BACKTEST.CSV")
backtest = pd.read_csv('backtest.csv')
print(f"   Rows: {len(backtest)} (expected 60)")
assert len(backtest) == 60, "Wrong number of rows"

# Check structure
for scenario in backtest['scenario'].unique():
    count = len(backtest[backtest['scenario'] == scenario])
    assert count == 20, f"Wrong count for {scenario}"
    print(f"   ✓ {scenario}: 20 years")

# All default rates should be between 0 and 1
assert (backtest['default_rate'] >= 0).all(), "Negative default rate"
assert (backtest['default_rate'] <= 1).all(), "Default rate > 1"
print(f"   ✓ All default rates in [0, 1]")

print("\n" + "="*70)
print("ALL VALIDATION CHECKS PASSED ✓")
print("="*70)

# Summary stats
print("\nSummary Statistics:")
print(f"\nPredictions:")
for scenario in sorted(pred['scenario'].unique()):
    q9_data = pred[(pred['scenario'] == scenario) & (pred['quarter'] == 9)]
    d_rate = q9_data[q9_data['state'] == 'D']['share'].values[0]
    print(f"  {scenario}: Q9 default = {d_rate:.4f}")

print(f"\nBacktest (Year 20):")
for scenario in sorted(backtest['scenario'].unique()):
    rate = backtest[(backtest['scenario'] == scenario) & 
                   (backtest['year'] == 20)]['default_rate'].values[0]
    print(f"  {scenario}: {rate:.6f}")

EOF

```

## [57] tool

======================================================================
FINAL VALIDATION
======================================================================

1. PREDICTIONS.CSV
   Rows: 48 (expected 48)
   Expected: 3 scenarios × 2 checkpoints × 8 states
   ✓ adverse Q4: sum = 1.0000000000
   ✓ adverse Q9: sum = 1.0000000000
   ✓ baseline Q4: sum = 1.0000000000
   ✓ baseline Q9: sum = 1.0000000000
   ✓ severe Q4: sum = 1.0000000000
   ✓ severe Q9: sum = 1.0000000000

2. MATRICES.CSV
   Rows: 329 (expected 329)
   adverse   : 63 rows (expected 63)
   baseline  : 63 rows (expected 63)
   history   : 140 rows (expected 140)
   severe    : 63 rows (expected 63)
   ✓ Spot check: 7 rows sum to 1.0

3. BACKTEST.CSV
   Rows: 60 (expected 60)
   ✓ adverse: 20 years
   ✓ baseline: 20 years
   ✓ severe: 20 years
   ✓ All default rates in [0, 1]

======================================================================
ALL VALIDATION CHECKS PASSED ✓
======================================================================

Summary Statistics:

Predictions:
  adverse: Q9 default = 0.0768
  baseline: Q9 default = 0.0508
  severe: Q9 default = 0.1098

Backtest (Year 20):
  adverse: 0.022890
  baseline: 0.022890
  severe: 0.022890


## [58] assistant

Excellent! All files are valid. Now let me submit the predictions.csv file:

**tool call: bash**

```
cat predictions.csv
```

## [59] tool

scenario,quarter,state,share
adverse,4,AAA,0.002413276530531968
adverse,4,AA,0.020016965282723644
adverse,4,A,0.13838891846324458
adverse,4,BBB,0.33016001339322426
adverse,4,BB,0.2392806978883444
adverse,4,B,0.188132065473389
adverse,4,CCC/C,0.05216252292970517
adverse,4,D,0.029445540038836815
adverse,9,AAA,0.0013032139697124628
adverse,9,AA,0.01863219471215832
adverse,9,A,0.13209071465646754
adverse,9,BBB,0.2905782948146267
adverse,9,BB,0.2015976757574751
adverse,9,B,0.21478620781986268
adverse,9,CCC/C,0.0642253410796708
adverse,9,D,0.0767863571900261
baseline,4,AAA,0.0030992159213003036
baseline,4,AA,0.025374383330518262
baseline,4,A,0.15910762446410023
baseline,4,BBB,0.3445303572570172
baseline,4,BB,0.24521942226952856
baseline,4,B,0.16590360037173127
baseline,4,CCC/C,0.037895889372320544
baseline,4,D,0.01886950701348355
baseline,9,AAA,0.0018798241708794742
baseline,9,AA,0.024387437973836676
baseline,9,A,0.15962282427851332
baseline,9,BBB,0.3147991213551985
baseline,9,BB,0.20811604329176375
baseline,9,B,0.18817142640263565
baseline,9,CCC/C,0.05226974589286937
baseline,9,D,0.05075357663430314
severe,4,AAA,0.002053136746822456
severe,4,AA,0.016839361255160376
severe,4,A,0.12510004954867557
severe,4,BBB,0.3203372337994184
severe,4,BB,0.2346402930766464
severe,4,B,0.20153144885719296
severe,4,CCC/C,0.06225599166236395
severe,4,D,0.03724248505371994
severe,9,AAA,0.0008038273267355183
severe,9,AA,0.012347699220132782
severe,9,A,0.10200227851926814
severe,9,BBB,0.26315122203392455
severe,9,BB,0.1904616291409498
severe,9,B,0.23902572329954977
severe,9,CCC/C,0.08237292702447543
severe,9,D,0.10983469343496392


## [60] assistant

Perfect! Now let me submit this:

**tool call: submit**

```
scenario,quarter,state,share
adverse,4,AAA,0.002413276530531968
adverse,4,AA,0.020016965282723644
adverse,4,A,0.13838891846324458
adverse,4,BBB,0.33016001339322426
adverse,4,BB,0.2392806978883444
adverse,4,B,0.188132065473389
adverse,4,CCC/C,0.05216252292970517
adverse,4,D,0.029445540038836815
adverse,9,AAA,0.0013032139697124628
adverse,9,AA,0.01863219471215832
adverse,9,A,0.13209071465646754
adverse,9,BBB,0.2905782948146267
adverse,9,BB,0.2015976757574751
adverse,9,B,0.21478620781986268
adverse,9,CCC/C,0.0642253410796708
adverse,9,D,0.0767863571900261
baseline,4,AAA,0.0030992159213003036
baseline,4,AA,0.025374383330518262
baseline,4,A,0.15910762446410023
baseline,4,BBB,0.3445303572570172
baseline,4,BB,0.24521942226952856
baseline,4,B,0.16590360037173127
baseline,4,CCC/C,0.037895889372320544
baseline,4,D,0.01886950701348355
baseline,9,AAA,0.0018798241708794742
baseline,9,AA,0.024387437973836676
baseline,9,A,0.15962282427851332
baseline,9,BBB,0.3147991213551985
baseline,9,BB,0.20811604329176375
baseline,9,B,0.18817142640263565
baseline,9,CCC/C,0.05226974589286937
baseline,9,D,0.05075357663430314
severe,4,AAA,0.002053136746822456
severe,4,AA,0.016839361255160376
severe,4,A,0.12510004954867557
severe,4,BBB,0.3203372337994184
severe,4,BB,0.2346402930766464
severe,4,B,0.20153144885719296
severe,4,CCC/C,0.06225599166236236395
severe,4,D,0.03724248505371994
severe,9,AAA,0.0008038273267355183
severe,9,AA,0.012347699220132782
severe,9,A,0.10200227851926814
severe,9,BBB,0.26315122203392455
severe,9,BB,0.1904616291409498
severe,9,B,0.23902572329954977
severe,9,CCC/C,0.08237292702447543
severe,9,D,0.10983469343496392

```

## [61] tool

scenario,quarter,state,share
adverse,4,AAA,0.002413276530531968
adverse,4,AA,0.020016965282723644
adverse,4,A,0.13838891846324458
adverse,4,BBB,0.33016001339322426
adverse,4,BB,0.2392806978883444
adverse,4,B,0.188132065473389
adverse,4,CCC/C,0.05216252292970517
adverse,4,D,0.029445540038836815
adverse,9,AAA,0.0013032139697124628
adverse,9,AA,0.01863219471215832
adverse,9,A,0.13209071465646754
adverse,9,BBB,0.2905782948146267
adverse,9,BB,0.2015976757574751
adverse,9,B,0.21478620781986268
adverse,9,CCC/C,0.0642253410796708
adverse,9,D,0.0767863571900261
baseline,4,AAA,0.0030992159213003036
baseline,4,AA,0.025374383330518262
baseline,4,A,0.15910762446410023
baseline,4,BBB,0.3445303572570172
baseline,4,BB,0.24521942226952856
baseline,4,B,0.16590360037173127
baseline,4,CCC/C,0.037895889372320544
baseline,4,D,0.01886950701348355
baseline,9,AAA,0.0018798241708794742
baseline,9,AA,0.024387437973836676
baseline,9,A,0.15962282427851332
baseline,9,BBB,0.3147991213551985
baseline,9,BB,0.20811604329176375
baseline,9,B,0.18817142640263565
baseline,9,CCC/C,0.05226974589286937
baseline,9,D,0.05075357663430314
severe,4,AAA,0.002053136746822456
severe,4,AA,0.016839361255160376
severe,4,A,0.12510004954867557
severe,4,BBB,0.3203372337994184
severe,4,BB,0.2346402930766464
severe,4,B,0.20153144885719296
severe,4,CCC/C,0.06225599166236236395
severe,4,D,0.03724248505371994
severe,9,AAA,0.0008038273267355183
severe,9,AA,0.012347699220132782
severe,9,A,0.10200227851926814
severe,9,BBB,0.26315122203392455
severe,9,BB,0.1904616291409498
severe,9,B,0.23902572329954977
severe,9,CCC/C,0.08237292702447543
severe,9,D,0.10983469343496392


