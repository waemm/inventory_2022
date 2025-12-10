#!/usr/bin/env python3
"""
Script 02: Identify Duplicates (v2 - Stricter Matching)

Combines filtered batches and identifies potential duplicates using strict
URL matching and entity name similarity. Generates a review file for user
verification before applying merges.

MATCHING CRITERIA:
- MERGE (high confidence): Exact URL match + similar name (≥85%)
- LIKELY_MERGE: Same URL path + similar name (≥70%)
- REVIEW: Same domain + similar path (≥80%) + high name similarity (≥85%)
- Multi-resource domains (NCBI, EBI, etc.) require exact path OR ≥95% name match

Input:
- data/filtered/batch_2010_2022_live.csv
- data/filtered/batch_2022_2025_live.csv

Output:
- data/combined/combined_batches.csv (merged but not deduped)
- review/proposed_merges.csv (for user review)
- docs/02_DUPLICATE_SUMMARY.md

Usage:
    python scripts/02_identify_duplicates.py
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from difflib import SequenceMatcher
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data"
REVIEW_DIR = BASE_DIR / "review"
DOCS_DIR = BASE_DIR / "docs"

# Input files
INPUT_2010_2022 = DATA_DIR / "filtered/batch_2010_2022_live.csv"
INPUT_2022_2025 = DATA_DIR / "filtered/batch_2022_2025_live.csv"

# Output files
COMBINED_OUTPUT = DATA_DIR / "combined/combined_batches.csv"
PROPOSED_MERGES = REVIEW_DIR / "proposed_merges.csv"
SUMMARY_FILE = DOCS_DIR / "02_DUPLICATE_SUMMARY.md"

# ============================================================================
# MULTI-RESOURCE DOMAINS - These host many different databases
# Require EXACT path match or very high name similarity (≥95%)
# ============================================================================

MULTI_RESOURCE_DOMAINS = [
    # Major bioinformatics hubs
    'ncbi.nlm.nih.gov',
    'ebi.ac.uk',
    'genome.ucsc.edu',
    'ensembl.org',
    'uniprot.org',

    # Data repositories
    'proteomexchange.org',
    'big.ac.cn',
    'bigd.big.ac.cn',
    'ngdc.cncb.ac.cn',

    # Package repositories
    'bioconductor.org',
    'cran.r-project.org',
    'pypi.org',

    # Code hosting
    'github.com',
    'github.io',
    'gitlab.com',
    'bitbucket.org',
    'sourceforge.net',

    # Cloud platforms
    'shinyapps.io',
    'herokuapp.com',
    'netlify.app',
    'vercel.app',

    # Academic institutions (generic)
    'nih.gov',
    'edu',
    'ac.uk',
    'ac.jp',
    'edu.cn',
]


def is_multi_resource_domain(domain):
    """Check if domain hosts multiple independent resources."""
    if not domain:
        return False
    domain = domain.lower()
    for mrd in MULTI_RESOURCE_DOMAINS:
        if domain == mrd or domain.endswith('.' + mrd):
            return True
    return False


# ============================================================================
# URL PARSING AND NORMALIZATION
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

    protocol = parsed.scheme
    full_domain = parsed.netloc.lower()
    path = parsed.path.rstrip('/').lower()

    # Remove www prefix from domain
    if full_domain.startswith('www.'):
        full_domain = full_domain[4:]

    return {
        'protocol': protocol,
        'domain': full_domain,
        'path': path,
        'full_url': f"{full_domain}{path}",
        'original_url': url
    }


def normalize_url_strict(url):
    """Strictly normalize URL for exact matching."""
    if pd.isna(url) or url == '':
        return ''

    url = str(url).strip().lower()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^ftp://', '', url)

    if url.startswith('www.'):
        url = url[4:]

    url = url.rstrip('/')
    url = re.sub(r'/index\.(html?|php|asp)$', '', url)
    url = re.sub(r':80($|/)', r'\1', url)

    return url


def urls_match_exactly(url1, url2):
    """Check if two URLs are identical after strict normalization."""
    n1 = normalize_url_strict(url1)
    n2 = normalize_url_strict(url2)

    if not n1 or not n2:
        return False

    return n1 == n2


def compute_path_similarity(path1, path2):
    """Compute similarity between two URL paths."""
    if not path1 and not path2:
        return 1.0
    if not path1 or not path2:
        return 0.0
    return SequenceMatcher(None, path1, path2).ratio()


# ============================================================================
# ENTITY NORMALIZATION
# ============================================================================

def normalize_entity(name):
    """Normalize entity name for matching."""
    if pd.isna(name) or name == '':
        return ''

    name = str(name).lower().strip()
    name = re.sub(r'[_\-\.]', ' ', name)
    name = ' '.join(name.split())

    return name


def compute_entity_similarity(name1, name2):
    """Compute similarity between two entity names."""
    n1 = normalize_entity(name1)
    n2 = normalize_entity(name2)

    if not n1 or not n2:
        return 0.0

    if n1 == n2:
        return 1.0

    return SequenceMatcher(None, n1, n2).ratio()


# ============================================================================
# DUPLICATE DETECTION (STRICT VERSION)
# ============================================================================

def find_duplicates_strict(df):
    """
    Find potential duplicate records using STRICT matching criteria.

    Matching levels:
    - MERGE: Exact URL + name similarity ≥85%
    - LIKELY_MERGE: Same domain+path + name similarity ≥70%
    - REVIEW: Same domain, similar path ≥80%, name similarity ≥85%

    Multi-resource domains require exact path OR name similarity ≥95%
    """
    print("\n  Building URL index...")

    # Index by normalized URL for exact matching
    url_to_indices = defaultdict(list)
    domain_to_indices = defaultdict(list)

    for idx, row in df.iterrows():
        url = row.get('extracted_url', '')
        components = parse_url_components(url)

        if components:
            normalized = normalize_url_strict(url)
            url_to_indices[normalized].append(idx)
            domain_to_indices[components['domain']].append(idx)

    print(f"    {len(url_to_indices):,} unique normalized URLs")
    print(f"    {len(domain_to_indices):,} unique domains")

    # Find duplicates
    merge_candidates = []
    processed_pairs = set()

    # Phase 1: Exact URL matches (highest confidence)
    print("\n  Phase 1: Finding exact URL matches...")
    exact_match_groups = 0

    for normalized_url, indices in url_to_indices.items():
        if len(indices) > 1:
            # Multiple records with exact same URL
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx_i, idx_j = indices[i], indices[j]
                    pair_key = (min(idx_i, idx_j), max(idx_i, idx_j))

                    if pair_key in processed_pairs:
                        continue
                    processed_pairs.add(pair_key)

                    name1 = df.loc[idx_i, 'best_name']
                    name2 = df.loc[idx_j, 'best_name']
                    name_sim = compute_entity_similarity(name1, name2)

                    # Exact URL match - high confidence if names also similar
                    if name_sim >= 0.85:
                        recommendation = 'MERGE'
                    elif name_sim >= 0.5:
                        recommendation = 'LIKELY_MERGE'
                    else:
                        recommendation = 'REVIEW'

                    merge_candidates.append({
                        'idx1': idx_i,
                        'idx2': idx_j,
                        'url_match_type': 'EXACT',
                        'url_similarity': 1.0,
                        'name_similarity': name_sim,
                        'recommendation': recommendation
                    })
            exact_match_groups += 1

    print(f"    Found {exact_match_groups} exact URL match groups")

    # Phase 2: Same domain matching (only for non-multi-resource domains)
    print("\n  Phase 2: Finding same-domain matches (excluding multi-resource domains)...")
    domain_match_count = 0

    for domain, indices in domain_to_indices.items():
        if len(indices) <= 1:
            continue

        is_multi = is_multi_resource_domain(domain)

        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                idx_i, idx_j = indices[i], indices[j]
                pair_key = (min(idx_i, idx_j), max(idx_i, idx_j))

                if pair_key in processed_pairs:
                    continue

                url1 = df.loc[idx_i, 'extracted_url']
                url2 = df.loc[idx_j, 'extracted_url']
                name1 = df.loc[idx_i, 'best_name']
                name2 = df.loc[idx_j, 'best_name']

                comp1 = parse_url_components(url1)
                comp2 = parse_url_components(url2)

                if not comp1 or not comp2:
                    continue

                path_sim = compute_path_similarity(comp1['path'], comp2['path'])
                name_sim = compute_entity_similarity(name1, name2)

                # For multi-resource domains: require exact path OR very high name similarity
                if is_multi:
                    if path_sim < 1.0 and name_sim < 0.95:
                        # Different paths on multi-resource domain with different names
                        # These are likely different resources - skip
                        continue

                # Determine if this is a valid duplicate candidate
                recommendation = None

                if path_sim == 1.0 and name_sim >= 0.70:
                    # Same path + reasonable name match
                    recommendation = 'LIKELY_MERGE'
                elif path_sim >= 0.8 and name_sim >= 0.85:
                    # Similar path + high name match
                    recommendation = 'REVIEW'
                elif name_sim >= 0.95:
                    # Very high name similarity (even with different paths)
                    recommendation = 'REVIEW'

                if recommendation:
                    processed_pairs.add(pair_key)
                    merge_candidates.append({
                        'idx1': idx_i,
                        'idx2': idx_j,
                        'url_match_type': 'DOMAIN',
                        'url_similarity': path_sim,
                        'name_similarity': name_sim,
                        'recommendation': recommendation
                    })
                    domain_match_count += 1

    print(f"    Found {domain_match_count} domain-level match candidates")

    # Build clusters using union-find
    print("\n  Building duplicate clusters...")
    parent = {idx: idx for idx in df.index}

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

    # Union pairs
    for candidate in merge_candidates:
        union(candidate['idx1'], candidate['idx2'])

    # Build clusters
    clusters = defaultdict(list)
    for idx in df.index:
        root = find(idx)
        if root != idx or any(c['idx1'] == idx or c['idx2'] == idx for c in merge_candidates):
            clusters[root].append(idx)

    # Filter to multi-member clusters
    duplicate_clusters = {k: v for k, v in clusters.items() if len(v) > 1}
    print(f"    {len(duplicate_clusters)} duplicate clusters identified")

    # Build output records
    merge_records = []
    pair_info = {}

    # Index pair info for lookup
    for candidate in merge_candidates:
        key = (min(candidate['idx1'], candidate['idx2']), max(candidate['idx1'], candidate['idx2']))
        pair_info[key] = candidate

    for group_id, (root, members) in enumerate(duplicate_clusters.items()):
        # Get best recommendation for this group
        group_recommendations = []
        group_url_sims = []
        group_name_sims = []

        for i, idx_i in enumerate(members):
            for idx_j in members[i+1:]:
                key = (min(idx_i, idx_j), max(idx_i, idx_j))
                if key in pair_info:
                    info = pair_info[key]
                    group_recommendations.append(info['recommendation'])
                    group_url_sims.append(info['url_similarity'])
                    group_name_sims.append(info['name_similarity'])

        # Best recommendation for group
        if 'MERGE' in group_recommendations:
            group_rec = 'MERGE'
        elif 'LIKELY_MERGE' in group_recommendations:
            group_rec = 'LIKELY_MERGE'
        else:
            group_rec = 'REVIEW'

        avg_url_sim = sum(group_url_sims) / len(group_url_sims) if group_url_sims else 0
        avg_name_sim = sum(group_name_sims) / len(group_name_sims) if group_name_sims else 0

        for idx in members:
            row = df.loc[idx]
            # Get paper titles - truncate if too long
            paper_titles = str(row.get('paper_titles', ''))
            if len(paper_titles) > 200:
                paper_titles = paper_titles[:200] + '...'

            merge_records.append({
                'merge_group_id': group_id,
                'row_id': idx,
                'best_name': row.get('best_name', ''),
                'extracted_url': row.get('extracted_url', ''),
                'paper_titles': paper_titles,
                'ID': row.get('ID', ''),
                'source_batch': row.get('source_batch', ''),
                'url_similarity': round(avg_url_sim, 3),
                'name_similarity': round(avg_name_sim, 3),
                'recommendation': group_rec,
                'user_decision': ''
            })

    return pd.DataFrame(merge_records), len(duplicate_clusters)


def generate_summary(stats: dict) -> str:
    """Generate markdown summary of duplicate detection."""

    summary = f"""# Step 2: Duplicate Detection Summary (Strict Matching v2)

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

Combined filtered batches and identified potential duplicates using **strict** matching:
- Exact URL match required for high-confidence merges
- Multi-resource domains (NCBI, EBI, etc.) require exact path OR ≥95% name similarity
- Name similarity thresholds applied at each level

---

## Input Summary

| Batch | Records |
|-------|---------|
| 2010-2022 | {stats['batch_2010_2022']:,} |
| 2022-2025 | {stats['batch_2022_2025']:,} |
| **Combined** | **{stats['combined_total']:,}** |

---

## Duplicate Detection Results

| Metric | Value |
|--------|-------|
| Total records | {stats['combined_total']:,} |
| Unique (no duplicates) | {stats['unique_count']:,} |
| Duplicate clusters | {stats['cluster_count']:,} |
| Records in clusters | {stats['records_in_clusters']:,} |
| Potential reduction | {stats['potential_reduction']:,} (~{stats['reduction_pct']:.1f}%) |

---

## Recommendation Breakdown

| Recommendation | Count | Description |
|----------------|-------|-------------|
| MERGE | {stats.get('merge_count', 0):,} | Exact URL + similar name (≥85%) |
| LIKELY_MERGE | {stats.get('likely_merge_count', 0):,} | Same path + name match (≥70%) |
| REVIEW | {stats.get('review_count', 0):,} | Needs manual verification |

---

## Multi-Resource Domain Handling

The following domains host multiple independent databases and require stricter matching:
- NCBI (ncbi.nlm.nih.gov)
- EBI (ebi.ac.uk)
- UCSC Genome Browser (genome.ucsc.edu)
- Bioconductor (bioconductor.org)
- GitHub (github.com, github.io)
- And others...

For these domains, records are only grouped if:
1. Exact same URL path, OR
2. Name similarity ≥95%

---

## Output Files

- `data/combined/combined_batches.csv` ({stats['combined_total']:,} records)
- `review/proposed_merges.csv` ({stats['records_in_clusters']:,} records for review)

---

## Next Steps

1. **Review the proposed merges:**
   ```
   review/proposed_merges.csv
   ```

2. **Edit the `user_decision` column:**
   - `MERGE` - Confirm merge (keep first record, merge metadata)
   - `KEEP_SEPARATE` - Do not merge these records
   - Leave blank to accept recommendation

3. **When ready, apply merges:**
   ```bash
   python scripts/02b_apply_merges.py
   ```
"""

    return summary


def main():
    print("=" * 60)
    print("Step 2: Identify Duplicates (Strict Matching v2)")
    print("=" * 60)

    # Load filtered batches
    print(f"\nLoading 2010-2022 batch from: {INPUT_2010_2022}")
    df_2010_2022 = pd.read_csv(INPUT_2010_2022)
    print(f"  Loaded {len(df_2010_2022):,} records")

    print(f"\nLoading 2022-2025 batch from: {INPUT_2022_2025}")
    df_2022_2025 = pd.read_csv(INPUT_2022_2025)
    print(f"  Loaded {len(df_2022_2025):,} records")

    # Combine batches
    print("\nCombining batches...")
    combined = pd.concat([df_2010_2022, df_2022_2025], ignore_index=True)
    print(f"  Combined total: {len(combined):,} records")

    # Save combined file
    COMBINED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(COMBINED_OUTPUT, index=False)
    print(f"  Saved: {COMBINED_OUTPUT}")

    # Find duplicates with strict matching
    print("\nIdentifying duplicates (strict matching)...")
    proposed_merges, cluster_count = find_duplicates_strict(combined)

    # Calculate statistics
    records_in_clusters = len(proposed_merges)
    unique_count = len(combined) - records_in_clusters + cluster_count
    potential_reduction = records_in_clusters - cluster_count

    stats = {
        'batch_2010_2022': len(df_2010_2022),
        'batch_2022_2025': len(df_2022_2025),
        'combined_total': len(combined),
        'unique_count': unique_count,
        'cluster_count': cluster_count,
        'records_in_clusters': records_in_clusters,
        'potential_reduction': potential_reduction,
        'reduction_pct': (potential_reduction / len(combined) * 100) if len(combined) > 0 else 0,
        'merge_count': len(proposed_merges[proposed_merges['recommendation'] == 'MERGE']) if len(proposed_merges) > 0 else 0,
        'likely_merge_count': len(proposed_merges[proposed_merges['recommendation'] == 'LIKELY_MERGE']) if len(proposed_merges) > 0 else 0,
        'review_count': len(proposed_merges[proposed_merges['recommendation'] == 'REVIEW']) if len(proposed_merges) > 0 else 0,
    }

    # Save proposed merges for review
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    proposed_merges.to_csv(PROPOSED_MERGES, index=False)
    print(f"\n  Saved proposed merges: {PROPOSED_MERGES}")

    # Generate summary
    summary = generate_summary(stats)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(summary)
    print(f"  Saved summary: {SUMMARY_FILE}")

    # Print summary to console
    print("\n" + "=" * 60)
    print("DUPLICATE DETECTION COMPLETE (Strict Matching)")
    print("=" * 60)
    print(f"\nCombined: {stats['combined_total']:,} records")
    print(f"Duplicate clusters: {stats['cluster_count']:,}")
    print(f"Records needing review: {stats['records_in_clusters']:,}")
    print(f"Potential reduction: {stats['potential_reduction']:,} ({stats['reduction_pct']:.1f}%)")
    print(f"\nBreakdown:")
    print(f"  MERGE (high confidence): {stats['merge_count']:,}")
    print(f"  LIKELY_MERGE: {stats['likely_merge_count']:,}")
    print(f"  REVIEW: {stats['review_count']:,}")
    print(f"\nReview the proposed merges at: {PROPOSED_MERGES}")
    print("\nWhen ready, proceed to Step 2b:")
    print("  python scripts/02b_apply_merges.py")


if __name__ == "__main__":
    main()
