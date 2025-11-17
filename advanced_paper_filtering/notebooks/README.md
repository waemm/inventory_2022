# SetFit Training Notebook for Google Colab

## Quick Start

1. **Upload to Google Drive**:
   ```bash
   python /Users/warren/development/GBC/inventory_2022/upload_to_drive.py \
     /Users/warren/development/GBC/inventory_2022/advanced_paper_filtering/notebooks/setfit_training_colab.ipynb
   ```

2. **Open in Google Colab**:
   - Navigate to Google Drive: `inventory_2022/advanced_paper_filtering/notebooks/`
   - Right-click `setfit_training_colab.ipynb` → Open with → Google Colaboratory

3. **Enable GPU** (CRITICAL for speed):
   - In Colab: Runtime → Change runtime type → Hardware accelerator → T4 GPU
   - **Without GPU**: 3-5 hours training time
   - **With GPU**: 10-20 minutes training time

4. **Run All Cells**:
   - Runtime → Run all
   - The notebook will:
     - Mount Google Drive
     - Install SetFit
     - Load training data from Drive
     - Train model on GPU
     - Classify medium-score papers
     - Save results back to Drive

## What This Notebook Does

### Input Data (from Google Drive)
- `data/results/high_score_papers.csv` - Papers with linguistic score ≥7 (positive examples)
- `data/results/low_score_papers.csv` - Papers with linguistic score ≤-2 (negative examples)
- `data/results/medium_score_papers.csv` - Papers with score 0-2 (to classify)

### Training Process
1. Samples 20 positive + 20 negative examples
2. Trains SetFit model on title+abstract embeddings
3. Uses sentence-transformers/all-mpnet-base-v2 base model
4. Few-shot learning (learns from 40 examples)

### Output (saved to Google Drive)
- `models/{SESSION_ID}/setfit_introduction_classifier/` - Trained model
- `models/{SESSION_ID}/setfit_classified_introductions.csv` - Classified introductions
- `models/{SESSION_ID}/setfit_classified_usage.csv` - Classified usage papers
- `models/{SESSION_ID}/training_data.csv` - Training examples used
- `models/{SESSION_ID}/training_summary.json` - Training metrics

## Comparison: SetFit vs Logistic Regression

| Feature | Logistic Regression | SetFit |
|---------|-------------------|--------|
| **Training Time (CPU)** | <1 second | 3-5 hours |
| **Training Time (GPU)** | <1 second | 10-20 minutes |
| **Training Data** | 70 examples (35+/35-) | 40 examples (20+/20-) |
| **Features** | 7 linguistic features | Title+abstract embeddings |
| **Model Type** | Simple linear | Deep learning (sentence transformers) |
| **Accuracy** | 100% (training) | TBD (to compare) |
| **Introductions Found** | 3 from 15,889 | TBD (to compare) |
| **Interpretability** | High (clear weights) | Low (black box) |
| **GPU Required** | No | Yes (for speed) |

## Expected Results

Based on logistic regression results, SetFit should:
- Find 5-20 borderline introductions (vs 3 for logistic regression)
- Have similar or slightly better accuracy on borderline cases
- Capture more semantic patterns in abstracts

**If SetFit finds significantly fewer**: The logistic regression features already captured most patterns

**If SetFit finds significantly more**: Deep learning found semantic patterns missed by linguistic features

## Structure (Based on PyCaret Template)

The notebook follows the same structure as `pycaret_metadata_training_v3.ipynb`:

1. **Cell 0-1**: Header and description
2. **Cell 2-5**: Session setup and Drive mounting
3. **Cell 6**: System information (GPU check)
4. **Cell 7**: Install dependencies
5. **Cell 8**: Import libraries
6. **Cell 9**: Load and prepare data (STEP 1)
7. **Cell 10**: Initialize model (STEP 2)
8. **Cell 11**: Prepare dataset and trainer (STEP 3)
9. **Cell 12**: Train model (STEP 4) ⏰
10. **Cell 13**: Test on examples (STEP 5)
11. **Cell 14**: Save model (STEP 6)
12. **Cell 15**: Classify medium papers (STEP 7) ⏰
13. **Cell 16**: Export summary (STEP 8)
14. **Cell 17**: Verify files saved to Drive (STEP 9) ✅
15. **Cell 18**: Completion summary

## Troubleshooting

### "No GPU detected"
- Go to Runtime → Change runtime type → T4 GPU
- Restart runtime and run all cells again

### "File not found" errors
- Check that all data files exist in Google Drive:
  - `inventory_2022/advanced_paper_filtering/data/results/high_score_papers.csv`
  - `inventory_2022/advanced_paper_filtering/data/results/low_score_papers.csv`
  - `inventory_2022/advanced_paper_filtering/data/results/medium_score_papers.csv`

### Out of memory
- Reduce BATCH_SIZE from 16 to 8 (Cell 4)
- Or use smaller base model (change BASE_MODEL in Cell 4)

### Slow training even with GPU
- Check GPU is actually being used: Cell 6 should show "CUDA available: True"
- If not, restart runtime and enable GPU again

## Download Results

After training completes, download results from Google Drive:

```bash
# Download entire session results
rclone copy gdrive:inventory_2022/advanced_paper_filtering/models/SESSION_ID /local/path

# Or use the download script
python download_from_drive.py --archive-type models
```

## Next Steps After Training

1. **Compare with Logistic Regression**:
   - Load both `ml_classified_introductions.csv` (logistic) and `setfit_classified_introductions.csv`
   - Check overlap and differences
   - Manual review of disagreements

2. **Manual Validation**:
   - Sample 10-20 papers from SetFit introductions
   - Verify they are actual resource introductions
   - Calculate precision

3. **Final Decision**:
   - If SetFit precision is similar but finds more papers: Use SetFit
   - If SetFit precision is lower: Stick with logistic regression
   - If similar results: Use logistic regression (simpler, faster)

---

**Created**: 2025-11-17
**Purpose**: GPU-accelerated SetFit training for paper classification
**Based on**: pycaret_metadata_training_v3.ipynb structure
**Runtime**: 10-20 minutes on Colab T4 GPU
