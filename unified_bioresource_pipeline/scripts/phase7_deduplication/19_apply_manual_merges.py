#!/usr/bin/env python3
"""
Apply Manual Merge Groups to Create Final Deduplicated Dataset

Takes the unclear_cases_with_similarity.csv (from script 18) where user has
assigned merge groups (single letters or any identifier), and merges papers
with the same merge_group_id.

Papers without merge_group_id are kept as singles.

Usage:
    python 19_apply_manual_merges.py --session-dir 2025-12-04-111420-z381s [--profile balanced]
"""

import argparse
import sys
import pandas as pd
import re
from pathlib import Path

# Add lib to path for session utilities
SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

from lib.session_utils import validate_session_dir, get_session_path

def parse_args():
    parser = argparse.ArgumentParser(
        description='Apply manual merge groups to create final deduplicated dataset'
    )
    parser.add_argument('--session-dir', type=str, required=True,
                        help='Session directory (e.g., 2025-12-04-111420-z381s)')
    parser.add_argument('--profile', type=str, default='balanced',
                        choices=['conservative', 'balanced', 'aggressive'],
                        help='Deduplication profile to process (default: balanced)')
    return parser.parse_args()

args = parse_args()

# Validate session directory
SESSION_DIR = PIPELINE_DIR / args.session_dir
validate_session_dir(SESSION_DIR, required_phases=['07_deduplication'])

# Paths - all relative to session directory
DEDUP_DIR = SESSION_DIR / '07_deduplication' / args.profile

# Inputs - from session directory
UNCLEAR_CASES_FILE = DEDUP_DIR / 'unclear_cases_with_similarity.csv'
ORIGINAL_DEDUP_FILE = DEDUP_DIR / 'set_c_final.csv'
# For full paper data, use the mapping output
FILTERED_DATA_FILE = SESSION_DIR / '05_mapping' / 'union_papers_with_urls.csv'

# Outputs - to session directory
OUTPUT_FILE = DEDUP_DIR / 'set_c_final_with_merges.csv'
MERGE_REPORT = DEDUP_DIR / 'manual_merge_report.txt'

print("="*80)
print("Apply Manual Merge Groups - Final Deduplication")
print("="*80)
print(f"\nSession: {args.session_dir}")
print(f"Profile: {args.profile}")
print(f"Input (unclear cases):  {UNCLEAR_CASES_FILE}")
print(f"Input (original dedup): {ORIGINAL_DEDUP_FILE}")
print(f"Output: {OUTPUT_FILE}")

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n1. Loading data...")

# Load manually edited unclear cases
unclear_df = pd.read_csv(UNCLEAR_CASES_FILE)
print(f"   Unclear cases: {len(unclear_df)}")

# Load original dedup file (974 resources)
dedup_df = pd.read_csv(ORIGINAL_DEDUP_FILE)
print(f"   Original deduplicated resources: {len(dedup_df)}")

# Load full filtered data (to get all columns for papers not in dedup yet)
filtered_df = pd.read_csv(FILTERED_DATA_FILE)
print(f"   Full filtered dataset: {len(filtered_df)}")

# ============================================================================
# IDENTIFY PAPERS TO MERGE
# ============================================================================

print("\n2. Analyzing merge groups...")

# Papers with merge group assigned (not empty, not NaN)
to_merge = unclear_df[
    unclear_df['merge_group_id'].notna() &
    (unclear_df['merge_group_id'] != '')
].copy()

# Papers without merge group (keep as singles)
keep_single = unclear_df[
    unclear_df['merge_group_id'].isna() |
    (unclear_df['merge_group_id'] == '')
]

print(f"   Papers with merge groups: {len(to_merge)}")
print(f"   Papers to keep single: {len(keep_single)}")

if len(to_merge) > 0:
    merge_groups = to_merge.groupby('merge_group_id')
    print(f"   Number of merge groups: {len(merge_groups)}")
    print()
    print("   Merge groups:")
    for group_id, group_df in merge_groups:
        print(f"     {group_id}: {len(group_df)} papers")

# ============================================================================
# PREPARE MERGED PAPERS
# ============================================================================

print("\n3. Preparing merged papers...")

merged_papers = []

if len(to_merge) > 0:
    for group_id, group_df in to_merge.groupby('merge_group_id'):
        # Get PMIDs for this group
        pmids = group_df['pmid'].tolist()

        # Get full data for these PMIDs from filtered dataset
        group_full_data = filtered_df[filtered_df['pmid'].isin(pmids)].copy()

        if len(group_full_data) == 0:
            print(f"   WARNING: No data found for merge group {group_id}")
            continue

        # Sort by PMID to keep earliest
        group_full_data = group_full_data.sort_values('pmid')

        # Create merged record
        merged_record = {
            'pmid': ', '.join(map(str, group_full_data['pmid'].tolist())),
            'title': group_full_data.iloc[0]['title'],
            'abstract': group_full_data.iloc[0]['abstract'],
            'in_linguistic': group_full_data.iloc[0]['in_linguistic'],
            'in_setfit': group_full_data.iloc[0]['in_setfit'],
            'ling_score': group_full_data.iloc[0]['ling_score'],
            'setfit_confidence': group_full_data.iloc[0]['setfit_confidence'],
            'primary_entity_long': group_full_data.iloc[0]['primary_entity_long'],
            'primary_entity_short': group_full_data.iloc[0]['primary_entity_short'],
            'primary_score': group_full_data['primary_score'].max(),
            'status': group_full_data.iloc[0]['status'],
            'matched_long_short': group_full_data.iloc[0]['matched_long_short'],
            'ner_source': group_full_data.iloc[0]['ner_source'],
            'ner_confidence': group_full_data['ner_confidence'].max(),
            'entity_from_title': group_full_data.iloc[0]['entity_from_title'],
            'db_keyword_found': group_full_data.iloc[0]['db_keyword_found'],
            'very_high_conf': group_full_data.iloc[0]['very_high_conf'],
            'title_entity_in_ner': group_full_data.iloc[0]['title_entity_in_ner'],
            'baseline_entity_match': group_full_data.iloc[0]['baseline_entity_match'],
            'all_urls': group_full_data.iloc[0]['all_urls'],
            'resource_url': group_full_data.iloc[0]['resource_url'],
            'has_resource_url': group_full_data.iloc[0]['has_resource_url'],
            'url_context': group_full_data.iloc[0]['url_context'],
            'article_count': len(group_full_data)
        }

        # Handle all_long and all_short - combine unique values
        all_long_values = set()
        all_short_values = set()

        for _, row in group_full_data.iterrows():
            if pd.notna(row.get('all_long')):
                all_long_values.update(str(row['all_long']).split(' | '))
            if pd.notna(row.get('all_short')):
                all_short_values.update(str(row['all_short']).split(' | '))

        # Remove empty strings and 'nan'
        all_long_values = all_long_values - {'', 'nan'}
        all_short_values = all_short_values - {'', 'nan'}

        merged_record['all_long'] = ' | '.join(sorted(all_long_values)) if all_long_values else ''
        merged_record['all_short'] = ' | '.join(sorted(all_short_values)) if all_short_values else ''

        merged_papers.append(merged_record)

print(f"   Created {len(merged_papers)} merged records")

# ============================================================================
# GET PMIDs THAT WERE MERGED
# ============================================================================

# Get all PMIDs that are part of merge groups
merged_pmids = set()
for group_id, group_df in to_merge.groupby('merge_group_id'):
    merged_pmids.update(group_df['pmid'].tolist())

print(f"   Total PMIDs in merged groups: {len(merged_pmids)}")

# ============================================================================
# REMOVE MERGED PMIDs FROM ORIGINAL DEDUP FILE
# ============================================================================

print("\n4. Removing merged PMIDs from original dedup file...")

# Split PMIDs in dedup_df (some have multiple PMIDs already)
def get_all_pmids(pmid_str):
    """Extract all PMIDs from a comma-separated string"""
    if pd.isna(pmid_str):
        return []
    return [int(p.strip()) for p in str(pmid_str).split(',')]

# Check which rows contain any of the merged PMIDs
rows_to_keep = []
for _, row in dedup_df.iterrows():
    row_pmids = get_all_pmids(row['pmid'])
    # Keep row if it doesn't contain any of the merged PMIDs
    if not any(p in merged_pmids for p in row_pmids):
        rows_to_keep.append(row)

remaining_dedup = pd.DataFrame(rows_to_keep)
print(f"   Remaining resources from original dedup: {len(remaining_dedup)}")
print(f"   Removed resources: {len(dedup_df) - len(remaining_dedup)}")

# ============================================================================
# COMBINE ALL RESOURCES
# ============================================================================

print("\n5. Creating final deduplicated dataset...")

# Combine:
# 1. Remaining resources from original dedup (not involved in manual merges)
# 2. Newly merged resources from manual merge groups

if len(merged_papers) > 0:
    merged_df = pd.DataFrame(merged_papers)
    final_df = pd.concat([remaining_dedup, merged_df], ignore_index=True)
else:
    final_df = remaining_dedup

# Sort by article_count (descending) then primary_score
final_df = final_df.sort_values(['article_count', 'primary_score'], ascending=[False, False])

print(f"\n   Final deduplicated count: {len(final_df)}")
print(f"   Resources with multiple papers: {(final_df['article_count'] > 1).sum()}")

# ============================================================================
# SAVE OUTPUT
# ============================================================================

print("\n6. Saving output...")
final_df.to_csv(OUTPUT_FILE, index=False)
print(f"   Saved to: {OUTPUT_FILE}")

# ============================================================================
# GENERATE MERGE REPORT
# ============================================================================

print("\n7. Generating merge report...")

report = []
report.append("="*80)
report.append("MANUAL MERGE GROUPS - FINAL DEDUPLICATION REPORT")
report.append("="*80)
report.append("")

report.append("Input:")
report.append(f"  Original deduplicated resources (Script 12): {len(dedup_df)}")
report.append(f"  Unclear cases analyzed: {len(unclear_df)}")
report.append("")

report.append("Manual Merge Groups Applied:")
report.append(f"  Papers with merge groups assigned: {len(to_merge)}")
report.append(f"  Papers kept as singles: {len(keep_single)}")
report.append(f"  Number of merge groups: {len(to_merge.groupby('merge_group_id')) if len(to_merge) > 0 else 0}")
report.append("")

if len(to_merge) > 0:
    report.append("Merge Groups Detail:")
    for group_id, group_df in to_merge.groupby('merge_group_id'):
        report.append(f"\n  Group {group_id}: {len(group_df)} papers")
        for _, row in group_df.iterrows():
            report.append(f"    - PMID: {row['pmid']}, Entity: {row['primary_entity']}")
    report.append("")

report.append("Final Results:")
report.append(f"  Resources before manual merges: {len(dedup_df)}")
report.append(f"  Resources after manual merges: {len(final_df)}")
report.append(f"  Additional merges applied: {len(dedup_df) - len(final_df)}")
report.append(f"  Reduction: {((len(dedup_df) - len(final_df)) / len(dedup_df) * 100):.1f}%")
report.append("")

report.append("Article Count Distribution:")
article_counts = final_df['article_count'].value_counts().sort_index()
for count, freq in article_counts.items():
    report.append(f"  {count} paper(s):  {freq} resources")
report.append("")

report.append("Top Resources by Article Count:")
top_resources = final_df.nlargest(10, 'article_count')[
    ['pmid', 'primary_entity_long', 'primary_entity_short', 'resource_url', 'article_count']
]
for _, row in top_resources.iterrows():
    entity = row['primary_entity_long'] if pd.notna(row['primary_entity_long']) and row['primary_entity_long'] != '' else row['primary_entity_short']
    if pd.notna(entity):
        entity_str = str(entity)[:40]
    else:
        entity_str = '(no entity name)'
    report.append(f"  {entity_str:40s} : {row['article_count']} papers")
report.append("")

report_text = '\n'.join(report)

with open(MERGE_REPORT, 'w') as f:
    f.write(report_text)

print(report_text)

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print(f"\nOutput files:")
print(f"  Final deduplicated data: {OUTPUT_FILE}")
print(f"  Merge report:            {MERGE_REPORT}")
print(f"\nFinal unique resources: {len(final_df)}")
print(f"Improvement over Script 12: {len(dedup_df) - len(final_df)} additional merges")
