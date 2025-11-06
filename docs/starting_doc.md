# Biodata Inventory ML Pipeline - AI Agent Reference Guide

**Created**: 2025-10-22
**Last Updated**: 2025-11-06 (Phase 4 vs V2 comparison analysis - critical bug identified)
**Status**: ⚠️ **V2 PRODUCTION READY** + 🔴 **PHASE 4 HAS POST-PROCESSING BUG** (NER entity grouping broken)
**Purpose**: High-level reference and navigation hub for AI agents

---

## 🎯 Executive Summary

Sophisticated ML pipeline using biomedical BERT models to automatically identify and extract biodata resources from scientific literature. Processes EuropePMC query results through classification and NER to generate comprehensive inventories.

### Current Status
- ✅ **Production Ready**: V2 models validated (Classification F1=0.898, NER F1=0.749)
- ✅ **Modern Stack**: Python 3.11.9, PyTorch 2.2.2, Transformers 4.35.0
- ✅ **Phase 4 Multi-Task Model**: NER F1=0.9274 (+23.82% improvement), PRODUCTION READY
- ✅ **Phase 4 Inference**: Cartesian product bug FIXED and VERIFIED (288,736 → 20,896 results)

### Key Architecture
- **Two Systems Available**:
  1. **V2 Models** (Traditional): Separate classification + NER models
  2. **Phase 4 Multi-Task** (Recommended): Single unified model with metadata integration
- **Base Model**: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500` (biomedical RoBERTa)
- **Pipeline**: EuropePMC → Classification → NER → URL Extraction → Processing → Final Inventory

---

## ✅ Recently Resolved Issues

### Phase 4 Cartesian Product Bug (2025-11-05)

**Status**: ✅ FIXED AND VERIFIED (Multiple Sessions)

**Issues Resolved**:
1. **Memory Overflow** (✅ FIXED - 2025-11-04):
   - Reduced from 160GB+ → <10GB (94% reduction)
   - Implemented slim results storage + chunked merge

2. **Cartesian Product Bug** (✅ FIXED - 2025-11-05):
   - Expected: ~20,890 results
   - Was producing: 288,736 results (13.8× multiplication)
   - Root cause: Converting NaN to string 'nan' BEFORE merge caused pandas to match all 'nan' strings
   - Fix: Filter NaN IDs FIRST using `.notna()`, THEN convert to string
   - Verification: Sessions 1f3ixn & f649n1 both produce 20,896 results ✅

**Impact**: ✅ Phase 4 model is now PRODUCTION READY and VERIFIED for inference

**Details**:
- **Comprehensive bug fix**: [`docs/PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md`](PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md) ⭐ **READ THIS**
- Memory optimization: [`docs/MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md)
- Initial investigation: [`docs/PHASE4_INFERENCE_FIX_2025-11-04.md`](PHASE4_INFERENCE_FIX_2025-11-04.md)

---

## ⚠️ Critical Discovery: Phase 4 Post-Processing Bug (2025-11-05)

**Status**: 🔴 **BUG IDENTIFIED** - Phase 4 NER has critical post-processing bug

**Issue**: Phase 4's entity grouping logic fragments multi-word entities into individual words
- **Example**: "Mouse Phenome Database" → `["Mouse", "Phenome", "Database"]` (3 fragments instead of 1 entity)
- **Impact**: Test split F1 drops from expected ~66% to actual 22.49%
- **V2 Performance**: 66.35% F1 on same test split (3× better)

**Root Cause**: Post-processing fails to merge consecutive IOB `I-` tags into complete multi-word entities

**Comparison Analysis** (Scripts 01-02 of 08 Complete):
- ✅ **Data bugs fixed** (6 critical bugs: ID mismatch, JSON serialization, NaN handling, etc.)
- ✅ **Test evaluation complete**: 63 papers with ground truth, statistically significant difference (p < 0.0001)
- ✅ **Root cause identified**: Entity grouping bug in Phase 4 inference notebook
- ⏳ **Pending**: Scripts 03-08 (inventory evaluation, BPE analysis, visualizations, final report)

**Two Options**:
1. **Continue analysis** with current (buggy) Phase 4 to document failures → Scripts 03-08
2. **Fix Phase 4 bug first**, then complete fair comparison

**Documentation**:
- **Project handover**: [`docs/handovers/HANDOVER_COMPARISON_PROJECT.md`](handovers/HANDOVER_COMPARISON_PROJECT.md) ⭐ **Complete context for continuing**
- **Bug fix guide**: [`docs/handovers/HANDOVER_PHASE4_BUG_FIX.md`](handovers/HANDOVER_PHASE4_BUG_FIX.md) ⭐ **Step-by-step fix instructions**
- **Comparison plan**: [`plans/2025-11-05_phase4_vs_v2_ner_comparison.md`](../plans/2025-11-05_phase4_vs_v2_ner_comparison.md)
- **Code review**: [`comparison_phase4_v_oldmodel/results/ROOT_CAUSE_ANALYSIS_DISCREPANCY.md`](../comparison_phase4_v_oldmodel/results/ROOT_CAUSE_ANALYSIS_DISCREPANCY.md)

**Project Location**: `comparison_phase4_v_oldmodel/` (scripts, data, results)

**Recommendation**: ⚠️ **DO NOT use Phase 4 for production NER** until post-processing bug is fixed

---

## 📈 Recent Major Milestones

| Date | Milestone | Status | Performance | Reference |
|------|-----------|--------|-------------|-----------|
| 2025-11-06 | Phase 4 vs V2 Comparison (Scripts 01-02) | 🔴 Bug Found | Phase 4: 22.49% vs V2: 66.35% | [handovers/HANDOVER_COMPARISON_PROJECT.md](handovers/HANDOVER_COMPARISON_PROJECT.md) |
| 2025-11-05 | Phase 4 Cartesian Product Fix | ✅ Verified | 288,736 → 20,896 results | [PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md](PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md) |
| 2025-11-04 | Phase 4 Memory Optimization | ✅ Done | Memory: 94% reduction | [MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md) |
| 2025-10-31 | Phase 4 Multi-Task Complete | ⚠️ Has Bug | NER F1: 0.9274* (validation) | [multi_task_model/README.md](multi_task_model/README.md) |
| 2025-10-30 | Enhanced Metadata Features | ✅ Done | 21,392 papers × 38 features | [ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md](ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md) |
| 2025-10-29 | Training Infrastructure | ✅ Done | Experimental pipeline ready | [EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md](EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md) |
| 2025-10-27 | PyTorch Compatibility | ✅ Resolved | Cross-platform models | [PYTORCH_CHECKPOINT_FIX.md](PYTORCH_CHECKPOINT_FIX.md) |

*Note: 0.9274 F1 was validation metric (token-level). Independent test evaluation shows 0.2249 F1 (entity-level) due to post-processing bug.

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

**V2 Models (Traditional Two-Model System)** - ✅ **RECOMMENDED FOR PRODUCTION**:
| Model | F1 Score | Precision | Recall | Test Split Performance | Status |
|-------|----------|-----------|--------|------------------------|--------|
| Classification | 0.898 | 0.930 | 0.869 | N/A | ✅ Production |
| NER | 0.749 | 0.779 | 0.722 | **0.6635** (entity-level) | ✅ Production |

**Phase 4 Multi-Task Model** - 🔴 **HAS POST-PROCESSING BUG**:
| Task | Validation F1* | Test F1** | vs V2 | Status |
|------|---------------|-----------|-------|--------|
| NER | 0.9274* (token-level) | **0.2249** (entity-level) | **-66% vs V2** | 🔴 BROKEN |
| Classification | 0.8586 | Not tested | -4.38% | ⚠️ Unknown |

*Validation metrics from training (token-level IOB accuracy, not entity extraction)
**Independent test evaluation on 63 papers with ground truth (entity-level matching)

**Issue**: Post-processing bug fragments multi-word entities (e.g., "Mouse Phenome Database" → ["Mouse", "Phenome", "Database"])

**Recommendation**: ⚠️ **USE V2 MODELS** until Phase 4 post-processing bug is fixed
- See: [`docs/handovers/HANDOVER_PHASE4_BUG_FIX.md`](handovers/HANDOVER_PHASE4_BUG_FIX.md) for fix instructions

---

## 📊 Production Status

### Production Models (V2 - ✅ RECOMMENDED)

**Classification**: `out/classif_train_out/article_classifier_v2.pt`
- F1: 0.898 | Status: ✅ Validated & Production Ready | Format: Dict (PyTorch 2.8 compatible)

**NER**: `out/ner_train_out/named_entity_recognition_v2.pt`
- F1: 0.749 (validation), 0.6635 (test split) | Status: ✅ Validated & Production Ready | Format: Dict (PyTorch 2.8 compatible)

### Phase 4 Multi-Task Model (🔴 NOT READY - HAS BUG)

**Location**: `collab_results/experiment_archives/2025-10-31-rq7i4n/multitask_training/`

**Checkpoint**: `checkpoint_best_ner.pt` (Validation F1: 0.9274, Test F1: 0.2249)

**Status**: 🔴 **DO NOT USE FOR PRODUCTION**
- Post-processing bug fragments multi-word entities
- Test performance 3× worse than V2 (22.49% vs 66.35%)
- Fix required before deployment
- See: [`docs/handovers/HANDOVER_PHASE4_BUG_FIX.md`](handovers/HANDOVER_PHASE4_BUG_FIX.md)

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
- [`PHASE4_NER_POST_PROCESSING_COMPLETE.md`](PHASE4_NER_POST_PROCESSING_COMPLETE.md) - **NEW:** NER post-processing (BPE fix + deduplication) ✅ PRODUCTION READY
- [`multi_task_model/PHASE4_VS_V2_COMPARISON.md`](multi_task_model/PHASE4_VS_V2_COMPARISON.md) - Why NER improved 23.8%

### Critical Issues & Fixes
- [`PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md`](PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md) - **⭐ MUST READ:** Cartesian product bug (2025-11-05) ✅ VERIFIED
- [`PHASE4_NER_POST_PROCESSING_COMPLETE.md`](PHASE4_NER_POST_PROCESSING_COMPLETE.md) - NER post-processing complete (2025-11-05) ✅
- [`MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md) - Memory overflow fix (2025-11-04) ✅
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

**Cartesian Product Bug** (Phase 4 Inference):
- Root cause: Converting NaN to string BEFORE merge
- Solution: Filter NaN FIRST, THEN convert to string
- Documentation: [`PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md`](PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md)

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

**Cutting Edge**: ✅ Phase 4 multi-task model VERIFIED (NER +23.82%, Combined F1 +8.28%)

**Latest Fix**: ✅ Cartesian product bug fixed and verified (sessions 1f3ixn & f649n1)

**Next Milestone**: Deploy Phase 4 model to production → Full 2022 dataset validation

**Infrastructure**: ✅ Complete (training, prediction, monitoring, archival, Drive sync)

**Documentation**: ✅ Comprehensive and current

---

**Document Location**: `GBC/inventory_2022/docs/starting_doc.md`
**Document Status**: ✅ Streamlined and current (~410 lines)
**Last Review**: 2025-11-05 (Phase 4 cartesian product bug fix verified)
**Next Review**: After full 2022 dataset validation with Phase 4
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
- **⭐ Latest Fix** → [`PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md`](PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md)
- NER Post-Processing → [`PHASE4_NER_POST_PROCESSING_COMPLETE.md`](PHASE4_NER_POST_PROCESSING_COMPLETE.md)
- Memory Optimization → [`MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md)
- NER Guide → [`NER_explanation.md`](NER_explanation.md)
- LLM Testing → [`../data/llm_comparison/prompts/README.md`](../data/llm_comparison/prompts/README.md)
