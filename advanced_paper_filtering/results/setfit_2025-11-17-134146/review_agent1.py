#!/usr/bin/env python3
"""
Agent 1 Review Script - SetFit Bioresource Classification Quality Assessment
Reviews 200 papers and scores them 0-1 on introduction likelihood
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path

class BioresourceReviewer:
    """Score papers on likelihood of being genuine resource introductions"""

    def __init__(self):
        # Introduction signal patterns
        self.intro_phrases = [
            r'\bwe\s+(present|introduce|describe|develop|report|implement|design|build|create|construct|propose)\b',
            r'\bis\s+a\s+(database|tool|platform|server|resource|repository|portal|website|web\s+server|system|application|software|package|pipeline|framework|suite)\b',
            r'\bprovides?\b.*\b(access|data|information|analysis|tools?|features?|capabilities|functionality)\b',
            r'\benables?\b.*\b(users?|researchers?|scientists?|community)\b',
            r'\bavailable\s+at\b',
            r'\bcan\s+be\s+accessed\b',
            r'\bfreely\s+available\b',
            r'\bopen\s+source\b',
            r'\bdownloadable?\b',
        ]

        # Usage signal patterns (NOT introductions)
        self.usage_phrases = [
            r'\bwe\s+used\b',
            r'\bwas\s+used\s+to\b',
            r'\bwere\s+used\s+to\b',
            r'\busing\s+the\b',
            r'\bdata\s+(was|were)\s+(obtained|downloaded|retrieved|collected)\s+from\b',
            r'\bapplied\s+to\b',
            r'\bperformed\s+using\b',
            r'\banalyzed?\s+(using|with)\b',
            r'\bidentified?\s+using\b',
            r'\bstatistical\s+analysis\b',
        ]

        # Resource type keywords in title
        self.title_resource_keywords = [
            'database', 'db', 'tool', 'server', 'platform', 'resource',
            'repository', 'portal', 'website', 'atlas', 'browser',
            'software', 'package', 'pipeline', 'suite', 'system'
        ]

    def score_paper(self, row):
        """
        Score a paper 0-1 on introduction likelihood
        Returns: (score, confidence_level, reasoning)
        """
        title = str(row['title']).lower()
        abstract = str(row['abstract']).lower()
        full_text = f"{title} {abstract}"

        # Count signals
        intro_signals = sum(1 for pattern in self.intro_phrases if re.search(pattern, full_text, re.IGNORECASE))
        usage_signals = sum(1 for pattern in self.usage_phrases if re.search(pattern, full_text, re.IGNORECASE))

        # Title analysis
        has_resource_in_title = any(keyword in title for keyword in self.title_resource_keywords)
        title_looks_like_name = bool(re.search(r'^[A-Z][a-z]+[A-Z]', str(row['title'])))  # CamelCase name

        # URL presence
        has_url = row['ling_has_url'] if 'ling_has_url' in row else False

        # Implementation vs usage keywords
        impl_keywords = int(row['ling_impl_keywords']) if 'ling_impl_keywords' in row else 0
        usage_keywords = int(row['ling_usage_keywords']) if 'ling_usage_keywords' in row else 0

        # Scoring logic
        score = 0.5  # Start neutral
        reasons = []

        # Strong positive signals
        if has_resource_in_title and intro_signals >= 2:
            score = 0.95
            reasons.append("Resource in title + strong intro language")
        elif has_resource_in_title and intro_signals >= 1:
            score = 0.85
            reasons.append("Resource in title + intro language")
        elif intro_signals >= 3:
            score = 0.80
            reasons.append("Multiple intro signals")
        elif intro_signals >= 2:
            score = 0.70
            reasons.append("Some intro signals")
        elif intro_signals >= 1:
            score = 0.60
            reasons.append("Weak intro signals")

        # Adjust for usage signals
        if usage_signals >= 3:
            score = max(0.0, score - 0.4)
            reasons.append("Strong usage language")
        elif usage_signals >= 2:
            score = max(0.1, score - 0.3)
            reasons.append("Some usage language")
        elif usage_signals >= 1:
            score = max(0.2, score - 0.2)
            reasons.append("Weak usage language")

        # URL/access info boost
        if has_url and score >= 0.6:
            score = min(1.0, score + 0.1)
            reasons.append("Has URL")

        # Implementation keywords boost
        if impl_keywords >= 3 and usage_keywords <= 1:
            score = min(1.0, score + 0.15)
            reasons.append("Strong implementation focus")

        # CamelCase name in title (like "BioDB")
        if title_looks_like_name and intro_signals >= 1:
            score = min(1.0, score + 0.1)
            reasons.append("Named resource in title")

        # Check for explicit introduction phrases
        if re.search(r'\bwe\s+(present|introduce)\s+\w+[,:]?\s+a\s+(database|tool|platform|server)', abstract, re.IGNORECASE):
            score = max(score, 0.90)
            reasons.append("Explicit introduction statement")

        # Check for "this database/tool" patterns
        if re.search(r'\b(this|the)\s+(database|tool|platform|server|resource)\s+(provides|enables|allows|contains)', abstract, re.IGNORECASE):
            score = max(score, 0.75)
            reasons.append("Resource description present")

        # Strong usage indicators (NOT introduction)
        if re.search(r'\bwe\s+used\s+\w+\s+to\s+(analyze|identify|determine|investigate)', abstract, re.IGNORECASE):
            score = min(score, 0.3)
            reasons.append("Clear usage context")

        # Multiple resources mentioned (using many tools)
        resource_mentions = len(re.findall(r'\b(database|tool|server|software)\b', abstract, re.IGNORECASE))
        if resource_mentions >= 5:
            score = min(score, 0.4)
            reasons.append("Multiple resources mentioned (likely usage)")

        # Statistical/methods focus
        if re.search(r'\b(statistical\s+analysis|regression|correlation|p\s*[<>=]|significance)', abstract, re.IGNORECASE):
            score = max(0.0, score - 0.15)
            reasons.append("Statistical analysis focus")

        # Review/survey indicators
        if re.search(r'\b(review|survey|overview|guide|tutorial)\b', title, re.IGNORECASE):
            score = min(score, 0.5)
            reasons.append("Review/guide content")

        # Ensure score is in valid range
        score = max(0.0, min(1.0, score))

        # Determine confidence level
        if score >= 0.8 or score <= 0.2:
            confidence = "high"
        elif score >= 0.6 or score <= 0.4:
            confidence = "medium"
        else:
            confidence = "low"

        reasoning = "; ".join(reasons) if reasons else "Neutral indicators"

        return score, confidence, reasoning

    def review_papers(self, input_csv, output_csv):
        """Process all papers and generate scored results"""
        print(f"Reading {input_csv}...")
        df = pd.read_csv(input_csv)
        print(f"Loaded {len(df)} papers")

        # Score each paper
        results = []
        for idx, row in df.iterrows():
            if idx % 20 == 0:
                print(f"Processing paper {idx+1}/{len(df)}...")

            score, confidence, reasoning = self.score_paper(row)

            # Create result row
            result = {
                'pmid': row['pmid'],
                'title_snippet': str(row['title'])[:80] + "..." if len(str(row['title'])) > 80 else str(row['title']),
                'agent_score': round(score, 3),
                'confidence_level': confidence,
                'reasoning': reasoning,
                'setfit_confidence': round(float(row['setfit_confidence']), 3),
                'ling_score': int(row['ling_score'])
            }
            results.append(result)

        # Save results
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_csv, index=False)
        print(f"\nSaved scored results to {output_csv}")

        return results_df

    def generate_summary(self, results_df, output_md):
        """Generate summary report with statistics and findings"""

        report = []
        report.append("# Agent 1 Review Summary - SetFit Classification Quality Assessment\n")
        report.append(f"**Date**: 2025-11-17")
        report.append(f"**Papers Reviewed**: {len(results_df)}\n")

        # Overall Statistics
        report.append("## Overall Statistics\n")

        mean_score = results_df['agent_score'].mean()
        median_score = results_df['agent_score'].median()
        std_score = results_df['agent_score'].std()

        report.append(f"- **Mean Agent Score**: {mean_score:.3f}")
        report.append(f"- **Median Agent Score**: {median_score:.3f}")
        report.append(f"- **Std Dev**: {std_score:.3f}\n")

        # Score distribution
        report.append("### Score Distribution\n")
        bins = [(0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
        for low, high in bins:
            count = len(results_df[(results_df['agent_score'] >= low) & (results_df['agent_score'] < high)])
            pct = 100 * count / len(results_df)
            report.append(f"- **{low:.1f}-{high:.1f}**: {count} papers ({pct:.1f}%)")
        count_perfect = len(results_df[results_df['agent_score'] == 1.0])
        if count_perfect > 0:
            report.append(f"- **1.0 (perfect)**: {count_perfect} papers ({100*count_perfect/len(results_df):.1f}%)")
        report.append("")

        # Agreement analysis
        report.append("### Agreement with SetFit and Linguistic Scores\n")

        correlation_setfit = results_df['agent_score'].corr(results_df['setfit_confidence'])
        correlation_ling = results_df['agent_score'].corr(results_df['ling_score'])

        report.append(f"- **Correlation with SetFit confidence**: {correlation_setfit:.3f}")
        report.append(f"- **Correlation with Linguistic score**: {correlation_ling:.3f}\n")

        # SetFit Performance Assessment
        report.append("## SetFit Performance Assessment\n")

        true_positives = len(results_df[results_df['agent_score'] >= 0.6])
        precision = 100 * true_positives / len(results_df)

        false_positives = len(results_df[results_df['agent_score'] < 0.4])
        false_positive_rate = 100 * false_positives / len(results_df)

        uncertain = len(results_df[(results_df['agent_score'] >= 0.4) & (results_df['agent_score'] < 0.6)])
        uncertain_rate = 100 * uncertain / len(results_df)

        report.append(f"- **Estimated Precision**: {precision:.1f}% (papers scored ≥0.6)")
        report.append(f"- **False Positive Rate**: {false_positive_rate:.1f}% (papers scored <0.4)")
        report.append(f"- **Uncertain Cases**: {uncertain_rate:.1f}% (papers scored 0.4-0.6)\n")

        # Confidence analysis
        high_conf_setfit = results_df[results_df['setfit_confidence'] >= 0.8]
        if len(high_conf_setfit) > 0:
            high_conf_precision = 100 * len(high_conf_setfit[high_conf_setfit['agent_score'] >= 0.6]) / len(high_conf_setfit)
            report.append(f"- **High SetFit Confidence (≥0.8)**: {len(high_conf_setfit)} papers, {high_conf_precision:.1f}% validated\n")

        # Key Findings
        report.append("## Key Findings\n")

        # Patterns for true introductions
        report.append("### Patterns Indicating True Introductions\n")
        true_intros = results_df[results_df['agent_score'] >= 0.8]
        if len(true_intros) > 0:
            report.append(f"- **{len(true_intros)} papers scored ≥0.8** (strong introductions)")
            report.append(f"- Average linguistic score: {true_intros['ling_score'].mean():.2f}")
            report.append(f"- Average SetFit confidence: {true_intros['setfit_confidence'].mean():.3f}\n")

        # Patterns for false positives
        report.append("### Patterns Indicating False Positives\n")
        false_pos = results_df[results_df['agent_score'] < 0.4]
        if len(false_pos) > 0:
            report.append(f"- **{len(false_pos)} papers scored <0.4** (likely false positives)")
            report.append(f"- Average linguistic score: {false_pos['ling_score'].mean():.2f}")
            report.append(f"- Average SetFit confidence: {false_pos['setfit_confidence'].mean():.3f}\n")

        # SetFit calibration
        report.append("### SetFit Calibration Analysis\n")

        overconfident = results_df[(results_df['setfit_confidence'] >= 0.8) & (results_df['agent_score'] < 0.5)]
        underconfident = results_df[(results_df['setfit_confidence'] < 0.6) & (results_df['agent_score'] >= 0.8)]

        if len(overconfident) > 0:
            report.append(f"- **Overconfident cases**: {len(overconfident)} papers (high SetFit conf, low agent score)")
        if len(underconfident) > 0:
            report.append(f"- **Underconfident cases**: {len(underconfident)} papers (low SetFit conf, high agent score)")
        report.append("")

        # Example Papers
        report.append("## Example Papers\n")

        # Excellent introductions
        report.append("### Excellent Introductions (Agent Score ≥0.9)\n")
        excellent = results_df[results_df['agent_score'] >= 0.9].head(5)
        for idx, row in excellent.iterrows():
            report.append(f"- **PMID {row['pmid']}** (score: {row['agent_score']:.2f}, SetFit: {row['setfit_confidence']:.2f})")
            report.append(f"  - Title: {row['title_snippet']}")
            report.append(f"  - Reasoning: {row['reasoning']}\n")

        # False positives
        report.append("### Likely False Positives (Agent Score <0.3, SetFit Confidence >0.6)\n")
        false_pos_examples = results_df[
            (results_df['agent_score'] < 0.3) &
            (results_df['setfit_confidence'] > 0.6)
        ].head(5)
        if len(false_pos_examples) > 0:
            for idx, row in false_pos_examples.iterrows():
                report.append(f"- **PMID {row['pmid']}** (score: {row['agent_score']:.2f}, SetFit: {row['setfit_confidence']:.2f})")
                report.append(f"  - Title: {row['title_snippet']}")
                report.append(f"  - Reasoning: {row['reasoning']}\n")
        else:
            report.append("- None found\n")

        # Borderline cases
        report.append("### Borderline Cases (Agent Score 0.4-0.6)\n")
        borderline = results_df[
            (results_df['agent_score'] >= 0.4) &
            (results_df['agent_score'] <= 0.6)
        ].head(5)
        if len(borderline) > 0:
            for idx, row in borderline.iterrows():
                report.append(f"- **PMID {row['pmid']}** (score: {row['agent_score']:.2f}, SetFit: {row['setfit_confidence']:.2f})")
                report.append(f"  - Title: {row['title_snippet']}")
                report.append(f"  - Reasoning: {row['reasoning']}\n")
        else:
            report.append("- None found\n")

        # Save report
        with open(output_md, 'w') as f:
            f.write('\n'.join(report))

        print(f"Saved summary report to {output_md}")


def main():
    base_dir = Path("/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146")

    input_csv = base_dir / "review_agent1_sample.csv"
    output_csv = base_dir / "agent1_scored_results.csv"
    output_md = base_dir / "agent1_summary.md"

    reviewer = BioresourceReviewer()

    # Review papers
    results_df = reviewer.review_papers(input_csv, output_csv)

    # Generate summary
    reviewer.generate_summary(results_df, output_md)

    print("\n✅ Review complete!")
    print(f"- Scored results: {output_csv}")
    print(f"- Summary report: {output_md}")


if __name__ == "__main__":
    main()
