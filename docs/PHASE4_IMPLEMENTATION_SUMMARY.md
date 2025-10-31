# Phase 4 Implementation Summary: Multi-Task Learning MVP

**Date**: 2025-10-31
**Implementation**: Multi-Task Learning with Metadata Integration
**Goal**: Improve NER F1 from 0.676 → ≥0.749 through joint training with classification

---

## Overview

This document summarizes the Phase 4 Multi-Task Learning MVP implementation for biomedical resource classification and Named Entity Recognition (NER).

## Architecture Decision

**Approach**: Hard parameter sharing with metadata integration

### Key Components

1. **Shared Encoder**: RoBERTa-base (can load from TAPT checkpoint)
2. **Metadata Integration**: 34 features projected to 768 dims
3. **Post-Encoder Fusion**: Concatenate text CLS + metadata projection
4. **Task-Specific Heads**:
   - Classification head (binary, dropout=0.3)
   - NER head (BIO tagging, dropout=0.1)
5. **Auxiliary Heads**: Metadata prediction for regularization

### Metadata Features (34 total)

**Boolean Features (10)**:
- `hasDbCrossReferences`, `hasData`, `hasSuppl`, `isOpenAccess`
- `inPMC`, `inEPMC`, `hasPDF`, `hasBook`
- `is_research_article`, `is_review_article`

**Numerical Features (4)**:
- `log_citations`, `years_since_pub`
- `citedByCount`, `pubYear`

**Categorical Features (2)**:
- `meshTerms_missing`, `keywords_missing`

**TF-IDF Embeddings (12)**:
- `mesh_tfidf_0` to `mesh_tfidf_6` (7 components)
- `keyword_tfidf_0` to `keyword_tfidf_4` (5 components)

---

## Implementation Files

### 1. Model Architecture
**File**: `src/models/multitask_model.py`

**Classes**:
- `MetadataProjection`: Projects 34 features → 768 dims
- `FusionLayer`: Fuses text + metadata embeddings
- `ClassificationHead`: Binary classification (dropout=0.3)
- `NERHead`: BIO tagging with metadata enhancement (dropout=0.1)
- `AuxiliaryMetadataHeads`: Predicts metadata for regularization
- `BiomedicalMultiTaskModel`: Main multi-task model

**Key Features**:
- Metadata projection with Xavier initialization (gain=0.1)
- Layer normalization for stability
- Metadata broadcasting to all tokens for NER
- Separate parameter groups for flexible optimization

### 2. Data Loading
**File**: `src/data/multitask_dataloader.py`

**Classes**:
- `MultiTaskDataset`: Combined classification + NER dataset

**Key Features**:
- Loads augmented data from Phase 3
- Oversamples NER (553 → 1634) to balance classes
- Creates mixed batches with task indicators
- Proper BIO label creation for NER
- Handles metadata extraction and normalization

**Data Statistics**:
- Classification: 1,634 samples (50 in TEST_MODE)
- NER: 553 samples → oversampled to 1,634 (50 in TEST_MODE)
- Total training samples: 3,268 (100 in TEST_MODE)

### 3. Training Script
**File**: `src/train_multitask.py`

**Classes**:
- `MultiTaskTrainer`: Handles multi-task training loop

**Key Features**:
- Fixed loss weighting: λ₁=0.3 (classif), λ₂=0.7 (NER), λ₃=0.1 (aux)
- Per-task metric tracking
- Gradient conflict detection (cosine similarity)
- Task-specific early stopping
- Checkpoint saving (best_classification, best_ner, best_combined)
- TEST_MODE support for quick validation

**Training Loop**:
1. Forward pass through shared encoder
2. Project and fuse metadata
3. Task-specific loss computation
4. Auxiliary loss for regularization
5. Combined loss = λ₁*L_classif + λ₂*L_ner + λ₃*L_aux
6. Gradient clipping (max_norm=1.0)
7. Optimizer step with learning rate scheduling

### 4. Evaluation Utilities
**File**: `src/evaluate_multitask.py`

**Classes**:
- `MultiTaskEvaluator`: Comprehensive evaluation

**Functions**:
- `evaluate_classification()`: Classification metrics
- `evaluate_ner()`: NER metrics (macro/micro F1)
- `compare_to_baseline()`: MTL vs single-task comparison
- `detect_negative_transfer()`: Alert if MTL hurts performance
- `generate_evaluation_report()`: Formatted report generation

### 5. Configuration
**File**: `config/multitask_config.yaml`

**Key Settings**:
- Model: `roberta-base`, 34 metadata features
- Loss weights: 0.3/0.7/0.1 (classif/NER/aux)
- Learning rate: 2e-5, warmup: 500 steps
- Early stopping: patience=10
- TEST_MODE: 50 samples per task, 5 epochs

### 6. Verification Script
**File**: `test_multitask_setup.py`

**Tests**:
1. Data loading and metadata extraction
2. Model architecture and forward pass
3. Loss computation correctness
4. Gradient flow to shared encoder
5. Metrics tracking
6. Short training run (5 epochs)

---

## Training Strategy

### Loss Function

```
L_total = λ₁ * L_classification + λ₂ * L_NER + λ₃ * L_auxiliary

where:
  L_classification = CrossEntropyLoss(logits, labels)
  L_NER = CrossEntropyLoss(logits, labels, ignore_index=-100)
  L_auxiliary = BCE(boolean_pred, boolean_target) + MSE(numerical_pred, numerical_target)

  λ₁ = 0.3  (classification weight)
  λ₂ = 0.7  (NER weight - higher priority)
  λ₃ = 0.1  (auxiliary weight - regularization)
```

### Data Balancing

- **NER Oversampling**: Repeat NER samples to match classification count
- **Mixed Batches**: 50% classification, 50% NER samples per batch
- **Task-Specific Max Length**: 256 (classif), 512 (NER)

### Gradient Management

- **Shared Encoder**: All tasks backpropagate through same encoder
- **Gradient Clipping**: max_norm=1.0 to prevent exploding gradients
- **Conflict Detection**: Monitor cosine similarity between task gradients
- **Alert Threshold**: Warn if similarity < 0 (conflicting gradients)

### Early Stopping

- **Monitor**: Combined F1 = 0.5 * F1_classif + 0.5 * F1_ner
- **Patience**: 10 epochs without improvement
- **Negative Transfer**: Stop if F1 < 0.85 * baseline

---

## Expected Outcomes

### Success Criteria

1. **Both tasks show learning**: Validation F1 > random baseline
2. **No severe gradient conflicts**: < 20% of batches with negative cosine similarity
3. **No immediate negative transfer**: F1 ≥ 0.85 * baseline for both tasks
4. **NER improvement**: F1 > 0.676 (current baseline)

### Target Performance

- **Classification F1**: ≥ 0.898 (maintain or improve)
- **NER F1**: ≥ 0.749 (target improvement)
- **Combined F1**: ≥ 0.824 (weighted average)

---

## Usage

### Quick Start (TEST_MODE)

```bash
# 1. Verify setup
python test_multitask_setup.py

# 2. Train with TEST_MODE (5 epochs, 50+50 samples)
python src/train_multitask.py --test_mode --output_dir outputs/test_multitask

# 3. Check results
cat outputs/test_multitask/training.log
```

### Full Training

```bash
# Edit config to disable TEST_MODE
sed -i 's/test_mode: true/test_mode: false/' config/multitask_config.yaml

# Train full model
python src/train_multitask.py \
  --config config/multitask_config.yaml \
  --output_dir outputs/multitask_full

# Evaluate best checkpoint
python src/evaluate_multitask.py \
  --checkpoint outputs/multitask_full/checkpoint_best_combined.pt \
  --data_classif data/augmented/classif_train_with_metadata.csv \
  --data_ner data/augmented/ner_train_with_metadata.csv \
  --output outputs/multitask_full/evaluation_report.txt
```

---

## Key Design Decisions

### Why Post-Encoder Fusion?

- Research shows better performance than pre-encoder concatenation
- Allows encoder to learn text representations first
- Metadata enhances rather than dominates text features

### Why Fixed Loss Weights?

- **Simplicity**: Easier to debug and understand
- **MVP Scope**: Advanced methods (GradNorm, PCGrad) deferred to production
- **Weights Rationale**: λ_ner=0.7 prioritizes improvement on weaker task

### Why Oversample NER?

- **Class Balance**: Prevents classification from dominating
- **Gradient Balance**: More NER updates per epoch
- **Simple Approach**: No complex batch construction needed

### Why Auxiliary Prediction?

- **Regularization**: Prevents overfitting on main tasks
- **Useful Representations**: Encourages learning metadata-relevant features
- **Low Weight**: λ_aux=0.1 provides gentle guidance

---

## Monitoring & Debugging

### Key Metrics to Track

1. **Per-Task Losses**: Monitor classif_loss and ner_loss separately
2. **Per-Task F1**: Track validation F1 for each task
3. **Gradient Conflicts**: % of batches with negative cosine similarity
4. **Combined F1**: Overall multi-task performance

### Warning Signs

- **High Gradient Conflicts (>20%)**: Tasks fighting each other
- **One Task Stagnates**: Negative transfer or poor weight balance
- **Both Tasks Degrade**: Model capacity or learning rate issues
- **Auxiliary Loss Dominates**: λ_aux too high

### Debugging Steps

1. Check data loading: Verify metadata extraction
2. Check model forward pass: Ensure correct shapes
3. Check loss computation: Verify masking and weighting
4. Check gradients: Ensure flow to shared encoder
5. Reduce complexity: Try single-task first, then multi-task

---

## Next Steps (Post-MVP)

### If TEST_MODE Succeeds

1. **Full Training**: Train on complete dataset (1634+553 samples)
2. **Hyperparameter Tuning**: Try different loss weights
3. **Validation Split**: Create proper train/val split
4. **Extended Training**: Increase epochs if needed

### If Performance Target Met

1. **Production Integration**: Add to Colab pipeline
2. **Ablation Studies**: Test importance of each component
3. **Advanced Techniques**: Try GradNorm or PCGrad
4. **Ensemble**: Combine with single-task models

### If Issues Found

1. **Negative Transfer**: Adjust loss weights or use separate optimizers
2. **Gradient Conflicts**: Add gradient projection or task scheduling
3. **Poor NER**: Increase λ_ner, add NER-specific data augmentation
4. **Overfitting**: Add dropout, reduce model capacity

---

## References

**Architecture**:
- Liu et al. (2019). "Multi-Task Deep Neural Networks for Natural Language Understanding"
- Kendall et al. (2018). "Multi-Task Learning Using Uncertainty to Weigh Losses"

**Metadata Integration**:
- Lauscher et al. (2020). "Common Sense or World Knowledge? Investigating Adapter-Based Knowledge Injection"

**Gradient Balancing**:
- Chen et al. (2018). "GradNorm: Gradient Normalization for Adaptive Loss Balancing"
- Yu et al. (2020). "Gradient Surgery for Multi-Task Learning"

---

## Conclusion

This implementation provides a solid MVP for multi-task learning with metadata integration. The architecture follows research-backed best practices while maintaining simplicity for debugging and iteration.

**Status**: Ready for TEST_MODE validation
**Next Action**: Run `test_multitask_setup.py` to verify implementation
