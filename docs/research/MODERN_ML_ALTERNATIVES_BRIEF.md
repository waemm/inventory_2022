# Research Brief: Modern ML Alternatives for Biomedical NLP

**Date**: 2025-10-29
**Research Topic**: Modern machine learning approaches, models, and techniques (2023-2025)
**Base Document**: [BASE_RESEARCH_BRIEF.md](BASE_RESEARCH_BRIEF.md) - **READ THIS FIRST**
**Research Agent**: Internet-researcher (comprehensive web research)
**Estimated Research Time**: 2-3 hours

---

## Overview

This brief augments the base research brief with specific questions about modern ML alternatives that have emerged since our 2022 codebase was developed. The goal is to identify state-of-the-art approaches for biomedical NLP that could improve our classification and NER tasks.

**Prerequisites**: Read [BASE_RESEARCH_BRIEF.md](BASE_RESEARCH_BRIEF.md) for complete project context.

---

## Research Questions

### 1. Modern Biomedical Language Models (2023-2025)

**Current Baseline**: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500` (2021, RoBERTa-base, 125M params)

**Research Questions**:

1.1. **What are the newest biomedical language models released in 2023-2025?**
   - BioGPT-2, Bio

Megatron, PubMedBERT-large, BioLinkBERT?
   - Any models specifically trained on database/resource mentions?
   - Models with improved domain adaptation strategies?
   - Lighter models that still maintain quality (distilled versions)?

1.2. **How do recent models compare on biomedical NER and classification tasks?**
   - BLURB benchmark results (2023-2025 papers)
   - BLUE benchmark comparisons
   - BioNLP shared task results
   - Any head-to-head comparisons with 2021 RoBERTa?

1.3. **Are there models beyond the BERT/RoBERTa architecture worth considering?**
   - Decoder-only models (GPT-style) fine-tuned for biomedical tasks?
   - Encoder-decoder models (T5-style) for sequence tagging?
   - Retrieval-augmented models?
   - Mixture of experts approaches?

1.4. **What about model size tradeoffs?**
   - Large models (300M+ params): Worth the computational cost?
   - Small models (< 100M params): Adequate for our tasks?
   - Optimal size for 1,635 classification and 554 NER samples?

1.5. **Domain specialization**:
   - Models pre-trained on specific biomedical subdomains?
   - Continued pre-training strategies for resource mention detection?
   - Any models trained on database/repository metadata?

**Deliverable**: Ranked list of 3-5 promising biomedical LMs with:
- Model name, size, release date
- Pre-training strategy and corpus
- Benchmark results (especially NER and classification)
- Availability (Hugging Face, GitHub, etc.)
- Expected performance improvement over our 2021 baseline
- Computational requirements (GPU memory, inference speed)
- Integration complexity (Low/Medium/High)

---

### 2. Parameter-Efficient Fine-Tuning (PEFT)

**Current Approach**: Full fine-tuning of all 125M parameters

**Research Questions**:

2.1. **LoRA (Low-Rank Adaptation)**:
   - What is the current state of LoRA for NLP tasks?
   - Performance comparison vs. full fine-tuning on small datasets?
   - Typical rank values (r) for BERT-size models?
   - Benefits: Faster training, lower memory, better generalization?
   - Hugging Face PEFT library: Maturity and ease of use?
   - Code examples for token classification with LoRA?

2.2. **QLoRA (Quantized LoRA)**:
   - Can we train with 4-bit quantization on T4 GPUs?
   - Quality tradeoffs: How much F1 loss is typical?
   - Memory savings: Fit larger models in Colab?
   - Training time impact?
   - BitsAndBytes library integration?

2.3. **Other PEFT Methods**:
   - **Adapter Layers**: Better than LoRA for our use case?
   - **Prefix Tuning**: Applicable to classification and NER?
   - **Prompt Tuning**: Viable for token classification?
   - **IA³ (Infused Adapter)**: Worth considering?

2.4. **PEFT for Small Datasets**:
   - Does PEFT help prevent overfitting with 554 samples?
   - Empirical results on small-dataset scenarios?
   - Best practices for hyperparameter selection with PEFT?

**Deliverable**: For each PEFT method:
- Description and how it works
- Expected performance vs. full fine-tuning
- Memory and training time savings
- Implementation complexity with Hugging Face PEFT
- Recommended use case (classification, NER, both, neither)
- Code snippet showing integration

---

### 3. Modern Optimizers

**Current Approach**: AdamW with fixed hyperparameters (LR=2e-5, WD=0.0)

**Research Questions**:

3.1. **Lion Optimizer**:
   - What is Lion and how does it differ from AdamW?
   - Performance on NLP tasks (especially small datasets)?
   - Memory requirements vs. AdamW?
   - Typical hyperparameters for BERT-size models?
   - Available implementations (PyTorch)?
   - Any biomedical NLP papers using Lion?

3.2. **Sophia Optimizer**:
   - Second-order optimization: Benefits for fine-tuning?
   - Computational overhead vs. Adam/AdamW?
   - Works well on small datasets?
   - Stability and ease of use?
   - Production readiness?

3.3. **AdamW Variants**:
   - **AdamW8bit** (bitsandbytes): Quality vs. memory tradeoff?
   - **Adafactor**: Lower memory, comparable performance?
   - **AdaBelief**: Better convergence than AdamW?

3.4. **Best Practices for Optimizer Selection**:
   - Which optimizer for small classification datasets (1,635 samples)?
   - Which for small NER datasets (554 samples)?
   - Recommended learning rates for each optimizer?
   - Weight decay recommendations by optimizer?

**Deliverable**: Comparison table with:
- Optimizer name and key characteristics
- Memory requirements (relative to AdamW)
- Training speed (relative to AdamW)
- Expected performance benefit
- Recommended learning rate range
- Best use case (classification, NER, general)
- Implementation guide (library, code example)
- Priority rating (High/Medium/Low)

---

### 4. Advanced Learning Rate Schedules

**Current Approach**: Linear warmup (10% of steps) + linear decay

**Research Questions**:

4.1. **Cosine Annealing with Warm Restarts**:
   - Benefits over linear decay for fine-tuning?
   - Typical restart schedule for 10-20 epoch training?
   - Helps escape local minima?
   - PyTorch implementation: CosineAnnealingWarmRestarts?

4.2. **OneCycleLR**:
   - One-cycle policy: Suitable for our training duration?
   - Typical max LR and cycle configuration?
   - Faster convergence than linear schedules?
   - Works well with early stopping?

4.3. **Polynomial Decay**:
   - Benefits over linear decay?
   - Typical power parameter?

4.4. **Layer-wise Learning Rate Decay (LLRD)**:
   - Different learning rates per layer: Why beneficial?
   - Typical decay factor (e.g., 0.95 per layer)?
   - Implementation complexity?
   - Performance improvement on small datasets?

4.5. **Warmup Strategies**:
   - Optimal warmup duration for small datasets?
   - Linear vs. exponential warmup?
   - Impact on training stability?

**Deliverable**: For each scheduler:
- Description and rationale
- When to use vs. linear schedule
- Hyperparameter recommendations
- Expected benefits (convergence speed, final performance)
- Implementation complexity
- Code example with PyTorch

---

### 5. Mixed Precision Training

**Current Approach**: Standard float32 training

**Research Questions**:

5.1. **Automatic Mixed Precision (AMP)**:
   - PyTorch AMP: Easy integration?
   - Training speed improvement on T4/V100/A100?
   - Memory savings?
   - Quality impact for biomedical text?

5.2. **bfloat16 vs. float16**:
   - Which is better for NLP fine-tuning?
   - Hardware support (T4 supports bfloat16)?
   - Numerical stability differences?

5.3. **Best Practices**:
   - Gradient scaling: Necessary for NER training?
   - Loss scaling strategies?
   - Known issues with mixed precision for token classification?

**Deliverable**:
- Recommended precision type (float32, float16, bfloat16)
- Expected speedup by GPU type (T4, V100, A100)
- Implementation guide with PyTorch
- Potential pitfalls and how to avoid them

---

### 6. Gradient Accumulation Strategies

**Current Approach**: Batch size 16, no gradient accumulation

**Research Questions**:

6.1. **When to Use Gradient Accumulation**:
   - Benefits beyond memory constraints?
   - Effective batch size recommendations for our tasks?
   - Impact on training dynamics vs. increasing batch size directly?

6.2. **Best Practices**:
   - Accumulation steps for small datasets?
   - Interaction with learning rate and schedulers?
   - Batch normalization considerations?

**Deliverable**:
- Recommended strategy for our use case
- Effective batch size targets
- Implementation notes

---

### 7. Regularization Techniques

**Current Issue**: Overfitting on 554 NER samples (train F1=0.974, val F1=0.621)

**Research Questions**:

7.1. **Modern Dropout Variants**:
   - **DropConnect**: Better than standard dropout?
   - **Variational Dropout**: Benefits for RNNs, applicable to Transformers?
   - **DropBlock**: Structural dropout for Transformers?

7.2. **Label Smoothing**:
   - Effective for classification tasks?
   - Applicable to NER (multi-class token classification)?
   - Typical smoothing parameter?

7.3. **Mixup / Manifold Mixup**:
   - Applicability to text classification and NER?
   - TextMixup implementations?
   - Benefits for small datasets?

7.4. **Weight Decay Best Practices**:
   - Optimal weight decay for 554-sample dataset?
   - Layer-specific weight decay?
   - Interaction with LoRA / PEFT?

7.5. **Early Stopping**:
   - Best patience values for small datasets?
   - Metric to monitor (val loss vs. val F1)?
   - Save best model vs. ensemble of checkpoints?

**Deliverable**:
- Top 3 regularization techniques for small NER dataset
- Hyperparameter recommendations
- Expected overfitting reduction
- Implementation complexity

---

### 8. Modern Training Frameworks & Libraries

**Current Stack**: PyTorch 2.2.2, Transformers 4.35.0, manual training loops

**Research Questions**:

8.1. **Hugging Face Transformers 4.x Features**:
   - New features since 4.35.0 (current version)?
   - Trainer class: Benefits vs. custom training loops?
   - Integration with PEFT, Accelerate, Optimum?

8.2. **Hugging Face PEFT Library**:
   - Maturity and production readiness?
   - Ease of integration?
   - Support for LoRA, QLoRA, adapters?
   - Code examples for token classification?

8.3. **Hugging Face Accelerate**:
   - Simplifies distributed/mixed precision training?
   - Benefits for single-GPU Colab training?
   - Integration overhead?

8.4. **PyTorch Lightning**:
   - Worth switching from raw PyTorch?
   - Benefits: cleaner code, better logging, easier experiments?
   - Overhead and learning curve?

8.5. **Weights & Biases (W&B) / MLflow**:
   - Experiment tracking: Worth the integration effort?
   - Free tier sufficient for our needs?
   - Better than manual logging?

**Deliverable**:
- Recommended framework upgrades
- Benefits vs. current approach
- Migration effort
- Priority (Must-have, Nice-to-have, Skip)

---

### 9. Quantization for Deployment

**Current Deployment**: Full precision models (float32, ~475MB each)

**Research Questions**:

9.1. **Post-Training Quantization**:
   - Int8 quantization: Quality impact for our tasks?
   - Tools: PyTorch quantization, ONNX Runtime?
   - Inference speedup on CPU?

9.2. **Quantization-Aware Training (QAT)**:
   - Worth the training complexity?
   - Better quality than post-training quantization?

9.3. **ONNX Conversion**:
   - Benefits for deployment?
   - Compatibility with Transformers models?
   - Inference speedup?

**Deliverable**:
- Recommended quantization approach (if any)
- Expected model size reduction
- Quality impact (F1 loss)
- Inference speedup estimates
- Priority for our use case

---

### 10. Evaluation & Monitoring Tools

**Current Approach**: Manual evaluation with seqeval for NER, sklearn for classification

**Research Questions**:

10.1. **Better Evaluation Frameworks**:
   - Modern NER evaluation libraries?
   - Confidence calibration metrics?
   - Uncertainty quantification tools?

10.2. **Training Monitoring**:
   - Real-time training curve visualization (beyond Colab)?
   - Anomaly detection in training metrics?
   - Automated hyperparameter suggestions?

10.3. **Model Interpretability**:
   - Attention visualization for entity extraction?
   - Error analysis tools?
   - Feature importance for classification?

**Deliverable**:
- Top 2-3 tools worth integrating
- Benefits for our workflow
- Integration complexity

---

## Research Methodology

### Step 1: Literature Review
- Search for "biomedical NLP 2024", "biomedical NER 2025", "PubMedBERT", "BioGPT"
- Check recent conference proceedings (ACL, EMNLP, BioNLP 2024)
- Review preprints on arXiv and bioRxiv

### Step 2: GitHub & Hugging Face
- Search Hugging Face Model Hub for biomedical models
- Check GitHub for popular biomedical NLP repositories (stars > 100)
- Look for updated implementations of classic approaches

### Step 3: Blog Posts & Tutorials
- Hugging Face blog for PEFT tutorials
- Google Research, Microsoft Research blogs
- Fast.ai, Weights & Biases blogs

### Step 4: Benchmarks & Leaderboards
- BLURB leaderboard (if active)
- Papers With Code - biomedical NER tasks
- Check for recent shared task results

---

## Deliverable Format

For each research area (1-10 above), provide:

### Summary Table
| Approach | Expected Benefit | Implementation Complexity | Resource Cost | Priority |
|----------|------------------|--------------------------|---------------|----------|
| Example | +3-5% F1 | Low | 1.2x training time | HIGH |

### Detailed Recommendations

For top 3-5 items per area:

**1. [Approach Name]**

**What it is**: Brief description (2-3 sentences)

**Why it's relevant**: How it addresses our problems

**Expected Impact**:
- F1 improvement: +X% (quantitative if available)
- Other benefits: stability, speed, etc.

**Implementation**:
- Complexity: Low/Medium/High
- Required libraries: [list with versions]
- Key code changes: [description]
- Code example: [snippet or link]

**Resources**:
- Training time: X.Xx current
- Memory: +/- X GB
- Cost: Free / Colab Pro / Paid API

**Evidence**:
- Papers: [citations with key results]
- GitHub: [repos with star counts]
- Blog posts: [links]
- Benchmarks: [results]

**Integration Steps**:
1. [Step-by-step guide]
2. ...

**Risks & Mitigation**:
- [Potential issues and how to handle them]

---

## Success Criteria

Your research is successful if it provides:

1. ✅ **Actionable recommendations**: We can implement immediately or plan to implement
2. ✅ **Evidence-based**: Every claim backed by papers, repos, or benchmarks
3. ✅ **Prioritized**: Clear HIGH/MEDIUM/LOW priority based on impact vs. effort
4. ✅ **Specific**: Not generic advice, tailored to biomedical NLP and small datasets
5. ✅ **Comprehensive**: Covers all 10 research areas above
6. ✅ **Realistic**: Feasible with Google Colab and our constraints

---

## Key Constraints (from Base Brief)

**Remember**:
- Small NER dataset: 554 samples (critical constraint)
- Classification dataset: 1,635 samples (adequate)
- Google Colab execution (T4/V100/A100 GPUs)
- Cost-conscious (prefer free/open-source)
- Biomedical domain specificity required
- Must maintain backward compatibility

---

## Timeline

**Research Duration**: 2-3 hours
**Deliverable**: Comprehensive report following format above
**Next Steps**: Findings will be consolidated with other research briefs into master recommendations document

---

**Document Status**: ✅ Ready for Research
**Research Agent**: Internet-researcher
**Priority**: HIGH (foundational for all other improvements)
