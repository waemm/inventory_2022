# Best Name Quality Control Analysis - Index

## Analysis Scope: Rows 1501-1688

This directory contains quality control analysis results for the `best_name` column in the final bioresource inventory.

---

## Quick Start

**For immediate action items:** See `best_name_qc_examples.txt`

**For visual overview:** See `best_name_qc_visual_summary.txt`

**For detailed analysis:** See `best_name_qc_summary_report.md`

**For raw data:** See `best_name_qc_rows_1501_1688.csv`

---

## Files in This Analysis

### 1. best_name_qc_rows_1501_1688.csv (8.8K)
**Primary deliverable** - Detailed CSV with all 52 flagged cases

**Columns:**
- `pmid` - PubMed ID(s)
- `current_best_name` - Current value in best_name column
- `issue_category` - Comma-separated list of issues (EMPTY, NUMERIC_ONLY, VERY_SHORT, SHORT_LOWERCASE, HAS_BRACKETS, SUSPICIOUS_CHARS, WRONG_EXTRACTION)
- `evidence_from_title` - Extracted evidence from paper title
- `evidence_from_url` - Extracted evidence from URL
- `best_common` - Value from best_common column (potential alternative)
- `best_full` - Value from best_full column (potential alternative)
- `suggested_name` - Recommended replacement name
- `confidence` - Fix confidence (HIGH/MEDIUM/LOW)
- `notes` - Additional context and reasoning

### 2. best_name_qc_summary_report.md (6.0K)
**Comprehensive analysis report** with:
- Executive summary with statistics
- Issue breakdown by category
- Known problem cases (all 3 found)
- High/medium/low confidence examples
- Pattern identification
- System improvement recommendations

### 3. best_name_qc_examples.txt (2.2K)
**Quick reference** showing:
- Known problem cases
- High confidence fixes (ready to apply)
- Wrong extraction examples
- Manual review queue
- Pattern summary
- Statistics

### 4. best_name_qc_visual_summary.txt (2.5K)
**Visual dashboard** with:
- Bar charts of issue distribution
- Confidence level breakdown
- Known problems detection
- Top patterns
- Actionable recommendations

### 5. BEST_NAME_QC_INDEX.md (this file)
**Navigation guide** for all QC outputs

---

## Key Findings Summary

### Overall Quality
- **189 rows** analyzed (rows 1501-1688 of final inventory)
- **52 rows (27.5%)** flagged with quality issues
- **137 rows (72.5%)** passed quality checks
- **88.5% fixable** (46/52 have suggested corrections)

### Issue Distribution
1. **WRONG_EXTRACTION** - 39 cases (75.0%)
   - Name doesn't match paper title or URL context
   - Often URL domain used instead of actual resource name

2. **HAS_BRACKETS** - 17 cases (32.7%)
   - Contains parentheses (usually URL domain suffix)
   - Example: "GEO (placentalendocrinology)" should be "GEO"

3. **NUMERIC_ONLY** - 1 case (1.9%)
   - Name is just a number: "265"

4. **VERY_SHORT** - 1 case (1.9%)
   - Name is 1-2 characters: "2d"

### Fix Confidence
- **HIGH** (8 cases, 15.4%) - Can auto-apply using best_common
- **MEDIUM** (38 cases, 73.1%) - Needs quick review, suggestions from title
- **LOW** (6 cases, 11.5%) - Needs expert review, no clear alternative

### Known Problems Detection: 100% Success
All 3 user-flagged problem cases were detected:
1. PMID 30999846: "Melanoma (khaos)" → VIGLA-M
2. PMID 34292965: "265" → Manual review needed
3. PMID 21841810: "2d" → Manual review needed

---

## Action Items

### Immediate (HIGH Confidence - 8 cases)
Apply these fixes automatically:
- Strip domain suffixes from well-known databases (GEO, TCGA, PDB, GBIF)
- Use best_common values which are cleaner

### Short-term (MEDIUM Confidence - 38 cases)
Quick human review and batch apply:
- Title-extracted names (uppercase acronyms)
- Domain names that should be resource names (e.g., Covid19dataportal → COVID-19)

### Manual Review Queue (LOW Confidence - 6 cases)
Expert review required:
- PMID 34292965: "265" - no clear database name
- PMID 21841810: "2d" - proteomics map with unclear name
- 4 generic "Database" names - need specific resource identification

---

## System Improvement Recommendations

### Post-processing Rules
1. **Strip domain suffixes:** Remove `(domain)` patterns from names
2. **Prioritize title extraction:** Use uppercase acronyms from titles over URL domains
3. **Validation flags:** Mark numeric-only and very short names during extraction

### Pattern Detection
- Flag when URL domain is used as name but title contains uppercase acronym
- Detect generic terms ("Database", "Repository") as primary names
- Check for bracket contamination in final names

---

## Analysis Methodology

### Detection Patterns
1. **EMPTY**: best_name is empty/null/whitespace
2. **NUMERIC_ONLY**: Names that are just numbers
3. **VERY_SHORT**: 1-2 character names
4. **SHORT_LOWERCASE**: 3-4 char all-lowercase generic words
5. **HAS_BRACKETS**: Names containing parentheses
6. **SUSPICIOUS_CHARS**: HTML tags, pipes, special characters
7. **WRONG_EXTRACTION**: Name clearly doesn't match title/URL context

### Evidence Sources
- **Title analysis:** Extract uppercase acronyms and quoted terms
- **URL analysis:** Extract domain and path components
- **Alternative columns:** Check best_common and best_full for better options

### Confidence Assignment
- **HIGH:** best_common provides clear alternative
- **MEDIUM:** best_full or title extraction provides good alternative
- **LOW:** No clear alternative found, manual review required

---

## Related Analyses

This is part of a series of best_name QC analyses:
- Rows 1-500: `best_name_qc_rows_1_500.csv` (if exists)
- Rows 501-1000: `best_name_qc_rows_501_1000.csv`
- Rows 1001-1500: `best_name_qc_rows_1001_1500.csv`
- **Rows 1501-1688: `best_name_qc_rows_1501_1688.csv` (THIS ANALYSIS)**

---

## Technical Details

**Input File:**
`/Users/warren/development/GBC/inventory_2022/unified_bioresource_pipeline/results/2025-12-01-104909-sa4r9/finalization/final_inventory.csv`

**Analysis Script:**
`/tmp/analyze_best_name_qc.py`

**Output Directory:**
`/Users/warren/development/GBC/inventory_2022/unified_bioresource_pipeline/post_processing/results/`

**Date Generated:** 2025-12-01

**Total File Size:** ~25.5K (all QC outputs for rows 1501-1688)

---

## Contact & Questions

For questions about specific flagged cases, consult the detailed CSV file.

For questions about methodology, see the analysis script or this index file.

For system improvements, see the recommendations section in the summary report.
