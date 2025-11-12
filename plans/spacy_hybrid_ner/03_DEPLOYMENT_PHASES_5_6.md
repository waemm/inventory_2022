# Hybrid Pipeline Integration & Production Deployment (Phases 5-6)

**Duration**: 4-6 days combined
**Prerequisites**: Phases 1-4 complete, Statistical NER trained
**Output**: Production-ready hybrid pipeline with benchmarks

---

## PHASE 5: Hybrid Pipeline Integration (2-3 days)

### Objective

Combine EntityRuler + Statistical NER into production-ready hybrid pipeline.

**Critical**: EntityRuler MUST run first so statistical model respects its high-precision matches.

---

### 5.1 Build Hybrid Pipeline

**Script**: `scripts/09_build_hybrid_pipeline.py`

```python
import spacy
from spacy.language import Language
import os

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
nlp_statistical = spacy.load("models/ner_statistical")
nlp.add_pipe("ner", source=nlp_statistical)
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
os.makedirs('models', exist_ok=True)
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

**Success Criteria**:
- [x] Pipeline order: ['entity_ruler', 'ner']
- [x] Both known AND new entities detected
- [x] Known entities have canonical IDs
- [x] New entities have no ID (source=Statistical)

---

### 5.2 Validation on Test Set

**Script**: `scripts/10_validate_hybrid_pipeline.py`

```python
import spacy
import pandas as pd
from collections import defaultdict
import json
import os

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
results['ruler_percentage'] = results['ruler_entities'] / results['total_entities'] if results['total_entities'] > 0 else 0
results['statistical_percentage'] = results['statistical_entities'] / results['total_entities'] if results['total_entities'] > 0 else 0

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

# Create results directory
os.makedirs('results', exist_ok=True)

# Save results
with open('results/phase5_hybrid_validation.json', 'w') as f:
    # Remove non-serializable fields
    results_to_save = {k: v for k, v in results.items() if k != 'entities_per_paper'}
    json.dump(results_to_save, f, indent=2)

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

---

### 5.3 Performance Benchmarking

**Script**: `scripts/11_benchmark_hybrid_speed.py`

```python
import spacy
import pandas as pd
import time
import os

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
        'time_sec': round(elapsed, 2),
        'papers_per_sec': round(papers_per_sec, 2)
    }

print("Benchmarking speed on 100 papers...")
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
os.makedirs('results', exist_ok=True)
df.to_csv('results/phase5_speed_benchmark.csv', index=False)
print(f"\n✓ Results saved to: results/phase5_speed_benchmark.csv")
```

**Expected Speed**:
- EntityRuler Only: 150-200 papers/sec (very fast!)
- Statistical NER Only: 30-50 papers/sec (slower)
- Hybrid: 40-60 papers/sec (statistical component is bottleneck)

---

### 5.4 Alias Resolution Analysis

**Script**: `scripts/12_analyze_alias_resolution.py`

```python
import spacy
import pandas as pd
from collections import defaultdict
import os

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

print("\n✓ Alias resolution analysis complete!")
```

**Success Criteria**:
- [x] 70-80% of entities have canonical IDs
- [x] Multiple alias forms correctly linked (e.g., "BAR", "Bio-Analytic Resource")
- [x] Statistical entities (NEW) correctly have no ID

---

### Phase 5 Deliverables

- [ ] `models/ner_hybrid_v1/` (packaged pipeline)
- [ ] `results/phase5_hybrid_validation.json`
- [ ] `results/phase5_hybrid_extractions.csv`
- [ ] `results/phase5_speed_benchmark.csv`
- [ ] Validation metrics: 80-85% coverage, 3-5 entities/paper
- [ ] Speed >40 papers/sec verified

---

## PHASE 6: Production Deployment (2-3 days)

### Objective

Package hybrid pipeline for production use and integrate with existing infrastructure.

---

### 6.1 Package Pipeline

```bash
# Create metadata file
cat > metadata.json << 'EOF'
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
EOF

# Package pipeline
python -m spacy package \
  models/ner_hybrid_v1 \
  packages \
  --name ner_hybrid \
  --version 1.0.0 \
  --meta-path metadata.json
```

**Build & Install**:
```bash
cd packages/en_ner_hybrid_bioresource-1.0.0
pip install -e .

# Test installation
python -c "import spacy; nlp = spacy.load('en_ner_hybrid_bioresource'); print('✓ Package installed')"
```

---

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

---

### 6.3 Benchmark vs Existing Models

**Script**: `scripts/13_benchmark_all_models.py`

```python
"""
Compare spaCy Hybrid vs V2 BERT vs Phase 4 Multi-Task
"""

import pandas as pd
import time
import json
import os
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
    'time_sec': round(spacy_time, 2),
    'papers_per_sec': round(len(test_df) / spacy_time, 2),
    'total_entities': sum(r['entity_count'] for r in spacy_results),
    'avg_entities_per_paper': round(sum(r['entity_count'] for r in spacy_results) / len(spacy_results), 2),
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
os.makedirs('results', exist_ok=True)
comparison.to_csv('results/phase6_model_comparison.csv', index=False)
print(f"\n✓ Results saved to: results/phase6_model_comparison.csv")
```

---

### Phase 6 Deliverables

- [ ] `packages/en_ner_hybrid_bioresource-1.0.0/` (packaged model)
- [ ] `src/ner_predict_spacy.py` (integration module)
- [ ] `results/phase6_model_comparison.csv`
- [ ] Production deployment documentation

---

## Key Concepts

### Pipeline Component Order

**CRITICAL**: Order matters!

```python
# CORRECT ✓
nlp.pipe_names = ["entity_ruler", "ner"]
# EntityRuler finds known entities first with 100% precision
# Statistical NER fills in gaps (finds NEW entities)

# INCORRECT ✗
nlp.pipe_names = ["ner", "entity_ruler"]
# Statistical NER tries to find all entities (including known ones)
# EntityRuler blocked from correcting misclassifications
# Wastes computation, loses precision on known entities
```

### Alias Resolution in Practice

```python
# Example: Paper mentions both forms
text = "The Bio-Analytic Resource (BAR) is a database. BAR contains..."

doc = nlp(text)
for ent in doc.ents:
    print(f"{ent.text} → {ent.ent_id_}")

# Output:
# Bio-Analytic Resource → BAR
# BAR → BAR
# BAR → BAR

# All three mentions link to canonical ID "BAR"!
```

---

## Troubleshooting

### Issue: Statistical entities overwrite EntityRuler entities

**Symptom**: Known entities lose their canonical IDs

**Cause**: Pipeline order is wrong

**Fix**:
```python
# Check pipeline order
print(nlp.pipe_names)  # Should be: ['entity_ruler', 'ner']

# If wrong, rebuild pipeline in correct order
```

### Issue: Hybrid pipeline slower than expected

**Cause**: Not using batch processing

**Fix**:
```python
# Instead of:
for text in texts:
    doc = nlp(text)  # Slow!

# Use:
docs = list(nlp.pipe(texts))  # 10-20x faster!
```

### Issue: Can't load packaged model

**Symptom**: `ModuleNotFoundError` when loading package

**Cause**: Package not installed

**Fix**:
```bash
cd packages/en_ner_hybrid_bioresource-1.0.0
pip install -e .
```

---

## Next Steps

After Phase 6 completion:
1. Review success criteria (see `00_PROJECT_OVERVIEW.md`)
2. Run full-scale inference on production data (10-40k papers)
3. Compare performance vs V2 BERT model
4. Deploy to production environment
5. Set up continuous dictionary enrichment process
