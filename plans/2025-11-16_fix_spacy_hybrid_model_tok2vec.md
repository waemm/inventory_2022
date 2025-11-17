# COMPREHENSIVE PLAN: Fix spaCy Hybrid Model & Run 3-Way Comparison

**Date Created**: 2025-11-16
**Status**: Ready for Execution
**Estimated Time**: 2-3 hours
**Objective**: Fix missing tok2vec dependency and run comprehensive 3-way NER comparison

---

## Executive Summary

**Current State**: The spaCy hybrid model is broken - statistical NER component extracts 0 entities because it's missing the tok2vec component that provides word embeddings.

**Goal**: Fix the hybrid model, rebuild it properly with all components, and run a comprehensive 3-way comparison to understand what each component contributes.

**Timeline**: 2-3 hours (fix + rebuild + run + analysis)

---

## Phase 1: Fix & Rebuild (60-90 minutes)

### 1.1 Backup Current Broken Model (5 minutes)

**Actions:**
```bash
# Backup the broken model
cp -r spacy_hybrid_ner/models/ner_hybrid_v2_com_ful \
      spacy_hybrid_ner/models/ner_hybrid_v2_com_ful_BROKEN_BACKUP_2025-11-16

# Document the issue
echo "Missing tok2vec component - statistical NER extracted 0 entities" > \
     spacy_hybrid_ner/models/ner_hybrid_v2_com_ful_BROKEN_BACKUP_2025-11-16/ISSUE.txt
```

**Success Criteria:**
- Backup directory created
- Original model preserved for comparison

---

### 1.2 Update Build Script (15 minutes)

**File**: `spacy_hybrid_ner/scripts/09_build_hybrid_pipeline.py`

**Changes Required:**

**Current code (BROKEN - lines 56-67):**
```python
# Step 3: Add trained statistical NER (SECOND!)
print("\nStep 3: Adding statistical NER (discovery component)...")
print(f"  Loading from: {statistical_model_path}")
nlp_statistical = spacy.load(statistical_model_path)

# Get the NER component from statistical model
ner_component = nlp_statistical.get_pipe("ner")

# Add it to our hybrid pipeline
nlp.add_pipe("ner", source=nlp_statistical)
```

**Fixed code (ADD tok2vec):**
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
```

**Update pipeline verification (line 76):**
```python
# OLD
assert nlp.pipe_names == ["entity_ruler", "ner"], "❌ Pipeline order incorrect!"

# NEW
assert nlp.pipe_names == ["entity_ruler", "tok2vec", "ner"], "❌ Pipeline order incorrect!"
print("✓ Pipeline order verified: EntityRuler → tok2vec → Statistical NER")
```

**Success Criteria:**
- Script updated to add tok2vec component
- Pipeline order: entity_ruler → tok2vec → ner
- Verification updated for 3 components

---

### 1.3 Rebuild Hybrid Model (10 minutes)

**Actions:**
```bash
cd /Users/warren/development/GBC/inventory_2022
source spacy_hybrid_ner/venv/bin/activate

# Run the fixed build script
python spacy_hybrid_ner/scripts/09_build_hybrid_pipeline.py
```

**Expected Output:**
```
Building hybrid NER pipeline...
======================================================================

Step 1: Creating blank English pipeline...
  ✓ Blank pipeline created

Step 2: Adding EntityRuler (high precision component)...
  ✓ Patterns loaded: 6,216
  ✓ Provides: High precision matching + canonical ID assignment

Step 3: Adding tok2vec (embedding component)...
  Loading from: collab_results/experiment_archives/2025-11-12-lof16h/spacy_model/model-best
  ✓ tok2vec component added
  ✓ Provides: Word embeddings for statistical NER

Step 4: Adding statistical NER (discovery component)...
  ✓ Statistical NER component added
  ✓ Provides: Discovery of new/unknown bioresources

----------------------------------------------------------------------
Pipeline Verification:
----------------------------------------------------------------------
Components: ['entity_ruler', 'tok2vec', 'ner']
Order: entity_ruler → tok2vec → ner
✓ Pipeline order verified: EntityRuler → tok2vec → Statistical NER
```

**Success Criteria:**
- All 3 components present: entity_ruler, tok2vec, ner
- Build script completes successfully
- No errors during rebuild

---

### 1.4 Verify Fix (10 minutes)

**Test the fixed model on sample text:**

```bash
cd /Users/warren/development/GBC/inventory_2022
source spacy_hybrid_ner/venv/bin/activate

python3 << 'EOF'
import spacy

print("="*70)
print("VERIFYING TOK2VEC FIX")
print("="*70)

# Load rebuilt model
nlp = spacy.load("spacy_hybrid_ner/models/ner_hybrid_v2_com_ful")

print(f"\n1. Pipeline components: {nlp.pipe_names}")
assert "tok2vec" in nlp.pipe_names, "❌ tok2vec missing!"
assert "entity_ruler" in nlp.pipe_names, "❌ entity_ruler missing!"
assert "ner" in nlp.pipe_names, "❌ ner missing!"
print("   ✓ All 3 components present")

print("\n2. Testing full hybrid pipeline...")
test_text = "We used GenBank and a novel genomic database for analysis."
doc = nlp(test_text)
print(f"   Entities found: {len(doc.ents)}")
for ent in doc.ents:
    source = "EntityRuler" if ent.ent_id_ else "Statistical NER"
    print(f"   - '{ent.text}' ({ent.label_}) from {source}")

print("\n3. Testing statistical NER only (disable EntityRuler)...")
with nlp.select_pipes(enable=["tok2vec", "ner"]):
    doc_stat = nlp(test_text)
    print(f"   Entities found: {len(doc_stat.ents)}")
    for ent in doc_stat.ents:
        print(f"   - '{ent.text}' ({ent.label_})")

    if len(doc_stat.ents) > 0:
        print("\n✓ STATISTICAL NER IS WORKING!")
    else:
        print("\n❌ Statistical NER still not extracting entities")

print("\n" + "="*70)
EOF
```

**Success Criteria:**
- All 3 components present
- Statistical NER extracts entities when EntityRuler disabled
- Full hybrid extracts entities from both sources

---

## Phase 2: Run Full Hybrid Pipeline (20-30 minutes)

### 2.1 Run on 50k Papers Dataset (20-30 minutes)

**Re-run the Phase 2 spaCy NER with FIXED model:**

```bash
cd /Users/warren/development/GBC/inventory_2022

# Re-run Script 10 with fixed hybrid model (all components enabled)
python3 validation_spacy_v_BERT/scripts/10_run_spacy_statistical_only_ner.py
```

**BUT modify the script first to NOT disable EntityRuler** - or create a new script for full hybrid.

**Expected Results (with working statistical NER):**
```
Papers processed: 50,192
Total entities: ~55,000-65,000 (vs 37,976 with broken model)
  - EntityRuler: ~30,000-35,000 (50-60%)
  - Statistical: ~20,000-30,000 (40-50%)
Coverage: ~35-45% of papers (vs 21% with broken model)
```

**Output File:**
`validation_spacy_v_BERT/results/phase2/ner/spacy_ner_full_hybrid_results_2025-11-16-XXXXXX.csv`

**Success Criteria:**
- More entities than broken model (37,976)
- Statistical entities > 0
- Both components contributing

---

## Phase 3: Run Statistical-Only Pipeline (15-20 minutes)

### 3.1 Re-run Statistical-Only with Fixed Model (15-20 minutes)

Now that the model has tok2vec, re-run the statistical-only extraction:

```bash
cd /Users/warren/development/GBC/inventory_2022
python3 validation_spacy_v_BERT/scripts/10_run_spacy_statistical_only_ner.py
```

**Expected Results:**
```
Papers processed: 50,192
Total entities: ~25,000-35,000 (vs 0 with broken model)
  - All from statistical NER
Coverage: ~25-35% of papers
```

**Output File:**
`validation_spacy_v_BERT/results/phase2/ner/spacy_ner_statistical_only_results_2025-11-16-XXXXXX.csv`

**Success Criteria:**
- Entities extracted > 0 (proves statistical NER works)
- Results different from EntityRuler-only
- Pure ML discoveries without pattern matching

---

## Phase 4: 3-Way Comparison & Analysis (30-45 minutes)

### 4.1 Update Comparison Script (20 minutes)

Modify `validation_spacy_v_BERT/scripts/11_compare_entityruler_vs_statistical.py` to handle 3-way comparison:

**Add third comparison set**:
- Full Hybrid (fixed model, both components)
- Statistical-Only (tok2vec + ner)
- EntityRuler-Only (broken model results as baseline)

**Key comparisons**:
1. What does EntityRuler add? (compare Full vs Statistical-only)
2. What does Statistical add? (compare Full vs EntityRuler-only)
3. Component synergy (Full vs sum of parts)

---

### 4.2 Run 3-Way Comparison (5 minutes)

```bash
cd /Users/warren/development/GBC/inventory_2022
python3 validation_spacy_v_BERT/scripts/11_compare_entityruler_vs_statistical.py \
    --full-hybrid validation_spacy_v_BERT/results/phase2/ner/spacy_ner_full_hybrid_results_2025-11-16-XXXXXX.csv \
    --statistical validation_spacy_v_BERT/results/phase2/ner/spacy_ner_statistical_only_results_2025-11-16-XXXXXX.csv \
    --entityruler validation_spacy_v_BERT/results/phase2/ner/spacy_ner_results_2025-11-15-h728fg.csv
```

**Output Files:**
- `validation_spacy_v_BERT/results/phase2/comparison/3way_comparison_report.md`
- `validation_spacy_v_BERT/results/phase2/comparison/3way_metrics.json`
- `validation_spacy_v_BERT/results/phase2/comparison/component_contributions.csv`

---

### 4.3 Validate Against Phase 1 (10 minutes)

```bash
python3 validation_spacy_v_BERT/scripts/12_validate_against_phase1.py \
    --full-hybrid validation_spacy_v_BERT/results/phase2/ner/spacy_ner_full_hybrid_results_2025-11-16-XXXXXX.csv \
    --statistical validation_spacy_v_BERT/results/phase2/ner/spacy_ner_statistical_only_results_2025-11-16-XXXXXX.csv
```

---

## Phase 5: Documentation (15-20 minutes)

### 5.1 Create Fix Documentation

**File**: `spacy_hybrid_ner/TOK2VEC_FIX_DOCUMENTATION.md`

Document:
- Problem summary (0 entities from statistical NER)
- Root cause (missing tok2vec)
- The fix (add tok2vec to build script)
- Before/after comparison
- Lessons learned

---

### 5.2 Update Comparison Documentation

**File**: `validation_spacy_v_BERT/results/phase2/ner/3WAY_COMPARISON_SUMMARY.md`

Document:
- Methodology (3 configurations compared)
- Key findings (component contributions)
- Production recommendations
- Next steps

---

### 5.3 Update PROGRESS.md

Add section:
- tok2vec fix completed
- 3-way comparison results
- Production recommendations for NER

---

## Timeline & Success Criteria

### Overall Timeline: 2-3 hours

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. Fix & Rebuild | 60-90 min | Working hybrid model with tok2vec |
| 2. Full Hybrid Run | 20-30 min | 50k papers processed |
| 3. Statistical-Only Run | 15-20 min | 50k papers processed (fixed) |
| 4. 3-Way Comparison | 30-45 min | Comprehensive report + metrics |
| 5. Documentation | 15-20 min | Fix docs + comparison summary |

### Success Criteria

**Phase 1 (Fix)**:
- ✓ Backup of broken model created
- ✓ Build script updated with tok2vec
- ✓ Rebuilt model has 3 components: entity_ruler, tok2vec, ner
- ✓ Verification shows statistical NER extracting entities

**Phase 2 (Full Hybrid)**:
- ✓ Statistical entities > 0 (vs 0 with broken model)
- ✓ 50k papers processed: 55k-65k entities
- ✓ Both components contributing

**Phase 3 (Statistical-Only)**:
- ✓ EntityRuler successfully disabled
- ✓ Entities extracted from statistical NER only (>0)
- ✓ Results show pure ML discoveries

**Phase 4 (Comparison)**:
- ✓ 3-way comparison report generated
- ✓ Clear component contribution breakdown
- ✓ Production strategy recommendations

**Phase 5 (Documentation)**:
- ✓ Fix documented with before/after
- ✓ Comparison methodology documented
- ✓ PROGRESS.md updated

---

## Expected Outcomes

### Full Hybrid Performance
- **Coverage**: 35-45% of 50k papers (vs 21% broken model)
- **Entities**: 55,000-65,000 (vs 37,976 broken model)
- **Sources**: 50-60% EntityRuler, 40-50% Statistical NER

### Statistical-Only Performance
- **Coverage**: 25-35% of papers
- **Entities**: 25,000-35,000 (vs 0 broken model)
- **Discovery**: Entities not in 6,216 pattern list

### Component Insights
- **EntityRuler adds**: High-precision canonical IDs, known resources
- **Statistical adds**: Discovery, variants, new resources
- **Hybrid synergy**: Maximum recall + precision

### Production Strategy
- **Recommended**: Full Hybrid for maximum value
- **Alternative 1**: Statistical-Only for discovery focus
- **Alternative 2**: EntityRuler-Only for high-precision only

---

## Files to Create/Modify

### Create:
1. `spacy_hybrid_ner/models/ner_hybrid_v2_com_ful_BROKEN_BACKUP_2025-11-16/` (backup)
2. `spacy_hybrid_ner/TOK2VEC_FIX_DOCUMENTATION.md`
3. `validation_spacy_v_BERT/results/phase2/ner/3WAY_COMPARISON_SUMMARY.md`
4. `validation_spacy_v_BERT/results/phase2/comparison/3way_comparison_report.md`
5. `validation_spacy_v_BERT/results/phase2/comparison/3way_metrics.json`

### Modify:
1. `spacy_hybrid_ner/scripts/09_build_hybrid_pipeline.py` (add tok2vec)
2. `validation_spacy_v_BERT/scripts/11_compare_entityruler_vs_statistical.py` (3-way comparison)
3. `plans/validation_spacy_v_BERT/PROGRESS.md` (update with findings)

---

## Risk Mitigation

**Risks**:
1. Source statistical model missing tok2vec
   - Mitigation: Agent verified model has tok2vec component

2. Statistical NER still doesn't extract after fix
   - Mitigation: Verification script tests before proceeding

3. Results don't match expectations
   - Mitigation: Clear documentation of actual results vs expected

**Rollback Plan**:
- Broken model backed up as `ner_hybrid_v2_com_ful_BROKEN_BACKUP_2025-11-16`
- Can restore if needed
- All original results preserved

---

## Next Steps After Completion

1. **Validate Results**: Compare against Phase 1 gold standard
2. **Update Reports**: Incorporate 3-way findings into documentation
3. **Production Deployment**: Use Full Hybrid for comprehensive extraction
4. **Monitor Performance**: Track statistical NER contribution over time

---

**Plan Created**: 2025-11-16
**Estimated Completion**: Same day (2-3 hours)
**Status**: Ready for execution
