# Step 3c: URL-Based Baseline Matching Summary

**Generated:** 2025-12-10 14:15:48

## Overview

Attempted to match inventory URLs against baseline URLs for records that had no PMID or name match.

---

## Results

| Metric | Value |
|--------|-------|
| NO_MATCH records checked | 1,652 |
| URL matches found | 312 |
| Match rate | 18.9% |

---

## Match Type Breakdown

| Match Type | Count | Confidence | Description |
|------------|-------|------------|-------------|
| URL_EXACT | 27 | 0.95 | Normalized URLs match exactly |
| URL_DOMAIN_SINGLE | 91 | 0.75 | Same domain, only one baseline resource |
| URL_DOMAIN_MULTI | 194 | 0.50 | Same domain, multiple baseline resources (needs review) |

---

## Recommendations

- **URL_EXACT matches**: High confidence, can be accepted
- **URL_DOMAIN_SINGLE matches**: Good confidence, review recommended
- **URL_DOMAIN_MULTI matches**: Lower confidence, manual review required

---

## Output Files

- `review/baseline_url_matches.csv` (312 records)

---

## Integration

These URL matches can be combined with the existing baseline matches to improve coverage.
Records in this file were previously marked as NO_MATCH but now have URL-based matches.
