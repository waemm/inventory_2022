# Troubleshooting & Risk Mitigation Guide

**Purpose**: Comprehensive guide for debugging issues and mitigating risks throughout implementation
**Audience**: Developers and AI agents working on spaCy hybrid NER project

---

## Risk Assessment Matrix

| Risk | Probability | Impact | Mitigation Priority |
|------|------------|--------|-------------------|
| Low distant supervision quality | Medium | High | **CRITICAL** |
| EntityRuler memory issues | Low | Medium | Monitor |
| Statistical model overfits | Medium | High | **CRITICAL** |
| Hybrid pipeline conflicts | Low | Critical | Test early |
| Slow inference at scale | Medium | Medium | **IMPORTANT** |

---

## RISK 1: Low Distant Supervision Quality

### Symptoms

- Statistical NER F1 <60% on test set
- High false positive rate (extracts non-bioresources)
- Model can't generalize to NEW entities
- Training loss doesn't decrease below 50

### Root Causes

1. **Noisy annotations**: Regex matches incorrect spans
2. **Insufficient training data**: <2,000 annotated documents
3. **Label imbalance**: 90% B-COM, 10% B-FUL
4. **Overfitting to dictionary**: Model memorizes instead of learning patterns

### Diagnosis Steps

```python
# Step 1: Inspect annotation quality
import spacy
from spacy.tokens import DocBin

nlp = spacy.blank("en")
db = DocBin().from_disk('data/ner_training/train.spacy')
docs = list(db.get_docs(nlp.vocab))

# Check for suspicious patterns
suspicious = []
for doc in docs:
    for ent in doc.ents:
        # Flag very short entities (likely noise)
        if len(ent.text) <= 2:
            suspicious.append((doc.text[:50], ent.text, ent.label_))

print(f"Suspicious annotations: {len(suspicious)}")
for text, ent, label in suspicious[:10]:
    print(f"  '{ent}' ({label}) in: {text}...")

# Step 2: Check label distribution
from collections import Counter
labels = [ent.label_ for doc in docs for ent in doc.ents]
print("\nLabel distribution:")
for label, count in Counter(labels).items():
    print(f"  {label}: {count} ({count/len(labels)*100:.1f}%)")
```

### Mitigation Strategies

#### Strategy A: Improve Pattern Matching (Quick Win)

```python
# More strict regex with word boundaries and context
pattern = r'\b(?:the\s+)?(' + '|'.join(re.escape(alias) for alias in aliases) + r')\b(?:\s+(?:database|resource))?'

# Case-sensitive for acronyms only
if alias.isupper():
    pattern_case_sensitive = r'\b' + re.escape(alias) + r'\b'
else:
    pattern_case_insensitive = r'\b' + re.escape(alias) + r'\b'
    regex = re.compile(pattern_case_insensitive, re.IGNORECASE)
```

#### Strategy B: Add Negative Examples

```python
# Add common false positives to exclusion list
false_positives = ['DNA', 'RNA', 'PCR', 'HIV', 'USA']  # Generic terms

# Filter out during annotation
if matched_text.upper() in false_positives:
    continue  # Skip this match
```

#### Strategy C: Supplement with Manual Annotations

```python
# Add 50-100 manually annotated papers to training data
# Focus on hard cases: NEW entities, ambiguous contexts

# Merge manual + distant supervision
manual_db = DocBin().from_disk('data/manual_annotations.spacy')
distant_db = DocBin().from_disk('data/ner_training/train.spacy')

merged_db = DocBin()
for doc in list(manual_db.get_docs(nlp.vocab)) + list(distant_db.get_docs(nlp.vocab)):
    merged_db.add(doc)

merged_db.to_disk('data/ner_training/train_merged.spacy')
```

#### Strategy D: Use Snorkel for Principled Weak Supervision (Advanced)

See research document for full implementation (Advanced Strategy 4).

#### Strategy E: Adjust Training Hyperparameters

```ini
# In config.cfg, increase regularization
[training.optimizer]
L2 = 0.05  # Increased from 0.01

[training]
dropout = 0.3  # Add dropout

# Train longer
max_epochs = 50  # Increased from 20
patience = 10   # More patience
```

---

## RISK 2: EntityRuler Memory Issues

### Symptoms

- Pipeline takes >10 seconds to load
- High memory usage (>2 GB for patterns)
- Slow inference (<10 papers/sec)
- Out of memory errors on large-scale inference

### Root Causes

1. Too many patterns (>10,000)
2. Complex token patterns (nested attributes)
3. Loading patterns repeatedly instead of caching

### Diagnosis Steps

```python
# Profile memory usage
import time
import psutil
import os

process = psutil.Process(os.getpid())

# Before loading
mem_before = process.memory_info().rss / 1024 / 1024  # MB

# Load EntityRuler
start = time.time()
nlp = spacy.blank("en")
ruler = nlp.add_pipe("entity_ruler")
ruler.from_disk("data/patterns.jsonl")
load_time = time.time() - start

# After loading
mem_after = process.memory_info().rss / 1024 / 1024  # MB

print(f"Load time: {load_time:.2f} seconds")
print(f"Memory usage: {mem_after - mem_before:.2f} MB")
print(f"Patterns loaded: {len(ruler.patterns)}")

# Benchmark: Should be <5 sec, <500 MB for 5,000 patterns
```

### Mitigation Strategies

#### Strategy A: Use PhraseMatcher for Phrase Patterns

```python
from spacy.matcher import PhraseMatcher

# Instead of EntityRuler for phrase patterns
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

# Add patterns
for resource_id, data in dictionary.items():
    if data['full_name']:
        doc = nlp.make_doc(data['full_name'])
        matcher.add(resource_id, [doc])

# Faster loading, lower memory
```

#### Strategy B: Use Aho-Corasick for Massive Scale

```python
# For >10k patterns, use flashtext library
from flashtext import KeywordProcessor

processor = KeywordProcessor(case_sensitive=False)

# Add keywords
for resource_id, data in dictionary.items():
    processor.add_keyword(data['short_name'], resource_id)
    if data['full_name']:
        processor.add_keyword(data['full_name'], resource_id)

# Extract
keywords_found = processor.extract_keywords(text)
```

#### Strategy C: Split Patterns into Multiple Files

```python
# Split patterns by frequency or resource type
high_freq_patterns = [p for p in patterns if dictionary[p['id']]['paper_count'] > 10]
low_freq_patterns = [p for p in patterns if dictionary[p['id']]['paper_count'] <= 10]

# Load only high-frequency patterns for initial pass
ruler_high = nlp.add_pipe("entity_ruler", name="ruler_high")
ruler_high.from_disk("data/patterns_high_freq.jsonl")

# Load low-frequency patterns only if needed
```

---

## RISK 3: Statistical Model Overfits Dictionary

### Symptoms

- Training F1 >90%, Test F1 <60% (huge gap!)
- Can't extract NEW entities (only finds known ones)
- Model outputs same entities regardless of context
- Perfect recall on training set, poor recall on test set

### Root Causes

1. Model memorizes dictionary instead of learning patterns
2. Training data too homogeneous (all bioresource papers)
3. No negative examples (non-bioresource entities)
4. Model too complex for data size

### Diagnosis Steps

```python
# Test on completely NEW entities
test_cases = [
    "The Genomics Knowledge Repository (GKR) is a database.",  # NEW
    "We used the Cell Atlas Platform.",  # NEW
    "Data from the Metabolomics Warehouse (MW).",  # NEW
]

nlp = spacy.load("models/ner_statistical")

print("Testing on NEW entities:")
for text in test_cases:
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    if entities:
        print(f"  ✓ {text} → {entities}")
    else:
        print(f"  ✗ {text} → No entities found (OVERFITTING!)")
```

### Mitigation Strategies

#### Strategy A: Add Diverse Training Data

```python
# Add papers from outside bioresource corpus
# Include biology papers WITHOUT bioresources (negative examples)

from sklearn.model_selection import train_test_split

# Mix bioresource + general biology papers
mixed_corpus = pd.concat([
    bioresource_papers,  # 4,559 papers
    general_biology_papers.sample(1000)  # 1,000 papers without bioresources
])

# Re-split
train, temp = train_test_split(mixed_corpus, test_size=0.30, random_state=42)
# ...
```

#### Strategy B: Increase Regularization

```ini
# In config.cfg
[training.optimizer]
L2 = 0.05  # Increased from 0.01

[components.ner.model]
dropout = 0.3  # Add dropout
```

#### Strategy C: Data Augmentation

```python
# Synonym replacement
import nlpaug.augmenter.word as naw

aug = naw.SynonymAug(aug_src='wordnet')

for doc in training_docs:
    augmented_text = aug.augment(doc.text)
    # Create new training example with same labels
```

#### Strategy D: Use Pre-trained Biomedical Embeddings

```python
# Download BioBERT or SciBERT embeddings
# Add to config.cfg

[components.ner.model.tok2vec]
@architectures = "spacy-transformers.TransformerModel.v1"
name = "allenai/scibert_scivocab_uncased"
```

---

## RISK 4: Hybrid Pipeline Conflicts

### Symptoms

- EntityRuler entities get overwritten by Statistical NER
- Known entities lose canonical IDs
- Overlapping entities (same span, different labels)
- Lower precision than EntityRuler-only baseline

### Root Causes

1. **Pipeline order wrong**: Statistical NER before EntityRuler
2. **Span overlap**: Both components tag same text differently
3. **Component interference**: One component blocks the other

### Diagnosis Steps

```python
# Step 1: Check pipeline order
nlp = spacy.load("models/ner_hybrid_v1")
print(f"Pipeline: {nlp.pipe_names}")

# MUST be: ['entity_ruler', 'ner']
# NOT: ['ner', 'entity_ruler']

# Step 2: Test with known entity
text = "The Protein Domain Database (PDB) is useful."
doc = nlp(text)

for ent in doc.ents:
    print(f"  {ent.text} → ID: {ent.ent_id_} (Label: {ent.label_})")

# PDB should have canonical ID
# If no ID, EntityRuler not working!

# Step 3: Analyze component outputs separately
nlp_ruler = spacy.blank("en")
nlp_ruler.add_pipe("entity_ruler").from_disk("data/patterns.jsonl")
doc_ruler = nlp_ruler(text)

nlp_statistical = spacy.load("models/ner_statistical")
doc_stat = nlp_statistical(text)

print("\nEntityRuler output:")
for ent in doc_ruler.ents:
    print(f"  {ent.text} (ID: {ent.ent_id_})")

print("\nStatistical NER output:")
for ent in doc_stat.ents:
    print(f"  {ent.text} (ID: {ent.ent_id_})")

print("\nHybrid output:")
for ent in doc.ents:
    print(f"  {ent.text} (ID: {ent.ent_id_})")
```

### Mitigation Strategies

#### Strategy A: Verify Pipeline Order

```python
# Rebuild pipeline in correct order
nlp = spacy.blank("en")

# 1. EntityRuler FIRST
ruler = nlp.add_pipe("entity_ruler", name="entity_ruler")
ruler.from_disk("data/patterns.jsonl")

# 2. Statistical NER SECOND
nlp_statistical = spacy.load("models/ner_statistical")
nlp.add_pipe("ner", source=nlp_statistical)

# Verify
assert nlp.pipe_names == ["entity_ruler", "ner"]
```

#### Strategy B: Configure EntityRuler to Overwrite

```python
# Add EntityRuler with overwrite_ents=True
ruler = nlp.add_pipe("entity_ruler", config={"overwrite_ents": True})

# This ensures EntityRuler has final say on conflicts
```

#### Strategy C: Use Entity Linking Component

```python
# Add entity linking component AFTER both NER components
# Links statistical entities to dictionary (if possible)

from spacy.kb import KnowledgeBase

kb = KnowledgeBase(vocab=nlp.vocab, entity_vector_length=96)
# Add entities from dictionary
# ...

nlp.add_pipe("entity_linker", config={"kb": kb})
```

---

## RISK 5: Slow Inference on Production Scale

### Symptoms

- Processing 153k papers takes >4 hours
- <10 papers/sec throughput
- High CPU usage but low GPU usage
- Memory usage grows over time (memory leak)

### Root Causes

1. Not using batch processing (`nlp.pipe()`)
2. GPU not enabled or not used
3. Inefficient text preprocessing
4. Loading model repeatedly

### Diagnosis Steps

```python
import time
import pandas as pd

# Load test data
df = pd.read_csv('data/test_papers.csv').head(1000)
texts = df['text'].tolist()

# Test 1: Sequential processing (BAD)
nlp = spacy.load("models/ner_hybrid_v1")
start = time.time()
for text in texts:
    doc = nlp(text)
time_sequential = time.time() - start

# Test 2: Batch processing (GOOD)
start = time.time()
docs = list(nlp.pipe(texts))
time_batch = time.time() - start

print(f"Sequential: {len(texts)/time_sequential:.2f} papers/sec")
print(f"Batch: {len(texts)/time_batch:.2f} papers/sec")
print(f"Speedup: {time_sequential/time_batch:.2f}x")
```

### Mitigation Strategies

#### Strategy A: Use Batch Processing

```python
# Instead of:
results = []
for text in texts:
    doc = nlp(text)  # Slow!
    results.append(doc)

# Use:
docs = list(nlp.pipe(texts, batch_size=50))  # 10-20x faster!
```

#### Strategy B: Enable GPU in Colab

```python
# Check GPU available
!nvidia-smi

# Enable GPU in spaCy
import spacy
spacy.prefer_gpu()

# Load model
nlp = spacy.load("models/ner_hybrid_v1")
```

#### Strategy C: Disable Unnecessary Components

```python
# If only need entities (not tokenization details)
nlp = spacy.load("models/ner_hybrid_v1", disable=["tagger", "parser"])

# Or select specific components
with nlp.select_pipes(enable=["entity_ruler", "ner"]):
    docs = nlp.pipe(texts)
```

#### Strategy D: Use Multiprocessing

```python
from multiprocessing import Pool
import spacy

def process_batch(texts):
    nlp = spacy.load("models/ner_hybrid_v1")
    return list(nlp.pipe(texts))

# Split data into chunks
chunk_size = 1000
chunks = [texts[i:i+chunk_size] for i in range(0, len(texts), chunk_size)]

# Process in parallel
with Pool(4) as pool:
    results = pool.map(process_batch, chunks)
```

---

## Common Errors & Solutions

### Error: "Can't find model 'en_core_web_sm'"

**Cause**: spaCy model not downloaded

**Solution**:
```bash
python -m spacy download en_core_web_sm
```

**Note**: We use `spacy.blank("en")` so this shouldn't happen unless following wrong tutorial.

---

### Error: "Pipeline component 'entity_ruler' not found"

**Cause**: Trying to load EntityRuler before adding it to pipeline

**Solution**:
```python
# Don't do this:
nlp = spacy.load("models/ner_hybrid_v1")
ruler = nlp.get_pipe("entity_ruler")  # Error!

# Do this:
nlp = spacy.blank("en")
ruler = nlp.add_pipe("entity_ruler")  # Create first
ruler.from_disk("data/patterns.jsonl")  # Then load
```

---

### Error: "alignment_mode 'contract' returns None for all spans"

**Cause**: Tokenization doesn't align with character spans

**Solution**:
```python
# Debug tokenization
text = "The PDB-101 database"
doc = nlp.make_doc(text)
print([token.text for token in doc])
# Output: ['The', 'PDB', '-', '101', 'database']

# Adjust regex to match token boundaries
# Instead of matching "PDB-101", match just "PDB"
```

---

### Error: "CUDA out of memory"

**Cause**: Batch size too large for GPU

**Solution**:
```python
# Reduce batch size
docs = nlp.pipe(texts, batch_size=16)  # Reduced from 50

# Or process in smaller chunks
for i in range(0, len(texts), 1000):
    batch = texts[i:i+1000]
    docs = list(nlp.pipe(batch))
```

---

## Validation Checklist

Use this checklist after each phase to ensure quality:

### Phase 1 (Data Preparation)

- [ ] Dictionary coverage >70%
- [ ] Patterns file >3,000 patterns
- [ ] No duplicate patterns
- [ ] Token patterns for short names, phrase patterns for full names
- [ ] Manual spot-check: 10 random resources have correct patterns

### Phase 2 (EntityRuler Baseline)

- [ ] Precision >95% (manual review of 50 samples)
- [ ] Coverage 70-80%
- [ ] All entities have canonical IDs
- [ ] Alias resolution works (test with known aliases)

### Phase 3 (Distant Supervision)

- [ ] 2-4 entities per document average
- [ ] B-COM:B-FUL ratio ~60:40
- [ ] Label distribution not skewed (no label >90%)
- [ ] Inspect 10 random docs: annotations look correct

### Phase 4 (Statistical Training)

- [ ] Test F1 >70%
- [ ] Can extract NEW entities (test with manual examples)
- [ ] No overfitting (train/test gap <15%)
- [ ] Error analysis: false positives are reasonable mistakes

### Phase 5 (Hybrid Integration)

- [ ] Pipeline order: ['entity_ruler', 'ner']
- [ ] Coverage 80-85%
- [ ] 25-30% of entities from Statistical NER
- [ ] Speed >40 papers/sec
- [ ] Known entities keep canonical IDs

---

## Emergency Rollback Plan

If hybrid pipeline performs worse than baseline:

1. **Keep EntityRuler Only**: Ship phase 2 baseline (>95% precision, 70-80% coverage)
2. **Fix Statistical Model**: Debug training issues offline
3. **Incremental Deployment**: Run hybrid on subset, compare to baseline
4. **Manual Validation**: Review 100 papers before full deployment

**Decision Criteria**: If hybrid precision <90% OR coverage <75%, rollback to EntityRuler-only.
