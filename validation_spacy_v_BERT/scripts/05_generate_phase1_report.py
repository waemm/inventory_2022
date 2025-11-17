#!/usr/bin/env python3
"""
Script 05: Generate Phase 1 Report
===================================

Purpose:
    Generates comprehensive Phase 1 validation report combining:
    - Sample characteristics
    - Classification comparison results
    - NER comparison results
    - Overall model performance summary
    - Recommendations for manual validation

Usage:
    cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT
    source ../biodata_modern_env/bin/activate  # Any environment works
    python scripts/05_generate_phase1_report.py

Inputs:
    - results/validation/sample/validation_sample_with_abstracts.csv
    - results/validation/classification/classification_comparison.csv
    - results/validation/ner/ner_comparison.csv

Outputs:
    - results/validation/PHASE1_VALIDATION_REPORT.md
    - logs/05_generate_phase1_report.log

Author: Phase 1 Validation Study
Date: 2025-11-13
"""

import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
from collections import Counter
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# TEST_MODE: Set to True for quick testing (10-15 papers)
#            Set to False for full validation (all papers in sample)
TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
SESSION_ID = os.environ.get('SESSION_ID', '')
if not SESSION_ID:
    # Generate session ID if not provided
    import random
    import string
    from datetime import datetime
    mode_suffix = "_test" if TEST_MODE else ""
    SESSION_ID = f"{datetime.now().strftime('%Y-%m-%d')}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}{mode_suffix}"


if TEST_MODE:
    print("\n🧪 TEST MODE ENABLED")
    print("   Will generate test validation report\n")
else:
    print("\n🚀 PRODUCTION MODE")
    print("   Will generate full validation report\n")

# Paths (relative to validation_spacy_v_BERT/) - use _test suffix in TEST_MODE
VALIDATION_ROOT = Path(__file__).parent.parent

output_suffix = f"_{SESSION_ID}" if SESSION_ID else ("_test" if TEST_MODE else "")

# Input files
SAMPLE_FILE = VALIDATION_ROOT / f"results/validation/sample/validation_sample_with_abstracts{output_suffix}.csv"
CLASSIFICATION_COMPARISON = VALIDATION_ROOT / f"results/validation/classification/classification_comparison{output_suffix}.csv"
NER_COMPARISON = VALIDATION_ROOT / f"results/validation/ner/ner_comparison{output_suffix}.csv"

# Output files
OUTPUT_REPORT = VALIDATION_ROOT / f"results/validation/PHASE1_VALIDATION_REPORT{output_suffix}.md"
LOG_FILE = VALIDATION_ROOT / "logs/05_generate_phase1_report.log"

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

def analyze_sample_characteristics(sample_df):
    """
    Analyze validation sample characteristics.

    Args:
        sample_df: DataFrame with validation sample

    Returns:
        dict with sample statistics
    """
    logger.info("📊 Analyzing sample characteristics...")

    stats = {
        'total_papers': len(sample_df),
        'papers_with_abstracts': (sample_df['abstract'].notna() & (sample_df['abstract'] != '')).sum(),
    }

    # Resource distribution
    if 'resource_short_name' in sample_df.columns:
        stats['unique_resources'] = sample_df['resource_short_name'].nunique()
        stats['top_resources'] = sample_df['resource_short_name'].value_counts().head(10).to_dict()

    # Global core distribution
    if 'is_global_core_biodata_resource' in sample_df.columns:
        stats['global_core_papers'] = (sample_df['is_global_core_biodata_resource'] == 1).sum()
        stats['other_papers'] = (sample_df['is_global_core_biodata_resource'] == 0).sum()

    # Abstract availability
    stats['abstract_percentage'] = (stats['papers_with_abstracts'] / stats['total_papers'] * 100) if stats['total_papers'] > 0 else 0

    logger.info(f"  Total papers: {stats['total_papers']}")
    logger.info(f"  Unique resources: {stats.get('unique_resources', 'N/A')}")
    logger.info(f"  Papers with abstracts: {stats['papers_with_abstracts']} ({stats['abstract_percentage']:.1f}%)")

    return stats

def analyze_classification_results(classif_df):
    """
    Analyze classification comparison results.

    Args:
        classif_df: DataFrame with classification comparison

    Returns:
        dict with classification statistics
    """
    logger.info("📊 Analyzing classification results...")

    stats = {}

    # Count predictions by model
    for model in ['v2', 'pycaret_true', 'pycaret_false']:
        pred_col = f'{model}_pred'
        if pred_col in classif_df.columns:
            stats[f'{model}_positive'] = (classif_df[pred_col] == 1).sum()
            stats[f'{model}_negative'] = (classif_df[pred_col] == 0).sum()
            stats[f'{model}_total'] = len(classif_df)

    # Calculate pairwise agreement
    if all(f'{model}_pred' in classif_df.columns for model in ['v2', 'pycaret_true', 'pycaret_false']):
        # V2 vs PyCaret (true)
        v2_pycaret_true_agree = ((classif_df['v2_pred'] == classif_df['pycaret_true_pred'])).sum()
        stats['v2_pycaret_true_agreement'] = (v2_pycaret_true_agree / len(classif_df) * 100) if len(classif_df) > 0 else 0

        # V2 vs PyCaret (false)
        v2_pycaret_false_agree = ((classif_df['v2_pred'] == classif_df['pycaret_false_pred'])).sum()
        stats['v2_pycaret_false_agreement'] = (v2_pycaret_false_agree / len(classif_df) * 100) if len(classif_df) > 0 else 0

        # PyCaret models agreement
        pycaret_agree = ((classif_df['pycaret_true_pred'] == classif_df['pycaret_false_pred'])).sum()
        stats['pycaret_models_agreement'] = (pycaret_agree / len(classif_df) * 100) if len(classif_df) > 0 else 0

        # Full consensus (all 3 agree)
        all_agree = ((classif_df['v2_pred'] == classif_df['pycaret_true_pred']) &
                     (classif_df['v2_pred'] == classif_df['pycaret_false_pred'])).sum()
        stats['full_consensus'] = (all_agree / len(classif_df) * 100) if len(classif_df) > 0 else 0

    logger.info(f"  V2 positive: {stats.get('v2_positive', 'N/A')}")
    logger.info(f"  Full consensus: {stats.get('full_consensus', 'N/A'):.1f}%")

    return stats

def analyze_ner_results(ner_df):
    """
    Analyze NER comparison results.

    Args:
        ner_df: DataFrame with NER comparison

    Returns:
        dict with NER statistics
    """
    logger.info("📊 Analyzing NER results...")

    stats = {}

    # Count entities by model
    if 'model' in ner_df.columns:
        v2_entities = ner_df[ner_df['model'] == 'v2']
        spacy_entities = ner_df[ner_df['model'] == 'spacy']

        stats['v2_total_entities'] = len(v2_entities)
        stats['v2_papers_with_entities'] = v2_entities['paper_id'].nunique()

        stats['spacy_total_entities'] = len(spacy_entities)
        stats['spacy_papers_with_entities'] = spacy_entities['paper_id'].nunique()

        # spaCy source breakdown
        if 'source' in spacy_entities.columns:
            stats['spacy_ruler_entities'] = (spacy_entities['source'] == 'ruler').sum()
            stats['spacy_statistical_entities'] = (spacy_entities['source'] == 'statistical').sum()
            stats['spacy_ruler_percentage'] = (stats['spacy_ruler_entities'] / stats['spacy_total_entities'] * 100) if stats['spacy_total_entities'] > 0 else 0

        # Paper coverage overlap
        v2_papers = set(v2_entities['paper_id'].unique())
        spacy_papers = set(spacy_entities['paper_id'].unique())
        both_papers = v2_papers & spacy_papers

        stats['both_models_papers'] = len(both_papers)
        stats['v2_only_papers'] = len(v2_papers - spacy_papers)
        stats['spacy_only_papers'] = len(spacy_papers - v2_papers)

    logger.info(f"  V2 entities: {stats.get('v2_total_entities', 'N/A')}")
    logger.info(f"  spaCy entities: {stats.get('spacy_total_entities', 'N/A')}")
    logger.info(f"  Both models found entities: {stats.get('both_models_papers', 'N/A')} papers")

    return stats

def generate_report(sample_stats, classif_stats, ner_stats, output_file):
    """
    Generate comprehensive Phase 1 validation report.

    Args:
        sample_stats: Sample characteristics
        classif_stats: Classification comparison statistics
        ner_stats: NER comparison statistics
        output_file: Path to save report
    """
    logger.info("\n📝 Generating Phase 1 validation report...")

    report_lines = []

    # ========================================================================
    # HEADER
    # ========================================================================
    report_lines.append("# Phase 1 Validation Study Report")
    report_lines.append("")
    report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Study Type**: Model Comparison Validation")
    report_lines.append(f"**Sample Size**: {sample_stats['total_papers']} papers, {sample_stats.get('unique_resources', 'N/A')} unique resources")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # ========================================================================
    # EXECUTIVE SUMMARY
    # ========================================================================
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This report presents the results of Phase 1 validation study comparing five ML models:")
    report_lines.append("")
    report_lines.append("**Classification Models:**")
    report_lines.append("1. V2 BERT Classifier (trained on title+abstract)")
    report_lines.append("2. PyCaret Metadata Classifier (TEST_MODE=True, 92 features)")
    report_lines.append("3. PyCaret Metadata Classifier (TEST_MODE=False, 112 features)")
    report_lines.append("")
    report_lines.append("**NER Models:**")
    report_lines.append("4. V2 BERT NER (BioBERT-based, trained on title+abstract)")
    report_lines.append("5. spaCy Hybrid NER (EntityRuler + Statistical NER)")
    report_lines.append("")

    # Key findings
    report_lines.append("### Key Findings")
    report_lines.append("")

    # Classification findings
    if classif_stats.get('full_consensus'):
        report_lines.append(f"**Classification**: {classif_stats['full_consensus']:.1f}% full consensus across all 3 models")

    # NER findings
    if ner_stats.get('both_models_papers'):
        report_lines.append(f"**NER**: {ner_stats['both_models_papers']} papers had entities detected by both models")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # ========================================================================
    # VALIDATION SAMPLE
    # ========================================================================
    report_lines.append("## 1. Validation Sample Characteristics")
    report_lines.append("")
    report_lines.append(f"**Total Papers**: {sample_stats['total_papers']}")
    report_lines.append(f"**Unique Resources**: {sample_stats.get('unique_resources', 'N/A')}")
    report_lines.append(f"**Papers with Abstracts**: {sample_stats['papers_with_abstracts']} ({sample_stats['abstract_percentage']:.1f}%)")
    report_lines.append("")

    # Resource distribution
    if sample_stats.get('global_core_papers'):
        report_lines.append("### Sample Composition")
        report_lines.append("")
        report_lines.append(f"- Global Core Resources: {sample_stats['global_core_papers']} papers")
        report_lines.append(f"- Other Resources: {sample_stats['other_papers']} papers")
        report_lines.append("")

    # Top resources
    if sample_stats.get('top_resources'):
        report_lines.append("### Top 10 Resources in Sample")
        report_lines.append("")
        report_lines.append("| Resource | Papers |")
        report_lines.append("|----------|--------|")
        for resource, count in sample_stats['top_resources'].items():
            report_lines.append(f"| {resource} | {count} |")
        report_lines.append("")

    report_lines.append("---")
    report_lines.append("")

    # ========================================================================
    # CLASSIFICATION RESULTS
    # ========================================================================
    report_lines.append("## 2. Classification Results")
    report_lines.append("")

    # Model predictions
    report_lines.append("### Predictions by Model")
    report_lines.append("")
    report_lines.append("| Model | Positive | Negative | Total |")
    report_lines.append("|-------|----------|----------|-------|")

    for model_name, model_key in [("V2 BERT", "v2"), ("PyCaret (92 feat)", "pycaret_true"), ("PyCaret (112 feat)", "pycaret_false")]:
        pos = classif_stats.get(f'{model_key}_positive', 'N/A')
        neg = classif_stats.get(f'{model_key}_negative', 'N/A')
        total = classif_stats.get(f'{model_key}_total', 'N/A')
        report_lines.append(f"| {model_name} | {pos} | {neg} | {total} |")

    report_lines.append("")

    # Agreement analysis
    report_lines.append("### Model Agreement")
    report_lines.append("")
    report_lines.append("| Model Pair | Agreement Rate |")
    report_lines.append("|------------|----------------|")

    if classif_stats.get('v2_pycaret_true_agreement'):
        report_lines.append(f"| V2 vs PyCaret (92 feat) | {classif_stats['v2_pycaret_true_agreement']:.1f}% |")
    if classif_stats.get('v2_pycaret_false_agreement'):
        report_lines.append(f"| V2 vs PyCaret (112 feat) | {classif_stats['v2_pycaret_false_agreement']:.1f}% |")
    if classif_stats.get('pycaret_models_agreement'):
        report_lines.append(f"| PyCaret (92) vs PyCaret (112) | {classif_stats['pycaret_models_agreement']:.1f}% |")

    report_lines.append("")

    if classif_stats.get('full_consensus'):
        report_lines.append(f"**Full Consensus**: {classif_stats['full_consensus']:.1f}% of papers (all 3 models agree)")
        report_lines.append("")

    report_lines.append("---")
    report_lines.append("")

    # ========================================================================
    # NER RESULTS
    # ========================================================================
    report_lines.append("## 3. NER Results")
    report_lines.append("")

    # Entity counts
    report_lines.append("### Entity Extraction Statistics")
    report_lines.append("")
    report_lines.append("| Model | Total Entities | Papers with Entities | Avg per Paper |")
    report_lines.append("|-------|----------------|----------------------|---------------|")

    v2_total = ner_stats.get('v2_total_entities', 0)
    v2_papers = ner_stats.get('v2_papers_with_entities', 0)
    v2_avg = (v2_total / v2_papers) if v2_papers > 0 else 0

    spacy_total = ner_stats.get('spacy_total_entities', 0)
    spacy_papers = ner_stats.get('spacy_papers_with_entities', 0)
    spacy_avg = (spacy_total / spacy_papers) if spacy_papers > 0 else 0

    report_lines.append(f"| V2 BERT NER | {v2_total} | {v2_papers} | {v2_avg:.2f} |")
    report_lines.append(f"| spaCy Hybrid NER | {spacy_total} | {spacy_papers} | {spacy_avg:.2f} |")
    report_lines.append("")

    # spaCy source breakdown
    if ner_stats.get('spacy_ruler_entities'):
        report_lines.append("### spaCy Entity Sources")
        report_lines.append("")
        report_lines.append(f"- **EntityRuler (dictionary)**: {ner_stats['spacy_ruler_entities']} entities ({ner_stats['spacy_ruler_percentage']:.1f}%)")
        report_lines.append(f"- **Statistical NER (learned)**: {ner_stats['spacy_statistical_entities']} entities ({100-ner_stats['spacy_ruler_percentage']:.1f}%)")
        report_lines.append("")

    # Paper coverage
    report_lines.append("### Paper-Level Coverage")
    report_lines.append("")
    report_lines.append(f"- Both models found entities: {ner_stats.get('both_models_papers', 'N/A')} papers")
    report_lines.append(f"- V2 only: {ner_stats.get('v2_only_papers', 'N/A')} papers")
    report_lines.append(f"- spaCy only: {ner_stats.get('spacy_only_papers', 'N/A')} papers")
    report_lines.append("")

    report_lines.append("---")
    report_lines.append("")

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================
    report_lines.append("## 4. Recommendations for Manual Validation")
    report_lines.append("")
    report_lines.append("Based on the model comparison results, we recommend the following strategy for manual validation:")
    report_lines.append("")

    # Classification recommendations
    report_lines.append("### Classification Validation Strategy")
    report_lines.append("")
    report_lines.append("1. **High Priority**: Papers where models disagree")
    report_lines.append("   - Focus on cases where V2 and PyCaret models predict differently")
    report_lines.append("   - These reveal the strengths/weaknesses of text-based vs metadata-based approaches")
    report_lines.append("")
    report_lines.append("2. **Medium Priority**: Consensus negative papers")
    report_lines.append("   - Validate sample of papers all models predict as negative")
    report_lines.append("   - Confirm these are truly non-resource papers")
    report_lines.append("")
    report_lines.append("3. **Lower Priority**: Consensus positive papers")
    report_lines.append("   - All models agree → likely true positives")
    report_lines.append("   - Spot-check for quality assurance")
    report_lines.append("")

    # NER recommendations
    report_lines.append("### NER Validation Strategy")
    report_lines.append("")
    report_lines.append("1. **V2-only entities**: Potential new discoveries from learned patterns")
    report_lines.append("2. **spaCy EntityRuler entities**: Known resources with canonical IDs")
    report_lines.append("3. **spaCy Statistical entities**: Novel resources not in dictionary")
    report_lines.append("4. **Exact matches**: Both models agree → high confidence")
    report_lines.append("5. **Fuzzy matches**: Similar but not identical → review for variants/aliases")
    report_lines.append("")

    # ========================================================================
    # FILES & OUTPUTS
    # ========================================================================
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 5. Generated Files")
    report_lines.append("")
    report_lines.append("**Sample Data:**")
    report_lines.append("- `results/validation/sample/validation_sample.csv`")
    report_lines.append("- `results/validation/sample/validation_sample_with_abstracts.csv`")
    report_lines.append("")
    report_lines.append("**Classification Results:**")
    report_lines.append("- `results/validation/classification/v2_classification_results.csv`")
    report_lines.append("- `results/validation/classification/pycaret_test_mode_true_results.csv`")
    report_lines.append("- `results/validation/classification/pycaret_test_mode_false_results.csv`")
    report_lines.append("- `results/validation/classification/classification_comparison.csv`")
    report_lines.append("- `results/validation/classification/classification_comparison_report.md`")
    report_lines.append("")
    report_lines.append("**NER Results:**")
    report_lines.append("- `results/validation/ner/v2_ner_results.csv`")
    report_lines.append("- `results/validation/ner/spacy_ner_results.csv`")
    report_lines.append("- `results/validation/ner/ner_comparison.csv`")
    report_lines.append("- `results/validation/ner/ner_comparison_report.md`")
    report_lines.append("")

    # ========================================================================
    # FOOTER
    # ========================================================================
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Next Steps")
    report_lines.append("")
    report_lines.append("1. **Review detailed comparison reports**:")
    report_lines.append("   - `classification_comparison_report.md`")
    report_lines.append("   - `ner_comparison_report.md`")
    report_lines.append("")
    report_lines.append("2. **Begin manual validation**:")
    report_lines.append("   - Prioritize disagreement cases")
    report_lines.append("   - Use validation strategy outlined above")
    report_lines.append("")
    report_lines.append("3. **Calculate performance metrics**:")
    report_lines.append("   - After manual validation, compute precision/recall/F1")
    report_lines.append("   - Compare models against ground truth labels")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*Generated by Phase 1 Validation Study Pipeline*")
    report_lines.append("")

    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"✓ Phase 1 report saved to: {output_file}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("SCRIPT 05: GENERATE PHASE 1 REPORT")
    logger.info("=" * 70)

    start_time = datetime.now()

    # ------------------------------------------------------------------------
    # 1. Load input files
    # ------------------------------------------------------------------------
    logger.info("\n📚 Loading input files...")

    # Validation sample
    if not SAMPLE_FILE.exists():
        logger.error(f"❌ Sample file not found: {SAMPLE_FILE}")
        return 1
    df_sample = pd.read_csv(SAMPLE_FILE)
    logger.info(f"✓ Sample: {len(df_sample)} papers")

    # Classification comparison
    if not CLASSIFICATION_COMPARISON.exists():
        logger.warning(f"⚠️  Classification comparison not found: {CLASSIFICATION_COMPARISON}")
        df_classif = None
    else:
        df_classif = pd.read_csv(CLASSIFICATION_COMPARISON)
        logger.info(f"✓ Classification: {len(df_classif)} papers")

    # NER comparison
    if not NER_COMPARISON.exists():
        logger.warning(f"⚠️  NER comparison not found: {NER_COMPARISON}")
        df_ner = None
    else:
        df_ner = pd.read_csv(NER_COMPARISON)
        logger.info(f"✓ NER: {len(df_ner)} entity extractions")

    # Check if we have enough data
    if df_classif is None and df_ner is None:
        logger.error("❌ No comparison results found. Please run classification and NER scripts first.")
        return 1

    # ------------------------------------------------------------------------
    # 2. Analyze results
    # ------------------------------------------------------------------------
    sample_stats = analyze_sample_characteristics(df_sample)

    classif_stats = analyze_classification_results(df_classif) if df_classif is not None else {}
    ner_stats = analyze_ner_results(df_ner) if df_ner is not None else {}

    # ------------------------------------------------------------------------
    # 3. Generate report
    # ------------------------------------------------------------------------
    generate_report(sample_stats, classif_stats, ner_stats, OUTPUT_REPORT)

    # ------------------------------------------------------------------------
    # 4. Final summary
    # ------------------------------------------------------------------------
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ SCRIPT 05 COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Log saved to: {LOG_FILE}")
    logger.info(f"Report saved to: {OUTPUT_REPORT}")
    logger.info(f"\n📖 View the report:")
    logger.info(f"  cat {OUTPUT_REPORT}")
    logger.info(f"\n🎉 Phase 1 validation study complete!")
    logger.info(f"  All scripts ready to execute")
    logger.info(f"{'=' * 70}")

    return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
