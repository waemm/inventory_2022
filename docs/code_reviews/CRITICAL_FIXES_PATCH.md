# CRITICAL FIXES PATCH
## Immediate Fixes for Production Deployment

**Priority:** HIGH
**Estimated Time:** 4-6 hours
**Impact:** Resolves data quality issues for production ML training

---

## FIX 1: Missing PMIDs (496 papers, 2.3%)

### File: `src/query_epmc.py`
### Location: Line 129

### Current Code:
```python
record = {
    # Core fields (original 4)
    'id': paper.get('pmid'),  # Returns None if missing
    'title': paper.get('title'),
    # ... rest of fields
}
```

### Proposed Fix (Option A - Recommended):
```python
# Use fallback IDs: PMID → PMC → DOI → Generate synthetic
def _get_paper_id(paper, page_idx, paper_idx):
    """Extract paper ID with fallbacks"""
    pmid = paper.get('pmid')
    if pmid:
        return str(pmid)

    # Fallback to PMC ID
    pmcid = paper.get('pmcid')
    if pmcid:
        return f"PMC{pmcid}"

    # Fallback to DOI
    doi = paper.get('doi')
    if doi:
        return f"DOI:{doi}"

    # Last resort: synthetic ID
    return f"NOID_{page_idx}_{paper_idx}"

# In clean_results():
for page_idx, page in enumerate(results):
    for paper_idx, paper in enumerate(page.get('resultList', {}).get('result', [])):
        record = {
            'id': _get_paper_id(paper, page_idx, paper_idx),
            # ... rest of fields
        }
```

### Proposed Fix (Option B - Conservative):
```python
# Filter out papers without PMID
for page in results:
    for paper in page.get('resultList', {}).get('result', []):
        # Skip papers without PMID
        if not paper.get('pmid'):
            print(f"Warning: Skipping paper without PMID: {paper.get('title', 'NO TITLE')[:80]}")
            continue

        record = {
            'id': paper.get('pmid'),
            # ... rest of fields
        }
```

### Testing:
```python
# Test with edge cases
test_papers = [
    {'pmid': '12345', 'title': 'Normal paper'},
    {'pmcid': 'PMC67890', 'title': 'Paper with PMC only'},
    {'doi': '10.1234/test', 'title': 'Paper with DOI only'},
    {'title': 'Paper with no IDs'}
]

for i, paper in enumerate(test_papers):
    paper_id = _get_paper_id(paper, 0, i)
    print(f"Paper {i}: ID = {paper_id}")
```

**Recommendation:** Use Option A (fallback IDs) to preserve all papers while maintaining traceability.

---

## FIX 2: Duplicate PMID (1 occurrence)

### File: `src/query_epmc.py`
### Location: `clean_results()` function (line 112)

### Current Code:
```python
def clean_results(results: List[dict]) -> pd.DataFrame:
    import json

    records = []
    for page in results:
        for paper in page.get('resultList').get('result'):
            # Extract metadata...
            record = {...}
            records.append(record)

    return pd.DataFrame(records)
```

### Proposed Fix:
```python
def clean_results(results: List[dict]) -> pd.DataFrame:
    """
    Retrieve enhanced metadata from results of query

    Parameters:
    `results`: JSON-encoded response (nested dictionary)

    Return: Dataframe of results with 20 metadata fields (deduplicated)
    """
    import json

    records = []
    seen_pmids = set()  # Track seen PMIDs to prevent duplicates
    duplicate_count = 0

    for page in results:
        for paper in page.get('resultList', {}).get('result', []):
            pmid = paper.get('pmid')

            # Check for duplicates
            if pmid and pmid in seen_pmids:
                duplicate_count += 1
                print(f"Warning: Duplicate PMID {pmid} found, skipping duplicate")
                continue

            # Track this PMID
            if pmid:
                seen_pmids.add(pmid)

            # Extract all enhanced metadata fields
            record = {
                # ... existing code
            }
            records.append(record)

    if duplicate_count > 0:
        print(f"Total duplicates removed: {duplicate_count}")

    return pd.DataFrame(records)
```

### Testing:
```python
# Test deduplication
test_results = [
    {
        'resultList': {
            'result': [
                {'pmid': '12345', 'title': 'Paper A'},
                {'pmid': '12345', 'title': 'Paper A (duplicate)'},
                {'pmid': '67890', 'title': 'Paper B'},
            ]
        }
    }
]

df = clean_results(test_results)
assert len(df) == 2, "Should have 2 unique papers"
assert list(df['id']) == ['12345', '67890']
```

---

## FIX 3: Author Affiliations (100% missing)

### File: `src/query_epmc.py`
### Location: `_extract_author_affiliations()` function (line 222)

### Current Code:
```python
def _extract_author_affiliations(author_list):
    """Extract author affiliations"""
    if not author_list:
        return None
    authors = author_list.get('author', [])
    if not authors:
        return None
    affiliations = set()
    for author in authors:
        affiliation = author.get('affiliation', '')
        if affiliation:
            affiliations.add(affiliation)
    if affiliations:
        import json
        return json.dumps(list(affiliations))
    return None
```

### Proposed Fix (Robust Multi-Key Extraction):
```python
def _extract_author_affiliations(author_list):
    """
    Extract author affiliations with multiple fallback strategies

    EuropePMC API may return author affiliations in different structures:
    1. authorList → author[] → affiliation (simple string)
    2. authorList → author[] → authorAffiliationDetailsList → authorAffiliation[] → affiliation
    3. authorList → author[] → affiliationInfo → affiliation

    Returns JSON list of unique affiliations or None
    """
    if not author_list:
        return None

    # Try multiple possible keys for author list
    authors = (author_list.get('author') or
               author_list.get('authors') or
               [])

    if not authors:
        return None

    affiliations = set()

    for author in authors:
        affiliation = None

        # Strategy 1: Direct affiliation field (most common)
        affiliation = author.get('affiliation')

        # Strategy 2: Nested in authorAffiliationDetailsList
        if not affiliation:
            affil_details = author.get('authorAffiliationDetailsList', {})
            affil_list = affil_details.get('authorAffiliation', [])
            if affil_list and len(affil_list) > 0:
                affiliation = affil_list[0].get('affiliation')

        # Strategy 3: Nested in affiliationInfo
        if not affiliation:
            affil_info = author.get('affiliationInfo', {})
            affiliation = affil_info.get('affiliation')

        # Add if valid
        if affiliation and isinstance(affiliation, str) and affiliation.strip():
            affiliations.add(affiliation.strip())

    if affiliations:
        import json
        return json.dumps(list(affiliations))

    return None
```

### Diagnostic Code (Run First):
```python
#!/usr/bin/env python3
"""
Diagnostic: Examine actual API response structure for author affiliations
Run this to understand why 100% are missing
"""
import requests
import json

# Query a single paper with known authors
test_pmid = "34599955"  # First paper in dataset

url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=PMID:{test_pmid}&resultType=core&format=json"

response = requests.get(url)
data = response.json()

# Examine structure
paper = data['resultList']['result'][0]

print("=== AUTHOR STRUCTURE DIAGNOSTIC ===")
print(f"\nPaper PMID: {paper.get('pmid')}")
print(f"Paper Title: {paper.get('title', '')[:80]}")

# Check for author list
if 'authorList' in paper:
    print("\n✓ authorList found")
    author_list = paper['authorList']
    print(f"  Keys in authorList: {author_list.keys()}")

    if 'author' in author_list:
        authors = author_list['author']
        print(f"  Number of authors: {len(authors)}")

        # Examine first author structure
        if authors:
            first_author = authors[0]
            print(f"\n  First author keys: {first_author.keys()}")
            print(f"  First author full structure:")
            print(json.dumps(first_author, indent=2))
else:
    print("\n❌ No authorList found")
    print(f"Available top-level keys: {paper.keys()}")

# Save full response for analysis
with open('/Users/warren/development/GBC/inventory_2022/api_response_sample.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\n✓ Full API response saved to: api_response_sample.json")
```

### Action Plan:
1. **Run diagnostic script first** to understand actual API structure
2. **Update extraction function** based on findings
3. **Re-run metadata extraction** if structure is different
4. **Validate** that affiliations are now captured

---

## FIX 4: Error Handling in API Response Parsing

### File: `src/query_epmc.py`
### Location: `clean_results()` function (line 124)

### Current Code:
```python
for page in results:
    for paper in page.get('resultList').get('result'):  # Can throw KeyError
        record = {...}
        records.append(record)
```

### Proposed Fix:
```python
def clean_results(results: List[dict]) -> pd.DataFrame:
    """
    Retrieve enhanced metadata from results of query

    Parameters:
    `results`: JSON-encoded response (nested dictionary)

    Return: Dataframe of results with 20 metadata fields
    """
    import json

    records = []
    seen_pmids = set()
    duplicate_count = 0
    error_count = 0

    for page_idx, page in enumerate(results):
        try:
            # Safe access with defaults
            result_list = page.get('resultList', {})
            papers = result_list.get('result', [])

            if not papers:
                print(f"Warning: Page {page_idx} has no results")
                continue

            for paper_idx, paper in enumerate(papers):
                try:
                    # Check for duplicates
                    pmid = paper.get('pmid')
                    if pmid and pmid in seen_pmids:
                        duplicate_count += 1
                        print(f"Warning: Duplicate PMID {pmid}, skipping")
                        continue

                    if pmid:
                        seen_pmids.add(pmid)

                    # Extract all enhanced metadata fields
                    record = {
                        # Core fields
                        'id': paper.get('pmid'),
                        'title': paper.get('title'),
                        'abstract': paper.get('abstractText'),
                        'publication_date': paper.get('firstPublicationDate'),

                        # Boolean flags
                        'hasDbCrossReferences': paper.get('hasDbCrossReferences'),
                        'hasData': paper.get('hasData'),
                        'hasSuppl': paper.get('hasSuppl'),
                        'isOpenAccess': paper.get('isOpenAccess'),
                        'inPMC': paper.get('inPMC'),
                        'inEPMC': paper.get('inEPMC'),
                        'hasPDF': paper.get('hasPDF'),
                        'hasBook': paper.get('hasBook'),

                        # Citation data
                        'citedByCount': paper.get('citedByCount'),
                        'pubYear': paper.get('pubYear'),

                        # Enhanced features
                        'pubType': _extract_pub_type(paper.get('pubTypeList')),
                        'keywords': _extract_keywords(paper.get('keywordList')),
                        'meshTerms': _extract_mesh_terms(paper.get('meshHeadingList')),
                        'journalTitle': _extract_journal_title(paper.get('journalInfo')),
                        'journalISSN': _extract_journal_issn(paper.get('journalInfo')),
                        'authorAffiliations': _extract_author_affiliations(paper.get('authorList')),
                    }

                    records.append(record)

                except Exception as e:
                    error_count += 1
                    paper_id = paper.get('pmid', f'page{page_idx}_paper{paper_idx}')
                    print(f"Warning: Failed to process paper {paper_id}: {e}")
                    # Continue processing other papers
                    continue

        except Exception as e:
            error_count += 1
            print(f"Warning: Failed to process page {page_idx}: {e}")
            # Continue processing other pages
            continue

    print(f"\nProcessing summary:")
    print(f"  Papers processed: {len(records)}")
    print(f"  Duplicates removed: {duplicate_count}")
    print(f"  Errors encountered: {error_count}")

    return pd.DataFrame(records)
```

---

## COMBINED PATCH (All Fixes)

### Full Updated `clean_results()` Function:

```python
def clean_results(results: List[dict]) -> pd.DataFrame:
    """
    Retrieve enhanced metadata from results of query with robust error handling

    Parameters:
    `results`: JSON-encoded response (nested dictionary)

    Return: Dataframe of results with 20 metadata fields (deduplicated, error-handled)

    Improvements:
    - Deduplication by PMID
    - Fallback IDs for papers without PMID
    - Comprehensive error handling
    - Processing statistics
    """
    import json

    records = []
    seen_pmids = set()
    duplicate_count = 0
    error_count = 0
    no_pmid_count = 0

    for page_idx, page in enumerate(results):
        try:
            result_list = page.get('resultList', {})
            papers = result_list.get('result', [])

            if not papers:
                print(f"Warning: Page {page_idx} has no results")
                continue

            for paper_idx, paper in enumerate(papers):
                try:
                    # Extract ID with fallbacks
                    pmid = paper.get('pmid')
                    if pmid:
                        # Check for duplicates
                        if pmid in seen_pmids:
                            duplicate_count += 1
                            print(f"Warning: Duplicate PMID {pmid}, skipping")
                            continue
                        seen_pmids.add(pmid)
                        paper_id = str(pmid)
                    else:
                        # Use fallback IDs
                        no_pmid_count += 1
                        pmcid = paper.get('pmcid')
                        if pmcid:
                            paper_id = f"PMC{pmcid}"
                        else:
                            doi = paper.get('doi')
                            if doi:
                                paper_id = f"DOI:{doi}"
                            else:
                                paper_id = f"NOID_{page_idx}_{paper_idx}"

                    # Extract all enhanced metadata fields
                    record = {
                        # Core fields
                        'id': paper_id,
                        'title': paper.get('title'),
                        'abstract': paper.get('abstractText'),
                        'publication_date': paper.get('firstPublicationDate'),

                        # Boolean flags (Tier 1 - 8 fields)
                        'hasDbCrossReferences': paper.get('hasDbCrossReferences'),
                        'hasData': paper.get('hasData'),
                        'hasSuppl': paper.get('hasSuppl'),
                        'isOpenAccess': paper.get('isOpenAccess'),
                        'inPMC': paper.get('inPMC'),
                        'inEPMC': paper.get('inEPMC'),
                        'hasPDF': paper.get('hasPDF'),
                        'hasBook': paper.get('hasBook'),

                        # Citation data
                        'citedByCount': paper.get('citedByCount'),

                        # Temporal (extract year)
                        'pubYear': paper.get('pubYear'),

                        # Publication type
                        'pubType': _extract_pub_type(paper.get('pubTypeList')),

                        # Enhanced features (Tier 2)
                        'keywords': _extract_keywords(paper.get('keywordList')),
                        'meshTerms': _extract_mesh_terms(paper.get('meshHeadingList')),
                        'journalTitle': _extract_journal_title(paper.get('journalInfo')),
                        'journalISSN': _extract_journal_issn(paper.get('journalInfo')),
                        'authorAffiliations': _extract_author_affiliations(paper.get('authorList')),
                    }

                    records.append(record)

                except Exception as e:
                    error_count += 1
                    paper_id = paper.get('pmid', f'page{page_idx}_paper{paper_idx}')
                    print(f"Warning: Failed to process paper {paper_id}: {e}")
                    continue

        except Exception as e:
            error_count += 1
            print(f"Warning: Failed to process page {page_idx}: {e}")
            continue

    # Print processing summary
    print(f"\nMetadata extraction summary:")
    print(f"  Papers processed: {len(records)}")
    print(f"  Papers without PMID: {no_pmid_count} (used fallback IDs)")
    print(f"  Duplicates removed: {duplicate_count}")
    print(f"  Errors encountered: {error_count}")

    return pd.DataFrame(records)
```

---

## TESTING CHECKLIST

After applying fixes:

- [ ] Run diagnostic script for author affiliations
- [ ] Re-extract metadata if needed
- [ ] Verify row count (should be ≈ 21,391)
- [ ] Check for duplicate PMIDs (should be 0)
- [ ] Check for missing IDs (should be 0 or minimal)
- [ ] Validate author affiliations (should be > 0%)
- [ ] Re-run validation script
- [ ] Check feature engineering output
- [ ] Verify zero NaN values maintained

---

## DEPLOYMENT STEPS

1. **Backup current files:**
   ```bash
   cp src/query_epmc.py src/query_epmc.py.backup
   cp data/metadata/pmc_metadata_enhanced_full.csv data/metadata/pmc_metadata_enhanced_full.csv.backup
   ```

2. **Apply fixes to `src/query_epmc.py`**

3. **Test with sample query:**
   ```bash
   python3 src/query_epmc.py \
     "COVID-19 AND (PUB_YEAR:2020)" \
     -f 2020-01 \
     -t 2020-02 \
     -o out/test_query/
   ```

4. **Validate test output:**
   ```bash
   python3 validate_metadata_implementation.py
   ```

5. **If validation passes, re-extract full dataset:**
   ```bash
   # Use your actual query
   python3 src/query_epmc.py <your_query> -f 2001 -t 2024 -o data/metadata/
   ```

6. **Re-run feature engineering:**
   ```bash
   python3 src/prepare_metadata_features.py \
     --input data/metadata/query_results.csv \
     --output data/metadata/features_engineered.csv
   ```

7. **Final validation:**
   ```bash
   python3 validate_metadata_implementation.py
   ```

---

## EXPECTED RESULTS AFTER FIXES

### Before Fixes:
- Missing PMIDs: 496 (2.3%)
- Duplicate PMIDs: 1
- Author affiliations: 0% valid

### After Fixes:
- Missing PMIDs: 0 (or < 0.1% if no fallback ID available)
- Duplicate PMIDs: 0
- Author affiliations: > 50% valid (depends on API data availability)

---

## CONTACT & QUESTIONS

For questions about these fixes:
1. Review the comprehensive report: `COMPREHENSIVE_CODE_REVIEW_REPORT.md`
2. Check validation results: `validate_metadata_implementation.py`
3. Examine diagnostic output: Run the diagnostic script for author affiliations

**Estimated fix time:** 4-6 hours
**Priority:** HIGH
**Production blocker:** YES
