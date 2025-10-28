"""
Rerun Utilities
~~~

Utility functions for the 2022 inventory rerun pipeline.
These functions support checkpoint management, model loading,
script execution, and archive creation for inventory processing.

Authors: AI Agent (Claude Code)
Created: 2025-10-24
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, List, Optional, Any

import pandas as pd


# ---------------------------------------------------------------------------
def validate_rerun_config(config: Dict[str, Any]) -> None:
    """
    Validate rerun configuration for required fields and valid settings

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If validation fails with descriptive error message
    """
    # Check TRAINING_SESSION_ID is not empty
    training_id = config.get('training_session_id', '').strip()
    if not training_id:
        raise ValueError(
            "❌ TRAINING_SESSION_ID is REQUIRED!\n"
            "Please specify the UNIQUE_ID from your training notebook.\n"
            "Example: TRAINING_SESSION_ID = '2025-10-23-abc123'"
        )

    print("✅ Configuration validation passed")


# ---------------------------------------------------------------------------
def display_rerun_config(config: Dict[str, Any]) -> None:
    """
    Pretty-print rerun configuration summary

    Args:
        config: Configuration dictionary with all settings
    """
    print("🔧 2022 Rerun Configuration")
    print("=" * 60)

    print(f"\n📋 Session Information:")
    print(f"   🆔 Rerun Session ID: {config['rerun_session_id']}")
    print(f"   🔗 Training Session ID: {config['training_session_id']}")
    print(f"   📅 Timestamp: {config['timestamp']}")

    print(f"\n📂 Path Configuration:")
    print(f"   📁 Inventory Directory: {config['inventory_directory']}")
    print(f"   📁 Training Archive: {config['training_archive_base']}")
    print(f"   📁 Results Archive: {config['results_archive_base']}")

    print(f"\n📊 Processing Configuration:")
    print(f"   📋 Input Data: {config['input_data']}")
    print(f"   🔍 Test Mode: {config.get('test_mode', False)}")
    if config.get('test_mode'):
        print(f"   🧪 Test Subset: {config.get('test_subset_size', 1000)} papers")
    print(f"   🔗 Max URLs: {config['max_urls']}")

    print("\n" + "=" * 60)


# ---------------------------------------------------------------------------
def load_models_with_traceability(
        training_session_id: str,
        inventory_dir: str,
        target_classif: str,
        target_ner: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Load models from training archive with full traceability and verification

    Args:
        training_session_id: Training session UNIQUE_ID
        inventory_dir: Base inventory directory path
        target_classif: Target path for classification model
        target_ner: Target path for NER model

    Returns:
        Tuple of (model_source, training_session_used, verification_report)

    Raises:
        FileNotFoundError: If training archive or models not found
        ValueError: If checksum verification fails
    """
    print(f"🔗 Using models from training session: {training_session_id}")

    # Source paths (training archive)
    archive_base = f"{inventory_dir}/training_archives/{training_session_id}_full_training"
    archive_classif = f"{archive_base}/classification_model.pt"
    archive_ner = f"{archive_base}/ner_model.pt"

    print(f"📁 Archive location: {archive_base}")

    # Validate archive exists
    if not Path(archive_base).exists():
        raise FileNotFoundError(
            f"Training archive not found: {archive_base}\n"
            f"Please verify TRAINING_SESSION_ID is correct.\n"
            f"Expected archive from training notebook UNIQUE_ID."
        )

    if not Path(archive_classif).exists():
        raise FileNotFoundError(f"Classification model not found: {archive_classif}")

    if not Path(archive_ner).exists():
        raise FileNotFoundError(f"NER model not found: {archive_ner}")

    print("✅ Training archive validated")

    # Verify checksums before copying
    manifest_path = f"{archive_base}/model_manifest.json"
    verification_report = {}

    if Path(manifest_path).exists():
        from src.model_traceability import load_and_verify_models

        print("\n🔐 Verifying model checksums...")
        try:
            verified, verification_report = load_and_verify_models(
                manifest_path,
                archive_classif,
                archive_ner,
                strict=True  # Raise exception on mismatch
            )

            if verified:
                print("   ✅ All models verified - integrity confirmed")
            else:
                raise ValueError(
                    "Model checksum verification failed!\n"
                    "Models may be corrupted. Check verification report."
                )
        except FileNotFoundError:
            print("   ⚠️ No manifest found - skipping checksum verification")
            print("   ℹ️  Consider regenerating training archive with checksums")
            verification_report = {'error': 'manifest_not_found'}
        except Exception as e:
            print(f"   ❌ Verification error: {e}")
            raise
    else:
        print("   ⚠️ No manifest found - skipping checksum verification")
        print("   ℹ️  Models from older training run without traceability")
        verification_report = {'error': 'manifest_not_found'}

    # Copy models to working locations
    print("\n📋 Copying verified models to working directory...")
    shutil.copy2(archive_classif, target_classif)
    shutil.copy2(archive_ner, target_ner)

    model_source = f"training_session_{training_session_id}"

    # Display model information
    classif_size = Path(target_classif).stat().st_size / (1024*1024)
    ner_size = Path(target_ner).stat().st_size / (1024*1024)

    print(f"✅ Models copied to working directory:")
    print(f"   📁 {target_classif} ({classif_size:.0f}MB)")
    print(f"   📁 {target_ner} ({ner_size:.0f}MB)")
    print(f"   Model Source: {model_source}")
    print(f"   Training Session: {training_session_id}")
    print(f"   Checksum Verified: {'✅ Yes' if verification_report.get('all_verified') else '⚠️ Skipped'}")

    return model_source, training_session_id, verification_report


# ---------------------------------------------------------------------------
def check_local_results(results_path: str) -> Tuple[bool, int]:
    """
    Check if local results exist and are valid

    Args:
        results_path: Path to results CSV file

    Returns:
        Tuple of (exists: bool, count: int)
    """
    if Path(results_path).exists():
        try:
            df = pd.read_csv(results_path)
            if len(df) > 0:
                return True, len(df)
        except:
            pass
    return False, 0


# ---------------------------------------------------------------------------
# CHECKPOINT FUNCTIONS REMOVED (2025-10-28)
# Checkpoint functionality was deprecated after discovering data contamination issues
# See docs/PYTORCH_CHECKPOINT_FIX.md (Addendum) for details
# Pipeline runs fast enough (~10-15 minutes) that checkpointing adds unnecessary complexity
# ---------------------------------------------------------------------------


def run_prediction_script(
        script_name: str,
        inventory_dir: str,
        args_dict: Dict[str, Optional[str]]) -> Tuple[bool, float]:
    """
    Execute prediction script with proper paths

    Args:
        script_name: Script name without .py extension (e.g., 'class_predict')
        inventory_dir: Base inventory directory path
        args_dict: Dictionary of arguments {'-flag': 'value'} or {'positional': None}

    Returns:
        Tuple of (success: bool, duration: float in seconds)
    """
    import time

    # Build command
    cmd = ['python', f'"{inventory_dir}/src/{script_name}.py"']

    # Add arguments
    for key, value in args_dict.items():
        if value is None:
            # Positional argument
            cmd.append(key)
        else:
            # Flag argument
            cmd.extend([key, value])

    # Join command for shell execution
    cmd_str = ' '.join(cmd)

    print(f"🔧 Command: {cmd_str}")

    start_time = time.time()

    # Execute using shell (for notebook compatibility)
    result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)

    duration = time.time() - start_time

    if result.returncode != 0:
        print(f"❌ Script failed: {result.stderr}")
        return False, duration

    return True, duration


# ---------------------------------------------------------------------------
def show_rerun_progress(progress: Dict[str, str], rerun_session_id: str) -> None:
    """
    Display pipeline progress with session ID

    Args:
        progress: Dictionary of step names to status strings
        rerun_session_id: Rerun session identifier
    """
    print(f"\n📊 Pipeline Progress ({rerun_session_id}):")
    for step, status in progress.items():
        print(f"   {status} {step.replace('_', ' ').title()}")


# ---------------------------------------------------------------------------
def display_step_results(step_name: str, results_path: str) -> None:
    """
    Display step statistics

    Args:
        step_name: Name of the step
        results_path: Path to results file
    """
    if not Path(results_path).exists():
        print(f"⚠️ Results file not found: {results_path}")
        return

    try:
        # Get file size
        size_mb = Path(results_path).stat().st_size / (1024*1024)
        print(f"📄 {step_name}: {size_mb:.1f}MB")

        # Get row count for CSV
        if results_path.endswith('.csv'):
            df = pd.read_csv(results_path)
            print(f"   📊 {len(df):,} rows")
    except Exception as e:
        print(f"⚠️ Could not read results: {e}")


# ---------------------------------------------------------------------------
def create_rerun_archive(
        archive_dir: str,
        rerun_session_id: str,
        config: Dict[str, Any],
        results_dirs: Dict[str, str]) -> int:
    """
    Create comprehensive archive with all outputs and full traceability

    Args:
        archive_dir: Archive directory path
        rerun_session_id: Rerun session identifier
        config: Configuration dictionary
        results_dirs: Dictionary mapping step names to result directories

    Returns:
        int: Number of files archived
    """
    Path(archive_dir).mkdir(parents=True, exist_ok=True)

    archived_count = 0

    # Archive structure for simplified pipeline
    file_mappings = {
        'classification': [
            ('predictions.csv', 'classification_results.csv'),
            ('predicted_positives.csv', 'classification_positives.csv')
        ],
        'ner': [
            ('predictions.csv', 'ner_results.csv')
        ],
        'url_extraction': [
            ('predictions.csv', 'url_extraction_results.csv')
        ],
        'names': [
            ('predictions.csv', 'processed_names_results.csv')
        ],
        'final': [
            ('biodata_inventory_2022_rerun.csv', 'final_inventory.csv')
        ]
    }

    # Archive files
    for step_name, mappings in file_mappings.items():
        step_dir = results_dirs.get(step_name)
        if not step_dir:
            continue

        for src_name, dst_name in mappings:
            src_path = f"{step_dir}/{src_name}"
            dst_path = f"{archive_dir}/{dst_name}"

            if Path(src_path).exists():
                try:
                    shutil.copy2(src_path, dst_path)

                    # Display info
                    file_size = Path(dst_path).stat().st_size / 1024
                    if dst_path.endswith('.csv'):
                        df = pd.read_csv(dst_path)
                        entries = len(df)
                        print(f"   ✅ {Path(dst_path).name}: {entries:,} entries ({file_size:.1f} KB)")
                    else:
                        print(f"   ✅ {Path(dst_path).name}: ({file_size:.1f} KB)")

                    archived_count += 1
                except Exception as e:
                    print(f"   ⚠️ Could not archive {src_name}: {e}")
            else:
                print(f"   ⏭️ Skipped {src_name} (not found)")

    # Save enhanced configuration
    enhanced_config = config.copy()
    enhanced_config.update({
        'archive_created_at': datetime.now().isoformat(),
        'archive_location': archive_dir,
        'files_archived': archived_count
    })

    # Add model verification record
    if 'model_traceability' in config and 'verification_report' in config['model_traceability']:
        enhanced_config['model_verification'] = config['model_traceability']['verification_report']
        print(f"   ℹ️  Model verification report included in config")

    config_path = f"{archive_dir}/config_with_traceability.json"
    with open(config_path, 'w') as f:
        json.dump(enhanced_config, f, indent=2)
    print(f"   ✅ config_with_traceability.json: Complete configuration and traceability")

    # Create README
    create_rerun_readme(archive_dir, rerun_session_id, enhanced_config)
    print(f"   ✅ README.md: Comprehensive documentation with lineage")

    return archived_count


# ---------------------------------------------------------------------------
def create_rerun_readme(
        archive_dir: str,
        rerun_session_id: str,
        config: Dict[str, Any]) -> None:
    """
    Generate comprehensive README for the archive

    Args:
        archive_dir: Archive directory path
        rerun_session_id: Rerun session identifier
        config: Enhanced configuration dictionary
    """
    training_session = config.get('training_session_id', 'Unknown')
    model_source = config.get('model_traceability', {}).get('model_source', 'Unknown')

    # Calculate processing time
    created_time = datetime.fromisoformat(config['created'])
    archived_time = datetime.fromisoformat(config['archive_created_at'])
    processing_time = archived_time - created_time
    processing_mins = int(processing_time.total_seconds() / 60)
    processing_hours = processing_mins // 60
    processing_mins_remainder = processing_mins % 60

    readme_content = f"""# 2022 Inventory Rerun Results: {rerun_session_id}

**Created**: {archived_time.strftime('%Y-%m-%d %H:%M:%S')}
**Environment**: Google Colab with GPU acceleration
**Status**: ✅ COMPLETED SUCCESSFULLY
**Processing Time**: {processing_hours}h {processing_mins_remainder}m

---

## Traceability Chain

### Training Session → Rerun Session → Results
```
Training Models: {training_session}
    ↓ models used by ↓
2022 Rerun: {rerun_session_id}
    ↓ processes ↓
Input Dataset: {config['input_data']}
    ↓ produces ↓
Final Inventory: biodata resources
```

### Model Information
- **Training Session ID**: `{training_session}`
- **Model Source**: {model_source}
- **Models Used**: Classification + NER from training archive
- **Rerun Session**: `{rerun_session_id}`

---

## Processing Configuration

### Input Parameters
- **Input Dataset**: {config['input_data']}
- **Test Mode**: {config.get('test_mode', False)}
- **Max URLs per Paper**: {config['max_urls']}

### Pipeline Steps Executed
1. ✅ **Input Validation** - Verified 2022 dataset
2. ✅ **Classification** - Identified bio-resource papers
3. ✅ **Named Entity Recognition** - Extracted database names
4. ✅ **URL Extraction** - Found resource URLs
5. ✅ **Name Processing** - Generated final inventory

---

## Files in Archive

### Core Results
- **`final_inventory.csv`** - Complete biodata resource inventory
- **`classification_results.csv`** - All classification predictions
- **`classification_positives.csv`** - Bio-resource papers only
- **`ner_results.csv`** - Named entity recognition results
- **`url_extraction_results.csv`** - URL extraction results
- **`processed_names_results.csv`** - Processed database names

### Configuration & Traceability
- **`config_with_traceability.json`** - Complete configuration with model lineage
- **`README.md`** - This documentation file

---

## Usage Instructions

### Loading Results
```python
import pandas as pd

# Load final inventory
inventory = pd.read_csv('{archive_dir}/final_inventory.csv')

# Load intermediate results
classifications = pd.read_csv('{archive_dir}/classification_results.csv')
ner_results = pd.read_csv('{archive_dir}/ner_results.csv')
```

---

**Archive Created**: {archived_time.strftime('%Y-%m-%d %H:%M:%S')}
**Pipeline**: rerun_2022_inventory_simplified.ipynb
**Data Integrity**: Fresh run without checkpoints (eliminates contamination risk)
**Archive Location**: {archive_dir}
"""

    readme_path = f"{archive_dir}/README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)


# ---------------------------------------------------------------------------
def validate_input_data(
        input_path: str,
        expected_columns: List[str]) -> Tuple[bool, int, List[str]]:
    """
    Validate input CSV file

    Args:
        input_path: Path to input CSV
        expected_columns: List of required column names

    Returns:
        Tuple of (valid: bool, row_count: int, columns: list)

    Raises:
        FileNotFoundError: If input file not found
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input data not found: {input_path}")

    # Try multiple encodings
    encodings = ['utf-8', 'latin-1', 'cp1252']
    df = None

    for encoding in encodings:
        try:
            df = pd.read_csv(input_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError(f"Could not read input file with any encoding: {input_path}")

    # Check for required columns
    missing_cols = [col for col in expected_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    return True, len(df), list(df.columns)


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit('This file is a module, and is not meant to be run.')
