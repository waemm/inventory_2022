# Multi-Model Comparison Results - October 30, 2025

**Session ID**: 2025-10-30-p9rat5
**Date**: 2025-10-30
**Duration**: 1 hour 4 minutes (08:34 → 09:38)
**Status**: ✅ **ALL 4 EXPERIMENTS COMPLETED** | ⚠️ **PERFORMANCE BELOW TARGET**

---

## Executive Summary

This session tested 4 different biomedical BERT models using validated optimal hyperparameters (classif_lr=1e-5, ner_lr=5e-5) and **fixed production data splits** to establish a true baseline comparison. All experiments completed successfully, but **NER performance was significantly below V2 production baseline**, indicating a critical hyperparameter or configuration mismatch.

### Key Findings

**Infrastructure**: ✅ **PERFECT**
- All 4 models trained successfully
- Fixed production splits enabled V2 comparison
- Early stopping effective (patience=5 working well)
- Total training time: 64 minutes (~16 min per model)

**Performance**: ❌ **BELOW TARGET**
- **Classification**: 0.917 best (PubMedBERT) vs 0.898 V2 = **+2.1%** ✅
- **NER**: 0.670 best (Original) vs 0.749 V2 = **-10.5%** ❌
- **Phase 1 Target**: NER F1 ≥ 0.80 = **NOT ACHIEVED** (15% gap)

**Critical Issue Identified**: V2 training configuration unknown - need to investigate actual hyperparameters used in October 21, 2025 training.

---

## Complete Results

### All Models Tested

| # | Model | Base Model | Year | Classification F1 | NER F1 |
|---|-------|-----------|------|------------------|--------|
| 1 | original_optimal | allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500 | 2021 | 0.8793 | **0.6698** ⭐ |
| 2 | biolinkbert | michiyasunaga/BioLinkBERT-base | 2022 | 0.8926 | 0.6562 |
| 3 | pubmedbert | microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext | 2020 | **0.9167** ⭐ | 0.6354 |
| 4 | scibert | allenai/scibert_scivocab_uncased | 2019 | 0.8926 | 0.6300 |

### Comparison to V2 Production Baseline

| Model | Classification | vs V2 (0.898) | NER | vs V2 (0.749) |
|-------|---------------|---------------|-----|---------------|
| **V2 Production** | **0.898** | Baseline | **0.749** | Baseline |
| **original_optimal** | 0.879 | -2.1% ⚠️ | **0.670** | **-10.5%** ⚠️ |
| **biolinkbert** | 0.893 | -0.6% | 0.656 | -12.4% ⚠️ |
| **pubmedbert** | **0.917** | **+2.1%** ✅ | 0.635 | -15.2% ⚠️ |
| **scibert** | 0.893 | -0.6% | 0.630 | -15.9% ⚠️ |

---

## Detailed Results by Model

### Experiment 1: Original Model (Optimal Parameters)

**Model**: allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500
**Description**: 2021 RoBERTa - Current production baseline with optimal LR

**Classification**:
- Val F1: 0.8793
- Val Precision: 0.9273
- Val Recall: 0.8361
- Train F1: 0.9970
- Best Epoch: 6/15
- Total Epochs: 12 (early stopped)

**NER** ⭐ **BEST NER RESULT**:
- Val F1: **0.6698** (best of all 4)
- Val Precision: 0.6951
- Val Recall: 0.6463
- Train F1: 0.9192
- Best Epoch: 6/15
- Total Epochs: 12 (early stopped)

**Training Time**: 17.6 minutes (1054 seconds)

**Analysis**:
- Best NER performance across all models
- Still 10.5% below V2 baseline
- Early stopping at epoch 12 (patience=5 triggered)
- High train/val gap suggests potential overfitting

---

### Experiment 2: BioLinkBERT (2022 SOTA)

**Model**: michiyasunaga/BioLinkBERT-base
**Description**: 2022 BioLinkBERT - SOTA biomedical (research recommended)

**Classification**:
- Val F1: 0.8926
- Val Precision: 0.9000
- Val Recall: 0.8852
- Train F1: 0.9880
- Best Epoch: 4/15
- Total Epochs: 10 (early stopped)

**NER**:
- Val F1: 0.6562
- Val Precision: 0.6731
- Val Recall: 0.6402
- Train F1: 0.9240
- Best Epoch: 9/15
- Total Epochs: 15 (completed)

**Training Time**: 17.5 minutes (1050 seconds)

**Analysis**:
- Completed all 15 epochs for NER (no early stopping)
- Classification stopped at epoch 10
- NER peaked late (epoch 9), may benefit from longer training
- Did not outperform original model despite being newer SOTA

---

### Experiment 3: PubMedBERT (2020)

**Model**: microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext
**Description**: 2020 PubMedBERT - Trained on PubMed

**Classification** ⭐ **BEST CLASSIFICATION RESULT**:
- Val F1: **0.9167** (best of all 4, exceeds V2!)
- Val Precision: 0.9322
- Val Recall: 0.9016
- Train F1: 0.9483
- Best Epoch: 2/15 ⚡
- Total Epochs: 8 (early stopped)

**NER**:
- Val F1: 0.6354
- Val Precision: 0.7379 (highest precision)
- Val Recall: 0.5579 (lowest recall)
- Train F1: 0.8614
- Best Epoch: 3/15
- Total Epochs: 9 (early stopped)

**Training Time**: 12.0 minutes (719 seconds) ⚡ **FASTEST**

**Analysis**:
- **Excellent classification performance** (+2.1% vs V2)
- Very fast convergence (best at epoch 2 for classification)
- Fastest training time
- NER has precision/recall imbalance (high precision, low recall)
- Lower train F1 suggests less overfitting

---

### Experiment 4: SciBERT (2019)

**Model**: allenai/scibert_scivocab_uncased
**Description**: 2019 SciBERT - Lighter scientific model

**Classification**:
- Val F1: 0.8926
- Val Precision: 0.9000
- Val Recall: 0.8852
- Train F1: 1.0000 (perfect training fit)
- Best Epoch: 8/15
- Total Epochs: 14 (early stopped)

**NER**:
- Val F1: 0.6300
- Val Precision: 0.6949
- Val Recall: 0.5762
- Train F1: 0.9190
- Best Epoch: 4/15
- Total Epochs: 10 (early stopped)

**Training Time**: 16.6 minutes (998 seconds)

**Analysis**:
- Classification achieved perfect training F1 (overfitting)
- Lowest NER performance of all models
- Similar to previous session results with SciBERT
- Not recommended for this task

---

## Performance Analysis

### Classification Performance Ranking

| Rank | Model | Val F1 | vs V2 | Best Epoch | Training Epochs |
|------|-------|--------|-------|------------|----------------|
| 🥇 1 | **PubMedBERT** | **0.9167** | **+2.1%** ✅ | 2 | 8 |
| 🥈 2 | BioLinkBERT | 0.8926 | -0.6% | 4 | 10 |
| 🥈 2 | SciBERT | 0.8926 | -0.6% | 8 | 14 |
| 4 | Original | 0.8793 | -2.1% | 6 | 12 |

**Key Insights**:
- **PubMedBERT is clear winner** for classification
- Exceeds V2 baseline by 2.1%
- Converges very fast (epoch 2)
- Most efficient training

### NER Performance Ranking

| Rank | Model | Val F1 | vs V2 | Best Epoch | Training Epochs |
|------|-------|--------|-------|------------|----------------|
| 🥇 1 | **Original** | **0.6698** | **-10.5%** ⚠️ | 6 | 12 |
| 🥈 2 | BioLinkBERT | 0.6562 | -12.4% ⚠️ | 9 | 15 |
| 🥉 3 | PubMedBERT | 0.6354 | -15.2% ⚠️ | 3 | 9 |
| 4 | SciBERT | 0.6300 | -15.9% ⚠️ | 4 | 10 |

**Key Insights**:
- **All models underperform V2 baseline significantly**
- Original model still best for NER
- Modern models did NOT improve NER performance
- 10-16% degradation vs V2 is **very concerning**

### Training Efficiency

| Model | Total Time | Classif Time | NER Time | Convergence Speed |
|-------|-----------|--------------|----------|-------------------|
| PubMedBERT | **12.0 min** ⚡ | ~4 min | ~8 min | Fastest (epoch 2-3) |
| SciBERT | 16.6 min | ~8 min | ~8 min | Medium |
| BioLinkBERT | 17.5 min | ~7 min | ~10 min | Slowest (epoch 9) |
| Original | 17.6 min | ~8 min | ~9 min | Medium |

---

## Comparison to Previous Sessions

### vs Session 2025-10-29-4lblwv (Session-Specific Splits)

| Metric | 2025-10-29 (bad splits) | 2025-10-30 (fixed splits) | Improvement |
|--------|------------------------|--------------------------|-------------|
| **Best Classification** | 0.882 (lower_lr) | **0.917** (PubMedBERT) | **+3.5%** ✅ |
| **Best NER** | 0.630 (higher_lr) | **0.670** (original) | **+4.0%** ✅ |
| **Data Configuration** | Session-specific | Production splits | ✅ Fixed |
| **Baseline Comparison** | Not valid | Valid | ✅ Enabled |

**Insight**: Fixed splits DID improve results (+4% NER), but still far from V2 baseline.

### vs V2 Production (October 21, 2025)

| Model | V2 Baseline | Best This Session | Gap | Status |
|-------|-------------|------------------|-----|--------|
| **Classification** | 0.898 | 0.917 (PubMedBERT) | **+2.1%** | ✅ **EXCEEDED** |
| **NER** | 0.749 | 0.670 (Original) | **-10.5%** | ❌ **DEGRADED** |

---

## Root Cause Analysis: Why NER Underperforms

### Hypothesis 1: V2 Training Configuration Mismatch ⭐ **MOST LIKELY**

**Evidence**:
- Same base model (original) performs 10.5% worse with "optimal" parameters
- Training curves show early stopping at epoch 6-12 (may be too early)
- High train/val gap (train F1=0.92, val F1=0.67) suggests overfitting

**Unknown V2 Parameters**:
- ❓ Actual learning rates used
- ❓ Batch size
- ❓ Weight decay settings
- ❓ Dropout rates
- ❓ Number of epochs trained
- ❓ Early stopping configuration

**Action Required**: Investigate `trained_models_25/2025-10-21_full_production_training/`

---

### Hypothesis 2: Data Split Mismatch

**Evidence**:
- We assume V2 used `data/classif_splits_full/` but this may not be correct
- V2 might have used different split ratios
- Or different random seed for splitting

**Questions**:
- ❓ Which splits did V2 actually use?
- ❓ Were splits generated with same random seed?
- ❓ Same train/val/test proportions (70/15/15)?

**Action Required**: Verify V2 split configuration

---

### Hypothesis 3: Learning Rate Still Not Optimal

**Evidence**:
- Previous session found classif_lr=1e-5, ner_lr=5e-5 best
- But those results used different splits
- With production splits, optimal LR might be different
- NER may need even lower LR (e.g., 3e-5 or 2e-5)

**Observation**:
- Original session (Oct 29) baseline config: classif_lr=2e-5, ner_lr=3e-5
- This session: classif_lr=1e-5, ner_lr=5e-5
- V2 actual LR: **unknown**

**Action Required**: Try additional LR sweep with production splits

---

### Hypothesis 4: Transformers Library Version Difference

**Evidence**:
- Using transformers==4.35.2 (pinned for PyTorch compatibility)
- V2 training used unknown version (possibly 4.35.0 or earlier)
- Different versions may have different default behaviors

**Action Required**: Check V2 training environment

---

### Hypothesis 5: Early Stopping Too Aggressive

**Evidence**:
- Patience=5, all models stopped at epochs 8-15
- BioLinkBERT NER peaked at epoch 9 (late convergence)
- V2 may have trained for 20+ epochs without early stopping

**Counter-evidence**:
- Original model best at epoch 6 (stopped at 12)
- Training F1 already very high (0.92), more epochs may overfit

**Action Required**: Review V2 training curves

---

## Early Stopping Analysis

### Classification Early Stopping

| Model | Best Epoch | Total Epochs | Stopped Early? | Notes |
|-------|------------|--------------|----------------|-------|
| PubMedBERT | 2 | 8 | Yes (patience=5) | Very fast convergence |
| BioLinkBERT | 4 | 10 | Yes (patience=5) | Good convergence |
| Original | 6 | 12 | Yes (patience=5) | Moderate convergence |
| SciBERT | 8 | 14 | Yes (patience=5) | Slow convergence |

**Pattern**: All stopped early (8-14 epochs), which is appropriate. Classification doesn't need 15 epochs.

### NER Early Stopping

| Model | Best Epoch | Total Epochs | Stopped Early? | Notes |
|-------|------------|--------------|----------------|-------|
| Original | 6 | 12 | Yes (patience=5) | Moderate convergence |
| BioLinkBERT | 9 | 15 | No (completed) | **Late peak - may need more epochs** |
| PubMedBERT | 3 | 9 | Yes (patience=5) | Fast convergence |
| SciBERT | 4 | 10 | Yes (patience=5) | Fast convergence |

**Pattern**: BioLinkBERT completed all 15 epochs with best at epoch 9. May benefit from max_epochs=20.

---

## Training Curves Availability

Training curves saved to:
```
collab_results/experiment_archives/2025-10-30-p9rat5/training_curves/
```

**Files** (8 PNG files):
- `exp1_original_optimal_classif_curves.png`
- `exp1_original_optimal_ner_curves.png`
- `exp2_biolinkbert_classif_curves.png`
- `exp2_biolinkbert_ner_curves.png`
- `exp3_pubmedbert_classif_curves.png`
- `exp3_pubmedbert_ner_curves.png`
- `exp4_scibert_classif_curves.png`
- `exp4_scibert_ner_curves.png`

**Recommendation**: Review curves to understand convergence patterns and validate early stopping decisions.

---

## Critical Next Steps

### 🚨 PRIORITY 1: Investigate V2 Training Configuration

**Objective**: Find actual hyperparameters used in October 21, 2025 training

**Actions**:
1. Check `trained_models_25/2025-10-21_full_production_training/train_stats.csv`
2. Look for V2 training logs
3. Check git history around October 21, 2025
4. Review `config/train_predict.yml` for October 21 settings
5. Check if V2 used bash script `run_full_training.sh` (check script for parameters)

**Expected Findings**:
- V2 learning rates (likely different from 1e-5/5e-5)
- V2 batch size
- V2 epochs trained
- V2 early stopping configuration

---

### 🔍 PRIORITY 2: Verify Data Configuration

**Objective**: Confirm V2 used same data splits

**Actions**:
1. Check V2 training command/logs for split directory paths
2. Verify `data/classif_splits_full/` and `data/ner_splits_full/` were used
3. Check if splits have metadata (creation date, random seed)
4. Compare split file sizes with current

---

### 🎯 PRIORITY 3: Run Targeted Learning Rate Experiment

**Objective**: Find truly optimal LR with production splits

**Configuration**:
```python
# Use original model (best NER performer)
MODEL = 'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500'

# Test NER learning rates around V2 baseline range
NER_LR_CONFIGS = [
    {'ner_lr': 2e-5, 'classif_lr': 1e-5},  # Lower
    {'ner_lr': 3e-5, 'classif_lr': 1e-5},  # V2 baseline guess
    {'ner_lr': 4e-5, 'classif_lr': 1e-5},  # Mid
    {'ner_lr': 5e-5, 'classif_lr': 1e-5},  # Current "optimal"
]
```

---

### 📊 PRIORITY 4: Test on Test Set

**Objective**: Verify if validation metrics are representative

**Actions**:
1. Run best model (Original, exp1) on test set
2. Compare test F1 vs validation F1
3. Check if V2 metrics were actually test metrics (not validation)

---

## Recommendations

### Immediate (This Week)

1. **Find V2 Training Configuration** 🚨 **BLOCKING**
   - Without this, we're guessing at hyperparameters
   - Check all possible sources listed in Priority 1
   - Document findings in `docs/V2_TRAINING_CONFIGURATION.md`

2. **Review Training Curves**
   - Download and examine all 8 PNG files
   - Look for overfitting patterns
   - Validate early stopping decisions

3. **Test on Test Set**
   - Use original model from exp1
   - Verify validation metrics are correct

### Short-Term (Next 1-2 Weeks)

4. **Iterative Hyperparameter Search**
   - Once V2 config found, match it exactly
   - Then systematically vary one parameter at a time
   - Target: NER F1 ≥ 0.75 (match V2)

5. **Consider Alternative Approaches**
   - If hyperparameter tuning doesn't work, investigate:
     - Different optimization algorithms
     - Gradient clipping
     - Learning rate schedulers
     - Weight decay tuning

### Medium-Term (Weeks 3-4)

6. **Phase 1 Completion** (if we can match V2)
   - Target: NER F1 ≥ 0.80 (requires +10% from current 0.67)
   - May need combination of:
     - Correct hyperparameters
     - Longer training
     - Better optimization

7. **Phase 2 Planning** (only if Phase 1 achieved)
   - Data augmentation
   - TAPT (Task-Adaptive Pre-Training)
   - Target: NER F1 ≥ 0.85

---

## Positive Findings

Despite NER underperformance, several positives emerged:

### ✅ Classification Success

**PubMedBERT** achieved **91.7% F1**, exceeding V2 baseline (89.8%) by 2.1%
- Could be deployed for classification immediately
- Very efficient training (12 minutes, best at epoch 2)
- Good generalization (lower train/val gap)

### ✅ Infrastructure Reliability

- All 4 experiments completed without errors
- Early stopping working correctly
- Training curves captured successfully
- Archival system working perfectly
- Fixed data splits enabled proper V2 comparison

### ✅ Original Model Validation

- Original model choice (allenai/dsp_roberta) validated as best for NER
- Modern alternatives (BioLinkBERT, PubMedBERT) did not improve NER
- Focus should be on hyperparameters, not model architecture

### ✅ Fast Experimentation

- 4 models in 64 minutes
- Can iterate quickly once configuration identified
- Infrastructure supports rapid experimentation

---

## Conclusion

This multi-model comparison session successfully demonstrated that:

1. **Infrastructure is production-ready** - all systems working flawlessly
2. **Fixed data splits enable V2 comparison** - can now measure accurately
3. **PubMedBERT excels at classification** - potential upgrade opportunity
4. **Original model is best for NER** - don't need to change base model
5. **Critical configuration mismatch exists** - NER underperforms by 10.5%

**The blocking issue is clear**: We don't know V2's actual training configuration. Until we find the exact hyperparameters used on October 21, 2025, we're essentially guessing.

**Immediate action required**: Investigate V2 training archives and configuration to identify the discrepancy.

**Phase 1 status**: Currently **NOT on track** to achieve NER F1 ≥ 0.80. Need to first match V2 baseline (0.749), then improve from there.

---

**Document Created**: 2025-10-30
**Author**: Warren Hack (with Claude Code Sonnet 4.5 assistance)
**Session**: 2025-10-30-p9rat5
**Status**: ⚠️ **CRITICAL INVESTIGATION REQUIRED**
**Next Action**: Find V2 training configuration
