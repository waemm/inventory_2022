#!/usr/bin/env python3
"""
Script 08: Create Visualizations

Purpose: Create all visualizations for the comparison report.

Figures:
1. Performance Comparison (F1/P/R bar charts)
2. Confusion Matrices (one for each system)
3. Entity Distributions (counts per paper)
4. BPE Contamination (histogram, before/after)
5. Coverage Venn (V2 only, Phase 4 only, Both, Neither)
6. Detection by Year (line plot over publication years)
7. Entity Length Distribution (histograms)

All outputs to ../figures/ as PNG files with 300 DPI.

Author: Analysis Pipeline
Date: 2025-11-05
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
from scipy import stats

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.comparison_utils import load_comparison_results


def setup_logging(output_dir: Path) -> logging.Logger:
    """Setup logging configuration."""
    log_file = output_dir / "08_visualizations.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


# Set publication-quality style
plt.style.use("seaborn-v0_8-paper")
sns.set_palette("husl")

FIGURE_DPI = 300
FIGURE_FORMAT = "png"


def create_performance_comparison(
    metrics: Dict[str, Any],
    output_path: Path,
    logger: logging.Logger = None,
) -> None:
    """
    Create bar chart comparing V2 and Phase 4 performance.

    Figure 1: Performance Comparison
    """
    if logger:
        logger.info("Creating Figure 1: Performance Comparison...")

    v2_metrics = metrics.get("v2_metrics", {})
    phase4_metrics = metrics.get("phase4_metrics", {})
    phase4_clean_metrics = metrics.get("phase4_clean_metrics", {})

    # Prepare data
    metric_names = ["Precision", "Recall", "F1-Score"]
    v2_values = [
        v2_metrics.get("precision", 0),
        v2_metrics.get("recall", 0),
        v2_metrics.get("f1", 0),
    ]
    phase4_raw_values = [
        phase4_metrics.get("precision", 0),
        phase4_metrics.get("recall", 0),
        phase4_metrics.get("f1", 0),
    ]
    phase4_clean_values = [
        phase4_clean_metrics.get("precision", 0),
        phase4_clean_metrics.get("recall", 0),
        phase4_clean_metrics.get("f1", 0),
    ]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(metric_names))
    width = 0.25

    bars1 = ax.bar(x - width, v2_values, width, label="V2 (Old)", color="#3498db", alpha=0.8)
    bars2 = ax.bar(x, phase4_raw_values, width, label="Phase 4 (Raw)", color="#e74c3c", alpha=0.8)
    bars3 = ax.bar(x + width, phase4_clean_values, width, label="Phase 4 (Clean)", color="#2ecc71", alpha=0.8)

    # Customize
    ax.set_xlabel("Metric", fontsize=12, fontweight="bold")
    ax.set_ylabel("Score", fontsize=12, fontweight="bold")
    ax.set_title("NER System Performance Comparison", fontsize=14, fontweight="bold", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metric_names)
    ax.legend(loc="lower right", fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    # Add value labels on bars
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.3f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    add_labels(bars1)
    add_labels(bars2)
    add_labels(bars3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, format=FIGURE_FORMAT, bbox_inches="tight")
    plt.close()

    if logger:
        logger.info(f"  Saved to {output_path}")


def create_confusion_matrices(
    metrics: Dict[str, Any],
    output_dir: Path,
    logger: logging.Logger = None,
) -> None:
    """
    Create confusion matrix heatmaps for each system.

    Figure 2: Confusion Matrices
    """
    if logger:
        logger.info("Creating Figure 2: Confusion Matrices...")

    systems = {
        "V2 (Old Model)": metrics.get("v2_metrics", {}),
        "Phase 4 (Clean)": metrics.get("phase4_clean_metrics", {}),
    }

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for idx, (system_name, system_metrics) in enumerate(systems.items()):
        cm = system_metrics.get("confusion_matrix", {})
        matrix = np.array([
            [cm.get("tp", 0), cm.get("fn", 0)],
            [cm.get("fp", 0), cm.get("tn", 0)]
        ])

        # Create heatmap
        sns.heatmap(
            matrix,
            annot=True,
            fmt="d",
            cmap="Blues",
            cbar=True,
            square=True,
            ax=axes[idx],
            xticklabels=["Predicted Positive", "Predicted Negative"],
            yticklabels=["Actual Positive", "Actual Negative"],
        )

        axes[idx].set_title(system_name, fontsize=12, fontweight="bold", pad=10)
        axes[idx].set_xlabel("Predicted", fontsize=10, fontweight="bold")
        axes[idx].set_ylabel("Actual", fontsize=10, fontweight="bold")

    plt.suptitle("Confusion Matrices", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    output_path = output_dir / "02_confusion_matrices.png"
    plt.savefig(output_path, dpi=FIGURE_DPI, format=FIGURE_FORMAT, bbox_inches="tight")
    plt.close()

    if logger:
        logger.info(f"  Saved to {output_path}")


def create_entity_distribution(
    comparison_df: pd.DataFrame,
    output_path: Path,
    logger: logging.Logger = None,
) -> None:
    """
    Create histogram of entity counts per paper.

    Figure 3: Entity Distribution
    """
    if logger:
        logger.info("Creating Figure 3: Entity Distribution...")

    # Parse entity counts
    v2_counts = []
    phase4_counts = []

    for _, row in comparison_df.iterrows():
        v2_entities = eval(row["v2_entities"]) if isinstance(row["v2_entities"], str) else row["v2_entities"]
        phase4_entities = eval(row["phase4_entities"]) if isinstance(row["phase4_entities"], str) else row["phase4_entities"]

        v2_counts.append(len([e for e in v2_entities if e.strip()]))
        phase4_counts.append(len([e for e in phase4_entities if e.strip()]))

    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # V2 distribution
    axes[0].hist(v2_counts, bins=20, color="#3498db", alpha=0.7, edgecolor="black")
    axes[0].set_xlabel("Entities per Paper", fontsize=10, fontweight="bold")
    axes[0].set_ylabel("Frequency", fontsize=10, fontweight="bold")
    axes[0].set_title("V2 (Old Model)", fontsize=12, fontweight="bold")
    axes[0].axvline(np.mean(v2_counts), color="red", linestyle="--", linewidth=2, label=f"Mean: {np.mean(v2_counts):.2f}")
    axes[0].legend()
    axes[0].grid(axis="y", alpha=0.3)

    # Phase 4 distribution
    axes[1].hist(phase4_counts, bins=20, color="#2ecc71", alpha=0.7, edgecolor="black")
    axes[1].set_xlabel("Entities per Paper", fontsize=10, fontweight="bold")
    axes[1].set_ylabel("Frequency", fontsize=10, fontweight="bold")
    axes[1].set_title("Phase 4 (Clean)", fontsize=12, fontweight="bold")
    axes[1].axvline(np.mean(phase4_counts), color="red", linestyle="--", linewidth=2, label=f"Mean: {np.mean(phase4_counts):.2f}")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.3)

    plt.suptitle("Entity Count Distribution", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, format=FIGURE_FORMAT, bbox_inches="tight")
    plt.close()

    if logger:
        logger.info(f"  Saved to {output_path}")


def create_bpe_contamination(
    bpe_analysis: Dict[str, Any],
    output_path: Path,
    logger: logging.Logger = None,
) -> None:
    """
    Create visualization of BPE contamination impact.

    Figure 4: BPE Contamination Analysis
    """
    if logger:
        logger.info("Creating Figure 4: BPE Contamination Analysis...")

    overall = bpe_analysis.get("overall_statistics", {})
    comparison = bpe_analysis.get("performance_comparison", {})

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: Contamination statistics
    labels = ["Clean Predictions", "BPE Contaminated"]
    sizes = [
        overall.get("total_phase4_predictions", 0) - overall.get("predictions_with_bpe", 0),
        overall.get("predictions_with_bpe", 0),
    ]
    colors = ["#2ecc71", "#e74c3c"]
    explode = (0, 0.1)

    axes[0].pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        shadow=True,
        startangle=90,
    )
    axes[0].set_title("BPE Contamination Rate", fontsize=12, fontweight="bold")

    # Right: Performance impact
    metrics = ["Precision", "Recall", "F1-Score"]
    raw_values = [
        comparison.get("raw_precision", 0),
        comparison.get("raw_recall", 0),
        comparison.get("raw_f1", 0),
    ]
    clean_values = [
        comparison.get("clean_precision", 0),
        comparison.get("clean_recall", 0),
        comparison.get("clean_f1", 0),
    ]

    x = np.arange(len(metrics))
    width = 0.35

    bars1 = axes[1].bar(x - width / 2, raw_values, width, label="Raw", color="#e74c3c", alpha=0.8)
    bars2 = axes[1].bar(x + width / 2, clean_values, width, label="Clean", color="#2ecc71", alpha=0.8)

    axes[1].set_xlabel("Metric", fontsize=10, fontweight="bold")
    axes[1].set_ylabel("Score", fontsize=10, fontweight="bold")
    axes[1].set_title("Impact on Performance", fontsize=12, fontweight="bold")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(metrics)
    axes[1].legend()
    axes[1].set_ylim(0, 1.0)
    axes[1].grid(axis="y", alpha=0.3)

    plt.suptitle("BPE Artifact Analysis", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, format=FIGURE_FORMAT, bbox_inches="tight")
    plt.close()

    if logger:
        logger.info(f"  Saved to {output_path}")


def create_coverage_venn(
    comparison_df: pd.DataFrame,
    output_path: Path,
    logger: logging.Logger = None,
) -> None:
    """
    Create Venn diagram-style visualization of prediction coverage.

    Figure 5: Coverage Analysis
    """
    if logger:
        logger.info("Creating Figure 5: Coverage Analysis...")

    # Calculate coverage statistics
    v2_only = 0
    phase4_only = 0
    both = 0
    neither = 0

    for _, row in comparison_df.iterrows():
        v2_entities = eval(row["v2_entities"]) if isinstance(row["v2_entities"], str) else row["v2_entities"]
        phase4_entities = eval(row["phase4_entities"]) if isinstance(row["phase4_entities"], str) else row["phase4_entities"]

        v2_has = len([e for e in v2_entities if e.strip()]) > 0
        phase4_has = len([e for e in phase4_entities if e.strip()]) > 0

        if v2_has and phase4_has:
            both += 1
        elif v2_has:
            v2_only += 1
        elif phase4_has:
            phase4_only += 1
        else:
            neither += 1

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Manual Venn diagram representation using rectangles
    categories = ["V2 Only", "Both Systems", "Phase 4 Only", "Neither"]
    counts = [v2_only, both, phase4_only, neither]
    colors = ["#3498db", "#9b59b6", "#2ecc71", "#95a5a6"]

    # Create stacked bar
    y_pos = 0
    for i, (cat, count, color) in enumerate(zip(categories, counts, colors)):
        height = count / sum(counts)
        ax.add_patch(Rectangle((0, y_pos), 1, height, facecolor=color, edgecolor="black", linewidth=2))

        # Add label
        label_text = f"{cat}\n{count} papers ({count / sum(counts) * 100:.1f}%)"
        ax.text(0.5, y_pos + height / 2, label_text, ha="center", va="center", fontsize=11, fontweight="bold")

        y_pos += height

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Entity Detection Coverage", fontsize=14, fontweight="bold", pad=20)

    # Add summary text
    total = sum(counts)
    summary_text = f"Total Papers: {total}\n\n"
    summary_text += f"Coverage:\n"
    summary_text += f"  Both: {both / total * 100:.1f}%\n"
    summary_text += f"  V2 Only: {v2_only / total * 100:.1f}%\n"
    summary_text += f"  Phase 4 Only: {phase4_only / total * 100:.1f}%\n"
    summary_text += f"  Neither: {neither / total * 100:.1f}%"

    ax.text(
        1.15,
        0.5,
        summary_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="center",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, format=FIGURE_FORMAT, bbox_inches="tight")
    plt.close()

    if logger:
        logger.info(f"  Saved to {output_path}")


def create_entity_length_distribution(
    comparison_df: pd.DataFrame,
    output_path: Path,
    logger: logging.Logger = None,
) -> None:
    """
    Create histogram of entity name lengths.

    Figure 6: Entity Length Distribution
    """
    if logger:
        logger.info("Creating Figure 6: Entity Length Distribution...")

    v2_lengths = []
    phase4_lengths = []

    for _, row in comparison_df.iterrows():
        v2_entities = eval(row["v2_entities"]) if isinstance(row["v2_entities"], str) else row["v2_entities"]
        phase4_entities = eval(row["phase4_entities"]) if isinstance(row["phase4_entities"], str) else row["phase4_entities"]

        v2_lengths.extend([len(e) for e in v2_entities if e.strip()])
        phase4_lengths.extend([len(e) for e in phase4_entities if e.strip()])

    # Create figure
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))

    # V2 lengths
    axes[0].hist(v2_lengths, bins=30, color="#3498db", alpha=0.7, edgecolor="black")
    axes[0].set_xlabel("Entity Name Length (characters)", fontsize=10, fontweight="bold")
    axes[0].set_ylabel("Frequency", fontsize=10, fontweight="bold")
    axes[0].set_title("V2 (Old Model)", fontsize=12, fontweight="bold")
    axes[0].axvline(np.mean(v2_lengths), color="red", linestyle="--", linewidth=2, label=f"Mean: {np.mean(v2_lengths):.1f}")
    axes[0].axvline(np.median(v2_lengths), color="orange", linestyle="--", linewidth=2, label=f"Median: {np.median(v2_lengths):.1f}")
    axes[0].legend()
    axes[0].grid(axis="y", alpha=0.3)

    # Phase 4 lengths
    axes[1].hist(phase4_lengths, bins=30, color="#2ecc71", alpha=0.7, edgecolor="black")
    axes[1].set_xlabel("Entity Name Length (characters)", fontsize=10, fontweight="bold")
    axes[1].set_ylabel("Frequency", fontsize=10, fontweight="bold")
    axes[1].set_title("Phase 4 (Clean)", fontsize=12, fontweight="bold")
    axes[1].axvline(np.mean(phase4_lengths), color="red", linestyle="--", linewidth=2, label=f"Mean: {np.mean(phase4_lengths):.1f}")
    axes[1].axvline(np.median(phase4_lengths), color="orange", linestyle="--", linewidth=2, label=f"Median: {np.median(phase4_lengths):.1f}")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.3)

    plt.suptitle("Entity Name Length Distribution", fontsize=14, fontweight="bold", y=1.00)
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, format=FIGURE_FORMAT, bbox_inches="tight")
    plt.close()

    if logger:
        logger.info(f"  Saved to {output_path}")


def create_all_visualizations(
    results_dir: Path,
    output_dir: Path,
    logger: logging.Logger = None,
) -> Dict[str, str]:
    """
    Create all visualizations for the report.

    Args:
        results_dir: Directory containing analysis results
        output_dir: Output directory for figures
        logger: Logger instance

    Returns:
        Dictionary mapping figure names to file paths
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("SCRIPT 08: CREATE VISUALIZATIONS")
    logger.info("=" * 80)

    # Load results
    logger.info("\nLoading analysis results...")

    quant_file = results_dir / "02_quantitative_metrics.json"
    with open(quant_file) as f:
        quantitative = json.load(f)

    bpe_file = results_dir / "04_bpe_analysis.json"
    with open(bpe_file) as f:
        bpe_analysis = json.load(f)

    comparison_file = results_dir / "04_merged_comparison.csv"
    comparison_df = pd.read_csv(comparison_file)

    logger.info(f"Loaded quantitative metrics: {len(quantitative)} keys")
    logger.info(f"Loaded BPE analysis: {len(bpe_analysis)} keys")
    logger.info(f"Loaded comparison data: {len(comparison_df)} papers")

    # Create figures
    figures = {}

    logger.info("\nGenerating visualizations...")

    # Figure 1: Performance Comparison
    fig1_path = output_dir / "01_performance_comparison.png"
    create_performance_comparison(quantitative, fig1_path, logger)
    figures["performance_comparison"] = str(fig1_path)

    # Figure 2: Confusion Matrices
    create_confusion_matrices(quantitative, output_dir, logger)
    figures["confusion_matrices"] = str(output_dir / "02_confusion_matrices.png")

    # Figure 3: Entity Distribution
    fig3_path = output_dir / "03_entity_distribution.png"
    create_entity_distribution(comparison_df, fig3_path, logger)
    figures["entity_distribution"] = str(fig3_path)

    # Figure 4: BPE Contamination
    fig4_path = output_dir / "04_bpe_contamination.png"
    create_bpe_contamination(bpe_analysis, fig4_path, logger)
    figures["bpe_contamination"] = str(fig4_path)

    # Figure 5: Coverage Venn
    fig5_path = output_dir / "05_coverage_analysis.png"
    create_coverage_venn(comparison_df, fig5_path, logger)
    figures["coverage_analysis"] = str(fig5_path)

    # Figure 6: Entity Length Distribution
    fig6_path = output_dir / "06_entity_length_distribution.png"
    create_entity_length_distribution(comparison_df, fig6_path, logger)
    figures["entity_length"] = str(fig6_path)

    # Save figure metadata
    metadata = {
        "figures": figures,
        "figure_count": len(figures),
        "dpi": FIGURE_DPI,
        "format": FIGURE_FORMAT,
        "generated_at": pd.Timestamp.now().isoformat(),
    }

    metadata_path = output_dir / "visualization_metadata.json"
    logger.info(f"\nSaving metadata to {metadata_path}")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VISUALIZATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total figures created: {len(figures)}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"DPI: {FIGURE_DPI}")
    logger.info(f"Format: {FIGURE_FORMAT}")

    logger.info("\nGenerated figures:")
    for name, path in figures.items():
        logger.info(f"  {name}: {Path(path).name}")

    logger.info("\n✓ Visualization generation complete!")

    return figures


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Create all visualizations for comparison report (Script 08)"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).parent.parent / "results",
        help="Directory with analysis results (default: ../results)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "figures",
        help="Output directory for figures (default: ../figures)",
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger = setup_logging(args.results_dir)

    try:
        # Create visualizations
        figures = create_all_visualizations(
            results_dir=args.results_dir,
            output_dir=args.output_dir,
            logger=logger,
        )

        logger.info(f"\n{'=' * 80}")
        logger.info("SUCCESS: All visualizations created successfully!")
        logger.info(f"{'=' * 80}\n")

        return 0

    except Exception as e:
        logger.error(f"\n{'=' * 80}")
        logger.error(f"ERROR: Visualization creation failed!")
        logger.error(f"{'=' * 80}")
        logger.error(f"Error details: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
