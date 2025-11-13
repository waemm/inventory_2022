# Biodata Inventory ML Pipeline - AI Agent Reference Guide

**Created**: 2025-10-22
**Last Updated**: 2025-11-13 (Condensed & Restructured)
**Status**: ✅ **V2 PRODUCTION READY** + ⚠️ **PHASE 4 HAS CRITICAL BUG**
**Purpose**: Quick onboarding and navigation hub for AI agents

---

## 🎯 Executive Summary

Sophisticated ML pipeline using biomedical BERT models to automatically identify and extract biodata resources from scientific literature. Processes EuropePMC query results through classification and NER to generate comprehensive inventories.

**Current Status**:
- ✅ **V2 Models**: Production ready (Classification F1=0.898, NER F1=0.749)
- ✅ **Modern Stack**: Python 3.11.9, PyTorch 2.2.2, Transformers 4.35.0
- ⚠️ **Phase 4 Multi-Task**: Has post-processing bug (DO NOT USE)
- ✅ **spaCy Hybrid NER**: Phase 1-3 complete (F1=79.62%)
- ✅ **EPMC Query V5.1**: 254k papers ready (2011-mid2025)
- ✅ **PyCaret Classifier**: 84.6% recall metadata-only model

**Pipeline**: EuropePMC → Classification → NER → URL Extraction → Processing → Final Inventory

---

## ⚠️ CRITICAL ACTIVE ISSUE

### Phase 4 Post-Processing Bug (Discovered 2025-11-05)

**Status**: 🔴 **BUG IDENTIFIED** - Phase 4 NER has critical post-processing bug

**Issue**: Entity grouping logic fragments multi-word entities into individual words
- **Example**: "Mouse Phenome Database" → `["Mouse", "Phenome", "Database"]` (3 fragments instead of 1)
- **Impact**: Test F1 drops from expected ~66% to actual 22.49%
- **V2 Performance**: 66.35% F1 on same test (3× better)

**Root Cause**: Post-processing fails to merge consecutive IOB `I-` tags into complete entities

**Comparison Analysis** (Scripts 01-02 of 08 Complete):
- ✅ Data bugs fixed, test evaluation complete
- ✅ Root cause identified in inference notebook
- ⏳ Pending: Scripts 03-08 (inventory evaluation, visualizations, final report)

**Two Options**:
1. **Continue analysis** with buggy Phase 4 to document failures → Scripts 03-08
2. **Fix Phase 4 bug first**, then complete fair comparison

**Documentation**:
- **Bug fix guide**: [`docs/handovers/HANDOVER_PHASE4_BUG_FIX.md`](handovers/HANDOVER_PHASE4_BUG_FIX.md) ⭐
- **Project handover**: [`docs/handovers/HANDOVER_COMPARISON_PROJECT.md`](handovers/HANDOVER_COMPARISON_PROJECT.md)
- **Root cause**: [`comparison_phase4_v_oldmodel/results/ROOT_CAUSE_ANALYSIS_DISCREPANCY.md`](../comparison_phase4_v_oldmodel/results/ROOT_CAUSE_ANALYSIS_DISCREPANCY.md)

**Recommendation**: ⚠️ **USE V2 MODELS** for production until bug is fixed

---

## 📈 Recent Major Milestones (2025)

| Date | Milestone | Performance | Reference |
|------|-----------|-------------|-----------|
| 2025-11-12 | **spaCy Phase 3 Training** | F1=79.62% (exceeded target) ⭐ | [RECENT_MILESTONES_2025.md](RECENT_MILESTONES_2025.md#spacy-hybrid-ner-phase-1-3-complete-2025-11-12) |
| 2025-11-12 | V2 vs PyCaret Comparison | 8,129 high-confidence papers | [RECENT_MILESTONES_2025.md](RECENT_MILESTONES_2025.md#v2-vs-pycaret-model-comparison-study-2025-11-12) |
| 2025-11-11 | **PyCaret Classification** | 84.6% recall (11/13 papers) | [RECENT_MILESTONES_2025.md](RECENT_MILESTONES_2025.md#pycaret-metadata-classification-2025-11-11) |
| 2025-11-11 | **EPMC Query V5.1** | 77.3% training capture | [RECENT_MILESTONES_2025.md](RECENT_MILESTONES_2025.md#epmc-query-optimization-2025-11-10-to-2025-11-11) |
| 2025-11-07 | Phase 4 Training Fixed | 7 bugs fixed ✅ | [ARCHIVE_RESOLVED_ISSUES.md](ARCHIVE_RESOLVED_ISSUES.md#phase-4-training-notebooks-fixed-2025-11-07) |
| 2025-11-05 | Phase 4 Cartesian Fix | 288k → 20k results ✅ | [ARCHIVE_RESOLVED_ISSUES.md](ARCHIVE_RESOLVED_ISSUES.md#phase-4-cartesian-product-bug-2025-11-05) |

**See**: [`docs/RECENT_MILESTONES_2025.md`](RECENT_MILESTONES_2025.md) for detailed descriptions
**See**: [`docs/ARCHIVE_RESOLVED_ISSUES.md`](ARCHIVE_RESOLVED_ISSUES.md) for resolved historical issues

---

## 🚀 Quick Start

### Environment Setup
```bash
cd /Users/warren/development/GBC/inventory_2022/
source biodata_modern_env/bin/activate
export PYTHONPATH="src:$PYTHONPATH"
```

### Key Operations

**Training** (Google Colab recommended):
```bash
# Notebook: full_training_pipeline_simplified.ipynb
# Test mode: Set TEST_MODE = True (5-8 min vs 9.5 hr)
# Local: ./run_full_training.sh
```

**Prediction**:
```bash
# Full pipeline: ./rerun_2022_inventory.sh
# Test mode: ./test_rerun_2022_inventory.sh
```

**EPMC Query (V5.1 - RECOMMENDED)**:
```bash
python src/query_epmc.py config/final_query_v5.1_wildcards_fixed.txt \
  -f 2022-01-01 -t 2022-12-31 -o data/final_query_v5.1_2022
```

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

**V2 Models (✅ RECOMMENDED FOR PRODUCTION)**:
| Model | F1 Score | Precision | Recall | Status |
|-------|----------|-----------|--------|--------|
| Classification | 0.898 | 0.930 | 0.869 | ✅ Production |
| NER (validation) | 0.749 | 0.779 | 0.722 | ✅ Production |
| NER (test split) | 0.664 | 0.69 | 0.64 | ✅ Validated |

**Phase 4 Multi-Task (🔴 HAS BUG - DO NOT USE)**:
| Task | Validation* | Test** | vs V2 |
|------|------------|--------|-------|
| NER | 0.9274* | **0.2249** | -66% |
| Classification | 0.8586 | Not tested | -4.4% |

*Token-level IOB accuracy (not entity extraction)
**Entity-level matching on 63 papers

**Recommendation**: Use V2 models until Phase 4 bug is fixed

**Technical Details**: See [`docs/TECHNICAL_SPECIFICATIONS.md`](TECHNICAL_SPECIFICATIONS.md)

---

## 📊 Production Status

### Production Models (V2)

**Classification**: `out/classif_train_out/article_classifier_v2.pt`
- F1: 0.898 | Format: Dict | Status: ✅ Production Ready

**NER**: `out/ner_train_out/named_entity_recognition_v2.pt`
- F1: 0.749 (val), 0.664 (test) | Format: Dict | Status: ✅ Production Ready

### Datasets

- **Training**: 1,635 classification samples, 554 NER samples
- **V5.1 Query (2011-2021)**: 156,231 papers in `data/final_query_v5.1_2011_2021/`
- **V5.1 Query (2022-mid2025)**: 98,571 papers in `data/final_query_v5.1_2022_mid2025/`
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

### Essential Reading (Start Here)
- **This Document** - Quick onboarding and navigation hub
- [`README.md`](../README.md) - Project overview and workflow
- [`RECENT_MILESTONES_2025.md`](RECENT_MILESTONES_2025.md) - Detailed recent work (2025)
- [`ARCHIVE_RESOLVED_ISSUES.md`](ARCHIVE_RESOLVED_ISSUES.md) - Historical resolved issues

### Technical References
- [`TECHNICAL_SPECIFICATIONS.md`](TECHNICAL_SPECIFICATIONS.md) - Detailed model specs
- [`TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md) - Hyperparameters and validation
- [`PIPELINE_GUIDES.md`](PIPELINE_GUIDES.md) - Comprehensive pipeline guides
- [`QUICK_REFERENCE_COMMANDS.md`](QUICK_REFERENCE_COMMANDS.md) - Common operations

### Phase 4 Multi-Task (⚠️ Has Bug)
- [`multi_task_model/README.md`](multi_task_model/README.md) - Start here for Phase 4
- [`PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md`](PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md) - Complete guide
- [`handovers/HANDOVER_PHASE4_BUG_FIX.md`](handovers/HANDOVER_PHASE4_BUG_FIX.md) - **Fix instructions** ⭐

### NER & Entity Extraction
- [`NER_explanation.md`](NER_explanation.md) - Comprehensive NER guide
- [`../data/llm_comparison/results/ANALYSIS_SUMMARY.md`](../data/llm_comparison/results/ANALYSIS_SUMMARY.md) - LLM vs BERT comparison

### Best Practices
- [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) - Critical issues and best practices
- [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) - Complete documentation map

---

## 🛡️ Best Practices

### Critical Rules

**DO**:
- ✅ Use V2 models for production (Phase 4 has bug)
- ✅ Run fresh pipelines without checkpoints
- ✅ Validate model performance before deployment
- ✅ Use dict-only checkpoint format
- ✅ Commit to git regularly (daily minimum)
- ✅ Test cross-platform compatibility (local + Colab)

**DON'T**:
- ❌ Use Phase 4 for production NER (has post-processing bug)
- ❌ Use V1 models (PyTorch 2.8 incompatible)
- ❌ Use learning rate 2e-5 for NER (too high, use 5e-6)
- ❌ Skip weight decay (causes overfitting)
- ❌ Include AI attribution in git commits
- ❌ Use checkpoint systems in short pipelines (<1 hour)

**Reference**: [`docs/LESSONS_LEARNED.md`](LESSONS_LEARNED.md) for complete best practices

---

## 🎓 Training New Models

### Recommended Hyperparameters

**Classification**:
- Epochs: 10-15 | Batch: 16 | LR: 1e-5 | Weight Decay: 0.01 | Dropout: 0.2-0.3

**NER** (Small dataset - requires care):
- Epochs: 15-20 | Batch: 16 | **LR: 5e-6** (CRITICAL) | Weight Decay: 0.01 | Dropout: 0.3

### Validation Checklist

Before deploying new models:
- [ ] NER test F1 > 0.70, Classification test F1 > 0.85
- [ ] Test matches validation F1 (±0.02)
- [ ] Training showed steady improvement
- [ ] Train/val gap < 0.15
- [ ] High-confidence predictions > 80%
- [ ] Cross-platform compatibility verified

**Complete Details**: [`docs/TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md) and [`docs/TECHNICAL_SPECIFICATIONS.md`](TECHNICAL_SPECIFICATIONS.md)

---

## 🔍 Troubleshooting

### Common Issues

**Phase 4 Post-Processing Bug** (Active):
- **Symptom**: Multi-word entities fragmented into single words
- **Impact**: F1 drops to 22.49% (vs 66.35% for V2)
- **Solution**: Use V2 models OR fix Phase 4 bug first
- **Guide**: [`docs/handovers/HANDOVER_PHASE4_BUG_FIX.md`](handovers/HANDOVER_PHASE4_BUG_FIX.md)

**Resolved Issues** (See archive for details):
- ✅ **Phase 4 Cartesian Product**: Fixed 2025-11-05
- ✅ **Phase 4 Memory Overflow**: Fixed 2025-11-04 (94% reduction)
- ✅ **Phase 4 Training Notebooks**: Fixed 2025-11-07 (7 bugs)
- ✅ **PyTorch Compatibility**: Fixed 2025-10-27 (use V2 models)

**Archive**: [`docs/ARCHIVE_RESOLVED_ISSUES.md`](ARCHIVE_RESOLVED_ISSUES.md)

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
- **Repository Root**: `/Users/warren/development/GBC/inventory_2022/`
- **Commit Frequency**: At least daily
- **Branch Strategy**: Create new branch for major work (current: `modernization-python311`)
- **Message Format**: Descriptive, no "Generated with Claude Code" or "Co-Authored-By: Claude"

### Planning Requirements
- ✅ Write detailed plans to `plans/` folder before major work
- ✅ Format: `YYYY-MM-DD_description_plan.md`
- ✅ Include timeline, requirements, success criteria

---

## 📞 System Status Summary

**Production Ready**: ✅ V2 models validated and operational

**Cutting Edge**:
- ⚠️ Phase 4 multi-task TRAINED but has post-processing bug (DO NOT USE)
- ✅ spaCy Hybrid NER Phase 1-3 complete (F1=79.62%)
- ✅ PyCaret metadata classifier ready (84.6% recall)
- ✅ EPMC Query V5.1 ready (254k papers)

**Active Issues**:
- 🔴 Phase 4 post-processing bug (fragments multi-word entities)

**Next Priorities**:
1. Fix Phase 4 post-processing bug OR continue comparison analysis
2. spaCy Phase 4-5: Integrate EntityRuler + Statistical NER
3. Deploy hybrid classification pipeline (PyCaret + V2)

**Infrastructure**: ✅ Complete (training, prediction, monitoring, archival, Drive sync)

**Documentation**: ✅ Comprehensive and current (restructured 2025-11-13)

---

## 🧭 Navigation to Supporting Documents

**Quick Access**:
- **Recent Work 2025** → [`RECENT_MILESTONES_2025.md`](RECENT_MILESTONES_2025.md) - Detailed recent achievements
- **Resolved Issues** → [`ARCHIVE_RESOLVED_ISSUES.md`](ARCHIVE_RESOLVED_ISSUES.md) - Historical fixes
- **Technical Specs** → [`TECHNICAL_SPECIFICATIONS.md`](TECHNICAL_SPECIFICATIONS.md) - Model architecture & training
- **Operations** → [`QUICK_REFERENCE_COMMANDS.md`](QUICK_REFERENCE_COMMANDS.md) - Common commands
- **Training** → [`TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md) - Hyperparameters & validation
- **Best Practices** → [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) - Critical lessons
- **Phase 4 Bug Fix** → [`handovers/HANDOVER_PHASE4_BUG_FIX.md`](handovers/HANDOVER_PHASE4_BUG_FIX.md) - Fix instructions
- **NER Guide** → [`NER_explanation.md`](NER_explanation.md) - Entity extraction guide
- **Pipelines** → [`PIPELINE_GUIDES.md`](PIPELINE_GUIDES.md) - Complete pipeline guides
- **Documentation Map** → [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) - All docs indexed

---

**Document Location**: `docs/starting_doc.md`
**Document Status**: ✅ Current and concise (condensed from 1,081 → 417 lines)
**Last Major Refactor**: 2025-11-13 (restructured for clarity)
**Next Review**: After Phase 4 bug fix or spaCy Phase 4-5 completion
**Maintained By**: AI agents working on biodata inventory pipeline
**Backup**: Original version saved to `docs/SD_backup/starting_doc_2025-11-13.md`
