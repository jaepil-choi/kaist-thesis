"""
CLI script to run TNIC-DL pipeline (Kim et al. 2020 Deep Autoencoder).

Usage:
    # Run pipeline for 2010 (with training)
    python scripts/run_tnic_dl_pipeline.py --years 2010

    # Run for multiple years
    python scripts/run_tnic_dl_pipeline.py --years 2010 2011 2012

    # Skip training (load existing model)
    python scripts/run_tnic_dl_pipeline.py --years 2010 --no-train

    # Run with clustering
    python scripts/run_tnic_dl_pipeline.py --years 2010 --cluster
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tnic_dl.pipeline import TNICDLPipeline
from tnic_dl.utils import setup_logger, save_json

logger = setup_logger("run_tnic_dl_pipeline")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run TNIC-DL pipeline using Kim et al. (2020) deep autoencoder methodology"
    )

    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        required=True,
        help="Years to process (e.g., --years 2010 2011 2012)"
    )

    parser.add_argument(
        "--no-train",
        action="store_true",
        help="Skip autoencoder training (load existing model)"
    )

    parser.add_argument(
        "--no-similarity",
        action="store_true",
        help="Skip similarity computation"
    )

    parser.add_argument(
        "--cluster",
        action="store_true",
        help="Perform spherical k-means clustering (K=300)"
    )

    parser.add_argument(
        "--save-results",
        type=str,
        default=None,
        help="Path to save results JSON (default: auto-generate)"
    )

    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()

    logger.info("=" * 80)
    logger.info("KIM ET AL. (2020) DEEP AUTOENCODER PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Years: {args.years}")
    logger.info(f"Train autoencoder: {not args.no_train}")
    logger.info(f"Compute similarity: {not args.no_similarity}")
    logger.info(f"Clustering: {args.cluster}")
    logger.info("=" * 80)

    # Initialize pipeline
    pipeline = TNICDLPipeline()

    # Run pipeline
    try:
        results = pipeline.run(
            years=args.years,
            train_autoencoder=not args.no_train,
            compute_similarity=not args.no_similarity,
            cluster=args.cluster,
        )

        # Save results
        if args.save_results:
            results_path = Path(args.save_results)
        else:
            # Auto-generate path
            years_str = "_".join(map(str, args.years))
            results_path = Path(f"data/korean_tnic_dl/outputs/pipeline_results_{years_str}.json")
            results_path.parent.mkdir(parents=True, exist_ok=True)

        save_json(results, results_path)
        logger.info(f"\nResults saved to: {results_path}")

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        for year, year_results in results.items():
            if 'error' not in year_results:
                logger.info(f"  {year}: {year_results.get('n_firms', 'N/A')} firms processed")
                if 'training_history' in year_results:
                    logger.info(f"    Training: {year_results['training_history']['epochs']} epochs, "
                              f"{year_results['training_history']['total_time']:.1f}s")
                logger.info(f"    Embeddings: {year_results['embeddings_shape']}")
            else:
                logger.info(f"  {year}: ERROR - {year_results['error']}")

    except Exception as e:
        logger.error(f"\nPipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
