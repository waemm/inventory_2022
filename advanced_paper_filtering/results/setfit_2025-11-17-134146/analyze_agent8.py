#!/usr/bin/env python3
"""
Create visualizations for Agent 8 evaluation results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 12)

# Load data
df = pd.read_csv('agent8_scored_results.csv')

print(f"Loaded {len(df)} papers")

# Create figure with subplots
fig, axes = plt.subplots(3, 3, figsize=(18, 14))
fig.suptitle('Review Agent 8 - Comprehensive Analysis of 400 SetFit Papers', 
             fontsize=16, fontweight='bold')

# 1. Review Score Distribution
ax1 = axes[0, 0]
ax1.hist(df['review_score'], bins=30, color='steelblue', edgecolor='black', alpha=0.7)
ax1.axvline(df['review_score'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df["review_score"].mean():.3f}')
ax1.axvline(df['review_score'].median(), color='green', linestyle='--', linewidth=2, label=f'Median: {df["review_score"].median():.3f}')
ax1.set_xlabel('Review Score', fontsize=12)
ax1.set_ylabel('Frequency', fontsize=12)
ax1.set_title('Review Score Distribution', fontsize=13, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. SetFit Confidence Distribution
ax2 = axes[0, 1]
ax2.hist(df['setfit_confidence'], bins=30, color='coral', edgecolor='black', alpha=0.7)
ax2.axvline(df['setfit_confidence'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df["setfit_confidence"].mean():.3f}')
ax2.axvline(0.7, color='purple', linestyle='--', linewidth=2, label='Threshold: 0.7')
ax2.set_xlabel('SetFit Confidence', fontsize=12)
ax2.set_ylabel('Frequency', fontsize=12)
ax2.set_title('SetFit Confidence Distribution', fontsize=13, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. Linguistic Score Distribution
ax3 = axes[0, 2]
ax3.hist(df['ling_score'], bins=range(0, int(df['ling_score'].max())+2), 
         color='lightgreen', edgecolor='black', alpha=0.7)
ax3.set_xlabel('Linguistic Score', fontsize=12)
ax3.set_ylabel('Frequency', fontsize=12)
ax3.set_title('Linguistic Score Distribution', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3)

# 4. SetFit vs Review (WEAK correlation)
ax4 = axes[1, 0]
scatter = ax4.scatter(df['setfit_confidence'], df['review_score'], 
                      c=df['ling_score'], cmap='viridis', alpha=0.6, s=50)
ax4.plot([0, 1], [0, 1], 'r--', alpha=0.5, label='Perfect correlation')
corr = df['setfit_confidence'].corr(df['review_score'])
ax4.set_xlabel('SetFit Confidence', fontsize=12)
ax4.set_ylabel('Review Score', fontsize=12)
ax4.set_title(f'SetFit vs Review Score\n(Correlation: {corr:.3f} - WEAK)', 
              fontsize=13, fontweight='bold', color='red')
ax4.legend()
ax4.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax4, label='Ling Score')

# 5. Linguistic vs Review (STRONG correlation)
ax5 = axes[1, 1]
scatter2 = ax5.scatter(df['ling_score'], df['review_score'], 
                       c=df['setfit_confidence'], cmap='plasma', alpha=0.6, s=50)
# Add trendline
z = np.polyfit(df['ling_score'], df['review_score'], 1)
p = np.poly1d(z)
x_trend = np.linspace(df['ling_score'].min(), df['ling_score'].max(), 100)
ax5.plot(x_trend, p(x_trend), 'r--', linewidth=2, label='Trendline')
corr2 = df['ling_score'].corr(df['review_score'])
ax5.set_xlabel('Linguistic Score', fontsize=12)
ax5.set_ylabel('Review Score', fontsize=12)
ax5.set_title(f'Linguistic vs Review Score\n(Correlation: {corr2:.3f} - STRONG)', 
              fontsize=13, fontweight='bold', color='green')
ax5.legend()
ax5.grid(True, alpha=0.3)
plt.colorbar(scatter2, ax=ax5, label='SetFit Conf')

# 6. SetFit vs Linguistic (WEAK correlation)
ax6 = axes[1, 2]
ax6.scatter(df['setfit_confidence'], df['ling_score'], 
            c=df['review_score'], cmap='coolwarm', alpha=0.6, s=50)
corr3 = df['setfit_confidence'].corr(df['ling_score'])
ax6.set_xlabel('SetFit Confidence', fontsize=12)
ax6.set_ylabel('Linguistic Score', fontsize=12)
ax6.set_title(f'SetFit vs Linguistic Score\n(Correlation: {corr3:.3f} - WEAK)', 
              fontsize=13, fontweight='bold')
ax6.grid(True, alpha=0.3)

# 7. Score Categories by SetFit Confidence
ax7 = axes[2, 0]
high_setfit = df[df['setfit_confidence'] >= 0.7]
med_setfit = df[df['setfit_confidence'] < 0.7]

categories = ['High\n(≥0.8)', 'Med-High\n(0.6-0.79)', 'Borderline\n(0.4-0.59)', 'Low\n(<0.4)']
high_counts = [
    len(high_setfit[high_setfit['review_score'] >= 0.8]),
    len(high_setfit[(high_setfit['review_score'] >= 0.6) & (high_setfit['review_score'] < 0.8)]),
    len(high_setfit[(high_setfit['review_score'] >= 0.4) & (high_setfit['review_score'] < 0.6)]),
    len(high_setfit[high_setfit['review_score'] < 0.4])
]
med_counts = [
    len(med_setfit[med_setfit['review_score'] >= 0.8]),
    len(med_setfit[(med_setfit['review_score'] >= 0.6) & (med_setfit['review_score'] < 0.8)]),
    len(med_setfit[(med_setfit['review_score'] >= 0.4) & (med_setfit['review_score'] < 0.6)]),
    len(med_setfit[med_setfit['review_score'] < 0.4])
]

x = np.arange(len(categories))
width = 0.35
ax7.bar(x - width/2, high_counts, width, label='High SetFit (≥0.7)', color='steelblue')
ax7.bar(x + width/2, med_counts, width, label='Med SetFit (<0.7)', color='coral')
ax7.set_xlabel('Review Score Category', fontsize=12)
ax7.set_ylabel('Number of Papers', fontsize=12)
ax7.set_title('Review Categories by SetFit Confidence', fontsize=13, fontweight='bold')
ax7.set_xticks(x)
ax7.set_xticklabels(categories)
ax7.legend()
ax7.grid(True, alpha=0.3, axis='y')

# Add values on bars
for i, (h, m) in enumerate(zip(high_counts, med_counts)):
    ax7.text(i - width/2, h + 1, str(h), ha='center', va='bottom', fontsize=9)
    ax7.text(i + width/2, m + 1, str(m), ha='center', va='bottom', fontsize=9)

# 8. Correlation Comparison
ax8 = axes[2, 1]
correlations = [
    df['setfit_confidence'].corr(df['review_score']),
    df['ling_score'].corr(df['review_score']),
    df['setfit_confidence'].corr(df['ling_score'])
]
labels = ['SetFit vs\nReview', 'Ling vs\nReview', 'SetFit vs\nLing']
colors = ['red', 'green', 'orange']
bars = ax8.bar(labels, correlations, color=colors, alpha=0.7, edgecolor='black')
ax8.axhline(0.5, color='black', linestyle='--', linewidth=1, label='Strong threshold')
ax8.axhline(0.3, color='gray', linestyle='--', linewidth=1, label='Moderate threshold')
ax8.set_ylabel('Pearson Correlation', fontsize=12)
ax8.set_title('Correlation Comparison\n(Ling >> SetFit)', fontsize=13, fontweight='bold')
ax8.set_ylim([0, 0.7])
ax8.legend()
ax8.grid(True, alpha=0.3, axis='y')

# Add values on bars
for i, (bar, corr) in enumerate(zip(bars, correlations)):
    ax8.text(i, corr + 0.02, f'{corr:.3f}', ha='center', va='bottom', 
             fontsize=11, fontweight='bold')

# 9. Quality Matrix
ax9 = axes[2, 2]
quality_data = {
    'High SetFit\nHigh Review\n(True Positive)': len(df[(df['setfit_confidence'] >= 0.7) & (df['review_score'] >= 0.8)]),
    'High SetFit\nLow Review\n(False Positive)': len(df[(df['setfit_confidence'] >= 0.7) & (df['review_score'] < 0.4)]),
    'Low SetFit\nHigh Review\n(False Negative)': len(df[(df['setfit_confidence'] < 0.6) & (df['review_score'] >= 0.7)]),
    'Low SetFit\nLow Review\n(True Negative)': len(df[(df['setfit_confidence'] < 0.6) & (df['review_score'] < 0.4)])
}

quality_labels = list(quality_data.keys())
quality_values = list(quality_data.values())
colors_quality = ['green', 'red', 'orange', 'blue']

bars2 = ax9.barh(quality_labels, quality_values, color=colors_quality, alpha=0.7, edgecolor='black')
ax9.set_xlabel('Number of Papers', fontsize=12)
ax9.set_title('SetFit Quality Matrix', fontsize=13, fontweight='bold')
ax9.grid(True, alpha=0.3, axis='x')

# Add values on bars
for i, (bar, val) in enumerate(zip(bars2, quality_values)):
    ax9.text(val + 1, i, str(val), va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('agent8_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved visualization to: agent8_comprehensive_analysis.png")

# Generate additional statistics
print("\n" + "="*80)
print("ADDITIONAL STATISTICS")
print("="*80)

print("\nScore Statistics by SetFit Confidence Level:")
print("-" * 60)
for threshold, label in [(0.8, "Very High"), (0.7, "High"), (0.6, "Medium"), (0.5, "Low")]:
    subset = df[df['setfit_confidence'] >= threshold]
    if len(subset) > 0:
        print(f"{label:12} (≥{threshold}): n={len(subset):3}, "
              f"Review Mean={subset['review_score'].mean():.3f}, "
              f"Review Median={subset['review_score'].median():.3f}")

print("\nScore Statistics by Linguistic Score:")
print("-" * 60)
for ling_threshold in [0, 1, 2]:
    subset = df[df['ling_score'] >= ling_threshold]
    if len(subset) > 0:
        print(f"Ling ≥{ling_threshold}: n={len(subset):3}, "
              f"Review Mean={subset['review_score'].mean():.3f}, "
              f"Review Median={subset['review_score'].median():.3f}")

print("\nSetFit False Positive Analysis:")
print("-" * 60)
false_positives = df[(df['setfit_confidence'] >= 0.7) & (df['review_score'] < 0.5)]
print(f"Papers with SetFit ≥0.7 but Review <0.5: {len(false_positives)}")
if len(false_positives) > 0:
    print(f"Mean SetFit confidence: {false_positives['setfit_confidence'].mean():.3f}")
    print(f"Mean Review score: {false_positives['review_score'].mean():.3f}")

print("\nSetFit False Negative Analysis:")
print("-" * 60)
false_negatives = df[(df['setfit_confidence'] < 0.6) & (df['review_score'] >= 0.8)]
print(f"Papers with SetFit <0.6 but Review ≥0.8: {len(false_negatives)}")
if len(false_negatives) > 0:
    print(f"Mean SetFit confidence: {false_negatives['setfit_confidence'].mean():.3f}")
    print(f"Mean Review score: {false_negatives['review_score'].mean():.3f}")

print("\n" + "="*80)
print("VISUALIZATION COMPLETE")
print("="*80)
