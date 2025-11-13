# Base Research Brief: Biodata Inventory ML Pipeline Modernization

**Date**: 2025-10-29
**Purpose**: Comprehensive research guide for AI agents investigating modern ML approaches
**Status**: Active Research Document
**Target Audience**: AI research agents with expertise in NLP, biomedical ML, and modern deep learning

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [Current Architecture](#current-architecture)
4. [Current Training Approach](#current-training-approach)
5. [Performance Requirements](#performance-requirements)
6. [Critical Constraints](#critical-constraints)
7. [Problem Statement](#problem-statement)
8. [Historical Context & Challenges](#historical-context--challenges)
9. [Research Requirements](#research-requirements)
10. [Evaluation Criteria](#evaluation-criteria)
11. [Success Metrics](#success-metrics)

---

## 1. Executive Summary

The **Biodata Inventory ML Pipeline** is a production system that automatically identifies and extracts biodata resources from scientific literature. The system uses two fine-tuned biomedical RoBERTa models (classification + NER) to process EuropePMC query results and generate comprehensive inventories of global biodata resources.

**Current Challenge**: The codebase originated in 2022, and recent training attempts have shown quality degradation. We need to investigate modern ML approaches (2023-2025) to determine if better tools, techniques, or models are available.

**Primary Goal**: Build new models with quality **equal to or exceeding** current production models:
- **Classification**: F1 ≥ 0.898
- **NER**: F1 ≥ 0.749

**Key Question**: Are we using optimal algorithms and approaches for 2025, or have significant improvements been made since 2022 that we should adopt?

---

## 2. Project Overview

### 2.1 Business Purpose

The pipeline serves researchers and institutions who need to:
- Identify biodata resources (databases, repositories, data collections) from scientific literature
- Extract structured information about these resources (names, URLs, descriptions)
- Maintain comprehensive inventories of available biodata resources globally
- Track new biodata resources as they emerge in the literature

### 2.2 System Architecture

```
Input: EuropePMC Query Results (CSV)
  ↓
[Classification Model] → Identify papers describing bio-resources
  ↓
[NER Model] → Extract database/resource names (entities)
  ↓
[URL Extraction] → Extract resource URLs using regex
  ↓
[Name Processing] → Select best name with confidence scoring
  ↓
Output: Final Inventory (structured biodata resource catalog)
```

### 2.3 Scale & Performance

- **Training data**: 1,635 classification samples, 554 NER samples (manually curated)
- **Production data**: 21,677 papers from 2022 EuropePMC query
- **Training time**: ~9.5 hours for full production training (Google Colab T4/V100/A100)
- **Prediction time**: ~54 minutes for 21,677 papers (classification)
- **Hardware**: Google Colab GPUs (T4/V100/A100), local testing on MPS/CPU

### 2.4 Technology Stack (Current)

- **Language**: Python 3.11.9
- **ML Framework**: PyTorch 2.2.2
- **Transformers**: Hugging Face Transformers 4.35.0
- **Execution**: Google Colab (primary), local development (secondary)
- **Base Model**: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500` (2021)

---

## 3. Current Architecture

### 3.1 Model 1: Classification (Bio-Resource Detection)

**Task**: Binary classification to identify papers that describe biodata resources

**Input**: Title + Abstract concatenation
**Output**: Binary label (bio-resource vs. general scientific paper)
**Architecture**: RoBERTa-base + classification head
**Max Sequence Length**: 256 tokens

**Training Data**:
- Total samples: 1,635 (manually annotated)
- Split: 70% train (1,145), 15% validation (245), 15% test (245)
- Class distribution: Balanced
- Features: Concatenated title and abstract text from EuropePMC papers

**Current Performance (V2 Model)**:
- Test F1: 0.898
- Precision: 0.930
- Recall: 0.869
- Status: ✅ Production-ready

### 3.2 Model 2: Named Entity Recognition (Database Name Extraction)

**Task**: Token-level classification to extract biodata resource names

**Input**: Title + Abstract text
**Output**: BIO-tagged sequences identifying entity spans
**Architecture**: RoBERTa-base + token classification head
**Max Sequence Length**: 512 tokens (longer than classification for entity extraction)

**Entity Types** (BIO tagging):
- **O**: Outside any entity (background text)
- **B-COM**: Beginning of compound/abbreviation name (e.g., "GEO", "TCGA")
- **I-COM**: Inside (continuation of) compound name
- **B-FUL**: Beginning of full descriptive name (e.g., "Gene Expression Omnibus")
- **I-FUL**: Inside (continuation of) full name

**Training Data**:
- Total samples: 554 (manually annotated) ⚠️ **SMALL DATASET**
- Split: 70% train (~388), 15% validation (~83), 15% test (~83)
- Entity distribution: Imbalanced (O tokens dominate)
- Format: CSV with text + BIO tags per token

**Current Performance (V2 Model)**:
- Test F1: 0.749 (entity-level)
- Precision: 0.779
- Recall: 0.722
- Status: ✅ Production-ready but **small dataset limits potential**

### 3.3 Base Model Details

**Model**: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500`

**Specifications**:
- Architecture: RoBERTa-base (Robustly Optimized BERT Pretraining Approach)
- Parameters: ~125M
- Vocabulary: 50,265 tokens
- Hidden size: 768
- Attention heads: 12
- Layers: 12
- Max position embeddings: 514

**Pre-training Strategy**:
- **DAPT** (Domain-Adaptive Pre-Training): Pre-trained on biomedical text
- **TAPT** (Task-Adaptive Pre-Training): Further adapted on RCT (Randomized Controlled Trial) abstracts
- Source: Allen Institute for AI (AllenAI)
- Released: 2021
- Domain: Biomedical NLP

**Why This Model Was Chosen (2022)**:
- Strong biomedical domain adaptation
- Proven performance on biomedical NER tasks
- Balanced size (not too large for Colab)
- Open source and well-documented

**Current Question**: Are there better biomedical language models in 2023-2025?

---

## 4. Current Training Approach

### 4.1 Training Hyperparameters (Current - Problematic)

**Classification Model**:
```yaml
epochs: 10
batch_size: 16 (auto-optimized based on GPU memory)
learning_rate: 2e-5  # ⚠️ TOO HIGH - causes instability
weight_decay: 0.0     # ⚠️ NO REGULARIZATION - causes overfitting
max_length: 256
optimizer: AdamW
scheduler: Linear warmup + linear decay
metric: precision (primary), also tracks F1 and recall
dropout: Default (0.1 from base model)
```

**NER Model**:
```yaml
epochs: 10
batch_size: 16
learning_rate: 2e-5  # ⚠️ TOO HIGH for small dataset (554 samples)
weight_decay: 0.0     # ⚠️ NO REGULARIZATION
max_length: 512
optimizer: AdamW
scheduler: Linear warmup + linear decay
metric: f1 (entity-level, using seqeval)
dropout: Default (0.1)
```

### 4.2 Training Infrastructure

**Execution Environment**: Google Colab notebooks
- Session isolation: Unique session IDs (YYYY-MM-DD-abcdef format)
- GPU allocation: T4 (free), V100/A100 (Colab Pro)
- Session management: Complete artifact archival to Google Drive
- No checkpointing: Eliminated due to data contamination risks

**Training Pipeline** (6 steps):
1. Data split generation (train/val/test)
2. Classification model training
3. NER model training
4. Model evaluation on test sets
5. Model deployment to production locations
6. Session archival with complete traceability

**Features**:
- TEST_MODE toggle: Quick validation (2 epochs, 5-8 min) vs. production (10 epochs, 9.5 hrs)
- Unique session directories: Prevents conflicts between parallel runs
- Model traceability: Checksums and lineage tracking
- No early stopping: Currently trains for fixed epochs
- Manual monitoring: Training curves reviewed post-hoc

### 4.3 Data Preprocessing

**Text Processing**:
- Concatenation: Title + " " + Abstract
- Tokenization: RoBERTa tokenizer (byte-pair encoding)
- Truncation: Hard cutoff at max_length
- Padding: Batch-level padding to longest sequence
- Special tokens: [CLS] text [SEP] format

**NER-Specific Processing**:
- Token alignment: Word-level labels mapped to subword tokens
- BIO consistency: Ensures valid BIO sequences (no I- without B-)
- Label handling: -100 for special tokens and subword continuations
- Entity validation: Validates entity spans during data loading

**No Data Augmentation**: Currently using raw annotated data without augmentation

---

## 5. Performance Requirements

### 5.1 Minimum Acceptable Performance

**Classification Model**:
- Test F1: ≥ 0.85 (minimum acceptable)
- Target F1: ≥ 0.898 (match or exceed V2)
- Precision: ≥ 0.90 (minimize false positives)
- Recall: ≥ 0.85 (minimize false negatives)

**NER Model**:
- Test F1: ≥ 0.70 (minimum acceptable)
- Target F1: ≥ 0.749 (match or exceed V2)
- Precision: ≥ 0.75 (entity-level)
- Recall: ≥ 0.70 (entity-level)

### 5.2 Training Quality Indicators

**Validation Curve Requirements**:
- Steady improvement (no significant bouncing)
- Peak validation F1 reached before final epoch
- Train/validation gap < 0.15 (acceptable overfitting level)
- No catastrophic drops after peak performance

**Inference Quality**:
- High-confidence predictions: > 80% of predictions above confidence threshold (0.978)
- Baseline overlap: > 75% agreement with validated V2 inventory
- Consistent predictions: Minimal variance across multiple runs
- Reasonable prediction distributions: Not all high or all low confidence

### 5.3 Operational Requirements

**Training Time**:
- Acceptable: ≤ 12 hours for full production training (Google Colab)
- Target: 8-10 hours (current: ~9.5 hours)

**Inference Time**:
- Acceptable: ≤ 90 minutes for 21,677 papers
- Target: ~60 minutes (current: ~54 minutes classification)

**Resource Constraints**:
- Google Colab GPU memory: ≤ 15GB for T4, ≤ 40GB for A100
- Model size: ≤ 500MB per model (storage considerations)
- CPU inference: Should be feasible (though slower) for local development

---

## 6. Critical Constraints

### 6.1 Dataset Limitations

**Classification Dataset**: 1,635 samples
- Status: **Adequate** for current approach
- Limitation: Cannot easily expand without extensive manual annotation
- Cost: Each sample requires expert review of title+abstract
- Time: ~5-10 minutes per sample for expert annotation

**NER Dataset**: 554 samples ⚠️ **CRITICAL CONSTRAINT**
- Status: **Too small** for optimal deep learning performance
- Limitation: Major bottleneck for NER quality improvements
- Annotation complexity: Requires precise entity boundary marking + BIO tagging
- Cost: ~10-20 minutes per sample for expert annotation
- Long-term goal: Expand to 1,000-2,000 samples

**Implications**:
- **Cannot simply "add more data"** without significant manual effort
- Must optimize for small-dataset scenarios
- Data-efficient techniques highly valuable
- Data augmentation strategies critical for NER

### 6.2 Computational Constraints

**Hardware**:
- Primary: Google Colab (free T4, Pro V100/A100)
- Limited: 12-hour runtime limit on Colab (free tier)
- Memory: Must fit in 15GB GPU memory (T4)
- Cost: Prefer free/low-cost solutions

**Inference Deployment**:
- Must support CPU inference (local development)
- Reasonable latency required (not production API, but interactive use)
- Model size: Prefer smaller models for easier deployment

### 6.3 Domain Constraints

**Biomedical Specialization Required**:
- General-purpose models (e.g., base BERT) perform poorly
- Domain knowledge critical: biomedical terminology, naming conventions
- Entity types are domain-specific (database names, not people/places)

**Text Characteristics**:
- Scientific writing style (formal, technical)
- Heavy use of acronyms and abbreviations (e.g., TCGA, GEO, UniProt)
- Entity ambiguity: Same abbreviation can mean different things
- Complex entity structures: Multi-word names, parenthetical notation

### 6.4 Operational Constraints

**Execution Environment**: Google Colab
- No persistent storage (must save to Google Drive)
- Session timeouts (12 hours free, 24 hours Pro)
- Variable GPU availability
- Must be self-contained (no external services)

**Backward Compatibility**:
- Must maintain compatibility with existing data formats
- Pipeline outputs must match expected schema
- Model traceability must be preserved

**Cost Considerations**:
- Prefer open-source models and tools
- Avoid paid APIs for core functionality
- Colab Pro acceptable if significant improvement

---

## 7. Problem Statement

### 7.1 Primary Problem

**Model Quality Degradation**: Recent training attempts (October 28, 2025) produced models with significantly worse performance than the validated V2 models:

**October 28 Training Results**:
- NER F1: 0.653 (vs. 0.749 target) - **12.8% drop**
- Classification F1: 0.859 (vs. 0.898 target) - **4.3% drop**
- High-confidence predictions: 22 (vs. 3,698 from V2) - **99.4% loss**

**Root Cause Identified**:
- Learning rate too high (2e-5) → training instability, F1 bouncing
- No weight decay (0.0) → overfitting on small NER dataset
- No early stopping → continued training past optimal point
- NER training curve: Peaked at epoch 4 (F1=0.739), declined to 0.653 by epoch 10
- Extreme overfitting: Train F1=0.974, Val F1=0.621 (gap of 0.353)

### 7.2 Underlying Questions

**Are we using optimal approaches?**

The current codebase was developed in 2022 using standard practices at the time. Since then, significant advances have been made in:
- **Biomedical language models** (2023-2025 releases)
- **Parameter-efficient fine-tuning** (LoRA, QLoRA, adapters)
- **Optimizers** (Lion, Sophia, improved AdamW variants)
- **Training strategies** (better regularization, scheduling, data efficiency)
- **Small dataset techniques** (few-shot learning, meta-learning)
- **Data augmentation** (modern augmentation libraries and techniques)

**Key Research Questions**:
1. Are there better biomedical base models than the 2021 RoBERTa we're using?
2. Would parameter-efficient fine-tuning (LoRA, QLoRA) improve results?
3. Are modern optimizers (Lion, Sophia) better than AdamW for our use case?
4. What are the best data augmentation strategies for biomedical NER?
5. Can few-shot learning or meta-learning help with our small dataset?
6. Would ensemble or multi-task learning improve overall performance?
7. What modern training techniques could prevent overfitting on 554 samples?
8. Are there better evaluation frameworks or quality monitoring tools?

### 7.3 Success Definition

**Immediate Success**: Build models with performance ≥ V2 models using validated hyperparameters

**Strategic Success**: Identify modern approaches that provide:
- **Higher quality**: Better F1 scores with same data
- **Better stability**: More consistent training, less hyperparameter sensitivity
- **Data efficiency**: Better performance with limited samples
- **Future-proofing**: Adopt 2025 best practices for long-term maintainability

---

## 8. Historical Context & Challenges

### 8.1 Development Timeline

**2022**: Initial development
- Original codebase and training approach established
- Python 3.8, PyTorch 2.0.0, older Transformers
- Original models trained successfully

**October 2025**: Modernization & Issues
- **October 21**: Successful training run with good models
- **October 27**: PyTorch 2.8 compatibility issue discovered and fixed
  - Problem: NamedTuple checkpoints caused 99% prediction loss
  - Solution: Converted to dict-only format, created V2 models
- **October 28**: Checkpoint corruption issue found and resolved
  - Problem: Checkpoint system mixed data from different runs
  - Solution: Deprecated checkpointing entirely
- **October 28**: New training produced poor quality models
  - Problem: Hyperparameters caused training instability
  - Root cause: LR too high, no weight decay, no early stopping
  - V2 models validated for continued production use

### 8.2 Key Learnings

**What Works Well**:
- Base architecture (RoBERTa + task-specific heads) is sound
- BIO tagging approach for NER is effective
- Two-model pipeline (classification then NER) is appropriate
- Session isolation and traceability systems are robust
- Google Colab execution is reliable and cost-effective

**What Needs Improvement**:
- Hyperparameter selection is fragile (small changes = large quality impact)
- Small NER dataset (554 samples) is a critical bottleneck
- No automated early stopping or training quality monitoring
- No data augmentation to expand limited training data
- Lack of modern training techniques (LoRA, better optimizers, etc.)
- Manual hyperparameter tuning without systematic approach

**Critical Insight**: The architecture and approach are fundamentally sound, but we need modern techniques to:
1. Handle small datasets more effectively
2. Stabilize training with better hyperparameters and regularization
3. Expand data through augmentation
4. Leverage 2023-2025 advancements in biomedical NLP

---

## 9. Research Requirements

### 9.1 Research Scope

**Time Period**: Focus on 2023-2025 developments
- Prioritize recent papers (2024-2025)
- Consider 2023 papers if highly relevant
- Acknowledge 2022 as baseline (current codebase era)

**Source Types**:
- **Academic papers**: NeurIPS, ICML, ACL, EMNLP, NAACL, BioNLP workshop
- **Preprints**: arXiv, bioRxiv (recent developments)
- **Industry blogs**: Hugging Face, Google Research, Microsoft Research, OpenAI
- **GitHub repositories**: Popular implementations, new libraries
- **Benchmarks**: BLURB, BLUE, biomedical NER competitions

**Domain Focus**:
- Biomedical NLP (primary)
- General NLP with biomedical applicability
- Small dataset scenarios
- Token classification / sequence labeling
- Transfer learning and domain adaptation

### 9.2 Key Research Areas

**1. Modern Biomedical Language Models**
- What are the state-of-the-art biomedical LMs in 2025?
- How do they compare to 2021 RoBERTa on NER and classification?
- Are there domain-specific models for database/resource mentions?
- What about newer architectures (e.g., models beyond BERT-style)?

**2. Parameter-Efficient Fine-Tuning**
- LoRA (Low-Rank Adaptation): Benefits for small datasets?
- QLoRA: 4-bit quantized training feasibility?
- Adapter layers: Pros/cons vs. full fine-tuning?
- Prefix tuning, prompt tuning: Applicable to our tasks?

**3. Modern Training Techniques**
- Optimizers: Lion, Sophia, AdamW8bit - better than standard AdamW?
- Schedulers: Cosine annealing with restarts, OneCycleLR?
- Regularization: Modern dropout variants, label smoothing?
- Mixed precision: bfloat16 vs. float16 for biomedical text?
- Layer-wise learning rate decay (LLRD): Benefits?

**4. Data Augmentation for Biomedical NER**
- Entity-preserving augmentation techniques
- Back-translation with entity protection
- Synonym replacement using biomedical embeddings
- GPT-4/Claude for synthetic data generation
- Active learning for strategic data expansion

**5. Small Dataset Optimization**
- Few-shot learning frameworks (SetFit, FLASH)
- Meta-learning (MAML, Reptile, ProtoNets)
- Self-training and pseudo-labeling
- Contrastive learning for better representations
- Knowledge distillation strategies

**6. Ensemble & Multi-Task Learning**
- Modern ensemble methods beyond averaging
- Joint training of classification + NER
- Cross-task knowledge transfer
- Uncertainty quantification and confidence calibration

### 9.3 Information to Gather

For each approach/technique, research should identify:

**Feasibility**:
- Implementation complexity (Low/Medium/High)
- Required expertise level
- Available libraries/tools
- Code examples or tutorials

**Performance Impact**:
- Expected F1 improvement (quantitative if available)
- Benefits for small datasets specifically
- Tradeoffs (e.g., speed vs. accuracy)
- Empirical results from papers

**Resource Requirements**:
- Computational cost (training time multiplier)
- Memory requirements
- GPU necessity (can it run on CPU?)
- Cost implications (APIs, paid services, etc.)

**Integration Effort**:
- Compatibility with current architecture
- Code changes required
- Data format changes needed
- Testing and validation needs

**Production Readiness**:
- Stability and maturity
- Community support and documentation
- Known issues or limitations
- Long-term maintenance considerations

---

## 10. Evaluation Criteria

### 10.1 How to Assess Recommendations

**Priority Assessment Matrix**:

| Criteria | Weight | Scoring |
|----------|--------|---------|
| Expected F1 Improvement | 30% | High (>5% gain) = 10pts, Medium (2-5%) = 5pts, Low (<2%) = 2pts |
| Implementation Complexity | 25% | Low = 10pts, Medium = 5pts, High = 2pts |
| Data Efficiency Benefit | 20% | High (helps small datasets) = 10pts, Medium = 5pts, Low = 2pts |
| Resource Cost | 15% | Low cost/time = 10pts, Medium = 5pts, High = 2pts |
| Production Feasibility | 10% | Ready now = 10pts, Near-term = 5pts, Research-stage = 2pts |

**Quick Wins** (High Priority):
- High expected impact + Low implementation complexity
- Examples: Better hyperparameters, simple data augmentation, existing libraries

**Strategic Improvements** (Medium Priority):
- High expected impact + Medium complexity
- Examples: Modern base models, parameter-efficient fine-tuning

**Research Opportunities** (Lower Priority):
- High potential but high complexity or uncertain impact
- Examples: Novel meta-learning approaches, custom architectures

### 10.2 Red Flags (Avoid)

**Avoid recommendations that**:
- Require massive computational resources (>>2x current cost)
- Need extensive labeled data (defeats purpose of data efficiency)
- Lack production-ready implementations
- Are highly experimental with no proven results
- Require paid APIs for core functionality (some augmentation ok)
- Are incompatible with Google Colab execution
- Would break backward compatibility without clear benefit

### 10.3 Ideal Recommendation Format

For each recommended approach, provide:

**1. Summary** (2-3 sentences)
- What it is and why it's relevant

**2. Expected Impact**
- Quantitative: Expected F1 improvement (with uncertainty)
- Qualitative: Other benefits (stability, efficiency, etc.)

**3. Implementation**
- Complexity rating: Low/Medium/High
- Required libraries/tools (with links)
- Key code changes needed
- Example code snippet or pseudocode

**4. Resources**
- Training time impact (multiplier, e.g., 1.2x current)
- Memory requirements
- Cost implications

**5. Evidence**
- Academic papers (with key results)
- GitHub repos (with star counts)
- Blog posts or tutorials
- Benchmark results

**6. Integration Guidance**
- Step-by-step integration approach
- Potential challenges
- Testing strategy
- Rollback plan if unsuccessful

---

## 11. Success Metrics

### 11.1 Research Phase Success

**Deliverables**:
- ✅ Comprehensive list of modern alternatives (ranked by priority)
- ✅ Top 3-5 actionable recommendations per research area
- ✅ Implementation guides for high-priority items
- ✅ Clear reasoning for each recommendation

**Quality Indicators**:
- Evidence-based (papers, repos, benchmarks)
- Specific to biomedical NLP and small datasets
- Actionable (not just theoretical)
- Prioritized (quick wins vs. long-term)

### 11.2 Implementation Phase Success

**Immediate Targets** (within 1-2 weeks):
- ✅ New models achieve F1 ≥ V2 models (0.749 NER, 0.898 classification)
- ✅ Training stability improved (no F1 bouncing)
- ✅ Reduced overfitting (train/val gap < 0.15)
- ✅ Early stopping implemented and tested

**Medium-Term Targets** (within 1-2 months):
- ✅ Data augmentation expands NER dataset to 1,000-1,500 samples
- ✅ At least one modern alternative implemented (e.g., LoRA, better optimizer)
- ✅ F1 improvement of 2-5% over V2 baseline
- ✅ Experimental training infrastructure validated

**Long-Term Vision** (3-6 months):
- ✅ Modernized training pipeline with 2025 best practices
- ✅ Robust to hyperparameter choices (less fragile)
- ✅ Data-efficient (high quality with limited samples)
- ✅ Clear roadmap for continued improvements

### 11.3 Documentation Success

**Required Documentation**:
- ✅ Research findings consolidated with actionable recommendations
- ✅ Implementation guides for adopted approaches
- ✅ Experimental results documented with comparisons
- ✅ Updated main documentation with modern approaches
- ✅ Lessons learned and future research directions

---

## 12. Appendix: Technical Details

### 12.1 Current Model Checksums (for reference)

**V2 Production Models** (Validated, Currently Used):
```
Classification: article_classifier_v2.pt
- MD5: ea57a1cab905c6d5c4e064204f3e160d
- Size: 476MB
- Test F1: 0.898

NER: named_entity_recognition_v2.pt
- MD5: fb53cb6c17db50d62bd90a4dcea83fa4
- Size: 473MB
- Test F1: 0.749
```

### 12.2 Example Data Samples

**Classification Example**:
```
Title: "The Gene Expression Omnibus: A Public Repository for Gene Expression Data"
Abstract: "The Gene Expression Omnibus (GEO) is a data repository that accepts array- and sequence-based data..."
Label: 1 (bio-resource paper)
```

**NER Example**:
```
Text: "We deposited the data in the Gene Expression Omnibus (GEO) database."
Tags: O O O O O O O B-FUL I-FUL I-FUL B-COM O O
Entities:
- FULL: "Gene Expression Omnibus" (positions 6-8)
- COMP: "GEO" (position 9)
```

### 12.3 Code Structure (for context)

**Key Files**:
- `src/class_train.py`: Classification model training script
- `src/ner_train.py`: NER model training script
- `src/class_predict.py`: Classification inference
- `src/ner_predict.py`: NER inference
- `src/training_utils.py`: Shared training utilities
- `full_training_pipeline_simplified.ipynb`: Main Google Colab training notebook

**Configuration**:
- `config/train_predict.yml`: Production training config
- `config/models_info.tsv`: Available base models

---

## 13. How to Use This Brief

### For AI Research Agents

**Step 1**: Read this entire brief to understand the project context

**Step 2**: Read your topic-specific brief (augmented research questions)

**Step 3**: Conduct research following the guidelines in Section 9

**Step 4**: Organize findings using the format in Section 10.3

**Step 5**: Prioritize recommendations using the matrix in Section 10.1

**Step 6**: Provide actionable next steps with implementation guidance

### Important Notes

**Focus on Actionability**: We need concrete recommendations we can implement, not just theoretical discussions

**Evidence-Based**: Every recommendation should cite papers, repos, or benchmarks

**Biomedical Specificity**: General NLP advances are interesting, but biomedical applications are critical

**Small Dataset Focus**: Techniques that help with 554 samples are especially valuable

**Cost-Conscious**: Free/open-source preferred, paid solutions need strong justification

---

**Document Status**: ✅ Ready for Research
**Last Updated**: 2025-10-29
**Next Review**: After research findings consolidated
**Contact**: See project maintainers in main repository documentation
