# Multi-Model Comparison Experimental Plan

**Date Created**: 2025-10-30
**Status**: Ready to Execute
**Session Type**: Full Training (not TEST_MODE)
**Estimated Duration**: ~48 hours (4 models × 15 epochs × ~0.8h/epoch)

---

## Executive Summary

This experimental run will compare 4 different biomedical BERT models using **validated optimal hyperparameters** and **fixed production data splits** to establish a true performance baseline and identify the best base model for our pipeline.

### Key Objectives

1. **Fix Data Configuration**: Use fixed production splits (enables V2 baseline comparison)
2. **Test Modern Models**: Compare current model against 3 modern alternatives
3. **Validate Optimal Parameters**: Confirm classif_lr=1e-5, ner_lr=5e-5 are optimal
4. **Achieve Phase 1 Target**: NER F1 ≥ 0.80 (+7% from baseline 0.749)

---

## Critical Fixes Applied

### 1. Data Splits (CRITICAL - Previous Session Issue)

**Previous Problem**: Session-specific splits prevented baseline comparison

**Fix Applied**:
```python
# Cell 10 - Now uses FIXED production splits
split_dir = "data/classif_splits_full"
ner_split_dir = "data/ner_splits_full"
```

**Impact**: Can now directly compare to V2 production models

---

### 2. Training Parameters (Optimized from 2025-10-29-4lblwv)

**Updates**:
```python
'num_epochs': 15,      # Increased from 10 (NER peaked at epochs 8-9)
'patience': 5,          # Increased from 3 (more patient for NER convergence)
```

**Rationale**: Previous session showed NER converging late (epochs 8-9), needs more time

---

### 3. Code Fixes (Critical Bugs from Review)

**Fixed**:
- ✅ Cell 8: Changed `LEARNING_RATE_CONFIGS` → `MODEL_EXPERIMENTS`
- ✅ Cell 12: Changed `BASE_CONFIG["model_name"]` → `MODEL_EXPERIMENTS[0]["model_name"]`
- ✅ Cell 10: Added TEST_MODE support for split selection
- ✅ Cell 12: Updated data file checking to use `BASE_CONFIG['classif_split_dir']`

---

## Experiment Configuration

### Models to Test (4 Total)

| # | Name | Model ID | Year | Description | Expected Improvement |
|---|------|----------|------|-------------|---------------------|
| 1 | original_optimal | allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500 | 2021 | Current production baseline | Baseline (0% change) |
| 2 | biolinkbert | michiyasunaga/BioLinkBERT-base | 2022 | **SOTA biomedical** (research recommended) | +2-4% F1 |
| 3 | pubmedbert | microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext | 2020 | Trained on PubMed | +1-3% F1 |
| 4 | scibert | allenai/scibert_scivocab_uncased | 2019 | Lighter scientific model | 0-2% F1 |

### Hyperparameters (All Models Use Same)

**Optimal Learning Rates** (from session 2025-10-29-4lblwv):
- Classification LR: `1e-5` (best from exp3_lower_lr)
- NER LR: `5e-5` (best from exp2_higher_lr)

**Training Configuration**:
```python
{
    'batch_size': 32,           # Auto-calculated for GPU
    'num_epochs': 15,           # Increased from 10
    'early_stopping': True,
    'patience': 5,              # Increased from 3
    'classif_lr': 1e-5,        # Validated optimal
    'ner_lr': 5e-5             # Validated optimal
}
```

### Data Configuration

**Classification Data**:
- Training: `data/classif_splits_full/train_paper_classif.csv` (1,635 samples × 70%)
- Validation: `data/classif_splits_full/val_paper_classif.csv` (1,635 samples × 15%)
- Test: `data/classif_splits_full/test_paper_classif.csv` (1,635 samples × 15%)

**NER Data**:
- Training: `data/ner_splits_full/train_ner.pkl` (554 samples × 70%)
- Validation: `data/ner_splits_full/val_ner.pkl` (554 samples × 15%)
- Test: `data/ner_splits_full/test_ner.pkl` (554 samples × 15%)

---

## Expected Results

### Performance Targets

| Model | Classification F1 | NER F1 | Total Improvement |
|-------|------------------|---------|-------------------|
| **V2 Production** | 0.898 | 0.749 | Baseline |
| **original_optimal** | 0.90-0.91 | 0.77-0.79 | +2-4% (better hyperparams) |
| **biolinkbert** | 0.91-0.93 | 0.80-0.82 | +5-9% (modern SOTA) |
| **pubmedbert** | 0.90-0.92 | 0.78-0.80 | +3-6% (domain-specific) |
| **scibert** | 0.89-0.91 | 0.76-0.78 | +1-3% (lighter model) |

### Success Criteria

**Must Achieve** (Phase 1 Goals):
- ✅ At least ONE model achieves NER F1 ≥ 0.80 (+7% from baseline)
- ✅ At least ONE model achieves Classification F1 ≥ 0.91 (+1.3% from baseline)
- ✅ Results are reproducible (fixed splits enable replication)
- ✅ Training stable (no F1 bouncing, early stopping effective)

**Optimal Outcome**:
- 🎯 BioLinkBERT achieves NER F1 ≥ 0.82 (Phase 1 complete)
- 🎯 Classification F1 ≥ 0.93 (bonus improvement)
- 🎯 Clear winner identified for Phase 2

---

## Timeline and Resource Requirements

### Estimated Duration

**Per Model**:
- Classification training: ~6-8 hours (15 epochs, early stopping)
- NER training: ~6-8 hours (15 epochs, early stopping)
- Total per model: ~12-16 hours

**Total Session**:
- 4 models × 12-16 hours = **48-64 hours**
- With early stopping: **~48 hours realistic**

### Execution Strategy

**Option A**: Sequential Execution (Recommended)
- Run all 4 models sequentially in Colab
- Estimated: 2-3 days of continuous training
- Pros: Simple, no coordination needed
- Cons: Long waiting time

**Option B**: Parallel Execution (Advanced)
- Run 2 models simultaneously in separate Colab notebooks
- Estimated: 1-1.5 days total
- Pros: Faster results
- Cons: Requires 2 Colab sessions, manual coordination

**Recommendation**: Option A (sequential) for this run

---

## Execution Checklist

### Pre-Flight (Before Running in Colab)

- [x] Notebook updated with multi-model configuration
- [x] Data splits fixed to use production splits
- [x] Critical bugs fixed (Cell 8, Cell 10, Cell 12)
- [x] Notebook uploaded to Google Drive
- [ ] Colab runtime selected (T4/V100/A100 GPU)
- [ ] Sufficient Google Drive space (5+ GB free)
- [ ] Sufficient time allocated (2-3 days)

### During Execution

- [ ] Cell 1: Mount Google Drive ✓
- [ ] Cell 2: Configuration loaded ✓
- [ ] Cell 3: Dependencies installed ✓
- [ ] Cell 4: Experiment tracker initialized ✓
- [ ] Cell 5: Data splits verified ✓
- [ ] Cell 5.5: Pre-flight checks passed ✓
- [ ] Cell 6: Training loop running
- [ ] Monitor progress periodically
- [ ] Check for errors in logs

### Post-Execution

- [ ] All 4 experiments completed
- [ ] Results CSV downloaded
- [ ] Training curves analyzed
- [ ] Best model identified
- [ ] Compare to V2 production baseline
- [ ] Document findings
- [ ] Decision: Proceed to Phase 2 or iterate

---

## Key Differences from Previous Session (2025-10-29-4lblwv)

| Aspect | Previous Session | This Session |
|--------|-----------------|--------------|
| **Data Splits** | Session-specific (`data/classif_splits_exp_{SESSION_ID}`) | **Fixed production** (`data/classif_splits_full/`) |
| **Experiments** | 4 learning rate variations | **4 different base models** |
| **Learning Rates** | Varied (2e-5 to 1e-4) | **Fixed optimal** (1e-5, 5e-5) |
| **Max Epochs** | 10 | **15** (increased) |
| **Patience** | 3 | **5** (increased) |
| **Comparison** | Not valid (different splits) | **Valid vs V2** (same splits) |
| **Goal** | Infrastructure validation | **Performance optimization** |

---

## Expected Artifacts

### Files Generated (Automatically)

1. **experiment_results.csv** - All metrics for all 4 models
2. **comparison_summary.md** - Markdown summary with best configs
3. **session_metadata.json** - Session timing and status
4. **Training curves** (8 PNG files):
   - `exp1_original_optimal_classif_curves.png`
   - `exp1_original_optimal_ner_curves.png`
   - `exp2_biolinkbert_classif_curves.png`
   - `exp2_biolinkbert_ner_curves.png`
   - `exp3_pubmedbert_classif_curves.png`
   - `exp3_pubmedbert_ner_curves.png`
   - `exp4_scibert_classif_curves.png`
   - `exp4_scibert_ner_curves.png`
5. **Training logs** (4 directories with full stdout/stderr)
6. **Model checkpoints** (8 total - 4 models × 2 tasks)

### Archive Location

```
gdrive:inventory_2022/experiment_archives/{SESSION_ID}/
├── experiment_results.csv
├── comparison_summary.md
├── session_metadata.json
├── training_curves/
│   └── (8 PNG files)
├── training_logs/
│   ├── exp1_original_optimal/
│   ├── exp2_biolinkbert/
│   ├── exp3_pubmedbert/
│   └── exp4_scibert/
└── models/
    └── (8 model checkpoints)
```

---

## Risk Assessment

### High Risks

1. **Timeout Issues** (Medium Probability)
   - **Risk**: 2-hour timeout may be insufficient for 15 epochs
   - **Mitigation**: Timeout increased to 7200s (2 hours), early stopping will likely trigger before timeout
   - **Contingency**: If timeout occurs, reduce epochs to 12

2. **Model Download Failures** (Low Probability)
   - **Risk**: Hugging Face model download issues
   - **Mitigation**: Pre-flight check verifies first model accessibility
   - **Contingency**: Retry with different model or check internet connectivity

3. **GPU Memory Issues** (Low Probability)
   - **Risk**: Larger models may exceed GPU memory
   - **Mitigation**: Optimal batch size calculation, GPU memory clearing between experiments
   - **Contingency**: Reduce batch size to 16 if OOM occurs

### Medium Risks

4. **Early Stopping Too Aggressive** (Medium Probability)
   - **Risk**: Patience=5 may still stop training too early
   - **Mitigation**: Increased from 3 to 5 based on evidence
   - **Contingency**: Next run could increase to patience=7

5. **BioLinkBERT Incompatibility** (Low Probability)
   - **Risk**: Model may not be compatible with our pipeline
   - **Mitigation**: Model is standard BERT-base architecture
   - **Contingency**: Exclude from analysis if incompatible

### Low Risks

6. **Disk Space** (Low Probability)
   - **Risk**: 5GB+ required for all artifacts
   - **Mitigation**: Most users have sufficient Drive space
   - **Contingency**: Clean up old experimental archives

---

## Decision Points

### After Experiment 1 (original_optimal)

**If results match V2 baseline (~0.90 classif, ~0.75 NER)**:
- ✅ Confirms fixed splits are working correctly
- ✅ Proceed with remaining experiments

**If results significantly differ from V2**:
- ⚠️ Investigate: Check hyperparameters, verify data splits
- ⚠️ May need to pause and debug before continuing

### After Experiment 2 (biolinkbert)

**If BioLinkBERT achieves NER F1 ≥ 0.80**:
- 🎉 Phase 1 goal achieved!
- ✅ Continue to test remaining models for comparison
- ✅ Plan for Phase 2 (data augmentation)

**If BioLinkBERT does NOT achieve ≥ 0.80**:
- ⚠️ Still continue with remaining models
- ⚠️ May need Phase 1 iteration with different hyperparameters

### After All Experiments Complete

**Best Case** (NER F1 ≥ 0.82):
- 🎉 Exceed Phase 1 target
- → Proceed directly to Phase 2 (data augmentation + TAPT)
- → Target: NER F1 ≥ 0.85

**Good Case** (NER F1 = 0.80-0.82):
- ✅ Phase 1 target achieved
- → Proceed to Phase 2 with best model
- → Continue hyperparameter tuning in parallel

**Acceptable Case** (NER F1 = 0.77-0.80):
- ⚠️ Close to target but not quite there
- → Try additional hyperparameter combinations
- → Consider smaller learning rate sweep
- → Delay Phase 2 until ≥ 0.80 achieved

**Concerning Case** (NER F1 < 0.77):
- ❌ Below current production and Phase 1 target
- → Debug: Verify training scripts, check for regressions
- → Review training curves for issues
- → May need to investigate further

---

## Next Steps After This Run

### Immediate (Day 1 After Completion)

1. **Download Results**: Use `python download_from_drive.py --archive-type experiment_archives`
2. **Analyze Results**: Compare all 4 models against V2 baseline
3. **Review Training Curves**: Check convergence patterns, identify issues
4. **Identify Best Model**: Select model with best NER F1 (prioritize) and Classification F1
5. **Document Findings**: Create results summary document

### Short-Term (Week 1)

**If Phase 1 Target Achieved (NER F1 ≥ 0.80)**:
1. Validate best model on test set
2. Run inference on 2022 dataset subset (1,000 papers)
3. Compare high-confidence predictions vs V2
4. Begin Phase 2 planning (UMLS license application)
5. Start implementing data augmentation

**If Phase 1 Target NOT Achieved**:
1. Analyze why performance is below target
2. Review training curves for clues
3. Plan hyperparameter iteration
   - Try batch_size variations (16, 24, 32)
   - Try learning rate refinement (8e-6, 1.5e-5)
   - Consider longer training (epochs=20, patience=7)
4. Run focused experiments on best-performing model

### Medium-Term (Weeks 2-3)

**Phase 2 Execution** (if Phase 1 successful):
1. UMLS-EDA data augmentation
2. Generate augmented NER dataset (1,100-1,600 samples)
3. Optional: GPT-4 synthetic generation
4. Train best model on augmented data
5. Target: NER F1 ≥ 0.85

---

## Success Metrics

### Infrastructure Validation

- ✅ All 4 experiments complete without crashes
- ✅ Fixed splits enable direct V2 comparison
- ✅ Training logs captured completely
- ✅ Results automatically archived to Drive

### Performance Validation

- 🎯 **Primary**: At least one model achieves NER F1 ≥ 0.80
- 🎯 **Secondary**: Classification F1 ≥ 0.91
- ✅ **Baseline**: Results comparable to V2 (confirms splits work)
- ✅ **Improvement**: Modern models outperform 2021 baseline

### Knowledge Gained

- ✅ Identify best base model for biodata inventory task
- ✅ Confirm optimal hyperparameters work across models
- ✅ Understand convergence patterns with longer training
- ✅ Validate early stopping effectiveness with patience=5

---

## Conclusion

This experimental run represents a critical milestone in the model improvement roadmap. By fixing the data configuration issue and testing modern biomedical BERT models with validated optimal hyperparameters, we can:

1. **Establish True Baseline**: Compare fairly to V2 production models
2. **Identify Best Model**: Select optimal base model for our specific task
3. **Achieve Phase 1 Target**: NER F1 ≥ 0.80 (+7% improvement)
4. **Enable Phase 2**: Data augmentation with best-performing model

With infrastructure 100% validated (from session 2025-10-29-4lblwv) and critical bugs fixed, this run should execute flawlessly and provide the data needed to make informed decisions about proceeding to Phase 2.

**Estimated Start**: 2025-10-30 (ready to execute immediately)
**Estimated Completion**: 2025-11-01 or 2025-11-02 (48-64 hours)
**Next Review**: Immediately after completion

---

**Document Created**: 2025-10-30
**Author**: Warren Hack (with Claude Code Sonnet 4.5 assistance)
**Status**: ✅ Ready to Execute
**Notebook**: experimental_training_pipeline.ipynb (uploaded to Drive)
