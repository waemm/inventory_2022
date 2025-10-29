# Experimental Training Pipeline - Visual Guide to New Features

**Date**: 2025-10-29

This guide shows what you'll see when using the new logging and diagnostics features.

---

## Cell 5.5: Pre-Flight Checks Output

### ✅ Successful Checks
```
================================================================================
PRE-FLIGHT CHECKS
================================================================================

1. Testing experimental_utils import...
   ✅ experimental_utils imported successfully

2. Testing training modules import...
   ✅ Training modules imported successfully

3. Checking NLTK punkt_tab availability...
   ✅ NLTK punkt_tab available

4. Testing model download capability...
   ✅ Model allenai/scibert_scivocab_uncased accessible

5. Verifying training data files...
   ✅ All 4 data files found

6. Checking GPU availability...
   ✅ GPU available: Tesla T4
   ✅ GPU memory: 15.0 GB

================================================================================
✅ ALL PRE-FLIGHT CHECKS PASSED
================================================================================
```

### ❌ Failed Checks Example
```
================================================================================
PRE-FLIGHT CHECKS
================================================================================

1. Testing experimental_utils import...
   ✅ experimental_utils imported successfully

2. Testing training modules import...
   ✅ Training modules imported successfully

3. Checking NLTK punkt_tab availability...
   ⚠️ NLTK punkt_tab not found, downloading...
   ✅ NLTK punkt_tab downloaded

4. Testing model download capability...
   ✅ Model allenai/scibert_scivocab_uncased accessible

5. Verifying training data files...
   ❌ Missing data files: ['data/classif_splits_full/train_paper_classif.csv']

6. Checking GPU availability...
   ⚠️ No GPU available - training will be slow

================================================================================
❌ PRE-FLIGHT CHECKS FAILED
================================================================================
RuntimeError: Pre-flight checks failed. Please resolve issues above before continuing.
```

---

## Cell 6: Training Loop Output

### Training Start
```
================================================================================
STARTING EXPERIMENTAL TRAINING SESSION: 2025-10-29-abc123
================================================================================
Started: 2025-10-29 14:23:45
Mode: FULL TRAINING
Configurations: 4
================================================================================
```

### Experiment Progress
```
================================================================================
EXPERIMENT 1/4: baseline
================================================================================

🔵 CLASSIFICATION TRAINING
   Learning rate: 2e-05
   Output: out/classif_2025-10-29-abc123_exp1_baseline
   Running classification training...

   Last 50 lines of output:
   Epoch 1/10
   Train: 100%|██████████| 125/125 [02:34<00:00,  1.23s/batch]
   Train Loss: 0.2341, Train F1: 0.8567
   Val: 100%|██████████| 32/32 [00:24<00:00,  1.32batch/s]
   Val Loss: 0.1876, Val F1: 0.8921

   Epoch 2/10
   Train: 100%|██████████| 125/125 [02:31<00:00,  1.21s/batch]
   Train Loss: 0.1654, Train F1: 0.9012
   Val: 100%|██████████| 32/32 [00:23<00:00,  1.35batch/s]
   Val Loss: 0.1432, Val F1: 0.9234

   ... (epochs 3-9)

   Epoch 10/10
   Train: 100%|██████████| 125/125 [02:29<00:00,  1.19s/batch]
   Train Loss: 0.0432, Train F1: 0.9678
   Val: 100%|██████████| 32/32 [00:22<00:00,  1.45batch/s]
   Val Loss: 0.1123, Val F1: 0.9456

   Training complete! Best validation F1: 0.9234 at epoch 2
   Saved best model to: out/classif_2025-10-29-abc123_exp1_baseline/model

✅ Classification complete: Val F1 = 0.9234
   Log saved to: experiments/2025-10-29-abc123/exp1_baseline/training_logs/exp1_baseline_classification.log
```

### NER Training
```
🟢 NER TRAINING
   Learning rate: 3e-05
   Output: out/ner_2025-10-29-abc123_exp1_baseline
   Running NER training...

   Last 50 lines of output:
   Epoch 1/10
   Train: 100%|██████████| 156/156 [03:12<00:00,  1.23s/batch]
   Train Loss: 0.3456, Train F1: 0.8234
   Val: 100%|██████████| 40/40 [00:32<00:00,  1.25batch/s]
   Val Loss: 0.2876, Val F1: 0.8543

   ... (epochs 2-9)

   Epoch 10/10
   Train: 100%|██████████| 156/156 [03:08<00:00,  1.21s/batch]
   Train Loss: 0.0543, Train F1: 0.9543
   Val: 100%|██████████| 40/40 [00:31<00:00,  1.28batch/s]
   Val Loss: 0.1234, Val F1: 0.9134

   Training complete! Best validation F1: 0.9134 at epoch 6
   Saved best model to: out/ner_2025-10-29-abc123_exp1_baseline/model

✅ NER complete: Val F1 = 0.9134
   Log saved to: experiments/2025-10-29-abc123/exp1_baseline/training_logs/exp1_baseline_ner.log

✅ Experiment 1 completed in 12.3 minutes
```

### Failed Experiment
```
================================================================================
EXPERIMENT 2/4: higher_lr
================================================================================

🔵 CLASSIFICATION TRAINING
   Learning rate: 5e-05
   Output: out/classif_2025-10-29-abc123_exp2_higher_lr
   Running classification training...

   Last 50 lines of output:
   Epoch 1/10
   Train: 100%|██████████| 125/125 [02:34<00:00,  1.23s/batch]
   Train Loss: 0.5432, Train F1: 0.7123
   Val: 100%|██████████| 32/32 [00:24<00:00,  1.32batch/s]
   Val Loss: 0.6234, Val F1: 0.6543

   Epoch 2/10
   Train:  45%|████▌     | 56/125 [01:09<01:25,  1.24s/batch]
   RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB

❌ Experiment 2 FAILED: CUDA out of memory. Tried to allocate 2.00 GiB
Traceback (most recent call last):
  File "/content/drive/MyDrive/inventory_2022/src/class_train.py", line 234, in train_epoch
    outputs = model(**batch)
  File "/usr/local/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1518, in _call_impl
    return forward_call(*args, **kwargs)
torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB
```

### Timeout Example
```
================================================================================
EXPERIMENT 3/4: aggressive
================================================================================

🔵 CLASSIFICATION TRAINING
   Learning rate: 0.0001
   Output: out/classif_2025-10-29-abc123_exp3_aggressive
   Running classification training...

   Last 50 lines of output:
   Epoch 1/10
   Train:   0%|          | 0/125 [00:00<?, ?batch/s]
   ... (hangs for 60 minutes) ...

❌ Experiment 3 TIMEOUT: 3600s
Traceback (most recent call last):
  File "<cell>", line 67, in <module>
    result = subprocess.run(...)
subprocess.TimeoutExpired: Command '['python', 'src/class_train.py', ...]' timed out after 3600 seconds
```

### Session Complete
```
================================================================================
ALL EXPERIMENTS COMPLETED
================================================================================
Finished: 2025-10-29 16:45:23

Summary:
- Experiments run: 4
- Completed: 2
- Failed: 1 (OOM)
- Timeout: 1
```

---

## Cell 7: Results Analysis

```
============================================================
RESULTS ANALYSIS
============================================================

📊 Results saved: experiments/2025-10-29-abc123/experiment_results.csv
📝 Summary saved: experiments/2025-10-29-abc123/comparison_summary.md

📈 EXPERIMENT RESULTS SUMMARY:

| experiment_id              | status    | classif_val_f1 | ner_val_f1 | error                         | error_file                        | log_file                                    |
|---------------------------|-----------|----------------|------------|-------------------------------|-----------------------------------|---------------------------------------------|
| 2025-10-29-abc123_exp1_baseline | completed | 0.9234        | 0.9134     | -                             | -                                 | -                                           |
| 2025-10-29-abc123_exp2_higher_lr | failed    | -             | -          | CUDA out of memory            | experiments/.../exp2_error_details.txt | experiments/.../exp2_higher_lr_classification.log |
| 2025-10-29-abc123_exp3_aggressive | failed    | -             | -          | Timeout after 3600s           | experiments/.../exp3_error_details.txt | -                                           |
| 2025-10-29-abc123_exp4_lower_lr | completed | 0.8876        | 0.8934     | -                             | -                                 | -                                           |

============================================================
BEST CONFIGURATIONS
============================================================

🏆 BEST CLASSIFICATION MODEL:
   Config: baseline
   Learning Rate: 2e-05
   Val F1: 0.9234
   Best Epoch: 2

🏆 BEST NER MODEL:
   Config: baseline
   Learning Rate: 3e-05
   Val F1: 0.9134
   Best Epoch: 6

📊 Training curves saved to:
   experiments/2025-10-29-abc123/exp1_baseline_classif_curves.png
   experiments/2025-10-29-abc123/exp1_baseline_ner_curves.png
   experiments/2025-10-29-abc123/exp4_lower_lr_classif_curves.png
   experiments/2025-10-29-abc123/exp4_lower_lr_ner_curves.png

✅ Analysis complete
```

---

## Cell 8: Archive Session

```
============================================================
SESSION ARCHIVAL
============================================================

📦 Creating session archive...
✅ Archive created: experiment_archives/2025-10-29-abc123

📁 Copying experiment outputs...
   ✅ classif_2025-10-29-abc123_exp1_baseline
   ✅ ner_2025-10-29-abc123_exp1_baseline
   ✅ classif_2025-10-29-abc123_exp4_lower_lr
   ✅ ner_2025-10-29-abc123_exp4_lower_lr

📝 Archiving training logs...
   ✅ exp1_baseline/training_logs
   ✅ exp2_higher_lr/training_logs
   ✅ exp3_aggressive/training_logs
   ✅ exp4_lower_lr/training_logs

📝 Archiving error details...
   ✅ 2025-10-29-abc123_exp2_higher_lr_error_details.txt
   ✅ 2025-10-29-abc123_exp3_aggressive_error_details.txt

✅ Logs and error details archived

📂 Archive contents:
   experiment_results.csv (15.2 KB)
   comparison_summary.md (8.4 KB)
   session_metadata.json (2.1 KB)
   training_logs/exp1_baseline/exp1_baseline_classification.log (234.5 KB)
   training_logs/exp1_baseline/exp1_baseline_ner.log (312.7 KB)
   training_logs/exp2_higher_lr/exp2_higher_lr_classification.log (156.3 KB)
   ... (more log files)
   error_details/2025-10-29-abc123_exp2_higher_lr_error_details.txt (3.2 KB)
   error_details/2025-10-29-abc123_exp3_aggressive_error_details.txt (2.8 KB)
   training_curves/exp1_baseline_classif_curves.png (245.6 KB)
   training_curves/exp1_baseline_ner_curves.png (238.9 KB)
   ... (more curves)

============================================================
SESSION SUMMARY
============================================================
Session ID: 2025-10-29-abc123
Mode: FULL TRAINING
Experiments Run: 4
Experiments Completed: 2
Experiments Failed: 2
Archive Size: 1.2 GB
Archive Location: experiment_archives/2025-10-29-abc123

🎉 EXPERIMENTAL SESSION COMPLETE!

📝 Next steps:
   1. Review comparison_summary.md for best configurations
   2. Examine training curves in training_curves/
   3. Use best model for production deployment
   4. Document findings in experiment log
```

---

## Error Details File

### Example: `2025-10-29-abc123_exp2_higher_lr_error_details.txt`
```
Experiment: 2025-10-29-abc123_exp2_higher_lr
Error: CUDA out of memory. Tried to allocate 2.00 GiB

Full Traceback:
================================================================================
Traceback (most recent call last):
  File "/content/drive/MyDrive/inventory_2022/src/class_train.py", line 234, in train_epoch
    outputs = model(**batch)
  File "/usr/local/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1518, in _call_impl
    return forward_call(*args, **kwargs)
  File "/usr/local/lib/python3.10/site-packages/transformers/models/bert/modeling_bert.py", line 1015, in forward
    embedding_output = self.embeddings(
  File "/usr/local/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1518, in _call_impl
    return forward_call(*args, **kwargs)
torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB (GPU 0; 14.76 GiB total capacity; 12.89 GiB already allocated; 1.34 GiB free; 13.12 GiB reserved in total by PyTorch)
If reserved memory is >> allocated memory try setting max_split_size_mb to avoid fragmentation. See documentation for Memory Management and PYTORCH_CUDA_ALLOC_CONF
```

---

## Training Log File

### Example: `exp1_baseline_classification.log` (excerpt)
```
================================================================================
Classification Training - allenai/scibert_scivocab_uncased
================================================================================

Configuration:
  Model: allenai/scibert_scivocab_uncased
  Learning Rate: 2e-05
  Batch Size: 16
  Epochs: 10
  Early Stopping: True (patience=3)

Loading training data: data/classif_splits_full/train_paper_classif.csv
  Training samples: 2,456
  Classes: 2 (positive/negative)

Loading validation data: data/classif_splits_full/val_paper_classif.csv
  Validation samples: 614

Initializing model...
  Model loaded: 110M parameters
  Device: cuda:0 (Tesla T4)

Starting training...

Epoch 1/10
================================================================================
Train: 100%|██████████| 154/154 [02:34<00:00,  1.00s/batch]
  Train Loss: 0.2341
  Train Precision: 0.8432
  Train Recall: 0.8704
  Train F1: 0.8567

Val: 100%|██████████| 39/39 [00:24<00:00,  1.62batch/s]
  Val Loss: 0.1876
  Val Precision: 0.8876
  Val Recall: 0.8967
  Val F1: 0.8921

New best validation F1! Saving checkpoint...
Saved: out/classif_2025-10-29-abc123_exp1_baseline/checkpoint_epoch1_f1_0.8921.pt

... (epochs 2-10)

Training complete!
================================================================================
Best validation F1: 0.9234 (epoch 2)
Total training time: 25.4 minutes
```

---

## File Structure After Training

```
inventory_2022/
├── experiments/
│   └── 2025-10-29-abc123/
│       ├── experiment_results.csv
│       ├── comparison_summary.md
│       ├── session_metadata.json
│       ├── exp1_baseline_classif_curves.png
│       ├── exp1_baseline_ner_curves.png
│       ├── 2025-10-29-abc123_exp2_higher_lr_error_details.txt
│       ├── 2025-10-29-abc123_exp3_aggressive_error_details.txt
│       ├── exp1_baseline/
│       │   └── training_logs/
│       │       ├── exp1_baseline_classification.log
│       │       └── exp1_baseline_ner.log
│       ├── exp2_higher_lr/
│       │   └── training_logs/
│       │       └── exp2_higher_lr_classification.log
│       ├── exp3_aggressive/
│       │   └── training_logs/
│       │       └── (empty or minimal)
│       └── exp4_lower_lr/
│           └── training_logs/
│               ├── exp4_lower_lr_classification.log
│               └── exp4_lower_lr_ner.log
│
├── experiment_archives/
│   └── 2025-10-29-abc123/
│       ├── experiment_results.csv
│       ├── comparison_summary.md
│       ├── session_metadata.json
│       ├── training_logs/
│       │   ├── exp1_baseline/
│       │   │   ├── exp1_baseline_classification.log
│       │   │   └── exp1_baseline_ner.log
│       │   ├── exp2_higher_lr/
│       │   │   └── exp2_higher_lr_classification.log
│       │   └── ... (all experiments)
│       ├── error_details/
│       │   ├── 2025-10-29-abc123_exp2_higher_lr_error_details.txt
│       │   └── 2025-10-29-abc123_exp3_aggressive_error_details.txt
│       └── training_curves/
│           ├── exp1_baseline_classif_curves.png
│           ├── exp1_baseline_ner_curves.png
│           └── ... (all curves)
│
└── out/
    ├── classif_2025-10-29-abc123_exp1_baseline/
    │   ├── model/
    │   ├── train_stats.csv
    │   └── ...
    ├── ner_2025-10-29-abc123_exp1_baseline/
    │   ├── model/
    │   ├── train_stats.csv
    │   └── ...
    └── ... (all successful experiments)
```

---

This visual guide demonstrates the complete user experience with the new logging and diagnostics features. All output is real-world formatted and shows both success and failure cases for comprehensive understanding.
