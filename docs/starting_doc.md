# Biodata Inventory ML Pipeline - AI Agent Reference Guide

**Created**: 2025-10-22
**Last Updated**: 2025-11-04 (Phase 4 inference bug FIXED - NaN cartesian product)
**Status**: ✅ **PRODUCTION READY** + ✅ **PHASE 4 MULTI-TASK MODEL COMPLETE** + ✅ **PHASE 4 INFERENCE BUG FIXED**
**Purpose**: High-level reference and navigation hub for AI agents

---

## 🎯 Executive Summary

Sophisticated ML pipeline using biomedical BERT models to automatically identify and extract biodata resources from scientific literature. Processes EuropePMC query results through classification and NER to generate comprehensive inventories.

### Current Status
- ✅ **Production Ready**: V2 models validated (Classification F1=0.898, NER F1=0.749)
- ✅ **Modern Stack**: Python 3.11.9, PyTorch 2.2.2, Transformers 4.35.0
- ✅ **Phase 4 Multi-Task Model**: NER F1=0.9274 (+23.82% improvement), PRODUCTION READY
- ✅ **Phase 4 Inference**: Fixed NaN cartesian product bug (288,730 → 20,890 results)

### Key Architecture
- **Two Systems Available**:
  1. **V2 Models** (Traditional): Separate classification + NER models
  2. **Phase 4 Multi-Task** (Recommended): Single unified model with metadata integration
- **Base Model**: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500` (biomedical RoBERTa)
- **Pipeline**: EuropePMC → Classification → NER → URL Extraction → Processing → Final Inventory

---

## ✅ Recently Resolved Issues

### Phase 4 Inference Memory Overflow & Result Discrepancy (2025-11-04)

**Status**: ✅ FIXED AND VERIFIED

**Issues Resolved**:
1. **Memory Overflow** (✅ FIXED):
   - Reduced from 160GB+ → <10GB (94% reduction)
   - Implemented slim results storage + chunked merge

2. **Result Multiplication** (✅ FIXED):
   - Expected: ~21,392 results
   - Was producing: 288,730 results (13.5× multiplication)
   - Root cause: NaN cartesian product in pandas merge
   - Fix: Filter NaN IDs before merge in `InferenceDataset.__init__()`
   - Verification: Test produces 20,890 results (correctly filtered 540 NaN IDs)

**Impact**: ✅ Phase 4 model is now PRODUCTION READY for inference

**Details**:
- Fix documentation: [`docs/PHASE4_INFERENCE_FIX_2025-11-04.md`](PHASE4_INFERENCE_FIX_2025-11-04.md)
- Memory optimization: [`docs/MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md)

---

## 📈 Recent Major Milestones

| Date | Milestone | Status | Performance | Reference |
|------|-----------|--------|-------------|-----------|
| 2025-11-04 | Phase 4 Inference Fix | 🚨 In Progress | Memory: 94% reduction | [MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md) |
| 2025-10-31 | Phase 4 Multi-Task Complete | ✅ Done | NER F1: 0.9274 (+23.82%) | [multi_task_model/README.md](multi_task_model/README.md) |
| 2025-10-30 | Enhanced Metadata Features | ✅ Done | 21,392 papers × 38 features | [ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md](ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md) |
| 2025-10-29 | Training Infrastructure | ✅ Done | Experimental pipeline ready | [EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md](EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md) |
| 2025-10-27 | PyTorch Compatibility | ✅ Resolved | Cross-platform models | [PYTORCH_CHECKPOINT_FIX.md](PYTORCH_CHECKPOINT_FIX.md) |

---

## 🚀 Quick Start

### Environment Setup
```bash
cd GBC/inventory_2022/
source biodata_modern_env/bin/activate
export PYTHONPATH="src:$PYTHONPATH"
```

### Key Operations

**Training** (Google Colab recommended):
- Full production: `full_training_pipeline_simplified.ipynb`
- Test mode: Set `TEST_MODE = True` (5-8 min vs 9.5 hr)
- Local: `./run_full_training.sh`

**Prediction**:
- Full pipeline: `./rerun_2022_inventory.sh`
- Test mode: `./test_rerun_2022_inventory.sh`

**Colab Notebooks**:
- Training: `full_training_pipeline_simplified.ipynb`
- 2022 Rerun: `rerun_2022_inventory_simplified.ipynb`
- Inventory Update: `inventory_update_pipeline_with_checkpoints.ipynb`

**More Commands**: See [`docs/QUICK_REFERENCE_COMMANDS.md`](QUICK_REFERENCE_COMMANDS.md)

---

## 🏗️ System Architecture

### Pipeline Flow
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

### Model Performance

**V2 Models (Traditional Two-Model System)**:
| Model | F1 Score | Precision | Recall | Status |
|-------|----------|-----------|--------|--------|
| Classification | 0.898 | 0.930 | 0.869 | ✅ Production |
| NER | 0.749 | 0.779 | 0.722 | ✅ Production |

**Phase 4 Multi-Task Model** (Recommended):
| Task | F1 Score | vs V2 | Status |
|------|----------|-------|--------|
| NER | **0.9274** | **+23.82%** | ✅ Ready (inference bug blocking) |
| Classification | 0.8586 | -4.38% | ✅ Ready (acceptable trade-off) |
| **Combined** | **0.8917** | **+8.28%** | ✅ Overall improvement |

**Recommendation**: Deploy Phase 4 model once inference bug is resolved

---

## 📊 Production Status

### Production Models (V2 - Currently Active)

**Classification**: `out/classif_train_out/article_classifier_v2.pt`
- F1: 0.898 | Status: ✅ Validated | Format: Dict (PyTorch 2.8 compatible)

**NER**: `out/ner_train_out/named_entity_recognition_v2.pt`
- F1: 0.749 | Status: ✅ Validated | Format: Dict (PyTorch 2.8 compatible)

### Phase 4 Multi-Task Model (Ready for Deployment)

**Location**: `collab_results/experiment_archives/2025-10-31-rq7i4n/multitask_training/`

**Recommended**: `checkpoint_best_ner.pt` (NER F1: 0.9274)

**Note**: Inference pipeline needs bug fix before production use

### Datasets
- **Training**: 1,635 classification samples, 554 NER samples
- **2022 Data**: 21,677 papers in `data/epmc_query_results_2022.csv`
- **Enhanced Metadata**: 21,392 papers × 38 features in `data/metadata/`

---

## 🔄 Google Drive Access

### Python Scripts (Automated Sync)

**Upload Files to Drive**:
```bash
# Upload single or multiple files
python upload_to_drive.py file1.py file2.ipynb src/module.py

# Force re-upload (skip MD5 check)
python upload_to_drive.py --force path/to/file.py

# Logs saved to: upload_logs/
```

**Download Archives from Drive**:
```bash
# Download new experimental results
python download_from_drive.py --archive-type experiment_archives

# Download new training results
python download_from_drive.py --archive-type training_archives

# Interactive mode (with confirmation)
python download_from_drive.py --interactive --archive-type experiment_archives

# Logs saved to: download_logs/
```

**Features**:
- ✅ MD5 checksum-based change detection (skips unchanged files)
- ✅ Preserves directory structure automatically
- ✅ CSV audit logs with timestamps and checksums
- ✅ Only downloads NEW sessions (folder existence check)

**Reference**: See `GDRIVE_SYNC_README.md` in project root for complete documentation

### Rclone Skill (Direct Access for AI Agents)

AI agents can use the rclone skill for direct Google Drive access:

```bash
# List sessions
rclone lsd gdrive:inventory_2022/experiment_archives

# View structure
rclone tree gdrive:inventory_2022/path --level 2

# Download archive
rclone copy gdrive:inventory_2022/experiment_archives/SESSION_ID /local/path

# View file
rclone cat gdrive:inventory_2022/path/file.json
```

**Reference**: [`docs/RCLONE_USAGE_GUIDE.md`](RCLONE_USAGE_GUIDE.md)

---

## 📚 Critical Documentation

### Must-Read Documents
- **This Document** - High-level reference and navigation
- [`README.md`](README.md) - Project overview and workflow
- [`PIPELINE_GUIDES.md`](PIPELINE_GUIDES.md) - Comprehensive pipeline execution guides
- [`TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md) - Hyperparameters and validation checklist
- [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) - Critical issues and best practices
- [`QUICK_REFERENCE_COMMANDS.md`](QUICK_REFERENCE_COMMANDS.md) - Common operations

### NER & LLM Testing
- [`NER_explanation.md`](NER_explanation.md) - **Comprehensive NER guide** (extraction, output format, examples)
- [`../data/llm_comparison/prompts/README.md`](../data/llm_comparison/prompts/README.md) - LLM testing prompts (V2 improved)
- [`../data/llm_comparison/results/ANALYSIS_SUMMARY.md`](../data/llm_comparison/results/ANALYSIS_SUMMARY.md) - LLM vs BERT comparison

### Phase 4 Multi-Task Learning
- [`multi_task_model/README.md`](multi_task_model/README.md) - **Start here** for Phase 4
- [`multi_task_model/PHASE4_IMPLEMENTATION_SUMMARY.md`](multi_task_model/PHASE4_IMPLEMENTATION_SUMMARY.md) - Complete architecture guide
- [`multi_task_model/PHASE4_VS_V2_COMPARISON.md`](multi_task_model/PHASE4_VS_V2_COMPARISON.md) - Why NER improved 23.8%

### Critical Issues & Fixes
- [`MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md) - 🚨 Current investigation handoff
- [`PYTORCH_CHECKPOINT_FIX.md`](PYTORCH_CHECKPOINT_FIX.md) - PyTorch 2.8 compatibility resolution
- [`FINAL_DIAGNOSIS_SUMMARY.md`](FINAL_DIAGNOSIS_SUMMARY.md) - Model quality investigation
- [`ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md`](ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md) - Metadata features implementation

### Historical & Research
- [`HISTORICAL_UPDATES.md`](HISTORICAL_UPDATES.md) - Session-by-session changelog
- [`research/RESEARCH_FINDINGS_CONSOLIDATED.md`](research/RESEARCH_FINDINGS_CONSOLIDATED.md) - ML research consolidation

### Complete File Inventory
See [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) for complete documentation map

---

## 🔧 Key Technical Specs

### Model Architecture
- **Base**: RoBERTa (biomedical domain-adapted)
- **Training**: 70/15/15 splits, AdamW optimizer, early stopping
- **Sequence Length**: 256 (classification), 512 (NER)
- **Batch Size**: 16 | Learning Rate: 1e-5 (classification), 5e-6 (NER)

### Performance
- **Training Time**: ~9.5 hours full production
- **Prediction Speed**: ~54 minutes for 21,677 papers
- **Memory**: ~8GB peak during training/inference
- **Storage**: ~1GB per training session

### Data Format
- **BIO Tagging**: O (outside), B-COM/I-COM (compound names), B-FUL/I-FUL (full names)
- **Input**: Title + abstract concatenation
- **Output**: CSV with predictions, probabilities, entities

---

## 🛡️ Best Practices

### Critical Rules

**DO**:
- ✅ Use V2 models for production (or Phase 4 once fixed)
- ✅ Run fresh pipelines without checkpoints
- ✅ Validate model performance before deployment
- ✅ Test cross-platform compatibility (local + Colab)
- ✅ Use dict-only checkpoint format
- ✅ Commit to git regularly (daily minimum)

**DON'T**:
- ❌ Use V1 models (PyTorch 2.8 incompatible)
- ❌ Use checkpoint systems in short pipelines (<1 hour)
- ❌ Deploy models without testing
- ❌ Use learning rate 2e-5 for NER (too high)
- ❌ Skip weight decay (causes overfitting)
- ❌ Include AI attribution in git commits

**Reference**: [`docs/LESSONS_LEARNED.md`](LESSONS_LEARNED.md) for complete best practices

---

## 📋 Document Maintenance

### When to Update This Document
- ✅ After major training runs or model updates
- ✅ When critical issues are discovered or resolved
- ✅ After significant code changes or new features
- ✅ When performance metrics change

### Update Process
1. Read current version before starting work
2. Update relevant sections as work progresses
3. Add new references to supporting documents
4. Update timestamp and status
5. Commit with clear message (no AI attribution)

### Git Workflow
- **Repository Root**: `GBC/inventory_2022/` (not GBC/)
- **Commit Frequency**: At least daily
- **Branch Strategy**: Create new branch for major work
- **Message Format**: Descriptive, no "Generated with Claude Code" or "Co-Authored-By: Claude"

### Planning Requirements
- ✅ Write detailed plans to `plans/` folder before major work
- ✅ Format: `YYYY-MM-DD_description_plan.md`
- ✅ Include timeline, requirements, success criteria

---

## 🎓 Training New Models

### Recommended Hyperparameters

**Classification**:
- Epochs: 10-15 | Batch: 16 | LR: 1e-5 | Weight Decay: 0.01 | Dropout: 0.2-0.3

**NER** (Small dataset - requires care):
- Epochs: 15-20 | Batch: 16 | LR: 5e-6 | Weight Decay: 0.01 | Dropout: 0.3

### Validation Checklist

Before deploying new models:
- [ ] NER test F1 > 0.70, Classification test F1 > 0.85
- [ ] Test matches validation F1 (±0.02)
- [ ] Training showed steady improvement
- [ ] Train/val gap < 0.15
- [ ] High-confidence predictions > 80%
- [ ] Baseline comparison > 75% overlap
- [ ] Cross-platform compatibility verified

**Complete Checklist**: [`docs/TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md)

---

## 🔍 Troubleshooting

### Common Issues

**Memory Overflow**:
- Phase 4 inference: See [`MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md)
- Solution: Use slim results storage + chunked merge

**PyTorch Compatibility**:
- V1 models fail in Colab: See [`PYTORCH_CHECKPOINT_FIX.md`](PYTORCH_CHECKPOINT_FIX.md)
- Solution: Use V2 models (dict format)

**Poor Training Quality**:
- Models perform below baseline: See [`FINAL_DIAGNOSIS_SUMMARY.md`](FINAL_DIAGNOSIS_SUMMARY.md)
- Solution: Check hyperparameters, use recommended values

**Data Integrity**:
- Mismatched row counts between steps: See [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md)
- Solution: Avoid checkpoints, validate each step

---

## 📞 System Status Summary

**Production Ready**: ✅ V2 models validated and operational

**Cutting Edge**: ✅ Phase 4 multi-task model trained (NER +23.82%)

**Blocking Issue**: 🚨 Phase 4 inference bug (288,730 vs 21,392 results)

**Next Milestone**: Fix Phase 4 inference bug → Deploy to production

**Infrastructure**: ✅ Complete (training, prediction, monitoring, archival, Drive sync)

**Documentation**: ✅ Comprehensive and current

---

**Document Location**: `GBC/inventory_2022/docs/starting_doc.md`
**Document Status**: ✅ Streamlined and current (~400 lines)
**Last Review**: 2025-10-31 (Added LLM testing & NER documentation)
**Next Review**: After Phase 4 inference bug resolution
**Maintained By**: AI agents working on biodata inventory pipeline

---

## Navigation to Supporting Documents

**Quick Access**:
- Operations → [`QUICK_REFERENCE_COMMANDS.md`](QUICK_REFERENCE_COMMANDS.md)
- Training → [`TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md)
- Best Practices → [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md)
- Phase 4 → [`multi_task_model/README.md`](multi_task_model/README.md)
- Pipelines → [`PIPELINE_GUIDES.md`](PIPELINE_GUIDES.md)
- History → [`HISTORICAL_UPDATES.md`](HISTORICAL_UPDATES.md)
- Current Issue → [`MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md)
- NER Guide → [`NER_explanation.md`](NER_explanation.md)
- LLM Testing → [`../data/llm_comparison/prompts/README.md`](../data/llm_comparison/prompts/README.md)
