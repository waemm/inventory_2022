# Plan: Filter and Merge Two Bioresource Batches

**Created:** 2025-12-10
**Status:** Ready for execution
**Output Directory:** `unified_bioresource_pipeline/final_merged_batch/`

---

## Overview

Merge two bioresource inventory batches (2010-2022 and 2022-2025) into a single deduplicated inventory with only live URLs, then compare against the GBC external baseline.

### Input Files

| Batch | File | Records | Live URLs |
|-------|------|---------|-----------|
| 2010-2022 | `unified_bioresource_pipeline/post_processing/results/final_inventory_QC_FIXED.csv` | 1,688 | ~996 (59%) |
| 2022-2025 | `unified_bioresource_pipeline/2025-12-04-111420-z381s/post_processing/final_inventory_QC_FIXED.csv` | 1,510 | 1,510 (100%) |

### Expected Output

- **~2,400-2,500 unique bioresources** with live URLs (after filtering and deduplication)
- Baseline comparison flagging resources already in GBC database

---

## Directory Structure

```
unified_bioresource_pipeline/final_merged_batch/
├── plan/
│   └── MERGE_PLAN.md                    # Copy of this plan
├── scripts/
│   ├── 01_filter_live_urls.py           # Filter both batches to live URLs only
│   ├── 02_merge_batches.py              # Combine and deduplicate
│   ├── 03_baseline_comparison.py        # Compare against GBC baseline
│   └── 04_generate_report.py            # Final statistics and report
├── data/
│   ├── input/                           # Symlinks or copies of source files
│   ├── filtered/                        # After URL filtering
│   ├── merged/                          # After deduplication
│   ├── review/                          # ** REVIEW FILES FOR USER APPROVAL **
│   └── final/                           # Final output with baseline flags
├── docs/
│   └── PROCESSING_LOG.md                # Execution log
└── README.md                            # Usage instructions
```

---

## Workflow with Review Checkpoints

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Filter Live URLs                                        │
│   Output: filtered/batch_*.csv                                  │
│   Summary: docs/01_FILTER_SUMMARY.md                            │
│   ** CHECKPOINT: Review summary before proceeding **            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Identify Duplicates (NO AUTO-MERGE)                     │
│   Output: review/proposed_merges.csv  ← ** USER REVIEWS THIS ** │
│   Summary: docs/02_DEDUP_SUMMARY.md                             │
│   ** CHECKPOINT: User approves/edits merge decisions **         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2b: Apply Approved Merges                                  │
│   Input: review/proposed_merges.csv (user-reviewed)             │
│   Output: merged/merged_inventory.csv                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Identify Baseline Matches (NO AUTO-FLAG)                │
│   Output: review/baseline_matches.csv ← ** USER REVIEWS THIS ** │
│   Summary: docs/03_BASELINE_SUMMARY.md                          │
│   ** CHECKPOINT: User verifies baseline matches are correct **  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3b: Apply Baseline Flags                                   │
│   Input: review/baseline_matches.csv (user-reviewed)            │
│   Output: final/final_merged_inventory.csv                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Generate Final Report                                   │
│   Output: docs/FINAL_REPORT.md                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Setup Directory Structure

Create the directory structure and copy required scripts.

**Scripts to copy from `unified_bioresource_pipeline/scripts/phase7_deduplication/`:**
- `17_deduplicate_all_sets.py` → base for `02_merge_batches.py`

**Scripts to copy from `unified_bioresource_pipeline/scripts/phase8_baseline/`:**
- `20_baseline_comparison.py` → base for `03_baseline_comparison.py`

---

## Step 1: Filter Live URLs (Script 01)

### Logic

```python
# Filter criteria: extracted_url_status == "200"
# Do NOT include Wayback URLs (per user requirement)

def filter_live_urls(df):
    return df[df['extracted_url_status'] == '200'].copy()
```

### Input/Output

| Input | Output |
|-------|--------|
| 2010-2022 batch (1,688 rows) | `filtered/batch_2010_2022_live.csv` (~996 rows) |
| 2022-2025 batch (1,510 rows) | `filtered/batch_2022_2025_live.csv` (~1,510 rows) |

### Column Schema Alignment

Both files have same schema (24-28 columns). Key columns to preserve:
- `ID` (PMID)
- `best_name`, `best_common`, `best_full`
- `extracted_url`, `extracted_url_status`
- `article_count`, `num_citations`
- `publication_date`, `authors`, `affiliation`

Add source tracking column:
- `source_batch`: "2010-2022" or "2022-2025"

### Summary Output: `docs/01_FILTER_SUMMARY.md`

```markdown
# Step 1: URL Filtering Summary

## Results
| Batch | Input | Live URLs | Filtered Out | Retention |
|-------|-------|-----------|--------------|-----------|
| 2010-2022 | 1,688 | 996 | 692 | 59.0% |
| 2022-2025 | 1,510 | 1,510 | 0 | 100.0% |
| **Total** | **3,198** | **2,506** | **692** | **78.4%** |

## Sample Filtered Records (first 10 removed)
| best_name | extracted_url | status | reason |
|-----------|---------------|--------|--------|
| ... | ... | 404 | Not found |

## Ready for Step 2?
Review the above. If satisfied, proceed to deduplication.
```

---

## Step 2: Identify Duplicates (Script 02) - WITH REVIEW

### Deduplication Strategy

**Duplicate detection key:** `normalized_url + '||' + normalized_entity_name`

### Functions to Reuse from Script 17

```python
# From 17_deduplicate_all_sets.py:
- normalize_url_strict()      # Lines 262-294
- normalize_url_aggressive()  # Lines 236-259
- compute_url_similarity()    # Lines 310-376
- cluster_similar_urls()      # Lines 411-511 (with domain blocking)
- normalize_entity()          # Lines 386-405
```

### Review File: `review/proposed_merges.csv`

**This file is for USER REVIEW before any merging happens.**

| Column | Description |
|--------|-------------|
| `merge_group_id` | Unique ID for each duplicate group |
| `row_id` | Original row identifier |
| `best_name` | Resource name |
| `extracted_url` | URL |
| `source_batch` | "2010-2022" or "2022-2025" |
| `url_similarity` | Score 0-1 showing how similar URLs are |
| `entity_similarity` | Score 0-1 for name match |
| `recommendation` | "MERGE" / "REVIEW" / "KEEP_SEPARATE" |
| `user_decision` | **USER FILLS THIS**: "merge" / "keep" / blank |

**Example rows:**
```csv
merge_group_id,row_id,best_name,extracted_url,source_batch,url_similarity,recommendation,user_decision
1,A_123,GenBank,ncbi.nlm.nih.gov/genbank,2010-2022,1.0,MERGE,
1,B_456,GenBank,ncbi.nlm.nih.gov/genbank/,2022-2025,1.0,MERGE,
2,A_789,BRENDA,brenda-enzymes.org,2010-2022,0.92,REVIEW,
2,B_101,Brenda Enzyme DB,brenda-enzymes.info,2022-2025,0.92,REVIEW,
```

### Summary Output: `docs/02_DEDUP_SUMMARY.md`

```markdown
# Step 2: Deduplication Review

## Duplicate Groups Found
| Category | Count | Action Needed |
|----------|-------|---------------|
| High confidence (similarity >= 0.95) | 85 | Auto-recommend MERGE |
| Medium confidence (0.80-0.95) | 32 | Review recommended |
| Low confidence (< 0.80) | 15 | Keep separate by default |
| **Total duplicate pairs** | **132** | |

## Cross-Batch vs Same-Batch
| Type | Count |
|------|-------|
| Cross-batch duplicates (2010-2022 ↔ 2022-2025) | 98 |
| Same-batch duplicates | 34 |

## Action Required
1. Open `review/proposed_merges.csv`
2. Review rows where `recommendation = "REVIEW"`
3. Fill in `user_decision` column: "merge" or "keep"
4. Save and run Step 2b to apply decisions
```

### Step 2b: Apply Approved Merges (Script 02b)

After user reviews `proposed_merges.csv`:

**Merge logic for approved merges:**
1. Combine PMIDs (comma-separated)
2. Sum `article_count`
3. Keep higher `num_citations`
4. Keep earliest `publication_date`
5. Concatenate `paper_titles` with separator
6. Track source batches (e.g., "2010-2022, 2022-2025")

**Output:** `merged/merged_inventory.csv`

### Expected Results

| Metric | Estimate |
|--------|----------|
| Total input (filtered) | ~2,506 rows |
| Cross-batch duplicates | ~100-200 |
| Final deduplicated | ~2,300-2,400 rows |

---

## Step 3: Baseline Comparison (Script 03) - WITH REVIEW

### GBC Baseline File

**Path:** `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`
**Records:** 4,560
**Key columns:**
- `pubmed_id` → matches our `ID`
- `resource_short_name` → matches our `best_name` / `best_common`
- `resource_full_name` → matches our `best_full`

### Baseline Matching Logic

```python
# Method 1: PMID match
in_gbc_pmid = merged_df['ID'].isin(gbc_baseline['pubmed_id'])

# Method 2: Entity name match (normalized)
in_gbc_entity = merged_df['best_name_normalized'].isin(
    gbc_baseline['resource_short_name_normalized']
)

# Combined flag
in_gbc_baseline = in_gbc_pmid | in_gbc_entity
```

### Review File: `review/baseline_matches.csv`

**This file shows ALL matches for USER REVIEW before flagging as "in baseline".**

| Column | Description |
|--------|-------------|
| `our_row_id` | Row ID from merged inventory |
| `our_best_name` | Our resource name |
| `our_url` | Our extracted URL |
| `gbc_resource_id` | Matched GBC resource ID |
| `gbc_short_name` | GBC resource short name |
| `gbc_full_name` | GBC resource full name |
| `match_type` | "PMID" / "ENTITY_NAME" / "BOTH" |
| `match_confidence` | "HIGH" / "MEDIUM" / "LOW" |
| `user_confirms` | **USER FILLS THIS**: "yes" / "no" / blank |

**Example rows:**
```csv
our_row_id,our_best_name,our_url,gbc_resource_id,gbc_short_name,match_type,match_confidence,user_confirms
M_001,UniProt,uniprot.org,1234,UniProt,BOTH,HIGH,
M_002,PDB,rcsb.org/pdb,2345,PDB,ENTITY_NAME,HIGH,
M_003,MyDB,mydb.edu,3456,MyDatabase,ENTITY_NAME,MEDIUM,
```

### Summary Output: `docs/03_BASELINE_SUMMARY.md`

```markdown
# Step 3: Baseline Comparison Review

## Match Statistics
| Match Type | Count | Confidence |
|------------|-------|------------|
| PMID match only | 156 | HIGH |
| Entity name match only | 89 | MEDIUM |
| Both PMID + Entity | 234 | HIGH |
| **Total matches** | **479** | |

## Novel Resources (NOT in GBC baseline)
| Count |
|-------|
| ~1,900 resources |

## Action Required
1. Open `review/baseline_matches.csv`
2. Review entity-name-only matches (may have false positives)
3. Fill `user_confirms` column: "yes" to confirm match, "no" to reject
4. Save and run Step 3b to apply decisions
```

### Step 3b: Apply Baseline Flags (Script 03b)

After user reviews `baseline_matches.csv`:

**Output Columns Added:**
- `in_gbc_pmid`: Boolean (PMID matched)
- `in_gbc_entity`: Boolean (entity name matched AND user confirmed)
- `in_gbc_baseline`: Boolean (either match confirmed)
- `is_novel`: Boolean (NOT in_gbc_baseline)
- `gbc_resource_id`: Matched GBC ID (if in baseline)

**Output:** `final/final_merged_inventory.csv`

---

## Phase 5: Generate Report (Script 04)

### Statistics to Calculate

1. **Filtering stats:**
   - 2010-2022: X filtered to Y (Z% live)
   - 2022-2025: X filtered to Y (Z% live)

2. **Deduplication stats:**
   - Total combined: X
   - Cross-batch duplicates found: Y
   - Final unique: Z

3. **Baseline comparison:**
   - In GBC baseline (PMID match): X
   - In GBC baseline (entity match): Y
   - Total in baseline: Z
   - Novel discoveries: W

### Output Files

- `final/final_merged_inventory.csv` - Main output
- `final/novel_resources.csv` - Resources NOT in GBC baseline
- `final/baseline_matches.csv` - Resources IN GBC baseline
- `docs/FINAL_REPORT.md` - Human-readable summary
- `docs/statistics.json` - Machine-readable stats

---

## Execution Steps (with Review Checkpoints)

```bash
cd unified_bioresource_pipeline/final_merged_batch

# ─────────────────────────────────────────────────────────────
# STEP 1: Filter to live URLs only
# ─────────────────────────────────────────────────────────────
python scripts/01_filter_live_urls.py
# → Outputs: data/filtered/*.csv, docs/01_FILTER_SUMMARY.md
# → CHECKPOINT: Review summary, then proceed

# ─────────────────────────────────────────────────────────────
# STEP 2: Identify duplicates (generates review file)
# ─────────────────────────────────────────────────────────────
python scripts/02_identify_duplicates.py
# → Outputs: data/review/proposed_merges.csv, docs/02_DEDUP_SUMMARY.md
# → CHECKPOINT: Review proposed_merges.csv
#   - Edit user_decision column for rows needing review
#   - Save file when done

# STEP 2b: Apply your merge decisions
python scripts/02b_apply_merges.py
# → Outputs: data/merged/merged_inventory.csv

# ─────────────────────────────────────────────────────────────
# STEP 3: Identify baseline matches (generates review file)
# ─────────────────────────────────────────────────────────────
python scripts/03_identify_baseline.py
# → Outputs: data/review/baseline_matches.csv, docs/03_BASELINE_SUMMARY.md
# → CHECKPOINT: Review baseline_matches.csv
#   - Verify entity-name-only matches are correct
#   - Edit user_confirms column if needed
#   - Save file when done

# STEP 3b: Apply baseline flags
python scripts/03b_apply_baseline.py
# → Outputs: data/final/final_merged_inventory.csv

# ─────────────────────────────────────────────────────────────
# STEP 4: Generate final report
# ─────────────────────────────────────────────────────────────
python scripts/04_generate_report.py
# → Outputs: docs/FINAL_REPORT.md, data/final/novel_resources.csv
```

**Estimated runtime:**
- Automated steps: ~5 minutes total
- Review time: Depends on number of items needing review

---

## Critical Files to Modify/Create

### New Files to Create

1. `final_merged_batch/scripts/01_filter_live_urls.py` - Filter to HTTP 200 only
2. `final_merged_batch/scripts/02_identify_duplicates.py` - Find duplicates, generate review file
3. `final_merged_batch/scripts/02b_apply_merges.py` - Apply user-reviewed merge decisions
4. `final_merged_batch/scripts/03_identify_baseline.py` - Find baseline matches, generate review file
5. `final_merged_batch/scripts/03b_apply_baseline.py` - Apply user-reviewed baseline flags
6. `final_merged_batch/scripts/04_generate_report.py` - Final statistics and report
7. `final_merged_batch/README.md` - Usage instructions
8. `final_merged_batch/plan/MERGE_PLAN.md` - Copy of this plan

### Source Files to Reference

1. `unified_bioresource_pipeline/scripts/phase7_deduplication/17_deduplicate_all_sets.py` (1,083 lines)
   - URL normalization functions
   - URL clustering with domain blocking
   - Entity normalization
   - Merge logic

2. `unified_bioresource_pipeline/scripts/phase8_baseline/20_baseline_comparison.py` (432 lines)
   - PMID matching
   - Entity matching
   - Statistics generation

---

## Key Implementation Notes

1. **URL Status Filter:** Use exact string match `extracted_url_status == "200"` (not numeric comparison - column contains mixed types)

2. **Column Schema:** 2022-2025 batch has 4 extra QC columns - these should be preserved in merged output

3. **GBC Baseline Format:** Has different column names - need mapping:
   - `pubmed_id` → `ID`
   - `resource_short_name` → `best_name`
   - `resource_full_name` → `best_full`

4. **Domain Blocking:** Preserve the domain blocking optimization from script 17 to prevent false merges on generic domains (`.edu`, `.ac.uk`, etc.)

5. **Merge Preference:** When merging duplicates, prefer data from the record with better metadata coverage (more non-null fields)
