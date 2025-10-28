# Historical Updates & Session Changelog

**Purpose**: Detailed session-by-session changelog documenting technical problems solved, architecture evolution, and refactoring work.

**Audience**: Developers needing to understand project history, architecture decisions, and technical evolution.

**For Operational Guide**: See [`starting_doc.md`](starting_doc.md)
**For Technical Issues**: See [`PYTORCH_CHECKPOINT_FIX.md`](PYTORCH_CHECKPOINT_FIX.md)

---

## Update Log (Newest First)

### **October 28, 2025: Training Notebook Simplification**

**Files**: `full_training_pipeline_simplified.ipynb`, `src/training_utils.py`

**Motivation**: Checkpoint system deprecated due to data contamination risks (see `PYTORCH_CHECKPOINT_FIX.md` Addendum). One production run showed 24% confidence score drop from loading wrong cached data.

**Key Changes**:
- ✅ **New Simplified Notebook**: Created `full_training_pipeline_simplified.ipynb` without checkpoint complexity
- ✅ **TEST_MODE Toggle**: Single variable switch between test (5-8 min, 100/50 samples) and production (9.5 hr, 1635/554 samples)
- ✅ **Session ID Suffix**: Test runs now include `_test` suffix (e.g., `2025-10-28-abc123_test`)
- ✅ **Fixed Archive Function**: Made `checkpoint_base` reference conditional in `create_final_archive()`
- ✅ **Updated Archive README**: Removed checkpoint references, added test mode indicator

**Benefits**:
- 🛡️ **Data Integrity**: No checkpoint contamination risk - each run produces fresh results
- 🐛 **Simpler Debugging**: Linear pipeline with single execution path
- ⚡ **Code Reduction**: ~100+ fewer lines of checkpoint logic
- 📚 **Code/Docs Alignment**: Matches documented decision to deprecate checkpoints
- 🧪 **Easy Testing**: Change one variable to switch modes

**Files Modified**:
- `full_training_pipeline_simplified.ipynb` - NEW simplified training notebook (19 cells)
- `src/training_utils.py` - Fixed `create_final_archive()` and archive README template
- `docs/starting_doc.md` - Updated to reference simplified notebook
- `docs/TRAINING_NOTEBOOK_SIMPLIFICATION.md` - NEW implementation documentation
- `plans/2025-10-28_training_notebook_simplification_plan.md` - NEW implementation plan

**Migration Path**:
- **Old notebook**: `full_training_pipeline_with_checkpoints_clean.ipynb` - Still works, marked DEPRECATED
- **New notebook**: `full_training_pipeline_simplified.ipynb` - Recommended for all new training runs
- **Backward Compatible**: `training_utils.py` works with both versions

**Related**: `docs/PYTORCH_CHECKPOINT_FIX.md` (Addendum) for checkpoint corruption investigation

---

### October 24, 2025: Rerun Notebook Restructure

**Architecture Improvements**

**Created**: `src/rerun_utils.py` - Reusable utility functions for inventory processing (~590 lines)

**Key Changes**:
- ✅ **Clean Configuration Cell**: All variables defined upfront (similar to training notebook)
- ✅ **Utility Functions**: Extracted 14 inline functions to reusable module
- ✅ **Fixed Script Paths**: Changed from relative `src/` to absolute `{INVENTORY_DIRECTORY}/src/`
- ✅ **Fixed Archive Paths**: Training archives now correctly reference `training_archives/{ID}_full_training/`
- ✅ **Mandatory Traceability**: TRAINING_SESSION_ID is required, no fallback to production models
- ✅ **Eliminated Duplication**: Removed 3 duplicate checkpoint function definitions
- ✅ **Consistent Pattern**: Matches training notebook architecture and style

**Files Modified**:
- `rerun_2022_inventory_with_checkpoints.ipynb` - Complete restructure with 12 clean cells
- `src/rerun_utils.py` - NEW utility module with 13 reusable functions
- `docs/starting_doc.md` - Updated compatibility documentation

**Column Name Fix**:
- ✅ Fixed Cell 8 validation to use correct 2022 dataset column names (`id`, `abstract` instead of `pmid`, `abstractText`)

**Benefits**:
- 🧹 **Cleaner Cells**: Pipeline cells reduced from 30-50 lines to 10-15 lines
- 🔄 **Reusable**: Functions can be used in future inventory processing notebooks
- 🐛 **Bug Fixes**: Critical script path bugs resolved
- 📊 **Maintainability**: Change logic once, works everywhere
- ✅ **Testable**: Utility functions can be unit tested
- 🎯 **Consistent**: Follows same architecture as training notebook

**Cell Structure**:
1. Mount Google Drive
2. Configuration (all variables)
3. Validation & Display
4. Environment Setup
5. GPU Check
6. Checkpoint System Setup
7. Model Loading with Traceability
8. Input Validation
9. Classification Pipeline (~15 lines)
10. NER Pipeline (~15 lines)
11. Post-Processing (URL + Names)
12. Final Results & Archive

**Utility Functions**:
- `validate_rerun_config()` - Config validation
- `display_rerun_config()` - Config display
- `load_models_with_traceability()` - Model loading
- `check_local_results()` - Check local files
- `check_drive_checkpoint()` - Check Google Drive
- `load_step_from_checkpoint()` - Load from checkpoint
- `save_step_to_checkpoint()` - Save to checkpoint
- `run_prediction_script()` - Execute scripts
- `show_rerun_progress()` - Progress display
- `display_step_results()` - Results display
- `create_rerun_archive()` - Archive creation
- `create_rerun_readme()` - README generation
- `validate_input_data()` - Input validation

---

### October 24, 2025: PyTorch 2.6 Compatibility Fix

**Issue**: PyTorch 2.6 changed default `weights_only` parameter in `torch.load()` from `False` to `True` for security. This broke model evaluation because checkpoints contain custom classes (`Metrics` NamedTuple).

**Solution**: Added `weights_only=False` parameter to all `torch.load()` calls for trusted checkpoints.

**Files Modified**:
- `src/inventory_utils/filing.py` - Fixed `get_classif_model()` (line 39) and `get_ner_model()` (line 70)
- `src/model_picker.py` - Fixed `get_metrics()` (line 68)

**Impact**: Model evaluation (Step 4) now completes successfully in Google Colab training notebook.

**Note**: This issue was superseded by the comprehensive PyTorch 2.8 checkpoint compatibility fix documented in [`PYTORCH_CHECKPOINT_FIX.md`](PYTORCH_CHECKPOINT_FIX.md).

---

### October 23, 2025: Session Summary

**Major Accomplishments**

**Documentation and Organization**
- ✅ **Living Document Creation**: Created comprehensive AI agent reference guide (`docs/starting_doc.md`)
- ✅ **Directory Reorganization**: Moved all markdown files to centralized `docs/` directory for better organization
- ✅ **Git Workflow Setup**: Configured fork-based development workflow with proper upstream tracking
- ✅ **File Path Updates**: Updated all documentation to reflect new centralized structure

**Google Colab Integration**
- ✅ **Notebook Conversion**: Successfully converted `run_full_training.sh` to Google Colab notebook
- ✅ **Hybrid Checkpointing System**: Implemented comprehensive checkpoint system with Google Drive backup
- ✅ **Dependency Management**: Resolved complex compatibility issues between transformers/datasets/evaluate versions
- ✅ **GPU Optimization**: Configured notebook for optimal Google Colab GPU performance

**Code Compatibility Fixes**
- ✅ **NumPy Updates**: Fixed `numpy.core.numeric` import issues in `ner_data_generator.py`
- ✅ **Pandas Testing**: Updated pandas testing imports for modern compatibility
- ✅ **AdamW Import**: Fixed AdamW import issues in `ner_train.py` for newer transformers versions
- ✅ **File Encoding**: Implemented robust multi-encoding CSV reading with fallback handling

**Session Deliverables**
- ✅ **Training Notebook**: `full_training_pipeline_with_checkpoints_clean.ipynb` - Production-ready Colab training notebook with path fixes
- ✅ **Inventory Update Notebook**: `inventory_update_pipeline_with_checkpoints.ipynb` - Complete inventory processing pipeline
- ✅ **Enhanced Utility Functions**: Updated `src/training_utils.py` with session-specific directory support
- ✅ **Path Configuration System**: Complete INVENTORY_DIRECTORY and DATA_DIRECTORY implementation
- ✅ **Conversion Plans**: Detailed technical plans for bash-to-notebook conversion
- ✅ **Updated Documentation**: Comprehensive updates to starting document and file references

**Technical Solutions Implemented**

**Dependency Resolution**
```yaml
Previous Issues:
- transformers/datasets/evaluate version conflicts
- numpy binary incompatibility with pandas
- AdamW import changes in newer transformers

Solutions Applied:
- Flexible version ranges: "transformers>=4.35.0,<5.0"
- Let Colab manage numpy/pandas versions automatically
- Updated AdamW import: torch.optim.AdamW instead of transformers.optimization.AdamW
- Multi-encoding file reading with UTF-8 → latin-1 → cp1252 → binary fallback
```

**Checkpointing System**
```python
UniqueID System: f"{datetime.now().strftime('%Y-%m-%d')}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
Checkpoint Path: "/content/drive/MyDrive/inventory_2022/checkpoints/{UNIQUE_ID}/"
Backup Strategy: Local files first, then Google Drive backup after each major step
Recovery: Smart detection of existing checkpoints with configuration validation
```

**Files Modified**
- `src/ner_data_generator.py` - Fixed numpy/pandas compatibility (lines 15-16, multiple NaN references)
- `src/ner_train.py` - Fixed AdamW import compatibility (line 14, removed optimization import)
- `docs/starting_doc.md` - Added comprehensive session documentation and file references

---

### October 23, 2025: Path Configuration Updates

**Critical Path Fixes Implemented**

**Problem Resolved**: Google Colab notebook was failing to find Python scripts and training data due to incorrect path configuration.

**Root Cause**:
- Notebook running from `/content/` but scripts located at `/content/drive/MyDrive/inventory_2022/src/`
- Training data expected at `/content/drive/MyDrive/inventory_2022/data/`
- All script paths were relative (`src/script.py`) instead of absolute

**Solution Implemented**:
- ✅ **INVENTORY_DIRECTORY Variable**: Added `INVENTORY_DIRECTORY = "/content/drive/MyDrive/inventory_2022"`
- ✅ **DATA_DIRECTORY Configuration**: Updated to `DATA_DIRECTORY = f"{INVENTORY_DIRECTORY}/data"`
- ✅ **Script Path Updates**: All Python script calls now use `{INVENTORY_DIRECTORY}/src/script_name.py`
- ✅ **Python Path Fix**: Updated `sys.path.append(f'{INVENTORY_DIRECTORY}/')` for imports
- ✅ **Utility Function Updates**: Enhanced all functions in `src/training_utils.py` to support session-specific directories

**Updated Function Signatures**

**Enhanced Utility Functions**:
```python
# Core directory and path management
create_directory_structure(unique_id=None)
check_prerequisites(data_directory="data")
check_local_splits(classif_splits_dir="...", ner_splits_dir="...")

# Checkpoint management with flexible paths
load_splits_from_checkpoint(checkpoint_path, classif_splits_dir="...", ner_splits_dir="...")
save_splits_to_checkpoint(checkpoint_path, classif_splits_dir="...", ner_splits_dir="...")

# Model deployment with session awareness
deploy_production_models(classif_output_dir="...", ner_output_dir="...")
create_final_archive(archive_dir, unique_id, config, classif_output_dir=None, ner_output_dir=None)

# Statistics display with parameterized paths
display_split_statistics(classif_splits_dir="...", ner_splits_dir="...")
```

**Notebook Configuration Structure**

**Path Variables**:
```python
# Core path configuration
INVENTORY_DIRECTORY = "/content/drive/MyDrive/inventory_2022"
DATA_DIRECTORY = f"{INVENTORY_DIRECTORY}/data"

# Training data paths
CLASSIF_DATA = f"{DATA_DIRECTORY}/manual_classifications.csv"
NER_DATA = f"{DATA_DIRECTORY}/manual_ner_extraction.csv"

# Session-specific output directories
CLASSIF_SPLITS_DIR = f"data/classif_splits_full_{UNIQUE_ID}"
NER_SPLITS_DIR = f"data/ner_splits_full_{UNIQUE_ID}"
CLASSIF_OUTPUT_DIR = f"out/classif_train_full_{UNIQUE_ID}"
NER_OUTPUT_DIR = f"out/ner_train_full_{UNIQUE_ID}"
```

**Script Path Resolution**

**Updated Script Calls**:
```bash
# Data generation
!python "{INVENTORY_DIRECTORY}/src/class_data_generator.py" ...
!python "{INVENTORY_DIRECTORY}/src/ner_data_generator.py" ...

# Model training
!python "{INVENTORY_DIRECTORY}/src/class_train.py" ...
!python "{INVENTORY_DIRECTORY}/src/ner_train.py" ...

# Model evaluation
!python "{INVENTORY_DIRECTORY}/src/class_final_eval.py" ...
!python "{INVENTORY_DIRECTORY}/src/ner_final_eval.py" ...
```

**Backwards Compatibility**

**Legacy Support**: All utility functions maintain backwards compatibility through default parameters, ensuring existing bash scripts continue to work unchanged.

**Dual Mode Operation**:
- **Session Mode**: `create_directory_structure(UNIQUE_ID)` for Colab notebooks
- **Legacy Mode**: `create_directory_structure()` for bash scripts

**Training-Inventory Compatibility**:
- **Archive Path**: ✅ FIXED - Both use `training_archives/{UNIQUE_ID}_full_training/`
- **Model Traceability**: ✅ REQUIRED - TRAINING_SESSION_ID mandatory in rerun notebook
- **Session Linking**: Training UNIQUE_ID → Rerun TRAINING_SESSION_ID → Full audit trail
- **Utility Functions**: Training uses `src/training_utils.py`, Rerun uses `src/rerun_utils.py`
- **Resolution Status**: ✅ Fixed as of 2025-10-24 - Full traceability enforced
- **Script Execution**: Both use absolute paths with INVENTORY_DIRECTORY prefix

---

## Document Maintenance

**When to Update**:
- After completing technical refactoring work
- When resolving compatibility issues
- After implementing new architecture patterns
- When making significant code organizational changes

**Update Process**:
1. Add new entry at the top (reverse chronological order)
2. Include date, summary, and detailed changes
3. List files modified with specific line numbers when relevant
4. Reference related technical documents
5. Describe impact and benefits

---

**Document Status**: ✅ **CURRENT**
**Last Updated**: 2025-10-28
**Location**: `GBC/inventory_2022/docs/HISTORICAL_UPDATES.md`
