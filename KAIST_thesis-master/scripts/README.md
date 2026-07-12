# Scripts Directory - TNIC Pipeline for Korean Market

This directory contains all scripts for implementing the Hoberg & Phillips (2016) Text-Based Network Industries and Endogenous Product Differentiation (TNIC) methodology using Korean DART business descriptions.

**Methodology Citation**:
> Hoberg, G., & Phillips, G. M. (2016). Text-based network industries and endogenous product differentiation. *Journal of Political Economy*, 124(5), 1423-1465.

**Application Paper**:
> Hoberg, G., & Phillips, G. M. (2018). Text-based industry momentum. *Journal of Financial and Quantitative Analysis*, 53(6), 2355-2388.

---

## Quick Start - Full Pipeline Execution

### Prerequisites
```bash
# Ensure MongoDB is running and contains DART data
# Check connection first:
poetry run python scripts/check_mongodb.py
```

### Complete Pipeline (Phases 1-4)

```bash
# Phase 1: Extract and clean business descriptions from MongoDB
poetry run python scripts/extract_korean_texts.py

# Phase 2: Build year-by-year Korean corpora (H&P methodology)
poetry run python scripts/build_korean_corpus_by_year.py

# Phase 3.1: Build binary matrices Q_t for each year
poetry run python scripts/build_binary_matrices_by_year.py

# Phase 3.2: Compute similarity matrices M_t
poetry run python scripts/compute_similarity_matrices_by_year.py

# Phase 4: Build TNIC peer groups with median adjustment
poetry run python scripts/build_tnic_peer_groups.py
```

**Note**: Phases 3-4 currently process pilot years [2010, 2011]. To process all years, edit the scripts to change `TARGET_YEARS = [2010, 2011]` to `TARGET_YEARS = None`.

---

## Directory Structure

```
scripts/
├── README.md                                    # This file
│
├── [PHASE 0: SETUP & VALIDATION]
├── check_mongodb.py                             # MongoDB connection test
├── validate_mongodb_coverage.py                 # Data coverage analysis
├── test_config.py                               # Configuration validation
│
├── [PHASE 1: DATA EXTRACTION]
├── extract_korean_texts.py                      # ⭐ Extract & clean from MongoDB
│
├── [PHASE 2: CORPUS BUILDING]
├── build_korean_corpus_by_year.py               # ⭐ Build year-by-year corpora (H&P)
│
├── [PHASE 3: TNIC CONSTRUCTION]
├── build_binary_matrices_by_year.py             # ⭐ Build Q_t binary matrices
├── compute_similarity_matrices_by_year.py       # ⭐ Compute M_t similarity matrices
│
├── [PHASE 4: PEER GROUP DEFINITION]
├── build_tnic_peer_groups.py                    # ⭐ Define TNIC peers with median adjustment
│
├── [PHASE 5: FNGUIDE ANALYSIS]
├── analyze_fnguide_classification_levels.py     # Compare FnGuide classification levels
├── calculate_fnguide_membership_fraction.py     # Calculate membership pairs fraction
├── calculate_all_fnguide_membership_fractions.py # Membership fractions over time
│
└── [UTILITIES]
    ├── debug_stock_codes.py                     # Stock code matching diagnostics
    ├── plot_char_distribution.py                # Character count visualization
    ├── retrieve_mongodb_data.py                 # Generic MongoDB retrieval
    ├── show_sample_text.py                      # Display sample texts
    ├── show_korean_text.py                      # Korean encoding test
    └── test_korean_tokenization.py              # Test kiwipiepy tokenizer
```

**Legend**: ⭐ = Core pipeline script (required for TNIC construction)

---

## Phase-by-Phase Documentation

### **Phase 0: Setup & Validation**

#### `check_mongodb.py`
**Purpose**: Verify MongoDB connection and data availability

**What it checks**:
- MongoDB connection status
- Total documents in collection
- Section codes available
- Year distribution
- Unique firms count
- Sample document structure

**When to run**: Before starting the pipeline to ensure data access

**Example output**:
```
Total documents: 12,345
Section codes: ['020000', '020100']
Business overview documents (020100): 8,234
Unique firms: 1,823
```

---

#### `validate_mongodb_coverage.py`
**Purpose**: Analyze MongoDB data completeness across years

**What it checks**:
- Firm-year coverage
- Missing years per firm
- Year range completeness
- Stock code validity

---

#### `test_config.py`
**Purpose**: Test project configuration and imports

**What it checks**:
- Environment variables loaded correctly
- Required packages importable
- Directory structure accessible

---

### **Phase 1: Data Extraction**

#### `extract_korean_texts.py` ⭐
**Purpose**: Extract and clean business descriptions from MongoDB

**Methodology**:
- Extracts business descriptions from DART financial reports
- Section codes: 020000 (old format) OR 020100 (new format) - Business Overview
- Equivalent to SEC 10-K Item 1 (Business section)

**Processing Steps**:

1. **MongoDB Extraction**
   - Database: `FS`
   - Collection: `A001` (annual reports)
   - Query: All documents (collection pre-filtered for business sections)

2. **Character Count Distribution Analysis**
   - Calculate percentiles (50%, 75%, 90%, 95%, 99%)
   - Identify 95th percentile cutoff for outlier removal
   - Generate distribution plots

3. **Deduplication Pipeline**
   - **Step 1**: Remove zero-length documents
   - **Step 2**: Apply 95th percentile cutoff for character count
   - **Step 3**: Level-based deduplication (prefer level=2 over level=1)
     - level=2: Individual sections (more detailed)
     - level=1: Merged text (less detailed)
   - **Step 4**: Firm-year deduplication (keep latest `rcept_dt` per firm-year)

4. **Validation**
   - Compare extracted counts vs MongoDB
   - Calculate retention rate (should be 70-90%)
   - Year distribution checks

**Outputs**:
```
data/korean_texts/
├── business_descriptions_raw.parquet          # Raw MongoDB data
├── business_descriptions_clean.parquet        # ⭐ Clean firm-year panel (PRIMARY OUTPUT)
├── text_samples.csv                           # Random samples for inspection
└── char_count_distribution.png                # Distribution plot

reports/
└── 1.2_data_extraction.md                     # Extraction report
```

**Critical Output**: `business_descriptions_clean.parquet` is the foundational dataset for all subsequent phases.

**Expected Results**:
- Typical retention: 70-90% after deduplication
- ~1,500-2,000 firm-years per year
- Mean char count: 2,000-4,000 characters per description

---

### **Phase 2: Corpus Building**

#### `build_korean_corpus_by_year.py` ⭐
**Purpose**: Build separate Korean corpora for each year following H&P (2016) methodology

**Why Year-by-Year?**

H&P (2016) explicitly requires year-specific processing:

> "We define Q_t as the matrix containing the set of normalized vectors V_i for all firms i **in year t**. Thus Q_t is an N_t × W matrix, where **N_t is the number of firms in year t**." (p. 1430)

> "W is 61,146 unique nouns and proper nouns **in 1996** and 55,605 **in 2008**." (p. 1430)

**Key Insight**: Vocabulary W changes each year as product markets evolve.

**Processing Steps**:

1. **Load Clean Data**
   - Input: `business_descriptions_clean.parquet` from Phase 1
   - Group by year

2. **Korean Text Processing** (for each year separately)
   - Tokenizer: `kiwipiepy` (Korean morphological analyzer)
   - POS tags kept: NNG (common noun), NNP (proper noun), NNB (dependent noun)
   - Filters:
     - Length ≥ 2 characters
     - Remove numbers
     - Remove Korean stopwords

3. **H&P Filters** (applied within each year)

   **Filter 1: Minimum Words per Firm**
   - Threshold: 20 unique words
   - Citation: H&P (2016, p. 1430) - "exclude firms having fewer than 20 unique words"
   - Rationale: Firms with <20 words lack sufficient information to characterize product space

   **Filter 2: Frequency-Based Stopwords**
   - Threshold: Remove words appearing in >25% of documents in that year
   - Citation: H&P (2016, p. 1429) - "words that appear in no more than 25 percent of all product descriptions"
   - Rationale: Common words don't distinguish products

4. **Build Year-Specific Vocabulary W_t**
   - Collect all unique words after filters
   - Calculate word frequencies
   - Calculate document frequencies (how many firms use each word)

**Parameters** (from H&P 2016):
```python
MIN_WORDS_PER_FIRM = 20       # H&P standard
FREQUENCY_THRESHOLD = 0.25    # H&P standard (25%)
```

**Outputs** (for each year):
```
data/korean_texts/by_year/YYYY/
├── firm_word_sets_YYYY.parquet          # ⭐ Firm-level word sets
│   Columns: [firm_year, stock_code, year, unique_nouns, word_count]
│
├── corpus_vocabulary_YYYY.csv           # Complete vocabulary
│   Columns: [word, frequency, document_frequency, pct_documents]
│
└── corpus_statistics_YYYY.json          # Summary statistics

reports/
└── 2.3_corpus_building_by_year.md       # Corpus building report
```

**Expected Vocabulary Evolution**:
- H&P (2016): 61,146 words (1996) → 55,605 words (2008), -9.1% change
- Korean market: Will vary, expect 10,000-30,000 words per year

**Expected Firm Statistics**:
- Avg words per firm: 50-200 (after filters)
- Firms removed: 5-15% (below 20-word threshold)

---

### **Phase 3: TNIC Construction**

#### `build_binary_matrices_by_year.py` ⭐
**Purpose**: Build sparse binary matrices Q_t for each year

**Methodology** (H&P 2016, p. 1429-1430):

> "A given firm i's vocabulary can be represented by a W-vector P_i, with each element being populated by the number **1 if firm i uses the given word and 0 if it does not**."

**Key Property**: Binary values only (0 or 1), **NOT frequencies or TF-IDF weights**.

**Matrix Definition**:
- **Q_t**: N_t × W_t matrix for year t
- **N_t**: Number of firms in year t
- **W_t**: Vocabulary size in year t
- **Q_t[i,j]**: 1 if firm i uses word j, else 0

**Processing Steps**:

1. **Load Data for Year**
   - Input: `firm_word_sets_YYYY.parquet` and `corpus_vocabulary_YYYY.csv`
   - Build word → column index mapping

2. **Construct Sparse Binary Matrix**
   - Initialize: `lil_matrix((N_t, W_t), dtype=np.int8)` for efficient construction
   - For each firm i:
     - For each word j in firm's vocabulary:
       - Set Q_t[i, j] = 1
   - Convert to CSR format for efficient computation and storage

3. **Validation**
   - **Row sum check**: Sum(Q_t[i, :]) should equal firm i's word count
   - **Column sum check**: Sum(Q_t[:, j]) should equal word j's document frequency
   - **Binary check**: All values are 0 or 1

4. **Sparsity Analysis**
   - Sparsity = 1 - (nnz / total_elements)
   - Expected: ~99.3% sparse (firms use ~200 words out of ~20,000)

**Memory Efficiency**:
- Dense format: N_t × W_t × 1 byte = ~32 MB per year
- Sparse format: nnz × 9 bytes = ~2-3 MB per year (90% savings)

**Current Configuration**:
```python
TARGET_YEARS = [2010, 2011]  # Pilot years
# Change to None to process all years
```

**Outputs**:
```
data/korean_tnic/by_year/
├── binary_matrix_YYYY.npz               # ⭐ Sparse binary matrix (CSR format)

data/korean_tnic/
└── binary_matrices_metadata.json        # Metadata for all years

reports/
└── 3.1_binary_matrices_by_year.md       # Binary matrix report
```

**Expected Matrix Dimensions**:
- N_t: ~1,600 firms per year
- W_t: ~10,000-20,000 words per year
- Total cells: ~16-32 million per year
- Non-zeros: ~200,000-400,000 per year (99.3% sparse)

---

#### `compute_similarity_matrices_by_year.py` ⭐
**Purpose**: Compute pairwise cosine similarity matrices M_t from binary matrices Q_t

**Methodology** (H&P 2016, Section II.A):

> "Product Cosine Similarity_{i,j} = (V_i · V_j)"

Where V_i and V_j are normalized unit-length vectors.

**Formula**:
```
M_t = cosine_similarity(Q_t)
M_t[i,j] = Q_t[i,:] · Q_t[j,:] / (||Q_t[i,:]|| × ||Q_t[j,:]||)
```

**Matrix Properties**:
- **Symmetric**: M_t[i,j] = M_t[j,i]
- **Diagonal**: M_t[i,i] = 1.0 (firms perfectly similar to themselves)
- **Range**: [0, 1] where 1 = identical vocabularies, 0 = no overlap
- **Shape**: N_t × N_t

**Processing Steps**:

1. **Load Binary Matrix Q_t**
   - Input: `binary_matrix_YYYY.npz` from Phase 3.1
   - Load firm identifiers from `firm_word_sets_YYYY.parquet`

2. **Compute Cosine Similarity**
   - Method: `sklearn.metrics.pairwise.cosine_similarity(Q_t)`
   - sklearn handles sparse input efficiently
   - Returns dense N_t × N_t matrix

3. **Validation**
   - **Diagonal check**: All diagonal elements ≈ 1.0
   - **Symmetry check**: M_t ≈ M_t^T (within numerical precision)
   - **Value range**: All values in [0, 1]
   - **NaN/inf check**: No invalid values

4. **Statistics** (off-diagonal elements only)
   - Mean, median, std, min, max
   - Percentiles: 50th, 75th, 90th, 95th, 99th

5. **Network Density Analysis**
   - Test thresholds: [0.1, 0.2, 0.3, 0.4, 0.5]
   - For each threshold:
     - Count pairs above threshold
     - Calculate % of total pairs
     - Average peers per firm

**Current Configuration**:
```python
TARGET_YEARS = [2010, 2011]  # Pilot years
# Change to None to process all years
```

**Outputs**:
```
data/korean_tnic/by_year/
├── similarity_matrix_YYYY.npz           # ⭐ Similarity matrix (N_t × N_t)
├── similarity_firms_YYYY.csv            # Firm mapping (index → stock_code)

data/korean_tnic/
└── similarity_matrices_metadata.json    # Metadata for all years

reports/
└── 3.2_similarity_matrices_by_year.md   # Similarity matrix report
```

**Expected Similarity Statistics**:
- Mean similarity: 0.03-0.05 (most firms not very similar)
- Median: 0.02-0.04 (right-skewed distribution)
- 95th percentile: 0.15-0.25
- At threshold=0.2: ~1-5% of pairs connected, ~20-50 peers per firm

**Interpretation**:
- Low mean similarity → sparse network (firms have focused product spaces)
- Right-skewed distribution → few firm-pairs with high similarity
- Long tail → some niche firms are very similar

---

### **Phase 4: Peer Group Definition**

#### `build_tnic_peer_groups.py` ⭐
**Purpose**: Define TNIC peer groups using median adjustment and threshold calibration

**Methodology** (H&P 2016, p. 1436):

**1. Threshold Calibration**:
> "A 21.32 percent minimum similarity threshold generates 10-K-based industries with 2.05 percent membership pairs, which is the same as SIC-3."

**2. Median Adjustment**:
> "For a firm i we compute its median score as the median similarity between firm i and all other firms in the economy in the given year... We achieve this by subtracting these median scores from the raw scores to obtain our final scores used for each firm."

**Processing Steps**:

**Step 1: Load Similarity Matrices**
- Input: `similarity_matrix_YYYY.npz` (raw scores) from Phase 3.2
- Load firm identifiers

**Step 2: Load FnGuide Industry Data**
- Input: `dataguide_groups.parquet` from FnGuide data
- Filter for December (EOY) of target year
- Match with TNIC firms by stock code

**Step 3: Calculate Target Membership Fraction**
- **Membership pair**: Two firms in same FnGuide Industry
- **Formula**: (sum of within-group pairs) / (total possible pairs)
- **Purpose**: Match FnGuide Industry granularity

**FnGuide Industry Baseline**:
- 62 categories (Korean equivalent of SIC-3)
- ~2.95% membership fraction (vs 2.05% for US SIC-3)
- Korean market is denser than US market

**Step 4: Calibrate Threshold on Raw Scores**
- Test thresholds: 0.0 to 0.5 in 0.005 increments
- Find threshold that best matches target membership fraction
- Use **raw similarity scores** (before median adjustment)

**Why calibrate on raw scores?**
- Ensures consistent network density with FnGuide
- Median adjustment comes after threshold is determined

**Step 5: Apply Median Adjustment**

For each firm i:
```python
median_i = np.median(M_raw[i, :])  # Median similarity to all other firms
M_adjusted[i, j] = M_raw[i, j] - median_i  # Subtract median
```

**Purpose**:
- Control for document length effects
- Normalize for firms with verbose vs concise descriptions
- Median should be ≈0 (no industry spans entire economy)

**Result**: M_adjusted is **asymmetric** (i's view of j ≠ j's view of i)

**Step 6: Build TNIC Peer Groups**

For each firm i:
```python
TNIC_peers(i) = {j : M_adjusted[i, j] > threshold, j ≠ i}
```

**Properties**:
- **Firm-centric**: Each firm has unique peer set
- **Non-transitive**: A→B and B→C does NOT imply A→C
- **Asymmetric**: i can be in j's peer group without j being in i's

**Step 7: Compare with FnGuide Industry**

For each firm, classify peers as:
- **TNIC-only**: High similarity but different FnGuide Industry
  - *Hidden competitive relationships*
  - *Less visible to investors*
  - **Key for H&P (2018) momentum hypothesis**
- **FnGuide-only**: Same industry but low similarity
  - *Traditional peers without text-based connection*
  - *May be diversified firms within broad industry*
- **Both**: TNIC and FnGuide agree
  - *Most visible competitive relationships*
  - *Baseline for comparison*

**Current Configuration**:
```python
TARGET_YEARS = [2010, 2011]  # Pilot years
```

**Outputs**:
```
data/korean_tnic/by_year/
├── tnic_peers_YYYY.csv                  # ⭐ Peer relationships
│   Columns: [firm_i, firm_j, stock_code_i, stock_code_j,
│             similarity_i_to_j, similarity_j_to_i, symmetric]
│
├── tnic_vs_fnguide_YYYY.csv            # Comparison statistics
│   Columns: [stock_code, fnguide_industry, n_tnic_peers,
│             n_fnguide_peers, n_both, n_tnic_only,
│             n_fnguide_only, overlap_pct]
│
└── tnic_metadata_YYYY.json             # Calibration metadata

reports/
└── 4.1_tnic_construction_pilot.md       # TNIC construction report (updated)
```

**Expected Results**:
- **Threshold**: 0.15-0.25 (calibrated to match FnGuide)
- **Avg peers per firm**: 25-35
- **Median adjustment**: Mean median ≈ 0.03-0.05
- **TNIC vs FnGuide overlap**: 30-50%
- **TNIC-only peers**: ~15-25 per firm
- **FnGuide-only peers**: ~15-25 per firm

**Critical for Next Phase**: TNIC-only peers are used to test H&P (2018) momentum hypothesis.

---

### **Phase 5: FnGuide Analysis**

#### `analyze_fnguide_classification_levels.py`
**Purpose**: Compare different FnGuide classification levels to choose appropriate baseline

**Classification Levels Analyzed**:
1. **FnGuide Sector** (Broadest) - ~10-15 categories
2. **FnGuide Industry Group 27** (≈ SIC-3) - ~27 categories
3. **FnGuide Industry Group** - ~40 categories
4. **FnGuide Industry** (Finest) - ~62 categories

**Metrics Calculated**:
- Number of categories
- Firms per category (mean, median, std)
- **Membership pairs fraction** (key metric)

**Output**: Console report showing which level is closest to H&P's SIC-3 baseline (2.05%)

**Findings**:
- FnGuide Industry (62 categories) gives ~2.95% membership fraction
- Closest to H&P's SIC-3 (2.05%)
- Korean market is denser than US market at all levels

---

#### `calculate_fnguide_membership_fraction.py`
**Purpose**: Calculate membership pairs fraction for a specific FnGuide level and year

**Formula**:
```python
total_membership_pairs = sum(M_i * (M_i - 1) / 2 for each industry)
total_possible_pairs = N * (N - 1) / 2
membership_fraction = total_membership_pairs / total_possible_pairs
```

Where:
- M_i = number of firms in industry i
- N = total number of firms

**Use**: Helper function for TNIC threshold calibration

---

#### `calculate_all_fnguide_membership_fractions.py`
**Purpose**: Compute membership fractions across all years (2010-2025)

**Output**: Time series showing evolution of industry structure

**Use**:
- Track industry concentration over time
- Verify consistency of FnGuide classifications
- Choose stable baseline for TNIC calibration

---

### **Utilities**

#### `debug_stock_codes.py`
**Purpose**: Diagnose stock code matching issues between datasets

**Checks**:
- Format consistency (6-digit codes)
- Missing stock codes
- Duplicates
- Overlap between TNIC and FnGuide datasets

---

#### `plot_char_distribution.py`
**Purpose**: Visualize character count distribution of business descriptions

**Output**: Histogram showing distribution before/after filtering

---

#### `retrieve_mongodb_data.py`
**Purpose**: Generic MongoDB data retrieval script

**Use**: Ad-hoc data extraction for debugging

---

#### `show_sample_text.py`
**Purpose**: Display sample business descriptions from clean data

**Use**: Manual inspection of text quality

---

#### `show_korean_text.py`
**Purpose**: Test Korean text encoding in console

**Use**: Debug UTF-8 encoding issues on Windows

---

#### `test_korean_tokenization.py`
**Purpose**: Test kiwipiepy Korean tokenizer on sample texts

**Output**:
- Sample tokenization results
- POS tag distribution
- Noun extraction quality

**Use**: Validate tokenizer before running full corpus

---

## Data Flow Diagram

```
MongoDB (DART Database)
    │
    ├─ Collection: FS.A001 (annual reports)
    └─ Section codes: 020000 OR 020100 (business overview)

    ↓ [Phase 1: extract_korean_texts.py]

data/korean_texts/business_descriptions_clean.parquet
    │
    ├─ Columns: [stock_code, corp_name, year, text, char_count, rcept_dt, rcept_no, level]
    └─ ~1,500-2,000 firm-years per year

    ↓ [Phase 2: build_korean_corpus_by_year.py]

data/korean_texts/by_year/YYYY/firm_word_sets_YYYY.parquet
    │
    ├─ Columns: [firm_year, stock_code, year, unique_nouns, word_count]
    ├─ After filters: min 20 words, <25% frequency
    └─ Vocabulary W_t: 10,000-20,000 words per year

    ↓ [Phase 3.1: build_binary_matrices_by_year.py]

data/korean_tnic/by_year/binary_matrix_YYYY.npz
    │
    ├─ Q_t: N_t × W_t sparse binary matrix
    ├─ Q_t[i,j] = 1 if firm i uses word j, else 0
    └─ ~99.3% sparse (CSR format)

    ↓ [Phase 3.2: compute_similarity_matrices_by_year.py]

data/korean_tnic/by_year/similarity_matrix_YYYY.npz
    │
    ├─ M_t: N_t × N_t similarity matrix
    ├─ M_t[i,j] = cosine similarity between firms i and j
    └─ Range: [0, 1], symmetric, diagonal = 1.0

    ↓ [Phase 4: build_tnic_peer_groups.py]

data/korean_tnic/by_year/tnic_peers_YYYY.csv
    │
    ├─ Peer relationships after median adjustment
    ├─ Calibrated threshold to match FnGuide Industry
    └─ TNIC-only vs FnGuide-only vs Both classification

    ↓ [Phase 5: Event study - not in scripts/]

Figure 1 Replication: Turnover around peer return shocks
```

---

## Key Methodology Points

### **1. Year-by-Year Processing (Critical)**

**Why**: H&P (2016) explicitly requires year-specific vocabularies:
> "Q_t is an N_t × W matrix, where N_t is the number of firms in year t"

**Implementation**:
- Each year has separate vocabulary W_t
- Filters applied within each year (not across years)
- Similarity matrices M_t are time-varying

**Wrong Approach** (deprecated):
- `build_korean_corpus.py` built single corpus across all years
- Violates H&P methodology
- **Removed from repository**

---

### **2. Binary Representation (Not TF-IDF)**

**Why**: H&P (2016) explicitly uses binary:
> "P_i with each element being populated by the number **1 if firm i uses the given word and 0 if it does not**"

H&P footnote 10 (p. 1432):
> "Our results suggest that uniform weights outperform TF-IDF weights for our application"

**Implementation**:
- Q_t[i,j] ∈ {0, 1}
- Word used once = same as word used 50 times

---

### **3. Median Adjustment (Document Length Control)**

**Why**: H&P (2016, p. 1436):
> "subtracting these median scores from the raw scores to obtain our final scores"

**Purpose**:
- Control for document length effects
- Longer documents → higher chance of overlap → inflated similarities
- Median should be near zero (no industry spans entire economy)

**Implementation**:
```python
for i in range(N):
    median_i = np.median(M_raw[i, :])
    M_adjusted[i, :] = M_raw[i, :] - median_i
```

---

### **4. Threshold Calibration (Match Industry Granularity)**

**Why**: H&P (2016, p. 1436):
> "A 21.32 percent minimum similarity threshold generates 10-K-based industries with 2.05 percent membership pairs, which is the same as SIC-3"

**Purpose**: Ensure TNIC networks have comparable density to traditional classifications

**Implementation**:
- Calculate FnGuide Industry membership fraction (~2.95%)
- Calibrate threshold on raw scores to match
- Apply threshold to median-adjusted scores

**Korean Adaptation**:
- Use FnGuide Industry (62 categories) as baseline
- Korean market is denser (2.95% vs 2.05% in US)
- Expected threshold: 0.15-0.25 (vs 0.2132 in H&P)

---

### **5. TNIC-Only Peers (Key for Momentum Hypothesis)**

**H&P (2018) Hypothesis**:
> Shocks to TNIC-only peers (not in same SIC) generate stronger momentum due to investor inattention

**Three Types of Peers**:
1. **TNIC-only**: High similarity but different FnGuide Industry
   - Hidden competitive relationships
   - Less visible to investors
   - **Expected to show stronger/longer momentum**
2. **FnGuide-only**: Same industry but low similarity
   - Traditional peers without text-based connection
3. **Both**: TNIC and FnGuide agree
   - Most visible competitive relationships
   - Baseline for comparison

---

## Expected Execution Times

Based on pilot runs with [2010, 2011] data:

| Phase | Script | Time (2 years) | Time (all years, est.) |
|-------|--------|----------------|------------------------|
| 1 | extract_korean_texts.py | ~5 minutes | ~5 minutes |
| 2 | build_korean_corpus_by_year.py | ~10 minutes | ~60-90 minutes |
| 3.1 | build_binary_matrices_by_year.py | ~5 minutes | ~30-45 minutes |
| 3.2 | compute_similarity_matrices_by_year.py | ~10 minutes | ~60-90 minutes |
| 4 | build_tnic_peer_groups.py | ~5 minutes | ~30-45 minutes |
| **Total** | | **~35 minutes** | **~3-4 hours** |

**Note**: Times assume:
- ~1,500-2,000 firms per year
- ~10,000-20,000 words vocabulary per year
- Modern CPU (8+ cores)

---

## Common Issues and Solutions

### **Issue 1: MongoDB Connection Failed**
**Error**: `pymongo.errors.ServerSelectionTimeoutError`

**Solution**:
```bash
# Check MongoDB is running
poetry run python scripts/check_mongodb.py

# Verify .env file has correct settings
MONGO_HOST=localhost:27017
DB_NAME=FS
COLLECTION_NAME=A001
```

---

### **Issue 2: Korean Text Encoding Errors**
**Error**: `UnicodeEncodeError` or garbled Korean text in console

**Solution**:
```bash
# On Windows, scripts automatically set UTF-8:
os.system('chcp 65001 > nul')
sys.stdout.reconfigure(encoding='utf-8')

# Test encoding:
poetry run python scripts/show_korean_text.py
```

---

### **Issue 3: Memory Error in Similarity Computation**
**Error**: `MemoryError` in `compute_similarity_matrices_by_year.py`

**Cause**: Large N_t × N_t similarity matrix doesn't fit in RAM

**Solution**:
```python
# For year with N_t = 2,000 firms:
# Memory needed: 2,000 × 2,000 × 8 bytes = 32 MB (should be fine)

# If N_t > 5,000, use chunked computation:
# Split into blocks and compute pairwise
```

---

### **Issue 4: Pilot Years Only Processing**
**Symptom**: Only 2010-2011 processed, other years skipped

**Cause**: Scripts have hardcoded `TARGET_YEARS = [2010, 2011]`

**Solution**:
```python
# Edit these scripts:
# - build_binary_matrices_by_year.py (line 256)
# - compute_similarity_matrices_by_year.py (line 308)
# - build_tnic_peer_groups.py (line 44)

# Change from:
TARGET_YEARS = [2010, 2011]

# To:
TARGET_YEARS = None  # Process all available years
```

---

### **Issue 5: FnGuide-TNIC Stock Code Mismatch**
**Symptom**: Low match rate between TNIC and FnGuide datasets

**Cause**: Stock code format differences (e.g., "A005930" vs "005930")

**Solution**:
```python
# Scripts automatically clean stock codes:
df['stock_code'] = df['symbol'].str.replace('A', '', regex=False)
df['stock_code'] = df['stock_code'].str.zfill(6)  # Pad to 6 digits

# Debug mismatches:
poetry run python scripts/debug_stock_codes.py
```

---

## Validation Checklist

Before proceeding to event study (Phase 5), validate:

### **Phase 1 Output**
- [ ] `business_descriptions_clean.parquet` exists
- [ ] Retention rate 70-90% after deduplication
- [ ] ~1,500-2,000 firm-years per year
- [ ] Mean char count: 2,000-4,000

### **Phase 2 Output**
- [ ] `firm_word_sets_YYYY.parquet` exists for all years
- [ ] Avg words per firm: 50-200 (after filters)
- [ ] Vocabulary W_t: 10,000-30,000 per year
- [ ] Firms removed: 5-15% (below 20-word threshold)

### **Phase 3 Output**
- [ ] `binary_matrix_YYYY.npz` and `similarity_matrix_YYYY.npz` exist
- [ ] Binary matrix validation: row sums = word counts
- [ ] Similarity matrix validation: diagonal ≈ 1.0, symmetric
- [ ] Mean similarity: 0.03-0.05 (sparse network)
- [ ] At threshold=0.2: ~20-50 peers per firm

### **Phase 4 Output**
- [ ] `tnic_peers_YYYY.csv` exists for all years
- [ ] Calibrated threshold: 0.15-0.25
- [ ] Avg peers per firm: 25-35
- [ ] TNIC vs FnGuide overlap: 30-50%
- [ ] TNIC-only peers: ~15-25 per firm

---

## Next Steps After Phase 4

Once TNIC peer groups are built for all years:

### **Phase 5: Event Study with TNIC Peers**

**Goal**: Replicate H&P (2018) Figure 1 using TNIC-based peer groups

**Script Location**: `figure1_graph_a.py` (in project root, not scripts/)

**Methodology**:
1. Load TNIC peer groups from Phase 4
2. Calculate peer returns for each firm-month
   - TNIC-only peers
   - FnGuide-only peers
   - Both (overlapping peers)
3. Identify high-quintile peer return shocks (top 20%)
4. Extract turnover windows (t-3 to t+12 months)
5. Normalize by t=0 turnover
6. Compare patterns across peer types

**Expected Results** (H&P 2018 hypothesis):
- **TNIC-only peers**: Strongest/longest momentum (6-12 months)
- **FnGuide-only peers**: Weakest momentum (1-2 months)
- **Both peers**: Intermediate momentum (3-6 months)

**Interpretation**:
- TNIC-only peers capture hidden competitive relationships
- Less visible to investors → slower price adjustment → stronger momentum
- Consistent with investor inattention hypothesis

---

## References

### **Primary Methodology**
Hoberg, G., & Phillips, G. M. (2016). Text-based network industries and endogenous product differentiation. *Journal of Political Economy*, 124(5), 1423-1465.

**Key sections**:
- Section II.A: Text processing methodology
- Appendix A: Detailed implementation
- Appendix B: Fixed classification algorithm

### **Application Paper**
Hoberg, G., & Phillips, G. M. (2018). Text-based industry momentum. *Journal of Financial and Quantitative Analysis*, 53(6), 2355-2388.

**Key sections**:
- Section II: TNIC methodology recap
- Section III: Event study design
- Figure 1: Turnover around peer shocks (our replication target)

### **Project Documentation**
- `CLAUDE.md` - Overall project instructions
- `thesis/research/tnic-methodology-hoberg-phillips-2016.md` - Detailed H&P methodology
- `computational_linguistics_exercise/` - H&P reference implementation

---

## Contact and Support

For issues or questions:
1. Check `reports/*.md` files for detailed phase outputs
2. Review `data/korean_tnic/*/metadata.json` for statistics
3. Consult H&P (2016) paper for methodology clarification

---

**Last Updated**: 2025-01-04 (Generated during TNIC pipeline development)
