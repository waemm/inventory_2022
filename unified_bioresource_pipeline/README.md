# Unified Bioresource Pipeline

**Version:** 1.0.0
**Date:** 2025-11-20
**Status:** Complete & Ready for Use

---

## Overview

The **Unified Bioresource Pipeline** is a complete, reproducible end-to-end system for discovering, extracting, and deduplicating bioresource mentions from scientific literature. This pipeline consolidates multiple ML models, filtering strategies, and validation steps into a single coordinated workflow.

### Key Features

- **🔄 Fully Reproducible:** Every step from EPMC query to final resources
- **⏸️ Resume Capability:** Start from any phase with checkpoints
- **🤖 Multiple ML Models:** RoBERTa, PyCaret, spaCy, SetFit
- **📊 Comprehensive Validation:** URL scanning, linguistic filtering, deduplication
- **📝 Complete Documentation:** Every script, model, and decision documented
- **🚀 Production Ready:** Used to generate 1,945 validated bioresources

---

## Pipeline Architecture

```
149,943 EPMC Papers (2011-2021, Query V5.1)
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 1: CLASSIFICATION (V2 RoBERTa + PyCaret)           │
│ • V2: 12,285 positives (8.2%)                            │
│ • PyCaret: 45,766 positives (30.6%)                      │
│ • Union: 50,192 positives (33.5%)                        │
│ Time: 2-4 hours (GPU)                                     │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 2: NER (V2 RoBERTa + spaCy Hybrid)                 │
│ • V2 NER: 18,319 papers, 67,187 entities                 │
│ • spaCy Hybrid: 32,317 papers, 117,491 entities          │
│ • Union: 34,279 unique papers                             │
│ Time: 5-10 hours (GPU + CPU)                              │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 3: LINGUISTIC FILTERING                             │
│ • High score (≥3): 8,648 introductions (25.2%)           │
│ • Medium score (0-2): 20,816 papers (60.7%)              │
│ • Low score (<0): 4,796 usage papers (14.0%)             │
│ Time: ~30 seconds                                         │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 4: SETFIT CLASSIFICATION (Medium confidence)       │
│ • Input: 20,816 medium-score papers                       │
│ • SetFit: ~7,800 additional introductions                 │
│ • Total: ~16,605 introductions (High + SetFit)           │
│ Time: 10-15 minutes (GPU on Colab)                        │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 5: ENTITY MAPPING & RESOURCE CREATION              │
│ • Map papers to NER entities                              │
│ • Create primary resource CSV                             │
│ • Add quality indicators                                  │
│ • Extract URLs                                            │
│ Time: 5-10 minutes                                        │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 6: URL SCANNING & VALIDATION                       │
│ • Multi-threaded URL scanning                             │
│ • Wayback Machine fallback                                │
│ • Quality scoring (domain, content, metadata)            │
│ Time: 75-90 minutes                                       │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 7: DEDUPLICATION                                    │
│ • Linguistic similarity (URL + entity matching)          │
│ • Manual review of unclear cases                          │
│ • Apply manual merge decisions                            │
│ Time: 5 minutes + manual review                           │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 8: URL RECOVERY (NEW)                              │
│ • Identify records missing URLs (~25%)                   │
│ • Search abstracts & fulltext (EPMC API)                 │
│ • Prepare web search chunks for agents                   │
│ • Merge agent results back                               │
│ Time: ~5 min (automated) + agent web search              │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 9: FINALIZATION                                     │
│ • Merge recovered URLs into inventory                    │
│ • Add final quality indicators                           │
│ • Generate final bioresource output                      │
│ Time: 5-10 minutes                                        │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ PHASE 10: POST-PROCESSING QC (NEW)                       │
│ • Analyze best_name column for quality issues            │
│ • Detect: empty, numeric, short, bracketed names         │
│ • Agent-based analysis in ~500 row chunks                │
│ • Auto-fix with confidence levels + manual review flags  │
│ Time: ~10 minutes (3 parallel agents)                    │
└───────────────────────────────────────────────────────────┘
    ↓
~1,945 Unique Validated Bioresources ✅
```

---

## Quick Start

### 1. Run Complete Pipeline

```bash
cd unified_bioresource_pipeline
python run_pipeline.py --full
```

### 2. Resume from Specific Phase

```bash
# Resume from PMID extraction (skip Classification + NER)
python run_pipeline.py --from phase3

# Resume from SetFit (skip Linguistic filtering)
python run_pipeline.py --from phase4
```

### 3. Check Pipeline Status

```bash
python run_pipeline.py --status
```

### 4. Preview Without Execution

```bash
python run_pipeline.py --full --dry-run
```

### 5. List All Phases

```bash
python run_pipeline.py --list-phases
```

---

## Directory Structure

```
unified_bioresource_pipeline/
├── run_pipeline.py           # Master orchestrator
│
├── config/
│   └── pipeline_config.yaml  # Complete configuration
│
├── scripts/
│   ├── phase1_classification/
│   │   ├── 01_run_v2_classification.py
│   │   └── 02_run_pycaret_classification.py
│   ├── phase2_ner/
│   │   ├── 04_run_v2_ner.py
│   │   ├── 05_run_spacy_ner.py
│   │   └── 06_extract_pmid_union.py
│   ├── phase3_linguistic/
│   │   └── 07_linguistic_scoring.py
│   ├── phase4_setfit/
│   │   └── 08_setfit_inference.py
│   ├── phase5_mapping/
│   │   ├── 09_create_paper_sets.py
│   │   ├── 10_map_to_entities.py
│   │   ├── 11_create_primary_resources.py
│   │   ├── 12_add_quality_indicators.py
│   │   └── 13_extract_urls.py
│   ├── phase6_scanning/
│   │   ├── 14_prepare_urls.py
│   │   ├── 15_scan_urls.py
│   │   └── 16_merge_scan_scores.py
│   ├── phase7_deduplication/
│   │   ├── 17_deduplicate_linguistic.py
│   │   ├── 18_analyze_unclear_cases.py
│   │   └── 19_apply_manual_merges.py
│   ├── phase8_url_recovery/          # URL recovery for missing URLs
│   │   ├── url_patterns.py           # Shared patterns & exclusions
│   │   ├── 28_identify_missing_urls.py
│   │   ├── 29_fetch_abstracts.py
│   │   ├── 30_search_abstracts_urls.py
│   │   ├── 31_fetch_fulltext.py
│   │   ├── 32_search_fulltext_urls.py
│   │   ├── 33_consolidate_recovery.py
│   │   ├── 34_merge_websearch_results.py
│   │   └── run_phase8.py             # Phase orchestrator
│   ├── phase9_finalization/
│   │   ├── 22_filter_novel_resources.py
│   │   └── ...
│   └── post_processing/              # NEW - Phase 10 QC
│       ├── README.md
│       ├── docs/AGENT_PROMPT_best_name_qc.md
│       └── merge_and_fix_inventory.py
│
├── notebooks/
│   ├── phase1_classification/
│   │   ├── v2_classification_colab.ipynb
│   │   └── pycaret_classification_colab.ipynb
│   ├── phase2_ner/
│   │   ├── v2_ner_colab.ipynb
│   │   └── spacy_ner_colab.ipynb
│   └── phase4_setfit/
│       └── setfit_inference_colab.ipynb
│
├── models/
│   ├── classification/       # Link to RoBERTa V2 + PyCaret models
│   ├── ner/                  # Link to RoBERTa V2 + spaCy models
│   └── setfit/               # Link to SetFit models
│
├── data/
│   ├── input/                # EPMC query results (149,943 papers)
│   ├── phase1_classification/
│   ├── phase2_ner/
│   ├── phase3_linguistic/
│   ├── phase4_setfit/
│   ├── phase5_mapping/
│   ├── phase6_scanning/
│   └── phase7_deduplication/
│
├── docs/
│   ├── PIPELINE_OVERVIEW.md
│   ├── MODEL_SPECIFICATIONS.md
│   ├── NOTEBOOK_GUIDE.md
│   └── TROUBLESHOOTING.md
│
└── logs/
    └── pipeline/             # Execution logs
```

---

## Models & Technologies

### Phase 1: Classification

**V2 RoBERTa Text Classifier**
- Architecture: `RobertaForSequenceClassification` (HuggingFace)
- Input: Title + Abstract (max 512 tokens)
- Training: 2,000+ labeled papers
- Performance: F1=0.898
- Model: `../out/original_model/article_classifier.pt`

**PyCaret Metadata Classifier**
- Features: 91 engineered (MeSH, journals, pub types)
- Training: Scikit-learn ensemble
- Performance: Complements V2 (high recall)
- Model: `../pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl`

### Phase 2: NER

**V2 RoBERTa NER**
- Architecture: `RobertaForTokenClassification` (HuggingFace)
- Labels: COM (common name), FUL (full name)
- Performance: F1=0.749
- Model: `../out/original_model/named_entity_recognition.pt` (473 MB)

**spaCy Hybrid NER**
- Components: EntityRuler (6,216 patterns) + Statistical NER
- Speed: 100-200 papers/sec (CPU)
- Coverage: 32,317 papers, 117,491 entities
- Model: `../spacy_hybrid_ner/models/ner_hybrid_v2_com_ful`

### Phase 4: SetFit

**SetFit Introduction Classifier**
- Architecture: Sentence Transformers (few-shot learning)
- Training: 40 examples (20 intro, 20 usage)
- Use Case: Classify medium-confidence papers
- Model: `../advanced_paper_filtering/results/setfit_*/setfit_introduction_classifier/`

---

## Resume Points

The pipeline can resume from any phase:

| Resume From | Required Input | Command |
|-------------|----------------|---------|
| **Phase 1** | EPMC v5.1 (149k papers) | `--from phase1` |
| **Phase 2** | Classification union (50k) | `--from phase2` |
| **Phase 3** | NER results (34k papers) | `--from phase3` ⭐ Common |
| **Phase 4** | Linguistic scores (21k medium) | `--from phase4` |
| **Phase 5** | SetFit introductions (16k) | `--from phase5` |
| **Phase 6** | Papers with entities | `--from phase6` |
| **Phase 7** | Papers with URL scores | `--from phase7` |
| **Phase 8** | Deduplicated resources | `--from phase8` |
| **Phase 9** | URL-recovered resources | `--from phase9` |
| **Phase 10** | Final inventory | `--from phase10` ⭐ NEW |

**Most Common:** Resume from **Phase 3** (PMID extraction) if you already have NER results.

---

## Performance

### Total Runtime

| Phase | Time | GPU Required |
|-------|------|--------------|
| Phase 1 | 2-4 hrs | ✓ Yes (V2) |
| Phase 2 | 5-10 hrs | ✓ Yes (V2 NER) |
| Phase 3 | <1 min | ✗ No |
| Phase 4 | 10-15 min | ✓ Yes (SetFit) |
| Phase 5 | 5-10 min | ✗ No |
| Phase 6 | 75-90 min | ✗ No |
| Phase 7 | 5 min + manual | ✗ No |
| Phase 8 | ~5 min + agents | ✗ No |
| Phase 9 | 5-10 min | ✗ No |
| Phase 10 | ~10 min | ✗ No |
| **TOTAL** | **8-16 hours** | GPU phases: 7-15 hrs |

### Hardware Requirements

**Google Colab (GPU Phases)**
- V2 Classification: T4 GPU (2-4 hrs) or V100 (1-2 hrs)
- V2 NER: T4 GPU (4-8 hrs) or V100 (2-4 hrs)
- SetFit: T4 GPU (10-15 min)

**Local Machine (CPU Phases)**
- CPU: Multi-core recommended
- RAM: 16GB minimum
- Storage: 10GB for models + data
- Network: For URL scanning

---

## Configuration

All settings are in `config/pipeline_config.yaml`:

```yaml
# Example: Adjust thresholds
linguistic:
  high_score_threshold: 3    # Change to 4 for higher precision
  low_score_threshold: 0

# Example: Adjust URL scanning
url_scanning:
  workers: 10                # Increase for faster scanning
  timeout: 30
  wayback_fallback: true

# Example: Adjust deduplication
deduplication:
  url_similarity_threshold: 0.8
  linguistic_similarity_threshold: 0.85
```

---

## Manual Steps

### Phase 1 & 2: Run Notebooks on Google Colab

**Reason:** GPU-accelerated inference requires Google Colab

**Steps:**
1. Upload notebooks from `notebooks/phase1_classification/` or `phase2_ner/`
2. Upload EPMC data to Colab
3. Run notebook cells sequentially
4. Download results to `data/phase*_*/`
5. Confirm completion when prompted by orchestrator

### Phase 4: SetFit on Colab

**Reason:** SetFit requires GPU for efficient inference

**Steps:**
1. Upload `notebooks/phase4_setfit/setfit_inference_colab.ipynb`
2. Upload medium-score papers
3. Run inference
4. Download results to `data/phase4_setfit/`

### Phase 7: Manual Merge Review

**Reason:** Some duplicates require human judgment

**Steps:**
1. Review `data/phase7_deduplication/unclear_cases.csv`
2. Assign merge groups in `merge_group` column
3. Save as `manual_merges.csv`
4. Run script 19 to apply merges

---

## Outputs

### Intermediate Outputs

- `data/phase1_classification/union_50k.csv` - 50,192 classified papers
- `data/phase2_ner/all_paper_pmids.txt` - 34,279 papers with entities
- `data/phase3_linguistic/high_score_papers.csv` - 8,648 high-confidence introductions
- `data/phase4_setfit/setfit_introductions.csv` - ~7,800 SetFit introductions
- `data/phase5_mapping/papers_with_entities.csv` - Papers mapped to resources
- `data/phase6_scanning/papers_with_url_scores.csv` - URL-validated resources

### Final Output

**`data/phase7_deduplication/final_deduplicated_resources.csv`**

~974 unique bioresources with:
- Resource name (COM and FUL variants)
- Source paper PMIDs
- URLs (validated)
- Quality indicators
- Confidence scores

---

## Troubleshooting

### Issue: GPU Out of Memory

**Solution:** Reduce batch size in `config/pipeline_config.yaml`
```yaml
classification:
  v2:
    batch_size: 8  # Reduce from 16
```

### Issue: URL Scanning Slow

**Solution:** Increase workers
```yaml
url_scanning:
  workers: 20  # Increase from 10
```

### Issue: Missing Input Files

**Solution:** Check status and verify phase outputs
```bash
python run_pipeline.py --status
```

### Issue: Script Fails

**Solution:** Check logs
```bash
cat logs/pipeline/phase*_*_*.log
```

---

## Documentation

### Core Documents

- **[PIPELINE_OVERVIEW.md](docs/PIPELINE_OVERVIEW.md)** - Detailed pipeline explanation
- **[MODEL_SPECIFICATIONS.md](docs/MODEL_SPECIFICATIONS.md)** - Model architectures & performance
- **[NOTEBOOK_GUIDE.md](docs/NOTEBOOK_GUIDE.md)** - How to run notebooks on Colab
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues & solutions

### Design Documents

- **[Consolidated Pipeline Design](../docs/plans/2025-11-20_consolidated_pipeline_design.md)** - Complete architecture
- **[Original Workflow](../docs/starting_doc.md)** - Context & background

---

## Version History

**v1.3.0** (2025-12-05)
- Added Phase 10: Post-Processing QC
  - Agent-based best_name quality control analysis
  - Detects: empty, numeric, short, bracketed, suspicious character names
  - Auto-fix with confidence levels (HIGH/MEDIUM/LOW)
  - Manual review flags for low-confidence fixes
  - Preserves original names in `best_name_original` column
- New files: `post_processing/` directory with agent prompts and merge script
- Session z381s: 61 issues found (4.0%), all auto-fixed, 2 flagged for manual review

**v1.2.0** (2025-11-29)
- Phase 10 Data Quality Improvements:
  - Script 23: Name disambiguation using URL subdomains (e.g., GXB → GXB (breastcancer))
  - Script 23: Auto-capitalize short names, sanitize non-ASCII chars (ø→o, é→e, μ→mu)
  - Script 23: Recover names from URL when NER produced encoding issues
  - Script 24: Block repository URLs (bitbucket, gitlab, sourceforge)
  - Script 24: Block file download URLs (.pdf, .xlsx, .zip, .tar.gz)
  - Added audit trail columns: best_name_original, name_modification_flags, url_validation
- Final inventory: 1,945 resources (up from 1,365)

**v1.1.0** (2025-11-28)
- Added Phase 8: URL Recovery
  - 7 new scripts for recovering URLs from abstracts/fulltext
  - Agent-based web search with strict output spec
  - Automated merge of agent results
- Phase 9: Finalization (renamed from Phase 8)
- Updated documentation

**v1.0.0** (2025-11-20)
- Initial unified pipeline release
- 18 scripts organized by phase
- 5 production notebooks
- Complete configuration system
- Master orchestrator with resume capability
- Comprehensive documentation

---

## Citation

If you use this pipeline in your research, please cite:

```bibtex
@software{unified_bioresource_pipeline,
  title = {Unified Bioresource Pipeline},
  author = {[Your Team]},
  year = {2025},
  version = {1.0.0},
  url = {[Repository URL]}
}
```

---

## License

[Your License Here]

---

## Contact

For questions or issues:
1. Check `docs/TROUBLESHOOTING.md`
2. Review logs in `logs/pipeline/`
3. Consult original project documentation

---

**Status:** ✅ Production Ready
**Last Updated:** 2025-12-05
**Tested On:** 149,943 papers (EPMC 2011-2021) + 98,571 papers (2022-mid2025)
**Output:** 1,510+ validated unique bioresources (with Phase 10 QC)
