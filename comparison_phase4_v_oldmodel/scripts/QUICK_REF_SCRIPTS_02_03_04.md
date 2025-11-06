# Quick Reference: Scripts 02-04

One-page reference for Scripts 02-04 of the Phase 4 vs V2 NER comparison project.

## Quick Start

```bash
# Prerequisites: Must run Script 01 first
python 01_preprocess_and_align.py

# Run all evaluation scripts
python 02_evaluate_on_test_split.py      # Test split evaluation
python 03_evaluate_on_inventory.py       # Inventory detection
python 04_analyze_bpe_artifacts.py       # BPE contamination analysis
```

---

## Script 02: Test Split Evaluation

**Purpose**: Evaluate on 67 papers with ground truth

**Basic Usage**:
```bash
python 02_evaluate_on_test_split.py
```

**Common Options**:
```bash
--match-strategy fuzzy    # Use fuzzy matching
--n-examples 20           # Generate 20 examples
--verbose                 # Detailed logging
```

**Key Outputs**:
- `results/test_split_metrics.csv` - Per-paper F1 scores
- `results/test_split_aggregate.json` - Overall metrics + CI
- `results/test_split_comparison.md` - Summary report
- `results/test_split_examples.txt` - Detailed examples

**Key Metrics**:
- **Micro F1**: Overall performance (weighted by entities)
- **Macro F1**: Average per-paper performance
- **McNemar's test**: Statistical significance (p < 0.05)

---

## Script 03: Inventory Evaluation

**Purpose**: Evaluate on 3,113 validated resources

**Basic Usage**:
```bash
python 03_evaluate_on_inventory.py
```

**Common Options**:
```bash
--inventory custom.csv    # Custom inventory file
--verbose                 # Detailed logging
```

**Key Outputs**:
- `results/inventory_evaluation.csv` - Per-resource results
- `results/inventory_metrics.json` - Detection rates
- `results/missed_resources.csv` - Resources neither found
- `results/novel_discoveries.csv` - New entities discovered

**Key Metrics**:
- **Detection Rate**: % of resources detected (any match)
- **Correct Detection Rate**: % with exact/fuzzy match
- **Novel Discoveries**: Entities not in inventory

---

## Script 04: BPE Artifact Analysis

**Purpose**: Analyze BPE contamination impact

**Basic Usage**:
```bash
python 04_analyze_bpe_artifacts.py
```

**Common Options**:
```bash
--figures custom_figs/    # Custom figures directory
--verbose                 # Detailed logging
```

**Key Outputs**:
- `results/bpe_contamination_report.md` - Detailed report
- `results/bpe_impact_on_metrics.csv` - F1 degradation
- `figures/bpe_contamination_histogram.png` - Distribution
- `figures/bpe_f1_comparison.png` - Before/after comparison

**Key Metrics**:
- **Entity Contamination Rate**: % entities with artifacts
- **Paper Contamination Rate**: % papers affected
- **F1 Improvement**: Clean F1 - Raw F1

---

## Output Files Quick Reference

### Script 02 Outputs
| File | Purpose |
|------|---------|
| `test_split_metrics.csv` | Per-paper P/R/F1 for all systems |
| `test_split_aggregate.json` | Micro/macro F1 + confidence intervals |
| `test_split_comparison.md` | Markdown summary report |
| `test_split_examples.txt` | 10 detailed examples |
| `test_split_significance.json` | McNemar's test, bootstrap CI |

### Script 03 Outputs
| File | Purpose |
|------|---------|
| `inventory_evaluation.csv` | Per-resource match results |
| `inventory_metrics.json` | Detection rates, precision |
| `missed_resources.csv` | Resources neither system found |
| `novel_discoveries.csv` | Entities not in inventory |
| `inventory_comparison.md` | Markdown summary report |
| `inventory_by_length.csv` | Performance by entity length |
| `inventory_by_year.csv` | Performance by publication year |

### Script 04 Outputs
| File | Purpose |
|------|---------|
| `bpe_contamination_report.md` | Comprehensive markdown report |
| `bpe_impact_on_metrics.csv` | Per-paper F1 comparison |
| `bpe_artifact_patterns.json` | Common patterns + frequencies |
| `bpe_contamination_stats.json` | Detailed contamination stats |
| `bpe_contamination_histogram.png` | Distribution visualization |
| `bpe_f1_comparison.png` | F1 scores before/after |

---

## Key Concepts

### F1 Score Components
```
Precision = TP / (TP + FP)    # What % of predictions are correct?
Recall = TP / (TP + FN)       # What % of true entities were found?
F1 = 2 × (P × R) / (P + R)   # Harmonic mean
```

### Match Types (Script 03)
- **Correct**: Exact or fuzzy match (Levenshtein ≤ 2)
- **Partial**: Substring or token overlap (Jaccard ≥ 0.6)
- **Miss**: No match found

### BPE Artifacts
- **Ġ markers**: "Ġprotein" should be "protein"
- **Subwords**: "pro te in" should be "protein"

---

## Common Commands

### Run with custom paths
```bash
python 02_evaluate_on_test_split.py \
    --input custom_aligned.csv \
    --output custom_results/
```

### Use fuzzy matching
```bash
python 02_evaluate_on_test_split.py --match-strategy fuzzy
```

### Generate more examples
```bash
python 02_evaluate_on_test_split.py --n-examples 20
```

### Custom inventory
```bash
python 03_evaluate_on_inventory.py --inventory data/custom_inventory.csv
```

### Verbose logging
```bash
python 04_analyze_bpe_artifacts.py --verbose 2>&1 | tee analysis.log
```

---

## Troubleshooting

### "Aligned papers file not found"
```bash
# Run Script 01 first
python 01_preprocess_and_align.py
```

### "Module 'scipy' not found"
```bash
pip install scipy
```

### "Module 'matplotlib' not found"
```bash
pip install matplotlib seaborn
```

### Check script help
```bash
python 02_evaluate_on_test_split.py --help
python 03_evaluate_on_inventory.py --help
python 04_analyze_bpe_artifacts.py --help
```

---

## Results Interpretation

### Script 02: Test Split
**Good Performance**:
- F1 > 0.8: Excellent
- F1 > 0.6: Good
- F1 > 0.4: Fair

**Statistical Significance**:
- p < 0.05: Significant difference
- 95% CI excludes 0: Meaningful improvement

### Script 03: Inventory
**Good Detection**:
- Detection rate > 80%: Excellent
- Detection rate > 60%: Good
- Detection rate > 40%: Fair

**Novel Discoveries**:
- High occurrences: Likely real entities
- Low occurrences: May be noise/errors

### Script 04: BPE Contamination
**Severity Levels**:
- > 50% contaminated: Critical
- 20-50%: High
- 5-20%: Moderate
- < 5%: Low

**F1 Impact**:
- Improvement > 0.1: Severe contamination
- Improvement 0.05-0.1: Moderate
- Improvement < 0.05: Minor

---

## Execution Time

| Script | Papers | Time |
|--------|--------|------|
| 02 | 67 | 30-60 sec |
| 03 | 20,890 | 5-10 min |
| 04 | 20,890 | 3-5 min |

---

## Dependencies

```bash
pip install pandas numpy scipy matplotlib seaborn tqdm
```

**Version requirements**:
- pandas >= 1.5.0
- numpy >= 1.23.0
- scipy >= 1.9.0
- matplotlib >= 3.6.0
- seaborn >= 0.12.0
- tqdm >= 4.64.0

---

## Further Help

- **Full documentation**: `README_SCRIPTS_02_03_04.md`
- **Script 01 docs**: `README_SCRIPT_01.md`
- **Utils docs**: `utils/README.md`
- **Project index**: `00_INDEX.md`

---

**Last Updated**: 2025-11-05
