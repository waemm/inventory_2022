#!/usr/bin/env python3
"""Quick script to check abstract availability in the CSV."""

import pandas as pd
import sys

CSV_PATH = '/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv'

df = pd.read_csv(CSV_PATH)

print("="*60)
print("ABSTRACT AVAILABILITY CHECK")
print("="*60)
print(f"\nTotal papers: {len(df)}")
print(f"Papers with non-null abstract: {df['abstract'].notna().sum()}")

# Check for empty strings too
non_empty = df['abstract'].notna() & (df['abstract'].astype(str).str.strip() != '') & (df['abstract'].astype(str) != 'nan')
print(f"Papers with non-empty abstract: {non_empty.sum()}")

# Get sample with abstract
papers_with_text = df[non_empty]
if len(papers_with_text) > 0:
    print("\n" + "="*60)
    print("SAMPLE PAPER WITH ABSTRACT:")
    print("="*60)
    sample = papers_with_text.iloc[0]
    print(f"Title: {sample['title']}")
    print(f"Short: {sample['resource_short_name']}")
    print(f"Full: {sample['resource_full_name']}")
    print(f"\nAbstract snippet:\n{str(sample['abstract'])[:500]}")
else:
    print("\n❌ NO PAPERS WITH ABSTRACTS FOUND!")
