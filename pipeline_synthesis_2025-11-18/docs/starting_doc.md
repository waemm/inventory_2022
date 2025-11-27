# Pipeline Synthesis 2025-11-18 - Getting Started

**Complete Bioresource Discovery, Deduplication & Validation Pipeline**

Last Updated: 2025-11-24

---

## Quick Overview

This pipeline processes scientific papers to discover bioresources through a 7-step process:

1. **Union NER** - Combine Named Entity Recognition results from multiple models
2. **Primary Resource Selection** - Identify one primary bioresource per paper
3. **Deduplication** - Remove duplicate resources using entity and URL matching
4. **URL Scanning** - Extract and validate bioresource URLs
5. **Backfill** - Propagate URL scan results across all datasets
6. **Baseline Comparison** - Compare results against 2022 baseline inventory
7. **Visualization** - Generate charts and reports

**Key Features**:
- Session-based execution with resume capability
- Automated URL scanning with Wayback Machine fallback (30% rescue rate)
- Dual-method baseline comparison (PMID + entity matching)
- Interactive visualizations (PNG + HTML formats)
- Comprehensive progress tracking and logging

---

## Quick Start

### Run Complete Pipeline (New Session)
```bash
python run_complete_pipeline.py
```

### Resume Previous Session
```bash
# List all sessions
python run_complete_pipeline.py --list-sessions

# Resume specific session
python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f
```

### Run From Specific Step
```bash
# Start from URL scanning (skip steps 1-3)
python run_complete_pipeline.py --from-step 4
```

### Skip Baseline Comparison
```bash
# Run pipeline without baseline comparison
python run_complete_pipeline.py --skip-baseline
```

---

## Documentation Index

### I want to... run the pipeline

| Goal | Documentation | Location |
|------|---------------|----------|
| **Run the pipeline for the first time** | Quick Start Guide | [run_complete_pipeline.py docstring](../run_complete_pipeline.py) (lines 1-261) |
| **Understand all CLI options** | Command-Line Interface | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md#command-line-interface) |
| **See usage examples** | Usage Examples | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md#usage-examples) |
| **Resume an interrupted run** | Session Management | [results/sessions/README.md](../results/sessions/README.md#quick-reference) |
| **List previous sessions** | Session Management | Run: `python run_complete_pipeline.py --list-sessions` |

### I want to... understand the implementation

| Goal | Documentation | Location |
|------|---------------|----------|
| **Understand the architecture** | Architecture Overview | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md#architecture) |
| **See what files were created/modified** | Implementation Details | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md#new-files-created) |
| **Understand session directory structure** | Session Outputs Guide | [results/sessions/README.md](../results/sessions/README.md#directory-structure) |
| **Review implementation changes** | Change Log | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md) |
| **See code review results** | Code Review | [CODE_REVIEW_2025-11-20.md](../CODE_REVIEW_2025-11-20.md) |

### I want to... understand individual scripts

| Goal | Documentation | Location |
|------|---------------|----------|
| **Quick reference for all scripts** | Script Guide | [SCRIPT_GUIDE.md](../SCRIPT_GUIDE.md) |
| **Detailed script explanations** | Scripts Explained | [SCRIPTS_EXPLAINED.md](../SCRIPTS_EXPLAINED.md) |
| **Understand deduplication logic** | Deduplication Details | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md#step-3-deduplication) |
| **Understand baseline comparison** | Baseline Comparison | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md#baseline-comparison) |
| **Understand visualization generation** | Visualization Details | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md#visualization-generation) |

### I want to... analyze results

| Goal | Documentation | Location |
|------|---------------|----------|
| **Understand output file structure** | Session Directory Guide | [results/sessions/README.md](../results/sessions/README.md) |
| **Analyze baseline comparison results** | Baseline Analysis | [results/sessions/README.md](../results/sessions/README.md#baseline-comparison-outputs) |
| **Investigate missing baseline resources** | Missing Baseline Analysis | [MISSING_BASELINE_ANALYSIS.md](../MISSING_BASELINE_ANALYSIS.md) |
| **View visualizations** | Visualization Outputs | Check `results/sessions/{session-id}/visualizations/` |
| **Access deduplication statistics** | Deduplication Stats | `results/sessions/{session-id}/deduplicated/deduplication_statistics.json` |
| **Review URL scan results** | URL Scan Stats | `results/sessions/{session-id}/url_scanned/url_scan_statistics.txt` |

### I want to... troubleshoot issues

| Goal | Documentation | Location |
|------|---------------|----------|
| **Common troubleshooting** | Troubleshooting Guide | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md#troubleshooting) |
| **Session not found errors** | Session Management | [results/sessions/README.md](../results/sessions/README.md#common-issues) |
| **Check execution logs** | Session Metadata | `results/sessions/{session-id}/session_metadata.json` |
| **Review execution timeline** | Execution Review | [PIPELINE_EXECUTION_REVIEW_2025-11-20.md](../PIPELINE_EXECUTION_REVIEW_2025-11-20.md) |

### I want to... understand project history

| Goal | Documentation | Location |
|------|---------------|----------|
| **Project overview** | Project Summary | [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md) |
| **Development progress** | Progress Tracker | [PROGRESS.md](../PROGRESS.md) |
| **Git commit history** | Commit Summary | [COMMIT_SUMMARY.md](../COMMIT_SUMMARY.md) |
| **Original session documentation** | Session Notes | [docs/PIPELINE_SYNTHESIS_SESSION_2025-11-18.md](PIPELINE_SYNTHESIS_SESSION_2025-11-18.md) |
| **Latest session summary** | Session 2025-11-24 | [SESSION_SUMMARY_2025-11-24.md](../SESSION_SUMMARY_2025-11-24.md) |
| **Deliverables manifest** | Deliverables | [DELIVERABLES_MANIFEST.md](../DELIVERABLES_MANIFEST.md) |

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT DATA                                  │
│  • Linguistic NER results (spacy_ner_results.csv)              │
│  • SetFit classification results (setfit_classified.csv)       │
│  • 2022 Baseline Inventory (data/baseline_2022/...)           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Union NER (18_create_union_ner.py)                    │
│  Merge NER results from linguistic and SetFit pipelines        │
│  Output: union_ner_results.csv                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Primary Resource Selection (19_primary_resource.py)   │
│  Select ONE primary bioresource per paper using scoring        │
│  Output: union_papers_with_primary_resources.csv               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Deduplication (17_deduplicate_all_sets.py)            │
│  Remove duplicates using entity + URL matching                 │
│  Output: set_a/b/c_dedup.csv + statistics                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: URL Scanning (18_scan_urls_set_c.py)                  │
│  Extract and validate bioresource URLs (AUTOMATED)             │
│  • Invokes bioresource_url_scanner via subprocess              │
│  • 120-minute timeout, Wayback Machine fallback                │
│  Output: set_c_with_url_scan.csv + statistics                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Backfill (script TBD)                                 │
│  Propagate URL scan results to Set A and Set B                 │
│  Output: set_a/b/c_final.csv                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Baseline Comparison (20_baseline_comparison.py)       │
│  Compare against 2022 baseline using PMID + entity matching    │
│  Output: baseline_comparison_report.txt + stats.json           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: Visualization (21_generate_visualizations.py)         │
│  Generate PNG + HTML charts from baseline comparison           │
│  Output: 4 chart types × 2 formats = 8 files                   │
└─────────────────────────────────────────────────────────────────┘
```

**Typical Execution Time**: 45-50 minutes for complete pipeline (URL scanning: ~40 min)

---

## Session Management

### Session ID Format
**Pattern**: `YYYY-MM-DD-HHMMSS-xxxxx`
- **Example**: `2025-11-21-143022-a7k3f`
- **Timestamp**: `2025-11-21` at `14:30:22`
- **Random suffix**: `a7k3f` (prevents collisions)

### Session Directory Structure
```
results/sessions/{session-id}/
├── session_metadata.json          # Progress tracking
├── deduplicated/                  # Step 3 outputs
├── url_scanned/                   # Step 4 outputs
├── final/                         # Step 5 outputs
├── baseline_comparison/           # Step 6 outputs
└── visualizations/                # Step 7 outputs
```

See [results/sessions/README.md](../results/sessions/README.md) for complete details.

### Resume Capability

The pipeline tracks completed steps in `session_metadata.json`:
```json
{
  "session_id": "2025-11-21-143022-a7k3f",
  "created_at": "2025-11-21T14:30:22",
  "completed_steps": [1, 2, 3, 4],
  "step_names": {
    "1": "Union NER",
    "2": "Primary Resource Selection",
    "3": "Deduplication"
  }
}
```

**Resume from last completed step**:
```bash
python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f
```

The pipeline will automatically skip completed steps and resume from step 5.

---

## Baseline Comparison

The pipeline compares final results against the 2022 baseline inventory using **dual-method matching**:

### Matching Methods
1. **PMID Match**: Same paper (same PMID)
2. **Entity Match**: Same resource name (normalized string comparison)

### New Columns Added
Each final CSV gets three new boolean columns:
- `in_baseline_pmid`: True if PMID found in baseline
- `in_baseline_entity`: True if entity name found in baseline
- `in_baseline`: True if EITHER match succeeds

### Output Files
1. **baseline_comparison_report.txt** - Human-readable summary
2. **baseline_comparison_stats.json** - Machine-readable statistics
3. **baseline_comparison_data.csv** - Comparison data for visualizations

### Example Statistics
From a recent run:
```json
{
  "baseline": {
    "total_resources": 3112,
    "coverage_set_c": 2197,
    "coverage_pct_c": 70.6
  },
  "sets": {
    "C": {
      "total_resources": 4076,
      "in_baseline": 2680,
      "in_baseline_pct": 65.8,
      "novel_discoveries": 1396,
      "novel_pct": 34.2
    }
  }
}
```

**Interpretation**: Set C found 70.6% of baseline resources and discovered 1,396 novel resources.

---

## Visualizations

The pipeline generates **4 chart types** in **2 formats** each:

### Chart Types
1. **Baseline Coverage** - Bar chart showing % of baseline resources found
2. **Match Types Distribution** - Stacked bar showing PMID/entity/both/novel breakdown
3. **Resource Counts** - Side-by-side comparison of baseline vs novel
4. **Score Distributions** - Histogram of URL scores (if available)

### Output Formats
- **PNG**: Static images for reports/papers
- **HTML**: Interactive Plotly charts with hover tooltips

### Location
All visualizations saved to: `results/sessions/{session-id}/visualizations/`

### Example Files
```
visualizations/
├── baseline_coverage.png
├── baseline_coverage.html
├── match_types.png
├── match_types.html
├── resource_counts.png
├── resource_counts.html
├── score_distributions.png      # Optional
└── score_distributions.html     # Optional
```

---

## Common Workflows

### Workflow 1: First Time User
```bash
# 1. Run complete pipeline
python run_complete_pipeline.py

# 2. View visualizations
open results/sessions/2025-11-21-*/visualizations/baseline_coverage.html

# 3. Check baseline comparison report
cat results/sessions/2025-11-21-*/baseline_comparison/baseline_comparison_report.txt
```

### Workflow 2: Resume Interrupted Run
```bash
# 1. List sessions to find interrupted session
python run_complete_pipeline.py --list-sessions

# Output:
# Available sessions:
# - 2025-11-21-143022-a7k3f (in progress) ✓ Steps: 1,2,3

# 2. Resume from last completed step
python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f
```

### Workflow 3: Skip Steps You've Already Run
```bash
# You've already run steps 1-3 manually, start from step 4
python run_complete_pipeline.py --from-step 4
```

### Workflow 4: Quick Run Without Baseline
```bash
# Run pipeline but skip baseline comparison (faster)
python run_complete_pipeline.py --skip-baseline
```

### Workflow 5: Analyze Previous Results
```bash
# List all sessions
python run_complete_pipeline.py --list-sessions

# Navigate to specific session
cd results/sessions/2025-11-21-143022-a7k3f

# View deduplication statistics
cat deduplicated/deduplication_statistics.json

# View baseline comparison
cat baseline_comparison/baseline_comparison_report.txt

# Open interactive charts
open visualizations/*.html
```

---

## File Locations Quick Reference

| File Type | Location | Description |
|-----------|----------|-------------|
| **Master script** | `run_complete_pipeline.py` | Main pipeline orchestrator |
| **Session manager** | `scripts/utils/session_manager.py` | Session tracking utilities |
| **Individual scripts** | `scripts/17-21_*.py` | Pipeline step implementations |
| **Session outputs** | `results/sessions/{session-id}/` | All outputs for a specific run |
| **Input data** | `data/union/` | Union NER and primary resources |
| **Baseline data** | `data/baseline_2022/` | 2022 baseline inventory |
| **Visualizations** | `results/sessions/{session-id}/visualizations/` | PNG and HTML charts |
| **Documentation** | `*.md` files | All documentation files |

---

## Key Statistics from Recent Runs

### Latest Run (2025-11-24, Session: 2025-11-21-133840-fowoc)

**Resource Counts with URL Validation:**
- **Set A (Linguistic)**: 3,512 resources (2,324 in baseline [66.2%], 1,188 novel [33.8%])
  - URL coverage: 75.9%
- **Set B (SetFit)**: 1,538 resources (803 in baseline [52.2%], 735 novel [47.8%])
  - URL coverage: 95.8%
- **Set C (Union)**: 4,268 resources (2,754 in baseline [64.5%], 1,514 novel [35.5%])
  - URL coverage: 64.9%

**URL Quality Metrics:**
- CRITICAL: 2,511 URLs (61.6%)
- HIGH: 297 URLs (7.3%)
- Total high-quality: 2,808 URLs (68.9%)
- Live URLs: 82.3% (3,354/4,076)
- Wayback Machine rescue: 30.0% (1,224 URLs)

**Baseline Recovery Analysis:**
- Total 2022 baseline: 3,112 resources
- Recovered by Set C: 2,197 (70.6%)
- Missing: 918 (29.5%)
- **Root cause**: Classification false negatives (not publication date issues)
- False negative rate increases over time: 23-26% (2011-2014) → 32-41% (2019-2021)

**Performance:**
- URL scanning: 39 minutes (4,076 URLs)
- Full pipeline: ~45 minutes total

---

## Requirements

### Python Dependencies
```
pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.4.0  # For PNG visualizations
plotly>=5.0.0      # For HTML interactive charts
```

Install with:
```bash
pip install -r requirements.txt
```

### Input Data Requirements
1. **Union NER results**: `data/union/union_ner_results.csv`
2. **Primary resources**: `data/union/union_papers_with_primary_resources.csv`
3. **2022 Baseline inventory**: `data/baseline_2022/baseline_inventory.csv`
4. **2022 Baseline PMIDs**: `data/baseline_2022/baseline_pmids.txt`

---

## Additional Documentation

### Comprehensive Guides
- **[PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md)** (27KB) - Most comprehensive implementation guide
- **[results/sessions/README.md](../results/sessions/README.md)** (20KB) - Session directory structure and usage
- **[SCRIPTS_EXPLAINED.md](../SCRIPTS_EXPLAINED.md)** (24KB) - Detailed explanations of all scripts

### Quick References
- **[SCRIPT_GUIDE.md](../SCRIPT_GUIDE.md)** (14KB) - Quick reference for all scripts
- **[QUICK_REVIEW_SUMMARY.md](../QUICK_REVIEW_SUMMARY.md)** (3KB) - Quick review summary
- **[README.md](../README.md)** (4KB) - Project overview

### Reviews and History
- **[CODE_REVIEW_2025-11-20.md](../CODE_REVIEW_2025-11-20.md)** (39KB) - Code review results
- **[PIPELINE_EXECUTION_REVIEW_2025-11-20.md](../PIPELINE_EXECUTION_REVIEW_2025-11-20.md)** (26KB) - Execution review
- **[REVIEW_INDEX.md](../REVIEW_INDEX.md)** (9KB) - Index of all reviews
- **[COMMIT_SUMMARY.md](../COMMIT_SUMMARY.md)** (7KB) - Git commit history

### Project Management
- **[PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md)** (10KB) - Project overview and achievements
- **[PROGRESS.md](../PROGRESS.md)** (14KB) - Development progress tracker
- **[DELIVERABLES_MANIFEST.md](../DELIVERABLES_MANIFEST.md)** (15KB) - Complete deliverables list

---

## Getting Help

### Documentation Issues
If you can't find what you're looking for:
1. Check the [Documentation Index](#documentation-index) above
2. Search across all markdown files: `grep -r "your search term" *.md docs/*.md`
3. Check the master script docstring: `python run_complete_pipeline.py --help`

### Pipeline Errors
If you encounter errors during execution:
1. Check troubleshooting guide: [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md#troubleshooting)
2. Review session metadata: `cat results/sessions/{session-id}/session_metadata.json`
3. Check individual script logs in session directories

### Common Questions

**Q: How do I know which step failed?**
A: Check `results/sessions/{session-id}/session_metadata.json` - the `completed_steps` array shows which steps succeeded.

**Q: Can I run individual steps manually?**
A: Yes! Each script (17-21) can be run independently. See [SCRIPT_GUIDE.md](../SCRIPT_GUIDE.md) for usage.

**Q: Where are my visualizations?**
A: In `results/sessions/{session-id}/visualizations/` - both PNG and HTML formats.

**Q: How do I compare two runs?**
A: Each session is isolated. Compare the `baseline_comparison_stats.json` files from different session directories.

**Q: What if I only want baseline comparison without running the full pipeline?**
A: Use: `python run_complete_pipeline.py --from-step 6` (assumes steps 1-5 already completed)

---

## False Positive Analysis & Baseline Deduplication (2025-11-27)

### Overview

A comprehensive review of 10,529 pipeline outputs was completed to:
1. Identify false positives (papers incorrectly classified as bioresource announcements)
2. Deduplicate true positives against the 2022 baseline inventory
3. Generate a final list of truly novel bioresources

### Key Results

| Stage | Input | Output | Removed |
|-------|-------|--------|---------|
| False Positive Review | 10,529 papers | 5,545 true bioresources | 4,984 (47.3%) |
| Baseline Deduplication | 5,639 true positives | 2,594 novel resources | 3,045 (54.0%) |

### Algorithm Improvements

The improved fuzzy matching algorithm (v4) includes:

1. **Generic Domain Handling** - Reduced weight for `.ac.uk`, `.nih.gov`, `.edu.cn` domains
2. **Strict URL Normalization** - Handles `www`, trailing slash, `http/https` differences
3. **Multi-Signal Requirement** - HIGH confidence requires multiple matching signals
4. **One-to-One Mapping** - Each baseline matches at most one extracted resource
5. **Review Flags** - Suspicious matches flagged for manual review

### Documentation

| Document | Location | Description |
|----------|----------|-------------|
| False Positive Analysis README | [false_positive_analysis/README.md](../../false_positive_analysis/README.md) | Complete analysis documentation |
| Fuzzy Matching Module | [false_positive_analysis/improved_fuzzy_matching.py](../../false_positive_analysis/improved_fuzzy_matching.py) | Reusable matching algorithm |
| Deduplication Improvements | [unified_bioresource_pipeline/.../DEDUPLICATION_IMPROVEMENTS_2025-11-27.md](../../unified_bioresource_pipeline/scripts/phase7_deduplication/DEDUPLICATION_IMPROVEMENTS_2025-11-27.md) | Pipeline integration details |
| Algorithm Fixes | [false_positive_analysis/ALGORITHM_FIXES_REQUIRED.md](../../false_positive_analysis/ALGORITHM_FIXES_REQUIRED.md) | Code review findings |
| Consolidation Report | [false_positive_analysis/CONSOLIDATION_REPORT.md](../../false_positive_analysis/CONSOLIDATION_REPORT.md) | Chunk consolidation details |

### Final Output

The truly novel bioresources are in:
```
false_positive_analysis/consolidated_true_positives_novel_only_v4.csv (2,594 records)
```

---

## URL Recovery & Final Consolidation (2025-11-27)

### Overview

After identifying 2,594 novel bioresources, URL recovery was performed to maximize URL coverage:

1. **Recovered URLs from original chunks** - Joined back to source files on PMID
2. **Fulltext URL extraction** - Used EPMC API to extract URLs from full text
3. **Manual verification** - Reviewed low-confidence extractions

### Final Results

| Category | Count | % |
|----------|-------|---|
| **Total Novel Bioresources** | 2,594 | 100% |
| **With URLs** | 1,931 | 74.4% |
| └─ From original chunks | 1,486 | 57.3% |
| └─ From fulltext extraction | 445 | 17.2% |
| **No URL found** | 663 | 25.6% |

### Fulltext Extraction Quality

Of 1,108 papers processed via EPMC fulltext:
- **445 validated matches** (40.2%)
- 228 good title matches (live URLs)
- 202 high-score but dead URLs (likely correct)
- 15 low-score verified by manual review

### Output Files

| File | Location | Records |
|------|----------|---------|
| Final with URLs | `false_positive_analysis/FINAL_novel_bioresources_with_urls.csv` | 1,931 |
| Missing URLs | `false_positive_analysis/FINAL_novel_bioresources_NO_URL.csv` | 663 |
| Fulltext matches | `false_positive_analysis/fulltext_urls_FINAL_MATCHES.csv` | 445 |

### Documentation

| Document | Location | Description |
|----------|----------|-------------|
| URL Extraction Script | `false_positive_analysis/scripts/extract_urls_from_fulltext.py` | EPMC fulltext URL extraction |
| Extraction Review | `false_positive_analysis/review_extraction_summary.md` | Quality analysis of extractions |
| Critical False Positives | `false_positive_analysis/CRITICAL_FALSE_POSITIVES.md` | 29 reference URL issues |
| Category Files | `false_positive_analysis/category_*.csv` | Split by quality for review |

---

## Version History

| Date | Version | Changes | Documentation |
|------|---------|---------|---------------|
| 2025-11-27 | v2.3 | URL recovery, fulltext extraction, final consolidation | [false_positive_analysis/README.md](../../false_positive_analysis/README.md) |
| 2025-11-27 | v2.2 | False positive analysis, improved fuzzy matching, URL normalization | [false_positive_analysis/README.md](../../false_positive_analysis/README.md) |
| 2025-11-24 | v2.1 | Automated URL scanner, baseline investigation | [SESSION_SUMMARY_2025-11-24.md](../SESSION_SUMMARY_2025-11-24.md) |
| 2025-11-21 | v2.0 | Added session management, baseline comparison, visualizations | [PIPELINE_CHANGES_2025-11-21.md](../PIPELINE_CHANGES_2025-11-21.md) |
| 2025-11-20 | v1.1 | Code review and improvements | [CODE_REVIEW_2025-11-20.md](../CODE_REVIEW_2025-11-20.md) |
| 2025-11-18 | v1.0 | Initial pipeline implementation | [docs/PIPELINE_SYNTHESIS_SESSION_2025-11-18.md](PIPELINE_SYNTHESIS_SESSION_2025-11-18.md) |

---

**Last Updated**: 2025-11-27
**Maintainer**: Pipeline Synthesis Team
**License**: See LICENSE file in repository root
