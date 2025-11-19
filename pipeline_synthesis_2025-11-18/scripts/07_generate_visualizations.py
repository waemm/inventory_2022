#!/usr/bin/env python3
"""
Generate Visualizations for Pipeline Synthesis

Create comprehensive visualizations:
1. GCBR Tracking Heatmap (52 × 10 matrix)
2. Paper Set Venn Diagrams
3. Entity Coverage Bar Charts
4. Baseline Retention Funnel
5. Strategy Comparison Charts
"""

import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from datetime import datetime
from matplotlib_venn import venn3, venn3_circles

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

# Paths
BASE_DIR = Path("/Users/warren/development/GBC/inventory_2022")
GCBR_TRACKING_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/results/gcbr_tracking"
BASELINE_COMP_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/results/baseline_comparison"
STRATEGY_COMP_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/results/strategy_comparison"
PAPER_SETS_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/data/paper_sets"
ENTITY_INV_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/data/entity_inventories"

# Output directory
OUTPUT_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/results/visualizations"

def create_gcbr_heatmap():
    """Create GCBR tracking heatmap (52 × 10 stages)"""
    print("\nCreating GCBR tracking heatmap...")

    df_gcbr = pd.read_csv(GCBR_TRACKING_DIR / "gcbr_tracking_complete.csv")

    # Select stage columns
    stage_cols = [col for col in df_gcbr.columns if col.startswith('s') and '_' in col]
    stage_cols = sorted(stage_cols, key=lambda x: int(x.split('_')[0][1:]))

    # Create matrix (normalize by row for retention rates)
    matrix = df_gcbr[stage_cols].values

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))

    # Heatmap 1: Absolute paper counts
    im1 = ax1.imshow(matrix, cmap='YlOrRd', aspect='auto')
    ax1.set_xticks(range(len(stage_cols)))
    ax1.set_xticklabels([col.replace('s', 'S').replace('_', ' ').title()
                          for col in stage_cols], rotation=45, ha='right')
    ax1.set_yticks(range(len(df_gcbr)))
    ax1.set_yticklabels(df_gcbr['gcbr_name'], fontsize=7)
    ax1.set_title('GCBR Tracking: Absolute Paper Counts', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Pipeline Stage', fontsize=12)
    ax1.set_ylabel('GCBR Name', fontsize=12)
    plt.colorbar(im1, ax=ax1, label='Paper Count')

    # Heatmap 2: Retention rates (normalized by first stage)
    matrix_norm = np.zeros_like(matrix, dtype=float)
    for i in range(matrix.shape[0]):
        if matrix[i, 0] > 0:
            matrix_norm[i, :] = matrix[i, :] / matrix[i, 0] * 100

    im2 = ax2.imshow(matrix_norm, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
    ax2.set_xticks(range(len(stage_cols)))
    ax2.set_xticklabels([col.replace('s', 'S').replace('_', ' ').title()
                          for col in stage_cols], rotation=45, ha='right')
    ax2.set_yticks(range(len(df_gcbr)))
    ax2.set_yticklabels(df_gcbr['gcbr_name'], fontsize=7)
    ax2.set_title('GCBR Tracking: Retention Rates (%)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Pipeline Stage', fontsize=12)
    ax2.set_ylabel('GCBR Name', fontsize=12)
    plt.colorbar(im2, ax=ax2, label='Retention %')

    plt.tight_layout()
    output_file = OUTPUT_DIR / "gcbr_tracking_heatmap.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

def create_paper_venn_diagram():
    """Create Venn diagram for paper set overlaps"""
    print("\nCreating paper set Venn diagram...")

    # Load paper sets
    df_a = pd.read_csv(PAPER_SETS_DIR / "set_a_linguistic.csv")
    df_b = pd.read_csv(PAPER_SETS_DIR / "set_b_setfit.csv")

    pmids_a = set(df_a['pmid'])
    pmids_b = set(df_b['pmid'])

    # Create Venn diagram
    fig, ax = plt.subplots(figsize=(10, 8))

    # Calculate overlaps
    only_a = len(pmids_a - pmids_b)
    only_b = len(pmids_b - pmids_a)
    both = len(pmids_a & pmids_b)

    # Create venn
    venn = venn3(subsets=(only_a, only_b, both, 0, 0, 0, 0),
                 set_labels=('Linguistic', 'SetFit', ''),
                 ax=ax)

    # Customize
    venn.get_label_by_id('100').set_text(f'{only_a:,}\n(52.2%)')
    venn.get_label_by_id('010').set_text(f'{only_b:,}\n(47.7%)')
    venn.get_label_by_id('110').set_text(f'{both}\n(0.1%)')

    ax.set_title('Paper Set Overlap: Linguistic vs SetFit\n(Total Union: 16,605 papers)',
                 fontsize=14, fontweight='bold')

    output_file = OUTPUT_DIR / "paper_set_venn.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

def create_entity_venn_diagram():
    """Create Venn diagram for entity overlaps"""
    print("\nCreating entity Venn diagram...")

    # Load entity inventories
    df_a = pd.read_csv(ENTITY_INV_DIR / "set_a_entity_inventory.csv")
    df_b = pd.read_csv(ENTITY_INV_DIR / "set_b_entity_inventory.csv")

    entities_a = set(df_a['entity_name'])
    entities_b = set(df_b['entity_name'])

    # Calculate overlaps
    only_a = len(entities_a - entities_b)
    only_b = len(entities_b - entities_a)
    both = len(entities_a & entities_b)

    # Create venn
    fig, ax = plt.subplots(figsize=(10, 8))
    venn = venn3(subsets=(only_a, only_b, both, 0, 0, 0, 0),
                 set_labels=('Linguistic', 'SetFit', ''),
                 ax=ax)

    # Customize
    venn.get_label_by_id('100').set_text(f'{only_a:,}\n(54.0%)')
    venn.get_label_by_id('010').set_text(f'{only_b:,}\n(39.2%)')
    venn.get_label_by_id('110').set_text(f'{both:,}\n(6.9%)')

    ax.set_title('Entity Overlap: Linguistic vs SetFit\n(Total Union: 29,642 entities)',
                 fontsize=14, fontweight='bold')

    output_file = OUTPUT_DIR / "entity_venn.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

def create_baseline_coverage_chart():
    """Create baseline coverage comparison chart"""
    print("\nCreating baseline coverage chart...")

    with open(BASELINE_COMP_DIR / "baseline_coverage_stats.json", 'r') as f:
        stats = json.load(f)

    # Data
    strategies = ['Linguistic\n(Set A)', 'SetFit\n(Set B)', 'Union\n(Set C)']
    coverage = [
        stats['exact_coverage_percent']['set_a'],
        stats['exact_coverage_percent']['set_b'],
        stats['exact_coverage_percent']['set_c']
    ]
    counts = [
        stats['exact_matches']['set_a'],
        stats['exact_matches']['set_b'],
        stats['exact_matches']['set_c']
    ]

    # Create chart
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(strategies, coverage, color=['#3498db', '#e74c3c', '#2ecc71'], alpha=0.8)

    # Add value labels
    for bar, count, pct in zip(bars, counts, coverage):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{pct:.1f}%\n({count:,}/3,112)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel('Coverage of 2022 Baseline (%)', fontsize=12, fontweight='bold')
    ax.set_title('Baseline Coverage Comparison (2022 → 2011-2021)',
                 fontsize=14, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.axhline(y=90, color='gray', linestyle='--', alpha=0.5, label='90% threshold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    output_file = OUTPUT_DIR / "baseline_coverage_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

def create_gcbr_capture_chart():
    """Create GCBR capture comparison chart"""
    print("\nCreating GCBR capture chart...")

    with open(STRATEGY_COMP_DIR / "strategy_comparison_summary.json", 'r') as f:
        stats = json.load(f)

    gcbr_perf = stats['gcbr_performance']

    # Data
    strategies = ['Linguistic\n(Set A)', 'SetFit\n(Set B)', 'Union\n(Set C)']
    gcbrs_captured = [
        gcbr_perf['gcbrs_in_a'],
        gcbr_perf['gcbrs_in_b'],
        gcbr_perf['gcbrs_in_c']
    ]
    total_papers = [
        gcbr_perf['papers_a'],
        gcbr_perf['papers_b'],
        gcbr_perf['papers_c']
    ]

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Chart 1: GCBRs captured
    bars1 = ax1.bar(strategies, gcbrs_captured, color=['#3498db', '#e74c3c', '#2ecc71'], alpha=0.8)
    for bar, count in zip(bars1, gcbrs_captured):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                 f'{count}/52\n({count/52*100:.1f}%)',
                 ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax1.set_ylabel('GCBRs Captured', fontsize=12, fontweight='bold')
    ax1.set_title('GCBR Capture Rates', fontsize=13, fontweight='bold')
    ax1.set_ylim(0, 40)
    ax1.axhline(y=34, color='green', linestyle='--', alpha=0.5, label='Union (34)')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Chart 2: Total GCBR papers
    bars2 = ax2.bar(strategies, total_papers, color=['#3498db', '#e74c3c', '#2ecc71'], alpha=0.8)
    for bar, count in zip(bars2, total_papers):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 20,
                 f'{count:,}',
                 ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax2.set_ylabel('Total Papers', fontsize=12, fontweight='bold')
    ax2.set_title('Total GCBR Papers Captured', fontsize=13, fontweight='bold')
    ax2.set_ylim(0, 1400)
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    output_file = OUTPUT_DIR / "gcbr_capture_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

def create_strategy_summary_dashboard():
    """Create comprehensive strategy summary dashboard"""
    print("\nCreating strategy summary dashboard...")

    with open(STRATEGY_COMP_DIR / "strategy_comparison_summary.json", 'r') as f:
        stats = json.load(f)

    # Create 2x2 dashboard
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # Panel 1: Paper counts
    ax1 = fig.add_subplot(gs[0, 0])
    strategies = ['Linguistic', 'SetFit', 'Union']
    papers = [
        stats['paper_overlap']['set_a_total'],
        stats['paper_overlap']['set_b_total'],
        stats['paper_overlap']['set_c_total']
    ]
    bars = ax1.bar(strategies, papers, color=['#3498db', '#e74c3c', '#2ecc71'], alpha=0.8)
    for bar, count in zip(bars, papers):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 300,
                 f'{count:,}', ha='center', va='bottom', fontweight='bold')
    ax1.set_ylabel('Papers', fontsize=11, fontweight='bold')
    ax1.set_title('Paper Counts by Strategy', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    # Panel 2: Entity counts
    ax2 = fig.add_subplot(gs[0, 1])
    entities = [
        stats['entity_coverage']['set_a_entities'],
        stats['entity_coverage']['set_b_entities'],
        stats['entity_coverage']['set_c_entities']
    ]
    bars = ax2.bar(strategies, entities, color=['#3498db', '#e74c3c', '#2ecc71'], alpha=0.8)
    for bar, count in zip(bars, entities):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 500,
                 f'{count:,}', ha='center', va='bottom', fontweight='bold')
    ax2.set_ylabel('Unique Entities', fontsize=11, fontweight='bold')
    ax2.set_title('Entity Counts by Strategy', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    # Panel 3: Baseline coverage
    ax3 = fig.add_subplot(gs[1, 0])
    coverage = [
        stats['baseline_performance']['coverage_a'],
        stats['baseline_performance']['coverage_b'],
        stats['baseline_performance']['coverage_c']
    ]
    bars = ax3.bar(strategies, coverage, color=['#3498db', '#e74c3c', '#2ecc71'], alpha=0.8)
    for bar, pct in zip(bars, coverage):
        ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                 f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')
    ax3.set_ylabel('Baseline Coverage (%)', fontsize=11, fontweight='bold')
    ax3.set_title('2022 Baseline Coverage (2011-2021)', fontsize=12, fontweight='bold')
    ax3.axhline(y=90, color='gray', linestyle='--', alpha=0.5)
    ax3.set_ylim(0, 105)
    ax3.grid(axis='y', alpha=0.3)

    # Panel 4: GCBR capture
    ax4 = fig.add_subplot(gs[1, 1])
    gcbr_perf = stats['gcbr_performance']
    gcbrs = [
        gcbr_perf['gcbrs_in_a'],
        gcbr_perf['gcbrs_in_b'],
        gcbr_perf['gcbrs_in_c']
    ]
    bars = ax4.bar(strategies, gcbrs, color=['#3498db', '#e74c3c', '#2ecc71'], alpha=0.8)
    for bar, count in zip(bars, gcbrs):
        ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                 f'{count}/52', ha='center', va='bottom', fontweight='bold')
    ax4.set_ylabel('GCBRs Captured', fontsize=11, fontweight='bold')
    ax4.set_title('High-Priority Resources (GCBRs)', fontsize=12, fontweight='bold')
    ax4.set_ylim(0, 40)
    ax4.grid(axis='y', alpha=0.3)

    fig.suptitle('Strategy Comparison Dashboard', fontsize=16, fontweight='bold', y=0.98)

    output_file = OUTPUT_DIR / "strategy_summary_dashboard.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

def main():
    print("=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate all visualizations
    create_gcbr_heatmap()
    create_paper_venn_diagram()
    create_entity_venn_diagram()
    create_baseline_coverage_chart()
    create_gcbr_capture_chart()
    create_strategy_summary_dashboard()

    print("\n" + "=" * 80)
    print("VISUALIZATION GENERATION COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nAll visualizations saved to: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
