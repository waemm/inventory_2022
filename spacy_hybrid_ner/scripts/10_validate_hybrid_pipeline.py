#!/usr/bin/env python3
"""
Phase 5.2: Validate Hybrid Pipeline
====================================

Validates hybrid pipeline (EntityRuler + Statistical NER) on test set.

Metrics:
- Coverage: 80-85% (improvement over EntityRuler-only)
- Entity sources: 70-75% from EntityRuler, 25-30% from Statistical NER
- Avg entities per paper: 3-5
"""

import spacy
import pandas as pd
from collections import defaultdict
import json
import os
from pathlib import Path

# Configuration
HYBRID_MODEL_PATH = "spacy_hybrid_ner/models/ner_hybrid_v1"
TEST_DATA_PATH = "spacy_hybrid_ner/data/ner_corpus_splits/test.csv"
OUTPUT_DIR = "spacy_hybrid_ner/results/phase5_hybrid_validation"


def validate_hybrid_pipeline(nlp, test_df: pd.DataFrame):
    """
    Validate hybrid pipeline on test set.

    Args:
        nlp: Hybrid pipeline
        test_df: Test papers DataFrame

    Returns:
        Tuple of (metrics dict, predictions list)
    """
    print(f"\nValidating on {len(test_df)} test papers...")

    # Track metrics
    results = {
        'total_papers': len(test_df),
        'total_entities': 0,
        'ruler_entities': 0,
        'statistical_entities': 0,
        'papers_with_entities': 0,
        'papers_with_ruler': 0,
        'papers_with_statistical': 0,
        'entities_per_paper': [],
    }

    all_extractions = []
    unique_ruler_resources = set()
    unique_statistical_resources = set()

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

        ruler_count = 0
        stat_count = 0

        for ent in doc.ents:
            if ent.ent_id_:  # Has canonical ID → from EntityRuler
                ruler_count += 1
                source = 'ruler'
                unique_ruler_resources.add(ent.ent_id_)
            else:  # No ID → from Statistical NER
                stat_count += 1
                source = 'statistical'
                # Use entity text as identifier for statistical entities
                unique_statistical_resources.add(ent.text)

            all_extractions.append({
                'pmid': paper.get('pubmed_id', ''),
                'text': ent.text,
                'label': ent.label_,
                'canonical_id': ent.ent_id_ if ent.ent_id_ else None,
                'source': source,
                'start_char': ent.start_char,
                'end_char': ent.end_char
            })

        results['total_entities'] += len(doc.ents)
        results['ruler_entities'] += ruler_count
        results['statistical_entities'] += stat_count

        if len(doc.ents) > 0:
            results['papers_with_entities'] += 1

        if ruler_count > 0:
            results['papers_with_ruler'] += 1

        if stat_count > 0:
            results['papers_with_statistical'] += 1

        results['entities_per_paper'].append(len(doc.ents))

        # Progress indicator
        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(test_df)} papers...")

    # Calculate statistics
    results['coverage'] = round(results['papers_with_entities'] / results['total_papers'] * 100, 2)
    results['avg_entities_per_paper'] = round(
        sum(results['entities_per_paper']) / len(results['entities_per_paper']), 2
    ) if results['entities_per_paper'] else 0

    results['ruler_percentage'] = round(
        results['ruler_entities'] / results['total_entities'] * 100, 2
    ) if results['total_entities'] > 0 else 0

    results['statistical_percentage'] = round(
        results['statistical_entities'] / results['total_entities'] * 100, 2
    ) if results['total_entities'] > 0 else 0

    results['unique_ruler_resources'] = len(unique_ruler_resources)
    results['unique_statistical_resources'] = len(unique_statistical_resources)

    # Remove detailed list for JSON serialization
    del results['entities_per_paper']

    return results, all_extractions


def print_validation_report(metrics: dict):
    """
    Print validation report.

    Args:
        metrics: Validation metrics dictionary
    """
    print("\n" + "="*70)
    print("HYBRID PIPELINE VALIDATION REPORT (PHASE 5.2)")
    print("="*70)

    print(f"\nTest Set:")
    print(f"  Total papers: {metrics['total_papers']:,}")
    print(f"  Papers with entities: {metrics['papers_with_entities']:,} ({metrics['coverage']:.1f}%)")
    print(f"    - With EntityRuler entities: {metrics['papers_with_ruler']:,}")
    print(f"    - With Statistical NER entities: {metrics['papers_with_statistical']:,}")

    print(f"\nEntity Counts:")
    print(f"  Total entities: {metrics['total_entities']:,}")
    print(f"  Avg per paper: {metrics['avg_entities_per_paper']:.2f}")

    print(f"\nEntity Sources:")
    print(f"  EntityRuler: {metrics['ruler_entities']:,} ({metrics['ruler_percentage']:.1f}%)")
    print(f"  Statistical NER: {metrics['statistical_entities']:,} ({metrics['statistical_percentage']:.1f}%)")

    print(f"\nUnique Resources:")
    print(f"  Known (from EntityRuler): {metrics['unique_ruler_resources']:,}")
    print(f"  Discovered (from Statistical NER): {metrics['unique_statistical_resources']:,}")

    # Target assessment
    print(f"\n" + "-"*70)
    print("TARGET ASSESSMENT:")
    print("-"*70)

    targets = [
        ("Coverage", metrics['coverage'], 80, 85),
        ("Avg entities/paper", metrics['avg_entities_per_paper'], 3, 5),
    ]

    all_met = True
    for name, value, min_target, max_target in targets:
        if min_target <= value <= max_target * 1.5:  # Allow 50% overshoot on max
            status = "✓"
        else:
            status = "~"
            all_met = False
        print(f"{status} {name}: {value:.1f} (Target: {min_target}-{max_target})")

    # Source distribution (informational, not strict target)
    print(f"\nℹ️  Entity Source Distribution (Informational):")
    print(f"   EntityRuler: {metrics['ruler_percentage']:.1f}% (Expected: 70-75%)")
    print(f"   Statistical NER: {metrics['statistical_percentage']:.1f}% (Expected: 25-30%)")

    if all_met:
        print(f"\n✓ All primary targets met!")
    else:
        print(f"\n~ Some targets not met, but hybrid pipeline is functional.")


def save_results(metrics: dict, extractions: list, output_dir: str):
    """
    Save validation results.

    Args:
        metrics: Metrics dictionary
        extractions: Extractions list
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save metrics
    metrics_path = os.path.join(output_dir, 'hybrid_validation_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\n✓ Metrics saved to: {metrics_path}")

    # Save extractions
    extractions_path = os.path.join(output_dir, 'hybrid_extractions.csv')
    pd.DataFrame(extractions).to_csv(extractions_path, index=False)
    print(f"✓ Extractions saved to: {extractions_path}")


def main():
    """Main execution function."""
    print("="*70)
    print("PHASE 5.2: VALIDATE HYBRID PIPELINE")
    print("="*70)

    # Load hybrid pipeline
    print(f"\nLoading hybrid pipeline from: {HYBRID_MODEL_PATH}")
    nlp = spacy.load(HYBRID_MODEL_PATH)
    print(f"  ✓ Loaded pipeline with components: {nlp.pipe_names}")

    # Load test data
    print(f"\nLoading test data from: {TEST_DATA_PATH}")
    test_df = pd.read_csv(TEST_DATA_PATH)
    print(f"  ✓ Loaded {len(test_df):,} test papers")

    # Validate
    metrics, extractions = validate_hybrid_pipeline(nlp, test_df)

    # Print report
    print_validation_report(metrics)

    # Save results
    save_results(metrics, extractions, OUTPUT_DIR)

    print("\n" + "="*70)
    print("✓ PHASE 5.2 COMPLETE")
    print("="*70)
    print(f"\nResults saved to: {OUTPUT_DIR}/")
    print("\nNext steps:")
    print("  - Phase 5.3: Benchmark speed")
    print("  - Phase 5.4: Analyze alias resolution")


if __name__ == "__main__":
    main()
