# Quick Reference: Scripts 05-08

**Purpose**: Fast reference for running the final analysis scripts.

---

## Quick Start

```bash
# Navigate to scripts directory
cd comparison_phase4_v_oldmodel/scripts

# Run all four scripts in sequence
python 05_sample_100_papers.py
python 06_generate_side_by_side.py
python 07_generate_final_report.py
python 08_create_visualizations.py

# Or use the master script (when available)
bash run_scripts_05_08.sh
```

---

## Script 05: Sample 100 Papers

**Input**: `../results/04_merged_comparison.csv`
**Output**: `../data/sample_100_papers.csv`, `../data/sample_stratification.json`

```bash
# Default usage
python 05_sample_100_papers.py

# Custom sample size (30 per category instead of 25)
python 05_sample_100_papers.py --n-per-category 30
```

**What it does**: Selects 100 interesting papers (25 from each category: Agreement, Phase 4 Better, V2 Better, Disagreement) for manual inspection, prioritizing papers with ground truth and interesting features.

---

## Script 06: Generate Side-by-Side

**Input**: `../data/sample_100_papers.csv`
**Output**: `../results/100_paper_comparison.html`, `../results/100_paper_comparison.md`, `../results/category_breakdown.json`

```bash
# Default usage
python 06_generate_side_by_side.py
```

**What it does**: Creates human-readable side-by-side comparison with color-coded categories, entity correctness indicators, and professional HTML styling.

**Key output**: Open `../results/100_paper_comparison.html` in browser for interactive review.

---

## Script 07: Generate Final Report

**Input**: All results from Scripts 01-06
**Output**: `../results/PHASE4_VS_V2_COMPREHENSIVE_REPORT.md`, `../results/EXECUTIVE_SUMMARY.md`, `../results/report_metadata.json`

```bash
# Default usage
python 07_generate_final_report.py
```

**What it does**: Synthesizes all findings into comprehensive report with:
- Executive summary (5 key findings + recommendation)
- Quantitative metrics
- Qualitative analysis
- BPE deep dive
- 100-paper analysis
- Recommendations

**Key output**: Review `../results/EXECUTIVE_SUMMARY.md` first for high-level takeaways.

---

## Script 08: Create Visualizations

**Input**: `../results/02_quantitative_metrics.json`, `../results/04_bpe_analysis.json`, `../results/04_merged_comparison.csv`
**Output**: 6 PNG files in `../figures/` at 300 DPI

```bash
# Default usage
python 08_create_visualizations.py
```

**What it does**: Creates publication-quality figures:
1. Performance comparison bar chart
2. Confusion matrices
3. Entity distribution histograms
4. BPE contamination analysis
5. Coverage Venn diagram
6. Entity length distributions

**Key output**: All figures saved to `../figures/` for inclusion in presentations/papers.

---

## Common Options

### All Scripts Support

```bash
--help              # Show help message
```

### Script-Specific Options

```bash
# Script 05
--n-per-category 30              # Sample 30 papers per category (default: 25)
--comparison-file PATH           # Custom comparison file
--ground-truth PATH              # Custom ground truth file
--output-dir PATH                # Custom output directory

# Script 06
--sample-file PATH               # Custom sample file
--ground-truth PATH              # Custom ground truth file
--output-dir PATH                # Custom output directory

# Script 07
--results-dir PATH               # Custom results directory
--output-dir PATH                # Custom output directory

# Script 08
--results-dir PATH               # Custom results directory
--output-dir PATH                # Custom figures directory
```

---

## Expected Outputs

### After Script 05

```
data/
├── sample_100_papers.csv           # 100 selected papers with metadata
└── sample_stratification.json      # Sampling breakdown
```

### After Script 06

```
results/
├── 100_paper_comparison.html       # Interactive HTML comparison ⭐
├── 100_paper_comparison.md         # Markdown version
└── category_breakdown.json         # Category statistics
```

### After Script 07

```
results/
├── PHASE4_VS_V2_COMPREHENSIVE_REPORT.md   # Full report ⭐⭐
├── EXECUTIVE_SUMMARY.md                   # 1-page summary ⭐
└── report_metadata.json                   # Report metadata
```

### After Script 08

```
figures/
├── 01_performance_comparison.png          # Main performance chart ⭐
├── 02_confusion_matrices.png              # CM heatmaps
├── 03_entity_distribution.png             # Entity counts
├── 04_bpe_contamination.png               # BPE analysis
├── 05_coverage_analysis.png               # Venn diagram
├── 06_entity_length_distribution.png      # Length histograms
└── visualization_metadata.json            # Figure metadata
```

⭐ = High-priority outputs to review

---

## Execution Time

| Script | Time | Memory | Notes |
|--------|------|--------|-------|
| 05 | 1-2 min | 500 MB | Interest score calculation |
| 06 | 2-3 min | 200 MB | HTML generation |
| 07 | <1 min | 100 MB | Fast synthesis |
| 08 | 2-3 min | 300 MB | Figure rendering |

**Total**: ~6-9 minutes for all four scripts

---

## Validation Checklist

After running each script:

### Script 05
- [ ] `sample_100_papers.csv` has 100 rows (or target sample size)
- [ ] All four categories represented (25 papers each by default)
- [ ] `sample_stratification.json` shows expected distribution
- [ ] Log shows no errors: `cat ../data/05_sampling.log | grep ERROR`

### Script 06
- [ ] HTML file opens in browser without errors
- [ ] All 100 papers displayed with categories
- [ ] Color coding works (green/blue/red/orange)
- [ ] Markdown file readable
- [ ] Log shows success: `tail ../results/06_side_by_side.log`

### Script 07
- [ ] Comprehensive report has all sections
- [ ] Executive summary has 5 findings + recommendation
- [ ] Metrics tables populated
- [ ] No placeholder text
- [ ] Log shows success: `tail ../results/07_report_generation.log`

### Script 08
- [ ] 6 PNG files created in `../figures/`
- [ ] All files >100 KB (not empty)
- [ ] Images open without errors
- [ ] High resolution (300 DPI)
- [ ] Log shows all figures created: `tail ../results/08_visualizations.log`

---

## Troubleshooting

### "File not found" errors

**Cause**: Missing outputs from earlier scripts
**Fix**: Re-run Scripts 01-04 first

```bash
cd comparison_phase4_v_oldmodel/scripts
python 01_compute_quantitative_metrics.py
python 02_qualitative_error_analysis.py
python 03_analyze_bpe_artifacts.py
python 04_merge_all_results.py
```

### HTML doesn't display correctly

**Cause**: Browser compatibility or special characters
**Fix**: Try different browser (Chrome recommended) or check Markdown version

### Figures look blurry

**Cause**: Low DPI or small figure size
**Fix**: Check `FIGURE_DPI = 300` in Script 08

### Out of memory

**Cause**: Large dataset
**Fix**: Process in batches or reduce sample size

---

## Pro Tips

1. **Review HTML first**: `open ../results/100_paper_comparison.html` gives best qualitative overview

2. **Check executive summary**: Quick read of `EXECUTIVE_SUMMARY.md` before diving into full report

3. **Use figures in presentations**: All PNGs at 300 DPI ready for papers/slides

4. **Compare with baseline**: Review figures side-by-side with previous analysis

5. **Archive results**: Back up entire `results/` and `figures/` directories before re-running

---

## One-Liner Commands

```bash
# Count papers per category in sample
python -c "import pandas as pd; df=pd.read_csv('../data/sample_100_papers.csv'); print(df['category'].value_counts())"

# Check report sections
grep "^#" ../results/PHASE4_VS_V2_COMPREHENSIVE_REPORT.md

# List all figures
ls -lh ../figures/*.png

# View logs quickly
tail -20 ../results/*.log
```

---

## Next Steps After Completion

1. **Review Executive Summary** (`EXECUTIVE_SUMMARY.md`)
2. **Open HTML Comparison** (`100_paper_comparison.html`)
3. **Check Key Figures** (01, 04, 05 are most important)
4. **Read Full Report** (`PHASE4_VS_V2_COMPREHENSIVE_REPORT.md`)
5. **Make Decision**: Deploy Phase 4 or continue with V2?

---

## Master Script (Optional)

Create `run_scripts_05_08.sh`:

```bash
#!/bin/bash
set -e  # Exit on error

echo "===== Script 05: Sampling ====="
python 05_sample_100_papers.py

echo "===== Script 06: Side-by-Side ====="
python 06_generate_side_by_side.py

echo "===== Script 07: Report ====="
python 07_generate_final_report.py

echo "===== Script 08: Visualizations ====="
python 08_create_visualizations.py

echo "===== COMPLETE ====="
echo "Review: ../results/EXECUTIVE_SUMMARY.md"
echo "HTML: ../results/100_paper_comparison.html"
echo "Figures: ../figures/"
```

Run with: `bash run_scripts_05_08.sh`

---

**Documentation**: See `README_SCRIPTS_05_08.md` for detailed information.
