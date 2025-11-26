#!/usr/bin/env python3
"""
URL Scanning for Set C (Union)

Scans all URLs in Set C using the bioresource_url_scanner and adds
validation columns to the dataset.

Created: 2025-11-20
Updated: 2025-11-21 (Added session support)
Estimated time: 75-90 minutes for full scan
"""

import argparse
import pandas as pd
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Scan URLs in Set C')
parser.add_argument('--session-id', type=str, required=False,
                    help='Session ID for scanner output matching')
parser.add_argument('--session-dir', type=str, required=False,
                    help='Session directory for inputs/outputs')
args = parser.parse_args()

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
SCANNER_DIR = BASE_DIR / 'bioresource_url_scanner'
SCANNER_DATA_DIR = SCANNER_DIR / 'data'

# Input/output paths - use session directory if provided
if args.session_dir:
    SESSION_DIR = Path(args.session_dir)
    INPUT_FILE = SESSION_DIR / 'deduplicated' / 'set_c_union_dedup.csv'
    RESULTS_DIR = SESSION_DIR / 'url_scanned'
else:
    # Legacy paths
    DEDUP_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/results/deduplicated'
    INPUT_FILE = DEDUP_DIR / 'set_c_union_dedup.csv'
    RESULTS_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/results/url_scanned'

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Output files
OUTPUT_FILE = RESULTS_DIR / 'set_c_with_url_scan.csv'
STATS_FILE = RESULTS_DIR / 'url_scan_statistics.txt'

# Scanner input file - use session ID if provided
if args.session_id:
    URL_PREP_FILE = SCANNER_DATA_DIR / f'set_c_urls_{args.session_id}.csv'
else:
    URL_PREP_FILE = SCANNER_DATA_DIR / 'set_c_urls.csv'

print("="*80)
print("URL SCANNING FOR SET C (UNION)")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
if args.session_id:
    print(f"Session: {args.session_id}")
if args.session_dir:
    print(f"Output directory: {RESULTS_DIR}")
print()

# ============================================================================
# STEP 1: LOAD SET C
# ============================================================================

print("1. Loading Set C...")
df_c = pd.read_csv(INPUT_FILE)
print(f"   Total resources: {len(df_c)}")

# Check for resource URLs
urls_present = df_c['resource_url'].notna().sum()
print(f"   Resources with URLs: {urls_present}")

# ============================================================================
# STEP 2: PREPARE URLS FOR SCANNER
# ============================================================================

print("\n2. Preparing URLs for scanner...")

# Create URL dataset for scanner
url_data = df_c[df_c['resource_url'].notna()][['pmid', 'resource_url', 'primary_entity_long', 'primary_entity_short']].copy()
url_data = url_data.rename(columns={
    'pmid': 'id',
    'resource_url': 'url',
    'primary_entity_long': 'entity_long',
    'primary_entity_short': 'entity_short'
})

# Add domain column (required by scanner)
from urllib.parse import urlparse
url_data['domain'] = url_data['url'].apply(lambda x: urlparse(str(x)).netloc if pd.notna(x) else '')

# Save for scanner
url_data.to_csv(URL_PREP_FILE, index=False)
print(f"   Prepared {len(url_data)} URLs")
print(f"   Saved to: {URL_PREP_FILE}")

# ============================================================================
# STEP 3: RUN URL SCANNER
# ============================================================================

print("\n3. Running URL scanner...")
print(f"   This will take 75-90 minutes for ~{len(url_data)} URLs")
print(f"   Scanner: {SCANNER_DIR / 'scripts/scan_gbc_full.py'}")

# Copy prepared file to scanner's expected location
scanner_input = SCANNER_DATA_DIR / 'gbc_urls.csv'
import shutil
shutil.copy2(URL_PREP_FILE, scanner_input)
print(f"   Copied URLs to: {scanner_input}")

# Run scanner
scanner_script = SCANNER_DIR / 'scripts/scan_gbc_full.py'
print(f"\n   Starting scan at {datetime.now().strftime('%H:%M:%S')}...")
print(f"   Running: python {scanner_script}")
print(f"   (This will take approximately 75-90 minutes)\n")

try:
    # Run scanner from its directory with Python from venv
    result = subprocess.run(
        [sys.executable, 'scripts/scan_gbc_full.py'],
        cwd=str(SCANNER_DIR),
        capture_output=True,
        text=True,
        timeout=7200  # 120 minutes timeout
    )

    print(result.stdout)
    if result.returncode != 0:
        print(f"\n   ⚠️  Scanner returned error code {result.returncode}")
        print(f"   Error output:\n{result.stderr}")
        sys.exit(1)

    print(f"\n   Scan completed at {datetime.now().strftime('%H:%M:%S')}")

    # Find the most recent scan result
    scan_results = sorted(SCANNER_DATA_DIR.glob('gbc_scan_results_*.csv'), key=lambda x: x.stat().st_mtime)
    if not scan_results:
        print(f"\n   ❌ ERROR: No scan results found in {SCANNER_DATA_DIR}")
        sys.exit(1)

    latest_scan = scan_results[-1]
    print(f"   Found scan result: {latest_scan.name}")

    # If session ID provided, copy result to session-specific name
    if args.session_id:
        session_scan = SCANNER_DATA_DIR / f'gbc_scan_results_{args.session_id}.csv'
        shutil.copy2(latest_scan, session_scan)
        print(f"   Copied to session-specific file: {session_scan.name}")
        latest_scan = session_scan

    # Load scan results
    print(f"\n4. Loading scan results from {latest_scan.name}...")
    scan_df = pd.read_csv(latest_scan)
    print(f"   Scanned URLs: {len(scan_df)}")

    # ============================================================================
    # STEP 4: MERGE SCAN RESULTS WITH SET C
    # ============================================================================

    print("\n5. Merging scan results with Set C...")

    # Prepare scan data for merge (using actual column names from scanner V4)
    scan_data = scan_df[['url', 'status_code', 'final_url', 'total_score',
                        'is_live', 'likelihood', 'indicators_found',
                        'wayback_used']].copy()

    # Rename columns with url_ prefix
    scan_data = scan_data.rename(columns={
        'status_code': 'url_status',
        'final_url': 'url_final',
        'total_score': 'url_score',
        'is_live': 'url_is_live',
        'likelihood': 'url_likelihood',
        'indicators_found': 'url_indicators_found',
        'wayback_used': 'url_wayback_used'
    })

    # Merge with Set C
    df_c_scanned = df_c.merge(scan_data, left_on='resource_url', right_on='url', how='left')
    df_c_scanned = df_c_scanned.drop(columns=['url'])

    # Fill NaN for resources without URLs
    url_cols = ['url_status', 'url_final', 'url_score', 'url_is_live',
                'url_likelihood', 'url_indicators_found', 'url_wayback_used']
    for col in url_cols:
        if col not in df_c_scanned.columns:
            df_c_scanned[col] = None

    print(f"   Merged: {len(df_c_scanned)} resources")
    print(f"   With URL scan data: {df_c_scanned['url_status'].notna().sum()}")

    # ============================================================================
    # STEP 5: SAVE OUTPUT
    # ============================================================================

    print("\n6. Saving output...")
    df_c_scanned.to_csv(OUTPUT_FILE, index=False)
    print(f"   Saved to: {OUTPUT_FILE}")

    # ============================================================================
    # STEP 6: GENERATE STATISTICS
    # ============================================================================

    print("\n7. Generating statistics...")

    stats = []
    stats.append("="*80)
    stats.append("SET C URL SCANNING STATISTICS")
    stats.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    stats.append("="*80)
    stats.append("")

    stats.append(f"Total resources in Set C: {len(df_c)}")
    stats.append(f"Resources with URLs: {urls_present}")
    stats.append(f"URLs scanned: {len(scan_df)}")
    stats.append("")

    # URL scan results breakdown
    if 'url_status' in df_c_scanned.columns:
        status_counts = df_c_scanned['url_status'].value_counts()
        stats.append("URL Scan Status:")
        for status, count in status_counts.items():
            stats.append(f"  {status}: {count}")
        stats.append("")

    # Score distribution
    if 'url_score' in df_c_scanned.columns:
        scored = df_c_scanned['url_score'].notna().sum()
        avg_score = df_c_scanned['url_score'].mean()
        stats.append(f"URLs with scores: {scored}")
        stats.append(f"Average score: {avg_score:.2f}")
        stats.append("")

        # Score categories
        very_high = (df_c_scanned['url_score'] >= 0.8).sum()
        high = ((df_c_scanned['url_score'] >= 0.6) & (df_c_scanned['url_score'] < 0.8)).sum()
        medium = ((df_c_scanned['url_score'] >= 0.4) & (df_c_scanned['url_score'] < 0.6)).sum()
        low = (df_c_scanned['url_score'] < 0.4).sum()

        stats.append("Score Distribution:")
        stats.append(f"  Very High (≥0.8): {very_high}")
        stats.append(f"  High (0.6-0.8): {high}")
        stats.append(f"  Medium (0.4-0.6): {medium}")
        stats.append(f"  Low (<0.4): {low}")
        stats.append("")

    # Wayback usage
    if 'url_wayback_used' in df_c_scanned.columns:
        wayback_count = df_c_scanned['url_wayback_used'].sum()
        stats.append(f"Wayback Machine used: {wayback_count}")
        stats.append("")

    stats_text = '\n'.join(stats)
    with open(STATS_FILE, 'w') as f:
        f.write(stats_text)

    print(stats_text)

    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)
    print(f"\nOutput file: {OUTPUT_FILE}")
    print(f"Statistics: {STATS_FILE}")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

except Exception as e:
    print(f"\n   Error: {e}")
    sys.exit(1)
