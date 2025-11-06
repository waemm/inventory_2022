#!/usr/bin/env python3
"""
Script 02: Evaluate V2 and Phase 4 NER systems on test split with ground truth.

This script evaluates both V2 and Phase 4 NER systems (raw + cleaned) on the
NER test split containing 67 papers with manually annotated ground truth entities.

Evaluation approach:
1. Load aligned papers from Script 01
2. Filter to papers with ground truth (test split)
3. For each paper:
   - Compare V2 predictions vs ground truth using match_entities()
   - Compare Phase 4 raw predictions vs ground truth
   - Compare Phase 4 cleaned predictions vs ground truth
4. Calculate entity-level metrics (Precision, Recall, F1) using entity_level_metrics()
5. Statistical significance testing (McNemar's test, bootstrap CI)
6. Generate detailed examples (10 papers showing successes/failures)

Key metrics:
- Precision: What % of predicted entities are correct?
- Recall: What % of true entities were found?
- F1-score: Harmonic mean of precision and recall
- Statistical significance: Are differences meaningful?

Outputs:
- results/test_split_metrics.csv: Per-paper metrics for all systems
- results/test_split_aggregate.json: Overall F1, P, R with confidence intervals
- results/test_split_examples.txt: Detailed examples of predictions
- results/test_split_comparison.md: Summary report comparing systems

Author: Generated for Phase 4 vs V2 NER comparison
Date: 2025-11-05
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import chi2
from tqdm import tqdm

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.data_loading import parse_entity_list, load_aligned_papers
from utils.entity_matching import match_entities
from utils.metrics import (
    aggregate_metrics,
    bootstrap_confidence_interval,
    entity_level_metrics,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('02_evaluate_on_test_split.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths (relative to script location)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "comparison_phase4_v_oldmodel" / "data"
RESULTS_DIR = PROJECT_ROOT / "comparison_phase4_v_oldmodel" / "results"


# Note: load_aligned_papers() is now imported from utils.data_loading


def filter_test_split(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to papers with ground truth (test split).

    Args:
        df: Aligned papers DataFrame

    Returns:
        DataFrame containing only test split papers with ground truth
    """
    logger.info("Filtering to test split papers with ground truth...")

    # Papers with ground truth have non-empty true_com or true_ful
    has_ground_truth = (
        df['true_com'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False) |
        df['true_ful'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)
    )

    test_df = df[has_ground_truth].copy()

    logger.info(f"Test split: {len(test_df):,} papers with ground truth")
    logger.info(f"  - All papers: {len(df):,}")
    logger.info(f"  - Coverage: {len(test_df)/len(df):.1%}")

    return test_df


def evaluate_predictions_vs_ground_truth(
    predicted_entities: List[str],
    true_entities: List[str],
    match_strategy: str = 'exact'
) -> Dict[str, float]:
    """
    Evaluate predicted entities against ground truth.

    Args:
        predicted_entities: List of predicted entity strings
        true_entities: List of ground truth entity strings
        match_strategy: Matching strategy ('exact', 'fuzzy', 'partial', 'token_overlap')

    Returns:
        Dictionary with precision, recall, F1, and confusion matrix counts
    """
    return entity_level_metrics(
        predicted_entities=predicted_entities,
        true_entities=true_entities,
        match_strategy=match_strategy
    )


def evaluate_all_systems_on_paper(
    paper_row: pd.Series,
    match_strategy: str = 'exact'
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate all systems (V2, Phase 4 raw, Phase 4 cleaned) on a single paper.

    Args:
        paper_row: Row from aligned DataFrame containing predictions and ground truth
        match_strategy: Matching strategy for entity comparison

    Returns:
        Dictionary with metrics for each system
    """
    # Extract entities
    true_common = paper_row.get('true_com', [])
    true_full = paper_row.get('true_ful', [])

    v2_common = paper_row.get('v2_com', [])
    v2_full = paper_row.get('v2_ful', [])

    p4_common_raw = paper_row.get('p4_com_raw', [])
    p4_common_clean = paper_row.get('p4_com_clean', [])
    p4_full_raw = paper_row.get('p4_ful_raw', [])
    p4_full_clean = paper_row.get('p4_ful_clean', [])

    # Combine true entities (use both common and full)
    true_entities = list(set(true_common + true_full))

    # Evaluate each system
    results = {}

    # V2 system (combine common and full)
    v2_predicted = list(set(v2_common + v2_full))
    results['v2'] = evaluate_predictions_vs_ground_truth(
        v2_predicted, true_entities, match_strategy
    )

    # Phase 4 raw (combine common and full)
    p4_raw_predicted = list(set(p4_common_raw + p4_full_raw))
    results['phase4_raw'] = evaluate_predictions_vs_ground_truth(
        p4_raw_predicted, true_entities, match_strategy
    )

    # Phase 4 cleaned (combine common and full)
    p4_clean_predicted = list(set(p4_common_clean + p4_full_clean))
    results['phase4_cleaned'] = evaluate_predictions_vs_ground_truth(
        p4_clean_predicted, true_entities, match_strategy
    )

    return results


def evaluate_test_split(
    test_df: pd.DataFrame,
    match_strategy: str = 'exact'
) -> Tuple[pd.DataFrame, Dict]:
    """
    Evaluate all systems on entire test split.

    Args:
        test_df: Test split DataFrame
        match_strategy: Matching strategy for entity comparison

    Returns:
        Tuple of (per_paper_metrics_df, aggregate_metrics_dict)
    """
    logger.info(f"\nEvaluating all systems on test split ({len(test_df):,} papers)...")
    logger.info(f"Matching strategy: {match_strategy}")

    per_paper_results = []

    for idx, row in tqdm(test_df.iterrows(), total=len(test_df), desc="Evaluating papers"):
        paper_id = row['paper_id']

        # Evaluate all systems on this paper
        system_metrics = evaluate_all_systems_on_paper(row, match_strategy)

        # Store results
        result_row = {
            'paper_id': paper_id,
            'title': row.get('title', ''),
        }

        # Add metrics for each system
        for system, metrics in system_metrics.items():
            result_row[f'{system}_precision'] = metrics['precision']
            result_row[f'{system}_recall'] = metrics['recall']
            result_row[f'{system}_f1'] = metrics['f1']
            result_row[f'{system}_tp'] = metrics['tp']
            result_row[f'{system}_fp'] = metrics['fp']
            result_row[f'{system}_fn'] = metrics['fn']
            result_row[f'{system}_total_predicted'] = metrics['total_predicted']
            result_row[f'{system}_total_true'] = metrics['total_true']

        per_paper_results.append(result_row)

    # Create DataFrame
    per_paper_df = pd.DataFrame(per_paper_results)

    # Calculate aggregate metrics for each system
    logger.info("\nCalculating aggregate metrics...")

    aggregate_results = {}

    for system in ['v2', 'phase4_raw', 'phase4_cleaned']:
        # Extract per-paper metrics
        system_metrics = []
        for _, row in per_paper_df.iterrows():
            system_metrics.append({
                'precision': row[f'{system}_precision'],
                'recall': row[f'{system}_recall'],
                'f1': row[f'{system}_f1'],
                'tp': row[f'{system}_tp'],
                'fp': row[f'{system}_fp'],
                'fn': row[f'{system}_fn'],
            })

        # Aggregate
        agg = aggregate_metrics(system_metrics, include_ci=True, confidence=0.95)
        aggregate_results[system] = agg

        # Log results
        logger.info(f"\n{system.upper()}:")
        logger.info(f"  Micro-averaged F1: {agg['micro']['f1']:.4f}")
        logger.info(f"  Macro-averaged F1: {agg['macro']['f1']:.4f} ± {agg['macro']['f1_std']:.4f}")
        if 'ci' in agg:
            logger.info(f"  95% CI: [{agg['ci']['lower']:.4f}, {agg['ci']['upper']:.4f}]")

    return per_paper_df, aggregate_results


def mcnemar_test(
    system1_correct: List[bool],
    system2_correct: List[bool]
) -> Dict[str, float]:
    """
    Perform McNemar's test to compare two systems.

    McNemar's test is appropriate for comparing paired nominal data
    (correct/incorrect predictions on the same papers).

    Args:
        system1_correct: List of boolean values (correct predictions for system 1)
        system2_correct: List of boolean values (correct predictions for system 2)

    Returns:
        Dictionary with test statistic and p-value
    """
    if len(system1_correct) != len(system2_correct):
        raise ValueError("Both systems must have same number of predictions")

    # Create contingency table
    # Rows: System 1 (correct/incorrect)
    # Cols: System 2 (correct/incorrect)
    both_correct = sum([s1 and s2 for s1, s2 in zip(system1_correct, system2_correct)])
    both_incorrect = sum([not s1 and not s2 for s1, s2 in zip(system1_correct, system2_correct)])
    s1_only = sum([s1 and not s2 for s1, s2 in zip(system1_correct, system2_correct)])
    s2_only = sum([not s1 and s2 for s1, s2 in zip(system1_correct, system2_correct)])

    # McNemar's test uses discordant pairs (b and c)
    # b = s2_only (system2 correct, system1 incorrect)
    # c = s1_only (system1 correct, system2 incorrect)
    b = s2_only
    c = s1_only

    # Calculate McNemar's test statistic with continuity correction
    # χ² = (|b - c| - 1)² / (b + c)
    n = b + c
    if n == 0:
        # No discordant pairs - systems are identical
        statistic = 0.0
        p_value = 1.0
    else:
        statistic = (abs(b - c) - 1) ** 2 / n
        # P-value from chi-square distribution with 1 degree of freedom
        p_value = 1 - chi2.cdf(statistic, df=1)

    return {
        'statistic': statistic,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'both_correct': both_correct,
        'both_incorrect': both_incorrect,
        'system1_only': s1_only,
        'system2_only': s2_only,
    }


def statistical_significance_testing(
    per_paper_df: pd.DataFrame
) -> Dict[str, Dict]:
    """
    Perform statistical significance testing between systems.

    Args:
        per_paper_df: Per-paper metrics DataFrame

    Returns:
        Dictionary with test results for each comparison
    """
    logger.info("\nPerforming statistical significance testing...")

    # Define comparisons
    comparisons = [
        ('phase4_cleaned', 'v2', 'Phase 4 Cleaned vs V2'),
        ('phase4_cleaned', 'phase4_raw', 'Phase 4 Cleaned vs Raw'),
        ('phase4_raw', 'v2', 'Phase 4 Raw vs V2'),
    ]

    results = {}

    for system1, system2, name in comparisons:
        logger.info(f"\nComparing: {name}")

        # Determine "correct" predictions (F1 > threshold or TP > 0)
        # We'll use TP > 0 as "correct" for McNemar's test
        system1_correct = (per_paper_df[f'{system1}_tp'] > 0).tolist()
        system2_correct = (per_paper_df[f'{system2}_tp'] > 0).tolist()

        # McNemar's test
        mcnemar_result = mcnemar_test(system1_correct, system2_correct)

        logger.info(f"  McNemar's test:")
        logger.info(f"    Statistic: {mcnemar_result['statistic']:.4f}")
        logger.info(f"    P-value: {mcnemar_result['p_value']:.4f}")
        logger.info(f"    Significant: {mcnemar_result['significant']}")
        logger.info(f"    Both correct: {mcnemar_result['both_correct']}")
        logger.info(f"    Both incorrect: {mcnemar_result['both_incorrect']}")
        logger.info(f"    {system1} only: {mcnemar_result['system1_only']}")
        logger.info(f"    {system2} only: {mcnemar_result['system2_only']}")

        # Bootstrap CI for F1 difference
        f1_diff = (per_paper_df[f'{system1}_f1'] - per_paper_df[f'{system2}_f1']).tolist()
        ci_diff = bootstrap_confidence_interval(f1_diff, confidence=0.95, random_state=42)

        logger.info(f"  F1 difference (bootstrap 95% CI):")
        logger.info(f"    Mean: {ci_diff['mean']:.4f}")
        logger.info(f"    CI: [{ci_diff['lower']:.4f}, {ci_diff['upper']:.4f}]")

        results[name] = {
            'system1': system1,
            'system2': system2,
            'mcnemar': mcnemar_result,
            'f1_difference': ci_diff,
        }

    return results


def generate_detailed_examples(
    test_df: pd.DataFrame,
    per_paper_df: pd.DataFrame,
    n_examples: int = 10
) -> str:
    """
    Generate detailed examples showing predictions vs ground truth.

    Selects papers to show:
    - Top 3 papers where Phase 4 cleaned > V2
    - Top 3 papers where V2 > Phase 4 cleaned
    - 2 papers where Phase 4 cleaned = V2 (both good)
    - 2 papers where both failed

    Args:
        test_df: Test split DataFrame with entities
        per_paper_df: Per-paper metrics DataFrame
        n_examples: Number of examples to generate

    Returns:
        String containing detailed examples
    """
    logger.info(f"\nGenerating {n_examples} detailed examples...")

    # Merge to get both entities and metrics
    merged = pd.merge(
        test_df[['paper_id', 'title', 'abstract', 'true_com', 'true_ful',
                 'v2_com', 'v2_ful', 'p4_com_clean', 'p4_ful_clean']],
        per_paper_df[['paper_id', 'v2_f1', 'phase4_cleaned_f1']],
        on='paper_id'
    )

    # Calculate F1 difference
    merged['f1_diff'] = merged['phase4_cleaned_f1'] - merged['v2_f1']

    examples = []
    examples.append("=" * 100)
    examples.append("DETAILED EXAMPLES: V2 vs Phase 4 Cleaned Predictions")
    examples.append("=" * 100)
    examples.append("")

    # Category 1: Phase 4 wins (top 3)
    examples.append("\n" + "=" * 100)
    examples.append("CATEGORY 1: Phase 4 Cleaned Significantly Outperforms V2 (Top 3)")
    examples.append("=" * 100)
    phase4_wins = merged[merged['f1_diff'] > 0].nlargest(3, 'f1_diff')

    for idx, (_, row) in enumerate(phase4_wins.iterrows(), 1):
        examples.append(f"\n{'─' * 100}")
        examples.append(f"Example {idx}: Phase 4 F1={row['phase4_cleaned_f1']:.3f} vs V2 F1={row['v2_f1']:.3f} (Δ={row['f1_diff']:.3f})")
        examples.append(f"{'─' * 100}")
        examples.append(f"Paper ID: {row['paper_id']}")
        title = str(row['title']) if pd.notna(row['title']) else "N/A"
        examples.append(f"Title: {title[:100]}...")
        examples.append("")

        true_entities = list(set(row['true_com'] + row['true_ful']))
        v2_entities = list(set(row['v2_com'] + row['v2_ful']))
        p4_entities = list(set(row['p4_com_clean'] + row['p4_ful_clean']))

        examples.append(f"Ground Truth ({len(true_entities)} entities):")
        for ent in sorted(true_entities)[:10]:
            examples.append(f"  - {ent}")
        if len(true_entities) > 10:
            examples.append(f"  ... and {len(true_entities) - 10} more")
        examples.append("")

        examples.append(f"V2 Predictions ({len(v2_entities)} entities):")
        v2_match = match_entities(v2_entities, true_entities)
        for ent in sorted(v2_entities)[:10]:
            status = "✓" if any(ent in pair[:2] for pair in v2_match['matched_pairs']) else "✗"
            examples.append(f"  {status} {ent}")
        if len(v2_entities) > 10:
            examples.append(f"  ... and {len(v2_entities) - 10} more")
        examples.append("")

        examples.append(f"Phase 4 Cleaned Predictions ({len(p4_entities)} entities):")
        p4_match = match_entities(p4_entities, true_entities)
        for ent in sorted(p4_entities)[:10]:
            status = "✓" if any(ent in pair[:2] for pair in p4_match['matched_pairs']) else "✗"
            examples.append(f"  {status} {ent}")
        if len(p4_entities) > 10:
            examples.append(f"  ... and {len(p4_entities) - 10} more")
        examples.append("")

    # Category 2: V2 wins (top 3)
    examples.append("\n" + "=" * 100)
    examples.append("CATEGORY 2: V2 Significantly Outperforms Phase 4 Cleaned (Top 3)")
    examples.append("=" * 100)
    v2_wins = merged[merged['f1_diff'] < 0].nsmallest(3, 'f1_diff')

    for idx, (_, row) in enumerate(v2_wins.iterrows(), 1):
        examples.append(f"\n{'─' * 100}")
        examples.append(f"Example {idx}: V2 F1={row['v2_f1']:.3f} vs Phase 4 F1={row['phase4_cleaned_f1']:.3f} (Δ={-row['f1_diff']:.3f})")
        examples.append(f"{'─' * 100}")
        examples.append(f"Paper ID: {row['paper_id']}")
        title = str(row['title']) if pd.notna(row['title']) else "N/A"
        examples.append(f"Title: {title[:100]}...")
        examples.append("")

        true_entities = list(set(row['true_com'] + row['true_ful']))
        v2_entities = list(set(row['v2_com'] + row['v2_ful']))
        p4_entities = list(set(row['p4_com_clean'] + row['p4_ful_clean']))

        examples.append(f"Ground Truth ({len(true_entities)} entities):")
        for ent in sorted(true_entities)[:5]:
            examples.append(f"  - {ent}")
        if len(true_entities) > 5:
            examples.append(f"  ... and {len(true_entities) - 5} more")
        examples.append("")

        examples.append(f"V2 Predictions ({len(v2_entities)} entities) - Better:")
        for ent in sorted(v2_entities)[:5]:
            examples.append(f"  - {ent}")
        if len(v2_entities) > 5:
            examples.append(f"  ... and {len(v2_entities) - 5} more")
        examples.append("")

        examples.append(f"Phase 4 Cleaned Predictions ({len(p4_entities)} entities) - Worse:")
        for ent in sorted(p4_entities)[:5]:
            examples.append(f"  - {ent}")
        if len(p4_entities) > 5:
            examples.append(f"  ... and {len(p4_entities) - 5} more")
        examples.append("")

    # Category 3: Both succeed (2 examples)
    examples.append("\n" + "=" * 100)
    examples.append("CATEGORY 3: Both Systems Perform Well (2 Examples)")
    examples.append("=" * 100)
    both_good = merged[(merged['v2_f1'] >= 0.7) & (merged['phase4_cleaned_f1'] >= 0.7)].head(2)

    for idx, (_, row) in enumerate(both_good.iterrows(), 1):
        examples.append(f"\nExample {idx}: V2 F1={row['v2_f1']:.3f}, Phase 4 F1={row['phase4_cleaned_f1']:.3f}")
        examples.append(f"Paper ID: {row['paper_id']}")
        title = str(row['title']) if pd.notna(row['title']) else "N/A"
        examples.append(f"Title: {title[:80]}...")
        examples.append("")

    # Category 4: Both fail (2 examples)
    examples.append("\n" + "=" * 100)
    examples.append("CATEGORY 4: Both Systems Struggle (2 Examples)")
    examples.append("=" * 100)
    both_bad = merged[(merged['v2_f1'] < 0.3) & (merged['phase4_cleaned_f1'] < 0.3)].head(2)

    for idx, (_, row) in enumerate(both_bad.iterrows(), 1):
        examples.append(f"\nExample {idx}: V2 F1={row['v2_f1']:.3f}, Phase 4 F1={row['phase4_cleaned_f1']:.3f}")
        examples.append(f"Paper ID: {row['paper_id']}")
        title = str(row['title']) if pd.notna(row['title']) else "N/A"
        examples.append(f"Title: {title[:80]}...")
        examples.append("")

    return "\n".join(examples)


def generate_comparison_report(
    aggregate_results: Dict,
    significance_results: Dict,
    per_paper_df: pd.DataFrame
) -> str:
    """
    Generate markdown summary report comparing all systems.

    Args:
        aggregate_results: Aggregate metrics for each system
        significance_results: Statistical significance test results
        per_paper_df: Per-paper metrics DataFrame

    Returns:
        Markdown-formatted report string
    """
    report = []
    report.append("# Test Split Evaluation: V2 vs Phase 4 NER Systems")
    report.append("")
    report.append("## Overview")
    report.append("")
    report.append(f"- **Test Split Size**: {len(per_paper_df):,} papers with ground truth")
    report.append(f"- **Evaluation Date**: 2025-11-05")
    report.append(f"- **Matching Strategy**: Exact match (case-insensitive)")
    report.append("")

    report.append("## Aggregate Metrics")
    report.append("")
    report.append("### Micro-Averaged F1 Scores")
    report.append("")
    report.append("| System | Precision | Recall | F1 | TP | FP | FN |")
    report.append("|--------|-----------|--------|----|----|----|----|")

    for system in ['v2', 'phase4_raw', 'phase4_cleaned']:
        micro = aggregate_results[system]['micro']
        report.append(
            f"| {system.replace('_', ' ').title()} | "
            f"{micro['precision']:.4f} | "
            f"{micro['recall']:.4f} | "
            f"{micro['f1']:.4f} | "
            f"{micro['tp']} | "
            f"{micro['fp']} | "
            f"{micro['fn']} |"
        )
    report.append("")

    report.append("### Macro-Averaged F1 Scores (with 95% CI)")
    report.append("")
    report.append("| System | Mean F1 | Std Dev | 95% CI |")
    report.append("|--------|---------|---------|--------|")

    for system in ['v2', 'phase4_raw', 'phase4_cleaned']:
        macro = aggregate_results[system]['macro']
        ci = aggregate_results[system].get('ci', {})
        ci_str = f"[{ci.get('lower', 0):.4f}, {ci.get('upper', 0):.4f}]" if ci else "N/A"
        report.append(
            f"| {system.replace('_', ' ').title()} | "
            f"{macro['f1']:.4f} | "
            f"{macro['f1_std']:.4f} | "
            f"{ci_str} |"
        )
    report.append("")

    report.append("## Statistical Significance")
    report.append("")

    for name, result in significance_results.items():
        report.append(f"### {name}")
        report.append("")

        mcnemar = result['mcnemar']
        f1_diff = result['f1_difference']

        report.append(f"**McNemar's Test:**")
        report.append(f"- Statistic: {mcnemar['statistic']:.4f}")
        report.append(f"- P-value: {mcnemar['p_value']:.4f}")
        report.append(f"- Significant: {'Yes' if mcnemar['significant'] else 'No'} (α=0.05)")
        report.append(f"- Both correct: {mcnemar['both_correct']}")
        report.append(f"- Both incorrect: {mcnemar['both_incorrect']}")
        report.append(f"- {result['system1']} only: {mcnemar['system1_only']}")
        report.append(f"- {result['system2']} only: {mcnemar['system2_only']}")
        report.append("")

        report.append(f"**F1 Difference (Bootstrap 95% CI):**")
        report.append(f"- Mean: {f1_diff['mean']:.4f}")
        report.append(f"- CI: [{f1_diff['lower']:.4f}, {f1_diff['upper']:.4f}]")
        report.append("")

    report.append("## Per-Paper Performance Distribution")
    report.append("")

    for system in ['v2', 'phase4_raw', 'phase4_cleaned']:
        f1_scores = per_paper_df[f'{system}_f1']
        report.append(f"### {system.replace('_', ' ').title()}")
        report.append(f"- Mean F1: {f1_scores.mean():.4f}")
        report.append(f"- Median F1: {f1_scores.median():.4f}")
        report.append(f"- Min F1: {f1_scores.min():.4f}")
        report.append(f"- Max F1: {f1_scores.max():.4f}")
        report.append(f"- Papers with F1 > 0.8: {(f1_scores > 0.8).sum()} ({(f1_scores > 0.8).mean():.1%})")
        report.append(f"- Papers with F1 > 0.5: {(f1_scores > 0.5).sum()} ({(f1_scores > 0.5).mean():.1%})")
        report.append("")

    return "\n".join(report)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Evaluate V2 and Phase 4 NER systems on test split",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate with exact matching
  python 02_evaluate_on_test_split.py

  # Evaluate with fuzzy matching
  python 02_evaluate_on_test_split.py --match-strategy fuzzy

  # Custom input/output paths
  python 02_evaluate_on_test_split.py --input custom_aligned.csv --output custom_results/

  # Generate more examples
  python 02_evaluate_on_test_split.py --n-examples 20
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
        '--match-strategy',
        choices=['exact', 'fuzzy', 'partial', 'token_overlap'],
        default='exact',
        help='Entity matching strategy (default: exact)'
    )

    parser.add_argument(
        '--n-examples',
        type=int,
        default=10,
        help='Number of detailed examples to generate (default: 10)'
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
    logger.info("SCRIPT 02: Evaluate on Test Split")
    logger.info("=" * 100)
    logger.info(f"Match strategy: {args.match_strategy}")
    logger.info(f"Output directory: {args.output}")
    logger.info("")

    try:
        # Create output directory
        args.output.mkdir(parents=True, exist_ok=True)

        # Step 1: Load aligned papers
        logger.info("STEP 1: Loading aligned papers...")
        input_file = args.input if args.input is not None else DATA_DIR / "aligned_papers.csv"
        aligned_df = load_aligned_papers(input_file)

        # Step 2: Filter to test split
        logger.info("\nSTEP 2: Filtering to test split...")
        test_df = filter_test_split(aligned_df)

        # Step 3: Evaluate all systems
        logger.info("\nSTEP 3: Evaluating all systems...")
        per_paper_df, aggregate_results = evaluate_test_split(
            test_df,
            match_strategy=args.match_strategy
        )

        # Step 4: Statistical significance testing
        logger.info("\nSTEP 4: Statistical significance testing...")
        significance_results = statistical_significance_testing(per_paper_df)

        # Step 5: Generate detailed examples
        logger.info("\nSTEP 5: Generating detailed examples...")
        examples_text = generate_detailed_examples(
            test_df,
            per_paper_df,
            n_examples=args.n_examples
        )

        # Step 6: Generate comparison report
        logger.info("\nSTEP 6: Generating comparison report...")
        report_text = generate_comparison_report(
            aggregate_results,
            significance_results,
            per_paper_df
        )

        # Step 7: Save outputs
        logger.info("\nSTEP 7: Saving outputs...")

        # Per-paper metrics CSV
        metrics_path = args.output / "test_split_metrics.csv"
        per_paper_df.to_csv(metrics_path, index=False)
        logger.info(f"✓ Saved per-paper metrics: {metrics_path}")

        # Aggregate metrics JSON
        aggregate_path = args.output / "test_split_aggregate.json"
        with open(aggregate_path, 'w') as f:
            json.dump(aggregate_results, f, indent=2, default=str)
        logger.info(f"✓ Saved aggregate metrics: {aggregate_path}")

        # Detailed examples TXT
        examples_path = args.output / "test_split_examples.txt"
        with open(examples_path, 'w') as f:
            f.write(examples_text)
        logger.info(f"✓ Saved detailed examples: {examples_path}")

        # Comparison report MD
        report_path = args.output / "test_split_comparison.md"
        with open(report_path, 'w') as f:
            f.write(report_text)
        logger.info(f"✓ Saved comparison report: {report_path}")

        # Significance results JSON
        significance_path = args.output / "test_split_significance.json"
        with open(significance_path, 'w') as f:
            json.dump(significance_results, f, indent=2, default=str)
        logger.info(f"✓ Saved significance results: {significance_path}")

        logger.info("\n" + "=" * 100)
        logger.info("EVALUATION COMPLETE!")
        logger.info("=" * 100)
        logger.info(f"Total papers evaluated: {len(per_paper_df):,}")
        logger.info(f"\nKey findings:")
        logger.info(f"  V2 F1:              {aggregate_results['v2']['micro']['f1']:.4f}")
        logger.info(f"  Phase 4 Raw F1:     {aggregate_results['phase4_raw']['micro']['f1']:.4f}")
        logger.info(f"  Phase 4 Cleaned F1: {aggregate_results['phase4_cleaned']['micro']['f1']:.4f}")
        logger.info("")
        logger.info(f"All outputs saved to: {args.output}")

        return 0

    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
