# Critical Learnings & Best Practices - Biodata Inventory Pipeline

**Created**: 2025-11-04
**Purpose**: Document critical issues, solutions, and best practices learned during development
**Audience**: AI agents and developers working on the pipeline

---

## Critical Issues Resolved

### 1. PyTorch Checkpoint Compatibility (2025-10-27)

**Problem**: Models trained in PyTorch 2.0.0 experienced 99% prediction loss when loaded in PyTorch 2.8.0 (Colab environment) due to NamedTuple deserialization issues.

**Root Cause**: Checkpoint files contained NamedTuple objects that PyTorch 2.8 deserializes incorrectly, corrupting model weights.

**Solution**:
- Converted checkpoints to dict-only format with backward-compatible loading
- Use `weights_only=True` flag when loading
- Modified Colab notebook to prevent model overwriting

**Impact**: Saved ~9.5 hours of retraining time, enabled seamless cross-platform deployment.

**Reference**: See `docs/PYTORCH_CHECKPOINT_FIX.md` for complete technical details.

---

### 2. Checkpoint Corruption in Rerun Pipeline (2025-10-28)

**Problem**: One Colab run showed 24% drop in confidence scores (74% vs 97% local) due to checkpoint system loading cached results from a different run.

**Evidence**:
- 825 rows lost during URL extraction step
- 125 mismatched IDs between pipeline steps
- 0% probability match between NER and URL extraction outputs

**Root Cause**: Checkpoint loading system mixed data from different pipeline sessions, causing data contamination.

**Resolution**: **Deprecated checkpoint functionality** from rerun pipeline. System runs fast enough (~10 minutes) that checkpointing adds unnecessary complexity and data integrity risks.

**Reference**: See `docs/PYTORCH_CHECKPOINT_FIX.md` (Addendum) for complete investigation.

---

### 3. Model Training Quality Issues (2025-10-29)

**Problem**: Newly trained models (October 28, 2025) showed 99.4% prediction loss despite correct checkpoint format and architecture.

**Root Cause**: Poor training quality - NER model achieved only F1=0.653 vs expected F1=0.749 due to:
- Learning rate too high (2e-5)
- Insufficient regularization (no weight decay)
- Training instability (F1 bouncing, peak at epoch 4 then decline)
- Overfitting (train F1=0.974 vs val F1=0.621, gap of 0.353)

**Solution**: Identified optimal training hyperparameters:
- Lower learning rate: 1e-5 or 5e-6
- Weight decay: 0.01
- Increased dropout: 0.2-0.3
- Early stopping: Monitor validation F1, stop if no improvement for 3 epochs
- More epochs: 15-20 with early stopping

**Impact**: Established training quality validation checklist, V2 models validated for production use.

**Reference**: See `docs/FINAL_DIAGNOSIS_SUMMARY.md` and `docs/MODEL_DEGRADATION_ROOT_CAUSE_ANALYSIS.md`

---

## Best Practices Established

### 1. No Checkpoint Systems
**Principle**: Each pipeline run produces completely fresh results

**Rationale**:
- Eliminates cross-contamination risk
- Simplifies debugging and validation
- Maintains data integrity across all steps

**Application**: Deprecated checkpoints in rerun_2022_inventory_simplified.ipynb

---

### 2. Data Integrity Validation
**Principle**: Always verify between pipeline steps

**Checks Required**:
- Row counts match expectations
- IDs are consistent across steps
- Sample values validate correctly
- Probability distributions remain stable

**Application**: Implemented systematic validation in all notebooks

---

### 3. Diagnostic Methodology
**Principle**: Evidence-based investigation

**Approach**:
- Check each pipeline step independently
- Compare row counts and IDs between consecutive steps
- Validate sample data matches expectations
- Don't assume obvious culprits without evidence

**Application**: Used to diagnose checkpoint corruption and training quality issues

---

### 4. Version Control for PyTorch Models
**Principle**: Ensure cross-platform compatibility

**Requirements**:
- Use dict-only checkpoint format
- Load with `weights_only=True`
- Maintain parameter checksums for validation
- Document version compatibility explicitly

**Application**: V2 models work on both local (PyTorch 2.2.2) and Colab (PyTorch 2.8.0)

---

### 5. Training Quality Validation
**Principle**: Validate before deployment

**Checklist**:
- [ ] Validation F1 > 0.70 for NER, > 0.85 for classification
- [ ] Test F1 matches validation F1 (±0.02)
- [ ] Training shows steady improvement (no bouncing)
- [ ] Train/val gap < 0.15 (acceptable overfitting)
- [ ] Test inference produces expected high-confidence predictions (>80% at threshold 0.978)
- [ ] Compare with baseline inventory (>75% overlap)

**Application**: Required before any model deployment to production

---

## Operational Recommendations

### For Future Development

1. **Keep pipeline architecture simple and linear**
   - Avoid premature optimization (e.g., checkpointing for 10-minute runs)
   - Prioritize data integrity over convenience features

2. **Avoid checkpointing unless runtime > 1 hour**
   - Short pipelines don't benefit from checkpoints
   - Risk of data contamination outweighs benefits

3. **Test cross-platform compatibility explicitly**
   - Test models in both local and Colab environments
   - Verify predictions match across platforms

4. **Document all technical decisions and rationale**
   - Future agents need context for decisions
   - Include why alternatives were rejected

---

### For Production Use

1. **Use fresh runs without checkpoints**
   - Start from scratch each time
   - Eliminates contamination risk

2. **Validate output statistics match expectations**
   - Check row counts at each step
   - Compare probability distributions with baseline

3. **Archive complete session results with traceability**
   - Store models, logs, and metrics together
   - Use unique session IDs for tracking

4. **Reference clean baseline runs for comparison**
   - Maintain known-good runs for validation
   - Compare new runs against baselines

5. **Monitor for unexpected probability distributions**
   - Check high-confidence prediction rates
   - Flag unusual distributions early

---

## Training-Specific Best Practices

### Avoid These Training Issues

**❌ DO NOT**:
- Use learning rate 2e-5 for NER (too high, causes instability)
- Skip weight decay (causes overfitting on small dataset)
- Train without early stopping (leads to overfitting)
- Ignore validation curve instability (sign of poor training)
- Deploy without testing on sample data
- Use checkpoints with NamedTuple objects

**✅ DO**:
- Monitor validation curves during training
- Stop at first sign of sustained decline
- Test models immediately after training
- Compare with baseline before deployment
- Document training parameters and results
- Use dict-only checkpoint format

---

### Training Data Limitations

**Current Datasets**:
- Classification: 1,635 samples (adequate)
- NER: 554 samples (small - requires careful hyperparameters)

**Impact**: Small NER dataset is highly sensitive to:
- Learning rate (must be low: 5e-6)
- Regularization (weight decay essential)
- Data splits (random seed affects performance)

**Long-term Goal**: Expand NER dataset to 1,000-2,000 samples for more robust training.

---

## Documentation References

**Primary Technical Documents**:
- **FINAL_DIAGNOSIS_SUMMARY.md**: Complete model quality investigation summary
- **MODEL_DEGRADATION_ROOT_CAUSE_ANALYSIS.md**: Detailed technical analysis of training quality issues
- **PYTORCH_CHECKPOINT_FIX.md**: Complete resolution of PyTorch compatibility and checkpoint corruption
- **INVENTORY_COMPARISON_REPORT_2025-10-28.md**: Detailed comparison and quality validation
- **CRITICAL_INVESTIGATION_2025-10-28.md**: Investigation process and diagnostic methodology
- **COMPARISON_SUMMARY.txt**: Quick reference summary of model comparisons

---

**Document Status**: ✅ Current and accurate
**Last Updated**: 2025-11-04
**Next Review**: After major incidents or new critical learnings
