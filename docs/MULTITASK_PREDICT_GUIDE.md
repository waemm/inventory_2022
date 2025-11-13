# Phase 4 Multi-Task Model Inference Guide

## Overview

`src/multitask_predict.py` is the production inference script for the Phase 4 unified multi-task model. It performs both classification (bio-resource detection) and NER (entity extraction) in a single pass using the trained model with metadata features.

**Key Features:**
- Unified inference for both tasks using a single model
- Metadata feature integration (28 features)
- Automatic device detection (CUDA/MPS/CPU)
- Missing metadata imputation with defaults
- Batch processing for efficiency
- Comprehensive error handling and logging
- BIO tag entity extraction with confidence scores

---

## Quick Start

### Basic Usage

```bash
python src/multitask_predict.py \
    --input data/epmc_query_results_2022.csv \
    --metadata data/metadata/features_engineered.csv \
    --checkpoint checkpoint_best_ner.pt \
    --output-dir output/ \
    --batch-size 32 \
    --device cuda
```

### Minimal Example (CPU)

```bash
python src/multitask_predict.py \
    --input data/test_papers.csv \
    --metadata data/test_metadata.csv \
    --checkpoint models/checkpoint.pt \
    --output-dir results/
```

---

## Arguments

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--input` | Input CSV with papers (id, title, abstract) | `data/epmc_query_results_2022.csv` |
| `--metadata` | CSV with engineered features (28 metadata columns) | `data/metadata/features_engineered.csv` |
| `--checkpoint` | Path to Phase 4 model checkpoint | `checkpoint_best_ner.pt` |
| `--output-dir` | Output directory for results | `output/` |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--batch-size` | 32 | Batch size for inference |
| `--device` | auto | Device (auto/cuda/cpu/mps) |
| `--max-length-classif` | 256 | Max tokens for classification |
| `--max-length-ner` | 512 | Max tokens for NER |
| `--num-workers` | 0 | DataLoader workers |

---

## Input Format

### Papers CSV (`--input`)

Required columns:
- `id`: Paper identifier (numeric)
- `title`: Paper title (string)
- `abstract`: Paper abstract (string)

```csv
id,title,abstract,publication_date
34599955,"PDB Database","The Protein Data Bank is...",2021-09-30
34741192,"Rat Genome Database","Model organism research...",2021-11-05
```

### Metadata CSV (`--metadata`)

Must contain 28 feature columns in the following order:

**Numerical Features (2):**
1. `log_citations`
2. `years_since_pub`

**Boolean Features (8):**
3. `hasDbCrossReferences`
4. `hasData`
5. `hasSuppl`
6. `isOpenAccess`
7. `inPMC`
8. `inEPMC`
9. `hasPDF`
10. `hasBook`

**Categorical Features (2):**
11. `is_research_article`
12. `is_review_article`

**TF-IDF Features - MeSH (7):**
13-19. `mesh_tfidf_0` through `mesh_tfidf_6`

**TF-IDF Features - Keywords (5):**
20-24. `keyword_tfidf_0` through `keyword_tfidf_4`

**Missing Indicators (2):**
25. `meshTerms_missing`
26. `keywords_missing`

**Note:** Papers without metadata will be automatically imputed with default values.

---

## Output Format

### Classification Results (`classification_results.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Paper ID |
| `predicted_label` | string | 'bio-resource' or 'not-bio-resource' |
| `probability` | float | Probability of being a bio-resource (0-1) |
| `title` | string | Paper title |
| `abstract` | string | Paper abstract |

**Example:**
```csv
id,predicted_label,probability,title,abstract
12345,bio-resource,0.987,"PDB database","The Protein Data Bank..."
67890,not-bio-resource,0.234,"Statistical methods","This paper presents..."
```

### NER Results (`ner_results.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Paper ID |
| `title` | string | Paper title |
| `abstract` | string | Paper abstract |
| `entities` | string | Pipe-separated entity texts |
| `entity_types` | string | Pipe-separated entity types (COM/FUL) |
| `entity_probs` | string | Pipe-separated confidence scores |

**Example:**
```csv
id,title,abstract,entities,entity_types,entity_probs
12345,"PDB database","The Protein Data Bank...","PDB|Protein Data Bank","COM|FUL","0.998|0.995"
67890,"Methods","Statistical analysis","","",""
```

**Entity Types:**
- `COM`: Component/Short Form (e.g., "PDB", "EMBL")
- `FUL`: Full Name (e.g., "Protein Data Bank", "European Molecular Biology Laboratory")

---

## Model Architecture

The Phase 4 model uses a unified architecture:

```
Input Text (title + abstract)
    ↓
RoBERTa Encoder (shared)
    ↓
Metadata Projection (28 features → 768 dims)
    ↓
Fusion Layer (text + metadata)
    ↓
    ├─→ Classification Head → Binary prediction
    └─→ NER Head → BIO tags (O, B-COM, I-COM, B-FUL, I-FUL)
```

**Key Model Properties:**
- Base model: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500`
- Metadata features: 28 (CRITICAL - must match training)
- Classification labels: 2 (bio-resource, not-bio-resource)
- NER labels: 5 (O, B-COM, I-COM, B-FUL, I-FUL)

---

## Error Handling

### Missing Metadata

If a paper is missing metadata features, the script will:
1. Log a warning with the count of missing papers
2. Impute missing values with defaults:
   - Boolean features: 0
   - Numerical features: 0.0
   - TF-IDF features: 0.0
   - Missing indicators: 0

### Missing Input Columns

If the input CSV is missing required columns (`id`, `title`, `abstract`), the script will raise a `ValueError` and exit.

### Checkpoint Compatibility

If the checkpoint was trained with a different number of metadata features, the script will fail to load. Ensure the checkpoint was trained with 28 metadata features.

---

## Performance Considerations

### Batch Size

- **GPU (16GB):** Use batch size 32-64
- **GPU (8GB):** Use batch size 16-32
- **CPU:** Use batch size 8-16

Larger batch sizes improve throughput but require more memory.

### Sequence Length

- **Classification:** 256 tokens (faster, sufficient for most papers)
- **NER:** 512 tokens (captures more context for entity extraction)

Longer sequences improve accuracy but increase processing time.

### Device Selection

- **CUDA:** Fastest, requires NVIDIA GPU
- **MPS:** Good for Apple Silicon (M1/M2/M3)
- **CPU:** Slowest, no GPU required
- **Auto:** Automatically selects best available device

---

## Advanced Usage

### Processing Large Datasets

For datasets with >10,000 papers, consider:

```bash
# Increase batch size on GPU
python src/multitask_predict.py \
    --input large_dataset.csv \
    --metadata metadata.csv \
    --checkpoint checkpoint.pt \
    --output-dir output/ \
    --batch-size 64 \
    --device cuda \
    --num-workers 4
```

### CPU-Only Inference

```bash
python src/multitask_predict.py \
    --input papers.csv \
    --metadata metadata.csv \
    --checkpoint checkpoint.pt \
    --output-dir output/ \
    --batch-size 8 \
    --device cpu
```

### Custom Sequence Lengths

```bash
# Shorter sequences for faster processing
python src/multitask_predict.py \
    --input papers.csv \
    --metadata metadata.csv \
    --checkpoint checkpoint.pt \
    --output-dir output/ \
    --max-length-classif 128 \
    --max-length-ner 256
```

---

## Troubleshooting

### Out of Memory (OOM)

**Symptom:** `RuntimeError: CUDA out of memory`

**Solution:**
```bash
# Reduce batch size
python src/multitask_predict.py ... --batch-size 8

# Or reduce max length
python src/multitask_predict.py ... --max-length-ner 256
```

### Slow Processing

**Symptom:** Very slow inference on CPU

**Solution:**
```bash
# Use GPU if available
python src/multitask_predict.py ... --device cuda

# Or reduce sequence length
python src/multitask_predict.py ... --max-length-classif 128
```

### Missing Metadata Warning

**Symptom:** `Found X papers without metadata`

**Solution:** This is expected if some papers don't have metadata. The script will use default values. To improve results, run `src/fetch_enhanced_metadata.py` first.

### Checkpoint Loading Error

**Symptom:** `size mismatch for metadata_projection.projection.weight`

**Solution:** The checkpoint was trained with a different number of metadata features. Ensure you're using a Phase 4 checkpoint trained with 28 features.

---

## Integration with Pipeline

### Step 1: Fetch Metadata

```bash
python src/fetch_enhanced_metadata.py \
    --input data/epmc_query_results_2022.csv \
    --output data/metadata/features_engineered.csv
```

### Step 2: Run Inference

```bash
python src/multitask_predict.py \
    --input data/epmc_query_results_2022.csv \
    --metadata data/metadata/features_engineered.csv \
    --checkpoint checkpoint_best_ner.pt \
    --output-dir output/
```

### Step 3: Analyze Results

```python
import pandas as pd

# Load results
classif = pd.read_csv('output/classification_results.csv')
ner = pd.read_csv('output/ner_results.csv')

# Filter bio-resources
resources = classif[classif['predicted_label'] == 'bio-resource']

# Extract high-confidence resources
high_conf = resources[resources['probability'] > 0.8]

print(f"Found {len(high_conf)} high-confidence bio-resources")
```

---

## Example Output

### Console Output

```
2025-11-03 10:30:15 - INFO - Output directory: output/
2025-11-03 10:30:15 - INFO - Using device: cuda
2025-11-03 10:30:15 - INFO - Loading tokenizer...
2025-11-03 10:30:16 - INFO - Loading input papers from: data/epmc_query_results_2022.csv
2025-11-03 10:30:16 - INFO - Loaded 5000 papers
2025-11-03 10:30:16 - INFO - Loading metadata from: data/metadata/features_engineered.csv
2025-11-03 10:30:17 - INFO - Loaded metadata for 4950 papers
2025-11-03 10:30:17 - WARNING - Found 50 papers without metadata (1.0%). Using default imputation.
2025-11-03 10:30:17 - INFO - Loading model from checkpoint: checkpoint_best_ner.pt
2025-11-03 10:30:20 - INFO - Model loaded successfully on cuda
2025-11-03 10:30:20 - INFO -   - Metadata features: 28
2025-11-03 10:30:20 - INFO -   - Classification classes: 2
2025-11-03 10:30:20 - INFO -   - NER labels: 5

================================================================================
CLASSIFICATION INFERENCE
================================================================================
Classification: 100%|████████████████████| 157/157 [00:45<00:00,  3.47it/s]
2025-11-03 10:31:05 - INFO - Classification complete: 5000 papers processed
2025-11-03 10:31:05 - INFO -   - Bio-resources: 1250 (25.0%)
2025-11-03 10:31:05 - INFO -   - Non-resources: 3750 (75.0%)
2025-11-03 10:31:05 - INFO -   - Mean probability: 0.423
2025-11-03 10:31:05 - INFO - Classification results saved to: output/classification_results.csv

================================================================================
NER INFERENCE
================================================================================
NER: 100%|████████████████████████████████| 157/157 [01:20<00:00,  1.95it/s]
2025-11-03 10:32:25 - INFO - NER complete: 5000 papers processed
2025-11-03 10:32:25 - INFO -   - Total entities extracted: 3420
2025-11-03 10:32:25 - INFO -   - Papers with entities: 1180
2025-11-03 10:32:25 - INFO -   - Avg entities per paper: 0.68
2025-11-03 10:32:25 - INFO - NER results saved to: output/ner_results.csv

================================================================================
INFERENCE SUMMARY
================================================================================
2025-11-03 10:32:25 - INFO - Total papers processed: 5000
2025-11-03 10:32:25 - INFO - Classification time: 45.23s (110.5 papers/s)
2025-11-03 10:32:25 - INFO - NER time: 80.12s (62.4 papers/s)
2025-11-03 10:32:25 - INFO - Total time: 125.35s
2025-11-03 10:32:25 - INFO -
Output files:
2025-11-03 10:32:25 - INFO -   - output/classification_results.csv
2025-11-03 10:32:25 - INFO -   - output/ner_results.csv
================================================================================
```

---

## Technical Details

### BIO Tagging Scheme

The NER model uses a 5-label BIO scheme:

- **O**: Outside any entity
- **B-COM**: Beginning of component/short form
- **I-COM**: Inside component/short form
- **B-FUL**: Beginning of full name
- **I-FUL**: Inside full name

**Example:**
```
Text:    The PDB database is the Protein Data Bank
Tags:    O   B-COM O        O  O   B-FUL   I-FUL I-FUL
```

### Entity Extraction Algorithm

1. Tokenize text with RoBERTa tokenizer
2. Run NER model to get BIO tag predictions
3. Extract softmax probabilities for each token
4. Group consecutive B-* and I-* tags into entities
5. Calculate average confidence per entity
6. Filter special tokens (CLS, SEP, PAD)
7. Return entities with text, type, and confidence

### Metadata Feature Imputation

Missing metadata is imputed with the following defaults:

| Feature Type | Default Value | Rationale |
|--------------|---------------|-----------|
| Boolean | 0 | Assume feature is absent |
| Numerical | 0.0 | Neutral/unknown value |
| TF-IDF | 0.0 | No semantic similarity |
| Missing Indicators | 0 | Feature is indeed missing |

---

## API Reference

### Main Functions

#### `load_model(checkpoint_path: str, device: torch.device) -> BiomedicalMultiTaskModel`

Load the Phase 4 multi-task model from checkpoint.

**Args:**
- `checkpoint_path`: Path to checkpoint file
- `device`: Device to load model on

**Returns:**
- Loaded model in eval mode

#### `run_classification_inference(model, dataloader, device) -> pd.DataFrame`

Run classification inference on a dataset.

**Returns:**
- DataFrame with columns: `id`, `predicted_label`, `probability`, `title`, `abstract`

#### `run_ner_inference(model, dataloader, tokenizer, device) -> pd.DataFrame`

Run NER inference on a dataset.

**Returns:**
- DataFrame with columns: `id`, `title`, `abstract`, `entities`, `entity_types`, `entity_probs`

#### `extract_entities_from_bio_tags(tokens, bio_tags, probabilities) -> List[Tuple]`

Extract entities from BIO-tagged tokens.

**Returns:**
- List of `(entity_text, entity_type, confidence)` tuples

---

## Related Documentation

- [Phase 4 Architecture Deep Dive](PHASE4_ARCHITECTURE_DEEP_DIVE.md)
- [Fetch Enhanced Metadata Guide](FETCH_ENHANCED_METADATA_GUIDE.md)
- [Multi-Task Training Guide](EXPERIMENTAL_TRAINING_IMPLEMENTATION.md)

---

## Changelog

### Version 1.0 (2025-11-03)
- Initial release
- Support for 28 metadata features
- BIO tagging with 5 labels (O, B-COM, I-COM, B-FUL, I-FUL)
- Automatic device detection
- Missing metadata imputation
- Batch processing
- Comprehensive logging

---

## License

This software is part of the Genomics-Biodata-Catalog project and is subject to the project's license terms.

---

## Contact

For questions or issues, please refer to the main project documentation or contact the development team.
