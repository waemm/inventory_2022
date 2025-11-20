#!/usr/bin/env python3
"""
Improved Deduplication of High-Confidence Linguistic Papers

Enhancement over script 12:
- Uses URL similarity scoring (threshold 0.85) to match URL variations
- Handles http/https, trailing slashes, path variations, subdomains
- More sophisticated entity matching

Filter criteria:
- db_keyword_found == True
- has_resource_url == True
- baseline_entity_match is empty (novel resources only)

Deduplication strategy:
1. URL similarity matching (0.85 threshold)
2. Entity normalization matching
3. Aggregate duplicates: Keep earliest paper, join PMIDs
"""

import pandas as pd
import re
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse
from difflib import SequenceMatcher

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
FILTERED_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/data/filtered'
RESULTS_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/results'

# Input file
INPUT_FILE = FILTERED_DIR / 'linguistic_excluding_baseline.csv'

# Output files
OUTPUT_FILE = RESULTS_DIR / 'linguistic_high_conf_dedup_v2.csv'
UNCLEAR_FILE = RESULTS_DIR / 'linguistic_dedup_unclear_cases_v2.csv'
STATS_FILE = RESULTS_DIR / 'linguistic_dedup_statistics_v2.txt'

# Create results dir
RESULTS_DIR.mkdir(exist_ok=True)

print("="*80)
print("Improved Deduplication - High-Confidence Linguistic Papers")
print("="*80)

# ============================================================================
# URL SIMILARITY FUNCTIONS (from script 13)
# ============================================================================

def parse_url_components(url):
    """Parse URL into normalized components for comparison."""
    if pd.isna(url) or url == '':
        return None

    url = str(url).strip()

    # Add http:// if missing
    if not url.startswith(('http://', 'https://', 'ftp://')):
        url = 'http://' + url

    parsed = urlparse(url)

    # Extract components
    protocol = parsed.scheme
    full_domain = parsed.netloc.lower()
    path = parsed.path.rstrip('/').lower()

    # Split domain into parts
    domain_parts = full_domain.split('.')

    # Extract TLD (last part)
    tld = '.' + domain_parts[-1] if len(domain_parts) > 0 else ''

    # Extract main domain (second-to-last part)
    if len(domain_parts) >= 2:
        # Handle compound TLDs like .ac.uk, .co.uk, .edu.cn
        if len(domain_parts) >= 3 and domain_parts[-2] in ['ac', 'co', 'edu', 'gov']:
            main_domain = domain_parts[-3]
            tld = '.' + '.'.join(domain_parts[-2:])
            subdomain = '.'.join(domain_parts[:-3]) if len(domain_parts) > 3 else ''
        else:
            main_domain = domain_parts[-2]
            subdomain = '.'.join(domain_parts[:-2]) if len(domain_parts) > 2 else ''
    else:
        main_domain = full_domain
        subdomain = ''

    return {
        'protocol': protocol,
        'subdomain': subdomain,
        'domain': main_domain,
        'tld': tld,
        'path': path,
        'full_domain': full_domain,
        'original_url': url
    }

def normalize_url_aggressive(url):
    """Aggressively normalize URL for matching."""
    components = parse_url_components(url)
    if not components:
        return ''

    # Build normalized form: domain + tld + path
    subdomain = components['subdomain']

    # Remove www from subdomain
    if subdomain == 'www':
        subdomain = ''
    elif subdomain.endswith('.www'):
        subdomain = subdomain[:-4]
    elif subdomain.startswith('www.'):
        subdomain = subdomain[4:]

    # Build normalized URL
    if subdomain:
        normalized = f"{subdomain}.{components['domain']}{components['tld']}{components['path']}"
    else:
        normalized = f"{components['domain']}{components['tld']}{components['path']}"

    return normalized

def compute_url_similarity(url1, url2):
    """Compute similarity score between two URLs (0.0 to 1.0)."""
    c1 = parse_url_components(url1)
    c2 = parse_url_components(url2)

    if not c1 or not c2:
        return 0.0

    # Exact match after aggressive normalization
    norm1 = normalize_url_aggressive(url1)
    norm2 = normalize_url_aggressive(url2)

    if norm1 == norm2:
        return 1.0

    # Domain similarity
    domain_sim = SequenceMatcher(None, c1['domain'], c2['domain']).ratio()

    # Path similarity
    path_sim = SequenceMatcher(None, c1['path'], c2['path']).ratio() if c1['path'] or c2['path'] else 1.0

    # Subdomain similarity
    subdomain_sim = SequenceMatcher(None, c1['subdomain'], c2['subdomain']).ratio()

    # Scoring logic
    score = 0.0

    # Case 1: Same main domain and TLD
    if c1['domain'] == c2['domain'] and c1['tld'] == c2['tld']:
        score = 0.8

        # Same path
        if c1['path'] == c2['path']:
            score += 0.2
        # Similar path
        elif path_sim > 0.8:
            score += 0.15
        # Different path but subdomain similar
        elif subdomain_sim > 0.8:
            score += 0.1

    # Case 2: Very similar domain (likely typo or variation)
    elif domain_sim > 0.85:
        score = 0.5

        # Same TLD
        if c1['tld'] == c2['tld']:
            score += 0.2

        # Similar path
        if path_sim > 0.8:
            score += 0.2

    # Case 3: Different domain but very similar subdomains and paths
    else:
        # Check if one is subdomain of the other
        if c1['full_domain'] in c2['full_domain'] or c2['full_domain'] in c1['full_domain']:
            score = 0.6 + (path_sim * 0.3)
        else:
            # Different domains
            score = domain_sim * 0.4

    return score

def urls_are_similar(url1, url2, threshold=0.85):
    """Check if two URLs are similar above threshold."""
    return compute_url_similarity(url1, url2) >= threshold

# ============================================================================
# ENTITY NORMALIZATION
# ============================================================================

def normalize_entity(name):
    """Normalize entity name for matching."""
    if pd.isna(name) or name == '':
        return ''

    name = str(name).lower().strip()

    # Remove common punctuation and extra spaces
    name = re.sub(r'[_\-\.]', ' ', name)
    name = ' '.join(name.split())

    return name

def get_primary_entity(row):
    """Get primary entity (prefer long, fallback to short)."""
    if pd.notna(row['primary_entity_long']) and row['primary_entity_long'] != '':
        return str(row['primary_entity_long'])
    elif pd.notna(row['primary_entity_short']) and row['primary_entity_short'] != '':
        return str(row['primary_entity_short'])
    return ''

# ============================================================================
# URL CLUSTERING
# ============================================================================

def cluster_similar_urls(urls, threshold=0.85):
    """
    Cluster URLs by similarity using union-find.

    Returns dict mapping each URL to its canonical URL (first in cluster).
    """
    if len(urls) == 0:
        return {}

    urls_list = list(urls)
    n = len(urls_list)

    # Union-find data structure
    parent = list(range(n))

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            # Always make lower index the parent (to preserve first URL as canonical)
            if px < py:
                parent[py] = px
            else:
                parent[px] = py

    # Find similar pairs and union them
    for i in range(n):
        for j in range(i+1, n):
            if urls_are_similar(urls_list[i], urls_list[j], threshold):
                union(i, j)

    # Build mapping from URL to canonical URL
    clusters = defaultdict(list)
    for i in range(n):
        root = find(i)
        clusters[root].append(urls_list[i])

    # Create mapping: url -> canonical_url (first in cluster)
    url_to_canonical = {}
    for cluster in clusters.values():
        canonical = cluster[0]  # First URL in cluster
        for url in cluster:
            url_to_canonical[url] = canonical

    return url_to_canonical

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

# Get primary entity
filtered['primary_entity'] = filtered.apply(get_primary_entity, axis=1)
filtered['norm_entity'] = filtered['primary_entity'].apply(normalize_entity)

print(f"   Unique URLs before clustering: {filtered['resource_url'].nunique()}")
print(f"   Unique entities: {filtered['norm_entity'].nunique()}")

# ============================================================================
# CLUSTER SIMILAR URLs
# ============================================================================

print("\n4. Clustering similar URLs (threshold=0.85)...")

# Get all unique URLs
all_urls = filtered['resource_url'].unique()

# Cluster them
url_to_canonical = cluster_similar_urls(all_urls, threshold=0.85)

# Map each paper's URL to canonical URL
filtered['canonical_url'] = filtered['resource_url'].map(url_to_canonical)

# Count URL merges
num_merged = len(all_urls) - len(set(url_to_canonical.values()))
print(f"   URLs before clustering: {len(all_urls)}")
print(f"   URLs after clustering: {len(set(url_to_canonical.values()))}")
print(f"   URLs merged: {num_merged}")

# ============================================================================
# FIND DUPLICATES
# ============================================================================

print("\n5. Finding duplicates by (canonical_url, norm_entity)...")

# Create deduplication key
filtered['dedup_key'] = filtered['canonical_url'] + '||' + filtered['norm_entity']

# Find duplicates
duplicates = filtered.duplicated(['canonical_url', 'norm_entity'], keep=False)
dup_df = filtered[duplicates]
unique_df = filtered[~duplicates]

print(f"   Duplicates by (canonical_url, entity): {len(dup_df)} papers in {dup_df.groupby(['canonical_url', 'norm_entity']).ngroups} groups")

# Find unclear cases (same canonical URL, different entities)
url_counts = filtered['canonical_url'].value_counts()
multi_entity_urls = url_counts[url_counts > 1].index
same_url_diff_entity = filtered[
    (filtered['canonical_url'].isin(multi_entity_urls))
].copy()

# Check if they have different entities
unclear_cases = []
for url in multi_entity_urls:
    url_group = same_url_diff_entity[same_url_diff_entity['canonical_url'] == url]
    entities = url_group['norm_entity'].unique()
    if len(entities) > 1:
        for _, row in url_group.iterrows():
            unclear_cases.append({
                'pmid': row['pmid'],
                'title': row['title'],
                'primary_entity': row['primary_entity'],
                'resource_url': row['resource_url'],
                'canonical_url': row['canonical_url'],
                'issue': f"Same URL, different entities: {', '.join(entities[:3])}",
                'group_size': len(url_group)
            })

print(f"   Unclear cases (same URL, different entities): {len(unclear_cases)}")

# ============================================================================
# SAVE UNCLEAR CASES
# ============================================================================

if unclear_cases:
    unclear_df = pd.DataFrame(unclear_cases)
    unclear_df.to_csv(UNCLEAR_FILE, index=False)
    print(f"   Saved unclear cases to: {UNCLEAR_FILE}")

# ============================================================================
# DEDUPLICATE
# ============================================================================

print("\n6. Deduplicating...")

if len(dup_df) > 0:
    # For duplicates, keep earliest paper and join PMIDs
    duplicate_merged = dup_df.sort_values('pmid').groupby(
        ['canonical_url', 'norm_entity']
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
        'resource_url': 'first',  # Keep first (canonical)
        'has_resource_url': 'first',
        'url_context': 'first',
    }).reset_index()

    # Add article count
    duplicate_merged['article_count'] = dup_df.groupby(
        ['canonical_url', 'norm_entity']
    ).size().values

    # Drop temporary columns
    duplicate_merged = duplicate_merged.drop(['canonical_url', 'norm_entity'], axis=1)
else:
    duplicate_merged = pd.DataFrame()

# Add article_count to unique papers
unique_df['article_count'] = 1

# Drop temporary columns from unique
unique_df = unique_df.drop(['primary_entity', 'norm_entity', 'canonical_url', 'dedup_key'], axis=1)

# Combine
if len(duplicate_merged) > 0:
    dedup_df = pd.concat([unique_df, duplicate_merged], ignore_index=True)
else:
    dedup_df = unique_df

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
stats.append("LINGUISTIC HIGH-CONFIDENCE DEDUPLICATION STATISTICS (v2 - IMPROVED)")
stats.append("="*80)
stats.append("")

stats.append("Input Filtering:")
stats.append(f"  Total linguistic papers:           {len(df)}")
stats.append(f"  db_keyword_found == True:          {(df['db_keyword_found'] == True).sum()}")
stats.append(f"  has_resource_url == True:          {(df['has_resource_url'] == True).sum()}")
stats.append(f"  baseline_entity_match empty:       {(df['baseline_entity_match'] == '').sum()}")
stats.append(f"  Meeting all criteria:              {len(filtered)}")
stats.append("")

stats.append("URL Clustering (Similarity ≥ 0.85):")
stats.append(f"  Unique URLs before clustering:     {len(all_urls)}")
stats.append(f"  Unique URLs after clustering:      {len(set(url_to_canonical.values()))}")
stats.append(f"  URLs merged:                       {num_merged}")
stats.append("")

stats.append("Duplication Analysis:")
stats.append(f"  Unique (canonical_url, entity):    {len(unique_df)}")
stats.append(f"  Duplicates to merge:               {len(dup_df)} papers in {dup_df.groupby(['canonical_url', 'norm_entity']).ngroups if len(dup_df) > 0 else 0} groups")
stats.append(f"  Unclear cases identified:          {len(unclear_cases)}")
stats.append("")

stats.append("Deduplication Results:")
stats.append(f"  Papers before deduplication:       {len(filtered)}")
stats.append(f"  Papers after deduplication:        {len(dedup_df)}")
stats.append(f"  Papers removed as duplicates:      {len(filtered) - len(dedup_df)}")
stats.append(f"  Reduction:                         {((len(filtered) - len(dedup_df)) / len(filtered) * 100):.1f}%")
stats.append("")

stats.append("Comparison with v1 (Script 12):")
stats.append(f"  v1 result:                         974 unique resources")
stats.append(f"  v2 result (improved):              {len(dedup_df)} unique resources")
stats.append(f"  Additional merges:                 {974 - len(dedup_df)}")
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
print(f"Improvement: {974 - len(dedup_df)} additional merges vs v1")
