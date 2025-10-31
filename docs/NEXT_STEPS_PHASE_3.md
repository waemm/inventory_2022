# Next Steps: Phase 3 - Dataset Augmentation

**Date**: 2025-10-30
**Current Status**: Phase 1 & 2 COMPLETE ✅
**Next Phase**: Dataset Augmentation (Phase 3)

---

## 🎯 What We Have Now

### ✅ Phase 1 Complete: Enhanced Metadata Fetching
- **21,392 papers** with 20 metadata fields
- File: `data/metadata/pmc_metadata_enhanced_full.csv`
- 100% Tier 1 completeness (boolean flags)
- 83.1% MeSH terms coverage

### ✅ Phase 2 Complete: Feature Engineering
- **18 engineered ML-ready features**
- File: `data/metadata/features_engineered.csv` (21,392 × 38 columns)
- **Zero NaN values** in all engineered features ✅
- Perfect normalization (mean=0, std=1)
- Transformers saved for reproducibility

### ✅ Code Review Complete
- Overall rating: 8.5/10
- Production ready (conditional pass)
- Files in: `docs/code_reviews/`

---

## 🚀 Phase 3: Dataset Augmentation

### Goal
Merge the engineered metadata features with existing training datasets to enable multi-task learning.

### Tasks

#### 1. Load Training Data
```python
# Classification training data
classif_train = pd.read_csv('data/manual_classifications.csv')
# Expected: 1,635 samples with PMID column

# NER training data
ner_train = pd.read_csv('data/manual_ner_extraction.csv')
# Expected: 554 samples with PMID column
```

#### 2. Load Engineered Features
```python
# Load features
features = pd.read_csv('data/metadata/features_engineered.csv')
# 21,392 papers × 38 features (includes PMID column)
```

#### 3. Merge on PMID
```python
# Join classification data with features
classif_augmented = classif_train.merge(
    features,
    on='id',  # or 'pmid' depending on column name
    how='left'  # Keep all training samples
)

# Join NER data with features
ner_augmented = ner_train.merge(
    features,
    on='id',
    how='left'
)
```

#### 4. Handle Missing Features
For training samples without metadata (PMIDs not in features dataset):
- Option A: Fill with median/mode (use saved transformers)
- Option B: Mark with missing indicators
- Option C: Exclude from training (reduces dataset size)

**Recommendation**: Option A - Use median imputation for numerical, mode for categorical

#### 5. Save Augmented Datasets
```python
# Save augmented datasets
classif_augmented.to_csv('data/classif_splits_full/train_with_metadata.csv', index=False)
ner_augmented.to_csv('data/ner_splits_full/train_with_metadata.csv', index=False)
```

---

## 📋 Implementation Checklist

### Prerequisites
- [ ] Verify training data has PMID/ID column
- [ ] Check column name consistency (id vs pmid)
- [ ] Confirm merge key exists in both datasets

### Core Tasks
- [ ] Create `src/augment_training_data.py` script
- [ ] Implement merge logic with left join
- [ ] Add missing value handling
- [ ] Validate merged datasets (row counts, no unexpected NaN)
- [ ] Save augmented datasets to appropriate directories

### Validation
- [ ] Verify row counts match training data (no rows lost)
- [ ] Check feature coverage (% of samples with metadata)
- [ ] Validate data types remain consistent
- [ ] Spot-check merged data looks correct

### Documentation
- [ ] Document merge strategy
- [ ] Record missing value handling approach
- [ ] Update dataset statistics
- [ ] Create usage examples

---

## 🎓 Expected Outcomes

### Classification Dataset
```
Before: 1,635 samples × 3 columns (id, title, abstract, label)
After:  1,635 samples × 41 columns (original 3 + 38 features)
```

### NER Dataset
```
Before: 554 samples × 4 columns (id, title, abstract, entities)
After:  554 samples × 42 columns (original 4 + 38 features)
```

### Feature Availability
```
Classification: ~80-90% samples will have metadata (overlap with 21K papers)
NER: ~80-90% samples will have metadata
Missing: 10-20% will need imputation
```

---

## ⚠️ Important Considerations

### 1. **PMID Matching**
The code review found 496 missing PMIDs (2.3%) in the metadata. This means:
- ~97.7% of training samples should match
- ~2.3% will need imputation

### 2. **Feature Compatibility**
- Engineered features are **already normalized** (mean=0, std=1)
- No additional preprocessing needed for numerical features
- Boolean features are 0/1 encoded
- TF-IDF features are ready to use

### 3. **Data Splits**
Augment the training data BEFORE splitting into train/val/test to avoid data leakage:
```
Load training data → Merge features → Split into train/val/test
```

### 4. **Transformer Reuse**
For new data, use saved transformers:
```python
import pickle
with open('data/metadata/feature_transformers.pkl', 'rb') as f:
    transformers = pickle.load(f)
```

---

## 🚀 Quick Start Command

**Estimated Time**: 1-2 hours for implementation + testing

```bash
# 1. Create augmentation script
# (Implementation needed)

# 2. Run augmentation
python3 src/augment_training_data.py \
    --classif-data data/manual_classifications.csv \
    --ner-data data/manual_ner_extraction.csv \
    --features data/metadata/features_engineered.csv \
    --output-dir data/augmented/

# 3. Validate outputs
python3 verify_augmented_datasets.py
```

---

## 📊 Success Metrics

Phase 3 is complete when:
- [ ] Augmentation script created and tested
- [ ] Classification dataset augmented (1,635 rows, 41 columns)
- [ ] NER dataset augmented (554 rows, 42 columns)
- [ ] ≥80% feature coverage (samples with metadata)
- [ ] Zero unexpected NaN values
- [ ] Validation script passes all checks
- [ ] Documentation updated

---

## 🔄 After Phase 3: Phase 4 Preview

Once datasets are augmented, Phase 4 will implement:

### Multi-Task Learning Architecture
```
Input: [title, abstract, metadata_features]
    ↓
RoBERTa Encoder (shared)
    ├─→ Classification Head (bio-resource detection)
    ├─→ NER Head (database name extraction)
    └─→ Metadata Prediction Heads (auxiliary tasks)
```

### Expected Impact
- **NER F1**: Current 0.676 → Target ≥0.749 (+10%)
- Improved through:
  - Richer feature representations
  - Better regularization
  - Multi-task learning benefits

---

## 📁 Related Documentation

- **Phase 1 & 2 Report**: `docs/ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md`
- **Code Review**: `docs/code_reviews/CODE_REVIEW_EXECUTIVE_SUMMARY.md`
- **Feature Reference**: `docs/FEATURE_ENGINEERING_QUICK_REFERENCE.md`
- **Main Guide**: `docs/starting_doc.md`

---

## ❓ Decision Points

Before starting Phase 3, decide:

1. **Missing Value Strategy**:
   - A) Median/mode imputation (recommended)
   - B) Zero-fill with missing indicators
   - C) Exclude samples without metadata

2. **Feature Subset**:
   - A) Use all 38 features (recommended)
   - B) Use only Tier 1 (12 core features)
   - C) Custom selection based on correlation analysis

3. **Implementation Approach**:
   - A) Simple script (1-2 hours)
   - B) Comprehensive pipeline with validation (3-4 hours)
   - C) Agent-based implementation with code review

**Recommendation**: Option A for missing values, A for features, B for implementation

---

**Next Action**: Create `src/augment_training_data.py` script

**Estimated Time**: 2-3 hours (implementation + validation + documentation)

**Status**: Ready to begin Phase 3
