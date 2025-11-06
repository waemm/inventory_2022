# Critical Data Corruption Bug Fixes - Summary

**Date**: 2025-11-05
**Author**: Claude Code
**Status**: ✅ COMPLETED AND VERIFIED

## Overview

Fixed three critical data corruption bugs in the NER comparison pipeline that were causing entities to be malformed during CSV serialization/deserialization.

## Bugs Fixed

### Bug #1: NaN Handling in parse_entity_list()

**Location**: `utils/data_loading.py` (line 258)

**Problem**:
- `float('nan')` was being converted to string `'nan'`, then to list `['nan']`
- This caused empty entity lists to become `['nan']` instead of `[]`
- Contaminated data with false positive entities

**Fix Applied**:
```python
# Check isinstance(list) FIRST before pd.isna() to avoid ValueError
if isinstance(entity_str, list):
    return [str(e).strip() for e in entity_str if e and str(e).strip() and str(e).strip().lower() != 'nan']

# Then check for NaN/None
if pd.isna(entity_str):
    return []

if entity_str is None or str(entity_str).strip().lower() in ['nan', 'none', '']:
    return []
```

**Result**:
- ✅ All NaN values properly return `[]`
- ✅ No 'nan' string contamination

---

### Bug #2: Double JSON Serialization in CSV

**Location**: `01_preprocess_and_align.py` (save_outputs function)

**Problem**:
- Entity lists were being saved to CSV without JSON serialization
- Pandas converted Python lists to string representations: `['sc-PDB']` → `"['sc-PDB']"`
- On reload, these became strings instead of being parsed back to lists
- Caused data type corruption and parsing failures

**Fix Applied**:
```python
# BUG FIX #2: Serialize entity lists to JSON before saving
aligned_df_to_save = aligned_df.copy()

entity_columns = [
    'true_com', 'true_ful',
    'v2_com', 'v2_ful',
    'p4_com_raw', 'p4_com_clean',
    'p4_ful_raw', 'p4_ful_clean'
]

for col in entity_columns:
    if col in aligned_df_to_save.columns:
        aligned_df_to_save[col] = aligned_df_to_save[col].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else x
        )

# Save to CSV
aligned_df_to_save.to_csv(aligned_path, index=False, encoding='utf-8')
```

**Companion Function**: Added `load_aligned_papers()` to properly deserialize:
```python
def load_aligned_papers(file_path: Optional[Path] = None) -> pd.DataFrame:
    """Load aligned papers CSV with proper JSON deserialization."""
    df = pd.read_csv(file_path, encoding='utf-8')

    entity_columns = [...]

    for col in entity_columns:
        if col in df.columns:
            df[col] = df[col].apply(parse_entity_list)

    return df
```

**Result**:
- ✅ Entity lists properly serialized as JSON: `["sc-PDB"]`
- ✅ Complete roundtrip preservation: list → JSON string → list
- ✅ No data corruption through save/load cycle

---

### Bug #3: Python List Repr Parsing with ast.literal_eval

**Location**: `utils/data_loading.py` (parse_entity_list function)

**Problem**:
- Python list representations with single quotes failed JSON parsing: `"['sc-PDB']"`
- Fell back to comma parsing which corrupted the data
- Hyphenated entities like 'sc-PDB' were split incorrectly

**Fix Applied**:
```python
# Try parsing as JSON first
if entity_str.startswith('[') and entity_str.endswith(']'):
    try:
        entities = json.loads(entity_str)
        if isinstance(entities, list):
            return [str(e).strip() for e in entities if e and str(e).strip() and str(e).strip().lower() != 'nan']
    except json.JSONDecodeError:
        logger.debug(f"JSON parsing failed, trying Python literal eval: {entity_str[:100]}")

        # BUG FIX #3: Try ast.literal_eval for Python list repr like "['item']"
        try:
            import ast
            entities = ast.literal_eval(entity_str)
            if isinstance(entities, list):
                return [str(e).strip() for e in entities if e and str(e).strip() and str(e).strip().lower() != 'nan']
        except (ValueError, SyntaxError):
            logger.warning(f"Failed to parse as Python literal, trying comma-separated: {entity_str[:100]}")
```

**Result**:
- ✅ Python list repr `['sc-PDB']` correctly parsed to `['sc-PDB']`
- ✅ JSON strings `["sc-PDB"]` correctly parsed to `['sc-PDB']`
- ✅ Hyphenated entities preserved intact

---

## Verification

### Unit Tests

Created comprehensive test suite: `test_bug_fixes.py`

**Test Results**: ✅ ALL TESTS PASSED

```
TEST 1: NaN Handling - ✓ PASS
  - None input → []
  - float('nan') → []
  - pd.NA → []
  - String 'nan' → []
  - Empty string → []

TEST 2: Python List Repr Parsing - ✓ PASS
  - "['sc-PDB']" → ['sc-PDB']
  - "['protein A', 'gene B']" → ['protein A', 'gene B']
  - '["protein A", "gene B"]' → ['protein A', 'gene B']

TEST 3: JSON Serialization Roundtrip - ✓ PASS
  - ['sc-PDB'] → '["sc-PDB"]' → ['sc-PDB']
  - No data corruption detected

TEST 4: Edge Cases - ✓ PASS
  - Comma-separated strings
  - Extra whitespace handling
  - Empty string filtering
```

### Integration Test

Re-ran Script 01 with bug fixes:

```bash
python 01_preprocess_and_align.py --verbose
```

**Results**:
- ✅ Successfully processed 13,907 papers
- ✅ Entity columns properly serialized to JSON
- ✅ Sample entities verified: `["sc-PDB"]` format
- ✅ File size: 1.5 MB
- ✅ Load test successful: all entities properly deserialized as lists

**Sample Data Verification**:
```python
Paper ID: 21398668
true_com: ['sc-PDB'] (type: list)
v2_com: ['DB', 'sc', 'sc-PDB'] (type: list)
p4_com_raw: ['PDB', 'sc'] (type: list)
```

---

## Files Modified

1. **`utils/data_loading.py`**
   - Fixed `parse_entity_list()` function (3 bug fixes)
   - Added `load_aligned_papers()` function
   - Added validation and logging

2. **`utils/__init__.py`**
   - Exported new `load_aligned_papers()` function

3. **`01_preprocess_and_align.py`**
   - Fixed `save_outputs()` function to serialize entities to JSON
   - Added logging for serialized data samples

4. **`test_bug_fixes.py`** (new)
   - Comprehensive test suite for all bug fixes
   - Unit tests and integration tests

---

## Impact

### Before Fixes
- ❌ NaN values became `['nan']` instead of `[]`
- ❌ Entity lists corrupted during CSV save: `['sc-PDB']` → `"['sc-PDB']"` (string)
- ❌ Python list repr failed to parse: `"['sc-PDB']"` → parsing error or incorrect split
- ❌ Data corruption propagated through pipeline

### After Fixes
- ✅ NaN values properly handled as `[]`
- ✅ Entity lists preserved through save/load: `['sc-PDB']` → `["sc-PDB"]` → `['sc-PDB']`
- ✅ Python list repr correctly parsed: `"['sc-PDB']"` → `['sc-PDB']`
- ✅ No data corruption - entities maintain integrity

---

## Usage

### Loading Aligned Papers

**Before** (incorrect):
```python
df = pd.read_csv('aligned_papers.csv')
# Entity columns are strings, not lists!
```

**After** (correct):
```python
from utils import load_aligned_papers

df = load_aligned_papers()
# Entity columns are properly deserialized as lists
```

### Running Script 01

```bash
# Regenerate aligned_papers.csv with bug fixes
python 01_preprocess_and_align.py --verbose

# Output:
# - ../data/aligned_papers.csv (with proper JSON serialization)
# - ../data/bpe_artifact_report.json
# - ../data/entity_counts.csv
```

---

## Validation Checklist

- [x] All unit tests pass
- [x] Script 01 runs successfully
- [x] aligned_papers.csv generated with correct format
- [x] Sample entities verified as lists
- [x] JSON serialization format confirmed
- [x] Roundtrip preservation verified
- [x] NaN handling tested
- [x] Python list repr parsing tested
- [x] Edge cases tested

---

## Next Steps

1. ✅ **COMPLETE**: All bug fixes implemented and tested
2. ✅ **COMPLETE**: aligned_papers.csv regenerated with correct format
3. ⏭️ **READY**: Script 02 can now use the corrected data
4. 🔍 **RECOMMENDED**: Run Script 02 to verify downstream pipeline

---

## Technical Notes

### Why ast.literal_eval?

- Safe evaluation of Python literals (lists, tuples, dicts, etc.)
- Handles single-quoted strings: `['sc-PDB']`
- More robust than `eval()` (security)
- Fallback when JSON parsing fails

### Why JSON Serialization?

- Standard format for structured data in CSV
- Consistent double-quote format: `["item"]`
- Properly handled by pandas and json.loads()
- Prevents string representation corruption

### Order of Operations in parse_entity_list()

1. Check `isinstance(list)` first (avoid pd.isna() ValueError on lists)
2. Check `pd.isna()` for scalar NaN values
3. Check string representations of 'nan'/'none'
4. Try JSON parsing (most common format)
5. Try ast.literal_eval (Python list repr fallback)
6. Try comma-separated parsing (legacy format)

---

## Conclusion

All critical data corruption bugs have been fixed and verified. The entity parsing and serialization pipeline now correctly preserves data integrity through the entire save/load cycle. Entities like `['sc-PDB']` are properly maintained as lists throughout the pipeline, with no corruption from NaN contamination or improper CSV serialization.

**Status**: ✅ PRODUCTION READY
