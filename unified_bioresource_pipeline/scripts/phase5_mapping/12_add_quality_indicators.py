#!/usr/bin/env python3
"""
Add quality indicators to union papers with primary resources.

This script enriches the dataset with quality indicators based on title analysis:
- entity_from_title: Extract resource name from title (text before colon)
- db_keyword_found: Database-related keywords in title
- title_entity_in_ner: Whether title entity matches NER-detected primary entity
- very_high_conf: Both db_keyword AND title_entity match (highest quality)

Input: union_papers_with_primary_resources.csv (16,605 papers)
Output: union_papers_with_quality_indicators.csv (same papers + quality columns)
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parents[3]  # Advanced_filtering_pipeline parent
DATA_DIR = BASE_DIR / 'advanced_filtering_pipeline/data'
DATA_DIR.mkdir(exist_ok=True)

# Input/Output files
INPUT_FILE = DATA_DIR / 'union_papers_with_primary_resources.csv'
OUTPUT_FILE = DATA_DIR / 'union_papers_with_quality_indicators.csv'
STATS_FILE = DATA_DIR / 'quality_indicators_statistics.txt'

print("="*80)
print("Adding Quality Indicators to Union Papers")
print("="*80)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize_text(text):
    """Normalize text for matching"""
    if pd.isna(text):
        return ''
    return str(text).lower().strip()

def extract_entity_from_title(title):
    """Extract potential resource name from title (text before first colon)"""
    if pd.isna(title):
        return ''

    # Find first colon
    if ':' not in title:
        return ''

    # Extract text before first colon
    entity = title.split(':')[0].strip()

    # Strip common articles
    for article in ['The ', 'A ', 'An ']:
        if entity.startswith(article):
            entity = entity[len(article):].strip()

    # Remove version numbers
    # Pattern: v2.0, version 2.0, 2025, etc.
    entity = re.sub(r'\bv?\d+\.?\d*\b', '', entity, flags=re.IGNORECASE)
    entity = re.sub(r'\bversion\s+\d+\.?\d*\b', '', entity, flags=re.IGNORECASE)

    # Handle parenthetical acronyms: "Name (ACRONYM)" -> "Name"
    entity = re.sub(r'\s*\([^)]+\)\s*$', '', entity)

    # Clean up extra whitespace
    entity = ' '.join(entity.split()).strip()

    return entity

def detect_db_keywords(title):
    """Detect database-related keywords in title"""
    if pd.isna(title):
        return False

    title_lower = title.lower()
    keywords = [
        'database', 'db',
        'server',
        'portal',
        'resource',
        'repository',
        'archive',
        'registry',
        'catalog',
        'collection'
    ]

    return any(keyword in title_lower for keyword in keywords)

def calculate_db_keyword_score(title):
    """Calculate strength of database indicators in title"""
    if pd.isna(title):
        return 0

    title_lower = title.lower()
    score = 0

    # High-value keywords (5 points each)
    high_keywords = ['database', 'server', 'portal', 'repository']
    for kw in high_keywords:
        if kw in title_lower:
            score += 5

    # Medium-value keywords (3 points each)
    med_keywords = ['resource', 'archive', 'registry', 'catalog']
    for kw in med_keywords:
        if kw in title_lower:
            score += 3

    # Low-value keywords (1 point each)
    low_keywords = ['collection', 'db']
    for kw in low_keywords:
        if kw in title_lower:
            score += 1

    return score

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n1. Loading union dataset...")
df = pd.read_csv(INPUT_FILE)
print(f"   Loaded: {len(df)} papers")
print(f"   Columns: {list(df.columns)}")

# ============================================================================
# TITLE PROCESSING - ADD QUALITY INDICATORS
# ============================================================================

print("\n2. Adding quality indicators...")

# Extract entity from title
df['entity_from_title'] = df['title'].apply(extract_entity_from_title)
entities_found = (df['entity_from_title'] != '').sum()
print(f"   ✓ Extracted entities from {entities_found:,} titles ({entities_found/len(df)*100:.1f}%)")

# Detect database keywords
df['db_keyword_found'] = df['title'].apply(detect_db_keywords)
db_keywords = df['db_keyword_found'].sum()
print(f"   ✓ Found DB keywords in {db_keywords:,} titles ({db_keywords/len(df)*100:.1f}%)")

# Calculate keyword score
df['db_keyword_score'] = df['title'].apply(calculate_db_keyword_score)
scored_titles = (df['db_keyword_score'] > 0).sum()
print(f"   ✓ Calculated keyword scores for {scored_titles:,} titles (mean: {df['db_keyword_score'].mean():.2f})")

# Check if title entity matches primary
def title_matches_primary(row):
    """Check if extracted title entity matches primary entity"""
    title_entity = normalize_text(row['entity_from_title'])
    primary_long = normalize_text(row['primary_entity_long'])
    primary_short = normalize_text(row['primary_entity_short'])

    if not title_entity:
        return False

    return title_entity == primary_long or title_entity == primary_short

df['title_entity_in_ner'] = df.apply(title_matches_primary, axis=1)
matches = df['title_entity_in_ner'].sum()
print(f"   ✓ Title matches primary in {matches:,} papers ({matches/len(df)*100:.1f}%)")

# Calculate very high confidence indicator
df['very_high_conf'] = (
    df['db_keyword_found'] & df['title_entity_in_ner']
)
high_conf = df['very_high_conf'].sum()
print(f"   ✓ Very high confidence: {high_conf:,} papers ({high_conf/len(df)*100:.1f}%)")

# ============================================================================
# SAVE OUTPUT
# ============================================================================

print("\n3. Saving enriched dataset...")
df.to_csv(OUTPUT_FILE, index=False)
print(f"   ✓ Saved to: {OUTPUT_FILE}")
print(f"   ✓ Shape: {df.shape}")

# ============================================================================
# GENERATE STATISTICS
# ============================================================================

print("\n4. Generating statistics...")

# Overall stats
stats = {
    'total': len(df),
    'entity_from_title': (df['entity_from_title'] != '').sum(),
    'db_keyword_found': df['db_keyword_found'].sum(),
    'title_entity_in_ner': df['title_entity_in_ner'].sum(),
    'very_high_conf': df['very_high_conf'].sum(),
    'status_ok': (df['status'] == 'ok').sum(),
    'status_conflict': (df['status'] == 'conflict').sum(),
    'status_low_score': (df['status'] == 'low_score').sum(),
    'status_no_entities': (df['status'] == 'no_entities').sum(),
}

# Calculate percentages
for key in ['entity_from_title', 'db_keyword_found', 'title_entity_in_ner', 'very_high_conf', 'status_ok']:
    stats[f'{key}_pct'] = (stats[key] / stats['total']) * 100 if stats['total'] > 0 else 0

# Breakdown by source (linguistic vs setfit)
ling_stats = {
    'total': df['in_linguistic'].sum(),
    'very_high_conf': df[df['in_linguistic']]['very_high_conf'].sum(),
}
setfit_stats = {
    'total': df['in_setfit'].sum(),
    'very_high_conf': df[df['in_setfit']]['very_high_conf'].sum(),
}

ling_stats['very_high_conf_pct'] = (ling_stats['very_high_conf'] / ling_stats['total']) * 100 if ling_stats['total'] > 0 else 0
setfit_stats['very_high_conf_pct'] = (setfit_stats['very_high_conf'] / setfit_stats['total']) * 100 if setfit_stats['total'] > 0 else 0

# Write statistics report
with open(STATS_FILE, 'w') as f:
    f.write("="*80 + "\n")
    f.write("QUALITY INDICATORS STATISTICS\n")
    f.write("="*80 + "\n\n")

    f.write(f"Total papers: {stats['total']:,}\n\n")

    f.write("Quality Indicators:\n")
    f.write(f"  Entity from title:      {stats['entity_from_title']:>6,} ({stats['entity_from_title_pct']:>5.1f}%)\n")
    f.write(f"  DB keyword found:       {stats['db_keyword_found']:>6,} ({stats['db_keyword_found_pct']:>5.1f}%)\n")
    f.write(f"  Title matches primary:  {stats['title_entity_in_ner']:>6,} ({stats['title_entity_in_ner_pct']:>5.1f}%)\n")
    f.write(f"  Very high confidence:   {stats['very_high_conf']:>6,} ({stats['very_high_conf_pct']:>5.1f}%)\n\n")

    f.write("Status Breakdown:\n")
    f.write(f"  OK (clear primary):     {stats['status_ok']:>6,} ({stats['status_ok_pct']:>5.1f}%)\n")
    f.write(f"  Conflict (tie):         {stats['status_conflict']:>6,}\n")
    f.write(f"  Low score:              {stats['status_low_score']:>6,}\n")
    f.write(f"  No entities:            {stats['status_no_entities']:>6,}\n\n")

    f.write("="*80 + "\n")
    f.write("BREAKDOWN BY SOURCE\n")
    f.write("="*80 + "\n\n")

    f.write("Linguistic Papers:\n")
    f.write(f"  Total:                  {ling_stats['total']:>6,}\n")
    f.write(f"  Very high confidence:   {ling_stats['very_high_conf']:>6,} ({ling_stats['very_high_conf_pct']:>5.1f}%)\n\n")

    f.write("SetFit Papers:\n")
    f.write(f"  Total:                  {setfit_stats['total']:>6,}\n")
    f.write(f"  Very high confidence:   {setfit_stats['very_high_conf']:>6,} ({setfit_stats['very_high_conf_pct']:>5.1f}%)\n\n")

    f.write("="*80 + "\n")
    f.write("KEYWORD SCORE DISTRIBUTION\n")
    f.write("="*80 + "\n\n")

    f.write(f"  Mean score:             {df['db_keyword_score'].mean():>6.2f}\n")
    f.write(f"  Median score:           {df['db_keyword_score'].median():>6.0f}\n")
    f.write(f"  Max score:              {df['db_keyword_score'].max():>6.0f}\n")
    f.write(f"  Papers with score > 0:  {(df['db_keyword_score'] > 0).sum():>6,}\n")
    f.write(f"  Papers with score >= 5: {(df['db_keyword_score'] >= 5).sum():>6,}\n")
    f.write(f"  Papers with score >= 10:{(df['db_keyword_score'] >= 10).sum():>6,}\n")

print(f"   ✓ Saved statistics to: {STATS_FILE}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nQuality Indicators Added:")
print(f"  Entity from title:      {stats['entity_from_title']:>6,} ({stats['entity_from_title_pct']:>5.1f}%)")
print(f"  DB keywords found:      {stats['db_keyword_found']:>6,} ({stats['db_keyword_found_pct']:>5.1f}%)")
print(f"  Title matches primary:  {stats['title_entity_in_ner']:>6,} ({stats['title_entity_in_ner_pct']:>5.1f}%)")
print(f"  Very high confidence:   {stats['very_high_conf']:>6,} ({stats['very_high_conf_pct']:>5.1f}%)")

print(f"\nOutput file: {OUTPUT_FILE}")
print(f"Statistics:  {STATS_FILE}")

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
