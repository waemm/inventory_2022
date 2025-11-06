# Phase 3 Work Plan - NER Entity Complexity Investigation

**Document Version**: 1.0
**Date**: 2025-11-03
**Status**: Ready for execution
**Estimated Duration**: 5-7 weeks (288 GPU hours)

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Work Completed (Phase 2 & 2B)](#work-completed-phase-2--2b)
3. [Key Findings](#key-findings)
4. [Work Remaining (Phase 3)](#work-remaining-phase-3)
5. [Detailed Execution Plan](#detailed-execution-plan)
6. [Technical Implementation](#technical-implementation)
7. [Expected Outcomes](#expected-outcomes)
8. [Decision Trees](#decision-trees)
9. [Resources Required](#resources-required)
10. [Success Criteria](#success-criteria)

---

## Executive Summary

### Current Status
We have completed Phase 2 and Phase 2B of the NER entity complexity investigation, testing **12 different complexity levels** from 5% to 92%. The investigation revealed that split composition explains **80% of the performance gap** between current baseline (F1=0.644) and V2 baseline (F1=0.749).

### Key Discovery
The relationship between entity complexity and NER performance is **more complex than expected**:
- Split B (66% complexity) achieved best performance: F1 = 0.7281
- BUT: Surrounded by lower-performing splits (valley at 55-60%)
- AND: High complexity plateau (80-92%) performs nearly as well: avg F1 = 0.7240
- Split K2 (92%) achieved F1 = 0.7273 (only 0.0008 behind Split B!)

### Critical Question
**Is Split B's superiority real or due to lucky initialization?**

### What Remains
1. **Validate Split B consistency** with multiple random seeds
2. **Test high-complexity plateau stability** (may be more reliable than Split B)
3. **Investigate the performance valley** at 55-60% complexity
4. **Close final 2.09 point gap** to V2 through hyperparameter optimization

### Recommendation
Start with **Phase 3A (Priority 1 & 2)**: Quick validation experiments (~112 GPU hours, 1-2 weeks) to determine optimal strategy before deeper investigation.

---

## Work Completed (Phase 2 & 2B)

### Phase 2: Initial Investigation (Splits A-E)
**Duration**: October 21 - November 3, 2025
**Splits tested**: 5

| Split | Complexity | Val F1 | Key Finding |
|-------|-----------|--------|-------------|
| A | 12.0% | 0.6788 | Low complexity baseline |
| D | 28.2% | 0.7165 | Mid-low performance |
| C | 35.3% | 0.7040 | Medium complexity |
| B | 65.9% | **0.7281** | **Best performer** |
| E | 83.9% | 0.7233 | High complexity (slight decline) |

**Initial conclusion**: Inverted U-curve with peak at ~66%

### Phase 2B: Granular Mapping (Splits F-K2)
**Duration**: November 3, 2025
**Splits tested**: 7 additional

| Split | Complexity | Val F1 | Key Finding |
|-------|-----------|--------|-------------|
| K1 | 5.0% | 0.6490 | Extreme low (worst) |
| F | 55.0% | 0.6975 | **Unexpected valley** |
| G | 60.0% | 0.6950 | **Valley continues** |
| H | 70.0% | 0.7100 | Post-optimal |
| I | 75.0% | 0.7122 | Mid-high |
| J | 80.0% | 0.7215 | **High plateau** |
| K2 | 92.0% | **0.7273** | **Extreme high - nearly ties Split B!** |

**Revised conclusion**: Complex non-linear relationship with valley phenomenon and high-complexity plateau

### Artifacts Generated

**Documentation**:
- `docs/split_project/PHASE2B_FINAL_RESULTS.md` - Complete analysis
- `SPLIT_E_RESULTS_SUMMARY.md` - Phase 2 conclusions
- `PHASE2_COMPLETE_ANALYSIS.md` - Initial 5-split analysis

**Data**:
- 12 data split directories in `data/ner_splits_split{X}/`
- Training archives in `collab_results/training_archives/2025-11-03-{SESSION_ID}_split{X}/`
- `docs/split_project/phase2_and_phase2b_combined_results.csv` - All 12 results

**Scripts**:
- `scripts/create_stratified_splits.py` - Splits A, B, C generation
- `scripts/create_split_d.py` - Split D generation
- `scripts/create_split_e.py` - Split E generation
- `scripts/create_phase2b_splits.py` - Splits F, G, H, I, J, K1, K2 generation
- `docs/split_project/analyze_phase2b_complete.py` - Full analysis script

**Notebooks**:
- `phase2b_granular_training.ipynb` - Loop-based training for all Phase 2B splits

**Visualizations**:
- `docs/split_project/phase2b_complete_analysis.png` - 12-point curve with cubic fit

---

## Key Findings

### Finding 1: Split Composition Matters (80% Gap Closure)
From current baseline (0.644) to Split B (0.7281):
- **Gap closed**: 8.41 percentage points
- **Total gap to V2**: 10.5 percentage points
- **Closure rate**: 80.1%
- **Remaining gap**: 2.09 percentage points

**Implication**: Split composition is the dominant factor, but not the complete story.

### Finding 2: The Performance Valley (55-60% Complexity)
Splits F and G performed **worse than expected**:
- Split F (55%): 0.6975
- Split G (60%): 0.6950
- Both worse than Split D (28%): 0.7165
- Drop of **2.03 points** from Split D

**Possible explanations**:
1. Mid-range class imbalance causes training instability
2. Splits F/G had unlucky random seeds
3. Specific interaction between simple/complex entity ratios
4. Training dynamics issue at this complexity level

**Status**: Unexplained - requires investigation (Priority 3)

### Finding 3: The High-Complexity Plateau (80-92%)
High complexity performs **almost as well as Split B**:
- Average F1 in plateau: 0.7240
- Split B F1: 0.7281
- Difference: only **0.0041 points**
- Split K2 (92%): 0.7273 (only **0.0008 behind Split B!**)

**Implication**: Very high complexity may be:
1. More stable across random seeds
2. Easier to optimize with hyperparameters
3. Better for production use (if validated)

**Status**: Promising - requires validation (Priority 2)

### Finding 4: Split B May Be Lucky
Split B's superiority is suspicious:
- Surrounded by lower-performing splits (F, G, H)
- Sharp peak at exactly 66%
- Could be due to fortunate random initialization

**Implication**: Need to test with multiple seeds to validate (Priority 1)

### Finding 5: Non-Linear Relationship
- Quadratic fit: R² = 0.6911 (poor)
- Cubic fit: R² = 0.8276 (much better)
- Three distinct phases: rising → valley → plateau
- Simple inverted-U model is insufficient

**Implication**: Cannot make simple predictions, need empirical testing

---

## Work Remaining (Phase 3)

### Phase 3A: Quick Validation (1-2 weeks, ~112 GPU hours)

**Priority 1: Validate Split B Consistency** 🔍
- **Goal**: Determine if Split B (66%) is consistently optimal or lucky
- **Method**: Retrain Split B with 5 different random seeds
- **Duration**: ~40 GPU hours (5 runs × 8 hours)
- **Decision point**: Determines entire Phase 3 strategy

**Priority 2: Test High-Complexity Plateau Stability** 📊
- **Goal**: Confirm high complexity (80-92%) is stable and reliable
- **Method**: Train at 80%, 85%, 90% with 3 seeds each
- **Duration**: ~72 GPU hours (9 runs × 8 hours)
- **Decision point**: Determines if high complexity is viable for production

### Phase 3B: Deep Investigation (2-3 weeks, ~56 GPU hours)

**Priority 3: Map the Performance Valley** 🕳️
- **Goal**: Understand why 55-60% complexity underperforms
- **Method**: Test 50%, 52%, 54%, 56%, 58%, 62%, 64% complexity
- **Duration**: ~56 GPU hours (7 runs × 8 hours)
- **Outcome**: Define safe vs danger zones for complexity

### Phase 3C: Final Optimization (2-3 weeks, ~120 GPU hours)

**Priority 4: Close the 2.09 Point Gap** 🔧
- **Goal**: Reach F1 ≥ 0.740 (within 1.5% of V2)
- **Method**: Hyperparameter sweep on best configuration
  - Learning rates: [1e-5, 2e-5, 3e-5, 5e-5]
  - Warmup steps: [0, 100, 500, 1000]
  - Epochs: [10, 15, 20]
  - Early stopping: [disabled, patience=3, patience=5]
- **Duration**: ~120 GPU hours
  - Broad search: 10 configs (~80 hours)
  - Fine-tuning: 5 configs (~40 hours)

---

## Detailed Execution Plan

### Phase 3A.1: Split B Multi-Seed Validation

**Objective**: Determine if Split B's F1=0.7281 is consistent or lucky

**Experimental Design**:
```python
# Configuration
base_split = 'splitB'
data_dir = 'data/ner_splits_splitB/'  # Same data as original
seeds = [241, 242, 243, 244, 245]     # Original seed was 241
epochs = 10
learning_rate = 2e-5
batch_size = 16

# Train 5 times with different seeds
results = []
for seed in seeds:
    model = train_ner(
        data_dir=data_dir,
        seed=seed,
        lr=learning_rate,
        batch_size=batch_size,
        epochs=epochs,
        model_name='allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500'
    )
    results.append({
        'seed': seed,
        'val_f1': model.val_f1,
        'val_precision': model.val_precision,
        'val_recall': model.val_recall
    })

# Analyze variance
mean_f1 = np.mean([r['val_f1'] for r in results])
std_f1 = np.std([r['val_f1'] for r in results])
```

**Success Criteria**:
- **Consistent** (✅): std_f1 < 0.005 (mean ~0.728 ± 0.005)
- **Moderate variance** (⚠️): 0.005 ≤ std_f1 < 0.010
- **High variance** (❌): std_f1 ≥ 0.010

**Expected Duration**: 40 hours (5 × 8 hours per run)

**Deliverables**:
- Training archives: `2025-11-XX-{SESSION_ID}_splitB_seed{XXX}/`
- Results CSV: `phase3a_splitB_multiseed_results.csv`
- Analysis report: `docs/handover/PHASE3A_SPLITB_VALIDATION.md`

**Decision Point**:
- If consistent → Proceed with Split B optimization (Priority 4)
- If variable → Investigate high-complexity plateau instead (Priority 2)

### Phase 3A.2: High-Complexity Plateau Testing

**Objective**: Validate that 80-92% complexity is stable across seeds

**Experimental Design**:
```python
# Test 3 complexity levels × 3 seeds each
complexities = [80, 85, 90]
seeds = [241, 242, 243]

results = {}

for complexity in complexities:
    for seed in seeds:
        # Create split with this complexity
        create_complexity_stratified_split(
            df=master_df,
            split_name=f'phase3_c{complexity}_s{seed}',
            test_complex_ratio=complexity/100,
            val_complex_ratio=0.25,
            seed=seed
        )

        # Train
        model = train_ner(
            data_dir=f'data/ner_splits_phase3_c{complexity}_s{seed}/',
            seed=seed,
            lr=2e-5,
            batch_size=16,
            epochs=10
        )

        results[(complexity, seed)] = model.val_f1
```

**Success Criteria**:
For each complexity level:
- **Stable** (✅): std_f1 < 0.005 across 3 seeds
- **Moderate** (⚠️): 0.005 ≤ std_f1 < 0.010
- **Unstable** (❌): std_f1 ≥ 0.010

**Expected Duration**: 72 hours (9 runs × 8 hours)

**Deliverables**:
- 9 training archives
- Results CSV: `phase3a_plateau_stability_results.csv`
- Analysis report: `docs/handover/PHASE3A_PLATEAU_VALIDATION.md`

**Decision Point**:
Compare Split B variance vs Plateau variance:
- If plateau more stable → Use 85-90% for production
- If both stable → Use Split B (slight edge in performance)
- If both unstable → Need better training procedure (Priority 4)

### Phase 3A Decision Matrix

After completing both Priority 1 and Priority 2:

| Split B Variance | Plateau Variance | Recommendation |
|-----------------|------------------|----------------|
| Low (< 0.005) | Low (< 0.005) | Use Split B (66%) - slightly better peak |
| Low (< 0.005) | High (≥ 0.010) | Use Split B (66%) - much more stable |
| High (≥ 0.010) | Low (< 0.005) | **Use 85-90% - more stable, nearly as good** |
| High (≥ 0.010) | High (≥ 0.010) | Investigate training procedures (Priority 4) |
| Medium | Medium | Test both in Priority 4, pick best |

**Phase 3A Output**: Clear recommendation for production split strategy

### Phase 3B: Valley Investigation

**Objective**: Understand the performance drop at 55-60% complexity

**Experimental Design**:
```python
# Map the valley with 7 new complexity levels
valley_complexities = [50, 52, 54, 56, 58, 62, 64]
seed = 241  # Use consistent seed

results = []
for complexity in valley_complexities:
    # Create split
    create_complexity_stratified_split(
        df=master_df,
        split_name=f'valley_c{complexity}',
        test_complex_ratio=complexity/100,
        val_complex_ratio=0.25,
        seed=seed
    )

    # Train
    model = train_ner(
        data_dir=f'data/ner_splits_valley_c{complexity}/',
        seed=seed,
        lr=2e-5,
        batch_size=16,
        epochs=10
    )

    results.append({
        'complexity': complexity,
        'val_f1': model.val_f1
    })
```

**Analysis Questions**:
1. Is the valley continuous or are F/G outliers?
2. Where does the valley begin (≤50%)?
3. Where does it end (≥64%)?
4. What is the steepness of recovery to Split B?

**Expected Patterns**:

**Pattern A: Real continuous valley**
```
50%: 0.700
52%: 0.698
54%: 0.696
56%: 0.697
58%: 0.696
62%: 0.705
64%: 0.715

Conclusion: Valley is real, avoid 50-62% range
```

**Pattern B: Sharp cliff at Split B**
```
60%: 0.695
62%: 0.702
64%: 0.718
66%: 0.728 (Split B)

Conclusion: Sweet spot is very narrow, 65-67% only
```

**Pattern C: F/G were outliers**
```
All 50-64% splits achieve 0.710-0.720
Conclusion: Valley doesn't exist, F/G had bad seeds
Action: Retrain F/G with new seeds
```

**Expected Duration**: 56 hours (7 runs × 8 hours)

**Deliverables**:
- 7 training archives
- Valley map visualization
- Results CSV: `phase3b_valley_investigation_results.csv`
- Analysis report: `docs/handover/PHASE3B_VALLEY_ANALYSIS.md`

### Phase 3C: Hyperparameter Optimization

**Objective**: Close the final 2.09 point gap to V2 baseline

**Target**: F1 ≥ 0.740 (from current best 0.7281)

**Experimental Design**:

**Step 1: Broad Search (10 configurations)**
```python
# Based on results from Phase 3A, use the best split
# (either Split B or 85-90% complexity)

broad_configs = [
    # Baseline
    {'lr': 2e-5, 'warmup': 0, 'epochs': 10, 'early_stop': False},

    # Learning rate variations
    {'lr': 1e-5, 'warmup': 0, 'epochs': 10, 'early_stop': False},
    {'lr': 3e-5, 'warmup': 0, 'epochs': 10, 'early_stop': False},
    {'lr': 5e-5, 'warmup': 0, 'epochs': 10, 'early_stop': False},

    # Warmup strategies
    {'lr': 2e-5, 'warmup': 500, 'epochs': 10, 'early_stop': False},
    {'lr': 2e-5, 'warmup': 1000, 'epochs': 10, 'early_stop': False},

    # Extended training
    {'lr': 2e-5, 'warmup': 500, 'epochs': 15, 'early_stop': False},
    {'lr': 2e-5, 'warmup': 500, 'epochs': 20, 'early_stop': False},

    # Early stopping
    {'lr': 2e-5, 'warmup': 500, 'epochs': 20, 'early_stop': True, 'patience': 3},
    {'lr': 3e-5, 'warmup': 500, 'epochs': 20, 'early_stop': True, 'patience': 5}
]

results = []
for config in broad_configs:
    model = train_with_config(
        data_dir=best_split_dir,
        seed=241,  # Use consistent seed
        **config
    )
    results.append({**config, 'val_f1': model.val_f1})
```

**Step 2: Fine-Tuning (5 configurations)**
```python
# Take best config from broad search
# Test variations around it
best_config = results[np.argmax([r['val_f1'] for r in results])]

fine_tune_configs = generate_variations(best_config, n=5)

for config in fine_tune_configs:
    model = train_with_config(
        data_dir=best_split_dir,
        seed=241,
        **config
    )
    # Track if improvement found
```

**Expected Duration**: 120 hours
- Broad search: 10 configs × ~8 hours = 80 hours
- Fine-tuning: 5 configs × ~8 hours = 40 hours

**Success Criteria**:
- **Excellent**: F1 ≥ 0.745 (within 0.5% of V2)
- **Good**: F1 ≥ 0.740 (within 1.5% of V2)
- **Acceptable**: F1 ≥ 0.735 (within 2% of V2)

**Deliverables**:
- 15 training archives
- Hyperparameter search results: `phase3c_hyperparam_results.csv`
- Best model configuration: `phase3c_best_config.json`
- Final report: `docs/handover/PHASE3C_OPTIMIZATION_RESULTS.md`
- Production-ready model and split configuration

---

## Technical Implementation

### Environment Setup
```bash
# Activate modern Python environment
source activate_modern.sh

# Verify dependencies
python -c "import torch, transformers, pandas, numpy; print('OK')"
```

### Data Generation Pattern
```python
# All splits follow this pattern
from src.data_augmentation.split_optimizer import create_complexity_stratified_split

create_complexity_stratified_split(
    df=master_df,                    # From data/manual_ner_extraction.csv
    split_name='split_name',
    test_complex_ratio=X,            # Target complexity (0-1)
    val_complex_ratio=0.25,          # Fixed at 25%
    train_size=0.70,
    val_size=0.15,
    test_size=0.15,
    seed=241,                        # Default seed
    output_dir='data/ner_splits_splitX/'
)
```

### Training Pattern
```python
# All training follows V2 baseline parameters
model = train_ner_model(
    data_dir='data/ner_splits_splitX/',
    output_dir='output/splitX/',
    model_name='allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500',
    learning_rate=2e-5,
    batch_size=16,
    epochs=10,
    early_stopping=False,
    seed=241
)
```

### Notebook Structure (for Google Colab)
All training should use loop-based notebook pattern from `phase2b_granular_training.ipynb`:
- Cell 1: Setup (imports, Drive mount)
- Cell 2: Configuration (splits list, parameters)
- Cell 3: Helper functions
- Cell 4: Data validation
- Cell 5: GPU check
- Cell 6: **Training loop** with error handling
- Cell 7: Results aggregation
- Cell 8: Upload to Drive

### Archive Organization
Each training run saves to:
```
collab_results/training_archives/{SESSION_ID}_split{X}/
├── data/
│   ├── training_results.csv
│   └── experiment_metadata.json
├── model/
│   ├── pytorch_model.bin
│   ├── config.json
│   └── training_args.bin
└── training_logs/
    └── training_output.log
```

### Results Tracking
Maintain a master results CSV:
```csv
Split,Session,Seed,Test_Complexity_Pct,Val_F1,Val_Precision,Val_Recall,Train_F1,Best_Epoch,Training_Time_Minutes,Notes
```

---

## Expected Outcomes

### After Phase 3A (Priority 1 & 2)
**Outcome 1: Split B is consistently optimal**
- Mean F1 across 5 seeds: ~0.728 ± 0.003
- High complexity less stable
- **Action**: Proceed with Split B for production
- **Next**: Phase 3C (hyperparameter optimization)

**Outcome 2: High complexity is more stable**
- Split B variance: ±0.010
- High complexity variance: ±0.003, mean ~0.724
- **Action**: Use 85-90% complexity for production
- **Next**: Phase 3C (optimize high complexity)

**Outcome 3: Both are unstable**
- Both show variance ±0.010
- **Action**: Training procedure is the issue, not split
- **Next**: Phase 3C (focus on training stability)

### After Phase 3B (Priority 3)
**Understanding of complexity landscape**:
- Safe zones identified
- Danger zones marked
- Optimal range characterized
- Production guidelines established

### After Phase 3C (Priority 4)
**Final production model**:
- F1 ≥ 0.740 achieved
- Optimal hyperparameters identified
- Training procedure documented
- Model ready for deployment

**If F1 < 0.740**:
- Document best achieved performance
- Remaining gap explained by:
  1. V2 test set differences
  2. V2 data augmentation
  3. V2 model advantages
  4. Hardware/software factors

---

## Decision Trees

### Decision Tree 1: After Phase 3A

```
Phase 3A Complete
├─ Split B stable (σ < 0.005) AND better than plateau?
│  ├─ YES → Use Split B (66%)
│  │  └─ Next: Phase 3C optimization on Split B
│  └─ NO
│     ├─ Plateau stable (σ < 0.005)?
│     │  ├─ YES → Use high complexity (85-90%)
│     │  │  └─ Next: Phase 3C optimization on 85-90%
│     │  └─ NO → Both unstable
│     │     └─ Next: Phase 3C focus on training stability
│
└─ Optional: Phase 3B (valley investigation)
   └─ Scientific interest, not production-critical
```

### Decision Tree 2: After Phase 3C

```
Hyperparameter Search Complete
├─ F1 ≥ 0.745?
│  ├─ YES → SUCCESS! Deploy to production
│  │  └─ Document: optimal split + hyperparameters
│  └─ NO
│     ├─ F1 ≥ 0.740?
│     │  ├─ YES → GOOD! Production ready
│     │  │  └─ Document: acceptable performance
│     │  └─ NO
│     │     ├─ F1 ≥ 0.735?
│     │     │  ├─ YES → ACCEPTABLE
│     │     │  │  └─ Document: remaining gap analysis
│     │     │  └─ NO
│     │     │     └─ Investigate:
│     │     │        ├─ V2 test set analysis
│     │     │        ├─ Data augmentation
│     │     │        └─ Alternative base models
```

---

## Resources Required

### Compute Resources

**Google Colab GPU Time**:
- Phase 3A: ~112 hours
- Phase 3B: ~56 hours
- Phase 3C: ~120 hours
- **Total**: ~288 GPU hours

**Recommended**: Colab Pro+ with A100 or T4 GPU

**Cost Estimate**:
- Colab Pro+: $50/month
- Estimated: 2-3 months if running continuously
- **Total**: ~$100-150

### Storage Requirements

**Google Drive**:
- Each training run: ~470 MB
- Phase 3A: 14 runs × 470 MB = ~6.6 GB
- Phase 3B: 7 runs × 470 MB = ~3.3 GB
- Phase 3C: 15 runs × 470 MB = ~7.1 GB
- **Total new**: ~17 GB
- **Cumulative** (with Phase 2+2B): ~30 GB

**Recommendation**: Ensure 50 GB free on Google Drive

### Human Resources

**Estimated effort per phase**:
- **Phase 3A**:
  - Setup: 4 hours
  - Monitoring: 8 hours (spot checks)
  - Analysis: 8 hours
  - **Total**: ~20 hours over 1-2 weeks

- **Phase 3B**:
  - Setup: 2 hours
  - Monitoring: 4 hours
  - Analysis: 6 hours
  - **Total**: ~12 hours over 1 week

- **Phase 3C**:
  - Setup: 4 hours
  - Monitoring: 12 hours
  - Analysis: 12 hours
  - Documentation: 8 hours
  - **Total**: ~36 hours over 2-3 weeks

**Grand Total**: ~68 human hours over 5-7 weeks

---

## Success Criteria

### Phase 3A Success
- [x] Split B variance quantified (σ < 0.005 for consistency)
- [x] High-complexity plateau validated (3 levels × 3 seeds)
- [x] Clear decision made: Split B vs high complexity
- [x] Phase 3C strategy determined

### Phase 3B Success
- [x] Valley mapped with 7 data points
- [x] Valley boundaries identified
- [x] Cause hypothesis proposed
- [x] Safe/danger zones documented

### Phase 3C Success
**Primary goal**:
- [x] F1 ≥ 0.740 achieved (within 1.5% of V2)

**Secondary goals**:
- [x] Optimal hyperparameters identified
- [x] Training procedure documented
- [x] Model artifacts saved
- [x] Production deployment guide created

**Tertiary goals**:
- [x] Remaining gap explained
- [x] Future work identified
- [x] Lessons learned documented

### Overall Phase 3 Success
**Minimum requirements**:
1. Split B validated OR high complexity validated
2. Production-ready model with F1 ≥ 0.735
3. Complete documentation
4. Deployment guide

**Ideal outcomes**:
1. F1 ≥ 0.745 (within 0.5% of V2)
2. Stable performance across seeds
3. Valley phenomenon explained
4. Clear production recommendations

---

## Risk Mitigation

### Risk 1: Both Split B and Plateau are Unstable
**Impact**: High - would invalidate Phase 2 conclusions
**Probability**: Low - at least one should be stable
**Mitigation**:
- If both unstable, the issue is training procedure not split
- Shift focus to training stability (learning rate schedules, warmup)
- Consider alternative base models

### Risk 2: Cannot Reach F1 ≥ 0.740
**Impact**: Medium - gap remains unexplained
**Probability**: Medium - hyperparameters may not bridge gap
**Mitigation**:
- Document best achieved performance
- Analyze V2 baseline more carefully:
  - Request V2 test set if possible
  - Investigate V2 training procedure
  - Check if V2 used data augmentation
- Consider this the practical limit of split optimization

### Risk 3: Valley Investigation Shows No Pattern
**Impact**: Low - doesn't affect production
**Probability**: Low - some pattern should emerge
**Mitigation**:
- Valley investigation is optional (Phase 3B)
- If inconclusive, simply avoid 55-60% range
- Focus on validated optimal range

### Risk 4: Compute Resources Exhausted
**Impact**: High - cannot complete experiments
**Probability**: Low with proper planning
**Mitigation**:
- Monitor GPU hours carefully
- Prioritize Phase 3A (highest ROI)
- Phase 3B is optional if resources limited
- Phase 3C can be reduced to broad search only (10 configs)

---

## Next Immediate Steps

### Step 1: Review and Approve Plan
- Review this document
- Confirm priorities
- Approve budget (time & compute)
- Set timeline expectations

### Step 2: Prepare Phase 3A Materials
- Create notebook: `phase3a_splitB_multiseed.ipynb`
- Create notebook: `phase3a_plateau_stability.ipynb`
- Prepare analysis scripts
- Set up results tracking

### Step 3: Execute Phase 3A
- Upload notebooks to Google Drive
- Run Split B validation (Priority 1)
- Run plateau testing (Priority 2)
- Monitor progress daily

### Step 4: Analyze and Decide
- Calculate variances
- Make decision: Split B vs plateau
- Document findings
- Plan Phase 3B/3C accordingly

---

## Questions for Discussion

1. **Timeline**: Is 5-7 weeks acceptable? Can we prioritize differently?
2. **Budget**: Is ~$150 for Colab Pro+ approved?
3. **Scope**: Should we do all of Phase 3B (valley investigation) or skip it?
4. **Target**: Is F1 ≥ 0.740 acceptable, or must we reach V2's 0.749?
5. **Risk tolerance**: If both Split B and plateau are unstable, pivot to training procedures immediately or investigate why?

---

## Appendices

### Appendix A: File Locations

**Phase 2/2B Results**:
- `docs/split_project/PHASE2B_FINAL_RESULTS.md`
- `docs/split_project/phase2_and_phase2b_combined_results.csv`
- `docs/split_project/phase2b_complete_analysis.png`

**Scripts**:
- Split generation: `scripts/create_phase2b_splits.py`
- Analysis: `docs/split_project/analyze_phase2b_complete.py`
- Summary: `docs/split_project/print_phase2b_summary.py`

**Training Archives**:
- `collab_results/training_archives/2025-11-03-*_split*/`

### Appendix B: Key Parameters

**Data Splits**:
- Train/Val/Test: 70% / 15% / 15%
- Val complexity: Always 25%
- Test complexity: Variable (experimental parameter)
- Default seed: 241

**Training Configuration (V2 Baseline)**:
- Model: `allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500`
- Learning rate: 2e-5
- Batch size: 16
- Epochs: 10
- Early stopping: Disabled
- Optimizer: AdamW
- Weight decay: 0.01

### Appendix C: Baseline Comparisons

| Configuration | Test Complexity | Val F1 | Status |
|--------------|----------------|--------|---------|
| V2 Baseline | ~17.0% | 0.7490 | TARGET |
| Split B (best) | 65.9% | 0.7281 | Current best |
| Current Baseline | 48.6% | 0.6440 | Original poor |

**Gap to close**: 0.0209 points (2.8% of V2 performance)

---

**Document End**

For questions or clarifications, refer to:
- Phase 2B results: `docs/split_project/PHASE2B_FINAL_RESULTS.md`
- Original Phase 2: `PHASE2_COMPLETE_ANALYSIS.md`
- Starting documentation: `docs/starting_doc.md`
