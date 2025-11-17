# Scripts Index & Quick Reference

**Purpose**: Complete reference for all scripts in the spaCy hybrid NER implementation
**Total Scripts**: 13 Python scripts + 2 Jupyter notebooks

---

## Quick Navigation

| Phase | Scripts | Purpose |
|-------|---------|---------|
| **Phase 1** | 01-03 | Data preparation & pattern generation |
| **Phase 2** | 04-05 | EntityRuler baseline & validation |
| **Phase 3** | 06-07 | Training data preparation |
| **Phase 4** | Training notebook | Statistical NER training (GPU) |
| **Phase 5** | 09-12 | Hybrid integration & analysis |
| **Phase 6** | 13 | Production benchmarking |

---

## Phase 1: Data Preparation (Scripts 01-03)

### Script 01: `scripts/01_extract_bioresource_dictionary.py`

**Purpose**: Extract unique bioresource pairs (short name ↔ full name) from CSV

**Input**:
- `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`

**Output**:
- `data/bioresource_dictionary_raw.json`

**Usage**:
```bash
python scripts/01_extract_bioresource_dictionary.py
```

**Key Operations**:
- Loads bioresource papers CSV
- Extracts unique (short_name, full_name) pairs
- Uses short_name as canonical ID
- Tracks paper count and PMIDs per resource
- Saves as JSON dictionary

**Expected Statistics**:
- Total resources: ~3,761
- With full name: ~1,840 (40%)
- Missing full name: ~1,921 (60%)

**Success Criteria**:
- [x] JSON file created
- [x] ~40% have both short + full names
- [x] ~60% missing full names

---

### Script 02: `scripts/02_enrich_missing_fullnames.py`

**Purpose**: Auto-extract missing full names from paper titles/abstracts using pattern matching

**Input**:
- `data/bioresource_dictionary_raw.json`
- Bioresource papers CSV (for text content)

**Output**:
- `data/bioresource_dictionary_enriched.json`
- `data/enrichment_review.csv` (optional, for manual review)

**Usage**:
```bash
python scripts/02_enrich_missing_fullnames.py
```

**Key Operations**:
- Loads dictionary with missing full_name entries
- For each resource, retrieves its papers
- Applies regex patterns to extract full name candidates:
  - `"Full Name (SHORT)"` format
  - `"SHORT (Full Name)"` format
  - `"the Full Name database ... SHORT"` format
- Consensus voting: most frequent match wins
- Flags ambiguous cases for manual review

**Pattern Examples**:
```python
patterns = [
    r"([\w\s]+)\s+\({short}\)",  # "Protein Domain Database (PDB)"
    r"{short}\s+\(([\w\s]+)\)",  # "PDB (Protein Domain Database)"
    r"the\s+([\w\s]+?)\s+database.*\b{short}\b",
]
```

**Target**: Add 700-900 full names → 70-80% total coverage

**Success Criteria**:
- [x] Coverage increased to 70-80%
- [x] Enrichment flag added for auto-enriched entries
- [x] Ambiguous cases saved for review

---

### Script 03: `scripts/03_generate_patterns_jsonl.py`

**Purpose**: Generate spaCy EntityRuler patterns from enriched dictionary

**Input**:
- `data/bioresource_dictionary_enriched.json`

**Output**:
- `data/patterns.jsonl` (~3,000-5,000 patterns)

**Usage**:
```bash
python scripts/03_generate_patterns_jsonl.py
```

**Key Operations**:
- Loads enriched dictionary
- For each resource:
  - Creates token pattern for short name: `[{"TEXT": "PDB"}]`
  - Creates phrase pattern for full name: `"Protein Domain Database"`
  - Optionally adds plural form: `"Protein Domain Databases"`
- Saves as JSONL (one JSON per line)

**Pattern Types**:
- **Token patterns**: For short names (handles punctuation)
- **Phrase patterns**: For full names (faster matching)

**Output Format**:
```jsonl
{"label": "BIO_RESOURCE", "pattern": [{"TEXT": "BAR"}], "id": "BAR"}
{"label": "BIO_RESOURCE", "pattern": "Bio-Analytic Resource for Plant Biology", "id": "BAR"}
```

**Success Criteria**:
- [x] JSONL file with 3,000-5,000 patterns
- [x] Each resource with both names has 2+ patterns
- [x] Token patterns for short names
- [x] Phrase patterns for full names

---

## Phase 2: EntityRuler Baseline (Scripts 04-05)

### Script 04: `scripts/04_test_entityruler_pipeline.py`

**Purpose**: Build EntityRuler pipeline and test on sample text

**Input**:
- `data/patterns.jsonl`

**Output**:
- Console output showing extracted entities
- Loaded pipeline (in memory, not saved)

**Usage**:
```bash
python scripts/04_test_entityruler_pipeline.py
```

**Key Operations**:
- Creates blank spaCy pipeline
- Adds EntityRuler component
- Loads patterns from JSONL
- Tests on hardcoded sample text
- Displays entities with canonical IDs
- Shows alias resolution examples

**Test Text**:
```python
test_text = """
We analyzed data from the Bio-Analytic Resource for Plant Biology (BAR),
the Protein Domain Database (PDB), and the Mouse Phenome Database (MPD).
The BAR and PDB databases were particularly useful.
"""
```

**Success Criteria**:
- [x] All known entities extracted
- [x] Aliases correctly linked to canonical IDs
- [x] No false positives in test examples

---

### Script 05: `scripts/05_validate_entityruler.py`

**Purpose**: Validate EntityRuler precision and coverage on 100 random papers

**Input**:
- Bioresource papers CSV
- Trained EntityRuler pipeline

**Output**:
- `results/phase2_entityruler_validation.json`
- `data/entityruler_precision_review.csv` (for manual annotation)

**Usage**:
```bash
python scripts/05_validate_entityruler.py
```

**Key Operations**:
- Samples 100 random papers
- Runs EntityRuler on each paper
- Tracks: papers with entities, entities per paper
- Saves 50 random extractions for manual precision review

**Metrics Tracked**:
1. **Coverage**: % papers with ≥1 entity found
2. **Avg entities/paper**: Mean number of entities
3. **Precision**: % correct (from manual review of 50 samples)

**Success Criteria**:
- [x] Coverage: 70-80%
- [x] Precision: >95% (from manual review)
- [x] All entities have canonical IDs

---

## Phase 3: Training Data Preparation (Scripts 06-07)

### Script 06: `scripts/06_prepare_training_corpus.py`

**Purpose**: Split bioresource papers into train/dev/test sets

**Input**:
- Bioresource papers CSV (4,559 papers)
- Metadata CSV (optional)

**Output**:
- `data/ner_corpus_splits/train.csv` (~3,191 papers)
- `data/ner_corpus_splits/dev.csv` (~684 papers)
- `data/ner_corpus_splits/test.csv` (~684 papers)

**Usage**:
```bash
python scripts/06_prepare_training_corpus.py
```

**Key Operations**:
- Loads papers and metadata
- Concatenates title + abstract into 'text' field
- Filters papers with insufficient text (<50 chars)
- Performs 70/15/15 train/dev/test split
- Saves CSV files with full text

**Split Ratios**:
- Train: 70% (~3,191 papers)
- Dev: 15% (~684 papers)
- Test: 15% (~684 papers)

**Success Criteria**:
- [x] 3 CSV files created
- [x] Train:Dev:Test ratio is 70:15:15
- [x] All papers have text content (>50 chars)

---

### Script 07: `scripts/07_distant_supervision_annotation.py`

**Purpose**: Auto-annotate papers with dictionary matches (distant supervision) and create spaCy .spacy files

**Input**:
- `data/bioresource_dictionary_enriched.json`
- `data/ner_corpus_splits/*.csv`

**Output**:
- `data/ner_training/train.spacy`
- `data/ner_training/dev.spacy`
- `data/ner_training/test.spacy`
- `data/ner_training/annotation_statistics.csv`

**Usage**:
```bash
python scripts/07_distant_supervision_annotation.py
```

**Key Operations**:
- Builds regex pattern from all aliases
- For each paper:
  - Finds all regex matches
  - Maps matches to labels (B-COM or B-FUL)
  - Uses `char_span(alignment_mode="contract")` to filter noise
  - Handles overlapping spans with `filter_spans()`
- Saves as spaCy DocBin format

**Critical Algorithm**:
```python
# Use "contract" mode to filter misaligned spans
span = doc.char_span(start, end, label=label, alignment_mode="contract")
if span is not None:
    ents.append(span)

# Handle overlaps (keeps longest span)
doc.ents = filter_spans(ents)
```

**Expected Statistics**:
- Train: 3,191 docs, ~8,000-12,000 entities (2-4 per doc)
- Dev: 684 docs, ~1,700-2,500 entities
- Test: 684 docs, ~1,700-2,500 entities
- Label ratio: B-COM ~60%, B-FUL ~40%

**Success Criteria**:
- [x] 3 .spacy files created
- [x] 2-4 entities per document average
- [x] B-COM:B-FUL ratio ~60:40
- [x] No annotation errors when inspecting samples

---

## Phase 4: Statistical NER Training (Notebook)

### Notebook: `notebooks/spacy_ner_training.ipynb`

**Purpose**: Train statistical NER model on GPU (Google Colab)

**Input**:
- `data/ner_training/*.spacy`
- `data/ner_training/config.cfg`

**Output**:
- `models/ner_statistical/model-best/`
- `models/ner_statistical/test_evaluation.json`

**Usage**:
1. Upload to Google Colab
2. Mount Google Drive
3. Copy training files
4. Run training: `python -m spacy train config.cfg --gpu-id 0`
5. Evaluate on test set
6. Copy model back to Drive

**Training Command**:
```bash
python -m spacy train \
  config.cfg \
  --output ./models/ner_statistical \
  --paths.train ./data/ner_training/train.spacy \
  --paths.dev ./data/ner_training/dev.spacy \
  --gpu-id 0 \
  --verbose
```

**Expected Results**:
- Training time: 10-30 minutes (GPU)
- Test F1: >70%
- Can extract NEW entities not in dictionary

**Success Criteria**:
- [x] Test F1 >70%
- [x] Generalizes to unseen entities
- [x] Model saved successfully

---

## Phase 5: Hybrid Integration (Scripts 09-12)

### Script 09: `scripts/09_build_hybrid_pipeline.py`

**Purpose**: Combine EntityRuler + Statistical NER into hybrid pipeline

**Input**:
- `data/patterns.jsonl`
- `models/ner_statistical/`

**Output**:
- `models/ner_hybrid_v2_com_ful/`

**Usage**:
```bash
python scripts/09_build_hybrid_pipeline.py
```

**Key Operations**:
- Creates blank pipeline
- Adds EntityRuler (FIRST!)
- Adds Statistical NER (SECOND!)
- Verifies pipeline order
- Tests on sample with known + new entities
- Saves hybrid pipeline

**Critical**:
```python
# Pipeline order MUST be:
nlp.pipe_names == ["entity_ruler", "ner"]
```

**Success Criteria**:
- [x] Pipeline order correct
- [x] Both known AND new entities detected
- [x] Known entities have canonical IDs

---

### Script 10: `scripts/10_validate_hybrid_pipeline.py`

**Purpose**: Validate hybrid pipeline on test set, measure coverage and entity sources

**Input**:
- `models/ner_hybrid_v2_com_ful/`
- `data/ner_corpus_splits/test.csv`

**Output**:
- `results/phase5_hybrid_validation.json`
- `results/phase5_hybrid_extractions.csv`

**Usage**:
```bash
python scripts/10_validate_hybrid_pipeline.py
```

**Key Metrics**:
- Coverage: % papers with entities
- Total entities extracted
- Ruler entities: Entities with canonical IDs
- Statistical entities: Entities without IDs
- Avg entities per paper

**Target Metrics**:
- Coverage: 80-85%
- Ruler: 70-75%
- Statistical: 25-30%
- Avg entities/paper: 3-5

**Success Criteria**:
- [x] Coverage improvement over baseline
- [x] 25-30% entities from Statistical NER
- [x] Alias resolution working

---

### Script 11: `scripts/11_benchmark_hybrid_speed.py`

**Purpose**: Benchmark speed of EntityRuler, Statistical NER, and Hybrid pipeline

**Input**:
- All three models (ruler, statistical, hybrid)
- 100 test papers

**Output**:
- `results/phase5_speed_benchmark.csv`
- Console output with comparison table

**Usage**:
```bash
python scripts/11_benchmark_hybrid_speed.py
```

**Metrics Tracked**:
- Time per 100 papers
- Papers per second
- Comparison across models

**Expected Speed**:
- EntityRuler Only: 150-200 papers/sec
- Statistical NER: 30-50 papers/sec
- Hybrid: 40-60 papers/sec

**Success Criteria**:
- [x] Hybrid pipeline >40 papers/sec
- [x] Speed acceptable for production

---

### Script 12: `scripts/12_analyze_alias_resolution.py`

**Purpose**: Analyze how well alias resolution links short/long form mentions

**Input**:
- `models/ner_hybrid_v2_com_ful/`
- `data/ner_corpus_splits/test.csv`

**Output**:
- Console output with alias examples
- Statistics on alias resolution success

**Usage**:
```bash
python scripts/12_analyze_alias_resolution.py
```

**Key Metrics**:
- Total resources detected
- Resources with multiple aliases found
- Examples of successful linking
- Entities with canonical ID vs without

**Success Criteria**:
- [x] 70-80% entities have canonical IDs
- [x] Multiple forms correctly linked
- [x] Examples demonstrate correct linking

---

## Phase 6: Production Deployment (Script 13)

### Script 13: `scripts/13_benchmark_all_models.py`

**Purpose**: Compare spaCy Hybrid vs V2 BERT vs Phase 4 Multi-Task models

**Input**:
- `models/ner_hybrid_v2_com_ful/`
- Test papers (100 samples)
- (Optional) V2 BERT model, Phase 4 model

**Output**:
- `results/phase6_model_comparison.csv`
- Comparison table with all metrics

**Usage**:
```bash
python scripts/13_benchmark_all_models.py
```

**Metrics Compared**:
- Speed (papers/sec)
- Entity count
- Alias resolution capability
- Coverage

**Success Criteria**:
- [x] Hybrid outperforms baseline on coverage
- [x] Maintains acceptable precision
- [x] Alias resolution unique to hybrid

---

## Additional File: Integration Module

### Module: `src/ner_predict_spacy.py`

**Purpose**: Production-ready predictor class for hybrid NER pipeline

**Key Class**: `SpacyNERPredictor`

**Methods**:
- `__init__(model_path)`: Load hybrid pipeline
- `predict(papers_df)`: Extract entities with alias resolution
- `predict_to_csv(papers_df, output_path)`: Save results as CSV
- `_group_by_canonical_id(entities)`: Group aliases together

**Usage Example**:
```python
from src.ner_predict_spacy import SpacyNERPredictor

# Initialize
predictor = SpacyNERPredictor("models/ner_hybrid_v2_com_ful")

# Predict
papers = pd.read_csv('papers.csv')
results = predictor.predict(papers)

# Save
predictor.predict_to_csv(papers, 'results.csv')
```

**Features**:
- Batch processing support
- Alias resolution via canonical IDs
- Compatible with existing pipeline
- Comprehensive logging

---

## Script Execution Order

### Local Development (Phases 1-3)

```bash
# Phase 1: Data Preparation
python scripts/01_extract_bioresource_dictionary.py
python scripts/02_enrich_missing_fullnames.py
python scripts/03_generate_patterns_jsonl.py

# Phase 2: EntityRuler Baseline
python scripts/04_test_entityruler_pipeline.py
python scripts/05_validate_entityruler.py

# Phase 3: Training Data
python scripts/06_prepare_training_corpus.py
python scripts/07_distant_supervision_annotation.py
```

### Google Colab (Phase 4)

```bash
# Upload notebooks/spacy_ner_training.ipynb to Colab
# Run all cells in notebook
# Model saves to Google Drive: models/ner_statistical/
```

### Local Development (Phases 5-6)

```bash
# Download model from Drive to local: models/ner_statistical/

# Phase 5: Hybrid Integration
python scripts/09_build_hybrid_pipeline.py
python scripts/10_validate_hybrid_pipeline.py
python scripts/11_benchmark_hybrid_speed.py
python scripts/12_analyze_alias_resolution.py

# Phase 6: Production
python scripts/13_benchmark_all_models.py
```

---

## Quick Start Commands

**Run entire Phase 1-2 pipeline**:
```bash
python scripts/01_extract_bioresource_dictionary.py && \
python scripts/02_enrich_missing_fullnames.py && \
python scripts/03_generate_patterns_jsonl.py && \
python scripts/04_test_entityruler_pipeline.py && \
python scripts/05_validate_entityruler.py
```

**Run entire Phase 3 pipeline**:
```bash
python scripts/06_prepare_training_corpus.py && \
python scripts/07_distant_supervision_annotation.py
```

**Run entire Phase 5 pipeline**:
```bash
python scripts/09_build_hybrid_pipeline.py && \
python scripts/10_validate_hybrid_pipeline.py && \
python scripts/11_benchmark_hybrid_speed.py && \
python scripts/12_analyze_alias_resolution.py
```

---

## Dependencies

All scripts require:
```bash
pip install spacy==3.7.0
pip install pandas scikit-learn tqdm
```

Phase 4 training (Colab) additionally requires:
```bash
pip install spacy[cuda117]==3.7.0  # For GPU
```

---

## File Locations Reference

```
inventory_2022/
├── data/
│   ├── bioresource_dictionary_raw.json        # Script 01 output
│   ├── bioresource_dictionary_enriched.json   # Script 02 output
│   ├── patterns.jsonl                          # Script 03 output
│   ├── ner_corpus_splits/                      # Script 06 output
│   │   ├── train.csv
│   │   ├── dev.csv
│   │   └── test.csv
│   └── ner_training/                           # Script 07 output
│       ├── train.spacy
│       ├── dev.spacy
│       ├── test.spacy
│       ├── config.cfg
│       └── annotation_statistics.csv
│
├── models/
│   ├── ner_statistical/                        # Phase 4 output
│   └── ner_hybrid_v2_com_ful/                          # Script 09 output
│
├── results/
│   ├── phase2_entityruler_validation.json      # Script 05 output
│   ├── phase5_hybrid_validation.json           # Script 10 output
│   ├── phase5_hybrid_extractions.csv           # Script 10 output
│   ├── phase5_speed_benchmark.csv              # Script 11 output
│   └── phase6_model_comparison.csv             # Script 13 output
│
└── src/
    └── ner_predict_spacy.py                    # Integration module
```

---

**Status**: Complete reference for all 13 scripts + 2 notebooks + 1 integration module
