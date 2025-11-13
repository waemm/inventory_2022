# Research Brief: Data Augmentation for Biomedical NER

**Date**: 2025-10-29
**Research Topic**: Data augmentation strategies for small biomedical NER datasets
**Base Document**: [BASE_RESEARCH_BRIEF.md](BASE_RESEARCH_BRIEF.md) - **READ THIS FIRST**
**Research Agent**: Internet-researcher (comprehensive web research)
**Estimated Research Time**: 2-3 hours

---

## Overview

This brief focuses on data augmentation techniques to expand our critical bottleneck: the NER dataset with only **554 manually annotated samples**. The goal is to identify practical augmentation strategies that can expand this to 1,000-1,500 high-quality samples while preserving entity boundaries and BIO tag consistency.

**Critical Context**: Our NER model shows severe overfitting (train F1=0.974, val F1=0.621, gap=0.353) due to the small dataset. Data augmentation is a high-priority strategy to address this.

**Prerequisites**: Read [BASE_RESEARCH_BRIEF.md](BASE_RESEARCH_BRIEF.md) for complete project context.

---

## The Challenge

### Current NER Dataset

**Size**: 554 samples (manually annotated scientific abstracts)
**Entity Types**:
- **COM** (Compound names): Abbreviations like "GEO", "TCGA", "UniProt"
- **FUL** (Full names): Descriptive names like "Gene Expression Omnibus"
**Tag Scheme**: BIO format (O, B-COM, I-COM, B-FUL, I-FUL)
**Domain**: Biomedical/life sciences literature

**Example**:
```
Text: "We deposited the data in the Gene Expression Omnibus (GEO) database."
Tags: O O O O O O O B-FUL I-FUL I-FUL B-COM O O
```

**Key Constraints**:
- Entity boundaries must be preserved
- BIO tag consistency must be maintained
- Domain terminology must remain valid
- Augmented samples must be realistic (not obviously synthetic)
- Cannot violate scientific accuracy

**Goal**: Expand 554 samples → 1,000-1,500 samples while maintaining quality

---

## Research Questions

### 1. Entity-Preserving Augmentation Techniques

**Core Challenge**: Augment text while keeping entity spans and labels intact

**Research Questions**:

1.1. **What augmentation techniques work well for NER tasks?**
   - Entity-swap augmentation: Replace entities with similar entities?
   - Context modification: Change non-entity words while preserving entities?
   - Entity-aware paraphrasing: Rephrase sentences around entities?

1.2. **BIO Tag Consistency**:
   - How to maintain valid BIO sequences during augmentation?
   - Tools that automatically handle BIO tag adjustments?
   - Common pitfalls and how to avoid them?

1.3. **Biomedical-Specific Considerations**:
   - Preserving scientific accuracy during augmentation?
   - Avoiding creation of nonsensical biomedical statements?
   - Maintaining domain terminology correctness?

**Deliverable**:
- Top 3-5 entity-preserving augmentation techniques
- Implementation guides with code examples
- Quality validation strategies

---

### 2. Back-Translation for Biomedical Text

**Technique**: Translate text to intermediate language(s) and back to English

**Research Questions**:

2.1. **Effectiveness for Biomedical NER**:
   - Does back-translation preserve entity boundaries?
   - Best intermediate languages for scientific text?
   - Quality vs. other augmentation techniques?

2.2. **Entity Protection Strategies**:
   - How to prevent entity translation/corruption?
   - Pre-masking entities before translation?
   - Post-translation entity verification?

2.3. **Tools & APIs**:
   - **Google Translate API**: Cost and quality for biomedical text?
   - **MarianMT** (Hugging Face): Free, local, quality adequate?
   - **M2M100**: Multilingual, any benefits?
   - **NLLB** (No Language Left Behind): Better for scientific text?

2.4. **Practical Implementation**:
   - Pipeline: Extract entities → Translate → Restore entities → Verify BIO tags
   - Intermediate languages to try (French, German, Spanish, Chinese)?
   - Batch processing for 554 samples?
   - Expected augmentation ratio (2x, 3x, 5x)?

**Deliverable**:
- Recommended back-translation pipeline
- Tool/API recommendation with cost analysis
- Code example with entity protection
- Expected quality and augmentation ratio

---

### 3. Synonym Replacement (Biomedical Context-Aware)

**Technique**: Replace non-entity words with synonyms from biomedical vocabulary

**Research Questions**:

3.1. **Biomedical Word Embeddings**:
   - **BioWordVec**: Still state-of-the-art?
   - **BioSentVec**: Sentence-level embeddings useful?
   - **PubMedBERT embeddings**: Use for synonym finding?
   - Contextualized embeddings vs. static embeddings?

3.2. **Synonym Databases**:
   - **UMLS (Unified Medical Language System)**: Access and usage?
   - **BioPortal**: API for biomedical ontologies?
   - **WordNet** with biomedical filtering?

3.3. **Implementation Strategy**:
   - Identify non-entity words safe to replace?
   - Ensure grammatical correctness after replacement?
   - Context-aware vs. random synonym selection?
   - Replacement probability (e.g., 10-30% of eligible words)?

3.4. **Tools & Libraries**:
   - **nlpaug** library: BioWordVec integration?
   - **textaugment**: Suitable for NER?
   - Custom implementation needed?

**Deliverable**:
- Recommended synonym replacement approach
- Biomedical resource (BioWordVec, UMLS, etc.)
- Implementation guide with code
- Example augmented samples

---

### 4. Easy Data Augmentation (EDA) for NER

**Technique**: Simple rule-based augmentation (insertion, deletion, swap, replacement)

**Research Questions**:

4.1. **EDA Techniques Applicable to NER**:
   - **Random Insertion**: Insert biomedical terms in non-entity positions?
   - **Random Deletion**: Delete non-entity words safely?
   - **Random Swap**: Swap non-entity word positions?
   - **Synonym Replacement**: (covered in Section 3)

4.2. **Entity-Safe EDA**:
   - How to mark entity spans as protected regions?
   - Maintain BIO tag consistency after augmentation?
   - Sentence coherence after random operations?

4.3. **Parameter Tuning**:
   - Optimal alpha (augmentation strength) for NER?
   - Number of augmented samples per original?
   - Best combination of EDA operations?

4.4. **Tools**:
   - **nlpaug** library: EDA support for NER?
   - **eda_nlp**: Original implementation, NER-compatible?
   - Custom entity-aware implementation needed?

**Deliverable**:
- EDA operations safe for NER
- Recommended parameters
- Code implementation
- Quality assessment strategy

---

### 5. AEDA (An Easier Data Augmentation)

**Technique**: Insert random punctuation marks for implicit augmentation

**Research Questions**:

5.1. **AEDA for Token Classification**:
   - Original paper focused on classification, works for NER?
   - Punctuation insertion: Affects tokenization/BIO tags?
   - Better than EDA for small datasets?

5.2. **Implementation**:
   - Random punctuation set (comma, period, semicolon, ...)?
   - Insertion probability?
   - BIO tag handling after punctuation insertion?

5.3. **Effectiveness**:
   - Empirical results on NER tasks?
   - Computational efficiency vs. other methods?

**Deliverable**:
- AEDA applicability assessment for NER
- Implementation guide if applicable
- Expected benefit vs. complexity

---

### 6. LLM-Based Synthetic Data Generation

**Technique**: Use GPT-4, Claude, or similar LLMs to generate synthetic training samples

**Research Questions**:

6.1. **LLM Capabilities for Biomedical NER Data**:
   - **GPT-4**: Quality of generated biomedical text with entities?
   - **Claude**: Better understanding of entity boundaries?
   - **Open-source LLMs**: LLaMA, Mistral with biomedical fine-tuning?
   - **BioGPT**: Specialized biomedical text generation?

6.2. **Prompting Strategies**:
   - Few-shot prompting with example entity annotations?
   - Instruction prompting for entity generation?
   - Chain-of-thought for complex entity structures?
   - Example prompt templates?

6.3. **Entity Generation Quality**:
   - Do LLMs generate realistic database/resource names?
   - Accuracy of BIO tag generation?
   - Validation: How to verify generated samples?
   - Hallucination risk: Fake database names?

6.4. **Practical Considerations**:
   - **Cost**: API costs for generating ~500-1,000 samples?
   - **Quality Control**: Manual review needed percentage?
   - **Diversity**: Avoid repetitive generations?
   - **Ethical**: Using LLM-generated data for training acceptable?

6.5. **Workflow**:
   - Prompt engineering → Generate candidates → Validate → Filter → Integrate
   - Batch generation strategies?
   - Human-in-the-loop validation?

**Deliverable**:
- Recommended LLM and approach
- Prompt templates with examples
- Cost analysis (API calls needed)
- Quality control strategy
- Integration workflow
- Priority assessment (High/Medium/Low)

---

### 7. Contextual Word Embeddings & Masked Language Modeling

**Technique**: Use BERT/RoBERTa to generate augmented samples via masked token prediction

**Research Questions**:

7.1. **MLM-Based Augmentation**:
   - Mask non-entity tokens, predict replacements with biomedical BERT?
   - Use PubMedBERT or BioBERT for higher quality?
   - Entity span protection during masking?

7.2. **Implementation**:
   - Random masking probability (e.g., 15% of non-entity tokens)?
   - Top-k sampling from MLM predictions (k=5-10)?
   - Batch processing efficiency?

7.3. **Quality & Diversity**:
   - More diverse than synonym replacement?
   - Contextual appropriateness?
   - Fluency validation?

7.4. **Tools**:
   - Transformers library: Straightforward implementation?
   - Existing libraries with MLM augmentation?

**Deliverable**:
- MLM augmentation feasibility assessment
- Implementation guide if promising
- Expected quality and diversity

---

### 8. Active Learning for Strategic Data Collection

**Not Augmentation, but Related**: Intelligently select which samples to manually annotate next

**Research Questions**:

8.1. **Active Learning Strategies for NER**:
   - **Uncertainty sampling**: Select samples with low model confidence?
   - **Query-by-committee**: Multiple models, select disagreement cases?
   - **Diversity sampling**: Select diverse entity types/contexts?

8.2. **Practical Application**:
   - Given 554 annotated + large unannotated pool (21,677 papers)?
   - Identify next 100-200 highest-value samples to annotate?
   - Tools: modAL, ALiPy libraries?

8.3. **ROI Assessment**:
   - Effort: Same annotation time as augmentation development?
   - Benefit: Higher quality than synthetic data?
   - Combination: Active learning + augmentation?

**Deliverable**:
- Active learning strategy recommendation
- Tool/library suggestions
- Comparison vs. data augmentation
- Priority in overall strategy

---

### 9. Mixup & Manifold Mixup for Text

**Technique**: Interpolate between training examples in embedding space

**Research Questions**:

9.1. **Text Mixup Variants**:
   - **Embedding-level mixup**: Interpolate token embeddings?
   - **Sentence-level mixup**: Average sentence representations?
   - **Seq2Mix**: Sequence-to-sequence mixup?

9.2. **Applicability to NER**:
   - How to handle label interpolation for BIO tags?
   - Soft labels for token classification?
   - Evidence of effectiveness on NER tasks?

9.3. **Implementation Complexity**:
   - Requires training pipeline modifications?
   - On-the-fly during training vs. pre-augmentation?

**Deliverable**:
- Mixup viability assessment for NER
- Implementation approach if applicable
- Expected benefit vs. simpler methods

---

### 10. Data Augmentation Libraries & Tools

**Research Question**: What are the best ready-to-use tools for NER augmentation?

**Libraries to Evaluate**:

10.1. **nlpaug**:
   - Features: Character, word, sentence augmentation
   - NER compatibility?
   - Biomedical support (BioWordVec integration)?
   - Ease of use?
   - Code examples for token classification?

10.2. **TextAttack**:
   - Adversarial augmentation: Useful for robustness?
   - NER support?
   - Complexity?

10.3. **TextAugment**:
   - Simple EDA implementation?
   - NER-compatible?

10.4. **Biomedical-Specific Tools**:
   - Any specialized libraries for biomedical NER augmentation?
   - scispaCy integration possibilities?

10.5. **Custom vs. Library**:
   - When to use libraries vs. build custom?
   - Library limitations for BIO tagging?

**Deliverable**:
- Recommended library (if any)
- Feature comparison table
- Code examples for our use case
- Custom implementation needs

---

## Augmentation Validation Strategy

**Critical**: How do we ensure augmented data is high quality?

**Research Questions**:

11.1. **Automatic Validation**:
- BIO tag consistency checks?
- Entity span validation?
- Sentence fluency scoring?
- Domain terminology validation (biomedical term checker)?

11.2. **Manual Review**:
- What percentage needs human review (10%, 25%, 50%)?
- Review criteria and guidelines?
- Efficient review workflows?

11.3. **Quality Metrics**:
- Augmented sample diversity measurement?
- Similarity to original data (avoid near-duplicates)?
- Model performance on augmented data (validation strategy)?

**Deliverable**:
- Validation workflow
- Quality metrics and thresholds
- Review guidelines

---

## Implementation Roadmap

### Phase 1: Quick Wins (1-2 days implementation)
- Identify 1-2 simplest high-impact techniques
- Implement with basic validation
- Test on small subset (50 samples → 100-150)
- Evaluate quality

### Phase 2: Comprehensive Augmentation (1 week)
- Implement top 3-5 techniques
- Generate 1,000-1,500 total samples
- Comprehensive validation
- Create train/val/test splits

### Phase 3: Quality Assurance (2-3 days)
- Manual review of sample (10-20%)
- Validate with model training
- Iterate on augmentation parameters
- Finalize augmented dataset

---

## Success Criteria

**Your research is successful if it provides**:

1. ✅ **Top 3-5 augmentation techniques** ranked by:
   - Expected quality (how realistic are augmented samples?)
   - Implementation complexity (hours to implement)
   - Augmentation ratio (how many samples per original?)
   - Entity preservation reliability

2. ✅ **Complete implementation guide** for #1 ranked technique:
   - Step-by-step instructions
   - Code examples with entity protection
   - BIO tag handling
   - Validation strategy

3. ✅ **Tool recommendations**:
   - Libraries to use (with versions)
   - APIs if needed (with cost estimates)
   - Custom code requirements

4. ✅ **Target Deliverable**:
   - Clear path to generating 1,000-1,500 samples from 554 originals
   - Expected quality assessment
   - Implementation timeline
   - Resource requirements (time, cost, compute)

5. ✅ **Validation strategy**:
   - Automatic checks
   - Manual review workflow
   - Quality metrics

---

## Key Constraints (from Base Brief)

**Remember**:
- Must preserve entity boundaries precisely
- BIO tag consistency is critical
- Domain accuracy (biomedical terminology)
- Avoid obvious synthetic artifacts
- Cost-effective (free or low-cost tools preferred)
- Implementable in 1-2 weeks
- Colab-friendly (no heavy infrastructure)

---

## Expected Deliverable

**Comprehensive Report** including:

1. **Summary Table**:
   | Technique | Quality | Complexity | Ratio | Cost | Priority |
   |-----------|---------|------------|-------|------|----------|
   | Example   | High    | Low        | 2x    | Free | HIGH     |

2. **Detailed Guides** for top 3-5 techniques

3. **Implementation Roadmap** with timeline

4. **Code Examples** (working snippets)

5. **Validation Strategy** (automatic + manual)

6. **Final Recommendation**: Which technique(s) to implement first

---

## Research Methodology

### Step 1: Literature Review
- "data augmentation NER", "biomedical NER augmentation", "entity-preserving augmentation"
- Recent papers (2023-2025) on small-dataset NER
- BioNLP workshop papers

### Step 2: Tool Discovery
- GitHub search for NER augmentation tools
- Hugging Face models for biomedical text generation
- NLP augmentation libraries (nlpaug, TextAttack, etc.)

### Step 3: Case Studies
- Find examples of successful NER augmentation (biomedical domain)
- Check papers with code - NER augmentation implementations
- Industry blog posts (Hugging Face, Snorkel, etc.)

### Step 4: Cost-Benefit Analysis
- API costs for LLM-based generation
- Development time for each technique
- Expected quality and performance improvement

---

**Document Status**: ✅ Ready for Research
**Research Agent**: Internet-researcher
**Priority**: HIGH (critical bottleneck for NER quality)
**Timeline**: 2-3 hours research + comprehensive report
