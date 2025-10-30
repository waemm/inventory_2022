# Parameter Optimization Clarification - Why We Got It Wrong

**Date**: 2025-10-30
**Issue**: Confusion about "optimal" learning rates from first experimental session

---

## The Mistake

### What We Did (Session 2025-10-29-4lblwv)

**Tested 4 learning rate configurations using SciBERT:**

| Experiment | Classif LR | NER LR | Classif F1 | NER F1 |
|------------|------------|--------|------------|--------|
| exp1_baseline | 2e-5 ✅ | 3e-5 | 0.873 | 0.624 |
| exp2_higher_lr | 5e-5 | 5e-5 | 0.877 | **0.630** ← "best" |
| exp3_lower_lr | 1e-5 ✅ | 2e-5 ✅ | **0.882** ← "best" | 0.622 |
| exp4_aggressive | 1e-4 | 8e-5 | 0.846 | 0.625 |

**Concluded:** "Optimal" parameters are classif_lr=1e-5, ner_lr=5e-5

**Applied to Session 2025-10-30-p9rat5:**
- Used these "optimal" LRs with original RoBERTa model
- Result: NER F1 = 0.670 (still 10.5% below V2 baseline)

---

## Why This Was Wrong

### Issue 1: Different Model

**Session 2025-10-29-4lblwv used:**
- Model: `allenai/scibert_scivocab_uncased`
- SciBERT is a lighter, different architecture
- Has different optimal learning rates than RoBERTa

**V2 Production uses:**
- Model: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500`
- Domain-adapted RoBERTa with TAPT
- Requires different hyperparameters

**Learning:** Optimal LRs for SciBERT ≠ Optimal LRs for RoBERTa

---

### Issue 2: Different Data Splits

**Session 2025-10-29-4lblwv used:**
- Classification: `data/classif_splits_exp_2025-10-29-4lblwv` (session-specific)
- NER: `data/ner_splits_exp_2025-10-29-4lblwv` (session-specific)
- **Cannot compare to V2 baseline** (uses different train/val/test splits)

**V2 Production uses:**
- Classification: `data/classif_splits_full/`
- NER: `data/ner_splits_full/`
- Fixed production splits for reproducibility

**Learning:** Results on different splits cannot be used to select "optimal" parameters

---

### Issue 3: All NER Results Were Terrible

**Session 2025-10-29-4lblwv NER performance:**
- Best: 0.630 (exp2_higher_lr with 5e-5)
- V2 Baseline: 0.749
- **Gap: -15.9%**

**RED FLAG WE MISSED:**
- Even the "best" configuration was 16% below baseline
- This should have indicated our parameter search wasn't working
- We should NOT have concluded these were "optimal"

**Learning:** If all results are bad, don't pick the "least bad" as optimal

---

### Issue 4: Different Batch Size and Early Stopping

**Session 2025-10-29-4lblwv used:**
- Batch size: 32
- Early stopping: YES (patience=3)

**V2 Production uses:**
- Batch size: 16
- Early stopping: NO (trains full 10 epochs)

**Learning:** Multiple variables changed → cannot isolate LR effect

---

## What We Should Have Done

### Correct Experimental Design

**Step 1:** Test V2's EXACT configuration first (baseline reproduction)
```python
{
    'model': 'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500',
    'classif_lr': 2e-5,
    'ner_lr': 2e-5,
    'batch_size': 16,
    'epochs': 10,
    'early_stopping': False,
    'splits': 'data/classif_splits_full/'  # Production splits
}
```

**Expected Result:** Should match V2 baseline (Classif F1=0.898, NER F1=0.749)

**Step 2:** ONLY THEN test variations
- If baseline matched → try LR variations around 2e-5
- If baseline not matched → investigate what's different
- Always use same model and splits as baseline

---

## Why We Were Misled

### The "Optimal" Learning Rates Were Actually Wrong

**What we thought:**
- Classif LR: 1e-5 (from SciBERT exp3)
- NER LR: 5e-5 (from SciBERT exp2)

**What V2 actually uses:**
- Classif LR: 2e-5 (from snakemake config)
- NER LR: 2e-5 (from snakemake config)

**Our mistake:**
1. Chose best results from SciBERT experiments
2. Applied those LRs to RoBERTa model
3. Different model = different optimal LRs
4. Results: 10-16% below baseline

---

## The Actual Timeline

### Session 2025-10-29-4lblwv (October 29)
- **Goal:** Test experimental infrastructure
- **Model:** SciBERT (NOT V2's model)
- **Splits:** Session-specific (NOT production splits)
- **Result:** Infrastructure validated, but wrong "optimal" LRs identified
- **Mistake:** Concluded 1e-5/5e-5 were optimal based on SciBERT

### Session 2025-10-30-p9rat5 (October 30)
- **Goal:** Test modern models with "optimal" LRs
- **Model:** Correct models including V2's RoBERTa
- **Splits:** Production splits ✅
- **LRs:** Wrong LRs (1e-5/5e-5 from SciBERT session)
- **Result:** All models 10-16% below baseline
- **Conclusion:** "Optimal" LRs were wrong

### Today (October 30 - Investigation)
- **Goal:** Find V2's actual configuration
- **Source:** snakemake config files
- **Discovery:** V2 uses 2e-5 for BOTH models
- **Realization:** We tested the right LR but with wrong model in first session

---

## The Correct V2 Baseline Configuration

```yaml
Model: allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500

Classification:
  learning_rate: 2e-5
  batch_size: 16
  epochs: 10
  early_stopping: false
  splits: data/classif_splits_full/

NER:
  learning_rate: 2e-5
  batch_size: 16
  epochs: 10
  early_stopping: false
  splits: data/ner_splits_full/

Expected Performance:
  Classification F1: 0.898
  NER F1: 0.749
```

---

## Lessons Learned

### 1. Always Reproduce Baseline First
- Never skip baseline reproduction
- Verify you can match production performance
- Only then start optimization

### 2. Don't Mix Variables
- Session 1: Different model + Different splits + Different batch size
- Can't conclude anything about optimal LRs
- Control for all variables except the one you're testing

### 3. Red Flags Indicate Bigger Problems
- Session 1: Best NER = 0.630 (16% below baseline)
- Should have stopped and investigated
- Don't pick "least bad" as "optimal"

### 4. Model-Specific Hyperparameters
- SciBERT optimal LRs ≠ RoBERTa optimal LRs
- Can't transfer hyperparameters between different models
- Each model needs its own tuning

### 5. Fixed Splits Are Essential
- Session-specific splits prevent baseline comparison
- Always use production splits for valid comparisons
- Random splits introduce uncontrolled variance

---

## Next Steps (Corrected)

### Phase 0: V2 Baseline Reproduction ✅ (Priority 1)

**Configuration:**
```python
{
    'name': 'v2_exact_reproduction',
    'model_name': 'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500',
    'classif_lr': 2e-5,  # V2 actual value
    'ner_lr': 2e-5,      # V2 actual value
    'batch_size': 16,    # V2 actual value
    'epochs': 10,        # V2 actual value
    'early_stopping': False,  # V2 doesn't use it
    'splits': 'production'    # Fixed splits
}
```

**Success Criteria:**
- Classification F1 ≈ 0.898 (±0.02)
- NER F1 ≈ 0.749 (±0.02)
- If matched: Phase 0 complete, proceed to Phase 1
- If not matched: Investigate further

### Phase 1: Systematic Optimization (After Phase 0)

**Only after matching V2 baseline, test variations:**

**Learning Rate Sweep (around V2's 2e-5):**
```python
configurations = [
    {'classif_lr': 1e-5, 'ner_lr': 1e-5},   # Lower
    {'classif_lr': 1.5e-5, 'ner_lr': 1.5e-5}, # Slightly lower
    {'classif_lr': 2e-5, 'ner_lr': 2e-5},   # V2 baseline
    {'classif_lr': 3e-5, 'ner_lr': 3e-5},   # Slightly higher
    {'classif_lr': 4e-5, 'ner_lr': 4e-5},   # Higher
]
```

**Modern Model Testing (with V2's LR):**
```python
models = [
    'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500',  # V2 baseline
    'michiyasunaga/BioLinkBERT-base',                      # Modern SOTA
    'microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext',
]
# All use classif_lr=2e-5, ner_lr=2e-5 as starting point
```

---

## Conclusion

**We DID test V2's learning rate (2e-5) in the first session, but:**
1. Used it with the wrong model (SciBERT)
2. Used it with the wrong data splits (session-specific)
3. Mixed it with other wrong parameters (batch size 32, early stopping)
4. Got terrible results (NER 0.624, 16% below baseline)
5. Incorrectly concluded other LRs were "better"
6. Applied those wrong LRs to the correct model in second session
7. Still got terrible results (10-16% below baseline)

**The fix:**
- Use V2's exact configuration: 2e-5 for both models
- Use V2's exact model: allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500
- Use V2's exact splits: production splits
- Use V2's exact settings: batch_size=16, no early stopping
- Should match V2 baseline (0.749 NER, 0.898 Classification)

**Confidence:** 95% that this will work based on snakemake config evidence.

---

**Document Created**: 2025-10-30
**Purpose**: Clarify confusion about "optimal" learning rates from first experimental session
**Impact**: Explains why session 2025-10-30-p9rat5 underperformed despite using "optimal" LRs
