# PyCaret vs V2 Classification Comparison

**Created**: 2025-11-11
**Status**: 🚧 IN PROGRESS
**Priority**: Accuracy over speed

---

## Overview

Comprehensive comparison of two fundamentally different approaches to bio-resource paper classification:
- **V2 Model**: BERT-based classifier using full text (title + abstract)
- **PyCaret Models**: AutoML ensemble using metadata features only

**Test Dataset**: V5.1 query results (156,231 papers from 2011-2021)
**Clean Test Set**: 3,329 papers with ground truth (257 positive, 3,072 negative)
**Training Overlap**: 0 papers (verified clean)

---

## Project Structure

```
comparison_pycaret_v2/
├── README.md                           # This file
├── QUICK_START.md                      # Step-by-step execution guide
├── data/                               # Prepared datasets
│   ├── test_set_full.csv               # 3,329 papers (clean test set)
│   ├── test_set_sample.csv             # 200 papers for testing
│   └── unlabeled_set.csv               # ~149K papers without labels
├── v2_predictions/                     # V2 model outputs
├── pycaret_predictions/                # PyCaret model outputs
├── results/                            # Analysis results
├── figures/                            # Visualizations
├── notebooks/                          # Execution notebooks
│   ├── 02_v2_classification.ipynb      # V2 inference (Google Colab)
│   ├── 03_pycaret_prediction.ipynb     # PyCaret inference (Local)
│   ├── 04_performance_evaluation.ipynb # Metrics & comparison (Local)
│   └── 05_disagreement_analysis.ipynb  # Disagreement patterns (Local)
└── scripts/                            # Python scripts
    ├── 01_prepare_data_v2.py           # Data preparation (independent test set)
    └── 01_prepare_data.py              # Original (deprecated - had leakage)
```

---

## Progress Tracker

### Phase 1: Data Preparation ✅ COMPLETE
- [x] Load V5.1 query data
- [x] Merge with ground truth labels (bioresource_papers.csv)
- [x] Create clean test set (3,329 papers, 0 training overlap)
- [x] Validate data quality

### Phase 2: V2 Model Inference ✅ COMPLETE
- [x] Create V2 classification notebook
- [ ] Run V2 inference on test set (Google Colab)
- [ ] Download results from Drive

### Phase 3: PyCaret Inference ✅ NOTEBOOK READY
- [x] Create PyCaret prediction notebook
- [ ] Run on test set (local execution)
- [ ] Extract predictions with confidence scores

### Phase 4: Performance Evaluation ✅ NOTEBOOK READY
- [x] Create evaluation notebook
- [ ] Calculate metrics (precision, recall, F1)
- [ ] Statistical significance testing
- [ ] Create confusion matrices

### Phase 5: Disagreement Analysis ✅ NOTEBOOK READY
- [x] Create disagreement analysis notebook
- [ ] Identify disagreement cases
- [ ] Analyze failure patterns
- [ ] Confidence score analysis

### Phase 6: Speed Comparison ⏳ PENDING
- [ ] Measure inference time
- [ ] Resource usage analysis
- [ ] Scalability projections

### Phase 7: Hybrid Pipeline ⏳ PENDING
- [ ] Design confidence-based routing
- [ ] Test different thresholds
- [ ] Optimize for accuracy

### Phase 8: Final Report ⏳ PENDING
- [ ] Comprehensive report
- [ ] Executive summary
- [ ] Visualizations

---

## Quick Start

**Phase 1 - Data Preparation** (COMPLETED):
```bash
python scripts/01_prepare_data_v2.py
```

**Phase 2 - V2 Inference** (Google Colab):
1. Upload `notebooks/02_v2_classification.ipynb` to Google Colab
2. Enable GPU runtime (Runtime > Change runtime type > GPU)
3. Run all cells (~3-5 minutes for full test set)
4. Download `comparison_pycaret_v2/v2_predictions/v2_classification_results.csv` from Drive

**Phase 3 - PyCaret Inference** (Local):
```bash
source pycaret_env/bin/activate
python scripts/03_pycaret_prediction.py
```

---

## Key Files

**Plan**: `../plans/2025-11-11_pycaret_vs_v2_classification_comparison.md`
**Data Source**: `../data/final_query_v5.1_2011_2021/query_results.csv`
**Ground Truth**: `GBC/gbc-publication-analysis/bioresource_papers.csv` (independent test set)
**Models**:
- V2: `out/original_model/article_classifier_v2.pt` (Google Drive)
- PyCaret TEST=True: `/tmp/pycaret_test/pycaret_metadata_classifier_v1.pkl`
- PyCaret TEST=False: `/tmp/pycaret_test_false/pycaret_metadata_classifier_v1.pkl`

---

## Current Status

**Last Updated**: 2025-11-11
**Phase**: All Notebooks Created (Ready for Execution)
**Next Action**: See `QUICK_START.md` for parallel execution guide

---

See `../plans/2025-11-11_pycaret_vs_v2_classification_comparison.md` for complete plan.
