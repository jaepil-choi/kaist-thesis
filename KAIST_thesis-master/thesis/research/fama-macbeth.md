<<AI>>

Great—here’s **exactly** how to run Hoberg & Phillips (2018) **Table 2: Return Comovement** using Fama–MacBeth.

---

# What you regress (per paper)

* **Unit of observation:** firm-month, July 1997–Dec 2012. Dependent variable is the **own-firm monthly stock return** at month (t). 
* **Key RHS (peer returns), excluding the focal firm:**

  * **TNIC-3 peer return** (equal-weighted).
  * **FF-48 peer return** (value-weighted).
  * Use **simultaneous (month (t))** and **lags (t-1,\dots,t-6)** as indicated by each column/spec. 
* **Controls (included but often not tabulated):** log **book-to-market**, log **size**, a **dummy for negative B/M**, and **own-firm momentum** defined as months (t-12) to (t-2) (i.e., skip (t-1) for reversal). Also include the **own-firm (t-1) return** separately as a reversal control.  
* **Standardization:** “All right-hand-side variables are standardized to **stdev = 1**” before running the regressions (do **not** standardize the dependent variable). Use cross-sectional standardization each month. 
* **Inference:** Fama–MacBeth across months with **Newey–West (2 lags)** on the time series of monthly slopes. 

---

# How to construct the variables

For each firm (i) and month (t):

* **TNIC peer return (equal-weight, exclude (i)):**
  [
  R^{\text{TNIC}}*{i,t}=\frac{1}{|G^{\text{TNIC3}}*{i,t}!\setminus!{i}|}\sum_{j\in G^{\text{TNIC3}}*{i,t},,j\neq i} R*{j,t}.
  ]

* **FF-48 peer return (value-weight, exclude (i)):**
  [
  R^{\text{FF48}}*{i,t}=\frac{\sum*{j\in G^{\text{FF48}}*{i}\setminus{i}} \text{MV}*{j,t-1},R_{j,t}}{\sum_{j\in G^{\text{FF48}}*{i}\setminus{i}} \text{MV}*{j,t-1}}.
  ]
  (Weights are **equal** for TNIC-3 and **value-weighted** for FF-48; in both, **exclude the focal firm**.) 

* **Controls:**

  * ( \log(\text{Size})): June market cap carried forward July–June.
  * ( \log(\text{B/M})): book from fiscal year, divided by Dec market value, carried forward in the standard way.
  * **Momentum (own-firm)**: cumulative return from (t-12) to (t-2).
  * **Reversal**: own-firm return at (t-1).  

---

# The Fama–MacBeth recipe (what you actually run)

For **each month (t)**:

1. **Standardize** all RHS variables **cross-sectionally** among firms observed at (t) so each has **stdev = 1** (z-scores). Keep dummies unscaled. 
2. Run the **cross-sectional OLS**:
   [
   R_{i,t}
   =\alpha_t
   +\sum_{k\in\mathcal{K}} \beta_{k,t},\widetilde{X}*{i,t}^{(k)}
   +\varepsilon*{i,t},
   ]
   where ( \widetilde{X} ) are the standardized RHS (peers at (t) and/or lags, plus controls).
3. Collect the slopes ( {\beta_{k,t}}_t ), compute **time-series means** ( \bar\beta_k ), and **Newey–West(2)** standard errors over (t). Report ( \bar\beta_k ) and t-stats. 

---

# Match the seven Table-2 specifications

Let (P^{\text{TNIC}}*{i,t-\ell}) and (P^{\text{FF48}}*{i,t-\ell}) be the (standardized) peer returns at lag (\ell\in{0,1,\dots,6}), with (\ell=0) = “month (t)”. Let (C_{i,t}) denote the (standardized) controls.

* **(1)** (R_{i,t}=\alpha_t+\beta_{1,t}P^{\text{TNIC}}*{i,t}+\beta*{2,t}P^{\text{FF48}}*{i,t}+\delta_t'C*{i,t}+\varepsilon).
* **(2)** Same as (1) but **drop** (P^{\text{FF48}}_{i,t}).
* **(3)** Same as (1) but **drop** (P^{\text{TNIC}}_{i,t}).
* **(4)** Include **(\ell=0,1,2,3)** for both TNIC and FF-48 (8 peer regressors) + controls.
* **(5)** Include **(\ell=0,1,2,3,4,5,6)** for both (14 peer regressors) + controls.
* **(6)** Include **(\ell=1,2,3)** (lags only) for both + controls.
* **(7)** Include **(\ell=1,\dots,6)** (lags only) for both + controls.
  (Exactly the structure described in Table 2 text.) 

---

## Implementation tips (to replicate the paper)

* **Exclude the focal firm** from peer averages (both TNIC and FF-48). 
* **Equal-weight TNIC, value-weight FF-48**, and **standardize** all RHS **each month** before the cross-section. 
* Use **NW(2)** on the monthly slope series. 
* Controls follow the **standard lag conventions** (June sizing, B/M carry-forward; momentum (t-12) to (t-2); include (t-1) return for reversal).  

---

## Minimal code shape (plug into your FM loop)

* Build a monthly panel with columns:

  * `ret_t` (dependent), `peer_tnic_t`, `peer_ff48_t`, … `peer_tnic_t-6`, `peer_ff48_t-6`,
  * `log_bm`, `log_size`, `own_ret_t-1`, `own_mom_t-12_to_t-2`, and (optionally) `neg_bm_dummy`.
* For month (t): z-score all RHS across firms, run the cross-sectional OLS for the chosen spec. Save slopes.
* Average slopes over (t); compute **NW(2)** SEs on those slope series; report ( \bar\beta ) and t-stats.

That’s exactly the Table-2 procedure the paper describes (including **equal- vs value-weighting**, **RHS standardization**, and **NW(2)**).  

<<USER>>

What I want to know is WHY we are doing cross sectional OLS (step 2) before time series regression (step 1). 

<<AI>>

Short answer: in **Hoberg Table 2** there is **no “time-series (step 1)” to do**—you go straight to **cross-sectional OLS each month** and then average the slopes. The **time-series–first** step exists only in the *beta–lambda* (1973) variant where your regressors are **latent factor loadings (\beta_i)** that must be estimated. Here, your RHS are **observed characteristics/peer-return variables**, so there’s nothing to estimate in a first pass.

---

## Why cross-sectional OLS (and not time-series first) in Hoberg?

* **What FM is doing conceptually:** FM treats the pricing/forecast relation as **cross-sectional at each date**:
  [
  r_{i,t} = \alpha_t + \boldsymbol{\gamma}*t^\top \mathbf{x}*{i,t} + \varepsilon_{i,t},
  ]
  then it **averages (\boldsymbol{\gamma}_t)** over (t) and bases inference on their **time-series variation**. That’s the estimator.

* **When a time-series “step 1” is needed:** Only when (\mathbf{x}*{i,t}) are **unobserved betas** on traded factors. Then you must first run time-series regressions (r*{i,\tau}=\alpha_i+\boldsymbol{\beta}*i^\top \mathbf{f}*\tau+u_{i,\tau}) to estimate (\hat{\boldsymbol{\beta}}_i). After you have (\hat{\boldsymbol{\beta}}_i), you do the cross-sectional step to get prices of risk (\lambda_t).

* **Hoberg Table 2 is the “characteristics FM” case:** Your RHS are **TNIC/FF48 peer returns (current and lags) and firm characteristics (size, B/M, momentum, reversal)**—all **directly observed** at (t). So you **don’t** estimate anything in a preliminary time-series pass. You just:

  1. (optionally) winsorize,
  2. **cross-sectionally standardize** each RHS within month (t) (stdev = 1),
  3. run the **cross-sectional OLS at (t)**,
  4. repeat over months, then
  5. average slopes and use **Newey–West over (t)**.

* **Intuition:** Table 2 asks: *in a given month*, do firms with higher peer returns (TNIC or SIC) have higher own returns, controlling for characteristics? That’s inherently a **cross-sectional** question each month. The FM averaging then answers whether this relation holds **on average over time**.

---

## Reconciling with Cochrane / FM (1973)

* **FM (1973) beta–lambda:**
  Step 1 (time-series) exists because (\beta_i) are **not observed**; you must estimate them.
  Step 2 (cross-section) regresses (r_{i,t}) on (\hat\beta_i) to recover (\lambda_t), then averages (\lambda_t).

* **Hoberg (Table 2):**
  No latent (\beta)’s—RHS are **observables**. So the FM estimator reduces to “**cross-section each (t), then average**.” There is no “step 1” to precede it.

---

## Practical takeaway

* If your RHS are **characteristics/peer returns** → **FM = cross-section each month → average**, with HAC SEs over time.
* If your RHS are **factor betas** → **time-series first to get (\hat\beta)** → **cross-section second** to price risk.

That’s why, for Hoberg’s Table 2, you “do the cross-sectional OLS” (and never need a preliminary time-series pass).
