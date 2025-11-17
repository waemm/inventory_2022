# Phase 1: Manual Validation Study
# 100-125 Unique Resource Papers

**Date**: 2025-11-13
**Prerequisite**: Phase 0 Complete ✅
**Timeline**: 3-4 days
**Outcome**: Detailed comparison report with production recommendations

---

## Objective

Validate and compare all 4 models on a high-quality sample of 100-125 curated bioresource papers:
- **Classification**: V2 BERT vs PyCaret
- **NER**: V2 BERT vs spaCy Hybrid

**Critical Success Factor**: Fetch abstracts from EPMC (previous spaCy validation used titles only → artificially low 48% recall)

---

## Overview

### Steps in Phase 1

1. **Sample Selection** (30 min)
   - Select 50 global core + 50 other papers
   - Remove training overlap
   - Output: `results/validation/sample/validation_sample.csv`

2. **Abstract Fetching** (1-2 hours)
   - Fetch abstracts from EPMC API
   - Handle rate limiting
   - Output: `results/validation/sample/validation_sample_with_abstracts.csv`

3. **Classification Comparison** (2-3 hours)
   - Run V2 classifier (biodata_modern_env)
   - Run PyCaret classifier (pycaret_env)
   - Compare predictions
   - Output: Classification comparison report

4. **NER Comparison** (2-3 hours)
   - Run V2 NER (biodata_modern_env)
   - Run spaCy NER (spacy_hybrid_ner/venv/)
   - Compare entity extractions
   - Output: NER comparison report

5. **Phase 1 Report** (2-3 hours)
   - Aggregate results
   - Generate visualizations
   - Write comprehensive report
   - Decision: Proceed to Phase 2?

**Total Estimated Time**: 1-2 days of development + 1-2 hours runtime

---

## Step 1: Sample Selection

### Script: `scripts/01_select_validation_sample.py`
**Status**: ✅ Already Created
**Environment**: Any (uses pandas only)

### Usage

```bash
cd /Users/warren/development/GBC/inventory_2022/
python scripts/01_select_validation_sample.py
```

### What It Does

1. **Loads Ground Truth**:
   - File: `/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv`
   - 4,560 curated papers with known resources

2. **Loads Training IDs** (to exclude):
   - Classification training: `data/classif_splits_full/train_paper_classif.csv`
   - NER training: `data/ner_splits_full/train.csv`

3. **Stratified Sampling**:
   - **Tier 1**: 50 papers with `is_global_core_biodata_resource=1`
     - Major databases: UniProt, PDB, Ensembl, KEGG, etc.
   - **Tier 2**: 50 papers with `is_global_core_biodata_resource=0`
     - Other validated bioresources
   - Random seed: 42 (reproducible)

4. **Outputs**:
   - File: `results/validation/sample/validation_sample.csv`
   - Columns: publication_id, pubmed_id, title, resource_short_name, resource_full_name, is_global_core_biodata_resource, etc.

### Expected Output

```
✅ Sample Selection Complete
   - Global core papers: 50
   - Other papers: 50
   - Total papers: 100
   - Unique resources: ~100
   - Training overlap removed: X papers
   - Saved to: results/validation/sample/validation_sample.csv
```

---

## Step 2: Fetch Abstracts from EPMC

### Script: `scripts/02_fetch_abstracts.py`
**Status**: ❌ Needs Creation
**Environment**: biodata_modern_env (has requests library)

### Why This is CRITICAL

**Previous spaCy Validation Issue**:
- Used titles only (no abstracts)
- Result: Recall = 48% (artificially low)
- With abstracts, expect: Recall = 60-80%

**V2 Models Context**:
- V2 models trained on title+abstract
- Must compare on same input for fair evaluation

### Implementation

```python
#!/usr/bin/env python3
"""
Fetch Abstracts from EPMC API
==============================

Fetches abstracts for papers in validation sample.

Usage:
    python scripts/02_fetch_abstracts.py
"""

import pandas as pd
import requests
import time
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
SAMPLE_FILE = Path("results/validation/sample/validation_sample.csv")
OUTPUT_FILE = Path("results/validation/sample/validation_sample_with_abstracts.csv")

# EPMC API
EPMC_API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

def fetch_abstract(pmid):
    """Fetch abstract for a single PMID from EPMC"""
    params = {
        'query': f'ext_id:{pmid}',
        'resultType': 'core',
        'format': 'json'
    }

    try:
        response = requests.get(EPMC_API_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = data.get('resultList', {}).get('result', [])

        if results:
            abstract = results[0].get('abstractText', '')
            return abstract
        else:
            logger.warning(f"No results for PMID {pmid}")
            return None

    except Exception as e:
        logger.error(f"Error fetching PMID {pmid}: {e}")
        return None

def main():
    """Main execution"""
    logger.info("Loading validation sample...")
    df = pd.read_csv(SAMPLE_FILE)
    logger.info(f"Loaded {len(df)} papers")

    # Identify ID column
    id_col = None
    for col in ['pubmed_id', 'PMID', 'pmid', 'publication_id']:
        if col in df.columns:
            id_col = col
            break

    if not id_col:
        raise ValueError(f"No ID column found. Columns: {list(df.columns)}")

    logger.info(f"Using ID column: {id_col}")

    # Fetch abstracts
    abstracts = []
    for idx, row in df.iterrows():
        pmid = row[id_col]

        # Check if already has abstract
        if 'abstract' in df.columns and pd.notna(row.get('abstract')):
            logger.info(f"[{idx+1}/{len(df)}] PMID {pmid}: Already has abstract")
            abstracts.append(row.get('abstract'))
            continue

        # Fetch from EPMC
        logger.info(f"[{idx+1}/{len(df)}] Fetching abstract for PMID {pmid}...")
        abstract = fetch_abstract(pmid)
        abstracts.append(abstract if abstract else '')

        # Rate limiting: max 10 requests/sec
        time.sleep(0.15)

    # Add abstracts to DataFrame
    df['abstract'] = abstracts

    # Count papers with abstracts
    has_abstract = df['abstract'].notna() & (df['abstract'] != '')
    logger.info(f"\nAbstract availability:")
    logger.info(f"   Papers with abstracts: {has_abstract.sum()}/{len(df)}")
    logger.info(f"   Papers without abstracts: {(~has_abstract).sum()}/{len(df)}")

    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"\n✅ Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
```

### Expected Output

```
Loading validation sample...
Loaded 100 papers
Using ID column: pubmed_id

[1/100] Fetching abstract for PMID 12345678...
[2/100] Fetching abstract for PMID 23456789...
...
[100/100] Fetching abstract for PMID 98765432...

Abstract availability:
   Papers with abstracts: 98/100
   Papers without abstracts: 2/100

✅ Saved to: results/validation/sample/validation_sample_with_abstracts.csv
```

**Timeline**: 1-2 hours (depends on API response time)

---

## Step 3: Classification Comparison

### Step 3a: Run V2 Classification

**Script**: `scripts/03a_run_v2_classification.py`
**Status**: ❌ Needs Creation
**Environment**: biodata_modern_env

### Implementation

```python
#!/usr/bin/env python3
"""
Run V2 BERT Classification on Validation Sample
================================================

Usage:
    source biodata_modern_env/bin/activate
    python scripts/03a_run_v2_classification.py
"""

import sys
import pandas as pd
from pathlib import Path
import subprocess

# Paths
SAMPLE_FILE = Path("results/validation/sample/validation_sample_with_abstracts.csv")
OUTPUT_DIR = Path("results/validation/classification/")
MODEL_PATH = Path("out/classif_train_out/article_classifier_v2.pt")

def main():
    print("=" * 60)
    print("V2 BERT Classification on Validation Sample")
    print("=" * 60)

    # Check model exists
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    # Check sample exists
    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(f"Sample not found: {SAMPLE_FILE}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Prepare input for V2 classifier
    df = pd.read_csv(SAMPLE_FILE)
    print(f"Loaded {len(df)} papers")

    # Ensure required columns
    if 'title' not in df.columns:
        raise ValueError("Missing 'title' column")
    if 'abstract' not in df.columns:
        raise ValueError("Missing 'abstract' column")

    # Create ID column if needed
    if 'id' not in df.columns:
        if 'pubmed_id' in df.columns:
            df['id'] = df['pubmed_id']
        elif 'publication_id' in df.columns:
            df['id'] = df['publication_id']
        else:
            df['id'] = range(len(df))

    # Save prepared input
    input_file = OUTPUT_DIR / "v2_input.csv"
    df[['id', 'title', 'abstract']].to_csv(input_file, index=False, encoding='ISO-8859-1')
    print(f"Prepared input: {input_file}")

    # Run V2 classifier
    print("\nRunning V2 classifier...")
    cmd = [
        'python', 'src/class_predict.py',
        '-c', str(MODEL_PATH),
        '-i', str(input_file),
        '-o', str(OUTPUT_DIR / 'v2_raw/'),
        '--predictive-field', 'title_abstract',
        '--batch-size', '8'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        raise RuntimeError("V2 classifier failed")

    print("✅ V2 classification complete")

    # Load and save predictions
    pred_file = OUTPUT_DIR / 'v2_raw' / 'classification_results.csv'
    if pred_file.exists():
        df_pred = pd.read_csv(pred_file, encoding='ISO-8859-1')
        df_pred.to_csv(OUTPUT_DIR / 'v2_predictions.csv', index=False)
        print(f"✅ Saved to: {OUTPUT_DIR / 'v2_predictions.csv'}")

        # Summary
        if 'predicted_label' in df_pred.columns:
            pos_count = (df_pred['predicted_label'] == 'bio-resource').sum()
            print(f"\nPredictions:")
            print(f"   Positive: {pos_count}/{len(df_pred)}")
            print(f"   Negative: {len(df_pred) - pos_count}/{len(df_pred)}")

if __name__ == "__main__":
    main()
```

**Timeline**: 30-45 min (model runtime + script creation)

---

### Step 3b: Run PyCaret Classification

**Script**: `scripts/03b_run_pycaret_classification.py`
**Status**: ❌ Needs Creation
**Environment**: pycaret_env

**Implementation Notes**:
- Must merge with V5.1 metadata to get features
- Requires feature engineering (92 or 112 columns)
- Adapt from: `comparison_pycaret_v2/scripts/03_pycaret_prediction.py`

**Timeline**: 1-2 hours (script creation + feature engineering setup)

---

### Step 3c: Compare Classifications

**Script**: `scripts/03c_compare_classification.py`
**Status**: ❌ Needs Creation
**Environment**: Any

**What It Does**:
1. Load ground truth labels (all papers should be positives)
2. Load V2 predictions
3. Load PyCaret predictions
4. Calculate metrics (accuracy, precision, recall, F1)
5. Generate confusion matrices
6. Identify disagreements
7. Save report

**Output**: `results/validation/classification/classification_comparison_report.md`

**Timeline**: 30-45 min

---

## Step 4: NER Comparison

### Step 4a: Run V2 NER

**Script**: `scripts/04a_run_v2_ner.py`
**Status**: ❌ Needs Creation
**Environment**: biodata_modern_env

**Implementation**:
```python
#!/usr/bin/env python3
"""
Run V2 BERT NER on Validation Sample
====================================

Usage:
    source biodata_modern_env/bin/activate
    python scripts/04a_run_v2_ner.py
"""

import sys
import pandas as pd
from pathlib import Path
import subprocess

# Paths
SAMPLE_FILE = Path("results/validation/sample/validation_sample_with_abstracts.csv")
OUTPUT_DIR = Path("results/validation/ner/")
MODEL_PATH = Path("out/ner_train_out/named_entity_recognition_v2.pt")

def main():
    print("=" * 60)
    print("V2 BERT NER on Validation Sample")
    print("=" * 60)

    # Check model exists
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    # Check sample exists
    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(f"Sample not found: {SAMPLE_FILE}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Prepare input
    df = pd.read_csv(SAMPLE_FILE)
    print(f"Loaded {len(df)} papers")

    # Ensure required columns
    required = ['id', 'title', 'abstract', 'publication_date']
    for col in ['id', 'publication_date']:
        if col not in df.columns:
            if col == 'id' and 'pubmed_id' in df.columns:
                df['id'] = df['pubmed_id']
            elif col == 'publication_date' and 'pubYear' in df.columns:
                df['publication_date'] = df['pubYear'].astype(str) + '-01-01'
            else:
                df[col] = ''

    # Save prepared input
    input_file = OUTPUT_DIR / "v2_ner_input.csv"
    df[['id', 'title', 'abstract', 'publication_date']].to_csv(
        input_file, index=False, encoding='ISO-8859-1'
    )
    print(f"Prepared input: {input_file}")

    # Run V2 NER
    print("\nRunning V2 NER...")
    cmd = [
        'python', 'src/ner_predict.py',
        '-c', str(MODEL_PATH),
        '-i', str(input_file),
        '-o', str(OUTPUT_DIR / 'v2_ner_raw/')
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        raise RuntimeError("V2 NER failed")

    print("✅ V2 NER complete")

    # Load and process results
    pred_file = OUTPUT_DIR / 'v2_ner_raw' / 'ner_results.csv'
    if pred_file.exists():
        df_pred = pd.read_csv(pred_file, encoding='ISO-8859-1')
        df_pred.to_csv(OUTPUT_DIR / 'v2_ner_predictions.csv', index=False)
        print(f"✅ Saved to: {OUTPUT_DIR / 'v2_ner_predictions.csv'}")

        # Summary
        papers_with_entities = df_pred[
            (df_pred['common_name'].notna() & (df_pred['common_name'] != '')) |
            (df_pred['full_name'].notna() & (df_pred['full_name'] != ''))
        ]
        print(f"\nResults:")
        print(f"   Papers with entities: {len(papers_with_entities)}/{len(df_pred)}")

if __name__ == "__main__":
    main()
```

**Timeline**: 30-45 min

---

### Step 4b: Run spaCy NER

**Script**: `scripts/04b_run_spacy_ner.py`
**Status**: ❌ Needs Creation
**Environment**: spacy_hybrid_ner/venv/

**Implementation**:
```python
#!/usr/bin/env python3
"""
Run spaCy Hybrid NER on Validation Sample
==========================================

Usage:
    source spacy_hybrid_ner/venv/bin/activate
    python scripts/04b_run_spacy_ner.py
"""

import sys
sys.path.insert(0, 'src')

import pandas as pd
from pathlib import Path
from ner_predict_spacy import SpacyNERPredictor

# Paths
SAMPLE_FILE = Path("results/validation/sample/validation_sample_with_abstracts.csv")
OUTPUT_DIR = Path("results/validation/ner/")
MODEL_PATH = Path("spacy_hybrid_ner/models/ner_hybrid_v2_com_ful")

def main():
    print("=" * 60)
    print("spaCy Hybrid NER on Validation Sample")
    print("=" * 60)

    # Check model exists
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    # Check sample exists
    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(f"Sample not found: {SAMPLE_FILE}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load sample
    df = pd.read_csv(SAMPLE_FILE)
    print(f"Loaded {len(df)} papers")

    # Prepare for spaCy
    if 'pubmed_id' not in df.columns and 'id' in df.columns:
        df['pubmed_id'] = df['id']

    # Initialize predictor
    print(f"\nLoading spaCy model from: {MODEL_PATH}")
    predictor = SpacyNERPredictor(str(MODEL_PATH))

    # Run prediction
    print("\nRunning spaCy NER...")
    output_file = OUTPUT_DIR / 'spacy_ner_predictions.csv'
    df_output = predictor.predict_to_csv(
        df,
        str(output_file),
        batch_size=32
    )

    print(f"✅ Saved to: {output_file}")

    # Summary
    if df_output is not None and len(df_output) > 0:
        papers_with_entities = df_output['pmid'].nunique()
        total_entities = len(df_output)
        print(f"\nResults:")
        print(f"   Papers with entities: {papers_with_entities}/{len(df)}")
        print(f"   Total entities: {total_entities}")
    else:
        print("\n⚠️  No entities found")

if __name__ == "__main__":
    main()
```

**Timeline**: 30-45 min

---

### Step 4c: Compare NER Results

**Script**: `scripts/04c_compare_ner.py`
**Status**: ❌ Needs Creation
**Environment**: Any

**What It Does**:
1. Load ground truth resources (resource_short_name, resource_full_name)
2. Load V2 NER predictions (COM, FUL)
3. Load spaCy NER predictions (entities with canonical IDs)
4. Calculate entity-level metrics (exact match, partial match, P/R/F1)
5. Calculate resource-level coverage
6. Analyze alias resolution (spaCy only)
7. Generate comparison report

**Key Challenges**:
- Different output formats (V2: wide format with comma-separated entities, spaCy: long format with one entity per row)
- Need to normalize entity text for comparison
- Need to handle partial matches

**Output**: `results/validation/ner/ner_comparison_report.md`

**Timeline**: 1-2 hours (complex comparison logic)

---

## Step 5: Generate Phase 1 Report

### Script: `scripts/05_generate_phase1_report.py`
**Status**: ❌ Needs Creation
**Environment**: Any

### What It Generates

**Report Sections**:
1. **Executive Summary**
   - Key findings
   - Model recommendations
   - Critical insights

2. **Classification Comparison**
   - Metrics (accuracy, precision, recall, F1)
   - Confusion matrices
   - Disagreement analysis
   - Speed comparison

3. **NER Comparison**
   - Entity-level metrics
   - Resource-level coverage
   - Alias resolution quality (spaCy)
   - Speed comparison

4. **Trade-Off Analysis**
   - Accuracy vs Speed
   - GPU vs CPU requirements
   - Deployment complexity
   - Resource usage

5. **Recommendations**
   - Which models for production?
   - Hybrid approaches?
   - Proceed to Phase 2?

**Output**: `results/validation/PHASE1_VALIDATION_REPORT.md`

**Timeline**: 2-3 hours

---

## Expected Results

### Classification

**V2 BERT**:
- Expected: 95-100% recall (may miss 0-5 papers due to edge cases)
- Precision: 100% (all true positives, but may have false positives)
- Speed: 5-10 papers/sec

**PyCaret**:
- Expected: 85-90% recall (may miss 10-15 papers)
- Precision: ~90-95%
- Speed: 20-50 papers/sec (5-10× faster!)

### NER (WITH ABSTRACTS - CRITICAL!)

**V2 BERT**:
- Expected F1: 66-75% (based on test set performance)
- Precision: ~70-80%
- Recall: ~65-75%
- Speed: 2-5 papers/sec

**spaCy Hybrid**:
- Expected F1: 70-80% (with abstracts, vs 63% title-only)
- Precision: ~85-90% (EntityRuler high precision)
- Recall: 60-75% (expected improvement from 48% title-only)
- Speed: 100-200 papers/sec (40-100× faster!)
- Bonus: Alias resolution (100% with canonical IDs)

### Key Insight Expected

**spaCy will show MUCH better recall than previous 48%** because:
1. Previous validation used titles only
2. This validation uses title+abstract
3. Most bioresource mentions are in abstracts
4. Expected improvement: +20-30pp recall

---

## Scripts Summary

### Total Scripts to Create: 5

| # | Script | Environment | Lines | Status |
|---|--------|-------------|-------|--------|
| 2 | `02_fetch_abstracts.py` | biodata_modern_env | ~100 | ❌ TODO |
| 3a | `03a_run_v2_classification.py` | biodata_modern_env | ~80 | ❌ TODO |
| 3b | `03b_run_pycaret_classification.py` | pycaret_env | ~150 | ❌ TODO |
| 3c | `03c_compare_classification.py` | Any | ~200 | ❌ TODO |
| 4a | `04a_run_v2_ner.py` | biodata_modern_env | ~100 | ❌ TODO |
| 4b | `04b_run_spacy_ner.py` | spacy_hybrid_ner/venv/ | ~80 | ❌ TODO |
| 4c | `04c_compare_ner.py` | Any | ~250 | ❌ TODO |
| 5 | `05_generate_phase1_report.py` | Any | ~300 | ❌ TODO |

**Total**: ~1,260 lines of code to write

**Estimated Development Time**: 1-2 days

---

## Execution Checklist

### Pre-Execution
- [x] Phase 0 complete (all models verified)
- [ ] User approval to proceed
- [ ] GPU available (optional but recommended for V2 models)

### Execution Steps
- [ ] Run sample selection (`scripts/01_select_validation_sample.py`)
- [ ] Create and run abstract fetching script
- [ ] Create and run V2 classification script
- [ ] Create and run PyCaret classification script
- [ ] Create and run classification comparison script
- [ ] Create and run V2 NER script
- [ ] Create and run spaCy NER script
- [ ] Create and run NER comparison script
- [ ] Create and run Phase 1 report generation script
- [ ] Review Phase 1 report
- [ ] Decision: Proceed to Phase 2?

---

## Timeline

### Optimistic (1-2 days)
- Day 1: Create all scripts (6-8 hours)
- Day 2: Run all steps, generate report (2-3 hours runtime)

### Realistic (3-4 days)
- Day 1-2: Create and debug scripts (8-12 hours)
- Day 3: Run all steps (2-3 hours runtime)
- Day 4: Analyze results, write report (3-4 hours)

### Pessimistic (5-7 days)
- Issues with API rate limiting, model errors, etc.
- Need to iterate on scripts
- Additional validation needed

---

## Decision Point

**After Phase 1 is complete, decide**:

**✅ Proceed to Phase 2 if**:
- All 4 models ran successfully
- Results make sense (no obvious bugs)
- Trade-offs are clear and quantified
- Methodology is sound

**⏸️ Pause and adjust if**:
- Models failing or producing nonsense
- Methodology issues discovered
- Need to refine comparison approach
- Unexpected findings require investigation

**❌ Stop if**:
- Models fundamentally broken
- Cannot get fair comparison
- Data quality issues
- Resource constraints prohibitive

---

**Document**: `plans/validation_spacy_v_BERT/PHASE1_MANUAL_VALIDATION.md`
**Lines**: ~545
**Status**: Ready for implementation
**Next**: Create Phase 2 and Appendix documents
