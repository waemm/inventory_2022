# Critical Files Reference - Model Validation Study

**Created**: 2025-11-13
**Purpose**: Quick reference for all critical files, models, and environments
**Source**: Extracted from `plans/validation_spacy_v_BERT/PROGRESS.md` and `docs/DATA_CATALOGUE.md`
**Status**: Phase 1 - Manual Validation (100-125 papers)

---

## 🎯 Quick Navigation

- [Environments](#-environments)
- [Models](#-models)
- [Ground Truth Data](#-ground-truth-data)
- [Training Data](#-training-data-to-exclude)
- [Full Datasets](#-full-datasets)
- [Quick Commands](#-quick-commands)
- [Critical Paths Summary](#-critical-paths-summary)

---

## 🌍 Environments

### Environment 1: biodata_modern_env (V2 BERT Models)

**Location**: `/Users/warren/development/GBC/inventory_2022/biodata_modern_env/`

**Activation**:
```bash
cd /Users/warren/development/GBC/inventory_2022
source biodata_modern_env/bin/activate
```

**Python Version**: 3.11.9

**Key Packages**:
- torch==2.1.0
- transformers==4.35.0
- pandas==2.1.1
- numpy==1.24.3
- requests

**Purpose**: Run V2 BERT classification and NER models

**Models Available**:
- V2 BERT Classifier
- V2 BERT NER

**GPU**: Required for reasonable performance (CPU fallback available but slow)

---

### Environment 2: pycaret_env (PyCaret Metadata Classifier)

**Location**: `/Users/warren/development/GBC/inventory_2022/pycaret_env/`

**Activation**:
```bash
cd /Users/warren/development/GBC/inventory_2022
source pycaret_env/bin/activate
```

**Python Version**: 3.11.9

**Key Packages**:
- pycaret==3.0.4
- pandas==2.0.3
- lightgbm==4.0.0
- catboost==1.2

**Purpose**: Run PyCaret metadata-based classification

**Models Available**:
- PyCaret TEST_MODE=True (92 features)
- PyCaret TEST_MODE=False (112 features)

**CPU-only**: No GPU required, runs efficiently on CPU

**Critical Note**: Models backed up from `/tmp/` to `pycaret_models/` (see Model Paths below)

---

### Environment 3: spacy_hybrid_ner/venv/ (spaCy Hybrid NER)

**Location**: `/Users/warren/development/GBC/inventory_2022/spacy_hybrid_ner/venv/`

**Activation**:
```bash
cd /Users/warren/development/GBC/inventory_2022
source spacy_hybrid_ner/venv/bin/activate
```

**Python Version**: 3.11.9

**Key Packages**:
- spacy==3.7.0
- pandas==2.1.1
- numpy==1.24.3

**Purpose**: Run spaCy Hybrid NER (EntityRuler + Statistical NER with alias resolution)

**Models Available**:
- spaCy Hybrid NER (ner_hybrid_v1)

**CPU-only**: No GPU required, 100-200 papers/sec on CPU

---

## 🤖 Models

### 1. V2 BERT Classifier

**Location**: `out/classif_train_out/article_classifier_v2.pt`

**Size**: 476 MB

**Format**: PyTorch state dict

**Performance**:
- F1: 0.898
- Precision: 0.930
- Recall: 0.869

**Status**: ✅ Production Ready

**Environment**: biodata_modern_env

**Usage**:
```bash
python src/class_predict.py \
  -c out/classif_train_out/article_classifier_v2.pt \
  -i input.csv \
  -o output_dir/
```

---

### 2. V2 BERT NER

**Location**: `out/ner_train_out/named_entity_recognition_v2.pt`

**Size**: 473 MB

**Format**: PyTorch state dict

**Performance**:
- Validation F1: 0.749
- Test F1: 0.664
- Precision: 0.69
- Recall: 0.64

**Status**: ✅ Production Ready

**Environment**: biodata_modern_env

**Usage**:
```bash
python src/ner_predict.py \
  -c out/ner_train_out/named_entity_recognition_v2.pt \
  -i input.csv \
  -o output_dir/
```

---

### 3. PyCaret Metadata Classifier (TEST_MODE=True)

**Location**: `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl`

**Size**: 184 KB

**Format**: PyCaret pickle

**Features**: 92 metadata features

**Performance**:
- Recall: 84.6% (11/13 test papers)
- Precision: ~90%

**Status**: ✅ Verified

**Environment**: pycaret_env

**Backup Location**: `/tmp/pycaret_test/pycaret_metadata_classifier_v1.pkl` (original)

**Usage**:
```python
from pycaret.classification import load_model, predict_model
model = load_model('pycaret_models/test_mode_true/pycaret_metadata_classifier_v1')
predictions = predict_model(model, data=df)
```

---

### 4. PyCaret Metadata Classifier (TEST_MODE=False)

**Location**: `pycaret_models/test_mode_false/pycaret_metadata_classifier_v1.pkl`

**Size**: 271 KB

**Format**: PyCaret pickle

**Features**: 112 metadata features

**Performance**: Similar to TEST_MODE=True (more features, slightly different model)

**Status**: ✅ Verified

**Environment**: pycaret_env

**Backup Location**: `/tmp/pycaret_test_false/pycaret_metadata_classifier_v1.pkl` (original)

**Usage**: Same as TEST_MODE=True

---

### 5. spaCy Hybrid NER

**Location**: `spacy_hybrid_ner/models/ner_hybrid_v1/`

**Size**: ~50 MB

**Format**: spaCy model directory

**Performance**:
- Test F1: 79.62% (exceeded target by 14.6pp)
- Speed: 100-200 papers/sec (optimized batch processing)
- Previous validation (title-only): Precision 91%, Recall 48%
- Expected with abstracts: Recall 60-80%

**Status**: ✅ Production Ready (Phases 1-6 Complete)

**Environment**: spacy_hybrid_ner/venv/

**Usage**:
```python
from src.ner_predict_spacy import SpacyNERPredictor
predictor = SpacyNERPredictor('spacy_hybrid_ner/models/ner_hybrid_v1')
results = predictor.predict(papers_df, batch_size=32)
```

---

## 📚 Ground Truth Data

### Bioresource Papers Latest (Manual Curation)

**Location**: `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`

**⚠️ Note**: This file is OUTSIDE the project directory

**Size**: 4,560 curated papers

**Key Columns**:
- `publication_id` or `pubmed_id`: Paper identifier
- `title`: Paper title
- `abstract`: Paper abstract (if available)
- `resource_short_name`: Resource common name
- `resource_full_name`: Resource full name
- `is_global_core_biodata_resource`: Binary flag (1=global core, 0=other)

**Purpose**: Source for validation sample (50 global core + remainder for 125 unique resources)

**Quality**: High-quality manually curated data

**Usage**: Phase 1 sample selection (script 01)

---

## 🎓 Training Data (To Exclude)

### Classification Training Data

**Location**: `data/classif_splits_full/`

**Files**:
- `train_paper_classif.csv` - 1,111 papers (68.0%)
- `val_paper_classif.csv` - 239 papers (14.6%)
- `test_paper_classif.csv` - 240 papers (14.7%)

**Total**: 1,590 labeled papers

**Purpose**: IDs to EXCLUDE from validation sample to prevent data leakage

**Script Handles**: `01_select_validation_sample.py` automatically excludes these

---

### NER Training Data

**Location**: `data/ner_splits_full/`

**Files**:
- `train_ner.csv` / `train_ner.pkl` - 307 papers (66.0%)
- `val_ner.csv` / `val_ner.pkl` - 67 papers (14.4%)
- `test_ner.csv` / `test_ner.pkl` - 67 papers (14.4%)

**Total**: 441 annotated papers

**Purpose**: IDs to EXCLUDE from validation sample to prevent data leakage

**Script Handles**: `01_select_validation_sample.py` automatically excludes these

---

## 📊 Full Datasets

### V5.1 EPMC Query Results (2011-2021) ⭐

**Location**: `data/final_query_v5.1_2011_2021/query_results.csv`

**Size**: 284 MB

**Rows**: 157,192 papers

**Date Range**: 2011-01-01 to 2021-12-31

**Query Version**: V5.1 (wildcards fixed)

**Coverage**: 77.3% of training data captured

**Columns** (20 EPMC fields):
- Core: id, title, abstract, publication_date
- Binary flags: hasDbCrossReferences, hasData, hasSuppl, isOpenAccess, inPMC, inEPMC, hasPDF, hasBook
- Metrics: citedByCount, pubYear
- Rich metadata: pubType, keywords, meshTerms, journalTitle, journalISSN, authorAffiliations

**Purpose**: Full-scale dataset for Phase 2 validation

---

### Enhanced Metadata (38 Features)

**Location**: `data/metadata/features_engineered.csv`

**Size**: 48 MB

**Rows**: 21,612 papers

**Features**: 38 attributes (20 base + 18 engineered)

**Format**: CSV + PKL

**Purpose**: PyCaret feature engineering reference

**Columns**:
```
Base EPMC Metadata (20):
- id, title, abstract, publication_date
- hasDbCrossReferences, hasData, hasSuppl, isOpenAccess
- inPMC, inEPMC, hasPDF, hasBook
- citedByCount, pubYear, pubType
- keywords, meshTerms, journalTitle, journalISSN, authorAffiliations

Engineered Features (18):
- mesh_term_count, keyword_count, db_xref_present
- has_abstract, title_length, abstract_length
- access_score, data_availability_score
- publication_age, citations_per_year
- journal_features, author_features, etc.
```

---

### Combined Metadata (All Sources)

**Location**: `data/metadata/combined_v4_plus_missing.csv`

**Size**: 236 MB

**Rows**: 122,373 papers (deduplicated)

**Sources**:
- V4 query results
- V5 query results
- Manual additions
- Missing training papers

**Purpose**: Complete metadata repository for all known papers

---

### PyCaret Test Set (Ground Truth)

**Location**: `comparison_pycaret_v2/data/test_set_full.csv`

**Size**: 6.7 MB

**Rows**: 3,742 papers

**Labels**: 3,683 positives (98.4%), 59 negatives (1.6%)

**Features**: Full EPMC metadata (38 attributes)

**Purpose**: Model evaluation with ground truth labels

---

### High-Confidence Model Agreement

**Location**: `comparison_pycaret_v2/full_v5_comparison/all_three_agree_positive.csv`

**Size**: 1.0 MB

**Rows**: 8,129 papers (5.3% of dataset)

**Models**: All 3 models (V2, PyCaret-92, PyCaret-112) agree = bio-resource

**Purpose**: High-confidence training/validation set (gold standard)

---

## 🏃 Quick Commands

### Verify All Models Load

```bash
# From project root
cd /Users/warren/development/GBC/inventory_2022

# Test V2 models (biodata_modern_env)
source biodata_modern_env/bin/activate
python validation_spacy_v_BERT/scripts/00_verify_models.py

# Test PyCaret models (pycaret_env)
source pycaret_env/bin/activate
python -c "
from pycaret.classification import load_model
m1 = load_model('pycaret_models/test_mode_true/pycaret_metadata_classifier_v1')
m2 = load_model('pycaret_models/test_mode_false/pycaret_metadata_classifier_v1')
print(f'✓ TEST_MODE=True: {len(m1.feature_names_in_)} features')
print(f'✓ TEST_MODE=False: {len(m2.feature_names_in_)} features')
"

# Test spaCy model (spacy_hybrid_ner/venv/)
source spacy_hybrid_ner/venv/bin/activate
python -c "
import spacy
nlp = spacy.load('spacy_hybrid_ner/models/ner_hybrid_v1')
print(f'✓ spaCy model loaded: {nlp.meta[\"name\"]}')
"
```

---

### Check Data Sources

```bash
# Ground truth
ls -lh /Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv

# Full dataset
ls -lh data/final_query_v5.1_2011_2021/query_results.csv

# Metadata
ls -lh data/metadata/features_engineered.csv
ls -lh data/metadata/combined_v4_plus_missing.csv

# Training data (to exclude)
ls -lh data/classif_splits_full/train_paper_classif.csv
ls -lh data/ner_splits_full/train_ner.pkl
```

---

### Run Phase 1 Scripts

```bash
cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT

# Script 01: Select validation sample (125 unique resources)
python scripts/01_select_validation_sample.py

# Script 02: Fetch missing abstracts from EPMC
source ../biodata_modern_env/bin/activate
python scripts/02_fetch_abstracts.py

# Verify output
wc -l results/validation/sample/validation_sample_with_abstracts.csv
```

---

## 📍 Critical Paths Summary

### Project Root
```
/Users/warren/development/GBC/inventory_2022/
```

### Models (4 Total)
| Model | Path | Size | Environment |
|-------|------|------|-------------|
| V2 Classifier | `out/classif_train_out/article_classifier_v2.pt` | 476 MB | biodata_modern_env |
| V2 NER | `out/ner_train_out/named_entity_recognition_v2.pt` | 473 MB | biodata_modern_env |
| PyCaret (92) | `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl` | 184 KB | pycaret_env |
| PyCaret (112) | `pycaret_models/test_mode_false/pycaret_metadata_classifier_v1.pkl` | 271 KB | pycaret_env |
| spaCy Hybrid | `spacy_hybrid_ner/models/ner_hybrid_v1/` | ~50 MB | spacy_hybrid_ner/venv/ |

### Ground Truth (Outside Project)
```
/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv
```

### Training Data (To Exclude)
```
data/classif_splits_full/train_paper_classif.csv
data/ner_splits_full/train_ner.pkl
```

### Full Datasets
```
data/final_query_v5.1_2011_2021/query_results.csv (157k papers)
data/metadata/features_engineered.csv (21k papers, 38 features)
data/metadata/combined_v4_plus_missing.csv (122k papers)
comparison_pycaret_v2/data/test_set_full.csv (3.7k papers, ground truth)
comparison_pycaret_v2/full_v5_comparison/all_three_agree_positive.csv (8.1k papers, high confidence)
```

---

## 🔄 Validation Study Structure

### Phase 1 Outputs (This Study)
```
validation_spacy_v_BERT/
├── scripts/
│   ├── 01_select_validation_sample.py
│   ├── 02_fetch_abstracts.py
│   ├── 03a_run_v2_classification.py
│   ├── 03b_run_pycaret_classification.py
│   ├── 03c_compare_classifications.py
│   ├── 04a_run_v2_ner.py
│   ├── 04b_run_spacy_ner.py
│   ├── 04c_compare_ner.py
│   └── 05_generate_phase1_report.py
├── results/
│   └── validation/
│       ├── sample/
│       │   ├── validation_sample.csv
│       │   └── validation_sample_with_abstracts.csv
│       ├── classification/
│       │   ├── v2_classification_results.csv
│       │   ├── pycaret_test_true_results.csv
│       │   ├── pycaret_test_false_results.csv
│       │   └── classification_comparison.csv
│       └── ner/
│           ├── v2_ner_results.csv
│           ├── spacy_ner_results.csv
│           └── ner_comparison.csv
├── logs/
│   ├── 02_fetch_abstracts.log
│   ├── 03a_v2_classification.log
│   └── ...
└── CRITICAL_FILES_REFERENCE.md (this file)
```

---

## 📞 Support & References

**Full Documentation**:
- Main reference: `docs/starting_doc.md`
- Phase 0 setup: `plans/validation_spacy_v_BERT/PHASE0_SETUP_OVERVIEW.md`
- Phase 1 plan: `plans/validation_spacy_v_BERT/PHASE1_MANUAL_VALIDATION.md`
- Phase 2 plan: `plans/validation_spacy_v_BERT/PHASE2_FULL_SCALE.md`
- Data catalogue: `docs/DATA_CATALOGUE.md`
- Progress tracking: `plans/validation_spacy_v_BERT/PROGRESS.md`

**Model Specs**:
- `docs/TECHNICAL_SPECIFICATIONS.md`
- `docs/TRAINING_CHECKLIST.md`

**spaCy Hybrid NER**:
- `spacy_hybrid_ner/PHASE4_5_6_COMPLETE.md`
- `spacy_hybrid_ner/MANUAL_VALIDATION_STUDY_REPORT.md`

**PyCaret Comparison**:
- `docs/V2_PYCARET_COMPARISON_STUDY.md`
- `comparison_pycaret_v2/QUICK_START.md`

---

**Document Status**: ✅ Current and comprehensive
**Last Updated**: 2025-11-13
**Next Update**: After Phase 1 completion
**Maintained By**: Phase 1 validation study team
