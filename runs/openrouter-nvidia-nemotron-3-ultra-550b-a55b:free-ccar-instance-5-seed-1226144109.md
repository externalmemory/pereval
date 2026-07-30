# openrouter/nvidia/nemotron-3-ultra-550b-a55b:free — ccar (id=instance-5-seed-1226144109)

- 9/9 points predicted; Winkler regret 0.084 (agent 0.142 vs oracle 0.059); MAE 0.010; coverage 0.765; mean width 0.037.
- messages 48 | limit None | seed None

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

**[reasoning]**

> Let me start by exploring the data to understand its structure and characteristics



**tool call: bash**

```

```

## [3] tool

total 20
drwxr-xr-x 2 root root 4096 Jul 26 01:56 .
drwxr-xr-x 1 root root 4096 Jul 26 01:56 ..
-rw-r--r-- 1 root root  795 Jul 26 01:56 scenario.csv
-rw-r--r-- 1 root root 6409 Jul 26 01:56 train.csv


## [4] assistant

**[reasoning]**

> Let me examine the training data and scenario data first



**tool call: bash**

```

```

## [5] tool

quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi,default_rate
1,118.0839,6.9666,,,,,333.9192,,119.3537,0.028427
2,122.2991,4.8709,,,,,347.8929,,119.5728,0.016979
3,121.5905,5.728,,,,,341.7487,,119.6025,0.040578
4,124.3742,4.66,,,,,322.3302,,119.5625,0.018229
5,124.3895,5.25,,3.0615,,,315.4091,,117.9744,0.021735
6,123.6063,5.5831,,3.1471,,,327.5714,,115.868,0.029706
7,124.3254,5.5927,,3.0098,,,337.3137,,114.6217,0.031683
8,124.3008,6.0145,,3.0713,,,319.8122,,112.7898,0.046739
9,124.49,5.2484,,3.0116,,,309.2161,,111.9499,0.024466
10,121.6852,7.2614,,3.2854,,,277.4297,,111.592,0.029245
11,121.9827,7.4492,138.0913,2.6347,,,325.9189,,111.3332,0.032507
12,122.3001,8.7299,139.3511,2.6723,,,358.8312,,111.4132,0.077993
13,125.0938,7.0009,142.6767,2.6562,,,385.852,,111.2378,0.028097
14,122.2763,7.7863,146.0911,2.6022,,,395.4958,,111.6419,0.013901
15,124.2113,5.8503,151.5873,2.1586,,,390.7672,,114.5279,0.012401
16,125.2539,6.7026,156.5992,1.8035,,,425.6597,,117.743,0.045277
17,125.2239,7.5203,158.0543,1.7664,,,458.8975,14.953,120.0067,0.035063
18,126.6187,6.7461,158.363,2.1709,,,489.8421,23.3079,120.7709,0.044815
19,126.066,8.8692,159.6983,2.5015,,,506.8776,27.6123,121.2174,0.051577
20,127.7946,7.8671,162.2248,2.7129,,,478.5797,27.1317,120.4447,0.036435
21,129.5382,6.6289,162.5444,2.8387,,,449.2617,27.8795,121.2737,0.053644
22,131.358,6.2431,165.6,2.5398,,,459.5625,22.0552,123.9397,0.024082
23,130.343,7.2607,165.3777,2.34,,,491.1192,22.9116,126.9428,0.040308
24,133.2988,6.2821,169.0098,2.2154,,,591.5855,16.9629,130.1727,0.0195
25,135.4651,5.6659,172.4994,2.0304,,,680.7255,16.0411,135.741,0.028569
26,126.0732,12.449,171.5385,5.8255,,,427.399,60.6218,133.4544,0.017724
27,129.3418,4.1447,172.5023,2.542,,,388.2343,19.2916,135.3673,0.012464
28,129.4139,4.1525,174.8252,2.7845,,,364.2583,25.3666,136.024,0.014187
29,129.4254,3.8882,179.7053,3.4525,,,337.5557,28.2178,136.9879,0.020992
30,130.4373,3.6095,179.227,3.4628,,,279.3735,32.0082,135.1687,0.019938
31,128.1726,4.8973,176.6875,3.5857,,,237.6799,30.7201,134.73,0.011093
32,128.7309,6.0422,175.9975,3.2269,,,236.5672,29.5504,134.6445,0.022611
33,129.1478,6.9059,173.2815,2.9545,,,273.2375,22.0283,136.1173,0.044054
34,129.6491,7.2056,173.0325,3.1966,687.3524,381.8969,250.7052,24.1924,139.3914,0.042628
35,131.1281,6.6088,172.0253,3.105,659.1218,364.5712,211.754,23.3012,141.7987,0.016994
36,134.4377,5.9168,171.0539,3.0444,654.8223,348.5331,207.6844,22.1918,143.3045,0.040844
37,134.703,5.904,170.8679,3.0096,666.5674,356.1495,213.0027,23.6216,145.5982,0.023463
38,135.9583,5.5074,175.3125,3.1592,718.0917,380.2295,233.4551,19.7695,148.04,0.024127
39,136.7518,5.6195,180.5625,3.2819,739.9429,372.4849,242.2696,18.9955,150.1015,0.016018
40,140.3178,4.5149,188.0826,3.3025,703.8391,357.5262,215.2651,25.1963,152.7833,0.029562
41,139.4477,5.327,191.5891,3.4264,710.5047,345.9365,193.711,28.1457,152.5643,0.024983
42,139.1564,6.9506,191.5349,3.265,789.5702,374.7813,214.1377,18.4329,154.5806,0.02455
43,139.9773,7.1805,192.9292,3.3925,834.7337,390.6726,221.0288,17.5814,156.7079,0.048764
44,139.122,7.3579,196.2382,3.2751,883.5841,416.7851,244.3968,17.1754,157.6929,0.041623
45,133.7165,13.6151,198.5628,5.6127,846.5396,425.8637,214.4154,49.2428,151.6805,0.038403
46,136.3814,5.4311,207.6946,2.3504,886.1563,425.7612,214.0758,17.041,156.0056,0.026055
47,136.8066,5.501,214.5346,2.4329,918.7191,442.742,214.2711,13.6786,158.6217,0.023403
48,138.0193,5.1504,216.1985,2.5193,930.9735,464.0175,218.7178,14.8146,160.4312,0.025625
49,139.6534,4.4225,217.0767,2.5154,999.0852,502.6581,241.3331,12.0483,161.4042,0.018705
50,133.4506,9.3339,216.1443,5.9879,927.6548,505.2917,176.4398,60.7798,155.5673,0.021089
51,133.7762,5.2273,217.7265,2.7331,957.8534,509.8675,184.9349,18.3401,158.5384,0.022179
52,134.9204,4.9726,222.7858,2.9516,950.2853,504.3439,166.0121,16.5381,162.8999,0.014982
53,135.08,5.6446,224.2793,3.2152,956.9954,521.0521,164.798,16.1003,165.5097,0.025695
54,134.7162,5.889,223.935,3.1878,983.3024,538.8459,172.1199,20.8143,167.4786,0.03016
55,135.1129,6.1848,225.0999,3.4797,999.2331,530.0432,166.1789,22.4321,168.7029,0.02447
56,134.3637,7.5693,224.4892,3.3131,1040.6479,580.8714,175.1077,19.8963,170.4353,0.038985
57,137.2713,6.325,227.577,3.3666,1126.238,633.2211,188.2457,17.3973,173.3388,0.031709
58,139.8172,5.1498,232.6676,3.3194,1157.7822,674.3309,197.993,19.5827,174.5471,0.024182
59,138.5298,5.8531,239.816,3.1291,1212.4017,743.6174,208.6692,18.1544,179.524,0.033244
60,140.7868,5.4808,239.1828,3.3528,1293.4204,775.7406,228.7391,24.515,183.2801,0.018945
61,140.3008,4.7681,238.2642,4.202,1281.5162,799.1618,194.2956,35.6645,184.6287,0.031162
62,141.2778,4.7699,233.3324,3.8229,1392.0534,873.2746,232.1017,19.8122,182.4824,0.032309
63,144.0245,3.9368,236.466,3.3457,1463.1817,945.6952,253.7099,17.3493,183.2394,0.017875
64,144.369,5.1822,235.5706,3.3292,1462.3159,961.363,230.6222,18.195,183.9069,0.029139
65,146.1254,4.4165,233.7863,3.3621,1515.6035,1018.901,250.8438,13.6304,184.6362,0.018354
66,149.9324,4.6095,235.8906,2.8606,1770.8056,1137.2796,316.7723,10.9935,187.4739,0.027076
67,153.5116,3.9044,237.8421,2.4957,1902.7272,1228.1599,379.4346,9.9514,190.3972,0.018774
68,154.8409,4.2379,238.943,2.4582,1981.7954,1316.8749,393.8893,12.0634,195.8188,0.022429
69,154.4991,5.4831,238.0474,1.9757,2095.1443,1365.4637,442.5325,11.8413,200.9278,0.041501
70,146.4253,11.7893,239.3387,5.4367,1911.6976,1232.1296,315.1915,46.98,195.532,0.026118
71,146.7702,4.6315,249.8175,1.2092,2069.3144,1241.5293,348.9992,8.9209,199.9856,0.03385
72,144.3651,5.6393,260.8562,1.5097,2189.6723,1340.485,378.3438,10.8088,204.4477,0.020619
73,147.7234,5.0728,266.454,1.311,2317.4319,1423.9358,424.5206,10.8296,208.78,0.00922
74,147.7691,5.2269,270.6202,1.6933,2529.5173,1517.2062,449.5438,14.6377,207.6375,0.015003
75,147.5721,5.9145,274.4956,1.2745,2679.5781,1643.1474,483.7691,12.0527,207.2007,0.016439
76,150.5191,5.2783,275.7014,1.3683,3004.314,1780.3912,581.3296,15.5189,211.2554,0.029767
77,151.2391,5.3464,277.4252,1.0414,3141.8579,1823.984,620.4019,12.7066,214.3225,0.029153
78,152.4973,5.916,277.6657,1.0927,3586.4013,1970.4456,693.4425,12.1383,216.8521,0.024123
79,153.9686,6.0062,283.0007,1.4688,3721.2305,2038.1546,719.6024,13.4733,217.6913,0.029878
80,154.2361,5.0024,294.2207,1.4962,3935.614,2078.7173,791.2444,13.7735,220.3592,0.011391


## [6] assistant

**[reasoning]**

> Let me also look at the scenario data.



**tool call: bash**

```

```

## [7] tool

quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi
81,152.617,5.2237,288.4656,1.6195,3985.1965,2116.6344,734.977,14.5721,219.3511
82,151.015,5.4547,282.823,1.7428,3956.7256,2099.4871,682.7109,15.4171,218.3476
83,149.4298,5.6959,277.2908,1.866,4065.7783,2175.5736,634.1615,16.311,217.3487
84,147.8612,5.9478,271.8668,1.9893,4036.9233,2068.6221,589.0647,17.2568,216.3544
85,146.309,6.2109,266.5489,2.1126,4087.7436,2025.2248,547.1747,18.2575,215.3646
86,144.7732,6.4855,261.3351,2.2359,4129.8979,2032.0418,508.2637,19.3161,214.3794
87,143.2535,6.7724,256.2232,2.3591,4083.426,2005.5909,472.1198,20.4362,213.3987
88,141.7497,7.0719,251.2113,2.4824,4096.7539,1951.5491,438.5461,21.6212,212.4224
89,140.2617,7.3846,246.2974,2.6057,3964.5524,1920.6252,407.36,22.8749,211.4506


## [8] assistant

**[reasoning]**

> Now I understand the data. We have historical data (historical.csv) with many economic variables and a scenario.csv with 9 future quarters (quarters 81-89) that we need to predict for.
> 
> Let me look at the historical data more carefully - it seems to have many columns. Let me parse it properly.



**tool call: python**

```

```

## [9] tool

## [10] assistant

**[reasoning]**

> I need to use the correct parameter name - it's `code` not `command` for the python tool



**tool call: python**

```
import pandas as pd
import numpy as np

# Read historical data
hist = pd.read_csv('data/historical.csv')
print("Historical data shape:", hist.shape)
print("Columns:", hist.columns.tolist())
print("\nFirst 5 rows:")
print(hist.head())
print("\nLast 5 rows:")
print(hist.tail())
print("\nData types:")
print(hist.dtypes)
print("\nQuarter range:", hist['quarter'].min(), "-", hist['quarter'].max())
```

## [11] tool

Traceback (most recent call last):
  File "<stdin>", line 5, in <module>
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
FileNotFoundError: [Errno 2] No such file or directory: 'data/historical.csv'



## [12] assistant

**[reasoning]**

> The file is called `historical.csv` not `train.csv`. Let me check the directory again and use the correct filename



**tool call: bash**

```

```

## [13] tool

total 20
drwxr-xr-x 2 root root 4096 Jul 26 01:56 .
drwxr-xr-x 1 root root 4096 Jul 26 01:56 ..
-rw-r--r-- 1 root root  795 Jul 26 01:56 scenario.csv
-rw-r--r-- 1 root root 6409 Jul 26 01:56 train.csv


## [14] assistant

**[reasoning]**

> The file is called train.csv, not historical.csv. Let me read it



**tool call: python**

```
import pandas as pd
import numpy as np

# Read historical data
hist = pd.read_csv('data/train.csv')
print("Historical data shape:", hist.shape)
print("Columns:", hist.columns.tolist())
print("\nFirst 5 rows:")
print(hist.head())
print("\nLast 5 rows:")
print(hist.tail())
print("\nData types:")
print(hist.dtypes)
print("\nQuarter range:", hist['quarter'].min(), "-", hist['quarter'].max())
print("\nMissing values:")
print(hist.isnull().sum())
print("\nDefault rate stats:")
print(hist['default_rate'].describe())
```

## [15] tool

Historical data shape: (80, 11)
Columns: ['quarter', 'gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi', 'default_rate']

First 5 rows:
   quarter       gdp  unemployment  hpi  ...    nasdaq  vix       cpi  default_rate
0        1  118.0839        6.9666  NaN  ...  333.9192  NaN  119.3537      0.028427
1        2  122.2991        4.8709  NaN  ...  347.8929  NaN  119.5728      0.016979
2        3  121.5905        5.7280  NaN  ...  341.7487  NaN  119.6025      0.040578
3        4  124.3742        4.6600  NaN  ...  322.3302  NaN  119.5625      0.018229
4        5  124.3895        5.2500  NaN  ...  315.4091  NaN  117.9744      0.021735

[5 rows x 11 columns]

Last 5 rows:
    quarter       gdp  unemployment  ...      vix       cpi  default_rate
75       76  150.5191        5.2783  ...  15.5189  211.2554      0.029767
76       77  151.2391        5.3464  ...  12.7066  214.3225      0.029153
77       78  152.4973        5.9160  ...  12.1383  216.8521      0.024123
78       79  153.9686        6.0062  ...  13.4733  217.6913      0.029878
79       80  154.2361        5.0024  ...  13.7735  220.3592      0.011391

[5 rows x 11 columns]

Data types:
quarter           int64
gdp             float64
unemployment    float64
hpi             float64
bbb_spread      float64
sp500           float64
djia            float64
nasdaq          float64
vix             float64
cpi             float64
default_rate    float64
dtype: object

Quarter range: 1 - 80

Missing values:
quarter          0
gdp              0
unemployment     0
hpi             10
bbb_spread       4
sp500           33
djia            33
nasdaq           0
vix             16
cpi              0
default_rate     0
dtype: int64

Default rate stats:
count    80.000000
mean      0.027882
std       0.011684
min       0.009220
25%       0.019361
50%       0.025660
75%       0.032691
max       0.077993
Name: default_rate, dtype: float64


## [16] assistant

**[reasoning]**

> Let me look at the scenario data more closely, and also explore the historical data more thoroughly to understand the features and their relationships with default_rate.



**tool call: python**

```
import pandas as pd
import numpy as np

# Read scenario data
scenario = pd.read_csv('data/scenario.csv')
print("Scenario data shape:", scenario.shape)
print("Columns:", scenario.columns.tolist())
print("\nAll rows:")
print(scenario)
print("\nData types:")
print(scenario.dtypes)
print("\nMissing values:")
print(scenario.isnull().sum())
```

## [17] tool

Scenario data shape: (9, 10)
Columns: ['quarter', 'gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']

All rows:
   quarter       gdp  unemployment  ...    nasdaq      vix       cpi
0       81  152.6170        5.2237  ...  734.9770  14.5721  219.3511
1       82  151.0150        5.4547  ...  682.7109  15.4171  218.3476
2       83  149.4298        5.6959  ...  634.1615  16.3110  217.3487
3       84  147.8612        5.9478  ...  589.0647  17.2568  216.3544
4       85  146.3090        6.2109  ...  547.1747  18.2575  215.3646
5       86  144.7732        6.4855  ...  508.2637  19.3161  214.3794
6       87  143.2535        6.7724  ...  472.1198  20.4362  213.3987
7       88  141.7497        7.0719  ...  438.5461  21.6212  212.4224
8       89  140.2617        7.3846  ...  407.3600  22.8749  211.4506

[9 rows x 10 columns]

Data types:
quarter           int64
gdp             float64
unemployment    float64
hpi             float64
bbb_spread      float64
sp500           float64
djia            float64
nasdaq          float64
vix             float64
cpi             float64
dtype: object

Missing values:
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


## [18] assistant

**[reasoning]**

> Let me explore the historical data more thoroughly to understand the relationships and handle missing values.



**tool call: python**

```
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

hist = pd.read_csv('data/train.csv')

# Look at the data more carefully
print("Quarter range:", hist['quarter'].min(), "-", hist['quarter'].max())
print("\nMissing values per column:")
print(hist.isnull().sum())

# Check when each series starts
for col in hist.columns:
    if col not in ['quarter', 'default_rate']:
        first_valid = hist[col].first_valid_index()
        if first_valid is not None:
            first_quarter = hist.loc[first_valid, 'quarter']
            print(f"{col}: first valid at quarter {first_quarter}")

print("\nDefault rate stats:")
print(hist['default_rate'].describe())

# Check correlations with default_rate for columns with no missing values
cols_no_missing = ['gdp', 'unemployment', 'nasdaq', 'cpi', 'default_rate']
corr_matrix = hist[cols_no_missing].corr()
print("\nCorrelations with default_rate (no missing):")
print(corr_matrix['default_rate'].sort_values(ascending=False))

# Check correlations for series with some missing
cols_some_missing = ['hpi', 'bbb_spread', 'vix']
for col in cols_some_missing:
    valid = hist[['default_rate', col]].dropna()
    if len(valid) > 10:
        corr = valid.corr().iloc[0,1]
        print(f"{col}: corr with default_rate = {corr:.4f} (n={len(valid)})")

# Check sp500, djia, nasdaq correlations where available
for col in ['sp500', 'djia', 'nasdaq']:
    valid = hist[['default_rate', col]].dropna()
    if len(valid) > 10:
        corr = valid.corr().iloc[0,1]
        print(f"{col}: corr with default_rate = {corr:.4f} (n={len(valid)})")

print("\nDefault rate over time (last 20 quarters):")
print(hist[['quarter', 'default_rate']].tail(20))
```

## [19] tool

Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
ModuleNotFoundError: No module named 'matplotlib'



## [20] assistant

**[reasoning]**

> Matplotlib isn't available. Let me just use pandas and numpy.



**tool call: python**

```
import pandas as pd
import numpy as np

hist = pd.read_csv('data/train.csv')

# Check when each series starts
for col in hist.columns:
    if col not in ['quarter', 'default_rate']:
        first_valid = hist[col].first_valid_index()
        if first_valid is not None:
            first_quarter = hist.loc[first_valid, 'quarter']
            print(f"{col}: first valid at quarter {first_quarter} (index {first_valid})")

print("\nCorrelations with default_rate for columns with no missing:")
cols_no_missing = ['gdp', 'unemployment', 'nasdaq', 'cpi', 'default_rate']
corr_matrix = hist[cols_no_missing].corr()
print(corr_matrix['default_rate'].sort_values(ascending=False))

print("\nCorrelations for columns with some missing:")
for col in ['hpi', 'bbb_spread', 'vix', 'sp500', 'djia']:
    valid = hist[['default_rate', col]].dropna()
    if len(valid) > 10:
        corr = valid.corr().iloc[0,1]
        print(f"{col}: corr with default_rate = {corr:.4f} (n={len(valid)})")

# Check correlations of first differences / growth rates
print("\nDefault rate stats:")
print(hist['default_rate'].describe())

# Look at default rate over time
print("\nDefault rate by quarter (last 20):")
print(hist[['quarter', 'default_rate']].tail(20))

# Check some transformations - growth rates
print("\nGrowth rates correlations with default_rate:")
for col in ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'nasdaq', 'sp500', 'djia', 'vix', 'cpi']:
    if col in hist.columns:
        valid = hist[['default_rate', col]].dropna()
        if len(valid) > 20:
            # Compute quarter-over-quarter growth rate
            valid = valid.sort_values('quarter') if 'quarter' in valid.columns else valid
            valid = valid.copy()
            valid[f'{col}_growth'] = valid[col].pct_change()
            valid = valid.dropna()
            if len(valid) > 10:
                corr = valid['default_rate'].corr(valid[f'{col}_growth'])
                print(f"{col}_growth: corr with default_rate = {corr:.4f} (n={len(valid)})")

# Also check levels vs changes
print("\nLevels correlations (full available history):")
for col in ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'nasdaq', 'sp500', 'djia', 'vix', 'cpi']:
    valid = hist[['default_rate', col]].dropna()
    if len(valid) > 10:
        corr = valid.corr().iloc[0,1]
        print(f"{col}: corr with default_rate = {corr:.4f} (n={len(valid)})")
```

## [21] tool

gdp: first valid at quarter 1 (index 0)
unemployment: first valid at quarter 1 (index 0)
hpi: first valid at quarter 11 (index 10)
bbb_spread: first valid at quarter 5 (index 4)
sp500: first valid at quarter 34 (index 33)
djia: first valid at quarter 34 (index 33)
nasdaq: first valid at quarter 1 (index 0)
vix: first valid at quarter 17 (index 16)
cpi: first valid at quarter 1 (index 0)

Correlations with default_rate for columns with no missing:
default_rate    1.000000
unemployment    0.372468
nasdaq          0.014227
gdp            -0.221236
cpi            -0.260368
Name: default_rate, dtype: float64

Correlations for columns with some missing:
hpi: corr with default_rate = -0.3084 (n=70)
bbb_spread: corr with default_rate = 0.0140 (n=76)
vix: corr with default_rate = 0.0600 (n=64)
sp500: corr with default_rate = -0.2444 (n=47)
djia: corr with default_rate = -0.2493 (n=47)

Default rate stats:
count    80.000000
mean      0.027882
std       0.011684
min       0.009220
25%       0.019361
50%       0.025660
75%       0.032691
max       0.077993
Name: default_rate, dtype: float64

Default rate by quarter (last 20):
    quarter  default_rate
60       61      0.031162
61       62      0.032309
62       63      0.017875
63       64      0.029139
64       65      0.018354
65       66      0.027076
66       67      0.018774
67       68      0.022429
68       69      0.041501
69       70      0.026118
70       71      0.033850
71       72      0.020619
72       73      0.009220
73       74      0.015003
74       75      0.016439
75       76      0.029767
76       77      0.029153
77       78      0.024123
78       79      0.029878
79       80      0.011391

Growth rates correlations with default_rate:
gdp_growth: corr with default_rate = -0.0494 (n=79)
unemployment_growth: corr with default_rate = 0.1197 (n=79)
hpi_growth: corr with default_rate = -0.1672 (n=69)
bbb_spread_growth: corr with default_rate = -0.0393 (n=75)
nasdaq_growth: corr with default_rate = 0.1363 (n=79)
sp500_growth: corr with default_rate = -0.0287 (n=46)
djia_growth: corr with default_rate = 0.0101 (n=46)
vix_growth: corr with default_rate = -0.0266 (n=63)
cpi_growth: corr with default_rate = -0.0325 (n=79)

Levels correlations (full available history):
gdp: corr with default_rate = -0.2212 (n=80)
unemployment: corr with default_rate = 0.3725 (n=80)
hpi: corr with default_rate = -0.3084 (n=70)
bbb_spread: corr with default_rate = 0.0140 (n=76)
nasdaq: corr with default_rate = 0.0142 (n=80)
sp500: corr with default_rate = -0.2444 (n=47)
djia: corr with default_rate = -0.2493 (n=47)
vix: corr with default_rate = 0.0600 (n=64)
cpi: corr with default_rate = -0.2604 (n=80)


## [22] assistant

**[reasoning]**

> Let me analyze the data more carefully. Key observations:
> 
> 1. The dataset has 80 quarters of history (quarters 1-80) and 9 scenario quarters (81-89)
> 2. Some macro series have missing values early on (hpi starts at Q11, bbb_spread at Q5, sp500/djia at Q34, vix at Q17)
> 3. Correlations with default_rate:
>    - unemployment: 0.37 (strongest positive)
>    - hpi: -0.31 (negative, but starts at Q11)
>    - cpi: -0.26
>    - gdp: -0.22
>    - sp500/djia: -0.24 (but only from Q34)
>    - vix: 0.06 (weak)
>    - bbb_spread: 0.014 (very weak)
>    - nasdaq: 0.01 (very weak)
>    - cpi: -0.26
> 
> The scenario (quarters 81-89) shows:
> - GDP declining from 152.6 to 140.3 (recession)
> - Unemployment rising from 5.2% to 7.4% (recession)
> - HPI jumps dramatically at Q89 from 180 to 246 (this seems like a data issue or regime change - HPI jumps from ~180 to 246)
> - BBB spread goes from ~3.3 down to 2.6 (compression, unusual in stress)
> - SP500 jumps from ~735 to 3964 (massive jump - regime change?)
> - DJIA jumps from ~380 to 1920
> - NASDAQ jumps from ~735 to 407
> - VIX rises from 14.6 to 22.9
> - CPI declines from 219 to 211
> 
> Wait, the scenario data at Q89 looks very strange - SP500 jumps from ~735 to 3964, DJIA from 380 to 1920, NASDAQ from 735 to 407, HPI from ~180 to 246. This looks like a regime change or different scaling. Let me check the historical data for these series to understand the scaling.
> 
> Actually, looking at the historical data, sp500 and djia start at quarter 34 with values around 687 and 381. By quarter 80, sp500 is around 739 and djia around 380. But in the scenario Q89, sp500 is 3964 and djia is 1920. That's a huge jump - likely a different index scaling or a major regime change in the scenario.
> 
> Similarly, HPI in historical data goes from ~138 at Q11 to ~188 at Q80. But in scenario Q89 it's 246. That's a jump but more plausible.
> 
> NASDAQ in historical goes from 334 to ~735. In scenario Q89 it's 407.
> 
> VIX goes from ~15 to ~22 in scenario.
> 
> BBB spread goes from ~3.3 down to 2.6.
> 
> CPI goes from 219 down to 211.
> 
> GDP declines from 152 to 140.
> Unemployment rises from 5.2% to 7.4%.
> 
> This scenario seems like a stress scenario with GDP declining, unemployment rising, VIX rising, but equity markets strangely rallying (or the indices are rebased). The HPI jump at Q89 is also odd.
> 
> Let me look at the historical data more carefully to understand the scaling of sp500, djia, nasdaq.
> 
> Let me explore more and build a model. Given the stress scenario pushes variables out of sample, I need a robust model. Let me consider:
> 
> 1. Unemployment has the strongest correlation with default rate (0.37)
> 2. HPI has -0.31 correlation (but only from Q11)
> 3. GDP has -0.22
> 4. CPI has -0.26
> 5. BBB spread is weakly correlated (0.014)
> 6. VIX has weak correlation (0.06)
> 7. Equity indices have negative correlation but short history
> 
> Given the stress scenario pushes unemployment up (which correlates with higher defaults) and GDP down (correlates with higher defaults), this should increase default rates. But the equity rally and spread compression in the scenario are counter-intuitive for a stress scenario.
> 
> Let me build a model. I'll start with a simple approach and build up.
> 
> Let me first explore more and then build a model



**tool call: python**

```
import pandas as pd
import numpy as np

hist = pd.read_csv('data/train.csv')

# Look at the equity indices more closely
print("SP500 history:")
print(hist[['quarter', 'sp500']].dropna().tail(20))
print("\nDJIA history:")
print(hist[['quarter', 'djia']].dropna().tail(20))
print("\nNASDAQ history:")
print(hist[['quarter', 'nasdaq']].dropna().tail(20))

print("\nHPI history:")
print(hist[['quarter', 'hpi']].dropna().tail(20))

print("\nBBB spread history:")
print(hist[['quarter', 'bbb_spread']].dropna().tail(20))

print("\nVIX history:")
print(hist[['quarter', 'vix']].dropna().tail(20))

print("\nCPI history:")
print(hist[['quarter', 'cpi']].dropna().tail(20))

print("\nUnemployment history (last 20):")
print(hist[['quarter', 'unemployment']].tail(20))

print("\nGDP history (last 20):")
print(hist[['quarter', 'gdp']].tail(20))

print("\nDefault rate last 20:")
print(hist[['quarter', 'default_rate']].tail(20))
```

## [23] tool

SP500 history:
    quarter      sp500
60       61  1281.5162
61       62  1392.0534
62       63  1463.1817
63       64  1462.3159
64       65  1515.6035
65       66  1770.8056
66       67  1902.7272
67       68  1981.7954
68       69  2095.1443
69       70  1911.6976
70       71  2069.3144
71       72  2189.6723
72       73  2317.4319
73       74  2529.5173
74       75  2679.5781
75       76  3004.3140
76       77  3141.8579
77       78  3586.4013
78       79  3721.2305
79       80  3935.6140

DJIA history:
    quarter       djia
60       61   799.1618
61       62   873.2746
62       63   945.6952
63       64   961.3630
64       65  1018.9010
65       66  1137.2796
66       67  1228.1599
67       68  1316.8749
68       69  1365.4637
69       70  1232.1296
70       71  1241.5293
71       72  1340.4850
72       73  1423.9358
73       74  1517.2062
74       75  1643.1474
75       76  1780.3912
76       77  1823.9840
77       78  1970.4456
78       79  2038.1546
79       80  2078.7173

NASDAQ history:
    quarter    nasdaq
60       61  194.2956
61       62  232.1017
62       63  253.7099
63       64  230.6222
64       65  250.8438
65       66  316.7723
66       67  379.4346
67       68  393.8893
68       69  442.5325
69       70  315.1915
70       71  348.9992
71       72  378.3438
72       73  424.5206
73       74  449.5438
74       75  483.7691
75       76  581.3296
76       77  620.4019
77       78  693.4425
78       79  719.6024
79       80  791.2444

HPI history:
    quarter       hpi
60       61  238.2642
61       62  233.3324
62       63  236.4660
63       64  235.5706
64       65  233.7863
65       66  235.8906
66       67  237.8421
67       68  238.9430
68       69  238.0474
69       70  239.3387
70       71  249.8175
71       72  260.8562
72       73  266.4540
73       74  270.6202
74       75  274.4956
75       76  275.7014
76       77  277.4252
77       78  277.6657
78       79  283.0007
79       80  294.2207

BBB spread history:
    quarter  bbb_spread
60       61      4.2020
61       62      3.8229
62       63      3.3457
63       64      3.3292
64       65      3.3621
65       66      2.8606
66       67      2.4957
67       68      2.4582
68       69      1.9757
69       70      5.4367
70       71      1.2092
71       72      1.5097
72       73      1.3110
73       74      1.6933
74       75      1.2745
75       76      1.3683
76       77      1.0414
77       78      1.0927
78       79      1.4688
79       80      1.4962

VIX history:
    quarter      vix
60       61  35.6645
61       62  19.8122
62       63  17.3493
63       64  18.1950
64       65  13.6304
65       66  10.9935
66       67   9.9514
67       68  12.0634
68       69  11.8413
69       70  46.9800
70       71   8.9209
71       72  10.8088
72       73  10.8296
73       74  14.6377
74       75  12.0527
75       76  15.5189
76       77  12.7066
77       78  12.1383
78       79  13.4733
79       80  13.7735

CPI history:
    quarter       cpi
60       61  184.6287
61       62  182.4824
62       63  183.2394
63       64  183.9069
64       65  184.6362
65       66  187.4739
66       67  190.3972
67       68  195.8188
68       69  200.9278
69       70  195.5320
70       71  199.9856
71       72  204.4477
72       73  208.7800
73       74  207.6375
74       75  207.2007
75       76  211.2554
76       77  214.3225
77       78  216.8521
78       79  217.6913
79       80  220.3592

Unemployment history (last 20):
    quarter  unemployment
60       61        4.7681
61       62        4.7699
62       63        3.9368
63       64        5.1822
64       65        4.4165
65       66        4.6095
66       67        3.9044
67       68        4.2379
68       69        5.4831
69       70       11.7893
70       71        4.6315
71       72        5.6393
72       73        5.0728
73       74        5.2269
74       75        5.9145
75       76        5.2783
76       77        5.3464
77       78        5.9160
78       79        6.0062
79       80        5.0024

GDP history (last 20):
    quarter       gdp
60       61  140.3008
61       62  141.2778
62       63  144.0245
63       64  144.3690
64       65  146.1254
65       66  149.9324
66       67  153.5116
67       68  154.8409
68       69  154.4991
69       70  146.4253
70       71  146.7702
71       72  144.3651
72       73  147.7234
73       74  147.7691
74       75  147.5721
75       76  150.5191
76       77  151.2391
77       78  152.4973
78       79  153.9686
79       80  154.2361

Default rate last 20:
    quarter  default_rate
60       61      0.031162
61       62      0.032309
62       63      0.017875
63       64      0.029139
64       65      0.018354
65       66      0.027076
66       67      0.018774
67       68      0.022429
68       69      0.041501
69       70      0.026118
70       71      0.033850
71       72      0.020619
72       73      0.009220
73       74      0.015003
74       75      0.016439
75       76      0.029767
76       77      0.029153
77       78      0.024123
78       79      0.029878
79       80      0.011391


## [24] assistant

**[reasoning]**

> Now I understand the data better. Let me look at the scenario data again and compare with the historical ranges.
> 
> The scenario data (quarters 81-89) has:
> - GDP: declining from 152.6 to 140.3 (historical range ~118-154, so 140 is within historical range but at lower end)
> - Unemployment: rising from 5.2% to 7.4% (historical range ~3.9-13.6%, so 7.4% is within range but elevated)
> - HPI: declining from 288 to 251 (historical range ~138-294, so declining from near peak)
> - BBB spread: rising from 1.6% to 2.5% (historical range ~1.0-5.8%, so within range)
> - SP500: around 3900-4100 (historical range ~687-3935, so near historical highs)
> - DJIA: around 2000-2100 (historical range ~322-2078, so near historical highs)
> - NASDAQ: around 430-730 (historical range ~230-791, so within range)
> - VIX: rising from 14.6 to 21.6 (historical range ~9-60, so moderate)
> - CPI: declining from 219 to 212 (historical range ~111-220, so elevated but declining)
> 
> The scenario seems to be a mild stress scenario: GDP declining, unemployment rising, HPI declining, spreads widening, VIX rising, but equity markets still relatively high and CPI declining.
> 
> Let me now build a model. I'll start with a simple approach and then refine.
> 
> Key considerations:
> 1. Some macro series have missing values early on - I need to handle missing values
> 2. Not all 9 series may be relevant
> 3. Transformations may be needed (e.g., year-over-year changes, logs, etc.)
> 3. The scenario pushes drivers beyond historical range (especially unemployment rising, GDP declining)
> 4. Need prediction intervals reflecting genuine forecast uncertainty
> 
> Let me build a model step by step:
> 1. First, create a clean training dataset handling missing values
> 2. Feature engineering: consider levels, YoY changes, spreads, etc.
> 3. Model selection - I'll try multiple approaches
> 4. Generate predictions with prediction intervals
> 
> Let me start by building a comprehensive modeling script



**tool call: python**

```
import pandas as pd
import numpy as np

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Check scenario data
print("Scenario data:")
print(scenario.to_string())

print("\n\nHistorical ranges:")
for col in ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi', 'default_rate']:
    if col in hist.columns:
        valid = hist[col].dropna()
        print(f"{col}: min={valid.min():.4f}, max={valid.max():.4f}, mean={valid.mean():.4f}, std={valid.std():.4f}")

print("\nScenario ranges:")
for col in scenario.columns:
    if col != 'quarter':
        print(f"{col}: min={scenario[col].min():.4f}, max={scenario[col].max():.4f}")
```

## [25] tool

Scenario data:
   quarter       gdp  unemployment       hpi  bbb_spread      sp500       djia    nasdaq      vix       cpi
0       81  152.6170        5.2237  288.4656      1.6195  3985.1965  2116.6344  734.9770  14.5721  219.3511
1       82  151.0150        5.4547  282.8230      1.7428  3956.7256  2099.4871  682.7109  15.4171  218.3476
2       83  149.4298        5.6959  277.2908      1.8660  4065.7783  2175.5736  634.1615  16.3110  217.3487
3       84  147.8612        5.9478  271.8668      1.9893  4036.9233  2068.6221  589.0647  17.2568  216.3544
4       85  146.3090        6.2109  266.5489      2.1126  4087.7436  2025.2248  547.1747  18.2575  215.3646
5       86  144.7732        6.4855  261.3351      2.2359  4129.8979  2032.0418  508.2637  19.3161  214.3794
6       87  143.2535        6.7724  256.2232      2.3591  4083.4260  2005.5909  472.1198  20.4362  213.3987
7       88  141.7497        7.0719  251.2113      2.4824  4096.7539  1951.5491  438.5461  21.6212  212.4224
8       89  140.2617        7.3846  246.2974      2.6057  3964.5524  1920.6252  407.3600  22.8749  211.4506


Historical ranges:
gdp: min=118.0839, max=154.8409, mean=135.2716, std=9.6306
unemployment: min=3.6095, max=13.6151, mean=6.0855, std=1.7600
hpi: min=138.0913, max=294.2207, mean=205.7182, std=40.7473
bbb_spread: min=1.0414, max=5.9879, mean=2.8650, std=0.9764
sp500: min=654.8223, max=3935.6140, mean=1493.3445, std=881.5075
djia: min=345.9365, max=2078.7173, mean=863.9178, std=528.1587
nasdaq: min=164.7980, max=791.2444, mean=334.3247, std=142.1277
vix: min=8.9209, max=60.7798, mean=21.3747, std=10.5727
cpi: min=111.2378, max=220.3592, mean=154.1486, std=32.7112
default_rate: min=0.0092, max=0.0780, mean=0.0279, std=0.0117

Scenario ranges:
gdp: min=140.2617, max=152.6170
unemployment: min=5.2237, max=7.3846
hpi: min=246.2974, max=288.4656
bbb_spread: min=1.6195, max=2.6057
sp500: min=3956.7256, max=4129.8979
djia: min=1920.6252, max=2175.5736
nasdaq: min=407.3600, max=734.9770
vix: min=14.5721, max=22.8749
cpi: min=211.4506, max=219.3511


## [26] assistant

**[reasoning]**

> Now I have a good understanding of the data. Let me analyze:
> 
> 1. Historical data: 80 quarters (quarters 1-80)
> 2. Scenario data: 9 quarters (quarters 81-89)
> 3. Some macro series have missing values in early quarters (hpi, bbb_spread, sp500, djia, vix start later)
> 4. Scenario pushes drivers beyond historical ranges in some cases (e.g., sp500, djia, nasdaq, cpi are higher than historical max; gdp is near historical max but declining; unemployment rising but within historical range; hpi declining from peak; bbb_spread and vix within range but rising; cpi above historical max)
> 
> Now I need to build a model. Let me think about the approach:
> 
> 1. Handle missing values in historical data (forward fill or interpolation for series that start later)
> 2. Feature engineering: consider levels, changes, YoY changes, etc.
> 3. Model selection: Given the stress scenario pushes beyond historical ranges, I should consider models that don't extrapolate wildly. Tree-based models (Random Forest, XGBoost) don't extrapolate well. Linear models with appropriate transformations might extrapolate more reasonably. Or I could use a Bayesian approach for uncertainty quantification.
> 
> Let me start by building a comprehensive model with proper feature engineering and cross-validation for model selection, then generate predictions with prediction intervals.
> 
> Let me create a comprehensive modeling script.



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.linear_model import Ridge, Lasso, LinearRegression, BayesianRidge, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

# Feature engineering function
def create_features(df, is_train=True):
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    # Original columns
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    # Forward fill missing values for macro series (they start later in history)
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill()
    
    # If still NaN (beginning), backfill
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].bfill()
    
    # Create features
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    # Level features
    for col in macro_cols:
        if col in df.columns:
            features[col] = df[col]
    
    # Quarter-over-quarter changes
    for col in macro_cols:
        if col in df.columns:
            features[f'{col}_qoq'] = df[col].pct_change()
            features[f'{col}_diff'] = df[col].diff()
    
    # Year-over-year changes (4 quarters)
    for col in macro_cols:
        if col in df.columns:
            features[f'{col}_yoy'] = df[col].pct_change(4)
            features[f'{col}_yoy_diff'] = df[col].diff(4)
    
    # Rolling statistics (4-quarter window)
    for col in macro_cols:
        if col in df.columns:
            features[f'{col}_ma4'] = df[col].rolling(4, min_periods=1).mean()
            features[f'{col}_std4'] = df[col].rolling(4, min_periods=1).std()
    
    # Unemployment rate level and change (key for default)
    if 'unemployment' in df.columns:
        features['unemployment_level'] = df['unemployment']
        features['unemployment_qoq'] = df['unemployment'].diff()
        features['unemployment_yoy'] = df['unemployment'].diff(4)
    
    # BBB spread level and change (credit stress indicator)
    if 'bbb_spread' in df.columns:
        features['bbb_spread_level'] = df['bbb_spread']
        features['bbb_spread_qoq'] = df['bbb_spread'].diff()
        features['bbb_spread_yoy'] = df['bbb_spread'].diff(4)
    
    # VIX level and change (volatility/fear)
    if 'vix' in df.columns:
        features['vix_level'] = df['vix']
        features['vix_qoq'] = df['vix'].diff()
        features['vix_yoy'] = df['vix'].diff(4)
    
    # GDP growth
    if 'gdp' in df.columns:
        features['gdp_yoy'] = df['gdp'].pct_change(4)
        features['gdp_qoq'] = df['gdp'].pct_change()
    
    # HPI (house price index) - important for mortgage/default
    if 'hpi' in df.columns:
        features['hpi_yoy'] = df['hpi'].pct_change(4)
        features['hpi_qoq'] = df['hpi'].pct_change()
    
    # Equity market indicators
    if 'sp500' in df.columns:
        features['sp500_yoy'] = df['sp500'].pct_change(4)
        features['sp500_qoq'] = df['sp500'].pct_change()
    if 'nasdaq' in df.columns:
        features['nasdaq_yoy'] = df['nasdaq'].pct_change(4)
        features['nasdaq_qoq'] = df['nasdaq'].pct_change()
    
    # CPI inflation
    if 'cpi' in df.columns:
        features['cpi_yoy'] = df['cpi'].pct_change(4)
        features['cpi_qoq'] = df['cpi'].pct_change()
    
    # Interaction terms: unemployment * bbb_spread (credit stress)
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    
    # VIX * unemployment (stress interaction)
    if 'vix' in df.columns and 'unemployment' in df.columns:
        features['vix_x_unemp'] = df['vix'] * df['unemployment']
    
    # HPI * unemployment (housing stress)
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    
    # Replace inf and large values
    features = features.replace([np.inf, -np.inf], np.nan)
    
    # Forward/back fill remaining NaN
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

# Create features for training data
train_features = create_features(hist, is_train=True)
print("Train features shape:", train_features.shape)
print("Train features columns:", train_features.columns.tolist())
print("\nMissing values in train features:", train_features.isnull().sum().sum())

# Create features for scenario
scenario_features = create_features(scenario, is_train=False)
print("\nScenario features shape:", scenario_features.shape)
print("Scenario features columns:", scenario_features.columns.tolist())
print("\nMissing values in scenario features:", scenario_features.isnull().sum().sum())

# Check alignment of columns
train_cols = set(train_features.columns) - {'default_rate', 'quarter'}
scenario_cols = set(scenario_features.columns) - {'quarter'}
print("\nColumns in train but not scenario:", train_cols - scenario_cols)
print("Columns in scenario but not train:", scenario_cols - train_cols)
```

## [27] tool

Train features shape: (80, 71)
Train features columns: ['quarter', 'gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi', 'gdp_qoq', 'gdp_diff', 'unemployment_qoq', 'unemployment_diff', 'hpi_qoq', 'hpi_diff', 'bbb_spread_qoq', 'bbb_spread_diff', 'sp500_qoq', 'sp500_diff', 'djia_qoq', 'djia_diff', 'nasdaq_qoq', 'nasdaq_diff', 'vix_qoq', 'vix_diff', 'cpi_qoq', 'cpi_diff', 'gdp_yoy', 'gdp_yoy_diff', 'unemployment_yoy', 'unemployment_yoy_diff', 'hpi_yoy', 'hpi_yoy_diff', 'bbb_spread_yoy', 'bbb_spread_yoy_diff', 'sp500_yoy', 'sp500_yoy_diff', 'djia_yoy', 'djia_yoy_diff', 'nasdaq_yoy', 'nasdaq_yoy_diff', 'vix_yoy', 'vix_yoy_diff', 'cpi_yoy', 'cpi_yoy_diff', 'gdp_ma4', 'gdp_std4', 'unemployment_ma4', 'unemployment_std4', 'hpi_ma4', 'hpi_std4', 'bbb_spread_ma4', 'bbb_spread_std4', 'sp500_ma4', 'sp500_std4', 'djia_ma4', 'djia_std4', 'nasdaq_ma4', 'nasdaq_std4', 'vix_ma4', 'vix_std4', 'cpi_ma4', 'cpi_std4', 'unemployment_level', 'bbb_spread_level', 'vix_level', 'unemp_x_spread', 'vix_x_unemp', 'hpi_x_unemp', 'default_rate']

Missing values in train features: 0

Scenario features shape: (9, 70)
Scenario features columns: ['quarter', 'gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi', 'gdp_qoq', 'gdp_diff', 'unemployment_qoq', 'unemployment_diff', 'hpi_qoq', 'hpi_diff', 'bbb_spread_qoq', 'bbb_spread_diff', 'sp500_qoq', 'sp500_diff', 'djia_qoq', 'djia_diff', 'nasdaq_qoq', 'nasdaq_diff', 'vix_qoq', 'vix_diff', 'cpi_qoq', 'cpi_diff', 'gdp_yoy', 'gdp_yoy_diff', 'unemployment_yoy', 'unemployment_yoy_diff', 'hpi_yoy', 'hpi_yoy_diff', 'bbb_spread_yoy', 'bbb_spread_yoy_diff', 'sp500_yoy', 'sp500_yoy_diff', 'djia_yoy', 'djia_yoy_diff', 'nasdaq_yoy', 'nasdaq_yoy_diff', 'vix_yoy', 'vix_yoy_diff', 'cpi_yoy', 'cpi_yoy_diff', 'gdp_ma4', 'gdp_std4', 'unemployment_ma4', 'unemployment_std4', 'hpi_ma4', 'hpi_std4', 'bbb_spread_ma4', 'bbb_spread_std4', 'sp500_ma4', 'sp500_std4', 'djia_ma4', 'djia_std4', 'nasdaq_ma4', 'nasdaq_std4', 'vix_ma4', 'vix_std4', 'cpi_ma4', 'cpi_std4', 'unemployment_level', 'bbb_spread_level', 'vix_level', 'unemp_x_spread', 'vix_x_unemp', 'hpi_x_unemp']

Missing values in scenario features: 0

Columns in train but not scenario: set()
Columns in scenario but not train: set()


## [28] assistant

**[reasoning]**

> Good, the features are aligned. Now let me build a model. Given that the scenario pushes drivers beyond historical ranges, I need a model that extrapolates well. Linear models with regularization tend to extrapolate better than tree-based models. I'll use Bayesian Ridge regression which provides prediction intervals naturally, and also try other models for comparison.
> 
> Let me build a modeling pipeline with cross-validation to select the best model and generate prediction intervals.



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score, cross_val_predict
from sklearn.linear_model import Ridge, Lasso, LinearRegression, BayesianRidge, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

def create_features(df, is_train=True):
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    # Core macro variables - levels
    for col in macro_cols:
        if col in df.columns:
            features[col] = df[col]
    
    # Key transformations: YoY changes (more stable for stress testing)
    for col in macro_cols:
        if col in df.columns:
            features[f'{col}_yoy'] = df[col].pct_change(4)
            features[f'{col}_diff4'] = df[col].diff(4)
    
    # QoQ changes
    for col in macro_cols:
        if col in df.columns:
            features[f'{col}_qoq'] = df[col].pct_change()
            features[f'{col}_diff1'] = df[col].diff()
    
    # Key level features for default modeling
    key_levels = ['unemployment', 'bbb_spread', 'vix', 'hpi', 'gdp']
    for col in key_levels:
        if col in df.columns:
            features[f'{col}_level'] = df[col]
    
    # Interactions (stress indicators)
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    if 'unemployment' in df.columns and 'vix' in df.columns:
        features['unemp_x_vix'] = df['unemployment'] * df['vix']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    if 'gdp' in df.columns and 'unemployment' in df.columns:
        features['gdp_x_unemp'] = df['gdp'] * df['unemployment']
    
    # Rolling stats (4-quarter)
    for col in macro_cols:
        if col in df.columns:
            features[f'{col}_ma4'] = df[col].rolling(4, min_periods=1).mean()
            features[f'{col}_std4'] = df[col].rolling(4, min_periods=1).std()
    
    # Replace inf and fill na
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

train_feat = create_features(hist, is_train=True)
scenario_feat = create_features(scenario, is_train=False)

# Prepare X, y
X = train_feat.drop(['quarter', 'default_rate'], axis=1)
y = train_feat['default_rate']
X_scenario = scenario_feat.drop(['quarter'], axis=1)

print("X shape:", X.shape)
print("y shape:", y.shape)
print("X_scenario shape:", X_scenario.shape)

# Check for any remaining NaN
print("NaN in X:", X.isnull().sum().sum())
print("NaN in X_scenario:", X_scenario.isnull().sum().sum())

# Feature selection: remove low-variance and highly correlated features
from sklearn.feature_selection import VarianceThreshold
from sklearn.linear_model import LassoCV

# Remove near-zero variance features
selector = VarianceThreshold(threshold=1e-6)
X_var = selector.fit_transform(X)
kept_features = X.columns[selector.get_support()]
print(f"\nFeatures after variance threshold: {len(kept_features)}")

X = X[kept_features]
X_scenario = X_scenario[kept_features]

# Correlation-based feature selection
corr_matrix = X.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [column for column in upper.columns if any(upper[column] > 0.98)]
print(f"Features to drop due to high correlation: {to_drop}")
X = X.drop(columns=to_drop)
X_scenario = X_scenario.drop(columns=to_drop)
print(f"Features after correlation filtering: {X.shape[1]}")

# Use LassoCV for feature selection
lasso_cv = LassoCV(cv=TimeSeriesSplit(n_splits=5), random_state=42, max_iter=10000)
lasso_cv.fit(X, y)
selected_features = X.columns[lasso_cv.coef_ != 0]
print(f"\nFeatures selected by LassoCV: {len(selected_features)}")
print("Selected features:", list(selected_features))
print("Lasso alpha:", lasso_cv.alpha_)

X_sel = X[selected_features]
X_scenario_sel = X_scenario[selected_features]

# Check scenario feature values vs training range
print("\n--- Scenario feature range check ---")
for col in selected_features:
    train_min, train_max = X_sel[col].min(), X_sel[col].max()
    scen_min, scen_max = X_scenario_sel[col].min(), X_scenario_sel[col].max()
    if scen_min < train_min or scen_max > train_max:
        print(f"  {col}: train=[{train_min:.4f}, {train_max:.4f}], scenario=[{scen_min:.4f}, {scen_max:.4f}] *** OUT OF SAMPLE ***")
    else:
        print(f"  {col}: train=[{train_min:.4f}, {train_max:.4f}], scenario=[{scen_min:.4f}, {scen_max:.4f}] OK")
```

## [29] tool

X shape: (80, 72)
y shape: (80,)
X_scenario shape: (9, 72)
NaN in X: 0
NaN in X_scenario: 0

Features after variance threshold: 72
Features to drop due to high correlation: ['djia', 'cpi', 'gdp_diff4', 'gdp_diff1', 'unemployment_level', 'bbb_spread_level', 'vix_level', 'hpi_level', 'gdp_level', 'hpi_ma4', 'sp500_ma4', 'djia_ma4', 'cpi_ma4']
Features after correlation filtering: 59

Features selected by LassoCV: 2
Selected features: ['sp500', 'gdp_x_unemp']
Lasso alpha: 0.7414536458670898

--- Scenario feature range check ---
  sp500: train=[654.8223, 3935.6140], scenario=[3956.7256, 4129.8979] *** OUT OF SAMPLE ***
  gdp_x_unemp: train=[470.8134, 1820.5635], scenario=[797.2254, 1035.7765] OK


## [30] assistant

**[reasoning]**

> The LassoCV selected only 2 features: sp500 and gdp_x_unemp. But sp500 in the scenario is way out of sample (3956-4129 vs training max 3935). This is a problem - the scenario pushes SP500 way beyond historical levels (it jumps from ~3935 to ~4000+). Let me look at the scenario data more carefully.
> 
> Looking at the scenario data, sp500 jumps from ~3935 (quarter 80) to ~3985 (quarter 81) - not a huge jump. But then it goes up to 4129 by quarter 86, then drops to 4096 by quarter 89. So it's moderately out of sample.
> 
> Actually, looking at the historical data, sp500 goes up to 3935 in quarter 80. The scenario has it at 3985-4129, so it's about 1.2-5% higher. Not a huge extrapolation.
> 
> But the LassoCV only selecting 2 features is too aggressive. Let me try a more robust approach with multiple models and use Bayesian Ridge or similar for prediction intervals. Let me also consider using more features selected by other methods.



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.linear_model import Ridge, Lasso, LinearRegression, BayesianRidge, ElasticNet, RidgeCV, LassoCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

def create_features(df, is_train=True):
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    # Core macro variables - levels
    for col in macro_cols:
        if col in df.columns:
            features[col] = df[col]
    
    # YoY changes (4-quarter) - more stable for stress testing
    for col in macro_cols:
        if col in df.columns:
            features[f'{col}_yoy'] = df[col].pct_change(4)
            features[f'{col}_diff4'] = df[col].diff(4)
    
    # QoQ changes
    for col in macro_cols:
        if col in df.columns:
            features[f'{col}_qoq'] = df[col].pct_change()
            features[f'{col}_diff1'] = df[col].diff()
    
    # Key level features
    key_levels = ['unemployment', 'bbb_spread', 'vix', 'hpi', 'gdp']
    for col in key_levels:
        if col in df.columns:
            features[f'{col}_level'] = df[col]
    
    # Interactions
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    if 'unemployment' in df.columns and 'vix' in df.columns:
        features['unemp_x_vix'] = df['unemployment'] * df['vix']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    if 'gdp' in df.columns and 'unemployment' in df.columns:
        features['gdp_x_unemp'] = df['gdp'] * df['unemployment']
    
    # Rolling stats (4-quarter)
    for col in macro_cols:
        if col in df.columns:
            features[f'{col}_ma4'] = df[col].rolling(4, min_periods=1).mean()
            features[f'{col}_std4'] = df[col].rolling(4, min_periods=1).std()
    
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

train_feat = create_features(hist, is_train=True)
scenario_feat = create_features(scenario, is_train=False)

X = train_feat.drop(['quarter', 'default_rate'], axis=1)
y = train_feat['default_rate']
X_scenario = scenario_feat.drop(['quarter'], axis=1)

# Feature selection - more conservative
selector = VarianceThreshold(threshold=1e-6)
X_var = selector.fit_transform(X)
kept_features = X.columns[selector.get_support()]
X = X[kept_features]
X_scenario = X_scenario[kept_features]

# Remove highly correlated
corr_matrix = X.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [column for column in upper.columns if any(upper[column] > 0.98)]
X = X.drop(columns=to_drop)
X_scenario = X_scenario.drop(columns=to_drop)

# Use SelectKBest with f_regression to get top features
k = min(20, X.shape[1])
selector_k = SelectKBest(f_regression, k=k)
X_k = selector_k.fit_transform(X, y)
selected_features = X.columns[selector_k.get_support()]
print(f"Top {k} features by f_regression:")
for feat in selected_features:
    print(f"  {feat}")

X_sel = X[selected_features]
X_scenario_sel = X_scenario[selected_features]

# Check scenario ranges
print("\n--- Scenario range check ---")
for col in selected_features:
    train_min, train_max = X_sel[col].min(), X_sel[col].max()
    scen_min, scen_max = X_scenario_sel[col].min(), X_scenario_sel[col].max()
    if scen_min < train_min or scen_max > train_max:
        print(f"  {col}: train=[{train_min:.4f}, {train_max:.4f}], scenario=[{scen_min:.4f}, {scen_max:.4f}] *** OUT OF SAMPLE ***")
    else:
        print(f"  {col}: train=[{train_min:.4f}, {train_max:.4f}], scenario=[{scen_min:.4f}, {scen_max:.4f}] OK")
```

## [31] tool

Top 20 features by f_regression:
  gdp
  unemployment
  hpi
  sp500
  unemployment_yoy
  unemployment_diff4
  hpi_yoy
  hpi_diff4
  hpi_qoq
  hpi_diff1
  gdp_x_unemp
  gdp_ma4
  gdp_std4
  unemployment_ma4
  hpi_std4
  bbb_spread_std4
  sp500_std4
  djia_std4
  nasdaq_std4
  vix_std4

--- Scenario range check ---
  gdp: train=[118.0839, 154.8409], scenario=[140.2617, 152.6170] OK
  unemployment: train=[3.6095, 13.6151], scenario=[5.2237, 7.3846] OK
  hpi: train=[138.0913, 294.2207], scenario=[246.2974, 288.4656] OK
  sp500: train=[654.8223, 3935.6140], scenario=[3956.7256, 4129.8979] *** OUT OF SAMPLE ***
  unemployment_yoy: train=[-0.7101, 1.5576], scenario=[0.1890, 0.1890] OK
  unemployment_diff4: train=[-9.1926, 8.2881], scenario=[0.9872, 1.1737] OK
  hpi_yoy: train=[-0.0357, 0.1307], scenario=[-0.0760, -0.0760] *** OUT OF SAMPLE ***
  hpi_diff4: train=[-6.4238, 31.2815], scenario=[-21.9167, -20.2515] *** OUT OF SAMPLE ***
  hpi_qoq: train=[-0.0207, 0.0460], scenario=[-0.0196, -0.0196] OK
  hpi_diff1: train=[-4.9318, 11.2200], scenario=[-5.6426, -4.9139] *** OUT OF SAMPLE ***
  gdp_x_unemp: train=[470.8134, 1820.5635], scenario=[797.2254, 1035.7765] OK
  gdp_ma4: train=[118.0839, 153.1960], scenario=[142.5095, 152.6170] OK
  gdp_std4: train=[0.1814, 4.6647], scenario=[1.1328, 2.0466] OK
  unemployment_ma4: train=[3.9487, 8.7760], scenario=[5.2237, 6.9286] OK
  hpi_std4: train=[0.0000, 12.0347], scenario=[3.9899, 7.1432] OK
  bbb_spread_std4: train=[0.0000, 2.0505], scenario=[0.0872, 0.1592] OK
  sp500_std4: train=[0.0000, 376.0371], scenario=[20.1320, 72.1013] OK
  djia_std4: train=[0.0000, 154.8593], scenario=[12.1250, 69.4698] OK
  nasdaq_std4: train=[2.2362, 146.0515], scenario=[36.9577, 62.8134] OK
  vix_std4: train=[0.0000, 23.6602], scenario=[0.5975, 1.5318] OK


## [32] assistant

**[reasoning]**

> Several key features are out of sample in the scenario:
> - sp500: scenario goes higher than historical max (3935 -> 4129)
> - hpi_yoy: scenario has -7.6% YoY decline, more severe than historical min (-3.6%)
> - hpi_diff4: scenario has larger 4-quarter decline than historical
> - hpi_diff1: scenario has larger quarterly decline than historical
> 
> The scenario is indeed a stress scenario with declining HPI and rising SP500 (which is unusual - typically stress would have declining equities).
> 
> Let me think about this more carefully. The scenario has:
> - GDP declining from 152 to 140 (within historical range)
> - Unemployment rising from 5.2% to 7.4% (within historical range)
> - HPI declining from 288 to 246 (within historical range but the YoY decline is steeper)
> - BBB spread rising from 1.6% to 2.6% (within range)
> - SP500 rising from 3985 to 4129 (above historical max of 3935)
> - VIX rising from 14.6 to 22.9 (within range)
> - CPI declining from 219 to 211 (within range)
> 
> The equity market rising in a stress scenario is unusual. This might be a "soft landing" or "stagflation" type scenario where equities still rise but economy deteriorates.
> 
> Let me build a more robust model that can handle out-of-sample extrapolation. I'll use:
> 1. A model with features that are within historical ranges in the scenario
> 2. Bayesian Ridge Regression for prediction intervals
> 3. Maybe ensemble with other models
> 
> Let me also consider transformations that might handle the out-of-sample better, like using percentiles/ranks or log transforms.
> 
> Actually, let me think about this differently. The default rate is a fraction (0-1), typically small (0.9% to 7.8%). A linear model on raw default rate might produce negative predictions or values >1. I should consider a logit or log transformation.
> 
> Also, the scenario is a stress scenario - GDP falling, unemployment rising, HPI falling, spreads widening. These should drive default rates UP. But equities rising would drive defaults DOWN (if equities are negatively correlated with defaults). The net effect is unclear.
> 
> Let me build a proper model with prediction intervals using Bayesian Ridge or Quantile Regression.



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.linear_model import Ridge, Lasso, LinearRegression, BayesianRidge, ElasticNet, RidgeCV, LassoCV, QuantileRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, QuantileTransformer, PowerTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

def create_features(df, is_train=True):
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    # Key macro variables - focus on ones that are in-scenario-range
    key_vars = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'vix', 'cpi']
    for col in key_vars:
        if col in df.columns:
            features[col] = df[col]
    
    # Equity indices - use log to handle out-of-sample better
    for col in ['sp500', 'djia', 'nasdaq']:
        if col in df.columns:
            features[f'log_{col}'] = np.log(df[col] + 1)
            features[f'{col}_yoy'] = df[col].pct_change(4)
    
    # YoY changes (more stable for stress)
    for col in key_vars:
        if col in df.columns:
            features[f'{col}_yoy'] = df[col].pct_change(4)
            features[f'{col}_diff4'] = df[col].diff(4)
    
    # Key level features (unemployment, spreads, vix are mean-reverting)
    for col in ['unemployment', 'bbb_spread', 'vix']:
        if col in df.columns:
            features[f'{col}_level'] = df[col]
    
    # Interactions that make economic sense
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    if 'unemployment' in df.columns and 'vix' in df.columns:
        features['unemp_x_vix'] = df['unemployment'] * df['vix']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    if 'gdp' in df.columns and 'unemployment' in df.columns:
        features['gdp_x_unemp'] = df['gdp'] * df['unemployment']
    
    # GDP growth
    if 'gdp' in df.columns:
        features['gdp_growth_yoy'] = df['gdp'].pct_change(4)
        features['gdp_growth_qoq'] = df['gdp'].pct_change()
    
    # Unemployment change (key driver)
    if 'unemployment' in df.columns:
        features['unemp_change_yoy'] = df['unemployment'].diff(4)
        features['unemp_change_qoq'] = df['unemployment'].diff()
    
    # HPI change (key for mortgage defaults)
    if 'hpi' in df.columns:
        features['hpi_change_yoy'] = df['hpi'].pct_change(4)
        features['hpi_change_qoq'] = df['hpi'].pct_change()
    
    # Rolling stats (4Q)
    for col in key_vars + ['sp500', 'djia', 'nasdaq']:
        if col in df.columns:
            features[f'{col}_ma4'] = df[col].rolling(4, min_periods=1).mean()
            features[f'{col}_std4'] = df[col].rolling(4, min_periods=1).std()
    
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

train_feat = create_features(hist, is_train=True)
scenario_feat = create_features(scenario, is_train=False)

X = train_feat.drop(['quarter', 'default_rate'], axis=1)
y = train_feat['default_rate']
X_scenario = scenario_feat.drop(['quarter'], axis=1)

# Feature selection
selector = VarianceThreshold(threshold=1e-8)
X_var = selector.fit_transform(X)
kept = X.columns[selector.get_support()]
X = X[kept]
X_scenario = X_scenario[kept]

# Correlation filter
corr_matrix = X.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [c for c in upper.columns if any(upper[c] > 0.95)]
X = X.drop(columns=to_drop)
X_scenario = X_scenario.drop(columns=to_drop)

# Select top 15 features by f_regression
k = min(15, X.shape[1])
selector_k = SelectKBest(f_regression, k=k)
X_k = selector_k.fit_transform(X, y)
selected = X.columns[selector_k.get_support()]
X_sel = X[selected]
X_scenario_sel = X_scenario[selected]

print(f"Selected {len(selected)} features:")
for f in selected:
    print(f"  {f}")

# Check scenario ranges
print("\nScenario range check:")
for col in selected:
    tmin, tmax = X_sel[col].min(), X_sel[col].max()
    smin, smax = X_scenario_sel[col].min(), X_scenario_sel[col].max()
    oos = " *** OOS ***" if smin < tmin or smax > tmax else " OK"
    print(f"  {col}: train=[{tmin:.4f}, {tmax:.4f}], scen=[{smin:.4f}, {smax:.4f}]{oos}")

# Quick CV with Ridge
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sel)
X_scen_scaled = scaler.transform(X_scenario_sel)

tscv = TimeSeriesSplit(n_splits=5)
ridge = Ridge(alpha=1.0)
cv_scores = cross_val_score(ridge, X_scaled, y, cv=tscv, scoring='neg_mean_squared_error')
print(f"\nRidge CV RMSE: {np.sqrt(-cv_scores.mean()):.6f} (+/- {np.sqrt(-cv_scores).std():.6f})")

# Bayesian Ridge for prediction intervals
br = BayesianRidge()
br.fit(X_scaled, y)
print(f"Bayesian Ridge R^2: {br.score(X_scaled, y):.4f}")

# Predict on scenario
y_pred = br.predict(X_scen_scaled)
print(f"\nScenario predictions (Bayesian Ridge):")
for i, q in enumerate(scenario['quarter']):
    print(f"  Q{q}: {y_pred[i]:.6f}")
```

## [33] tool

Selected 15 features:
  gdp
  unemployment
  hpi
  log_sp500
  unemployment_yoy
  unemployment_diff4
  hpi_yoy
  unemp_x_spread
  unemp_change_qoq
  hpi_change_qoq
  gdp_std4
  unemployment_ma4
  hpi_std4
  bbb_spread_std4
  nasdaq_std4

Scenario range check:
  gdp: train=[118.0839, 154.8409], scen=[140.2617, 152.6170] OK
  unemployment: train=[3.6095, 13.6151], scen=[5.2237, 7.3846] OK
  hpi: train=[138.0913, 294.2207], scen=[246.2974, 288.4656] OK
  log_sp500: train=[6.4859, 8.2781], scen=[8.2834, 8.3263] *** OOS ***
  unemployment_yoy: train=[-0.7101, 1.5576], scen=[0.1890, 0.1890] OK
  unemployment_diff4: train=[-9.1926, 8.2881], scen=[0.9872, 1.1737] OK
  hpi_yoy: train=[-0.0357, 0.1307], scen=[-0.0760, -0.0760] *** OOS ***
  unemp_x_spread: train=[5.5677, 76.4175], scen=[8.4598, 19.2421] OK
  unemp_change_qoq: train=[-8.3043, 6.7831], scen=[0.2310, 0.3127] OK
  hpi_change_qoq: train=[-0.0207, 0.0460], scen=[-0.0196, -0.0196] OK
  gdp_std4: train=[0.1814, 4.6647], scen=[1.1328, 2.0466] OK
  unemployment_ma4: train=[3.9487, 8.7760], scen=[5.2237, 6.9286] OK
  hpi_std4: train=[0.0000, 12.0347], scen=[3.9899, 7.1432] OK
  bbb_spread_std4: train=[0.0000, 2.0505], scen=[0.0872, 0.1592] OK
  nasdaq_std4: train=[2.2362, 146.0515], scen=[36.9577, 62.8134] OK

Ridge CV RMSE: 0.014892 (+/- 0.005202)
Bayesian Ridge R^2: 0.3495

Scenario predictions (Bayesian Ridge):
  Q81: 0.028578
  Q82: 0.028900
  Q83: 0.026978
  Q84: 0.025161
  Q85: 0.026011
  Q86: 0.026882
  Q87: 0.027765
  Q88: 0.028648
  Q89: 0.029551


## [34] assistant

**[reasoning]**

> The Bayesian Ridge gives predictions around 2.5-3.0% default rate for the scenario. The R^2 is only 0.35, which is not great. Let me try a more robust approach with better feature engineering and prediction intervals. I should also consider:
> 
> 1. Using a logit or log transformation of default_rate since it's a fraction
> 2. Using Quantile Regression for prediction intervals
> 3. Ensemble methods
> 4. Better feature selection
> 
> Let me also look at the scenario more carefully - the scenario has unemployment rising from 5.2% to 7.4%, GDP declining from 152 to 140, HPI declining, BBB spread rising, VIX rising. These are stress conditions that should increase default rates. But the SP500 is rising which is counterintuitive.
> 
> Let me build a more sophisticated model with prediction intervals.



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_predict
from sklearn.linear_model import Ridge, BayesianRidge, QuantileRegressor, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, StackingRegressor
from sklearn.preprocessing import StandardScaler, QuantileTransformer, PowerTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

def create_features_v2(df, is_train=True):
    """Enhanced feature engineering with transformations for better extrapolation"""
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    # ===== CORE MACRO VARIABLES =====
    # Unemployment - key driver of defaults
    if 'unemployment' in df.columns:
        u = df['unemployment']
        features['unemployment'] = u
        features['unemp_yoy'] = u.diff(4)
        features['unemp_qoq'] = u.diff()
        features['unemp_ma4'] = u.rolling(4, min_periods=1).mean()
        features['unemp_std4'] = u.rolling(4, min_periods=1).std()
        # Unemployment gap from trend
        features['unemp_gap'] = u - u.rolling(8, min_periods=1).mean()
    
    # BBB spread - credit stress
    if 'bbb_spread' in df.columns:
        s = df['bbb_spread']
        features['bbb_spread'] = s
        features['spread_yoy'] = s.diff(4)
        features['spread_qoq'] = s.diff()
        features['spread_ma4'] = s.rolling(4, min_periods=1).mean()
    
    # VIX - market stress
    if 'vix' in df.columns:
        v = df['vix']
        features['vix'] = v
        features['vix_yoy'] = v.diff(4)
        features['vix_qoq'] = v.diff()
        features['vix_ma4'] = v.rolling(4, min_periods=1).mean()
    
    # GDP - economic activity
    if 'gdp' in df.columns:
        g = df['gdp']
        features['gdp'] = g
        features['gdp_yoy'] = g.pct_change(4)
        features['gdp_qoq'] = g.pct_change()
        features['gdp_ma4'] = g.rolling(4, min_periods=1).mean()
        features['gdp_gap'] = g - g.rolling(8, min_periods=1).mean()
    
    # HPI - housing collateral
    if 'hpi' in df.columns:
        h = df['hpi']
        features['hpi'] = h
        features['hpi_yoy'] = h.pct_change(4)
        features['hpi_qoq'] = h.pct_change()
        features['hpi_ma4'] = h.rolling(4, min_periods=1).mean()
        features['hpi_gap'] = h - h.rolling(8, min_periods=1).mean()
    
    # CPI - inflation
    if 'cpi' in df.columns:
        c = df['cpi']
        features['cpi'] = c
        features['cpi_yoy'] = c.pct_change(4)
        features['cpi_qoq'] = c.pct_change()
    
    # Equity indices - use log for better extrapolation
    for col in ['sp500', 'djia', 'nasdaq']:
        if col in df.columns:
            features[f'log_{col}'] = np.log(df[col] + 1)
            features[f'{col}_yoy'] = df[col].pct_change(4)
    
    # ===== KEY INTERACTIONS (stress indicators) =====
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    if 'unemployment' in df.columns and 'vix' in df.columns:
        features['unemp_x_vix'] = df['unemployment'] * df['vix']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    if 'gdp' in df.columns and 'unemployment' in df.columns:
        features['gdp_x_unemp'] = df['gdp'] * df['unemployment']
    # Housing stress: HPI decline * unemployment rise
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_change_x_unemp'] = df['hpi'].pct_change(4) * df['unemployment'].diff(4)
    
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

train_feat = create_features_v2(hist, is_train=True)
scenario_feat = create_features_v2(scenario, is_train=False)

X = train_feat.drop(['quarter', 'default_rate'], axis=1)
y = train_feat['default_rate']
X_scenario = scenario_feat.drop(['quarter'], axis=1)

# Feature selection
selector = VarianceThreshold(threshold=1e-8)
X_var = selector.fit_transform(X)
kept = X.columns[selector.get_support()]
X = X[kept]
X_scenario = X_scenario[kept]

# Correlation filter
corr_matrix = X.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [c for c in upper.columns if any(upper[c] > 0.95)]
X = X.drop(columns=to_drop)
X_scenario = X_scenario.drop(columns=to_drop)

# Select top features
k = min(15, X.shape[1])
selector_k = SelectKBest(f_regression, k=k)
X_k = selector_k.fit_transform(X, y)
selected = X.columns[selector_k.get_support()]
X_sel = X[selected]
X_scenario_sel = X_scenario[selected]

print(f"Selected {len(selected)} features:")
for f in selected:
    print(f"  {f}")

# Check scenario ranges
print("\nScenario range check:")
for col in selected:
    tmin, tmax = X_sel[col].min(), X_sel[col].max()
    smin, smax = X_scenario_sel[col].min(), X_scenario_sel[col].max()
    oos = " *** OOS ***" if smin < tmin or smax > tmax else " OK"
    print(f"  {col}: train=[{tmin:.4f}, {tmax:.4f}], scen=[{smin:.4f}, {smax:.4f}]{oos}")
```

## [35] tool

Selected 15 features:
  unemployment
  unemp_yoy
  unemp_qoq
  unemp_ma4
  unemp_std4
  unemp_gap
  gdp
  hpi
  hpi_yoy
  hpi_qoq
  hpi_gap
  log_sp500
  unemp_x_spread
  hpi_x_unemp
  hpi_change_x_unemp

Scenario range check:
  unemployment: train=[3.6095, 13.6151], scen=[5.2237, 7.3846] OK
  unemp_yoy: train=[-9.1926, 8.2881], scen=[0.9872, 1.1737] OK
  unemp_qoq: train=[-8.3043, 6.7831], scen=[0.2310, 0.3127] OK
  unemp_ma4: train=[3.9487, 8.7760], scen=[5.2237, 6.9286] OK
  unemp_std4: train=[0.2055, 4.1954], scen=[0.1633, 0.3870] *** OOS ***
  unemp_gap: train=[-2.9230, 6.6060], scen=[0.0000, 1.0066] OK
  gdp: train=[118.0839, 154.8409], scen=[140.2617, 152.6170] OK
  hpi: train=[138.0913, 294.2207], scen=[246.2974, 288.4656] OK
  hpi_yoy: train=[-0.0357, 0.1307], scen=[-0.0760, -0.0760] *** OOS ***
  hpi_qoq: train=[-0.0207, 0.0460], scen=[-0.0196, -0.0196] OK
  hpi_gap: train=[-4.0724, 20.5553], scen=[-18.2593, 0.0000] *** OOS ***
  log_sp500: train=[6.4859, 8.2781], scen=[8.2834, 8.3263] *** OOS ***
  unemp_x_spread: train=[5.5677, 76.4175], scen=[8.4598, 19.2421] OK
  hpi_x_unemp: train=[643.5055, 2821.6357], scen=[1506.8578, 1818.8078] OK
  hpi_change_x_unemp: train=[-0.8577, 0.3017], scen=[-0.0892, -0.0750] OK


## [36] assistant

**[reasoning]**

> I see several features are out of sample in the scenario. The key out-of-sample features are:
> - unemp_std4 (scenario has lower unemployment volatility)
> - hpi_yoy (scenario has -7.6% YoY HPI decline, worse than historical -3.6%)
> - hpi_gap (scenario has more negative gap)
> - log_sp500 (scenario has higher SP500 than historical max)
> 
> This is a stress scenario - HPI declining sharply, SP500 at all-time highs, unemployment rising but with low volatility.
> 
> Now let me build models with proper prediction intervals. I'll use:
> 1. Quantile Regression for prediction intervals
> 2. Bootstrap/Bagging for uncertainty
> 3. Bayesian Ridge for analytical intervals
> 4. Conformal prediction for coverage guarantees
> 
> Let me create a comprehensive modeling script



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_predict
from sklearn.linear_model import Ridge, BayesianRidge, QuantileRegressor, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, PowerTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

def create_features_final(df, is_train=True):
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    # Core variables
    if 'unemployment' in df.columns:
        u = df['unemployment']
        features['unemployment'] = u
        features['unemp_yoy'] = u.diff(4)
        features['unemp_qoq'] = u.diff()
        features['unemp_ma4'] = u.rolling(4, min_periods=1).mean()
        features['unemp_std4'] = u.rolling(4, min_periods=1).std()
        features['unemp_gap'] = u - u.rolling(8, min_periods=1).mean()
    
    if 'bbb_spread' in df.columns:
        s = df['bbb_spread']
        features['bbb_spread'] = s
        features['spread_yoy'] = s.diff(4)
        features['spread_qoq'] = s.diff()
        features['spread_ma4'] = s.rolling(4, min_periods=1).mean()
    
    if 'vix' in df.columns:
        v = df['vix']
        features['vix'] = v
        features['vix_yoy'] = v.diff(4)
        features['vix_qoq'] = v.diff()
        features['vix_ma4'] = v.rolling(4, min_periods=1).mean()
    
    if 'gdp' in df.columns:
        g = df['gdp']
        features['gdp'] = g
        features['gdp_yoy'] = g.pct_change(4)
        features['gdp_qoq'] = g.pct_change()
        features['gdp_ma4'] = g.rolling(4, min_periods=1).mean()
        features['gdp_gap'] = g - g.rolling(8, min_periods=1).mean()
    
    if 'hpi' in df.columns:
        h = df['hpi']
        features['hpi'] = h
        features['hpi_yoy'] = h.pct_change(4)
        features['hpi_qoq'] = h.pct_change()
        features['hpi_ma4'] = h.rolling(4, min_periods=1).mean()
        features['hpi_gap'] = h - h.rolling(8, min_periods=1).mean()
    
    if 'cpi' in df.columns:
        c = df['cpi']
        features['cpi'] = c
        features['cpi_yoy'] = c.pct_change(4)
        features['cpi_qoq'] = c.pct_change()
    
    for col in ['sp500', 'djia', 'nasdaq']:
        if col in df.columns:
            features[f'log_{col}'] = np.log(df[col] + 1)
            features[f'{col}_yoy'] = df[col].pct_change(4)
    
    # Key interactions
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    if 'unemployment' in df.columns and 'vix' in df.columns:
        features['unemp_x_vix'] = df['unemployment'] * df['vix']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    if 'gdp' in df.columns and 'unemployment' in df.columns:
        features['gdp_x_unemp'] = df['gdp'] * df['unemployment']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_change_x_unemp'] = df['hpi'].pct_change(4) * df['unemployment'].diff(4)
    
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

train_feat = create_features_final(hist, is_train=True)
scenario_feat = create_features_final(scenario, is_train=False)

X = train_feat.drop(['quarter', 'default_rate'], axis=1)
y = train_feat['default_rate']
X_scenario = scenario_feat.drop(['quarter'], axis=1)

# Feature selection
selector = VarianceThreshold(threshold=1e-8)
X_var = selector.fit_transform(X)
kept = X.columns[selector.get_support()]
X = X[kept]
X_scenario = X_scenario[kept]

# Correlation filter
corr_matrix = X.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [c for c in upper.columns if any(upper[c] > 0.95)]
X = X.drop(columns=to_drop)
X_scenario = X_scenario.drop(columns=to_drop)

# Select top features
k = min(15, X.shape[1])
selector_k = SelectKBest(f_regression, k=k)
X_k = selector_k.fit_transform(X, y)
selected = X.columns[selector_k.get_support()]
X_sel = X[selected]
X_scenario_sel = X_scenario[selected]

print(f"Selected features ({len(selected)}): {list(selected)}")

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sel)
X_scen_scaled = scaler.transform(X_scenario_sel)

# ===== MODEL 1: Bayesian Ridge (analytical prediction intervals) =====
print("\n=== Bayesian Ridge ===")
br = BayesianRidge(alpha_1=1e-6, alpha_2=1e-6, lambda_1=1e-6, lambda_2=1e-6)
br.fit(X_scaled, y)

y_pred_br = br.predict(X_scen_scaled)

# Bayesian Ridge gives predictive variance
from scipy.stats import t
n, p = X_scaled.shape
y_pred_train = br.predict(X_scaled)
residuals = y - y_pred_train
sigma2 = np.var(residuals) * n / (n - p - 1)  # unbiased estimate

# Predictive variance for new points
# var(y_new) = sigma^2 + x_new^T * Sigma_w * x_new
# where Sigma_w is posterior covariance of weights
# BayesianRidge stores sigma_ (precision of weights) and lambda_ (precision of noise)
# Actually, BayesianRidge.predict with return_std=True gives predictive std
y_pred_br, y_std_br = br.predict(X_scen_scaled, return_std=True)

# 95% prediction interval using t-distribution
t_crit = t.ppf(0.975, n - p - 1)
y_lower_br = y_pred_br - t_crit * y_std_br
y_upper_br = y_pred_br + t_crit * y_std_br

print(f"Train R^2: {br.score(X_scaled, y):.4f}")
print(f"Predictions:")
for i, q in enumerate(scenario['quarter']):
    print(f"  Q{q}: y_pred={y_pred_br[i]:.6f}, y_lower={y_lower_br[i]:.6f}, y_upper={y_upper_br[i]:.6f}")

# ===== MODEL 2: Quantile Regression for prediction intervals =====
print("\n=== Quantile Regression (95% PI) ===")
qr_low = QuantileRegressor(quantile=0.025, alpha=0.1, solver='highs')
qr_med = QuantileRegressor(quantile=0.5, alpha=0.1, solver='highs')
qr_high = QuantileRegressor(quantile=0.975, alpha=0.1, solver='highs')

qr_low.fit(X_scaled, y)
qr_med.fit(X_scaled, y)
qr_high.fit(X_scaled, y)

y_pred_qr = qr_med.predict(X_scen_scaled)
y_lower_qr = qr_low.predict(X_scen_scaled)
y_upper_qr = qr_high.predict(X_scen_scaled)

print(f"Predictions:")
for i, q in enumerate(scenario['quarter']):
    print(f"  Q{q}: y_pred={y_pred_qr[i]:.6f}, y_lower={y_lower_qr[i]:.6f}, y_upper={y_upper_qr[i]:.6f}")

# ===== MODEL 3: Random Forest with Bootstrap for PI =====
print("\n=== Random Forest + Bootstrap PI ===")
rf = RandomForestRegressor(n_estimators=500, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1)
rf.fit(X_scaled, y)

# Bootstrap prediction intervals
n_boot = 200
boot_preds = np.zeros((n_boot, X_scen_scaled.shape[0]))
n_train = X_scaled.shape[0]

for i in range(n_boot):
    idx = np.random.choice(n_train, n_train, replace=True)
    rf_boot = RandomForestRegressor(n_estimators=200, max_depth=5, min_samples_leaf=3, random_state=i, n_jobs=-1)
    rf_boot.fit(X_scaled[idx], y.iloc[idx])
    boot_preds[i] = rf_boot.predict(X_scen_scaled)

y_pred_rf = np.mean(boot_preds, axis=0)
y_lower_rf = np.percentile(boot_preds, 2.5, axis=0)
y_upper_rf = np.percentile(boot_preds, 97.5, axis=0)

print(f"Train R^2: {rf.score(X_scaled, y):.4f}")
print(f"Predictions:")
for i, q in enumerate(scenario['quarter']):
    print(f"  Q{q}: y_pred={y_pred_rf[i]:.6f}, y_lower={y_lower_rf[i]:.6f}, y_upper={y_upper_rf[i]:.6f}")

# ===== MODEL 4: Gradient Boosting with Quantile Loss =====
print("\n=== Gradient Boosting Quantile ===")
gb_low = GradientBoostingRegressor(loss='quantile', alpha=0.025, n_estimators=200, max_depth=3, random_state=42)
gb_med = GradientBoostingRegressor(loss='quantile', alpha=0.5, n_estimators=200, max_depth=3, random_state=42)
gb_high = GradientBoostingRegressor(loss='quantile', alpha=0.975, n_estimators=200, max_depth=3, random_state=42)

gb_low.fit(X_scaled, y)
gb_med.fit(X_scaled, y)
gb_high.fit(X_scaled, y)

y_pred_gb = gb_med.predict(X_scen_scaled)
y_lower_gb = gb_low.predict(X_scen_scaled)
y_upper_gb = gb_high.predict(X_scen_scaled)

print(f"Train R^2: {gb_med.score(X_scaled, y):.4f}")
print(f"Predictions:")
for i, q in enumerate(scenario['quarter']):
    print(f"  Q{q}: y_pred={y_pred_gb[i]:.6f}, y_lower={y_lower_gb[i]:.6f}, y_upper={y_upper_gb[i]:.6f}")

# ===== Cross-validation evaluation =====
print("\n=== Cross-validation RMSE ===")
tscv = TimeSeriesSplit(n_splits=5)
models = {
    'BayesianRidge': br,
    'QuantileReg': qr_med,
    'RandomForest': rf,
    'GradBoost': gb_med
}

for name, model in models.items():
    preds = cross_val_predict(model, X_scaled, y, cv=tscv)
    rmse = np.sqrt(mean_squared_error(y, preds))
    mae = mean_absolute_error(y, preds)
    print(f"  {name}: RMSE={rmse:.6f}, MAE={mae:.6f}")
```

## [37] tool

Traceback (most recent call last):
  File "<stdin>", line 240, in <module>
  File "/usr/local/lib/python3.12/site-packages/sklearn/utils/_param_validation.py", line 218, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/sklearn/model_selection/_validation.py", line 1215, in cross_val_predict
    raise ValueError("cross_val_predict only works for partitions")
ValueError: cross_val_predict only works for partitions

Selected features (15): ['unemployment', 'unemp_yoy', 'unemp_qoq', 'unemp_ma4', 'unemp_std4', 'unemp_gap', 'gdp', 'hpi', 'hpi_yoy', 'hpi_qoq', 'hpi_gap', 'log_sp500', 'unemp_x_spread', 'hpi_x_unemp', 'hpi_change_x_unemp']

=== Bayesian Ridge ===
Train R^2: 0.2850
Predictions:
  Q81: y_pred=0.028336, y_lower=0.005790, y_upper=0.050882
  Q82: y_pred=0.028952, y_lower=0.006379, y_upper=0.051524
  Q83: y_pred=0.029414, y_lower=0.006689, y_upper=0.052138
  Q84: y_pred=0.029934, y_lower=0.007004, y_upper=0.052863
  Q85: y_pred=0.030688, y_lower=0.007403, y_upper=0.053972
  Q86: y_pred=0.031487, y_lower=0.007763, y_upper=0.055211
  Q87: y_pred=0.032340, y_lower=0.008133, y_upper=0.056548
  Q88: y_pred=0.033189, y_lower=0.008411, y_upper=0.057967
  Q89: y_pred=0.033897, y_lower=0.009026, y_upper=0.058768

=== Quantile Regression (95% PI) ===
Predictions:
  Q81: y_pred=0.025043, y_lower=0.011391, y_upper=0.051577
  Q82: y_pred=0.025383, y_lower=0.011391, y_upper=0.051577
  Q83: y_pred=0.025739, y_lower=0.011391, y_upper=0.051577
  Q84: y_pred=0.026110, y_lower=0.011391, y_upper=0.051577
  Q85: y_pred=0.026498, y_lower=0.011391, y_upper=0.051577
  Q86: y_pred=0.026909, y_lower=0.011391, y_upper=0.051577
  Q87: y_pred=0.027338, y_lower=0.011391, y_upper=0.051577
  Q88: y_pred=0.027786, y_lower=0.011391, y_upper=0.051577
  Q89: y_pred=0.028254, y_lower=0.011391, y_upper=0.051577

=== Random Forest + Bootstrap PI ===
Train R^2: 0.7008
Predictions:
  Q81: y_pred=0.026769, y_lower=0.021471, y_upper=0.030616
  Q82: y_pred=0.028087, y_lower=0.022694, y_upper=0.032243
  Q83: y_pred=0.028488, y_lower=0.022443, y_upper=0.033102
  Q84: y_pred=0.029463, y_lower=0.022328, y_upper=0.035882
  Q85: y_pred=0.030005, y_lower=0.023671, y_upper=0.036361
  Q86: y_pred=0.031614, y_lower=0.024075, y_upper=0.038648
  Q87: y_pred=0.035024, y_lower=0.028471, y_upper=0.041317
  Q88: y_pred=0.035508, y_lower=0.028064, y_upper=0.040692
  Q89: y_pred=0.035509, y_lower=0.028208, y_upper=0.040734

=== Gradient Boosting Quantile ===
Train R^2: 0.7938
Predictions:
  Q81: y_pred=0.032585, y_lower=0.012457, y_upper=0.035348
  Q82: y_pred=0.032841, y_lower=0.012457, y_upper=0.035348
  Q83: y_pred=0.032680, y_lower=0.012457, y_upper=0.035348
  Q84: y_pred=0.032359, y_lower=0.012457, y_upper=0.037072
  Q85: y_pred=0.032468, y_lower=0.012457, y_upper=0.045074
  Q86: y_pred=0.033739, y_lower=0.012457, y_upper=0.045074
  Q87: y_pred=0.037385, y_lower=0.012457, y_upper=0.045074
  Q88: y_pred=0.037525, y_lower=0.012457, y_upper=0.045074
  Q89: y_pred=0.038266, y_lower=0.012457, y_upper=0.046704

=== Cross-validation RMSE ===


## [38] assistant

**[reasoning]**

> The cross_val_predict failed due to TimeSeriesSplit not being a partition. Let me fix that and also analyze the results.
> 
> Key observations:
> 1. Bayesian Ridge gives predictions ~2.8-3.4% with wide intervals (~0.6-5.9%)
> 2. Quantile Regression gives ~2.5-2.8% with intervals ~1.1-5.2%
> 3. Random Forest gives ~2.7-3.6% with narrower intervals (~2.1-4.1%)
> 4. Gradient Boosting gives ~3.3-3.8% with intervals ~1.2-4.7%
> 
> The models differ significantly. The Bayesian Ridge has the widest intervals, which is more conservative. The Random Forest has the highest in-sample R^2 (0.70) but may overfit. The Gradient Boosting has the highest R^2 (0.79) but quantile intervals are very wide on the upper end.
> 
> Given the scenario is a stress test (unemployment rising, GDP falling, HPI falling, spreads widening), default rates should increase. The scenario shows:
> - Unemployment rising from 5.2% to 7.4% (stress)
> - GDP falling from 152 to 140 (recession)
> - HPI falling from 288 to 246 (housing crash)
> - BBB spread rising from 1.6% to 2.6% (credit stress)
> - VIX rising from 14.6 to 22.9 (market stress)
> - But SP500 rising (odd for stress scenario)
> 
> This is a mixed scenario - real economy stress but financial markets booming. The default rate should likely increase due to real economy stress.
> 
> Let me use cross_val_score instead and then create an ensemble prediction with proper intervals.



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.linear_model import Ridge, BayesianRidge, QuantileRegressor, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

def create_features_final(df, is_train=True):
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    if 'unemployment' in df.columns:
        u = df['unemployment']
        features['unemployment'] = u
        features['unemp_yoy'] = u.diff(4)
        features['unemp_qoq'] = u.diff()
        features['unemp_ma4'] = u.rolling(4, min_periods=1).mean()
        features['unemp_std4'] = u.rolling(4, min_periods=1).std()
        features['unemp_gap'] = u - u.rolling(8, min_periods=1).mean()
    
    if 'bbb_spread' in df.columns:
        s = df['bbb_spread']
        features['bbb_spread'] = s
        features['spread_yoy'] = s.diff(4)
        features['spread_qoq'] = s.diff()
        features['spread_ma4'] = s.rolling(4, min_periods=1).mean()
    
    if 'vix' in df.columns:
        v = df['vix']
        features['vix'] = v
        features['vix_yoy'] = v.diff(4)
        features['vix_qoq'] = v.diff()
        features['vix_ma4'] = v.rolling(4, min_periods=1).mean()
    
    if 'gdp' in df.columns:
        g = df['gdp']
        features['gdp'] = g
        features['gdp_yoy'] = g.pct_change(4)
        features['gdp_qoq'] = g.pct_change()
        features['gdp_ma4'] = g.rolling(4, min_periods=1).mean()
        features['gdp_gap'] = g - g.rolling(8, min_periods=1).mean()
    
    if 'hpi' in df.columns:
        h = df['hpi']
        features['hpi'] = h
        features['hpi_yoy'] = h.pct_change(4)
        features['hpi_qoq'] = h.pct_change()
        features['hpi_ma4'] = h.rolling(4, min_periods=1).mean()
        features['hpi_gap'] = h - h.rolling(8, min_periods=1).mean()
    
    if 'cpi' in df.columns:
        c = df['cpi']
        features['cpi'] = c
        features['cpi_yoy'] = c.pct_change(4)
        features['cpi_qoq'] = c.pct_change()
    
    for col in ['sp500', 'djia', 'nasdaq']:
        if col in df.columns:
            features[f'log_{col}'] = np.log(df[col] + 1)
            features[f'{col}_yoy'] = df[col].pct_change(4)
    
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    if 'unemployment' in df.columns and 'vix' in df.columns:
        features['unemp_x_vix'] = df['unemployment'] * df['vix']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    if 'gdp' in df.columns and 'unemployment' in df.columns:
        features['gdp_x_unemp'] = df['gdp'] * df['unemployment']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_change_x_unemp'] = df['hpi'].pct_change(4) * df['unemployment'].diff(4)
    
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

train_feat = create_features_final(hist, is_train=True)
scenario_feat = create_features_final(scenario, is_train=False)

X = train_feat.drop(['quarter', 'default_rate'], axis=1)
y = train_feat['default_rate']
X_scenario = scenario_feat.drop(['quarter'], axis=1)

# Feature selection
selector = VarianceThreshold(threshold=1e-8)
X_var = selector.fit_transform(X)
kept = X.columns[selector.get_support()]
X = X[kept]
X_scenario = X_scenario[kept]

corr_matrix = X.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [c for c in upper.columns if any(upper[c] > 0.95)]
X = X.drop(columns=to_drop)
X_scenario = X_scenario.drop(columns=to_drop)

k = min(15, X.shape[1])
selector_k = SelectKBest(f_regression, k=k)
X_k = selector_k.fit_transform(X, y)
selected = X.columns[selector_k.get_support()]
X_sel = X[selected]
X_scenario_sel = X_scenario[selected]

print(f"Selected features: {list(selected)}")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sel)
X_scen_scaled = scaler.transform(X_scenario_sel)

# CV evaluation
tscv = TimeSeriesSplit(n_splits=5)

models_cv = {
    'BayesianRidge': BayesianRidge(alpha_1=1e-6, alpha_2=1e-6, lambda_1=1e-6, lambda_2=1e-6),
    'Ridge': Ridge(alpha=1.0),
    'RandomForest': RandomForestRegressor(n_estimators=500, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1),
    'GradBoost': GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=42),
}

print("Cross-validation RMSE:")
for name, model in models_cv.items():
    scores = cross_val_score(model, X_scaled, y, cv=tscv, scoring='neg_mean_squared_error')
    rmse = np.sqrt(-scores)
    print(f"  {name}: RMSE={rmse.mean():.6f} (+/- {rmse.std():.6f})")

# Now fit final models and get predictions with intervals
print("\n=== Fitting final models ===")

# 1. Bayesian Ridge with analytical intervals
br = BayesianRidge(alpha_1=1e-6, alpha_2=1e-6, lambda_1=1e-6, lambda_2=1e-6)
br.fit(X_scaled, y)
y_pred_br, y_std_br = br.predict(X_scen_scaled, return_std=True)
from scipy.stats import t
n, p = X_scaled.shape
t_crit = t.ppf(0.975, n - p - 1)
y_lower_br = y_pred_br - t_crit * y_std_br
y_upper_br = y_pred_br + t_crit * y_std_br

# 2. Quantile Regression
qr_low = QuantileRegressor(quantile=0.025, alpha=0.1, solver='highs')
qr_med = QuantileRegressor(quantile=0.5, alpha=0.1, solver='highs')
qr_high = QuantileRegressor(quantile=0.975, alpha=0.1, solver='highs')
qr_low.fit(X_scaled, y)
qr_med.fit(X_scaled, y)
qr_high.fit(X_scaled, y)
y_pred_qr = qr_med.predict(X_scen_scaled)
y_lower_qr = qr_low.predict(X_scen_scaled)
y_upper_qr = qr_high.predict(X_scen_scaled)

# 3. Gradient Boosting Quantile
gb_low = GradientBoostingRegressor(loss='quantile', alpha=0.025, n_estimators=200, max_depth=3, random_state=42)
gb_med = GradientBoostingRegressor(loss='quantile', alpha=0.5, n_estimators=200, max_depth=3, random_state=42)
gb_high = GradientBoostingRegressor(loss='quantile', alpha=0.975, n_estimators=200, max_depth=3, random_state=42)
gb_low.fit(X_scaled, y)
gb_med.fit(X_scaled, y)
gb_high.fit(X_scaled, y)
y_pred_gb = gb_med.predict(X_scen_scaled)
y_lower_gb = gb_low.predict(X_scen_scaled)
y_upper_gb = gb_high.predict(X_scen_scaled)

# 4. Random Forest Bootstrap
n_boot = 300
boot_preds = np.zeros((n_boot, X_scen_scaled.shape[0]))
n_train = X_scaled.shape[0]
for i in range(n_boot):
    idx = np.random.choice(n_train, n_train, replace=True)
    rf_boot = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=3, random_state=i, n_jobs=-1)
    rf_boot.fit(X_scaled[idx], y.iloc[idx])
    boot_preds[i] = rf_boot.predict(X_scen_scaled)
y_pred_rf = np.mean(boot_preds, axis=0)
y_lower_rf = np.percentile(boot_preds, 2.5, axis=0)
y_upper_rf = np.percentile(boot_preds, 97.5, axis=0)

# Ensemble: average of point predictions, and for intervals use the most conservative/widest
print("\n=== Ensemble Predictions ===")
y_pred_ensemble = np.mean([y_pred_br, y_pred_qr, y_pred_gb, y_pred_rf], axis=0)

# For intervals, use the widest (most conservative) across methods
y_lower_ensemble = np.minimum.reduce([y_lower_br, y_lower_qr, y_lower_gb, y_lower_rf])
y_upper_ensemble = np.maximum.reduce([y_upper_br, y_upper_qr, y_upper_gb, y_upper_rf])

print("Individual model predictions:")
for i, q in enumerate(scenario['quarter']):
    print(f"  Q{q}:")
    print(f"    BR:    {y_pred_br[i]:.6f} [{y_lower_br[i]:.6f}, {y_upper_br[i]:.6f}]")
    print(f"    QR:    {y_pred_qr[i]:.6f} [{y_lower_qr[i]:.6f}, {y_upper_qr[i]:.6f}]")
    print(f"    GB:    {y_pred_gb[i]:.6f} [{y_lower_gb[i]:.6f}, {y_upper_gb[i]:.6f}]")
    print(f"    RF:    {y_pred_rf[i]:.6f} [{y_lower_rf[i]:.6f}, {y_upper_rf[i]:.6f}]")
    print(f"    ENS:   {y_pred_ensemble[i]:.6f} [{y_lower_ensemble[i]:.6f}, {y_upper_ensemble[i]:.6f}]")

# Also compute a more refined ensemble: weight by CV performance
# Lower RMSE -> higher weight
cv_rmse = {}
for name, model in models_cv.items():
    scores = cross_val_score(model, X_scaled, y, cv=tscv, scoring='neg_mean_squared_error')
    cv_rmse[name] = np.sqrt(-scores.mean())

print(f"\nCV RMSE: {cv_rmse}")

# Weights inversely proportional to RMSE
weights = {k: 1/v for k, v in cv_rmse.items()}
total = sum(weights.values())
weights = {k: v/total for k, v in weights.items()}
print(f"Weights: {weights}")

# Weighted ensemble predictions
y_pred_weighted = (weights['BayesianRidge'] * y_pred_br + 
                   weights['Ridge'] * y_pred_qr +  # using QR as proxy for Ridge
                   weights['RandomForest'] * y_pred_rf + 
                   weights['GradBoost'] * y_pred_gb)

print("\nWeighted Ensemble:")
for i, q in enumerate(scenario['quarter']):
    print(f"  Q{q}: {y_pred_weighted[i]:.6f}")
```

## [39] tool

Selected features: ['unemployment', 'unemp_yoy', 'unemp_qoq', 'unemp_ma4', 'unemp_std4', 'unemp_gap', 'gdp', 'hpi', 'hpi_yoy', 'hpi_qoq', 'hpi_gap', 'log_sp500', 'unemp_x_spread', 'hpi_x_unemp', 'hpi_change_x_unemp']
Cross-validation RMSE:
  BayesianRidge: RMSE=0.011059 (+/- 0.005828)
  Ridge: RMSE=0.016162 (+/- 0.006509)
  RandomForest: RMSE=0.009800 (+/- 0.003188)
  GradBoost: RMSE=0.012316 (+/- 0.005197)

=== Fitting final models ===

=== Ensemble Predictions ===
Individual model predictions:
  Q81:
    BR:    0.028336 [0.005790, 0.050882]
    QR:    0.025043 [0.011391, 0.051577]
    GB:    0.032585 [0.012457, 0.035348]
    RF:    0.026596 [0.021465, 0.031340]
    ENS:   0.028140 [0.005790, 0.051577]
  Q82:
    BR:    0.028952 [0.006379, 0.051524]
    QR:    0.025383 [0.011391, 0.051577]
    GB:    0.032841 [0.012457, 0.035348]
    RF:    0.027758 [0.022758, 0.032564]
    ENS:   0.028733 [0.006379, 0.051577]
  Q83:
    BR:    0.029414 [0.006689, 0.052138]
    QR:    0.025739 [0.011391, 0.051577]
    GB:    0.032680 [0.012457, 0.035348]
    RF:    0.028142 [0.022827, 0.033460]
    ENS:   0.028994 [0.006689, 0.052138]
  Q84:
    BR:    0.029934 [0.007004, 0.052863]
    QR:    0.026110 [0.011391, 0.051577]
    GB:    0.032359 [0.012457, 0.037072]
    RF:    0.029037 [0.023358, 0.035138]
    ENS:   0.029360 [0.007004, 0.052863]
  Q85:
    BR:    0.030688 [0.007403, 0.053972]
    QR:    0.026498 [0.011391, 0.051577]
    GB:    0.032468 [0.012457, 0.045074]
    RF:    0.029607 [0.024005, 0.036369]
    ENS:   0.029815 [0.007403, 0.053972]
  Q86:
    BR:    0.031487 [0.007763, 0.055211]
    QR:    0.026909 [0.011391, 0.051577]
    GB:    0.033739 [0.012457, 0.045074]
    RF:    0.030844 [0.024634, 0.038565]
    ENS:   0.030745 [0.007763, 0.055211]
  Q87:
    BR:    0.032340 [0.008133, 0.056548]
    QR:    0.027338 [0.011391, 0.051577]
    GB:    0.037385 [0.012457, 0.045074]
    RF:    0.033904 [0.026159, 0.040373]
    ENS:   0.032742 [0.008133, 0.056548]
  Q88:
    BR:    0.033189 [0.008411, 0.057967]
    QR:    0.027786 [0.011391, 0.051577]
    GB:    0.037525 [0.012457, 0.045074]
    RF:    0.034452 [0.026359, 0.040787]
    ENS:   0.033238 [0.008411, 0.057967]
  Q89:
    BR:    0.033897 [0.009026, 0.058768]
    QR:    0.028254 [0.011391, 0.051577]
    GB:    0.038266 [0.012457, 0.046704]
    RF:    0.034475 [0.026754, 0.040269]
    ENS:   0.033723 [0.009026, 0.058768]

CV RMSE: {'BayesianRidge': np.float64(0.012500524366082118), 'Ridge': np.float64(0.017423276876820718), 'RandomForest': np.float64(0.010306033557611527), 'GradBoost': np.float64(0.013367982553506592)}
Weights: {'BayesianRidge': np.float64(0.2586985411473358), 'Ridge': np.float64(0.1856061543385324), 'RandomForest': np.float64(0.3137839013432858), 'GradBoost': np.float64(0.24191140317084603)}

Weighted Ensemble:
  Q81: 0.028207
  Q82: 0.028856
  Q83: 0.029123
  Q84: 0.029529
  Q85: 0.030002
  Q86: 0.030980
  Q87: 0.033123
  Q88: 0.033631
  Q89: 0.034088


## [40] assistant

**[reasoning]**

> The ensemble approach looks good. Now I need to create proper prediction intervals. The simple min/max ensemble intervals are too wide. Let me create a more principled approach for the prediction intervals.
> 
> I should consider:
> 1. Bayesian Ridge gives analytical prediction intervals
> 2. Quantile Regression gives direct prediction intervals
> 3. Gradient Boosting with quantile loss gives prediction intervals
> 4. Random Forest bootstrap gives prediction intervals
> 
> I should combine these in a statistically sound way. One approach is to use the variance of the ensemble predictions plus the average of the individual prediction variances.
> 
> Let me create a final model with proper prediction intervals and write the predictions.csv file



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.linear_model import Ridge, BayesianRidge, QuantileRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

def create_features_final(df, is_train=True):
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    if 'unemployment' in df.columns:
        u = df['unemployment']
        features['unemployment'] = u
        features['unemp_yoy'] = u.diff(4)
        features['unemp_qoq'] = u.diff()
        features['unemp_ma4'] = u.rolling(4, min_periods=1).mean()
        features['unemp_std4'] = u.rolling(4, min_periods=1).std()
        features['unemp_gap'] = u - u.rolling(8, min_periods=1).mean()
    
    if 'bbb_spread' in df.columns:
        s = df['bbb_spread']
        features['bbb_spread'] = s
        features['spread_yoy'] = s.diff(4)
        features['spread_qoq'] = s.diff()
        features['spread_ma4'] = s.rolling(4, min_periods=1).mean()
    
    if 'vix' in df.columns:
        v = df['vix']
        features['vix'] = v
        features['vix_yoy'] = v.diff(4)
        features['vix_qoq'] = v.diff()
        features['vix_ma4'] = v.rolling(4, min_periods=1).mean()
    
    if 'gdp' in df.columns:
        g = df['gdp']
        features['gdp'] = g
        features['gdp_yoy'] = g.pct_change(4)
        features['gdp_qoq'] = g.pct_change()
        features['gdp_ma4'] = g.rolling(4, min_periods=1).mean()
        features['gdp_gap'] = g - g.rolling(8, min_periods=1).mean()
    
    if 'hpi' in df.columns:
        h = df['hpi']
        features['hpi'] = h
        features['hpi_yoy'] = h.pct_change(4)
        features['hpi_qoq'] = h.pct_change()
        features['hpi_ma4'] = h.rolling(4, min_periods=1).mean()
        features['hpi_gap'] = h - h.rolling(8, min_periods=1).mean()
    
    if 'cpi' in df.columns:
        c = df['cpi']
        features['cpi'] = c
        features['cpi_yoy'] = c.pct_change(4)
        features['cpi_qoq'] = c.pct_change()
    
    for col in ['sp500', 'djia', 'nasdaq']:
        if col in df.columns:
            features[f'log_{col}'] = np.log(df[col] + 1)
            features[f'{col}_yoy'] = df[col].pct_change(4)
    
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    if 'unemployment' in df.columns and 'vix' in df.columns:
        features['unemp_x_vix'] = df['unemployment'] * df['vix']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    if 'gdp' in df.columns and 'unemployment' in df.columns:
        features['gdp_x_unemp'] = df['gdp'] * df['unemployment']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_change_x_unemp'] = df['hpi'].pct_change(4) * df['unemployment'].diff(4)
    
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

train_feat = create_features_final(hist, is_train=True)
scenario_feat = create_features_final(scenario, is_train=False)

X = train_feat.drop(['quarter', 'default_rate'], axis=1)
y = train_feat['default_rate']
X_scenario = scenario_feat.drop(['quarter'], axis=1)

# Feature selection
selector = VarianceThreshold(threshold=1e-8)
X_var = selector.fit_transform(X)
kept = X.columns[selector.get_support()]
X = X[kept]
X_scenario = X_scenario[kept]

corr_matrix = X.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [c for c in upper.columns if any(upper[c] > 0.95)]
X = X.drop(columns=to_drop)
X_scenario = X_scenario.drop(columns=to_drop)

k = min(15, X.shape[1])
selector_k = SelectKBest(f_regression, k=k)
X_k = selector_k.fit_transform(X, y)
selected = X.columns[selector_k.get_support()]
X_sel = X[selected]
X_scenario_sel = X_scenario[selected]

# Scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sel)
X_scen_scaled = scaler.transform(X_scenario_sel)

# ===== FINAL MODELS =====
print("Training final models...")

# 1. Bayesian Ridge (analytical PI)
br = BayesianRidge(alpha_1=1e-6, alpha_2=1e-6, lambda_1=1e-6, lambda_2=1e-6)
br.fit(X_scaled, y)
y_pred_br, y_std_br = br.predict(X_scen_scaled, return_std=True)

# 2. Quantile Regression
qr_low = QuantileRegressor(quantile=0.025, alpha=0.1, solver='highs')
qr_med = QuantileRegressor(quantile=0.5, alpha=0.1, solver='highs')
qr_high = QuantileRegressor(quantile=0.975, alpha=0.1, solver='highs')
qr_low.fit(X_scaled, y)
qr_med.fit(X_scaled, y)
qr_high.fit(X_scaled, y)
y_pred_qr = qr_med.predict(X_scen_scaled)
y_lower_qr = qr_low.predict(X_scen_scaled)
y_upper_qr = qr_high.predict(X_scen_scaled)

# 3. Gradient Boosting Quantile
gb_low = GradientBoostingRegressor(loss='quantile', alpha=0.025, n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42)
gb_med = GradientBoostingRegressor(loss='quantile', alpha=0.5, n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42)
gb_high = GradientBoostingRegressor(loss='quantile', alpha=0.975, n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42)
gb_low.fit(X_scaled, y)
gb_med.fit(X_scaled, y)
gb_high.fit(X_scaled, y)
y_pred_gb = gb_med.predict(X_scen_scaled)
y_lower_gb = gb_low.predict(X_scen_scaled)
y_upper_gb = gb_high.predict(X_scen_scaled)

# 4. Random Forest with bootstrap PI
rf = RandomForestRegressor(n_estimators=500, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1)
rf.fit(X_scaled, y)

n_boot = 200
boot_preds = np.zeros((n_boot, X_scen_scaled.shape[0]))
n_train = X_scaled.shape[0]
for i in range(n_boot):
    idx = np.random.choice(n_train, n_train, replace=True)
    rf_boot = RandomForestRegressor(n_estimators=200, max_depth=5, min_samples_leaf=3, random_state=i, n_jobs=-1)
    rf_boot.fit(X_scaled[idx], y.iloc[idx])
    boot_preds[i] = rf_boot.predict(X_scen_scaled)

y_pred_rf = np.mean(boot_preds, axis=0)
y_lower_rf = np.percentile(boot_preds, 2.5, axis=0)
y_upper_rf = np.percentile(boot_preds, 97.5, axis=0)

# ===== ENSEMBLE PREDICTIONS =====
# Weighted by inverse CV RMSE
tscv = TimeSeriesSplit(n_splits=5)
models_cv = {
    'BayesianRidge': BayesianRidge(alpha_1=1e-6, alpha_2=1e-6, lambda_1=1e-6, lambda_2=1e-6),
    'Ridge': Ridge(alpha=1.0),
    'RandomForest': RandomForestRegressor(n_estimators=300, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1),
    'GradBoost': GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42)
}

cv_rmse = {}
for name, model in models_cv.items():
    scores = cross_val_score(model, X_scaled, y, cv=tscv, scoring='neg_mean_squared_error')
    cv_rmse[name] = np.sqrt(-scores.mean())

weights = {k: 1/v for k, v in cv_rmse.items()}
total = sum(weights.values())
weights = {k: v/total for k, v in weights.items()}

print(f"CV RMSE: {cv_rmse}")
print(f"Weights: {weights}")

# Weighted point prediction
y_pred_ensemble = (weights['BayesianRidge'] * y_pred_br + 
                   weights['Ridge'] * y_pred_qr +  # QR median as Ridge proxy
                   weights['RandomForest'] * y_pred_rf + 
                   weights['GradBoost'] * y_pred_gb)

# For prediction intervals: combine uncertainties properly
# Method: Use the spread of ensemble predictions + average model uncertainty
# This gives a more conservative interval

# Ensemble variance from spread of predictions
ensemble_preds = np.column_stack([y_pred_br, y_pred_qr, y_pred_rf, y_pred_gb])
ensemble_var = np.var(ensemble_preds, axis=1, ddof=1)

# Average model-specific variances
# For BR: use returned std
# For QR: use quantile spread
# For GB: use quantile spread
# For RF: use bootstrap variance
var_br = y_std_br**2
var_qr = ((y_upper_qr - y_lower_qr) / 3.92)**2  # approximate std from 95% PI
var_gb = ((y_upper_gb - y_lower_gb) / 3.92)**2
var_rf = ((y_upper_rf - y_lower_rf) / 3.92)**2

avg_model_var = np.mean([var_br, var_qr, var_gb, var_rf], axis=0)

# Total predictive variance = ensemble variance + average model variance
total_var = ensemble_var + avg_model_var
total_std = np.sqrt(total_var)

# 95% PI using t-distribution
from scipy.stats import t
n, p = X_scaled.shape
t_crit = t.ppf(0.975, n - p - 1)
y_lower_ensemble = y_pred_ensemble - t_crit * total_std
y_upper_ensemble = y_pred_ensemble + t_crit * total_std

# Also compute a simpler approach: percentile of all bootstrap/quantile predictions
# Collect all predictions
all_preds = np.column_stack([
    boot_preds,  # 200 RF bootstrap
    # For others, sample from their predictive distributions
])

# Simpler: use percentiles of all individual model PIs
# For each model, generate samples from their predictive distribution
n_samples = 1000
all_samples = []

# BR samples
for i in range(X_scen_scaled.shape[0]):
    samples = np.random.normal(y_pred_br[i], y_std_br[i], n_samples // 4)
    all_samples.append(samples)
all_samples = np.column_stack(all_samples).T

# Add QR samples (uniform between quantiles)
for i in range(X_scen_scaled.shape[0]):
    samples = np.random.uniform(y_lower_qr[i], y_upper_qr[i], n_samples // 4)
    if i == 0:
        qr_samples = samples
    else:
        qr_samples = np.column_stack([qr_samples, samples])
all_samples = np.vstack([all_samples, qr_samples])

# Add GB samples
for i in range(X_scen_scaled.shape[0]):
    samples = np.random.uniform(y_lower_gb[i], y_upper_gb[i], n_samples // 4)
    if i == 0:
        gb_samples = samples
    else:
        gb_samples = np.column_stack([gb_samples, samples])
all_samples = np.vstack([all_samples, gb_samples])

# Add RF bootstrap samples (already have boot_preds)
rf_samples = boot_preds.T
all_samples = np.vstack([all_samples, rf_samples])

# Final ensemble PIs from all samples
y_lower_final = np.percentile(all_samples, 2.5, axis=0)
y_upper_final = np.percentile(all_samples, 97.5, axis=0)

print("\n=== FINAL ENSEMBLE PREDICTIONS ===")
for i, q in enumerate(scenario['quarter']):
    print(f"  Q{q}: y_pred={y_pred_ensemble[i]:.6f}, y_lower={y_lower_final[i]:.6f}, y_upper={y_upper_final[i]:.6f}")

# Ensure lower bound >= 0 (default rate can't be negative)
y_lower_final = np.maximum(y_lower_final, 0)

# Write predictions.csv
output = pd.DataFrame({
    'quarter': scenario['quarter'],
    'y_pred': y_pred_ensemble,
    'y_lower': y_lower_final,
    'y_upper': y_upper_final
})
output.to_csv('predictions.csv', index=False)
print("\npredictions.csv written successfully")
print(output.to_string(index=False))
```

## [41] tool

Traceback (most recent call last):
  File "<stdin>", line 259, in <module>
  File "/usr/local/lib/python3.12/site-packages/numpy/_core/shape_base.py", line 290, in vstack
    return _nx.concatenate(arrs, 0, dtype=dtype, casting=casting)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: all the input array dimensions except for the concatenation axis must match exactly, but along dimension 1, the array at index 0 has size 250 and the array at index 1 has size 9

Training final models...
CV RMSE: {'BayesianRidge': np.float64(0.012500524366082118), 'Ridge': np.float64(0.017423276876820718), 'RandomForest': np.float64(0.010366976741913104), 'GradBoost': np.float64(0.013619542835234266)}
Weights: {'BayesianRidge': np.float64(0.2603420387801728), 'Ridge': np.float64(0.18678530004976246), 'RandomForest': np.float64(0.3139210283099837), 'GradBoost': np.float64(0.2389516328600811)}


## [42] assistant

**[reasoning]**

> The issue is with the array stacking. Let me fix the sampling approach - I need to generate samples per quarter, not stack across quarters incorrectly.



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.linear_model import Ridge, BayesianRidge, QuantileRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

def create_features_final(df, is_train=True):
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    if 'unemployment' in df.columns:
        u = df['unemployment']
        features['unemployment'] = u
        features['unemp_yoy'] = u.diff(4)
        features['unemp_qoq'] = u.diff()
        features['unemp_ma4'] = u.rolling(4, min_periods=1).mean()
        features['unemp_std4'] = u.rolling(4, min_periods=1).std()
        features['unemp_gap'] = u - u.rolling(8, min_periods=1).mean()
    
    if 'bbb_spread' in df.columns:
        s = df['bbb_spread']
        features['bbb_spread'] = s
        features['spread_yoy'] = s.diff(4)
        features['spread_qoq'] = s.diff()
        features['spread_ma4'] = s.rolling(4, min_periods=1).mean()
    
    if 'vix' in df.columns:
        v = df['vix']
        features['vix'] = v
        features['vix_yoy'] = v.diff(4)
        features['vix_qoq'] = v.diff()
        features['vix_ma4'] = v.rolling(4, min_periods=1).mean()
    
    if 'gdp' in df.columns:
        g = df['gdp']
        features['gdp'] = g
        features['gdp_yoy'] = g.pct_change(4)
        features['gdp_qoq'] = g.pct_change()
        features['gdp_ma4'] = g.rolling(4, min_periods=1).mean()
        features['gdp_gap'] = g - g.rolling(8, min_periods=1).mean()
    
    if 'hpi' in df.columns:
        h = df['hpi']
        features['hpi'] = h
        features['hpi_yoy'] = h.pct_change(4)
        features['hpi_qoq'] = h.pct_change()
        features['hpi_ma4'] = h.rolling(4, min_periods=1).mean()
        features['hpi_gap'] = h - h.rolling(8, min_periods=1).mean()
    
    if 'cpi' in df.columns:
        c = df['cpi']
        features['cpi'] = c
        features['cpi_yoy'] = c.pct_change(4)
        features['cpi_qoq'] = c.pct_change()
    
    for col in ['sp500', 'djia', 'nasdaq']:
        if col in df.columns:
            features[f'log_{col}'] = np.log(df[col] + 1)
            features[f'{col}_yoy'] = df[col].pct_change(4)
    
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    if 'unemployment' in df.columns and 'vix' in df.columns:
        features['unemp_x_vix'] = df['unemployment'] * df['vix']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    if 'gdp' in df.columns and 'unemployment' in df.columns:
        features['gdp_x_unemp'] = df['gdp'] * df['unemployment']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_change_x_unemp'] = df['hpi'].pct_change(4) * df['unemployment'].diff(4)
    
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

train_feat = create_features_final(hist, is_train=True)
scenario_feat = create_features_final(scenario, is_train=False)

X = train_feat.drop(['quarter', 'default_rate'], axis=1)
y = train_feat['default_rate']
X_scenario = scenario_feat.drop(['quarter'], axis=1)

# Feature selection
selector = VarianceThreshold(threshold=1e-8)
X_var = selector.fit_transform(X)
kept = X.columns[selector.get_support()]
X = X[kept]
X_scenario = X_scenario[kept]

corr_matrix = X.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [c for c in upper.columns if any(upper[c] > 0.95)]
X = X.drop(columns=to_drop)
X_scenario = X_scenario.drop(columns=to_drop)

k = min(15, X.shape[1])
selector_k = SelectKBest(f_regression, k=k)
X_k = selector_k.fit_transform(X, y)
selected = X.columns[selector_k.get_support()]
X_sel = X[selected]
X_scenario_sel = X_scenario[selected]

# Scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sel)
X_scen_scaled = scaler.transform(X_scenario_sel)

# ===== FINAL MODELS =====
print("Training final models...")

# 1. Bayesian Ridge (analytical PI)
br = BayesianRidge(alpha_1=1e-6, alpha_2=1e-6, lambda_1=1e-6, lambda_2=1e-6)
br.fit(X_scaled, y)
y_pred_br, y_std_br = br.predict(X_scen_scaled, return_std=True)

# 2. Quantile Regression
qr_low = QuantileRegressor(quantile=0.025, alpha=0.1, solver='highs')
qr_med = QuantileRegressor(quantile=0.5, alpha=0.1, solver='highs')
qr_high = QuantileRegressor(quantile=0.975, alpha=0.1, solver='highs')
qr_low.fit(X_scaled, y)
qr_med.fit(X_scaled, y)
qr_high.fit(X_scaled, y)
y_pred_qr = qr_med.predict(X_scen_scaled)
y_lower_qr = qr_low.predict(X_scen_scaled)
y_upper_qr = qr_high.predict(X_scen_scaled)

# 3. Gradient Boosting Quantile
gb_low = GradientBoostingRegressor(loss='quantile', alpha=0.025, n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42)
gb_med = GradientBoostingRegressor(loss='quantile', alpha=0.5, n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42)
gb_high = GradientBoostingRegressor(loss='quantile', alpha=0.975, n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42)
gb_low.fit(X_scaled, y)
gb_med.fit(X_scaled, y)
gb_high.fit(X_scaled, y)
y_pred_gb = gb_med.predict(X_scen_scaled)
y_lower_gb = gb_low.predict(X_scen_scaled)
y_upper_gb = gb_high.predict(X_scen_scaled)

# 4. Random Forest with bootstrap PI
rf = RandomForestRegressor(n_estimators=500, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1)
rf.fit(X_scaled, y)

n_boot = 200
boot_preds = np.zeros((n_boot, X_scen_scaled.shape[0]))
n_train = X_scaled.shape[0]
for i in range(n_boot):
    idx = np.random.choice(n_train, n_train, replace=True)
    rf_boot = RandomForestRegressor(n_estimators=200, max_depth=5, min_samples_leaf=3, random_state=i, n_jobs=-1)
    rf_boot.fit(X_scaled[idx], y.iloc[idx])
    boot_preds[i] = rf_boot.predict(X_scen_scaled)

y_pred_rf = np.mean(boot_preds, axis=0)
y_lower_rf = np.percentile(boot_preds, 2.5, axis=0)
y_upper_rf = np.percentile(boot_preds, 97.5, axis=0)

# ===== ENSEMBLE WEIGHTS FROM CV =====
tscv = TimeSeriesSplit(n_splits=5)
models_cv = {
    'BayesianRidge': BayesianRidge(alpha_1=1e-6, alpha_2=1e-6, lambda_1=1e-6, lambda_2=1e-6),
    'Ridge': Ridge(alpha=1.0),
    'RandomForest': RandomForestRegressor(n_estimators=300, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1),
    'GradBoost': GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42)
}

cv_rmse = {}
for name, model in models_cv.items():
    scores = cross_val_score(model, X_scaled, y, cv=tscv, scoring='neg_mean_squared_error')
    cv_rmse[name] = np.sqrt(-scores.mean())

weights = {k: 1/v for k, v in cv_rmse.items()}
total = sum(weights.values())
weights = {k: v/total for k, v in weights.items()}

print(f"CV RMSE: {cv_rmse}")
print(f"Weights: {weights}")

# Weighted point prediction
y_pred_ensemble = (weights['BayesianRidge'] * y_pred_br + 
                   weights['Ridge'] * y_pred_qr + 
                   weights['RandomForest'] * y_pred_rf + 
                   weights['GradBoost'] * y_pred_gb)

# ===== ENSEMBLE PREDICTION INTERVALS =====
# Generate samples from each model's predictive distribution for each quarter
n_samples_per_model = 250
n_quarters = X_scen_scaled.shape[0]
all_samples = []

# For each quarter, collect samples from all models
for q in range(n_quarters):
    quarter_samples = []
    
    # BR samples (normal)
    br_samples = np.random.normal(y_pred_br[q], y_std_br[q], n_samples_per_model)
    quarter_samples.append(br_samples)
    
    # QR samples (uniform between quantiles, or use asymmetric)
    qr_samples = np.random.uniform(y_lower_qr[q], y_upper_qr[q], n_samples_per_model)
    quarter_samples.append(qr_samples)
    
    # GB samples
    gb_samples = np.random.uniform(y_lower_gb[q], y_upper_gb[q], n_samples_per_model)
    quarter_samples.append(gb_samples)
    
    # RF bootstrap samples (already have 200)
    rf_samples = boot_preds[:, q]
    quarter_samples.append(rf_samples)
    
    # Combine all samples for this quarter
    all_q_samples = np.concatenate(quarter_samples)
    all_samples.append(all_q_samples)

# Compute percentiles for each quarter
y_lower_final = np.array([np.percentile(s, 2.5) for s in all_samples])
y_upper_final = np.array([np.percentile(s, 97.5) for s in all_samples])

# Ensure lower bound >= 0
y_lower_final = np.maximum(y_lower_final, 0)

print("\n=== FINAL ENSEMBLE PREDICTIONS ===")
for i, q in enumerate(scenario['quarter']):
    print(f"  Q{q}: y_pred={y_pred_ensemble[i]:.6f}, y_lower={y_lower_final[i]:.6f}, y_upper={y_upper_final[i]:.6f}")

# Write predictions.csv
output = pd.DataFrame({
    'quarter': scenario['quarter'],
    'y_pred': y_pred_ensemble,
    'y_lower': y_lower_final,
    'y_upper': y_upper_final
})
output.to_csv('predictions.csv', index=False)
print("\npredictions.csv written successfully")
print(output.to_string(index=False))

# Verify
verify = pd.read_csv('predictions.csv')
print(f"\nVerification: {verify.shape[0]} rows, columns: {verify.columns.tolist()}")
```

## [43] tool

Training final models...
CV RMSE: {'BayesianRidge': np.float64(0.012500524366082118), 'Ridge': np.float64(0.017423276876820718), 'RandomForest': np.float64(0.010366976741913104), 'GradBoost': np.float64(0.013619542835234266)}
Weights: {'BayesianRidge': np.float64(0.2603420387801728), 'Ridge': np.float64(0.18678530004976246), 'RandomForest': np.float64(0.3139210283099837), 'GradBoost': np.float64(0.2389516328600811)}

=== FINAL ENSEMBLE PREDICTIONS ===
  Q81: y_pred=0.027377, y_lower=0.011577, y_upper=0.048876
  Q82: y_pred=0.028283, y_lower=0.012575, y_upper=0.049195
  Q83: y_pred=0.028493, y_lower=0.012832, y_upper=0.050007
  Q84: y_pred=0.028838, y_lower=0.012602, y_upper=0.050127
  Q85: y_pred=0.029475, y_lower=0.012853, y_upper=0.049074
  Q86: y_pred=0.030315, y_lower=0.012624, y_upper=0.050211
  Q87: y_pred=0.032625, y_lower=0.013345, y_upper=0.049874
  Q88: y_pred=0.033245, y_lower=0.012672, y_upper=0.051169
  Q89: y_pred=0.033595, y_lower=0.012870, y_upper=0.051171

predictions.csv written successfully
 quarter   y_pred  y_lower  y_upper
      81 0.027377 0.011577 0.048876
      82 0.028283 0.012575 0.049195
      83 0.028493 0.012832 0.050007
      84 0.028838 0.012602 0.050127
      85 0.029475 0.012853 0.049074
      86 0.030315 0.012624 0.050211
      87 0.032625 0.013345 0.049874
      88 0.033245 0.012672 0.051169
      89 0.033595 0.012870 0.051171

Verification: 9 rows, columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']


## [44] assistant

**[reasoning]**

> The predictions look reasonable. The default rates increase from ~2.7% to ~3.4% over the stress scenario period, which makes sense given rising unemployment, falling GDP, falling HPI, and widening spreads. The prediction intervals are around 1.1-1.3% on the lower end and 4.9-5.1% on the upper end, which reflects substantial uncertainty.
> 
> Let me verify the predictions make sense:
> - The scenario has unemployment rising from 5.2% to 7.4% - this should increase defaults
> - GDP falling from 152 to 140 - recessionary
> - HPI falling from 288 to 246 - housing stress
> - BBB spread rising from 1.6% to 2.6% - credit stress
> - VIX rising from 14.6 to 22.9 - market stress
> - But SP500 rising - this is counterintuitive for a stress scenario
> 
> The model captures the stress from unemployment, GDP, HPI, and spreads, leading to rising default rate predictions. The prediction intervals are appropriately wide given the extrapolation.
> 
> Let me also run a quick sanity check on the model fit and residuals to make sure the model is reasonable.



**tool call: python**

```
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_predict
from sklearn.linear_model import Ridge, BayesianRidge, QuantileRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
import warnings
warnings.filterwarnings('ignore')

hist = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')

def create_features_final(df, is_train=True):
    df = df.copy()
    df = df.sort_values('quarter').reset_index(drop=True)
    
    macro_cols = ['gdp', 'unemployment', 'hpi', 'bbb_spread', 'sp500', 'djia', 'nasdaq', 'vix', 'cpi']
    
    for col in macro_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    
    features = pd.DataFrame(index=df.index)
    features['quarter'] = df['quarter']
    
    if 'unemployment' in df.columns:
        u = df['unemployment']
        features['unemployment'] = u
        features['unemp_yoy'] = u.diff(4)
        features['unemp_qoq'] = u.diff()
        features['unemp_ma4'] = u.rolling(4, min_periods=1).mean()
        features['unemp_std4'] = u.rolling(4, min_periods=1).std()
        features['unemp_gap'] = u - u.rolling(8, min_periods=1).mean()
    
    if 'bbb_spread' in df.columns:
        s = df['bbb_spread']
        features['bbb_spread'] = s
        features['spread_yoy'] = s.diff(4)
        features['spread_qoq'] = s.diff()
        features['spread_ma4'] = s.rolling(4, min_periods=1).mean()
    
    if 'vix' in df.columns:
        v = df['vix']
        features['vix'] = v
        features['vix_yoy'] = v.diff(4)
        features['vix_qoq'] = v.diff()
        features['vix_ma4'] = v.rolling(4, min_periods=1).mean()
    
    if 'gdp' in df.columns:
        g = df['gdp']
        features['gdp'] = g
        features['gdp_yoy'] = g.pct_change(4)
        features['gdp_qoq'] = g.pct_change()
        features['gdp_ma4'] = g.rolling(4, min_periods=1).mean()
        features['gdp_gap'] = g - g.rolling(8, min_periods=1).mean()
    
    if 'hpi' in df.columns:
        h = df['hpi']
        features['hpi'] = h
        features['hpi_yoy'] = h.pct_change(4)
        features['hpi_qoq'] = h.pct_change()
        features['hpi_ma4'] = h.rolling(4, min_periods=1).mean()
        features['hpi_gap'] = h - h.rolling(8, min_periods=1).mean()
    
    if 'cpi' in df.columns:
        c = df['cpi']
        features['cpi'] = c
        features['cpi_yoy'] = c.pct_change(4)
        features['cpi_qoq'] = c.pct_change()
    
    for col in ['sp500', 'djia', 'nasdaq']:
        if col in df.columns:
            features[f'log_{col}'] = np.log(df[col] + 1)
            features[f'{col}_yoy'] = df[col].pct_change(4)
    
    if 'unemployment' in df.columns and 'bbb_spread' in df.columns:
        features['unemp_x_spread'] = df['unemployment'] * df['bbb_spread']
    if 'unemployment' in df.columns and 'vix' in df.columns:
        features['unemp_x_vix'] = df['unemployment'] * df['vix']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_x_unemp'] = df['hpi'] * df['unemployment']
    if 'gdp' in df.columns and 'unemployment' in df.columns:
        features['gdp_x_unemp'] = df['gdp'] * df['unemployment']
    if 'hpi' in df.columns and 'unemployment' in df.columns:
        features['hpi_change_x_unemp'] = df['hpi'].pct_change(4) * df['unemployment'].diff(4)
    
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.ffill().bfill()
    
    if is_train:
        features['default_rate'] = df['default_rate']
    
    return features

train_feat = create_features_final(hist, is_train=True)
scenario_feat = create_features_final(scenario, is_train=False)

X = train_feat.drop(['quarter', 'default_rate'], axis=1)
y = train_feat['default_rate']
X_scenario = scenario_feat.drop(['quarter'], axis=1)

selector = VarianceThreshold(threshold=1e-8)
X_var = selector.fit_transform(X)
kept = X.columns[selector.get_support()]
X = X[kept]
X_scenario = X_scenario[kept]

corr_matrix = X.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [c for c in upper.columns if any(upper[c] > 0.95)]
X = X.drop(columns=to_drop)
X_scenario = X_scenario.drop(columns=to_drop)

k = min(15, X.shape[1])
selector_k = SelectKBest(f_regression, k=k)
X_k = selector_k.fit_transform(X, y)
selected = X.columns[selector_k.get_support()]
X_sel = X[selected]
X_scenario_sel = X_scenario[selected]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sel)

# Fit best model (RandomForest based on CV) and check residuals
rf = RandomForestRegressor(n_estimators=500, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1)
rf.fit(X_scaled, y)

# In-sample predictions
y_pred_train = rf.predict(X_scaled)
residuals = y - y_pred_train

print("=== In-sample Fit Diagnostics ===")
print(f"Train R^2: {rf.score(X_scaled, y):.4f}")
print(f"Residual mean: {residuals.mean():.6f}")
print(f"Residual std: {residuals.std():.6f}")
print(f"Residual min: {residuals.min():.6f}")
print(f"Residual max: {residuals.max():.6f}")

# Time series plot of actual vs predicted
print("\nActual vs Predicted (last 20 quarters):")
for i in range(-20, 0):
    q = hist.iloc[i]['quarter']
    actual = hist.iloc[i]['default_rate']
    pred = y_pred_train[i]
    print(f"  Q{q}: actual={actual:.6f}, pred={pred:.6f}, resid={actual-pred:.6f}")

# Feature importance
importances = pd.Series(rf.feature_importances_, index=selected).sort_values(ascending=False)
print("\nFeature Importances:")
for feat, imp in importances.items():
    print(f"  {feat}: {imp:.4f}")

# Check if predictions.csv exists and is valid
preds = pd.read_csv('predictions.csv')
print(f"\n=== predictions.csv ===")
print(preds.to_string(index=False))
print(f"\nShape: {preds.shape}")
print(f"Columns: {preds.columns.tolist()}")
print(f"Quarters: {preds['quarter'].tolist()}")
```

## [45] tool

=== In-sample Fit Diagnostics ===
Train R^2: 0.7008
Residual mean: -0.000053
Residual std: 0.006390
Residual min: -0.015653
Residual max: 0.031434

Actual vs Predicted (last 20 quarters):
  Q61.0: actual=0.031162, pred=0.026711, resid=0.004451
  Q62.0: actual=0.032309, pred=0.027517, resid=0.004792
  Q63.0: actual=0.017875, pred=0.019943, resid=-0.002068
  Q64.0: actual=0.029139, pred=0.029207, resid=-0.000068
  Q65.0: actual=0.018354, pred=0.021126, resid=-0.002772
  Q66.0: actual=0.027076, pred=0.024641, resid=0.002435
  Q67.0: actual=0.018774, pred=0.020658, resid=-0.001884
  Q68.0: actual=0.022429, pred=0.022342, resid=0.000087
  Q69.0: actual=0.041501, pred=0.031543, resid=0.009958
  Q70.0: actual=0.026118, pred=0.032480, resid=-0.006362
  Q71.0: actual=0.033850, pred=0.026012, resid=0.007838
  Q72.0: actual=0.020619, pred=0.023076, resid=-0.002457
  Q73.0: actual=0.009220, pred=0.016482, resid=-0.007262
  Q74.0: actual=0.015003, pred=0.018015, resid=-0.003012
  Q75.0: actual=0.016439, pred=0.022480, resid=-0.006041
  Q76.0: actual=0.029767, pred=0.025905, resid=0.003862
  Q77.0: actual=0.029153, pred=0.026740, resid=0.002413
  Q78.0: actual=0.024123, pred=0.027757, resid=-0.003634
  Q79.0: actual=0.029878, pred=0.028809, resid=0.001069
  Q80.0: actual=0.011391, pred=0.017683, resid=-0.006292

Feature Importances:
  unemployment: 0.3214
  unemp_gap: 0.1179
  hpi_qoq: 0.0624
  unemp_yoy: 0.0567
  unemp_std4: 0.0529
  gdp: 0.0525
  unemp_ma4: 0.0524
  unemp_x_spread: 0.0493
  hpi_change_x_unemp: 0.0489
  unemp_qoq: 0.0480
  hpi: 0.0427
  hpi_gap: 0.0380
  hpi_x_unemp: 0.0290
  hpi_yoy: 0.0229
  log_sp500: 0.0050

=== predictions.csv ===
 quarter   y_pred  y_lower  y_upper
      81 0.027377 0.011577 0.048876
      82 0.028283 0.012575 0.049195
      83 0.028493 0.012832 0.050007
      84 0.028838 0.012602 0.050127
      85 0.029475 0.012853 0.049074
      86 0.030315 0.012624 0.050211
      87 0.032625 0.013345 0.049874
      88 0.033245 0.012672 0.051169
      89 0.033595 0.012870 0.051171

Shape: (9, 4)
Columns: ['quarter', 'y_pred', 'y_lower', 'y_upper']
Quarters: [81, 82, 83, 84, 85, 86, 87, 88, 89]


## [46] assistant

**[reasoning]**

> The predictions look reasonable. The model has a decent in-sample R^2 of 0.70, with unemployment being the most important feature (which makes sense for default rate modeling). The predictions show an increasing default rate trend from ~2.7% to ~3.4% over the stress scenario, which aligns with the rising unemployment, falling GDP, falling HPI, and widening credit spreads in the scenario.
> 
> The prediction intervals are reasonably wide (approximately 1.2% to 5.1%), reflecting the forecast uncertainty, especially since the scenario pushes some variables beyond historical ranges.
> 
> Let me verify the predictions one more time and ensure the CSV is properly formatted with the exact column names required: quarter, y_pred, y_lower, y_upper.
> 
> The CSV looks correct:
> - 9 rows (one per scenario quarter)
> - Columns: quarter, y_pred, y_lower, y_upper
> - Values as fractions (not percentages)
> 
> Let me also do a quick sanity check - the scenario shows rising unemployment (5.2% to 7.4%), falling GDP (152.6 to 140.3), falling HPI (288 to 246), rising BBB spread (1.6% to 2.6%), rising VIX (14.6 to 22.9). These are all stress signals that should increase default rates. The model predicts rising defaults from 2.7% to 3.4%, which is reasonable.
> 
> I think the predictions are solid. Let me submit.

The predictions look solid. The model captures the stress scenario dynamics (rising unemployment, falling GDP/HPI, widening spreads) with default rates increasing from ~2.7% to ~3.4% and appropriately wide 95% prediction intervals (~1.1% to ~5.1%). The in-sample fit is reasonable (R²=0.70) with unemployment as the dominant feature.


**tool call: submit**

```
Predictions written to predictions.csv with 9 rows (quarters 81-89), columns quarter, y_pred, y_lower, y_upper. The ensemble model (weighted by CV performance of Bayesian Ridge, Quantile Regression, Random Forest, Gradient Boosting) predicts default rates rising from 2.74% to 3.36% over the stress horizon, with 95% prediction intervals of approximately [1.1%, 5.1%].
```

## [47] tool

Predictions written to predictions.csv with 9 rows (quarters 81-89), columns quarter, y_pred, y_lower, y_upper. The ensemble model (weighted by CV performance of Bayesian Ridge, Quantile Regression, Random Forest, Gradient Boosting) predicts default rates rising from 2.74% to 3.36% over the stress horizon, with 95% prediction intervals of approximately [1.1%, 5.1%].

