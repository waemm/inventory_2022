#!/usr/bin/env python3
"""
Create 4 review samples for SetFit results analysis:
- Each agent gets 200 papers (100 high confidence + 100 medium confidence)
- Agents will score each paper 0-1 on bioresource likelihood
- No overlap between agents
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

print(f"\nConfidence distribution:")
print(f"  High (>=0.7):     {len(high_conf):,} papers")
print(f"  Medium (0.5-0.7): {len(medium_conf):,} papers")
print(f"  Total:            {len(high_conf) + len(medium_conf):,} papers")

# Shuffle for random distribution
high_conf = high_conf.sample(frac=1, random_state=42).reset_index(drop=True)
medium_conf = medium_conf.sample(frac=1, random_state=42).reset_index(drop=True)

# Create 4 non-overlapping samples (100 high + 100 medium each)
print(f"\nCreating 4 review samples (200 papers each: 100 high + 100 medium)...")

samples = []
for i in range(4):
    # Take next 100 from each category
    high_start = i * 100
    high_end = (i + 1) * 100
    medium_start = i * 100
    medium_end = (i + 1) * 100

    sample_high = high_conf.iloc[high_start:high_end].copy()
    sample_medium = medium_conf.iloc[medium_start:medium_end].copy()

    # Combine and shuffle
    sample = pd.concat([sample_high, sample_medium], ignore_index=True)
    sample = sample.sample(frac=1, random_state=42 + i).reset_index(drop=True)

    samples.append(sample)

    print(f"  Agent {i+1}: {len(sample)} papers (high: {len(sample_high)}, medium: {len(sample_medium)})")

# Select key columns for review
review_cols = ['pmid', 'title', 'abstract', 'ling_score', 'setfit_confidence',
               'ling_has_intro_pattern', 'ling_has_title_pattern', 'ling_has_url',
               'ling_impl_keywords', 'ling_usage_keywords']

# Save samples
print(f"\nSaving review samples...")
for i, sample in enumerate(samples):
    filename = f'review_agent{i+1}_sample.csv'
    sample[review_cols].to_csv(filename, index=False)
    print(f"  ✓ {filename} ({len(sample)} papers)")

# Print detailed stats for each sample
print(f"\n{'='*80}")
print("SAMPLE STATISTICS")
print(f"{'='*80}")

for i, sample in enumerate(samples):
    high_count = (sample['setfit_confidence'] >= 0.7).sum()
    medium_count = (sample['setfit_confidence'] < 0.7).sum()

    print(f"\nAgent {i+1} Sample:")
    print(f"  Total papers: {len(sample)}")
    print(f"  High confidence (>=0.7): {high_count} ({100*high_count/len(sample):.1f}%)")
    print(f"  Medium confidence (<0.7): {medium_count} ({100*medium_count/len(sample):.1f}%)")
    print(f"  SetFit confidence: {sample['setfit_confidence'].mean():.3f} ± {sample['setfit_confidence'].std():.3f}")
    print(f"  Linguistic score: {sample['ling_score'].mean():.2f} ± {sample['ling_score'].std():.2f}")
    print(f"  Has intro pattern: {sample['ling_has_intro_pattern'].sum()}/{len(sample)} ({100*sample['ling_has_intro_pattern'].sum()/len(sample):.1f}%)")
    print(f"  Has title pattern: {sample['ling_has_title_pattern'].sum()}/{len(sample)} ({100*sample['ling_has_title_pattern'].sum()/len(sample):.1f}%)")
    print(f"  Has URL: {sample['ling_has_url'].sum()}/{len(sample)} ({100*sample['ling_has_url'].sum()/len(sample):.1f}%)")

# Show example papers from first sample
print(f"\n{'='*80}")
print("EXAMPLE PAPERS (Agent 1 Sample)")
print(f"{'='*80}")

sample1 = samples[0]
for idx in [0, 50, 100, 150]:
    if idx < len(sample1):
        paper = sample1.iloc[idx]
        print(f"\nPaper {idx+1}:")
        print(f"  PMID: {paper['pmid']}")
        print(f"  Title: {paper['title'][:80]}...")
        print(f"  SetFit confidence: {paper['setfit_confidence']:.3f}")
        print(f"  Ling score: {paper['ling_score']}")

print(f"\n{'='*80}")
print("✓ Ready for 4 review agents!")
print(f"{'='*80}")
print("\nEach agent will:")
print("  1. Review 200 papers (100 high + 100 medium confidence)")
print("  2. Score each paper 0-1 on bioresource likelihood")
print("  3. Provide assessment of SetFit classification quality")
