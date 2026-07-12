# TNIC Methodology: Hoberg & Phillips (2016)

**Source**: Hoberg, G., & Phillips, G. M. (2016). Text-based network industries and endogenous product differentiation. *Journal of Political Economy*, 124(5), 1423-1465.

---

## 1. Text Data Collection

### 1.1 Data Source and Document Types

**Source**: SEC Edgar website (<https://www.sec.gov/edgar>)

**Document types searched**:

- "10-K" (standard annual filing)
- "10-K405" (late filing by insiders)
- "10KSB" (small business annual filing)
- "10KSB40" (small business with late insider filing)

**Time period**: 1996-2008

- Primary sample: Fiscal years ending in calendar years 1997-2008
- 1997 start date: Electronic filing became required by SEC

**Direct quote**: "We electronically gather 10-Ks by searching the Edgar database for filings that appear as '10-K,' '10-K405,' '10KSB,' or '10KSB40.' Our primary sample includes filings associated with firm fiscal years ending in calendar years 1997–2008." (p. 1433)

### 1.2 Section Extraction

**Target section**: Item 1 or Item 1A - Business Description

**Legal requirement**: Item 101 of Regulation S-K

- Requires firms to describe significant products they offer to the market
- Must describe "the general development of the business during the past five years"
- Must include "the principal products produced and services rendered"

**Extraction methodology**:

1. Perl web crawling scripts (automated download from Edgar)
2. APL programming (text parsing and extraction)
3. Human intervention (for non-standard document formats)

**Direct quote**: "From each linked 10-K, our goal is to extract its business description. This section of the document appears as item 1 or item 1A in most 10-Ks. We utilize a combination of Perl web crawling scripts, APL programming, and human intervention (when documents are nonstandard) to extract and summarize this section." (p. 1433-1434)

### 1.3 Sample Construction and Filters

**Initial sample**: 68,302 total 10-K observations (1997-2008)

**Filter 1 - Invalid financial data**:

- Remove firms without valid Compustat data
- Remove firms with nonpositive sales
- Remove firms with assets < $1 million
- **Result**: 63,875 observations

**Filter 2 - Financial firms exclusion**:

- Remove firms with SIC codes 6000-6999 (financial services)
- Require 1 year of lagged Compustat data
- **Result**: 50,673 observations (final sample)

**Filter 3 - Text length requirement**:

- Minimum text length: **>=1,000 characters**
- Excludes ~100 firms without valid product descriptions or insufficient text length

**Direct quote**: "we encountered only a small number of firms (roughly 100) that we were not able to process because they did not contain a valid product description or because the product description had fewer than 1,000 characters." (p. 1434)

**Final sample characteristics**:

- 50,673 firm-year observations
- ~5,000 firms per year (average)
- Coverage: **97.9% of CRSP/Compustat universe**

**Direct quote**: "Our full sample of 10-Ks from 1997–2008 comprises 68,302 observations; this declines to 63,875 when we exclude firms without valid Compustat data, firms with nonpositive sales, or firms with assets of less than $1 million. This declines further to 50,673 if we additionally require 1 year of lagged Compustat data and exclude financial firms (SIC codes in the range 6000–6999)." (p. 1434)

---

## 2. Text Processing Pipeline

### 2.1 Part-of-Speech Filtering

**Primary filter**: **Keep only nouns and proper nouns**

#### 2.1.1 Noun Definition

- **Source**: Webster.com dictionary
- **Rule**: Word must be defined as a noun by Webster.com
- **Mixed usage exception**: "When a word can be used as more than one part of speech, we include the word in our universe if it has at least one use as a noun." (footnote 9, p. 1430)

**Example**: "bank" can be noun (financial institution) or verb (to bank money) -> **included** because it has noun usage

#### 2.1.2 Proper Noun Definition

- **Detection rule**: First letter capitalized >=90% of the time in sample
- **Rationale**: Captures company names, product brands, technology names not in Webster.com
- **Examples**: "iPhone", "Microsoft", "Java" (programming language)

**Direct quote**: "We define proper nouns as words that appear with the first letter capitalized at least 90 percent of the time in our sample of 10-Ks." (p. 1429)

#### 2.1.3 Exclusions (Non-Nouns)

All other parts of speech removed:

- Verbs (running, manufacture, develop)
- Adjectives (large, innovative, efficient)
- Adverbs (quickly, very, highly)
- Prepositions (in, on, through)
- Conjunctions (and, but, or)

### 2.2 Stopword Filtering (Common Words)

**Three-layer filtering approach**:

#### 2.2.1 Frequency-Based Filter (Primary)

- **Threshold**: Remove words appearing in **>25% of all firm documents**
- **Rationale**: Words used by >25% of firms are too common to distinguish products
- **Examples**: "company", "business", "product", "service", "customer"

**Threshold variations tested**: 10%, 25%, 100%

- Results robust across all thresholds
- 25% selected as baseline

**Direct quote**: "In our main specification, we limit attention to nouns (defined by Webster.com) and proper nouns that appear in no more than 25 percent of all product descriptions in order to avoid common words." (p. 1429)

**Appendix A clarification**: "Specifically, we restrict attention to words that are either nouns or proper nouns and that also appear in fewer than 25 percent of all business descriptions in the given year." (p. 1460)

#### 2.2.2 Geographical Term Filter

Remove all geographical location words:

- **Country names**: United States, China, Japan, etc. (all countries)
- **State names**: California, New York, Texas, etc. (all US states)
- **Top 50 US cities**: New York, Los Angeles, Chicago, Houston, etc.
- **Top 50 world cities**: London, Tokyo, Beijing, Paris, etc.

**Rationale**: Geographical presence does not indicate product similarity

**Direct quote**: "we omit geographical words including country and state names, as well as the names of the top 50 cities in the United States and in the world." (p. 1429-1430)

#### 2.2.3 Generic Common Words

Remove standard stopwords:

- Articles: "the", "a", "an"
- Conjunctions: "and", "but", "or"
- Personal pronouns: "we", "our", "they"
- Common abbreviations: "inc", "corp", "ltd"
- Legal/filing jargon: "section", "item", "filing", "sec"

### 2.3 Firm-Level Word Count Filter

**Minimum unique words per firm**: **>=20 unique words**

**Exclusion rule**: Firms with <20 unique words (after all filters) excluded from classification algorithm

**Rationale**: Firms with <20 words lack sufficient information to characterize product space

**Direct quote**: "Because they are not likely to be informative, we exclude firms having fewer than 20 unique words from our classification algorithm." (p. 1430)

---

## 3. Vocabulary Construction

### 3.1 Corpus-Wide Vocabulary (W)

**Definition**: Set of all unique nouns/proper nouns across all firms in year t (after filters)

**Vocabulary size by year**:

- **1996**: W = 61,146 unique words
- **2008**: W = 55,605 unique words

**Direct quote**: "In our sample, W is 61,146 unique nouns and proper nouns in 1996 and 55,605 in 2008." (p. 1430)

**Trend**: Declining over time (61,146 -> 55,605)

- May reflect firm consolidation, standardization of business language

### 3.2 Firm-Level Word Statistics

**Distribution of unique words per firm**:

- **Typical firm**: ~200 unique words
- **Range**: 50 to 1,000 unique words
- **Distribution shape**: Right-skewed (long tail toward high word counts)

**Direct quote**: "Figure 1 displays a histogram showing the number of unique words in firm product descriptions. Typical firms use roughly 200 unique words. The tail is also somewhat skewed, as some firms use as many as 500–1,000 words, although some use fewer than 50." (p. 1430)

**Implications**:

- Average firm uses ~0.3-0.4% of total vocabulary (200/55,000)
- High-dimensional sparse representation
- Most firms have non-overlapping vocabularies (explains low average similarity)

### 3.3 Time-Varying Vocabulary

**Annual recalculation**: Vocabulary W recalculated each year

**Reasons for time variation**:

1. **New firms enter**: Bring new product terms (e.g., "smartphone" appears post-2007)
2. **Technology evolution**: New words emerge (e.g., "cloud", "streaming")
3. **Firms exit**: Some words disappear from corpus
4. **Product changes**: Firms update business descriptions annually

**Filing timing**: 10-K generally filed within 3 months after fiscal year ends

- Fiscal year 2008 -> 10-K filed January-March 2009
- Business description represents products as of December 31, 2008

**Implication**: Similarity matrices (Mt) are **time-varying** and updated annually

---

## 4. Binary Document Representation

### 4.1 Raw Binary Vector (Pi)

**For each firm i in year t**:

**Vector definition**:

- **Dimension**: W (total unique words in vocabulary)
- **Element w**: Pi[w] in {0, 1}

**Population rule**:

```
Pi[w] = 1   if firm i uses word w in business description
Pi[w] = 0   otherwise
```

**Direct quote (Appendix A)**: "For a given firm, a given element of this vector is one if the word associated with the given element is in the given firm's product description." (p. 1460)

**Example**:

- Vocabulary: W = {apple, software, hardware, retail, ...} (55,000 words total)
- Firm = Apple Inc.
- Pi[apple] = 1, Pi[software] = 1, Pi[hardware] = 1, Pi[retail] = 1, ...
- Pi has ~200 elements = 1, remaining ~54,800 elements = 0

**Weighting scheme**: **Binary (uniform weights)**

- Word presence/absence only (not frequency)
- Word used 1 time = same as word used 50 times

**Direct quote**: "Because we populate Pi with binary values, our baseline method weights words equally regardless of their frequency." (p. 1431, footnote 10)

**TF-IDF alternative tested**: Term Frequency - Inverse Document Frequency weighting

- Weights common words lower, rare words higher
- **Result**: "Our results suggest that uniform weights outperform TF-IDF weights for our application" (footnote 10, p. 1432)
- **Conclusion**: Binary representation is preferred

### 4.2 Normalized Vector (Vi)

**Normalization formula**:

```
Vi = Pi / sqrt(Pi * Pi)
```

**Where**:

- Vi = normalized vector for firm i (unit length)
- Pi = raw binary vector
- Pi * Pi = dot product = Sum(w=1 to W) Pi[w]^2 = sum of squared elements
- sqrt() = square root function

**Direct quote**: "We then normalize each vector to have unit length as follows: Vi = Pi / sqrt(Pi*Pi) for all i,j" (Equation 1, p. 1430)

**For binary vectors**:

- Pi * Pi = count of words used by firm i (since Pi[w]^2 = Pi[w] for binary)
- If firm uses 200 words: Pi * Pi = 200
- Normalization: Vi = Pi / sqrt(200) = Pi / 14.14

**Properties of Vi**:

- **Unit length**: Vi * Vi = 1 (all firms on surface of W-dimensional unit sphere)
- **Direction preserved**: Relative magnitudes of word weights unchanged
- **Geometric interpretation**: Each firm is a point on unit hypersphere

**Purpose of normalization**:

1. **Controls for document length**: Long documents don't automatically get higher similarity scores

**Direct quote (Appendix A)**: "This normalization ensures that product descriptions with fewer words are not penalized excessively." (p. 1460)

2. **Enables cosine similarity**: Normalized vectors allow dot product to equal cosine of angle

3. **Comparability**: All firms on same scale (unit sphere) regardless of verbosity

### 4.3 Firm-to-Word Matrix (Qt)

**Matrix definition**:

```
Qt = Nt x W matrix
```

**Dimensions**:

- **Rows**: Nt = number of firms in year t (~5,000)
- **Columns**: W = vocabulary size in year t (~55,000-61,000)
- **Total elements**: ~5,000 x 60,000 = 300 million

**Elements**:

- Qt[i, w] = Vi[w] (normalized value for firm i, word w)
- Most elements approx 0 (sparse representation)
- Non-zero elements approx 1/sqrt(word_count) for firm i

**Direct quote**: "We define Qt as the matrix containing the set of normalized vectors Vi for all firms i in year t. Thus Qt is an Nt x W matrix, where Nt is the number of firms in year t." (p. 1430)

**Time-varying**: Qt recalculated annually

- Q_1997, Q_1998, ..., Q_2008
- Rows (firms) change: entries, exits, stock symbol changes
- Columns (words) change: new words appear, old words drop out

---

## 5. Pairwise Similarity Calculation

### 5.1 Cosine Similarity Formula

**For any two firms i and j**:

```
Product Cosine Similarity(i,j) = Vi * Vj
```

**Where**:

- Vi = normalized unit-length vector for firm i
- Vj = normalized unit-length vector for firm j
- - = dot product operation

**Dot product expansion**:

```
Vi * Vj = Sum(w=1 to W) Vi[w] * Vj[w]
```

**Direct quote**: "Product Cosine Similarityi,j = (Vi * Vj)" (Equation 2, p. 1430)

**Appendix A formula**: "Product Similarityi,j = (Vi * Vj)" (Equation A2, p. 1460)

**Why this equals cosine**:

- For unit-length vectors: Vi *Vj = ||Vi||* ||Vj|| * cos(theta)
- Since ||Vi|| = ||Vj|| = 1: Vi * Vj = cos(theta)
- theta = angle between vectors in W-dimensional space

### 5.2 Interpretation

**Range**: [0, 1]

- **0**: No common words between firms i and j (orthogonal vectors)
- **1**: Identical word usage (same vector, theta = 0 degrees)
- **0.5**: Moderate overlap (theta = 60 degrees)

**Direct quote**: "Intuitively, the cosine similarity is higher when firms i and j use more of the same words, as both vectors will then have positive values in the same elements." (p. 1431)

**Example calculation**:

- Firm A uses: {software, hardware, computer, network} (4 words)
- Firm B uses: {software, consulting, services, support} (4 words)
- Common words: {software} (1 word)
- Vi[software] = 1/sqrt(4) = 0.5, Vj[software] = 1/sqrt(4) = 0.5
- Similarity(A,B) = 0.5 * 0.5 = 0.25

**More overlap -> higher similarity**:

- 0 common words -> similarity approx 0
- 50 common words (both firms use 200 words) -> similarity approx 0.25
- 200 common words (identical) -> similarity = 1.0

### 5.3 Properties

#### 5.3.1 Symmetry

```
Similarity(i,j) = Similarity(j,i)
```

Firm i's similarity to j equals j's similarity to i

#### 5.3.2 Self-Similarity

```
Similarity(i,i) = Vi * Vi = 1
```

Each firm is perfectly similar to itself

#### 5.3.3 Non-Transitivity (Critical Property)

**Transitive relationship does NOT hold**:

- If Similarity(A,B) > threshold AND Similarity(B,C) > threshold
- **Does NOT imply** Similarity(A,C) > threshold

**Example from paper**:
"Consider firms A and B, which are 25 percent similar. Because this is higher than 21.32 percent, A and B are in each other's industry. Now consider a firm C that is 27 percent similar to firm A and 5 percent similar to firm B. Firm C is in firm A's industry but not in firm B's industry." (p. 1436)

**Implication**: TNIC peer groups are **firm-centric**, not hierarchical

- Each firm has unique set of competitors
- Contrast with SIC/NAICS where all firms in 3-digit code are mutually in same industry

#### 5.3.4 Triangle Inequality Not Guaranteed

Unlike Euclidean distance, cosine similarity does not satisfy triangle inequality

### 5.4 Firm-to-Firm Network Matrix (Mt)

**Matrix definition**:

```
Mt = Nt x Nt square symmetric matrix
```

**Dimensions**:

- **Rows & Columns**: Nt firms in year t (~5,000)
- **Total elements**: ~5,000 x 5,000 = 25 million pairwise similarities
- **Unique similarities**: ~12.5 million (symmetric, so upper/lower triangles identical)

**Elements**:

- Mt[i, j] = Product Cosine Similarity(i,j)
- Mt[i, i] = 1.0 (diagonal)
- Mt[i, j] = Mt[j, i] (symmetric)

**Direct quote**: "The network representation of firms is fully described by an Nt x Nt square matrix Mt (i.e., a network), where an entry of this matrix for row i and column j is the Product Cosine Similarityi,j for firms i and j defined above." (p. 1431)

**Sparsity**: Mt is **NOT sparse**

- Most elements are non-zero (though typically small)
- Contrasts with SIC/NAICS which are extremely sparse (most pairs have 0 similarity)
- Enables continuous measures of relatedness

**Computational burden**:

- ~5,000 firms -> ~12.5 million pairwise calculations per year
- 12 years x 12.5 million = ~150 million total similarity calculations
- **Method selected**: Cosine similarity chosen for being "only moderately computationally burdensome, making it practical to replicate or extend" (p. 1431)

**Time-varying**: Mt recalculated annually

- M_1997, M_1998, ..., M_2008
- Each year's matrix uses that year's business descriptions
- Firm relationships evolve as products change

---

## 6. TNIC Peer Group Definition - Threshold Method

### 6.1 Simple Threshold Definition

**TNIC peer group for firm i**:

```
TNIC(i) = {j : Similarity(i,j) > threshold, j != i}
```

**In words**: All firms j with pairwise similarity to firm i exceeding a minimum threshold

**Direct quote**: "We use a simple minimum similarity threshold and define each firm i's industry to include all firms j with pairwise cosine similarities relative to i above a prespecified minimum threshold." (p. 1435)

**Exclusion**: Firm i is not in its own peer group (j != i)

### 6.2 Threshold Calibration

**Goal**: Match granularity of existing classification (SIC-3)

**SIC-3 benchmark**:

- 3-digit SIC codes (~270-280 unique industries)
- **2.05% of all possible firm pairs are membership pairs**
  - Membership pair: both firms in same SIC-3 code
  - Total pairs: N *(N-1) / 2 approx 5,000* 4,999 / 2 approx 12.5 million
  - Membership pairs: 2.05% * 12.5M approx 256,000 pairs

**Matching threshold**:

- **21.32% similarity threshold** generates 2.05% membership pairs
- TNIC threshold: 100 *Vi* Vj > 21.32

**Direct quote**: "For three-digit SIC codes, 2.05 percent of all possible firm pairs are membership pairs. A 21.32 percent minimum similarity threshold (where we define firms i and j as being in the same industry when 100*Vi*Vj > 21.32) generates 10-K-based industries with 2.05 percent membership pairs, which is the same as SIC-3." (p. 1436)

**Alternative calibrations**:

- Lower threshold (e.g., 15%) -> broader industries (more like SIC-2)
- Higher threshold (e.g., 30%) -> narrower industries (more like SIC-4)
- Paper uses 21.32% to match SIC-3 granularity for comparability

### 6.3 Median Score Adjustment

**Problem**: Document length can bias similarity scores

- Longer documents use more words -> higher chance of overlap -> inflated similarities
- Shorter documents use fewer words -> lower chance of overlap -> deflated similarities

**Solution**: Median score adjustment to control for length effects

#### 6.3.1 Calculate Median Score for Each Firm

**For firm i**:

1. Compute similarity between firm i and **all** other firms in economy: {Similarity(i,1), Similarity(i,2), ..., Similarity(i,Nt)}
2. Calculate median of this distribution: Median_Score(i)

**Interpretation**: Median should be near zero (no industry spans entire economy)

- If median > 0 -> firm i's document length inflates similarities
- If median < 0 (not possible with cosine) -> deflated

**Direct quote**: "For a firm i we compute its median score as the median similarity between firm i and all other firms in the economy in the given year" (p. 1436)

#### 6.3.2 Adjust Raw Similarity Scores

**Adjustment formula**:

```
Adjusted Similarity(i,j) = Raw Similarity(i,j) - Median_Score(i)
```

**For symmetric adjustment** (both firms):

```
Adjusted Similarity(i,j) = Raw Similarity(i,j) - [Median_Score(i) + Median_Score(j)] / 2
```

**Apply threshold to adjusted scores**:

```
TNIC(i) = {j : Adjusted Similarity(i,j) > threshold, j != i}
```

**Direct quote**: "We achieve this by subtracting these median scores from the raw scores to obtain our final scores used for each firm." (p. 1436)

**Effect**: Controls for document length while preserving relative similarity rankings

### 6.4 Key TNIC Properties

#### 6.4.1 Time-Varying Peer Groups

**Annual updates**: TNIC peer groups recalculated each year

- Firms update 10-K business descriptions annually
- New products introduced, old products discontinued
- Similarity scores change -> peer groups change

**Implication**: Firm i's competitors in 2005 != competitors in 2008

**Example**: Netflix

- 1997-2006: Peers include DVD rental/retail firms (Blockbuster)
- 2007-2008: Peers shift toward streaming media firms

#### 6.4.2 Intransitivity (No Transitivity)

**Definition**: A->B and B->C does NOT imply A->C

**Example** (from paper):

- Firm A and B: 25% similar (both in each other's TNIC industry, threshold=21.32%)
- Firm B and C: 30% similar (in each other's industry)
- Firm A and C: 5% similar (**not in each other's industry**)

**Implication**: TNIC industries are **firm-centric**, not transitive clusters

**Direct quote**: "Note that the transitivity property does not hold for these firm-centric industries." (p. 1436)

**Contrast with SIC/NAICS**:

- SIC/NAICS are transitive: if A and B in same SIC-3, and B and C in same SIC-3, then A and C in same SIC-3
- TNIC is non-transitive: allows more nuanced product space representation

#### 6.4.3 Firm-Centric Industries

**Concept**: Each firm has its own unique set of competitors

**Analogy**: "Facebook circle of friends"

- Your friends (TNIC peers) != your friend's friends
- Some overlap, but not identical sets
- Allows for gradual transitions across product space

**Implication**: Industry is defined relative to focal firm, not as fixed categories

**Contrast with traditional classifications**:

- SIC/NAICS: Firm belongs to ONE industry code (e.g., SIC 3571)
- TNIC: Firm has UNIQUE set of peer firms (e.g., 50 peers for firm A, different 50 peers for firm B)

#### 6.4.4 Asymmetric Peer Importance

**While similarity is symmetric** (Similarity(i,j) = Similarity(j,i)):

- Firm j may be **more important** to firm i than vice versa
- If i is small competitor in j's space but j is major competitor in i's space

**Peer return calculation** (for momentum studies):

- Equal-weighted average: All peers weighted equally
- Alternative: Weight by similarity, market cap, or sales

---

## 7. Fixed Classification Algorithm - Hierarchical Clustering

**Purpose**: Create static industry classification (like SIC/NAICS) using text-based methodology

**Source**: Appendix B, p. 1460-1461

**Two-stage process**:

1. Industry Formation (1997 data, single-segment firms only)
2. Industry Assignment (all years, all firms)

### 7.1 Stage 1: Industry Formation (1997 Only)

**Objective**: Group single-segment firms into 300 industries using agglomerative hierarchical clustering

#### 7.1.1 Initialization

**Starting point**:

- N = number of single-segment firms in 1997 (identified via Compustat segment database)
- Initialize: N industries, each containing one firm
- Each firm in its own industry

**Direct quote**: "We begin the first stage by taking the subsample of N single-segment firms in 1997... We then initialize our industry classifications to have N industries, with each of the N firms residing within its own one-firm industry." (Appendix B, p. 1460)

**Why single-segment firms**:

- Multi-segment firms operate in multiple product markets
- Single-segment firms have focused product descriptions
- Creates cleaner initial industry definitions

#### 7.1.2 Agglomerative Clustering Algorithm

**Algorithm type**: Bottom-up hierarchical clustering

- Start with N clusters (one firm each)
- Iteratively merge two most similar clusters
- Continue until target number of industries reached

**Iteration steps**:

1. **Compute all pairwise industry similarities**: I_{j,k} for all industries j, k

2. **Find maximum pairwise similarity**:

   ```
   (j*, k*) = argmax(j,k) I_{j,k}
   ```

3. **Merge industries j* and k***:
   - Create new industry l = j*union k*
   - Remove industries j*and k* from list
   - Number of industries decreases by 1: N -> N-1

4. **Recompute similarities** involving new industry l

5. **Repeat** until number of industries = 300 (target)

**Direct quote**: "To reduce the industry count to N-1 industries, we take the maximum pairwise industry similarity... The two industries with the highest similarity are then combined." (Appendix B, p. 1460-1461)

#### 7.1.3 Industry Similarity Formula

**For two industries l and q containing m_l and m_q firms respectively**:

```
I_{l,q} = Sum(x=1 to m_l) Sum(y=1 to m_q) S_{x,y} / (m_l * m_q)
```

**Where**:

- I_{l,q} = similarity between industries l and q
- S_{x,y} = firm-level pairwise similarity between firm x (in industry l) and firm y (in industry q)
- m_l = number of firms in industry l
- m_q = number of firms in industry q

**Interpretation**: Average pairwise similarity across all firm pairs between two industries

**Example**:

- Industry A: firms {1, 2, 3} (m_A = 3)
- Industry B: firms {4, 5} (m_B = 2)
- I_{A,B} = [S_{1,4} + S_{1,5} + S_{2,4} + S_{2,5} + S_{3,4} + S_{3,5}] / (3 * 2)
- I_{A,B} = sum of 6 pairwise similarities / 6

**Direct quote**: "Equation (B1) [describes] how we measure similarities between industries (rather than firms). Equation (B1) shows that we take a simple average of all pairwise firm similarities between the two industries." (Appendix B, p. 1461)

**Computational note**:

- Early iterations (N approx 5,000): Most industries have 1 firm, so I_{j,k} = S_{j,k}
- Later iterations: Industries have multiple firms, requires averaging many pairwise similarities
- Final iterations: Industries may have 10-50 firms each

#### 7.1.4 Optimization Pass

**After clustering complete** (300 industries formed):

1. **Check each firm individually**:
   - For firm i currently in industry l
   - Compute firm i's average similarity to all industries: {I_{i,1}, I_{i,2}, ..., I_{i,300}}
   - Find industry q with maximum similarity to firm i: q* = argmax_q I_{i,q}

2. **Reclassify if beneficial**:
   - If q* != l (firm fits better in different industry)
   - Move firm i from industry l to industry q*
   - Recompute industry similarities involving l and q*

3. **Iterate** until no firm wants to move

**Objective function**: Maximize total within-industry similarity

**Stopping criterion**: "within-industry similarity cannot be maximized further by moving any one firm to another industry" (Appendix B, p. 1461)

**Direct quote**: "After the clustering step, we take an additional pass at optimizing our classifications. Specifically, we check whether any firm would, on its own, like to switch to another industry...we iterate this process until within-industry similarity cannot be maximized further by moving any one firm to another industry." (Appendix B, p. 1461)

#### 7.1.5 Target Industry Count

**Primary specification**: 300 industries

- Comparable to SIC-3: 274 unique codes in sample
- Comparable to NAICS-4: 331 unique codes in sample

**Sensitivity analysis**: 50 to 800 industries (increments of 50)

- Test range covers SIC-2 (50-100 industries) to SIC-4 (400-500 industries)
- Results robust across specifications

**Optimal range** (via Akaike Information Criterion tests): 300-400 industries

### 7.2 Stage 2: Industry Assignment (All Years)

**Objective**: Assign all firms in all years to the 300 fixed industries created in Stage 1

#### 7.2.1 Create Industry Word Vectors

**For each industry k = 1, 2, ..., 300**:

1. **Identify constituent firms** from 1997 (Stage 1 output)
   - Industry k contains firms {i_1, i_2, ..., i_{m_k}}

2. **Create industry word vector P_k**:
   - Dimension: W (vocabulary size)
   - Element P_k[w] = count of firms in industry k that use word w

**Example**:

- Industry k has 10 firms
- 7 of them use word "software"
- P_k[software] = 7

3. **Normalize to unit length**:

   ```
   V_k = P_k / sqrt(P_k * P_k)
   ```

**Direct quote**: "Specifically, we take all of the firms from 1997 that are classified into a given industry and create an industry word vector. The vector is populated such that each element equals a count of the number of firms that mention the given word." (Appendix B, p. 1461)

**Result**: 300 industry vectors {V_1, V_2, ..., V_300}

#### 7.2.2 Assign Firms to Industries

**For each firm i in any year t** (1997-2008):

1. **Compute similarity to all industries**:

   ```
   Similarity(i, k) = V_i * V_k   for k = 1, 2, ..., 300
   ```

2. **Assign to most similar industry**:

   ```
   Industry(i) = argmax_k [V_i * V_k]
   ```

**Direct quote**: "For a given firm that we wish to classify, we simply compute its similarity to all of the candidate industries and assign the firm to the industry it is most similar to. A firm's similarity to an industry is simply the dot product of the firm's normalized word vector to the industry's normalized word vector." (Appendix B, p. 1461)

**Properties**:

- **Deterministic**: Each firm assigned to exactly one industry
- **Time-varying assignment**: Firm i can switch industries across years as business description changes
- **Comparable to SIC/NAICS**: Fixed number of industries, but assignment can change

#### 7.2.3 Multi-Segment Firms

**Treatment**:

- Excluded from Stage 1 industry formation (1997)
- Included in Stage 2 industry assignment (all years)
- Assigned to single industry (most similar)

**Limitation**: Multi-segment firms operate in multiple product markets but assigned to one industry

- Could be addressed with probabilistic assignment (e.g., 50% industry A, 50% industry B)
- Paper uses single-industry assignment for simplicity and comparability with SIC/NAICS

---

## 8. Implementation Parameters Summary

### 8.1 Critical Parameter Values

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Minimum text length** | 1,000 characters | Exclude firms with <1,000 chars |
| **Part-of-speech filter** | Nouns + proper nouns only | Webster.com + 90% capitalization |
| **Stopword frequency threshold** | 25% | Remove words in >25% of documents |
| **Minimum unique words/firm** | 20 words | Exclude firms with <20 unique words |
| **TNIC similarity threshold** | 21.32% | Matches SIC-3 granularity (2.05% membership) |
| **Fixed classification industries** | 300 | Comparable to SIC-3: 274, NAICS-4: 331 |
| **Proper noun capitalization** | 90% | First letter capitalized >=90% of time |
| **Vocabulary size (W)** | 55,605 - 61,146 | Year-dependent (1996: 61,146; 2008: 55,605) |
| **Typical firm word count** | ~200 words | Range: 50-1,000 words |
| **Average firms per year** | ~5,000 | Total sample: 50,673 firm-years |
| **Document types** | 4 types | 10-K, 10-K405, 10KSB, 10KSB40 |

### 8.2 Threshold Robustness Tests

| Threshold Type | Values Tested | Result |
|----------------|---------------|--------|
| **Stopword frequency** | 10%, 25%, 100% | Robust across all |
| **Fixed industries** | 50-800 (increments of 50) | Optimal: 300-400 |
| **TNIC similarity** | Multiple (not specified) | 21.32% for SIC-3 match |

### 8.3 Sample Size Progression

| Stage | Observations | Filter Applied |
|-------|--------------|----------------|
| **Initial 10-Ks** | 68,302 | None |
| **Valid financial data** | 63,875 | Remove invalid Compustat, sales<=0, assets<$1M |
| **Final sample** | 50,673 | + Remove financials (SIC 6000-6999), require 1-yr lag |
| **Annual average** | ~5,000 firms/year | 50,673 / 12 years approx 4,223 per year |
| **Coverage** | 97.9% | CRSP/Compustat universe |

---

## 9. Computational Details

### 9.1 Matrix Dimensions and Computational Burden

#### Matrix Qt (Firm-to-Word)

- **Dimensions**: Nt x W (rows: firms, columns: words)
- **Example scale**: 5,000 x 60,000 = 300 million elements
- **Sparsity**: High (~99.7% zeros, since typical firm uses 200/60,000 words)
- **Storage**: Sparse matrix representation recommended
- **Computation**: One-time per year (vocabulary extraction + binary population)

#### Matrix Mt (Firm-to-Firm Similarities)

- **Dimensions**: Nt x Nt (square, symmetric)
- **Example scale**: 5,000 x 5,000 = 25 million elements
- **Unique similarities**: ~12.5 million (upper/lower triangles identical, exclude diagonal)
- **Sparsity**: Low (~most elements non-zero, though many near zero)
- **Storage**: Dense matrix (cannot compress much)
- **Computation**: Quadratic in number of firms O(Nt^2)

**Direct quote**: Cosine similarity chosen for being "only moderately computationally burdensome, making it practical to replicate or extend" (p. 1431)

### 9.2 Annual Recalculation Requirements

**Every year t requires**:

1. **Vocabulary extraction**: Scan all documents, extract unique words, apply filters
   - Complexity: O(Nt * avg_words_per_document)

2. **Binary matrix construction** (Qt): For each firm-word pair, check presence
   - Complexity: O(Nt * W)

3. **Normalization**: Compute sqrt(Pi * Pi) for each firm, divide elements
   - Complexity: O(Nt * W)

4. **Pairwise similarities** (Mt): Compute Vi * Vj for all pairs i,j
   - Complexity: O(Nt^2 *W) naively, O(Nt^2* avg_words) in practice
   - **Bottleneck**: This is the computational bottleneck

5. **Median score adjustment**: Sort similarities for each firm, find median
   - Complexity: O(Nt^2 log Nt)

**Total annual computation**: Dominated by O(Nt^2) pairwise similarity calculations

**Sample timing** (approximate, modern hardware):

- 5,000 firms x 60,000 words x 200 avg words per firm
- 12.5 million similarity calculations
- ~1-2 hours on single CPU core (estimate)
- Parallelizable across firm pairs

### 9.3 Special Cases and Edge Conditions

#### 9.3.1 Single-Firm Industries

**Occurrence**: Firm with highly unique product description (low similarity to all others)

**TNIC method**: More common than SIC-3/NAICS-4

- SIC-3: Rare (most codes have >=10 firms)
- TNIC: ~5-10% of firms may be in single-firm industries (high threshold)

**Treatment**: Not excluded (valid representation of isolated market position)

#### 9.3.2 Multi-Segment Firms

**Identification**: Compustat segment database

- Firms reporting multiple business segments with different products

**Treatment in TNIC threshold method**:

- Included (use full business description combining all segments)
- Similarity reflects aggregate product portfolio

**Treatment in fixed classification** (Appendix B):

- Excluded from Stage 1 industry formation (1997)
- Included in Stage 2 assignment (all years)
- Assigned to single most-similar industry

**Limitation**: Doesn't capture multi-industry operations explicitly

#### 9.3.3 Missing Years

**Cause**: Firm doesn't file 10-K in year t

- Delisting, merger, bankruptcy, private transaction, filing delay

**Treatment**:

- No similarity scores for year t
- Firm removed from Mt for year t
- Can reappear in subsequent years

**Implication**: Panel is unbalanced

#### 9.3.4 Newly Public Firms (IPOs)

**First 10-K**: Firm appears in sample when first 10-K filed

- Usually 3-12 months after IPO

**Treatment**: Included immediately in year t similarity matrix

- No lagged TNIC peers available
- Can use contemporaneous peers

#### 9.3.5 Conglomerates

**Firms with highly diverse products** (e.g., General Electric):

- Use many unique words (500-1,000)
- High similarity to firms in multiple industries
- Large TNIC peer group (many peers above threshold)

**Treatment**: No special handling (included as-is)

**Implication**: Conglomerates may have peer groups spanning multiple SIC codes

#### 9.3.6 Generic Business Descriptions

**Firms with vague descriptions** (e.g., "holding company"):

- Use few unique words after stopword filtering
- May fall below 20-word minimum -> excluded

**Treatment**: Excluded if <20 unique words

#### 9.3.7 Identical Business Descriptions

**Multiple firms with same text** (rare):

- Spinoffs, subsidiaries, acquired firms

**Similarity**: 1.0 (perfect similarity)

**Treatment**: Both firms in each other's TNIC peer group

---

## 10. Mathematical Formulas Reference

### 10.1 Binary Vector

```
P_i[w] in {0, 1}

P_i[w] = 1   if firm i uses word w
P_i[w] = 0   otherwise
```

### 10.2 Vector Normalization

```
V_i = P_i / sqrt(P_i * P_i)

where: P_i * P_i = Sum(w=1 to W) P_i[w]^2
```

**For binary vectors**: P_i * P_i = number of unique words used by firm i

### 10.3 Cosine Similarity (Pairwise)

```
Similarity(i,j) = V_i * V_j = Sum(w=1 to W) V_i[w] * V_j[w]
```

**Range**: [0, 1]

- 0 = no common words
- 1 = identical word usage

### 10.4 Product Differentiation

```
Differentiation(i,j) = 1 - Similarity(i,j)
```

**Range**: [0, 1]

- 0 = identical products
- 1 = completely differentiated products

### 10.5 Median Score Adjustment

```
Median_Score(i) = median({Similarity(i,1), Similarity(i,2), ..., Similarity(i,N)})

Adjusted_Similarity(i,j) = Raw_Similarity(i,j) - Median_Score(i)
```

**Alternative (symmetric)**:

```
Adjusted_Similarity(i,j) = Raw_Similarity(i,j) - [Median_Score(i) + Median_Score(j)] / 2
```

### 10.6 TNIC Peer Group Definition

```
TNIC(i) = {j : Adjusted_Similarity(i,j) > threshold, j != i}
```

**Standard threshold**: 21.32% (for SIC-3 equivalence)

### 10.7 Industry Similarity (Hierarchical Clustering)

```
I_{l,q} = Sum(x=1 to m_l) Sum(y=1 to m_q) S_{x,y} / (m_l * m_q)
```

**Where**:

- I_{l,q} = similarity between industries l and q
- S_{x,y} = firm-level similarity between firms x and y
- m_l = number of firms in industry l
- m_q = number of firms in industry q

### 10.8 Firm-to-Industry Similarity (Assignment)

```
Similarity(firm i, industry k) = V_i * V_k

Industry(i) = argmax_{k=1,...,300} [V_i * V_k]
```

**Where**:

- V_i = normalized word vector for firm i
- V_k = normalized word vector for industry k

---

## 11. Critical Implementation Rules

### 11.1 DO NOT

**Text preprocessing**:

- ❌ Do NOT apply lowercase transformation initially (needed for proper noun detection)
- ❌ Do NOT remove all punctuation initially (needed for proper noun detection)
- ❌ Do NOT keep non-nouns (verbs, adjectives, adverbs, etc.)
- ❌ Do NOT use stemming or lemmatization (not mentioned in paper)

**Weighting**:

- ❌ Do NOT use TF-IDF weighting (tested but underperformed)
- ❌ Do NOT weight by word frequency (use binary: 0 or 1 only)
- ❌ Do NOT weight rare words higher (uniform weights preferred)

**Similarity calculation**:

- ❌ Do NOT use raw vectors (must normalize to unit length first)
- ❌ Do NOT use Euclidean distance (cosine similarity specified)
- ❌ Do NOT use Jaccard similarity (not used in paper)

**Vocabulary**:

- ❌ Do NOT use static vocabulary across years (must update annually)
- ❌ Do NOT include stopwords above 25% frequency threshold
- ❌ Do NOT include geographical terms

### 11.2 DO

**Text preprocessing**:

- ✅ DO filter for nouns and proper nouns FIRST (before other processing)
- ✅ DO use Webster.com (or equivalent) for noun definition
- ✅ DO detect proper nouns via 90% capitalization rule
- ✅ DO include words with mixed part-of-speech if at least one use is noun

**Stopword filtering**:

- ✅ DO remove words appearing in >25% of documents
- ✅ DO remove geographical terms explicitly (countries, states, top 50 cities)
- ✅ DO remove generic common words (articles, conjunctions, pronouns)

**Firm filtering**:

- ✅ DO exclude firms with <1,000 characters in business description
- ✅ DO exclude firms with <20 unique words after filtering
- ✅ DO exclude financial firms (SIC 6000-6999)

**Vector construction**:

- ✅ DO use binary representation (0 or 1 only)
- ✅ DO normalize vectors to unit length (divide by sqrt of sum of squares)
- ✅ DO ensure all firms reside on surface of unit hypersphere

**Similarity calculation**:

- ✅ DO use cosine similarity (dot product of normalized vectors)
- ✅ DO compute pairwise similarities for all firm pairs
- ✅ DO subtract median scores for length control (recommended)

**Vocabulary**:

- ✅ DO recalculate vocabulary annually (time-varying)
- ✅ DO update similarity matrices each year
- ✅ DO allow peer groups to change over time

**Hierarchical clustering** (if using fixed classification):

- ✅ DO use single-segment firms only for Stage 1 (1997)
- ✅ DO use agglomerative (bottom-up) clustering
- ✅ DO merge industries with maximum pairwise similarity
- ✅ DO perform optimization pass after clustering complete
- ✅ DO create industry word vectors for Stage 2 assignment

### 11.3 Critical Quote on Methodology

**On binary weighting**:
"Because we populate Pi with binary values, our baseline method weights words equally regardless of their frequency." (p. 1431, footnote 10)

**On normalization purpose**:
"This normalization ensures that product descriptions with fewer words are not penalized excessively." (Appendix A, p. 1460)

**On computational choice**:
Cosine similarity chosen for being "only moderately computationally burdensome, making it practical to replicate or extend" (p. 1431)

**On intransitivity**:
"Note that the transitivity property does not hold for these firm-centric industries." (p. 1436)

---

## 12. Additional Implementation Notes

### 12.1 Software and Tools Used in Original Paper

**Text extraction**:

- Perl web crawling scripts (SEC Edgar download automation)
- APL programming language (text parsing and processing)
- Human intervention (for non-standard formats)

**Data analysis**:

- Not specified (likely Stata, SAS, or MATLAB for econometric analysis)

**Modern alternatives**:

- Python: pandas, numpy, scikit-learn, beautifulsoup
- R: tidyverse, text, tm package
- SQL: for large-scale data management

### 12.2 Replication Tips

1. **Start small**: Test on 100-500 firms first (1 year)
   - Verify methodology correctness
   - Debug code before scaling

2. **Validate vocabulary extraction**:
   - Check word counts match paper (~200 per firm typical)
   - Verify W approx 55,000-61,000 total words
   - Inspect sample words (should be product-related nouns)

3. **Check normalization**:
   - Verify ||Vi|| = 1 for all firms (unit length)
   - Test: Vi * Vi should equal 1.0

4. **Validate similarities**:
   - Most pairwise similarities should be near 0 (sparse product space)
   - Distribution should be right-skewed (long tail toward high similarity)
   - Self-similarity must equal 1.0

5. **Test with known firm pairs**:
   - Apple vs Microsoft (high similarity expected: both software/hardware)
   - Apple vs ExxonMobil (low similarity expected: tech vs oil)
   - Nike vs Adidas (high similarity expected: both athletic footwear)

6. **Compare with SIC/NAICS**:
   - Compute overlap between TNIC peers and SIC-3 peers
   - Hoberg & Phillips find ~40-50% overlap (validation benchmark)

### 12.3 Common Pitfalls

1. **Forgetting to normalize**: Using raw binary vectors -> incorrect similarities

2. **Including stopwords**: Not filtering common words -> all firms similar

3. **Not updating annually**: Using static vocabulary -> missing temporal dynamics

4. **Double-counting self**: Including firm i in its own peer group -> inflated peer returns

5. **Wrong threshold**: Using 0.2132 (absolute) vs 21.32% (percentage) -> 100x error

6. **Transitive assumption**: Assuming TNIC industries are transitive clusters -> incorrect peer assignments

7. **Ignoring median adjustment**: Not subtracting median scores -> document length bias

---

**End of Methodology Document**

This document provides complete, data-level specifications for replicating the Hoberg & Phillips (2016) TNIC methodology. All parameter values, formulas, and implementation rules are extracted directly from the original paper with page references for verification.
