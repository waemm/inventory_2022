#!/usr/bin/env python3
"""
Additional pattern analysis for Agent 11 evaluation
"""

import pandas as pd
import numpy as np

def main():
    print("Loading scored results...")
    df = pd.read_csv('agent11_scored_results.csv')

    print("\n" + "="*80)
    print("PATTERN ANALYSIS - Review Agent 11")
    print("="*80)

    # Analysis 1: SetFit confidence bands
    print("\n1. SETFIT CONFIDENCE BANDS vs REVIEW SCORES")
    print("-" * 60)

    bins = [0.5, 0.6, 0.65, 0.7, 0.75, 0.8]
    labels = ['0.5-0.6', '0.6-0.65', '0.65-0.7', '0.7-0.75', '0.75-0.8']

    df['setfit_band'] = pd.cut(df['setfit_confidence'], bins=bins, labels=labels)

    band_analysis = df.groupby('setfit_band', observed=True).agg({
        'review_score': ['mean', 'std', 'count'],
        'pmid': 'count'
    }).round(3)

    print(band_analysis)

    # Analysis 2: Linguistic score impact
    print("\n\n2. LINGUISTIC SCORE IMPACT")
    print("-" * 60)

    ling_analysis = df.groupby('ling_score').agg({
        'review_score': ['mean', 'std', 'count'],
        'setfit_confidence': ['mean', 'std']
    }).round(3)

    print(ling_analysis)

    # Analysis 3: Disagreement cases
    print("\n\n3. MAJOR DISAGREEMENTS (SetFit vs Review Score)")
    print("-" * 60)

    # High SetFit, Low Review
    print("\na) High SetFit (≥0.7), Low Review (<0.3):")
    high_setfit_low_review = df[(df['setfit_confidence'] >= 0.7) & (df['review_score'] < 0.3)]
    print(f"   Count: {len(high_setfit_low_review)}")
    if len(high_setfit_low_review) > 0:
        print("\n   Examples:")
        for idx, row in high_setfit_low_review.head(5).iterrows():
            print(f"   - PMID {row['pmid']}: {row['title'][:70]}...")
            print(f"     SetFit: {row['setfit_confidence']:.3f}, Review: {row['review_score']:.3f}")
            print(f"     Note: {row['notes'][:80]}...")
            print()

    # Low SetFit, High Review
    print("\nb) Low SetFit (<0.65), High Review (≥0.7):")
    low_setfit_high_review = df[(df['setfit_confidence'] < 0.65) & (df['review_score'] >= 0.7)]
    print(f"   Count: {len(low_setfit_high_review)}")
    if len(low_setfit_high_review) > 0:
        print("\n   Examples:")
        for idx, row in low_setfit_high_review.head(5).iterrows():
            print(f"   - PMID {row['pmid']}: {row['title'][:70]}...")
            print(f"     SetFit: {row['setfit_confidence']:.3f}, Review: {row['review_score']:.3f}")
            print(f"     Note: {row['notes'][:80]}...")
            print()

    # Analysis 4: Perfect agreement
    print("\n4. PERFECT AGREEMENT ANALYSIS")
    print("-" * 60)

    # Both high
    both_high = df[(df['setfit_confidence'] >= 0.7) & (df['review_score'] >= 0.7)]
    print(f"\nBoth high (SetFit≥0.7, Review≥0.7): {len(both_high)} papers ({len(both_high)/len(df)*100:.1f}%)")
    print(f"  Mean SetFit: {both_high['setfit_confidence'].mean():.3f}")
    print(f"  Mean Review: {both_high['review_score'].mean():.3f}")

    # Both medium-low
    both_low = df[(df['setfit_confidence'] < 0.65) & (df['review_score'] < 0.5)]
    print(f"\nBoth low (SetFit<0.65, Review<0.5): {len(both_low)} papers ({len(both_low)/len(df)*100:.1f}%)")
    print(f"  Mean SetFit: {both_low['setfit_confidence'].mean():.3f}")
    print(f"  Mean Review: {both_low['review_score'].mean():.3f}")

    # Analysis 5: Score distribution
    print("\n\n5. REVIEW SCORE DISTRIBUTION")
    print("-" * 60)

    score_bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    score_labels = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']

    df['review_bin'] = pd.cut(df['review_score'], bins=score_bins, labels=score_labels)

    dist = df['review_bin'].value_counts(sort=False)
    print("\nReview Score Range | Count | Percentage")
    print("-" * 60)
    for label in score_labels:
        count = dist.get(label, 0)
        pct = count / len(df) * 100
        print(f"{label:18} | {count:5} | {pct:5.1f}% {'█' * int(pct/2)}")

    # Analysis 6: Top features in high-scoring papers
    print("\n\n6. COMMON PATTERNS IN HIGH-SCORING PAPERS (≥0.9)")
    print("-" * 60)

    high_scorers = df[df['review_score'] >= 0.9]
    print(f"\nTotal high scorers: {len(high_scorers)}")

    # Extract pattern keywords from notes
    patterns = {
        'intro_phrases': 0,
        'resource_in_title': 0,
        'structured_title': 0,
        'has_url': 0,
        'multiple_resource_types': 0,
        'high_ling_score': 0
    }

    for notes in high_scorers['notes']:
        notes_lower = notes.lower()
        if 'intro phrase' in notes_lower:
            patterns['intro_phrases'] += 1
        if 'resource type in title' in notes_lower:
            patterns['resource_in_title'] += 1
        if 'structured title' in notes_lower:
            patterns['structured_title'] += 1
        if 'url' in notes_lower:
            patterns['has_url'] += 1
        if 'multiple resource types' in notes_lower:
            patterns['multiple_resource_types'] += 1
        if 'ling_score' in notes_lower:
            patterns['high_ling_score'] += 1

    print("\nFeature Prevalence in High-Scoring Papers:")
    for feature, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(high_scorers) * 100
        print(f"  {feature:30}: {count:3}/{len(high_scorers)} ({pct:5.1f}%)")

    # Analysis 7: Correlation matrix
    print("\n\n7. CORRELATION MATRIX")
    print("-" * 60)

    corr_cols = ['setfit_confidence', 'ling_score', 'review_score']
    corr_matrix = df[corr_cols].corr()
    print("\n", corr_matrix.round(3))

    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80)

if __name__ == '__main__':
    main()
