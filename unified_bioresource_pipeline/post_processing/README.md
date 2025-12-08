# Post-Processing: Best Name Quality Control (Phase 10)

This directory contains tools and documentation for quality control analysis of the `best_name` column in the final inventory output. This is **Phase 10** of the unified bioresource pipeline.

## Purpose

The Phase 9 finalization pipeline produces a `final_inventory.csv` with resource names extracted from NER and URL processing. This post-processing step (Phase 10) identifies and corrects problematic names that slipped through upstream processing.

## Issue Categories Detected

| Category | Description | Example |
|----------|-------------|---------|
| `EMPTY` | Missing resource name | (blank) |
| `NUMERIC_ONLY` | Name is just a number | "265" |
| `VERY_SHORT` | 1-2 character names | "2d", "GO" |
| `SHORT_LOWERCASE` | Generic short words | "ice", "org" |
| `HAS_BRACKETS` | Disambiguation suffixes | "ENCODE (genome)" |
| `WRONG_EXTRACTION` | Name doesn't match title/URL | "Melanoma" when title says "VIGLA-M" |
| `SUSPICIOUS_CHARS` | HTML, pipes, special chars | "i>tool</i" |

## Workflow

### 1. Run QC Analysis

The analysis uses an agent-based approach documented in `docs/AGENT_PROMPT_best_name_qc.md`.

Analysis is run in chunks of ~500 rows to avoid context limits:
- Rows 1-500
- Rows 501-1000
- Rows 1001-1500
- Rows 1501-end

### 2. Review Results

Results are saved to `results/`:
- `best_name_qc_ALL.csv` - Consolidated findings from all chunks
- `best_name_qc_rows_*.csv` - Individual chunk reports

### 3. Apply Fixes

The `final_inventory_QC_FIXED.csv` contains:
- All suggested corrections applied
- Flags added to `name_modification_flags` column:
  - `QC_FIX_HIGH` - High confidence fix applied
  - `QC_FIX_MEDIUM` - Medium confidence fix applied
  - `QC_FIX_LOW` - Low confidence fix applied
  - `NEEDS_MANUAL_REVIEW` - Could not auto-fix, needs human review

## Files

```
post_processing/
├── README.md                         # This file
├── docs/
│   └── AGENT_PROMPT_best_name_qc.md  # Agent instructions
└── results/                          # Legacy results (session sa4r9)
    └── ...

# Session-specific results are stored in:
# {session_id}/post_processing/
#   ├── best_name_qc_ALL.csv          # Consolidated QC findings
#   ├── best_name_qc_rows_1_500.csv   # Chunk 1
#   ├── best_name_qc_rows_501_1000.csv
#   ├── best_name_qc_rows_1001_*.csv
#   ├── final_inventory_QC_FIXED.csv  # Fixed inventory
#   ├── fixes_applied.csv             # Log of all fixes
#   └── merge_and_fix_inventory.py    # Merge script
```

---

## Session Results

### Session z381s (2025-12-05)

**Input:** 1,510 resources from `final_inventory.csv`

**Findings:**
- Total flagged: 61 (4.0%)
- Auto-fixed: 61 (100%)
- Manual review flagged: 2

**By Category:**
| Category | Count |
|----------|-------|
| HAS_BRACKETS | 47 |
| VERY_SHORT | 12 |
| NUMERIC_ONLY | 1 |
| SUSPICIOUS_CHARS | 1 |

**By Confidence:**
| Confidence | Count | Action |
|------------|-------|--------|
| HIGH | 38 | Auto-fixed |
| MEDIUM | 21 | Auto-fixed |
| LOW | 2 | Auto-fixed, flagged for review |

**Location:** `2025-12-04-111420-z381s/post_processing/`

---

### Session sa4r9 (2025-12-01) - Legacy

**Input:** 1,688 resources from `final_inventory.csv`

**Findings:**
- Total flagged: 111 (6.6%)
- Auto-fixed: 105
- Needs manual review: 6

**By Confidence:**
| Confidence | Count | Action |
|------------|-------|--------|
| HIGH | 29 | Auto-fixed |
| MEDIUM | 66 | Auto-fixed |
| LOW | 16 | 10 auto-fixed, 6 manual review |

**Location:** `post_processing/results/` (legacy)

## Common Root Causes

1. **URL disambiguation adding noise**: Bracket suffixes like "(genome)" from URL domains
2. **POPULATED_FROM_URL extracting wrong part**: Getting path segments (e.g., "265") instead of resource names
3. **NER extracting partial names**: Short fragments instead of full resource names
4. **Title case mismatches**: Paper titles sometimes have incorrect capitalization

## Integration with Pipeline

This post-processing step runs AFTER Phase 9 finalization as **Phase 10**:

```
Phase 9 Scripts (22-27)
         ↓
final_inventory.csv
         ↓
Phase 10: Post-Processing QC Analysis
  • Launch 3 parallel agents (chunks of ~500 rows)
  • Detect issues: empty, numeric, short, bracketed, suspicious
  • Investigate using paper_titles, extracted_url, best_common, best_full
  • Generate suggested fixes with confidence levels
         ↓
merge_and_fix_inventory.py
  • Merge chunk results
  • Apply fixes to inventory
  • Add QC columns: best_name_original, qc_manual_review, etc.
         ↓
final_inventory_QC_FIXED.csv
```

## New Columns Added

The fixed inventory includes these new columns:

| Column | Description |
|--------|-------------|
| `best_name_original` | Original name before QC fix |
| `qc_manual_review` | YES/NO - whether item needs human review |
| `qc_fix_applied` | YES if a QC fix was applied |
| `qc_confidence` | HIGH/MEDIUM/LOW confidence of fix |
| `qc_issue_category` | Type of issue detected |

## Future Improvements

Based on patterns found:
1. Improve URL-based name extraction to avoid path segments
2. Add minimum name length validation in Script 23
3. Consider removing bracket disambiguation or making it optional
4. Add title-based validation earlier in pipeline

---

**Last Updated:** 2025-12-05
