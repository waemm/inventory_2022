#!/usr/bin/env python3
"""
Unified Deduplication for Sets A, B, and C

Set A: Linguistic papers (all, including baseline)
Set B: SetFit papers (all, including baseline)
Set C: Union of deduplicated A + B

Created: 2025-11-20
Purpose: Complete three-strategy comparison with full baseline inclusion
"""

import pandas as pd
import re
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse
from difflib import SequenceMatcher
from datetime import datetime

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
FILTERED_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/data/filtered'
RESULTS_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/results/deduplicated'

# Input files
INPUT_SET_A = FILTERED_DIR / 'linguistic_all_papers.csv'
INPUT_SET_B = FILTERED_DIR / 'setfit_all_papers.csv'

# Output files
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_SET_A = RESULTS_DIR / 'set_a_linguistic_dedup.csv'
OUTPUT_SET_B = RESULTS_DIR / 'set_b_setfit_dedup.csv'
OUTPUT_SET_C = RESULTS_DIR / 'set_c_union_dedup.csv'
STATS_FILE = RESULTS_DIR / 'deduplication_statistics.txt'

print("="*80)
print("UNIFIED DEDUPLICATION FOR SETS A, B, AND C")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# URL SIMILARITY FUNCTIONS
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
# CORE DEDUPLICATION FUNCTION
# ============================================================================

def deduplicate_dataset(df, dataset_name, filter_criteria=True):
    """
    Deduplicate a dataset using URL clustering and entity matching.

    Args:
        df: DataFrame to deduplicate
        dataset_name: Name for logging (e.g., "Set A")
        filter_criteria: If True, filter for high-conf resources (db_keyword, has_url)

    Returns:
        Deduplicated DataFrame
    """
    print(f"\n{'='*80}")
    print(f"DEDUPLICATING {dataset_name}")
    print(f"{'='*80}")

    print(f"\n1. Input: {len(df)} papers")

    # Filter for high-confidence resources if requested
    if filter_criteria:
        print("\n2. Filtering for high-confidence resources...")
        print("   Criteria:")
        print("   - db_keyword_found == True")
        print("   - has_resource_url == True")

        filtered = df[
            (df['db_keyword_found'] == True) &
            (df['has_resource_url'] == True)
        ].copy()

        print(f"   Filtered: {len(filtered)} papers")
    else:
        filtered = df.copy()
        print("\n2. No filtering applied (using all papers)")

    # Prepare for deduplication
    print("\n3. Preparing data for deduplication...")

    # Get primary entity
    filtered['primary_entity'] = filtered.apply(get_primary_entity, axis=1)
    filtered['norm_entity'] = filtered['primary_entity'].apply(normalize_entity)

    print(f"   Unique URLs: {filtered['resource_url'].nunique()}")
    print(f"   Unique entities: {filtered['norm_entity'].nunique()}")

    # Cluster similar URLs
    print("\n4. Clustering similar URLs (threshold=0.85)...")

    all_urls = filtered['resource_url'].unique()
    url_to_canonical = cluster_similar_urls(all_urls, threshold=0.85)
    filtered['canonical_url'] = filtered['resource_url'].map(url_to_canonical)

    num_merged = len(all_urls) - len(set(url_to_canonical.values()))
    print(f"   URLs before clustering: {len(all_urls)}")
    print(f"   URLs after clustering: {len(set(url_to_canonical.values()))}")
    print(f"   URLs merged: {num_merged}")

    # Find duplicates
    print("\n5. Finding duplicates by (canonical_url, norm_entity)...")

    filtered['dedup_key'] = filtered['canonical_url'] + '||' + filtered['norm_entity']

    duplicates = filtered.duplicated(['canonical_url', 'norm_entity'], keep=False)
    dup_df = filtered[duplicates]
    unique_df = filtered[~duplicates]

    print(f"   Duplicates: {len(dup_df)} papers in {dup_df.groupby(['canonical_url', 'norm_entity']).ngroups if len(dup_df) > 0 else 0} groups")

    # Deduplicate
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
    print(f"   Reduction: {((len(filtered) - len(dedup_df)) / len(filtered) * 100):.1f}%")

    return dedup_df

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Load data
print("\nLoading datasets...")
df_a = pd.read_csv(INPUT_SET_A)
df_b = pd.read_csv(INPUT_SET_B)
print(f"  Set A (Linguistic): {len(df_a)} papers")
print(f"  Set B (SetFit): {len(df_b)} papers")

# Deduplicate Set A
dedup_a = deduplicate_dataset(df_a, "SET A (LINGUISTIC)", filter_criteria=True)
dedup_a.to_csv(OUTPUT_SET_A, index=False)
print(f"\n✓ Saved Set A: {OUTPUT_SET_A}")

# Deduplicate Set B
dedup_b = deduplicate_dataset(df_b, "SET B (SETFIT)", filter_criteria=True)
dedup_b.to_csv(OUTPUT_SET_B, index=False)
print(f"\n✓ Saved Set B: {OUTPUT_SET_B}")

# Create Set C (Union of deduplicated A + B)
print(f"\n{'='*80}")
print(f"CREATING SET C (UNION OF DEDUPLICATED A + B)")
print(f"{'='*80}")

# Combine dedup_a and dedup_b
df_c = pd.concat([dedup_a, dedup_b], ignore_index=True)
print(f"\n1. Combined A + B: {len(df_c)} total rows")

# Deduplicate the union
dedup_c = deduplicate_dataset(df_c, "SET C (UNION)", filter_criteria=False)
dedup_c.to_csv(OUTPUT_SET_C, index=False)
print(f"\n✓ Saved Set C: {OUTPUT_SET_C}")

# ============================================================================
# GENERATE STATISTICS
# ============================================================================

print(f"\n{'='*80}")
print("GENERATING STATISTICS")
print(f"{'='*80}")

stats = []
stats.append("="*80)
stats.append("UNIFIED DEDUPLICATION STATISTICS")
stats.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
stats.append("="*80)
stats.append("")

stats.append("INPUT DATA:")
stats.append(f"  Set A (Linguistic): {len(df_a):>6} papers")
stats.append(f"  Set B (SetFit):     {len(df_b):>6} papers")
stats.append("")

stats.append("DEDUPLICATED OUTPUTS:")
stats.append(f"  Set A: {len(dedup_a):>6} unique resources")
stats.append(f"  Set B: {len(dedup_b):>6} unique resources")
stats.append(f"  Set C: {len(dedup_c):>6} unique resources (union)")
stats.append("")

stats.append("OVERLAP ANALYSIS:")
a_pmids = set()
for pmids in dedup_a['pmid'].astype(str):
    a_pmids.update(pmids.split(', '))

b_pmids = set()
for pmids in dedup_b['pmid'].astype(str):
    b_pmids.update(pmids.split(', '))

overlap = a_pmids & b_pmids
only_a = a_pmids - b_pmids
only_b = b_pmids - a_pmids

stats.append(f"  Papers only in A:   {len(only_a):>6}")
stats.append(f"  Papers only in B:   {len(only_b):>6}")
stats.append(f"  Papers in both:     {len(overlap):>6}")
stats.append(f"  Overlap rate:       {(len(overlap)/(len(a_pmids | b_pmids))*100):>5.1f}%")
stats.append("")

stats.append("TOP RESOURCES BY ARTICLE COUNT:")
stats.append("\n  Set A (Linguistic):")
for _, row in dedup_a.nlargest(5, 'article_count').iterrows():
    entity = row['primary_entity_long'] if pd.notna(row['primary_entity_long']) else row['primary_entity_short']
    stats.append(f"    {entity[:50]:50s} : {row['article_count']} papers")

stats.append("\n  Set B (SetFit):")
for _, row in dedup_b.nlargest(5, 'article_count').iterrows():
    entity = row['primary_entity_long'] if pd.notna(row['primary_entity_long']) else row['primary_entity_short']
    stats.append(f"    {entity[:50]:50s} : {row['article_count']} papers")

stats.append("\n  Set C (Union):")
for _, row in dedup_c.nlargest(5, 'article_count').iterrows():
    entity = row['primary_entity_long'] if pd.notna(row['primary_entity_long']) else row['primary_entity_short']
    stats.append(f"    {entity[:50]:50s} : {row['article_count']} papers")

stats.append("")

stats_text = '\n'.join(stats)
with open(STATS_FILE, 'w') as f:
    f.write(stats_text)

print(stats_text)

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print(f"\nOutput files:")
print(f"  Set A: {OUTPUT_SET_A}")
print(f"  Set B: {OUTPUT_SET_B}")
print(f"  Set C: {OUTPUT_SET_C}")
print(f"  Stats: {STATS_FILE}")
print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
