#!/usr/bin/env python3
"""
Deduplicate high-confidence linguistic papers (novel resources).

Filter criteria:
- db_keyword_found == True
- has_resource_url == True
- baseline_entity_match is empty (novel resources only)

Deduplication strategy:
1. Primary: Match by normalized resource_url
2. Secondary: Match by normalized primary_entity (long or short)
3. Aggregate duplicates: Keep earliest paper, join PMIDs
"""

import pandas as pd
import re
from pathlib import Path
from collections import defaultdict

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
FILTERED_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/data/filtered'
RESULTS_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/results'

# Input file
INPUT_FILE = FILTERED_DIR / 'linguistic_excluding_baseline.csv'

# Output files
OUTPUT_FILE = RESULTS_DIR / 'linguistic_high_conf_dedup.csv'
UNCLEAR_FILE = RESULTS_DIR / 'linguistic_dedup_unclear_cases.csv'
STATS_FILE = RESULTS_DIR / 'linguistic_dedup_statistics.txt'

# Create results dir
RESULTS_DIR.mkdir(exist_ok=True)

print("="*80)
print("Deduplicating High-Confidence Linguistic Papers")
print("="*80)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clean_url(url):
    """
    Normalize URL for matching:
    - Remove trailing slash
    - Replace https:// with http://
    - Lowercase domain (before first single slash)
    """
    if pd.isna(url) or url == '':
        return ''

    url = str(url).strip()

    # Split at first single slash to lowercase the domain
    url_parts = re.search(
        r'(?P<before_slash>.*?)(?<!/)\/(?!\/)(?P<after_slash>.*)',
        url,
        re.X
    )

    if url_parts:
        url = url_parts['before_slash'].lower() + '/' + url_parts['after_slash']
    else:
        url = url.lower()

    # Replace https with http and remove trailing slash
    return re.sub('https', 'http', url.rstrip('/'))

def normalize_entity(name):
    """Normalize entity name for matching"""
    if pd.isna(name) or name == '':
        return ''

    name = str(name).lower().strip()

    # Remove common punctuation and extra spaces
    name = re.sub(r'[_\-\.]', ' ', name)
    name = ' '.join(name.split())

    return name

def get_primary_entity(row):
    """Get primary entity (prefer long, fallback to short)"""
    if pd.notna(row['primary_entity_long']) and row['primary_entity_long'] != '':
        return str(row['primary_entity_long'])
    elif pd.notna(row['primary_entity_short']) and row['primary_entity_short'] != '':
        return str(row['primary_entity_short'])
    return ''

# ============================================================================
# LOAD AND FILTER DATA
# ============================================================================

print("\n1. Loading linguistic_excluding_baseline.csv...")
df = pd.read_csv(INPUT_FILE)
print(f"   Total papers: {len(df)}")

# Filter for high-confidence novel resources
print("\n2. Filtering for high-confidence novel resources...")
print("   Criteria:")
print("   - db_keyword_found == True")
print("   - has_resource_url == True")
print("   - baseline_entity_match is empty (novel)")

# Handle baseline_entity_match (might be NaN or empty string)
df['baseline_entity_match'] = df['baseline_entity_match'].fillna('')

filtered = df[
    (df['db_keyword_found'] == True) &
    (df['has_resource_url'] == True) &
    (df['baseline_entity_match'] == '')
].copy()

print(f"\n   Filtered papers: {len(filtered)}")

# ============================================================================
# PREPARE FOR DEDUPLICATION
# ============================================================================

print("\n3. Preparing data for deduplication...")

# Clean URLs and normalize entities
filtered['clean_url'] = filtered['resource_url'].apply(clean_url)
filtered['primary_entity'] = filtered.apply(get_primary_entity, axis=1)
filtered['norm_entity'] = filtered['primary_entity'].apply(normalize_entity)

# Add match keys
filtered['url_entity_key'] = filtered['clean_url'] + '||' + filtered['norm_entity']

print(f"   Unique URLs: {filtered['clean_url'].nunique()}")
print(f"   Unique entities: {filtered['norm_entity'].nunique()}")
print(f"   Unique URL+Entity pairs: {filtered['url_entity_key'].nunique()}")

# ============================================================================
# FIND DUPLICATES
# ============================================================================

print("\n4. Finding duplicates...")

# Group 1: Exact URL+Entity match
duplicates_url_entity = filtered.duplicated(['clean_url', 'norm_entity'], keep=False)
dup_url_entity_df = filtered[duplicates_url_entity]
print(f"   Duplicates by URL+Entity: {len(dup_url_entity_df)} papers in {dup_url_entity_df.groupby(['clean_url', 'norm_entity']).ngroups} groups")

# Group 2: Same URL, different entity (potential conflicts)
url_counts = filtered['clean_url'].value_counts()
multi_entity_urls = url_counts[url_counts > 1].index
same_url_diff_entity = filtered[
    (filtered['clean_url'].isin(multi_entity_urls)) &
    (~duplicates_url_entity)
]
print(f"   Same URL, different entities: {len(same_url_diff_entity)} papers in {len(multi_entity_urls)} URL groups")

# Group 3: Same entity, different URL (potential conflicts)
entity_counts = filtered[filtered['norm_entity'] != '']['norm_entity'].value_counts()
multi_url_entities = entity_counts[entity_counts > 1].index
same_entity_diff_url = filtered[
    (filtered['norm_entity'].isin(multi_url_entities)) &
    (~duplicates_url_entity) &
    (~filtered['clean_url'].isin(multi_entity_urls))
]
print(f"   Same entity, different URLs: {len(same_entity_diff_url)} papers in {len(multi_url_entities)} entity groups")

# ============================================================================
# IDENTIFY UNCLEAR CASES
# ============================================================================

print("\n5. Identifying unclear cases...")

unclear_cases = []

# Unclear Case 1: Same URL, different entities
if len(same_url_diff_entity) > 0:
    for url in multi_entity_urls:
        url_group = filtered[filtered['clean_url'] == url]
        if len(url_group) > 1:
            entities = url_group['primary_entity'].unique()
            if len(entities) > 1:
                for _, row in url_group.iterrows():
                    unclear_cases.append({
                        'pmid': row['pmid'],
                        'title': row['title'],
                        'primary_entity': row['primary_entity'],
                        'resource_url': row['resource_url'],
                        'issue': f"Same URL, different entities: {', '.join(entities[:3])}",
                        'group_size': len(url_group),
                        'url_group': url
                    })

# Unclear Case 2: Same entity, different URLs
if len(same_entity_diff_url) > 0:
    for entity in multi_url_entities:
        entity_group = filtered[filtered['norm_entity'] == normalize_entity(entity)]
        if len(entity_group) > 1:
            urls = entity_group['resource_url'].unique()
            if len(urls) > 1:
                for _, row in entity_group.iterrows():
                    unclear_cases.append({
                        'pmid': row['pmid'],
                        'title': row['title'],
                        'primary_entity': row['primary_entity'],
                        'resource_url': row['resource_url'],
                        'issue': f"Same entity, different URLs: {len(urls)} URLs found",
                        'group_size': len(entity_group),
                        'entity_group': entity
                    })

unclear_df = pd.DataFrame(unclear_cases)
if len(unclear_df) > 0:
    unclear_df.to_csv(UNCLEAR_FILE, index=False)
    print(f"   Found {len(unclear_df)} unclear cases")
    print(f"   Saved to: {UNCLEAR_FILE}")
else:
    print(f"   No unclear cases found")

# ============================================================================
# DEDUPLICATE
# ============================================================================

print("\n6. Deduplicating...")

# Strategy: Group by (clean_url, norm_entity) and aggregate
unique_papers = filtered[~duplicates_url_entity]
duplicate_papers = filtered[duplicates_url_entity]

print(f"   Unique papers: {len(unique_papers)}")
print(f"   Duplicate papers to merge: {len(duplicate_papers)}")

if len(duplicate_papers) > 0:
    # For duplicates, keep earliest paper and join PMIDs
    duplicate_merged = duplicate_papers.sort_values('pmid').groupby(
        ['clean_url', 'norm_entity']
    ).agg({
        'pmid': lambda x: ', '.join(map(str, x)),
        'title': 'first',
        'abstract': 'first',
        'in_linguistic': 'first',
        'in_setfit': 'first',
        'ling_score': 'first',
        'setfit_confidence': 'first',
        'primary_entity_long': 'first',
        'primary_entity_short': 'first',
        'primary_score': 'max',
        'status': 'first',
        'matched_long_short': 'first',
        'all_long': lambda x: ' | '.join(set(' | '.join(str(v) for v in x if pd.notna(v)).split(' | ')) - {'', 'nan'}),
        'all_short': lambda x: ' | '.join(set(' | '.join(str(v) for v in x if pd.notna(v)).split(' | ')) - {'', 'nan'}),
        'ner_source': 'first',
        'ner_confidence': 'max',
        'entity_from_title': 'first',
        'db_keyword_found': 'first',
        'very_high_conf': 'first',
        'title_entity_in_ner': 'first',
        'baseline_entity_match': 'first',
        'all_urls': 'first',
        'resource_url': 'first',
        'has_resource_url': 'first',
        'url_context': 'first',
    }).reset_index()

    # Add article count
    duplicate_merged['article_count'] = duplicate_papers.groupby(
        ['clean_url', 'norm_entity']
    ).size().values

    # Drop temporary columns
    duplicate_merged = duplicate_merged.drop(['clean_url', 'norm_entity'], axis=1)
else:
    duplicate_merged = pd.DataFrame()

# Add article_count to unique papers
unique_papers['article_count'] = 1

# Drop temporary columns from unique
unique_papers = unique_papers.drop(['clean_url', 'norm_entity', 'primary_entity', 'url_entity_key'], axis=1)

# Combine
if len(duplicate_merged) > 0:
    dedup_df = pd.concat([unique_papers, duplicate_merged], ignore_index=True)
else:
    dedup_df = unique_papers

# Sort by article count (descending) then primary_score
dedup_df = dedup_df.sort_values(['article_count', 'primary_score'], ascending=[False, False])

print(f"\n   Final deduplicated count: {len(dedup_df)}")
print(f"   Papers removed: {len(filtered) - len(dedup_df)}")

# ============================================================================
# SAVE OUTPUT
# ============================================================================

print("\n7. Saving output...")
dedup_df.to_csv(OUTPUT_FILE, index=False)
print(f"   Saved to: {OUTPUT_FILE}")

# ============================================================================
# GENERATE STATISTICS
# ============================================================================

print("\n8. Generating statistics...")

stats = []
stats.append("="*80)
stats.append("LINGUISTIC HIGH-CONFIDENCE DEDUPLICATION STATISTICS")
stats.append("="*80)
stats.append("")

stats.append("Input Filtering:")
stats.append(f"  Total linguistic papers:           {len(df)}")
stats.append(f"  db_keyword_found == True:          {(df['db_keyword_found'] == True).sum()}")
stats.append(f"  has_resource_url == True:          {(df['has_resource_url'] == True).sum()}")
stats.append(f"  baseline_entity_match empty:       {(df['baseline_entity_match'] == '').sum()}")
stats.append(f"  Meeting all criteria:              {len(filtered)}")
stats.append("")

stats.append("Duplication Analysis:")
stats.append(f"  Unique URL+Entity pairs:           {filtered['url_entity_key'].nunique()}")
stats.append(f"  Duplicates by URL+Entity:          {len(dup_url_entity_df)} papers")
stats.append(f"  Same URL, different entities:      {len(same_url_diff_entity)} papers")
stats.append(f"  Same entity, different URLs:       {len(same_entity_diff_url)} papers")
stats.append(f"  Unclear cases identified:          {len(unclear_df)}")
stats.append("")

stats.append("Deduplication Results:")
stats.append(f"  Papers before deduplication:       {len(filtered)}")
stats.append(f"  Papers after deduplication:        {len(dedup_df)}")
stats.append(f"  Papers removed as duplicates:      {len(filtered) - len(dedup_df)}")
stats.append(f"  Reduction:                         {((len(filtered) - len(dedup_df)) / len(filtered) * 100):.1f}%")
stats.append("")

stats.append("Article Count Distribution:")
article_counts = dedup_df['article_count'].value_counts().sort_index()
for count, freq in article_counts.items():
    stats.append(f"  {count} paper(s):  {freq} resources")
stats.append("")

stats.append("Top Resources by Article Count:")
top_resources = dedup_df.nlargest(10, 'article_count')[
    ['pmid', 'primary_entity_long', 'primary_entity_short', 'resource_url', 'article_count']
]
for _, row in top_resources.iterrows():
    entity = row['primary_entity_long'] if pd.notna(row['primary_entity_long']) and row['primary_entity_long'] != '' else row['primary_entity_short']
    stats.append(f"  {entity[:40]:40s} : {row['article_count']} papers")
stats.append("")

stats_text = '\n'.join(stats)
with open(STATS_FILE, 'w') as f:
    f.write(stats_text)

print(stats_text)

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print(f"\nOutput files:")
print(f"  Deduplicated data: {OUTPUT_FILE}")
print(f"  Unclear cases:     {UNCLEAR_FILE}")
print(f"  Statistics:        {STATS_FILE}")
print(f"\nFinal count: {len(dedup_df)} unique resources")
