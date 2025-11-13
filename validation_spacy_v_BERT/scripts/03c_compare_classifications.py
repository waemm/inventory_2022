#!/usr/bin/env python3
"""
Script 03c: Compare Classification Results
===========================================

Purpose:
    Compare predictions from V2 BERT classifier and both PyCaret models.
    Analyzes agreement/disagreement patterns and generates comparison report.

Models Compared:
    1. V2 BERT Classifier (trained on title+abstract)
    2. PyCaret test_mode_true (92 metadata features)
    3. PyCaret test_mode_false (112 metadata features)

Usage:
    cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT
    source ../biodata_modern_env/bin/activate  # Any environment works
    python scripts/03c_compare_classifications.py

Inputs:
    - results/validation/classification/v2_classification_results.csv
    - results/validation/classification/pycaret_test_mode_true_results.csv
    - results/validation/classification/pycaret_test_mode_false_results.csv

Outputs:
    - results/validation/classification/classification_comparison.csv
    - results/validation/classification/classification_comparison_report.md
    - logs/03c_compare_classifications.log

Author: Phase 1 Validation Study
Date: 2025-11-13
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from collections import Counter

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths (relative to validation_spacy_v_BERT/)
VALIDATION_ROOT = Path(__file__).parent.parent
CLASSIFICATION_DIR = VALIDATION_ROOT / "results/validation/classification"

# Input files
V2_RESULTS = CLASSIFICATION_DIR / "v2_classification_results.csv"
PYCARET_TRUE_RESULTS = CLASSIFICATION_DIR / "pycaret_test_mode_true_results.csv"
PYCARET_FALSE_RESULTS = CLASSIFICATION_DIR / "pycaret_test_mode_false_results.csv"

# Output files
OUTPUT_CSV = CLASSIFICATION_DIR / "classification_comparison.csv"
OUTPUT_REPORT = CLASSIFICATION_DIR / "classification_comparison_report.md"
LOG_FILE = VALIDATION_ROOT / "logs/03c_compare_classifications.log"

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

def normalize_prediction(pred):
    """
    Normalize prediction to binary 0/1.

    Args:
        pred: Prediction value (could be 'bio-resource', 'not-bio-resource', 0, 1, etc.)

    Returns:
        int: 0 for negative, 1 for positive
    """
    if pd.isna(pred):
        return None

    # String labels
    if isinstance(pred, str):
        if 'bio-resource' in pred.lower() and 'not-bio-resource' not in pred.lower():
            return 1
        else:
            return 0

    # Numeric
    try:
        return int(pred)
    except:
        return None

def load_predictions(file_path, model_name):
    """
    Load predictions from CSV file.

    Args:
        file_path: Path to predictions CSV
        model_name: Name of model (for column naming)

    Returns:
        DataFrame with id, title, and normalized prediction
    """
    logger.info(f"📂 Loading {model_name} predictions from {file_path.name}...")

    if not file_path.exists():
        logger.error(f"❌ File not found: {file_path}")
        return None

    df = pd.read_csv(file_path)
    logger.info(f"   Loaded {len(df)} predictions")

    # Identify columns
    id_col = None
    for col in ['id', 'pmid', 'publication_id', 'pubmed_id', 'PMID']:
        if col in df.columns:
            id_col = col
            break

    pred_col = None
    for col in ['predicted_label', 'prediction_label', 'prediction']:
        if col in df.columns:
            pred_col = col
            break

    if not id_col or not pred_col:
        logger.error(f"❌ Required columns not found in {file_path}")
        logger.error(f"   Available columns: {list(df.columns)}")
        return None

    # Create normalized dataframe
    df_norm = pd.DataFrame()
    df_norm['id'] = df[id_col].astype(str)
    df_norm['title'] = df['title'] if 'title' in df.columns else ''
    df_norm[f'{model_name}_pred'] = df[pred_col].apply(normalize_prediction)

    # Add confidence score if available
    score_col = None
    for col in ['prediction_score', 'score', 'confidence']:
        if col in df.columns:
            score_col = col
            break

    if score_col:
        df_norm[f'{model_name}_score'] = df[score_col]

    # Summary
    n_positive = (df_norm[f'{model_name}_pred'] == 1).sum()
    n_negative = (df_norm[f'{model_name}_pred'] == 0).sum()

    logger.info(f"   ✓ {model_name}: {n_positive} positive, {n_negative} negative")

    return df_norm

def calculate_agreement(df, model1, model2):
    """
    Calculate agreement between two models.

    Args:
        df: DataFrame with predictions
        model1: Name of first model
        model2: Name of second model

    Returns:
        dict with agreement statistics
    """
    col1 = f'{model1}_pred'
    col2 = f'{model2}_pred'

    # Count agreements
    both_positive = ((df[col1] == 1) & (df[col2] == 1)).sum()
    both_negative = ((df[col1] == 0) & (df[col2] == 0)).sum()
    disagree = ((df[col1] != df[col2])).sum()

    total = len(df)
    agreement = both_positive + both_negative
    agreement_rate = agreement / total if total > 0 else 0

    return {
        'model1': model1,
        'model2': model2,
        'total': total,
        'agreement': agreement,
        'agreement_rate': agreement_rate,
        'both_positive': both_positive,
        'both_negative': both_negative,
        'disagree': disagree
    }

def generate_markdown_report(df, agreement_stats, output_file):
    """
    Generate markdown report with comparison results.

    Args:
        df: DataFrame with merged predictions
        agreement_stats: List of agreement statistics
        output_file: Path to save report
    """
    logger.info("\n📝 Generating markdown report...")

    report_lines = []

    # Header
    report_lines.append("# Classification Comparison Report")
    report_lines.append("")
    report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## Overview")
    report_lines.append("")
    report_lines.append("Comparison of classification predictions from three models:")
    report_lines.append("")
    report_lines.append("1. **V2 BERT Classifier**: Trained on title+abstract text")
    report_lines.append("2. **PyCaret test_mode_true**: 92 metadata features")
    report_lines.append("3. **PyCaret test_mode_false**: 112 metadata features (includes MeSH/journal)")
    report_lines.append("")

    # Summary statistics
    report_lines.append("## Summary Statistics")
    report_lines.append("")
    report_lines.append(f"**Total papers**: {len(df)}")
    report_lines.append("")

    # Per-model predictions
    report_lines.append("### Predictions by Model")
    report_lines.append("")
    report_lines.append("| Model | Positive | Negative | Positive Rate |")
    report_lines.append("|-------|----------|----------|---------------|")

    for model in ['v2', 'pycaret_true', 'pycaret_false']:
        col = f'{model}_pred'
        if col in df.columns:
            n_pos = (df[col] == 1).sum()
            n_neg = (df[col] == 0).sum()
            pos_rate = n_pos / len(df) if len(df) > 0 else 0
            report_lines.append(f"| {model} | {n_pos} | {n_neg} | {pos_rate:.1%} |")

    report_lines.append("")

    # Agreement analysis
    report_lines.append("## Pairwise Agreement")
    report_lines.append("")
    report_lines.append("| Model 1 | Model 2 | Agreement Rate | Both Pos | Both Neg | Disagree |")
    report_lines.append("|---------|---------|----------------|----------|----------|----------|")

    for stats in agreement_stats:
        report_lines.append(
            f"| {stats['model1']} | {stats['model2']} | "
            f"{stats['agreement_rate']:.1%} | "
            f"{stats['both_positive']} | "
            f"{stats['both_negative']} | "
            f"{stats['disagree']} |"
        )

    report_lines.append("")

    # Consensus analysis
    report_lines.append("## Consensus Analysis")
    report_lines.append("")

    # Count consensus patterns
    if all(col in df.columns for col in ['v2_pred', 'pycaret_true_pred', 'pycaret_false_pred']):
        all_agree_pos = ((df['v2_pred'] == 1) & (df['pycaret_true_pred'] == 1) & (df['pycaret_false_pred'] == 1)).sum()
        all_agree_neg = ((df['v2_pred'] == 0) & (df['pycaret_true_pred'] == 0) & (df['pycaret_false_pred'] == 0)).sum()
        two_agree_pos = ((df['v2_pred'] + df['pycaret_true_pred'] + df['pycaret_false_pred']) == 2).sum()
        all_disagree = ((df['v2_pred'] + df['pycaret_true_pred'] + df['pycaret_false_pred']) == 1).sum()

        total_consensus = all_agree_pos + all_agree_neg
        consensus_rate = total_consensus / len(df) if len(df) > 0 else 0

        report_lines.append(f"**Full Consensus**: {total_consensus} papers ({consensus_rate:.1%})")
        report_lines.append(f"- All predict positive: {all_agree_pos}")
        report_lines.append(f"- All predict negative: {all_agree_neg}")
        report_lines.append("")
        report_lines.append(f"**Partial Agreement**: {two_agree_pos} papers (2 out of 3 agree)")
        report_lines.append("")
        report_lines.append(f"**Maximum Disagreement**: {all_disagree} papers (only 1 predicts positive)")
        report_lines.append("")

    # Disagreement examples
    report_lines.append("## Disagreement Examples")
    report_lines.append("")
    report_lines.append("### Papers where only V2 predicts positive")
    report_lines.append("")

    v2_only = df[(df['v2_pred'] == 1) & (df['pycaret_true_pred'] == 0) & (df['pycaret_false_pred'] == 0)]
    if len(v2_only) > 0:
        report_lines.append(f"**Count**: {len(v2_only)} papers")
        report_lines.append("")
        for idx, row in v2_only.head(5).iterrows():
            report_lines.append(f"- `{row['id']}`: {row['title'][:100]}...")
        if len(v2_only) > 5:
            report_lines.append(f"- ... and {len(v2_only) - 5} more")
    else:
        report_lines.append("None")

    report_lines.append("")
    report_lines.append("### Papers where only PyCaret models predict positive")
    report_lines.append("")

    pycaret_only = df[(df['v2_pred'] == 0) & ((df['pycaret_true_pred'] == 1) | (df['pycaret_false_pred'] == 1))]
    if len(pycaret_only) > 0:
        report_lines.append(f"**Count**: {len(pycaret_only)} papers")
        report_lines.append("")
        for idx, row in pycaret_only.head(5).iterrows():
            report_lines.append(f"- `{row['id']}`: {row['title'][:100]}...")
        if len(pycaret_only) > 5:
            report_lines.append(f"- ... and {len(pycaret_only) - 5} more")
    else:
        report_lines.append("None")

    report_lines.append("")

    # Footer
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*Note: Ground truth labels not available in this Phase 1 analysis.*")
    report_lines.append("*Manual validation will determine actual precision/recall for each model.*")
    report_lines.append("")

    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"✓ Report saved to: {output_file}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("SCRIPT 03c: CLASSIFICATION COMPARISON")
    logger.info("=" * 70)

    start_time = datetime.now()

    # ------------------------------------------------------------------------
    # 1. Load all predictions
    # ------------------------------------------------------------------------
    logger.info("\n📚 Loading predictions from all models...")

    df_v2 = load_predictions(V2_RESULTS, 'v2')
    df_pycaret_true = load_predictions(PYCARET_TRUE_RESULTS, 'pycaret_true')
    df_pycaret_false = load_predictions(PYCARET_FALSE_RESULTS, 'pycaret_false')

    # Check for missing files
    missing_files = []
    if df_v2 is None:
        missing_files.append("V2 BERT")
    if df_pycaret_true is None:
        missing_files.append("PyCaret test_mode_true")
    if df_pycaret_false is None:
        missing_files.append("PyCaret test_mode_false")

    if missing_files:
        logger.error(f"\n❌ Missing prediction files for: {', '.join(missing_files)}")
        logger.error("Please run the corresponding scripts:")
        if "V2 BERT" in missing_files:
            logger.error("  - python scripts/03a_run_v2_classification.py")
        if "PyCaret" in ' '.join(missing_files):
            logger.error("  - python scripts/03b_run_pycaret_classification.py")
        return 1

    # ------------------------------------------------------------------------
    # 2. Merge predictions
    # ------------------------------------------------------------------------
    logger.info("\n🔗 Merging predictions...")

    df_merged = df_v2.copy()

    if df_pycaret_true is not None:
        df_merged = df_merged.merge(
            df_pycaret_true[[col for col in df_pycaret_true.columns if col != 'title']],
            on='id',
            how='outer'
        )

    if df_pycaret_false is not None:
        df_merged = df_merged.merge(
            df_pycaret_false[[col for col in df_pycaret_false.columns if col != 'title']],
            on='id',
            how='outer'
        )

    logger.info(f"✓ Merged {len(df_merged)} papers")

    # ------------------------------------------------------------------------
    # 3. Calculate pairwise agreement
    # ------------------------------------------------------------------------
    logger.info("\n📊 Calculating pairwise agreement...")

    agreement_stats = []

    # V2 vs PyCaret (test_mode_true)
    if 'pycaret_true_pred' in df_merged.columns:
        stats = calculate_agreement(df_merged, 'v2', 'pycaret_true')
        agreement_stats.append(stats)
        logger.info(f"   V2 vs PyCaret(true): {stats['agreement_rate']:.1%} agreement")

    # V2 vs PyCaret (test_mode_false)
    if 'pycaret_false_pred' in df_merged.columns:
        stats = calculate_agreement(df_merged, 'v2', 'pycaret_false')
        agreement_stats.append(stats)
        logger.info(f"   V2 vs PyCaret(false): {stats['agreement_rate']:.1%} agreement")

    # PyCaret models
    if 'pycaret_true_pred' in df_merged.columns and 'pycaret_false_pred' in df_merged.columns:
        stats = calculate_agreement(df_merged, 'pycaret_true', 'pycaret_false')
        agreement_stats.append(stats)
        logger.info(f"   PyCaret(true) vs PyCaret(false): {stats['agreement_rate']:.1%} agreement")

    # ------------------------------------------------------------------------
    # 4. Analyze consensus patterns
    # ------------------------------------------------------------------------
    logger.info("\n🎯 Analyzing consensus patterns...")

    if all(col in df_merged.columns for col in ['v2_pred', 'pycaret_true_pred', 'pycaret_false_pred']):
        all_agree_pos = ((df_merged['v2_pred'] == 1) & (df_merged['pycaret_true_pred'] == 1) & (df_merged['pycaret_false_pred'] == 1)).sum()
        all_agree_neg = ((df_merged['v2_pred'] == 0) & (df_merged['pycaret_true_pred'] == 0) & (df_merged['pycaret_false_pred'] == 0)).sum()
        total_consensus = all_agree_pos + all_agree_neg
        consensus_rate = total_consensus / len(df_merged) if len(df_merged) > 0 else 0

        logger.info(f"   Full consensus: {total_consensus} papers ({consensus_rate:.1%})")
        logger.info(f"     - All positive: {all_agree_pos}")
        logger.info(f"     - All negative: {all_agree_neg}")

    # ------------------------------------------------------------------------
    # 5. Save merged predictions
    # ------------------------------------------------------------------------
    logger.info(f"\n💾 Saving comparison data...")

    CLASSIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    df_merged.to_csv(OUTPUT_CSV, index=False)

    logger.info(f"✓ Saved to: {OUTPUT_CSV}")
    logger.info(f"  Size: {OUTPUT_CSV.stat().st_size / 1024:.1f} KB")

    # ------------------------------------------------------------------------
    # 6. Generate markdown report
    # ------------------------------------------------------------------------
    generate_markdown_report(df_merged, agreement_stats, OUTPUT_REPORT)

    # ------------------------------------------------------------------------
    # 7. Final report
    # ------------------------------------------------------------------------
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ SCRIPT 03c COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Log saved to: {LOG_FILE}")
    logger.info(f"Outputs:")
    logger.info(f"  - Comparison data: {OUTPUT_CSV}")
    logger.info(f"  - Report: {OUTPUT_REPORT}")
    logger.info(f"\nNext step: Review comparison report and begin Batch 3 (NER scripts)")
    logger.info(f"{'=' * 70}")

    return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    exit(main())
