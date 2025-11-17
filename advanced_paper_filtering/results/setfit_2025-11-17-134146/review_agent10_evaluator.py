#!/usr/bin/env python3
"""
Review Agent 10: Systematic evaluation of SetFit-classified papers
Evaluates 400 papers for bioresource introduction likelihood
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
import json

class BioresourceReviewer:
    """Evaluates papers for bioresource introduction likelihood"""

    def __init__(self):
        # Strong introduction indicators
        self.intro_patterns = [
            r'\bwe present\b',
            r'\bwe developed\b',
            r'\bwe describe\b',
            r'\bwe introduce\b',
            r'\bwe created\b',
            r'\bwe built\b',
            r'\bwe designed\b',
            r'\bwe constructed\b',
            r'\bhere we\b',
            r'\bwe report\b',
            r'\bwe have developed\b',
            r'\bwe have created\b',
            r'\bwe have built\b',
            r'\bis described\b',
            r'\bis presented\b',
            r'\bis introduced\b',
            r'\bhas been developed\b',
            r'\bhas been created\b',
            r'\bhave developed\b',
            r'\bhave created\b',
        ]

        # Resource type indicators
        self.resource_types = [
            r'\bdatabase\b',
            r'\bserver\b',
            r'\btool\b',
            r'\bsoftware\b',
            r'\bwebsite\b',
            r'\bweb.?server\b',
            r'\bplatform\b',
            r'\bresource\b',
            r'\brepository\b',
            r'\bportal\b',
            r'\bapplication\b',
            r'\bpipeline\b',
            r'\bpackage\b',
            r'\btoolbox\b',
            r'\bframework\b',
        ]

        # Strong negative indicators (usage-only papers)
        self.usage_patterns = [
            r'\busing\b.*?\b(database|tool|software)\b',
            r'\bapplied to\b',
            r'\bwas used\b',
            r'\bwere used\b',
            r'\bwe used\b',
            r'\bwe applied\b',
            r'\bwe analyzed\b',
            r'\banalysis of\b.*?\busing\b',
        ]

        # Weak indicators (might be usage or development)
        self.ambiguous_patterns = [
            r'\bimplementation\b',
            r'\bmethod\b',
            r'\bapproach\b',
            r'\balgorithm\b',
        ]

    def score_paper(self, pmid, title, abstract):
        """
        Score a paper 0.0-1.0 for bioresource introduction likelihood
        Returns: (score, notes)
        """
        if pd.isna(abstract) or not abstract or abstract.strip() == '':
            return 0.0, "No abstract available"

        text = (str(title) + " " + str(abstract)).lower()
        notes = []

        # Base score
        score = 0.5

        # Check for introduction patterns
        intro_matches = sum(1 for p in self.intro_patterns if re.search(p, text, re.I))
        if intro_matches > 0:
            score += 0.15 * min(intro_matches, 3)
            notes.append(f"Intro patterns: {intro_matches}")

        # Check for resource type mentions
        resource_matches = sum(1 for p in self.resource_types if re.search(p, text, re.I))
        if resource_matches > 0:
            score += 0.10 * min(resource_matches, 2)
            notes.append(f"Resource types: {resource_matches}")

        # Check for URL/web presence (strong indicator)
        if re.search(r'http[s]?://|www\.|\bavailable at\b', text, re.I):
            score += 0.10
            notes.append("URL present")

        # Check title for resource name (often in title if introduction paper)
        if re.search(r':\s*[A-Z]', title if not pd.isna(title) else ''):
            score += 0.10
            notes.append("Resource name in title")

        # Negative indicators (usage papers)
        usage_matches = sum(1 for p in self.usage_patterns if re.search(p, text, re.I))
        if usage_matches > 2:
            score -= 0.20
            notes.append(f"Usage patterns: {usage_matches}")

        # Check for "new" or "novel" with resource
        if re.search(r'\b(new|novel)\s+\w+\s+(database|tool|server|resource)', text, re.I):
            score += 0.15
            notes.append("Novel resource mentioned")

        # Check for version numbers (strong indicator)
        if re.search(r'\bversion\s+\d+|\bv\d+\.\d+', text, re.I):
            score += 0.08
            notes.append("Version number")

        # Check for "freely available" or "open access" (resource indicator)
        if re.search(r'\b(freely available|open.?source|publicly available|free access)\b', text, re.I):
            score += 0.08
            notes.append("Publicly available")

        # Specific anti-patterns (definitely NOT introduction papers)
        if re.search(r'\b(review|survey|perspective|commentary|opinion)\b', text, re.I):
            if not re.search(r'\bwe present\b|\bwe developed\b', text, re.I):
                score -= 0.25
                notes.append("Review/survey paper")

        # Clinical/experimental study patterns (usually not bioresource)
        if re.search(r'\b(patients|cohort|clinical trial|randomized)\b', text, re.I):
            if not re.search(r'\b(database|tool|software|server)\b', text, re.I):
                score -= 0.20
                notes.append("Clinical study")

        # Clamp score to 0.0-1.0
        score = max(0.0, min(1.0, score))

        return score, "; ".join(notes) if notes else "No strong indicators"

    def evaluate_sample(self, input_csv, output_csv, summary_md):
        """Evaluate all papers in the sample"""

        print("Loading data...")
        df = pd.read_csv(input_csv)
        print(f"Loaded {len(df)} papers")

        # Initialize output columns
        results = []

        print("\nEvaluating papers...")
        for idx, row in df.iterrows():
            if idx % 50 == 0:
                print(f"  Progress: {idx}/{len(df)}")

            pmid = row['pmid']
            title = row['title']
            abstract = row['abstract']
            ling_score = row['ling_score']
            setfit_conf = row['setfit_confidence']

            review_score, notes = self.score_paper(pmid, title, abstract)

            results.append({
                'pmid': pmid,
                'title': title,
                'setfit_confidence': setfit_conf,
                'ling_score': ling_score,
                'review_score': review_score,
                'notes': notes
            })

        print(f"\nEvaluation complete: {len(results)} papers scored")

        # Create output dataframe
        results_df = pd.DataFrame(results)

        # Save results
        results_df.to_csv(output_csv, index=False)
        print(f"\nResults saved to: {output_csv}")

        # Generate summary statistics
        self.generate_summary(results_df, df, summary_md)

        return results_df

    def generate_summary(self, results_df, original_df, summary_md):
        """Generate summary statistics"""

        summary = []
        summary.append("# Review Agent 10: Evaluation Summary\n")
        summary.append(f"**Total papers evaluated**: {len(results_df)}\n")
        summary.append(f"**Date**: 2025-11-17\n\n")

        # Score distribution
        summary.append("## Review Score Distribution\n")
        summary.append(f"- **Mean score**: {results_df['review_score'].mean():.3f}\n")
        summary.append(f"- **Median score**: {results_df['review_score'].median():.3f}\n")
        summary.append(f"- **Std dev**: {results_df['review_score'].std():.3f}\n")
        summary.append(f"- **Min**: {results_df['review_score'].min():.3f}\n")
        summary.append(f"- **Max**: {results_df['review_score'].max():.3f}\n\n")

        # Categorize papers
        high_confidence = results_df[results_df['review_score'] >= 0.75]
        medium_confidence = results_df[(results_df['review_score'] >= 0.50) & (results_df['review_score'] < 0.75)]
        low_confidence = results_df[results_df['review_score'] < 0.50]

        summary.append("## Classification by Review Score\n")
        summary.append(f"- **High confidence bioresources** (≥0.75): {len(high_confidence)} ({len(high_confidence)/len(results_df)*100:.1f}%)\n")
        summary.append(f"- **Medium confidence** (0.50-0.74): {len(medium_confidence)} ({len(medium_confidence)/len(results_df)*100:.1f}%)\n")
        summary.append(f"- **Low confidence/Not bioresource** (<0.50): {len(low_confidence)} ({len(low_confidence)/len(results_df)*100:.1f}%)\n\n")

        # SetFit correlation analysis
        summary.append("## SetFit Performance Analysis\n")
        correlation = results_df['setfit_confidence'].corr(results_df['review_score'])
        summary.append(f"- **Correlation (SetFit vs Review)**: {correlation:.3f}\n")

        # Compare high/medium SetFit confidence groups
        results_df['setfit_group'] = results_df['setfit_confidence'].apply(
            lambda x: 'high' if x >= 0.75 else 'medium'
        )

        for group in ['high', 'medium']:
            group_df = results_df[results_df['setfit_group'] == group]
            if len(group_df) > 0:
                avg_review = group_df['review_score'].mean()
                true_positives = len(group_df[group_df['review_score'] >= 0.65])
                precision = true_positives / len(group_df) * 100
                summary.append(f"\n### SetFit {group.capitalize()} Confidence (n={len(group_df)})\n")
                summary.append(f"- Average review score: {avg_review:.3f}\n")
                summary.append(f"- Likely true positives (review ≥0.65): {true_positives} ({precision:.1f}%)\n")

        # Linguistic score correlation
        summary.append("\n## Linguistic Score Analysis\n")
        ling_correlation = results_df['ling_score'].corr(results_df['review_score'])
        summary.append(f"- **Correlation (Ling vs Review)**: {ling_correlation:.3f}\n")

        # Top scored papers
        summary.append("\n## Top 10 Highest Scored Papers\n")
        top_10 = results_df.nlargest(10, 'review_score')[['pmid', 'title', 'review_score', 'setfit_confidence']]
        summary.append("| PMID | Review Score | SetFit Conf | Title |\n")
        summary.append("|------|--------------|-------------|-------|\n")
        for _, row in top_10.iterrows():
            title_short = row['title'][:80] + '...' if len(str(row['title'])) > 80 else row['title']
            summary.append(f"| {row['pmid']} | {row['review_score']:.3f} | {row['setfit_confidence']:.3f} | {title_short} |\n")

        # Bottom 10 (likely false positives)
        summary.append("\n## Bottom 10 Lowest Scored Papers (Likely False Positives)\n")
        bottom_10 = results_df.nsmallest(10, 'review_score')[['pmid', 'title', 'review_score', 'setfit_confidence']]
        summary.append("| PMID | Review Score | SetFit Conf | Title |\n")
        summary.append("|------|--------------|-------------|-------|\n")
        for _, row in bottom_10.iterrows():
            title_short = row['title'][:80] + '...' if len(str(row['title'])) > 80 else row['title']
            summary.append(f"| {row['pmid']} | {row['review_score']:.3f} | {row['setfit_confidence']:.3f} | {title_short} |\n")

        # Agreement analysis
        summary.append("\n## Agreement Analysis\n")

        # High agreement (both high)
        high_agree = results_df[(results_df['setfit_confidence'] >= 0.70) & (results_df['review_score'] >= 0.70)]
        summary.append(f"- **High agreement (SetFit≥0.70 & Review≥0.70)**: {len(high_agree)} papers ({len(high_agree)/len(results_df)*100:.1f}%)\n")

        # Disagreement cases
        setfit_high_review_low = results_df[(results_df['setfit_confidence'] >= 0.70) & (results_df['review_score'] < 0.50)]
        summary.append(f"- **SetFit confident but Review low (false positives)**: {len(setfit_high_review_low)} papers ({len(setfit_high_review_low)/len(results_df)*100:.1f}%)\n")

        setfit_low_review_high = results_df[(results_df['setfit_confidence'] < 0.70) & (results_df['review_score'] >= 0.75)]
        summary.append(f"- **SetFit uncertain but Review high (missed positives)**: {len(setfit_low_review_high)} papers ({len(setfit_low_review_high)/len(results_df)*100:.1f}%)\n")

        # Write summary
        with open(summary_md, 'w') as f:
            f.writelines(summary)

        print(f"Summary saved to: {summary_md}")

        # Print key findings to console
        print("\n" + "="*70)
        print("KEY FINDINGS")
        print("="*70)
        print(f"Total papers: {len(results_df)}")
        print(f"High confidence bioresources (review ≥0.75): {len(high_confidence)} ({len(high_confidence)/len(results_df)*100:.1f}%)")
        print(f"SetFit-Review correlation: {correlation:.3f}")
        print(f"Linguistic-Review correlation: {ling_correlation:.3f}")
        print(f"Likely false positives: {len(setfit_high_review_low)} ({len(setfit_high_review_low)/len(results_df)*100:.1f}%)")
        print("="*70 + "\n")


def main():
    """Main execution"""

    base_dir = Path('/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146')

    input_csv = base_dir / 'review_agent10_sample.csv'
    output_csv = base_dir / 'agent10_scored_results.csv'
    summary_md = base_dir / 'agent10_summary.md'

    reviewer = BioresourceReviewer()
    results = reviewer.evaluate_sample(input_csv, output_csv, summary_md)

    print("\n✓ Review Agent 10 evaluation complete!")


if __name__ == '__main__':
    main()
