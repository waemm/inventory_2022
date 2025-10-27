# Checkpoint Conversion Plan for PyTorch 2.8 Compatibility

**Date**: 2025-10-27
**Status**: 🚀 In Progress
**Priority**: HIGH - Fixes 99% prediction loss in Colab
**Estimated Duration**: ~2 hours (vs 9.5 hours retraining)

---

## Executive Summary

### Problem
Models trained in PyTorch 2.0.0 produce different predictions when loaded in PyTorch 2.8.0 (Colab), causing 99% of predictions to fail quality thresholds.

**Root Cause**: PyTorch version incompatibility in deserializing custom NamedTuple objects from checkpoint files.

### Solution
Convert existing checkpoints to a version-resilient format (dicts only, no custom objects) and implement backward-compatible loading code.

### Impact
- ✅ Fixes Colab predictions without retraining (saves 9.5 hours)
- ✅ Makes checkpoints work across PyTorch versions
- ✅ Maintains backward compatibility with old checkpoints

---

## Technical Background

### Current Checkpoint Format
```python
{
    'model_state_dict': <tensor dict>,           # ✓ Version-safe
    'model_name': 'allenai/dsp_roberta...',      # ✓ Version-safe
    'train_metrics': Metrics(...),               # ✗ NamedTuple (custom class)
    'val_metrics': Metrics(...)                  # ✗ NamedTuple (custom class)
}
```

### Problem Chain
```
Same .pt file (MD5 match)
    ↓
PyTorch 2.8 loads differently (weights_only=False with NamedTuple)
    ↓
Different parameter values (checksum: 1b17681a4bc90587 vs a6d0f62fc239a626)
    ↓
Same input → Different logits (6.22 vs 2.64)
    ↓
Lower logits → Lower probabilities (0.998 vs 0.764)
    ↓
Fewer predictions pass 0.978 threshold (3,698 vs 29)
    ↓
Only 0.8% predictions pass vs 84.7%
```

### New Checkpoint Format
```python
{
    'model_state_dict': <tensor dict>,           # ✓ Version-safe
    'model_name': 'allenai/dsp_roberta...',      # ✓ Version-safe
    'train_metrics': {                           # ✓ Dict (version-safe)
        'precision': 0.93,
        'recall': 0.87,
        'f1': 0.90,
        'loss': 0.15
    },
    'val_metrics': {                             # ✓ Dict (version-safe)
        'precision': 0.93,
        'recall': 0.87,
        'f1': 0.90,
        'loss': 0.15
    }
}
```

**Key**: No custom classes → Can use `weights_only=True` → Version-consistent loading

---

## Implementation Plan

### Phase 1: Write Plan Document ✓
**Duration**: 5 minutes
**File**: `plans/2025-10-27_checkpoint_conversion_plan.md`

Document complete strategy, success criteria, and rollback plan.

---

### Phase 2: Create Conversion Script
**Duration**: 15 minutes
**File**: `convert_checkpoints_to_weights_only.py`

**Requirements**:
- Load checkpoint in PyTorch 2.0.0 (biodata_modern_env)
- Convert NamedTuple metrics to dicts
- Save new checkpoint with `_v2.pt` suffix
- Verify parameter checksums match before/after
- Test new checkpoint loads with `weights_only=True`

**Script Structure**:
```python
def convert_checkpoint(old_path, new_path):
    # 1. Load with PyTorch 2.0 (weights_only=False OK here)
    checkpoint = torch.load(old_path, map_location='cpu', weights_only=False)

    # 2. Extract and convert metrics
    train_metrics = checkpoint['train_metrics']
    val_metrics = checkpoint['val_metrics']

    # 3. Create new checkpoint (dicts only)
    new_checkpoint = {
        'model_state_dict': checkpoint['model_state_dict'],
        'model_name': checkpoint['model_name'],
        'train_metrics': {
            'precision': float(train_metrics.precision),
            'recall': float(train_metrics.recall),
            'f1': float(train_metrics.f1),
            'loss': float(train_metrics.loss)
        },
        'val_metrics': {
            'precision': float(val_metrics.precision),
            'recall': float(val_metrics.recall),
            'f1': float(val_metrics.f1),
            'loss': float(val_metrics.loss)
        }
    }

    # 4. Verify checksums
    # 5. Save and test
```

---

### Phase 3: Run Conversion in biodata_modern_env
**Duration**: 5 minutes
**Environment**: biodata_modern_env (PyTorch 2.0.0)

**Commands**:
```bash
source biodata_modern_env/bin/activate
python --version  # Verify Python 3.11.9
python -c "import torch; print(torch.__version__)"  # Verify PyTorch 2.0.0
python convert_checkpoints_to_weights_only.py
```

**Models to Convert**:
1. Classification: `out/classif_train_out/article_classifier.pt` (476MB)
   - Output: `out/classif_train_out/article_classifier_v2.pt`

2. NER: `out/ner_train_out/named_entity_recognition.pt` (473MB)
   - Output: `out/ner_train_out/named_entity_recognition_v2.pt`

**Verification**:
- Parameter checksum: `a6d0f62fc239a626` (must match)
- File sizes: ~same as original
- Loads with `weights_only=True`: ✓

---

### Phase 4: Update Loading Code in filing.py
**Duration**: 30 minutes
**File**: `src/inventory_utils/filing.py`

**Functions to Update**:
1. `get_classif_model()` (lines ~36-51)
2. `get_ner_model()` (lines ~67-85)

**Pattern** (try-except with fallback):
```python
def get_classif_model(checkpoint_fh, device):
    # Try new format first (weights_only=True)
    try:
        checkpoint = torch.load(checkpoint_fh, map_location=device, weights_only=True)
        # ... load model ...
    except (pickle.UnpicklingError, RuntimeError):
        # Fall back to old format (weights_only=False)
        checkpoint_fh.seek(0)  # Reset file pointer
        checkpoint = torch.load(checkpoint_fh, map_location=device, weights_only=False)
        # ... load model ...
```

---

### Phase 5: Update Loading Code in model_picker.py
**Duration**: 15 minutes
**File**: `src/model_picker.py`

**Function to Update**: `get_metrics()` (lines ~60-76)

**Pattern**:
```python
def get_metrics(checkpoint_fh):
    try:
        # Try new format (dict)
        checkpoint = torch.load(checkpoint_fh, weights_only=True)
        metrics = checkpoint['val_metrics']  # Already a dict
        return {
            'f1': metrics['f1'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'loss': metrics['loss']
        }
    except:
        # Fall back to old format (NamedTuple)
        checkpoint_fh.seek(0)
        checkpoint = torch.load(checkpoint_fh, weights_only=False)
        metrics = cast(Metrics, checkpoint['val_metrics'])
        return {
            'f1': metrics.f1,
            'precision': metrics.precision,
            'recall': metrics.recall,
            'loss': metrics.loss
        }
```

---

### Phase 6: Update save_model() Function
**Duration**: 15 minutes
**File**: `src/inventory_utils/filing.py`

**Function**: `save_model()` (lines ~114-133)

**Change**:
```python
def save_model(model, model_name, train_metrics, val_metrics, filename):
    torch.save(
        {
            'model_state_dict': model.state_dict(),
            'model_name': model_name,
            'train_metrics': {  # Convert NamedTuple to dict
                'precision': float(train_metrics.precision),
                'recall': float(train_metrics.recall),
                'f1': float(train_metrics.f1),
                'loss': float(train_metrics.loss)
            },
            'val_metrics': {  # Convert NamedTuple to dict
                'precision': float(val_metrics.precision),
                'recall': float(val_metrics.recall),
                'f1': float(val_metrics.f1),
                'loss': float(val_metrics.loss)
            }
        }, filename)
```

**Impact**: Future training runs will create v2 format automatically.

---

### Phase 7: Local Testing
**Duration**: 15 minutes
**Environment**: biodata_modern_env (PyTorch 2.0.0)

**Test Checklist**:
1. [ ] Load `article_classifier_v2.pt` with new code
2. [ ] Verify parameter checksum: `a6d0f62fc239a626`
3. [ ] Load `named_entity_recognition_v2.pt` with new code
4. [ ] Verify parameter checksum: `a6d0f62fc239a626`
5. [ ] Run test prediction on "Rat Genome Database" paper
6. [ ] Verify logits: `[6.22, -2.04, -1.42, -1.45, -2.24]`
7. [ ] Verify probability: ~0.998
8. [ ] Test backward compatibility: load old `.pt` with new code
9. [ ] Verify old checkpoints still work

**Commands**:
```bash
source biodata_modern_env/bin/activate
python -c "
import torch
from src.inventory_utils.filing import get_ner_model

with open('out/ner_train_out/named_entity_recognition_v2.pt', 'rb') as f:
    model, name, tokenizer = get_ner_model(f, torch.device('cpu'))

# Verify checksum
import hashlib
param_bytes = b''.join([p.cpu().detach().numpy().tobytes()
                        for p in model.parameters()])
checksum = hashlib.md5(param_bytes).hexdigest()[:16]
print(f'Checksum: {checksum}')
print(f'Expected: a6d0f62fc239a626')
assert checksum == 'a6d0f62fc239a626', 'Checksum mismatch!'
print('✅ Conversion successful!')
"
```

---

### Phase 8: Commit Changes
**Duration**: 10 minutes

**Commands**:
```bash
git add convert_checkpoints_to_weights_only.py
git add src/inventory_utils/filing.py
git add src/model_picker.py
git add plans/2025-10-27_checkpoint_conversion_plan.md
git commit -m "$(cat <<'EOF'
Add checkpoint conversion and backward-compatible loading for PyTorch 2.8

- Create convert_checkpoints_to_weights_only.py script
- Convert NamedTuple metrics to dicts in checkpoints
- Implement try-except loading pattern in filing.py and model_picker.py
- Update save_model() to save dicts instead of NamedTuples
- Maintain backward compatibility with old checkpoint format

This fixes the Colab vs Local prediction discrepancy (99% loss) without
retraining models. New checkpoints work across PyTorch versions.

Fixes: PyTorch 2.8 deserialization incompatibility with NamedTuple objects
EOF
)"
```

---

### Phase 9: Upload to Google Drive
**Duration**: 10 minutes

**Files to Upload**:
1. `article_classifier_v2.pt` (476MB) → `/content/drive/MyDrive/inventory_2022/out/classif_train_out/`
2. `named_entity_recognition_v2.pt` (473MB) → `/content/drive/MyDrive/inventory_2022/out/ner_train_out/`

**Method**: Use Google Drive desktop app or web interface

---

### Phase 10: Colab Testing
**Duration**: 20 minutes
**Environment**: Google Colab (PyTorch 2.8)

**Test Notebook Updates**:
```python
# Change model paths to use _v2.pt files
CLASSIF_MODEL = "/content/drive/MyDrive/inventory_2022/out/classif_train_out/article_classifier_v2.pt"
NER_MODEL = "/content/drive/MyDrive/inventory_2022/out/ner_train_out/named_entity_recognition_v2.pt"
```

**Critical Tests**:
1. [ ] Load models with updated code
2. [ ] Verify parameter checksum: `a6d0f62fc239a626`
3. [ ] Run diagnostic on "Rat Genome Database" paper
4. [ ] Verify logits: `[6.22, -2.04, -1.42, -1.45, -2.24]`
5. [ ] Verify probability: ~0.998 (not 0.764)
6. [ ] Run full 2022 rerun (21,677 papers)
7. [ ] Verify pass rate: ~84.7% (not 0.8%)
8. [ ] Verify entity count: ~3,698 (not 29)

---

### Phase 11: Documentation
**Duration**: 15 minutes

**Files to Create/Update**:

1. **NEW**: `weights_issues/CONVERSION_GUIDE.md`
   - Step-by-step conversion instructions
   - Troubleshooting guide
   - Verification procedures

2. **UPDATE**: `docs/starting_doc.md`
   - Add checkpoint format section
   - Document v2 checkpoint locations
   - Update model loading information

3. **UPDATE**: `weights_issues/PROBLEM_SUMMARY_COLAB_VS_LOCAL.md`
   - Mark solution as RESOLVED
   - Document conversion approach
   - Link to conversion guide

---

## Success Criteria

### Critical Metrics

| Metric | Before (Colab) | After (Colab) | Target |
|--------|----------------|---------------|--------|
| **Parameter Checksum** | `1b17681a4bc90587` | `a6d0f62fc239a626` | Match local |
| **First Token Logits** | `[2.64, -0.74, ...]` | `[6.22, -2.04, ...]` | Match local |
| **Entity Probability** | 0.764 | 0.998 | ≥0.978 |
| **Pass Rate** | 0.8% (29/3569) | 84.7% (3698/4368) | >80% |
| **High-Conf Entities** | 29 | 3,698 | ~3,700 |

### Backward Compatibility

- [ ] Old checkpoints (`*.pt`) still load correctly
- [ ] New checkpoints (`*_v2.pt`) load with `weights_only=True`
- [ ] No breaking changes for local environment
- [ ] Graceful fallback if new format fails

### Business Impact

- [ ] Colab inventory completeness matches local
- [ ] No need for 9.5-hour retraining
- [ ] Future training runs use new format automatically
- [ ] Models work across PyTorch versions

---

## Risk Mitigation

### Rollback Plan

**If conversion fails**:
1. Original `*.pt` files remain unchanged
2. Revert code changes: `git checkout HEAD~1`
3. Fall back to PyTorch downgrade in Colab
4. Last resort: Full retraining

**Checkpoints to Preserve**:
- `out/classif_train_out/article_classifier.pt` (original)
- `out/ner_train_out/named_entity_recognition.pt` (original)

### Verification Points

**After each phase**:
1. Phase 3: Verify checksums match `a6d0f62fc239a626`
2. Phase 7: Verify local predictions still work
3. Phase 10: Verify Colab predictions fixed

**Stop conditions**:
- Checksum mismatch after conversion
- Local tests fail with new code
- Colab tests don't show improvement

---

## Timeline

| Phase | Task | Duration | Cumulative |
|-------|------|----------|------------|
| 1 | Write plan | 5 min | 5 min |
| 2 | Create script | 15 min | 20 min |
| 3 | Run conversion | 5 min | 25 min |
| 4 | Update filing.py | 30 min | 55 min |
| 5 | Update model_picker.py | 15 min | 70 min |
| 6 | Update save_model() | 15 min | 85 min |
| 7 | Local testing | 15 min | 100 min |
| 8 | Commit changes | 10 min | 110 min |
| 9 | Upload to Drive | 10 min | 120 min |
| 10 | Colab testing | 20 min | 140 min |
| 11 | Documentation | 15 min | 155 min |

**Total**: ~2.5 hours vs 9.5 hours retraining (73% time savings)

---

## Dependencies

### Required
- biodata_modern_env with PyTorch 2.0.0
- Existing model checkpoints (article_classifier.pt, named_entity_recognition.pt)
- Google Drive access for Colab testing

### Optional
- Google Colab access (for final verification)

---

## Post-Implementation

### Monitoring
- Track prediction quality metrics in Colab
- Monitor for any regressions in local environment
- Verify future training runs use new format

### Future Work
- Phase out old checkpoint format over time
- Update all archived models to new format
- Document checkpoint format in training guides

---

## References

- **Problem Analysis**: `weights_issues/PROBLEM_SUMMARY_COLAB_VS_LOCAL.md`
- **Investigation**: `docs/COLAB_PROBABILITY_INVESTIGATION.md`
- **Solution Docs**: `weights_issues/solutions.md`, `weights_issues/solutions2.md`
- **Diagnostic Script**: `src/ner_predict_diagnostic.py`

---

**Status**: ✅ Ready for implementation
**Next Step**: Create conversion script (Phase 2)
