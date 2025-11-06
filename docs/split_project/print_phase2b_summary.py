import pandas as pd

# Load combined results
df = pd.read_csv('phase2_and_phase2b_combined_results.csv')

print("="*80)
print("PHASE 2B COMPLETE - SURPRISING FINDINGS")
print("="*80)
print()

print("📊 Performance by Complexity Range:")
print()

# Group by complexity ranges
ranges = [
    ("Extreme Low (5%)", df[df['Test_Complexity_Pct'] == 5.0]),
    ("Low (12-28%)", df[(df['Test_Complexity_Pct'] >= 12) & (df['Test_Complexity_Pct'] <= 28.2)]),
    ("Mid-Low (35%)", df[df['Test_Complexity_Pct'] == 35.3]),
    ("⚠️  VALLEY (55-60%)", df[(df['Test_Complexity_Pct'] >= 55) & (df['Test_Complexity_Pct'] <= 60)]),
    ("🥇 PEAK (66%)", df[df['Test_Complexity_Pct'] == 65.9]),
    ("Mid-High (70-75%)", df[(df['Test_Complexity_Pct'] >= 70) & (df['Test_Complexity_Pct'] <= 75)]),
    ("High Plateau (80-92%)", df[(df['Test_Complexity_Pct'] >= 80) & (df['Test_Complexity_Pct'] <= 92)])
]

for range_name, range_df in ranges:
    if not range_df.empty:
        avg_f1 = range_df['Val_F1'].mean()
        splits = ', '.join(range_df['Split'].tolist())
        print(f"{range_name:30s} | Avg F1: {avg_f1:.4f} | Splits: {splits}")

print()
print("="*80)
print("KEY INSIGHTS")
print("="*80)
print()

# Valley analysis
valley_splits = df[(df['Test_Complexity_Pct'] >= 55) & (df['Test_Complexity_Pct'] <= 60)]
split_d = df[df['Split'] == 'D'].iloc[0]
print("🕳️  THE VALLEY PROBLEM:")
print(f"   - Splits F (55%) and G (60%) are in a performance VALLEY")
print(f"   - Average F1 in valley: {valley_splits['Val_F1'].mean():.4f}")
print(f"   - This is WORSE than Split D (28%): {split_d['Val_F1']:.4f}")
print(f"   - Drop from Split D: {split_d['Val_F1'] - valley_splits['Val_F1'].mean():.4f} points")
print()

# Plateau analysis
plateau_splits = df[(df['Test_Complexity_Pct'] >= 80) & (df['Test_Complexity_Pct'] <= 92)]
split_b = df[df['Split'] == 'B'].iloc[0]
print("🏔️  THE HIGH PLATEAU:")
print(f"   - High complexity (80-92%) performs ALMOST AS WELL as Split B")
print(f"   - Average F1 in plateau: {plateau_splits['Val_F1'].mean():.4f}")
print(f"   - Split B F1: {split_b['Val_F1']:.4f}")
print(f"   - Difference: only {split_b['Val_F1'] - plateau_splits['Val_F1'].mean():.4f} points")
print(f"   - Split K2 (92%) is only {split_b['Val_F1'] - df[df['Split']=='K2'].iloc[0]['Val_F1']:.4f} points behind Split B!")
print()

# Comparison table
print("="*80)
print("COMPARISON: EXPECTED vs ACTUAL")
print("="*80)
print()
print("Complexity | Expected Rank | Actual F1 | Actual Rank | Surprise?")
print("-"*80)

expectations = [
    (5.0, "Worst", "Worst"),
    (12.0, "Low", "Low"),
    (28.2, "Medium-Low", "High!"),  # Surprising
    (35.3, "Medium", "Medium-Low"),
    (55.0, "Near-Optimal", "LOW!"),  # VERY SURPRISING
    (60.0, "Near-Optimal", "LOWEST!"),  # VERY SURPRISING
    (65.9, "OPTIMAL", "BEST!"),  # As expected
    (70.0, "Good", "Medium"),  # Slightly disappointing
    (75.0, "Good", "Medium"),
    (80.0, "Declining", "HIGH!"),  # Surprising
    (83.9, "Declining", "HIGH!"),  # Surprising
    (92.0, "Low", "VERY HIGH!")  # VERY SURPRISING
]

for complexity, expected, outcome in expectations:
    row = df[df['Test_Complexity_Pct'] == complexity]
    if not row.empty:
        split = row.iloc[0]['Split']
        f1 = row.iloc[0]['Val_F1']
        rank = len(df[df['Val_F1'] > f1]) + 1
        surprise = "⚠️  YES" if "!" in outcome else "✓ No"
        print(f"{complexity:5.1f}%     | {expected:14s} | {f1:.4f}    | #{rank:2d}/12       | {surprise}")

print()
print("="*80)
print("RECOMMENDATIONS")
print("="*80)
print()
print("1. ✅ USE Split B (66%) for benchmarking - empirically best")
print("2. ⚠️  TEST high complexity (80-85%) for production - nearly as good, may be more stable")
print("3. ❌ AVOID the valley (55-60%) - consistently underperforms")
print("4. 🔍 INVESTIGATE Split B with multiple seeds - is it consistently good or just lucky?")
print("5. 📊 VALIDATE high-complexity plateau with repeated runs")
print()
