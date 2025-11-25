# Title-Based Score Modifiers for False Positive Reduction

**Created**: 2025-11-25
**Status**: Implemented in `17_deduplicate_all_sets.py`

---

## Overview

Title-based score modifiers improve precision by adjusting the linguistic score (`ling_score`) based on patterns found in paper titles. This helps distinguish legitimate bioresource introductions from pure methodology papers.

## How It Works

The effective linguistic score is calculated as:

```
effective_score = ling_score + title_modifier
```

Where `title_modifier` is:
- **+1** if title contains data resource words (boost)
- **-1** if title contains methodology patterns WITHOUT data words (penalty)
- **0** otherwise (neutral)

## Data Resource Words (+1 Boost)

Papers with these words in the title are more likely to be legitimate bioresources:

```python
DATA_RESOURCE_WORDS = [
    'database', 'archive', 'repository', 'atlas',
    'resource', 'commons', 'data management',
    'data integration', 'data platform'
]
```

**Rationale**: Analysis of 200 manually reviewed papers showed that 22.2% of legitimate bioresources have "database" in the title vs only 3.7% of false positives.

## Methodology Patterns (-1 Penalty)

Papers with these patterns in the title (WITHOUT any data resource words) are likely pure methodology papers:

```python
METHODOLOGY_PATTERNS = [
    r'\btool for\b',
    r'\bmethod for\b',
    r'\bapproach for\b',
    r'\bframework for\b',
    r'\bpipeline for\b',
    r'\bworkflow for\b',
    r'\balgorithm for\b',
    r'\bprediction of\b',
    r'\bpredicting\b',
    r'\bidentifying\b',
    r'\bdetection of\b',
]
```

**Important**: The penalty ONLY applies if the title has NO data resource words. This prevents false negatives for papers like "PepBind: a comprehensive database and computational tool for analysis..."

## Validation Results

Based on manual review of 200 papers from the aggressive profile:

| Category | Papers | Correctly Handled |
|----------|--------|-------------------|
| True False Positives (Y) | 164 | 76 would be filtered (46%) |
| Legitimate Bioresources (N) | 36 | 0 wrongly filtered (0%) |

**Key Insight**: All "database" papers are protected by the boost, and the 21 "platform" papers without data words don't trigger penalties because they lack methodology patterns.

## Impact on Filtering

The title modifier affects the linguistic bypass threshold:

```python
# In passes_profile_filter():
effective_score = ling_score + title_modifier
if effective_score >= bypass_threshold:
    # Paper bypasses keyword filter
```

For example, with `linguistic_bypass_threshold = 5`:
- Paper with ling_score=4 and "database" in title: 4+1=5 → passes
- Paper with ling_score=5 and "tool for" only: 5-1=4 → needs keyword match

## Configuration

The title modifiers are applied automatically in `17_deduplicate_all_sets.py`. No configuration changes are needed - they work with all existing profiles (conservative, balanced, aggressive).

## Related Files

- **Implementation**: `pipeline_synthesis_2025-11-18/scripts/17_deduplicate_all_sets.py`
- **Analysis data**: `false_positive_analysis/false_positives_200_for_review.csv`
- **Config file**: `unified_bioresource_pipeline/config/pipeline_config.yaml`

## Future Improvements

Potential enhancements based on user feedback:
1. Add more data resource words (e.g., "catalog", "compendium")
2. Add more methodology patterns (e.g., "classifier for", "model for")
3. Make patterns configurable per profile
