# spaCy Hybrid NER for Bioresource Extraction

**Status**: Phase 1-2 Complete (5 scripts implemented)
**Created**: 2025-11-12
**Project Plan**: `../plans/spacy_hybrid_ner/`

## Overview

Hybrid EntityRuler + Statistical NER system for extracting bioresource names from scientific literature with alias resolution capability.

### Key Capabilities

1. **High-Precision Known Entity Extraction**: EntityRuler with pattern matching (>95% precision)
2. **Alias Resolution**: Links short/long form names (e.g., "PDB" ↔ "Protein Domain Database")
3. **Generalization to New Entities**: Statistical NER trained via distant supervision (Phase 3-4)
4. **Production-Ready Pipeline**: Packaged spaCy model for deployment (Phase 5-6)

## Quick Start

### Prerequisites

```bash
# Install spaCy 3.7.0
pip install spacy==3.7.0

# Ensure you're in the project directory
cd /Users/warren/development/GBC/inventory_2022/spacy_hybrid_ner
```

### Phase 1-2: EntityRuler Baseline (Implemented)

Run scripts in order to build and validate EntityRuler:

```bash
# Phase 1.1: Extract bioresource dictionary
python scripts/01_extract_bioresource_dictionary.py

# Phase 1.2: Enrich missing full names
python scripts/02_enrich_missing_fullnames.py

# Phase 1.3: Generate EntityRuler patterns
python scripts/03_generate_patterns_jsonl.py

# Phase 2.2: Test EntityRuler pipeline
python scripts/04_test_entityruler_pipeline.py

# Phase 2.3: Validate on real papers
python scripts/05_validate_entityruler.py
```

### Expected Results

**Phase 1**:
- ~3,761 unique resources extracted
- 70-80% with full names (after enrichment)
- 3,000-5,000 patterns generated

**Phase 2**:
- >95% precision on known entities
- 70-80% coverage on bioresource papers
- 100% alias resolution (all entities have canonical IDs)

## Project Structure

```
spacy_hybrid_ner/
├── scripts/              # Python scripts for each phase
│   ├── 01_extract_bioresource_dictionary.py
│   ├── 02_enrich_missing_fullnames.py
│   ├── 03_generate_patterns_jsonl.py
│   ├── 04_test_entityruler_pipeline.py
│   └── 05_validate_entityruler.py
│
├── data/                 # Data files (created by scripts)
│   ├── bioresource_dictionary_raw.json
│   ├── bioresource_dictionary_enriched.json
│   ├── patterns.jsonl
│   └── entityruler_precision_review.csv
│
├── results/              # Validation results
│   └── phase2_entityruler_validation.json
│
├── notebooks/            # Google Colab notebooks (Phase 3+)
├── models/               # Trained models (Phase 4+)
├── packages/             # Packaged spaCy models (Phase 6)
└── src/                  # Integration modules (Phase 6)
```

## Implementation Status

### ✅ Phase 1: Data Preparation & Dictionary Enrichment (COMPLETE)

**Goal**: Build comprehensive bioresource dictionary with 70-80% alias coverage

**Scripts**:
- ✅ `01_extract_bioresource_dictionary.py` - Extract unique resources from CSV
- ✅ `02_enrich_missing_fullnames.py` - Pattern matching to find full names
- ✅ `03_generate_patterns_jsonl.py` - Generate spaCy EntityRuler patterns

**Output**:
- `data/bioresource_dictionary_raw.json` (~3,761 resources)
- `data/bioresource_dictionary_enriched.json` (70-80% coverage)
- `data/patterns.jsonl` (3,000-5,000 patterns)

### ✅ Phase 2: EntityRuler Baseline (COMPLETE)

**Goal**: Validate EntityRuler achieves >95% precision before training

**Scripts**:
- ✅ `04_test_entityruler_pipeline.py` - Test with sample text
- ✅ `05_validate_entityruler.py` - Validate on 100 real papers

**Output**:
- `results/phase2_entityruler_validation.json` (metrics)
- `data/entityruler_precision_review.csv` (manual review sample)

### ⏳ Phase 3: Distant Supervision Training Data (TODO)

**Goal**: Create spaCy-compatible training data (.spacy format)

**Scripts** (to be created):
- `06_prepare_training_corpus.py`
- `07_distant_supervision_annotation.py`

**Output** (expected):
- `data/ner_training/train.spacy`
- `data/ner_training/dev.spacy`
- `data/ner_training/test.spacy`

### ⏳ Phase 4: Statistical NER Training (TODO)

**Goal**: Train statistical NER model on GPU

**Notebook** (to be created):
- `notebooks/spacy_ner_training.ipynb` (Google Colab)

**Output** (expected):
- `models/ner_statistical/` (Test F1 >70%)

### ⏳ Phase 5: Hybrid Pipeline Integration (TODO)

**Goal**: Combine EntityRuler + Statistical NER

**Scripts** (to be created):
- `09_build_hybrid_pipeline.py`
- `10_validate_hybrid_pipeline.py`
- `11_benchmark_hybrid_speed.py`
- `12_analyze_alias_resolution.py`

**Output** (expected):
- `models/ner_hybrid_v1/`

### ⏳ Phase 6: Production Deployment (TODO)

**Goal**: Package and deploy pipeline

**Deliverables** (to be created):
- `packages/en_ner_hybrid_bioresource-1.0.0/`
- `src/ner_predict_spacy.py`
- `notebooks/spacy_full_inference_v5.ipynb`

## Usage Examples

### EntityRuler Only (Phase 2)

```python
import spacy

# Load EntityRuler pipeline
nlp = spacy.blank("en")
ruler = nlp.add_pipe("entity_ruler")
ruler.from_disk("data/patterns.jsonl")

# Extract entities
text = "We used the Protein Domain Database (PDB) and UniProt."
doc = nlp(text)

# Show results with alias resolution
for ent in doc.ents:
    print(f"{ent.text} → {ent.ent_id_}")
```

**Output**:
```
Protein Domain Database → PDB
PDB → PDB
UniProt → UniProt
```

### Hybrid Pipeline (Phase 5+)

```python
import spacy

# Load hybrid pipeline (EntityRuler + Statistical NER)
nlp = spacy.load("models/ner_hybrid_v1")

# Extract known AND unknown entities
text = "We used PDB and a new Genomics Knowledge Base."
doc = nlp(text)

for ent in doc.ents:
    source = "known" if ent.ent_id_ else "discovered"
    print(f"{ent.text} ({source})")
```

**Expected Output**:
```
PDB (known) → PDB
Genomics Knowledge Base (discovered)
```

## Key Features

### Alias Resolution

The EntityRuler assigns canonical IDs to entities, enabling alias linking:

```python
# Both "PDB" and "Protein Domain Database" get ID="PDB"
# This enables downstream analysis to group aliases together
```

### Token vs Phrase Patterns

- **Token Patterns**: Used for short names (handles punctuation)
  ```json
  {"pattern": [{"TEXT": "PDB"}], "id": "PDB"}
  ```
  Matches: `PDB`, `PDB.`, `(PDB)`, `PDB,`

- **Phrase Patterns**: Used for full names (faster)
  ```json
  {"pattern": "Protein Domain Database", "id": "PDB"}
  ```

## Configuration

### Input Files

- **Bioresource CSV**: `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`
  - Expected columns: `resource_short_name`, `resource_full_name`, `pubmed_id`, `title`, `abstract`

### Customization

Edit script constants to customize:

```python
# In each script
SAMPLE_SIZE = 100          # Number of papers to sample
REVIEW_SAMPLE = 50         # Extractions for manual review
OUTPUT_JSON = 'results/...'  # Output paths
```

## Troubleshooting

### Issue: No entities extracted

**Cause**: Patterns file not loaded or tokenization mismatch

**Solution**:
```python
# Check patterns loaded
print(len(ruler.patterns))

# Check tokenization
doc = nlp("Test text with PDB")
print([token.text for token in doc])
```

### Issue: Low coverage (<70%)

**Cause**: Dictionary missing too many full names

**Solution**: Re-run Phase 1.2 with additional patterns or manually add high-frequency resources

### Issue: spaCy not installed

**Solution**:
```bash
pip install spacy==3.7.0
```

## Next Steps

1. **Manual Review**: Annotate `data/entityruler_precision_review.csv` to verify >95% precision
2. **Phase 3**: Implement distant supervision scripts (06, 07)
3. **Phase 4**: Create training notebook and train statistical NER
4. **Phase 5**: Build hybrid pipeline combining both components
5. **Phase 6**: Package for production deployment

## Documentation

- **Complete Plan**: `../plans/2025-11-12_spacy_hybrid_ner_implementation.md`
- **Project Overview**: `../plans/spacy_hybrid_ner/00_PROJECT_OVERVIEW.md`
- **Phase 1-2 Details**: `../plans/spacy_hybrid_ner/01_DATA_PREPARATION_PHASES_1_2.md`

## References

- **spaCy EntityRuler**: https://spacy.io/api/entityruler
- **Research Strategy**: `../docs/research_docs/ner_implementation.md` (Strategy 3: Hybrid)
- **V2 NER Baseline**: F1=0.749 (to be compared against)

---

**Created**: 2025-11-12
**Status**: Phase 1-2 Complete
**Next Milestone**: Phase 3 (Distant Supervision)
