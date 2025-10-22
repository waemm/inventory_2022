# Biodata Inventory ML Pipeline - AI Agent Reference Guide

**Created**: 2025-10-22  
**Last Updated**: 2025-10-22 (File paths updated for docs/ reorganization)  
**Status**: ✅ **PRODUCTION READY**  
**Purpose**: Living document for AI agents working on the biodata inventory ML pipeline

---

## 🎯 **Executive Summary**

This is a **sophisticated ML pipeline** that uses biomedical BERT models to automatically identify and extract biodata resources from scientific literature. The system processes EuropePMC query results through classification and Named Entity Recognition (NER) to generate comprehensive inventories of global biodata resources.

### **Current Status**
- ✅ **Production Ready**: Latest models trained October 21, 2025
- ✅ **Modern Environment**: Python 3.11.9, PyTorch 2.2.2, Transformers 4.35.0
- ✅ **High Performance**: Classification F1=0.898, NER F1=0.749
- ✅ **Complete Infrastructure**: Training, prediction, monitoring, and archival systems

### **Key Architecture**
- **Two-Model System**: Classification (bio-resource detection) + NER (database name extraction)
- **Base Model**: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500` (biomedical RoBERTa)
- **Pipeline**: EuropePMC → Classification → NER → URL Extraction → Processing → Final Inventory
- **Data**: 1,635 classification samples + 554 NER samples (manually curated)

---

## 🚀 **Quick Start**

### **Environment Activation**
```bash
cd GBC/inventory_2022/  # This is the git repository root
source biodata_modern_env/bin/activate
export PYTHONPATH="src:$PYTHONPATH"
```

### **Run Full Training Pipeline** (9.5 hours)
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

### **Latest Models (October 21, 2025)**
```
Classification Model: out/classif_train_out/article_classifier.pt
- Size: 476MB
- Performance: F1=0.898 (validation), Precision=0.930, Recall=0.869
- Training: 10 epochs on 1,635 samples

NER Model: out/ner_train_out/named_entity_recognition.pt  
- Size: 481MB
- Performance: F1=0.749 (validation), Precision=0.779, Recall=0.722
- Training: 10 epochs on 554 samples
```

### **Available Datasets**
- **Full Training Data**: `data/manual_classifications.csv` (1,635), `data/manual_ner_extraction.csv` (554)
- **Test Data**: `data/manual_classifications_test.csv` (100), `data/manual_ner_extraction_test.csv` (50)
- **2022 EuropePMC Data**: `data/epmc_query_results_2022.csv` (21,677 papers)

### **Model Archive**
- **Location**: `trained_models_25/2025-10-21_full_production_training/`
- **Complete Preservation**: Models, training stats, logs, evaluation results
- **Automatic Archival**: Every training run preserved with documentation

---

## 📚 **Critical File Reference List**

### **Core Documentation** (MUST READ)
- `GBC/inventory_2022/docs/README.md` - Main project overview and workflow
- `GBC/inventory_2022/docs/modernization-python311.md` - Complete modernization documentation
- `GBC/inventory_2022/docs/training_ML_explanation.md` - Detailed ML pipeline explanation with BIO tagging
- `GBC/inventory_2022/docs/MODERN_ENVIRONMENT_SETUP.md` - Environment setup and troubleshooting
- `GBC/inventory_2022/docs/FULL_TRAINING_README.md` - Training pipeline user guide

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
- `GBC/inventory_2022/plans/2025-10-22_2022_inventory_rerun_plan.md` - 2022 rerun implementation plan

### **Source Code**
- `GBC/inventory_2022/src/class_train.py` - Classification model training
- `GBC/inventory_2022/src/ner_train.py` - NER model training
- `GBC/inventory_2022/src/class_predict.py` - Classification prediction
- `GBC/inventory_2022/src/ner_predict.py` - NER prediction
- `GBC/inventory_2022/src/inventory_utils/` - Utility modules and classes

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

### **Immediate Use**
- ✅ **Run Production Training**: Full 10-epoch training on complete datasets
- ✅ **Process New Literature**: Apply models to new EuropePMC queries
- ✅ **Generate Inventories**: Create structured biodata resource catalogs
- ✅ **Monitor Progress**: Real-time tracking of long-running processes

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

**Document Status**: ✅ **CURRENT AND ACCURATE**  
**Document Location**: `GBC/inventory_2022/docs/starting_doc.md`  
**Next Review**: After completion of 2022 inventory rerun  
**Maintained by**: AI agents working on biodata inventory pipeline