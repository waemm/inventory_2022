# 2022 Inventory Rerun Plan - October 22, 2025

**Created**: October 22, 2025  
**Purpose**: Re-run the original 2022 biodata inventory using latest production models  
**Status**: 📋 **PLANNING PHASE**

---

## 🎯 **Project Overview**

### Objective
Re-process the original 2022 EuropePMC query results using the latest production-trained models from October 21, 2025 to generate an updated biodata resource inventory with improved accuracy.

### Key Requirements
- ✅ **Latest Models**: Use October 21, 2025 production models (Classification F1=0.898, NER F1=0.749)
- ✅ **Full Dataset**: Process all 21,678 papers from 2022 query
- ✅ **Streamlined Pipeline**: Focus on core classification and NER only
- ✅ **Fresh Results**: No integration with previous inventories
- ✅ **Comprehensive Backup**: Organized results with metadata

---

## 📊 **Data Specifications**

### Input Data
```
Source File: data/epmc_query_results_2022.csv
Papers Count: 21,678 papers
Date Range: 2011-2021 publications
Query Scope: EuropePMC biodata-related literature
File Size: ~5MB
Columns: id, title, abstract, publication_date
```

### Models to Use
```
Classification Model: out/classif_train_out/article_classifier.pt
- Performance: F1=0.898 (validation)
- Task: Binary classification (bio-resource vs general papers)
- Size: 476MB
- Training: October 21, 2025 (9.5 hour run)

NER Model: out/ner_train_out/named_entity_recognition.pt  
- Performance: F1=0.749 (validation)
- Task: Database name extraction (COM/FUL entities)
- Size: 481MB
- Training: October 21, 2025 (9.5 hour run)
```

### Environment
```
Python Environment: biodata_modern_env/
Python Version: 3.11.9
PyTorch: 2.2.2
Transformers: 4.35.0
Base Model: allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500
```

---

## 🔄 **Pipeline Steps (Simplified)**

### Core Processing Pipeline
```
Step 1: Classification
├── Input: data/epmc_query_results_2022.csv (21,678 papers)
├── Model: article_classifier.pt
├── Output: all classification predictions
└── Filter: Extract bio-resource papers only

Step 2: Named Entity Recognition  
├── Input: Bio-resource papers from Step 1
├── Model: named_entity_recognition.pt
├── Output: Extracted database names (COM/FUL entities)
└── Entities: Compound names + Full names

Step 3: URL Extraction
├── Input: NER results from Step 2
├── Process: Regex-based URL extraction
├── Output: Resource URLs from paper text
└── Max URLs: 3 per paper

Step 4: Name Processing
├── Input: URL extraction results
├── Process: Best name selection and probability assignment
├── Output: Processed resource names with confidence scores
└── Format: best_name, best_common, best_full with probabilities

Step 5: Final Results
├── Input: Processed names
├── Process: Clean and organize final output
├── Output: biodata_inventory_2022_rerun.csv
└── Columns: Standard inventory format
```

### Steps Explicitly Skipped
- ❌ EuropePMC querying (using existing 2022 data)
- ❌ Manual review and flagging
- ❌ URL status checking and validation
- ❌ Wayback Machine archival checks
- ❌ EuropePMC metadata enrichment
- ❌ Country/geographical processing
- ❌ Deduplication against previous inventories

---

## 📁 **Output Directory Structure**

### Primary Output Location
```
inventory_classification_results/
└── 2025-10-22_2022_rerun/
    ├── README.md                           # Run metadata and documentation
    ├── classification/
    │   ├── predictions.csv                 # All 21,678 classification results
    │   └── predicted_positives.csv         # Bio-resource papers only
    ├── ner/
    │   └── predictions.csv                 # Database names extracted from positives
    ├── url_extraction/
    │   └── predictions.csv                 # URLs extracted from papers
    ├── processed_names/
    │   └── predictions.csv                 # Processed names with probabilities
    ├── final_results/
    │   └── biodata_inventory_2022_rerun.csv # Final clean inventory
    └── logs/
        ├── processing_log.txt              # Complete processing log
        └── timing_report.txt               # Performance metrics
```

### Auto-generated Metadata (README.md)
```yaml
Run Information:
  Date: 2025-10-22
  Purpose: 2022 Inventory Rerun with Latest Models
  Input: data/epmc_query_results_2022.csv (21,678 papers)
  
Model Details:
  Classification Model: October 21, 2025 training (F1=0.898)
  NER Model: October 21, 2025 training (F1=0.749)
  Environment: biodata_modern_env (Python 3.11.9)
  
Processing Results:
  Total Papers: 21,678
  Bio-resource Papers: [Auto-filled during run]
  Extracted Resources: [Auto-filled during run]
  Processing Time: [Auto-filled during run]
  
Pipeline Configuration:
  Skip Manual Review: Yes
  Skip URL Checking: Yes
  Skip Wayback Machine: Yes
  Fresh Start: Yes (no previous data integration)
```

---

## ⚙️ **Technical Implementation**

### Script Name
```bash
rerun_2022_inventory.sh
```

### Key Script Features
- **Environment Verification**: Check Python 3.11 and package compatibility
- **Model Validation**: Verify latest models are present and correct
- **Progress Tracking**: Real-time progress indicators with timestamps
- **Error Handling**: Comprehensive error checking and recovery
- **Automatic Backup**: Results automatically archived with metadata
- **Performance Monitoring**: Track processing times and resource usage

### Expected Performance
```
Estimated Processing Time: 2-3 hours total
├── Classification: ~45-60 minutes (21,678 papers)
├── NER: ~30-45 minutes (estimated 2,000-4,000 positive papers)  
├── URL Extraction: ~5-10 minutes
├── Name Processing: ~10-15 minutes
└── Final Processing: ~5 minutes

Resource Requirements:
├── Memory: ~8GB peak during model inference
├── Storage: ~500MB for all results
├── CPU: Multi-core processing for data preparation
└── Models: ~960MB for both classification and NER models
```

### Expected Results
```
Classification Results:
├── Total Papers: 21,678
├── Estimated Bio-resource: ~2,000-4,000 papers (~10-18%)
├── Classification Accuracy: High confidence based on F1=0.898
└── False Positive Rate: Low (precision-focused model)

NER Results:  
├── Database Names Extracted: Estimated 1,500-3,000 unique resources
├── Entity Types: Compound names (abbreviations) + Full names
├── Extraction Quality: Good confidence based on F1=0.749
└── Coverage: Comprehensive entity extraction from positive papers

Final Inventory:
├── Unique Resources: After name processing and consolidation
├── URL Coverage: Resources with associated URLs
├── Quality: High-confidence resources with probability scores
└── Format: Standard biodata inventory format for comparison
```

---

## 🔄 **Implementation Steps**

### Phase 1: Script Creation
1. Create `rerun_2022_inventory.sh` based on `run_update_inventory_modern.sh`
2. Modify to use existing 2022 data instead of EuropePMC query
3. Remove manual review, URL checking, and metadata steps
4. Add comprehensive logging and backup functionality
5. Include automatic results organization and metadata generation

### Phase 2: Execution
1. Verify environment and models are ready
2. Execute full pipeline on 21,678 papers  
3. Monitor progress and handle any issues
4. Verify results quality and completeness
5. Generate final documentation and metadata

### Phase 3: Analysis
1. Compare results with original 2022 inventory
2. Analyze improvements from better models
3. Document findings and performance gains
4. Archive complete run for future reference

---

## 📈 **Expected Improvements Over Original 2022**

### Model Performance Gains
- **Classification**: Latest models trained on full datasets with 10 epochs
- **NER**: Improved entity extraction with modern training techniques  
- **Accuracy**: Higher precision and recall compared to original models
- **Coverage**: Better detection of biodata resources and database names

### Processing Efficiency
- **Modern Environment**: Python 3.11 with optimized packages
- **Faster Inference**: PyTorch 2.2.2 performance improvements
- **Streamlined Pipeline**: Focus on core ML tasks without overhead
- **Better Error Handling**: Robust processing with comprehensive logging

---

## 🎯 **Success Criteria**

### Technical Success
- ✅ Process all 21,678 papers without errors
- ✅ Generate classification results for every paper
- ✅ Extract entities from all bio-resource papers
- ✅ Complete processing within estimated timeframe
- ✅ Organize results with comprehensive documentation

### Quality Success  
- ✅ Results demonstrate improved accuracy over original 2022
- ✅ Extracted resources are high-quality and relevant
- ✅ Pipeline demonstrates reproducibility and reliability
- ✅ Documentation enables future analysis and comparison
- ✅ Archive preserves complete run for reference

---

## 📋 **Next Steps**

1. **Script Development**: Create `rerun_2022_inventory.sh` based on this plan
2. **Testing**: Quick validation on subset before full run
3. **Execution**: Run full pipeline on all 21,678 papers
4. **Documentation**: Generate results summary and comparison analysis
5. **Archive**: Preserve complete run in organized directory structure

---

**Plan Status**: ✅ **READY FOR IMPLEMENTATION**  
**Last Updated**: October 22, 2025  
**Implementation Target**: Same day execution  
**Expected Completion**: Within 3-4 hours total (including script creation)