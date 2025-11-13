# Biodata Inventory - Data Files Catalogue

**Created**: 2025-11-13
**Purpose**: Comprehensive index of all data files with focus on metadata for training/validation
**Total Dataset Size**: ~1.5 GB across 250+ files

---

## 📊 Executive Summary

### Key Statistics
- **EPMC Query Results**: 254,142 papers (V5.1 - 2011 to mid-2025)
- **Metadata Files**: 122,373 papers with enhanced features (38 attributes)
- **Training Data**: 1,635 classification samples, 554 NER samples
- **Comparison Results**: 156,922 papers analyzed across 3 models
- **Manual Validation**: 100+ papers manually reviewed

### Critical Metadata Files for ML
1. **Enhanced Metadata** (38 features): `data/metadata/features_engineered.csv` - 21,612 papers
2. **Combined Metadata** (all sources): `data/metadata/combined_v4_plus_missing.csv` - 122,373 papers
3. **PyCaret Training Data**: `comparison_pycaret_v2/data/test_set_full.csv` - 3,742 papers
4. **High-Confidence Subset**: `comparison_pycaret_v2/full_v5_comparison/all_three_agree_positive.csv` - 8,129 papers

---

## 🎯 PART 1: METADATA FILES (FOR TRAINING & VALIDATION)

### A. Enhanced Metadata (EPMC - 38 Features)

**Primary Metadata File** ⭐:
- **Location**: `data/metadata/features_engineered.csv`
- **Size**: 48 MB (CSV), 44 MB (pickle)
- **Rows**: 21,612 papers
- **Features**: 38 attributes (20 base + 18 engineered)
- **Format**: CSV + PKL
- **Purpose**: PyCaret metadata classifier training
- **Date Range**: Subset of 2011-2021 EPMC query

**Columns**:
```
Base EPMC Metadata (20):
- id, title, abstract, publication_date
- hasDbCrossReferences, hasData, hasSuppl, isOpenAccess
- inPMC, inEPMC, hasPDF, hasBook
- citedByCount, pubYear, pubType
- keywords, meshTerms, journalTitle, journalISSN
- authorAffiliations

Engineered Features (18):
- mesh_term_count, keyword_count, db_xref_present
- has_abstract, title_length, abstract_length
- access_score, data_availability_score
- publication_age, citations_per_year
- journal_features, author_features
- etc.
```

**Related Files**:
- `data/metadata/features_engineered.pkl` - Pickle format (44 MB)
- `data/metadata/feature_transformers.pkl` - Feature engineering pipeline (63 KB)
- `data/metadata/features_validation.json` - Feature validation report (9.4 KB)

**Usage**:
```python
import pandas as pd
df = pd.read_csv('data/metadata/features_engineered.csv')
# OR
df = pd.read_pickle('data/metadata/features_engineered.pkl')
```

---

### B. Combined Metadata (All Sources)

**Comprehensive Metadata File**:
- **Location**: `data/metadata/combined_v4_plus_missing.csv`
- **Size**: 236 MB
- **Rows**: 122,373 papers (deduplicated)
- **Sources**:
  - V4 query results
  - V5 query results
  - Manual additions
  - Missing training papers
- **Purpose**: Complete metadata repository for all known papers
- **Date Range**: 2011-2021 (primary), some 2022-mid2025

**Key Features**:
- Merges all EPMC query results across versions
- Includes manually added unsearchable papers
- Covers all training data PMIDs
- Deduplicated by PMID

---

### C. PyCaret Training & Test Data

**Test Set (Ground Truth)** ⭐:
- **Location**: `comparison_pycaret_v2/data/test_set_full.csv`
- **Size**: 6.7 MB
- **Rows**: 3,742 papers
- **Labels**: 3,683 positives (98.4%), 59 negatives (1.6%)
- **Features**: Full EPMC metadata (38 attributes)
- **Purpose**: Model evaluation with ground truth labels
- **Date Range**: 2011-2021

**Sample Test Set**:
- **Location**: `comparison_pycaret_v2/data/test_set_sample.csv`
- **Size**: 365 KB
- **Rows**: ~500 papers (stratified sample)
- **Purpose**: Quick model testing

**Unlabeled Production Data**:
- **Location**: `comparison_pycaret_v2/data/unlabeled_set.csv`
- **Size**: 276 MB
- **Rows**: 153,180 papers
- **Purpose**: Production-scale evaluation dataset
- **Date Range**: 2011-2021

---

### D. Missing Training Metadata

**Metadata for Missing Papers**:
- **Location**: `data/metadata/missing_training_metadata.csv`
- **Size**: 5.0 MB
- **Rows**: 795 papers
- **Purpose**: Metadata for training papers not captured in V4 query
- **Status**: Used to improve V5.1 query recall

**Missing PMIDs List**:
- **Location**: `data/metadata/missing_pmids.txt`
- **Size**: 1.7 KB
- **Rows**: 86 PMIDs
- **Purpose**: Papers still not found after enhanced metadata fetch

---

### E. High-Confidence Model Agreement

**Unanimous Positive Predictions** ⭐:
- **Location**: `comparison_pycaret_v2/full_v5_comparison/all_three_agree_positive.csv`
- **Size**: 1.0 MB
- **Rows**: 8,129 papers (5.3% of dataset)
- **Models**: All 3 models (V2, PyCaret-92, PyCaret-112) agree = bio-resource
- **Purpose**: High-confidence training/validation set
- **Use Case**: Gold standard for manual validation

**Model Disagreement (The "Gap")**:
- **Location**: `comparison_pycaret_v2/full_v5_comparison/v2_no_pycaret_true_yes.csv`
- **Size**: 6.3 MB
- **Rows**: 44,013 papers (28.7% of dataset)
- **Description**: PyCaret says YES, V2 says NO
- **Purpose**: Investigate classification boundary differences

**Full Merged Predictions**:
- **Location**: `comparison_pycaret_v2/full_v5_comparison/full_v5_merged_predictions.csv`
- **Size**: 22 MB
- **Rows**: 153,180 papers
- **Columns**: PMID, V2 prediction, PyCaret-92 prediction, PyCaret-112 prediction
- **Purpose**: Complete comparison dataset with all model predictions

---

## 🎓 PART 2: TRAINING DATA (Classification & NER)

### A. Classification Training Data

**Full Training Split** ⭐:
- **Location**: `data/classif_splits_full/`
- **Files**:
  - `train_paper_classif.csv` - 1,111 papers (68.0%)
  - `val_paper_classif.csv` - 239 papers (14.6%)
  - `test_paper_classif.csv` - 240 papers (14.7%)
- **Total**: 1,590 labeled papers
- **Format**: CSV with columns: `id, title, abstract, label`
- **Purpose**: V2 classification model training

**Test Split Only**:
- **Location**: `data/classif_splits_test/`
- **Purpose**: Small test subset for quick validation

**Columns**:
```
id: PMID
title: Paper title
abstract: Paper abstract
label: 1 (bio-resource) or 0 (not bio-resource)
```

---

### B. NER Training Data (Multiple Splits)

**Full NER Training Split** ⭐:
- **Location**: `data/ner_splits_full/`
- **Files**:
  - `train_ner.csv` / `train_ner.pkl` - 307 papers (66.0%)
  - `val_ner.csv` / `val_ner.pkl` - 67 papers (14.4%)
  - `test_ner.csv` / `test_ner.pkl` - 67 papers (14.4%)
- **Total**: 441 annotated papers
- **Format**: CSV + Pickle (nested lists)
- **Purpose**: V2 NER model training

**Entity Complexity Splits** (Phase 2B Research):
- `data/ner_splits_splitA/` - Split A (baseline)
- `data/ner_splits_splitB/` - Split B (balanced complexity)
- `data/ner_splits_splitC/` - Split C
- `data/ner_splits_splitD/` - Split D (high complexity)
- `data/ner_splits_splitE/` through `data/ner_splits_splitK2/` - Additional stratified splits

**Experimental Splits**:
- `data/ner_splits_short/` - Short abstracts only
- `data/ner_splits_long/` - Long abstracts only
- `data/ner_splits_test/` - Test subset

**NER Data Format**:
```python
# CSV columns: id, title, abstract, entities
# Pickle format (nested lists):
[
  {
    'pmid': '12345678',
    'title': 'Paper title',
    'abstract': 'Abstract text',
    'entities': [
      {
        'text': 'Mouse Phenome Database',
        'start': 42,
        'end': 64,
        'label': 'RESOURCE'
      },
      ...
    ]
  },
  ...
]
```

---

### C. Augmented NER Data

**Augmented Training Data**:
- **Location**: `data/augmented/ner_train_test.pkl`
- **Size**: 90 KB (list format), 94 KB (nested format)
- **Purpose**: Data augmentation experiments for NER
- **Format**: Pickle (two variants)

**SplitB Augmented Variants**:
- `data/augmented_splitB/` - SplitB with augmentation
- `data/augmented_splitB_val/` - SplitB validation augmented

---

## 📥 PART 3: EPMC QUERY RESULTS (RAW DATA)

### A. V5.1 Query Results (RECOMMENDED)

**2011-2021 Dataset** ⭐:
- **Location**: `data/final_query_v5.1_2011_2021/query_results.csv`
- **Size**: 284 MB
- **Rows**: 157,192 papers (includes header)
- **Date Range**: 2011-01-01 to 2021-12-31
- **Query Version**: V5.1 (wildcards fixed)
- **Coverage**: 77.3% of training data captured

**2022-mid2025 Dataset**:
- **Location**: `data/final_query_v5.1_2022_mid2025/query_results.csv`
- **Size**: 188 MB
- **Rows**: 98,951 papers (includes header)
- **Date Range**: 2022-01-01 to 2025-06-30
- **Query Version**: V5.1

**Combined Total**: 254,142 papers (V5.1 across all years)

**Columns** (20 EPMC fields):
```
id, title, abstract, publication_date
hasDbCrossReferences, hasData, hasSuppl, isOpenAccess
inPMC, inEPMC, hasPDF, hasBook, citedByCount
pubYear, pubType, keywords, meshTerms
journalTitle, journalISSN, authorAffiliations
```

---

### B. Previous Query Versions (Historical)

**V5.0 (2011-2021)**:
- **Location**: `data/final_query_v5_2011_2021/`
- **Status**: Superseded by V5.1 (wildcard fix)

**V4 (2011-2021)**:
- **Location**: `data/final_query_v4_2011_2021/`
- **Issues**: Lower recall than V5.1

**Comprehensive Query (2011-2021)**:
- **Location**: `data/comprehensive_query_2011_2021/`
- **Status**: Experimental variant

**Balanced Query (2011-2021)**:
- **Location**: `data/balanced_query_2011_2021/`
- **Status**: Experimental variant

---

## 🔬 PART 4: MODEL PREDICTIONS & RESULTS

### A. V2 BERT Predictions

**Full V5.1 Production Predictions**:
- **Location**: `comparison_pycaret_v2/v2_full_v5_predictions/v2_full_v5_predictions.csv`
- **Size**: 286 MB
- **Rows**: 153,180 papers
- **Columns**: PMID, title, abstract, prediction, confidence
- **Model**: V2 BERT classifier
- **Results**: 12,285 bio-resources (8.0%), 140,895 NOT (92.0%)

**Input Data**:
- **Location**: `comparison_pycaret_v2/v2_full_v5_predictions/v5_input_for_v2.csv`
- **Size**: 283 MB
- **Purpose**: Preprocessed V5.1 data for V2 model

---

### B. PyCaret Predictions

**PyCaret TEST_MODE=True (92 features)**:
- Results embedded in `full_v5_merged_predictions.csv`
- Predictions: 52,630 bio-resources (34.4%)

**PyCaret TEST_MODE=False (112 features)**:
- Results embedded in `full_v5_merged_predictions.csv`
- Predictions: 41,638 bio-resources (27.2%)

---

### C. spaCy Hybrid NER Results

**EntityRuler Baseline**:
- **Location**: `spacy_hybrid_ner/results/phase4_entityruler_baseline/entityruler_baseline_predictions.csv`
- **Purpose**: Rule-based NER baseline (exact matches)

**Hybrid System Extractions**:
- **Location**: `spacy_hybrid_ner/results/phase5_hybrid_validation/hybrid_extractions.csv`
- **Purpose**: Combined EntityRuler + Statistical NER results

**Manual Validation**:
- **Location**: `spacy_hybrid_ner/results/manual_validation_detailed.csv`
- **Rows**: 100+ manually reviewed extractions
- **Purpose**: Ground truth for spaCy NER validation

**Speed Benchmark**:
- **Location**: `spacy_hybrid_ner/results/phase5_speed_benchmark/speed_benchmark.csv`
- **Results**: 100-200 papers/sec (optimized batch processing)

---

## 🧪 PART 5: VALIDATION & MANUAL REVIEW DATA

### A. Manual Validation

**Manually Reviewed Inventory**:
- **Location**: `data/manually_reviewed_inventory.csv`
- **Purpose**: Human-validated bio-resource papers
- **Use Case**: Ground truth for model validation

**Validation Sample (100 Resources)**:
- **Location**: `data/validation_sample_100_resources.csv`
- **Purpose**: Stratified sample for quick validation

**Unsearchable Papers**:
- **Location**: `data/unsearchable_papers_manual_add.csv`
- **Purpose**: Papers not found in EPMC but known to be bio-resources
- **Use Case**: Improve query recall analysis

---

### B. GCBR Validation

**GCBR Tagging Sheet**:
- **Location**: `GCBR_tagging_sheet.csv` (root directory)
- **Purpose**: Google Cloud Bioscience Research tagging reference
- **Status**: Used for validation matching

**GCBR Validated**:
- **Location**: `GCBR_tagging_sheet_validated.csv`
- **Purpose**: Validated GCBR matches against EPMC

---

### C. LLM Comparison Data

**Test Set**:
- **Location**: `data/llm_comparison/test_set_combined_300.csv`
- **Rows**: 300 papers (100 positives, 200 negatives)
- **Purpose**: Compare LLM (Claude) vs BERT classification

**Training Set**:
- **Location**: `data/llm_comparison/training_set_combined_100.csv`
- **Rows**: 100 papers (50 positives, 50 negatives)
- **Purpose**: Few-shot examples for LLM

**LLM Predictions**:
- **Location**: `data/llm_comparison/results/claude_sonnet_predictions.csv`
- **Model**: Claude Sonnet 3.5
- **Results**: Detailed in `data/llm_comparison/results/ANALYSIS_SUMMARY.md`

---

## 📦 PART 6: SPECIALIZED DATA FILES

### A. TAPT Corpus (Domain Adaptation)

**Corpus File**:
- **Location**: `data/tapt_corpus.txt`
- **Purpose**: Task-Adaptive Pre-Training corpus for domain-specific BERT
- **Source**: Bio-resource paper abstracts
- **Status**: Prepared but not yet used

**Statistics**:
- **Location**: `data/tapt_corpus_statistics.md`
- **Purpose**: Corpus analysis and statistics

---

### B. Metrics & Monitoring

**Classification Metrics**:
- **Location**: `data/classif_metrics/`
- **Purpose**: Stores classification model evaluation metrics

**NER Metrics**:
- **Location**: `data/ner_metrics/`
- **Purpose**: Stores NER model evaluation metrics

---

## 📍 PART 7: FILE LOCATION QUICK REFERENCE

### Critical Files for ML Training

**Top 10 Most Important Data Files**:

1. ⭐ **Enhanced Metadata (38 features)**
   - `data/metadata/features_engineered.csv` (21,612 papers)
   - Use for: PyCaret training, metadata-only classification

2. ⭐ **Combined Metadata (all sources)**
   - `data/metadata/combined_v4_plus_missing.csv` (122,373 papers)
   - Use for: Complete metadata repository

3. ⭐ **Classification Training Data**
   - `data/classif_splits_full/train_paper_classif.csv` (1,111 papers)
   - Use for: BERT classification model training

4. ⭐ **NER Training Data**
   - `data/ner_splits_full/train_ner.pkl` (307 papers)
   - Use for: BERT NER model training

5. ⭐ **Test Set with Ground Truth**
   - `comparison_pycaret_v2/data/test_set_full.csv` (3,742 papers)
   - Use for: Model evaluation

6. ⭐ **High-Confidence Subset**
   - `comparison_pycaret_v2/full_v5_comparison/all_three_agree_positive.csv` (8,129 papers)
   - Use for: Gold standard validation

7. ⭐ **V5.1 EPMC Query Results**
   - `data/final_query_v5.1_2011_2021/query_results.csv` (157k papers)
   - Use for: Production dataset

8. ⭐ **Full Model Comparison**
   - `comparison_pycaret_v2/full_v5_comparison/full_v5_merged_predictions.csv` (153k papers)
   - Use for: Model comparison analysis

9. ⭐ **Manual Validation Data**
   - `data/manually_reviewed_inventory.csv`
   - Use for: Ground truth validation

10. ⭐ **spaCy NER Patterns**
    - `spacy_hybrid_ner/models/ner_hybrid_v1/entity_ruler/patterns.jsonl`
    - Use for: Rule-based NER (5,000+ patterns)

---

### Data File Size Summary

| Category | Total Size | File Count | Key Files |
|----------|-----------|------------|-----------|
| EPMC Query Results | ~750 MB | 10+ | V5.1 2011-2021, V5.1 2022-mid2025 |
| Metadata | ~350 MB | 15+ | features_engineered, combined_v4 |
| Training Splits | ~50 MB | 100+ | classif_full, ner_full, splitB-K |
| Model Predictions | ~600 MB | 20+ | V2 predictions, PyCaret results |
| Comparison Results | ~30 MB | 10+ | Merged predictions, agreement sets |
| Manual Validation | ~5 MB | 10+ | Manually reviewed, LLM comparison |
| spaCy NER | ~5 MB | 10+ | Patterns, validations, benchmarks |
| **TOTAL** | **~1.8 GB** | **250+** | - |

---

## 🗂️ PART 8: DATA USAGE GUIDE

### For Classification Model Training

**Use these files**:
1. `data/classif_splits_full/train_paper_classif.csv` - Training (1,111 papers)
2. `data/classif_splits_full/val_paper_classif.csv` - Validation (239 papers)
3. `data/classif_splits_full/test_paper_classif.csv` - Testing (240 papers)

**Example**:
```python
import pandas as pd

train_df = pd.read_csv('data/classif_splits_full/train_paper_classif.csv')
val_df = pd.read_csv('data/classif_splits_full/val_paper_classif.csv')
test_df = pd.read_csv('data/classif_splits_full/test_paper_classif.csv')
```

---

### For NER Model Training

**Use these files**:
1. `data/ner_splits_full/train_ner.pkl` - Training (307 papers)
2. `data/ner_splits_full/val_ner.pkl` - Validation (67 papers)
3. `data/ner_splits_full/test_ner.pkl` - Testing (67 papers)

**Example**:
```python
import pickle

with open('data/ner_splits_full/train_ner.pkl', 'rb') as f:
    train_data = pickle.load(f)
```

---

### For Metadata Classification (PyCaret)

**Use these files**:
1. `data/metadata/features_engineered.csv` - Enhanced features (21,612 papers)
2. `comparison_pycaret_v2/data/test_set_full.csv` - Test set with labels (3,742 papers)

**Example**:
```python
import pandas as pd

# Load engineered features
features_df = pd.read_csv('data/metadata/features_engineered.csv')

# Load test set with ground truth
test_df = pd.read_csv('comparison_pycaret_v2/data/test_set_full.csv')
```

---

### For Production Inference

**Use these files**:
1. `data/final_query_v5.1_2011_2021/query_results.csv` - Production dataset (157k papers)
2. `comparison_pycaret_v2/data/unlabeled_set.csv` - Preprocessed for models (153k papers)

---

### For Validation & Benchmarking

**Use these files**:
1. `comparison_pycaret_v2/full_v5_comparison/all_three_agree_positive.csv` - High confidence (8,129)
2. `data/manually_reviewed_inventory.csv` - Manual validation
3. `spacy_hybrid_ner/results/manual_validation_detailed.csv` - NER validation

---

## 📚 PART 9: RELATED DOCUMENTATION

**Metadata Documentation**:
- [`docs/EPMC_QUERY_V5_OPTIMIZATION.md`](EPMC_QUERY_V5_OPTIMIZATION.md) - V5.1 query details
- [`plans/2025-11-10_inventory_epmc_attributes_analysis.md`](../plans/2025-11-10_inventory_epmc_attributes_analysis.md) - Metadata analysis

**Model Comparison**:
- [`docs/V2_PYCARET_COMPARISON_STUDY.md`](V2_PYCARET_COMPARISON_STUDY.md) - Complete comparison study
- [`comparison_pycaret_v2/QUICK_START.md`](../comparison_pycaret_v2/QUICK_START.md) - Quick reference

**Training Guides**:
- [`docs/TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md) - Hyperparameters & validation
- [`docs/TECHNICAL_SPECIFICATIONS.md`](TECHNICAL_SPECIFICATIONS.md) - Model specifications

**spaCy Hybrid NER**:
- [`spacy_hybrid_ner/PHASE4_5_6_COMPLETE.md`](../spacy_hybrid_ner/PHASE4_5_6_COMPLETE.md) - Complete implementation
- [`spacy_hybrid_ner/MANUAL_VALIDATION_STUDY_REPORT.md`](../spacy_hybrid_ner/MANUAL_VALIDATION_STUDY_REPORT.md) - Validation study

---

## 🔄 PART 10: DATA MAINTENANCE

### Data Refresh Cycle

**EPMC Query Results**: Refresh quarterly
- V5.1 query for new papers
- Update metadata for existing papers

**Training Data**: Update semi-annually
- Add new manually validated papers
- Re-split if sample size increases >20%

**Metadata**: Update monthly
- Fetch enhanced metadata for new papers
- Update citation counts for existing papers

### Data Quality Checks

**Before Training**:
- [ ] Check for duplicates (by PMID)
- [ ] Verify no NaN values in critical columns
- [ ] Validate date ranges
- [ ] Confirm label distribution

**After Data Updates**:
- [ ] Run data validation scripts
- [ ] Check metadata coverage
- [ ] Verify file sizes are within expected range
- [ ] Update this catalogue document

---

## 📞 Contact & Support

**Data Issues**: Report in GitHub issues
**Missing Files**: Check Google Drive backups (`inventory_2022/data/`)
**Questions**: See [`docs/starting_doc.md`](starting_doc.md) for full system documentation

---

**Document Status**: ✅ Current and comprehensive
**Last Updated**: 2025-11-13
**Next Review**: After next major data update or model training run
**Maintained By**: AI agents working on biodata inventory pipeline
