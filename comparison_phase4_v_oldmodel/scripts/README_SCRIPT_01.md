# Script 01: Preprocess and Align

## Overview

This script performs the initial data preprocessing and alignment for the Phase 4 vs V2 NER comparison analysis. It loads all datasets, detects and cleans BPE tokenization artifacts, and aligns papers by ID to create a unified dataset for downstream analysis.

## Features

### Core Functionality

1. **Data Loading**
   - V2 (old model) NER results
   - Phase 4 (new model) NER results
   - NER test split ground truth
   - Final inventory metadata

2. **Entity Parsing**
   - Converts string/JSON entity representations to Python lists
   - Handles comma-separated and JSON array formats
   - Cleans empty and malformed entries

3. **BPE Artifact Detection & Cleaning**
   - Detects "Ġ" prefix markers (GPT-2 style tokenization)
   - Identifies subword tokenization patterns
   - Cleans artifacts while preserving valid biological abbreviations
   - Generates contamination statistics

4. **Data Alignment**
   - Merges all datasets by paper ID
   - Preserves ground truth where available
   - Creates unified columns for comparison

5. **Statistics Generation**
   - Entity count distributions across systems
   - Coverage analysis
   - Contamination metrics

## Usage

### Basic Usage

```bash
# Run with default paths (recommended)
python 01_preprocess_and_align.py

# Run with verbose output
python 01_preprocess_and_align.py --verbose
```

### Custom Paths

```bash
# Use custom input paths
python 01_preprocess_and_align.py \
    --v2-path /path/to/v2_results.csv \
    --phase4-path /path/to/phase4_results.csv \
    --test-split-path /path/to/test_ner.csv \
    --inventory-path /path/to/inventory.csv \
    --output-dir /path/to/output
```

### Advanced Options

```bash
# Skip BPE cleaning (for debugging)
python 01_preprocess_and_align.py --skip-bpe-cleaning

# Custom output directory
python 01_preprocess_and_align.py --output-dir ./custom_output
```

## Input Files

### Required Files (Default Locations)

1. **V2 NER Results**
   - Path: `collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/ner_results.csv`
   - Contains: Old model predictions (common_name, full_name)

2. **Phase 4 NER Results**
   - Path: `experiment_archives/2025-11-05-poq5i4_phase4_2022_rerun/ner_results.csv`
   - Contains: New model predictions with enhanced post-processing

3. **NER Test Split**
   - Path: `data/ner_splits_full/test_ner.csv`
   - Contains: Ground truth annotations for evaluation

4. **Final Inventory**
   - Path: `data/final_inventory_2022.csv`
   - Contains: Paper metadata (title, abstract, etc.)

## Output Files

### Generated Files (Default: `../data/`)

1. **aligned_papers.csv**
   - Unified dataset with all systems' outputs
   - Columns:
     - `paper_id`: PubMed ID
     - `title`: Paper title
     - `abstract`: Paper abstract
     - `true_com`: Ground truth common names (list)
     - `true_ful`: Ground truth full names (list)
     - `v2_com`: V2 predicted common names (list)
     - `v2_ful`: V2 predicted full names (list)
     - `p4_com_raw`: Phase 4 raw common names (list)
     - `p4_com_clean`: Phase 4 cleaned common names (list)
     - `p4_ful_raw`: Phase 4 raw full names (list)
     - `p4_ful_clean`: Phase 4 cleaned full names (list)

2. **bpe_artifact_report.json**
   - Contamination statistics
   - Example artifacts with before/after cleaning
   - Artifact type counts

3. **entity_counts.csv**
   - Entity count distributions per system
   - Mean/median/std statistics
   - Coverage percentages

### Log File

- `01_preprocess_and_align.log`: Detailed execution log

## Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--v2-path` | Path | Auto | Path to V2 NER results CSV |
| `--phase4-path` | Path | Auto | Path to Phase 4 NER results CSV |
| `--test-split-path` | Path | Auto | Path to NER test split CSV |
| `--inventory-path` | Path | Auto | Path to final inventory CSV |
| `--output-dir` | Path | `../data` | Output directory for results |
| `--skip-bpe-cleaning` | Flag | False | Skip BPE artifact cleaning |
| `--verbose` | Flag | False | Enable verbose logging |

## Processing Steps

### Step 1: Load Datasets
- Loads all four required datasets
- Validates file existence and format
- Reports row counts and columns

### Step 2: Parse Entity Columns
- Converts string representations to lists
- Handles JSON arrays and comma-separated strings
- Cleans empty entries

### Step 3: Detect & Clean BPE Artifacts
- Analyzes Phase 4 data for BPE contamination
- Detects "Ġ" markers and subword patterns
- Cleans artifacts using smart heuristics
- Preserves biological abbreviations (T cell, IL-6, etc.)
- Generates contamination report

### Step 4: Align Papers by ID
- Merges V2 and Phase 4 results
- Adds ground truth where available
- Creates unified paper ID index
- Reports coverage statistics

### Step 5: Generate Entity Statistics
- Calculates entity counts per system
- Computes distribution statistics
- Identifies coverage gaps

### Step 6: Save Outputs
- Writes aligned dataset
- Saves BPE report
- Exports entity statistics
- Creates log file

## BPE Artifact Cleaning

### What are BPE Artifacts?

BPE (Byte-Pair Encoding) artifacts are tokenization remnants that contaminate NER outputs:
- "Ġ" prefix markers (e.g., "Ġprotein" → "protein")
- Subword splits (e.g., "pro te in" → "protein")

### Cleaning Strategy

1. **Primary Detection**: "Ġ" marker presence
2. **Secondary Detection**: Multiple consecutive short tokens
3. **Smart Cleaning**:
   - Remove "Ġ" markers
   - Merge subword fragments
   - Preserve valid abbreviations
4. **Whitelist**: T, B, IL, A, C, G, E (biological tokens)

### Example Transformations

```
"Ġprotein ĠA"        → "protein A"
"ĠRat ĠGen ome"      → "Rat Genome"
"T cell"             → "T cell"        (preserved)
"IL-6"               → "IL-6"          (preserved)
"Ġwaste Ġwater"      → "waste water"
```

## Expected Output

### Console Output

```
================================================================================
Phase 4 vs V2 NER Comparison: Preprocessing and Alignment
================================================================================
Output directory: ../data
BPE cleaning: ENABLED

================================================================================
STEP 1: Loading Datasets
================================================================================

[1/4] Loading V2 (old model) NER results...
✓ Loaded 20,805 V2 results

[2/4] Loading Phase 4 (new model) NER results...
✓ Loaded 20,805 Phase 4 results

[3/4] Loading NER test split ground truth...
✓ Loaded 400 test samples

[4/4] Loading final inventory...
✓ Loaded 20,805 papers in inventory

✓ All datasets loaded successfully

================================================================================
STEP 2: Parsing Entity Columns
================================================================================
...

================================================================================
FINAL SUMMARY
================================================================================

📊 Dataset Statistics:
  Total papers aligned: 20,805
  Papers with ground truth: 400
  Papers with V2 results: 20,805
  Papers with Phase 4 results: 20,805

🔍 BPE Contamination:
  Common name papers contaminated: 18,234 (87.6%)
  Full name papers contaminated: 1,245 (6.0%)

✅ Preprocessing complete! Ready for comparison analysis.
   Next step: Run 02_entity_level_comparison.py
```

## Error Handling

### Common Errors

1. **FileNotFoundError**: Input file doesn't exist
   - Check file paths
   - Verify experiment IDs in filenames

2. **EmptyDataError**: Input file is empty
   - Verify files contain data
   - Check CSV format

3. **MemoryError**: Insufficient memory
   - Process large files in chunks
   - Close other applications

### Troubleshooting

```bash
# Verify input files exist
ls -lh collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/ner_results.csv
ls -lh experiment_archives/2025-11-05-poq5i4_phase4_2022_rerun/ner_results.csv
ls -lh data/ner_splits_full/test_ner.csv
ls -lh data/final_inventory_2022.csv

# Check log file for details
tail -100 01_preprocess_and_align.log

# Run with verbose output
python 01_preprocess_and_align.py --verbose
```

## Dependencies

### Required Packages
- pandas >= 1.3.0
- tqdm >= 4.62.0

### Utility Modules
- utils.data_loading
- utils.bpe_cleaning
- utils.entity_matching (indirectly)
- utils.metrics (indirectly)

## Performance

### Typical Execution Time
- Small dataset (100 papers): ~1 second
- Medium dataset (1,000 papers): ~5 seconds
- Large dataset (20,000+ papers): ~30 seconds

### Memory Usage
- ~100 MB for 20,000 papers
- Scales linearly with dataset size

## Next Steps

After running this script:

1. **Review Outputs**
   - Check `aligned_papers.csv` for completeness
   - Examine `bpe_artifact_report.json` for contamination levels
   - Review `entity_counts.csv` for distributions

2. **Run Entity Comparison**
   - Execute `02_entity_level_comparison.py`
   - Generates precision/recall/F1 metrics
   - Performs entity-level matching

3. **Generate Visualizations**
   - Run visualization scripts
   - Create comparison plots
   - Produce summary reports

## Author

- **Script**: Claude Code
- **Date**: 2025-11-05
- **Version**: 1.0.0
- **Project**: Phase 4 vs V2 NER Comparison

## License

Internal research use only.
