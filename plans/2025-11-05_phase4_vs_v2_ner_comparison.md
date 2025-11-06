# Phase 4 vs V2 NER Comparison Study Plan

**Date**: 2025-11-05
**Purpose**: Comprehensive comparison study of Phase 4 multi-task NER vs V2 original NER model on 2022 inference outputs
**Status**: Planning & Implementation
**Priority**: High - Critical for validating Phase 4 improvements

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Research Findings](#research-findings)
3. [Implementation Plan](#implementation-plan)
4. [Directory Structure](#directory-structure)
5. [Technical Details](#technical-details)
6. [Timeline & Milestones](#timeline--milestones)
7. [Success Criteria](#success-criteria)
8. [References](#references)

---

## Executive Summary

### Study Objectives

This plan documents a comprehensive comparison between two NER systems to validate claimed performance improvements and identify real-world impact on entity extraction quality.

**Primary Goals**:
1. **Quantitative Analysis**: Measure precision, recall, F1 differences on 2022 papers
2. **Qualitative Analysis**: Analyze entity quality, error patterns, BPE artifacts
3. **Ground Truth Validation**: Compare both models against manually annotated entities
4. **Production Readiness**: Determine if Phase 4 is ready for deployment

**Key Questions**:
- Is the +23.82% F1 improvement real or an artifact of evaluation methodology?
- Does Phase 4 extract higher-quality entities than V2?
- What is the impact of BPE tokenization on Phase 4 output quality?
- Are Phase 4's additional predictions (4.8x more rows) true positives or noise?

### Critical Context

**V2 Original Model**:
- Training F1: 0.749 (entity-level evaluation with seqeval)
- Clean, post-processed output (4,395 papers)
- Separate NER model (BERT-based, 5 BIO labels)
- Ready-to-use entity names

**Phase 4 Multi-Task Model**:
- Training F1: 0.9274 (token-level evaluation with sklearn) - **+23.82% improvement**
- Raw, tokenized output (20,890 papers - 4.8x more predictions)
- Unified multi-task model (3 BIO labels with metadata)
- **BPE artifacts found**: Needs post-processing

**Critical Discovery**: Phase 4 outputs raw BPE tokens (e.g., "ĠRat, ĠGen, ome, ĠDatabase") while V2 outputs clean strings (e.g., "Rat Genome Database"). This format mismatch prevents direct comparison.

---

## Research Findings

### V2 NER Results

**Location**: `/Users/warren/development/GBC/inventory_2022/collab_results/2025-10-27-7mvru2_oldmodel_2022_rerun/ner_results.csv`

**Characteristics**:
- **Run Date**: 2025-10-27
- **Training Session**: 2025-10-24-apz1py
- **Pipeline**: `rerun_2022_inventory_simplified.ipynb`
- **Output Script**: `src/ner_predict.py`
- **Model Type**: Separate single-task NER (5 BIO labels)

**Output Format** (7 columns):
```
ID, text, publication_date, common_name, common_prob, full_name, full_prob
```

**Statistics**:
- **Total rows**: 4,395 (one row per paper)
- **Unique papers**: 4,395
- **Format**: Clean entity names (post-processed)
- **Probabilities**: Single averaged score per entity
- **Metadata**: Includes full abstract text and publication date

**Example Output**:
```csv
21063943,"PRIDE and Database on Demand...",2011-01-01,"DoD, PRIDE","0.8464635, 0.99868494",Proteomics Identifications Database,0.9936275
```

**Key Strengths**:
- ✅ Clean, ready-to-use entity names
- ✅ Post-processed through `reformat_output()` function
- ✅ Includes metadata (text, publication_date)
- ✅ Validated format used in production

### Phase 4 NER Results

**Location**: `/Users/warren/development/GBC/inventory_2022/collab_results/experiment_archives/2025-11-05-1f3ixn_phase4_2022_rerun/ner_results.csv`

**Characteristics**:
- **Run Date**: 2025-11-05
- **Training Session**: Phase 4 multi-task learning
- **Pipeline**: `phase4_full_inference_2022_FIXED.ipynb`
- **Output Script**: `src/multitask_predict.py`
- **Model Type**: Multi-task (classification + NER, 3 BIO labels)

**Output Format** (5 columns):
```
ID, common_name, common_prob, full_name, full_prob
```

**Statistics**:
- **Total rows**: 20,890 (4.8x more than V2)
- **Unique papers**: 20,889
- **Format**: Raw BPE tokenized (needs post-processing)
- **Probabilities**: Comma-separated per-token scores
- **Metadata**: Missing (no text or publication_date)

**Example Output**:
```csv
21063943.0,"ĠPro, te, omics, ĠIdent, ifications, ĠDatabase","0.999, 1.000, 1.000, 1.000, 1.000, 1.000",,
```

**Critical Issues Found**:
- ⚠️ **BPE tokenization**: "ĠRat, ĠGen, ome, ĠDatabase" instead of "Rat Genome Database"
- ⚠️ **'Ġ' prefix**: Indicates space before token in BPE encoding
- ⚠️ **Per-token probabilities**: "0.999, 1.000, 1.000, ..." needs averaging
- ❌ **Missing metadata**: No abstract text or publication_date columns
- ⚠️ **4.8x more predictions**: Requires investigation (true positives or duplicates?)

**BPE Artifact Examples**:
```
Entity            V2 Output              Phase 4 Output (Raw)
----------------  ---------------------  ----------------------------------------
InterPro          "InterPro"             "Inter, Pro, ĠInter, Pro"
mESAdb            "mESAdb"               "Ġmicro, RNA, Ġexpression, Ġand, Ġsequence"
PRIDE             "PRIDE"                "ĠPro, te, omics, ĠIdent, ifications"
```

### Ground Truth Data Sources

**NER Training Set**:
- **Location**: `data/ner_splits_full/train_ner.csv`
- **Size**: 307 training samples, 67 validation, 67 test
- **Contains**: Manually annotated compound names and full names
- **Columns**: `id`, `title`, `abstract`, `compound_name`, `full_name`, `labels`

**Challenge**: The 2022 rerun dataset (21,677 papers) is **different** from the training/test splits (441 papers total). There is likely minimal overlap between:
- Training/validation/test sets (used for model development)
- 2022 EPMC query results (used for production inference)

**Available Ground Truth Options**:
1. **Manual annotation**: Select random sample of 2022 papers and annotate
2. **Training set overlap**: Find papers present in both 2022 and training data
3. **Distant supervision**: Use known database names as weak labels
4. **Expert review**: Human validation of model outputs

**Recommendation**: Use a combination approach:
- Find training set overlap (if any) for quantitative metrics
- Manually annotate 100 random 2022 papers for qualitative analysis
- Expert review of disagreement cases between V2 and Phase 4

---

## Implementation Plan

### Script 1: Post-Process Phase 4 Output

**Purpose**: Convert raw Phase 4 BPE tokens to clean entity names matching V2 format

**File**: `scripts/postprocess_phase4_ner.py`

**Methodology**:
1. **BPE Detokenization**:
   ```python
   def detokenize_bpe(tokens_str):
       """
       Input: "ĠPro, te, omics, ĠIdent, ifications, ĠDatabase"
       Output: "Proteomics Identifications Database"
       """
       tokens = tokens_str.split(', ')
       # Remove 'Ġ' prefix (indicates space)
       # Join tokens: "Ġ" → space, no prefix → direct concatenation
       result = []
       for token in tokens:
           if token.startswith('Ġ'):
               result.append(' ' + token[1:])
           else:
               result.append(token)
       return ''.join(result).strip()
   ```

2. **Probability Aggregation**:
   ```python
   def aggregate_probabilities(prob_str):
       """
       Input: "0.999, 1.000, 1.000, 1.000, 1.000, 1.000"
       Output: 0.9998 (arithmetic mean)
       """
       probs = [float(p) for p in prob_str.split(', ')]
       return sum(probs) / len(probs)
   ```

3. **Deduplication**:
   ```python
   def deduplicate_entities(df):
       """
       Phase 4 has multiple predictions per paper (20,890 rows for 20,889 papers)
       Group by paper ID and deduplicate entities
       """
       # Group by ID
       # For each entity, keep highest probability instance
       # Remove exact duplicates (case-insensitive)
       # Return one row per paper with comma-separated entities
   ```

4. **Reformat to Wide Format**:
   ```python
   def reformat_to_wide(df):
       """
       Transform from long format (multiple rows per paper)
       to wide format (one row per paper)
       Matching V2 structure: ID, common_name, common_prob, full_name, full_prob
       """
   ```

**Output**: `comparison_phase4_v_oldmodel/phase4_ner_cleaned.csv` (matching V2 format)

**Validation**:
- Check for remaining 'Ġ' tokens (should be zero)
- Verify probability ranges (0.0 to 1.0)
- Confirm one row per paper
- Spot-check entity readability

---

### Script 2: Entity-Level Comparison

**Purpose**: Compare entity extraction between V2 and Phase 4 at the entity level

**File**: `scripts/compare_entity_extraction.py`

**Methodology**:

1. **Load Both Datasets**:
   ```python
   v2_df = pd.read_csv('v2_ner_results.csv')
   phase4_df = pd.read_csv('phase4_ner_cleaned.csv')  # Post-processed
   ```

2. **Entity Matching Strategy**:
   ```python
   def match_entities(entity1, entity2):
       """
       Match entities with fuzzy matching to handle variations:
       - Case-insensitive comparison
       - Whitespace normalization
       - Partial matches (substring containment)
       - Edit distance threshold (Levenshtein)
       """
       # Exact match (case-insensitive)
       if entity1.lower() == entity2.lower():
           return 'exact'

       # Substring match
       if entity1.lower() in entity2.lower() or entity2.lower() in entity1.lower():
           return 'substring'

       # Edit distance (fuzzy)
       from Levenshtein import ratio
       if ratio(entity1.lower(), entity2.lower()) >= 0.85:
           return 'fuzzy'

       return 'no_match'
   ```

3. **Categorize Predictions**:
   ```python
   # For each paper:
   v2_entities = set(parse_entities(v2_row))
   phase4_entities = set(parse_entities(phase4_row))

   # Agreement: Both models extracted same entity
   agreement = v2_entities & phase4_entities

   # V2-only: Entity in V2 but not Phase 4 (potential Phase 4 miss)
   v2_only = v2_entities - phase4_entities

   # Phase4-only: Entity in Phase 4 but not V2 (potential new discovery or FP)
   phase4_only = phase4_entities - v2_entities
   ```

4. **Compute Metrics**:
   ```python
   # Overlap metrics
   overlap_rate = len(agreement) / len(v2_entities | phase4_entities)

   # Extraction coverage
   v2_coverage = len(v2_entities)  # Average per paper
   phase4_coverage = len(phase4_entities)

   # Delta statistics
   more_entities = len(phase4_only) - len(v2_only)
   ```

**Output**:
- `comparison_phase4_v_oldmodel/entity_comparison_stats.csv`
- `comparison_phase4_v_oldmodel/agreement_cases.csv`
- `comparison_phase4_v_oldmodel/v2_only_entities.csv`
- `comparison_phase4_v_oldmodel/phase4_only_entities.csv`

**Statistics Tracked**:
- Total entities per model
- Agreement rate (%)
- V2-only count and examples
- Phase4-only count and examples
- Per-paper entity count distribution

---

### Script 3: Confidence Analysis

**Purpose**: Analyze prediction confidence scores and relationship to accuracy

**File**: `scripts/analyze_confidence_scores.py`

**Methodology**:

1. **Confidence Distribution**:
   ```python
   # Histogram of confidence scores
   v2_confidences = extract_probabilities(v2_df)
   phase4_confidences = extract_probabilities(phase4_df)

   plot_distributions(v2_confidences, phase4_confidences)
   ```

2. **Confidence vs Accuracy**:
   ```python
   # For high-confidence predictions (>0.95), what % are correct?
   # For low-confidence predictions (<0.7), what % are correct?
   # Requires ground truth for validation
   ```

3. **Calibration Analysis**:
   ```python
   # Are the confidence scores well-calibrated?
   # If model says 90% confident, is it correct 90% of the time?
   ```

**Output**:
- `comparison_phase4_v_oldmodel/confidence_histograms.png`
- `comparison_phase4_v_oldmodel/confidence_by_accuracy.csv`
- `comparison_phase4_v_oldmodel/calibration_plot.png`

---

### Script 4: Error Pattern Analysis

**Purpose**: Identify systematic errors and failure modes for each model

**File**: `scripts/analyze_error_patterns.py`

**Methodology**:

1. **Categorize Errors**:
   ```python
   error_types = [
       'partial_entity',      # "Protein Data" instead of "Protein Data Bank"
       'wrong_boundary',      # Includes extra/missing tokens
       'false_positive',      # Not actually a database name
       'missed_entity',       # Present in text but not extracted
       'tokenization_error',  # BPE artifacts (Phase 4 specific)
       'type_confusion'       # Common vs Full name mismatch (V2 specific)
   ]
   ```

2. **Pattern Detection**:
   ```python
   # Does Phase 4 struggle with specific entity types?
   # Does V2 miss long entities more often?
   # Are there specific tokens that cause problems?
   ```

3. **Examples Collection**:
   ```python
   # For each error type, collect top 20 examples
   # Show: PMID, true entity, predicted entity, context
   ```

**Output**:
- `comparison_phase4_v_oldmodel/error_patterns_v2.csv`
- `comparison_phase4_v_oldmodel/error_patterns_phase4.csv`
- `comparison_phase4_v_oldmodel/error_comparison_report.md`

---

### Script 5: BPE Artifact Detection

**Purpose**: Quantify and document BPE tokenization issues in Phase 4 output

**File**: `scripts/detect_bpe_artifacts.py`

**Methodology**:

1. **Artifact Patterns**:
   ```python
   bpe_issues = [
       'orphan_g_prefix',     # Entities starting with "Ġ"
       'excessive_splits',    # >10 tokens for short entity
       'duplicate_subwords',  # "Inter, Pro, ĠInter, Pro"
       'incomplete_join',     # Missing spaces or concatenation
       'special_char_split',  # Splits on parentheses, hyphens
   ]
   ```

2. **Detection Logic**:
   ```python
   def detect_artifacts(entity_str):
       artifacts = []

       # Check for 'Ġ' in cleaned output
       if 'Ġ' in entity_str:
           artifacts.append('orphan_g_prefix')

       # Check for unusual tokenization
       tokens = entity_str.split(', ')
       if len(tokens) > 10 and len(entity_str) < 50:
           artifacts.append('excessive_splits')

       # Check for duplicates
       if len(tokens) != len(set(tokens)):
           artifacts.append('duplicate_subwords')

       return artifacts
   ```

3. **Impact Assessment**:
   ```python
   # How many entities are affected?
   # What % of Phase 4 output has artifacts?
   # Does post-processing fully resolve issues?
   ```

**Output**:
- `comparison_phase4_v_oldmodel/bpe_artifacts_report.csv`
- `comparison_phase4_v_oldmodel/bpe_artifacts_examples.txt`
- `comparison_phase4_v_oldmodel/bpe_cleaning_effectiveness.md`

**Validation**:
- **Before cleaning**: Count 'Ġ' occurrences in raw Phase 4 output
- **After cleaning**: Should be zero 'Ġ' in final entities
- **Success metric**: >99% of entities properly detokenized

---

### Script 6: Ground Truth Validation

**Purpose**: Compare both models against manually annotated entities

**File**: `scripts/validate_against_ground_truth.py`

**Methodology**:

1. **Load Ground Truth**:
   ```python
   # Option 1: Training set papers (if overlap exists)
   gt_df = pd.read_csv('data/ner_splits_full/test_ner.csv')

   # Option 2: Manually annotated 2022 sample
   gt_df = pd.read_csv('data/manual_annotations_2022_sample.csv')
   ```

2. **Compute Standard NER Metrics**:
   ```python
   from sklearn.metrics import precision_recall_fscore_support

   # For V2
   v2_precision, v2_recall, v2_f1, _ = compute_metrics(
       true_entities=ground_truth,
       pred_entities=v2_predictions
   )

   # For Phase 4
   phase4_precision, phase4_recall, phase4_f1, _ = compute_metrics(
       true_entities=ground_truth,
       pred_entities=phase4_predictions
   )
   ```

3. **Entity-Level Evaluation** (strict):
   ```python
   def entity_level_metrics(true_entities, pred_entities):
       """
       Strict evaluation: entity must be extracted completely
       Matches seqeval evaluation used in V2 training
       """
       tp = 0  # True positives: exact match
       fp = 0  # False positives: predicted but not in ground truth
       fn = 0  # False negatives: in ground truth but not predicted

       for true_ent in true_entities:
           if any(match_entity(true_ent, pred) == 'exact' for pred in pred_entities):
               tp += 1
           else:
               fn += 1

       for pred_ent in pred_entities:
           if not any(match_entity(pred_ent, true) == 'exact' for true in true_entities):
               fp += 1

       precision = tp / (tp + fp) if (tp + fp) > 0 else 0
       recall = tp / (tp + fn) if (tp + fn) > 0 else 0
       f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

       return precision, recall, f1
   ```

4. **Statistical Significance Testing**:
   ```python
   from scipy.stats import ttest_rel, wilcoxon

   # Paired t-test (if normally distributed)
   t_stat, p_value = ttest_rel(v2_f1_scores, phase4_f1_scores)

   # Or Wilcoxon signed-rank test (non-parametric)
   stat, p_value = wilcoxon(v2_f1_scores, phase4_f1_scores)

   # Is the improvement statistically significant (p < 0.05)?
   ```

**Output**:
- `comparison_phase4_v_oldmodel/ground_truth_metrics.csv`
- `comparison_phase4_v_oldmodel/statistical_tests.txt`
- `comparison_phase4_v_oldmodel/per_paper_scores.csv`

**Key Metrics**:
- Precision (both models)
- Recall (both models)
- F1 Score (both models)
- Improvement (Phase 4 vs V2)
- Statistical significance (p-value)

---

### Script 7: False Positive Investigation

**Purpose**: Analyze Phase 4's 4.8x more predictions - are they valid or noise?

**File**: `scripts/investigate_phase4_extra_predictions.py`

**Methodology**:

1. **Identify Extra Predictions**:
   ```python
   # Phase 4 has 20,890 rows vs V2's 4,395 rows
   # 16,495 additional predictions (+375%)

   # Find papers in Phase 4 but not in V2
   v2_ids = set(v2_df['ID'].unique())
   phase4_ids = set(phase4_df['ID'].unique())
   extra_ids = phase4_ids - v2_ids

   print(f"Papers with Phase 4 predictions only: {len(extra_ids)}")
   ```

2. **Sample Analysis**:
   ```python
   # Randomly sample 100 papers from extra predictions
   sample_papers = random.sample(extra_ids, 100)

   # For each paper:
   #   - Retrieve full abstract
   #   - Show Phase 4 extracted entities
   #   - Manual review: True positive or false positive?
   ```

3. **Pattern Analysis**:
   ```python
   # Are extra predictions concentrated in specific journals?
   # Are they mostly low-confidence predictions?
   # Are they primarily common names or full names?
   # Do they tend to be shorter or longer entities?
   ```

4. **Categorization**:
   ```python
   categories = {
       'true_positive': 0,      # Valid entity, V2 missed it
       'false_positive': 0,     # Not a database name
       'ambiguous': 0,          # Unclear if valid
       'tokenization_issue': 0  # BPE artifact
   }
   ```

**Output**:
- `comparison_phase4_v_oldmodel/extra_predictions_sample.csv` (100 random samples)
- `comparison_phase4_v_oldmodel/extra_predictions_analysis.md`
- `comparison_phase4_v_oldmodel/false_positive_rate_estimate.txt`

**Deliverable**: Manual review spreadsheet with columns:
- PMID
- Paper title
- Phase 4 extracted entities
- Full abstract snippet
- Manual label (TP/FP/Ambiguous)
- Notes

---

### Script 8: Production Readiness Report

**Purpose**: Synthesize all findings into actionable recommendations

**File**: `scripts/generate_comparison_report.py`

**Methodology**:

1. **Aggregate All Statistics**:
   ```python
   # Compile results from Scripts 1-7
   results = {
       'entity_comparison': load_stats('entity_comparison_stats.csv'),
       'confidence_analysis': load_stats('confidence_by_accuracy.csv'),
       'error_patterns': load_stats('error_patterns_*.csv'),
       'bpe_artifacts': load_stats('bpe_artifacts_report.csv'),
       'ground_truth_validation': load_stats('ground_truth_metrics.csv'),
       'extra_predictions': load_stats('extra_predictions_analysis.md'),
   }
   ```

2. **Generate Executive Summary**:
   ```python
   summary = f"""
   ## Comparison Summary

   ### Overall Performance
   - V2 F1: {v2_f1:.3f}
   - Phase 4 F1: {phase4_f1:.3f}
   - Improvement: {improvement:.1f}% (p = {p_value:.4f})

   ### Entity Extraction
   - Agreement rate: {agreement_rate:.1f}%
   - Phase 4 found {extra_entities} more entities
   - False positive rate: {fp_rate:.1f}%

   ### Production Readiness: {status}
   """
   ```

3. **Recommendations**:
   ```python
   recommendations = []

   if phase4_f1 > v2_f1 + 0.05 and fp_rate < 0.10:
       recommendations.append("✅ RECOMMEND: Deploy Phase 4 to production")
   elif phase4_f1 > v2_f1 and fp_rate < 0.20:
       recommendations.append("⚠️  CONDITIONAL: Deploy with monitoring")
   else:
       recommendations.append("❌ NOT READY: Additional training needed")

   if bpe_artifacts_rate > 0.01:
       recommendations.append("⚠️  WARNING: BPE post-processing required")
   ```

4. **Risk Assessment**:
   ```python
   risks = []

   if extra_predictions_fp_rate > 0.15:
       risks.append("HIGH: Elevated false positive rate in new predictions")

   if bpe_cleaning_success < 0.99:
       risks.append("MEDIUM: BPE artifacts not fully resolved")

   if metadata_coverage < 1.0:
       risks.append("MEDIUM: Metadata dependency for Phase 4")
   ```

**Output**: `comparison_phase4_v_oldmodel/COMPARISON_REPORT.md`

**Report Sections**:
1. Executive Summary
2. Methodology Overview
3. Quantitative Results (tables and charts)
4. Qualitative Findings
5. Error Analysis
6. Recommendations
7. Risk Assessment
8. Next Steps

---

## Directory Structure

```
comparison_phase4_v_oldmodel/
│
├── README.md                              # Study overview and navigation
│
├── raw_data/                              # Original NER outputs
│   ├── v2_ner_results.csv                # V2 output (4,395 rows)
│   ├── phase4_ner_results_raw.csv        # Phase 4 raw output (20,890 rows)
│   └── data_summary.txt                  # Row counts, columns, timestamps
│
├── processed_data/                        # Cleaned and transformed data
│   ├── phase4_ner_cleaned.csv            # Phase 4 after BPE detokenization
│   ├── v2_entities_normalized.csv        # V2 with normalized formatting
│   ├── phase4_entities_normalized.csv    # Phase 4 normalized
│   └── combined_dataset.csv              # Merged for comparison
│
├── ground_truth/                          # Validation data
│   ├── training_set_overlap.csv          # Papers in both 2022 & training
│   ├── manual_annotations_sample.csv     # 100 manually annotated papers
│   └── annotation_guidelines.md          # How entities were annotated
│
├── entity_comparison/                     # Script 2 outputs
│   ├── entity_comparison_stats.csv       # Aggregate statistics
│   ├── agreement_cases.csv               # Entities extracted by both
│   ├── v2_only_entities.csv              # V2 found, Phase 4 missed
│   ├── phase4_only_entities.csv          # Phase 4 found, V2 missed
│   └── overlap_analysis.md               # Detailed analysis
│
├── confidence_analysis/                   # Script 3 outputs
│   ├── confidence_histograms.png         # Distribution plots
│   ├── confidence_by_accuracy.csv        # Calibration data
│   ├── calibration_plot.png              # Visual calibration curve
│   └── confidence_summary.md             # Interpretation
│
├── error_analysis/                        # Script 4 outputs
│   ├── error_patterns_v2.csv             # V2 error categorization
│   ├── error_patterns_phase4.csv         # Phase 4 error categorization
│   ├── error_examples_v2.txt             # Top 20 V2 errors with context
│   ├── error_examples_phase4.txt         # Top 20 Phase 4 errors
│   └── error_comparison_report.md        # Side-by-side comparison
│
├── bpe_artifacts/                         # Script 5 outputs
│   ├── bpe_artifacts_report.csv          # Quantified artifact types
│   ├── bpe_artifacts_examples.txt        # Concrete examples
│   ├── bpe_cleaning_effectiveness.md     # Post-processing validation
│   └── before_after_comparison.csv       # Raw vs cleaned samples
│
├── ground_truth_validation/               # Script 6 outputs
│   ├── ground_truth_metrics.csv          # P/R/F1 for both models
│   ├── statistical_tests.txt             # Significance testing results
│   ├── per_paper_scores.csv              # Detailed per-paper breakdown
│   ├── confusion_matrices.png            # V2 and Phase 4 confusion matrices
│   └── metrics_comparison.md             # Interpretation and analysis
│
├── extra_predictions/                     # Script 7 outputs
│   ├── extra_predictions_sample.csv      # 100 random samples
│   ├── manual_review_spreadsheet.csv     # TP/FP labels from human review
│   ├── extra_predictions_analysis.md     # Pattern analysis
│   └── false_positive_rate_estimate.txt  # FP rate extrapolation
│
├── visualizations/                        # Charts and plots
│   ├── entity_count_comparison.png       # V2 vs Phase 4 entities per paper
│   ├── f1_score_comparison.png           # Bar chart: V2 vs Phase 4 F1
│   ├── venn_diagram_entities.png         # Overlap visualization
│   ├── error_type_distribution.png       # Error patterns comparison
│   └── confidence_distributions.png      # Confidence score histograms
│
├── scripts/                               # Analysis scripts (1-8)
│   ├── postprocess_phase4_ner.py
│   ├── compare_entity_extraction.py
│   ├── analyze_confidence_scores.py
│   ├── analyze_error_patterns.py
│   ├── detect_bpe_artifacts.py
│   ├── validate_against_ground_truth.py
│   ├── investigate_phase4_extra_predictions.py
│   └── generate_comparison_report.py
│
└── final_report/                          # Script 8 deliverable
    ├── COMPARISON_REPORT.md              # Comprehensive findings
    ├── EXECUTIVE_SUMMARY.pdf             # One-page summary
    ├── PRODUCTION_RECOMMENDATIONS.md     # Deployment decision
    └── SUPPLEMENTARY_MATERIALS.zip       # All data and code
```

**Total Estimated Size**: ~500 MB
- Raw data: 50 MB
- Processed data: 100 MB
- Visualizations: 10 MB
- Ground truth: 5 MB
- Reports: 5 MB
- Scripts: 1 MB

---

## Technical Details

### Entity Matching Strategies

#### 1. Exact Match (Case-Insensitive)

```python
def exact_match(entity1, entity2):
    """Strict equality after normalization"""
    return entity1.lower().strip() == entity2.lower().strip()

# Example:
# "PDB" == "pdb" → True
# "GenBank" == "Genbank" → True
# "PRIDE" == "pride database" → False
```

#### 2. Substring Match

```python
def substring_match(entity1, entity2):
    """One entity contains the other"""
    e1, e2 = entity1.lower(), entity2.lower()
    return e1 in e2 or e2 in e1

# Example:
# "Protein Data Bank" contains "PDB" → False (token match needed)
# "Protein Data Bank" contains "Protein Data" → True
# Useful for partial entity extraction
```

#### 3. Token Overlap

```python
def token_overlap(entity1, entity2, threshold=0.8):
    """Jaccard similarity of word tokens"""
    tokens1 = set(entity1.lower().split())
    tokens2 = set(entity2.lower().split())

    overlap = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    jaccard = overlap / union if union > 0 else 0
    return jaccard >= threshold

# Example:
# "Protein Data Bank" vs "Data Bank of Proteins"
# Tokens: {protein, data, bank} vs {data, bank, of, proteins}
# Overlap: {data, bank} = 2
# Union: 5
# Jaccard: 2/5 = 0.4 → False (below threshold)
```

#### 4. Fuzzy Match (Edit Distance)

```python
from Levenshtein import ratio

def fuzzy_match(entity1, entity2, threshold=0.85):
    """Levenshtein distance similarity"""
    similarity = ratio(entity1.lower(), entity2.lower())
    return similarity >= threshold

# Example:
# "GenBank" vs "Genbank" → 0.933 → True
# "PRIDE" vs "PRIDEDB" → 0.833 → False (below threshold)
# Handles typos and minor variations
```

#### 5. Acronym Expansion

```python
def acronym_match(acronym, full_name):
    """Check if acronym matches full name"""
    # Extract first letters of each word
    words = full_name.split()
    acronym_candidate = ''.join(w[0] for w in words).upper()

    return acronym.upper() == acronym_candidate

# Example:
# "PDB" matches "Protein Data Bank" → True
# "GEO" matches "Gene Expression Omnibus" → True
# "NCBI" matches "National Center Biotechnology Information" → False (word missing)
```

### BPE Cleaning Algorithm

**Step-by-Step BPE Detokenization**:

```python
def clean_bpe_entity(bpe_str):
    """
    Convert BPE tokenized entity to clean string

    Input:  "ĠPro, te, omics, ĠIdent, ifications, ĠDatabase"
    Output: "Proteomics Identifications Database"
    """

    # Step 1: Split on comma
    tokens = bpe_str.split(', ')
    # ['ĠPro', 'te', 'omics', 'ĠIdent', 'ifications', 'ĠDatabase']

    # Step 2: Process each token
    result = []
    for token in tokens:
        if token.startswith('Ġ'):
            # 'Ġ' indicates space before token
            # Remove prefix and add space
            result.append(' ' + token[1:])
        else:
            # No space, concatenate directly
            result.append(token)

    # Step 3: Join and clean
    entity = ''.join(result).strip()
    # " Pro" + "te" + "omics" + " Ident" + "ifications" + " Database"
    # → "Proteomics Identifications Database"

    # Step 4: Normalize whitespace
    entity = ' '.join(entity.split())
    # Remove duplicate spaces

    # Step 5: Final validation
    if 'Ġ' in entity:
        warnings.warn(f"BPE artifact remaining in: {entity}")

    return entity
```

**Edge Cases**:

1. **Repeated Tokens**:
   ```python
   Input:  "Inter, Pro, ĠInter, Pro"
   Output: "InterPro InterPro"
   Action: Deduplicate → "InterPro"
   ```

2. **Orphaned 'Ġ' Prefix**:
   ```python
   Input:  "Ġdatabase"
   Output: " database"
   Action: Strip leading whitespace → "database"
   ```

3. **Special Characters**:
   ```python
   Input:  "ĠP, DB, Ġ(, database, Ġ)"
   Output: "PDB (database )"
   Action: Clean spacing around punctuation → "PDB (database)"
   ```

4. **Empty Tokens**:
   ```python
   Input:  "ĠPro, , te, omics"
   Output: "Pro te omics"
   Action: Filter empty strings before joining
   ```

**Validation Checks**:

```python
def validate_bpe_cleaning(original, cleaned):
    """Ensure BPE cleaning was successful"""
    checks = []

    # 1. No 'Ġ' should remain
    if 'Ġ' in cleaned:
        checks.append(('FAIL', 'BPE prefix remaining'))
    else:
        checks.append(('PASS', 'No BPE artifacts'))

    # 2. Should be readable (no excessive punctuation)
    punct_ratio = sum(c in '.,;:' for c in cleaned) / len(cleaned)
    if punct_ratio > 0.2:
        checks.append(('WARN', 'High punctuation ratio'))
    else:
        checks.append(('PASS', 'Readable text'))

    # 3. Length should be reasonable
    if len(cleaned) < 2:
        checks.append(('WARN', 'Very short entity'))
    elif len(cleaned) > 100:
        checks.append(('WARN', 'Very long entity'))
    else:
        checks.append(('PASS', 'Reasonable length'))

    return checks
```

### Statistical Testing Methodology

**Paired T-Test** (for normally distributed metrics):

```python
from scipy.stats import ttest_rel, shapiro

# Step 1: Compute per-paper F1 scores
v2_f1_per_paper = []
phase4_f1_per_paper = []

for paper_id in common_papers:
    v2_entities = get_entities(v2_df, paper_id)
    phase4_entities = get_entities(phase4_df, paper_id)
    ground_truth = get_ground_truth(paper_id)

    v2_f1 = compute_f1(v2_entities, ground_truth)
    phase4_f1 = compute_f1(phase4_entities, ground_truth)

    v2_f1_per_paper.append(v2_f1)
    phase4_f1_per_paper.append(phase4_f1)

# Step 2: Test for normality (Shapiro-Wilk test)
stat_v2, p_v2 = shapiro(v2_f1_per_paper)
stat_p4, p_p4 = shapiro(phase4_f1_per_paper)

if p_v2 > 0.05 and p_p4 > 0.05:
    # Data is normally distributed
    print("Using paired t-test")

    # Step 3: Paired t-test
    t_stat, p_value = ttest_rel(v2_f1_per_paper, phase4_f1_per_paper)

    # Step 4: Interpret
    if p_value < 0.05:
        print(f"Phase 4 improvement is statistically significant (p={p_value:.4f})")
    else:
        print(f"Phase 4 improvement is NOT significant (p={p_value:.4f})")
else:
    # Data is not normally distributed
    print("Data not normal, using Wilcoxon test instead")
```

**Wilcoxon Signed-Rank Test** (non-parametric alternative):

```python
from scipy.stats import wilcoxon

# Use when data is not normally distributed
stat, p_value = wilcoxon(v2_f1_per_paper, phase4_f1_per_paper)

if p_value < 0.05:
    print(f"Phase 4 is significantly better (p={p_value:.4f})")
```

**Effect Size (Cohen's d)**:

```python
import numpy as np

def cohens_d(group1, group2):
    """
    Measure effect size (magnitude of difference)
    Small: 0.2, Medium: 0.5, Large: 0.8
    """
    mean_diff = np.mean(group1) - np.mean(group2)
    pooled_std = np.sqrt((np.std(group1)**2 + np.std(group2)**2) / 2)
    return mean_diff / pooled_std

effect = cohens_d(phase4_f1_per_paper, v2_f1_per_paper)
print(f"Effect size: {effect:.3f}")

if abs(effect) < 0.2:
    print("Small effect")
elif abs(effect) < 0.5:
    print("Medium effect")
else:
    print("Large effect")
```

**Confidence Intervals**:

```python
from scipy.stats import sem, t

def mean_confidence_interval(data, confidence=0.95):
    """95% confidence interval for mean"""
    n = len(data)
    mean = np.mean(data)
    std_err = sem(data)
    h = std_err * t.ppf((1 + confidence) / 2, n - 1)
    return mean, mean - h, mean + h

# V2 F1 confidence interval
v2_mean, v2_lower, v2_upper = mean_confidence_interval(v2_f1_per_paper)
print(f"V2 F1: {v2_mean:.3f} [{v2_lower:.3f}, {v2_upper:.3f}]")

# Phase 4 F1 confidence interval
p4_mean, p4_lower, p4_upper = mean_confidence_interval(phase4_f1_per_paper)
print(f"Phase 4 F1: {p4_mean:.3f} [{p4_lower:.3f}, {p4_upper:.3f}]")

# Check if confidence intervals overlap
if p4_lower > v2_upper:
    print("✅ Phase 4 is significantly better (no CI overlap)")
elif v2_lower > p4_upper:
    print("❌ V2 is significantly better (no CI overlap)")
else:
    print("⚠️  Confidence intervals overlap (inconclusive)")
```

### Evaluation Metrics

**Precision, Recall, F1**:

```python
def compute_metrics(true_entities, pred_entities):
    """
    Compute standard NER evaluation metrics
    """
    # True Positives: predicted AND in ground truth
    tp = len(set(pred_entities) & set(true_entities))

    # False Positives: predicted but NOT in ground truth
    fp = len(set(pred_entities) - set(true_entities))

    # False Negatives: in ground truth but NOT predicted
    fn = len(set(true_entities) - set(pred_entities))

    # Precision: what % of predictions are correct?
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0

    # Recall: what % of true entities were found?
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    # F1: harmonic mean of precision and recall
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'tp': tp,
        'fp': fp,
        'fn': fn
    }
```

**Entity-Level vs Token-Level**:

```python
# Entity-level (strict)
# "Protein Data Bank" must be fully extracted
true_entities = ["Protein Data Bank", "GenBank"]
pred_entities = ["Protein Data", "GenBank", "NCBI"]

entity_metrics = compute_metrics(true_entities, pred_entities)
# TP: 1 (GenBank)
# FP: 2 (Protein Data - partial, NCBI - hallucination)
# FN: 1 (Protein Data Bank - not fully captured)
# Precision: 1/3 = 0.333
# Recall: 1/2 = 0.500
# F1: 0.400
```

```python
# Token-level (lenient)
# Each token evaluated independently
true_labels = [O, B, I, I, O, B, O]  # "Protein Data Bank" + "GenBank"
pred_labels = [O, B, I, O, O, B, B]  # "Protein Data" + "GenBank" + "NCBI"

token_accuracy = (true_labels == pred_labels).mean()
# 4/7 = 0.571 (higher than entity-level F1)
```

**Interpretation**:
- Token-level metrics are typically **higher** than entity-level
- Phase 4's +23.82% improvement is measured token-level
- This study will compute **both** for fair comparison

---

## Timeline & Milestones

### Phase 1: Data Preparation (Days 1-2)

**Day 1**: Setup and data loading
- ✅ Identify V2 and Phase 4 NER result locations
- ✅ Document format differences
- Create comparison directory structure
- Copy raw data files

**Day 2**: Post-processing Phase 4 output
- Implement BPE detokenization (Script 1)
- Validate cleaning effectiveness
- Generate cleaned Phase 4 dataset
- **Deliverable**: `phase4_ner_cleaned.csv`

### Phase 2: Entity Comparison (Days 3-4)

**Day 3**: Entity-level comparison
- Implement entity matching logic (Script 2)
- Compute agreement, V2-only, Phase4-only statistics
- Generate overlap visualizations
- **Deliverable**: Entity comparison statistics and Venn diagrams

**Day 4**: Confidence analysis
- Analyze confidence score distributions (Script 3)
- Compute calibration metrics
- Generate confidence plots
- **Deliverable**: Confidence analysis report

### Phase 3: Error Analysis (Days 5-7)

**Day 5**: Error pattern detection
- Categorize errors for both models (Script 4)
- Collect error examples with context
- Compare error types
- **Deliverable**: Error pattern analysis

**Day 6**: BPE artifact investigation
- Quantify BPE tokenization issues (Script 5)
- Validate post-processing effectiveness
- Document remaining artifacts
- **Deliverable**: BPE artifacts report

**Day 7**: Ground truth validation (if available)
- Load ground truth annotations (Script 6)
- Compute precision, recall, F1 for both models
- Perform statistical significance testing
- **Deliverable**: Ground truth metrics and p-values

### Phase 4: Deep Dive Analysis (Days 8-9)

**Day 8**: Extra predictions investigation
- Sample 100 Phase 4-only predictions (Script 7)
- Manual review and labeling
- Estimate false positive rate
- **Deliverable**: False positive analysis

**Day 9**: Manual annotation (if needed)
- Select random 100 papers from 2022 dataset
- Manually annotate entities
- Use for ground truth validation
- **Deliverable**: Manual annotations dataset

### Phase 5: Reporting (Days 10-11)

**Day 10**: Final report generation
- Synthesize all findings (Script 8)
- Generate visualizations
- Write executive summary
- **Deliverable**: Draft comparison report

**Day 11**: Review and finalization
- Review all results
- Validate conclusions
- Finalize recommendations
- **Deliverable**: Final comparison report

**Total Duration**: 11 days (2-3 weeks with interruptions)

---

## Success Criteria

### Quantitative Criteria

**Primary Metrics**:
- [ ] **F1 Score Comparison**: Phase 4 F1 ≥ V2 F1 + 0.05 (5% improvement)
- [ ] **Statistical Significance**: p-value < 0.05 (95% confidence)
- [ ] **False Positive Rate**: Phase 4 FP rate < 10%
- [ ] **BPE Cleaning**: >99% of entities properly detokenized

**Secondary Metrics**:
- [ ] **Precision**: Phase 4 precision ≥ V2 precision - 0.03 (acceptable trade-off)
- [ ] **Recall**: Phase 4 recall > V2 recall (improvement expected)
- [ ] **Agreement Rate**: >80% agreement on shared predictions
- [ ] **Effect Size**: Cohen's d ≥ 0.5 (medium effect)

### Qualitative Criteria

**Entity Quality**:
- [ ] Phase 4 entities are readable and properly formatted
- [ ] No systematic tokenization errors in cleaned output
- [ ] Entity boundaries are accurate (not truncated or extended)
- [ ] Special characters and punctuation handled correctly

**Error Analysis**:
- [ ] Error patterns are well-documented for both models
- [ ] Phase 4 does not introduce new error types
- [ ] BPE artifacts are rare (<1% of entities)
- [ ] False positives are identifiable and explainable

**Documentation**:
- [ ] All scripts are well-commented and reproducible
- [ ] Results are clearly visualized with charts and tables
- [ ] Comparison report is comprehensive and actionable
- [ ] Recommendations are clear and evidence-based

### Deployment Decision Criteria

**RECOMMEND DEPLOYMENT** if:
1. ✅ Phase 4 F1 > V2 F1 + 0.05 (5% improvement)
2. ✅ Improvement is statistically significant (p < 0.05)
3. ✅ False positive rate < 10%
4. ✅ BPE cleaning is effective (>99% success)
5. ✅ No critical new error types introduced
6. ✅ Manual review confirms quality improvement

**CONDITIONAL DEPLOYMENT** if:
1. ⚠️ Phase 4 F1 > V2 F1 (improvement exists but <5%)
2. ⚠️ False positive rate 10-20% (acceptable with monitoring)
3. ⚠️ Some BPE artifacts remain but <2%
4. ⚠️ Requires additional post-processing pipeline

**DO NOT DEPLOY** if:
1. ❌ Phase 4 F1 ≤ V2 F1 (no improvement or regression)
2. ❌ False positive rate > 20%
3. ❌ BPE cleaning fails >1% of the time
4. ❌ Critical new error patterns emerge
5. ❌ Manual review shows quality degradation

---

## References

### Source Documentation

**Comparison Analysis**:
- `V2_VS_PHASE4_NER_OUTPUT_COMPARISON.md` - Raw output format differences
- `docs/NER_SYSTEM_COMPARISON.md` - Comprehensive technical comparison
- `compare_ner_v2_vs_phase4.py` - Existing comparison script

**Model Documentation**:
- `docs/NER_explanation.md` - NER task explanation
- `docs/multi_task_model/PHASE4_IMPLEMENTATION_SUMMARY.md` - Phase 4 details
- `docs/starting_doc.md` - Project overview

**Training Results**:
- V2: `trained_models_25/2025-10-21_full_production_training/training_stats_ner.csv`
- Phase 4: `collab_results/experiment_archives/2025-10-31-rq7i4n/multitask_training/training_history.json`

### Data Sources

**V2 Results**:
- Path: `collab_results/2025-10-27-7mvru2_oldmodel_2022_rerun/ner_results.csv`
- Format: Clean entities (7 columns)
- Size: 4,395 papers

**Phase 4 Results**:
- Path: `collab_results/experiment_archives/2025-11-05-1f3ixn_phase4_2022_rerun/ner_results.csv`
- Format: Raw BPE tokens (5 columns)
- Size: 20,890 predictions

**Ground Truth**:
- Training: `data/ner_splits_full/train_ner.csv` (307 samples)
- Validation: `data/ner_splits_full/val_ner.csv` (67 samples)
- Test: `data/ner_splits_full/test_ner.csv` (67 samples)

### Related Scripts

**Existing Code**:
- `compare_ner_v2_vs_phase4.py` - Initial comparison attempt
- `src/ner_predict.py` - V2 inference with `reformat_output()`
- `src/multitask_predict.py` - Phase 4 inference (raw tokens)

**Pipeline Notebooks**:
- `rerun_2022_inventory_simplified.ipynb` - V2 full pipeline
- `phase4_full_inference_2022_FIXED.ipynb` - Phase 4 full pipeline

### External Resources

**Libraries**:
- `seqeval` - Entity-level NER evaluation
- `sklearn.metrics` - Token-level metrics
- `Levenshtein` - Fuzzy string matching
- `scipy.stats` - Statistical testing

**Documentation**:
- HuggingFace Transformers: https://huggingface.co/docs/transformers
- seqeval: https://github.com/chakki-works/seqeval
- BPE tokenization: https://huggingface.co/docs/transformers/tokenizer_summary

---

## Appendices

### Appendix A: BPE Tokenization Examples

**Common BPE Patterns**:

| Original Entity | BPE Tokenized Output | Cleaned Output | Notes |
|----------------|----------------------|----------------|-------|
| InterPro | "Inter, Pro" | "InterPro" | Simple split |
| PubMed | "Pub, Med" | "PubMed" | Compound word |
| Protein Data Bank | "ĠPro, tein, ĠData, ĠBank" | "Protein Data Bank" | Multi-word |
| GEO | "ĠG, EO" | "GEO" | Acronym split |
| UniProt | "Uni, Prot, ĠUni, Prot" | "UniProt UniProt" | Duplicate (needs dedup) |
| mESAdb | "Ġm, ES, A, db" | "mESAdb" | Mixed case |
| dbSNP | "db, SN, P" | "dbSNP" | Lowercase prefix |

### Appendix B: Evaluation Methodology Comparison

**V2 Training Evaluation** (entity-level):
```python
from evaluate import load
calc_seq_metrics = load('seqeval')

# Entity-level evaluation
metrics = calc_seq_metrics.compute(
    predictions=all_predictions,  # BIO tags as strings
    references=all_labels
)
# Returns: precision, recall, f1 (entity-level)
```

**Phase 4 Training Evaluation** (token-level):
```python
from sklearn.metrics import f1_score

# Token-level evaluation
ner_f1 = f1_score(
    all_labels,       # Flattened token labels
    all_predictions,  # Flattened token predictions
    average='macro'   # Average across classes
)
```

**This Study's Evaluation** (both methods):
```python
# Method 1: Entity-level (strict, matches V2 training)
entity_f1 = entity_level_f1(true_entities, pred_entities)

# Method 2: Token-level (lenient, matches Phase 4 training)
token_f1 = token_level_f1(true_labels, pred_labels)

# Report both for transparency
```

### Appendix C: Manual Annotation Guidelines

**Entity Annotation Rules**:

1. **Database/Tool Names**: Include if mentioned as a resource
   - ✅ "PubMed", "GenBank", "BLAST"
   - ❌ "the", "database", "tool" (generic terms)

2. **Abbreviations and Full Names**: Label both separately
   - ✅ "PDB" (common name)
   - ✅ "Protein Data Bank" (full name)

3. **Compound Names**: Include hyphens and special characters
   - ✅ "dbSNP", "miRBase", "Ensembl-like"

4. **Ambiguous Cases**: Use judgment
   - ⚠️ "our database" → Include if it has a name
   - ⚠️ "new resource" → Include if specific name provided

5. **Context**: Entity must be clearly a database/tool/resource
   - ✅ "GEO contains expression data" (GEO is a database)
   - ❌ "geo-location data" (geo is not a database)

**Annotation Format**:
```csv
ID,title,abstract,annotated_entities,notes
21063943,"PRIDE database...","...","PRIDE, Proteomics Identifications Database","Clear database"
```

---

**Document Version**: 1.0
**Created**: 2025-11-05
**Last Updated**: 2025-11-05
**Author**: Research Agent
**Status**: Planning Complete - Ready for Implementation
**Next Steps**: Execute Scripts 1-8 sequentially
