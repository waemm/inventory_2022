# CRITICAL INVESTIGATION: Model Degradation in New Training Session
**Date**: 2025-10-28
**Status**: 🚨 ACTIVE INVESTIGATION - PRODUCTION IMPACT
**Severity**: CRITICAL - 99.4% performance loss in new models

---

## Executive Summary

The newly trained models from training session **2025-10-28-nzksic** show catastrophic performance degradation similar to the PyTorch checkpoint corruption issue documented in October 2025. Despite following the corrected training pipeline (`full_training_pipeline_simplified.ipynb`), the models produce only **22 high-confidence records** compared to the expected **3,698 records** from the validated old models.

**This represents a 99.4% non-overlap rate - nearly identical to the 99.2% prediction loss from the previous checkpoint corruption issue.**

---

## Timeline of Events

### Previous Issues (Resolved October 2025)

1. **PyTorch Checkpoint Corruption** (Resolved 2025-10-27)
   - Models trained in PyTorch 2.0.0 lost 99.2% of predictions in PyTorch 2.8.0
   - Root cause: NamedTuple objects in checkpoints corrupted weights
   - Solution: Converted to v2 format (dict-only), use `weights_only=True`

2. **Checkpoint Data Contamination** (Resolved 2025-10-28)
   - Checkpoint/caching system mixed data from different runs
   - 24% confidence drop, 825 rows lost between pipeline steps
   - Solution: Deprecated checkpoint system entirely

### Current Issue (2025-10-28)

1. **New Training Attempt**:
   - Used `full_training_pipeline_simplified.ipynb` (corrected version)
   - Training session: **2025-10-28-nzksic**
   - Models produced with new checksums:
     - Classification: `992a1381f7b507c72286d88d2582945d` (475.57 MB)
     - NER: `752cfaa0711d414269c7d22e2c6d1bf5` (473.33 MB)

2. **Inference Run** (2025-10-28-gl3fd6):
   - Used `rerun_2022_inventory_simplified.ipynb` (corrected version)
   - Input: 21,677 papers (same as validated run)
   - Output: **Only 22 high-confidence records** (0.61% pass rate)
   - Expected: ~3,698 records (84.7% pass rate)

3. **Comparison Results**:
   - NEW vs OLD: 0.54% overlap
   - NEW vs Baseline: 0.38% overlap
   - OLD vs Baseline: 82.09% overlap ✅

---

## Critical Findings

### 1. Missing Training Session

**ALERT**: Training session `2025-10-28-nzksic` is **NOT FOUND** in local repository.

**Implications**:
- Models may have been trained in Colab without local backup
- No local training logs, validation metrics, or performance data
- Cannot verify training parameters, data, or quality
- Cannot reproduce or debug training process

**Action Required**: Locate this training session in Google Drive archives

### 2. Model Checksum Mismatch

The new models have **completely different checksums** from all known good models:

| Model Type | OLD (Working) | NEW (Degraded) | Match? |
|------------|---------------|----------------|--------|
| Classification | `a496eae1d5cf343ae509bcbc7e3f400e` | `992a1381f7b507c72286d88d2582945d` | ❌ |
| NER | `37eebc38463a90c43cc36ee8ee1f4aa3` | `752cfaa0711d414269c7d22e2c6d1bf5` | ❌ |

**This confirms these are entirely different models, not corrupted versions of good models.**

### 3. Performance Degradation Pattern

The degradation pattern is eerily similar to the previous checkpoint corruption:

| Issue | Previous (Oct 2025) | Current (Oct 2025) |
|-------|---------------------|-------------------|
| High-conf records | 3,698 → 29 | 3,698 → 22 |
| Loss percentage | 99.2% | 99.4% |
| Confidence drop | 0.998 → 0.764 (23.4%) | 0.9968 → 0.9838 (1.3%) |
| Root cause | PyTorch incompatibility | **UNKNOWN** |

**Key Difference**: The confidence drop is much smaller (1.3% vs 23.4%), suggesting a different failure mode.

### 4. Pipeline Step Analysis

| Step | NEW (gl3fd6) | OLD (ulgfhi) | Loss |
|------|--------------|--------------|------|
| Classification Positives | 4,713 | 4,827 | **-2.4%** |
| NER Results | 3,611 | 4,395 | **-17.8%** |
| Final Inventory | 3,592 | 4,368 | **-17.7%** |
| High-Confidence (≥0.978) | **22** | **3,698** | **-99.4%** |

**Critical Observation**:
- Classification is relatively intact (-2.4%)
- NER shows moderate loss (-17.8%)
- **Catastrophic collapse at confidence filtering** (-99.4%)

This suggests the models are producing predictions, but with **systematically lower confidence scores** that fail the 0.978 threshold.

---

## Hypothesis Analysis

### Hypothesis 1: Wrong Training Data (HIGH PROBABILITY)

**Evidence**:
- Training session not found locally
- Models have completely different checksums
- Small training dataset (only 307 NER samples) insufficient for robust model

**Potential Causes**:
- Trained on test split instead of training split
- Trained on subset of data (test mode left enabled?)
- Wrong CSV files loaded during training
- Data loading error in Colab

**Verification**:
- ✅ Check training session in Google Drive
- ✅ Review training logs for data file paths
- ✅ Verify sample counts in training logs
- ✅ Compare data splits used

### Hypothesis 2: Insufficient Training (MEDIUM PROBABILITY)

**Evidence**:
- Known NER dataset is very small (307 training samples)
- Previous local training showed Val F1 of only 0.732 for NER
- Classification achieved perfect training accuracy (possible overfitting)

**Potential Causes**:
- Too few training epochs
- Wrong hyperparameters (learning rate, batch size)
- Insufficient regularization
- Model didn't converge

**Verification**:
- ✅ Check training logs for epoch count and loss curves
- ✅ Verify training/validation metrics
- ✅ Compare hyperparameters to successful training runs

### Hypothesis 3: PyTorch Incompatibility Redux (MEDIUM PROBABILITY)

**Evidence**:
- Similar 99.4% loss pattern as previous checkpoint issue
- Training in Colab (PyTorch 2.8.0), inference in Colab (PyTorch 2.8.0)
- New checkpoint format may still have issues

**Potential Causes**:
- Checkpoint saving still includes problematic objects
- `weights_only=True` not used during training save
- Serialization/deserialization mismatch
- Transformers library version differences (4.35.0 → 4.57.1)

**Verification**:
- ✅ Inspect checkpoint file structure
- ✅ Verify parameter checksums after loading
- ✅ Test model loading in both PyTorch 2.2.2 and 2.8.0
- ✅ Check for custom objects in checkpoint

### Hypothesis 4: Model Corruption During Transfer (LOW PROBABILITY)

**Evidence**:
- Model checksums verified as correct during loading
- MD5 verification passed for both models

**Potential Causes**:
- File corruption during Google Drive transfer
- Incomplete file downloads
- Network transmission errors

**Verification**:
- ✅ Re-download models and verify MD5
- ✅ Compare file sizes
- ✅ Test models immediately after training in Colab

### Hypothesis 5: Configuration Error (LOW PROBABILITY)

**Evidence**:
- Models verified and loaded correctly
- No errors during inference pipeline
- Processing completed normally

**Potential Causes**:
- Wrong probability threshold
- Wrong model evaluation mode
- Tokenizer mismatch
- Wrong base model architecture

**Verification**:
- ✅ Check inference configuration
- ✅ Verify model.eval() mode
- ✅ Compare tokenizer settings
- ✅ Verify model architecture matches training

---

## Diagnostic Steps

### Phase 1: Locate and Examine Training Session (URGENT)

1. **Find Training Archive**:
   ```bash
   # Search Google Drive for training session
   # Expected location: /content/drive/MyDrive/inventory_2022/training_archives/2025-10-28-nzksic_full_training/
   ```

2. **Review Training Artifacts**:
   - Training logs (check for errors, warnings)
   - `model_manifest.json` (git commit, training metrics, data paths)
   - Training statistics CSV files
   - Validation results
   - README.md

3. **Verify Training Data**:
   - Check data file paths in logs
   - Verify sample counts (should be 1,635 classification, 554 NER)
   - Confirm correct data splits loaded
   - Check for TEST_MODE flag

### Phase 2: Model Integrity Verification

1. **Load Models Locally** (PyTorch 2.2.2):
   ```python
   import torch
   from src.model_traceability import compute_parameter_checksum

   # Load new model
   new_model = torch.load('path/to/new/model.pt', map_location='cpu')
   new_checksum = compute_parameter_checksum(new_model)

   # Load old model
   old_model = torch.load('path/to/old/model.pt', map_location='cpu')
   old_checksum = compute_parameter_checksum(old_model)

   # Compare
   print(f"New: {new_checksum}")
   print(f"Old: {old_checksum}")
   ```

2. **Inspect Checkpoint Structure**:
   ```python
   checkpoint = torch.load('model.pt', map_location='cpu')
   print("Keys:", checkpoint.keys())
   print("Metrics type:", type(checkpoint.get('train_metrics')))
   print("Has custom objects:", any(hasattr(v, '__module__') for v in checkpoint.values()))
   ```

3. **Test Inference on Sample Input**:
   ```python
   # Use diagnostic script to compare predictions
   # Compare logits and probabilities between old and new models
   ```

### Phase 3: Training Data Verification

1. **Check Training Dataset Integrity**:
   ```bash
   wc -l data/manual_classifications.csv  # Should be 1,636 (including header)
   wc -l data/manual_ner_extraction.csv   # Should be 555 (including header)
   ```

2. **Verify Split Generation**:
   - Check if splits were created correctly
   - Verify train/val/test proportions (70/15/15)
   - Ensure no data leakage

### Phase 4: Comparative Testing

1. **Run Both Models on Identical Input**:
   - Same paper sample (e.g., first 100 papers)
   - Compare classification predictions
   - Compare NER extractions
   - Compare confidence scores

2. **Analyze Prediction Distributions**:
   ```python
   import pandas as pd
   import matplotlib.pyplot as plt

   # Load results
   old_results = pd.read_csv('old_run/classification_results.csv')
   new_results = pd.read_csv('new_run/classification_results.csv')

   # Compare probability distributions
   plt.hist(old_results['probability'], alpha=0.5, label='Old')
   plt.hist(new_results['probability'], alpha=0.5, label='New')
   plt.legend()
   plt.show()
   ```

---

## Risk Assessment

### Impact

**Severity**: CRITICAL
- Production pipeline blocked
- Cannot generate reliable inventories
- Significant time investment in training wasted
- Unknown if issue will recur with future training

**Scope**:
- Affects all future training runs until root cause identified
- May affect models already in production if issue spreads
- Blocks modernization/improvement efforts

### Urgency

**Timeline**: IMMEDIATE ACTION REQUIRED
- Need reliable models for production runs
- Risk of repeating the issue without understanding root cause
- May indicate systematic problem in training pipeline

---

## Action Plan

### Immediate (Today)

1. ✅ **Document current status** (this report)
2. 🔲 **Locate training session 2025-10-28-nzksic** in Google Drive
3. 🔲 **Review training logs** for errors and data paths
4. 🔲 **Verify model checksums** after loading in both environments
5. 🔲 **Use old validated models** (2025-10-24-apz1py) for production

### Short-term (This Week)

1. 🔲 **Reproduce training locally** with identical data
2. 🔲 **Test models immediately after training** (in same environment)
3. 🔲 **Implement automated quality checks** after training
4. 🔲 **Add diagnostic logging** to training pipeline
5. 🔲 **Document training data versioning**

### Long-term (This Month)

1. 🔲 **Expand NER training dataset** (307 samples insufficient)
2. 🔲 **Implement model registry** with checksums and validation
3. 🔲 **Add automated comparison tests** between training runs
4. 🔲 **Establish model quality gates** before production deployment
5. 🔲 **Create training reproducibility checklist**

---

## Lessons from Previous Issues

### From PYTORCH_CHECKPOINT_FIX.md

**Critical Insights**:
1. **Silent corruption is the worst kind** - Same file, different results
2. **Don't assume the obvious culprit** - Name processing looked broken but wasn't
3. **Verify data lineage** - Check session IDs and data sources between steps
4. **Checksum everything** - Parameters, data, intermediate results
5. **Avoid checkpoint systems** - Added complexity, integrity risks

**Applicable to Current Issue**:
- ✅ Verify parameter checksums after loading
- ✅ Check for custom objects in checkpoints
- ✅ Test in target environment immediately
- ✅ Compare intermediate results, not just final output
- ✅ Document complete data lineage

### Red Flags to Watch For

1. **Missing training sessions** ← **CURRENT ISSUE**
2. Different model checksums without explanation ← **CURRENT ISSUE**
3. Drastically different performance without code changes ← **CURRENT ISSUE**
4. Row count changes between pipeline steps
5. Probability distribution shifts
6. Confidence score drops > 5%
7. Parameter checksum mismatches after loading

---

## Next Steps

### Required Information

To continue investigation, we need:

1. **Training session location**:
   - Google Drive path for 2025-10-28-nzksic
   - Training logs and manifests
   - Model files for local testing

2. **Training parameters**:
   - Data files used
   - Epoch count and hyperparameters
   - Training/validation metrics
   - Any errors or warnings

3. **Environment details**:
   - PyTorch version during training
   - Transformers version
   - GPU type
   - Colab runtime information

### Investigation Priority

**HIGHEST PRIORITY**: Locate training session 2025-10-28-nzksic
- This will reveal training data, parameters, and logs
- May immediately explain the degradation
- Required to determine if training can be salvaged

**HIGH PRIORITY**: Verify checkpoint format
- Check for custom objects
- Test loading in different PyTorch versions
- Compute parameter checksums

**MEDIUM PRIORITY**: Comparative testing
- Run both models on identical inputs
- Analyze prediction distributions
- Identify systematic differences

---

## References

- **Previous Investigation**: `/Users/warren/development/GBC/inventory_2022/docs/PYTORCH_CHECKPOINT_FIX.md`
- **Comparison Report**: `/Users/warren/development/GBC/inventory_2022/INVENTORY_COMPARISON_REPORT_2025-10-28.md`
- **Training Logs**: `/Users/warren/development/GBC/inventory_2022/logs/full_training_2025-10-21_14-36-32.log`
- **Old Model Results**: `/Users/warren/development/GBC/inventory_2022/collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/`
- **New Model Results**: `/Users/warren/development/GBC/inventory_2022/collab_results/2025-10-28-gl3fd6_2022_rerun/`

---

**Report Status**: DRAFT - Awaiting training session location
**Last Updated**: 2025-10-28
**Next Update**: After locating training session 2025-10-28-nzksic
