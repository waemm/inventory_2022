#!/usr/bin/env python3
"""
Phase 1: Data Preparation for PyCaret vs V2 Comparison

Prepares V5.1 query data for model comparison:
- Loads V5.1 query results (156,231 papers)
- Merges with ground truth labels from manual_classifications.csv
- Creates evaluation set (papers with labels)
- Creates unlabeled set (papers without labels)
- Creates sample set for notebook testing
- Validates data quality
"""
import pandas as pd
import numpy as np
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent  # Go up to inventory_2022/
V5_QUERY = BASE_DIR / "data/final_query_v5.1_2011_2021/query_results.csv"
MANUAL_LABELS = BASE_DIR / "data/manual_classifications.csv"
OUTPUT_DIR = BASE_DIR / "comparison_pycaret_v2/data"

print("=" * 80)
print("PHASE 1: DATA PREPARATION")
print("=" * 80)

# Create output directory
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ============================================================================
# Step 1: Load V5.1 Query Data
# ============================================================================
print("\n1. Loading V5.1 query data...")
v5_df = pd.read_csv(str(V5_QUERY), low_memory=False)
print(f"   ✅ Loaded {len(v5_df):,} papers from V5.1 query")

# Validate required columns
required_v2_cols = ['id', 'title', 'abstract']
required_pycaret_cols = ['id', 'meshTerms', 'journalTitle', 'citedByCount', 'pubYear',
                         'pubType', 'hasData', 'isOpenAccess', 'keywords']

missing_v2 = [col for col in required_v2_cols if col not in v5_df.columns]
missing_pycaret = [col for col in required_pycaret_cols if col not in v5_df.columns]

if missing_v2:
    raise ValueError(f"❌ Missing V2 columns: {missing_v2}")
if missing_pycaret:
    raise ValueError(f"❌ Missing PyCaret columns: {missing_pycaret}")

print(f"   ✅ All required columns present")

# Check data quality
print(f"\n   Data Quality:")
print(f"   - Missing titles: {v5_df['title'].isna().sum():,} ({v5_df['title'].isna().mean():.1%})")
print(f"   - Missing abstracts: {v5_df['abstract'].isna().sum():,} ({v5_df['abstract'].isna().mean():.1%})")
print(f"   - Missing meshTerms: {v5_df['meshTerms'].isna().sum():,} ({v5_df['meshTerms'].isna().mean():.1%})")
print(f"   - Missing journalTitle: {v5_df['journalTitle'].isna().sum():,} ({v5_df['journalTitle'].isna().mean():.1%})")

# Convert ID to PMID
v5_df['pmid'] = v5_df['id'].astype(float)
print(f"   ✅ PMID conversion complete")

# ============================================================================
# Step 2: Load Manual Classifications (Ground Truth)
# ============================================================================
print("\n2. Loading ground truth labels...")

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
print(f"   ✅ Loaded {len(manual_df):,} papers from manual_classifications.csv")

# Extract PMIDs
manual_df['pmid'] = manual_df['id'].apply(extract_pmid)
manual_df = manual_df[manual_df['pmid'].notna()].copy()
print(f"   ✅ Extracted {len(manual_df):,} valid PMIDs")

# Create clean label dataframe
manual_labels = manual_df[['pmid', 'curation_score', 'title']].copy()
manual_labels = manual_labels.rename(columns={
    'curation_score': 'ground_truth',
    'title': 'title_gt'
})

# Count labels
n_positive = (manual_labels['ground_truth'] == 1).sum()
n_negative = (manual_labels['ground_truth'] == 0).sum()
print(f"   ✅ Ground truth labels:")
print(f"      - Positives (bio-resource): {n_positive:,}")
print(f"      - Negatives: {n_negative:,}")

# ============================================================================
# Step 3: Merge V5.1 with Ground Truth
# ============================================================================
print("\n3. Merging V5.1 data with ground truth...")

# Merge
v5_with_labels = v5_df.merge(
    manual_labels,
    on='pmid',
    how='left',
    suffixes=('', '_manual')
)

print(f"   ✅ Merge complete: {len(v5_with_labels):,} papers")

# Check for duplicates
duplicates = v5_with_labels['pmid'].duplicated().sum()
if duplicates > 0:
    print(f"   ⚠️  Warning: {duplicates} duplicate PMIDs found")
    # Keep first occurrence
    v5_with_labels = v5_with_labels.drop_duplicates(subset='pmid', keep='first')
    print(f"   ✅ Duplicates removed: {len(v5_with_labels):,} unique papers")

# ============================================================================
# Step 4: Split into Evaluation and Unlabeled Sets
# ============================================================================
print("\n4. Creating evaluation and unlabeled sets...")

# Evaluation set: Papers with ground truth
eval_set = v5_with_labels[v5_with_labels['ground_truth'].notna()].copy()
print(f"   ✅ Evaluation set: {len(eval_set):,} papers")

# Check expected size
if len(eval_set) != 987:
    print(f"   ⚠️  Warning: Expected 987 papers, got {len(eval_set):,}")
    # Analyze difference
    expected_pmids = set(manual_labels['pmid'])
    v5_pmids = set(v5_df['pmid'])
    missing_from_v5 = expected_pmids - v5_pmids
    if missing_from_v5:
        print(f"   ⚠️  {len(missing_from_v5):,} ground truth papers not in V5.1 query")

# Count positives and negatives in evaluation set
eval_positive = (eval_set['ground_truth'] == 1).sum()
eval_negative = (eval_set['ground_truth'] == 0).sum()
print(f"   - Positives: {eval_positive:,} ({eval_positive/len(eval_set)*100:.1f}%)")
print(f"   - Negatives: {eval_negative:,} ({eval_negative/len(eval_set)*100:.1f}%)")

# Unlabeled set: Papers without ground truth
unlabeled_set = v5_with_labels[v5_with_labels['ground_truth'].isna()].copy()
print(f"   ✅ Unlabeled set: {len(unlabeled_set):,} papers")

# ============================================================================
# Step 5: Create Sample Set for Testing
# ============================================================================
print("\n5. Creating sample set for notebook testing...")

# Stratified sample of 200 papers
from sklearn.model_selection import train_test_split

_, eval_sample = train_test_split(
    eval_set,
    test_size=200,
    stratify=eval_set['ground_truth'],
    random_state=42
)

eval_sample = eval_sample.copy()
print(f"   ✅ Sample set: {len(eval_sample):,} papers (stratified)")

sample_positive = (eval_sample['ground_truth'] == 1).sum()
sample_negative = (eval_sample['ground_truth'] == 0).sum()
print(f"   - Positives: {sample_positive:,} ({sample_positive/len(eval_sample)*100:.1f}%)")
print(f"   - Negatives: {sample_negative:,} ({sample_negative/len(eval_sample)*100:.1f}%)")

# ============================================================================
# Step 6: Save All Datasets
# ============================================================================
print("\n6. Saving datasets...")

# Evaluation set (full)
eval_output = f"{OUTPUT_DIR}/evaluation_set_full.csv"
eval_set.to_csv(eval_output, index=False)
print(f"   ✅ {eval_output} ({len(eval_set):,} papers)")

# Evaluation set (sample)
sample_output = f"{OUTPUT_DIR}/evaluation_set_sample.csv"
eval_sample.to_csv(sample_output, index=False)
print(f"   ✅ {sample_output} ({len(eval_sample):,} papers)")

# Unlabeled set
unlabeled_output = f"{OUTPUT_DIR}/unlabeled_set.csv"
unlabeled_set.to_csv(unlabeled_output, index=False)
print(f"   ✅ {unlabeled_output} ({len(unlabeled_set):,} papers)")

# ============================================================================
# Step 7: Data Quality Validation
# ============================================================================
print("\n7. Validating data quality...")

# Check for missing values in critical columns
critical_cols = ['pmid', 'title', 'ground_truth']
for col in critical_cols:
    missing = eval_set[col].isna().sum()
    if missing > 0:
        print(f"   ⚠️  {col}: {missing:,} missing values")
    else:
        print(f"   ✅ {col}: No missing values")

# Check PMID uniqueness
pmid_unique = eval_set['pmid'].is_unique
if pmid_unique:
    print(f"   ✅ PMIDs are unique")
else:
    print(f"   ❌ Duplicate PMIDs found!")

# Check label distribution
label_counts = eval_set['ground_truth'].value_counts()
print(f"\n   Label Distribution:")
print(f"   - Bio-resource (1): {label_counts.get(1, 0):,}")
print(f"   - Not bio-resource (0): {label_counts.get(0, 0):,}")
print(f"   - Balance: {label_counts.get(1, 0)/len(eval_set)*100:.1f}% positive")

# Check for NaN contamination in PMIDs
nan_check = eval_set['pmid'].astype(str).str.contains('nan', case=False, na=False).sum()
if nan_check > 0:
    print(f"   ❌ WARNING: {nan_check} PMIDs contain 'nan' string!")
else:
    print(f"   ✅ No 'nan' contamination in PMIDs")

# ============================================================================
# Step 8: Generate Summary Report
# ============================================================================
print("\n" + "=" * 80)
print("DATA PREPARATION SUMMARY")
print("=" * 80)

summary = {
    "V5.1 Query Papers": len(v5_df),
    "Manual Classifications": len(manual_df),
    "Evaluation Set": len(eval_set),
    "  - Positives": eval_positive,
    "  - Negatives": eval_negative,
    "Sample Set": len(eval_sample),
    "Unlabeled Set": len(unlabeled_set),
    "Coverage": f"{len(eval_set)/len(manual_df)*100:.1f}%"
}

for key, value in summary.items():
    if isinstance(value, str):
        print(f"{key:.<40} {value}")
    else:
        print(f"{key:.<40} {value:,}")

print("\n" + "=" * 80)
print("FILES CREATED")
print("=" * 80)
print(f"✅ {eval_output}")
print(f"✅ {sample_output}")
print(f"✅ {unlabeled_output}")

print("\n" + "=" * 80)
print("PHASE 1 COMPLETE")
print("=" * 80)
print("\n✅ Data preparation successful!")
print(f"📊 Evaluation set: {len(eval_set):,} papers ready for comparison")
print(f"🎯 Next: Phase 2 - V2 Model Inference")
