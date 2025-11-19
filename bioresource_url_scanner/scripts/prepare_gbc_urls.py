#!/usr/bin/env python3
"""
prepare_gbc_urls.py - Extract URLs from GBC publication analysis dataset

Reads: ../gbc-publication-analysis/bioresource_papers_with_urls.csv
Writes: data/gbc_urls.csv (ready for scanning)
"""

import pandas as pd
from urllib.parse import urlparse

# Read GBC publication analysis data
input_path = "/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_with_urls.csv"
df = pd.read_csv(input_path)

print(f"Loaded {len(df)} records from GBC publication analysis")

# Extract required columns
url_data = df[['url', 'pubmed_id', 'resource_full_name', 'resource_short_name',
               'is_global_core_biodata_resource', 'publication_id', 'title']].copy()

# Add domain column
url_data['domain'] = url_data['url'].apply(lambda x: urlparse(x).netloc if pd.notna(x) else '')

# Mark source
url_data['source_file'] = 'gbc_publication_analysis'

# Rename columns to match scanner expectations
url_data = url_data.rename(columns={
    'pubmed_id': 'pmid',
    'resource_full_name': 'primary_entity_long',
    'resource_short_name': 'primary_entity_short',
    'is_global_core_biodata_resource': 'is_gcbr'
})

# Remove any rows with missing URLs
url_data = url_data[url_data['url'].notna()].copy()

print(f"\n📊 Dataset Statistics:")
print(f"   Total URLs: {len(url_data)}")
print(f"   Unique domains: {url_data['domain'].nunique()}")
print(f"   GCBR resources: {url_data['is_gcbr'].sum() if 'is_gcbr' in url_data.columns else 'N/A'}")

# Domain distribution
print(f"\n🌐 Top 10 domains:")
top_domains = url_data['domain'].value_counts().head(10)
for domain, count in top_domains.items():
    print(f"   {domain:40s}: {count:3d} URLs")

# Save
output_path = "data/gbc_urls.csv"
url_data.to_csv(output_path, index=False)

print(f"\n✅ Saved {len(url_data)} URLs to: {output_path}")
print(f"\n🚀 Ready for scanning!")
print(f"   Test mode: python scripts/scan_gbc_test.py")
print(f"   Full scan: python scripts/scan_gbc_full.py")
