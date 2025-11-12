#!/usr/bin/env python3
"""
Phase 3.1: Prepare Training Corpus for spaCy NER
=================================================

Splits bioresource papers into train/dev/test sets (70/15/15) for distant supervision.

Input:
  - /Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv
  - Optional: data/metadata/pmc_metadata_enhanced_full.csv

Output:
  - data/ner_corpus_splits/train.csv (70%)
  - data/ner_corpus_splits/dev.csv (15%)
  - data/ner_corpus_splits/test.csv (15%)
  - data/ner_corpus_splits/split_statistics.json

Usage:
    python scripts/06_prepare_training_corpus.py

Author: Claude (Sonnet 4.5)
Date: 2025-11-12
"""

import pandas as pd
import os
import sys
import json
from pathlib import Path
from sklearn.model_selection import train_test_split

# Project paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SPACY_ROOT = SCRIPT_DIR.parent

# Input paths
PAPERS_CSV = Path('/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv')
METADATA_CSV = PROJECT_ROOT / 'data' / 'metadata' / 'pmc_metadata_enhanced_full.csv'

# Output directory
OUTPUT_DIR = SPACY_ROOT / 'data' / 'ner_corpus_splits'


def load_papers():
    """Load bioresource papers from CSV."""
    print(f"\nLoading papers from: {PAPERS_CSV}")

    if not PAPERS_CSV.exists():
        print(f"❌ Error: Papers CSV not found at {PAPERS_CSV}")
        sys.exit(1)

    df = pd.read_csv(PAPERS_CSV)
    print(f"✓ Loaded {len(df)} papers")
    print(f"  Columns: {list(df.columns)}")

    return df


def merge_metadata(df):
    """Merge with enhanced metadata if available."""
    if not METADATA_CSV.exists():
        print(f"\nℹ️  Metadata not found at {METADATA_CSV}")
        print("   Continuing with papers only (title + abstract)")
        return df, False

    print(f"\nMerging with metadata from: {METADATA_CSV}")
    metadata = pd.read_csv(METADATA_CSV)
    print(f"✓ Loaded {len(metadata)} metadata records")

    # Merge on PMID
    # Papers CSV has 'pubmed_id', metadata has 'id'
    df_merged = df.merge(
        metadata,
        left_on='pubmed_id',
        right_on='id',
        how='left',
        suffixes=('', '_meta')
    )

    matched = df_merged['id'].notna().sum()
    print(f"✓ Matched {matched}/{len(df)} papers with metadata ({matched/len(df)*100:.1f}%)")

    return df_merged, True


def prepare_text_field(df):
    """Create 'text' field by concatenating title + abstract."""
    print("\nPreparing text field (title + abstract)...")

    # Check if we have title and abstract columns
    if 'title' not in df.columns:
        print("❌ Error: 'title' column not found")
        sys.exit(1)

    # Handle abstract (may or may not exist)
    if 'abstract' in df.columns:
        # Fill NaN abstracts with empty string
        df['abstract'] = df['abstract'].fillna('')
        df['text'] = df['title'].astype(str) + ' ' + df['abstract'].astype(str)
        has_abstract = (df['abstract'].str.len() > 0).sum()
        print(f"✓ Papers with abstracts: {has_abstract}/{len(df)} ({has_abstract/len(df)*100:.1f}%)")
    else:
        # No abstract column - use title only
        df['text'] = df['title'].astype(str)
        print("ℹ️  No 'abstract' column found - using titles only")

    # Strip whitespace
    df['text'] = df['text'].str.strip()

    return df


def filter_papers(df, min_text_length=50):
    """Filter papers with insufficient text."""
    print(f"\nFiltering papers (min text length: {min_text_length} chars)...")

    initial_count = len(df)
    df = df[df['text'].str.len() >= min_text_length].copy()
    filtered_count = len(df)
    removed = initial_count - filtered_count

    print(f"✓ Kept {filtered_count} papers")
    if removed > 0:
        print(f"  Removed {removed} papers with insufficient text")

    return df


def create_splits(df, test_size=0.30, dev_size=0.50, random_state=42):
    """Split into train/dev/test (70/15/15)."""
    print("\nCreating train/dev/test splits...")

    # First split: train vs (dev+test)
    train, temp = train_test_split(
        df,
        test_size=test_size,  # 30% for dev+test
        random_state=random_state,
        shuffle=True
    )

    # Second split: dev vs test
    dev, test = train_test_split(
        temp,
        test_size=dev_size,  # 50% of temp = 15% of total
        random_state=random_state,
        shuffle=True
    )

    print(f"✓ Train: {len(train)} papers ({len(train)/len(df)*100:.1f}%)")
    print(f"✓ Dev:   {len(dev)} papers ({len(dev)/len(df)*100:.1f}%)")
    print(f"✓ Test:  {len(test)} papers ({len(test)/len(df)*100:.1f}%)")

    return train, dev, test


def save_splits(train, dev, test):
    """Save splits to CSV files."""
    print(f"\nSaving splits to: {OUTPUT_DIR}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save CSV files
    train.to_csv(OUTPUT_DIR / 'train.csv', index=False)
    dev.to_csv(OUTPUT_DIR / 'dev.csv', index=False)
    test.to_csv(OUTPUT_DIR / 'test.csv', index=False)

    print(f"✓ Saved train.csv ({len(train)} papers)")
    print(f"✓ Saved dev.csv ({len(dev)} papers)")
    print(f"✓ Saved test.csv ({len(test)} papers)")

    # Save statistics (convert numpy types to Python types for JSON)
    stats = {
        'total_papers': int(len(train) + len(dev) + len(test)),
        'train_papers': int(len(train)),
        'dev_papers': int(len(dev)),
        'test_papers': int(len(test)),
        'train_pct': float(len(train) / (len(train) + len(dev) + len(test)) * 100),
        'dev_pct': float(len(dev) / (len(train) + len(dev) + len(test)) * 100),
        'test_pct': float(len(test) / (len(train) + len(dev) + len(test)) * 100),
        'text_statistics': {
            'train_avg_length': float(train['text'].str.len().mean()),
            'dev_avg_length': float(dev['text'].str.len().mean()),
            'test_avg_length': float(test['text'].str.len().mean()),
            'train_min_length': int(train['text'].str.len().min()),
            'train_max_length': int(train['text'].str.len().max()),
        }
    }

    stats_path = OUTPUT_DIR / 'split_statistics.json'
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"✓ Saved split_statistics.json")

    return stats


def main():
    """Main execution."""
    print("=" * 70)
    print("Phase 3.1: Prepare Training Corpus for spaCy NER")
    print("=" * 70)

    # Load papers
    df = load_papers()

    # Merge with metadata (optional)
    df, has_metadata = merge_metadata(df)

    # Prepare text field
    df = prepare_text_field(df)

    # Filter papers with insufficient text
    df = filter_papers(df, min_text_length=50)

    # Create splits
    train, dev, test = create_splits(df)

    # Save splits
    stats = save_splits(train, dev, test)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total papers: {stats['total_papers']}")
    print(f"Train: {stats['train_papers']} ({stats['train_pct']:.1f}%)")
    print(f"Dev: {stats['dev_papers']} ({stats['dev_pct']:.1f}%)")
    print(f"Test: {stats['test_papers']} ({stats['test_pct']:.1f}%)")
    print(f"\nAverage text length:")
    print(f"  Train: {stats['text_statistics']['train_avg_length']:.0f} chars")
    print(f"  Dev: {stats['text_statistics']['dev_avg_length']:.0f} chars")
    print(f"  Test: {stats['text_statistics']['test_avg_length']:.0f} chars")
    print("\n✓ Phase 3.1 complete!")
    print(f"\nNext step: Run script 07 (distant supervision annotation)")
    print("=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
