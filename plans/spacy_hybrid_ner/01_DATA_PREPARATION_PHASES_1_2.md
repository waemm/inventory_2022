# Data Preparation & EntityRuler Baseline (Phases 1-2)

**Duration**: 5-7 days combined
**Prerequisites**: Project overview, bioresource CSV file
**Output**: EntityRuler pipeline with >95% precision

---

## PHASE 1: Data Preparation & Dictionary Enrichment (3-4 days)

### Objective

Build comprehensive bioresource dictionary with 70-80% alias coverage (up from 40%).

---

### 1.1 Extract Bioresource Dictionary from CSV

**Script**: `scripts/01_extract_bioresource_dictionary.py`

**Input**:
- `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`

**Processing**:
```python
import pandas as pd
import json

df = pd.read_csv('/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv')

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

**Expected Output**:
- `data/bioresource_dictionary_raw.json`
- Statistics: ~3,761 resources (1,840 complete, 1,921 missing full_name)

**Success Criteria**:
- [ ] JSON file created with all unique resources
- [ ] ~40% have both short + full names
- [ ] ~60% missing full names (to be enriched in 1.2)

---

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
from collections import Counter

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
        most_common = Counter(candidates).most_common(1)[0][0]
        dictionary[resource_id]['full_name'] = most_common.strip()
        dictionary[resource_id]['enriched'] = True
        enriched_count += 1

print(f"Enriched {enriched_count} resources with full names")

# Save enriched dictionary
with open('data/bioresource_dictionary_enriched.json', 'w') as f:
    json.dump(dictionary, f, indent=2)
```

**Interactive Review (Optional)**:
```python
# Show ambiguous cases for manual review
ambiguous = []
for resource_id, candidates in candidate_matches.items():
    if len(Counter(candidates).most_common()) > 1:  # Multiple candidates
        ambiguous.append({
            'resource_id': resource_id,
            'candidates': Counter(candidates).most_common(3)
        })

# Save for manual review
pd.DataFrame(ambiguous).to_csv('data/enrichment_review.csv', index=False)
```

**Target**: Add 700-900 full names → 70-80% total coverage

**Output**: `data/bioresource_dictionary_enriched.json`

**Success Criteria**:
- [ ] 70-80% of resources have full names
- [ ] Enrichment flag added for auto-enriched entries
- [ ] Ambiguous cases flagged for manual review

---

### 1.3 Generate spaCy EntityRuler Patterns

**Script**: `scripts/03_generate_patterns_jsonl.py`

**Pattern Generation Logic**:
```python
import json

# Load enriched dictionary
with open('data/bioresource_dictionary_enriched.json', 'r') as f:
    dictionary = json.load(f)

patterns = []

for resource_id, data in dictionary.items():
    short = data['short_name']
    full = data.get('full_name')

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

**Success Criteria**:
- [ ] JSONL file with 3,000-5,000 patterns
- [ ] Each resource with both names has 2+ patterns
- [ ] Token patterns used for short names (handles punctuation)
- [ ] Phrase patterns used for full names

---

### Phase 1 Deliverables

- [ ] `data/bioresource_dictionary_raw.json`
- [ ] `data/bioresource_dictionary_enriched.json`
- [ ] `data/patterns.jsonl`
- [ ] Statistics report (coverage, enrichment rate)

---

## PHASE 2: EntityRuler Baseline (Local Testing) (2-3 days)

### Objective

Validate EntityRuler achieves >95% precision on known entities before investing in statistical training.

---

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

**Success Criteria**:
- [ ] spaCy 3.7.0 installed
- [ ] Can import spacy without errors

---

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

[... more entities ...]

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

---

### 2.3 Validate on Bioresource Papers

**Script**: `scripts/05_validate_entityruler.py`

**Sampling Strategy**:
```python
import pandas as pd
import random

# Load bioresource papers
df = pd.read_csv('/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv')

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

# Save results
import json
with open('results/phase2_entityruler_validation.json', 'w') as f:
    json.dump({
        'total_papers': len(results),
        'papers_with_entities': papers_with_entities,
        'coverage': coverage,
        'avg_entities_per_paper': sum(r['entities_found'] for r in results) / len(results)
    }, f, indent=2)
```

**Manual Precision Evaluation**:
```python
# Sample 50 extractions for manual review
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

**Success Criteria**:
- [ ] Coverage: 70-80%
- [ ] Precision: >95% (from manual review)
- [ ] All extracted entities have canonical IDs

---

### Phase 2 Deliverables

- [ ] `scripts/04_test_entityruler_pipeline.py`
- [ ] `scripts/05_validate_entityruler.py`
- [ ] `results/phase2_entityruler_validation.json`
- [ ] Precision >95% confirmed via manual review
- [ ] Coverage 70-80% confirmed

---

## Key Decisions & Trade-offs

### Why Token Patterns for Short Names?

**Decision**: Use `[{"TEXT": "PDB"}]` instead of `"PDB"`

**Rationale**:
- Token patterns match the token itself, ignoring surrounding punctuation
- `"PDB"` (phrase) would fail to match "PDB." or "(PDB)"
- Token patterns are more robust for acronyms

**Example**:
```python
# Phrase pattern (fails on punctuation)
{"pattern": "PDB"}  # Matches: "... PDB database"
                    # Fails: "... PDB.", "(PDB)", "PDB,"

# Token pattern (handles punctuation)
{"pattern": [{"TEXT": "PDB"}]}  # Matches all of the above!
```

### Why Phrase Patterns for Full Names?

**Decision**: Use `"Protein Domain Database"` instead of token patterns

**Rationale**:
- Phrase patterns are faster for multi-word strings
- Full names are usually complete phrases without punctuation variations
- Simpler pattern format

### Why Not Use PhraseMatcher?

**Decision**: Use EntityRuler instead of PhraseMatcher

**Rationale**:
- EntityRuler supports both phrase AND token patterns
- EntityRuler has `id` attribute for alias resolution (PhraseMatcher doesn't)
- EntityRuler integrates with NER pipeline (spaCy best practice)
- Performance difference negligible at 5,000 patterns

---

## Troubleshooting

### Issue: EntityRuler loads slowly (>10 seconds)

**Cause**: Large pattern file (>10,000 patterns)

**Solution**:
1. Profile loading time: `time python scripts/04_test_entityruler_pipeline.py`
2. If >10 sec, consider PhraseMatcher for phrase-only patterns
3. Split patterns into smaller files if needed

### Issue: Patterns not matching expected entities

**Cause**: Tokenization mismatch

**Debug**:
```python
# Check how spaCy tokenizes your text
nlp = spacy.blank("en")
doc = nlp("The PDB-101 database")
print([token.text for token in doc])
# Output: ['The', 'PDB', '-', '101', 'database']

# Pattern {"TEXT": "PDB-101"} will FAIL (expects single token)
# Pattern [{"TEXT": "PDB"}, {"TEXT": "-"}, {"TEXT": "101"}] will SUCCEED
```

### Issue: Low coverage (<70%)

**Cause**: Dictionary has too many missing full names

**Solution**:
1. Re-run Phase 1.2 with more patterns
2. Manually add high-frequency resources
3. Accept lower coverage for baseline (improve in Phase 3)

---

## Next Steps

After Phase 2 completion, proceed to **Phase 3: Distant Supervision Training Data** (see `02_TRAINING_PHASES_3_4.md`)
