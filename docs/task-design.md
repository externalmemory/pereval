# Task Design: Objective Verification under N = 1

## The Problem

Econometric model quality cannot be objectively verified against real history. There is one realized macro path; backtesting on it, however the holdout is carved, measures fit to a single draw, and cannot distinguish a sound model from a lucky one (or an unlucky sound model from a degenerate one that shrinks to the mean). Any eval that scores "out-of-sample fit on real data" inherits this and rewards the wrong thing.

Pure synthetic data solves verification (the data-generating process is known, so exact answers exist and instances can be replicated without limit) but severs the connection to reality: clean simulated covariates don't exercise the judgment that makes real econometrics hard.

## The Principle

**Realism and ground truth can live in different parts of the same task.** In a conditional modeling problem, realism belongs to the covariates; ground truth only needs to exist for the response given the covariates, or for a property of the solution that is checkable without any data-generating process at all.

Objective verification must own one of: the data-generating process, a mathematical invariant, or a planted defect. It must never require owning the future. Fit to realized history is the one verification target that is banned.

## Task Families

### 1. Plasmode (Real Covariates, Planted Response): the Workhorse

Real macro series (FRED), with their true collinearity, autocorrelation, structural breaks, and short T; response series generated from a known conditional DGP (e.g., Vasicek one-factor with a planted macro loading). The agent faces realistic difficulty; the scorer knows true parameters and the true conditional law, and can draw unlimited fresh response replications for out-of-sample scoring on the same real covariate path.

- **Scoring:** oracle-anchored regret. The correct estimator's own sampling distribution (wide at T ≈ 120 quarters) is estimated by replication; the agent is scored relative   to oracle / competent-baseline / degenerate-baseline anchors, never on absolute error.
- **Misspecified variants:** some instances plant a DGP outside the obvious model class (threshold effects, regime asymmetry). Scoring switches from parameter recovery to   predictive log-density on fresh simulated continuations.
- **Author-bias risk:** the planted DGP is the author's choice. Mitigate by rotating DGP families across instances and documenting the generator. Implemented for CCAR, and load-bearing rather than cosmetic: while its law was a single fixed form with published coefficients, a good score could only show that the agent recovers *that* law, and the instance was in fact solvable in closed form straight from the source.

### 2. Estimated DGP (model-mediated resampling)

Fit a rich generator (regime-switching VAR, factor model with fat-tailed shocks) to real macro + loss history; the fitted object becomes the known DGP. Realism is inherited from data by estimation; ground truth holds by construction.

- **Circularity risk:** a Gaussian-VAR generator rewards agents that fit Gaussian VARs. Inject structure outside convenient model classes; rotate generator families.
- Note: *plain* path resampling (block bootstrap) is not a member of this family. It yields replication without ground truth: averaging a fit metric over resampled pseudo-histories reduces its variance but still measures fit, and adds splice artifacts and a stationarity assumption macro data violates. Use it only as a variance-reduction supplement, never as the verification basis.

### 3. Cross-Sectional Real Data

The N = 1 problem is specific to the time dimension. Public loan-level datasets (Freddie Mac, Fannie Mae) offer millions of real outcomes; tasks hold out *entities*, and discrimination/calibration metrics on real data carry honest error bars.

- **Scope limit:** defaults are correlated through the macro factor, so the effective N for anything macro-sensitive collapses to the number of observed cycles. Standard errors cluster by period. This family verifies ranking and level (AUC, calibration by segment), not macro sensitivity.

### 4. Discipline Traps (Process-Verifiable, no DGP Needed)

Plant a defect in otherwise real data and score its detection or avoidance mechanically from the agent's code and output:

- revised vs. real-time data vintages (FRED vs. ALFRED) in a backtest;
- a feature that mechanically contains the target (leakage);
- survivorship-filtered panels;
- holdout hygiene (does the agent's code touch data it was told is out of bounds).

One realized history suffices here: the truth is the planted defect.

### 5. Identity and Guarantee Tasks (Mathematically Verifiable)

Solutions hard to find, verifiable in seconds against an invariant:

- annual-to-quarterly rating transition matrix conversion (the Markov embedding problem: naive matrix roots yield negative/complex probabilities; verification is one matrix exponentiation plus validity checks);
- conformal / Jackknife+ prediction intervals scored on empirical coverage across simulated replications against the finite-sample guarantee;
- closed-form estimators checked against known answers on per-instance fresh data.

Instances are trivially generated per run, which also neutralizes training-set contamination for this family.

### 6. Simulator-Owned DGP (Validated Physical Simulator, Controlled Covariate)

Realism supplied by a validated numerical simulator rather than by real historical data, over a covariate the task designer controls. The implemented ballistic trajectory task is the example: a projectile point-mass simulator (py-ballisticcalc) generates y (impact height) as a function of x (distance) with noise injected into muzzle velocity and launch angle, per-run randomized per-category ballistic truth, and a held-out x range beyond the training range. The scorer owns the exact predictive distribution by Monte Carlo, so point accuracy, interval coverage, and interval sharpness are all measurable against an oracle.

Unlike family 1, the covariate is a designed grid, not messy real data, and unlike family 5 there is no closed-form invariant; the ground truth is the simulator's own output. Two design obligations are specific to this family. First, keep the held-out regime inside the simulator's validated range (for the ballistic task, rifle held-out distances stay supersonic, so the extrapolation difficulty is drag curvature rather than an unvalidated transonic regime). Second, prevent the agent from re-simulating instead of modeling. The load-bearing defense for that is opaque category identifiers plus per-run randomized generator parameters: with no known instance to look up, any simulation first requires estimating the parameters from the data, which is the task itself (and a physics-informed parameter fit is exactly what the task should reward). Generating host-side, injecting only neutral data, and running the sandbox with no network are secondary hardening: they keep the simulator and oracle out of reach and block fetching the exact generator, its reference tables, or an online equivalent. None of this prevents the agent from recognizing the domain from the data, which is legitimate and, absent the known parameters, does not shortcut the task.

The generator need not be a numerical library; a closed-form physical model qualifies. The orbital-angle tasks generate the observed angle from Kepler's laws in pure numpy. The two-body task (predict one planet's heliocentric angle) is the easier, strictly periodic case. The three-body task predicts beta, the apparent direction to an outer planet as seen from the inner observer planet, which is coupled to the inner planet's position (given by alpha), shows retrograde motion, and is quasi-periodic on the synodic period rather than a bare Kepler angle. Here alpha is essential auxiliary data, not a distractor. These targets are circular (degrees mod 360), which the shared interval scorer handles by localizing every quantity to the branch nearest the known true value before applying the linear scoring math. The submitted interval is localized as a unit rather than endpoint by endpoint, so its width survives the move; doing it separately used to rewrite the interval and credit coverage for an arc the agent never submitted. See [limitations.md](limitations.md#circular-intervals-were-rewritten-by-the-scorer).

Each orbital task ships two reference solvers that bracket it and guard against confusing a wrong basis with a hard problem: a naive harmonic (Fourier) fit and a Kepler reference that fits the true elliptical-orbit model by least squares. The harmonic fit fails on the retrograde three-body angle (it is not a Fourier series in a single period), while the Kepler reference recovers it to the noise floor and scores near the oracle. The gap between them shows the difficulty is real headroom, and the model's distance from the Kepler reference measures how far it is from the right approach. This is the concrete instance of the degenerate/competent/oracle anchoring below.

## Statistical Treatment (all Families)

- k repeated runs per task instance; many generated instances per family.
- Reported scores are anchored (degenerate → baseline → oracle), not raw.
- No leaderboard claims the sample size cannot support.
- Standard errors clustered at the task level.
- **Paired-difference comparison was prescribed here and does not work on this suite.** It was measured rather than assumed; see below.

### Pairing Is Not the Lever

The obvious reading of the tables is that they waste power: runs are paired on identical instances and the numbers are reported as unpaired mean ± 2 SD. `scripts/paired_analysis.py` tests that against the archived runs, over every model pair sharing at least three instances, and the criticism does not survive.

| Pairing scale | Pairs | Median paired / independent SD | Variance reduction |
| --- | --- | --- | --- |
| regret levels | 71 | 0.99 | 1% |
| log regret | 71 | 0.95 | 10% |

Instance difficulty is a real common factor: each model's per-instance profile rank-correlates with the mean of the others at +0.71 on ballistic, +0.42 on three-body, +0.30 on two-body and +0.27 on CCAR. But it carries almost none of the magnitude variance, because per-instance regret is dominated by whether *that* model blew up on *that* instance rather than by how hard the instance was. The effect is multiplicative, which is why the log scale recovers ten times more than the level scale and still only reaches 10%.

The reproducibility study closes the argument: the same model on byte-identical data swings by up to 30x, so the variance lives in the model-by-run interaction, and no amount of differencing across instances reaches it. The lever on variance is more runs per instance (`-T repeats=K`), not pairing.

### Anchoring and Non-Response

Three anchors, not one. The oracle gives the achievable floor and a naive or competent reference gives the practical one, but neither answers the question "does this model carry any information at all". That needs a third: the **degenerate answer**, the least informative admissible response, taken here as one constant point estimate for the whole instance with no interval. It is computed from ground truth on every run and reported as `degenerate_regret`, so it costs nothing.

It earns its place empirically. On the hyperbolic flyby task every measured model scores worse than a constant, which regret against the oracle alone cannot reveal, because a large regret and a *useless* regret look identical when the only reference is zero. On the two orbital tasks the same anchor sits in the thousands and real models beat it easily. Same metric, opposite verdicts, and only the degenerate anchor separates them.

The degenerate answer also prices abstention. A missing prediction is scored as though that answer had been submitted, floored at a multiple of the oracle for targets with almost no variation. Anchoring the penalty on the oracle instead, as this suite originally did, prices non-response at the *measurement noise* rather than at the cost of being wrong, which on tasks where a bad answer costs hundreds and the noise floor is one to four degrees makes silence the dominant strategy. See [limitations.md](limitations.md#non-response-was-cheaper-than-failure) for what that did to a published leaderboard.

Pricing is not enough on its own, because a penalty is still a number and a number still gets averaged into a cell. So a run that fails to produce complete output is reported as **unmeasured**, never as a score. The scorer cannot tell a model that declined from a provider that failed, and neither is a measurement of capability.
