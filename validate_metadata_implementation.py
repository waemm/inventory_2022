#!/usr/bin/env python3
"""
Comprehensive validation script for metadata fetching and feature engineering
Validates data integrity, correctness, and edge cases
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

def validate_enhanced_metadata():
    """Validate the enhanced metadata CSV"""
    print("=" * 70)
    print("VALIDATING ENHANCED METADATA")
    print("=" * 70)

    issues = []
    warnings = []

    # Load data
    csv_path = "/Users/warren/development/GBC/inventory_2022/data/metadata/pmc_metadata_enhanced_full.csv"
    df = pd.read_csv(csv_path)

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"Expected: 21,392 rows (header + 21,391 data)")

    # 1. Row count validation
    expected_rows = 21391  # Data rows (not counting header)
    actual_rows = len(df)
    if actual_rows != expected_rows:
        issues.append(f"Row count mismatch: expected {expected_rows}, got {actual_rows}")
    else:
        print(f"✓ Row count correct: {actual_rows}")

    # 2. Column count validation (20 metadata fields)
    expected_cols = 20
    actual_cols = len(df.columns)
    if actual_cols != expected_cols:
        issues.append(f"Column count mismatch: expected {expected_cols}, got {actual_cols}")
    else:
        print(f"✓ Column count correct: {actual_cols}")

    # 3. Required columns
    required_cols = [
        'id', 'title', 'abstract', 'publication_date',
        'hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess',
        'inPMC', 'inEPMC', 'hasPDF', 'hasBook',
        'citedByCount', 'pubYear', 'pubType',
        'keywords', 'meshTerms', 'journalTitle', 'journalISSN', 'authorAffiliations'
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")
    else:
        print(f"✓ All {len(required_cols)} required columns present")

    # 4. Check for duplicate PMIDs
    duplicates = df['id'].duplicated().sum()
    if duplicates > 0:
        issues.append(f"Found {duplicates} duplicate PMIDs")
    else:
        print(f"✓ No duplicate PMIDs")

    # 5. Check PMID format (should be numeric)
    non_numeric_pmids = df['id'].apply(lambda x: not str(x).isdigit() if pd.notna(x) else False).sum()
    if non_numeric_pmids > 0:
        warnings.append(f"Found {non_numeric_pmids} non-numeric PMIDs")
    else:
        print(f"✓ All PMIDs are numeric")

    # 6. Check boolean fields (should be Y/N or NaN)
    boolean_fields = ['hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess',
                      'inPMC', 'inEPMC', 'hasPDF', 'hasBook']

    for field in boolean_fields:
        if field in df.columns:
            valid_values = df[field].dropna().isin(['Y', 'N']).sum()
            total_values = df[field].notna().sum()
            if valid_values != total_values:
                issues.append(f"{field}: {total_values - valid_values} invalid values (not Y/N)")
            else:
                print(f"✓ {field}: all values are Y/N or NaN")

    # 7. Check citedByCount (should be numeric, >= 0)
    if 'citedByCount' in df.columns:
        negative_citations = (df['citedByCount'] < 0).sum()
        if negative_citations > 0:
            issues.append(f"citedByCount: {negative_citations} negative values")
        else:
            print(f"✓ citedByCount: all values >= 0")

        # Check for reasonable range
        max_citations = df['citedByCount'].max()
        print(f"  Citation range: 0 to {max_citations}")

    # 8. Check pubYear (should be 4-digit year, reasonable range)
    if 'pubYear' in df.columns:
        invalid_years = df['pubYear'].apply(
            lambda x: pd.isna(x) or x < 1900 or x > 2025
        ).sum()
        if invalid_years > 0:
            warnings.append(f"pubYear: {invalid_years} invalid years (outside 1900-2025)")
        else:
            print(f"✓ pubYear: all values in valid range")

        year_range = f"{df['pubYear'].min():.0f} to {df['pubYear'].max():.0f}"
        print(f"  Publication year range: {year_range}")

    # 9. Check JSON fields (should be valid JSON or NaN)
    json_fields = ['pubType', 'keywords', 'meshTerms', 'authorAffiliations']

    for field in json_fields:
        if field in df.columns:
            invalid_json = 0
            valid_json = 0
            for value in df[field]:
                if pd.isna(value):
                    continue
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        valid_json += 1
                    else:
                        invalid_json += 1
                except (json.JSONDecodeError, TypeError):
                    invalid_json += 1

            if invalid_json > 0:
                issues.append(f"{field}: {invalid_json} invalid JSON values")
            else:
                print(f"✓ {field}: all non-null values are valid JSON lists ({valid_json} valid)")

    # 10. Check for completely empty rows
    empty_rows = df.isnull().all(axis=1).sum()
    if empty_rows > 0:
        issues.append(f"Found {empty_rows} completely empty rows")
    else:
        print(f"✓ No completely empty rows")

    # 11. Missing data summary
    print("\nMissing data summary:")
    missing_summary = df.isnull().sum()
    missing_pct = 100 * missing_summary / len(df)
    for col in required_cols:
        if col in df.columns:
            print(f"  {col}: {missing_summary[col]} missing ({missing_pct[col]:.1f}%)")

    return issues, warnings

def validate_engineered_features():
    """Validate the engineered features CSV"""
    print("\n" + "=" * 70)
    print("VALIDATING ENGINEERED FEATURES")
    print("=" * 70)

    issues = []
    warnings = []

    # Load data
    csv_path = "/Users/warren/development/GBC/inventory_2022/data/metadata/features_engineered.csv"
    df = pd.read_csv(csv_path)

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # 1. Row count consistency
    expected_rows = 21391
    actual_rows = len(df)
    if actual_rows != expected_rows:
        issues.append(f"Row count mismatch: expected {expected_rows}, got {actual_rows}")
    else:
        print(f"✓ Row count consistent: {actual_rows}")

    # 2. Expected column count (20 original + 18 engineered = 38)
    expected_total_cols = 38
    actual_cols = len(df.columns)
    if actual_cols != expected_total_cols:
        warnings.append(f"Column count: expected {expected_total_cols}, got {actual_cols}")
    print(f"  Total columns: {actual_cols}")

    # 3. Check for NaN in engineered features
    engineered_features = [
        'log_citations', 'years_since_pub',
        'is_research_article', 'is_review_article',
        'meshTerms_missing', 'keywords_missing'
    ]

    # Add TF-IDF features
    tfidf_features = [col for col in df.columns if 'tfidf' in col.lower()]
    engineered_features.extend(tfidf_features)

    # Add boolean flags (should now be 0/1)
    boolean_features = ['hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess',
                        'inPMC', 'inEPMC', 'hasPDF', 'hasBook']
    engineered_features.extend([f for f in boolean_features if f in df.columns])

    nan_found = False
    for feature in engineered_features:
        if feature in df.columns:
            nan_count = df[feature].isnull().sum()
            if nan_count > 0:
                issues.append(f"{feature}: {nan_count} NaN values found")
                nan_found = True

    if not nan_found:
        print(f"✓ No NaN values in {len(engineered_features)} engineered features")

    # 4. Check normalized features (log_citations, years_since_pub)
    for feature in ['log_citations', 'years_since_pub']:
        if feature in df.columns:
            mean = df[feature].mean()
            std = df[feature].std()
            print(f"\n{feature}:")
            print(f"  Mean: {mean:.6f} (expected ~0)")
            print(f"  Std: {std:.6f} (expected ~1)")
            print(f"  Min: {df[feature].min():.3f}")
            print(f"  Max: {df[feature].max():.3f}")

            if abs(mean) > 0.01:
                warnings.append(f"{feature}: mean {mean:.6f} not close to 0")
            if abs(std - 1.0) > 0.01:
                warnings.append(f"{feature}: std {std:.6f} not close to 1")

    # 5. Check boolean features (should be 0 or 1)
    for feature in boolean_features:
        if feature in df.columns:
            unique_vals = df[feature].unique()
            if not set(unique_vals).issubset({0, 1}):
                issues.append(f"{feature}: contains values other than 0/1: {unique_vals}")
            else:
                positive_count = df[feature].sum()
                print(f"✓ {feature}: {positive_count} positive ({100*positive_count/len(df):.1f}%)")

    # 6. Check publication type features
    for feature in ['is_research_article', 'is_review_article']:
        if feature in df.columns:
            unique_vals = df[feature].unique()
            if not set(unique_vals).issubset({0, 1}):
                issues.append(f"{feature}: contains values other than 0/1: {unique_vals}")
            else:
                count = df[feature].sum()
                print(f"✓ {feature}: {count} positive ({100*count/len(df):.1f}%)")

    # 7. Check missing indicators
    for feature in ['meshTerms_missing', 'keywords_missing']:
        if feature in df.columns:
            unique_vals = df[feature].unique()
            if not set(unique_vals).issubset({0, 1}):
                issues.append(f"{feature}: contains values other than 0/1: {unique_vals}")
            else:
                missing_count = df[feature].sum()
                print(f"  {feature}: {missing_count} missing ({100*missing_count/len(df):.1f}%)")

    # 8. Check TF-IDF features (should be numeric, reasonable range)
    print(f"\nTF-IDF features found: {len(tfidf_features)}")
    for feature in tfidf_features:
        if feature in df.columns:
            if df[feature].dtype not in ['float64', 'int64']:
                issues.append(f"{feature}: wrong dtype {df[feature].dtype}")

            # Check for inf values
            inf_count = np.isinf(df[feature]).sum()
            if inf_count > 0:
                issues.append(f"{feature}: {inf_count} inf values")

    # 9. Check data types
    print("\nData types:")
    for col in ['log_citations', 'years_since_pub'] + tfidf_features[:3]:
        if col in df.columns:
            print(f"  {col}: {df[col].dtype}")

    # 10. Overall statistics
    print(f"\nOverall statistics:")
    print(f"  Total papers: {len(df):,}")
    print(f"  Total columns: {len(df.columns)}")
    print(f"  Engineered features: {len(engineered_features)}")

    return issues, warnings

def validate_json_output():
    """Validate the validation JSON file"""
    print("\n" + "=" * 70)
    print("VALIDATING JSON OUTPUT")
    print("=" * 70)

    issues = []
    warnings = []

    json_path = "/Users/warren/development/GBC/inventory_2022/data/metadata/features_validation.json"

    try:
        with open(json_path, 'r') as f:
            validation = json.load(f)

        print(f"✓ JSON file loaded successfully")

        # Check required keys
        required_keys = ['total_rows', 'total_features', 'feature_names', 'feature_statistics']
        missing_keys = [key for key in required_keys if key not in validation]
        if missing_keys:
            issues.append(f"JSON missing keys: {missing_keys}")
        else:
            print(f"✓ All required keys present")

        # Check row count consistency
        if validation['total_rows'] != 21392:
            issues.append(f"JSON reports {validation['total_rows']} rows, expected 21,392")
        else:
            print(f"✓ Row count in JSON: {validation['total_rows']}")

        # Check feature count
        print(f"  Total features in JSON: {validation['total_features']}")
        print(f"  Feature names count: {len(validation['feature_names'])}")

        # Check for NaN in feature statistics
        nan_features = []
        for feature_name, stats in validation['feature_statistics'].items():
            if 'nan_count' in stats and stats['nan_count'] > 0:
                nan_features.append(f"{feature_name}: {stats['nan_count']} NaNs")

        if nan_features:
            issues.append(f"Features with NaN values: {nan_features}")
        else:
            print(f"✓ No NaN values reported in statistics")

    except FileNotFoundError:
        issues.append(f"Validation JSON file not found: {json_path}")
    except json.JSONDecodeError as e:
        issues.append(f"JSON decode error: {e}")
    except Exception as e:
        issues.append(f"Unexpected error loading JSON: {e}")

    return issues, warnings

def main():
    """Main validation function"""
    print("\n")
    print("*" * 70)
    print("COMPREHENSIVE METADATA IMPLEMENTATION VALIDATION")
    print("*" * 70)
    print("\n")

    all_issues = []
    all_warnings = []

    # Validate enhanced metadata
    try:
        issues, warnings = validate_enhanced_metadata()
        all_issues.extend(issues)
        all_warnings.extend(warnings)
    except Exception as e:
        all_issues.append(f"Enhanced metadata validation failed: {e}")
        import traceback
        traceback.print_exc()

    # Validate engineered features
    try:
        issues, warnings = validate_engineered_features()
        all_issues.extend(issues)
        all_warnings.extend(warnings)
    except Exception as e:
        all_issues.append(f"Engineered features validation failed: {e}")
        import traceback
        traceback.print_exc()

    # Validate JSON output
    try:
        issues, warnings = validate_json_output()
        all_issues.extend(issues)
        all_warnings.extend(warnings)
    except Exception as e:
        all_issues.append(f"JSON validation failed: {e}")
        import traceback
        traceback.print_exc()

    # Print final summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if all_issues:
        print(f"\n❌ CRITICAL ISSUES FOUND: {len(all_issues)}")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n✓ No critical issues found")

    if all_warnings:
        print(f"\n⚠️  WARNINGS: {len(all_warnings)}")
        for i, warning in enumerate(all_warnings, 1):
            print(f"  {i}. {warning}")
    else:
        print("\n✓ No warnings")

    # Overall assessment
    print("\n" + "=" * 70)
    if not all_issues:
        print("OVERALL ASSESSMENT: PASS ✓")
    else:
        print("OVERALL ASSESSMENT: FAIL ❌")
    print("=" * 70)

    return len(all_issues) == 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
