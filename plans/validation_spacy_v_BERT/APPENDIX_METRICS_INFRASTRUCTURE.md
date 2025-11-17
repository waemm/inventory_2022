# Appendix: Metrics & Infrastructure

**Date**: 2025-11-13
**Status**: 📚 REFERENCE DOCUMENT

---

## Classification Metrics Definitions

### Binary Classification Metrics

**Precision**:
```
Precision = TP / (TP + FP)
```
- Of all papers classified as positive, what % are truly positive?
- High precision = few false positives
- Important when false positives are costly

**Recall (Sensitivity)**:
```
Recall = TP / (TP + FN)
```
- Of all true positive papers, what % did we correctly identify?
- High recall = few false negatives
- Critical for ensuring comprehensive resource discovery

**F1 Score**:
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```
- Harmonic mean of precision and recall
- Balanced metric when both precision and recall matter
- Range: 0-1 (higher is better)

**Accuracy**:
```
Accuracy = (TP + TN) / (TP + TN + FP + FN)
```
- Overall correctness
- Can be misleading with imbalanced datasets

**Confusion Matrix**:
```
                Predicted Positive    Predicted Negative
Actual Positive        TP                    FN
Actual Negative        FP                    TN
```

### Agreement Metrics

**Cohen's Kappa**:
```
κ = (p_o - p_e) / (1 - p_e)
where:
  p_o = observed agreement
  p_e = expected agreement by chance
```
- Measures agreement between two classifiers
- Range: -1 to 1 (>0.6 = substantial agreement)

**Agreement Rate**:
```
Agreement = (Both Positive + Both Negative) / Total Papers
```
- Simple percentage agreement
- Easier to interpret than Kappa

---

## NER Metrics Definitions

### Entity-Level Metrics

**Exact Match**:
- Entity span and label must match exactly
- Strictest evaluation
- Used for V2 BERT NER

**Token-Level F1**:
- Evaluate each token independently
- More forgiving for boundary errors
- Used for spaCy evaluation

**Entity F1**:
```
Entity F1 = 2 × (Entity Precision × Entity Recall) / (Entity Precision + Entity Recall)

where:
  Entity Precision = Correct Entities / Predicted Entities
  Entity Recall = Correct Entities / True Entities
```

### Resource-Level Metrics

**Resource Precision**:
```
Resource Precision = Correct Resources / Predicted Resources
```
- Of all extracted resources, what % are correct?

**Resource Recall**:
```
Resource Recall = Correct Resources / True Resources
```
- Of all true resources, what % did we find?

**Resource F1**:
```
Resource F1 = 2 × (Resource Precision × Resource Recall) / (Resource Precision + Resource Recall)
```

**Novel Discovery Rate**:
```
Novel Discovery Rate = Novel Resources / Total Extracted Resources
```
- % of extracted resources not in 2022 baseline

---

## Performance Metrics

### Speed Metrics

**Throughput**:
```
Throughput = Papers Processed / Time (seconds)
```
- Papers per second
- Higher is better
- Varies by batch size and hardware

**Latency**:
```
Latency = Time (seconds) / Papers Processed
```
- Seconds per paper
- Lower is better
- Inverse of throughput

### Resource Metrics

**Memory Usage**:
- Peak RAM/VRAM during processing
- Measured in GB
- Important for deployment sizing

**Model Size**:
- Disk space for model files
- Measured in MB/GB
- Affects deployment and loading time

**GPU Utilization**:
- % GPU compute used during processing
- Should be >70% for efficient GPU usage
- Measured with `nvidia-smi`

---

## Environment Specifications

### Environment 1: biodata_modern_env (V2 Models)

**Location**: `/Users/warren/development/GBC/inventory_2022/biodata_modern_env/`

**Python**: 3.11.9

**Key Packages**:
```
torch==2.1.0
transformers==4.35.0
pandas==2.1.1
numpy==1.24.3
scikit-learn==1.3.1
requests==2.31.0
```

**Purpose**: V2 BERT Classification and NER models

**Models**:
- `out/classif_train_out/article_classifier_v2.pt` (476 MB)
- `out/ner_train_out/named_entity_recognition_v2.pt` (473 MB)

**Activation**:
```bash
source /Users/warren/development/GBC/inventory_2022/biodata_modern_env/bin/activate
```

**GPU Requirements**:
- CUDA-capable GPU with 4+ GB VRAM (recommended: 8+ GB)
- CPU fallback available but much slower

### Environment 2: pycaret_env (PyCaret Classification)

**Location**: `/Users/warren/development/GBC/inventory_2022/pycaret_env/`

**Python**: 3.11.9

**Key Packages**:
```
pycaret==3.0.4
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
lightgbm==4.0.0
catboost==1.2
xgboost==1.7.6
```

**Purpose**: PyCaret metadata-based classification

**Models**:
- `pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl` (184 KB)
- `pycaret_models/test_mode_false/pycaret_metadata_classifier_v1.pkl` (271 KB)

**Activation**:
```bash
source /Users/warren/development/GBC/inventory_2022/pycaret_env/bin/activate
```

**CPU-Only**: No GPU required, runs efficiently on CPU

### Environment 3: spacy_hybrid_ner/venv/ (spaCy NER)

**Location**: `/Users/warren/development/GBC/inventory_2022/spacy_hybrid_ner/venv/`

**Python**: 3.11.9

**Key Packages**:
```
spacy==3.7.0
pandas==2.1.1
numpy==1.24.3
scikit-learn==1.3.1
```

**Purpose**: spaCy Hybrid NER (EntityRuler + Statistical NER)

**Models**:
- `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/` (~50 MB)

**Activation**:
```bash
source /Users/warren/development/GBC/inventory_2022/spacy_hybrid_ner/venv/bin/activate
```

**CPU-Only**: No GPU required, 100-200 papers/sec on CPU

---

## Data Sources

### Ground Truth: bioresource_papers_latest.csv

**Location**: `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`

**Size**: 4,560 papers

**Columns**:
- `publication_id` / `pubmed_id`: Paper identifier
- `title`: Paper title
- `abstract`: Paper abstract (if available)
- `publication_date`: Publication date
- `resource_short_name`: Resource name
- `is_global_core_biodata_resource`: Binary flag (1=global core, 0=other)

**Purpose**: Ground truth for manual validation sample

**Notes**:
- Curated dataset with known bioresources
- High-quality labels
- Mix of global core and other resources

### Full Dataset: V5.1 2011-2021

**Location**: `data/final_query_v5.1_2011_2021/query_results.csv`

**Size**: 157,191 papers (284 MB)

**Columns**:
- `pubmed_id`: PubMed identifier
- `title`: Paper title
- `abstract`: Paper abstract
- `publication_date`: Publication date
- Additional EPMC metadata columns

**Purpose**: Full-scale validation dataset

**Time Range**: 2011-01-01 to 2021-12-31

**Source**: EuropePMC comprehensive query V5.1

### Metadata Full: V5.1 Metadata

**Location**: `data/final_query_v5.1_2011_2021/metadata_full.csv`

**Size**: 157,191 papers

**Columns**:
- `pubmed_id`
- `inPMC`, `inEPMC`: Binary flags
- `citedByCount`: Citation count
- `pubYear`: Publication year
- `log_citations`: Log-transformed citations
- MeSH terms (one-hot encoded): ~80-100 columns
- Total: 92-112 columns

**Purpose**: Features for PyCaret classification

**Notes**:
- Requires feature engineering before prediction
- One-hot encoded MeSH terms
- Log-transformed numeric features

### Reference Inventory: 2022 Baseline

**Location**: `data/final_inventory_2022.csv`

**Size**: 3,112 unique resources

**Columns**:
- Resource names/IDs
- Paper counts
- Other metadata

**Purpose**: Baseline for identifying novel discoveries

**Notes**:
- Resources identified in 2022 inventory run
- Used to calculate novel discovery rate

---

## API Usage Examples

### V2 BERT Classification

**Command Line**:
```bash
source biodata_modern_env/bin/activate

python src/class_predict.py \
  -c out/classif_train_out/article_classifier_v2.pt \
  -i input_papers.csv \
  -o output_dir/ \
  --predictive-field title_abstract \
  --batch-size 8
```

**Input Format** (CSV):
```csv
id,title,abstract
12345,"Title here","Abstract here..."
67890,"Another title","Another abstract..."
```

**Output Format** (CSV):
```csv
id,title,abstract,predicted_label,prediction_score
12345,"Title here","Abstract here...","bio-resource",0.95
67890,"Another title","Another abstract...","not-bio-resource",0.78
```

**Python API**:
```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load model
model_path = "out/classif_train_out/article_classifier_v2.pt"
checkpoint = torch.load(model_path, map_location='cpu')
model = AutoModelForSequenceClassification.from_pretrained('allenai/scibert_scivocab_uncased')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained('allenai/scibert_scivocab_uncased')

# Predict
text = "Title and abstract concatenated"
inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
with torch.no_grad():
    outputs = model(**inputs)
    prediction = torch.argmax(outputs.logits, dim=1).item()
```

### PyCaret Classification

**Python API**:
```python
import pandas as pd
from pycaret.classification import load_model, predict_model

# Load model
model = load_model('pycaret_models/test_mode_true/pycaret_metadata_classifier_v1')

# Load and prepare data (requires feature engineering!)
df = pd.read_csv('input_with_metadata.csv')

# Engineer features to match training
# - Merge with metadata
# - One-hot encode MeSH terms
# - Log transform numeric features
# - Ensure exact column match (92 or 112 columns)
df_features = engineer_features(df)  # See comparison_pycaret_v2/scripts/03_pycaret_prediction.py

# Predict
predictions = predict_model(model, data=df_features)

# predictions contains:
#   - prediction_label: 0 or 1
#   - prediction_score: probability of class 1
```

### V2 BERT NER

**Command Line**:
```bash
source biodata_modern_env/bin/activate

python src/ner_predict.py \
  -c out/ner_train_out/named_entity_recognition_v2.pt \
  -i classified_positives.csv \
  -o output_dir/
```

**Input Format** (CSV):
```csv
id,title,abstract,publication_date
12345,"Title","Abstract","2020-01-15"
```

**Output Format** (CSV):
```csv
ID,text,publication_date,common_name,common_prob,full_name,full_prob
12345,"Title. Abstract","2020-01-15","GenBank",0.95,"GenBank Database",0.89
12345,"Title. Abstract","2020-01-15","PDB",0.92,"Protein Data Bank",0.88
```

### spaCy Hybrid NER

**Python API**:
```python
from src.ner_predict_spacy import SpacyNERPredictor
import pandas as pd

# Initialize predictor
predictor = SpacyNERPredictor("spacy_hybrid_ner/models/ner_hybrid_v2_com_ful")

# Load papers (must have: pubmed_id, title, abstract)
papers_df = pd.read_csv('classified_positives.csv')

# Predict and get results
results = predictor.predict(papers_df, batch_size=32)

# results is a list of dicts:
# [
#   {'pmid': '12345', 'entity_text': 'GenBank', 'entity_label': 'RESOURCE',
#    'canonical_id': 'genbank', 'source': 'entityruler',
#    'start_char': 45, 'end_char': 52},
#   ...
# ]

# Or save directly to CSV
df_output = predictor.predict_to_csv(papers_df, 'output.csv', batch_size=32)

# Output format:
# pmid,entity_text,entity_label,canonical_id,source,start_char,end_char
# 12345,GenBank,RESOURCE,genbank,entityruler,45,52
# 12345,PDB,RESOURCE,pdb,entityruler,89,92
```

---

## Directory Structure

```
inventory_2022/
├── plans/
│   └── validation_spacy_v_BERT/
│       ├── PHASE0_SETUP_OVERVIEW.md
│       ├── PHASE1_MANUAL_VALIDATION.md
│       ├── PHASE2_FULL_SCALE.md
│       ├── APPENDIX_METRICS_INFRASTRUCTURE.md
│       └── PROGRESS.md
│
├── scripts/
│   ├── 00_verify_models.py              # Model loading verification
│   ├── 01_select_validation_sample.py   # Sample selection
│   ├── 02_fetch_abstracts.py            # EPMC abstract fetching
│   ├── 03_run_v2_classification.py      # V2 classification
│   ├── 04_run_pycaret_classification.py # PyCaret classification
│   ├── 05_compare_classifications.py    # Classification comparison
│   ├── 06_run_full_classification.py    # Full-scale classification
│   ├── 07_run_full_ner.py               # Full-scale NER
│   ├── 08_generate_inventories.py       # Inventory generation
│   └── 09_generate_final_report.py      # Final report
│
├── results/
│   ├── validation/
│   │   ├── sample/
│   │   │   └── validation_sample.csv
│   │   ├── classification/
│   │   ├── ner/
│   │   └── manual_review/
│   │
│   ├── full_scale/
│   │   ├── classification/
│   │   ├── ner/
│   │   ├── inventories/
│   │   ├── benchmarks/
│   │   └── reports/
│   │
│   └── final_report/
│       ├── COMPREHENSIVE_MODEL_COMPARISON_REPORT.md
│       ├── executive_summary.json
│       └── figures/
│
├── data/
│   ├── final_query_v5.1_2011_2021/
│   │   ├── query_results.csv            # 157,191 papers
│   │   └── metadata_full.csv            # PyCaret features
│   └── final_inventory_2022.csv         # 3,112 resources
│
├── out/
│   ├── classif_train_out/
│   │   └── article_classifier_v2.pt     # 476 MB
│   └── ner_train_out/
│       └── named_entity_recognition_v2.pt # 473 MB
│
├── pycaret_models/
│   ├── test_mode_true/
│   │   └── pycaret_metadata_classifier_v1.pkl  # 184 KB
│   └── test_mode_false/
│       └── pycaret_metadata_classifier_v1.pkl  # 271 KB
│
├── spacy_hybrid_ner/
│   ├── venv/                            # spaCy environment
│   ├── models/
│   │   └── ner_hybrid_v2_com_ful/               # ~50 MB
│   └── scripts/
│       └── 12_manual_validation_study.py # Previous validation
│
├── biodata_modern_env/                  # V2 models environment
├── pycaret_env/                         # PyCaret environment
│
└── VALIDATION_STUDY_QUICK_START.md
```

---

## Troubleshooting Guide

### Issue: Model fails to load

**V2 Models**:
```bash
# Check model file exists
ls -lh out/classif_train_out/article_classifier_v2.pt
ls -lh out/ner_train_out/named_entity_recognition_v2.pt

# Verify environment
source biodata_modern_env/bin/activate
python -c "import torch; print(torch.__version__)"
python -c "import transformers; print(transformers.__version__)"

# Test loading
python scripts/00_verify_models.py
```

**PyCaret Models**:
```bash
# Check model files
ls -lh pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl

# Verify environment
source pycaret_env/bin/activate
python -c "import pycaret; print(pycaret.__version__)"

# Test loading
cd /Users/warren/development/GBC/inventory_2022
python -c "from pycaret.classification import load_model; model = load_model('pycaret_models/test_mode_true/pycaret_metadata_classifier_v1'); print('OK')"
```

**spaCy Models**:
```bash
# Check model directory
ls -lh spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/

# Verify environment
source spacy_hybrid_ner/venv/bin/activate
python -c "import spacy; print(spacy.__version__)"

# Test loading
python -c "from src.ner_predict_spacy import SpacyNERPredictor; p = SpacyNERPredictor('spacy_hybrid_ner/models/ner_hybrid_v2_com_ful'); print('OK')"
```

### Issue: Out of memory (GPU)

**Symptoms**: CUDA out of memory error

**Solutions**:
1. Reduce batch size:
   ```bash
   python src/class_predict.py ... --batch-size 4  # Try 4, 2, or 1
   ```

2. Clear GPU cache:
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

3. Monitor GPU memory:
   ```bash
   nvidia-smi  # Check VRAM usage
   watch -n 1 nvidia-smi  # Monitor continuously
   ```

4. Use CPU (slower):
   ```python
   device = 'cpu'  # Force CPU usage
   ```

### Issue: Out of memory (RAM)

**Symptoms**: Killed process, memory error

**Solutions**:
1. Process in smaller batches:
   ```python
   BATCH_SIZE = 5000  # Reduce from 10000
   ```

2. Clear memory between batches:
   ```python
   import gc
   del large_dataframe
   gc.collect()
   ```

3. Monitor RAM:
   ```bash
   htop  # Check RAM usage
   ```

### Issue: PyCaret prediction fails

**Common Error**: `KeyError: 'column_name'`

**Cause**: Feature engineering mismatch

**Solution**:
```python
# Ensure exact column match with training
model_features = model.feature_names_in_  # Get expected features
df_features = df[model_features]  # Select only those columns

# Check for missing columns
missing = set(model_features) - set(df.columns)
if missing:
    print(f"Missing columns: {missing}")
```

### Issue: EPMC API rate limiting

**Symptoms**: 429 Too Many Requests error

**Solution**:
```python
import time

def fetch_with_retry(pmid, max_retries=3):
    for i in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 429:
                wait_time = 2 ** i  # Exponential backoff
                time.sleep(wait_time)
                continue
            return response.json()
        except:
            time.sleep(1)
    return None
```

### Issue: Different results between runs

**Cause**: Random seed not set

**Solution**:
```python
import random
import numpy as np
import torch

# Set seeds
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(42)
```

---

## Resource Requirements Summary

### Minimum Requirements

**Hardware**:
- CPU: 4+ cores
- RAM: 16 GB
- GPU: Optional (4+ GB VRAM)
- Disk: 10 GB free

**Software**:
- Python 3.11.9
- macOS or Linux
- CUDA 11.8+ (if using GPU)

### Recommended Requirements

**Hardware**:
- CPU: 8+ cores
- RAM: 32 GB
- GPU: 8+ GB VRAM (NVIDIA)
- Disk: 50 GB free
- SSD for faster I/O

**Software**:
- Python 3.11.9
- Ubuntu 20.04+ or macOS 12+
- CUDA 12.0+
- cuDNN 8.0+

### Processing Time Estimates

**Phase 1 (100-125 papers)**:
- V2 Classification: 10-20 seconds
- PyCaret Classification: 2-5 seconds
- V2 NER: 20-60 seconds
- spaCy NER: 0.5-1 seconds
- **Total**: 1-2 hours (including manual review)

**Phase 2 (157k papers)**:
- V2 Classification: 8-16 hours (GPU)
- PyCaret Classification: 1-3 hours (CPU)
- V2 NER: 4-10 hours (GPU, on ~20k positives)
- spaCy NER: 0.5-2 hours (CPU, on ~20k positives)
- **Total**: 2-3 weeks (including analysis & reporting)

---

## Critical Notes

### 1. Abstract Availability

**CRITICAL**: NER performance depends heavily on abstract availability.

- **Title-only recall**: ~48% (previous spaCy validation)
- **Title+abstract recall**: ~60-80% (expected improvement)
- **Impact**: +20-30 percentage points recall

**Action**: Always verify abstract coverage before NER:
```python
abstract_coverage = df['abstract'].notna().sum() / len(df) * 100
print(f"Abstract coverage: {abstract_coverage:.1f}%")

if abstract_coverage < 80:
    print("WARNING: Low abstract coverage, NER recall will be reduced")
    print("Consider fetching missing abstracts from EPMC")
```

### 2. Training Overlap

**CRITICAL**: Must remove training papers from validation sample to avoid data leakage.

**Training Data**:
- Classification: `data/classif_splits_full/train_paper_classif.csv`
- NER: `data/ner_splits_full/train.csv`

**Action**: Always filter out training IDs:
```python
# Load training IDs
train_ids = set()
train_ids.update(pd.read_csv('data/classif_splits_full/train_paper_classif.csv')['id'])
train_ids.update(pd.read_csv('data/ner_splits_full/train.csv')['id'])

# Filter validation sample
df_valid = df[~df['id'].isin(train_ids)]
```

### 3. PyCaret Feature Engineering

**CRITICAL**: PyCaret requires exact feature match with training data.

**Required Features** (92 or 112 columns):
- Binary flags: `inPMC`, `inEPMC`, etc.
- Numeric: `citedByCount`, `pubYear`, `log_citations`
- MeSH terms: One-hot encoded (~80-100 columns)

**Action**: Use existing feature engineering function:
```python
from comparison_pycaret_v2.scripts.03_pycaret_prediction import engineer_features_for_model

# This function handles:
# - Metadata merging
# - MeSH encoding
# - Log transformations
# - Column selection
df_features = engineer_features_for_model(df, model)
```

---

**End of Appendix**
