#!/usr/bin/env python3
"""
Script 01: Preprocess and Align NER Results

Purpose:
    Load all data (V2, Phase 4, ground truth), detect and clean BPE artifacts,
    align papers by ID, and generate comprehensive statistics.

Key Functionality:
    1. Load all datasets (V2, Phase 4, test split, inventory)
    2. Parse entities from various formats (JSON, CSV, lists)
    3. Detect and clean BPE tokenization artifacts
    4. Generate BPE contamination report
    5. Align papers by ID across all datasets
    6. Generate entity count statistics
    7. Save aligned data and reports

Output Files:
    - ../data/aligned_papers.csv: Merged dataset with all system outputs
    - ../data/bpe_artifact_report.json: BPE contamination analysis
    - ../data/entity_counts.csv: Distribution of entity counts across systems

Usage:
    python 01_preprocess_and_align.py [options]

    Options:
        --v2-path PATH              Path to V2 NER results CSV
        --phase4-path PATH          Path to Phase 4 NER results CSV
        --test-split-path PATH      Path to NER test split CSV
        --inventory-path PATH       Path to final inventory CSV
        --output-dir PATH           Output directory for results (default: ../data)
        --verbose                   Enable verbose logging
        --skip-bpe-cleaning         Skip BPE artifact cleaning (for debugging)

Examples:
    # Use default paths
    python 01_preprocess_and_align.py

    # Use custom paths with verbose output
    python 01_preprocess_and_align.py --v2-path /path/to/v2.csv --verbose

    # Skip BPE cleaning for faster processing
    python 01_preprocess_and_align.py --skip-bpe-cleaning

Author: Claude Code
Date: 2025-11-05
Version: 1.0.0
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from tqdm import tqdm

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    load_v2_results,
    load_phase4_results,
    load_ner_test_split,
    load_inventory,
    parse_entity_list,
    detect_bpe_artifacts,
    clean_bpe_entity,
    clean_bpe_dataframe,
    generate_bpe_report,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('01_preprocess_and_align.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Preprocess and align V2 and Phase 4 NER results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Input file paths
    parser.add_argument(
        '--v2-path',
        type=Path,
        default=None,
        help='Path to V2 NER results CSV (default: uses standard location)'
    )

    parser.add_argument(
        '--phase4-path',
        type=Path,
        default=None,
        help='Path to Phase 4 NER results CSV (default: uses standard location)'
    )

    parser.add_argument(
        '--test-split-path',
        type=Path,
        default=None,
        help='Path to NER test split CSV (default: uses standard location)'
    )

    parser.add_argument(
        '--inventory-path',
        type=Path,
        default=None,
        help='Path to final inventory CSV (default: uses standard location)'
    )

    # Output directory
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).parent.parent / 'data',
        help='Output directory for results (default: ../data)'
    )

    # Processing options
    parser.add_argument(
        '--skip-bpe-cleaning',
        action='store_true',
        help='Skip BPE artifact cleaning (for debugging)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def load_all_data(args: argparse.Namespace) -> Dict[str, pd.DataFrame]:
    """
    Load all datasets with error handling.

    Args:
        args: Command-line arguments containing file paths

    Returns:
        Dictionary with keys: 'v2', 'phase4', 'test_split', 'inventory'

    Raises:
        FileNotFoundError: If any required file is not found
        pd.errors.EmptyDataError: If any file is empty
    """
    logger.info("=" * 80)
    logger.info("STEP 1: Loading Datasets")
    logger.info("=" * 80)

    datasets = {}

    try:
        # Load V2 results
        logger.info("\n[1/4] Loading V2 (old model) NER results...")
        datasets['v2'] = load_v2_results(args.v2_path)
        logger.info(f"✓ Loaded {len(datasets['v2']):,} V2 results")

        # Load Phase 4 results
        logger.info("\n[2/4] Loading Phase 4 (new model) NER results...")
        datasets['phase4'] = load_phase4_results(args.phase4_path)
        logger.info(f"✓ Loaded {len(datasets['phase4']):,} Phase 4 results")

        # Load test split
        logger.info("\n[3/4] Loading NER test split ground truth...")
        datasets['test_split'] = load_ner_test_split(args.test_split_path)
        logger.info(f"✓ Loaded {len(datasets['test_split']):,} test samples")

        # Load inventory
        logger.info("\n[4/4] Loading final inventory...")
        datasets['inventory'] = load_inventory(args.inventory_path)
        logger.info(f"✓ Loaded {len(datasets['inventory']):,} papers in inventory")

        logger.info("\n✓ All datasets loaded successfully")
        return datasets

    except FileNotFoundError as e:
        logger.error(f"✗ File not found: {e}")
        raise
    except pd.errors.EmptyDataError as e:
        logger.error(f"✗ Empty data file: {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Unexpected error loading data: {e}")
        raise


def parse_all_entities(datasets: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Parse entity columns from string/JSON to lists.

    Args:
        datasets: Dictionary of DataFrames

    Returns:
        Updated dictionary with parsed entity columns
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Parsing Entity Columns")
    logger.info("=" * 80)

    # Parse V2 entities
    logger.info("\n[1/3] Parsing V2 entities (common_name, full_name)...")
    datasets['v2']['common_name_list'] = datasets['v2']['common_name'].apply(
        lambda x: parse_entity_list(x) if pd.notna(x) else []
    )
    datasets['v2']['full_name_list'] = datasets['v2']['full_name'].apply(
        lambda x: parse_entity_list(x) if pd.notna(x) else []
    )
    logger.info(f"✓ Parsed V2 entities")

    # Parse Phase 4 entities
    logger.info("\n[2/3] Parsing Phase 4 entities (common_name, full_name)...")
    datasets['phase4']['common_name_list'] = datasets['phase4']['common_name'].apply(
        lambda x: parse_entity_list(x) if pd.notna(x) else []
    )
    datasets['phase4']['full_name_list'] = datasets['phase4']['full_name'].apply(
        lambda x: parse_entity_list(x) if pd.notna(x) else []
    )
    logger.info(f"✓ Parsed Phase 4 entities")

    # Parse test split entities
    logger.info("\n[3/3] Parsing test split entities (ground truth)...")
    datasets['test_split']['common_name_list'] = datasets['test_split']['common_name'].apply(
        lambda x: parse_entity_list(x) if pd.notna(x) else []
    )
    datasets['test_split']['full_name_list'] = datasets['test_split']['full_name'].apply(
        lambda x: parse_entity_list(x) if pd.notna(x) else []
    )
    logger.info(f"✓ Parsed test split entities")

    logger.info("\n✓ All entity columns parsed successfully")
    return datasets


def detect_and_clean_bpe(
    datasets: Dict[str, pd.DataFrame],
    skip_cleaning: bool = False
) -> Tuple[Dict[str, pd.DataFrame], Dict]:
    """
    Detect and clean BPE artifacts in Phase 4 data.

    Args:
        datasets: Dictionary of DataFrames
        skip_cleaning: If True, skip BPE cleaning

    Returns:
        Tuple of (updated datasets, BPE report)
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: Detecting and Cleaning BPE Artifacts")
    logger.info("=" * 80)

    if skip_cleaning:
        logger.warning("\n⚠ BPE cleaning skipped (--skip-bpe-cleaning flag set)")
        return datasets, {}

    # Check Phase 4 common_name for BPE artifacts
    logger.info("\n[1/3] Analyzing Phase 4 common_name for BPE contamination...")
    phase4_df = datasets['phase4']

    # Generate BPE report on common_name column (raw string)
    bpe_report_common = generate_bpe_report(phase4_df, entity_column='common_name')

    # Generate BPE report on full_name column (raw string)
    logger.info("\n[2/3] Analyzing Phase 4 full_name for BPE contamination...")
    bpe_report_full = generate_bpe_report(phase4_df, entity_column='full_name')

    # Combine reports
    bpe_report = {
        'common_name': bpe_report_common,
        'full_name': bpe_report_full,
        'summary': {
            'total_papers': len(phase4_df),
            'common_contaminated': bpe_report_common.get('contaminated_rows', 0),
            'full_contaminated': bpe_report_full.get('contaminated_rows', 0),
        }
    }

    # Clean BPE artifacts
    logger.info("\n[3/3] Cleaning BPE artifacts from Phase 4 entity lists...")

    def clean_entity_list(entity_list: List[str]) -> List[str]:
        """Clean BPE artifacts from a list of entities."""
        if not entity_list:
            return []
        return [clean_bpe_entity(e) for e in entity_list]

    # Clean common_name_list
    logger.info("  - Cleaning common_name_list...")
    datasets['phase4']['common_name_list_cleaned'] = datasets['phase4']['common_name_list'].apply(
        clean_entity_list
    )

    # Clean full_name_list
    logger.info("  - Cleaning full_name_list...")
    datasets['phase4']['full_name_list_cleaned'] = datasets['phase4']['full_name_list'].apply(
        clean_entity_list
    )

    # Count how many entities were cleaned
    total_entities_common = sum(len(x) for x in datasets['phase4']['common_name_list'])
    total_entities_full = sum(len(x) for x in datasets['phase4']['full_name_list'])

    logger.info(f"\n✓ BPE cleaning complete:")
    logger.info(f"  - Common name contamination: {bpe_report_common.get('row_contamination_rate', 0):.1%} of papers")
    logger.info(f"  - Full name contamination: {bpe_report_full.get('row_contamination_rate', 0):.1%} of papers")
    logger.info(f"  - Total entities processed: {total_entities_common + total_entities_full:,}")

    return datasets, bpe_report


def align_papers_by_id(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Align papers by ID across all datasets.

    Creates unified DataFrame with columns:
    - paper_id: PubMed ID
    - title: Paper title
    - abstract: Paper abstract
    - true_com: Ground truth common names (list)
    - true_ful: Ground truth full names (list)
    - v2_com: V2 predicted common names (list)
    - v2_ful: V2 predicted full names (list)
    - p4_com_raw: Phase 4 raw common names (list)
    - p4_com_clean: Phase 4 cleaned common names (list)
    - p4_ful_raw: Phase 4 raw full names (list)
    - p4_ful_clean: Phase 4 cleaned full names (list)

    Args:
        datasets: Dictionary of DataFrames

    Returns:
        Aligned DataFrame with all papers
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: Aligning Papers by ID")
    logger.info("=" * 80)

    # Prepare V2 data
    logger.info("\n[1/4] Preparing V2 data...")
    v2_aligned = datasets['v2'][['ID', 'common_name_list', 'full_name_list']].copy()
    v2_aligned.columns = ['paper_id', 'v2_com', 'v2_ful']
    v2_aligned['paper_id'] = v2_aligned['paper_id'].astype(str)
    logger.info(f"✓ V2: {len(v2_aligned):,} papers")

    # Prepare Phase 4 data
    logger.info("\n[2/4] Preparing Phase 4 data...")
    phase4_aligned = datasets['phase4'][[
        'ID',
        'common_name_list',
        'common_name_list_cleaned',
        'full_name_list',
        'full_name_list_cleaned'
    ]].copy()
    phase4_aligned.columns = [
        'paper_id',
        'p4_com_raw',
        'p4_com_clean',
        'p4_ful_raw',
        'p4_ful_clean'
    ]
    phase4_aligned['paper_id'] = phase4_aligned['paper_id'].astype(str)
    logger.info(f"✓ Phase 4: {len(phase4_aligned):,} papers")

    # Prepare test split (ground truth)
    logger.info("\n[3/4] Preparing test split (ground truth)...")
    test_aligned = datasets['test_split'][['id', 'title', 'abstract', 'common_name_list', 'full_name_list']].copy()
    test_aligned.columns = ['paper_id', 'title', 'abstract', 'true_com', 'true_ful']
    test_aligned['paper_id'] = test_aligned['paper_id'].astype(str)
    logger.info(f"✓ Test split: {len(test_aligned):,} papers")

    # Merge all datasets
    logger.info("\n[4/4] Merging datasets by paper_id...")

    # Start with V2 and Phase 4 (inner join - only papers present in both)
    logger.info("  - Merging V2 and Phase 4 results...")
    aligned = pd.merge(
        v2_aligned,
        phase4_aligned,
        on='paper_id',
        how='outer',
        indicator=True
    )
    logger.info(f"    • Both V2 and Phase 4: {sum(aligned['_merge'] == 'both'):,}")
    logger.info(f"    • Only V2: {sum(aligned['_merge'] == 'left_only'):,}")
    logger.info(f"    • Only Phase 4: {sum(aligned['_merge'] == 'right_only'):,}")
    aligned = aligned.drop('_merge', axis=1)

    # Add ground truth where available (left join - preserve all V2/Phase4 papers)
    logger.info("  - Merging with ground truth...")
    aligned = pd.merge(
        aligned,
        test_aligned,
        on='paper_id',
        how='left',
        indicator=True
    )
    logger.info(f"    • With ground truth: {sum(aligned['_merge'] == 'both'):,}")
    logger.info(f"    • Without ground truth: {sum(aligned['_merge'] == 'left_only'):,}")
    aligned = aligned.drop('_merge', axis=1)

    # Reorder columns for clarity
    column_order = [
        'paper_id',
        'title',
        'abstract',
        'true_com',
        'true_ful',
        'v2_com',
        'v2_ful',
        'p4_com_raw',
        'p4_com_clean',
        'p4_ful_raw',
        'p4_ful_clean'
    ]
    aligned = aligned[column_order]

    logger.info(f"\n✓ Alignment complete: {len(aligned):,} total papers")

    # Summary statistics
    has_ground_truth = aligned['true_com'].notna().sum()
    has_v2 = aligned['v2_com'].notna().sum()
    has_phase4 = aligned['p4_com_raw'].notna().sum()

    logger.info(f"\nCoverage statistics:")
    logger.info(f"  - Papers with ground truth: {has_ground_truth:,} ({has_ground_truth/len(aligned):.1%})")
    logger.info(f"  - Papers with V2 predictions: {has_v2:,} ({has_v2/len(aligned):.1%})")
    logger.info(f"  - Papers with Phase 4 predictions: {has_phase4:,} ({has_phase4/len(aligned):.1%})")

    return aligned


def generate_entity_count_stats(aligned_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate entity count statistics across all systems.

    Args:
        aligned_df: Aligned papers DataFrame

    Returns:
        DataFrame with entity count distributions
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 5: Generating Entity Count Statistics")
    logger.info("=" * 80)

    stats_rows = []

    # Define columns to analyze
    columns_to_analyze = [
        ('true_com', 'Ground Truth Common'),
        ('true_ful', 'Ground Truth Full'),
        ('v2_com', 'V2 Common'),
        ('v2_ful', 'V2 Full'),
        ('p4_com_raw', 'Phase 4 Common (Raw)'),
        ('p4_com_clean', 'Phase 4 Common (Clean)'),
        ('p4_ful_raw', 'Phase 4 Full (Raw)'),
        ('p4_ful_clean', 'Phase 4 Full (Clean)'),
    ]

    logger.info("\nCalculating entity count distributions...")

    for col, name in tqdm(columns_to_analyze, desc="Processing columns"):
        # Count entities per paper
        entity_counts = aligned_df[col].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )

        # Calculate statistics
        stats = {
            'system': name,
            'column': col,
            'total_papers': len(aligned_df),
            'papers_with_entities': (entity_counts > 0).sum(),
            'papers_without_entities': (entity_counts == 0).sum(),
            'total_entities': entity_counts.sum(),
            'mean_entities_per_paper': entity_counts.mean(),
            'median_entities_per_paper': entity_counts.median(),
            'min_entities_per_paper': entity_counts.min(),
            'max_entities_per_paper': entity_counts.max(),
            'std_entities_per_paper': entity_counts.std(),
        }

        stats_rows.append(stats)

    stats_df = pd.DataFrame(stats_rows)

    # Log summary
    logger.info("\n✓ Entity count statistics:")
    for _, row in stats_df.iterrows():
        logger.info(f"\n{row['system']}:")
        logger.info(f"  - Total entities: {row['total_entities']:,}")
        logger.info(f"  - Papers with entities: {row['papers_with_entities']:,} ({row['papers_with_entities']/row['total_papers']:.1%})")
        logger.info(f"  - Mean per paper: {row['mean_entities_per_paper']:.2f}")
        logger.info(f"  - Median per paper: {row['median_entities_per_paper']:.1f}")

    return stats_df


def save_outputs(
    aligned_df: pd.DataFrame,
    bpe_report: Dict,
    entity_stats: pd.DataFrame,
    output_dir: Path
) -> None:
    """
    Save all output files.

    Args:
        aligned_df: Aligned papers DataFrame
        bpe_report: BPE contamination report
        entity_stats: Entity count statistics
        output_dir: Output directory
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 6: Saving Output Files")
    logger.info("=" * 80)

    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"\nOutput directory: {output_dir}")

    # Save aligned papers
    logger.info("\n[1/3] Saving aligned_papers.csv...")
    aligned_path = output_dir / "aligned_papers.csv"

    # BUG FIX #2: Serialize entity lists to JSON before saving
    logger.info("  - Serializing entity lists to JSON...")
    aligned_df_to_save = aligned_df.copy()

    # List of entity columns that need JSON serialization
    entity_columns = [
        'true_com', 'true_ful',
        'v2_com', 'v2_ful',
        'p4_com_raw', 'p4_com_clean',
        'p4_ful_raw', 'p4_ful_clean'
    ]

    for col in entity_columns:
        if col in aligned_df_to_save.columns:
            aligned_df_to_save[col] = aligned_df_to_save[col].apply(
                lambda x: json.dumps(x) if isinstance(x, list) else x
            )
            logger.debug(f"    • Serialized '{col}' to JSON")

    # Log sample serialized data to verify proper formatting
    logger.info("  - Sample serialized entities:")
    for col in entity_columns:
        if col in aligned_df_to_save.columns:
            # Find first non-null value
            first_non_null = aligned_df_to_save[col].dropna().iloc[0] if len(aligned_df_to_save[col].dropna()) > 0 else None
            if first_non_null:
                logger.info(f"    • {col}: {first_non_null[:80]}..." if len(str(first_non_null)) > 80 else f"    • {col}: {first_non_null}")

    # Save to CSV
    aligned_df_to_save.to_csv(aligned_path, index=False, encoding='utf-8')
    logger.info(f"✓ Saved {len(aligned_df):,} papers to: {aligned_path}")
    logger.info(f"  File size: {aligned_path.stat().st_size / 1024 / 1024:.2f} MB")

    # Save BPE report
    logger.info("\n[2/3] Saving bpe_artifact_report.json...")
    bpe_path = output_dir / "bpe_artifact_report.json"
    with open(bpe_path, 'w', encoding='utf-8') as f:
        json.dump(bpe_report, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Saved BPE report to: {bpe_path}")

    # Save entity count statistics
    logger.info("\n[3/3] Saving entity_counts.csv...")
    stats_path = output_dir / "entity_counts.csv"
    entity_stats.to_csv(stats_path, index=False, encoding='utf-8')
    logger.info(f"✓ Saved entity statistics to: {stats_path}")

    logger.info("\n✓ All outputs saved successfully")


def print_summary(
    aligned_df: pd.DataFrame,
    bpe_report: Dict,
    entity_stats: pd.DataFrame
) -> None:
    """
    Print final summary statistics.

    Args:
        aligned_df: Aligned papers DataFrame
        bpe_report: BPE contamination report
        entity_stats: Entity count statistics
    """
    logger.info("\n" + "=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)

    logger.info("\n📊 Dataset Statistics:")
    logger.info(f"  Total papers aligned: {len(aligned_df):,}")
    logger.info(f"  Papers with ground truth: {aligned_df['true_com'].notna().sum():,}")
    logger.info(f"  Papers with V2 results: {aligned_df['v2_com'].notna().sum():,}")
    logger.info(f"  Papers with Phase 4 results: {aligned_df['p4_com_raw'].notna().sum():,}")

    if bpe_report:
        logger.info("\n🔍 BPE Contamination:")
        common_report = bpe_report.get('common_name', {})
        full_report = bpe_report.get('full_name', {})
        logger.info(f"  Common name papers contaminated: {common_report.get('contaminated_rows', 0):,} ({common_report.get('row_contamination_rate', 0):.1%})")
        logger.info(f"  Full name papers contaminated: {full_report.get('contaminated_rows', 0):,} ({full_report.get('row_contamination_rate', 0):.1%})")

    logger.info("\n📈 Entity Counts:")
    for _, row in entity_stats.iterrows():
        if 'Ground Truth' in row['system']:
            logger.info(f"  {row['system']}: {int(row['total_entities']):,} entities")

    logger.info("\n✅ Preprocessing complete! Ready for comparison analysis.")
    logger.info("   Next step: Run 02_entity_level_comparison.py")


def main():
    """Main execution function."""
    # Parse arguments
    args = parse_arguments()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 80)
    logger.info("Phase 4 vs V2 NER Comparison: Preprocessing and Alignment")
    logger.info("=" * 80)
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"BPE cleaning: {'DISABLED' if args.skip_bpe_cleaning else 'ENABLED'}")

    try:
        # Step 1: Load all data
        datasets = load_all_data(args)

        # Step 2: Parse entity columns
        datasets = parse_all_entities(datasets)

        # Step 3: Detect and clean BPE artifacts
        datasets, bpe_report = detect_and_clean_bpe(datasets, args.skip_bpe_cleaning)

        # Step 4: Align papers by ID
        aligned_df = align_papers_by_id(datasets)

        # Step 5: Generate entity count statistics
        entity_stats = generate_entity_count_stats(aligned_df)

        # Step 6: Save outputs
        save_outputs(aligned_df, bpe_report, entity_stats, args.output_dir)

        # Print final summary
        print_summary(aligned_df, bpe_report, entity_stats)

        logger.info("\n" + "=" * 80)
        logger.info("✅ SUCCESS: All processing completed successfully")
        logger.info("=" * 80)

        return 0

    except FileNotFoundError as e:
        logger.error(f"\n❌ ERROR: Required file not found: {e}")
        logger.error("   Please check file paths and try again.")
        return 1

    except pd.errors.EmptyDataError as e:
        logger.error(f"\n❌ ERROR: Empty data file: {e}")
        logger.error("   Please check that input files contain data.")
        return 1

    except Exception as e:
        logger.error(f"\n❌ ERROR: Unexpected error: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
