# Best Name Quality Control Analysis Report
## Rows 1001-1500 (500 rows analyzed)

**Analysis Date:** 2025-12-01
**Input File:** `unified_bioresource_pipeline/results/2025-12-01-104909-sa4r9/finalization/final_inventory.csv`
**Output File:** `unified_bioresource_pipeline/post_processing/results/best_name_qc_rows_1001_1500.csv`

---

## Executive Summary

- **Total rows analyzed:** 500
- **Rows flagged:** 37 (7.4%)
- **Clean rows:** 463 (92.6%)

The analysis identified **3 main issue categories**:

1. **HAS_BRACKETS** (24 cases, 64.9%): Names with parenthetical disambiguation
2. **VERY_SHORT** (8 cases, 21.6%): Names with 1-2 characters (acronyms)
3. **SHORT_LOWERCASE** (5 cases, 13.5%): Short generic lowercase names

---

## Issue Categories Analysis

### 1. HAS_BRACKETS (24 cases)

These are resources where the `best_name` includes parenthetical disambiguation, typically to distinguish between different versions or contexts of the same resource.

**Examples:**
- `SEEK (snp-seek)` → Suggested: "Rice SNP" (from title)
- `Genomics (genome-cancer)` → Suggested: "The UCSC Cancer Genomics Browser"
- `Database (pgl)` → Generic name, needs title context
- `GXB (breastcancer)`, `GXB (monocyte)`, `GXB (pid)` → Multiple GXB variants
- `COSMIC (cr10)`, `COSMIC (score)` → COSMIC database variants

**Analysis:**
- Most parenthetical additions provide valuable disambiguation
- Some could be improved by using the full name from the title
- GXB (Gene Expression Browser) appears multiple times with different specializations
- COSMIC appears with different release versions/scores

**Recommendations:**
- Keep brackets when they provide essential disambiguation (e.g., GXB variants)
- Consider using full names for standalone resources
- Review whether version numbers in brackets are necessary

### 2. VERY_SHORT (8 cases)

Names with only 1-2 characters, typically well-known acronyms.

**Examples:**
- `GO` (Gene Ontology) - appears twice (PMIDs: 27899567, 30395331, 25428369)
- `TO` (Drug Target Ontology) - PMID: 29122012
- `IM` - PMID: 23721660
- `EQ` - PMID: 27863463
- `AX` (JAX Synteny Browser) - PMID: 31776723
- `BR` - PMID: 33555347
- `PX` - PMID: 32941026

**Analysis:**
- GO is a widely recognized acronym and acceptable
- Some acronyms like "TO", "IM", "EQ" are too generic
- Title evidence suggests better full names available

**Recommendations:**
- Keep "GO" as it's universally recognized
- Expand other 2-letter acronyms to full names from titles
- Consider "Gene Ontology" instead of "GO" for clarity

### 3. SHORT_LOWERCASE (5 cases)

Short (3-4 character) all-lowercase names that may be too generic.

**Examples:**
- `org` - PMID: 33590862 (long-read-tools.org)
- `3dgb` - PMID: 25990738
- `ase` - PMID: 31100356
- `t4.0` - PMID: 24767513 (version number!)
- `tlas` - PMID: 28185543

**Analysis:**
- `org` is too generic (domain suffix)
- `t4.0` is a version number, not a resource name
- Others may be valid short codes but lack context

**Recommendations:**
- Replace `org` with actual resource name from title
- Replace `t4.0` with resource name (appears to be Medicago-related)
- Verify if short codes are official abbreviations

---

## Notable High-Confidence Fixes

The following fix was identified with HIGH confidence:

**PMID: 27134731**
- Current: `GEO (hiv)`
- Suggested: `gene expression omnibus` (from best_full)
- Evidence: Both best_common and best_full agree
- Recommendation: **USE THIS FIX**

---

## Parenthetical Disambiguation Patterns

Several resource families use parenthetical disambiguation effectively:

### GXB (Gene Expression Browser) Family
- GXB (breastcancer)
- GXB (ige)
- GXB (ivf)
- GXB (monocyte)
- GXB (pid)

**Analysis:** These represent different specialized versions of the GXB platform. The parenthetical additions are essential and should be retained.

### COSMIC Database Variants
- COSMIC (cr10)
- COSMIC (score)

**Analysis:** These represent different COSMIC releases/features. Consider whether these should use full names or keep disambiguation.

### ZENODO Deposits
- ZENODO (bluebox)
- ZENODO (trivellone)

**Analysis:** These appear to be different ZENODO datasets. The parenthetical may refer to depositor/project.

---

## Data Quality Observations

### Strengths
1. **High overall quality**: 92.6% of names are clean
2. **Consistent capitalization**: Most names follow proper capitalization rules
3. **Meaningful disambiguation**: Parenthetical additions generally serve a purpose

### Areas for Improvement
1. **Version numbers as names**: `t4.0` should not be a resource name
2. **Generic words**: `org`, `database` are too generic
3. **Ultra-short acronyms**: 2-letter codes like `TO`, `IM`, `EQ` need expansion
4. **Consistency**: Some resources use full names while similar ones use acronyms

---

## Recommended Actions

### Immediate Fixes (High Priority)

1. **PMID 27134731**: Change `GEO (hiv)` → `gene expression omnibus`
2. **PMID 24767513**: Change `t4.0` → Extract proper name from title (Medicago-related)
3. **PMID 33590862**: Change `org` → Extract proper name from title

### Medium Priority

4. Expand 2-letter acronyms (TO, IM, EQ, AX, BR, PX) to full names
5. Review GXB and COSMIC variants for consistency
6. Standardize parenthetical format across similar resources

### Low Priority (Review Needed)

7. Review all HAS_BRACKETS cases to determine if brackets add value
8. Consider policy for when to use full names vs. acronyms
9. Document standard format for resource variants

---

## Pattern Detection Statistics

```
Total rows analyzed:        500
Flagged for review:          37 (7.4%)
Clean rows:                 463 (92.6%)

Issue breakdown:
- HAS_BRACKETS:              24 (64.9% of flagged)
- VERY_SHORT:                 8 (21.6% of flagged)
- SHORT_LOWERCASE:            5 (13.5% of flagged)
```

---

## Files Generated

1. **QC Results CSV**: `best_name_qc_rows_1001_1500.csv`
   Contains all 37 flagged entries with suggested fixes

2. **Analysis Script**: `analyze_best_name_qc_1001_1500.py`
   Can be rerun or adapted for other row ranges

3. **This Report**: `best_name_qc_analysis_report_1001_1500.md`
   Comprehensive analysis and recommendations

---

## Next Steps

1. Review the 37 flagged entries in the CSV file
2. Apply high-confidence fixes immediately
3. Make decisions on medium-priority items
4. Consider developing naming guidelines for future entries
5. Run similar analysis on other row ranges to identify global patterns

---

**Analysis completed successfully.**
