#!/usr/bin/env python3
"""
Biodata Inventory Comparison Script

Compares the 2022 inventory rerun results with the original manually verified final inventory.
Generates two CSV reports: summary statistics and detailed breakdown.

Author: AI Assistant
Date: 2025-10-24
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import argparse

# Probability threshold for filtering
PROB_THRESHOLD = 0.978


def load_and_filter_data(file_path, dataset_name):
    """
    Load CSV file and filter by probability threshold.

    Args:
        file_path: Path to CSV file
        dataset_name: Name for logging purposes

    Returns:
        Filtered DataFrame
    """
    print(f"\n{'='*60}")
    print(f"Loading {dataset_name}...")
    print(f"{'='*60}")

    df = pd.read_csv(file_path)
    print(f"Total records loaded: {len(df):,}")

    # Filter by best_name_prob >= threshold
    df_filtered = df[df['best_name_prob'] >= PROB_THRESHOLD].copy()
    print(f"Records after filtering (best_name_prob >= {PROB_THRESHOLD}): {len(df_filtered):,}")
    print(f"Records filtered out: {len(df) - len(df_filtered):,}")

    # Handle potential duplicates within the dataset
    duplicates = df_filtered.duplicated(subset=['ID', 'best_name'], keep='first')
    if duplicates.any():
        print(f"WARNING: Found {duplicates.sum()} duplicate ID+best_name combinations")
        df_filtered = df_filtered[~duplicates].copy()
        print(f"After removing duplicates: {len(df_filtered):,}")

    return df_filtered


def article_level_comparison(rerun_df, final_df):
    """
    Compare at article ID level.

    Args:
        rerun_df: Rerun results DataFrame
        final_df: Final inventory DataFrame

    Returns:
        Dictionary with comparison metrics
    """
    print(f"\n{'='*60}")
    print("ARTICLE-LEVEL COMPARISON")
    print(f"{'='*60}")

    rerun_ids = set(rerun_df['ID'].unique())
    final_ids = set(final_df['ID'].unique())

    overlap_ids = rerun_ids & final_ids
    rerun_only_ids = rerun_ids - final_ids
    final_only_ids = final_ids - rerun_ids

    metrics = {
        'total_articles_rerun': len(rerun_ids),
        'total_articles_final': len(final_ids),
        'overlapping_articles': len(overlap_ids),
        'unique_to_rerun': len(rerun_only_ids),
        'unique_to_final': len(final_only_ids),
        'overlap_percentage': (len(overlap_ids) / len(final_ids) * 100) if len(final_ids) > 0 else 0
    }

    print(f"Rerun articles: {metrics['total_articles_rerun']:,}")
    print(f"Final inventory articles: {metrics['total_articles_final']:,}")
    print(f"Overlapping articles: {metrics['overlapping_articles']:,}")
    print(f"Unique to rerun: {metrics['unique_to_rerun']:,}")
    print(f"Unique to final: {metrics['unique_to_final']:,}")
    print(f"Overlap percentage: {metrics['overlap_percentage']:.2f}%")

    return metrics, overlap_ids, rerun_only_ids, final_only_ids


def resource_level_comparison(rerun_df, final_df):
    """
    Compare at resource level (ID + best_name combination).

    Args:
        rerun_df: Rerun results DataFrame
        final_df: Final inventory DataFrame

    Returns:
        Dictionary with comparison metrics and detailed comparison DataFrame
    """
    print(f"\n{'='*60}")
    print("RESOURCE-LEVEL COMPARISON")
    print(f"{'='*60}")

    # Create resource identifiers
    rerun_df['resource_id'] = rerun_df['ID'].astype(str) + '||' + rerun_df['best_name'].astype(str)
    final_df['resource_id'] = final_df['ID'].astype(str) + '||' + final_df['best_name'].astype(str)

    rerun_resources = set(rerun_df['resource_id'])
    final_resources = set(final_df['resource_id'])

    overlap_resources = rerun_resources & final_resources
    rerun_only_resources = rerun_resources - final_resources
    final_only_resources = final_resources - rerun_resources

    metrics = {
        'total_resources_rerun': len(rerun_resources),
        'total_resources_final': len(final_resources),
        'overlapping_resources': len(overlap_resources),
        'unique_to_rerun': len(rerun_only_resources),
        'unique_to_final': len(final_only_resources),
        'overlap_percentage': (len(overlap_resources) / len(final_resources) * 100) if len(final_resources) > 0 else 0
    }

    print(f"Rerun resources: {metrics['total_resources_rerun']:,}")
    print(f"Final inventory resources: {metrics['total_resources_final']:,}")
    print(f"Overlapping resources: {metrics['overlapping_resources']:,}")
    print(f"Unique to rerun: {metrics['unique_to_rerun']:,}")
    print(f"Unique to final: {metrics['unique_to_final']:,}")
    print(f"Overlap percentage: {metrics['overlap_percentage']:.2f}%")

    # Build detailed comparison DataFrame
    detailed_comparison = build_detailed_comparison(
        rerun_df, final_df,
        overlap_resources, rerun_only_resources, final_only_resources
    )

    return metrics, detailed_comparison


def build_detailed_comparison(rerun_df, final_df, overlap, rerun_only, final_only):
    """
    Build detailed comparison DataFrame with all resources.

    Args:
        rerun_df: Rerun results DataFrame
        final_df: Final inventory DataFrame
        overlap: Set of overlapping resource IDs
        rerun_only: Set of rerun-only resource IDs
        final_only: Set of final-only resource IDs

    Returns:
        Detailed comparison DataFrame
    """
    detailed_rows = []

    # Process overlapping resources
    for resource_id in overlap:
        id_val, name_val = resource_id.split('||')

        rerun_row = rerun_df[rerun_df['resource_id'] == resource_id].iloc[0]
        final_row = final_df[final_df['resource_id'] == resource_id].iloc[0]

        rerun_best_name_prob = rerun_row.get('best_name_prob', np.nan)
        final_best_name_prob = final_row.get('best_name_prob', np.nan)
        rerun_best_common_prob = rerun_row.get('best_common_prob', np.nan)
        final_best_common_prob = final_row.get('best_common_prob', np.nan)

        # Determine status and calculate difference_score if applicable
        if pd.notna(rerun_best_common_prob) and pd.notna(final_best_common_prob):
            if rerun_best_common_prob >= PROB_THRESHOLD and final_best_common_prob >= PROB_THRESHOLD:
                status = "both_high_conf"
                difference_score = np.nan
            elif rerun_best_common_prob < PROB_THRESHOLD:
                status = "rerun_low_conf"
                difference_score = abs(rerun_best_common_prob - final_best_common_prob)
            elif final_best_common_prob < PROB_THRESHOLD:
                status = "final_low_conf"
                difference_score = abs(rerun_best_common_prob - final_best_common_prob)
            else:
                status = "both_high_conf"
                difference_score = np.nan
        else:
            # If best_common_prob is missing, use best_name_prob for status determination
            if rerun_best_name_prob >= PROB_THRESHOLD and final_best_name_prob >= PROB_THRESHOLD:
                status = "both_high_conf"
            else:
                status = "prob_missing"
            difference_score = np.nan

        detailed_rows.append({
            'ID': id_val,
            'best_name': name_val,
            'in_rerun': True,
            'in_final': True,
            'rerun_best_name_prob': rerun_best_name_prob,
            'final_best_name_prob': final_best_name_prob,
            'rerun_best_common_prob': rerun_best_common_prob,
            'final_best_common_prob': final_best_common_prob,
            'difference_score': difference_score,
            'status': status
        })

    # Process rerun-only resources
    for resource_id in rerun_only:
        id_val, name_val = resource_id.split('||')
        rerun_row = rerun_df[rerun_df['resource_id'] == resource_id].iloc[0]

        detailed_rows.append({
            'ID': id_val,
            'best_name': name_val,
            'in_rerun': True,
            'in_final': False,
            'rerun_best_name_prob': rerun_row.get('best_name_prob', np.nan),
            'final_best_name_prob': np.nan,
            'rerun_best_common_prob': rerun_row.get('best_common_prob', np.nan),
            'final_best_common_prob': np.nan,
            'difference_score': np.nan,
            'status': 'unique_to_rerun'
        })

    # Process final-only resources
    for resource_id in final_only:
        id_val, name_val = resource_id.split('||')
        final_row = final_df[final_df['resource_id'] == resource_id].iloc[0]

        detailed_rows.append({
            'ID': id_val,
            'best_name': name_val,
            'in_rerun': False,
            'in_final': True,
            'rerun_best_name_prob': np.nan,
            'final_best_name_prob': final_row.get('best_name_prob', np.nan),
            'rerun_best_common_prob': np.nan,
            'final_best_common_prob': final_row.get('best_common_prob', np.nan),
            'difference_score': np.nan,
            'status': 'unique_to_final'
        })

    detailed_df = pd.DataFrame(detailed_rows)

    # Sort by difference_score (highest first), then by status
    detailed_df = detailed_df.sort_values(
        by=['difference_score', 'status'],
        ascending=[False, True],
        na_position='last'
    )

    return detailed_df


def calculate_probability_statistics(rerun_df, final_df, detailed_df):
    """
    Calculate statistics on probability scores.

    Args:
        rerun_df: Rerun results DataFrame
        final_df: Final inventory DataFrame
        detailed_df: Detailed comparison DataFrame

    Returns:
        Dictionary with probability statistics
    """
    print(f"\n{'='*60}")
    print("PROBABILITY STATISTICS")
    print(f"{'='*60}")

    stats = {
        'rerun_avg_best_name_prob': rerun_df['best_name_prob'].mean(),
        'final_avg_best_name_prob': final_df['best_name_prob'].mean(),
        'rerun_avg_best_common_prob': rerun_df['best_common_prob'].mean() if 'best_common_prob' in rerun_df.columns else np.nan,
        'final_avg_best_common_prob': final_df['best_common_prob'].mean() if 'best_common_prob' in final_df.columns else np.nan,
        'resources_needing_review': len(detailed_df[detailed_df['difference_score'].notna()]),
        'avg_difference_score': detailed_df['difference_score'].mean()
    }

    print(f"Rerun average best_name_prob: {stats['rerun_avg_best_name_prob']:.4f}")
    print(f"Final average best_name_prob: {stats['final_avg_best_name_prob']:.4f}")
    print(f"Rerun average best_common_prob: {stats['rerun_avg_best_common_prob']:.4f}")
    print(f"Final average best_common_prob: {stats['final_avg_best_common_prob']:.4f}")
    print(f"Resources needing review (prob differences): {stats['resources_needing_review']:,}")
    if stats['resources_needing_review'] > 0:
        print(f"Average difference score: {stats['avg_difference_score']:.4f}")

    return stats


def generate_summary_csv(article_metrics, resource_metrics, prob_stats, output_dir):
    """
    Generate summary CSV file.

    Args:
        article_metrics: Article-level metrics
        resource_metrics: Resource-level metrics
        prob_stats: Probability statistics
        output_dir: Output directory path
    """
    summary_data = []

    # Article-level metrics
    summary_data.append({
        'Metric Category': 'Article-Level',
        'Metric': 'Total Articles (Rerun)',
        'Value': article_metrics['total_articles_rerun']
    })
    summary_data.append({
        'Metric Category': 'Article-Level',
        'Metric': 'Total Articles (Final)',
        'Value': article_metrics['total_articles_final']
    })
    summary_data.append({
        'Metric Category': 'Article-Level',
        'Metric': 'Overlapping Articles',
        'Value': article_metrics['overlapping_articles']
    })
    summary_data.append({
        'Metric Category': 'Article-Level',
        'Metric': 'Unique to Rerun',
        'Value': article_metrics['unique_to_rerun']
    })
    summary_data.append({
        'Metric Category': 'Article-Level',
        'Metric': 'Unique to Final',
        'Value': article_metrics['unique_to_final']
    })
    summary_data.append({
        'Metric Category': 'Article-Level',
        'Metric': 'Overlap Percentage',
        'Value': f"{article_metrics['overlap_percentage']:.2f}%"
    })

    # Resource-level metrics
    summary_data.append({
        'Metric Category': 'Resource-Level',
        'Metric': 'Total Resources (Rerun)',
        'Value': resource_metrics['total_resources_rerun']
    })
    summary_data.append({
        'Metric Category': 'Resource-Level',
        'Metric': 'Total Resources (Final)',
        'Value': resource_metrics['total_resources_final']
    })
    summary_data.append({
        'Metric Category': 'Resource-Level',
        'Metric': 'Overlapping Resources',
        'Value': resource_metrics['overlapping_resources']
    })
    summary_data.append({
        'Metric Category': 'Resource-Level',
        'Metric': 'Unique to Rerun',
        'Value': resource_metrics['unique_to_rerun']
    })
    summary_data.append({
        'Metric Category': 'Resource-Level',
        'Metric': 'Unique to Final',
        'Value': resource_metrics['unique_to_final']
    })
    summary_data.append({
        'Metric Category': 'Resource-Level',
        'Metric': 'Overlap Percentage',
        'Value': f"{resource_metrics['overlap_percentage']:.2f}%"
    })

    # Probability statistics
    summary_data.append({
        'Metric Category': 'Probability Statistics',
        'Metric': 'Rerun Avg best_name_prob',
        'Value': f"{prob_stats['rerun_avg_best_name_prob']:.4f}"
    })
    summary_data.append({
        'Metric Category': 'Probability Statistics',
        'Metric': 'Final Avg best_name_prob',
        'Value': f"{prob_stats['final_avg_best_name_prob']:.4f}"
    })
    summary_data.append({
        'Metric Category': 'Probability Statistics',
        'Metric': 'Rerun Avg best_common_prob',
        'Value': f"{prob_stats['rerun_avg_best_common_prob']:.4f}"
    })
    summary_data.append({
        'Metric Category': 'Probability Statistics',
        'Metric': 'Final Avg best_common_prob',
        'Value': f"{prob_stats['final_avg_best_common_prob']:.4f}"
    })
    summary_data.append({
        'Metric Category': 'Probability Statistics',
        'Metric': 'Resources Needing Review',
        'Value': prob_stats['resources_needing_review']
    })
    if prob_stats['resources_needing_review'] > 0:
        summary_data.append({
            'Metric Category': 'Probability Statistics',
            'Metric': 'Avg Difference Score',
            'Value': f"{prob_stats['avg_difference_score']:.4f}"
        })

    summary_df = pd.DataFrame(summary_data)

    output_file = output_dir / "inventory_comparison_summary.csv"
    summary_df.to_csv(output_file, index=False)
    print(f"\n✓ Summary report saved to: {output_file}")

    return summary_df


def generate_detailed_csv(detailed_df, output_dir):
    """
    Generate detailed comparison CSV file.

    Args:
        detailed_df: Detailed comparison DataFrame
        output_dir: Output directory path
    """
    output_file = output_dir / "inventory_comparison_detailed.csv"
    detailed_df.to_csv(output_file, index=False)
    print(f"✓ Detailed report saved to: {output_file}")

    # Print status breakdown
    print(f"\n{'='*60}")
    print("STATUS BREAKDOWN (Detailed Report)")
    print(f"{'='*60}")
    status_counts = detailed_df['status'].value_counts()
    for status, count in status_counts.items():
        print(f"{status}: {count:,}")

    return output_file


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Compare two biodata inventory CSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare Colab rerun vs Final inventory
  python compare_inventory_results.py \\
    collab_results/2025-10-24-s4985d_2022_rerun/final_inventory.csv \\
    data/final_inventory_2022.csv \\
    -o collab_results/2025-10-24-s4985d_2022_rerun/comparison \\
    -n1 "Colab Rerun" -n2 "Final Inventory"

  # Compare Local rerun vs Colab rerun
  python compare_inventory_results.py \\
    inventory_classification_results/2025-10-22_2022_rerun/final_results/biodata_inventory_2022_rerun.csv \\
    collab_results/2025-10-24-s4985d_2022_rerun/final_inventory.csv \\
    -o comparison_local_vs_colab \\
    -n1 "Local Rerun" -n2 "Colab Rerun"
        """
    )
    parser.add_argument('file1', type=str, help='Path to first inventory CSV file')
    parser.add_argument('file2', type=str, help='Path to second inventory CSV file')
    parser.add_argument('-o', '--output', type=str, default='comparison_output',
                        help='Output directory for comparison results (default: comparison_output)')
    parser.add_argument('-n1', '--name1', type=str, default='Dataset 1',
                        help='Name for first dataset (default: Dataset 1)')
    parser.add_argument('-n2', '--name2', type=str, default='Dataset 2',
                        help='Name for second dataset (default: Dataset 2)')
    parser.add_argument('-t', '--threshold', type=float, default=0.978,
                        help='Probability threshold for filtering (default: 0.978)')

    args = parser.parse_args()

    # Update global threshold
    global PROB_THRESHOLD
    PROB_THRESHOLD = args.threshold

    # Convert paths
    file1_path = Path(args.file1)
    file2_path = Path(args.file2)
    output_dir = Path(args.output)

    print("\n" + "="*60)
    print("BIODATA INVENTORY COMPARISON")
    print("="*60)
    print(f"File 1 ({args.name1}): {file1_path}")
    print(f"File 2 ({args.name2}): {file2_path}")
    print(f"Probability threshold: {PROB_THRESHOLD}")

    # Check if files exist
    if not file1_path.exists():
        print(f"ERROR: File 1 not found: {file1_path}")
        sys.exit(1)
    if not file2_path.exists():
        print(f"ERROR: File 2 not found: {file2_path}")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Load and filter data
    df1 = load_and_filter_data(file1_path, args.name1)
    df2 = load_and_filter_data(file2_path, args.name2)

    # Article-level comparison
    article_metrics, overlap_ids, file1_only_ids, file2_only_ids = article_level_comparison(df1, df2)

    # Resource-level comparison
    resource_metrics, detailed_df = resource_level_comparison(df1, df2)

    # Probability statistics
    prob_stats = calculate_probability_statistics(df1, df2, detailed_df)

    # Generate output files
    print(f"\n{'='*60}")
    print("GENERATING OUTPUT FILES")
    print(f"{'='*60}")

    summary_df = generate_summary_csv(article_metrics, resource_metrics, prob_stats, output_dir)
    detailed_file = generate_detailed_csv(detailed_df, output_dir)

    print(f"\n{'='*60}")
    print("COMPARISON COMPLETE!")
    print(f"{'='*60}")
    print(f"\nResults saved to: {output_dir}")
    print(f"  - inventory_comparison_summary.csv")
    print(f"  - inventory_comparison_detailed.csv")


if __name__ == "__main__":
    main()
