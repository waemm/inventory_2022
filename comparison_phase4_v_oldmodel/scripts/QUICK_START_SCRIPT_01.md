# Quick Start: Script 01 - Preprocess and Align

## 🚀 TL;DR

```bash
cd /Users/warren/development/GBC/inventory_2022/comparison_phase4_v_oldmodel/scripts
python 01_preprocess_and_align.py
```

That's it! The script will:
1. Load V2 and Phase 4 NER results
2. Clean BPE artifacts
3. Align papers by ID
4. Save outputs to `../data/`

## 📋 Prerequisites

### Required Files (Auto-detected)
- ✅ V2 results: `collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/ner_results.csv`
- ✅ Phase 4 results: `experiment_archives/2025-11-05-poq5i4_phase4_2022_rerun/ner_results.csv`
- ✅ Test split: `data/ner_splits_full/test_ner.csv`
- ✅ Inventory: `data/final_inventory_2022.csv`

### Python Environment
```bash
# Make sure you're in the correct environment
source activate biodata_modern_env  # or your environment name

# Required packages (should already be installed)
pip install pandas tqdm
```

## 🏃 Run Commands

### Standard Run (Recommended)
```bash
cd /Users/warren/development/GBC/inventory_2022/comparison_phase4_v_oldmodel/scripts
python 01_preprocess_and_align.py
```

### With Verbose Output
```bash
python 01_preprocess_and_align.py --verbose
```

### Custom Output Directory
```bash
python 01_preprocess_and_align.py --output-dir /path/to/custom/output
```

## 📊 Expected Output

### Files Created in `../data/`:
1. **aligned_papers.csv** (~50 MB)
   - All papers with V2, Phase 4, and ground truth entities
   - Ready for comparison analysis

2. **bpe_artifact_report.json** (~1 KB)
   - BPE contamination statistics
   - Example artifacts

3. **entity_counts.csv** (~2 KB)
   - Entity distribution statistics
   - Per-system counts

### Console Output:
```
================================================================================
Phase 4 vs V2 NER Comparison: Preprocessing and Alignment
================================================================================

STEP 1: Loading Datasets
  ✓ Loaded 20,805 V2 results
  ✓ Loaded 20,805 Phase 4 results
  ✓ Loaded 400 test samples
  ✓ Loaded 20,805 papers in inventory

STEP 2: Parsing Entity Columns
  ✓ Parsed all entity columns

STEP 3: Detecting and Cleaning BPE Artifacts
  ✓ BPE cleaning complete
    - Common name contamination: 87.6% of papers
    - Full name contamination: 6.0% of papers

STEP 4: Aligning Papers by ID
  ✓ Alignment complete: 20,805 total papers

STEP 5: Generating Entity Count Statistics
  ✓ Entity count statistics calculated

STEP 6: Saving Output Files
  ✓ Saved 20,805 papers to: ../data/aligned_papers.csv
  ✓ Saved BPE report to: ../data/bpe_artifact_report.json
  ✓ Saved entity statistics to: ../data/entity_counts.csv

✅ SUCCESS: All processing completed successfully
```

## ⏱️ Expected Runtime

- **Small test**: 1-2 seconds (100 papers)
- **Full dataset**: 20-30 seconds (20,805 papers)

## 🔍 Verify Results

### Check Output Files
```bash
# List generated files
ls -lh ../data/

# Preview aligned papers
head -5 ../data/aligned_papers.csv

# View BPE report
cat ../data/bpe_artifact_report.json

# View entity statistics
cat ../data/entity_counts.csv
```

### Check Logs
```bash
# View execution log
tail -50 01_preprocess_and_align.log

# Search for errors
grep -i error 01_preprocess_and_align.log
```

## 🐛 Troubleshooting

### Error: FileNotFoundError
```bash
# Verify input files exist
ls -lh ../../collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/ner_results.csv
ls -lh ../../collab_results/experiment_archives/2025-11-05-poq5i4_phase4_2022_rerun/ner_results.csv
```

**Fix**: Update paths in script or use `--v2-path` and `--phase4-path` flags

### Error: Module not found
```bash
# Check Python environment
which python
python --version

# Reinstall dependencies
pip install pandas tqdm
```

### Error: Memory issue
```bash
# Monitor memory usage
top

# Close other applications
# Consider processing in chunks (contact developer)
```

## 📈 Next Steps

After successful completion:

1. **Review Outputs**
   ```bash
   # Quick preview
   head -20 ../data/aligned_papers.csv

   # Count papers
   wc -l ../data/aligned_papers.csv
   ```

2. **Run Entity Comparison** (Script 02)
   ```bash
   python 02_entity_level_comparison.py
   ```

3. **Check BPE Contamination**
   ```bash
   # View contamination report
   python -m json.tool ../data/bpe_artifact_report.json | less
   ```

## 💡 Pro Tips

### Quick Test Run
```bash
# Test on small subset (modify script temporarily)
python 01_preprocess_and_align.py --skip-bpe-cleaning  # Faster
```

### Debug Mode
```bash
# Enable verbose logging and check each step
python 01_preprocess_and_align.py --verbose 2>&1 | tee debug.log
```

### Re-run with Different Data
```bash
# Use custom Phase 4 results
python 01_preprocess_and_align.py \
    --phase4-path ../../experiment_archives/2025-11-05-XXXXX_phase4_2022_rerun/ner_results.csv
```

## 📞 Need Help?

### Common Issues

1. **Wrong file paths**: Check experiment IDs in directory names
2. **Import errors**: Verify utils module is in scripts directory
3. **Data format issues**: Check CSV headers match expected format

### Getting Support

1. Check the detailed README: `README_SCRIPT_01.md`
2. Review the log file: `01_preprocess_and_align.log`
3. Contact the developer with error messages

## ✅ Success Checklist

- [ ] Script runs without errors
- [ ] `aligned_papers.csv` created (~50 MB)
- [ ] `bpe_artifact_report.json` created
- [ ] `entity_counts.csv` created
- [ ] Log shows "SUCCESS" message
- [ ] Ready to run Script 02

---

**Ready to continue?** → `python 02_entity_level_comparison.py`
