# Utils Library - Phase 4 vs V2 NER Comparison

Production-quality utility library for comparing Phase 4 and V2 NER results.

## Overview

This library provides comprehensive utilities for:
- **Data Loading**: Load NER results, test splits, and inventory data
- **Entity Matching**: Match entities using multiple strategies (exact, fuzzy, partial, token overlap)
- **Metrics Calculation**: Compute precision, recall, F1, confidence intervals
- **BPE Cleaning**: Detect and clean BPE tokenization artifacts

## Module Structure

```
utils/
├── __init__.py              # Package initialization with all exports
├── data_loading.py          # Load V2, Phase 4, test split, inventory data
├── entity_matching.py       # Entity matching strategies
├── metrics.py               # Evaluation metrics and statistics
├── bpe_cleaning.py          # BPE artifact detection and cleaning
└── README.md               # This file
```

## Installation

No installation needed - just import from the scripts directory:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils import load_v2_results, match_entities, calculate_precision_recall_f1
```

## Quick Start

### 1. Loading Data

```python
from utils import load_v2_results, load_phase4_results, load_ner_test_split

# Load NER results
v2_df = load_v2_results()
phase4_df = load_phase4_results()
test_df = load_ner_test_split()

print(f"Loaded {len(v2_df)} V2 results, {len(phase4_df)} Phase 4 results")
```

### 2. Parsing Entities

```python
from utils import parse_entity_list

# Parse comma-separated entities
entities = parse_entity_list("protein A, gene B, compound C")
# ['protein A', 'gene B', 'compound C']

# Parse JSON format
entities = parse_entity_list('["protein A", "gene B"]')
# ['protein A', 'gene B']

# Handle empty/None
entities = parse_entity_list(None)
# []
```

### 3. Matching Entities

```python
from utils import match_entities, exact_match, fuzzy_match

# Simple matching
if exact_match("Protein A", "protein a"):
    print("Match!")

# Match entity lists
predicted = ["protein A", "gene B", "compound C"]
true = ["protein A", "gene B", "gene D"]

results = match_entities(predicted, true)
print(f"Matched: {results['match_count']}")
print(f"Unmatched predicted: {results['unmatched_1']}")
print(f"Unmatched true: {results['unmatched_2']}")
```

### 4. Calculating Metrics

```python
from utils import calculate_precision_recall_f1, entity_level_metrics

# From confusion matrix counts
metrics = calculate_precision_recall_f1(tp=80, fp=10, fn=10)
print(f"F1: {metrics['f1']:.3f}")  # F1: 0.889

# Entity-level metrics
predicted_ents = ["protein A", "gene B", "compound C"]
true_ents = ["protein A", "gene B", "gene D"]

metrics = entity_level_metrics(predicted_ents, true_ents)
print(f"Precision: {metrics['precision']:.3f}")
print(f"Recall: {metrics['recall']:.3f}")
print(f"F1: {metrics['f1']:.3f}")
```

### 5. Cleaning BPE Artifacts

```python
from utils import detect_bpe_artifacts, clean_bpe_entity, clean_bpe_dataframe

# Detect artifacts
if detect_bpe_artifacts("Ġprotein"):
    print("BPE artifact detected!")

# Clean single entity
cleaned = clean_bpe_entity("Ġprotein")
print(cleaned)  # "protein"

# Clean entire DataFrame
import pandas as pd
df = pd.DataFrame({'entities': ['Ġprotein', 'gene A', 'ĠIL-6']})
cleaned_df = clean_bpe_dataframe(df, entity_column='entities')
print(cleaned_df['entities_cleaned'].tolist())
# ['protein', 'gene A', 'IL-6']
```

## Module Details

### data_loading.py

Functions for loading data from various sources:

- **`load_v2_results()`**: Load V2 (old model) NER results
  - Default: `collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/ner_results.csv`

- **`load_phase4_results()`**: Load Phase 4 (new model) NER results
  - Default: `experiment_archives/2025-11-05-ygnr9f_phase4_2022_rerun/ner_results.csv`

- **`load_ner_test_split()`**: Load NER test split ground truth
  - Default: `data/ner_splits_full/test_ner.csv`

- **`load_inventory()`**: Load final inventory metadata
  - Default: `data/final_inventory_2022.csv`

- **`parse_entity_list()`**: Parse entity strings (comma-separated or JSON)

All functions:
- Handle missing files with clear error messages
- Support custom file paths
- Use UTF-8 encoding
- Log loading progress

### entity_matching.py

Functions for matching entities between datasets:

- **`exact_match(entity1, entity2)`**: Case-insensitive exact match
  - Normalizes whitespace and case
  - Returns: `True` if exact match

- **`partial_match(entity1, entity2)`**: Substring matching
  - Checks if one entity contains the other
  - Minimum length threshold to avoid spurious matches
  - Returns: `True` if substring match

- **`fuzzy_match(entity1, entity2)`**: Levenshtein distance ≤ 2
  - Uses dynamic programming for efficient computation
  - Handles typos and minor variations
  - Returns: `True` if distance ≤ threshold

- **`token_overlap(entity1, entity2)`**: Jaccard similarity
  - Computes word token overlap
  - Threshold default: 0.5
  - Returns: `True` if Jaccard ≥ threshold

- **`match_entities(entities1, entities2)`**: Match entity lists
  - Tries all strategies in order
  - Returns detailed match results
  - Includes per-strategy counts

### metrics.py

Functions for calculating evaluation metrics:

- **`calculate_precision_recall_f1(tp, fp, fn)`**: Core metrics
  - Handles division by zero
  - Supports F-beta scores
  - Returns: dict with precision, recall, F1

- **`entity_level_metrics(predicted, true)`**: Entity-level evaluation
  - Uses entity matching under the hood
  - Supports different match strategies
  - Returns: complete metric dict

- **`confusion_matrix(y_true, y_pred)`**: Create confusion matrix
  - Returns pandas DataFrame
  - Works for binary and multi-class

- **`bootstrap_confidence_interval(scores)`**: Compute CI
  - Uses bootstrap resampling (default: 10,000 samples)
  - Configurable confidence level (default: 95%)
  - Returns: mean, std, lower, upper bounds

Additional utilities:
- **`micro_average_metrics()`**: Micro-averaging across samples
- **`macro_average_metrics()`**: Macro-averaging across samples
- **`aggregate_metrics()`**: Convenience function for both

### bpe_cleaning.py

Functions for detecting and cleaning BPE artifacts:

- **`detect_bpe_artifacts(entity)`**: Check for BPE contamination
  - Detects "Ġ" prefix markers
  - Identifies suspicious short token sequences
  - Returns: `True` if artifacts detected

- **`clean_bpe_entity(entity)`**: Clean single entity
  - Removes "Ġ" markers
  - Merges subword tokens
  - Normalizes whitespace
  - Returns: cleaned entity string

- **`clean_bpe_dataframe(df)`**: Clean entire DataFrame
  - Creates new column or modifies in-place
  - Handles various entity formats (lists, comma-separated)
  - Returns: DataFrame with cleaned entities

- **`generate_bpe_report(df)`**: Generate contamination report
  - Row-level and entity-level statistics
  - Artifact type breakdown
  - Example contaminated entities
  - Returns: comprehensive report dict

## Usage Examples

### Complete Evaluation Pipeline

```python
from utils import (
    load_v2_results,
    load_phase4_results,
    load_ner_test_split,
    parse_entity_list,
    entity_level_metrics,
    aggregate_metrics,
    clean_bpe_dataframe,
    generate_bpe_report
)

# Load data
print("Loading data...")
v2_df = load_v2_results()
phase4_df = load_phase4_results()
test_df = load_ner_test_split()

# Check for BPE contamination
print("\nChecking Phase 4 for BPE artifacts...")
phase4_report = generate_bpe_report(phase4_df, entity_column='entities')
print(f"Contamination rate: {phase4_report['entity_contamination_rate']:.1%}")

# Clean if needed
if phase4_report['entity_contamination_rate'] > 0:
    print("Cleaning Phase 4 entities...")
    phase4_df = clean_bpe_dataframe(phase4_df, entity_column='entities')

# Evaluate each model
print("\nEvaluating models...")
per_sample_metrics = []

for idx, row in test_df.iterrows():
    true_entities = parse_entity_list(row['entities'])

    # Get predictions for this sample
    v2_pred = parse_entity_list(v2_df.loc[v2_df['pmid'] == row['pmid'], 'entities'].values[0])
    phase4_pred = parse_entity_list(phase4_df.loc[phase4_df['pmid'] == row['pmid'], 'entities'].values[0])

    # Calculate metrics
    v2_metrics = entity_level_metrics(v2_pred, true_entities)
    phase4_metrics = entity_level_metrics(phase4_pred, true_entities)

    per_sample_metrics.append({
        'pmid': row['pmid'],
        'v2_f1': v2_metrics['f1'],
        'phase4_f1': phase4_metrics['f1'],
        'v2_metrics': v2_metrics,
        'phase4_metrics': phase4_metrics,
    })

# Aggregate results
print("\nAggregating results...")
v2_aggregate = aggregate_metrics([m['v2_metrics'] for m in per_sample_metrics])
phase4_aggregate = aggregate_metrics([m['phase4_metrics'] for m in per_sample_metrics])

print(f"\nV2 Results:")
print(f"  Micro F1: {v2_aggregate['micro']['f1']:.3f}")
print(f"  Macro F1: {v2_aggregate['macro']['f1']:.3f}")
print(f"  95% CI: [{v2_aggregate['ci']['lower']:.3f}, {v2_aggregate['ci']['upper']:.3f}]")

print(f"\nPhase 4 Results:")
print(f"  Micro F1: {phase4_aggregate['micro']['f1']:.3f}")
print(f"  Macro F1: {phase4_aggregate['macro']['f1']:.3f}")
print(f"  95% CI: [{phase4_aggregate['ci']['lower']:.3f}, {phase4_aggregate['ci']['upper']:.3f}]")
```

### Custom Matching Strategy

```python
from utils import match_entities, get_match_statistics

predicted = ["protein kinase A", "interleukin 6", "tumor necrosis factor"]
true = ["kinase A protein", "IL-6", "TNF"]

# Try different strategies
for strategy in ['exact', 'fuzzy', 'partial', 'token_overlap']:
    results = match_entities(predicted, true, strategies=[strategy])
    print(f"\n{strategy.upper()} matching:")
    print(f"  Matches: {results['match_count']}")
    print(f"  Matched pairs: {results['matched_pairs']}")

# Try all strategies (default behavior)
results = match_entities(predicted, true)
stats = get_match_statistics(results)

print(f"\nBest matches: {results['match_count']}")
print("Strategy breakdown:")
for strategy, count in stats['strategy_counts'].items():
    if count > 0:
        print(f"  {strategy}: {count} ({stats['strategy_percentages'][strategy]:.1%})")
```

## Error Handling

All functions include comprehensive error handling:

```python
from utils import load_v2_results

try:
    df = load_v2_results()
except FileNotFoundError:
    print("Results file not found")
except pd.errors.EmptyDataError:
    print("Results file is empty")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing

Run the test suite:

```bash
cd comparison_phase4_v_oldmodel/scripts
python test_utils_import.py
```

This will:
1. Verify all modules import correctly
2. Check that all functions are available
3. Run basic functional tests
4. Confirm the library is ready to use

## Performance Notes

- **Data Loading**: Uses pandas with UTF-8 encoding, handles large files efficiently
- **Entity Matching**: O(n×m) worst case, but early termination optimizations included
- **Fuzzy Matching**: Dynamic programming implementation, O(n×m) per comparison
- **Bootstrap CI**: Default 10,000 samples, adjust `n_bootstrap` for speed/accuracy tradeoff

## Dependencies

- **pandas**: Data loading and manipulation
- **numpy**: Numerical operations and statistics
- **logging**: Comprehensive logging throughout

All dependencies are standard and should be available in the project environment.

## Logging

Enable detailed logging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now all utils functions will log their progress
from utils import load_v2_results
df = load_v2_results()  # Will log loading progress
```

## Contributing

When adding new functions:
1. Include comprehensive docstrings with examples
2. Add type hints for all parameters and return values
3. Handle edge cases (None, empty lists, division by zero)
4. Add logging at appropriate levels
5. Update `__init__.py` to export new functions
6. Add tests to `test_utils_import.py`

## Version History

- **1.0.0** (2025-11-05): Initial release
  - Data loading utilities
  - Entity matching (4 strategies)
  - Metrics calculation
  - BPE cleaning utilities

## License

Part of the GBC Inventory 2022 project.
