#!/usr/bin/env python3
"""
Consolidate all 22 chunk review files into final outputs.
Generates:
  1. consolidated_full_review.csv - ALL papers from all 22 chunks
  2. consolidated_fp_only.csv - Only false positives
  3. consolidated_bioresources.csv - Only true bioresources
"""

import csv
import os
import json
from pathlib import Path
from collections import defaultdict

# Paths
AGENT_REVIEWS_DIR = Path("/Users/warren/development/GBC/inventory_2022/false_positive_analysis/agent_reviews")
OUTPUT_DIR = Path("/Users/warren/development/GBC/inventory_2022/false_positive_analysis")

# Expected columns
EXPECTED_COLUMNS = ['pmid', 'title', 'has_url', 'is_false_positive', 'confidence', 'reason', 'database_name', 'long_database_name']

def consolidate_reviews():
    """Consolidate all chunk review files."""

    # Collect all chunk files (chunks 1-22)
    chunk_files = sorted(AGENT_REVIEWS_DIR.glob("chunk_*_review_v3.csv"))

    print(f"Found {len(chunk_files)} chunk review files")
    print("Files to process:")
    for f in chunk_files:
        print(f"  - {f.name}")
    print()

    # Storage for all records
    all_records = []
    false_positives = []
    bioresources = []

    # Statistics
    total_papers = 0
    fp_count = 0
    bioresource_count = 0
    errors = []
    chunk_stats = []

    # Process each chunk file
    for chunk_file in chunk_files:
        chunk_name = chunk_file.name
        print(f"Processing {chunk_name}...", end=" ")

        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Verify columns
                if reader.fieldnames != EXPECTED_COLUMNS:
                    print(f"\nWARNING: Column mismatch in {chunk_name}")
                    print(f"  Expected: {EXPECTED_COLUMNS}")
                    print(f"  Found: {reader.fieldnames}")

                chunk_papers = 0
                chunk_fp = 0
                chunk_bio = 0

                for row in reader:
                    # Add to all records
                    all_records.append(row)
                    chunk_papers += 1

                    # Check if false positive
                    is_fp = row.get('is_false_positive', '').strip().upper()
                    if is_fp == 'Y':
                        false_positives.append(row)
                        chunk_fp += 1
                        fp_count += 1
                    else:
                        bioresources.append(row)
                        chunk_bio += 1
                        bioresource_count += 1

                total_papers += chunk_papers
                chunk_fp_pct = (chunk_fp / chunk_papers * 100) if chunk_papers > 0 else 0

                # Extract chunk number from filename
                chunk_num = int(chunk_name.split('_')[1])
                chunk_stats.append({
                    'chunk': chunk_num,
                    'total': chunk_papers,
                    'false_positives': chunk_fp,
                    'bioresources': chunk_bio,
                    'fp_percentage': chunk_fp_pct
                })

                print(f"{chunk_papers} papers ({chunk_fp} FP, {chunk_bio} bio, {chunk_fp_pct:.1f}% FP)")

        except Exception as e:
            error_msg = f"Error processing {chunk_name}: {str(e)}"
            errors.append(error_msg)
            print(f"\nERROR: {error_msg}")

    print(f"\n{'='*80}")
    print(f"OVERALL STATISTICS")
    print(f"{'='*80}")
    overall_fp_pct = (fp_count / total_papers * 100) if total_papers > 0 else 0
    print(f"Total papers processed: {total_papers:,}")
    print(f"False positives: {fp_count:,} ({overall_fp_pct:.1f}%)")
    print(f"True bioresources: {bioresource_count:,} ({100-overall_fp_pct:.1f}%)")
    print()

    # Check for duplicates
    pmids = [r['pmid'] for r in all_records]
    duplicates = len(pmids) - len(set(pmids))
    if duplicates > 0:
        print(f"WARNING: Found {duplicates} duplicate PMIDs")
        print()

    # Write output files
    print(f"{'='*80}")
    print("GENERATING OUTPUT FILES")
    print(f"{'='*80}")

    # 1. Full consolidated file
    full_output = OUTPUT_DIR / "consolidated_full_review.csv"
    print(f"1. Writing {full_output.name}...", end=" ")
    with open(full_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_records)
    print(f"✓ {len(all_records):,} rows")

    # 2. False positives only
    fp_output = OUTPUT_DIR / "consolidated_fp_only.csv"
    print(f"2. Writing {fp_output.name}...", end=" ")
    with open(fp_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(false_positives)
    print(f"✓ {len(false_positives):,} rows")

    # 3. True bioresources only
    bio_output = OUTPUT_DIR / "consolidated_bioresources.csv"
    print(f"3. Writing {bio_output.name}...", end=" ")
    with open(bio_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(bioresources)
    print(f"✓ {len(bioresources):,} rows")
    print()

    # Per-chunk statistics
    print(f"{'='*80}")
    print("PER-CHUNK STATISTICS")
    print(f"{'='*80}")
    print()
    print(f"{'Chunk':<8} {'Total':<8} {'FP':<8} {'Bio':<8} {'FP %':<8}")
    print("-" * 50)

    # Sort chunk stats by chunk number
    chunk_stats.sort(key=lambda x: x['chunk'])
    for stat in chunk_stats:
        print(f"{stat['chunk']:02d}       "
              f"{stat['total']:<8} "
              f"{stat['false_positives']:<8} "
              f"{stat['bioresources']:<8} "
              f"{stat['fp_percentage']:<8.1f}")

    print("-" * 50)
    print(f"{'TOTAL':<8} {total_papers:<8} {fp_count:<8} {bioresource_count:<8} {overall_fp_pct:<8.1f}")
    print()

    # Save statistics as JSON
    stats_output = {
        'total_papers': total_papers,
        'false_positives': fp_count,
        'true_bioresources': bioresource_count,
        'fp_percentage': overall_fp_pct,
        'chunks_processed': len(chunk_stats),
        'chunk_details': chunk_stats
    }

    stats_file = OUTPUT_DIR / "consolidation_statistics.json"
    print(f"Saving statistics to {stats_file.name}...")
    with open(stats_file, 'w') as f:
        json.dump(stats_output, f, indent=2)
    print()

    # Data quality checks
    print(f"{'='*80}")
    print("DATA QUALITY CHECKS")
    print(f"{'='*80}")

    # Check for missing database names in bioresources
    bio_with_db = sum(1 for r in bioresources if r.get('database_name', '').strip())
    bio_without_db = len(bioresources) - bio_with_db
    print(f"\nBioresources with database_name: {bio_with_db:,} / {len(bioresources):,}")
    print(f"Bioresources without database_name: {bio_without_db:,} / {len(bioresources):,}")
    if bio_without_db > 0:
        pct = (bio_without_db / len(bioresources) * 100) if len(bioresources) > 0 else 0
        print(f"  WARNING: {pct:.1f}% of bioresources missing database names!")

    # Check has_url distribution
    has_url_counts = defaultdict(int)
    for r in all_records:
        has_url_counts[r.get('has_url', '')] += 1
    print(f"\nhas_url distribution:")
    for val, count in sorted(has_url_counts.items()):
        print(f"  '{val}': {count:,}")

    # Check confidence distribution
    conf_counts = defaultdict(int)
    for r in all_records:
        conf_counts[r.get('confidence', '')] += 1
    print(f"\nconfidence distribution:")
    for val, count in sorted(conf_counts.items()):
        print(f"  '{val}': {count:,}")

    if errors:
        print(f"\n{'='*80}")
        print("ERRORS ENCOUNTERED:")
        print(f"{'='*80}")
        for error in errors:
            print(f"  - {error}")
        print()

    print(f"{'='*80}")
    print("CONSOLIDATION COMPLETE")
    print(f"{'='*80}")
    print()
    print("Output files created:")
    print(f"  1. consolidated_full_review.csv ({total_papers:,} rows)")
    print(f"  2. consolidated_fp_only.csv ({fp_count:,} rows)")
    print(f"  3. consolidated_bioresources.csv ({bioresource_count:,} rows)")
    print(f"  4. consolidation_statistics.json")
    print()

    return {
        'total_papers': total_papers,
        'fp_count': fp_count,
        'bioresource_count': bioresource_count,
        'full_output': str(full_output),
        'fp_output': str(fp_output),
        'bio_output': str(bio_output),
        'stats_file': str(stats_file),
        'errors': errors,
        'chunk_stats': chunk_stats
    }

if __name__ == "__main__":
    results = consolidate_reviews()
