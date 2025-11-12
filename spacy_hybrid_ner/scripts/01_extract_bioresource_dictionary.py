#!/usr/bin/env python3
"""
Extract Bioresource Dictionary from CSV (Phase 1.1)

Reads the bioresource papers CSV and extracts unique resource pairs
(short_name, full_name) into a structured dictionary format.

Input:
    - /Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv

Output:
    - data/bioresource_dictionary_raw.json
    - Statistics printed to console

Expected Results:
    - ~3,761 unique resources
    - ~40% with both short + full names
    - ~60% missing full names (to be enriched in Phase 1.2)
"""

import pandas as pd
import json
from pathlib import Path
import sys

# Configuration
INPUT_CSV = '/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv'
OUTPUT_JSON = 'data/bioresource_dictionary_raw.json'


def extract_dictionary(df):
    """
    Extract unique resource pairs from dataframe.

    Args:
        df: DataFrame with 'resource_short_name', 'resource_full_name', 'pubmed_id' columns

    Returns:
        dict: Dictionary with canonical IDs as keys, resource data as values
    """
    dictionary = {}

    for _, row in df.iterrows():
        short = row.get('resource_short_name')
        full = row.get('resource_full_name')
        pmid = row.get('pubmed_id')

        # Skip rows without short name
        if pd.isna(short) or not short:
            continue

        # Use short name as canonical ID
        canonical_id = str(short).strip()

        # Initialize entry if not exists
        if canonical_id not in dictionary:
            dictionary[canonical_id] = {
                'short_name': canonical_id,
                'full_name': None,
                'paper_count': 0,
                'pmids': []
            }

        # Update full name if available (take first non-null value)
        if pd.notna(full) and full and dictionary[canonical_id]['full_name'] is None:
            dictionary[canonical_id]['full_name'] = str(full).strip()

        # Increment paper count and add PMID
        dictionary[canonical_id]['paper_count'] += 1
        if pd.notna(pmid):
            dictionary[canonical_id]['pmids'].append(str(pmid))

    return dictionary


def print_statistics(dictionary):
    """Print summary statistics about the extracted dictionary."""
    total = len(dictionary)
    with_full = sum(1 for v in dictionary.values() if v['full_name'])
    without_full = total - with_full

    print("\n" + "="*60)
    print("BIORESOURCE DICTIONARY EXTRACTION SUMMARY")
    print("="*60)
    print(f"\nTotal unique resources: {total}")
    print(f"With full name: {with_full} ({with_full/total*100:.1f}%)")
    print(f"Missing full name: {without_full} ({without_full/total*100:.1f}%)")

    # Paper count statistics
    paper_counts = [v['paper_count'] for v in dictionary.values()]
    print(f"\nPaper count per resource:")
    print(f"  Min: {min(paper_counts)}")
    print(f"  Max: {max(paper_counts)}")
    print(f"  Avg: {sum(paper_counts)/len(paper_counts):.2f}")

    # Show top 10 most frequent resources
    top_resources = sorted(dictionary.items(), key=lambda x: x[1]['paper_count'], reverse=True)[:10]
    print(f"\nTop 10 most frequent resources:")
    for canonical_id, data in top_resources:
        full = data['full_name'] if data['full_name'] else "N/A"
        print(f"  {canonical_id} ({data['paper_count']} papers): {full}")

    print("="*60 + "\n")


def main():
    """Main execution function."""
    print("="*60)
    print("Phase 1.1: Extract Bioresource Dictionary")
    print("="*60)

    # Check if input file exists
    if not Path(INPUT_CSV).exists():
        print(f"\n❌ ERROR: Input file not found: {INPUT_CSV}")
        print("Please ensure the file exists and the path is correct.")
        sys.exit(1)

    # Load CSV
    print(f"\n📖 Loading CSV from: {INPUT_CSV}")
    try:
        df = pd.read_csv(INPUT_CSV)
        print(f"✓ Loaded {len(df)} rows")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to load CSV: {e}")
        sys.exit(1)

    # Check required columns
    required_cols = ['resource_short_name', 'resource_full_name', 'pubmed_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"\n❌ ERROR: Missing required columns: {missing_cols}")
        print(f"Available columns: {df.columns.tolist()}")
        sys.exit(1)

    # Extract dictionary
    print("\n🔄 Extracting unique resource pairs...")
    dictionary = extract_dictionary(df)

    # Print statistics
    print_statistics(dictionary)

    # Create output directory if needed
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)

    # Save to JSON
    print(f"💾 Saving dictionary to: {OUTPUT_JSON}")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(dictionary, f, indent=2, ensure_ascii=False)

    print(f"✓ Dictionary saved successfully!")
    print(f"\n📊 Next step: Run 02_enrich_missing_fullnames.py to improve coverage")

    return 0


if __name__ == "__main__":
    sys.exit(main())
