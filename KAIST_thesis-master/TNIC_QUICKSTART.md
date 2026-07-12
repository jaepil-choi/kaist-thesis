# TNIC Pipeline - Quick Reference

## 🚀 Installation & Setup

```bash
# 1. Install dependencies
poetry install

# 2. Download NLTK data (one-time setup)
poetry run python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('punkt_tab')"

# 3. Verify installation
poetry run python -c "from tnic import TNICPipeline; print('✓ TNIC installed!')"
```

## 📊 Run the Pipeline (3 Ways)

### Option 1: Command Line (Easiest)

```bash
poetry run python scripts/run_tnic_pipeline.py --input computational_linguistics_exercise/data/rantextsout --output outputs/tnic
```

### Option 2: Python Script

```python
from pathlib import Path
from tnic import TNICPipeline

pipeline = TNICPipeline(output_dir=Path("outputs/tnic"))
results = pipeline.run(input_dir=Path("computational_linguistics_exercise/data/rantextsout"))

print(f"✓ Processed {results['n_firms']} firms")
print(f"✓ Mean similarity: {results['mean_similarity']:.3f}")
```

### Option 3: Jupyter Notebook

```bash
poetry run jupyter lab examples/tnic_example.py
```

## 📁 Output Files

All results are saved to `outputs/tnic/`:

| File | Description |
|------|-------------|
| `binary_matrix.csv` | Word presence matrix (0/1) |
| `similarity_matrix.csv` | Firm-to-firm similarity scores |
| `pairwise_similarities.csv` | Long format: (firm1, firm2, score) |
| `firm_statistics.csv` | Statistics per firm |
| `word_statistics.csv` | Word frequency stats |
| `top10_words.png` | Visualization |

## 🔍 Common Use Cases

### Find Industry Peers

```python
from pathlib import Path
from tnic import TNICPipeline

pipeline = TNICPipeline(output_dir=Path("outputs/tnic"))
results = pipeline.run(input_dir=Path("data/rantextsout"))

# Get top 10 most similar firms
firm_id = list(results['binary_df'].index)[0]
peers = pipeline.get_industry_peers(firm_id, top_n=10)
print(peers)
```

### Customize Configuration

```python
from tnic import TNICPipeline
from tnic.config import TNICConfig

config = TNICConfig(
    min_word_length=3,           # Only words > 3 chars
    remove_stopwords=True,       # Remove common words
    keep_pos_tags=["NN", "NNS"] # Keep nouns only
)

pipeline = TNICPipeline(config=config, output_dir=Path("outputs/tnic"))
```

### Compare with Hoberg-Phillips TNIC

```python
# If you have the official TNIC data
comparison = pipeline.compare_with_hoberg_phillips(
    tnic_file=Path("data/hoberg/tnic3_data.txt"),
    year=2018,
    mapping_file=Path("data/Map_gvkey_cik.xlsm")
)
print(f"Correlation: {comparison[['score_sample', 'score_tnic']].corr().iloc[0,1]:.3f}")
```

## 📚 Documentation

- **Getting Started**: `TNIC_PIPELINE_README.md`
- **Full API Docs**: `tnic/README.md`
- **Implementation Details**: `tnic/IMPLEMENTATION_NOTES.md`
- **Example Notebook**: `examples/tnic_example.py`

## 🏗️ Package Structure

```
tnic/
├── __init__.py           # Main package
├── config.py             # Configuration
├── cleaner.py            # Text preprocessing
├── processor.py          # Corpus & matrix building
├── similarity.py         # Cosine similarity
├── pipeline.py           # End-to-end orchestrator
└── utils.py              # Utilities

scripts/
└── run_tnic_pipeline.py  # CLI script

examples/
└── tnic_example.py       # Example notebook (Jupytext format)
```

## 🎯 Key Concepts

### Similarity Score Interpretation

- **0.0 - 0.1**: Unrelated firms (different industries)
- **0.1 - 0.3**: Same broad industry (some overlap)
- **0.3 - 0.5**: Related products (moderate competition)
- **> 0.5**: Direct competitors (high overlap)

### Methodology

1. **Clean Text**: Lowercase → Remove punctuation → Remove stopwords → Keep nouns
2. **Build Corpus**: Union of all unique words across all firms
3. **Vectorize**: Binary matrix (1 = word present, 0 = absent)
4. **Compute Similarity**: Cosine similarity between word vectors

## 📖 References

**Paper**: Hoberg, Gerard, and Gordon Phillips. "Text-based network industries and endogenous product differentiation." *Journal of Political Economy* 124.5 (2016): 1423-1465.

**Data**: http://hobergphillips.tuck.dartmouth.edu

---

**Need Help?** Check the full documentation in `tnic/README.md` or the example notebook in `examples/tnic_example.py`
