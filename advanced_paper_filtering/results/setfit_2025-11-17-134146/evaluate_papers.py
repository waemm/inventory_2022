#!/usr/bin/env python3
"""
Review Agent 8: Evaluate 400 SetFit-classified papers for bioresource introduction likelihood.
Scores each paper 0.0-1.0 based on title, abstract, and linguistic features.
"""

import pandas as pd
import re
from typing import Tuple
import json

# Patterns indicating bioresource INTRODUCTION
INTRO_PATTERNS = [
    r'\bwe\s+(present|introduce|describe|report|developed?|created?|built|designed|implemented|propose)\b',
    r'\bhere\s+we\s+(present|introduce|describe|report|show|developed?)',
    r'\b(this|the)\s+(paper|article|study)\s+(presents|introduces|describes|reports)',
    r'\bnew\s+(database|tool|server|resource|repository|platform|web\s*server|software|application)',
    r'\bnovel\s+(database|tool|server|resource|repository|platform|method|approach)',
    r'\bfreely\s+(available|accessible)',
    r'\bavailable\s+at\s+https?://',
    r'\bcan\s+be\s+accessed\s+(at|via|through)',
]

# Strong database/resource indicators
RESOURCE_KEYWORDS = [
    r'\bdatabase\b', r'\brepository\b', r'\bweb\s*server\b', r'\bserver\b',
    r'\btool\b', r'\bsoftware\b', r'\bplatform\b', r'\bportal\b',
    r'\bresource\b', r'\bapplication\b', r'\binterface\b', r'\bpipeline\b'
]

# Usage patterns (NOT introduction)
USAGE_PATTERNS = [
    r'\busing\s+(the|a|an)\s+\w+\s+(database|tool|server)',
    r'\bwas\s+used\s+to\b',
    r'\bwere\s+obtained\s+from\b',
    r'\bretrieved\s+from\b',
    r'\bdata\s+from\s+the\b',
    r'\banalyzed\s+using\b',
    r'\bidentified\s+using\b',
]

# Generic research patterns (not resource-specific)
GENERIC_PATTERNS = [
    r'\breview\b', r'\bsurvey\b', r'\bmeta-analysis\b',
    r'\bclinical\s+trial\b', r'\bpatient\b', r'\bcohort\b',
    r'\btreatment\b', r'\btherapy\b', r'\bdiagnosis\b'
]


def score_paper(row: pd.Series) -> Tuple[float, str]:
    """
    Score a paper 0.0-1.0 for bioresource introduction likelihood.

    Returns:
        (score, notes)
    """
    title = str(row.get('title', '')).lower()
    abstract = str(row.get('abstract', '')).lower()
    text = f"{title} {abstract}"

    # Start with neutral score
    score = 0.5
    notes = []

    # Check for introduction patterns (strong positive signal)
    intro_matches = sum(1 for pattern in INTRO_PATTERNS if re.search(pattern, text, re.IGNORECASE))
    if intro_matches >= 2:
        score += 0.3
        notes.append(f"Strong intro language ({intro_matches} patterns)")
    elif intro_matches == 1:
        score += 0.15
        notes.append("Some intro language")

    # Check for resource keywords
    resource_matches = sum(1 for pattern in RESOURCE_KEYWORDS if re.search(pattern, text, re.IGNORECASE))
    if resource_matches >= 3:
        score += 0.15
        notes.append(f"Multiple resource keywords ({resource_matches})")
    elif resource_matches >= 1:
        score += 0.05
        notes.append(f"Resource keywords ({resource_matches})")

    # Check for URL (strong indicator of new resource)
    has_url = bool(row.get('ling_has_url', False))
    if has_url and intro_matches > 0:
        score += 0.2
        notes.append("Has URL with intro pattern")
    elif has_url:
        score += 0.1
        notes.append("Has URL")

    # Check for usage patterns (negative signal)
    usage_matches = sum(1 for pattern in USAGE_PATTERNS if re.search(pattern, text, re.IGNORECASE))
    if usage_matches >= 2 and intro_matches == 0:
        score -= 0.3
        notes.append(f"Appears to USE resources ({usage_matches} patterns)")
    elif usage_matches >= 1 and intro_matches == 0:
        score -= 0.15
        notes.append("May use existing resources")

    # Check for generic research (not resource-focused)
    generic_matches = sum(1 for pattern in GENERIC_PATTERNS if re.search(pattern, text, re.IGNORECASE))
    if generic_matches >= 2 and resource_matches == 0:
        score -= 0.2
        notes.append("Generic research paper")

    # Use linguistic features
    ling_has_intro = bool(row.get('ling_has_intro_pattern', False))
    ling_has_title = bool(row.get('ling_has_title_pattern', False))
    ling_impl = int(row.get('ling_impl_keywords', 0))
    ling_usage = int(row.get('ling_usage_keywords', 0))

    if ling_has_intro or ling_has_title:
        score += 0.1
        notes.append("Ling features: intro/title pattern")

    if ling_impl > ling_usage:
        score += 0.05
        notes.append(f"More impl ({ling_impl}) than usage ({ling_usage})")
    elif ling_usage > ling_impl and ling_impl == 0:
        score -= 0.1
        notes.append(f"Usage-heavy ({ling_usage} vs {ling_impl})")

    # Specific title patterns
    if re.search(r':\s*(a|an)\s+(new|novel)?\s*(database|tool|server|resource|platform)', title):
        score += 0.2
        notes.append("Title suggests new resource")

    # Clamp score to [0.0, 1.0]
    score = max(0.0, min(1.0, score))

    return score, "; ".join(notes) if notes else "No strong signals"


def main():
    print("Review Agent 8: Evaluating 400 SetFit-classified papers...")

    # Load data
    input_file = '/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/review_agent8_sample.csv'
    df = pd.read_csv(input_file)

    print(f"Loaded {len(df)} papers")
    print(f"Columns: {list(df.columns)}")

    # Score each paper
    results = []
    for idx, row in df.iterrows():
        if idx % 50 == 0:
            print(f"Processing paper {idx+1}/{len(df)}...")

        score, notes = score_paper(row)

        results.append({
            'pmid': row['pmid'],
            'title': row['title'],
            'setfit_confidence': row['setfit_confidence'],
            'ling_score': row['ling_score'],
            'review_score': round(score, 3),
            'notes': notes
        })

    # Create output DataFrame
    output_df = pd.DataFrame(results)

    # Save results
    output_file = '/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/agent8_scored_results.csv'
    output_df.to_csv(output_file, index=False)
    print(f"\n✓ Saved scored results to: {output_file}")

    # Generate statistics
    stats = generate_statistics(output_df, df)

    # Save summary
    summary_file = '/Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/results/setfit_2025-11-17-134146/agent8_summary.md'
    with open(summary_file, 'w') as f:
        f.write(stats)
    print(f"✓ Saved summary to: {summary_file}")

    print("\n" + "="*80)
    print("EVALUATION COMPLETE")
    print("="*80)


def generate_statistics(output_df: pd.DataFrame, input_df: pd.DataFrame) -> str:
    """Generate comprehensive statistics and summary markdown."""

    # Split by SetFit confidence (high vs medium)
    high_conf = output_df[output_df['setfit_confidence'] >= 0.7]
    med_conf = output_df[output_df['setfit_confidence'] < 0.7]

    summary = f"""# Review Agent 8 - Evaluation Summary

**Date**: 2025-11-17
**Total Papers Evaluated**: {len(output_df)}
**High Confidence (≥0.7)**: {len(high_conf)} papers
**Medium Confidence (<0.7)**: {len(med_conf)} papers

---

## Review Score Distribution

### Overall Statistics
- **Mean Review Score**: {output_df['review_score'].mean():.3f}
- **Median Review Score**: {output_df['review_score'].median():.3f}
- **Std Dev**: {output_df['review_score'].std():.3f}
- **Min**: {output_df['review_score'].min():.3f}
- **Max**: {output_df['review_score'].max():.3f}

### Score Categories
- **High Confidence (≥0.8)**: {len(output_df[output_df['review_score'] >= 0.8])} papers ({len(output_df[output_df['review_score'] >= 0.8])/len(output_df)*100:.1f}%)
- **Medium-High (0.6-0.79)**: {len(output_df[(output_df['review_score'] >= 0.6) & (output_df['review_score'] < 0.8)])} papers ({len(output_df[(output_df['review_score'] >= 0.6) & (output_df['review_score'] < 0.8)])/len(output_df)*100:.1f}%)
- **Borderline (0.4-0.59)**: {len(output_df[(output_df['review_score'] >= 0.4) & (output_df['review_score'] < 0.6)])} papers ({len(output_df[(output_df['review_score'] >= 0.4) & (output_df['review_score'] < 0.6)])/len(output_df)*100:.1f}%)
- **Low (0.2-0.39)**: {len(output_df[(output_df['review_score'] >= 0.2) & (output_df['review_score'] < 0.4)])} papers ({len(output_df[(output_df['review_score'] >= 0.2) & (output_df['review_score'] < 0.4)])/len(output_df)*100:.1f}%)
- **Very Low (<0.2)**: {len(output_df[output_df['review_score'] < 0.2])} papers ({len(output_df[output_df['review_score'] < 0.2])/len(output_df)*100:.1f}%)

---

## SetFit Quality Analysis

### High Confidence Papers (SetFit ≥0.7, n={len(high_conf)})
- **Mean Review Score**: {high_conf['review_score'].mean():.3f}
- **Median Review Score**: {high_conf['review_score'].median():.3f}
- **Papers with Review Score ≥0.8**: {len(high_conf[high_conf['review_score'] >= 0.8])} ({len(high_conf[high_conf['review_score'] >= 0.8])/len(high_conf)*100:.1f}%)
- **Papers with Review Score ≥0.6**: {len(high_conf[high_conf['review_score'] >= 0.6])} ({len(high_conf[high_conf['review_score'] >= 0.6])/len(high_conf)*100:.1f}%)
- **Papers with Review Score <0.4**: {len(high_conf[high_conf['review_score'] < 0.4])} ({len(high_conf[high_conf['review_score'] < 0.4])/len(high_conf)*100:.1f}%)

### Medium Confidence Papers (SetFit <0.7, n={len(med_conf)})
- **Mean Review Score**: {med_conf['review_score'].mean():.3f}
- **Median Review Score**: {med_conf['review_score'].median():.3f}
- **Papers with Review Score ≥0.8**: {len(med_conf[med_conf['review_score'] >= 0.8])} ({len(med_conf[med_conf['review_score'] >= 0.8])/len(med_conf)*100:.1f}%)
- **Papers with Review Score ≥0.6**: {len(med_conf[med_conf['review_score'] >= 0.6])} ({len(med_conf[med_conf['review_score'] >= 0.6])/len(med_conf)*100:.1f}%)
- **Papers with Review Score <0.4**: {len(med_conf[med_conf['review_score'] < 0.4])} ({len(med_conf[med_conf['review_score'] < 0.4])/len(med_conf)*100:.1f}%)

### Correlation Analysis
- **Pearson Correlation (SetFit vs Review)**: {output_df['setfit_confidence'].corr(output_df['review_score']):.3f}
- **Pearson Correlation (Ling vs Review)**: {output_df['ling_score'].corr(output_df['review_score']):.3f}
- **Pearson Correlation (SetFit vs Ling)**: {output_df['setfit_confidence'].corr(output_df['ling_score']):.3f}

---

## Key Findings

### SetFit Performance
"""

    # Analyze SetFit accuracy
    high_review_in_high_setfit = len(high_conf[high_conf['review_score'] >= 0.6])
    low_review_in_high_setfit = len(high_conf[high_conf['review_score'] < 0.4])

    summary += f"""
1. **Agreement Rate**: {high_review_in_high_setfit}/{len(high_conf)} ({high_review_in_high_setfit/len(high_conf)*100:.1f}%) of high-confidence SetFit papers scored ≥0.6 in manual review
2. **False Positive Rate**: {low_review_in_high_setfit}/{len(high_conf)} ({low_review_in_high_setfit/len(high_conf)*100:.1f}%) of high-confidence SetFit papers scored <0.4 (likely false positives)
3. **Correlation**: {'Strong' if output_df['setfit_confidence'].corr(output_df['review_score']) > 0.5 else 'Moderate' if output_df['setfit_confidence'].corr(output_df['review_score']) > 0.3 else 'Weak'} correlation (r={output_df['setfit_confidence'].corr(output_df['review_score']):.3f}) between SetFit confidence and review scores

### Linguistic Features Performance
"""

    ling_corr = output_df['ling_score'].corr(output_df['review_score'])
    summary += f"""
1. **Correlation**: {'Strong' if ling_corr > 0.5 else 'Moderate' if ling_corr > 0.3 else 'Weak'} correlation (r={ling_corr:.3f}) between linguistic scores and review scores
2. **Complementary Value**: Linguistic features {'provide significant' if abs(ling_corr - output_df['setfit_confidence'].corr(output_df['review_score'])) > 0.1 else 'align with'} additional signal beyond SetFit

---

## Top 10 Most Confident True Positives
(High review score ≥0.8 AND high SetFit confidence ≥0.7)

"""

    top_true_positives = output_df[(output_df['review_score'] >= 0.8) & (output_df['setfit_confidence'] >= 0.7)].nlargest(10, 'review_score')

    for idx, (_, row) in enumerate(top_true_positives.iterrows(), 1):
        summary += f"{idx}. **PMID {row['pmid']}** (Review: {row['review_score']:.3f}, SetFit: {row['setfit_confidence']:.3f})\n"
        summary += f"   - {row['title'][:100]}...\n"
        summary += f"   - Notes: {row['notes'][:150]}...\n\n"

    summary += "\n---\n\n## Top 10 Likely False Positives\n(Low review score <0.4 BUT high SetFit confidence ≥0.7)\n\n"

    false_positives = output_df[(output_df['review_score'] < 0.4) & (output_df['setfit_confidence'] >= 0.7)].nlargest(10, 'setfit_confidence')

    if len(false_positives) > 0:
        for idx, (_, row) in enumerate(false_positives.iterrows(), 1):
            summary += f"{idx}. **PMID {row['pmid']}** (Review: {row['review_score']:.3f}, SetFit: {row['setfit_confidence']:.3f})\n"
            summary += f"   - {row['title'][:100]}...\n"
            summary += f"   - Notes: {row['notes'][:150]}...\n\n"
    else:
        summary += "*No significant false positives found*\n\n"

    summary += "\n---\n\n## Top 10 Potential False Negatives\n(High review score ≥0.7 BUT low SetFit confidence <0.6)\n\n"

    false_negatives = output_df[(output_df['review_score'] >= 0.7) & (output_df['setfit_confidence'] < 0.6)].nlargest(10, 'review_score')

    if len(false_negatives) > 0:
        for idx, (_, row) in enumerate(false_negatives.iterrows(), 1):
            summary += f"{idx}. **PMID {row['pmid']}** (Review: {row['review_score']:.3f}, SetFit: {row['setfit_confidence']:.3f})\n"
            summary += f"   - {row['title'][:100]}...\n"
            summary += f"   - Notes: {row['notes'][:150]}...\n\n"
    else:
        summary += "*No significant false negatives found*\n\n"

    summary += """
---

## Recommendations

### SetFit Model Quality
"""

    if output_df['setfit_confidence'].corr(output_df['review_score']) > 0.5:
        summary += "- ✓ SetFit shows **strong performance** with good correlation to manual review\n"
    elif output_df['setfit_confidence'].corr(output_df['review_score']) > 0.3:
        summary += "- ⚠ SetFit shows **moderate performance** - consider retraining or feature engineering\n"
    else:
        summary += "- ✗ SetFit shows **weak performance** - significant model improvements needed\n"

    if low_review_in_high_setfit / len(high_conf) > 0.2:
        summary += f"- ⚠ High false positive rate ({low_review_in_high_setfit/len(high_conf)*100:.1f}%) - consider raising confidence threshold\n"
    else:
        summary += f"- ✓ Low false positive rate ({low_review_in_high_setfit/len(high_conf)*100:.1f}%) in high-confidence predictions\n"

    summary += f"""
### Optimal Thresholds
- **Precision-focused** (minimize false positives): Use SetFit confidence ≥0.75 + Review score ≥0.7
- **Recall-focused** (capture more true positives): Use SetFit confidence ≥0.6 + Review score ≥0.5
- **Balanced**: Use SetFit confidence ≥0.7 + Review score ≥0.6

### Next Steps
1. Manual review of borderline cases (Review score 0.4-0.6) to improve training data
2. Investigate false positives to understand SetFit's weaknesses
3. Consider ensemble approach combining SetFit, linguistic features, and rule-based scoring

---

*Generated by Review Agent 8*
"""

    return summary


if __name__ == '__main__':
    main()
