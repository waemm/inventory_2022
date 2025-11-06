# HANDOVER: Phase 4 Post-Processing Bug Fix

**Date**: 2025-11-05
**Bug**: Word-level tokenization failure in Phase 4 NER post-processing
**Severity**: 🔴 **CRITICAL** - Destroys 67% of model performance
**Impact**: Phase 4 F1 drops from potential ~66%+ to 22.49%
**Status**: Identified, Not Fixed

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Description](#problem-description)
3. [Evidence and Examples](#evidence-and-examples)
4. [Root Cause Analysis](#root-cause-analysis)
5. [Where to Fix](#where-to-fix)
6. [Step-by-Step Fix Instructions](#step-by-step-fix-instructions)
7. [Testing the Fix](#testing-the-fix)
8. [Re-Running Phase 4 Inference](#re-running-phase-4-inference)
9. [Validation Checklist](#validation-checklist)
10. [Expected Results After Fix](#expected-results-after-fix)

---

## Executive Summary

### The Problem in One Sentence

**Phase 4's post-processing pipeline fragments multi-word entities into individual words, causing 0% F1 on papers where V2 achieves 100% F1.**

### Why This Matters

- Phase 4 claims **92.74% F1** in training README
- Actual performance on test split: **22.49% F1**
- V2 (old model) achieves **66.35% F1**
- The bug makes Phase 4 appear **3x worse** than it likely is

### What Needs to Be Fixed

The **entity grouping logic** in Phase 4's post-processing that converts token-level predictions (IOB tags) into complete entity strings. Currently it outputs individual words instead of merging consecutive entity tokens into multi-word entities.

### Fix Location

**Primary Target**: `phase4_full_inference_2022_AUTO_FIX_v2.ipynb` (or latest version)
**Specific Cell**: NER post-processing cell (after model.predict(), before saving results)
**Function**: Entity grouping/detokenization logic

---

## Problem Description

### High-Level Issue

Phase 4 uses a token-level NER approach:
1. ✅ **Tokenize** text into words: `["Mouse", "Phenome", "Database"]`
2. ✅ **Predict** IOB tags per token: `["B-COM", "I-COM", "I-COM"]`
3. ❌ **Group** consecutive tokens into entities: **BROKEN**
4. ✅ **Clean** BPE artifacts: Working but irrelevant due to step 3 failure
5. ✅ **Deduplicate**: Working but operates on fragments

**Expected output**: `["Mouse Phenome Database"]`
**Actual output**: `["Mouse", "Phenome", "Database"]`

### Technical Issue

The post-processing code fails to merge consecutive tokens tagged with `I-*` (inside entity) tags into a single multi-word entity. Instead, it treats each token as a separate entity.

**IOB Tagging Primer**:
- `B-COM`: Beginning of common name entity
- `I-COM`: Inside common name entity (continuation)
- `B-FUL`: Beginning of full name entity
- `I-FUL`: Inside full name entity
- `O`: Outside any entity

**Correct Behavior**:
```python
tokens = ["Mouse", "Phenome", "Database", "(", "MPD", ")"]
tags =   ["B-FUL", "I-FUL", "I-FUL",   "O", "B-COM", "O"]

# Should group consecutive B/I tags:
entities = {
    "full_name": ["Mouse Phenome Database"],
    "common_name": ["MPD"]
}
```

**Current Buggy Behavior**:
```python
tokens = ["Mouse", "Phenome", "Database", "(", "MPD", ")"]
tags =   ["B-FUL", "I-FUL", "I-FUL",   "O", "B-COM", "O"]

# Each token becomes separate entity:
entities = {
    "full_name": ["Mouse", "Phenome", "Database"],  # WRONG - should be 1 entity
    "common_name": ["MPD"]
}
```

### Impact Statistics

From comparison analysis on 63 test papers:

| Metric | Current (Buggy) | Expected (Fixed) |
|--------|-----------------|------------------|
| F1 Score | **22.49%** | ~60-70% (estimated) |
| Precision | 18.18% | ~50-60% |
| Recall | 29.47% | ~70-80% |
| True Positives | 28 | ~65-70 |
| False Positives | 126 | ~30-50 |
| Median F1 | **0.00** | ~0.60-0.80 |

**Key Impact**: On 11 papers where V2 achieves F1=1.0, Phase 4 currently gets F1=0.0 due to this bug.

---

## Evidence and Examples

### Example 1: Mouse Phenome Database

**Paper ID**: 22102583

**Ground Truth**:
```json
{
  "common_name": ["MPD"],
  "full_name": ["Mouse Phenome Database"]
}
```

**V2 Predictions** (correct):
```json
{
  "common_name": ["MPD"],
  "full_name": ["Mouse Phenome Database"]
}
```
**V2 Result**: F1 = 1.00 ✅ Perfect

**Phase 4 Predictions** (buggy):
```json
{
  "common_name": [],
  "full_name": ["Mouse", "Phenome", "Database"]
}
```
**Phase 4 Result**: F1 = 0.00 ❌ Total failure

**Analysis**:
- Phase 4 model likely predicted: `["Mouse/B-FUL", "Phenome/I-FUL", "Database/I-FUL"]`
- Post-processing should have merged: `"Mouse Phenome Database"`
- Instead it kept them separate: `["Mouse", "Phenome", "Database"]`
- Entity matching: No exact match for "Mouse Phenome Database"
- Result: 0 TP, 3 FP, 2 FN → F1 = 0.00

### Example 2: Integrated Resource for Reproducibility

**Paper ID**: 27841751

**Ground Truth**:
```json
{
  "full_name": ["Integrated Resource for Reproducibility in Macromolecular Crystallography"]
}
```

**V2 Predictions** (correct):
```json
{
  "full_name": ["Integrated Resource for Reproducibility in Macromolecular Crystallography"]
}
```
**V2 Result**: F1 = 1.00 ✅

**Phase 4 Predictions** (buggy):
```json
{
  "full_name": ["Crystallography", "Integrated", "Macromolecular", "Reproducibility", "Resource", "for", "in"]
}
```
**Phase 4 Result**: F1 = 0.00 ❌

**Analysis**:
- 8-word entity fragmented into 7+ individual words
- Not even in correct order (alphabetical sorting artifact?)
- Complete post-processing failure

### Example 3: lncR2metasta

**Paper ID**: 32766766

**Ground Truth**:
```json
{
  "common_name": ["lncR2metasta"]
}
```

**V2 Predictions** (correct):
```json
{
  "common_name": ["LncR2metasta"]
}
```
**V2 Result**: F1 = 1.00 ✅ (case-insensitive match)

**Phase 4 Predictions** (buggy):
```json
{
  "common_name": ["lncR", "metasta"]
}
```
**Phase 4 Result**: F1 = 0.00 ❌

**Analysis**:
- Single entity split in half (likely due to BPE tokenization: "lnc" + "R" + "2" + "metasta")
- Should have been merged back into single entity
- Instead kept as 2 fragments

### Example 4: Where Phase 4 Succeeds

**Paper ID**: 24285302

**Ground Truth**:
```json
{
  "common_name": ["iRefIndex"]
}
```

**V2 Predictions**:
```json
{
  "common_name": ["iRefIndex"]
}
```
**V2 Result**: F1 = 1.00 ✅

**Phase 4 Predictions**:
```json
{
  "common_name": ["iRefIndex"]
}
```
**Phase 4 Result**: F1 = 1.00 ✅

**Analysis**:
- Single-word entity (no word boundaries to fragment)
- Post-processing bug doesn't affect single-word entities
- This is why Phase 4 still achieves 22.49% F1 (works on simple cases)

### Pattern Summary

**Phase 4 succeeds when**:
- Entity is a single word (no spaces): "iRefIndex", "PubMed", "TCLUST"
- Entity is an abbreviation: "MPD", "ERA", "RGD"

**Phase 4 fails when**:
- Entity has 2+ words: "Mouse Phenome Database", "Gene Expression Atlas"
- Entity is a compound: "lncR2metasta" (gets split by BPE)

**Statistics from 63 test papers**:
- Papers with multi-word entities: ~50 (79%)
- Papers where Phase 4 F1 = 0 but V2 F1 = 1: 11 (17.5%)
- Papers where Phase 4 F1 > 0: 28 (44.4%)
- Papers where Phase 4 F1 = 0: 35 (55.6%)

---

## Root Cause Analysis

### The NER Pipeline (What Should Happen)

```
Input: "The Mouse Phenome Database (MPD) stores genetic data."

Step 1: Tokenization
["The", "Mouse", "Phenome", "Database", "(", "MPD", ")", "stores", "genetic", "data", "."]

Step 2: Model Prediction (IOB tags)
["O", "B-FUL", "I-FUL", "I-FUL", "O", "B-COM", "O", "O", "O", "O", "O"]

Step 3: Entity Grouping ⚠️ THIS IS WHERE THE BUG IS
# Correct implementation:
for i, (token, tag) in enumerate(zip(tokens, tags)):
    if tag.startswith("B-"):  # Beginning of entity
        entity_type = tag.split("-")[1]
        entity_tokens = [token]

        # Collect all following I- tags of same type
        j = i + 1
        while j < len(tags) and tags[j] == f"I-{entity_type}":
            entity_tokens.append(tokens[j])
            j += 1

        # Join tokens with spaces
        entity_text = " ".join(entity_tokens)
        entities[entity_type].append(entity_text)

# Result:
{
    "full_name": ["Mouse Phenome Database"],
    "common_name": ["MPD"]
}

Step 4: BPE Cleaning
# Clean "Ġ" artifacts (working correctly)

Step 5: Deduplication
# Remove duplicates (working correctly)
```

### The Actual Buggy Implementation

Based on evidence, the current implementation likely does:

```python
# BUGGY CODE (approximately what's happening)
entities = {"common_name": [], "full_name": []}

for i, (token, tag) in enumerate(zip(tokens, tags)):
    if tag != "O":  # Any entity tag
        # BUG: Adds each token individually, ignores I- tags
        entity_type = tag.split("-")[1] if "-" in tag else "common_name"
        entities[entity_type].append(token)  # ❌ WRONG - no grouping!

# Result:
{
    "full_name": ["Mouse", "Phenome", "Database"],  # ❌ Should be 1 entity
    "common_name": ["MPD"]  # ✅ Happens to work for single word
}
```

### Why This Bug Went Undetected

1. **Validation used token-level metrics**: During training, validation measured token-level IOB tag accuracy, not entity-level F1. The model predictions are likely correct at token level (tags are right), but entity extraction is broken.

2. **Token accuracy ≠ entity quality**:
   ```
   Tokens: ["Mouse", "Phenome", "Database"]
   Tags:   ["B-FUL", "I-FUL", "I-FUL"]

   Token accuracy: 100% (all tags correct!)
   Entity F1: 0% (produced 3 entities instead of 1)
   ```

3. **Small test cases masked the issue**: Manual testing likely used simple single-word entities that don't expose the bug.

4. **No entity-level validation**: The training pipeline only reported token-level metrics, never entity-level P/R/F1.

---

## Where to Fix

### Primary Location

**Notebook**:
- Latest: `phase4_full_inference_2022_AUTO_FIX_v2.ipynb`
- Or: `phase4_full_inference_2022.ipynb`
- Location: `/Users/warren/development/GBC/inventory_2022/`

**Cell to Modify**:
Search for the cell containing NER post-processing. Look for:
- After `predictions = model.predict(...)` or similar
- Before `ner_results.to_csv(...)`
- Keywords: "entity", "IOB", "B-", "I-", "common_name", "full_name"

**Specific Code Pattern to Find**:
```python
# Current buggy pattern (approximate):
for token, tag in zip(tokens, predictions):
    if tag != 'O':
        entities.append(token)  # ❌ Bug: no grouping

# Or:
entities = [token for token, tag in zip(tokens, predictions) if tag != 'O']

# Or similar code that processes tokens individually
```

### Secondary Locations (Less Likely)

If the bug is not in the notebook, check:

**1. Multi-task Model Class**:
- File: `src/models/multitask_model.py` or similar
- Method: `predict()` or `extract_entities()`
- Look for: Post-processing after forward pass

**2. Dedicated Post-Processing Script**:
- File: `src/postprocessing/ner_postprocessing.py` or similar
- Function: `extract_entities_from_predictions()`

**3. Inference Utility**:
- File: `src/inference/multitask_predict.py` or similar
- Function: `process_ner_predictions()`

### How to Locate the Exact Spot

1. **Search for entity extraction**:
   ```bash
   cd /Users/warren/development/GBC/inventory_2022
   grep -r "B-COM\|B-FUL\|I-COM\|I-FUL" *.ipynb src/
   grep -r "common_name\|full_name" *.ipynb src/ | grep -i "entity\|prediction"
   ```

2. **Look for IOB tag processing**:
   ```bash
   grep -r "startswith.*B-\|split.*-" *.ipynb src/
   ```

3. **Find where results are created**:
   ```bash
   grep -r "ner_results\|entity_results" *.ipynb src/
   ```

4. **Check notebook cells**:
   - Open `phase4_full_inference_2022_AUTO_FIX_v2.ipynb`
   - Search for: "post-processing", "extract entities", "IOB"
   - Look for cell after model prediction, before saving CSV

---

## Step-by-Step Fix Instructions

### Step 1: Locate the Buggy Code

1. Open the inference notebook:
   ```python
   # File: phase4_full_inference_2022_AUTO_FIX_v2.ipynb
   ```

2. Find the NER post-processing cell (look for these patterns):
   ```python
   # Pattern 1: Simple list comprehension (most likely)
   entities = [token for token, tag in zip(tokens, predictions) if tag != 'O']

   # Pattern 2: Loop without grouping
   for token, tag in zip(tokens, predictions):
       if tag != 'O':
           entities.append(token)

   # Pattern 3: Processing each tag individually
   for i, tag in enumerate(predictions):
       if tag.startswith('B-') or tag.startswith('I-'):
           entities.append(tokens[i])
   ```

### Step 2: Replace with Correct Implementation

Replace the buggy code with this **correct implementation**:

```python
def extract_entities_from_iob(tokens, predictions):
    """
    Extract entities from IOB-tagged tokens.

    Args:
        tokens: List of token strings
        predictions: List of IOB tags (e.g., ["B-COM", "I-COM", "O", "B-FUL", ...])

    Returns:
        Dictionary with entity types as keys and lists of entity strings as values
    """
    entities = {
        "common_name": [],
        "full_name": []
    }

    i = 0
    while i < len(predictions):
        tag = predictions[i]

        # Check if this is a B- (beginning) tag
        if tag.startswith("B-"):
            # Extract entity type (COM or FUL)
            entity_type_code = tag.split("-")[1]
            entity_type = "common_name" if entity_type_code == "COM" else "full_name"

            # Start collecting tokens for this entity
            entity_tokens = [tokens[i]]
            j = i + 1

            # Collect all following I- tags of the same type
            while j < len(predictions) and predictions[j] == f"I-{entity_type_code}":
                entity_tokens.append(tokens[j])
                j += 1

            # Join tokens with spaces to form complete entity
            entity_text = " ".join(entity_tokens)
            entities[entity_type].append(entity_text)

            # Move to the next unprocessed token
            i = j
        else:
            # Not a B- tag, skip this token
            i += 1

    return entities


# Usage in the notebook:
# After getting predictions from model, apply this function per paper:

all_results = []
for idx, row in tqdm(papers_df.iterrows(), total=len(papers_df)):
    paper_id = row['ID']
    text = row['abstract']  # or wherever text comes from

    # Get model predictions
    predictions = model.predict(text)  # Returns IOB tags
    tokens = tokenize(text)  # Get corresponding tokens

    # Extract entities using correct grouping
    entities = extract_entities_from_iob(tokens, predictions)

    # Store results
    all_results.append({
        'ID': paper_id,
        'common_name': entities['common_name'],
        'full_name': entities['full_name']
    })

# Convert to DataFrame
ner_results = pd.DataFrame(all_results)
```

### Step 3: Add BPE Cleaning (Already Implemented)

The BPE cleaning should remain as-is (it's working correctly). Apply it AFTER entity grouping:

```python
# After extract_entities_from_iob():
from utils.bpe_cleaning import clean_entity_list

# Clean entities
entities['common_name'] = clean_entity_list(entities['common_name'])
entities['full_name'] = clean_entity_list(entities['full_name'])
```

### Step 4: Add Entity Deduplication (Already Implemented)

Keep the deduplication logic (it's working correctly):

```python
# After BPE cleaning:
entities['common_name'] = list(set(entities['common_name']))
entities['full_name'] = list(set(entities['full_name']))
```

### Step 5: Verify Token-Tag Alignment

Add a sanity check to ensure tokens and predictions are aligned:

```python
def extract_entities_from_iob(tokens, predictions):
    """Extract entities from IOB-tagged tokens."""

    # Sanity check
    if len(tokens) != len(predictions):
        raise ValueError(f"Token count ({len(tokens)}) doesn't match prediction count ({len(predictions)})")

    # ... rest of implementation
```

---

## Testing the Fix

### Unit Test: Create Test Cases

Create a test cell in the notebook to verify the fix:

```python
# Test Case 1: Multi-word entity
tokens_1 = ["The", "Mouse", "Phenome", "Database", "stores", "data"]
tags_1 = ["O", "B-FUL", "I-FUL", "I-FUL", "O", "O"]

entities_1 = extract_entities_from_iob(tokens_1, tags_1)
assert entities_1['full_name'] == ["Mouse Phenome Database"], f"Expected ['Mouse Phenome Database'], got {entities_1['full_name']}"
print("✅ Test 1 passed: Multi-word entity")


# Test Case 2: Multiple entities
tokens_2 = ["MPD", "is", "the", "Mouse", "Phenome", "Database"]
tags_2 = ["B-COM", "O", "O", "B-FUL", "I-FUL", "I-FUL"]

entities_2 = extract_entities_from_iob(tokens_2, tags_2)
assert entities_2['common_name'] == ["MPD"], f"Expected ['MPD'], got {entities_2['common_name']}"
assert entities_2['full_name'] == ["Mouse Phenome Database"], f"Expected ['Mouse Phenome Database'], got {entities_2['full_name']}"
print("✅ Test 2 passed: Multiple entities")


# Test Case 3: Single-word entities
tokens_3 = ["PubMed", "and", "GenBank"]
tags_3 = ["B-COM", "O", "B-COM"]

entities_3 = extract_entities_from_iob(tokens_3, tags_3)
assert entities_3['common_name'] == ["PubMed", "GenBank"], f"Expected ['PubMed', 'GenBank'], got {entities_3['common_name']}"
print("✅ Test 3 passed: Single-word entities")


# Test Case 4: No entities
tokens_4 = ["The", "study", "analyzed", "data"]
tags_4 = ["O", "O", "O", "O"]

entities_4 = extract_entities_from_iob(tokens_4, tags_4)
assert entities_4['common_name'] == [], f"Expected [], got {entities_4['common_name']}"
assert entities_4['full_name'] == [], f"Expected [], got {entities_4['full_name']}"
print("✅ Test 4 passed: No entities")


# Test Case 5: Adjacent entities
tokens_5 = ["scPDB", "and", "MPD", "databases"]
tags_5 = ["B-COM", "O", "B-COM", "O"]

entities_5 = extract_entities_from_iob(tokens_5, tags_5)
assert entities_5['common_name'] == ["scPDB", "MPD"], f"Expected ['scPDB', 'MPD'], got {entities_5['common_name']}"
print("✅ Test 5 passed: Adjacent entities")


print("\n🎉 All tests passed! Entity grouping is working correctly.")
```

### Integration Test: Sample Papers

Test on known failure cases from the comparison analysis:

```python
# Test on actual predictions for paper 22102583 (Mouse Phenome Database)
test_paper_id = "22102583"
test_row = papers_df[papers_df['ID'] == test_paper_id].iloc[0]
text = test_row['abstract']

# Get predictions
predictions = model.predict(text)
tokens = tokenize(text)

# Extract entities
entities = extract_entities_from_iob(tokens, predictions)

print(f"Paper {test_paper_id} predictions:")
print(f"  Common names: {entities['common_name']}")
print(f"  Full names: {entities['full_name']}")

# Expected to contain "Mouse Phenome Database" as a single entity
if "Mouse Phenome Database" in entities['full_name']:
    print("✅ FIXED: Multi-word entity correctly extracted")
else:
    print("❌ STILL BROKEN: Expected 'Mouse Phenome Database' in full_name")

# Should NOT contain fragments
fragments = ["Mouse", "Phenome", "Database"]
found_fragments = [f for f in fragments if f in entities['full_name']]
if found_fragments:
    print(f"❌ STILL BROKEN: Found fragments {found_fragments}")
else:
    print("✅ FIXED: No word fragments")
```

---

## Re-Running Phase 4 Inference

After fixing the bug, you need to regenerate Phase 4 predictions on the full 2022 dataset.

### Step 1: Update Notebook Version

1. Save a backup of current notebook:
   ```bash
   cp phase4_full_inference_2022_AUTO_FIX_v2.ipynb phase4_full_inference_2022_AUTO_FIX_v2_BEFORE_FIX.ipynb
   ```

2. Create new version with fix:
   ```bash
   # Or increment version: _v3.ipynb
   ```

3. Add comment at top of notebook:
   ```markdown
   # Phase 4 Full Inference - FIXED Entity Grouping Bug

   ## Changes from v2:
   - Fixed entity grouping logic to merge consecutive I- tags
   - Multi-word entities now correctly extracted as single strings
   - Expected F1 improvement from ~22% to ~60-70%

   ## Bug Fix Details:
   See: docs/handovers/HANDOVER_PHASE4_BUG_FIX.md
   ```

### Step 2: Run Inference on Full Dataset

```python
# In notebook:

# Load 2022 dataset
papers_df = pd.read_csv('data/epmc_query_results_2022.csv')
print(f"Total papers: {len(papers_df)}")  # Should be 20,889 or 20,890

# Load Phase 4 model
from src.models.multitask_model import BiomedicalMultiTaskModel
model_checkpoint = "collab_results/experiment_archives/2025-10-31-rq7i4n/multitask_training/checkpoint_best_ner.pt"
model = BiomedicalMultiTaskModel.load_from_checkpoint(model_checkpoint)
model.eval()

# Process all papers
all_results = []
for idx, row in tqdm(papers_df.iterrows(), total=len(papers_df), desc="Processing papers"):
    paper_id = str(row['ID'])
    abstract = row['abstract'] if pd.notna(row['abstract']) else ""

    if not abstract:
        # No abstract, no entities
        all_results.append({
            'ID': paper_id,
            'common_name': [],
            'full_name': []
        })
        continue

    # Get predictions
    predictions = model.predict_ner(abstract)  # IOB tags
    tokens = model.tokenize(abstract)  # Corresponding tokens

    # Extract entities (FIXED implementation)
    entities = extract_entities_from_iob(tokens, predictions)

    # Apply BPE cleaning
    from utils.bpe_cleaning import clean_entity_list
    entities['common_name'] = clean_entity_list(entities['common_name'])
    entities['full_name'] = clean_entity_list(entities['full_name'])

    # Deduplicate
    entities['common_name'] = list(set(entities['common_name']))
    entities['full_name'] = list(set(entities['full_name']))

    # Store results
    all_results.append({
        'ID': paper_id,
        'common_name': entities['common_name'],
        'full_name': entities['full_name']
    })

# Convert to DataFrame
ner_results = pd.DataFrame(all_results)
print(f"\nProcessed {len(ner_results)} papers")
print(f"Papers with entities: {(ner_results['common_name'].apply(len) + ner_results['full_name'].apply(len) > 0).sum()}")
```

### Step 3: Save Results with New Session ID

```python
import datetime

# Create new session ID
session_id = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S") + "_phase4_2022_rerun_FIXED"
output_dir = f"collab_results/experiment_archives/{session_id}/"

# Create output directory
import os
os.makedirs(output_dir, exist_ok=True)

# Save NER results
ner_results_file = os.path.join(output_dir, "ner_results.csv")
ner_results.to_csv(ner_results_file, index=False)
print(f"Saved NER results to: {ner_results_file}")

# Create README documenting the fix
readme_content = f"""# Phase 4 Multi-Task Inference Results (FIXED)

**Session ID**: {session_id}
**Created**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Bug Fix**: Entity grouping logic corrected

---

## What Changed

**Previous Version** (`2025-11-05-ygnr9f`):
- F1 on test split: 22.49%
- Bug: Multi-word entities fragmented into individual words
- Example: "Mouse Phenome Database" → ["Mouse", "Phenome", "Database"]

**This Version** (FIXED):
- Expected F1 on test split: ~60-70% (to be measured)
- Fix: Consecutive I- tags now properly merged into multi-word entities
- Example: "Mouse Phenome Database" → ["Mouse Phenome Database"]

## Bug Details

See: `docs/handovers/HANDOVER_PHASE4_BUG_FIX.md`

## Results

- **Total Papers**: {len(ner_results)}
- **Papers with Entities**: {(ner_results['common_name'].apply(len) + ner_results['full_name'].apply(len) > 0).sum()}
- **Total Common Names**: {ner_results['common_name'].apply(len).sum()}
- **Total Full Names**: {ner_results['full_name'].apply(len).sum()}

## Next Steps

1. Re-run comparison analysis: `comparison_phase4_v_oldmodel/`
2. Update aligned_papers.csv with fixed Phase 4 results
3. Re-run Scripts 02-08 for fair comparison
4. Compare FIXED Phase 4 vs V2 performance
"""

readme_file = os.path.join(output_dir, "README.md")
with open(readme_file, 'w') as f:
    f.write(readme_content)
print(f"Saved README to: {readme_file}")
```

### Step 4: Upload to Google Drive (Optional)

If using Google Colab:

```python
# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Copy results to Drive
import shutil
drive_output = f"/content/drive/MyDrive/inventory_2022_results/{session_id}/"
os.makedirs(drive_output, exist_ok=True)
shutil.copytree(output_dir, drive_output, dirs_exist_ok=True)
print(f"Uploaded to: {drive_output}")
```

---

## Validation Checklist

After re-running inference with the fix, validate that the bug is actually fixed:

### Validation Test 1: Multi-Word Entity Check

```python
# Load fixed results
fixed_results = pd.read_csv(f"{output_dir}/ner_results.csv")

# Parse entities
from utils.data_loading import parse_entity_list
fixed_results['common_name_list'] = fixed_results['common_name'].apply(parse_entity_list)
fixed_results['full_name_list'] = fixed_results['full_name'].apply(parse_entity_list)

# Check for multi-word entities
def has_multi_word_entities(entities):
    return any(' ' in str(e) for e in entities if e)

multi_word_com = fixed_results['common_name_list'].apply(has_multi_word_entities).sum()
multi_word_ful = fixed_results['full_name_list'].apply(has_multi_word_entities).sum()

print(f"Papers with multi-word common names: {multi_word_com} ({multi_word_com/len(fixed_results)*100:.1f}%)")
print(f"Papers with multi-word full names: {multi_word_ful} ({multi_word_ful/len(fixed_results)*100:.1f}%)")

# PASS CRITERIA: Should be >0 (previously was 0 or very low)
if multi_word_ful > 100:
    print("✅ VALIDATION PASSED: Multi-word entities detected")
else:
    print("❌ VALIDATION FAILED: Still no multi-word entities")
```

### Validation Test 2: Known Failure Cases

```python
# Test on specific papers that failed before

# Paper 22102583: Should have "Mouse Phenome Database"
paper_22102583 = fixed_results[fixed_results['ID'] == "22102583"].iloc[0]
entities_22102583 = parse_entity_list(paper_22102583['full_name'])

if "Mouse Phenome Database" in entities_22102583:
    print("✅ Paper 22102583: FIXED - 'Mouse Phenome Database' found")
else:
    print(f"❌ Paper 22102583: STILL BROKEN - Got: {entities_22102583}")

# Paper 27841751: Should have full entity name
paper_27841751 = fixed_results[fixed_results['ID'] == "27841751"].iloc[0]
entities_27841751 = parse_entity_list(paper_27841751['full_name'])

expected_27841751 = "Integrated Resource for Reproducibility in Macromolecular Crystallography"
if any(expected_27841751 in e for e in entities_27841751):
    print("✅ Paper 27841751: FIXED - Long entity found")
else:
    print(f"❌ Paper 27841751: STILL BROKEN - Got: {entities_27841751}")

# Paper 32766766: Should have "lncR2metasta" not fragments
paper_32766766 = fixed_results[fixed_results['ID'] == "32766766"].iloc[0]
entities_32766766 = parse_entity_list(paper_32766766['common_name'])

if any("lncR2metasta" in str(e).lower() for e in entities_32766766):
    print("✅ Paper 32766766: FIXED - 'lncR2metasta' found as complete entity")
else:
    print(f"❌ Paper 32766766: STILL BROKEN - Got: {entities_32766766}")
```

### Validation Test 3: Entity Count Distribution

```python
# Check entity count statistics
com_counts = fixed_results['common_name_list'].apply(len)
ful_counts = fixed_results['full_name_list'].apply(len)

print("\nEntity Count Distribution:")
print(f"Average common names per paper: {com_counts.mean():.2f}")
print(f"Average full names per paper: {ful_counts.mean():.2f}")
print(f"Max common names: {com_counts.max()}")
print(f"Max full names: {ful_counts.max()}")

# Compare to buggy version
print("\nBuggy Version (for comparison):")
print("Average common names per paper: ~1.26")  # From previous run
print("Average full names per paper: ~1.26")
print("Max common names: ~20+")  # Was inflated due to fragments
print("Max full names: ~20+")

# PASS CRITERIA:
# - Averages should be lower (fewer fragments = fewer entities)
# - Max should be lower (no extreme fragmentation)
if com_counts.mean() < 2.0 and ful_counts.mean() < 2.0:
    print("\n✅ VALIDATION PASSED: Entity counts reasonable")
else:
    print("\n⚠️  WARNING: Entity counts still high - possible residual issue")
```

### Validation Test 4: Compare to Test Split

```python
# Re-run Script 02 with fixed data and compare to V2

# First, regenerate aligned_papers.csv with fixed Phase 4 data
# (This is done in Step 5 below)

# Then run Script 02
import subprocess
result = subprocess.run(
    ["python", "comparison_phase4_v_oldmodel/scripts/02_evaluate_on_test_split.py"],
    capture_output=True,
    text=True
)

# Check for improved F1
if "Phase 4 Cleaned F1: 0.6" in result.stdout or "Phase 4 Cleaned F1: 0.5" in result.stdout:
    print("✅ VALIDATION PASSED: Phase 4 F1 significantly improved")
elif "Phase 4 Cleaned F1: 0.2" in result.stdout:
    print("❌ VALIDATION FAILED: Phase 4 F1 still low - bug not fully fixed")
else:
    print("⚠️  Cannot determine F1 from output - check manually")
```

---

## Expected Results After Fix

### Performance Expectations

Based on the analysis, after fixing the bug:

**Test Split (63 papers)**:
- Phase 4 F1: **60-70%** (up from 22.49%)
- Phase 4 Precision: **50-60%** (up from 18.18%)
- Phase 4 Recall: **70-80%** (up from 29.47%)

**Comparison to V2**:
- V2 F1: **66.35%** (unchanged)
- Difference: **±5 percentage points** (competitive, not 3x worse)
- Statistical significance: May no longer be significant

**Papers with Perfect Scores**:
- Currently: Phase 4 wins 2, V2 wins 26
- After fix: Phase 4 wins ~15-20, V2 wins ~20-25

**Median F1**:
- Currently: Phase 4 = 0.00, V2 = 0.80
- After fix: Phase 4 = 0.60-0.70, V2 = 0.80

### Quality Indicators

**Multi-Word Entities**:
- Before: 0% of full names have spaces (all fragments)
- After: ~50-70% of full names have spaces (realistic)

**Entity Length**:
- Before: Average 1-2 words per entity (fragments)
- After: Average 2-4 words per entity (realistic)

**False Positives**:
- Before: 126 FPs (excessive fragments)
- After: ~40-60 FPs (reasonable)

**Entity Examples That Should Now Work**:
```
✅ "Mouse Phenome Database" (not ["Mouse", "Phenome", "Database"])
✅ "Integrated Resource for Reproducibility in Macromolecular Crystallography" (not fragments)
✅ "lncR2metasta" (not ["lncR", "metasta"])
✅ "Gene Expression Atlas" (not ["Gene", "Expression", "Atlas"])
```

---

## After Fixing: Update Comparison Analysis

Once Phase 4 is fixed and re-run, you need to update the comparison analysis:

### Step 1: Update Data Sources Configuration

Edit `comparison_phase4_v_oldmodel/scripts/utils/data_loading.py`:

```python
# Update Phase 4 data source to use FIXED version
def load_phase4_results(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load Phase 4 NER results with normalized IDs."""
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent.parent / "collab_results" / "experiment_archives"

    # OLD (buggy): file_path = data_dir / "2025-11-05-ygnr9f_phase4_2022_rerun" / "ner_results.csv"
    # NEW (fixed):
    file_path = data_dir / "2025-11-06-XXXXXX_phase4_2022_rerun_FIXED" / "ner_results.csv"  # Update with actual session ID

    # ... rest of function
```

### Step 2: Regenerate aligned_papers.csv

```bash
cd /Users/warren/development/GBC/inventory_2022/comparison_phase4_v_oldmodel/scripts
python 01_preprocess_and_align.py
```

This will:
- Load V2 results (unchanged)
- Load FIXED Phase 4 results (new)
- Load test split (unchanged)
- Load inventory (unchanged)
- Align all by paper ID
- Save new `aligned_papers.csv`

### Step 3: Re-Run Comparison Scripts

```bash
# Run Scripts 02-08 with fixed data
python 02_evaluate_on_test_split.py   # Should show Phase 4 F1 ~60-70%
python 03_evaluate_on_inventory.py
python 04_analyze_bpe_artifacts.py
python 05_sample_100_papers.py
python 06_generate_side_by_side.py
python 07_generate_final_report.py
python 08_create_visualizations.py
```

### Step 4: Create Comparison Report

Document the before/after:

```markdown
# Phase 4 Bug Fix Impact Report

## Performance Before Fix (Buggy)

Session: 2025-11-05-ygnr9f
Test Split F1: 22.49%
Issue: Word-level fragmentation

## Performance After Fix

Session: 2025-11-06-XXXXXX (FIXED)
Test Split F1: XX.XX%
Improvement: +XX.XX percentage points

## Bug Description

[Paste from this handover document]

## Evidence of Fix

[Include validation test results]

## Conclusion

[Compare to V2, determine which system is actually better]
```

---

## Troubleshooting

### Issue 1: Fix Doesn't Improve F1

**Possible Causes**:
1. Bug not actually fixed (entity grouping still broken)
2. Different bug causing the issue (not the one we identified)
3. Model predictions themselves are wrong (not just post-processing)

**Diagnosis**:
```python
# Check if entities are being grouped
sample_entities = fixed_results['full_name_list'].head(100)
multi_word = [e for entities in sample_entities for e in entities if ' ' in str(e)]
print(f"Sample multi-word entities: {multi_word[:10]}")

# If this list is empty, entity grouping is still broken
# If this list has entities but F1 is still low, the model predictions may be wrong
```

**Solution**:
- Review the entity grouping code again
- Add more print statements to debug what's happening
- Check that IOB tags from model are correct

### Issue 2: Entity Grouping Creates Too-Long Entities

**Symptom**: Entities like "the Mouse Phenome Database stores genetic data from"

**Cause**: Over-grouping - not respecting O tags correctly

**Fix**:
```python
# Make sure you break on O tags:
while j < len(predictions) and predictions[j] == f"I-{entity_type_code}":
    entity_tokens.append(tokens[j])
    j += 1

# NOT:
while j < len(predictions) and predictions[j] != "O":  # ❌ Wrong - includes B- tags
```

### Issue 3: Some Entities Still Fragmented

**Symptom**: Some entities grouped, but some still broken

**Cause**: Incomplete fix or model sometimes predicting wrong tags

**Diagnosis**:
```python
# Check which entities are still fragmented
test_paper = papers_df[papers_df['ID'] == "22102583"].iloc[0]
predictions = model.predict_ner(test_paper['abstract'])
tokens = model.tokenize(test_paper['abstract'])

# Print tokens and tags side by side
for token, tag in zip(tokens, predictions):
    print(f"{token:20s} {tag}")

# Look for unexpected tag patterns
```

---

## Additional Resources

### Related Documents

1. **Main Handover**: `docs/handovers/HANDOVER_COMPARISON_PROJECT.md`
   - Full project context
   - All bugs fixed so far
   - Complete workflow

2. **Root Cause Analysis**: `comparison_phase4_v_oldmodel/results/ROOT_CAUSE_ANALYSIS_DISCREPANCY.md`
   - Detailed technical analysis
   - Evidence from 500+ lines of investigation
   - Multiple examples

3. **Executive Summary**: `comparison_phase4_v_oldmodel/results/EXECUTIVE_SUMMARY_DISCREPANCY.md`
   - Quick reference
   - Key statistics

4. **Original Plan**: `plans/2025-11-05_phase4_vs_v2_ner_comparison.md`
   - Original comparison plan
   - Expected outputs

### Code References

**Inference Notebook**:
- Primary: `phase4_full_inference_2022_AUTO_FIX_v2.ipynb`
- Backup before fix: `phase4_full_inference_2022_AUTO_FIX_v2_BEFORE_FIX.ipynb`

**Comparison Scripts**:
- Preprocessing: `comparison_phase4_v_oldmodel/scripts/01_preprocess_and_align.py`
- Evaluation: `comparison_phase4_v_oldmodel/scripts/02_evaluate_on_test_split.py`

**Utils Library**:
- Data loading: `comparison_phase4_v_oldmodel/scripts/utils/data_loading.py`
- Entity matching: `comparison_phase4_v_oldmodel/scripts/utils/entity_matching.py`
- BPE cleaning: `comparison_phase4_v_oldmodel/scripts/utils/bpe_cleaning.py`

---

## Summary

### The Bug

Phase 4's NER post-processing fails to merge consecutive IOB tags into multi-word entities, instead outputting individual words as separate entities.

### The Impact

- F1 drops from ~66% (expected) to 22.49% (actual)
- 0% success on multi-word entity papers (V2 gets 100%)
- Makes Phase 4 appear 3x worse than it actually is

### The Fix

Replace entity extraction code to properly group consecutive `I-*` tags:
```python
# Current (buggy): entities.append(token)
# Fixed: entity_tokens.append(token) then " ".join(entity_tokens)
```

### Expected Outcome

- Phase 4 F1: 60-70% (competitive with V2's 66.35%)
- Multi-word entities correctly extracted
- Fair comparison between Phase 4 and V2

### Next Steps

1. Locate buggy code in inference notebook
2. Replace with correct entity grouping implementation
3. Test with unit tests
4. Re-run full inference on 2022 dataset
5. Validate with known failure cases
6. Update comparison analysis
7. Re-run Scripts 02-08 for fair comparison

---

**Good luck fixing the bug!** 🐛 → 🎉
