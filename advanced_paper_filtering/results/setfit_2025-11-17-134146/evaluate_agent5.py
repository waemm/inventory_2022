#!/usr/bin/env python3
"""
Review Agent 5: Systematic evaluation of 400 SetFit-classified papers
Scores each paper 0.0-1.0 on bioresource introduction likelihood
"""

import pandas as pd
import re
from typing import Tuple, Dict
import numpy as np

class BioresourceEvaluator:
    """Evaluates papers for bioresource introduction likelihood"""

    def __init__(self):
        # Strong indicators of resource introduction
        self.intro_patterns = [
            r'\bwe (?:present|describe|introduce|developed?|report|created?)\b',
            r'\bhere we (?:present|describe|introduce|report)\b',
            r'\bwe have (?:developed|created|built|constructed|generated)\b',
            r'\bnew (?:database|tool|server|resource|repository|platform|software|method|algorithm|pipeline)\b',
            r'\bnovel (?:database|tool|server|resource|repository|platform|software|method)\b',
            r'\bthis (?:database|tool|server|resource|repository|platform|software) (?:provides|offers|enables|allows)\b',
        ]

        # Title patterns indicating introduction
        self.title_intro_patterns = [
            r'^[A-Z][a-zA-Z0-9\-]+\s*:',  # Tool name followed by colon
            r'\bnew\s+(?:database|tool|server|resource|repository)\b',
            r'\bnovel\s+(?:database|tool|server|resource|repository)\b',
        ]

        # Resource type keywords
        self.resource_types = [
            'database', 'tool', 'server', 'repository', 'resource',
            'platform', 'software', 'web server', 'portal', 'pipeline',
            'application', 'system', 'framework', 'package', 'library'
        ]

        # Implementation/development keywords
        self.dev_keywords = [
            'developed', 'created', 'built', 'constructed', 'designed',
            'implemented', 'generated', 'established', 'introduced',
            'presents', 'provides access', 'freely available', 'publicly available'
        ]

        # Usage-only patterns (negative indicators)
        self.usage_patterns = [
            r'\busing\s+(?:the\s+)?(?:' + '|'.join(self.resource_types) + r')\b',
            r'\bapplied\s+(?:the\s+)?(?:' + '|'.join(self.resource_types) + r')\b',
            r'\bused\s+(?:the\s+)?(?:' + '|'.join(self.resource_types) + r')\b',
            r'\butiliz(?:ed|ing)\s+(?:the\s+)?(?:' + '|'.join(self.resource_types) + r')\b',
            r'\bwith\s+(?:the\s+)?(?:' + '|'.join(self.resource_types) + r')\b',
            r'\bfrom\s+(?:the\s+)?(?:' + '|'.join(self.resource_types) + r')\b',
        ]

        # Review/survey indicators (usually not introductions)
        self.review_patterns = [
            r'\breview(?:s|ed|ing)?\b',
            r'\bsurvey(?:s|ed)?\b',
            r'\bsummar(?:y|ize|izes|izing)\b',
            r'\boverview\b',
            r'\bperspective\b',
            r'\bcurrent state\b',
            r'\brecent (?:advances|developments|progress)\b',
        ]

    def score_paper(self, row: pd.Series) -> Tuple[float, str]:
        """
        Score a paper from 0.0 to 1.0 on bioresource introduction likelihood
        Returns: (score, notes)
        """
        title = str(row.get('title', '')).lower()
        abstract = str(row.get('abstract', '')).lower()
        ling_score = row.get('ling_score', 0)

        combined_text = title + ' ' + abstract
        score = 0.0
        notes = []

        # Check if it's a review/survey (strong negative)
        review_matches = sum(1 for p in self.review_patterns if re.search(p, title, re.I))
        if review_matches >= 2:
            notes.append("Review/survey paper")
            return 0.1, "; ".join(notes)

        # Check for strong introduction patterns
        intro_count = sum(1 for p in self.intro_patterns if re.search(p, combined_text, re.I))

        # Check title patterns
        title_intro = any(re.search(p, row.get('title', ''), re.I) for p in self.title_intro_patterns)

        # Check for resource type mentions
        resource_mentions = sum(1 for rt in self.resource_types if rt in combined_text)

        # Check for development keywords
        dev_mentions = sum(1 for kw in self.dev_keywords if kw in combined_text)

        # Check for usage-only patterns
        usage_count = sum(1 for p in self.usage_patterns if re.search(p, combined_text, re.I))

        # Check for URL (strong positive)
        has_url = bool(re.search(r'https?://|www\.', abstract))

        # Scoring logic
        if intro_count >= 3 and resource_mentions >= 2:
            score = 0.9
            notes.append("Strong introduction patterns + multiple resource mentions")
        elif intro_count >= 2 and (has_url or title_intro):
            score = 0.85
            notes.append("Multiple intro patterns + URL/title pattern")
        elif intro_count >= 2 and resource_mentions >= 1:
            score = 0.8
            notes.append("Multiple intro patterns + resource mention")
        elif intro_count >= 1 and dev_mentions >= 2 and resource_mentions >= 1:
            score = 0.75
            notes.append("Intro pattern + development keywords + resource")
        elif title_intro and intro_count >= 1:
            score = 0.7
            notes.append("Title pattern + intro language")
        elif intro_count >= 1 and resource_mentions >= 1:
            score = 0.6
            notes.append("Intro pattern + resource mention")
        elif dev_mentions >= 2 and resource_mentions >= 1:
            score = 0.5
            notes.append("Development keywords + resource mention")
        elif resource_mentions >= 2 and usage_count < 3:
            score = 0.4
            notes.append("Multiple resource mentions, limited usage patterns")
        elif usage_count >= 3:
            score = 0.2
            notes.append("Primarily usage/application language")
        else:
            score = 0.3
            notes.append("Limited bioresource indicators")

        # Adjust based on URL presence
        if has_url and score >= 0.6:
            score = min(1.0, score + 0.05)
            notes.append("URL present")

        # Adjust based on linguistic score
        if ling_score >= 2:
            score = min(1.0, score + 0.05)
            notes.append(f"High ling_score={ling_score}")

        # Final adjustments based on specific patterns
        if re.search(r'\bprecompute[d]?\s+\w+\s+for\b', combined_text, re.I):
            score = min(1.0, score + 0.05)
            notes.append("Precomputed results available")

        if re.search(r'\bfreely available\s+(?:at|from)\b', combined_text, re.I):
            score = min(1.0, score + 0.05)
            notes.append("Freely available")

        # Cap at 1.0
        score = min(1.0, score)

        return round(score, 2), "; ".join(notes) if notes else "No strong indicators"

    def evaluate_dataset(self, input_file: str, output_file: str, summary_file: str):
        """Evaluate all papers and generate results"""
        print(f"Loading data from {input_file}...")
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} papers")

        # Score each paper
        print("Scoring papers...")
        results = []
        for idx, row in df.iterrows():
            if idx % 50 == 0:
                print(f"  Processed {idx}/{len(df)} papers...")

            score, notes = self.score_paper(row)
            results.append({
                'pmid': row['pmid'],
                'title': row['title'],
                'setfit_confidence': row['setfit_confidence'],
                'ling_score': row['ling_score'],
                'review_score': score,
                'notes': notes
            })

        # Create output dataframe
        results_df = pd.DataFrame(results)

        # Save results
        print(f"\nSaving results to {output_file}...")
        results_df.to_csv(output_file, index=False)

        # Generate summary statistics
        self.generate_summary(results_df, summary_file)

        print(f"\nEvaluation complete!")
        print(f"Results saved to: {output_file}")
        print(f"Summary saved to: {summary_file}")

        return results_df

    def generate_summary(self, df: pd.DataFrame, summary_file: str):
        """Generate summary markdown with statistics"""

        # Calculate statistics
        total_papers = len(df)

        # Score distribution
        score_bins = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
        score_labels = ['Very Low (0-0.3)', 'Low (0.3-0.5)', 'Medium (0.5-0.7)', 'High (0.7-0.9)', 'Very High (0.9-1.0)']
        df['score_category'] = pd.cut(df['review_score'], bins=score_bins, labels=score_labels, include_lowest=True)

        # SetFit confidence correlation
        high_conf = df[df['setfit_confidence'] >= 0.7]
        med_conf = df[df['setfit_confidence'] < 0.7]

        # Top and bottom papers
        top_20 = df.nlargest(20, 'review_score')
        bottom_20 = df.nsmallest(20, 'review_score')

        # Generate markdown
        summary = f"""# Review Agent 5: Evaluation Summary

## Overview
- **Total Papers Evaluated**: {total_papers}
- **High Confidence SetFit (≥0.7)**: {len(high_conf)} papers
- **Medium Confidence SetFit (<0.7)**: {len(med_conf)} papers

## Review Score Distribution

| Score Range | Count | Percentage |
|-------------|-------|------------|
| Very High (0.9-1.0) | {len(df[df['review_score'] >= 0.9])} | {len(df[df['review_score'] >= 0.9])/total_papers*100:.1f}% |
| High (0.7-0.9) | {len(df[(df['review_score'] >= 0.7) & (df['review_score'] < 0.9)])} | {len(df[(df['review_score'] >= 0.7) & (df['review_score'] < 0.9)])/total_papers*100:.1f}% |
| Medium (0.5-0.7) | {len(df[(df['review_score'] >= 0.5) & (df['review_score'] < 0.7)])} | {len(df[(df['review_score'] >= 0.5) & (df['review_score'] < 0.7)])/total_papers*100:.1f}% |
| Low (0.3-0.5) | {len(df[(df['review_score'] >= 0.3) & (df['review_score'] < 0.5)])} | {len(df[(df['review_score'] >= 0.3) & (df['review_score'] < 0.5)])/total_papers*100:.1f}% |
| Very Low (0-0.3) | {len(df[df['review_score'] < 0.3])} | {len(df[df['review_score'] < 0.3])/total_papers*100:.1f}% |

## SetFit Quality Assessment

### Correlation Analysis
- **Mean review score (High Confidence SetFit)**: {high_conf['review_score'].mean():.3f}
- **Mean review score (Medium Confidence SetFit)**: {med_conf['review_score'].mean():.3f}
- **Difference**: {high_conf['review_score'].mean() - med_conf['review_score'].mean():.3f}

### Agreement Analysis
- Papers where both SetFit and Review score are high (SetFit≥0.7, Review≥0.7): {len(df[(df['setfit_confidence'] >= 0.7) & (df['review_score'] >= 0.7)])}
- Papers where SetFit is high but Review is low (SetFit≥0.7, Review<0.5): {len(df[(df['setfit_confidence'] >= 0.7) & (df['review_score'] < 0.5)])}
- Papers where SetFit is medium but Review is high (SetFit<0.7, Review≥0.7): {len(df[(df['setfit_confidence'] < 0.7) & (df['review_score'] >= 0.7)])}

**Correlation coefficient (SetFit confidence vs Review score)**: {df['setfit_confidence'].corr(df['review_score']):.3f}

## Key Findings

### SetFit Performance
"""

        # Assess SetFit performance
        corr = df['setfit_confidence'].corr(df['review_score'])
        if corr > 0.5:
            summary += f"✅ **Strong positive correlation** ({corr:.3f}): SetFit confidence is a good predictor of bioresource introduction likelihood.\n\n"
        elif corr > 0.3:
            summary += f"⚠️ **Moderate correlation** ({corr:.3f}): SetFit shows some alignment but has room for improvement.\n\n"
        else:
            summary += f"❌ **Weak correlation** ({corr:.3f}): SetFit confidence does not reliably predict bioresource introduction likelihood.\n\n"

        # False positives and negatives
        false_positives = df[(df['setfit_confidence'] >= 0.7) & (df['review_score'] < 0.5)]
        false_negatives = df[(df['setfit_confidence'] < 0.7) & (df['review_score'] >= 0.7)]

        summary += f"### Potential Issues\n"
        summary += f"- **False Positives** (High SetFit, Low Review): {len(false_positives)} papers ({len(false_positives)/total_papers*100:.1f}%)\n"
        summary += f"- **False Negatives** (Low SetFit, High Review): {len(false_negatives)} papers ({len(false_negatives)/total_papers*100:.1f}%)\n\n"

        # Top 20 highest scored papers
        summary += f"## Top 20 Highest Scored Papers\n\n"
        summary += "| PMID | SetFit Conf | Review Score | Title |\n"
        summary += "|------|-------------|--------------|-------|\n"
        for _, row in top_20.iterrows():
            title_short = row['title'][:80] + "..." if len(str(row['title'])) > 80 else row['title']
            summary += f"| {row['pmid']} | {row['setfit_confidence']:.3f} | {row['review_score']:.2f} | {title_short} |\n"

        # Bottom 20 lowest scored papers
        summary += f"\n## Bottom 20 Lowest Scored Papers\n\n"
        summary += "| PMID | SetFit Conf | Review Score | Title |\n"
        summary += "|------|-------------|--------------|-------|\n"
        for _, row in bottom_20.iterrows():
            title_short = row['title'][:80] + "..." if len(str(row['title'])) > 80 else row['title']
            summary += f"| {row['pmid']} | {row['setfit_confidence']:.3f} | {row['review_score']:.2f} | {title_short} |\n"

        # Examples of disagreement
        summary += f"\n## Examples of SetFit/Review Disagreement\n\n"

        if len(false_positives) > 0:
            summary += f"### High SetFit, Low Review (Possible False Positives)\n\n"
            summary += "| PMID | SetFit Conf | Review Score | Title | Notes |\n"
            summary += "|------|-------------|--------------|-------|-------|\n"
            for _, row in false_positives.head(10).iterrows():
                title_short = row['title'][:60] + "..." if len(str(row['title'])) > 60 else row['title']
                notes_short = str(row['notes'])[:50] + "..." if len(str(row['notes'])) > 50 else row['notes']
                summary += f"| {row['pmid']} | {row['setfit_confidence']:.3f} | {row['review_score']:.2f} | {title_short} | {notes_short} |\n"

        if len(false_negatives) > 0:
            summary += f"\n### Low SetFit, High Review (Possible False Negatives)\n\n"
            summary += "| PMID | SetFit Conf | Review Score | Title | Notes |\n"
            summary += "|------|-------------|--------------|-------|-------|\n"
            for _, row in false_negatives.head(10).iterrows():
                title_short = row['title'][:60] + "..." if len(str(row['title'])) > 60 else row['title']
                notes_short = str(row['notes'])[:50] + "..." if len(str(row['notes'])) > 50 else row['notes']
                summary += f"| {row['pmid']} | {row['setfit_confidence']:.3f} | {row['review_score']:.2f} | {title_short} | {notes_short} |\n"

        # Recommendations
        summary += f"\n## Recommendations\n\n"

        if corr > 0.5:
            summary += f"1. ✅ SetFit is performing well and can be trusted for high-confidence predictions\n"
            summary += f"2. Consider using a threshold of {df[df['review_score'] >= 0.7]['setfit_confidence'].min():.3f} for high-precision filtering\n"
        else:
            summary += f"1. ⚠️ SetFit needs improvement - consider retraining with better examples\n"
            summary += f"2. Use linguistic features as a complementary signal\n"

        summary += f"3. Papers with review_score ≥ 0.7 are strong bioresource introduction candidates ({len(df[df['review_score'] >= 0.7])} papers)\n"
        summary += f"4. Papers with review_score < 0.3 are likely not bioresource introductions ({len(df[df['review_score'] < 0.3])} papers)\n"

        # Write summary
        with open(summary_file, 'w') as f:
            f.write(summary)


def main():
    """Main execution"""
    input_file = "/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/review_agent5_sample.csv"
    output_file = "/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/agent5_scored_results.csv"
    summary_file = "/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/agent5_summary.md"

    evaluator = BioresourceEvaluator()
    results_df = evaluator.evaluate_dataset(input_file, output_file, summary_file)

    print("\n" + "="*60)
    print("QUICK SUMMARY")
    print("="*60)
    print(f"Total papers: {len(results_df)}")
    print(f"High confidence (≥0.7): {len(results_df[results_df['review_score'] >= 0.7])}")
    print(f"Medium confidence (0.5-0.7): {len(results_df[(results_df['review_score'] >= 0.5) & (results_df['review_score'] < 0.7)])}")
    print(f"Low confidence (<0.5): {len(results_df[results_df['review_score'] < 0.5])}")
    print(f"\nCorrelation (SetFit vs Review): {results_df['setfit_confidence'].corr(results_df['review_score']):.3f}")
    print("="*60)


if __name__ == "__main__":
    main()
