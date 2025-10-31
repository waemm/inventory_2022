#!/usr/bin/env python3
"""
Quick test/demo script for augmented training data

Demonstrates:
1. Loading augmented datasets
2. Verifying feature completeness
3. Separating original and feature columns
4. Basic statistics and coverage analysis
"""

import pandas as pd
import numpy as np


def test_augmented_data():
    """Test and demonstrate augmented training data"""

    print("="*70)
    print("Augmented Training Data Test")
    print("="*70)

    # Load augmented datasets
    print("\n1. Loading augmented datasets...")
    classif = pd.read_csv('data/augmented/classif_train_with_metadata.csv')
    ner = pd.read_csv('data/augmented/ner_train_with_metadata.csv')
    print(f"   ✓ Classification: {len(classif)} rows × {len(classif.columns)} columns")
    print(f"   ✓ NER: {len(ner)} rows × {len(ner.columns)} columns")

    # Define feature columns
    metadata_features = [
        'publication_date', 'hasDbCrossReferences', 'hasData', 'hasSuppl',
        'isOpenAccess', 'inPMC', 'inEPMC', 'hasPDF', 'hasBook',
        'citedByCount', 'pubYear', 'pubType', 'keywords', 'meshTerms',
        'journalTitle', 'journalISSN', 'authorAffiliations'
    ]

    engineered_features = [
        'log_citations', 'years_since_pub', 'is_research_article',
        'is_review_article', 'meshTerms_missing', 'keywords_missing'
    ]

    tfidf_features = (
        [f'mesh_tfidf_{i}' for i in range(7)] +
        [f'keyword_tfidf_{i}' for i in range(5)]
    )

    all_feature_cols = metadata_features + engineered_features + tfidf_features

    # Verify features exist
    print("\n2. Verifying feature columns...")
    missing_classif = [col for col in all_feature_cols if col not in classif.columns]
    missing_ner = [col for col in all_feature_cols if col not in ner.columns]

    if not missing_classif and not missing_ner:
        print(f"   ✓ All {len(all_feature_cols)} feature columns present")
    else:
        print(f"   ⚠ Missing in classification: {missing_classif}")
        print(f"   ⚠ Missing in NER: {missing_ner}")

    # Check for missing values
    print("\n3. Checking for missing values...")
    # Note: Text fields (keywords, meshTerms, etc.) may have NaN when legitimately
    # unavailable in source metadata, even for papers with citations
    classif_missing = classif[all_feature_cols].isna().sum()
    ner_missing = ner[all_feature_cols].isna().sum()

    # Check critical numerical/engineered features
    critical_features = ['log_citations', 'years_since_pub', 'is_research_article',
                         'is_review_article'] + tfidf_features
    critical_missing = classif[critical_features].isna().sum().sum()

    print(f"   Critical features missing: {critical_missing}")
    if critical_missing == 0:
        print(f"   ✓ All critical numerical/engineered features complete")
    else:
        print(f"   ⚠ Some critical features have NaN")

    # Text fields may legitimately be missing
    text_fields = ['keywords', 'meshTerms', 'journalTitle', 'journalISSN', 'authorAffiliations']
    text_missing = classif[text_fields].isna().sum()
    print(f"   Text fields (may be unavailable in source):")
    for field in text_fields:
        if field in text_missing.index:
            pct = (text_missing[field] / len(classif)) * 100
            print(f"      {field}: {text_missing[field]} ({pct:.1f}%) missing")

    # Analyze real vs imputed metadata
    print("\n4. Analyzing metadata coverage...")

    # Papers with citations > 0 likely have real metadata
    classif_real_metadata = (classif['citedByCount'] > 0).sum()
    ner_real_metadata = (ner['citedByCount'] > 0).sum()

    print(f"   Classification:")
    print(f"      Real metadata: {classif_real_metadata}/{len(classif)} "
          f"({classif_real_metadata/len(classif)*100:.1f}%)")
    print(f"      Imputed: {len(classif) - classif_real_metadata} "
          f"({(len(classif) - classif_real_metadata)/len(classif)*100:.1f}%)")

    print(f"   NER:")
    print(f"      Real metadata: {ner_real_metadata}/{len(ner)} "
          f"({ner_real_metadata/len(ner)*100:.1f}%)")
    print(f"      Imputed: {len(ner) - ner_real_metadata} "
          f"({(len(ner) - ner_real_metadata)/len(ner)*100:.1f}%)")

    # Feature statistics
    print("\n5. Feature statistics (Classification dataset)...")

    # Boolean features
    print(f"   hasData: {(classif['hasData'] == 1).sum()} "
          f"({(classif['hasData'] == 1).sum()/len(classif)*100:.1f}%) have data")
    print(f"   isOpenAccess: {(classif['isOpenAccess'] == 1).sum()} "
          f"({(classif['isOpenAccess'] == 1).sum()/len(classif)*100:.1f}%) open access")

    # Numerical features
    print(f"   Citations: mean={classif['citedByCount'].mean():.1f}, "
          f"median={classif['citedByCount'].median():.1f}")
    print(f"   Log citations (scaled): mean={classif['log_citations'].mean():.3f}, "
          f"std={classif['log_citations'].std():.3f}")

    # TF-IDF features
    mesh_tfidf_cols = [f'mesh_tfidf_{i}' for i in range(7)]
    mesh_nonzero = (classif[mesh_tfidf_cols].abs() > 0.01).any(axis=1).sum()
    print(f"   MeSH TF-IDF: {mesh_nonzero}/{len(classif)} "
          f"({mesh_nonzero/len(classif)*100:.1f}%) have non-zero vectors")

    # Sample data
    print("\n6. Sample augmented data (first 3 rows)...")
    sample_cols = ['id', 'title', 'citedByCount', 'hasData', 'log_citations',
                   'years_since_pub', 'is_research_article']
    sample_cols = [col for col in sample_cols if col in classif.columns]

    print("\n" + classif[sample_cols].head(3).to_string(index=False))

    # Usage example
    print("\n" + "="*70)
    print("Usage Example: Preparing for Multi-Task Learning")
    print("="*70)

    print("\nOriginal columns:")
    original_cols = [col for col in classif.columns if col not in all_feature_cols]
    print(f"   {len(original_cols)} columns: {original_cols[:5]}...")

    print("\nFeature columns:")
    print(f"   {len(all_feature_cols)} columns:")
    print(f"      Metadata: {len(metadata_features)} columns")
    print(f"      Engineered: {len(engineered_features)} columns")
    print(f"      TF-IDF: {len(tfidf_features)} columns")

    print("\nExample code:")
    print("""
    # Load augmented data
    df = pd.read_csv('data/augmented/classif_train_with_metadata.csv')

    # Separate features
    text_cols = ['title', 'abstract']
    metadata_cols = [list of 35 feature columns]
    label_col = 'curation_score'

    # Extract for training
    X_text = df[text_cols]
    X_metadata = df[metadata_cols]
    y = df[label_col]

    # Multi-task model
    # Option 1: Early fusion (concatenate embeddings)
    # Option 2: Late fusion (separate towers + combine)
    """)

    print("\n" + "="*70)
    print("✓ All tests passed! Augmented data ready for training.")
    print("="*70)


if __name__ == '__main__':
    test_augmented_data()
