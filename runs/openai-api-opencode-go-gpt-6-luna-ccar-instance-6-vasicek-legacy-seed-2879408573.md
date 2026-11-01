# openai-api/opencode-go/gpt-6-luna — ccar (id=instance-6-vasicek-legacy-seed-2879408573)

- 9/9 points predicted; Winkler regret 0.068 (agent 0.130 vs oracle 0.062, degenerate 0.507); MAE 0.015; coverage 0.837; mean width 0.058.
- messages 34 | limit None | seed None

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

**tool call: bash**

```
ls -la; ls -la data; head -5 data/train.csv; echo SCENARIO; cat data/scenario.csv
```

## [3] tool

total 12
drwxr-xr-x 1 root root 4096 Nov  1 18:48 .
drwxr-xr-x 1 root root 4096 Nov  1 18:48 ..
drwxr-xr-x 2 root root 4096 Nov  1 18:48 data
total 20
drwxr-xr-x 2 root root 4096 Nov  1 18:48 .
drwxr-xr-x 1 root root 4096 Nov  1 18:48 ..
-rw-r--r-- 1 root root  801 Nov  1 18:48 scenario.csv
-rw-r--r-- 1 root root 6632 Nov  1 18:48 train.csv
quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi,default_rate
1,118.1357,5.3835,,,,,206.1819,,139.8419,0.057906
2,120.9263,4.194,,,,,209.6106,,140.2162,0.018413
3,122.1376,4.244,,,,,231.6045,,142.548,0.032449
4,121.4998,5.0109,,,,,266.4801,,146.1476,0.01775
SCENARIO
quarter,gdp,unemployment,hpi,bbb_spread,sp500,djia,nasdaq,vix,cpi
81,189.4475,6.1123,440.7895,2.4757,3155.28,2707.5744,1204.3204,16.9714,256.9787
82,186.9307,6.3683,430.1398,2.6096,2997.2036,2681.1818,1101.6521,18.4556,255.3111
83,184.4472,6.635,419.7474,2.7435,2923.8252,2684.5934,1007.7363,20.0696,253.6543
84,181.9968,6.9129,409.6061,2.8774,2935.3619,2628.5345,921.8268,21.8248,252.0083
85,179.5789,7.2024,399.7098,3.0113,2860.4207,2575.3038,843.2411,23.7335,250.3729
86,177.1932,7.504,390.0526,3.1451,2818.4892,2482.4195,771.3548,25.8091,248.7482
87,174.8391,7.8183,380.6287,3.279,2775.8612,2509.8697,705.5969,28.0662,247.134
88,172.5163,8.1457,371.4326,3.4129,2684.5635,2498.4213,645.4448,30.5207,245.5303
89,170.2244,8.4869,362.4586,3.5468,2574.3546,2488.4546,590.4206,33.1899,243.937


## [4] assistant

**tool call: bash**

```
cat > /tmp/quick.py <<'PY'
import pandas as pd
s=pd.read_csv('data/scenario.csv'); s[['quarter']].assign(y_pred=.03,y_lower=0,y_upper=.1).to_csv('predictions.csv',index=False)
PY
python /tmp/quick.py
python - <<'PY'
import pandas as pd
x=pd.read_csv('data/train.csv');print(x.shape);print(x.to_string(index=False));print(x.describe().T)
PY
```

## [5] tool

(80, 11)
 quarter      gdp  unemployment      hpi  bbb_spread     sp500      djia    nasdaq     vix      cpi  default_rate
       1 118.1357        5.3835      NaN         NaN       NaN       NaN  206.1819     NaN 139.8419      0.057906
       2 120.9263        4.1940      NaN         NaN       NaN       NaN  209.6106     NaN 140.2162      0.018413
       3 122.1376        4.2440      NaN         NaN       NaN       NaN  231.6045     NaN 142.5480      0.032449
       4 121.4998        5.0109      NaN         NaN       NaN       NaN  266.4801     NaN 146.1476      0.017750
       5 122.7031        5.2394      NaN         NaN       NaN       NaN  308.7019     NaN 149.4206      0.015145
       6 124.4073        4.8868      NaN         NaN       NaN       NaN  325.6080     NaN 154.4166      0.022096
       7 124.7114        5.8852      NaN         NaN       NaN       NaN  338.3812     NaN 156.4523      0.009019
       8 124.6294        7.1076      NaN         NaN       NaN       NaN  349.6917     NaN 156.7739      0.021769
       9 123.5072        7.6953      NaN         NaN       NaN       NaN  321.0547     NaN 155.7177      0.032043
      10 124.5559        7.9132      NaN      2.2573       NaN       NaN  329.9435     NaN 157.1777      0.030504
      11 123.5083        9.7752      NaN      2.5685       NaN       NaN  339.4883     NaN 157.5744      0.021829
      12 127.0281        7.4210      NaN      2.2356       NaN       NaN  365.5585 17.5274 157.6717      0.024346
      13 128.4485        7.7958 216.8688      2.2833       NaN       NaN  391.3983 14.6537 160.2476      0.013303
      14 127.2807        8.8212 222.2693      2.4226       NaN       NaN  384.6045 15.3532 163.2285      0.018255
      15 126.9519        9.0242 226.5904      2.5871       NaN       NaN  364.4348 17.8270 163.2625      0.027617
      16 128.6270        7.4630 224.1597      2.5630       NaN       NaN  333.1712 19.6479 161.4557      0.034803
      17 130.4303        8.0766 222.6726      2.3384       NaN       NaN  349.1118 22.2670 160.5054      0.031138
      18 132.4978        8.7354 222.8952      2.0760       NaN       NaN  380.9037 24.5396 160.3565      0.029622
      19 134.3085        7.9562 225.9118      1.7353       NaN       NaN  384.8224 20.0069 162.0516      0.033011
      20 135.1068        8.8750 225.9616      2.2704       NaN       NaN  387.3895 19.2357 160.2172      0.022143
      21 137.8969        7.2176 234.2792      1.5320       NaN       NaN  437.5172 13.6987 164.4326      0.011561
      22 139.4237        6.3515 243.9501      1.4309  508.6139  442.6283  450.2767 16.8174 168.8631      0.012700
      23 137.8641        7.8916 250.1776      1.5174  534.0476  443.0810  414.7519 18.4947 170.9678      0.028384
      24 137.8307        7.5588 251.0720      2.3556  508.0522  443.3977  363.3406 21.2753 167.5672      0.031984
      25 140.0525        7.1015 249.0873      2.1457  523.7998  445.8024  348.5671 20.3770 164.2272      0.025349
      26 141.0877        6.8513 250.5037      1.9706  574.9607  473.2823  397.2454 16.5182 164.6287      0.016359
      27 144.2805        5.4322 250.6044      1.6346  622.8300  520.5294  458.4136 13.1206 164.4866      0.026388
      28 147.5350        4.0500 249.3295      1.9250  647.7427  554.5305  492.2901 13.2064 165.9741      0.011056
      29 150.2659        3.6465 251.2118      1.7650  658.0016  532.7204  509.3886  9.6119 168.5407      0.016757
      30 152.3775        3.9252 253.4112      2.1744  632.7920  509.1967  498.6900 15.6099 169.4575      0.014137
      31 151.9558        4.1930 252.3630      2.7634  652.0195  520.1332  475.2463 20.7794 169.5092      0.031056
      32 154.1674        4.3723 254.3846      2.1537  689.1502  548.9503  541.9453 16.9752 173.8711      0.015495
      33 157.8242        4.5417 256.8280      2.2850  729.6785  575.7964  597.0559 15.8546 176.8951      0.012951
      34 158.8938        4.4437 256.4574      2.1486  803.7607  598.0293  725.6216 13.1299 178.5739      0.018497
      35 160.2248        4.4116 256.2029      2.1493  856.6613  620.5587  801.3427 12.1979 177.8112      0.010159
      36 161.2331        4.7379 255.2951      2.0926  886.1626  664.0545  845.5841 12.8820 176.6103      0.016005
      37 149.9253       13.5819 252.4308      5.5918  755.7245  551.3381  558.4359 54.3852 167.8589      0.006599
      38 147.4163        6.1463 249.1822      1.8949  794.8966  588.2102  575.6821 17.4790 169.1516      0.010400
      39 149.1642        5.3143 249.2599      1.9788  798.9625  574.7122  556.7972 20.2807 172.5391      0.024090
      40 149.2728        6.0921 256.5452      1.5652  813.5811  596.2928  552.5104 18.8416 178.1555      0.009900
      41 149.7084        7.1548 256.0341      1.5356  875.7381  640.6426  618.0851 19.1497 181.5238      0.023451
      42 151.7338        5.9251 253.4233      2.0074  869.9089  632.9143  558.5536 24.2644 186.5473      0.016434
      43 151.4770        6.5351 256.4013      1.7006  937.1728  662.1508  585.3516 20.0391 193.0166      0.013434
      44 152.0335        6.4016 260.2748      1.7937 1018.1446  683.9009  633.5021 19.0714 197.8281      0.015216
      45 154.9806        5.9596 271.0540      1.6845 1127.8719  760.6418  726.2260 16.8811 203.6243      0.023523
      46 153.9812        6.6167 276.5247      1.9064 1132.4376  760.9649  696.6299 24.0622 206.4967      0.023591
      47 156.4810        5.3396 282.4338      1.8715 1221.4173  781.4503  739.2550 23.7348 207.8647      0.014160
      48 159.9802        4.6971 291.4282      1.4063 1208.0914  819.8405  760.3926 24.9566 214.3718      0.006697
      49 157.8626        5.4117 299.9768      1.9542 1200.8016  821.8033  719.2939 23.1727 219.6000      0.020122
      50 158.4688        5.8991 298.2314      1.6818 1239.4418  821.3390  697.0827 20.8138 221.6623      0.017235
      51 157.2025        7.8867 298.3681      1.8116 1286.4671  854.5997  746.0643 20.7618 222.1724      0.036361
      52 158.9153        7.2343 295.9835      1.7588 1391.9169  903.5379  823.4491 24.5558 220.8316      0.023670
      53 159.5311        7.9183 298.4388      1.6255 1418.4591  939.8682  875.6285 20.6428 223.1625      0.019091
      54 162.0395        6.8858 304.8622      1.7261 1541.8274 1039.9381 1000.8826 20.8625 226.9631      0.017708
      55 163.3487        6.3550 308.3361      2.3875 1506.1976 1023.4204  899.5267 25.3374 224.6748      0.026145
      56 168.0820        4.7837 304.7995      2.5148 1566.5196 1085.4435  927.9231 21.5090 224.6347      0.040987
      57 169.9746        4.4243 304.0985      2.6074 1609.1778 1104.6961  905.4188 17.3558 222.8687      0.035746
      58 170.3433        4.9125 292.7437      2.8549 1772.6928 1200.7442 1018.6276 16.0053 220.4957      0.028072
      59 170.2150        5.5410 294.7521      2.9352 1774.3897 1285.3075 1032.1880 15.5155 221.9305      0.030932
      60 174.6674        4.1437 308.1172      2.9177 1817.4279 1332.4256  987.0562 16.5169 226.4747      0.056742
      61 173.2591        4.6588 323.1068      2.8453 1874.3647 1356.8565 1018.8284 11.4648 231.2021      0.026463
      62 173.8911        4.3850 330.7625      2.9129 1955.5314 1378.3823 1030.4861 14.3241 234.5414      0.020672
      63 177.5113        4.0598 332.2210      2.8240 2219.3068 1521.6141 1249.4219  8.7440 238.1634      0.031457
      64 177.8298        4.2374 334.4654      2.7062 2254.2079 1591.7541 1268.6028 10.5863 236.1272      0.025416
      65 176.1794        5.5071 332.3271      3.1956 2317.6432 1624.3332 1236.5005 14.6292 233.7489      0.067846
      66 173.2351        6.8233 333.8266      3.6716 2387.7833 1663.9336 1228.7659 22.2026 229.1355      0.043787
      67 174.1293        6.3240 345.1145      3.3275 2443.3111 1745.4162 1245.3735 20.2494 227.3205      0.054151
      68 172.7739        5.8963 357.9856      3.2671 2460.0463 1734.8930 1194.3937 22.0208 228.2320      0.041487
      69 173.9401        5.5755 369.1470      3.3196 2490.8705 1840.7219 1170.4101 23.5074 229.5563      0.048401
      70 174.5795        4.5566 378.3077      3.5024 2487.3549 1975.7467 1115.6667 26.9170 229.4964      0.033304
      71 176.8675        4.2191 380.8089      3.5333 2378.2261 1949.9136  940.9966 31.6762 230.8488      0.048797
      72 178.8516        3.6012 391.4000      3.3810 2333.7212 1961.2032  919.0355 24.8708 233.4274      0.042397
      73 180.3217        3.9905 400.7571      3.2470 2424.5875 1998.9174  915.3058 24.4880 231.1717      0.056338
      74 183.7907        4.0582 401.6903      2.8279 2836.4551 2295.6357 1222.8370 13.8634 232.0560      0.044175
      75 184.6833        5.3912 409.8035      2.5881 2969.4394 2408.0633 1318.4918 10.4974 237.4959      0.029859
      76 184.0288        5.8748 424.5705      2.4302 3055.6405 2536.0379 1360.2489 16.8011 240.9621      0.021518
      77 185.2981        5.6980 438.6278      2.2466 3140.4818 2632.7385 1405.2286 16.0561 246.6250      0.018605
      78 189.7900        5.4037 453.1241      1.7419 3249.6864 2727.4995 1417.7193 15.9722 254.3398      0.039494
      79 189.9217        6.5123 451.4167      1.8573 3201.2712 2770.1498 1393.0189 17.3313 261.0988      0.027637
      80 191.9983        5.8666 451.7029      2.3418 3143.1820 2747.3576 1316.5568 15.6065 258.6572      0.028035
              count         mean  ...          75%          max
quarter        80.0    40.500000  ...    60.250000    80.000000
gdp            80.0   153.550007  ...   172.889200   191.998300
unemployment   80.0     6.025370  ...     7.119400    13.581900
hpi            68.0   297.166962  ...   332.247525   453.124100
bbb_spread     71.0     2.350152  ...     2.734800     5.591800
sp500          59.0  1544.587308  ...  2325.682200  3249.686400
djia           59.0  1166.441392  ...  1644.133400  2770.149800
nasdaq         80.0   713.598375  ...   990.512800  1417.719300
vix            69.0    18.979872  ...    21.509000    54.385200
cpi            80.0   194.079446  ...   227.052450   261.098800
default_rate   80.0     0.026277  ...     0.031999     0.067846

[11 rows x 8 columns]


## [6] assistant

**tool call: python**

```
import pandas as pd, numpy as np
x=pd.read_csv('data/train.csv'); y=x.default_rate
print(x.corr(numeric_only=True)['default_rate'])
for c in x.columns[1:-1]:
 z=x[c];print(c, 'corr',z.corr(y), 'delta',z.diff().corr(y), 'lag',z.shift(1).corr(y), 'next',z.shift(-1).corr(y))

```

## [7] tool

quarter         0.369655
gdp             0.332008
unemployment   -0.170066
hpi             0.470915
bbb_spread      0.470039
sp500           0.575056
djia            0.536247
nasdaq          0.374526
vix             0.039132
cpi             0.378557
default_rate    1.000000
Name: default_rate, dtype: float64
gdp corr 0.33200827662382393 delta 0.10461359670248456 lag 0.39979111454539346 next 0.3379285896662047
unemployment corr -0.170065847908352 delta -0.027040449831428722 lag -0.14006362205204184 next -0.1448999757045949
hpi corr 0.4709148548032612 delta 0.15095479227680741 lag 0.46329917387112024 next 0.484912076824904
bbb_spread corr 0.47003912803217834 delta 0.03493279539816705 lag 0.43689181562260027 next 0.5084370653917759
sp500 corr 0.5750555532133486 delta 0.15989822637032025 lag 0.5612594739453094 next 0.6073963912709847
djia corr 0.5362474705977671 delta 0.27916959935281416 lag 0.5237836868833509 next 0.5743096537963881
nasdaq corr 0.37452634128597934 delta -0.0869801567838549 lag 0.4631596989909642 next 0.38493922489508897
vix corr 0.03913238667448917 delta -0.0006329896406359048 lag 0.03943975650165111 next 0.05336349192154831
cpi corr 0.37855703386702494 delta -0.2652191960254851 lag 0.47942715747163483 next 0.3600772005791004


## [8] assistant

**tool call: python**

```
import pandas as pd,numpy as np
x=pd.read_csv('data/train.csv'); y=x.default_rate
print('autocorr', [y.autocorr(i) for i in range(1,9)])
print(pd.DataFrame({'q':x.quarter,'y':y}).groupby((x.quarter-1)//10).y.agg(['mean','std','min','max']))

```

## [9] tool

autocorr [np.float64(0.4987469347137381), np.float64(0.470698238047049), np.float64(0.30231199001976394), np.float64(0.35387946639116324), np.float64(0.43237490685680163), np.float64(0.37672185179391326), np.float64(0.4192565182027577), np.float64(0.4238340503141857)]
             mean       std       min       max
quarter                                        
0        0.025709  0.013665  0.009019  0.057906
1        0.025607  0.006859  0.013303  0.034803
2        0.019467  0.007768  0.011056  0.031984
3        0.015515  0.007428  0.006599  0.031056
4        0.017386  0.005440  0.006697  0.023591
5        0.031545  0.011619  0.017708  0.056742
6        0.039298  0.014701  0.020672  0.067846
7        0.035685  0.012382  0.018605  0.056338


## [10] assistant

**tool call: python**

```
import pandas as pd,numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge,LinearRegression
from sklearn.metrics import mean_squared_error
x=pd.read_csv('data/train.csv'); y=x.default_rate.values; cols=x.columns[1:-1]
# engineered macro change features and levels, log diffs, and lag target
v=x[list(cols)].interpolate(limit_direction='both')
F=pd.DataFrame(index=x.index)
for c in cols:
 F[c+'_lev']=v[c]
 F[c+'_d']=v[c].diff()
 F[c+'_pct']=v[c].pct_change()
F=F.replace([np.inf,-np.inf],np.nan).fillna(0)
# evaluate predictors all feature types only, standardize train fold
for name, feats in [('lev',[c+'_lev' for c in cols]),('diff',[c+'_d' for c in cols]),('pct',[c+'_pct' for c in cols]),('levdiff',[c+'_lev' for c in cols]+[c+'_d' for c in cols])]:
 for addlag in [False,True]:
  rms=[]; rmslog=[]; bias=[]
  # walk-forward tests contiguous last blocks, recursive if addlag
  for start in [48,56,64,68,72,76]:
   tr=np.arange(start); te=np.arange(start,min(start+4,80));
   # lag target use actual at forecast start then recursion
   fcols=feats+(['ylag'] if addlag else [])
   Xt=F[feats].copy(); Xv=F[feats].copy()
   Xt=Xt.iloc[tr].reset_index(drop=True); Xv=Xv.iloc[te].copy()
   if addlag: Xt['ylag']=np.r_[np.nan,y[:-1]][tr]; Xt=Xt.fillna(y[:start].mean())
   scaler=StandardScaler().fit(Xt); model=Ridge(alpha=10).fit(scaler.transform(Xt), y[tr])
   preds=[]
   lag=y[start-1]
   for ix in te:
    row=F[feats].iloc[[ix]].copy()
    if addlag: row['ylag']=lag
    p=model.predict(scaler.transform(row))[0]; preds.append(p); lag=p
   rms.extend((np.array(preds)-y[te]).tolist())
  print(name,addlag,'rmse',np.mean(np.array(rms)**2)**.5,'bias',np.mean(rms))

```

## [11] tool

lev False rmse 0.016217156670918335 bias -0.00322624242334796
lev True rmse 0.015981279594877783 bias -0.003495847812453226
diff False rmse 0.01612533471329113 bias -0.008625177008912709
diff True rmse 0.015426798905300788 bias -0.008011484278795658
pct False rmse 0.0176778080603593 bias -0.012150801684394065
pct True rmse 0.01687757070108854 bias -0.011578407956417167
levdiff False rmse 0.016039650314071556 bias -0.003346214819690074
levdiff True rmse 0.016137453699852818 bias -0.0035722734650487677


## [12] assistant

**tool call: python**

```
import pandas as pd,numpy as np
from scipy.stats import pearsonr
x=pd.read_csv('data/train.csv'); y=x.default_rate
m=x.iloc[:,1:10].interpolate(limit_direction='both')
features={}
for c in m:
 features[c]=m[c]
 features[c+'_chg']=m[c].diff()
 features[c+'_pct']=m[c].pct_change()
 features[c+'_lag']=m[c].shift(1)
 features[c+'_lagdiff']=m[c].diff().shift(1)
for n,z in features.items():
 z=z.iloc[1:]; yy=y.iloc[1:]
 print(n,round(z.corr(yy),3),round(z.corr(y.shift(1).iloc[1:]),3))

```

## [13] tool

gdp 0.41 0.338
gdp_chg 0.105 0.025
gdp_pct 0.073 0.029
gdp_lag 0.4 0.336
gdp_lagdiff -0.057 0.104
unemployment -0.165 -0.145
unemployment_chg -0.027 0.028
unemployment_pct -0.09 -0.036
unemployment_lag -0.14 -0.17
unemployment_lagdiff -0.024 -0.026
hpi 0.463 0.422
hpi_chg 0.177 0.173
hpi_pct 0.109 0.105
hpi_lag 0.465 0.423
hpi_lagdiff 0.216 0.178
bbb_spread 0.462 0.478
bbb_spread_chg 0.034 0.038
bbb_spread_pct -0.032 -0.042
bbb_spread_lag 0.429 0.44
bbb_spread_lagdiff -0.026 0.032
sp500 0.524 0.487
sp500_chg 0.185 0.19
sp500_pct 0.036 0.011
sp500_lag 0.522 0.484
sp500_lagdiff 0.008 0.19
djia 0.504 0.479
djia_chg 0.296 0.317
djia_pct 0.146 0.12
djia_lag 0.501 0.474
djia_lagdiff 0.227 0.3
nasdaq 0.443 0.385
nasdaq_chg -0.087 0.04
nasdaq_pct -0.153 -0.002
nasdaq_lag 0.463 0.379
nasdaq_lagdiff -0.163 -0.085
vix 0.047 0.051
vix_chg -0.001 0.009
vix_pct -0.08 -0.06
vix_lag 0.048 0.04
vix_lagdiff -0.009 -0.0
cpi 0.453 0.36
cpi_chg -0.265 -0.243
cpi_pct -0.293 -0.265
cpi_lag 0.479 0.384
cpi_lagdiff -0.244 -0.265


## [14] assistant

**tool call: python**

```
import pandas as pd,numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
x=pd.read_csv('data/train.csv'); y=x.default_rate.values; cols=x.columns[1:-1]
v=x[list(cols)].interpolate(limit_direction='both')
# features aligned level/diff and pct, using proper initial difference
D=pd.DataFrame(index=x.index)
for c in cols:
 D[c]=v[c];D[c+'_d']=v[c].diff();D[c+'_pct']=v[c].pct_change()
D=D.replace([np.inf,-np.inf],np.nan).fillna(0)
sets={
 'spread_unemp':['bbb_spread','unemployment'],
 'macro':['bbb_spread','unemployment','gdp_d','hpi_d','sp500_pct','vix'],
 'alllev':list(cols),
 'select':['bbb_spread','unemployment','gdp','hpi','sp500','vix'],
 'stress':['bbb_spread','unemployment','gdp_d','hpi_d','sp500_d','vix'],
 'spread':['bbb_spread'],
 'unemspread':['bbb_spread','unemployment','bbb_spread_d','unemployment_d'],
 'ytrend':['bbb_spread','unemployment','gdp_d','hpi_d','sp500_pct','vix','cpi_pct','nasdaq_pct']}
for setn,fs in sets.items():
 for lag in [0,1]:
  for alpha in [1,10,100]:
   errors=[]
   for start in [40,48,56,64,68,72,76]:
    tr=np.arange(start);te=np.arange(start,min(start+4,80)); xx=D[fs].copy()
    if lag:xx['lag']=np.r_[y[0],y[:-1]]
    sc=StandardScaler().fit(xx.iloc[tr]); mo=Ridge(alpha=alpha).fit(sc.transform(xx.iloc[tr]),y[tr]);
    yp=[]; prev=y[start-1]
    for i in te:
     row=xx.iloc[[i]].copy()
     if lag: row.loc[:,'lag']=prev
     prev=mo.predict(sc.transform(row))[0];yp.append(prev)
    errors.extend(np.array(yp)-y[te])
   print(setn,lag,alpha,round(np.mean(np.array(errors)**2)**.5,4),round(np.mean(errors),4))

```

## [15] tool

spread_unemp 0 1 0.0154 -0.0087
spread_unemp 0 10 0.0157 -0.0091
spread_unemp 0 100 0.0168 -0.0103
spread_unemp 1 1 0.0153 -0.009
spread_unemp 1 10 0.0155 -0.0092
spread_unemp 1 100 0.0165 -0.0102
macro 0 1 0.0161 -0.0084
macro 0 10 0.0161 -0.009
macro 0 100 0.017 -0.0103
macro 1 1 0.0158 -0.0084
macro 1 10 0.0159 -0.009
macro 1 100 0.0167 -0.0102
alllev 0 1 0.0151 0.002
alllev 0 10 0.0151 -0.0034
alllev 0 100 0.0161 -0.0076
alllev 1 1 0.0149 0.0013
alllev 1 10 0.0148 -0.0036
alllev 1 100 0.0158 -0.0075
select 0 1 0.0147 -0.0025
select 0 10 0.0153 -0.0056
select 0 100 0.0161 -0.0082
select 1 1 0.0143 -0.0026
select 1 10 0.0148 -0.0054
select 1 100 0.0158 -0.0081
stress 0 1 0.016 -0.0083
stress 0 10 0.0161 -0.0088
stress 0 100 0.017 -0.0102
stress 1 1 0.0158 -0.0082
stress 1 10 0.0159 -0.0087
stress 1 100 0.0167 -0.0101
spread 0 1 0.0158 -0.0093
spread 0 10 0.016 -0.0096
spread 0 100 0.0169 -0.0104
spread 1 1 0.0155 -0.0095
spread 1 10 0.0156 -0.0096
spread 1 100 0.0166 -0.0104
unemspread 0 1 0.0155 -0.0087
unemspread 0 10 0.0156 -0.0091
unemspread 0 100 0.0168 -0.0103
unemspread 1 1 0.0155 -0.0092
unemspread 1 10 0.0155 -0.0093
unemspread 1 100 0.0165 -0.0103
ytrend 0 1 0.0154 -0.0081
ytrend 0 10 0.0155 -0.0088
ytrend 0 100 0.0167 -0.0102
ytrend 1 1 0.0151 -0.008
ytrend 1 10 0.0152 -0.0088
ytrend 1 100 0.0164 -0.0102


## [16] assistant

**tool call: python**

```
import pandas as pd,numpy as np
from sklearn.linear_model import Ridge,LinearRegression
from sklearn.preprocessing import StandardScaler
tr=pd.read_csv('data/train.csv'); scn=pd.read_csv('data/scenario.csv'); y=tr.default_rate.values; cols=tr.columns[1:-1]
# feature engineering: select core transformative variables. macro features rates/deltas; current level risks
allx=pd.concat([tr[list(cols)],scn[list(cols)]],ignore_index=True).interpolate(limit_direction='both')
F=pd.DataFrame(index=allx.index)
for c in cols:
 F[c]=allx[c]
 F[c+'_d']=allx[c].diff()
 F[c+'_pct']=allx[c].pct_change()
F=F.replace([np.inf,-np.inf],np.nan).fillna(0)
sets={'all_levels':list(cols),'selectlevels':['gdp','unemployment','hpi','bbb_spread','sp500','vix','cpi'], 'transform':['unemployment','bbb_spread','gdp_d','hpi_pct','sp500_pct','djia_pct','nasdaq_pct','vix','cpi_pct'], 'stress':['unemployment','bbb_spread','gdp_d','hpi_d','sp500_d','vix_d'], 'rate':['unemployment','bbb_spread','gdp_pct','hpi_pct','sp500_pct','vix','cpi_pct'], 'levels_changes':['gdp','unemployment','hpi','bbb_spread','sp500','vix','gdp_d','hpi_pct','sp500_pct'], 'spreadunemp':['unemployment','bbb_spread']}
for name,fs in sets.items():
 for alpha in [0,1,10]:
  train=F.iloc[:80][fs].copy(); future=F.iloc[80:][fs].copy()
  sc=StandardScaler().fit(train); mo=Ridge(alpha=alpha).fit(sc.transform(train),y) if alpha else LinearRegression().fit(sc.transform(train),y)
  yp=mo.predict(sc.transform(future)); print(name,alpha,np.round(yp,4), 'full',round(yp.mean(),4))

```

## [17] tool

all_levels 0 [0.0471 0.0453 0.0483 0.0607 0.0647 0.0726 0.0741 0.0726 0.0688] full 0.0616
all_levels 1 [0.0411 0.0424 0.0448 0.0481 0.0498 0.0518 0.0536 0.0545 0.0548] full 0.049
all_levels 10 [0.0377 0.0381 0.0389 0.0398 0.0403 0.0407 0.0414 0.0417 0.0419] full 0.0401
selectlevels 0 [0.036  0.036  0.037  0.0389 0.0397 0.0408 0.0419 0.0423 0.0424] full 0.0394
selectlevels 1 [0.0362 0.0362 0.037  0.0384 0.039  0.0398 0.0406 0.0409 0.0409] full 0.0388
selectlevels 10 [0.036  0.0359 0.0362 0.0368 0.037  0.0373 0.0376 0.0376 0.0375] full 0.0369
transform 0 [0.0232 0.0224 0.025  0.0254 0.0251 0.0252 0.029  0.0279 0.0281] full 0.0257
transform 1 [0.0232 0.0225 0.025  0.0253 0.0251 0.0251 0.0288 0.0277 0.028 ] full 0.0256
transform 10 [0.0235 0.0233 0.0251 0.0251 0.0251 0.025  0.0281 0.0274 0.0276] full 0.0256
stress 0 [0.0176 0.0172 0.0203 0.0234 0.0241 0.0265 0.0284 0.0297 0.0314] full 0.0243
stress 1 [0.0179 0.0173 0.0204 0.0235 0.0241 0.0264 0.0283 0.0295 0.0311] full 0.0243
stress 10 [0.0196 0.0184 0.0211 0.0239 0.024  0.0259 0.0274 0.028  0.0291] full 0.0242
rate 0 [0.0208 0.0203 0.0218 0.0233 0.0233 0.0243 0.025  0.0251 0.0255] full 0.0233
rate 1 [0.021  0.0205 0.022  0.0234 0.0234 0.0244 0.025  0.0252 0.0256] full 0.0234
rate 10 [0.0223 0.0219 0.0231 0.0243 0.0243 0.025  0.0256 0.0257 0.026 ] full 0.0242
levels_changes 0 [0.0298 0.0288 0.031  0.0347 0.0356 0.038  0.0401 0.041  0.0417] full 0.0356
levels_changes 1 [0.0303 0.0294 0.0314 0.0344 0.035  0.0369 0.0386 0.0392 0.0399] full 0.035
levels_changes 10 [0.0313 0.0311 0.0321 0.0336 0.034  0.0351 0.0359 0.0364 0.0368] full 0.034
spreadunemp 0 [0.0274 0.0282 0.029  0.0297 0.0305 0.0312 0.0319 0.0326 0.0333] full 0.0304
spreadunemp 1 [0.0274 0.0281 0.0289 0.0297 0.0304 0.0312 0.0319 0.0326 0.0332] full 0.0304
spreadunemp 10 [0.0272 0.028  0.0287 0.0294 0.03   0.0307 0.0313 0.0319 0.0325] full 0.03


## [18] assistant

**tool call: bash**

```
cat > /tmp/makepred.py <<'PY'
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

train = pd.read_csv('data/train.csv')
scenario = pd.read_csv('data/scenario.csv')
cols = ['gdp','unemployment','hpi','bbb_spread','sp500','djia','nasdaq','vix','cpi']
# Interpolate series that start late; scenario values are appended before interpolation
# so their supplied levels are preserved and early missing history is filled sensibly.
raw = pd.concat([train[cols], scenario[cols]], ignore_index=True).astype(float)
raw = raw.interpolate(limit_direction='both')

# Regularized model on a compact set of macro levels: the small history does not
# support estimating separate effects for all nine correlated indicators.
features = ['gdp','unemployment','hpi','bbb_spread','sp500','vix','cpi']
X = raw[features]
scaler = StandardScaler().fit(X.iloc[:len(train)])
model = Ridge(alpha=10.0).fit(scaler.transform(X.iloc[:len(train)]), train['default_rate'].values)
macro_pred = model.predict(scaler.transform(X.iloc[len(train):]))

# Stabilize extrapolation with a conservative shrink toward the historical mean.
y = train['default_rate'].to_numpy()
mean = float(y.mean())
pred = 0.75 * macro_pred + 0.25 * mean
# Rates are nonnegative; the projection is also bounded to avoid extreme
# linear-model extrapolation beyond the response's observed support.
pred = np.clip(pred, 0.0, 0.09)

# A wide predictive band uses the historical residual dispersion (about 1.3pp)
# plus explicit extra allowance for out-of-range scenario extrapolation and
# accumulating horizon uncertainty. Bands are intentionally not just fitted-mean CIs.
width = 0.027 + 0.00045*np.arange(1, len(scenario)+1)
lower = np.maximum(0.0, pred - width)
upper = np.minimum(0.15, pred + width)
out = pd.DataFrame({'quarter': scenario['quarter'], 'y_pred': pred,
                    'y_lower': lower, 'y_upper': upper})
out.to_csv('predictions.csv', index=False)
assert len(out) == len(scenario) and out.columns.tolist() == ['quarter','y_pred','y_lower','y_upper']
assert out['quarter'].equals(scenario['quarter'])
print(out.to_string(index=False))
PY
python /tmp/makepred.py
cat predictions.csv; wc -l predictions.csv
```

## [19] tool

 quarter   y_pred  y_lower  y_upper
      81 0.033541 0.006091 0.060991
      82 0.033478 0.005578 0.061378
      83 0.033684 0.005334 0.062034
      84 0.034157 0.005357 0.062957
      85 0.034308 0.005058 0.063558
      86 0.034545 0.004845 0.064245
      87 0.034751 0.004601 0.064901
      88 0.034759 0.004159 0.065359
      89 0.034668 0.003618 0.065718
quarter,y_pred,y_lower,y_upper
81,0.03354086939967119,0.006090869399671194,0.06099086939967119
82,0.033478399322388566,0.005578399322388565,0.06137839932238857
83,0.033683943285990135,0.005333943285990135,0.062033943285990135
84,0.03415654197881812,0.005356541978818123,0.06295654197881811
85,0.03430807776144913,0.005058077761449134,0.06355807776144913
86,0.03454492812113338,0.004844928121133376,0.06424492812113337
87,0.03475069351983285,0.00460069351983285,0.06490069351983285
88,0.03475855334627689,0.004158553346276888,0.06535855334627688
89,0.034667825670357054,0.0036178256703570527,0.06571782567035706
10 predictions.csv


## [20] assistant

Created `predictions.csv` with one prediction and 95% interval for each of the nine scenario quarters. Verified the output has the required columns and one row per scenario quarter.

## [21] user

Please proceed to the next step using your best judgement.

## [22] assistant

**tool call: bash**

```
python - <<'PY'
import pandas as pd
p=pd.read_csv('predictions.csv'); s=pd.read_csv('data/scenario.csv')
assert p.columns.tolist()==['quarter','y_pred','y_lower','y_upper']
assert len(p)==len(s)==9
assert p.quarter.tolist()==s.quarter.tolist()
assert (p.y_lower<=p.y_pred).all() and (p.y_pred<=p.y_upper).all()
print(f'Validated {len(p)} rows; {p.columns.tolist()}')
PY
```

## [23] tool

Validated 9 rows; ['quarter', 'y_pred', 'y_lower', 'y_upper']


## [24] assistant

`predictions.csv` is complete and validated: it has the required columns and one row for each of the nine scenario quarters.

## [25] user

Please proceed to the next step using your best judgement.

## [26] assistant

No further step is specified. `predictions.csv` is complete and validated.

## [27] user

Please proceed to the next step using your best judgement.

## [28] assistant

The requested projection is complete. `predictions.csv` is in the working directory and contains the nine scenario quarters with point estimates and 95% intervals.

## [29] user

Please proceed to the next step using your best judgement.

## [30] assistant

The projection is complete. `predictions.csv` contains one point estimate and 95% interval for each of the nine scenario quarters, and the output has been validated.

## [31] user

Please proceed to the next step using your best judgement.

## [32] assistant

**tool call: submit**

```
Created and validated predictions.csv with columns quarter,y_pred,y_lower,y_upper and one row for each of the nine scenario quarters.
```

## [33] tool

Created and validated predictions.csv with columns quarter,y_pred,y_lower,y_upper and one row for each of the nine scenario quarters.

