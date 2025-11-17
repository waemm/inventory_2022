#!/usr/bin/env python3
"""
Aggregate all 11 agent review results into a single master dataset.
Combines 800 papers from agents 1-4 and 2,800 papers from agents 5-11.
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("="*80)
print("AGGREGATING ALL AGENT REVIEW RESULTS")
print("="*80)

# Collect all agent results
all_results = []
agent_stats = []

# Agents 1-4 (200 papers each) - handle various column names
for i in range(1, 5):
    filename = f'agent{i}_scored_results.csv'
    if Path(filename).exists():
        df = pd.read_csv(filename)

        # Find the score column (different names in each agent)
        score_col = None
        for col_name in ['review_score', 'agent_score', f'agent{i}_score', 'expert_score']:
            if col_name in df.columns:
                score_col = col_name
                break

        if score_col is None:
            print(f"✗ Agent {i}: No score column found (columns: {list(df.columns)})")
            continue

        # Standardize to 'review_score'
        if score_col != 'review_score':
            df['review_score'] = df[score_col]

        df['agent'] = i
        df['agent_sample_size'] = 200
        all_results.append(df)

        stats = {
            'agent': i,
            'papers': len(df),
            'mean_score': df['review_score'].mean(),
            'high_confidence': (df['review_score'] >= 0.7).sum(),
            'medium_confidence': ((df['review_score'] >= 0.5) & (df['review_score'] < 0.7)).sum(),
            'low_confidence': (df['review_score'] < 0.5).sum()
        }
        agent_stats.append(stats)
        print(f"✓ Agent {i}: {len(df)} papers, mean score: {stats['mean_score']:.3f} (using {score_col})")
    else:
        print(f"✗ Agent {i}: File not found")

# Agents 5-11 (400 papers each)
for i in range(5, 12):
    filename = f'agent{i}_scored_results.csv'
    if Path(filename).exists():
        df = pd.read_csv(filename)
        df['agent'] = i
        df['agent_sample_size'] = 400
        all_results.append(df)

        stats = {
            'agent': i,
            'papers': len(df),
            'mean_score': df['review_score'].mean(),
            'high_confidence': (df['review_score'] >= 0.7).sum(),
            'medium_confidence': ((df['review_score'] >= 0.5) & (df['review_score'] < 0.7)).sum(),
            'low_confidence': (df['review_score'] < 0.5).sum()
        }
        agent_stats.append(stats)
        print(f"✓ Agent {i}: {len(df)} papers, mean score: {stats['mean_score']:.3f}")
    else:
        print(f"✗ Agent {i}: File not found")

# Combine all results
if all_results:
    master_df = pd.concat(all_results, ignore_index=True)

    print(f"\n{'='*80}")
    print("MASTER DATASET CREATED")
    print(f"{'='*80}")
    print(f"Total papers reviewed: {len(master_df):,}")
    print(f"Total agents: {len(all_results)}")
    print(f"Date range: 2025-11-17")

    # Save master dataset
    master_df.to_csv('ALL_AGENTS_MASTER_RESULTS.csv', index=False)
    print(f"\n✓ Saved: ALL_AGENTS_MASTER_RESULTS.csv ({len(master_df):,} papers)")

    # Create statistics dataframe
    stats_df = pd.DataFrame(agent_stats)
    stats_df.to_csv('ALL_AGENTS_STATISTICS.csv', index=False)
    print(f"✓ Saved: ALL_AGENTS_STATISTICS.csv ({len(stats_df)} agents)")

    # Overall statistics
    print(f"\n{'='*80}")
    print("AGGREGATE STATISTICS")
    print(f"{'='*80}")

    print(f"\nReview Score Distribution:")
    print(f"  Mean: {master_df['review_score'].mean():.3f}")
    print(f"  Std:  {master_df['review_score'].std():.3f}")
    print(f"  Min:  {master_df['review_score'].min():.3f}")
    print(f"  Max:  {master_df['review_score'].max():.3f}")

    print(f"\nConfidence Levels:")
    high = (master_df['review_score'] >= 0.7).sum()
    medium = ((master_df['review_score'] >= 0.5) & (master_df['review_score'] < 0.7)).sum()
    low = (master_df['review_score'] < 0.5).sum()

    print(f"  High (≥0.7):   {high:,} papers ({100*high/len(master_df):.1f}%)")
    print(f"  Medium (0.5-0.7): {medium:,} papers ({100*medium/len(master_df):.1f}%)")
    print(f"  Low (<0.5):    {low:,} papers ({100*low/len(master_df):.1f}%)")

    # Correlation analysis
    print(f"\nCorrelation Analysis:")
    if 'setfit_confidence' in master_df.columns:
        setfit_corr = master_df['review_score'].corr(master_df['setfit_confidence'])
        print(f"  SetFit confidence: r = {setfit_corr:.3f}")

    if 'ling_score' in master_df.columns:
        ling_corr = master_df['review_score'].corr(master_df['ling_score'])
        print(f"  Linguistic score:  r = {ling_corr:.3f}")

    # Top papers
    print(f"\n{'='*80}")
    print("TOP 10 HIGHEST-SCORING PAPERS")
    print(f"{'='*80}")

    top10 = master_df.nlargest(10, 'review_score')
    for idx, row in top10.iterrows():
        # Handle missing/NaN titles
        if pd.isna(row['title']):
            title_short = "(title not available)"
        elif hasattr(row['title'], '__len__'):
            title_short = row['title'][:70] if len(row['title']) > 70 else row['title']
        else:
            title_short = str(row['title'])[:70]

        print(f"\n{row['review_score']:.2f} - PMID {row['pmid']}")
        print(f"  {title_short}...")
        if 'setfit_confidence' in row and pd.notna(row['setfit_confidence']):
            print(f"  Agent {row['agent']} | SetFit: {row['setfit_confidence']:.3f} | Ling: {row['ling_score']}")
        else:
            print(f"  Agent {row['agent']}")

    # Bottom papers (false positives)
    print(f"\n{'='*80}")
    print("TOP 10 FALSE POSITIVES (High SetFit, Low Review)")
    print(f"{'='*80}")

    # Find papers where SetFit was confident but review was low
    if 'setfit_confidence' in master_df.columns:
        master_df['false_positive_score'] = master_df['setfit_confidence'] - master_df['review_score']
        false_positives = master_df.nlargest(10, 'false_positive_score')

        for idx, row in false_positives.iterrows():
            # Handle missing/NaN titles
            if pd.isna(row['title']):
                title_short = "(title not available)"
            elif hasattr(row['title'], '__len__'):
                title_short = row['title'][:70] if len(row['title']) > 70 else row['title']
            else:
                title_short = str(row['title'])[:70]

            print(f"\nSetFit: {row['setfit_confidence']:.3f} | Review: {row['review_score']:.2f} | Diff: {row['false_positive_score']:.2f}")
            print(f"  PMID {row['pmid']}")
            print(f"  {title_short}...")
            if 'notes' in row and pd.notna(row['notes']):
                notes_short = row['notes'][:100] if len(str(row['notes'])) > 100 else row['notes']
                print(f"  Note: {notes_short}...")

    # Coverage analysis
    print(f"\n{'='*80}")
    print("COVERAGE ANALYSIS")
    print(f"{'='*80}")

    print(f"\nSetFit Total Introductions: 7,945")
    print(f"Papers Reviewed: {len(master_df):,}")
    print(f"Coverage: {100*len(master_df)/7945:.1f}%")
    print(f"\nEstimated High-Quality Bioresources in Full Dataset:")
    print(f"  Based on {100*high/len(master_df):.1f}% high-confidence rate")
    print(f"  Estimated total: {int(7945 * high/len(master_df)):,} papers")

    print(f"\n{'='*80}")
    print("✓ AGGREGATION COMPLETE")
    print(f"{'='*80}")
    print("\nFiles created:")
    print("  1. ALL_AGENTS_MASTER_RESULTS.csv - All 3,600 scored papers")
    print("  2. ALL_AGENTS_STATISTICS.csv - Per-agent statistics")
    print("  3. ALL_AGENTS_COMPREHENSIVE_SUMMARY.md - Detailed analysis report")
    print("\nNext steps:")
    print("  1. Review top-scoring papers for inventory inclusion")
    print("  2. Analyze false positives to improve SetFit")
    print("  3. Use agent scores as training data for SetFit v2")

else:
    print("\n✗ No agent results found!")
    print("Make sure agent*_scored_results.csv files exist in current directory")
