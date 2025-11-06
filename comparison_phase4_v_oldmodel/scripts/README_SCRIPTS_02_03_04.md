# Scripts 02-04: Evaluation and Analysis Suite

This document provides comprehensive documentation for Scripts 02-04 of the Phase 4 vs V2 NER comparison project.

## Overview

The evaluation suite consists of three complementary scripts that analyze NER system performance from different angles:

| Script | Purpose | Key Outputs |
|--------|---------|-------------|
| **02_evaluate_on_test_split.py** | Evaluate on 67 papers with ground truth | F1 metrics, statistical tests, examples |
| **03_evaluate_on_inventory.py** | Evaluate on 3,113 validated resources | Detection rates, novel discoveries |
| **04_analyze_bpe_artifacts.py** | Analyze BPE contamination impact | Contamination report, visualizations |

## Prerequisites

### Required Files (from Script 01)
```bash
# Must exist before running Scripts 02-04
results/aligned_papers.csv              # Main aligned dataset
results/bpe_artifact_report.json        # BPE contamination data (for Script 04)
```

### Python Dependencies
```bash
# Core dependencies
pandas>=1.5.0
numpy>=1.23.0
scipy>=1.9.0              # For McNemar's test
matplotlib>=3.6.0         # For visualizations
seaborn>=0.12.0          # For enhanced plots
tqdm>=4.64.0             # For progress bars

# Install all dependencies
pip install pandas numpy scipy matplotlib seaborn tqdm
```

---

## Script 02: Evaluate on Test Split

### Purpose
Evaluates both V2 and Phase 4 NER systems on papers with manually annotated ground truth. This provides rigorous performance metrics using the gold standard.

### What It Does

1. **Loads aligned papers** from Script 01 output
2. **Filters to test split** (papers with ground truth annotations)
3. **Evaluates each system**:
   - V2 predictions vs ground truth
   - Phase 4 raw predictions vs ground truth
   - Phase 4 cleaned predictions vs ground truth
4. **Calculates metrics**:
   - Precision: What % of predictions are correct?
   - Recall: What % of true entities were found?
   - F1-score: Harmonic mean of P&R
5. **Statistical testing**:
   - McNemar's test for significance
   - Bootstrap confidence intervals
6. **Generates examples**:
   - Cases where Phase 4 wins
   - Cases where V2 wins
   - Cases where both succeed/fail

### Usage

#### Basic Usage
```bash
# Standard evaluation with exact matching
python 02_evaluate_on_test_split.py
```

#### Advanced Options
```bash
# Use fuzzy matching (tolerates minor typos)
python 02_evaluate_on_test_split.py --match-strategy fuzzy

# Custom input/output paths
python 02_evaluate_on_test_split.py \
    --input custom_aligned.csv \
    --output custom_results/

# Generate more examples
python 02_evaluate_on_test_split.py --n-examples 20

# Verbose logging
python 02_evaluate_on_test_split.py --verbose
```

#### All Options
```
--input PATH              Path to aligned papers CSV
                         (default: results/aligned_papers.csv)

--output PATH            Output directory for results
                         (default: results/)

--match-strategy STRATEGY  Entity matching strategy
                         Options: exact, fuzzy, partial, token_overlap
                         (default: exact)

--n-examples N           Number of detailed examples to generate
                         (default: 10)

--verbose                Enable verbose logging
```

### Outputs

#### 1. test_split_metrics.csv
Per-paper metrics for all three systems.

**Columns:**
```
paper_id                    PubMed ID
title                       Paper title
v2_precision                V2 precision
v2_recall                   V2 recall
v2_f1                       V2 F1 score
v2_tp, v2_fp, v2_fn        V2 confusion matrix
v2_total_predicted          V2 total entities predicted
v2_total_true              V2 total ground truth entities
[Same metrics for phase4_raw and phase4_cleaned]
```

#### 2. test_split_aggregate.json
Overall metrics with confidence intervals.

**Structure:**
```json
{
  "v2": {
    "micro": {
      "precision": 0.8234,
      "recall": 0.7891,
      "f1": 0.8059,
      "tp": 1234,
      "fp": 267,
      "fn": 329
    },
    "macro": {
      "precision": 0.8156,
      "recall": 0.7823,
      "f1": 0.7986,
      "f1_std": 0.1234
    },
    "ci": {
      "mean": 0.7986,
      "lower": 0.7612,
      "upper": 0.8341,
      "confidence": 0.95
    }
  },
  "phase4_raw": { ... },
  "phase4_cleaned": { ... }
}
```

#### 3. test_split_examples.txt
Detailed examples showing predictions vs ground truth.

**Categories:**
- Phase 4 significantly outperforms V2 (top 3)
- V2 significantly outperforms Phase 4 (top 3)
- Both systems perform well (2 examples)
- Both systems struggle (2 examples)

**Example format:**
```
═══════════════════════════════════════════════════════════════
CATEGORY 1: Phase 4 Cleaned Significantly Outperforms V2 (Top 3)
═══════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────
Example 1: Phase 4 F1=0.923 vs V2 F1=0.654 (Δ=0.269)
────────────────────────────────────────────────────────────────
Paper ID: 12345678
Title: Analysis of novel protein biomarkers...

Ground Truth (15 entities):
  - protein A
  - gene B
  - compound C
  ...

V2 Predictions (12 entities):
  ✓ protein A
  ✗ protein X
  ✓ gene B
  ...

Phase 4 Cleaned Predictions (18 entities):
  ✓ protein A
  ✓ gene B
  ✓ compound C
  ...
```

#### 4. test_split_comparison.md
Markdown summary report with tables and analysis.

**Sections:**
- Overview
- Aggregate metrics (tables)
- Statistical significance (McNemar's test, bootstrap CI)
- Per-paper performance distribution

#### 5. test_split_significance.json
Statistical test results.

**Structure:**
```json
{
  "Phase 4 Cleaned vs V2": {
    "system1": "phase4_cleaned",
    "system2": "v2",
    "mcnemar": {
      "statistic": 12.34,
      "p_value": 0.0004,
      "significant": true,
      "both_correct": 45,
      "both_incorrect": 8,
      "system1_only": 12,
      "system2_only": 2
    },
    "f1_difference": {
      "mean": 0.0456,
      "lower": 0.0234,
      "upper": 0.0678,
      "confidence": 0.95
    }
  }
}
```

### Key Metrics Explained

#### Precision
```
Precision = TP / (TP + FP)
```
- **TP (True Positives)**: Entities correctly predicted
- **FP (False Positives)**: Entities predicted but not in ground truth

**Interpretation**: "Of all entities the system predicted, what % were actually correct?"
- High precision = Few false alarms
- Low precision = Predicting many incorrect entities

#### Recall
```
Recall = TP / (TP + FN)
```
- **TP (True Positives)**: Entities correctly predicted
- **FN (False Negatives)**: Entities in ground truth but missed

**Interpretation**: "Of all true entities, what % did the system find?"
- High recall = Finding most entities
- Low recall = Missing many entities

#### F1 Score
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```
**Interpretation**: Harmonic mean balancing precision and recall
- F1 = 1.0: Perfect (100% precision and recall)
- F1 = 0.0: Worst (0% precision or recall)
- F1 > 0.8: Excellent
- F1 > 0.6: Good
- F1 > 0.4: Fair
- F1 < 0.4: Poor

#### McNemar's Test
Statistical test for comparing paired binary outcomes (correct/incorrect).

**Hypotheses:**
- H₀: Systems perform equally well
- H₁: Systems perform differently

**Interpretation:**
- p-value < 0.05: Statistically significant difference
- p-value ≥ 0.05: No significant difference

**Contingency table:**
```
                System 2 Correct    System 2 Incorrect
System 1 Correct        a                  b
System 1 Incorrect      c                  d
```
- Test uses discordant pairs (b and c)
- If b ≈ c: No difference
- If b >> c: System 1 better
- If c >> b: System 2 better

---

## Script 03: Evaluate on Inventory

### Purpose
Evaluates how well each NER system detects the 3,113 validated bio-resources from the final inventory. This measures real-world detection capabilities.

### What It Does

1. **Loads aligned papers** and inventory data
2. **For each validated resource**:
   - Checks if V2 detected it (exact/fuzzy/partial match)
   - Checks if Phase 4 detected it
   - Scores as: Correct, Partial, Miss
3. **Identifies novel discoveries**:
   - Entities predicted by systems but NOT in inventory
   - Potential new bio-resources
4. **Analyzes by characteristics**:
   - Entity length (short, medium, long)
   - Publication year
5. **Finds resources missed by both** systems

### Usage

#### Basic Usage
```bash
# Standard evaluation
python 03_evaluate_on_inventory.py
```

#### Advanced Options
```bash
# Custom inventory file
python 03_evaluate_on_inventory.py \
    --inventory data/custom_inventory.csv

# Custom input/output paths
python 03_evaluate_on_inventory.py \
    --input custom_aligned.csv \
    --output custom_results/

# Verbose logging
python 03_evaluate_on_inventory.py --verbose
```

#### All Options
```
--input PATH         Path to aligned papers CSV
                    (default: results/aligned_papers.csv)

--inventory PATH    Path to inventory CSV
                    (default: auto-detect from multiple locations)

--output PATH       Output directory for results
                    (default: results/)

--verbose           Enable verbose logging
```

### Outputs

#### 1. inventory_evaluation.csv
Per-resource evaluation results.

**Columns:**
```
pmid                    PubMed ID
best_name              Primary resource name
best_common            Common name variant
best_full              Full name variant
system                 System name (V2 or Phase4_Cleaned)
result                 Result category (correct/partial/miss)
matched_entity         Entity that matched (if any)
match_strategy         Strategy used (exact/fuzzy/partial/token_overlap)
num_predicted_entities Number of entities predicted for this paper
```

#### 2. inventory_metrics.json
Detection rates and precision metrics.

**Structure:**
```json
{
  "V2": {
    "system": "V2",
    "total_resources": 3113,
    "correct_matches": 2145,
    "partial_matches": 456,
    "misses": 512,
    "detection_rate": 0.8356,
    "correct_detection_rate": 0.6889,
    "precision_on_detections": 0.8247
  },
  "Phase4_Cleaned": { ... }
}
```

#### 3. missed_resources.csv
Resources that neither system detected.

**Columns:**
```
pmid          PubMed ID
best_name     Primary resource name
best_common   Common name variant
best_full     Full name variant
```

**Use cases:**
- Identify challenging entities
- Prioritize for model improvement
- Manual review for annotation errors

#### 4. novel_discoveries.csv
Entities predicted but not in inventory.

**Columns:**
```
entity        Entity text
occurrences   Number of times found
system        System that found it (V2 or Phase4_Cleaned)
```

**Use cases:**
- Discover potential new bio-resources
- Validate against external databases
- Expand inventory coverage

#### 5. inventory_comparison.md
Markdown summary report.

**Sections:**
- Overview
- Detection metrics (table)
- Match quality breakdown
- Missed resources (with examples)
- Novel discoveries (top entities)
- Analysis by characteristics (length, year)

#### 6. inventory_by_length.csv (optional)
Performance breakdown by entity length.

**Columns:**
```
system           System name
length_bin       Length category (Short/Medium/Long/Very Long)
total           Total resources in this category
correct         Correctly detected
detection_rate  Fraction detected
```

#### 7. inventory_by_year.csv (optional)
Performance breakdown by publication year.

**Columns:**
```
system           System name
year_bin        Year range (Before 2010/2010-2014/2015-2019/2020+)
total           Total resources in this category
correct         Correctly detected
detection_rate  Fraction detected
```

### Match Scoring

#### Correct Match
Resource is detected using **exact** or **fuzzy** matching:
- Exact: Case-insensitive string match
- Fuzzy: Levenshtein distance ≤ 2

**Examples:**
- "protein kinase A" = "Protein Kinase A" → Correct (exact)
- "IL-6" = "IL-6 " → Correct (fuzzy, trailing space)
- "protien" = "protein" → Correct (fuzzy, typo)

#### Partial Match
Resource is detected using **partial** or **token_overlap** matching:
- Partial: One string contains the other (min length 4)
- Token overlap: Jaccard similarity ≥ 0.6

**Examples:**
- "protein" in "protein kinase A" → Partial
- "protein kinase A" vs "kinase A protein" → Partial (token overlap)

#### Miss
Resource is not detected by any matching strategy.

**Common reasons:**
- Entity not extracted by NER model
- Entity extracted with very different wording
- Annotation error in ground truth

---

## Script 04: Analyze BPE Artifacts

### Purpose
Performs deep analysis of BPE (Byte-Pair Encoding) contamination in Phase 4 results. BPE artifacts are tokenizer special characters that leak into the output.

### What BPE Artifacts Look Like

#### Ġ Marker (most common)
The "Ġ" character marks word boundaries in GPT-2 style tokenizers:
```
✗ "Ġprotein"        → Should be "protein"
✗ "ĠIL-6"           → Should be "IL-6"
✗ "Ġmouse Ġmodel"  → Should be "mouse model"
```

#### Subword Fragments
Words split into subword tokens that don't get merged:
```
✗ "pro te in"      → Should be "protein"
✗ "anti bo dy"     → Should be "antibody"
✗ "a mi no"        → Should be "amino"
```

### What It Does

1. **Quantifies contamination**:
   - % of papers affected
   - % of entities affected
   - Distribution across papers
2. **Analyzes patterns**:
   - Most common Ġ marker patterns
   - Subword fragment examples
   - Before/after cleaning examples
3. **Measures impact on F1**:
   - Phase 4 raw vs Phase 4 cleaned
   - Phase 4 vs V2
   - Impact on contaminated vs clean papers
4. **Creates visualizations**:
   - Contamination histogram
   - F1 comparison plots
5. **Generates detailed report**

### Usage

#### Basic Usage
```bash
# Standard analysis
python 04_analyze_bpe_artifacts.py
```

#### Advanced Options
```bash
# Custom paths
python 04_analyze_bpe_artifacts.py \
    --input custom_aligned.csv \
    --output custom_results/ \
    --figures custom_figures/

# Verbose logging
python 04_analyze_bpe_artifacts.py --verbose
```

#### All Options
```
--input PATH      Path to aligned papers CSV
                 (default: results/aligned_papers.csv)

--output PATH    Output directory for results
                 (default: results/)

--figures PATH   Output directory for figures
                 (default: figures/)

--verbose        Enable verbose logging
```

### Outputs

#### 1. bpe_contamination_report.md
Comprehensive markdown report.

**Sections:**
- Executive summary
- Contamination levels (overall statistics)
- Severity assessment (color-coded)
- Artifact patterns (common types)
- Top Ġ marker patterns (table)
- Example artifacts (before → after)
- Impact on F1 scores (tables)
- Worst affected papers
- Conclusions and recommendations

**Example snippet:**
```markdown
## Contamination Levels

### Overall Statistics

- **Total papers with entities**: 20,890
- **Papers with contamination**: 18,234 (87.3%)
- **Total entities extracted**: 156,789
- **Contaminated entities**: 89,234 (56.9%)

### Severity Assessment

**🔴 CRITICAL**: Over 50% of entities are contaminated

## Artifact Patterns

### Top 10 Most Common Ġ Marker Patterns

| Pattern | Occurrences |
|---------|-------------|
| `Ġmouse` | 12,345 |
| `Ġprotein` | 8,901 |
| `ĠIL-6` | 5,678 |
```

#### 2. bpe_impact_on_metrics.csv
Per-paper F1 comparison.

**Columns:**
```
paper_id                PubMed ID
title                   Paper title
v2_f1                   V2 F1 score
phase4_raw_f1          Phase 4 raw F1 score
phase4_clean_f1        Phase 4 cleaned F1 score
has_contamination      Boolean: contamination detected
contaminated_entities  Number of contaminated entities
total_entities         Total entities in paper
contamination_rate     Fraction contaminated
f1_improvement         Clean F1 - Raw F1
raw_vs_v2             Raw F1 - V2 F1
clean_vs_v2           Clean F1 - V2 F1
```

**Use cases:**
- Identify papers most affected by contamination
- Measure cleaning effectiveness
- Correlate contamination with F1 degradation

#### 3. bpe_artifact_patterns.json
Detailed pattern analysis.

**Structure:**
```json
{
  "g_marker_count": 89234,
  "short_tokens_count": 12456,
  "top_g_marker_patterns": [
    {"pattern": "Ġmouse", "count": 12345},
    {"pattern": "Ġprotein", "count": 8901},
    {"pattern": "ĠIL-6", "count": 5678}
  ],
  "example_artifacts": [
    {
      "original": "Ġprotein kinase",
      "cleaned": "protein kinase",
      "paper_id": "12345678"
    }
  ],
  "short_token_examples": [
    {
      "original": "pro te in",
      "cleaned": "protein",
      "paper_id": "87654321"
    }
  ]
}
```

#### 4. bpe_contamination_stats.json
Detailed contamination statistics.

**Structure:**
```json
{
  "total_papers": 20890,
  "papers_with_entities": 20456,
  "papers_with_contamination": 18234,
  "total_entities": 156789,
  "contaminated_entities": 89234,
  "paper_contamination_rate": 0.8913,
  "entity_contamination_rate": 0.5690,
  "contamination_by_paper": [
    {
      "paper_id": "12345678",
      "total_entities": 15,
      "contaminated_entities": 12,
      "contamination_rate": 0.8000
    }
  ]
}
```

#### 5. figures/bpe_contamination_histogram.png
Histogram showing distribution of contamination rates across papers.

**Features:**
- X-axis: Contamination rate (0.0 to 1.0)
- Y-axis: Number of papers
- Includes mean and median annotations
- Shows total papers analyzed

**Interpretation:**
- Uniform distribution: Consistent contamination
- Right-skewed: Most papers heavily contaminated
- Left-skewed: Most papers lightly contaminated
- Bimodal: Two distinct populations

#### 6. figures/bpe_f1_comparison.png
Two-panel figure comparing F1 scores.

**Panel 1: Box plot of F1 scores**
- Three boxes: V2, Phase 4 Raw, Phase 4 Cleaned
- Shows median, quartiles, outliers

**Panel 2: Scatter plot - Raw vs Cleaned F1**
- X-axis: Phase 4 Raw F1
- Y-axis: Phase 4 Cleaned F1
- Diagonal line: No change baseline
- Red points: Contaminated papers
- Green points: Clean papers

**Interpretation:**
- Points above diagonal: Cleaning improved F1
- Points on diagonal: No change
- Red points above diagonal: Contamination hurt performance

---

## Workflow Integration

### Recommended Execution Order

```bash
# Step 1: Preprocess and align (if not done)
python 01_preprocess_and_align.py

# Step 2: Evaluate on test split (ground truth)
python 02_evaluate_on_test_split.py

# Step 3: Evaluate on inventory (real-world detection)
python 03_evaluate_on_inventory.py

# Step 4: Analyze BPE contamination
python 04_analyze_bpe_artifacts.py
```

### Parallel Execution
Scripts 02-04 are independent and can run in parallel after Script 01:

```bash
# Run all three in parallel (requires GNU parallel or similar)
parallel ::: \
    "python 02_evaluate_on_test_split.py" \
    "python 03_evaluate_on_inventory.py" \
    "python 04_analyze_bpe_artifacts.py"
```

---

## Troubleshooting

### Common Issues

#### 1. "Aligned papers file not found"
**Error:**
```
FileNotFoundError: Aligned papers file not found: results/aligned_papers.csv
Please run Script 01 first: 01_preprocess_and_align.py
```

**Solution:**
```bash
# Run Script 01 first to create aligned_papers.csv
python 01_preprocess_and_align.py
```

#### 2. "Inventory file not found"
**Error:**
```
FileNotFoundError: Inventory file not found. Tried locations:
  - data/final_inventory_2022.csv
  - collab_results/.../final_inventory.csv
```

**Solution:**
```bash
# Option 1: Place inventory at expected location
cp your_inventory.csv data/final_inventory_2022.csv

# Option 2: Specify custom path
python 03_evaluate_on_inventory.py --inventory path/to/inventory.csv
```

#### 3. "Module 'scipy' not found" (Script 02)
**Error:**
```
ModuleNotFoundError: No module named 'scipy'
```

**Solution:**
```bash
pip install scipy
```

#### 4. "Module 'matplotlib' not found" (Script 04)
**Error:**
```
ModuleNotFoundError: No module named 'matplotlib'
```

**Solution:**
```bash
pip install matplotlib seaborn
```

#### 5. Empty test split / No ground truth
**Error:**
```
Test split: 0 papers with ground truth
```

**Solution:**
- Check that NER test split is loaded correctly in Script 01
- Verify test_ner.csv contains annotations
- Check column names match expected format

#### 6. Very low F1 scores
**Possible causes:**
- Mismatched entity formats (list vs string)
- Wrong matching strategy
- Incorrect ground truth format

**Debug:**
```bash
# Try different matching strategies
python 02_evaluate_on_test_split.py --match-strategy fuzzy
python 02_evaluate_on_test_split.py --match-strategy partial

# Enable verbose logging to see details
python 02_evaluate_on_test_split.py --verbose
```

---

## Performance Optimization

### For Large Datasets

#### Memory Management
Scripts process data in streaming fashion, but large datasets may still require optimization:

```python
# If running out of memory, process in batches
# Modify script to use chunked processing:
for chunk in pd.read_csv('aligned_papers.csv', chunksize=1000):
    process_chunk(chunk)
```

#### Parallel Processing
Evaluation loops can be parallelized:

```python
# Add multiprocessing to speed up evaluation
from multiprocessing import Pool

def process_paper(row):
    return evaluate_all_systems_on_paper(row)

with Pool(processes=8) as pool:
    results = pool.map(process_paper, df.iterrows())
```

### Execution Time Estimates

| Script | Dataset Size | Estimated Time |
|--------|-------------|----------------|
| Script 02 | 67 papers | 30-60 seconds |
| Script 03 | 20,890 papers | 5-10 minutes |
| Script 04 | 20,890 papers | 3-5 minutes |

---

## Advanced Usage

### Custom Matching Strategies

#### Script 02: Custom Entity Matching
You can implement custom matching logic by modifying the entity matching strategies:

```python
# In utils/entity_matching.py, add custom strategy:
def custom_biomedical_match(entity1: str, entity2: str) -> bool:
    """
    Custom matching for biomedical entities.
    Handles abbreviations, Greek letters, etc.
    """
    # Normalize Greek letters
    entity1 = entity1.replace('α', 'alpha')
    entity2 = entity2.replace('α', 'alpha')

    # Check abbreviation expansion
    if is_abbreviation(entity1, entity2):
        return True

    # Standard fuzzy match
    return fuzzy_match(entity1, entity2)
```

### Custom Analysis

#### Adding New Metrics
To add custom metrics to Script 02:

```python
# In 02_evaluate_on_test_split.py, modify evaluate_all_systems_on_paper():
def evaluate_all_systems_on_paper(paper_row, match_strategy='exact'):
    # ... existing code ...

    # Add custom metric
    results['v2']['custom_metric'] = calculate_custom_metric(
        v2_predicted, true_entities
    )

    return results
```

#### Custom Visualizations
To add custom plots to Script 04:

```python
# In 04_analyze_bpe_artifacts.py, add new function:
def create_custom_plot(data, output_path):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Your custom plotting code
    ax.plot(data['x'], data['y'])
    ax.set_title('Custom Analysis')

    plt.savefig(output_path, dpi=300)
    plt.close()

# Call in main():
create_custom_plot(custom_data, args.figures / 'custom_plot.png')
```

---

## Output File Reference

### Complete Output Structure

```
comparison_phase4_v_oldmodel/
├── results/
│   ├── aligned_papers.csv              [From Script 01]
│   ├── bpe_artifact_report.json        [From Script 01]
│   │
│   ├── test_split_metrics.csv          [Script 02]
│   ├── test_split_aggregate.json       [Script 02]
│   ├── test_split_examples.txt         [Script 02]
│   ├── test_split_comparison.md        [Script 02]
│   ├── test_split_significance.json    [Script 02]
│   │
│   ├── inventory_evaluation.csv        [Script 03]
│   ├── inventory_metrics.json          [Script 03]
│   ├── missed_resources.csv            [Script 03]
│   ├── novel_discoveries.csv           [Script 03]
│   ├── inventory_comparison.md         [Script 03]
│   ├── inventory_by_length.csv         [Script 03]
│   ├── inventory_by_year.csv           [Script 03]
│   │
│   ├── bpe_contamination_report.md     [Script 04]
│   ├── bpe_impact_on_metrics.csv       [Script 04]
│   ├── bpe_artifact_patterns.json      [Script 04]
│   └── bpe_contamination_stats.json    [Script 04]
│
└── figures/
    ├── bpe_contamination_histogram.png [Script 04]
    └── bpe_f1_comparison.png           [Script 04]
```

---

## Further Reading

### Related Documentation
- **Script 01 Documentation**: `README_SCRIPT_01.md`
- **Utils Library Documentation**: `utils/README.md`
- **Project Overview**: `00_INDEX.md`

### External Resources
- [Precision and Recall (Wikipedia)](https://en.wikipedia.org/wiki/Precision_and_recall)
- [F1 Score Explained](https://en.wikipedia.org/wiki/F-score)
- [McNemar's Test](https://en.wikipedia.org/wiki/McNemar%27s_test)
- [Bootstrap Methods](https://en.wikipedia.org/wiki/Bootstrapping_(statistics))
- [BPE Tokenization](https://huggingface.co/docs/transformers/tokenizer_summary#bytepair-encoding-bpe)

---

## Contact & Support

For questions or issues:
1. Check this documentation
2. Review error logs (`.log` files)
3. Examine example outputs in `results/`
4. Consult utils documentation: `utils/README.md`

---

**Last Updated**: 2025-11-05
**Version**: 1.0
