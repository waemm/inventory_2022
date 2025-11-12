#!/usr/bin/env python3
"""
Phase 3: PyCaret Prediction for Comparison

Runs PyCaret models on clean test set for comparison with V2 model.
Uses EXACT features expected by trained models.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("PHASE 3: PYCARET PREDICTION")
print("=" * 60)

# ============================================
# CONFIGURATION
# ============================================

BASE_DIR = Path(__file__).parent.parent.parent  # Go up to inventory_2022/
COMPARISON_DIR = BASE_DIR / "comparison_pycaret_v2"

# Input data
TEST_SET = COMPARISON_DIR / "data/test_set_full.csv"
V5_METADATA = BASE_DIR / "data/final_query_v5.1_2011_2021/query_results.csv"

# Model paths
MODEL_TEST_TRUE = Path("/tmp/pycaret_test/pycaret_metadata_classifier_v1")
MODEL_TEST_FALSE = Path("/tmp/pycaret_test_false/pycaret_metadata_classifier_v1")

# Output paths
OUTPUT_DIR = COMPARISON_DIR / "pycaret_predictions"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SESSION_ID = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

print(f"Session ID: {SESSION_ID}")
print(f"Test Set: {TEST_SET}")
print(f"Output: {OUTPUT_DIR}")
print("=" * 60)

# ============================================
# LOAD DATA
# ============================================

print("\n📚 Loading data...")

# Load test set with ground truth
df_test = pd.read_csv(TEST_SET)
print(f"✓ Test set: {len(df_test):,} papers")
print(f"  - Positives: {(df_test['ground_truth']==1).sum():,}")
print(f"  - Negatives: {(df_test['ground_truth']==0).sum():,}")

# Load V5.1 metadata for feature engineering
df_metadata = pd.read_csv(V5_METADATA, low_memory=False)
print(f"✓ V5.1 metadata: {len(df_metadata):,} papers")

# Convert IDs to PMID
df_test['pmid'] = df_test['id'].astype(float)
df_metadata['pmid'] = df_metadata['id'].astype(float)

# Merge test set with metadata
df = df_test.merge(
    df_metadata,
    on='pmid',
    how='left',
    suffixes=('_test', '_meta')
)

print(f"✓ Merged: {len(df):,} papers")

# Check for missing metadata
missing_metadata = df['title_meta'].isna().sum()
if missing_metadata > 0:
    print(f"⚠️  Warning: {missing_metadata} papers missing metadata")

# ============================================
# FEATURE ENGINEERING FUNCTION
# ============================================

def engineer_features_for_model(df, model):
    """
    Engineer features to match EXACTLY what the model expects.
    Uses model.feature_names_in_ to get the expected features.
    """
    expected_features = list(model.feature_names_in_)
    print(f"\n🔧 Engineering {len(expected_features)} features to match model expectations...")

    df = df.copy()

    # Helper function to convert binary strings to int
    def convert_to_binary(val):
        if pd.isna(val) or val == '' or val == 'N' or val == False or val == 'false':
            return 0
        elif val == 'Y' or val == True or val == 'true':
            return 1
        else:
            try:
                return int(val)
            except:
                return 0

    # ============================================
    # 1. Parse List Columns
    # ============================================
    mesh_col = 'meshTerms' if 'meshTerms' in df.columns else 'meshTerms_meta'
    df['meshTerms_list'] = df[mesh_col].fillna('[]').apply(
        lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else []
    )

    pubtype_col = 'pubType' if 'pubType' in df.columns else 'pubType_meta'
    df['pubType_list'] = df[pubtype_col].fillna('[]').apply(
        lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else []
    )

    keywords_col = 'keywords' if 'keywords' in df.columns else 'keywords_meta'
    df['keywords_list'] = df[keywords_col].fillna('[]').apply(
        lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else []
    )

    journal_col = 'journalTitle' if 'journalTitle' in df.columns else 'journalTitle_meta'

    # ============================================
    # 2. Create Base Features
    # ============================================
    cite_col = 'citedByCount' if 'citedByCount' in df.columns else 'citedByCount_meta'
    year_col = 'pubYear' if 'pubYear' in df.columns else 'pubYear_meta'

    df['citedByCount'] = df[cite_col].fillna(0).astype(int)
    df['pubYear'] = df[year_col].fillna(2020).astype(int)

    # Binary access features
    binary_features_map = {
        'inEPMC': 'inEPMC' if 'inEPMC' in df.columns else 'inEPMC_meta',
        'inPMC': 'inPMC' if 'inPMC' in df.columns else 'inPMC_meta',
        'hasDbCrossReferences': 'hasDbCrossReferences' if 'hasDbCrossReferences' in df.columns else 'hasDbCrossReferences_meta',
        'hasData': 'hasData' if 'hasData' in df.columns else 'hasData_meta',
        'hasSuppl': 'hasSuppl' if 'hasSuppl' in df.columns else 'hasSuppl_meta',
        'isOpenAccess': 'isOpenAccess' if 'isOpenAccess' in df.columns else 'isOpenAccess_meta',
    }

    for feat_name, col in binary_features_map.items():
        if col in df.columns:
            df[feat_name] = df[col].apply(convert_to_binary)
        else:
            df[feat_name] = 0

    # Computed features
    df['log_citations'] = np.log1p(df['citedByCount'])
    df['years_since_pub'] = 2025 - df['pubYear']
    df['citation_age_ratio'] = df['citedByCount'] / (df['years_since_pub'] + 1)
    df['is_highly_cited'] = (df['citedByCount'] > df['citedByCount'].quantile(0.75)).astype(int)
    df['is_uncited'] = (df['citedByCount'] == 0).astype(int)
    df['access_score'] = df[['hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess']].sum(axis=1)
    df['is_recent'] = (df['pubYear'] >= 2018).astype(int)
    df['is_old'] = (df['pubYear'] < 2010).astype(int)

    # MeSH features
    df['mesh_term_count'] = df['meshTerms_list'].apply(len)

    # Pubtype features
    df['pubtype_count'] = df['pubType_list'].apply(len)
    df['is_review'] = df['pubType_list'].apply(lambda x: 1 if 'Review' in x else 0)
    df['is_letter'] = df['pubType_list'].apply(lambda x: 1 if 'Letter' in x else 0)

    # Text features
    title_col = 'title_test' if 'title_test' in df.columns else 'title'
    abstract_col = 'abstract_test' if 'abstract_test' in df.columns else 'abstract'

    df['title_length'] = df[title_col].fillna('').apply(len)
    df['abstract_length'] = df[abstract_col].fillna('').apply(len)
    df['has_abstract'] = (df['abstract_length'] > 0).astype(int)

    # Keyword features
    df['keyword_count'] = df['keywords_list'].apply(len)
    database_keywords = ['database', 'repository', 'resource', 'portal', 'knowledgebase',
                         'archive', 'registry', 'catalog', 'collection']
    df['has_database_keyword'] = df['keywords_list'].apply(
        lambda x: 1 if any(kw.lower() in [k.lower() for k in x] for kw in database_keywords) else 0
    )

    # ============================================
    # 3. Create Specific MeSH Features
    # ============================================
    for feat in expected_features:
        if feat.startswith('mesh_') and feat != 'mesh_term_count':
            # Extract the MeSH term name from feature name
            mesh_name = feat[5:]  # Remove 'mesh_' prefix
            # Restore original formatting (commas, spaces)
            mesh_name = mesh_name.replace('_', ' ').replace(',', ', ')

            # Check if this MeSH term appears in the paper
            df[feat] = df['meshTerms_list'].apply(
                lambda x: 1 if any(mesh_name.lower() in term.lower() for term in x) else 0
            )

    # ============================================
    # 4. Create Specific Pubtype Features
    # ============================================
    pubtype_mapping = {
        'pubtype_Journal_Article': 'Journal Article',
        'pubtype_Review': 'Review',
        'pubtype_Research_Support_NIH_Extramura': 'Research Support, N.I.H., Extramural',
        'pubtype_Research_Support_Non-US_Govt': "Research Support, Non-U.S. Gov't",
        'pubtype_Research_Support_US_Govt_PHS': 'Research Support, U.S. Gov\'t, P.H.S.',
        'pubtype_Comparative_Study': 'Comparative Study',
        'pubtype_Letter': 'Letter',
        'pubtype_Comment': 'Comment',
        'pubtype_Editorial': 'Editorial',
        'pubtype_Case_Reports': 'Case Reports',
    }

    for feat, pubtype in pubtype_mapping.items():
        if feat in expected_features:
            df[feat] = df['pubType_list'].apply(lambda x: 1 if pubtype in x else 0)

    # ============================================
    # 5. Create Specific Journal Features
    # ============================================
    for feat in expected_features:
        if feat.startswith('journal_'):
            # Extract journal name from feature (truncated to 30 chars in training)
            journal_pattern = feat[8:]  # Remove 'journal_' prefix

            # Match against actual journal title (partial match due to truncation)
            df[feat] = df[journal_col].fillna('').apply(
                lambda x: 1 if journal_pattern.lower().replace('_', ' ') in x.lower() else 0
            )

    # ============================================
    # 6. Add label column (required by PyCaret)
    # ============================================
    df['label'] = 0.5  # Neutral value for prediction

    # ============================================
    # 7. Select ONLY Expected Features
    # ============================================
    # Ensure all expected features exist
    for feat in expected_features:
        if feat not in df.columns:
            df[feat] = 0  # Default value for missing features

    # Select features in the EXACT order expected by model
    X = df[expected_features].copy()
    X = X.fillna(0)

    print(f"✓ Created {len(expected_features)} features matching model expectations")

    return X

# ============================================
# LOAD PYCARET MODELS
# ============================================

from pycaret.classification import load_model, predict_model

print("\n🤖 Loading PyCaret models...")

# Check which models exist
models_to_run = []

if MODEL_TEST_TRUE.with_suffix('.pkl').exists():
    model_test_true = load_model(str(MODEL_TEST_TRUE))
    models_to_run.append(('TEST_MODE_True', model_test_true))
    print(f"✓ Loaded TEST_MODE=True model ({len(model_test_true.feature_names_in_)} features)")
else:
    print(f"⚠️  TEST_MODE=True model not found: {MODEL_TEST_TRUE}")

if MODEL_TEST_FALSE.with_suffix('.pkl').exists():
    model_test_false = load_model(str(MODEL_TEST_FALSE))
    models_to_run.append(('TEST_MODE_False', model_test_false))
    print(f"✓ Loaded TEST_MODE=False model ({len(model_test_false.feature_names_in_)} features)")
else:
    print(f"⚠️  TEST_MODE=False model not found: {MODEL_TEST_FALSE}")

if len(models_to_run) == 0:
    raise FileNotFoundError(
        "No PyCaret models found!\n"
        f"Expected locations:\n"
        f"  - {MODEL_TEST_TRUE}.pkl\n"
        f"  - {MODEL_TEST_FALSE}.pkl\n\n"
        f"Please train models first using pycaret_metadata_training.ipynb"
    )

print(f"\n✓ {len(models_to_run)} model(s) loaded and ready")

# ============================================
# RUN PREDICTIONS
# ============================================

print("\n🔮 Running predictions...\n")

results = {}

for model_name, model in models_to_run:
    print(f"=" * 60)
    print(f"Model: {model_name}")
    print(f"=" * 60)

    # Engineer features to match model expectations
    X = engineer_features_for_model(df, model)

    print(f"\n🔮 Predicting with {model_name}...")

    # Make predictions
    predictions = predict_model(model, data=X)

    # Create results dataframe
    id_col = 'id_test' if 'id_test' in df.columns else 'id'
    title_col = 'title_test' if 'title_test' in df.columns else 'title'

    df_results = pd.DataFrame({
        'id': df[id_col].values,
        'pmid': df['pmid'].values,
        'title': df[title_col].values,
        'ground_truth': df['ground_truth'].values,
        'predicted_label': predictions['prediction_label'].values,
        'prediction_score': predictions['prediction_score'].values
    })

    # Calculate metrics
    total = len(df_results)
    predicted_positive = (df_results['predicted_label'] == 1).sum()
    actual_positive = (df_results['ground_truth'] == 1).sum()

    # Confusion matrix
    tp = ((df_results['predicted_label'] == 1) & (df_results['ground_truth'] == 1)).sum()
    fp = ((df_results['predicted_label'] == 1) & (df_results['ground_truth'] == 0)).sum()
    tn = ((df_results['predicted_label'] == 0) & (df_results['ground_truth'] == 0)).sum()
    fn = ((df_results['predicted_label'] == 0) & (df_results['ground_truth'] == 1)).sum()

    # Metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / total if total > 0 else 0

    print(f"\n📊 Results for {model_name}:")
    print(f"   Total: {total:,} papers")
    print(f"   Predicted positive: {predicted_positive:,}")
    print(f"   Actual positive: {actual_positive:,}")
    print(f"\n   Metrics:")
    print(f"   - Accuracy: {accuracy:.3f}")
    print(f"   - Precision: {precision:.3f}")
    print(f"   - Recall: {recall:.3f}")
    print(f"   - F1: {f1:.3f}")

    # Save results
    output_file = OUTPUT_DIR / f"pycaret_{model_name}_results.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n✅ Saved: {output_file}")

    # Store metrics
    results[model_name] = {
        'total_papers': int(total),
        'predicted_positive': int(predicted_positive),
        'actual_positive': int(actual_positive),
        'confusion_matrix': {
            'tp': int(tp),
            'fp': int(fp),
            'tn': int(tn),
            'fn': int(fn)
        },
        'metrics': {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1)
        },
        'output_file': str(output_file)
    }

# ============================================
# SAVE SUMMARY
# ============================================

summary = {
    'session_id': SESSION_ID,
    'timestamp': datetime.now().isoformat(),
    'test_set': str(TEST_SET),
    'test_set_size': len(df),
    'models_run': list(results.keys()),
    'results': results
}

summary_file = OUTPUT_DIR / "pycaret_prediction_summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*60}")
print("🎉 PYCARET PREDICTION COMPLETE")
print(f"{'='*60}")
print(f"\n📁 Results saved to: {OUTPUT_DIR}")
print(f"📄 Summary: {summary_file}")
print(f"\n✅ {len(results)} model(s) completed successfully")
print("\n🎯 Next step: Run Phase 4 - Performance evaluation")
