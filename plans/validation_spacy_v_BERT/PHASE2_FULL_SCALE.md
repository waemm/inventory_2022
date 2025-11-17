# Phase 2: Full-Scale Validation on 149,943 Papers

**Date**: 2025-11-14 (Updated)
**Prerequisites**: Phase 1 completed ✅, V5.1 data validated ✅
**Timeline**: 2-3 weeks
**Status**: 📋 READY TO BEGIN

---

## Overview

Phase 2 applies all 4 models to the complete V5.1 2011-2021 dataset to:
- Generate production-scale performance benchmarks
- Build comprehensive resource inventories
- Identify novel discoveries not in 2022 baseline
- Compare resource-level agreement between models
- Provide final recommendations for production deployment

### Success Criteria ✅

- [ ] All 149,943 papers processed through classification (V2 + PyCaret)
- [ ] Classified positives processed through NER (V2 + spaCy)
- [ ] Resource inventories generated for all 4 model combinations
- [ ] Performance benchmarks collected (speed, memory, accuracy)
- [ ] Novel discoveries identified and validated
- [ ] Comprehensive comparison report completed
- [ ] Production deployment recommendation made

---

## Dataset Overview

**Input Dataset**: `validation_spacy_v_BERT/data/v5.1_cleaned.csv`
- **Size**: 149,943 papers (338 MB, cleaned from original 156,231)
- **Columns**: 42 (20 base + 22 engineered features)
- **Time Range**: 2011-01-01 to 2021-12-31 (strictly enforced)
- **Source**: EuropePMC comprehensive query V5.1 (cleaned)
- **Quality**: ✅ Validated (see `validation_spacy_v_BERT/V5.1_DATA_QUALITY_REPORT.md`)

**Reference Baseline**: `data/final_inventory_2022.csv`
- **Size**: 3,112 unique resources
- **Purpose**: Compare against to identify novel discoveries

**Expected Outputs**:
- Classification: 15k-22k positives (10-15% of 150k)
- NER: 3k-5k unique resources total
- Novel discoveries: 500-1000 new resources vs 2022 baseline

---

## Implementation Strategy: Colab + Local Hybrid

**Why Colab for V2 Models?**
- V2 BERT models require GPU for reasonable speed (5-10 papers/sec vs 0.5 papers/sec CPU)
- Local execution would take 8-40 hours for classification alone
- Colab provides free GPU access (T4/V100) reducing runtime to 2-8 hours

**Why Local for Analysis?**
- Comparison/inventory scripts are lightweight (CPU-only)
- Direct file access without Drive sync overhead
- Easier debugging and iteration

### Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2 WORKFLOW                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. UPLOAD DATA (Google Drive)                              │
│    ├─ v5.1_cleaned.csv (150k papers) → Drive              │
│    └─ V2 models (already on Drive)                         │
│                                                             │
│ 2. COLAB NOTEBOOKS (GPU Processing)                        │
│    ├─ 06a_v2_classification_150k.ipynb  (2-4 hrs GPU)     │
│    ├─ 06b_pycaret_classification_150k.ipynb (1-3 hrs CPU) │
│    ├─ 07a_v2_ner_150k.ipynb            (4-8 hrs GPU)      │
│    └─ 07b_spacy_ner_150k.ipynb         (0.5-2 hrs CPU)    │
│                                                             │
│ 3. DOWNLOAD RESULTS (Local)                                │
│    ├─ Use rclone or Google Drive sync                      │
│    └─ Pull classification + NER results from Drive         │
│                                                             │
│ 4. LOCAL ANALYSIS (Python Scripts)                         │
│    ├─ 08_generate_inventories.py                           │
│    └─ 09_generate_final_report.py                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Upload Data to Google Drive

### Objective
Upload cleaned V5.1 dataset to Google Drive for Colab access.

### Files to Upload

```bash
# Use existing upload script
python upload_to_drive.py validation_spacy_v_BERT/data/v5.1_cleaned.csv

# Or use rclone
rclone copy validation_spacy_v_BERT/data/v5.1_cleaned.csv \
  gdrive:inventory_2022/validation_spacy_v_BERT/data/
```

**Verify upload:**
```bash
rclone ls gdrive:inventory_2022/validation_spacy_v_BERT/data/v5.1_cleaned.csv
# Should show: 354,000,000 v5.1_cleaned.csv (approx)
```

---

## Step 6a: V2 BERT Classification (Colab Notebook)

### Objective
Run V2 BERT classifier on all 149,943 papers using Google Colab GPU.

### Notebook: `validation_spacy_v_BERT/notebooks/phase2_v2_classification_150k.ipynb`

**Runtime**: 2-4 hours (GPU T4/V100)

**Inputs**:
- `gdrive:inventory_2022/validation_spacy_v_BERT/data/v5.1_cleaned.csv` (149,943 papers)
- `gdrive:inventory_2022/out/original_model/article_classifier.pt` (V2 model)

**Outputs** (saved to Google Drive):
- `gdrive:inventory_2022/validation_spacy_v_BERT/results/phase2/classification/v2_classification_150k_SESSION_ID.csv`
- `gdrive:inventory_2022/validation_spacy_v_BERT/results/phase2/benchmarks/v2_classification_benchmark_SESSION_ID.json`

**Key Features**:
- Batch processing (batch_size=16 for GPU memory efficiency)
- Progress tracking every 1000 papers
- Automatic checkpoint saving every 10,000 papers
- Memory-efficient streaming for large dataset
- GPU utilization monitoring

**Expected Results**:
- Processing speed: ~5-10 papers/sec (GPU)
- Positive rate: 10-15% (~15k-22k papers)
- Mean confidence: >0.85
- GPU memory usage: 8-12 GB

---

## Step 6b: PyCaret Classification (Colab Notebook)

### Objective
Run PyCaret metadata classifier on all 149,943 papers using CPU.

### Notebook: `validation_spacy_v_BERT/notebooks/phase2_pycaret_classification_150k.ipynb`

**Runtime**: 1-3 hours (CPU)

**Inputs**:
- `gdrive:inventory_2022/validation_spacy_v_BERT/data/v5.1_cleaned.csv` (149,943 papers with 42 features)
- `gdrive:inventory_2022/pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl`

**Outputs** (saved to Google Drive):
- `gdrive:inventory_2022/validation_spacy_v_BERT/results/phase2/classification/pycaret_classification_150k_SESSION_ID.csv`
- `gdrive:inventory_2022/validation_spacy_v_BERT/results/phase2/benchmarks/pycaret_classification_benchmark_SESSION_ID.json`

**Key Features**:
- Uses pre-cleaned V5.1 dataset with 22 engineered features
- Feature engineering already complete (binary flags, counts, scores)
- Batch processing for memory efficiency
- Progress tracking
- Feature importance analysis

**Expected Results**:
- Processing speed: ~20-50 papers/sec (CPU)
- Positive rate: 6-12% (~9k-18k papers)
- Precision: High (based on Phase 1: 100%)
- CPU memory usage: 4-8 GB

---

## Step 7a: V2 BERT NER (Colab Notebook)

### Objective
Run V2 BERT NER on classified positives using Google Colab GPU.

### Notebook: `validation_spacy_v_BERT/notebooks/phase2_v2_ner_150k.ipynb`

**Runtime**: 4-8 hours (GPU T4/V100)

**Inputs**:
- Classification results from Steps 6a & 6b (merged positives: ~15k-20k papers)
- `gdrive:inventory_2022/out/original_model/named_entity_recognition.pt` (V2 NER model)

**Outputs** (saved to Google Drive):
- `gdrive:inventory_2022/validation_spacy_v_BERT/results/phase2/ner/v2_ner_150k_SESSION_ID.csv`
- `gdrive:inventory_2022/validation_spacy_v_BERT/results/phase2/benchmarks/v2_ner_benchmark_SESSION_ID.json`

**Key Features**:
- Processes union of V2 + PyCaret positives (~15k-20k papers)
- Batch processing (batch_size=8 for NER memory requirements)
- Progress tracking every 500 papers
- Entity post-processing (grouping IOB tags into complete entities)
- GPU memory monitoring

**Expected Results**:
- Processing speed: ~2-5 papers/sec (GPU)
- Total entities: 20k-40k
- Unique mentions: 2k-4k
- Papers with entities: 85-95%
- GPU memory usage: 10-14 GB

---

## Step 7b: spaCy Hybrid NER (Colab Notebook)

### Objective
Run spaCy Hybrid NER on classified positives using CPU.

### Notebook: `validation_spacy_v_BERT/notebooks/phase2_spacy_ner_150k.ipynb`

**Runtime**: 0.5-2 hours (CPU)

**Inputs**:
- Classification results from Steps 6a & 6b (merged positives: ~15k-20k papers)
- `gdrive:inventory_2022/spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/` (spaCy model)

**Outputs** (saved to Google Drive):
- `gdrive:inventory_2022/validation_spacy_v_BERT/results/phase2/ner/spacy_ner_150k_SESSION_ID.csv`
- `gdrive:inventory_2022/validation_spacy_v_BERT/results/phase2/benchmarks/spacy_ner_benchmark_SESSION_ID.json`

**Key Features**:
- Batch processing with `.pipe()` (batch_size=64 for speed)
- EntityRuler (752 resources) + Statistical NER hybrid pipeline
- Alias resolution to canonical IDs
- Entity source tracking (dictionary vs learned)
- Very fast CPU processing (100-200 papers/sec)

**Expected Results**:
- Processing speed: ~100-200 papers/sec (CPU)
- Total entities: 25k-45k
- Unique canonical IDs: 2k-4k resources
- Papers with entities: 90-98%
- CPU memory usage: 4-6 GB

---

## Step 8: Download Results & Local Analysis

### Objective
Download Colab results from Google Drive and run local analysis scripts.

### Download Results

```bash
# Use rclone to download all Phase 2 results
rclone copy \
  gdrive:inventory_2022/validation_spacy_v_BERT/results/phase2/ \
  validation_spacy_v_BERT/results/phase2/ \
  --progress

# Verify downloads
ls -lh validation_spacy_v_BERT/results/phase2/classification/
ls -lh validation_spacy_v_BERT/results/phase2/ner/
```

**Expected files**:
- `v2_classification_150k_SESSION_ID.csv` (~5-8 MB)
- `pycaret_classification_150k_SESSION_ID.csv` (~5-8 MB)
- `v2_ner_150k_SESSION_ID.csv` (~2-4 MB)
- `spacy_ner_150k_SESSION_ID.csv` (~3-5 MB)
- 4 benchmark JSON files

---

## Step 9: Generate Resource Inventories (Local Script)

### Objective
Convert NER results into resource inventories and identify novel discoveries.

### Script: `validation_spacy_v_BERT/scripts/08_generate_inventories.py`

**Runtime**: 5-15 minutes (local CPU)

**Inputs** (downloaded from Drive):
- `results/phase2/ner/v2_ner_150k_SESSION_ID.csv`
- `results/phase2/ner/spacy_ner_150k_SESSION_ID.csv`
- `data/final_inventory_2022.csv` (3,112 resources baseline)

**Outputs**:
- `results/phase2/inventories/v2_inventory.csv` - V2 unique resources
- `results/phase2/inventories/spacy_inventory.csv` - spaCy unique resources
- `results/phase2/inventories/inventory_comparison.csv` - Resource overlap
- `results/phase2/inventories/novel_discoveries_v2.csv` - New resources (V2)
- `results/phase2/inventories/novel_discoveries_spacy.csv` - New resources (spaCy)
- `results/phase2/inventories/inventory_metrics.json` - Summary statistics

**Key Metrics**:
- Total unique resources per model
- Overlap with 2022 baseline (recall vs baseline)
- Novel discoveries (not in baseline)
- Resource-level agreement between V2 and spaCy
- Paper coverage per resource
- High-confidence novel discoveries (>5 papers)

---

## Step 10: Generate Final Report (Local Script)

### Objective
Create comprehensive comparison report integrating Phase 1 + Phase 2 results.

### Script: `validation_spacy_v_BERT/scripts/09_generate_final_report.py`

**Runtime**: 2-5 minutes (local CPU)

**Inputs**:
- All Phase 1 results
- All Phase 2 results
- All benchmark files

**Outputs**:
- `results/final_report/COMPREHENSIVE_MODEL_COMPARISON_REPORT.md` - Full report
- `results/final_report/executive_summary.json` - Key metrics
- `results/final_report/production_recommendations.md` - Deployment guide
- `results/final_report/figures/` - Visualization charts

**Report Sections**:
1. Executive Summary
2. Phase 1 Results (148 papers manual validation)
3. Phase 2 Results (150k papers full-scale)
4. Model Comparison Matrix
5. Novel Discoveries Analysis
6. Production Deployment Recommendations
7. Performance vs Accuracy Trade-offs

---

## Timeline & Resource Estimates

### Week 1: Data Preparation & Upload (Days 1-2)

**Day 1: Data Preparation**
- ✅ V5.1 data validation complete (already done)
- ✅ V5.1 data cleaning complete (already done)
- Upload v5.1_cleaned.csv to Google Drive (~5 minutes)
- Verify all models on Drive (V2 classifier, V2 NER, PyCaret, spaCy)

**Day 2: Notebook Setup**
- Review all 4 Colab notebooks
- Test notebooks with small sample (TEST_MODE=True)
- Verify Drive paths and permissions

### Week 2: Classification (Days 3-9)

**Day 3-4: V2 Classification (Colab)**
- Run `phase2_v2_classification_150k.ipynb`
- Runtime: 2-4 hours (GPU)
- Monitor progress, handle any errors
- Verify results saved to Drive

**Day 5: PyCaret Classification (Colab)**
- Run `phase2_pycaret_classification_150k.ipynb`
- Runtime: 1-3 hours (CPU)
- Verify feature engineering worked correctly
- Check results saved to Drive

**Day 6: Download & Merge Classifications**
- Download both classification results locally
- Merge to create union of positives for NER
- Expected: 15k-22k papers classified as positive
- Upload merged positives back to Drive for NER

**Day 7-9: Buffer/Troubleshooting**

### Week 3: NER Extraction (Days 10-16)

**Day 10-11: V2 NER (Colab)**
- Run `phase2_v2_ner_150k.ipynb` on ~20k positives
- Runtime: 4-8 hours (GPU)
- Monitor entity extraction progress
- Verify results saved to Drive

**Day 12: spaCy NER (Colab)**
- Run `phase2_spacy_ner_150k.ipynb` on ~20k positives
- Runtime: 0.5-2 hours (CPU)
- Very fast, should complete quickly
- Verify alias resolution worked

**Day 13: Download NER Results**
- Download all 4 result files from Drive
- Verify file integrity and completeness
- Check entity counts are reasonable

**Day 14-16: Buffer/Troubleshooting**

### Week 4: Analysis & Reporting (Days 17-21)

**Day 17: Generate Inventories (Local)**
- Run `08_generate_inventories.py`
- Runtime: 5-15 minutes
- Generate resource catalogs
- Identify novel discoveries

**Day 18-19: Final Report (Local)**
- Run `09_generate_final_report.py`
- Runtime: 2-5 minutes
- Combine Phase 1 + Phase 2 results
- Generate visualizations

**Day 20-21: Review & Iteration**
- Review comprehensive report
- Validate novel discoveries
- Finalize production recommendations

---

## Checkpoints & Validation

### After Classification (Day 6)

**Validate**:
- [ ] All 149,943 papers processed
- [ ] Positive rates reasonable (10-15% for V2, 6-12% for PyCaret)
- [ ] No duplicate papers
- [ ] Classification files exist and are >0 bytes
- [ ] Benchmark metrics saved

**Action if failed**:
- Review Colab notebook logs
- Check input data quality
- Re-run notebooks if needed
- Verify model loading

### After NER (Day 13)

**Validate**:
- [ ] All classified positives processed
- [ ] Entity extraction counts reasonable (20k-45k entities)
- [ ] NER output format correct
- [ ] No missing papers
- [ ] Benchmark metrics saved

**Action if failed**:
- Review Colab notebook logs
- Check abstract availability
- Re-run notebooks if needed
- Verify model/tokenizer compatibility

### After Inventories (Day 17)

**Validate**:
- [ ] Resource counts reasonable (3k-5k unique)
- [ ] Novel discoveries identified (500-1000 expected)
- [ ] Inventory comparison complete
- [ ] Metrics saved

**Action if failed**:
- Review entity aggregation logic
- Check resource name normalization
- Verify baseline comparison
- Re-run inventory generation

---

## Risk Mitigation

### Colab Timeout Issues

**Symptom**: Colab session disconnects before completion

**Solution**:
- Use Colab Pro for longer runtimes (24 hours vs 12 hours)
- Implement checkpoint saving every 10k papers
- Monitor session and click browser periodically
- Save intermediate results to Drive

### GPU Memory Issues

**Symptom**: Out of memory errors in V2 notebooks

**Solution**:
- Reduce batch size (16 → 8 → 4)
- Clear GPU cache between batches (`torch.cuda.empty_cache()`)
- Use gradient checkpointing if available
- Monitor memory with cell outputs

### Missing Abstracts

**Symptom**: Many papers lack abstracts in v5.1_cleaned.csv

**Current Status**: ✅ 90.87% abstract coverage (validated)

**If issues arise**:
- Already documented in V5.1_DATA_QUALITY_REPORT.md
- Expected to handle gracefully (title-only fallback)
- Note in final report

### Drive Storage Limits

**Symptom**: Running out of Google Drive space

**Solution**:
- Check Drive quota before starting
- Expected usage: ~50-100 MB total for all results
- Clean up old experiment archives if needed
- Use compression for large result files

---

## Success Criteria Review

### Must Have ✅

- [ ] **Classification**: Both models run successfully on 150k papers
- [ ] **NER**: Both models run successfully on classified positives
- [ ] **Inventories**: Resource inventories generated for both NER models
- [ ] **Benchmarks**: Performance metrics collected for all models
- [ ] **Report**: Comprehensive comparison report completed

### Should Have 📊

- [ ] Novel discoveries identified and validated
- [ ] Agreement analysis between models at both classification and NER levels
- [ ] Performance vs accuracy trade-off analysis
- [ ] Production deployment recommendations

### Nice to Have 🎯

- [ ] Ensemble approach evaluation
- [ ] Error analysis deep-dive
- [ ] Visualization dashboard
- [ ] API integration examples

---

## Next Steps After Phase 2

1. **Review Final Report** (Day 22)
   - Read comprehensive comparison
   - Review executive summary
   - Understand recommendations

2. **Validate Novel Discoveries** (Day 23-25)
   - Manual review of high-confidence discoveries
   - Cross-reference with literature
   - Validate with domain experts

3. **Production Deployment Plan** (Day 26-28)
   - Choose production models based on recommendations
   - Design deployment architecture
   - Set up monitoring and logging
   - Create API endpoints

4. **Documentation & Handoff** (Day 29-30)
   - Update project README
   - Create deployment guide
   - Document API usage
   - Train team on new system

---

## Appendix: Output Directory Structure

```
validation_spacy_v_BERT/results/phase2/
├── classification/
│   ├── v2_classification_150k_SESSION_ID.csv
│   ├── pycaret_classification_150k_SESSION_ID.csv
│   ├── merged_positives_SESSION_ID.csv
│   └── classification_comparison_SESSION_ID.json
│
├── ner/
│   ├── v2_ner_150k_SESSION_ID.csv
│   ├── spacy_ner_150k_SESSION_ID.csv
│   └── ner_comparison_SESSION_ID.json
│
├── inventories/
│   ├── v2_inventory.csv
│   ├── spacy_inventory.csv
│   ├── inventory_comparison.csv
│   ├── novel_discoveries_v2.csv
│   ├── novel_discoveries_spacy.csv
│   └── inventory_metrics.json
│
├── benchmarks/
│   ├── v2_classification_benchmark_SESSION_ID.json
│   ├── pycaret_classification_benchmark_SESSION_ID.json
│   ├── v2_ner_benchmark_SESSION_ID.json
│   └── spacy_ner_benchmark_SESSION_ID.json
│
└── final_report/
    ├── COMPREHENSIVE_MODEL_COMPARISON_REPORT.md
    ├── executive_summary.json
    ├── production_recommendations.md
    └── figures/
        ├── classification_comparison.png
        ├── ner_performance.png
        └── novel_discoveries.png
```

---

**Phase 2 Plan Complete** ✅

**Status**: Ready for notebook creation

**Next**: Create 4 Colab notebooks using code-developer agent
