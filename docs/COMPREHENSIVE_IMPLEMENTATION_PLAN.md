# Comprehensive Implementation Plan: Build Higher-Quality Models

**Date Created**: 2025-10-29
**Status**: Ready for Review and Execution
**Goal**: Build new models with quality ≥ V2 (Classification F1≥0.898, NER F1≥0.749)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Situation](#current-situation)
3. [Research Findings](#research-findings)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Phase 1: Quick Wins](#phase-1-quick-wins-week-1)
6. [Phase 2: Data & Transfer](#phase-2-data--transfer-weeks-2-3)
7. [Phase 3: Advanced Techniques](#phase-3-advanced-techniques-weeks-4-6)
8. [Cost Analysis](#cost-analysis)
9. [Risk Assessment](#risk-assessment)
10. [Success Criteria](#success-criteria)
11. [Decision Points](#decision-points)
12. [Deliverables Checklist](#deliverables-checklist)

---

## Executive Summary

### The Challenge

Your biodata inventory ML pipeline uses two models (classification + NER) that were trained successfully in October 2021, but recent training attempts (October 28, 2025) showed significant quality degradation:

**Current Production Models (V2 - October 21, 2025)**:
- Classification F1: **0.898** ✅
- NER F1: **0.749** ✅

**Failed Training Attempt (October 28, 2025)**:
- Classification F1: **0.859** ❌ (-4.3%)
- NER F1: **0.653** ❌ (-12.8%)
- High-confidence predictions: **22** vs **3,698** (99.4% loss)

**Root Cause Identified**:
- Learning rate too high (2e-5)
- No weight decay (0.0)
- No early stopping
- NER training: Peaked at epoch 4 (F1=0.739), declined to 0.653 by epoch 10

### The Solution

Comprehensive research by 4 specialized AI agents identified:
1. **Your issues are fixable** - suboptimal hyperparameters, not fundamental problems
2. **Modern techniques exist** - 2023-2025 advances can significantly improve performance
3. **Your unlabeled data is valuable** - 21,677 papers can be leveraged for improvement
4. **Clear path forward** - Prioritized 3-phase roadmap with evidence-based projections

### Expected Outcomes

| Phase | Timeline | NER F1 | Classification F1 | Key Actions |
|-------|----------|--------|-------------------|-------------|
| **Current (V2)** | - | 0.749 | 0.898 | Production baseline |
| **Phase 1** | Week 1 | 0.80-0.82 | 0.91-0.93 | Fix hyperparameters, modern model |
| **Phase 2** | Weeks 2-3 | 0.85-0.87 | 0.93-0.95 | Data augmentation, TAPT |
| **Phase 3** | Weeks 4-6 | 0.86-0.88 | 0.93-0.95 | Self-training, advanced |
| **Conservative** | - | **0.85+** | **0.92+** | +13% NER, +2% Classification |
| **Optimistic** | - | **0.88+** | **0.95+** | +18% NER, +6% Classification |

**Confidence Level**: 75% for Phase 1-2, 60% for Phase 3

### Investment Required

**Financial**: $40-60 total
- UMLS license: Free (1-2 days approval)
- GPT-4 augmentation: $30-50 (optional)
- Colab Pro: $10/month (optional, for A100 access)

**Time**: 4-6 weeks
- Active development: 17-22 days
- Training time (unattended): 40-50 hours
- Total calendar time: 4-6 weeks with overnight training

**Resources**: Google Colab (current infrastructure sufficient)

---

## Current Situation

### Infrastructure Status

**✅ Complete**:
- Research phase: 4 comprehensive reports (150+ pages total)
- Consolidated findings: Single master document with prioritized roadmap
- Experimental infrastructure: 8 files created/modified
- Code review: Comprehensive analysis complete

**⚠️ Needs Fixing** (30 minutes):
- 2 critical import path issues in training scripts
- Best model restoration logic in early stopping

### Available Resources

**Data Assets**:
- ✅ 1,635 classification samples (manually annotated)
- ✅ 554 NER samples (manually annotated) - **Critical bottleneck**
- ✅ 21,677 unlabeled papers (EuropePMC 2022 data) - **Valuable for TAPT and self-training**

**Computational Resources**:
- ✅ Google Colab (T4/V100/A100 GPUs)
- ✅ Google Drive for archival
- ✅ Local development environment (Python 3.11.9)

**Current Models**:
- ✅ V2 Production Models (validated, PyTorch 2.8 compatible)
- ✅ Base model: allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500 (2021)

---

## Research Findings

### Consensus Across All 4 Research Reports

All research agents (Modern ML, Data Augmentation, Few-Shot Learning, Ensemble/Multi-Task) reached consensus on priorities:

#### ✅ HIGH PRIORITY (Implement Immediately)

1. **Hyperparameter Optimization** (ALL 4 REPORTS AGREE)
   - Weight decay: 0.0 → 0.01 (NER), 0.01 (classification)
   - Learning rate: 2e-5 → 5e-6 (NER), 1e-5 (classification)
   - Early stopping: Add with patience=3
   - Dropout: 0.1 → 0.3 (NER), 0.15 (classification)
   - Expected impact: +5-10% val F1

2. **Modern Biomedical Base Model**
   - Current: 2021 RoBERTa
   - Recommended: **BioLinkBERT-base** (2022, SOTA on BLURB benchmark)
   - Alternative: PubMedBERT (2023)
   - Expected impact: +2-4% F1
   - Cost: Free, drop-in replacement

3. **Early Stopping Implementation**
   - Your October 28 training: Peaked epoch 4, declined to epoch 10
   - Early stopping would have saved 6 epochs AND gained +8.6% F1
   - Status: ✅ Implemented (needs fixing)
   - Expected impact: +2-8% F1, saves training time

4. **Mixed Precision Training**
   - Use bfloat16 (A100) or fp16 (T4/V100)
   - 2x training speedup
   - Zero quality loss
   - Expected impact: 0% F1 change, 50% time savings

#### ✅ MEDIUM PRIORITY (Weeks 2-3)

5. **UMLS-EDA Data Augmentation** (#1 Recommendation)
   - Proven: +5-17% F1 in published biomedical NER research
   - Entity-preserving by design
   - Cost: Free (UMLS license approval 1-2 days)
   - Output: 554 → 1,100-1,600 samples
   - Implementation: 3.5 days
   - Expected impact: +3-7% F1

6. **GPT-4 Synthetic Generation** (Optional, Complementary)
   - 2024 research: +17.8% accuracy with LLM augmentation
   - High diversity, quality samples
   - Cost: $30-50 for 400-500 samples
   - Implementation: 1.5 days
   - Expected impact: +2-5% F1

7. **TAPT (Task-Adaptive Pre-Training)**
   - Continue pre-training on your 21,677 unlabeled papers
   - 2024 clinical study (500 samples + 50K unlabeled): +8.5% improvement
   - Your scenario: Similar dataset size, strong applicability
   - Implementation: 3-5 days (one-time pre-training run)
   - Expected impact: +5-10% F1

#### ⚠️ LOW PRIORITY (Weeks 4-6, Optional)

8. **Self-Training with Pseudo-Labels**
   - Use model predictions on 21,677 papers as training data
   - 2024 research: 66% annotation savings, +5-12% F1
   - Iterative improvement (3-4 rounds)
   - Implementation: 4-7 days
   - Expected impact: +5-12% F1

9. **Contrastive Learning (Token-Level)**
   - Better representations for small datasets
   - Implementation: 5-8 days
   - Expected impact: +5-10% F1

#### ❌ NOT RECOMMENDED (Skip)

10. **Traditional Ensembles**
    - Cost: 3-5x training time (28-47 hours)
    - Cost: 3-5x inference time (162-270 minutes)
    - Benefit: +1-3% F1
    - Verdict: Poor ROI, pursue only if all else fails

11. **Multi-Task Learning**
    - High complexity, risk of negative transfer
    - Conditional: Only if Phase 1-2 insufficient

---

## Implementation Roadmap

### Overview

```
Phase 1 (Week 1)
  ↓ Test: Is NER F1 ≥ 0.80?
  ├─ YES → Proceed to Phase 2
  └─ NO → Debug, iterate on Phase 1

Phase 2 (Weeks 2-3)
  ↓ Test: Is NER F1 ≥ 0.85?
  ├─ YES → SUCCESS, consider Phase 3 optional
  └─ NO → Proceed to Phase 3

Phase 3 (Weeks 4-6, Optional)
  ↓ Test: Is NER F1 ≥ 0.88?
  ├─ YES → EXCEPTIONAL SUCCESS
  └─ NO → Acceptable if ≥ 0.85

Decision: Stop if target (F1 ≥ 0.749) achieved
```

### Timeline Summary

| Week | Phase | Focus | Expected NER F1 | Hours |
|------|-------|-------|----------------|-------|
| 1 | Phase 1 | Hyperparameters + Modern Model | 0.80-0.82 | 20-25 |
| 2-3 | Phase 2 | Data Aug + TAPT | 0.85-0.87 | 30-40 |
| 4-6 | Phase 3 | Self-Training + Advanced | 0.86-0.88 | 25-35 |
| **Total** | - | - | **0.85-0.88** | **75-100** |

---

## Phase 1: Quick Wins (Week 1)

### Goal
Achieve NER F1 ≥ 0.80 (+7% from 0.749) with minimal implementation effort.

### Tasks

#### Day 1-2: Fix Infrastructure and Update Config (8 hours)

**1.1 Fix Critical Code Issues** (1 hour)
- Fix import paths in src/class_train.py and src/ner_train.py
- Fix best model restoration in EarlyStopping class
- Test early stopping works correctly
- **Deliverable**: ✅ Working early stopping

**1.2 Update Training Configuration** (2 hours)
- Create new config: `config/train_experimental.yml`
- Set hyperparameters:
  ```yaml
  # Classification
  learning_rate: 1e-5
  weight_decay: 0.01
  dropout: 0.15
  epochs: 15
  early_stopping: true
  patience: 3

  # NER
  learning_rate: 5e-6
  weight_decay: 0.01
  dropout: 0.3
  epochs: 20
  early_stopping: true
  patience: 3
  ```
- **Deliverable**: ✅ config/train_experimental.yml

**1.3 Switch to BioLinkBERT** (2 hours)
- Research: Verify BioLinkBERT-base on Hugging Face
- Update model identifier in config
- Test model loading and tokenization
- Verify compatibility with existing pipeline
- **Deliverable**: ✅ BioLinkBERT integration

**1.4 Enable Mixed Precision** (2 hours)
- Add automatic mixed precision (AMP) to training scripts
- Test on Colab T4 (fp16) and A100 (bfloat16)
- Measure speedup
- **Deliverable**: ✅ 2x faster training

**1.5 Update Experimental Notebook** (1 hour)
- Integrate new configurations
- Add TEST_MODE validation (2 epochs)
- Update session tracking
- **Deliverable**: ✅ Updated experimental_training_pipeline.ipynb

#### Day 3: Test Run (2 hours active, 1-2 hours training)

**1.6 TEST_MODE Validation**
- Run experimental notebook with TEST_MODE=True
- Verify: Early stopping works, configs load, tracking works
- Expected: Completes in 5-10 minutes
- **Deliverable**: ✅ Validated infrastructure

**1.7 Single Model Test Run**
- Train ONE config (classification validated params)
- Run full training (~4 hours)
- Evaluate on test set
- **Deliverable**: ✅ Proof of concept

#### Day 4-5: Full Production Training (2 hours active, ~20 hours training)

**1.8 Full Training Run**
- Set TEST_MODE=False in experimental notebook
- Configure 3 learning rate experiments:
  - Config A: Conservative (LR=3e-6 NER, 5e-6 class)
  - Config B: Validated (LR=5e-6 NER, 1e-5 class)
  - Config C: Moderate (LR=1e-5 NER, 2e-5 class)
- Run all configs sequentially (~20 hours total)
- **Deliverable**: ✅ 6 trained models (3 configs × 2 tasks)

**1.9 Results Analysis**
- Compare all configs against V2 baseline
- Identify best configuration
- Generate comparison report
- **Deliverable**: ✅ Phase 1 results report

#### Day 6-7: Validation and Documentation (6 hours)

**1.10 Model Validation**
- Run inference on 2022 dataset subset (1,000 papers)
- Compare with V2 predictions
- Verify high-confidence rate > 80%
- Calculate baseline overlap (target > 75%)
- **Deliverable**: ✅ Validation report

**1.11 Phase 1 Documentation**
- Document final hyperparameters
- Record training curves and metrics
- Document lessons learned
- Update starting_doc.md
- **Deliverable**: ✅ docs/PHASE1_RESULTS.md

### Success Criteria

**Must Achieve**:
- ✅ NER test F1 ≥ 0.80 (target: 0.80-0.82)
- ✅ Classification test F1 ≥ 0.91 (target: 0.91-0.93)
- ✅ Training stability: No F1 bouncing
- ✅ Overfitting: Train/val gap < 0.15
- ✅ High-confidence rate > 80% at threshold 0.978

**If Achieved**: Proceed to Phase 2
**If Not Achieved**: Debug and iterate, adjust hyperparameters

### Estimated Effort
- **Active work**: 20-25 hours (spread over 7 days)
- **Training time**: ~20-25 hours (unattended, overnight)
- **Total calendar time**: 1 week

---

## Phase 2: Data & Transfer (Weeks 2-3)

### Goal
Achieve NER F1 ≥ 0.85 (+13% from 0.749) through data augmentation and transfer learning.

### Tasks

#### Week 2: Data Augmentation (20-30 hours)

**2.1 UMLS License Application** (1 hour, 1-2 days wait)
- Apply for UMLS license: https://www.nlm.nih.gov/research/umls/
- Free, takes 1-2 business days approval
- Required for UMLS-EDA augmentation
- **Deliverable**: ✅ UMLS account with API access

**2.2 Implement UMLS-EDA** (12 hours)
- Install QuickUMLS and dependencies
- Implement entity-preserving augmentation
- Adapt for BIO tagging
- Test on sample data
- **Deliverable**: ✅ Working UMLS-EDA augmentation

**2.3 Generate Augmented Dataset** (4 hours)
- Run augmentation on 554 NER samples
- Target: 1,100-1,600 augmented samples
- Validate: Entity preservation, BIO consistency
- Manual review: 10% of augmented samples
- **Deliverable**: ✅ data/manual_ner_extraction_augmented.csv

**2.4 Optional: GPT-4 Synthetic Generation** (6 hours, $30-50)
- Design prompts for biomedical database mentions
- Generate 400-500 synthetic samples
- Validate quality (manual review 20%)
- Merge with UMLS-EDA augmented data
- **Deliverable**: ✅ Additional high-quality samples

**2.5 Train with Augmented Data** (2 hours active, 10 hours training)
- Use --augmented flag in training
- Use best config from Phase 1
- Train on expanded dataset
- **Deliverable**: ✅ Models trained on augmented data

**2.6 Evaluate Augmentation Impact** (4 hours)
- Compare: Augmented vs non-augmented
- Measure: Test F1, train/val gap, generalization
- Validate: Baseline overlap, high-confidence rate
- **Deliverable**: ✅ Augmentation impact report

#### Week 3: Task-Adaptive Pre-Training (15-20 hours)

**2.7 Prepare TAPT Corpus** (4 hours)
- Extract text from 21,677 EuropePMC papers
- Clean and preprocess
- Create masked language modeling dataset
- **Deliverable**: ✅ TAPT corpus ready

**2.8 Run TAPT** (2 hours active, 12-15 hours training)
- Continue pre-training BioLinkBERT on your corpus
- Use masked language modeling objective
- Monitor perplexity
- **Deliverable**: ✅ Domain-adapted model

**2.9 Fine-tune TAPT Model** (2 hours active, 10 hours training)
- Fine-tune on classification and NER
- Use augmented data + best hyperparameters
- Compare: TAPT vs no-TAPT
- **Deliverable**: ✅ TAPT-enhanced models

**2.10 Phase 2 Analysis** (6 hours)
- Comprehensive evaluation on test set
- Compare all variations: Baseline, Phase 1, Augmented, TAPT
- Calculate cumulative improvement
- Validate against success criteria
- **Deliverable**: ✅ docs/PHASE2_RESULTS.md

### Success Criteria

**Must Achieve**:
- ✅ NER test F1 ≥ 0.85 (target: 0.85-0.87)
- ✅ Classification test F1 ≥ 0.93
- ✅ Augmented dataset: 1,000-1,600 samples
- ✅ Reduced overfitting: Train/val gap < 0.10

**If Achieved**: SUCCESS - Phase 3 is optional
**If Not Achieved**: Proceed to Phase 3 for additional improvements

### Estimated Effort
- **Active work**: 30-40 hours (spread over 2 weeks)
- **Training time**: ~30-35 hours (unattended)
- **Total calendar time**: 2-3 weeks (includes UMLS approval wait)

---

## Phase 3: Advanced Techniques (Weeks 4-6, Optional)

### Goal
Push beyond F1 0.85 toward F1 0.88-0.92 using advanced techniques.

**Prerequisites**: Phase 2 complete, NER F1 ≥ 0.85

### Tasks

#### Week 4: Self-Training Setup (15-20 hours)

**3.1 Implement Self-Training Pipeline** (8 hours)
- Pseudo-labeling on 21,677 unlabeled papers
- Confidence threshold selection (start with 0.95)
- Iterative refinement loop (3-4 rounds)
- Quality control mechanisms
- **Deliverable**: ✅ Self-training infrastructure

**3.2 Round 1: Initial Pseudo-Labeling** (4 hours active, 6 hours inference)
- Use best model from Phase 2
- Generate pseudo-labels for all 21,677 papers
- Filter by confidence > 0.95
- Add to training data
- **Deliverable**: ✅ Pseudo-labeled dataset (round 1)

**3.3 Round 1: Retrain** (2 hours active, 10 hours training)
- Train on original + pseudo-labeled data
- Evaluate on test set
- Measure improvement
- **Deliverable**: ✅ Self-trained model (round 1)

#### Week 5: Self-Training Iteration (15-20 hours)

**3.4 Rounds 2-3: Iterative Improvement** (per round: 2 hours active, 10 hours training)
- Lower confidence threshold gradually (0.95 → 0.90 → 0.85)
- Re-label with updated model
- Retrain on expanded dataset
- Monitor for quality degradation
- **Deliverable**: ✅ Self-trained models (rounds 2-3)

**3.5 Self-Training Analysis** (6 hours)
- Compare all rounds
- Identify optimal confidence threshold
- Measure final improvement
- Document convergence
- **Deliverable**: ✅ Self-training results report

#### Week 6: Advanced Techniques (Optional) (15-20 hours)

**3.6 Contrastive Learning** (8 hours setup, 10 hours training)
- Implement token-level contrastive learning
- Train on augmented data
- Fine-tune for NER
- **Deliverable**: ✅ Contrastive learning model

**3.7 Final Evaluation & Selection** (6 hours)
- Comprehensive comparison: All phases, all techniques
- Select best model(s) for production
- Generate final performance report
- **Deliverable**: ✅ docs/PHASE3_RESULTS.md

**3.8 Production Deployment** (4 hours)
- Archive best models
- Update production paths (out/classif_train_out/, out/ner_train_out/)
- Generate model cards with metadata
- Update starting_doc.md
- **Deliverable**: ✅ New production models deployed

### Success Criteria

**Target**:
- ✅ NER test F1 ≥ 0.88 (stretch: 0.90-0.92)
- ✅ Classification test F1 ≥ 0.94
- ✅ Demonstrable improvement over Phase 2

**If Achieved**: EXCEPTIONAL SUCCESS
**If Not Achieved**: Acceptable if Phase 2 goals met (F1 ≥ 0.85)

### Estimated Effort
- **Active work**: 25-35 hours (spread over 3 weeks)
- **Training time**: ~40-50 hours (unattended)
- **Total calendar time**: 3 weeks

---

## Cost Analysis

### Financial Costs

| Item | Cost | Required? | Notes |
|------|------|-----------|-------|
| **UMLS License** | Free | Yes (Phase 2) | 1-2 days approval |
| **GPT-4 Augmentation** | $30-50 | Optional | 400-500 samples |
| **Colab Pro** | $10/month | Optional | For A100 access |
| **Total (Minimum)** | **$0-10** | - | If skip GPT-4, use free Colab |
| **Total (Recommended)** | **$40-60** | - | Includes GPT-4 + Colab Pro |

### Time Investment

| Phase | Active Work | Training Time | Calendar Time |
|-------|-------------|---------------|---------------|
| **Phase 1** | 20-25 hours | 20-25 hours | 1 week |
| **Phase 2** | 30-40 hours | 30-35 hours | 2-3 weeks |
| **Phase 3** | 25-35 hours | 40-50 hours | 3 weeks (optional) |
| **Total** | **75-100 hours** | **90-110 hours** | **4-6 weeks** |

**Note**: Training time is unattended (overnight runs). Active work can be spread across business hours.

### Return on Investment

| Metric | Current | Target | Improvement | Value |
|--------|---------|--------|-------------|-------|
| **NER F1** | 0.749 | 0.85-0.88 | +13-18% | High |
| **Classification F1** | 0.898 | 0.92-0.95 | +2-6% | Medium |
| **Training Stability** | Low | High | Significant | High |
| **Overfitting** | High (gap=0.353) | Low (gap<0.10) | -71% | High |
| **Annotation Savings** | 0 samples | +500-1,000 | $25k+ value | High |

**Manual annotation cost avoided**: ~$50 per NER sample × 500-1,000 samples = **$25,000-50,000 value**

---

## Risk Assessment

### High Risks (Mitigation Required)

**R1: Phase 1 doesn't achieve target (F1 < 0.80)**
- **Probability**: Low (20%)
- **Impact**: High - blocks Phase 2
- **Mitigation**:
  - Fallback: Try PubMedBERT instead of BioLinkBERT
  - Fallback: Adjust learning rates (try 3e-6, 1e-5, 5e-5)
  - Fallback: Increase dropout further (0.4 for NER)
  - Escalation: Request additional hyperparameter research

**R2: Data augmentation introduces noise**
- **Probability**: Medium (30%)
- **Impact**: Medium - waste of time, possible F1 drop
- **Mitigation**:
  - Validate augmented samples manually (10-20% review)
  - Compare: Augmented vs non-augmented performance
  - Fallback: Filter augmented samples by quality score
  - Abort criterion: If F1 drops > 2%, discard augmentation

**R3: UMLS license delayed > 5 days**
- **Probability**: Low (10%)
- **Impact**: Low - delays Phase 2 by days
- **Mitigation**:
  - Apply for license early (Day 1 of Phase 1)
  - Alternative: Start with GPT-4 augmentation while waiting
  - Alternative: Use synonym replacement without UMLS (lower quality)

### Medium Risks (Monitor)

**R4: Training time exceeds Colab limits**
- **Probability**: Medium (40% on free tier)
- **Impact**: Medium - need to restart training
- **Mitigation**:
  - Use Colab Pro ($10/month, 24-hour limit)
  - Train models sequentially, not all at once
  - Use early stopping to reduce epoch count
  - Save checkpoints frequently

**R5: Self-training causes error propagation**
- **Probability**: Medium (30%)
- **Impact**: Medium - Phase 3 fails
- **Mitigation**:
  - Use high confidence threshold initially (0.95)
  - Monitor test F1 every round
  - Abort if test F1 doesn't improve
  - Fallback: Use confidence threshold adaptive strategy

### Low Risks (Accept)

**R6: Phase 3 doesn't provide additional gains**
- **Probability**: Medium (40%)
- **Impact**: Low - Phase 2 already successful
- **Mitigation**: Accept - Phase 3 is optional
- **Fallback**: Stop at Phase 2 if F1 ≥ 0.85

**R7: Code bugs in experimental infrastructure**
- **Probability**: Low (20% after fixes)
- **Impact**: Low - delays by hours
- **Mitigation**: Comprehensive testing in TEST_MODE first

### Risk Summary

| Risk Level | Count | Acceptable? |
|------------|-------|-------------|
| **High** | 2 | ⚠️ Requires mitigation |
| **Medium** | 3 | ✅ Acceptable with monitoring |
| **Low** | 2 | ✅ Acceptable |

**Overall Risk**: **MEDIUM** - Well-understood risks with clear mitigation strategies

---

## Success Criteria

### Phase 1 Success

**Must Meet ALL**:
- ✅ NER test F1 ≥ 0.80
- ✅ Classification test F1 ≥ 0.91
- ✅ Training completes without crashes
- ✅ Early stopping triggers appropriately
- ✅ Train/val gap < 0.15

**Should Meet (Nice to Have)**:
- ✅ NER test F1 ≥ 0.82
- ✅ High-confidence rate > 85%
- ✅ Baseline overlap > 80%

**Decision**: If all "Must Meet" achieved → Proceed to Phase 2

### Phase 2 Success

**Must Meet ALL**:
- ✅ NER test F1 ≥ 0.85
- ✅ Classification test F1 ≥ 0.93
- ✅ Augmented dataset created (1,000+ samples)
- ✅ Train/val gap < 0.10

**Should Meet**:
- ✅ NER test F1 ≥ 0.87
- ✅ TAPT provides measurable benefit (+1-2% F1)

**Decision**:
- If F1 ≥ 0.87 → SUCCESS, Phase 3 optional
- If 0.85 ≤ F1 < 0.87 → Proceed to Phase 3

### Phase 3 Success (Optional)

**Target**:
- ✅ NER test F1 ≥ 0.88

**Acceptable**:
- ✅ Any improvement over Phase 2
- ✅ Demonstrable benefit from self-training

**Decision**: If Phase 2 achieved F1 ≥ 0.85, project is successful regardless of Phase 3 outcome

### Overall Project Success

**Minimum Success** (Must Achieve):
- ✅ NER F1 ≥ 0.80 (V2 0.749 + 7%)
- ✅ Classification F1 ≥ 0.91 (V2 0.898 + 1.3%)
- ✅ Models production-ready and deployed
- ✅ Training pipeline stable and reproducible

**Target Success** (Should Achieve):
- ✅ NER F1 ≥ 0.85 (V2 + 13%)
- ✅ Classification F1 ≥ 0.92 (V2 + 2.4%)

**Exceptional Success** (Stretch Goal):
- ✅ NER F1 ≥ 0.88 (V2 + 18%)
- ✅ Classification F1 ≥ 0.94 (V2 + 4.7%)

---

## Decision Points

### When to Stop

**✅ STOP and DEPLOY** if:
1. NER F1 ≥ 0.85 after Phase 2 (target met)
2. Any phase achieves "Exceptional Success" criteria
3. Diminishing returns observed (< 1% improvement for significant effort)

### When to Continue

**➡️ CONTINUE to next phase** if:
1. Current phase success criteria met
2. Improvement trend is positive
3. Time/budget allows
4. Risk remains acceptable

### When to Pivot

**🔄 PIVOT strategy** if:
1. Phase 1 < 0.75 F1 (worse than V2) → Debug hyperparameters
2. Phase 2 < 0.80 F1 → Revisit data augmentation quality
3. Self-training degrades performance → Adjust confidence threshold or abort

### When to Abort

**❌ ABORT project** if:
1. Cannot achieve F1 ≥ 0.749 (V2 baseline) after Phase 1 revisions
2. Critical infrastructure failures cannot be resolved
3. Budget or time constraints exceeded

**Note**: Aborting is unlikely given:
- Phase 1 has 75% confidence of success
- Multiple fallback options available
- Can always revert to V2 models

---

## Deliverables Checklist

### Research Phase (✅ COMPLETE)

- [x] BASE_RESEARCH_BRIEF.md
- [x] MODERN_ML_ALTERNATIVES_BRIEF.md + Research Report
- [x] DATA_AUGMENTATION_NER_BRIEF.md + Research Report
- [x] FEW_SHOT_META_LEARNING_BRIEF.md + Research Report
- [x] ENSEMBLE_MULTITASK_BRIEF.md + Research Report
- [x] RESEARCH_FINDINGS_CONSOLIDATED.md

### Infrastructure Phase (⚠️ NEEDS FIXES)

- [x] src/experimental_utils.py
- [x] src/class_train.py (modified)
- [x] src/ner_train.py (modified)
- [x] src/ner_data_generator.py (modified)
- [x] src/data_augmentation/ module
- [x] augment_ner_dataset.py
- [x] experimental_training_pipeline.ipynb
- [ ] **Fix critical import issues** (30 min)
- [ ] **Fix early stopping restoration** (30 min)

### Phase 1 Deliverables (Week 1)

- [ ] config/train_experimental.yml
- [ ] BioLinkBERT integration tested
- [ ] Mixed precision enabled
- [ ] 6 trained models (3 configs × 2 tasks)
- [ ] Phase 1 results comparison report
- [ ] Model validation report
- [ ] docs/PHASE1_RESULTS.md
- [ ] Updated starting_doc.md

### Phase 2 Deliverables (Weeks 2-3)

- [ ] UMLS account approved
- [ ] UMLS-EDA implemented
- [ ] data/manual_ner_extraction_augmented.csv (1,000-1,600 samples)
- [ ] Optional: GPT-4 synthetic samples
- [ ] Models trained on augmented data
- [ ] Augmentation impact report
- [ ] TAPT corpus prepared
- [ ] Domain-adapted model (TAPT)
- [ ] TAPT-enhanced models
- [ ] docs/PHASE2_RESULTS.md

### Phase 3 Deliverables (Weeks 4-6, Optional)

- [ ] Self-training pipeline implemented
- [ ] Pseudo-labeled datasets (3-4 rounds)
- [ ] Self-trained models (3-4 rounds)
- [ ] Self-training results report
- [ ] Optional: Contrastive learning model
- [ ] Final performance comparison
- [ ] Production models deployed
- [ ] Model cards with metadata
- [ ] docs/PHASE3_RESULTS.md
- [ ] Updated starting_doc.md

### Documentation Deliverables

- [x] docs/COMPREHENSIVE_IMPLEMENTATION_PLAN.md (this document)
- [x] docs/EXPERIMENTAL_TRAINING_IMPLEMENTATION.md
- [ ] docs/PHASE1_RESULTS.md
- [ ] docs/PHASE2_RESULTS.md
- [ ] docs/PHASE3_RESULTS.md (optional)
- [ ] docs/FINAL_MODEL_REPORT.md
- [ ] Updated docs/starting_doc.md with new recommendations

---

## Appendix A: Hyperparameter Reference

### Validated Hyperparameters (Phase 1)

**Classification Model**:
```yaml
model: michiyasunaga/BioLinkBERT-base
epochs: 15
batch_size: 16
learning_rate: 1e-5
weight_decay: 0.01
dropout: 0.15
max_length: 256
optimizer: AdamW
scheduler: linear_warmup_linear_decay
warmup_ratio: 0.1
early_stopping: true
patience: 3
mixed_precision: true (bfloat16 or fp16)
```

**NER Model**:
```yaml
model: michiyasunaga/BioLinkBERT-base
epochs: 20
batch_size: 16
learning_rate: 5e-6
weight_decay: 0.01
dropout: 0.3
max_length: 512
optimizer: AdamW
scheduler: linear_warmup_linear_decay
warmup_ratio: 0.1
early_stopping: true
patience: 3
mixed_precision: true (bfloat16 or fp16)
```

### Alternative Configurations (Fallback)

**Conservative** (if validated params too aggressive):
```yaml
classification_lr: 5e-6
ner_lr: 3e-6
dropout: 0.2 (classification), 0.25 (NER)
```

**Aggressive** (if validated params too conservative):
```yaml
classification_lr: 2e-5
ner_lr: 1e-5
weight_decay: 0.005
```

---

## Appendix B: Quick Reference Commands

### Run Training with Early Stopping

```bash
# Classification
python src/class_train.py \
    -t data/classif_splits/train.csv \
    -v data/classif_splits/val.csv \
    -o out/classif_train_exp/ \
    -m michiyasunaga/BioLinkBERT-base \
    -ne 15 \
    -rate 1e-5 \
    -decay 0.01 \
    --early-stopping \
    --patience 3 \
    -r

# NER
python src/ner_train.py \
    -t data/ner_splits/train.pkl \
    -v data/ner_splits/val.pkl \
    -o out/ner_train_exp/ \
    -m michiyasunaga/BioLinkBERT-base \
    -ne 20 \
    -rate 5e-6 \
    -decay 0.01 \
    --early-stopping \
    --patience 3 \
    -r
```

### Run Experimental Notebook

```python
# In Google Colab
# 1. Upload experimental_training_pipeline.ipynb
# 2. Mount Google Drive
# 3. Set configuration

TEST_MODE = True  # For quick testing
# TEST_MODE = False  # For production

# Run all cells
```

### Generate Augmented Dataset

```bash
# After UMLS-EDA implementation
python augment_ner_dataset.py \
    --input data/manual_ner_extraction.csv \
    --output data/manual_ner_extraction_augmented.csv \
    --strategy umls \
    --augmentation-factor 2.0
```

---

## Appendix C: Troubleshooting

### Common Issues

**Issue: Import errors when running training scripts**
```bash
# Fix: Add src to PYTHONPATH
export PYTHONPATH="src:$PYTHONPATH"
python src/class_train.py ...
```

**Issue: Colab disconnects during long training**
```python
# Solution: Use Colab Pro or split into shorter runs
# Or: Use session persistence tricks (keep browser tab active)
```

**Issue: GPU out of memory**
```python
# Solution 1: Reduce batch size
batch_size = 8  # instead of 16

# Solution 2: Use gradient accumulation
accumulation_steps = 2
effective_batch_size = 8 * 2 = 16
```

**Issue: Early stopping triggers too early**
```python
# Solution: Increase patience
patience = 5  # instead of 3
```

**Issue: Models not improving after Phase 1**
```python
# Debug checklist:
# 1. Verify hyperparameters are actually being used
# 2. Check training curves for issues
# 3. Verify data loading correctly
# 4. Test with smaller learning rate
# 5. Ensure BioLinkBERT is actually loaded (not cached old model)
```

---

## Next Steps

### Immediate Actions (Today)

1. **Review this plan** - Read thoroughly, ask questions
2. **Fix code issues** - Launch fix agent (see separate task)
3. **Approve plan** - Confirm readiness to proceed
4. **Schedule Week 1** - Block calendar time for Phase 1

### Week 1 Start (After Approval)

1. **Apply for UMLS license** - Get this started early
2. **Fix infrastructure** - 1-2 hours
3. **Update configs** - 2 hours
4. **Run TEST_MODE** - Validate everything works
5. **Start full training** - Let it run overnight

### Stay on Track

- **Daily**: Check training progress, review logs
- **Weekly**: Evaluate phase results, decide next steps
- **End of Phase**: Comprehensive evaluation, document results
- **Decision points**: Use framework in this document

---

**Document Status**: ✅ Ready for Review
**Last Updated**: 2025-10-29
**Next Review**: After Phase 1 completion
**Owner**: Biodata Inventory ML Team
**Contact**: See project repository for maintainers

---

**This plan is your roadmap to success. Follow it systematically, adapt when needed, and celebrate incremental wins. You've got this! 🚀**
