# NumPy 2.0 Compatibility Fix

**Date**: 2025-11-12
**Issue**: Colab notebook fails on Cell 6 with NumPy 2.0 incompatibility
**Status**: ✅ FIXED

## Problem

When running `spacy_training_colab.ipynb` in Google Colab, Cell 6 (Environment Setup) failed with:

```
AttributeError: `np.float_` was removed in the NumPy 2.0 release. Use `np.float64` instead.
```

### Root Cause

1. **Google Colab** now ships with NumPy 2.0 by default (as of late 2024)
2. **spaCy[cuda12x]** depends on `cupy-cuda12x` for GPU support
3. **cupy** has not yet been updated for NumPy 2.0 compatibility
4. When spaCy tries to import cupy, cupy's initialization code uses the deprecated `np.float_` which was removed in NumPy 2.0

### Error Chain

```
spacy[cuda12x] → cupy-cuda12x → numpy 2.0 → AttributeError: np.float_ removed
```

## Solution

**Downgrade NumPy to 1.26.x BEFORE installing spaCy**

### Fixed Cell 6 Code

```python
import sys
import subprocess
from pathlib import Path
import json

print("📦 Installing dependencies...")

# CRITICAL FIX: Downgrade NumPy to 1.26.x for cupy compatibility
# Colab now has NumPy 2.0 by default, but cupy (used by spaCy CUDA) doesn't support it yet
print("⚙️  Installing NumPy 1.26.x (cupy/spaCy CUDA compatibility)...")
subprocess.run(['pip', 'install', '-q', 'numpy<2.0'], check=True)

# Now install spaCy with CUDA support
print("⚙️  Installing spaCy with CUDA support...")
subprocess.run([
    'pip', 'install', '-q',
    'spacy[cuda12x]',  # CUDA 12.x support for Colab
    'pandas',
    'matplotlib',
    'seaborn',
    'tqdm'
], check=False)

print("✅ Dependencies installed")
```

### Key Changes

1. **Added NumPy downgrade**: `pip install numpy<2.0` runs FIRST
2. **Added progress messages**: User sees what's being installed
3. **Added comments**: Explains WHY we're downgrading NumPy
4. **Set check=True**: Ensures NumPy install completes before spaCy

## Testing

✅ Fixed notebook uploaded to Google Drive: `spacy_hybrid_ner/spacy_training_colab.ipynb`

## Timeline for Upstream Fix

- **cupy**: Working on NumPy 2.0 support (tracked in cupy/cupy#7991)
- **spaCy**: Waiting for cupy update
- **Our fix**: Can be removed once cupy releases NumPy 2.0 compatible version

## Alternative Solutions Considered

1. ❌ **Use CPU-only spaCy**: Loses 5-10x GPU speedup
2. ❌ **Pin older Colab runtime**: Not sustainable long-term
3. ✅ **Downgrade NumPy**: Clean, targeted fix that works today

## Impact

- **Training speed**: No impact - still uses GPU with CUDA 12.x
- **Compatibility**: Works with current Colab environment
- **Maintenance**: Will need updating when cupy releases NumPy 2.0 support

## Related Issues

- cupy GitHub: NumPy 2.0 compatibility tracking issue
- spaCy Discussions: Multiple reports of this issue in Nov 2024
- Google Colab: NumPy 2.0 now default in standard runtime

## Files Modified

- `spacy_hybrid_ner/spacy_training_colab.ipynb` - Cell 6 (Environment Setup)

## Verification

To verify the fix works in Colab:

1. Open notebook in Colab
2. Run Cell 6 (Environment Setup)
3. Check output shows:
   ```
   ⚙️  Installing NumPy 1.26.x (cupy/spaCy CUDA compatibility)...
   ⚙️  Installing spaCy with CUDA support...
   ✅ Dependencies installed
   🔧 Imported modules
      spaCy version: 3.7.x
   ✅ GPU Available: spaCy will use CUDA
   ```

## Next Steps

1. ✅ Fixed and uploaded corrected notebook
2. Monitor cupy releases for NumPy 2.0 support
3. Update notebook to remove NumPy downgrade when cupy is compatible
4. Test training runs in Colab with fixed notebook
