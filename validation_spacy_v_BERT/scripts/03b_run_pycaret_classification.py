#!/usr/bin/env python3
"""
Script 03b: Run PyCaret Classification
=======================================

Purpose:
    Run BOTH PyCaret models on validation sample for comparison study.
    Engineers features to match model expectations (92 or 112 features).

Models:
    1. test_mode_true: 92 features (basic metadata)
    2. test_mode_false: 112 features (includes MeSH/journal features)

Usage:
    cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT
    source ../pycaret_env/bin/activate
    python scripts/03b_run_pycaret_classification.py

    For testing with small sample:
    TEST_MODE=True python scripts/03b_run_pycaret_classification.py

Inputs:
    - results/validation/sample/validation_sample_with_abstracts.csv
    - results/validation/metadata/validation_metadata_epmc.csv (fresh EPMC metadata)
    - ../../pycaret_models/test_mode_true/pycaret_metadata_classifier_v1.pkl
    - ../../pycaret_models/test_mode_false/pycaret_metadata_classifier_v1.pkl

Outputs:
    - results/validation/classification/pycaret_test_mode_true_results.csv
    - results/validation/classification/pycaret_test_mode_false_results.csv
    - logs/03b_run_pycaret_classification.log

Environment: pycaret_env (Python 3.11.9, PyCaret 3.0.4)

Author: Phase 1 Validation Study
Date: 2025-11-13
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json
import ast  # CRITICAL FIX: For parsing Python literal syntax (single quotes)
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# TEST_MODE: Set to True for quick testing (10-15 papers)
#            Set to False for full validation (all papers in sample)
TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
SESSION_ID = os.environ.get('SESSION_ID', '')
if not SESSION_ID:
    # Generate session ID if not provided
    import random
    import string
    from datetime import datetime
    mode_suffix = "_test" if TEST_MODE else ""
    SESSION_ID = f"{datetime.now().strftime('%Y-%m-%d')}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}{mode_suffix}"

TEST_SIZE = 15 if TEST_MODE else None

if TEST_MODE:
    print("\n🧪 TEST MODE ENABLED")
    print(f"   Will process first {TEST_SIZE} papers\n")
else:
    print("\n🚀 PRODUCTION MODE")
    print("   Will process all papers in validation sample\n")

# Paths (relative to validation_spacy_v_BERT/) - use _test suffix in TEST_MODE
VALIDATION_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = VALIDATION_ROOT.parent

output_suffix = f"_{SESSION_ID}" if SESSION_ID else ("_test" if TEST_MODE else "")
SAMPLE_FILE = VALIDATION_ROOT / f"results/validation/sample/validation_sample_with_abstracts{output_suffix}.csv"
METADATA_FILE = VALIDATION_ROOT / f"results/validation/metadata/validation_metadata_epmc{output_suffix}.csv"
OUTPUT_DIR = VALIDATION_ROOT / "results/validation/classification"
LOG_FILE = VALIDATION_ROOT / "logs/03b_run_pycaret_classification.log"

# Model paths
MODEL_TEST_TRUE = PROJECT_ROOT / "pycaret_models/test_mode_true/pycaret_metadata_classifier_v1"
MODEL_TEST_FALSE = PROJECT_ROOT / "pycaret_models/test_mode_false/pycaret_metadata_classifier_v1"

# ============================================================================
# LOGGING SETUP
# ============================================================================

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# FEATURE ENGINEERING FUNCTION
# ============================================================================

def engineer_features_for_model(df, model):
    """
    Engineer features to match EXACTLY what the model expects.
    Uses model.feature_names_in_ to get the expected features.

    Args:
        df: DataFrame with paper data and metadata
        model: Loaded PyCaret model

    Returns:
        DataFrame with engineered features in correct order
    """
    expected_features = list(model.feature_names_in_)
    logger.info(f"🔧 Engineering {len(expected_features)} features to match model expectations...")

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
    def safe_parse_list(x):
        """Safely parse string list to actual list using json.loads()"""
        if isinstance(x, str) and x.startswith('['):
            try:
                return json.loads(x)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse list: {x[:50]}...")
                return []
        return []

    mesh_col = 'meshTerms' if 'meshTerms' in df.columns else 'meshTerms_meta'
    df['meshTerms_list'] = df[mesh_col].fillna('[]').apply(safe_parse_list)

    pubtype_col = 'pubType' if 'pubType' in df.columns else 'pubType_meta'
    df['pubType_list'] = df[pubtype_col].fillna('[]').apply(safe_parse_list)

    keywords_col = 'keywords' if 'keywords' in df.columns else 'keywords_meta'
    df['keywords_list'] = df[keywords_col].fillna('[]').apply(safe_parse_list)

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
    current_year = datetime.now().year
    df['years_since_pub'] = current_year - df['pubYear']
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
            mesh_name = mesh_name.replace('_', ' ')

            # Check if this MeSH term appears in the paper (exact match, case-insensitive)
            # Use exact match to avoid false positives (e.g., "Humans" matching "Nonhumans")
            df[feat] = df['meshTerms_list'].apply(
                lambda x: 1 if any(mesh_name.lower() == term.lower().strip() for term in x) else 0
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

    logger.info(f"✓ Created {len(expected_features)} features matching model expectations")

    return X

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("SCRIPT 03b: PYCARET CLASSIFICATION")
    logger.info("=" * 70)

    start_time = datetime.now()

    # ------------------------------------------------------------------------
    # 1. Validate inputs
    # ------------------------------------------------------------------------
    logger.info("\n🔍 Validating inputs...")

    if not SAMPLE_FILE.exists():
        logger.error(f"❌ Sample file not found: {SAMPLE_FILE}")
        logger.error("Please run script 02 first: python scripts/02_fetch_abstracts.py")
        return 1

    if not METADATA_FILE.exists():
        logger.error(f"❌ Metadata file not found: {METADATA_FILE}")
        logger.error("Expected V5.1 EPMC query results for feature engineering")
        return 1

    # Check which models exist
    models_available = []
    if MODEL_TEST_TRUE.with_suffix('.pkl').exists():
        models_available.append(('test_mode_true', MODEL_TEST_TRUE))
        logger.info(f"✓ Model (TEST_MODE=True): {MODEL_TEST_TRUE}.pkl")
    else:
        logger.warning(f"⚠️  Model (TEST_MODE=True) not found: {MODEL_TEST_TRUE}.pkl")

    if MODEL_TEST_FALSE.with_suffix('.pkl').exists():
        models_available.append(('test_mode_false', MODEL_TEST_FALSE))
        logger.info(f"✓ Model (TEST_MODE=False): {MODEL_TEST_FALSE}.pkl")
    else:
        logger.warning(f"⚠️  Model (TEST_MODE=False) not found: {MODEL_TEST_FALSE}.pkl")

    if len(models_available) == 0:
        logger.error("❌ No PyCaret models found!")
        logger.error("Expected models at:")
        logger.error(f"  - {MODEL_TEST_TRUE}.pkl")
        logger.error(f"  - {MODEL_TEST_FALSE}.pkl")
        return 1

    logger.info(f"\n✓ Found {len(models_available)} model(s) to run")

    # ------------------------------------------------------------------------
    # 2. Load validation sample
    # ------------------------------------------------------------------------
    logger.info("\n📚 Loading validation sample...")
    df_sample = pd.read_csv(SAMPLE_FILE)
    logger.info(f"✓ Loaded {len(df_sample)} papers")

    # Apply TEST_MODE if enabled
    if TEST_MODE:
        logger.info(f"🧪 TEST_MODE: Using first {TEST_SIZE} papers")
        df_sample = df_sample.head(TEST_SIZE)
        logger.info(f"✓ Test sample size: {len(df_sample)} papers")

    # ------------------------------------------------------------------------
    # 3. Load metadata for feature engineering
    # ------------------------------------------------------------------------
    logger.info("\n📊 Loading metadata for feature engineering...")
    df_metadata = pd.read_csv(METADATA_FILE, low_memory=False)
    logger.info(f"✓ Loaded {len(df_metadata):,} papers from fresh EPMC validation metadata")

    # ------------------------------------------------------------------------
    # 4. Standardize on PMID column and merge
    # ------------------------------------------------------------------------
    logger.info("\n🔗 Merging sample with metadata on PMID...")

    # CRITICAL: Ensure we use actual PubMed IDs, NOT internal publication_id
    # The sample file has both 'publication_id' (internal DB ID) and 'pubmed_id' (actual PMID)
    # We MUST use 'pubmed_id' to match with EPMC metadata

    # Find PMID column in sample (explicitly exclude non-PMID columns)
    sample_pmid_col = None
    for col in ['pubmed_id', 'pmid', 'PMID']:  # Only accept actual PMID column names
        if col in df_sample.columns:
            sample_pmid_col = col
            logger.info(f"  Using sample PMID column: '{col}'")
            break

    if not sample_pmid_col:
        logger.error(f"❌ No PMID column found in sample!")
        logger.error(f"   Available columns: {list(df_sample.columns)}")
        logger.error(f"   Expected one of: pubmed_id, pmid, PMID")
        return 1

    # Find PMID column in metadata
    metadata_pmid_col = None
    for col in ['pmid', 'PMID', 'id']:  # EPMC uses 'id' or 'pmid'
        if col in df_metadata.columns:
            metadata_pmid_col = col
            logger.info(f"  Using metadata PMID column: '{col}'")
            break

    if not metadata_pmid_col:
        logger.error(f"❌ No PMID column found in metadata!")
        logger.error(f"   Available columns: {list(df_metadata.columns)}")
        return 1

    # Standardize both to 'pmid' column for merge
    df_sample['pmid'] = df_sample[sample_pmid_col].astype(str).str.replace('.0', '', regex=False)
    df_metadata['pmid'] = df_metadata[metadata_pmid_col].astype(str).str.replace('.0', '', regex=False)

    logger.info(f"  Sample PMIDs: {df_sample['pmid'].nunique()} unique values")
    logger.info(f"  Metadata PMIDs: {df_metadata['pmid'].nunique()} unique values")

    # Check PMID overlap before merge (early warning system)
    sample_pmids = set(df_sample['pmid'].unique())
    metadata_pmids = set(df_metadata['pmid'].unique())
    overlap = sample_pmids & metadata_pmids
    overlap_rate = len(overlap) / len(sample_pmids) * 100 if len(sample_pmids) > 0 else 0

    logger.info(f"  PMID overlap: {len(overlap)}/{len(sample_pmids)} ({overlap_rate:.1f}%)")

    if overlap_rate < 95:
        logger.warning(f"⚠️  Only {overlap_rate:.1f}% of sample PMIDs found in metadata")
        missing_pmids = sample_pmids - metadata_pmids
        logger.warning(f"   Missing {len(missing_pmids)} PMIDs, showing first 5:")
        for pmid in list(missing_pmids)[:5]:
            logger.warning(f"     - {pmid}")

    # Merge on standardized PMID column
    df = df_sample.merge(
        df_metadata,
        on='pmid',
        how='left',
        suffixes=('_test', '_meta')
    )

    # Validate merge success
    merged_count = len(df)
    papers_with_metadata = df['title_meta'].notna().sum() if 'title_meta' in df.columns else df['title'].notna().sum()
    merge_rate = (papers_with_metadata / merged_count * 100) if merged_count > 0 else 0

    logger.info(f"✓ Merged: {merged_count} papers")
    logger.info(f"  Papers with metadata: {papers_with_metadata}/{merged_count} ({merge_rate:.1f}%)")

    # ------------------------------------------------------------------------
    # 4b. Normalize fresh EPMC column names to match V5.1 schema
    # ------------------------------------------------------------------------
    logger.info("\n🔄 Normalizing fresh EPMC metadata columns...")

    # Debug: Show what columns we have after merge
    logger.info(f"  Columns after merge: {len(df.columns)} total")
    epmc_cols = [col for col in df.columns if any(x in col for x in ['abstractText', 'meshHeading', 'pubType', 'keyword', 'journal'])]
    logger.info(f"  EPMC-related columns found: {epmc_cols}")

    # Functions to extract nested EPMC data structures to V5.1 format
    def extract_mesh_terms(mesh_heading_list):
        """Extract mesh term names from nested meshHeadingList dict

        CRITICAL FIX: Use ast.literal_eval() instead of json.loads() because
        EPMC data uses Python literal syntax (single quotes) not JSON (double quotes)
        """
        if pd.isna(mesh_heading_list):
            return '[]'

        try:
            if isinstance(mesh_heading_list, str):
                data = ast.literal_eval(mesh_heading_list)  # FIXED: was json.loads()
            elif isinstance(mesh_heading_list, dict):
                data = mesh_heading_list
            else:
                return '[]'

            # Extract descriptorName from each meshHeading
            mesh_headings = data.get('meshHeading', []) if isinstance(data, dict) else []
            terms = [mh.get('descriptorName', '') for mh in mesh_headings if isinstance(mh, dict)]
            return json.dumps(terms)
        except:
            return '[]'

    def extract_keywords(keyword_list):
        """Extract keyword names from nested keywordList dict

        CRITICAL FIX: Use ast.literal_eval() instead of json.loads()
        """
        if pd.isna(keyword_list):
            return '[]'

        try:
            if isinstance(keyword_list, str):
                data = ast.literal_eval(keyword_list)  # FIXED: was json.loads()
            elif isinstance(keyword_list, dict):
                data = keyword_list
            else:
                return '[]'

            # Extract keywords from list
            keywords = data.get('keyword', []) if isinstance(data, dict) else []
            return json.dumps(keywords)
        except:
            return '[]'

    def extract_pub_types(pub_type_list):
        """Extract publication type names from nested pubTypeList dict

        CRITICAL FIX: Use ast.literal_eval() instead of json.loads()
        """
        if pd.isna(pub_type_list):
            return '[]'

        try:
            if isinstance(pub_type_list, str):
                data = ast.literal_eval(pub_type_list)  # FIXED: was json.loads()
            elif isinstance(pub_type_list, dict):
                data = pub_type_list
            else:
                return '[]'

            # Extract values from pubType list
            pub_types = data.get('pubType', []) if isinstance(data, dict) else []
            return json.dumps(pub_types)
        except:
            return '[]'

    # Map and transform fresh EPMC columns to V5.1 format
    if 'abstractText' in df.columns:
        df['abstract'] = df['abstractText']
        logger.info(f"  ✓ Mapped abstractText → abstract")

    if 'meshHeadingList' in df.columns:
        df['meshTerms'] = df['meshHeadingList'].apply(extract_mesh_terms)
        logger.info(f"  ✓ Extracted meshTerms from meshHeadingList")

    if 'pubTypeList' in df.columns:
        df['pubType'] = df['pubTypeList'].apply(extract_pub_types)
        logger.info(f"  ✓ Extracted pubType from pubTypeList")

    if 'keywordList' in df.columns:
        df['keywords'] = df['keywordList'].apply(extract_keywords)
        logger.info(f"  ✓ Extracted keywords from keywordList")

    # Extract journalTitle and journalISSN from nested journalInfo dict
    journal_info_col = 'journalInfo_meta' if 'journalInfo_meta' in df.columns else ('journalInfo' if 'journalInfo' in df.columns else None)
    if journal_info_col:
        def extract_journal_fields(journal_info):
            """Extract title and ISSN from journalInfo dict

            CRITICAL FIX: Use ast.literal_eval() instead of json.loads()
            """
            if pd.isna(journal_info):
                return pd.Series({'journalTitle': None, 'journalISSN': None})

            try:
                if isinstance(journal_info, str):
                    info = ast.literal_eval(journal_info)  # FIXED: was json.loads()
                elif isinstance(journal_info, dict):
                    info = journal_info
                else:
                    return pd.Series({'journalTitle': None, 'journalISSN': None})

                journal_dict = info.get('journal', {}) if isinstance(info, dict) else {}
                return pd.Series({
                    'journalTitle': journal_dict.get('title'),
                    'journalISSN': journal_dict.get('issn')
                })
            except:
                return pd.Series({'journalTitle': None, 'journalISSN': None})

        journal_fields = df[journal_info_col].apply(extract_journal_fields)
        df['journalTitle'] = journal_fields['journalTitle']
        df['journalISSN'] = journal_fields['journalISSN']
        logger.info(f"  ✓ Extracted journalTitle and journalISSN from {journal_info_col}")

    logger.info(f"✓ Column normalization complete")

    # Check for missing metadata
    title_col = 'title_meta' if 'title_meta' in df.columns else 'title'
    missing_metadata = df[title_col].isna().sum()
    if missing_metadata > 0:
        logger.warning(f"⚠️  Warning: {missing_metadata} papers missing metadata")
        logger.warning("   These papers will have limited features (may affect predictions)")

    # ------------------------------------------------------------------------
    # 5. Load PyCaret models and run predictions
    # ------------------------------------------------------------------------
    from pycaret.classification import load_model, predict_model

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results_summary = []

    for model_name, model_path in models_available:
        logger.info(f"\n{'=' * 70}")
        logger.info(f"MODEL: {model_name}")
        logger.info(f"{'=' * 70}")

        # Load model
        logger.info(f"🤖 Loading model from {model_path}...")
        model = load_model(str(model_path))
        n_features = len(model.feature_names_in_)
        logger.info(f"✓ Model loaded ({n_features} features)")

        # Engineer features
        X = engineer_features_for_model(df, model)

        # Make predictions
        logger.info(f"\n🔮 Running predictions with {model_name}...")
        predictions = predict_model(model, data=X)

        # Create results dataframe
        # Use publication_id if available (internal ID), otherwise use PMID
        id_col = 'publication_id' if 'publication_id' in df.columns else sample_pmid_col
        title_col = 'title_test' if 'title_test' in df.columns else 'title'

        df_results = pd.DataFrame({
            'id': df[id_col].values,
            'pmid': df['pmid'].values,
            'title': df[title_col].values,
            'predicted_label': predictions['prediction_label'].values,
            'prediction_score': predictions['prediction_score'].values
        })

        # Calculate summary statistics
        total = len(df_results)
        predicted_positive = (df_results['predicted_label'] == 1).sum()

        precision_score = df_results[df_results['predicted_label'] == 1]['prediction_score'].mean() if predicted_positive > 0 else 0

        logger.info(f"\n📊 Results for {model_name}:")
        logger.info(f"   Total papers:           {total}")
        logger.info(f"   Predicted positive:     {predicted_positive} ({100*predicted_positive/total:.1f}%)")
        logger.info(f"   Predicted negative:     {total - predicted_positive} ({100*(total-predicted_positive)/total:.1f}%)")
        logger.info(f"   Avg confidence (pos):   {precision_score:.3f}")

        # Save results
        output_file = OUTPUT_DIR / f"pycaret_{model_name}_results{output_suffix}.csv"
        df_results.to_csv(output_file, index=False)
        logger.info(f"\n✓ Saved to: {output_file}")
        logger.info(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")

        # Store summary
        results_summary.append({
            'model': model_name,
            'n_features': n_features,
            'total_papers': total,
            'predicted_positive': predicted_positive,
            'predicted_negative': total - predicted_positive,
            'output_file': str(output_file)
        })

    # ------------------------------------------------------------------------
    # 6. Final summary
    # ------------------------------------------------------------------------
    logger.info(f"\n{'=' * 70}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'=' * 70}")

    for summary in results_summary:
        logger.info(f"\n{summary['model'].upper()}:")
        logger.info(f"  Features: {summary['n_features']}")
        logger.info(f"  Predictions: {summary['predicted_positive']} positive / {summary['predicted_negative']} negative")
        logger.info(f"  Output: {Path(summary['output_file']).name}")

    # ------------------------------------------------------------------------
    # 7. Final report
    # ------------------------------------------------------------------------
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ SCRIPT 03b COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Log saved to: {LOG_FILE}")
    logger.info(f"\nNext step: Compare all classification results")
    logger.info(f"  python scripts/03c_compare_classifications.py")
    logger.info(f"{'=' * 70}")

    return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
