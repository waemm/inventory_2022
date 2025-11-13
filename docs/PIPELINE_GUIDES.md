# Pipeline Execution Guides

**Purpose**: Comprehensive guide for running various inventory processing pipelines in Google Colab.

**Audience**: Users executing inventory updates or dataset processing using trained models.

**For Operational Guide**: See [`starting_doc.md`](starting_doc.md)
**For Historical Context**: See [`HISTORICAL_UPDATES.md`](HISTORICAL_UPDATES.md)

---

## Available Pipelines

### 1. Inventory Update Pipeline
**Purpose**: Process new EuropePMC queries through complete ML pipeline with manual review and URL validation
**Notebook**: `inventory_update_pipeline_with_checkpoints.ipynb`
**Best For**: Production-quality inventory updates with human oversight

### 2. 2022 Inventory Rerun Pipeline
**Purpose**: Streamlined processing of 2022 dataset (21,677 papers) with latest models
**Notebook**: `rerun_2022_inventory_with_checkpoints.ipynb`
**Best For**: Rapid reprocessing of fixed datasets without manual review

---

## Inventory Update Pipeline

### Overview

**Google Colab Integration for Comprehensive Inventory Processing**

Complete inventory update pipeline in Google Colab with model traceability and flexible workflow options. Process new literature from EuropePMC through classification, NER, URL validation, and manual review stages.

**Key Features:**
- ✅ **Model Traceability**: Link to specific training sessions using `TRAINING_SESSION_ID`
- ✅ **7 Workflow Options**: From full pipeline to fast-track processing
- ✅ **Checkpoint System**: Resume from any interruption point
- ✅ **Interactive Manual Review**: File upload/download with quality control
- ✅ **Archive System**: Complete traceability from training to final inventory

---

### Workflow Options Available

#### Option 1: Full Pipeline (Most Thorough)
**Description**: Complete 11-step pipeline with manual review and URL validation
**Use Case**: Production-quality inventory updates requiring human oversight
**Duration**: ~2-4 hours (depending on dataset size)

**Pipeline Steps**:
1. EuropePMC query execution
2. Classification (bio-resource detection)
3. Named Entity Recognition (database name extraction)
4. URL extraction
5. Name processing
6. Flagging for manual review
7. **Manual review download/upload**
8. Manual review processing
9. URL validation
10. Metadata enrichment
11. Final inventory generation

#### Option 2: Stop at Manual Review
**Description**: Process through flagging, stop for external review
**Use Case**: When review needs to happen offline or by multiple reviewers

**Workflow**:
- Run pipeline through step 6 (flagging)
- Download flagged entries for review
- Upload reviewed results when ready
- Use Option 3 to continue

#### Option 3: Continue from Manual Review
**Description**: Resume from manual review step (skip early pipeline)
**Use Case**: Continue processing after offline manual review

**Requirements**:
- Upload manually reviewed file
- Provide configuration from previous run
- Continue from step 8 onwards

#### Option 4: Skip Manual Review
**Description**: Automated processing with full URL validation
**Use Case**: When confident in automatic predictions, but want URL validation

**Pipeline Steps**:
1. EuropePMC query
2. Classification
3. NER
4. URL extraction
5. Name processing
6. URL validation (automatic)
7. Metadata enrichment
8. Final inventory

**Duration**: ~1-2 hours

#### Option 5: Fast Track Mode
**Description**: Skip both manual review AND URL validation
**Use Case**: Rapid prototyping, testing, or when URLs not critical

**Pipeline Steps**:
1. EuropePMC query
2. Classification
3. NER
4. URL extraction
5. Name processing
6. Final inventory

**Duration**: ~30-60 minutes

#### Option 6: Review-Only Mode
**Description**: Manual review for quality but skip URL validation
**Use Case**: Focus on data quality over URL accessibility

**Pipeline Steps**:
1-7. Standard pipeline through manual review
8. Skip URL validation
9. Metadata enrichment
10. Final inventory

#### Option 7: Custom Continuation
**Description**: Combine continuation with other skip options
**Use Case**: Maximum flexibility for custom workflows

**Examples**:
- Continue from review + skip URL validation
- Continue from review + fast track to final
- Resume from checkpoint + modify workflow

---

### Model Traceability System

**Configuration Example**:
```python
# Required for full traceability
TRAINING_SESSION_ID = "2025-10-23-abc123"  # From training notebook

# Results in complete lineage:
# Training (2025-10-23-abc123) → Inventory (2025-10-23-xyz789) → Archive
```

**Traceability Chain**:
- Training models archived with session ID
- Inventory processing links to specific training session
- Final archive preserves complete lineage
- Configuration files maintain audit trail

---

### Technical Implementation

**Archive Structure**:
```
/content/drive/MyDrive/inventory_2022/inventory_results/{INVENTORY_SESSION_ID}/
├── final_inventory.csv                 # Main output
├── query_results.csv                   # Raw EuropePMC data
├── classification_results.csv          # Classification predictions
├── ner_results.csv                     # Named entity extractions
├── url_validation_results.csv          # URL accessibility results
├── config_with_traceability.json       # Complete configuration
└── README.md                           # Documentation with lineage
```

**Checkpoint System**:
- Smart recovery: Local files → Google Drive → Fresh computation
- Configuration validation between runs
- Resume from any major pipeline step
- Automatic Google Drive backup after each step

**Configuration Variables**:
```python
TRAINING_SESSION_ID = "2025-10-23-abc123"  # Required
WORKFLOW_OPTION = 1  # 1-7, choose workflow mode
SKIP_MANUAL_REVIEW = False  # Automated vs manual review
SKIP_URL_VALIDATION = False  # Include URL checking
EUROPMC_QUERY = "your query here"  # EuropePMC search
```

---

## 2022 Inventory Rerun Pipeline

### Overview

**Streamlined Google Colab Integration for 2022 Dataset Processing**

Dedicated pipeline for reprocessing the 2022 EuropePMC dataset (21,677 papers) with latest production models and optimized workflow. Focuses on speed and simplicity for bulk reprocessing.

**Key Features**:
- ✅ **Model Traceability**: Link to specific training sessions using `TRAINING_SESSION_ID`
- ✅ **Streamlined Processing**: Optimized 5-step pipeline for 2022 dataset
- ✅ **Checkpoint System**: Resume from any interruption point
- ✅ **GPU Acceleration**: 5-10x faster than bash script processing
- ✅ **Archive System**: Complete traceability from training to final inventory

---

### Processing Modes Available

#### Full Mode
**Description**: Process all 21,677 papers from 2022 dataset
**Duration**: ~10-15 minutes on GPU
**Output**: Complete classification → NER → URL extraction → name processing

**Use Case**:
- Production inventory updates
- Comprehensive results with detailed statistics
- Full dataset processing

**Configuration**:
```python
RUN_MODE = "full"
INPUT_DATA = "data/epmc_query_results_2022.csv"
```

#### Test Mode
**Description**: Process subset (1,000 papers) for testing and validation
**Duration**: ~2-3 minutes on GPU
**Output**: Same pipeline with faster execution

**Use Case**:
- Testing model changes
- Pipeline modifications
- Quick validation

**Configuration**:
```python
RUN_MODE = "test"
TEST_SUBSET_SIZE = 1000
```

#### Resume Mode
**Description**: Continue from checkpoint if processing is interrupted
**Duration**: Depends on where resuming from

**Features**:
- Smart recovery from local files or Google Drive backups
- Configuration validation ensures consistency
- Automatic checkpoint detection

---

### Simplified Pipeline (5 Steps)

#### Step 1: Input Validation
**Actions**:
- Verify 2022 dataset availability and integrity
- Load and validate model traceability
- Create output directory structure

**Validation Checks**:
- Dataset file exists and readable
- Required columns present
- Models available from training session

#### Step 2: Classification Processing
**Actions**:
- Process all papers through classification model
- Filter bio-resource papers
- Save classification results and positives

**Expected Results**:
- ~15-20% positive rate (bio-resource papers)
- High confidence scores (>0.90)
- Complete prediction for all papers

#### Step 3: NER Processing
**Actions**:
- Process bio-resource papers through NER model
- Extract database names (COM/FUL entities)
- Save NER results with entity predictions

**Expected Results**:
- ~80-90% of papers have entity predictions
- Multiple entities per paper common
- High entity extraction confidence

#### Step 4: URL Extraction & Name Processing
**Actions**:
- Extract URLs from paper text using regex patterns
- Process extracted names with confidence scoring
- Select best names using probability thresholds

**Processing Logic**:
- Multiple URLs: Keep papers with ≤3 URLs
- Name selection: Choose highest probability name
- Confidence filtering: Remove low-quality predictions

#### Step 5: Final Results & Archive
**Actions**:
- Create final inventory file
- Generate comprehensive archive with full traceability
- Document complete processing lineage

**Archive Contents**:
- All intermediate results (classification, NER, URL, names)
- Configuration with traceability
- README with processing documentation
- Timing and performance metrics

---

### Technical Implementation

**Archive Structure**:
```
/content/drive/MyDrive/inventory_2022/rerun_results/{RERUN_SESSION_ID}_2022_rerun/
├── final_inventory.csv                 # Complete biodata resource inventory
├── classification_results.csv          # All classification predictions
├── classification_positives.csv        # Bio-resource papers only
├── ner_results.csv                     # Named entity recognition results
├── url_extraction_results.csv          # URL extraction results
├── processed_names_results.csv         # Processed database names
├── config_with_traceability.json       # Complete configuration
└── README.md                           # Documentation with lineage
```

**Model Traceability Chain**:
```
Training Session (e.g., 2025-10-23-abc123)
    ↓ archived models ↓
Rerun Session (e.g., 2025-10-23-xyz789)
    ↓ processes ↓
2022 Dataset (21,677 papers)
    ↓ produces ↓
Final Inventory (biodata resources)
```

**Performance Optimizations**:
- Streamlined for large dataset processing (21K papers)
- GPU acceleration for classification and NER inference
- Batch processing with progress tracking
- Comprehensive timing and performance metrics

**Configuration Variables**:
```python
TRAINING_SESSION_ID = "2025-10-23-abc123"  # Required
RUN_MODE = "full"  # or "test"
TEST_SUBSET_SIZE = 1000  # for test mode
MAX_URLS = 3  # Maximum URLs per paper
```

---

### Key Differences from Update Pipeline

**Simplified Workflow**:
- ❌ No EuropePMC querying (fixed input dataset)
- ❌ No manual review workflow (automated processing)
- ❌ No URL validation (focus on speed)
- ❌ No metadata enrichment (core pipeline only)
- ❌ No country processing (basic results)
- ❌ No deduplication (standalone processing)

**Optimized for Speed**:
- Fixed input eliminates query variability
- Reduced pipeline steps for faster execution
- Focus on core classification and NER processing
- Streamlined for batch processing of large datasets

**When to Use This Pipeline**:
- Reprocessing fixed datasets with new models
- Rapid bulk processing without manual review
- Testing model performance on large datasets
- Generating baseline results for comparison

**When to Use Update Pipeline Instead**:
- Processing new EuropePMC queries
- Need manual review and quality control
- URL validation required
- Metadata enrichment needed
- Production-quality inventory with human oversight

---

## Best Practices

### Model Traceability
- Always specify `TRAINING_SESSION_ID` for audit trail
- Document which models were used for each inventory
- Maintain lineage from training to final results

### Checkpoint Management
- ⚠️ **Note**: Checkpoint functionality deprecated as of 2025-10-28
- Use fresh runs for each execution
- Avoid loading cached results from different sessions
- See [`PYTORCH_CHECKPOINT_FIX.md`](PYTORCH_CHECKPOINT_FIX.md) for details

### Quality Validation
- Compare results against known baselines
- Check probability distributions (should be >0.95 average)
- Verify row counts match expectations between steps
- Use comparison tools for validation

### Performance Monitoring
- Track processing times for each step
- Monitor GPU utilization
- Log memory usage during inference
- Document any performance issues

---

## Troubleshooting

### Common Issues

**Issue**: Models not found
**Solution**: Verify `TRAINING_SESSION_ID` points to valid training archive

**Issue**: Low confidence scores
**Solution**: Check model loading, verify correct PyTorch version

**Issue**: Missing results between steps
**Solution**: Verify input file exists, check column names match expectations

**Issue**: GPU out of memory
**Solution**: Reduce batch size or process in smaller chunks

---

**Document Status**: ✅ **CURRENT**
**Last Updated**: 2025-10-28
**Location**: `GBC/inventory_2022/docs/PIPELINE_GUIDES.md`
