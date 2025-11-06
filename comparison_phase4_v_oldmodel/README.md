# Phase 4 vs V2 NER System Comparison

**Comprehensive comparison framework for evaluating Named Entity Recognition systems**

## Overview

This project provides a complete pipeline for comparing two NER systems (Phase 4 and V2) across multiple dimensions:
- Quantitative performance metrics
- Qualitative error analysis
- BPE artifact contamination
- Stratified sampling for manual inspection
- Publication-quality visualizations
- Comprehensive reporting

## Project Structure

```
comparison_phase4_v_oldmodel/
├── README.md                          # This file
├── data/                              # Input and sampled data
│   ├── ground_truth.json              # Ground truth annotations
│   ├── v2_predictions.csv             # V2 system predictions
│   ├── phase4_predictions.csv         # Phase 4 system predictions
│   ├── sample_100_papers.csv          # Stratified sample (Script 05)
│   └── sample_stratification.json     # Sampling metadata
├── scripts/                           # Analysis pipeline scripts
│   ├── 01_compute_quantitative_metrics.py
│   ├── 02_qualitative_error_analysis.py
│   ├── 03_analyze_bpe_artifacts.py
│   ├── 04_merge_all_results.py
│   ├── 05_sample_100_papers.py
│   ├── 06_generate_side_by_side.py
│   ├── 07_generate_final_report.py
│   ├── 08_create_visualizations.py
│   ├── run_complete_comparison.sh     # Master script (all 8 scripts)
│   ├── run_scripts_05_08.sh           # Final phase only
│   ├── README_SCRIPTS_01_04.md        # Docs for Scripts 01-04
│   ├── README_SCRIPTS_05_08.md        # Docs for Scripts 05-08
│   ├── QUICK_REFERENCE_01_04.md       # Quick ref for Scripts 01-04
│   └── QUICK_REFERENCE_05_08.md       # Quick ref for Scripts 05-08
├── utils/                             # Shared utilities
│   ├── __init__.py
│   ├── comparison_utils.py            # Core comparison functions
│   └── README_UTILS.md                # Utility documentation
├── results/                           # Analysis outputs
│   ├── 02_quantitative_metrics.json
│   ├── 03_qualitative_analysis.json
│   ├── 04_bpe_analysis.json
│   ├── 04_merged_comparison.csv
│   ├── 100_paper_comparison.html      # Interactive comparison ⭐
│   ├── 100_paper_comparison.md
│   ├── category_breakdown.json
│   ├── PHASE4_VS_V2_COMPREHENSIVE_REPORT.md  # Main report ⭐⭐
│   ├── EXECUTIVE_SUMMARY.md           # 1-page summary ⭐
│   └── report_metadata.json
├── figures/                           # Visualizations
│   ├── 01_performance_comparison.png
│   ├── 02_confusion_matrices.png
│   ├── 03_entity_distribution.png
│   ├── 04_bpe_contamination.png
│   ├── 05_coverage_analysis.png
│   ├── 06_entity_length_distribution.png
│   └── visualization_metadata.json
└── tests/                             # Unit tests
    ├── test_quantitative_metrics.py
    ├── test_qualitative_analysis.py
    ├── test_bpe_detection.py
    └── test_utils.py
```

⭐ = High-priority outputs to review

## Quick Start

### Option 1: Run Complete Pipeline (Recommended)

```bash
cd comparison_phase4_v_oldmodel/scripts
bash run_complete_comparison.sh
```

This runs all 8 scripts in sequence (~15-20 minutes total).

### Option 2: Run in Phases

**Phase 1: Core Analysis (Scripts 01-04)**
```bash
cd comparison_phase4_v_oldmodel/scripts
python 01_compute_quantitative_metrics.py
python 02_qualitative_error_analysis.py
python 03_analyze_bpe_artifacts.py
python 04_merge_all_results.py
```

**Phase 2: Reporting (Scripts 05-08)**
```bash
bash run_scripts_05_08.sh
```

### Option 3: Individual Scripts

```bash
cd comparison_phase4_v_oldmodel/scripts
python 05_sample_100_papers.py           # ~2 min
python 06_generate_side_by_side.py       # ~3 min
python 07_generate_final_report.py       # ~1 min
python 08_create_visualizations.py       # ~3 min
```

## Key Deliverables

### 1. Executive Summary
**File**: `results/EXECUTIVE_SUMMARY.md`

High-level overview with:
- 5 key findings
- Overall recommendation
- Performance comparison

**Start here** for quick insights.

### 2. Comprehensive Report
**File**: `results/PHASE4_VS_V2_COMPREHENSIVE_REPORT.md`

Full analysis including:
- Quantitative metrics (P/R/F1, confusion matrices)
- Statistical significance tests
- Qualitative error patterns
- BPE artifact deep dive
- 100-paper analysis
- Recommendations

### 3. Interactive Comparison
**File**: `results/100_paper_comparison.html`

Side-by-side comparison of 100 papers with:
- Color-coded categories
- Entity-level correctness indicators
- Ground truth comparison
- Professional styling

**Open in browser** for best experience.

### 4. Visualizations
**Directory**: `figures/`

6 publication-quality figures (300 DPI):
1. Performance comparison bar chart
2. Confusion matrices
3. Entity distribution histograms
4. BPE contamination analysis
5. Coverage Venn diagram
6. Entity length distributions

## Pipeline Overview

### Scripts 01-04: Core Analysis

**Script 01**: Compute quantitative metrics
- Precision, Recall, F1-score
- Confusion matrices
- Statistical significance tests
- Bootstrap confidence intervals

**Script 02**: Qualitative error analysis
- Error pattern categorization
- Representative examples
- Failure mode identification
- Manual inspection of edge cases

**Script 03**: Analyze BPE artifacts
- Detect tokenization contamination
- Measure impact on performance
- Identify common artifacts
- Before/after cleaning comparison

**Script 04**: Merge all results
- Consolidate predictions
- Link ground truth
- Create unified dataset
- Prepare for reporting

### Scripts 05-08: Reporting

**Script 05**: Sample 100 papers
- Stratified sampling (25 per category)
- Interest score prioritization
- Ground truth preference
- Edge case selection

**Script 06**: Generate side-by-side
- HTML with interactive styling
- Markdown for easy reading
- Category breakdown statistics
- Entity correctness indicators

**Script 07**: Generate final report
- Executive summary
- Comprehensive analysis
- Recommendations
- Best practices

**Script 08**: Create visualizations
- 6 publication-quality figures
- 300 DPI PNG format
- Consistent styling
- Ready for presentations

## Requirements

### Python Packages

```bash
pip install pandas numpy scipy matplotlib seaborn tqdm
```

Or use requirements file:
```bash
pip install -r requirements.txt
```

### Versions

- Python ≥ 3.8
- pandas ≥ 1.5.0
- numpy ≥ 1.23.0
- scipy ≥ 1.9.0
- matplotlib ≥ 3.6.0
- seaborn ≥ 0.12.0
- tqdm ≥ 4.64.0

## Input Data Format

### Ground Truth (`data/ground_truth.json`)

```json
{
  "21389154": ["16SpathDB", "Salmonella"],
  "28384796": ["CARD"],
  ...
}
```

### Predictions (`data/v2_predictions.csv`, `data/phase4_predictions.csv`)

```csv
pmid,entities,title,abstract
21389154,"['16SpathDB', 'Salmonella']","Title text...","Abstract text..."
28384796,"['CARD']","Title text...","Abstract text..."
```

## Usage Examples

### Run with Custom Options

```bash
# Custom sample size
python 05_sample_100_papers.py --n-per-category 30

# Custom paths
python 06_generate_side_by_side.py \
    --sample-file custom_sample.csv \
    --output-dir custom_output/

# Skip visualizations
bash run_scripts_05_08.sh --skip-viz

# Run with different ground truth
python 01_compute_quantitative_metrics.py \
    --ground-truth alternate_gt.json
```

### Check Outputs

```bash
# View sample statistics
python -c "import pandas as pd; \
    df=pd.read_csv('data/sample_100_papers.csv'); \
    print(df['category'].value_counts())"

# Count figures generated
ls -1 figures/*.png | wc -l

# View report sections
grep "^#" results/PHASE4_VS_V2_COMPREHENSIVE_REPORT.md

# Check logs for errors
grep ERROR results/*.log
```

## Validation

After running the pipeline, verify:

### Data Integrity
- [ ] All input files present and valid
- [ ] Ground truth loaded correctly
- [ ] Predictions aligned by PMID

### Script Outputs
- [ ] All JSON files valid
- [ ] CSV files have expected columns
- [ ] Sample has correct size (100 papers by default)
- [ ] All 6 figures generated

### Report Quality
- [ ] Executive summary has 5 findings + recommendation
- [ ] All sections populated (no placeholders)
- [ ] Metrics tables complete
- [ ] HTML renders correctly

### Figure Quality
- [ ] All PNGs > 100 KB (not empty)
- [ ] High resolution (300 DPI)
- [ ] Color-coded correctly
- [ ] Labels readable

## Troubleshooting

### Common Issues

**Import errors**
```bash
pip install -r requirements.txt
```

**Missing files**
```bash
# Check prerequisites
ls -lh data/*.{json,csv}
ls -lh results/0*.{json,csv}
```

**Permission errors**
```bash
chmod +x scripts/*.sh
```

**Memory errors**
```bash
# Reduce sample size
python 05_sample_100_papers.py --n-per-category 10
```

### Log Files

All scripts generate logs:
- `results/01_metrics.log`
- `results/02_qualitative.log`
- `results/03_bpe.log`
- `results/04_merge.log`
- `data/05_sampling.log`
- `results/06_side_by_side.log`
- `results/07_report_generation.log`
- `results/08_visualizations.log`

Check logs for detailed error messages.

## Documentation

### Quick References
- **Scripts 01-04**: `scripts/QUICK_REFERENCE_01_04.md`
- **Scripts 05-08**: `scripts/QUICK_REFERENCE_05_08.md`
- **Utilities**: `utils/README_UTILS.md`

### Detailed Guides
- **Scripts 01-04**: `scripts/README_SCRIPTS_01_04.md`
- **Scripts 05-08**: `scripts/README_SCRIPTS_05_08.md`

### API Documentation
- **Core Functions**: `utils/comparison_utils.py` (docstrings)

## Testing

Run unit tests:

```bash
cd comparison_phase4_v_oldmodel
pytest tests/
```

Individual test files:
```bash
pytest tests/test_quantitative_metrics.py
pytest tests/test_qualitative_analysis.py
pytest tests/test_bpe_detection.py
pytest tests/test_utils.py
```

## Performance

| Phase | Scripts | Time | Memory |
|-------|---------|------|--------|
| Core Analysis | 01-04 | 6-9 min | 800 MB |
| Reporting | 05-08 | 6-9 min | 500 MB |
| **Total** | **01-08** | **15-20 min** | **800 MB** |

Scales linearly with dataset size.

## Customization

### Modify Sampling Strategy

Edit `scripts/05_sample_100_papers.py`:
```python
# Change interest score weights
interest_score += 20.0 if has_ground_truth else 0.0
interest_score += 10.0 if disagreement else 0.0
```

### Add Custom Analysis

Create new script `09_custom_analysis.py`:
```python
from utils.comparison_utils import load_comparison_results

# Your analysis here
```

### Customize Report

Edit `scripts/07_generate_final_report.py`:
```python
def generate_custom_section(results):
    """Add custom analysis section."""
    return "# My Analysis\n\n..."
```

## Best Practices

1. **Always run scripts in order** (01 → 08)
2. **Check logs** after each script
3. **Validate outputs** before proceeding
4. **Back up results** before re-running
5. **Review HTML comparison** before finalizing
6. **Read executive summary first**

## Citation

If you use this comparison framework in your research, please cite:

```bibtex
@software{ner_comparison_framework,
  title={Phase 4 vs V2 NER System Comparison Framework},
  author={Your Team},
  year={2025},
  url={https://github.com/your-repo}
}
```

## Contributing

To contribute:
1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## Support

For questions or issues:
1. Check documentation in `scripts/` and `utils/`
2. Review log files in `results/`
3. Run unit tests: `pytest tests/`
4. Contact ML team

## Version History

- **v1.0** (2025-11-05): Initial release
  - Complete 8-script pipeline
  - Stratified sampling
  - Comprehensive reporting
  - Publication-quality figures
  - Unit tests and documentation

## License

[Your License Here]

## Acknowledgments

Built on top of:
- scikit-learn metrics
- matplotlib/seaborn visualization
- pandas data manipulation

---

**Quick Start**: `cd scripts && bash run_complete_comparison.sh`

**Documentation**: See `scripts/README_*.md` and `scripts/QUICK_REFERENCE_*.md`

**Support**: Check logs in `results/*.log` or contact ML team
