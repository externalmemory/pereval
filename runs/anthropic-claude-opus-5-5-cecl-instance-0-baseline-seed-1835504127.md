# anthropic/claude-opus-5-5 — cecl (id=instance-0-baseline-seed-1835504127)

- Lifetime ECL regret 6.53348e-07; loss-rate MAE 6.92 bps; completion 100%. Winkler regret 0.000133019; coverage 95.0%.
- messages 12 | limit None | seed None

---

## [0] system

Build lifetime expected credit loss estimates for closed-end loan pools.
Inputs in data/:
- history.csv: segment-level quarterly observed PD (default probability), LGD
  (net loss/defaulted principal after recoveries), prepay (full prepayment
  probability conditional on no default), unemployment (percent), hpi_growth
  (year-over-year fraction). Rates are quarterly, not annualized. Historical
  observations are noisy estimates of the segment's conditional mean rates.
- forecast.csv: one supplied economic path for the reasonable-and-supportable
  period. Treat this path as the expectation scenario for this exercise.
- pools.csv: pool_id, segment, current principal balance in dollars and remaining
  contractual quarters. Pools share their segment's rates; there is no age effect.
- policy.json: forecast and reversion lengths, in quarters.

Estimate quarterly PD, LGD and prepayment from the segment history and forecast.
Beyond the forecast period, linearly blend each rate from its last forecast
value to its segment historical mean over reversion_quarters. The first
post-forecast quarter uses weight 1/reversion_quarters on history; the last uses
weight 1. Zero means immediate reversion. Afterward hold historical rates fixed.
Estimate historical means from the supplied history.

For a pool with initial balance B and remaining term T, a surviving loan's
beginning principal in quarter q (1-based) is B*(1-(q-1)/T). Default occurs first
on beginning principal. Nondefaulting loans may then prepay fully; remaining
loans make their scheduled equal-principal payment. Neither defaulted nor
prepaid loans re-enter. Recoveries are fully reflected in LGD. Within a quarter,
LGD is the conditional mean severity of defaults. There is no discounting, new
lending, renewal, extension, accrued interest or fees in this exercise.

Output the conditional MEAN total net principal loss over each pool's remaining
life, not a stress percentile or one year's loss. Write predictions.csv with
exactly pool_id,ecl,ecl_lower,ecl_upper, one row per pool, dollars with 0 <= ecl <= balance. The
portfolio allowance is the sum of pool allowances. Primary score is balance-
weighted squared error in pool lifetime loss rates; zero is perfect. Pool errors
cannot cancel. Missing, duplicate, nonfinite or out-of-bounds answers are penalized.

Python has numpy, pandas, scipy, statsmodels and scikit-learn; no internet.
Executions use fresh interpreters: save self-contained scripts to files.
Write a complete predictions.csv early and refine it before finishing.

Simulation mode: for EACH pool, also predict a central 95% interval for THAT
POOL'S OWN lifetime loss in dollars (ecl_lower, ecl_upper). Require
0 <= lower <= upper <= balance. Every pool's interval is scored on its own
against that pool's loss distribution, so do not build a single portfolio-wide
interval and split it across pools: pool losses are correlated and do not
diversify away, so an allocated portfolio interval is too narrow for each pool
and will score badly. No portfolio-level interval is requested or scored.
This is a large homogeneous pool model: no finite-loan sampling noise, so
"aggregate" below means aggregated over the many loans inside one pool, never
aggregated across pools.
History measures conditional mean rates with observation noise, not the future
systemic shocks. Fit those means as above. For each future quarter with mean PD m,
the pool's realized aggregate PD = Phi((Phi_inverse(m)+sqrt(rho)*z)/sqrt(1-rho)).
Phi is the standard normal CDF. z starts N(0,1), independent of history;
z_next = persistence*z + sqrt(1-persistence^2)*epsilon, epsilon iid N(0,1).
Use rho and persistence from policy.json. This construction preserves marginal
mean PD. Apply reversion to mean rates BEFORE drawing shocks, through maturity.
LGD and prepay remain deterministic conditional rates. Pools in a segment share
shocks; segments are independent. Apply the balance recursion on each full path,
then average lifetime losses for ecl; do not recurse on average PDs instead.
The interval describes future loss variability, not confidence in the mean.
Intervals receive balance-weighted Winkler regret, coverage and width diagnostics
separately from expected-loss error. The mean oracle is a Monte Carlo estimate.


## [1] user

Estimate lifetime expected losses and 95% prediction intervals; write predictions.csv.

## [2] assistant

Let me look at the data.

**tool call: bash**

```
cd data; ls; head -5 history.csv; wc -l *.csv; cat policy.json; cat forecast.csv | head -20; head pools.csv; python -c "import pandas as pd; d=pd.read_csv('history.csv'); print(d.describe()); print(d.segment.value_counts())"
```

## [3] tool

forecast.csv
history.csv
policy.json
pools.csv
segment,quarter,unemployment,hpi_growth,pd,lgd,prepay
A,1,5.0,0.03,0.0146,0.4685938820883749,0.0361
A,2,4.824740190507209,0.04387778880553293,0.0099,0.49228897984676967,0.0401
A,3,4.743043624240682,0.05193581947548945,0.0101,0.4113087413614516,0.0458
A,4,6.606475349245191,-5.36325748075675e-06,0.0354,0.6073802617896171,0.0241
    9 forecast.csv
  241 history.csv
   13 pools.csv
  263 total
{"forecast_quarters": 8, "reversion_quarters": 4, "simulation": "aggregate_probit_ar1_v1", "rho": 0.02, "persistence": 0.6, "interval_level": 0.95}quarter,unemployment,hpi_growth
1,5.214184032703037,0.05737439396773715
2,5.212157742316889,0.052892337686631846
3,5.2101314519307405,0.04841028140552654
4,5.208105161544593,0.04392822512442123
5,5.206078871158445,0.03944616884331592
6,5.204052580772296,0.03496411256221062
7,5.202026290386148,0.03048205628110531
8,5.2,0.026
pool_id,segment,balance,remaining_quarters
A1,A,4070313.0,4
A2,A,2172203.0,12
A3,A,5855437.0,24
A4,A,8937399.0,40
B1,B,8725002.0,4
B2,B,3576193.0,12
B3,B,1986035.0,24
B4,B,7954167.0,40
C1,C,4977525.0,4
          quarter  unemployment  hpi_growth          pd         lgd      prepay
count  240.000000    240.000000  240.000000  240.000000  240.000000  240.000000
mean    40.500000      5.386108    0.036537    0.025141    0.467375    0.067781
std     23.140466      0.780147    0.028091    0.016837    0.107431    0.027590
min      1.000000      3.365644   -0.039770    0.004100    0.208389    0.019400
25%     20.750000      4.790750    0.019259    0.014775    0.396984    0.043500
50%     40.500000      5.360814    0.038932    0.020700    0.471406    0.067550
75%     60.250000      6.005380    0.058597    0.029800    0.541744    0.089125
max     80.000000      7.002681    0.089789    0.112500    0.710974    0.146000
segment
A    80
B    80
C    80
Name: count, dtype: int64


## [4] assistant

**[reasoning]**

> CAQStwYKEAgTGAI4AUIIdGhpbmtpbmcSDD0KA5drb85sJ6DbJBoMnYGNDcoUoKs5PJjEIjCHIzrQB9259wV3t1s/SCZpZQn9pBxSgZmJrHIKL+vCHRRwPELUgT2pynCtQ0kSbmkq1AU3bQwMl/X6iHA/3MK59WO4HwkeWhP+xiGzbYY9z/5ScVVsJXVOglF7rAdVXYXyoogv12ORloI8drSA2d5Q+sOe9MBMY/oTFRReSDjdcDMjNJdLIIdxaCfo7BkFvu+uYIExYKwuvzAas76bwC5+aJvyz3M5SZ0taVUh3XzD1kADN/Kyn9uTL3bk+1khgfX7hTc1R3e62mVPHTWiPZ/XsFPrMqDnjQ4q69Nw4iJQkj2Q7tVfMsxKKfCkbArTQRcFkkK7ZU+Bh8witivEEbjsvuZGwxDTpfuY3TnVqGHFNvLk5Ib/EfnyXtnf6UZDet/F3kffuisl+sy1652VjbfRAdNcuTRsD33GfJctf896ZOBA8IT+rpUCt97xWS5TkBmQ0iQGOjy2y75v6qNUHYcria2vwTnK+x8x+OJKuJNZdJxg9qd+3c9PeEkOXpMiIGo9mCqzGxRz29PNU0/NxpSq1OY6hN1BE36ip77Fu0fFTi+YVZroAksaPwkM7/Tx+nMkx5Xg+U2i1Ub7ab8dECiAzKAxllgjXOxZysOt3a3RTloQ8/RMqxGra/eXh1fQGSkAIF0Kn/bY/jHFMneSE9N6EpmSv2fmzHck+hA1ouLKf50n2D2xnT7M0nMrfC2ofimhWr2jL+AUTFGfSGvv1uedAlSxj+onSPn2vrktSi5M3qd3dsdd7Cadv4ku3m7WjHTmSGESRe1ZwviWwucrXWA1Zz5WtLUVeprBv+/AXL3j4I96j5YB//s010O+cqLsuiJwb2b8rdM5PfsQ9SpU1YM9dmnwEmATFqrVZwatgxFDxCLjiJf8+DKQpM95jm/9tD2tKtO9nzSnmQccxBaDjLRYuKGNP/Cz5udnr/MHQQIJ3FtNFnV2i/yiIvVXQSQlMF+dm8XS5UqnpX4PXrFvNpeaHog/Yf+c5TbC701Q495uZQO8AP0QwT0WdB+mlxTQz/EJtsplc/faGAE=

**tool call: python**

```

import pandas as pd,numpy as np,statsmodels.api as sm
d=pd.read_csv('data/history.csv')
from scipy.special import logit
for s,g in d.groupby('segment'):
    X=sm.add_constant(g[['unemployment','hpi_growth']])
    for c in ['pd','lgd','prepay']:
        for f,name in [(logit,'logit'),(lambda x:x,'lin'),(np.log,'log')]:
            r=sm.OLS(f(g[c]),X).fit(); print(s,c,name,r.params.round(3).values,round(r.rsquared,3))
print(d[d.quarter<4])

```

## [5] tool

A pd logit [-7.135  0.585 -4.225] 0.978
A pd lin [-0.032  0.01  -0.084] 0.915
A pd log [-7.102  0.574 -4.139] 0.978
A lgd logit [-0.553  0.151 -9.297] 0.935
A lgd lin [ 0.365  0.037 -2.262] 0.937
A lgd log [-1.006  0.079 -4.582] 0.925
A prepay logit [-2.724 -0.142  5.905] 0.952
A prepay lin [ 0.058 -0.005  0.197] 0.94
A prepay log [-2.784 -0.136  5.701] 0.951
B pd logit [ -6.264   0.579 -11.751] 0.992
B pd lin [-0.042  0.017 -0.446] 0.889
B pd log [ -6.22    0.561 -11.28 ] 0.992
B lgd logit [ -0.891   0.149 -11.464] 0.94
B lgd lin [ 0.295  0.034 -2.669] 0.94
B lgd log [-1.246  0.092 -6.875] 0.928
B prepay logit [-1.563 -0.167  4.507] 0.98
B prepay lin [ 0.156 -0.014  0.353] 0.968
B prepay log [-1.731 -0.152  4.12 ] 0.98
C pd logit [-5.128  0.285 -4.705] 0.963
C pd lin [-0.006  0.006 -0.119] 0.947
C pd log [-5.121  0.279 -4.583] 0.963
C lgd logit [-0.159  0.114 -7.752] 0.895
C lgd lin [ 0.463  0.028 -1.887] 0.895
C lgd log [-0.764  0.05  -3.468] 0.886
C prepay logit [-2.168 -0.122  6.921] 0.971
C prepay lin [ 0.101 -0.008  0.438] 0.955
C prepay log [-2.275 -0.113  6.45 ] 0.971
    segment  quarter  unemployment  hpi_growth      pd       lgd  prepay
0         A        1      5.000000    0.030000  0.0146  0.468594  0.0361
1         A        2      4.824740    0.043878  0.0099  0.492289  0.0401
2         A        3      4.743044    0.051936  0.0101  0.411309  0.0458
80        B        1      5.000000    0.030000  0.0239  0.392347  0.0939
81        B        2      4.824740    0.043878  0.0200  0.353975  0.1047
82        B        3      4.743044    0.051936  0.0160  0.301730  0.1126
160       C        1      5.000000    0.030000  0.0215  0.540567  0.0705
161       C        2      4.824740    0.043878  0.0194  0.528995  0.0768
162       C        3      4.743044    0.051936  0.0181  0.504838  0.0864


## [6] assistant

**[reasoning]**

> CAQS9AgKEAgTGAI4AUIIdGhpbmtpbmcSDBUwPh9hOdH5FPJOZxoM1dsoEgaJltmqFuq2IjAJZAWlK8QAmy05Ba7XQbFCU/iPP5lk1Po4p6ZTQCj/dIEnOLXWY4Y0mUHWpiMGBt8qkQhNgS2oKUk4w6DqMoZ5pGc+UM5VMx2Hbg/IJaLCJhQTUlZ3SAP/3Nfh3Jq+VelUQN7VzLICr9w5V2JU2JTqHtUs69jcT5iI4WsF3Oa2vunde07GHpxbjmkS2ukG4sB/BD9elxhHz/3F+QtF2piumLQ2RHjOeY6293cwB97PzIvGY8wtGDJRtChvtf0jA1oghhPTWlxBnIG0OvQo0V8v/KZfU/I1hZG3af2W5o9GlxDkpnmSm16ET8okT+hgzOAU9HuduQTaFvjM52cka4xVKyrwKfud2jbAj1cSBNqj/7QTK8dLG2iHL2ikIglMnS6S7adjod/Ra+wGii3JAOXDUK55LHcI4UShm/wDbEQONlAIJthqWAlx3euqQ90YTTFU74cxtwFF2N3jGjlQIeZYpFI9lpLYcjoGoXOcoA9yXr2cuuA6OD++bQHA1duCS3sV/KjY5oKuVr6/OtMJwZi6Q11k3YDGmlWM4HZn7wkp0NBPMoFYNFpxOjmgsMKFm9jEVlfu3VcfEP514YbnBh5YqUgOTglnBDjTfd1N2Drl83m9f8F/04FiL7LfjrZsMNYYtcobJ2T/Zd4Xw+LqOZ9+hhdgrrSUxsBaJ6/iTOP7jSUMZ13CBsS5XwUS0w6hv9HjujLWJ5nbQ5/KymspQ/w/E5rPaDPJS7DoS0761FZ8SlLrwZDZneaNL32gU2gNw3OZOCJL5l3dhonbRGeUrhY7HAHbpJ2He5/4A6GCRr7IdMPmMgX8GCV5z81YHGudNjn5SJPHqr4lG/AWCv+9310c2Qxbg+DlXQJa9jJtruwOEOEvu9ZMIskFWmMVQIVLIE3iwb+o1/SN1ypd4HTp37u7f55ZivHd15+PkB7WPPcwjxvMNNMhelTcz8dkh7NvVVyPDtXHOY+sYaQbn+ZXB+L6Rm3nT49smR4MhH8lRIkqzh8YdBAAJ2OftQYOtu540HEOG+c0mdzGa5nNwPEdbFB6x45xagZ3P0gKPmV+2t7ed0kkZjBlc7SaEc4aV/2XWJTwEs1J3lwuOMb+e3ELf8uO6XxsX7HCy0hBHAQAQM60ZK4ZMHD7A8k3GrZcHk1zRmeYOvQov3cbRS48YwMoBB5tK1FzoP7UfYGqhnuRsMcSYu5m0QOMc1GkitBxlqT+EJKmDHAmSg+2uNMKaHPDDuqtTmdtGxB1fVSD/fmg9WkpmwZel2MkMB3+kuc5fI7uCnvlwaYDcAWCHDqo3NcbFBLKL0sBK1RiF7p0bGT/eeJ3HikGVzNVfcOeHcQ+jSqUnstQHzynwbMxmVxReNgltHQlOUQufiIDb2XXhOhXaAbkz/2raziHeGMarQCAONI4XecK6eY2Loa1p0dOjTvajFTNaGN140ByhUvZQil7XhcBk3m0I5gYAQ==

**tool call: bash**

```
cat > run.py <<'EOF'
import pandas as pd,numpy as np,statsmodels.api as sm,json
from scipy.stats import norm
d=pd.read_csv('data/history.csv');f=pd.read_csv('data/forecast.csv');P=pd.read_csv('data/pools.csv')
pol=json.load(open('data/policy.json'));F=pol['forecast_quarters'];R=pol['reversion_quarters'];rho=pol['rho'];ph=pol['persistence']
Tmax=P.remaining_quarters.max();rng=np.random.default_rng(1);N=200000
out=[]
for s,g in d.groupby('segment'):
    X=sm.add_constant(g[['unemployment','hpi_growth']]);Xf=sm.add_constant(f[['unemployment','hpi_growth']],has_constant='add')
    paths={}
    for c in ['pd','lgd','prepay']:
        m=sm.GLM(g[c],X,family=sm.families.Binomial()).fit(scale='X2')
        fc=m.predict(Xf).values[:F];h=g[c].mean()
        rev=[fc[-1]+(h-fc[-1])*k/R for k in range(1,R+1)]
        p=np.concatenate([fc,rev,np.full(max(Tmax-F-R,0),h)])[:Tmax];paths[c]=p
        print(s,c,np.round(p[:14],4),round(h,4))
    z=rng.standard_normal(N);PD=np.empty((N,Tmax))
    a=norm.ppf(paths['pd'])
    for q in range(Tmax):
        PD[:,q]=norm.cdf((a[q]+np.sqrt(rho)*z)/np.sqrt(1-rho))
        z=ph*z+np.sqrt(1-ph**2)*rng.standard_normal(N)
    for _,r in P[P.segment==s].iterrows():
        T=r.remaining_quarters;B=r.balance;surv=np.ones(N);L=np.zeros(N)
        for q in range(T):
            bp=B*(1-q/T);L+=surv*PD[:,q]*bp*paths['lgd'][q]
            surv=surv*(1-PD[:,q])*(1-paths['prepay'][q])
        out.append((r.pool_id,L.mean(),np.quantile(L,.025),np.quantile(L,.975)))
o=pd.DataFrame(out,columns=['pool_id','ecl','ecl_lower','ecl_upper']);o.to_csv('predictions.csv',index=False)
o['rate']=o.ecl/P.set_index('pool_id').loc[o.pool_id].balance.values;print(o)
EOF
python run.py
```

## [7] tool

A pd [0.0131 0.0133 0.0135 0.0138 0.014  0.0143 0.0145 0.0148 0.0155 0.0163
 0.0171 0.0179 0.0179 0.0179] 0.0179
A lgd [0.4262 0.4362 0.4464 0.4566 0.4668 0.4771 0.4873 0.4976 0.4933 0.4891
 0.4848 0.4805 0.4805 0.4805] 0.4805
A prepay [0.0422 0.0411 0.0401 0.0391 0.0382 0.0372 0.0363 0.0354 0.0359 0.0365
 0.037  0.0376 0.0376 0.0376] 0.0376
B pd [0.0195 0.0205 0.0216 0.0227 0.0239 0.0251 0.0264 0.0278 0.0293 0.0308
 0.0323 0.0338 0.0338 0.0338] 0.0338
B lgd [0.3161 0.3272 0.3385 0.3501 0.3618 0.3736 0.3856 0.3978 0.3932 0.3887
 0.3841 0.3795 0.3795 0.3795] 0.3795
B prepay [0.1018 0.1    0.0983 0.0965 0.0948 0.0932 0.0915 0.0899 0.0906 0.0914
 0.0921 0.0929 0.0929 0.0929] 0.0929
C pd [0.0197 0.0201 0.0205 0.0209 0.0213 0.0218 0.0222 0.0227 0.0229 0.0232
 0.0235 0.0238 0.0238 0.0238] 0.0238
C lgd [0.4978 0.5065 0.5151 0.5237 0.5323 0.5409 0.5495 0.5581 0.5541 0.5501
 0.5461 0.5421 0.5421 0.5421] 0.5421
C prepay [0.0828 0.0805 0.0783 0.0761 0.0739 0.0719 0.0698 0.0679 0.0691 0.0704
 0.0717 0.0729 0.0729 0.0729] 0.0729
   pool_id            ecl      ecl_lower     ecl_upper      rate
0       A1   55677.785854   29810.668271  9.274209e+04  0.013679
1       A2   74506.483975   48760.685370  1.073920e+05  0.034300
2       A3  351951.460719  258867.708499  4.630457e+05  0.060107
3       A4  741245.950863  580607.132477  9.260997e+05  0.082938
4       B1  128895.904318   72121.155711  2.076093e+05  0.014773
5       B2  122706.935854   82975.588005  1.724971e+05  0.034312
6       B3  103395.353765   76863.733832  1.350028e+05  0.052061
7       B4  498972.203257  386116.716249  6.307166e+05  0.062731
8       C1  114167.632299   63449.685093  1.848817e+05  0.022937
9       C2  144861.890109   96552.687269  2.058300e+05  0.050674
10      C3   78302.390532   57385.029131  1.033940e+05  0.075995
11      C4  906257.245065  695140.461526  1.153763e+06  0.092929


## [8] assistant

**[reasoning]**

> CAQSiQYKEAgTGAI4AUIIdGhpbmtpbmcSDNa62ZGltwUo5kcNChoMKuIGh09c3ag/8pHbIjBFvxO0P78TY7wr77RoBwU7eqXwbAEMWnJam56Lehw/s4PQQmgj0Py4NBGrjTetpB8qpgXylt+LClT9bH+E0J+q2TFbD1A3uA2AkJOKxBvye/wfPnOPTHtRMbJa/gwLYPWr96R93sUeA3wBWlCiUV7J1YEOyFDRQWjBIynEWxDayKqUXOHDsz8BZPHW3+YSvivZcHEy/bINg9GyutmHuSHEvQulkdF5cdYqxIeoyUfOYLQ75CIn+VxyB4fbKyv1Mc1oFBNXY2bsA6oahq/DroZ5Uxe5PVuU/vU+/ZFVnOY0gCekQI2sj7xLvWZPIyduNdICQM3xbceiThUOqdG2ecmj4lgDv2ZajSWq3fp/SAvpRdl7uLeMlIuZp4cc6pWzd3LxTJkG1NjAvMMEL5sru8hfvVJNkEqNxjokWQu7/hvBjxQijoPAQZCZCSKa+/NCti4IFR9E2mwyx5e3qJ5w/cy8PUx4nPrIkv5fXstTo5K+HVJe3T/sfSqbTgxZ6kHJ3fttbH4a+HufZOvz2VS2ZafH+al27KN+TTn5uk66FgP6Zis0GS+iPAVkb5xV2EwmdJx0oNXHhF/wCZ21f5Eyda+XPod0sPK6xN8LHe/QsXGJG+lL/NuvoI9rNwLBtFGJ6guKn+ZXgKNPRDRHSk1Vmo1xUZ+iTfGhu3eHF52QyrvY5zOGLu+5atXMnoAKkcuNyWM1etbHrOpeQtOUyLA3tSBbTW/1thJwocYUOUSZxEVk1cbzQB2ZAKldVHTm7WStuunav9h77XqlqEgDxUdcR97giwygMep7rUBPM3yuIG9qFUKzF9G4bMtpx/DJSZXmcM//+WweHIPKU6LRDK9f6AyMAs0CKtMGm58vCZsu+i/y8k95kMJNcck5RTc4ITzHAECQfsQLK4vQK47XEOYP6i43MnI/rRK819scKwSmlS++Yc12SN3QA26T+sjEZF6stg7iBMSZd/9HPHEYAQ==

**tool call: bash**

```
cat predictions.csv
```

## [9] tool

pool_id,ecl,ecl_lower,ecl_upper
A1,55677.785853678724,29810.66827106758,92742.09464918722
A2,74506.48397548987,48760.68536992171,107391.9878442312
A3,351951.46071910154,258867.70849888615,463045.6617592161
A4,741245.9508629158,580607.1324774312,926099.7490128689
B1,128895.90431762257,72121.15571113164,207609.3376226044
B2,122706.93585410237,82975.58800456705,172497.08562891398
B3,103395.35376518629,76863.73383239395,135002.78757222314
B4,498972.2032569505,386116.71624888503,630716.6474226471
C1,114167.63229926945,63449.685092840955,184881.68667993232
C2,144861.8901089846,96552.68726920534,205830.01853127195
C3,78302.39053180048,57385.029131221345,103394.01491006663
C4,906257.2450653324,695140.4615257927,1153763.2978569083


## [10] assistant

**tool call: submit**

```
predictions.csv written (12 pools: pool_id, ecl, ecl_lower, ecl_upper). Method: per-segment quasi-binomial logit GLMs for PD, LGD and prepayment on unemployment and HPI growth, applied to the forecast path. Linear 4-quarter reversion to the segment's historical sample mean, then held fixed. 200k-path Monte Carlo per segment with a shared Vasicek-probit AR(1) shock (rho=0.02, persistence=0.6). The balance recursion runs on each full path; ecl is the path mean, and the interval is that pool's own 2.5%/97.5% loss quantiles.
```

## [11] tool

predictions.csv written (12 pools: pool_id, ecl, ecl_lower, ecl_upper). Method: per-segment quasi-binomial logit GLMs for PD, LGD and prepayment on unemployment and HPI growth, applied to the forecast path. Linear 4-quarter reversion to the segment's historical sample mean, then held fixed. 200k-path Monte Carlo per segment with a shared Vasicek-probit AR(1) shock (rho=0.02, persistence=0.6). The balance recursion runs on each full path; ecl is the path mean, and the interval is that pool's own 2.5%/97.5% loss quantiles.

