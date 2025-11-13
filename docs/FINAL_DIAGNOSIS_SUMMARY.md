# Final Diagnosis Summary: Model Performance Degradation
**Date**: 2025-10-29
**Status**: 🔴 ROOT CAUSE CONFIRMED

---

## The Bottom Line

**PROBLEM**: Newly trained models (2025-10-28-nzksic) produce 99.4% fewer high-confidence predictions than validated models.

**ROOT CAUSE**: **Poor NER model training quality** - achieved only F1=0.653 vs expected F1=0.749 (12.8% drop).

**SOLUTION**: **Use converted v2 models** for production (good training + correct format) and retrain new models with better hyperparameters.

---

## Model Inventory

### ✅ RECOMMENDED: V2 Models (Converted from Good Training)

**Location**: `out/classif_train_out/article_classifier_v2.pt` and `out/ner_train_out/named_entity_recognition_v2.pt`

**Properties**:
- ✅ **Checkpoint Format**: Dict (v2 - PyTorch 2.8 compatible)
- ✅ **Training Quality**: Good (F1=0.749 NER, F1=0.898 Classification)
- ✅ **Architecture**: 5 labels NER, 2 labels Classification
- ✅ **Status**: Production-ready

**Checksums**:
- Classification: `ea57a1cab905c6d5c4e064204f3e160d`
- NER: `fb53cb6c17db50d62bd90a4dcea83fa4`

**History**: Converted from original v1 models on 2025-10-27 to fix PyTorch compatibility

---

### ⚠️ LEGACY: V1 Models (Original - Good Training, Old Format)

**Location**: `out/original_model/article_classifier.pt` and `named_entity_recognition.pt`

**Properties**:
- ❌ **Checkpoint Format**: NamedTuple (v1 - PyTorch 2.8 incompatible)
- ✅ **Training Quality**: Good (F1=0.749 NER, F1=0.898 Classification)
- ✅ **Architecture**: 5 labels NER, 2 labels Classification
- ⚠️ **Status**: Works locally (PyTorch 2.2), FAILS in Colab (PyTorch 2.8)

**Checksums**:
- Classification: `a496eae1d5cf343ae509bcbc7e3f400e`
- NER: `37eebc38463a90c43cc36ee8ee1f4aa3`

**Note**: These are the source models that were converted to v2. Do not use in PyTorch 2.8+.

---

### ❌ BROKEN: NEW Models (Fresh Training, Poor Quality)

**Location**: `collab_results/models/2025-10-28-nzksic_full_training/`

**Properties**:
- ✅ **Checkpoint Format**: Dict (v2 - PyTorch 2.8 compatible)
- ❌ **Training Quality**: POOR (F1=0.653 NER - 12.8% below target)
- ✅ **Architecture**: 5 labels NER, 2 labels Classification
- ❌ **Status**: DO NOT USE - produces 99.4% fewer predictions

**Checksums**:
- Classification: `992a1381f7b507c72286d88d2582945d`
- NER: `752cfaa0711d414269c7d22e2c6d1bf5`

**Training Issues**:
1. NER validation F1 peaked at 0.640 (epoch 4), then declined
2. Training unstable (F1 bouncing 0.58-0.64)
3. Final test F1 only 0.653 vs expected 0.749
4. Large train/val gap (0.974 vs 0.621) indicates overfitting

---

## What Happened: Timeline

### Phase 1: Original Models (Pre-Oct 2025)
- Models trained successfully with good performance
- Format: NamedTuple (v1) - works in PyTorch 2.0/2.2
- Status: Production use, local only

### Phase 2: PyTorch Incompatibility Discovered (Oct 2025)
- V1 models failed in PyTorch 2.8 (Colab) with 99% prediction loss
- Root cause: NamedTuple objects corrupt weights during deserialization
- Solution: Convert to dict-only format (v2)
- Result: V2 models created, working in both PyTorch 2.2 and 2.8

### Phase 3: New Training Attempt (Oct 28, 2025)
- Trained fresh models using corrected pipeline
- Used dict format (v2) - correct!
- But: Poor training quality (NER F1 only 0.653)
- Result: 99.4% prediction loss due to low confidence scores

---

## Key Insights

### Insight 1: Checkpoint Format ≠ Model Quality

The NEW models have the **correct checkpoint format** (v2, dicts) but **poor training quality**.
The V2 models have the **correct checkpoint format** AND **good training quality**.

**Lesson**: Format compatibility and training quality are independent issues.

###Insight 2: Similar Symptoms, Different Causes

| Issue | Previous (Oct 2025) | Current (Oct 2025) |
|-------|---------------------|-------------------|
| **Symptom** | 99% prediction loss | 99% prediction loss |
| **Cause** | PyTorch incompatibility | Poor training |
| **Fix** | Convert checkpoint format | Retrain with better params |
| **Format** | V1 → V2 | V2 ✓ (already correct) |

**Lesson**: Same symptoms can have completely different root causes.

### Insight 3: Training Stability Matters

**Good Training** (V1/V2 models):
```
Epoch 0: Val F1 ~ 0.45
Epoch 5: Val F1 ~ 0.70
Epoch 9: Val F1 ~ 0.75 (stable)
```

**Poor Training** (NEW models):
```
Epoch 0: Val F1 = 0.459
Epoch 4: Val F1 = 0.640 (peak)
Epoch 5: Val F1 = 0.580 (decline!)
Epoch 9: Val F1 = 0.621 (unstable)
```

**Lesson**: Monitor training curves for stability and convergence.

---

## Production Impact

### With V2 Models (Recommended)
- ✅ 3,698 high-confidence resources (84.7% pass rate)
- ✅ Average probability: 0.9968
- ✅ Validated against baseline: 82% overlap
- ✅ Works in both PyTorch 2.2 and 2.8

### With NEW Models (Broken)
- ❌ Only 22 high-confidence resources (0.6% pass rate)
- ❌ Average probability: 0.9838
- ❌ Probabilities 30-47% lower than expected
- ❌ 99.4% production failure

---

## Recommendations

### Immediate (Production)

**USE**: V2 models (`article_classifier_v2.pt`, `named_entity_recognition_v2.pt`)
- Best of both worlds: good training + compatible format
- Validated performance
- Works in all environments

**DO NOT USE**:
- ❌ V1 models (fail in PyTorch 2.8)
- ❌ NEW models (poor training quality)

### Short-Term (Retraining)

Fix the training issues:

1. **Lower learning rate**: 1e-5 instead of 2e-5
2. **Add weight decay**: 0.01
3. **Increase dropout**: 0.2-0.3
4. **Early stopping**: Stop at epoch 4-5 (before overfitting)
5. **Verify data**: Check splits are correct (307/67/67)

### Long-Term (Data Expansion)

**Current**: 307 NER training samples (insufficient)
**Target**: 1,000-2,000 samples

**Actions**:
- Manual annotation
- Semi-supervised learning
- Data augmentation

---

## Validation Checklist

Before using any newly trained models:

- [ ] NER test F1 > 0.70
- [ ] Classification test F1 > 0.85
- [ ] Training shows steady improvement (no bouncing)
- [ ] Train/val gap < 0.15
- [ ] Checkpoint uses dicts (no NamedTuples)
- [ ] Test on sample papers produces expected results
- [ ] High-confidence rate > 80% at threshold 0.978
- [ ] Compare with baseline inventory (>75% overlap)

---

## Files for Production Use

### Models
```bash
# RECOMMENDED for production
out/classif_train_out/article_classifier_v2.pt
out/ner_train_out/named_entity_recognition_v2.pt
```

### Results
```bash
# VALIDATED results (use these)
collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/final_inventory.csv

# BROKEN results (do not use)
collab_results/2025-10-28-gl3fd6_2022_rerun/final_inventory.csv
```

---

## Conclusion

The NEW models are **technically correct** (proper format, architecture) but **functionally broken** (poor training). Use the **V2 models** which combine validated training quality with PyTorch 2.8 compatibility.

The degradation was caused by **training instability** (learning rate too high, insufficient regularization, small dataset), NOT by checkpoint format or PyTorch version issues.

**Priority**: Use V2 models for production, retrain with corrected hyperparameters for future models.

---

**Report Complete**: 2025-10-29
**Action Required**: Deploy V2 models, retrain with better parameters
**Status**: Production unblocked with V2 models
