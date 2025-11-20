#!/usr/bin/env python3
"""
SetFit Inference Script - Phase 1
==================================
Run SetFit inference on 20,816 medium-score papers using trained model from Google Drive.

Input:
    - advanced_paper_filtering/results/setfit_2025-11-17-134146/setfit_introduction_classifier/
    - advanced_paper_filtering/data/results/medium_score_papers.csv

Output:
    - results/setfit_inference/setfit_classified_introductions.csv
    - results/setfit_inference/setfit_classified_usage.csv
    - results/setfit_inference/setfit_inference_summary.txt
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def load_setfit_model(model_dir):
    """Load trained SetFit model"""
    from setfit import SetFitModel

    print(f"\nLoading SetFit model from: {model_dir}")
    model = SetFitModel.from_pretrained(model_dir)
    print("✓ Model loaded successfully")
    return model

def load_medium_score_papers(papers_file):
    """Load medium-score papers for classification"""
    print(f"\nLoading medium-score papers from: {papers_file}")
    df = pd.read_csv(papers_file)
    print(f"✓ Loaded {len(df):,} papers")

    # Verify required columns
    required_cols = ['pmid', 'title', 'abstract']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    return df

def prepare_texts(df):
    """Prepare text inputs for SetFit model"""
    print("\nPreparing text inputs...")

    texts = []
    for idx, row in df.iterrows():
        title = str(row['title']) if pd.notna(row['title']) else ""
        abstract = str(row['abstract']) if pd.notna(row['abstract']) else ""

        if abstract:
            text = f"{title}\n\n{abstract}"
        else:
            text = title

        texts.append(text)

    print(f"✓ Prepared {len(texts):,} text inputs")
    return texts

def run_inference(model, texts, batch_size=32):
    """Run SetFit inference on texts"""
    print(f"\nRunning inference on {len(texts):,} papers...")
    print(f"Batch size: {batch_size}")

    start_time = time.time()

    # Get predictions and probabilities
    predictions = model.predict(texts)
    proba = model.predict_proba(texts)

    # Extract confidence scores (probability of positive class)
    if len(proba.shape) == 2:
        # Binary classification: get probability of class 1
        confidence = proba[:, 1]
    else:
        # Single probability per prediction
        confidence = proba

    elapsed = time.time() - start_time
    print(f"✓ Inference complete in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"  Average: {elapsed/len(texts):.3f} sec/paper")

    return predictions, confidence

def categorize_by_confidence(predictions, confidence):
    """Categorize predictions by confidence tier"""
    print("\nCategorizing by confidence tier...")

    # Define tiers
    high_mask = confidence >= 0.70
    medium_mask = (confidence >= 0.60) & (confidence < 0.70)
    low_mask = confidence < 0.60

    # Count by tier and prediction
    intro_high = sum(predictions & high_mask)
    intro_medium = sum(predictions & medium_mask)
    intro_low = sum(predictions & low_mask)

    usage_high = sum((~predictions) & high_mask)
    usage_medium = sum((~predictions) & medium_mask)
    usage_low = sum((~predictions) & low_mask)

    print(f"\n  Introductions:")
    print(f"    High confidence (≥0.70):    {intro_high:,} ({intro_high/len(predictions)*100:.1f}%)")
    print(f"    Medium confidence (0.60-0.69): {intro_medium:,} ({intro_medium/len(predictions)*100:.1f}%)")
    print(f"    Low confidence (<0.60):     {intro_low:,} ({intro_low/len(predictions)*100:.1f}%)")
    print(f"    TOTAL:                      {sum(predictions):,}")

    print(f"\n  Usage:")
    print(f"    High confidence (≥0.70):    {usage_high:,} ({usage_high/len(predictions)*100:.1f}%)")
    print(f"    Medium confidence (0.60-0.69): {usage_medium:,} ({usage_medium/len(predictions)*100:.1f}%)")
    print(f"    Low confidence (<0.60):     {usage_low:,} ({usage_low/len(predictions)*100:.1f}%)")
    print(f"    TOTAL:                      {sum(~predictions):,}")

    return {
        'intro_high': intro_high,
        'intro_medium': intro_medium,
        'intro_low': intro_low,
        'usage_high': usage_high,
        'usage_medium': usage_medium,
        'usage_low': usage_low
    }

def save_results(df, predictions, confidence, output_dir):
    """Save classification results"""
    print(f"\nSaving results to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    # Add predictions to dataframe
    results_df = df.copy()
    results_df['setfit_prediction'] = predictions.astype(int)
    results_df['setfit_confidence'] = confidence

    # Add confidence tier
    conditions = [
        confidence >= 0.70,
        (confidence >= 0.60) & (confidence < 0.70),
        confidence < 0.60
    ]
    choices = ['high', 'medium', 'low']
    results_df['confidence_tier'] = np.select(conditions, choices, default='unknown')

    # Add prediction label
    results_df['prediction_label'] = results_df['setfit_prediction'].map({
        1: 'INTRODUCTION',
        0: 'USAGE'
    })

    # Save introductions
    intro_df = results_df[results_df['setfit_prediction'] == 1].copy()
    intro_df = intro_df.sort_values('setfit_confidence', ascending=False)
    intro_file = os.path.join(output_dir, 'setfit_classified_introductions.csv')
    intro_df.to_csv(intro_file, index=False)
    print(f"✓ Saved {len(intro_df):,} introductions to: {intro_file}")

    # Save usage
    usage_df = results_df[results_df['setfit_prediction'] == 0].copy()
    usage_df = usage_df.sort_values('setfit_confidence', ascending=False)
    usage_file = os.path.join(output_dir, 'setfit_classified_usage.csv')
    usage_df.to_csv(usage_file, index=False)
    print(f"✓ Saved {len(usage_df):,} usage papers to: {usage_file}")

    # Save combined results
    combined_file = os.path.join(output_dir, 'setfit_all_results.csv')
    results_df = results_df.sort_values('setfit_confidence', ascending=False)
    results_df.to_csv(combined_file, index=False)
    print(f"✓ Saved {len(results_df):,} total results to: {combined_file}")

    return intro_df, usage_df, results_df

def generate_summary(stats, intro_df, usage_df, output_dir, elapsed_time):
    """Generate summary report"""
    print("\nGenerating summary report...")

    summary_file = os.path.join(output_dir, 'setfit_inference_summary.txt')

    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("SETFIT INFERENCE SUMMARY - PHASE 1\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total papers classified: {len(intro_df) + len(usage_df):,}\n")
        f.write(f"Inference time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)\n")
        f.write("\n")

        f.write("CLASSIFICATION RESULTS\n")
        f.write("-" * 80 + "\n")
        total = len(intro_df) + len(usage_df)
        f.write(f"Introductions: {len(intro_df):,} ({len(intro_df)/total*100:.1f}%)\n")
        f.write(f"Usage:         {len(usage_df):,} ({len(usage_df)/total*100:.1f}%)\n")
        f.write("\n")

        f.write("CONFIDENCE TIERS - INTRODUCTIONS\n")
        f.write("-" * 80 + "\n")
        f.write(f"High (≥0.70):       {stats['intro_high']:,} ({stats['intro_high']/len(intro_df)*100:.1f}% of intros)\n")
        f.write(f"Medium (0.60-0.69): {stats['intro_medium']:,} ({stats['intro_medium']/len(intro_df)*100:.1f}% of intros)\n")
        f.write(f"Low (<0.60):        {stats['intro_low']:,} ({stats['intro_low']/len(intro_df)*100:.1f}% of intros)\n")
        f.write("\n")

        f.write("CONFIDENCE TIERS - USAGE\n")
        f.write("-" * 80 + "\n")
        f.write(f"High (≥0.70):       {stats['usage_high']:,} ({stats['usage_high']/len(usage_df)*100:.1f}% of usage)\n")
        f.write(f"Medium (0.60-0.69): {stats['usage_medium']:,} ({stats['usage_medium']/len(usage_df)*100:.1f}% of usage)\n")
        f.write(f"Low (<0.60):        {stats['usage_low']:,} ({stats['usage_low']/len(usage_df)*100:.1f}% of usage)\n")
        f.write("\n")

        f.write("CONFIDENCE STATISTICS - INTRODUCTIONS\n")
        f.write("-" * 80 + "\n")
        intro_conf = intro_df['setfit_confidence']
        f.write(f"Mean:   {intro_conf.mean():.4f}\n")
        f.write(f"Median: {intro_conf.median():.4f}\n")
        f.write(f"Min:    {intro_conf.min():.4f}\n")
        f.write(f"Max:    {intro_conf.max():.4f}\n")
        f.write(f"Std:    {intro_conf.std():.4f}\n")
        f.write("\n")

        f.write("CONFIDENCE STATISTICS - USAGE\n")
        f.write("-" * 80 + "\n")
        usage_conf = usage_df['setfit_confidence']
        f.write(f"Mean:   {usage_conf.mean():.4f}\n")
        f.write(f"Median: {usage_conf.median():.4f}\n")
        f.write(f"Min:    {usage_conf.min():.4f}\n")
        f.write(f"Max:    {usage_conf.max():.4f}\n")
        f.write(f"Std:    {usage_conf.std():.4f}\n")
        f.write("\n")

        f.write("=" * 80 + "\n")

    print(f"✓ Summary saved to: {summary_file}")

    # Also print to console
    print("\n" + "=" * 80)
    print("INFERENCE COMPLETE")
    print("=" * 80)
    print(f"Total papers: {total:,}")
    print(f"Introductions: {len(intro_df):,} ({len(intro_df)/total*100:.1f}%)")
    print(f"  High confidence: {stats['intro_high']:,}")
    print(f"  Medium confidence: {stats['intro_medium']:,}")
    print(f"Usage: {len(usage_df):,} ({len(usage_df)/total*100:.1f}%)")
    print(f"  High confidence: {stats['usage_high']:,}")
    print(f"  Medium confidence: {stats['usage_medium']:,}")
    print("=" * 80)

def main():
    """Main execution"""
    start_time = time.time()

    print("=" * 80)
    print("SETFIT INFERENCE - PHASE 1")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    model_dir = base_dir / "advanced_paper_filtering/results/setfit_2025-11-17-134146/setfit_introduction_classifier"
    papers_file = base_dir / "advanced_paper_filtering/data/results/medium_score_papers.csv"
    output_dir = Path(__file__).parent.parent / "results/setfit_inference"

    print(f"Base directory: {base_dir}")
    print(f"Model directory: {model_dir}")
    print(f"Papers file: {papers_file}")
    print(f"Output directory: {output_dir}")

    # Check if model exists
    if not model_dir.exists():
        print(f"\nERROR: Model directory not found: {model_dir}")
        sys.exit(1)

    if not papers_file.exists():
        print(f"\nERROR: Papers file not found: {papers_file}")
        sys.exit(1)

    # Step 1: Load model
    model = load_setfit_model(str(model_dir))

    # Step 2: Load papers
    df = load_medium_score_papers(str(papers_file))

    # Step 3: Prepare texts
    texts = prepare_texts(df)

    # Step 4: Run inference
    predictions, confidence = run_inference(model, texts)

    # Step 5: Categorize by confidence
    stats = categorize_by_confidence(predictions, confidence)

    # Step 6: Save results
    intro_df, usage_df, results_df = save_results(df, predictions, confidence, str(output_dir))

    # Step 7: Generate summary
    elapsed = time.time() - start_time
    generate_summary(stats, intro_df, usage_df, str(output_dir), elapsed)

    print(f"\nTotal execution time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print("\n✓ Phase 1 complete!")

if __name__ == "__main__":
    main()
