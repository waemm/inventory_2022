# Scripts 05-08: Analysis & Reporting

**Purpose**: Final phase of the comparison pipeline - sampling, visualization, and comprehensive reporting.

## Overview

These scripts complete the Phase 4 vs V2 NER comparison by:
1. Selecting interesting papers for qualitative review
2. Creating human-readable comparisons
3. Synthesizing all findings into a comprehensive report
4. Generating publication-quality visualizations

---

## Script 05: Sample 100 Papers

**File**: `05_sample_100_papers.py`

**Purpose**: Select 100 interesting papers for detailed manual inspection using stratified sampling.

### Sampling Strategy

Selects 25 papers from each category:
- **Agreement**: Both V2 and Phase 4 predict same entities
- **Phase 4 Better**: Phase 4 finds entities V2 missed
- **V2 Better**: V2 finds entities Phase 4 missed
- **Disagreement**: Both predict different entities

### Prioritization Criteria

Papers are ranked by "interest score" based on:
- Papers with ground truth (highest priority)
- Papers with multiple entities
- Papers with BPE artifacts
- Papers with long entity names (>50 chars)
- Papers showing disagreement patterns

### Usage

```bash
# Basic usage
python 05_sample_100_papers.py

# Custom sample size per category
python 05_sample_100_papers.py --n-per-category 30

# Custom paths
python 05_sample_100_papers.py \
    --comparison-file ../results/04_merged_comparison.csv \
    --ground-truth ../data/ground_truth.json \
    --output-dir ../data
```

### Outputs

- **`sample_100_papers.csv`**: Selected papers with all metadata
  - PMID, title, abstract
  - V2 and Phase 4 predictions
  - Category assignment
  - Interest score
  - BPE artifact counts

- **`sample_stratification.json`**: Sampling metadata
  - Total papers available
  - Sample distribution by category
  - Sampling criteria used
  - Feature statistics

### Key Features

```python
def categorize_paper(pmid, v2_entities, phase4_entities, ground_truth):
    """
    Categorize paper based on prediction patterns.

    Categories:
    - AGREEMENT: Same predictions
    - PHASE4_BETTER: Phase 4 has unique entities
    - V2_BETTER: V2 has unique entities
    - DISAGREEMENT: Both have unique entities
    """
```

**Interest Score Calculation**:
```python
interest_score = 0.0
interest_score += 10.0 if has_ground_truth else 0.0
interest_score += min(total_entities * 2, 10.0)
interest_score += 5.0 if disagreement else 0.0
interest_score += (bpe_artifacts * 0.5)
interest_score += 3.0 if max_entity_length > 50 else 0.0
```

---

## Script 06: Generate Side-by-Side Comparison

**File**: `06_generate_side_by_side.py`

**Purpose**: Create human-readable side-by-side comparison for the 100 sampled papers.

### Output Formats

1. **HTML** (`100_paper_comparison.html`)
   - Interactive web page with professional styling
   - Color-coded categories
   - Collapsible sections
   - Printable format

2. **Markdown** (`100_paper_comparison.md`)
   - Plain text format for easy reading
   - Git-friendly
   - Searchable

3. **JSON** (`category_breakdown.json`)
   - Machine-readable statistics
   - Category counts and distributions

### Usage

```bash
# Basic usage
python 06_generate_side_by_side.py

# Custom paths
python 06_generate_side_by_side.py \
    --sample-file ../data/sample_100_papers.csv \
    --ground-truth ../data/ground_truth.json \
    --output-dir ../results
```

### HTML Features

**Professional Styling**:
- Responsive design
- Color-coded categories (green=agreement, blue=Phase 4 better, red=V2 better, orange=disagreement)
- Entity-level correctness indicators (✓/✗)
- Summary statistics dashboard
- Table of contents with jump links

**Paper Display Format**:
```
Paper ID: 21389154
Category: AGREEMENT

Title: Automated identification...
Abstract: [First 300 chars]

Ground Truth: 16SpathDB
V2 Prediction: 16SpathDB ✓
Phase 4 (Raw): Ġ16SpathDB ✗
Phase 4 (Clean): 16SpathDB ✓

Metadata:
- V2 Count: 1
- Phase 4 Count: 1
- Ground Truth: Yes
- Interest Score: 12.5
```

### Key Functions

```python
def create_paper_html(paper, ground_truth):
    """Generate HTML for single paper with styling."""

def create_paper_markdown(paper, ground_truth):
    """Generate Markdown for single paper."""
```

---

## Script 07: Generate Final Report

**File**: `07_generate_final_report.py`

**Purpose**: Synthesize all findings into a comprehensive report.

### Report Structure

1. **Executive Summary** (1 page)
   - 5 key findings
   - Overall recommendation
   - High-level metrics

2. **Quantitative Metrics**
   - Performance tables
   - Confusion matrices
   - Statistical significance tests

3. **Qualitative Analysis**
   - Error pattern distribution
   - Representative examples
   - Failure mode analysis

4. **BPE Artifact Deep Dive**
   - Contamination overview
   - Performance impact
   - Most common artifacts

5. **100-Paper Analysis**
   - Sampling strategy
   - Category distribution
   - Key observations

6. **Recommendations**
   - Immediate actions
   - Long-term improvements
   - Best practices

### Usage

```bash
# Basic usage
python 07_generate_final_report.py

# Custom paths
python 07_generate_final_report.py \
    --results-dir ../results \
    --output-dir ../results
```

### Outputs

- **`PHASE4_VS_V2_COMPREHENSIVE_REPORT.md`**: Full report (main deliverable)
- **`EXECUTIVE_SUMMARY.md`**: 1-page summary for stakeholders
- **`report_metadata.json`**: Report generation metadata

### Key Sections

**Executive Summary Generation**:
```python
def generate_executive_summary(results):
    """
    Create executive summary with:
    - 5 key findings (data-driven)
    - Overall recommendation
    - Performance comparison
    - Error pattern highlights
    """
```

**Recommendation Logic**:
```python
if phase4_clean_f1 > v2_f1 and bpe_contamination < 20:
    return "Deploy Phase 4 with BPE cleaning"
elif phase4_clean_f1 > v2_f1:
    return "Address BPE contamination first"
else:
    return "Continue with V2"
```

### Report Customization

Each section is independently generated:
- `generate_quantitative_section()`
- `generate_qualitative_section()`
- `generate_bpe_section()`
- `generate_100_paper_section()`
- `generate_recommendations_section()`

---

## Script 08: Create Visualizations

**File**: `08_create_visualizations.py`

**Purpose**: Create publication-quality visualizations for the report.

### Figures Generated

1. **`01_performance_comparison.png`**
   - Bar chart: Precision, Recall, F1
   - Three systems: V2, Phase 4 Raw, Phase 4 Clean
   - Value labels on bars

2. **`02_confusion_matrices.png`**
   - Heatmaps for V2 and Phase 4
   - Side-by-side comparison
   - Annotated with counts

3. **`03_entity_distribution.png`**
   - Histograms of entities per paper
   - Separate panels for V2 and Phase 4
   - Mean lines

4. **`04_bpe_contamination.png`**
   - Pie chart: contamination rate
   - Bar chart: performance impact
   - Before/after cleaning

5. **`05_coverage_analysis.png`**
   - Venn diagram-style visualization
   - V2 only, Phase 4 only, Both, Neither
   - Percentage breakdown

6. **`06_entity_length_distribution.png`**
   - Histograms of entity name lengths
   - Mean and median lines
   - Two panels (V2, Phase 4)

### Usage

```bash
# Basic usage
python 08_create_visualizations.py

# Custom paths
python 08_create_visualizations.py \
    --results-dir ../results \
    --output-dir ../figures
```

### Output Specifications

- **Format**: PNG
- **DPI**: 300 (publication quality)
- **Style**: seaborn-paper
- **Color palette**: husl (colorblind-friendly)

### Figure Creation

```python
FIGURE_DPI = 300
FIGURE_FORMAT = "png"

def create_performance_comparison(metrics, output_path):
    """Bar chart comparing V2 and Phase 4."""

def create_confusion_matrices(metrics, output_dir):
    """Heatmaps for each system."""

def create_entity_distribution(comparison_df, output_path):
    """Histograms of entity counts."""
```

### Customization

All visualizations use consistent styling:
- Font sizes: 10-14pt
- Bold titles and labels
- Grid lines for readability
- Color-coded by system
- Professional aesthetics

---

## Pipeline Integration

### Complete Workflow

```bash
# Step 1: Sample papers
python 05_sample_100_papers.py

# Step 2: Generate comparisons
python 06_generate_side_by_side.py

# Step 3: Create report
python 07_generate_final_report.py

# Step 4: Generate figures
python 08_create_visualizations.py
```

### Or use the master script:

```bash
# Run all scripts in sequence
bash run_complete_comparison.sh
```

---

## Dependencies

### Python Packages

```txt
pandas>=1.5.0
numpy>=1.23.0
matplotlib>=3.6.0
seaborn>=0.12.0
scipy>=1.9.0
tqdm>=4.64.0
```

### Input Files Required

- `../results/04_merged_comparison.csv` (from Script 04)
- `../data/ground_truth.json` (from Script 01)
- `../results/02_quantitative_metrics.json` (from Script 02)
- `../results/03_qualitative_analysis.json` (from Script 03)
- `../results/04_bpe_analysis.json` (from Script 04)

---

## Output Directory Structure

```
comparison_phase4_v_oldmodel/
├── data/
│   ├── sample_100_papers.csv          # Script 05
│   └── sample_stratification.json     # Script 05
├── results/
│   ├── 100_paper_comparison.html      # Script 06
│   ├── 100_paper_comparison.md        # Script 06
│   ├── category_breakdown.json        # Script 06
│   ├── PHASE4_VS_V2_COMPREHENSIVE_REPORT.md  # Script 07
│   ├── EXECUTIVE_SUMMARY.md           # Script 07
│   └── report_metadata.json           # Script 07
├── figures/
│   ├── 01_performance_comparison.png  # Script 08
│   ├── 02_confusion_matrices.png      # Script 08
│   ├── 03_entity_distribution.png     # Script 08
│   ├── 04_bpe_contamination.png       # Script 08
│   ├── 05_coverage_analysis.png       # Script 08
│   ├── 06_entity_length_distribution.png  # Script 08
│   └── visualization_metadata.json    # Script 08
└── logs/
    ├── 05_sampling.log
    ├── 06_side_by_side.log
    ├── 07_report_generation.log
    └── 08_visualizations.log
```

---

## Error Handling

All scripts include comprehensive error handling:

```python
try:
    # Main processing
    result = process_data(...)
    logger.info("SUCCESS!")
    return 0
except Exception as e:
    logger.error(f"ERROR: {str(e)}", exc_info=True)
    return 1
```

### Common Issues

**Issue**: Missing input files
**Solution**: Check that Scripts 01-04 completed successfully

**Issue**: Matplotlib backend errors
**Solution**: Set `MPLBACKEND=Agg` environment variable

**Issue**: Memory errors with large datasets
**Solution**: Process in batches or increase available RAM

---

## Performance Considerations

### Script 05 (Sampling)
- **Time**: ~1-2 minutes for 20K papers
- **Memory**: ~500MB
- **Bottleneck**: Interest score calculation

### Script 06 (Side-by-Side)
- **Time**: ~2-3 minutes for 100 papers
- **Memory**: ~200MB
- **Bottleneck**: HTML generation

### Script 07 (Report)
- **Time**: <1 minute
- **Memory**: ~100MB
- **Bottleneck**: JSON loading

### Script 08 (Visualizations)
- **Time**: ~2-3 minutes for 6 figures
- **Memory**: ~300MB
- **Bottleneck**: Figure rendering at 300 DPI

---

## Quality Assurance

### Validation Checks

Each script performs validation:
- Input file existence
- Data integrity
- Required columns present
- Output directory writable

### Logging

All scripts log:
- Input/output file paths
- Processing steps
- Summary statistics
- Errors and warnings

### Reproducibility

Fixed random seeds ensure reproducibility:
```python
np.random.seed(42)
random_state = 42
```

---

## Customization Guide

### Modify Sampling Strategy

Edit `05_sample_100_papers.py`:

```python
# Change interest score weights
interest_score += 20.0 if has_ground_truth else 0.0  # Increase GT priority
interest_score += 10.0 if disagreement else 0.0      # Increase disagreement priority

# Change sample size
n_per_category = 30  # Default: 25
```

### Customize Report Sections

Edit `07_generate_final_report.py`:

```python
def generate_custom_section(results):
    """Add your own analysis section."""
    section = "# My Custom Analysis\n\n"
    # Add content
    return section

# Add to report
full_report = (
    header
    + exec_summary
    + custom_section  # <-- Add here
    + quant_section
    # ...
)
```

### Modify Visualizations

Edit `08_create_visualizations.py`:

```python
# Change figure size
fig, ax = plt.subplots(figsize=(12, 8))  # Default: (10, 6)

# Change DPI
FIGURE_DPI = 600  # Default: 300

# Change colors
colors = ["#FF0000", "#00FF00", "#0000FF"]  # Custom palette
```

---

## Best Practices

1. **Always run scripts in order** (01 → 02 → 03 → 04 → 05 → 06 → 07 → 08)
2. **Check logs** after each script for warnings
3. **Validate outputs** before proceeding to next step
4. **Back up results** before re-running
5. **Review HTML comparison** before finalizing report

---

## Troubleshooting

### Script 05: No papers sampled

**Cause**: Merged comparison file empty or missing categories
**Fix**: Check Script 04 output

### Script 06: HTML rendering issues

**Cause**: Special characters in titles/abstracts
**Fix**: Script handles HTML escaping automatically

### Script 07: Missing metrics

**Cause**: Earlier analysis scripts failed
**Fix**: Re-run Scripts 02-04

### Script 08: Import errors

**Cause**: Missing visualization libraries
**Fix**: `pip install matplotlib seaborn scipy`

---

## Support

For questions or issues:
1. Check script logs in `../results/` or `../logs/`
2. Review this documentation
3. Examine example outputs
4. Contact ML team

---

## Version History

- **v1.0** (2025-11-05): Initial implementation
  - Stratified sampling
  - Side-by-side comparison
  - Comprehensive reporting
  - Publication-quality figures

---

**Next Steps**: Run the complete pipeline and review the comprehensive report!
