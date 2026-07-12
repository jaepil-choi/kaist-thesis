# TNIC Pipeline - Getting Started Guide

This guide will help you get started with the **Text-Based Network Industry Classification (TNIC)** pipeline.

## What is TNIC?

TNIC is a methodology developed by **Hoberg and Phillips (2016)** that uses **textual analysis** of 10-K business descriptions to measure **product market similarity** between firms.

### Why Use TNIC?

Traditional industry classifications (SIC, NAICS) have limitations:
- **Static**: Don't update with business changes
- **Coarse**: Force firms into predefined buckets
- **Incomplete**: Miss product-level competitive relationships

TNIC addresses these by:
- **Dynamically** updating with annual 10-K filings
- **Granularly** capturing product-level overlap
- **Data-driven** classification without manual coding

## Installation

### 1. Install Dependencies

```bash
# Install all dependencies via Poetry
poetry install

# Download required NLTK data
poetry run python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('punkt_tab')"
```

### 2. Verify Installation

```bash
# Test import
poetry run python -c "from tnic import TNICPipeline; print('TNIC pipeline installed successfully!')"
```

## Quick Start (3 Steps)

### Step 1: Prepare Your Data

The pipeline expects a directory of text files (e.g., extracted 10-K Item 1 business descriptions):

```
data/
  rantextsout/
    firm1.txt
    firm2.txt
    firm3.txt
    ...
```

**Example data location**: `computational_linguistics_exercise/data/rantextsout/`

### Step 2: Run the Pipeline

**Option A: Command Line (Easiest)**

```bash
poetry run python scripts/run_tnic_pipeline.py \
    --input computational_linguistics_exercise/data/rantextsout \
    --output outputs/tnic
```

**Option B: Python Script**

```python
from pathlib import Path
from tnic import TNICPipeline

pipeline = TNICPipeline(output_dir=Path("outputs/tnic"))
results = pipeline.run(input_dir=Path("computational_linguistics_exercise/data/rantextsout"))

print(f"Processed {results['n_firms']} firms")
print(f"Mean similarity: {results['mean_similarity']:.3f}")
```

**Option C: Jupyter Notebook**

```bash
# Open the example notebook
poetry run jupyter lab examples/tnic_example.py
```

### Step 3: View Results

The pipeline outputs several files to the specified output directory:

```
outputs/tnic/
├── binary_matrix.csv              # Word presence matrix
├── similarity_matrix.csv          # Firm similarity matrix
├── pairwise_similarities.csv      # Long-format similarities
├── firm_statistics.csv            # Firm-level stats
├── word_statistics.csv            # Word-level stats
├── similarity_statistics.csv      # Summary statistics
└── top10_words.png               # Visualization
```

## Example Use Cases

### 1. Find Industry Peers

```python
from pathlib import Path
from tnic import TNICPipeline

# Run pipeline
pipeline = TNICPipeline(output_dir=Path("outputs/tnic"))
results = pipeline.run(input_dir=Path("data/rantextsout"))

# Find peers for a specific firm
firm_id = list(results['binary_df'].index)[0]
peers = pipeline.get_industry_peers(firm_id, top_n=10)

print(f"Top 10 peers for {firm_id}:")
print(peers)
```

### 2. Analyze Word Usage

```python
# Get word statistics
word_stats = results['word_stats']

# Most common words
print("Top 10 words:")
print(word_stats.head(10))

# Rare words (potential industry-specific terms)
rare_words = word_stats[word_stats['count'] <= 2]
print(f"\nRare words: {len(rare_words)}")
```

### 3. Compare with Hoberg-Phillips TNIC

```python
# If you have the official TNIC data
comparison = pipeline.compare_with_hoberg_phillips(
    tnic_file=Path("data/hoberg/tnic3_data.txt"),
    year=2018,
    mapping_file=Path("data/Map_gvkey_cik.xlsm")
)

print(f"Correlation: {comparison[['score_sample', 'score_tnic']].corr().iloc[0,1]:.3f}")
```

## Understanding the Output

### Similarity Scores

The pipeline computes **cosine similarity** between all firm pairs:

```
similarity(i,j) = (v_i · v_j) / (||v_i|| ||v_j||)
```

**Interpretation:**
- **0.0**: No word overlap (completely different products)
- **0.5**: Moderate overlap (some product similarity)
- **1.0**: Perfect overlap (identical word sets)

Typical ranges:
- **< 0.1**: Unrelated firms
- **0.1 - 0.3**: Same broad industry
- **> 0.3**: Direct competitors

### Binary Matrix

The binary matrix represents word presence:
- **Rows**: Words in the corpus
- **Columns**: Firms
- **Values**: 1 if word appears in firm's description, 0 otherwise

This is the **bag-of-words** representation used to compute similarities.

## Configuration Options

Customize the pipeline using `TNICConfig`:

```python
from tnic import TNICPipeline
from tnic.config import TNICConfig

config = TNICConfig(
    min_word_length=3,              # Only keep words > 3 characters
    remove_stopwords=True,          # Remove common words
    keep_pos_tags=["NN", "NNS"],   # Keep only nouns (singular + plural)
)

pipeline = TNICPipeline(config=config, output_dir=Path("outputs/tnic"))
```

## Pipeline Architecture

```
Input: Text Files (10-K Business Descriptions)
    ↓
[1] TextCleaner
    - Lowercase
    - Remove punctuation
    - Remove stopwords
    - Tokenize
    - POS tagging (keep nouns)
    ↓
[2] TNICProcessor
    - Build corpus (all unique words)
    - Create binary matrix (firms × words)
    ↓
[3] SimilarityCalculator
    - Compute cosine similarity
    - Generate pairwise scores
    ↓
Output: Similarity Matrices & Statistics
```

## Troubleshooting

### NLTK Data Not Found

```bash
poetry run python -c "import nltk; nltk.download('all')"
```

### No Files Found

Check that your input directory contains `.txt` files:

```bash
dir computational_linguistics_exercise\data\rantextsout\*.txt
```

### Memory Issues

For large datasets (>1000 firms), use batching:

```python
config = TNICConfig(batch_size=100)
pipeline = TNICPipeline(config=config)
```

## Next Steps

1. **Read the full documentation**: `tnic/README.md`
2. **Explore the example notebook**: `examples/tnic_example.py`
3. **Read the original paper**: Hoberg & Phillips (2016) JPE
4. **Download official TNIC data**: http://hobergphillips.tuck.dartmouth.edu

## References

**Primary Paper:**
- Hoberg, Gerard, and Gordon Phillips. "Text-based network industries and endogenous product differentiation." *Journal of Political Economy* 124, no. 5 (2016): 1423-1465.

**Data Library:**
- Hoberg-Phillips Data Library: http://hobergphillips.tuck.dartmouth.edu

## Support

For issues or questions:
1. Check the documentation in `tnic/README.md`
2. Review the example notebook in `examples/tnic_example.py`
3. Check the original exercise materials in `computational_linguistics_exercise/`

---

**Happy analyzing! 📊**
