#!/usr/bin/env python3
"""
Create 3 review samples for SetFit results analysis:
- Agent 1: 100 high-confidence papers (confidence >= 0.7)
- Agent 2: 100 medium-confidence papers (0.5 <= confidence < 0.7)
- Agent 3: 100 low-confidence papers (confidence < 0.5)
"""

import pandas as pd
import random

random.seed(42)

# Load SetFit introductions
print("Loading SetFit classified introductions...")
df = pd.read_csv('setfit_classified_introductions.csv')
print(f"Total introductions: {len(df):,}")
print(f"Confidence range: {df['setfit_confidence'].min():.3f} - {df['setfit_confidence'].max():.3f}")

# Split by confidence levels
high_conf = df[df['setfit_confidence'] >= 0.7].copy()
medium_conf = df[(df['setfit_confidence'] >= 0.5) & (df['setfit_confidence'] < 0.7)].copy()
low_conf = df[df['setfit_confidence'] < 0.5].copy()

print(f"\nConfidence distribution:")
print(f"  High (>=0.7):   {len(high_conf):,} papers")
print(f"  Medium (0.5-0.7): {len(medium_conf):,} papers")
print(f"  Low (<0.5):     {len(low_conf):,} papers")

# Sample 100 from each category
print(f"\nSampling 100 papers from each category...")

sample_high = high_conf.sample(min(100, len(high_conf)), random_state=42)
sample_medium = medium_conf.sample(min(100, len(medium_conf)), random_state=42)
sample_low = low_conf.sample(min(100, len(low_conf)), random_state=42)

# Select key columns for review
review_cols = ['pmid', 'title', 'abstract', 'ling_score', 'setfit_confidence',
               'ling_has_intro_pattern', 'ling_has_title_pattern', 'ling_has_url',
               'ling_impl_keywords', 'ling_usage_keywords']

# Save samples
sample_high[review_cols].to_csv('review_agent1_high_confidence.csv', index=False)
sample_medium[review_cols].to_csv('review_agent2_medium_confidence.csv', index=False)
sample_low[review_cols].to_csv('review_agent3_low_confidence.csv', index=False)

print(f"\nSamples created:")
print(f"  ✓ review_agent1_high_confidence.csv ({len(sample_high)} papers)")
print(f"  ✓ review_agent2_medium_confidence.csv ({len(sample_medium)} papers)")
print(f"  ✓ review_agent3_low_confidence.csv ({len(sample_low)} papers)")

# Print stats for each sample
for name, sample in [('Agent 1 (High)', sample_high),
                      ('Agent 2 (Medium)', sample_medium),
                      ('Agent 3 (Low)', sample_low)]:
    print(f"\n{name}:")
    print(f"  Confidence: {sample['setfit_confidence'].mean():.3f} ± {sample['setfit_confidence'].std():.3f}")
    print(f"  Ling score: {sample['ling_score'].mean():.2f} ± {sample['ling_score'].std():.2f}")
    print(f"  Has intro pattern: {sample['ling_has_intro_pattern'].sum()}/{len(sample)}")
    print(f"  Has title pattern: {sample['ling_has_title_pattern'].sum()}/{len(sample)}")
    print(f"  Has URL: {sample['ling_has_url'].sum()}/{len(sample)}")

print("\n✓ Ready for review agent analysis!")
