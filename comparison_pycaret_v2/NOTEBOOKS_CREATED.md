# All Notebooks Created - Ready for Execution

**Date**: 2025-11-11
**Status**: ✅ ALL NOTEBOOKS READY

---

## Summary

All comparison notebooks have been created and are ready for parallel execution. You can now run all phases simultaneously to minimize total time.

---

## Created Notebooks

### ✅ Phase 2: V2 Classification (Google Colab)
**File**: `notebooks/02_v2_classification.ipynb`
- Simplified classification-only pipeline
- GPU-accelerated inference
- Input validation for test_set_full.csv
- Outputs predictions with confidence scores
- **Runtime**: ~3-5 minutes (3,329 papers)

**Key Features**:
- Validates input format (id, title, abstract)
- Verifies ground truth column
- Calculates quick metrics (accuracy, precision, recall, F1)
- Generates confusion matrix
- Saves configuration for traceability

### ✅ Phase 3: PyCaret Prediction (Local)
**File**: `notebooks/03_pycaret_prediction.ipynb`
- Replicates exact training feature engineering
- Supports both TEST_MODE models
- Auto-detects available models
- Runs predictions on clean test set
- **Runtime**: ~5-6 minutes (both models)

**Key Features**:
- Feature engineering function (91/111 features depending on model)
- MeSH term encoding (30 or 50 terms)
- Target encoding with smoothing
- Journal and publication type features
- Citation, access, and temporal features

### ✅ Phase 4: Performance Evaluation (Local)
**File**: `notebooks/04_performance_evaluation.ipynb`
- Comprehensive metrics comparison
- Statistical significance testing
- Visualization generation
- **Runtime**: ~2-3 minutes

**Outputs**:
- Metrics CSV (accuracy, precision, recall, F1)
- Confusion matrices (visual)
- McNemar's test results
- Confidence score analysis
- Performance comparison charts
- Evaluation report (markdown)

### ✅ Phase 5: Disagreement Analysis (Local)
**File**: `notebooks/05_disagreement_analysis.ipynb`
- Identifies disagreement patterns
- Analyzes model complementarity
- Exports specific disagreement cases
- **Runtime**: ~2-3 minutes

**Outputs**:
- Disagreement categories (both correct, V2 only, PyCaret only, both wrong)
- Pattern analysis by category
- Confidence score scatter plots
- Disagreement case exports (CSV)
- Disagreement report (markdown)

---

## Execution Strategies

### Strategy 1: Parallel Execution (FASTEST - ~10 minutes total)

```bash
# Terminal 1: Start V2 inference in Colab
# Upload 02_v2_classification.ipynb → Run all cells

# Terminal 2: Start PyCaret inference (local)
cd /Users/warren/development/GBC/inventory_2022/comparison_pycaret_v2
source ../../pycaret_env/bin/activate
jupyter notebook notebooks/03_pycaret_prediction.ipynb
# Run all cells

# Wait for both to complete (~5 minutes each)

# Terminal 3: Run analysis notebooks (sequential)
jupyter notebook notebooks/04_performance_evaluation.ipynb
# Wait to complete, then:
jupyter notebook notebooks/05_disagreement_analysis.ipynb
```

### Strategy 2: Sequential Execution (SAFEST - ~15 minutes total)

```bash
# 1. V2 inference (Colab) - ~5 min
# 2. Download V2 results
# 3. PyCaret inference (local) - ~5 min
# 4. Performance evaluation (local) - ~3 min
# 5. Disagreement analysis (local) - ~2 min
```

---

## Prerequisites Checklist

Before running notebooks:

**Data Preparation** (Phase 1):
- [x] `data/test_set_full.csv` exists (3,329 papers)
- [x] `data/test_set_sample.csv` exists (200 papers)
- [x] 0 training data overlap verified

**V2 Model** (Phase 2):
- [ ] Google Colab account
- [ ] GPU runtime enabled
- [ ] V2 model on Drive: `out/original_model/article_classifier_v2.pt`

**PyCaret Models** (Phase 3):
- [ ] PyCaret environment activated
- [ ] Model(s) trained and saved:
  - [ ] `/tmp/pycaret_test/pycaret_metadata_classifier_v1.pkl` (TEST_MODE=True)
  - [ ] `/tmp/pycaret_test_false/pycaret_metadata_classifier_v1.pkl` (TEST_MODE=False)
- [ ] V5.1 metadata available: `data/final_query_v5.1_2011_2021/query_results.csv`

**Analysis** (Phases 4-5):
- [ ] Python libraries: matplotlib, seaborn, scikit-learn, scipy
- [ ] Sufficient disk space for results and figures

---

## Expected Outputs

After running all notebooks:

### Files Created

```
comparison_pycaret_v2/
├── v2_predictions/
│   ├── v2_classification_results.csv      # V2 predictions + ground truth
│   └── v2_classification_config.json      # V2 configuration
│
├── pycaret_predictions/
│   ├── pycaret_TEST_MODE_True_results.csv  # PyCaret predictions
│   ├── pycaret_TEST_MODE_False_results.csv # (if model exists)
│   └── pycaret_prediction_summary.json     # Summary
│
├── results/
│   ├── metrics_comparison.csv             # All model metrics
│   ├── mcnemar_tests.csv                  # Statistical tests
│   ├── evaluation_report.md               # Phase 4 summary
│   ├── disagreement_patterns.csv          # Pattern analysis
│   ├── disagreement_v2_only_correct.csv   # V2 wins
│   ├── disagreement_pycaret_only_correct.csv # PyCaret wins
│   ├── disagreement_both_wrong.csv        # Hard cases
│   └── disagreement_report.md             # Phase 5 summary
│
└── figures/
    ├── confusion_matrices.png             # Side-by-side matrices
    ├── metrics_comparison.png             # Bar charts
    ├── confidence_analysis.png            # Score distributions
    ├── disagreement_categories.png        # Pie + bar charts
    └── confidence_scatter_by_category.png # Scatter plots
```

### Key Insights You'll Get

1. **Overall Performance**: Which model performs better on independent test set?
2. **Metric Breakdown**: Precision, recall, F1, accuracy for each model
3. **Statistical Significance**: Are differences statistically significant?
4. **Complementarity**: Do models make different types of errors?
5. **Failure Modes**: What types of papers does each model struggle with?
6. **Confidence Patterns**: How confident are models when correct vs incorrect?
7. **Hard Cases**: Which papers are hardest to classify (both wrong)?
8. **Routing Opportunities**: Can we identify rules for hybrid approach?

---

## Next Steps After Execution

1. **Review Results**:
   - Read `results/evaluation_report.md`
   - Read `results/disagreement_report.md`
   - Examine figures in `figures/`

2. **Analyze Findings**:
   - Compare F1 scores
   - Review disagreement patterns
   - Identify complementary strengths

3. **Make Decision**:
   - Choose best single model, OR
   - Design hybrid approach, OR
   - Identify areas for improvement

4. **Optional Phase 6-8**:
   - Speed comparison (if performance is close)
   - Hybrid pipeline design (if models are complementary)
   - Final comprehensive report

---

## Troubleshooting

### Common Issues

**Q: V2 notebook can't find model**
A: Ensure model uploaded to Drive at: `inventory_2022/out/original_model/article_classifier_v2.pt`

**Q: PyCaret notebook fails with "model not found"**
A: Train PyCaret models first using `pycaret_metadata_training.ipynb`

**Q: Feature engineering errors in PyCaret**
A: Verify V5.1 metadata exists: `data/final_query_v5.1_2011_2021/query_results.csv`

**Q: Analysis notebooks show "predictions not found"**
A: Run Phase 2 and 3 first, ensure CSV files exist in prediction directories

**Q: Matplotlib/seaborn errors**
A: Install visualization libraries:
```bash
pip install matplotlib seaborn scikit-learn scipy
```

---

## Success Criteria

After running all notebooks, you should have:

- ✅ Predictions from V2 model (3,329 papers)
- ✅ Predictions from PyCaret model(s) (3,329 papers)
- ✅ Comprehensive metrics for all models
- ✅ Statistical significance tests
- ✅ Disagreement analysis with specific cases
- ✅ Multiple visualizations (5+ figures)
- ✅ Two summary reports (evaluation + disagreement)

**Total Files Created**: 15+ files (predictions, metrics, reports, figures)
**Total Runtime**: 10-15 minutes (parallel execution)

---

## What's Next?

After completing all notebooks:

1. **Review the reports** in `results/` directory
2. **Examine the figures** in `figures/` directory
3. **Make an informed decision** about which approach to use
4. **Consider hybrid strategies** if models show complementary strengths

For detailed instructions, see: `QUICK_START.md`

---

**You're ready to run! All notebooks are created and waiting for execution.**

Start with `QUICK_START.md` for the fastest parallel execution strategy.
