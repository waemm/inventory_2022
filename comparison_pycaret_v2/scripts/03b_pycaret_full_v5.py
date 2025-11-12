#!/usr/bin/env python3
"""
Phase 3b: PyCaret Prediction on Full V5.1 Query Set

Runs PyCaret models on ENTIRE V5.1 query set (156,231 papers)
to see production-scale performance.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings
import time
warnings.filterwarnings('ignore')

print("=" * 80)
print("PYCARET PREDICTION - FULL V5.1 QUERY SET")
print("=" * 80)

# ============================================
# CONFIGURATION
# ============================================

BASE_DIR = Path(__file__).parent.parent.parent
COMPARISON_DIR = BASE_DIR / "comparison_pycaret_v2"

# Input data - FULL V5.1
V5_FULL = BASE_DIR / "data/final_query_v5.1_2011_2021/query_results.csv"

# Model paths
MODEL_TEST_TRUE = Path("/tmp/pycaret_test/pycaret_metadata_classifier_v1")
MODEL_TEST_FALSE = Path("/tmp/pycaret_test_false/pycaret_metadata_classifier_v1")

# Output paths
OUTPUT_DIR = COMPARISON_DIR / "pycaret_full_v5_predictions"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SESSION_ID = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

print(f"\n📋 Configuration:")
print(f"   Session ID: {SESSION_ID}")
print(f"   Input: Full V5.1 query set")
print(f"   Output: {OUTPUT_DIR}")
print("=" * 80)

# ============================================
# LOAD DATA
# ============================================

print("\n📚 Loading full V5.1 dataset...")
start_load = time.time()

df = pd.read_csv(V5_FULL, low_memory=False)
df['pmid'] = df['id'].astype(float)

# Deduplicate
n_before = len(df)
df = df.drop_duplicates(subset=['pmid'], keep='first')
n_after = len(df)

print(f"   ✅ Loaded: {n_before:,} papers")
if n_before > n_after:
    print(f"   ✅ Deduplicated: {n_after:,} unique papers ({n_before - n_after:,} duplicates removed)")

load_time = time.time() - start_load
print(f"   ⏱️  Load time: {load_time:.1f}s")

# ============================================
# FEATURE ENGINEERING FUNCTION
# (Same as 03_pycaret_prediction.py)
# ============================================

def engineer_features_for_model(df, model):
    """Engineer features to match EXACTLY what the model expects."""
    expected_features = list(model.feature_names_in_)
    print(f"\n🔧 Engineering {len(expected_features)} features...")

    df = df.copy()

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

    # Parse list columns
    import json

    def safe_parse_list(x):
        if pd.isna(x) or x == '':
            return []
        if isinstance(x, str) and x.startswith('['):
            try:
                parsed = json.loads(x)
                # Filter out None values that come from JSON null
                return [item for item in parsed if item is not None]
            except:
                return []
        return []

    df['meshTerms_list'] = df['meshTerms'].apply(safe_parse_list)
    df['pubType_list'] = df['pubType'].apply(safe_parse_list)
    df['keywords_list'] = df['keywords'].apply(safe_parse_list)

    # Base features
    df['citedByCount'] = df['citedByCount'].fillna(0).astype(int)
    df['pubYear'] = df['pubYear'].fillna(2020).astype(int)

    # Binary access features
    binary_features = ['inEPMC', 'inPMC', 'hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess']
    for feat in binary_features:
        if feat in df.columns:
            df[feat] = df[feat].apply(convert_to_binary)
        else:
            df[feat] = 0

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
    df['title_length'] = df['title'].fillna('').apply(len)
    df['abstract_length'] = df['abstract'].fillna('').apply(len)
    df['has_abstract'] = (df['abstract_length'] > 0).astype(int)

    # Keyword features
    df['keyword_count'] = df['keywords_list'].apply(len)
    database_keywords = ['database', 'repository', 'resource', 'portal', 'knowledgebase',
                         'archive', 'registry', 'catalog', 'collection']
    df['has_database_keyword'] = df['keywords_list'].apply(
        lambda x: 1 if any(kw.lower() in [k.lower() for k in x if k and isinstance(k, str)] for kw in database_keywords) else 0
    )

    # Create specific MeSH features
    for feat in expected_features:
        if feat.startswith('mesh_') and feat != 'mesh_term_count':
            mesh_name = feat[5:].replace('_', ' ').replace(',', ', ')
            df[feat] = df['meshTerms_list'].apply(
                lambda x: 1 if any(mesh_name.lower() in term.lower() for term in x if term and isinstance(term, str)) else 0
            )

    # Create specific pubtype features
    pubtype_mapping = {
        'pubtype_Journal_Article': 'Journal Article',
        'pubtype_Review': 'Review',
        'pubtype_Research_Support_NIH_Extramura': 'Research Support, N.I.H., Extramural',
        'pubtype_Research_Support_Non-US_Govt': "Research Support, Non-U.S. Gov't",
        'pubtype_Research_Support_US_Govt_PHS': "Research Support, U.S. Gov't, P.H.S.",
        'pubtype_Comparative_Study': 'Comparative Study',
        'pubtype_Letter': 'Letter',
        'pubtype_Comment': 'Comment',
        'pubtype_Editorial': 'Editorial',
        'pubtype_Case_Reports': 'Case Reports',
    }
    for feat, pubtype in pubtype_mapping.items():
        if feat in expected_features:
            df[feat] = df['pubType_list'].apply(lambda x: 1 if pubtype in x else 0)

    # Create specific journal features
    for feat in expected_features:
        if feat.startswith('journal_'):
            journal_pattern = feat[8:]
            df[feat] = df['journalTitle'].fillna('').apply(
                lambda x: 1 if journal_pattern.lower().replace('_', ' ') in x.lower() else 0
            )

    # Add label column (required by PyCaret)
    df['label'] = 0.5

    # Ensure all expected features exist
    for feat in expected_features:
        if feat not in df.columns:
            df[feat] = 0

    # Select features in EXACT order
    X = df[expected_features].copy()
    X = X.fillna(0)

    print(f"   ✅ Created {len(expected_features)} features")
    return X

# ============================================
# LOAD PYCARET MODELS
# ============================================

from pycaret.classification import load_model, predict_model

print("\n🤖 Loading PyCaret models...")

models_to_run = []

if MODEL_TEST_TRUE.with_suffix('.pkl').exists():
    model_test_true = load_model(str(MODEL_TEST_TRUE))
    models_to_run.append(('TEST_MODE_True', model_test_true))
    print(f"   ✅ Loaded TEST_MODE=True model ({len(model_test_true.feature_names_in_)} features)")

if MODEL_TEST_FALSE.with_suffix('.pkl').exists():
    model_test_false = load_model(str(MODEL_TEST_FALSE))
    models_to_run.append(('TEST_MODE_False', model_test_false))
    print(f"   ✅ Loaded TEST_MODE=False model ({len(model_test_false.feature_names_in_)} features)")

if len(models_to_run) == 0:
    raise FileNotFoundError("No PyCaret models found!")

print(f"\n✅ {len(models_to_run)} model(s) loaded and ready")

# ============================================
# RUN PREDICTIONS
# ============================================

print("\n🔮 Running predictions on full V5.1 dataset...")
print("=" * 80)

results = {}

for model_name, model in models_to_run:
    print(f"\n{'='*80}")
    print(f"Model: {model_name}")
    print(f"{'='*80}")

    start_time = time.time()

    # Engineer features
    X = engineer_features_for_model(df, model)

    feature_time = time.time() - start_time
    print(f"   ⏱️  Feature engineering: {feature_time:.1f}s")

    # Make predictions
    print(f"\n🔮 Predicting on {len(X):,} papers...")
    predict_start = time.time()

    predictions = predict_model(model, data=X)

    predict_time = time.time() - predict_start
    print(f"   ⏱️  Prediction time: {predict_time:.1f}s")
    print(f"   ⚡ Speed: {len(X)/predict_time:.0f} papers/second")

    # Create results dataframe
    df_results = pd.DataFrame({
        'id': df['id'].values,
        'pmid': df['pmid'].values,
        'title': df['title'].values,
        'predicted_label': predictions['prediction_label'].values,
        'prediction_score': predictions['prediction_score'].values
    })

    # Calculate statistics
    total = len(df_results)
    predicted_positive = (df_results['predicted_label'] == 1).sum()
    predicted_negative = (df_results['predicted_label'] == 0).sum()

    total_time = time.time() - start_time

    print(f"\n📊 Results for {model_name}:")
    print(f"   Total papers: {total:,}")
    print(f"   Predicted bio-resource: {predicted_positive:,} ({predicted_positive/total*100:.1f}%)")
    print(f"   Predicted NOT bio-resource: {predicted_negative:,} ({predicted_negative/total*100:.1f}%)")
    print(f"   ⏱️  Total time: {total_time:.1f}s ({total/total_time:.0f} papers/sec)")

    # Save results
    output_file = OUTPUT_DIR / f"pycaret_{model_name}_full_v5_results.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n✅ Saved: {output_file}")

    # Store metrics
    results[model_name] = {
        'total_papers': int(total),
        'predicted_positive': int(predicted_positive),
        'predicted_negative': int(predicted_negative),
        'positive_percentage': float(predicted_positive/total*100),
        'processing_time_seconds': float(total_time),
        'papers_per_second': float(total/total_time),
        'output_file': str(output_file)
    }

# ============================================
# SAVE SUMMARY
# ============================================

summary = {
    'session_id': SESSION_ID,
    'timestamp': datetime.now().isoformat(),
    'dataset': 'Full V5.1 Query (2011-2021)',
    'dataset_size': len(df),
    'models_run': list(results.keys()),
    'results': results
}

summary_file = OUTPUT_DIR / "full_v5_prediction_summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*80}")
print("🎉 PYCARET FULL V5.1 PREDICTION COMPLETE")
print(f"{'='*80}")
print(f"\n📁 Results saved to: {OUTPUT_DIR}")
print(f"📄 Summary: {summary_file}")
print(f"\n✅ Processed {len(df):,} papers with {len(results)} model(s)")
print("\n🎯 Next: Upload V5.1 to Google Drive for V2 classification")
