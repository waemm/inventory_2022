#!/usr/bin/env python3
"""
Extract All Unique Papers from NER Union

Extracts all unique PMIDs from spaCy Hybrid NER and V2 BERT NER results,
creating the complete union for input to the advanced_paper_filtering pipeline.

Input:
    - validation_spacy_v_BERT/results/phase2/ner/spacy_ner_full_hybrid_results_*.csv
    - validation_spacy_v_BERT/results/phase2/ner/v2_ner_results_*.csv

Output:
    - advanced_paper_filtering/data/input/all_paper_pmids.txt (34,279 PMIDs)

Author: Pipeline Consolidation
Date: 2025-11-20
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
NER_DIR = PROJECT_ROOT / "validation_spacy_v_BERT" / "results" / "phase2" / "ner"
OUTPUT_FILE = PROJECT_ROOT / "advanced_paper_filtering" / "data" / "input" / "all_paper_pmids.txt"


def find_latest_ner_files():
    """Find the most recent spaCy and V2 NER result files."""
    print("=" * 80)
    print("FINDING LATEST NER RESULT FILES")
    print("=" * 80)

    # Find spaCy hybrid files
    spacy_files = list(NER_DIR.glob("spacy_ner_full_hybrid_results_*.csv"))
    if not spacy_files:
        print("ERROR: No spaCy NER files found!")
        print(f"Searched in: {NER_DIR}")
        sys.exit(1)

    spacy_file = max(spacy_files, key=lambda p: p.stat().st_mtime)
    print(f"\nspaCy NER file: {spacy_file.name}")
    print(f"  Size: {spacy_file.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"  Modified: {datetime.fromtimestamp(spacy_file.stat().st_mtime)}")

    # Find V2 BERT files
    v2_files = list(NER_DIR.glob("v2_ner_results_*.csv"))
    if not v2_files:
        print("ERROR: No V2 NER files found!")
        print(f"Searched in: {NER_DIR}")
        sys.exit(1)

    v2_file = max(v2_files, key=lambda p: p.stat().st_mtime)
    print(f"\nV2 NER file: {v2_file.name}")
    print(f"  Size: {v2_file.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"  Modified: {datetime.fromtimestamp(v2_file.stat().st_mtime)}")

    return spacy_file, v2_file


def extract_unique_pmids(spacy_file, v2_file):
    """Extract unique PMIDs from both NER files."""
    print("\n" + "=" * 80)
    print("EXTRACTING UNIQUE PMIDs")
    print("=" * 80)

    # Load spaCy NER results
    print(f"\nLoading spaCy NER results...")
    spacy_df = pd.read_csv(spacy_file)
    print(f"  Loaded: {len(spacy_df):,} entity mentions")

    # Extract unique PMIDs (column is 'ID')
    spacy_pmids = set(spacy_df['ID'].astype(str).unique())
    print(f"  Unique papers: {len(spacy_pmids):,}")

    # Load V2 NER results
    print(f"\nLoading V2 BERT NER results...")
    v2_df = pd.read_csv(v2_file)
    print(f"  Loaded: {len(v2_df):,} entity mentions")

    # Extract unique PMIDs
    v2_pmids = set(v2_df['ID'].astype(str).unique())
    print(f"  Unique papers: {len(v2_pmids):,}")

    # Calculate union
    print("\n" + "-" * 80)
    print("UNION STATISTICS")
    print("-" * 80)

    both = spacy_pmids & v2_pmids
    spacy_only = spacy_pmids - v2_pmids
    v2_only = v2_pmids - spacy_pmids
    union = spacy_pmids | v2_pmids

    print(f"\nspaCy only:     {len(spacy_only):,} papers")
    print(f"V2 only:        {len(v2_only):,} papers")
    print(f"Both (overlap): {len(both):,} papers")
    print(f"Union (total):  {len(union):,} papers")

    return sorted(union, key=int)


def save_pmids(pmids, output_file):
    """Save PMIDs to text file."""
    print("\n" + "=" * 80)
    print("SAVING PMIDs")
    print("=" * 80)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write PMIDs (one per line)
    print(f"\nWriting to: {output_file}")
    with open(output_file, 'w') as f:
        for pmid in pmids:
            f.write(f"{pmid}\n")

    print(f"✓ Saved {len(pmids):,} PMIDs")

    # Verify file
    file_size = output_file.stat().st_size / 1024
    print(f"✓ File size: {file_size:.1f} KB")


def main():
    """Main execution."""
    start_time = datetime.now()

    print("\n" + "=" * 80)
    print("EXTRACT NER UNION PAPERS")
    print("=" * 80)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Find latest NER files
        spacy_file, v2_file = find_latest_ner_files()

        # Extract unique PMIDs
        pmids = extract_unique_pmids(spacy_file, v2_file)

        # Save to output file
        save_pmids(pmids, OUTPUT_FILE)

        # Summary
        end_time = datetime.now()
        duration = end_time - start_time

        print("\n" + "=" * 80)
        print("✅ SUCCESS")
        print("=" * 80)
        print(f"\nCompleted: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration}")
        print(f"\nOutput: {OUTPUT_FILE}")
        print(f"Papers: {len(pmids):,}")

        print("\n" + "=" * 80)
        print("NEXT STEP")
        print("=" * 80)
        print("\nRun the advanced paper filtering pipeline:")
        print("  cd advanced_paper_filtering")
        print("  python scripts/03_linguistic_scoring.py")

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
