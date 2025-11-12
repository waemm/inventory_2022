# Distant Supervision & Statistical NER Training (Phases 3-4)

**Duration**: 5-7 days combined
**Prerequisites**: Phases 1-2 complete, EntityRuler validated
**Output**: Trained statistical NER model (F1 >70%)

---

## PHASE 3: Distant Supervision Training Data (4-5 days)

### Objective

Create spaCy-compatible training data (.spacy format) using distant supervision from the bioresource dictionary.

**Key Concept**: Auto-annotate 4,559 papers by matching dictionary patterns → generates 8k-12k training examples automatically!

---

### 3.1 Prepare Paper Corpus

**Script**: `scripts/06_prepare_training_corpus.py`

**Processing**:
```python
import pandas as pd
from sklearn.model_selection import train_test_split

# Load bioresource papers
df = pd.read_csv('/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv')

# Merge with metadata (if available)
metadata_path = 'data/metadata/pmc_metadata_enhanced_full.csv'
try:
    metadata = pd.read_csv(metadata_path)
    df = df.merge(metadata, left_on='pubmed_id', right_on='id', how='left', suffixes=('', '_meta'))
    print(f"Merged with {len(metadata)} metadata records")
except FileNotFoundError:
    print("Metadata not found, using papers only")

# Concatenate title + abstract
df['text'] = df['title'] + ' ' + df['abstract'].fillna('')

# Filter: must have text
df = df[df['text'].str.len() > 50]  # At least 50 chars

print(f"Total papers with text: {len(df)}")

# Train/Dev/Test split (70/15/15)
train, temp = train_test_split(df, test_size=0.30, random_state=42, stratify=None)
dev, test = train_test_split(temp, test_size=0.50, random_state=42, stratify=None)

print(f"Train: {len(train)} papers")
print(f"Dev: {len(dev)} papers")
print(f"Test: {len(test)} papers")

# Create output directory
import os
os.makedirs('data/ner_corpus_splits', exist_ok=True)

# Save splits
train.to_csv('data/ner_corpus_splits/train.csv', index=False)
dev.to_csv('data/ner_corpus_splits/dev.csv', index=False)
test.to_csv('data/ner_corpus_splits/test.csv', index=False)

print("\n✓ Corpus splits saved to data/ner_corpus_splits/")
```

**Expected Output**:
- Train: ~3,191 papers (70%)
- Dev: ~684 papers (15%)
- Test: ~684 papers (15%)

**Success Criteria**:
- [ ] 3 CSV files created
- [ ] Train:Dev:Test ratio is 70:15:15
- [ ] All papers have text content (>50 chars)

---

### 3.2 Auto-Annotate with Dictionary (Distant Supervision)

**Script**: `scripts/07_distant_supervision_annotation.py`

This is the **most critical script** - implements the distant supervision algorithm from the research document.

**Core Algorithm**:
```python
import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans
import pandas as pd
import re
from tqdm import tqdm
import json
import os

# Create output directory
os.makedirs('data/ner_training', exist_ok=True)

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

print(f"Regex pattern compiled successfully")

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
        'avg_per_doc': total_entities / total_docs if total_docs > 0 else 0,
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

print("\n✓ Distant supervision annotation complete!")
```

**Quality Validation**:
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

**Why "contract" alignment mode?**

- `char_span(start, end, alignment_mode="contract")` ensures spans align with token boundaries
- If a span doesn't align perfectly (e.g., cuts through middle of token), it returns `None`
- This filters out noisy annotations from imperfect regex matches
- Trade-off: Slightly lower recall, much higher precision

**Success Criteria**:
- [ ] 3 .spacy files created
- [ ] 2-4 entities per document on average
- [ ] B-COM:B-FUL ratio approximately 60:40
- [ ] No annotation errors when inspecting samples

---

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

**Success Criteria**:
- [ ] config.cfg file created
- [ ] Labels correctly specified: B-COM, I-COM, B-FUL, I-FUL
- [ ] Paths point to correct .spacy files

---

### Phase 3 Deliverables

- [ ] `data/ner_corpus_splits/train.csv`
- [ ] `data/ner_corpus_splits/dev.csv`
- [ ] `data/ner_corpus_splits/test.csv`
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

**Why Colab?** Free GPU access, faster training (10-30 min vs hours on CPU)

---

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

**Cell 7: Save Model to Drive**
```python
# Copy trained model back to Drive
!cp -r ./models/ner_statistical/model-best {PROJECT_ROOT}/models/ner_statistical

print("Model saved to Google Drive!")
print(f"Location: {PROJECT_ROOT}/models/ner_statistical")
```

---

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

print("Testing generalization to NEW entities...")
print("=" * 60)

for text in test_cases:
    doc = nlp(text)
    print(f"\nText: {text}")
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    print(f"Entities: {entities}")

    # Check if NEW entities detected
    if entities:
        print("  ✓ Generalization successful!" if "NEW" in text else "  ✓ Known entity detected")
    else:
        print("  ✗ No entities found")

print("\n" + "=" * 60)
print("If NEW entities are detected, statistical model is generalizing correctly!")
```

**Success Criteria**:
- [ ] Test F1 >70%
- [ ] Can extract NEW entities not in training dictionary
- [ ] Generalizes to unseen resource names (this is the key!)

---

### Phase 4 Deliverables

- [ ] `notebooks/spacy_ner_training.ipynb`
- [ ] `models/ner_statistical/` (trained model)
- [ ] `models/ner_statistical/test_evaluation.json`
- [ ] Test F1 >70% achieved
- [ ] NEW entity detection validated

---

## Key Concepts

### Distant Supervision vs Manual Annotation

| Aspect | Distant Supervision | Manual Annotation |
|--------|---------------------|-------------------|
| Cost | $0 | $1,000s |
| Time | 1-2 days | 2-3 weeks |
| Quality | Noisy (~80% correct) | High (~95% correct) |
| Scale | 4,559 papers | 100-500 papers |
| Coverage | Limited by dictionary | Comprehensive |

**Trade-off**: We accept lower quality (F1 ~70%) to get massive scale (4,559 papers).

### Why Use .spacy Format (DocBin)?

- **Efficient**: Binary format, 10x smaller than JSON
- **Fast**: Loads quickly during training
- **Compatible**: Works with spaCy's training CLI
- **Portable**: Single file contains all annotations

---

## Troubleshooting

### Issue: Annotation produces 0 entities

**Cause**: Regex pattern not matching

**Debug**:
```python
# Test regex manually
import re
pattern = r'\b(PDB|BAR|OMIM)\b'
text = "We used the PDB database."
matches = re.findall(pattern, text, re.IGNORECASE)
print(matches)  # Should print: ['PDB']
```

### Issue: Training F1 <60%

**Causes**:
1. Poor annotation quality (too many false positives in distant supervision)
2. Model underfitting (not enough training data or epochs)
3. Model overfitting (too complex for data size)

**Solutions**:
1. Improve annotation: stricter regex, case-sensitive matching
2. Train longer: increase `max_epochs` from 20 to 50
3. Add regularization: increase `L2` from 0.01 to 0.05

### Issue: Training too slow (>2 hours)

**Cause**: Running on CPU instead of GPU

**Fix**:
```python
# In Colab, check GPU is enabled
!nvidia-smi  # Should show GPU info

# In training config, verify:
# [training]
# gpu_allocator = "pytorch"
```

---

## Next Steps

After Phase 4 completion, proceed to **Phase 5: Hybrid Pipeline Integration** (see `03_DEPLOYMENT_PHASES_5_6.md`)
