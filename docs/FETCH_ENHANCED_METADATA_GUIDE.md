# Enhanced Metadata Fetching Guide

**Date**: 2025-10-30
**Script**: `src/fetch_enhanced_metadata.py`
**Purpose**: Bulk-fetch enhanced metadata for papers from Europe PMC API

---

## Overview

This guide documents the usage of the enhanced metadata fetching script, which efficiently retrieves comprehensive metadata for thousands of papers using the Europe PMC bulk POST API.

### Key Features

- **Efficient bulk fetching**: Uses POST API with batched PMIDs (up to 1000 per request)
- **Robust error handling**: Exponential backoff, retry logic, and graceful degradation
- **Checkpoint recovery**: Resume from interruptions without re-fetching completed batches
- **Comprehensive metadata**: Extracts 20+ fields including boolean flags, citations, MeSH terms, and more
- **Data validation**: Automated completeness checks and summary statistics
- **Multiple output formats**: CSV for analysis, pickle for fast loading

---

## Quick Start

### Basic Usage

```bash
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/pmc_metadata_enhanced_full.csv
```

### With Custom Parameters

```bash
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/pmc_metadata_enhanced_full.csv \
    --chunk-size 1000 \
    --retry 3 \
    --backoff 0.5
```

### Resume from Checkpoint

```bash
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/pmc_metadata_enhanced_full.csv \
    --resume
```

---

## Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--input` | Yes | - | Input CSV file with PMIDs (must have "id" column) |
| `--output` | Yes | - | Output CSV file for enhanced metadata |
| `--chunk-size` | No | 1000 | Number of PMIDs per API request (max 1000) |
| `--retry` | No | 3 | Maximum retry attempts for failed requests |
| `--backoff` | No | 0.5 | Initial backoff delay in seconds for exponential retry |
| `--checkpoint` | No | auto | Checkpoint file path (auto-generated if not specified) |
| `--resume` | No | False | Resume from existing checkpoint if available |

---

## Input Requirements

The input CSV file must contain:
- **Required column**: `id` (contains PMIDs)
- **Optional columns**: Any other columns (e.g., title, abstract) will be ignored

### Example Input Format

```csv
id,title,abstract,publication_date
34599955,"Wastewater, waste, and water-based...",Traditional wastewater-based...,2021-09-30
34741192,The Rat Genome Database (RGD)...,Model organism research...,2021-11-05
```

---

## Output Files

### 1. Primary Output: CSV File

**File**: `data/metadata/pmc_metadata_enhanced_full.csv`

Contains 24 metadata columns:

#### Core Identifiers (3 fields)
- `id` - PubMed ID
- `doi` - Digital Object Identifier
- `pmcid` - PubMed Central ID

#### Basic Information (3 fields)
- `title` - Paper title
- `abstract` - Abstract text
- `publication_date` - First publication date (YYYY-MM-DD)

#### Priority Tier 1: Boolean Flags (8 fields)
- `hasDbCrossReferences` ⭐ - Has database cross-references (highest priority for identifying data resources)
- `hasData` - Has associated datasets
- `hasSuppl` - Has supplementary materials
- `isOpenAccess` - Is open access publication
- `inPMC` - Available in PubMed Central
- `inEPMC` - Available in Europe PMC
- `hasPDF` - Has full-text PDF
- `hasBook` - Is or part of a book

#### Citation & Temporal Data (2 fields)
- `citedByCount` - Number of citations (integer)
- `pubYear` - Publication year (integer, extracted from publication_date)

#### Publication Type (1 field)
- `pubType` - Publication type(s), pipe-delimited if multiple (e.g., "research-article|Journal Article")

#### Priority Tier 2: Enhanced Features (4 fields)
- `keywords` - JSON-encoded list of keywords
- `meshTerms` - JSON-encoded list of MeSH descriptor names
- `journalTitle` - Journal title
- `journalISSN` - Journal ISSN(s), pipe-delimited if multiple
- `authorCountries` - JSON-encoded list of author affiliations (raw)

#### Metadata (2 fields)
- `fetch_timestamp` - When the record was fetched
- `fetch_success` - Boolean indicating successful fetch

**Total**: 24 columns

### 2. Pickle Backup

**File**: `data/metadata/pmc_metadata_enhanced_full.pkl`

Binary format for fast loading in Python:

```python
import pandas as pd
df = pd.read_pickle('data/metadata/pmc_metadata_enhanced_full.pkl')
```

**Advantages**:
- 10-100x faster loading than CSV
- Preserves data types (no string/int conversion needed)
- Ideal for repeated use in analysis/training

### 3. Validation Statistics

**File**: `data/metadata/pmc_metadata_enhanced_full_validation.json`

JSON file containing:

```json
{
  "total_input": 21677,
  "total_fetched": 21500,
  "coverage_pct": 99.18,
  "missing_count": 177,
  "missing_pmids": ["12345", "67890", ...],
  "duplicate_count": 0,
  "tier1_completeness": {
    "hasDbCrossReferences": 98.5,
    "hasData": 97.2,
    "citedByCount": 99.8,
    ...
  },
  "tier1_avg_completeness": 97.8,
  "citation_stats": {
    "mean": 15.3,
    "median": 8.0,
    "min": 0,
    "max": 1523
  },
  "year_range": {
    "min": 2011,
    "max": 2021
  }
}
```

### 4. Log File

**File**: `data/metadata/fetch_log_YYYYMMDD_HHMMSS.txt`

Detailed execution log with:
- Timestamp for each operation
- Success/warning/error messages
- Progress tracking
- Final summary statistics
- Total elapsed time

**Example**:
```
=== Enhanced Metadata Fetch Log ===
Started: 2025-10-30 14:42:02

[2025-10-30 14:42:02] [INFO] === Enhanced Metadata Fetch Started ===
[2025-10-30 14:42:02] [INFO] Input: data/epmc_query_results_2022.csv
[2025-10-30 14:42:02] [INFO] Loaded 21677 PMIDs
[2025-10-30 14:42:02] [INFO] Split into 22 chunks
...
[2025-10-30 14:43:08] [INFO] === Summary ===
[2025-10-30 14:43:08] [INFO] Coverage: 99.18%

Completed: 2025-10-30 14:43:08
Total elapsed time: 1m 6.2s
```

---

## Architecture & Components

### 1. PMIDChunker
Splits large PMID lists into manageable chunks for batch processing.

**Methods**:
- `chunk_pmids(pmids, chunk_size)` - Split PMIDs into chunks
- `build_query(pmids)` - Build Europe PMC query string

### 2. BulkFetcher
Handles Europe PMC API requests with robust error handling.

**Features**:
- POST requests to `https://www.ebi.ac.uk/europepmc/webservices/rest/searchPOST`
- Exponential backoff: 0.5s → 1s → 2s → 4s
- Retry up to 3 times per failed request
- Handles rate limiting (HTTP 429)
- Request timeout: 30 seconds

**Parameters**:
- `query` - OR'd PMID query (e.g., "EXT_ID:123 OR EXT_ID:456")
- `resultType=core` - Returns comprehensive metadata
- `format=json` - JSON response format
- `pageSize` - Number of results per page

### 3. MetadataParser
Extracts all metadata fields from Europe PMC JSON responses.

**Extraction Methods**:
- `parse_paper(paper)` - Main parsing function
- `_to_bool(value)` - Convert to boolean safely
- `_to_int(value)` - Convert to integer safely
- `_extract_year(date_str)` - Extract year from date
- `_extract_pub_type(pub_type_list)` - Extract publication types
- `_extract_keywords(keyword_list)` - Extract keywords as JSON
- `_extract_mesh_terms(mesh_heading_list)` - Extract MeSH terms
- `_extract_journal_title(journal_info)` - Extract journal title
- `_extract_journal_issn(journal_info)` - Extract journal ISSN
- `_extract_author_countries(author_list)` - Extract author affiliations

**Graceful Degradation**:
- Missing fields return `None` or `NaN`
- Invalid data types are handled safely
- Script continues even if individual fields fail to parse

### 4. CheckpointManager
Manages progress saving and recovery for interruption resilience.

**Checkpoint Data**:
- `processed_chunks` - List of completed chunk indices
- `results` - All parsed papers so far
- `failed_chunks` - List of (chunk_idx, pmids) for failed batches
- `timestamp` - Checkpoint creation time

**Methods**:
- `save_checkpoint(...)` - Save progress after each batch
- `load_checkpoint(...)` - Load existing checkpoint on resume

**Checkpoint File**: Auto-generated as `{output_base}_checkpoint.pkl`

### 5. Validator
Validates completeness and quality of fetched metadata.

**Validation Checks**:
1. **Coverage**: % of input PMIDs successfully fetched
2. **Missing PMIDs**: List of PMIDs not found in Europe PMC
3. **Duplicates**: Check for duplicate PMID entries
4. **Tier 1 Completeness**: % non-null values for priority fields
5. **Citation Statistics**: Mean, median, min, max citations
6. **Year Range**: Min and max publication years

**Success Criteria**:
- Coverage ≥ 95%
- Tier 1 avg completeness ≥ 95%
- No duplicates
- Year range within expected bounds (2011-2021)

### 6. Logger
Provides comprehensive logging to both console and file.

**Log Levels**:
- `INFO` - Normal operation messages
- `WARNING` - Non-fatal issues (rate limiting, retries)
- `ERROR` - Fatal errors (failed after all retries)
- `DEBUG` - Detailed progress information

---

## Performance

### Expected Runtime (21,677 papers)

| Configuration | Chunks | Time per Request | Total Time |
|---------------|--------|------------------|------------|
| Chunk size 1000 | 22 | ~3 seconds | ~66 seconds |
| Chunk size 500 | 44 | ~2 seconds | ~88 seconds |
| Chunk size 100 | 217 | ~1 second | ~217 seconds |

**Recommendation**: Use default chunk size of 1000 for optimal performance.

### API Rate Limiting

Europe PMC does not publish strict rate limits, but we implement:
- 0.1 second delay between requests (polite crawling)
- Exponential backoff on 429 errors
- Max 3 retries per request

**Best Practice**: Schedule large fetches during off-peak hours (weekends, evenings UTC).

---

## Error Handling & Recovery

### Network Failures

**Symptoms**:
- Connection timeout errors
- DNS resolution failures
- Temporary network interruptions

**Handling**:
1. Automatic retry with exponential backoff (0.5s → 1s → 2s → 4s)
2. Progress saved to checkpoint after each successful batch
3. Failed chunks logged for manual review
4. Script continues processing remaining chunks

**Recovery**:
```bash
# Simply re-run with --resume flag
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/pmc_metadata_enhanced_full.csv \
    --resume
```

### Rate Limiting (HTTP 429)

**Symptoms**:
- HTTP 429 "Too Many Requests" errors
- Temporary API throttling

**Handling**:
1. Exponential backoff automatically applied
2. Longer delays between retries (up to 4 seconds)
3. Progress saved to avoid re-fetching

**Prevention**:
- Use default 0.1s delay between requests
- Reduce `--chunk-size` if experiencing frequent 429s
- Increase `--backoff` delay (e.g., `--backoff 1.0`)

### Missing PMIDs

**Symptoms**:
- PMIDs not found in Europe PMC
- Empty API responses for some papers

**Causes**:
- Papers not indexed in Europe PMC
- Recently published papers (indexing delay)
- Retracted or removed papers
- PMID typos in input data

**Handling**:
1. Missing PMIDs logged in validation stats
2. Records created with `fetch_success=False`
3. Can be identified for manual review

**Review Missing PMIDs**:
```python
import pandas as pd
import json

# Load validation stats
with open('data/metadata/pmc_metadata_enhanced_full_validation.json') as f:
    stats = json.load(f)

# Print missing PMIDs
print(f"Missing: {stats['missing_count']}")
print(stats['missing_pmids'])
```

### Interrupted Execution

**Symptoms**:
- Script killed (Ctrl+C)
- System shutdown
- Connection lost

**Recovery**:
```bash
# Resume automatically from checkpoint
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/pmc_metadata_enhanced_full.csv \
    --resume
```

**Checkpoint Cleanup**:
- Automatically removed on successful completion (≥95% coverage)
- Manually remove with: `rm data/metadata/*_checkpoint.pkl`

---

## Data Quality

### Tier 1 Field Completeness

Expected completeness rates based on Europe PMC data characteristics:

| Field | Expected | Notes |
|-------|----------|-------|
| `hasDbCrossReferences` | 95-100% | Core boolean flag |
| `hasData` | 95-100% | Core boolean flag |
| `hasSuppl` | 95-100% | Core boolean flag |
| `isOpenAccess` | 99-100% | Almost always present |
| `inPMC` | 99-100% | Core indexing field |
| `inEPMC` | 99-100% | Core indexing field |
| `hasPDF` | 95-100% | Core availability flag |
| `hasBook` | 95-100% | Core type flag |
| `citedByCount` | 98-100% | May be 0 for new papers |
| `pubYear` | 99-100% | Extracted from publication_date |

### Tier 2 Field Completeness

Variable completeness due to inconsistent metadata:

| Field | Expected | Notes |
|-------|----------|-------|
| `keywords` | 30-60% | Not all papers have keywords |
| `meshTerms` | 60-80% | More complete for PubMed papers |
| `journalTitle` | 95-100% | Almost always present |
| `journalISSN` | 90-95% | Usually present |
| `authorCountries` | 50-70% | Depends on affiliation formatting |

### Validation Thresholds

**Acceptable Quality**:
- Coverage ≥ 95% (at least 20,593 of 21,677 papers)
- Tier 1 avg completeness ≥ 95%
- Duplicate count = 0

**Warning Signs**:
- Coverage < 90% → Check API availability
- Tier 1 completeness < 90% → Possible API schema change
- Many failed chunks → Network or rate limiting issues

---

## Troubleshooting

### Issue: Low Coverage (< 90%)

**Possible Causes**:
1. Europe PMC API downtime
2. Network connectivity issues
3. Invalid PMIDs in input file

**Solutions**:
```bash
# 1. Check API status
curl "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=cancer&format=json"

# 2. Verify input PMIDs
python -c "import pandas as pd; df = pd.read_csv('data/epmc_query_results_2022.csv'); print(df['id'].describe())"

# 3. Retry with longer backoff
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/pmc_metadata_enhanced_full.csv \
    --backoff 2.0 \
    --resume
```

### Issue: Frequent Rate Limiting

**Symptoms**:
- Many HTTP 429 errors in log
- Slow progress

**Solutions**:
```bash
# Reduce chunk size and increase backoff
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/pmc_metadata_enhanced_full.csv \
    --chunk-size 500 \
    --backoff 1.0 \
    --retry 5
```

### Issue: Script Hangs

**Possible Causes**:
1. Network timeout (default 30s may be too short)
2. Large response size

**Solutions**:
- Check network connectivity: `ping www.ebi.ac.uk`
- Monitor log file in real-time: `tail -f data/metadata/fetch_log_*.txt`
- Kill and resume: Ctrl+C, then re-run with `--resume`

### Issue: Invalid JSON Response

**Symptoms**:
- Parse errors in log
- Empty results for valid PMIDs

**Solution**:
- Check Europe PMC status page
- Retry with `--resume` after API recovery
- Report issue to Europe PMC if persistent

---

## Advanced Usage

### Custom Checkpoint Location

```bash
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/pmc_metadata_enhanced_full.csv \
    --checkpoint /tmp/my_checkpoint.pkl
```

### Aggressive Retry Strategy

For unreliable networks:

```bash
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/pmc_metadata_enhanced_full.csv \
    --retry 5 \
    --backoff 2.0
```

### Parallel Fetching (NOT RECOMMENDED)

While the script is single-threaded, you could split input and run parallel instances:

```bash
# Split input into 4 parts
split -l 5420 data/epmc_query_results_2022.csv input_part_

# Run 4 parallel instances (in separate terminals)
python src/fetch_enhanced_metadata.py --input input_part_aa --output data/metadata/part1.csv &
python src/fetch_enhanced_metadata.py --input input_part_ab --output data/metadata/part2.csv &
python src/fetch_enhanced_metadata.py --input input_part_ac --output data/metadata/part3.csv &
python src/fetch_enhanced_metadata.py --input input_part_ad --output data/metadata/part4.csv &

# Merge results
python -c "
import pandas as pd
parts = [pd.read_csv(f'data/metadata/part{i}.csv') for i in range(1,5)]
merged = pd.concat(parts, ignore_index=True)
merged.to_csv('data/metadata/pmc_metadata_enhanced_full.csv', index=False)
"
```

**Warning**: This may trigger rate limiting. Use with caution and longer backoff delays.

---

## Next Steps

After successfully fetching metadata:

### 1. Load and Explore Data

```python
import pandas as pd
import json

# Load CSV
df = pd.read_csv('data/metadata/pmc_metadata_enhanced_full.csv')

# Or load pickle (faster)
df = pd.read_pickle('data/metadata/pmc_metadata_enhanced_full.pkl')

# Basic stats
print(df.info())
print(df.describe())

# Check boolean flags
boolean_cols = ['hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess']
print(df[boolean_cols].sum())

# Citation distribution
print(df['citedByCount'].describe())
```

### 2. Feature Engineering

See `docs/PIPELINE_GUIDES.md` for Phase 2: Feature Engineering Pipeline

**Key transformations**:
- `log_citations = log(citedByCount + 1)`
- `years_since_pub = 2025 - pubYear`
- TF-IDF on MeSH terms
- One-hot encode pubType

### 3. Merge with Training Data

```python
import pandas as pd

# Load metadata
metadata = pd.read_pickle('data/metadata/pmc_metadata_enhanced_full.pkl')

# Load training data
classif = pd.read_csv('data/manual_classifications.csv')

# Merge on PMID
merged = classif.merge(metadata, on='id', how='left')

# Check merge success
print(f"Matched: {merged['fetch_success'].sum()} / {len(merged)}")
```

### 4. Run Validation Notebook

Create `notebooks/validate_metadata_fetch.ipynb` to:
- Visualize field completeness
- Plot citation distributions
- Analyze year ranges
- Identify missing value patterns
- Correlate features with labels

---

## References

### Europe PMC API Documentation
- **Main API**: https://europepmc.org/RestfulWebService
- **POST Endpoint**: https://www.ebi.ac.uk/europepmc/webservices/rest/searchPOST
- **Query Syntax**: https://europepmc.org/Help#mostofsearch
- **Result Types**: https://europepmc.org/RestfulWebService#resultTypes

### Related Scripts
- `src/query_epmc.py` - Original query script (GET requests, pagination)
- `src/prepare_metadata_features.py` - Feature engineering (Phase 2)
- `src/create_training_datasets_with_metadata.py` - Dataset integration (Phase 3)

### Project Documentation
- `plans/2025-10-30_enhanced_metadata_fetching_plan.md` - Implementation plan
- `docs/PIPELINE_GUIDES.md` - Full pipeline documentation
- `docs/AGENT_HANDOFF_2025-10-30.md` - Project context

---

## Support

For issues or questions:
1. Check this guide's Troubleshooting section
2. Review log file in `data/metadata/fetch_log_*.txt`
3. Examine validation stats in `*_validation.json`
4. Consult Europe PMC documentation

---

**Last Updated**: 2025-10-30
**Maintainer**: Claude Code
**Version**: 1.0
