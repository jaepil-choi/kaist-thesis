# Text-Based Network Industries and Endogenous Product Differentiation (2016)

Journal of Political Economy

## 1. Introduction

## 2. Objective and Methodology: From Words to Industry Classifications

### A. Objective

- Overall objective: Capture the relatedness of firms based on their product offerings to customers using a flexible network approach. 
- Our classifications provide measures of distance for all firm pairs. 
- Second objective: Allow for frequent annual updating. 
- Capture horizontal relatedness between firms, not vertical relatedness. 

### B. Capturing Relatedness between Firms

- Data range: 1996-2008
- business description sections from 10-K filings
- We limit attention to nouns and proper nouns that appear in no more than 25% of all product descriptions in order to avoid common words.
  - Proper nouns: Words that appear with the first letter capitalized at least 90% of the time in our sample of 10-Ks. 
- Omit common words
  - Omit common words that are used by more than 25% of all firms
  - Geographical words (country, state, city names)
- We exclude firms having fewer than 20 unique words from our classification algorithm
- We map firms into industries using word vectors and firm pairwise cosine similarity scores. 
- W: unique words used in the union of the document used by all firms in year t
  - W changes every year. 
- P: One-hot encoding W-vector
  - 1 if word w is used by firm i in year t, 0 otherwise
  - Because we use unique words only, frequency does not affect P
- V: normalize P to have unit length
  - $ V_i = \frac{P_i}{\sqrt{P_i \dot P_j}}$
- Q: Matrix containing the set of normalized vectors V_i for all firms i in year t
  - Shape: N_t * W
  - N_t: number of firms in year t
- Product Cosine Similarity between firms i and j in year t:
  - $ S_{i,j} = V_i \dot V_j $
  - Product Differentiation = 1 - S_{i,j}
  - Both are bound in the interval (0, 1)
- M_t: Network representation of firms
  - N_t * N_t matrix
  - Its entries are real numbers in the interval [0, 1]
  - M_t is time varying

#### **Figure 1**: Frequency distribution (number of unique words in description)

## 3. Industry Classification Methods and Firm 10-Ks

- 1. Fixed industry classifications
  - Impose transitivity on firm membership such that if firm A and firm C are in the same industry as firm B, then firms A and C are in the same industry. 
  - SIC, NAIC industries
  - heavily restricted:
    - Definition 1. "Binary Membership Transitivity Property":
      - If M_t has a binary banded diagonal form (1 on all banded diagonal and 0 elsewhere)
      - Transitivity holds. 
      - All firms are homogeneous within industries and industries are entirely unrelated to one another. 
    - Definition 2. "Fixed location property":
      - If M_t is not updated each year. 
      - time-fixed. 
- 2. Relax Transitivity and allow firms to have different sets of competitors. 
  - Relax both properties

### A. The sample of 10-Ks and the business descriptions

- Exclude firms:
  - Firms with nonpositive sales
  - Firms with assets of less than $1 million
  - Must have 1 year of lagged data (at least 2 years of data)
  - Exclude financial firms

### B. Fixed Industry Classifications Based on 10-Ks

- Skip

### C. 10-K-Based Textual Network Industry Classifications

- We use a simple minimum similarity threshold and define each firm i's industry to include all firms j with pairwise cosine similarities relative to i above a prespecified minimum threshold. 
- We focus on thresholds generating industries with the same fraction of membership pairs as SIC-3 industries. 
  - All membership pairs: N_t * (N_t - 1) / 2
  - SIC membership pairs: sum over k of n_k * (n_k - 1) / 2 for SIC-3 industries k with n_k firms.
- We calibrate the minimum similarity threshold to match the fraction of membership pairs in SIC-3 industries.
- Further refinement to mitigate the impact of document length:
  - For a firm i we compute its median score as the median similarity between firm i and all other firms in the economy in the given year. 
  - This median should be near-zero because no industry is large enough to span the entire economy.
  - We subtract these median scores from the raw scores to obtain our final scores used for each firm. 
  - Example:
    - Firm i has raw similarity scores of {0.2, 0.15, 0.1, 0.05, 0.01} with firms {A, B, C, D, E}
    - Median score = 0.1
    - Final scores = {0.1, 0.05, 0, -0.05, -0.09}
- If this final score is above the calibrated minimum similarity threshold, we assign firm j to firm i's industry.
  - Example: 
    - Minimum similarity threshold = 0.03
    - Firm i's industry includes firms A and B only.

## 4. Qualitative Assessment of Our New Industry Classifications

### A. Capturing Within-Industry Heterogeneity

### B. Ability to Capture Product and Industry Change

### C. Ability to Capture Cross-Industry Relatedness

## 5. External Validation

### A. Across-Industry Variation

### Competition and Reported Peers

## 6. Capturing Industry Change

### A. Military Intelligence and Battlefield Products

### B. Software Industry

## 7. Endogenous Barriers to Entry

## 8. Conclusions

## Appendix

### A

### B
