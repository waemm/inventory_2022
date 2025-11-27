# False Positive Analysis Progress

**Created**: 2025-11-26
**Last Updated**: 2025-11-26
**Status**: In Progress

---

## Overview

This analysis reviews papers from the aggressive profile Set C (10,810 papers) to identify false positives and extract database names from true bioresources.

### Source Data
- **Input file**: `pipeline_synthesis_2025-11-18/results/baseline_comparison/aggressive/set_c_with_baseline.csv`
- **Total papers**: 10,810
- **Chunks created**: 22 (500 papers each, last chunk has 310)

### Output Files
| File | Description | Status |
|------|-------------|--------|
| `consolidated_full_review.csv` | All 10,810 papers with classifications | Pending |
| `consolidated_fp_only.csv` | Only false positives for manual review | Pending |

---

## Guide Development History

### Version 1 (Initial)
- Basic rules for title-based classification
- FALSE POSITIVE indicators: "tool for", "method for", "pipeline for", etc.
- TRUE BIORESOURCE indicators: "database", "repository", "archive", "atlas"

### Version 2 (After User Annotation Review)
Based on user review of 267 filtered papers (60 marked as bioresources):

**Added FALSE POSITIVE indicators:**
- "integration platform" - tools for combining data, NOT databases

**Added TRUE BIORESOURCE indicators:**
- Name suffixes: [Name]DB, [Name]Base, [Name]KB, [Name]pedia, [Name]Map, [Name]Hub
- Knowledge terms: "knowledge base", "encyclopedia", "reference panel", "compendium"
- Priority rule: Name suffixes override methodology keywords

### Version 3 (Current)
**Added database name extraction:**
- `database_name`: Short name/acronym (e.g., MGD, VIPERdb, OncoKB)
- `long_database_name`: Full expanded name (e.g., Mouse Gene Expression Database)

---

## Processing Progress

### Chunk Status

| Chunk | Papers | Agent Review | Has DB Names | Consolidation | Notes |
|-------|--------|--------------|--------------|---------------|-------|
| 01 | 1-500 | DONE (v1) | NO | DONE (v1) | NEEDS RE-RUN with v3 guide |
| 02 | 501-1000 | DONE (v1) | NO | DONE (v1) | NEEDS RE-RUN with v3 guide |
| 03 | 1001-1500 | DONE (v1) | NO | DONE (v1) | NEEDS RE-RUN with v3 guide |
| 04 | 1501-2000 | DONE (v1) | NO | DONE (v1) | NEEDS RE-RUN with v3 guide |
| 05 | 2001-2500 | DONE (v1) | NO | DONE (v1) | NEEDS RE-RUN with v3 guide |
| 06 | 2501-3000 | DONE (v3) | YES | PENDING | FP:184 Bio:316 |
| 07 | 3001-3500 | DONE (v3) | YES | PENDING | FP:283 Bio:218 |
| 08 | 3501-4000 | DONE (v3) | YES | PENDING | FP:339 Bio:162 |
| 09 | 4001-4500 | DONE (v3) | YES | PENDING | FP:254 Bio:246 |
| 10 | 4501-5000 | DONE (v3) | YES | PENDING | FP:335 Bio:165 |
| 11 | 5001-5500 | DONE (v3) | YES | PENDING | FP:262 Bio:238 |
| 12 | 5501-6000 | DONE (v3) | YES | PENDING | FP:312 Bio:187 |
| 13 | 6001-6500 | DONE (v3) | YES | PENDING | FP:371 Bio:128 |
| 14 | 6501-7000 | DONE (v3) | YES | PENDING | FP:230 Bio:270 |
| 15 | 7001-7500 | DONE (v3) | YES | PENDING | FP:280 Bio:220 |
| 16 | 7501-8000 | DONE (v3) | YES | PENDING | FP:285 Bio:215 |
| 17 | 8001-8500 | DONE (v3) | YES | PENDING | FP:291 Bio:209 |
| 18 | 8501-9000 | DONE (v3) | YES | PENDING | FP:278 Bio:222 |
| 19 | 9001-9500 | DONE (v3) | YES | PENDING | FP:315 Bio:184 |
| 20 | 9501-10000 | DONE (v3) | YES | PENDING | FP:270 Bio:59 |
| 21 | 10001-10500 | IN PROGRESS | - | - | |
| 22 | 10501-10810 | IN PROGRESS | - | - | |

### Batch Processing Plan

| Batch | Chunks | Status | Notes |
|-------|--------|--------|-------|
| Batch 1 | 01-05 | NEEDS RE-RUN | Original run lacked database name extraction |
| Batch 2 | 06-10 | DONE | FP:1395 Bio:1107 (55.8%/44.2%) |
| Batch 3 | 11-15 | DONE | FP:1455 Bio:1043 (58.2%/41.8%) |
| Batch 4 | 16-20 | DONE | FP:1439 Bio:889 (61.8%/38.2%) |
| Batch 5 | 21-22 | IN PROGRESS | Running with v3 guide |

---

## Output Column Definitions

| Column | Description |
|--------|-------------|
| pmid | PubMed ID(s) for the paper |
| title | Paper title |
| has_url | Whether paper has a resource URL (True/False) |
| is_false_positive | Y = False Positive, N = True Bioresource |
| confidence | high/medium/low |
| reason | Brief explanation for classification |
| database_name | Short name/acronym (if bioresource) |
| long_database_name | Full expanded name (if bioresource) |
| consol_agent_agree | Y = consolidation agent agrees, N = disagrees |
| consol_is_fp | Consolidation agent's classification (if disagrees) |
| consol_reason | Consolidation agent's reasoning (if disagrees) |

---

## Files Created

### Documentation
- `docs/FALSE_POSITIVE_DETECTION_GUIDE.md` - Agent instructions (v3)
- `PROGRESS.md` - This file

### Data Files
- `chunks/chunk_01.csv` through `chunk_22.csv` - Input data chunks
- `agent_reviews/chunk_XX_review.csv` - Individual agent outputs
- `consolidated_fp_review.csv` - Initial consolidation (v1, 2500 papers)
- `fp_review_filtered.csv` - Filtered for FPs and conflicts (267 papers)

### Scripts
- `chunk_data.py` - Script to create data chunks

---

## Action Items

1. [x] Create progress documentation
2. [ ] Run agents on chunks 06-10 (Batch 2)
3. [ ] Re-run agents on chunks 01-05 with v3 guide (database names)
4. [ ] Run agents on chunks 11-15 (Batch 3)
5. [ ] Run agents on chunks 16-20 (Batch 4)
6. [ ] Run agents on chunks 21-22 (Batch 5)
7. [ ] Run consolidation agent on all chunks
8. [ ] Generate final outputs:
   - `consolidated_full_review.csv`
   - `consolidated_fp_only.csv`

---

## Session Log

### 2025-11-26 Session 1
- Created initial chunking (22 chunks)
- Ran agents on chunks 1-5 with v1 guide
- Ran consolidation agent on chunks 1-5
- Results: 2,500 papers processed
  - 93.2% agreement rate
  - 171 disagreements
- User reviewed 267 filtered papers
- Updated guide to v2 based on user annotations:
  - Added name suffix rules (DB, KB, Base, pedia, Map, Hub)
  - Added knowledge terms (knowledge base, encyclopedia, etc.)
  - Clarified "integration platform" as FALSE POSITIVE
- Updated guide to v3:
  - Added database_name and long_database_name extraction
- **Next**: Run chunks 6-10, then re-run chunks 1-5

---

## Notes

- Chunks 1-5 need re-processing because they were run before database name extraction was added
- All future runs should use the v3 guide in `docs/FALSE_POSITIVE_DETECTION_GUIDE.md`
- Priority rule: Name suffixes (DB, KB, Base, pedia, Map) override methodology keywords
