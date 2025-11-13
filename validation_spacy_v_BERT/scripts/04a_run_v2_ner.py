#!/usr/bin/env python3
"""
Script 04a: Run V2 BERT NER
============================

Purpose:
    Run V2 BERT NER on validation sample for comparison study.
    Extracts biodata resource entities (COM, FUL, ABB labels).

Usage:
    cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT
    source ../biodata_modern_env/bin/activate
    python scripts/04a_run_v2_ner.py

Inputs:
    - results/validation/sample/validation_sample_with_abstracts.csv
    - ../../out/ner_train_out/article_ner_v2.pt

Outputs:
    - results/validation/ner/v2_ner_results.csv
    - logs/04a_run_v2_ner.log

Environment: biodata_modern_env (Python 3.11.9, PyTorch 2.1.0)

Author: Phase 1 Validation Study
Date: 2025-11-13
"""

import sys
import pandas as pd
import torch
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ner_predict import predict
from inventory_utils.filing import get_ner_model
from inventory_utils.runtime import get_torch_device

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths (relative to validation_spacy_v_BERT/)
VALIDATION_ROOT = Path(__file__).parent.parent
SAMPLE_FILE = VALIDATION_ROOT / "results/validation/sample/validation_sample_with_abstracts.csv"
OUTPUT_DIR = VALIDATION_ROOT / "results/validation/ner"
OUTPUT_FILE = OUTPUT_DIR / "v2_ner_results.csv"
LOG_FILE = VALIDATION_ROOT / "logs/04a_run_v2_ner.log"

# Model path (relative to project root)
MODEL_PATH = PROJECT_ROOT / "out/ner_train_out/article_ner_v2.pt"

# ============================================================================
# LOGGING SETUP
# ============================================================================

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# FUNCTIONS
# ============================================================================

def prepare_input_dataframe(sample_df):
    """
    Prepare input DataFrame in the format expected by ner_predict.predict().

    Expected columns: id, title_abstract, publication_date

    Args:
        sample_df: DataFrame with validation sample

    Returns:
        DataFrame ready for V2 NER prediction
    """
    logger.info("📝 Preparing input DataFrame for V2 NER...")

    # Identify ID column
    id_col = None
    for col in ['publication_id', 'pubmed_id', 'PMID', 'pmid', 'id']:
        if col in sample_df.columns:
            id_col = col
            break

    if not id_col:
        raise ValueError(f"No ID column found. Available: {list(sample_df.columns)}")

    # Identify text columns
    title_col = None
    for col in ['title', 'title_test', 'title_meta']:
        if col in sample_df.columns:
            title_col = col
            break

    abstract_col = 'abstract' if 'abstract' in sample_df.columns else None

    # Create input dataframe
    input_df = pd.DataFrame()
    input_df['id'] = sample_df[id_col].astype(str)
    input_df['title'] = sample_df[title_col].fillna('') if title_col else ''
    input_df['abstract'] = sample_df[abstract_col].fillna('') if abstract_col else ''
    input_df['title_abstract'] = input_df['title'] + ' ' + input_df['abstract']

    # Publication date (use empty string if not available)
    pub_date_col = None
    for col in ['publication_date', 'pubYear', 'pub_year', 'year']:
        if col in sample_df.columns:
            pub_date_col = col
            break

    input_df['publication_date'] = sample_df[pub_date_col].astype(str) if pub_date_col else ''

    # Clean text
    input_df = input_df.replace(r'\n', ' ', regex=True)
    input_df = input_df.replace(r'\t', ' ', regex=True)

    logger.info(f"✓ Prepared {len(input_df)} papers for NER extraction")
    logger.info(f"  - Title column: {title_col}")
    logger.info(f"  - Abstract column: {abstract_col}")
    logger.info(f"  - Papers with abstracts: {(input_df['abstract'] != '').sum()}")

    return input_df

def run_v2_ner(input_df, model_path, device):
    """
    Run V2 BERT NER on input DataFrame.

    Args:
        input_df: DataFrame with id, title_abstract, publication_date
        model_path: Path to model checkpoint
        device: Torch device

    Returns:
        DataFrame with entity extractions
    """
    logger.info("🤖 Loading V2 BERT NER model...")

    # Load model
    with open(model_path, 'rb') as f:
        model, tokenizer = get_ner_model(f, device)

    logger.info(f"✓ Model loaded")
    logger.info(f"  Device: {device}")

    # Run predictions
    logger.info(f"🔮 Running NER predictions on {len(input_df)} papers...")
    logger.info(f"   This may take several minutes...")

    predictions_df = predict(model, tokenizer, input_df, device)

    logger.info(f"✓ NER predictions complete")
    logger.info(f"  Total entities extracted: {len(predictions_df)}")

    return predictions_df

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("SCRIPT 04a: V2 BERT NER")
    logger.info("=" * 70)

    start_time = datetime.now()

    # ------------------------------------------------------------------------
    # 1. Validate inputs
    # ------------------------------------------------------------------------
    logger.info("\n🔍 Validating inputs...")

    if not SAMPLE_FILE.exists():
        logger.error(f"❌ Sample file not found: {SAMPLE_FILE}")
        logger.error("Please run script 02 first: python scripts/02_fetch_abstracts.py")
        return 1

    if not MODEL_PATH.exists():
        logger.error(f"❌ Model not found: {MODEL_PATH}")
        logger.error("Expected V2 BERT NER model")
        return 1

    logger.info(f"✓ Sample file: {SAMPLE_FILE}")
    logger.info(f"✓ Model: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024 / 1024:.1f} MB)")

    # ------------------------------------------------------------------------
    # 2. Load validation sample
    # ------------------------------------------------------------------------
    logger.info("\n📚 Loading validation sample...")
    df_sample = pd.read_csv(SAMPLE_FILE)
    logger.info(f"✓ Loaded {len(df_sample)} papers")

    # Check for abstracts
    has_abstract = df_sample['abstract'].notna() & (df_sample['abstract'] != '')
    logger.info(f"  - Papers with abstracts: {has_abstract.sum()}/{len(df_sample)} ({100*has_abstract.sum()/len(df_sample):.1f}%)")

    # ------------------------------------------------------------------------
    # 3. Prepare input DataFrame
    # ------------------------------------------------------------------------
    input_df = prepare_input_dataframe(df_sample)

    # ------------------------------------------------------------------------
    # 4. Get device and run NER
    # ------------------------------------------------------------------------
    logger.info("\n🖥️  Detecting compute device...")
    device = get_torch_device()
    logger.info(f"✓ Using device: {device}")

    predictions_df = run_v2_ner(input_df, MODEL_PATH, device)

    # ------------------------------------------------------------------------
    # 5. Calculate summary statistics
    # ------------------------------------------------------------------------
    logger.info(f"\n{'=' * 70}")
    logger.info("SUMMARY STATISTICS")
    logger.info(f"{'=' * 70}")
    logger.info(f"Total papers:              {len(df_sample)}")
    logger.info(f"Total entities extracted:  {len(predictions_df)}")
    logger.info(f"Papers with entities:      {predictions_df['ID'].nunique()}/{len(df_sample)}")
    logger.info(f"Avg entities per paper:    {len(predictions_df)/len(df_sample):.2f}")

    # Entity type breakdown
    if 'label' in predictions_df.columns:
        logger.info(f"\nEntity types:")
        for label, count in predictions_df['label'].value_counts().items():
            logger.info(f"  - {label}: {count} ({100*count/len(predictions_df):.1f}%)")

    # ------------------------------------------------------------------------
    # 6. Save results
    # ------------------------------------------------------------------------
    logger.info(f"\n💾 Saving results...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clean results
    predictions_df = predictions_df.replace(r'\n', ' ', regex=True)
    predictions_df.to_csv(OUTPUT_FILE, index=False)

    logger.info(f"✓ Saved to: {OUTPUT_FILE}")
    logger.info(f"  Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    logger.info(f"  Columns: {list(predictions_df.columns)}")

    # ------------------------------------------------------------------------
    # 7. Final report
    # ------------------------------------------------------------------------
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ SCRIPT 04a COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Log saved to: {LOG_FILE}")
    logger.info(f"Results saved to: {OUTPUT_FILE}")
    logger.info(f"\nNext step: Run spaCy Hybrid NER")
    logger.info(f"  python scripts/04b_run_spacy_ner.py")
    logger.info(f"{'=' * 70}")

    return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    exit(main())
