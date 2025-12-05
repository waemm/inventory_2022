# Bioresource Pipeline Execution Guide

**Purpose**: Step-by-step guide for running the bioresource extraction pipeline on new data.

**Last Updated**: 2025-12-02
**Validated On**: 2022-mid2025 dataset (98,571 papers → 27,975 positives → 68,149 entities)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Directory Structure](#directory-structure)
4. [Phase 1: Classification](#phase-1-classification)
5. [Phase 2: Named Entity Recognition](#phase-2-named-entity-recognition)
6. [Phase 3-9: Downstream Processing](#phase-3-9-downstream-processing)
7. [Key Learnings & Troubleshooting](#key-learnings--troubleshooting)
8. [File Reference](#file-reference)

---

## Overview

The pipeline extracts bioresource mentions from scientific papers through:

1. **Classification**: Identify papers likely describing bioresources (V2 RoBERTa + PyCaret)
2. **NER**: Extract entity mentions from classified papers (V2 BERT + spaCy Hybrid)
3. **Post-processing**: Linguistic scoring, deduplication, URL extraction, validation

### Key Architecture Decisions

| Component | Where to Run | Why |
|-----------|--------------|-----|
| V2 RoBERTa Classification | **Colab (GPU)** | Large transformer model, GPU speeds up 10x |
| PyCaret Classification | **Local (CPU)** | Lightweight ML model, fast on CPU |
| V2 BERT NER | **Colab (GPU)** | Large transformer model |
| spaCy Hybrid NER | **Local only** | Model on Google Drive is broken; local model has tok2vec fix |

---

## Prerequisites

### 1. Environments

```bash
# For spaCy NER (local)
cd /Users/warren/development/GBC/inventory_2022
source spacy_hybrid_ner/venv/bin/activate

# For PyCaret (local)
source pycaret_env/bin/activate
# OR
source biodata_modern_env/bin/activate
```

### 2. Models Required

| Model | Path | Size | Used By |
|-------|------|------|---------|
| V2 Classification | `out/original_model/article_classifier.pt` | 476 MB | Colab notebook |
| V2 NER | `out/original_model/named_entity_recognition.pt` | 473 MB | Colab notebook |
| PyCaret | `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl` | 184 KB | Local script |
| spaCy Hybrid | `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/` | 34 MB | **Local script only** |

### 3. Input Data Format

Your input CSV must have:
- `id` or `publication_id`: Unique identifier
- `title`: Paper title
- `abstract`: Paper abstract
- For PyCaret: Additional metadata columns (meshTerms, pubType, citedByCount, etc.)

---

## Directory Structure

```
unified_bioresource_pipeline/
├── config/
│   └── pipeline_config.yaml          # Pipeline configuration
├── data/
│   ├── input/                         # Input data files
│   ├── phase1_classification/         # Classification outputs
│   ├── phase2_ner/                    # NER outputs
│   └── ...                            # Other phase outputs
├── notebooks/
│   ├── phase1_classification/
│   │   ├── v2_classification_2022_mid2025.ipynb    # V2 on Colab
│   │   └── pycaret_classification_2022_mid2025.ipynb
│   └── phase2_ner/
│       ├── v2_ner_2022_mid2025.ipynb              # V2 NER on Colab
│       └── spacy_ner_2022_mid2025.ipynb           # DO NOT USE - broken
├── scripts/
│   ├── phase1_classification/
│   │   └── 02_run_pycaret_local.py    # PyCaret local script ✓
│   └── phase2_ner/
│       └── run_spacy_full_hybrid_local.py  # spaCy local script ✓
└── docs/
    └── PIPELINE_EXECUTION_GUIDE.md    # This file
```

---

## Phase 1: Classification

**Goal**: Identify papers likely describing bioresources from ~100k papers down to ~25-30k candidates.

### Step 1.1: V2 RoBERTa Classification (Colab)

**Script**: `notebooks/phase1_classification/v2_classification_2022_mid2025.ipynb`

**Run on**: Google Colab with T4 GPU

**Process**:
1. Upload notebook to Google Colab
2. Set `TEST_MODE = False` for production
3. Run all cells
4. Results saved to `data/phase1_classification/v2_classification_98k_{session_id}.csv`

**Expected Output**:
- ~6-8% positive rate
- Example: 98,571 papers → 6,645 positives (6.7%)

**Key Code** (uses correct model loading):
```python
from inventory_utils.filing import get_classif_model

with open(MODEL_PATH, 'rb') as f:
    model, model_name = get_classif_model(f, device)
# model_name will be: allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500
```

### Step 1.2: PyCaret Classification

PyCaret can be run **locally** (recommended) or on **Google Colab**.

#### Option A: Run Locally (Recommended)

**Script**: `scripts/phase1_classification/02_run_pycaret_local.py`

**Run on**: Local machine (CPU)

#### Option B: Run on Google Colab

**Script**: `notebooks/phase1_classification/pycaret_classification_2022_mid2025.ipynb`

**Run on**: Google Colab (CPU is fine)

⚠️ **IMPORTANT: Colab Runtime Configuration**

1. **Change runtime version**: Go to `Runtime` → `Change runtime type` → Select **Python 3.11 (2025.07)** or similar 2025.x version
2. **First run will crash**: When you first run the notebook, it will crash with a **numpy error**
3. **Fix**: Simply go to `Runtime` → `Restart and run all` - the second run will work correctly

This numpy error occurs because PyCaret installs dependencies that conflict with the pre-installed numpy version. The restart resolves the conflict.

---

**Local execution** (recommended)

**Process**:
```bash
cd /Users/warren/development/GBC/inventory_2022
source pycaret_env/bin/activate
python unified_bioresource_pipeline/scripts/phase1_classification/02_run_pycaret_local.py
```

**Expected Output**:
- ~25-27% positive rate
- Example: 95,393 papers → 25,476 positives (26.7%)
- Runtime: ~30-60 seconds

**Output Files**:
- `data/phase1_classification/pycaret_classification_98k_{session_id}.csv`
- `data/phase1_classification/pycaret_summary_{session_id}.json`

### Step 1.3: Create Classification Union

**Logic**: Paper is positive if V2 OR PyCaret predicts positive.

**Manual Process** (or create script):
```python
import pandas as pd

# Load both results
v2 = pd.read_csv('data/phase1_classification/v2_classification_98k_{session}.csv')
pycaret = pd.read_csv('data/phase1_classification/pycaret_classification_98k_{session}.csv')

# Merge on publication_id
merged = v2.merge(pycaret[['publication_id', 'pycaret_positive']], on='publication_id', how='outer')

# Union: positive if either is positive
merged['union_positive'] = ((merged['v2_positive'] == 1) | (merged['pycaret_positive'] == 1)).astype(int)

# Filter to positives only
union = merged[merged['union_positive'] == 1]
union.to_csv('data/phase1_classification/classification_union.csv', index=False)
```

**Expected Output**:
- ~28-30% of original papers
- Example: 98,571 papers → 27,975 union positives (28.4%)

---

## Phase 2: Named Entity Recognition

**Goal**: Extract bioresource entity mentions from classified papers.

### Step 2.1: V2 BERT NER (Colab)

**Script**: `notebooks/phase2_ner/v2_ner_2022_mid2025.ipynb`

**Run on**: Google Colab with T4 GPU

**Process**:
1. Upload notebook to Google Colab
2. Ensure `classification_union.csv` is on Google Drive
3. Run all cells
4. Results saved to `data/phase2_ner/v2_ner_results_{session_id}.csv`

**Expected Output**:
- ~35,000-40,000 entities
- ~10,000-12,000 papers with entities
- Runtime: 1-2 hours on T4 GPU

**Key Code** (uses correct model loading):
```python
from src.ner_predict import predict_sequence
from inventory_utils.filing import get_ner_model

with open(MODEL_PATH, 'rb') as f:
    model, model_name, tokenizer = get_ner_model(f, device)
# model_name will be: allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500
```

### Step 2.2: spaCy Full Hybrid NER (LOCAL ONLY)

⚠️ **CRITICAL**: spaCy NER MUST be run locally. The model on Google Drive is missing the `tok2vec` component.

**Script**: `scripts/phase2_ner/run_spacy_full_hybrid_local.py`

**Run on**: Local machine (CPU)

**Process**:
```bash
cd /Users/warren/development/GBC/inventory_2022
source spacy_hybrid_ner/venv/bin/activate
python unified_bioresource_pipeline/scripts/phase2_ner/run_spacy_full_hybrid_local.py
```

**Expected Output**:
- ~65,000-70,000 entities
- ~65-70% paper coverage
- Entity source breakdown: ~30% ruler, ~70% statistical
- Runtime: ~40-60 minutes

**Output Files**:
- `data/phase2_ner/spacy_ner_results_{session_id}.csv`
- `data/phase2_ner/spacy_ner_results.csv` (copy for pipeline)
- `data/phase2_ner/benchmarks/spacy_ner_benchmark_{session_id}.json`

**Verification** - Check the benchmark shows all 3 components:
```json
{
  "model": {
    "components": ["entity_ruler", "tok2vec", "ner"]  // All 3 required!
  },
  "results": {
    "total_entities": 68149,
    "entities_with_canonical_id": 14445  // ~21% from ruler
  }
}
```

### Step 2.3: Create NER Union

**Logic**: Entity is included if found by V2 OR spaCy.

**Script**: `scripts/phase2_ner/06_extract_pmid_union.py` (or manual)

**Expected Output**:
- Combined unique entities from both systems
- Deduplication by (paper_id, mention, label)

---

## Phase 3-9: Downstream Processing

After NER, the pipeline continues with:

| Phase | Script(s) | Purpose |
|-------|-----------|---------|
| 3 | `scripts/phase3_linguistic/07_linguistic_scoring.py` | Score entities linguistically |
| 4 | `scripts/phase4_setfit/08_setfit_inference.py` | SetFit classification |
| 5 | `scripts/phase5_mapping/09-13_*.py` | Create paper sets, map entities |
| 6 | `scripts/phase6_scanning/14-19_*.py` | URL extraction and scanning |
| 7 | `scripts/phase7_deduplication/17-19_*.py` | Deduplicate resources |
| 8 | `scripts/phase8_url_recovery/28-34_*.py` | URL recovery (abstract/fulltext/web search) |
| 9 | `scripts/phase9_finalization/22-27_*.py` | Final inventory generation |

---

## Phase 8: URL Recovery

**Goal**: Recover URLs for resources that didn't have URLs from initial extraction.

### Overview

Phase 8 uses a 3-stage approach:
1. **Abstract search** - Search for URLs in paper abstracts
2. **Fulltext search** - Fetch fulltext from PMC and search for URLs
3. **Web search agents** - Use AI agents to search the web for remaining resources

### Stage 1: Abstract URL Search

**Script**: `scripts/phase8_url_recovery/30_search_abstracts.py`

```bash
python scripts/phase8_url_recovery/30_search_abstracts.py \
    --input data/phase8_url_recovery/missing_urls_prepared.csv \
    --abstracts data/phase8_url_recovery/abstracts_cache.json \
    --output-dir data/phase8_url_recovery
```

**Expected**: Low yield (~0.3% - URLs rarely in abstracts)

### Stage 2: Fulltext URL Search

**Scripts**:
```bash
# Step 1: Fetch fulltext from PMC
python scripts/phase8_url_recovery/31_fetch_fulltext.py \
    --input data/phase8_url_recovery/abstract_url_results.csv \
    --abstracts data/phase8_url_recovery/abstracts_cache.json \
    --output-dir data/phase8_url_recovery \
    --rate-limit 0.1

# Step 2: Search fulltext for URLs
python scripts/phase8_url_recovery/32_search_fulltext.py \
    --input data/phase8_url_recovery/abstract_url_results.csv \
    --fulltext data/phase8_url_recovery/fulltext_cache.json \
    --output-dir data/phase8_url_recovery
```

**Expected**: High yield (~80% - URLs commonly in paper body)

### Stage 3: Web Search Agent Workflow

For resources still missing URLs, AI agents search the web.

**Files**:
- `data/phase8_url_recovery/websearch_chunks/AGENT_BRIEF.md` - Instructions for agents
- `data/phase8_url_recovery/websearch_chunks/Orchestrator_prompt.md` - Orchestration guide
- `data/phase8_url_recovery/websearch_chunks/chunk_XX.csv` - Input chunks (~20 resources each)

**Process**:
1. Script 33 creates chunks and `still_missing.csv`
2. Launch agents in parallel batches (2-4 at a time recommended)
3. Each agent receives AGENT_BRIEF.md instructions
4. Agents output `websearch_results_chunk_XX.csv`
5. Merge with script 34

**Agent Launch Example** (using Claude Code):
```
Launch internet-researcher agents with:
- Input: chunk_XX.csv records
- Instructions: AGENT_BRIEF.md content
- Output: websearch_results_chunk_XX.csv
```

**URL Exclusions** (auto-filtered by script 34):
- GitHub, GitLab, Bitbucket (code repos)
- Zenodo, DOI, Dryad, Figshare (data archives)
- FTP servers
- CRAN, Bioconductor, PyPI (package repos)

### Stage 4: Merge Results

**Script**: `scripts/phase8_url_recovery/34_merge_websearch_results.py`

```bash
python scripts/phase8_url_recovery/34_merge_websearch_results.py \
    --recovered data/phase8_url_recovery/recovered_urls.csv \
    --websearch-dir data/phase8_url_recovery/websearch_chunks \
    --output-dir data/phase8_url_recovery
```

**Output**:
- `final_url_recovery.csv` - All recovered URLs
- `excluded_urls.csv` - URLs filtered out
- `url_recovery_summary.json` - Statistics

---

## Key Learnings & Troubleshooting

### Issue 1: V2 Models Use Wrong Base Model

**Symptom**: Classification/NER produces unexpected results.

**Cause**: Hardcoding `roberta-base` instead of reading from checkpoint.

**Solution**: Always use the helper functions:
```python
# Classification
from inventory_utils.filing import get_classif_model
model, model_name = get_classif_model(f, device)

# NER
from inventory_utils.filing import get_ner_model
model, model_name, tokenizer = get_ner_model(f, device)
```

The correct model is: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500`

### Issue 2: spaCy Shows 100% Ruler or 100% Statistical

**Symptom**: Entity source breakdown shows 100% one type, 0% other.

**Cause**: Model missing `tok2vec` component.

**Solution**:
1. **Run locally** using `run_spacy_full_hybrid_local.py`
2. **Never use Colab** for spaCy NER - Drive model is broken
3. Verify pipeline: `nlp.pipe_names` should show `['entity_ruler', 'tok2vec', 'ner']`

### Issue 3: NER Tokenizer Error

**Symptom**: `NotImplementedError: return_offset_mapping is not available when using Python tokenizers`

**Cause**: Using `RobertaTokenizer` instead of `RobertaTokenizerFast`.

**Solution**: Use `get_ner_model()` which loads the correct tokenizer from the checkpoint.

### Issue 4: PyCaret Infinity Values

**Symptom**: PyCaret crashes with infinity/NaN errors.

**Solution**: The `02_run_pycaret_local.py` script includes fixes:
```python
df['citation_age_ratio'] = df['citation_age_ratio'].replace([np.inf, -np.inf], 0).fillna(0).clip(upper=10000)
```

### Issue 5: PyCaret Numpy Error on Colab

**Symptom**: First run of PyCaret notebook on Colab crashes with a numpy compatibility error.

**Cause**: PyCaret installs dependencies that conflict with Colab's pre-installed numpy version.

**Solution**:
1. Before running: Change runtime to **Python 3.11 (2025.07)** via `Runtime` → `Change runtime type`
2. Run the notebook - it will crash with numpy error (this is expected)
3. Go to `Runtime` → `Restart and run all`
4. Second run will complete successfully

**Note**: This is a known Colab environment issue, not a bug in the notebook code.

---

## File Reference

### Scripts (Relative to `unified_bioresource_pipeline/`)

| Script | Purpose | Where to Run |
|--------|---------|--------------|
| `scripts/phase1_classification/02_run_pycaret_local.py` | PyCaret classification | Local |
| `scripts/phase2_ner/run_spacy_full_hybrid_local.py` | spaCy Full Hybrid NER | **Local only** |
| `scripts/phase2_ner/04_run_v2_ner.py` | V2 NER (reference) | Colab |
| `scripts/phase2_ner/06_extract_pmid_union.py` | Create NER union (updated 2025-12-03) | Local |
| `scripts/phase3_linguistic/run_linguistic_scoring.py` | Linguistic scoring (NEW 2025-12-03) | Local |

#### Script Updates (2025-12-03)

**`06_extract_pmid_union.py`** - Now supports command-line arguments:
```bash
# Auto-detect files (recommended)
python scripts/phase2_ner/06_extract_pmid_union.py --auto

# Explicit paths
python scripts/phase2_ner/06_extract_pmid_union.py \
    --spacy-file ../data/phase2_ner/spacy_ner_results.csv \
    --v2-file ../data/phase2_ner/v2_ner_results.csv \
    --output ../data/phase2_ner/ner_union_pmids.txt \
    --entity-csv ../data/phase2_ner/ner_union.csv
```
- `--auto`: Auto-detects files in unified_bioresource_pipeline paths first, falls back to legacy
- `--spacy-file`, `--v2-file`: Explicit input paths
- `--output`: Custom output path for PMID list
- `--entity-csv`: Output combined entity CSV with normalized columns
- Auto-detects ID column (`ID` vs `publication_id`)

**`run_linguistic_scoring.py`** - New standalone Phase 3 script:
```bash
python scripts/phase3_linguistic/run_linguistic_scoring.py
```
- Input: NER union PMIDs + classification union (for titles/abstracts)
- Output: `high_score_papers.csv`, `medium_score_papers.csv`, `low_score_papers.csv`
- Aggressive profile: High >= 2, Low < -1

### Notebooks (Relative to `unified_bioresource_pipeline/`)

| Notebook | Purpose | Where to Run |
|----------|---------|--------------|
| `notebooks/phase1_classification/v2_classification_2022_mid2025.ipynb` | V2 Classification | Colab (GPU) |
| `notebooks/phase1_classification/pycaret_classification_2022_mid2025.ipynb` | PyCaret (backup) | Colab |
| `notebooks/phase2_ner/v2_ner_2022_mid2025.ipynb` | V2 NER | Colab (GPU) |
| `notebooks/phase2_ner/spacy_ner_2022_mid2025.ipynb` | ⚠️ **DO NOT USE** | - |

### Data Files (Relative to `unified_bioresource_pipeline/`)

| File | Description |
|------|-------------|
| `data/input/v5.1_2022_mid2025_for_classification.csv` | Input papers |
| `data/phase1_classification/classification_union.csv` | Union of V2 + PyCaret positives |
| `data/phase2_ner/spacy_ner_results.csv` | spaCy NER output |
| `data/phase2_ner/v2_ner_results.csv` | V2 NER output |
| `data/phase2_ner/ner_union.csv` | Combined NER results |
| `data/phase2_ner/ner_union_pmids.txt` | Unique PMIDs from NER union |
| `data/phase3_linguistic/high_score_papers.csv` | High confidence introductions (>=2) |
| `data/phase3_linguistic/medium_score_papers.csv` | Needs SetFit classification |
| `data/phase3_linguistic/low_score_papers.csv` | Likely usage papers |

### Models (Relative to repository root)

| Model | Path |
|-------|------|
| V2 Classification | `out/original_model/article_classifier.pt` |
| V2 NER | `out/original_model/named_entity_recognition.pt` |
| PyCaret | `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl` |
| spaCy Hybrid | `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/` |

---

## Quick Start Checklist

### For New Data:

1. [ ] Prepare input CSV with `id`, `title`, `abstract` columns
2. [ ] Upload to `unified_bioresource_pipeline/data/input/`
3. [ ] Update paths in scripts/notebooks
4. [ ] Run V2 Classification on Colab
5. [ ] Run PyCaret locally: `python scripts/phase1_classification/02_run_pycaret_local.py`
6. [ ] Create classification union
7. [ ] Run V2 NER on Colab
8. [ ] Run spaCy locally: `python scripts/phase2_ner/run_spacy_full_hybrid_local.py`
9. [ ] Create NER union
10. [ ] Continue with Phase 3-9

### Validation Checkpoints:

- [ ] V2 Classification: ~6-8% positive rate
- [ ] PyCaret Classification: ~25-30% positive rate
- [ ] Classification Union: ~28-32% of input
- [ ] spaCy NER: ~65-70% coverage, BOTH ruler AND statistical sources
- [ ] V2 NER: ~35-40k entities

---

## Session Log: 2022-mid2025 Fresh Run

| Date | Phase | Result |
|------|-------|--------|
| 2025-12-02 | V2 Classification | 6,645 positives (6.7%) |
| 2025-12-02 | PyCaret Classification | 25,476 positives (26.7%) |
| 2025-12-02 | Classification Union | 27,975 papers (28.4%) |
| 2025-12-02 | V2 NER | 35,320 entities |
| 2025-12-02 | spaCy Full Hybrid NER (local) | **68,149 entities** (67.68% coverage) |
| 2025-12-03 | NER Union | **20,017 papers** (48,163 entities after dedup) |
| 2025-12-03 | Phase 3 Linguistic Scoring | High: 5,734, Medium: 14,266, Low: 30 |
| 2025-12-03 | Phase 4 SetFit Inference | 5,046 intros (35.4% of medium-score) |
| 2025-12-03 | Phase 4 Adjusted | +556 V2-rescued → **5,602 intros** |
| 2025-12-03 | Phase 5 Entity Mapping | 28,694 entity-paper pairs, 11,328 papers |
| 2025-12-03 | Phase 6 URL Extraction | 5,299 URLs from 4,514 papers |
| 2025-12-03 | Phase 7 Deduplication | 20,588 unique resources |
| 2025-12-03 | Phase 9 Final Inventory | **1,858 resources** (≥2 papers) |
| 2025-12-03 | Phase 8 URL Recovery (Abstract) | 2 URLs found |
| 2025-12-03 | Phase 8 URL Recovery (Fulltext) | 483 URLs found (80.4%) |
| 2025-12-03 | Phase 8 URL Recovery (Web Search) | 54 URLs found (6 agent chunks) |
| 2025-12-03 | Phase 8 Total Recovered | **539 URLs** → 96.6% coverage |

---

## Phase 4 Classification Decision (2025-12-03)

### Issue Identified

SetFit classified 556 papers as "usage" that the V2 classifier identified as introductions. Analysis showed:

- **93% of these 556 papers** have bioresource entities found by spaCy NER
- These papers have titles like "Hyperspectral Imaging **Database**", "TACO: A Turkish **database**"
- SetFit confidence on these papers: median 0.38 (highly uncertain)

### Decision Made

**Add all V2-YES papers to the introduction set**, regardless of SetFit prediction.

**Rationale**:
1. V2 classifier was trained specifically for bioresource detection
2. spaCy NER confirms 93% have relevant entities
3. Lowering SetFit threshold (e.g., 0.45) would only capture 24% of these papers while adding many uncertain ones

### Output Files

| File | Contents | Count |
|------|----------|-------|
| `setfit_classified_introductions.csv` | Original SetFit positives | 5,046 |
| `setfit_introductions_adjusted.csv` | SetFit + V2-rescued | 5,602 |
| `v2_rescued_papers_FOR_REVIEW.csv` | Papers added by V2 decision | 556 |

### Final Introduction Counts

| Source | Count | Notes |
|--------|-------|-------|
| Phase 3 High-Score (auto-intro) | 5,734 | Linguistic score ≥ 2 |
| Phase 4 SetFit Introductions | 5,046 | SetFit confidence ≥ 0.50 |
| Phase 4 V2-Rescued | 556 | V2=YES, SetFit=NO |
| **TOTAL INTRODUCTIONS** | **11,336** | For downstream processing |

### ⚠️ REVIEW NEEDED

The following require manual review to validate inclusion/exclusion criteria:

1. **`v2_rescued_papers_FOR_REVIEW.csv`** - 556 papers where V2 and SetFit disagree
2. **SetFit low-confidence introductions** - Papers with 0.50-0.60 confidence
3. **SetFit borderline usage** - Papers with 0.45-0.50 confidence that were excluded

This decision prioritizes **recall over precision**. Future runs should evaluate whether this trade-off is appropriate.

---

**Document Version**: 1.3
**Last Updated**: 2025-12-03
**Author**: Pipeline Automation
**Contact**: Check repository issues for support

---

## Changelog

### v1.3 (2025-12-03)
- Added Phase 8 URL Recovery documentation
- Documented web search agent workflow with AGENT_BRIEF.md
- Updated session log with URL recovery results (539 URLs, 96.6% coverage)

### v1.2 (2025-12-03)
- Added Phase 4 classification decision documentation
- Updated session log with Phase 3-9 results

### v1.1 (2025-12-02)
- Initial documentation with Phase 1-2 execution details
