# Biodata Inventory ML Pipeline - AI Agent Reference Guide

**Created**: 2025-10-22
**Last Updated**: 2025-11-16 (spaCy tok2vec fix - Statistical NER now working!)
**Status**: ✅ **V2 PRODUCTION READY** + ⚠️ **PHASE 4 HAS CRITICAL BUG** + ✅ **SPACY FULL HYBRID READY**
**Purpose**: Quick onboarding and navigation hub for AI agents

---

## 🎯 Executive Summary

Sophisticated ML pipeline using biomedical BERT models to automatically identify and extract biodata resources from scientific literature. Processes EuropePMC query results through classification and NER to generate comprehensive inventories.

**Current Status**:
- ✅ **V2 Models**: Production ready (Classification F1=0.898, NER F1=0.749)
- ✅ **Modern Stack**: Python 3.11.9, PyTorch 2.2.2, Transformers 4.35.0
- ⚠️ **Phase 4 Multi-Task**: Has post-processing bug (DO NOT USE)
- ✅ **spaCy Full Hybrid NER**: tok2vec fix complete - **117k entities (3.1x improvement)**, 64% coverage ⭐
- ✅ **EPMC Query V5.1**: 254k papers ready (2011-mid2025)
- ✅ **PyCaret Classifier**: 84.6% recall metadata-only model

**🎊 USE SPACY FULL HYBRID FOR PRODUCTION NER** (model: `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful`)

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
| 2025-11-16 | **🎊 spaCy tok2vec Fix Complete** | **117k entities (3.1x), 64% coverage** - Statistical NER now contributes 67.7% of entities! ⭐ | [docs/SPACY_TOK2VEC_FIX_2025-11-16.md](SPACY_TOK2VEC_FIX_2025-11-16.md) + [docs/SPACY_3WAY_COMPARISON_2025-11-16.md](SPACY_3WAY_COMPARISON_2025-11-16.md) |
| 2025-11-15 | **spaCy Label Alignment Fix Complete** | Perfect alignment achieved (Index 0='COM', Index 1='FUL') ✅ | [plans/spacy_ner_hybrid_retraining/FIX_COMPLETION_SUMMARY.md](../plans/spacy_ner_hybrid_retraining/FIX_COMPLETION_SUMMARY.md) |
| 2025-11-15 | **spaCy Label Mismatch Investigation** | Statistical NER 0 entities (label incompatibility) 🔴 | [validation_spacy_v_BERT/SPACY_NER_LABEL_MISMATCH_INVESTIGATION.md](../validation_spacy_v_BERT/SPACY_NER_LABEL_MISMATCH_INVESTIGATION.md) |
| 2025-11-15 | **Phase 2 NER Complete** | 105k entities from 50k papers (spaCy: 38k, V2: 67k) ⭐ | [plans/validation_spacy_v_BERT/PROGRESS.md](../plans/validation_spacy_v_BERT/PROGRESS.md) |
| 2025-11-14 | **Google Drive NER Model Fix** | 341 → 694 entities (+103.5%, verified identical) ✅ | [validation_spacy_v_BERT/NER_FIX_VERIFICATION_COMPLETE.md](../validation_spacy_v_BERT/NER_FIX_VERIFICATION_COMPLETE.md) |
| 2025-11-14 | **Model Validation Study Complete** | PyCaret 98.65%, spaCy NER 76% recall ⭐ | [validation_spacy_v_BERT/](../validation_spacy_v_BERT/) |
| 2025-11-14 | **PyCaret Validation Bug Fix** | 0% → 94.6% positive (PMID merge fix) ✅ | [plans/2025-11-13-FINAL_ROOT_CAUSE.md](../plans/2025-11-13-FINAL_ROOT_CAUSE.md) |
| 2025-11-13 | **spaCy Phases 4-6 + Validation** | 91% precision, 48% recall (title-only) ⭐ | [spacy_hybrid_ner/MANUAL_VALIDATION_STUDY_REPORT.md](../spacy_hybrid_ner/MANUAL_VALIDATION_STUDY_REPORT.md) |
| 2025-11-12 | **spaCy Phase 3 Training** | F1=79.62% (exceeded target) ⭐ | [RECENT_MILESTONES_2025.md](RECENT_MILESTONES_2025.md#spacy-hybrid-ner-phase-1-3-complete-2025-11-12) |
| 2025-11-12 | V2 vs PyCaret Comparison | 8,129 high-confidence papers | [RECENT_MILESTONES_2025.md](RECENT_MILESTONES_2025.md#v2-vs-pycaret-model-comparison-study-2025-11-12) |
| 2025-11-11 | **PyCaret Classification** | 84.6% recall (11/13 papers) | [RECENT_MILESTONES_2025.md](RECENT_MILESTONES_2025.md#pycaret-metadata-classification-2025-11-11) |
| 2025-11-11 | **EPMC Query V5.1** | 77.3% training capture | [RECENT_MILESTONES_2025.md](RECENT_MILESTONES_2025.md#epmc-query-optimization-2025-11-10-to-2025-11-11) |
| 2025-11-07 | Phase 4 Training Fixed | 7 bugs fixed ✅ | [ARCHIVE_RESOLVED_ISSUES.md](ARCHIVE_RESOLVED_ISSUES.md#phase-4-training-notebooks-fixed-2025-11-07) |
| 2025-11-05 | Phase 4 Cartesian Fix | 288k → 20k results ✅ | [ARCHIVE_RESOLVED_ISSUES.md](ARCHIVE_RESOLVED_ISSUES.md#phase-4-cartesian-product-bug-2025-11-05) |

**See**: [`docs/RECENT_MILESTONES_2025.md`](RECENT_MILESTONES_2025.md) for detailed descriptions
**See**: [`docs/ARCHIVE_RESOLVED_ISSUES.md`](ARCHIVE_RESOLVED_ISSUES.md) for resolved historical issues

---

## 🔬 Model Validation Study (2025-11-14)

### Status: ✅ PHASE 1 COMPLETE - 148 Papers Validated

Comprehensive comparison of 5 models (3 classification + 2 NER) on 148 validation papers covering 125 unique biodata resources.

### Classification Results

**Models Compared:**
- V2 BERT Classifier (text-based: title+abstract)
- PyCaret TEST_MODE=True (metadata: 92 features)
- PyCaret TEST_MODE=False (metadata: 112 features)

**Key Findings:**
- **Agreement**: 94.6% consensus (140/148 papers)
- **PyCaret Winner**: 98.65% accuracy vs V2's 97.97%
- **PyCaret Strength**: 100% precision (zero false positives), perfect GCBR detection
- **V2 Strength**: Catches 2 emerging databases PyCaret misses (no citation bias)
- **Disagreements**: Only 8 papers (5.4%) - 6/8 resolved in PyCaret's favor

**Recommendation**: Use PyCaret as primary classifier with V2 as safety net for edge cases

### NER Results

**Models Compared:**
- V2 BERT NER (BioBERT-based, trained on title+abstract)
- spaCy Hybrid NER (EntityRuler + Statistical NER, 752 resources)

**Key Findings:**
- **spaCy Winner**: 76.0% recall vs V2's 69.6% (+6.4% advantage)
- **spaCy extracted**: 295 entities (100% with canonical IDs)
- **V2 extracted**: 270 entities (no canonical IDs)
- **Agreement**: 171 exact matches + 6 fuzzy (44.1% overlap)
- **spaCy Strength**: Higher recall, zero false positives, 100% canonical ID coverage
- **V2 Issues**: 35 fragmentation errors, 6 false positives (single chars), missed 118 major resources

**Recommendation**: Use spaCy Hybrid NER as primary (with postprocessing to trim 18 overly long entities)

### Google Drive NER Model Fix (2025-11-14)

**Issue Discovered**: Colab NER extracted only 341 entities vs 694 expected (50% fewer)

**Root Cause**: Wrong NER model file on Google Drive (MD5: `98f2355d...` vs correct `37eebc38...`)

**Fix Applied**:
- ✅ Backed up wrong model: `BACKUP_WRONG_named_entity_recognition_20251114.pt`
- ✅ Uploaded correct model (473 MB, verified MD5 match)
- ✅ Verified fix: New Colab run produced **identical** results to local (694 entities, mean prob 0.9415)

**Impact**:
- Entities: 341 → 694 (+103.5%)
- Mean probability: 0.69 → 0.94 (+36.4%)
- High confidence (≥0.9): 7.6% → 80.4% (+953%)

**Documentation**:
- Investigation: [`validation_spacy_v_BERT/MULTIPLE_COLAB_RUNS_ANALYSIS.md`](../validation_spacy_v_BERT/MULTIPLE_COLAB_RUNS_ANALYSIS.md)
- Fix Summary: [`validation_spacy_v_BERT/NER_MODEL_FIX_COMPLETE.md`](../validation_spacy_v_BERT/NER_MODEL_FIX_COMPLETE.md)
- Verification: [`validation_spacy_v_BERT/NER_FIX_VERIFICATION_COMPLETE.md`](../validation_spacy_v_BERT/NER_FIX_VERIFICATION_COMPLETE.md)
- Quick Start: [`validation_spacy_v_BERT/COLAB_NER_FIX_QUICK_START.md`](../validation_spacy_v_BERT/COLAB_NER_FIX_QUICK_START.md)

**Status**: ✅ VERIFIED COMPLETE - Colab now produces identical results to local

### Detailed Documentation

**Classification Analysis:**
- Quick Reference: [`validation_spacy_v_BERT/DISAGREEMENT_QUICK_REFERENCE.md`](../validation_spacy_v_BERT/DISAGREEMENT_QUICK_REFERENCE.md)
- Full Report: [`validation_spacy_v_BERT/DISAGREEMENT_ANALYSIS_REPORT.md`](../validation_spacy_v_BERT/DISAGREEMENT_ANALYSIS_REPORT.md)
- Summary Table: [`validation_spacy_v_BERT/disagreement_cases_summary.csv`](../validation_spacy_v_BERT/disagreement_cases_summary.csv)

**NER Analysis:**
- Key Findings: [`validation_spacy_v_BERT/results/validation/ner/KEY_FINDINGS.txt`](../validation_spacy_v_BERT/results/validation/ner/KEY_FINDINGS.txt)
- Summary: [`validation_spacy_v_BERT/results/validation/ner/NER_ANALYSIS_SUMMARY.md`](../validation_spacy_v_BERT/results/validation/ner/NER_ANALYSIS_SUMMARY.md)
- Full Report: [`validation_spacy_v_BERT/results/validation/ner/NER_COMPARISON_REPORT_2025-11-13-iwsisa.md`](../validation_spacy_v_BERT/results/validation/ner/NER_COMPARISON_REPORT_2025-11-13-iwsisa.md)

**Phase 1 Overview:**
- Executive Report: [`validation_spacy_v_BERT/results/validation/PHASE1_VALIDATION_REPORT_2025-11-13-iwsisa.md`](../validation_spacy_v_BERT/results/validation/PHASE1_VALIDATION_REPORT_2025-11-13-iwsisa.md)
- Progress Tracking: [`plans/validation_spacy_v_BERT/PROGRESS.md`](../plans/validation_spacy_v_BERT/PROGRESS.md)
- Critical Files: [`validation_spacy_v_BERT/CRITICAL_FILES_REFERENCE.md`](../validation_spacy_v_BERT/CRITICAL_FILES_REFERENCE.md)

**Production Recommendation**:
- Classification: PyCaret (98.65% accuracy) + V2 safety net
- NER: spaCy Hybrid (76% recall, 100% canonical IDs) + optional V2 supplement for maximum recall

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

## 🧬 spaCy Hybrid NER System (Phases 1-6)

### Status: ✅ PRODUCTION READY - Code Quality 9.5/10

**Complete Implementation** (2025-11-12 to 2025-11-13):
- ✅ **Phase 1-3**: Training & validation complete (F1=79.62%, exceeded target by 14.6pp)
- ✅ **Phase 4-6**: EntityRuler integration + production API + optimization (100-200 papers/sec)
- ✅ **Code Review**: All critical fixes implemented and optimized

### Architecture

**Hybrid Two-Stage Pipeline**:
```
Papers → EntityRuler (rule-based) → Statistical NER (ML-based) → Merged Results
         [Exact matches]              [Contextual extraction]      [Alias resolution]
```

**Key Innovation**: EntityRuler precedes Statistical NER in pipeline to ensure:
1. Exact database name matches from catalog (high precision)
2. Contextual extraction for variations (high recall)
3. Alias resolution to canonical IDs (e.g., "PDB" ↔ "Protein Data Bank")

### Performance Metrics

**Phase 3 Statistical NER**:
- Test F1: **79.62%** (target: 65%, exceeded by 14.6pp)
- Speed: 14 papers/sec (single processing)

**Phase 4-6 Hybrid System (After Optimization)**:
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Speed | 43 p/s | **100-200 p/s** | 2-5× faster ⚡ |
| Code Quality | 8.1/10 | **9.5/10** | +17% |
| Processing Method | Sequential | Batch (`.pipe()`) | Optimized |
| Resource Utilization | Wastes CPU on invalid texts | Skips invalid texts | Efficient |

**EntityRuler Baseline**:
- Speed: ~64 p/s → 150-200 p/s (with batching)
- Precision: High (exact matches)
- Coverage: 5,000+ bioresource patterns

### Code Quality & Optimizations (2025-11-13)

**Original Code Review Score**: 8.1/10 - Production ready with improvements needed

**Critical Fixes Implemented**:
1. **CRITICAL-01**: Division by zero handling → Returns `float('inf')` for data quality signals
2. **HIGH-01**: Batch processing → 2-5× speedup using spaCy's `.pipe()` method
3. **HIGH-02**: Robust pipeline validation → Catches missing/duplicate components

**Optimizations Applied**:
- ✅ Batch size validation (raises error on invalid, warns on large values)
- ✅ Skip invalid texts before NLP processing (efficiency gain)
- ✅ Enhanced error messages with full context
- ✅ Improved logging and progress tracking

**Final Score**: **9.5/10** - Fully optimized and production-ready ⭐

### Production API

**Location**: `src/ner_predict_spacy.py`

**Usage Example**:
```python
from src.ner_predict_spacy import SpacyNERPredictor

# Initialize predictor (auto-loads model and validates pipeline)
predictor = SpacyNERPredictor(
    model_path="spacy_hybrid_ner/models/phase3_statistical_model"
)

# Predict on papers (batch processing with default batch_size=32)
results = predictor.predict(papers_df, batch_size=32)

# Or save directly to CSV
predictor.predict_to_csv(
    papers_df,
    output_path="results/ner_results.csv",
    batch_size=64  # Adjust for your hardware
)
```

**Features**:
- ✅ Automatic pipeline validation (EntityRuler → NER order enforcement)
- ✅ Batch processing for 2-5× speedup
- ✅ Alias resolution (merges mentions to canonical IDs)
- ✅ Flexible text extraction (title+abstract or custom column)
- ✅ Comprehensive error handling and validation

### Quick Start Commands

**Run Validation Scripts** (Phases 4-6):
```bash
cd spacy_hybrid_ner/scripts/

# Phase 4: Validate EntityRuler baseline
python 08_validate_entityruler_baseline.py

# Phase 5: Validate hybrid integration
python 10_validate_hybrid_integration.py

# Phase 6: Benchmark speed & end-to-end validation
python 11_benchmark_hybrid_speed.py
python 12_validate_end_to_end.py
```

**Expected Results**:
- EntityRuler: 100% precision on catalog matches
- Hybrid: Balanced precision/recall with alias resolution
- Speed: 100-200 papers/sec (optimized batch processing)

### Documentation References

**Complete Guides**:
- **Completion Report**: [`spacy_hybrid_ner/PHASE4_5_6_COMPLETE.md`](../spacy_hybrid_ner/PHASE4_5_6_COMPLETE.md) - Full implementation details
- **Code Review**: [`spacy_hybrid_ner/CODE_REVIEW_FINDINGS.md`](../spacy_hybrid_ner/CODE_REVIEW_FINDINGS.md) - Original findings + status
- **Fixes Summary**: [`spacy_hybrid_ner/FIXES_IMPLEMENTATION_SUMMARY.md`](../spacy_hybrid_ner/FIXES_IMPLEMENTATION_SUMMARY.md) - All optimizations
- **Progress Tracker**: [`plans/spacy_hybrid_ner/PROGRESS_TRACKER.md`](../plans/spacy_hybrid_ner/PROGRESS_TRACKER.md) - Phase-by-phase tracking

**Phase-Specific Docs**:
- Phase 1-3: Training, validation, optimization results
- Phase 4: EntityRuler baseline validation (script 08)
- Phase 5: Hybrid integration validation (scripts 10)
- Phase 6: Speed benchmarking + end-to-end testing (scripts 11-12)

### Commits & History

**Key Commits**:
- `967b665`: Phase 3 training complete (F1=79.62%)
- `2ff9ec7`: Phases 4-6 complete implementation
- `15ad8e4`: Critical fixes (division by zero, batch processing, validation)
- `2ebb514`: Production optimizations (batch validation, efficiency gains)

### Testing & Validation

**All Fixes Tested** ✅:
- Division by zero edge cases
- Batch processing with various batch sizes (1, 8, 32, 64)
- Pipeline validation (correct, missing, duplicate, wrong order)
- Mixed valid/invalid texts
- Empty DataFrame handling
- Batch size validation (negative, zero, large values)

**Production Readiness Checklist**: ✅ Complete
- [x] All critical fixes implemented
- [x] Code review feedback addressed
- [x] Comprehensive testing completed
- [x] Performance validated (2-5× speedup)
- [x] Documentation complete

### Recommendations

**For Production Use**:
1. Start with `batch_size=32` (balanced performance/memory)
2. Increase to 64-128 if you have high memory (8GB+ RAM)
3. Reduce to 8-16 for memory-constrained environments
4. Monitor for batch_size > 1000 warning (may cause OOM)

**Future Enhancements** (Optional):
- Unit tests with pytest framework
- Text length limits (MAX_TEXT_LENGTH=100K)
- Progress bar with tqdm (better UX)
- Multi-run benchmarks for speed validation

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
- ✅ **spaCy Hybrid NER Phases 1-6 COMPLETE** (F1=79.62%, 100-200 p/s, Code: 9.5/10) ⭐
- ✅ PyCaret metadata classifier ready (84.6% recall)
- ✅ EPMC Query V5.1 ready (254k papers)

**Active Issues**:
- 🔴 Phase 4 multi-task post-processing bug (fragments multi-word entities)

**Next Priorities**:
1. Fix Phase 4 multi-task post-processing bug OR continue comparison analysis
2. Deploy spaCy Hybrid NER for production inventory generation
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
- **spaCy Hybrid NER** → [`../spacy_hybrid_ner/PHASE4_5_6_COMPLETE.md`](../spacy_hybrid_ner/PHASE4_5_6_COMPLETE.md) - Complete Phases 1-6 ⭐
- **spaCy Code Review** → [`../spacy_hybrid_ner/FIXES_IMPLEMENTATION_SUMMARY.md`](../spacy_hybrid_ner/FIXES_IMPLEMENTATION_SUMMARY.md) - Optimizations
- **Phase 4 Bug Fix** → [`handovers/HANDOVER_PHASE4_BUG_FIX.md`](handovers/HANDOVER_PHASE4_BUG_FIX.md) - Fix instructions
- **NER Guide** → [`NER_explanation.md`](NER_explanation.md) - Entity extraction guide
- **Pipelines** → [`PIPELINE_GUIDES.md`](PIPELINE_GUIDES.md) - Complete pipeline guides
- **Documentation Map** → [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) - All docs indexed

---

**Document Location**: `docs/starting_doc.md`
**Document Status**: ✅ Current and comprehensive (includes spaCy Hybrid NER Phases 1-6)
**Last Major Update**: 2025-11-13 (added spaCy Hybrid NER complete section)
**Last Major Refactor**: 2025-11-13 (restructured for clarity)
**Next Review**: After Phase 4 multi-task bug fix
**Maintained By**: AI agents working on biodata inventory pipeline
**Backup**: Original version saved to `docs/SD_backup/starting_doc_2025-11-13.md`
