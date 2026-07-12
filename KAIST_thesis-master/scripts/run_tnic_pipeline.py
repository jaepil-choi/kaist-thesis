#!/usr/bin/env python
"""
CLI interface for running the TNIC pipeline.

Usage examples:
    # Run full pipeline on pilot years (2010-2011)
    python scripts/run_tnic_pipeline.py --mode pilot

    # Start from binary matrices and run through peers
    python scripts/run_tnic_pipeline.py --start-from binary --mode full

    # Run only similarity computation for specific years
    python scripts/run_tnic_pipeline.py --phase similarity --years 2010 2011 2012

    # Force re-run of binary matrices
    python scripts/run_tnic_pipeline.py --phase binary --force

    # Skip dependency validation (use with caution)
    python scripts/run_tnic_pipeline.py --start-from binary --no-validate
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from tnic import TNICPipeline


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the TNIC (Text-based Network Industry Classification) pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline on pilot years (2010-2011)
  %(prog)s --mode pilot

  # Start from binary matrices through peers on all years
  %(prog)s --start-from binary --mode full

  # Run only similarity computation for specific years
  %(prog)s --phase similarity --years 2010 2011 2012

  # Force re-run of peer groups
  %(prog)s --phase peers --force

  # Check what would run without actually running
  %(prog)s --start-from binary --dry-run

Phase order:
  extraction → cleaning → universe_matching → corpus → binary → similarity → peers
        """
    )

    # Phase selection (mutually exclusive)
    phase_group = parser.add_mutually_exclusive_group()
    phase_group.add_argument(
        "--phase",
        type=str,
        choices=["extraction", "cleaning", "universe_matching", "corpus", "binary", "similarity", "peers"],
        help="Run only this specific phase"
    )
    phase_group.add_argument(
        "--start-from",
        type=str,
        choices=["extraction", "cleaning", "universe_matching", "corpus", "binary", "similarity", "peers"],
        help="Start from this phase and run all subsequent phases"
    )

    # Year selection
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        help="Specific years to process (e.g., --years 2010 2011 2012)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["pilot", "full"],
        default="full",
        help="Year mode: 'pilot' (2010-2011) or 'full' (2010-2025). Default: full"
    )

    # Options
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-run even if outputs exist"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip dependency validation (use with caution)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers for corpus building (default: CPU count)"
    )

    # Dry run
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without actually running"
    )

    # Config
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config directory (default: uses project config/)"
    )

    return parser.parse_args()


def format_phase_list(phases):
    """Format list of phases with arrows."""
    return " → ".join(phases)


def main():
    """Main CLI entry point."""
    args = parse_args()

    # Initialize pipeline
    print("=" * 80)
    print("TNIC PIPELINE CLI")
    print("=" * 80)

    try:
        pipeline = TNICPipeline(config_path=args.config)
    except Exception as e:
        print(f"Error initializing pipeline: {e}")
        return 1

    # Determine which phases will run
    phase_order = ["extraction", "cleaning", "universe_matching", "corpus", "binary", "similarity", "peers"]

    if args.phase:
        phases_to_run = [args.phase]
        run_description = f"Single phase: {args.phase}"
    elif args.start_from:
        start_idx = phase_order.index(args.start_from)
        phases_to_run = phase_order[start_idx:]
        run_description = f"From {args.start_from} onwards: {format_phase_list(phases_to_run)}"
    else:
        phases_to_run = phase_order
        run_description = f"All phases: {format_phase_list(phases_to_run)}"

    # Determine years
    if args.years:
        years = args.years
        year_description = f"Years: {min(years)}-{max(years)} ({len(years)} years)"
    else:
        year_range = pipeline.config.get_year_range(args.mode)
        years = list(year_range)
        year_description = f"Mode: {args.mode} ({min(years)}-{max(years)}, {len(years)} years)"

    # Show what will be run
    print("\nPipeline Configuration:")
    print(f"  {run_description}")
    print(f"  {year_description}")
    print(f"  Force re-run: {args.force}")
    print(f"  Validate dependencies: {not args.no_validate}")
    if args.workers:
        print(f"  Parallel workers: {args.workers}")

    # Dry run mode
    if args.dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - Nothing will be executed")
        print("=" * 80)

        # Check dependencies if requested
        if not args.no_validate:
            print("\nDependency check:")
            for phase_name in phases_to_run:
                if phase_name == "extraction":
                    print(f"  {phase_name}: no dependencies")
                    continue

                validation = pipeline.validate_dependencies(
                    phase_name, years, phases_in_execution=phases_to_run
                )
                if validation['valid']:
                    print(f"  [OK] {phase_name}: all dependencies satisfied")
                else:
                    print(f"  [FAIL] {phase_name}: missing dependencies")
                    for dep_phase, missing_years in validation['missing'].items():
                        print(f"      - {dep_phase}: missing years {missing_years}")

        # Show which files would be processed
        print("\nFiles to be checked/created:")
        for phase_name in phases_to_run:
            print(f"\n  {phase_name.upper()}:")
            for year in years[:3]:  # Show first 3 years as example
                file_exists = pipeline._check_phase_output_exists(phase_name, year)
                status = "EXISTS" if file_exists else "MISSING"
                print(f"    Year {year}: {status}")
            if len(years) > 3:
                print(f"    ... and {len(years) - 3} more years")

        print("\n" + "=" * 80)
        print("To execute, remove --dry-run flag")
        print("=" * 80)
        return 0

    # Confirm execution for full mode (only if years not explicitly specified)
    if args.mode == "full" and not args.force and not args.phase and not args.years:
        print("\n" + "!" * 80)
        print("WARNING: Running full pipeline on all years (2010-2025)")
        print("This may take significant time and compute resources.")
        print("!" * 80)
        response = input("\nContinue? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Aborted.")
            return 0

    # Run pipeline
    print("\n" + "=" * 80)
    print("STARTING EXECUTION")
    print("=" * 80)

    try:
        results = pipeline.run(
            phase=args.phase,
            start_from_phase=args.start_from,
            years=years if args.years else None,
            mode=args.mode,
            force=args.force,
            validate_deps=not args.no_validate,
            max_workers=args.workers
        )

        # Print summary
        print("\n" + "=" * 80)
        print("EXECUTION COMPLETE")
        print("=" * 80)

        # Count successes/failures
        total_success = 0
        total_skipped = 0
        total_failed = 0

        for phase_name, phase_results in results.items():
            if isinstance(phase_results, dict):
                if 'status' in phase_results:
                    # Single result (like extraction)
                    status = phase_results['status']
                    if status == 'success':
                        total_success += 1
                    elif status == 'skipped':
                        total_skipped += 1
                    elif status == 'failed':
                        total_failed += 1
                else:
                    # Multi-year results
                    for year_result in phase_results.values():
                        if isinstance(year_result, dict):
                            status = year_result.get('status', 'unknown')
                            if status == 'success':
                                total_success += 1
                            elif status == 'skipped':
                                total_skipped += 1
                            elif status == 'failed':
                                total_failed += 1

        print(f"\nResults:")
        print(f"  [+] Success: {total_success}")
        print(f"  [-] Skipped: {total_skipped}")
        if total_failed > 0:
            print(f"  [X] Failed: {total_failed}")

        return 0 if total_failed == 0 else 1

    except ValueError as e:
        # Dependency validation error
        print(f"\nError: {e}")
        print("\nTo skip validation, add --no-validate flag (not recommended)")
        return 1

    except Exception as e:
        print(f"\nPipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
