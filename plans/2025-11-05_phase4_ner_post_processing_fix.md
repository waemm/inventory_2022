# Phase 4 NER Post-Processing Implementation Plan

**Date:** 2025-11-05
**Author:** Claude Code
**Status:** Implementation Ready
**Priority:** High

---

## Executive Summary

Phase 4 multi-task model achieves excellent NER performance (F1=0.9274, +23.82% vs V2) but outputs raw BPE tokens with severe duplication issues (2-7x per entity). This plan implements V2's proven word-level reconstruction approach to produce clean, production-ready entity extractions.

---

## Problem Statement

### Current Phase 4 Output Issues

**Example: PMID 34741192**
- **Current Output:** `"ĠRat, ĠGen, ome, ĠDatabase, ĠRat, ĠGen, ome, ĠDatabase"` (repeated 2x)
- **Expected Output:** `"Rat Genome Database"` (once, clean)

**Observed Issues:**
1. **BPE tokenization artifacts:** Ġ prefix characters in output
2. **Massive duplication:** Same entity repeated 2-7 times per paper
3. **No quality filtering:** URLs, single-chars, overly long entities not removed
4. **Not production-ready:** Requires manual cleanup before downstream use

### Impact
- 20,891 NER predictions contain ~40,000-60,000 entity instances (est. 2-3x duplication)
- Downstream URL extraction and name processing cannot handle duplicated entities
- Manual comparison shows Phase 4 finds correct entities but with poor post-processing

---

## Root Cause Analysis

### Investigation Summary

**V2 Pipeline (Clean Output):**
```
src/ner_predict.py:
  predict_sequence() → convert_predictions() → deduplicate() → reformat_output()

Key: Uses word-level reconstruction via tokenizer.word_ids() and word_to_chars()
```

**Phase 4 Pipeline (Raw BPE Output):**
```
src/multitask_predict.py:
  run_ner_inference() → extract_entities_from_bio_tags()

Issue: Direct token concatenation without word-level aggregation
```

### Technical Root Causes

1. **Token-Level Concatenation (Phase 4):**
   ```python
   # Current Phase 4 approach (WRONG)
   tokens = ["Ġ Rat", "ĠGen", "ome", "ĠDatabase"]
   entity = " ".join(tokens)  # "Ġ Rat Ġ Gen ome ĠDatabase"
   ```

2. **Word-Level Reconstruction (V2):**
   ```python
   # V2 approach (CORRECT)
   word_ids = tokenizer.word_ids()  # [0, 1, 1, 2]
   word_to_chars(1)  # CharSpan(start=4, end=10)
   entity = text[4:10]  # "Genome" (clean from original text)
   ```

3. **No Deduplication:** Phase 4 outputs every token-level prediction without within-paper deduplication

4. **No Quality Filtering:** V2 filters single-chars, URLs, >100 char entities

---

## Solution: Hybrid Approach (Option B)

**Strategy:** Adapt V2's word-level reconstruction for Phase 4's batch processing architecture

### Why This Approach?

| Criteria | Assessment |
|----------|------------|
| **Proven** | V2 production for 2+ years, 90%+ precision |
| **Root Cause Fix** | Solves tokenization at source (word-level) |
| **Code Reuse** | V2's deduplicate() and reformat_output() work as-is |
| **Risk** | Low - well-understood algorithm |
| **Effort** | 2-3 hours implementation + testing |

---

## Implementation Plan

### Phase 1: Word-Level Extraction Function (1 hour)

**File:** `src/multitask_predict.py`
**New Function:** `extract_entities_word_level()`

**Implementation:**
```python
def extract_entities_word_level(
    text: str,
    tokenizer,
    input_ids: torch.Tensor,
    bio_tags: List[int],
    probabilities: List[float],
    id2tag: Dict[int, str]
) -> List[Tuple[str, str, float]]:
    """
    Extract entities using word-level reconstruction (V2 approach).

    Args:
        text: Original text string
        tokenizer: HuggingFace tokenizer
        input_ids: Token IDs [seq_len]
        bio_tags: BIO tag IDs [seq_len]
        probabilities: Token-level probabilities [seq_len]
        id2tag: Mapping from tag IDs to tag strings

    Returns:
        List of (entity_text, entity_type, avg_confidence) tuples
    """
    # Step 1: Get word-level mappings
    encoding = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    word_ids = encoding.word_ids()[1:-1]  # Skip [CLS] and [SEP]

    # Step 2: Build word_locs dict
    word_locs = {}
    for word_id in set(word_ids):
        if word_id is not None:
            word_locs[word_id] = encoding.word_to_chars(word_id)

    # Step 3: Process word-by-word (not token-by-token!)
    entities = []
    current_entity = None

    for word_id in sorted(word_locs.keys()):
        # Find all tokens for this word
        token_indices = [i for i, wid in enumerate(word_ids) if wid == word_id]

        # Get tags and probs for this word's tokens
        word_tags = [id2tag[bio_tags[i+1]] for i in token_indices]  # +1 for [CLS]
        word_probs = [probabilities[i+1] for i in token_indices]

        # Determine word's BIO tag (prioritize B-tags, then I-tags)
        if any(tag.startswith('B-') for tag in word_tags):
            word_tag = next(tag for tag in word_tags if tag.startswith('B-'))
        elif any(tag.startswith('I-') for tag in word_tags):
            word_tag = next(tag for tag in word_tags if tag.startswith('I-'))
        else:
            word_tag = 'O'

        # Extract clean word text from original string
        span = word_locs[word_id]
        word_text = text[span.start:span.end]

        # Entity assembly logic (same as V2)
        if word_tag.startswith('B-'):
            if current_entity:
                entities.append(current_entity)

            entity_type = word_tag[2:]  # 'RESOURCE' for Phase 4
            current_entity = {
                'text': word_text,
                'type': entity_type,
                'probs': word_probs
            }

        elif word_tag.startswith('I-') and current_entity:
            entity_type = word_tag[2:]
            if entity_type == current_entity['type']:
                current_entity['text'] += ' ' + word_text
                current_entity['probs'].extend(word_probs)
            else:
                # Type mismatch - start new entity
                entities.append(current_entity)
                current_entity = {
                    'text': word_text,
                    'type': entity_type,
                    'probs': word_probs
                }

        else:  # O tag
            if current_entity:
                entities.append(current_entity)
                current_entity = None

    # Don't forget last entity
    if current_entity:
        entities.append(current_entity)

    # Calculate average confidence and apply V2 quality filters
    results = []
    for ent in entities:
        entity_text = ent['text'].strip()
        avg_prob = sum(ent['probs']) / len(ent['probs'])

        # V2 quality filters
        if (len(entity_text) > 1 and
            'http' not in entity_text.lower() and
            len(entity_text) <= 100):
            results.append((entity_text, ent['type'], avg_prob))

    return results
```

**Key Features:**
- ✅ Word-level aggregation (no BPE artifacts)
- ✅ Clean text extraction from original string
- ✅ Token probability averaging at word level
- ✅ V2 quality filters (length, URLs)
- ✅ Proper entity boundary detection

---

### Phase 2: Update Inference Pipeline (30 min)

**File:** `src/multitask_predict.py`
**Function:** `run_ner_inference()`

**Changes:**
1. Replace `extract_entities_from_bio_tags()` call with `extract_entities_word_level()`
2. Pass additional parameters: `text`, `tokenizer`, `id2tag`
3. Maintain batch processing architecture

**Modified Section:**
```python
# In run_ner_inference(), inside batch loop:
for i in range(len(batch['id'])):
    # Get predictions for this sequence
    seq_preds = preds[i].cpu().numpy()
    seq_probs = probs[i].cpu().numpy()
    token_probs = [seq_probs[j, seq_preds[j]] for j in range(len(seq_preds))]

    # NEW: Word-level extraction with proper detokenization
    entities = extract_entities_word_level(
        text=batch['text'][i] if 'text' in batch else batch['abstract'][i],
        tokenizer=tokenizer,
        input_ids=input_ids[i],
        bio_tags=seq_preds.tolist(),
        probabilities=token_probs,
        id2tag=id2tag
    )

    # Separate entities by type
    com_entities = [e for e in entities if e[1] == 'RESOURCE']

    # Format output (rest stays same)
    if com_entities:
        common_names = ', '.join([e[0] for e in com_entities])
        common_probs = ', '.join([f'{e[2]:.3f}' for e in com_entities])
    else:
        common_names = ''
        common_probs = ''

    # ... rest of result building
```

---

### Phase 3: Add Deduplication Step (30 min)

**File:** `src/multitask_predict.py`
**New Function:** `deduplicate_phase4_output()`

**Implementation:**
```python
def deduplicate_phase4_output(ner_results: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate Phase 4 NER output using V2's proven deduplication logic.

    Args:
        ner_results: DataFrame with columns [ID, common_name, common_prob, ...]

    Returns:
        Deduplicated DataFrame in same format
    """
    from ner_predict import deduplicate, reformat_output

    # Convert Phase 4 wide format to V2 long format
    long_format = []
    for _, row in ner_results.iterrows():
        # Parse common_name entities (Phase 4 uses common_name for RESOURCE)
        if pd.notna(row['common_name']) and row['common_name']:
            names = [n.strip() for n in row['common_name'].split(',') if n.strip()]
            probs = [p.strip() for p in row['common_prob'].split(',') if p.strip()]

            for name, prob in zip(names, probs):
                long_format.append({
                    'ID': row['ID'],
                    'mention': name,
                    'label': 'COM',  # V2 format expects COM/FUL
                    'prob': float(prob)
                })

    if not long_format:
        return ner_results

    # Apply V2 deduplication (unchanged!)
    long_df = pd.DataFrame(long_format)
    deduped_df = deduplicate(long_df)

    # Convert back to Phase 4 wide format
    results = []
    for paper_id in deduped_df['ID'].unique():
        paper_entities = deduped_df[deduped_df['ID'] == paper_id]

        # Get original row data
        orig_row = ner_results[ner_results['ID'] == paper_id].iloc[0]

        # Rebuild entity strings
        entities = paper_entities.to_dict('records')
        common_names = ', '.join([e['mention'] for e in entities])
        common_probs = ', '.join([f"{e['prob']:.3f}" for e in entities])

        results.append({
            'ID': paper_id,
            'title': orig_row.get('title', ''),
            'abstract': orig_row.get('abstract', ''),
            'publication_date': orig_row.get('publication_date', ''),
            'common_name': common_names,
            'common_prob': common_probs,
            'full_name': '',
            'full_prob': ''
        })

    return pd.DataFrame(results)
```

**Integration:**
```python
# In main() or run_phase4_ner():
ner_results = run_ner_inference(model, dataloader, tokenizer, device)
ner_results_deduped = deduplicate_phase4_output(ner_results)
```

---

### Phase 4: Testing & Validation (1 hour)

**Test Cases:**

1. **Unit Test: Word-Level Extraction**
   ```python
   def test_word_level_extraction():
       text = "The Rat Genome Database (RGD) is a resource."
       # Mock tokenizer, tags, probs
       entities = extract_entities_word_level(...)
       assert entities[0][0] == "Rat Genome Database"
       assert "Ġ" not in entities[0][0]  # No BPE artifacts
   ```

2. **Integration Test: Deduplication**
   ```python
   def test_deduplication():
       # Input with duplicates
       df = pd.DataFrame({
           'ID': [123, 123],
           'common_name': ['RGD, RGD, RGD', 'RGD'],
           'common_prob': ['0.99, 0.99, 0.99', '0.98']
       })
       result = deduplicate_phase4_output(df)
       assert result.loc[0, 'common_name'] == 'RGD'  # Only once
   ```

3. **End-to-End Test: Real Phase 4 Output**
   ```python
   # Load Phase 4 model
   # Run on 10 sample papers
   # Verify:
   # - No BPE artifacts (Ġ) in output
   # - Duplication reduced by 2-7x
   # - Entity quality matches V2 standards
   ```

---

## Expected Results

### Quantitative Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Entities per paper** | 2-14 (duplicated) | 1-2 (clean) | 2-7x reduction |
| **BPE artifacts** | 100% | 0% | Eliminated |
| **Quality filtered** | 0% | 100% | V2 filters applied |
| **Downstream compatible** | No | Yes | Full pipeline ready |

### Qualitative Improvements

**Example: PMID 34741192**

**Before:**
```csv
ID,common_name,common_prob
34741192.0,"ĠRat, ĠGen, ome, ĠDatabase, ĠRat, ĠGen, ome, ĠDatabase","1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000"
```

**After:**
```csv
ID,common_name,common_prob
34741192.0,"Rat Genome Database",1.000
```

---

## Code Reuse from V2

### Direct Reuse (No Changes)
- ✅ `deduplicate()` function from `src/ner_predict.py`
- ✅ `reformat_output()` function from `src/ner_predict.py`
- ✅ Quality filtering rules (length, URLs, punctuation)
- ✅ Probability averaging logic

### Adapted for Phase 4
- 🔄 Word-level reconstruction logic (adapted to batch processing)
- 🔄 Entity assembly algorithm (adapted for RESOURCE label)
- 🔄 Token-to-word aggregation (integrated with Phase 4 inference)

### New Components
- 🆕 `extract_entities_word_level()` - Phase 4-specific word-level extraction
- 🆕 `deduplicate_phase4_output()` - Wrapper to convert formats for V2 functions
- 🆕 Format conversion utilities (Phase 4 ↔ V2)

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Word-level mapping errors** | Low | High | Use V2's proven algorithm, comprehensive testing |
| **Batch processing issues** | Low | Medium | Maintain Phase 4's existing batch architecture |
| **Format incompatibility** | Low | Medium | Test format conversion thoroughly |
| **Performance degradation** | Very Low | Low | Word-level processing is fast (V2 proof) |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Breaking existing workflow** | Low | High | Preserve Phase 4 output format exactly |
| **Regression in F1 score** | Very Low | High | Core model unchanged, only post-processing |
| **Downstream pipeline issues** | Very Low | Medium | Output format matches V2 exactly |

### Overall Risk: **LOW**
- Using proven V2 approach (2+ years production)
- No model architecture changes
- Comprehensive test coverage
- Reversible changes (can rollback easily)

---

## Implementation Timeline

### Day 1 (2-3 hours)
- **Hour 1:** Implement `extract_entities_word_level()`
- **Hour 2:** Update `run_ner_inference()` integration
- **Hour 3:** Add deduplication wrapper + testing

### Day 2 (1 hour)
- **Testing:** Run on full Phase 4 dataset
- **Validation:** Compare entity quality to V2
- **Documentation:** Update README and starting_doc

### Total Effort: 3-4 hours

---

## Success Criteria

### Must Have (Launch Blockers)
- ✅ No BPE artifacts (Ġ prefix) in output
- ✅ Duplication reduced to ≤1 entity per unique resource per paper
- ✅ Output format matches V2 structure (for downstream compatibility)
- ✅ All unit tests passing
- ✅ Entity quality matches V2 standards (manual review of 10 samples)

### Should Have (Quality Metrics)
- ✅ 2-7x reduction in entity count per paper (deduplication)
- ✅ 100% of entities pass quality filters (length, URLs)
- ✅ Entity extraction time <2x slower than current (acceptable overhead)
- ✅ F1 score unchanged or improved (core model performance)

### Nice to Have (Future Enhancements)
- 🔄 Confidence score calibration analysis
- 🔄 Entity linking to external databases
- 🔄 Abbreviation expansion using full names

---

## Rollback Plan

If issues arise during implementation:

1. **Immediate Rollback:**
   ```bash
   git revert <commit-hash>
   ```

2. **Partial Rollback:**
   - Keep word-level extraction
   - Remove deduplication step
   - Investigate and fix incrementally

3. **Emergency Fallback:**
   - Revert to current Phase 4 output
   - Apply post-processing as separate script
   - Debug offline without blocking inference

---

## Documentation Updates

### Files to Update

1. **`docs/starting_doc.md`:**
   - Add Phase 4 post-processing improvement section
   - Reference this plan document
   - Update Phase 4 status to "Production Ready"

2. **`src/README_MULTITASK_PREDICT.md`:**
   - Document `extract_entities_word_level()` function
   - Explain word-level reconstruction approach
   - Add usage examples

3. **`docs/NER_SYSTEM_COMPARISON.md`:**
   - Update Phase 4 output format section
   - Add before/after examples
   - Update quality metrics

4. **`CHANGELOG.md`:**
   - Add entry for Phase 4 post-processing fix
   - Document breaking changes (if any)
   - List improvements

---

## Future Enhancements

### Post-Launch Improvements (Not in Scope)

1. **COM/FUL Distinction for Phase 4:**
   - Currently Phase 4 uses unified RESOURCE label
   - Future: Train abbreviation classifier
   - Separate entities into abbreviations vs full names

2. **Entity Linking:**
   - Link extracted entities to external databases
   - Resolve ambiguities using context
   - Validate entity existence

3. **Confidence Calibration:**
   - Analyze probability distribution
   - Calibrate confidence scores
   - Improve uncertainty quantification

4. **Multi-Entity Resolution:**
   - Handle nested entities
   - Resolve overlapping spans
   - Co-reference resolution

---

## References

### Documentation
- `docs/PYTORCH_CHECKPOINT_FIX.md` - PyTorch compatibility context
- `docs/multi_task_model/PHASE4_IMPLEMENTATION_SUMMARY.md` - Phase 4 architecture
- `docs/NER_SYSTEM_COMPARISON.md` - V2 vs Phase 4 comparison
- `V2_VS_PHASE4_NER_OUTPUT_COMPARISON.md` - Output format analysis

### Code Files
- `src/ner_predict.py` - V2 NER prediction with post-processing
- `src/multitask_predict.py` - Phase 4 NER prediction (to be modified)
- `src/models/multitask_model.py` - Phase 4 model architecture

### Research
- V2 NER implementation (2023) - word-level reconstruction
- Phase 4 multi-task learning (2025) - metadata integration
- HuggingFace tokenizers documentation - word_ids() and word_to_chars()

---

## Approval & Sign-Off

**Prepared By:** Claude Code (AI Assistant)
**Date:** 2025-11-05
**Status:** Awaiting Approval

**Approved By:** _________________
**Date:** _________________

---

## Appendix A: Technical Deep Dive

### Word-Level vs Token-Level Extraction

**Token-Level (Current Phase 4 - WRONG):**
```
Input Text: "The Rat Genome Database (RGD)"
Tokens:     ["ĠThe", "ĠRat", "ĠGen", "ome", "ĠDatabase", "Ġ(", "RG", "D", ")"]
Tags:       [O, B-RES, B-RES, I-RES, I-RES, O, B-RES, I-RES, O]
Output:     "Rat", "Genome Database", "RGD" (incorrect split!)
```

**Word-Level (V2 Approach - CORRECT):**
```
Input Text: "The Rat Genome Database (RGD)"
Words:      ["The", "Rat", "Genome", "Database", "(", "RGD", ")"]
word_ids:   [None, 0, 1, 2, 3, 4, 5, 6, 7, None] (token→word mapping)
Tags:       [O, B-RES, I-RES, I-RES, O, B-RES, O]
Output:     "Rat Genome Database", "RGD" (correct!)
```

### Performance Analysis

**Time Complexity:**
- Token-level: O(n) where n = token count
- Word-level: O(n) where n = token count (same!)
- Deduplication: O(m log m) where m = entity count per paper

**Space Complexity:**
- Additional: O(w) where w = word count (word_ids mapping)
- Negligible compared to model inference memory

**Expected Overhead:**
- Word-level extraction: +5-10% inference time
- Deduplication: +1-2% inference time
- Total: <12% overhead (acceptable)

---

## Appendix B: Test Plan Details

### Unit Tests

1. **test_word_level_extraction_basic**
   - Input: Simple text with one entity
   - Expected: Clean entity extraction

2. **test_word_level_extraction_multiple**
   - Input: Text with 3 entities
   - Expected: All entities extracted, no overlap

3. **test_word_level_extraction_duplicates**
   - Input: Text with same entity mentioned twice
   - Expected: Both mentions extracted separately

4. **test_deduplication_exact_match**
   - Input: Same entity repeated 5 times
   - Expected: Single entity with highest probability

5. **test_deduplication_case_insensitive**
   - Input: "RGD", "rgd", "Rgd"
   - Expected: Single entity with preferred case

6. **test_quality_filters**
   - Input: Mix of valid/invalid entities
   - Expected: URLs, single-chars filtered out

### Integration Tests

1. **test_end_to_end_phase4_pipeline**
   - Load Phase 4 model
   - Run on 10 test papers
   - Verify output format matches V2

2. **test_batch_processing_consistency**
   - Run same papers in different batch sizes
   - Verify identical results

3. **test_backwards_compatibility**
   - Verify downstream URL extraction works
   - Verify name processing works
   - Verify final inventory generation works

---

## Appendix C: Example Outputs

### Example 1: Rat Genome Database (PMID 34741192)

**Before (Raw BPE):**
```
"ĠRat, ĠGen, ome, ĠDatabase, ĠRat, ĠGen, ome, ĠDatabase"
Probabilities: 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000
Count: 8 tokens → 2 duplicate entities
```

**After (Word-Level):**
```
"Rat Genome Database"
Probability: 1.000
Count: 1 entity
```

### Example 2: Animal Sex Reversal Database (PMID 34839012)

**Before (Raw BPE):**
```
"ĠAnimal, ĠSex, ĠRe, vers, al, ĠDatabase, Animal, ĠSex, ĠRe, vers, al"
Probabilities: 0.999, 0.999, 0.999, 0.999, 1.000, 1.000, 0.997, 0.997, 0.998, 0.999, 0.999
Count: 11 tokens → 2 duplicate entities
```

**After (Word-Level):**
```
"Animal Sex Reversal Database"
Probability: 0.999
Count: 1 entity
```

### Example 3: Multiple Entities (PMID 34911434)

**Before (Raw BPE):**
```
"q, tl, X, pl, orer, Ġq, tl, X, pl, orer, Q, TL, X, pl, orer, q, tl, X, pl, orer"
Count: 20 tokens → 4 duplicate entities (case variations)
```

**After (Word-Level + Deduplication):**
```
"qtlXplorer"
Probability: 0.995
Count: 1 entity (case normalized)
```

---

**END OF PLAN**
