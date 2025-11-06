# Comparison Scripts Index

## 📚 Overview

This directory contains scripts for comparing Phase 4 (new model) and V2 (old model) NER results.

## 🗂️ File Structure

### Core Scripts
```
01_preprocess_and_align.py          ✅ Load, clean, align datasets
02_entity_level_comparison.py       🚧 Coming next
03_paper_level_aggregation.py       🚧 Coming next
04_visualize_results.py              🚧 Coming next
```

### Utilities
```
utils/
├── __init__.py                     # Package initialization
├── data_loading.py                 # Load V2, Phase 4, test data
├── bpe_cleaning.py                 # BPE artifact detection/cleaning
├── entity_matching.py              # Entity matching strategies
└── metrics.py                      # Precision/recall/F1 calculation
```

### Documentation

#### Script 01 Documentation
```
SCRIPT_01_QUICK_REF.md              # ⚡ Quick reference (1 page)
QUICK_START_SCRIPT_01.md            # 🚀 Quick start guide (5 min read)
README_SCRIPT_01.md                 # 📖 Complete documentation (20 min read)
SCRIPT_01_IMPLEMENTATION_SUMMARY.md # 📊 Implementation details
```

#### General Documentation
```
00_INDEX.md                         # This file
CRITICAL_FIXES_APPLIED.md           # Critical bug fixes log
QUICK_REFERENCE_FIXES.md            # Quick fix reference
```

### Testing
```
test_01_preprocess.py               # Unit tests for Script 01
test_utils_import.py                # Utils import validation
test_critical_fixes.py              # Critical fixes validation
```

## 🚀 Quick Start

### New User? Start Here
1. **Quick Reference**: `SCRIPT_01_QUICK_REF.md` (30 seconds)
2. **Quick Start**: `QUICK_START_SCRIPT_01.md` (5 minutes)
3. **Run Script**: `python 01_preprocess_and_align.py`

### Need Details?
- **Full Docs**: `README_SCRIPT_01.md`
- **Implementation**: `SCRIPT_01_IMPLEMENTATION_SUMMARY.md`

## 📋 Script 01: Preprocess and Align

### Status: ✅ Complete and Tested

### What It Does
1. Loads V2 and Phase 4 NER results
2. Detects and cleans BPE artifacts
3. Aligns papers by ID
4. Generates statistics

### Quick Run
```bash
python 01_preprocess_and_align.py
```

### Outputs
- `../data/aligned_papers.csv`
- `../data/bpe_artifact_report.json`
- `../data/entity_counts.csv`

### Documentation
| File | Purpose | Read Time |
|------|---------|-----------|
| `SCRIPT_01_QUICK_REF.md` | One-page reference | 30 sec |
| `QUICK_START_SCRIPT_01.md` | Getting started | 5 min |
| `README_SCRIPT_01.md` | Complete guide | 20 min |
| `SCRIPT_01_IMPLEMENTATION_SUMMARY.md` | Technical details | 15 min |

### Testing
```bash
python test_01_preprocess.py
# Expected: ✅ All tests passed!
```

## 📋 Script 02: Entity Level Comparison

### Status: 🚧 Coming Next

### What It Will Do
1. Entity-level matching (exact, partial, fuzzy)
2. Calculate precision/recall/F1
3. Per-paper metrics
4. System comparison

### Planned Outputs
- `../data/entity_matches.csv`
- `../data/system_metrics.csv`
- `../data/per_paper_metrics.csv`

## 📋 Script 03: Paper Level Aggregation

### Status: 🚧 Coming Next

### What It Will Do
1. Aggregate entity metrics to paper level
2. Statistical testing
3. Error analysis
4. Category-based analysis

## 📋 Script 04: Visualize Results

### Status: 🚧 Coming Next

### What It Will Do
1. Generate comparison plots
2. Create heatmaps
3. Produce summary figures
4. Export publication-ready graphics

## 🛠️ Utilities Library

### data_loading.py
- `load_v2_results()`: Load V2 NER results
- `load_phase4_results()`: Load Phase 4 NER results
- `load_ner_test_split()`: Load ground truth
- `load_inventory()`: Load paper metadata
- `parse_entity_list()`: Parse entity strings

### bpe_cleaning.py
- `detect_bpe_artifacts()`: Detect BPE contamination
- `clean_bpe_entity()`: Clean single entity
- `clean_bpe_dataframe()`: Clean entire DataFrame
- `generate_bpe_report()`: Create contamination report

### entity_matching.py
- `exact_match()`: Exact string matching
- `partial_match()`: Substring matching
- `fuzzy_match()`: Fuzzy string matching
- `token_overlap()`: Token-based matching
- `match_entities()`: Unified matching function

### metrics.py
- `calculate_precision_recall_f1()`: Core metrics
- `entity_level_metrics()`: Entity-level evaluation
- `confusion_matrix()`: Build confusion matrix
- `bootstrap_confidence_interval()`: Statistical CI

## 📊 Workflow

```
01_preprocess_and_align.py
    ↓
    aligned_papers.csv
    ↓
02_entity_level_comparison.py
    ↓
    entity_matches.csv + system_metrics.csv
    ↓
03_paper_level_aggregation.py
    ↓
    paper_metrics.csv + statistical_tests.csv
    ↓
04_visualize_results.py
    ↓
    figures/*.png
```

## 🔧 Common Tasks

### Run Full Pipeline (When Complete)
```bash
python 01_preprocess_and_align.py
python 02_entity_level_comparison.py
python 03_paper_level_aggregation.py
python 04_visualize_results.py
```

### Run Tests
```bash
python test_01_preprocess.py
python test_utils_import.py
python test_critical_fixes.py
```

### Check Outputs
```bash
ls -lh ../data/
cat ../data/entity_counts.csv
python -m json.tool ../data/bpe_artifact_report.json
```

### View Logs
```bash
tail -50 01_preprocess_and_align.log
grep -i error *.log
```

## 🐛 Troubleshooting

### Import Errors
```bash
# Verify utils exist
ls -la utils/

# Test imports
python test_utils_import.py
```

### File Not Found
```bash
# Check input files
ls -lh ../../collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/
ls -lh ../../collab_results/experiment_archives/2025-11-05-poq5i4_phase4_2022_rerun/
```

### Memory Issues
```bash
# Check available memory
top

# Use skip flags for debugging
python 01_preprocess_and_align.py --skip-bpe-cleaning
```

## 📖 Reading Guide

### For Newcomers
1. Start with `SCRIPT_01_QUICK_REF.md`
2. Read `QUICK_START_SCRIPT_01.md`
3. Run `python test_01_preprocess.py`
4. Execute `python 01_preprocess_and_align.py`

### For Developers
1. Read `SCRIPT_01_IMPLEMENTATION_SUMMARY.md`
2. Review `README_SCRIPT_01.md`
3. Study `utils/` module code
4. Check `test_01_preprocess.py`

### For Users
1. Read `SCRIPT_01_QUICK_REF.md`
2. Run the script
3. Verify outputs
4. Proceed to next script

## 📞 Support

### Documentation Hierarchy
1. **Quick Ref** → 30 seconds, one command
2. **Quick Start** → 5 minutes, step-by-step
3. **README** → 20 minutes, comprehensive
4. **Implementation** → 15 minutes, technical details

### Help Resources
- Script help: `python 01_preprocess_and_align.py --help`
- Run tests: `python test_01_preprocess.py`
- Check logs: `tail -50 *.log`
- Documentation: This index file

## 📈 Progress Tracker

| Script | Status | Tests | Docs | Ready |
|--------|--------|-------|------|-------|
| 01_preprocess_and_align.py | ✅ | ✅ | ✅ | ✅ |
| 02_entity_level_comparison.py | 🚧 | - | - | - |
| 03_paper_level_aggregation.py | 🚧 | - | - | - |
| 04_visualize_results.py | 🚧 | - | - | - |

**Legend**: ✅ Complete | 🚧 In Progress | - Not Started

## 🎯 Project Goals

1. **Quantify Improvements**: Measure Phase 4 vs V2 performance
2. **Identify Issues**: Find BPE contamination and errors
3. **Statistical Testing**: Rigorous comparison with confidence intervals
4. **Publication Quality**: Generate publication-ready figures

## 📦 Dependencies

### Required Packages
```
pandas >= 1.3.0
tqdm >= 4.62.0
numpy >= 1.20.0 (for Script 02+)
matplotlib >= 3.4.0 (for Script 04)
seaborn >= 0.11.0 (for Script 04)
scipy >= 1.7.0 (for Script 03+)
```

### Python Version
- Python >= 3.8
- Tested on Python 3.11

## 🔄 Version History

### v1.0.0 (2025-11-05)
- ✅ Script 01 complete
- ✅ Full test coverage
- ✅ Comprehensive documentation
- ✅ Utils library complete

### Planned
- v1.1.0: Script 02 (entity comparison)
- v1.2.0: Script 03 (aggregation)
- v1.3.0: Script 04 (visualization)

## 📄 License

Internal research use only.

## 👤 Author

Claude Code - 2025-11-05

---

**Current Status**: Script 01 complete and tested ✅

**Next Step**: Implement Script 02 (entity-level comparison)

**Last Updated**: 2025-11-05
