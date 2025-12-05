# Fresh Pipeline Run: 2022-mid2025 Progress Tracker

**Run ID**: 2025-12-02
**Started**: 2025-12-01
**Status**: ✅ Complete - All Phases Finished

---

## Quick Status

| Phase | Status | Notes |
|-------|--------|-------|
| **Setup** | ✅ Complete | Configuration, data prep, notebooks ready |
| **Phase 1** | ✅ Complete | V2 + PyCaret + Union done |
| **Phase 2** | ✅ Complete | V2 NER + spaCy NER + NER Union done |
| **Phase 3** | ✅ Complete | Linguistic scoring done |
| **Phase 4** | ✅ Complete | SetFit inference + V2 rescue done |
| **Phase 5** | ✅ Complete | Paper sets + entity mapping done |
| **Phase 6** | ✅ Complete | URL extraction done |
| **Phase 7** | ✅ Complete | Deduplication done |
| **Phase 8** | ✅ Complete | URL Recovery (abstract + fulltext + web search) |
| **Phase 9** | ✅ Complete | Final inventory: 1,858 resources |

**Legend**: ✅ Complete | 🔄 In Progress | ⏳ Pending | ❌ Failed | ⚠️ Needs Attention

---

## Phase 1: Classification ✅ COMPLETE

### V2 RoBERTa Classification ✅

**Date**: 2025-12-02
**Status**: Complete
**Session ID**: 2025-12-02-elktqk
**Runtime**: ~2.5 hours on T4 GPU (Colab)

**Results**:
- Total papers: 98,571
- Predicted bio-resource: **6,645 (6.7%)**
- Predicted NOT bio-resource: 91,926 (93.3%)

**Output File**: `data/phase1_classification/v2_classification_98k_2025-12-02-elktqk.csv`

### PyCaret Metadata Classification ✅

**Date**: 2025-12-02
**Status**: Complete
**Session ID**: 2025-12-02-83iwb9
**Runtime**: 34.2 seconds (local execution)

**Results**:
- Total papers: 95,393 (after deduplication - 3,178 duplicates removed)
- Predicted bio-resource: **25,476 (26.7%)**
- Predicted NOT bio-resource: 69,917 (73.3%)

**Output Files**:
- `data/phase1_classification/pycaret_classification_98k_2025-12-02-83iwb9.csv`
- `data/phase1_classification/pycaret_classification_98k.csv`

**Note**: PyCaret was run locally instead of Colab - faster and more reliable.

### Classification Union ✅

**Date**: 2025-12-02
**Status**: Complete

**Union Logic**: V2 positive OR PyCaret positive

**Results**:
| Classifier | Positives | Percentage |
|------------|-----------|------------|
| V2 RoBERTa | 6,645 | 6.7% |
| PyCaret | 25,476 | 25.8% |
| **Union Total** | **27,975** | **28.4%** |

**Breakdown**:
- V2 only: 2,484 papers
- PyCaret only: 21,330 papers
- Both agree: 4,161 papers

**Output Files**:
- `data/phase1_classification/classification_union.csv` (27,975 papers)
- `data/phase1_classification/classification_all_merged.csv` (full dataset)

---

## Phase 2: Named Entity Recognition ✅ COMPLETE

### V2 RoBERTa NER ✅

**Date**: 2025-12-02
**Status**: Complete
**Where Run**: Google Colab (T4 GPU)
**Runtime**: ~1-2 hours

**Results**:
- Input papers: 27,975
- **Total entities: 35,320**
- Papers with entities: ~10,000-12,000

**Output Files**:
- `data/phase2_ner/v2_ner_results.csv`

**Notebook**: `notebooks/phase2_ner/v2_ner_2022_mid2025.ipynb`

### spaCy Full Hybrid NER ✅

**Date**: 2025-12-02
**Status**: Complete
**Session ID**: 2025-12-02-a42bsx
**Where Run**: **LOCAL ONLY** (critical - see warning below)
**Runtime**: ~55 minutes

⚠️ **CRITICAL WARNING**: spaCy NER MUST be run locally. The model on Google Drive is BROKEN - missing the `tok2vec` component. Without `tok2vec`, statistical NER produces 0 entities (100% EntityRuler only).

**Results**:
- Input papers: 27,975
- **Total entities: 68,149**
- Papers with entities: 18,934 (67.68% coverage)
- Entity sources:
  - EntityRuler: ~30%
  - Statistical NER: ~70%

**Pipeline Verification**: `['entity_ruler', 'tok2vec', 'ner']` - all 3 components working

**Output Files**:
- `data/phase2_ner/spacy_ner_results_2025-12-02-a42bsx.csv`
- `data/phase2_ner/spacy_ner_results.csv` (copy for pipeline)
- `data/phase2_ner/benchmarks/spacy_ner_benchmark_2025-12-02-a42bsx.json`

**Script**: `scripts/phase2_ner/run_spacy_full_hybrid_local.py`

**How to Run**:
```bash
cd /Users/warren/development/GBC/inventory_2022
source spacy_hybrid_ner/venv/bin/activate
python unified_bioresource_pipeline/scripts/phase2_ner/run_spacy_full_hybrid_local.py
```

### NER Union ⏳

**Status**: Pending

**Logic**: Entity is included if found by V2 OR spaCy

**Script**: `scripts/phase2_ner/06_extract_pmid_union.py`

**Expected Output**: Combined unique entities from both systems, deduplicated by (paper_id, mention, label)

---

## Phase 3-9: Downstream Processing ✅ COMPLETE

| Phase | Script(s) | Purpose | Status |
|-------|-----------|---------|--------|
| 3 | `scripts/phase3_linguistic/07_linguistic_scoring.py` | Score entities linguistically | ✅ |
| 4 | `scripts/phase4_setfit/08_setfit_inference.py` | SetFit classification | ✅ |
| 5 | `scripts/phase5_mapping/09-13_*.py` | Create paper sets, map entities | ✅ |
| 6 | `scripts/phase6_scanning/14-19_*.py` | URL extraction and scanning | ✅ |
| 7 | `scripts/phase7_deduplication/17-19_*.py` | Deduplicate resources | ✅ |
| 8 | `scripts/phase8_url_recovery/28-34_*.py` | URL Recovery (abstract/fulltext/web search) | ✅ |
| 9 | `scripts/phase9_finalization/22-27_*.py` | Final inventory generation | ✅ |

---

## Phase 8: URL Recovery ✅ COMPLETE

**Date**: 2025-12-03
**Status**: Complete

Phase 8 recovers URLs for resources that didn't have URLs from the initial extraction. Uses a 3-stage approach:

### Stage 1: Abstract URL Search ✅

**Script**: `scripts/phase8_url_recovery/30_search_abstracts.py`

**Results**:
- Input: 603 resources missing URLs
- URLs found in abstracts: **2**
- Coverage: 0.3%

### Stage 2: Fulltext URL Search ✅

**Scripts**:
- `scripts/phase8_url_recovery/31_fetch_fulltext.py` - Fetch fulltext from PMC
- `scripts/phase8_url_recovery/32_search_fulltext.py` - Search for URLs in fulltext

**Results**:
- PMCIDs fetched: 989
- Papers with fulltext: 889
- URLs found in fulltext: **483**
- Coverage: 80.4%

### Stage 3: Web Search Agent Workflow ✅

**Date**: 2025-12-03

For resources still missing URLs after fulltext search, web search agents were dispatched.

**Process**:
1. Created 6 chunks of ~20 resources each (118 total)
2. Each agent received `AGENT_BRIEF.md` instructions
3. Agents launched in parallel batches (2 at a time initially, then 4)
4. Results merged with `34_merge_websearch_results.py`

**Files**:
- `data/phase8_url_recovery/websearch_chunks/AGENT_BRIEF.md` - Agent instructions
- `data/phase8_url_recovery/websearch_chunks/Orchestrator_prompt.md` - Orchestration guide
- `data/phase8_url_recovery/websearch_chunks/chunk_01.csv` through `chunk_06.csv` - Input chunks
- `data/phase8_url_recovery/websearch_chunks/websearch_results_chunk_01.csv` through `websearch_results_chunk_06.csv` - Output

**Web Search Results by Chunk**:

| Chunk | Searched | Found | Not Found |
|-------|----------|-------|-----------|
| 01 | 20 | 5 | 15 |
| 02 | 20 | 9 | 11 |
| 03 | 20 | 16 | 4 |
| 04 | 20 | 8 | 12 |
| 05 | 20 | 12 | 8 |
| 06 | 18 | 5 | 13 |
| **Total** | **118** | **55** | **63** |

**URL Filtering Applied**:
- 1 GitLab URL excluded (COMPAS)
- Final web search URLs: **54**

### Phase 8 Final Summary ✅

**Script**: `scripts/phase8_url_recovery/34_merge_websearch_results.py`

**Final URL Recovery Results**:

| Source | URLs Found |
|--------|------------|
| Abstract extraction | 2 |
| Fulltext extraction | 483 |
| Web search (filtered) | 54 |
| **Total Recovered** | **539** |

**Output Files**:
- `data/phase8_url_recovery/final_url_recovery.csv` - 539 resources with URLs
- `data/phase8_url_recovery/excluded_urls.csv` - 1 filtered record
- `data/phase8_url_recovery/url_recovery_summary.json` - Statistics

**Coverage Improvement**:
- Initial inventory: 1,255 resources with URLs (67.5%)
- After URL recovery: 1,794 resources with URLs (~96.6%)
- Resources still missing URLs: ~64

---

## Setup Phase ✅ COMPLETE

### Configuration Updates ✅

**Date**: 2025-12-01
**Status**: Complete

Updated `config/pipeline_config.yaml`:

```yaml
input:
  epmc_query_file: "../data/final_query_v5.1_2022_mid2025/query_results.csv"
  total_papers: 98571
  date_range: "2022-mid2025"
  query_version: "v5.1"

default_profile: "aggressive"
```

### Model Verification ✅

| Model | Path | Size | Status |
|-------|------|------|--------|
| V2 Classification | `out/original_model/article_classifier.pt` | 476 MB | ✅ Verified |
| V2 NER | `out/original_model/named_entity_recognition.pt` | 473 MB | ✅ Verified |
| PyCaret | `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl` | 184 KB | ✅ Verified |
| spaCy Hybrid | `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/` | 34 MB | ✅ Verified (LOCAL ONLY) |
| SetFit | `advanced_paper_filtering/results/setfit_2025-11-17-134146/setfit_introduction_classifier/` | 419 MB | ✅ Verified |

---

## Session Log

### 2025-12-01

**Time**: Initial setup
**Actions**:
1. Updated pipeline_config.yaml with new input path and aggressive profile
2. Verified all 5 model files exist and are accessible
3. Prepared classification input file (98,571 papers)
4. Created V2 classification Colab notebook for 2022-mid2025
5. Created PyCaret classification Colab notebook for 2022-mid2025
6. Created detailed plan document
7. Created this progress tracker

### 2025-12-02

**Time**: Phase 1 + Phase 2 execution
**Actions**:
1. Ran V2 classification on Colab (session: 2025-12-02-elktqk) - 6,645 positives (6.7%)
2. Created local PyCaret script (`02_run_pycaret_local.py`) with infinity value fixes
3. Ran PyCaret classification locally (session: 2025-12-02-83iwb9) - 25,476 positives (26.7%)
4. Created classification union - 27,975 papers (28.4%)
5. Ran V2 NER on Colab - 35,320 entities
6. **Discovered spaCy model on Google Drive is BROKEN** (missing tok2vec)
7. Created local spaCy script (`run_spacy_full_hybrid_local.py`)
8. Ran spaCy NER locally (session: 2025-12-02-a42bsx) - **68,149 entities** (67.68% coverage)
9. Created comprehensive pipeline documentation (`docs/PIPELINE_EXECUTION_GUIDE.md`)

**Key Discovery**: spaCy NER MUST be run locally. The model on Google Drive is missing the `tok2vec` component, which causes statistical NER to produce 0 entities. The local model has all 3 required components: `['entity_ruler', 'tok2vec', 'ner']`.

**Next Steps**:
1. Create NER union (V2 + spaCy)
2. Continue to Phase 3-9

---

## Files Created This Run

All paths relative to `unified_bioresource_pipeline/`

### Phase 1 Classification

| File | Type | Date |
|------|------|------|
| `config/pipeline_config.yaml` | Modified | 2025-12-01 |
| `data/input/v5.1_2022_mid2025_for_classification.csv` | Created | 2025-12-01 |
| `notebooks/phase1_classification/v2_classification_2022_mid2025.ipynb` | Created | 2025-12-01 |
| `notebooks/phase1_classification/pycaret_classification_2022_mid2025.ipynb` | Created | 2025-12-01 |
| `scripts/phase1_classification/02_run_pycaret_local.py` | Created | 2025-12-02 |
| `data/phase1_classification/v2_classification_98k_2025-12-02-elktqk.csv` | Created | 2025-12-02 |
| `data/phase1_classification/pycaret_classification_98k_2025-12-02-83iwb9.csv` | Created | 2025-12-02 |
| `data/phase1_classification/pycaret_classification_98k.csv` | Created | 2025-12-02 |
| `data/phase1_classification/classification_union.csv` | Created | 2025-12-02 |
| `data/phase1_classification/classification_all_merged.csv` | Created | 2025-12-02 |

### Phase 2 NER

| File | Type | Date |
|------|------|------|
| `notebooks/phase2_ner/v2_ner_2022_mid2025.ipynb` | Created | 2025-12-02 |
| `notebooks/phase2_ner/spacy_ner_2022_mid2025.ipynb` | Created | 2025-12-02 |
| `scripts/phase2_ner/run_spacy_full_hybrid_local.py` | Created | 2025-12-02 |
| `scripts/phase2_ner/run_spacy_ner_2022_mid2025.py` | Created | 2025-12-02 |
| `data/phase2_ner/v2_ner_results.csv` | Created | 2025-12-02 |
| `data/phase2_ner/spacy_ner_results_2025-12-02-a42bsx.csv` | Created | 2025-12-02 |
| `data/phase2_ner/spacy_ner_results.csv` | Created | 2025-12-02 |
| `data/phase2_ner/benchmarks/spacy_ner_benchmark_2025-12-02-a42bsx.json` | Created | 2025-12-02 |

### Documentation

| File | Type | Date |
|------|------|------|
| `docs/FRESH_RUN_2022_MID2025_PLAN.md` | Created | 2025-12-01 |
| `docs/FRESH_RUN_2022_MID2025_PROGRESS.md` | Created | 2025-12-01 |
| `docs/PIPELINE_EXECUTION_GUIDE.md` | Created | 2025-12-02 |

---

## Metrics

### Phase 1 Results ✅
- V2 Positives: 6,645 (6.7%)
- PyCaret Positives: 25,476 (26.7%)
- Union Total: **27,975 (28.4%)**

### Phase 2 Results ✅
- V2 NER Entities: **35,320**
- spaCy NER Entities: **68,149**
- spaCy Coverage: 67.68% (18,934 papers with entities)
- spaCy Entity Sources: ~30% EntityRuler, ~70% Statistical
- Union Papers: *pending*
- Union Entities: *pending*

### Final Results
- Total Bioresources: *pending*
- Novel Bioresources: *pending*
- URLs Recovered: *pending*

---

## Key Learnings

### spaCy NER Must Run Locally

**Problem**: Running spaCy NER on Colab produced 100% EntityRuler entities and 0% statistical entities.

**Root Cause**: The spaCy model on Google Drive is missing the `tok2vec` component. Without `tok2vec`, the statistical NER component cannot function.

**Solution**: Run spaCy NER locally using `scripts/phase2_ner/run_spacy_full_hybrid_local.py`. The local model at `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/` has all 3 required components.

**Verification**: Check `nlp.pipe_names` returns `['entity_ruler', 'tok2vec', 'ner']`

### PyCaret on Colab Requires Runtime Change

**Problem**: First run of PyCaret on Colab crashes with numpy error.

**Solution**:
1. Change runtime to Python 3.11 (2025.07) via `Runtime` → `Change runtime type`
2. Run notebook - first run will crash with numpy error (expected)
3. `Runtime` → `Restart and run all` - second run works

---

**Document Version**: 3.0
**Last Updated**: 2025-12-03
**Status**: Complete - All Phases Finished

---

## Final Results Summary

| Metric | Value |
|--------|-------|
| Input Papers | 98,571 |
| Classification Union | 27,975 (28.4%) |
| NER Union Papers | 20,017 |
| Final Introductions | 11,336 |
| Unique Resources | 1,858 (≥2 papers) |
| URL Coverage | 96.6% (after recovery) |

### URL Recovery Breakdown
| Source | URLs |
|--------|------|
| Initial extraction | 1,255 |
| Abstract search | +2 |
| Fulltext search | +483 |
| Web search agents | +54 |
| **Total with URLs** | **1,794** |
