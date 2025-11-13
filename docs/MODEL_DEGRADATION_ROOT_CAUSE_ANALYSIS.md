# Model Degradation Root Cause Analysis
**Date**: 2025-10-29
**Status**: 🔴 ROOT CAUSE IDENTIFIED
**Severity**: CRITICAL - Training Quality Issue

---

## Executive Summary

The newly trained models from session **2025-10-28-nzksic** produce **99.4% fewer high-confidence predictions** than the validated old models (2025-10-24-apz1py). After comprehensive investigation including model comparison, checkpoint analysis, and training metrics review, the root cause has been identified:

**ROOT CAUSE**: **Poor NER Model Training Quality**

The NEW NER model achieved only **F1=0.653** on the test set, compared to the expected **F1=0.749** for production models. This 12.8% performance drop causes systematically lower confidence scores, resulting in catastrophic filtering failure.

---

## Investigation Summary

### Models Compared

| Model Set | Session ID | Environment | Status |
|-----------|-----------|-------------|--------|
| **OLD (Working)** | 2025-10-24-apz1py | Local PyTorch 2.0.0 | ✅ Validated |
| **NEW (Degraded)** | 2025-10-28-nzksic | Colab PyTorch 2.8.0 | ❌ Poor Performance |

### Checksums

| Model | OLD MD5 | NEW MD5 | Match? |
|-------|---------|---------|--------|
| Classification | `a496eae1d5cf343ae509bcbc7e3f400e` | `992a1381f7b507c72286d88d2582945d` | ❌ Different |
| NER | `37eebc38463a90c43cc36ee8ee1f4aa3` | `752cfaa0711d414269c7d22e2c6d1bf5` | ❌ Different |

**Confirmed**: These are completely different models, not corrupted versions.

---

## Key Findings

### 1. ✅ Checkpoint Format is CORRECT

**Previous Issue (Oct 2025)**: PyTorch checkpoint corruption due to NamedTuple objects
**Current Status**: ✅ RESOLVED

**Evidence**:
```
OLD Models:
  train_metrics: Metrics (NamedTuple - problematic)
  val_metrics: Metrics (NamedTuple - problematic)

NEW Models:
  train_metrics: dict (correct format!)
  val_metrics: dict (correct format!)
```

**Conclusion**: The NEW models use the corrected checkpoint format. This is NOT a PyTorch incompatibility issue.

---

### 2. ✅ Model Architecture is IDENTICAL

**Evidence**:
```
Classification Model:
  OLD parameters: 124,647,170
  NEW parameters: 124,647,170
  ✓ MATCH

NER Model:
  OLD output labels: 5 (O, B-COM, I-COM, B-FUL, I-FUL)
  NEW output labels: 5 (same schema)
  ✓ MATCH
```

**Note**: The model manifest incorrectly claims 3 labels, but the actual model has 5 labels matching the old schema.

**Conclusion**: Model architectures are identical. The problem is NOT structural.

---

### 3. 🔴 TRAINING PERFORMANCE IS DEGRADED

#### Classification Model: Acceptable

| Metric | OLD (Expected) | NEW (Actual) | Status |
|--------|----------------|--------------|--------|
| **Test F1** | 0.898 | 0.859 | ⚠️ Slight drop (4.3%) |
| **Test Precision** | 0.930 | 0.928 | ✓ Similar |
| **Test Recall** | 0.869 | 0.800 | ⚠️ Moderate drop (7.9%) |

#### NER Model: SEVERELY DEGRADED

| Metric | OLD (Expected) | NEW (Actual) | Status |
|--------|----------------|--------------|--------|
| **Test F1** | 0.749 | **0.653** | 🔴 **CRITICAL (-12.8%)** |
| **Test Precision** | 0.779 | 0.674 | 🔴 Major drop (-13.5%) |
| **Test Recall** | 0.722 | 0.632 | 🔴 Major drop (-12.5%) |

**Training Progression Analysis**:

**NEW NER Model Training (from training_stats.csv)**:
```
Epoch 0: Val F1=0.459
Epoch 1: Val F1=0.575
Epoch 2: Val F1=0.592
Epoch 3: Val F1=0.606
Epoch 4: Val F1=0.640
Epoch 5: Val F1=0.580 ← Decline!
Epoch 6: Val F1=0.633
Epoch 7: Val F1=0.591
Epoch 8: Val F1=0.613
Epoch 9: Val F1=0.621 ← Final
```

**Problem Indicators**:
1. **Peak at Epoch 4** (F1=0.640), then decline
2. **Unstable training**: F1 bounces between 0.58-0.64
3. **No convergence**: Still fluctuating at epoch 9
4. **Final performance**: F1=0.621 (validation), F1=0.653 (test)

**Expected Pattern** (from old models):
- Steady improvement across epochs
- Convergence to F1~0.75 by epoch 9
- Stable performance in later epochs

---

### 4. 🔴 PRODUCTION IMPACT: Probability Collapse

The poor NER training directly causes the production failure:

#### Probability Distribution Comparison

| Threshold | OLD (Working) | NEW (Degraded) | Loss |
|-----------|---------------|----------------|------|
| **≥ 0.978** | 3,698 (84.7%) | **22 (0.6%)** | **-99.4%** |
| ≥ 0.99 | 3,460 (79.2%) | 1 (0.0%) | -99.9% |
| ≥ 0.95 | 3,882 (88.9%) | 161 (4.5%) | -95.9% |
| ≥ 0.9 | 4,017 (92.0%) | 432 (12.0%) | -87.0% |

#### Sample-by-Sample Evidence

For the SAME resources, probabilities are **30-47% lower**:

| Database | NEW Prob | OLD Prob | Drop |
|----------|----------|----------|------|
| HProtDB | 0.5250 | 0.9979 | **-47.3%** |
| IMG/M | 0.5462 | 0.9970 | **-45.2%** |
| AromaDeg | 0.8905 | 0.9991 | **-10.9%** |
| EvoSNP | 0.6710 | 0.9993 | **-32.8%** |
| BC-TFdb | 0.8386 | 0.9991 | **-16.1%** |

**Conclusion**: The NEW NER model produces systematically lower confidence scores, causing mass failure at the 0.978 threshold.

---

## Root Cause Deep Dive

### Why Did Training Fail?

Based on the training metrics, the NEW NER model shows classic symptoms of **undertraining** or **training instability**:

#### Hypothesis 1: Insufficient Training Data

**Evidence**:
- NER training set: Only **307 samples** (very small)
- Previous documentation notes this is insufficient for robust model
- Small datasets require more careful hyperparameter tuning

#### Hypothesis 2: Learning Rate Too High

**Evidence**:
- Training shows instability (F1 bouncing 0.58-0.64)
- Peak performance at epoch 4, then decline
- Learning rate: 2e-5 (standard but may be too high for small dataset)

**Expected behavior with correct LR**:
- Steady improvement
- Convergence by epoch 7-9
- No significant decline after peak

#### Hypothesis 3: Inadequate Regularization

**Evidence**:
- Train F1 reaches 0.974 (epoch 9)
- Val F1 only 0.621 (epoch 9)
- **Gap of 0.353** indicates overfitting

**Solution**:
- Increase dropout
- Add weight decay
- Early stopping at epoch 4

#### Hypothesis 4: Data Quality or Preprocessing Issues

**Potential Issues**:
- Wrong data splits loaded
- Tokenization differences in PyTorch 2.8.0 / Transformers 4.57.1
- Label encoding errors

**Requires Investigation**:
- Verify correct CSV files were loaded
- Check data split sizes match expected (307 train, 67 val, 67 test)
- Compare tokenization between environments

---

## Why OLD Models Work Despite Having NamedTuples

The OLD models have problematic NamedTuple objects in checkpoints, but they still work locally because:

1. **Trained in PyTorch 2.0.0**: Compatible with NamedTuple serialization
2. **Used locally in PyTorch 2.2.2**: Still compatible (similar version)
3. **Never loaded in PyTorch 2.8.0+**: Would fail if moved to Colab

**Risk**: The OLD models will fail if loaded in PyTorch 2.8.0+ (Colab) due to NamedTuple incompatibility.

**Action Needed**: Convert OLD models to v2 format before using in Colab.

---

## Environment Comparison

| Aspect | OLD (Working) | NEW (Degraded) |
|--------|---------------|----------------|
| **Training Environment** | Local | Google Colab |
| **Python** | 3.8 or 3.11 | 3.12.12 |
| **PyTorch** | 2.0.0 or 2.2.2 | 2.8.0+cu126 |
| **Transformers** | 4.35.0 | 4.57.1 |
| **GPU** | Local (unknown) | Tesla T4 |
| **Checkpoint Format** | NamedTuple (v1) | Dict (v2) ✓ |

**Library Version Changes**:
- PyTorch: 2.0/2.2 → 2.8 (major version jump)
- Transformers: 4.35 → 4.57 (22 versions)
- Python: 3.8/3.11 → 3.12

**Potential Impact**:
- Tokenization behavior changes
- Training dynamics differences
- Numerical precision variations

---

## Comparison to Previous PyTorch Issue

### Previous Issue (Oct 2025)

| Aspect | Previous Issue | Current Issue |
|--------|---------------|---------------|
| **Symptom** | 99.2% prediction loss | 99.4% prediction loss |
| **Probability Drop** | 0.998 → 0.764 (23.4%) | 0.9968 → 0.5-0.9 (10-45%) |
| **Root Cause** | PyTorch NamedTuple corruption | Poor training quality |
| **Affected** | Model weights corrupted | Model poorly trained |
| **Checkpoint Format** | NamedTuple (v1) | Dict (v2) ✓ |
| **Fix** | Convert checkpoints | Retrain with better params |

**Key Difference**: Previous issue was **environmental** (PyTorch incompatibility), current issue is **training quality**.

---

## Recommended Solutions

### Immediate Action (Use Working Models)

**DO**:
- ✅ Use OLD models (2025-10-24-apz1py) for production
- ✅ Results: `collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/final_inventory.csv`
- ✅ 3,698 high-confidence resources (validated)

**DO NOT**:
- ❌ Use NEW models (2025-10-28-nzksic)
- ❌ Results: `collab_results/2025-10-28-gl3fd6_2022_rerun/final_inventory.csv`
- ❌ Only 22 high-confidence resources (broken)

### Short-Term Fix (Retrain with Better Parameters)

1. **Lower Learning Rate**: Try 1e-5 or 5e-6 instead of 2e-5
2. **Add Weight Decay**: 0.01 or 0.001 to reduce overfitting
3. **Increase Dropout**: 0.2 or 0.3 in classifier
4. **Early Stopping**: Monitor validation F1, stop if no improvement for 3 epochs
5. **More Epochs**: Train for 15-20 epochs with early stopping
6. **Verify Data**: Ensure correct splits loaded (307/67/67 samples)

### Long-Term Solution (Expand Training Data)

**Current NER Dataset**: 307 train / 67 val / 67 test = **441 total samples**

**Target**: At least 1,000-2,000 samples for robust NER model

**Actions**:
1. Manual annotation of additional papers
2. Semi-supervised learning (use model predictions + manual review)
3. Data augmentation techniques
4. Transfer learning from related NER tasks

---

## Validation Checklist for Next Training Run

Before deploying new models, verify:

- [ ] Validation F1 > 0.70 for both models
- [ ] Test F1 matches validation F1 (±0.02)
- [ ] Training shows steady improvement (no bouncing)
- [ ] Train/val gap < 0.15 (indicates acceptable overfitting)
- [ ] Checkpoint format uses dicts (not NamedTuples)
- [ ] Test inference on sample papers produces expected results
- [ ] Probability distributions match baseline (mean > 0.95 for positives)
- [ ] High-confidence rate > 80% (threshold 0.978)

---

## Files Reference

### Training Session (NEW - Degraded)
- **Location**: `collab_results/models/2025-10-28-nzksic_full_training/`
- **Manifest**: `model_manifest.json`
- **Training Stats**: `classification_training_stats.csv`, `ner_training_stats.csv`
- **Test Metrics**: `classification_test_evaluation/metrics.csv`, `ner_test_evaluation/metrics.csv`

### Working Models (OLD)
- **Location**: `out/original_model/`
- **Files**: `article_classifier.pt`, `named_entity_recognition.pt`
- **Checksums**: See above

### Production Results
- **Working**: `collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/final_inventory.csv`
- **Broken**: `collab_results/2025-10-28-gl3fd6_2022_rerun/final_inventory.csv`

### Comparison Analysis
- **Report**: `INVENTORY_COMPARISON_REPORT_2025-10-28.md`
- **Summary**: `COMPARISON_SUMMARY.txt`
- **Detailed**: `comparison_gl3fd6_vs_ulgfhi/inventory_comparison_detailed.csv`

---

## Conclusion

The NEW models (2025-10-28-nzksic) are **correctly formatted** (no PyTorch compatibility issues) but **poorly trained** (NER F1 = 0.653 vs expected 0.749). The 12.8% performance drop causes systematically lower confidence scores, resulting in 99.4% failure at the production threshold.

**The problem is NOT technical infrastructure—it's training quality.**

The solution is to **retrain with better hyperparameters** (lower learning rate, more regularization, early stopping) and **expand the training dataset** for long-term robustness.

**For production use**: Continue using OLD models (2025-10-24-apz1py) which have validated performance, but convert them to v2 format before deploying to PyTorch 2.8+ environments.

---

**Report Status**: COMPLETE
**Next Steps**: Retrain models with corrected parameters
**Priority**: HIGH - Production blocked by poor model quality
