# Phase 4: Multi-Task Learning MVP - Quick Start Guide

**Goal**: Improve NER F1 from 0.676 → ≥0.749 through multi-task learning with metadata

---

## Prerequisites

1. **Phase 1-3 Complete**: Augmented training data with metadata features
2. **Python Environment**: Python 3.8+ with PyTorch and Transformers
3. **GPU Recommended**: For faster training (CPU works but slower)

### Install Dependencies

```bash
pip install torch transformers scikit-learn pyyaml tqdm pandas numpy
```

---

## Quick Start (TEST_MODE - 5 minutes)

### Step 1: Verify Setup

```bash
python test_multitask_setup.py
```

**Expected Output**:
```
✓ TEST 1 PASSED - Data Loading
✓ TEST 2 PASSED - Model Architecture
✓ TEST 3 PASSED - Loss Computation
✓ TEST 4 PASSED - Gradient Flow
✓ TEST 5 PASSED - Metrics Tracking
✓ TEST 6 PASSED - Short Training Run

Total: 6/6 tests passed
✓ ALL TESTS PASSED - Ready for full training!
```

### Step 2: Review TEST_MODE Results

```bash
cat outputs/test_multitask/training.log
```

**What to Look For**:
- Losses decreasing over 5 epochs
- No NaN or Inf values
- Both classification and NER tasks showing learning
- Gradient conflicts < 20%

---

## Full Training (30-60 minutes on GPU)

### Step 1: Configure Training

Edit `config/multitask_config.yaml`:

```yaml
training:
  test_mode: false  # Change to false
  epochs: 30
  batch_size: 16
```

### Step 2: Start Training

```bash
python src/train_multitask.py \
  --config config/multitask_config.yaml \
  --output_dir outputs/multitask_full
```

**Monitor Training**:
```bash
# Watch log in real-time
tail -f outputs/multitask_full/training.log
```

### Step 3: Evaluate Results

```bash
python src/evaluate_multitask.py \
  --checkpoint outputs/multitask_full/checkpoint_best_combined.pt \
  --data_classif data/augmented/classif_train_with_metadata.csv \
  --data_ner data/augmented/ner_train_with_metadata.csv \
  --output outputs/multitask_full/evaluation_report.txt

# View report
cat outputs/multitask_full/evaluation_report.txt
```

---

## Understanding the Output

### Training Checkpoints

Three checkpoints are saved:

1. **`checkpoint_best_classification.pt`**: Best classification F1
2. **`checkpoint_best_ner.pt`**: Best NER F1
3. **`checkpoint_best_combined.pt`**: Best combined F1 (use this)

### Training Metrics

**File**: `outputs/multitask_full/training_history.json`

```json
{
  "train_loss": [2.34, 1.89, 1.45, ...],
  "train_classif_loss": [0.52, 0.41, 0.33, ...],
  "train_ner_loss": [1.67, 1.34, 1.02, ...],
  "val_classif_f1": [0.850, 0.875, 0.890, ...],
  "val_ner_f1": [0.600, 0.650, 0.705, ...]
}
```

### Evaluation Report

**File**: `outputs/multitask_full/evaluation_report.txt`

```
CLASSIFICATION TASK
  F1 Score:       0.8980
  Precision:      0.9120
  Recall:         0.8845

NER TASK
  F1 Score (Macro):  0.7520
  F1 Score (Micro):  0.8650
  Precision (Macro): 0.7680
  Recall (Macro):    0.7365

COMBINED METRICS
  Average F1:          0.8250
  Weighted F1 (0.3/0.7): 0.7958
```

---

## Success Criteria

### Minimum Requirements

- [ ] Training completes without errors
- [ ] Both tasks show learning (loss decreasing)
- [ ] Gradient conflicts < 20% of batches
- [ ] No severe negative transfer (F1 ≥ 0.85 × baseline)

### Target Performance

- [ ] **Classification F1 ≥ 0.898** (maintain baseline)
- [ ] **NER F1 ≥ 0.749** (reach target)
- [ ] **Combined F1 ≥ 0.824** (weighted average)

---

## Troubleshooting

### Issue: Out of Memory (OOM)

**Solution**: Reduce batch size

```yaml
training:
  batch_size: 8  # Reduce from 16
```

### Issue: Training Too Slow

**Solution**: Enable mixed precision (requires GPU)

```yaml
hardware:
  mixed_precision: true
```

### Issue: NER Not Improving

**Solutions**:
1. Increase NER loss weight: `lambda_ner: 0.8`
2. Reduce classification weight: `lambda_classification: 0.2`
3. Check NER data quality and labels

### Issue: High Gradient Conflicts

**Solutions**:
1. Reduce learning rate: `learning_rate: 1.0e-5`
2. Increase warmup: `warmup_steps: 1000`
3. Try task scheduling (advanced)

### Issue: Negative Transfer Detected

**Solutions**:
1. Adjust loss weights
2. Use separate optimizers per task
3. Add gradient projection (advanced)
4. Fall back to single-task training

---

## File Structure

```
inventory_2022/
├── config/
│   └── multitask_config.yaml       # Configuration
├── src/
│   ├── models/
│   │   └── multitask_model.py      # Model architecture
│   ├── data/
│   │   └── multitask_dataloader.py # Data loading
│   ├── train_multitask.py          # Training script
│   └── evaluate_multitask.py       # Evaluation script
├── data/
│   └── augmented/                  # Phase 3 output
│       ├── classif_train_with_metadata.csv
│       └── ner_train_with_metadata.csv
├── outputs/
│   └── multitask_full/             # Training output
│       ├── checkpoint_best_*.pt
│       ├── training.log
│       └── training_history.json
├── test_multitask_setup.py         # Verification script
└── README_PHASE4.md                # This file
```

---

## Configuration Reference

### Loss Weights

```yaml
lambda_classification: 0.3  # Classification weight
lambda_ner: 0.7             # NER weight (higher priority)
lambda_auxiliary: 0.1       # Metadata prediction weight
```

**Guidance**:
- Sum doesn't need to equal 1.0
- Higher weight = more gradient updates for that task
- Start with 0.3/0.7/0.1, adjust based on results

### Learning Rate

```yaml
learning_rate: 2.0e-5  # Default for RoBERTa fine-tuning
```

**Guidance**:
- 2e-5: Standard for transformer fine-tuning
- 1e-5: More stable but slower
- 5e-5: Faster but risk of instability

### Early Stopping

```yaml
patience: 10          # Epochs without improvement
min_delta: 0.001      # Minimum improvement threshold
monitor: combined_f1  # Metric to monitor
```

---

## Next Steps

### If TEST_MODE Succeeds ✓

1. Run full training (30 epochs)
2. Evaluate on held-out test set
3. Compare to single-task baselines
4. Analyze per-class performance

### If Target Performance Met ✓

1. Integrate into Colab pipeline
2. Run on 2022 inventory dataset
3. Create production deployment
4. Document in main README

### If Issues Persist ✗

1. Review training logs for errors
2. Check gradient conflicts and negative transfer
3. Try hyperparameter adjustments
4. Consider Option 1 (Expanded Training Data) instead

---

## Advanced Options (Post-MVP)

### Custom Loss Weights

```python
# In train_multitask.py
config['training']['lambda_classification'] = 0.25
config['training']['lambda_ner'] = 0.75
```

### Separate Learning Rates

```python
# In MultiTaskTrainer._create_optimizer()
optimizer = AdamW([
    {'params': model.encoder.parameters(), 'lr': 1e-5},
    {'params': model.classification_head.parameters(), 'lr': 2e-5},
    {'params': model.ner_head.parameters(), 'lr': 3e-5}
])
```

### Gradient Projection (if conflicts persist)

```python
# Add PCGrad implementation
from pcgrad import PCGrad
optimizer = PCGrad(optimizer)
```

---

## Support

**Documentation**:
- Full implementation details: `docs/PHASE4_IMPLEMENTATION_SUMMARY.md`
- Architecture diagrams: `docs/research/multitask_architecture.md`
- Troubleshooting guide: `docs/TROUBLESHOOTING.md`

**Common Issues**:
- Data loading errors → Check Phase 3 output exists
- Model errors → Run `test_multitask_setup.py`
- Training errors → Check GPU memory and batch size
- Poor performance → Adjust loss weights

---

## Summary

**Phase 4 provides**:
- Multi-task model with metadata integration
- Automatic data balancing (NER oversampling)
- Gradient monitoring and conflict detection
- Task-specific evaluation and checkpointing
- TEST_MODE for quick validation

**Time Investment**:
- Setup verification: 5 minutes
- TEST_MODE training: 5 minutes
- Full training: 30-60 minutes
- Evaluation: 2 minutes

**Total**: ~1 hour to validate approach and see results

Good luck! 🚀
