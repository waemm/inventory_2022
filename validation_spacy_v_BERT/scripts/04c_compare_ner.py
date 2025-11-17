#!/usr/bin/env python3
"""
Script 04c: Compare NER Results
=================================

Purpose:
    Compare entity extractions from V2 BERT NER and spaCy Hybrid NER.
    Analyzes entity-level agreement, coverage patterns, and differences.

Comparison Dimensions:
    - Paper-level coverage: Which papers have entities detected?
    - Entity-level overlap: Same entities detected by both models?
    - Entity text similarity: Fuzzy matching for similar extractions
    - Model-specific patterns: What does each model find uniquely?

Usage:
    cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT
    source ../biodata_modern_env/bin/activate  # Any environment works
    python scripts/04c_compare_ner.py

Inputs:
    - results/validation/ner/v2_ner_results.csv
    - results/validation/ner/spacy_ner_results.csv

Outputs:
    - results/validation/ner/ner_comparison.csv
    - results/validation/ner/ner_comparison_report.md
    - logs/04c_compare_ner.log

Author: Phase 1 Validation Study
Date: 2025-11-13
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from collections import Counter, defaultdict
import difflib
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
    print("   Will compare test NER results\n")
else:
    print("\n🚀 PRODUCTION MODE")
    print("   Will compare full NER results\n")

# Paths (relative to validation_spacy_v_BERT/) - use _test suffix in TEST_MODE
VALIDATION_ROOT = Path(__file__).parent.parent
NER_DIR = VALIDATION_ROOT / "results/validation/ner"

output_suffix = f"_{SESSION_ID}" if SESSION_ID else ("_test" if TEST_MODE else "")

# Input files
V2_NER_RESULTS = NER_DIR / f"v2_ner_results{output_suffix}.csv"
SPACY_NER_RESULTS = NER_DIR / f"spacy_ner_results{output_suffix}.csv"

# Output files
OUTPUT_CSV = NER_DIR / f"ner_comparison{output_suffix}.csv"
OUTPUT_REPORT = NER_DIR / f"ner_comparison_report{output_suffix}.md"
LOG_FILE = VALIDATION_ROOT / "logs/04c_compare_ner.log"

# Similarity threshold for fuzzy matching
SIMILARITY_THRESHOLD = 0.85

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

def normalize_entity_text(text):
    """
    Normalize entity text for comparison.

    Args:
        text: Entity text string

    Returns:
        Normalized text (lowercase, stripped)
    """
    if pd.isna(text):
        return ""
    return str(text).lower().strip()

def calculate_text_similarity(text1, text2):
    """
    Calculate text similarity using difflib.

    Args:
        text1, text2: Strings to compare

    Returns:
        float: Similarity score (0-1)
    """
    return difflib.SequenceMatcher(None, text1, text2).ratio()

def load_ner_results(file_path, model_name):
    """
    Load NER results from CSV file.

    Args:
        file_path: Path to NER results CSV
        model_name: Name of model (for column naming)

    Returns:
        DataFrame with normalized columns
    """
    logger.info(f"📂 Loading {model_name} NER results from {file_path.name}...")

    if not file_path.exists():
        logger.error(f"❌ File not found: {file_path}")
        return None

    df = pd.read_csv(file_path)
    logger.info(f"   Loaded {len(df)} entity extractions")

    # Identify columns
    id_col = None
    for col in ['ID', 'id', 'pmid', 'publication_id', 'pubmed_id']:
        if col in df.columns:
            id_col = col
            break

    mention_col = None
    for col in ['mention', 'text', 'entity', 'entity_text']:
        if col in df.columns:
            mention_col = col
            break

    label_col = None
    for col in ['label', 'entity_type', 'type']:
        if col in df.columns:
            label_col = col
            break

    if not id_col or not mention_col:
        logger.error(f"❌ Required columns not found in {file_path}")
        logger.error(f"   Available columns: {list(df.columns)}")
        return None

    # Create normalized dataframe
    df_norm = pd.DataFrame()
    df_norm['paper_id'] = df[id_col].astype(str)
    df_norm['mention'] = df[mention_col]
    df_norm['mention_normalized'] = df[mention_col].apply(normalize_entity_text)
    df_norm['label'] = df[label_col] if label_col else 'RESOURCE'
    df_norm['model'] = model_name

    # Add source column for spaCy (ruler vs statistical)
    if 'source' in df.columns:
        df_norm['source'] = df['source']

    # Add canonical ID for spaCy (from EntityRuler)
    if 'canonical_id' in df.columns:
        df_norm['canonical_id'] = df['canonical_id']

    # Summary
    n_papers = df_norm['paper_id'].nunique()
    n_entities = len(df_norm)

    logger.info(f"   ✓ {model_name}: {n_entities} entities from {n_papers} papers")

    return df_norm

def calculate_paper_coverage(v2_df, spacy_df):
    """
    Calculate paper-level coverage for both models.

    Args:
        v2_df, spacy_df: DataFrames with entity extractions

    Returns:
        dict with coverage statistics
    """
    v2_papers = set(v2_df['paper_id'].unique())
    spacy_papers = set(spacy_df['paper_id'].unique())

    both = v2_papers & spacy_papers
    v2_only = v2_papers - spacy_papers
    spacy_only = spacy_papers - v2_papers

    return {
        'v2_papers': len(v2_papers),
        'spacy_papers': len(spacy_papers),
        'both_papers': len(both),
        'v2_only_papers': len(v2_only),
        'spacy_only_papers': len(spacy_only),
        'v2_only_paper_ids': list(v2_only),
        'spacy_only_paper_ids': list(spacy_only)
    }

def calculate_entity_overlap(v2_df, spacy_df):
    """
    Calculate entity-level overlap (exact + fuzzy matching).

    Args:
        v2_df, spacy_df: DataFrames with entity extractions

    Returns:
        dict with overlap statistics
    """
    logger.info("\n🔍 Analyzing entity-level overlap...")

    # Track matches
    exact_matches = []
    fuzzy_matches = []
    v2_unmatched = []
    spacy_unmatched = []

    # Build paper-level indices
    v2_by_paper = v2_df.groupby('paper_id')
    spacy_by_paper = spacy_df.groupby('paper_id')

    papers = set(v2_df['paper_id'].unique()) | set(spacy_df['paper_id'].unique())

    for paper_id in papers:
        v2_entities = v2_by_paper.get_group(paper_id) if paper_id in v2_by_paper.groups else pd.DataFrame()
        spacy_entities = spacy_by_paper.get_group(paper_id) if paper_id in spacy_by_paper.groups else pd.DataFrame()

        v2_mentions = set(v2_entities['mention_normalized']) if len(v2_entities) > 0 else set()
        spacy_mentions = set(spacy_entities['mention_normalized']) if len(spacy_entities) > 0 else set()

        # Exact matches
        exact = v2_mentions & spacy_mentions
        exact_matches.extend([(paper_id, m) for m in exact])

        # Check for fuzzy matches in remaining entities
        v2_remaining = v2_mentions - exact
        spacy_remaining = spacy_mentions - exact

        for v2_mention in v2_remaining:
            matched = False
            for spacy_mention in spacy_remaining:
                similarity = calculate_text_similarity(v2_mention, spacy_mention)
                if similarity >= SIMILARITY_THRESHOLD:
                    fuzzy_matches.append((paper_id, v2_mention, spacy_mention, similarity))
                    matched = True
                    break
            if not matched:
                v2_unmatched.append((paper_id, v2_mention))

        # Remaining spaCy entities
        for spacy_mention in spacy_remaining:
            # Check if already matched in fuzzy
            already_matched = any(m[2] == spacy_mention for m in fuzzy_matches if m[0] == paper_id)
            if not already_matched:
                spacy_unmatched.append((paper_id, spacy_mention))

    logger.info(f"   Exact matches: {len(exact_matches)}")
    logger.info(f"   Fuzzy matches (>{SIMILARITY_THRESHOLD*100:.0f}% similar): {len(fuzzy_matches)}")
    logger.info(f"   V2 unique: {len(v2_unmatched)}")
    logger.info(f"   spaCy unique: {len(spacy_unmatched)}")

    return {
        'exact_matches': len(exact_matches),
        'fuzzy_matches': len(fuzzy_matches),
        'v2_unmatched': len(v2_unmatched),
        'spacy_unmatched': len(spacy_unmatched),
        'v2_unmatched_list': v2_unmatched[:50],  # Sample
        'spacy_unmatched_list': spacy_unmatched[:50]  # Sample
    }

def generate_markdown_report(coverage_stats, overlap_stats, v2_df, spacy_df, output_file):
    """
    Generate markdown report with NER comparison results.

    Args:
        coverage_stats: Paper-level coverage statistics
        overlap_stats: Entity-level overlap statistics
        v2_df, spacy_df: DataFrames with entity extractions
        output_file: Path to save report
    """
    logger.info("\n📝 Generating markdown report...")

    report_lines = []

    # Header
    report_lines.append("# NER Comparison Report")
    report_lines.append("")
    report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## Overview")
    report_lines.append("")
    report_lines.append("Comparison of entity extractions from two NER models:")
    report_lines.append("")
    report_lines.append("1. **V2 BERT NER**: Trained on title+abstract, BioBERT-based")
    report_lines.append("2. **spaCy Hybrid NER**: EntityRuler (752 resources) + Statistical NER")
    report_lines.append("")

    # Paper-level coverage
    report_lines.append("## Paper-Level Coverage")
    report_lines.append("")
    report_lines.append(f"**Total papers analyzed**: {coverage_stats['v2_papers'] + coverage_stats['spacy_only_papers']}")
    report_lines.append("")
    report_lines.append("| Model | Papers with Entities | Percentage |")
    report_lines.append("|-------|---------------------|------------|")
    report_lines.append(f"| V2 BERT NER | {coverage_stats['v2_papers']} | {100*coverage_stats['v2_papers']/(coverage_stats['v2_papers']+coverage_stats['spacy_only_papers']):.1f}% |")
    report_lines.append(f"| spaCy Hybrid NER | {coverage_stats['spacy_papers']} | {100*coverage_stats['spacy_papers']/(coverage_stats['v2_papers']+coverage_stats['spacy_only_papers']):.1f}% |")
    report_lines.append(f"| Both Models | {coverage_stats['both_papers']} | - |")
    report_lines.append(f"| V2 Only | {coverage_stats['v2_only_papers']} | - |")
    report_lines.append(f"| spaCy Only | {coverage_stats['spacy_only_papers']} | - |")
    report_lines.append("")

    # Entity counts
    report_lines.append("## Entity Extraction Statistics")
    report_lines.append("")
    report_lines.append("| Model | Total Entities | Avg per Paper | Papers with Entities |")
    report_lines.append("|-------|----------------|---------------|----------------------|")

    v2_total = len(v2_df)
    v2_papers = v2_df['paper_id'].nunique()
    v2_avg = v2_total / v2_papers if v2_papers > 0 else 0

    spacy_total = len(spacy_df)
    spacy_papers = spacy_df['paper_id'].nunique()
    spacy_avg = spacy_total / spacy_papers if spacy_papers > 0 else 0

    report_lines.append(f"| V2 BERT NER | {v2_total} | {v2_avg:.2f} | {v2_papers} |")
    report_lines.append(f"| spaCy Hybrid NER | {spacy_total} | {spacy_avg:.2f} | {spacy_papers} |")
    report_lines.append("")

    # spaCy source breakdown (if available)
    if 'source' in spacy_df.columns:
        report_lines.append("### spaCy Entity Sources")
        report_lines.append("")
        ruler_count = (spacy_df['source'] == 'ruler').sum()
        stat_count = (spacy_df['source'] == 'statistical').sum()
        report_lines.append(f"- **EntityRuler (dictionary)**: {ruler_count} ({100*ruler_count/spacy_total:.1f}%)")
        report_lines.append(f"- **Statistical NER (learned)**: {stat_count} ({100*stat_count/spacy_total:.1f}%)")
        report_lines.append("")

    # Entity overlap
    report_lines.append("## Entity-Level Overlap")
    report_lines.append("")
    report_lines.append(f"**Exact matches**: {overlap_stats['exact_matches']} entities found by both models")
    report_lines.append(f"**Fuzzy matches**: {overlap_stats['fuzzy_matches']} entities (>{SIMILARITY_THRESHOLD*100:.0f}% similar)")
    report_lines.append(f"**V2 unique**: {overlap_stats['v2_unmatched']} entities only found by V2 BERT")
    report_lines.append(f"**spaCy unique**: {overlap_stats['spacy_unmatched']} entities only found by spaCy Hybrid")
    report_lines.append("")

    # Model-specific patterns
    report_lines.append("## Model-Specific Patterns")
    report_lines.append("")

    # V2-only entities (sample)
    report_lines.append("### Entities Found Only by V2 BERT NER")
    report_lines.append("")
    if len(overlap_stats['v2_unmatched_list']) > 0:
        report_lines.append("Sample of V2-unique entities:")
        report_lines.append("")
        for paper_id, mention in overlap_stats['v2_unmatched_list'][:20]:
            report_lines.append(f"- `{paper_id}`: {mention}")
        if overlap_stats['v2_unmatched'] > 20:
            report_lines.append(f"- ... and {overlap_stats['v2_unmatched'] - 20} more")
    else:
        report_lines.append("None")
    report_lines.append("")

    # spaCy-only entities (sample)
    report_lines.append("### Entities Found Only by spaCy Hybrid NER")
    report_lines.append("")
    if len(overlap_stats['spacy_unmatched_list']) > 0:
        report_lines.append("Sample of spaCy-unique entities:")
        report_lines.append("")
        for paper_id, mention in overlap_stats['spacy_unmatched_list'][:20]:
            report_lines.append(f"- `{paper_id}`: {mention}")
        if overlap_stats['spacy_unmatched'] > 20:
            report_lines.append(f"- ... and {overlap_stats['spacy_unmatched'] - 20} more")
    else:
        report_lines.append("None")
    report_lines.append("")

    # Papers with no entities from either model
    report_lines.append("### Papers with No Entities Detected")
    report_lines.append("")
    all_papers_with_entities = set(v2_df['paper_id'].unique()) | set(spacy_df['paper_id'].unique())
    report_lines.append(f"**Count**: {coverage_stats['v2_papers'] + coverage_stats['spacy_only_papers'] - len(all_papers_with_entities)} papers")
    report_lines.append("")
    report_lines.append("*These papers may be false negatives or genuinely non-resource papers.*")
    report_lines.append("")

    # Footer
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*Note: This comparison is based on model predictions. Manual validation will determine actual precision/recall.*")
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
    logger.info("SCRIPT 04c: NER COMPARISON")
    logger.info("=" * 70)

    start_time = datetime.now()

    # ------------------------------------------------------------------------
    # 1. Load NER results
    # ------------------------------------------------------------------------
    logger.info("\n📚 Loading NER results from both models...")

    v2_df = load_ner_results(V2_NER_RESULTS, 'v2')
    spacy_df = load_ner_results(SPACY_NER_RESULTS, 'spacy')

    # Check for missing files
    missing_files = []
    if v2_df is None:
        missing_files.append("V2 BERT NER")
    if spacy_df is None:
        missing_files.append("spaCy Hybrid NER")

    if missing_files:
        logger.error(f"\n❌ Missing NER results for: {', '.join(missing_files)}")
        logger.error("Please run the corresponding scripts:")
        if "V2 BERT NER" in missing_files:
            logger.error("  - python scripts/04a_run_v2_ner.py")
        if "spaCy Hybrid NER" in missing_files:
            logger.error("  - python scripts/04b_run_spacy_ner.py")
        return 1

    # ------------------------------------------------------------------------
    # 2. Calculate paper-level coverage
    # ------------------------------------------------------------------------
    logger.info("\n📊 Calculating paper-level coverage...")

    coverage_stats = calculate_paper_coverage(v2_df, spacy_df)

    logger.info(f"   V2 papers: {coverage_stats['v2_papers']}")
    logger.info(f"   spaCy papers: {coverage_stats['spacy_papers']}")
    logger.info(f"   Both: {coverage_stats['both_papers']}")
    logger.info(f"   V2 only: {coverage_stats['v2_only_papers']}")
    logger.info(f"   spaCy only: {coverage_stats['spacy_only_papers']}")

    # ------------------------------------------------------------------------
    # 3. Calculate entity-level overlap
    # ------------------------------------------------------------------------
    overlap_stats = calculate_entity_overlap(v2_df, spacy_df)

    # ------------------------------------------------------------------------
    # 4. Merge results for CSV export
    # ------------------------------------------------------------------------
    logger.info("\n🔗 Merging results for export...")

    # Combine both DataFrames
    df_merged = pd.concat([v2_df, spacy_df], ignore_index=True)

    logger.info(f"✓ Merged {len(df_merged)} entity extractions from both models")

    # ------------------------------------------------------------------------
    # 5. Save merged results
    # ------------------------------------------------------------------------
    logger.info(f"\n💾 Saving comparison data...")

    NER_DIR.mkdir(parents=True, exist_ok=True)
    df_merged.to_csv(OUTPUT_CSV, index=False)

    logger.info(f"✓ Saved to: {OUTPUT_CSV}")
    logger.info(f"  Size: {OUTPUT_CSV.stat().st_size / 1024:.1f} KB")

    # ------------------------------------------------------------------------
    # 6. Generate markdown report
    # ------------------------------------------------------------------------
    generate_markdown_report(coverage_stats, overlap_stats, v2_df, spacy_df, OUTPUT_REPORT)

    # ------------------------------------------------------------------------
    # 7. Final report
    # ------------------------------------------------------------------------
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ SCRIPT 04c COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Log saved to: {LOG_FILE}")
    logger.info(f"Outputs:")
    logger.info(f"  - Comparison data: {OUTPUT_CSV}")
    logger.info(f"  - Report: {OUTPUT_REPORT}")
    logger.info(f"\nNext step: Review NER comparison report")
    logger.info(f"  cat {OUTPUT_REPORT}")
    logger.info(f"{'=' * 70}")

    return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
