#!/usr/bin/env python3
"""
Agent 2 Scoring Script for SetFit Bioresource Classification Review
Scores papers 0-1 on likelihood of introducing new bioresource
"""

import pandas as pd
import csv
import re

def score_paper(row):
    """
    Score a single paper for bioresource introduction likelihood (0-1 scale)

    Criteria:
    - Strong indicators (0.8-1.0): Database/tool/resource with URL, downloadable software,
      new repository, physical resource collection
    - Moderate indicators (0.5-0.8): Computational tools, protocols, methods with sharing intent,
      community resources, knowledgebases
    - Weak indicators (0.2-0.5): Methods papers, protocols, potential resources
    - No resource (0-0.2): Pure research, reviews, theoretical work
    """

    title = str(row['title']).lower()
    abstract = str(row['abstract']).lower()
    combined = title + " " + abstract

    # Initialize score
    score = 0.0
    reasons = []

    # STRONG INDICATORS (base score 0.8-1.0)
    # Databases and repositories with URLs
    if row['ling_has_url']:
        if any(keyword in combined for keyword in [
            'database', 'repository', 'web server', 'online resource',
            'freely available', 'publicly available', 'open access',
            'web portal', 'web-based', 'web application'
        ]):
            score = max(score, 0.85)
            reasons.append("URL + database/repository language")

    # Explicit resource introduction language
    resource_intro_patterns = [
        r'we (?:have )?(?:developed|created|established|built|present|introduce)',
        r'here we (?:describe|present|report)',
        r'new (?:database|resource|tool|platform|repository)',
        r'first.*(?:database|resource|tool|platform)'
    ]

    for pattern in resource_intro_patterns:
        if re.search(pattern, combined):
            if any(keyword in combined for keyword in ['database', 'repository', 'resource', 'web', 'available']):
                score = max(score, 0.80)
                reasons.append(f"Resource introduction pattern: {pattern[:30]}")
                break

    # Physical resources
    if any(keyword in combined for keyword in [
        'collection of', 'biobank', 'cell line', 'strain collection',
        'model organism', 'mutant library'
    ]) and 'available' in combined:
        score = max(score, 0.75)
        reasons.append("Physical resource collection")

    # Software/tools with implementation keywords
    if row['ling_impl_keywords'] >= 1:
        if any(keyword in combined for keyword in [
            'software', 'package', 'pipeline', 'toolkit', 'program',
            'implementation', 'algorithm', 'method'
        ]):
            score = max(score, 0.70)
            reasons.append(f"Implementation keywords ({row['ling_impl_keywords']})")

    # MODERATE INDICATORS (0.5-0.7)
    # Knowledgebases and curated resources
    if any(keyword in combined for keyword in [
        'knowledgebase', 'knowledge base', 'curated', 'curation',
        'annotation', 'catalog', 'compendium', 'atlas'
    ]):
        if any(keyword in combined for keyword in ['database', 'resource', 'web']):
            score = max(score, 0.65)
            reasons.append("Knowledgebase/curated resource")

    # Protocols and methods with sharing
    if row['ling_usage_keywords'] >= 1:
        if any(keyword in combined for keyword in [
            'protocol', 'workflow', 'framework', 'platform', 'system'
        ]):
            score = max(score, 0.60)
            reasons.append(f"Usage keywords + method ({row['ling_usage_keywords']})")

    # Update/version language (existing resource)
    if any(keyword in combined for keyword in [
        'update', 'new version', 'release', 'v2', 'v3', 'improved'
    ]) and 'database' in combined:
        score = max(score, 0.75)
        reasons.append("Database update/new version")

    # WEAK INDICATORS (0.2-0.5)
    # Methods papers without clear resource
    if any(keyword in combined for keyword in [
        'method', 'approach', 'technique', 'strategy'
    ]) and not any(keyword in combined for keyword in ['database', 'repository', 'web']):
        score = max(score, 0.30)
        reasons.append("Methods paper (no clear resource)")

    # Analysis tools without clear availability
    if any(keyword in combined for keyword in [
        'analysis', 'prediction', 'classification', 'detection'
    ]) and 'tool' in combined:
        score = max(score, 0.40)
        reasons.append("Analysis tool mention")

    # NEGATIVE INDICATORS (reduce score)
    # Pure research/study
    if any(keyword in combined for keyword in [
        'we studied', 'we investigated', 'we found', 'we show that',
        'our results', 'our findings', 'this study'
    ]) and not any(keyword in combined for keyword in ['database', 'tool', 'resource', 'available']):
        score = min(score, 0.20)
        reasons.append("Pure research study")

    # Reviews and surveys
    if any(keyword in combined for keyword in [
        'review', 'survey', 'overview', 'perspective'
    ]) and 'database' not in combined:
        score = min(score, 0.15)
        reasons.append("Review/survey paper")

    # Case reports, clinical studies
    if any(keyword in combined for keyword in [
        'case report', 'clinical trial', 'patient', 'cohort study'
    ]):
        score = min(score, 0.10)
        reasons.append("Clinical/case study")

    # Linguistic score consideration
    if row['ling_score'] > 0:
        # Boost if high linguistic score
        score = max(score, min(0.70, score + row['ling_score'] * 0.15))
        reasons.append(f"Linguistic score boost: {row['ling_score']:.2f}")

    # SetFit confidence consideration (weak signal)
    if row['setfit_confidence'] > 0.7:
        score = max(score, 0.30)  # Minimum floor for high confidence

    # Cap at 1.0
    score = min(1.0, score)

    # Round to 2 decimals
    score = round(score, 2)

    return score, "; ".join(reasons) if reasons else "No strong indicators"

def main():
    print("Loading Agent 2 sample file...")
    df = pd.read_csv('/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/review_agent2_sample.csv')

    print(f"Processing {len(df)} papers...")

    scores = []
    rationales = []

    for idx, row in df.iterrows():
        score, rationale = score_paper(row)
        scores.append(score)
        rationales.append(rationale)

        if (idx + 1) % 20 == 0:
            print(f"  Processed {idx + 1}/{len(df)} papers...")

    # Add to dataframe
    df['agent2_score'] = scores
    df['agent2_rationale'] = rationales

    # Save scored results
    output_file = '/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/agent2_scored_results.csv'
    df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
    print(f"\nSaved scored results to: {output_file}")

    # Generate summary statistics
    print("\n" + "="*60)
    print("AGENT 2 SCORING SUMMARY")
    print("="*60)

    print(f"\nTotal papers scored: {len(df)}")
    print(f"Mean score: {df['agent2_score'].mean():.3f}")
    print(f"Median score: {df['agent2_score'].median():.3f}")
    print(f"Std deviation: {df['agent2_score'].std():.3f}")
    print(f"Min score: {df['agent2_score'].min():.3f}")
    print(f"Max score: {df['agent2_score'].max():.3f}")

    print("\nScore distribution:")
    print(f"  0.00-0.20 (Very unlikely): {len(df[df['agent2_score'] <= 0.20])}")
    print(f"  0.21-0.40 (Unlikely): {len(df[(df['agent2_score'] > 0.20) & (df['agent2_score'] <= 0.40)])}")
    print(f"  0.41-0.60 (Moderate): {len(df[(df['agent2_score'] > 0.40) & (df['agent2_score'] <= 0.60)])}")
    print(f"  0.61-0.80 (Likely): {len(df[(df['agent2_score'] > 0.60) & (df['agent2_score'] <= 0.80)])}")
    print(f"  0.81-1.00 (Very likely): {len(df[df['agent2_score'] > 0.80])}")

    # Top 10 highest scores
    print("\n" + "-"*60)
    print("TOP 10 HIGHEST SCORING PAPERS:")
    print("-"*60)
    top10 = df.nlargest(10, 'agent2_score')[['pmid', 'title', 'agent2_score', 'agent2_rationale']]
    for idx, row in top10.iterrows():
        print(f"\nPMID {row['pmid']} - Score: {row['agent2_score']:.2f}")
        print(f"Title: {row['title'][:80]}...")
        print(f"Rationale: {row['agent2_rationale']}")

    # Bottom 10 lowest scores
    print("\n" + "-"*60)
    print("BOTTOM 10 LOWEST SCORING PAPERS:")
    print("-"*60)
    bottom10 = df.nsmallest(10, 'agent2_score')[['pmid', 'title', 'agent2_score', 'agent2_rationale']]
    for idx, row in bottom10.iterrows():
        print(f"\nPMID {row['pmid']} - Score: {row['agent2_score']:.2f}")
        print(f"Title: {row['title'][:80]}...")
        print(f"Rationale: {row['agent2_rationale']}")

    # Comparison with linguistic and SetFit scores
    print("\n" + "="*60)
    print("COMPARISON WITH OTHER SCORES")
    print("="*60)

    print(f"\nCorrelation with linguistic score: {df['agent2_score'].corr(df['ling_score']):.3f}")
    print(f"Correlation with SetFit confidence: {df['agent2_score'].corr(df['setfit_confidence']):.3f}")

    # Papers with high linguistic score but low agent score
    high_ling_low_agent = df[(df['ling_score'] > 0.5) & (df['agent2_score'] < 0.3)]
    print(f"\nPapers with high linguistic score (>0.5) but low agent score (<0.3): {len(high_ling_low_agent)}")

    # Papers with low linguistic score but high agent score
    low_ling_high_agent = df[(df['ling_score'] < 0.5) & (df['agent2_score'] > 0.7)]
    print(f"Papers with low linguistic score (<0.5) but high agent score (>0.7): {len(low_ling_high_agent)}")

    # Create summary markdown file
    summary_file = '/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/agent2_summary.md'

    with open(summary_file, 'w') as f:
        f.write("# Agent 2 Bioresource Scoring Summary\n\n")
        f.write(f"**Date**: 2025-11-17\n")
        f.write(f"**Papers Scored**: {len(df)}\n\n")

        f.write("## Scoring Methodology\n\n")
        f.write("Each paper was scored on a 0-1 scale based on likelihood of introducing a new bioresource:\n\n")
        f.write("- **0.81-1.00**: Very likely - databases/repositories with URLs, downloadable tools\n")
        f.write("- **0.61-0.80**: Likely - computational tools, curated resources, knowledgebases\n")
        f.write("- **0.41-0.60**: Moderate - protocols, methods, potential resources\n")
        f.write("- **0.21-0.40**: Unlikely - analysis methods, tools without clear availability\n")
        f.write("- **0.00-0.20**: Very unlikely - pure research, reviews, clinical studies\n\n")

        f.write("## Summary Statistics\n\n")
        f.write(f"- **Mean Score**: {df['agent2_score'].mean():.3f}\n")
        f.write(f"- **Median Score**: {df['agent2_score'].median():.3f}\n")
        f.write(f"- **Standard Deviation**: {df['agent2_score'].std():.3f}\n")
        f.write(f"- **Range**: {df['agent2_score'].min():.3f} - {df['agent2_score'].max():.3f}\n\n")

        f.write("## Score Distribution\n\n")
        f.write(f"- **0.00-0.20** (Very unlikely): {len(df[df['agent2_score'] <= 0.20])} papers ({len(df[df['agent2_score'] <= 0.20])/len(df)*100:.1f}%)\n")
        f.write(f"- **0.21-0.40** (Unlikely): {len(df[(df['agent2_score'] > 0.20) & (df['agent2_score'] <= 0.40)])} papers ({len(df[(df['agent2_score'] > 0.20) & (df['agent2_score'] <= 0.40)])/len(df)*100:.1f}%)\n")
        f.write(f"- **0.41-0.60** (Moderate): {len(df[(df['agent2_score'] > 0.40) & (df['agent2_score'] <= 0.60)])} papers ({len(df[(df['agent2_score'] > 0.40) & (df['agent2_score'] <= 0.60)])/len(df)*100:.1f}%)\n")
        f.write(f"- **0.61-0.80** (Likely): {len(df[(df['agent2_score'] > 0.60) & (df['agent2_score'] <= 0.80)])} papers ({len(df[(df['agent2_score'] > 0.60) & (df['agent2_score'] <= 0.80)])/len(df)*100:.1f}%)\n")
        f.write(f"- **0.81-1.00** (Very likely): {len(df[df['agent2_score'] > 0.80])} papers ({len(df[df['agent2_score'] > 0.80])/len(df)*100:.1f}%)\n\n")

        f.write("## Comparison with Other Metrics\n\n")
        f.write(f"- **Correlation with Linguistic Score**: {df['agent2_score'].corr(df['ling_score']):.3f}\n")
        f.write(f"- **Correlation with SetFit Confidence**: {df['agent2_score'].corr(df['setfit_confidence']):.3f}\n\n")

        f.write("## Top 10 Highest Scoring Papers\n\n")
        for idx, row in top10.iterrows():
            f.write(f"### PMID {row['pmid']} - Score: {row['agent2_score']:.2f}\n")
            f.write(f"**Title**: {row['title']}\n\n")
            f.write(f"**Rationale**: {row['agent2_rationale']}\n\n")

        f.write("## Bottom 10 Lowest Scoring Papers\n\n")
        for idx, row in bottom10.iterrows():
            f.write(f"### PMID {row['pmid']} - Score: {row['agent2_score']:.2f}\n")
            f.write(f"**Title**: {row['title']}\n\n")
            f.write(f"**Rationale**: {row['agent2_rationale']}\n\n")

        f.write("## Discrepancy Analysis\n\n")
        f.write(f"### High Linguistic Score but Low Agent Score\n")
        f.write(f"Papers: {len(high_ling_low_agent)}\n\n")
        if len(high_ling_low_agent) > 0:
            for idx, row in high_ling_low_agent.head(5).iterrows():
                f.write(f"- PMID {row['pmid']}: {row['title'][:80]}...\n")
                f.write(f"  - Linguistic: {row['ling_score']:.2f}, Agent2: {row['agent2_score']:.2f}\n")

        f.write(f"\n### Low Linguistic Score but High Agent Score\n")
        f.write(f"Papers: {len(low_ling_high_agent)}\n\n")
        if len(low_ling_high_agent) > 0:
            for idx, row in low_ling_high_agent.head(5).iterrows():
                f.write(f"- PMID {row['pmid']}: {row['title'][:80]}...\n")
                f.write(f"  - Linguistic: {row['ling_score']:.2f}, Agent2: {row['agent2_score']:.2f}\n")

        f.write("\n## Conclusion\n\n")
        f.write("Agent 2 review complete. Scored results saved to `agent2_scored_results.csv`.\n")

    print(f"\nSaved summary to: {summary_file}")
    print("\n" + "="*60)
    print("AGENT 2 SCORING COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
