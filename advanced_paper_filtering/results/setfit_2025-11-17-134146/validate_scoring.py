#!/usr/bin/env python3
"""
Validation script to examine specific examples and generate additional insights
"""

import pandas as pd

def main():
    # Load both files
    results = pd.read_csv("/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/agent7_scored_results.csv")
    original = pd.read_csv("/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/review_agent7_sample.csv")

    # Merge to get abstracts
    merged = results.merge(original[['pmid', 'abstract']], on='pmid', how='left')

    print("="*80)
    print("DETAILED VALIDATION ANALYSIS")
    print("="*80)

    # Top 10 highest scoring papers
    print("\n\n" + "="*80)
    print("TOP 10 HIGHEST SCORING PAPERS (Most Likely Bioresource Introductions)")
    print("="*80)

    top_papers = merged.nlargest(10, 'review_score')
    for idx, row in top_papers.iterrows():
        print(f"\n{'-'*80}")
        print(f"RANK: #{list(top_papers.index).index(idx) + 1}")
        print(f"PMID: {row['pmid']}")
        print(f"Review Score: {row['review_score']:.3f}")
        print(f"SetFit Confidence: {row['setfit_confidence']:.3f}")
        print(f"Linguistic Score: {row['ling_score']}")
        print(f"Title: {row['title']}")
        print(f"Notes: {row['notes']}")
        if pd.notna(row['abstract']) and row['abstract']:
            abstract_preview = row['abstract'][:300] + "..." if len(str(row['abstract'])) > 300 else row['abstract']
            print(f"Abstract Preview: {abstract_preview}")

    # Bottom 10 lowest scoring papers (excluding no abstract)
    print("\n\n" + "="*80)
    print("BOTTOM 10 LOWEST SCORING PAPERS (Least Likely Bioresource Introductions)")
    print("="*80)

    bottom_papers = merged[~merged['notes'].str.contains('NO_ABSTRACT', na=False)].nsmallest(10, 'review_score')
    for idx, row in bottom_papers.iterrows():
        print(f"\n{'-'*80}")
        print(f"PMID: {row['pmid']}")
        print(f"Review Score: {row['review_score']:.3f}")
        print(f"SetFit Confidence: {row['setfit_confidence']:.3f}")
        print(f"Linguistic Score: {row['ling_score']}")
        print(f"Title: {row['title']}")
        print(f"Notes: {row['notes']}")
        if pd.notna(row['abstract']) and row['abstract']:
            abstract_preview = row['abstract'][:300] + "..." if len(str(row['abstract'])) > 300 else row['abstract']
            print(f"Abstract Preview: {abstract_preview}")

    # Biggest disagreements - SetFit high, Review low
    print("\n\n" + "="*80)
    print("BIGGEST DISAGREEMENTS: SetFit HIGH (≥0.70) but Review LOW (<0.3)")
    print("="*80)

    disagreements = merged[
        (merged['setfit_confidence'] >= 0.70) &
        (merged['review_score'] < 0.3)
    ].sort_values('setfit_confidence', ascending=False).head(10)

    for idx, row in disagreements.iterrows():
        print(f"\n{'-'*80}")
        print(f"PMID: {row['pmid']}")
        print(f"SetFit: {row['setfit_confidence']:.3f} | Review: {row['review_score']:.3f} | Diff: {row['setfit_confidence'] - row['review_score']:.3f}")
        print(f"Title: {row['title']}")
        print(f"Notes: {row['notes']}")
        if pd.notna(row['abstract']) and row['abstract']:
            abstract_preview = row['abstract'][:300] + "..." if len(str(row['abstract'])) > 300 else row['abstract']
            print(f"Abstract Preview: {abstract_preview}")

    # Interesting cases - SetFit low, Review high (potential false negatives)
    print("\n\n" + "="*80)
    print("POTENTIAL MISSED OPPORTUNITIES: SetFit LOW (<0.60) but Review HIGH (≥0.7)")
    print("="*80)

    missed = merged[
        (merged['setfit_confidence'] < 0.60) &
        (merged['review_score'] >= 0.7)
    ].sort_values('review_score', ascending=False)

    if len(missed) > 0:
        for idx, row in missed.iterrows():
            print(f"\n{'-'*80}")
            print(f"PMID: {row['pmid']}")
            print(f"SetFit: {row['setfit_confidence']:.3f} | Review: {row['review_score']:.3f}")
            print(f"Title: {row['title']}")
            print(f"Notes: {row['notes']}")
            if pd.notna(row['abstract']) and row['abstract']:
                abstract_preview = row['abstract'][:300] + "..." if len(str(row['abstract'])) > 300 else row['abstract']
                print(f"Abstract Preview: {abstract_preview}")
    else:
        print("\nNo cases found where SetFit <0.60 and Review ≥0.7")

    # Score distribution analysis
    print("\n\n" + "="*80)
    print("SCORE DISTRIBUTION DETAILS")
    print("="*80)

    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    merged['score_bin'] = pd.cut(merged['review_score'], bins=bins, include_lowest=True)
    dist = merged.groupby('score_bin', observed=True).size()

    print("\nReview Score Distribution:")
    for bin_range, count in dist.items():
        bar = "█" * int(count / 5)  # Scale for display
        print(f"{bin_range}: {bar} ({count} papers)")

    # Note patterns analysis
    print("\n\n" + "="*80)
    print("NOTE PATTERNS ANALYSIS")
    print("="*80)

    note_patterns = [
        ('INTRO_LANG', 'Strong introduction language'),
        ('RESOURCE:database', 'Database resource type'),
        ('RESOURCE:tool', 'Tool resource type'),
        ('RESOURCE:server', 'Server resource type'),
        ('URL_PRESENT', 'Contains URL'),
        ('USAGE_LANG', 'Usage language (negative)'),
        ('BIO_FOCUS', 'Biological focus (negative)'),
        ('LIKELY_BIORESOURCE', 'Final: Likely bioresource'),
        ('BORDERLINE', 'Final: Borderline'),
        ('NOT_BIORESOURCE', 'Final: Not bioresource'),
    ]

    print("\nPattern Frequency:")
    for pattern, description in note_patterns:
        count = merged['notes'].str.contains(pattern, na=False).sum()
        pct = count / len(merged) * 100
        print(f"  {description:40s}: {count:3d} papers ({pct:5.1f}%)")

    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
