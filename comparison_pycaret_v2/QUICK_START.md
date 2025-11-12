# V2 vs PyCaret Comparison - Quick Start Guide

## 📊 Key Results at a Glance

### Test Set (3,742 papers with ground truth)

| Model | F1 Score | Precision | Recall | Accuracy |
|-------|----------|-----------|--------|----------|
| **V2 BERT** | **98.9%** | 99.9% | 98.1% | 98.0% |
| PyCaret (92 feat) | 94.0% | 99.0% | 89.4% | 94.3% |
| PyCaret (112 feat) | 93.8% | 99.1% | 89.0% | 94.2% |

### Production Scale (153,180 unlabeled papers)

| Model | Bio-resource | % Positive | Speed | Size |
|-------|--------------|------------|-------|------|
| **V2 BERT** | 12,285 | **8.0%** | 133 p/s | 400 MB |
| PyCaret (92) | 52,630 | **34.4%** | 3,121 p/s | 184 KB |
| PyCaret (112) | 41,638 | **27.2%** | 2,088 p/s | 271 KB |

**Speed**: PyCaret is **20-30x faster** than V2
**Size**: PyCaret is **2,000x smaller** than V2

---

## 🎯 Key Findings

1. **V2 is CONSERVATIVE** (8% positive) - High precision, fewer positives
2. **PyCaret is SENSITIVE** (27-34% positive) - High recall, more positives
3. **High confidence set**: 8,129 papers where ALL 3 models agree = bio-resource
4. **Agreement gap**: Only 69-76% agreement between V2 and PyCaret on unlabeled data

---

## 📁 Important Files

### Results
\`\`\`
comparison_pycaret_v2/
├── evaluation/                          # Test set comparison
│   ├── performance_comparison.csv       # Metrics table
│   ├── metrics_comparison.png           # Visualizations
│   └── evaluation_summary.txt           # Full report
│
├── full_v5_comparison/                  # Production scale (153k)
│   ├── full_v5_merged_predictions.csv   # All 153k predictions
│   ├── all_three_agree_positive.csv     # 8,129 unanimous papers
│   ├── v2_yes_pycaret_no.csv            # 3,433 V2-only positives
│   ├── v2_no_pycaret_true_yes.csv       # 44,013 PyCaret-only
│   └── full_v5_comparison.png           # Visualizations
│
└── COMPARISON_COMPLETE_SUMMARY.md       # Full project summary
\`\`\`

### Google Colab Notebooks
\`\`\`
Google Drive: inventory_2022/comparison_pycaret_v2/notebooks/
├── 02_v2_classification.ipynb           # V2 on test set (3,742)
└── 03_v2_full_v5_classification.ipynb   # V2 on full V5.1 (153k)
\`\`\`

### Scripts
\`\`\`
comparison_pycaret_v2/scripts/
├── 01_prepare_data.py                   # Test set creation
├── 02_run_v2_locally.py                 # (Skip - use Colab)
├── 03_pycaret_prediction.py             # PyCaret test set
├── 03b_pycaret_full_v5.py              # PyCaret full V5.1
├── 04_performance_evaluation.py         # Test set metrics
└── 05_full_v5_comparison.py            # Full V5.1 comparison
\`\`\`

---

## 🚀 Quick Commands

### Run Test Set Evaluation
\`\`\`bash
python comparison_pycaret_v2/scripts/04_performance_evaluation.py
\`\`\`

### Run Full V5.1 Comparison
\`\`\`bash
python comparison_pycaret_v2/scripts/05_full_v5_comparison.py
\`\`\`

### View Results
\`\`\`bash
# Test set metrics
cat comparison_pycaret_v2/evaluation/evaluation_summary.txt

# Full V5.1 comparison
cat comparison_pycaret_v2/full_v5_comparison/full_v5_comparison_report.txt
\`\`\`

---

## 💡 Use Cases

### Use V2 BERT when:
✅ Maximum accuracy required
✅ GPU available
✅ Can afford 15-20 min inference
✅ High precision critical (minimize false positives)

### Use PyCaret when:
✅ Speed critical
✅ CPU-only environment
✅ Resource constraints
✅ High recall screening (catch more candidates)
✅ Model size matters (<300 KB vs 400 MB)

### Hybrid Approach:
1. **Stage 1**: PyCaret fast screening (27-34% pass)
2. **Stage 2**: V2 validation on PyCaret positives
3. **High confidence**: 8,129 papers with unanimous agreement

---

## 📈 Interesting Discoveries

### The "Gap"
- **44,013 papers** (28.7%) where PyCaret says YES but V2 says NO
- Represents fundamental difference in classification strategy
- Worth manual review to understand disagreement

### High Confidence Subset
- **8,129 papers** (5.3%) where all 3 models agree
- Likely genuine bio-resources
- Could be gold standard validation set

### Speed vs Accuracy Tradeoff
- V2: Best accuracy (98.9% F1), slowest (133 p/s), largest (400 MB)
- PyCaret: Good accuracy (94% F1), **23x faster**, **2000x smaller**
- Performance gap: Only 5% F1 difference for 23x speedup

---

## 🔍 Next Steps

1. **Manual review** of disagreement cases
2. **Validate** high-confidence unanimous subset
3. **Test** hybrid two-stage pipeline
4. **Monitor** agreement rates in production

---

## 📊 Summary Statistics

| Metric | Value |
|--------|-------|
| **Total papers analyzed** | 156,922 (3,742 test + 153,180 production) |
| **Models compared** | 3 |
| **Unanimous positives** | 8,129 (5.3%) |
| **V2-only positives** | 3,433 |
| **PyCaret-only positives** | 44,013 |
| **V2 accuracy** | 98.9% F1 on test set |
| **PyCaret accuracy** | 94.0% F1 on test set |
| **Speed improvement** | 20-30x (PyCaret vs V2) |
| **Size reduction** | 2,000x (PyCaret vs V2) |

---

**Status**: ✅ Project Complete
**Date**: 2025-11-12
**Key Insight**: Classification strategy (conservative vs sensitive) matters more than model architecture
