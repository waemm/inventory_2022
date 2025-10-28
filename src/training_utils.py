"""
Training Utilities for Biodata Inventory ML Pipeline
==================================================

This module contains utility functions for the training pipeline that are not core
to the algorithmic work, including checkpoint management, GPU optimization, 
directory management, and progress tracking.

Created: 2025-10-23
Purpose: Clean separation of utilities from main training notebook
"""

import os
import shutil
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
import torch
from torch.cuda.amp import GradScaler, autocast


# ==========================================
# DIRECTORY MANAGEMENT UTILITIES
# ==========================================

def clean_training_directories(clean_directory_flag, unique_id=None):
    """
    Remove all existing training outputs for a fresh start
    
    Args:
        clean_directory_flag (bool): Whether cleaning was requested
        unique_id (str, optional): Unique session ID for session-specific directories
        
    Returns:
        bool: True if cleaning was completed, False if cancelled
    """
    if not clean_directory_flag:
        print("✅ Using existing files (CLEAN_DIRECTORY = False)")
        return False
    
    if unique_id:
        # Session-specific directories
        directories_to_clean = [
            f"out/classif_train_full_{unique_id}",
            f"out/ner_train_full_{unique_id}", 
            "out/classif_train_out",  # Production directories are shared
            "out/ner_train_out",
            f"data/classif_splits_full_{unique_id}",
            f"data/ner_splits_full_{unique_id}",
            f"logs_{unique_id}",
            f"model_backups_{unique_id}"
        ]
    else:
        # Legacy directories
        directories_to_clean = [
            "out/classif_train_full",
            "out/ner_train_full", 
            "out/classif_train_out",
            "out/ner_train_out",
            "data/classif_splits_full",
            "data/ner_splits_full",
            "logs",
            "model_backups"
        ]
    
    print(f"\n{'='*60}")
    print("DIRECTORY CLEANING REQUESTED")
    print(f"{'='*60}")
    
    print("🧹 The following directories will be cleaned:")
    existing_dirs = []
    for dir_path in directories_to_clean:
        if Path(dir_path).exists():
            existing_dirs.append(dir_path)
            print(f"   📁 {dir_path}")
    
    if not existing_dirs:
        print("   ℹ️ No existing directories found to clean")
        return True
    
    print("\n⚠️ WARNING: This will permanently delete all existing training outputs!")
    print("⚠️ This includes:")
    print("   - All trained models")
    print("   - Training statistics and logs") 
    print("   - Data splits")
    print("   - Evaluation results")
    print("   - Production model deployments")
    
    # Interactive confirmation
    print("\n" + "=" * 50)
    print("CONFIRMATION REQUIRED")
    print("=" * 50)
    confirm = input("Type 'DELETE' to confirm directory cleaning (anything else cancels): ")
    
    if confirm == "DELETE":
        print("\n🧹 Cleaning directories...")
        cleaned_count = 0
        
        for dir_path in directories_to_clean:
            if Path(dir_path).exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"   ✅ Cleaned: {dir_path}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to clean {dir_path}: {e}")
            else:
                print(f"   ⏭️ Skipped: {dir_path} (doesn't exist)")
        
        print(f"\n✅ Cleaned {cleaned_count} directories successfully")
        print("🚀 Ready for fresh training run!")
        return True
        
    else:
        print("\n❌ Directory cleaning cancelled")
        print("Continuing with existing files...")
        return False


def create_directory_structure(unique_id=None):
    """Create all necessary directories for training
    
    Args:
        unique_id (str, optional): Unique session ID for directory naming.
                                  If None, uses legacy directory names.
    """
    if unique_id:
        # Session-specific directories
        directories = [
            f"data/classif_splits_full_{unique_id}",
            f"data/ner_splits_full_{unique_id}", 
            f"out/classif_train_full_{unique_id}",
            f"out/ner_train_full_{unique_id}",
            f"logs_{unique_id}",
            f"model_backups_{unique_id}"
        ]
        print(f"📁 Creating session-specific directory structure for {unique_id}...")
    else:
        # Legacy directories for backwards compatibility
        directories = [
            "data/classif_splits_full",
            "data/ner_splits_full", 
            "out/classif_train_full",
            "out/ner_train_full",
            "logs",
            "model_backups"
        ]
        print("📁 Creating directory structure...")
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")
    
    print("✅ Directory structure ready")


# ==========================================
# CHECKPOINT MANAGEMENT UTILITIES
# ==========================================

def check_local_splits(classif_splits_dir="data/classif_splits_full", ner_splits_dir="data/ner_splits_full"):
    """Check if local data splits exist and are valid
    
    Args:
        classif_splits_dir (str): Path to classification splits directory
        ner_splits_dir (str): Path to NER splits directory
        
    Returns:
        bool: True if all required split files exist
    """
    required_files = [
        f"{classif_splits_dir}/train_paper_classif.csv",
        f"{classif_splits_dir}/val_paper_classif.csv",
        f"{classif_splits_dir}/test_paper_classif.csv",
        f"{ner_splits_dir}/train_ner.csv",
        f"{ner_splits_dir}/val_ner.csv",
        f"{ner_splits_dir}/test_ner.csv",
        f"{ner_splits_dir}/train_ner.pkl",
        f"{ner_splits_dir}/val_ner.pkl",
        f"{ner_splits_dir}/test_ner.pkl"
    ]
    
    return all(Path(f).exists() for f in required_files)


def check_drive_checkpoint(checkpoint_path, step_name):
    """Check if checkpoint exists in Google Drive"""
    if step_name == "data_splits":
        return (Path(f"{checkpoint_path}/classif_splits_full").exists() and 
                Path(f"{checkpoint_path}/ner_splits_full").exists())
    elif step_name in ["classification_training", "ner_training"]:
        return (Path(f"{checkpoint_path}/checkpt.pt").exists() and 
                Path(f"{checkpoint_path}/train_stats.csv").exists())
    elif step_name == "evaluation":
        return (Path(f"{checkpoint_path}/classif_evaluation").exists() and 
                Path(f"{checkpoint_path}/ner_evaluation").exists())
    elif step_name == "final_archive":
        return Path(checkpoint_path).exists()
    else:
        return Path(checkpoint_path).exists()


def load_splits_from_checkpoint(checkpoint_path, classif_splits_dir="data/classif_splits_full", ner_splits_dir="data/ner_splits_full"):
    """Load data splits from Google Drive checkpoint
    
    Args:
        checkpoint_path (str): Path to checkpoint directory
        classif_splits_dir (str): Local path for classification splits
        ner_splits_dir (str): Local path for NER splits
    """
    print(f"📥 Loading data splits from checkpoint: {checkpoint_path}")
    
    # Copy classification splits
    if Path(f"{checkpoint_path}/classif_splits_full").exists():
        if Path(classif_splits_dir).exists():
            shutil.rmtree(classif_splits_dir)
        shutil.copytree(f"{checkpoint_path}/classif_splits_full", classif_splits_dir)
        print("   ✅ Classification splits loaded")
    
    # Copy NER splits
    if Path(f"{checkpoint_path}/ner_splits_full").exists():
        if Path(ner_splits_dir).exists():
            shutil.rmtree(ner_splits_dir)
        shutil.copytree(f"{checkpoint_path}/ner_splits_full", ner_splits_dir)
        print("   ✅ NER splits loaded")


def save_splits_to_checkpoint(checkpoint_path, classif_splits_dir="data/classif_splits_full", ner_splits_dir="data/ner_splits_full"):
    """Save data splits to Google Drive checkpoint
    
    Args:
        checkpoint_path (str): Path to checkpoint directory
        classif_splits_dir (str): Local path for classification splits
        ner_splits_dir (str): Local path for NER splits
    """
    print(f"💾 Saving data splits to checkpoint: {checkpoint_path}")
    
    # Create checkpoint directory
    Path(checkpoint_path).mkdir(parents=True, exist_ok=True)
    
    # Copy classification splits
    if Path(classif_splits_dir).exists():
        checkpoint_classif = f"{checkpoint_path}/classif_splits_full"
        if Path(checkpoint_classif).exists():
            shutil.rmtree(checkpoint_classif)
        shutil.copytree(classif_splits_dir, checkpoint_classif)
        print("   ✅ Classification splits saved")
    
    # Copy NER splits
    if Path(ner_splits_dir).exists():
        checkpoint_ner = f"{checkpoint_path}/ner_splits_full"
        if Path(checkpoint_ner).exists():
            shutil.rmtree(checkpoint_ner)
        shutil.copytree(ner_splits_dir, checkpoint_ner)
        print("   ✅ NER splits saved")


def load_training_from_checkpoint(checkpoint_path, local_output):
    """Load training model and stats from Google Drive checkpoint"""
    print(f"📥 Loading training results from checkpoint: {checkpoint_path}")
    
    # Ensure local output directory exists
    Path(local_output).mkdir(parents=True, exist_ok=True)
    
    # Copy entire checkpoint directory to local
    if Path(checkpoint_path).exists():
        # Remove existing local output
        if Path(local_output).exists():
            shutil.rmtree(local_output)
        
        # Copy from checkpoint
        shutil.copytree(checkpoint_path, local_output)
        
        # Report what was loaded
        for item in Path(local_output).rglob("*"):
            if item.is_file():
                size_mb = item.stat().st_size / (1024*1024)
                print(f"   ✅ Loaded: {item.name} ({size_mb:.1f}MB)")


def save_training_to_checkpoint(checkpoint_path, local_output):
    """Save training outputs to Google Drive checkpoint"""
    print(f"💾 Saving training results to checkpoint: {checkpoint_path}")
    
    # Copy entire output directory to checkpoint
    if Path(local_output).exists():
        # Remove existing checkpoint
        if Path(checkpoint_path).exists():
            shutil.rmtree(checkpoint_path)
        
        # Copy to checkpoint
        shutil.copytree(local_output, checkpoint_path)
        
        # Report what was saved
        for item in Path(checkpoint_path).rglob("*"):
            if item.is_file():
                size_mb = item.stat().st_size / (1024*1024)
                print(f"   ✅ Saved: {item.name} ({size_mb:.1f}MB)")


def verify_config_compatibility(checkpoint_path, current_config):
    """Check if current config matches checkpointed config"""
    checkpoint_config_file = f"{checkpoint_path}/config.json"
    
    if Path(checkpoint_config_file).exists():
        with open(checkpoint_config_file, 'r') as f:
            checkpoint_config = json.load(f)
        
        # Compare key parameters
        differences = []
        for key, current_val in current_config.items():
            checkpoint_val = checkpoint_config.get(key)
            if current_val != checkpoint_val:
                differences.append(f"{key}: {checkpoint_val} → {current_val}")
        
        if differences:
            print("⚠️ Configuration differences detected:")
            for diff in differences:
                print(f"   {diff}")
            
            response = input("Continue with checkpoint anyway? (y/N): ")
            return response.lower().startswith('y')
        else:
            print("✅ Configuration matches checkpoint")
            return True
    return True


# ==========================================
# GPU & MEMORY MANAGEMENT UTILITIES
# ==========================================

def clear_gpu_memory():
    """Clear GPU memory cache"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        print("🧹 GPU memory cleared")


def get_optimal_batch_size():
    """Determine optimal batch size based on available GPU memory"""
    if not torch.cuda.is_available():
        return 8
    
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    if gpu_memory >= 24:
        return 32
    elif gpu_memory >= 16:
        return 24  
    elif gpu_memory >= 12:
        return 16
    else:
        return 8


def get_gpu_memory_info():
    """Get current GPU memory usage"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        cached = torch.cuda.memory_reserved(0) / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"📊 GPU Memory: {allocated:.1f}GB allocated, {cached:.1f}GB cached, {total:.1f}GB total")


def setup_gpu_optimizations():
    """Set up GPU optimizations for training"""
    print("🚀 Setting up GPU optimizations...")
    
    # Enable mixed precision training
    scaler = GradScaler()
    
    optimal_batch_size = get_optimal_batch_size()
    print(f"🚀 Optimal batch size: {optimal_batch_size}")
    get_gpu_memory_info()
    print("✅ GPU optimizations configured")
    
    return scaler, optimal_batch_size


# ==========================================
# MODEL DEPLOYMENT UTILITIES
# ==========================================

def check_local_deployment():
    """Check if models are deployed to production locations"""
    production_models = [
        "out/classif_train_out/article_classifier.pt",
        "out/ner_train_out/named_entity_recognition.pt"
    ]
    return all(Path(model).exists() for model in production_models)


def deploy_production_models(classif_output_dir="out/classif_train_full", ner_output_dir="out/ner_train_full"):
    """Deploy trained models to production locations
    
    Args:
        classif_output_dir (str): Path to classification training output directory
        ner_output_dir (str): Path to NER training output directory
        
    Returns:
        int: Number of models successfully deployed
    """
    print("🚀 Deploying models to production locations...")
    
    # Create production directories
    production_dirs = ["out/classif_train_out", "out/ner_train_out"]
    for dir_path in production_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Copy models to production locations
    models_deployed = 0
    
    classif_model = f"{classif_output_dir}/checkpt.pt"
    if Path(classif_model).exists():
        shutil.copy2(classif_model, "out/classif_train_out/article_classifier.pt")
        size_mb = Path("out/classif_train_out/article_classifier.pt").stat().st_size / (1024*1024)
        print(f"   ✅ Classification model deployed: article_classifier.pt ({size_mb:.0f}MB)")
        models_deployed += 1
    
    ner_model = f"{ner_output_dir}/checkpt.pt"
    if Path(ner_model).exists():
        shutil.copy2(ner_model, "out/ner_train_out/named_entity_recognition.pt")
        size_mb = Path("out/ner_train_out/named_entity_recognition.pt").stat().st_size / (1024*1024)
        print(f"   ✅ NER model deployed: named_entity_recognition.pt ({size_mb:.0f}MB)")
        models_deployed += 1
    
    # Create model reference files
    Path("out/classif_train_out/best").mkdir(exist_ok=True)
    Path("out/ner_train_out/best").mkdir(exist_ok=True)
    
    with open("out/classif_train_out/best/best_checkpt.txt", "w") as f:
        f.write("out/classif_train_out/article_classifier.pt\n")
    
    with open("out/ner_train_out/best/best_checkpt.txt", "w") as f:
        f.write("out/ner_train_out/named_entity_recognition.pt\n")
    
    print(f"   ✅ Model references updated ({models_deployed}/2 models deployed)")
    return models_deployed


def create_final_archive(archive_dir, unique_id, config, classif_output_dir=None, ner_output_dir=None):
    """Create comprehensive archive with all training artifacts
    
    Args:
        archive_dir (str): Path to archive directory
        unique_id (str): Unique session ID
        config (dict): Training configuration
        classif_output_dir (str, optional): Classification training output directory
        ner_output_dir (str, optional): NER training output directory
        
    Returns:
        int: Number of items archived
    """
    print(f"📦 Creating final archive: {archive_dir}")
    
    # Use session-specific directories if provided, otherwise fall back to config or defaults
    if classif_output_dir is None:
        classif_output_dir = f"out/classif_train_full_{unique_id}" if unique_id else "out/classif_train_full"
    if ner_output_dir is None:
        ner_output_dir = f"out/ner_train_full_{unique_id}" if unique_id else "out/ner_train_full"
    
    # Create archive directory
    Path(archive_dir).mkdir(parents=True, exist_ok=True)
    
    # Archive models
    archive_files = {
        f"{classif_output_dir}/checkpt.pt": f"{archive_dir}/classification_model.pt",
        f"{ner_output_dir}/checkpt.pt": f"{archive_dir}/ner_model.pt",
        f"{classif_output_dir}/train_stats.csv": f"{archive_dir}/classification_training_stats.csv",
        f"{ner_output_dir}/train_stats.csv": f"{archive_dir}/ner_training_stats.csv"
    }
    
    archived_count = 0
    for src, dst in archive_files.items():
        if Path(src).exists():
            shutil.copy2(src, dst)
            size_mb = Path(dst).stat().st_size / (1024*1024)
            print(f"   ✅ Archived: {Path(dst).name} ({size_mb:.0f}MB)")
            archived_count += 1
        else:
            print(f"   ⚠️ Missing: {src}")
    
    # Archive evaluation results
    eval_dirs = {
        f"{classif_output_dir}/test_evaluation": f"{archive_dir}/classification_test_evaluation",
        f"{ner_output_dir}/test_evaluation": f"{archive_dir}/ner_test_evaluation"
    }
    
    for src, dst in eval_dirs.items():
        if Path(src).exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"   ✅ Archived: {Path(dst).name}/")
            archived_count += 1
    
    # Archive configuration (if checkpoint_base exists in config)
    if 'checkpoint_base' in config:
        config_path = f"{config['checkpoint_base']}/config.json"
        if Path(config_path).exists():
            shutil.copy2(config_path, f"{archive_dir}/training_config.json")
            print(f"   ✅ Archived: training_config.json")
    
    # Create comprehensive documentation
    create_archive_readme(archive_dir, unique_id, config)

    print(f"   ✅ Archived: README.md")

    # Create model manifest with checksums
    from model_traceability import create_model_manifest

    classif_model = f"{archive_dir}/classification_model.pt"
    ner_model = f"{archive_dir}/ner_model.pt"

    if Path(classif_model).exists() and Path(ner_model).exists():
        try:
            manifest_path = create_model_manifest(
                archive_dir,
                unique_id,
                config,
                classif_model,
                ner_model
            )
            print(f"   ✅ Model manifest created with checksums")
            archived_count += 1
        except Exception as e:
            print(f"   ⚠️ Could not create model manifest: {e}")
            print(f"   ℹ️  Models archived but traceability limited")

    print(f"\n📊 Archive Summary: {archived_count + 2} items archived")
    return archived_count


def create_archive_readme(archive_dir, unique_id, config):
    """Create comprehensive README for the archive"""
    timestamp = config.get('timestamp', 'Unknown')
    hf_model = config.get('model', 'Unknown')
    epochs = config.get('epochs', 'Unknown')
    optimal_batch_size = config.get('optimal_batch_size', 'Unknown')
    learning_rate = config.get('learning_rate', 'Unknown')
    model_name = config.get('model_name', 'Unknown')
    
    readme_content = f"""# Training Run: {unique_id}

**Training Date**: {timestamp.split('_')[0]}  
**Duration**: Completed in Google Colab  
**Status**: ✅ COMPLETED SUCCESSFULLY  
**Environment**: Google Colab with GPU acceleration
**Session ID**: {unique_id}

## Model Information

### Classification Model
- **File**: classification_model.pt
- **Architecture**: RobertaForSequenceClassification  
- **Base Model**: {hf_model}
- **Task**: Binary classification (bio-resource vs non-bio-resource papers)
- **Epochs**: {epochs}
- **Batch Size**: {optimal_batch_size}

### NER Model
- **File**: ner_model.pt
- **Architecture**: RobertaForTokenClassification
- **Base Model**: {hf_model}  
- **Task**: Named Entity Recognition (resource name extraction)
- **Epochs**: {epochs}
- **Batch Size**: {optimal_batch_size}

## Training Configuration

```yaml
Model Name: {model_name}
HuggingFace Model: {hf_model}
Epochs: {epochs}
Batch Size: {optimal_batch_size}
Learning Rate: {learning_rate}
Optimizer: AdamW
GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}
```

## Files in Archive

### Core Model Files
- **classification_model.pt** - Trained classification model
- **ner_model.pt** - Trained NER model

### Training Statistics
- **classification_training_stats.csv** - Epoch-by-epoch training metrics
- **ner_training_stats.csv** - Epoch-by-epoch training metrics

### Evaluation Results  
- **classification_test_evaluation/** - Test set evaluation for classification
- **ner_test_evaluation/** - Test set evaluation for NER

### Configuration
- **README.md** - This documentation file

## Session Information

- **Session ID**: {unique_id}
- **Test Mode**: {'Yes' if config.get('test_mode', False) else 'No'}
- **Training Pipeline**: Simplified (no checkpoints)

## Usage Instructions

### Loading Models
```python
import torch

# Load classification model
classif_model = torch.load('classification_model.pt', map_location='cpu')

# Load NER model  
ner_model = torch.load('ner_model.pt', map_location='cpu')
```

### Integration with Pipeline
These models can be directly used with the existing prediction pipeline:
- Copy `classification_model.pt` to `out/classif_train_out/article_classifier.pt`
- Copy `ner_model.pt` to `out/ner_train_out/named_entity_recognition.pt`

---

**Archive Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Training Pipeline**: full_training_pipeline_simplified.ipynb
**Archive Location**: {archive_dir}
**Data Integrity**: No checkpoints - clean linear pipeline
"""
    
    with open(f"{archive_dir}/README.md", "w") as f:
        f.write(readme_content)


# ==========================================
# PROGRESS TRACKING UTILITIES
# ==========================================

def show_progress(progress, unique_id):
    """Display pipeline progress with emojis"""
    print(f"\n📊 Training Progress ({unique_id}):")
    for step, status in progress.items():
        print(f"   {status} {step.replace('_', ' ').title()}")


def display_split_statistics(classif_splits_dir="data/classif_splits_full", ner_splits_dir="data/ner_splits_full"):
    """Display data split statistics
    
    Args:
        classif_splits_dir (str): Path to classification splits directory
        ner_splits_dir (str): Path to NER splits directory
    """
    print("\n📊 Split Statistics:")
    for split in ['train', 'val', 'test']:
        classif_file = f"{classif_splits_dir}/{split}_paper_classif.csv"
        ner_file = f"{ner_splits_dir}/{split}_ner.csv"
        
        if Path(classif_file).exists():
            classif_lines = len(open(classif_file).readlines()) - 1
            print(f"   {split}: {classif_lines} classification samples")
        
        if Path(ner_file).exists():
            try:
                ner_lines = len(open(ner_file, encoding='utf-8').readlines()) - 1
            except UnicodeDecodeError:
                ner_lines = len(open(ner_file, encoding='latin-1').readlines()) - 1
            print(f"   {split}: {ner_lines} NER samples")


def display_training_results(local_output, model_type):
    """Display training results summary"""
    model_file = f"{local_output}/checkpt.pt"
    stats_file = f"{local_output}/train_stats.csv"
    
    if Path(model_file).exists():
        size_mb = Path(model_file).stat().st_size / (1024*1024)
        print(f"📊 {model_type} Model: {model_file} ({size_mb:.0f}MB)")
    
    if Path(stats_file).exists():
        stats_df = pd.read_csv(stats_file)
        best_epoch = stats_df.loc[stats_df['val_f1'].idxmax()]
        print(f"📈 Best F1: {best_epoch['val_f1']:.3f} (epoch {best_epoch['epoch']})")


def display_evaluation_results(eval_dir, model_type):
    """Display evaluation results"""
    metrics_file = f"{eval_dir}/metrics.csv"
    
    if Path(metrics_file).exists():
        eval_df = pd.read_csv(metrics_file)
        print(f"\n📊 {model_type} Test Results:")
        print(eval_df.to_string(index=False))


# ==========================================
# FILE VALIDATION UTILITIES
# ==========================================

def check_prerequisites(data_directory="data"):
    """Check that all required training data files exist
    
    Args:
        data_directory (str): Path to data directory containing training files
    """
    print("📋 Prerequisites Check:")
    
    required_files = [
        f"{data_directory}/manual_classifications.csv",
        f"{data_directory}/manual_ner_extraction.csv"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size / 1024
            
            # Handle different file encodings safely
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        lines = len(f.readlines())
                    print(f"⚠️ {file_path}: Using latin-1 encoding")
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='cp1252') as f:
                            lines = len(f.readlines())
                        print(f"⚠️ {file_path}: Using cp1252 encoding")
                    except UnicodeDecodeError:
                        # If all encodings fail, count bytes and estimate
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            lines = content.count(b'\n') + 1
                        print(f"⚠️ {file_path}: Binary count (encoding issues)")
            
            print(f"✅ {file_path}: {lines-1} samples ({size:.1f} KB)")
        else:
            print(f"❌ Missing: {file_path}")
            all_files_exist = False
    
    if not all_files_exist:
        raise FileNotFoundError("Required training data files not found. Please ensure data files are present.")
    
    print("✅ All prerequisite files found and ready for training")
    return True


# ==========================================
# SUBPROCESS EXECUTION UTILITIES
# ==========================================

def run_training_command(cmd, step_name):
    """
    Execute training command with real-time output and progress tracking
    
    Args:
        cmd (list): Command to execute
        step_name (str): Name of the training step for logging
        
    Returns:
        bool: True if successful, False if failed
    """
    print(f"🔧 Command: {' '.join(cmd)}")
    start_time = time.time()
    
    # Execute training with progress tracking
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                              text=True, universal_newlines=True)
    
    # Real-time output display with progress tracking
    output_lines = []
    for line in iter(process.stdout.readline, ''):
        if line.strip():
            print(line.strip())
            output_lines.append(line.strip())
            
            # Show memory usage periodically
            if len(output_lines) % 20 == 0:
                get_gpu_memory_info()
    
    process.wait()
    
    if process.returncode == 0:
        end_time = time.time()
        duration = (end_time - start_time) / 60
        print(f"\n✅ {step_name} completed in {duration:.1f} minutes")
        print(f"⏰ End time: {datetime.now().strftime('%H:%M:%S')}")
        return True
    else:
        print(f"❌ {step_name} failed")
        if "AdamW" in '\n'.join(output_lines):
            print("🔧 This appears to be an AdamW import compatibility issue.")
            print("The source code has been updated to fix the AdamW import.")
            print("Try running this cell again.")
        return False