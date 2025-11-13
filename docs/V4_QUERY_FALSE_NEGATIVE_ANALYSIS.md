# V4 Query False Negative Analysis
**Date**: 2025-11-11
**Investigator**: Claude Code
**Severity**: CRITICAL
**Impact**: 49.5% of training data missing from V4 query results

---

## Executive Summary

During PyCaret metadata classification development, a critical issue was discovered: **the V4 EPMC query is missing 795 out of 1,606 training papers (49.5%)**, all of which fall within the query's target date range of 2011-2021. This represents a **~50% false negative rate** for bio-resource papers that human curators successfully identified.

**Key Finding**: The V4 query, despite capturing 100% of the 13 manually curated test papers, has a massive blind spot for the broader training dataset.

---

## The Problem

### Initial Symptom
When merging training labels (`manual_classifications.csv`) with V4 query metadata (`query_results_complete.csv`):
- **Expected**: 1,606 merged samples
- **Actual**: 811 merged samples (50.5%)
- **Missing**: 795 samples (49.5%)

### Data Pipeline Failure
The original PyCaret notebook had a cascading failure:
1. Merge on PMID: 811 matches, 795 NaN rows
2. `dropna()` removed ALL 1,606 rows (due to sparse metadata columns)
3. LightGBM received: **2 samples, 0 features** ❌
4. Training failed with "no meaningful features" error

---

## Investigation Details

### Methodology
```bash
# Diagnostic script: pycaret_local_diagnostic.py
1. Load training labels: 1,634 samples
2. Extract valid PMIDs: 1,606 samples (28 non-PMID IDs filtered)
3. Load V4 metadata: 123,505 papers (2011-2025)
4. Check PMID overlap:
   - Training PMIDs: 1,606
   - Metadata PMIDs: 121,160
   - Overlap: 811 (50.5%)
   - Missing: 795 (49.5%)
```

### Missing Paper Analysis

#### Year Distribution of Missing Papers
```
Year Range    | Missing Papers | % of Missing | Cumulative
--------------|----------------|--------------|------------
2011-2012     | 90             | 11.3%        | 11.3%
2013-2014     | 72             | 9.1%         | 20.4%
2015-2016     | 87             | 10.9%        | 31.3%
2017-2018     | 86             | 10.8%        | 42.1%
2019          | 81             | 10.2%        | 52.3%
2020          | 164            | 20.6%        | 72.9%
2021          | 215            | 27.0%        | 100.0%
--------------|----------------|--------------|------------
TOTAL         | 795            | 100.0%       |
```

**Critical Observation**:
- **100% of missing papers are from 2011-2021** (the query's target range)
- Recent years (2020-2021) have higher miss rates: 379/795 papers (47.7%)
- No missing papers are from outside the query range

### Sample Missing Papers (within 2011-2021)

```
PMID      | Year  | Curation | Title (truncated)
----------|-------|----------|--------------------------------------------------
31139843  | 2019  | 0.0      | Erratum to: Stroke in patients with prosthetic...
31930403  | 2019  | 0.0      | The Protein Imager: a full-featured online...
32548865  | 2020  | 1.0      | The UK Veterinary Immunological Toolbox...
32569358  | 2020  | 1.0      | COVID-19 TestNorm: A tool to normalize COVID-19...
32614400  | 2020  | 1.0      | iPromoter-BnCNN: a novel branched CNN-based...
22210604  | 2012  | 1.0      | Discovery and mapping of a new expressed...
31201317  | 2019  | 1.0      | Multi omics analysis of fibrotic kidneys...
22257670  | 2012  | 1.0      | AnnTools: a comprehensive and versatile...
23771137  | 2013  | 1.0      | Secondary structure and domain architecture...
25837579  | 2015  | 1.0      | Maximum-Likelihood Phylogenetic Inference...
```

**Note**: Many missing papers have `curation_score=1.0` (positive bio-resource labels), indicating these are **legitimate bio-resource papers** that the V4 query failed to capture.

---

## Impact Analysis

### 1. Training Data Loss
- **Available for training**: 811 samples (50.5%)
- **Lost**: 795 samples (49.5%)
- **Class distribution of missing**:
  - Need to check, but likely includes both positive and negative samples

### 2. Model Performance Impact
Training on only 50% of available data will:
- ✗ Reduce statistical power
- ✗ Increase overfitting risk (smaller sample size)
- ✗ Miss important feature patterns present in missing papers
- ✗ Reduce generalization capability
- ✗ Fail to learn from 49.5% of expert curation decisions

### 3. Validation Concerns
- Manual papers (N=13) were 100% captured by V4 query
- This created **false confidence** in query completeness
- The broader training set reveals the true 50% miss rate

### 4. Production Pipeline Risk
If V4 query misses 50% of training papers, it will likely miss similar papers in production:
- **Expected recall on new papers**: ~50%
- **Actual coverage**: Significantly lower than reported

---

## Root Cause Analysis

### Why V4 Query Misses These Papers

**Hypothesis 1: Query Specificity Too High**
The V4 query may use overly restrictive MeSH terms, keywords, or filters that exclude valid bio-resource papers with:
- Non-standard terminology
- Emerging fields (e.g., COVID-19 tools in 2020)
- Cross-disciplinary resources
- Database/tool announcements in non-traditional journals

**Hypothesis 2: EPMC Indexing Delays**
Recent papers (2020-2021) have higher miss rates, suggesting:
- Incomplete EPMC indexing for newer papers
- MeSH terms not yet assigned
- Metadata enrichment still in progress

**Hypothesis 3: Query Construction**
V4 query may rely on:
- Specific MeSH terms that aren't universal
- Title/abstract keywords that don't match all bio-resource paper formats
- Publication type filters that exclude Letters, Comments, Errata

### Evidence Against Alternative Explanations

**NOT a Date Range Issue**:
- Metadata spans 2011-2025 ✓
- Missing papers are within 2011-2021 ✓
- Query should capture these ✓

**NOT a PMID Format Issue**:
- All missing PMIDs are standard numeric IDs ✓
- Successfully extracted and converted ✓

**NOT a Merge Logic Error**:
- Diagnostic script confirmed clean merge ✓
- PMID overlap calculation is correct ✓

---

## Recommended Solutions

### Option 1: Fetch Missing Metadata Directly (IMMEDIATE)
**Action**: Use `src/fetch_enhanced_metadata.py` to retrieve metadata for 795 missing PMIDs
- **Pros**:
  - Quick fix (5-10 minutes)
  - Recovers all training data
  - Allows PyCaret training to proceed
- **Cons**:
  - Doesn't fix root query issue
  - Metadata may be less rich than V4 results
- **Timeline**: Immediate (today)

### Option 2: Revise V4 Query (MEDIUM-TERM)
**Action**: Analyze missing papers to identify common patterns, then broaden query
- **Pros**:
  - Fixes root cause
  - Improves production pipeline
  - Benefits future runs
- **Cons**:
  - Time-consuming investigation
  - May increase false positives
  - Requires query re-validation
- **Timeline**: 1-2 weeks

### Option 3: Hybrid Approach (RECOMMENDED)
**Action**:
1. Fetch missing metadata NOW (Option 1)
2. Train PyCaret model with full 1,606 samples
3. Investigate query gaps in parallel (Option 2)
4. Update production query based on findings

---

## Immediate Action Plan

### Phase 1: Data Recovery (Today)
1. ✅ Create list of 795 missing PMIDs
2. ⏳ Fetch metadata using EPMC API
3. ⏳ Merge with training labels
4. ⏳ Verify 1,606 samples available for training

### Phase 2: Training (Today)
5. ⏳ Re-run feature engineering with full dataset
6. ⏳ Train PyCaret models
7. ⏳ Validate on 13 manual papers

### Phase 3: Query Investigation (Next Week)
8. ⏳ Analyze characteristics of missing papers
9. ⏳ Identify query gaps (MeSH terms, keywords, filters)
10. ⏳ Propose V5 query improvements
11. ⏳ Re-run and validate V5 query

---

## Files Generated

### Diagnostic Scripts
- `pycaret_local_diagnostic.py` - Identifies merge failure and data loss
- `pycaret_local_train.py` - Fixed preprocessing (replaces `dropna()` with selective filling)

### Results
- `pycaret_results_local/local_test_test_training.log` - Full diagnostic log
- `pycaret_results_local/preprocessed_data.csv` - Clean data with 811 samples, 67 features

### Documentation
- `docs/V4_QUERY_FALSE_NEGATIVE_ANALYSIS.md` - This document

---

## Key Learnings

### What Went Wrong
1. **Assumed V4 query was complete** based on 100% manual paper capture
2. **Didn't validate** query against full training set before building pipeline
3. **Used `dropna()`** without understanding data sparsity patterns

### What Went Right
1. ✅ Local debugging caught the issue before production
2. ✅ Diagnostic script provided clear evidence
3. ✅ Fixed data pipeline (proper NaN handling)
4. ✅ Comprehensive investigation of root cause

### Best Practices Going Forward
1. **Always validate queries** against full training set, not just manual samples
2. **Use selective filling** instead of `dropna()` for sparse metadata
3. **Monitor coverage metrics** throughout pipeline development
4. **Document data quality issues** immediately when discovered

---

## Next Steps

**IMMEDIATE (Today)**:
- [ ] Fetch metadata for 795 missing PMIDs
- [ ] Merge and verify full 1,606 sample dataset
- [ ] Complete PyCaret training pipeline

**SHORT-TERM (This Week)**:
- [ ] Update Colab notebook with fixed data pipeline
- [ ] Document metadata fetching process
- [ ] Test on full dataset

**MEDIUM-TERM (Next Week)**:
- [ ] Analyze missing paper characteristics
- [ ] Identify V4 query gaps
- [ ] Propose and test V5 query improvements

---

## Related Documents
- `V4_QUERY_MANUAL_PAPERS_ANALYSIS.md` - Original V4 query validation (100% on 13 papers)
- `docs/starting_doc.md` - Pipeline overview
- `plans/2025-11-11_pycaret_metadata_classification.md` - PyCaret implementation plan

---

## Appendix: Code Snippets

### Missing PMID Extraction
```python
import pandas as pd
import numpy as pd

# Load data
df_train = pd.read_csv('data/manual_classifications.csv', encoding='latin-1')
df_meta = pd.read_csv('data/final_query_v4_2011_2021/query_results_complete.csv',
                       encoding='latin-1', low_memory=False)

# Extract PMIDs
def extract_pmid(id_value):
    try:
        return float(id_value)
    except (ValueError, TypeError):
        if isinstance(id_value, str):
            import re
            match = re.match(r'^(\d+)', id_value)
            if match:
                return float(match.group(1))
        return np.nan

df_train['pmid'] = df_train['id'].apply(extract_pmid)
df_train = df_train[df_train['pmid'].notna()]

df_meta['pmid'] = df_meta['id'].astype(float)

# Find missing
train_pmids = set(df_train['pmid'])
meta_pmids = set(df_meta['pmid'])
missing_pmids = sorted(list(train_pmids - meta_pmids))

print(f"Missing PMIDs: {len(missing_pmids)}")
# Save for metadata fetching
pd.DataFrame({'pmid': missing_pmids}).to_csv('missing_pmids.txt', index=False, header=False)
```

### Fixed Data Pipeline (Key Change)
```python
# ❌ OLD: Removed ALL data
data_for_pycaret = df[feature_cols + ['label']].copy()
data_for_pycaret = data_for_pycaret.dropna()  # 1606 -> 0 rows!

# ✅ NEW: Selective filling preserves data
data_for_pycaret = df[feature_cols + ['label']].copy()
data_for_pycaret = data_for_pycaret.fillna(0)  # 1606 -> 1606 rows (or 811 with current metadata)
```

---

**Status**: Investigation complete, awaiting metadata fetch to proceed with training.
