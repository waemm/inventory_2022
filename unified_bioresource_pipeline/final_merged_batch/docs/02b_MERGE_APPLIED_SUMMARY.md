# Step 2b: Merge Application Summary

**Generated:** 2025-12-10 12:07:22

## Overview

Applied user-reviewed merge decisions to deduplicate the combined inventory.

---

## Results

| Metric | Value |
|--------|-------|
| Input records | 2,506 |
| Output records | 2,422 |
| Records merged away | 78 |
| URL mismatch cases (qw) | 6 |
| Total reduction | 3.4% |

---

## Merge Statistics

| Action | Count |
|--------|-------|
| Merge groups applied | 64 |
| Groups kept separate | 4 |

---

## Output Files

- `data/deduplicated/merged_inventory.csv` (2,422 records)
- `data/deduplicated/url_mismatch_review.csv` (6 records for later review)

---

## URL Mismatch Cases

Records marked with 'qw' have been exported to a separate file for manual review.
These are cases where the URL doesn't match the resource name and need investigation.

---

## Next Steps

Proceed to baseline comparison:

```bash
python scripts/03_identify_baseline.py
```
