#!/usr/bin/env python3
"""
01_sample_urls.py - Stratified URL Sampling for Bioresource Scanner Pilot

Samples 50-100 URLs from 4 filtered datasets with stratification by:
- Source file (baseline vs novel, linguistic vs SetFit)
- Confidence level (very_high_conf, db_keyword_found, random)
- Domain diversity (max 10 URLs per domain)

Author: Warren
Date: 2025-11-19
"""

import pandas as pd
from pathlib import Path
from urllib.parse import urlparse
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
FILTERED_DATA_DIR = PROJECT_ROOT / "pipeline_synthesis_2025-11-18" / "data" / "filtered"
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# Input files
INPUT_FILES = {
    "baseline_pmid": FILTERED_DATA_DIR / "baseline_by_pmid.csv",
    "baseline_entity": FILTERED_DATA_DIR / "baseline_by_entity_match.csv",
    "linguistic_novel": FILTERED_DATA_DIR / "linguistic_excluding_baseline.csv",
    "setfit_novel": FILTERED_DATA_DIR / "setfit_excluding_baseline.csv",
}

# Sampling configuration
URLS_PER_FILE = 25  # 25 × 4 = 100 total
MAX_URLS_PER_DOMAIN = 10  # Domain diversity
PRIORITY_WEIGHTS = {
    "very_high_conf": 0.40,  # 40% very high confidence
    "db_keyword": 0.30,      # 30% database keywords
    "random": 0.30,          # 30% random
}


def extract_domain(url):
    """Extract domain from URL"""
    if pd.isna(url) or not isinstance(url, str):
        return None
    try:
        return urlparse(url).netloc
    except Exception:
        return None


def sample_from_file(df, file_key, n_samples=25):
    """
    Sample n URLs from dataframe with priority weighting

    Args:
        df: DataFrame with columns: resource_url, very_high_conf, db_keyword_found
        file_key: Source file identifier
        n_samples: Number of URLs to sample

    Returns:
        DataFrame with sampled URLs
    """
    # Filter: must have resource_url
    df = df[df['has_resource_url'] == True].copy()

    if len(df) == 0:
        print(f"  ⚠️  {file_key}: No URLs found!")
        return pd.DataFrame()

    # Add domain
    df['domain'] = df['resource_url'].apply(extract_domain)
    df = df.dropna(subset=['domain'])

    # Calculate sample sizes by priority
    n_very_high = int(n_samples * PRIORITY_WEIGHTS['very_high_conf'])
    n_db_keyword = int(n_samples * PRIORITY_WEIGHTS['db_keyword'])
    n_random = n_samples - n_very_high - n_db_keyword

    samples = []

    # 1. Very high confidence
    very_high = df[df['very_high_conf'] == True]
    if len(very_high) > 0:
        sample = very_high.sample(n=min(n_very_high, len(very_high)), random_state=42)
        sample['sample_priority'] = 'very_high_conf'
        samples.append(sample)

    # 2. Database keyword (excluding already sampled)
    remaining = df[~df.index.isin(pd.concat(samples).index)] if samples else df
    db_kw = remaining[remaining['db_keyword_found'] == True]
    if len(db_kw) > 0:
        sample = db_kw.sample(n=min(n_db_keyword, len(db_kw)), random_state=42)
        sample['sample_priority'] = 'db_keyword'
        samples.append(sample)

    # 3. Random (excluding already sampled)
    remaining = df[~df.index.isin(pd.concat(samples).index)] if samples else df
    if len(remaining) > 0:
        # Fill to target with random
        needed = n_samples - sum(len(s) for s in samples)
        sample = remaining.sample(n=min(needed, len(remaining)), random_state=42)
        sample['sample_priority'] = 'random'
        samples.append(sample)

    # Combine
    result = pd.concat(samples, ignore_index=True)
    result['source_file'] = file_key

    return result


def enforce_domain_diversity(df, max_per_domain=10):
    """
    Ensure no single domain is over-represented

    Args:
        df: Sampled URLs dataframe
        max_per_domain: Maximum URLs per domain

    Returns:
        Filtered dataframe
    """
    # Count URLs per domain
    domain_counts = df['domain'].value_counts()

    # Find over-represented domains
    over_domains = domain_counts[domain_counts > max_per_domain].index

    if len(over_domains) == 0:
        return df

    print(f"\n  ⚠️  Enforcing domain diversity (max {max_per_domain} per domain):")
    for domain in over_domains:
        count = domain_counts[domain]
        print(f"     {domain}: {count} → {max_per_domain} URLs")

    # Downsample over-represented domains
    filtered_dfs = []
    for domain in df['domain'].unique():
        domain_df = df[df['domain'] == domain]
        if domain in over_domains:
            # Keep max_per_domain, prioritizing high confidence
            domain_df = domain_df.sort_values('very_high_conf', ascending=False)
            domain_df = domain_df.head(max_per_domain)
        filtered_dfs.append(domain_df)

    return pd.concat(filtered_dfs, ignore_index=True)


def main():
    """Main sampling workflow"""
    print("=" * 70)
    print("Bioresource URL Scanner - Stratified Sampling")
    print("=" * 70)

    all_samples = []

    # Sample from each file
    for file_key, file_path in INPUT_FILES.items():
        print(f"\n📂 {file_key}:")
        print(f"   Loading: {file_path.name}")

        if not file_path.exists():
            print(f"   ❌ File not found!")
            continue

        # Load data
        df = pd.read_csv(file_path)
        print(f"   Total papers: {len(df):,}")
        print(f"   With URLs: {df['has_resource_url'].sum():,}")

        # Sample
        sample = sample_from_file(df, file_key, URLS_PER_FILE)

        if len(sample) > 0:
            print(f"   ✅ Sampled: {len(sample)} URLs")
            print(f"      - Very high conf: {(sample['sample_priority'] == 'very_high_conf').sum()}")
            print(f"      - DB keyword: {(sample['sample_priority'] == 'db_keyword').sum()}")
            print(f"      - Random: {(sample['sample_priority'] == 'random').sum()}")
            all_samples.append(sample)
        else:
            print(f"   ⚠️  No URLs sampled")

    # Combine all samples
    if not all_samples:
        print("\n❌ No URLs sampled from any file!")
        sys.exit(1)

    combined = pd.concat(all_samples, ignore_index=True)
    print(f"\n📊 Combined Sample:")
    print(f"   Total URLs: {len(combined)}")
    print(f"   Unique domains: {combined['domain'].nunique()}")
    print(f"   By source:")
    for source in combined['source_file'].unique():
        count = (combined['source_file'] == source).sum()
        print(f"      - {source}: {count}")

    # Enforce domain diversity
    combined = enforce_domain_diversity(combined, MAX_URLS_PER_DOMAIN)
    print(f"\n   After diversity filter: {len(combined)} URLs")

    # Domain statistics
    domain_counts = combined['domain'].value_counts()
    print(f"\n   Top 5 domains:")
    for domain, count in domain_counts.head(5).items():
        print(f"      - {domain}: {count} URLs")

    # Select columns for output
    output_cols = [
        'resource_url', 'pmid', 'primary_entity_long', 'primary_entity_short',
        'source_file', 'domain', 'sample_priority',
        'very_high_conf', 'db_keyword_found', 'title_matches_primary'
    ]

    # Handle missing columns gracefully
    available_cols = [col for col in output_cols if col in combined.columns]
    output_df = combined[available_cols].copy()

    # Rename for consistency
    output_df = output_df.rename(columns={'resource_url': 'url'})

    # Save
    output_path = OUTPUT_DIR / "pilot_urls.csv"
    output_df.to_csv(output_path, index=False)

    print(f"\n✅ Saved to: {output_path}")
    print(f"   Columns: {', '.join(output_df.columns)}")
    print(f"   Ready for scanning!")
    print("=" * 70)


if __name__ == "__main__":
    main()
