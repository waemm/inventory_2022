#!/usr/bin/env python3
"""
Review Agent 9 - Systematic scoring of 400 SetFit-classified papers
Evaluates bioresource introduction likelihood for each paper
"""

import pandas as pd
import re
from typing import Tuple
import numpy as np

def score_bioresource_likelihood(row: pd.Series) -> Tuple[float, str]:
    """
    Score a paper 0.0-1.0 on bioresource introduction likelihood

    Returns:
        (score, notes) where score is 0.0-1.0 and notes explain the decision
    """
    title = str(row['title']).lower()
    abstract = str(row['abstract']).lower()
    ling_score = row['ling_score']

    # Strong positive indicators (HIGH confidence bioresource)
    strong_intro_patterns = [
        r'\bwe present\b',
        r'\bwe developed\b',
        r'\bwe describe\b',
        r'\bwe introduce\b',
        r'\bhere we present\b',
        r'\bhere we describe\b',
        r'\bhere we report\b',
        r'\bhere, we present\b',
        r'\bhere, we describe\b',
        r'\bwe have developed\b',
        r'\bwe have created\b',
        r'\bwe have constructed\b',
        r'\bwe created\b',
        r'\bwe constructed\b',
        r'\bwe built\b',
        r'\bwe report\b',
        r'\bwe designed\b',
    ]

    # Resource type keywords in title (strong signal)
    title_resource_keywords = [
        r'\bdatabase\b',
        r'\bserver\b',
        r'\btool\b',
        r'\brepository\b',
        r'\bplatform\b',
        r'\bresource\b',
        r'\bportal\b',
        r'\bsoftware\b',
        r'\bweb.?server\b',
        r'\bweb.?tool\b',
        r'\bpipeline\b',
        r'\bworkflow\b',
    ]

    # Version numbers suggest resource updates (positive)
    version_pattern = r'\b(version|v\.?)\s*\d+\.?\d*\b|\b\d+\.?\d*:\s*(a|an|the)\s+(database|server|tool|resource)'

    # Negative indicators (NOT a bioresource introduction)
    negative_patterns = [
        r'\bwe used\b',
        r'\bwe applied\b',
        r'\bwe analyzed\b',
        r'\bwe investigated\b',
        r'\bwe evaluated\b',
        r'\bwe assessed\b',
        r'\bwe examined\b',
        r'\bwe tested\b',
        r'\bwe performed\b',
        r'\bwe conducted\b',
        r'\busing\b.*\b(database|tool|server)\b',
        r'\bapplication of\b',
        r'\breview\b.*\b(of|on)\b',
        r'\bcase study\b',
        r'\bclinical trial\b',
        r'\bmeta.?analysis\b',
    ]

    # URL pattern (weak positive)
    url_pattern = r'https?://|www\.|\.org/|\.edu/|\.gov/'

    # Available at pattern (moderate positive)
    available_pattern = r'(freely )?available (at|from)|can be (accessed|downloaded|obtained)'

    # Implementation keywords (moderate positive)
    impl_keywords = [
        r'\bimplementation\b',
        r'\bimplemented\b',
        r'\bdeployment\b',
        r'\bdeployed\b',
    ]

    # Calculate feature scores
    has_strong_intro = any(re.search(p, abstract) for p in strong_intro_patterns)
    has_title_resource = any(re.search(p, title) for p in title_resource_keywords)
    has_version = bool(re.search(version_pattern, title + ' ' + abstract))
    has_negatives = any(re.search(p, abstract) for p in negative_patterns)
    has_url = bool(re.search(url_pattern, abstract))
    has_available = bool(re.search(available_pattern, abstract))
    has_impl = any(re.search(p, abstract) for p in impl_keywords)

    # Count introduction patterns
    intro_count = sum(1 for p in strong_intro_patterns if re.search(p, abstract))

    # Scoring logic
    score = 0.5  # Start at neutral
    notes_parts = []

    # STRONG POSITIVE signals (high weight)
    if has_strong_intro and has_title_resource:
        score = 0.95
        notes_parts.append("Strong intro pattern + resource in title")
    elif has_strong_intro and intro_count >= 2:
        score = 0.90
        notes_parts.append("Multiple strong intro patterns")
    elif has_strong_intro and ling_score >= 2:
        score = 0.85
        notes_parts.append("Strong intro pattern + high ling_score")
    elif has_strong_intro:
        score = 0.80
        notes_parts.append("Strong intro pattern detected")

    # MODERATE POSITIVE signals
    elif has_title_resource and has_version:
        score = 0.75
        notes_parts.append("Resource in title + version number")
    elif has_title_resource and has_available:
        score = 0.70
        notes_parts.append("Resource in title + availability statement")
    elif has_title_resource and ling_score >= 1:
        score = 0.65
        notes_parts.append("Resource in title + linguistic features")
    elif has_title_resource:
        score = 0.60
        notes_parts.append("Resource keyword in title")

    # WEAK POSITIVE signals
    elif ling_score >= 2 and has_url:
        score = 0.55
        notes_parts.append("High ling_score + URL")
    elif ling_score >= 2:
        score = 0.52
        notes_parts.append("High linguistic score")
    elif has_available and has_url:
        score = 0.50
        notes_parts.append("Availability + URL (borderline)")

    # NEGATIVE adjustments
    if has_negatives and not has_strong_intro:
        score = max(0.0, score - 0.30)
        notes_parts.append("Usage/analysis patterns detected")

    # Special case: very low ling_score
    if ling_score == 0 and not has_strong_intro and not has_title_resource:
        score = min(score, 0.25)
        notes_parts.append("No linguistic features")

    # Check for specific non-resource paper types
    if re.search(r'\breview\b', title) and not re.search(r'\bdatabase\b|\bserver\b|\btool\b', title):
        score = min(score, 0.20)
        notes_parts.append("Review article")

    if re.search(r'\bmeta.?analysis\b', title):
        score = min(score, 0.15)
        notes_parts.append("Meta-analysis")

    if re.search(r'\bclinical trial\b|\bcase report\b', title):
        score = min(score, 0.10)
        notes_parts.append("Clinical study")

    # Ensure score is in valid range
    score = max(0.0, min(1.0, score))

    # Create notes
    notes = "; ".join(notes_parts) if notes_parts else "No clear signals"

    return score, notes


def main():
    """Main scoring function"""
    print("Review Agent 9 - Starting systematic review of 400 papers...")

    # Load the data
    input_file = "/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/review_agent9_sample.csv"
    output_file = "/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/agent9_scored_results.csv"
    summary_file = "/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/agent9_summary.md"

    print(f"Loading data from: {input_file}")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} papers")

    # Score each paper
    print("\nScoring papers...")
    scores = []
    notes_list = []

    for idx, row in df.iterrows():
        score, notes = score_bioresource_likelihood(row)
        scores.append(score)
        notes_list.append(notes)

        if (idx + 1) % 50 == 0:
            print(f"  Processed {idx + 1}/{len(df)} papers...")

    # Add scores to dataframe
    df['review_score'] = scores
    df['notes'] = notes_list

    # Create output with requested columns
    output_df = df[['pmid', 'title', 'setfit_confidence', 'ling_score', 'review_score', 'notes']]

    # Save results
    print(f"\nSaving scored results to: {output_file}")
    output_df.to_csv(output_file, index=False)

    # Generate summary statistics
    print("\nGenerating summary statistics...")

    # Calculate correlations
    corr_setfit = df['setfit_confidence'].corr(df['review_score'])
    corr_ling = df['ling_score'].corr(df['review_score'])

    # Score distribution
    score_bins = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
    score_labels = ['Very Low (0-0.3)', 'Low (0.3-0.5)', 'Medium (0.5-0.7)', 'High (0.7-0.9)', 'Very High (0.9-1.0)']
    df['score_category'] = pd.cut(df['review_score'], bins=score_bins, labels=score_labels, include_lowest=True)

    # SetFit confidence bins
    setfit_bins = [0, 0.55, 0.65, 0.75, 1.0]
    setfit_labels = ['Low (<0.55)', 'Medium (0.55-0.65)', 'High (0.65-0.75)', 'Very High (>0.75)']
    df['setfit_category'] = pd.cut(df['setfit_confidence'], bins=setfit_bins, labels=setfit_labels, include_lowest=True)

    # Generate summary markdown
    with open(summary_file, 'w') as f:
        f.write("# Review Agent 9 - Summary Report\n\n")
        f.write(f"**Date**: 2025-11-17\n")
        f.write(f"**Papers Reviewed**: {len(df)}\n\n")

        f.write("## Overall Statistics\n\n")
        f.write(f"- **Mean Review Score**: {df['review_score'].mean():.3f}\n")
        f.write(f"- **Median Review Score**: {df['review_score'].median():.3f}\n")
        f.write(f"- **Std Dev**: {df['review_score'].std():.3f}\n")
        f.write(f"- **Min Score**: {df['review_score'].min():.3f}\n")
        f.write(f"- **Max Score**: {df['review_score'].max():.3f}\n\n")

        f.write("## Score Distribution\n\n")
        score_dist = df['score_category'].value_counts().sort_index()
        for category, count in score_dist.items():
            pct = (count / len(df)) * 100
            f.write(f"- **{category}**: {count} papers ({pct:.1f}%)\n")

        f.write("\n## SetFit Quality Evaluation\n\n")
        f.write(f"**Correlation between SetFit confidence and Review score**: {corr_setfit:.3f}\n\n")

        if corr_setfit > 0.6:
            assessment = "STRONG - SetFit confidence is a good predictor of bioresource likelihood"
        elif corr_setfit > 0.4:
            assessment = "MODERATE - SetFit shows reasonable alignment with human review"
        elif corr_setfit > 0.2:
            assessment = "WEAK - SetFit confidence has limited predictive value"
        else:
            assessment = "POOR - SetFit confidence does not correlate well with actual bioresource likelihood"

        f.write(f"**Assessment**: {assessment}\n\n")

        f.write("### SetFit Confidence vs Review Score Breakdown\n\n")
        f.write("| SetFit Category | Count | Mean Review Score | % High Scoring (>0.7) |\n")
        f.write("|-----------------|-------|-------------------|------------------------|\n")

        for category in setfit_labels:
            subset = df[df['setfit_category'] == category]
            if len(subset) > 0:
                mean_score = subset['review_score'].mean()
                high_pct = (subset['review_score'] > 0.7).sum() / len(subset) * 100
                f.write(f"| {category} | {len(subset)} | {mean_score:.3f} | {high_pct:.1f}% |\n")

        f.write("\n## Linguistic Features Evaluation\n\n")
        f.write(f"**Correlation between ling_score and Review score**: {corr_ling:.3f}\n\n")

        f.write("### Linguistic Score Breakdown\n\n")
        f.write("| Ling Score | Count | Mean Review Score | % High Scoring (>0.7) |\n")
        f.write("|------------|-------|-------------------|------------------------|\n")

        for ling_val in sorted(df['ling_score'].unique()):
            subset = df[df['ling_score'] == ling_val]
            mean_score = subset['review_score'].mean()
            high_pct = (subset['review_score'] > 0.7).sum() / len(subset) * 100
            f.write(f"| {int(ling_val)} | {len(subset)} | {mean_score:.3f} | {high_pct:.1f}% |\n")

        f.write("\n## High Confidence Bioresources (Score >= 0.8)\n\n")
        high_conf = df[df['review_score'] >= 0.8].sort_values('review_score', ascending=False)
        f.write(f"**Count**: {len(high_conf)} papers\n\n")

        if len(high_conf) > 0:
            f.write("### Top 20 High Confidence Papers\n\n")
            for idx, (_, row) in enumerate(high_conf.head(20).iterrows(), 1):
                f.write(f"{idx}. **PMID {row['pmid']}** (Score: {row['review_score']:.2f})\n")
                f.write(f"   - Title: {row['title']}\n")
                f.write(f"   - SetFit: {row['setfit_confidence']:.3f}, Ling: {row['ling_score']}\n")
                f.write(f"   - Notes: {row['notes']}\n\n")

        f.write("\n## Low Confidence Papers (Score <= 0.2)\n\n")
        low_conf = df[df['review_score'] <= 0.2].sort_values('review_score')
        f.write(f"**Count**: {len(low_conf)} papers\n\n")

        if len(low_conf) > 0:
            f.write("### Examples of Low Confidence Papers\n\n")
            for idx, (_, row) in enumerate(low_conf.head(10).iterrows(), 1):
                f.write(f"{idx}. **PMID {row['pmid']}** (Score: {row['review_score']:.2f})\n")
                f.write(f"   - Title: {row['title']}\n")
                f.write(f"   - SetFit: {row['setfit_confidence']:.3f}, Ling: {row['ling_score']}\n")
                f.write(f"   - Notes: {row['notes']}\n\n")

        f.write("\n## SetFit Misclassifications\n\n")

        # High SetFit confidence but low review score
        false_positives = df[(df['setfit_confidence'] > 0.7) & (df['review_score'] < 0.3)]
        f.write(f"### Potential False Positives (High SetFit, Low Review Score)\n")
        f.write(f"**Count**: {len(false_positives)}\n\n")

        if len(false_positives) > 0:
            for idx, (_, row) in enumerate(false_positives.head(10).iterrows(), 1):
                f.write(f"{idx}. **PMID {row['pmid']}** (SetFit: {row['setfit_confidence']:.3f}, Review: {row['review_score']:.2f})\n")
                f.write(f"   - {row['title']}\n")
                f.write(f"   - Notes: {row['notes']}\n\n")

        # Low SetFit confidence but high review score
        false_negatives = df[(df['setfit_confidence'] < 0.6) & (df['review_score'] > 0.7)]
        f.write(f"### Potential False Negatives (Low SetFit, High Review Score)\n")
        f.write(f"**Count**: {len(false_negatives)}\n\n")

        if len(false_negatives) > 0:
            for idx, (_, row) in enumerate(false_negatives.head(10).iterrows(), 1):
                f.write(f"{idx}. **PMID {row['pmid']}** (SetFit: {row['setfit_confidence']:.3f}, Review: {row['review_score']:.2f})\n")
                f.write(f"   - {row['title']}\n")
                f.write(f"   - Notes: {row['notes']}\n\n")

        f.write("\n## Recommendations\n\n")

        if corr_setfit > 0.5:
            f.write("1. **SetFit Performance**: Good correlation suggests SetFit is effective. Consider using confidence threshold of 0.65+ for high precision.\n")
        else:
            f.write("1. **SetFit Performance**: Moderate correlation suggests room for improvement. Review false positives for retraining.\n")

        f.write(f"2. **Linguistic Features**: Correlation of {corr_ling:.3f} shows linguistic patterns are {'highly' if corr_ling > 0.5 else 'moderately'} useful.\n")
        f.write(f"3. **High Confidence Threshold**: Papers with review score >= 0.8 ({len(high_conf)} papers) are strong bioresource candidates.\n")
        f.write(f"4. **Manual Review Priority**: Focus on papers with scores 0.5-0.7 ({len(df[(df['review_score'] >= 0.5) & (df['review_score'] < 0.7)])} papers) for final classification.\n")

    print(f"Summary saved to: {summary_file}")
    print("\n✓ Review Agent 9 scoring complete!")
    print(f"\nResults: {output_file}")
    print(f"Summary: {summary_file}")
    print(f"\nQuick Stats:")
    print(f"  - Mean score: {df['review_score'].mean():.3f}")
    print(f"  - High confidence (>0.8): {len(df[df['review_score'] >= 0.8])} papers")
    print(f"  - Low confidence (<0.3): {len(df[df['review_score'] < 0.3])} papers")
    print(f"  - SetFit correlation: {corr_setfit:.3f}")


if __name__ == "__main__":
    main()
