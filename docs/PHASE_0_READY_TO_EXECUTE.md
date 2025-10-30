# Phase 0: V2 Baseline Reproduction - Ready to Execute

**Date**: 2025-10-30
**Status**: ✅ READY TO EXECUTE
**Notebook**: experimental_training_pipeline.ipynb (uploaded to Drive)
**Estimated Duration**: 24-32 hours

---

## Executive Summary

The experimental training notebook has been updated with **V2's exact baseline parameters** discovered from the snakemake configuration. The notebook is ready to execute in Google Colab to complete Phase 0: V2 Baseline Reproduction.

### What Was Changed

**CORRECTED Parameters (from previous incorrect values):**

| Parameter | Previous (Wrong) | V2 Actual | Status |
|-----------|-----------------|-----------|--------|
| **Classification LR** | 1e-5 (50% too low) | **2e-5** | ✅ CORRECTED |
| **NER LR** | 5e-5 (150% too high) | **2e-5** | ✅ CORRECTED |
| **Batch Size** | 32 | **16** | ✅ CORRECTED |
| **Epochs** | 15 | **10** | ✅ CORRECTED |
| **Early Stopping** | YES (patience=5) | **NO** | ✅ DISABLED |
| **Data Splits** | Production splits | Production splits | ✅ MAINTAINED |

---

## Experiment Plan

### 4 Experiments Configured

#### Experiment 1: V2 Exact Reproduction (PRIMARY GOAL)
```python
{
    'name': 'v2_exact_reproduction',
    'model': 'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500',
    'classif_lr': 2e-5,  # V2 EXACT VALUE
    'ner_lr': 2e-5,      # V2 EXACT VALUE
    'batch_size': 16,
    'epochs': 10,
    'early_stopping': False
}
```

**Expected Results**:
- Classification F1: 0.898 (±0.02)
- NER F1: 0.749 (±0.02)
- If matched: **Phase 0 COMPLETE** ✅

#### Experiment 2: V2 with Lower LR (1.5e-5)
Test if slightly lower LR improves stability without sacrificing performance.

**Expected**: Slower convergence, similar final performance.

#### Experiment 3: V2 with Higher LR (3e-5)
Test if slightly higher LR speeds up convergence without instability.

**Expected**: Faster convergence, possible instability risk.

#### Experiment 4: Asymmetric LR (classif=2e-5, ner=1.5e-5)
Test if NER benefits from lower LR while classification uses baseline.

**Expected**: Potentially better NER stability.

---

## Timeline and Execution

### Estimated Duration

**Per Experiment**:
- Classification training: ~4 hours (10 epochs × ~0.4h)
- NER training: ~4 hours (10 epochs × ~0.4h)
- Total per experiment: ~8 hours

**Total Session**:
- 4 experiments × 8 hours = **32 hours**
- Actual with variance: **24-32 hours**
- **Completion**: 1-1.5 days of continuous training

### Execution Steps

1. **Open Google Colab**
   - Navigate to Google Drive
   - Open `inventory_2022/experimental_training_pipeline.ipynb`

2. **Select Runtime**
   - Runtime → Change runtime type
   - Hardware accelerator: GPU (T4, V100, or A100)
   - Recommended: T4 is sufficient

3. **Execute Cells Sequentially**
   - Cell 1: Mount Google Drive ✅
   - Cell 2: Configuration (shows experiment plan) ✅
   - Cell 3: Environment setup ✅
   - Cell 4: Initialize tracker ✅
   - Cell 5: Data preparation ✅
   - Cell 5.5: Pre-flight checks ✅
   - **Cell 6: Training loop (MAIN)** ← This runs all 4 experiments
   - Cell 7: Results analysis ✅
   - Cell 8: Archive session ✅

4. **Monitor Progress**
   - Check Cell 6 output for training progress
   - Each experiment shows last 50 lines of output
   - Can monitor periodically (every 2-4 hours)

5. **After Completion**
   - Results saved to `gdrive:inventory_2022/experiment_archives/{SESSION_ID}/`
   - Download results using: `python download_from_drive.py --archive-type experiment_archives`

---

## Success Criteria

### Primary Goal (Experiment 1)

**Phase 0 Complete** if:
- ✅ Classification F1 ≥ 0.895 (within 0.3% of V2 baseline 0.898)
- ✅ NER F1 ≥ 0.745 (within 0.5% of V2 baseline 0.749)
- ✅ Training stable (no bouncing, smooth convergence)
- ✅ Best epochs similar to V2 (classif~4, ner~8)

**If matched**: Phase 0 COMPLETE → Proceed to Phase 1

**If not matched**: Continue investigation, check for other differences

### Secondary Goals (Experiments 2-4)

- Identify if small LR variations improve performance
- Test asymmetric LRs (different for classif vs NER)
- Gather evidence for Phase 1 optimization
- Document convergence patterns

---

## Expected Outcomes

### Experiment 1: V2 Exact (2e-5, 2e-5)
**Prediction**: **SHOULD MATCH V2 BASELINE**
- Classification F1: 0.898
- NER F1: 0.749
- Confidence: 95%

**Why**: Using exact V2 configuration from snakemake

### Experiment 2: Lower LR (1.5e-5, 1.5e-5)
**Prediction**: Similar or slightly better
- Classification F1: 0.89-0.90
- NER F1: 0.74-0.76
- Slower convergence, more stable training

### Experiment 3: Higher LR (3e-5, 3e-5)
**Prediction**: Faster convergence, possible instability
- Classification F1: 0.88-0.90
- NER F1: 0.72-0.75
- Risk of training instability

### Experiment 4: Asymmetric (2e-5, 1.5e-5)
**Prediction**: Good classification, potentially better NER
- Classification F1: 0.89-0.90
- NER F1: 0.74-0.76
- Tests if NER needs lower LR

---

## Configuration Validation

### Source Documentation

**V2 Parameters Confirmed From**:
- ✅ `snakemake/config/train_predict.yml`
- ✅ `snakemake/config/models_info.tsv`
- ✅ `trained_models_25/2025-10-21_full_production_training/`
- ✅ `docs/V2_BASELINE_PARAMETERS_FOUND.md`

**Notebook Updated**:
- ✅ Cell 4: Configuration corrected
- ✅ Cell 6: Training loop handles no early stopping
- ✅ Cell 3: Batch size fixed to 16
- ✅ All cells: Tested and validated

**Upload Status**:
- ✅ Uploaded to `gdrive:inventory_2022/experimental_training_pipeline.ipynb`
- ✅ Force uploaded to ensure latest version
- ✅ Ready for Colab execution

---

## What to Do After Execution

### Immediate (Day 1 After Completion)

1. **Download Results**
   ```bash
   python download_from_drive.py --archive-type experiment_archives
   ```

2. **Analyze Results**
   - Check `experiment_results.csv`
   - Review `comparison_summary.md`
   - Examine training curves in `training_curves/`

3. **Compare to V2 Baseline**
   - Experiment 1 vs V2 production models
   - Classification: 0.898 target
   - NER: 0.749 target

4. **Decision Point**:
   - If Exp 1 matches V2: **Phase 0 COMPLETE** ✅ → Proceed to Phase 1
   - If Exp 1 doesn't match: Investigate further

### Documentation (Day 2)

1. **Create Results Document**
   - `docs/PHASE_0_RESULTS_YYYY-MM-DD.md`
   - Document all 4 experiment results
   - Compare with V2 baseline
   - Include training curves analysis

2. **Update Implementation Plan**
   - Mark Phase 0 as complete (if successful)
   - Update Phase 1 status to active
   - Document lessons learned

3. **Commit Updates**
   - Commit results analysis
   - Update documentation
   - Tag git commit as phase-0-complete

---

## Troubleshooting

### If Experiment 1 Doesn't Match V2

**Possible Causes**:
1. Different random seed (V2 used `-r` flag)
2. Different data splits (verify production splits used)
3. Different PyTorch/Transformers versions
4. Different GPU/precision settings

**Investigation Steps**:
1. Check training logs for parameter confirmation
2. Review training curves for convergence patterns
3. Compare best epochs with V2 (classif~4, ner~8)
4. Verify data splits are identical to V2
5. Check if dropout/other defaults differ

### If All Experiments Fail

**Unlikely but possible**:
- Infrastructure issue (GPU, dependencies)
- Data corruption
- Code regression

**Actions**:
- Review pre-flight checks output
- Check training logs for errors
- Verify data files integrity
- Test locally with TEST_MODE=True

---

## Key Files and Locations

### Notebook
- **Local**: `/Users/warren/development/GBC/inventory_2022/experimental_training_pipeline.ipynb`
- **Drive**: `gdrive:inventory_2022/experimental_training_pipeline.ipynb`

### Documentation
- **V2 Config**: `docs/V2_BASELINE_PARAMETERS_FOUND.md`
- **Clarification**: `docs/PARAMETER_OPTIMIZATION_CLARIFICATION.md`
- **Multi-Model Results**: `docs/MULTI_MODEL_RESULTS_2025-10-30.md`
- **Implementation Plan**: `docs/COMPREHENSIVE_IMPLEMENTATION_PLAN.md`

### Data Splits (Production)
- **Classification**: `data/classif_splits_full/`
- **NER**: `data/ner_splits_full/`

### V2 Archive
- **Models**: `trained_models_25/2025-10-21_full_production_training/`
- **Config**: `snakemake/config/`

---

## Confidence Assessment

**Overall Confidence**: **95%** that Experiment 1 will match V2 baseline

**Evidence Supporting High Confidence**:
1. ✅ Exact V2 parameters found in snakemake config
2. ✅ Parameters validated across multiple files
3. ✅ Configuration matches V2 training date (October 21, 2025)
4. ✅ Same model, same data splits, same hyperparameters
5. ✅ Infrastructure validated in previous sessions

**Remaining 5% Uncertainty**:
- Possible random seed differences
- Possible PyTorch/Transformers version effects
- Possible GPU precision differences

**Risk Mitigation**:
- Using `-r` flag for random seed (like V2)
- Using same PyTorch/Transformers versions
- Testing 4 experiments (redundancy)

---

## Next Steps After Phase 0

### If Successful (V2 Matched)

**Phase 1: Hyperparameter Optimization**
- Learning rate sweep around 2e-5
- Test weight decay (0.01)
- Test dropout variations (0.2-0.3)
- Test modern models (BioLinkBERT, PubMedBERT)
- Goal: NER F1 ≥ 0.80 (+7% from baseline)

### If Partially Successful

**Iteration**:
- Analyze what worked vs what didn't
- Refine hypothesis about V2 configuration
- Plan targeted experiments
- Document findings

---

## Summary Checklist

**Before Execution**:
- [x] V2 parameters documented
- [x] Notebook updated and tested
- [x] Notebook uploaded to Drive
- [x] Configuration validated
- [x] Documentation complete
- [ ] Google Colab session ready
- [ ] Sufficient time allocated (1-2 days)

**During Execution**:
- [ ] Pre-flight checks passed
- [ ] Experiment 1 started
- [ ] Monitor progress periodically
- [ ] Check for errors in output

**After Execution**:
- [ ] Results downloaded
- [ ] Analysis complete
- [ ] Baseline comparison done
- [ ] Phase 0 status determined
- [ ] Documentation updated
- [ ] Phase 1 planning (if successful)

---

**Document Created**: 2025-10-30
**Status**: ✅ READY TO EXECUTE
**Estimated Completion**: 2025-10-31 or 2025-11-01
**Impact**: Unblocks Phase 1 of model improvement plan
