# Test Split Evaluation: V2 vs Phase 4 NER Systems

## Overview

- **Test Split Size**: 63 papers with ground truth
- **Evaluation Date**: 2025-11-05
- **Matching Strategy**: Exact match (case-insensitive)

## Aggregate Metrics

### Micro-Averaged F1 Scores

| System | Precision | Recall | F1 | TP | FP | FN |
|--------|-----------|--------|----|----|----|----|
| V2 | 0.6034 | 0.7368 | 0.6635 | 70 | 46 | 25 |
| Phase4 Raw | 0.1818 | 0.2947 | 0.2249 | 28 | 126 | 67 |
| Phase4 Cleaned | 0.1818 | 0.2947 | 0.2249 | 28 | 126 | 67 |

### Macro-Averaged F1 Scores (with 95% CI)

| System | Mean F1 | Std Dev | 95% CI |
|--------|---------|---------|--------|
| V2 | 0.6803 | 0.3750 | [0.5884, 0.7700] |
| Phase4 Raw | 0.4095 | 0.4795 | [0.2937, 0.5270] |
| Phase4 Cleaned | 0.4095 | 0.4795 | [0.2968, 0.5286] |

## Statistical Significance

### Phase 4 Cleaned vs V2

**McNemar's Test:**
- Statistic: 18.8929
- P-value: 0.0000
- Significant: Yes (α=0.05)
- Both correct: 26
- Both incorrect: 9
- phase4_cleaned only: 2
- v2 only: 26

**F1 Difference (Bootstrap 95% CI):**
- Mean: -0.2708
- CI: [-0.3950, -0.1502]

### Phase 4 Cleaned vs Raw

**McNemar's Test:**
- Statistic: 0.0000
- P-value: 1.0000
- Significant: No (α=0.05)
- Both correct: 28
- Both incorrect: 35
- phase4_cleaned only: 0
- phase4_raw only: 0

**F1 Difference (Bootstrap 95% CI):**
- Mean: 0.0000
- CI: [0.0000, 0.0000]

### Phase 4 Raw vs V2

**McNemar's Test:**
- Statistic: 18.8929
- P-value: 0.0000
- Significant: Yes (α=0.05)
- Both correct: 26
- Both incorrect: 9
- phase4_raw only: 2
- v2 only: 26

**F1 Difference (Bootstrap 95% CI):**
- Mean: -0.2708
- CI: [-0.3950, -0.1502]

## Per-Paper Performance Distribution

### V2
- Mean F1: 0.6803
- Median F1: 0.8000
- Min F1: 0.0000
- Max F1: 1.0000
- Papers with F1 > 0.8: 29 (46.0%)
- Papers with F1 > 0.5: 44 (69.8%)

### Phase4 Raw
- Mean F1: 0.4095
- Median F1: 0.0000
- Min F1: 0.0000
- Max F1: 1.0000
- Papers with F1 > 0.8: 24 (38.1%)
- Papers with F1 > 0.5: 24 (38.1%)

### Phase4 Cleaned
- Mean F1: 0.4095
- Median F1: 0.0000
- Min F1: 0.0000
- Max F1: 1.0000
- Papers with F1 > 0.8: 24 (38.1%)
- Papers with F1 > 0.5: 24 (38.1%)
