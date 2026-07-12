"""
TNIC Pipeline Orchestrator

Orchestrates the complete TNIC ETL pipeline from data extraction to peer group definition.

Pipeline Phases:
    1. Data Extraction: MongoDB → raw business descriptions
    1b. Data Cleaning: Raw descriptions → cleaned descriptions
    1.5. Universe Matching: Cleaned descriptions → filled descriptions
    2. Corpus Building: Filled descriptions → firm word sets (by year)
    3. Binary Matrices: Firm word sets → sparse binary matrices Q_t
    4. Similarity Matrices: Binary matrices → cosine similarity M_t
    5. Peer Groups: Similarity matrices + baseline → TNIC peers

Features:
    - Dependency tracking and validation
    - Progress checkpointing
    - Error recovery and resume capability
    - Configurable execution (individual phases or full pipeline)
    - Detailed logging and progress tracking
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
# import multiprocess as mp  # Disabled: using sequential processing
import sys
import traceback

import numpy as np
import pandas as pd

from tnic.binary_matrix import BinaryMatrixBuilder
from tnic.config import get_config
from tnic.corpus_builder import CorpusBuilder
from tnic.data_loader import MongoDBLoader, ParquetLoader
from tnic.peer_groups import PeerGroupBuilder
from tnic.text_cleaner import TextCleaner
from tnic.similarity import SimilarityComputer
from tnic.universe_matcher import UniverseMatcher
from tnic.utils import ensure_dir, setup_logger


# DISABLED: Multiprocessing worker function (not used in sequential mode)
# Kept for reference in case multiprocessing is re-enabled later
def _build_corpus_for_year_DISABLED(year: int, filled_descriptions_path: str, config_dict: dict) -> Dict:
    """
    Worker function to build corpus for a single year (for parallel processing).

    Args:
        year: Year to process
        filled_descriptions_path: Path to filled descriptions parquet file
        config_dict: Configuration dictionary

    Returns:
        Dictionary with corpus statistics
    """
    try:
        import os
        import sys

        # Set environment to avoid threading issues with Kiwi
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'

        print(f"Worker process {os.getpid()} starting for year {year}", flush=True)

        # OPTIMIZATION: Load only the specific year's data using filters
        # This is MUCH faster than loading all data and filtering
        print(f"  Loading data for year {year}...", flush=True)
        df = pd.read_parquet(
            filled_descriptions_path,
            filters=[('year', '=', year)]
        )
        print(f"  Loaded {len(df)} rows for year {year}", flush=True)

        # Recreate config from dict
        from tnic.config import TNICConfig
        config = TNICConfig.__new__(TNICConfig)
        config._config = config_dict
        config.hp = config_dict.get('hp', {})
        config.nlp = config_dict.get('nlp', {})
        config.paths = config_dict.get('paths', {})
        config.mongodb = config_dict.get('mongodb', {})

        # Create corpus builder (this will initialize Kiwi)
        print(f"  Initializing corpus builder for year {year}...", flush=True)
        corpus_builder = CorpusBuilder(config_path=None)
        corpus_builder.config = config
        print(f"  Corpus builder initialized for year {year}", flush=True)

        # Build corpus for this year
        print(f"  Building corpus for year {year}...", flush=True)
        _, _, stats = corpus_builder.build_year_corpus(
            year, df=df, save_outputs=True
        )

        print(f"  Completed year {year}: {stats['N_t_output']} firms, {stats['W_t']} words", flush=True)
        return stats

    except Exception as e:
        # Print full traceback for debugging
        import traceback
        import os
        print(f"ERROR in worker process {os.getpid()} for year {year}:", flush=True)
        traceback.print_exc()
        raise RuntimeError(f"Year {year} failed: {str(e)}") from e


class TNICPipeline:
    """
    End-to-end TNIC pipeline orchestrator.

    Manages execution of all pipeline phases with dependency tracking,
    checkpointing, and error recovery.

    Attributes:
        config: TNIC configuration
        logger: Logger instance
        checkpoint_path: Path to checkpoint file
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        checkpoint_file: Optional[str] = None
    ):
        """
        Initialize pipeline orchestrator.

        Args:
            config_path: Path to config directory
            checkpoint_file: Path to checkpoint file (default: auto)

        Examples:
            >>> pipeline = TNICPipeline()
            >>> pipeline.run(mode="pilot")  # Run on pilot years
            >>> pipeline.run(phase="corpus", years=[2010, 2011])  # Run specific phase
        """
        # Load configuration
        if config_path is None:
            self.config = get_config()
        else:
            from tnic.config import TNICConfig
            self.config = TNICConfig(config_dir=config_path)

        # Initialize logger
        self.logger = setup_logger(__name__)

        # Initialize components
        self.text_cleaner = TextCleaner(config_path=config_path)
        self.universe_matcher = UniverseMatcher(config_path=config_path)
        self.corpus_builder = CorpusBuilder(config_path=config_path)
        self.binary_builder = BinaryMatrixBuilder(config_path=config_path)
        self.similarity_computer = SimilarityComputer(config_path=config_path)
        self.peer_builder = PeerGroupBuilder(config_path=config_path)
        self.loader = ParquetLoader(config_path=config_path)

        # Checkpoint management
        if checkpoint_file is None:
            checkpoint_dir = Path(self.config.get("paths.directories.base", "data")) / "checkpoints"
            ensure_dir(checkpoint_dir)
            checkpoint_file = checkpoint_dir / "tnic_pipeline_checkpoint.json"

        self.checkpoint_path = Path(checkpoint_file)
        self.checkpoint = self._load_checkpoint()

        self.logger.info("TNIC Pipeline initialized")

    def run(
        self,
        phase: Optional[str] = None,
        start_from_phase: Optional[str] = None,
        years: Optional[List[int]] = None,
        mode: str = "full",
        force: bool = False,
        validate_deps: bool = True,
        max_workers: Optional[int] = None
    ) -> Dict:
        """
        Run the TNIC pipeline.

        Args:
            phase: Specific phase to run (runs only this phase)
                   Options: "extraction", "corpus", "binary", "similarity", "peers"
            start_from_phase: Phase to start from (runs this phase and all subsequent phases)
                             Cannot be used with 'phase' parameter
            years: List of years to process (None = from config)
            mode: "full" (all years) or "pilot" (pilot years only)
            force: Force re-run even if outputs exist
            validate_deps: Validate dependencies before running phases (default: True)

        Returns:
            Dictionary with execution results per phase/year

        Examples:
            >>> pipeline = TNICPipeline()
            >>> # Run full pipeline on pilot years
            >>> results = pipeline.run(mode="pilot")
            >>>
            >>> # Run only corpus building for specific years
            >>> results = pipeline.run(phase="corpus", years=[2010, 2011])
            >>>
            >>> # Start from binary matrices and run all subsequent phases
            >>> results = pipeline.run(start_from_phase="binary", mode="full")
            >>>
            >>> # Force re-run of similarity computation
            >>> results = pipeline.run(phase="similarity", force=True)
        """
        # Validate parameters
        if phase is not None and start_from_phase is not None:
            raise ValueError(
                "Cannot specify both 'phase' and 'start_from_phase'. "
                "Use 'phase' to run a single phase, or 'start_from_phase' to run from a phase onwards."
            )

        # Define phase order
        phase_order = ["extraction", "cleaning", "universe_matching", "corpus", "binary", "similarity", "peers"]

        # Determine which phases to run
        if phase is not None:
            # Run only specified phase
            phases_to_run = [phase]
            run_mode = f"SINGLE PHASE: {phase}"
        elif start_from_phase is not None:
            # Run from specified phase onwards
            if start_from_phase not in phase_order:
                raise ValueError(
                    f"Invalid start_from_phase: {start_from_phase}. "
                    f"Must be one of: {', '.join(phase_order)}"
                )
            start_idx = phase_order.index(start_from_phase)
            phases_to_run = phase_order[start_idx:]
            run_mode = f"FROM {start_from_phase.upper()} ONWARDS"
        else:
            # Run all phases
            phases_to_run = phase_order
            run_mode = "ALL PHASES"

        self.logger.info(f"{'=' * 80}")
        self.logger.info("STARTING TNIC PIPELINE")
        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"  Run mode: {run_mode}")
        self.logger.info(f"  Phases to run: {', '.join(phases_to_run)}")
        self.logger.info(f"  Year mode: {mode}")
        self.logger.info(f"  Years: {years or 'from config'}")
        self.logger.info(f"  Force re-run: {force}")
        self.logger.info(f"  Validate dependencies: {validate_deps}")

        # Get years to process
        if years is None:
            years = list(self.config.get_year_range(mode))

        self.logger.info(f"  Processing years: {min(years)} - {max(years)}")

        # Validate dependencies if requested
        if validate_deps:
            self.logger.info(f"\nValidating dependencies...")
            for phase_name in phases_to_run:
                if phase_name == "extraction":
                    continue  # Extraction has no dependencies

                # Only validate dependencies that are NOT in the execution plan
                # (dependencies that ARE in the plan will be satisfied by running them)
                validation = self.validate_dependencies(
                    phase_name, years, phases_in_execution=phases_to_run
                )
                if not validation['valid']:
                    error_msg = (
                        f"\nDependency validation failed for phase '{phase_name}':\n"
                        f"Missing prerequisites: {validation['missing']}\n"
                        f"\nPlease run the missing phases first, or set validate_deps=False to skip validation."
                    )
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)

            self.logger.info(f"  All dependencies satisfied")

        # Execute phases
        results = {}

        # Define dependencies
        dependencies = {
            'cleaning': ['extraction'],
            'universe_matching': ['cleaning'],
            'corpus': ['universe_matching'],
            'binary': ['corpus'],
            'similarity': ['binary'],
            'peers': ['similarity']
        }

        try:
            for phase_name in phases_to_run:
                # Check if dependencies succeeded (for multi-phase runs)
                should_skip = False
                if phase_name in dependencies:
                    for dep_phase in dependencies[phase_name]:
                        if dep_phase in results:
                            # Check if dependency phase had failures
                            dep_results = results[dep_phase]
                            failed_count = sum(1 for r in dep_results.values() if isinstance(r, dict) and r.get('status') == 'failed')
                            if failed_count > 0:
                                self.logger.error(f"\nSkipping {phase_name}: dependency '{dep_phase}' had {failed_count} failures")
                                results[phase_name] = {'status': 'skipped', 'reason': f'dependency {dep_phase} failed'}
                                should_skip = True
                                break

                if should_skip:
                    continue

                if phase_name == "extraction":
                    results['extraction'] = self._run_extraction(years, force)
                elif phase_name == "cleaning":
                    results['cleaning'] = self._run_cleaning(years, force)
                elif phase_name == "universe_matching":
                    results['universe_matching'] = self._run_universe_matching(years, force)
                elif phase_name == "corpus":
                    results['corpus'] = self._run_corpus(years, force, max_workers)
                elif phase_name == "binary":
                    results['binary'] = self._run_binary_matrices(years, force)
                elif phase_name == "similarity":
                    results['similarity'] = self._run_similarity(years, force)
                elif phase_name == "peers":
                    results['peers'] = self._run_peer_groups(years, force)

            # Update checkpoint
            self._save_checkpoint()

            # Summary
            self._print_summary(results)

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            self._save_checkpoint()
            raise

        return results

    def _run_extraction(self, years: List[int], force: bool) -> Dict:
        """
        Phase 1: Extract business descriptions from MongoDB.

        Extracts data year-by-year and saves separate parquet files for each year.

        Args:
            years: List of years to extract
            force: Force re-run

        Returns:
            Dictionary with extraction results
        """
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("PHASE 1: DATA EXTRACTION")
        self.logger.info(f"{'=' * 80}")

        self.logger.info(f"  Extracting years: {min(years)}-{max(years)}")
        self.logger.info(f"  Output directory: data/korean_texts/")
        self.logger.info("")

        results = {}
        total_firm_years = 0

        with MongoDBLoader() as mongo_loader:
            for year in years:
                # Check if already done
                output_path = Path(f"data/korean_texts/business_descriptions_raw_{year}.parquet")

                if output_path.exists() and not force:
                    self.logger.info(f"  {year}: [OK] Already exists, skipping")
                    # Count rows for summary
                    df_existing = pd.read_parquet(output_path)
                    results[year] = {
                        'status': 'skipped',
                        'output': str(output_path),
                        'n_firm_years': len(df_existing)
                    }
                    total_firm_years += len(df_existing)
                    continue

                # Extract this year
                self.logger.info(f"  {year}: Extracting from MongoDB...")
                try:
                    df_year = mongo_loader.extract_business_descriptions(
                        year_range=(year, year)
                    )

                    # Save
                    ensure_dir(output_path.parent)
                    df_year.to_parquet(output_path, index=False)

                    self.logger.info(f"  {year}: [OK] Extracted {len(df_year):,} documents → {output_path.name}")

                    results[year] = {
                        'status': 'success',
                        'output': str(output_path),
                        'n_firm_years': len(df_year)
                    }
                    total_firm_years += len(df_year)

                except Exception as e:
                    self.logger.error(f"  {year}: [ERROR] Extraction failed: {e}")
                    results[year] = {'status': 'failed', 'error': str(e)}

        # Update checkpoint
        self.checkpoint['extraction'] = {
            'completed': True,
            'timestamp': datetime.now().isoformat(),
            'years': results,
            'total_firm_years': total_firm_years
        }

        self.logger.info("")
        self.logger.info(f"  Total extracted: {total_firm_years:,} firm-years across {len(years)} years")

        return {
            'status': 'success',
            'years': results,
            'total_firm_years': total_firm_years
        }

    def _run_cleaning(self, years: List[int], force: bool) -> Dict:
        """
        Phase 1b: Clean extracted business descriptions.

        Processes data year-by-year and saves separate parquet files for each year.

        Applies:
        - Zero-length removal
        - Per-year 95th percentile truncation (NEW - not exclusion)
        - Level-based deduplication
        - Firm-year deduplication

        Args:
            years: List of years to clean
            force: Force re-run

        Returns:
            Dictionary with cleaning results
        """
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("PHASE 1B: DATA CLEANING")
        self.logger.info(f"{'=' * 80}")

        self.logger.info(f"  Cleaning years: {min(years)}-{max(years)}")
        self.logger.info(f"  Output directory: data/korean_texts/")
        self.logger.info("")

        results = {}
        total_firm_years = 0
        total_initial = 0
        total_firms = 0

        for year in years:
            # Check input file exists
            input_path = Path(f"data/korean_texts/business_descriptions_raw_{year}.parquet")
            output_path = Path(f"data/korean_texts/business_descriptions_clean_{year}.parquet")
            stats_path = Path(f"data/korean_texts/cleaning_stats_{year}.json")

            if not input_path.exists():
                self.logger.warning(f"  {year}: [SKIP] Raw file not found: {input_path.name}")
                results[year] = {'status': 'skipped', 'reason': 'no_raw_file'}
                continue

            if output_path.exists() and not force:
                self.logger.info(f"  {year}: [OK] Already cleaned, skipping")
                # Count rows for summary
                df_existing = pd.read_parquet(output_path)
                results[year] = {
                    'status': 'skipped',
                    'output': str(output_path),
                    'n_final': len(df_existing)
                }
                total_firm_years += len(df_existing)
                continue

            # Run cleaning for this year
            self.logger.info(f"  {year}: Cleaning...")
            try:
                result = self.text_cleaner.run(
                    input_path=input_path,
                    output_path=output_path,
                    year_range=(year, year)
                )

                self.logger.info(f"  {year}: [OK] {result['n_final']:,} documents (from {result['n_initial']:,}) → {output_path.name}")

                results[year] = {
                    'status': 'success',
                    **result
                }
                total_firm_years += result['n_final']
                total_initial += result['n_initial']
                total_firms = max(total_firms, result['n_firms_final'])

            except Exception as e:
                self.logger.error(f"  {year}: [ERROR] Cleaning failed: {e}")
                results[year] = {'status': 'failed', 'error': str(e)}

        # Update checkpoint
        self.checkpoint['cleaning'] = {
            'completed': True,
            'timestamp': datetime.now().isoformat(),
            'years': results,
            'total_initial': total_initial,
            'total_final': total_firm_years,
            'total_firms': total_firms
        }

        self.logger.info("")
        self.logger.info(f"  Total cleaned: {total_firm_years:,} firm-years (from {total_initial:,}) across {len(years)} years")
        self.logger.info(f"  Unique firms: {total_firms:,}")

        return {
            'status': 'success',
            'years': results,
            'total_initial': total_initial,
            'total_final': total_firm_years,
            'total_firms': total_firms
        }

    def _run_universe_matching(self, years: List[int], force: bool) -> Dict:
        """
        Phase 1.5: Match text data to trading universe and fill gaps.

        Implements Hoberg & Phillips methodology:
        1. Forward fill missing firm-years
        2. Backfill early years
        3. Mask to actual trading universe (from alpha-excel)

        Args:
            years: List of years to process
            force: Force re-run

        Returns:
            Dictionary with matching and filling results
        """
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("PHASE 1.5: UNIVERSE MATCHING & DATA FILLING")
        self.logger.info(f"{'=' * 80}")

        # Check if already done
        output_path = Path(self.config.get("paths.outputs.universe_matching.filled_descriptions"))

        if output_path.exists() and not force:
            self.logger.info(f"  [OK] Output exists: {output_path}")
            self.logger.info("  Skipping (use force=True to re-run)")
            return {'status': 'skipped', 'output': str(output_path)}

        # Use provided years
        start_year = min(years)
        end_year = max(years)

        # Load Phase 1b output (cleaned data) - use yearly files directory
        # The universe matcher will load from business_descriptions_clean_YYYY.parquet files
        input_path = Path(self.config.get("paths.inputs.business_descriptions_clean"))

        # Check if at least one yearly cleaned file exists
        yearly_files_exist = False
        for year in years:
            year_file = input_path.parent / f"business_descriptions_clean_{year}.parquet"
            if year_file.exists():
                yearly_files_exist = True
                break

        if not yearly_files_exist and not input_path.exists():
            error_msg = (
                f"Phase 1b (cleaning) output not found. Expected either:\n"
                f"  - Yearly files: {input_path.parent}/business_descriptions_clean_YYYY.parquet\n"
                f"  - Consolidated file: {input_path}\n"
                f"Please run cleaning first."
            )
            self.logger.error(f"  [ERROR] {error_msg}")
            return {'status': 'failed', 'error': error_msg}

        try:
            # Run matching and filling
            result = self.universe_matcher.run(
                input_path=input_path,
                output_path=output_path,
                start_year=start_year,
                end_year=end_year
            )

            # Update checkpoint
            self.checkpoint['universe_matching'] = {
                'completed': True,
                'timestamp': datetime.now().isoformat(),
                **result
            }

            self.logger.info(f"  [OK] Filled {result['n_filled']:,} firm-years")
            self.logger.info(f"  [OK] Saved: {output_path}")

            return {'status': 'success', **result}

        except Exception as e:
            self.logger.error(f"  [ERROR] Universe matching failed: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'failed', 'error': str(e)}

    def _run_corpus(self, years: List[int], force: bool, max_workers: Optional[int] = None) -> Dict:
        """
        Phase 2: Build year-specific corpora (sequential processing).

        Args:
            years: Years to process
            force: Force re-run
            max_workers: Ignored (kept for API compatibility)

        Returns:
            Dictionary with corpus building results per year
        """
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("PHASE 2: CORPUS BUILDING (SEQUENTIAL)")
        self.logger.info(f"{'=' * 80}")

        results = {}

        # Get path to filled descriptions
        filled_descriptions_path = self.config.get("paths.outputs.universe_matching.filled_descriptions")

        # Check if filled descriptions exist
        if not Path(filled_descriptions_path).exists():
            self.logger.error(f"  [ERROR] Filled descriptions not found: {filled_descriptions_path}")
            self.logger.error("  Please run Phase 1.5 (universe matching) first")
            return {'status': 'failed', 'error': 'Filled descriptions not found'}

        # Filter years that need processing
        years_to_process = []
        for year in years:
            output_path = Path(
                self.config.format_path("paths.outputs.corpus.firm_word_sets", year=year)
            )

            if output_path.exists() and not force:
                self.logger.info(f"  {year}: [OK] Output exists, skipping")
                results[year] = {'status': 'skipped', 'output': str(output_path)}
            else:
                years_to_process.append(year)

        if not years_to_process:
            self.logger.info("  All years already processed!")
            return results

        # Process years sequentially
        self.logger.info(f"\n  Processing {len(years_to_process)} years sequentially...")

        # Load data once for all years (more efficient than loading per year)
        self.logger.info(f"  Loading filled descriptions...")
        df_all = pd.read_parquet(filled_descriptions_path)
        self.logger.info(f"  Loaded {len(df_all):,} total rows")

        for year in years_to_process:
            self.logger.info(f"\n  Processing year {year}...")

            try:
                # Filter to this year
                df_year = df_all[df_all['year'] == year].copy()
                self.logger.info(f"    {len(df_year):,} rows for year {year}")

                # Build corpus for this year
                _, _, stats = self.corpus_builder.build_year_corpus(
                    year, df=df_year, save_outputs=True
                )

                self.logger.info(f"  {year}: [OK] Built corpus: {stats['N_t_output']} firms, {stats['W_t']} words")

                results[year] = {
                    'status': 'success',
                    'N_t': stats['N_t_output'],
                    'W_t': stats['W_t']
                }

                # Update checkpoint
                if 'corpus' not in self.checkpoint:
                    self.checkpoint['corpus'] = {}
                self.checkpoint['corpus'][str(year)] = {
                    'completed': True,
                    'timestamp': datetime.now().isoformat(),
                    'stats': stats
                }

            except Exception as e:
                self.logger.error(f"  {year}: [ERROR] Failed: {e}")
                import traceback
                traceback.print_exc()
                results[year] = {'status': 'failed', 'error': str(e)}

        return results

    def _run_binary_matrices(self, years: List[int], force: bool) -> Dict:
        """
        Phase 3a: Build binary matrices Q_t.

        Args:
            years: Years to process
            force: Force re-run

        Returns:
            Dictionary with binary matrix results per year
        """
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("PHASE 3A: BINARY MATRICES")
        self.logger.info(f"{'=' * 80}")

        results = {}

        for year in years:
            self.logger.info(f"\n  Processing year {year}...")

            # Check if already done
            base_dir = self.config.get("paths.outputs.binary_matrix.base_dir")
            output_path = Path(base_dir) / f"binary_matrix_{year}.npz"

            if output_path.exists() and not force:
                self.logger.info(f"    [OK] Output exists: {output_path}")
                self.logger.info("    Skipping (use force=True to re-run)")
                results[year] = {'status': 'skipped', 'output': str(output_path)}
                continue

            # Run binary matrix construction
            try:
                Q_t, metadata = self.binary_builder.build_matrix(year, save_output=True)

                self.logger.info(f"    [OK] Built matrix: {metadata['N_t']} × {metadata['W_t']}, {metadata['sparsity']*100:.2f}% sparse")

                results[year] = {
                    'status': 'success',
                    'N_t': metadata['N_t'],
                    'W_t': metadata['W_t'],
                    'sparsity': metadata['sparsity']
                }

                # Update checkpoint
                if 'binary' not in self.checkpoint:
                    self.checkpoint['binary'] = {}
                self.checkpoint['binary'][str(year)] = {
                    'completed': True,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': metadata
                }

            except Exception as e:
                self.logger.error(f"    [ERROR] Failed: {e}")
                results[year] = {'status': 'failed', 'error': str(e)}

        return results

    def _run_similarity(self, years: List[int], force: bool) -> Dict:
        """
        Phase 3b: Compute similarity matrices M_t.

        Args:
            years: Years to process
            force: Force re-run

        Returns:
            Dictionary with similarity results per year
        """
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("PHASE 3B: SIMILARITY MATRICES")
        self.logger.info(f"{'=' * 80}")

        results = {}

        for year in years:
            self.logger.info(f"\n  Processing year {year}...")

            # Check if already done
            base_dir = self.config.get("paths.outputs.similarity.base_dir")
            output_path = Path(base_dir) / f"similarity_matrix_{year}.npz"

            if output_path.exists() and not force:
                self.logger.info(f"    [OK] Output exists: {output_path}")
                self.logger.info("    Skipping (use force=True to re-run)")
                results[year] = {'status': 'skipped', 'output': str(output_path)}
                continue

            # Run similarity computation
            try:
                M_t, metadata = self.similarity_computer.compute_similarity(year, save_output=True)

                self.logger.info(f"    [OK] Computed similarity: {metadata['N_t']} × {metadata['N_t']}, mean={metadata['off_diagonal']['mean']:.4f}")

                results[year] = {
                    'status': 'success',
                    'N_t': metadata['N_t'],
                    'mean_similarity': metadata['off_diagonal']['mean']
                }

                # Update checkpoint
                if 'similarity' not in self.checkpoint:
                    self.checkpoint['similarity'] = {}
                self.checkpoint['similarity'][str(year)] = {
                    'completed': True,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': metadata
                }

            except Exception as e:
                self.logger.error(f"    [ERROR] Failed: {e}")
                results[year] = {'status': 'failed', 'error': str(e)}

        return results

    def _run_peer_groups(self, years: List[int], force: bool) -> Dict:
        """
        Phase 4: Build TNIC peer groups.

        Args:
            years: Years to process
            force: Force re-run

        Returns:
            Dictionary with peer group results per year
        """
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("PHASE 4: PEER GROUPS")
        self.logger.info(f"{'=' * 80}")

        results = {}

        for year in years:
            self.logger.info(f"\n  Processing year {year}...")

            # Check if already done
            base_dir = self.config.get("paths.outputs.peers.base_dir")
            output_path = Path(base_dir) / f"tnic_peers_{year}.csv"

            if output_path.exists() and not force:
                self.logger.info(f"    [OK] Output exists: {output_path}")
                self.logger.info("    Skipping (use force=True to re-run)")
                results[year] = {'status': 'skipped', 'output': str(output_path)}
                continue

            # Run peer group construction
            try:
                peers_df, comp_df, metadata = self.peer_builder.build_peer_groups(year, save_output=True)

                self.logger.info(f"    [OK] Built peer groups: {metadata['tnic_stats']['avg_peers_per_firm']:.1f} avg peers, {metadata['comparison']['avg_overlap_pct']:.1f}% overlap")

                results[year] = {
                    'status': 'success',
                    'avg_peers': metadata['tnic_stats']['avg_peers_per_firm'],
                    'overlap_pct': metadata['comparison']['avg_overlap_pct']
                }

                # Update checkpoint
                if 'peers' not in self.checkpoint:
                    self.checkpoint['peers'] = {}
                self.checkpoint['peers'][str(year)] = {
                    'completed': True,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': metadata
                }

            except Exception as e:
                self.logger.error(f"    [ERROR] Failed: {e}")
                results[year] = {'status': 'failed', 'error': str(e)}

        return results

    def get_completed_years(self, phase: str) -> Set[int]:
        """
        Get set of years that have completed a specific phase.

        Args:
            phase: Phase name

        Returns:
            Set of completed years

        Examples:
            >>> pipeline = TNICPipeline()
            >>> completed = pipeline.get_completed_years("corpus")
            >>> print(f"Corpus built for years: {sorted(completed)}")
        """
        if phase not in self.checkpoint:
            return set()

        completed = {
            int(year) for year, data in self.checkpoint[phase].items()
            if data.get('completed', False)
        }

        return completed

    def validate_dependencies(
        self,
        phase: str,
        years: List[int],
        phases_in_execution: Optional[List[str]] = None
    ) -> Dict:
        """
        Validate that dependencies are met for a phase by checking file existence.

        This method checks for actual output files on disk, not just checkpoint status,
        ensuring that prerequisites truly exist. Dependencies that are included in the
        current execution plan are skipped (they will be satisfied by running them).

        Args:
            phase: Phase to validate
            years: Years to check
            phases_in_execution: List of phases that will be run in current execution.
                                Dependencies in this list will be skipped.

        Returns:
            Dictionary with validation results

        Examples:
            >>> pipeline = TNICPipeline()
            >>> # Check if similarity can run (assuming binary is not in execution plan)
            >>> validation = pipeline.validate_dependencies("similarity", [2010, 2011])
            >>> if not validation['valid']:
            ...     print(f"Missing: {validation['missing']}")
            >>>
            >>> # Check if similarity can run when binary will be executed first
            >>> validation = pipeline.validate_dependencies(
            ...     "similarity", [2010, 2011], phases_in_execution=["binary", "similarity"]
            ... )
            >>> # Should pass because binary will be run first
        """
        dependencies = {
            'extraction': [],  # No dependencies
            'cleaning': ['extraction'],  # Cleaning depends on extraction
            'universe_matching': ['cleaning'],  # Universe matching depends on cleaning
            'corpus': ['universe_matching'],  # Corpus depends on universe matching
            'binary': ['corpus'],
            'similarity': ['binary'],  # Binary depends on corpus, so transitively satisfied
            'peers': ['similarity']  # Similarity depends on binary, so transitively satisfied
        }

        if phase not in dependencies:
            return {'valid': False, 'error': f"Unknown phase: {phase}"}

        if phases_in_execution is None:
            phases_in_execution = []

        missing = {}

        # Check each dependency phase
        for dep_phase in dependencies[phase]:
            # Skip validation if dependency is in the execution plan
            # (it will be satisfied by running it before this phase)
            if dep_phase in phases_in_execution:
                continue

            missing_years = []

            # Check file existence for each year
            for year in years:
                file_exists = self._check_phase_output_exists(dep_phase, year)

                if not file_exists:
                    missing_years.append(year)

            if missing_years:
                missing[dep_phase] = sorted(missing_years)

        valid = len(missing) == 0

        return {
            'valid': valid,
            'missing': missing if not valid else None
        }

    def _check_phase_output_exists(self, phase: str, year: int) -> bool:
        """
        Check if output files exist for a specific phase and year.

        Args:
            phase: Phase name
            year: Year to check

        Returns:
            True if output files exist, False otherwise
        """
        if phase == "extraction":
            # Extraction now uses year-specific files
            output_path = Path(f"data/korean_texts/business_descriptions_raw_{year}.parquet")
            return output_path.exists()

        elif phase == "cleaning":
            # Cleaning now uses year-specific files
            output_path = Path(f"data/korean_texts/business_descriptions_clean_{year}.parquet")
            return output_path.exists()

        elif phase == "universe_matching":
            # Universe matching is year-independent
            output_path = Path(self.config.get("paths.outputs.universe_matching.filled_descriptions"))
            return output_path.exists()

        elif phase == "corpus":
            # Check for firm word sets file
            base_dir = self.config.get("paths.outputs.corpus.base_dir")
            year_dir = Path(str(base_dir).format(year=year))
            firm_sets_path = year_dir / f"firm_word_sets_{year}.parquet"
            return firm_sets_path.exists()

        elif phase == "binary":
            # Check for binary matrix file
            base_dir = self.config.get("paths.outputs.binary_matrix.base_dir")
            matrix_path = Path(base_dir) / f"binary_matrix_{year}.npz"
            return matrix_path.exists()

        elif phase == "similarity":
            # Check for similarity matrix file
            base_dir = self.config.get("paths.outputs.similarity.base_dir")
            matrix_path = Path(base_dir) / f"similarity_matrix_{year}.npz"
            return matrix_path.exists()

        elif phase == "peers":
            # Check for peer groups file
            base_dir = self.config.get("paths.outputs.peers.base_dir")
            peers_path = Path(base_dir) / f"tnic_peers_{year}.csv"
            return peers_path.exists()

        else:
            return False

    def _load_checkpoint(self) -> Dict:
        """Load checkpoint from file."""
        if not self.checkpoint_path.exists():
            return {}

        try:
            with open(self.checkpoint_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load checkpoint: {e}")
            return {}

    def _save_checkpoint(self):
        """Save checkpoint to file."""
        try:
            self.checkpoint['last_updated'] = datetime.now().isoformat()

            # Convert numpy types to native Python types for JSON serialization
            checkpoint_serializable = self._convert_to_serializable(self.checkpoint)

            with open(self.checkpoint_path, 'w') as f:
                json.dump(checkpoint_serializable, f, indent=2)

            self.logger.debug(f"Checkpoint saved: {self.checkpoint_path}")

        except Exception as e:
            self.logger.warning(f"Could not save checkpoint: {e}")

    def _convert_to_serializable(self, obj):
        """
        Recursively convert numpy types to native Python types for JSON serialization.

        Args:
            obj: Object to convert (can be dict, list, or any value)

        Returns:
            Serializable version of the object
        """
        if isinstance(obj, dict):
            return {key: self._convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    def _print_summary(self, results: Dict):
        """Print execution summary."""
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("PIPELINE EXECUTION SUMMARY")
        self.logger.info(f"{'=' * 80}")

        for phase, phase_results in results.items():
            if isinstance(phase_results, dict):
                if 'status' in phase_results:
                    # Single-year phase
                    status = phase_results['status']
                    self.logger.info(f"  {phase}: {status}")
                else:
                    # Multi-year phase
                    statuses = [r.get('status', 'unknown') for r in phase_results.values()]
                    success = statuses.count('success')
                    skipped = statuses.count('skipped')
                    failed = statuses.count('failed')

                    self.logger.info(f"  {phase}: {success} success, {skipped} skipped, {failed} failed")

        self.logger.info(f"{'=' * 80}")

    def __repr__(self) -> str:
        """String representation."""
        return f"TNICPipeline(checkpoint={self.checkpoint_path})"
