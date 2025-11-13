# PHASE 4 SPLIT B TRAINING INVESTIGATION - SESSION 2025-11-07-f08r7d

## EXECUTIVE SUMMARY

**CRITICAL FAILURE**: The training run 2025-11-07-f08r7d **DID NOT** use Split B data as intended. Instead, it used **classification data** for NER training, resulting in complete NER system failure.

## KEY FINDINGS

### 1. DATA MISMATCH - CRITICAL ISSUE

**Expected (Split B):**
- Training samples: 2,914 (sentence-level)
- Validation samples: 594 (sentence-level)  
- B/I ratio: 2.57 (healthy multi-token entity representation)
- I-RESOURCE tags: 94 tokens (0.70% of validation)
- Multi-token entities present

**Actual (Session f08r7d):**
- Training samples: 246 (paper-level)
- Validation samples: 62 (paper-level)
- B/I ratio: 0.0 (ZERO I-tags)
- I-RESOURCE tags: 0 (completely absent)
- NO ner_tags column - used classification data!

**Evidence:**
```
Split B columns: ['pmid', 'sent_idx', 'word_idx', 'ner_tags', 'words']
Session columns: ['id', 'title', 'abstract', 'has_resource', ... metadata ...]
```

### 2. REPORTED METRICS - MISLEADING

**SESSION_SUMMARY.md claims:**
- NER F1: 0.0000 (entity-level)
- Token F1: 1.0000 (all tokens classified as 'O')

**evaluation_results.json shows:**
- B-RESOURCE support: 0 (no entities in validation!)
- I-RESOURCE support: 0 (no multi-token entities!)
- O tokens: 1,501 (100% of validation)

**The "perfect" token F1 of 1.0 is MEANINGLESS:**
- Model learned to predict only 'O' tags
- No actual entities in validation set to evaluate
- This is a data loading bug, not model success

### 3. COMPARISON TO PREVIOUS RUN (2025-11-07-rzpdmq)

**Previous run (rzpdmq):**
- Classification F1: 0.8454
- NER F1: 0.9500 (suspiciously high)
- Training: 442 samples
- Validation: 111 samples

**Current run (f08r7d):**
- Classification F1: 0.8541
- NER F1: 0.0000 (complete failure)
- Training: 246 samples
- Validation: 62 samples

**BOTH runs used wrong data format!**
- Neither used actual Split B NER data
- Both loaded classification data for NER task
- Previous "0.9500" was also invalid

### 4. TRAINING BEHAVIOR ANALYSIS

**From training_history.json:**

**Epochs 1-2:**
- Token F1 starts at 0.0057, jumps to 1.0 by epoch 2
- Entity F1: 0.0 throughout all 30 epochs
- B/I ratio: 5.0 in epoch 1, then 0.0 forever

**This indicates:**
1. Initial prediction of some B-tags (B/I ratio: 5.0)
2. Model quickly learned to suppress all entity predictions
3. Converged to "predict O for everything" strategy
4. No entities in validation = no penalty for this behavior

**Loss analysis:**
- Classification loss: 0.44 → 0.002 (normal convergence)
- NER loss: 378.7 → 0.018 (appeared to converge)
- Auxiliary loss: 1.60 → 0.76 (normal)

The NER loss decreased because predicting all 'O' is "correct" when validation has no entities!

### 5. ROOT CAUSE ANALYSIS

**Data Loading Bug:**
The training script loaded classification data (paper-level with has_resource) instead of NER data (sentence-level with ner_tags/words).

**Expected data location:**
```
data/ner_splits_splitB/train_ner.pkl
data/ner_splits_splitB/val_ner.pkl  
```

**Actual data loaded:**
```
collab_results/experiment_archives/2025-11-07-f08r7d/splits/ner_train.csv
collab_results/experiment_archives/2025-11-07-f08r7d/splits/ner_val.csv
```

**The splits/ directory contains:**
- classif_train.csv (1307 papers) - CORRECT
- classif_val.csv (327 papers) - CORRECT  
- ner_train.csv (246 papers) - WRONG FORMAT
- ner_val.csv (62 papers) - WRONG FORMAT

### 6. VERIFICATION OF SPLIT B DATA

**Split B validation data (CORRECT format):**
```
Total samples: 594 sentences
Total tokens: 13,516
- O tags: 13,180 (97.51%)
- B-RESOURCE: 242 (1.79%)
  - B-FUL: 41
  - B-COM: 201
- I-RESOURCE: 94 (0.70%)
  - I-FUL: 91 (avg 3.22 tokens/entity)
  - I-COM: 3 (avg 1.01 tokens/entity)
B/I ratio: 2.57 (healthy)
Multi-token entities: Present
```

This is the data that SHOULD have been used.

## ANSWERS TO CRITICAL QUESTIONS

### 1. Did Split B deliver expected improvements?
**NO** - Split B data was never used. Training used wrong data format.

### 2. Final scores vs baselines?
**INVALID** - Scores are meaningless due to data mismatch:
- Classification F1: 0.8541 (legitimate, but on different task)
- NER Entity F1: 0.0000 (no entities in validation = invalid test)

### 3. I-tag representation verified?
**NO** - Validation set had ZERO I-tags (should have 94)
- B/I ratio: 0.0 (should be 2.57)
- Stratification fix: Not tested (wrong data)

### 4. seqeval usage verified?
**N/A** - Can't verify entity-level metrics without entities
- Metrics tracked both token_f1 and entity_f1
- But entity_f1 = 0.0 throughout (no entities to detect)

### 5. Training quality indicators?
- Epochs: 30/30 completed
- Training time: Not recorded
- Overfitting: N/A (invalid test)
- Critical fixes applied: Unknown (wrong data loaded)

### 6. Compare to baselines?
**INVALID COMPARISON:**
- V2 NER baseline: 0.749 (sentence-level NER)
- Session f08r7d: 0.0000 (paper-level classification data)
- Comparing apples to oranges

### 7. Red flags?
**MULTIPLE CRITICAL RED FLAGS:**
1. ✓ Zero I-tags in validation (should have 94)
2. ✓ Suspiciously perfect token F1 (1.0)
3. ✓ Entity F1 = 0.0 throughout training
4. ✓ B/I ratio = 0.0 after epoch 1
5. ✓ Validation set has 62 samples (should be 594)
6. ✓ Training set has 246 samples (should be 2,914)
7. ✓ Wrong column schema (has_resource vs ner_tags)

## PRODUCTION READINESS

**STATUS: NOT PRODUCTION READY**

This model:
- Was not trained on Split B data
- Was trained on wrong data format
- Learned to suppress all entity predictions
- Cannot perform NER tasks
- All reported metrics are invalid

## RECOMMENDED ACTIONS

1. **IMMEDIATE**: Verify data loading in training script
   - Check how splits/ directory is created
   - Ensure Split B .pkl files are loaded, not .csv
   
2. **FIX**: Correct data pipeline
   - Load from data/ner_splits_splitB/
   - Verify ner_tags column exists
   - Validate B/I ratio before training

3. **RERUN**: Complete training with correct data
   - Use actual Split B training (2,914 samples)
   - Validate on Split B validation (594 samples)
   - Monitor B/I ratio during training

4. **VALIDATE**: Post-training checks
   - Entity F1 > 0.0 (should be ~0.72-0.73)
   - B/I ratio in validation (should be ~2.57)
   - I-tags present in predictions

## FILES ANALYZED

- /Users/warren/development/GBC/inventory_2022/collab_results/experiment_archives/2025-11-07-f08r7d/SESSION_SUMMARY.md
- /Users/warren/development/GBC/inventory_2022/collab_results/experiment_archives/2025-11-07-f08r7d/multitask_training/evaluation_results.json
- /Users/warren/development/GBC/inventory_2022/collab_results/experiment_archives/2025-11-07-f08r7d/multitask_training/config.json
- /Users/warren/development/GBC/inventory_2022/collab_results/experiment_archives/2025-11-07-f08r7d/multitask_training/training_history.json
- /Users/warren/development/GBC/inventory_2022/collab_results/experiment_archives/2025-11-07-f08r7d/splits/ner_val.csv (WRONG)
- /Users/warren/development/GBC/inventory_2022/data/ner_splits_splitB/val_ner.pkl (CORRECT)

---

**Investigation completed**: 2025-11-07
**Investigator**: Claude Code Analysis
**Severity**: CRITICAL - Complete NER system failure due to data mismatch
