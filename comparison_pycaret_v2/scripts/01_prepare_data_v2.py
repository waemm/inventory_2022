#!/usr/bin/env python3
"""
Phase 1: Data Preparation for PyCaret vs V2 Comparison (v2)

Uses bioresource_papers.csv as ground truth (independent test set)
"""
import pandas as pd
import numpy as np
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent  # Go up to inventory_2022/
V5_QUERY = BASE_DIR / "data/final_query_v5.1_2011_2021/query_results.csv"
GROUND_TRUTH = Path("/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers.csv")
MANUAL_LABELS = BASE_DIR / "data/manual_classifications.csv"  # To check for leakage
OUTPUT_DIR = BASE_DIR / "comparison_pycaret_v2/data"

print("=" * 80)
print("PHASE 1: DATA PREPARATION (v2 - Independent Test Set)")
print("=" * 80)

# Create output directory
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ============================================================================
# Step 1: Load V5.1 Query Data
# ============================================================================
print("\n1. Loading V5.1 query data...")
v5_df = pd.read_csv(str(V5_QUERY), low_memory=False)
print(f"   ✅ Loaded {len(v5_df):,} papers from V5.1 query")

# Convert ID to PMID
v5_df['pmid'] = v5_df['id'].astype(float)

# Remove duplicates
duplicates = v5_df['pmid'].duplicated().sum()
if duplicates > 0:
    print(f"   ⚠️  Removing {duplicates:,} duplicate PMIDs")
    v5_df = v5_df.drop_duplicates(subset='pmid', keep='first')
    print(f"   ✅ Unique papers: {len(v5_df):,}")

# ============================================================================
# Step 2: Load Ground Truth (bioresource_papers.csv)
# ============================================================================
print("\n2. Loading ground truth (bioresource_papers.csv)...")
gt_df = pd.read_csv(str(GROUND_TRUTH))
print(f"   ✅ Loaded {len(gt_df):,} papers from ground truth")

# Extract PMIDs
gt_df['pmid'] = gt_df['pubmed_id'].astype(float)

# Check label distribution
n_positive = (gt_df['is_global_core_biodata_resource'] == 1).sum()
n_negative = (gt_df['is_global_core_biodata_resource'] == 0).sum()
print(f"   ✅ Ground truth labels:")
print(f"      - Positives (bio-resource): {n_positive:,} ({n_positive/len(gt_df)*100:.1f}%)")
print(f"      - Negatives: {n_negative:,} ({n_negative/len(gt_df)*100:.1f}%)")

# ============================================================================
# Step 3: Check Training Data Overlap (Ensure No Leakage)
# ============================================================================
print("\n3. Checking training data overlap...")

def extract_pmid(id_value):
    """Extract numeric PMID or return NaN for non-numeric IDs"""
    try:
        return float(id_value)
    except (ValueError, TypeError):
        if isinstance(id_value, str):
            match = re.match(r'^(\d+)', id_value)
            if match:
                return float(match.group(1))
        return np.nan

manual_df = pd.read_csv(str(MANUAL_LABELS), encoding='latin-1')
manual_df['pmid'] = manual_df['id'].apply(extract_pmid)
manual_df = manual_df[manual_df['pmid'].notna()].copy()

training_pmids = set(manual_df['pmid'])
gt_pmids = set(gt_df['pmid'])
overlap_training = gt_pmids & training_pmids

print(f"   Training data papers: {len(training_pmids):,}")
print(f"   Ground truth papers: {len(gt_pmids):,}")
print(f"   Overlap: {len(overlap_training):,} ({len(overlap_training)/len(gt_pmids)*100:.1f}%)")

if len(overlap_training) > 0:
    print(f"   ⚠️  WARNING: {len(overlap_training):,} papers in both training and test sets")
    print(f"   These will be EXCLUDED from evaluation to prevent data leakage")

# ============================================================================
# Step 4: Merge V5.1 with Ground Truth
# ============================================================================
print("\n4. Merging V5.1 data with ground truth...")

# Merge
v5_with_labels = v5_df.merge(
    gt_df[['pmid', 'is_global_core_biodata_resource', 'resource_short_name', 'resource_full_name']],
    on='pmid',
    how='left'
)

print(f"   ✅ Merge complete: {len(v5_with_labels):,} papers")

# ============================================================================
# Step 5: Create Clean Test Set (No Training Data Leakage)
# ============================================================================
print("\n5. Creating clean test set (excluding training data)...")

# Papers with ground truth labels
test_set_all = v5_with_labels[v5_with_labels['is_global_core_biodata_resource'].notna()].copy()
print(f"   Papers with ground truth in V5.1: {len(test_set_all):,}")

# EXCLUDE papers that are in training data
test_set_clean = test_set_all[~test_set_all['pmid'].isin(training_pmids)].copy()
print(f"   ✅ Clean test set (no training overlap): {len(test_set_clean):,}")

if len(test_set_all) - len(test_set_clean) > 0:
    print(f"   ⚠️  Excluded {len(test_set_all) - len(test_set_clean):,} papers that were in training data")

# Rename label column
test_set_clean = test_set_clean.rename(columns={'is_global_core_biodata_resource': 'ground_truth'})

# Count positives and negatives
test_positive = (test_set_clean['ground_truth'] == 1).sum()
test_negative = (test_set_clean['ground_truth'] == 0).sum()
print(f"   - Positives: {test_positive:,} ({test_positive/len(test_set_clean)*100:.1f}%)")
print(f"   - Negatives: {test_negative:,} ({test_negative/len(test_set_clean)*100:.1f}%)")

# Unlabeled set: Papers without ground truth
unlabeled_set = v5_with_labels[v5_with_labels['is_global_core_biodata_resource'].isna()].copy()
print(f"   ✅ Unlabeled set: {len(unlabeled_set):,} papers")

# ============================================================================
# Step 6: Create Stratified Sample for Testing
# ============================================================================
print("\n6. Creating sample set for notebook testing...")

from sklearn.model_selection import train_test_split

# Stratified sample of 200 papers
if len(test_set_clean) >= 200:
    _, test_sample = train_test_split(
        test_set_clean,
        test_size=200,
        stratify=test_set_clean['ground_truth'],
        random_state=42
    )
    test_sample = test_sample.copy()

    sample_positive = (test_sample['ground_truth'] == 1).sum()
    sample_negative = (test_sample['ground_truth'] == 0).sum()
    print(f"   ✅ Sample set: {len(test_sample):,} papers (stratified)")
    print(f"   - Positives: {sample_positive:,} ({sample_positive/len(test_sample)*100:.1f}%)")
    print(f"   - Negatives: {sample_negative:,} ({sample_negative/len(test_sample)*100:.1f}%)")
else:
    print(f"   ⚠️  Test set too small for 200-paper sample, using all {len(test_set_clean):,} papers")
    test_sample = test_set_clean.copy()

# ============================================================================
# Step 7: Save All Datasets
# ============================================================================
print("\n7. Saving datasets...")

# Test set (full)
test_output = f"{OUTPUT_DIR}/test_set_full.csv"
test_set_clean.to_csv(test_output, index=False)
print(f"   ✅ {test_output} ({len(test_set_clean):,} papers)")

# Test set (sample)
sample_output = f"{OUTPUT_DIR}/test_set_sample.csv"
test_sample.to_csv(sample_output, index=False)
print(f"   ✅ {sample_output} ({len(test_sample):,} papers)")

# Unlabeled set
unlabeled_output = f"{OUTPUT_DIR}/unlabeled_set.csv"
unlabeled_set.to_csv(unlabeled_output, index=False)
print(f"   ✅ {unlabeled_output} ({len(unlabeled_set):,} papers)")

# ============================================================================
# Step 8: Data Quality Validation
# ============================================================================
print("\n8. Validating data quality...")

# Check for missing values
critical_cols = ['pmid', 'title', 'ground_truth']
for col in critical_cols:
    missing = test_set_clean[col].isna().sum()
    if missing > 0:
        print(f"   ⚠️  {col}: {missing:,} missing values")
    else:
        print(f"   ✅ {col}: No missing values")

# Check PMID uniqueness
pmid_unique = test_set_clean['pmid'].is_unique
if pmid_unique:
    print(f"   ✅ PMIDs are unique")
else:
    print(f"   ❌ Duplicate PMIDs found!")

# Check for NaN contamination
nan_check = test_set_clean['pmid'].astype(str).str.contains('nan', case=False, na=False).sum()
if nan_check > 0:
    print(f"   ❌ WARNING: {nan_check} PMIDs contain 'nan' string!")
else:
    print(f"   ✅ No 'nan' contamination in PMIDs")

# Verify no training data leakage
leakage_check = test_set_clean['pmid'].isin(training_pmids).sum()
if leakage_check > 0:
    print(f"   ❌ CRITICAL: {leakage_check} papers from training data still in test set!")
else:
    print(f"   ✅ No training data leakage detected")

# ============================================================================
# Step 9: Generate Summary Report
# ============================================================================
print("\n" + "=" * 80)
print("DATA PREPARATION SUMMARY")
print("=" * 80)

summary = {
    "V5.1 Query Papers": len(v5_df),
    "Ground Truth Papers": len(gt_df),
    "  - Positives (bio-resource)": n_positive,
    "  - Negatives": n_negative,
    "Papers in V5.1 with labels": len(test_set_all),
    "Training data overlap (excluded)": len(test_set_all) - len(test_set_clean),
    "Clean Test Set": len(test_set_clean),
    "  - Positives": test_positive,
    "  - Negatives": test_negative,
    "Sample Set": len(test_sample),
    "Unlabeled Set": len(unlabeled_set),
    "Coverage": f"{len(test_set_all)/len(gt_df)*100:.1f}%"
}

for key, value in summary.items():
    if isinstance(value, str):
        print(f"{key:.<50} {value}")
    else:
        print(f"{key:.<50} {value:,}")

print("\n" + "=" * 80)
print("FILES CREATED")
print("=" * 80)
print(f"✅ {test_output}")
print(f"✅ {sample_output}")
print(f"✅ {unlabeled_output}")

print("\n" + "=" * 80)
print("CRITICAL VALIDATION CHECKS")
print("=" * 80)
print(f"✅ No training data leakage: {leakage_check == 0}")
print(f"✅ PMIDs unique: {pmid_unique}")
print(f"✅ No NaN contamination: {nan_check == 0}")
print(f"✅ Realistic class imbalance: {test_positive/len(test_set_clean)*100:.1f}% positive")

print("\n" + "=" * 80)
print("PHASE 1 COMPLETE")
print("=" * 80)
print("\n✅ Data preparation successful!")
print(f"📊 Clean test set: {len(test_set_clean):,} papers ready for comparison")
print(f"🎯 Next: Phase 2 - V2 Model Inference")
