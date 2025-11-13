# Quick Reference Commands - Biodata Inventory Pipeline

**Created**: 2025-11-04
**Purpose**: Quick command reference for common operations
**Audience**: AI agents and developers

---

## Environment Management

### Activate Environment
```bash
cd GBC/inventory_2022/  # Repository root
source biodata_modern_env/bin/activate
export PYTHONPATH="src:$PYTHONPATH"
```

### Verify Environment
```bash
python -c "import torch, transformers; print(f'PyTorch: {torch.__version__}, Transformers: {transformers.__version__}')"
```

### Deactivate
```bash
deactivate
```

---

## Training Operations

### Full Production Training (9.5 hours)
```bash
./run_full_training.sh
```

### Quick Test Training (5-8 minutes)
```bash
./run_train_test_modern.sh
```

### Monitor Training Progress
```bash
./monitor_training.sh --follow
```

---

## Prediction Operations

### Manual Classification Prediction
```bash
python src/class_predict.py \
  -c out/classif_train_out/article_classifier_v2.pt \
  -i data/input.csv \
  -o output_dir/
```

### Manual NER Prediction
```bash
python src/ner_predict.py \
  -c out/ner_train_out/named_entity_recognition_v2.pt \
  -i data/input.csv \
  -o output_dir/
```

### Full Pipeline (2022 Rerun)
```bash
./rerun_2022_inventory.sh
```

### Test Mode (Small Dataset)
```bash
./test_rerun_2022_inventory.sh
```

---

## Results Analysis

### Check Recent Results
```bash
ls -la inventory_classification_results/
```

### View Training Logs
```bash
tail -f logs/full_training_*.log
```

### Check Model Archives
```bash
ls -la trained_models_25/
```

### View Specific Session Results
```bash
ls -la trained_models_25/2025-10-21_full_production_training/
```

---

## Google Drive Operations

### Upload Files to Drive
```bash
# Upload single file
python upload_to_drive.py path/to/file.py

# Upload multiple files
python upload_to_drive.py file1.py file2.ipynb src/module.py

# Force re-upload (skip change detection)
python upload_to_drive.py --force path/to/file.py
```

### Download New Archives from Drive
```bash
# Download new experimental results
python download_from_drive.py --archive-type experiment_archives

# Download new training results
python download_from_drive.py --archive-type training_archives

# Interactive mode (with confirmation)
python download_from_drive.py --archive-type experiment_archives --interactive
```

### Check Upload/Download Logs
```bash
# View recent uploads
ls -la upload_logs/

# View recent downloads
ls -la download_logs/

# Check latest upload
tail upload_logs/*.csv
```

---

## Git Operations

### Commit Changes (No AI Attribution)
```bash
# Stage changes
git add path/to/files

# Commit (WITHOUT AI attribution lines)
git commit -m "Description of changes"

# Push to remote
git push origin branch-name
```

### Create New Branch for Work
```bash
git checkout -b feature/description-of-work
```

### Check Status
```bash
git status
git log --oneline -5
```

---

## Session Management

### Check Current Sessions
```bash
# List training archives
ls -la trained_models_25/

# List experiment archives (if synced locally)
ls -la experiment_archives/
```

### View Session Details
```bash
# View training statistics
cat trained_models_25/SESSION_ID_full_training/training_stats.txt

# View evaluation metrics
cat trained_models_25/SESSION_ID_full_training/eval_metrics.txt
```

---

## File Operations

### Find Files by Pattern
```bash
# Find all Python files
find . -name "*.py" -type f

# Find training configuration
find . -name "*train*.yml" -type f

# Find model checkpoints
find . -name "*.pt" -type f
```

### Search Code for Pattern
```bash
# Search for function definition
grep -r "def function_name" src/

# Search for class definition
grep -r "class ClassName" src/

# Search with line numbers
grep -rn "pattern" src/
```

### Check File Sizes
```bash
# Check model sizes
du -h out/classif_train_out/*.pt
du -h out/ner_train_out/*.pt

# Check archive sizes
du -h trained_models_25/*/
```

---

## Validation Operations

### Verify Model Checksums
```bash
# MD5 checksums for V2 models
md5 out/classif_train_out/article_classifier_v2.pt
# Expected: ea57a1cab905c6d5c4e064204f3e160d

md5 out/ner_train_out/named_entity_recognition_v2.pt
# Expected: fb53cb6c17db50d62bd90a4dcea83fa4
```

### Check Data Integrity
```bash
# Count rows in datasets
wc -l data/manual_classifications.csv
wc -l data/manual_ner_extraction.csv
wc -l data/epmc_query_results_2022.csv

# Verify splits match
wc -l data/classif_splits_full/train.csv
wc -l data/classif_splits_full/val.csv
wc -l data/classif_splits_full/test.csv
```

---

## Troubleshooting Commands

### Check Python Environment
```bash
which python
python --version
pip list | grep -E "torch|transformers"
```

### Check Disk Space
```bash
df -h .
du -sh trained_models_25/
```

### Check Memory Usage
```bash
# During training
ps aux | grep python
top -p $(pgrep -f python)
```

### View Error Logs
```bash
# Recent errors
tail -100 logs/full_training_*.log | grep -i error

# Training errors
cat logs/classif_train_full_*/training.log
cat logs/ner_train_full_*/training.log
```

---

## Quick File Paths Reference

### Key Directories
```
GBC/inventory_2022/              # Repository root
├── data/                        # Datasets
├── src/                         # Source code
├── out/                         # Model outputs
├── docs/                        # Documentation
├── config/                      # Configuration files
├── trained_models_25/           # Model archives
├── experiment_archives/         # Experimental results
├── upload_logs/                 # Drive upload logs
└── download_logs/               # Drive download logs
```

### Key Files
```
docs/starting_doc.md             # Main AI agent reference
config/train_predict.yml         # Production config
requirements_frozen.txt          # Exact dependencies
run_full_training.sh            # Training script
rerun_2022_inventory.sh         # Prediction script
upload_to_drive.py              # Drive upload
download_from_drive.py          # Drive download
```

---

**Document Status**: ✅ Current
**Last Updated**: 2025-11-04
