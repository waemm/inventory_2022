# Full Text URL Extraction Plan

**Goal**: Create a standalone script to extract URLs from EPMC full text for bioresources that were marked as false positives due to missing URLs.

**Input**: `fp_bioresources_need_url_refined.csv` (37 papers marked `is_bioresource=Y`)

---

## Architecture Overview

```
fp_bioresources_need_url_refined.csv (37 papers with is_bioresource=Y)
          │
          ▼
┌─────────────────────────────────┐
│  1. EPMC Full Text Retriever    │
│  - Check PMC availability       │
│  - Fetch full text XML/HTML     │
│  - Rate limiting (1 req/sec)    │
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  2. URL Extraction              │
│  - Regex patterns (from 11_)    │
│  - Context extraction           │
│  - URL scoring/filtering        │
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  3. URL Validation              │
│  - HTTP status check            │
│  - Multi-threaded (from 02_)    │
│  - Bioresource indicator scan   │
└─────────────────────────────────┘
          │
          ▼
fulltext_url_results.csv
```

---

## Implementation Tasks

### Task 1: EPMC Full Text Fetcher (NEW)

**Purpose**: Fetch full text from Europe PMC for papers with available full text.

**API Endpoints**:
- Full text: `https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{id}/fullTextXML`
- Example: `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC/PMC7889865/fullTextXML`
- Annotations: `https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds`

**Logic**:
1. For each PMID, check if PMC ID exists (use metadata endpoint)
2. If PMC ID exists, fetch full text XML
3. Parse XML to extract all text content
4. Handle rate limiting (1 request/second recommended)

**Code reuse**: Rate limiting pattern from `src/fetch_enhanced_metadata.py`

### Task 2: URL Extraction Module (REUSE)

**Source**: `pipeline_synthesis_2025-11-18/scripts/11_extract_urls.py`

**Components to reuse**:
- `extract_urls()` function (lines 89-149) - comprehensive regex patterns
- `EXCLUDE_DOMAINS` list (lines 38-63) - filter non-bioresource URLs
- `RESOURCE_KEYWORDS` list (lines 66-71) - score URLs
- `score_url()` function (lines 213-249) - URL scoring system
- `get_url_context()` function (lines 188-211) - context extraction

**Adaptation needed**:
- Accept full text instead of abstract
- Handle longer text (potentially multiple sections)

### Task 3: URL Validation Module (REUSE)

**Source**: `bioresource_url_scanner/scripts/02_scan_urls.py`

**Components to reuse**:
- `DomainRateLimiter` class (lines 95-118) - thread-safe rate limiting
- `BioresourceScanner.scan_url()` method (lines 134-216) - HTTP validation
- `INDICATOR_SCORES` dictionary (lines 42-92) - bioresource indicators

**Adaptation needed**:
- Simpler output (just live/dead status + error message)
- Optional: basic indicator scan for high-confidence results

---

## Script Structure

```python
#!/usr/bin/env python3
"""
extract_urls_from_fulltext.py

Extracts URLs from EPMC full text for bioresources that lack URLs.
"""

# Structure:
# 1. EPMCFullTextFetcher class
#    - get_pmc_id(pmid) -> str or None
#    - fetch_fulltext(pmc_id) -> str or None
#    - Rate limiting

# 2. URLExtractor class (adapted from 11_extract_urls.py)
#    - extract_urls(text) -> list
#    - score_url(url, text) -> float
#    - get_context(text, url) -> str

# 3. URLValidator class (adapted from 02_scan_urls.py)
#    - validate_url(url) -> dict (is_live, status_code, error)

# 4. Main workflow
#    - Load input CSV
#    - For each paper with is_bioresource=Y:
#      a. Fetch full text from EPMC
#      b. Extract URLs from full text
#      c. Validate extracted URLs
#      d. Score and rank URLs
#    - Save results
```

---

## Output Format

**File**: `fulltext_url_results.csv`

| Column | Description |
|--------|-------------|
| pmid | PubMed ID |
| title | Paper title |
| has_fulltext | Whether EPMC full text was available |
| fulltext_source | 'PMC' or 'None' |
| urls_found | All URLs found (pipe-separated) |
| best_url | Highest-scoring URL |
| best_url_score | Score of best URL |
| best_url_context | Text surrounding best URL |
| best_url_is_live | HTTP status check result |
| best_url_status | HTTP status code |
| best_url_error | Error message if validation failed |
| all_url_details | JSON with all URL scores/validation |

---

## Dependencies

**Existing packages** (already in project):
- `pandas` - data handling
- `requests` - HTTP requests
- `beautifulsoup4` / `lxml` - XML parsing
- `tqdm` - progress bars

**No new dependencies required**.

---

## Estimated Complexity

| Component | Effort | Notes |
|-----------|--------|-------|
| EPMC Full Text Fetcher | Medium | New code, but simple API |
| URL Extraction | Low | Mostly copy from 11_extract_urls.py |
| URL Validation | Low | Mostly copy from 02_scan_urls.py |
| Integration | Low | Simple workflow |

**Total**: ~150-200 lines of code

---

## API Rate Limiting Notes

From [Europe PMC REST API](https://europepmc.org/RestfulWebService):
- No hard rate limit published
- Recommended: 1 request per second for batch queries
- Use `sleep(1)` between requests

---

## Execution Plan

1. Create script at `false_positive_analysis/scripts/extract_urls_from_fulltext.py`
2. Run on 37 papers with `is_bioresource=Y`
3. Review results, identify papers with newly found URLs
4. Update classification for papers where URLs were found

---

## Success Criteria

- [ ] Script successfully fetches full text for papers with PMC IDs
- [ ] URLs extracted using proven regex patterns
- [ ] URLs validated with HTTP status check
- [ ] Output CSV has all required columns
- [ ] Results reviewed for false positives needing URL updates
