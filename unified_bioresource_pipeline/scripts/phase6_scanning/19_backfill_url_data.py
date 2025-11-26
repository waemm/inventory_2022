#!/usr/bin/env python3
"""
Backfill URL Scan Data to Sets A and B

Takes URL scan data from Set C and adds it to Sets A and B based on
matching resource_url or entity name. This ensures all three sets have
identical column structure for comparison.

Created: 2025-11-20
Updated: 2025-11-21 (Added session support)
"""

import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Backfill URL scan data to Sets A and B')
parser.add_argument('--session-dir', type=str, required=False,
                    help='Session directory for inputs/outputs')
args = parser.parse_args()

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')

# Input/output paths - use session directory if provided
if args.session_dir:
    SESSION_DIR = Path(args.session_dir)
    INPUT_SET_A = SESSION_DIR / 'deduplicated' / 'set_a_linguistic_dedup.csv'
    INPUT_SET_B = SESSION_DIR / 'deduplicated' / 'set_b_setfit_dedup.csv'
    INPUT_SET_C = SESSION_DIR / 'url_scanned' / 'set_c_with_url_scan.csv'
    FINAL_DIR = SESSION_DIR / 'final'
else:
    # Legacy paths
    PIPELINE_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/results'
    INPUT_SET_A = PIPELINE_DIR / 'deduplicated' / 'set_a_linguistic_dedup.csv'
    INPUT_SET_B = PIPELINE_DIR / 'deduplicated' / 'set_b_setfit_dedup.csv'
    INPUT_SET_C = PIPELINE_DIR / 'url_scanned' / 'set_c_with_url_scan.csv'
    FINAL_DIR = PIPELINE_DIR / 'final'

FINAL_DIR.mkdir(parents=True, exist_ok=True)

# Output files
OUTPUT_SET_A = FINAL_DIR / 'set_a_linguistic_final.csv'
OUTPUT_SET_B = FINAL_DIR / 'set_b_setfit_final.csv'
OUTPUT_SET_C = FINAL_DIR / 'set_c_union_final.csv'
STATS_FILE = FINAL_DIR / 'backfill_statistics.txt'

print("="*80)
print("BACKFILLING URL SCAN DATA TO SETS A AND B")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
if args.session_dir:
    print(f"Session: {Path(args.session_dir).name}")
print(f"Output directory: {FINAL_DIR}\n")

# ============================================================================
# STEP 1: LOAD ALL DATASETS
# ============================================================================

print("1. Loading datasets...")
df_a = pd.read_csv(INPUT_SET_A)
df_b = pd.read_csv(INPUT_SET_B)
df_c = pd.read_csv(INPUT_SET_C)

print(f"   Set A: {len(df_a)} resources")
print(f"   Set B: {len(df_b)} resources")
print(f"   Set C: {len(df_c)} resources (with URL scan data)")

# ============================================================================
# STEP 2: EXTRACT URL SCAN COLUMNS FROM SET C
# ============================================================================

print("\n2. Extracting URL scan columns from Set C...")

# Identify URL scan columns (columns starting with 'url_')
url_cols = [col for col in df_c.columns if col.startswith('url_')]
print(f"   Found {len(url_cols)} URL scan columns:")
for col in url_cols:
    print(f"     - {col}")

# Create lookup dataset: resource_url -> URL scan data
url_scan_data = df_c[['resource_url'] + url_cols].copy()
url_scan_data = url_scan_data[url_scan_data['resource_url'].notna()]
print(f"\n   URL scan lookup table: {len(url_scan_data)} URLs")

# ============================================================================
# STEP 3: BACKFILL SET A
# ============================================================================

print("\n3. Backfilling Set A...")

# Merge URL scan data
df_a_final = df_a.merge(url_scan_data, on='resource_url', how='left')

# Count matches
matches_a = df_a_final['url_status'].notna().sum() if 'url_status' in df_a_final.columns else 0
print(f"   Matched URL scan data: {matches_a}/{len(df_a)} resources ({matches_a/len(df_a)*100:.1f}%)")

# Save
df_a_final.to_csv(OUTPUT_SET_A, index=False)
print(f"   Saved to: {OUTPUT_SET_A}")

# ============================================================================
# STEP 4: BACKFILL SET B
# ============================================================================

print("\n4. Backfilling Set B...")

# Merge URL scan data
df_b_final = df_b.merge(url_scan_data, on='resource_url', how='left')

# Count matches
matches_b = df_b_final['url_status'].notna().sum() if 'url_status' in df_b_final.columns else 0
print(f"   Matched URL scan data: {matches_b}/{len(df_b)} resources ({matches_b/len(df_b)*100:.1f}%)")

# Save
df_b_final.to_csv(OUTPUT_SET_B, index=False)
print(f"   Saved to: {OUTPUT_SET_B}")

# ============================================================================
# STEP 5: COPY SET C TO FINAL
# ============================================================================

print("\n5. Copying Set C to final directory...")
df_c.to_csv(OUTPUT_SET_C, index=False)
print(f"   Saved to: {OUTPUT_SET_C}")

# ============================================================================
# STEP 6: VALIDATE COLUMN CONSISTENCY
# ============================================================================

print("\n6. Validating column consistency...")

cols_a = set(df_a_final.columns)
cols_b = set(df_b_final.columns)
cols_c = set(df_c.columns)

# Check if all sets have same columns
all_same = (cols_a == cols_b == cols_c)

if all_same:
    print(f"   ✅ All three sets have identical columns ({len(cols_a)} columns)")
else:
    print(f"   ⚠️  Column mismatch detected:")
    print(f"      Set A: {len(cols_a)} columns")
    print(f"      Set B: {len(cols_b)} columns")
    print(f"      Set C: {len(cols_c)} columns")

    # Show differences
    only_a = cols_a - cols_c
    only_b = cols_b - cols_c
    only_c = cols_c - cols_a

    if only_a:
        print(f"\n      Only in A: {only_a}")
    if only_b:
        print(f"      Only in B: {only_b}")
    if only_c:
        print(f"      Only in C: {only_c}")

# ============================================================================
# STEP 7: GENERATE STATISTICS
# ============================================================================

print("\n7. Generating statistics...")

stats = []
stats.append("="*80)
stats.append("URL SCAN DATA BACKFILL STATISTICS")
stats.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
stats.append("="*80)
stats.append("")

stats.append("INPUT DATASETS:")
stats.append(f"  Set A (Linguistic): {len(df_a)} resources")
stats.append(f"  Set B (SetFit):     {len(df_b)} resources")
stats.append(f"  Set C (Union):      {len(df_c)} resources")
stats.append("")

stats.append("URL SCAN DATA COVERAGE:")
stats.append(f"  Set A: {matches_a}/{len(df_a)} ({matches_a/len(df_a)*100:.1f}%)")
stats.append(f"  Set B: {matches_b}/{len(df_b)} ({matches_b/len(df_b)*100:.1f}%)")
stats.append(f"  Set C: {df_c['url_status'].notna().sum()}/{len(df_c)} ({df_c['url_status'].notna().sum()/len(df_c)*100:.1f}%)")
stats.append("")

stats.append("URL SCAN COLUMNS ADDED:")
for col in url_cols:
    stats.append(f"  - {col}")
stats.append("")

stats.append("COLUMN CONSISTENCY:")
if all_same:
    stats.append(f"  ✅ All three sets have identical {len(cols_a)} columns")
else:
    stats.append(f"  ⚠️  Column mismatch:")
    stats.append(f"     Set A: {len(cols_a)} columns")
    stats.append(f"     Set B: {len(cols_b)} columns")
    stats.append(f"     Set C: {len(cols_c)} columns")
stats.append("")

stats.append("OUTPUT FILES:")
stats.append(f"  {OUTPUT_SET_A.name}")
stats.append(f"  {OUTPUT_SET_B.name}")
stats.append(f"  {OUTPUT_SET_C.name}")
stats.append("")

stats_text = '\n'.join(stats)
with open(STATS_FILE, 'w') as f:
    f.write(stats_text)

print(stats_text)

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print(f"\nFinal datasets ready for analysis:")
print(f"  Set A: {OUTPUT_SET_A}")
print(f"  Set B: {OUTPUT_SET_B}")
print(f"  Set C: {OUTPUT_SET_C}")
print(f"\nStatistics: {STATS_FILE}")
print(f"\nAll sets now have identical column structure with URL scan data.")
print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
