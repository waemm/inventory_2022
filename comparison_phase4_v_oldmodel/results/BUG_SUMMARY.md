# Critical Bugs in Phase 4 vs V2 Comparison

## The Problem

Phase 4 shows F1 of 0.72% vs V2's 61.55% - a 99% performance drop.

**This is NOT real** - it's caused by data corruption bugs.

## Bug #1: Double Nested JSON Serialization

### What Happens
```python
# test_ner.csv stores entities as:
"['sc-PDB']"  # String representation of Python list

# Script 01 parses it to:
['sc-PDB']  # Python list

# Saves to CSV (pandas stringifies):
"['sc-PDB']"  # Back to string

# Script 02 reads and parses AGAIN:
["['sc-PDB']"]  # List containing the string "['sc-PDB']" ← BUG!
```

### Impact
- Ground truth becomes: `["['sc-PDB']"]` instead of `['sc-PDB']`
- Entities are now **strings that look like lists** instead of actual entity names
- Matching fails completely

## Bug #2: Incorrect Comma Splitting

### What Happens
```python
# V2 stores: "DB, sc, sc-PDB" (comma-separated)
# After CSV round-trip: "['DB', 'sc', 'sc-PDB']"
# JSON parse fails (single quotes not valid JSON)
# Falls back to comma parsing:
["['DB'", " 'sc'", " 'sc-PDB']"]  # ← BUG! Split on wrong commas
```

### Impact
- V2 predictions: `["['DB'", "'sc'", "'sc-PDB']"]` instead of `['DB', 'sc', 'sc-PDB']`
- Phase 4 has similar corruption

## Bug #3: NaN Handling

### What Happens
```python
# parse_entity_list() converts float('nan') to:
['nan']  # List containing string "nan"

# Should return:
[]  # Empty list
```

### Impact
- 13,844 papers with NO ground truth are included in evaluation
- Only 63 papers have real ground truth, but evaluation uses 13,907
- Phase 4 "succeeds" on papers where both ground truth and predictions are `['nan']`

## The Evidence

From test_split_examples.txt:
```
Ground Truth (1 entities):
  - nan                    ← literal string "nan"

V2 Predictions (1 entities):
  ✗ ['AID-Net']           ← malformed string

Phase 4 Cleaned Predictions (1 entities):
  ✓ nan                   ← matches corrupted ground truth!
```

## The Fix

### 1. Fix parse_entity_list() in utils/data_loading.py

```python
def parse_entity_list(entity_str):
    # Handle None, empty, NaN
    if entity_str is None or entity_str == "" or entity_str == "[]":
        return []
    if pd.isna(entity_str):  # ← ADD THIS
        return []
    if str(entity_str).lower() == 'nan':  # ← ADD THIS
        return []

    # ... rest of function
```

### 2. Fix CSV Serialization in Script 01

```python
import json

# Before saving to CSV:
for col in ['true_com', 'true_ful', 'v2_com', 'v2_ful', ...]:
    aligned[col] = aligned[col].apply(
        lambda x: json.dumps(x) if isinstance(x, list) else x
    )
```

### 3. Fix CSV Deserialization in Script 02

```python
import json

# After reading from CSV:
for col in entity_columns:
    df[col] = df[col].apply(
        lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else []
    )
```

## Expected Results After Fix

- **Test split**: ~63 papers (not 13,907)
- **V2 F1**: ~60-70% (similar to baseline)
- **Phase 4 F1**: Should be comparable to or better than V2
- **No more `"nan"` or `"['...']"` patterns in entities**

## Verification Commands

```bash
# Check aligned_papers.csv for corruption
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/aligned_papers.csv')
sample = df[df['paper_id'] == '21398668'].iloc[0]
print(f"true_com: {sample['true_com']}")
# Should be: ["sc-PDB"] (JSON array)
# Not: ["['sc-PDB']"] (nested string)
EOF

# Count real ground truth papers
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/aligned_papers.csv')
has_gt = ~df['true_com'].isna() | ~df['true_ful'].isna()
print(f"Papers with ground truth: {has_gt.sum()}")
# Should be: ~63
# Not: 13,907
EOF
```

## Priority

🔴 **CRITICAL** - Fix immediately before drawing any conclusions about Phase 4 performance.

The current evaluation results are **completely invalid** and do not reflect actual model quality.
