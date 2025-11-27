# False Positive Analysis & Baseline Deduplication

**Date**: November 26-27, 2025
**Purpose**: Review pipeline outputs, identify false positives, and deduplicate against baseline inventory

---

## Overview

This directory contains the analysis and review of 10,529 papers from the bioresource pipeline to:
1. Identify false positives (papers incorrectly classified as bioresource announcements)
2. Deduplicate against the 2022 baseline inventory using improved fuzzy matching
3. Generate a final list of **truly novel bioresources**

---

## Key Results

### False Positive Review (22 Chunks)
- **Total papers reviewed**: 10,529
- **False positives identified**: 4,984 (47.3%)
- **True bioresources**: 5,545 (52.7%)

### Baseline Deduplication (v4 Algorithm)
- **True positives input**: 5,639
- **Baseline duplicates removed**: 3,045 (54.0%)
- **Truly novel bioresources**: 2,594 (46.0%)

---

## Final Output Files

| File | Records | Description |
|------|---------|-------------|
| `consolidated_true_positives_novel_only_v4.csv` | 2,594 | **Final output** - truly novel bioresources |
| `improved_filter_list_v4.txt` | 2,750 | Names filtered as baseline duplicates |
| `improved_fuzzy_match_v4.csv` | 4,008 | Full matching results |
| `consolidated_bioresources.csv` | 5,545 | All true bioresources (before dedup) |
| `consolidated_fp_only.csv` | 4,984 | All false positives |

---

## Improved Fuzzy Matching Algorithm (v4)

The `improved_fuzzy_matching.py` module implements 7 key improvements based on code review:

### 1. Generic Domain Handling
Reduced matching weight for institutional domains that host many unrelated databases:
- `.ac.uk` (UK universities)
- `.edu.cn` (Chinese universities)
- `.nih.gov` (US NIH institutes)
- And others...

### 2. Strict URL Normalization
URLs are considered identical if they differ only by:
- Trailing slash (`http://db.com/` = `http://db.com`)
- www prefix (`http://www.db.com` = `http://db.com`)
- Protocol (`https://db.com` = `http://db.com`)

### 3. Multi-Signal Requirement
HIGH confidence matches require multiple signals, not just one strong signal.

### 4. One-to-One Mapping
Each baseline database can only match ONE extracted database. Conflicts are resolved by keeping the best match.

### 5. Improved Edit Distance Weights
- Edit distance 1: Strong signal (typos)
- Edit distance 2: Medium signal
- Edit distance 3+: Weak signal

### 6. Context-Aware Contains Matching
Substring matching is weighted by context (complete token vs partial match).

### 7. Review Flags
Suspicious matches are flagged for manual review:
- `GENERIC_DOMAIN` - From institutional domain
- `SAME_DOMAIN_ONLY` - Only evidence is same domain
- `HIGH_ED_MATCH` - High edit distance
- `THRESHOLD_EDGE` - Score near decision boundary

---

## Directory Structure

```
false_positive_analysis/
├── README.md                                    # This file
├── CONSOLIDATION_REPORT.md                      # Report from chunk consolidation
├── improved_fuzzy_matching.py                   # Reusable matching module
│
├── # Final Outputs
├── consolidated_true_positives_novel_only_v4.csv  # FINAL: Novel bioresources
├── improved_filter_list_v4.txt                    # Names to filter
├── improved_fuzzy_match_v4.csv                    # All match results
│
├── # Consolidated Reviews
├── consolidated_full_review.csv                 # All 10,529 reviewed papers
├── consolidated_bioresources.csv                # 5,545 true bioresources
├── consolidated_fp_only.csv                     # 4,984 false positives
├── consolidation_statistics.json                # Per-chunk statistics
│
├── # Review Files
├── review_files_v4/                             # Review files for v4 matching
│   ├── 01_MAYBE_remaining.csv                   # 528 borderline cases
│   ├── 02_Y_url_exact_sample.csv                # Sample of URL matches
│   ├── 03_conflicts_resolved.csv                # One-to-many conflicts
│   ├── 04_EXACT_name_sample.csv                 # Sample of exact matches
│   └── 05_Y_flagged.csv                         # Flagged Y matches
│
├── agent_reviews/                               # Original chunk review files
│   ├── chunk_01_review_v3.csv
│   ├── chunk_02_review_v3.csv
│   └── ... (22 chunks)
│
└── chunks/                                      # Source data chunks
    ├── chunk_01.csv
    └── ... (22 chunks)
```

---

## Usage

### Using the Improved Fuzzy Matching Module

```python
from improved_fuzzy_matching import run_fuzzy_matching

# Run matching
matches_df, conflicts_df, filter_list = run_fuzzy_matching(
    extracted_df,
    baseline_df,
    extracted_name_col='database_name',
    baseline_name_col='best_name',
    extracted_url_col='resource_url',
    baseline_url_col='extracted_url'
)

# filter_list contains names to remove from novel dataset
```

### Standalone Execution

```bash
python improved_fuzzy_matching.py \
    --extracted consolidated_true_positives.csv \
    --baseline ../data/final_inventory_2022.csv \
    --output fuzzy_matches.csv
```

---

## Algorithm Evolution

| Version | Date | Changes | Y Matches |
|---------|------|---------|-----------|
| v1 | 2025-11-27 | Basic edit distance | N/A |
| v2 | 2025-11-27 | Added SAME_DOMAIN | 3,590 |
| v3 | 2025-11-27 | Generic domain handling, multi-signal | 2,669 |
| v4 | 2025-11-27 | Strict URL normalization | 2,750 |

---

## Related Documentation

- **Unified Pipeline Integration**: `unified_bioresource_pipeline/scripts/phase7_deduplication/`
- **Code Review Findings**: `ALGORITHM_FIXES_REQUIRED.md`
- **Consolidation Report**: `CONSOLIDATION_REPORT.md`

---

## Key Decisions Made

1. **MAYBE matches (528) treated as non-matches** - Manual review showed almost all were different resources
2. **URL exact matching upgraded to HIGH confidence** - If URLs match exactly after normalization, it's the same resource
3. **Generic domains downgraded** - `.ac.uk`, `.nih.gov`, etc. alone are weak evidence
4. **One-to-one enforcement** - Prevents one baseline matching multiple extracted (83 conflicts resolved)

---

**Last Updated**: 2025-11-27
