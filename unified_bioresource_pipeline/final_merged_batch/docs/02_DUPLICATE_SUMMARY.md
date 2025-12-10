# Step 2: Duplicate Detection Summary (Strict Matching v2)

**Generated:** 2025-12-10 11:34:19

## Overview

Combined filtered batches and identified potential duplicates using **strict** matching:
- Exact URL match required for high-confidence merges
- Multi-resource domains (NCBI, EBI, etc.) require exact path OR ≥95% name similarity
- Name similarity thresholds applied at each level

---

## Input Summary

| Batch | Records |
|-------|---------|
| 2010-2022 | 996 |
| 2022-2025 | 1,510 |
| **Combined** | **2,506** |

---

## Duplicate Detection Results

| Metric | Value |
|--------|-------|
| Total records | 2,506 |
| Unique (no duplicates) | 2,415 |
| Duplicate clusters | 68 |
| Records in clusters | 159 |
| Potential reduction | 91 (~3.6%) |

---

## Recommendation Breakdown

| Recommendation | Count | Description |
|----------------|-------|-------------|
| MERGE | 37 | Exact URL + similar name (≥85%) |
| LIKELY_MERGE | 33 | Same path + name match (≥70%) |
| REVIEW | 89 | Needs manual verification |

---

## Multi-Resource Domain Handling

The following domains host multiple independent databases and require stricter matching:
- NCBI (ncbi.nlm.nih.gov)
- EBI (ebi.ac.uk)
- UCSC Genome Browser (genome.ucsc.edu)
- Bioconductor (bioconductor.org)
- GitHub (github.com, github.io)
- And others...

For these domains, records are only grouped if:
1. Exact same URL path, OR
2. Name similarity ≥95%

---

## Output Files

- `data/combined/combined_batches.csv` (2,506 records)
- `review/proposed_merges.csv` (159 records for review)

---

## Next Steps

1. **Review the proposed merges:**
   ```
   review/proposed_merges.csv
   ```

2. **Edit the `user_decision` column:**
   - `MERGE` - Confirm merge (keep first record, merge metadata)
   - `KEEP_SEPARATE` - Do not merge these records
   - Leave blank to accept recommendation

3. **When ready, apply merges:**
   ```bash
   python scripts/02b_apply_merges.py
   ```
