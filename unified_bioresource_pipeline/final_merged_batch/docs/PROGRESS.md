# Final Merged Batch Pipeline Progress

**Last Updated:** 2025-12-10
**Status:** COMPLETE

## Project Overview

Merging two bioresource inventory batches to create a unified, deduplicated inventory of live bioinformatics resources:
- **Batch 1 (2010-2022):** Historical inventory from previous pipeline run
- **Batch 2 (2022-2025):** New inventory from December 2025 pipeline run

---

## Final Results

| Metric | Value |
|--------|-------|
| **Total deduplicated records** | **2,422** |
| Removed (in GBC baseline) | 825 (34.1%) |
| **NEW resources to investigate** | **1,597** (65.9%) |

---

## Pipeline Steps

| Step | Script | Status | Description |
|------|--------|--------|-------------|
| 1 | `01_filter_live_urls.py` | COMPLETE | Filter to live URLs only |
| 2 | `02_identify_duplicates.py` | COMPLETE | Detect potential duplicates |
| 2b | `02b_apply_merges.py` | COMPLETE | Apply user-reviewed merges |
| 3 | `03_identify_baseline.py` | COMPLETE | Compare to GBC baseline (PMID + NAME) |
| 3c | `03c_url_matching.py` | COMPLETE | Additional URL-based baseline matching |
| Final | (manual process) | COMPLETE | Remove baseline matches, keep NEW only |

---

## Completed Steps

### Step 1: URL Filtering (2025-12-10)

Filtered both batches to include only resources with live URLs (HTTP 200).

| Batch | Input | Live URLs | Filtered Out | Retention |
|-------|-------|-----------|--------------|-----------|
| 2010-2022 | 1,688 | 996 | 692 | 59.0% |
| 2022-2025 | 1,510 | 1,510 | 0 | 100.0% |
| **Total** | **3,198** | **2,506** | **692** | **78.4%** |

**Output:** `data/filtered/batch_2010_2022_live.csv`, `data/filtered/batch_2022_2025_live.csv`

---

### Step 2: Duplicate Detection (2025-12-10)

Identified potential duplicates using strict matching algorithm:
- Exact URL match required for high-confidence merges
- Multi-resource domains (NCBI, EBI, etc.) require exact path OR ≥95% name similarity
- Name similarity thresholds at each level

| Metric | Value |
|--------|-------|
| Total records | 2,506 |
| Unique (no duplicates) | 2,415 |
| Duplicate clusters | 68 |
| Records in clusters | 159 |

**Recommendation Breakdown:**
- MERGE: 37 (Exact URL + similar name ≥85%)
- LIKELY_MERGE: 33 (Same path + name match ≥70%)
- REVIEW: 89 (Needs manual verification)

**Output:** `review/proposed_merges.csv` for user review

---

### Step 2b: Merge Application (2025-12-10)

Applied user-reviewed merge decisions with custom marking system:
- `y` = Primary record (use this best_name)
- `x` = Merge these rows together
- `qw` = URL mismatch error (export to separate file)
- blank = Auto-merge for MERGE recommendation; keep separate for REVIEW

| Metric | Value |
|--------|-------|
| Input records | 2,506 |
| Output records | 2,422 |
| Records merged away | 78 |
| URL mismatch cases (qw) | 6 |
| Total reduction | 3.4% |
| Merge groups applied | 64 |
| Groups kept separate | 4 |

**User marks processed:** y=44, x=9, qw=6

**Output:**
- `data/deduplicated/merged_inventory.csv` (2,422 records)
- `data/deduplicated/url_mismatch_review.csv` (6 records for later review)

---

### Step 3: Baseline Comparison (2025-12-10)

Compared merged inventory against GBC baseline database using PMID and name matching.

| Match Method | Count |
|--------------|-------|
| PMID match | 397 |
| NAME_EXACT match | 181 |
| NAME_FUZZY match (reviewed) | 192 |
| **Subtotal** | **770** |

**Output:** `review/baseline_matches.csv`, `review/baseline_high_confidence.csv`, `review/baseline_fuzzy_review.csv`

---

### Step 3c: URL Matching (2025-12-10)

Additional baseline matching using URL comparison for records that had no PMID/name match.

| Match Type | Count | Confidence |
|------------|-------|------------|
| URL_EXACT | 27 | High - accepted |
| URL_DOMAIN_SINGLE (reviewed) | 7 | User confirmed |
| URL_DOMAIN_SINGLE (from false positives) | 17 | User confirmed |
| URL_DOMAIN_MULTI (reviewed) | 4 | User confirmed |
| **Total URL matches** | **55** | |

**Output:** `review/url_confirmed_matches.csv`

---

### Final: Remove Baseline Matches (2025-12-10)

Removed all baseline-matched records to create final inventory of NEW resources only.

| Metric | Value |
|--------|-------|
| Input (deduplicated) | 2,422 |
| Baseline matches removed | 825 |
| **NEW resources** | **1,597** |

**Breakdown by source batch:**
- 2010-2022: 726 (45.5%)
- 2022-2025: 871 (54.5%)

---

## Key Decisions Made

1. **URL Scanning:** Both batches were scanned within 2 weeks (Dec 1-5, 2025), so re-scanning was skipped.

2. **Strict Matching Algorithm:** Implemented to prevent over-merging of multi-resource domains (NCBI, EBI, Bioconductor, GitHub, etc.).

3. **Special Name Selections:**
   - Group 0: GenBank (not "GenBank/EMBL/DDBJ")
   - Group 1: UCSC (not "UCSC Table Browser")
   - Group 18: PanDrugs (not "PanDrugs2")
   - Group 28: GDBChEMBL
   - Group 46: MPI bioinformatics Toolkit
   - Group 57: Protein Data Bank Japan
   - Group 58: DDBJ

4. **URL Mismatch Cases (qw):** 6 records flagged for separate review where the URL doesn't match the resource name.

5. **URL Matching:** Added Step 3c to catch additional baseline matches via URL comparison (+55 matches).

6. **Final Output:** Removed all baseline matches to produce inventory of NEW resources only for investigation.

---

## File Structure

```
final_merged_batch/
├── data/
│   ├── filtered/
│   │   ├── batch_2010_2022_live.csv (996 records)
│   │   └── batch_2022_2025_live.csv (1,510 records)
│   ├── combined/
│   │   └── combined_batches.csv (2,506 records)
│   ├── deduplicated/
│   │   ├── merged_inventory.csv (2,422 records)
│   │   └── url_mismatch_review.csv (6 records)
│   └── final/
│       └── new_resources_to_investigate.csv (1,597 records) ← MAIN OUTPUT
├── review/
│   ├── proposed_merges.csv (user-edited)
│   ├── baseline_matches.csv
│   ├── baseline_high_confidence.csv
│   ├── baseline_fuzzy_review.csv
│   ├── url_confirmed_matches.csv
│   └── all_baseline_matches_consolidated.csv (825 records removed)
├── docs/
│   ├── 01_FILTER_SUMMARY.md
│   ├── 02_DUPLICATE_SUMMARY.md
│   ├── 02b_MERGE_APPLIED_SUMMARY.md
│   ├── 03_BASELINE_SUMMARY.md
│   ├── 03c_URL_MATCHING_SUMMARY.md
│   ├── FINAL_REPORT.md
│   └── PROGRESS.md (this file)
├── plan/
│   └── MERGE_PLAN.md
└── scripts/
    ├── 01_filter_live_urls.py
    ├── 02_identify_duplicates.py
    ├── 02b_apply_merges.py
    ├── 03_identify_baseline.py
    ├── 03c_url_matching.py
    └── 04_generate_report.py
```

---

## Next Steps

The 1,597 new resources in `data/final/new_resources_to_investigate.csv` are candidates for:

1. Manual review and curation
2. Addition to the GBC baseline database
3. Further investigation for quality and relevance
