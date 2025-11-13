# Inventory Comparison Analysis (October 24, 2025)

**Purpose**: Comprehensive three-way comparison of inventory results to assess consistency, quality, and identify processing issues.

**Date**: October 24, 2025

**For Operational Guide**: See [`starting_doc.md`](starting_doc.md)
**For Pipeline Details**: See [`PIPELINE_GUIDES.md`](PIPELINE_GUIDES.md)

---

## Overview

Three-way comparison analysis performed on 2022 inventory rerun results to validate processing quality and identify discrepancies between local bash script execution and Google Colab execution.

---

## Comparison Tool

**Tool**: `compare_inventory_results.py` - Command-line script for comparing any two inventory CSV files

**Usage**:
```bash
python compare_inventory_results.py <file1> <file2> \
  -o <output_dir> \
  -n1 "<dataset1_name>" \
  -n2 "<dataset2_name>" \
  -t <probability_threshold>
```

**Features**:
- ✅ **Generic Comparison**: Works with any two inventory CSV files
- ✅ **Configurable Threshold**: Default 0.978 probability filtering
- ✅ **Resource-Level Matching**: Compares by (ID + best_name) combination
- ✅ **Two Output Files**: Summary metrics + detailed breakdown
- ✅ **Status Classification**: both_high_conf, unique_to_file1, unique_to_file2, prob_difference

---

## Analysis Results Summary

Three comparisons were performed on 2022 inventory rerun results:

### Comparison 1: Local Rerun vs Final Inventory ✅

**Files Compared**:
- Local: `inventory_classification_results/2025-10-22_2022_rerun/final_results/biodata_inventory_2022_rerun.csv`
- Baseline: `data/final_inventory_2022.csv`

**Results**:
- **82.09% resource overlap** (1,939 of 2,362 final inventory resources matched)
- Local rerun: 3,698 high-quality resources (avg prob 0.9968)
- Final inventory: 2,362 resources (manually verified)
- 1,759 additional resources discovered by local rerun
- Only 2 resources need review (probability differences)

**Assessment**: ✅ **EXCELLENT** - Local bash script rerun is production-ready

**Key Findings**:
- Very high average probabilities (>0.99)
- Identified 1,759 new resources beyond final inventory
- Strong agreement with manually verified data
- **RECOMMENDED FOR PRODUCTION USE**

---

### Comparison 2: Colab Rerun vs Final Inventory ⚠️

**Files Compared**:
- Colab: `collab_results/2025-10-24-s4985d_2022_rerun/final_inventory.csv`
- Baseline: `data/final_inventory_2022.csv`

**Results**:
- **0.64% resource overlap** (only 15 of 2,362 final inventory resources matched)
- Colab rerun: Only 29 resources passed 0.978 threshold (of 3,569 total)
- 99.2% of Colab predictions failed quality threshold
- Missing 99.4% of final inventory resources

**Assessment**: ❌ **CRITICAL ISSUE** - Colab rerun has probability calculation problem

**Key Findings**:
- Extremely low pass rate for quality threshold
- Probability calculation appears broken
- Most predictions have unexpectedly low confidence scores
- **DO NOT USE** until issue is resolved

---

### Comparison 3: Local Rerun vs Colab Rerun 🔍

**Files Compared**:
- Local: `inventory_classification_results/2025-10-22_2022_rerun/final_results/biodata_inventory_2022_rerun.csv`
- Colab: `collab_results/2025-10-24-s4985d_2022_rerun/final_inventory.csv`

**Results**:
- **96.55% agreement on high-confidence predictions** (28 of 29 Colab resources match Local)
- When Colab predictions are high-confidence, they align with local predictions
- Issue is not prediction accuracy but coverage/probability calculation

**Assessment**: 🔍 **CONFIRMS COLAB ISSUE** - Problem is probability scoring, not model quality

**Key Findings**:
- Confirms Colab accuracy is good when probabilities are high
- Issue is systematic probability calculation/extraction problem
- Likely causes to investigate:
  - Model loading issue
  - Tokenization problem
  - Probability extraction bug
  - Environment-specific numerical precision issue

---

## Generated Outputs

**Comparison Reports**:
- `inventory_classification_results/2025-10-22_2022_rerun/comparison/` - Local vs Final
- `collab_results/2025-10-24-s4985d_2022_rerun/comparison/` - Colab vs Final
- `comparison_local_vs_colab/` - Local vs Colab + COMPREHENSIVE_SUMMARY.md

**Each comparison includes**:
- `inventory_comparison_summary.csv` - High-level metrics and statistics
- `inventory_comparison_detailed.csv` - Row-by-row resource comparison with status

---

## Detailed Statistics

### Local Rerun Performance
- **Total Resources**: 3,698 (high-quality, >0.978 threshold)
- **Average Probability**: 0.9968
- **Overlap with Baseline**: 82.09% (1,939/2,362)
- **Unique Discoveries**: 1,759 new resources
- **Quality Issues**: 2 resources with probability differences

### Colab Rerun Issues
- **Total Resources**: 3,569 (total identified)
- **High-Quality Resources**: 29 (only 0.8% pass threshold)
- **Average Probability**: Significantly lower than expected
- **Overlap with Baseline**: 0.64% (15/2,362)
- **Missing Resources**: 2,347 of 2,362 baseline resources

### Cross-Platform Agreement
- **When Both High-Confidence**: 96.55% match rate (28/29)
- **Model Predictions**: Consistent when confidence is high
- **Confidence Scores**: Drastically different between platforms

---

## Recommendations

### Immediate Actions

1. ✅ **Use Local Rerun** for production inventory updates
   - 82% validated accuracy against manual baseline
   - High confidence scores (>0.99 average)
   - Discovers additional resources beyond baseline

2. 🔍 **Investigate Colab Issue** before using for production
   - Debug probability calculation/extraction
   - Verify model loading and tokenization
   - Check for environment-specific numerical issues

3. 📊 **Validation Standard**
   - Use `final_inventory_2022.csv` as quality benchmark
   - Expect >80% overlap for production-ready runs
   - Average probabilities should be >0.95 for high-quality results

4. 🔄 **Future Comparisons**
   - Use this tool to validate all new pipeline runs
   - Compare against both baseline and local rerun
   - Flag any runs with <50% overlap for investigation

### Quality Thresholds Established

**Production-Ready Criteria**:
- Average probability: >0.95
- Baseline overlap: >80%
- High-quality resources: >3,000
- Probability distribution: Most values >0.97

**Warning Signs**:
- Average probability: <0.80
- Baseline overlap: <50%
- High-quality resources: <1,000
- Widespread low confidence scores

---

## Resolution Update (October 28, 2025)

**Issue Resolved**: The Colab probability issue was traced to checkpoint corruption where URL extraction loaded cached data from a different run. See [`PYTORCH_CHECKPOINT_FIX.md`](PYTORCH_CHECKPOINT_FIX.md) (Addendum) for complete investigation.

**Solution**: Deprecated checkpoint functionality from rerun pipeline. Fresh Colab runs now produce correct probabilities matching local results.

---

## Tool Usage Examples

**Basic Comparison**:
```bash
python compare_inventory_results.py \
  inventory_classification_results/2025-10-22_2022_rerun/final_results/biodata_inventory_2022_rerun.csv \
  data/final_inventory_2022.csv \
  -o comparison_output/ \
  -n1 "Local Rerun 2025-10-22" \
  -n2 "Final Inventory 2022"
```

**Custom Threshold**:
```bash
python compare_inventory_results.py file1.csv file2.csv \
  -o output_dir/ \
  -t 0.95 \
  -n1 "Run A" \
  -n2 "Run B"
```

---

## Files Modified

**New Files**:
- `compare_inventory_results.py` - Generic inventory comparison tool
- `comparison_local_vs_colab/COMPREHENSIVE_SUMMARY.md` - Detailed analysis summary

**Updated Files**:
- `docs/starting_doc.md` - Added comparison analysis documentation
- `docs/INVENTORY_COMPARISON_ANALYSIS.md` - This document

---

**Document Status**: ✅ **CURRENT**
**Last Updated**: 2025-10-28
**Location**: `GBC/inventory_2022/docs/INVENTORY_COMPARISON_ANALYSIS.md`
