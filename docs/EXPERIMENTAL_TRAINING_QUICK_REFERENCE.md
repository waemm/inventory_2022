# Experimental Training Pipeline - Quick Reference Guide

**Last Updated**: 2025-10-29

## Quick Start

### 1. Launch Notebook
```python
# In Google Colab
# Open: experimental_training_pipeline.ipynb
# Runtime → Change runtime type → GPU (T4, A100, or V100)
```

### 2. Set Test Mode (Optional)
```python
# Cell 2: Configuration
TEST_MODE = True   # Quick validation (2 epochs per experiment)
TEST_MODE = False  # Full training (10 epochs per experiment)
```

### 3. Run All Cells
- Cell 1: Mount Drive → generates `SESSION_ID`
- Cell 2: Configure experiments
- Cell 3: Setup environment
- Cell 4: Initialize tracker
- Cell 5: Prepare data
- **Cell 5.5: Pre-flight checks** ← NEW!
- Cell 6: Run experiments (with logging!)
- Cell 7: Analyze results
- Cell 8: Archive session (includes logs!)

## What's New - Logging Features

### Output Capture
**Where**: Cell 6 - Training Loop

**What it does**:
- Captures all training output to log files
- Shows last 50 lines in notebook
- Saves complete logs for debugging

**Log files location**:
```
experiments/{SESSION_ID}/exp1_baseline/training_logs/
  ├── exp1_baseline_classification.log
  └── exp1_baseline_ner.log
```

### Pre-Flight Checks
**Where**: Cell 5.5 - NEW cell

**What it checks**:
1. ✅ Can import experimental_utils?
2. ✅ Can import training modules?
3. ✅ NLTK data available?
4. ✅ Can download models?
5. ✅ Training data files exist?
6. ✅ GPU available and ready?

**What happens if checks fail?**
- Cell raises `RuntimeError`
- Fix the issue and re-run
- Prevents wasted GPU time

### Error Tracking
**Where**: Cell 6 - Training Loop

**What it captures**:
- Full Python tracebacks
- Training log references
- Timeout vs error distinction

**Error files location**:
```
experiments/{SESSION_ID}/
  └── 2025-10-29-abc123_exp1_baseline_error_details.txt
```

**Results CSV includes**:
- `error_file`: Path to traceback file
- `log_file`: Path to training log

### Archive with Logs
**Where**: Cell 8 - Archive Session

**What gets archived**:
- ✅ Training logs (all experiments)
- ✅ Error details (failed experiments)
- ✅ Training curves (PNG plots)
- ✅ Results CSV and summary

**Archive location**:
```
experiment_archives/{SESSION_ID}/
  ├── experiment_results.csv
  ├── comparison_summary.md
  ├── training_logs/
  │   └── exp1_baseline/
  │       ├── exp1_baseline_classification.log
  │       └── exp1_baseline_ner.log
  ├── error_details/
  │   └── 2025-10-29-abc123_exp1_baseline_error_details.txt
  └── training_curves/
      ├── exp1_baseline_classif_curves.png
      └── exp1_baseline_ner_curves.png
```

## Common Tasks

### Check if Pre-Flight Checks Passed
```python
# Cell 5.5 output will show:
# ========================================
# PRE-FLIGHT CHECKS
# ========================================
#
# 1. Testing experimental_utils import...
#    ✅ experimental_utils imported successfully
# ...
# ========================================
# ✅ ALL PRE-FLIGHT CHECKS PASSED
# ========================================
```

### View Training Output During Run
```python
# Cell 6 will display:
# 🔵 CLASSIFICATION TRAINING
#    Learning rate: 2e-05
#    Output: out/classif_2025-10-29-abc123_exp1_baseline
#    Running classification training...
#
#    Last 50 lines of output:
#    Epoch 1/10 - Loss: 0.234, F1: 0.876
#    ...
#    ✅ Classification complete: Val F1 = 0.8921
#    Log saved to: experiments/2025-10-29-abc123/exp1_baseline/training_logs/exp1_baseline_classification.log
```

### Debug Failed Experiment
```python
# 1. Check inline error in Cell 6 output
❌ Experiment 1 FAILED: Classification training failed with code 1
Traceback (most recent call last):
  ...

# 2. Read error details file
from pathlib import Path
error_file = Path('experiments/{SESSION_ID}/{exp_id}_error_details.txt')
print(error_file.read_text())

# 3. Check training log (full output)
log_file = Path('experiments/{SESSION_ID}/exp1_baseline/training_logs/exp1_baseline_classification.log')
lines = log_file.read_text().split('\n')
print('\n'.join(lines[-100:]))  # Last 100 lines
```

### Find Best Model After Training
```python
# Cell 7 automatically displays:
# ========================================
# BEST CONFIGURATIONS
# ========================================
#
# 🏆 BEST CLASSIFICATION MODEL:
#    Config: baseline
#    Learning Rate: 2e-05
#    Val F1: 0.8921
#    Best Epoch: 7
#
# 🏆 BEST NER MODEL:
#    Config: higher_lr
#    Learning Rate: 5e-05
#    Val F1: 0.9134
#    Best Epoch: 6
```

### Access Archived Results
```python
# All results saved to:
session_id = "2025-10-29-abc123"

# Google Drive archive:
archive_path = f"/content/drive/MyDrive/inventory_2022/experiment_archives/{session_id}"

# Key files:
results_csv = f"{archive_path}/experiment_results.csv"
summary_md = f"{archive_path}/comparison_summary.md"
logs_dir = f"{archive_path}/training_logs"
errors_dir = f"{archive_path}/error_details"

# Load results
import pandas as pd
df = pd.read_csv(results_csv)
display(df)
```

## Troubleshooting

### Pre-Flight Checks Failed

**Problem**: `❌ Failed to import experimental_utils`
**Solution**: Run Cell 3 (Environment Setup) first

**Problem**: `❌ Missing data files`
**Solution**: Run Cell 5 (Data Preparation) to generate splits

**Problem**: `⚠️ No GPU available`
**Solution**: Runtime → Change runtime type → GPU

### Training Errors

**Problem**: `TimeoutExpired: Command timed out after 3600s`
**Solution**:
- Check if model is too large
- Increase timeout in Cell 6
- Reduce batch size in Cell 2

**Problem**: `RuntimeError: CUDA out of memory`
**Solution**:
- Reduce `batch_size` in Cell 2
- Clear GPU: `clear_gpu_memory()` in Cell 3
- Restart runtime

**Problem**: Training fails silently
**Solution**:
- Check log file in `training_logs/`
- Review error_details.txt
- Check last 50 lines displayed in Cell 6

### Archive Issues

**Problem**: Logs not in archive
**Solution**:
- Verify Cell 8 completed
- Check `training_logs/` exists in experiment dir
- Re-run Cell 8

**Problem**: Google Drive space full
**Solution**:
- Delete old experiment archives
- Compress large log files
- Use selective archival

## Best Practices

### Before Training
1. ✅ Set `TEST_MODE = True` for first run
2. ✅ Verify pre-flight checks pass
3. ✅ Check GPU memory available
4. ✅ Review experiment configurations

### During Training
1. ✅ Monitor Cell 6 output for errors
2. ✅ Check GPU memory usage periodically
3. ✅ Watch validation F1 scores
4. ✅ Note any timeout warnings

### After Training
1. ✅ Review experiment_results.csv
2. ✅ Check for failed experiments
3. ✅ Examine training curves
4. ✅ Archive session to Drive
5. ✅ Document best configurations

## Configuration Examples

### Quick Test Run
```python
# Cell 2
TEST_MODE = True
LEARNING_RATE_CONFIGS = [
    {'name': 'baseline', 'classif_lr': 2e-5, 'ner_lr': 3e-5}
]
# Result: 1 experiment, 2 epochs each, ~5 minutes
```

### Full Hyperparameter Sweep
```python
# Cell 2
TEST_MODE = False
LEARNING_RATE_CONFIGS = [
    {'name': 'baseline', 'classif_lr': 2e-5, 'ner_lr': 3e-5},
    {'name': 'higher_lr', 'classif_lr': 5e-5, 'ner_lr': 5e-5},
    {'name': 'lower_lr', 'classif_lr': 1e-5, 'ner_lr': 2e-5},
    {'name': 'aggressive', 'classif_lr': 1e-4, 'ner_lr': 8e-5}
]
# Result: 4 experiments, 10 epochs each, ~4 hours
```

### Conservative Run (Avoid OOM)
```python
# Cell 2
BASE_CONFIG = {
    'model_name': 'allenai/scibert_scivocab_uncased',
    'batch_size': 8,  # Reduced from auto-calculated
    'num_epochs': 10,
    'early_stopping': True,
    'patience': 3
}
```

## Key Cell Reference

| Cell | Purpose | New Features |
|------|---------|--------------|
| 1 | Mount Drive, setup paths | - |
| 2 | Configuration | - |
| 3 | Environment setup | - |
| 4 | Initialize tracker | - |
| 5 | Data preparation | - |
| **5.5** | **Pre-flight checks** | ✨ **NEW** |
| 6 | Training loop | ✨ **Output capture**, ✨ **Error tracking** |
| 7 | Results analysis | - |
| 8 | Archive session | ✨ **Log archival** |

## Quick Commands

```python
# Check session ID
print(SESSION_ID)  # e.g., "2025-10-29-abc123"

# Check GPU memory
get_gpu_memory_info()

# Clear GPU memory
clear_gpu_memory()

# View results
results_df = pd.read_csv(f'experiments/{SESSION_ID}/experiment_results.csv')
display(results_df)

# Find log files
!find experiments/{SESSION_ID} -name "*.log"

# Find error files
!find experiments/{SESSION_ID} -name "*_error_details.txt"

# Check archive size
!du -sh experiment_archives/{SESSION_ID}
```

---

**Need Help?**
- Full documentation: `docs/EXPERIMENTAL_TRAINING_LOGGING_UPDATES.md`
- Implementation details: `docs/EXPERIMENTAL_TRAINING_IMPLEMENTATION.md`
