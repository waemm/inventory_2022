# Quick Fix: Dictionary Lookup Bug

## Problem

The `load_dictionary_mapping()` function creates a global mapping that overwrites entries when multiple resources share the same full name. This causes 4 patterns to be misclassified.

## Solution

Replace the global mapping approach with direct resource ID lookups.

---

## Code Changes

### 1. Remove `load_dictionary_mapping()` function

**DELETE lines 26-42:**
```python
def load_dictionary_mapping(dict_path: Path) -> dict:
    """Load dictionary to map patterns to short/full names."""
    with open(dict_path) as f:
        data = json.load(f)

    mapping = {'short': {}, 'full': {}}

    for resource_id, info in data.items():
        short_name = info.get('short_name', '')
        full_name = info.get('full_name', '')

        if short_name:
            mapping['short'][short_name] = resource_id
        if full_name:
            mapping['full'][full_name] = resource_id

    return mapping
```

### 2. Update `classify_pattern()` signature and logic

**REPLACE lines 62-113 with:**

```python
def classify_pattern(pattern_text: str, pattern_obj: dict, dictionary: dict) -> tuple:
    """
    Classify a pattern as COM or FUL.

    Args:
        pattern_text: String representation of pattern
        pattern_obj: Full pattern object (contains 'id' and 'pattern' fields)
        dictionary: Full dictionary from bioresource_dictionary_enriched.json

    Returns:
        (label, confidence) where label is 'COM' or 'FUL' and confidence is 0-1
    """
    # 1. Dictionary lookup using the pattern's own resource ID (highest confidence)
    resource_id = pattern_obj.get('id', '')
    if resource_id in dictionary:
        resource_info = dictionary[resource_id]
        short_name = resource_info.get('short_name', '')
        full_name = resource_info.get('full_name', '')

        # Check if pattern matches this resource's names
        if pattern_text == short_name:
            return ('COM', 1.0)
        elif pattern_text == full_name:
            return ('FUL', 1.0)

    # 2. Token-based pattern (very high confidence for COM)
    if isinstance(pattern_obj.get('pattern'), list):
        return ('COM', 0.95)

    # 3. Orthographic features
    words = pattern_text.split()

    # All caps single word
    if len(words) == 1 and pattern_text.isupper() and len(pattern_text) <= 10:
        return ('COM', 0.90)

    # CamelCase or mixed case single word
    if len(words) == 1 and len(pattern_text) <= 20:
        if any(c.isupper() for c in pattern_text[1:]):  # Has internal caps
            return ('COM', 0.85)

    # Multiple words with title case
    if len(words) >= 3:
        return ('FUL', 0.85)

    # 4. Length heuristic
    if len(pattern_text) <= 10:
        return ('COM', 0.75)
    elif len(pattern_text) <= 15:
        return ('COM', 0.65)  # Less confident
    elif len(pattern_text) > 25:
        return ('FUL', 0.85)

    # 5. Default based on word count
    if len(words) == 1:
        return ('COM', 0.60)  # Low confidence
    else:
        return ('FUL', 0.70)
```

### 3. Update `relabel_patterns()` to pass full dictionary

**MODIFY lines 115-186:**

Change:
```python
def relabel_patterns(input_path: Path, dict_path: Path, output_path: Path):
    """Main relabeling function."""
    # ...

    # Load dictionary
    print(f"\nLoading dictionary from: {dict_path}")
    dict_mapping = load_dictionary_mapping(dict_path)
    print(f"  Short names: {len(dict_mapping['short']):,}")
    print(f"  Full names: {len(dict_mapping['full']):,}")
```

To:
```python
def relabel_patterns(input_path: Path, dict_path: Path, output_path: Path):
    """Main relabeling function."""
    # ...

    # Load dictionary
    print(f"\nLoading dictionary from: {dict_path}")
    with open(dict_path) as f:
        dictionary = json.load(f)
    print(f"  Resources in dictionary: {len(dictionary):,}")
```

And change the classification call from:
```python
label, confidence = classify_pattern(pattern_text, p, dict_mapping)
```

To:
```python
label, confidence = classify_pattern(pattern_text, p, dictionary)
```

### 4. Update main() function call

**MODIFY line 233:**

Change:
```python
stats, relabeled = relabel_patterns(PATTERNS_INPUT, DICTIONARY_PATH, PATTERNS_OUTPUT)
```

To:
```python
stats, relabeled = relabel_patterns(PATTERNS_INPUT, DICTIONARY_PATH, PATTERNS_OUTPUT)
```
(No change needed - signature is the same)

---

## Complete Fixed Function

Here's the complete updated `classify_pattern()` function:

```python
def classify_pattern(pattern_text: str, pattern_obj: dict, dictionary: dict) -> tuple:
    """
    Classify a pattern as COM or FUL.

    Args:
        pattern_text: String representation of pattern
        pattern_obj: Full pattern object (contains 'id' and 'pattern' fields)
        dictionary: Full dictionary from bioresource_dictionary_enriched.json

    Returns:
        (label, confidence) where label is 'COM' or 'FUL' and confidence is 0-1
    """
    # 1. Dictionary lookup using the pattern's own resource ID (highest confidence)
    resource_id = pattern_obj.get('id', '')
    if resource_id in dictionary:
        resource_info = dictionary[resource_id]
        short_name = resource_info.get('short_name', '')
        full_name = resource_info.get('full_name', '')

        # Check if pattern matches this resource's names
        if pattern_text == short_name:
            return ('COM', 1.0)
        elif pattern_text == full_name:
            return ('FUL', 1.0)

    # 2. Token-based pattern (very high confidence for COM)
    if isinstance(pattern_obj.get('pattern'), list):
        return ('COM', 0.95)

    # 3. Orthographic features
    words = pattern_text.split()

    # All caps single word
    if len(words) == 1 and pattern_text.isupper() and len(pattern_text) <= 10:
        return ('COM', 0.90)

    # CamelCase or mixed case single word
    if len(words) == 1 and len(pattern_text) <= 20:
        if any(c.isupper() for c in pattern_text[1:]):  # Has internal caps
            return ('COM', 0.85)

    # Multiple words with title case
    if len(words) >= 3:
        return ('FUL', 0.85)

    # 4. Length heuristic
    if len(pattern_text) <= 10:
        return ('COM', 0.75)
    elif len(pattern_text) <= 15:
        return ('COM', 0.65)  # Less confident
    elif len(pattern_text) > 25:
        return ('FUL', 0.85)

    # 5. Default based on word count
    if len(words) == 1:
        return ('COM', 0.60)  # Low confidence
    else:
        return ('FUL', 0.70)
```

---

## Testing the Fix

### 1. Backup original output
```bash
cd /Users/warren/development/GBC/inventory_2022
cp spacy_hybrid_ner/data/patterns_com_ful.jsonl spacy_hybrid_ner/data/patterns_com_ful.jsonl.backup
cp spacy_hybrid_ner/data/relabeling_stats.json spacy_hybrid_ner/data/relabeling_stats.json.backup
cp spacy_hybrid_ner/data/relabeling_report.txt spacy_hybrid_ner/data/relabeling_report.txt.backup
```

### 2. Run fixed script
```bash
python3 spacy_hybrid_ner/scripts/13_relabel_patterns_com_ful.py
```

### 3. Verify corrections
```bash
# Check the 4 patterns that should now be FUL
grep '"Integrated Microbial Genomes Atlas of Biosynthetic gene Clusters"' spacy_hybrid_ner/data/patterns_com_ful.jsonl
grep '"antimicrobial peptide database".*YADAMP' spacy_hybrid_ner/data/patterns_com_ful.jsonl
grep '"SEQanswers"' spacy_hybrid_ner/data/patterns_com_ful.jsonl
grep '"RNA Characterization of Secondary Structure Motifs".*RNA CoSSMos' spacy_hybrid_ner/data/patterns_com_ful.jsonl
```

**Expected output:** All 4 should show `"label": "FUL"`

### 4. Verify overall statistics
```bash
python3 << 'EOF'
import json

with open('spacy_hybrid_ner/data/relabeling_stats.json') as f:
    stats = json.load(f)

print(f"Total: {stats['total']}")
print(f"COM: {stats['COM']} ({stats['COM']/stats['total']*100:.1f}%)")
print(f"FUL: {stats['FUL']} ({stats['FUL']/stats['total']*100:.1f}%)")
print(f"Manual review: {len(stats['manual_review'])}")
EOF
```

**Expected output:**
- Total: 6,216
- COM: ~3,911 (63.0%) (was 3,915, should decrease by 4)
- FUL: ~2,305 (37.0%) (was 2,301, should increase by 4)
- Manual review: 6 (unchanged)

---

## Validation Script

Run this to confirm all 4 corrections:

```python
import json

# Load patterns
with open('spacy_hybrid_ner/data/patterns_com_ful.jsonl') as f:
    patterns = [json.loads(line) for line in f]

# Check the 4 specific patterns
test_cases = [
    ('IMG-ABC', 'Integrated Microbial Genomes Atlas of Biosynthetic gene Clusters', 'FUL'),
    ('YADAMP', 'antimicrobial peptide database', 'FUL'),
    ('SEQwiki', 'SEQanswers', 'FUL'),
    ('RNA CoSSMos', 'RNA Characterization of Secondary Structure Motifs', 'FUL')
]

print("Verification of 4 corrected patterns:")
print("=" * 80)
all_correct = True
for res_id, pattern_text, expected_label in test_cases:
    # Find pattern
    found = [p for p in patterns if p['id'] == res_id and p['pattern'] == pattern_text]
    if found:
        actual_label = found[0]['label']
        status = '✓' if actual_label == expected_label else '✗'
        print(f"{status} {res_id}: '{pattern_text[:50]}...' → {actual_label} (expected {expected_label})")
        if actual_label != expected_label:
            all_correct = False
    else:
        print(f"✗ {res_id}: Pattern not found!")
        all_correct = False

print("=" * 80)
if all_correct:
    print("✓ All 4 patterns corrected successfully!")
else:
    print("✗ Some patterns still incorrect - check implementation")
```

---

## Expected Results After Fix

- **Total patterns:** 6,216 (unchanged)
- **COM labels:** 3,911 (decreased by 4)
- **FUL labels:** 2,305 (increased by 4)
- **Manual review cases:** 6 (unchanged)
- **Classification accuracy:** 100% for dictionary-matched patterns

---

## Time Estimate

- Code changes: 30 minutes
- Testing: 15 minutes
- Validation: 15 minutes
- **Total: ~1 hour**

---

## Rollback (if needed)

If something goes wrong:

```bash
cp spacy_hybrid_ner/data/patterns_com_ful.jsonl.backup spacy_hybrid_ner/data/patterns_com_ful.jsonl
cp spacy_hybrid_ner/data/relabeling_stats.json.backup spacy_hybrid_ner/data/relabeling_stats.json
cp spacy_hybrid_ner/data/relabeling_report.txt.backup spacy_hybrid_ner/data/relabeling_report.txt
```
