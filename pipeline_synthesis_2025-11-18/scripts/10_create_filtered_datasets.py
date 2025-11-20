#!/usr/bin/env python3
"""
Create 4 filtered datasets from union with primary resources:
1a. Baseline by PMID match
1b. Baseline by entity match
2. Linguistic (INCLUDING baseline for deduplication)
3. SetFit (INCLUDING baseline for deduplication)

All files include quality indicators based on title analysis.

NOTE: Changed 2025-11-20 to INCLUDE baseline in linguistic and SetFit sets
for complete deduplication analysis.
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
SYNTHESIS_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18'

# Input files
UNION_PRIMARY = SYNTHESIS_DIR / 'data/union_papers_with_primary_resources.csv'
BASELINE_INV = BASE_DIR / 'data/final_inventory_2022.csv'

# Output directory
OUTPUT_DIR = SYNTHESIS_DIR / 'data/filtered'
OUTPUT_DIR.mkdir(exist_ok=True)

# Output files
FILE_1A = OUTPUT_DIR / 'baseline_by_pmid.csv'
FILE_1B = OUTPUT_DIR / 'baseline_by_entity_match.csv'
FILE_2 = OUTPUT_DIR / 'linguistic_all_papers.csv'  # Changed: now includes baseline
FILE_3 = OUTPUT_DIR / 'setfit_all_papers.csv'  # Changed: now includes baseline
STATS_FILE = OUTPUT_DIR / 'filtering_statistics.txt'

print("="*80)
print("Creating Filtered Datasets with Quality Indicators")
print("="*80)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize_text(text):
    """Normalize text for matching"""
    if pd.isna(text):
        return ''
    return str(text).lower().strip()

def fuzzy_match(name1, name2, threshold=0.90):
    """Fuzzy string matching with threshold"""
    s1 = normalize_text(name1)
    s2 = normalize_text(name2)
    if not s1 or not s2:
        return False
    ratio = SequenceMatcher(None, s1, s2).ratio()
    return ratio >= threshold

def extract_entity_from_title(title):
    """Extract potential resource name from title (text before first colon)"""
    if pd.isna(title):
        return ''

    # Find first colon
    if ':' not in title:
        return ''

    # Extract text before first colon
    entity = title.split(':')[0].strip()

    # Strip common articles
    for article in ['The ', 'A ', 'An ']:
        if entity.startswith(article):
            entity = entity[len(article):].strip()

    # Remove version numbers
    # Pattern: v2.0, version 2.0, 2025, etc.
    entity = re.sub(r'\bv?\d+\.?\d*\b', '', entity, flags=re.IGNORECASE)
    entity = re.sub(r'\bversion\s+\d+\.?\d*\b', '', entity, flags=re.IGNORECASE)

    # Handle parenthetical acronyms: "Name (ACRONYM)" -> "Name"
    entity = re.sub(r'\s*\([^)]+\)\s*$', '', entity)

    # Clean up extra whitespace
    entity = ' '.join(entity.split()).strip()

    return entity

def detect_db_keywords(title):
    """Detect database-related keywords in title"""
    if pd.isna(title):
        return False

    title_lower = title.lower()
    keywords = [
        'database', 'db',
        'server',
        'portal',
        'resource',
        'repository',
        'archive',
        'registry',
        'catalog',
        'collection'
    ]

    return any(keyword in title_lower for keyword in keywords)

def find_best_baseline_match(entity, baseline_entities, threshold=0.90):
    """Find best matching baseline entity"""
    if pd.isna(entity) or not entity:
        return None

    best_match = None
    best_ratio = 0.0

    for baseline_entity in baseline_entities:
        ratio = SequenceMatcher(None,
                               normalize_text(entity),
                               normalize_text(baseline_entity)).ratio()
        if ratio >= threshold and ratio > best_ratio:
            best_ratio = ratio
            best_match = baseline_entity

    return best_match

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n1. Loading datasets...")
df_union = pd.read_csv(UNION_PRIMARY)
print(f"   Union dataset: {len(df_union)} papers")

df_baseline = pd.read_csv(BASELINE_INV)
print(f"   Baseline inventory: {len(df_baseline)} resources")

# Extract baseline PMIDs and entity names
baseline_pmids = set(df_baseline['ID'].astype(str).unique())
baseline_entities = df_baseline['best_name'].dropna().unique().tolist()
print(f"   Baseline PMIDs: {len(baseline_pmids)}")
print(f"   Baseline entities: {len(baseline_entities)}")

# ============================================================================
# TITLE PROCESSING FOR ALL PAPERS
# ============================================================================

print("\n2. Processing titles for all papers...")

# Extract entity from title
df_union['entity_from_title'] = df_union['title'].apply(extract_entity_from_title)
print(f"   Extracted entities from {(df_union['entity_from_title'] != '').sum()} titles")

# Detect database keywords
df_union['db_keyword_found'] = df_union['title'].apply(detect_db_keywords)
print(f"   Found DB keywords in {df_union['db_keyword_found'].sum()} titles")

# Check if title entity matches primary
def title_matches_primary(row):
    """Check if extracted title entity matches primary entity"""
    title_entity = normalize_text(row['entity_from_title'])
    primary_long = normalize_text(row['primary_entity_long'])
    primary_short = normalize_text(row['primary_entity_short'])

    if not title_entity:
        return False

    return title_entity == primary_long or title_entity == primary_short

df_union['title_matches_primary'] = df_union.apply(title_matches_primary, axis=1)
print(f"   Title matches primary in {df_union['title_matches_primary'].sum()} papers")

# Calculate very high confidence indicator
df_union['very_high_conf'] = (
    df_union['db_keyword_found'] & df_union['title_matches_primary']
)
print(f"   Very high confidence: {df_union['very_high_conf'].sum()} papers")

# ============================================================================
# BASELINE ENTITY MATCHING
# ============================================================================

print("\n3. Matching entities to baseline...")

# Build normalized baseline lookup for faster matching
baseline_lookup = {}
for entity in baseline_entities:
    normalized = normalize_text(entity)
    baseline_lookup[normalized] = entity

print(f"   Built baseline lookup: {len(baseline_lookup)} normalized entities")

# Collect all unique primary entities from union dataset
unique_entities = set()
for _, row in df_union.iterrows():
    if pd.notna(row['primary_entity_long']):
        unique_entities.add(str(row['primary_entity_long']))
    if pd.notna(row['primary_entity_short']):
        unique_entities.add(str(row['primary_entity_short']))

print(f"   Found {len(unique_entities)} unique primary entities")

# Pre-compute matches for unique entities using exact match only (instant)
print("   Pre-computing baseline matches (exact match only)...")
entity_to_baseline = {}

for entity in unique_entities:
    normalized = normalize_text(entity)

    # Exact match only (instant)
    if normalized in baseline_lookup:
        entity_to_baseline[entity] = baseline_lookup[normalized]

print(f"   Matched {len(entity_to_baseline)} unique entities to baseline (exact match)")

# Now apply pre-computed matches to all papers (instant lookup)
print("   Applying matches to all papers...")
def lookup_baseline_match(row):
    """Look up pre-computed baseline match"""
    # Check primary_long first
    if pd.notna(row['primary_entity_long']):
        entity = str(row['primary_entity_long'])
        if entity in entity_to_baseline:
            return entity_to_baseline[entity]

    # Then check primary_short
    if pd.notna(row['primary_entity_short']):
        entity = str(row['primary_entity_short'])
        if entity in entity_to_baseline:
            return entity_to_baseline[entity]

    return None

df_union['baseline_entity_match'] = df_union.apply(lookup_baseline_match, axis=1)
baseline_matches = df_union['baseline_entity_match'].notna().sum()
print(f"   Found baseline entity matches: {baseline_matches} papers")

# ============================================================================
# CREATE FILE 1A: BASELINE BY PMID
# ============================================================================

print("\n4. Creating File 1a: Baseline by PMID...")

df_union['pmid_str'] = df_union['pmid'].astype(str)
df_1a = df_union[df_union['pmid_str'].isin(baseline_pmids)].copy()

# Drop temp column
df_1a = df_1a.drop(columns=['pmid_str', 'baseline_entity_match'])

print(f"   File 1a: {len(df_1a)} papers")
df_1a.to_csv(FILE_1A, index=False)
print(f"   Saved to: {FILE_1A}")

# ============================================================================
# CREATE FILE 1B: BASELINE BY ENTITY MATCH
# ============================================================================

print("\n5. Creating File 1b: Baseline by Entity Match...")

df_1b = df_union[df_union['baseline_entity_match'].notna()].copy()

# Rename column for clarity
df_1b = df_1b.rename(columns={'baseline_entity_match': 'baseline_entity_matched'})

# Drop temp column
df_1b = df_1b.drop(columns=['pmid_str'])

print(f"   File 1b: {len(df_1b)} papers")
df_1b.to_csv(FILE_1B, index=False)
print(f"   Saved to: {FILE_1B}")

# ============================================================================
# CREATE FILE 2: LINGUISTIC (INCLUDING BASELINE)
# ============================================================================

print("\n6. Creating File 2: Linguistic (including baseline)...")

df_2 = df_union[
    (df_union['in_linguistic'] == True)
].copy()

# Rename for clarity
df_2 = df_2.rename(columns={'baseline_entity_match': 'baseline_entity_match'})

# Keep entity_from_title, title_entity_in_ner would be same as title_matches_primary
df_2 = df_2.rename(columns={'title_matches_primary': 'title_entity_in_ner'})

# Drop temp column
df_2 = df_2.drop(columns=['pmid_str'])

print(f"   File 2: {len(df_2)} papers")
df_2.to_csv(FILE_2, index=False)
print(f"   Saved to: {FILE_2}")

# ============================================================================
# CREATE FILE 3: SETFIT (INCLUDING BASELINE)
# ============================================================================

print("\n7. Creating File 3: SetFit (including baseline)...")

df_3 = df_union[
    (df_union['in_setfit'] == True)
].copy()

# Rename for clarity
df_3 = df_3.rename(columns={
    'baseline_entity_match': 'baseline_entity_match',
    'title_matches_primary': 'title_entity_in_ner'
})

# Drop temp column
df_3 = df_3.drop(columns=['pmid_str'])

print(f"   File 3: {len(df_3)} papers")
df_3.to_csv(FILE_3, index=False)
print(f"   Saved to: {FILE_3}")

# ============================================================================
# GENERATE STATISTICS
# ============================================================================

print("\n8. Generating statistics...")

def calculate_stats(df, name):
    """Calculate statistics for a dataset"""
    stats = {
        'name': name,
        'total': len(df),
        'db_keyword_found': df['db_keyword_found'].sum(),
        'title_entity_in_ner': df.get('title_entity_in_ner', df.get('title_matches_primary', pd.Series([False]*len(df)))).sum(),
        'very_high_conf': df['very_high_conf'].sum(),
        'status_ok': (df['status'] == 'ok').sum(),
        'status_conflict': (df['status'] == 'conflict').sum(),
        'status_low_score': (df['status'] == 'low_score').sum(),
        'status_no_entities': (df['status'] == 'no_entities').sum(),
        'has_primary_long': df['primary_entity_long'].notna().sum(),
        'has_primary_short': df['primary_entity_short'].notna().sum(),
    }

    # Calculate percentages
    if stats['total'] > 0:
        stats['db_keyword_pct'] = (stats['db_keyword_found'] / stats['total']) * 100
        stats['title_entity_pct'] = (stats['title_entity_in_ner'] / stats['total']) * 100
        stats['very_high_conf_pct'] = (stats['very_high_conf'] / stats['total']) * 100
        stats['status_ok_pct'] = (stats['status_ok'] / stats['total']) * 100

    return stats

stats_1a = calculate_stats(df_1a, "File 1a: Baseline by PMID")
stats_1b = calculate_stats(df_1b, "File 1b: Baseline by Entity")
stats_2 = calculate_stats(df_2, "File 2: Linguistic (All Papers)")
stats_3 = calculate_stats(df_3, "File 3: SetFit (All Papers)")

# Write statistics report
with open(STATS_FILE, 'w') as f:
    f.write("="*80 + "\n")
    f.write("FILTERED DATASETS STATISTICS\n")
    f.write("="*80 + "\n\n")

    for stats in [stats_1a, stats_1b, stats_2, stats_3]:
        f.write(f"\n{stats['name']}\n")
        f.write("-"*80 + "\n")
        f.write(f"Total papers: {stats['total']}\n\n")

        f.write("Quality Indicators:\n")
        f.write(f"  DB keyword found:       {stats['db_keyword_found']:>6} ({stats.get('db_keyword_pct', 0):>5.1f}%)\n")
        f.write(f"  Title matches primary:  {stats['title_entity_in_ner']:>6} ({stats.get('title_entity_pct', 0):>5.1f}%)\n")
        f.write(f"  Very high confidence:   {stats['very_high_conf']:>6} ({stats.get('very_high_conf_pct', 0):>5.1f}%)\n\n")

        f.write("Status Breakdown:\n")
        f.write(f"  OK (clear primary):     {stats['status_ok']:>6} ({stats.get('status_ok_pct', 0):>5.1f}%)\n")
        f.write(f"  Conflict (tie):         {stats['status_conflict']:>6}\n")
        f.write(f"  Low score:              {stats['status_low_score']:>6}\n")
        f.write(f"  No entities:            {stats['status_no_entities']:>6}\n\n")

        f.write("Primary Entity Assignment:\n")
        f.write(f"  Has primary_long:       {stats['has_primary_long']:>6}\n")
        f.write(f"  Has primary_short:      {stats['has_primary_short']:>6}\n")
        f.write("\n")

print(f"   Saved statistics to: {STATS_FILE}")

# ============================================================================
# VALIDATION CHECKS
# ============================================================================

print("\n9. Running validation checks...")

# Check 1: Linguistic and SetFit should now INCLUDE baseline  (changed 2025-11-20)
baseline_pmids_1a = set(df_1a['pmid'].astype(str))
ling_pmids = set(df_2['pmid'].astype(str))
setfit_pmids = set(df_3['pmid'].astype(str))

overlap_ling = baseline_pmids_1a & ling_pmids
overlap_setfit = baseline_pmids_1a & setfit_pmids

print(f"   Linguistic papers: {len(ling_pmids)} ({len(overlap_ling)} from baseline)")
print(f"   SetFit papers: {len(setfit_pmids)} ({len(overlap_setfit)} from baseline)")

# Check 2: Total unique PMIDs
all_pmids = ling_pmids | setfit_pmids
print(f"   Total unique PMIDs (Linguistic OR SetFit): {len(all_pmids)}")
print(f"   Union dataset total: {len(df_union)}")

# Check 3: File 1a should be subset of baseline
check_1a = baseline_pmids_1a - baseline_pmids
if check_1a:
    print(f"   ⚠️  WARNING: {len(check_1a)} PMIDs in File 1a not in baseline inventory")
else:
    print(f"   ✅ File 1a is subset of baseline inventory")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nFiles Created:")
print(f"  File 1a (Baseline by PMID):        {len(df_1a):>6} papers → {FILE_1A.name}")
print(f"  File 1b (Baseline by Entity):      {len(df_1b):>6} papers → {FILE_1B.name}")
print(f"  File 2 (Linguistic, All):          {len(df_2):>6} papers → {FILE_2.name}")
print(f"  File 3 (SetFit, All):              {len(df_3):>6} papers → {FILE_3.name}")

print(f"\nQuality Indicators (Very High Confidence):")
print(f"  File 1a: {stats_1a['very_high_conf']:>6} ({stats_1a.get('very_high_conf_pct', 0):>5.1f}%)")
print(f"  File 1b: {stats_1b['very_high_conf']:>6} ({stats_1b.get('very_high_conf_pct', 0):>5.1f}%)")
print(f"  File 2:  {stats_2['very_high_conf']:>6} ({stats_2.get('very_high_conf_pct', 0):>5.1f}%)")
print(f"  File 3:  {stats_3['very_high_conf']:>6} ({stats_3.get('very_high_conf_pct', 0):>5.1f}%)")

print(f"\nStatistics report: {STATS_FILE}")

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
