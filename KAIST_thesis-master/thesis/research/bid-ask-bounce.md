Great question. The short answer is: **bid–ask bounce is a 1-month, microstructure-driven negative autocorrelation**. If your predictive variable uses very recent returns, it can pick up this mechanical reversal rather than genuine information diffusion across firms or industries. Hoberg & Phillips (HP, 2018) design **Panel A of Table 5** precisely to isolate—and then remove—this contamination.

### Why those exact variables?

* **Split the peer (industry) signal into two pieces**

  * **t−2 to t−12 (11-month window):** captures *true* momentum/comovement beyond the microstructure horizon.
  * **t−1 (1-month window):** soaks up the piece most likely driven by bid–ask bounce (and other very short-term reversals). HP explicitly say Panel A “examines robustness to the bid–ask bounce critique… we divide each industry momentum variable into two parts: an 11-month term (t−2 to t−12) and a 1-month term (t−1).” 
* **Include the stock’s own past returns**

  * **Own t−2 to t−12:** standard stock-level momentum control, so industry effects aren’t just stock-specific momentum in disguise.
  * **Own t−1:** directly controls the firm’s own bid–ask/reversal component at the 1-month horizon. HP describe this exact lag structure: own-firm 1-month reversal (t−1) and 11-month momentum (t−12…t−2); industry variables use t−12…t−1 but are then split in Table 5 Panel A. 

### How does the Fama–MacBeth (FM) setup test robustness to bid–ask bounce?

1. **Each month**, run a cross-sectional OLS of next-month stock returns on:
   size, B/M, **own t−1**, **own t−2…t−12**, **industry t−1**, **industry t−2…t−12** (TNIC and/or FF-48).
2. **Average the slopes over time** (FM step 2) and test with NW errors.
3. **Diagnosis:**

   * If **t−1 coefficients are significantly negative** (reversal) while **t−2…t−12 industry coefficients remain positive and significant**, the predictive industry effect is **not** an artifact of bid–ask bounce.
   * That is exactly what HP report in Panel A: industry (TNIC) **t−2…t−11** positive and significant, while **t−1** is negative (classic 1-month reversal). They also standardize all RHS variables so magnitudes are comparable “for ease of comparison.”  

### Why this addresses Grundy & Martin’s concern?

Grundy & Martin show the **immediate post-formation month** can drive results and is particularly susceptible to **bid–ask bounce** and other microstructure effects; skipping one month or explicitly **isolating t−1** is the standard fix. HP’s specification operationalizes that fix inside FM regressions: **control for t−1 directly and test whether the longer-horizon (t−2…t−12) industry component still predicts**. GM themselves emphasize inserting a one-month gap to avoid very short-term reversals (the essence of “bid–ask bounce”).  

### Read-off in HP Table 5 Panel A (what to look for)

* **Industry (TNIC) t−2…t−11:** positive, significant.
* **Industry t−1:** negative (reversal), significant.
* **Own t−2…t−12:** positive, significant (stock momentum control).
* **Own t−1:** negative (reversal), significant.
  This pattern is exactly what you expect if **bid–ask bounce lives at t−1**, while **true comovement/underreaction lives over t−2…t−12**. 

**Bottom line:** By **splitting the industry signal** and **including both own and industry t−1 controls** in an FM regression, HP show their industry-based predictability **survives** once the 1-month microstructure effect is carved out—i.e., it’s **robust to bid–ask bounce**. 
