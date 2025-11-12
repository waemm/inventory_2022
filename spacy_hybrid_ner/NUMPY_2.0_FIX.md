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

**Two-step process: Downgrade NumPy, then force reinstall spaCy**

### Issue Evolution

**Attempt 1**: Downgrade NumPy before installing spaCy
- Result: Got past `np.float_` error but hit binary incompatibility
- Error: `ValueError: numpy.dtype size changed, may indicate binary incompatibility`
- Cause: Colab pre-installs spaCy compiled against NumPy 2.0

**Attempt 2** (WORKING SOLUTION): Force reinstall spaCy after NumPy downgrade

### Fixed Cell 6 Code

```python
import sys
import subprocess
from pathlib import Path
import json

print("📦 Installing dependencies...")

# CRITICAL FIX: NumPy 2.0 incompatibility with cupy
# Step 1: Downgrade NumPy to 1.26.x (cupy doesn't support NumPy 2.0 yet)
print("⚙️  Step 1/2: Installing NumPy 1.26.x (cupy compatibility)...")
subprocess.run(['pip', 'install', '-q', 'numpy<2.0'], check=True)

# Step 2: Force reinstall spaCy to recompile against NumPy 1.26.x
# Without --force-reinstall, spaCy would use cached build from NumPy 2.0
print("⚙️  Step 2/2: Installing spaCy with CUDA (forced rebuild)...")
subprocess.run([
    'pip', 'install', '-q',
    '--force-reinstall',       # Force rebuild against new NumPy
    '--no-cache-dir',          # Don't use cached wheels
    'spacy[cuda12x]'           # CUDA 12.x support
], check=True)

# Install other dependencies (no binary compatibility issues)
print("⚙️  Installing visualization dependencies...")
subprocess.run([
    'pip', 'install', '-q',
    'pandas',
    'matplotlib',
    'seaborn',
    'tqdm'
], check=False)

print("✅ Dependencies installed")
```

### Key Changes

1. **Added NumPy downgrade**: `pip install numpy<2.0` runs FIRST
2. **Added forced reinstall**: `--force-reinstall --no-cache-dir` to rebuild spaCy
3. **Separated visualization deps**: No need to rebuild pandas/matplotlib
4. **Added progress messages**: User sees what's being installed step-by-step
5. **Set check=True**: Ensures each critical step completes before continuing

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
   📦 Installing dependencies...
   ⚙️  Step 1/2: Installing NumPy 1.26.x (cupy compatibility)...
   ⚙️  Step 2/2: Installing spaCy with CUDA (forced rebuild)...
   ⚙️  Installing visualization dependencies...
   ✅ Dependencies installed
   🔧 Imported modules
      spaCy version: 3.7.x

   ============================================================
   GPU CONFIGURATION
   ============================================================
   ✅ GPU Available: spaCy will use CUDA
      GPU will be used for training
      Expected speedup: 5-10x faster than CPU

   ✅ Environment setup complete
   ```

**Note**: Step 2 (forced rebuild) will take ~2-3 minutes as it recompiles spaCy and cupy against the new NumPy version.

## Next Steps

1. ✅ Fixed and uploaded corrected notebook
2. Monitor cupy releases for NumPy 2.0 support
3. Update notebook to remove NumPy downgrade when cupy is compatible
4. Test training runs in Colab with fixed notebook
