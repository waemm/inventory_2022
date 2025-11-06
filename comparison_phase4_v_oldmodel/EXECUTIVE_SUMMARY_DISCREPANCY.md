# Executive Summary: Phase 4 vs V2 NER Performance Discrepancy

**Date**: 2025-11-05
**Status**: ✅ **INVESTIGATION COMPLETE**
**Conclusion**: **Phase 4 is SIGNIFICANTLY WORSE than V2** - Do NOT deploy

---

## The Discrepancy

| Source | Phase 4 F1 | Context |
|--------|-----------|---------|
| **Phase 4 README** | **92.74%** | Validation set during training (111 papers) |
| **Script 02 Test Evaluation** | **22.49%** | Independent test set (63 papers) |
| **Gap** | **-70.25 points** | Apples-to-oranges comparison |

---

## Root Causes (4 Issues)

### 1. Different Evaluation Sets ⚠️
- **92.74%**: Measured on validation set during training (111 papers)
- **22.49%**: Measured on independent test set (63 papers)
- **Problem**: Not the same dataset, not comparable

### 2. Data Leakage 🚨
- **16 papers overlap** between validation and test sets
- Represents **25% of test set**
- Validation F1 inflated by seeing test data during training

### 3. Word-Level Tokenization Failure ❌
**Critical Bug**: Phase 4 predicts individual words, not complete entities

**Example**: Paper 22102583 - "Mouse Phenome Database (MPD)"

| System | Predictions | F1 |
|--------|------------|-----|
| Ground Truth | `["MPD", "Mouse Phenome Database"]` | - |
| V2 | `["MPD", "Mouse Phenome Database"]` | **1.00** ✅ |
| Phase 4 | `["Mouse", "Phenome", "Database"]` | **0.00** ❌ |

**Pattern**: Multi-word entities fragmented into individual words

### 4. Different Matching Strategies 📊
- **Validation** (92.74%): Token-level IOB tag matching (forgiving, partial credit)
- **Test** (22.49%): Entity-level exact string matching (strict, all-or-nothing)
- **Impact**: Token accuracy ≠ entity extraction quality

---

## Real Performance: Phase 4 vs V2 on Test Split

| Metric | Phase 4 | V2 | Winner |
|--------|---------|-----|---------|
| **F1 Score** | **22.49%** | **66.35%** | **V2 by 44 points** |
| Precision | 18.18% | 60.34% | V2 by 42 points |
| Recall | 29.47% | 73.68% | V2 by 44 points |
| True Positives | 28 | 70 | V2 finds 2.5x more |
| False Positives | 126 | 46 | Phase 4 makes 2.7x more errors |
| Median F1 | **0.00** | **0.80** | V2 by 80 points |
| Papers Won | 2 | 26 | V2 wins 13x more papers |
| Statistical Significance | - | p < 0.0001 | **V2 significantly better** |

---

## Key Findings

### Phase 4 Failures
1. **Low Recall**: Misses 70% of entities that V2 finds (29% vs 74%)
2. **Low Precision**: 82% of Phase 4 predictions are wrong (18% precision)
3. **Inconsistent**: Median F1 = 0.00 (half of papers get nothing right)
4. **Fragmentation**: Breaks multi-word entities into individual words
5. **High FP Rate**: 126 false positives vs 28 true positives (4.5:1 ratio)

### Why Validation F1 Was Misleading
1. **Token-level evaluation**: Each word scored independently (forgiving)
2. **Partial credit**: Getting 2/3 words = 67% accuracy
3. **IOB matching**: Only tags matter, not entity boundaries
4. **Not real-world**: Users need complete entities, not word tags

---

## Concrete Examples

### Example 1: Word Fragmentation
**Paper**: 27841751 - "A public database of macromolecular diffraction experiments"

```
Ground Truth: ["IRRMC", "Integrated Resource for Reproducibility in Macromolecular Crystallography"]
V2:           ["IRRMC", "Integrated Resource for Reproducibility in Macromolecular Crystallography"] ✅
Phase 4:      ["Crystallography", "Integrated", "Macromolecular", "Reproducibility", "Resource", ...] ❌
              (7 fragments instead of 1 entity)

Result: V2 F1=1.0, Phase 4 F1=0.0
```

### Example 2: Case Sensitivity
**Paper**: 32766766 - "LncR2metasta database"

```
Ground Truth: ["lncR2metasta"]
V2:           ["LncR2metasta"] ✅ (case-insensitive match)
Phase 4:      ["lncR", "metasta"] ❌ (entity split in half)

Result: V2 F1=1.0, Phase 4 F1=0.0
```

### Example 3: Papers Won
- **V2 wins on**: 26 papers
- **Phase 4 wins on**: 2 papers
- **Both correct**: 26 papers
- **Both fail**: 9 papers

---

## Recommendations

### Immediate (Now)
1. ✅ **DO NOT deploy Phase 4** for NER
2. ✅ **Continue using V2** - 3x better performance
3. ✅ **Fix post-processing bug** - word-level entity grouping broken
4. ✅ **Document this analysis** - prevent future confusion

### Short-Term (This Week)
1. **Debug Phase 4 post-processing**:
   - Investigate entity grouping logic
   - Test with multi-word entities
   - Fix consecutive I-tag merging

2. **Re-evaluate Phase 4**:
   - Remove 16 leaked test papers from validation
   - Report entity-level F1, not just token-level
   - Test on clean held-out set

3. **Add validation checks**:
   - Entity-level metrics during training
   - Multi-word entity test cases
   - Post-processing unit tests

### Medium-Term (Next Sprint)
1. **Rethink architecture**:
   - Consider span-based NER (predict boundaries directly)
   - Or add CRF layer (model tag dependencies)
   - Don't rely on post-processing to fix boundaries

2. **Improve evaluation**:
   - Track both token-level AND entity-level metrics
   - Use entity-level F1 for checkpoint selection
   - Validate on clean, independent test set

3. **Prevent data leakage**:
   - Programmatically verify split independence
   - Document split methodology
   - Never reuse test data in validation

---

## Lessons Learned

### 1. Token Accuracy ≠ Entity Quality
- 90% token accuracy can mean 20% entity F1
- Always evaluate on production metric

### 2. Validation ≠ Real-World Performance
- 92.74% validation → 22.49% test
- Need independent held-out evaluation

### 3. Data Leakage Inflates Metrics
- 16 leaked papers (25% of test) made Phase 4 look better
- Verify split independence programmatically

### 4. Post-Processing Is Critical
- Phase 4's grouping bug destroyed model
- Test post-processing separately
- Add unit tests for each step

### 5. Multi-Word Entities Are Hard
- Most databases have multi-word names
- Word-level models need proper boundary handling
- Consider span-based or sequence-to-sequence approaches

---

## The Bottom Line

**Phase 4's claimed 92.74% F1 is meaningless** - it was measured on validation data with a forgiving metric that doesn't reflect real-world entity extraction quality.

**On independent test data with real-world evaluation**, Phase 4 achieves only **22.49% F1**, making it **dramatically worse than V2's 66.35% F1**.

**The word-level tokenization bug** causes Phase 4 to fragment multi-word entities like "Mouse Phenome Database" into individual words ["Mouse", "Phenome", "Database"], resulting in 0% F1 on papers where V2 achieves 100% F1.

**Statistical testing confirms** V2 is significantly better (p < 0.0001), winning on 26 papers vs Phase 4's 2 papers.

**Recommendation**: **DO NOT USE PHASE 4**. Stick with V2 until Phase 4's post-processing is fixed and properly evaluated on entity-level metrics.

---

**Full Analysis**: `ROOT_CAUSE_ANALYSIS_DISCREPANCY.md`
**Generated**: 2025-11-05
**Version**: 1.0
