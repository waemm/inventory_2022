#!/usr/bin/env python3
"""
Merge URL scanner scores back into pipeline dataset.

This script bridges the URL scanner and deduplication phases by adding
scanner quality scores to the papers dataset.

Input:
  - data/union_papers_with_urls.csv (papers with extracted URLs from Script 11)
  - results/gbc_scan_results.csv (URL scan results from scanner)

Output:
  - data/union_papers_with_scanner_scores.csv (enriched with scanner scores)

Scanner scores added:
  - url_scanner_score: Total indicator score (0-500+)
  - url_likelihood: Classification (CRITICAL/HIGH/MEDIUM/LOW/VERY_LOW)
  - url_indicators: List of matching indicators
  - url_scan_status: Scan outcome (success/failed/not_scanned)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Paths
BASE_DIR = Path(__file__).resolve().parents[3]  # Advanced_filtering_pipeline parent
DATA_DIR = BASE_DIR / 'advanced_filtering_pipeline/data'
RESULTS_DIR = BASE_DIR / 'advanced_filtering_pipeline/results'

# Input files
PAPERS_FILE = DATA_DIR / 'union_papers_with_urls.csv'
SCAN_RESULTS_FILE = RESULTS_DIR / 'gbc_scan_results.csv'

# Output file
OUTPUT_FILE = DATA_DIR / 'union_papers_with_scanner_scores.csv'
STATS_FILE = RESULTS_DIR / 'scanner_merge_statistics.txt'

print("="*80)
print("Merging URL Scanner Scores into Pipeline Dataset")
print("="*80)

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n1. Loading datasets...")

# Load papers with URLs
if not PAPERS_FILE.exists():
    print(f"   ❌ ERROR: Papers file not found: {PAPERS_FILE}")
    print(f"   Please run Script 11 (extract_urls.py) first.")
    exit(1)

df_papers = pd.read_csv(PAPERS_FILE)
print(f"   ✓ Loaded papers: {len(df_papers):,} papers")
print(f"   ✓ Papers with URLs: {df_papers['has_resource_url'].sum():,}")

# Load scan results
if not SCAN_RESULTS_FILE.exists():
    print(f"   ⚠️  WARNING: Scan results not found: {SCAN_RESULTS_FILE}")
    print(f"   Creating output without scanner scores.")
    print(f"   Run scanner scripts first to add URL validation scores.")
    has_scan_results = False
else:
    df_scan = pd.read_csv(SCAN_RESULTS_FILE)
    print(f"   ✓ Loaded scan results: {len(df_scan):,} URLs")
    print(f"   ✓ Successfully scanned: {(df_scan['status'] == 'success').sum():,}")
    has_scan_results = True

# ============================================================================
# NORMALIZE URLS FOR MATCHING
# ============================================================================

if has_scan_results:
    print("\n2. Normalizing URLs for matching...")

    def normalize_url(url):
        """Normalize URL for matching (lowercase, strip protocol/www)"""
        if pd.isna(url):
            return ''

        url = str(url).lower().strip()

        # Remove protocol
        url = url.replace('https://', '').replace('http://', '')

        # Remove www prefix
        if url.startswith('www.'):
            url = url[4:]

        # Remove trailing slash
        url = url.rstrip('/')

        return url

    # Normalize URLs in both datasets
    df_papers['resource_url_normalized'] = df_papers['resource_url'].apply(normalize_url)
    df_scan['url_normalized'] = df_scan['url'].apply(normalize_url)

    print(f"   ✓ Normalized {len(df_papers):,} paper URLs")
    print(f"   ✓ Normalized {len(df_scan):,} scan URLs")

# ============================================================================
# MERGE SCANNER SCORES
# ============================================================================

if has_scan_results:
    print("\n3. Merging scanner scores...")

    # Prepare scan results for merge
    scan_cols = {
        'url_normalized': 'resource_url_normalized',
        'total_score': 'url_scanner_score',
        'likelihood': 'url_likelihood',
        'indicators': 'url_indicators',
        'status': 'url_scan_status',
        'error_type': 'url_scan_error'
    }

    df_scan_subset = df_scan[list(scan_cols.keys())].rename(columns=scan_cols)

    # Merge on normalized URL
    df_merged = df_papers.merge(
        df_scan_subset,
        on='resource_url_normalized',
        how='left'
    )

    # Fill missing scanner scores (URLs not scanned)
    df_merged['url_scanner_score'] = df_merged['url_scanner_score'].fillna(0)
    df_merged['url_likelihood'] = df_merged['url_likelihood'].fillna('NOT_SCANNED')
    df_merged['url_scan_status'] = df_merged['url_scan_status'].fillna('not_scanned')

    # Drop normalized URL column (temp column for matching)
    df_merged = df_merged.drop(columns=['resource_url_normalized'])

    print(f"   ✓ Merged scanner scores")
    print(f"   ✓ Matched URLs: {(df_merged['url_scan_status'] == 'success').sum():,}")
    print(f"   ✓ Failed scans: {(df_merged['url_scan_status'] == 'failed').sum():,}")
    print(f"   ✓ Not scanned: {(df_merged['url_scan_status'] == 'not_scanned').sum():,}")

else:
    # No scan results - create placeholder columns
    print("\n3. Creating placeholder scanner columns...")
    df_merged = df_papers.copy()
    df_merged['url_scanner_score'] = 0
    df_merged['url_likelihood'] = 'NOT_SCANNED'
    df_merged['url_scan_status'] = 'not_scanned'
    df_merged['url_indicators'] = ''
    df_merged['url_scan_error'] = ''
    print(f"   ✓ Added placeholder columns (all NOT_SCANNED)")

# ============================================================================
# CALCULATE STATISTICS
# ============================================================================

print("\n4. Calculating statistics...")

stats = {
    'total_papers': len(df_merged),
    'papers_with_urls': df_merged['has_resource_url'].sum(),
    'papers_without_urls': (~df_merged['has_resource_url']).sum(),
}

if has_scan_results:
    stats.update({
        'scanned_success': (df_merged['url_scan_status'] == 'success').sum(),
        'scanned_failed': (df_merged['url_scan_status'] == 'failed').sum(),
        'not_scanned': (df_merged['url_scan_status'] == 'not_scanned').sum(),
        'critical': (df_merged['url_likelihood'] == 'CRITICAL').sum(),
        'high': (df_merged['url_likelihood'] == 'HIGH').sum(),
        'medium': (df_merged['url_likelihood'] == 'MEDIUM').sum(),
        'low': (df_merged['url_likelihood'] == 'LOW').sum(),
        'very_low': (df_merged['url_likelihood'] == 'VERY_LOW').sum(),
        'mean_score': df_merged[df_merged['url_scanner_score'] > 0]['url_scanner_score'].mean(),
        'median_score': df_merged[df_merged['url_scanner_score'] > 0]['url_scanner_score'].median(),
    })

# ============================================================================
# SAVE OUTPUT
# ============================================================================

print("\n5. Saving enriched dataset...")
df_merged.to_csv(OUTPUT_FILE, index=False)
print(f"   ✓ Saved to: {OUTPUT_FILE}")
print(f"   ✓ Shape: {df_merged.shape}")
print(f"   ✓ New columns added: url_scanner_score, url_likelihood, url_scan_status, url_indicators")

# ============================================================================
# SAVE STATISTICS REPORT
# ============================================================================

print("\n6. Generating statistics report...")

with open(STATS_FILE, 'w') as f:
    f.write("="*80 + "\n")
    f.write("URL SCANNER MERGE STATISTICS\n")
    f.write("="*80 + "\n\n")

    f.write(f"Total papers: {stats['total_papers']:,}\n")
    f.write(f"Papers with URLs: {stats['papers_with_urls']:,} ({stats['papers_with_urls']/stats['total_papers']*100:.1f}%)\n")
    f.write(f"Papers without URLs: {stats['papers_without_urls']:,} ({stats['papers_without_urls']/stats['total_papers']*100:.1f}%)\n\n")

    if has_scan_results:
        f.write("="*80 + "\n")
        f.write("SCANNER RESULTS\n")
        f.write("="*80 + "\n\n")

        f.write("Scan Status:\n")
        f.write(f"  Success:      {stats['scanned_success']:>6,} ({stats['scanned_success']/stats['papers_with_urls']*100:>5.1f}% of URLs)\n")
        f.write(f"  Failed:       {stats['scanned_failed']:>6,} ({stats['scanned_failed']/stats['papers_with_urls']*100:>5.1f}% of URLs)\n")
        f.write(f"  Not scanned:  {stats['not_scanned']:>6,}\n\n")

        f.write("URL Quality Classification:\n")
        f.write(f"  CRITICAL:     {stats['critical']:>6,} ({stats['critical']/stats['scanned_success']*100:>5.1f}% of successful scans)\n")
        f.write(f"  HIGH:         {stats['high']:>6,} ({stats['high']/stats['scanned_success']*100:>5.1f}%)\n")
        f.write(f"  MEDIUM:       {stats['medium']:>6,} ({stats['medium']/stats['scanned_success']*100:>5.1f}%)\n")
        f.write(f"  LOW:          {stats['low']:>6,} ({stats['low']/stats['scanned_success']*100:>5.1f}%)\n")
        f.write(f"  VERY_LOW:     {stats['very_low']:>6,} ({stats['very_low']/stats['scanned_success']*100:>5.1f}%)\n\n")

        high_quality = stats['critical'] + stats['high']
        f.write(f"High-quality URLs (CRITICAL + HIGH): {high_quality:,} ({high_quality/stats['scanned_success']*100:.1f}%)\n\n")

        f.write("Scanner Score Statistics:\n")
        f.write(f"  Mean score:   {stats['mean_score']:>6.1f}\n")
        f.write(f"  Median score: {stats['median_score']:>6.0f}\n\n")

    else:
        f.write("="*80 + "\n")
        f.write("NO SCANNER RESULTS AVAILABLE\n")
        f.write("="*80 + "\n\n")
        f.write("Run scanner scripts to generate URL quality scores:\n")
        f.write("  1. scripts/scanning/prepare_gbc_urls.py\n")
        f.write("  2. scripts/scanning/scan_gbc_full.py\n")
        f.write("  3. Re-run this script to merge scores\n")

print(f"   ✓ Saved statistics to: {STATS_FILE}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nPapers processed: {stats['total_papers']:,}")
print(f"Papers with URLs: {stats['papers_with_urls']:,} ({stats['papers_with_urls']/stats['total_papers']*100:.1f}%)")

if has_scan_results:
    print(f"\nSuccessfully scanned: {stats['scanned_success']:,}")
    high_quality = stats['critical'] + stats['high']
    print(f"High-quality URLs: {high_quality:,} ({high_quality/stats['scanned_success']*100:.1f}%)")
    print(f"Mean scanner score: {stats['mean_score']:.1f}")
else:
    print(f"\n⚠️  No scanner results merged (placeholder columns added)")

print(f"\nOutput: {OUTPUT_FILE}")
print(f"Stats:  {STATS_FILE}")

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
