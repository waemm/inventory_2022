#!/usr/bin/env python3
"""
Script 07a: Run Phase 2 V2 BERT NER
====================================

Purpose:
    Run V2 BERT NER on Phase 2 classified positives.
    Based on script 04a but for Phase 2 full-scale evaluation.

Usage:
    cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT
    source ../biodata_modern_env/bin/activate
    python scripts/07a_run_phase2_v2_ner.py

    For testing with small sample:
    TEST_MODE=True python scripts/07a_run_phase2_v2_ner.py

Inputs:
    - results/phase2/classification/v2_classification_150k.csv (or pycaret)
    - ../../out/original_model/named_entity_recognition.pt

Outputs:
    - results/phase2/ner/v2_ner_150k.csv
    - logs/07a_run_phase2_v2_ner.log

Environment: biodata_modern_env (Python 3.11.9, PyTorch 2.1.0)

Author: Phase 2 Full Scale Study
Date: 2025-11-14
"""

import sys
import os
import pandas as pd
import torch
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.ner_predict import predict
from inventory_utils.filing import get_ner_model
from inventory_utils.runtime import get_torch_device

# ============================================================================
# CONFIGURATION
# ============================================================================

TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
SESSION_ID = os.environ.get('SESSION_ID', '')
if not SESSION_ID:
    import random
    import string
    SESSION_ID = f"{datetime.now().strftime('%Y-%m-%d')}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"

TEST_SIZE = 100 if TEST_MODE else None

if TEST_MODE:
    print("\n🧪 TEST MODE ENABLED")
    print(f"   Will process first {TEST_SIZE} positive papers\n")
else:
    print("\n🚀 PRODUCTION MODE")
    print("   Will process all positives from classification\n")

# Paths
VALIDATION_ROOT = Path(__file__).parent.parent

# Input: Try to find classification results
output_suffix = f"_{SESSION_ID}" if SESSION_ID else ("_test" if TEST_MODE else "")
CLASSIFICATION_FILE = None
for candidate in [
    VALIDATION_ROOT / f"results/phase2/classification/v2_classification_150k{output_suffix}.csv",
    VALIDATION_ROOT / f"results/phase2/classification/pycaret_classification_150k{output_suffix}.csv",
    VALIDATION_ROOT / f"results/phase2/classification/v2_classification_150k.csv",
    VALIDATION_ROOT / f"results/phase2/classification/pycaret_classification_150k.csv",
]:
    if candidate.exists():
        CLASSIFICATION_FILE = candidate
        break

OUTPUT_DIR = VALIDATION_ROOT / "results/phase2/ner"
OUTPUT_FILE = OUTPUT_DIR / f"v2_ner_150k{output_suffix}.csv"
LOG_FILE = VALIDATION_ROOT / f"logs/07a_run_phase2_v2_ner.log"

MODEL_PATH = PROJECT_ROOT / "out/original_model/named_entity_recognition.pt"

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

def prepare_input_dataframe(df):
    """Prepare input DataFrame for V2 NER"""
    logger.info("📝 Preparing input DataFrame for V2 NER...")

    # Identify ID column
    id_col = None
    for col in ['publication_id', 'id', 'pmid', 'PMID']:
        if col in df.columns:
            id_col = col
            break

    if not id_col:
        raise ValueError(f"No ID column found. Available: {list(df.columns)}")

    # Create input dataframe
    input_df = pd.DataFrame()
    input_df['id'] = df[id_col].astype(str)
    input_df['title'] = df['title'].fillna('') if 'title' in df.columns else ''
    input_df['abstract'] = df['abstract'].fillna('') if 'abstract' in df.columns else ''
    input_df['title_abstract'] = input_df['title'] + ' ' + input_df['abstract']

    # Publication date
    pub_date_col = None
    for col in ['publication_date', 'pubYear', 'pub_year', 'year']:
        if col in df.columns:
            pub_date_col = col
            break

    input_df['publication_date'] = df[pub_date_col].astype(str) if pub_date_col else ''

    # Clean text
    input_df = input_df.replace(r'\n', ' ', regex=True)
    input_df = input_df.replace(r'\t', ' ', regex=True)

    logger.info(f"✓ Prepared {len(input_df):,} papers for NER")
    logger.info(f"  - Papers with abstracts: {(input_df['abstract'] != '').sum():,}")

    return input_df

def run_v2_ner(input_df, model_path, device):
    """Run V2 BERT NER"""
    logger.info("🤖 Loading V2 BERT NER model...")

    with open(model_path, 'rb') as f:
        model, model_name, tokenizer = get_ner_model(f, device)

    logger.info(f"✓ Model loaded")
    logger.info(f"  Device: {device}")

    logger.info(f"🔮 Running NER predictions on {len(input_df):,} papers...")
    logger.info(f"   This may take 30-60 minutes for full dataset...")

    predictions_df = predict(model, tokenizer, input_df, device)

    logger.info(f"✓ NER complete")
    logger.info(f"  Total entities: {len(predictions_df):,}")

    return predictions_df

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    try:
        logger.info("=" * 70)
        logger.info("SCRIPT 07a: PHASE 2 V2 BERT NER")
        logger.info("=" * 70)

        start_time = datetime.now()

        # ------------------------------------------------------------------------
        # 1. Validate inputs
        # ------------------------------------------------------------------------
        logger.info("\n🔍 Validating inputs...")

        if not CLASSIFICATION_FILE:
            logger.error(f"❌ No classification results found in results/phase2/classification/")
            logger.error("Please run script 06a or 06b first")
            return 1

        if not MODEL_PATH.exists():
            logger.error(f"❌ Model not found: {MODEL_PATH}")
            return 1

        logger.info(f"✓ Classification results: {CLASSIFICATION_FILE}")
        logger.info(f"✓ Model: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024 / 1024:.1f} MB)")

        # Validate and create output directory early
        logger.info(f"✓ Output directory: {OUTPUT_DIR}")
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.error(f"❌ Cannot create output directory: {e}")
            return 1

        # ------------------------------------------------------------------------
        # 2. Load classification results and filter positives
        # ------------------------------------------------------------------------
        logger.info("\n📚 Loading classification results...")
        try:
            df_classif = pd.read_csv(CLASSIFICATION_FILE, low_memory=False)
            logger.info(f"✓ Loaded {len(df_classif):,} papers")
        except pd.errors.ParserError as e:
            logger.error(f"❌ Failed to parse CSV: {e}")
            return 1
        except MemoryError:
            logger.error(f"❌ Out of memory loading {CLASSIFICATION_FILE.stat().st_size / 1024**3:.1f} GB file")
            return 1

        # Filter for positives
        if 'predicted_label' in df_classif.columns:
            # V2 classification format
            df_positives = df_classif[df_classif['predicted_label'] == 'bio-resource'].copy()
        elif 'prediction_label' in df_classif.columns:
            # PyCaret format
            df_positives = df_classif[df_classif['prediction_label'] == 1].copy()
        else:
            logger.error(f"❌ No prediction column found in: {CLASSIFICATION_FILE}")
            return 1

        logger.info(f"✓ Filtered {len(df_positives):,} positives ({100*len(df_positives)/len(df_classif):.1f}%)")

        # Apply TEST_MODE if enabled
        if TEST_MODE:
            logger.info(f"🧪 TEST_MODE: Using first {TEST_SIZE} positives")
            df_positives = df_positives.head(TEST_SIZE)
            logger.info(f"✓ Test sample size: {len(df_positives):,} papers")

        # ------------------------------------------------------------------------
        # 3. Prepare input DataFrame
        # ------------------------------------------------------------------------
        input_df = prepare_input_dataframe(df_positives)

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
        logger.info(f"Total papers:              {len(df_positives):,}")
        logger.info(f"Total entities extracted:  {len(predictions_df):,}")
        logger.info(f"Papers with entities:      {predictions_df['ID'].nunique():,}/{len(df_positives):,}")
        logger.info(f"Avg entities per paper:    {len(predictions_df)/len(df_positives):.2f}")

        if 'label' in predictions_df.columns:
            logger.info(f"\nEntity types:")
            for label, count in predictions_df['label'].value_counts().items():
                logger.info(f"  - {label}: {count:,} ({100*count/len(predictions_df):.1f}%)")

        # ------------------------------------------------------------------------
        # 6. Save results
        # ------------------------------------------------------------------------
        logger.info(f"\n💾 Saving results...")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        predictions_df = predictions_df.replace(r'\n', ' ', regex=True)
        predictions_df.to_csv(OUTPUT_FILE, index=False)

        logger.info(f"✓ Saved to: {OUTPUT_FILE}")
        logger.info(f"  Size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")

        # ------------------------------------------------------------------------
        # 7. Final report
        # ------------------------------------------------------------------------
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info(f"\n{'=' * 70}")
        logger.info(f"✅ SCRIPT 07a COMPLETE")
        logger.info(f"{'=' * 70}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Log saved to: {LOG_FILE}")
        logger.info(f"Results saved to: {OUTPUT_FILE}")
        logger.info(f"\nNext step: Run spaCy Hybrid NER")
        logger.info(f"  python scripts/07b_run_phase2_spacy_ner.py")
        logger.info(f"{'=' * 70}")

        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user (Ctrl+C)")
        return 130
    except Exception as e:
        logger.exception(f"\n❌ Unexpected error occurred")
        return 1


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
