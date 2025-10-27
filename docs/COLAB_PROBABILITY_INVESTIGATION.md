# Colab Probability Calculation Investigation

**Date**: 2025-10-24
**Issue**: Colab reruns producing dramatically lower probability scores compared to local bash script runs
**Impact**: Only 0.8% of Colab predictions pass 0.978 quality threshold vs 84.7% for local runs

---

## Problem Statement

### Observed Behavior

Both Colab rerun environments (new model `s4985d` and old model `y5hsk6`) exhibit identical issues:
- **Total predictions**: 3,569
- **Passing threshold (≥0.978)**: Only 29 (0.8%)
- **Failed threshold**: 3,540 (99.2%)

This is dramatically different from the local bash script execution:
- **Total predictions**: 4,368
- **Passing threshold (≥0.978)**: 3,698 (84.7%)
- **Failed threshold**: 670 (15.3%)

### Critical Finding

When Colab predictions ARE high-confidence (≥0.978), they match local predictions with **96.55% agreement**. This suggests:
- ✅ Model accuracy is CORRECT
- ✅ Prediction logic is CORRECT
- ⚠️ **Probability calculation/extraction is BROKEN**

---

## Environment Differences

### Colab Environment
- **Python**: 3.12.12
- **PyTorch**: 2.8.0+cu126
- **Transformers**: 4.57.1
- **CUDA**: 12.6
- **Execution**: Google Colab notebook (rerun_2022_inventory_with_checkpoints.ipynb)

### Local Environment (biodata_modern_env)
- **Python**: 3.11.9
- **PyTorch**: 2.2.2
- **Transformers**: 4.35.0
- **Execution**: Bash script (rerun_2022_inventory.sh)

### Version Gaps
- PyTorch: **2.2.2 → 2.8.0** (3 major versions, 6 months of changes)
- Transformers: **4.35.0 → 4.57.1** (22 minor versions, ~6 months)
- Python: **3.11.9 → 3.12.12** (1 major version)

---

## Code Investigation Findings

### 1. Execution Path (IDENTICAL)

Both environments use the same Python scripts:
```bash
# Classification
python src/class_predict.py -i <input> -o <output> -c <model>

# NER
python src/ner_predict.py -i <input> -o <output> -c <model>
```

### 2. Model Loading (IDENTICAL)

File: `src/inventory_utils/filing.py`

```python
# Lines 39 & 70
checkpoint = torch.load(checkpoint_fh, map_location=device, weights_only=False)
model_name = checkpoint['model_name']
model = classifier.from_pretrained(model_name, num_labels=2)

# Remove incompatible keys for newer transformers versions
state_dict = checkpoint['model_state_dict']
if 'roberta.embeddings.position_ids' in state_dict:
    del state_dict['roberta.embeddings.position_ids']  # Known compatibility fix

model.load_state_dict(state_dict)
model.to(device)
model.eval()
```

**Note**: The `weights_only=False` parameter was recently added for PyTorch 2.6+ compatibility. This parameter affects **security during loading**, not model behavior after loading.

### 3. Probability Extraction (CRITICAL CODE)

File: `src/ner_predict.py` (lines 257-261)

```python
logits = outputs.logits
preds = logits.argmax(dim=-1).cpu().numpy()[0][1:-1]

# THIS IS WHERE PROBABILITIES ARE CALCULATED
all_probs = torch.nn.functional.softmax(logits, dim=-1).cpu().numpy()[0][1:-1]
probs = [prob[pred] for pred, prob in zip(preds, all_probs)]
```

**This is the most likely source of the problem!**

The `torch.nn.functional.softmax()` function behavior could differ between PyTorch 2.2.2 and 2.8.0, especially regarding:
- Default dtype handling (float32 vs float16)
- Numerical precision
- CUDA kernel implementations
- Gradient mode interaction

---

## Research Findings from Web Search

### PyTorch Softmax Dtype Issues (CONFIRMED)

Multiple GitHub issues document that softmax behavior differs based on dtype:
- `torch.softmax(inp, dtype=torch.float32).to(torch.float16)` ≠ `torch.softmax(inp)` for fp16 inputs
- Softmax typically requires fp32 for numerical stability
- Mixed precision training can cause unexpected dtype conversions
- PyTorch 2.8 may have different default dtype behavior than 2.2.2

### Transformers position_ids Issue (ALREADY HANDLED)

The error "Unexpected key(s) in state_dict: embeddings.position_ids" is a known compatibility issue when loading RoBERTa models across different versions.

**Our code already handles this** by deleting the position_ids from state_dict before loading (lines 46, 79 in filing.py).

### No Documented Breaking Changes

Research did NOT find explicit documentation of:
- Softmax calculation changes in PyTorch 2.8 release notes
- AutoModelForSequenceClassification output changes in Transformers 4.57
- Explicit breaking changes to probability extraction

**This suggests the issue is subtle and related to implicit behavior changes.**

---

## Potential Root Causes (Ranked by Likelihood)

### 1. ⚠️ **Softmax Dtype/Precision Issue** (HIGHEST LIKELIHOOD)

**Theory**: PyTorch 2.8 or Transformers 4.57 may be using different default dtype for logits or softmax calculations.

**Evidence**:
- PyTorch has documented float16/float32 differences in softmax behavior
- Newer PyTorch versions prioritize mixed precision training
- Colab may default to different CUDA kernel implementations

**Test**:
```python
# Add explicit dtype checking/conversion
print(f"Logits dtype: {logits.dtype}")
all_probs = torch.nn.functional.softmax(logits.float(), dim=-1).cpu().numpy()[0][1:-1]
```

---

### 2. ⚠️ **Model eval() Mode Issue** (MEDIUM LIKELIHOOD)

**Theory**: PyTorch 2.8 or Transformers 4.57 may have changed how `model.eval()` affects dropout or batch normalization layers.

**Evidence**:
- Transformers models use dropout layers in attention mechanisms
- PyTorch forums document cases where eval() behavior changed between versions
- eval() is critical for deterministic inference

**Test**:
```python
# Verify eval mode is actually active
print(f"Model training mode: {model.training}")
# Should print: False

# Check dropout layers
for name, module in model.named_modules():
    if isinstance(module, torch.nn.Dropout):
        print(f"{name}: training={module.training}, p={module.p}")
```

---

### 3. ⚠️ **Tokenization Differences** (MEDIUM LIKELIHOOD)

**Theory**: Transformers 4.57 may handle tokenization differently than 4.35, affecting input to the model.

**Evidence**:
- Transformers library frequently updates tokenization logic
- Different token IDs could affect model outputs
- Padding/truncation behavior may have changed

**Test**:
```python
# Compare tokenization outputs
from transformers import AutoTokenizer

tokenizer_local = AutoTokenizer.from_pretrained("allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500")
test_text = "Sample abstract text here"

tokens_local = tokenizer_local(test_text, return_tensors="pt")
print(f"Token IDs: {tokens_local['input_ids']}")
print(f"Attention mask: {tokens_local['attention_mask']}")
```

---

### 4. ⚠️ **CUDA Kernel/Computation Differences** (LOW-MEDIUM LIKELIHOOD)

**Theory**: PyTorch 2.8 with CUDA 12.6 may use different numerical computation kernels than PyTorch 2.2.2.

**Evidence**:
- PyTorch 2.8 specifically mentions improved Intel CPU performance (not GPU)
- CUDA 12.6 is newer than what PyTorch 2.2.2 was tested with
- Numerical precision can vary between CUDA versions

**Test**:
```python
# Check CUDA version and capabilities
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"Device: {next(model.parameters()).device}")
print(f"Device dtype: {next(model.parameters()).dtype}")
```

---

### 5. ✅ **weights_only=False Parameter** (UNLIKELY - RULED OUT)

**Theory**: The `weights_only=False` parameter affects model behavior after loading.

**Evidence**:
- This parameter only affects security during unpickling
- Model state is loaded identically regardless of this parameter
- Same models produce different results, so loading is not the issue

**Conclusion**: **NOT THE CAUSE**

---

## Systematic Investigation Plan

### Phase 1: Diagnostic Logging (Immediate)

Add detailed logging to `src/ner_predict.py` before line 259:

```python
def predict_sequence(model, device: torch.device, seq: str,
                     tokenizer: PreTrainedTokenizer) -> List[NamedEntity]:
    # ... existing code ...

    with torch.no_grad():
        tokenized_seq = tokenizer(seq,
                                  return_tensors='pt',
                                  padding=True,
                                  truncation=True,
                                  max_length=512).to(device)

        # DIAGNOSTIC LOGGING
        print(f"\n=== DIAGNOSTIC INFO ===")
        print(f"Model training mode: {model.training}")
        print(f"Input device: {tokenized_seq['input_ids'].device}")
        print(f"Input dtype: {tokenized_seq['input_ids'].dtype}")

        outputs = cast(TokenClassifierOutput, model(**tokenized_seq))
        logits = outputs.logits

        print(f"Logits shape: {logits.shape}")
        print(f"Logits dtype: {logits.dtype}")
        print(f"Logits device: {logits.device}")
        print(f"Logits range: [{logits.min():.4f}, {logits.max():.4f}]")

        preds = logits.argmax(dim=-1).cpu().numpy()[0][1:-1]

        # CRITICAL: Test explicit dtype conversion
        all_probs_default = torch.nn.functional.softmax(logits, dim=-1).cpu().numpy()[0][1:-1]
        all_probs_float32 = torch.nn.functional.softmax(logits.float(), dim=-1).cpu().numpy()[0][1:-1]

        print(f"Softmax default dtype result sample: {all_probs_default[:3]}")
        print(f"Softmax float32 result sample: {all_probs_float32[:3]}")
        print(f"Difference: {abs(all_probs_default - all_probs_float32).max()}")
        print(f"======================\n")

        probs = [prob[pred] for pred, prob in zip(preds, all_probs_default)]
```

**Run this on BOTH Colab and local and compare outputs.**

---

### Phase 2: Version-Specific Tests

#### Test 1: Isolate PyTorch Version

Create minimal test script that doesn't depend on full pipeline:

```python
import torch
import torch.nn.functional as F

# Test softmax behavior
logits = torch.randn(1, 10, 5)  # Batch, seq_len, num_labels
print(f"PyTorch version: {torch.__version__}")
print(f"Logits dtype: {logits.dtype}")

probs_default = F.softmax(logits, dim=-1)
probs_float32 = F.softmax(logits.float(), dim=-1)

print(f"Default softmax dtype: {probs_default.dtype}")
print(f"Float32 softmax dtype: {probs_float32.dtype}")
print(f"Max difference: {(probs_default - probs_float32).abs().max()}")
```

**Run on both environments and compare.**

#### Test 2: Isolate Transformers Version

```python
from transformers import AutoModelForTokenClassification, AutoTokenizer
import torch

model_name = "allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(
    model_name,
    num_labels=3  # O, B-DB, I-DB
)
model.eval()

test_text = "The PRIDE database provides proteomics data."
inputs = tokenizer(test_text, return_tensors="pt")

print(f"Transformers version: {transformers.__version__}")

with torch.no_grad():
    outputs = model(**inputs)
    logits = outputs.logits

    print(f"Logits dtype: {logits.dtype}")
    print(f"Logits shape: {logits.shape}")

    probs = torch.nn.functional.softmax(logits, dim=-1)
    print(f"Probs dtype: {probs.dtype}")
    print(f"Sample probs: {probs[0, 1:4]}")  # First few tokens
```

**Run on both environments and compare.**

---

### Phase 3: Controlled Environment Testing

#### Option A: Downgrade Colab Libraries

In Colab notebook, before model loading:

```python
!pip install torch==2.2.2
!pip install transformers==4.35.0
```

Then rerun prediction. If this fixes the issue, we've confirmed it's library version-specific.

#### Option B: Upgrade Local Libraries

In local environment:

```bash
pip install torch==2.8.0
pip install transformers==4.57.1
```

Then rerun local script. If this BREAKS the local script, we've confirmed the issue.

---

### Phase 4: Probability Extraction Alternatives

If softmax dtype is the issue, test explicit conversions:

```python
# Current (possibly problematic)
all_probs = torch.nn.functional.softmax(logits, dim=-1).cpu().numpy()[0][1:-1]

# Alternative 1: Force float32
all_probs = torch.nn.functional.softmax(logits.float(), dim=-1).cpu().numpy()[0][1:-1]

# Alternative 2: Explicit dtype parameter (if supported)
all_probs = torch.nn.functional.softmax(logits, dim=-1, dtype=torch.float32).cpu().numpy()[0][1:-1]

# Alternative 3: Log softmax (sometimes more numerically stable)
log_probs = torch.nn.functional.log_softmax(logits, dim=-1)
all_probs = torch.exp(log_probs).cpu().numpy()[0][1:-1]
```

---

### Phase 5: Model State Verification

Verify that models are loading identically:

```python
# In src/inventory_utils/filing.py, after line 48 (after load_state_dict)

# Check model parameters
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

print(f"Total parameters: {total_params:,}")
print(f"Trainable parameters: {trainable_params:,}")
print(f"Model dtype: {next(model.parameters()).dtype}")
print(f"Model device: {next(model.parameters()).device}")

# Check a few parameter values to ensure loading worked
for name, param in model.named_parameters():
    if 'embeddings.word_embeddings.weight' in name:
        print(f"Word embeddings sample: {param[0, :5]}")
        break
```

---

## Recommended Investigation Order

1. **IMMEDIATE**: Add diagnostic logging (Phase 1) and run comparison
2. **QUICK TEST**: Run isolated softmax test (Phase 2, Test 1) on both environments
3. **IF SOFTMAX DIFFERS**: Try float32 conversion fix (Phase 4, Alternative 1)
4. **IF STILL BROKEN**: Try library downgrade in Colab (Phase 3, Option A)
5. **IF NEEDED**: Full model state verification (Phase 5)

---

## Expected Outcomes

### If Softmax Dtype is the Issue:
- Diagnostic logs will show different dtype in logits or probs
- Explicit float32 conversion will fix the problem
- **Solution**: Update `ner_predict.py` line 259 to force float32

### If Transformers Version is the Issue:
- Downgrading Transformers in Colab will fix the problem
- **Solution**: Pin Transformers to 4.35.0 or update local to 4.57.1 after verification

### If PyTorch Version is the Issue:
- Isolated softmax test will show different behavior
- Downgrading PyTorch in Colab will fix the problem
- **Solution**: Pin PyTorch to 2.2.2 or update local after verification

### If Model Loading is the Issue:
- Model state verification will show parameter differences
- **Solution**: Investigate state_dict compatibility further

---

## Success Criteria

A fix is successful when:
1. ✅ Colab rerun passes >80% of predictions at 0.978 threshold (matching local)
2. ✅ Colab rerun maintains 96%+ agreement with local on high-confidence predictions
3. ✅ Resource-level overlap with final inventory reaches >80%
4. ✅ Changes don't break local environment performance

---

## Additional Resources

- PyTorch 2.8 Release Notes: https://pytorch.org/blog/pytorch-2-8/
- Transformers Changelog: https://github.com/huggingface/transformers/releases
- Softmax Dtype Issue: https://github.com/pytorch/pytorch/issues/123911
- Position IDs Issue: https://github.com/huggingface/transformers/issues/25330

---

**Next Action**: Run Phase 1 diagnostic logging on both environments and compare outputs.
