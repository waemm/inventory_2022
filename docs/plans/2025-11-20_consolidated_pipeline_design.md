# Consolidated Bioresource Pipeline - Complete Design

**Date:** 2025-11-20
**Status:** Design Complete
**Purpose:** Unified end-to-end pipeline from EPMC query to deduplicated bioresources

---

## Executive Summary

This document describes the **consolidated bioresource discovery pipeline** that integrates:
- Classification (RoBERTa V2 + PyCaret)
- NER (RoBERTa V2 + spaCy Hybrid)
- Linguistic filtering
- SetFit classification
- Advanced deduplication & URL validation

**Key Achievement:** Single reproducible pipeline that can start from any step.

---

## Pipeline Architecture

### Overview Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    EPMC QUERY V5.1 (2011-2021)                  │
│                        149,943 papers                           │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ PHASE 1: CLASSIFICATION (V2 RoBERTa + PyCaret)                 │
│ • V2 Text Classifier: 12,285 positives (8.2%)                 │
│ • PyCaret Metadata: 45,766 positives (30.6%)                  │
│ • Union (OR logic): 50,192 positives (33.5%)                  │
│                                                                 │
│ Time: 2-4 hrs (V2 GPU) + 15 min (PyCaret CPU)                 │
│ Resumable: ✓ Save union_v2_pycaret_*.csv                      │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ PHASE 2: NER (V2 RoBERTa + spaCy Hybrid)                       │
│ • V2 NER: 18,319 papers, 67,187 entities                      │
│ • spaCy Hybrid: 32,317 papers, 117,491 entities               │
│ • Union: 34,279 unique papers                                  │
│                                                                 │
│ Time: 4-8 hrs (V2 GPU) + 1-2 hrs (spaCy CPU)                  │
│ Resumable: ✓ Save spacy_ner_*.csv, v2_ner_*.csv              │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ PHASE 3: PMID EXTRACTION                                        │
│ • Extract unique PMIDs from both NER results                   │
│ • Output: all_paper_pmids.txt (34,279 PMIDs)                  │
│                                                                 │
│ Script: extract_ner_union_papers.py                            │
│ Time: <1 minute                                                 │
│ Resumable: ✓ Start here if you have NER results               │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ PHASE 4: LINGUISTIC FILTERING                                   │
│ • High score (≥3): 8,648 introductions (25.2%)                │
│ • Medium score (0-2): 20,816 papers (60.7%)                   │
│ • Low score (<0): 4,796 usage papers (14.0%)                  │
│                                                                 │
│ Script: 03_linguistic_scoring.py                               │
│ Time: ~30 seconds                                               │
│ Resumable: ✓ Start here with all_paper_pmids.txt              │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ PHASE 5: SETFIT CLASSIFICATION (Medium-score only)            │
│ • Input: 20,816 medium-score papers                            │
│ • SetFit inference (GPU): ~7,800 introductions                 │
│ • High + SetFit = ~16,605 total introductions                  │
│                                                                 │
│ Notebook: setfit_inference_colab.ipynb                         │
│ Time: 10-15 minutes (GPU)                                       │
│ Resumable: ✓ Start here with medium_score_papers.csv          │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ PHASE 6: ENTITY MAPPING & RESOURCE CREATION                    │
│ • Merge linguistic + SetFit introductions                       │
│ • Map papers back to NER entities                              │
│ • Create primary resource CSV                                   │
│ • Add quality indicators                                        │
│ • Extract URLs                                                  │
│                                                                 │
│ Scripts: 02_create_paper_sets.py, 03_map_papers_to_entities.py│
│         09_create_primary_resource_csv.py, etc.                │
│ Time: 5-10 minutes                                              │
│ Resumable: ✓ Start here with union paper sets                 │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ PHASE 7: URL SCANNING & VALIDATION                             │
│ • Prepare URLs for scanning                                     │
│ • Multi-threaded scan with Wayback fallback                    │
│ • Merge scores back into dataset                               │
│                                                                 │
│ Scripts: prepare_gbc_urls.py, scan_gbc_full.py,               │
│         merge_scan_scores.py                                    │
│ Time: 75-90 minutes                                             │
│ Resumable: ✓ Start here with primary_resource CSV             │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ PHASE 8: DEDUPLICATION                                          │
│ • Linguistic deduplication (URL similarity)                     │
│ • Analyze unclear cases                                         │
│ • MANUAL: Review and assign merge groups                       │
│ • Apply manual merges                                           │
│                                                                 │
│ Scripts: 14_deduplicate_linguistic_improved.py,                │
│         15_analyze_unclear_cases.py, 16_apply_manual_merges.py│
│ Time: 5 minutes + manual review                                 │
│ Resumable: ✓ Start here with URL-scanned papers               │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                 FINAL OUTPUT: ~974 Unique Bioresources         │
└────────────────────────────────────────────────────────────────┘
```

---

## Models & Notebooks

### Phase 1: Classification

**V2 RoBERTa Text Classifier**
- Model: `out/original_model/article_classifier.pt` (RoBERTa-base)
- Architecture: HuggingFace `RobertaForSequenceClassification`
- Input: Title + Abstract (max 256 tokens script, 512 tokens notebook)
- Output: bio-resource / not-bio-resource + confidence
- Notebook: `validation_spacy_v_BERT/notebooks/phase2_v2_classification_150k_VB.ipynb`
- Runtime: 2-4 hours (T4/V100 GPU)
- Results: ~12,285 positives (8.2%)

**PyCaret Metadata Classifier**
- Model: `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl`
- Features: 91 engineered (numeric, binary, MeSH terms, pub types, journals)
- Input: EPMC metadata only (no text)
- Output: 0/1 + prediction_score
- Notebook: `validation_spacy_v_BERT/notebooks/phase2_pycaret_classification_150k_VB.ipynb`
- Runtime: 10-15 minutes (CPU - FASTER than GPU!)
- Results: ~45,766 positives (30.6%)

**Union Logic**
- Method: Logical OR (V2 positive OR PyCaret positive)
- Rationale: Prioritize recall over precision
- Manual merge in notebooks
- Results: 50,192 positives (33.5%)

### Phase 2: NER

**V2 RoBERTa NER**
- Model: `out/original_model/named_entity_recognition.pt` (RoBERTa-base, 473 MB)
- Architecture: HuggingFace `RobertaForTokenClassification`
- Labels: COM (common name), FUL (full name)
- Input: Title + Abstract tokenized
- Notebook: `validation_spacy_v_BERT/notebooks/phase2_v2_ner_150k_VB.ipynb`
- Runtime: 4-8 hours (T4/V100 GPU)
- Results: 18,319 papers, 67,187 entities

**spaCy Hybrid NER**
- Model: `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful`
- Architecture: EntityRuler (6,216 patterns) + Statistical NER (tok2vec + ner)
- Components: [entity_ruler, tok2vec, ner]
- Input: Title + Abstract
- Notebook: `validation_spacy_v_BERT/notebooks/phase2_spacy_ner_150k_VB.ipynb`
- Runtime: 1-2 hours (CPU - 100-200 papers/sec)
- Results: 32,317 papers, 117,491 entities
- **Note:** Statistical NER currently broken (label mismatch), EntityRuler works

### Phase 5: SetFit

**SetFit Introduction Classifier**
- Model: `advanced_paper_filtering/results/setfit_*/setfit_introduction_classifier/`
- Architecture: Sentence Transformers (SetFit framework)
- Training: 40 examples (20 intro, 20 usage)
- Input: Title + Abstract embeddings
- Notebook: `advanced_paper_filtering/notebooks/setfit_training_colab.ipynb` (train)
           `advanced_paper_filtering/notebooks/setfit_inference_colab.ipynb` (inference)
- Runtime: 10-15 minutes (GPU inference)
- Results: ~7,800 introductions from 20,816 medium-score papers

---

## Directory Structure

### Proposed Unified Structure

```
unified_bioresource_pipeline/
├── models/
│   ├── classification/
│   │   ├── v2_roberta_classifier.pt → out/original_model/article_classifier.pt
│   │   └── pycaret_classifier.pkl → pycaret_models/.../pycaret_metadata_classifier_v1.pkl
│   ├── ner/
│   │   ├── v2_roberta_ner.pt → out/original_model/named_entity_recognition.pt
│   │   └── spacy_hybrid/ → spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/
│   └── setfit/
│       └── introduction_classifier/ → advanced_paper_filtering/results/setfit_*/
│
├── scripts/
│   ├── phase1_classification/
│   │   ├── 01_run_v2_classification.py (copy from validation_spacy_v_BERT/scripts/03a_*)
│   │   ├── 02_run_pycaret_classification.py (copy from validation_spacy_v_BERT/scripts/03b_*)
│   │   └── 03_create_union.py (NEW - merge V2 + PyCaret)
│   │
│   ├── phase2_ner/
│   │   ├── 04_run_v2_ner.py (copy from validation_spacy_v_BERT/scripts/07a_*)
│   │   ├── 05_run_spacy_ner.py (copy from validation_spacy_v_BERT/scripts/09b_*)
│   │   └── 06_extract_pmid_union.py (copy from extract_ner_union_papers.py)
│   │
│   ├── phase3_linguistic/
│   │   └── 07_linguistic_scoring.py (copy from advanced_paper_filtering/scripts/03_*)
│   │
│   ├── phase4_setfit/
│   │   └── 08_setfit_inference.py (copy from advanced_filtering_pipeline/scripts/setup/01_*)
│   │
│   ├── phase5_mapping/
│   │   ├── 09_create_paper_sets.py (copy from advanced_filtering_pipeline/scripts/setup/02_*)
│   │   ├── 10_map_to_entities.py (copy from advanced_filtering_pipeline/scripts/setup/03_*)
│   │   ├── 11_create_primary_resources.py (copy from advanced_filtering_pipeline/scripts/deduplication/09_*)
│   │   ├── 12_add_quality_indicators.py (copy from advanced_filtering_pipeline/scripts/deduplication/10_*)
│   │   └── 13_extract_urls.py (copy from advanced_filtering_pipeline/scripts/deduplication/11_*)
│   │
│   ├── phase6_scanning/
│   │   ├── 14_prepare_urls.py (copy from advanced_filtering_pipeline/scripts/scanning/prepare_*)
│   │   ├── 15_scan_urls.py (copy from advanced_filtering_pipeline/scripts/scanning/scan_gbc_full.py)
│   │   └── 16_merge_scan_scores.py (copy from advanced_filtering_pipeline/scripts/scanning/merge_*)
│   │
│   ├── phase7_deduplication/
│   │   ├── 17_deduplicate_linguistic.py (copy from advanced_filtering_pipeline/scripts/deduplication/14_*)
│   │   ├── 18_analyze_unclear_cases.py (copy from advanced_filtering_pipeline/scripts/deduplication/15_*)
│   │   └── 19_apply_manual_merges.py (copy from advanced_filtering_pipeline/scripts/deduplication/16_*)
│   │
│   └── utils/
│       ├── linguistic_patterns.py
│       ├── config.py
│       └── common_utils.py
│
├── notebooks/
│   ├── phase1_classification/
│   │   ├── v2_classification_colab.ipynb (copy from validation_spacy_v_BERT/notebooks/phase2_v2_classification_150k_VB.ipynb)
│   │   └── pycaret_classification_colab.ipynb (copy from validation_spacy_v_BERT/notebooks/phase2_pycaret_classification_150k_VB.ipynb)
│   │
│   ├── phase2_ner/
│   │   ├── v2_ner_colab.ipynb (copy from validation_spacy_v_BERT/notebooks/phase2_v2_ner_150k_VB.ipynb)
│   │   └── spacy_ner_colab.ipynb (copy from validation_spacy_v_BERT/notebooks/phase2_spacy_ner_150k_VB.ipynb)
│   │
│   └── phase4_setfit/
│       ├── setfit_training_colab.ipynb (copy from advanced_paper_filtering/notebooks/setfit_training_colab.ipynb)
│       └── setfit_inference_colab.ipynb (copy from advanced_paper_filtering/notebooks/setfit_inference_colab.ipynb)
│
├── data/
│   ├── input/
│   │   └── v5.1_cleaned.csv (149,943 papers from EPMC)
│   ├── phase1_classification/
│   │   ├── v2_results.csv
│   │   ├── pycaret_results.csv
│   │   └── union_50k.csv
│   ├── phase2_ner/
│   │   ├── v2_ner_results.csv
│   │   ├── spacy_ner_results.csv
│   │   └── all_paper_pmids.txt (34,279)
│   ├── phase3_linguistic/
│   │   ├── high_score_papers.csv
│   │   ├── medium_score_papers.csv
│   │   └── low_score_papers.csv
│   ├── phase4_setfit/
│   │   └── setfit_introductions.csv
│   ├── phase5_mapping/
│   │   └── papers_with_entities.csv
│   ├── phase6_scanning/
│   │   └── papers_with_url_scores.csv
│   └── phase7_deduplication/
│       └── final_deduplicated_resources.csv (~974)
│
├── config/
│   └── pipeline_config.yaml
│
├── docs/
│   ├── PIPELINE_OVERVIEW.md
│   ├── MODEL_SPECIFICATIONS.md
│   ├── NOTEBOOK_GUIDE.md
│   └── TROUBLESHOOTING.md
│
└── run_pipeline.py (Master orchestrator)
```

---

## Resume Points

The pipeline can be resumed from any phase:

| Resume From | Required Input | Command |
|-------------|---------------|---------|
| **Phase 1** | v5.1_cleaned.csv (149k papers) | `python run_pipeline.py --from phase1` |
| **Phase 2** | union_50k.csv (50k positives) | `python run_pipeline.py --from phase2` |
| **Phase 3** | spacy_ner_*.csv + v2_ner_*.csv | `python run_pipeline.py --from phase3` |
| **Phase 4** | medium_score_papers.csv (20k) | `python run_pipeline.py --from phase4` |
| **Phase 5** | high_score + setfit results | `python run_pipeline.py --from phase5` |
| **Phase 6** | papers_with_entities.csv | `python run_pipeline.py --from phase6` |
| **Phase 7** | papers_with_url_scores.csv | `python run_pipeline.py --from phase7` |

---

## Performance Characteristics

### Total Runtime

| Phase | Time | Bottleneck |
|-------|------|------------|
| Phase 1 | 2-4 hrs | V2 classification (GPU) |
| Phase 2 | 5-10 hrs | V2 NER (GPU) |
| Phase 3 | <1 min | CPU |
| Phase 4 | 30 sec | CPU |
| Phase 5 | 10-15 min | SetFit (GPU) |
| Phase 6 | 5-10 min | CPU |
| Phase 7 | 75-90 min | Network I/O |
| Phase 8 | 5 min + manual | CPU + human |
| **TOTAL** | **8-15 hours** | **GPU availability** |

### Hardware Requirements

**For Scripts (Local)**:
- CPU: Multi-core recommended
- RAM: 16GB minimum
- GPU: Not required (except V2 models extremely slow)
- Storage: 10GB for models + data

**For Notebooks (Google Colab)**:
- V2 Classification: T4 GPU (2-4 hrs) or V100 (1-2 hrs)
- V2 NER: T4 GPU (4-8 hrs) or V100 (2-4 hrs)
- PyCaret: CPU only (FASTER on CPU!)
- spaCy: CPU optimal (100-200 papers/sec)
- SetFit: T4 GPU (10-15 min)

---

## Configuration

### pipeline_config.yaml

```yaml
# Input
input:
  epmc_query: "data/input/v5.1_cleaned.csv"
  total_papers: 149943

# Phase 1: Classification
classification:
  v2:
    model_path: "models/classification/v2_roberta_classifier.pt"
    max_length: 512
    batch_size: 16
    device: "cuda"
  pycaret:
    model_path: "models/classification/pycaret_classifier.pkl"
    test_mode: true
  union:
    logic: "OR"  # V2 positive OR PyCaret positive

# Phase 2: NER
ner:
  v2:
    model_path: "models/ner/v2_roberta_ner.pt"
    batch_size: 8
    device: "cuda"
  spacy:
    model_path: "models/ner/spacy_hybrid"
    batch_size: 64
    device: "cpu"

# Phase 3: Linguistic
linguistic:
  high_score_threshold: 3
  low_score_threshold: 0

# Phase 4: SetFit
setfit:
  model_path: "models/setfit/introduction_classifier"
  batch_size: 32
  device: "cuda"

# Phase 6: URL Scanning
url_scanning:
  workers: 10
  timeout: 30
  wayback_fallback: true

# Phase 7: Deduplication
deduplication:
  url_similarity_threshold: 0.8
  linguistic_similarity_threshold: 0.85
```

---

## Next Steps

1. **Create master orchestrator** (`run_pipeline.py`)
2. **Copy scripts** to unified structure (retain originals)
3. **Create unified config** (merge all configs)
4. **Test end-to-end** with small sample
5. **Document edge cases** and troubleshooting
6. **Create CI/CD** for reproducibility

---

## References

- **Classification Investigation**: `validation_spacy_v_BERT/CLASSIFICATION_*`
- **NER Investigation**: Agent reports (NER pipeline creation)
- **Notebook Inventory**: `COLAB_NOTEBOOKS_*.md`
- **Original Projects**: Retained in place for reference

---

**Design Complete**: 2025-11-20
**Ready for**: Implementation (Tasks 2-3)
