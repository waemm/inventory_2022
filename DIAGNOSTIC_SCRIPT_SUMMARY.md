# Diagnostic Script Ready for Colab Testing

**Date**: 2025-10-24
**Status**: Ready to test in Google Colab

---

## Quick Start

### In Google Colab Notebook

Replace your NER prediction call with:

```python
run_prediction_script(
    'ner_predict_diagnostic',  # Changed from 'ner_predict'
    INVENTORY_DIRECTORY,
    {
        '-i': CLASSIF_POSITIVES,
        '-o': NER_DIR,
        '-c': TARGET_NER_MODEL
    }
)
```

---

## What This Script Does

1. **Logs diagnostic info** for the first prediction:
   - Shows if logits are float16 or float32
   - Compares default vs float32 softmax outputs
   - Calculates probability differences

2. **Applies float32 fix**:
   - Converts logits to float32 before softmax
   - Uses: `torch.nn.functional.softmax(logits.float(), dim=-1)`

3. **Minimal overhead**:
   - Only logs first prediction
   - Rest of predictions run at normal speed

---

## What to Expect

### If the fix works ✅

You should see:
- Diagnostic output showing dtype info
- Many more predictions in `ner/predictions.csv`
- Higher probability scores in output
- **~2,500+ resources** passing 0.978 threshold (vs previous 29)
- **>80% overlap** with final inventory (vs previous 0.64%)

### Diagnostic Output Example

Look for something like:

```
======================================================================
DIAGNOSTIC INFO - First Prediction
======================================================================
Model training mode: False
Logits dtype: torch.float16  ← This would explain the problem
...
Probability differences:
  Max difference: 0.87343200  ← Large = dtype issue confirmed
======================================================================
```

---

## Files Created

1. **src/ner_predict_diagnostic.py** - The diagnostic script to run
2. **src/ner_predict_diagnostic_README.md** - Detailed usage guide
3. **docs/COLAB_PROBABILITY_INVESTIGATION.md** - Full investigation writeup

---

## After Testing

### If it works:
1. Share the diagnostic output
2. We'll apply the fix to main `ner_predict.py`
3. Update Colab notebook permanently

### If it doesn't work:
1. Share the diagnostic output
2. We'll try Phase 2 investigations (library versions, tokenization, etc.)

---

## The Problem We're Solving

**Colab Results** (Current - BROKEN):
- Total predictions: 3,569
- Passing threshold: **29 (0.8%)** ⚠️
- Resource overlap: **0.64%** ⚠️

**Local Results** (Working):
- Total predictions: 4,368
- Passing threshold: **3,698 (84.7%)** ✅
- Resource overlap: **82%** ✅

**Why float32 matters**: PyTorch 2.8 may default to float16 for softmax, causing numerical precision issues that result in artificially low probability scores.

---

Ready to test! 🚀
