# Training Quality Checklist - Biodata Inventory Pipeline

**Created**: 2025-11-04
**Purpose**: Validation checklist and guidelines for training new models
**Audience**: AI agents and developers training models

---

## Recommended Hyperparameters

Based on October 2025 investigation, use these parameters for new model training:

### Classification Model
```yaml
epochs: 10-15
batch_size: 16
learning_rate: 1e-5           # Lower than default 2e-5
weight_decay: 0.01            # Add regularization
dropout: 0.2-0.3              # Increase if available
optimizer: AdamW
early_stopping: 3 epochs without improvement
max_sequence_length: 256
```

### NER Model (requires more care due to small dataset)
```yaml
epochs: 15-20
batch_size: 16
learning_rate: 5e-6           # Even lower for stability
weight_decay: 0.01
dropout: 0.3
optimizer: AdamW
early_stopping: 3 epochs without improvement
max_sequence_length: 512
```

---

## Pre-Training Validation

Before starting training, verify:

- [ ] **Environment activated**: `source biodata_modern_env/bin/activate`
- [ ] **Python 3.11.9**: `python --version`
- [ ] **PyTorch 2.2.2**: `python -c "import torch; print(torch.__version__)"`
- [ ] **Transformers 4.35.0**: `python -c "import transformers; print(transformers.__version__)"`
- [ ] **PYTHONPATH set**: `export PYTHONPATH="src:$PYTHONPATH"`
- [ ] **Data files exist**: Check `data/manual_classifications.csv` and `data/manual_ner_extraction.csv`
- [ ] **GPU available** (if training on GPU): `python -c "import torch; print(torch.cuda.is_available())"`
- [ ] **Sufficient disk space**: At least 5GB free

---

## Training Quality Validation Checklist

**CRITICAL**: Before deploying newly trained models to production, verify ALL items:

### Performance Metrics
- [ ] **NER test F1 > 0.70** (minimum acceptable)
- [ ] **Classification test F1 > 0.85** (minimum acceptable)
- [ ] **Test F1 matches validation F1 (±0.02)** (no overfitting to validation)

### Training Stability
- [ ] **Training stability**: Validation F1 shows steady improvement
- [ ] **No bouncing**: F1 doesn't decline significantly after peak
- [ ] **Low overfitting**: Train/val F1 gap < 0.15

### Technical Validation
- [ ] **Checkpoint format**: Uses dicts, not NamedTuples
- [ ] **Model loads correctly**: Test loading with `weights_only=True`
- [ ] **Parameter checksums**: Documented for model verification

### Production Readiness
- [ ] **Inference test**: Sample papers produce expected high-confidence results
- [ ] **High-confidence rate > 80%**: At threshold 0.978 for classification
- [ ] **Baseline comparison**: >75% overlap with validated inventory
- [ ] **Cross-platform test**: Verify predictions match on local and Colab

---

## During Training Monitoring

### Watch for These Red Flags

**🚨 STOP TRAINING IF**:
- Validation F1 bounces up and down erratically
- Validation loss increases for 3+ consecutive epochs
- Train/val F1 gap exceeds 0.20
- Memory errors or out-of-memory issues
- NaN losses or gradients

**⚠️ INVESTIGATE IF**:
- Validation F1 plateaus below target (0.70 NER, 0.85 classification)
- Training takes significantly longer than expected
- Loss decreases very slowly
- Model checkpoints grow unexpectedly large

---

## Post-Training Validation

### Immediate Tests (Within 5 minutes of training completion)

1. **Load Test**
   ```python
   import torch
   model = torch.load('path/to/model.pt', map_location='cpu', weights_only=True)
   print(f"Model loaded successfully: {type(model)}")
   ```

2. **Sample Inference Test**
   ```bash
   # Test on small sample (5-10 papers)
   python src/class_predict.py -c MODEL.pt -i sample.csv -o test_output/
   ```

3. **Check Output Statistics**
   - Count predictions: Should match input count
   - Check probability distribution: Should have reasonable spread
   - Verify high-confidence predictions: Should have >80% above threshold

### Full Validation (Within 1 hour)

1. **Test Set Evaluation**
   ```bash
   # Run full test set evaluation
   python src/class_predict.py -c MODEL.pt -i data/manual_classifications_test.csv -o test_eval/
   ```

2. **Baseline Comparison**
   - Run prediction on known-good dataset
   - Compare with previous baseline results
   - Check overlap percentage (should be >75%)

3. **Cross-Platform Test**
   - Test locally (PyTorch 2.2.2)
   - Test in Colab (PyTorch 2.8.0)
   - Verify predictions match (>99% agreement)

---

## Known Training Issues to Avoid

### ❌ DO NOT

1. **Use learning rate 2e-5 for NER**
   - Too high, causes training instability
   - Validation F1 will bounce erratically
   - Use 5e-6 instead

2. **Skip weight decay**
   - Causes overfitting on small NER dataset (554 samples)
   - Train/val gap will exceed 0.20
   - Always use weight_decay=0.01

3. **Train without early stopping**
   - Leads to overfitting after peak performance
   - Wastes compute time on declining performance
   - Use patience=3 epochs

4. **Ignore validation curve instability**
   - Sign of poor hyperparameter choices
   - Will result in unreliable production model
   - Stop and adjust hyperparameters

5. **Deploy without testing on sample data**
   - May have loading issues or prediction bugs
   - Always test inference before deployment

6. **Use checkpoints with NamedTuple objects**
   - Incompatible with PyTorch 2.8.0 (Colab)
   - Will cause prediction corruption
   - Use dict-only format

### ✅ DO

1. **Monitor validation curves during training**
   - Watch for steady improvement
   - Identify peak performance
   - Stop when performance plateaus

2. **Stop at first sign of sustained decline**
   - Save best checkpoint, not final checkpoint
   - Prevents overfitting

3. **Test models immediately after training**
   - Catch issues early
   - Validate performance claims

4. **Compare with baseline before deployment**
   - Ensure no regression
   - Verify improvement claims

5. **Document training parameters and results**
   - Store hyperparameters in session archive
   - Save training curves and metrics
   - Record any anomalies or issues

---

## Training Data Limitations

### Current Datasets

**Classification**:
- Training samples: 1,635
- Status: Adequate size for stable training
- Sensitivity: Low - consistent across runs

**NER**:
- Training samples: 554
- Status: Small - requires careful hyperparameters
- Sensitivity: High - sensitive to splits, learning rate, regularization

### Impact of Small NER Dataset

The small NER dataset (554 samples) is highly sensitive to:

1. **Learning Rate**
   - Must be low (5e-6 recommended)
   - Higher rates cause instability

2. **Regularization**
   - Weight decay essential (0.01)
   - Without it, severe overfitting occurs

3. **Data Splits**
   - Random seed affects performance significantly
   - Different splits can vary by 10% F1
   - Always use fixed seed for reproducibility

4. **Batch Size**
   - Small batches (8-16) work better
   - Large batches (32+) cause instability

### Long-term Recommendation

**Goal**: Expand NER dataset to 1,000-2,000 samples

**Benefits**:
- More robust training
- Less sensitive to hyperparameters
- Better generalization
- Easier to match baseline performance

**Methods**:
- Manual annotation of additional papers
- Data augmentation techniques
- Transfer learning from related tasks

---

## Emergency Procedures

### If Training Fails

1. **Check logs immediately**
   ```bash
   tail -100 logs/*/training.log
   ```

2. **Verify environment**
   ```bash
   python -c "import torch; print(torch.__version__)"
   which python
   ```

3. **Check data integrity**
   ```bash
   wc -l data/manual_classifications.csv
   head -5 data/manual_classifications.csv
   ```

4. **Test with smaller dataset**
   - Use test configuration
   - Verify pipeline works end-to-end

### If Model Performance is Poor

1. **Check validation curves**
   - Is training stable?
   - Is there overfitting?
   - Did training converge?

2. **Compare hyperparameters with recommendations**
   - Learning rate correct?
   - Weight decay enabled?
   - Early stopping configured?

3. **Test on known-good examples**
   - Use papers from training set
   - Verify model can learn

4. **Compare with baseline**
   - Is performance actually worse?
   - By how much?
   - On which metrics?

---

## Success Criteria Summary

A model is ready for production when:

✅ **Performance**: Meets minimum F1 thresholds (0.70 NER, 0.85 classification)
✅ **Stability**: Training showed steady improvement without bouncing
✅ **Validation**: Test performance matches validation performance
✅ **Generalization**: Train/val gap < 0.15
✅ **Compatibility**: Works on both local and Colab platforms
✅ **Baseline**: Matches or exceeds previous model performance
✅ **Inference**: Produces expected high-confidence predictions
✅ **Documentation**: Hyperparameters and metrics recorded

---

**Document Status**: ✅ Current
**Last Updated**: 2025-11-04
**Reference**: Based on October 2025 training quality investigation
