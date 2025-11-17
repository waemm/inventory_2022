#!/usr/bin/env python3
"""
Create correlation plots for SetFit vs Review scores
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Load data
base_dir = Path('/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146')
df = pd.read_csv(base_dir / 'agent10_scored_results.csv')

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 1. SetFit vs Review Scatter
ax1 = axes[0, 0]
scatter = ax1.scatter(df['setfit_confidence'], df['review_score'],
                     alpha=0.5, s=30, c=df['review_score'], cmap='RdYlGn')
ax1.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Perfect agreement')
correlation = df['setfit_confidence'].corr(df['review_score'])
ax1.set_xlabel('SetFit Confidence', fontsize=11)
ax1.set_ylabel('Review Score', fontsize=11)
ax1.set_title(f'SetFit vs Review Score (r={correlation:.3f})', fontsize=12, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax1, label='Review Score')

# 2. Linguistic vs Review Scatter
ax2 = axes[0, 1]
scatter2 = ax2.scatter(df['ling_score'], df['review_score'],
                      alpha=0.5, s=30, c=df['review_score'], cmap='RdYlGn')
ling_correlation = df['ling_score'].corr(df['review_score'])
ax2.set_xlabel('Linguistic Score', fontsize=11)
ax2.set_ylabel('Review Score', fontsize=11)
ax2.set_title(f'Linguistic vs Review Score (r={ling_correlation:.3f})', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)
plt.colorbar(scatter2, ax=ax2, label='Review Score')

# 3. Review Score Distribution
ax3 = axes[1, 0]
ax3.hist(df['review_score'], bins=20, edgecolor='black', alpha=0.7, color='steelblue')
ax3.axvline(df['review_score'].mean(), color='red', linestyle='--',
            linewidth=2, label=f'Mean: {df["review_score"].mean():.3f}')
ax3.axvline(df['review_score'].median(), color='orange', linestyle='--',
            linewidth=2, label=f'Median: {df["review_score"].median():.3f}')
ax3.set_xlabel('Review Score', fontsize=11)
ax3.set_ylabel('Count', fontsize=11)
ax3.set_title('Review Score Distribution', fontsize=12, fontweight='bold')
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')

# 4. Agreement Matrix
ax4 = axes[1, 1]
# Create bins for both scores
setfit_bins = pd.cut(df['setfit_confidence'], bins=[0, 0.6, 0.7, 0.75, 1.0],
                     labels=['<0.6', '0.6-0.7', '0.7-0.75', '0.75+'])
review_bins = pd.cut(df['review_score'], bins=[0, 0.5, 0.65, 0.75, 1.0],
                     labels=['<0.5', '0.5-0.65', '0.65-0.75', '0.75+'])

# Create crosstab
crosstab = pd.crosstab(review_bins, setfit_bins)
sns.heatmap(crosstab, annot=True, fmt='d', cmap='YlGnBu', ax=ax4, cbar_kws={'label': 'Count'})
ax4.set_xlabel('SetFit Confidence Bin', fontsize=11)
ax4.set_ylabel('Review Score Bin', fontsize=11)
ax4.set_title('Agreement Matrix (SetFit vs Review)', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig(base_dir / 'agent10_correlation_analysis.png', dpi=300, bbox_inches='tight')
print(f"✓ Correlation plots saved to: {base_dir / 'agent10_correlation_analysis.png'}")

# Create second figure for detailed breakdown
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))

# 5. Box plots by SetFit confidence category
ax5 = axes2[0]
df['setfit_category'] = pd.cut(df['setfit_confidence'],
                               bins=[0, 0.65, 0.70, 0.75, 1.0],
                               labels=['Medium\n(<0.65)', 'Med-High\n(0.65-0.70)',
                                      'High\n(0.70-0.75)', 'Very High\n(0.75+)'])
df.boxplot(column='review_score', by='setfit_category', ax=ax5)
ax5.set_xlabel('SetFit Confidence Category', fontsize=11)
ax5.set_ylabel('Review Score', fontsize=11)
ax5.set_title('Review Score Distribution by SetFit Category', fontsize=12, fontweight='bold')
plt.sca(ax5)
plt.xticks(rotation=0)

# 6. Disagreement cases
ax6 = axes2[1]
df['agreement_type'] = 'Medium Agreement'
df.loc[(df['setfit_confidence'] >= 0.70) & (df['review_score'] >= 0.70), 'agreement_type'] = 'High Agreement'
df.loc[(df['setfit_confidence'] >= 0.70) & (df['review_score'] < 0.50), 'agreement_type'] = 'False Positive'
df.loc[(df['setfit_confidence'] < 0.70) & (df['review_score'] >= 0.75), 'agreement_type'] = 'Missed Positive'

agreement_counts = df['agreement_type'].value_counts()
colors = {'High Agreement': '#2ecc71', 'Medium Agreement': '#f39c12',
          'False Positive': '#e74c3c', 'Missed Positive': '#3498db'}
bars = ax6.bar(range(len(agreement_counts)), agreement_counts.values,
               color=[colors.get(x, 'gray') for x in agreement_counts.index])
ax6.set_xticks(range(len(agreement_counts)))
ax6.set_xticklabels(agreement_counts.index, rotation=45, ha='right')
ax6.set_ylabel('Count', fontsize=11)
ax6.set_title('Agreement Type Distribution', fontsize=12, fontweight='bold')
ax6.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, (bar, value) in enumerate(zip(bars, agreement_counts.values)):
    height = bar.get_height()
    ax6.text(bar.get_x() + bar.get_width()/2., height,
             f'{value}\n({value/len(df)*100:.1f}%)',
             ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig(base_dir / 'agent10_agreement_analysis.png', dpi=300, bbox_inches='tight')
print(f"✓ Agreement analysis saved to: {base_dir / 'agent10_agreement_analysis.png'}")

# Print summary statistics
print("\n" + "="*70)
print("SUMMARY STATISTICS")
print("="*70)
print(f"Total papers: {len(df)}")
print(f"\nReview Score Statistics:")
print(f"  Mean: {df['review_score'].mean():.3f}")
print(f"  Median: {df['review_score'].median():.3f}")
print(f"  Std Dev: {df['review_score'].std():.3f}")
print(f"\nCorrelations:")
print(f"  SetFit-Review: {correlation:.3f}")
print(f"  Linguistic-Review: {ling_correlation:.3f}")
print(f"\nAgreement Types:")
for cat, count in agreement_counts.items():
    print(f"  {cat}: {count} ({count/len(df)*100:.1f}%)")
print("="*70)
