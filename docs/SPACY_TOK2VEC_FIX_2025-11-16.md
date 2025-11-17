# spaCy Hybrid NER tok2vec Fix Documentation

**Date**: 2025-11-16
**Status**: ✅ Fixed and Validated
**Impact**: Statistical NER now contributing 79,515 entities (vs 0 before fix)

---

## Executive Summary

The spaCy hybrid NER model's statistical component was non-functional due to a missing tok2vec dependency. After fixing the build script to include tok2vec, statistical NER now contributes **67.7% of all entities** (79,515/117,491), increasing coverage from 21% to 64% of papers.

---

## Problem Summary

### Symptoms

**Observed Behavior:**
- Statistical NER extracted **0 entities** across all datasets
- EntityRuler-only extracted 37,976 entities (21% coverage)
- Full hybrid extracted same 37,976 entities as EntityRuler-only
- All entities had `source='ruler'`, none had `source='statistical'`

**Affected Runs:**
- Phase 1 validation (148 papers): 0 statistical entities
- Phase 2 initial run (50k papers, session 2025-11-15-h728fg): 0 statistical entities
- Phase 2 statistical-only test (session 2025-11-16-8wrzpw): 0 entities extracted

---

## Root Cause Analysis

### Investigation Process

1. **Hypothesis Testing:**
   - ✗ Label mismatch (both components use COM/FUL labels)
   - ✗ Source model broken (verified model works independently)
   - ✅ **Missing tok2vec component** (confirmed via config inspection)

2. **Config Analysis:**

```toml
[components.ner.model.tok2vec]
@architectures = "spacy.Tok2VecListener.v1"
width = 256
upstream = "*"  # Expects tok2vec component upstream!
```

3. **Pipeline Inspection:**

```python
# BROKEN MODEL
nlp.pipe_names = ['entity_ruler', 'ner']  # ❌ Missing tok2vec!

# SOURCE MODEL (working)
nlp_statistical.pipe_names = ['tok2vec', 'ner']  # ✓ Has tok2vec
```

### Root Cause

**The statistical NER component uses `Tok2VecListener` architecture** which requires an upstream `tok2vec` component to provide word embeddings.

**Build script (spacy_hybrid_ner/scripts/09_build_hybrid_pipeline.py line 65)** only copied the NER component, not its tok2vec dependency:

```python
# BROKEN CODE
nlp.add_pipe("ner", source=nlp_statistical)  # ❌ NER without tok2vec!
```

**Result:** NER component had no input features → produced 0 predictions

---

## The Fix

### Code Changes

**File**: `spacy_hybrid_ner/scripts/09_build_hybrid_pipeline.py`

**Before (lines 56-67):**
```python
# Step 3: Add trained statistical NER (SECOND!)
print("\nStep 3: Adding statistical NER (discovery component)...")
print(f"  Loading from: {statistical_model_path}")
nlp_statistical = spacy.load(statistical_model_path)

# Get the NER component from statistical model
ner_component = nlp_statistical.get_pipe("ner")

# Add it to our hybrid pipeline
nlp.add_pipe("ner", source=nlp_statistical)  # ❌ Missing tok2vec!
```

**After (fixed):**
```python
# Step 3: Add tok2vec (REQUIRED for NER!)
print("\nStep 3: Adding tok2vec (embedding component)...")
print(f"  Loading from: {statistical_model_path}")
nlp_statistical = spacy.load(statistical_model_path)

# Add tok2vec FIRST - NER depends on it
nlp.add_pipe("tok2vec", source=nlp_statistical)
print(f"  ✓ tok2vec component added")
print(f"  ✓ Provides: Word embeddings for statistical NER")

# Step 4: Add trained statistical NER (requires tok2vec!)
print("\nStep 4: Adding statistical NER (discovery component)...")
# Get the NER component from statistical model
ner_component = nlp_statistical.get_pipe("ner")

# Add it to our hybrid pipeline
nlp.add_pipe("ner", source=nlp_statistical)
print(f"  ✓ Statistical NER component added")
print(f"  ✓ Provides: Discovery of new/unknown bioresources")
```

**Pipeline Verification Update (line 83):**
```python
# Before
assert nlp.pipe_names == ["entity_ruler", "ner"], "❌ Pipeline order incorrect!"

# After
assert nlp.pipe_names == ["entity_ruler", "tok2vec", "ner"], "❌ Pipeline order incorrect!"
```

---

## Verification & Results

### Immediate Verification

```bash
source spacy_hybrid_ner/venv/bin/activate
python spacy_hybrid_ner/scripts/09_build_hybrid_pipeline.py
```

**Build Output:**
```
Step 3: Adding tok2vec (embedding component)...
  ✓ tok2vec component added
  ✓ Provides: Word embeddings for statistical NER

Step 4: Adding statistical NER (discovery component)...
  ✓ Statistical NER component added

Pipeline Verification:
Components: ['entity_ruler', 'tok2vec', 'ner']
✓ Pipeline order verified: EntityRuler → tok2vec → Statistical NER

Test Results:
  EntityRuler entities: 4 (known, with canonical IDs)
  Statistical NER entities: 1 (discovered, no canonical IDs)  # ✅ WORKING!
```

### Full-Scale Validation (50k Papers)

| Metric | Broken Model | Fixed Model | Improvement |
|--------|--------------|-------------|-------------|
| **Total Entities** | 37,976 | 117,491 | **+79,515 (3.1x)** |
| **Statistical Entities** | 0 (0%) | 79,515 (67.7%) | **+79,515** |
| **EntityRuler Entities** | 37,976 (100%) | 37,976 (32.3%) | Same |
| **Papers w/ Entities** | 10,554 (21%) | 32,317 (64%) | **+21,763 (3.1x)** |
| **Coverage** | 21.03% | 64.39% | **+43.36%** |

### Phase 1 Validation (148 Papers, 395 Gold Entities)

| Metric | EntityRuler-Only | Statistical-Only | Ensemble |
|--------|-----------------|------------------|----------|
| **Recall** | 57.5% | 56.5% | **60.8%** |
| **Precision** | **100.0%** | 89.9% | 90.6% |
| **F1 Score** | 0.730 | 0.694 | **0.727** |

**Key Findings:**
- Statistical NER provides +3.3% recall gain (13 additional entities)
- Precision remains high (90.6% for ensemble)
- Both components contribute unique value

---

## Impact Assessment

### Before Fix

**EntityRuler-only Performance:**
- 37,976 entities from 50,192 papers
- 21.03% coverage (only papers with known resources)
- 100% precision, 57.5% recall on gold standard
- Limited to 6,216 pattern dictionary

### After Fix

**Full Hybrid Performance:**
- 117,491 entities from 50,192 papers (**3.1x increase**)
- 64.39% coverage (**3.1x increase**)
- 90.6% precision, 60.8% recall on gold standard
- Discovers resources beyond dictionary

**Component Breakdown:**
- **EntityRuler**: 37,976 entities (32.3%) - High precision, known resources
- **Statistical NER**: 79,515 entities (67.7%) - Discovery, new/unknown resources

**Speed:**
- EntityRuler-only: 31.77 papers/sec (26 min for 50k papers)
- Full Hybrid: 8.58 papers/sec (97 min for 50k papers)
- **3.7x slower but 3.1x more entities** - worth the tradeoff!

---

## Lessons Learned

### Technical Insights

1. **Dependency Awareness**: spaCy components can have implicit dependencies (e.g., Tok2VecListener requires tok2vec)

2. **Pipeline Order Matters**: tok2vec must be added **before** NER component

3. **Component Source Verification**: When copying components with `source=`, verify **all dependencies** are included

4. **Silent Failures**: Missing dependencies don't always error - they can produce valid but empty results

### Testing Improvements

1. **Sanity Checks**: Always verify both components contribute entities after building
   ```python
   # Test statistical component in isolation
   with nlp.select_pipes(enable=["tok2vec", "ner"]):
       doc = nlp("test text")
       assert len(doc.ents) > 0, "Statistical NER not working"
   ```

2. **Config Inspection**: Check component architectures for dependency requirements

3. **Before/After Comparison**: Track source distribution (ruler vs statistical)

---

## Production Recommendations

### Use Full Hybrid Model

**Rationale:**
- **3.1x more entities** than EntityRuler-only
- **3.1x better coverage** (64% vs 21% of papers)
- **Balanced precision/recall** (90.6% precision, 60.8% recall)
- Discovers resources not in pattern dictionary

**When to Use Each Component:**

| Use Case | Recommended Configuration |
|----------|--------------------------|
| **Production (default)** | Full Hybrid (entity_ruler + tok2vec + ner) |
| **High precision required** | EntityRuler-only (100% precision) |
| **Maximum discovery** | Statistical-only (pure ML, 63.7% coverage) |
| **Fast processing** | EntityRuler-only (3.7x faster) |

---

## Files Modified

### Created/Modified

1. **spacy_hybrid_ner/scripts/09_build_hybrid_pipeline.py** - Added tok2vec component
2. **spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/** - Rebuilt model with fix
3. **spacy_hybrid_ner/models/ner_hybrid_v2_com_ful_BROKEN_BACKUP_2025-11-16/** - Backup of broken model

### New Scripts Created

1. **validation_spacy_v_BERT/scripts/09b_run_spacy_full_hybrid_ner.py** - Full hybrid extraction
2. **validation_spacy_v_BERT/scripts/10_run_spacy_statistical_only_ner.py** - Statistical-only extraction
3. **validation_spacy_v_BERT/scripts/09c_run_spacy_entityruler_only_ner.py** - EntityRuler-only extraction
4. **validation_spacy_v_BERT/scripts/12_validate_against_phase1.py** - Updated with PMID mapping fix

---

## Timeline

| Date | Activity | Duration |
|------|----------|----------|
| 2025-11-15 | Problem discovered (0 statistical entities) | - |
| 2025-11-16 09:00 | Root cause investigation | 2 hours |
| 2025-11-16 11:00 | Fix implemented and verified | 30 min |
| 2025-11-16 11:30 | Full hybrid run (50k papers) | 97 min |
| 2025-11-16 13:10 | Statistical-only run | 79 min |
| 2025-11-16 14:10 | EntityRuler-only run | 26 min |
| 2025-11-16 15:00 | Phase 1 validation | 15 min |
| 2025-11-16 15:30 | Documentation complete | 30 min |

**Total Time**: ~7 hours from discovery to full validation

---

## Next Steps

1. ✅ Update production deployment to use fixed hybrid model
2. ✅ Document 3-way comparison methodology
3. ✅ Update PROGRESS.md with findings
4. 🔄 Run on full 150k dataset (if needed)
5. 🔄 Monitor statistical NER quality over time

---

**Fix Validated By**: Claude Code
**Approved By**: Warren
**Documentation Created**: 2025-11-16
