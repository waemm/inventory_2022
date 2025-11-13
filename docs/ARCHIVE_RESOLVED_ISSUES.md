# Archive of Resolved Issues

**Purpose**: Historical record of resolved technical issues and their solutions
**Status**: All issues documented here are ✅ RESOLVED and for reference only
**Last Updated**: 2025-11-13

---

## Table of Contents
- [Phase 4 Cartesian Product Bug (2025-11-05)](#phase-4-cartesian-product-bug-2025-11-05)
- [Phase 4 Training Notebooks Fixed (2025-11-07)](#phase-4-training-notebooks-fixed-2025-11-07)
- [Phase 4 Memory Overflow (2025-11-04)](#phase-4-memory-overflow-2025-11-04)
- [Entity Complexity Investigation (Phase 2 & 2B)](#entity-complexity-investigation-phase-2--2b)
- [PyTorch Compatibility (2025-10-27)](#pytorch-compatibility-2025-10-27)
- [Enhanced Metadata Features (2025-10-30)](#enhanced-metadata-features-2025-10-30)

---

## Phase 4 Cartesian Product Bug (2025-11-05)

**Status**: ✅ FIXED AND VERIFIED (Multiple Sessions)

### Issues Resolved

**1. Memory Overflow** (✅ FIXED - 2025-11-04):
- Reduced from 160GB+ → <10GB (94% reduction)
- Implemented slim results storage + chunked merge

**2. Cartesian Product Bug** (✅ FIXED - 2025-11-05):
- Expected: ~20,890 results
- Was producing: 288,736 results (13.8× multiplication)
- Root cause: Converting NaN to string 'nan' BEFORE merge caused pandas to match all 'nan' strings
- Fix: Filter NaN IDs FIRST using `.notna()`, THEN convert to string
- Verification: Sessions 1f3ixn & f649n1 both produce 20,896 results ✅

### Impact

✅ Phase 4 model is now PRODUCTION READY and VERIFIED for inference

### Documentation

- **Comprehensive bug fix**: [`docs/PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md`](PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md) ⭐ **READ THIS**
- Memory optimization: [`docs/MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md)
- Initial investigation: [`docs/PHASE4_INFERENCE_FIX_2025-11-04.md`](PHASE4_INFERENCE_FIX_2025-11-04.md)

---

## Phase 4 Training Notebooks Fixed (2025-11-07)

**Status**: ✅ PRODUCTION READY - All training bugs fixed, A100 optimized

### Issues Resolved

**1. 7 Critical Training Errors Fixed** (Errors #1-7):
- ✅ Syntax errors, missing modules, data source mismatches
- ✅ Pickle structure handling, JSON serialization
- ✅ Nested list handling in metrics (3 functions)
- ✅ AttributeError: `best_ner_f1` → `best_entity_f1`

**2. A100 GPU Optimizations Implemented**:
- ✅ Parallel data loading (8 workers, persistent) - 25-40% speedup
- ✅ Aggressive batch scaling (batch 128, LR 8e-5) - 100-150% speedup
- ✅ Auto-detection with T4/V100 fallback

**3. Agent Network Verification**:
- ✅ Explore Agent: Investigated trainer attributes
- ✅ Code-Developer Agent: Fixed 26 attribute references
- ✅ Code-Reviewer Agent: 100% verification (41 references checked)

### Training Results (Test run 2025-11-06)

- Duration: 27.7 minutes on A100 (aggressive batch scaling)
- Classification F1: 0.8513 ✅
- NER Entity F1: Saved in checkpoint (display crashed before fix)

### Two Optimized Notebooks Available

**1. phase4_multitask_training_FIXED.ipynb** (✅ uploaded to Drive)
- Aggressive batch scaling: ~30-45 min on A100
- High speedup, moderate risk (potential OOM)

**2. phase4_multitask_training_FIXED_A100opti.ipynb** (ready for upload)
- Parallel data loading: ~1.0-1.2 hours on A100
- Safe optimization, low risk

### Impact

Phase 4 training pipeline is now fully functional and ready for production training runs

### Comprehensive Documentation

- **⭐ Complete Implementation Guide**: [`docs/PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md`](PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md) - **Read this to get up to speed**
- **Attribute error fix**: [`ATTRIBUTE_ERROR_FIX_COMPLETE.md`](../ATTRIBUTE_ERROR_FIX_COMPLETE.md)
- **A100 optimizations**: [`A100_QUICK_START.md`](../A100_QUICK_START.md), [`A100_OPTIMIZATIONS_SUMMARY.md`](../A100_OPTIMIZATIONS_SUMMARY.md)
- **Bug fix history**: [`NOTEBOOK_FIX_ERROR6_COMPLETE.md`](../NOTEBOOK_FIX_ERROR6_COMPLETE.md)

---

## Phase 4 Memory Overflow (2025-11-04)

**Status**: ✅ FIXED - Memory reduced from 160GB+ to <10GB (94% reduction)

### Problem

Phase 4 inference notebook was attempting to load entire result dictionaries into memory, causing:
- Memory overflow on systems with <160GB RAM
- Colab crashes
- Unable to complete merge operations

### Solution

**1. Slim Results Storage**:
```python
# Before: Store full dicts (huge memory)
results = {'predictions': [...], 'scores': [...], 'entities': [...]}

# After: Store only IDs + predictions (minimal memory)
slim_results = {'pmid': [...], 'prediction': [...]}
```

**2. Chunked Merge**:
- Process results in chunks of 1000 papers
- Merge incrementally
- Clear memory after each chunk

**3. Efficient Data Types**:
- Use int64 for IDs (not string until needed)
- Filter NaN before conversion
- Drop unnecessary columns early

### Impact

- Memory usage: 160GB+ → <10GB (94% reduction)
- Enables inference on standard machines
- Colab compatible

### Documentation

- [`docs/MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md)

---

## Entity Complexity Investigation (Phase 2 & 2B)

**Status**: ✅ COMPLETE - 12 complexity levels tested (5% to 92%)
**Duration**: October 21 - November 3, 2025

### Key Finding

Split composition explains **80% of NER performance gap** to V2 baseline

### Executive Summary

Comprehensive investigation revealed that test set entity complexity significantly affects NER model performance, but the relationship is **more complex than expected**:

- **Split B (66% complexity)** achieved best performance: F1 = 0.7281 (vs current baseline 0.644)
- **Gap closure**: 80.1% (8.41 out of 10.5 percentage points to V2's 0.749)
- **Unexpected "valley"** at 55-60% complexity (worse than 28% complexity)
- **High-complexity plateau** at 80-92% performs nearly as well as Split B (avg F1 = 0.7240)
- **Split K2 (92%)** achieved F1 = 0.7273 (only 0.0008 behind Split B!)

### Key Results

| Split | Complexity | Val F1 | Performance Tier |
|-------|-----------|--------|------------------|
| **Split B** | 65.9% | **0.7281** | 🥇 Best |
| **Split K2** | 92.0% | **0.7273** | 🥈 Nearly tied |
| **Split E** | 83.9% | 0.7233 | 🥉 High plateau |
| Split J | 80.0% | 0.7215 | High plateau |
| Split D | 28.2% | 0.7165 | Mid-tier |
| Split G | 60.0% | 0.6950 | ⚠️ Valley (worse than 28%!) |
| Split F | 55.0% | 0.6975 | ⚠️ Valley |

### What This Means

1. **Split composition is critical** - explains 80% of performance difference
2. **Optimal complexity ~66%** BUT Split B may have benefited from lucky initialization
3. **High complexity (80-92%) is viable** - almost as good, potentially more stable
4. **Avoid 55-60% range** - unexpected performance valley
5. **Remaining 2.09 points to V2** require training procedure optimization

### Next Steps (Phase 3)

**Priority 1**: Validate Split B consistency with 5 random seeds (~40 GPU hours)
**Priority 2**: Test high-complexity plateau stability (~72 GPU hours)
**Priority 3**: Map the 55-60% performance valley (~56 GPU hours)
**Priority 4**: Hyperparameter optimization to close final 2.09 point gap (~120 GPU hours)

**Estimated timeline**: 5-7 weeks, ~288 GPU hours total

### Documentation

- **Phase 3 Work Plan**: [`docs/handover/PHASE3_WORK_PLAN.md`](handover/PHASE3_WORK_PLAN.md) ⭐ **Complete execution plan with all details**
- **Phase 2B Final Results**: [`docs/split_project/PHASE2B_FINAL_RESULTS.md`](split_project/PHASE2B_FINAL_RESULTS.md)
- **Phase 2 Results**: `PHASE2_COMPLETE_ANALYSIS.md`
- **Analysis Scripts**: `docs/split_project/analyze_phase2b_complete.py`
- **Data**: All 12 splits in `data/ner_splits_split{X}/`
- **Training Archives**: `collab_results/training_archives/2025-11-03-*_split*/`

---

## PyTorch Compatibility (2025-10-27)

**Status**: ✅ RESOLVED - Cross-platform models working

### Problem

V1 models saved with `torch.save(model, ...)` (entire object) were failing to load in different environments:
- PyTorch version mismatches
- CUDA availability differences
- Platform-specific serialization issues

### Solution

**V2 Models - Dict Format**:
```python
# Save only state dict + metadata
checkpoint = {
    'model_state_dict': model.state_dict(),
    'config': config_dict,
    'metadata': {...}
}
torch.save(checkpoint, path)

# Load anywhere
checkpoint = torch.load(path, map_location='cpu')
model.load_state_dict(checkpoint['model_state_dict'])
```

### Impact

- ✅ V2 models work on all platforms (local, Colab, different PyTorch versions)
- ✅ Forward compatible with PyTorch updates
- ✅ Can load on CPU even if saved on GPU

### Documentation

- [`PYTORCH_CHECKPOINT_FIX.md`](PYTORCH_CHECKPOINT_FIX.md)

---

## Enhanced Metadata Features (2025-10-30)

**Status**: ✅ COMPLETE - 21,392 papers × 38 features

### Achievement

Fetched comprehensive metadata from EuropePMC API to enrich papers with features for classification:

**Features Added**:
- Citation counts and metrics
- Publication types
- MeSH terms and keywords
- Journal information
- Access flags (Open Access, hasData, etc.)
- Grant information
- Author details

### Impact

- Enables PyCaret metadata-only classification
- Provides rich features for analysis
- Supports future metadata-based filtering

### Documentation

- [`ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md`](ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md)

---

## Summary Table - All Resolved Issues

| Issue | Date Resolved | Impact | Documentation |
|-------|--------------|--------|---------------|
| **Phase 4 Cartesian Product** | 2025-11-05 | 288k → 20k results (CRITICAL) | [PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md](PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md) |
| **Phase 4 Training Notebooks** | 2025-11-07 | 7 bugs fixed, A100 optimized | [PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md](PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md) |
| **Phase 4 Memory Overflow** | 2025-11-04 | 160GB → <10GB (94% reduction) | [MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md) |
| **Entity Complexity** | 2025-11-03 | 80% gap closure to V2 | [handover/PHASE3_WORK_PLAN.md](handover/PHASE3_WORK_PLAN.md) |
| **PyTorch Compatibility** | 2025-10-27 | Cross-platform models | [PYTORCH_CHECKPOINT_FIX.md](PYTORCH_CHECKPOINT_FIX.md) |
| **Enhanced Metadata** | 2025-10-30 | 38 features for 21k papers | [ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md](ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md) |

---

**Document Location**: `docs/ARCHIVE_RESOLVED_ISSUES.md`
**Last Updated**: 2025-11-13
**Note**: All issues in this archive are RESOLVED. For active issues, see `starting_doc.md`
