# Restructure Rerun Notebook with Utility Functions & Fix Path Compatibility

**Created**: 2025-10-24
**Status**: Approved - Ready for Implementation
**Objective**: Restructure `rerun_2022_inventory_with_checkpoints.ipynb` to match the clean architecture of `full_training_pipeline_with_checkpoints_clean.ipynb`, create `src/rerun_utils.py` for all utility functions, and fix model archive path compatibility.

---

## Overview

This plan addresses multiple issues in the rerun notebook:
1. **Critical bug**: Scripts called with relative paths instead of absolute paths
2. **Path incompatibility**: Archive paths don't match training notebook output
3. **Code duplication**: 14 utility functions defined inline, 3 with name collisions
4. **Inconsistent architecture**: Doesn't follow training notebook pattern

---

## Part 1: Create `src/rerun_utils.py`

### New File: `src/rerun_utils.py`
Extract and consolidate all utility functions from the notebook into a reusable module (~250 lines).

**Functions to include:**

#### 1. Configuration & Validation
- `validate_rerun_config(config)` - Validate required fields and settings
  - Checks TRAINING_SESSION_ID is not empty
  - Validates RUN_MODE is "full" or "test"
  - Raises ValueError with clear messages

- `display_rerun_config(config)` - Pretty-print configuration summary
  - Session information
  - Path configuration
  - Processing configuration
  - Model paths
  - Output directories

#### 2. Model Management
- `load_models_with_traceability(training_session_id, inventory_dir, target_classif, target_ner)`
  - Validates training archive exists at `training_archives/{id}_full_training/`
  - Copies models to working locations
  - Returns: (model_source, training_session_used)
  - Raises FileNotFoundError with helpful messages

#### 3. Checkpoint Management (Generic, reusable)
- `check_local_results(results_path)` - Check if local results exist and are valid
  - Returns: (exists: bool, count: int)

- `check_drive_checkpoint(checkpoint_base, step_name)` - Check Google Drive checkpoint
  - Returns: bool

- `load_step_from_checkpoint(checkpoint_base, step_name, output_dir)` - Load any step from checkpoint
  - Copies files from checkpoint to output directory
  - Returns: bool (success)

- `save_step_to_checkpoint(checkpoint_base, step_name, output_dir)` - Save any step to checkpoint
  - Creates checkpoint directory
  - Copies files to checkpoint location

#### 4. Script Execution
- `run_prediction_script(script_name, inventory_dir, args_dict)` - Execute prediction script
  - Uses `!python "{inventory_dir}/src/{script_name}.py"` pattern
  - Builds command from args_dict
  - Captures output and timing
  - Returns: (success: bool, duration: float)

#### 5. Progress & Display
- `show_rerun_progress(progress, rerun_session_id)` - Display pipeline progress
  - Shows step name with status emoji
  - Session ID header

- `display_step_results(step_name, results_path)` - Show step statistics
  - File size
  - Row count for CSVs
  - Key metrics

#### 6. Archive Creation
- `create_rerun_archive(archive_dir, rerun_session_id, config, results_dirs)` - Create comprehensive archive
  - Copies all result files
  - Saves configuration with traceability
  - Creates README
  - Returns: archived_count

- `create_rerun_readme(archive_dir, rerun_session_id, config, stats)` - Generate README
  - Traceability chain
  - Processing configuration
  - Results summary
  - Usage instructions

#### 7. Data Validation
- `validate_input_data(input_path, expected_columns)` - Validate input CSV
  - Checks file exists
  - Validates columns present
  - Handles encoding issues
  - Returns: (valid: bool, row_count: int, columns: list)

---

## Part 2: Restructure Notebook

### Cell Structure (matching training notebook):

**Cell 1: Mount Google Drive** (unchanged)
```python
from google.colab import drive
drive.mount('/content/drive')

print("✅ Google Drive mounted successfully")
print("💾 Checkpoint and archive paths are now accessible")
print("🔗 Ready for hybrid checkpointing system")
```

**Cell 2: Configuration Cell** (NEW - consolidated all configuration)
```python
# =============================================================================
# STEP 2: RERUN PIPELINE CONFIGURATION
# =============================================================================

import os
import random
import string
from datetime import datetime

# =============================================================================
# USER-EDITABLE CONFIGURATION
# =============================================================================

# REQUIRED: Model Traceability - Link to specific training session
TRAINING_SESSION_ID = ""  # e.g., "2025-10-23-abc123" from training notebook
# This MUST match the UNIQUE_ID from your training notebook run

# Input Data Configuration
INPUT_DATA = "data/epmc_query_results_2022.csv"  # Fixed: 2022 dataset
RUN_MODE = "full"  # Options: "full" (21,677 papers) or "test" (subset)
TEST_SUBSET_SIZE = 1000  # Papers to process in test mode

# Processing Configuration
MAX_URLS = 3  # Maximum URLs to extract per paper

# =============================================================================
# AUTO-GENERATED CONFIGURATION (DO NOT EDIT BELOW THIS LINE)
# =============================================================================

# Session Management
RERUN_SESSION_ID = f"{datetime.now().strftime('%Y-%m-%d')}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
TIMESTAMP = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
RUN_DATE = datetime.now().strftime('%Y-%m-%d')

# Path Configuration
INVENTORY_DIRECTORY = "/content/drive/MyDrive/inventory_2022"
DATA_DIRECTORY = f"{INVENTORY_DIRECTORY}/data"

# Checkpoint Configuration
CHECKPOINT_BASE = f"{INVENTORY_DIRECTORY}/rerun_checkpoints/{RERUN_SESSION_ID}"
USE_CHECKPOINTS = True

# Model Archive Paths (FIXED to match training notebook)
TRAINING_ARCHIVE_BASE = f"{INVENTORY_DIRECTORY}/training_archives/{TRAINING_SESSION_ID}_full_training"
ARCHIVE_CLASSIF_MODEL = f"{TRAINING_ARCHIVE_BASE}/classification_model.pt"
ARCHIVE_NER_MODEL = f"{TRAINING_ARCHIVE_BASE}/ner_model.pt"

# Working Model Locations (where scripts expect them)
TARGET_CLASSIF_MODEL = "out/classif_train_out/article_classifier.pt"
TARGET_NER_MODEL = "out/ner_train_out/named_entity_recognition.pt"

# Output Configuration
OUTPUT_BASE_DIR = "inventory_classification_results"
OUTPUT_RUN_DIR = f"{OUTPUT_BASE_DIR}/{RUN_DATE}_2022_rerun"
CLASSIF_DIR = f"{OUTPUT_RUN_DIR}/classification"
NER_DIR = f"{OUTPUT_RUN_DIR}/ner"
URL_DIR = f"{OUTPUT_RUN_DIR}/url_extraction"
NAMES_DIR = f"{OUTPUT_RUN_DIR}/processed_names"
FINAL_DIR = f"{OUTPUT_RUN_DIR}/final_results"
LOG_DIR = f"{OUTPUT_RUN_DIR}/logs"

# Results Archive
RESULTS_ARCHIVE_BASE = f"{INVENTORY_DIRECTORY}/rerun_results/{RERUN_SESSION_ID}_2022_rerun"

# Results file paths
CLASSIF_RESULTS = f"{CLASSIF_DIR}/predictions.csv"
CLASSIF_POSITIVES = f"{CLASSIF_DIR}/predicted_positives.csv"
NER_RESULTS = f"{NER_DIR}/predictions.csv"
URL_RESULTS = f"{URL_DIR}/predictions.csv"
NAMES_RESULTS = f"{NAMES_DIR}/predictions.csv"
FINAL_RESULTS = f"{FINAL_DIR}/biodata_inventory_2022_rerun.csv"

# Environment
os.environ['PYTHONPATH'] = 'src'

# Configuration dictionary for utilities
config = {
    'rerun_session_id': RERUN_SESSION_ID,
    'training_session_id': TRAINING_SESSION_ID,
    'timestamp': TIMESTAMP,
    'run_mode': RUN_MODE,
    'test_subset_size': TEST_SUBSET_SIZE,
    'input_data': INPUT_DATA,
    'max_urls': MAX_URLS,
    'inventory_directory': INVENTORY_DIRECTORY,
    'data_directory': DATA_DIRECTORY,
    'checkpoint_base': CHECKPOINT_BASE,
    'training_archive_base': TRAINING_ARCHIVE_BASE,
    'results_archive_base': RESULTS_ARCHIVE_BASE,
    'created': datetime.now().isoformat()
}

print("=" * 60)
print("CONFIGURATION LOADED")
print("=" * 60)
```

**Cell 3: Validation & Display**
```python
# Validate and display configuration
import sys
from pathlib import Path

# Setup Python path
if f'{INVENTORY_DIRECTORY}/' not in sys.path:
    sys.path.append(f'{INVENTORY_DIRECTORY}/')

# Import utilities
from src.rerun_utils import validate_rerun_config, display_rerun_config

# Validate configuration
validate_rerun_config(config)

# Display configuration
display_rerun_config(config)

print("\n" + "=" * 60)
print("CONFIGURATION VALIDATED")
print("=" * 60)
```

**Cell 4: Environment Setup**
```python
# Install dependencies (Colab default versions)
print("🔧 Installing packages...")
!pip install transformers datasets evaluate seqeval nltk

print("\n✅ Dependencies installed")

# Download NLTK data
import nltk
import ssl

print("Downloading NLTK data...")
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt_tab')
print("✅ NLTK data downloaded")

# Import all utilities
from src.rerun_utils import *

# Import libraries
import pandas as pd
import numpy as np
import torch
import transformers
import shutil
import time
import json

# Verify environment
print(f"\n🐍 Python: {sys.version.split()[0]}")
print(f"🔥 PyTorch: {torch.__version__}")
print(f"🤗 Transformers: {transformers.__version__}")
print(f"🎯 GPU Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")

print("\n✅ Environment setup complete")
```

**Cell 5: GPU Check**
```python
print("🔍 GPU Environment Check:")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")

if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    print(f"CUDA version: {torch.version.cuda}")
    print("✅ GPU acceleration available")
else:
    print("⚠️ No GPU detected - inference will be slower")
    print("Consider enabling GPU runtime: Runtime > Change runtime type > GPU")
```

**Cell 6: Checkpoint System Setup**
```python
print("🔧 Setting up checkpoint system...")

# Create checkpoint directory
Path(CHECKPOINT_BASE).mkdir(parents=True, exist_ok=True)

# Save configuration
with open(f"{CHECKPOINT_BASE}/config.json", 'w') as f:
    json.dump(config, f, indent=2)

print(f"✅ Config saved: {CHECKPOINT_BASE}/config.json")

# Initialize progress tracker
progress = {
    "input_validation": "⏳ pending",
    "classification": "⏳ pending",
    "ner_processing": "⏳ pending",
    "url_extraction": "⏳ pending",
    "final_processing": "⏳ pending"
}

show_rerun_progress(progress, RERUN_SESSION_ID)
print("\n✅ Checkpoint system ready!")
```

**Cell 7: Model Loading with Traceability**
```python
print("🤖 Model Loading & Traceability System")
print("=" * 50)

# Create target directories
Path("out/classif_train_out").mkdir(parents=True, exist_ok=True)
Path("out/ner_train_out").mkdir(parents=True, exist_ok=True)

# Load models with traceability
model_source, training_session_used = load_models_with_traceability(
    TRAINING_SESSION_ID,
    INVENTORY_DIRECTORY,
    TARGET_CLASSIF_MODEL,
    TARGET_NER_MODEL
)

# Update config with traceability
config['model_traceability'] = {
    'model_source': model_source,
    'training_session_used': training_session_used,
    'models_loaded_at': datetime.now().isoformat()
}

# Save updated config
with open(f"{CHECKPOINT_BASE}/config.json", 'w') as f:
    json.dump(config, f, indent=2)

print(f"\n🎯 Model Traceability Established:")
print(f"   Training Session → {training_session_used}")
print(f"   Rerun Session → {RERUN_SESSION_ID}")
print(f"   Model Source → {model_source}")
print("\n✅ Models ready for inference!")
```

**Cell 8: Input Validation**
```python
print("📚 Input Data Validation")
print("=" * 50)

# Create output directories
output_dirs = [OUTPUT_RUN_DIR, CLASSIF_DIR, NER_DIR, URL_DIR, NAMES_DIR, FINAL_DIR, LOG_DIR]
for dir_path in output_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# Validate input data
valid, total_papers, columns = validate_input_data(
    f"{DATA_DIRECTORY}/{INPUT_DATA.split('/')[-1]}",
    ['pmid', 'title', 'abstractText']
)

if not valid:
    raise ValueError(f"Input data validation failed for {INPUT_DATA}")

print(f"✅ Input data validated: {total_papers:,} papers")
print(f"📋 Columns: {columns}")

# Handle test mode
if RUN_MODE == "test":
    print(f"\n🧪 Test Mode: Using subset of {TEST_SUBSET_SIZE} papers")
    input_df = pd.read_csv(f"{DATA_DIRECTORY}/{INPUT_DATA.split('/')[-1]}").head(TEST_SUBSET_SIZE)
    test_input_path = f"{OUTPUT_RUN_DIR}/test_input.csv"
    input_df.to_csv(test_input_path, index=False)
    effective_input = test_input_path
    papers_to_process = len(input_df)
    print(f"📁 Test subset saved: {test_input_path}")
else:
    effective_input = f"{DATA_DIRECTORY}/{INPUT_DATA.split('/')[-1]}"
    papers_to_process = total_papers
    print(f"\n🔍 Full Mode: Processing all {papers_to_process:,} papers")

progress["input_validation"] = "✅ completed"
show_rerun_progress(progress, RERUN_SESSION_ID)
print("\n✅ Input validation complete")
```

**Cell 9: Classification Pipeline** (CLEANED UP - ~15 lines vs ~50)
```python
progress['classification'] = '🔄 running'
show_rerun_progress(progress, RERUN_SESSION_ID)

print("📋 Step 1/5: Classification Pipeline")
print("=" * 40)

# Check existing results
local_exists, local_count = check_local_results(CLASSIF_RESULTS)

if local_exists:
    print(f"✅ Local classification results found ({local_count:,} papers)")
    progress['classification'] = '✅ loaded from local'

elif USE_CHECKPOINTS and check_drive_checkpoint(CHECKPOINT_BASE, 'classification'):
    print("📥 Loading from checkpoint...")
    load_step_from_checkpoint(CHECKPOINT_BASE, 'classification', CLASSIF_DIR)
    df = pd.read_csv(CLASSIF_RESULTS)
    print(f"✅ Loaded {len(df):,} predictions from checkpoint")
    progress['classification'] = '✅ loaded from checkpoint'

else:
    print("🚀 Running classification...")
    print(f"📅 Input: {effective_input}")
    print(f"🤖 Model: {TARGET_CLASSIF_MODEL}")

    start_time = time.time()

    # Run classification
    success, duration = run_prediction_script(
        'class_predict',
        INVENTORY_DIRECTORY,
        {
            '-i': effective_input,
            '-o': CLASSIF_DIR,
            '-c': TARGET_CLASSIF_MODEL
        }
    )

    if success:
        # Filter positives
        df_all = pd.read_csv(CLASSIF_RESULTS)
        positives = df_all[df_all['predicted_label'] == 'bio-resource']
        positives.to_csv(CLASSIF_POSITIVES, index=False)

        duration_mins = int(duration // 60)
        duration_secs = int(duration % 60)
        print(f"✅ Classification completed in {duration_mins}m {duration_secs}s")
        print(f"📊 Total: {len(df_all):,}, Bio-resource: {len(positives):,} ({len(positives)/len(df_all)*100:.1f}%)")

        # Save to checkpoint
        if USE_CHECKPOINTS:
            save_step_to_checkpoint(CHECKPOINT_BASE, 'classification', CLASSIF_DIR)
            print("💾 Saved to checkpoint")

        progress['classification'] = '✅ completed'
    else:
        raise RuntimeError("Classification processing failed")

show_rerun_progress(progress, RERUN_SESSION_ID)
print("🎯 Classification step complete!")
```

**Cell 10: NER Pipeline** (similar pattern, ~15 lines)
```python
progress['ner_processing'] = '🔄 running'
show_rerun_progress(progress, RERUN_SESSION_ID)

print("🏷️ Step 2/5: NER Pipeline")
print("=" * 40)

# Check existing results
local_exists, local_count = check_local_results(NER_RESULTS)

if local_exists:
    print(f"✅ Local NER results found ({local_count:,} papers)")
    progress['ner_processing'] = '✅ loaded from local'

elif USE_CHECKPOINTS and check_drive_checkpoint(CHECKPOINT_BASE, 'ner_processing'):
    print("📥 Loading from checkpoint...")
    load_step_from_checkpoint(CHECKPOINT_BASE, 'ner_processing', NER_DIR)
    df = pd.read_csv(NER_RESULTS)
    print(f"✅ Loaded {len(df):,} NER results from checkpoint")
    progress['ner_processing'] = '✅ loaded from checkpoint'

else:
    print("🚀 Running NER...")
    print(f"📅 Input: {CLASSIF_POSITIVES}")
    print(f"🤖 Model: {TARGET_NER_MODEL}")

    # Verify input exists
    if not Path(CLASSIF_POSITIVES).exists():
        raise FileNotFoundError(f"Bio-resource papers file not found: {CLASSIF_POSITIVES}")

    input_df = pd.read_csv(CLASSIF_POSITIVES)
    print(f"📊 Bio-resource papers to process: {len(input_df):,}")

    # Run NER
    success, duration = run_prediction_script(
        'ner_predict',
        INVENTORY_DIRECTORY,
        {
            '-i': CLASSIF_POSITIVES,
            '-o': NER_DIR,
            '-c': TARGET_NER_MODEL
        }
    )

    if success:
        df = pd.read_csv(NER_RESULTS)
        duration_mins = int(duration // 60)
        duration_secs = int(duration % 60)
        print(f"✅ NER completed in {duration_mins}m {duration_secs}s")
        print(f"📊 Papers with NER results: {len(df):,}")

        # Save to checkpoint
        if USE_CHECKPOINTS:
            save_step_to_checkpoint(CHECKPOINT_BASE, 'ner_processing', NER_DIR)
            print("💾 Saved to checkpoint")

        progress['ner_processing'] = '✅ completed'
    else:
        raise RuntimeError("NER processing failed")

show_rerun_progress(progress, RERUN_SESSION_ID)
print("🎯 NER step complete!")
```

**Cell 11: Post-Processing Pipeline** (URL Extraction + Name Processing)
```python
print("🔍 Step 3-4/5: Post-Processing Pipeline")
print("=" * 40)

# URL Extraction
print("\n📋 Step 3/5: URL Extraction")
url_exists, url_count = check_local_results(URL_RESULTS)

if url_exists:
    print(f"✅ URL extraction results found ({url_count:,} entries)")
else:
    print("🚀 Starting URL extraction...")
    success, duration = run_prediction_script(
        'url_extractor',
        INVENTORY_DIRECTORY,
        {
            NER_RESULTS: None,  # positional arg
            '-o': URL_DIR,
            '-x': str(MAX_URLS)
        }
    )

    if success:
        df = pd.read_csv(URL_RESULTS)
        print(f"✅ URL extraction completed in {duration:.1f}s")
        print(f"📊 Papers with URLs: {len(df):,}")
    else:
        raise RuntimeError("URL extraction failed")

progress["url_extraction"] = "✅ completed"

# Name Processing
print("\n📋 Step 4/5: Name Processing")
names_exists, names_count = check_local_results(NAMES_RESULTS)

if names_exists:
    print(f"✅ Name processing results found ({names_count:,} entries)")
else:
    print("🚀 Starting name processing...")
    success, duration = run_prediction_script(
        'process_names',
        INVENTORY_DIRECTORY,
        {
            URL_RESULTS: None,  # positional arg
            '-o': NAMES_DIR
        }
    )

    if success:
        df = pd.read_csv(NAMES_RESULTS)
        print(f"✅ Name processing completed in {duration:.1f}s")
        print(f"📊 Processed entries: {len(df):,}")
    else:
        raise RuntimeError("Name processing failed")

show_rerun_progress(progress, RERUN_SESSION_ID)
print("🎯 Post-processing steps complete!")
```

**Cell 12: Final Results & Comprehensive Archive**
```python
print("🎉 Step 5/5: Final Results Creation & Archive")
print("=" * 40)

# Create final inventory
print("\n📋 Creating final inventory...")
if Path(NAMES_RESULTS).exists():
    shutil.copy2(NAMES_RESULTS, FINAL_RESULTS)
    final_df = pd.read_csv(FINAL_RESULTS)
    final_count = len(final_df)
    print(f"✅ Final inventory created: {final_count:,} biodata resources")
    print(f"📁 Location: {FINAL_RESULTS}")
else:
    raise FileNotFoundError(f"Name processing results not found: {NAMES_RESULTS}")

progress["final_processing"] = "✅ completed"

# Create comprehensive archive
print(f"\n💾 Creating comprehensive archive...")
print(f"📦 Archive location: {RESULTS_ARCHIVE_BASE}")

archived_count = create_rerun_archive(
    RESULTS_ARCHIVE_BASE,
    RERUN_SESSION_ID,
    config,
    {
        'classification': CLASSIF_DIR,
        'ner': NER_DIR,
        'url_extraction': URL_DIR,
        'names': NAMES_DIR,
        'final': FINAL_DIR
    }
)

print(f"\n✅ Archive created with {archived_count} items")

# Final summary
completion_time = datetime.now()
processing_time = completion_time - datetime.fromisoformat(config['created'])
processing_mins = int(processing_time.total_seconds() / 60)
processing_hours = processing_mins // 60
processing_mins_remainder = processing_mins % 60

print("\n" + "🎉" * 20)
print("🎉 2022 INVENTORY RERUN COMPLETE")
print("🎉" * 20)

show_rerun_progress(progress, RERUN_SESSION_ID)

print(f"\n📊 Final Status:")
print(f"   Rerun Session ID: {RERUN_SESSION_ID}")
print(f"   Training Session Used: {training_session_used}")
print(f"   Completion Time: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Processing Time: {processing_hours}h {processing_mins_remainder}m")
print(f"   Papers Processed: {papers_to_process:,}")
print(f"   Final Inventory: {final_count:,} resources")

print(f"\n📁 Results Archive:")
print(f"   📁 {RESULTS_ARCHIVE_BASE}")
print(f"   📄 Main Output: final_inventory.csv")
print(f"   📄 Configuration: config_with_traceability.json")
print(f"   📄 Documentation: README.md")

print(f"\n🎯 Model Traceability:")
print(f"   Training Session → {training_session_used}")
print(f"   Rerun Session → {RERUN_SESSION_ID}")
print(f"   Models Source → {model_source}")
print(f"   Archive Location → {RESULTS_ARCHIVE_BASE}")

print(f"\n✨ Rerun completed successfully!")
print(f"🆔 Session ID: {RERUN_SESSION_ID} (save this for future reference)")
print(f"🔗 Training Session: {training_session_used} (linked models)")

print(f"\n🏁 Completed at {completion_time.strftime('%H:%M:%S')}")
print("📋 Full traceability chain established from training to final inventory!")
```

---

## Part 3: Update Documentation

### File: `docs/starting_doc.md`

**Location**: Lines 271-276

**Change FROM:**
```markdown
### **Training-Inventory Compatibility**
- **Archive Path Issue**: Training uses `training_archives/`, inventory expects `trained_models_archive/`
- **Model Deployment**: Training automatically deploys to standard locations for compatibility
- **Session Linking**: Use training UNIQUE_ID as TRAINING_SESSION_ID in inventory notebooks
- **Resolution Status**: ⚠️ Archive path mismatch requires update (see compatibility analysis)
- **Pending Fix**: `src/training_utils.py` needs archive path update for full compatibility
```

**Change TO:**
```markdown
### **Training-Inventory Compatibility**
- **Archive Path**: ✅ FIXED - Both use `training_archives/{UNIQUE_ID}_full_training/`
- **Model Traceability**: ✅ REQUIRED - TRAINING_SESSION_ID mandatory in rerun notebook
- **Session Linking**: Training UNIQUE_ID → Rerun TRAINING_SESSION_ID → Full audit trail
- **Utility Functions**: Training uses `src/training_utils.py`, Rerun uses `src/rerun_utils.py`
- **Resolution Status**: ✅ Fixed as of 2025-10-24 - Full traceability enforced
- **Script Execution**: Both use absolute paths with INVENTORY_DIRECTORY prefix
```

**Add new section after October 24, 2025 PyTorch fix (after line 491):**

```markdown
## 📝 **October 24, 2025 Rerun Notebook Restructure**

### **Architecture Improvements**

**Created**: `src/rerun_utils.py` - Reusable utility functions for inventory processing (~250 lines)

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
```

---

## Part 4: Implementation Order

### Step 1: Create `src/rerun_utils.py`
- Write all 13 utility functions
- Add comprehensive docstrings
- Include error handling
- Test imports

### Step 2: Restructure Notebook
- Create new notebook with 12 cells
- Cell 1: Mount (copy from training)
- Cell 2: Configuration (new consolidated)
- Cell 3: Validation & Display
- Cell 4: Environment Setup
- Cell 5: GPU Check
- Cell 6: Checkpoint Setup
- Cell 7: Model Loading
- Cell 8: Input Validation
- Cell 9: Classification (simplified)
- Cell 10: NER (simplified)
- Cell 11: Post-Processing (simplified)
- Cell 12: Final Results (simplified)

### Step 3: Update Documentation
- Update compatibility section in starting_doc.md
- Add new section for October 24 restructure
- Update file references

### Step 4: Testing
- Test with training session ID
- Verify all paths resolve correctly
- Test checkpoint recovery
- Verify archive creation

---

## Files Summary

### Files to CREATE:
1. `src/rerun_utils.py` - NEW utility module (~250 lines)

### Files to MODIFY:
1. `rerun_2022_inventory_with_checkpoints.ipynb` - Complete restructure (12 cells)
2. `docs/starting_doc.md` - Update compatibility section + add new section

### Files to REFERENCE:
- `src/training_utils.py` - Pattern reference
- `full_training_pipeline_with_checkpoints_clean.ipynb` - Structure reference

---

## Expected Outcomes

✅ **Rerun notebook matches training notebook architecture**
- Clean configuration cell with all variables
- Mount Google Drive first
- Utility functions in separate module
- Consistent code style
- 12 clean cells vs 15 cluttered cells

✅ **Critical bugs fixed**
- Script paths use absolute `{INVENTORY_DIRECTORY}/src/` prefix
- Archive paths correctly point to `training_archives/{ID}_full_training/`
- TRAINING_SESSION_ID is mandatory (enforced validation)
- No function name collisions

✅ **Code quality improvements**
- ~150 lines of duplication eliminated
- Cells are 50-70% shorter and clearer
- Follows DRY principle
- Reusable utility functions
- Testable code

✅ **Full traceability**
- Training Session → Rerun Session → Results
- Complete audit trail preserved
- Archive system works end-to-end
- Configuration tracking

✅ **Documentation updated**
- Compatibility section reflects current state
- New section documents restructure
- Clear instructions for users
- File references accurate

---

## Testing Checklist

After implementation:
1. ✅ Run training notebook, capture UNIQUE_ID
2. ✅ Set TRAINING_SESSION_ID in rerun notebook
3. ✅ Verify config validation catches empty TRAINING_SESSION_ID
4. ✅ Verify models load from training archive (correct path)
5. ✅ Run full pipeline in test mode (1000 papers)
6. ✅ Verify all script paths resolve correctly
7. ✅ Verify checkpoint recovery works for each step
8. ✅ Verify final archive created with traceability
9. ✅ Confirm configuration display shows all paths correctly
10. ✅ Verify no import errors from rerun_utils

---

## Success Criteria

- ✅ Notebook runs without path errors
- ✅ Models load from training archive successfully
- ✅ All 5 pipeline steps complete
- ✅ Checkpoint system works for all steps
- ✅ Final archive contains all expected files
- ✅ Traceability chain is complete and documented
- ✅ Code is clean, readable, and maintainable
- ✅ Documentation is accurate and up-to-date

---

**Plan Status**: Ready for Implementation
**Estimated Time**: 2-3 hours
**Risk Level**: Low (following established patterns)
