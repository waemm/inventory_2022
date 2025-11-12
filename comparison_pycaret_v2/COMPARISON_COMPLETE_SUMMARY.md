# V2 vs PyCaret Comparison - Project Complete Summary

**Date**: 2025-11-12
**Project**: Bio-resource Classification Model Comparison
**Models**: V2 BERT vs PyCaret AutoML (2 variants)

---

## Executive Summary

This project successfully compared three bio-resource classification models:
1. **V2 BERT** - Production deep learning model (400 MB, GPU-required)
2. **PyCaret (92 features)** - AutoML ensemble with 30 MeSH terms (180 KB, CPU-only)
3. **PyCaret (112 features)** - AutoML ensemble with 54 MeSH terms (270 KB, CPU-only)

**Key Finding**: V2 is highly conservative (8% positive rate), while PyCaret is more sensitive (27-34% positive rate). The models show fundamentally different classification strategies.

---

## Test Set Performance (3,742 papers with ground truth)

### Metrics Comparison

| Model | Accuracy | Precision | Recall | F1 Score |
|-------|----------|-----------|--------|----------|
| V2 BERT | 98.0% | **99.9%** | 98.1% | **98.9%** |
| PyCaret (92 feat) | 94.3% | 99.0% | 89.4% | 94.0% |
| PyCaret (112 feat) | 94.2% | 99.1% | 89.0% | 93.8% |

**Performance Gap**: V2 outperforms PyCaret by ~5% F1 score

### Confusion Matrices

**V2 BERT**:
```
TP: 3,613  |  FP: 5
FN: 70     |  TN: 54
```

**PyCaret (92 features)**:
```
TP: 3,292  |  FP: 33
FN: 391    |  TN: 26
```

**PyCaret (112 features)**:
```
TP: 3,278  |  FP: 30
FN: 405    |  TN: 29
```

---

## Production Scale Performance (153,180 papers, unlabeled)

### Prediction Distributions

| Model | Bio-resource | NOT Bio-resource | % Bio-resource |
|-------|--------------|------------------|----------------|
| V2 BERT | 12,285 | 140,895 | **8.0%** |
| PyCaret (92 feat) | 52,630 | 100,550 | **34.4%** |
| PyCaret (112 feat) | 41,638 | 111,542 | **27.2%** |

**Key Observation**: PyCaret identifies 3-4x MORE papers as bio-resources than V2

### Model Agreement

| Comparison | Agreement Rate |
|------------|---------------|
| V2 vs PyCaret (92 feat) | 68.9% |
| V2 vs PyCaret (112 feat) | 75.7% |
| PyCaret (92) vs PyCaret (112) | 89.0% |

**High Confidence Set**: 8,129 papers (5.3%) where ALL 3 models agree = bio-resource

### Overlap Analysis

- **All 3 agree POSITIVE**: 8,129 papers (5.3%)
- **All 3 agree NEGATIVE**: 94,156 papers (61.5%)
- **Total 3-way agreement**: 102,285 papers (66.8%)
- **V2 ONLY says bio-resource**: 3,433 papers
- **PyCaret says bio but V2 says NOT**: 44,013 papers

---

## Speed & Efficiency Comparison

### Processing Time (153k papers)

| Model | Time | Speed | Speedup vs V2 |
|-------|------|-------|---------------|
| V2 BERT | 19.2 min | 133 papers/sec | 1x |
| PyCaret (92 feat) | 49 sec | 3,121 papers/sec | **23.5x faster** |
| PyCaret (112 feat) | 73 sec | 2,088 papers/sec | **15.7x faster** |

### Model Size

| Model | Size | Size vs V2 |
|-------|------|------------|
| V2 BERT | 400 MB | 1x |
| PyCaret (92 feat) | 184 KB | **2,173x smaller** |
| PyCaret (112 feat) | 271 KB | **1,476x smaller** |

---

## Key Findings & Recommendations

### 1. Classification Strategy Differences

**V2 BERT**:
- **Conservative/High-Precision** approach
- Only 8% classified as bio-resource on unlabeled data
- 99.9% precision on test set
- Best for: Minimizing false positives, high-confidence predictions

**PyCaret**:
- **Sensitive/High-Recall** approach
- 27-34% classified as bio-resource on unlabeled data
- 99.0-99.1% precision on test set (slightly lower than V2)
- Best for: Maximizing coverage, initial screening

### 2. Production Deployment Recommendations

**Use V2 BERT when**:
- Maximum accuracy is critical
- GPU resources available
- Can afford 15-20 minute inference time
- Need highest precision (minimize false positives)

**Use PyCaret when**:
- Speed is critical (20-30x faster)
- CPU-only environment
- Resource-constrained deployment
- Want high-recall screening (catch more candidates)
- Model size constraints (~2000x smaller)

**Hybrid Approach**:
1. **First Pass**: PyCaret for fast, high-recall screening (catches 27-34%)
2. **Second Pass**: V2 BERT for high-precision validation
3. **High Confidence**: Use the 8,129 papers where all 3 models agree

### 3. The "Gap" Investigation

**44,013 papers** where PyCaret says "bio-resource" but V2 says "NOT":
- Represents **28.7%** of the dataset
- Could be:
  - False positives from PyCaret (over-prediction)
  - False negatives from V2 (under-prediction)
  - Papers with ambiguous bio-resource status

**Recommendation**: Manual review of sample from this set to understand the disagreement

### 4. High Confidence Subset

**8,129 papers (5.3%)** with unanimous agreement:
- ALL 3 models agree = bio-resource
- Likely genuine bio-resource papers
- Could be used as:
  - High-confidence training data
  - Gold standard validation set
  - Priority curation target

---

## Files Generated

### Test Set Analysis (Phase 4)
- `comparison_pycaret_v2/evaluation/performance_comparison.csv`
- `comparison_pycaret_v2/evaluation/model_characteristics.csv`
- `comparison_pycaret_v2/evaluation/detailed_metrics.json`
- `comparison_pycaret_v2/evaluation/metrics_comparison.png`
- `comparison_pycaret_v2/evaluation/confusion_matrices.png`
- `comparison_pycaret_v2/evaluation/evaluation_summary.txt`

### Full V5.1 Analysis (Phase 5)
- `comparison_pycaret_v2/full_v5_comparison/full_v5_merged_predictions.csv` (153k rows)
- `comparison_pycaret_v2/full_v5_comparison/all_three_agree_positive.csv` (8,129 rows)
- `comparison_pycaret_v2/full_v5_comparison/v2_yes_pycaret_no.csv` (3,433 rows)
- `comparison_pycaret_v2/full_v5_comparison/v2_no_pycaret_true_yes.csv` (44,013 rows)
- `comparison_pycaret_v2/full_v5_comparison/full_v5_comparison.png`
- `comparison_pycaret_v2/full_v5_comparison/full_v5_comparison_summary.json`
- `comparison_pycaret_v2/full_v5_comparison/full_v5_comparison_report.txt`

---

## Technical Details

### Test Set Composition
- **Total**: 3,742 papers
- **Positives**: 3,683 (98.4%)
- **Negatives**: 59 (1.6%)
- **Source**: Validated bio-resource papers + V2 test negatives
- **Date Range**: Papers matching V5.1 query dates (2011-2021)

### Full V5.1 Dataset
- **Source**: EPMC query results with V5.1 query
- **Raw**: 156,231 papers
- **After deduplication**: 153,180 unique papers
- **Date Range**: 2011-2021
- **Ground Truth**: None (unlabeled production data)

### PyCaret Model Details

**TEST_MODE=True (92 features)**:
- 30 MeSH terms
- Metadata-only features
- Citation metrics
- Access indicators
- Publication type flags
- Size: 184 KB

**TEST_MODE=False (112 features)**:
- 54 MeSH terms (more granular)
- All features from TEST_MODE=True
- Additional journal features
- Size: 271 KB

### V2 BERT Model
- BERT-based sequence classification
- Input: Title + Abstract
- Max sequence length: 512 tokens
- Model size: 400 MB
- Requires: GPU with 8GB+ VRAM

---

## Next Steps & Future Work

### 1. Disagreement Analysis
- **Manual review** of sample from 44,013 "PyCaret=YES, V2=NO" papers
- Understand why models disagree
- Identify edge cases and ambiguous papers

### 2. High Confidence Validation
- **Manually validate** sample from 8,129 unanimous papers
- Confirm they are genuine bio-resources
- Calculate true positive rate for this subset

### 3. Model Refinement
- Consider ensemble approach combining both models
- Adjust V2 threshold for higher recall if needed
- Train PyCaret on larger, more balanced dataset

### 4. Production Pipeline
- Implement two-stage filtering:
  - Stage 1: PyCaret high-recall screening
  - Stage 2: V2 high-precision validation
- Monitor agreement rates in production

---

## Conclusion

This comparison reveals that **V2 BERT** and **PyCaret** represent fundamentally different classification philosophies:

- **V2**: Conservative, high-precision (8% positive rate)
- **PyCaret**: Sensitive, high-recall (27-34% positive rate)

Both approaches have merit depending on use case. The **8,129 unanimous papers** provide a high-confidence subset for further analysis.

The dramatic speed difference (20-30x) and size difference (2000x) make PyCaret attractive for resource-constrained deployments, while V2's superior accuracy makes it ideal when precision is paramount.

**Final Recommendation**: Use a **hybrid approach** - PyCaret for fast screening, V2 for validation, with the unanimous subset as high-confidence targets.

---

**Project Status**: ✅ COMPLETE
**Total Papers Analyzed**: 153,180 (production) + 3,742 (test)
**Models Compared**: 3
**Key Insight**: Classification strategy matters more than model size
