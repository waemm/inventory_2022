#!/usr/bin/env python3
"""
Manual Validation Study - spaCy Hybrid NER
Validates predictions against known bioresource papers with ground truth.

This script:
1. Loads 125 high-quality papers with known bioresources (ground truth)
2. Runs spaCy Hybrid NER predictions
3. Compares predictions against ground truth
4. Calculates precision, recall, F1 scores
5. Generates detailed validation report

Input: data/validation_sample_100_resources.csv
Output: spacy_hybrid_ner/results/manual_validation_report.json
        spacy_hybrid_ner/results/manual_validation_detailed.csv
"""

import sys
import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ner_predict_spacy import SpacyNERPredictor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_resource_name(name: str) -> str:
    """
    Normalize resource name for matching.
    Handles case, whitespace, and common variations.
    """
    if pd.isna(name) or name is None:
        return ""

    # Convert to lowercase and strip
    normalized = str(name).lower().strip()

    # Remove common suffixes
    suffixes = [' database', ' db', ' resource', ' repository', ' portal']
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()

    # Handle common abbreviations
    abbreviations = {
        'uniprot': 'uniprotkb',
        'pdb': 'protein data bank',
        'genbank': 'ncbi genbank',
        'embl': 'european nucleotide archive',
    }

    normalized = abbreviations.get(normalized, normalized)

    return normalized


def extract_ground_truth_resources(row: pd.Series) -> Set[str]:
    """
    Extract ground truth resource names from a paper row.
    Returns a set of normalized resource names.
    """
    resources = set()

    # Add primary resource name
    if pd.notna(row.get('resource_short_name')):
        resources.add(normalize_resource_name(row['resource_short_name']))

    # Add full resource name
    if pd.notna(row.get('resource_full_name')):
        resources.add(normalize_resource_name(row['resource_full_name']))

    return resources


def calculate_paper_metrics(
    predicted_entities: List[Dict],
    ground_truth: Set[str]
) -> Dict:
    """
    Calculate precision, recall, F1 for a single paper.

    Args:
        predicted_entities: List of predicted entity dicts with 'text' and 'canonical_id'
        ground_truth: Set of normalized ground truth resource names

    Returns:
        Dict with metrics and details
    """
    # Extract predicted resource names (normalized)
    predicted = set()
    for entity in predicted_entities:
        # Use canonical_id if available, otherwise use text
        name = entity.get('canonical_id') or entity.get('text', '')
        normalized = normalize_resource_name(name)
        if normalized:
            predicted.add(normalized)

    # Calculate true positives, false positives, false negatives
    true_positives = predicted.intersection(ground_truth)
    false_positives = predicted - ground_truth
    false_negatives = ground_truth - predicted

    # Calculate metrics
    precision = len(true_positives) / len(predicted) if predicted else 0.0
    recall = len(true_positives) / len(ground_truth) if ground_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'true_positives': list(true_positives),
        'false_positives': list(false_positives),
        'false_negatives': list(false_negatives),
        'predicted_count': len(predicted),
        'ground_truth_count': len(ground_truth),
        'tp_count': len(true_positives),
        'fp_count': len(false_positives),
        'fn_count': len(false_negatives),
        'precision': precision,
        'recall': recall,
        'f1': f1,
    }


def run_validation_study():
    """
    Run manual validation study on 125 high-quality papers.
    """
    logger.info("="*80)
    logger.info("MANUAL VALIDATION STUDY - spaCy Hybrid NER")
    logger.info("="*80)

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    input_csv = project_root / "data" / "validation_sample_100_resources.csv"
    output_dir = project_root / "spacy_hybrid_ner" / "results"
    output_dir.mkdir(exist_ok=True, parents=True)

    report_json = output_dir / "manual_validation_report.json"
    detailed_csv = output_dir / "manual_validation_detailed.csv"

    # Load validation sample
    logger.info(f"\nLoading validation sample from: {input_csv}")
    df = pd.read_csv(input_csv)
    logger.info(f"  Loaded {len(df)} papers")
    logger.info(f"  Unique resources: {df['resource_short_name'].nunique()}")
    logger.info(f"  Global core papers: {df['is_global_core_biodata_resource'].sum()}")

    # Initialize predictor
    logger.info("\nInitializing spaCy Hybrid NER predictor...")
    try:
        predictor = SpacyNERPredictor()
        logger.info("  ✓ Model loaded successfully")
        logger.info(f"  Pipeline: {predictor.nlp.pipe_names}")
    except Exception as e:
        logger.error(f"  ✗ Failed to load model: {e}")
        return

    # Run predictions
    logger.info("\nRunning NER predictions on 125 papers...")
    logger.info("  (This will take 1-3 minutes)")

    # Prepare DataFrame with required columns
    # Note: This validation sample doesn't have abstracts, only titles
    papers_df = df[['pubmed_id', 'title']].copy()

    # Add empty abstract column for compatibility with predictor
    papers_df['abstract'] = ''

    try:
        # Run batch prediction
        predictions = predictor.predict(papers_df, batch_size=32)
        logger.info(f"  ✓ Completed predictions for {len(predictions)} papers")
    except Exception as e:
        logger.error(f"  ✗ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Create predictions lookup by pmid
    predictions_by_pmid = {str(pred['pmid']): pred for pred in predictions}

    # Calculate metrics for each paper
    logger.info("\nCalculating validation metrics...")
    results = []

    for idx, row in df.iterrows():
        pmid = str(row['pubmed_id'])
        ground_truth = extract_ground_truth_resources(row)

        # Get predictions for this paper
        pred = predictions_by_pmid.get(pmid, {})
        predicted_entities = pred.get('entities', [])

        # Calculate metrics
        metrics = calculate_paper_metrics(predicted_entities, ground_truth)

        # Compile result
        result = {
            'pubmed_id': pmid,
            'title': row['title'][:100] + '...' if len(str(row['title'])) > 100 else row['title'],
            'publication_year': row.get('year', ''),
            'resource_short_name': row['resource_short_name'],
            'resource_full_name': row['resource_full_name'],
            'is_global_core': row['is_global_core_biodata_resource'],
            'citation_count': row.get('citation_count', 0),
            **metrics
        }
        results.append(result)

        # Progress indicator
        if (idx + 1) % 25 == 0:
            logger.info(f"  Processed {idx + 1}/{len(df)} papers...")

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    # Calculate aggregate metrics
    logger.info("\nCalculating aggregate metrics...")

    # Paper-level metrics (micro-averaged)
    total_tp = results_df['tp_count'].sum()
    total_fp = results_df['fp_count'].sum()
    total_fn = results_df['fn_count'].sum()

    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) \
               if (micro_precision + micro_recall) > 0 else 0.0

    # Macro-averaged metrics (average across papers)
    macro_precision = results_df['precision'].mean()
    macro_recall = results_df['recall'].mean()
    macro_f1 = results_df['f1'].mean()

    # By global core status
    global_core_df = results_df[results_df['is_global_core'] == 1]
    other_df = results_df[results_df['is_global_core'] == 0]

    # Compile report
    report = {
        'metadata': {
            'study_date': datetime.now().isoformat(),
            'model_type': 'spaCy Hybrid NER (EntityRuler + Statistical NER)',
            'num_papers': len(df),
            'num_unique_resources': df['resource_short_name'].nunique(),
            'num_global_core_papers': int(df['is_global_core_biodata_resource'].sum()),
            'num_other_papers': int((df['is_global_core_biodata_resource'] == 0).sum()),
        },
        'aggregate_metrics': {
            'micro_averaged': {
                'precision': round(micro_precision, 4),
                'recall': round(micro_recall, 4),
                'f1': round(micro_f1, 4),
                'total_true_positives': int(total_tp),
                'total_false_positives': int(total_fp),
                'total_false_negatives': int(total_fn),
            },
            'macro_averaged': {
                'precision': round(macro_precision, 4),
                'recall': round(macro_recall, 4),
                'f1': round(macro_f1, 4),
            },
        },
        'by_paper_type': {
            'global_core': {
                'num_papers': len(global_core_df),
                'precision': round(global_core_df['precision'].mean(), 4),
                'recall': round(global_core_df['recall'].mean(), 4),
                'f1': round(global_core_df['f1'].mean(), 4),
            },
            'other': {
                'num_papers': len(other_df),
                'precision': round(other_df['precision'].mean(), 4),
                'recall': round(other_df['recall'].mean(), 4),
                'f1': round(other_df['f1'].mean(), 4),
            },
        },
        'distribution': {
            'perfect_matches': int((results_df['f1'] == 1.0).sum()),
            'partial_matches': int(((results_df['f1'] > 0) & (results_df['f1'] < 1.0)).sum()),
            'no_matches': int((results_df['f1'] == 0.0).sum()),
        },
        'top_missed_resources': results_df[results_df['fn_count'] > 0]['resource_short_name'].value_counts().head(10).to_dict(),
        'top_false_positive_papers': results_df.nlargest(5, 'fp_count')[['pubmed_id', 'resource_short_name', 'fp_count']].to_dict('records'),
    }

    # Save results
    logger.info(f"\nSaving results...")
    logger.info(f"  JSON report: {report_json}")
    with open(report_json, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"  Detailed CSV: {detailed_csv}")
    results_df.to_csv(detailed_csv, index=False)

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("VALIDATION RESULTS SUMMARY")
    logger.info("="*80)

    logger.info("\n📊 AGGREGATE METRICS (Micro-averaged):")
    logger.info(f"  Precision: {micro_precision:.2%}")
    logger.info(f"  Recall:    {micro_recall:.2%}")
    logger.info(f"  F1 Score:  {micro_f1:.2%}")

    logger.info("\n📊 AGGREGATE METRICS (Macro-averaged):")
    logger.info(f"  Precision: {macro_precision:.2%}")
    logger.info(f"  Recall:    {macro_recall:.2%}")
    logger.info(f"  F1 Score:  {macro_f1:.2%}")

    logger.info("\n📋 BY PAPER TYPE:")
    logger.info(f"  Global Core ({len(global_core_df)} papers):")
    logger.info(f"    Precision: {global_core_df['precision'].mean():.2%}")
    logger.info(f"    Recall:    {global_core_df['recall'].mean():.2%}")
    logger.info(f"    F1 Score:  {global_core_df['f1'].mean():.2%}")

    logger.info(f"\n  Other Papers ({len(other_df)} papers):")
    logger.info(f"    Precision: {other_df['precision'].mean():.2%}")
    logger.info(f"    Recall:    {other_df['recall'].mean():.2%}")
    logger.info(f"    F1 Score:  {other_df['f1'].mean():.2%}")

    logger.info("\n📈 MATCH DISTRIBUTION:")
    logger.info(f"  Perfect matches (F1=1.0):  {report['distribution']['perfect_matches']} papers ({report['distribution']['perfect_matches']/len(df)*100:.1f}%)")
    logger.info(f"  Partial matches (0<F1<1):  {report['distribution']['partial_matches']} papers ({report['distribution']['partial_matches']/len(df)*100:.1f}%)")
    logger.info(f"  No matches (F1=0):         {report['distribution']['no_matches']} papers ({report['distribution']['no_matches']/len(df)*100:.1f}%)")

    logger.info("\n🔍 TOP MISSED RESOURCES (False Negatives):")
    for resource, count in list(report['top_missed_resources'].items())[:5]:
        logger.info(f"  {resource}: {count} papers")

    logger.info("\n" + "="*80)
    logger.info("✓ Validation study complete!")
    logger.info("="*80)


if __name__ == '__main__':
    run_validation_study()
