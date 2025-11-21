#!/usr/bin/env python3
"""
Generate Visualizations - Create PNG and interactive HTML charts

Generates visualizations from baseline comparison data:
1. Baseline Coverage Bar Chart (PNG + HTML)
2. Match Type Distribution Stacked Bar (PNG + HTML)
3. Resource Counts Bar Chart (PNG + HTML)
4. Score Distribution Histogram (PNG + HTML, if available)

Note: matplotlib-venn and plotly are optional dependencies.
If not available, will skip relevant visualizations.

Created: 2025-11-21
"""

import argparse
import pandas as pd
import json
from pathlib import Path
import sys

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Generate visualization charts')
parser.add_argument('--session-dir', type=str, required=True,
                    help='Session directory containing baseline_comparison/ subdirectory')
args = parser.parse_args()

# Paths
SESSION_DIR = Path(args.session_dir)
BASELINE_DIR = SESSION_DIR / 'baseline_comparison'
FINAL_DIR = SESSION_DIR / 'final'
VIZ_DIR = SESSION_DIR / 'visualizations'
VIZ_DIR.mkdir(parents=True, exist_ok=True)

# Input files
STATS_FILE = BASELINE_DIR / 'baseline_comparison_stats.json'
DATA_FILE = BASELINE_DIR / 'baseline_comparison_data.csv'
SET_C_FILE = FINAL_DIR / 'set_c_union_final.csv'

print("="*80)
print("GENERATING VISUALIZATIONS")
print("="*80)
print(f"Session: {SESSION_DIR.name}")
print(f"Output directory: {VIZ_DIR}\n")

# ============================================================================
# CHECK DEPENDENCIES
# ============================================================================

print("1. Checking dependencies...")

# Try importing matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
    print("   ✅ matplotlib available")
except ImportError:
    HAS_MATPLOTLIB = False
    print("   ⚠️  matplotlib not available - PNG charts will be skipped")
    print("      Install with: pip install matplotlib")

# Try importing plotly
try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
    print("   ✅ plotly available")
except ImportError:
    HAS_PLOTLY = False
    print("   ⚠️  plotly not available - HTML charts will be skipped")
    print("      Install with: pip install plotly")

if not HAS_MATPLOTLIB and not HAS_PLOTLY:
    print("\n❌ ERROR: Neither matplotlib nor plotly available")
    print("   Please install at least one:")
    print("   pip install matplotlib plotly")
    sys.exit(1)

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n2. Loading baseline comparison data...")

if not STATS_FILE.exists():
    print(f"   ❌ ERROR: Stats file not found: {STATS_FILE}")
    print(f"   Please run baseline comparison first (script 20)")
    sys.exit(1)

if not DATA_FILE.exists():
    print(f"   ❌ ERROR: Data file not found: {DATA_FILE}")
    print(f"   Please run baseline comparison first (script 20)")
    sys.exit(1)

with open(STATS_FILE, 'r') as f:
    stats = json.load(f)

df_data = pd.read_csv(DATA_FILE)

print(f"   Loaded stats for {len(stats['sets'])} sets")
print(f"   Loaded visualization data: {len(df_data)} rows")

# ============================================================================
# CHART 1: BASELINE COVERAGE BAR CHART
# ============================================================================

print("\n3. Generating baseline coverage chart...")

baseline_info = stats['baseline']
coverage_data = {
    'Set': ['Set A\n(Linguistic)', 'Set B\n(SetFit)', 'Set C\n(Union)'],
    'Coverage': [
        baseline_info['coverage_pct_a'],
        baseline_info['coverage_pct_b'],
        baseline_info['coverage_pct_c']
    ],
    'Count': [
        baseline_info['coverage_set_a'],
        baseline_info['coverage_set_b'],
        baseline_info['coverage_set_c']
    ]
}

# PNG version (matplotlib)
if HAS_MATPLOTLIB:
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(coverage_data['Set'], coverage_data['Coverage'],
                   color=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.8)

    # Add value labels on bars
    for i, (bar, count, pct) in enumerate(zip(bars, coverage_data['Count'], coverage_data['Coverage'])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('Baseline Coverage (%)', fontsize=12)
    ax.set_xlabel('Dataset', fontsize=12)
    ax.set_title(f'Baseline Coverage: % of {baseline_info["total_resources"]} Baseline Resources Found',
                 fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(coverage_data['Coverage']) * 1.15)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_png = VIZ_DIR / 'baseline_coverage.png'
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved PNG: {output_png}")

# HTML version (plotly)
if HAS_PLOTLY:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=coverage_data['Set'],
        y=coverage_data['Coverage'],
        text=[f"{count}<br>({pct:.1f}%)" for count, pct in zip(coverage_data['Count'], coverage_data['Coverage'])],
        textposition='outside',
        marker=dict(color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    ))

    fig.update_layout(
        title=f'Baseline Coverage: % of {baseline_info["total_resources"]} Baseline Resources Found',
        xaxis_title='Dataset',
        yaxis_title='Baseline Coverage (%)',
        yaxis=dict(range=[0, max(coverage_data['Coverage']) * 1.15]),
        template='plotly_white',
        height=500
    )

    output_html = VIZ_DIR / 'baseline_coverage.html'
    fig.write_html(output_html)
    print(f"   ✅ Saved HTML: {output_html}")

# ============================================================================
# CHART 2: MATCH TYPE DISTRIBUTION (STACKED BAR)
# ============================================================================

print("\n4. Generating match type distribution chart...")

match_data = {
    'Set': [],
    'PMID Only': [],
    'Entity Only': [],
    'Both': [],
    'Novel': []
}

for _, row in df_data.iterrows():
    match_data['Set'].append(row['set'])
    match_data['PMID Only'].append(row['pmid_only'])
    match_data['Entity Only'].append(row['entity_only'])
    match_data['Both'].append(row['both_match'])
    match_data['Novel'].append(row['novel'])

# PNG version (matplotlib)
if HAS_MATPLOTLIB:
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(match_data['Set']))
    width = 0.6

    # Create stacked bars
    p1 = ax.bar(x, match_data['Both'], width, label='Both Matches', color='#2ca02c')
    p2 = ax.bar(x, match_data['PMID Only'], width, bottom=match_data['Both'],
                label='PMID Match Only', color='#1f77b4')
    p3 = ax.bar(x, match_data['Entity Only'], width,
                bottom=[b + p for b, p in zip(match_data['Both'], match_data['PMID Only'])],
                label='Entity Match Only', color='#ff7f0e')
    p4 = ax.bar(x, match_data['Novel'], width,
                bottom=[b + p + e for b, p, e in zip(match_data['Both'], match_data['PMID Only'], match_data['Entity Only'])],
                label='Novel Discovery', color='#d62728')

    ax.set_ylabel('Number of Resources', fontsize=12)
    ax.set_xlabel('Dataset', fontsize=12)
    ax.set_title('Match Type Distribution by Dataset', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f"Set {s}" for s in match_data['Set']])
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_png = VIZ_DIR / 'match_types.png'
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved PNG: {output_png}")

# HTML version (plotly)
if HAS_PLOTLY:
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Both Matches',
        x=[f"Set {s}" for s in match_data['Set']],
        y=match_data['Both'],
        marker_color='#2ca02c'
    ))
    fig.add_trace(go.Bar(
        name='PMID Match Only',
        x=[f"Set {s}" for s in match_data['Set']],
        y=match_data['PMID Only'],
        marker_color='#1f77b4'
    ))
    fig.add_trace(go.Bar(
        name='Entity Match Only',
        x=[f"Set {s}" for s in match_data['Set']],
        y=match_data['Entity Only'],
        marker_color='#ff7f0e'
    ))
    fig.add_trace(go.Bar(
        name='Novel Discovery',
        x=[f"Set {s}" for s in match_data['Set']],
        y=match_data['Novel'],
        marker_color='#d62728'
    ))

    fig.update_layout(
        barmode='stack',
        title='Match Type Distribution by Dataset',
        xaxis_title='Dataset',
        yaxis_title='Number of Resources',
        template='plotly_white',
        height=500
    )

    output_html = VIZ_DIR / 'match_types.html'
    fig.write_html(output_html)
    print(f"   ✅ Saved HTML: {output_html}")

# ============================================================================
# CHART 3: RESOURCE COUNTS BAR CHART
# ============================================================================

print("\n5. Generating resource counts chart...")

# PNG version (matplotlib)
if HAS_MATPLOTLIB:
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(df_data))
    width = 0.35

    bars1 = ax.bar(x - width/2, df_data['in_baseline'], width, label='In Baseline', color='#1f77b4', alpha=0.8)
    bars2 = ax.bar(x + width/2, df_data['novel'], width, label='Novel', color='#ff7f0e', alpha=0.8)

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=9)

    ax.set_ylabel('Number of Resources', fontsize=12)
    ax.set_xlabel('Dataset', fontsize=12)
    ax.set_title('Resource Counts: In Baseline vs Novel Discoveries', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f"Set {s}\n(Total: {t})" for s, t in zip(df_data['set'], df_data['total'])])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_png = VIZ_DIR / 'resource_counts.png'
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved PNG: {output_png}")

# HTML version (plotly)
if HAS_PLOTLY:
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='In Baseline',
        x=[f"Set {s}" for s in df_data['set']],
        y=df_data['in_baseline'],
        marker_color='#1f77b4'
    ))
    fig.add_trace(go.Bar(
        name='Novel',
        x=[f"Set {s}" for s in df_data['set']],
        y=df_data['novel'],
        marker_color='#ff7f0e'
    ))

    fig.update_layout(
        barmode='group',
        title='Resource Counts: In Baseline vs Novel Discoveries',
        xaxis_title='Dataset',
        yaxis_title='Number of Resources',
        template='plotly_white',
        height=500
    )

    output_html = VIZ_DIR / 'resource_counts.html'
    fig.write_html(output_html)
    print(f"   ✅ Saved HTML: {output_html}")

# ============================================================================
# CHART 4: URL SCORE DISTRIBUTION (OPTIONAL)
# ============================================================================

print("\n6. Generating URL score distribution chart (if available)...")

if SET_C_FILE.exists():
    df_set_c = pd.read_csv(SET_C_FILE)

    # Check if URL score columns exist
    if 'url_score' in df_set_c.columns and df_set_c['url_score'].notna().sum() > 0:
        scores_baseline = df_set_c[df_set_c['in_baseline'] == True]['url_score'].dropna()
        scores_novel = df_set_c[df_set_c['in_baseline'] == False]['url_score'].dropna()

        if len(scores_baseline) > 0 or len(scores_novel) > 0:
            # PNG version (matplotlib)
            if HAS_MATPLOTLIB:
                fig, ax = plt.subplots(figsize=(10, 6))

                bins = np.linspace(0, 1, 21)
                if len(scores_baseline) > 0:
                    ax.hist(scores_baseline, bins=bins, alpha=0.6, label=f'In Baseline (n={len(scores_baseline)})',
                            color='#1f77b4', edgecolor='black')
                if len(scores_novel) > 0:
                    ax.hist(scores_novel, bins=bins, alpha=0.6, label=f'Novel (n={len(scores_novel)})',
                            color='#ff7f0e', edgecolor='black')

                ax.set_xlabel('URL Score', fontsize=12)
                ax.set_ylabel('Frequency', fontsize=12)
                ax.set_title('URL Score Distribution: Baseline vs Novel Resources', fontsize=14, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3, axis='y')

                plt.tight_layout()
                output_png = VIZ_DIR / 'score_distributions.png'
                plt.savefig(output_png, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"   ✅ Saved PNG: {output_png}")

            # HTML version (plotly)
            if HAS_PLOTLY:
                fig = go.Figure()

                if len(scores_baseline) > 0:
                    fig.add_trace(go.Histogram(
                        x=scores_baseline,
                        name=f'In Baseline (n={len(scores_baseline)})',
                        marker_color='#1f77b4',
                        opacity=0.7,
                        nbinsx=20
                    ))
                if len(scores_novel) > 0:
                    fig.add_trace(go.Histogram(
                        x=scores_novel,
                        name=f'Novel (n={len(scores_novel)})',
                        marker_color='#ff7f0e',
                        opacity=0.7,
                        nbinsx=20
                    ))

                fig.update_layout(
                    barmode='overlay',
                    title='URL Score Distribution: Baseline vs Novel Resources',
                    xaxis_title='URL Score',
                    yaxis_title='Frequency',
                    template='plotly_white',
                    height=500
                )

                output_html = VIZ_DIR / 'score_distributions.html'
                fig.write_html(output_html)
                print(f"   ✅ Saved HTML: {output_html}")
        else:
            print("   ⏭️  No URL scores available - skipping score distribution chart")
    else:
        print("   ⏭️  URL score column not found - skipping score distribution chart")
else:
    print("   ⏭️  Set C file not found - skipping score distribution chart")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("VISUALIZATIONS COMPLETE!")
print("="*80)

# Count generated files
png_files = list(VIZ_DIR.glob('*.png'))
html_files = list(VIZ_DIR.glob('*.html'))

print(f"\nGenerated {len(png_files)} PNG files and {len(html_files)} HTML files in:")
print(f"  {VIZ_DIR}")

print(f"\nFiles created:")
for f in sorted(VIZ_DIR.iterdir()):
    if f.suffix in ['.png', '.html']:
        print(f"  - {f.name}")

print("\n💡 Open HTML files in your browser for interactive charts!")
