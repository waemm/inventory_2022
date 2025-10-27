# NER Predict Diagnostic Version - Usage Guide

**Created**: 2025-10-24
**Purpose**: Diagnose and fix probability calculation issues in Google Colab

---

## What This Does

This diagnostic version of `ner_predict.py` includes:

1. **Detailed logging** of the first prediction to show:
   - Model state (training vs eval mode)
   - Input/logits dtype and device
   - Logits value range
   - Comparison between default and float32 softmax outputs

2. **Float32 fix** applied automatically:
   - Converts logits to float32 before softmax calculation
   - Should fix PyTorch 2.8 dtype issues

3. **Diagnostic output** that lets you see exactly what's happening with probability calculations

---

## How to Use in Google Colab

### Option 1: Replace the script call (Recommended)

In your Colab notebook, when calling NER prediction, use:

```python
# Instead of:
# python src/ner_predict.py -i <input> -o <output> -c <model>

# Use:
python src/ner_predict_diagnostic.py -i <input> -o <output> -c <model>
```

Or if using `run_prediction_script()` utility function:

```python
# In rerun_utils.py or your notebook cell
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

### Option 2: Temporarily replace original (For testing)

```bash
# In Colab, backup and replace
!mv src/ner_predict.py src/ner_predict_original_backup.py
!cp src/ner_predict_diagnostic.py src/ner_predict.py

# Run your pipeline normally

# Restore when done
!mv src/ner_predict_original_backup.py src/ner_predict.py
```

---

## What to Look For

### Successful Fix Indicators

After running with the diagnostic version, look for these signs of success:

1. **Diagnostic output shows**:
   ```
   Logits dtype: torch.float16 or torch.float32
   Default softmax dtype: <class 'numpy.float32'>
   Float32 softmax dtype: <class 'numpy.float32'>
   ```

2. **Probability differences**:
   - If `Max difference: 0.00000000` → dtypes were already compatible
   - If `Max difference: > 0.001` → the fix is making a difference!

3. **Final results**:
   - Check `ner/predictions.csv` - should have many more rows
   - Check `processed_names/predictions.csv` - probabilities should be higher
   - Run comparison script - should show >80% passing 0.978 threshold

### Problem Indicators

If you still see low probabilities after using this version:

1. **Check diagnostic output** - save the first few lines
2. **Check logits dtype** - if it's bfloat16, that's unusual
3. **Check differences** - if Max difference is large (>0.1), there's a dtype mismatch

---

## Expected Diagnostic Output

### Good Output (Fix Working)

```
======================================================================
DIAGNOSTIC INFO - First Prediction
======================================================================
Model training mode: False
Input device: cuda:0
Input dtype: torch.int64

Logits shape: torch.Size([1, 147, 3])
Logits dtype: torch.float32
Logits device: cuda:0
Logits range: [-3.123456, 4.567890]

--- Softmax Comparison ---
Default softmax dtype: <class 'numpy.float32'>
Float32 softmax dtype: <class 'numpy.float32'>

Sample probabilities (first 3 tokens):
  Token 0: pred=0, default_prob=0.998765, float32_prob=0.998765
  Token 1: pred=1, default_prob=0.995432, float32_prob=0.995432
  Token 2: pred=2, default_prob=0.987654, float32_prob=0.987654

Probability differences:
  Max difference: 0.00000000
  Mean difference: 0.00000000
======================================================================
```

### Bad Output (Dtype Problem Detected)

```
======================================================================
DIAGNOSTIC INFO - First Prediction
======================================================================
Model training mode: False
Input device: cuda:0
Input dtype: torch.int64

Logits shape: torch.Size([1, 147, 3])
Logits dtype: torch.float16  ← PROBLEM: Using float16
Logits device: cuda:0
Logits range: [-3.125000, 4.562500]

--- Softmax Comparison ---
Default softmax dtype: <class 'numpy.float32'>
Float32 softmax dtype: <class 'numpy.float32'>

Sample probabilities (first 3 tokens):
  Token 0: pred=0, default_prob=0.125678, float32_prob=0.998765  ← BIG DIFFERENCE
  Token 1: pred=1, default_prob=0.087432, float32_prob=0.995432  ← BIG DIFFERENCE
  Token 2: pred=2, default_prob=0.056234, float32_prob=0.987654  ← BIG DIFFERENCE

Probability differences:
  Max difference: 0.87343200  ← LARGE DIFFERENCE = DTYPE ISSUE CONFIRMED
  Mean difference: 0.45678900
======================================================================
```

---

## Comparing Results

After running the diagnostic version, compare with final inventory:

```bash
# Run comparison
python compare_inventory_results.py \
  collab_results/YOUR_RUN_DIR/final_inventory.csv \
  data/final_inventory_2022.csv \
  -o collab_results/YOUR_RUN_DIR/comparison_diagnostic \
  -n1 "Diagnostic Rerun" \
  -n2 "Final Inventory"
```

**Success criteria**:
- Resources passing threshold should jump from ~29 to ~2,500+
- Resource overlap should be >80% (vs previous 0.64%)

---

## Next Steps Based on Results

### If Fix Works ✅
1. Update `src/ner_predict.py` with the float32 conversion (line 295)
2. Remove diagnostic logging
3. Document the fix in changelog
4. Update Colab notebook to use fixed version

### If Fix Doesn't Work ⚠️
1. Save the diagnostic output
2. Check if logits are bfloat16 (uncommon dtype)
3. Try Phase 2 tests from investigation document
4. Consider library version downgrade

---

## Additional Diagnostics

If you want more detailed output, you can modify line 262 to log more predictions:

```python
# Log first 10 predictions instead of just 1
should_log = predict_sequence.call_count <= 10
```

Or add this at the end of main() to print library versions:

```python
print(f"\n{'='*70}")
print("Environment Information")
print(f"{'='*70}")
print(f"PyTorch version: {torch.__version__}")
print(f"Transformers version: {transformers.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"Device count: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.current_device()}")
print(f"{'='*70}\n")
```

---

## Questions?

If you see unexpected behavior, check:
1. The diagnostic output (first prediction)
2. The probability differences (should be small if dtypes match)
3. The final results counts (should be much higher)

Report back with the diagnostic output for further investigation.
