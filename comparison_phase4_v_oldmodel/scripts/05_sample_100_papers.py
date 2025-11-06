#!/usr/bin/env python3
"""
Script 05: Sample 100 Papers for Qualitative Analysis

Purpose: Select 100 interesting papers for manual inspection using stratified sampling.

Sampling Strategy (25 papers each):
- Agreement: Both V2 and Phase 4 predict same entities
- Phase 4 Better: Phase 4 finds entities V2 missed
- V2 Better: V2 finds entities Phase 4 missed
- Disagreement: Both predict different entities

Author: Analysis Pipeline
Date: 2025-11-05
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

import pandas as pd
import numpy as np
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.comparison_utils import (
    load_comparison_results,
    load_ground_truth,
    calculate_entity_similarity,
)


def setup_logging(output_dir: Path) -> logging.Logger:
    """Setup logging configuration."""
    log_file = output_dir / "05_sampling.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


def categorize_paper(
    pmid: str,
    v2_entities: List[str],
    phase4_entities: List[str],
    ground_truth: Dict[str, List[str]],
) -> Tuple[str, Dict[str, Any]]:
    """
    Categorize a paper based on prediction patterns.

    Returns:
        Tuple of (category, metadata)
    """
    # Clean and normalize entities
    v2_clean = set(e.strip() for e in v2_entities if e.strip())
    phase4_clean = set(e.strip() for e in phase4_entities if e.strip())
    gt = set(ground_truth.get(pmid, []))

    has_ground_truth = len(gt) > 0

    # Calculate overlaps
    both_predicted = v2_clean & phase4_clean
    v2_only = v2_clean - phase4_clean
    phase4_only = phase4_clean - v2_clean

    # Determine category
    if v2_clean == phase4_clean and len(v2_clean) > 0:
        category = "AGREEMENT"
    elif len(phase4_only) > 0 and len(v2_only) == 0:
        category = "PHASE4_BETTER"
    elif len(v2_only) > 0 and len(phase4_only) == 0:
        category = "V2_BETTER"
    elif len(v2_only) > 0 and len(phase4_only) > 0:
        category = "DISAGREEMENT"
    elif len(v2_clean) == 0 and len(phase4_clean) == 0:
        category = "BOTH_EMPTY"
    else:
        category = "OTHER"

    # Calculate interest score (for prioritization)
    interest_score = 0.0

    # Higher score for papers with ground truth
    if has_ground_truth:
        interest_score += 10.0

    # Higher score for papers with multiple entities
    total_entities = len(v2_clean | phase4_clean)
    interest_score += min(total_entities * 2, 10.0)

    # Higher score for disagreements
    if category == "DISAGREEMENT":
        interest_score += 5.0

    # Higher score for unique findings
    interest_score += len(v2_only) + len(phase4_only)

    metadata = {
        "category": category,
        "interest_score": interest_score,
        "has_ground_truth": has_ground_truth,
        "total_entities": total_entities,
        "v2_count": len(v2_clean),
        "phase4_count": len(phase4_clean),
        "both_count": len(both_predicted),
        "v2_only_count": len(v2_only),
        "phase4_only_count": len(phase4_only),
        "ground_truth_count": len(gt),
    }

    return category, metadata


def detect_bpe_artifacts(entities: List[str]) -> int:
    """Count entities with BPE artifacts (Ġ prefix)."""
    return sum(1 for e in entities if "Ġ" in e)


def extract_publication_year(paper_data: Dict[str, Any]) -> int:
    """Extract publication year from paper metadata."""
    # Try various fields
    year = paper_data.get("year")
    if year:
        return int(year)

    # Try parsing from date fields
    for field in ["publication_date", "pub_date", "date"]:
        date_str = paper_data.get(field)
        if date_str:
            try:
                if isinstance(date_str, str):
                    # Try parsing YYYY-MM-DD or YYYY
                    if "-" in date_str:
                        return int(date_str.split("-")[0])
                    elif len(date_str) == 4:
                        return int(date_str)
            except (ValueError, AttributeError):
                continue

    return 0  # Unknown


def stratified_sample(
    df: pd.DataFrame,
    category_col: str,
    n_per_category: int,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Perform stratified sampling, prioritizing by interest_score.

    Args:
        df: DataFrame with papers
        category_col: Column name for categories
        n_per_category: Number of samples per category
        random_state: Random seed

    Returns:
        Sampled DataFrame
    """
    np.random.seed(random_state)
    sampled = []

    for category in df[category_col].unique():
        category_df = df[df[category_col] == category].copy()

        # Sort by interest score (descending)
        category_df = category_df.sort_values("interest_score", ascending=False)

        # Sample with preference for high-interest papers
        n_available = len(category_df)
        n_sample = min(n_per_category, n_available)

        if n_sample > 0:
            # Take top samples by interest score
            sampled.append(category_df.head(n_sample))

    return pd.concat(sampled, ignore_index=True)


def create_sample_100_papers(
    comparison_file: Path,
    ground_truth_file: Path,
    output_dir: Path,
    n_per_category: int = 25,
    logger: logging.Logger = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create stratified sample of 100 papers for qualitative analysis.

    Args:
        comparison_file: Path to merged comparison results
        ground_truth_file: Path to ground truth data
        output_dir: Output directory for results
        n_per_category: Number of papers per category (default: 25)
        logger: Logger instance

    Returns:
        Tuple of (sampled DataFrame, stratification metadata)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("SCRIPT 05: SAMPLE 100 PAPERS FOR QUALITATIVE ANALYSIS")
    logger.info("=" * 80)

    # Load data
    logger.info(f"Loading comparison results from {comparison_file}")
    comparison_df = load_comparison_results(comparison_file)

    logger.info(f"Loading ground truth from {ground_truth_file}")
    ground_truth = load_ground_truth(ground_truth_file)

    logger.info(f"Total papers in comparison: {len(comparison_df)}")
    logger.info(f"Papers with ground truth: {len(ground_truth)}")

    # Categorize all papers
    logger.info("\nCategorizing papers...")
    categories = []
    metadata_list = []

    for _, row in tqdm(comparison_df.iterrows(), total=len(comparison_df), desc="Categorizing"):
        pmid = str(row["pmid"])
        v2_entities = eval(row["v2_entities"]) if isinstance(row["v2_entities"], str) else row["v2_entities"]
        phase4_entities = eval(row["phase4_entities"]) if isinstance(row["phase4_entities"], str) else row["phase4_entities"]

        category, meta = categorize_paper(pmid, v2_entities, phase4_entities, ground_truth)
        categories.append(category)
        metadata_list.append(meta)

    # Add categorization to DataFrame
    comparison_df["category"] = categories
    for key in metadata_list[0].keys():
        comparison_df[key] = [m[key] for m in metadata_list]

    # Add additional features for prioritization
    logger.info("\nExtracting additional features...")

    # BPE artifacts
    comparison_df["v2_bpe_artifacts"] = comparison_df["v2_entities"].apply(
        lambda x: detect_bpe_artifacts(eval(x) if isinstance(x, str) else x)
    )
    comparison_df["phase4_bpe_artifacts"] = comparison_df["phase4_entities"].apply(
        lambda x: detect_bpe_artifacts(eval(x) if isinstance(x, str) else x)
    )

    # Entity length stats (if available)
    comparison_df["max_entity_length"] = comparison_df.apply(
        lambda row: max(
            [len(e) for e in (eval(row["v2_entities"]) if isinstance(row["v2_entities"], str) else row["v2_entities"])]
            + [len(e) for e in (eval(row["phase4_entities"]) if isinstance(row["phase4_entities"], str) else row["phase4_entities"])]
        ) if row["total_entities"] > 0 else 0,
        axis=1,
    )

    # Boost interest score for edge cases
    comparison_df["interest_score"] += (
        comparison_df["v2_bpe_artifacts"] + comparison_df["phase4_bpe_artifacts"]
    ) * 0.5
    comparison_df["interest_score"] += (comparison_df["max_entity_length"] > 50) * 3.0

    # Log category distribution
    logger.info("\nCategory distribution (all papers):")
    category_counts = comparison_df["category"].value_counts()
    for category, count in category_counts.items():
        logger.info(f"  {category}: {count}")

    # Perform stratified sampling
    logger.info(f"\nPerforming stratified sampling ({n_per_category} per category)...")

    # Filter out BOTH_EMPTY and OTHER categories for sampling
    sample_categories = ["AGREEMENT", "PHASE4_BETTER", "V2_BETTER", "DISAGREEMENT"]
    sample_df = comparison_df[comparison_df["category"].isin(sample_categories)].copy()

    sampled_df = stratified_sample(
        sample_df,
        category_col="category",
        n_per_category=n_per_category,
        random_state=42,
    )

    logger.info(f"\nTotal papers sampled: {len(sampled_df)}")
    logger.info("\nSampled distribution:")
    sampled_counts = sampled_df["category"].value_counts()
    for category, count in sampled_counts.items():
        logger.info(f"  {category}: {count}")

    # Create stratification metadata
    stratification = {
        "total_papers": len(comparison_df),
        "target_sample_size": n_per_category * len(sample_categories),
        "actual_sample_size": len(sampled_df),
        "samples_per_category": n_per_category,
        "categories": {
            "all_distribution": category_counts.to_dict(),
            "sampled_distribution": sampled_counts.to_dict(),
        },
        "sampling_criteria": {
            "prioritize_ground_truth": True,
            "prioritize_multiple_entities": True,
            "prioritize_disagreements": True,
            "prioritize_bpe_artifacts": True,
            "prioritize_long_entities": True,
        },
        "features": {
            "papers_with_ground_truth": int(sampled_df["has_ground_truth"].sum()),
            "papers_with_bpe_artifacts": int(
                ((sampled_df["v2_bpe_artifacts"] > 0) | (sampled_df["phase4_bpe_artifacts"] > 0)).sum()
            ),
            "mean_entities_per_paper": float(sampled_df["total_entities"].mean()),
            "mean_interest_score": float(sampled_df["interest_score"].mean()),
        },
        "timestamp": datetime.now().isoformat(),
        "random_seed": 42,
    }

    # Save results
    output_csv = output_dir / "sample_100_papers.csv"
    output_json = output_dir / "sample_stratification.json"

    logger.info(f"\nSaving sample to {output_csv}")
    sampled_df.to_csv(output_csv, index=False)

    logger.info(f"Saving stratification metadata to {output_json}")
    with open(output_json, "w") as f:
        json.dump(stratification, f, indent=2)

    # Summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("SAMPLING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total papers available: {len(comparison_df)}")
    logger.info(f"Papers sampled: {len(sampled_df)}")
    logger.info(f"Papers with ground truth: {sampled_df['has_ground_truth'].sum()}")
    logger.info(f"Papers with BPE artifacts: {((sampled_df['v2_bpe_artifacts'] > 0) | (sampled_df['phase4_bpe_artifacts'] > 0)).sum()}")
    logger.info(f"Mean entities per paper: {sampled_df['total_entities'].mean():.2f}")
    logger.info(f"Mean interest score: {sampled_df['interest_score'].mean():.2f}")

    logger.info("\n✓ Sampling complete!")

    return sampled_df, stratification


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Sample 100 papers for qualitative analysis (Script 05)"
    )
    parser.add_argument(
        "--comparison-file",
        type=Path,
        default=Path(__file__).parent.parent / "results" / "04_merged_comparison.csv",
        help="Path to merged comparison results (default: ../results/04_merged_comparison.csv)",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "ground_truth.json",
        help="Path to ground truth data (default: ../data/ground_truth.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data",
        help="Output directory (default: ../data)",
    )
    parser.add_argument(
        "--n-per-category",
        type=int,
        default=25,
        help="Number of papers per category (default: 25)",
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger = setup_logging(args.output_dir)

    try:
        # Run sampling
        sampled_df, stratification = create_sample_100_papers(
            comparison_file=args.comparison_file,
            ground_truth_file=args.ground_truth,
            output_dir=args.output_dir,
            n_per_category=args.n_per_category,
            logger=logger,
        )

        logger.info(f"\n{'=' * 80}")
        logger.info("SUCCESS: Sampling completed successfully!")
        logger.info(f"{'=' * 80}\n")

        return 0

    except Exception as e:
        logger.error(f"\n{'=' * 80}")
        logger.error(f"ERROR: Sampling failed!")
        logger.error(f"{'=' * 80}")
        logger.error(f"Error details: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
