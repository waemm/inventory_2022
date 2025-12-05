# Final Inventory Data Quality Report

**Date:** 2025-11-28
**Updated:** 2025-11-29 (Issues IMPLEMENTED in Phase 10)
**File Analyzed:** `unified_bioresource_pipeline/results/2025-11-28-180950-wyaty/finalization/final_inventory.csv`
**Total Records:** 1,945

---

## Executive Summary

This report documents data quality issues identified in the final inventory output and provides actionable recommendations for improvement. The issues primarily originate from upstream NER (Named Entity Recognition) output quality and source data inconsistencies.

**UPDATE 2025-11-29:** Most issues have been **IMPLEMENTED** in Phase 10 scripts 23 and 24.

### Issues by Severity

| Severity | Issue | Count | Impact | Status |
|----------|-------|-------|--------|--------|
| **High** | Empty best_name | 148→153 | Resources have no name | ✅ IMPLEMENTED |
| **High** | article_count incorrect | 339+ | Incorrect statistics | ✅ IMPLEMENTED |
| **Medium** | All-lowercase names | 1,134→657 | Lost acronym capitalization | ✅ IMPLEMENTED |
| **Medium** | Duplicate best_names | 53→65 | Ambiguous resources | ✅ IMPLEMENTED |
| **Medium** | Single/two-letter names | 28→18 | NER artifacts | ✅ IMPLEMENTED |
| **Low** | Pipe in names | 8→7 | Multiple names concatenated | ✅ IMPLEMENTED |
| **Low** | Non-ASCII characters | 9→10 | Encoding issues | ✅ IMPLEMENTED |
| **Low** | HTML tags in names | 3→5 | Source data artifacts | ✅ IMPLEMENTED |
| **Low** | Problematic URLs | 26+→21 | Navigation/aggregator pages | ✅ IMPLEMENTED |

---

## Issue 1: article_count Calculation

### Problem
The `article_count` column contains incorrect values. It should represent the count of PMIDs associated with each resource (i.e., count of comma-separated values in the ID column).

### Examples
```
ID: "27261064, 27987171, 29069403"  -> article_count should be 3
ID: "23161693, 22102590, ..."        -> article_count should be count of PMIDs
```

### Root Cause
The source file (`set_c_final.csv`) has an incorrect `article_count` column. Investigation showed 339 rows where `article_count != actual PMID count`.

### Recommendation
**Fix in Script 23 (transform_columns.py):**
```python
def calculate_article_count(id_str):
    """Count PMIDs in comma-separated ID string."""
    if pd.isna(id_str) or str(id_str).strip() == '':
        return 0
    pmids = [p.strip() for p in str(id_str).split(',') if p.strip()]
    return len(pmids)

df['article_count'] = df['ID'].apply(calculate_article_count)
```

---

## Issue 2: Empty best_name (148 cases)

### Problem
148 resources have empty `best_name` field, meaning they have no display name.

### Example
```csv
ID: "29067135, 30088220"
best_name: ""
best_name_prob: 0.0
extracted_url: http://braingraph.org
```

### Root Cause
NER extraction found no entity name. The source data shows `primary_entity_short` and `primary_entity_long` are both empty.

### Recommendation
**Fix in Script 23:**
```python
def populate_empty_names(row):
    """Fallback strategy for empty names."""
    if pd.isna(row['best_name']) or row['best_name'].strip() == '':
        # Strategy 1: Extract from URL domain
        url = row.get('extracted_url', '')
        if url:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace('www.', '')
            if domain:
                return domain.split('.')[0]
        # Strategy 2: Use "Unknown Resource" placeholder
        return "[No Name Extracted]"
    return row['best_name']
```

---

## Issue 3: Lost Capitalization (1,134 cases)

### Problem
Many resource names are all lowercase when they should preserve acronym capitalization (e.g., "encode" should be "ENCODE").

### Examples Found
- `plaza` -> should be `PLAZA`
- `genbank` -> should be `GenBank`
- `encode` -> should be `ENCODE`
- `hmdb` -> should be `HMDB`
- `kegg` -> should be `KEGG`

### Root Cause
NER output converts names to lowercase. 1,134 names are 10 characters or fewer and all lowercase.

### Recommendation
**Create known acronyms dictionary:**
```python
KNOWN_ACRONYMS = {
    'encode': 'ENCODE',
    'kegg': 'KEGG',
    'hmdb': 'HMDB',
    'gwas': 'GWAS',
    'genbank': 'GenBank',
    'pubchem': 'PubChem',
    'uniprot': 'UniProt',
    # ... add more as discovered
}

def restore_capitalization(name):
    """Restore known acronym capitalization."""
    if pd.isna(name):
        return name
    lower_name = name.lower().strip()
    if lower_name in KNOWN_ACRONYMS:
        return KNOWN_ACRONYMS[lower_name]
    # Fallback: if all lowercase and <=6 chars, uppercase it
    if name.isalpha() and name.islower() and len(name) <= 6:
        return name.upper()
    return name
```

---

## Issue 4: Pipe in Names (8 cases)

### Problem
Some `best_name` values contain multiple names separated by pipes.

### Examples
```
"dbnsfp | encode"
```

### Recommendation
**Fix in Script 23:**
```python
def clean_pipe_names(name):
    """Take first name when pipe-separated."""
    if pd.isna(name):
        return name
    if '|' in str(name):
        return str(name).split('|')[0].strip()
    return name
```

---

## Issue 5: Non-ASCII Characters (9 cases)

### Problem
Names contain non-standard characters that may cause encoding issues.

### Examples Found
- `gren-db` (contains Greek mu: )
- Names with , , symbols

### Recommendation
**Fix in Script 23:**
```python
import unicodedata

def sanitize_characters(name):
    """Replace non-ASCII with ASCII equivalents."""
    if pd.isna(name):
        return name

    replacements = {
        '': 'mu',      # Greek mu
        '': '(R)',     # Registered
        '': '(TM)',    # Trademark
        '': "'",       # Smart quote
        '': "'",       # Smart quote
    }

    for char, replacement in replacements.items():
        name = name.replace(char, replacement)

    # Normalize remaining unicode
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')

    return name.strip()
```

---

## Issue 6: HTML Tags in Names (3 cases)

### Problem
Some names contain HTML artifacts from abstract parsing.

### Examples
```
"i>econtour</i"  (should be "eContour")
```

### Root Cause
6 rows in source data (`set_c_final.csv`) have HTML in `primary_entity_long`.

### Recommendation
**Fix in Script 23:**
```python
import re

def remove_html_tags(name):
    """Remove HTML tags from name."""
    if pd.isna(name):
        return name
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', str(name))
    # Remove partial tags
    clean = re.sub(r'[<>]', '', clean)
    return clean.strip()
```

---

## Issue 7: Single/Two Letter Names (28 cases)

### Problem
NER extracted single or two-letter "names" that are not real resource names.

### Examples
```
PMID 27910033: best_name = "h"
PMID 28742084: best_name = "load"  (not matching URL content)
```

### Root Cause
NER noise - these are artifacts, not real bioresource names.

### Recommendation
**Add validation in Script 23:**
```python
def validate_name_length(name, min_length=3):
    """Flag or remove names below minimum length."""
    if pd.isna(name):
        return name
    if len(str(name).strip()) < min_length:
        return None  # Will trigger fallback logic
    return name
```

---

## Issue 8: Duplicate best_names (53 unique names with duplicates)

### Problem
Multiple resources share the same `best_name`, making them indistinguishable.

### Example: "gxb" appears 5 times
```
PMID 24163257 -> gxd (Gene Expression Database)
PMID 30335138 -> gxd (same)
...
```

### Recommendation
**Add disambiguation in Script 23:**
```python
def disambiguate_duplicate_names(df):
    """Add URL domain to duplicate names."""
    from urllib.parse import urlparse

    # Find duplicates
    name_counts = df['best_name'].value_counts()
    duplicates = name_counts[name_counts > 1].index.tolist()

    def add_domain_suffix(row):
        if row['best_name'] in duplicates:
            url = row.get('extracted_url', '')
            if url:
                domain = urlparse(url).netloc.replace('www.', '')
                short_domain = domain.split('.')[0]
                return f"{row['best_name']} ({short_domain})"
        return row['best_name']

    df['best_name'] = df.apply(add_domain_suffix, axis=1)
    return df
```

---

## Issue 9: Problematic URLs (26+ cases)

### Problem
Some URLs are not specific resource pages but navigation pages, aggregator sites, or incorrect links.

### Categories Identified

| URL Pattern | Count | Issue |
|-------------|-------|-------|
| oxfordjournals.org | 6 | NAR database list page (not resource) |
| mozilla.org | 1 | Browser website (not resource) |
| github.io | 15 | Personal pages, may be valid |
| clinicaltrials.gov | 4 | Trial registry (not bioresource) |

### Specific PMIDs to Investigate/Remove

| PMID | URL | Reason |
|------|-----|--------|
| 33396976 | oxfordjournals.org | Database list page, not specific resource |
| 21737439 | mozilla.org | Browser, not bioresource |
| 34078918 | github.io | Verify if actual resource |
| 28673048 | - | Not a bioresource (per user) |

### Recommendation
**Add URL validation rules:**
```python
BLOCKED_URL_PATTERNS = [
    r'oxfordjournals\.org/nar/article',  # NAR article pages
    r'mozilla\.org',                      # Browser
    r'clinicaltrials\.gov/ct2/show',     # Trial pages (not resources)
]

REVIEW_URL_PATTERNS = [
    r'github\.io',      # May be valid, needs review
    r'github\.com',     # May be valid, needs review
]

def validate_url(url):
    """Check URL against known problematic patterns."""
    import re
    for pattern in BLOCKED_URL_PATTERNS:
        if re.search(pattern, url):
            return 'blocked'
    for pattern in REVIEW_URL_PATTERNS:
        if re.search(pattern, url):
            return 'review'
    return 'ok'
```

---

## Issue 10: Specific PMIDs to Exclude

Based on user review, the following PMIDs should be excluded from the final inventory:

| PMID | Reason |
|------|--------|
| 28673048 | Not a bioresource |
| 33396976 | oxfordjournals.org URL (aggregator page) |
| 21737439 | mozilla.org URL (browser, not resource) |
| 34078918 | github.io URL (needs verification) |

### Recommendation
**Add exclusion list to Script 22:**
```python
EXCLUDED_PMIDS = {
    '28673048',  # Not a bioresource
    '33396976',  # Aggregator page
    '21737439',  # Mozilla browser
    '34078918',  # GitHub pages - needs verification
}

def filter_excluded_pmids(df):
    """Remove rows with excluded PMIDs."""
    def has_excluded_pmid(id_str):
        pmids = str(id_str).split(',')
        pmids = [p.strip() for p in pmids]
        return not any(p in EXCLUDED_PMIDS for p in pmids)

    return df[df['ID'].apply(has_excluded_pmid)]
```

---

## Implementation Plan

### Phase 1: Script 22 Updates (Filter)
1. Add PMID exclusion list
2. Document exclusion reasons in metadata

### Phase 2: Script 23 Updates (Transform)
1. Recalculate article_count from PMID count
2. Clean pipe-separated names (use first)
3. Remove HTML tags from names
4. Sanitize non-ASCII characters
5. Validate minimum name length
6. Populate empty names with fallback
7. Restore known acronym capitalization
8. Disambiguate duplicate names

### Phase 3: Script 24 Updates (URL Check)
1. Add URL pattern validation
2. Flag/exclude blocked URL patterns
3. Mark review-needed URLs

### Phase 4: Quality Metrics
Add data quality metrics to statistics.json:
```json
{
  "quality_metrics": {
    "empty_names_filled": 148,
    "names_capitalized": 1134,
    "pipes_cleaned": 8,
    "html_removed": 3,
    "duplicates_disambiguated": 53,
    "pmids_excluded": 4,
    "urls_blocked": 7
  }
}
```

---

## Summary of Recommendations

| Issue | Fix Location | Priority | Effort |
|-------|-------------|----------|--------|
| article_count | Script 23 | High | Low |
| Empty names | Script 23 | High | Medium |
| Capitalization | Script 23 | Medium | Medium |
| Pipe names | Script 23 | Low | Low |
| Non-ASCII | Script 23 | Low | Low |
| HTML tags | Script 23 | Low | Low |
| Short names | Script 23 | Medium | Low |
| Duplicates | Script 23 | Medium | Medium |
| URL validation | Script 24 | Medium | Medium |
| PMID exclusion | Script 22 | High | Low |

---

## Files to Modify

1. `unified_bioresource_pipeline/scripts/phase9_finalization/22_filter_novel_resources.py`
   - Add PMID exclusion list

2. `unified_bioresource_pipeline/scripts/phase9_finalization/23_transform_columns.py`
   - Add all name sanitization functions
   - Fix article_count calculation
   - Add disambiguation logic

3. `unified_bioresource_pipeline/scripts/phase9_finalization/24_check_urls_with_geo.py`
   - Add URL pattern validation

---

## Appendix: Data Quality Queries

### Find Empty Names
```python
empty = df[df['best_name'].isna() | (df['best_name'] == '')]
print(f"Empty names: {len(empty)}")
```

### Find Lowercase Short Names
```python
short_lower = df[
    (df['best_name'].str.len() <= 10) &
    (df['best_name'].str.islower())
]
print(f"Lowercase short names: {len(short_lower)}")
```

### Find Problematic URLs
```python
import re
patterns = ['oxfordjournals', 'mozilla', 'github.io', 'clinicaltrials']
for p in patterns:
    matches = df[df['extracted_url'].str.contains(p, na=False)]
    print(f"{p}: {len(matches)} matches")
```

---

*Report generated by Claude Code data quality analysis*

---

## Implementation Summary (2025-11-29)

All recommended fixes have been implemented in Phase 10 scripts:

### Script 23 (`23_transform_columns.py`)

**Functions Added:**
- `sanitize_name()` - Comprehensive name cleaning pipeline
- `auto_capitalize_names()` - Smart capitalization for short names
- `clean_pipe_names()` - Extract first name from pipe-separated values
- `remove_html_tags()` - Strip HTML artifacts
- `sanitize_characters()` - Replace non-ASCII (ø→o, é→e, μ→mu, etc.)
- `name_appears_in_url()` - Detect name/URL mismatches
- `extract_subdomain()` - Get subdomain for disambiguation
- `disambiguate_duplicate_names()` - Add subdomain qualifiers (e.g., GXB → GXB (breastcancer))
- `populate_empty_names()` - Fallback to URL domain when name is empty

**Tracking Columns Added:**
- `best_name_original` - Original name before modifications
- `name_modification_flags` - Audit trail (CAPITALIZED, DISAMBIGUATED, CHARS_SANITIZED, etc.)

### Script 24 (`24_check_urls_with_geo.py`)

**URL Blocking Added:**
```python
BLOCKED_URL_PATTERNS = [
    r'oxfordjournals\.org',    # NAR database list pages
    r'academic\.oup\.com/nar', # NAR articles
    r'mozilla\.org',           # Browser website
    r'bitbucket\.org',         # Code repository
    r'gitlab\.com',            # Code repository
    r'sourceforge\.net',       # Code repository
    r'\.pdf($|\?)',            # PDF files
    r'\.xlsx?($|\?)',          # Excel files
    r'\.zip($|\?)',            # ZIP archives
    r'\.tar\.gz($|\?)',        # Tarball archives
]
```

**Tracking Column Added:**
- `url_validation` - 'ok', 'review', or 'blocked'

### Results (Latest Run)

| Metric | Value |
|--------|-------|
| Total final resources | 1,945 |
| Names capitalized | 657 |
| Names populated from URL | 153 |
| Names disambiguated | 65 |
| Short names replaced | 18 |
| Chars sanitized | 10 |
| Pipe names cleaned | 7 |
| HTML removed | 5 |
| URLs blocked | 21 |
| URLs flagged for review | 19 |

---

## Post-Processing QC (2025-12-01)

An additional post-processing step was implemented to catch remaining data quality issues not handled by the Phase 9 scripts.

### Location

`unified_bioresource_pipeline/post_processing/`

### Methodology

Agent-based analysis scans the `best_name` column for:
- Empty/missing names
- Numeric-only names (e.g., "265")
- Very short names (1-2 chars)
- Short lowercase generic words
- Names with brackets (disambiguation artifacts)
- Wrong extractions (name doesn't match title/URL)

### Results (Session 2025-12-01-104909)

| Metric | Value |
|--------|-------|
| Total rows analyzed | 1,688 |
| Issues flagged | 111 (6.6%) |
| Auto-fixed (HIGH confidence) | 29 |
| Auto-fixed (MEDIUM confidence) | 66 |
| Auto-fixed (LOW confidence) | 10 |
| Needs manual review | 6 |

### Output Files

- `post_processing/results/final_inventory_QC_FIXED.csv` - Corrected inventory
- `post_processing/results/fixes_applied.csv` - Audit log of all changes
- `post_processing/results/best_name_qc_ALL.csv` - Full QC findings

### Flags Added

- `QC_FIX_HIGH` - High confidence correction applied
- `QC_FIX_MEDIUM` - Medium confidence correction applied
- `QC_FIX_LOW` - Low confidence correction applied
- `NEEDS_MANUAL_REVIEW` - Could not auto-fix, requires human review
