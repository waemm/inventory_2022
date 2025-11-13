#!/usr/bin/env python3
"""
Select Validation Sample for Model Comparison
==============================================

Selects 100-125 unique resource papers for manual validation study:
- 50 global core bioresources (is_global_core_biodata_resource=1)
- 50-75 other validated resources
- Removes training overlap
- Saves to results/validation/sample/validation_sample.csv

Usage:
    python scripts/01_select_validation_sample.py
"""

import sys
import pandas as pd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
GROUND_TRUTH_PATH = Path("/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv")
OUTPUT_DIR = PROJECT_ROOT / "results" / "validation" / "sample"
OUTPUT_FILE = OUTPUT_DIR / "validation_sample.csv"

# Training data paths (to remove overlap)
CLASSIF_TRAIN_PATH = PROJECT_ROOT / "data" / "classif_splits_full" / "train_paper_classif.csv"
NER_TRAIN_PATH = PROJECT_ROOT / "data" / "ner_splits_full" / "train.csv"

def load_training_ids():
    """Load all training paper IDs to exclude from validation sample"""
    training_ids = set()

    # Load classification training IDs
    if CLASSIF_TRAIN_PATH.exists():
        logger.info(f"Loading classification training IDs from: {CLASSIF_TRAIN_PATH}")
        df_classif = pd.read_csv(CLASSIF_TRAIN_PATH)

        # Check for ID column
        id_col = None
        for col in ['id', 'pubmed_id', 'ID', 'PMID']:
            if col in df_classif.columns:
                id_col = col
                break

        if id_col:
            ids = df_classif[id_col].dropna().astype(str).unique()
            training_ids.update(ids)
            logger.info(f"   Found {len(ids)} classification training IDs")

    # Load NER training IDs
    if NER_TRAIN_PATH.exists():
        logger.info(f"Loading NER training IDs from: {NER_TRAIN_PATH}")
        df_ner = pd.read_csv(NER_TRAIN_PATH)

        # Check for ID column
        id_col = None
        for col in ['id', 'pubmed_id', 'ID', 'PMID']:
            if col in df_ner.columns:
                id_col = col
                break

        if id_col:
            ids = df_ner[id_col].dropna().astype(str).unique()
            training_ids.update(ids)
            logger.info(f"   Found {len(ids)} NER training IDs")

    logger.info(f"Total training IDs to exclude: {len(training_ids)}")
    return training_ids

def load_ground_truth():
    """Load bioresource_papers_latest.csv"""
    logger.info(f"Loading ground truth from: {GROUND_TRUTH_PATH}")

    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(f"Ground truth file not found: {GROUND_TRUTH_PATH}")

    df = pd.read_csv(GROUND_TRUTH_PATH)
    logger.info(f"   Loaded {len(df)} papers")
    logger.info(f"   Columns: {list(df.columns)}")

    return df

def select_sample(df_ground_truth, training_ids, n_global_core=50, n_other=50):
    """
    Select stratified sample:
    - n_global_core papers with is_global_core_biodata_resource=1
    - n_other papers with is_global_core_biodata_resource=0

    Excludes training papers and ensures unique resources.
    """
    logger.info("\n" + "="*60)
    logger.info("SAMPLE SELECTION")
    logger.info("="*60)

    # Convert ID column to string for comparison
    id_col = None
    for col in ['publication_id', 'pubmed_id', 'PMID', 'id']:
        if col in df_ground_truth.columns:
            id_col = col
            break

    if not id_col:
        raise ValueError(f"No ID column found in ground truth. Available columns: {list(df_ground_truth.columns)}")

    logger.info(f"Using ID column: {id_col}")
    df_ground_truth[id_col] = df_ground_truth[id_col].astype(str)

    # Remove training overlap
    initial_count = len(df_ground_truth)
    df_filtered = df_ground_truth[~df_ground_truth[id_col].isin(training_ids)].copy()
    removed_count = initial_count - len(df_filtered)
    logger.info(f"Removed {removed_count} training papers")
    logger.info(f"Remaining papers: {len(df_filtered)}")

    # Check for global core column
    if 'is_global_core_biodata_resource' not in df_filtered.columns:
        logger.warning("Column 'is_global_core_biodata_resource' not found")
        logger.info(f"Available columns: {list(df_filtered.columns)}")
        # Create dummy column
        df_filtered['is_global_core_biodata_resource'] = 0

    # Select global core papers
    df_global = df_filtered[df_filtered['is_global_core_biodata_resource'] == 1].copy()
    logger.info(f"\nGlobal core papers available: {len(df_global)}")

    if len(df_global) >= n_global_core:
        sample_global = df_global.sample(n=n_global_core, random_state=42)
        logger.info(f"   Selected {n_global_core} global core papers (random sample)")
    else:
        sample_global = df_global
        logger.info(f"   Selected ALL {len(df_global)} global core papers (less than target)")
        n_global_core = len(df_global)

    # Select other papers
    df_other = df_filtered[df_filtered['is_global_core_biodata_resource'] == 0].copy()
    logger.info(f"\nOther papers available: {len(df_other)}")

    if len(df_other) >= n_other:
        sample_other = df_other.sample(n=n_other, random_state=42)
        logger.info(f"   Selected {n_other} other papers (random sample)")
    else:
        sample_other = df_other
        logger.info(f"   Selected ALL {len(df_other)} other papers (less than target)")

    # Combine samples
    sample_df = pd.concat([sample_global, sample_other], ignore_index=True)

    logger.info(f"\n" + "="*60)
    logger.info(f"FINAL SAMPLE")
    logger.info("="*60)
    logger.info(f"Global core papers: {n_global_core}")
    logger.info(f"Other papers: {len(sample_other)}")
    logger.info(f"Total papers: {len(sample_df)}")

    # Count unique resources
    if 'resource_short_name' in sample_df.columns:
        unique_resources = sample_df['resource_short_name'].nunique()
        logger.info(f"Unique resources: {unique_resources}")

    return sample_df

def save_sample(sample_df, output_file):
    """Save validation sample to CSV"""
    logger.info(f"\nSaving sample to: {output_file}")

    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    sample_df.to_csv(output_file, index=False)
    logger.info(f"✅ Sample saved successfully")
    logger.info(f"   {len(sample_df)} papers")
    logger.info(f"   {output_file.stat().st_size / 1024:.1f} KB")

    # Print sample statistics
    logger.info("\n" + "="*60)
    logger.info("SAMPLE STATISTICS")
    logger.info("="*60)

    if 'is_global_core_biodata_resource' in sample_df.columns:
        global_count = (sample_df['is_global_core_biodata_resource'] == 1).sum()
        other_count = (sample_df['is_global_core_biodata_resource'] == 0).sum()
        logger.info(f"Global core: {global_count} papers")
        logger.info(f"Other: {other_count} papers")

    if 'resource_short_name' in sample_df.columns:
        top_resources = sample_df['resource_short_name'].value_counts().head(10)
        logger.info("\nTop 10 resources:")
        for resource, count in top_resources.items():
            logger.info(f"   {resource}: {count} papers")

def main():
    """Main execution"""
    logger.info("\n" + "="*60)
    logger.info("VALIDATION SAMPLE SELECTION")
    logger.info("="*60)
    logger.info(f"Project root: {PROJECT_ROOT}")

    try:
        # Load training IDs to exclude
        training_ids = load_training_ids()

        # Load ground truth
        df_ground_truth = load_ground_truth()

        # Select sample
        sample_df = select_sample(df_ground_truth, training_ids, n_global_core=50, n_other=50)

        # Save sample
        save_sample(sample_df, OUTPUT_FILE)

        logger.info("\n" + "="*60)
        logger.info("✅ SAMPLE SELECTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Next step: Fetch abstracts from EPMC")
        logger.info(f"   python scripts/02_fetch_abstracts.py")

        return 0

    except Exception as e:
        logger.error(f"\n❌ Error during sample selection: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
