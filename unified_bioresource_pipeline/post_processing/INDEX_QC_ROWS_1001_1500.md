# Best Name Quality Control - Index for Rows 1001-1500

## Quick Navigation

### 🎯 Start Here
- **[QUICK_SUMMARY.txt](QUICK_SUMMARY.txt)** - Visual overview with boxes and charts
- **[QC_ANALYSIS_COMPLETE_1001_1500.md](QC_ANALYSIS_COMPLETE_1001_1500.md)** - Complete analysis summary

### 📊 Detailed Analysis
- **[results/best_name_qc_rows_1001_1500.csv](results/best_name_qc_rows_1001_1500.csv)** - All 37 flagged entries (CSV format)
- **[results/best_name_qc_analysis_report_1001_1500.md](results/best_name_qc_analysis_report_1001_1500.md)** - Comprehensive markdown report
- **[results/best_name_qc_summary.txt](results/best_name_qc_summary.txt)** - Text-based summary

### 🔧 Tools
- **[analyze_best_name_qc_1001_1500.py](analyze_best_name_qc_1001_1500.py)** - Python analysis script (reusable)

---

## What Was Analyzed

**Input File:** `/Users/warren/development/GBC/inventory_2022/unified_bioresource_pipeline/results/2025-12-01-104909-sa4r9/finalization/final_inventory.csv`

**Row Range:** 1001-1500 (500 rows total, excluding header)

**Columns Analyzed:**
- `best_name` (primary focus)
- `paper_titles` (for context)
- `extracted_url` (for domain clues)
- `best_common` (alternative name)
- `best_full` (alternative name)
- `ID` (PMID)

---

## Detection Patterns Used

1. **EMPTY** - best_name is empty/null/whitespace
2. **NUMERIC_ONLY** - Names that are just numbers (e.g., "265")
3. **VERY_SHORT** - 1-2 character names (e.g., "GO", "TO")
4. **SHORT_LOWERCASE** - 3-4 char all-lowercase generic words (e.g., "org", "data")
5. **HAS_BRACKETS** - Names containing parentheses (analyzed for appropriateness)
6. **SUSPICIOUS_CHARS** - HTML tags, pipes, special characters
7. **WRONG_EXTRACTION** - Name clearly doesn't match title/URL context

---

## Results at a Glance

```
Total Analyzed:    500 rows
Flagged:            37 rows (7.4%)
Clean:             463 rows (92.6%)

Issue Breakdown:
  HAS_BRACKETS:      24 (64.9% of flagged)
  VERY_SHORT:         8 (21.6% of flagged)
  SHORT_LOWERCASE:    5 (13.5% of flagged)
```

---

## Top 3 Critical Findings

### 1. Version Number as Name (PRIORITY 1)
**PMID:** 24767513
**Current:** `t4.0`
**Issue:** Software version number used instead of resource name
**Action:** Extract actual resource name from paper

### 2. Generic Domain Suffix (PRIORITY 2)
**PMID:** 33590862
**Current:** `org`
**Issue:** Domain suffix, not a resource name
**Action:** Use "long-read-tools" or extract from title

### 3. High-Confidence Fix Available (PRIORITY 3)
**PMID:** 27134731
**Current:** `GEO (hiv)`
**Suggested:** `gene expression omnibus`
**Confidence:** HIGH (both best_common and best_full agree)
**Action:** Apply this fix immediately

---

## Notable Patterns

### Gene Ontology (3 occurrences)
- PMIDs: 27899567, 30395331, 25428369
- All use ultra-short acronym "GO"
- Decision needed: Keep acronym or expand to "Gene Ontology"?

### GXB Resource Family (5 variants)
- GXB (breastcancer), GXB (ige), GXB (ivf), GXB (monocyte), GXB (pid)
- Status: **KEEP** - Brackets provide essential disambiguation

### COSMIC Variants (2 cases)
- COSMIC (cr10), COSMIC (score)
- Status: **REVIEW** - Naming convention needs standardization

### 2-Letter Acronyms (6 cases)
- TO, IM, EQ, AX, BR, PX
- Status: **EXPAND** - Too short, lack context

---

## File Descriptions

### Main Output: best_name_qc_rows_1001_1500.csv

**Columns:**
- `pmid` - PubMed ID
- `current_best_name` - Current name in database
- `issue_category` - Type(s) of issues detected (pipe-separated)
- `evidence_from_title` - Clues extracted from paper title
- `evidence_from_url` - Clues extracted from resource URL
- `best_common` - Alternative from best_common column
- `best_full` - Alternative from best_full column
- `suggested_name` - Recommended fix
- `confidence` - HIGH, MEDIUM, or LOW
- `notes` - Explanation of suggestion

**Format:** CSV (comma-separated)
**Encoding:** UTF-8
**Rows:** 38 (37 data + 1 header)

### Analysis Script: analyze_best_name_qc_1001_1500.py

**Language:** Python 3
**Dependencies:** Standard library only (csv, re, pathlib, collections)
**Can be modified to:**
- Analyze different row ranges (change offset/limit)
- Add new detection patterns
- Adjust confidence scoring
- Change output format

**Usage:**
```bash
python3 analyze_best_name_qc_1001_1500.py
```

---

## Recommendations by Priority

### Immediate (Today)
- [ ] Fix PMID 24767513: `t4.0` → proper resource name
- [ ] Fix PMID 33590862: `org` → proper resource name
- [ ] Fix PMID 27134731: `GEO (hiv)` → `gene expression omnibus`

### Short Term (This Week)
- [ ] Standardize Gene Ontology references (GO vs. full name)
- [ ] Expand 6 two-letter acronyms to full names
- [ ] Review COSMIC and SEEK naming consistency

### Medium Term (This Month)
- [ ] Create naming guidelines for parenthetical disambiguation
- [ ] Establish acronym usage policy
- [ ] Review all "Database (...)" patterns

### Long Term
- [ ] Implement automated QC for new entries
- [ ] Document resource families (GXB, COSMIC, etc.)
- [ ] Establish version/variant naming standards

---

## Quality Assessment

**Overall Grade:** A- (92.6% clean)

**Strengths:**
- Excellent overall quality
- Consistent capitalization
- Meaningful use of disambiguation
- Good handling of complex names

**Weaknesses:**
- A few overly generic names (org, database)
- One version number used as name (t4.0)
- Some ultra-short acronyms need expansion
- Minor inconsistencies in similar resources

---

## How to Use These Files

1. **For Quick Overview:** Read QUICK_SUMMARY.txt
2. **For Action Items:** Check QC_ANALYSIS_COMPLETE_1001_1500.md
3. **For Detailed Review:** Open best_name_qc_rows_1001_1500.csv in Excel/spreadsheet
4. **For Full Context:** Read best_name_qc_analysis_report_1001_1500.md
5. **To Analyze More Rows:** Modify and run analyze_best_name_qc_1001_1500.py

---

## Next Steps

1. Review the 37 flagged entries in the CSV
2. Apply the 3 high-priority fixes
3. Make policy decisions on:
   - Gene Ontology acronym usage
   - Parenthetical disambiguation standards
   - Acronym expansion rules
4. Consider running analysis on other row ranges:
   - Rows 1-500
   - Rows 501-1000
   - Rows 1501-2000
   - etc.

---

## Contact Information

**Analysis Date:** 2025-12-01
**Analyst:** Automated QC Script
**Row Range:** 1001-1500
**Total Flagged:** 37 entries

For questions or to request additional analysis, reference this index file.

---

**Status:** ✅ ANALYSIS COMPLETE
