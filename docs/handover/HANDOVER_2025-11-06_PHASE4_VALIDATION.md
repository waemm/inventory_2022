# Phase 4 Validation & 2-Model Strategy Investigation

**Date**: 2025-11-06
**Session Duration**: ~2 hours
**Status**: ⚠️ **CRITICAL FINDINGS - Phase 4 Performance Issues Identified**

---

## Executive Summary

This session investigated the Phase 4 entity extraction bug and planned a simplified 2-model NER training strategy. While we confirmed Phase 4's output format is clean (no BPE tokenization artifacts), **entity-level F1 evaluation revealed catastrophically poor performance: 16.77% F1 vs. target of 60%**.

### Key Findings:
- ✅ **Format validation PASSED**: Zero BPE artifacts detected on 66 test papers
- ❌ **Performance validation FAILED**: 16.77% F1 (83.23 points below target)
- ⚠️ **Critical Issue**: Only 15.76% recall - Phase 4 misses 84% of ground truth entities
- 🚨 **Strategic Impact**: Cannot rely on Phase 4 for hybrid 2-model pipeline as planned

---

## Session Objectives

### Primary Goals:
1. ✅ Validate Phase 4 entity extraction bug fix (format check)
2. ✅ Run proper entity-level F1 evaluation (performance check)
3. ⏸️ **PAUSED**: Plan and implement 2-model training strategy (blocked by findings)

### Original Plan (Now Under Review):
- **Model 1**: Classification with 28 metadata features (fail-fast if F1 < 90%)
- **Model 2**: Short entity NER (≤2 words, 89.9% of entities, target F1 ≥ 80%)
- **Model 3**: Reuse Phase 4 for long entities (>2 words, 10.1% of entities)
- **Expected Overall F1**: 75-80%

**⚠️ BLOCKED**: Phase 4's 16.77% F1 invalidates strategy assuming it handles long entities well.

---

## Work Completed

### 1. Phase 4 Format Validation ✅

**Script**: `validate_phase4_fix.py`

**Purpose**: Verify Phase 4's entity extraction produces clean, word-level entities without BPE tokenization artifacts.

**Methodology**:
- Loaded Phase 4 checkpoint: `collab_results/experiment_archives/2025-10-31-rq7i4n/multitask_training/checkpoint_best_ner.pt`
- Tested on all 66 unique papers from test split
- Checked each entity for:
  - 'Ġ' prefix (BPE space indicator)
  - Comma-separated tokens (e.g., "ĠRat, ĠGen, ome")

**Results**:
```
📊 Test Statistics:
   Papers tested: 66
   Papers with entities: 60 (90.9%)
   Total entities extracted: 367
   Avg entities per paper: 5.56

🔍 Entity Quality Check:
   Papers with issues: 0
   Clean papers: 66 (100%)

✅ ALL TESTS PASSED
   No BPE tokenization artifacts detected
```

**Sample Clean Entities**:
- ✅ "Rat Genome Database" (not "ĠRat, ĠGen, ome, ĠDatabase")
- ✅ "Animal Sex Reversal Database"
- ✅ "Plant Metabolic Network"
- ✅ "qtlXplorer"

**Conclusion**: Phase 4 uses correct function (`extract_entities_word_level()`) and produces properly formatted output.

**Files Created**:
- `validate_phase4_fix.py` - Format validation script
- `PHASE4_VALIDATION_REPORT.md` - Format validation summary

---

### 2. Entity-Level F1 Evaluation ❌

**Script**: `evaluate_phase4_entity_f1.py`

**Purpose**: Proper validation comparing Phase 4 predictions against ground truth entities from test split.

**Methodology**:
- Loaded ground truth from: `data/ner_splits_full/test_ner.pkl` (608 sentences, 66 papers)
- Ran Phase 4 inference on same test papers
- Extracted entities using `extract_entities_word_level()`
- Compared predictions vs ground truth (entity-level, case-insensitive)
- Calculated precision, recall, F1 using entity matching (not token-level)

**Results**:
```
🎯 Entity-Level Metrics (Micro-averaged):
   Precision: 17.93% (26 correct / 145 predicted)
   Recall:    15.76% (26 found / 165 ground truth)
   F1 Score:  16.77%

📈 Entity Counts:
   Ground truth entities: 165
   Predicted entities: 145
   True Positives: 26
   False Positives: 119 (82% of predictions wrong!)
   False Negatives: 139 (84% of ground truth missed!)

📊 Per-Paper F1 Statistics:
   Mean F1: 0.2700
   Median F1: 0.0000 (half the papers had ZERO correct predictions)
   Std Dev: 0.3290
   Min F1: 0.0000
   Max F1: 1.0000

🎯 Target Evaluation:
   ❌ BELOW TARGET: F1 0.1677 << target 0.6000
   Gap: -43.23 percentage points
```

**Critical Analysis**:
- **Only 26/165 ground truth entities correctly identified** (15.76% recall)
- **119/145 predictions were false positives** (82% precision failure)
- **Median F1 of 0.0** indicates systemic failure, not random errors
- Performance is 43 percentage points below minimum acceptable threshold

**Files Created**:
- `evaluate_phase4_entity_f1.py` - Entity-level F1 evaluation script
- `phase4_entity_evaluation_results.csv` - Per-paper detailed metrics
- `phase4_evaluation_output.log` - Full evaluation console output

---

## Critical Findings & Root Cause Analysis

### Finding 1: Format vs. Performance Disconnect

**Observation**: Phase 4 produces clean, properly formatted entities BUT very few are correct.

**Examples of Format Success**:
- No tokenization artifacts detected
- Multi-word entities preserved as single strings
- Whitespace handled correctly

**Examples of Performance Failure**:
- Ground truth: "Rat Genome Database" → Phase 4 prediction: None (missed)
- Ground truth: "MGI" → Phase 4 prediction: "genomic", "transcriptome" (wrong entities)

**Implication**: The bug fix works (format is clean) but the model itself has poor entity recognition.

---

### Finding 2: Possible Context Mismatch Issue

**Hypothesis**: Training vs. inference context discrepancy may explain poor performance.

**Training Context**:
- Model trained on individual sentences (from `ner_splits_full/train_ner.pkl`)
- Each training example: single sentence with labeled entities
- Average sentence length: ~40 tokens

**Inference Context**:
- Evaluation runs on full papers (title + abstract concatenated)
- Average paper length: ~200-300 tokens
- May exceed model's effective context window

**Test Needed**: Re-run evaluation on individual sentences instead of full papers to isolate issue.

---

### Finding 3: High False Positive Rate (82%)

**Observation**: Phase 4 predicts many entities that don't exist in ground truth.

**Potential Causes**:
1. **Over-prediction**: Model tags too many tokens as entities
2. **Wrong entity types**: Predicts COM when should be FUL or vice versa
3. **Boundary errors**: Extracts substrings or superstrings of correct entities
4. **Domain drift**: Test set entities differ from training distribution

**Evidence Required**: Manual inspection of false positives to categorize error types.

---

### Finding 4: Low Recall (15.76%)

**Observation**: Phase 4 misses 84% of ground truth entities.

**Potential Causes**:
1. **Context length**: Full paper context confuses sentence-trained model
2. **Tokenization**: BPE tokenizer may split entities in unexpected ways during inference
3. **Confidence thresholds**: Model may be too conservative in predictions
4. **Class imbalance**: Model may favor 'O' tag over entity tags

**Evidence Required**: Analyze false negatives to understand what types of entities are missed.

---

## Data Splits & Files Referenced

### Test Split Data:
- **Location**: `data/ner_splits_full/test_ner.pkl`
- **Size**: 608 sentences from 66 unique papers
- **Ground Truth Entities**: 165 entities total
- **Papers Not in 2022 Dataset**: 3 papers (PMIDs: 33480398, 34034817, 34167460)

### Phase 4 Model:
- **Checkpoint**: `collab_results/experiment_archives/2025-10-31-rq7i4n/multitask_training/checkpoint_best_ner.pt`
- **Training Session**: 2025-10-31-rq7i4n
- **Architecture**: BiomedicalMultiTaskModel (RoBERTa-based)
- **Metadata Features**: 28 features
- **NER Labels**: 3 (O, B-COM, I-COM)

### Papers Dataset:
- **Location**: `data/epmc_query_results_2022.csv`
- **Size**: 21,429 papers
- **Coverage**: 63/66 test papers found (95.5%)

### Metadata:
- **Location**: `data/metadata/features_engineered.csv`
- **Size**: 21,392 papers
- **Features**: 28 engineered features (10 boolean, 4 numerical, 14 TF-IDF)

---

## Documents & Code Created

### Documentation:
1. **`PHASE4_VALIDATION_REPORT.md`** - Format validation summary (clean output confirmed)
2. **`docs/handover/HANDOVER_2025-11-06_PHASE4_VALIDATION.md`** - This comprehensive report

### Scripts:
1. **`validate_phase4_fix.py`** - Format validation (checks for BPE artifacts)
   - Runtime: ~20 minutes on CPU
   - Tests: 66 papers
   - Result: ✅ PASSED

2. **`evaluate_phase4_entity_f1.py`** - Entity-level F1 evaluation
   - Runtime: ~4 minutes on CPU
   - Tests: 60 papers with ground truth entities
   - Result: ❌ FAILED (16.77% F1)

### Result Files:
1. **`phase4_entity_evaluation_results.csv`** - Per-paper metrics (precision, recall, F1, TP, FP, FN)
2. **`phase4_evaluation_output.log`** - Full evaluation console output

---

## Strategic Implications

### Original 2-Model Hybrid Strategy (NOW INVALID):

**Assumption**: Phase 4 handles long entities well (F1 ≥ 60%)
**Reality**: Phase 4 achieves only 16.77% F1 overall
**Impact**: Cannot use Phase 4 as "long entity specialist" in hybrid pipeline

### Revised Options:

#### Option A: Investigate & Fix Phase 4 Performance
**Hypothesis**: Context mismatch (sentence training vs. full paper inference)

**Action Plan**:
1. Re-run evaluation on individual sentences (not full papers)
2. Compare sentence-level vs. paper-level F1
3. If sentence-level F1 ≥ 60%, use sentence-based inference
4. If still poor, abandon Phase 4

**Timeline**: 1-2 days
**Risk**: Medium - may not resolve fundamental model issues

#### Option B: Train 3 New Models from Scratch
**Strategy**: Classification + Short NER + Long NER (no Phase 4 reuse)

**Models**:
1. Classification with metadata (target F1 ≥ 90%)
2. Short entity NER (≤2 words, 1,009 sentences, target F1 ≥ 80%)
3. Long entity NER (>2 words, 120 sentences, target F1 ≥ 60%)

**Challenges**:
- Only 120 training sentences for long entities (99% smaller than typical NER datasets)
- Requires data augmentation or transfer learning
- Longer implementation timeline (4 weeks)

**Timeline**: 4 weeks
**Risk**: High - insufficient long entity training data

#### Option C: Single Unified Model (Alternative Approach)
**Strategy**: Train one strong NER model on all entity types with data augmentation

**Advantages**:
- No entity length separation
- Simpler pipeline
- Full 1,192 training entities available

**Disadvantages**:
- Loses specialization benefits
- May not achieve 80%+ F1 on short entities

**Timeline**: 2-3 weeks
**Risk**: Medium - unknown if unified approach beats specialized models

---

## Recommended Next Steps

### Immediate (Next Session):

1. **Root Cause Investigation** (Option A - 1 day):
   - Modify `evaluate_phase4_entity_f1.py` to run sentence-level inference
   - Compare sentence-level F1 vs. paper-level F1
   - Manual inspection of 10 false positive and 10 false negative examples
   - Decision point: If sentence-level F1 ≥ 60%, proceed with Option A; otherwise Option B or C

2. **If Sentence-Level F1 ≥ 60%**:
   - Implement sentence-based inference for Phase 4
   - Proceed with 2-model hybrid strategy (Classification + Short NER + Phase 4 sentences)
   - Timeline: 3 weeks to production

3. **If Sentence-Level F1 < 60%**:
   - Abandon Phase 4 entirely
   - Choose between Option B (3-model from scratch) or Option C (1 unified model)
   - Consult with stakeholders on data augmentation budget and timeline

### Decision Matrix:

| Scenario | Next Action | Timeline | Expected F1 |
|----------|-------------|----------|-------------|
| Phase 4 sentence-level F1 ≥ 60% | Hybrid 2-model (Classification + Short NER + Phase 4) | 3 weeks | 75-80% |
| Phase 4 sentence-level F1 < 60% | 3-model from scratch (all new) | 4 weeks | 70-75% |
| Phase 4 sentence-level F1 < 60% | 1 unified model (alternative) | 2-3 weeks | 65-70% |

---

## Technical Details

### Entity Extraction Functions:

**Correct Function** (used by Phase 4):
```python
# src/multitask_predict.py:407-559
def extract_entities_word_level(text, tokenizer, input_ids, bio_tags, probabilities, id2tag):
    """
    Extract entities at word level from BPE token predictions.
    Handles word-level reconstruction correctly.
    """
```

**Deprecated Function** (NOT used):
```python
# src/multitask_predict.py:319-404
def extract_entities_from_bio_tags(tokens, bio_tags, probabilities, id2tag):
    """
    DEPRECATED: Causes entity fragmentation.
    """
```

### Evaluation Methodology:

**Entity Matching Logic**:
```python
def calculate_entity_metrics(predicted_entities, ground_truth_entities):
    # Normalize for comparison (lowercase, strip whitespace)
    pred_set = set((normalize_entity(text), etype) for text, etype, _ in predicted_entities)
    gold_set = set((normalize_entity(text), etype) for text, etype in ground_truth_entities)

    tp = len(pred_set & gold_set)  # Exact matches
    fp = len(pred_set - gold_set)  # Predicted but not in ground truth
    fn = len(gold_set - pred_set)  # In ground truth but not predicted

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall)
```

**Key Properties**:
- Entity-level (not token-level)
- Case-insensitive matching
- Exact span matching (no partial credit)
- Type-aware (COM vs. FUL must match)

---

## Environment & Configuration

### Compute:
- **Device**: CPU (MacBook Pro)
- **Model Size**: ~110M parameters (RoBERTa-base)
- **Inference Speed**: ~3-5 seconds per paper

### Python Environment:
- **Python**: 3.11
- **PyTorch**: Latest
- **Transformers**: 4.35.2
- **Key Packages**: pandas, numpy, tqdm

### Data Locations:
```
data/
├── ner_splits_full/
│   ├── train_ner.pkl (1,473 sentences, 1,192 entities)
│   ├── val_ner.pkl (318 sentences, 257 entities)
│   └── test_ner.pkl (608 sentences, 165 entities)
├── ner_splits_short/
│   ├── train_ner.pkl (1,009 sentences, 1,176 entities)
│   └── test_ner.pkl (245 sentences, 282 entities)
├── ner_splits_long/
│   ├── train_ner.pkl (120 sentences, 227 entities)
│   └── test_ner.pkl (33 sentences, 57 entities)
├── metadata/
│   └── features_engineered.csv (21,392 papers, 38 columns)
└── epmc_query_results_2022.csv (21,429 papers)
```

---

## Outstanding Questions

### Technical:
1. **Why is Phase 4's recall so low (15.76%)?**
   - Context length issue?
   - Tokenization problems?
   - Model quality issue?

2. **Why is precision poor (17.93%)?**
   - Over-prediction?
   - Wrong entity boundaries?
   - Entity type confusion?

3. **What explains the 0.0 median F1?**
   - Many papers with zero correct predictions
   - Systemic failure pattern?

### Strategic:
1. **Is sentence-level inference feasible for production?**
   - Would require sentence segmentation pipeline
   - Complexity vs. accuracy trade-off

2. **Can we achieve 80%+ F1 with only 120 long entity training examples?**
   - Data augmentation sufficient?
   - Transfer learning from short entity model?

3. **Should we abandon multi-model approach entirely?**
   - Would unified model perform better?
   - Simpler deployment vs. specialization benefits

---

## Files for Review

### High Priority:
1. **`phase4_entity_evaluation_results.csv`** - Per-paper metrics (identify failure patterns)
2. **`PHASE4_VALIDATION_REPORT.md`** - Format validation summary
3. **`evaluate_phase4_entity_f1.py`** - Review evaluation logic for correctness

### Supporting Materials:
4. **`validate_phase4_fix.py`** - Format validation script
5. **`phase4_evaluation_output.log`** - Full evaluation console output
6. **`docs/NER_SYSTEM_COMPARISON.md`** - Background on V2 vs Phase 4 differences

---

## Handover Checklist

- [x] Format validation completed (clean output confirmed)
- [x] Entity-level F1 evaluation completed (poor performance identified)
- [x] Critical findings documented
- [x] Result files saved and locations documented
- [x] Scripts created and tested
- [x] Next steps identified with decision matrix
- [ ] **PENDING**: Root cause investigation (sentence-level vs. paper-level inference)
- [ ] **PENDING**: Decision on strategy (fix Phase 4 vs. train new models)
- [ ] **PENDING**: Stakeholder approval on timeline and approach

---

## Summary & Status

**Session Goal**: Validate Phase 4 and plan 2-model strategy
**Actual Outcome**: Identified critical Phase 4 performance issue blocking strategy

**What Worked**:
- ✅ Phase 4 format is clean (no BPE artifacts)
- ✅ Proper entity-level evaluation framework established
- ✅ Data splits prepared and validated

**What Failed**:
- ❌ Phase 4 entity-level F1: 16.77% (83 points below target)
- ❌ Cannot use Phase 4 in hybrid pipeline as planned
- ❌ Strategy blocked pending root cause investigation

**Critical Path**:
1. Investigate context mismatch (sentence vs. paper inference)
2. Decide: Fix Phase 4 OR train new models from scratch
3. Resume implementation based on decision

**Timeline Impact**:
- **Best Case** (sentence-level fix works): 3 weeks to production
- **Worst Case** (need to retrain): 4 weeks to production

---

**Report Created**: 2025-11-06
**Session Duration**: ~2 hours
**Next Session**: Root cause investigation + strategy decision
**Recommended Owner**: Data Science Lead + NLP Engineer

**Status**: ⚠️ **BLOCKED - Awaiting Root Cause Investigation**
