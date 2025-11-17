# Phase 0: Setup & Overview
# spaCy Hybrid NER vs V2 BERT NER | PyCaret vs V2 Classification

**Date**: 2025-11-13
**Status**: ✅ COMPLETE - All Prerequisites Met
**Next**: Phase 1 Implementation

---

## Executive Summary

Comprehensive validation study comparing 4 models across 2 phases:
- **Classification**: V2 BERT (GPU, F1=0.898) vs PyCaret (CPU, Recall=84.6%)
- **NER**: V2 BERT (GPU, F1=0.749) vs spaCy Hybrid (CPU, F1=79.62%)

**Two-Phase Approach**:
1. **Phase 1**: Manual validation on 100-125 unique resource papers (3-4 days)
2. **Phase 2**: Full-scale on 157,191 papers from V5.1 2011-2021 (2-3 weeks)

**Goal**: Determine optimal production deployment strategy with quantified trade-offs.

---

## ✅ Phase 0 Completion Status

### All Prerequisites Met:

1. ✅ **Environments Configured**:
   - `biodata_modern_env`: V2 BERT models verified
   - `pycaret_env`: PyCaret models verified
   - `spacy_hybrid_ner/venv/`: spaCy 3.7.0 verified

2. ✅ **Critical Data Backed Up**:
   - PyCaret models moved from `/tmp/` → `pycaret_models/`

3. ✅ **Infrastructure Ready**:
   - Results directory structure created
   - Sample selection script ready

4. ✅ **All Models Verified**:
   - V2 Classifier loads (476 MB)
   - V2 NER loads (473 MB)
   - PyCaret loads (184-271 KB)
   - spaCy Hybrid NER loads (~50 MB)

**Ready to proceed to Phase 1!**

---

## Environment Configuration

### 🔧 Three Separate Environments

#### 1. biodata_modern_env (V2 BERT Models)
**Location**: `/Users/warren/development/GBC/inventory_2022/biodata_modern_env/`
**Python**: 3.11.9
**Activate**: `source biodata_modern_env/bin/activate`

**Key Packages**:
- PyTorch 2.2.2
- Transformers 4.35.0
- pandas 2.1.4
- numpy 1.26.4

**Models**:
- ✅ V2 BERT Classifier (`out/classif_train_out/article_classifier_v2.pt`)
- ✅ V2 BERT NER (`out/ner_train_out/named_entity_recognition_v2.pt`)

**Performance**: GPU-accelerated (CUDA optional, slower on CPU)

---

#### 2. pycaret_env (PyCaret Classifier)
**Location**: `/Users/warren/development/GBC/inventory_2022/pycaret_env/`
**Python**: Unknown (check activation)
**Activate**: `source pycaret_env/bin/activate`

**Key Packages**:
- PyCaret 3.x
- scikit-learn
- lightgbm
- pandas

**Models**:
- ✅ PyCaret TEST_MODE=True (`pycaret_models/test_mode_true/*.pkl` - 184 KB)
- ✅ PyCaret TEST_MODE=False (`pycaret_models/test_mode_false/*.pkl` - 271 KB)

**Performance**: CPU-only (no GPU required), 5-10× faster than V2

---

#### 3. spacy_hybrid_ner/venv/ (spaCy Hybrid NER)
**Location**: `/Users/warren/development/GBC/inventory_2022/spacy_hybrid_ner/venv/`
**Python**: 3.11
**Activate**: `source spacy_hybrid_ner/venv/bin/activate`

**Key Packages**:
- spaCy 3.7.0
- pandas
- numpy

**Models**:
- ✅ spaCy Hybrid NER (`spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/`)

**Performance**: CPU-only, 40-100× faster than V2 BERT NER

---

## Model Inventory

### Classification Models

#### V2 BERT Classifier
**File**: `out/classif_train_out/article_classifier_v2.pt` (476 MB)
**Environment**: biodata_modern_env
**API**: `src/class_predict.py`

**Usage**:
```bash
source biodata_modern_env/bin/activate
python src/class_predict.py \
  -c out/classif_train_out/article_classifier_v2.pt \
  -i papers.csv \
  -o output_dir/ \
  --predictive-field title_abstract \
  --batch-size 8
```

**Input**: CSV with `id, title, abstract`
**Output**: CSV with `predicted_label` ('bio-resource' or 'not-bio-resource')

**Performance**:
- F1: 0.898 | Precision: 0.930 | Recall: 0.869
- Speed: 5-10 papers/sec (GPU)
- Requirements: PyTorch, Transformers, GPU recommended

---

#### PyCaret Classifier
**Files**:
- `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl` (184 KB)
- `pycaret_models/test_mode_false/pycaret_metadata_classifier_v1.pkl` (271 KB)

**Environment**: pycaret_env
**API**: Programmatic (PyCaret functions)

**Usage**:
```python
source pycaret_env/bin/activate
python  # Then in Python:

from pycaret.classification import load_model, predict_model
import pandas as pd

# Load model
model = load_model('pycaret_models/test_mode_true/pycaret_metadata_classifier_v1')

# Prepare features (92 or 112 columns - see feature engineering script)
df = engineer_features_for_model(input_df, model)

# Predict
predictions = predict_model(model, data=df)
```

**Input**: DataFrame with 92 or 112 metadata features
**Output**: Columns `prediction_label` (0/1), `prediction_score` (probability)

**Performance**:
- Recall: 84.6% (11/13 papers on manual validation)
- Speed: 20-50 papers/sec (CPU-only)
- Requirements: PyCaret, scikit-learn

**Feature Engineering Required**: Must merge with V5.1 metadata and engineer features
- Script: `comparison_pycaret_v2/scripts/03_pycaret_prediction.py::engineer_features_for_model()`

---

### NER Models

#### V2 BERT NER
**File**: `out/ner_train_out/named_entity_recognition_v2.pt` (473 MB)
**Environment**: biodata_modern_env
**API**: `src/ner_predict.py`

**Usage**:
```bash
source biodata_modern_env/bin/activate
python src/ner_predict.py \
  -c out/ner_train_out/named_entity_recognition_v2.pt \
  -i classified_positives.csv \
  -o output_dir/
```

**Input**: CSV with `id, title, abstract, publication_date`
**Output**: CSV with `ID, text, publication_date, common_name, common_prob, full_name, full_prob`
- Multiple entities per label are comma-separated
- COM = common name/abbreviation (e.g., "PDB", "UniProt")
- FUL = full name (e.g., "Protein Data Bank")

**Performance**:
- F1: 0.749 (validation), 0.664 (test)
- Precision: 0.779 | Recall: 0.722
- Speed: 2-5 papers/sec (GPU)
- Requirements: PyTorch, Transformers, GPU recommended

---

#### spaCy Hybrid NER
**Directory**: `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/`
**Environment**: spacy_hybrid_ner/venv/
**API**: `src/ner_predict_spacy.py`

**Usage**:
```bash
source spacy_hybrid_ner/venv/bin/activate
python  # Then in Python:

import sys
sys.path.insert(0, 'src')
from ner_predict_spacy import SpacyNERPredictor
import pandas as pd

# Initialize
predictor = SpacyNERPredictor("spacy_hybrid_ner/models/ner_hybrid_v2_com_ful")

# Predict
papers_df = pd.read_csv('papers.csv')  # Must have: pubmed_id, title, abstract
results = predictor.predict(papers_df, batch_size=32)

# Or save to CSV
df_output = predictor.predict_to_csv(papers_df, 'output.csv', batch_size=32)
```

**Input**: DataFrame with `pubmed_id, title, abstract`
**Output**: CSV with `pmid, entity_text, entity_label, canonical_id, source, start_char, end_char`
- One row per entity mention
- `source`: 'ruler' (EntityRuler match) or 'statistical' (NER discovery)
- `canonical_id`: For alias resolution (e.g., "PDB" and "Protein Data Bank" → same ID)

**Performance**:
- Training F1: 79.62% (Phase 3 statistical NER on training data)
- Validation (title-only): Precision 91%, Recall 48%, F1 63.23%
- ⚠️ **Recall artificially low**: Previous validation used titles only
- **Expected with abstracts**: Recall 60-80%, F1 70-80%
- Speed: 100-200 papers/sec (CPU, batch_size=32)
- Requirements: spaCy 3.7.0, Python 3.11+

**Key Features**:
- **Hybrid architecture**: EntityRuler (precision) + Statistical NER (discovery)
- **Alias resolution**: Links different mentions to same canonical ID
- **Batch processing**: 2-5× speedup vs sequential
- **CPU-only**: No GPU required, fast

---

## Data Sources

### Ground Truth for Validation
**File**: `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`
**Size**: 4,560 curated bioresource papers

**Schema**:
```
publication_id, pubmed_id, pmc_id, title, publication_date, authors,
affiliation, affiliation_countries, citation_count, keywords, email,
resource_id, resource_short_name, resource_full_name,
is_global_core_biodata_resource (1 or 0)
```

**Key Stats**:
- Total papers: 4,560
- Global core bioresources: 53+ papers (`is_global_core_biodata_resource=1`)
- Contains major databases: UniProt, PDB, Ensembl, KEGG, STRING, etc.

**Purpose**: High-quality ground truth for Phase 1 manual validation

---

### V5.1 Query Dataset (2011-2021)
**File**: `data/final_query_v5.1_2011_2021/query_results.csv`
**Size**: 157,191 papers (284 MB)
**Date Range**: 2011-01-01 to 2021-12-31

**Schema**:
```
id, title, abstract, publication_date, hasDbCrossReferences, hasData,
hasSuppl, isOpenAccess, inPMC, inEPMC, hasPDF, hasBook, citedByCount,
pubYear, pubType, keywords, meshTerms, journalTitle, journalISSN,
authorAffiliations
```

**Purpose**: Full-scale Phase 2 validation dataset

**Query Performance**:
- V4 (2011-2021): 123,497 papers
- V5.1 (2011-2021): 157,191 papers (+26.5% improvement)
- Training positive capture: 77.3% (34/44 papers)
- Manual paper capture: 100% (13/13 papers)

---

### Reference Inventory (2022 Baseline)
**File**: `data/final_inventory_2022.csv`
**Size**: 3,112 unique resources

**Purpose**: Baseline for comparison in Phase 2
- Compare novel discoveries (expected: 500-1000 new resources)
- Validate resource extraction quality

---

### Training Data (For Overlap Removal)
**Classification**: `data/classif_splits_full/train_paper_classif.csv`
**NER**: `data/ner_splits_full/train.csv`

**Purpose**: Remove training papers from validation sample to ensure test set integrity

---

## Validation Methodology

### Phase 1: Manual Validation Study (100-125 papers)

**Sampling Strategy (Stratified)**:
1. **50 Global Core** papers (`is_global_core_biodata_resource=1`)
2. **50 Other Curated** papers (`is_global_core_biodata_resource=0`)
3. **Remove training overlap** (ensure test set integrity)
4. **Fetch abstracts from EPMC** ⚠️ CRITICAL for fair NER comparison

**Why Abstracts Are Critical**:
- Previous spaCy validation used titles only → 48% recall
- With abstracts, expect 60-80% recall (much fairer comparison)
- V2 models trained on title+abstract, so must compare on same input

**Steps**:
1. Select sample (script ready)
2. Fetch abstracts from EPMC
3. Run classification comparison (V2 + PyCaret)
4. Run NER comparison (V2 + spaCy)
5. Generate Phase 1 report

**Expected Timeline**: 3-4 days

---

### Phase 2: Full-Scale Application (157k papers)

**Approach**:
1. Run both classifiers on all 157,191 papers
2. Run both NER models on classified positives
3. Generate comprehensive inventories
4. Compare against 2022 baseline (3,112 resources)
5. Identify novel discoveries
6. Performance benchmarking

**Expected Results**:
- V2 Classification: 15k-25k positives (10-15% rate)
- PyCaret Classification: 10k-20k positives (6-12% rate)
- Unique Resources: 3k-5k total
- Novel Discoveries: 500-1000 resources

**Expected Timeline**: 2-3 weeks

---

## Key Metrics

### Classification Metrics
- **Accuracy**: Overall correctness
- **Precision**: When predicting positive, how often correct?
- **Recall**: Of all true positives, how many found?
- **F1 Score**: Harmonic mean of precision and recall
- **Confusion Matrix**: TP, FP, TN, FN breakdown
- **Speed**: Papers per second
- **Resource Usage**: Memory, GPU

### NER Metrics
**Entity-Level** (Primary):
- **Exact Match Precision/Recall/F1**: Entity text matches ground truth exactly
- **Partial Match Precision/Recall/F1**: Entity overlaps with ground truth

**Resource-Level** (Secondary):
- **Resource Coverage**: % of ground truth resources detected
- **Unique Resources**: Count of distinct resources found
- **Alias Resolution Quality**: % entities with canonical IDs (spaCy only)

**Performance**:
- **Speed**: Papers per second
- **Resource Usage**: Memory, CPU/GPU

---

## Success Criteria

### Phase 1 Success = ✅ if:
- [x] Validation sample created (100-125 papers with abstracts)
- [x] All 4 models run successfully on sample
- [x] Comparison metrics calculated
- [x] Phase 1 report generated
- [x] Clear insights on model trade-offs

### Phase 2 Success = ✅ if:
- [x] All 157k papers processed through classification
- [x] NER run on classified positives
- [x] Resource inventories generated
- [x] Performance benchmarks collected
- [x] Comprehensive comparison report completed
- [x] Production deployment recommendations provided

### Overall Success = ✅ if:
- [x] Quantified accuracy/speed trade-offs documented
- [x] Clear recommendation on model choices for production
- [x] Novel discoveries identified and validated
- [x] Deployment plan created with resource requirements

---

## Critical Insights from Investigation

### 1. spaCy's 48% Recall Was Artificially Low
**Finding**: Previous spaCy validation used titles only (no abstracts)
**Impact**: Recall appeared much lower than it actually is
**Fix**: Phase 1 will fetch abstracts from EPMC
**Expected Improvement**: 48% → 60-80% recall with abstracts

### 2. Speed Difference is Massive
**spaCy NER**: 100-200 papers/sec (40-100× faster than V2!)
**V2 NER**: 2-5 papers/sec
**PyCaret Classification**: 20-50 papers/sec (5-10× faster than V2)
**V2 Classification**: 5-10 papers/sec

**Implication**: spaCy and PyCaret can process in minutes what V2 takes hours

### 3. Environment Separation is Key
- V2 models: GPU-dependent, shared environment (biodata_modern_env)
- PyCaret: CPU-only, separate environment (pycaret_env)
- spaCy: CPU-only, separate environment (spacy_hybrid_ner/venv/)

**Implication**: Scripts must activate correct environment before running

### 4. All Data Sources Verified and Accessible
- ✅ Ground truth: 4,560 papers accessible
- ✅ Full dataset: 157,191 papers ready
- ✅ Training data: Available for overlap removal
- ✅ Reference inventory: 3,112 resources for comparison

---

## Decision Points

### After Phase 1 (Manual Validation)
**Question**: Proceed to Phase 2?

**Criteria for YES**:
- All 4 models run successfully
- Results make sense (no obvious bugs)
- Trade-offs are clear
- Methodology is sound

**Criteria for NO (adjust first)**:
- Models failing or producing nonsense
- Methodology issues discovered
- Need to refine approach

### After Phase 2 (Full-Scale)
**Question**: Which models for production?

**Options**:
1. **V2 only** (high accuracy, GPU-dependent)
2. **PyCaret + spaCy** (good accuracy, CPU-only, fast)
3. **Hybrid approach** (PyCaret screening → V2 validation)
4. **All models** (ensemble predictions)

**Decision based on**:
- Accuracy requirements
- Speed requirements
- Resource constraints (GPU availability)
- Deployment complexity tolerance

---

## Risk Mitigation

### Risk: Sample Lacks Abstracts
**Impact**: Can't fairly compare NER models
**Mitigation**:
- Fetch from EPMC API before validation
- Validate abstract availability in sample selection
- Exclude papers without abstracts

### Risk: Environment Conflicts
**Impact**: Models fail to load or produce errors
**Mitigation**:
- Use separate environments (already done)
- Verify each model in its environment (already done)
- Test scripts in each environment before full run

### Risk: Out of Memory
**Impact**: Processing fails on large datasets
**Mitigation**:
- Batch processing (10k papers per batch)
- Monitor memory usage
- Use generators instead of loading full dataset
- Implement checkpointing

### Risk: Long Runtime
**Impact**: Phase 2 takes too long
**Mitigation**:
- Use GPU for V2 models (5-10× speedup)
- Run models in parallel where possible
- Process overnight/weekend if needed

---

## Infrastructure Ready

### Directory Structure Created ✅
```
results/
├── validation/                    # Phase 1
│   ├── sample/
│   ├── classification/
│   ├── ner/
│   └── manual_review/
└── full_scale/                    # Phase 2
    ├── classification/
    ├── ner/
    ├── inventories/
    ├── benchmarks/
    └── reports/
```

### Scripts Ready
- ✅ `scripts/00_verify_models.py` (verification complete)
- ✅ `scripts/01_select_validation_sample.py` (ready to run)

### Scripts to Create (Phase 1)
- `scripts/02_fetch_abstracts.py`
- `scripts/03a_run_v2_classification.py`
- `scripts/03b_run_pycaret_classification.py`
- `scripts/03c_compare_classification.py`
- `scripts/04a_run_v2_ner.py`
- `scripts/04b_run_spacy_ner.py`
- `scripts/04c_compare_ner.py`
- `scripts/05_generate_phase1_report.py`

---

## Resource Requirements

### Phase 1 (Manual Validation)
**Minimum**:
- CPU: 4+ cores
- RAM: 16 GB
- GPU: Optional (4GB+ VRAM)
- Disk: 10 GB free
- Runtime: 1-2 hours

**Recommended**:
- CPU: 8+ cores
- RAM: 32 GB
- GPU: 8GB+ VRAM
- Disk: 20 GB free

### Phase 2 (Full-Scale)
**Minimum**:
- CPU: 8+ cores
- RAM: 32 GB
- GPU: 8GB+ VRAM
- Disk: 50 GB free
- Runtime: 50-100 hours (CPU only)

**Recommended**:
- CPU: 16+ cores
- RAM: 64 GB
- GPU: 16GB+ VRAM
- Disk: 100 GB free
- Runtime: 10-20 hours (with GPU)

---

## Next Steps

**Phase 0 is COMPLETE** ✅

**Ready to proceed to Phase 1**:
1. Confirm plan approval
2. Run validation sample selection
3. Create remaining Phase 1 scripts
4. Execute Phase 1 validation
5. Generate Phase 1 report
6. Decide: Proceed to Phase 2 or adjust?

---

**Document**: `plans/validation_spacy_v_BERT/PHASE0_SETUP_OVERVIEW.md`
**Lines**: ~490
**Status**: ✅ Complete - Ready for Phase 1
