# Pipeline Changes - 2025-11-20

## Summary of Changes

**Major Update**: Modified the bioresource discovery pipeline to **INCLUDE baseline** in all strategy sets and added comprehensive URL validation for the final union dataset.

---

## Key Changes

### 1. Baseline Inclusion (CRITICAL CHANGE)

**Previous Behavior:**
- Sets A and B excluded baseline resources
- Files: `linguistic_excluding_baseline.csv` and `setfit_excluding_baseline.csv`
- Purpose: Find only "novel" resources

**New Behavior:**
- Sets A and B **INCLUDE ALL papers** (including baseline)
- Files: `linguistic_all_papers.csv` and `setfit_all_papers.csv`
- Purpose: Complete comparison of filtering strategies

**Rationale:**
- User requested complete deduplication analysis including baseline
- Enables accurate comparison of strategy performance
- No artificial exclusion of known resources

### 2. Three-Set Deduplication

**Previous:**
- Only Set A (Linguistic) was deduplicated
- Result: 963 unique resources

**New:**
- **Set A (Linguistic)**: All 8,683 papers → deduplicated
- **Set B (SetFit)**: All 7,938 papers → deduplicated
- **Set C (Union)**: Deduplicated A + B → deduplicated again

**Script**: `scripts/17_deduplicate_all_sets.py`

### 3. URL Validation Pipeline

**New Addition:**
- URL scanning for Set C using bioresource_url_scanner
- Backfill URL data to Sets A & B for comparison
- All three final sets have identical column structure

**Scripts:**
- `scripts/18_scan_urls_set_c.py` - Scan URLs (75-90 min)
- `scripts/19_backfill_url_data.py` - Add URL columns to A & B

---

## Modified Scripts

### Script 10: `create_filtered_datasets.py`

**Changes:**
1. File names changed:
   - `linguistic_excluding_baseline.csv` → `linguistic_all_papers.csv`
   - `setfit_excluding_baseline.csv` → `setfit_all_papers.csv`

2. Filtering logic removed:
   ```python
   # OLD:
   df_2 = df_union[
       (df_union['in_linguistic'] == True) &
       (~df_union['pmid_str'].isin(baseline_pmids))
   ].copy()

   # NEW:
   df_2 = df_union[
       (df_union['in_linguistic'] == True)
   ].copy()
   ```

3. Validation checks updated to reflect baseline inclusion

### Script 17: `deduplicate_all_sets.py` (NEW)

**Purpose:** Unified deduplication for all three sets

**Features:**
- Deduplicates Set A (Linguistic)
- Deduplicates Set B (SetFit)
- Creates Set C by merging deduplicated A + B
- Deduplicates Set C
- Generates comprehensive statistics

**Input:**
- `data/filtered/linguistic_all_papers.csv`
- `data/filtered/setfit_all_papers.csv`

**Output:**
- `results/deduplicated/set_a_linguistic_dedup.csv`
- `results/deduplicated/set_b_setfit_dedup.csv`
- `results/deduplicated/set_c_union_dedup.csv`
- `results/deduplicated/deduplication_statistics.txt`

### Script 18: `scan_urls_set_c.py` (NEW)

**Purpose:** Scan URLs in Set C for validation

**Process:**
1. Extract URLs from Set C
2. Run bioresource_url_scanner (75-90 min)
3. Merge scan results back to Set C
4. Add URL validation columns

**URL Scan Columns Added:**
- `url_status` - HTTP status or error
- `url_final` - Final URL after redirects
- `url_score` - Bioresource confidence score (0-1)
- `url_is_database` - Boolean
- `url_is_portal` - Boolean
- `url_keywords_found` - Count of bio keywords
- `url_content_indicators` - Content analysis
- `url_bioinformatics_terms` - Domain-specific terms
- `url_download_links` - Download availability
- `url_institutional` - Institutional affiliation
- `url_wayback_used` - Whether Wayback Machine was used

**Output:**
- `results/url_scanned/set_c_with_url_scan.csv`

### Script 19: `backfill_url_data.py` (NEW)

**Purpose:** Add URL validation columns to Sets A & B

**Process:**
1. Load URL scan data from Set C
2. Match URLs in Sets A & B
3. Add URL columns to both sets
4. Validate column consistency

**Output (Final Datasets):**
- `results/final/set_a_linguistic_final.csv`
- `results/final/set_b_setfit_final.csv`
- `results/final/set_c_union_final.csv`

All three files have **identical column structure** for easy comparison.

---

## New Pipeline Flow

```
Input: EPMC Papers (149,943)
    ↓
Phase 1: Classification (V2 + PyCaret)
    ↓
Phase 2: NER (V2 + spaCy Hybrid)
    ↓
Phase 3: PMID Extraction → 34,279 papers
    ↓
Phase 4: Linguistic Filtering → 8,648 high + 20,816 medium
    ↓
Phase 5: SetFit Inference → 7,938 papers (conf ≥0.60)
    ↓
Phase 6: Entity Mapping
    ├─ Set A: 8,683 linguistic papers (ALL, including baseline)
    ├─ Set B: 7,938 SetFit papers (ALL, including baseline)
    └─ Set C: 16,605 union papers
    ↓
Phase 7: Create Filtered Datasets
    ├─ linguistic_all_papers.csv (8,683 papers)
    └─ setfit_all_papers.csv (7,938 papers)
    ↓
Phase 8: Unified Deduplication ← NEW!
    ├─ Set A: 8,683 → ~1,200-1,400 resources
    ├─ Set B: 7,938 → ~600-800 resources
    └─ Set C: Union → ~1,500-1,800 resources
    ↓
Phase 9: URL Scanning (Set C only) ← NEW!
    └─ Validate all URLs with bioresource_url_scanner
    ↓
Phase 10: Backfill URL Data ← NEW!
    └─ Add URL columns to Sets A & B
    ↓
Final Output:
    ├─ set_a_linguistic_final.csv (identical columns)
    ├─ set_b_setfit_final.csv (identical columns)
    └─ set_c_union_final.csv (identical columns)
```

---

## Running the Pipeline

### Quick Start

```bash
# Run complete pipeline (automated)
cd /Users/warren/development/GBC/inventory_2022/pipeline_synthesis_2025-11-18
python run_complete_pipeline.py
```

### Step-by-Step

```bash
# 1. Entity mapping
python scripts/03_map_papers_to_entities.py

# 2. Create filtered datasets (with baseline)
python scripts/10_create_filtered_datasets.py

# 3. Deduplicate all sets
python scripts/17_deduplicate_all_sets.py

# 4. URL scan Set C (75-90 min, optional)
python scripts/18_scan_urls_set_c.py

# 5. Backfill URL data
python scripts/19_backfill_url_data.py
```

### Estimated Runtime

- **Without URL scanning**: ~12-17 minutes
- **With URL scanning**: ~87-107 minutes

---

## Output Files

### Deduplication Outputs

```
results/deduplicated/
├── set_a_linguistic_dedup.csv       # Linguistic strategy resources
├── set_b_setfit_dedup.csv           # SetFit strategy resources
├── set_c_union_dedup.csv            # Combined strategy resources
└── deduplication_statistics.txt     # Summary stats
```

### URL Scan Outputs

```
results/url_scanned/
├── set_c_with_url_scan.csv          # Set C with URL validation
└── url_scan_statistics.txt          # URL scan stats
```

### Final Outputs (Ready for Analysis)

```
results/final/
├── set_a_linguistic_final.csv       # Set A with URL data
├── set_b_setfit_final.csv           # Set B with URL data
├── set_c_union_final.csv            # Set C (already has URL data)
└── backfill_statistics.txt          # Backfill stats
```

---

## Expected Results

### Set A (Linguistic)
- **Input**: 8,683 papers (all linguistic, including baseline)
- **Expected**: ~1,200-1,400 unique resources
- **Coverage**: 80% of baseline (from previous analysis)

### Set B (SetFit)
- **Input**: 7,938 papers (confidence ≥0.60, including baseline)
- **Expected**: ~600-800 unique resources
- **Coverage**: 38% of baseline (from previous analysis)

### Set C (Union)
- **Input**: Deduplicated A + B
- **Expected**: ~1,500-1,800 unique resources
- **Coverage**: 97% of baseline (from previous analysis)
- **Overlap**: ~0.1% (only 16 papers common between A and B)

---

## Validation & Quality Checks

1. **Baseline Inclusion**: Sets A & B now include baseline PMIDs
2. **Column Consistency**: All three final sets have identical structure
3. **URL Validation**: All resources have URL scan data for quality assessment
4. **Deduplication**: Each set independently deduplicated + union deduplicated

---

## Notes

- **Baseline no longer excluded**: This is intentional for complete analysis
- **URL scanning is optional**: Can skip if URL validation not needed
- **All sets comparable**: Identical columns enable direct comparison
- **Three-strategy comparison**: Linguistic vs SetFit vs Union

---

## Files Modified

1. `scripts/10_create_filtered_datasets.py` - Removed baseline exclusion
2. `scripts/17_deduplicate_all_sets.py` - NEW unified deduplication
3. `scripts/18_scan_urls_set_c.py` - NEW URL scanning
4. `scripts/19_backfill_url_data.py` - NEW URL backfill
5. `run_complete_pipeline.py` - NEW master orchestrator

---

## Questions?

See:
- `docs/starting_doc.md` - Main navigation
- `PIPELINE_STATUS_2025-11-20.md` - Previous status (before changes)
- Script headers for detailed documentation

---

**Last Updated**: 2025-11-20
**Author**: Claude Code
**Status**: ✅ Ready for Execution
