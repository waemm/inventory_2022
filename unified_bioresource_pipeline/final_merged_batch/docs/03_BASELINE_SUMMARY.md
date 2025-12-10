# Step 3: Baseline Comparison Summary

**Generated:** 2025-12-10 12:29:23

## Overview

Compared deduplicated inventory against the GBC baseline database to identify
resources already in the baseline vs new discoveries.

---

## Baseline Database

| Metric | Value |
|--------|-------|
| Unique resources | 3,789 |
| Papers (PMIDs) | 4,554 |

---

## Match Results

| Match Type | Count | Description |
|------------|-------|-------------|
| PMID Match | 397 | Exact paper match in baseline |
| Name Match | 373 | Resource name match |
| No Match | 1,652 | Potentially new resources |
| **Total** | **2,422** | |

---

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| In Baseline | 770 | 31.8% |
| New Resources | 1,652 | 68.2% |

---

## Output Files

- `review/baseline_matches.csv` (2,422 records)

---

## Next Steps

1. **Review the baseline matches:**
   ```
   review/baseline_matches.csv
   ```

2. **Edit the `user_decision` column:**
   - `IN_BASELINE` - Confirm this is in the baseline
   - `NEW_RESOURCE` - Confirm this is a new resource
   - Leave blank to accept recommendation

3. **When ready, apply baseline flags:**
   ```bash
   python scripts/03b_apply_baseline.py
   ```
