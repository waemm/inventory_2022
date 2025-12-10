#!/usr/bin/env python3
"""
Script 03c: URL-Based Baseline Matching

Matches inventory URLs against baseline URLs to find additional matches
that weren't caught by PMID or name matching.

Input:
- data/deduplicated/merged_inventory.csv
- review/baseline_matches.csv (to identify NO_MATCH records)
- GBC baseline with URLs: bioresource_papers_with_urls.csv

Output:
- review/baseline_url_matches.csv (new URL-based matches)
- docs/03c_URL_MATCHING_SUMMARY.md

Usage:
    python scripts/03c_url_matching.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import re

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data"
REVIEW_DIR = BASE_DIR / "review"
DOCS_DIR = BASE_DIR / "docs"

# Input files
INVENTORY_FILE = DATA_DIR / "deduplicated/merged_inventory.csv"
BASELINE_MATCHES = REVIEW_DIR / "baseline_matches.csv"
BASELINE_WITH_URLS = Path("/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_with_urls.csv")

# Output files
URL_MATCHES_OUTPUT = REVIEW_DIR / "baseline_url_matches.csv"
SUMMARY_FILE = DOCS_DIR / "03c_URL_MATCHING_SUMMARY.md"


def normalize_url(url: str) -> str:
    """
    Normalize URL for matching:
    - Remove protocol (http/https)
    - Remove www prefix
    - Remove trailing slashes
    - Lowercase everything
    - Remove common tracking parameters
    """
    if pd.isna(url) or not url:
        return ""

    url = str(url).strip().lower()

    # Remove protocol
    url = re.sub(r'^https?://', '', url)

    # Remove www prefix
    url = re.sub(r'^www\.', '', url)

    # Remove trailing slashes
    url = url.rstrip('/')

    # Remove common tracking/session parameters
    url = re.sub(r'\?.*$', '', url)  # Remove query string entirely for base matching

    return url


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    normalized = normalize_url(url)
    if not normalized:
        return ""

    # Get just the domain part
    parts = normalized.split('/')
    return parts[0] if parts else ""


def extract_domain_and_path(url: str) -> str:
    """Extract domain and path (without query params)."""
    return normalize_url(url)


def load_baseline_urls(baseline_path: Path) -> pd.DataFrame:
    """Load baseline and create URL lookup structures."""
    print(f"Loading baseline with URLs: {baseline_path}")
    df = pd.read_csv(baseline_path)
    print(f"  Loaded {len(df):,} records")

    # Normalize URLs
    df['normalized_url'] = df['resource_url'].apply(normalize_url)
    df['domain'] = df['resource_url'].apply(extract_domain)

    # Also process wayback URLs
    df['normalized_wayback'] = df['resource_wayback_url'].apply(normalize_url)

    # Count unique URLs
    unique_urls = df['normalized_url'].dropna().nunique()
    unique_domains = df['domain'].dropna().nunique()
    print(f"  Unique normalized URLs: {unique_urls:,}")
    print(f"  Unique domains: {unique_domains:,}")

    return df


def find_url_matches(inventory_df: pd.DataFrame, baseline_df: pd.DataFrame,
                     no_match_ids: set) -> pd.DataFrame:
    """
    Find URL-based matches between inventory and baseline.

    Returns DataFrame with match results.
    """
    results = []

    # Build lookup dictionaries from baseline
    url_to_baseline = {}  # normalized_url -> list of baseline records
    domain_to_baseline = {}  # domain -> list of baseline records

    for _, row in baseline_df.iterrows():
        norm_url = row['normalized_url']
        domain = row['domain']

        if norm_url:
            if norm_url not in url_to_baseline:
                url_to_baseline[norm_url] = []
            url_to_baseline[norm_url].append(row)

        if domain:
            if domain not in domain_to_baseline:
                domain_to_baseline[domain] = []
            domain_to_baseline[domain].append(row)

    print(f"\nBuilt lookup: {len(url_to_baseline):,} unique URLs, {len(domain_to_baseline):,} unique domains")

    # Process inventory records that had NO_MATCH
    no_match_records = inventory_df[inventory_df.index.isin(no_match_ids) |
                                     inventory_df['best_name'].isin(no_match_ids)]

    # Actually filter by the row indices from baseline_matches
    inventory_df_indexed = inventory_df.reset_index(drop=True)

    exact_matches = 0
    domain_matches = 0

    for idx, row in inventory_df_indexed.iterrows():
        if idx not in no_match_ids:
            continue

        inv_url = row.get('extracted_url', '')
        norm_inv_url = normalize_url(inv_url)
        inv_domain = extract_domain(inv_url)

        if not norm_inv_url:
            continue

        match_type = None
        matched_baseline = None
        confidence = 0.0

        # Try exact URL match first
        if norm_inv_url in url_to_baseline:
            match_type = "URL_EXACT"
            matched_baseline = url_to_baseline[norm_inv_url][0]
            confidence = 0.95
            exact_matches += 1

        # Try domain + path match (already normalized, so same as exact)
        # Skip if already matched

        # Try domain-only match
        elif inv_domain in domain_to_baseline:
            # Only flag as review if there are multiple resources on this domain
            baseline_on_domain = domain_to_baseline[inv_domain]
            if len(baseline_on_domain) == 1:
                # Single resource on domain - likely a match
                match_type = "URL_DOMAIN_SINGLE"
                matched_baseline = baseline_on_domain[0]
                confidence = 0.75
                domain_matches += 1
            else:
                # Multiple resources on domain - needs review
                match_type = "URL_DOMAIN_MULTI"
                matched_baseline = baseline_on_domain[0]  # Just take first for reference
                confidence = 0.50
                domain_matches += 1

        if match_type and matched_baseline is not None:
            results.append({
                'inventory_idx': idx,
                'best_name': row.get('best_name', ''),
                'extracted_url': inv_url,
                'normalized_url': norm_inv_url,
                'match_type': match_type,
                'confidence': confidence,
                'baseline_resource_id': matched_baseline.get('resource_id', ''),
                'baseline_resource_name': matched_baseline.get('resource_short_name', ''),
                'baseline_resource_full': matched_baseline.get('resource_full_name', ''),
                'baseline_url': matched_baseline.get('resource_url', ''),
                'baseline_normalized_url': matched_baseline.get('normalized_url', ''),
                'is_gcbr': matched_baseline.get('is_global_core_biodata_resource', ''),
                'source_batch': row.get('source_batch', ''),
                'paper_titles': row.get('paper_titles', ''),
            })

    print(f"\nURL Matches found:")
    print(f"  Exact URL matches: {exact_matches}")
    print(f"  Domain-based matches: {domain_matches}")

    return pd.DataFrame(results)


def generate_summary(results_df: pd.DataFrame, total_no_match: int) -> str:
    """Generate markdown summary."""

    match_counts = results_df['match_type'].value_counts().to_dict() if len(results_df) > 0 else {}

    summary = f"""# Step 3c: URL-Based Baseline Matching Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

Attempted to match inventory URLs against baseline URLs for records that had no PMID or name match.

---

## Results

| Metric | Value |
|--------|-------|
| NO_MATCH records checked | {total_no_match:,} |
| URL matches found | {len(results_df):,} |
| Match rate | {len(results_df)/total_no_match*100:.1f}% |

---

## Match Type Breakdown

| Match Type | Count | Confidence | Description |
|------------|-------|------------|-------------|
| URL_EXACT | {match_counts.get('URL_EXACT', 0):,} | 0.95 | Normalized URLs match exactly |
| URL_DOMAIN_SINGLE | {match_counts.get('URL_DOMAIN_SINGLE', 0):,} | 0.75 | Same domain, only one baseline resource |
| URL_DOMAIN_MULTI | {match_counts.get('URL_DOMAIN_MULTI', 0):,} | 0.50 | Same domain, multiple baseline resources (needs review) |

---

## Recommendations

- **URL_EXACT matches**: High confidence, can be accepted
- **URL_DOMAIN_SINGLE matches**: Good confidence, review recommended
- **URL_DOMAIN_MULTI matches**: Lower confidence, manual review required

---

## Output Files

- `review/baseline_url_matches.csv` ({len(results_df):,} records)

---

## Integration

These URL matches can be combined with the existing baseline matches to improve coverage.
Records in this file were previously marked as NO_MATCH but now have URL-based matches.
"""

    return summary


def main():
    print("=" * 60)
    print("Step 3c: URL-Based Baseline Matching")
    print("=" * 60)

    # Check inputs
    if not INVENTORY_FILE.exists():
        print(f"ERROR: Inventory not found: {INVENTORY_FILE}")
        return

    if not BASELINE_MATCHES.exists():
        print(f"ERROR: Baseline matches not found: {BASELINE_MATCHES}")
        return

    if not BASELINE_WITH_URLS.exists():
        print(f"ERROR: Baseline with URLs not found: {BASELINE_WITH_URLS}")
        return

    # Load data
    print(f"\nLoading inventory: {INVENTORY_FILE}")
    inventory_df = pd.read_csv(INVENTORY_FILE)
    print(f"  Loaded {len(inventory_df):,} records")

    print(f"\nLoading baseline matches: {BASELINE_MATCHES}")
    baseline_matches_df = pd.read_csv(BASELINE_MATCHES)
    print(f"  Loaded {len(baseline_matches_df):,} records")

    # Get NO_MATCH record indices
    no_match_df = baseline_matches_df[baseline_matches_df['match_type'] == 'NO_MATCH']
    no_match_ids = set(no_match_df.index.tolist())
    print(f"  NO_MATCH records: {len(no_match_ids):,}")

    # Load baseline with URLs
    baseline_df = load_baseline_urls(BASELINE_WITH_URLS)

    # Find URL matches
    print("\nFinding URL-based matches...")
    results_df = find_url_matches(inventory_df, baseline_df, no_match_ids)

    # Save results
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(URL_MATCHES_OUTPUT, index=False)
    print(f"\nSaved: {URL_MATCHES_OUTPUT} ({len(results_df):,} records)")

    # Generate summary
    summary = generate_summary(results_df, len(no_match_ids))
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(summary)
    print(f"Saved: {SUMMARY_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("URL MATCHING COMPLETE")
    print("=" * 60)
    print(f"\nNO_MATCH records checked: {len(no_match_ids):,}")
    print(f"URL matches found: {len(results_df):,}")
    if len(no_match_ids) > 0:
        print(f"Match rate: {len(results_df)/len(no_match_ids)*100:.1f}%")

    if len(results_df) > 0:
        print("\nMatch type breakdown:")
        for match_type, count in results_df['match_type'].value_counts().items():
            print(f"  {match_type}: {count}")

    print(f"\nResults saved to: {URL_MATCHES_OUTPUT}")


if __name__ == "__main__":
    main()
