# Entity-URL Association Investigation Report

**Date:** 2025-12-03
**Issue:** Critical data quality bug - resources have incorrect URL associations
**Status:** Root cause identified, fix required

---

## Executive Summary

A critical data quality bug was discovered where resources in the final inventory have **ALL URLs from papers that mention them**, rather than just the **URL for that specific resource**. For example, PDB (Protein Data Bank) ended up with 118 URLs that are NOT rcsb.org - they are random URLs from papers that happen to mention PDB.

### Root Cause

Script `28b_merge_and_identify_missing.py` in the unified_bioresource_pipeline joins resources to URLs by PMID only. It collects ALL URLs from ALL papers mentioning a resource, instead of only the URL FOR that resource.

---

## The Problem Illustrated

### Expected Behavior
```
Resource: PDB
Papers mentioning PDB: PMID_1, PMID_2, PMID_3
URL for PDB: https://www.rcsb.org/
```

### Actual (Broken) Behavior
```
Resource: PDB
Papers mentioning PDB: PMID_1, PMID_2, PMID_3
URLs assigned to PDB:
  - https://www.rcsb.org/  (correct)
  - https://github.com/some/project  (from PMID_1 - WRONG)
  - https://example-database.org  (from PMID_2 - WRONG)
  - https://another-tool.com  (from PMID_3 - WRONG)
  - ... 118 total URLs (mostly WRONG)
```

---

## Two Pipelines Exist

There are **two separate pipeline directories** with different approaches:

### 1. `unified_bioresource_pipeline/` (Current 2022-mid2025 run)
- **Problem:** Entity-URL association is BROKEN
- Script 10 creates `entity_inventories/` with NO URL data
- Script 13 extracts URLs to paper CSVs AFTER script 10
- Script 28b tries to reconnect them by PMID - **THIS IS THE BUG**

### 2. `pipeline_synthesis_2025-11-18/` (Alternative pipeline)
- **Working:** Entity-URL association is CORRECT
- Script 11 extracts URLs directly to paper CSVs that already have entity columns
- `primary_entity_long`, `primary_entity_short`, and `resource_url` are in the SAME row
- Each paper-entity row has its associated URL

---

## Data Flow Comparison

### pipeline_synthesis (CORRECT)
```
Papers
  → NER extraction (entities)
  → Scoring (linguistic/setfit)
  → Filtered datasets (with entity columns)
  → URL extraction (script 11) adds url columns TO SAME FILE
  → Deduplication (maintains entity+url association)
  → Final output: entity + url in same row
```

### unified_bioresource_pipeline (BROKEN)
```
Papers
  → NER extraction (entities)
  → Scoring (linguistic/setfit)
  → Paper sets created (NO entity columns yet)
  → Script 10: entity_inventories/ created (NO URLs - ORPHANED)
  → Script 13: URLs added to paper CSVs (separate from entity_inventories)
  → Script 28b: Tries to join by PMID - COLLECTS ALL URLS FROM ALL PAPERS
  → Final output: resources have wrong URLs
```

---

## The Broken Script

**File:** `unified_bioresource_pipeline/scripts/phase8_url_recovery/28b_merge_and_identify_missing.py`

**Lines 123-127 (the bug):**
```python
# Find all URLs associated with this resource's papers
resource_urls = set()
for pmid in resource_pmids:
    if pmid in pmid_to_urls:
        resource_urls.update(pmid_to_urls[pmid])  # <-- BUG: gets ALL urls from paper
```

**What it does wrong:**
1. For each resource, gets all PMIDs of papers mentioning that resource
2. For each PMID, gets ALL URLs extracted from that paper
3. Assigns ALL those URLs to the resource

**What it should do:**
- Only assign a URL to a resource if the URL appears IN CONTEXT with the resource name
- OR use the `resource_url` column from the paper CSVs (which is the scored/primary URL for that paper)

---

## Input/Output Mapping

Full script mappings are available in:
- `unified_bioresource_pipeline_scripts_map.csv` - 32 scripts from unified pipeline
- `pipeline_synthesis_scripts_map.csv` - 28 scripts from pipeline_synthesis

### Key Scripts in unified_bioresource_pipeline

| Phase | Script | Problem |
|-------|--------|---------|
| 5 | 10_map_to_entities.py | Creates entity_inventories/ with NO URL data |
| 5 | 13_extract_urls.py | Adds URLs to paper CSVs, but doesn't update entity_inventories/ |
| 8 | 28b_merge_and_identify_missing.py | **THE BUG** - joins by PMID, gets all URLs |

### Key Scripts in pipeline_synthesis (working)

| Script | Why it works |
|--------|--------------|
| 10_create_filtered_datasets.py | Creates paper CSVs with entity columns |
| 11_extract_urls.py | Adds URL columns to SAME files that have entity columns |

---

## Evidence of the Bug

### File with correct association (pipeline_synthesis)
**File:** `pipeline_synthesis_2025-11-18/data/filtered/baseline_by_entity_match.csv`

**Columns include:**
- `primary_entity_long` - the resource name (e.g., "hahmir.db")
- `primary_entity_short` - short name
- `resource_url` - URL for THIS resource (e.g., "http://www.hahmirdb.in")
- `has_resource_url` - boolean

**Sample data:**
```
primary_entity_long    primary_entity_short    resource_url                    has_resource_url
bc-tfdb                NaN                     https://www.dqweilab-sjtu.com   True
hahmir.db              NaN                     http://www.hahmirdb.in          True
mufold-db              NaN                     http://mufold.org/mufolddb.php  True
```

### File with broken association (unified_bioresource_pipeline)
**File:** `unified_bioresource_pipeline/data/phase6_scanning/all_extracted_urls.csv`

**Columns:**
- `pmid` - paper ID
- `title` - paper title
- `url` - a URL from that paper
- `domain` - URL domain
- `intro_source` - why paper was included

**NO resource_name column** - URLs are not associated with specific resources

---

## Recommended Fixes

### Option 1: Use pipeline_synthesis data
The `pipeline_synthesis_2025-11-18/data/filtered/` files have correct entity-URL associations. These could be used as the source of truth.

**Pros:** Data already exists, no code changes needed
**Cons:** May need to verify it covers 2022-mid2025 date range

### Option 2: Fix script ordering in unified_bioresource_pipeline
Move URL extraction (script 13) BEFORE entity mapping (script 10), so entity_inventories/ gets created with URL data.

**Pros:** Fixes the pipeline properly
**Cons:** Requires re-running phases 5-9

### Option 3: Fix script 28b logic
Instead of joining ALL URLs by PMID, use only the `resource_url` column from the paper CSVs.

**Changes needed in 28b:**
```python
# Instead of getting ALL urls from papers:
# resource_urls.update(pmid_to_urls[pmid])

# Should get only the resource_url for papers where THIS resource is primary:
# Only add URL if it's the primary resource URL for that paper
```

**Pros:** Minimal change
**Cons:** Still a hack, doesn't fix root cause

### Option 4: Create bridge script
Create a new script that:
1. Reads `set_c_final.csv` (has both entity and URL columns)
2. Groups by entity name
3. Outputs proper entity-URL mapping

**Pros:** Doesn't require re-running pipeline
**Cons:** Additional script to maintain

---

## Files Referenced

### Documentation
- This file: `unified_bioresource_pipeline/docs/entity_url_investigation_2022-2025m.md`
- Script maps: `unified_bioresource_pipeline/docs/unified_bioresource_pipeline_scripts_map.csv`
- Script maps: `unified_bioresource_pipeline/docs/pipeline_synthesis_scripts_map.csv`

### Broken Script
- `unified_bioresource_pipeline/scripts/phase8_url_recovery/28b_merge_and_identify_missing.py`

### Correct Data Source
- `pipeline_synthesis_2025-11-18/data/filtered/baseline_by_entity_match.csv`
- `pipeline_synthesis_2025-11-18/data/filtered/baseline_by_pmid.csv`
- `pipeline_synthesis_2025-11-18/data/filtered/linguistic_excluding_baseline.csv`
- `pipeline_synthesis_2025-11-18/data/filtered/setfit_excluding_baseline.csv`

### Broken Data
- `unified_bioresource_pipeline/data/phase6_scanning/all_extracted_urls.csv` (no entity association)
- `unified_bioresource_pipeline/data/phase8_url_recovery/resources_merged_with_urls.csv` (wrong URLs)

### Original 2010-2022 Data (safe, not overwritten)
- `data/final_inventory_2022.csv` - original final inventory
- `data/manual_ner_extraction.csv` - original NER with URL column

---

## Original Data Safety

The original 2010-2022 data is **SAFE** in the `/data/` directory (separate from `unified_bioresource_pipeline/data/`):
- `data/final_inventory_2022.csv` - 3,112 resources
- `data/manual_ner_extraction.csv` - training data with URLs
- `data/manual_classifications.csv` - classification training data

These files have NOT been overwritten by the 2022-mid2025 run.

---

## Next Steps

1. **Decide on fix approach** (Options 1-4 above)
2. **Verify 2022-mid2025 data exists** in pipeline_synthesis if using Option 1
3. **Re-run affected phases** if using Options 2 or 3
4. **Regenerate final inventory** with correct entity-URL associations
5. **Run URL scanning** on corrected data

---

## Appendix: Background Processes

As of this investigation, these background processes are still running:
- `29_fetch_abstracts.py` - fetching abstracts for URL recovery
- `31_fetch_fulltext.py` - fetching fulltext for URL recovery

These should be stopped/reviewed as they are operating on broken data.
