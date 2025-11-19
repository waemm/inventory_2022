#!/usr/bin/env python3
"""
URL Similarity Analysis and Grouping

Analyzes URL variations in unclear deduplication cases and computes
similarity scores to identify URLs that represent the same resource.

Similarity scoring considers:
1. Domain similarity (main domain matching, subdomain variations)
2. Path similarity (normalized paths, trailing slashes)
3. Protocol normalization (http vs https)
4. TLD variations (.com, .org, .edu, etc.)
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

# Input
INPUT_FILE = RESULTS_DIR / 'linguistic_dedup_unclear_cases.csv'

# Output
SIMILARITY_REPORT = RESULTS_DIR / 'url_similarity_report.txt'
SUGGESTED_MERGES = RESULTS_DIR / 'url_suggested_merges.csv'
URL_GROUPS = RESULTS_DIR / 'url_similarity_groups.csv'

print("="*80)
print("URL Similarity Analysis")
print("="*80)

# ============================================================================
# URL NORMALIZATION AND PARSING
# ============================================================================

def parse_url_components(url):
    """
    Parse URL into normalized components for comparison.

    Returns dict with:
    - protocol: http/https/ftp
    - subdomain: www, db, data, etc.
    - domain: main domain name
    - tld: .com, .org, .edu, etc.
    - path: normalized path
    - full_domain: complete domain including subdomains
    """
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
    """
    Aggressively normalize URL for matching:
    - Remove protocol (http vs https)
    - Remove www subdomain
    - Remove trailing slashes
    - Lowercase everything
    """
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

# ============================================================================
# URL SIMILARITY SCORING
# ============================================================================

def compute_url_similarity(url1, url2):
    """
    Compute similarity score between two URLs (0.0 to 1.0).

    Scoring breakdown:
    - Exact match after normalization: 1.0
    - Same domain + tld: 0.8 base score
      - Same path: +0.2
      - Similar path (>0.8): +0.15
      - Same subdomain: +0.0 (already high confidence)
      - Similar subdomain: +0.05
    - Similar domain (>0.85): 0.5 base score
      - Same TLD: +0.2
      - Path similarity: +0.2
    - Different domain: <0.5
    """
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

def find_url_groups(urls, threshold=0.85):
    """
    Group URLs by similarity using threshold-based clustering.

    Args:
        urls: List of URLs
        threshold: Minimum similarity score to group (default 0.85)

    Returns:
        List of groups, where each group is a list of similar URLs
    """
    # Build similarity matrix
    n = len(urls)
    similarity = {}

    for i in range(n):
        for j in range(i+1, n):
            sim = compute_url_similarity(urls[i], urls[j])
            if sim >= threshold:
                similarity[(i, j)] = sim

    # Group URLs using union-find
    parent = list(range(n))

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Union similar URLs
    for (i, j), sim in similarity.items():
        union(i, j)

    # Extract groups
    groups = defaultdict(list)
    for i in range(n):
        root = find(i)
        groups[root].append(urls[i])

    return [group for group in groups.values() if len(group) > 1], similarity

# ============================================================================
# ANALYZE UNCLEAR CASES
# ============================================================================

print("\n1. Loading unclear cases...")
df = pd.read_csv(INPUT_FILE)
print(f"   Total unclear cases: {len(df)}")

# Focus on "Same entity, different URLs"
entity_issues = df[df['issue'].str.contains('Same entity', na=False)].copy()
print(f"   Same entity, different URLs: {len(entity_issues)}")

print("\n2. Grouping by entity and analyzing URL variations...")

results = []
all_groups = []
merge_suggestions = []

# Group by entity
grouped = entity_issues.groupby('entity_group')

for entity, group in grouped:
    urls = group['resource_url'].unique().tolist()

    if len(urls) < 2:
        continue

    # Find URL groups for this entity
    url_groups, similarities = find_url_groups(urls, threshold=0.85)

    # Record results
    for url_group in url_groups:
        if len(url_group) > 1:
            # Get papers for these URLs
            papers = group[group['resource_url'].isin(url_group)]

            results.append({
                'entity': entity,
                'num_urls': len(url_group),
                'num_papers': len(papers),
                'urls': ' | '.join(url_group),
                'pmids': ', '.join(papers['pmid'].astype(str).tolist())
            })

            all_groups.append({
                'entity': entity,
                'group_id': len(all_groups),
                'urls': url_group
            })

            # Merge suggestions
            for url in url_group:
                merge_suggestions.append({
                    'entity': entity,
                    'url': url,
                    'canonical_url': url_group[0],  # Use first as canonical
                    'group_size': len(url_group),
                    'similarity_score': 1.0 if url == url_group[0] else max(
                        [similarities.get((urls.index(url), urls.index(u)), 0.0)
                         for u in url_group if u != url] or [0.0]
                    )
                })

print(f"   Found {len(all_groups)} URL groups that should be merged")
print(f"   Total URLs to be merged: {sum(len(g['urls']) for g in all_groups)}")

# ============================================================================
# GENERATE DETAILED EXAMPLES
# ============================================================================

print("\n3. Generating examples...")

examples = []

for i, res in enumerate(results[:20], 1):
    examples.append(f"\n{'='*60}")
    examples.append(f"Example {i}: {res['entity']}")
    examples.append(f"{'='*60}")
    examples.append(f"Papers: {res['num_papers']}")
    examples.append(f"URLs ({res['num_urls']}):")

    urls = res['urls'].split(' | ')
    for j, url in enumerate(urls, 1):
        examples.append(f"  {j}. {url}")

    # Show similarity scores
    if len(urls) > 1:
        examples.append(f"\nSimilarity scores:")
        for j in range(len(urls)):
            for k in range(j+1, len(urls)):
                sim = compute_url_similarity(urls[j], urls[k])
                examples.append(f"  {urls[j]}")
                examples.append(f"  vs")
                examples.append(f"  {urls[k]}")
                examples.append(f"  → Similarity: {sim:.3f}")
                examples.append("")

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("\n4. Saving results...")

# Save detailed report
report_lines = [
    "="*80,
    "URL SIMILARITY ANALYSIS REPORT",
    "="*80,
    "",
    f"Total unclear cases analyzed: {len(entity_issues)}",
    f"URL groups identified (similarity ≥ 0.85): {len(all_groups)}",
    f"Total URLs to be merged: {sum(len(g['urls']) for g in all_groups)}",
    "",
    "="*80,
    "TOP 20 EXAMPLES",
    "="*80,
] + examples

with open(SIMILARITY_REPORT, 'w') as f:
    f.write('\n'.join(report_lines))

print(f"   Saved report: {SIMILARITY_REPORT}")

# Save merge suggestions
if merge_suggestions:
    merge_df = pd.DataFrame(merge_suggestions)
    merge_df = merge_df.sort_values(['entity', 'similarity_score'], ascending=[True, False])
    merge_df.to_csv(SUGGESTED_MERGES, index=False)
    print(f"   Saved merge suggestions: {SUGGESTED_MERGES}")

# Save URL groups
if results:
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('num_papers', ascending=False)
    results_df.to_csv(URL_GROUPS, index=False)
    print(f"   Saved URL groups: {URL_GROUPS}")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nURL Similarity Analysis:")
print(f"  Unclear cases with multiple URLs: {grouped.ngroups}")
print(f"  URL groups found (similarity ≥ 85%): {len(all_groups)}")
print(f"  URLs that can be merged: {sum(len(g['urls']) for g in all_groups)}")

if results:
    print(f"\nTop 10 entities with URL variations:")
    top_results = sorted(results, key=lambda x: x['num_papers'], reverse=True)[:10]
    for i, res in enumerate(top_results, 1):
        print(f"  {i}. {res['entity']:40s} - {res['num_urls']} URLs, {res['num_papers']} papers")

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print(f"\nOutput files:")
print(f"  1. {SIMILARITY_REPORT}")
print(f"  2. {SUGGESTED_MERGES}")
print(f"  3. {URL_GROUPS}")
