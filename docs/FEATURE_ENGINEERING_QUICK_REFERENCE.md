# Feature Engineering Quick Reference

**Phase 2: Feature Engineering Pipeline**
**Script**: `src/prepare_metadata_features.py`
**Status**: ✅ Complete and Verified

## Quick Start

### Run Feature Engineering
```bash
python src/prepare_metadata_features.py \
    --input data/metadata/pmc_metadata_enhanced_full.csv \
    --output data/metadata/features_engineered.csv \
    --mesh-components 7 \
    --keyword-components 5
```

### Verify Outputs
```bash
python verify_feature_engineering.py
```

### Load Features in Python
```python
import pandas as pd

# Fast loading (recommended)
df = pd.read_pickle('data/metadata/features_engineered.pkl')

# Or load CSV
df = pd.read_csv('data/metadata/features_engineered.csv')
```

## Feature List (18 Total)

### Tier 1: Core Features (12)

**Numerical (2)** - Z-score normalized
- `log_citations` - log(citedByCount + 1)
- `years_since_pub` - 2025 - pubYear

**Boolean (8)** - 0/1 encoding
- `hasDbCrossReferences` ⭐ (4.2% positive)
- `hasData` (48.0% positive)
- `hasSuppl` (34.7% positive)
- `isOpenAccess` (55.2% positive)
- `inPMC` (67.1% positive)
- `inEPMC` (66.9% positive)
- `hasPDF` (65.8% positive)
- `hasBook` (0.2% positive)

**Publication Type (2)**
- `is_research_article` (57.9% positive)
- `is_review_article` (5.4% positive)

### Tier 2: Enhanced Features (6)

**MeSH TF-IDF (7)** - Dimensionality reduced
- `mesh_tfidf_0` through `mesh_tfidf_6`
- Explained variance: 26.7%

**Keyword TF-IDF (5)** - Dimensionality reduced
- `keyword_tfidf_0` through `keyword_tfidf_4`
- Explained variance: 48.0%

**Missing Indicators (2)**
- `meshTerms_missing` (16.9% missing)
- `keywords_missing` (66.2% missing)

## Output Files

| File | Size | Purpose |
|------|------|---------|
| `features_engineered.csv` | 48 MB | Main output (all features) |
| `features_engineered.pkl` | 44 MB | Fast loading format |
| `features_validation.json` | 9.4 KB | Statistics and metadata |
| `feature_transformers.pkl` | 63 KB | Saved sklearn transformers |

## Command-Line Options

```
--input FILE              Input CSV with enhanced metadata
--output FILE             Output CSV for engineered features
--mesh-components N       SVD components for MeSH (default: 7)
--keyword-components N    SVD components for keywords (default: 5)
--current-year YEAR       Year for years_since_pub (default: 2025)
--min-df N                Min doc frequency for TF-IDF (default: 2)
--max-features-mesh N     Max MeSH TF-IDF features (default: 500)
--max-features-kw N       Max keyword TF-IDF features (default: 200)
```

## Data Quality

✅ **21,392 papers** processed
✅ **Zero NaN values** in engineered features
✅ **38 total columns** (20 original + 18 engineered)
✅ **Normalized features** (mean≈0, std≈1)
✅ **All transformers saved** for inference

## Using Transformers

```python
import pickle

# Load transformers
with open('data/metadata/feature_transformers.pkl', 'rb') as f:
    transformers = pickle.load(f)

# Available transformers:
# - transformers['scaler']           # StandardScaler
# - transformers['mesh_vectorizer']  # TfidfVectorizer
# - transformers['mesh_svd']         # TruncatedSVD
# - transformers['keyword_vectorizer']  # TfidfVectorizer
# - transformers['keyword_svd']      # TruncatedSVD

# Apply to new data
new_features_scaled = transformers['scaler'].transform(new_numerical_data)
```

## Feature Statistics Summary

| Feature Category | Count | Mean | Std | Notes |
|-----------------|-------|------|-----|-------|
| Numerical | 2 | 0.00 | 1.00 | Z-score normalized |
| Boolean | 8 | - | - | 0/1 encoding |
| Publication Type | 2 | - | - | One-hot encoded |
| MeSH TF-IDF | 7 | varies | varies | 26.7% variance |
| Keyword TF-IDF | 5 | varies | varies | 48.0% variance |
| Missing Indicators | 2 | - | - | Binary flags |

## Next Steps (Phase 3)

1. ✅ Features ready for ML
2. ⏭️ Train/test split
3. ⏭️ Multi-task neural network
4. ⏭️ Model training & evaluation

## Troubleshooting

**Q: Getting NaN values?**
A: Check that input CSV has all required columns. Missing indicators handle absent data.

**Q: TF-IDF shape errors?**
A: Adjust `--min-df` (try 1) or `--max-features-mesh/kw` for smaller datasets.

**Q: Memory issues?**
A: Use pickle format instead of CSV. TF-IDF peak memory ~500 MB for 21K papers.

**Q: Want different SVD dimensions?**
A: Use `--mesh-components` and `--keyword-components` options.

## Technical Details

**TF-IDF Configuration**:
- Unigrams only (ngram_range=(1,1))
- Lowercase normalization
- Min document frequency: 2
- Max features: 500 (MeSH), 200 (keywords)

**SVD Configuration**:
- Random state: 42 (reproducible)
- Components: 7 (MeSH), 5 (keywords)
- Algorithm: randomized

**Missing Value Strategy**:
- Boolean: Missing → 0
- Text: Placeholder for TF-IDF
- Numerical: None missing (computed)

## References

- Full documentation: `docs/PHASE2_FEATURE_ENGINEERING_SUMMARY.md`
- Source code: `src/prepare_metadata_features.py`
- Verification: `verify_feature_engineering.py`
- Project overview: `docs/AGENT_HANDOFF_2025-10-30.md`

---
**Last Updated**: 2025-10-30
**Python**: 3.11+
**Dependencies**: pandas, numpy, scikit-learn
