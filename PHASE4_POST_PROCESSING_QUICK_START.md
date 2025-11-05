# Phase 4 Post-Processing Quick Start Guide

**Purpose:** Quick reference for using the improved Phase 4 NER post-processing

**Date:** 2025-11-05

---

## What Changed?

**Before:**
- Phase 4 output had BPE tokenization artifacts (Ġ prefix)
- Massive duplication (same entity 2-7x per paper)
- Not compatible with downstream pipeline

**After:**
- ✅ Clean entity text (no BPE artifacts)
- ✅ Deduplicated output (1 entity per unique mention per paper)
- ✅ V2-compatible format (works with URL extraction, name processing)

---

## Usage (Nothing Changes for You!)

The improvements are **automatic** - no changes needed to your workflow:

```bash
# Same command as before
python src/multitask_predict.py \
    --input data/epmc_query_results_2022.csv \
    --metadata data/metadata/features_engineered.csv \
    --checkpoint trained_models_25/checkpoint_best_ner.pt \
    --output-dir output/phase4 \
    --batch-size 32 \
    --device cuda
```

**Output:**
- `output/phase4/ner_results.csv` - Now clean and deduplicated!
- Same format as before, but higher quality

---

## Verification

### Check for BPE Artifacts

```bash
# Should return empty (no Ġ character)
grep 'Ġ' output/phase4/ner_results.csv
```

### Check Deduplication

```bash
# Count entities before/after (if you have old output)
OLD_COUNT=$(wc -l < output/old/ner_results.csv)
NEW_COUNT=$(wc -l < output/phase4/ner_results.csv)
echo "Reduction: $((OLD_COUNT - NEW_COUNT)) rows"
```

### Manual Inspection

```bash
# View first 10 results
head -n 10 output/phase4/ner_results.csv
```

**Look for:**
- Clean entity names (no Ġ prefix)
- No obvious duplicates in same paper
- Reasonable entity counts per paper

---

## Testing

### Run Unit Tests

```bash
python test_phase4_postprocessing.py
```

**Expected output:**
```
✅ PASSED: Word-Level Extraction
✅ PASSED: Deduplication
✅ PASSED: No BPE Artifacts

Total: 3/3 tests passed
```

### Test on Sample Data

```bash
# Create small test file (10 papers)
head -n 11 data/epmc_query_results_2022.csv > data/sample_10_papers.csv

# Run inference
python src/multitask_predict.py \
    --input data/sample_10_papers.csv \
    --metadata data/metadata/features_engineered.csv \
    --checkpoint trained_models_25/checkpoint_best_ner.pt \
    --output-dir output/test_sample \
    --batch-size 4

# Check output
cat output/test_sample/ner_results.csv
```

---

## Troubleshooting

### Issue: "No entities found for deduplication"

**Cause:** No entities extracted (model predicted all 'O' tags)

**Solution:**
- Check if input papers are bio-resource related
- Verify model checkpoint is correct
- Review classification results first

### Issue: Import error for `deduplicate`

**Cause:** Can't find `src/ner_predict.py`

**Solution:**
```bash
# Ensure you're in project root
cd /path/to/inventory_2022

# Verify file exists
ls src/ner_predict.py
```

### Issue: Slow inference

**Cause:** Word-level extraction adds ~10% overhead

**Solution:**
- Use GPU: `--device cuda`
- Increase batch size: `--batch-size 64`
- Expected overhead is acceptable for quality gain

---

## Code Examples

### Using Word-Level Extraction Directly

```python
from src.multitask_predict import extract_entities_word_level, ID2TAG
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500'
)

text = "The Rat Genome Database (RGD) is a comprehensive resource."

# ... get predictions from model ...
# bio_tags = model predictions
# probabilities = token probabilities

entities = extract_entities_word_level(
    text=text,
    tokenizer=tokenizer,
    input_ids=input_ids,
    bio_tags=bio_tags,
    probabilities=probabilities,
    id2tag=ID2TAG
)

# entities = [('Rat Genome Database', 'COM', 0.99), ...]
for entity_text, entity_type, confidence in entities:
    print(f"{entity_text} ({entity_type}, {confidence:.3f})")
```

### Using Deduplication Directly

```python
import pandas as pd
from src.multitask_predict import deduplicate_phase4_output

# Load Phase 4 NER results
ner_results = pd.read_csv('output/phase4/ner_results.csv')

# Deduplicate
deduped_results = deduplicate_phase4_output(ner_results)

# Save
deduped_results.to_csv('output/phase4/ner_results_deduped.csv', index=False)
```

---

## Performance Expectations

### Entity Count Reduction

**Before:** 40,000-60,000 entity instances (with duplicates)
**After:** 15,000-25,000 entity instances (deduplicated)
**Reduction:** 2-7x fewer entities (expected)

### Inference Time

**Overhead:** +10-12% (word-level extraction + deduplication)
**Example:** 10 min → 11 min for full 2022 dataset
**Acceptable:** Yes (quality improvement worth it)

### Output Quality

**Before:**
```csv
ID,common_name,common_prob
123,"Ġ Rat, ĠGen, ome, ĠDatabase, ĠRat, ĠGen, ome","0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99"
```

**After:**
```csv
ID,common_name,common_prob
123,"Rat Genome Database","0.99"
```

---

## Integration with Downstream Pipeline

### Phase 4 → URL Extraction

```bash
# Run Phase 4 NER (now with clean output)
python src/multitask_predict.py ... --output-dir output/phase4

# Run URL extraction (should work seamlessly)
python src/url_extraction.py \
    --input output/phase4/ner_results.csv \
    --output output/phase4/url_extraction_results.csv
```

### Phase 4 → Name Processing

```bash
# Process extracted names
python src/process_names.py \
    --input output/phase4/ner_results.csv \
    --output output/phase4/processed_names_results.csv
```

### Full Pipeline

```bash
# Run full inventory update pipeline
# Phase 4 post-processing is now integrated
bash scripts/run_phase4_full_pipeline.sh
```

---

## Comparison to V2

| Feature | V2 | Phase 4 (Old) | Phase 4 (New) |
|---------|----|--------------:|---------------|
| **F1 Score** | 0.749 | 0.927 | 0.927 (unchanged) |
| **BPE Artifacts** | ❌ No | ✅ Yes | ❌ No |
| **Duplication** | ❌ No | ✅ Yes (2-7x) | ❌ No |
| **Quality Filters** | ✅ Yes | ❌ No | ✅ Yes |
| **Production Ready** | ✅ Yes | ❌ No | ✅ Yes |

**Conclusion:** Phase 4 (New) = V2 quality + Phase 4 performance 🎉

---

## Key Files

### Modified
- `src/multitask_predict.py` - Core implementation

### Created
- `test_phase4_postprocessing.py` - Unit tests
- `PHASE4_NER_POST_PROCESSING_IMPLEMENTATION.md` - Full technical details
- `PHASE4_POST_PROCESSING_QUICK_START.md` - This file

### Referenced
- `src/ner_predict.py` - V2 deduplication function (imported)
- `plans/2025-11-05_phase4_ner_post_processing_fix.md` - Original plan

---

## FAQ

**Q: Will this break existing code?**
A: No. Old functions are deprecated but still available for backward compatibility.

**Q: Do I need to retrain the model?**
A: No. This is post-processing only; the model is unchanged.

**Q: Can I disable deduplication?**
A: Yes. Comment out the deduplication step in `main()` if needed.

**Q: Will F1 score change?**
A: No. Core model predictions are unchanged; only post-processing improved.

**Q: Can I use this with V2?**
A: V2 already has proper post-processing. This is Phase 4 only.

---

## Support

**Issues?** Check:
1. `PHASE4_NER_POST_PROCESSING_IMPLEMENTATION.md` - Full technical details
2. `plans/2025-11-05_phase4_ner_post_processing_fix.md` - Original requirements
3. Test script: `python test_phase4_postprocessing.py`

**Questions?** Review:
- Implementation decisions in main document
- Edge cases handled section
- Known limitations section

---

**Last Updated:** 2025-11-05
**Status:** ✅ Production Ready
