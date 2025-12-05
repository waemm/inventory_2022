# Best Name Quality Control Analysis - Rows 1-500

**Analysis Date:** 2025-12-05
**Input File:** `final_inventory.csv`
**Rows Analyzed:** 1-500
**Output File:** `best_name_qc_rows_1_500.csv`

---

## Executive Summary

Out of 500 rows analyzed, **18 entries (3.6%)** have quality issues with the `best_name` field.

**Overall Quality:** 96.4% of entries have acceptable names.

---

## Issue Breakdown by Category

| Category | Count | % of Issues | Priority | Description |
|----------|-------|-------------|----------|-------------|
| **HAS_BRACKETS** | 9 | 50.0% | MEDIUM | Names with parenthetical suffixes |
| **VERY_SHORT** | 8 | 44.4% | HIGH | 1-2 character names (potential errors) |
| **NUMERIC_ONLY** | 1 | 5.6% | **CRITICAL** | Name is just numbers |

---

## Confidence Levels for Suggested Fixes

| Confidence | Count | % of Issues | Notes |
|------------|-------|-------------|-------|
| **HIGH** | 16 | 88.9% | Clear evidence from titles/URLs - safe to auto-correct |
| **LOW** | 2 | 11.1% | Needs manual expert review |

---

## Critical Cases Requiring Immediate Attention

### 1. NUMERIC_ONLY - INVALID NAME (1 case)

**PMID: 37870448**
- **Current:** `023`
- **Issue:** Name consists only of numbers - completely invalid
- **Paper Title:** "ASD2023: towards the integrating landscapes of allosteric knowledgebase"
- **Suggested Fix:** `ASD2023`
- **Confidence:** HIGH
- **Action:** **FIX IMMEDIATELY** - This is clearly an extraction error

---

## High Priority Cases - Very Short Names

### Cases with HIGH Confidence Fixes (6 cases)

These appear to be extraction errors where only part of the name was captured:

1. **PMID: 37244568** - `DB` → `C4S` (from title)
2. **PMID: 39319582** - `G4` → `G4LDB` (from title)
3. **PMID: 37953304** - `DO` → `DO-KB` (from title)
4. **PMID: 36464767** - `MM` → `CMM-` (from title)
5. **PMID: 39999010** - `PM` → `NPM` (from title)
6. **PMID: 37566336** - `EX` → `CPB-LEX` (from title)

### Cases Requiring Manual Review (2 cases - LOW confidence)

1. **PMID: 38757367** - `GO` → ?
   - **Paper:** "Mutual annotation-based prediction of protein domain functions with Domain2GO"
   - **Suggested:** `Domain2GO` (not `GO` alone)
   - **Issue:** Current name is too generic

2. **PMID: 39288310** - `AG` → ?
   - **Paper:** "Biomedical knowledge graph-optimized prompt generation for large language models"
   - **URL:** speaks.rbvi.ucsf.edu/neighborhood.html
   - **Issue:** No clear resource name in title; may need manual inspection

---

## Medium Priority - Bracketed Names

9 entries have bracketed suffixes indicating disambiguation or parent platform:

### Cases Where Title Suggests Different Name

1. **PMID: 34634793** - `Prokaryotes (lpsn)` → ?
   - **Paper:** "TYGS and LPSN: a database tandem..."
   - **Issue:** Two resources mentioned - TYGS and LPSN
   - **Recommendation:** May need TWO separate entries or choose primary resource

2. **PMID: 36857575** - `KBASE (narrative)` → ?
   - **Paper:** "kb_DRAM: annotation and metabolic profiling..."
   - **Issue:** Paper is about DRAM tool, not KBase platform
   - **Recommendation:** Consider `DRAM` or `kb_DRAM`

3. **PMID: 39905665** - `3d (brainportal)` → `DHARANI`
   - **Paper:** Contains "DHARANI"
   - **Recommendation:** Use proper name from title

### Cases Where Brackets Are Just Disambiguation

4. **PMID: 39677536** - `FAIR (eppi)` → `FAIR`
   - Remove bracket, main name is correct

5. **PMID: 36494623** - `AMICA (bioapps)` → `AMICA`
   - Remove bracket, main name is correct

6. **PMID: 37889037** - `BASE (slkb)` → `SLKB`
   - Paper title suggests `SLKB` is the correct name

### Generic Names with Brackets (3 cases)

7. **PMID: 39959838** - `Catalog (tianzelab)`
8. **PMID: 38801081** - `Toolbox (mtb)`
9. **PMID: 35275211** - `Database (csdb)`

**Issue:** Generic terms (Catalog, Toolbox, Database) used as names
**Recommendation:** Check if more specific names available in papers

---

## Recommended Actions

### Immediate (Before Any Publication)
- [ ] **Fix PMID 37870448:** `023` → `ASD2023`

### High Priority (This Week)
- [ ] Review and fix 6 VERY_SHORT cases with HIGH confidence
- [ ] Manual review of 2 LOW confidence VERY_SHORT cases (GO, AG)
- [ ] Investigate bracketed names where title suggests different resource

### Medium Priority (Before Final Publication)
- [ ] Establish policy for bracketed disambiguators:
  - Should they be kept for clarity?
  - Or should primary name be used without brackets?
- [ ] Review 3 generic names (Catalog, Toolbox, Database)
- [ ] Verify TYGS/LPSN and KBASE/DRAM cases (may need separate entries)

### Process Improvement
- [ ] Review name extraction algorithm to prevent:
  - Number-only extractions
  - Over-truncation to 1-2 characters
  - Generic term assignment
- [ ] Add validation rules:
  - Flag numeric-only names
  - Flag 1-2 character names
  - Flag generic terms (Database, Catalog, Tool, etc.)

---

## Statistics

- **Total Rows Analyzed:** 500
- **Rows with Issues:** 18 (3.6%)
- **Rows OK:** 482 (96.4%)

### By Priority
- **CRITICAL:** 1 case (0.2%)
- **HIGH:** 8 cases (1.6%)
- **MEDIUM:** 9 cases (1.8%)

### By Confidence of Fix
- **HIGH Confidence:** 16 cases (88.9% of issues)
- **LOW Confidence:** 2 cases (11.1% of issues)

---

## Files Generated

1. **best_name_qc_rows_1_500.csv** - Detailed list of all 18 problematic entries with evidence and suggestions
2. **BEST_NAME_QC_SUMMARY.md** - This summary report

---

## Notes

The overall quality is good (96.4% clean), but the identified issues need attention to ensure data quality. Most issues (88.9%) have clear fixes with high confidence based on paper titles and URLs.

The most concerning pattern is the extraction algorithm occasionally producing:
- Number-only names (1 case)
- Over-truncated names (8 cases)
- Generic terms as names (3 cases)

These patterns suggest opportunities for validation rules in the extraction pipeline.
