#!/usr/bin/env python3
"""
Script 04: Deep analysis of BPE contamination in Phase 4 NER results.

This script performs comprehensive analysis of BPE (Byte-Pair Encoding) tokenization
artifacts that contaminate Phase 4 NER results. BPE artifacts include:
- "Ġ" prefix markers (e.g., "Ġprotein" instead of "protein")
- Subword fragments (e.g., "pro te in" instead of "protein")
- Mixed contaminated and clean entities in the same dataset

Analysis approach:
1. Load BPE artifact report from Script 01
2. Quantify contamination (% papers affected, % entities affected)
3. Compare F1 scores: Phase 4 raw vs Phase 4 cleaned vs V2
4. Analyze common artifact patterns and their frequency
5. Create before/after examples showing cleaning effectiveness
6. Generate visualizations (histograms, distributions)
7. Assess impact on downstream metrics

Key questions answered:
- What % of Phase 4 results are contaminated?
- How much does BPE contamination hurt F1 scores?
- What are the most common artifact patterns?
- Does cleaning fully restore performance?
- Which papers are most affected?

Outputs:
- results/bpe_contamination_report.md: Detailed markdown report
- results/bpe_impact_on_metrics.csv: F1 degradation analysis
- results/bpe_artifact_patterns.json: Common patterns with frequencies
- figures/bpe_contamination_histogram.png: Contamination distribution
- figures/bpe_f1_comparison.png: F1 scores before/after cleaning

Author: Generated for Phase 4 vs V2 NER comparison
Date: 2025-11-05
"""

import argparse
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from tqdm import tqdm

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.bpe_cleaning import (
    clean_bpe_entity,
    compare_before_after_cleaning,
    detect_bpe_artifacts,
    generate_bpe_report,
)
from utils.data_loading import parse_entity_list
from utils.entity_matching import match_entities
from utils.metrics import entity_level_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('04_analyze_bpe_artifacts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths (relative to script location)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RESULTS_DIR = PROJECT_ROOT / "comparison_phase4_v_oldmodel" / "results"
FIGURES_DIR = PROJECT_ROOT / "comparison_phase4_v_oldmodel" / "figures"

# Matplotlib configuration
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def load_bpe_report(file_path: Optional[Path] = None) -> Dict:
    """
    Load BPE artifact report from Script 01.

    Args:
        file_path: Optional custom path. If None, uses default location.

    Returns:
        Dictionary with BPE contamination report
    """
    if file_path is None:
        file_path = RESULTS_DIR / "bpe_artifact_report.json"

    if not file_path.exists():
        raise FileNotFoundError(
            f"BPE artifact report not found: {file_path}\n"
            f"Please run Script 01 first: 01_preprocess_and_align.py"
        )

    logger.info(f"Loading BPE artifact report from: {file_path}")
    with open(file_path, 'r') as f:
        report = json.load(f)

    logger.info(f"Loaded report with {report.get('total_rows', 0):,} papers analyzed")
    return report


def load_aligned_papers(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load aligned papers from Script 01 output.

    Args:
        file_path: Optional custom path. If None, uses default location.

    Returns:
        DataFrame with aligned papers including Phase 4 raw and cleaned entities
    """
    if file_path is None:
        file_path = RESULTS_DIR / "aligned_papers.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Aligned papers file not found: {file_path}\n"
            f"Please run Script 01 first: 01_preprocess_and_align.py"
        )

    logger.info(f"Loading aligned papers from: {file_path}")
    df = pd.read_csv(file_path)

    # Parse entity lists
    entity_columns = [
        'true_com', 'true_ful',
        'v2_com', 'v2_ful',
        'p4_com_raw', 'p4_com_clean',
        'p4_ful_raw', 'p4_ful_clean'
    ]

    for col in entity_columns:
        if col in df.columns:
            df[col] = df[col].apply(parse_entity_list)

    logger.info(f"Loaded {len(df):,} aligned papers")
    return df


def quantify_contamination(aligned_df: pd.DataFrame) -> Dict:
    """
    Quantify BPE contamination levels across Phase 4 results.

    Args:
        aligned_df: Aligned papers DataFrame

    Returns:
        Dictionary with contamination statistics
    """
    logger.info("\nQuantifying BPE contamination...")

    stats = {
        'total_papers': len(aligned_df),
        'papers_with_entities': 0,
        'papers_with_contamination': 0,
        'total_entities': 0,
        'contaminated_entities': 0,
        'contamination_by_paper': [],
    }

    for idx, row in tqdm(aligned_df.iterrows(), total=len(aligned_df), desc="Analyzing contamination"):
        # Combine raw entities
        raw_entities = []
        for col in ['p4_com_raw', 'p4_ful_raw']:
            if col in row and isinstance(row[col], list):
                raw_entities.extend(row[col])

        if not raw_entities:
            continue

        stats['papers_with_entities'] += 1

        # Check each entity for contamination
        contaminated_count = 0
        for entity in raw_entities:
            stats['total_entities'] += 1
            if detect_bpe_artifacts(entity):
                contaminated_count += 1
                stats['contaminated_entities'] += 1

        # Paper-level contamination
        if contaminated_count > 0:
            stats['papers_with_contamination'] += 1
            contamination_rate = contaminated_count / len(raw_entities)
            stats['contamination_by_paper'].append({
                'paper_id': row['paper_id'],
                'total_entities': len(raw_entities),
                'contaminated_entities': contaminated_count,
                'contamination_rate': contamination_rate,
            })

    # Calculate overall rates
    stats['paper_contamination_rate'] = (
        stats['papers_with_contamination'] / stats['papers_with_entities']
        if stats['papers_with_entities'] > 0 else 0.0
    )
    stats['entity_contamination_rate'] = (
        stats['contaminated_entities'] / stats['total_entities']
        if stats['total_entities'] > 0 else 0.0
    )

    logger.info(f"\nContamination Statistics:")
    logger.info(f"  Papers with entities: {stats['papers_with_entities']:,}")
    logger.info(f"  Papers with contamination: {stats['papers_with_contamination']:,} "
                f"({stats['paper_contamination_rate']:.1%})")
    logger.info(f"  Total entities: {stats['total_entities']:,}")
    logger.info(f"  Contaminated entities: {stats['contaminated_entities']:,} "
                f"({stats['entity_contamination_rate']:.1%})")

    return stats


def analyze_artifact_patterns(aligned_df: pd.DataFrame) -> Dict:
    """
    Analyze common BPE artifact patterns.

    Args:
        aligned_df: Aligned papers DataFrame

    Returns:
        Dictionary with artifact pattern analysis
    """
    logger.info("\nAnalyzing artifact patterns...")

    patterns = {
        'g_marker_count': 0,
        'short_tokens_count': 0,
        'mixed_contamination': 0,
        'example_artifacts': [],
        'cleaned_examples': [],
    }

    g_marker_pattern_counter = Counter()
    short_token_examples = []

    for idx, row in tqdm(aligned_df.iterrows(), total=len(aligned_df), desc="Analyzing patterns"):
        raw_entities = []
        for col in ['p4_com_raw', 'p4_ful_raw']:
            if col in row and isinstance(row[col], list):
                raw_entities.extend(row[col])

        for entity in raw_entities:
            if not entity:
                continue

            # Check for Ġ marker
            if 'Ġ' in entity:
                patterns['g_marker_count'] += 1
                # Count specific patterns
                g_marker_pattern_counter[entity] += 1

                # Collect examples (limit to 50)
                if len(patterns['example_artifacts']) < 50:
                    cleaned = clean_bpe_entity(entity)
                    patterns['example_artifacts'].append({
                        'original': entity,
                        'cleaned': cleaned,
                        'paper_id': row['paper_id']
                    })

            # Check for short tokens (potential subwords)
            tokens = entity.strip().split()
            if len(tokens) >= 3:
                short_tokens = [t for t in tokens if len(t) <= 2 and t.isalpha()]
                if len(short_tokens) >= 2:
                    patterns['short_tokens_count'] += 1
                    if len(short_token_examples) < 20:
                        short_token_examples.append({
                            'original': entity,
                            'cleaned': clean_bpe_entity(entity),
                            'paper_id': row['paper_id']
                        })

    # Get top patterns
    patterns['top_g_marker_patterns'] = [
        {'pattern': pattern, 'count': count}
        for pattern, count in g_marker_pattern_counter.most_common(20)
    ]

    patterns['short_token_examples'] = short_token_examples

    logger.info(f"\nArtifact Pattern Statistics:")
    logger.info(f"  Entities with Ġ markers: {patterns['g_marker_count']:,}")
    logger.info(f"  Entities with short tokens: {patterns['short_tokens_count']:,}")
    logger.info(f"  Unique Ġ patterns: {len(g_marker_pattern_counter):,}")

    return patterns


def compare_f1_scores(aligned_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare F1 scores between Phase 4 raw, cleaned, and V2 on papers with ground truth.

    Args:
        aligned_df: Aligned papers DataFrame

    Returns:
        DataFrame with per-paper F1 comparison
    """
    logger.info("\nComparing F1 scores across systems...")

    # Filter to papers with ground truth
    has_ground_truth = (
        aligned_df['true_com'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False) |
        aligned_df['true_ful'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)
    )
    test_df = aligned_df[has_ground_truth].copy()

    logger.info(f"  Evaluating on {len(test_df):,} papers with ground truth")

    results = []

    for idx, row in tqdm(test_df.iterrows(), total=len(test_df), desc="Calculating F1 scores"):
        paper_id = row['paper_id']

        # Get ground truth
        true_entities = list(set(
            (row.get('true_com', []) if isinstance(row.get('true_com'), list) else []) +
            (row.get('true_ful', []) if isinstance(row.get('true_ful'), list) else [])
        ))

        if not true_entities:
            continue

        # V2 predictions
        v2_entities = list(set(
            (row.get('v2_com', []) if isinstance(row.get('v2_com'), list) else []) +
            (row.get('v2_ful', []) if isinstance(row.get('v2_ful'), list) else [])
        ))

        # Phase 4 raw
        p4_raw_entities = list(set(
            (row.get('p4_com_raw', []) if isinstance(row.get('p4_com_raw'), list) else []) +
            (row.get('p4_ful_raw', []) if isinstance(row.get('p4_ful_raw'), list) else [])
        ))

        # Phase 4 cleaned
        p4_clean_entities = list(set(
            (row.get('p4_com_clean', []) if isinstance(row.get('p4_com_clean'), list) else []) +
            (row.get('p4_ful_clean', []) if isinstance(row.get('p4_ful_clean'), list) else [])
        ))

        # Calculate F1 for each system
        v2_metrics = entity_level_metrics(v2_entities, true_entities)
        p4_raw_metrics = entity_level_metrics(p4_raw_entities, true_entities)
        p4_clean_metrics = entity_level_metrics(p4_clean_entities, true_entities)

        # Check for contamination in raw Phase 4
        contaminated_count = sum(1 for e in p4_raw_entities if detect_bpe_artifacts(e))
        has_contamination = contaminated_count > 0

        results.append({
            'paper_id': paper_id,
            'title': row.get('title', ''),
            'v2_f1': v2_metrics['f1'],
            'phase4_raw_f1': p4_raw_metrics['f1'],
            'phase4_clean_f1': p4_clean_metrics['f1'],
            'has_contamination': has_contamination,
            'contaminated_entities': contaminated_count,
            'total_entities': len(p4_raw_entities),
            'contamination_rate': contaminated_count / len(p4_raw_entities) if p4_raw_entities else 0.0,
            'f1_improvement': p4_clean_metrics['f1'] - p4_raw_metrics['f1'],
            'raw_vs_v2': p4_raw_metrics['f1'] - v2_metrics['f1'],
            'clean_vs_v2': p4_clean_metrics['f1'] - v2_metrics['f1'],
        })

    results_df = pd.DataFrame(results)

    # Summary statistics
    logger.info(f"\nF1 Score Comparison:")
    logger.info(f"  V2 mean F1: {results_df['v2_f1'].mean():.4f}")
    logger.info(f"  Phase 4 raw mean F1: {results_df['phase4_raw_f1'].mean():.4f}")
    logger.info(f"  Phase 4 cleaned mean F1: {results_df['phase4_clean_f1'].mean():.4f}")
    logger.info(f"  Mean improvement from cleaning: {results_df['f1_improvement'].mean():.4f}")

    # Impact of contamination
    contaminated = results_df[results_df['has_contamination']]
    clean_papers = results_df[~results_df['has_contamination']]

    if len(contaminated) > 0:
        logger.info(f"\nImpact of Contamination:")
        logger.info(f"  Papers with contamination: {len(contaminated):,}")
        logger.info(f"  Mean F1 improvement for contaminated papers: {contaminated['f1_improvement'].mean():.4f}")
        logger.info(f"  Papers with no contamination: {len(clean_papers):,}")
        logger.info(f"  Mean F1 for clean papers: {clean_papers['phase4_raw_f1'].mean():.4f}")

    return results_df


def create_contamination_histogram(
    contamination_stats: Dict,
    output_path: Path
):
    """
    Create histogram showing contamination distribution across papers.

    Args:
        contamination_stats: Contamination statistics from quantify_contamination()
        output_path: Path to save figure
    """
    logger.info("\nCreating contamination histogram...")

    contamination_by_paper = contamination_stats['contamination_by_paper']

    if not contamination_by_paper:
        logger.warning("No contamination data to plot")
        return

    contamination_rates = [p['contamination_rate'] for p in contamination_by_paper]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(contamination_rates, bins=20, edgecolor='black', alpha=0.7)
    ax.set_xlabel('Contamination Rate (fraction of entities with BPE artifacts)', fontsize=12)
    ax.set_ylabel('Number of Papers', fontsize=12)
    ax.set_title('Distribution of BPE Contamination Across Phase 4 Results', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add statistics text
    mean_rate = np.mean(contamination_rates)
    median_rate = np.median(contamination_rates)
    stats_text = f'Mean: {mean_rate:.1%}\nMedian: {median_rate:.1%}\nPapers: {len(contamination_rates):,}'
    ax.text(0.98, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"✓ Saved contamination histogram: {output_path}")
    plt.close()


def create_f1_comparison_plot(
    f1_comparison_df: pd.DataFrame,
    output_path: Path
):
    """
    Create plot comparing F1 scores before and after cleaning.

    Args:
        f1_comparison_df: DataFrame with F1 comparison results
        output_path: Path to save figure
    """
    logger.info("\nCreating F1 comparison plot...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Box plot of F1 scores
    f1_data = [
        f1_comparison_df['v2_f1'],
        f1_comparison_df['phase4_raw_f1'],
        f1_comparison_df['phase4_clean_f1']
    ]
    labels = ['V2', 'Phase 4 Raw', 'Phase 4 Cleaned']

    bp = ax1.boxplot(f1_data, labels=labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], ['lightblue', 'lightcoral', 'lightgreen']):
        patch.set_facecolor(color)

    ax1.set_ylabel('F1 Score', fontsize=12)
    ax1.set_title('F1 Score Distribution by System', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')

    # Plot 2: Scatter plot showing improvement from cleaning
    contaminated = f1_comparison_df[f1_comparison_df['has_contamination']]
    clean_papers = f1_comparison_df[~f1_comparison_df['has_contamination']]

    ax2.scatter(contaminated['phase4_raw_f1'], contaminated['phase4_clean_f1'],
                alpha=0.5, s=50, c='red', label=f'Contaminated ({len(contaminated)})')
    ax2.scatter(clean_papers['phase4_raw_f1'], clean_papers['phase4_clean_f1'],
                alpha=0.5, s=50, c='green', label=f'Clean ({len(clean_papers)})')

    # Add diagonal line (no change)
    lims = [0, 1]
    ax2.plot(lims, lims, 'k--', alpha=0.5, linewidth=1, label='No change')

    ax2.set_xlabel('Phase 4 Raw F1', fontsize=12)
    ax2.set_ylabel('Phase 4 Cleaned F1', fontsize=12)
    ax2.set_title('Impact of BPE Cleaning on F1 Scores', fontsize=13, fontweight='bold')
    ax2.legend(loc='lower right')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"✓ Saved F1 comparison plot: {output_path}")
    plt.close()


def generate_detailed_report(
    contamination_stats: Dict,
    artifact_patterns: Dict,
    f1_comparison_df: pd.DataFrame
) -> str:
    """
    Generate detailed markdown report on BPE contamination.

    Args:
        contamination_stats: Contamination statistics
        artifact_patterns: Artifact pattern analysis
        f1_comparison_df: F1 score comparison DataFrame

    Returns:
        Markdown-formatted report string
    """
    report = []
    report.append("# BPE Contamination Analysis: Phase 4 NER Results")
    report.append("")
    report.append("## Executive Summary")
    report.append("")
    report.append("This report analyzes BPE (Byte-Pair Encoding) tokenization artifacts that")
    report.append("contaminate Phase 4 NER results. BPE artifacts occur when the tokenizer's")
    report.append("special markers (e.g., 'Ġ' for spaces) leak into the final output.")
    report.append("")

    report.append("## Contamination Levels")
    report.append("")
    report.append("### Overall Statistics")
    report.append("")
    report.append(f"- **Total papers with entities**: {contamination_stats['papers_with_entities']:,}")
    report.append(f"- **Papers with contamination**: {contamination_stats['papers_with_contamination']:,} "
                  f"({contamination_stats['paper_contamination_rate']:.1%})")
    report.append(f"- **Total entities extracted**: {contamination_stats['total_entities']:,}")
    report.append(f"- **Contaminated entities**: {contamination_stats['contaminated_entities']:,} "
                  f"({contamination_stats['entity_contamination_rate']:.1%})")
    report.append("")

    report.append("### Severity Assessment")
    report.append("")
    if contamination_stats['entity_contamination_rate'] > 0.5:
        report.append("**🔴 CRITICAL**: Over 50% of entities are contaminated")
    elif contamination_stats['entity_contamination_rate'] > 0.2:
        report.append("**🟡 HIGH**: 20-50% of entities are contaminated")
    elif contamination_stats['entity_contamination_rate'] > 0.05:
        report.append("**🟢 MODERATE**: 5-20% of entities are contaminated")
    else:
        report.append("**✓ LOW**: Less than 5% of entities are contaminated")
    report.append("")

    report.append("## Artifact Patterns")
    report.append("")
    report.append("### Common Pattern Types")
    report.append("")
    report.append(f"- **Ġ marker artifacts**: {artifact_patterns['g_marker_count']:,} occurrences")
    report.append(f"- **Short token fragments**: {artifact_patterns['short_tokens_count']:,} occurrences")
    report.append("")

    if artifact_patterns.get('top_g_marker_patterns'):
        report.append("### Top 10 Most Common Ġ Marker Patterns")
        report.append("")
        report.append("| Pattern | Occurrences |")
        report.append("|---------|-------------|")
        for item in artifact_patterns['top_g_marker_patterns'][:10]:
            # Escape pipes in pattern
            pattern = item['pattern'].replace('|', '\\|')
            report.append(f"| `{pattern}` | {item['count']:,} |")
        report.append("")

    if artifact_patterns.get('example_artifacts'):
        report.append("### Example Artifacts (Before → After Cleaning)")
        report.append("")
        for example in artifact_patterns['example_artifacts'][:10]:
            report.append(f"- `{example['original']}` → `{example['cleaned']}`")
        report.append("")

    report.append("## Impact on F1 Scores")
    report.append("")

    if len(f1_comparison_df) > 0:
        report.append("### Overall Performance")
        report.append("")
        report.append("| System | Mean F1 | Median F1 | Std Dev |")
        report.append("|--------|---------|-----------|---------|")
        for system in ['v2_f1', 'phase4_raw_f1', 'phase4_clean_f1']:
            name = system.replace('_f1', '').replace('_', ' ').title()
            report.append(
                f"| {name} | "
                f"{f1_comparison_df[system].mean():.4f} | "
                f"{f1_comparison_df[system].median():.4f} | "
                f"{f1_comparison_df[system].std():.4f} |"
            )
        report.append("")

        report.append("### Impact of BPE Contamination")
        report.append("")
        contaminated = f1_comparison_df[f1_comparison_df['has_contamination']]
        clean_papers = f1_comparison_df[~f1_comparison_df['has_contamination']]

        report.append(f"- **Papers with contamination**: {len(contaminated):,}")
        if len(contaminated) > 0:
            report.append(f"  - Mean F1 improvement from cleaning: {contaminated['f1_improvement'].mean():.4f}")
            report.append(f"  - Max F1 improvement: {contaminated['f1_improvement'].max():.4f}")
            report.append(f"  - Papers where cleaning helped (F1 improved): "
                         f"{(contaminated['f1_improvement'] > 0).sum()} "
                         f"({(contaminated['f1_improvement'] > 0).mean():.1%})")

        report.append("")
        report.append(f"- **Papers without contamination**: {len(clean_papers):,}")
        if len(clean_papers) > 0:
            report.append(f"  - Mean F1: {clean_papers['phase4_raw_f1'].mean():.4f}")

        report.append("")
        report.append("### Worst Affected Papers")
        report.append("")
        report.append("Papers with largest F1 degradation due to BPE contamination:")
        report.append("")
        worst = contaminated.nlargest(5, 'contamination_rate')
        for idx, row in worst.iterrows():
            report.append(f"- **{row['paper_id']}**: {row['contamination_rate']:.1%} contamination, "
                         f"F1 improved by {row['f1_improvement']:.3f} after cleaning")
        report.append("")

    report.append("## Conclusions")
    report.append("")
    report.append("### Key Findings")
    report.append("")
    report.append(f"1. **Contamination is {'widespread' if contamination_stats['entity_contamination_rate'] > 0.2 else 'limited'}**: "
                  f"{contamination_stats['entity_contamination_rate']:.1%} of Phase 4 entities contain BPE artifacts")
    report.append(f"2. **Cleaning {'significantly' if f1_comparison_df['f1_improvement'].mean() > 0.05 else 'moderately'} improves performance**: "
                  f"Mean F1 improvement of {f1_comparison_df['f1_improvement'].mean():.4f}")
    report.append(f"3. **Primary artifact type**: Ġ markers ({artifact_patterns['g_marker_count']:,} occurrences)")
    report.append("")

    report.append("### Recommendations")
    report.append("")
    report.append("1. **Always use cleaned Phase 4 results** for downstream analysis")
    report.append("2. **Investigate tokenization pipeline** to prevent artifact leakage at source")
    report.append("3. **Add validation checks** to detect BPE artifacts in production")
    report.append("4. **Monitor contamination rates** in future model versions")
    report.append("")

    return "\n".join(report)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Analyze BPE contamination in Phase 4 NER results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard analysis
  python 04_analyze_bpe_artifacts.py

  # Custom paths
  python 04_analyze_bpe_artifacts.py --input custom_aligned.csv

  # Custom output directory
  python 04_analyze_bpe_artifacts.py --output custom_results/ --figures custom_figures/
        """
    )

    parser.add_argument(
        '--input',
        type=Path,
        default=None,
        help='Path to aligned papers CSV (default: results/aligned_papers.csv)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=RESULTS_DIR,
        help='Output directory for results (default: results/)'
    )

    parser.add_argument(
        '--figures',
        type=Path,
        default=FIGURES_DIR,
        help='Output directory for figures (default: figures/)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("=" * 100)
    logger.info("SCRIPT 04: Analyze BPE Artifacts")
    logger.info("=" * 100)
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Figures directory: {args.figures}")
    logger.info("")

    try:
        # Create output directories
        args.output.mkdir(parents=True, exist_ok=True)
        args.figures.mkdir(parents=True, exist_ok=True)

        # Step 1: Load data
        logger.info("STEP 1: Loading data...")
        aligned_df = load_aligned_papers(args.input)

        # Step 2: Quantify contamination
        logger.info("\nSTEP 2: Quantifying contamination...")
        contamination_stats = quantify_contamination(aligned_df)

        # Step 3: Analyze artifact patterns
        logger.info("\nSTEP 3: Analyzing artifact patterns...")
        artifact_patterns = analyze_artifact_patterns(aligned_df)

        # Step 4: Compare F1 scores
        logger.info("\nSTEP 4: Comparing F1 scores...")
        f1_comparison_df = compare_f1_scores(aligned_df)

        # Step 5: Create visualizations
        logger.info("\nSTEP 5: Creating visualizations...")
        create_contamination_histogram(
            contamination_stats,
            args.figures / "bpe_contamination_histogram.png"
        )
        create_f1_comparison_plot(
            f1_comparison_df,
            args.figures / "bpe_f1_comparison.png"
        )

        # Step 6: Generate detailed report
        logger.info("\nSTEP 6: Generating detailed report...")
        report = generate_detailed_report(
            contamination_stats,
            artifact_patterns,
            f1_comparison_df
        )

        # Step 7: Save outputs
        logger.info("\nSTEP 7: Saving outputs...")

        # Contamination report (markdown)
        report_path = args.output / "bpe_contamination_report.md"
        with open(report_path, 'w') as f:
            f.write(report)
        logger.info(f"✓ Saved contamination report: {report_path}")

        # F1 impact CSV
        impact_path = args.output / "bpe_impact_on_metrics.csv"
        f1_comparison_df.to_csv(impact_path, index=False)
        logger.info(f"✓ Saved F1 impact data: {impact_path}")

        # Artifact patterns JSON
        patterns_path = args.output / "bpe_artifact_patterns.json"
        with open(patterns_path, 'w') as f:
            json.dump(artifact_patterns, f, indent=2, default=str)
        logger.info(f"✓ Saved artifact patterns: {patterns_path}")

        # Contamination statistics JSON
        stats_path = args.output / "bpe_contamination_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(contamination_stats, f, indent=2, default=str)
        logger.info(f"✓ Saved contamination statistics: {stats_path}")

        logger.info("\n" + "=" * 100)
        logger.info("ANALYSIS COMPLETE!")
        logger.info("=" * 100)
        logger.info(f"\nKey findings:")
        logger.info(f"  Entity contamination rate: {contamination_stats['entity_contamination_rate']:.1%}")
        logger.info(f"  Paper contamination rate: {contamination_stats['paper_contamination_rate']:.1%}")
        logger.info(f"  Mean F1 improvement from cleaning: {f1_comparison_df['f1_improvement'].mean():.4f}")
        logger.info(f"\nAll outputs saved to:")
        logger.info(f"  Results: {args.output}")
        logger.info(f"  Figures: {args.figures}")

        return 0

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
