# Biodata Inventory ML Pipeline - AI Agent Reference Guide

**Created**: 2025-10-22
**Last Updated**: 2025-11-12 (spaCy Hybrid NER implementation plan approved)
**Status**: ✅ **V2 PRODUCTION READY** + ✅ **PHASE 4 TRAINING NOTEBOOKS READY** + ✅ **PYCARET METADATA CLASSIFIER READY** + 📋 **SPACY HYBRID NER READY FOR IMPLEMENTATION**
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

### Phase 4 Training Notebooks Fixed (2025-11-07)

**Status**: ✅ PRODUCTION READY - All training bugs fixed, A100 optimized

**Issues Resolved**:
1. **7 Critical Training Errors Fixed** (Errors #1-7):
   - ✅ Syntax errors, missing modules, data source mismatches
   - ✅ Pickle structure handling, JSON serialization
   - ✅ Nested list handling in metrics (3 functions)
   - ✅ AttributeError: `best_ner_f1` → `best_entity_f1`

2. **A100 GPU Optimizations Implemented**:
   - ✅ Parallel data loading (8 workers, persistent) - 25-40% speedup
   - ✅ Aggressive batch scaling (batch 128, LR 8e-5) - 100-150% speedup
   - ✅ Auto-detection with T4/V100 fallback

3. **Agent Network Verification**:
   - ✅ Explore Agent: Investigated trainer attributes
   - ✅ Code-Developer Agent: Fixed 26 attribute references
   - ✅ Code-Reviewer Agent: 100% verification (41 references checked)

**Training Results** (Test run 2025-11-06):
- Duration: 27.7 minutes on A100 (aggressive batch scaling)
- Classification F1: 0.8513 ✅
- NER Entity F1: Saved in checkpoint (display crashed before fix)

**Two Optimized Notebooks Available**:
1. **phase4_multitask_training_FIXED.ipynb** (✅ uploaded to Drive)
   - Aggressive batch scaling: ~30-45 min on A100
   - High speedup, moderate risk (potential OOM)

2. **phase4_multitask_training_FIXED_A100opti.ipynb** (ready for upload)
   - Parallel data loading: ~1.0-1.2 hours on A100
   - Safe optimization, low risk

**Impact**: Phase 4 training pipeline is now fully functional and ready for production training runs

**Comprehensive Documentation**:
- **⭐ Complete Implementation Guide**: [`docs/PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md`](PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md) - **Read this to get up to speed**
- **Attribute error fix**: [`ATTRIBUTE_ERROR_FIX_COMPLETE.md`](../ATTRIBUTE_ERROR_FIX_COMPLETE.md)
- **A100 optimizations**: [`A100_QUICK_START.md`](../A100_QUICK_START.md), [`A100_OPTIMIZATIONS_SUMMARY.md`](../A100_OPTIMIZATIONS_SUMMARY.md)
- **Bug fix history**: [`NOTEBOOK_FIX_ERROR6_COMPLETE.md`](../NOTEBOOK_FIX_ERROR6_COMPLETE.md)

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

## 🔍 EPMC Query Optimization (2025-11-10 to 2025-11-11)

**Status**: ✅ **V5.1 PRODUCTION READY** - Dual optimization complete

**Achievements**:
1. **V4 Query** (2025-11-10): Manual paper capture 0% → 92.3% (12/13 papers)
2. **V5.1 Query** (2025-11-11): Training positive capture 0% → 77.3% (34/44 papers), includes Ensembl, PANTHER

### Key Findings

**Inventory Characteristics** (vs 21,392 background papers):
- **Citation Impact**: 1.66x higher (163.5 vs 98.3 mean citations, p < 0.001)
- **Open Access**: 1.37x enrichment (75.8% vs 55.2%)
- **Journal Concentration**: 36.7% from Nucleic Acids Research alone
- **MeSH Terms**: 50.1% have database-related MeSH (3-4x enrichment)
- **Publication Type**: "Dataset" type 3.88x enriched

### Query Evolution

| Version | Papers (2011-2021) | Manual Add Capture | Training Positives | Status |
|---------|-------------------|-------------------|-------------------|---------|
| **Original** | 21,677 | 0/13 (0%) | 0/44 (0%) | Baseline |
| **Balanced v3** | 52,008 | 7/13 (53.8%) | N/A | Improved |
| **V4** | 123,497 | 12/13 (92.3%) | 0/44 (0%) | Production |
| **V5.1** ⭐ | **156,231** | **13/13 (100%)** | **34/44 (77.3%)** | **RECOMMENDED** |

### Root Cause Analysis

Systematic component-by-component testing revealed **3 missing title keywords** caused 5 missed papers:
1. **"resource"** - Excluded: ClinGen, Bio-Analytic Resource, Cellosaurus
2. **"knowledgebase"** (one word) - Excluded: CIViC knowledgebase
3. **"dataset"** - Excluded: Molecular interactions dataset

**MeSH Limitation Discovered**: MeSH terms exist in paper metadata but are NOT searchable via `MESH:"term"` queries for ~50% of papers (post-publication indexing delay).

### V4 Query (Manual Paper Optimization)

**Location**: `config/final_query_v4_improved.txt`

**Components**:
- MeSH terms (37% coverage, high precision)
- Title keywords (HIGH RECALL) - **Added: resource, knowledgebase, dataset**
- Abstract with URL requirement

**Results**:
- 2011-2021: 123,497 papers (5.7x original)
- Manual capture: 92.3% (12/13)
- Training positives: 0/44 (0%) - revealed need for V5

### V5.1 Query (Training Data Optimization) ⭐ RECOMMENDED

**Location**: `config/final_query_v5.1_wildcards_fixed.txt`

**Key Improvements over V4**:
- **Expanded abstract clause**: Added `resource*`, `collection*`, `catalog*` (with wildcards!)
- **Expanded title keywords**: Added `toolkit`, `toolbox`, `browser`, `annotation`, `collection*`
- **Critical wildcard fix**: `resource*` (not `resource`) matches "resources" plural

**Results** (2011-2021):
- Papers: 156,231 (26.5% increase over V4)
- Manual capture: 13/13 (100%)
- Training positives: 34/44 (77.3%) - includes Ensembl 2012/2021, PANTHER v16, OMIM, IDEAL
- Wildcard fix: Captured 4 additional papers with plural forms

**Critical Discovery**: EPMC does NOT auto-stem! Must use wildcards (`resource*` not `resource`) to match plural forms.

### Unsearchable Papers

**1 paper requires manual merge**: PMID 24727771 (ProteomeXchange 2014)
- Generic title with no identifying keywords
- No searchable MeSH database terms
- File: `data/unsearchable_papers_manual_add.csv`

### Implementation Commands

**V5.1 Test (2011-2021)**:
```bash
python src/query_epmc.py config/final_query_v5.1_wildcards_fixed.txt \
  -f 2011-01-01 -t 2021-12-31 -o data/final_query_v5.1_2011_2021
```

**V5.1 Production (2022)** ⭐ RECOMMENDED:
```bash
python src/query_epmc.py config/final_query_v5.1_wildcards_fixed.txt \
  -f 2022-01-01 -t 2022-12-31 -o data/final_query_v5.1_2022
```

**V4 Production (2022)** (Alternative if V5.1 precision issues):
```bash
python src/query_epmc.py config/final_query_v4_improved.txt \
  -f 2022-01-01 -t 2022-12-31 -o data/final_query_v4_2022
```

**Merge unsearchable papers** (see final report for Python code)

### Comprehensive Documentation

**⭐ V5.1 Complete Report**: [`docs/EPMC_QUERY_V5_OPTIMIZATION.md`](EPMC_QUERY_V5_OPTIMIZATION.md) - **READ THIS FIRST**

**V4 Documentation**:
- V4 Final Report: [`analysis_output/EPMC_QUERY_OPTIMIZATION_FINAL_REPORT.md`](../analysis_output/EPMC_QUERY_OPTIMIZATION_FINAL_REPORT.md)
- Extended statistical analysis: [`analysis_output/inventory_epmc_attributes_extended_report.md`](../analysis_output/inventory_epmc_attributes_extended_report.md)
- Root cause diagnosis: [`analysis_output/MISSED_PAPERS_ROOT_CAUSE_ANALYSIS.md`](../analysis_output/MISSED_PAPERS_ROOT_CAUSE_ANALYSIS.md)

**V5/V5.1 Documentation**:
- Missing positives analysis: [`MISSING_44_POSITIVES_ANALYSIS.md`](../MISSING_44_POSITIVES_ANALYSIS.md)
- V5 changes: [`V5_QUERY_CHANGES.md`](../V5_QUERY_CHANGES.md)
- V5.1 wildcard fix: [`V5.1_WILDCARD_FIX.md`](../V5.1_WILDCARD_FIX.md)

**Implementation Plans**:
- V4 plan: [`plans/2025-11-10_inventory_epmc_attributes_analysis.md`](../plans/2025-11-10_inventory_epmc_attributes_analysis.md)

**Test Scripts & Data**:
- `test_query_count.py` - Test query without downloading
- `test_manual_add_capture.py` - Validate capture rate
- `diagnose_missed_papers.py` - Systematic diagnosis tool
- `analyze_inventory_epmc_attributes_extended.py` - Full analysis (569 lines)
- `missing_positive_papers.csv` - 44 training positives for validation (66KB)

### Maintenance Recommendations

- **Quarterly review**: Sample precision, check for new terminology, validate edge cases
- **Annual deep analysis**: Re-analyze training data vs EPMC captures, check for new patterns
- **Trigger for V6 update**: >15 edge cases per year, precision <55%, or new resource types emerge

**Impact**: V5.1 ready for production with 77.3% training positive capture + 100% manual paper capture. Remaining 10 edge cases documented for manual curation.

**Critical Lesson**: EPMC query syntax does NOT auto-stem! Always use wildcards (`resource*` not `resource`) to match plural forms.

---

## 🤖 PyCaret Metadata-Only Classification (2025-11-11)

**Status**: ✅ **COMPLETE** - Target achieved (84.6% recall on external validation)

**Achievement**: Trained metadata-only classifier using PyCaret AutoML to identify bio-resource papers with **84.6% recall** (11/13 papers), exceeding the ≥80% target. Both TEST_MODE=True and TEST_MODE=False models achieved identical performance.

### Key Results

**External Validation Performance**:
- **TEST_MODE=True**: 11/13 detected = **84.6% recall** ✅
- **TEST_MODE=False**: 11/13 detected = **84.6% recall** ✅
- Cross-validation: 80.0% recall (5-fold) and 75.0% recall (10-fold)

**Models**:
- Base: PyCaret ensemble (GaussianNB + ExtraTreesClassifier + AdaBoostClassifier)
- Features: 91 (TEST_MODE=True) / 111 (TEST_MODE=False)
- Training samples: 1,605 papers

### Critical Fixes Applied

**Data Loss Bug** (30% samples lost):
- Root cause: PyCaret's default `train_size=0.7` was splitting data
- Fix: Changed to `train_size=0.999` (can't use 1.0 - exclusive range)
- Result: Preserved all 1,605 samples ✅

**Column Name Mismatch**:
- PyCaret uses 'Prec.' not 'Precision'
- Fixed result display to handle column name variations

**Ensemble Compatibility**:
- Changed from `method='soft'` to `method='auto'`
- Handles models without `predict_proba()`

### Features Engineered (91-111 features)

1. **MeSH Terms** (30-50 features): Target-encoded with smoothing
2. **Journals** (30 features): Top journals with target encoding
3. **Citations** (7 features): Raw counts, log transform, highly_cited indicator, age ratio
4. **Publication Types** (13 features): Binary indicators for common types
5. **Access Features** (9 features): hasData, isOpenAccess, hasSuppl, inPMC, etc.
6. **Temporal** (2 features): is_recent, is_old
7. **Text Length** (3 features): title_length, abstract_length, has_abstract
8. **Keywords** (3 features): database-specific keyword indicators

### Missed Papers Analysis

**Papers Consistently Missed**:
- **PMID 24727771** (ProteomeXchange 2014): Missed by BOTH models
  - hasData = 0% (vs 63.6% for detected papers) ⚠️
  - Unknown journal ("Nature biotechnology")
  - Only 23.3% MeSH term overlap

- **PMID 26014595** (ClinGen 2015): Missed by TEST_MODE=True
  - hasData = 0%
  - Unknown journal ("New England Journal of Medicine")
  - Only 6.7% MeSH term overlap ⚠️

**Root Causes**:
1. **Missing access metadata**: Missed papers lack hasData/hasSuppl flags (0% vs 63.6%)
2. **Unknown journals**: Both from journals not in training data → zero journal features
3. **Low MeSH overlap**: Insufficient overlap with top MeSH terms → most mesh features near zero
4. **Older papers**: 2014-2015 vs 2017-2018 average for detected

### Recommendations for Improvement

**Priority 1** (Most promising): Threshold optimization using `optimize_threshold()`
- Papers may have borderline scores just below 0.5 cutoff
- Expected to reach 92.3% recall (12/13 papers)

**Priority 2**:
- Re-enable class balancing with BorderlineSMOTE (careful testing)
- SHAP analysis on missed papers
- Test individual models vs ensemble

**Priority 3**:
- Enhanced feature engineering (database-specific keyword combinations)
- Try stacking instead of blending
- Expand training data with similar papers

### Production Readiness

**Status**: ✅ Ready for deployment

**Recommendation**: Deploy **TEST_MODE=True model** (91 features, 5-fold CV):
- Simpler feature set (91 vs 111)
- Faster training (5 vs 10 folds)
- Same external validation performance (84.6%)
- Better cross-validation recall (80% vs 75%)

**Use Case**: Fast metadata-only screening for large-scale paper filtering before applying full-text NER pipeline

### Files & Locations

**Notebooks** (Google Drive):
- `pycaret_metadata_training_v3.ipynb` (34 KB) - ⭐ **FINAL VERSION**

**Models** (Local):
- `/tmp/pycaret_test/pycaret_metadata_classifier_v1.pkl` (TEST_MODE=True)
- `/tmp/pycaret_test_false/pycaret_metadata_classifier_v1.pkl` (TEST_MODE=False)

**Validation Scripts**:
- `/tmp/pycaret_test/validate_13_papers.py` (external validation)
- `/tmp/pycaret_test/analyze_missed_papers.py` (failure pattern analysis)

### Comprehensive Documentation

**⭐ Complete Final Report**: [`docs/PYCARET_METADATA_CLASSIFICATION_FINAL_REPORT.md`](PYCARET_METADATA_CLASSIFICATION_FINAL_REPORT.md) - **READ THIS**

**Related Documentation**:
- `PYCARET_NOTEBOOK_UPDATES_2025-11-11.md` - Notebook update history
- `PYCARET_V3_CRITICAL_FIXES.md` - Critical fixes applied
- `SESSION_SUMMARY_2025-11-11_PYCARET_RECOVERY.md` - Session summary

**Impact**: Metadata-only classification is viable for bio-resource paper identification, achieving 84.6% recall without requiring full-text processing. Suitable for large-scale screening (120K+ papers).

---

## 🔬 spaCy Hybrid NER Implementation (2025-11-12)

**Status**: 📋 **READY FOR IMPLEMENTATION** - Comprehensive plan approved

**Goal**: Build EntityRuler + Statistical NER system for bioresource extraction with alias resolution and NEW entity discovery

### Key Capabilities

1. **High-Precision Known Entity Extraction**: EntityRuler with pattern matching (>95% precision target)
2. **Alias Resolution**: Links short/long form names (e.g., "PDB" ↔ "Protein Domain Database")
3. **Generalization to New Entities**: Statistical NER trained via distant supervision
4. **Production-Ready Pipeline**: Packaged spaCy model for deployment

### Architecture

**Hybrid Pipeline**: EntityRuler → Statistical NER (order is CRITICAL!)
- **EntityRuler**: Rule-based matching for ~3,000-5,000 known resources (dictionary-based)
- **Statistical NER**: Learns patterns to discover NEW/unknown bioresources
- **Training Method**: Distant supervision on 4,559 bioresource papers

### Timeline & Phases

**Total Duration**: 14-20 days (3-4 weeks full-time)

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 3-4 days | Dictionary enriched (70-80% coverage), patterns.jsonl |
| Phase 2 | 2-3 days | EntityRuler validated (>95% precision) |
| Phase 3 | 4-5 days | Training data (.spacy files) via distant supervision |
| Phase 4 | 1-2 days | Statistical NER trained (F1 >70% target) |
| Phase 5 | 2-3 days | Hybrid pipeline integrated and validated |
| Phase 6 | 2-3 days | Production deployment, benchmarks |

### Comprehensive Documentation

**⭐ Implementation Plan**: [`plans/spacy_hybrid_ner/`](../plans/spacy_hybrid_ner/) - **Start here**

**Phase-Specific Guides**:
- [`00_PROJECT_OVERVIEW.md`](../plans/spacy_hybrid_ner/00_PROJECT_OVERVIEW.md) - Architecture, timeline, success criteria
- [`01_DATA_PREPARATION_PHASES_1_2.md`](../plans/spacy_hybrid_ner/01_DATA_PREPARATION_PHASES_1_2.md) - Dictionary extraction, EntityRuler baseline
- [`02_TRAINING_PHASES_3_4.md`](../plans/spacy_hybrid_ner/02_TRAINING_PHASES_3_4.md) - Distant supervision, statistical training
- [`03_DEPLOYMENT_PHASES_5_6.md`](../plans/spacy_hybrid_ner/03_DEPLOYMENT_PHASES_5_6.md) - Hybrid integration, production deployment
- [`04_TROUBLESHOOTING_AND_RISKS.md`](../plans/spacy_hybrid_ner/04_TROUBLESHOOTING_AND_RISKS.md) - Risk mitigation, debugging guide
- [`05_SCRIPTS_INDEX.md`](../plans/spacy_hybrid_ner/05_SCRIPTS_INDEX.md) - Complete reference for all 13 scripts

**Research Foundation**: [`docs/research_docs/ner_implementation.md`](research_docs/ner_implementation.md) - Strategy 3 (Hybrid) detailed analysis

### Data Assets

**Bioresource Dictionary**: `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`
- 4,559 papers, 3,761 unique short names, 1,450 unique full names
- ⚠️ 60% missing full_name (will be enriched in Phase 1.2)

**Metadata**: `data/metadata/pmc_metadata_enhanced_full.csv` (21,612 papers with 28-34 features)

### Implementation Status

**Scripts to be Created** (13 total):
- Phase 1: `01_extract_bioresource_dictionary.py`, `02_enrich_missing_fullnames.py`, `03_generate_patterns_jsonl.py`
- Phase 2: `04_test_entityruler_pipeline.py`, `05_validate_entityruler.py`
- Phase 3: `06_prepare_training_corpus.py`, `07_distant_supervision_annotation.py`
- Phase 4: `notebooks/spacy_ner_training.ipynb` (Google Colab)
- Phase 5: `09_build_hybrid_pipeline.py`, `10_validate_hybrid_pipeline.py`, `11_benchmark_hybrid_speed.py`, `12_analyze_alias_resolution.py`
- Phase 6: `13_benchmark_all_models.py`, `src/ner_predict_spacy.py`

**Impact**: Will enable discovery of NEW/unknown bioresources not in training dictionary while maintaining high precision (>95%) on known entities. Addresses key limitation of existing V2/Phase 4 models: no alias linking capability.

---

## 📈 Recent Major Milestones

| Date | Milestone | Status | Performance | Reference |
|------|-----------|--------|-------------|-----------|
| 2025-11-12 | spaCy Hybrid NER Implementation Plan | 📋 Ready | 6 phases, 14-20 days timeline | [plans/spacy_hybrid_ner/](../plans/spacy_hybrid_ner/) ⭐ |
| 2025-11-11 | PyCaret Metadata Classification | ✅ Complete | 84.6% recall (11/13 papers) | [PYCARET_METADATA_CLASSIFICATION_FINAL_REPORT.md](PYCARET_METADATA_CLASSIFICATION_FINAL_REPORT.md) ⭐ |
| 2025-11-11 | EPMC Query V5.1 | ✅ Complete | 77.3% training positives, 100% manual | [EPMC_QUERY_V5_OPTIMIZATION.md](EPMC_QUERY_V5_OPTIMIZATION.md) ⭐ |
| 2025-11-10 | EPMC Query V4 | ✅ Complete | 0% → 92.3% manual capture (12/13) | [EPMC_QUERY_OPTIMIZATION_FINAL_REPORT.md](../analysis_output/EPMC_QUERY_OPTIMIZATION_FINAL_REPORT.md) |
| 2025-11-07 | Phase 4 Training Notebooks Fixed | ✅ Complete | 7 bugs fixed, A100 optimized | [PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md](PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md) ⭐ |
| 2025-11-06 | Phase 4 vs V2 Comparison (Scripts 01-02) | 🔴 Bug Found | Phase 4: 22.49% vs V2: 66.35% | [handovers/HANDOVER_COMPARISON_PROJECT.md](handovers/HANDOVER_COMPARISON_PROJECT.md) |
| 2025-11-05 | Phase 4 Cartesian Product Fix | ✅ Verified | 288,736 → 20,896 results | [PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md](PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md) |
| 2025-11-04 | Phase 4 Memory Optimization | ✅ Done | Memory: 94% reduction | [MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md) |
| 2025-10-31 | Phase 4 Multi-Task Complete | ⚠️ Has Bug | NER F1: 0.9274* (validation) | [multi_task_model/README.md](multi_task_model/README.md) |
| 2025-10-30 | Enhanced Metadata Features | ✅ Done | 21,392 papers × 38 features | [ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md](ENHANCED_METADATA_FINAL_REPORT_2025-10-30.md) |
| 2025-10-29 | Training Infrastructure | ✅ Done | Experimental pipeline ready | [EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md](EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md) |
| 2025-10-27 | PyTorch Compatibility | ✅ Resolved | Cross-platform models | [PYTORCH_CHECKPOINT_FIX.md](PYTORCH_CHECKPOINT_FIX.md) |

*Note: 0.9274 F1 was validation metric (token-level). Independent test evaluation shows 0.2249 F1 (entity-level) due to post-processing bug.

---

## 🔬 Entity Complexity Investigation (Phase 2 & 2B)

**Status**: ✅ COMPLETE - 12 complexity levels tested (5% to 92%)
**Duration**: October 21 - November 3, 2025
**Key Finding**: Split composition explains **80% of NER performance gap** to V2 baseline

### Executive Summary

Comprehensive investigation revealed that test set entity complexity significantly affects NER model performance, but the relationship is **more complex than expected**:

- **Split B (66% complexity)** achieved best performance: F1 = 0.7281 (vs current baseline 0.644)
- **Gap closure**: 80.1% (8.41 out of 10.5 percentage points to V2's 0.749)
- **Unexpected "valley"** at 55-60% complexity (worse than 28% complexity)
- **High-complexity plateau** at 80-92% performs nearly as well as Split B (avg F1 = 0.7240)
- **Split K2 (92%)** achieved F1 = 0.7273 (only 0.0008 behind Split B!)

### Key Results

| Split | Complexity | Val F1 | Performance Tier |
|-------|-----------|--------|------------------|
| **Split B** | 65.9% | **0.7281** | 🥇 Best |
| **Split K2** | 92.0% | **0.7273** | 🥈 Nearly tied |
| **Split E** | 83.9% | 0.7233 | 🥉 High plateau |
| Split J | 80.0% | 0.7215 | High plateau |
| Split D | 28.2% | 0.7165 | Mid-tier |
| Split G | 60.0% | 0.6950 | ⚠️ Valley (worse than 28%!) |
| Split F | 55.0% | 0.6975 | ⚠️ Valley |

### What This Means

1. **Split composition is critical** - explains 80% of performance difference
2. **Optimal complexity ~66%** BUT Split B may have benefited from lucky initialization
3. **High complexity (80-92%) is viable** - almost as good, potentially more stable
4. **Avoid 55-60% range** - unexpected performance valley
5. **Remaining 2.09 points to V2** require training procedure optimization

### Next Steps (Phase 3)

**Priority 1**: Validate Split B consistency with 5 random seeds (~40 GPU hours)
**Priority 2**: Test high-complexity plateau stability (~72 GPU hours)
**Priority 3**: Map the 55-60% performance valley (~56 GPU hours)
**Priority 4**: Hyperparameter optimization to close final 2.09 point gap (~120 GPU hours)

**Estimated timeline**: 5-7 weeks, ~288 GPU hours total

### Documentation

- **Phase 3 Work Plan**: [`docs/handover/PHASE3_WORK_PLAN.md`](handover/PHASE3_WORK_PLAN.md) ⭐ **Complete execution plan with all details**
- **Phase 2B Final Results**: [`docs/split_project/PHASE2B_FINAL_RESULTS.md`](split_project/PHASE2B_FINAL_RESULTS.md)
- **Phase 2 Results**: `PHASE2_COMPLETE_ANALYSIS.md`
- **Analysis Scripts**: `docs/split_project/analyze_phase2b_complete.py`
- **Data**: All 12 splits in `data/ner_splits_split{X}/`
- **Training Archives**: `collab_results/training_archives/2025-11-03-*_split*/`

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
- **⭐ [`PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md`](PHASE4_COMPLETE_IMPLEMENTATION_GUIDE.md)** - **Complete Phase 4 implementation guide** (get up to speed fast)
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
**Document Status**: ✅ Current and comprehensive (~670 lines)
**Last Review**: 2025-11-12 (V2 vs PyCaret comparison study complete)
**Next Review**: After model deployment decision and manual validation of high-confidence subset
**Maintained By**: AI agents working on biodata inventory pipeline

**Latest Work Summary** (2025-11-12):
- ✅ **V2 vs PyCaret Model Comparison**: Complete systematic evaluation on 156k papers
- ✅ Discovered fundamental classification difference: V2=conservative (8%), PyCaret=sensitive (27-34%)
- ✅ Identified 8,129 high-confidence papers (unanimous agreement across 3 models)
- ✅ Documented 44k disagreement cases requiring manual review
- ✅ Created hybrid two-stage pipeline recommendation (23x speedup)
- ✅ All scripts, results, and comprehensive documentation committed
- 📊 **Next**: Manual validation of high-confidence subset, deploy hybrid pipeline

**Previous Work** (2025-11-11):
- ✅ EPMC query V5.1 optimization (wildcard fix, 77.3% training coverage)
- ✅ PyCaret metadata classifier (84.6% recall on test set)

---

## 🆚 V2 vs PyCaret Model Comparison Study (2025-11-12)

**Status**: ✅ **COMPLETE** - Systematic evaluation on 156k papers (3,742 test + 153k production)

**Key Finding**: V2 (conservative, 8% positive) vs PyCaret (sensitive, 27-34% positive) represent fundamentally different classification strategies. Both valid, choice depends on deployment constraints.

### Critical Findings

1. **Classification Philosophy**: V2=high precision (99.9%), PyCaret=high recall (89-90%) - 5% F1 difference
2. **Speed & Size**: PyCaret is **23x faster** (3,121 vs 133 p/s) and **2,000x smaller** (184 KB vs 400 MB)
3. **Agreement**: Only 69-76% agreement on 153k unlabeled papers (large disagreement gap)
4. **High Confidence**: **8,129 papers** (5.3%) where ALL 3 models agree = bio-resource
5. **The Gap**: **44k papers** where PyCaret=YES but V2=NO (requires manual review)

### Recommendations

- **Use V2**: Maximum accuracy, GPU available, high precision critical
- **Use PyCaret**: Speed critical (23x faster), CPU-only, resource constraints
- **⭐ Hybrid Pipeline**: PyCaret screening (1 min) → V2 validation (5 min) = Best of both

### Key Artifacts

**Results**: `comparison_pycaret_v2/full_v5_comparison/`
- `all_three_agree_positive.csv` - 8,129 high-confidence papers
- `v2_no_pycaret_true_yes.csv` - 44k disagreement cases
- `full_v5_merged_predictions.csv` - All 153k predictions

**Documentation**:
- **⭐ COMPLETE STUDY**: [`V2_PYCARET_COMPARISON_STUDY.md`](V2_PYCARET_COMPARISON_STUDY.md) - Full methodology, results, analysis
- Quick start: `comparison_pycaret_v2/QUICK_START.md`

**Next Steps**: Manual validation of high-confidence subset, deploy hybrid pipeline

---

## Navigation to Supporting Documents

**Quick Access**:
- Operations → [`QUICK_REFERENCE_COMMANDS.md`](QUICK_REFERENCE_COMMANDS.md)
- Training → [`TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md)
- Best Practices → [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md)
- **⭐ EPMC Query V5.1** → [`EPMC_QUERY_V5_OPTIMIZATION.md`](EPMC_QUERY_V5_OPTIMIZATION.md) - **Latest optimization**
- **⭐ V2 vs PyCaret Study** → [`V2_PYCARET_COMPARISON_STUDY.md`](V2_PYCARET_COMPARISON_STUDY.md) - **Model comparison analysis**
- Phase 4 → [`multi_task_model/README.md`](multi_task_model/README.md)
- Pipelines → [`PIPELINE_GUIDES.md`](PIPELINE_GUIDES.md)
- History → [`HISTORICAL_UPDATES.md`](HISTORICAL_UPDATES.md)
- Phase 4 Inference Fix → [`PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md`](PHASE4_INFERENCE_CARTESIAN_PRODUCT_BUG_FIX.md)
- NER Post-Processing → [`PHASE4_NER_POST_PROCESSING_COMPLETE.md`](PHASE4_NER_POST_PROCESSING_COMPLETE.md)
- Memory Optimization → [`MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md`](MEMORY_OVERFLOW_FIX_SESSION_2025-11-04.md)
- NER Guide → [`NER_explanation.md`](NER_explanation.md)
- LLM Testing → [`../data/llm_comparison/prompts/README.md`](../data/llm_comparison/prompts/README.md)
