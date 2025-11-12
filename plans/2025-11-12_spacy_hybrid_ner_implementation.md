# spaCy Hybrid NER Implementation Plan

**Date**: November 12, 2025
**Author**: AI Assistant
**Status**: Approved - Ready for Implementation
**Goal**: Build EntityRuler + Statistical NER system for bioresource extraction with alias resolution

---

## Executive Summary

This plan implements the hybrid NER strategy from `docs/research_docs/ner_implementation.md` (Strategy 3: Recommended) to extract bioresource entities from scientific literature with the following capabilities:

1. **High-Precision Known Entity Extraction**: EntityRuler with pattern matching (>95% precision)
2. **Alias Resolution**: Links short/long form names (e.g., "PDB" ↔ "Protein Domain Database")
3. **Generalization to New Entities**: Statistical NER trained via distant supervision
4. **Production-Ready Pipeline**: Packaged spaCy model for deployment

### Key Design Decisions

- **Framework**: spaCy v3.7 (new implementation, not compatible with existing BERT models)
- **Pipeline Order**: EntityRuler → Statistical NER (critical for hybrid approach)
- **Training Method**: Distant supervision on 4,559 bioresource papers
- **Entity Labels**: Reuse existing COM/FUL distinction (aligned with V2 models)
- **Deployment**: Local scripts (testing) + Google Colab notebook (training/inference)

### Timeline

**Total Duration**: 14-20 days (3-4 weeks full-time)
**Phases**: 6 phases from data preparation to production deployment

---

## Background & Context

### Current State

**Existing NER Models**:
- **V2 NER**: BERT-based, F1=0.749, production-ready
- **Phase 4 Multi-Task**: F1=0.9274 (validation) but has post-processing bug (F1=0.2249 on test)
- **Entity Labels**: Already uses B-COM/I-COM (short names) and B-FUL/I-FUL (full names)

**Key Limitation**: No alias linking capability (doesn't know "PDB" = "Protein Domain Database")

### Available Assets

1. **Bioresource Dictionary**: `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`
   - 4,559 papers
   - 3,761 unique short names
   - 1,450 unique full names
   - ⚠️ **60% missing full_name** (2,719 resources)

2. **Training Corpus**: Same 4,559 papers with full text

3. **Metadata**: 21,612 papers with 28-34 enhanced features (from PyCaret study)

4. **Existing Training Data**: `data/ner_splits_full/` (441 papers, 2,876 samples)
   - Already in COM/FUL format
   - Currently BERT format (not spaCy DocBin)

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
# Entities: ["Bio-Analytic Resource" (ID=BAR), "BAR" (ID=BAR), "Genomics Repository" (ID=None)]
```

**Critical**: EntityRuler MUST run first so statistical model respects its high-precision matches.

### Entity Label Schema

Reusing existing V2/Phase 4 labels:

| Label | Description | Example | Source |
|-------|-------------|---------|--------|
| B-COM | Begin - Common/Short name | "PDB" | EntityRuler or Statistical |
| I-COM | Inside - Common name | N/A (rare for short names) | Statistical |
| B-FUL | Begin - Full name | "Protein Domain Database" | EntityRuler or Statistical |
| I-FUL | Inside - Full name | "Domain Database" | EntityRuler or Statistical |
| O | Outside (not entity) | "the", "and" | Statistical |

**Alias Resolution**: `ent.ent_id_` stores canonical ID (e.g., "PDB" for both "PDB" and "Protein Domain Database")

---

## PHASE 1: Data Preparation & Dictionary Enrichment (3-4 days)

### Objective

Build comprehensive bioresource dictionary with 70-80% alias coverage (up from 40%).

### 1.1 Extract Bioresource Dictionary from CSV

**Script**: `scripts/01_extract_bioresource_dictionary.py`

**Input**:
- `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`

**Processing**:
```python
import pandas as pd
import json

df = pd.read_csv('bioresource_papers_latest.csv')

# Extract unique resource pairs
dictionary = {}
for _, row in df.iterrows():
    short = row['resource_short_name']
    full = row['resource_full_name']

    if pd.notna(short):
        canonical_id = short  # Use short name as canonical ID

        if canonical_id not in dictionary:
            dictionary[canonical_id] = {
                'short_name': short,
                'full_name': full if pd.notna(full) else None,
                'paper_count': 0,
                'pmids': []
            }

        dictionary[canonical_id]['paper_count'] += 1
        dictionary[canonical_id]['pmids'].append(row['pubmed_id'])

# Save
with open('data/bioresource_dictionary_raw.json', 'w') as f:
    json.dump(dictionary, f, indent=2)

# Statistics
total = len(dictionary)
with_full = sum(1 for v in dictionary.values() if v['full_name'])
print(f"Total resources: {total}")
print(f"With full name: {with_full} ({with_full/total*100:.1f}%)")
print(f"Missing full name: {total - with_full} ({(total-with_full)/total*100:.1f}%)")
```

**Output**:
- `data/bioresource_dictionary_raw.json`
- Statistics: ~3,761 resources (1,840 complete, 1,921 missing full_name)

### 1.2 Manual Full Name Enrichment

**Script**: `scripts/02_enrich_missing_fullnames.py`

**Strategy**: Extract full names from paper titles/abstracts using pattern matching

**Common Patterns**:
```python
patterns = [
    r"([\w\s]+)\s+\({short}\)",  # "Protein Domain Database (PDB)"
    r"{short}\s+\(([\w\s]+)\)",  # "PDB (Protein Domain Database)"
    r"the\s+([\w\s]+?)\s+database.*\b{short}\b",  # "the Mouse Phenome database ... MPD"
    r"\b{short}\b.*?is\s+(?:a|an)\s+([\w\s]+?)\s+(?:database|resource)",
]
```

**Processing**:
```python
import re

missing_full = [rid for rid, data in dictionary.items() if not data['full_name']]
enriched_count = 0

for resource_id in missing_full:
    short = dictionary[resource_id]['short_name']
    pmids = dictionary[resource_id]['pmids']

    # Load papers with this resource
    papers = df[df['pubmed_id'].isin(pmids)]

    # Try pattern matching on titles/abstracts
    candidates = []
    for _, paper in papers.iterrows():
        text = f"{paper['title']} {paper.get('abstract', '')}"

        for pattern in patterns:
            regex = pattern.format(short=re.escape(short))
            matches = re.findall(regex, text, re.IGNORECASE)
            candidates.extend(matches)

    # Consensus: most frequent match
    if candidates:
        from collections import Counter
        most_common = Counter(candidates).most_common(1)[0][0]
        dictionary[resource_id]['full_name'] = most_common.strip()
        dictionary[resource_id]['enriched'] = True
        enriched_count += 1

print(f"Enriched {enriched_count} resources with full names")
```

**Interactive Review**:
- Show ambiguous cases (multiple candidate names)
- Allow manual selection or skip
- Flag resources for manual research

**Target**: Add 700-900 full names → 70-80% total coverage

**Output**: `data/bioresource_dictionary_enriched.json`

### 1.3 Generate spaCy EntityRuler Patterns

**Script**: `scripts/03_generate_patterns_jsonl.py`

**Pattern Generation Logic**:
```python
import json

patterns = []

for resource_id, data in dictionary.items():
    short = data['short_name']
    full = data['full_name']

    # Always add short name (token pattern for punctuation handling)
    patterns.append({
        "label": "BIO_RESOURCE",
        "pattern": [{"TEXT": short}],  # Token pattern
        "id": resource_id
    })

    # Add full name if available (phrase pattern)
    if full:
        patterns.append({
            "label": "BIO_RESOURCE",
            "pattern": full,  # Phrase pattern (exact string)
            "id": resource_id
        })

        # Add common variations (optional)
        # e.g., "Protein Domain Database" → "Protein Domain Databases" (plural)
        if not full.endswith('s'):
            patterns.append({
                "label": "BIO_RESOURCE",
                "pattern": full + "s",
                "id": resource_id
            })

# Save as JSONL (one JSON per line)
with open('data/patterns.jsonl', 'w') as f:
    for pattern in patterns:
        f.write(json.dumps(pattern) + '\n')

print(f"Generated {len(patterns)} patterns from {len(dictionary)} resources")
```

**Pattern Examples**:
```jsonl
{"label": "BIO_RESOURCE", "pattern": [{"TEXT": "BAR"}], "id": "BAR"}
{"label": "BIO_RESOURCE", "pattern": "Bio-Analytic Resource for Plant Biology", "id": "BAR"}
{"label": "BIO_RESOURCE", "pattern": [{"TEXT": "PDB"}], "id": "PDB"}
{"label": "BIO_RESOURCE", "pattern": "Protein Domain Database", "id": "PDB"}
```

**Validation Tests**:
```python
import spacy

# Test tokenization edge cases
nlp = spacy.blank("en")
test_cases = [
    "We used PDB.",           # Period after acronym
    "The (PDB) database",     # Parentheses
    "PDB-101 tutorial",       # Hyphenated compound
    "PRIDE, PDB, and UniProt" # Comma-separated list
]

for text in test_cases:
    doc = nlp(text)
    print(f"Text: {text}")
    print(f"Tokens: {[token.text for token in doc]}")
```

**Output**: `data/patterns.jsonl` (~3,000-5,000 patterns)

### Deliverables Phase 1

- [ ] `data/bioresource_dictionary_raw.json`
- [ ] `data/bioresource_dictionary_enriched.json`
- [ ] `data/patterns.jsonl`
- [ ] Statistics report (coverage, enrichment rate)

---

## PHASE 2: EntityRuler Baseline (Local Testing) (2-3 days)

### Objective

Validate EntityRuler achieves >95% precision on known entities before investing in statistical training.

### 2.1 Environment Setup

**Update requirements.txt**:
```bash
# Add to requirements.txt
spacy>=3.7.0,<4.0.0
```

**Installation**:
```bash
pip install spacy==3.7.0
python -m spacy download en_core_web_sm  # Optional: for tokenization
```

**Note**: We'll use `spacy.blank("en")` (no pre-trained model needed) since we're building from scratch.

### 2.2 Build EntityRuler Pipeline

**Script**: `scripts/04_test_entityruler_pipeline.py`

```python
import spacy
from spacy.pipeline import EntityRuler

# Load blank English pipeline (no pre-trained weights)
nlp = spacy.blank("en")

# Add EntityRuler component
ruler = nlp.add_pipe("entity_ruler")
ruler.from_disk("data/patterns.jsonl")

print(f"Pipeline components: {nlp.pipe_names}")
print(f"EntityRuler patterns loaded: {len(ruler.patterns)}")

# Test on sample text
test_text = """
We analyzed data from the Bio-Analytic Resource for Plant Biology (BAR),
the Protein Domain Database (PDB), and the Mouse Phenome Database (MPD).
The BAR and PDB databases were particularly useful.
"""

doc = nlp(test_text)

print("\nExtracted Entities:")
print("-" * 60)
for ent in doc.ents:
    print(f"Text: '{ent.text}'")
    print(f"  Label: {ent.label_}")
    print(f"  Canonical ID: {ent.ent_id_}")
    print(f"  Span: [{ent.start_char}:{ent.end_char}]")
    print()

# Check alias resolution
aliases = {}
for ent in doc.ents:
    canonical = ent.ent_id_
    if canonical not in aliases:
        aliases[canonical] = []
    aliases[canonical].append(ent.text)

print("\nAlias Resolution:")
print("-" * 60)
for canonical, mentions in aliases.items():
    print(f"{canonical}: {mentions}")
```

**Expected Output**:
```
Pipeline components: ['entity_ruler']
EntityRuler patterns loaded: 4823

Extracted Entities:
------------------------------------------------------------
Text: 'Bio-Analytic Resource for Plant Biology'
  Label: BIO_RESOURCE
  Canonical ID: BAR
  Span: [24:66]

Text: 'BAR'
  Label: BIO_RESOURCE
  Canonical ID: BAR
  Span: [69:72]

Text: 'Protein Domain Database'
  Label: BIO_RESOURCE
  Canonical ID: PDB
  Span: [79:102]

Text: 'PDB'
  Label: BIO_RESOURCE
  Canonical ID: PDB
  Span: [105:108]

Text: 'Mouse Phenome Database'
  Label: BIO_RESOURCE
  Canonical ID: MPD
  Span: [119:141]

Text: 'MPD'
  Label: BIO_RESOURCE
  Canonical ID: MPD
  Span: [144:147]

Text: 'BAR'
  Label: BIO_RESOURCE
  Canonical ID: BAR
  Span: [154:157]

Text: 'PDB'
  Label: BIO_RESOURCE
  Canonical ID: PDB
  Span: [162:165]

Alias Resolution:
------------------------------------------------------------
BAR: ['Bio-Analytic Resource for Plant Biology', 'BAR', 'BAR']
PDB: ['Protein Domain Database', 'PDB', 'PDB']
MPD: ['Mouse Phenome Database', 'MPD']
```

**Success Criteria**:
- [x] All known entities extracted
- [x] Aliases correctly linked to canonical IDs
- [x] No false positives in test examples

### 2.3 Validate on Bioresource Papers

**Script**: `scripts/05_validate_entityruler.py`

**Sampling Strategy**:
```python
import pandas as pd
import random

# Load bioresource papers
df = pd.read_csv('bioresource_papers_latest.csv')

# Sample 100 random papers
sample = df.sample(n=100, random_state=42)

# Run EntityRuler
results = []
for _, paper in sample.iterrows():
    text = f"{paper['title']} {paper.get('abstract', '')}"
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        entities.append({
            'text': ent.text,
            'label': ent.label_,
            'canonical_id': ent.ent_id_,
            'start': ent.start_char,
            'end': ent.end_char
        })

    results.append({
        'pmid': paper['pubmed_id'],
        'resource_short_name': paper['resource_short_name'],
        'resource_full_name': paper['resource_full_name'],
        'entities_found': len(entities),
        'entities': entities
    })

# Calculate metrics
papers_with_entities = sum(1 for r in results if r['entities_found'] > 0)
coverage = papers_with_entities / len(results)

print(f"Papers processed: {len(results)}")
print(f"Papers with ≥1 entity: {papers_with_entities} ({coverage*100:.1f}%)")
print(f"Avg entities per paper: {sum(r['entities_found'] for r in results) / len(results):.2f}")
```

**Manual Precision Evaluation**:
```python
# Sample 50 extractions for manual review
import random

all_entities = []
for result in results:
    for ent in result['entities']:
        all_entities.append({
            'pmid': result['pmid'],
            'text': ent['text'],
            'canonical_id': ent['canonical_id']
        })

review_sample = random.sample(all_entities, min(50, len(all_entities)))

# Save for manual annotation
pd.DataFrame(review_sample).to_csv('data/entityruler_precision_review.csv', index=False)
print("Review file saved: data/entityruler_precision_review.csv")
print("Please annotate: Add column 'correct' (1=correct, 0=incorrect)")
```

**Metrics**:
1. **Coverage**: % papers with ≥1 entity found
   - Target: 70-80% (limited by dictionary coverage)

2. **Precision**: % correct extractions (from manual review)
   - Target: >95% (high precision expected for rule-based)

3. **Alias Resolution**: % entities with canonical ID
   - Target: 100% (all EntityRuler extractions have IDs)

**Output**:
- `results/phase2_entityruler_validation.json`
- `data/entityruler_precision_review.csv` (for manual annotation)

### Deliverables Phase 2

- [ ] `scripts/04_test_entityruler_pipeline.py`
- [ ] `scripts/05_validate_entityruler.py`
- [ ] `results/phase2_entityruler_validation.json`
- [ ] Precision >95% confirmed via manual review
- [ ] Coverage 70-80% confirmed

---

## PHASE 3: Distant Supervision Training Data (4-5 days)

### Objective

Create spaCy-compatible training data (.spacy format) using distant supervision from the bioresource dictionary.

### 3.1 Prepare Paper Corpus

**Script**: `scripts/06_prepare_training_corpus.py`

```python
import pandas as pd
from sklearn.model_selection import train_test_split

# Load bioresource papers
df = pd.read_csv('bioresource_papers_latest.csv')

# Merge with metadata (if available)
metadata = pd.read_csv('data/metadata/pmc_metadata_enhanced_full.csv')
df = df.merge(metadata, left_on='pubmed_id', right_on='id', how='left', suffixes=('', '_meta'))

# Concatenate title + abstract
df['text'] = df['title'] + ' ' + df['abstract'].fillna('')

# Filter: must have text
df = df[df['text'].str.len() > 50]  # At least 50 chars

print(f"Total papers with text: {len(df)}")

# Train/Dev/Test split (70/15/15)
train, temp = train_test_split(df, test_size=0.30, random_state=42)
dev, test = train_test_split(temp, test_size=0.50, random_state=42)

print(f"Train: {len(train)} papers")
print(f"Dev: {len(dev)} papers")
print(f"Test: {len(test)} papers")

# Save splits
train.to_csv('data/ner_corpus_splits/train.csv', index=False)
dev.to_csv('data/ner_corpus_splits/dev.csv', index=False)
test.to_csv('data/ner_corpus_splits/test.csv', index=False)
```

**Expected Output**:
- Train: ~3,191 papers
- Dev: ~684 papers
- Test: ~684 papers

### 3.2 Auto-Annotate with Dictionary (Distant Supervision)

**Script**: `scripts/07_distant_supervision_annotation.py`

This is the **most critical script** - implements the distant supervision algorithm from the research document.

```python
import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans
import pandas as pd
import re
from tqdm import tqdm
import json

# Load enriched dictionary
with open('data/bioresource_dictionary_enriched.json', 'r') as f:
    dictionary = json.load(f)

# Build alias → label mapping
alias_to_label = {}
for resource_id, data in dictionary.items():
    short = data['short_name']
    full = data.get('full_name')

    # Short name → B-COM
    alias_to_label[short] = "B-COM"

    # Full name → B-FUL (if available)
    if full:
        alias_to_label[full] = "B-FUL"

print(f"Alias dictionary size: {len(alias_to_label)}")

# Create regex pattern (all aliases)
# Sort by length (longest first) to avoid partial matches
aliases_sorted = sorted(alias_to_label.keys(), key=len, reverse=True)
regex_pattern = r'\b(' + '|'.join(re.escape(alias) for alias in aliases_sorted) + r')\b'
pattern = re.compile(regex_pattern, re.IGNORECASE)

print(f"Regex pattern length: {len(regex_pattern)} chars")

def annotate_text(text, nlp):
    """Auto-annotate text with dictionary matches."""
    doc = nlp.make_doc(text)
    ents = []

    # Find all string matches
    for match in pattern.finditer(text):
        matched_text = match.group(1)
        start, end = match.span()

        # Determine label (COM or FUL)
        # Case-insensitive lookup
        label = None
        for alias, lbl in alias_to_label.items():
            if matched_text.lower() == alias.lower():
                label = lbl
                break

        if not label:
            continue  # Skip if not found (shouldn't happen)

        # CRITICAL: char_span with alignment_mode="contract"
        # This filters out noise (misaligned spans)
        span = doc.char_span(start, end, label=label, alignment_mode="contract")

        if span is not None:
            ents.append(span)

    # Handle overlaps (e.g., "PDB" inside "PDB-101")
    doc.ents = filter_spans(ents)

    return doc

# Process each split
def process_split(split_name):
    print(f"\nProcessing {split_name} split...")

    # Load papers
    df = pd.read_csv(f'data/ner_corpus_splits/{split_name}.csv')

    # Initialize spaCy and DocBin
    nlp = spacy.blank("en")
    db = DocBin()

    # Statistics
    total_docs = 0
    total_entities = 0
    skipped = 0

    for _, paper in tqdm(df.iterrows(), total=len(df)):
        text = paper['text']

        if not text or len(text) < 10:
            skipped += 1
            continue

        # Annotate
        doc = annotate_text(text, nlp)

        # Add to DocBin
        db.add(doc)

        total_docs += 1
        total_entities += len(doc.ents)

    # Save
    output_path = f'data/ner_training/{split_name}.spacy'
    db.to_disk(output_path)

    print(f"  Saved: {output_path}")
    print(f"  Documents: {total_docs}")
    print(f"  Entities: {total_entities}")
    print(f"  Avg entities/doc: {total_entities/total_docs:.2f}")
    print(f"  Skipped: {skipped}")

    return {
        'split': split_name,
        'documents': total_docs,
        'entities': total_entities,
        'avg_per_doc': total_entities / total_docs,
        'skipped': skipped
    }

# Process all splits
stats = []
for split in ['train', 'dev', 'test']:
    stat = process_split(split)
    stats.append(stat)

# Save statistics
stats_df = pd.DataFrame(stats)
stats_df.to_csv('data/ner_training/annotation_statistics.csv', index=False)
print("\n=== Annotation Statistics ===")
print(stats_df)
```

**Quality Checks**:
```python
# Load and inspect a .spacy file
import spacy
from spacy.tokens import DocBin

nlp = spacy.blank("en")
db = DocBin().from_disk('data/ner_training/train.spacy')
docs = list(db.get_docs(nlp.vocab))

print(f"Loaded {len(docs)} documents")

# Inspect first 5 docs
for i, doc in enumerate(docs[:5]):
    print(f"\nDoc {i+1}:")
    print(f"  Text: {doc.text[:100]}...")
    print(f"  Entities ({len(doc.ents)}):")
    for ent in doc.ents:
        print(f"    - '{ent.text}' ({ent.label_}) [{ent.start}:{ent.end}]")

# Label distribution
from collections import Counter
all_labels = [ent.label_ for doc in docs for ent in doc.ents]
label_counts = Counter(all_labels)
print("\nLabel Distribution:")
for label, count in label_counts.items():
    print(f"  {label}: {count}")
```

**Expected Statistics**:
- Train: 3,191 docs, ~8,000-12,000 entities (2-4 per doc)
- Dev: 684 docs, ~1,700-2,500 entities
- Test: 684 docs, ~1,700-2,500 entities
- Label ratio: B-COM ~60%, B-FUL ~40%

**Output Files**:
- `data/ner_training/train.spacy`
- `data/ner_training/dev.spacy`
- `data/ner_training/test.spacy`
- `data/ner_training/annotation_statistics.csv`

### 3.3 Generate Training Config

**Config Generation**:
```bash
# Generate base config
python -m spacy init config \
  --lang en \
  --pipeline ner \
  --optimize accuracy \
  data/ner_training/config_base.cfg

# Fill in defaults
python -m spacy init fill-config \
  data/ner_training/config_base.cfg \
  data/ner_training/config.cfg
```

**Manual Configuration** (`data/ner_training/config.cfg`):

Key sections to customize:

```ini
[nlp]
lang = "en"
pipeline = ["ner"]
batch_size = 1000

[components.ner]
factory = "ner"

[components.ner.model]
@architectures = "spacy.TransitionBasedParser.v2"
state_type = "ner"
extra_state_tokens = false
hidden_width = 64
maxout_pieces = 3
use_upper = true

[components.ner.model.tok2vec]
@architectures = "spacy.HashEmbedCNN.v2"
pretrained_vectors = null
width = 96
depth = 4
embed_size = 2000
window_size = 1
maxout_pieces = 3
subword_features = true

[training]
dev_corpus = "corpora.dev"
train_corpus = "corpora.train"
seed = 42
gpu_allocator = "pytorch"  # For Colab GPU
accumulate_gradient = 3
max_epochs = 20
patience = 5

[training.batcher]
@batchers = "spacy.batch_by_words.v1"
discard_oversize = false
tolerance = 0.2

[training.batcher.size]
@schedules = "compounding.v1"
start = 100
stop = 1000
compound = 1.001

[training.optimizer]
@optimizers = "Adam.v1"
beta1 = 0.9
beta2 = 0.999
L2_is_weight_decay = true
L2 = 0.01
grad_clip = 1.0
use_averages = false
eps = 0.00000001
learn_rate = 0.001

[initialize.components]
[initialize.components.ner]
labels = ["B-COM", "I-COM", "B-FUL", "I-FUL"]

[corpora]
[corpora.train]
@readers = "spacy.Corpus.v1"
path = ${paths.train}
max_length = 0

[corpora.dev]
@readers = "spacy.Corpus.v1"
path = ${paths.dev}
max_length = 0

[paths]
train = "data/ner_training/train.spacy"
dev = "data/ner_training/dev.spacy"
```

**Output**: `data/ner_training/config.cfg`

### Deliverables Phase 3

- [ ] `data/ner_corpus_splits/` (train/dev/test CSVs)
- [ ] `data/ner_training/train.spacy`
- [ ] `data/ner_training/dev.spacy`
- [ ] `data/ner_training/test.spacy`
- [ ] `data/ner_training/config.cfg`
- [ ] `data/ner_training/annotation_statistics.csv`
- [ ] Quality validation: 2-4 entities/doc, 60/40 COM/FUL ratio

---

## PHASE 4: Statistical NER Training (Google Colab) (1-2 days)

### Objective

Train statistical NER model on GPU using distant supervision data.

### 4.1 Create Training Notebook

**Notebook**: `notebooks/spacy_ner_training.ipynb`

**Cell 1: Setup Environment**
```python
# Install spaCy
!pip install -U spacy==3.7.0

# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Set up paths
PROJECT_ROOT = '/content/drive/MyDrive/inventory_2022'
!mkdir -p ./data/ner_training
!mkdir -p ./models
```

**Cell 2: Copy Training Data**
```python
# Copy files from Drive to Colab (faster training)
!cp {PROJECT_ROOT}/data/ner_training/train.spacy ./data/ner_training/
!cp {PROJECT_ROOT}/data/ner_training/dev.spacy ./data/ner_training/
!cp {PROJECT_ROOT}/data/ner_training/test.spacy ./data/ner_training/
!cp {PROJECT_ROOT}/data/ner_training/config.cfg ./

print("Files copied successfully!")
!ls -lh ./data/ner_training/
```

**Cell 3: Verify Data**
```python
import spacy
from spacy.tokens import DocBin

nlp = spacy.blank("en")

# Load training data
db_train = DocBin().from_disk('./data/ner_training/train.spacy')
docs_train = list(db_train.get_docs(nlp.vocab))

db_dev = DocBin().from_disk('./data/ner_training/dev.spacy')
docs_dev = list(db_dev.get_docs(nlp.vocab))

print(f"Train documents: {len(docs_train)}")
print(f"Dev documents: {len(docs_dev)}")

# Sample entities
print("\nSample entities from training data:")
for doc in docs_train[:3]:
    print(f"\nText: {doc.text[:80]}...")
    for ent in doc.ents[:5]:
        print(f"  - '{ent.text}' ({ent.label_})")
```

**Cell 4: Train Model**
```bash
%%bash
# Train with GPU
python -m spacy train \
  config.cfg \
  --output ./models/ner_statistical \
  --paths.train ./data/ner_training/train.spacy \
  --paths.dev ./data/ner_training/dev.spacy \
  --gpu-id 0 \
  --verbose
```

**Expected Training Output**:
```
=========================== Initializing pipeline ===========================
[...]

============================ Training pipeline ============================
E    #       LOSS NER  ENTS_F  ENTS_P  ENTS_R  SCORE
---  ------  --------  ------  ------  ------  ------
  0       0      0.00    0.00    0.00    0.00    0.00
  1     200    245.67   45.32   52.14   40.12    0.45
  2     400    178.23   58.76   62.45   55.48    0.59
  3     600    134.56   65.89   68.23   63.72    0.66
[...]
 15    3000     45.12   72.45   75.34   69.78    0.72
 16    3200     43.87   73.12   76.01   70.48    0.73  ← Best
 17    3400     42.34   72.98   75.87   70.32    0.73
 18    3600     41.23   72.76   75.45   70.28    0.73
[Early stopping triggered - no improvement for 5 epochs]

✔ Saved pipeline to output directory
./models/ner_statistical/model-best
```

**Cell 5: Evaluate on Test Set**
```python
import spacy

# Load best model
nlp = spacy.load("./models/ner_statistical/model-best")

# Test on sample text
test_text = """
The Clinical Genome Resource (ClinGen) and the OMIM database provide
comprehensive genetic information. We also analyzed a new Genomics Repository.
"""

doc = nlp(test_text)

print("Extracted Entities:")
for ent in doc.ents:
    print(f"  - '{ent.text}' ({ent.label_})")
```

**Cell 6: Quantitative Evaluation**
```bash
%%bash
python -m spacy evaluate \
  ./models/ner_statistical/model-best \
  ./data/ner_training/test.spacy \
  --output ./models/ner_statistical/test_evaluation.json \
  --gpu-id 0
```

**Expected Test Metrics**:
```
================================== Results ==================================

TOK                 100.00
NER P               75.23
NER R               68.45
NER F               71.67
ENTS_PER_TYPE       {'B-COM': {'p': 77.45, 'r': 70.12, 'f': 73.61},
                     'B-FUL': {'p': 72.34, 'r': 65.78, 'f': 68.91}}
```

**Target**: F1 >70% (acceptable for distant supervision quality)

**Cell 7: Error Analysis**
```python
import spacy
from spacy.tokens import DocBin

nlp_trained = spacy.load("./models/ner_statistical/model-best")
nlp_blank = spacy.blank("en")

# Load test data
db_test = DocBin().from_disk('./data/ner_training/test.spacy')
test_docs = list(db_test.get_docs(nlp_blank.vocab))

# Compare predictions vs gold
errors = []
for gold_doc in test_docs[:20]:
    # Predict
    pred_doc = nlp_trained(gold_doc.text)

    # Compare
    gold_ents = [(ent.text, ent.label_, ent.start, ent.end) for ent in gold_doc.ents]
    pred_ents = [(ent.text, ent.label_, ent.start, ent.end) for ent in pred_doc.ents]

    # False negatives (in gold, not in pred)
    fn = [g for g in gold_ents if g not in pred_ents]

    # False positives (in pred, not in gold)
    fp = [p for p in pred_ents if p not in gold_ents]

    if fn or fp:
        errors.append({
            'text': gold_doc.text[:100] + '...',
            'false_negatives': fn,
            'false_positives': fp
        })

print(f"Documents with errors: {len(errors)}")
for err in errors[:5]:
    print(f"\nText: {err['text']}")
    if err['false_negatives']:
        print(f"  Missed (FN): {err['false_negatives']}")
    if err['false_positives']:
        print(f"  Over-extracted (FP): {err['false_positives']}")
```

**Cell 8: Save Model to Drive**
```python
# Copy trained model back to Drive
!cp -r ./models/ner_statistical/model-best {PROJECT_ROOT}/models/ner_statistical

print("Model saved to Google Drive!")
print(f"Location: {PROJECT_ROOT}/models/ner_statistical")
```

### 4.2 Local Validation (After Training)

**Script**: `scripts/08_validate_statistical_ner.py`

```python
import spacy

# Load trained model
nlp = spacy.load("models/ner_statistical")

# Test generalization on NEW entities
test_cases = [
    "We created the Genomics Knowledge Base (GKB).",  # NEW!
    "The Cell Atlas Repository was very useful.",     # NEW!
    "Data from PDB and UniProt were integrated.",     # KNOWN
]

for text in test_cases:
    doc = nlp(text)
    print(f"\nText: {text}")
    print(f"Entities: {[(ent.text, ent.label_) for ent in doc.ents]}")
```

**Success Criteria**:
- [x] Test F1 >70%
- [x] Can extract NEW entities not in training dictionary
- [x] Generalizes to unseen resource names

### Deliverables Phase 4

- [ ] `notebooks/spacy_ner_training.ipynb`
- [ ] `models/ner_statistical/` (trained model)
- [ ] `models/ner_statistical/test_evaluation.json`
- [ ] Test F1 >70% achieved
- [ ] Error analysis report

---

## PHASE 5: Hybrid Pipeline Integration (2-3 days)

### Objective

Combine EntityRuler + Statistical NER into production-ready hybrid pipeline.

### 5.1 Build Hybrid Pipeline

**Script**: `scripts/09_build_hybrid_pipeline.py`

```python
import spacy
from spacy.language import Language

print("Building hybrid NER pipeline...")

# Step 1: Load blank pipeline
nlp = spacy.blank("en")

# Step 2: Add EntityRuler (MUST BE FIRST!)
print("  Adding EntityRuler...")
ruler = nlp.add_pipe("entity_ruler", name="entity_ruler")
ruler.from_disk("data/patterns.jsonl")
print(f"    Patterns loaded: {len(ruler.patterns)}")

# Step 3: Add trained statistical NER (SECOND!)
print("  Adding statistical NER...")
nlp.add_pipe("ner", source=spacy.load("models/ner_statistical"))
print(f"    NER component added")

# Verify pipeline order (CRITICAL!)
print(f"\nPipeline components: {nlp.pipe_names}")
assert nlp.pipe_names == ["entity_ruler", "ner"], "Pipeline order incorrect!"

# Test on mixed entities (known + new)
test_text = """
We analyzed the Bio-Analytic Resource (BAR) and a new Genomics Knowledge Base.
The PDB and OMIM databases provided additional context.
"""

print("\n" + "="*60)
print("Testing Hybrid Pipeline")
print("="*60)

doc = nlp(test_text)

print(f"\nExtracted {len(doc.ents)} entities:")
for ent in doc.ents:
    canonical_id = ent.ent_id_ if ent.ent_id_ else "N/A (Statistical)"
    source = "EntityRuler" if ent.ent_id_ else "Statistical NER"
    print(f"  - '{ent.text}' ({ent.label_})")
    print(f"      Canonical ID: {canonical_id}")
    print(f"      Source: {source}")

# Save hybrid pipeline
output_path = "models/ner_hybrid_v1"
nlp.to_disk(output_path)
print(f"\n✓ Hybrid pipeline saved to: {output_path}")
```

**Expected Output**:
```
Building hybrid NER pipeline...
  Adding EntityRuler...
    Patterns loaded: 4823
  Adding statistical NER...
    NER component added

Pipeline components: ['entity_ruler', 'ner']

============================================================
Testing Hybrid Pipeline
============================================================

Extracted 5 entities:
  - 'Bio-Analytic Resource' (B-FUL)
      Canonical ID: BAR
      Source: EntityRuler
  - 'BAR' (B-COM)
      Canonical ID: BAR
      Source: EntityRuler
  - 'Genomics Knowledge Base' (B-FUL)
      Canonical ID: N/A (Statistical)
      Source: Statistical NER
  - 'PDB' (B-COM)
      Canonical ID: PDB
      Source: EntityRuler
  - 'OMIM' (B-COM)
      Canonical ID: OMIM
      Source: EntityRuler

✓ Hybrid pipeline saved to: models/ner_hybrid_v1
```

### 5.2 Validation on Test Set

**Script**: `scripts/10_validate_hybrid_pipeline.py`

```python
import spacy
import pandas as pd
from collections import defaultdict
import json

# Load hybrid pipeline
nlp = spacy.load("models/ner_hybrid_v1")

# Load test papers
test_df = pd.read_csv('data/ner_corpus_splits/test.csv')

print(f"Validating on {len(test_df)} test papers...")

# Track metrics
results = {
    'total_papers': len(test_df),
    'total_entities': 0,
    'ruler_entities': 0,
    'statistical_entities': 0,
    'papers_with_entities': 0,
    'entities_per_paper': [],
}

all_extractions = []

for _, paper in test_df.iterrows():
    text = paper['text']
    doc = nlp(text)

    ruler_count = 0
    stat_count = 0

    for ent in doc.ents:
        if ent.ent_id_:  # Has canonical ID → from EntityRuler
            ruler_count += 1
            source = 'ruler'
        else:  # No ID → from Statistical NER
            stat_count += 1
            source = 'statistical'

        all_extractions.append({
            'pmid': paper['pubmed_id'],
            'text': ent.text,
            'label': ent.label_,
            'canonical_id': ent.ent_id_ if ent.ent_id_ else None,
            'source': source
        })

    results['total_entities'] += len(doc.ents)
    results['ruler_entities'] += ruler_count
    results['statistical_entities'] += stat_count

    if len(doc.ents) > 0:
        results['papers_with_entities'] += 1

    results['entities_per_paper'].append(len(doc.ents))

# Calculate statistics
results['coverage'] = results['papers_with_entities'] / results['total_papers']
results['avg_entities_per_paper'] = sum(results['entities_per_paper']) / len(results['entities_per_paper'])
results['ruler_percentage'] = results['ruler_entities'] / results['total_entities']
results['statistical_percentage'] = results['statistical_entities'] / results['total_entities']

# Print report
print("\n" + "="*60)
print("HYBRID PIPELINE VALIDATION REPORT")
print("="*60)
print(f"\nPapers: {results['total_papers']}")
print(f"Papers with entities: {results['papers_with_entities']} ({results['coverage']*100:.1f}%)")
print(f"Total entities: {results['total_entities']}")
print(f"Avg entities/paper: {results['avg_entities_per_paper']:.2f}")
print(f"\nEntity Sources:")
print(f"  EntityRuler: {results['ruler_entities']} ({results['ruler_percentage']*100:.1f}%)")
print(f"  Statistical NER: {results['statistical_entities']} ({results['statistical_percentage']*100:.1f}%)")

# Save results
with open('results/phase5_hybrid_validation.json', 'w') as f:
    json.dump(results, f, indent=2)

# Save extractions
pd.DataFrame(all_extractions).to_csv('results/phase5_hybrid_extractions.csv', index=False)

print(f"\n✓ Results saved to:")
print(f"  - results/phase5_hybrid_validation.json")
print(f"  - results/phase5_hybrid_extractions.csv")
```

**Target Metrics**:
- **Coverage**: 80-85% (10-15% improvement over EntityRuler-only baseline)
- **Ruler Entities**: 70-75% (high precision known entities)
- **Statistical Entities**: 25-30% (NEW discoveries!)
- **Avg Entities/Paper**: 3-5

### 5.3 Performance Benchmarking

**Script**: `scripts/11_benchmark_hybrid_speed.py`

```python
import spacy
import pandas as pd
import time

# Load models
nlp_hybrid = spacy.load("models/ner_hybrid_v1")
nlp_ruler = spacy.blank("en")
nlp_ruler.add_pipe("entity_ruler").from_disk("data/patterns.jsonl")
nlp_statistical = spacy.load("models/ner_statistical")

# Load test data
test_df = pd.read_csv('data/ner_corpus_splits/test.csv').head(100)
texts = test_df['text'].tolist()

def benchmark(nlp, name):
    start = time.time()
    for text in texts:
        doc = nlp(text)
    end = time.time()

    elapsed = end - start
    papers_per_sec = len(texts) / elapsed

    return {
        'model': name,
        'papers': len(texts),
        'time_sec': elapsed,
        'papers_per_sec': papers_per_sec
    }

print("Benchmarking speed...")
results = []
results.append(benchmark(nlp_ruler, 'EntityRuler Only'))
results.append(benchmark(nlp_statistical, 'Statistical NER Only'))
results.append(benchmark(nlp_hybrid, 'Hybrid Pipeline'))

df = pd.DataFrame(results)
print("\n" + "="*60)
print("SPEED BENCHMARK")
print("="*60)
print(df.to_string(index=False))

# Save
df.to_csv('results/phase5_speed_benchmark.csv', index=False)
```

**Expected Speed**:
- EntityRuler Only: 150-200 papers/sec (very fast!)
- Statistical NER Only: 30-50 papers/sec (slower)
- Hybrid: 40-60 papers/sec (statistical component is bottleneck)

### 5.4 Alias Resolution Analysis

**Script**: `scripts/12_analyze_alias_resolution.py`

```python
import spacy
import pandas as pd
from collections import defaultdict

nlp = spacy.load("models/ner_hybrid_v1")

# Load test papers
test_df = pd.read_csv('data/ner_corpus_splits/test.csv')

# Track alias groups
alias_groups = defaultdict(lambda: {'mentions': [], 'papers': set()})

for _, paper in test_df.iterrows():
    text = paper['text']
    doc = nlp(text)

    for ent in doc.ents:
        if ent.ent_id_:  # Has canonical ID
            canonical = ent.ent_id_
            alias_groups[canonical]['mentions'].append(ent.text)
            alias_groups[canonical]['papers'].add(paper['pubmed_id'])

# Analyze
print("="*60)
print("ALIAS RESOLUTION ANALYSIS")
print("="*60)

# Resources with multiple aliases found
multi_alias = {k: v for k, v in alias_groups.items() if len(set(v['mentions'])) > 1}

print(f"\nTotal resources detected: {len(alias_groups)}")
print(f"Resources with multiple aliases: {len(multi_alias)}")

# Show examples
print("\nExamples of alias resolution:")
for canonical, data in list(multi_alias.items())[:10]:
    unique_mentions = set(data['mentions'])
    if len(unique_mentions) > 1:
        print(f"\n{canonical}:")
        for mention in unique_mentions:
            count = data['mentions'].count(mention)
            print(f"  - '{mention}' ({count} times)")

# Success rate
total_entities_with_id = sum(len(v['mentions']) for v in alias_groups.values())
print(f"\nAlias Resolution Success Rate:")
print(f"  Entities with canonical ID: {total_entities_with_id}")
print(f"  Resources identified: {len(alias_groups)}")
```

**Success Criteria**:
- [x] 70-80% of entities have canonical IDs
- [x] Multiple alias forms correctly linked (e.g., "BAR", "Bio-Analytic Resource")
- [x] Statistical entities (NEW) correctly have no ID

### Deliverables Phase 5

- [ ] `models/ner_hybrid_v1/` (packaged pipeline)
- [ ] `results/phase5_hybrid_validation.json`
- [ ] `results/phase5_hybrid_extractions.csv`
- [ ] `results/phase5_speed_benchmark.csv`
- [ ] Validation metrics: 80-85% coverage, 3-5 entities/paper

---

## PHASE 6: Production Deployment (2-3 days)

### Objective

Package hybrid pipeline for production use and integrate with existing infrastructure.

### 6.1 Package Pipeline

```bash
python -m spacy package \
  models/ner_hybrid_v1 \
  packages \
  --name ner_hybrid \
  --version 1.0.0 \
  --meta-path metadata.json
```

**metadata.json**:
```json
{
  "name": "en_ner_hybrid_bioresource",
  "version": "1.0.0",
  "description": "Hybrid EntityRuler + Statistical NER for bioresource entity extraction with alias resolution",
  "author": "Biodata Inventory Team",
  "license": "MIT",
  "spacy_version": ">=3.7.0,<4.0.0",
  "pipeline": ["entity_ruler", "ner"],
  "components": {
    "entity_ruler": {
      "patterns": 4823,
      "description": "Rule-based matching for known bioresources with canonical ID assignment"
    },
    "ner": {
      "labels": ["B-COM", "I-COM", "B-FUL", "I-FUL"],
      "description": "Statistical NER for discovering new bioresources"
    }
  },
  "training": {
    "corpus_size": 3191,
    "method": "distant_supervision",
    "test_f1": 0.717
  }
}
```

**Build & Install**:
```bash
cd packages/en_ner_hybrid_bioresource-1.0.0
pip install -e .

# Test installation
python -c "import spacy; nlp = spacy.load('en_ner_hybrid_bioresource'); print('✓ Package installed')"
```

### 6.2 Integration Module

**New File**: `src/ner_predict_spacy.py`

```python
"""
spaCy Hybrid NER Predictor for Bioresource Extraction

Integrates EntityRuler + Statistical NER with alias resolution.
Compatible with existing pipeline but provides enhanced capabilities.
"""

import spacy
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SpacyNERPredictor:
    """
    Hybrid NER predictor using spaCy EntityRuler + Statistical NER.

    Features:
    - High-precision extraction of known bioresources (EntityRuler)
    - Discovery of new/unknown bioresources (Statistical NER)
    - Alias resolution (links short/long forms via canonical IDs)
    """

    def __init__(self, model_path: str = "models/ner_hybrid_v1"):
        """
        Initialize predictor.

        Args:
            model_path: Path to trained spaCy hybrid pipeline
        """
        logger.info(f"Loading spaCy hybrid pipeline from {model_path}")
        self.nlp = spacy.load(model_path)

        # Verify pipeline components
        assert "entity_ruler" in self.nlp.pipe_names, "EntityRuler not found!"
        assert "ner" in self.nlp.pipe_names, "NER not found!"
        assert self.nlp.pipe_names.index("entity_ruler") < self.nlp.pipe_names.index("ner"), \
            "Pipeline order incorrect! EntityRuler must come before NER."

        logger.info(f"Pipeline components: {self.nlp.pipe_names}")

    def predict(self, papers_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extract bioresource entities from papers with alias resolution.

        Args:
            papers_df: DataFrame with columns ['pubmed_id', 'title', 'abstract']

        Returns:
            List of dicts with extracted entities and metadata
        """
        logger.info(f"Processing {len(papers_df)} papers...")

        results = []

        for idx, paper in papers_df.iterrows():
            # Concatenate title + abstract
            text = str(paper.get('title', '')) + ' ' + str(paper.get('abstract', ''))

            if len(text.strip()) < 10:
                logger.warning(f"Skipping paper {paper['pubmed_id']}: insufficient text")
                continue

            # Run hybrid pipeline
            doc = self.nlp(text)

            # Extract entities with metadata
            entities = []
            for ent in doc.ents:
                entity_data = {
                    'text': ent.text,
                    'label': ent.label_,  # B-COM, I-COM, B-FUL, I-FUL
                    'start_char': ent.start_char,
                    'end_char': ent.end_char,
                    'canonical_id': ent.ent_id_ if ent.ent_id_ else None,
                    'source': 'ruler' if ent.ent_id_ else 'statistical'
                }
                entities.append(entity_data)

            # Aggregate by canonical ID (alias resolution!)
            entities_grouped = self._group_by_canonical_id(entities)

            results.append({
                'pmid': paper['pubmed_id'],
                'entity_count': len(entities),
                'entities': entities,
                'resources': entities_grouped  # Grouped by canonical ID
            })

        logger.info(f"Extracted entities from {len(results)} papers")
        return results

    def _group_by_canonical_id(self, entities: List[Dict]) -> List[Dict]:
        """
        Group entities by canonical ID (alias resolution).

        Args:
            entities: List of entity dicts

        Returns:
            List of resource dicts with all aliases grouped
        """
        resources = {}

        for ent in entities:
            canonical = ent['canonical_id']

            if canonical:
                # Known resource with canonical ID
                if canonical not in resources:
                    resources[canonical] = {
                        'canonical_id': canonical,
                        'mentions': [],
                        'source': 'known'
                    }
                resources[canonical]['mentions'].append(ent['text'])
            else:
                # Unknown resource (from statistical NER)
                # Create temporary ID
                temp_id = f"UNKNOWN_{ent['text']}"
                if temp_id not in resources:
                    resources[temp_id] = {
                        'canonical_id': None,
                        'mentions': [ent['text']],
                        'source': 'discovered'
                    }

        return list(resources.values())

    def predict_to_csv(self, papers_df: pd.DataFrame, output_path: str):
        """
        Predict and save results to CSV.

        Args:
            papers_df: Input papers
            output_path: Path to save results CSV
        """
        results = self.predict(papers_df)

        # Flatten for CSV
        rows = []
        for result in results:
            for ent in result['entities']:
                rows.append({
                    'pmid': result['pmid'],
                    'entity_text': ent['text'],
                    'entity_label': ent['label'],
                    'canonical_id': ent['canonical_id'],
                    'source': ent['source'],
                    'start_char': ent['start_char'],
                    'end_char': ent['end_char']
                })

        df_output = pd.DataFrame(rows)
        df_output.to_csv(output_path, index=False)
        logger.info(f"Results saved to {output_path}")

        return df_output


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Load test papers
    papers = pd.read_csv('data/ner_corpus_splits/test.csv')

    # Initialize predictor
    predictor = SpacyNERPredictor("models/ner_hybrid_v1")

    # Run prediction
    results = predictor.predict(papers.head(10))

    # Print sample
    for result in results[:3]:
        print(f"\nPMID: {result['pmid']}")
        print(f"Entities found: {result['entity_count']}")
        for res in result['resources']:
            print(f"  {res['canonical_id']}: {set(res['mentions'])}")
```

### 6.3 Benchmark vs Existing Models

**Script**: `scripts/13_benchmark_all_models.py`

```python
"""
Compare spaCy Hybrid vs V2 BERT vs Phase 4 Multi-Task
"""

import pandas as pd
import time
import json
from src.ner_predict_spacy import SpacyNERPredictor

# Load test data
test_df = pd.read_csv('data/ner_corpus_splits/test.csv').head(100)

# Initialize models
print("Loading models...")
spacy_predictor = SpacyNERPredictor("models/ner_hybrid_v1")

# TODO: Add V2 BERT predictor
# from src.ner_predict import NERPredictor as BERTPredictor
# v2_predictor = BERTPredictor("out/ner_train_out/named_entity_recognition_v2.pt")

# Benchmark spaCy Hybrid
print("\nBenchmarking spaCy Hybrid...")
start = time.time()
spacy_results = spacy_predictor.predict(test_df)
spacy_time = time.time() - start

spacy_metrics = {
    'model': 'spaCy Hybrid',
    'papers': len(test_df),
    'time_sec': spacy_time,
    'papers_per_sec': len(test_df) / spacy_time,
    'total_entities': sum(r['entity_count'] for r in spacy_results),
    'avg_entities_per_paper': sum(r['entity_count'] for r in spacy_results) / len(spacy_results),
    'entities_with_id': sum(1 for r in spacy_results for e in r['entities'] if e['canonical_id']),
    'alias_resolution': 'Yes'
}

# TODO: Benchmark V2 BERT
# v2_metrics = {...}

# TODO: Benchmark Phase 4 (if bug fixed)
# phase4_metrics = {...}

# Comparison table
comparison = pd.DataFrame([spacy_metrics])  # Add v2_metrics, phase4_metrics
print("\n" + "="*80)
print("MODEL COMPARISON")
print("="*80)
print(comparison.to_string(index=False))

# Save
comparison.to_csv('results/phase6_model_comparison.csv', index=False)
```

### 6.4 Full Scale Inference (Colab)

**Notebook**: `notebooks/spacy_full_inference_v5.ipynb`

**Purpose**: Run hybrid pipeline on full V5.1 query results (153k papers)

**Cell 1: Setup**
```python
!pip install spacy==3.7.0

from google.colab import drive
drive.mount('/content/drive')

# Copy model
!cp -r /content/drive/MyDrive/inventory_2022/models/ner_hybrid_v1 ./
```

**Cell 2: Load Data**
```python
import pandas as pd

# Load V5.1 query results
df = pd.read_csv('/content/drive/MyDrive/inventory_2022/data/final_query_v5.1_2011_2021/query_results.csv')

print(f"Total papers: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
```

**Cell 3: Run Inference**
```python
import spacy
from tqdm import tqdm

nlp = spacy.load('ner_hybrid_v1')

results = []

for idx, paper in tqdm(df.iterrows(), total=len(df)):
    text = str(paper['title']) + ' ' + str(paper.get('abstract', ''))

    if len(text.strip()) < 10:
        continue

    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        entities.append({
            'text': ent.text,
            'label': ent.label_,
            'canonical_id': ent.ent_id_ if ent.ent_id_ else None
        })

    if entities:
        results.append({
            'pmid': paper['id'],
            'entity_count': len(entities),
            'entities': entities
        })

print(f"Papers with entities: {len(results)}")
```

**Cell 4: Save Results**
```python
import json

# Save to Drive
with open('/content/drive/MyDrive/inventory_2022/results/spacy_hybrid_v5_full_inference.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Results saved!")
```

### Deliverables Phase 6

- [ ] `packages/en_ner_hybrid_bioresource-1.0.0/` (packaged model)
- [ ] `src/ner_predict_spacy.py` (integration module)
- [ ] `results/phase6_model_comparison.csv`
- [ ] `notebooks/spacy_full_inference_v5.ipynb`
- [ ] Production deployment documentation

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

## Risk Mitigation

### Risk 1: Low Distant Supervision Quality

**Symptom**: Statistical NER F1 <60%

**Mitigation**:
1. Improve pattern matching (more careful regex, case-insensitive)
2. Add negative examples (non-bioresource entities)
3. Use Snorkel for principled weak supervision (Advanced Strategy 4)
4. Supplement with 50-100 manual annotations
5. Adjust training hyperparameters (learning rate, dropout)

### Risk 2: EntityRuler Memory Issues

**Symptom**: Pipeline loads slowly (>10 seconds for 5,000 patterns)

**Mitigation**:
1. Profile memory usage: `python -m memory_profiler scripts/04_test_entityruler_pipeline.py`
2. Consider PhraseMatcher for phrase patterns (faster than token patterns)
3. For massive scale (>10k patterns), use Aho-Corasick (flashtext library)
4. Split patterns into multiple files, load incrementally

### Risk 3: Statistical Model Overfits Dictionary

**Symptom**: Can't generalize to new entities (only extracts known ones)

**Mitigation**:
1. Add more diverse training data (papers outside bioresource corpus)
2. Increase regularization (L2 weight decay, dropout)
3. Data augmentation (synonym replacement, paraphrasing)
4. Use pre-trained biomedical embeddings (BioBERT, SciBERT)

### Risk 4: Hybrid Pipeline Conflicts

**Symptom**: EntityRuler and NER produce overlapping/contradictory entities

**Mitigation**:
1. Verify pipeline order (EntityRuler MUST be first)
2. Use `nlp.pipe_names` to inspect component order
3. Test with `nlp.analyze_pipes()` to see data flow
4. Manually inspect doc.ents at each pipeline stage

### Risk 5: Slow Inference on Production Scale

**Symptom**: <10 papers/sec on 153k dataset (>4 hours processing time)

**Mitigation**:
1. Use `nlp.pipe()` for batch processing (10-20x speedup)
2. Enable GPU in Colab: `spacy.prefer_gpu()`
3. Disable unnecessary pipeline components during inference
4. Use multiprocessing: `spacy.util.use_multiprocessing()`

---

## Timeline & Milestones

| Week | Phase | Key Deliverables | Risk Level |
|------|-------|------------------|------------|
| **Week 1** | Phase 1 + 2 | Dictionary enriched, EntityRuler validated | Low |
| **Week 2** | Phase 3 | Training data created (.spacy files) | Medium |
| **Week 3** | Phase 4 + 5 | Statistical NER trained, Hybrid pipeline | Medium |
| **Week 4** | Phase 6 | Production deployment, benchmarks | Low |

**Total Duration**: 14-20 days (3-4 weeks)

**Critical Path**: Phase 3 (distant supervision) → Phase 4 (training) → Phase 5 (hybrid integration)

---

## Documentation Requirements

### Technical Documentation

1. **SPACY_NER_IMPLEMENTATION.md**:
   - Architecture overview
   - Component descriptions
   - Configuration details
   - Training procedure
   - Evaluation metrics

2. **ALIAS_RESOLUTION_GUIDE.md**:
   - How to use canonical IDs
   - Example queries
   - Troubleshooting

3. **HYBRID_PIPELINE_ARCHITECTURE.md**:
   - System design
   - Data flow diagrams
   - Component interaction
   - Performance characteristics

### User Documentation

1. **QUICK_START_SPACY_NER.md**:
   - Installation
   - Basic usage examples
   - Common pitfalls

2. **API_REFERENCE.md**:
   - `SpacyNERPredictor` class documentation
   - Method signatures
   - Return formats

### Maintenance Documentation

1. **UPDATE_PATTERNS_GUIDE.md**:
   - How to add new resources to dictionary
   - Regenerate patterns.jsonl
   - Retrain statistical model (if needed)

2. **TROUBLESHOOTING.md**:
   - Common errors
   - Performance tuning
   - Debugging tips

---

## Next Steps After Completion

### Short-term (1-2 weeks)

1. **Manual validation** of high-value subset (e.g., 100 papers)
2. **Compare** spaCy Hybrid vs V2 BERT on same test set
3. **Fix Phase 4 bug** (if not yet done) and compare to hybrid
4. **Deploy** hybrid pipeline to staging environment

### Medium-term (1-2 months)

1. **Continuous dictionary enrichment** (add new resources as discovered)
2. **Active learning** pipeline (select uncertain cases for manual annotation)
3. **Fine-tune** statistical NER on manual annotations
4. **Scale testing** on full production dataset (40k papers)

### Long-term (3-6 months)

1. **Snorkel integration** (Advanced Strategy 4) for better training data
2. **Multi-language support** (if needed)
3. **API endpoint** for real-time entity extraction
4. **Integration** with PyCaret metadata classifier (two-stage pipeline)

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

**Plan Status**: ✅ Approved
**Created**: November 12, 2025
**Next Review**: After Phase 2 completion
