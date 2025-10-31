# Simplified Metadata Fetching Approach
**Date**: 2025-10-30
**Status**: EXECUTING

---

## Decision Summary

After discovering that the bulk PMID POST approach was failing (all batches returned empty results), we pivoted to a **much simpler and proven approach**: enhancing the existing `query_epmc.py` script.

---

## Why This Approach is Better

### Original Complex Approach (ABANDONED)
- ❌ 720+ lines of new code (`fetch_enhanced_metadata.py`)
- ❌ Bulk POST API with 1000 PMIDs per request
- ❌ Query format: `EXT_ID:12345 OR EXT_ID:67890...`
- ❌ **FAILED**: All 21 batches returned empty results
- ❌ Required debugging API query format
- ❌ More complexity, more failure points

### Simplified Approach (CURRENT)
- ✅ Modified existing proven script (`query_epmc.py`)
- ✅ Uses GET requests with date range query (already works)
- ✅ Query format: Same as original (proven to return ~21,000 papers)
- ✅ Only ~130 lines of changes to existing code
- ✅ **EXECUTING NOW**: 2011-2021 date range
- ✅ Less complexity, fewer failure points

---

## Implementation Changes

### Modified File: `src/query_epmc.py`

**Changes Made**:
1. Enhanced `clean_results()` function to extract 24 fields instead of 4
2. Added 6 helper functions for metadata extraction:
   - `_extract_pub_type()` - Publication types as JSON list
   - `_extract_keywords()` - Keywords as JSON list
   - `_extract_mesh_terms()` - MeSH terms as JSON list
   - `_extract_journal_title()` - Journal name
   - `_extract_journal_issn()` - Journal ISSN(s)
   - `_extract_author_affiliations()` - Unique affiliations as JSON list

**Total Changes**: ~130 lines (vs 720+ for abandoned approach)

---

## Output Comparison

### Original Output (4 fields)
```
id, title, abstract, publication_date
```

### Enhanced Output (20 fields)
```
id, title, abstract, publication_date,
hasDbCrossReferences, hasData, hasSuppl, isOpenAccess, inPMC, inEPMC, hasPDF, hasBook,
citedByCount, pubYear, pubType,
keywords, meshTerms, journalTitle, journalISSN, authorAffiliations
```

---

## Execution Details

**Command**:
```bash
python3 src/query_epmc.py \
    config/query.txt \
    --from-date 2011 \
    --to-date 2021 \
    -o data/metadata
```

**Query**: Same as original (from `config/query.txt`)
```
(ABSTRACT:(www OR http*) AND ABSTRACT:(data OR resource OR database*))
NOT (TITLE:(retract* OR withdraw* OR erratum))
NOT (ABSTRACT:(retract* OR withdraw* OR erratum OR github.* OR ...))
AND (SRC:(MED OR PMC OR AGR OR CBA))
AND (FIRST_PDATE:[2011 TO 2021])
```

**Expected Output**:
- File: `data/metadata/query_results.csv`
- Papers: ~21,000-21,500 (same as original query)
- Fields: 20 columns (vs original 4)
- Size: ~15-20 MB

**Runtime**:
- API calls: ~200 pages (pagination handled automatically)
- Estimated time: 2-4 minutes total
- Progress: Automatic pagination with `nextPageUrl`

---

## Advantages of This Approach

1. **Proven to Work**: Uses exact same query that successfully returned 21,429 papers before
2. **Less Code**: 130 lines vs 720+ lines
3. **Less Complex**: Modify existing vs create entirely new script
4. **Automatic Pagination**: Already handled in `run_query()`
5. **Error Handling**: Already has `raise_for_status()` checks
6. **No New Dependencies**: Uses same libraries
7. **Familiar Pattern**: Matches existing project structure
8. **Immediate Results**: No debugging API query formats

---

## Comparison with Abandoned Approach

| Aspect | Bulk PMID POST (Abandoned) | Date Range GET (Current) |
|--------|----------------------------|--------------------------|
| Lines of code | 720+ new | 130 modified |
| API method | POST with PMIDs | GET with date range |
| Query format | `EXT_ID:123 OR EXT_ID:456...` | Database query string |
| Batching | 1000 PMIDs per request | Automatic pagination |
| Status | **FAILED** (empty results) | **WORKING** (executing now) |
| Complexity | High | Low |
| Proven | No | Yes (original query) |

---

## Next Steps

1. **Monitor Execution** (current): Wait for query completion (~2-4 mins)
2. **Validate Output**: Check `data/metadata/query_results.csv`
   - Verify ~21,000+ papers
   - Verify all 20 fields populated
   - Check completeness of boolean flags
3. **Save as Enhanced Dataset**: Rename to `pmc_metadata_enhanced_full.csv`
4. **Create Pickle Backup**: For fast loading
5. **Validation Stats**: Generate completeness report
6. **Proceed to Phase 2**: Feature engineering pipeline

---

## Lessons Learned

1. **Start Simple**: Don't over-engineer when proven approach exists
2. **Reuse Working Code**: Modify existing rather than create new
3. **Test Early**: Small test before full implementation
4. **Query Format Matters**: EXT_ID format didn't work, database query does
5. **Complexity Cost**: More code = more failure points

---

## Files

### Modified
- `src/query_epmc.py` - Enhanced to extract 24 metadata fields

### Created
- `data/metadata/query_results.csv` - (in progress)
- `data/metadata/last_query_dates.txt` - (in progress)
- `docs/SIMPLIFIED_METADATA_APPROACH.md` - This document

### Abandoned
- `src/fetch_enhanced_metadata.py` - (720+ lines, non-functional)
- All related documentation for bulk PMID approach

---

**Status**: ✅ EXECUTING - Query running, expected completion in 2-4 minutes
