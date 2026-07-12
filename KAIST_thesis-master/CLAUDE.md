# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Objective

**Replicate Hoberg & Phillips (2018) "Text-Based Industry Momentum" using Korean market data**

**Target Paper**: Hoberg, G., & Phillips, G. M. (2018). Text-based industry momentum. *Journal of Financial and Quantitative Analysis*, 53(6), 2355-2388.

**Key Hypothesis**: Shocks to text-based network industry peers that are less visible (don't overlap with traditional classifications) generate stronger momentum profits due to investor inattention.

**Our Approach**:
- Replace SEC 10-K business descriptions → Korean DART financial report business descriptions (from MongoDB)
- Replace SIC codes → FnGuide industry classifications
- Replicate Figure 1: Turnover patterns around peer shocks
- Compare TNIC-based peers vs FnGuide-based peers

## Repository Structure

### Working Code

**figure1_graph_a.py** - BASELINE REPLICATION (currently working)
- Replicates Figure 1A using FnGuide industry classifications
- Event study: turnover around high-quintile peer return shocks
- Window: t-3 to t+12 months
- Output: `outputs/figure1a_turnover_peer_shock.png`
- **Status**: Working with FnGuide data (Korean equivalent of SIC)

**sample_mongo_db.json** - MongoDB data structure reference
- Shows structure of Korean business description data
- Key fields: `stock_code`, `text`, `corp_name`, `section_title`

### Reference Materials

**computational_linguistics_exercise/** - Official H&P methodology reference
- Original Hoberg & Phillips exercise materials
- `data/rantextsout/` - Sample 10-K text files (English)
- `data/binary.csv`, `data/similarity.csv` - Example outputs
- **Use this to understand TNIC methodology**, then adapt for Korean

**docs/papers/** - Academic papers
- **Primary**: `Text-Based_Industry_Momentum_...pdf.txt` (use .txt version, .md incomplete)
- **TNIC methodology**: Hoberg & Phillips (2016) JPE paper
- Contains full paper text for methodology reference

### Code to Rewrite

**tnic/** - UNTESTED trial implementation
- Attempted TNIC implementation but NEVER tested
- **Status**: Should be rewritten when connecting to actual MongoDB data
- Contains: text cleaning, corpus building, similarity calculation
- **Do not trust this code** - use as reference only, rewrite from scratch

### Supporting Scripts

**scripts/** - Utility scripts
- `run_tnic_pipeline.py` - Untested CLI runner
- `test_config.py` - Configuration testing

### Data

**data/fnguide/processed/** - Korean financial market data
- `price_wide.parquet` - Monthly stock prices
- `turnover_listed_wide.parquet` - Trading turnover
- `dataguide_filtered.parquet` - Company metadata + FnGuide industry codes
- **Critical field**: `FnGuide Industry` (Korean equivalent of SIC)

**data/** (other subdirectories)
- `jkp/`, `patent/` - Other datasets (not primary focus)

### Analysis Scripts

**load_dataguide.py**, **analysis_dataguide.py**, **eda_dataguide.py**
- FnGuide data loading and exploration
- Helper scripts for data analysis

## Development Setup

```bash
# Install dependencies
poetry install

# Install Korean NLP support
poetry install -E korean

# Activate environment
poetry shell

# Install NLTK data (for eventual English validation)
poetry run python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

## MongoDB Data Structure

**Source**: Korean DART financial reports (equivalent to SEC EDGAR)

**Sample document** (see `sample_mongo_db.json`):
```json
{
  "document_id": "20250318000739_020100",
  "rcept_no": "20250318000739",
  "rcept_dt": "20250318",
  "year": "2025",
  "corp_code": "00119195",
  "corp_name": "동화약품",
  "stock_code": "000020",              ← KEY: Match with FnGuide data
  "report_type": "A001",
  "report_name": "사업보고서 (2024.12)",
  "section_code": "020100",
  "section_title": "1. 사업의 개요",   ← Business Overview (like 10-K Item 1)
  "text": "당사는 제약업, 의료기기...", ← Korean business description text
  "char_count": 3364,
  "word_count": 663
}
```

**Key fields**:
- `stock_code`: 6-digit Korean stock code (e.g., "000020") - use to match FnGuide data
- `text`: Korean business description (equivalent to 10-K Item 1 Business section)
- `section_code`: "020100" is business overview section
- `year`: Report year

**Connection details**: Should be in `.env` file
```bash
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=dart
MONGODB_COLLECTION=business_reports
```

## Data Flow Architecture

### Current State (Baseline)

```
FnGuide Data → Industry Groups → Peer Returns → Event Study → Figure 1A
```

### Target State (TNIC-based)

```
MongoDB (Korean Text) → Korean NLP → TNIC Similarity → TNIC Peers → Event Study → Figure 1
                                                              ↓
                                                    Compare with FnGuide Peers
```

## Running Current Code

### Baseline Replication (FnGuide Industries)

```bash
python figure1_graph_a.py
```

**What it does**:
1. Loads FnGuide price/turnover data from `data/fnguide/processed/`
2. Creates time-varying industry peer groups (FnGuide classification)
3. Calculates peer returns (equal-weighted, excluding focal firm)
4. Identifies high-quintile (top 20%) peer return shocks
5. Extracts turnover windows (t-3 to t+12) around shocks
6. Normalizes by t=0 turnover and plots

**Output**: `outputs/figure1a_turnover_peer_shock.png`

**Expected pattern**: Turnover spike at t=0 (peer shock), persistence to t+12 months

## Development Roadmap

### Phase 1: Validate Methodology (DONE)
- ✅ Implement baseline Figure 1A with FnGuide industries
- ✅ Understand event study methodology
- ✅ Validate data structure and coverage

### Phase 2: Connect to MongoDB (TODO - NEXT)
1. **Query MongoDB for business descriptions**
   ```python
   from pymongo import MongoClient

   client = MongoClient("mongodb://localhost:27017/")
   db = client["dart"]
   collection = db["business_reports"]

   # Query: business overview sections only
   docs = collection.find({
       "section_code": "020100",  # Business overview
       "year": {"$gte": "2010"}   # Year range
   })
   ```

2. **Extract and validate data**
   - Get unique `stock_code` values
   - Match with FnGuide `symbol` field
   - Check text quality (length, completeness)
   - Group by firm and year

3. **Data quality checks**
   - How many firms have business descriptions?
   - Time coverage (2010-2024)?
   - Average text length?
   - Missing/incomplete descriptions?

### Phase 3: Build Korean TNIC (TODO)

**Rewrite `tnic/` from scratch** (current code is untested)

1. **Korean text preprocessing**
   ```python
   # Use Mecab for Korean tokenization
   from konlpy.tag import Mecab

   mecab = Mecab()

   # Tokenize and filter
   tokens = mecab.nouns(korean_text)  # Extract nouns only
   tokens = [t for t in tokens if len(t) >= 2]  # Min length 2
   tokens = [t for t in tokens if not is_number(t)]  # Remove numbers
   ```

2. **Build corpus and binary matrix**
   - Collect all unique Korean words across firms
   - Create firm × word binary matrix (1 if word present, 0 otherwise)
   - Filter: Keep firms with ≥20 unique words (H&P methodology)

3. **Compute pairwise similarities**
   ```python
   from sklearn.metrics.pairwise import cosine_similarity

   # Cosine similarity between firms
   similarity_matrix = cosine_similarity(binary_matrix)
   ```

4. **Define TNIC peer groups**
   - For each firm, rank other firms by similarity
   - Define peers as firms with similarity > threshold (e.g., 0.2)
   - Or top-N most similar firms

### Phase 4: Event Study with TNIC Peers (TODO)

1. **Adapt `figure1_graph_a.py` to use TNIC peers**
   - Replace FnGuide industry grouping with TNIC similarity-based peers
   - Keep same event study methodology
   - Compare results

2. **Key comparison: TNIC vs FnGuide**
   - TNIC-only peers (similar but different FnGuide industry)
   - Overlapping peers (TNIC + FnGuide agree)
   - FnGuide-only peers (same industry but low TNIC similarity)

3. **Test H&P hypothesis**
   - **Prediction**: TNIC-only peers should show stronger/longer momentum
   - **Reason**: Less visible to investors (not in same SIC/FnGuide group)

## Key Methodological Details

### Event Study Design (from H&P 2018)

1. **Peer return calculation**
   - Equal-weighted average of peer returns
   - **CRITICAL**: Exclude focal firm from peer calculation
   - Time-varying peer groups (industries/similarities change over time)

2. **Event definition**
   - High-quintile = top 20% of cross-sectional peer returns each month
   - Calculate quintile breakpoints separately for each date

3. **Window extraction**
   - t-3 to t+12 months (16 months total)
   - Require complete data (no missing turnover in window)
   - Exclude overlapping events (if firm has event at t, exclude events at t+1 to t+15)

4. **Normalization**
   - Divide all turnover by turnover at t=0
   - This controls for cross-sectional differences in turnover levels

### Korean Text Processing

**H&P methodology (English)**:
- Lowercase
- Remove punctuation, numbers, stopwords
- Keep only nouns (via POS tagging)
- Min word length: 2-3 characters

**Korean adaptation**:
- Mecab tokenization (morphological analysis)
- Keep only nouns (명사): Mecab.nouns()
- Min length: 2 characters (Korean words typically 2-4 chars)
- Remove numbers, single-char words, common stopwords
- **Issue**: Korean doesn't have direct equivalent to English stopwords
  - May need custom Korean stopword list
  - Or frequency-based filtering (H&P alternative method)

### Similarity Thresholds

H&P use multiple approaches:
- Fixed threshold (e.g., similarity > 0.2)
- Top-N peers (e.g., 20 most similar firms)
- Industry-adjusted (peers within same broad sector)

**Recommendation**: Start with fixed threshold = 0.2, validate with multiple thresholds

## Critical Data Mappings

### MongoDB → FnGuide

**Primary key**: `stock_code` (MongoDB) = `symbol` (FnGuide)

Both are 6-digit Korean stock codes (e.g., "000020" for 동화약품)

**Time matching**:
- MongoDB: `year` field (e.g., "2024")
- FnGuide: `date` field (monthly, end-of-month dates)
- **Match rule**: Use business description from annual report year for all months in that year

**Example**:
```python
# For firm with stock_code "000020"
# Business description from 2024 annual report
# Apply to all months: 2024-01 to 2024-12
```

### Section Codes (MongoDB)

- `020100` = "사업의 개요" (Business Overview) ← **This is what we want**
- Similar to SEC 10-K Item 1 (Business section)

**Query filter**:
```python
collection.find({"section_code": "020100"})
```

## Expected Outputs

### Phase 2 (MongoDB Connection)
- `data/korean_texts/` - Extracted business descriptions by firm-year
- `korean_corpus_stats.csv` - Text statistics (word counts, coverage)

### Phase 3 (Korean TNIC)
- `outputs/korean_tnic/binary_matrix.csv` - Firm × word binary matrix
- `outputs/korean_tnic/similarity_matrix.csv` - Firm × firm similarities
- `outputs/korean_tnic/peer_groups.csv` - TNIC peer assignments
- `outputs/korean_tnic/corpus_stats.csv` - Word frequency statistics

### Phase 4 (Event Study)
- `outputs/figure1a_fnguide.png` - Baseline (FnGuide peers)
- `outputs/figure1a_tnic.png` - TNIC peers
- `outputs/figure1a_tnic_only.png` - TNIC-only peers (not FnGuide)
- `outputs/comparison_table.csv` - Statistical comparison

## Common Development Commands

### Explore MongoDB Data

```python
from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb://localhost:27017/")
db = client["dart"]
collection = db["business_reports"]

# Count documents
print(f"Total documents: {collection.count_documents({})}")

# Check section codes
sections = collection.distinct("section_code")
print(f"Section codes: {sections}")

# Sample business overview sections
docs = list(collection.find(
    {"section_code": "020100"},
    limit=5
))

# Convert to DataFrame for analysis
df = pd.DataFrame(docs)
print(df[['stock_code', 'corp_name', 'year', 'char_count']].head())
```

### Match with FnGuide Data

```python
import pandas as pd

# Load FnGuide data
fnguide = pd.read_parquet("data/fnguide/processed/dataguide_filtered.parquet")

# Get unique stock codes in MongoDB
mongo_codes = set(df['stock_code'].unique())

# Get unique symbols in FnGuide
fnguide_codes = set(fnguide['symbol'].unique())

# Find overlap
overlap = mongo_codes & fnguide_codes
print(f"Firms in both datasets: {len(overlap)}")
print(f"Only in MongoDB: {len(mongo_codes - fnguide_codes)}")
print(f"Only in FnGuide: {len(fnguide_codes - mongo_codes)}")
```

### Test Korean Tokenization

```python
from konlpy.tag import Mecab

mecab = Mecab()

sample_text = """
당사는 제약업, 의료기기 제조 및 판매업, 기타금융업을 운영하고 있습니다.
연결실체는 제약업, 기타금융업, 의료기기 제조판매업, 의약품 유통체인 등을 영위하고 있습니다.
"""

# Extract nouns
nouns = mecab.nouns(sample_text)
print(f"Nouns: {nouns}")

# Filter
nouns = [n for n in nouns if len(n) >= 2]
nouns = list(set(nouns))  # Unique
print(f"Filtered: {nouns}")
```

## Important Notes

### Abandoned Code
- **kopdb/** - Patent data pipeline, NOT relevant to thesis, ignore completely
- **KOPDB_REFACTORED_README.md**, **REFACTORING_SUMMARY.md** - Ignore

### Untested Code
- **tnic/** - Trial implementation, never validated
- When building Korean TNIC, use this as reference but rewrite from scratch
- Test thoroughly with `computational_linguistics_exercise/` English data first

### No Reference TNIC Data
- We do NOT have official Hoberg-Phillips TNIC scores for Korean firms
- Cannot validate Korean TNIC against ground truth
- Instead, validate methodology with English data, then apply to Korean

### Time-Varying Peer Groups
**Critical**: Both FnGuide industries and TNIC peers can change over time

```python
# BAD: Static peer groups
peers = get_peers(firm)  # Same peers for all dates

# GOOD: Time-varying peer groups
peers = get_peers(firm, date)  # Different peers each month
```

For TNIC: Business descriptions update annually, so peer similarities change yearly.

### Turnover Calculation
**Definition**: Trading volume / shares outstanding

FnGuide provides `turnover_listed` which is already calculated. Verify formula if needed:
```python
turnover = volume / shares_outstanding * 100
```

## Data Quality Considerations

### MongoDB Data
- Check for missing/incomplete business descriptions
- Verify `stock_code` format consistency
- Handle multiple reports per year (use most recent)
- Text quality: Some reports may have parsing errors

### FnGuide Data
- Check for suspended trading (turnover = 0)
- Handle delistings (missing data after delisting)
- Price adjustments (splits, dividends) - should be pre-adjusted
- FnGuide industry changes (firms can switch industries)

### Matching Issues
- Some MongoDB firms may not be in FnGuide (small/delisted firms)
- Some FnGuide firms may not have business descriptions in MongoDB
- **Solution**: Use intersection only (firms in both datasets)

## Testing Strategy

### Phase 1: English Validation
1. Use `computational_linguistics_exercise/` data
2. Implement TNIC pipeline for English
3. Compare with reference outputs (binary.csv, similarity.csv)
4. Validate methodology works correctly

### Phase 2: Korean Implementation
1. Test Mecab tokenization on sample texts
2. Build small-scale TNIC (10-20 firms)
3. Manually inspect similarity scores
4. Validate reasonable peer groupings

### Phase 3: Full Pipeline
1. Run on complete Korean dataset
2. Compare TNIC peers vs FnGuide industries
3. Sanity checks:
   - Similar firms have high similarity scores
   - Different industries have low similarity
   - Peer groups are reasonable size (5-50 firms)

## Expected Results

**Hypothesis (from H&P 2018)**:
1. **TNIC peers show momentum effects**
   - Turnover increases after peer shocks
   - Effect persists 6-12 months

2. **TNIC-only peers show stronger effects than FnGuide**
   - Longer persistence (up to 12 months vs 1-2 months)
   - Larger magnitude
   - Consistent with investor inattention

3. **Overlapping peers (TNIC + FnGuide) show intermediate effects**

**Prediction for Korean market**:
- Should replicate US findings
- Korean market may have different information environment
- Smaller market → potentially stronger inattention effects

## Next Immediate Steps

1. **Connect to MongoDB** - Query and extract business descriptions
2. **Validate data coverage** - Check firm-year overlap with FnGuide
3. **Test Korean NLP** - Verify Mecab tokenization quality
4. **Build small TNIC** - Test with 20-50 firms first
5. **Scale up** - Full dataset once methodology validated

## References

**Primary Paper**: docs/papers/Text-Based_Industry_Momentum...pdf.txt

**Key Sections**:
- Section II: TNIC methodology
- Section III: Event study design
- Figure 1: Turnover around peer shocks (our target replication)
- Table 2-4: Momentum profit statistics

**TNIC Methodology**: Hoberg & Phillips (2016) JPE - See docs/papers/
