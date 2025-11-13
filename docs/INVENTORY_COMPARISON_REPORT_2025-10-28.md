# Inventory Results Comparison Report
**Date**: October 28, 2025
**Comparison Scope**: 3 rerun sessions + 1 baseline inventory

---

## Executive Summary

Three rerun sessions were executed on October 28, 2025, each producing different inventory results:

| Run | Session ID | Models | Mode | Records | High Confidence | Status |
|-----|-----------|--------|------|---------|-----------------|--------|
| **Full Run** | 2025-10-28-gl3fd6 | 2025-10-28-nzksic | Full | 3,592 | 22 | ✅ |
| **Old Model** | 2025-10-28-ulgfhi | 2025-10-24-apz1py | Full | 4,368 | 3,698 | ✅ |
| **Baseline** | final_inventory_2022 | N/A | N/A | 3,112 | 2,362 | ✅ |

**Key Finding**: The gl3fd6 full run produced significantly fewer high-confidence results (22) compared to the oldmodel run (3,698), despite using newer training models from 2025-10-28-nzksic. This suggests a substantial difference in model behavior or data quality issues.

---

## Detailed Comparison Results

### 1. Full Run (gl3fd6) vs Old Model (ulgfhi)

**Comparison Output**: `comparison_gl3fd6_vs_ulgfhi/`

#### Record Counts
- **Full Run (gl3fd6)**: 3,592 total records
  - After filtering (best_name_prob >= 0.978): **22 records**
- **Old Model (ulgfhi)**: 4,368 total records
  - After filtering (best_name_prob >= 0.978): **3,698 records**

#### Article-Level Analysis
| Metric | Value |
|--------|-------|
| Articles in gl3fd6 | 22 |
| Articles in ulgfhi | 3,698 |
| Overlapping articles | 20 |
| Unique to gl3fd6 | 2 |
| Unique to ulgfhi | 3,678 |
| Overlap % | 0.54% |

#### Resource-Level Analysis
| Metric | Value |
|--------|-------|
| Resources in gl3fd6 | 22 |
| Resources in ulgfhi | 3,698 |
| Overlapping resources | 20 |
| Unique to gl3fd6 | 2 |
| Unique to ulgfhi | 3,678 |
| Overlap % | 0.54% |

#### Probability Statistics
| Metric | gl3fd6 | ulgfhi |
|--------|--------|--------|
| Avg best_name_prob | 0.9838 | 0.9968 |
| Avg best_common_prob | 0.9838 | 0.9951 |

**Status Breakdown**:
- `both_high_conf`: 20 (matching between runs)
- `unique_to_gl3fd6`: 2 (new resources)
- `unique_to_ulgfhi`: 3,678 (old model found many more)

---

### 2. Full Run (gl3fd6) vs Baseline (final_inventory_2022)

**Comparison Output**: `comparison_gl3fd6_vs_baseline/`

#### Record Counts
- **Full Run (gl3fd6)**: 3,592 total → **22 high confidence**
- **Baseline**: 3,112 total → **2,362 high confidence**

#### Article-Level Analysis
| Metric | Value |
|--------|-------|
| Articles in gl3fd6 | 22 |
| Articles in baseline | 2,362 |
| Overlapping articles | 0 |
| Unique to gl3fd6 | 22 |
| Unique to baseline | 2,362 |
| Overlap % | 0.00% |

#### Resource-Level Analysis
| Metric | Value |
|--------|-------|
| Resources in gl3fd6 | 22 |
| Resources in baseline | 2,362 |
| Overlapping resources | 9 |
| Unique to gl3fd6 | 13 |
| Unique to baseline | 2,353 |
| Overlap % | 0.38% |

**Status Breakdown**:
- `both_high_conf`: 9 (matching with baseline)
- `unique_to_gl3fd6`: 13 (new)
- `unique_to_baseline`: 2,353 (original inventory)

---

### 3. Old Model (ulgfhi) vs Baseline (final_inventory_2022)

**Comparison Output**: `comparison_oldmodel_vs_baseline/`

#### Record Counts
- **Old Model (ulgfhi)**: 4,368 total → **3,698 high confidence**
- **Baseline**: 3,112 total → **2,362 high confidence**

#### Article-Level Analysis
| Metric | Value |
|--------|-------|
| Articles in ulgfhi | 3,698 |
| Articles in baseline | 2,362 |
| Overlapping articles | 0 |
| Unique to ulgfhi | 3,698 |
| Unique to baseline | 2,362 |
| Overlap % | 0.00% |

#### Resource-Level Analysis
| Metric | Value |
|--------|-------|
| Resources in ulgfhi | 3,698 |
| Resources in baseline | 2,362 |
| Overlapping resources | 1,939 |
| Unique to ulgfhi | 1,759 |
| Unique to baseline | 423 |
| **Overlap %** | **82.09%** |

**Key Finding**: 82% overlap at resource level indicates the old model had strong consistency with the baseline.

**Status Breakdown**:
- `both_high_conf`: 1,937
- `unique_to_ulgfhi`: 1,759
- `unique_to_baseline`: 423
- `final_low_conf`: 2

---

## Critical Findings

### 🚨 Data Quality Issue in gl3fd6 Run

The gl3fd6 full run shows severely degraded results compared to the oldmodel run:

1. **Filtering Collapse**:
   - gl3fd6: 3,592 records → 22 high confidence (0.61% pass rate)
   - ulgfhi: 4,368 records → 3,698 high confidence (84.7% pass rate)

2. **No Article-Level Match with Baseline**:
   - ulgfhi had 0% article overlap but 82% resource overlap with baseline
   - gl3fd6 has only 0.38% resource overlap with baseline

3. **Lower Average Confidence**:
   - gl3fd6: 0.9838 vs ulgfhi: 0.9968 (0.013 difference)
   - gl3fd6: 0.9838 vs baseline: 0.9933 (0.0095 difference)

### Potential Causes

The degradation in gl3fd6 could stem from:

1. **Model Quality**: Training session 2025-10-28-nzksic may have issues:
   - MD5 hashes show different models from the old training session (2025-10-24-apz1py)
   - Need to verify model training quality and performance metrics

2. **Data Processing**: The pipeline may have encountered issues with:
   - Classification predictions (higher false negatives)
   - NER extraction (missed database names)
   - Confidence scoring computation
   - Processing chains degradation

3. **Infrastructure/Environment**:
   - Google Colab GPU/memory issues
   - PyTorch version or library inconsistencies
   - Model loading/inference issues

---

## Recommendation

### Immediate Actions

1. **Investigate 2025-10-28-nzksic Models**:
   - Check training logs for performance metrics
   - Compare F1 scores vs previous sessions
   - Verify model checkpoints are complete and uncorrupted

2. **Validate Pipeline Execution**:
   - Examine classification_results.csv for prediction distribution
   - Check NER predictions for coverage
   - Review url_extraction_results.csv for extraction quality
   - Analyze processed_names_results.csv for name selection logic

3. **Data Quality Check**:
   - Compare raw classification predictions between ulgfhi and gl3fd6
   - Analyze confidence score distributions
   - Check for systematic differences in predictions

### Expected Baselines

For a production-quality rerun against a 21,677-paper dataset:
- **High-confidence resources**: 2,000-4,000 records
- **Average confidence**: > 0.99
- **Baseline overlap**: > 75-80% at resource level

The gl3fd6 run with only 22 high-confidence records falls far short of these expectations.

---

## Files Available for Review

### Comparison Results
- `comparison_gl3fd6_vs_ulgfhi/` - Full vs Old Model comparison
- `comparison_gl3fd6_vs_baseline/` - Full vs Baseline comparison
- `comparison_oldmodel_vs_baseline/` - Old Model vs Baseline comparison

Each contains:
- `inventory_comparison_summary.csv` - Key metrics
- `inventory_comparison_detailed.csv` - Detailed resource-by-resource comparison

### Raw Result Files
- `collab_results/2025-10-28-gl3fd6_2022_rerun/` - Full run results
- `collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/` - Old model run results
- `data/final_inventory_2022.csv` - Baseline inventory

---

## Next Steps

1. **Root Cause Analysis**: Investigate the 2025-10-28-nzksic training session
2. **Model Comparison**: Run diagnostic on both training sessions
3. **Pipeline Validation**: Check intermediate pipeline outputs
4. **Decision**:
   - If 2025-10-28-nzksic is broken → use oldmodel results
   - If pipeline issue → debug and rerun
   - If both valid → understand why they differ so much
