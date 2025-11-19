#!/usr/bin/env python3
"""
Analyze Unclear Cases with URL Similarity Scoring

Takes unclear cases from Script 12 and applies URL similarity analysis
to identify which ones should potentially be merged.

Output includes:
- similarity_score: Similarity to other URLs in the same group
- merge_group_id: Unique ID for potential merge groups (e.g., MG001, MG002)
- merge_recommendation: MERGE (≥0.85) or REVIEW (manual check needed)
"""

import pandas as pd
import re
from pathlib import Path
from urllib.parse import urlparse
from difflib import SequenceMatcher
from collections import defaultdict

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
RESULTS_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/results'

# Input (from Script 12)
INPUT_FILE = RESULTS_DIR / 'linguistic_dedup_unclear_cases.csv'

# Output
OUTPUT_FILE = RESULTS_DIR / 'linguistic_unclear_cases_with_similarity.csv'
SUMMARY_FILE = RESULTS_DIR / 'unclear_cases_merge_summary.txt'

print("="*80)
print("Unclear Cases Analysis with URL Similarity Scoring")
print("="*80)

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

def compute_url_similarity(url1, url2):
    """Compute similarity score between two URLs (0.0 to 1.0)."""
    c1 = parse_url_components(url1)
    c2 = parse_url_components(url2)

    if not c1 or not c2:
        return 0.0

    # Normalize for comparison
    def normalize_url(c):
        subdomain = c['subdomain']
        if subdomain == 'www':
            subdomain = ''
        elif subdomain.endswith('.www'):
            subdomain = subdomain[:-4]
        elif subdomain.startswith('www.'):
            subdomain = subdomain[4:]

        if subdomain:
            return f"{subdomain}.{c['domain']}{c['tld']}{c['path']}"
        else:
            return f"{c['domain']}{c['tld']}{c['path']}"

    norm1 = normalize_url(c1)
    norm2 = normalize_url(c2)

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

# ============================================================================
# LOAD AND ANALYZE UNCLEAR CASES
# ============================================================================

print("\n1. Loading unclear cases from Script 12...")
df = pd.read_csv(INPUT_FILE)
print(f"   Total unclear cases: {len(df)}")

# Check what groups we have
if 'url_group' in df.columns:
    group_col = 'url_group'
    print("   Analyzing 'Same URL, different entities' cases")
elif 'entity_group' in df.columns:
    group_col = 'entity_group'
    print("   Analyzing 'Same entity, different URLs' cases")
else:
    print("   ERROR: No group column found")
    exit(1)

print(f"   Number of groups: {df[group_col].nunique()}")

# ============================================================================
# COMPUTE SIMILARITY SCORES FOR EACH GROUP
# ============================================================================

print("\n2. Computing URL similarity scores for each group...")

results = []
merge_groups = []
merge_group_counter = 1

# Group by url_group or entity_group
grouped = df.groupby(group_col)

for group_name, group_df in grouped:
    urls = group_df['resource_url'].unique()

    if len(urls) == 1:
        # Only one URL, no similarity to compute
        for _, row in group_df.iterrows():
            results.append({
                **row.to_dict(),
                'similarity_score': 1.0,
                'max_similarity': 1.0,
                'merge_group_id': '',
                'merge_recommendation': 'SINGLE_URL'
            })
        continue

    # Compute similarity matrix for this group
    similarity_matrix = {}
    for i, url1 in enumerate(urls):
        for j, url2 in enumerate(urls):
            if i != j:
                sim = compute_url_similarity(url1, url2)
                similarity_matrix[(url1, url2)] = sim

    # Find clusters of similar URLs (≥0.85)
    # Use union-find to group similar URLs
    url_to_idx = {url: i for i, url in enumerate(urls)}
    parent = list(range(len(urls)))

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            if px < py:
                parent[py] = px
            else:
                parent[px] = py

    # Union similar URLs
    for (url1, url2), sim in similarity_matrix.items():
        if sim >= 0.85:
            idx1 = url_to_idx[url1]
            idx2 = url_to_idx[url2]
            union(idx1, idx2)

    # Extract clusters
    clusters = defaultdict(list)
    for i, url in enumerate(urls):
        root = find(i)
        clusters[root].append(url)

    # Assign merge group IDs to clusters with 2+ URLs
    cluster_to_group_id = {}
    for cluster_urls in clusters.values():
        if len(cluster_urls) >= 2:
            cluster_to_group_id[tuple(sorted(cluster_urls))] = f"MG{merge_group_counter:03d}"
            merge_group_counter += 1

    # Assign results for each paper in this group
    for _, row in group_df.iterrows():
        url = row['resource_url']

        # Find max similarity for this URL
        max_sim = 0.0
        for other_url in urls:
            if url != other_url:
                sim = similarity_matrix.get((url, other_url), 0.0)
                max_sim = max(max_sim, sim)

        # Find which cluster this URL belongs to
        cluster_key = None
        merge_group_id = ''
        for cluster_urls in clusters.values():
            if url in cluster_urls and len(cluster_urls) >= 2:
                cluster_key = tuple(sorted(cluster_urls))
                merge_group_id = cluster_to_group_id.get(cluster_key, '')
                break

        # Recommendation
        if max_sim >= 0.85:
            recommendation = f"MERGE - High similarity ({max_sim:.2f})"
        elif max_sim >= 0.7:
            recommendation = f"REVIEW - Moderate similarity ({max_sim:.2f})"
        else:
            recommendation = f"KEEP_SEPARATE - Low similarity ({max_sim:.2f})"

        results.append({
            **row.to_dict(),
            'similarity_score': max_sim,
            'max_similarity': max_sim,
            'merge_group_id': merge_group_id,
            'merge_recommendation': recommendation
        })

# ============================================================================
# CREATE OUTPUT DATAFRAME
# ============================================================================

print("\n3. Creating enhanced output file...")

results_df = pd.DataFrame(results)

# Reorder columns to put new ones at the end
original_cols = df.columns.tolist()
new_cols = ['similarity_score', 'max_similarity', 'merge_group_id', 'merge_recommendation']
results_df = results_df[original_cols + new_cols]

# Sort by merge_group_id, then similarity_score
results_df = results_df.sort_values(
    ['merge_group_id', 'similarity_score'],
    ascending=[True, False]
)

# Save
results_df.to_csv(OUTPUT_FILE, index=False)
print(f"   Saved to: {OUTPUT_FILE}")

# ============================================================================
# GENERATE SUMMARY STATISTICS
# ============================================================================

print("\n4. Generating summary statistics...")

# Count recommendations
merge_count = results_df['merge_recommendation'].str.startswith('MERGE').sum()
review_count = results_df['merge_recommendation'].str.startswith('REVIEW').sum()
separate_count = results_df['merge_recommendation'].str.startswith('KEEP_SEPARATE').sum()
single_count = results_df['merge_recommendation'].eq('SINGLE_URL').sum()

# Count merge groups
merge_groups = results_df[results_df['merge_group_id'] != '']['merge_group_id'].nunique()

summary = []
summary.append("="*80)
summary.append("UNCLEAR CASES SIMILARITY ANALYSIS SUMMARY")
summary.append("="*80)
summary.append("")

summary.append(f"Total unclear cases: {len(results_df)}")
summary.append("")

summary.append("Merge Recommendations:")
summary.append(f"  MERGE (similarity ≥ 0.85):           {merge_count} papers")
summary.append(f"  REVIEW (similarity 0.70-0.84):       {review_count} papers")
summary.append(f"  KEEP_SEPARATE (similarity < 0.70):   {separate_count} papers")
summary.append(f"  SINGLE_URL (only one URL in group):  {single_count} papers")
summary.append("")

summary.append(f"Merge Groups Identified: {merge_groups}")
summary.append("")

summary.append("Top Merge Groups (by number of papers):")
if merge_groups > 0:
    merge_group_sizes = results_df[results_df['merge_group_id'] != ''].groupby('merge_group_id').size()
    merge_group_sizes = merge_group_sizes.sort_values(ascending=False)

    for i, (group_id, size) in enumerate(merge_group_sizes.head(10).items(), 1):
        group_papers = results_df[results_df['merge_group_id'] == group_id]
        entity = group_papers.iloc[0][group_col]
        summary.append(f"  {group_id}: {entity[:50]:50s} - {size} papers")
summary.append("")

summary.append("Examples of High Similarity Merges (≥0.85):")
high_sim = results_df[results_df['similarity_score'] >= 0.85].head(10)
for i, (_, row) in enumerate(high_sim.iterrows(), 1):
    summary.append(f"\n  {i}. {row['merge_group_id']} - Similarity: {row['similarity_score']:.3f}")
    summary.append(f"     PMID: {row['pmid']}")
    summary.append(f"     Entity: {row['primary_entity']}")
    summary.append(f"     URL: {row['resource_url']}")

summary_text = '\n'.join(summary)

# Save summary
with open(SUMMARY_FILE, 'w') as f:
    f.write(summary_text)

print(summary_text)

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print(f"\nOutput files:")
print(f"  Enhanced unclear cases: {OUTPUT_FILE}")
print(f"  Summary statistics:     {SUMMARY_FILE}")
print(f"\nMerge groups identified: {merge_groups}")
print(f"Papers recommended to merge: {merge_count}")
