#!/usr/bin/env python3
"""
Feature engineering pipeline for enhanced metadata
Transforms raw metadata into ML-ready features for multi-task learning

Purpose: Convert raw PMC metadata into engineered features for Option 2 (Multi-Task Learning)
Authors: Claude Code
Date: 2025-10-30

This script transforms the enhanced metadata CSV into ML-ready features by:
1. Engineering numerical features (log citations, years since publication)
2. Processing boolean flags (8 dimensions)
3. One-hot encoding publication types
4. TF-IDF + SVD dimensionality reduction for MeSH terms
5. Optional TF-IDF + SVD for keywords
6. Handling missing values with indicators and imputation

Usage:
    python src/prepare_metadata_features.py \
        --input data/metadata/pmc_metadata_enhanced_full.csv \
        --output data/metadata/features_engineered.csv \
        --mesh-components 7 \
        --keyword-components 5
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

import numpy as np
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler

from inventory_utils.custom_classes import CustomHelpFormatter


# ---------------------------------------------------------------------------
class Args(NamedTuple):
    """Command-line arguments"""
    input: str
    output: str
    mesh_components: int
    keyword_components: int
    current_year: int
    min_df: int
    max_features_mesh: int
    max_features_kw: int


# ---------------------------------------------------------------------------
def get_args() -> Args:
    """Parse command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Transform raw metadata into ML-ready features',
        formatter_class=CustomHelpFormatter)

    parser.add_argument(
        '--input',
        metavar='FILE',
        type=str,
        required=True,
        help='Input CSV file with enhanced metadata')

    parser.add_argument(
        '--output',
        metavar='FILE',
        type=str,
        required=True,
        help='Output CSV file for engineered features')

    parser.add_argument(
        '--mesh-components',
        metavar='N',
        type=int,
        default=7,
        help='Number of SVD components for MeSH terms (default: 7)')

    parser.add_argument(
        '--keyword-components',
        metavar='N',
        type=int,
        default=5,
        help='Number of SVD components for keywords (default: 5)')

    parser.add_argument(
        '--current-year',
        metavar='YEAR',
        type=int,
        default=2025,
        help='Current year for years_since_pub calculation (default: 2025)')

    parser.add_argument(
        '--min-df',
        metavar='N',
        type=int,
        default=2,
        help='Minimum document frequency for TF-IDF (default: 2)')

    parser.add_argument(
        '--max-features-mesh',
        metavar='N',
        type=int,
        default=500,
        help='Maximum features for MeSH TF-IDF (default: 500)')

    parser.add_argument(
        '--max-features-kw',
        metavar='N',
        type=int,
        default=200,
        help='Maximum features for keyword TF-IDF (default: 200)')

    args = parser.parse_args()

    return Args(
        input=args.input,
        output=args.output,
        mesh_components=args.mesh_components,
        keyword_components=args.keyword_components,
        current_year=args.current_year,
        min_df=args.min_df,
        max_features_mesh=args.max_features_mesh,
        max_features_kw=args.max_features_kw
    )


# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Setup logging configuration"""

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


# ---------------------------------------------------------------------------
class MetadataFeatureEngineer:
    """Transform raw metadata into ML features"""

    def __init__(
        self,
        mesh_components: int = 7,
        keyword_components: int = 5,
        current_year: int = 2025,
        min_df: int = 2,
        max_features_mesh: int = 500,
        max_features_kw: int = 200,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize feature engineer

        Args:
            mesh_components: Number of SVD components for MeSH terms
            keyword_components: Number of SVD components for keywords
            current_year: Current year for calculating years since publication
            min_df: Minimum document frequency for TF-IDF
            max_features_mesh: Maximum features for MeSH TF-IDF
            max_features_kw: Maximum features for keyword TF-IDF
            logger: Logger instance
        """
        self.mesh_components = mesh_components
        self.keyword_components = keyword_components
        self.current_year = current_year
        self.min_df = min_df
        self.max_features_mesh = max_features_mesh
        self.max_features_kw = max_features_kw
        self.logger = logger or logging.getLogger(__name__)

        # Initialize transformers (will be fit during transform)
        self.scaler = StandardScaler()
        self.mesh_vectorizer = None
        self.mesh_svd = None
        self.keyword_vectorizer = None
        self.keyword_svd = None

        # Track feature statistics
        self.feature_stats = {}


    def parse_json_field(self, field_series: pd.Series, field_name: str) -> pd.Series:
        """
        Safely parse JSON string fields into lists

        Args:
            field_series: Pandas series containing JSON strings
            field_name: Name of field for logging

        Returns:
            Series with parsed lists or empty lists for invalid entries
        """
        def safe_parse(value):
            if pd.isna(value):
                return []
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    # Filter out None values and convert to strings
                    cleaned = [str(item) for item in parsed if item is not None]
                    return cleaned
                return []
            except (json.JSONDecodeError, TypeError):
                return []

        parsed = field_series.apply(safe_parse)

        valid_count = sum(len(x) > 0 for x in parsed)
        self.logger.info(
            f"Parsed {field_name}: {valid_count}/{len(parsed)} "
            f"({100*valid_count/len(parsed):.1f}%) have values"
        )

        return parsed


    def transform_numerical(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform numerical features: citations and publication year

        Creates:
        - log_citations: log(citedByCount + 1)
        - years_since_pub: current_year - pubYear
        - Both are z-score normalized

        Args:
            df: Input dataframe

        Returns:
            Dataframe with added numerical features
        """
        self.logger.info("Transforming numerical features...")

        df_copy = df.copy()

        # Log-transform citations
        df_copy['log_citations_raw'] = np.log1p(df_copy['citedByCount'])

        # Years since publication
        df_copy['years_since_pub_raw'] = self.current_year - df_copy['pubYear']

        # Handle any negative years (future publications)
        df_copy['years_since_pub_raw'] = df_copy['years_since_pub_raw'].clip(lower=0)

        # Z-score normalization
        numerical_cols = ['log_citations_raw', 'years_since_pub_raw']
        normalized = self.scaler.fit_transform(df_copy[numerical_cols])

        df_copy['log_citations'] = normalized[:, 0]
        df_copy['years_since_pub'] = normalized[:, 1]

        # Store statistics
        self.feature_stats['log_citations'] = {
            'mean': float(self.scaler.mean_[0]),
            'std': float(np.sqrt(self.scaler.var_[0])),
            'min': float(df_copy['log_citations'].min()),
            'max': float(df_copy['log_citations'].max())
        }

        self.feature_stats['years_since_pub'] = {
            'mean': float(self.scaler.mean_[1]),
            'std': float(np.sqrt(self.scaler.var_[1])),
            'min': float(df_copy['years_since_pub'].min()),
            'max': float(df_copy['years_since_pub'].max())
        }

        self.logger.info(
            f"  log_citations: mean={self.scaler.mean_[0]:.3f}, "
            f"std={np.sqrt(self.scaler.var_[0]):.3f}"
        )
        self.logger.info(
            f"  years_since_pub: mean={self.scaler.mean_[1]:.3f}, "
            f"std={np.sqrt(self.scaler.var_[1]):.3f}"
        )

        # Drop raw columns
        df_copy = df_copy.drop(columns=['log_citations_raw', 'years_since_pub_raw'])

        return df_copy


    def transform_boolean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform boolean flags to 0/1 encoding

        Processes 8 boolean fields:
        - hasDbCrossReferences (highest priority)
        - hasData, hasSuppl, isOpenAccess
        - inPMC, inEPMC, hasPDF, hasBook

        Missing values are treated as False (0)

        Args:
            df: Input dataframe

        Returns:
            Dataframe with boolean features as 0/1
        """
        self.logger.info("Transforming boolean features...")

        df_copy = df.copy()

        boolean_cols = [
            'hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess',
            'inPMC', 'inEPMC', 'hasPDF', 'hasBook'
        ]

        for col in boolean_cols:
            # Convert Y/N to 1/0, treating missing as 0
            df_copy[col] = (df_copy[col] == 'Y').astype(int)

            positive_count = df_copy[col].sum()
            positive_pct = 100 * positive_count / len(df_copy)

            self.logger.info(f"  {col}: {positive_count} positive ({positive_pct:.1f}%)")

            self.feature_stats[col] = {
                'positive_count': int(positive_count),
                'positive_pct': float(positive_pct)
            }

        return df_copy


    def transform_pubtype(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        One-hot encode publication types

        Creates binary indicators for:
        - is_research_article
        - is_review_article
        - Other types are not separately encoded

        Args:
            df: Input dataframe

        Returns:
            Dataframe with publication type features
        """
        self.logger.info("Transforming publication type...")

        df_copy = df.copy()

        # Parse pubType JSON
        pubtypes_parsed = self.parse_json_field(df_copy['pubType'], 'pubType')

        # Convert to lowercase for case-insensitive matching
        pubtypes_lower = pubtypes_parsed.apply(
            lambda x: [item.lower() for item in x] if x else []
        )

        # Research article indicators
        research_keywords = ['research-article', 'research', 'original research', 'article']
        df_copy['is_research_article'] = pubtypes_lower.apply(
            lambda x: int(any(kw in x for kw in research_keywords))
        )

        # Review article indicators
        review_keywords = ['review-article', 'review', 'systematic review']
        df_copy['is_review_article'] = pubtypes_lower.apply(
            lambda x: int(any(kw in x for kw in review_keywords))
        )

        research_count = df_copy['is_research_article'].sum()
        review_count = df_copy['is_review_article'].sum()

        self.logger.info(f"  Research articles: {research_count} ({100*research_count/len(df_copy):.1f}%)")
        self.logger.info(f"  Review articles: {review_count} ({100*review_count/len(df_copy):.1f}%)")

        self.feature_stats['is_research_article'] = {
            'count': int(research_count),
            'pct': float(100 * research_count / len(df_copy))
        }
        self.feature_stats['is_review_article'] = {
            'count': int(review_count),
            'pct': float(100 * review_count / len(df_copy))
        }

        return df_copy


    def transform_mesh(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        TF-IDF + SVD dimensionality reduction for MeSH terms

        Process:
        1. Parse JSON meshTerms field
        2. Join terms into space-separated strings
        3. TF-IDF vectorization (max 500 features)
        4. SVD reduction to n_components dimensions
        5. Create missing indicator

        Args:
            df: Input dataframe

        Returns:
            Dataframe with MeSH TF-IDF features
        """
        self.logger.info(f"Transforming MeSH terms (SVD to {self.mesh_components} dims)...")

        df_copy = df.copy()

        # Parse MeSH terms
        mesh_parsed = self.parse_json_field(df_copy['meshTerms'], 'meshTerms')

        # Create missing indicator
        df_copy['meshTerms_missing'] = (mesh_parsed.apply(len) == 0).astype(int)
        missing_count = df_copy['meshTerms_missing'].sum()
        self.logger.info(f"  Missing MeSH terms: {missing_count} ({100*missing_count/len(df_copy):.1f}%)")

        # Join terms into strings for TF-IDF
        mesh_strings = mesh_parsed.apply(lambda x: ' '.join(x) if x else '')

        # Replace empty strings with placeholder for TF-IDF
        mesh_strings = mesh_strings.replace('', 'NO_MESH_TERMS')

        # TF-IDF vectorization
        self.mesh_vectorizer = TfidfVectorizer(
            max_features=self.max_features_mesh,
            min_df=self.min_df,
            lowercase=True,
            ngram_range=(1, 1)
        )

        try:
            mesh_tfidf = self.mesh_vectorizer.fit_transform(mesh_strings)
            self.logger.info(f"  TF-IDF shape: {mesh_tfidf.shape}")

            # SVD dimensionality reduction
            # Use min of requested components and available features
            n_components = min(self.mesh_components, mesh_tfidf.shape[1])

            if n_components < self.mesh_components:
                self.logger.warning(
                    f"  Reducing mesh_components from {self.mesh_components} to {n_components} "
                    f"(limited by vocabulary size)"
                )

            self.mesh_svd = TruncatedSVD(n_components=n_components, random_state=42)
            mesh_reduced = self.mesh_svd.fit_transform(mesh_tfidf)

            # Add features to dataframe
            for i in range(n_components):
                col_name = f'mesh_tfidf_{i}'
                df_copy[col_name] = mesh_reduced[:, i]

                self.feature_stats[col_name] = {
                    'mean': float(mesh_reduced[:, i].mean()),
                    'std': float(mesh_reduced[:, i].std()),
                    'min': float(mesh_reduced[:, i].min()),
                    'max': float(mesh_reduced[:, i].max())
                }

            # Report explained variance
            explained_var = self.mesh_svd.explained_variance_ratio_
            cumulative_var = explained_var.cumsum()
            self.logger.info(
                f"  Explained variance: {explained_var.sum():.3f} "
                f"(cumulative: {cumulative_var[-1]:.3f})"
            )

            self.feature_stats['mesh_explained_variance'] = {
                'per_component': explained_var.tolist(),
                'cumulative': cumulative_var.tolist(),
                'total': float(explained_var.sum())
            }

        except Exception as e:
            self.logger.error(f"Error in MeSH TF-IDF: {e}")
            # Create zero-filled features as fallback
            for i in range(self.mesh_components):
                df_copy[f'mesh_tfidf_{i}'] = 0.0

        return df_copy


    def transform_keywords(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        TF-IDF + SVD dimensionality reduction for keywords

        Process:
        1. Parse JSON keywords field
        2. Join terms into space-separated strings
        3. TF-IDF vectorization (max 200 features)
        4. SVD reduction to n_components dimensions
        5. Create missing indicator

        Args:
            df: Input dataframe

        Returns:
            Dataframe with keyword TF-IDF features
        """
        self.logger.info(f"Transforming keywords (SVD to {self.keyword_components} dims)...")

        df_copy = df.copy()

        # Parse keywords
        kw_parsed = self.parse_json_field(df_copy['keywords'], 'keywords')

        # Create missing indicator
        df_copy['keywords_missing'] = (kw_parsed.apply(len) == 0).astype(int)
        missing_count = df_copy['keywords_missing'].sum()
        self.logger.info(f"  Missing keywords: {missing_count} ({100*missing_count/len(df_copy):.1f}%)")

        # Check if we have enough data
        non_missing = len(kw_parsed) - missing_count
        if non_missing < 100:
            self.logger.warning(
                f"  Only {non_missing} papers with keywords, skipping keyword features"
            )
            # Create zero-filled features
            for i in range(self.keyword_components):
                df_copy[f'keyword_tfidf_{i}'] = 0.0
            return df_copy

        # Join terms into strings for TF-IDF
        kw_strings = kw_parsed.apply(lambda x: ' '.join(x) if x else '')

        # Replace empty strings with placeholder
        kw_strings = kw_strings.replace('', 'NO_KEYWORDS')

        # TF-IDF vectorization
        self.keyword_vectorizer = TfidfVectorizer(
            max_features=self.max_features_kw,
            min_df=self.min_df,
            lowercase=True,
            ngram_range=(1, 1)
        )

        try:
            kw_tfidf = self.keyword_vectorizer.fit_transform(kw_strings)
            self.logger.info(f"  TF-IDF shape: {kw_tfidf.shape}")

            # SVD dimensionality reduction
            n_components = min(self.keyword_components, kw_tfidf.shape[1])

            if n_components < self.keyword_components:
                self.logger.warning(
                    f"  Reducing keyword_components from {self.keyword_components} to {n_components} "
                    f"(limited by vocabulary size)"
                )

            self.keyword_svd = TruncatedSVD(n_components=n_components, random_state=42)
            kw_reduced = self.keyword_svd.fit_transform(kw_tfidf)

            # Add features to dataframe
            for i in range(n_components):
                col_name = f'keyword_tfidf_{i}'
                df_copy[col_name] = kw_reduced[:, i]

                self.feature_stats[col_name] = {
                    'mean': float(kw_reduced[:, i].mean()),
                    'std': float(kw_reduced[:, i].std()),
                    'min': float(kw_reduced[:, i].min()),
                    'max': float(kw_reduced[:, i].max())
                }

            # Report explained variance
            explained_var = self.keyword_svd.explained_variance_ratio_
            cumulative_var = explained_var.cumsum()
            self.logger.info(
                f"  Explained variance: {explained_var.sum():.3f} "
                f"(cumulative: {cumulative_var[-1]:.3f})"
            )

            self.feature_stats['keyword_explained_variance'] = {
                'per_component': explained_var.tolist(),
                'cumulative': cumulative_var.tolist(),
                'total': float(explained_var.sum())
            }

        except Exception as e:
            self.logger.error(f"Error in keyword TF-IDF: {e}")
            # Create zero-filled features as fallback
            for i in range(self.keyword_components):
                df_copy[f'keyword_tfidf_{i}'] = 0.0

        return df_copy


    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Complete feature engineering pipeline

        Applies all transformations in sequence:
        1. Numerical features (citations, years)
        2. Boolean flags
        3. Publication type
        4. MeSH terms (TF-IDF + SVD)
        5. Keywords (TF-IDF + SVD)

        All original columns are preserved.

        Args:
            df: Input dataframe with raw metadata

        Returns:
            Dataframe with all engineered features
        """
        self.logger.info("=" * 70)
        self.logger.info("FEATURE ENGINEERING PIPELINE")
        self.logger.info("=" * 70)
        self.logger.info(f"Input shape: {df.shape}")

        # Apply transformations
        df_out = df.copy()
        df_out = self.transform_numerical(df_out)
        df_out = self.transform_boolean(df_out)
        df_out = self.transform_pubtype(df_out)
        df_out = self.transform_mesh(df_out)
        df_out = self.transform_keywords(df_out)

        self.logger.info("=" * 70)
        self.logger.info(f"Output shape: {df_out.shape}")
        self.logger.info(f"Added {df_out.shape[1] - df.shape[1]} new features")

        # Verify no NaN in engineered features
        engineered_cols = [col for col in df_out.columns if col not in df.columns]
        nan_counts = df_out[engineered_cols].isnull().sum()

        if nan_counts.sum() > 0:
            self.logger.warning(f"Found NaN values in engineered features:\n{nan_counts[nan_counts > 0]}")
        else:
            self.logger.info("✓ No NaN values in engineered features")

        return df_out


# ---------------------------------------------------------------------------
def validate_features(df: pd.DataFrame, original_cols: List[str]) -> Dict:
    """
    Generate validation statistics for engineered features

    Args:
        df: Dataframe with engineered features
        original_cols: List of original column names

    Returns:
        Dictionary with validation statistics
    """
    # Identify engineered features
    engineered_cols = [col for col in df.columns if col not in original_cols]

    validation = {
        'total_rows': len(df),
        'total_features': len(engineered_cols),
        'feature_names': engineered_cols,
        'timestamp': datetime.now().isoformat(),
        'feature_statistics': {}
    }

    # Calculate statistics for each engineered feature
    for col in engineered_cols:
        if df[col].dtype in ['int64', 'float64']:
            validation['feature_statistics'][col] = {
                'dtype': str(df[col].dtype),
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'median': float(df[col].median()),
                'nan_count': int(df[col].isnull().sum()),
                'unique_values': int(df[col].nunique())
            }
        else:
            validation['feature_statistics'][col] = {
                'dtype': str(df[col].dtype),
                'nan_count': int(df[col].isnull().sum()),
                'unique_values': int(df[col].nunique())
            }

    return validation


# ---------------------------------------------------------------------------
def main() -> None:
    """Main execution function"""

    # Parse arguments
    args = get_args()

    # Setup logging
    logger = setup_logging()

    logger.info("=" * 70)
    logger.info("METADATA FEATURE ENGINEERING")
    logger.info("=" * 70)
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"MeSH components: {args.mesh_components}")
    logger.info(f"Keyword components: {args.keyword_components}")

    # Check input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info("\nLoading data...")
    try:
        df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        original_cols = df.columns.tolist()
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)

    # Initialize feature engineer
    engineer = MetadataFeatureEngineer(
        mesh_components=args.mesh_components,
        keyword_components=args.keyword_components,
        current_year=args.current_year,
        min_df=args.min_df,
        max_features_mesh=args.max_features_mesh,
        max_features_kw=args.max_features_kw,
        logger=logger
    )

    # Transform features
    logger.info("\nTransforming features...")
    try:
        df_engineered = engineer.fit_transform(df)
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Validate features
    logger.info("\nValidating features...")
    validation = validate_features(df_engineered, original_cols)

    # Combine with engineer's statistics
    validation['engineering_stats'] = engineer.feature_stats

    # Save outputs
    logger.info("\nSaving outputs...")

    # Save CSV
    df_engineered.to_csv(output_path, index=False)
    logger.info(f"✓ Saved CSV: {output_path}")

    # Save pickle for fast loading
    pkl_path = output_path.with_suffix('.pkl')
    df_engineered.to_pickle(pkl_path)
    logger.info(f"✓ Saved pickle: {pkl_path}")

    # Save validation JSON
    validation_path = output_path.parent / 'features_validation.json'
    with open(validation_path, 'w') as f:
        json.dump(validation, f, indent=2)
    logger.info(f"✓ Saved validation: {validation_path}")

    # Save transformers for future use
    transformers_path = output_path.parent / 'feature_transformers.pkl'
    transformers = {
        'scaler': engineer.scaler,
        'mesh_vectorizer': engineer.mesh_vectorizer,
        'mesh_svd': engineer.mesh_svd,
        'keyword_vectorizer': engineer.keyword_vectorizer,
        'keyword_svd': engineer.keyword_svd
    }
    with open(transformers_path, 'wb') as f:
        pickle.dump(transformers, f)
    logger.info(f"✓ Saved transformers: {transformers_path}")

    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("FEATURE ENGINEERING COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total papers: {len(df_engineered):,}")
    logger.info(f"Original features: {len(original_cols)}")
    logger.info(f"Engineered features: {len(validation['feature_names'])}")
    logger.info(f"Total features: {len(df_engineered.columns)}")

    # Feature breakdown
    tier1_features = [
        'log_citations', 'years_since_pub',
        'hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess',
        'inPMC', 'inEPMC', 'hasPDF', 'hasBook',
        'is_research_article', 'is_review_article'
    ]

    mesh_features = [col for col in df_engineered.columns if col.startswith('mesh_tfidf_')]
    kw_features = [col for col in df_engineered.columns if col.startswith('keyword_tfidf_')]
    missing_indicators = [col for col in df_engineered.columns if col.endswith('_missing')]

    logger.info(f"\nFeature breakdown:")
    logger.info(f"  Tier 1 (core): {len([c for c in tier1_features if c in df_engineered.columns])}")
    logger.info(f"  MeSH TF-IDF: {len(mesh_features)}")
    logger.info(f"  Keyword TF-IDF: {len(kw_features)}")
    logger.info(f"  Missing indicators: {len(missing_indicators)}")

    logger.info("\n✓ All outputs saved successfully")


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    main()
