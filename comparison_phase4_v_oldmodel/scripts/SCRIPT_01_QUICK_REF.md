# Script 01: Quick Reference Card

## ⚡ One-Line Run
```bash
cd /Users/warren/development/GBC/inventory_2022/comparison_phase4_v_oldmodel/scripts && python 01_preprocess_and_align.py
```

## 📋 What It Does
1. Loads V2 & Phase 4 NER results
2. Cleans BPE artifacts (Ġ markers)
3. Aligns papers by ID
4. Saves 3 output files

## 🎯 Key Outputs
```
../data/aligned_papers.csv          # Main unified dataset
../data/bpe_artifact_report.json    # Contamination stats
../data/entity_counts.csv           # Distribution stats
```

## 🔧 Common Commands

### Standard
```bash
python 01_preprocess_and_align.py
```

### Verbose
```bash
python 01_preprocess_and_align.py --verbose
```

### Custom Output
```bash
python 01_preprocess_and_align.py --output-dir /custom/path
```

### Skip BPE Cleaning
```bash
python 01_preprocess_and_align.py --skip-bpe-cleaning
```

## ✅ Verify Success
```bash
# Check outputs exist
ls -lh ../data/aligned_papers.csv

# Count papers (should be 20,806 including header)
wc -l ../data/aligned_papers.csv

# Check log for success
grep "SUCCESS" 01_preprocess_and_align.log
```

## 🧪 Test First
```bash
python test_01_preprocess.py
# Should show: "✅ All tests passed!"
```

## 🐛 Troubleshoot
```bash
# View recent errors
tail -50 01_preprocess_and_align.log | grep -i error

# Check input files exist
ls -lh ../../collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/ner_results.csv
ls -lh ../../collab_results/experiment_archives/2025-11-05-poq5i4_phase4_2022_rerun/ner_results.csv
```

## 📊 Expected Stats
- **Papers**: 20,805
- **V2 Coverage**: 100%
- **Phase 4 Coverage**: 100%
- **Ground Truth**: 400 papers
- **BPE Contamination**: ~88% (common), ~6% (full)
- **Runtime**: ~30 seconds

## 🔑 Key Columns in Output
- `paper_id`: PubMed ID
- `true_com`, `true_ful`: Ground truth
- `v2_com`, `v2_ful`: V2 predictions
- `p4_com_clean`, `p4_ful_clean`: Phase 4 cleaned

## 📚 More Info
- Detailed docs: `README_SCRIPT_01.md`
- Quick start: `QUICK_START_SCRIPT_01.md`
- Implementation: `SCRIPT_01_IMPLEMENTATION_SUMMARY.md`

## ➡️ Next Step
```bash
python 02_entity_level_comparison.py
```

---
**Status**: ✅ Ready to use
**Runtime**: ~30 sec
**Output**: ~50 MB
