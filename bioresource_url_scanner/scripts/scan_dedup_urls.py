#!/usr/bin/env python3
"""
scan_dedup_urls.py - Scan First 50 URLs from Deduplicated Dataset

Quick script to test scanner on high-confidence linguistic resources.
"""

import pandas as pd
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "pipeline_synthesis_2025-11-18" / "results" / "linguistic_high_conf_dedup_final.csv"
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# Load data
print(f"Loading: {INPUT_FILE.name}")
df = pd.read_csv(INPUT_FILE)

print(f"Total deduplicated resources: {len(df)}")
print(f"With URLs: {df['has_resource_url'].sum()}")

# Get first 50 with URLs
df_with_urls = df[df['has_resource_url'] == True].head(50)
print(f"\nSelected first 50 with URLs: {len(df_with_urls)}")

# Prepare for scanner (rename columns to match expected format)
scanner_input = df_with_urls.copy()
scanner_input = scanner_input.rename(columns={'resource_url': 'url'})

# Extract domain
from urllib.parse import urlparse
scanner_input['domain'] = scanner_input['url'].apply(
    lambda x: urlparse(x).netloc if pd.notna(x) else None
)

# Add metadata
scanner_input['source_file'] = 'linguistic_high_conf_dedup'
scanner_input['sample_priority'] = 'high_conf_dedup'

# Select columns
output_cols = [
    'url', 'pmid', 'primary_entity_long', 'primary_entity_short',
    'domain', 'source_file', 'sample_priority',
    'title', 'db_keyword_found', 'very_high_conf', 'article_count'
]

available_cols = [col for col in output_cols if col in scanner_input.columns]
output_df = scanner_input[available_cols]

# Save
output_path = OUTPUT_DIR / "dedup_urls.csv"
output_df.to_csv(output_path, index=False)

print(f"\n✅ Saved to: {output_path}")
print(f"   Columns: {', '.join(output_df.columns)}")
print(f"\nTop 5 resources by article count:")
top_5 = df_with_urls.nlargest(5, 'article_count')[['primary_entity_long', 'primary_entity_short', 'article_count', 'url']]
for idx, row in top_5.iterrows():
    entity = row['primary_entity_long'] or row['primary_entity_short'] or 'Unknown'
    print(f"  {row['article_count']:2d} articles | {entity:40s} | {row['url'][:50]}...")
