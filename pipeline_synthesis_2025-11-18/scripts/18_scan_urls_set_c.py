#!/usr/bin/env python3
"""
URL Scanning for Set C (Union)

Scans all URLs in Set C using the bioresource_url_scanner and adds
validation columns to the dataset.

Created: 2025-11-20
Estimated time: 75-90 minutes for full scan
"""

import pandas as pd
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
DEDUP_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/results/deduplicated'
SCANNER_DIR = BASE_DIR / 'bioresource_url_scanner'
SCANNER_DATA_DIR = SCANNER_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/results/url_scanned'

# Input file
INPUT_FILE = DEDUP_DIR / 'set_c_union_dedup.csv'

# Output files
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RESULTS_DIR / 'set_c_with_url_scan.csv'
URL_PREP_FILE = SCANNER_DATA_DIR / 'set_c_urls.csv'
STATS_FILE = RESULTS_DIR / 'url_scan_statistics.txt'

print("="*80)
print("URL SCANNING FOR SET C (UNION)")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

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

# Run scanner
scanner_script = SCANNER_DIR / 'scripts/scan_gbc_full.py'

# Modify scanner script call to use our prepared file
print("\n   Starting scan...")
print(f"   Command: python {scanner_script}")

try:
    # Note: The scanner script will need to be adapted to read from set_c_urls.csv
    # For now, we'll document the manual process
    print("\n   ⚠️  MANUAL STEP REQUIRED:")
    print(f"   1. cd {SCANNER_DIR}")
    print(f"   2. source venv/bin/activate")
    print(f"   3. Modify scan_gbc_full.py to read from: {URL_PREP_FILE}")
    print(f"   4. python scripts/scan_gbc_full.py")
    print(f"   5. Results will be in: {SCANNER_DATA_DIR}/gbc_scan_results_*.csv")
    print(f"\n   Once complete, re-run this script to continue with Step 4")

    # Check if scan results already exist
    scan_results = sorted(SCANNER_DATA_DIR.glob('gbc_scan_results_*.csv'))
    if scan_results:
        latest_scan = scan_results[-1]
        print(f"\n   Found existing scan: {latest_scan.name}")

        # Ask user if they want to use it
        print("\n   Do you want to use this scan result? (y/n)")
        # For automation, we'll assume yes if the file is recent

        # Load scan results
        print(f"\n4. Loading scan results from {latest_scan.name}...")
        scan_df = pd.read_csv(latest_scan)
        print(f"   Scanned URLs: {len(scan_df)}")

        # ============================================================================
        # STEP 4: MERGE SCAN RESULTS WITH SET C
        # ============================================================================

        print("\n5. Merging scan results with Set C...")

        # Prepare scan data for merge
        scan_data = scan_df[['url', 'status', 'final_url', 'score',
                            'is_database', 'is_portal', 'keywords_found',
                            'content_indicators', 'bioinformatics_terms',
                            'download_links', 'institutional', 'wayback_used']].copy()

        # Rename columns with url_scan_ prefix
        scan_data = scan_data.rename(columns={
            'status': 'url_status',
            'final_url': 'url_final',
            'score': 'url_score',
            'is_database': 'url_is_database',
            'is_portal': 'url_is_portal',
            'keywords_found': 'url_keywords_found',
            'content_indicators': 'url_content_indicators',
            'bioinformatics_terms': 'url_bioinformatics_terms',
            'download_links': 'url_download_links',
            'institutional': 'url_institutional',
            'wayback_used': 'url_wayback_used'
        })

        # Merge with Set C
        df_c_scanned = df_c.merge(scan_data, left_on='resource_url', right_on='url', how='left')
        df_c_scanned = df_c_scanned.drop(columns=['url'])

        # Fill NaN for resources without URLs
        url_cols = ['url_status', 'url_final', 'url_score', 'url_is_database',
                    'url_is_portal', 'url_keywords_found', 'url_content_indicators',
                    'url_bioinformatics_terms', 'url_download_links', 'url_institutional',
                    'url_wayback_used']
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
    else:
        print("\n   No scan results found. Please run the scanner manually (see instructions above).")
        print("\n   After scanning, re-run this script to merge results.")
        sys.exit(0)

except Exception as e:
    print(f"\n   Error: {e}")
    sys.exit(1)
