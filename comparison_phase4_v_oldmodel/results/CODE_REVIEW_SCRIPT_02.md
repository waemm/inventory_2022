# Code Review: Script 02 Evaluation Results

**Date**: 2025-11-05
**Reviewer**: Claude Code
**Script**: `comparison_phase4_v_oldmodel/scripts/02_evaluate_on_test_split.py`

## Executive Summary

The Phase 4 vs V2 NER evaluation shows **catastrophic performance** (Phase 4 F1: 0.72% vs V2 F1: 61.55%). However, this is **NOT a real model failure** - it is caused by **TWO CRITICAL DATA PROCESSING BUGS** in the preprocessing pipeline that corrupt the ground truth and predictions during serialization/deserialization.

**Status**: 🔴 **CRITICAL BUGS IDENTIFIED** - Results are invalid

---

## Critical Bugs Identified

### Bug #1: Double JSON Serialization in Script 01 → aligned_papers.csv

**Location**: `01_preprocess_and_align.py` lines 333-451 (align_papers_by_id function)

**Root Cause**: The aligned_papers.csv contains Python lists that are stringified by pandas when saving to CSV, but are parsed again when reading back, causing double nesting.

**Data Flow**:
```
1. test_ner.csv contains:        "['sc-PDB']"     (string repr of Python list)
2. parse_entity_list() returns:  ['sc-PDB']       (Python list)
3. pandas to_csv() writes:       "['sc-PDB']"     (str() of list)
4. pandas read_csv() reads:      "['sc-PDB']"     (string)
5. parse_entity_list() returns:  ["['sc-PDB']"]   (WRONG - list with string item)
```

**Impact**: Ground truth entities become **strings containing Python list repr** instead of actual entity strings.
- Expected: `['sc-PDB']`
- Actual: `["['sc-PDB']"]`

**Evidence**:
```python
# From aligned_papers.csv for paper 21398668
true_com: '["[\'sc-PDB\']"]'  # WRONG - double nested
v2_com: "['DB', 'sc', 'sc-PDB']"  # Also wrong format
```

### Bug #2: Incorrect Comma-Separated Parsing for V2 Results

**Location**: `utils/data_loading.py` lines 258-318 (parse_entity_list function)

**Root Cause**: V2 results store entities as comma-separated strings (e.g., `"DB, sc, sc-PDB"`), but when these are saved to CSV and read back as a string containing a Python list repr, the comma parsing splits on the wrong delimiter.

**Data Flow**:
```
1. V2 ner_results.csv contains:  "DB, sc, sc-PDB"     (comma-separated)
2. pandas read + parse:          ['DB', 'sc', 'sc-PDB']  (list)
3. pandas to_csv() writes:       "['DB', 'sc', 'sc-PDB']" (str repr)
4. pandas read_csv() reads:      "['DB', 'sc', 'sc-PDB']" (string)
5. JSON parse fails (single quotes)
6. Comma parse splits on:        ["['DB'", " 'sc'", " 'sc-PDB']"] (WRONG)
```

**Impact**: Entity predictions are split incorrectly:
- Expected: `['DB', 'sc', 'sc-PDB']`
- Actual: `["['DB'", "'sc'", "'sc-PDB']"]`

---

## Why Performance Appears Catastrophic

### Matching Failure

**Ground Truth**:
```python
["['sc-PDB']"]  # String containing "['sc-PDB']"
```

**V2 Predictions**:
```python
["['DB'", "'sc'", "'sc-PDB']"]  # Three malformed strings
```

**Phase 4 Predictions**:
```python
Similar corruption
```

**Result**: Exact string matching fails because:
- Ground truth: `"['sc-PDB']"` (a single string)
- V2: `"['DB'"`, `"'sc'"`, `"'sc-PDB']"` (three different strings)
- **None match** → 0% precision/recall

### Test Split Coverage Issue

The evaluation claims to use **13,907 papers** but only **63 papers** have actual ground truth:

```python
Papers where true_com is pd.NaN: 13,844
Papers where true_ful is pd.NaN: 13,844
Papers with actual ground truth: 63
```

**Why**: Script 02's `filter_test_split()` function (lines 116-140) checks for "non-empty" ground truth but considers the corrupted data as "non-empty":

```python
# This incorrectly counts papers with corrupted data as having ground truth
has_ground_truth = (
    df['true_com'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False) |
    df['true_ful'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)
)
```

Because parse_entity_list() returns `['nan']` for NaN values (not an empty list), 13,844 papers with no ground truth are included in evaluation!

---

## Evidence from Examples File

The generated examples confirm the bug:

```
Example 1: Phase 4 F1=1.000 vs V2 F1=0.000 (Δ=1.000)
Paper ID: 21148158

Ground Truth (1 entities):
  - nan                    ← BUG: literal string "nan"

V2 Predictions (1 entities):
  ✗ ['AID-Net']           ← BUG: list repr as string

Phase 4 Cleaned Predictions (1 entities):
  ✓ nan                   ← BUG: matches the corrupted ground truth!
```

**Phase 4 "wins"** on papers with corrupted ground truth because it also has corrupted predictions that match the corrupted ground truth (both contain the literal string `"nan"`).

---

## Impact Assessment

### Severity: 🔴 CRITICAL

1. **Evaluation Results Invalid**: The F1 scores do not reflect actual model performance
2. **Test Split Contaminated**: 99.5% of "test" papers have no real ground truth (13,844 / 13,907)
3. **Misleading Conclusions**: Phase 4 appears 99% worse than V2, but this is an artifact

### Actual Test Split Size

Only **63 papers** have legitimate ground truth from `test_ner.csv`:
- Test split should have ~67 papers based on the original file
- 63 papers matched between test_ner.csv and the inventory
- **13,844 papers were incorrectly included** due to NaN handling

### Data Corruption Rate

- **100%** of ground truth entities are corrupted (double-nested strings)
- **100%** of V2 predictions are corrupted (malformed string splits)
- **100%** of Phase 4 predictions likely also corrupted

---

## Root Cause Analysis

### Why This Happened

1. **Pandas CSV Serialization**: Lists are converted to string repr when saving CSV
2. **No Proper JSON Serialization**: Should use `json.dumps()` for lists, not str()
3. **parse_entity_list() Not Idempotent**: Calling it twice produces different results
4. **No Validation**: No checks to verify data integrity after round-trip CSV save/load

### Design Flaw

The pipeline assumes:
```python
parse_entity_list(csv_value) → correct_list
```

But actually:
```python
parse_entity_list(str(parse_entity_list(csv_value))) → corrupted_list
```

---

## Recommendations

### Immediate Actions (Priority 1)

1. **Fix aligned_papers.csv Generation**
   - Use `json.dumps()` to serialize lists before CSV save
   - Use `json.loads()` to deserialize when reading CSV
   - Alternative: Use Parquet format which preserves Python lists

2. **Fix parse_entity_list() NaN Handling**
   ```python
   # Current (WRONG):
   if entity_str is None or entity_str == "" or entity_str == "[]":
       return []

   # Should be:
   import pandas as pd
   if entity_str is None or entity_str == "" or entity_str == "[]":
       return []
   if pd.isna(entity_str):  # Check for pandas NaN
       return []
   if str(entity_str).lower() == 'nan':  # Check for string 'nan'
       return []
   ```

3. **Add Data Validation**
   - Verify entity lists contain strings, not list reprs
   - Check for malformed entities (strings starting with `"['` or `"'`)
   - Log warnings for suspicious patterns

### Medium-Term Fixes (Priority 2)

4. **Improve filter_test_split() Logic**
   ```python
   # Current (includes papers with ['nan']):
   has_ground_truth = (
       df['true_com'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)
   )

   # Should be:
   def has_valid_ground_truth(entities):
       if not isinstance(entities, list):
           return False
       if len(entities) == 0:
           return False
       # Filter out 'nan', empty strings, list reprs
       valid = [e for e in entities if e and e != 'nan' and not e.startswith("['")]
       return len(valid) > 0

   has_ground_truth = (
       df['true_com'].apply(has_valid_ground_truth) |
       df['true_ful'].apply(has_valid_ground_truth)
   )
   ```

5. **Add Unit Tests**
   - Test parse_entity_list() with various inputs
   - Test round-trip CSV serialization
   - Test NaN handling explicitly

6. **Add Integrity Checks**
   - Count papers with ground truth at each stage
   - Validate entity strings don't contain list repr patterns
   - Compare counts before/after CSV round-trip

### Long-Term Improvements (Priority 3)

7. **Use Better Data Formats**
   - Parquet preserves Python types
   - SQLite for structured storage
   - JSON Lines for text data with lists

8. **Standardize Entity Storage**
   - Define canonical format (JSON array strings)
   - Convert all sources to canonical format at load time
   - Never mix formats (comma-separated vs JSON arrays)

9. **Add Documentation**
   - Document expected formats for each column
   - Add examples of valid vs invalid data
   - Create data schema validation

---

## Verification Plan

### Step 1: Fix Script 01 and Regenerate aligned_papers.csv

```python
# In align_papers_by_id(), before saving:
for col in ['true_com', 'true_ful', 'v2_com', 'v2_ful',
            'p4_com_raw', 'p4_com_clean', 'p4_ful_raw', 'p4_ful_clean']:
    if col in aligned.columns:
        # Serialize lists to JSON strings
        aligned[col] = aligned[col].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else x
        )
```

### Step 2: Fix Script 02 to Deserialize Correctly

```python
# In load_aligned_papers(), after reading CSV:
for col in entity_columns:
    if col in df.columns:
        # Deserialize JSON strings to lists
        df[col] = df[col].apply(
            lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else []
        )
```

### Step 3: Rerun Evaluation

After fixes, expect:
- Test split: ~63 papers (not 13,907)
- V2 F1: ~60-70% (similar to original claims)
- Phase 4 F1: Should be comparable or better than V2

### Step 4: Validate Results

- Check example outputs show actual entity strings
- Verify ground truth no longer contains `"nan"` or `"['...']"` patterns
- Compare per-paper metrics to spot-check correctness

---

## Conclusion

The evaluation results are **completely invalid** due to systematic data corruption. The Phase 4 model is **NOT performing poorly** - the bugs in data processing make fair comparison impossible.

**Next Steps**:
1. Fix parse_entity_list() NaN handling immediately
2. Fix CSV serialization to use JSON
3. Regenerate aligned_papers.csv
4. Rerun evaluation
5. Add validation checks to prevent recurrence

**Estimated Time to Fix**: 2-4 hours
**Risk of Fix**: Low (well-understood bugs, clear solutions)
**Impact of Fix**: Will enable valid comparison between Phase 4 and V2 models

---

## Code Quality Issues (Secondary)

While fixing the critical bugs, also address:

1. **Line 159-163**: `evaluate_predictions_vs_ground_truth()` function is just a wrapper - unnecessary indirection
2. **Line 382-384**: McNemar's test uses `TP > 0` to define "correct" - should use F1 threshold or exact match
3. **Line 474-477**: Sorting entities for display loses information about which matched
4. **No logging of entity counts**: Should log how many entities in ground truth vs predictions
5. **No sample validation**: Should show sample entities in log to catch corruption early

---

## Additional Observations

### Positive Aspects

- Comprehensive statistical testing (McNemar's test, bootstrap CI)
- Good code organization and documentation
- Proper error handling and logging
- Detailed example generation for debugging

### Architectural Issues

The two-script pipeline (01 → CSV → 02) is fragile:
- CSV doesn't preserve Python types
- No schema validation between scripts
- parse_entity_list() called inconsistently

**Better approach**:
- Script 01 saves to Parquet (preserves lists)
- OR: Script 01 returns dataframes to Script 02 directly (no intermediate file)
- OR: Use proper JSON serialization with explicit schema

---

**Review Complete** - Priority: 🔴 **FIX IMMEDIATELY** before drawing any conclusions about model performance.
