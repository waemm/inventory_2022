# Script Audit Criteria for Session-Based Pipeline

**Created:** 2025-12-05
**Purpose:** Standard criteria for auditing scripts to ensure session directory compliance

---

## Overview

All scripts in the unified pipeline must follow session-based architecture where:
- All inputs come from the session directory
- All outputs go to the session directory
- No hardcoded paths exist outside the session structure

---

## Audit Criteria

### 1. Session Directory Support

| Check | Required |
|-------|----------|
| Accepts `--session-dir` argument | YES |
| Uses `lib/session_utils.py` helpers | RECOMMENDED |
| Validates session directory exists | YES |
| Creates output subdirectories if needed | YES |

### 2. Input Path Compliance

| Check | Required |
|-------|----------|
| All input files read from session directory | YES |
| No hardcoded absolute paths | YES |
| Handles missing input files gracefully | YES |
| Documents expected input files | RECOMMENDED |

### 3. Output Path Compliance

| Check | Required |
|-------|----------|
| All output files written to session directory | YES |
| Output directory created if missing | YES |
| No files written outside session | YES |
| Documents output files produced | RECOMMENDED |

### 4. Profile Directory Handling

For scripts that work with deduplication output:

| Check | Required |
|-------|----------|
| Accepts `--profile` argument | YES (if applicable) |
| Supports: conservative, balanced, aggressive | YES |
| Default profile: aggressive | RECOMMENDED |
| Checks multiple input locations (fallback) | RECOMMENDED |

### 5. File Dependency Chain

Scripts must correctly chain inputs/outputs:

```
Phase 6 (Scanning):
  Script 18 → 06_scanning/set_c_url_scan_results.csv
  Script 19 reads: 06_scanning/set_c_url_scan_results.csv
                   07_deduplication/{profile}/set_c_final.csv
  Script 19 → 06_scanning/set_c_with_scan_scores.csv

Phase 9 (Finalization):
  Script 25 reads: 06_scanning/set_c_with_scan_scores.csv (or dedup output)
  Script 25 → 09_finalization/set_c_with_metadata.csv

  Script 27 reads: 09_finalization/set_c_with_metadata.csv
  Script 27 → 09_finalization/final_inventory.csv
```

---

## Session Directory Structure

```
{session_id}/
├── 01_query/
├── 02_ner_union/
├── 03_linguistic_scoring/
├── 04_setfit/
├── 05_paper_sets/
├── 06_scanning/
│   ├── set_c_url_scan_results.csv    # From Script 18
│   └── set_c_with_scan_scores.csv    # From Script 19
├── 07_deduplication/
│   ├── aggressive/
│   │   └── set_c_final.csv
│   ├── balanced/
│   └── conservative/
├── 08_url_recovery/
│   └── final/
│       └── set_c_with_urls.csv
└── 09_finalization/
    ├── set_c_with_metadata.csv       # From Script 25
    └── final_inventory.csv           # From Script 27
```

---

## Audit Output Format

For each script audited, report:

```
Script: {script_name}
Path: {full_path}

Session-dir Support:    PASS/FAIL/NEEDS_UPDATE
Input Path Compliance:  PASS/FAIL/NEEDS_UPDATE
Output Path Compliance: PASS/FAIL/NEEDS_UPDATE
Profile Handling:       PASS/FAIL/N/A
File Dependencies:      PASS/FAIL/NEEDS_UPDATE

Issues Found:
- [CRITICAL/MAJOR/MINOR] Description

Required Fixes:
1. Description of fix needed

Overall: COMPLIANT / NEEDS_FIXES
```

---

## Scripts Pending Audit (2025-12-05)

| Script | Phase | Status |
|--------|-------|--------|
| `19_backfill_url_data.py` | Phase 6 | Pending |
| `25_fetch_epmc_metadata.py` | Phase 9 | Pending |
| `27_generate_final_inventory.py` | Phase 9 | Pending |

---

## Previously Audited Scripts

| Script | Phase | Status | Date |
|--------|-------|--------|------|
| `18_scan_urls_set_c.py` | Phase 6 | COMPLIANT (after fixes) | 2025-12-05 |
| `14_prepare_urls.py` | Phase 6 | COMPLIANT | 2025-12-04 |
| `15_scan_urls.py` | Phase 6 | COMPLIANT | 2025-12-04 |
| `16_merge_scan_scores.py` | Phase 6 | COMPLIANT | 2025-12-04 |
