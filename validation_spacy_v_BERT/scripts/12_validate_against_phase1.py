#!/usr/bin/env python3
"""
Script 12: Validate NER Pipelines Against Phase 1 Gold Standard

Purpose: Calculate precision/recall metrics for both pipelines vs Phase 1 validation set
Inputs:
    - Phase 1 gold standard: validation_spacy_v_BERT/results/validation/ner/ner_comparison_2025-11-13-iwsisa.csv
    - EntityRuler-first Phase 2 results
    - Statistical-only Phase 2 results

Output:
    - phase1_validation_metrics.json with precision/recall for both pipelines

Usage:
    python validation_spacy_v_BERT/scripts/12_validate_against_phase1.py \
        --entityruler validation_spacy_v_BERT/results/phase2/ner/spacy_ner_results_2025-11-15-h728fg.csv \
        --statistical validation_spacy_v_BERT/results/phase2/ner/spacy_ner_statistical_only_results_<SESSION>.csv

    Or with auto-detection:
    python validation_spacy_v_BERT/scripts/12_validate_against_phase1.py
"""

import pandas as pd
import json
from pathlib import Path
import argparse
import glob


def find_latest_statistical_results():
    """Find the most recent statistical-only results file"""
    pattern = "validation_spacy_v_BERT/results/phase2/ner/spacy_ner_statistical_only_results_*.csv"
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No statistical-only results found matching: {pattern}")
    latest = max(files, key=lambda f: Path(f).stat().st_mtime)
    return latest


def load_phase1_gold_standard():
    """Load Phase 1 validation set gold standard entities"""
    # Try to find the gold standard file
    gold_file = "validation_spacy_v_BERT/results/validation/ner/ner_comparison_2025-11-13-iwsisa.csv"
    sample_file = "validation_spacy_v_BERT/results/validation/sample/validation_sample_with_abstracts_2025-11-13-iwsisa.csv"

    if not Path(gold_file).exists():
        raise FileNotFoundError(f"Phase 1 gold standard not found: {gold_file}")

    df = pd.read_csv(gold_file)

    # Load sample to get publication_id → pubmed_id mapping
    if Path(sample_file).exists():
        df_sample = pd.read_csv(sample_file)
        id_mapping = dict(zip(df_sample['publication_id'], df_sample['pubmed_id']))
    else:
        id_mapping = {}

    # The gold standard is the union of V2 + spaCy from Phase 1 validation
    # Get unique entities (normalized)
    df['mention_normalized'] = df['mention'].str.lower().str.strip()

    # Map publication_id to pubmed_id for Phase 2 comparison
    df['pubmed_id'] = df['paper_id'].map(id_mapping)
    df['paper_entity'] = df['pubmed_id'].astype(str) + '::' + df['mention_normalized']

    # Count unique entities per paper and total
    unique_entities = set(df['paper_entity'].unique())
    papers = df['paper_id'].nunique()

    print(f"\nPhase 1 Gold Standard:")
    print(f"  Papers: {papers}")
    print(f"  Total unique entities: {len(unique_entities)}")
    print(f"  Mapped to PMIDs: {df['pubmed_id'].notna().sum()}/{len(df)}")

    return df, unique_entities, papers, df['pubmed_id'].dropna().unique()


def filter_to_phase1_papers(df, phase1_paper_ids):
    """Filter results to only Phase 1 validation papers"""
    # Convert paper IDs to strings for comparison
    df['ID_str'] = df['ID'].astype(str)
    phase1_ids_str = set(str(p) for p in phase1_paper_ids)

    # Filter
    df_phase1 = df[df['ID_str'].isin(phase1_ids_str)].copy()

    return df_phase1


def calculate_precision_recall(extracted_df, gold_entities, phase1_papers):
    """Calculate precision and recall metrics"""

    if len(extracted_df) == 0:
        return {
            "recall": 0.0,
            "precision": 0.0,
            "f1": 0.0,
            "entities_found": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": len(gold_entities),
            "papers_with_entities": 0,
            "papers_coverage": 0.0
        }

    # Create paper::entity pairs for comparison
    extracted_df['mention_normalized'] = extracted_df['mention'].str.lower().str.strip()
    extracted_df['paper_entity'] = extracted_df['ID'].astype(str) + '::' + extracted_df['mention_normalized']

    extracted_entities = set(extracted_df['paper_entity'].unique())

    # Calculate metrics
    true_positives = len(extracted_entities & gold_entities)
    false_positives = len(extracted_entities - gold_entities)
    false_negatives = len(gold_entities - extracted_entities)

    # Precision and Recall
    precision = true_positives / len(extracted_entities) if len(extracted_entities) > 0 else 0
    recall = true_positives / len(gold_entities) if len(gold_entities) > 0 else 0

    # F1 Score
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Paper coverage
    papers_with_entities = extracted_df['ID'].nunique()
    papers_coverage = papers_with_entities / phase1_papers if phase1_papers > 0 else 0

    return {
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "f1": round(f1, 4),
        "entities_found": len(extracted_entities),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "papers_with_entities": papers_with_entities,
        "papers_coverage": round(papers_coverage, 4)
    }


def calculate_ensemble_metrics(er_df, stat_df, gold_entities, phase1_papers):
    """Calculate metrics for ensemble approach (union of both pipelines)"""

    # Combine both DataFrames
    combined_df = pd.concat([er_df, stat_df], ignore_index=True)

    # Remove duplicates (same paper::entity pairs)
    combined_df['mention_normalized'] = combined_df['mention'].str.lower().str.strip()
    combined_df['paper_entity'] = combined_df['ID'].astype(str) + '::' + combined_df['mention_normalized']
    combined_df = combined_df.drop_duplicates(subset='paper_entity')

    # Calculate metrics
    metrics = calculate_precision_recall(combined_df, gold_entities, phase1_papers)

    return metrics


def main():
    parser = argparse.ArgumentParser(description='Validate NER pipelines against Phase 1 gold standard')
    parser.add_argument('--entityruler', default="validation_spacy_v_BERT/results/phase2/ner/spacy_ner_results_2025-11-15-h728fg.csv",
                        help='EntityRuler-first results CSV')
    parser.add_argument('--statistical', default=None,
                        help='Statistical-only results CSV (auto-detects if not provided)')

    args = parser.parse_args()

    print("=" * 70)
    print("PHASE 1 VALIDATION: NER PIPELINE COMPARISON")
    print("=" * 70)

    # Find statistical results if not provided
    if args.statistical is None:
        print("\nAuto-detecting statistical results...")
        args.statistical = find_latest_statistical_results()
        print(f"✓ Found: {args.statistical}")

    # Verify files exist
    if not Path(args.entityruler).exists():
        raise FileNotFoundError(f"EntityRuler results not found: {args.entityruler}")
    if not Path(args.statistical).exists():
        raise FileNotFoundError(f"Statistical results not found: {args.statistical}")

    print(f"\nInputs:")
    print(f"  EntityRuler: {args.entityruler}")
    print(f"  Statistical: {args.statistical}")

    # Load Phase 1 gold standard
    print("\n" + "=" * 70)
    print("LOADING PHASE 1 GOLD STANDARD")
    print("=" * 70)

    gold_df, gold_entities, phase1_papers, phase1_pmids = load_phase1_gold_standard()
    # Use PMIDs for filtering Phase 2 results (not publication_ids)
    phase1_paper_ids = phase1_pmids

    # Load Phase 2 results
    print("\n" + "=" * 70)
    print("LOADING PHASE 2 RESULTS")
    print("=" * 70)

    print("\nLoading EntityRuler results...")
    df_er_full = pd.read_csv(args.entityruler)
    print(f"✓ Loaded {len(df_er_full):,} entities from {df_er_full['ID'].nunique():,} papers")

    print("\nLoading Statistical results...")
    df_stat_full = pd.read_csv(args.statistical)
    print(f"✓ Loaded {len(df_stat_full):,} entities from {df_stat_full['ID'].nunique():,} papers")

    # Filter to Phase 1 papers only
    print("\n" + "=" * 70)
    print("FILTERING TO PHASE 1 PAPERS")
    print("=" * 70)

    df_er = filter_to_phase1_papers(df_er_full, phase1_paper_ids)
    df_stat = filter_to_phase1_papers(df_stat_full, phase1_paper_ids)

    print(f"\nEntityRuler (Phase 1 subset):")
    print(f"  Entities: {len(df_er):,}")
    print(f"  Papers: {df_er['ID'].nunique()}/{phase1_papers}")

    print(f"\nStatistical (Phase 1 subset):")
    print(f"  Entities: {len(df_stat):,}")
    print(f"  Papers: {df_stat['ID'].nunique()}/{phase1_papers}")

    # Calculate metrics
    print("\n" + "=" * 70)
    print("CALCULATING METRICS")
    print("=" * 70)

    print("\nEntityRuler performance...")
    er_metrics = calculate_precision_recall(df_er, gold_entities, phase1_papers)

    print("\nStatistical performance...")
    stat_metrics = calculate_precision_recall(df_stat, gold_entities, phase1_papers)

    print("\nEnsemble (combined) performance...")
    ensemble_metrics = calculate_ensemble_metrics(df_er, df_stat, gold_entities, phase1_papers)

    # Create full results
    results = {
        "phase1_gold_standard": {
            "total_papers": phase1_papers,
            "total_unique_entities": len(gold_entities),
            "spacy_baseline_recall": 0.760,  # From Phase 1 validation
            "spacy_baseline_entities": 295
        },
        "entityruler_performance": {
            **er_metrics,
            "note": "EntityRuler-first pipeline (session 2025-11-15-h728fg)"
        },
        "statistical_performance": {
            **stat_metrics,
            "note": "Statistical-only pipeline (EntityRuler disabled)"
        },
        "ensemble_performance": {
            **ensemble_metrics,
            "improvement_over_entityruler": {
                "additional_entities": ensemble_metrics['entities_found'] - er_metrics['entities_found'],
                "recall_gain": round(ensemble_metrics['recall'] - er_metrics['recall'], 4),
                "precision_change": round(ensemble_metrics['precision'] - er_metrics['precision'], 4)
            },
            "note": "Union of EntityRuler + Statistical extractions"
        }
    }

    # Save results
    output_dir = Path("validation_spacy_v_BERT/results/phase2/comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "phase1_validation_metrics.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Display results
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    print("\n📊 ENTITYRULER PERFORMANCE:")
    print(f"  Recall: {er_metrics['recall']:.1%} ({er_metrics['true_positives']}/{len(gold_entities)} entities)")
    print(f"  Precision: {er_metrics['precision']:.1%} ({er_metrics['true_positives']}/{er_metrics['entities_found']} correct)")
    print(f"  F1 Score: {er_metrics['f1']:.3f}")
    print(f"  Papers covered: {er_metrics['papers_with_entities']}/{phase1_papers} ({er_metrics['papers_coverage']:.1%})")

    print("\n📊 STATISTICAL PERFORMANCE:")
    print(f"  Recall: {stat_metrics['recall']:.1%} ({stat_metrics['true_positives']}/{len(gold_entities)} entities)")
    print(f"  Precision: {stat_metrics['precision']:.1%} ({stat_metrics['true_positives']}/{stat_metrics['entities_found']} correct)")
    print(f"  F1 Score: {stat_metrics['f1']:.3f}")
    print(f"  Papers covered: {stat_metrics['papers_with_entities']}/{phase1_papers} ({stat_metrics['papers_coverage']:.1%})")

    print("\n📊 ENSEMBLE (COMBINED) PERFORMANCE:")
    print(f"  Recall: {ensemble_metrics['recall']:.1%} ({ensemble_metrics['true_positives']}/{len(gold_entities)} entities)")
    print(f"  Precision: {ensemble_metrics['precision']:.1%} ({ensemble_metrics['true_positives']}/{ensemble_metrics['entities_found']} correct)")
    print(f"  F1 Score: {ensemble_metrics['f1']:.3f}")
    print(f"  Papers covered: {ensemble_metrics['papers_with_entities']}/{phase1_papers} ({ensemble_metrics['papers_coverage']:.1%})")

    print("\n📈 IMPROVEMENT OVER ENTITYRULER:")
    print(f"  Additional entities: {results['ensemble_performance']['improvement_over_entityruler']['additional_entities']:+}")
    print(f"  Recall gain: {results['ensemble_performance']['improvement_over_entityruler']['recall_gain']:+.1%}")
    print(f"  Precision change: {results['ensemble_performance']['improvement_over_entityruler']['precision_change']:+.1%}")

    print("\n" + "=" * 70)
    print("✓ VALIDATION COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
