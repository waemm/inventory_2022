# Quick Start Guide - Fixed Pipeline

**Date**: 2025-11-05
**Status**: ✅ Bug fixes applied and verified

## Critical Bug Fixes Applied

Three critical data corruption bugs have been fixed:

1. **NaN Handling**: NaN values no longer become `['nan']`
2. **JSON Serialization**: Entity lists properly saved/loaded as JSON
3. **Python List Repr**: Single-quoted lists like `['sc-PDB']` correctly parsed

See [BUG_FIXES_SUMMARY.md](./BUG_FIXES_SUMMARY.md) for complete details.

---

## Running the Fixed Pipeline

### Step 1: Run Script 01 (Preprocess and Align)

```bash
cd /Users/warren/development/GBC/inventory_2022/comparison_phase4_v_oldmodel/scripts

# Run with verbose logging
python 01_preprocess_and_align.py --verbose
```

**Output Files**:
- `../data/aligned_papers.csv` - Main output (13,907 papers, 1.5 MB)
- `../data/bpe_artifact_report.json` - BPE contamination analysis
- `../data/entity_counts.csv` - Entity distribution statistics

**Expected Results**:
- Total papers aligned: 13,907
- Papers with ground truth: 63
- Papers with V2 results: 4,395
- Papers with Phase 4 results: 13,754

---

### Step 2: Load Data Correctly

**IMPORTANT**: Always use `load_aligned_papers()` to load the aligned data.

```python
from utils import load_aligned_papers

# Load aligned papers with proper deserialization
df = load_aligned_papers()

# Verify data integrity
print(f"Total papers: {len(df)}")
print(f"Columns: {df.columns.tolist()}")

# Check entity columns are lists
sample = df[df['true_com'].apply(lambda x: len(x) > 0)].iloc[0]
print(f"\nSample entities:")
print(f"Ground truth: {sample['true_com']}")  # ['sc-PDB']
print(f"V2 predicted: {sample['v2_com']}")     # ['DB', 'sc', 'sc-PDB']
print(f"Phase 4 predicted: {sample['p4_com_raw']}")  # ['PDB', 'sc']
```

**DO NOT** load the CSV directly:
```python
# ❌ WRONG - entity columns will be strings, not lists!
df = pd.read_csv('aligned_papers.csv')

# ✅ CORRECT - entity columns properly deserialized as lists
df = load_aligned_papers()
```

---

### Step 3: Run Script 02 (Entity-Level Comparison)

```bash
python 02_entity_level_comparison.py
```

This script now receives properly formatted data with no corruption.

---

## Verification Commands

### Test Bug Fixes

```bash
# Run comprehensive test suite
python test_bug_fixes.py
```

**Expected output**: ✅ ALL TESTS PASSED

### Inspect Aligned Data

```bash
# Check file exists and size
ls -lh ../data/aligned_papers.csv

# Inspect first few rows
head -5 ../data/aligned_papers.csv

# Count papers
wc -l ../data/aligned_papers.csv
```

### Verify Entity Format

```python
import pandas as pd
import json
from pathlib import Path

# Load CSV directly to inspect raw format
df = pd.read_csv('../data/aligned_papers.csv')

# Check a sample entity column
sample_entity = df['true_com'].dropna().iloc[0]
print(f"Raw value: {sample_entity}")
print(f"Type: {type(sample_entity)}")

# Parse it
parsed = json.loads(sample_entity)
print(f"Parsed: {parsed}")
print(f"Parsed type: {type(parsed)}")

# Should output:
# Raw value: ["sc-PDB"]
# Type: <class 'str'>
# Parsed: ['sc-PDB']
# Parsed type: <class 'list'>
```

---

## Common Issues (Now Fixed)

### Issue 1: NaN becoming ['nan']
**Status**: ✅ FIXED
- NaN values now properly return `[]`
- No 'nan' string contamination

### Issue 2: Entity lists as strings
**Status**: ✅ FIXED
- Entities properly serialized as JSON: `["sc-PDB"]`
- Use `load_aligned_papers()` for proper deserialization

### Issue 3: Single-quoted lists not parsed
**Status**: ✅ FIXED
- `['sc-PDB']` correctly parsed with ast.literal_eval
- Hyphenated entities preserved intact

---

## Entity Columns Reference

All entity columns in `aligned_papers.csv`:

| Column | Description | Source | Type |
|--------|-------------|--------|------|
| `true_com` | Ground truth common names | Test split | List[str] |
| `true_ful` | Ground truth full names | Test split | List[str] |
| `v2_com` | V2 predicted common names | Old model | List[str] |
| `v2_ful` | V2 predicted full names | Old model | List[str] |
| `p4_com_raw` | Phase 4 raw common names | New model | List[str] |
| `p4_com_clean` | Phase 4 cleaned common names | New model (BPE cleaned) | List[str] |
| `p4_ful_raw` | Phase 4 raw full names | New model | List[str] |
| `p4_ful_clean` | Phase 4 cleaned full names | New model (BPE cleaned) | List[str] |

**Format in CSV**: JSON strings like `["sc-PDB"]`
**Format after load_aligned_papers()**: Python lists like `['sc-PDB']`

---

## Directory Structure

```
comparison_phase4_v_oldmodel/
├── scripts/
│   ├── 01_preprocess_and_align.py          ✅ Fixed
│   ├── 02_entity_level_comparison.py       Ready to use
│   ├── test_bug_fixes.py                   ✅ All tests pass
│   ├── BUG_FIXES_SUMMARY.md               📄 Complete documentation
│   ├── QUICK_START_FIXED.md               📄 This file
│   └── utils/
│       ├── data_loading.py                 ✅ Fixed (parse_entity_list, load_aligned_papers)
│       ├── __init__.py                     ✅ Updated exports
│       ├── entity_matching.py              Ready to use
│       ├── metrics.py                      Ready to use
│       └── bpe_cleaning.py                 Ready to use
├── data/
│   ├── aligned_papers.csv                  ✅ Regenerated with fixes
│   ├── bpe_artifact_report.json            ✅ Generated
│   └── entity_counts.csv                   ✅ Generated
└── logs/
    └── 01_rerun_with_fixes.log             ✅ Successful run log
```

---

## Example Usage

### Load and Explore Data

```python
from utils import load_aligned_papers

# Load data
df = load_aligned_papers()

# Papers with all three sources
complete = df[
    df['true_com'].apply(lambda x: len(x) > 0) &
    df['v2_com'].apply(lambda x: len(x) > 0) &
    df['p4_com_raw'].apply(lambda x: len(x) > 0)
]
print(f"Papers with all three sources: {len(complete)}")

# Compare V2 vs Phase 4
for idx, row in complete.head(5).iterrows():
    print(f"\nPaper {row['paper_id']}:")
    print(f"  Ground truth: {row['true_com']}")
    print(f"  V2 predicted: {row['v2_com']}")
    print(f"  Phase 4 predicted: {row['p4_com_raw']}")
```

### Count Entities by System

```python
from utils import load_aligned_papers

df = load_aligned_papers()

# Count entities per system
for col in ['true_com', 'v2_com', 'p4_com_raw']:
    total = df[col].apply(len).sum()
    papers_with = df[col].apply(lambda x: len(x) > 0).sum()
    mean = df[col].apply(len).mean()
    print(f"{col:15s}: {total:5d} entities across {papers_with:5d} papers (mean: {mean:.2f})")
```

---

## Help and Support

### Documentation

- [BUG_FIXES_SUMMARY.md](./BUG_FIXES_SUMMARY.md) - Complete bug fix documentation
- [test_bug_fixes.py](./test_bug_fixes.py) - Test suite and examples
- [01_preprocess_and_align.py](./01_preprocess_and_align.py) - Full script documentation

### Logs

- `01_preprocess_and_align.log` - Latest run log
- `01_rerun_with_fixes.log` - Bug fix verification run

### Validation

Run the test suite anytime:
```bash
python test_bug_fixes.py
```

Expected: ✅ ALL TESTS PASSED

---

## Status Summary

| Component | Status | Details |
|-----------|--------|---------|
| Bug #1: NaN Handling | ✅ Fixed | NaN → [] (not ['nan']) |
| Bug #2: JSON Serialization | ✅ Fixed | Lists properly saved/loaded |
| Bug #3: Python List Repr | ✅ Fixed | ['sc-PDB'] parsed correctly |
| Unit Tests | ✅ Passing | All 4 test suites pass |
| Script 01 | ✅ Working | Successfully regenerated data |
| Data Integrity | ✅ Verified | Sample entities confirmed |
| Documentation | ✅ Complete | Full details in BUG_FIXES_SUMMARY.md |

**Overall Status**: ✅ PRODUCTION READY

---

## Next Steps

1. ✅ **COMPLETE**: Bug fixes applied and verified
2. ✅ **COMPLETE**: Data regenerated with fixes
3. ⏭️ **READY**: Run Script 02 for entity-level comparison
4. 🔍 **RECOMMENDED**: Review comparison results

---

**Last Updated**: 2025-11-05
**Pipeline Version**: 1.0.0 (with critical bug fixes)
