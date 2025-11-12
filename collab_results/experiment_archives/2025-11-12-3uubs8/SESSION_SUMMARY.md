
# spaCy Hybrid NER Training Session

**Session ID**: 2025-11-12-3uubs8
**Date**: 2025-11-12 19:59:23
**Mode**: FULL_TRAINING
**Training Time**: 46.0 minutes

## Configuration

### Model Architecture
- Type: spaCy TransitionBasedParser.v2
- Embeddings: Tok2Vec (MultiHashEmbed + MaxoutWindowEncoder)
- Hidden width: 128
- Dropout: 0.2
- Labels: COM (common names), FUL (full names)

### Training Configuration
- Max epochs: 50
- Patience: 10
- Batch size: 1000 (compounding)
- Learning rate: 0.0001->0.001->0.00001 (warmup_linear)
- Optimizer: Adam (β1=0.9, β2=0.999, L2=0.01)
- GPU: Enabled

### Training Data
- Train: 3,153 documents, 15,096 entities
- Dev: 676 documents, 3,175 entities
- Test: 676 documents, 3,101 entities
- Total: 21,372 annotations (distant supervision)

## Results

### Best Model Performance (Validation Set)
- **F1 Score**: 0.7962
- **Precision**: 0.8394
- **Recall**: 0.7572

### Expected vs Actual
- Expected F1: 0.65-0.75 (distant supervision baseline)
- Actual F1: 0.7962
- Status: ✅ Meets expectations

## Files

### Model Checkpoints
- `model-best/` - Best validation F1 model (use this for inference)
- `model-last/` - Final epoch model

### Evaluation
- `test_evaluation.txt` - Detailed test set evaluation
- `performance_summary.png` - Visualization

### Metadata
- `model-best/meta.json` - Training metrics and configuration

## Next Steps

1. **Review Results**: Check test_evaluation.txt for detailed metrics
2. **Load Model**: Use `nlp = spacy.load("/content/drive/MyDrive/inventory_2022/experiment_archives/2025-11-12-3uubs8/spacy_model/model-best")`
3. **Inference**: Apply model to new papers for bioresource extraction
4. **Phase Integration**: Combine with EntityRuler for hybrid NER (Phase 6)
5. **Document Findings**: Update experiment log

## Notes

- Training used distant supervision (automatic annotation from dictionary)
- Hyperparameters optimized based on code review recommendations
- Data quality validated: 0 overlaps, 97%+ coverage
- Model saved with full pipeline (tokenizer + ner)
- Ready for production inference

