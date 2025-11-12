#!/usr/bin/env python3
"""
Phase 1: Data Preparation for PyCaret vs V2 Comparison (V3)

Uses ORIGINAL V2 TEST SET to get validated true negatives.

Strategy:
- Positives: All bio-resource papers from bioresource_papers.csv
- Negatives: Validated negatives from original V2 test set (curation_score=0)
- Merge with V5.1 for metadata
- Remove training data overlap
"""

import pandas as pd
from pathlib import Path
import numpy as np

print("=" * 80)
print("PHASE 1: DATA PREPARATION (V3 - Using Original V2 Test Set Negatives)")
print("=" * 80)

# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path("/Users/warren/development/GBC/inventory_2022")
COMPARISON_DIR = BASE_DIR / "comparison_pycaret_v2"
GBC_DIR = Path("/Users/warren/development/GBC/gbc-publication-analysis")

# Input files
V5_QUERY = BASE_DIR / "data/final_query_v5.1_2011_2021/query_results.csv"
BIORESOURCE_PAPERS = GBC_DIR / "bioresource_papers.csv"
ORIGINAL_V2_TEST = BASE_DIR / "data/classif_splits_full/test_paper_classif.csv"
MANUAL_ADD = BASE_DIR / "data/unsearchable_papers_manual_add.csv"

# Output files
OUTPUT_DIR = COMPARISON_DIR / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

test_output = OUTPUT_DIR / "test_set_full.csv"
sample_output = OUTPUT_DIR / "test_set_sample.csv"
unlabeled_output = OUTPUT_DIR / "unlabeled_set.csv"

print(f"\n📁 Input files:")
print(f"   V5.1 query: {V5_QUERY}")
print(f"   Bio-resources: {BIORESOURCE_PAPERS}")
print(f"   Original V2 test: {ORIGINAL_V2_TEST}")
print(f"   Manual add: {MANUAL_ADD}")

# ============================================================================
# Step 1: Load V5.1 Query Results
# ============================================================================
print("\n1. Loading V5.1 query results...")

v5_df = pd.read_csv(V5_QUERY, low_memory=False)
v5_df['pmid'] = v5_df['id'].astype(float)

print(f"   Loaded {len(v5_df):,} papers from V5.1 (2011-2021)")

# Remove duplicate PMIDs (keep first occurrence)
n_before = len(v5_df)
v5_df = v5_df.drop_duplicates(subset=['pmid'], keep='first')
n_after = len(v5_df)
if n_before > n_after:
    print(f"   Removed {n_before - n_after:,} duplicate PMIDs")

print(f"   ✅ {len(v5_df):,} unique papers")

# ============================================================================
# Step 2: Load Bio-Resource Papers (POSITIVES)
# ============================================================================
print("\n2. Loading bio-resource papers (positives)...")

bio_df = pd.read_csv(BIORESOURCE_PAPERS)
print(f"   Original bio-resource papers: {len(bio_df):,}")

# Convert ID column to pmid
if 'pubmed_id' in bio_df.columns:
    bio_df['pmid'] = bio_df['pubmed_id'].astype(float)
elif 'PMID' in bio_df.columns:
    bio_df['pmid'] = bio_df['PMID'].astype(float)
elif 'pmid' in bio_df.columns:
    bio_df['pmid'] = bio_df['pmid'].astype(float)
else:
    raise ValueError("Cannot find PMID column in bioresource_papers.csv")

bio_df['label'] = 1  # All are positives

# Deduplicate by PMID (same paper can appear in multiple resources)
n_before = len(bio_df)
bio_df = bio_df.drop_duplicates(subset=['pmid'], keep='first')
n_after = len(bio_df)
if n_before > n_after:
    print(f"   Removed {n_before - n_after:,} duplicate PMIDs (same paper, multiple resources)")

print(f"   ✅ {len(bio_df):,} unique bio-resource papers loaded as POSITIVES")

# ============================================================================
# Step 3: Load Original V2 Test Set (NEGATIVES)
# ============================================================================
print("\n3. Loading original V2 test set (negatives)...")

v2_test_df = pd.read_csv(ORIGINAL_V2_TEST)

# Handle mixed ID types (some are PMC IDs, most are PMIDs)
# Extract numeric IDs only
v2_test_df['id_str'] = v2_test_df['id'].astype(str)
v2_test_df = v2_test_df[v2_test_df['id_str'].str.isnumeric()].copy()
v2_test_df['pmid'] = v2_test_df['id'].astype(float)

print(f"   Original V2 test set: {len(v2_test_df):,} papers")
print(f"   Label distribution:")
print(f"      curation_score=1 (bio-resource): {(v2_test_df['curation_score']==1).sum()}")
print(f"      curation_score=0 (NOT bio-resource): {(v2_test_df['curation_score']==0).sum()}")

# Extract NEGATIVES only (curation_score=0)
negatives_df = v2_test_df[v2_test_df['curation_score'] == 0].copy()
negatives_df['label'] = 0  # Mark as negatives

print(f"   ✅ Extracted {len(negatives_df):,} validated NEGATIVES")

# ============================================================================
# Step 4: Check Training Data Overlap
# ============================================================================
print("\n4. Checking for training data overlap...")

# Load training PMIDs
manual_df = pd.read_csv(MANUAL_ADD)
if 'PMID' in manual_df.columns:
    manual_df['pmid'] = manual_df['PMID'].astype(float)
elif 'pmid' not in manual_df.columns:
    manual_df['pmid'] = manual_df['id'].astype(float)

training_pmids = set(manual_df['pmid'])

print(f"   Training data papers: {len(training_pmids):,}")

# Check overlap with positives
bio_pmids = set(bio_df['pmid'])
overlap_bio = bio_pmids & training_pmids
print(f"   Bio-resources in training: {len(overlap_bio):,} ({len(overlap_bio)/len(bio_pmids)*100:.1f}%)")

# Check overlap with negatives
neg_pmids = set(negatives_df['pmid'])
overlap_neg = neg_pmids & training_pmids
print(f"   Negatives in training: {len(overlap_neg):,} ({len(overlap_neg)/len(neg_pmids)*100:.1f}%)")

# ============================================================================
# Step 5: Filter to V5.1 Coverage
# ============================================================================
print("\n5. Filtering to V5.1 coverage...")

v5_pmids = set(v5_df['pmid'])

# Positives in V5.1
bio_in_v5 = bio_df[bio_df['pmid'].isin(v5_pmids)].copy()
print(f"   Bio-resources in V5.1: {len(bio_in_v5):,} / {len(bio_df):,} ({len(bio_in_v5)/len(bio_df)*100:.1f}%)")

# Negatives in V5.1
neg_in_v5 = negatives_df[negatives_df['pmid'].isin(v5_pmids)].copy()
print(f"   Negatives in V5.1: {len(neg_in_v5):,} / {len(negatives_df):,} ({len(neg_in_v5)/len(negatives_df)*100:.1f}%)")

# ============================================================================
# Step 6: Remove Training Data Overlap
# ============================================================================
print("\n6. Removing training data overlap...")

# Exclude training data from positives
bio_clean = bio_in_v5[~bio_in_v5['pmid'].isin(training_pmids)].copy()
excluded_bio = len(bio_in_v5) - len(bio_clean)
print(f"   Bio-resources after training exclusion: {len(bio_clean):,} (excluded {excluded_bio:,})")

# Exclude training data from negatives
neg_clean = neg_in_v5[~neg_in_v5['pmid'].isin(training_pmids)].copy()
excluded_neg = len(neg_in_v5) - len(neg_clean)
print(f"   Negatives after training exclusion: {len(neg_clean):,} (excluded {excluded_neg:,})")

# ============================================================================
# Step 7: Merge with V5.1 Metadata
# ============================================================================
print("\n7. Merging with V5.1 metadata...")

# Combine positives and negatives
test_pmids = pd.concat([
    bio_clean[['pmid', 'label']],
    neg_clean[['pmid', 'label']]
], ignore_index=True)

print(f"   Total test papers: {len(test_pmids):,}")
print(f"      Positives: {(test_pmids['label']==1).sum():,}")
print(f"      Negatives: {(test_pmids['label']==0).sum():,}")

# Merge with V5.1 to get full metadata
test_set = v5_df.merge(test_pmids, on='pmid', how='inner')

# Remove any duplicates created by merge
n_before_dedup = len(test_set)
test_set = test_set.drop_duplicates(subset=['pmid'], keep='first')
if n_before_dedup > len(test_set):
    print(f"   Removed {n_before_dedup - len(test_set)} duplicate(s) from merge")

# Rename label to ground_truth for consistency
test_set = test_set.rename(columns={'label': 'ground_truth'})

# Add resource names for positives
if 'resource_short_name' in bio_df.columns:
    resource_info = bio_df[['pmid', 'resource_short_name', 'resource_full_name']].copy()
    test_set = test_set.merge(resource_info, on='pmid', how='left')

print(f"   ✅ Merged: {len(test_set):,} papers with metadata")

# Verify counts
n_positive = (test_set['ground_truth'] == 1).sum()
n_negative = (test_set['ground_truth'] == 0).sum()
print(f"      Positives: {n_positive:,} ({n_positive/len(test_set)*100:.1f}%)")
print(f"      Negatives: {n_negative:,} ({n_negative/len(test_set)*100:.1f}%)")

# ============================================================================
# Step 8: Create Sample Set
# ============================================================================
print("\n8. Creating sample set for testing...")

from sklearn.model_selection import train_test_split

if len(test_set) >= 200:
    _, test_sample = train_test_split(
        test_set,
        test_size=200,
        stratify=test_set['ground_truth'],
        random_state=42
    )
    test_sample = test_sample.copy()

    sample_positive = (test_sample['ground_truth'] == 1).sum()
    sample_negative = (test_sample['ground_truth'] == 0).sum()
    print(f"   ✅ Sample set: {len(test_sample):,} papers (stratified)")
    print(f"      Positives: {sample_positive:,} ({sample_positive/len(test_sample)*100:.1f}%)")
    print(f"      Negatives: {sample_negative:,} ({sample_negative/len(test_sample)*100:.1f}%)")
else:
    print(f"   ⚠️  Test set too small for 200-paper sample, using all {len(test_set):,} papers")
    test_sample = test_set.copy()

# ============================================================================
# Step 9: Create Unlabeled Set
# ============================================================================
print("\n9. Creating unlabeled set...")

# Papers in V5.1 but not in test set
test_pmids_set = set(test_set['pmid'])
unlabeled_set = v5_df[~v5_df['pmid'].isin(test_pmids_set)].copy()

print(f"   ✅ Unlabeled set: {len(unlabeled_set):,} papers")

# ============================================================================
# Step 10: Save Datasets
# ============================================================================
print("\n10. Saving datasets...")

test_set.to_csv(test_output, index=False)
print(f"   ✅ {test_output}")

test_sample.to_csv(sample_output, index=False)
print(f"   ✅ {sample_output}")

unlabeled_set.to_csv(unlabeled_output, index=False)
print(f"   ✅ {unlabeled_output}")

# ============================================================================
# Step 11: Validation
# ============================================================================
print("\n11. Validation checks...")

# Check for duplicates
pmid_unique = test_set['pmid'].nunique() == len(test_set)
if pmid_unique:
    print(f"   ✅ No duplicate PMIDs")
else:
    print(f"   ❌ Duplicate PMIDs found!")

# Check for NaN contamination
nan_check = test_set['pmid'].astype(str).str.contains('nan', case=False, na=False).sum()
if nan_check > 0:
    print(f"   ❌ WARNING: {nan_check} PMIDs contain 'nan' string!")
else:
    print(f"   ✅ No 'nan' contamination in PMIDs")

# Verify no training data leakage
leakage_check = test_set['pmid'].isin(training_pmids).sum()
if leakage_check > 0:
    print(f"   ❌ CRITICAL: {leakage_check} papers from training data still in test set!")
else:
    print(f"   ✅ No training data leakage detected")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("DATA PREPARATION SUMMARY")
print("=" * 80)

summary = {
    "V5.1 Query Papers": len(v5_df),
    "Bio-resource Papers (all)": len(bio_df),
    "Original V2 Test Negatives": len(negatives_df),
    "Bio-resources in V5.1": len(bio_in_v5),
    "Negatives in V5.1": len(neg_in_v5),
    "Training overlap (excluded)": excluded_bio + excluded_neg,
    "Clean Test Set": len(test_set),
    "  - Positives (bio-resource)": n_positive,
    "  - Negatives (NOT bio-resource)": n_negative,
    "Sample Set": len(test_sample),
    "Unlabeled Set": len(unlabeled_set),
}

for key, value in summary.items():
    if isinstance(value, str):
        print(f"{key:.<50} {value}")
    else:
        print(f"{key:.<50} {value:,}")

print("\n" + "=" * 80)
print("CRITICAL VALIDATION CHECKS")
print("=" * 80)
print(f"✅ No training data leakage: {leakage_check == 0}")
print(f"✅ PMIDs unique: {pmid_unique}")
print(f"✅ No NaN contamination: {nan_check == 0}")
print(f"✅ Has TRUE NEGATIVES: {n_negative > 0}")
print(f"✅ Balanced classes: {n_positive/len(test_set)*100:.1f}% positive")

print("\n" + "=" * 80)
print("PHASE 1 COMPLETE")
print("=" * 80)
print("\n✅ Data preparation successful!")
print(f"📊 Clean test set: {len(test_set):,} papers ready for comparison")
print(f"   ✅ {n_positive:,} TRUE positives (bio-resources)")
print(f"   ✅ {n_negative:,} TRUE negatives (NOT bio-resources)")
print(f"\n🎯 Next: Phase 2 - V2 Model Inference")
