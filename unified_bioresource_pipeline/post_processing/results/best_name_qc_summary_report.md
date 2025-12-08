# Best Name Quality Control Report
## Analysis of Rows 1501-1688

**Date:** 2025-12-01
**Analyst:** Quality Control System
**Input File:** `unified_bioresource_pipeline/results/2025-12-01-104909-sa4r9/finalization/final_inventory.csv`

---

## Executive Summary

Out of **189 rows** analyzed (rows 1501-1688), **52 rows (27.5%)** were flagged with quality issues in the `best_name` field. The majority of issues (75%) involve wrong extraction where the extracted name doesn't match the actual resource described in the paper title or URL.

### Key Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Rows Analyzed | 189 | 100% |
| Rows Flagged | 52 | 27.5% |
| Clean Rows | 137 | 72.5% |
| High Confidence Fixes Available | 8 | 15.4% of flagged |
| Medium Confidence Fixes | 38 | 73.1% of flagged |
| Require Manual Review | 6 | 11.5% of flagged |

---

## Issue Category Breakdown

| Issue Type | Count | % of Flagged | Description |
|------------|-------|--------------|-------------|
| **WRONG_EXTRACTION** | 39 | 75.0% | Name doesn't match paper title/URL context |
| **HAS_BRACKETS** | 17 | 32.7% | Contains parentheses (often URL domain suffix) |
| **NUMERIC_ONLY** | 1 | 1.9% | Name is just a number |
| **VERY_SHORT** | 1 | 1.9% | Name is 1-2 characters |

Note: Some rows have multiple issues (e.g., both HAS_BRACKETS and WRONG_EXTRACTION)

---

## Known Problem Cases - All Found ✓

All 3 user-flagged problem cases were successfully detected:

### 1. PMID 30999846
- **Current:** "Melanoma (khaos)"
- **Issue:** Title says "VIGLA-M" - completely wrong extraction
- **Suggested:** VIGLA-M
- **Confidence:** MEDIUM

### 2. PMID 34292965
- **Current:** "265"
- **Issue:** Numeric only, extracted from URL path
- **Suggested:** MANUAL_REVIEW_NEEDED
- **Confidence:** LOW
- **Note:** Title is about periodontal trials outcome set - may not have a specific database name

### 3. PMID 21841810
- **Current:** "2d"
- **Issue:** Very short (2 characters), from URL domain
- **Suggested:** MANUAL_REVIEW_NEEDED
- **Confidence:** LOW
- **Note:** Appears to be a proteomics reference map

---

## High-Confidence Fix Examples

These cases have clear alternatives in the `best_common` field:

| PMID | Current Name | Suggested Fix | Issue |
|------|--------------|---------------|-------|
| 27303626 | GEO (placentalendocrinology) | geo | Has unnecessary domain suffix in brackets |
| 33858332 | TCGA (manticore) | tcga | Has unnecessary domain suffix in brackets |
| 30783007 | PDB (ifr48) | pdb | Has unnecessary domain suffix in brackets |
| 28195585 | GBIF (science) | gbif | Has unnecessary domain suffix in brackets |
| 29605928 | CHEBI | chebi | Wrong - should be from title EMBL-EBI context |
| 24234439 | CHEMBL | chembl | Mismatch with IUPHAR/BPS content |
| 24792157 | STRING | string | Mismatch with SIB content |
| 28934507 | GEO (134) | geo | Has IP address in brackets |

---

## Medium-Confidence Fixes

These cases have potential fixes from title extraction or `best_full` field:

### Examples of Title-Based Extraction:
- **PMID 32838343:** Covid19 (amp) → COVID-19
- **PMID 21929785:** PRO (pir) → PRO
- **PMID 33858848:** Hla-ligand-atlas → HLA
- **PMID 21990165:** LOVD (brca) → BRCA

### Pattern: Domain Names Used as Resource Names
Many cases show the URL domain was used instead of the actual resource name:
- Covid19dataportal → COVID-19
- Caliberresearch → CALIBER
- Hla-ligand-atlas → HLA
- Covid-19-diagnostics → COVID-19

---

## Low-Confidence / Manual Review Required

6 cases need manual review due to lack of clear alternatives:

| PMID | Current Name | Issue | Context |
|------|--------------|-------|---------|
| 34292965 | 265 | Numeric only | Periodontal trials outcome set |
| 21841810 | 2d | Very short | Proteomics reference map |
| 28039431 | Database (hpcwebapps) | Generic + domain | Unclear resource name |
| 22114206 | Database (helixweb) | Generic + domain | Gene expression database |
| 29092956 | Personalizedcancertherapy | Domain name | May be correct as-is |
| 33683565 | Healthy-worm-database | Domain name | May be correct as-is |

---

## Patterns Identified

### 1. Bracket Contamination (32.7% of issues)
Many names have URL domain suffixes in parentheses that should be removed:
- Pattern: `ResourceName (domain)`
- Example: `GEO (placentalendocrinology)` should be `GEO`

### 2. Domain-as-Name Problem (Major pattern in WRONG_EXTRACTION)
URL domains being used as resource names instead of extracting the actual database/tool name from title:
- Pattern: URL domain like `covid19dataportal` used instead of resource name `COVID-19`
- Affects ~25 entries

### 3. Generic Terms
"Database" appears as the name in some cases, which is too generic

---

## Recommendations

### Immediate Actions (High Confidence - 8 cases)
Apply automated fixes for the 8 HIGH confidence cases where `best_common` provides clear alternatives.

### Semi-Automated Actions (Medium Confidence - 38 cases)
Review and apply the suggested fixes from title extraction. These appear correct but should have quick human validation.

### Manual Review Queue (Low Confidence - 6 cases)
Queue for expert review:
- 2 cases with no clear resource name (PMID 34292965, 21841810)
- 4 cases where domain name might be the actual resource name

### System Improvements
1. **Post-processing rule:** Strip parenthetical domain suffixes from names
2. **Extraction priority:** Prefer uppercase acronyms from titles over URL domains
3. **Validation:** Flag numeric-only and very short names for review

---

## Output Files

1. **Detailed CSV:** `best_name_qc_rows_1501_1688.csv`
   - Contains all 52 flagged cases with evidence and suggestions

2. **Summary Report:** `best_name_qc_summary_report.md` (this file)

---

## Quality Metrics

- **Detection Rate:** 100% of known problem cases found
- **Fix Availability:** 88.5% have suggested fixes (46/52)
- **Automation Ready:** 15.4% can be auto-fixed (8/52)
- **Human Review Needed:** 11.5% (6/52)

The analysis successfully identified all flagged problem cases and provides actionable fixes for the majority of quality issues.
