#!/usr/bin/env python3
"""
Create 7 additional review samples for SetFit results analysis:
- Each agent gets 400 papers (200 high confidence + 200 medium confidence)
- Papers are DISTINCT from first 4 agents (indices 400-1799 used)
- No overlap between these 7 agents
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

# Shuffle for random distribution (same seed as first 4 agents)
high_conf = high_conf.sample(frac=1, random_state=42).reset_index(drop=True)
medium_conf = medium_conf.sample(frac=1, random_state=42).reset_index(drop=True)

# Create 7 non-overlapping samples (200 high + 200 medium each)
# Start from index 400 (first 400 already used by agents 1-4)
print(f"\nCreating 7 review samples (400 papers each: 200 high + 200 medium)...")
print(f"Using indices 400-1799 (avoiding first 400 used by agents 1-4)")

samples = []
for i in range(7):
    # Agent 5-11: indices 400-1799
    # Agent 5: 400-599, Agent 6: 600-799, etc.
    agent_num = i + 5  # Agents 5-11
    base_index = 400 + (i * 200)

    high_start = base_index
    high_end = base_index + 200
    medium_start = base_index
    medium_end = base_index + 200

    sample_high = high_conf.iloc[high_start:high_end].copy()
    sample_medium = medium_conf.iloc[medium_start:medium_end].copy()

    # Combine and shuffle
    sample = pd.concat([sample_high, sample_medium], ignore_index=True)
    sample = sample.sample(frac=1, random_state=42 + agent_num).reset_index(drop=True)

    samples.append(sample)

    print(f"  Agent {agent_num}: {len(sample)} papers (high: {len(sample_high)}, medium: {len(sample_medium)}) - indices {base_index}-{base_index+199}")

# Select key columns for review
review_cols = ['pmid', 'title', 'abstract', 'ling_score', 'setfit_confidence',
               'ling_has_intro_pattern', 'ling_has_title_pattern', 'ling_has_url',
               'ling_impl_keywords', 'ling_usage_keywords']

# Save samples
print(f"\nSaving review samples...")
for i, sample in enumerate(samples):
    agent_num = i + 5
    filename = f'review_agent{agent_num}_sample.csv'
    sample[review_cols].to_csv(filename, index=False)
    print(f"  ✓ {filename} ({len(sample)} papers)")

# Print detailed stats for each sample
print(f"\n{'='*80}")
print("SAMPLE STATISTICS")
print(f"{'='*80}")

for i, sample in enumerate(samples):
    agent_num = i + 5
    high_count = (sample['setfit_confidence'] >= 0.7).sum()
    medium_count = (sample['setfit_confidence'] < 0.7).sum()

    print(f"\nAgent {agent_num} Sample:")
    print(f"  Total papers: {len(sample)}")
    print(f"  High confidence (>=0.7): {high_count} ({100*high_count/len(sample):.1f}%)")
    print(f"  Medium confidence (<0.7): {medium_count} ({100*medium_count/len(sample):.1f}%)")
    print(f"  SetFit confidence: {sample['setfit_confidence'].mean():.3f} ± {sample['setfit_confidence'].std():.3f}")
    print(f"  Linguistic score: {sample['ling_score'].mean():.2f} ± {sample['ling_score'].std():.2f}")
    print(f"  Has intro pattern: {sample['ling_has_intro_pattern'].sum()}/{len(sample)} ({100*sample['ling_has_intro_pattern'].sum()/len(sample):.1f}%)")
    print(f"  Has title pattern: {sample['ling_has_title_pattern'].sum()}/{len(sample)} ({100*sample['ling_has_title_pattern'].sum()/len(sample):.1f}%)")
    print(f"  Has URL: {sample['ling_has_url'].sum()}/{len(sample)} ({100*sample['ling_has_url'].sum()/len(sample):.1f}%)")

print(f"\n{'='*80}")
print("✓ Ready for 7 additional review agents!")
print(f"{'='*80}")
print(f"\nTotal review coverage:")
print(f"  Agents 1-4:  800 papers (indices 0-399)")
print(f"  Agents 5-11: 2,800 papers (indices 400-1799)")
print(f"  Total:       3,600 papers")
print(f"  Coverage:    {3600}/{len(df)} = {100*3600/len(df):.1f}% of SetFit introductions")

print(f"\nEach agent will:")
print(f"  1. Review 400 papers (200 high + 200 medium confidence)")
print(f"  2. Score each paper 0-1 on bioresource likelihood")
print(f"  3. Generate scored results and summary")
