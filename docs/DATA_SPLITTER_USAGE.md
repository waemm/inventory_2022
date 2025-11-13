# NER Data Splitter by Entity Length

## Overview

`src/data_splitter.py` splits NER training/validation/test datasets based on entity length, enabling targeted model training and evaluation for different entity complexity levels.

## Created Files

The script has been successfully executed and created two sets of data splits:

### Short Entities (≤2 words)
- **Location**: `data/ner_splits_short/`
- **Files**:
  - `train_ner.pkl` / `train_ner.csv` (1,009 sentences, 1,176 entities)
  - `val_ner.pkl` / `val_ner.csv` (219 sentences, 262 entities)
  - `test_ner.pkl` / `test_ner.csv` (245 sentences, 282 entities)
- **Total**: 1,473 sentences with 1,720 entities (91.6% ≤2 words, 8.4% >2 words)

### Long Entities (>2 words)
- **Location**: `data/ner_splits_long/`
- **Files**:
  - `train_ner.pkl` / `train_ner.csv` (120 sentences, 227 entities)
  - `val_ner.pkl` / `val_ner.csv` (26 sentences, 45 entities)
  - `test_ner.pkl` / `test_ner.csv` (33 sentences, 57 entities)
- **Total**: 179 sentences with 329 entities (45.6% ≤2 words, 54.4% >2 words)

## Key Statistics

### Short Entity Split
- **Train**: 1,009 sentences (35.1% of original)
  - COM entities: 1,014 (86.2%) - avg length: 1.02 words
  - FUL entities: 162 (13.8%) - avg length: 3.10 words
- **Val**: 219 sentences (35.5% of original)
  - COM entities: 214 (81.7%) - avg length: 1.04 words
  - FUL entities: 48 (18.3%) - avg length: 2.40 words
- **Test**: 245 sentences (40.3% of original)
  - COM entities: 255 (90.4%) - avg length: 1.01 words
  - FUL entities: 27 (9.6%) - avg length: 3.67 words

### Long Entity Split
- **Train**: 120 sentences (4.2% of original)
  - COM entities: 108 (47.6%) - avg length: 1.05 words
  - FUL entities: 119 (52.4%) - avg length: 4.13 words
- **Val**: 26 sentences (4.2% of original)
  - COM entities: 22 (48.9%) - avg length: 1.36 words
  - FUL entities: 23 (51.1%) - avg length: 4.43 words
- **Test**: 33 sentences (5.4% of original)
  - COM entities: 25 (43.9%) - avg length: 1.12 words
  - FUL entities: 32 (56.1%) - avg length: 4.25 words

## Important Notes

1. **Overlapping Sentences**: A sentence can appear in BOTH short and long splits if it contains entities of both types. This is intentional to ensure complete coverage.

2. **Entity Length Calculation**:
   - Counted by number of consecutive tokens from B-* tag through I-* tags
   - Example: `["B-FUL", "I-FUL", "I-FUL"]` = 3 words

3. **Filter Criteria**:
   - **Short mode**: Keeps sentences with ANY entity ≤ threshold
   - **Long mode**: Keeps sentences with ANY entity > threshold

## Usage

### Basic Usage

```bash
# Create short entity splits (≤2 words)
python src/data_splitter.py \
  --input-train data/ner_splits_full/train_ner.pkl \
  --input-val data/ner_splits_full/val_ner.pkl \
  --input-test data/ner_splits_full/test_ner.pkl \
  --output-dir data/ner_splits_short \
  --threshold 2 \
  --mode short

# Create long entity splits (>2 words)
python src/data_splitter.py \
  --input-train data/ner_splits_full/train_ner.pkl \
  --input-val data/ner_splits_full/val_ner.pkl \
  --input-test data/ner_splits_full/test_ner.pkl \
  --output-dir data/ner_splits_long \
  --threshold 2 \
  --mode long
```

### Custom Threshold

```bash
# Use a different threshold (e.g., 3 words)
python src/data_splitter.py \
  --input-train data/ner_splits_full/train_ner.pkl \
  --input-val data/ner_splits_full/val_ner.pkl \
  --input-test data/ner_splits_full/test_ner.pkl \
  --output-dir data/ner_splits_3words \
  --threshold 3 \
  --mode short
```

## Command-Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--input-train` | Yes | Path to training data pickle file |
| `--input-val` | Yes | Path to validation data pickle file |
| `--input-test` | Yes | Path to test data pickle file |
| `--output-dir` | Yes | Base output directory for split data |
| `--threshold` | No | Entity length threshold in words (default: 2) |
| `--mode` | Yes | Split mode: 'short' (≤threshold) or 'long' (>threshold) |

## Output Format

The script generates two file formats for each split:

1. **Pickle files (.pkl)**: Original DataFrame format for Python processing
2. **CSV files (.csv)**: Human-readable format for inspection

Both formats contain the same data:
- `id`: Paper ID
- `title`: Paper title
- `abstract`: Abstract text
- `tokens`: List of word tokens
- `ner_tags`: List of BIO tags
- Additional metadata columns

## Use Cases

### 1. Training Specialized Models
Train separate models optimized for different entity complexities:
```bash
# Train model A on short entities
python train_ner.py --data-dir data/ner_splits_short

# Train model B on long entities
python train_ner.py --data-dir data/ner_splits_long
```

### 2. Ensemble Approach
Use different models for different entity types and merge predictions.

### 3. Analysis and Debugging
Compare model performance on simple vs. complex entities:
```bash
# Evaluate on short entities
python evaluate_ner.py --test-data data/ner_splits_short/test_ner.pkl

# Evaluate on long entities
python evaluate_ner.py --test-data data/ner_splits_long/test_ner.pkl
```

## Implementation Details

### Entity Length Algorithm
```python
def count_entity_lengths(ner_tags):
    """Extract entity lengths from BIO tags."""
    entity_lengths = []
    current_length = 0
    in_entity = False

    for tag in ner_tags:
        if tag.startswith('B-'):
            if in_entity and current_length > 0:
                entity_lengths.append(current_length)
            current_length = 1
            in_entity = True
        elif tag.startswith('I-') and in_entity:
            current_length += 1
        else:  # 'O' tag
            if in_entity and current_length > 0:
                entity_lengths.append(current_length)
            current_length = 0
            in_entity = False

    if in_entity and current_length > 0:
        entity_lengths.append(current_length)

    return entity_lengths
```

### Filtering Logic
```python
def filter_by_entity_length(df, threshold, mode):
    """Filter sentences based on entity length criteria."""
    def has_matching_entity(ner_tags):
        lengths = count_entity_lengths(ner_tags)
        if not lengths:
            return False

        if mode == 'short':
            return any(length <= threshold for length in lengths)
        else:  # mode == 'long'
            return any(length > threshold for length in lengths)

    mask = df['ner_tags'].apply(has_matching_entity)
    return df[mask].copy()
```

## Troubleshooting

### Issue: "Input file not found"
**Solution**: Verify the input file paths exist:
```bash
ls -l data/ner_splits_full/*.pkl
```

### Issue: "Failed to load pickle file"
**Solution**: Ensure the pickle files are valid pandas DataFrames:
```python
import pandas as pd
df = pd.read_pickle('data/ner_splits_full/train_ner.pkl')
print(df.head())
```

### Issue: "No entities found"
**Solution**: Check that the `ner_tags` column contains BIO tags:
```python
print(df['ner_tags'].iloc[0])  # Should show list like ['O', 'B-COM', 'I-COM', ...]
```

## Related Documentation

- See `docs/PHASE2_ENTITY_COMPLEXITY_EXPERIMENT.md` for experiment design
- See `docs/split_project/` for phase 2 results and analysis
- See training notebooks for model training examples

## Script Location

**File**: `/Users/warren/development/GBC/inventory_2022/src/data_splitter.py`

The script is fully documented with docstrings and includes comprehensive error handling.
