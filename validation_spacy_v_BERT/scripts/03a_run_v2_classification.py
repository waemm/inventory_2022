#!/usr/bin/env python3
"""
Script 03a: Run V2 BERT Classification
========================================

Purpose:
    Run V2 BERT classifier on validation sample for comparison study.
    Uses the existing src/class_predict.py with proper paths and parameters.

Usage:
    cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT
    source ../biodata_modern_env/bin/activate
    python scripts/03a_run_v2_classification.py

    For testing with small sample:
    TEST_MODE=True python scripts/03a_run_v2_classification.py

Inputs:
    - results/validation/sample/validation_sample_with_abstracts.csv
    - ../../out/original_model/article_classifier.pt

Outputs:
    - results/validation/classification/v2_classification_results.csv
    - logs/03a_run_v2_classification.log

Environment: biodata_modern_env (Python 3.11.9, PyTorch 2.1.0)

Author: Phase 1 Validation Study
Date: 2025-11-13
"""

import sys
import os
import pandas as pd
import torch
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# Also add src directory for inventory_utils imports
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.class_predict import get_dataloaders, predict, Args
from inventory_utils.filing import get_classif_model
from inventory_utils.runtime import get_torch_device
from datasets import ClassLabel

# ============================================================================
# CONFIGURATION
# ============================================================================

# TEST_MODE: Set to True for quick testing (10-15 papers)
#            Set to False for full validation (all papers in sample)
TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
SESSION_ID = os.environ.get('SESSION_ID', '')
if not SESSION_ID:
    # Generate session ID if not provided (without _test suffix - TEST_MODE just limits processing)
    import random
    import string
    from datetime import datetime
    SESSION_ID = f"{datetime.now().strftime('%Y-%m-%d')}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"

TEST_SIZE = 15 if TEST_MODE else None

if TEST_MODE:
    print("\n🧪 TEST MODE ENABLED")
    print(f"   Will process first {TEST_SIZE} papers\n")
else:
    print("\n🚀 PRODUCTION MODE")
    print("   Will process all papers in validation sample\n")

# Paths (relative to validation_spacy_v_BERT/) - use _test suffix in TEST_MODE
VALIDATION_ROOT = Path(__file__).parent.parent
output_suffix = f"_{SESSION_ID}" if SESSION_ID else ("_test" if TEST_MODE else "")
SAMPLE_FILE = VALIDATION_ROOT / f"results/validation/sample/validation_sample_with_abstracts{output_suffix}.csv"
OUTPUT_DIR = VALIDATION_ROOT / "results/validation/classification"
OUTPUT_FILE = OUTPUT_DIR / f"v2_classification_results{output_suffix}.csv"
LOG_FILE = VALIDATION_ROOT / "logs/03a_run_v2_classification.log"

# Model path (relative to project root)
MODEL_PATH = PROJECT_ROOT / "out/original_model/article_classifier.pt"

# Model parameters (matching training configuration)
MAX_LEN = 256
BATCH_SIZE = 8
PREDICTIVE_FIELD = 'title_abstract'
DESCRIPTIVE_LABELS = ['not-bio-resource', 'bio-resource']

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

def prepare_input_file(sample_df, temp_file_path):
    """
    Prepare input file in the format expected by class_predict.py.

    Args:
        sample_df: DataFrame with validation sample
        temp_file_path: Path to save temporary input file

    Returns:
        Path to prepared input file
    """
    logger.info("📝 Preparing input file for V2 classifier...")

    # Identify ID and text columns
    id_col = None
    for col in ['publication_id', 'pubmed_id', 'PMID', 'pmid', 'id']:
        if col in sample_df.columns:
            id_col = col
            break

    if not id_col:
        raise ValueError(f"No ID column found. Available: {list(sample_df.columns)}")

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

    # Clean text
    input_df = input_df.replace(r'\n', ' ', regex=True)
    input_df = input_df.replace(r'\t', ' ', regex=True)

    # Save to temp file
    input_df.to_csv(temp_file_path, index=False, encoding='utf-8')

    logger.info(f"✓ Prepared {len(input_df)} papers for classification")
    logger.info(f"  - Title column: {title_col}")
    logger.info(f"  - Abstract column: {abstract_col}")
    logger.info(f"  - Papers with abstracts: {(input_df['abstract'] != '').sum()}")

    return temp_file_path

def run_classification(input_file_path, model_path, device):
    """
    Run V2 BERT classification on input file.

    Args:
        input_file_path: Path to input CSV
        model_path: Path to model checkpoint
        device: Torch device

    Returns:
        DataFrame with predictions
    """
    logger.info("🤖 Loading V2 BERT model...")

    # Load model and dataloader with proper file handle management
    # Open files, create dataloader, then close handles before prediction
    with open(model_path, 'rb') as checkpoint_file:
        model, model_name = get_classif_model(checkpoint_file, device)

    logger.info(f"✓ Model loaded: {model_name}")
    logger.info(f"  Device: {device}")

    # Create Args object with proper file handle
    # Note: get_dataloaders() reads the file immediately, so we can close it after
    with open(input_file_path, 'rt', encoding='ISO-8859-1') as infile:
        args = Args(
            checkpoint=model_path.open('rb'),  # Create new file handle for Args
            infile=infile,
            out_dir=str(OUTPUT_DIR),
            predictive_field=PREDICTIVE_FIELD,
            descriptive_labels=DESCRIPTIVE_LABELS,
            max_len=MAX_LEN,
            batch_size=BATCH_SIZE
        )

        # Get dataloader (reads from infile immediately)
        logger.info(f"🔄 Creating dataloader (batch_size={BATCH_SIZE}, max_len={MAX_LEN})...")
        dataloader = get_dataloaders(args, model_name)
        logger.info(f"✓ Dataloader ready with {len(dataloader)} batches")

        # Close the checkpoint file handle from Args
        args.checkpoint.close()

    # File handles are now closed, but dataloader has already read all data

    # Run predictions
    logger.info("🔮 Running predictions...")
    class_labels = ClassLabel(num_classes=2, names=DESCRIPTIVE_LABELS)

    # Load input data for merging with predictions
    df = pd.read_csv(input_file_path, encoding='ISO-8859-1', dtype=str)
    df = df.fillna('')
    df = df[~df.duplicated('id')]
    df = df[df['id'] != '']

    # Predict
    predicted_labels = predict(model, dataloader, class_labels, device)
    df['predicted_label'] = predicted_labels

    logger.info(f"✓ Predictions complete for {len(df)} papers")

    return df

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("SCRIPT 03a: V2 BERT CLASSIFICATION")
    logger.info("=" * 70)

    start_time = datetime.now()

    # ------------------------------------------------------------------------
    # 1. Validate inputs
    # ------------------------------------------------------------------------
    logger.info("\n🔍 Validating inputs...")

    # Use local variable to avoid UnboundLocalError
    sample_file = SAMPLE_FILE

    # Fail fast if expected file doesn't exist (no fallback discovery)
    if not sample_file.exists():
        logger.error(f"❌ Sample file not found: {sample_file}")
        logger.error("Please run script 02 first: python scripts/02_fetch_abstracts.py")
        if SESSION_ID:
            logger.error(f"   Expected session: {SESSION_ID}")
        return 1

    if not MODEL_PATH.exists():
        logger.error(f"❌ Model not found: {MODEL_PATH}")
        logger.error("Expected V2 BERT classification model")
        return 1

    logger.info(f"✓ Sample file: {sample_file}")
    logger.info(f"✓ Model: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024 / 1024:.1f} MB)")

    # ------------------------------------------------------------------------
    # 2. Load validation sample
    # ------------------------------------------------------------------------
    logger.info("\n📚 Loading validation sample...")
    df_sample = pd.read_csv(sample_file)
    logger.info(f"✓ Loaded {len(df_sample)} papers")

    # Apply TEST_MODE if enabled
    if TEST_MODE:
        logger.info(f"🧪 TEST_MODE: Using first {TEST_SIZE} papers")
        df_sample = df_sample.head(TEST_SIZE)
        logger.info(f"✓ Test sample size: {len(df_sample)} papers")

    # Check for abstracts
    has_abstract = df_sample['abstract'].notna() & (df_sample['abstract'] != '')
    logger.info(f"  - Papers with abstracts: {has_abstract.sum()}/{len(df_sample)} ({100*has_abstract.sum()/len(df_sample):.1f}%)")

    # ------------------------------------------------------------------------
    # 3. Prepare input file
    # ------------------------------------------------------------------------
    temp_input = OUTPUT_DIR / "temp_v2_input.csv"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prepare_input_file(df_sample, temp_input)

    # ------------------------------------------------------------------------
    # 4. Get device and run classification
    # ------------------------------------------------------------------------
    logger.info("\n🖥️  Detecting compute device...")
    device = get_torch_device()
    logger.info(f"✓ Using device: {device}")

    predictions_df = run_classification(temp_input, MODEL_PATH, device)

    # ------------------------------------------------------------------------
    # 5. Merge predictions with original sample data
    # ------------------------------------------------------------------------
    logger.info("\n🔗 Merging predictions with sample data...")

    # Identify ID column in original sample
    id_col = None
    for col in ['publication_id', 'pubmed_id', 'PMID', 'pmid', 'id']:
        if col in df_sample.columns:
            id_col = col
            break

    df_sample['id_str'] = df_sample[id_col].astype(str)
    predictions_df['id_str'] = predictions_df['id'].astype(str)

    # Merge
    df_results = df_sample.merge(
        predictions_df[['id_str', 'predicted_label']],
        on='id_str',
        how='left'
    )

    df_results = df_results.drop(columns=['id_str'])

    logger.info(f"✓ Merged {len(df_results)} papers")

    # ------------------------------------------------------------------------
    # 6. Calculate summary statistics
    # ------------------------------------------------------------------------
    predicted_positive = (df_results['predicted_label'] == 'bio-resource').sum()
    predicted_negative = (df_results['predicted_label'] == 'not-bio-resource').sum()

    logger.info(f"\n{'=' * 70}")
    logger.info("SUMMARY STATISTICS")
    logger.info(f"{'=' * 70}")
    logger.info(f"Total papers:          {len(df_results)}")
    logger.info(f"Predicted positive:    {predicted_positive} ({100*predicted_positive/len(df_results):.1f}%)")
    logger.info(f"Predicted negative:    {predicted_negative} ({100*predicted_negative/len(df_results):.1f}%)")

    # ------------------------------------------------------------------------
    # 7. Save results
    # ------------------------------------------------------------------------
    logger.info(f"\n💾 Saving results...")

    # Clean results
    df_results = df_results.replace(r'\n', ' ', regex=True)
    df_results.to_csv(OUTPUT_FILE, index=False)

    logger.info(f"✓ Saved to: {OUTPUT_FILE}")
    logger.info(f"  Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

    # Clean up temp file
    if temp_input.exists():
        temp_input.unlink()
        logger.info("✓ Cleaned up temporary files")

    # ------------------------------------------------------------------------
    # 8. Final report
    # ------------------------------------------------------------------------
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ SCRIPT 03a COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Log saved to: {LOG_FILE}")
    logger.info(f"Results saved to: {OUTPUT_FILE}")
    logger.info(f"\nNext step: Run PyCaret classification")
    logger.info(f"  python scripts/03b_run_pycaret_classification.py")
    logger.info(f"{'=' * 70}")

    return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
