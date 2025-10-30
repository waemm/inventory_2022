# Biodata Inventory ML Pipeline - AI Agent Reference Guide

**Created**: 2025-10-22
**Last Updated**: 2025-10-30 (Multi-model comparison completed - critical NER performance gap identified)
**Status**: ✅ **PRODUCTION READY (Local & Colab)** + ⚠️ **EXPERIMENTAL TRAINING BLOCKED (NER baseline gap)**
**Purpose**: Living document for AI agents working on the biodata inventory ML pipeline

---

## 🎯 **Executive Summary**

This is a **sophisticated ML pipeline** that uses biomedical BERT models to automatically identify and extract biodata resources from scientific literature. The system processes EuropePMC query results through classification and Named Entity Recognition (NER) to generate comprehensive inventories of global biodata resources.

### **Current Status**
- ✅ **Production Ready**: V2 models (converted October 27, 2025) validated for use
- ✅ **Modern Environment**: Python 3.11.9, PyTorch 2.2.2, Transformers 4.35.0
- ✅ **High Performance**: Classification F1=0.898, NER F1=0.749
- ✅ **Complete Infrastructure**: Training, prediction, monitoring, and archival systems
- ✅ **Session Isolation**: Unique directories eliminate conflicts between training runs
- ✅ **Enhanced Traceability**: Full lineage from training sessions to inventory results
- ⚠️ **Training Parameters**: Validated hyperparameters required for new model training

### **Key Architecture**
- **Two-Model System**: Classification (bio-resource detection) + NER (database name extraction)
- **Base Model**: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500` (biomedical RoBERTa)
- **Pipeline**: EuropePMC → Classification → NER → URL Extraction → Processing → Final Inventory
- **Data**: 1,635 classification samples + 554 NER samples (manually curated)

### **Critical Execution Order (Google Colab)**
1. **Mount Google Drive** - MUST be first cell for checkpoint access
2. **Configure Session** - Auto-generates unique session ID for isolation
3. **Environment Setup** - Dependencies and utility imports via full paths
4. **Training Pipeline** - 6-step process with session-specific directories
5. **Model Deployment** - Copy to standard production locations for compatibility
6. **Archive Creation** - Complete session artifacts preservation with traceability

### **🎉 PyTorch Checkpoint Compatibility (RESOLVED 2025-10-27)**

**Problem**: Models trained in PyTorch 2.0.0 produced different predictions in PyTorch 2.8.0 (Colab), causing 99% prediction loss.

**Root Cause**: Checkpoint files contained NamedTuple objects that PyTorch 2.8 deserializes incorrectly, corrupting model weights.

**Solution**:
- ✅ Converted checkpoints to dict-only format (no custom objects)
- ✅ Updated loading code to use `weights_only=True` with backward compatibility
- ✅ Modified Colab notebook to prevent model overwriting
- ✅ Verified predictions match local results (99.97% agreement)

**Impact**: Saved ~9.5 hours of retraining time, models now work across PyTorch versions

**For Details**: See [`docs/PYTORCH_CHECKPOINT_FIX.md`](PYTORCH_CHECKPOINT_FIX.md) for comprehensive documentation

### **⚠️ CRITICAL: Multi-Model Comparison Results (2025-10-30)**

**Session**: 2025-10-30-p9rat5 (4 experiments, 64 minutes total)

**Problem**: All 4 biomedical BERT models underperform V2 baseline by 10-16% on NER task despite using validated optimal hyperparameters and fixed production data splits.

**Results Summary**:
- **Classification**: PubMedBERT best (F1=0.917) - EXCEEDS V2 baseline by +2.1% ✅
- **NER**: Original model best (F1=0.670) - BELOW V2 baseline by -10.5% ❌
- **Phase 1 Target** (NER F1 ≥ 0.80): NOT ACHIEVED

**Critical Finding**: All tested models show significant NER performance degradation:
- Original (allenai/dsp_roberta): F1=0.670 vs V2 0.749 (-10.5%)
- BioLinkBERT (2022 SOTA): F1=0.656 (-12.4%)
- PubMedBERT: F1=0.635 (-15.2%)
- SciBERT: F1=0.630 (-15.9%)

**Root Cause Hypotheses**:
1. **V2 Training Configuration Unknown**: Actual V2 hyperparameters may differ from assumptions
2. **Learning Rate Mismatch**: Experimental LRs (classif=1e-5, ner=5e-5) may not be optimal for production splits
3. **Early Stopping Too Aggressive**: Patience=5 may stop training before convergence
4. **Training Duration Insufficient**: V2 may have trained longer than 15 epochs
5. **Unknown V2 Optimizations**: V2 may use additional techniques (weight decay, dropout adjustments, etc.)

**Immediate Action Required**:
- 🔍 **CRITICAL**: Find actual V2 training configuration (check October 21 training archives)
- 📊 Review training curves to understand convergence patterns
- 🧪 Run test set validation to verify metrics
- 🔄 Consider additional learning rate sweep with production splits

**Impact**: Phase 1 blocked until V2 baseline performance can be matched. Cannot proceed to Phase 2 (data augmentation) without first matching baseline.

**For Details**: See [`docs/MULTI_MODEL_RESULTS_2025-10-30.md`](MULTI_MODEL_RESULTS_2025-10-30.md) for complete analysis

---

### **⚠️ Model Training Quality Investigation (2025-10-29)**

**Problem**: Fresh model training (October 28, 2025) produced models with 99.4% fewer high-confidence predictions than validated models.

**Root Cause**: Poor NER model training quality - achieved only F1=0.653 vs expected F1=0.749 (12.8% drop) due to training instability.

**Solution**:
- ✅ Identified training issues: learning rate too high, insufficient regularization, overfitting
- ✅ V2 models validated for production use (good training + PyTorch 2.8 compatible)
- ✅ Established training quality validation checklist
- ✅ **Experimental infrastructure built** for systematic hyperparameter optimization
- ✅ **Comprehensive research completed** on modern ML techniques and improvements
- ✅ **Google Drive automation scripts** for seamless upload/download with audit logging
- ✅ **Rclone integration** for direct Drive access from AI agents
- ✅ **First full experimental run completed** (2025-10-29) - 4 experiments, infrastructure validated
- ✅ **Multi-model comparison completed** (2025-10-30) - 4 models tested, critical performance gap identified

**Impact**: Production unblocked with V2 models, clear path forward for model improvement established, automated workflow for Colab experimentation fully operational, **but critical V2 baseline gap discovered requiring investigation**

**For Details**: See [`docs/FINAL_DIAGNOSIS_SUMMARY.md`](FINAL_DIAGNOSIS_SUMMARY.md), [`docs/MODEL_DEGRADATION_ROOT_CAUSE_ANALYSIS.md`](MODEL_DEGRADATION_ROOT_CAUSE_ANALYSIS.md), [`docs/EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md`](EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md), [`docs/EXPERIMENTAL_SESSION_ANALYSIS_2025-10-29.md`](EXPERIMENTAL_SESSION_ANALYSIS_2025-10-29.md), and [`docs/MULTI_MODEL_RESULTS_2025-10-30.md`](MULTI_MODEL_RESULTS_2025-10-30.md)

---

## 🚀 **Quick Start**

### **Environment Activation**
```bash
cd GBC/inventory_2022/  # This is the git repository root
source biodata_modern_env/bin/activate
export PYTHONPATH="src:$PYTHONPATH"
```

### **Run Full Training Pipeline** (Google Colab - Recommended)
```python
# Use the Google Colab notebook for cloud-based training
# full_training_pipeline_simplified.ipynb
# - Simple TEST_MODE toggle (True for 5-8 min test, False for 9.5 hr production)
# - Unique session directories (no conflicts)
# - Complete session isolation and traceability
# - No checkpoints (see PYTORCH_CHECKPOINT_FIX.md)
```

### **Run Full Training Pipeline** (Local - 9.5 hours)
```bash
./run_full_training.sh
```

### **Run Prediction Pipeline**
```bash
# Test mode (small dataset)
./test_rerun_2022_inventory.sh

# Full 2022 rerun (21,677 papers)
./rerun_2022_inventory.sh
```

### **Run Inventory Update Pipeline** (Google Colab)
```python
# Use the Google Colab notebook for cloud-based processing
# inventory_update_pipeline_with_checkpoints.ipynb
# - Configure TRAINING_SESSION_ID for model traceability
# - Choose from 7 workflow options
# - Full checkpoint system with Google Drive backup
```

### **Run 2022 Inventory Rerun** (Google Colab)
```python
# Use the Google Colab notebook for streamlined 2022 dataset processing
# rerun_2022_inventory_simplified.ipynb
# - Configure TRAINING_SESSION_ID for model traceability
# - Streamlined 5-step pipeline optimized for 21,677 papers
# - TEST_MODE toggle for quick testing vs production runs
# - No checkpoints (eliminates data contamination risk)
```

---

## 🏗️ **System Architecture Overview**

### **Pipeline Flow**
```
EuropePMC Query → Papers (CSV)
      ↓
Classification Model → Bio-resource vs General Papers
      ↓
NER Model → Extract Database Names (COM/FUL entities)
      ↓
URL Extraction → Extract Resource URLs (regex)
      ↓
Name Processing → Best name selection with confidence
      ↓
Final Inventory → Structured biodata resource catalog
```

### **Model Architecture**
- **Classification**: Binary classification (bio-resource vs general scientific papers)
- **NER**: Token classification using BIO tagging (O, B-COM, I-COM, B-FUL, I-FUL)
- **Entities**: COM (compound/abbreviation names), FUL (full descriptive names)
- **Training**: 70/15/15 splits, 10 epochs, AdamW optimizer

---

## 📊 **Current Production Status**

### **Production Models (V2 - Recommended for All Use)**

**✅ USE THESE MODELS**:
```
Classification Model: out/classif_train_out/article_classifier_v2.pt
- Size: 476MB
- MD5: ea57a1cab905c6d5c4e064204f3e160d
- Performance: F1=0.898 (validation), Precision=0.930, Recall=0.869
- Format: Dict (v2) - PyTorch 2.8 compatible
- Status: ✅ VALIDATED FOR PRODUCTION

NER Model: out/ner_train_out/named_entity_recognition_v2.pt
- Size: 473MB
- MD5: fb53cb6c17db50d62bd90a4dcea83fa4
- Performance: F1=0.749 (validation), Precision=0.779, Recall=0.722
- Format: Dict (v2) - PyTorch 2.8 compatible
- Status: ✅ VALIDATED FOR PRODUCTION
```

**History**: These V2 models were converted from original training (October 21, 2025) on October 27, 2025 to fix PyTorch 2.8 compatibility. They combine validated training quality with cross-platform compatibility.

### **Legacy Models (V1 - Local Use Only)**

**⚠️ DO NOT USE IN COLAB (PyTorch 2.8)**:
```
Classification Model: out/original_model/article_classifier.pt
- MD5: a496eae1d5cf343ae509bcbc7e3f400e
- Format: NamedTuple (v1) - PyTorch 2.8 INCOMPATIBLE
- Status: Works locally (PyTorch 2.2), fails in Colab

NER Model: out/original_model/named_entity_recognition.pt
- MD5: 37eebc38463a90c43cc36ee8ee1f4aa3
- Format: NamedTuple (v1) - PyTorch 2.8 INCOMPATIBLE
- Status: Works locally (PyTorch 2.2), fails in Colab
```

**Note**: These are the original models with good training but incompatible checkpoint format. They were converted to V2 format. Use V2 models instead.

### **Session Management (Updated)**
- **Unique Session IDs**: Each training run gets auto-generated unique ID (`YYYY-MM-DD-abcdef`)
- **Session Isolation**: No directory conflicts between parallel runs
- **No Cleaning Required**: Unique paths eliminate need for directory management
- **Session Format**: Date + 6-character random string for complete uniqueness

### **Available Datasets**
- **Full Training Data**: `data/manual_classifications.csv` (1,635), `data/manual_ner_extraction.csv` (554)
- **Test Data**: `data/manual_classifications_test.csv` (100), `data/manual_ner_extraction_test.csv` (50)
- **2022 EuropePMC Data**: `data/epmc_query_results_2022.csv` (21,677 papers)

### **Output Directories (Session-Specific)**
- **Training Splits**: `data/classif_splits_full_{UNIQUE_ID}`, `data/ner_splits_full_{UNIQUE_ID}`
- **Training Outputs**: `out/classif_train_full_{UNIQUE_ID}`, `out/ner_train_full_{UNIQUE_ID}`
- **Logs & Backups**: `logs_{UNIQUE_ID}`, `model_backups_{UNIQUE_ID}`
- **Production Models**: `out/classif_train_out/`, `out/ner_train_out/` (standard locations for compatibility)

### **Model Archive (Updated Paths)**
- **Session Archives**: `/content/drive/MyDrive/inventory_2022/training_archives/{UNIQUE_ID}_full_training/`
- **Session ID Format**: `YYYY-MM-DD-abcdef` (production) or `YYYY-MM-DD-abcdef_test` (test mode)
- **Compatibility**: Archives accessible by session ID for inventory traceability
- **Legacy Location**: `trained_models_25/2025-10-21_full_production_training/` (local bash script)
- **Complete Preservation**: Models, training stats, logs, evaluation results

### **🔑 Google Drive Access via Rclone (NEW - 2025-10-29)**

**CRITICAL FOR AI AGENTS**: Direct access to Google Drive is now available using the rclone skill.

**What This Means**:
- ✅ **Direct access** to all experimental and training archives stored in Google Drive
- ✅ **Download results** from Colab training runs for local analysis
- ✅ **View metadata** without downloading entire archives
- ✅ **Backup local results** to Drive when needed
- ✅ **Retrieve models** from any training session

**Remote Configuration**:
- **Remote Name**: `gdrive` (configured and verified)
- **Base Path**: `gdrive:inventory_2022/`
- **Key Directories**:
  - `experiment_archives/` - Experimental training results (TEST_MODE runs)
  - `training_archives/` - Production training results
  - `data/`, `out/`, `docs/`, `config/` - Project files

**Usage Rules** (See `docs/RCLONE_USAGE_GUIDE.md` for complete details):
1. **Read-only by default** - Always prefer listing/downloading over modifications
2. **Token efficient** - Avoid `--progress` and `--dry-run` flags (use `tree`, `lsf` instead)
3. **Safe operations** - Get user confirmation before uploads/deletes
4. **Common commands**:
   - List sessions: `rclone lsd gdrive:inventory_2022/experiment_archives`
   - View structure: `rclone tree gdrive:path --level 2`
   - Download: `rclone copy gdrive:path /local/path`
   - View file: `rclone cat gdrive:path/file.json`

**When to Use Rclone**:
- 🔍 User asks to "check what's on Drive" or "download experimental results"
- 📊 Need to analyze completed Colab training runs
- 🔄 Comparing local results with Drive archives
- 📦 Retrieving specific models or session artifacts
- 🗂️ Managing experimental training archives

**Reference**: See `docs/RCLONE_USAGE_GUIDE.md` for comprehensive usage rules and examples.

### **🔄 Automated Sync Scripts (NEW - 2025-10-29)**

**Python scripts for automated Google Drive synchronization** - located in project root.

**Available Scripts**:

1. **upload_to_drive.py** - Upload files to Google Drive
   - Preserves directory structure automatically
   - MD5 checksum-based change detection (skips unchanged files)
   - `--force` flag to skip change detection
   - CSV audit logs in `upload_logs/`

2. **download_from_drive.py** - Download new archives from Google Drive
   - Configurable archive types (experiment_archives, training_archives, custom)
   - Only downloads NEW sessions (folder existence check)
   - `--interactive` mode for confirmation
   - CSV audit logs in `download_logs/`

**Common Usage**:
```bash
# Upload files for Colab testing
python upload_to_drive.py experimental_training_pipeline.ipynb src/experimental_utils.py

# Download new experimental results
python download_from_drive.py --archive-type experiment_archives

# Force re-upload
python upload_to_drive.py --force src/file.py

# Interactive download with confirmation
python download_from_drive.py --archive-type training_archives --interactive
```

**When to Use These Scripts**:
- 📤 Before Colab runs: Upload updated code to Drive
- 📥 After Colab runs: Download new experimental results for analysis
- 🔄 Regular sync: Keep local and Drive in sync
- 📋 Audit trail: All operations logged to CSV with checksums

**Reference**: See `GDRIVE_SYNC_README.md` in project root for complete documentation, examples, and troubleshooting.

---

## 📚 **Critical File Reference List**

### **Core Documentation** (MUST READ)
- `GBC/inventory_2022/docs/README.md` - Main project overview and workflow
- `GBC/inventory_2022/docs/modernization-python311.md` - Complete modernization documentation
- `GBC/inventory_2022/docs/training_ML_explanation.md` - Detailed ML pipeline explanation with BIO tagging
- `GBC/inventory_2022/docs/MODERN_ENVIRONMENT_SETUP.md` - Environment setup and troubleshooting
- `GBC/inventory_2022/docs/FULL_TRAINING_README.md` - Training pipeline user guide
- `GBC/inventory_2022/docs/PYTORCH_CHECKPOINT_FIX.md` - PyTorch compatibility and checkpoint issues resolution
- `GBC/inventory_2022/docs/PIPELINE_GUIDES.md` - Comprehensive pipeline execution guides
- `GBC/inventory_2022/docs/HISTORICAL_UPDATES.md` - Session-by-session changelog and technical evolution
- `GBC/inventory_2022/docs/INVENTORY_COMPARISON_ANALYSIS.md` - Quality validation and comparison methodology
- `GBC/inventory_2022/docs/RCLONE_USAGE_GUIDE.md` - **NEW (2025-10-29)** Google Drive access using rclone skill - CRITICAL for AI agents
- `GBC/inventory_2022/docs/EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md` - **NEW (2025-10-29)** Experimental training infrastructure and progress report
- `GBC/inventory_2022/docs/COMPREHENSIVE_IMPLEMENTATION_PLAN.md` - **NEW (2025-10-29)** 3-phase model improvement roadmap
- `GBC/inventory_2022/docs/MULTI_MODEL_RESULTS_2025-10-30.md` - **NEW (2025-10-30)** Multi-model comparison results and critical performance gap analysis

### **Execution Scripts**
- `GBC/inventory_2022/run_full_training.sh` - Main production training pipeline (9.5h)
- `GBC/inventory_2022/monitor_training.sh` - Training progress monitoring
- `GBC/inventory_2022/rerun_2022_inventory.sh` - 2022 inventory rerun (production)
- `GBC/inventory_2022/test_rerun_2022_inventory.sh` - Test version (small dataset)
- `GBC/inventory_2022/setup_training_worktree.sh` - Git worktree setup for isolated training

### **Configuration Files**
- `GBC/inventory_2022/config/train_predict.yml` - Production training configuration
- `GBC/inventory_2022/config/models_info.tsv` - All 16 BERT model configurations
- `GBC/inventory_2022/config/train_test_modern.yml` - Modern test training config
- `GBC/inventory_2022/requirements_frozen.txt` - Exact working package versions

### **Recent Work Documentation**
- `GBC/inventory_2022/docs/full_training_21_10_25_doc.md` - October 21 training session documentation
- `GBC/inventory_2022/docs/MODEL_ARCHIVAL_SYSTEM.md` - Model archival system implementation
- `GBC/inventory_2022/docs/RERUN_NOTEBOOK_SIMPLIFICATION_SUMMARY.md` - Rerun notebook simplification (October 28, 2025)
- `GBC/inventory_2022/plans/2025-10-22_2022_inventory_rerun_plan.md` - 2022 rerun implementation plan
- `GBC/inventory_2022/plans/2025-10-23_colab_conversion_plan.md` - Colab notebook conversion plan
- `GBC/inventory_2022/plans/2025-10-28_rerun_notebook_simplification_plan.md` - Rerun simplification implementation plan
- `GBC/inventory_2022/plans/2025-10-28_model_traceability_plan.md` - Model traceability implementation plan

### **Experimental Training & Research** (NEW 2025-10-29)
- `GBC/inventory_2022/docs/research/RESEARCH_FINDINGS_CONSOLIDATED.md` - Master consolidation of all research findings
- `GBC/inventory_2022/docs/research/BASE_RESEARCH_BRIEF.md` - Comprehensive project context for research agents
- `GBC/inventory_2022/docs/research/MODERN_ML_ALTERNATIVES_RESEARCH_REPORT.md` - 100+ page report on modern ML techniques
- `GBC/inventory_2022/docs/research/DATA_AUGMENTATION_NER_RESEARCH_REPORT.md` - Data augmentation strategies and implementations
- `GBC/inventory_2022/docs/research/FEW_SHOT_META_LEARNING_RESEARCH_REPORT.md` - Few-shot learning and meta-learning approaches
- `GBC/inventory_2022/docs/research/ENSEMBLE_MULTITASK_RESEARCH_REPORT.md` - Ensemble and multi-task learning evaluation
- `GBC/inventory_2022/docs/CODE_FIXES_VERIFICATION_2025-10-29.md` - Verification of critical code fixes

### **Experimental Training Analysis** (NEW 2025-10-29 & 2025-10-30)
- `GBC/inventory_2022/docs/EXPERIMENTAL_SESSION_ANALYSIS_2025-10-29.md` - **Complete analysis of first full experimental run**
  - Session 2025-10-29-4lblwv: 4 experiments, 53 minutes total
  - Infrastructure validation: ✅ All systems operational
  - Performance results: Classification F1=0.882, NER F1=0.630 (best configurations)
  - Root cause analysis: Data split inconsistency vs production baseline
  - Recommendations for next experimental run
- `GBC/inventory_2022/docs/MULTI_MODEL_RESULTS_2025-10-30.md` - **Multi-model comparison results and critical findings**
  - Session 2025-10-30-p9rat5: 4 models, 64 minutes total
  - Fixed data splits: Production data with optimal hyperparameters
  - Classification results: PubMedBERT best (F1=0.917) - exceeds V2 baseline
  - NER results: All models BELOW V2 baseline by 10-16% (CRITICAL ISSUE)
  - Root cause analysis: 5 hypotheses for performance gap
  - Critical action required: Find V2 actual training configuration

### **Google Colab Notebooks**
- `GBC/inventory_2022/experimental_training_pipeline.ipynb` - **NEW (2025-10-29)** Automated experimental training with hyperparameter optimization
- `GBC/inventory_2022/full_training_pipeline_simplified.ipynb` - Complete training pipeline (simplified, no checkpoints)
- `GBC/inventory_2022/full_training_pipeline_with_checkpoints_clean.ipynb` - DEPRECATED - Use simplified version
- `GBC/inventory_2022/inventory_update_pipeline_with_checkpoints.ipynb` - Inventory update pipeline with model traceability
- `GBC/inventory_2022/rerun_2022_inventory_simplified.ipynb` - Streamlined 2022 dataset rerun (simplified, no checkpoints)
- `GBC/inventory_2022/rerun_2022_inventory_with_checkpoints.ipynb.backup` - DEPRECATED - Backup of checkpoint version

### **Source Code**
- `GBC/inventory_2022/src/class_train.py` - Classification model training (updated 2025-10-29: early stopping support)
- `GBC/inventory_2022/src/ner_train.py` - NER model training (updated 2025-10-29: early stopping support)
- `GBC/inventory_2022/src/class_predict.py` - Classification prediction
- `GBC/inventory_2022/src/ner_predict.py` - NER prediction
- `GBC/inventory_2022/src/inventory_utils/` - Utility modules and classes
- `GBC/inventory_2022/src/experimental_utils.py` - **NEW (2025-10-29)** Experimental training utilities (EarlyStopping, ExperimentTracker)
- `GBC/inventory_2022/src/data_augmentation/` - **NEW (2025-10-29)** Data augmentation module (placeholders for Phase 2)
- `GBC/inventory_2022/augment_ner_dataset.py` - **NEW (2025-10-29)** CLI tool for data augmentation

---

## 🔧 **Key Technical Details**

### **Model Specifications**
- **Base Architecture**: RoBERTa (Robustly Optimized BERT Pretraining Approach)
- **Domain Adaptation**: Biomedical text (allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500)
- **Batch Size**: 16, Learning Rate: 2e-5, Optimizer: AdamW
- **Max Sequence Length**: 256 (classification), 512 (NER)

### **Performance Expectations**
- **Training Time**: ~9.5 hours for full production training
- **Prediction Speed**: ~54 minutes for 21,677 papers (classification)
- **Memory Requirements**: ~8GB peak during training/inference
- **Storage**: ~1GB per complete training run (models + artifacts)

### **Data Processing**
- **BIO Tagging**: O (outside), B-COM/I-COM (compound names), B-FUL/I-FUL (full names)
- **Text Processing**: Title + abstract concatenation, tokenization, truncation
- **Entity Extraction**: Regex-based URL extraction, probability-based name selection

---

## 💻 **Common Tasks & Commands**

### **Environment Management**
```bash
# Activate environment
source biodata_modern_env/bin/activate

# Verify environment
python -c "import torch, transformers; print(f'PyTorch: {torch.__version__}, Transformers: {transformers.__version__}')"

# Deactivate
deactivate
```

### **Training Operations**
```bash
# Full production training
./run_full_training.sh

# Quick test training (5-8 minutes)
./run_train_test_modern.sh

# Monitor training progress
./monitor_training.sh --follow
```

### **Prediction Operations**
```bash
# Manual classification prediction
python src/class_predict.py -c out/classif_train_out/article_classifier.pt -i data/input.csv -o output_dir/

# Manual NER prediction  
python src/ner_predict.py -c out/ner_train_out/named_entity_recognition.pt -i data/input.csv -o output_dir/

# Full pipeline (2022 rerun)
./rerun_2022_inventory.sh
```

### **Results Analysis**
```bash
# Check recent results
ls -la inventory_classification_results/

# View training logs
tail -f logs/full_training_*.log

# Check model archives
ls -la trained_models_25/
```

---

### **Training-Inventory Compatibility**
- **Archive Path**: ✅ FIXED - Both use `training_archives/{UNIQUE_ID}_full_training/`
- **Model Traceability**: ✅ REQUIRED - TRAINING_SESSION_ID mandatory in rerun notebook
- **Session Linking**: Training UNIQUE_ID → Rerun TRAINING_SESSION_ID → Full audit trail
- **Utility Functions**: Training uses `src/training_utils.py`, Rerun uses `src/rerun_utils.py`
- **Resolution Status**: ✅ Fixed as of 2025-10-24 - Full traceability enforced
- **Script Execution**: Both use absolute paths with INVENTORY_DIRECTORY prefix

---

## 🛡️ **Safety & Best Practices**

### **Backup Procedures**
- **Automatic Backups**: All training runs create timestamped backups in `model_backups/`
- **Model Archival**: Complete training runs preserved in `trained_models_25/`
- **Git Version Control**: All code changes committed to git branches

### **Model Protection**
- **Overwrite Prevention**: Archival system prevents model loss
- **Checkpoint Validation**: Models verified before deployment
- **Recovery Options**: Previous models can be restored from archives

### **Error Handling**
- **Comprehensive Logging**: All operations logged with timestamps
- **Graceful Failures**: Scripts handle errors and provide actionable messages
- **Environment Validation**: Prerequisites checked before execution

---

## 🎯 **Current Capabilities**

### **Enhanced Training Features**
- ✅ **Test Mode Toggle**: Single variable for quick testing (5-8 min) vs production (9.5 hr)
- ✅ **Parallel Training Sessions**: Multiple notebooks can run simultaneously
- ✅ **Zero Conflicts**: Each session completely isolated with unique directories
- ✅ **No Checkpoints**: Simple linear pipeline eliminates data contamination risk
- ✅ **Utility Separation**: Core algorithms separated from utility functions (`src/training_utils.py`)
- ✅ **Session Traceability**: Full lineage from training to inventory processing
- ✅ **Simplified Workflow**: No directory cleaning or conflict resolution needed

### **Experimental Training Infrastructure** (NEW - 2025-10-29)
- ✅ **Pre-Flight Checks**: 6-point validation before training (imports, NLTK, model, data, GPU)
- ✅ **Enhanced Logging**: Complete subprocess output captured to files
- ✅ **Error Diagnostics**: Full tracebacks saved to error_details.txt files
- ✅ **Log Archival**: Training logs and error details included in session archives
- ✅ **Notebook Visibility**: Last 50 lines of training output displayed for quick debugging
- ✅ **Timeout Protection**: 3600s (1 hour) timeout prevents hung processes
- ✅ **Intelligent Error Tracking**: References log files in experiment results CSV
- ✅ **Google Drive Ready**: All updates compatible with Colab/Drive workflow

### **Immediate Use**
- ✅ **Run Production Training**: Full 10-epoch training on complete datasets (Google Colab)
- ✅ **Process New Literature**: Apply models to new EuropePMC queries (Google Colab + Local)
- ✅ **Generate Inventories**: Create structured biodata resource catalogs (7 workflow options)
- ✅ **Rerun 2022 Dataset**: Streamlined processing of 21,677 papers with latest models (Google Colab)
- ✅ **Monitor Progress**: Real-time tracking of long-running processes
- ✅ **Model Traceability**: Link inventory updates to specific training sessions

### **Available Models**
- ✅ **Production Classification Model**: Ready for immediate use (F1=0.898)
- ✅ **Production NER Model**: Ready for immediate use (F1=0.749)
- ✅ **16 Model Configurations**: Available for comparative training
- ✅ **Test Models**: Smaller datasets for quick validation

### **Data Processing**
- ✅ **EuropePMC Integration**: Query and process scientific literature
- ✅ **Multi-format Support**: CSV, pickle, JSON outputs
- ✅ **Batch Processing**: Handle thousands of papers efficiently
- ✅ **Quality Control**: Confidence scoring and validation

---

## 📝 **Recent Technical Updates**

For detailed session-by-session changelog, architecture evolution, and refactoring work, see [`HISTORICAL_UPDATES.md`](HISTORICAL_UPDATES.md).

**Recent Highlights:**
- ⚠️ **October 30, 2025**: **CRITICAL - Multi-model comparison reveals baseline performance gap** (session 2025-10-30-p9rat5)
  - All 4 models tested (64 minutes total)
  - Fixed data splits to use production data ✅
  - Classification: PubMedBERT F1=0.917 (+2.1% vs V2) ✅
  - **NER: All models 10-16% BELOW V2 baseline (F1=0.630-0.670 vs V2 0.749) ❌**
  - **CRITICAL ISSUE**: Cannot match V2 baseline performance despite validated infrastructure
  - **Action required**: Find actual V2 training configuration and parameters
  - See [`MULTI_MODEL_RESULTS_2025-10-30.md`](MULTI_MODEL_RESULTS_2025-10-30.md)
- ✅ **October 29, 2025**: **First full experimental run completed** (session 2025-10-29-4lblwv)
  - All 4 experiments successful (53 minutes total)
  - Infrastructure 100% validated: logging, tracking, archival all operational
  - Results: Classification F1=0.882, NER F1=0.630 (best configs)
  - Issue identified: Data split inconsistency prevents baseline comparison
  - Fixed in next run (2025-10-30-p9rat5)
  - See [`EXPERIMENTAL_RESULTS_COMPREHENSIVE_2025-10-29.md`](EXPERIMENTAL_RESULTS_COMPREHENSIVE_2025-10-29.md) and [`EXPERIMENTAL_SESSION_ANALYSIS_2025-10-29.md`](EXPERIMENTAL_SESSION_ANALYSIS_2025-10-29.md)
- ✅ **October 29, 2025**: Experimental training infrastructure complete - enhanced logging, pre-flight checks, error diagnostics
- ✅ **October 29, 2025**: Google Drive sync scripts operational - upload_to_drive.py, download_from_drive.py with MD5 checking
- ✅ **October 29, 2025**: Google Drive access via rclone skill - direct access to experimental archives
- ✅ **October 29, 2025**: 3-phase model improvement plan - roadmap to NER F1 0.85-0.88 (+15-18%)
- ✅ **October 28, 2025**: Rerun notebook simplified - removed checkpoint system for data integrity
- ✅ **October 28, 2025**: Checkpoint corruption issue resolved - deprecated checkpoint functionality
- ✅ **October 27, 2025**: PyTorch 2.8 compatibility issue resolved - see [`PYTORCH_CHECKPOINT_FIX.md`](PYTORCH_CHECKPOINT_FIX.md)
- ✅ **October 24, 2025**: Rerun notebook restructured with reusable utility functions
- ✅ **October 24, 2025**: Inventory comparison analysis completed - 82% validation accuracy
- ✅ **October 23, 2025**: Google Colab integration with path fixes and session isolation

---

## 📊 **Pipeline Execution Options**

The system provides two Google Colab pipelines for different use cases. For comprehensive pipeline guides, see [`PIPELINE_GUIDES.md`](PIPELINE_GUIDES.md).

### **Inventory Update Pipeline**
**Notebook**: `inventory_update_pipeline_with_checkpoints.ipynb`
**Use Case**: Process new EuropePMC queries with manual review and URL validation
**Features**: 7 workflow options from full pipeline to fast-track processing

### **2022 Inventory Rerun Pipeline**
**Notebook**: `rerun_2022_inventory_with_checkpoints.ipynb`
**Use Case**: Streamlined processing of 2022 dataset (21,677 papers)
**Features**: Optimized 5-step pipeline, full/test modes, GPU acceleration

For inventory quality validation, see [`INVENTORY_COMPARISON_ANALYSIS.md`](INVENTORY_COMPARISON_ANALYSIS.md).

---

## 🔄 **Development Context**

### **Recent Modernization** (October 2025)
- **Python Upgrade**: 3.8 → 3.11.9 with modern ML stack
- **Package Updates**: PyTorch 2.2.2, Transformers 4.35.0, modern ecosystem
- **Infrastructure**: Complete training pipeline with monitoring and archival
- **Testing**: Comprehensive validation and integration testing

### **Current Project Status**
- **Phase**: Production-ready with active development
- **Models**: Latest training completed October 21, 2025
- **Pipeline**: 2022 inventory rerun in progress (estimated completion ~13:54)
- **Documentation**: Comprehensive guides and technical documentation

### **Future Opportunities**
- **Hyperparameter Optimization**: Further improve NER performance
- **Ensemble Methods**: Combine multiple model predictions
- **Data Augmentation**: Expand training datasets
- **Real-time Processing**: Stream processing capabilities

---

## 📋 **Document Maintenance Instructions**

### **CRITICAL: This Document Must Be Kept Updated**

**When to Update**:
- ✅ After completing major training runs
- ✅ When models are updated or replaced
- ✅ After significant code changes or new features
- ✅ When performance metrics change
- ✅ After environment updates or dependency changes

**Git Workflow Requirements**:
- ✅ **Git Repository**: `GBC/inventory_2022/` is the git repository root (not GBC/)
- ✅ **Commit work to git at regular intervals** (at least daily)
- ✅ **Always prompt user if new branch needed for new work**
- ✅ **Use descriptive commit messages with context**
- ✅ **Tag major releases and model updates**
- ❌ **Do NOT include AI attribution lines** in commit messages (no "Generated with Claude Code" or "Co-Authored-By: Claude")

**Planning Requirements**:
- ✅ **Always write detailed plans to the `plans/` folder before major work**
- ✅ **Use format: `YYYY-MM-DD_description_plan.md`**
- ✅ **Include timeline, requirements, and success criteria**
- ✅ **Update plans with actual results and lessons learned**

**Update Process**:
1. **Read current version** of this document before starting work
2. **Update relevant sections** as work progresses
3. **Add new file references** with full paths from GBC root
4. **Update performance metrics** with latest results
5. **Commit updates** with clear messages about what changed
6. **Update timestamp** at top of document

**File Path Convention**:
- **Always use full paths from GBC root**: `GBC/inventory_2022/filename`
- **Verify paths are accessible**: Test paths before committing
- **Use consistent formatting**: Maintain readability and navigation

**Version Control**:
- **This document lives at**: `GBC/inventory_2022/docs/starting_doc.md`
- **Update last modified date**: Every time changes are made
- **Maintain change log**: Consider adding brief change notes for major updates

---

## Conclusion & Critical Learnings

### System Status: Production Ready

The biodata inventory ML pipeline is **production-ready** and has been successfully deployed in both local (Python 3.8/PyTorch 2.0) and Google Colab (Python 3.10/PyTorch 2.8) environments. The system demonstrates:

- ✅ **High Performance**: Classification F1=0.898, NER F1=0.749
- ✅ **Cross-Platform Compatibility**: Resolved PyTorch version incompatibilities
- ✅ **Data Integrity**: 99.97% prediction match between environments
- ✅ **Production Reliability**: Clean pipeline without checkpoint complexity

### Critical Issues Resolved

Three major technical challenges were identified and resolved during October 2025:

#### 1. PyTorch Checkpoint Compatibility (2025-10-27)

**Problem**: Models trained in PyTorch 2.0.0 experienced 99% prediction loss when loaded in PyTorch 2.8.0 (Colab environment) due to NamedTuple deserialization issues.

**Solution**: Converted checkpoints to dict-only format with backward-compatible loading using `weights_only=True`.

**Impact**: Saved ~9.5 hours of retraining time, enabled seamless cross-platform deployment.

**Reference**: See `GBC/inventory_2022/docs/PYTORCH_CHECKPOINT_FIX.md` for complete technical details.

#### 2. Checkpoint Corruption in Rerun Pipeline (2025-10-28)

**Problem**: One Colab run showed 24% drop in confidence scores (74% vs 97% local) due to checkpoint system loading cached results from a different run.

**Evidence**:
- 825 rows lost during URL extraction step
- 125 mismatched IDs between pipeline steps
- 0% probability match between NER and URL extraction outputs

**Root Cause**: Checkpoint loading system mixed data from different pipeline sessions, causing data contamination.

**Resolution**: **Deprecated checkpoint functionality** from rerun pipeline. System runs fast enough (~10 minutes) that checkpointing adds unnecessary complexity and data integrity risks.

**Reference**: See `GBC/inventory_2022/docs/PYTORCH_CHECKPOINT_FIX.md` (Addendum) for complete investigation details.

#### 3. Model Training Quality Issues (2025-10-29)

**Problem**: Newly trained models (October 28, 2025) showed 99.4% prediction loss despite using correct checkpoint format and architecture.

**Root Cause**: Poor training quality - NER model achieved only F1=0.653 vs expected F1=0.749 due to:
- Learning rate too high (2e-5)
- Insufficient regularization (no weight decay)
- Training instability (F1 bouncing, peak at epoch 4 then decline)
- Overfitting (train F1=0.974 vs val F1=0.621, gap of 0.353)

**Solution**: Identified optimal training hyperparameters:
- Lower learning rate: 1e-5 or 5e-6
- Weight decay: 0.01
- Increased dropout: 0.2-0.3
- Early stopping: Monitor validation F1, stop if no improvement for 3 epochs
- More epochs: 15-20 with early stopping

**Impact**: Established training quality validation checklist, V2 models validated for production use.

**Reference**: See `GBC/inventory_2022/docs/FINAL_DIAGNOSIS_SUMMARY.md` and `GBC/inventory_2022/docs/MODEL_DEGRADATION_ROOT_CAUSE_ANALYSIS.md` for complete analysis.

### Best Practices Established

From these experiences, the following practices are now required:

1. **No Checkpoint Systems**: Each pipeline run produces completely fresh results
   - Eliminates cross-contamination risk
   - Simplifies debugging and validation
   - Maintains data integrity across all steps

2. **Data Integrity Validation**: Always verify between pipeline steps:
   - Row counts match expectations
   - IDs are consistent across steps
   - Sample values validate correctly
   - Probability distributions remain stable

3. **Diagnostic Methodology**: When investigating data quality issues:
   - Check each pipeline step independently
   - Compare row counts and IDs between consecutive steps
   - Validate sample data matches expectations
   - Don't assume obvious culprits without evidence

4. **Version Control**: For PyTorch models:
   - Use dict-only checkpoint format
   - Load with `weights_only=True`
   - Maintain parameter checksums for validation
   - Document version compatibility explicitly

5. **Training Quality Validation**: Before deploying new models:
   - Validation F1 > 0.70 for NER, > 0.85 for classification
   - Test F1 matches validation F1 (±0.02)
   - Training shows steady improvement (no bouncing)
   - Train/val gap < 0.15 (acceptable overfitting)
   - Test inference produces expected high-confidence predictions (>80% at threshold 0.978)
   - Compare with baseline inventory (>75% overlap)

### Operational Recommendations

**For Future Development**:
- Keep pipeline architecture simple and linear
- Avoid premature optimization (e.g., checkpointing for 10-minute runs)
- Prioritize data integrity over convenience features
- Test cross-platform compatibility explicitly
- Document all technical decisions and their rationale

**For Production Use**:
- Use fresh runs without checkpoints
- Validate output statistics match expectations
- Archive complete session results with traceability
- Reference clean baseline runs for comparison
- Monitor for unexpected probability distributions

### Documentation References

**Primary Technical Documents**:
- **This Document**: System overview and operational guide
- **FINAL_DIAGNOSIS_SUMMARY.md**: Complete model quality investigation summary (2025-10-29)
- **MODEL_DEGRADATION_ROOT_CAUSE_ANALYSIS.md**: Detailed technical analysis of training quality issues
- **PYTORCH_CHECKPOINT_FIX.md**: Complete technical resolution of PyTorch compatibility and checkpoint corruption issues
- **INVENTORY_COMPARISON_REPORT_2025-10-28.md**: Detailed comparison of model outputs and quality validation
- **CRITICAL_INVESTIGATION_2025-10-28.md**: Investigation process and diagnostic methodology
- **COMPARISON_SUMMARY.txt**: Quick reference summary of model comparisons

**Supporting Documentation**:
- Training procedures: In-file documentation in training notebooks
- Model architecture: See `src/` directory scripts
- Data processing: See `src/` utility scripts

---

**Document Status**: ✅ **CURRENT AND ACCURATE**
**Document Location**: `GBC/inventory_2022/docs/starting_doc.md`
**Last Updated**: 2025-10-30 (Added multi-model comparison critical findings)
**Next Review**: After V2 training configuration investigation
**Maintained by**: AI agents working on biodata inventory pipeline

---

## 🎓 **Training New Models: Validated Parameters**

Based on the October 2025 investigation, use these parameters for new model training:

### **Recommended Hyperparameters**

```yaml
# Classification Model
epochs: 10-15
batch_size: 16
learning_rate: 1e-5  # Lower than default 2e-5
weight_decay: 0.01   # Add regularization
dropout: 0.2-0.3     # Increase if available
optimizer: AdamW
early_stopping: 3 epochs without improvement

# NER Model (requires more care due to small dataset)
epochs: 15-20
batch_size: 16
learning_rate: 5e-6  # Even lower for stability
weight_decay: 0.01
dropout: 0.3
optimizer: AdamW
early_stopping: 3 epochs without improvement
```

### **Training Quality Validation Checklist**

Before deploying newly trained models, verify:

- [ ] **NER test F1 > 0.70** (minimum acceptable)
- [ ] **Classification test F1 > 0.85** (minimum acceptable)
- [ ] **Training stability**: Validation F1 shows steady improvement
- [ ] **No bouncing**: F1 doesn't decline significantly after peak
- [ ] **Low overfitting**: Train/val F1 gap < 0.15
- [ ] **Checkpoint format**: Uses dicts, not NamedTuples
- [ ] **Inference test**: Sample papers produce expected high-confidence results
- [ ] **High-confidence rate > 80%**: At threshold 0.978
- [ ] **Baseline comparison**: >75% overlap with validated inventory
- [ ] **Parameter checksums**: Documented for model verification

### **Known Training Issues to Avoid**

**❌ DO NOT**:
- Use learning rate 2e-5 (too high, causes instability)
- Skip weight decay (causes overfitting on small NER dataset)
- Train without early stopping (leads to overfitting)
- Ignore validation curve instability (sign of poor training)
- Deploy without testing on sample data

**✅ DO**:
- Monitor validation curves during training
- Stop at first sign of sustained decline
- Test models immediately after training
- Compare with baseline before deployment
- Document training parameters and results

### **Training Data Limitations**

**Current Datasets**:
- Classification: 1,635 samples (adequate)
- NER: 554 samples (small - requires careful hyperparameters)

**Long-term Goal**: Expand NER dataset to 1,000-2,000 samples for more robust training.

**For Details**: See `docs/FINAL_DIAGNOSIS_SUMMARY.md` for complete training recommendations.