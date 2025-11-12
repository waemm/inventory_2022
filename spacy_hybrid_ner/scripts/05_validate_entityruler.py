#!/usr/bin/env python3
"""
Validate EntityRuler on Bioresource Papers (Phase 2.3)

Validates the EntityRuler pipeline on a sample of real papers to measure:
1. Coverage: % of papers with at least one entity extracted
2. Precision: % of extractions that are correct (via manual review sample)
3. Alias resolution: % of entities with canonical IDs

Input:
    - data/patterns.jsonl
    - /Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv

Output:
    - results/phase2_entityruler_validation.json
    - data/entityruler_precision_review.csv (sample for manual annotation)

Target Metrics:
    - Coverage: 70-80% (limited by dictionary coverage)
    - Precision: >95% (high precision expected for rule-based)
    - Alias Resolution: 100% (all EntityRuler extractions have IDs)
"""

import spacy
import pandas as pd
import json
import random
from pathlib import Path
import sys
from collections import Counter


# Configuration
PATTERNS_FILE = 'data/patterns.jsonl'
INPUT_CSV = '/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv'
OUTPUT_JSON = 'results/phase2_entityruler_validation.json'
OUTPUT_REVIEW = 'data/entityruler_precision_review.csv'
SAMPLE_SIZE = 100  # Number of papers to sample
REVIEW_SAMPLE = 50  # Number of extractions for manual precision review


def validate_on_papers(nlp, df, sample_size):
    """
    Validate EntityRuler on a sample of papers.

    Args:
        nlp: spaCy pipeline with EntityRuler
        df: DataFrame with papers
        sample_size: Number of papers to sample

    Returns:
        list: Results for each paper
    """
    # Sample papers
    if len(df) > sample_size:
        sample = df.sample(n=sample_size, random_state=42)
    else:
        sample = df

    print(f"\n🔄 Processing {len(sample)} papers...")

    results = []
    for idx, (_, paper) in enumerate(sample.iterrows(), 1):
        # Concatenate title + abstract with NaN handling
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')

        # Handle NaN values properly
        if pd.isna(title):
            title = ''
        else:
            title = str(title)

        if pd.isna(abstract):
            abstract = ''
        else:
            abstract = str(abstract)

        text = f"{title} {abstract}".strip()

        if len(text) < 10:
            continue

        # Run EntityRuler
        doc = nlp(text)

        # Extract entities
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'canonical_id': ent.ent_id_,
                'start': ent.start_char,
                'end': ent.end_char
            })

        results.append({
            'pmid': paper.get('pubmed_id'),
            'resource_short_name': paper.get('resource_short_name'),
            'resource_full_name': paper.get('resource_full_name'),
            'entities_found': len(entities),
            'entities': entities
        })

        if idx % 20 == 0:
            print(f"  Progress: {idx}/{len(sample)} ({idx/len(sample)*100:.1f}%)")

    return results


def calculate_metrics(results):
    """Calculate validation metrics."""
    total_papers = len(results)
    papers_with_entities = sum(1 for r in results if r['entities_found'] > 0)
    total_entities = sum(r['entities_found'] for r in results)

    # Coverage
    coverage = papers_with_entities / total_papers if total_papers > 0 else 0

    # Average entities per paper
    avg_entities = total_entities / total_papers if total_papers > 0 else 0

    # Entities with canonical IDs (should be 100% for EntityRuler)
    all_entities = [ent for r in results for ent in r['entities']]
    entities_with_id = sum(1 for ent in all_entities
                           if ent.get('canonical_id') is not None and ent['canonical_id'] != '')
    id_coverage = entities_with_id / len(all_entities) if all_entities else 1.0  # Should be 100%

    # Entity label distribution
    label_dist = Counter(ent['label'] for ent in all_entities)

    # Most frequent resources
    resource_dist = Counter(ent['canonical_id'] for ent in all_entities)

    metrics = {
        'total_papers': total_papers,
        'papers_with_entities': papers_with_entities,
        'coverage': coverage,
        'total_entities': total_entities,
        'avg_entities_per_paper': avg_entities,
        'entities_with_canonical_id': entities_with_id,
        'canonical_id_coverage': id_coverage,
        'label_distribution': dict(label_dist),
        'top_10_resources': dict(resource_dist.most_common(10))
    }

    return metrics


def create_precision_review_sample(results, review_sample):
    """Create sample of extractions for manual precision review."""
    # Collect all entities
    all_entities = []
    for result in results:
        for ent in result['entities']:
            all_entities.append({
                'pmid': result['pmid'],
                'text': ent['text'],
                'canonical_id': ent['canonical_id'],
                'correct': ''  # To be filled manually
            })

    # Sample for review
    if len(all_entities) > review_sample:
        review = random.sample(all_entities, review_sample)
    else:
        review = all_entities

    return review


def print_metrics(metrics):
    """Print metrics in a readable format."""
    print("\n" + "="*60)
    print("VALIDATION METRICS")
    print("="*60)

    print(f"\n📊 Coverage:")
    print(f"  Total papers: {metrics['total_papers']}")
    print(f"  Papers with entities: {metrics['papers_with_entities']}")
    print(f"  Coverage: {metrics['coverage']*100:.1f}%")

    print(f"\n📊 Entity Statistics:")
    print(f"  Total entities: {metrics['total_entities']}")
    print(f"  Avg entities per paper: {metrics['avg_entities_per_paper']:.2f}")

    print(f"\n📊 Alias Resolution:")
    print(f"  Entities with canonical ID: {metrics['entities_with_canonical_id']}/{metrics['total_entities']}")
    print(f"  ID coverage: {metrics['canonical_id_coverage']*100:.1f}%")

    print(f"\n📊 Label Distribution:")
    for label, count in metrics['label_distribution'].items():
        print(f"  {label}: {count}")

    print(f"\n📊 Top 10 Most Frequent Resources:")
    for resource, count in metrics['top_10_resources'].items():
        print(f"  {resource}: {count}")

    print("="*60)

    # Evaluation
    print("\n🎯 Evaluation:")

    coverage_ok = metrics['coverage'] >= 0.70
    id_coverage_ok = metrics['canonical_id_coverage'] == 1.0  # EntityRuler must be 100%

    print(f"  Coverage (target: ≥70%): {'✓ PASS' if coverage_ok else '✗ FAIL'} ({metrics['coverage']*100:.1f}%)")
    print(f"  ID Coverage (target: 100%): {'✓ PASS' if id_coverage_ok else '✗ FAIL'} ({metrics['canonical_id_coverage']*100:.1f}%)")

    if not coverage_ok:
        print("\n⚠️  Coverage below target. This is expected if dictionary is incomplete.")
        print("   Consider running Phase 1.2 again with more patterns.")

    return coverage_ok and id_coverage_ok


def main():
    """Main execution function."""
    print("="*60)
    print("Phase 2.3: Validate EntityRuler on Real Papers")
    print("="*60)

    # Check files exist
    if not Path(PATTERNS_FILE).exists():
        print(f"\n❌ ERROR: Patterns file not found: {PATTERNS_FILE}")
        sys.exit(1)

    if not Path(INPUT_CSV).exists():
        print(f"\n❌ ERROR: CSV file not found: {INPUT_CSV}")
        sys.exit(1)

    # Build pipeline
    print(f"\n🔧 Building EntityRuler pipeline...")
    try:
        nlp = spacy.blank("en")
        ruler = nlp.add_pipe("entity_ruler")
        ruler.from_disk(PATTERNS_FILE)
        print(f"✓ Loaded {len(ruler.patterns)} patterns")
    except Exception as e:
        print(f"❌ ERROR: Failed to build pipeline: {e}")
        sys.exit(1)

    # Load papers
    print(f"\n📖 Loading papers from: {INPUT_CSV}")
    try:
        df = pd.read_csv(INPUT_CSV)
        print(f"✓ Loaded {len(df)} papers")
    except Exception as e:
        print(f"❌ ERROR: Failed to load CSV: {e}")
        sys.exit(1)

    # Validate on sample
    results = validate_on_papers(nlp, df, SAMPLE_SIZE)
    print(f"✓ Processed {len(results)} papers")

    # Calculate metrics
    print("\n📊 Calculating metrics...")
    metrics = calculate_metrics(results)

    # Print metrics
    passed = print_metrics(metrics)

    # Save results
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    print(f"\n💾 Saving results to: {OUTPUT_JSON}")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print("✓ Results saved!")

    # Create precision review sample
    print(f"\n📝 Creating precision review sample...")
    review_sample = create_precision_review_sample(results, REVIEW_SAMPLE)

    Path(OUTPUT_REVIEW).parent.mkdir(parents=True, exist_ok=True)
    print(f"💾 Saving review sample to: {OUTPUT_REVIEW}")
    pd.DataFrame(review_sample).to_csv(OUTPUT_REVIEW, index=False)
    print(f"✓ Saved {len(review_sample)} extractions for manual review")

    print(f"\n📋 Manual Review Instructions:")
    print(f"  1. Open: {OUTPUT_REVIEW}")
    print(f"  2. Review each extraction")
    print(f"  3. Fill 'correct' column: 1 (correct) or 0 (incorrect)")
    print(f"  4. Calculate precision: (sum of correct) / {len(review_sample)}")
    print(f"  5. Target precision: >95%")

    if passed:
        print(f"\n🎉 Validation passed! EntityRuler meets target metrics.")
        print(f"\n📊 Next step: Proceed to Phase 3 (Distant Supervision Training Data)")
    else:
        print(f"\n⚠️  Some metrics below target. Review and improve if needed.")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
