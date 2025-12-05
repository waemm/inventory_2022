# Fresh Pipeline Run: 2022-mid2025 EPMC Data

**Created**: 2025-12-01
**Status**: In Progress
**Input Data**: 98,571 papers from EPMC Query V5.1 (2022-mid2025)
**Filtering Profile**: Aggressive (maximum recall)

---

## Table of Contents

1. [Overview](#overview)
2. [Input Data](#input-data)
3. [Phase 1: Classification](#phase-1-classification)
4. [Phase 2: Named Entity Recognition](#phase-2-named-entity-recognition)
5. [Phase 3: Linguistic Filtering](#phase-3-linguistic-filtering)
6. [Phase 4: SetFit Classification](#phase-4-setfit-classification)
7. [Phase 5: Entity Mapping](#phase-5-entity-mapping)
8. [Phase 6: URL Scanning](#phase-6-url-scanning)
9. [Phase 7: Deduplication](#phase-7-deduplication)
10. [Phase 8: URL Recovery](#phase-8-url-recovery)
11. [Phase 9: Finalization](#phase-9-finalization)
12. [Baseline Creation](#baseline-creation)
13. [Expected Outputs](#expected-outputs)
14. [Troubleshooting](#troubleshooting)

---

## Overview

### Objective

Run the complete unified bioresource pipeline on new EPMC query results covering **2022 to mid-2025** to discover novel bioresources not present in the existing baseline.

### Key Parameters

| Parameter | Value |
|-----------|-------|
| Input Papers | 98,571 |
| Date Range | 2022 - mid-2025 |
| Query Version | V5.1 |
| Filtering Profile | **Aggressive** |
| Expected Output | ~1,500-2,000 unique bioresources |
| Total Runtime | 10-17 hours |

### Pipeline Flow

```
98,571 papers (EPMC V5.1, 2022-mid2025)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: CLASSIFICATION                                      │
│ ├─ V2 RoBERTa (GPU, Colab) ──────► ~8,000 positives (~8%)   │
│ └─ PyCaret Metadata (GPU/CPU) ───► ~30,000 positives (~30%) │
│     Union: ~33,000 positives (~33%)                          │
│     Time: 2-4 hours                                          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: NAMED ENTITY RECOGNITION                            │
│ ├─ V2 RoBERTa NER (GPU, Colab) ──► ~12,000 papers           │
│ └─ spaCy Hybrid NER (CPU, Local) ► ~21,000 papers           │
│     Union: ~23,000 papers with entities                      │
│     Time: 5-10 hours                                         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: LINGUISTIC FILTERING                                │
│ ├─ High score (≥3): ~6,000 papers                           │
│ ├─ Medium score (0-2): ~14,000 papers                       │
│ └─ Low score (<0): ~3,000 papers                            │
│     Time: <1 minute                                          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: SETFIT CLASSIFICATION                               │
│ Input: ~14,000 medium-score papers                           │
│ Output: ~5,000 additional introductions                      │
│ Total introductions: ~11,000 (High + SetFit)                │
│ Time: 10-15 minutes (GPU)                                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: ENTITY MAPPING & RESOURCE CREATION                  │
│ ├─ Create paper sets (A, B, C)                              │
│ ├─ Map papers to NER entities                               │
│ ├─ Extract URLs from abstracts                              │
│ └─ CRITICAL: Run 02b script to merge entity/URL data        │
│     Time: 5-10 minutes                                       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: URL SCANNING & VALIDATION                           │
│ ├─ Multi-threaded HTTP scanning (10 workers)                │
│ ├─ Wayback Machine fallback for offline URLs                │
│ └─ Quality scoring (domain, content, metadata)              │
│     Time: 75-90 minutes                                      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 7: DEDUPLICATION (Aggressive Profile)                  │
│ ├─ Linguistic similarity matching                           │
│ ├─ URL-based deduplication                                  │
│ ├─ Baseline comparison (combined baseline)                  │
│ └─ Manual review of unclear cases                           │
│     Time: 5 minutes + manual review                          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 8: URL RECOVERY                                        │
│ ├─ Identify records missing URLs                            │
│ ├─ Search abstracts for URLs                                │
│ ├─ Search fulltext (EPMC API) for URLs                      │
│ └─ Prepare web search chunks for manual/agent search        │
│     Time: ~5 minutes (automated)                             │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 9: FINALIZATION                                        │
│ ├─ Name disambiguation (URL subdomain analysis)             │
│ ├─ URL validation and blocking (repos, file downloads)      │
│ ├─ EPMC metadata enrichment                                 │
│ └─ Generate final inventory CSV                             │
│     Time: 5-10 minutes                                       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
~1,500-2,000 Unique Validated Bioresources
```

---

## Input Data

### Source File

| Attribute | Value |
|-----------|-------|
| Path | `data/final_query_v5.1_2022_mid2025/query_results.csv` |
| Size | 188 MB |
| Papers | 98,571 |
| Columns | 20 |

### Column Schema

```
id, title, abstract, publication_date, hasDbCrossReferences, hasData,
hasSuppl, isOpenAccess, inPMC, inEPMC, hasPDF, hasBook, citedByCount,
pubYear, pubType, keywords, meshTerms, journalTitle, journalISSN,
authorAffiliations
```

### Data Quality

| Metric | Value |
|--------|-------|
| Papers with abstracts | 89,938 (91.2%) |
| Papers without abstracts | 8,633 (8.8%) |
| Papers with MeSH terms | ~59% |
| Papers with keywords | ~71% |

### Prepared Input Files

| File | Location | Purpose |
|------|----------|---------|
| Classification input | `unified_bioresource_pipeline/data/input/v5.1_2022_mid2025_for_classification.csv` | Simplified 3-column format for V2 classifier |
| Full metadata | `data/final_query_v5.1_2022_mid2025/query_results.csv` | Full 20-column format for PyCaret |

---

## Phase 1: Classification

### Overview

Two classifiers run in parallel to maximize recall:
- **V2 RoBERTa**: Text-based classifier (title + abstract)
- **PyCaret**: Metadata-based classifier (91 engineered features)

### V2 RoBERTa Classification

| Parameter | Value |
|-----------|-------|
| Model | `out/original_model/article_classifier.pt` (476 MB) |
| Architecture | RobertaForSequenceClassification |
| Max Length | 512 tokens |
| Batch Size | 16 |
| Device | CUDA (GPU required) |
| Expected Positives | ~8,000 (~8%) |

**Colab Notebook**: `unified_bioresource_pipeline/notebooks/phase1_classification/v2_classification_2022_mid2025.ipynb`

**Runtime**: 1.5-3 hours on T4 GPU

**Input**: `unified_bioresource_pipeline/data/input/v5.1_2022_mid2025_for_classification.csv`

**Output**: `unified_bioresource_pipeline/data/phase1_classification/v2_classification_98k_{session_id}.csv`

### PyCaret Metadata Classification

| Parameter | Value |
|-----------|-------|
| Model | `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl` (184 KB) |
| Features | 91 engineered (MeSH, journals, pub types, etc.) |
| Device | CPU or GPU |
| Expected Positives | ~30,000 (~30%) |

**Colab Notebook**: `unified_bioresource_pipeline/notebooks/phase1_classification/pycaret_classification_2022_mid2025.ipynb`

**Runtime**: 10-15 minutes

**Input**: `data/final_query_v5.1_2022_mid2025/query_results.csv` (needs full metadata)

**Output**: `unified_bioresource_pipeline/data/phase1_classification/pycaret_classification_98k_{session_id}.csv`

### Union Creation

After both classifiers complete:

```bash
cd unified_bioresource_pipeline/scripts/phase1_classification
python 03_create_classification_union.py
```

**Logic**: Paper is positive if V2 positive OR PyCaret positive

**Expected Union**: ~33,000 papers (~33%)

**Output**: `unified_bioresource_pipeline/data/phase1_classification/classification_union.csv`

---

## Phase 2: Named Entity Recognition

### Overview

Two NER systems extract bioresource names (COM = common name, FUL = full name):
- **V2 RoBERTa NER**: Deep learning model (GPU required)
- **spaCy Hybrid NER**: EntityRuler + Statistical NER (CPU optimal)

### V2 RoBERTa NER

| Parameter | Value |
|-----------|-------|
| Model | `out/original_model/named_entity_recognition.pt` (473 MB) |
| Architecture | RobertaForTokenClassification |
| Labels | COM, FUL |
| Batch Size | 8 |
| Device | CUDA (GPU required) |
| Expected Papers | ~12,000 |
| Expected Entities | ~45,000 |

**Colab Notebook**: `unified_bioresource_pipeline/notebooks/phase2_ner/v2_ner_colab.ipynb` (needs update for 2022-mid2025)

**Runtime**: 3-6 hours on T4 GPU

**Input**: Classification union from Phase 1

**Output**: `unified_bioresource_pipeline/data/phase2_ner/v2_ner_results.csv`

### spaCy Hybrid NER

| Parameter | Value |
|-----------|-------|
| Model | `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful` (34 MB) |
| Components | EntityRuler (6,216 patterns) + tok2vec + NER |
| Speed | 100-200 papers/sec |
| Device | CPU (optimal) |
| Expected Papers | ~21,000 |
| Expected Entities | ~78,000 |

**Script**: `unified_bioresource_pipeline/scripts/phase2_ner/05_run_spacy_ner.py`

**Runtime**: 0.5-2 hours locally

**Input**: Classification union from Phase 1

**Output**: `unified_bioresource_pipeline/data/phase2_ner/spacy_ner_results.csv`

### PMID Union Extraction

```bash
cd unified_bioresource_pipeline/scripts/phase2_ner
python 06_extract_pmid_union.py
```

**Output**: `unified_bioresource_pipeline/data/phase2_ner/all_paper_pmids.txt`

**Expected**: ~23,000 unique papers with entities

---

## Phase 3: Linguistic Filtering

### Overview

Score papers based on 7 linguistic features to identify resource introduction papers vs. usage papers.

### Features

1. `database_keyword` - Contains "database", "repository", etc.
2. `availability` - "available at", "can be accessed"
3. `first_person` - "we developed", "our database"
4. `present_tense` - "is available", "contains"
5. `version_number` - "version 2.0", "v3.1"
6. `download_mention` - "download", "freely available"
7. `url_present` - URL in abstract

### Score Thresholds (Aggressive Profile)

| Category | Threshold | Expected Papers |
|----------|-----------|-----------------|
| High confidence | ≥2 | ~6,000 |
| Medium confidence | -1 to 1 | ~14,000 |
| Low confidence | <-1 | ~3,000 |

**Script**: `unified_bioresource_pipeline/scripts/phase3_linguistic/07_linguistic_scoring.py`

**Runtime**: <1 minute

**Outputs**:
- `data/phase3_linguistic/high_score_papers.csv`
- `data/phase3_linguistic/medium_score_papers.csv`
- `data/phase3_linguistic/low_score_papers.csv`

---

## Phase 4: SetFit Classification

### Overview

Use few-shot learning to classify medium-confidence papers as introductions or usage papers.

### Model

| Parameter | Value |
|-----------|-------|
| Model | `advanced_paper_filtering/results/setfit_2025-11-17-134146/setfit_introduction_classifier/` (419 MB) |
| Architecture | Sentence Transformers (few-shot) |
| Training Examples | 40 (20 intro, 20 usage) |
| Threshold | 0.55 (aggressive profile) |

**Colab Notebook**: `unified_bioresource_pipeline/notebooks/phase4_setfit/setfit_inference_colab.ipynb` (needs update)

**Runtime**: 10-15 minutes on T4 GPU

**Input**: `data/phase3_linguistic/medium_score_papers.csv`

**Output**: `data/phase4_setfit/setfit_introductions.csv`

**Expected**: ~5,000 additional introductions

---

## Phase 5: Entity Mapping

### Overview

Map classified papers to NER entities and extract URLs.

### Scripts (Run in Order)

```bash
cd unified_bioresource_pipeline/scripts/phase5_mapping

# 1. Create paper sets (A=linguistic, B=SetFit, C=union)
python 09_create_paper_sets.py

# 2. Map papers to NER entities
python 10_map_to_entities.py

# 3. Create primary resource records
python 11_create_primary_resources.py

# 4. Add quality indicators
python 12_add_quality_indicators.py

# 5. Extract URLs from abstracts
python 13_extract_urls.py

# 6. CRITICAL: Merge entity/URL data into set_c_union.csv
python 02b_update_set_c_with_entities.py
```

**Runtime**: 5-10 minutes total

**Critical Note**: Script `02b_update_set_c_with_entities.py` fixes a data loss bug - **DO NOT SKIP**.

**Output**: `data/phase5_mapping/papers_with_urls.csv`

---

## Phase 6: URL Scanning

### Overview

Validate URLs and assess quality using multi-threaded scanner with Wayback fallback.

### Parameters

| Parameter | Value |
|-----------|-------|
| Scanner Version | V4 |
| Workers | 10 concurrent |
| Timeout | 30 seconds |
| Wayback Fallback | Enabled |

### Scripts

```bash
cd unified_bioresource_pipeline/scripts/phase6_scanning

# 1. Prepare and deduplicate URLs
python 14_prepare_urls.py

# 2. Run multi-threaded URL scanning
python 15_scan_urls.py

# 3. Merge scan scores
python 16_merge_scan_scores.py

# 4. Scan Set C URLs (with session support)
python 18_scan_urls_set_c.py

# 5. Backfill URL data to resources
python 19_backfill_url_data.py
```

**Runtime**: 75-90 minutes

**Output**: `data/phase6_scanning/papers_with_url_scores.csv`

---

## Phase 7: Deduplication

### Overview

Remove duplicates using linguistic similarity, URL matching, and baseline comparison.

### Aggressive Profile Settings

| Parameter | Value |
|-----------|-------|
| DB Keywords | database, server, portal, repository, archive, atlas, map, bank, wiki, hub, resource, browser, db, base, tool, network, collection, catalog, platform, pedia, mine, cyc |
| Linguistic Bypass Threshold | 4 |
| SetFit Threshold | 0.55 |
| Linguistic High Threshold | 2 |
| Linguistic Low Threshold | -1 |
| Require URL | false |

### Scripts

```bash
cd unified_bioresource_pipeline/scripts/phase7_deduplication

# 1. Run deduplication with aggressive profile
python 17_deduplicate_all_sets.py --profile aggressive

# 2. Analyze unclear cases for manual review
python 18_analyze_unclear_cases.py

# 3. [MANUAL] Review unclear_cases.csv, assign merge groups
# 4. Apply manual merge decisions
python 19_apply_manual_merges.py
```

**Runtime**: 5 minutes + manual review time

**Outputs**:
- `data/phase7_deduplication/deduplicated_resources.csv`
- `data/phase7_deduplication/unclear_cases.csv` (for manual review)
- `data/phase7_deduplication/manual_merges.csv` (user-created)

---

## Phase 8: URL Recovery

### Overview

Recover URLs for records missing them by searching abstracts and fulltext.

### Scripts

```bash
cd unified_bioresource_pipeline/scripts/phase8_url_recovery

# Run all phase 8 scripts
python run_phase8.py

# Or run individually:
python 28_identify_missing_urls.py
python 29_fetch_abstracts.py
python 30_search_abstracts_urls.py
python 31_fetch_fulltext.py
python 32_search_fulltext_urls.py
python 33_consolidate_recovery.py
python 34_merge_websearch_results.py  # After agent web search
```

**Runtime**: ~5 minutes (automated) + optional agent web search

**Outputs**:
- `data/phase8_url_recovery/recovered_urls.csv`
- `data/phase8_url_recovery/still_missing.csv`
- `data/phase8_url_recovery/websearch_chunks/` (for agent search)

---

## Phase 9: Finalization

### Overview

Apply final quality improvements and generate the final inventory.

### Scripts

```bash
cd unified_bioresource_pipeline/scripts/phase9_finalization

# Run all phase 9 scripts
python run_phase9.py

# Or run individually:
python 22_filter_novel_resources.py
python 23_transform_columns.py      # Name disambiguation, capitalization
python 24_check_urls_with_geo.py    # URL validation, geolocation
python 25_fetch_epmc_metadata.py    # EPMC metadata enrichment
python 26_process_countries.py      # Country processing
python 27_generate_final_inventory.py
```

**Runtime**: 5-10 minutes

**Final Output**: `data/phase9_finalization/final_inventory.csv`

---

## Baseline Creation

### Overview

Create a combined baseline from two sources for deduplication comparison.

### Source Files

| Source | Path | Records |
|--------|------|---------|
| GBC External Database | `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv` | 4,560 |
| Recent 2010-2022 Run | `unified_bioresource_pipeline/post_processing/results/final_inventory_QC_FIXED.csv` | 1,688 |

### Baseline Creation Task (Before Phase 7)

1. Load both source files
2. Harmonize column schemas:
   - External: `resource_short_name`, `resource_full_name`, `pubmed_id`
   - Internal: `best_name`, `best_common`, `best_full`, `ID`
3. Deduplicate by resource name and URL
4. Create unified baseline CSV
5. Save to `data/baseline/combined_baseline.csv`

**Note**: This step should be done when reaching Phase 7, as the 2010-2022 data may still need QC improvements.

---

## Expected Outputs

### Per-Phase Outputs

| Phase | Output | Expected Records |
|-------|--------|------------------|
| 1 | Classification union | ~33,000 papers |
| 2 | NER union | ~23,000 papers |
| 3 | Linguistic scores | High: ~6k, Medium: ~14k, Low: ~3k |
| 4 | SetFit introductions | ~5,000 papers |
| 5 | Papers with entities | ~11,000 papers |
| 6 | Papers with URL scores | ~11,000 papers |
| 7 | Deduplicated resources | ~2,000 resources |
| 8 | URL-recovered resources | +100-200 URLs |
| 9 | Final inventory | ~1,500-2,000 resources |

### Final Output Schema

```
best_name, best_name_prob, best_common, best_common_prob, best_full,
best_full_prob, article_count, extracted_url, extracted_url_status,
extracted_url_country, extracted_url_coordinates, wayback_url,
publication_date, affiliation, authors, grant_ids, grant_agencies,
num_citations, affiliation_countries, best_name_original, url_validation,
paper_titles, name_modification_flags
```

---

## Troubleshooting

### GPU Out of Memory (OOM)

**Symptom**: CUDA OOM error during classification or NER

**Solution**: Reduce batch size in config or notebook:
```yaml
classification:
  v2:
    batch_size: 8  # Reduce from 16
```

### Missing Input Files

**Symptom**: FileNotFoundError during phase execution

**Solution**: Check that previous phase completed successfully:
```bash
python run_pipeline.py --status
ls -la data/phase{N-1}_*/
```

### Slow URL Scanning

**Symptom**: Phase 6 taking longer than expected

**Solution**: Increase workers (if network allows):
```yaml
url_scanning:
  workers: 20  # Increase from 10
```

### PyCaret Model Load Error

**Symptom**: Error loading PyCaret model

**Solution**: Ensure PyCaret is installed:
```bash
pip install pycaret[full]
```

### spaCy Model Not Found

**Symptom**: OSError when loading spaCy model

**Solution**: Verify model path exists:
```bash
ls -la spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/
```

---

## Quick Reference Commands

### Check Status
```bash
cd unified_bioresource_pipeline
python run_pipeline.py --status
```

### Run Full Pipeline
```bash
python run_pipeline.py --full
```

### Resume from Phase 3
```bash
python run_pipeline.py --from phase3
```

### Run Single Phase
```bash
python run_pipeline.py --phase phase5
```

### Dry Run (Preview)
```bash
python run_pipeline.py --full --dry-run
```

---

## File Locations Summary

### Configuration
- `unified_bioresource_pipeline/config/pipeline_config.yaml`

### Input Data
- `data/final_query_v5.1_2022_mid2025/query_results.csv`
- `unified_bioresource_pipeline/data/input/v5.1_2022_mid2025_for_classification.csv`

### Colab Notebooks (2022-mid2025)
- `unified_bioresource_pipeline/notebooks/phase1_classification/v2_classification_2022_mid2025.ipynb`
- `unified_bioresource_pipeline/notebooks/phase1_classification/pycaret_classification_2022_mid2025.ipynb`

### Models
- V2 Classifier: `out/original_model/article_classifier.pt`
- V2 NER: `out/original_model/named_entity_recognition.pt`
- PyCaret: `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl`
- spaCy: `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/`
- SetFit: `advanced_paper_filtering/results/setfit_2025-11-17-134146/setfit_introduction_classifier/`

### Progress Tracking
- `unified_bioresource_pipeline/docs/FRESH_RUN_2022_MID2025_PROGRESS.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-12-01
