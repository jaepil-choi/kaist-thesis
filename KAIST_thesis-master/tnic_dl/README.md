# TNIC-DL: Kim et al. (2020) Deep Autoencoder for Korean TNIC

This module implements the **Kim et al. (2020) deep autoencoder methodology** for generating low-dimensional (10-dim) industry embeddings from Korean business descriptions.

## Reference Paper

**Kim et al. (2020)**: "An artificial intelligence-enabled industry classification and its interpretation"

Full methodology documented in: `thesis/research/kim-et-al-deep-autoencoder.md`

## Methodology Overview

Kim et al. (2020) propose using a **deep autoencoder** to compress high-dimensional bag-of-words representations into low-dimensional embeddings that better capture industry relationships.

### Key Innovation

Traditional TNIC (Hoberg & Phillips 2016) uses:
- High-dimensional sparse binary vectors (vocabulary size × 1)
- Direct cosine similarity on sparse vectors
- Skewed similarity distributions

Kim et al. (2020) improve this with:
- **Dimensionality reduction**: 2000-dim → 10-dim via deep autoencoder
- **Dense representations**: 10-dim continuous embeddings
- **More normal similarity distribution** (claimed benefit)
- **Better clustering properties** via spherical k-means

---

## Pipeline Architecture

```
[Step 1] Load Noun Data
   Input: data/korean_texts/by_year/{year}/firm_word_sets_{year}.parquet
   (From existing tnic/ pipeline Phase 2: Corpus Builder)
          ↓
[Step 2] Build Vocabulary (Kim et al. Filters)
   - Exclude words in >20% of documents (too common)
   - Exclude words in <2 documents (too rare)
   - Exclude geographic terms (cities, countries)
   - Exclude firms with <20 unique words
   - Select top 2000 most frequent words
          ↓
[Step 3] Create Bag-of-Words Binary Matrix
   - For each firm: 2000-dim binary vector
   - Element = 1 if word appears, 0 otherwise
   - Sparse CSR matrix (N × 2000)
          ↓
[Step 4] Train Deep Autoencoder ⭐ TRAINING STEP
   Architecture:
     Input (2000)
       ↓ Dense(500, ReLU)
       ↓ Dense(125, ReLU)
       ↓ Dense(10, Linear)    ← LATENT CODE (10-dim)
       ↓ Dense(125, ReLU)
       ↓ Dense(500, ReLU)
       ↓ Dense(2000, Sigmoid)
     Output (2000)

   Loss: Binary Cross-Entropy
   Optimizer: Adam (lr=0.001)
   Training: 90/10 train/val split, early stopping (patience=10)
   Time: ~5-10 minutes per year on CPU
          ↓
[Step 5] Generate 10-dim Embeddings
   - Run encoder only (first half of autoencoder)
   - Extract latent code (10-dimensional dense vector per firm)
   - Output: (N_firms × 10) numpy array
          ↓
[Step 6] Compute Cosine Similarity
   - Pairwise cosine similarity on 10-dim embeddings
   - L2 normalize first
   - Output: (N_firms × N_firms) sparse matrix
          ↓
[Step 7] Spherical K-means Clustering (Optional)
   - K=300 clusters (match TNIC-300 granularity)
   - Cosine distance (directional, not Euclidean)
   - Output: Cluster assignments (0-299)
```

---

## Installation & Setup

### Dependencies

Already installed via poetry:
- `torch` (CPU version)
- `scikit-learn`
- `scipy`
- `numpy`, `pandas`

**No sentence-transformers required** (removed from this version)

### Configuration

Settings in `config/tnic_dl.yaml`:

```yaml
tnic_dl:
  autoencoder:
    architecture:
      input_dim: 2000
      encoder_hidden: [500, 125]
      latent_dim: 10              # 10-dim embeddings
      decoder_hidden: [125, 500]
      output_dim: 2000

    training:
      learning_rate: 0.001
      batch_size: 64
      epochs: 100
      early_stopping_patience: 10
      device: cpu                 # CPU-only

  vocabulary:
    top_n_words: 2000
    max_document_frequency: 0.20  # Exclude >20%
    min_words_per_document: 20    # Minimum per firm
```

---

## Usage

### Command Line Interface (Recommended)

```bash
# Run pipeline for 2010 (includes training)
python scripts/run_tnic_dl_pipeline.py --years 2010

# Run for multiple years
python scripts/run_tnic_dl_pipeline.py --years 2010 2011 2012

# Skip training (load existing model)
python scripts/run_tnic_dl_pipeline.py --years 2010 --no-train

# Run with clustering (K=300)
python scripts/run_tnic_dl_pipeline.py --years 2010 --cluster
```

### Python API

```python
from tnic_dl.pipeline import TNICDLPipeline

# Initialize pipeline
pipeline = TNICDLPipeline()

# Run for year 2010
results = pipeline.run(
    years=[2010],
    train_autoencoder=True,      # Train model (required first time)
    compute_similarity=True,
    cluster=False
)

# Check results
print(f"Firms processed: {results[2010]['n_firms']}")
print(f"Embeddings shape: {results[2010]['embeddings_shape']}")  # (N, 10)
print(f"Training epochs: {results[2010]['training_history']['epochs']}")
print(f"Final loss: {results[2010]['training_history']['best_val_loss']:.6f}")
```

### Load Saved Results

```python
# Load previously generated embeddings and similarity
results = pipeline.load_results(year=2010)

embeddings = results['embeddings']  # (N, 10) numpy array
similarity = results['similarity']  # (N, N) sparse matrix

print(f"Embeddings: {embeddings.shape}")
print(f"Similarity: {similarity.shape}")
```

### Extract TNIC Peer Groups

```python
# Get peers with similarity > 0.20
peer_df = pipeline.get_peer_groups(
    year=2010,
    threshold=0.20,
    min_peers=1,
    max_peers=None  # No limit
)

# Result: DataFrame with columns
# - stock_code: Focal firm
# - peer_stock_code: Peer firm
# - similarity: Cosine similarity score
# - year: Year

print(peer_df.head())
```

---

## Output Files

All outputs saved to `data/korean_tnic_dl/by_year/{year}/`:

### Per-Year Outputs

| File | Description | Size |
|------|-------------|------|
| `vocab_{year}.json` | Top 2000 vocabulary words | ~50 KB |
| `vocab_stats_{year}.json` | Vocabulary statistics | ~10 KB |
| `binary_matrix_{year}.npz` | Sparse bag-of-words matrix (N × 2000) | ~5-10 MB |
| `firm_info_{year}.parquet` | Firm identifiers (stock_code, year) | ~100 KB |
| `embeddings_autoencoder_{year}.npy` | **10-dim embeddings** (N × 10) | ~1 MB |
| `similarity_autoencoder_{year}.npz` | Similarity matrix (N × N, sparse) | ~10-20 MB |
| `clusters_autoencoder_{year}.csv` | Cluster assignments (if clustering) | ~100 KB |

### Model Checkpoints

| File | Description |
|------|-------------|
| `data/korean_tnic_dl/models/autoencoder_{year}.pt` | Trained autoencoder weights |
| `data/korean_tnic_dl/models/training_logs/training_log_{year}.json` | Training history |

---

## Individual Components

### 1. Vocabulary Builder

```python
from tnic_dl.data_loader import DLDataLoader
from tnic_dl.preprocessing.vocab_builder import VocabularyBuilder

# Load noun data
loader = DLDataLoader()
df_nouns = loader.load_noun_data(2010)

# Build vocabulary with Kim et al. filters
vocab_builder = VocabularyBuilder(
    top_n_words=2000,
    max_doc_freq=0.20,
    min_words_per_doc=20,
    exclude_geographic=True
)

vocabulary, stats = vocab_builder.build(df_nouns, year=2010, save=True)

print(f"Vocabulary size: {len(vocabulary)}")
print(f"Top 10 words: {vocabulary[:10]}")
print(f"Firms filtered: {stats['n_firms_after_min_words_filter']}")
```

### 2. Bag-of-Words Vectorizer

```python
from tnic_dl.preprocessing.vectorizer import BagOfWordsVectorizer

vectorizer = BagOfWordsVectorizer()
binary_matrix, firm_info = vectorizer.fit_transform(df_nouns, vocabulary)

print(f"Matrix shape: {binary_matrix.shape}")  # (N, 2000)
print(f"Sparsity: {vectorizer._compute_sparsity(binary_matrix):.2%}")
print(f"Non-zero elements: {binary_matrix.nnz:,}")
```

### 3. Deep Autoencoder Training

```python
from tnic_dl.models.autoencoder import DeepAutoencoder
from tnic_dl.models.trainer import AutoencoderTrainer

# Create model (2000→500→125→10→125→500→2000)
model = DeepAutoencoder(
    input_dim=2000,
    encoder_hidden=[500, 125],
    latent_dim=10,
    decoder_hidden=[125, 500],
    output_dim=2000
)

# Print model summary
print(model.summary())

# Train model
trainer = AutoencoderTrainer(model=model)
trained_model, history = trainer.train(
    binary_matrix,
    year=2010,
    save_best=True
)

# Check training progress
print(f"Epochs: {len(history['train_loss'])}")
print(f"Best validation loss: {min(history['val_loss']):.6f}")
print(f"Training time: {sum(history['epoch_times']):.1f} seconds")
```

### 4. Generate Embeddings

```python
# Use trained model to encode
embeddings = trainer.encode_data(binary_matrix)

print(f"Embeddings shape: {embeddings.shape}")  # (N, 10)
print(f"Sample embedding:\n{embeddings[0]}")

# Example output:
# [ 0.234, -0.567,  0.891,  0.123, -0.345,
#   0.678, -0.234,  0.456,  0.789, -0.123]
```

### 5. Similarity Computation

```python
from tnic_dl.similarity.cosine_similarity import (
    compute_cosine_similarity,
    compute_similarity_statistics
)

# Compute similarity
similarity = compute_cosine_similarity(
    embeddings,
    normalize_first=True,
    return_sparse=True
)

# Get statistics
stats = compute_similarity_statistics(similarity)
print(f"Mean similarity: {stats['mean']:.4f}")
print(f"Median similarity: {stats['median']:.4f}")
print(f"Sparsity: {stats.get('sparsity', 0):.2%}")
```

### 6. Spherical K-means Clustering

```python
from tnic_dl.similarity.spherical_kmeans import SphericalKMeans

# Cluster into 300 industries
kmeans = SphericalKMeans(n_clusters=300, random_state=42)
labels = kmeans.fit_predict(embeddings)

# Get cluster statistics
stats = kmeans.get_cluster_statistics()
print(f"Clusters: {stats['n_clusters']}")
print(f"Mean cluster size: {stats['cluster_sizes']['mean']:.1f}")
print(f"Min/Max size: {stats['cluster_sizes']['min']}/{stats['cluster_sizes']['max']}")
```

---

## Expected Results

### Training (Year 2010, ~1000 firms)

- Vocabulary: 2000 words
- Binary matrix: (1000 × 2000), ~95% sparse
- Training time: 5-10 minutes on CPU
- Training epochs: 40-60 (early stopping)
- Final validation loss: ~0.08-0.12

### Embeddings

- Shape: (N_firms × 10)
- Each firm represented by 10-dimensional dense vector
- Values typically in range [-2, 2]

### Similarity Distribution

Kim et al. (2020) claim the autoencoder produces a **more normal distribution** of similarities compared to raw bag-of-words:

- Raw BOW: Heavily skewed toward 0 (most firms dissimilar)
- Autoencoder: More bell-shaped, centered around mean

**Hypothesis**: This improves clustering and peer group quality

---

## Comparison with Traditional TNIC

| Aspect | Traditional TNIC (tnic/) | Deep Autoencoder (tnic_dl/) |
|--------|-------------------------|---------------------------|
| **Dimensionality** | Full vocabulary (~5000-10000) | 10 dimensions |
| **Representation** | Sparse binary vectors | Dense continuous vectors |
| **Similarity distribution** | Heavily skewed | More normal (claimed) |
| **Computational cost** | Low (direct cosine) | Medium (training required) |
| **Training** | None | ~5-10 min per year |
| **Methodology** | Hoberg & Phillips (2016) | Kim et al. (2020) |

---

## Troubleshooting

### "Noun data not found for year X"

**Cause**: Traditional TNIC pipeline not run yet

**Solution**: Run Phase 2 (Corpus Builder) first:
```bash
python -m tnic.pipeline --start-from-phase corpus_builder --years 2010
```

### Training is slow

**Normal**: 5-10 minutes per year on CPU is expected

**To speed up**:
- Reduce `epochs` in config (e.g., 50 instead of 100)
- Increase `batch_size` (e.g., 128 instead of 64)
- Reduce `early_stopping_patience` (e.g., 5 instead of 10)

### Memory issues

**Solutions**:
- Process years one at a time
- Reduce `batch_size` in config
- Ensure `save_sparse=True` for similarity matrices

---

## Next Steps

1. **Run pilot (2010)**:
   ```bash
   python scripts/run_tnic_dl_pipeline.py --years 2010
   ```

2. **Validate outputs**:
   - Check embeddings shape: (N, 10)
   - Verify training converged (loss decreased)
   - Inspect similarity distributions

3. **Compare with traditional TNIC**:
   - Load both similarity matrices
   - Compare peer group overlap
   - Analyze similarity distributions

4. **Scale to full dataset**:
   ```bash
   python scripts/run_tnic_dl_pipeline.py --years 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025
   ```

5. **Event study analysis**:
   - Use DL-based peer groups in Figure 1 replication
   - Compare momentum effects: Traditional TNIC vs Deep Autoencoder TNIC

---

## References

**Kim et al. (2020)**: "An artificial intelligence-enabled industry classification and its interpretation"
- Deep autoencoder architecture: 2000 → 500 → 125 → 10
- Binary cross-entropy loss
- Spherical k-means clustering (K=300)
- Claim: More normal similarity distribution

**Hoberg & Phillips (2016)**: "Text-based network industries and endogenous product differentiation"
- Original TNIC methodology
- High-dimensional bag-of-words approach

**Hoberg & Phillips (2018)**: "Text-based industry momentum"
- Event study methodology (Figure 1 replication)
- Peer return shocks and turnover dynamics

---

## Files Modified/Created

This module creates:
- `tnic_dl/` - Main module directory (10 Python files)
- `config/tnic_dl.yaml` - Configuration
- `scripts/run_tnic_dl_pipeline.py` - CLI runner
- `data/korean_tnic_dl/` - Output directory

**No changes to existing `tnic/` module** - operates independently
