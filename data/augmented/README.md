# Augmented Training Data

This directory contains training datasets augmented with engineered metadata features for multi-task learning.

## Generated Files

### 1. `classif_train_with_metadata.csv`
**Classification training data with metadata features**
- **Rows**: 1,634 papers (100% preserved from original)
- **Columns**: 46 total
  - 11 original classification columns (id, title, abstract, labels, notes)
  - 35 metadata feature columns
- **Feature Coverage**: 100% (97% real metadata, 3% intelligently imputed)
- **No missing values**: All features complete after imputation

### 2. `ner_train_with_metadata.csv`
**NER training data with metadata features**
- **Rows**: 553 papers (100% preserved from original)
- **Columns**: 42 total
  - 7 original NER columns (id, title, abstract, entities)
  - 35 metadata feature columns
- **Feature Coverage**: 100% (98% real metadata, 2% intelligently imputed)
- **No missing values**: All features complete after imputation

### 3. `augmentation_report.json`
**Detailed validation report**
- Row count verification
- Feature coverage statistics
- Missing value analysis by column
- Data type consistency checks
- Overall validation status

### 4. `augmentation.log`
**Complete execution log**
- Detailed processing steps
- ID normalization details
- Imputation warnings
- Validation results

## Added Features (35 columns)

### Metadata Fields (17 columns)
- `publication_date` - Publication date
- `hasDbCrossReferences` - Has database cross-references (boolean)
- `hasData` - Has associated data (boolean)
- `hasSuppl` - Has supplementary materials (boolean)
- `isOpenAccess` - Open access status (boolean)
- `inPMC` - In PubMed Central (boolean)
- `inEPMC` - In Europe PMC (boolean)
- `hasPDF` - PDF available (boolean)
- `hasBook` - Is book/chapter (boolean)
- `citedByCount` - Raw citation count (integer)
- `pubYear` - Publication year (integer)
- `pubType` - Publication type (string)
- `keywords` - Author keywords (string)
- `meshTerms` - MeSH terms (string)
- `journalTitle` - Journal name (string)
- `journalISSN` - Journal ISSN (string)
- `authorAffiliations` - Author affiliations (string)

### Engineered Features (18 columns)
- `log_citations` - Log-transformed citation count (scaled)
- `years_since_pub` - Years since publication (scaled)
- `is_research_article` - Research article flag (boolean)
- `is_review_article` - Review article flag (boolean)
- `meshTerms_missing` - MeSH terms missing indicator (boolean)
- `mesh_tfidf_0` through `mesh_tfidf_6` - MeSH TF-IDF components (7 dims)
- `keywords_missing` - Keywords missing indicator (boolean)
- `keyword_tfidf_0` through `keyword_tfidf_4` - Keyword TF-IDF components (5 dims)

## Feature Imputation Strategy

For papers without metadata (~2-3% of training data), values were intelligently imputed:

### Numerical Features
- **Method**: Median from feature dataset
- **Examples**: `log_citations`, `years_since_pub`

### Boolean Features
- **Method**: Mode (most common value) from feature dataset
- **Examples**: `hasData`, `isOpenAccess`, `is_research_article`

### TF-IDF Features
- **Method**: Zero vector (0.0)
- **Rationale**: Neutral position in reduced semantic space
- **Examples**: All `mesh_tfidf_*` and `keyword_tfidf_*` columns

### Text Features
- **Method**: Empty string ('')
- **Examples**: `keywords`, `meshTerms`, `authorAffiliations`

## Usage in Training

### Loading Augmented Data

```python
import pandas as pd

# Load augmented training data
classif_train = pd.read_csv('data/augmented/classif_train_with_metadata.csv')
ner_train = pd.read_csv('data/augmented/ner_train_with_metadata.csv')

# Separate original and feature columns
original_classif_cols = ['id', 'title', 'abstract', 'checked_by',
                          'kes_check', 'hji_check', 'curation_sum',
                          'number_of_checks', 'curation_score',
                          'kes_notes', 'hji_notes']

feature_cols = [col for col in classif_train.columns
                if col not in original_classif_cols]

print(f"Feature columns: {len(feature_cols)}")
print(f"First 10 features: {feature_cols[:10]}")
```

### Multi-Task Learning Integration

```python
# Example: Combine text and metadata for classification
X_text = classif_train['abstract']
X_metadata = classif_train[feature_cols]
y = classif_train['curation_score']

# Option 1: Concatenate at embedding level
# text_embeddings = bert_model.encode(X_text)
# combined_features = np.hstack([text_embeddings, X_metadata])

# Option 2: Separate towers with fusion
# text_tower = BERTEncoder(X_text)
# metadata_tower = MLPEncoder(X_metadata)
# fused = Concatenate([text_tower, metadata_tower])
```

## Regeneration

To regenerate augmented datasets:

```bash
# Standard regeneration
python3 src/augment_training_data.py

# With custom paths
python3 src/augment_training_data.py \
    --classif-data data/manual_classifications.csv \
    --ner-data data/manual_ner_extraction.csv \
    --features data/metadata/features_engineered.csv \
    --output-dir data/augmented/

# Validation only (dry run)
python3 src/augment_training_data.py --validate-only

# Verbose logging
python3 src/augment_training_data.py --verbose
```

## Validation Criteria

All augmented datasets pass these validation checks:
- ✅ Row count preserved (no samples lost)
- ✅ No missing values in feature columns
- ✅ ≥34 feature columns added
- ✅ ≥80% feature coverage (actual: 97-98%)
- ✅ Data type consistency maintained
- ✅ ID matching successful

## Notes

### ID Normalization
The augmentation script handles mixed ID formats:
- **Numeric IDs**: PubMed IDs (e.g., 28791657) - normalized to string integers
- **Non-numeric IDs**: PMC and IND identifiers (e.g., PMC8090191, IND607223097) - preserved as-is

### Coverage Statistics
- **Classification**: 1,586/1,634 (97%) papers have real metadata
- **NER**: 542/553 (98%) papers have real metadata
- Remaining papers use intelligent imputation

### Feature Distribution
All features are ready for model training:
- Numerical features are scaled (mean=0, std=1)
- Boolean features are 0/1 encoded
- TF-IDF features are normalized vectors
- No preprocessing required beyond standard train/test splitting

## Related Files

- **Source Script**: `/Users/warren/development/GBC/inventory_2022/src/augment_training_data.py`
- **Feature Engineering**: `/Users/warren/development/GBC/inventory_2022/src/prepare_metadata_features.py`
- **Original Training Data**: `/Users/warren/development/GBC/inventory_2022/data/manual_*.csv`
- **Engineered Features**: `/Users/warren/development/GBC/inventory_2022/data/metadata/features_engineered.csv`

---
*Generated: 2025-10-31*
*Pipeline Phase: 3 - Dataset Augmentation*
