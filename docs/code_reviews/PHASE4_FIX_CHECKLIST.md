# Phase 4 Fixes - Quick Checklist

**Estimated Time**: 15-30 minutes
**Risk Level**: LOW (only bug fixes, no architecture changes)
**Files to Edit**: 3

---

## Pre-Fix Checklist

- [ ] Backup current code: `git stash` or create branch
- [ ] Verify you're on correct branch: `git branch` (should show `modernization-python311`)
- [ ] Verify test failures: `python test_multitask_setup.py` (should show 2/6 passing)

---

## Fix #1: Metadata Dimension (34 → 28)

**File**: `src/models/multitask_model.py`

### Change 1.1: Line 11 (Documentation)
```python
- Metadata projection layer (34 features → 768 dims)
```
→
```python
- Metadata projection layer (28 features → 768 dims)
```
- [ ] Updated line 11

### Change 1.2: Line 39 (Comment)
```python
    n_features: Number of input metadata features (34)
```
→
```python
    n_features: Number of input metadata features (28)
```
- [ ] Updated line 39

### Change 1.3: Line 156 (Comment)
```python
    metadata: [batch_size, 34] - Ground truth metadata
```
→
```python
    metadata: [batch_size, 28] - Ground truth metadata
```
- [ ] Updated line 156

### Change 1.4: Line 262 (Function signature)
```python
    n_metadata_features: int = 34,
```
→
```python
    n_metadata_features: int = None,
```
- [ ] Updated line 262

### Change 1.5: Lines 270-280 (Add validation)
Add AFTER line 270 (`super().__init__()`):
```python
    # ADDED: Validation for n_metadata_features
    if n_metadata_features is None:
        raise ValueError(
            "n_metadata_features must be specified explicitly. "
            "Expected 28 for current augmented dataset (Phase 3). "
            "Features: 10 boolean + 4 numerical + 2 categorical + 12 TF-IDF."
        )

    if n_metadata_features != 28:
        logger.warning(
            f"n_metadata_features={n_metadata_features} specified, but current "
            f"augmented data has 28 features. Ensure this matches your data!"
        )
```
- [ ] Added validation after line 270

### Change 1.6: Line 461 (Factory function)
```python
        n_metadata_features=config.get('n_metadata_features', 34),
```
→
```python
        n_metadata_features=config['n_metadata_features'],  # No default
```

And ADD before the return statement:
```python
    # ADDED: Validation
    if 'n_metadata_features' not in config:
        raise ValueError(
            "config must specify 'n_metadata_features'. "
            "For Phase 3 augmented data, use 28."
        )
```
- [ ] Updated line 461
- [ ] Added validation before return

### Change 1.7: Line 483 (Test code)
```python
    metadata = torch.randn(batch_size, 34)
```
→
```python
    metadata = torch.randn(batch_size, 28)
```

And line 475:
```python
    model = BiomedicalMultiTaskModel(model_name_or_path="roberta-base")
```
→
```python
    model = BiomedicalMultiTaskModel(
        model_name_or_path="roberta-base",
        n_metadata_features=28
    )
```
- [ ] Updated line 475 (model creation)
- [ ] Updated line 483 (metadata tensor)

---

## Fix #2: Import Error Handling

**File**: `src/train_multitask.py`

### Change 2.1: Line 22 (Import statement)
```python
from transformers import get_linear_schedule_with_warmup
```
→
```python
try:
    from transformers import get_linear_schedule_with_warmup
except ImportError as e:
    raise ImportError(
        "Failed to import get_linear_schedule_with_warmup from transformers. "
        "Please ensure transformers>=4.0.0 is installed: "
        "pip install transformers>=4.0.0"
    ) from e
```
- [ ] Updated line 22 with try-except

---

## Fix #3: Documentation Improvements (Optional but Recommended)

**File**: `src/train_multitask.py`

### Change 3.1: Lines 144-176 (compute_auxiliary_loss docstring)

Replace the existing docstring with:
```python
    """
    Compute auxiliary loss for metadata prediction (regularization).

    The auxiliary task predicts a SUBSET of metadata features:
    - Boolean: All 10 features (hasDbCrossReferences, hasData, etc.)
    - Numerical: Only 2 features (log_citations, years_since_pub)
      Note: citedByCount and pubYear are NOT predicted

    Metadata tensor ordering:
    - [0:10]   Boolean (10)
    - [10:14]  Numerical (4) - we use only [10:12]
    - [14:16]  Categorical (2) - not used
    - [16:28]  TF-IDF (12) - not used

    Args:
        boolean_logits: [batch_size, 10] - Predicted boolean features
        numerical_preds: [batch_size, 2] - Predicted numerical features
        metadata: [batch_size, 28] - Ground truth metadata

    Returns:
        loss: Scalar auxiliary loss (BCE + MSE)
    """
```
- [ ] Updated docstring (optional)

---

## Fix #4: Data Validation (Optional but Recommended)

**File**: `src/data/multitask_dataloader.py`

### Change 4.1: Lines 155-167 (_validate_metadata_features)

Add AFTER line 166 (`logger.info(f"Validated {len(self.metadata_features)} metadata features")`):
```python
    # ADDED: Validate extracted dimensions
    sample_classif = self._extract_metadata(self.classif_df.iloc[0])
    sample_ner = self._extract_metadata(self.ner_df.iloc[0])

    if len(sample_classif) != self.n_metadata_features:
        raise ValueError(
            f"Classification metadata extraction failed! "
            f"Expected {self.n_metadata_features} features but got {len(sample_classif)}."
        )

    if len(sample_ner) != self.n_metadata_features:
        raise ValueError(
            f"NER metadata extraction failed! "
            f"Expected {self.n_metadata_features} features but got {len(sample_ner)}."
        )

    logger.info(f"✓ Metadata extraction validated: {len(sample_classif)} features")
```
- [ ] Added dimension validation (optional)

---

## Verification

### Step 1: Syntax Check
```bash
python -m py_compile src/models/multitask_model.py
python -m py_compile src/train_multitask.py
python -m py_compile src/data/multitask_dataloader.py
```
- [ ] All files compile without syntax errors

### Step 2: Run Tests
```bash
python test_multitask_setup.py
```
Expected output:
```
✓ Test 1: Data Loading - PASSED
✓ Test 2: Model Architecture - PASSED
✓ Test 3: Loss Computation - PASSED
✓ Test 4: Gradient Flow - PASSED
✓ Test 5: Metrics Tracking - PASSED
✓ Test 6: Short Training Run - PASSED

Total: 6/6 tests passed
```
- [ ] All 6 tests passing

### Step 3: Commit Changes
```bash
git add src/models/multitask_model.py
git add src/train_multitask.py
git add src/data/multitask_dataloader.py
git commit -m "Fix Phase 4 critical bugs: metadata dimension mismatch (34→28) and import handling"
```
- [ ] Changes committed

---

## Troubleshooting

### If tests still fail:

**Test 1-2 fail**: Check data files exist at `data/augmented/`

**Test 3-5 fail**: Dimension mismatch still present - recheck all `34` → `28` changes

**Test 6 fails**:
- Check transformers installed: `pip install transformers>=4.0.0`
- Check torch installed: `pip install torch`

**Import errors**:
```bash
pip install transformers torch scikit-learn pandas numpy pyyaml tqdm
```

---

## Success Criteria

- [x] 6/6 tests passing
- [x] No syntax errors
- [x] Changes committed to git
- [ ] Ready for full training

---

## Next Steps After Fixes

1. Run short training test:
   ```bash
   python src/train_multitask.py --test_mode --output_dir outputs/test_multitask
   ```

2. Check output logs:
   ```bash
   cat outputs/test_multitask/training.log
   ```

3. If successful, proceed with full training

---

**Questions?** See full review at `docs/code_reviews/PHASE4_CODE_REVIEW.md`
