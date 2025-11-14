# Colab vs Local NER: Entity Extraction Examples
**Date:** 2025-11-14
**Purpose:** Show concrete examples of Colab model failures

---

## Overview

This document shows specific examples where the Colab model (wrong file) fails compared to the Local model (correct file).

---

## Example 1: Truncated Entity Boundaries

**Paper ID:** 22
**Resource:** AIDS and Cancer Specimen Resource (ACSR)

### Local (Correct Model) - 7 entities detected
```
1. "AIDS and Cancer Specimen Resource"  [FUL]  conf=0.987 ✅
2. "AIDS and Cancer Specimen Resource"  [FUL]  conf=0.989 ✅
3. "ACSR"                               [COM]  conf=0.992 ✅
4. "ACSR"                               [COM]  conf=0.716 ✅
5. "ACSR"                               [COM]  conf=0.803 ✅
6. "ACSR"                               [COM]  conf=0.659 ✅
7. "ACSR"                               [COM]  conf=0.990 ✅
```

### Colab (Wrong Model) - 3 entities detected
```
1. "and Cancer Specimen Resource"       [FUL]  conf=0.580 ❌ TRUNCATED! Missing "AIDS"
2. "and Cancer Specimen Resource"       [FUL]  conf=0.703 ❌ TRUNCATED! Missing "AIDS"
3. "ACSR"                               [COM]  conf=0.672 ⚠️  Missed 4 other mentions
```

**Problem:**
- Colab model truncates entity start ("and Cancer..." instead of "AIDS and Cancer...")
- Colab model misses 4 out of 5 ACSR mentions
- Lower confidence scores (0.58-0.70 vs 0.66-0.99)

**Impact:** Missing full resource name, incomplete mention detection

---

## Example 2: Wrong Entity Boundaries

**Paper ID:** 26
**Resource:** AD&FTD Mutation Database

### Local (Correct Model) - 3 entities detected
```
1. "AD&FTD"                             [COM]  conf=0.614 ✅
2. "AD&FTD"                             [COM]  conf=0.996 ✅
3. "AD&FTD"                             [COM]  conf=0.981 ✅
```

### Colab (Wrong Model) - 1 entity detected
```
1. "AD&FTD Mutation"                    [COM]  conf=0.510 ❌ WRONG BOUNDARY!
```

**Problem:**
- Colab model includes "Mutation" in entity (should be just "AD&FTD")
- Colab model misses 2 out of 3 mentions
- Much lower confidence (0.51 vs 0.61-1.00)

**Impact:** Wrong entity boundaries, missed mentions, low confidence

---

## Example 3: Missed Duplicate Mentions

**Paper ID:** 127
**Resource:** ASL-LEX

### Local (Correct Model) - 3 entities detected
```
1. "ASL-LEX"                            [COM]  conf=0.997 ✅
2. "ASL-LEX"                            [COM]  conf=0.999 ✅
3. "ASL-LEX"                            [COM]  conf=0.999 ✅
```

### Colab (Wrong Model) - 2 entities detected
```
1. "ASL-LEX"                            [COM]  conf=0.867 ⚠️
2. "ASL-LEX"                            [COM]  conf=0.566 ⚠️  Missed 1 mention
```

**Problem:**
- Colab model misses 1 out of 3 mentions
- Lower confidence scores (0.57-0.87 vs 0.997-0.999)

**Impact:** Incomplete mention detection, lower confidence

---

## Example 4: Complete Miss (Zero Entities Detected)

**Paper ID:** 395
**Resource:** CHPC2012

### Local (Correct Model) - 6 entities detected
```
1. "CHPC2012"                           [COM]  conf=0.979 ✅
2. "CHPC2012"                           [COM]  conf=0.946 ✅
3. "CHPC2012"                           [COM]  conf=0.890 ✅
4. "CHPC2012"                           [COM]  conf=0.??? ✅
5. "CHPC2012"                           [COM]  conf=0.??? ✅
6. "CHPC2012"                           [COM]  conf=0.??? ✅
```

### Colab (Wrong Model) - 0 entities detected
```
(NONE)  ❌ COMPLETE MISS!
```

**Problem:**
- Colab model finds ZERO entities in this paper
- Local model finds 6 mentions of CHPC2012

**Impact:** Entire paper missed, zero recall

---

## Example 5: Complete Miss - DIVAS

**Paper ID:** 675
**Resource:** DIVAS

### Local (Correct Model) - 1 entity detected
```
1. "DIVAS"                              [COM]  conf=0.905 ✅
```

### Colab (Wrong Model) - 0 entities detected
```
(NONE)  ❌ COMPLETE MISS!
```

**Problem:**
- Colab model misses single mention of DIVAS
- Paper has zero entities detected

**Impact:** Paper completely missed

---

## Example 6: Complete Miss - e23D

**Paper ID:** 698
**Resource:** e23D

### Local (Correct Model) - 3 entities detected
```
1. "e23D"                               [COM]  conf=0.995 ✅
2. "23D"                                [COM]  conf=0.920 ✅
3. "e23D"                               [COM]  conf=0.998 ✅
```

### Colab (Wrong Model) - 0 entities detected
```
(NONE)  ❌ COMPLETE MISS!
```

**Problem:**
- Colab model finds ZERO entities
- Local model finds 3 mentions (both "e23D" and "23D" variants)

**Impact:** Entire paper and resource missed

---

## Summary Statistics

### Paper-Level Coverage
- **Papers with entities (Colab):** 130
- **Papers with entities (Local):** 147
- **Papers completely missed by Colab:** 17 (11.6%)

### Entity-Level Performance
- **Total entities (Colab):** 341
- **Total entities (Local):** 694
- **Missing entities:** 353 (50.8%)

### Confidence Distribution
| Metric | Colab | Local | Difference |
|--------|-------|-------|------------|
| Mean confidence | 0.6902 | 0.9415 | -0.2513 |
| % High confidence (≥0.9) | 7.6% | 80.4% | -72.8% |
| Median confidence | 0.6668 | 0.9912 | -0.3244 |

---

## Error Patterns Identified

### 1. Truncated Entity Starts
**Example:** "and Cancer..." instead of "AIDS and Cancer..."
- Colab model frequently misses first word(s) of entities
- Happens with multi-word resource names

### 2. Wrong Entity Boundaries
**Example:** "AD&FTD Mutation" instead of "AD&FTD"
- Colab model includes extra words in entity span
- Results in incorrect entity extraction

### 3. Missed Duplicate Mentions
**Example:** Finding 2 out of 3 "ASL-LEX" mentions
- Colab model inconsistently detects repeated mentions
- Lower recall on duplicate entities in same paper

### 4. Complete Paper Misses
**Example:** 17 papers with ZERO entities detected
- Colab model fails completely on some papers
- Local model successfully extracts entities from all these papers

### 5. Low Confidence Scores
**Overall pattern:** Mean 0.69 vs 0.94
- Consistent with undertrained model
- Only 7.6% predictions have high confidence (≥0.9)

---

## Conclusion

The Colab model exhibits systematic failures across multiple error types:

1. **Entity boundary errors** (truncation, extension)
2. **Recall failures** (missing mentions, missing papers)
3. **Low confidence** (undertrained or wrong architecture)

All errors are **consistent across 4 independent runs** (MD5 hash identical), proving this is a **model file issue**, not a random variation.

**Solution:** Upload correct 473 MB model file to Google Drive.
