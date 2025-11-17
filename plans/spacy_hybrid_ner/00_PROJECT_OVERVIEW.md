# spaCy Hybrid NER - Project Overview

**Date**: November 12, 2025
**Status**: Approved - Ready for Implementation
**Main Plan**: `plans/2025-11-12_spacy_hybrid_ner_implementation.md`

---

## Executive Summary

### Goal

Build EntityRuler + Statistical NER system for bioresource extraction with alias resolution capability.

### Key Capabilities

1. **High-Precision Known Entity Extraction**: EntityRuler with pattern matching (>95% precision)
2. **Alias Resolution**: Links short/long form names (e.g., "PDB" ↔ "Protein Domain Database")
3. **Generalization to New Entities**: Statistical NER trained via distant supervision
4. **Production-Ready Pipeline**: Packaged spaCy model for deployment

### Timeline

**Total Duration**: 14-20 days (3-4 weeks full-time)

| Week | Phases | Key Deliverables |
|------|--------|------------------|
| Week 1 | Phase 1-2 | Dictionary enriched, EntityRuler validated |
| Week 2 | Phase 3 | Training data (.spacy files) |
| Week 3 | Phase 4-5 | Statistical NER trained, Hybrid pipeline |
| Week 4 | Phase 6 | Production deployment, benchmarks |

---

## Background & Context

### Current State

**Existing NER Models**:
- **V2 NER**: BERT-based, F1=0.749, production-ready
- **Phase 4 Multi-Task**: F1=0.9274 (validation) but has post-processing bug (F1=0.2249 on test)
- **Entity Labels**: Already uses B-COM/I-COM (short names) and B-FUL/I-FUL (full names)

**Key Limitation**: No alias linking capability (doesn't know "PDB" = "Protein Domain Database")

### Available Assets

1. **Bioresource Dictionary**:
   - Location: `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`
   - 4,559 papers, 3,761 unique short names, 1,450 unique full names
   - ⚠️ **60% missing full_name** (2,719 resources)

2. **Training Corpus**: Same 4,559 papers with full text

3. **Metadata**: 21,612 papers with 28-34 enhanced features (from PyCaret study)
   - Location: `data/metadata/pmc_metadata_enhanced_full.csv`

4. **Existing Training Data**: `data/ner_splits_full/` (441 papers, 2,876 samples)

### Problem Statement

**User Goal**: "Run this on novel papers about new bioresources we haven't seen before"

**Required Capabilities**:
1. Extract KNOWN bioresources with high precision
2. Link aliases (PDB ↔ Protein Domain Database)
3. **Discover NEW/unknown bioresources** by generalizing from context
4. Scale to 10-40k papers in production

---

## Architecture Design

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                 spaCy Hybrid NER Pipeline                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. EntityRuler (Rule-Based)                            │
│     ├── patterns.jsonl (~3,000-5,000 patterns)          │
│     ├── Deterministic matching                          │
│     ├── Alias resolution via ent_id_                    │
│     └── Output: Spans with canonical IDs                │
│                                                          │
│  2. Statistical NER (ML-Based)                          │
│     ├── Trained on distant supervision                  │
│     ├── Generalizes to unseen entities                  │
│     ├── Respects EntityRuler's spans                    │
│     └── Output: New entity spans (no IDs)               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Pipeline Execution Flow

```python
# Input: Raw text
text = "We used the Bio-Analytic Resource (BAR) and a new Genomics Repository."

# Step 1: EntityRuler finds known entities
doc_after_ruler = ruler(text)
# Entities: ["Bio-Analytic Resource" (ID=BAR), "BAR" (ID=BAR)]

# Step 2: Statistical NER finds NEW entities
doc_final = statistical_ner(doc_after_ruler)
# Entities: ["Bio-Analytic Resource" (ID=BAR), "BAR" (ID=BAR),
#            "Genomics Repository" (ID=None)]
```

**Critical**: EntityRuler MUST run first so statistical model respects its high-precision matches.

### Entity Label Schema

Reusing existing V2/Phase 4 labels:

| Label | Description | Example | Source |
|-------|-------------|---------|--------|
| B-COM | Begin - Common/Short name | "PDB" | EntityRuler or Statistical |
| I-COM | Inside - Common name | N/A | Statistical |
| B-FUL | Begin - Full name | "Protein Domain Database" | EntityRuler or Statistical |
| I-FUL | Inside - Full name | "Domain Database" | EntityRuler or Statistical |
| O | Outside (not entity) | "the", "and" | Statistical |

**Alias Resolution**: `ent.ent_id_` stores canonical ID (e.g., "PDB" for both "PDB" and "Protein Domain Database")

---

## Phase Overview

### Phase 1: Data Preparation & Dictionary Enrichment (3-4 days)
**Focus**: Build comprehensive bioresource dictionary with 70-80% alias coverage

**Scripts**:
- `01_extract_bioresource_dictionary.py`
- `02_enrich_missing_fullnames.py`
- `03_generate_patterns_jsonl.py`

**Output**: `data/patterns.jsonl` (~3,000-5,000 patterns)

### Phase 2: EntityRuler Baseline (2-3 days)
**Focus**: Validate EntityRuler achieves >95% precision before investing in training

**Scripts**:
- `04_test_entityruler_pipeline.py`
- `05_validate_entityruler.py`

**Output**: Precision >95%, Coverage 70-80%

### Phase 3: Distant Supervision Training Data (4-5 days)
**Focus**: Create spaCy-compatible training data (.spacy format)

**Scripts**:
- `06_prepare_training_corpus.py`
- `07_distant_supervision_annotation.py`

**Output**: `data/ner_training/*.spacy` files

### Phase 4: Statistical NER Training (1-2 days)
**Focus**: Train statistical NER model on GPU using distant supervision data

**Notebook**: `notebooks/spacy_ner_training.ipynb` (Google Colab)

**Output**: `models/ner_statistical/` (Test F1 >70%)

### Phase 5: Hybrid Pipeline Integration (2-3 days)
**Focus**: Combine EntityRuler + Statistical NER into production pipeline

**Scripts**:
- `09_build_hybrid_pipeline.py`
- `10_validate_hybrid_pipeline.py`
- `11_benchmark_hybrid_speed.py`
- `12_analyze_alias_resolution.py`

**Output**: `models/ner_hybrid_v2_com_ful/`

### Phase 6: Production Deployment (2-3 days)
**Focus**: Package pipeline and integrate with existing infrastructure

**Deliverables**:
- `packages/en_ner_hybrid_bioresource-1.0.0/`
- `src/ner_predict_spacy.py`
- `notebooks/spacy_full_inference_v5.ipynb`

---

## Success Criteria

### Technical Requirements

- [ ] EntityRuler achieves >95% precision on known entities
- [ ] Statistical NER achieves >70% F1 on test set
- [ ] Hybrid pipeline successfully combines both components
- [ ] Pipeline order verified: EntityRuler → Statistical NER
- [ ] Alias resolution works for 70-80% of entities
- [ ] Speed: >50 papers/sec on CPU

### Scientific Requirements

- [ ] Discovers NEW bioresources not in dictionary (key goal!)
- [ ] Links short/long form aliases correctly (e.g., PDB ↔ Protein Domain Database)
- [ ] Outperforms baseline on recall (+10-15% coverage)
- [ ] Maintains V2-level precision (~75-80%)

### Production Requirements

- [ ] Packaged spaCy pipeline ready for deployment
- [ ] Integration scripts for existing pipeline
- [ ] Comprehensive documentation
- [ ] Benchmarks vs existing models
- [ ] Scales to 10-40k papers

---

## Key Design Decisions

### Why spaCy Instead of HuggingFace Transformers?

**Current System**: V2/Phase 4 use HuggingFace BERT (token classification)

**New System**: spaCy EntityRuler + spaCy Statistical NER

**Rationale**:
1. **Hybrid Architecture**: spaCy designed for EntityRuler + NER combination
2. **Alias Resolution**: EntityRuler's `ent_id_` attribute built for this
3. **Production-Ready**: spaCy pipelines package easily, serve efficiently
4. **Research Alignment**: Implements Strategy 3 from research document exactly

**Trade-off**: Cannot directly reuse existing BERT models (different frameworks)

### Why Distant Supervision Instead of Manual Annotation?

**Approach**: Auto-annotate 4,559 papers using dictionary matches

**Rationale**:
1. **Scale**: 4,559 papers × 2-4 entities = ~10k annotations (would take weeks manually)
2. **Cost**: $0 vs thousands of dollars for manual annotation
3. **Research Validation**: Distant supervision is proven effective for NER
4. **Quality**: Expected F1 >70% is acceptable for discovery task

**Trade-off**: Lower quality than manual annotations (noisy labels)

### Why EntityRuler Before Statistical NER?

**Pipeline Order**: `nlp.pipe_names = ["entity_ruler", "ner"]`

**Critical Importance**:
- EntityRuler finds known entities with 100% precision
- Statistical NER respects these spans (doesn't overwrite)
- Statistical NER fills in gaps (finds NEW entities)
- Prevents "catastrophic forgetting" of known entities

**Wrong Order**: Statistical NER → EntityRuler
- Statistical model might mislabel "PDB" → EntityRuler blocked from correcting
- Wastes computation (statistical model tries to find known entities)

---

## File Structure

```
inventory_2022/
├── data/
│   ├── bioresource_dictionary_raw.json
│   ├── bioresource_dictionary_enriched.json
│   ├── patterns.jsonl
│   ├── ner_corpus_splits/
│   │   ├── train.csv
│   │   ├── dev.csv
│   │   └── test.csv
│   └── ner_training/
│       ├── train.spacy
│       ├── dev.spacy
│       ├── test.spacy
│       └── config.cfg
│
├── scripts/
│   ├── 01_extract_bioresource_dictionary.py
│   ├── 02_enrich_missing_fullnames.py
│   ├── 03_generate_patterns_jsonl.py
│   ├── 04_test_entityruler_pipeline.py
│   ├── 05_validate_entityruler.py
│   ├── 06_prepare_training_corpus.py
│   ├── 07_distant_supervision_annotation.py
│   ├── 09_build_hybrid_pipeline.py
│   ├── 10_validate_hybrid_pipeline.py
│   ├── 11_benchmark_hybrid_speed.py
│   ├── 12_analyze_alias_resolution.py
│   └── 13_benchmark_all_models.py
│
├── notebooks/
│   ├── spacy_ner_training.ipynb
│   └── spacy_full_inference_v5.ipynb
│
├── models/
│   ├── ner_statistical/
│   └── ner_hybrid_v2_com_ful/
│
├── packages/
│   └── en_ner_hybrid_bioresource-1.0.0/
│
├── src/
│   └── ner_predict_spacy.py
│
└── results/
    ├── phase2_entityruler_validation.json
    ├── phase5_hybrid_validation.json
    └── phase6_model_comparison.csv
```

---

## References

### Research Documents
- **Primary**: `docs/research_docs/ner_implementation.md` (Strategy 3: Hybrid)
- **V2 vs PyCaret**: `docs/V2_PYCARET_COMPARISON_STUDY.md`
- **Project Context**: `docs/starting_doc.md`

### spaCy Documentation
- EntityRuler: https://spacy.io/api/entityruler
- Training: https://spacy.io/usage/training
- DocBin: https://spacy.io/api/docbin
- Pipeline Architecture: https://spacy.io/usage/processing-pipelines

### Code References
- V2 NER: `src/ner_train.py`
- Phase 4 Multi-Task: `src/models/multitask_model.py`
- Entity Constants: `src/inventory_utils/constants.py`

---

## Quick Start

### For AI Agents

**To work on a specific phase**, read:
1. This overview (context)
2. The specific phase document (e.g., `01_DATA_PREPARATION_PHASES_1_2.md`)
3. `05_SCRIPTS_INDEX.md` (find relevant scripts)
4. `04_TROUBLESHOOTING_AND_RISKS.md` (if encountering issues)

**Do not read the full plan** (`plans/2025-11-12_spacy_hybrid_ner_implementation.md`) unless you need complete context.

### For Developers

1. **Start here**: Read this overview
2. **Phase 1-2**: See `01_DATA_PREPARATION_PHASES_1_2.md`
3. **Phase 3-4**: See `02_TRAINING_PHASES_3_4.md`
4. **Phase 5-6**: See `03_DEPLOYMENT_PHASES_5_6.md`
5. **Troubleshooting**: See `04_TROUBLESHOOTING_AND_RISKS.md`
6. **Scripts**: See `05_SCRIPTS_INDEX.md`

---

**Status**: ✅ Ready for Implementation
**Next Step**: Begin Phase 1 (Data Preparation)
