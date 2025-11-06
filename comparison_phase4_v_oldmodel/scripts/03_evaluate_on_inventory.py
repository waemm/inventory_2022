#!/usr/bin/env python3
"""
Script 03: Evaluate V2 and Phase 4 NER systems on validated bio-resources from inventory.

This script evaluates both NER systems on 3,113 validated bio-resources from the
final inventory. This represents a different type of evaluation:
- Test split (Script 02): Measures overall NER performance against ground truth
- Inventory (Script 03): Measures detection of known validated resources

Key evaluation questions:
1. What % of validated resources does each system detect?
2. How many false positives (entities not in inventory)?
3. What novel entities do systems discover (not in inventory)?
4. How do results vary by resource characteristics (length, type, year)?

Scoring criteria:
- Correct: Exact or fuzzy match to best_name, best_common, or best_full
- Partial: Substring match or significant token overlap
- Miss: Resource not found by system
- False Positive: Entity predicted but not in inventory

Outputs:
- results/inventory_evaluation.csv: Per-resource results for each system
- results/inventory_metrics.json: Detection rates, precision on known resources
- results/missed_resources.csv: Resources neither system found
- results/novel_discoveries.csv: New entities not in inventory
- results/inventory_comparison.md: Summary report

Author: Generated for Phase 4 vs V2 NER comparison
Date: 2025-11-05
"""

import argparse
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.data_loading import parse_entity_list
from utils.entity_matching import exact_match, fuzzy_match, partial_match, token_overlap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('03_evaluate_on_inventory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths (relative to script location)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RESULTS_DIR = PROJECT_ROOT / "comparison_phase4_v_oldmodel" / "results"
DATA_DIR = PROJECT_ROOT / "data"


def load_aligned_papers(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load aligned papers from Script 01 output.

    Args:
        file_path: Optional custom path. If None, uses default location.

    Returns:
        DataFrame with aligned V2, Phase 4, and ground truth data
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
        'v2_com', 'v2_ful',
        'p4_com_raw', 'p4_com_clean',
        'p4_ful_raw', 'p4_ful_clean'
    ]

    for col in entity_columns:
        if col in df.columns:
            df[col] = df[col].apply(parse_entity_list)

    logger.info(f"Loaded {len(df):,} aligned papers")
    return df


def load_inventory(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load final inventory with validated bio-resources.

    Args:
        file_path: Optional custom path. If None, uses default location.

    Returns:
        DataFrame with inventory data including best_name, best_common, best_full
    """
    if file_path is None:
        # Try multiple possible locations
        possible_paths = [
            DATA_DIR / "final_inventory_2022.csv",
            PROJECT_ROOT / "collab_results" / "2025-10-28-gl3fd6_2022_rerun" / "final_inventory.csv",
            PROJECT_ROOT / "data" / "inventory_2022.csv"
        ]

        for path in possible_paths:
            if path.exists():
                file_path = path
                break

        if file_path is None:
            raise FileNotFoundError(
                f"Inventory file not found. Tried locations:\n" +
                "\n".join(f"  - {p}" for p in possible_paths)
            )

    logger.info(f"Loading inventory from: {file_path}")
    df = pd.read_csv(file_path)

    # Ensure required columns exist
    required_cols = ['pmid', 'best_name', 'best_common', 'best_full']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in inventory: {missing_cols}")

    logger.info(f"Loaded {len(df):,} inventory entries")
    return df


def match_entity_to_resource(
    entity: str,
    resource_names: List[str],
    strategies: List[str] = ['exact', 'fuzzy', 'partial', 'token_overlap']
) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to match an entity to a resource using multiple strategies.

    Args:
        entity: Entity string to match
        resource_names: List of resource name variants (best_name, best_common, best_full)
        strategies: List of matching strategies to try (in order)

    Returns:
        Tuple of (matched_resource, strategy_used) or (None, None) if no match
    """
    # Filter out None/empty resource names
    resource_names = [r for r in resource_names if r and str(r).strip()]

    if not entity or not resource_names:
        return None, None

    # Try each strategy in order
    for strategy in strategies:
        if strategy == 'exact':
            for resource in resource_names:
                if exact_match(entity, resource):
                    return resource, 'exact'

        elif strategy == 'fuzzy':
            for resource in resource_names:
                if fuzzy_match(entity, resource, max_distance=2):
                    return resource, 'fuzzy'

        elif strategy == 'partial':
            for resource in resource_names:
                if partial_match(entity, resource, min_length=4):
                    return resource, 'partial'

        elif strategy == 'token_overlap':
            for resource in resource_names:
                if token_overlap(entity, resource, threshold=0.6):
                    return resource, 'token_overlap'

    return None, None


def evaluate_system_on_inventory(
    system_name: str,
    aligned_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    entity_columns: List[str]
) -> Tuple[pd.DataFrame, Dict]:
    """
    Evaluate a single system (V2 or Phase 4) on inventory resources.

    Args:
        system_name: Name of the system (for logging)
        aligned_df: Aligned papers DataFrame with predictions
        inventory_df: Inventory DataFrame with resources
        entity_columns: List of entity column names for this system

    Returns:
        Tuple of (per_resource_results_df, summary_metrics_dict)
    """
    logger.info(f"\nEvaluating {system_name} on inventory...")

    # Create paper_id to entities mapping
    paper_entities = {}
    for _, row in aligned_df.iterrows():
        paper_id = row['paper_id']
        entities = []
        for col in entity_columns:
            if col in row and isinstance(row[col], list):
                entities.extend(row[col])
        paper_entities[paper_id] = list(set(entities))  # Deduplicate

    logger.info(f"  Loaded predictions from {len(paper_entities):,} papers")

    # Evaluate each inventory resource
    results = []
    matched_count = 0
    partial_count = 0
    missed_count = 0

    for idx, inv_row in tqdm(inventory_df.iterrows(), total=len(inventory_df), desc=f"Evaluating {system_name}"):
        pmid = inv_row.get('pmid')
        best_name = inv_row.get('best_name', '')
        best_common = inv_row.get('best_common', '')
        best_full = inv_row.get('best_full', '')

        # Get predicted entities for this paper
        predicted_entities = paper_entities.get(pmid, [])

        # Try to match resource
        resource_variants = [best_name, best_common, best_full]
        matched_entity, match_strategy = match_entity_to_resource(
            best_name,  # Primary: try to match best_name
            predicted_entities
        )

        # If no match with best_name, try other variants
        if not matched_entity:
            for variant in [best_common, best_full]:
                matched_entity, match_strategy = match_entity_to_resource(
                    variant,
                    predicted_entities
                )
                if matched_entity:
                    break

        # Determine result category
        if match_strategy in ['exact', 'fuzzy']:
            result_category = 'correct'
            matched_count += 1
        elif match_strategy in ['partial', 'token_overlap']:
            result_category = 'partial'
            partial_count += 1
        else:
            result_category = 'miss'
            missed_count += 1

        # Store result
        results.append({
            'pmid': pmid,
            'best_name': best_name,
            'best_common': best_common,
            'best_full': best_full,
            'system': system_name,
            'result': result_category,
            'matched_entity': matched_entity if matched_entity else '',
            'match_strategy': match_strategy if match_strategy else '',
            'num_predicted_entities': len(predicted_entities),
        })

    # Create DataFrame
    results_df = pd.DataFrame(results)

    # Calculate metrics
    total = len(results_df)
    detection_rate = (matched_count + partial_count) / total if total > 0 else 0.0
    precision = matched_count / (matched_count + partial_count) if (matched_count + partial_count) > 0 else 0.0

    metrics = {
        'system': system_name,
        'total_resources': total,
        'correct_matches': matched_count,
        'partial_matches': partial_count,
        'misses': missed_count,
        'detection_rate': detection_rate,
        'correct_detection_rate': matched_count / total if total > 0 else 0.0,
        'precision_on_detections': precision,
    }

    logger.info(f"\n{system_name} Results:")
    logger.info(f"  Total resources: {total:,}")
    logger.info(f"  Correct matches: {matched_count:,} ({matched_count/total:.1%})")
    logger.info(f"  Partial matches: {partial_count:,} ({partial_count/total:.1%})")
    logger.info(f"  Misses: {missed_count:,} ({missed_count/total:.1%})")
    logger.info(f"  Overall detection rate: {detection_rate:.1%}")

    return results_df, metrics


def find_missed_resources(
    v2_results: pd.DataFrame,
    phase4_results: pd.DataFrame
) -> pd.DataFrame:
    """
    Identify resources that neither system detected.

    Args:
        v2_results: V2 evaluation results
        phase4_results: Phase 4 evaluation results

    Returns:
        DataFrame with resources missed by both systems
    """
    logger.info("\nIdentifying resources missed by both systems...")

    # Find resources missed by both
    v2_misses = set(v2_results[v2_results['result'] == 'miss']['pmid'])
    phase4_misses = set(phase4_results[phase4_results['result'] == 'miss']['pmid'])

    both_missed = v2_misses & phase4_misses

    # Get details for missed resources
    missed_df = v2_results[v2_results['pmid'].isin(both_missed)][
        ['pmid', 'best_name', 'best_common', 'best_full']
    ].copy()

    logger.info(f"  Resources missed by both: {len(missed_df):,}")
    logger.info(f"  V2 only misses: {len(v2_misses - both_missed):,}")
    logger.info(f"  Phase 4 only misses: {len(phase4_misses - both_missed):,}")

    return missed_df


def find_novel_discoveries(
    aligned_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    entity_columns: List[str],
    system_name: str
) -> pd.DataFrame:
    """
    Identify entities predicted by system but not in inventory (potential novel discoveries).

    Args:
        aligned_df: Aligned papers DataFrame
        inventory_df: Inventory DataFrame
        entity_columns: Entity columns for this system
        system_name: Name of system (for logging)

    Returns:
        DataFrame with novel entities
    """
    logger.info(f"\nIdentifying novel discoveries for {system_name}...")

    # Get all inventory entities
    inventory_entities = set()
    for col in ['best_name', 'best_common', 'best_full']:
        if col in inventory_df.columns:
            entities = inventory_df[col].dropna().unique()
            inventory_entities.update([str(e).lower().strip() for e in entities if e])

    logger.info(f"  Total unique inventory entities: {len(inventory_entities):,}")

    # Get all predicted entities
    predicted_entities = []
    for _, row in aligned_df.iterrows():
        paper_id = row['paper_id']
        for col in entity_columns:
            if col in row and isinstance(row[col], list):
                for entity in row[col]:
                    if entity and str(entity).strip():
                        predicted_entities.append({
                            'paper_id': paper_id,
                            'entity': entity,
                            'entity_normalized': str(entity).lower().strip()
                        })

    predicted_df = pd.DataFrame(predicted_entities)
    logger.info(f"  Total predicted entities: {len(predicted_df):,}")

    # Find novel entities (not in inventory)
    if len(predicted_df) > 0:
        predicted_df['in_inventory'] = predicted_df['entity_normalized'].isin(inventory_entities)
        novel_df = predicted_df[~predicted_df['in_inventory']].copy()

        # Count occurrences
        entity_counts = novel_df['entity'].value_counts()
        novel_summary = pd.DataFrame({
            'entity': entity_counts.index,
            'occurrences': entity_counts.values,
            'system': system_name
        })

        logger.info(f"  Novel entities: {len(novel_summary):,}")
        logger.info(f"  Novel entity occurrences: {novel_df.shape[0]:,}")
    else:
        novel_summary = pd.DataFrame(columns=['entity', 'occurrences', 'system'])

    return novel_summary


def analyze_by_characteristics(
    results_df: pd.DataFrame,
    inventory_df: pd.DataFrame
) -> Dict:
    """
    Analyze results by resource characteristics (length, year, etc.).

    Args:
        results_df: Combined results for all systems
        inventory_df: Inventory DataFrame with metadata

    Returns:
        Dictionary with breakdown by characteristics
    """
    logger.info("\nAnalyzing results by resource characteristics...")

    analysis = {}

    # Merge with inventory to get metadata
    if 'year' in inventory_df.columns:
        merged = pd.merge(
            results_df,
            inventory_df[['pmid', 'year']],
            on='pmid',
            how='left'
        )

        # By year bins
        if 'year' in merged.columns:
            merged['year_bin'] = pd.cut(
                merged['year'],
                bins=[0, 2010, 2015, 2020, 2025],
                labels=['Before 2010', '2010-2014', '2015-2019', '2020+']
            )

            year_analysis = []
            for system in merged['system'].unique():
                system_data = merged[merged['system'] == system]
                for year_bin in system_data['year_bin'].dropna().unique():
                    bin_data = system_data[system_data['year_bin'] == year_bin]
                    year_analysis.append({
                        'system': system,
                        'year_bin': year_bin,
                        'total': len(bin_data),
                        'correct': (bin_data['result'] == 'correct').sum(),
                        'detection_rate': (bin_data['result'] != 'miss').mean()
                    })

            analysis['by_year'] = pd.DataFrame(year_analysis)

    # By entity length
    results_df['entity_length'] = results_df['best_name'].str.len()
    results_df['length_bin'] = pd.cut(
        results_df['entity_length'],
        bins=[0, 10, 20, 50, 1000],
        labels=['Short (1-10)', 'Medium (11-20)', 'Long (21-50)', 'Very Long (50+)']
    )

    length_analysis = []
    for system in results_df['system'].unique():
        system_data = results_df[results_df['system'] == system]
        for length_bin in system_data['length_bin'].dropna().unique():
            bin_data = system_data[system_data['length_bin'] == length_bin]
            length_analysis.append({
                'system': system,
                'length_bin': length_bin,
                'total': len(bin_data),
                'correct': (bin_data['result'] == 'correct').sum(),
                'detection_rate': (bin_data['result'] != 'miss').mean()
            })

    analysis['by_length'] = pd.DataFrame(length_analysis)

    return analysis


def generate_comparison_report(
    metrics: Dict[str, Dict],
    missed_df: pd.DataFrame,
    novel_v2: pd.DataFrame,
    novel_phase4: pd.DataFrame,
    analysis: Dict
) -> str:
    """
    Generate markdown summary report.

    Args:
        metrics: Metrics for each system
        missed_df: Resources missed by both systems
        novel_v2: Novel entities from V2
        novel_phase4: Novel entities from Phase 4
        analysis: Analysis by characteristics

    Returns:
        Markdown-formatted report
    """
    report = []
    report.append("# Inventory Evaluation: V2 vs Phase 4 NER Systems")
    report.append("")
    report.append("## Overview")
    report.append("")
    report.append("This evaluation measures how well each NER system detects validated bio-resources")
    report.append("from the final inventory. Unlike test split evaluation (ground truth), this measures")
    report.append("detection of known resources in real-world papers.")
    report.append("")

    report.append("## Detection Metrics")
    report.append("")
    report.append("| System | Total Resources | Correct | Partial | Misses | Detection Rate | Correct Rate |")
    report.append("|--------|----------------|---------|---------|--------|----------------|--------------|")

    for system_name, m in metrics.items():
        report.append(
            f"| {system_name} | "
            f"{m['total_resources']:,} | "
            f"{m['correct_matches']:,} | "
            f"{m['partial_matches']:,} | "
            f"{m['misses']:,} | "
            f"{m['detection_rate']:.1%} | "
            f"{m['correct_detection_rate']:.1%} |"
        )
    report.append("")

    report.append("### Match Quality")
    report.append("")
    report.append("- **Correct**: Exact or fuzzy match to best_name/best_common/best_full")
    report.append("- **Partial**: Substring match or significant token overlap")
    report.append("- **Miss**: Resource not detected by system")
    report.append("")

    report.append("## Missed Resources")
    report.append("")
    report.append(f"- Resources missed by both systems: **{len(missed_df):,}**")
    report.append(f"- These represent challenging entities that neither system can detect")
    report.append("")

    if len(missed_df) > 0:
        report.append("### Examples of Missed Resources")
        report.append("")
        for _, row in missed_df.head(10).iterrows():
            report.append(f"- {row['best_name']} (PMID: {row['pmid']})")
        if len(missed_df) > 10:
            report.append(f"- ... and {len(missed_df) - 10:,} more")
        report.append("")

    report.append("## Novel Discoveries")
    report.append("")
    report.append("Entities predicted by systems but not in inventory (potential new discoveries):")
    report.append("")
    report.append(f"- **V2**: {len(novel_v2):,} unique novel entities")
    report.append(f"- **Phase 4**: {len(novel_phase4):,} unique novel entities")
    report.append("")

    if len(novel_v2) > 0:
        report.append("### Top Novel Entities - V2")
        report.append("")
        for _, row in novel_v2.head(10).iterrows():
            report.append(f"- {row['entity']} (found {row['occurrences']} times)")
        report.append("")

    if len(novel_phase4) > 0:
        report.append("### Top Novel Entities - Phase 4")
        report.append("")
        for _, row in novel_phase4.head(10).iterrows():
            report.append(f"- {row['entity']} (found {row['occurrences']} times)")
        report.append("")

    report.append("## Analysis by Characteristics")
    report.append("")

    if 'by_length' in analysis and len(analysis['by_length']) > 0:
        report.append("### By Entity Length")
        report.append("")
        report.append("| System | Length | Total | Correct | Detection Rate |")
        report.append("|--------|--------|-------|---------|----------------|")
        for _, row in analysis['by_length'].iterrows():
            report.append(
                f"| {row['system']} | "
                f"{row['length_bin']} | "
                f"{row['total']:,} | "
                f"{row['correct']:,} | "
                f"{row['detection_rate']:.1%} |"
            )
        report.append("")

    if 'by_year' in analysis and len(analysis['by_year']) > 0:
        report.append("### By Publication Year")
        report.append("")
        report.append("| System | Year Range | Total | Correct | Detection Rate |")
        report.append("|--------|------------|-------|---------|----------------|")
        for _, row in analysis['by_year'].iterrows():
            report.append(
                f"| {row['system']} | "
                f"{row['year_bin']} | "
                f"{row['total']:,} | "
                f"{row['correct']:,} | "
                f"{row['detection_rate']:.1%} |"
            )
        report.append("")

    return "\n".join(report)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Evaluate V2 and Phase 4 NER systems on validated inventory resources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard evaluation
  python 03_evaluate_on_inventory.py

  # Custom paths
  python 03_evaluate_on_inventory.py --input custom_aligned.csv --inventory custom_inventory.csv

  # Custom output directory
  python 03_evaluate_on_inventory.py --output custom_results/
        """
    )

    parser.add_argument(
        '--input',
        type=Path,
        default=None,
        help='Path to aligned papers CSV (default: results/aligned_papers.csv)'
    )

    parser.add_argument(
        '--inventory',
        type=Path,
        default=None,
        help='Path to inventory CSV (default: auto-detect)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=RESULTS_DIR,
        help='Output directory (default: results/)'
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
    logger.info("SCRIPT 03: Evaluate on Inventory")
    logger.info("=" * 100)
    logger.info(f"Output directory: {args.output}")
    logger.info("")

    try:
        # Create output directory
        args.output.mkdir(parents=True, exist_ok=True)

        # Step 1: Load data
        logger.info("STEP 1: Loading data...")
        aligned_df = load_aligned_papers(args.input)
        inventory_df = load_inventory(args.inventory)

        # Step 2: Evaluate V2
        logger.info("\nSTEP 2: Evaluating V2...")
        v2_results, v2_metrics = evaluate_system_on_inventory(
            system_name='V2',
            aligned_df=aligned_df,
            inventory_df=inventory_df,
            entity_columns=['v2_com', 'v2_ful']
        )

        # Step 3: Evaluate Phase 4 cleaned
        logger.info("\nSTEP 3: Evaluating Phase 4 (cleaned)...")
        phase4_results, phase4_metrics = evaluate_system_on_inventory(
            system_name='Phase4_Cleaned',
            aligned_df=aligned_df,
            inventory_df=inventory_df,
            entity_columns=['p4_com_clean', 'p4_ful_clean']
        )

        # Step 4: Find missed resources
        logger.info("\nSTEP 4: Finding missed resources...")
        missed_df = find_missed_resources(v2_results, phase4_results)

        # Step 5: Find novel discoveries
        logger.info("\nSTEP 5: Finding novel discoveries...")
        novel_v2 = find_novel_discoveries(
            aligned_df, inventory_df, ['v2_com', 'v2_ful'], 'V2'
        )
        novel_phase4 = find_novel_discoveries(
            aligned_df, inventory_df, ['p4_com_clean', 'p4_ful_clean'], 'Phase4_Cleaned'
        )

        # Step 6: Analyze by characteristics
        logger.info("\nSTEP 6: Analyzing by characteristics...")
        combined_results = pd.concat([v2_results, phase4_results], ignore_index=True)
        analysis = analyze_by_characteristics(combined_results, inventory_df)

        # Step 7: Generate report
        logger.info("\nSTEP 7: Generating report...")
        report = generate_comparison_report(
            metrics={'V2': v2_metrics, 'Phase4_Cleaned': phase4_metrics},
            missed_df=missed_df,
            novel_v2=novel_v2,
            novel_phase4=novel_phase4,
            analysis=analysis
        )

        # Step 8: Save outputs
        logger.info("\nSTEP 8: Saving outputs...")

        # Combined per-resource results
        eval_path = args.output / "inventory_evaluation.csv"
        combined_results.to_csv(eval_path, index=False)
        logger.info(f"✓ Saved evaluation results: {eval_path}")

        # Metrics JSON
        metrics_path = args.output / "inventory_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump({'V2': v2_metrics, 'Phase4_Cleaned': phase4_metrics}, f, indent=2)
        logger.info(f"✓ Saved metrics: {metrics_path}")

        # Missed resources
        missed_path = args.output / "missed_resources.csv"
        missed_df.to_csv(missed_path, index=False)
        logger.info(f"✓ Saved missed resources: {missed_path}")

        # Novel discoveries
        novel_path = args.output / "novel_discoveries.csv"
        novel_combined = pd.concat([novel_v2, novel_phase4], ignore_index=True)
        novel_combined.to_csv(novel_path, index=False)
        logger.info(f"✓ Saved novel discoveries: {novel_path}")

        # Report
        report_path = args.output / "inventory_comparison.md"
        with open(report_path, 'w') as f:
            f.write(report)
        logger.info(f"✓ Saved comparison report: {report_path}")

        # Analysis breakdown
        if 'by_length' in analysis:
            length_path = args.output / "inventory_by_length.csv"
            analysis['by_length'].to_csv(length_path, index=False)
            logger.info(f"✓ Saved length analysis: {length_path}")

        if 'by_year' in analysis:
            year_path = args.output / "inventory_by_year.csv"
            analysis['by_year'].to_csv(year_path, index=False)
            logger.info(f"✓ Saved year analysis: {year_path}")

        logger.info("\n" + "=" * 100)
        logger.info("EVALUATION COMPLETE!")
        logger.info("=" * 100)
        logger.info(f"\nV2 Detection Rate: {v2_metrics['detection_rate']:.1%}")
        logger.info(f"Phase 4 Detection Rate: {phase4_metrics['detection_rate']:.1%}")
        logger.info(f"\nMissed by both: {len(missed_df):,}")
        logger.info(f"Novel entities (V2): {len(novel_v2):,}")
        logger.info(f"Novel entities (Phase 4): {len(novel_phase4):,}")
        logger.info(f"\nAll outputs saved to: {args.output}")

        return 0

    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
