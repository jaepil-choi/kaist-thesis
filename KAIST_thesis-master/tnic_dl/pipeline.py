"""
Main Pipeline for TNIC-DL.

Implements the Kim et al. (2020) deep autoencoder methodology:
1. Load noun data (from existing tnic/ pipeline)
2. Build vocabulary (top 2000 words with Kim et al. filters)
3. Create bag-of-words binary matrix (N × 2000)
4. Train deep autoencoder (2000 → 500 → 125 → 10 → 125 → 500 → 2000)
5. Generate 10-dimensional embeddings
6. Compute cosine similarity
7. (Optional) Spherical k-means clustering (K=300)
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix

from tnic_dl.config import get_output_path, get_config
from tnic_dl.data_loader import DLDataLoader
from tnic_dl.preprocessing.vocab_builder import VocabularyBuilder
from tnic_dl.preprocessing.vectorizer import BagOfWordsVectorizer
from tnic_dl.models.autoencoder import DeepAutoencoder
from tnic_dl.models.trainer import AutoencoderTrainer
from tnic_dl.similarity.cosine_similarity import compute_cosine_similarity, compute_similarity_statistics
from tnic_dl.similarity.spherical_kmeans import SphericalKMeans
from tnic_dl.utils import (
    setup_logger,
    save_embeddings,
    load_embeddings,
    save_similarity_matrix,
    load_similarity_matrix,
    save_json,
)

logger = setup_logger(__name__)


class TNICDLPipeline:
    """
    Main pipeline for Deep Learning-based TNIC using Kim et al. (2020) methodology.

    Pipeline Steps:
    1. Load noun data from existing tnic/ pipeline output
    2. Build vocabulary (top 2000 words, Kim et al. filters)
    3. Create bag-of-words binary matrix
    4. Train deep autoencoder
    5. Generate 10-dim embeddings
    6. Compute cosine similarity
    7. (Optional) Spherical k-means clustering
    """

    def __init__(self):
        """Initialize the pipeline."""
        self.data_loader = DLDataLoader()
        self.logger = logger

    def run(
        self,
        years: List[int],
        train_autoencoder: bool = True,
        compute_similarity: bool = True,
        cluster: bool = False,
    ) -> Dict[int, Dict[str, Any]]:
        """
        Run the Kim et al. (2020) autoencoder pipeline.

        Args:
            years: List of years to process
            train_autoencoder: Whether to train autoencoder (or load existing model)
            compute_similarity: Whether to compute similarity matrix
            cluster: Whether to perform spherical k-means clustering

        Returns:
            Dictionary mapping year → results
        """
        self.logger.info("=" * 80)
        self.logger.info("KIM ET AL. (2020) DEEP AUTOENCODER PIPELINE")
        self.logger.info("=" * 80)
        self.logger.info(f"Years to process: {years}")
        self.logger.info(f"Train autoencoder: {train_autoencoder}")
        self.logger.info(f"Compute similarity: {compute_similarity}")
        self.logger.info(f"Clustering: {cluster}")
        self.logger.info("=" * 80)

        results = {}

        for year in years:
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"Processing year: {year}")
            self.logger.info(f"{'='*80}\n")

            try:
                year_results = self._run_year(
                    year,
                    train=train_autoencoder,
                    compute_sim=compute_similarity,
                    cluster=cluster,
                )
                results[year] = year_results

            except Exception as e:
                self.logger.error(f"Error processing year {year}: {e}", exc_info=True)
                results[year] = {'error': str(e)}

        self.logger.info("\n" + "=" * 80)
        self.logger.info("PIPELINE COMPLETED")
        self.logger.info("=" * 80)

        return results

    def _run_year(
        self,
        year: int,
        train: bool,
        compute_sim: bool,
        cluster: bool,
    ) -> Dict[str, Any]:
        """Run pipeline for a single year."""
        results = {'year': year, 'method': 'deep_autoencoder', 'reference': 'Kim et al. (2020)'}

        # Step 1: Load noun data
        self.logger.info(f"[1/7] Loading noun data for {year}")
        df_nouns = self.data_loader.load_noun_data(year)
        results['n_firms'] = len(df_nouns)
        self.logger.info(f"  Loaded {len(df_nouns)} firms")

        # Step 2: Build vocabulary
        self.logger.info(f"[2/7] Building vocabulary (top 2000 words, Kim et al. filters)")
        vocab_builder = VocabularyBuilder()
        vocabulary, vocab_stats = vocab_builder.build(df_nouns, year, save=True)
        results['vocabulary_size'] = len(vocabulary)
        results['vocab_stats'] = vocab_stats
        self.logger.info(f"  Vocabulary size: {len(vocabulary)} words")
        self.logger.info(f"  Firms after filtering: {vocab_stats['n_firms_after_min_words_filter']}")

        # Step 3: Create bag-of-words binary matrix
        self.logger.info(f"[3/7] Creating bag-of-words binary matrix (N × 2000)")
        vectorizer = BagOfWordsVectorizer()
        binary_matrix, firm_info = vectorizer.fit_transform(df_nouns, vocabulary)
        vectorizer.save(year, binary_matrix, firm_info, vocabulary)

        results['binary_matrix_shape'] = binary_matrix.shape
        results['binary_matrix_sparsity'] = vectorizer._compute_sparsity(binary_matrix)
        self.logger.info(f"  Matrix shape: {binary_matrix.shape}")
        self.logger.info(f"  Sparsity: {results['binary_matrix_sparsity']:.2%}")

        # Step 4: Train or load autoencoder
        if train:
            self.logger.info(f"[4/7] Training deep autoencoder (2000→500→125→10→125→500→2000)")
            self.logger.info(f"  This may take 5-10 minutes on CPU...")
            trainer = AutoencoderTrainer()
            model, history = trainer.train(binary_matrix, year=year, save_best=True)
            results['training_history'] = {
                'final_train_loss': history['train_loss'][-1],
                'final_val_loss': history['val_loss'][-1],
                'best_val_loss': min(history['val_loss']),
                'epochs': len(history['train_loss']),
                'total_time': sum(history['epoch_times']),
            }
            self.logger.info(f"  Training completed in {len(history['train_loss'])} epochs")
            self.logger.info(f"  Final validation loss: {min(history['val_loss']):.6f}")
            self.logger.info(f"  Total training time: {sum(history['epoch_times']):.1f} seconds")
        else:
            self.logger.info(f"[4/7] Loading pre-trained autoencoder")
            model, checkpoint = AutoencoderTrainer.load_model(year)
            trainer = AutoencoderTrainer(model=model)
            results['model_loaded'] = True
            self.logger.info(f"  Model loaded successfully")

        # Step 5: Generate 10-dim embeddings
        self.logger.info(f"[5/7] Generating 10-dimensional embeddings")
        embeddings = trainer.encode_data(binary_matrix)

        # Save embeddings
        embeddings_path = get_output_path(year, f"embeddings_autoencoder_{year}.npy")
        save_embeddings(embeddings, embeddings_path, metadata={
            'year': year,
            'method': 'deep_autoencoder',
            'reference': 'Kim et al. (2020)',
            'shape': embeddings.shape,
            'latent_dim': 10,
            'vocabulary_size': len(vocabulary),
        })
        results['embeddings_shape'] = embeddings.shape
        results['embeddings_path'] = str(embeddings_path)
        self.logger.info(f"  Embeddings shape: {embeddings.shape}")
        self.logger.info(f"  Saved to: {embeddings_path}")

        # Step 6: Compute similarity
        if compute_sim:
            self.logger.info(f"[6/7] Computing pairwise cosine similarity")
            similarity = compute_cosine_similarity(
                embeddings,
                normalize_first=True,
                return_sparse=True
            )

            # Save similarity matrix
            similarity_path = get_output_path(year, f"similarity_autoencoder_{year}.npz")
            sim_stats = compute_similarity_statistics(similarity)
            save_similarity_matrix(similarity, similarity_path, metadata={
                'year': year,
                'method': 'deep_autoencoder',
                'reference': 'Kim et al. (2020)',
                'statistics': sim_stats,
            })
            results['similarity_shape'] = similarity.shape
            results['similarity_stats'] = sim_stats
            results['similarity_path'] = str(similarity_path)
            self.logger.info(f"  Similarity matrix shape: {similarity.shape}")
            self.logger.info(f"  Mean similarity: {sim_stats['mean']:.4f}")
            self.logger.info(f"  Sparsity: {sim_stats.get('sparsity', 0):.2%}")
            self.logger.info(f"  Saved to: {similarity_path}")
        else:
            self.logger.info(f"[6/7] Skipping similarity computation")
            similarity = None

        # Step 7: Clustering (optional)
        if cluster and similarity is not None:
            config = get_config()
            n_clusters = config.clustering.n_clusters
            self.logger.info(f"[7/7] Performing spherical k-means clustering (K={n_clusters})")
            kmeans = SphericalKMeans()  # Will load n_clusters from config
            labels = kmeans.fit_predict(embeddings)

            # Save cluster assignments
            cluster_df = firm_info.copy()
            cluster_df['cluster'] = labels
            cluster_path = get_output_path(year, f"clusters_autoencoder_{year}.csv")
            cluster_df.to_csv(cluster_path, index=False)

            cluster_stats = kmeans.get_cluster_statistics()
            results['clustering'] = cluster_stats
            results['cluster_path'] = str(cluster_path)
            self.logger.info(f"  Clusters: {cluster_stats['n_clusters']}")
            self.logger.info(f"  Mean cluster size: {cluster_stats['cluster_sizes']['mean']:.1f}")
            self.logger.info(f"  Saved to: {cluster_path}")
        else:
            self.logger.info(f"[7/7] Skipping clustering")

        return results

    def load_results(self, year: int) -> Dict[str, Any]:
        """
        Load saved results for a year.

        Args:
            year: Year to load

        Returns:
            Dictionary with loaded embeddings and similarity matrix
        """
        results = {'year': year}

        # Load embeddings
        embeddings_path = get_output_path(year, f"embeddings_autoencoder_{year}.npy", create_dir=False)
        if embeddings_path.exists():
            embeddings, metadata = load_embeddings(embeddings_path, return_metadata=True)
            results['embeddings'] = embeddings
            results['embeddings_metadata'] = metadata
            self.logger.info(f"Loaded embeddings: {embeddings.shape}")
        else:
            self.logger.warning(f"Embeddings not found for year {year}")

        # Load similarity matrix
        similarity_path = get_output_path(year, f"similarity_autoencoder_{year}.npz", create_dir=False)
        if similarity_path.exists():
            similarity, metadata = load_similarity_matrix(similarity_path, return_metadata=True)
            results['similarity'] = similarity
            results['similarity_metadata'] = metadata
            self.logger.info(f"Loaded similarity matrix: {similarity.shape}")
        else:
            self.logger.warning(f"Similarity matrix not found for year {year}")

        return results

    def get_peer_groups(
        self,
        year: int,
        threshold: float = 0.20,
        min_peers: int = 1,
        max_peers: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Extract TNIC peer groups from similarity matrix.

        Args:
            year: Year to extract peers for
            threshold: Minimum similarity threshold (default 0.20)
            min_peers: Minimum number of peers required
            max_peers: Maximum number of peers (None = no limit)

        Returns:
            DataFrame with columns: stock_code, year, peer_stock_code, similarity
        """
        from tnic_dl.similarity.cosine_similarity import get_similar_above_threshold

        self.logger.info(f"Extracting peer groups for {year} (threshold={threshold})")

        # Load similarity matrix and firm info
        similarity_path = get_output_path(year, f"similarity_autoencoder_{year}.npz", create_dir=False)
        firm_info_path = get_output_path(year, f"firm_info_{year}.parquet", create_dir=False)

        similarity = load_similarity_matrix(similarity_path)
        firm_info = pd.read_parquet(firm_info_path)

        # Get peers above threshold
        peers_dict = get_similar_above_threshold(similarity, threshold, exclude_self=True)

        # Convert to DataFrame
        peer_records = []
        for firm_idx, peers in peers_dict.items():
            stock_code = firm_info.iloc[firm_idx]['stock_code']

            # Filter by min/max peers
            if len(peers) < min_peers:
                continue

            if max_peers is not None and len(peers) > max_peers:
                # Keep top-k by similarity
                peers = sorted(peers, key=lambda x: x[1], reverse=True)[:max_peers]

            for peer_idx, sim_score in peers:
                peer_stock_code = firm_info.iloc[peer_idx]['stock_code']
                peer_records.append({
                    'stock_code': stock_code,
                    'year': year,
                    'peer_stock_code': peer_stock_code,
                    'similarity': sim_score,
                })

        peer_df = pd.DataFrame(peer_records)
        self.logger.info(f"  Total peer relationships: {len(peer_df)}")
        self.logger.info(f"  Firms with peers: {peer_df['stock_code'].nunique()}")

        return peer_df
