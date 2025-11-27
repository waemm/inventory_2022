# URL Extraction Review - Document Index

**Review Date**: 2025-11-27
**Working Directory**: `/Users/warren/development/GBC/inventory_2022/false_positive_analysis`
**Input File**: `novel_fulltext_url_results.csv` (1,108 papers)

---

## Quick Start

**New to this review?** Start here:
1. Read: `REVIEW_SUMMARY.txt` (2-minute overview)
2. Review: `CRITICAL_FALSE_POSITIVES.md` (29 critical cases)
3. Read: `CODE_REVIEW_URL_EXTRACTION.md` (comprehensive technical review)

**Need the data?**
- All issues: `review_extraction_issues.csv` (383 flagged cases)
- Summary stats: `review_extraction_summary.md`

---

## Document Guide

### Executive Summaries

| File | Purpose | Size | Read Time |
|------|---------|------|-----------|
| `REVIEW_SUMMARY.txt` | Quick overview with key statistics | 2.8K | 2 min |
| `CRITICAL_FALSE_POSITIVES.md` | Focus on 29 false positive cases | 5.1K | 5 min |

### Detailed Analysis

| File | Purpose | Size | Read Time |
|------|---------|------|-----------|
| `CODE_REVIEW_URL_EXTRACTION.md` | Comprehensive code review with recommendations | 14K | 15 min |
| `review_extraction_summary.md` | Statistical analysis with examples by issue type | 5.5K | 8 min |

### Data Files

| File | Purpose | Records | Format |
|------|---------|---------|--------|
| `review_extraction_issues.csv` | All flagged issues ready for manual review | 383 | CSV |
| `novel_fulltext_url_results.csv` | Original input data | 1,108 | CSV |

---

## Issue Categories Explained

### 1. FALSE_POSITIVE_URL (29 cases, 4.6%)
**Severity**: CRITICAL

Papers where the script found a **reference database URL** (NCBI, EBI, KEGG, etc.) instead of the actual database being announced.

**Why critical**: These are WRONG URLs that will mislead downstream analyses.

**Examples**:
- PMID 33767203 (NLM-Chem) → Found NCBI URL with score 73
- PMID 34181736 (CROssBAR) → Found EBI URL with score 73

**File**: `CRITICAL_FALSE_POSITIVES.md` has complete analysis

**Action**: Manual review required to find correct URLs

---

### 2. LOW_SCORE (152 cases, 24.1%)
**Severity**: MEDIUM-HIGH

URLs found with very low confidence scores (<20), suggesting weak or possibly incorrect matches.

**Statistics**:
- Score range: 0-18
- 44 cases have scores ≤5 (essentially random)

**Examples**:
- PMID 30788499 (FairBase) → Score: 0
- PMID 28556827 (RiceAtlas) → Score: 5

**Action**: Manual review or discard these results

---

### 3. DEAD_HIGH_SCORE (202 cases, 32.0%)
**Severity**: MEDIUM

URLs that score well (≥30) but are no longer accessible.

**Statistics**:
- Score range: 50-76
- Mean score: 62.5

**Why medium severity**: URLs are likely CORRECT but databases are offline.

**Examples**:
- PMID 31169290 (ResMarkerDB) → Score: 76
- PMID 32024829 (ProtCID) → Score: 73

**Action**:
- Check Internet Archive for archived versions
- Look for updated URLs in citing papers
- Re-check periodically (may be temporary outages)

---

## Key Findings

### Overall Quality Assessment

```
Total papers: 1,108
URLs found: 631 (56.9%)
Issues flagged: 383 (60.7% of URLs found)

Estimated quality URLs: ~248 (39.3% of URLs found)
```

**Conclusion**: Only ~39% of extracted URLs are reliable enough for automated use.

### Most Critical Problems

1. **No reference URL filtering** (29 false positives)
   - Script doesn't distinguish between reference citations and the announced database
   - Some false positives have very high scores (up to 73)

2. **Weak scoring algorithm** (152 low-score cases)
   - Too many results with very low confidence
   - Generic keyword matching not specific enough

3. **Dead databases** (202 cases)
   - Nearly 1/3 of databases are no longer accessible
   - Need strategy for archived/moved resources

### Success Patterns

What works well:
- Title matching (when using specific keywords)
- URL liveness checking
- Comprehensive output with all details preserved

What needs improvement:
- Reference URL filtering (critical)
- Context analysis weighting
- Minimum score thresholds
- Multi-source validation

---

## Recommendations Summary

### Priority 0 (Critical - Do First)

1. **Manual review of 29 false positives**
   - Use: `review_extraction_issues.csv` filtered by `FALSE_POSITIVE_URL`
   - Find correct URLs for each paper
   - Document where correct URLs were found

2. **Implement reference URL blacklist**
   - Filter out NCBI, EBI, KEGG, UniProt, etc. before scoring
   - Prevents future false positives

3. **Raise minimum score threshold**
   - Current: accepting any score ≥0
   - Recommended: require score ≥25 for automated use
   - Score 20-25: flag for manual review

### Priority 1 (High - Do Soon)

4. **Cross-validate with abstracts**
   - Extract URLs from abstracts
   - Boost scores when full-text URL matches abstract

5. **Improve context analysis**
   - Add heavy weight (+30-50 points) for "available at" phrases
   - Penalize URLs in references/bibliography sections

6. **Return top 3 candidates instead of just "best"**
   - Allows human review of alternatives
   - Reduces impact of scoring errors

### Priority 2 (Nice to Have)

7. Integrate with bio.tools API for validation
8. Machine learning-based scoring model
9. Citation network analysis for URL validation
10. Periodic re-checking of dead URLs

---

## How to Use These Files

### For Manual Review Work

1. Open: `review_extraction_issues.csv`
2. Filter by: `issue_type == "FALSE_POSITIVE_URL"`
3. For each row:
   - Read the paper (use PMID to fetch from PubMed)
   - Find the correct database URL
   - Update the results file
4. Document findings and patterns

### For Code Improvements

1. Read: `CODE_REVIEW_URL_EXTRACTION.md` (section: "Recommendations")
2. Implement reference URL filtering first (highest impact)
3. Test on the 29 known false positives
4. Run on full dataset and compare results
5. Iterate on scoring improvements

### For Reporting

1. Use: `REVIEW_SUMMARY.txt` for stakeholder updates
2. Use: `CRITICAL_FALSE_POSITIVES.md` for focus on critical issues
3. Use: `CODE_REVIEW_URL_EXTRACTION.md` for technical discussions

---

## Statistics at a Glance

| Metric | Value |
|--------|-------|
| Total papers analyzed | 1,108 |
| Papers with URLs found | 631 (56.9%) |
| High-quality URLs (estimated) | 248 (39.3% of URLs) |
| Issues flagged | 383 (60.7% of URLs) |
| Critical false positives | 29 (4.6% of URLs) |
| Low-confidence results | 152 (24.1% of URLs) |
| Dead URLs (likely correct) | 202 (32.0% of URLs) |

### False Positive Breakdown by Domain

| Domain Type | Count | Examples |
|-------------|-------|----------|
| NCBI/GenBank | 7 | ncbi.nlm.nih.gov, genbank |
| EBI | 7 | ebi.ac.uk, 1000genomes.ebi.ac.uk |
| CRAN/Bioconductor | 5 | cran.r-project.org, bioconductor.org |
| Other references | 10 | KEGG, UniProt, OMIM, STRING, etc. |

---

## Tools and Scripts

### Analysis Script
- `analyze_url_extraction.py` - Python script that generated this review
- Can be re-run on updated data: `python analyze_url_extraction.py`

### Dependencies
- pandas
- json
- re (regex)

---

## Next Steps

1. **Immediate** (this week):
   - Review all 29 false positives
   - Implement reference URL blacklist
   - Test on known false positives

2. **Short-term** (next 2 weeks):
   - Improve scoring algorithm
   - Add abstract cross-validation
   - Raise minimum score threshold

3. **Long-term** (next month):
   - Integrate with bioresource registries
   - Implement ML-based scoring
   - Build validation pipeline

**Estimated effort**: 2-4 days of development to fix major issues

**Expected improvement**: From ~39% precision to >80% precision

---

## Contact & Support

**Questions about this review?**
- All files are in: `/Users/warren/development/GBC/inventory_2022/false_positive_analysis/`
- Start with: `REVIEW_SUMMARY.txt` or `CRITICAL_FALSE_POSITIVES.md`

**Need help with specific cases?**
- See: `review_extraction_issues.csv` for complete data
- See: `CODE_REVIEW_URL_EXTRACTION.md` for technical details

**Ready to fix the code?**
- See: `CODE_REVIEW_URL_EXTRACTION.md` (sections: "Recommendations" and "Testing")
- Prioritize: Reference URL filtering (highest impact)

---

**Review completed**: 2025-11-27
**Analyst**: Claude Code Review System
**Status**: Ready for action
