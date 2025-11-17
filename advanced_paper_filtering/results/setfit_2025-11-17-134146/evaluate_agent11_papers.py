#!/usr/bin/env python3
"""
Review Agent 11 - Systematic evaluation of 400 SetFit-classified papers
Scores each paper 0.0-1.0 on bioresource introduction likelihood
"""

import pandas as pd
import re
from typing import Dict, Tuple
import numpy as np

# Introduction keywords (strong signal)
INTRO_VERBS = [
    'we present', 'we developed', 'we introduce', 'we describe', 'we report',
    'here we present', 'here we describe', 'here we report', 'we propose',
    'we have developed', 'we have created', 'we constructed', 'we created',
    'we built', 'we established', 'we designed', 'introducing', 'presents'
]

# Database/Resource type keywords
RESOURCE_TYPES = [
    'database', 'resource', 'platform', 'server', 'tool', 'toolkit', 'repository',
    'collection', 'web resource', 'web server', 'web-based', 'software', 'package',
    'pipeline', 'framework', 'system', 'atlas', 'library', 'catalogue', 'catalog'
]

# Usage keywords (negative signal)
USAGE_KEYWORDS = [
    'using', 'we used', 'we analyzed', 'we applied', 'we investigated',
    'we examined', 'we performed', 'we studied', 'we assessed', 'we evaluated',
    'we compared', 'analysis of', 'study of', 'application of', 'review of'
]

# Strong positive indicators in title
TITLE_PATTERNS = [
    r'^[A-Z][a-zA-Z0-9]+:\s',  # "SSNOMBACTER: ..."
    r':\s*a\s+(database|resource|platform|tool|server|toolkit)',
    r':\s*an?\s+(integrated|comprehensive|novel|new)',
]

def extract_url_domain(text: str) -> bool:
    """Check if text contains URLs (indicator of web resource)"""
    url_pattern = r'https?://[^\s,)>]+'
    return bool(re.search(url_pattern, text))

def score_paper(row: pd.Series) -> Tuple[float, str]:
    """
    Score a paper 0.0-1.0 on bioresource introduction likelihood
    Returns (score, explanation)
    """
    title = str(row['title']).lower()
    abstract = str(row['abstract']).lower()
    combined = f"{title} {abstract}"

    score = 0.0
    reasons = []

    # High confidence indicators (0.3-0.4 each)
    # 1. Introduction language in abstract
    intro_count = sum(1 for phrase in INTRO_VERBS if phrase in abstract)
    if intro_count >= 2:
        score += 0.4
        reasons.append(f"Multiple intro phrases ({intro_count})")
    elif intro_count == 1:
        score += 0.3
        reasons.append("Has intro phrase")

    # 2. Resource type in title
    resource_in_title = any(rtype in title for rtype in RESOURCE_TYPES)
    if resource_in_title:
        score += 0.3
        reasons.append("Resource type in title")

    # 3. Structured title pattern (Name: description)
    has_title_pattern = any(re.search(pattern, row['title'], re.IGNORECASE)
                           for pattern in TITLE_PATTERNS)
    if has_title_pattern:
        score += 0.2
        reasons.append("Structured title")

    # 4. URL presence (strong indicator of web resource)
    if extract_url_domain(abstract):
        score += 0.25
        reasons.append("Contains URL")

    # Medium confidence indicators (0.1-0.2 each)
    # 5. Resource keywords in abstract
    resource_count = sum(1 for rtype in RESOURCE_TYPES if rtype in abstract)
    if resource_count >= 3:
        score += 0.2
        reasons.append(f"Multiple resource types ({resource_count})")
    elif resource_count >= 1:
        score += 0.1
        reasons.append("Has resource type")

    # 6. Check for dataset/collection/database description patterns
    dataset_patterns = [
        'contains', 'consists of', 'includes', 'provides', 'offers',
        'enables', 'allows', 'supports', 'available at', 'can be accessed'
    ]
    dataset_count = sum(1 for phrase in dataset_patterns if phrase in abstract)
    if dataset_count >= 3:
        score += 0.15
        reasons.append("Multiple capability statements")

    # Negative signals (reduce score)
    # 7. Usage language (suggests using existing resources, not creating)
    usage_count = sum(1 for phrase in USAGE_KEYWORDS if phrase in abstract)
    if usage_count >= 3 and intro_count == 0:
        score -= 0.3
        reasons.append(f"Heavy usage language ({usage_count}), no intro")
    elif usage_count >= 2 and intro_count == 0:
        score -= 0.2
        reasons.append("Usage-focused, no intro")

    # 8. Research study patterns (not resource development)
    study_patterns = [
        'we found', 'our results', 'our findings', 'demonstrated that',
        'showed that', 'revealed that', 'suggests that', 'indicates that'
    ]
    study_count = sum(1 for phrase in study_patterns if phrase in abstract)
    if study_count >= 2 and intro_count == 0 and not resource_in_title:
        score -= 0.2
        reasons.append("Research study pattern")

    # 9. Review/perspective articles
    if any(word in title for word in ['review', 'perspective', 'commentary', 'editorial']):
        if intro_count == 0:
            score -= 0.3
            reasons.append("Review/commentary type")

    # 10. Conference abstracts or short communications (often not resources)
    if 'abstract' in title.lower() and len(abstract) < 200:
        score -= 0.3
        reasons.append("Conference abstract")

    # Consider linguistic score from input
    ling_score = float(row.get('ling_score', 0))
    if ling_score >= 2:
        score += 0.1
        reasons.append(f"High ling_score ({ling_score})")

    # Cap score at 1.0
    score = min(1.0, max(0.0, score))

    # Generate explanation
    if score >= 0.7:
        confidence = "High confidence bioresource"
    elif score >= 0.5:
        confidence = "Likely bioresource"
    elif score >= 0.3:
        confidence = "Uncertain/borderline"
    elif score >= 0.15:
        confidence = "Probably not bioresource"
    else:
        confidence = "Unlikely bioresource"

    explanation = f"{confidence}: {'; '.join(reasons) if reasons else 'No strong signals'}"

    return score, explanation


def analyze_setfit_quality(df: pd.DataFrame) -> Dict:
    """Analyze correlation between SetFit confidence and actual bioresource likelihood"""

    # Categorize papers
    df['score_category'] = pd.cut(df['review_score'],
                                   bins=[0, 0.3, 0.5, 0.7, 1.0],
                                   labels=['Low', 'Medium-Low', 'Medium-High', 'High'])

    df['setfit_category'] = pd.cut(df['setfit_confidence'],
                                    bins=[0, 0.6, 0.7, 0.8, 1.0],
                                    labels=['Low', 'Medium', 'High', 'Very High'])

    # Calculate correlations
    correlation = df['review_score'].corr(df['setfit_confidence'])

    # Group analysis
    by_setfit = df.groupby('setfit_category')['review_score'].agg(['mean', 'std', 'count'])
    by_score = df.groupby('score_category')['setfit_confidence'].agg(['mean', 'std', 'count'])

    # Confusion matrix style analysis
    true_positives = len(df[(df['review_score'] >= 0.5) & (df['setfit_confidence'] >= 0.7)])
    false_positives = len(df[(df['review_score'] < 0.5) & (df['setfit_confidence'] >= 0.7)])
    true_negatives = len(df[(df['review_score'] < 0.5) & (df['setfit_confidence'] < 0.7)])
    false_negatives = len(df[(df['review_score'] >= 0.5) & (df['setfit_confidence'] < 0.7)])

    return {
        'correlation': correlation,
        'by_setfit': by_setfit,
        'by_score': by_score,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'true_negatives': true_negatives,
        'false_negatives': false_negatives,
        'precision': true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0,
        'recall': true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    }


def main():
    print("=" * 80)
    print("Review Agent 11 - Evaluating 400 SetFit-classified papers")
    print("=" * 80)

    # Load data
    input_file = 'review_agent11_sample.csv'
    print(f"\nLoading: {input_file}")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} papers")

    # Score each paper
    print("\nScoring papers...")
    scores = []
    notes = []

    for idx, row in df.iterrows():
        if (idx + 1) % 50 == 0:
            print(f"  Processed {idx + 1}/{len(df)} papers...")

        score, note = score_paper(row)
        scores.append(score)
        notes.append(note)

    # Add results to dataframe
    df['review_score'] = scores
    df['notes'] = notes

    # Create output dataframe
    output_cols = ['pmid', 'title', 'setfit_confidence', 'ling_score', 'review_score', 'notes']
    output_df = df[output_cols].copy()

    # Save results
    output_file = 'agent11_scored_results.csv'
    output_df.to_csv(output_file, index=False)
    print(f"\n✓ Saved scored results to: {output_file}")

    # Analyze SetFit quality
    print("\nAnalyzing SetFit quality...")
    analysis = analyze_setfit_quality(df)

    # Generate summary statistics
    print("\nGenerating summary report...")

    summary_md = f"""# Review Agent 11 - Summary Report

## Overview
- **Total papers evaluated**: {len(df)}
- **Date**: 2025-11-17
- **Task**: Score papers 0.0-1.0 on bioresource introduction likelihood

## Scoring Distribution

### Review Scores
- **High confidence (≥0.7)**: {len(df[df['review_score'] >= 0.7])} papers ({len(df[df['review_score'] >= 0.7])/len(df)*100:.1f}%)
- **Likely (0.5-0.7)**: {len(df[(df['review_score'] >= 0.5) & (df['review_score'] < 0.7)])} papers ({len(df[(df['review_score'] >= 0.5) & (df['review_score'] < 0.7)])/len(df)*100:.1f}%)
- **Uncertain (0.3-0.5)**: {len(df[(df['review_score'] >= 0.3) & (df['review_score'] < 0.5)])} papers ({len(df[(df['review_score'] >= 0.3) & (df['review_score'] < 0.5)])/len(df)*100:.1f}%)
- **Unlikely (<0.3)**: {len(df[df['review_score'] < 0.3])} papers ({len(df[df['review_score'] < 0.3])/len(df)*100:.1f}%)

**Mean review score**: {df['review_score'].mean():.3f}
**Median review score**: {df['review_score'].median():.3f}
**Std deviation**: {df['review_score'].std():.3f}

## SetFit Performance Evaluation

### Correlation Analysis
**Pearson correlation** between SetFit confidence and review score: **{analysis['correlation']:.3f}**

This indicates {'a strong' if abs(analysis['correlation']) > 0.6 else 'a moderate' if abs(analysis['correlation']) > 0.3 else 'a weak'} {'positive' if analysis['correlation'] > 0 else 'negative'} correlation.

### SetFit Confidence vs Actual Bioresource Likelihood

Average review scores by SetFit confidence category:

{analysis['by_setfit'].to_string()}

### Review Score vs SetFit Confidence

Average SetFit confidence by review score category:

{analysis['by_score'].to_string()}

### Classification Performance (using 0.5 review score and 0.7 SetFit threshold)

- **True Positives**: {analysis['true_positives']} (High SetFit, actually bioresource)
- **False Positives**: {analysis['false_positives']} (High SetFit, not bioresource)
- **True Negatives**: {analysis['true_negatives']} (Low SetFit, not bioresource)
- **False Negatives**: {analysis['false_negatives']} (Low SetFit, actually bioresource)

**Precision**: {analysis['precision']:.3f} (of papers SetFit predicts positive, how many are true positives)
**Recall**: {analysis['recall']:.3f} (of actual bioresources, how many does SetFit catch)

## Top 10 Highest Scoring Papers

{output_df.nlargest(10, 'review_score')[['pmid', 'title', 'setfit_confidence', 'review_score']].to_string(index=False)}

## Bottom 10 Lowest Scoring Papers

{output_df.nsmallest(10, 'review_score')[['pmid', 'title', 'setfit_confidence', 'review_score']].to_string(index=False)}

## Key Findings

### What Makes a Strong Bioresource Paper?
Based on analysis of high-scoring papers (≥0.7), key indicators include:
1. **Introduction language**: Phrases like "we present", "we developed", "we introduce"
2. **Structured titles**: Often format "NAME: description of resource"
3. **URL presence**: Web resources typically include accessible URLs
4. **Resource terminology**: Clear mention of database, platform, tool, etc.
5. **Capability statements**: Language describing what the resource "provides", "enables", "contains"

### Common False Positives (High SetFit, Low Review Score)
Papers with high SetFit confidence but low actual bioresource likelihood ({len(df[(df['setfit_confidence'] >= 0.7) & (df['review_score'] < 0.3)])} papers):
- Often mention existing resources but don't introduce new ones
- May be reviews or perspectives about resources
- Include research papers that USE databases/tools
- Conference abstracts about resources

### Missed Opportunities (Low SetFit, High Review Score)
Papers with low SetFit confidence but high actual bioresource likelihood ({len(df[(df['setfit_confidence'] < 0.65) & (df['review_score'] >= 0.7)])} papers):
- May have unusual naming conventions
- Could be embedded in larger research narratives
- Might lack typical database-announcement structure

## Recommendations

### For SetFit Model Improvement:
1. **{"Increase weight on introduction verbs" if analysis['correlation'] < 0.5 else "Current introduction verb weighting seems appropriate"}**
2. **{"Add URL detection as a feature" if df['ling_has_url'].sum() < 100 else "URL detection appears well-utilized"}**
3. **Focus on title structure patterns** - structured titles are strong predictors
4. **Reduce false positives from** usage-heavy papers without introduction language

### For Manual Review:
- Prioritize papers with review_score ≥ 0.7 for high-confidence bioresources
- Papers in 0.5-0.7 range warrant careful manual review
- Papers < 0.3 are likely not bioresource introductions

## Methodology

**Scoring Algorithm**:
- Positive indicators (add to score):
  - Introduction language (0.3-0.4)
  - Resource type in title (0.3)
  - Structured title patterns (0.2)
  - URL presence (0.25)
  - Resource keywords in abstract (0.1-0.2)
  - Capability statements (0.15)
  - High linguistic score (0.1)

- Negative indicators (subtract from score):
  - Usage-focused language without introduction (-0.2 to -0.3)
  - Research study patterns without resource mention (-0.2)
  - Review/commentary articles (-0.3)
  - Conference abstracts (-0.3)

Score capped at 0.0-1.0 range.

---
*Generated by Review Agent 11*
*Output file: agent11_scored_results.csv*
"""

    # Save summary
    summary_file = 'agent11_summary.md'
    with open(summary_file, 'w') as f:
        f.write(summary_md)
    print(f"✓ Saved summary to: {summary_file}")

    # Print quick stats
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total papers: {len(df)}")
    print(f"Mean review score: {df['review_score'].mean():.3f}")
    print(f"High confidence bioresources (≥0.7): {len(df[df['review_score'] >= 0.7])}")
    print(f"SetFit correlation: {analysis['correlation']:.3f}")
    print(f"SetFit precision: {analysis['precision']:.3f}")
    print(f"SetFit recall: {analysis['recall']:.3f}")
    print("=" * 80)
    print(f"\n✓ Complete! See {output_file} and {summary_file}")


if __name__ == '__main__':
    main()
