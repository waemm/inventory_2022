#!/usr/bin/env python3
"""
Verification script for Phase 2: Feature Engineering Pipeline

This script performs comprehensive validation of the feature engineering outputs:
1. Loads all output files (CSV, pickle, JSON, transformers)
2. Verifies data integrity and feature statistics
3. Tests transformer functionality
4. Generates a verification report

Usage:
    python verify_feature_engineering.py
"""

import json
import pickle
from pathlib import Path
import pandas as pd
import numpy as np


def test_file_existence():
    """Test that all expected output files exist"""
    print("=" * 70)
    print("TEST 1: FILE EXISTENCE")
    print("=" * 70)

    expected_files = {
        'CSV': 'data/metadata/features_engineered.csv',
        'Pickle': 'data/metadata/features_engineered.pkl',
        'Validation JSON': 'data/metadata/features_validation.json',
        'Transformers': 'data/metadata/feature_transformers.pkl'
    }

    all_exist = True
    for name, path in expected_files.items():
        exists = Path(path).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name:20s}: {path}")
        all_exist = all_exist and exists

    return all_exist


def test_data_integrity():
    """Test data integrity and shape"""
    print("\n" + "=" * 70)
    print("TEST 2: DATA INTEGRITY")
    print("=" * 70)

    # Load both CSV and pickle
    df_csv = pd.read_csv('data/metadata/features_engineered.csv')
    df_pkl = pd.read_pickle('data/metadata/features_engineered.pkl')

    print(f"\n  CSV shape: {df_csv.shape}")
    print(f"  Pickle shape: {df_pkl.shape}")

    # Test 1: Shapes match
    shapes_match = df_csv.shape == df_pkl.shape
    print(f"  {'✓' if shapes_match else '✗'} CSV and pickle shapes match")

    # Test 2: Expected dimensions
    expected_rows = 21392
    expected_cols = 38
    dims_correct = (len(df_csv) == expected_rows and
                   len(df_csv.columns) == expected_cols)
    print(f"  {'✓' if dims_correct else '✗'} Expected dimensions: ({expected_rows}, {expected_cols})")

    # Test 3: No NaN in engineered features
    original_cols = ['id', 'title', 'abstract', 'publication_date',
                    'hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess',
                    'inPMC', 'inEPMC', 'hasPDF', 'hasBook', 'citedByCount',
                    'pubYear', 'pubType', 'keywords', 'meshTerms', 'journalTitle',
                    'journalISSN', 'authorAffiliations']

    engineered_cols = [col for col in df_csv.columns if col not in original_cols]
    nan_in_engineered = df_csv[engineered_cols].isnull().sum().sum()
    no_nans = nan_in_engineered == 0

    print(f"  {'✓' if no_nans else '✗'} No NaN in engineered features (found {nan_in_engineered})")

    return shapes_match and dims_correct and no_nans


def test_feature_statistics():
    """Test feature statistics are within expected ranges"""
    print("\n" + "=" * 70)
    print("TEST 3: FEATURE STATISTICS")
    print("=" * 70)

    df = pd.read_pickle('data/metadata/features_engineered.pkl')
    all_pass = True

    # Test numerical features (should be normalized)
    print("\n  Normalized numerical features:")
    for col in ['log_citations', 'years_since_pub']:
        mean = df[col].mean()
        std = df[col].std()
        mean_ok = abs(mean) < 1e-10  # Should be ~0
        std_ok = abs(std - 1.0) < 0.01  # Should be ~1

        status = "✓" if (mean_ok and std_ok) else "✗"
        print(f"    {status} {col:20s}: mean={mean:.6f}, std={std:.6f}")
        all_pass = all_pass and mean_ok and std_ok

    # Test boolean features (should be 0/1)
    print("\n  Boolean features (0/1 encoding):")
    boolean_cols = ['hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess',
                   'inPMC', 'inEPMC', 'hasPDF', 'hasBook']

    for col in boolean_cols:
        unique_vals = set(df[col].unique())
        is_binary = unique_vals.issubset({0, 1})
        status = "✓" if is_binary else "✗"
        print(f"    {status} {col:25s}: values={unique_vals}")
        all_pass = all_pass and is_binary

    # Test publication type features
    print("\n  Publication type features:")
    for col in ['is_research_article', 'is_review_article']:
        unique_vals = set(df[col].unique())
        is_binary = unique_vals.issubset({0, 1})
        count = df[col].sum()
        status = "✓" if is_binary else "✗"
        print(f"    {status} {col:25s}: {count} positive")
        all_pass = all_pass and is_binary

    # Test TF-IDF features exist
    print("\n  TF-IDF features:")
    mesh_cols = [col for col in df.columns if col.startswith('mesh_tfidf_')]
    kw_cols = [col for col in df.columns if col.startswith('keyword_tfidf_')]

    mesh_ok = len(mesh_cols) == 7
    kw_ok = len(kw_cols) == 5

    print(f"    {'✓' if mesh_ok else '✗'} MeSH components: {len(mesh_cols)} (expected 7)")
    print(f"    {'✓' if kw_ok else '✗'} Keyword components: {len(kw_cols)} (expected 5)")

    all_pass = all_pass and mesh_ok and kw_ok

    return all_pass


def test_validation_report():
    """Test validation report structure and content"""
    print("\n" + "=" * 70)
    print("TEST 4: VALIDATION REPORT")
    print("=" * 70)

    with open('data/metadata/features_validation.json', 'r') as f:
        validation = json.load(f)

    all_pass = True

    # Required top-level keys
    required_keys = ['total_rows', 'total_features', 'feature_names',
                    'timestamp', 'feature_statistics', 'engineering_stats']

    print("\n  Required keys:")
    for key in required_keys:
        exists = key in validation
        status = "✓" if exists else "✗"
        print(f"    {status} {key}")
        all_pass = all_pass and exists

    # Check counts
    print("\n  Validation counts:")
    rows_ok = validation['total_rows'] == 21392
    features_ok = validation['total_features'] == 18

    print(f"    {'✓' if rows_ok else '✗'} Total rows: {validation['total_rows']}")
    print(f"    {'✓' if features_ok else '✗'} Total features: {validation['total_features']}")

    all_pass = all_pass and rows_ok and features_ok

    # Check explained variance exists
    print("\n  Explained variance:")
    mesh_var_ok = 'mesh_explained_variance' in validation['engineering_stats']
    kw_var_ok = 'keyword_explained_variance' in validation['engineering_stats']

    print(f"    {'✓' if mesh_var_ok else '✗'} MeSH explained variance")
    print(f"    {'✓' if kw_var_ok else '✗'} Keyword explained variance")

    if mesh_var_ok:
        total_var = validation['engineering_stats']['mesh_explained_variance']['total']
        print(f"        MeSH total variance: {total_var:.4f}")

    if kw_var_ok:
        total_var = validation['engineering_stats']['keyword_explained_variance']['total']
        print(f"        Keyword total variance: {total_var:.4f}")

    all_pass = all_pass and mesh_var_ok and kw_var_ok

    return all_pass


def test_transformers():
    """Test that transformers can be loaded and used"""
    print("\n" + "=" * 70)
    print("TEST 5: TRANSFORMERS")
    print("=" * 70)

    with open('data/metadata/feature_transformers.pkl', 'rb') as f:
        transformers = pickle.load(f)

    required_transformers = ['scaler', 'mesh_vectorizer', 'mesh_svd',
                            'keyword_vectorizer', 'keyword_svd']

    all_pass = True
    print("\n  Transformer objects:")
    for name in required_transformers:
        exists = name in transformers and transformers[name] is not None
        status = "✓" if exists else "✗"
        print(f"    {status} {name}")
        all_pass = all_pass and exists

    # Test scaler can transform
    if transformers['scaler'] is not None:
        try:
            test_data = np.array([[2.5, 8.0]])
            scaled = transformers['scaler'].transform(test_data)
            scaler_works = scaled.shape == test_data.shape
            print(f"\n  {'✓' if scaler_works else '✗'} Scaler transform test")
            all_pass = all_pass and scaler_works
        except Exception as e:
            print(f"\n  ✗ Scaler transform test: {e}")
            all_pass = False

    return all_pass


def test_feature_names():
    """Test that all expected feature names exist"""
    print("\n" + "=" * 70)
    print("TEST 6: FEATURE NAMES")
    print("=" * 70)

    df = pd.read_pickle('data/metadata/features_engineered.pkl')

    expected_features = {
        'Numerical (2)': ['log_citations', 'years_since_pub'],
        'Boolean (8)': ['hasDbCrossReferences', 'hasData', 'hasSuppl',
                       'isOpenAccess', 'inPMC', 'inEPMC', 'hasPDF', 'hasBook'],
        'Publication Type (2)': ['is_research_article', 'is_review_article'],
        'MeSH TF-IDF (7)': [f'mesh_tfidf_{i}' for i in range(7)],
        'Keyword TF-IDF (5)': [f'keyword_tfidf_{i}' for i in range(5)],
        'Missing Indicators (2)': ['meshTerms_missing', 'keywords_missing']
    }

    all_pass = True
    for category, features in expected_features.items():
        print(f"\n  {category}:")
        for feat in features:
            exists = feat in df.columns
            status = "✓" if exists else "✗"
            print(f"    {status} {feat}")
            all_pass = all_pass and exists

    return all_pass


def main():
    """Run all verification tests"""
    print("\n" + "=" * 70)
    print("FEATURE ENGINEERING PIPELINE VERIFICATION")
    print("=" * 70)
    print("\nRunning comprehensive validation tests...\n")

    results = {
        'File Existence': test_file_existence(),
        'Data Integrity': test_data_integrity(),
        'Feature Statistics': test_feature_statistics(),
        'Validation Report': test_validation_report(),
        'Transformers': test_transformers(),
        'Feature Names': test_feature_names()
    }

    # Print summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status:10s} {test_name}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nPhase 2 feature engineering is complete and verified.")
        print("Ready to proceed to Phase 3 (Multi-Task Model Training).")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease review the failed tests above and re-run:")
        print("  python src/prepare_metadata_features.py \\")
        print("      --input data/metadata/pmc_metadata_enhanced_full.csv \\")
        print("      --output data/metadata/features_engineered.csv")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
