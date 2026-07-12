"""
TNIC Peer Group Builder

Implements peer group definition following Hoberg & Phillips (2016) with:
- Load median-adjusted similarity matrices from similarity.py
- Threshold calibration on adjusted scores to match baseline industry classification
- Peer group extraction using calibrated threshold
- Comparison with baseline (FnGuide Industry)

Architecture:
    similarity.py → median-adjusted similarities (final scores) → peer_groups.py → peer definitions

Note: Median adjustment is performed by similarity.py (H&P 2016, p. 1436), NOT by this module.
This module works with "final scores" that are already median-adjusted.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from tnic.config import get_config
from tnic.data_loader import ParquetLoader
from tnic.utils import ensure_dir, setup_logger


class PeerGroupBuilder:
    """
    Build TNIC peer groups using median-adjusted similarities from similarity.py.

    Following H&P (2016), this class:
    1. Loads median-adjusted similarity matrices (final scores) from similarity.py
    2. Calibrates threshold on adjusted scores to match baseline membership fraction
    3. Defines peer groups as firms with adjusted_score(i,j) > threshold
    4. Compares with baseline classification (FnGuide Industry)

    Note: Median adjustment happens in similarity.py, not here. This class operates
    on "final scores" (median-adjusted similarities) only.

    Attributes:
        config: TNIC configuration
        loader: Parquet data loader
        logger: Logger instance
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize peer group builder.

        Args:
            config_path: Path to config directory (default: uses default config)

        Examples:
            >>> builder = PeerGroupBuilder()
            >>> peers_df, comparison_df, metadata = builder.build_peer_groups(2010)
        """
        # Load configuration
        if config_path is None:
            self.config = get_config()
        else:
            from tnic.config import TNICConfig
            self.config = TNICConfig(config_dir=config_path)

        # Initialize components
        self.loader = ParquetLoader(config_path=config_path)
        self.logger = setup_logger(__name__)

        # Get baseline classification
        self.baseline = self.config.get("hp.peer_groups.calibration_baseline", "fnguide_industry")

        self.logger.info("Peer group builder initialized")
        self.logger.info(f"  Baseline: {self.baseline}")

    def build_peer_groups(
        self,
        year: int,
        M_adjusted: Optional[np.ndarray] = None,
        save_output: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Build TNIC peer groups for a specific year.

        Args:
            year: Year to process
            M_adjusted: Median-adjusted similarity matrix (if None, loads from file)
                       Note: Matrix should already be adjusted by similarity.py
            save_output: Whether to save outputs to disk

        Returns:
            Tuple of (peers_df, comparison_df, metadata):
                - peers_df: Peer relationships
                - comparison_df: Comparison with FnGuide
                - metadata: Statistics and parameters

        Examples:
            >>> builder = PeerGroupBuilder()
            >>> peers, comp, meta = builder.build_peer_groups(2010)
        """
        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"BUILDING TNIC PEER GROUPS FOR {year}")
        self.logger.info(f"{'=' * 80}")

        # Load similarity matrix (already median-adjusted by similarity.py)
        if M_adjusted is None:
            M_adjusted, firms_df, median_stats = self._load_similarity_matrix(year)
        else:
            firms_df = self._load_firm_mapping(year)
            median_stats = None

        # Load FnGuide baseline
        matched_df, target_stats = self._load_fnguide_baseline(year, firms_df)

        # Calibrate threshold on adjusted scores to match baseline membership fraction
        # (H&P 2016: calibrate to match SIC-3; we match FnGuide Industry)
        target_fraction = target_stats['fraction']
        threshold, _ = self._calibrate_threshold(M_adjusted, target_fraction)

        # Extract ALL peer pairs with comprehensive metadata
        # Includes: FnGuide classifications, similarity scores, membership fraction
        peers_df, peers_per_firm = self._extract_peer_groups(
            M_adjusted, threshold, firms_df, matched_df, target_fraction, year
        )

        # Compare with FnGuide
        comparison_df = self._compare_with_baseline(
            peers_per_firm, matched_df, firms_df
        )

        # Build metadata (use median stats from similarity.py)
        metadata = self._build_metadata(
            year, threshold, target_fraction, target_stats,
            median_stats, peers_df, peers_per_firm, comparison_df
        )

        # Save outputs
        if save_output:
            self._save_outputs(year, peers_df, comparison_df, metadata)

        return peers_df, comparison_df, metadata

    def _load_similarity_matrix(self, year: int) -> Tuple[np.ndarray, pd.DataFrame, Optional[Dict]]:
        """
        Load median-adjusted similarity matrix and firm mapping.

        Note: Matrix is already median-adjusted by similarity.py (H&P 2016, p. 1436).
        This method also loads the median adjustment statistics for metadata.
        """
        self.logger.info(f"Loading similarity matrix for {year}...")

        # Load matrix (already median-adjusted by similarity.py)
        base_dir = self.config.get("paths.outputs.similarity.base_dir")
        if base_dir is None:
            raise ValueError("Similarity directory not configured")

        matrix_path = Path(base_dir) / f"similarity_matrix_{year}.npz"

        if not matrix_path.exists():
            raise FileNotFoundError(
                f"Similarity matrix not found: {matrix_path}\n"
                f"Please run similarity computation for year {year} first."
            )

        data = np.load(matrix_path)
        M_adjusted = data['similarity_matrix']

        # Load firm mapping
        firms_path = Path(base_dir) / f"similarity_firms_{year}.csv"
        firms_df = pd.read_parquet(firms_path) if firms_path.suffix == '.parquet' else pd.read_csv(firms_path)
        firms_df['stock_code'] = firms_df['stock_code'].astype(str).str.zfill(6)

        self.logger.info(f"  Matrix shape: {M_adjusted.shape}")
        self.logger.info(f"  Firms: {len(firms_df)}")

        # Mean adjusted similarity (upper triangle, excluding diagonal)
        triu_indices = np.triu_indices_from(M_adjusted, k=1)
        mean_sim = M_adjusted[triu_indices].mean()
        self.logger.info(f"  Mean adjusted similarity: {mean_sim:.4f}")

        # Load median adjustment statistics from similarity.py
        import json
        metadata_path = Path(base_dir) / "similarity_matrices_metadata.json"
        median_stats = None

        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    similarity_metadata = json.load(f)

                year_meta = similarity_metadata.get(str(year), {})
                median_stats = year_meta.get('median_adjustment', None)

                if median_stats:
                    self.logger.info(f"  Median adjustment stats (from similarity.py):")
                    self.logger.info(f"    Mean median: {median_stats['mean_median']:.6f}")
                    self.logger.info(f"    Std median: {median_stats['std_median']:.6f}")
                else:
                    self.logger.warning(f"  No median adjustment stats found for {year}")
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"  Could not load median stats: {e}")
        else:
            self.logger.warning(f"  Similarity metadata not found: {metadata_path}")

        return M_adjusted, firms_df, median_stats

    def _load_firm_mapping(self, year: int) -> pd.DataFrame:
        """Load firm identifier mapping."""
        base_dir = self.config.get("paths.outputs.corpus.base_dir")
        year_dir = Path(str(base_dir).format(year=year))
        firms_path = year_dir / f"firm_word_sets_{year}.parquet"

        firms_df = pd.read_parquet(firms_path)
        firms_df['stock_code'] = firms_df['stock_code'].astype(str).str.zfill(6)

        return firms_df

    def _load_fnguide_baseline(
        self,
        year: int,
        firms_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict]:
        """Load FnGuide Industry classifications and calculate target fraction."""
        self.logger.info(f"Loading FnGuide baseline for {year}...")

        # Load FnGuide data
        fnguide_df = self.loader.load_fnguide_data("dataguide")

        # Filter for latest available date in target year
        fnguide_df['date'] = pd.to_datetime(fnguide_df['date'])
        fnguide_df['year'] = fnguide_df['date'].dt.year
        df_year_all = fnguide_df[fnguide_df['year'] == year].copy()

        if len(df_year_all) > 0:
            latest_date = df_year_all['date'].max()
            df_year = df_year_all[df_year_all['date'] == latest_date].copy()
            self.logger.info(f"  Using FnGuide data from: {latest_date.strftime('%Y-%m-%d')}")
        else:
            self.logger.error(f"  No FnGuide data available for year {year}")
            raise ValueError(f"No FnGuide data available for year {year}")

        # Clean stock codes
        df_year['stock_code'] = df_year['symbol'].str.replace('A', '', regex=False)
        df_year = df_year.drop_duplicates(subset=['stock_code'], keep='first')

        # Match with TNIC firms
        matched = firms_df.merge(
            df_year[['stock_code', 'FnGuide Industry', 'symbol_name']],
            on='stock_code',
            how='inner'
        )

        self.logger.info(f"  FnGuide firms: {len(df_year)}")
        self.logger.info(f"  Matched: {len(matched)}/{len(firms_df)} ({len(matched)/len(firms_df)*100:.1f}%)")

        # Calculate membership fraction
        target_stats = self._calculate_membership_fraction(matched, 'FnGuide Industry')

        self.logger.info(f"  Industry groups: {target_stats['num_groups']}")
        self.logger.info(f"  Target membership fraction: {target_stats['fraction_pct']:.4f}%")

        return matched, target_stats

    def _calculate_membership_fraction(
        self,
        df: pd.DataFrame,
        industry_col: str = 'FnGuide Industry'
    ) -> Dict:
        """Calculate membership pairs fraction for baseline classification."""
        df_clean = df[df[industry_col].notna()].copy()
        N = len(df_clean)

        if N == 0:
            raise ValueError(f"No valid {industry_col} data")

        total_possible_pairs = N * (N - 1) / 2
        industry_counts = df_clean[industry_col].value_counts()

        total_membership_pairs = 0
        for M_i in industry_counts:
            pairs_in_group = M_i * (M_i - 1) / 2
            total_membership_pairs += pairs_in_group

        fraction = total_membership_pairs / total_possible_pairs

        return {
            'N': int(N),
            'num_groups': len(industry_counts),
            'total_membership_pairs': int(total_membership_pairs),
            'total_possible_pairs': int(total_possible_pairs),
            'fraction': float(fraction),
            'fraction_pct': float(fraction * 100)
        }

    def _calibrate_threshold(
        self,
        M_adjusted: np.ndarray,
        target_fraction: float
    ) -> Tuple[float, List[Dict]]:
        """
        Calibrate threshold on adjusted scores to match target membership fraction.

        Note: This operates on median-adjusted "final scores" from similarity.py,
        not raw similarities. H&P (2016, p. 1436) calibrates threshold after
        median adjustment.

        Args:
            M_adjusted: Median-adjusted similarity matrix (final scores)
            target_fraction: Target membership pairs fraction

        Returns:
            Tuple of (best_threshold, calibration_results)
        """
        self.logger.info(f"Calibrating threshold...")
        self.logger.info(f"  Target fraction: {target_fraction*100:.4f}%")

        # Get threshold range from config
        thresh_range = self.config.get("hp.peer_groups.threshold_search_range", [0.10, 0.30])
        thresh_step = self.config.get("hp.peer_groups.threshold_step", 0.005)

        thresholds = np.arange(thresh_range[0], thresh_range[1], thresh_step)

        N = M_adjusted.shape[0]
        total_possible_pairs = N * (N - 1) / 2

        # Get upper triangle (excluding diagonal)
        triu_indices = np.triu_indices_from(M_adjusted, k=1)
        similarities = M_adjusted[triu_indices]

        results = []
        for threshold in thresholds:
            n_pairs = np.sum(similarities > threshold)
            fraction = n_pairs / total_possible_pairs
            diff = abs(fraction - target_fraction)
            results.append({
                'threshold': float(threshold),
                'n_pairs': int(n_pairs),
                'fraction': float(fraction),
                'fraction_pct': float(fraction * 100),
                'diff': float(diff)
            })

        # Find best threshold
        best = min(results, key=lambda x: x['diff'])

        self.logger.info(f"  Best threshold: {best['threshold']:.4f}")
        self.logger.info(f"  Achieves fraction: {best['fraction_pct']:.4f}%")
        self.logger.info(f"  Difference: {(best['fraction'] - target_fraction)*100:+.4f}%")

        return best['threshold'], results


    def _extract_peer_groups(
        self,
        M_adjusted: np.ndarray,
        threshold: float,
        firms_df: pd.DataFrame,
        matched_df: pd.DataFrame,
        fn_membership_fraction: float,
        year: int
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Extract ALL firm pairs with comprehensive TNIC and FnGuide metadata.

        Output format includes:
        - Year identifier
        - All firm pairs (not just TNIC peers above threshold)
        - Similarity scores and calibrated threshold
        - TNIC peer classification (is_same_tnic: similarity > threshold)
        - TNIC membership fraction (fraction of pairs above threshold)
        - FnGuide industry classifications for both firms
        - FnGuide membership fraction (constant for the year)
        - Boolean flags for same FnGuide group

        Args:
            M_adjusted: Median-adjusted similarity matrix
            threshold: Calibrated threshold for TNIC peer definition
            firms_df: Firm identifier mapping
            matched_df: FnGuide data with industry classifications
            fn_membership_fraction: FnGuide membership fraction for this year
            year: Year identifier for this data

        Returns:
            Tuple of (all_pairs_df, peers_per_firm):
                - all_pairs_df: DataFrame with ALL pairs and complete metadata
                - peers_per_firm: Dict mapping firm index to list of TNIC peer indices
        """
        self.logger.info(f"Extracting all firm pairs with metadata...")
        self.logger.info(f"  Calibrated threshold: {threshold:.4f}")

        N = M_adjusted.shape[0]
        pairs_list = []
        peers_per_firm = {}

        # Calculate TNIC membership fraction ONCE (constant for this year)
        triu_indices = np.triu_indices_from(M_adjusted, k=1)
        n_tnic_pairs = np.sum(M_adjusted[triu_indices] > threshold)
        total_possible_pairs = N * (N - 1) / 2
        tnic_membership_fraction = n_tnic_pairs / total_possible_pairs

        # Create mapping from stock_code to FnGuide industry
        fnguide_map = dict(zip(matched_df['stock_code'], matched_df['FnGuide Industry']))

        # Generate ALL pairs (i < j to avoid duplicates)
        for i in range(N):
            peers_i = []  # Will store TNIC peers for statistics

            for j in range(i + 1, N):
                # Get stock codes
                stock_code_i = firms_df.iloc[i]['stock_code']
                stock_code_j = firms_df.iloc[j]['stock_code']

                # Get similarity
                similarity = M_adjusted[i, j]

                # Get FnGuide industries (if available)
                fngroup_i = fnguide_map.get(stock_code_i, None)
                fngroup_j = fnguide_map.get(stock_code_j, None)

                # Determine if same FnGuide group
                if fngroup_i is not None and fngroup_j is not None:
                    is_same_fngroup = (fngroup_i == fngroup_j)
                else:
                    is_same_fngroup = None

                # Track TNIC peers for statistics (bidirectional)
                if similarity > threshold:
                    peers_i.append(j)

                # Add pair to output
                pairs_list.append({
                    'year': year,
                    'firm_i': i,
                    'firm_j': j,
                    'stock_code_i': stock_code_i,
                    'stock_code_j': stock_code_j,
                    'similarity': float(similarity),
                    'threshold': float(threshold),
                    'is_same_tnic': bool(similarity > threshold),
                    'tnic_membership_fraction': float(tnic_membership_fraction),
                    'fn_membership_fraction': float(fn_membership_fraction),
                    'fngroup_i': fngroup_i,
                    'fngroup_j': fngroup_j,
                    'is_same_fngroup': is_same_fngroup,
                })

            # Store TNIC peers for this firm (for statistics)
            peers_per_firm[i] = peers_i

        # Also need to add reverse direction for TNIC peer counts
        # (since we only loop i < j, but peers are bidirectional)
        for i in range(N):
            for j in range(i):
                if M_adjusted[i, j] > threshold:
                    if i not in peers_per_firm:
                        peers_per_firm[i] = []
                    peers_per_firm[i].append(j)

        all_pairs_df = pd.DataFrame(pairs_list)

        # Statistics (based on TNIC threshold)
        n_peers = [len(peers_per_firm.get(i, [])) for i in range(N)]
        n_tnic_relationships = sum(1 for row in pairs_list if row['similarity'] > threshold)

        self.logger.info(f"  Total pairs: {len(pairs_list):,}")
        self.logger.info(f"  TNIC peer relationships (similarity > {threshold:.4f}): {n_tnic_relationships:,}")
        self.logger.info(f"  TNIC peers per firm: mean={np.mean(n_peers):.1f}, median={np.median(n_peers):.1f}")

        return all_pairs_df, peers_per_firm

    def _compare_with_baseline(
        self,
        peers_per_firm: Dict,
        matched_df: pd.DataFrame,
        firms_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Compare TNIC peer groups with FnGuide Industry baseline."""
        self.logger.info("Comparing with FnGuide baseline...")

        # Create mapping
        stock_to_idx = {row['stock_code']: idx for idx, row in firms_df.iterrows()}

        comparisons = []

        for _, row in matched_df.iterrows():
            stock_code = row['stock_code']
            fnguide_industry = row['FnGuide Industry']

            if stock_code not in stock_to_idx:
                continue

            firm_idx = stock_to_idx[stock_code]

            # TNIC peers
            tnic_peers = set(peers_per_firm.get(firm_idx, []))

            # FnGuide peers
            fnguide_peers_stocks = matched_df[
                (matched_df['FnGuide Industry'] == fnguide_industry) &
                (matched_df['stock_code'] != stock_code)
            ]['stock_code'].tolist()

            fnguide_peers = set([stock_to_idx[s] for s in fnguide_peers_stocks if s in stock_to_idx])

            # Overlap
            both = tnic_peers & fnguide_peers
            tnic_only = tnic_peers - fnguide_peers
            fnguide_only = fnguide_peers - tnic_peers

            comparisons.append({
                'stock_code': stock_code,
                'fnguide_industry': fnguide_industry,
                'n_tnic_peers': len(tnic_peers),
                'n_fnguide_peers': len(fnguide_peers),
                'n_both': len(both),
                'n_tnic_only': len(tnic_only),
                'n_fnguide_only': len(fnguide_only),
                'overlap_pct': len(both) / len(tnic_peers) * 100 if len(tnic_peers) > 0 else 0
            })

        comparison_df = pd.DataFrame(comparisons)

        self.logger.info(f"  Firms analyzed: {len(comparison_df)}")
        self.logger.info(f"  Avg TNIC peers: {comparison_df['n_tnic_peers'].mean():.1f}")
        self.logger.info(f"  Avg FnGuide peers: {comparison_df['n_fnguide_peers'].mean():.1f}")
        self.logger.info(f"  Avg overlap: {comparison_df['overlap_pct'].mean():.1f}%")

        return comparison_df

    def _build_metadata(
        self,
        year: int,
        threshold: float,
        target_fraction: float,
        target_stats: Dict,
        median_stats: Optional[Dict],
        peers_df: pd.DataFrame,
        peers_per_firm: Dict,
        comparison_df: pd.DataFrame
    ) -> Dict:
        """
        Build metadata dictionary.

        Note: Uses median adjustment statistics from similarity.py (not computed locally).
        This ensures consistency and avoids re-computing median stats on already-adjusted matrix.

        Args:
            year: Year
            threshold: Calibrated threshold
            target_fraction: Target membership fraction
            target_stats: Baseline statistics
            median_stats: Median adjustment statistics from similarity.py (can be None)
            peers_df: All pairs dataframe (not just TNIC peers)
            peers_per_firm: Peer indices per firm (TNIC peers only)
            comparison_df: Comparison with baseline

        Returns:
            Metadata dictionary
        """
        n_peers = [len(peers) for peers in peers_per_firm.values()]

        # Count TNIC peer relationships (similarity > threshold)
        # Note: peers_df now contains ALL pairs, so we need to filter
        n_tnic_relationships = len(peers_df[peers_df['similarity'] > threshold])

        metadata = {
            'year': year,
            'N_firms': len(peers_per_firm),
            'threshold_calibrated': float(threshold),
            'target_fraction_pct': float(target_fraction * 100),
            'fnguide_stats': target_stats,
            'tnic_stats': {
                'n_total_pairs': len(peers_df),  # All possible pairs
                'n_peer_relationships': n_tnic_relationships,  # TNIC peers (similarity > threshold)
                'avg_peers_per_firm': float(np.mean(n_peers)),
                'median_peers_per_firm': float(np.median(n_peers)),
                'std_peers_per_firm': float(np.std(n_peers)),
                'min_peers': int(np.min(n_peers)),
                'max_peers': int(np.max(n_peers))
            },
            'comparison': {
                'avg_tnic_peers': float(comparison_df['n_tnic_peers'].mean()),
                'avg_fnguide_peers': float(comparison_df['n_fnguide_peers'].mean()),
                'avg_both': float(comparison_df['n_both'].mean()),
                'avg_tnic_only': float(comparison_df['n_tnic_only'].mean()),
                'avg_fnguide_only': float(comparison_df['n_fnguide_only'].mean()),
                'avg_overlap_pct': float(comparison_df['overlap_pct'].mean())
            }
        }

        # Add median adjustment stats from similarity.py if available
        if median_stats is not None:
            metadata['median_adjustment'] = median_stats
        else:
            self.logger.warning("Median adjustment statistics not available from similarity.py")

        return metadata

    def _save_outputs(
        self,
        year: int,
        peers_df: pd.DataFrame,
        comparison_df: pd.DataFrame,
        metadata: Dict
    ):
        """Save peer groups and comparison data."""
        self.logger.info(f"Saving outputs for {year}...")

        # Get output directory
        base_dir = self.config.get("paths.outputs.peers.base_dir")
        if base_dir is None:
            raise ValueError("Output directory not configured")

        output_dir = Path(base_dir)
        ensure_dir(output_dir)

        # Save comprehensive all-pairs file (new format)
        all_pairs_path = output_dir / f"tnic_all_pairs_{year}.csv"
        peers_df.to_csv(all_pairs_path, index=False)
        self.logger.info(f"  Saved: {all_pairs_path}")
        self.logger.info(f"    Total pairs: {len(peers_df):,}")
        self.logger.info(f"    File size: {all_pairs_path.stat().st_size / (1024**2):.1f} MB")

        # Save comparison (backward compatibility)
        comp_path = output_dir / f"tnic_vs_fnguide_{year}.csv"
        comparison_df.to_csv(comp_path, index=False)
        self.logger.info(f"  Saved: {comp_path}")

        # Save metadata
        meta_path = output_dir / f"tnic_metadata_{year}.json"
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        self.logger.info(f"  Saved: {meta_path}")

    def _save_combined_parquet(self, all_peers_dfs: List[pd.DataFrame]):
        """Combine all years and save to single parquet file."""
        self.logger.info(f"{'=' * 80}")
        self.logger.info("Creating combined parquet file for all years...")
        self.logger.info(f"{'=' * 80}")

        # Concatenate all DataFrames
        combined_df = pd.concat(all_peers_dfs, ignore_index=True)

        # Get output directory
        base_dir = self.config.get("paths.outputs.peers.base_dir")
        if base_dir is None:
            raise ValueError("Output directory not configured")

        output_path = Path(base_dir) / "tnic_all_pairs_all_years.parquet"

        # Save to parquet
        combined_df.to_parquet(output_path, index=False)

        # Log statistics
        years = sorted(combined_df['year'].unique())
        self.logger.info(f"  Saved: {output_path}")
        self.logger.info(f"  Total rows: {len(combined_df):,}")
        self.logger.info(f"  Years: {years}")
        self.logger.info(f"  File size: {output_path.stat().st_size / (1024**2):.1f} MB")

    def build_all_peer_groups(
        self,
        years: Optional[List[int]] = None,
        mode: str = "full"
    ) -> Dict[int, Dict]:
        """Build peer groups for multiple years and create consolidated parquet."""
        if years is None:
            years = list(self.config.get_year_range(mode))

        self.logger.info(f"Building peer groups for {len(years)} years")

        all_metadata = {}
        all_peers_dfs = []  # Collect all DataFrames for combined parquet

        for year in years:
            try:
                peers_df, _, metadata = self.build_peer_groups(year, save_output=True)
                all_metadata[year] = metadata
                all_peers_dfs.append(peers_df)  # Accumulate for combined output
            except Exception as e:
                self.logger.error(f"Error processing year {year}: {e}")
                all_metadata[year] = {'status': 'failed', 'error': str(e)}

        # Create combined parquet file with all years
        if all_peers_dfs:
            self._save_combined_parquet(all_peers_dfs)

        # Summary
        successful = [y for y, m in all_metadata.items() if m.get('status') != 'failed']
        failed = [y for y, m in all_metadata.items() if m.get('status') == 'failed']

        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"PEER GROUP CONSTRUCTION COMPLETE")
        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"  Successful: {len(successful)} years")
        if failed:
            self.logger.warning(f"  Failed: {len(failed)} years: {failed}")

        return all_metadata

    def __repr__(self) -> str:
        """String representation."""
        return f"PeerGroupBuilder(baseline={self.baseline})"
