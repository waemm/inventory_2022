# Final Merged Batch Pipeline

Pipeline for filtering, merging, and deduplicating the 2010-2022 and 2022-2025 bioresource inventory batches.

## Quick Start

```bash
# Step 1: Filter to live URLs only
python scripts/01_filter_live_urls.py

# Step 2: Identify duplicates (generates review file)
python scripts/02_identify_duplicates.py
# --> Review: review/proposed_merges.csv

# Step 2b: Apply merge decisions
python scripts/02b_apply_merges.py

# Step 3: Compare against GBC baseline (generates review file)
python scripts/03_identify_baseline.py
# --> Review: review/baseline_matches.csv

# Step 3b: Apply baseline flags
python scripts/03b_apply_baseline.py

# Step 4: Generate final report
python scripts/04_generate_report.py
```

## Directory Structure

```
final_merged_batch/
├── README.md              # This file
├── plan/
│   └── MERGE_PLAN.md      # Detailed implementation plan
├── scripts/
│   ├── 01_filter_live_urls.py
│   ├── 02_identify_duplicates.py
│   ├── 02b_apply_merges.py
│   ├── 03_identify_baseline.py
│   ├── 03b_apply_baseline.py
│   └── 04_generate_report.py
├── data/
│   ├── filtered/          # Step 1 output
│   ├── combined/          # Step 2 output
│   ├── deduplicated/      # Step 2b output
│   └── final/             # Final inventory
├── review/
│   ├── proposed_merges.csv    # Duplicate review
│   └── baseline_matches.csv   # Baseline review
└── docs/
    ├── 01_FILTER_SUMMARY.md
    ├── 02_DUPLICATE_SUMMARY.md
    ├── 02b_MERGE_APPLIED_SUMMARY.md
    ├── 03_BASELINE_SUMMARY.md
    ├── 03b_BASELINE_APPLIED_SUMMARY.md
    └── FINAL_REPORT.md
```

## Review Checkpoints

The pipeline has two review checkpoints where you can verify results before proceeding:

### 1. Duplicate Review (`review/proposed_merges.csv`)

After Step 2, review the proposed merges:

| Column | Description |
|--------|-------------|
| `merge_group_id` | ID grouping duplicate records |
| `best_name` | Resource name |
| `extracted_url` | Resource URL |
| `recommendation` | MERGE, LIKELY_MERGE, or REVIEW |
| `user_decision` | Fill in: MERGE or KEEP_SEPARATE |

### 2. Baseline Review (`review/baseline_matches.csv`)

After Step 3, review the baseline matches:

| Column | Description |
|--------|-------------|
| `match_type` | PMID, NAME_EXACT, NAME_FUZZY, or NO_MATCH |
| `recommendation` | IN_BASELINE, LIKELY_IN_BASELINE, REVIEW, or NEW_RESOURCE |
| `user_decision` | Fill in: IN_BASELINE or NEW_RESOURCE |

## Input Files

- **2010-2022 batch**: `unified_bioresource_pipeline/post_processing/results/final_inventory_QC_FIXED.csv`
- **2022-2025 batch**: `unified_bioresource_pipeline/2025-12-04-111420-z381s/post_processing/final_inventory_QC_FIXED.csv`
- **GBC baseline**: `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`

## Output Files

- `data/final/final_inventory.csv` - Complete merged inventory
- `data/final/new_resources_only.csv` - New discoveries (not in baseline)
- `docs/FINAL_REPORT.md` - Comprehensive statistics
