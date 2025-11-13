# Technical Specifications

**Purpose**: Detailed technical specifications for the Biodata Inventory ML Pipeline
**Last Updated**: 2025-11-13

---

## Table of Contents
- [Model Architecture](#model-architecture)
- [Training Specifications](#training-specifications)
- [Data Format](#data-format)
- [Performance Metrics](#performance-metrics)
- [System Requirements](#system-requirements)
- [Hyperparameter Recommendations](#hyperparameter-recommendations)

---

## Model Architecture

### Base Model

**Name**: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500`

**Description**:
- RoBERTa-base architecture (125M parameters)
- Domain-adapted on biomedical literature (DAPT)
- Task-adapted on randomized controlled trials (TAPT)
- Specialized for biomedical text understanding

**Architecture Details**:
- Layers: 12 transformer layers
- Hidden size: 768
- Attention heads: 12
- Vocabulary: 50,265 tokens
- Max sequence length: 512 tokens

### V2 Models (Traditional Approach)

**Classification Model**:
```
RoBERTa Base (frozen/fine-tuned)
    ↓
[CLS] Token Pooling
    ↓
Dropout (p=0.2-0.3)
    ↓
Linear Layer (768 → 2)
    ↓
Softmax (bio-resource vs general paper)
```

**NER Model**:
```
RoBERTa Base (frozen/fine-tuned)
    ↓
Token-level embeddings
    ↓
Dropout (p=0.3)
    ↓
Linear Layer (768 → 5)
    ↓
Softmax (O, B-COM, I-COM, B-FUL, I-FUL)
```

### Phase 4 Multi-Task Model

**Architecture**:
```
RoBERTa Base (shared encoder)
    ├─→ Classification Head
    │   ├─ [CLS] Pooling
    │   ├─ Dropout
    │   └─ Linear (768 → 2)
    │
    └─→ NER Head
        ├─ Token embeddings
        ├─ Dropout
        └─ Linear (768 → 5)
```

**Multi-Task Learning**:
- Shared encoder learns both tasks simultaneously
- Task-specific heads for classification and NER
- Joint loss: `L = α * L_classif + β * L_ner`
- Default weights: α=0.5, β=0.5

---

## Training Specifications

### Sequence Length

| Task | Sequence Length | Rationale |
|------|----------------|-----------|
| Classification | 256 tokens | Captures title + abstract intro |
| NER | 512 tokens | Full context for entity extraction |

### Batch Size & Learning Rate

| Model | Batch Size | Learning Rate | Weight Decay |
|-------|-----------|---------------|--------------|
| Classification V2 | 16 | 1e-5 | 0.01 |
| NER V2 | 16 | 5e-6 | 0.01 |
| Phase 4 Multi-Task | 16 | 5e-6 | 0.01 |
| Phase 4 A100 (aggressive) | 128 | 8e-5 | 0.01 |

### Training Duration

| Model | Epochs | Time (T4) | Time (A100) |
|-------|--------|-----------|-------------|
| Classification V2 | 10-15 | ~2 hours | ~25 min |
| NER V2 | 15-20 | ~7 hours | ~60 min |
| Phase 4 Multi-Task | 15 | ~9.5 hours | ~1.5-2 hours |
| Phase 4 A100 (aggressive) | 15 | N/A | ~30-45 min |

### Optimizer Configuration

**AdamW Optimizer**:
```python
optimizer = AdamW(
    model.parameters(),
    lr=learning_rate,
    weight_decay=0.01,
    betas=(0.9, 0.999),
    eps=1e-8
)
```

**Learning Rate Scheduler**:
```python
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=warmup_steps,  # 10% of total steps
    num_training_steps=total_steps
)
```

### Early Stopping

- Patience: 3 epochs
- Monitor: Validation F1 score
- Mode: maximize
- Restore best weights

---

## Data Format

### BIO Tagging Scheme

| Tag | Description | Example |
|-----|-------------|---------|
| O | Outside (no entity) | "The", "is", "a" |
| B-COM | Beginning of compound name | "PDB" in "PDB database" |
| I-COM | Inside compound name | N/A (most compounds are single token) |
| B-FUL | Beginning of full name | "Protein" in "Protein Data Bank" |
| I-FUL | Inside full name | "Data", "Bank" in "Protein Data Bank" |

### Input Format

**Classification**:
```
[CLS] title [SEP] abstract [SEP]
```

**NER**:
```
[CLS] token1 token2 ... tokenN [SEP]
```

### Output Format

**Classification CSV**:
```csv
pmid,title,abstract,prediction,probability,confidence
12345678,Title text,Abstract text,1,0.987,high
```

**NER CSV**:
```csv
pmid,entity_text,entity_type,start_char,end_char,confidence
12345678,Protein Data Bank,FUL,45,63,0.95
12345678,PDB,COM,65,68,0.92
```

---

## Performance Metrics

### V2 Models (Validation Set)

**Classification**:
| Metric | Score |
|--------|-------|
| F1 | 0.898 |
| Precision | 0.930 |
| Recall | 0.869 |
| Accuracy | 0.913 |

**NER**:
| Metric | Overall | COM | FUL |
|--------|---------|-----|-----|
| F1 | 0.749 | 0.82 | 0.68 |
| Precision | 0.779 | 0.85 | 0.71 |
| Recall | 0.722 | 0.79 | 0.65 |

### V2 Models (Test Set)

**NER Entity-Level Performance**:
- F1: 0.6635 (66.35%)
- Precision: 0.69
- Recall: 0.64
- Test set: 63 papers with ground truth

### Phase 4 Multi-Task (Validation)

**Classification**:
- F1: 0.8586 (-4.38% vs V2)

**NER** (Token-level):
- F1: 0.9274 (+23.82% vs V2)

**Note**: Phase 4 has post-processing bug affecting entity-level extraction. Token-level metrics don't reflect actual production performance.

### spaCy Hybrid NER (Phase 3)

**Statistical NER**:
| Metric | Overall | COM | FUL |
|--------|---------|-----|-----|
| F1 | 0.7962 | 0.8432 | 0.5178 |
| Precision | 0.8394 | 0.8723 | 0.6538 |
| Recall | 0.7572 | 0.8161 | 0.4286 |

**Training Time**: 46 minutes on A100

---

## System Requirements

### Minimum Requirements

**Training**:
- GPU: NVIDIA T4 (16GB VRAM) or better
- RAM: 16GB system RAM
- Storage: 20GB free space
- Python: 3.11.9

**Inference**:
- GPU: Optional (can run on CPU)
- RAM: 8GB system RAM
- Storage: 5GB free space
- Python: 3.11.9

### Recommended Requirements

**Training**:
- GPU: NVIDIA A100 (40GB VRAM)
- RAM: 32GB system RAM
- Storage: 50GB free space (for experiments)

**Production Inference**:
- GPU: NVIDIA T4 or better
- RAM: 16GB system RAM
- Storage: 10GB free space

### Software Dependencies

**Core**:
- Python: 3.11.9
- PyTorch: 2.2.2
- Transformers: 4.35.0
- CUDA: 11.8+ (for GPU)

**Complete list**: See `requirements.txt`

### Performance Benchmarks

| Task | Papers | T4 Time | A100 Time | CPU Time |
|------|--------|---------|-----------|----------|
| Classification | 21,677 | ~18 min | ~5 min | ~2 hours |
| NER | 21,677 | ~36 min | ~10 min | ~4 hours |
| Full Pipeline | 21,677 | ~54 min | ~15 min | ~6 hours |

---

## Hyperparameter Recommendations

### Classification Model

**Standard Configuration**:
```python
config = {
    'epochs': 10-15,
    'batch_size': 16,
    'learning_rate': 1e-5,
    'weight_decay': 0.01,
    'dropout': 0.2-0.3,
    'warmup_ratio': 0.1,
    'max_seq_length': 256,
    'gradient_accumulation': 1
}
```

**When to Adjust**:
- **More data** (>2000 samples): Reduce epochs to 8-10
- **Less data** (<1000 samples): Increase dropout to 0.3-0.4
- **Overfitting**: Increase weight_decay to 0.02, increase dropout

### NER Model (Small Dataset)

**Standard Configuration**:
```python
config = {
    'epochs': 15-20,
    'batch_size': 16,
    'learning_rate': 5e-6,  # CRITICAL: Lower than classification
    'weight_decay': 0.01,
    'dropout': 0.3,
    'warmup_ratio': 0.1,
    'max_seq_length': 512,
    'gradient_accumulation': 1
}
```

**Critical Notes**:
- ⚠️ **Never use LR > 5e-6** for NER (causes instability)
- ⚠️ **Always use weight decay** (prevents overfitting on small dataset)
- Monitor train/val gap closely (should be <0.15)

### Phase 4 Multi-Task

**Standard Configuration**:
```python
config = {
    'epochs': 15,
    'batch_size': 16,
    'learning_rate': 5e-6,
    'weight_decay': 0.01,
    'dropout': 0.3,
    'warmup_ratio': 0.1,
    'max_seq_length': 512,
    'task_weights': {'classification': 0.5, 'ner': 0.5}
}
```

**A100 Aggressive Configuration**:
```python
config = {
    'epochs': 15,
    'batch_size': 128,        # 8x larger
    'learning_rate': 8e-5,    # Scale with batch size
    'weight_decay': 0.01,
    'dropout': 0.3,
    'warmup_ratio': 0.1,
    'max_seq_length': 512,
    'gradient_accumulation': 1
}
```

### spaCy Training Configuration

**A100 Optimized**:
```ini
[training]
max_epochs = 30
patience = 3000
eval_frequency = 500
batch_size = compounding(500, 1000, 1.001)

[training.optimizer]
learn_rate = 0.0001

[components.ner]
dropout = 0.3
```

---

## Validation Checklist

### Before Deploying New Models

**Performance Requirements**:
- [ ] NER test F1 > 0.70 (70%)
- [ ] Classification test F1 > 0.85 (85%)
- [ ] Test F1 within ±0.02 of validation F1
- [ ] Training showed steady improvement (no erratic spikes)
- [ ] Train/val gap < 0.15 (no severe overfitting)

**Quality Checks**:
- [ ] High-confidence predictions > 80% of total
- [ ] Baseline comparison > 75% agreement
- [ ] Manual review of 20 random predictions (all correct)
- [ ] Edge case testing (special characters, long abstracts, etc.)

**Technical Validation**:
- [ ] Cross-platform compatibility verified (local + Colab)
- [ ] Model loads without errors on CPU
- [ ] Inference speed acceptable (<5 min for 1000 papers)
- [ ] Memory usage reasonable (<10GB)

**Documentation**:
- [ ] Training config saved
- [ ] Performance metrics documented
- [ ] Known issues documented
- [ ] Usage examples provided

**Complete Checklist**: See [`docs/TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md)

---

## Data Split Strategy

### Standard Splits

**Classification**:
- Train: 70% (~1,145 samples)
- Val: 15% (~245 samples)
- Test: 15% (~245 samples)

**NER**:
- Train: 70% (~388 samples)
- Val: 15% (~83 samples)
- Test: 15% (~83 samples)

### Stratification

- Stratify by label distribution
- Ensure balanced positive/negative samples in each split
- For NER: Consider entity complexity distribution

---

## Model File Formats

### V2 Models (Recommended)

**Format**: Dictionary checkpoint
```python
checkpoint = {
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'epoch': epoch,
    'config': config_dict,
    'performance': metrics_dict
}
```

**Advantages**:
- Cross-platform compatible
- Forward compatible with PyTorch updates
- Can load on different devices (CPU/GPU)
- Smaller file size

### V1 Models (Deprecated)

**Format**: Full model object
```python
torch.save(model, path)  # DON'T USE
```

**Issues**:
- Not compatible with PyTorch 2.8+
- Platform-dependent
- Fails to load in different environments

---

**Document Location**: `docs/TECHNICAL_SPECIFICATIONS.md`
**Last Updated**: 2025-11-13
**Related**: See [`docs/TRAINING_CHECKLIST.md`](TRAINING_CHECKLIST.md) for complete training guide
