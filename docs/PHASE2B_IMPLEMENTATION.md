# Phase 2B Implementation - Granular Entity Complexity Investigation

**Created**: 2025-11-03
**Purpose**: Map the inverted U-shaped complexity vs F1 relationship with granular data points

## Overview

Phase 2 discovered a non-linear (inverted U-shaped) relationship between entity complexity and NER F1 performance:

| Split | Test Complexity | Val F1  | Pattern |
|-------|----------------|---------|----------|
| A     | 12%            | 0.6788  | Low |
| D     | 28%            | 0.7165  | Rising |
| C     | 35%            | 0.7040  | Rising |
| **B** | **66%**        | **0.7281** | **PEAK** |
| E     | 84%            | 0.7233  | Declining |

Phase 2B adds 7 additional data points to precisely characterize this relationship and validate the curve at extreme values.

## Implementation

### 1. Split Generation Script

**File**: `/Users/warren/development/GBC/inventory_2022/scripts/create_phase2b_splits.py`

Creates 7 new complexity-stratified splits:

| Split | Target Complexity | Purpose | Expected F1 |
|-------|------------------|---------|-------------|
| K1 | ~5% | Extreme low (validate curve) | 0.67-0.68 |
| F | ~55% | Pre-optimal | 0.72-0.725 |
| G | ~60% | Approaching optimal | 0.725-0.728 |
| H | ~70% | Post-optimal | 0.726-0.728 |
| I | ~75% | Declining region | 0.724-0.727 |
| J | ~80% | Between B and E | 0.724-0.726 |
| K2 | ~92% | Extreme high (validate curve) | 0.71-0.72 |

**Key Features**:
- Uses `seed=241` for consistency with Phase 2
- Leverages existing `src/split_optimizer.py` functions
- Creates standard 70/15/15 train/val/test splits
- Saves both CSV (raw) and PKL (BIO-tagged) formats
- Generates README.md with split metadata
- Output: `data/ner_splits_splitF/` through `data/ner_splits_splitK2/`

**Usage**:
```bash
python scripts/create_phase2b_splits.py
```

### 2. Loop-Based Training Notebook

**File**: `/Users/warren/development/GBC/inventory_2022/phase2b_granular_training.ipynb`

Google Colab notebook that trains all 7 splits automatically.

**Structure**:

1. **Cell 1**: Mount Drive & Session Setup
   - Generates base session ID: `YYYY-MM-DD-xxxxxx`
   - Each split gets suffix: `{BASE_SESSION_ID}_split{X}`

2. **Cell 2**: Configuration
   - Defines all 7 splits in `SPLITS_CONFIG` list
   - V2 baseline parameters: lr=2e-5, batch=16, epochs=10
   - TEST_MODE option for validation

3. **Cell 3**: Environment Setup
   - Install dependencies (transformers==4.35.2, etc.)
   - GPU configuration
   - Import training utilities

4. **Cell 4**: Data Inspection
   - Verify all split data files exist
   - Display sample statistics

5. **Cell 5**: Prerequisites Check
   - Training modules
   - NLTK data
   - Model accessibility
   - GPU availability

6. **Cell 6**: Loop-Based Training ⭐
   - Iterates through all splits in `SPLITS_CONFIG`
   - For each split:
     - Generates unique `SESSION_ID = {BASE_SESSION_ID}_split{X}`
     - Creates separate archive: `training_archives/{SESSION_ID}/`
     - Trains NER model with V2 baseline parameters
     - Saves results, model, and logs to split-specific archive
     - Error handling: one failure doesn't stop pipeline
   - Tracks all results in `all_results` list

7. **Cell 7**: Aggregate Results
   - Combines results from all splits
   - Creates visualization (complexity vs F1 plot)
   - Saves combined results CSV
   - Identifies optimal complexity

8. **Cell 8**: Summary & Documentation
   - Final statistics
   - Archive locations
   - Next steps

**Key Features**:
- **Automated**: Trains all 7 splits sequentially without manual intervention
- **Separate Archives**: Each split saves to its own `training_archives/{SESSION_ID}_split{X}/` folder
- **Error Resilient**: Try/except blocks ensure one split failure doesn't stop the entire pipeline
- **Comprehensive Logging**: Each split has detailed training logs
- **Progress Tracking**: Clear console output showing which split is training
- **GPU Memory Management**: Clears GPU between splits to prevent OOM errors

### Archive Structure

After running, you'll have:

```
training_archives/
├── {BASE_SESSION_ID}_splitF/
│   ├── training_logs/
│   │   └── {SESSION_ID}_ner_training.log
│   ├── model/
│   │   └── [trained model files]
│   ├── training_results.csv
│   └── experiment_metadata.json
├── {BASE_SESSION_ID}_splitG/
│   └── [same structure]
├── {BASE_SESSION_ID}_splitH/
│   └── [same structure]
├── {BASE_SESSION_ID}_splitI/
│   └── [same structure]
├── {BASE_SESSION_ID}_splitJ/
│   └── [same structure]
├── {BASE_SESSION_ID}_splitK1/
│   └── [same structure]
├── {BASE_SESSION_ID}_splitK2/
│   └── [same structure]
├── phase2b_combined_results_{BASE_SESSION_ID}.csv
└── phase2b_results_plot_{BASE_SESSION_ID}.png
```

## Training Configuration

All splits use **V2 baseline parameters** for consistency:

```python
{
    'model_name': 'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500',
    'learning_rate': 2e-5,
    'batch_size': 16,
    'num_epochs': 10,
    'early_stopping': False
}
```

## Estimated Training Time

- **Per epoch**: ~48 minutes
- **Per split**: 10 epochs × 48 min = ~8 hours
- **All 7 splits**: 7 × 8 hours = **~56 hours** (2.3 days)

With Colab's GPU, you can run this over a weekend or use Colab Pro for extended runtime.

## Usage Instructions

### Step 1: Generate Splits

```bash
cd /Users/warren/development/GBC/inventory_2022
python scripts/create_phase2b_splits.py
```

This creates 7 directories in `data/`:
- `data/ner_splits_splitF/`
- `data/ner_splits_splitG/`
- `data/ner_splits_splitH/`
- `data/ner_splits_splitI/`
- `data/ner_splits_splitJ/`
- `data/ner_splits_splitK1/`
- `data/ner_splits_splitK2/`

### Step 2: Upload to Google Drive

Upload the entire `inventory_2022` folder to Google Drive at:
```
MyDrive/inventory_2022/
```

### Step 3: Run Training Notebook

1. Open `phase2b_granular_training.ipynb` in Google Colab
2. Ensure GPU runtime is enabled (Runtime → Change runtime type → GPU)
3. Run all cells sequentially
4. Monitor progress in Cell 6 (loop training)
5. Review results in Cell 7 (aggregation)

### Step 4: Download Results

After training completes, download:
- `training_archives/{BASE_SESSION_ID}_split*/` (individual archives)
- `training_archives/phase2b_combined_results_{BASE_SESSION_ID}.csv`
- `training_archives/phase2b_results_plot_{BASE_SESSION_ID}.png`

## Expected Results

Based on Phase 2 findings, we expect:

1. **K1 (5%)**: F1 ≈ 0.67-0.68 (similar to Split A at 12%)
2. **F (55%)**: F1 ≈ 0.72-0.725 (rising toward peak)
3. **G (60%)**: F1 ≈ 0.725-0.728 (approaching peak)
4. **H (70%)**: F1 ≈ 0.726-0.728 (just past peak, similar to B at 66%)
5. **I (75%)**: F1 ≈ 0.724-0.727 (declining region)
6. **J (80%)**: F1 ≈ 0.724-0.726 (between B and E)
7. **K2 (92%)**: F1 ≈ 0.71-0.72 (declining, similar to E at 84%)

## Data Points for Curve Fitting

After Phase 2B, you'll have **12 total data points**:

| Split | Complexity | Val F1 | Source |
|-------|-----------|--------|--------|
| K1 | ~5% | TBD | Phase 2B |
| A | 12% | 0.6788 | Phase 2 |
| D | 28% | 0.7165 | Phase 2 |
| C | 35% | 0.7040 | Phase 2 |
| F | ~55% | TBD | Phase 2B |
| G | ~60% | TBD | Phase 2B |
| B | 66% | 0.7281 | Phase 2 |
| H | ~70% | TBD | Phase 2B |
| I | ~75% | TBD | Phase 2B |
| J | ~80% | TBD | Phase 2B |
| E | 84% | 0.7233 | Phase 2 |
| K2 | ~92% | TBD | Phase 2B |

## Next Steps After Phase 2B

1. **Combine Results**: Merge Phase 2B with Phase 2 data
2. **Curve Fitting**: Fit polynomial or spline to 12 data points
3. **Analysis**:
   - Identify precise peak complexity
   - Calculate confidence intervals
   - Find inflection points
   - Determine optimal complexity range
4. **Recommendations**:
   - Optimal complexity target for production
   - Acceptable complexity range
   - Training split strategy
5. **Documentation**: Create comprehensive Phase 2 + 2B final report

## Technical Notes

### Why Separate Archives?

Each split gets its own archive folder because:
1. **Isolation**: Each training run is completely independent
2. **Debugging**: Easy to identify which split failed
3. **Comparison**: Side-by-side analysis of different complexity levels
4. **Reproducibility**: Each archive is self-contained with metadata

### Why Loop Instead of Parallel?

Training runs sequentially (not parallel) because:
1. **GPU Memory**: One model at a time prevents OOM errors
2. **Stability**: Easier to debug and monitor progress
3. **Colab Limits**: Colab doesn't support multiple GPU processes well
4. **Simplicity**: Clearer code flow and error handling

### Error Handling

The notebook includes comprehensive error handling:
- **Timeout**: 2 hours per split (prevents infinite hangs)
- **Try/Except**: Captures training failures without stopping pipeline
- **Error Tracking**: `training_errors` list records all failures
- **Status Field**: Each result has 'success', 'failed', or 'timeout' status

## Files Created

### New Files
1. `/Users/warren/development/GBC/inventory_2022/scripts/create_phase2b_splits.py`
2. `/Users/warren/development/GBC/inventory_2022/phase2b_granular_training.ipynb`
3. `/Users/warren/development/GBC/inventory_2022/docs/PHASE2B_IMPLEMENTATION.md` (this file)

### Generated Data (after running script)
- `data/ner_splits_splitF/` through `data/ner_splits_splitK2/`
- Each contains: train/val/test CSVs and PKLs, README.md

### Generated Results (after running notebook)
- `training_archives/{BASE_SESSION_ID}_splitF/` through `{BASE_SESSION_ID}_splitK2/`
- `training_archives/phase2b_combined_results_{BASE_SESSION_ID}.csv`
- `training_archives/phase2b_results_plot_{BASE_SESSION_ID}.png`

## Success Criteria

Phase 2B is successful if:
1. ✅ All 7 splits generate successfully
2. ✅ At least 6 out of 7 training runs complete
3. ✅ Results show consistent pattern with Phase 2
4. ✅ Extreme values (K1, K2) validate the inverted U-shape
5. ✅ Additional data points improve curve fit confidence

## References

- **Phase 2 Results**: See existing training archives for splits A, B, C, D, E
- **V2 Baseline Parameters**: From Phase 0 investigation (docs/PHASE_0_CRITICAL_FINDINGS_2025-10-30.md)
- **Split Optimizer**: `src/split_optimizer.py`
- **NER Training**: `src/ner_train.py`

---

**Implementation Status**: ✅ Complete
**Files Ready**: Yes
**Ready to Run**: Yes (after generating splits and uploading to Drive)
