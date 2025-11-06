import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from pathlib import Path
import json

# Configuration
PHASE2_RESULTS_FILE = 'phase2_complete_results.csv'
PHASE2B_BASE_DIR = 'collab_results/training_archives'
OUTPUT_CSV = 'phase2b_complete_results.csv'
OUTPUT_COMBINED_CSV = 'phase2_and_phase2b_combined_results.csv'

print("="*80)
print("PHASE 2B COMPLETE ANALYSIS - ALL 12 DATA POINTS")
print("="*80)
print()

# Load Phase 2 results (splits A, B, C, D, E)
print("📊 Loading Phase 2 results...")
phase2_df = pd.read_csv(PHASE2_RESULTS_FILE)
print(f"  ✓ Loaded {len(phase2_df)} Phase 2 splits (A, B, C, D, E)")
print()

# Extract Phase 2B results (splits F, G, H, I, J, K1, K2)
print("📊 Extracting Phase 2B results...")
phase2b_sessions = [
    '2025-11-03-lbd4go_splitF',
    '2025-11-03-lbd4go_splitG',
    '2025-11-03-lbd4go_splitH',
    '2025-11-03-lbd4go_splitI',
    '2025-11-03-lbd4go_splitJ',
    '2025-11-03-lbd4go_splitK1',
    '2025-11-03-lbd4go_splitK2'
]

phase2b_data = []
for session_id in phase2b_sessions:
    results_file = Path(PHASE2B_BASE_DIR) / session_id / 'data' / 'training_results.csv'
    metadata_file = Path(PHASE2B_BASE_DIR) / session_id / 'data' / 'experiment_metadata.json'

    if results_file.exists():
        df = pd.read_csv(results_file)
        row = df.iloc[0]

        # Load metadata for additional info
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        phase2b_data.append({
            'Split': row['split_name'],
            'Session': session_id,
            'Test_Complexity_Pct': row['complexity'] * 100,
            'Val_F1': row['val_f1'],
            'Val_Precision': row['val_precision'],
            'Val_Recall': row['val_recall'],
            'Train_F1': row['train_f1'],
            'Best_Epoch': row['best_epoch'],
            'Training_Time_Minutes': row['training_time_minutes'],
            'Status': row['status']
        })
        print(f"  ✓ {row['split_name']}: Complexity={row['complexity']*100:.1f}%, F1={row['val_f1']:.4f}")
    else:
        print(f"  ✗ {session_id}: Results file not found")

phase2b_df = pd.DataFrame(phase2b_data)
print(f"\n  ✓ Extracted {len(phase2b_df)} Phase 2B splits")
print()

# Save Phase 2B results
phase2b_df.to_csv(OUTPUT_CSV, index=False)
print(f"💾 Saved Phase 2B results to: {OUTPUT_CSV}")
print()

# Combine Phase 2 and Phase 2B for analysis
print("📊 Combining Phase 2 and Phase 2B results...")

# Standardize column names
phase2_analysis = phase2_df[['Split', 'Test_Complexity_Pct', 'Val_F1']].copy()
phase2b_analysis = phase2b_df[['Split', 'Test_Complexity_Pct', 'Val_F1']].copy()

combined_df = pd.concat([phase2_analysis, phase2b_analysis], ignore_index=True)
combined_df = combined_df.sort_values('Test_Complexity_Pct').reset_index(drop=True)

# Add baselines
v2_baseline = pd.DataFrame([{
    'Split': 'V2',
    'Test_Complexity_Pct': 17.0,
    'Val_F1': 0.749
}])
current_baseline = pd.DataFrame([{
    'Split': 'Current',
    'Test_Complexity_Pct': 48.6,
    'Val_F1': 0.644
}])

# Full dataset with baselines for plotting
plot_df = pd.concat([combined_df, v2_baseline, current_baseline], ignore_index=True)
plot_df = plot_df.sort_values('Test_Complexity_Pct').reset_index(drop=True)

print("="*80)
print("ALL 12 DATA POINTS (Phase 2 + Phase 2B)")
print("="*80)
print()
print(combined_df.to_string(index=False))
print()

# Save combined results
combined_df.to_csv(OUTPUT_COMBINED_CSV, index=False)
print(f"💾 Saved combined results to: {OUTPUT_COMBINED_CSV}")
print()

# Statistical Analysis
print("="*80)
print("STATISTICAL ANALYSIS")
print("="*80)
print()

# Extract Phase 2 + Phase 2B data points (exclude baselines)
complexity = combined_df['Test_Complexity_Pct'].values
f1_scores = combined_df['Val_F1'].values

# Overall correlation
overall_corr = np.corrcoef(complexity, f1_scores)[0, 1]
print(f"Overall Pearson Correlation: {overall_corr:.4f}")
print(f"Overall R-squared: {overall_corr**2:.4f}")
print()

# Performance metrics
best_idx = combined_df['Val_F1'].idxmax()
worst_idx = combined_df['Val_F1'].idxmin()

print("="*80)
print("PERFORMANCE METRICS")
print("="*80)
print()
print(f"Best Split: {combined_df.loc[best_idx, 'Split']} "
      f"(F1 = {combined_df.loc[best_idx, 'Val_F1']:.4f}, "
      f"Complexity = {combined_df.loc[best_idx, 'Test_Complexity_Pct']:.1f}%)")
print(f"Worst Split: {combined_df.loc[worst_idx, 'Split']} "
      f"(F1 = {combined_df.loc[worst_idx, 'Val_F1']:.4f}, "
      f"Complexity = {combined_df.loc[worst_idx, 'Test_Complexity_Pct']:.1f}%)")
print(f"Performance Range: {combined_df['Val_F1'].max() - combined_df['Val_F1'].min():.4f} points")
print(f"Standard Deviation: {combined_df['Val_F1'].std():.4f}")
print()

# Gap analysis
best_f1 = combined_df['Val_F1'].max()
v2_f1 = 0.749
current_f1 = 0.644
original_gap = v2_f1 - current_f1
closed_gap = best_f1 - current_f1

print("="*80)
print("GAP CLOSURE ANALYSIS")
print("="*80)
print()
print(f"Original Gap (V2 vs Current): {original_gap:.4f} ({100*original_gap:.1f}%)")
print(f"Best Split vs Current: +{closed_gap:.4f} ({100*closed_gap/current_f1:.1f}% improvement)")
print(f"Best Split vs V2: {best_f1 - v2_f1:+.4f} ({100*(best_f1 - v2_f1)/v2_f1:+.1f}%)")
print(f"\nGap Closure: {100*closed_gap/original_gap:.1f}% of original gap")
print(f"Remaining Gap to V2: {v2_f1 - best_f1:.4f} ({100*(v2_f1 - best_f1)/v2_f1:.1f}%)")
print()

# Create comprehensive visualization
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# Left plot: Scatter with polynomial fit
ax1 = axes[0]

# Assign colors based on split type
colors_dict = {
    'K1': '#e74c3c',  # Red - extreme low
    'A': '#ff6b6b',   # Light red
    'D': '#4ecdc4',   # Cyan
    'C': '#45b7d1',   # Blue
    'F': '#95a5a6',   # Gray (Phase 2B)
    'G': '#7f8c8d',   # Dark gray (Phase 2B)
    'B': '#ffd700',   # Gold - BEST
    'H': '#6c757d',   # Medium gray (Phase 2B)
    'I': '#5a6268',   # Darker gray (Phase 2B)
    'J': '#96ceb4',   # Green
    'E': '#ffeaa7',   # Yellow
    'K2': '#e67e22'   # Orange - extreme high
}

# Plot Phase 2 + Phase 2B splits
for idx, row in combined_df.iterrows():
    split_name = row['Split']
    color = colors_dict.get(split_name, '#95a5a6')
    marker = '*' if split_name == 'B' else 'o'
    size = 400 if split_name == 'B' else 150
    alpha = 1.0 if split_name == 'B' else 0.7
    zorder = 10 if split_name == 'B' else 3

    ax1.scatter(row['Test_Complexity_Pct'], row['Val_F1'],
                color=color, s=size, marker=marker,
                alpha=alpha, edgecolors='black', linewidth=2,
                label=f"Split {split_name}", zorder=zorder)

# Plot baselines
ax1.scatter(17.0, 0.749, color='green', s=250, marker='^',
            alpha=0.8, edgecolors='black', linewidth=2.5,
            label='V2 Baseline (TARGET)', zorder=5)
ax1.scatter(48.6, 0.644, color='darkred', s=250, marker='v',
            alpha=0.8, edgecolors='black', linewidth=2.5,
            label='Current Baseline', zorder=5)

# Fit polynomial curve (quadratic or cubic)
def quadratic(x, a, b, c):
    return a * x**2 + b * x + c

def cubic(x, a, b, c, d):
    return a * x**3 + b * x**2 + c * x + d

# Try both fits
try:
    popt_quad, _ = curve_fit(quadratic, complexity, f1_scores)
    popt_cubic, _ = curve_fit(cubic, complexity, f1_scores)

    # Calculate R² for both
    y_pred_quad = quadratic(complexity, *popt_quad)
    y_pred_cubic = cubic(complexity, *popt_cubic)

    r2_quad = 1 - np.sum((f1_scores - y_pred_quad)**2) / np.sum((f1_scores - np.mean(f1_scores))**2)
    r2_cubic = 1 - np.sum((f1_scores - y_pred_cubic)**2) / np.sum((f1_scores - np.mean(f1_scores))**2)

    print(f"Quadratic fit R²: {r2_quad:.4f}")
    print(f"Cubic fit R²: {r2_cubic:.4f}")

    # Use cubic if significantly better
    if r2_cubic > r2_quad + 0.05:
        popt = popt_cubic
        fit_func = cubic
        fit_type = 'Cubic'
        print(f"Using cubic fit (R² = {r2_cubic:.4f})")
    else:
        popt = popt_quad
        fit_func = quadratic
        fit_type = 'Quadratic'
        print(f"Using quadratic fit (R² = {r2_quad:.4f})")

    x_smooth = np.linspace(5, 95, 200)
    y_smooth = fit_func(x_smooth, *popt)
    ax1.plot(x_smooth, y_smooth, 'k--', alpha=0.5, linewidth=3,
             label=f'{fit_type} Fit', zorder=2)

    # Find and mark the peak
    if fit_type == 'Quadratic':
        peak_x = -popt[1] / (2 * popt[0])
    else:
        # For cubic, find peak numerically
        from scipy.optimize import minimize_scalar
        result = minimize_scalar(lambda x: -fit_func(x, *popt), bounds=(5, 95), method='bounded')
        peak_x = result.x

    peak_y = fit_func(peak_x, *popt)
    ax1.axvline(peak_x, color='gray', linestyle=':', alpha=0.5, linewidth=2.5)
    ax1.text(peak_x, 0.655, f'Peak: {peak_x:.1f}%',
             ha='center', fontsize=11, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    print(f"\nOptimal Complexity: {peak_x:.1f}%")
    print(f"Peak F1 (from fit): {peak_y:.4f}")
    print()

except Exception as e:
    print(f"Curve fitting failed: {e}")
    peak_x = None

ax1.set_xlabel('Test Set Entity Complexity (%)', fontsize=13, fontweight='bold')
ax1.set_ylabel('Validation F1 Score', fontsize=13, fontweight='bold')
ax1.set_title('Phase 2 + Phase 2B: Complete Complexity-Performance Map (12 Data Points)',
              fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(loc='lower right', fontsize=8, ncol=2)
ax1.set_ylim(0.63, 0.76)
ax1.set_xlim(0, 100)

# Right plot: Bar chart with ranking
ax2 = axes[1]

# Create ranking dataframe
all_configs = pd.concat([
    pd.DataFrame([{
        'Config': 'V2 Baseline',
        'Val_F1': 0.749,
        'Complexity': 17.0,
        'Color': 'green',
        'Type': 'baseline'
    }]),
    pd.DataFrame([{
        'Config': f"Split {row['Split']}",
        'Val_F1': row['Val_F1'],
        'Complexity': row['Test_Complexity_Pct'],
        'Color': colors_dict.get(row['Split'], '#95a5a6'),
        'Type': 'phase2b' if row['Split'] in ['F', 'G', 'H', 'I', 'J', 'K1', 'K2'] else 'phase2'
    } for idx, row in combined_df.iterrows()]),
    pd.DataFrame([{
        'Config': 'Current',
        'Val_F1': 0.644,
        'Complexity': 48.6,
        'Color': 'darkred',
        'Type': 'baseline'
    }])
], ignore_index=True)

# Sort by F1
all_configs = all_configs.sort_values('Val_F1', ascending=False).reset_index(drop=True)

# Create bars
bars = ax2.bar(range(len(all_configs)), all_configs['Val_F1'],
               color=all_configs['Color'], alpha=0.7,
               edgecolor='black', linewidth=1.5)

# Add value labels
for idx, (bar, f1, complexity) in enumerate(zip(bars, all_configs['Val_F1'], all_configs['Complexity'])):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.002,
             f'{f1:.4f}\n({complexity:.1f}%)',
             ha='center', va='bottom', fontsize=8, fontweight='bold')

# Highlight the winner
winner_idx = all_configs['Val_F1'].idxmax()
bars[winner_idx].set_linewidth(3.5)
bars[winner_idx].set_edgecolor('gold')

ax2.set_xticks(range(len(all_configs)))
ax2.set_xticklabels(all_configs['Config'], rotation=45, ha='right', fontsize=9)
ax2.set_ylabel('Validation F1 Score', fontsize=13, fontweight='bold')
ax2.set_title('Final Rankings - All Configurations (Phase 2 + Phase 2B)',
              fontsize=14, fontweight='bold')
ax2.set_ylim(0.63, 0.76)
ax2.grid(True, alpha=0.3, axis='y')
ax2.axhline(y=0.749, color='green', linestyle='--', linewidth=2.5, alpha=0.5)
ax2.axhline(y=0.644, color='darkred', linestyle='--', linewidth=2.5, alpha=0.5)

plt.tight_layout()
plt.savefig('phase2b_complete_analysis.png', dpi=300, bbox_inches='tight')
print(f"📊 Visualization saved to: phase2b_complete_analysis.png")
plt.close()

# Summary findings
print()
print("="*80)
print("KEY FINDINGS - PHASE 2B COMPLETE")
print("="*80)
print()
print("1. COMPREHENSIVE CURVE MAPPING COMPLETE")
print(f"   - Tested 12 complexity levels (5% to 92%)")
print(f"   - Optimal complexity: ~{peak_x:.1f}%" if peak_x else "   - Peak identification failed")
print(f"   - Best performer: Split {combined_df.loc[best_idx, 'Split']} at {combined_df.loc[best_idx, 'Test_Complexity_Pct']:.1f}% complexity")
print()
print("2. GAP CLOSURE STATUS")
print(f"   - Closed {100*closed_gap/original_gap:.1f}% of gap to V2 baseline")
print(f"   - Best F1: {best_f1:.4f} vs V2's {v2_f1:.4f}")
print(f"   - Remaining gap: {v2_f1 - best_f1:.4f} points ({100*(v2_f1-best_f1)/v2_f1:.1f}%)")
print()
print("3. UNEXPECTED PATTERNS")
print("   - Check for any non-monotonic behavior in low/mid range")
print("   - Phase 2B provides fine-grained mapping around optimal region")
print()
print("4. NEXT STEPS")
print("   ✅ Curve fully characterized with 12 data points")
print("   ⚠️  If peak shifted from Split B, investigate training variations")
print("   🔍 Final gap analysis requires training procedure investigation")
print()
print("="*80)
print("✅ PHASE 2B ANALYSIS COMPLETE")
print("="*80)
print()
