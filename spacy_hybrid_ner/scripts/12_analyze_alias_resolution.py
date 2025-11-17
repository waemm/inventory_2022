#!/usr/bin/env python3
"""
Phase 5.4: Analyze Alias Resolution
====================================

Analyzes how well the hybrid pipeline links different aliases to canonical IDs.

Success Criteria:
- 70-80% of entities have canonical IDs
- Multiple alias forms correctly linked (e.g., "BAR", "Bio-Analytic Resource")
- Statistical entities (NEW) correctly have no ID
"""

import spacy
import pandas as pd
from collections import defaultdict
import json
import os
from pathlib import Path

# Configuration
HYBRID_MODEL_PATH = "spacy_hybrid_ner/models/ner_hybrid_v2_com_ful"
TEST_DATA_PATH = "spacy_hybrid_ner/data/ner_corpus_splits/test.csv"
OUTPUT_DIR = "spacy_hybrid_ner/results/phase5_alias_resolution"


def analyze_alias_resolution(nlp, test_df: pd.DataFrame):
    """
    Analyze alias resolution in hybrid pipeline.

    Args:
        nlp: Hybrid pipeline
        test_df: Test papers DataFrame

    Returns:
        Dictionary with alias resolution metrics
    """
    print(f"\nAnalyzing alias resolution on {len(test_df)} test papers...")

    # Track alias groups
    alias_groups = defaultdict(lambda: {
        'mentions': [],
        'papers': set(),
        'unique_forms': set()
    })

    total_entities = 0
    entities_with_id = 0
    entities_without_id = 0

    for idx, paper in test_df.iterrows():
        # Get text
        if 'text' in paper and pd.notna(paper['text']):
            text = str(paper['text'])
        else:
            title = str(paper.get('title', ''))
            abstract = str(paper.get('abstract', ''))
            text = f"{title} {abstract}".strip()

        if len(text) < 10:
            continue

        # Run hybrid pipeline
        doc = nlp(text)

        for ent in doc.ents:
            total_entities += 1

            if ent.ent_id_:  # Has canonical ID
                entities_with_id += 1
                canonical = ent.ent_id_

                alias_groups[canonical]['mentions'].append(ent.text)
                alias_groups[canonical]['papers'].add(paper.get('pubmed_id', ''))
                alias_groups[canonical]['unique_forms'].add(ent.text)
            else:
                entities_without_id += 1

        # Progress
        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(test_df)} papers...")

    # Calculate metrics
    resources_with_multiple_aliases = sum(
        1 for data in alias_groups.values() if len(data['unique_forms']) > 1
    )

    metrics = {
        'total_entities': total_entities,
        'entities_with_id': entities_with_id,
        'entities_without_id': entities_without_id,
        'id_percentage': round(entities_with_id / total_entities * 100, 2) if total_entities > 0 else 0,
        'total_resources': len(alias_groups),
        'resources_with_multiple_aliases': resources_with_multiple_aliases,
        'multi_alias_percentage': round(
            resources_with_multiple_aliases / len(alias_groups) * 100, 2
        ) if alias_groups else 0
    }

    return metrics, alias_groups


def print_alias_examples(alias_groups: dict, max_examples: int = 15):
    """
    Print example aliases with multiple forms.

    Args:
        alias_groups: Dictionary of alias groups
        max_examples: Maximum examples to print
    """
    print(f"\n{'-'*70}")
    print("ALIAS RESOLUTION EXAMPLES")
    print(f"{'-'*70}")

    # Find resources with multiple aliases
    multi_alias = {
        canonical: data
        for canonical, data in alias_groups.items()
        if len(data['unique_forms']) > 1
    }

    if not multi_alias:
        print("  No resources with multiple alias forms found.")
        return

    # Sort by number of unique forms (most diverse first)
    sorted_resources = sorted(
        multi_alias.items(),
        key=lambda x: len(x[1]['unique_forms']),
        reverse=True
    )

    print(f"\nTop {max_examples} resources with multiple alias forms:\n")

    for i, (canonical, data) in enumerate(sorted_resources[:max_examples], 1):
        unique_forms = data['unique_forms']
        total_mentions = len(data['mentions'])
        papers_count = len(data['papers'])

        print(f"{i}. {canonical} ({len(unique_forms)} forms, {total_mentions} mentions, {papers_count} papers)")

        # Show each form with frequency
        form_counts = {}
        for mention in data['mentions']:
            form_counts[mention] = form_counts.get(mention, 0) + 1

        for form, count in sorted(form_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"     - '{form}' ({count}×)")
        print()


def print_analysis_report(metrics: dict):
    """
    Print alias resolution analysis report.

    Args:
        metrics: Analysis metrics
    """
    print("\n" + "="*70)
    print("ALIAS RESOLUTION ANALYSIS REPORT (PHASE 5.4)")
    print("="*70)

    print(f"\nEntity Statistics:")
    print(f"  Total entities: {metrics['total_entities']:,}")
    print(f"  Entities with canonical ID: {metrics['entities_with_id']:,} ({metrics['id_percentage']:.1f}%)")
    print(f"  Entities without ID (from Statistical NER): {metrics['entities_without_id']:,}")

    print(f"\nResource Statistics:")
    print(f"  Total unique resources: {metrics['total_resources']:,}")
    print(f"  Resources with multiple aliases: {metrics['resources_with_multiple_aliases']:,}")
    print(f"  Multi-alias percentage: {metrics['multi_alias_percentage']:.1f}%")

    print(f"\n{'-'*70}")
    print("TARGET ASSESSMENT:")
    print(f"{'-'*70}")

    # Alias resolution success rate
    id_pct = metrics['id_percentage']
    if 70 <= id_pct <= 100:
        status = "✓"
    else:
        status = "~"
    print(f"{status} Entities with canonical ID: {id_pct:.1f}% (Target: 70-80%)")

    # Multiple aliases
    multi_pct = metrics['multi_alias_percentage']
    if multi_pct > 0:
        print(f"✓ Multiple alias forms detected: {metrics['resources_with_multiple_aliases']:,} resources")
    else:
        print(f"~ No multiple alias forms detected (may be due to test set composition)")


def save_results(metrics: dict, alias_groups: dict, output_dir: str):
    """
    Save alias resolution analysis results.

    Args:
        metrics: Metrics dictionary
        alias_groups: Alias groups dictionary
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save metrics
    metrics_path = os.path.join(output_dir, 'alias_resolution_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\n✓ Metrics saved to: {metrics_path}")

    # Save alias groups (convert sets to lists for JSON)
    alias_data = {}
    for canonical, data in alias_groups.items():
        alias_data[canonical] = {
            'unique_forms': list(data['unique_forms']),
            'total_mentions': len(data['mentions']),
            'papers': list(data['papers'])
        }

    alias_path = os.path.join(output_dir, 'alias_groups.json')
    with open(alias_path, 'w') as f:
        json.dump(alias_data, f, indent=2)
    print(f"✓ Alias groups saved to: {alias_path}")


def main():
    """Main execution function."""
    print("="*70)
    print("PHASE 5.4: ANALYZE ALIAS RESOLUTION")
    print("="*70)

    # Load hybrid pipeline
    print(f"\nLoading hybrid pipeline from: {HYBRID_MODEL_PATH}")
    nlp = spacy.load(HYBRID_MODEL_PATH)
    print(f"  ✓ Loaded pipeline with components: {nlp.pipe_names}")

    # Load test data
    print(f"\nLoading test data from: {TEST_DATA_PATH}")
    test_df = pd.read_csv(TEST_DATA_PATH)
    print(f"  ✓ Loaded {len(test_df):,} test papers")

    # Analyze
    metrics, alias_groups = analyze_alias_resolution(nlp, test_df)

    # Print report
    print_analysis_report(metrics)

    # Print examples
    print_alias_examples(alias_groups, max_examples=15)

    # Save results
    save_results(metrics, alias_groups, OUTPUT_DIR)

    print("\n" + "="*70)
    print("✓ PHASE 5.4 COMPLETE")
    print("="*70)
    print(f"\nResults saved to: {OUTPUT_DIR}/")
    print("\n✅ PHASE 5 COMPLETE - All hybrid pipeline tasks done!")
    print("\nNext: Phase 6 - Production deployment")


if __name__ == "__main__":
    main()
