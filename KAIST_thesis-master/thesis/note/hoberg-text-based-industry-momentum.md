# Hoberg et al - Text-Based Industry Momentum (2018)

Journal of Financial and Quantitative Analysis

## 1. Introduction

- TNIC(Text-based Network Industry Classification) is defined and researched in (Hoberg and Philips 2016)

### 1.1 Central findings using TNIC

1. Industry momentum profits are highly robust and substantially larger than previously documented when TNIC is used
    - Grundy and Martin (2001): SIC(Standard Industrial Classification) industry momentum is not robust to the bid-ask bounce and to lagging the portfolio formation by 1 month.
    - But we show that industry momentum is substatially more important for less visible text-based industry peer firms, and this stronger form of industry momentum is highly robust to the issues raised by Grundy and Martin
2. Inattention to shocks to less visible industry peers can explain these large industry momentum profits
    - Hong and Stein (1999), Barberis, Shleifer, and Vishny (1998) suggest that inattention or slow-moving information might also be a key driver of momentum.
    - 5 key results that support our conclusion that inattention is likely a central explanation for the industry momentum:
        1. The economic magnitudes are too large to be explained by simple differences in the information content of industry classifications.
            - Hoberg and Phillips (2016) find that TNIC is roughly 25%~40% more informative than SIC codes in their ability to explain a battery of variables in cross section.
            - These gains are much smaller than the 100%~200% improvements in momentum profits we document here.
        2. Industry momentum profits are stronger following shocks to specific peers that are less visible to the investment community.
            - SIC peers are widely reported in financial databases, financial reports, regulatory disclosures, etc
            - However, TNIC peer data were not widely distributed during our sample period, and the first paper focusing on TNIC peers (Hoberg and Phillips 2010) was published late in our sample period.
            - **Because TNIC and SIC both capture horizontal relatedness, we consider TNIC peers that are not SIC peers to examine the role of visiblility**
        3. We find that the timing of momentum profits due to shocks to SIC peer firms vs less visible TNIC peer firms is fundamentally different.
            - Stock return shocks to SIC peers transmit to the focal firm in 1~2 months, but when it comes to TNIC peers it takes up to 12 months to transmit.
            - We also find that own-firm share turnover increases only with significant lag when TNIC peers have high stock returns, whereas share turnover increases immediately when SIC peers are similary shocked.
            - Alternative risk-based theories predict that returns will be linked more to systematic shocks than to idiosyncratic shocks, but we find that only idiosyncratic shocks transmit slowly and generate industry momentum.
                - This is consistent with inattention and not systematic risk-based explanations
        4. We find that longer term industry momentum profits exist only when mutual funds on average do not jointly own economically linked firms.
            - Motivated by Cohen and Frazzini (2008)
            - This implies that profits are largest where there is little institutional attention to the given economic links.
            - Fewer professionals paying attention, the better.
            - We find that sector funds are more likely to own pairs of firms that are in the same SIC code but are less likely to own pairs of TNIC peer firms.
        5. Momentum profits are driven by economic links that are relatively local in the product market network.
            - We define, `broad shocks`: Those that affect a large set of related firms that are distant in the product market space
            - We define, `localized shocks`: Those that affect only a small number of proximate firms
            - We find that local TNIC peers calibrated to be as fine as the SIC-3, 4 classification generate strong momentum returns
            - Broader level TNIC-2, SIC-2 still generate statistically significant industry momentum profits, but lower.
            - Our results suggest that only 2%~5% of all firm pairs are needed to explain industry momentum.
    - Our results support these interpretations:
        - Initially, the market underreacts to large shocks to economically linked firms
        - Thus, underreaction is more severe when the economic links are less visible.
        - Time required for shocks to transmit is substantially longer.
    - Our findings indicate:
        - industry momentum profits have high Sharpe ratios because we can still diversify the portfolio and the returns are high.
        - These findings cannot be explained by a systematic risk explanation. It is consistent with inattention driving at least part of industry momentum profits.

### 1.2 Additional remarks

- We examine various momentum horizon variables
  - Using the standard 1-year momentum horizon, TNIC's momentum variable is more statistically significant in standard Fama-MacBeth return regressions.
  - Economic magnitude of TNIC peer momentum variables is considerably larger.
  - Our results are strong for both the 6-month horizon and the subsequent 6-month period from the months (t+7 ~ t+12)
- We counter recent conclusion that industry momentum is not robust to bid-ask bounce and to lagging the portfolio formation period by 1 month
  - That's because SIC was used. (Highly visible)
  - This is reversed when TNIC is used. (Less visible)
- Recent work by Cohen and Frazzini (2008) and Menzley and Ozbas (2010) suggests that inattention also plays a role in vertically linked firms.
  - But we focus on shocks horizontally linked.
  - Our objective is to address the industry momentum literature.
  - Controls for shocks to vertically linked firms do not materically affect our results.
- Our result's duration of momentum profits is roughly 12 months (long)
  - Our result is not driven by the existing short-horizon finding that large firm returns lead small firm returns especially within industry. (short)

## 2. Hypotheses

1. **First Hypothesis**: Industry momentum arises from underreaction to shocks to groups of peer firms with less visible economic links.
2. **Second Hypothesis**: Past returns of less visible industry peers are stronger than past returns of highly visible peers in simultaneous regressions predicting future returns. Momentum profits from less visible peer shocks are also economically larger than profits from highly visible peer shocks.
3. **Third Hypothesis**: Momentum profits are largest following idiosyncratic shocks to peers, as fewer investors likely pay attention to such localized shocks. Profits are smaller following more visible systematic shocks.

## 3. Data and Methods

- We extract 10-K text following Hoberg and Phillips (2016)
  - Make a DB of business descriptions from SEC EDGAR
  - Date range: 1996~2011
  - Business descriptions appear as Item 1
- Our focus is on publicly traded firms in the CRSP database
  - CRSP monthly returns database is our primary database
- To use lag structure by Fama and Fench (2000), our starting point is July 1997 and ending in December 2012.
- We exclude stock price < $1 (penny stocks)

### 3.1 Asset Pricing Variables

- We construct size and book-to-market ratio variables following Davis et al. (2000) and Fama and French (1992)
  - Size variable
    - Following the lag convention, we use size variables from each June and apply them to the monthly panel to predict returns in the following 1-year interval from July to June
    - Market size is the natural log of the market capitalization
  - Book-to-Market (value) variable
    - Numerator: Book value of equity - use end of fiscal year
    - Denumerator: Market equity - use end of December of calendar year
    - Then compute log(B/M ratio)
    - Following the standard lags, this is applied to monthly panel to predict returns for the 1 year window (July of the following year ~ June of year later)
  - Momentum variable
    - 11 month period (t-12 ~ t-2) to avoid well-known 1-month reversal effect
    - But because industry momentum variables do not experience the 1-month reversal effect, we compute our baseline industry momentum variable as the average return of the given firm's industry peers over the complete window from t-12 ~ t-1.
    - We consider both (t-12 ~ t-2) and (t-12 ~ t-1) to show robustness.

### 3.2 Industry Momentum Variables

- We wocus on the return of peer firms residing in related product markets relative to a given firm
  - We define `focal firm`: "given firm" in this context.
  - Industry = focal firm + peer firms
- Central question:
  - Whether shocks to related firms generate comovement?
  - Whether the shocks disseminate slowly and thus entail prolonged return predictability

#### 3.2.1 TNIC Momentum Variable

- We use TNIC of Hoberg and Phillips (2016)
- We compute **equally-weighted** average of the simultaneous monthly stock returns of TNIC industry peers, excluding the focal firm itself.
- We use the TNIC-3 network
  - How TNIC-N is calibrated: It is calibrated to have a granularity to be comparable with SIC-N code
    - Larger N indicates more granular grouping.
  - Why TNIC-3?
    - SIC-3 Standard in the literature
    - Consistent with our hypothesis that the impact of low visibility is stronger in more localized regions. (more idiosyncratic in nature)
- We compute ex ante TNIC peers returns using **both equally-weighted and value-weighted** averages.
  - However, we focus on equal weighting.
  - It is more consistent with visibility playing an important role.
- We hypothesize: Large peers are likely subject to high attention and shocks to large peers are priced appropriately with little underreaction and thus little industry momentum.

#### 3.2.2 SIC-Based Industry Momentum Variables

- For traditional SIC-based industry momentum returns, we follow the literature to ensure consistency.
  - Follows Moskowitz and Grinblatt (1999)
  - Use highly coarse SIC-based classification
  - **value-weighted** industry peers
  - In the main specification, we use Fama-French (1997) 48 (`FF-48`) industries
    - considered more coarse than SIC-3 or TNIC-3
  - For robustness we test all of them:
        1. 20 industries from Moskowitz and Grinblatt
        2. FF-48 (This derives from SIC codes)
        3. SIC-2
        4. SIC-3

### 3.3 Industry Disparity

- We define `disparity`: The extent to which a given focal firm's less visible TNIC peers disagree with highly visible SIC peers
  - $ \text{Disparity} = 1 - \operatorname{TotalSales}( \text{TNIC-3} \cap \text{SIC-3} ) / \operatorname{TotalSales}( \text{TNIC-3} \cup \text{SIC-3} ) $
  - Why use sales weight?
    - Based on the assumption that the price of a focal firm is more likely to be influenced by larger rivals than smaller rivals.
- Our prediction: The dissemination of information should be particularly lagged when disparity is high
  - High disparity --> Fewer channels to disseminate information

### 3.4 Systematic and Idiosyncratic Risk

- Decompose any firm's monthly return into systematic + idiosyncratic component.
- Use **daily** excess return of i-th firm as Y
- Use **daily** return of market factor, HML(value) factor, SMB(size) factor and UMD(momentum) factor as X
- We can calculate `systematic return` for each day and aggregate it to monthly return.
- `idiosyncratic return` = i-th firm's monthly return - systematic return

## 4. Industry Peer Returns and Share Turnover

- Share turnover is a direct consequence of attention.
- `Share turnover` = trading volume / shares outstanding

### 4.1 **Figure 1**: Turnover following return stocks

- Plots average levels of turnover surrounding months during which either SIC/TNIC peers experienced the highest quintile of samplewide(cross-sectional) returns in the given month
- Y-axis: Relative Average Stock Turnover (of the industry) --> Event month 0's turnover scaled to 1.0
- X-axis: Relative months (-3 ~ +12)

#### 4.1.1 Graph A: Unconditional Turnover around High-Quintile SIC or TNIC Peer Shock

- Data 1: When calculated with SIC industry group
- Data 2: When calculated with TNIC industry group

#### 4.1.2 Graph B: Conditional Turnover around High-Quintile SIC Without TNIC Peer Shock & TNIC Without SIC Peer Shock

- Data 1: SIC shock without TNIC shock
- Data 2: TNIC shock without SIC shock

### 4.2 How to plot Figure 1 (My guess)

#### 4.2.1 Graph A

- For each firm i in SIC industry G, calculate peer firms' return. (At time t) --> Rsic_i_t
  - equal weight peer `return = (group_sum(return) - firm_i_return) / (N-1)` where N = number of firms in industry G
  - If we have N stocks, we have N peer returns.
- Sort these peer returns (Rsic_i_t) cross-sectionally
- If Rsic_i_t is in top quintile (**this is the event**) , save its share turnover data (from t-3 to t+12) --> vector of len = 16. Call it shtvr_i_t
- Loop over all t and all N(All stocks)
- To prevent shtvr_i_t overlapping, drop all overlapping shtvr_i_t if it comes later (earlier event date priority) --> Paper doesn't mention it. It is my original idea.
- Sum all shtvr_i_t to create a single vector data for the plot
- Do the same for TNIC industry.

#### 4.2.2 Graph B

- For each firm i in SIC industry G, calculate peer firms' return. (At time t) --> Rsic_i_t
- For the same firm i in TNIC industry G, calculate peer firms' return. (At time t) --> Rtnic_i_t
  - TNIC is "time-varying", "network" based industry classification
    - network based:
      - Remember that even if A and B are in the same TNIC industry and A and C are in the same TNIC industry, B and C are not necessarily in the same TNIC industry.
      - For example: Similarity(A, B) > threshold & Similarity(A, C) > threshold & Similarity(B, C) < threshold
    - time-varying:
      - TNIC is recalculated each year based on that year's 10-K text data.
      - So TNIC peers can change year by year.
  - You need to loop over ALL firms one by one because each firm's TNIC peers are different
- If we have N stocks, we have N peer returns for both SIC and TNIC.
- Sort Rsic_i_t cross sectionally & Sort Rtsic_i_t cross sectionally
- If Rsic_i_t is in top quintile && Rtnic_i_t is in 3rd quintile, save its share turnover data (from t-3 to t+12) --> vector of len = 16. Call it shtvr_i_t
- Loop over all t and all N
- To prevent shtvr_i_t overlapping, drop all overlapping shtvr_i_t if it comes later (earlier event date priority) --> Paper doesn't mention it. It is my original idea.
- Sum all shtvr_i_t to create a single vector data for the plot
- Do the same by switching the order of SIC and TNIC

## 5. Return Comovement

- We present summary statistics and examine the short-term relation **between the focal firm's returns and its peers' returns.**
  - To show that the peers identified using the text-based methods are indeed relevant in understanding linked firms.

### 5.1 **Table 1**: Summary Statistics

- We already have a return 2d dataset and two peer return 2d datasets (one for TNIC, one for SIC) constructed in the previous section.
  - 2d dataset: index are dates, columns are firm IDs
- Common statistics of Panel A, B, C:
  - Mean
  - Std Dev
  - Min
  - Median
  - Max
- Panel A: Summary statistics of:
  - (1) Monthly return 2d dataset (own firm, i.e., focal firm)
  - (2) Log book-to-market ratio 2d dataset
  - (3) Log market size 2d dataset
  - (4) Month t-1 past return
  - (5) Month t-2 to t-12 past return
- Panel B: Summary statistics of SIC peer return dataset
  - (1) Month t-1 past return
  - (2) Month t-1 to t-3 past return
  - (3) Month t-1 to t-6 past return
  - (4) Month t-1 to t-12 past return
- Panel C: Summary statistics of TNIC peer return dataset
  - (1) Month t-1 past return
  - (2) Month t-1 to t-3 past return
  - (3) Month t-1 to t-6 past return
  - (4) Month t-1 to t-12 past return
- Panel D: Pearson Correlations of
  - Month t own firm return
  - Month t Log Book-to-Market ratio
  - Month t Log Market Size
  - Month t-1 own firm return
  - Month t-1 SIC peer return
  - Month t-1 TNIC peer return
- Comments on Table 1:
  - std dev of own firm > std dev of SIC/TNIC peer return because peer return is averaged across many firms

### 5.2 **Table 2** Return Comovement (Fama MacBeth Regression)

- Dependent variable:
  - month t focal-firm return
- Independent variables: (RHS variables)
  - main interest variables:
    - TNIC: **use equal weight**
      - month t TNIC peer return
      - month t-1 TNIC peer return
      - month t-2 TNIC peer return
      - month t-3 TNIC peer return
      - month t-4 TNIC peer return
      - month t-5 TNIC peer return
      - month t-6 TNIC peer return
    - SIC: **use value weight**
      - month t SIC peer return
      - month t-1 SIC peer return
      - month t-2 SIC peer return
      - month t-3 SIC peer return
      - month t-4 SIC peer return
      - month t-5 SIC peer return
      - month t-6 SIC peer return
  - control variables
    - log book to market ratio (value characteristic)
    - log firm size (size characteristic)
    - month t-1 own firm return (reversion characteristic)
    - month t-2 to t-12 own firm return (momentum characteristic)
- All RHS(Right Hand Side) variables are standardized to have unit std dev before running the regression. (cross-sectional z-scores)
- Regressions:
  1. Control variables + month t TNIC peer return + month t SIC peer return
  2. Control variables + month t TNIC peer return
  3. Control variables + month t SIC peer return
  4. Control variables + month t to t-3 TNIC peer return + month t to t-3 SIC peer return
  5. Control variables + month t to t-6 TNIC peer return + month t to t-6 SIC peer return
  6. Control variables + month t-1 to t-3 TNIC peer return + month t-1 to t-3 SIC peer return
  7. Control variables + month t-1 to t-6 TNIC peer return + month t-1 to t-6 SIC peer return
- standard errors: Newey-West(2 lags)
- The results:
  - TNIC beats SIC in all specifications
  - SIC based momentum becomes negative and insignificant after 3 months

## 6. Industry Momentum

### 6.1 **Table 3** Fama-MacBeth Return Regressions: Various 1-Year Momentum Variables

- We consider momentum variables with varying horizons
  - Test the hypothesis that momentum might be partially explained by the slow dissemination of shocks to product market peers.
  - Our initial tests explore whether less visible TNIC peer returns contribute information above SIC peer returns
- Independent variables: (ex ante)
  - TNIC industry momentum
    - use equal weighting
    - past returns from month t-12 to t-1
  - SIC industry momentum
    - use value weighting
    - past returns from month t-12 to t-1
  - Control variables
    - log book to market ratio
    - log firm size
    - month t-1 own firm return
    - month t-2 to t-12 own firm return
- Dependent variable: (ex post)
  - monthly stock return (focal firm)
- This test assesses whether lagged monthly returns from more/less visible product market peers predict monthly ex post focal-firm returns.
  - More visible: SIC-based industry momentum
  - Less visible: TNIC-based industry momentum
- SIC based momentum is shorter lived
  - Only significant for smaller firms when their larger SIC peers are shocked.
  - SIC momentum might be driven by lead-lag effect between large and small firms within the same industry. (Hou, 2007)
- TNIC based momentum is longer lived
  - Robust for both small and large cap firms
  - Hou cannot explain TNIC momentum
- Sample used:
  1. Entire sample (**Panel A**)
  2. Subsample that ends before the 2008 financial crisis. Since Korean data starts from 2010, we should consider COVID crisis instead. (**Panel B**)
- Results:
  - Own firm return variables and SIC momentum variables are significant only before adding TNIC momentum variable.
  - Shows that the shocks to related product market links that are less visible can explain large fraction of the industry momentum anomaly. 
- Regressions: Do it for both Panel A and Panel B (5 * 2 = 10 regressions)
  1. Control variables + own firm past returns (t-1, t-2 to t-12)
  2. Control variables + TNIC momentum
  3. Control variables + SIC momentum
  4. Control variables + SIC momentum + own firm past returns (t-1, t-2 to t-12)
  5. Control variables + SIC momentum + TNIC momentum + own firm past returns (t-1, t-2 to t-12)
- All RHS variables are standardized to have unit std dev before running the regression. (cross-sectional z-scores)
- standard errors: Newey-West(2 lags)

### 6.2 **Table 4** Fama-MacBeth Return Regressions: Split Half-Year Variables

- The same as table 3, but divide the momentum variables into:
  - One component from month t-12 to t-7 (old 6 months)
  - Another component from month t-6 to t-1 (recent 6 months)
- Now we have:
  - TNIC momentum:
    - past returns from month t-12 to t-7
    - past returns from month t-6 to t-1
  - SIC momentum:
    - past returns from month t-12 to t-7
    - past returns from month t-6 to t-1
  - Own firm past returns using various lags
    - t-1
    - t-2 to t-6
    - t-7 to t-12
- Sample used:
  - The same as Table 3
    1. Entire sample (**Panel A**)
    2. Subsample that ends before the 2008 financial crisis. Since Korean data starts from 2010, we should consider COVID crisis instead. (**Panel B**)
- Control variables:
  - log book to market ratio
  - log firm size
  - Own firm past returns using various lags
    - t-1
    - t-2 to t-6
    - t-7 to t-12
- Regressions: Do it for both Panel A and Panel B (5 * 2 = 10 regressions)
  1. Control variables + own firm past returns (t-1, t-2 to t-6, t-7 to t-12)
  2. Control variables + TNIC momentum (t-12 to t-7, t-6 to t-1)
  3. Control variables + SIC momentum (t-12 to t-7, t-6 to t-1)
  4. Control variables + SIC momentum (t-12 to t-7, t-6 to t-1) + own firm past returns (t-1, t-2 to t-6, t-7 to t-12)
  5. Control variables + SIC momentum (t-12 to t-7, t-6 to t-1) + TNIC momentum (t-12 to t-7, t-6 to t-1) + own firm past returns (t-1, t-2 to t-6, t-7 to t-12)
- All RHS variables are standardized to have unit std dev before running the regression. (cross-sectional z-scores)
- standard errors: Newey-West(2 lags)

### A. Bid-Ask Bounce, Vertical Links, and Simultaneous Returns

- Cohen and Frazzini (2008) , Menzley and Ozbas (2010) considers vertical links 
- However, our objective is to examine whether information in our horizontal links is distinct from information in these vertical links
- Because Hoberg and Phillips (2016) document that TNIC links overlap very little with vertical links, we predict that information in both sets of links will be highly distinct. 

#### 6.4 **Table 5** Fama-MacBeth Return Regressions: Bid-Ask Bounce, Vertical Links, and Simultaneous Returns

- **Panel B** examines robustness to shocks to vertically linked firms following: 
  - Cohen and Frazzini (2008) - vertical links using customer links
    - Used Compustat segment files. 
    - Lag information on major customers by 6 months to avoid look-ahead bias.
  - Menzley and Ozbas (2010) - vertical links using the input-output tables
    - Used input-output tables 
    - Compute the average returns separately for both upstream and downstream industries for the same 2 return windows
    - Compute the average of the upstream and downstream peer returns for both return windows
    - Then reconsider the regressions in Table 3 including these 4 additional control variables (2 horizons, 2 types of vertical links)
  - 2 horizons:
    - month t-1
    - month t-2 to t-12
  - 2 types of vertical links:
    - customer links
    - input-output links
- **Panel C** examines robustness to simultaneous returns
  - Include month t SIC and TNIC peer returns as additional control variables in the regressions of Table 3
- **Panel A** examines robustness to bid-ask bounce
  
### B. Various Horizons

- To consider various horizons of the momentum variables, we consider 3-, 6-, 12-, and 24-month past returns

#### **Table 6** Fama-MacBeth Return Regressions: Various Momentum Horizons

- dependent variable:
  - month t focal-firm return
- independent variables:
  - TNIC
    - Months 1-6
    - Month 7-12
    - Month 13-24
  - SIC
    - Months 1-6
    - Month 7-12
    - Month 13-24
  - Own Firm
    - Month 1-6
    - Month 7-12
    - Month 13-24
- control variables:
  - log book to market ratio
  - log firm size
- All RHS variables are standardized to have unit std dev before running the regression. (cross-sectional z-scores)
- standard errors: Newey-West(2 lags)
- Number of regressions: 3 * 2 (entire sample & pre-crisis sample) = 6

### C. Product Market Breadth

- Test if momentum arise from shocks to more "localized" vs "broad" product market peers
- According to systematic risk premia viewponit:
  - Only broad shocks affecting many firms will be priced
  - Very visible --> less susceptible to inattention-driven anomalies. 
- In contrast, the inattention hypothesis states that shocks to local product market peers are be more important. 
  - Less visible & more idiosyncratic. 
- We consider TNIC peers at varying levels of granularity:
  - TNIC-4 (most granular)
  - TNIC-3 - TNIC-4
  - TNIC-2 - TNIC-3
  - TNIC-1 - TNIC-2 (least granular)
- We create momentum variables using these varying levels of granularity and include them simultaneously in Fama-MacBeth regressions
  - t-1 to t-12
- Other variables:
  - Own firm t-2 to t-12
  - Own firm t-1
  - SIC t-1 to t-12
- Control variables:
  - log book to market ratio
  - log firm size
- All RHS variables are standardized to have unit std dev before running the regression. (cross-sectional z-scores)
- standard errors: Newey-West(2 lags)
- Regressions:
  1. TNIC-4 momentum, TNIC(3-4) momentum, TNIC(2-3) momentum, TNIC(1-2) momentum + own firm t-1 + control variables
  2. TNIC-4 momentum, TNIC(3-4) momentum, TNIC(2-3) momentum, TNIC(1-2) momentum + own firm t-2 to t-12 + SIC t-1 to t-12 + own firm t-1 + control variables
  3. TNIC-4 momentum, TNIC(3-4) momentum + own firm t-2 to t-12 + SIC t-1 to t-12 + own firm t-1 + control variables
- Number of regressions: 3 * 2 (entire sample & pre-crisis sample) = 6

### D. Idiosyncratic and Systematic Risk

- We decompose momentum variables into component that is due to systematic risk and a component that is due to idiosyncratic risk. 
- We use projections of daily stock returns onto the daily Fama-French (1992) factors plus momentum (UMD) and then tabulate the total contribution of systematic risk projections to each firm's monthly return. 
- Idiosyncratic component = raw peer return minus the systematic peer return component

#### **Table 8** Fama-MacBeth Return Regressions: Idiosyncratic and Systematic Risk

### E. TNIC and SIC Disparity 

#### **Table 9** Fama-MacBeth Return Regressions: High- and Low- Industry Disparity

### F. Partitioning TNIC and SIC peers

#### **Table 10** Fama-MacBeth Return Regressions: Various Peer Groups

### G. Calendar-Time Portfolios

#### **Table 11** Calendar-Time Portfolios: Equal-Weighted Black-Jensen-Scholes (BJS) Alpha Test

### H. Time Series and the Financial Crisis

**Figure 2**: Equal-Weighted Cumulative Portfolio Returns

**Figure 3**: Value-Weighted Cumulative Portfolio Returns

## 7. Mutual Fund Ownership

### **Table 12** Fama-MacBeth Return Regressions: High versus Low Mutual Fund Common Ownership of Linked Peers

### **Table 13** Mutual Fund Common Ownership Regressions

## 8. Robustness

## 9. Conclusions