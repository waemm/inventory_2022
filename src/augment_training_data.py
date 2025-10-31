#!/usr/bin/env python3
"""
Dataset Augmentation for Multi-Task Learning
Merges engineered metadata features with training datasets

This script augments classification and NER training datasets with metadata features
engineered from PubMed Central. It handles missing values through intelligent imputation
and maintains data integrity throughout the merge process.

Usage:
    python3 src/augment_training_data.py \
        --classif-data data/manual_classifications.csv \
        --ner-data data/manual_ner_extraction.csv \
        --features data/metadata/features_engineered.csv \
        --transformers data/metadata/feature_transformers.pkl \
        --output-dir data/augmented/

Example:
    >>> augmenter = DatasetAugmenter(features_df, transformers)
    >>> classif_augmented = augmenter.augment_dataset(classif_df, 'classification')
    >>> # Expected: Same row count, 38 new columns, no NaN in features
"""

import argparse
import json
import logging
import os
import pickle
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/augmented/augmentation.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


class DatasetAugmenter:
    """
    Augment training datasets with metadata features

    This class handles the complete augmentation pipeline:
    1. Merging training data with engineered features
    2. Imputing missing values for samples without metadata
    3. Validating data integrity
    4. Generating augmentation reports

    Attributes:
        features_df: DataFrame containing engineered metadata features
        transformers: Dictionary of fitted transformers for imputation
        imputation_values: Calculated median/mode values for imputation
        feature_columns: List of feature column names to add
    """

    # Expected feature column patterns
    METADATA_COLUMNS = [
        'title', 'abstract', 'publication_date', 'hasDbCrossReferences',
        'hasData', 'hasSuppl', 'isOpenAccess', 'inPMC', 'inEPMC',
        'hasPDF', 'hasBook', 'citedByCount', 'pubYear', 'pubType',
        'keywords', 'meshTerms', 'journalTitle', 'journalISSN',
        'authorAffiliations'
    ]

    ENGINEERED_COLUMNS = [
        'log_citations', 'years_since_pub', 'is_research_article',
        'is_review_article', 'meshTerms_missing', 'keywords_missing'
    ]

    def __init__(self, features_df: pd.DataFrame, transformers: dict):
        """
        Initialize the augmenter with features and transformers

        Args:
            features_df: DataFrame with engineered features (must have 'id' column)
            transformers: Dictionary containing fitted transformers
        """
        self.features_df = features_df
        self.transformers = transformers

        # Identify feature columns to merge (exclude 'id' and original text columns)
        self.feature_columns = self._identify_feature_columns()
        logger.info(f"Identified {len(self.feature_columns)} feature columns to merge")

        # Calculate imputation values from the feature dataset
        self.imputation_values = self._calculate_imputation_values()
        logger.info("Calculated imputation values for missing data")

    def _identify_feature_columns(self) -> List[str]:
        """
        Identify columns that should be added to training data

        Excludes 'id' and preserves only metadata/engineered features.
        Original text columns (title, abstract) won't be duplicated.

        Returns:
            List of feature column names
        """
        # Get all columns except 'id'
        all_cols = [col for col in self.features_df.columns if col != 'id']

        # For metadata, we exclude title and abstract as they exist in training data
        # Keep all other metadata and engineered features
        feature_cols = [col for col in all_cols if col not in ['title', 'abstract']]

        logger.debug(f"Feature columns: {feature_cols[:10]}... (showing first 10)")
        return feature_cols

    def _calculate_imputation_values(self) -> Dict[str, float]:
        """
        Calculate median/mode values for imputing missing metadata

        Uses the feature dataset statistics to fill missing values:
        - Numerical features: median
        - Boolean/categorical features: mode
        - TF-IDF features: 0.0 (zero vector)

        Returns:
            Dictionary mapping column names to imputation values
        """
        imputation_vals = {}

        for col in self.feature_columns:
            if col not in self.features_df.columns:
                logger.warning(f"Column {col} not found in features, will skip")
                continue

            col_data = self.features_df[col]

            # TF-IDF components: use 0.0 (neutral in reduced space)
            if 'tfidf_' in col or col.endswith(('_0', '_1', '_2', '_3', '_4', '_5', '_6')):
                imputation_vals[col] = 0.0

            # Text fields: use empty string
            elif col in ['authorAffiliations', 'keywords', 'meshTerms', 'journalTitle', 'journalISSN']:
                imputation_vals[col] = ''

            # Boolean and categorical features: use mode
            elif col_data.dtype == 'bool' or col_data.dtype == 'object':
                mode_val = col_data.mode()
                imputation_vals[col] = mode_val[0] if len(mode_val) > 0 else False

            # Numerical features: use median
            elif col_data.dtype in ['int64', 'float64']:
                imputation_vals[col] = col_data.median()

            else:
                # Default to median for unknown types
                logger.warning(f"Unknown dtype for {col}: {col_data.dtype}, using median")
                imputation_vals[col] = col_data.median()

        # Log sample imputation values
        sample_keys = list(imputation_vals.keys())[:5]
        for key in sample_keys:
            logger.debug(f"Imputation value for {key}: {imputation_vals[key]}")

        return imputation_vals

    def _detect_id_column(self, df: pd.DataFrame) -> str:
        """
        Detect the ID column name in training data

        Tries common variations: 'id', 'pmid', 'PMID', 'ID'
        Prefers 'id' if multiple exist.

        Args:
            df: Training DataFrame

        Returns:
            Name of the ID column

        Raises:
            ValueError: If no ID column is found
        """
        # Try common ID column names in order of preference
        id_candidates = ['id', 'pmid', 'PMID', 'ID', 'Id']

        found_columns = [col for col in id_candidates if col in df.columns]

        if not found_columns:
            # Check for any column containing 'id' case-insensitive
            id_like = [col for col in df.columns if 'id' in col.lower()]
            if id_like:
                logger.warning(f"No standard ID column found, using: {id_like[0]}")
                return id_like[0]

            raise ValueError(
                f"No ID column found in dataset. Tried: {id_candidates}\n"
                f"Available columns: {list(df.columns)}"
            )

        id_column = found_columns[0]
        if len(found_columns) > 1:
            logger.warning(
                f"Multiple ID columns found: {found_columns}. Using: {id_column}"
            )

        logger.info(f"Detected ID column: {id_column}")
        return id_column

    def augment_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Merge features with training data and handle missing values

        Process:
        1. Detect ID column in training data
        2. Left join with feature data (preserves all training samples)
        3. Impute missing values for samples without metadata
        4. Validate data integrity
        5. Return augmented dataset and statistics

        Args:
            df: Training DataFrame to augment
            dataset_name: Name for logging (e.g., 'classification', 'NER')

        Returns:
            Tuple of (augmented_df, validation_dict)
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Augmenting {dataset_name} dataset")
        logger.info(f"{'='*60}")

        original_rows = len(df)
        logger.info(f"Original dataset: {original_rows} rows, {len(df.columns)} columns")

        # Step 1: Detect ID column
        id_column = self._detect_id_column(df)

        # Step 2: Prepare features for merge (only selected columns + id)
        features_to_merge = self.features_df[['id'] + self.feature_columns].copy()

        # Step 2.5: Normalize IDs for merging
        # Both datasets may have mixed numeric and non-numeric IDs
        # Convert numeric IDs to int, keep non-numeric as-is
        def normalize_id(val):
            """Convert ID to normalized string format for merging"""
            if pd.isna(val):
                return None
            try:
                # Try to convert to int (handles both float and int)
                numeric_val = int(float(val))
                return str(numeric_val)
            except (ValueError, TypeError):
                # Non-numeric ID (e.g., 'PMC123', 'IND123')
                return str(val)

        # Create normalized ID columns for merging
        df = df.copy()
        df['_merge_id'] = df[id_column].apply(normalize_id)
        features_to_merge['_merge_id'] = features_to_merge['id'].apply(normalize_id)

        logger.info(f"Normalized IDs for merging: {df['_merge_id'].notna().sum()} training IDs, "
                   f"{features_to_merge['_merge_id'].notna().sum()} feature IDs")

        # Step 3: Merge with left join to preserve all training samples
        logger.info(f"Merging {len(self.feature_columns)} feature columns...")
        augmented_df = df.merge(
            features_to_merge,
            left_on='_merge_id',
            right_on='_merge_id',
            how='left',
            suffixes=('', '_features')
        )

        # Drop merge helper columns and duplicate 'id' column if created
        cols_to_drop = ['_merge_id']
        if 'id_features' in augmented_df.columns:
            cols_to_drop.append('id_features')

        augmented_df = augmented_df.drop(columns=cols_to_drop)

        # Verify row count preserved
        if len(augmented_df) != original_rows:
            raise ValueError(
                f"Row count changed after merge! "
                f"Original: {original_rows}, After merge: {len(augmented_df)}"
            )

        logger.info(f"✓ Merge complete: {len(augmented_df)} rows preserved")

        # Step 4: Calculate feature coverage before imputation
        samples_with_metadata = augmented_df[self.feature_columns].notna().all(axis=1).sum()
        coverage_pct = (samples_with_metadata / len(augmented_df)) * 100
        logger.info(f"Feature coverage: {samples_with_metadata}/{len(augmented_df)} "
                   f"({coverage_pct:.1f}%) samples have complete metadata")

        # Step 5: Impute missing values
        missing_counts_before = augmented_df[self.feature_columns].isna().sum()
        total_missing = missing_counts_before.sum()

        if total_missing > 0:
            logger.warning(f"Imputing {total_missing} missing values across features...")

            for col in self.feature_columns:
                if col in augmented_df.columns and col in self.imputation_values:
                    missing_count = augmented_df[col].isna().sum()
                    if missing_count > 0:
                        impute_val = self.imputation_values[col]
                        augmented_df[col] = augmented_df[col].fillna(impute_val)
                        logger.debug(f"  {col}: filled {missing_count} values with {impute_val}")

        # Step 6: Validate no unexpected NaN values remain in feature columns
        missing_counts_after = augmented_df[self.feature_columns].isna().sum()
        total_missing_after = missing_counts_after.sum()

        if total_missing_after > 0:
            logger.error(f"WARNING: {total_missing_after} NaN values remain after imputation!")
            problem_cols = missing_counts_after[missing_counts_after > 0]
            logger.error(f"Columns with NaN: {problem_cols.to_dict()}")
        else:
            logger.info("✓ No NaN values in feature columns after imputation")

        # Step 7: Generate validation statistics
        validation_stats = self.validate_augmented(df, augmented_df, dataset_name)

        logger.info(f"\nAugmentation complete for {dataset_name}:")
        logger.info(f"  - Rows: {len(augmented_df)}")
        logger.info(f"  - Columns: {len(df.columns)} → {len(augmented_df.columns)} "
                   f"(+{len(augmented_df.columns) - len(df.columns)} features)")
        logger.info(f"  - Coverage: {coverage_pct:.1f}%")
        logger.info(f"  - Missing imputed: {total_missing}")

        return augmented_df, validation_stats

    def validate_augmented(
        self,
        original: pd.DataFrame,
        augmented: pd.DataFrame,
        dataset_name: str
    ) -> Dict:
        """
        Validate augmented dataset integrity

        Checks:
        - Row count preservation
        - Column additions
        - Missing value counts
        - Feature coverage statistics
        - Data type consistency

        Args:
            original: Original training DataFrame
            augmented: Augmented training DataFrame
            dataset_name: Name for reporting

        Returns:
            Dictionary of validation statistics
        """
        validation = {
            'dataset_name': dataset_name,
            'original_rows': len(original),
            'augmented_rows': len(augmented),
            'original_columns': len(original.columns),
            'augmented_columns': len(augmented.columns),
            'features_added': len(augmented.columns) - len(original.columns),
            'row_count_preserved': len(original) == len(augmented),
        }

        # Feature coverage analysis
        if len(self.feature_columns) > 0:
            feature_data = augmented[self.feature_columns]
            samples_with_all_features = feature_data.notna().all(axis=1).sum()
            validation['samples_with_metadata'] = int(samples_with_all_features)
            validation['feature_coverage_percent'] = round(
                (samples_with_all_features / len(augmented)) * 100, 2
            )
        else:
            validation['samples_with_metadata'] = 0
            validation['feature_coverage_percent'] = 0.0

        # Missing value analysis
        missing_by_column = augmented[self.feature_columns].isna().sum()
        validation['missing_values_by_column'] = missing_by_column.to_dict()
        validation['total_missing_values'] = int(missing_by_column.sum())

        # Data type consistency check
        original_dtypes = {col: str(dtype) for col, dtype in original.dtypes.items()}
        augmented_original_dtypes = {
            col: str(augmented[col].dtype)
            for col in original.columns
            if col in augmented.columns
        }
        dtype_mismatches = {
            col: {'original': original_dtypes[col], 'augmented': augmented_original_dtypes[col]}
            for col in original.columns
            if col in augmented_original_dtypes and original_dtypes[col] != augmented_original_dtypes[col]
        }
        validation['dtype_mismatches'] = dtype_mismatches

        if dtype_mismatches:
            logger.warning(f"Data type mismatches detected: {dtype_mismatches}")

        return validation


def load_csv_with_encoding(filepath: Path, name: str) -> pd.DataFrame:
    """
    Load CSV file with automatic encoding detection

    Tries UTF-8 first, then falls back to latin-1 if needed.

    Args:
        filepath: Path to CSV file
        name: Name for logging

    Returns:
        Loaded DataFrame

    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If file cannot be loaded
    """
    if not filepath.exists():
        raise FileNotFoundError(f"{name} file not found: {filepath}")

    # Try UTF-8 first (standard encoding)
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        logger.info(f"✓ Loaded {len(df)} {name} samples (UTF-8 encoding)")
        return df
    except UnicodeDecodeError:
        logger.warning(f"UTF-8 decoding failed for {name}, trying latin-1...")
        try:
            df = pd.read_csv(filepath, encoding='latin-1')
            logger.info(f"✓ Loaded {len(df)} {name} samples (latin-1 encoding)")
            return df
        except Exception as e:
            logger.error(f"Failed to load {name} with latin-1: {e}")
            raise
    except Exception as e:
        logger.error(f"Failed to load {name}: {e}")
        raise


def load_pickle_file(filepath: Path) -> dict:
    """
    Safely load a pickle file

    Args:
        filepath: Path to pickle file

    Returns:
        Loaded object

    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If file cannot be unpickled
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Transformer file not found: {filepath}")

    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        logger.info(f"Loaded transformers from: {filepath}")
        return data
    except Exception as e:
        logger.error(f"Failed to load pickle file {filepath}: {e}")
        raise


def save_augmented_data(
    df: pd.DataFrame,
    output_path: Path,
    dataset_name: str
) -> None:
    """
    Save augmented dataset to CSV

    Args:
        df: Augmented DataFrame
        output_path: Output file path
        dataset_name: Name for logging
    """
    try:
        df.to_csv(output_path, index=False)
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"✓ Saved {dataset_name} data to: {output_path} "
                   f"({file_size_mb:.2f} MB)")
    except Exception as e:
        logger.error(f"Failed to save {dataset_name} data: {e}")
        raise


def generate_report(
    classif_stats: Dict,
    ner_stats: Dict,
    output_path: Path
) -> None:
    """
    Generate comprehensive augmentation report

    Args:
        classif_stats: Classification validation statistics
        ner_stats: NER validation statistics
        output_path: Output JSON file path
    """
    report = {
        'augmentation_summary': {
            'classification': classif_stats,
            'ner': ner_stats
        },
        'overall_statistics': {
            'total_training_samples': (
                classif_stats['original_rows'] + ner_stats['original_rows']
            ),
            'total_augmented_samples': (
                classif_stats['augmented_rows'] + ner_stats['augmented_rows']
            ),
            'features_added_per_sample': classif_stats['features_added'],
            'validation_passed': (
                classif_stats['row_count_preserved'] and
                ner_stats['row_count_preserved'] and
                classif_stats['total_missing_values'] == 0 and
                ner_stats['total_missing_values'] == 0
            )
        }
    }

    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"✓ Saved augmentation report to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        raise


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Augment training datasets with engineered metadata features',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Standard usage
    python3 src/augment_training_data.py

    # Custom paths
    python3 src/augment_training_data.py \\
        --classif-data data/custom_classifications.csv \\
        --ner-data data/custom_ner.csv \\
        --features data/metadata/features_engineered.csv \\
        --output-dir data/augmented/

    # Validation only (no files saved)
    python3 src/augment_training_data.py --validate-only

    # Verbose logging
    python3 src/augment_training_data.py --verbose
        """
    )

    parser.add_argument(
        '--classif-data',
        type=str,
        default='data/manual_classifications.csv',
        help='Path to classification training data CSV (default: data/manual_classifications.csv)'
    )

    parser.add_argument(
        '--ner-data',
        type=str,
        default='data/manual_ner_extraction.csv',
        help='Path to NER training data CSV (default: data/manual_ner_extraction.csv)'
    )

    parser.add_argument(
        '--features',
        type=str,
        default='data/metadata/features_engineered.csv',
        help='Path to engineered features CSV (default: data/metadata/features_engineered.csv)'
    )

    parser.add_argument(
        '--transformers',
        type=str,
        default='data/metadata/feature_transformers.pkl',
        help='Path to feature transformers pickle (default: data/metadata/feature_transformers.pkl)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/augmented/',
        help='Output directory for augmented datasets (default: data/augmented/)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG level) logging'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Run validation without saving files (dry run)'
    )

    args = parser.parse_args()

    # Adjust logging level if verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    logger.info("="*70)
    logger.info("Dataset Augmentation Pipeline")
    logger.info("="*70)

    # Convert paths to Path objects
    classif_path = Path(args.classif_data)
    ner_path = Path(args.ner_data)
    features_path = Path(args.features)
    transformers_path = Path(args.transformers)
    output_dir = Path(args.output_dir)

    # Validate input files exist
    logger.info("\nValidating input files...")
    for filepath, name in [
        (classif_path, "Classification data"),
        (ner_path, "NER data"),
        (features_path, "Engineered features"),
        (transformers_path, "Feature transformers")
    ]:
        if not filepath.exists():
            logger.error(f"{name} not found: {filepath}")
            sys.exit(1)
        logger.info(f"✓ {name}: {filepath}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"✓ Output directory: {output_dir}")

    try:
        # Load data
        logger.info("\n" + "="*70)
        logger.info("Loading data...")
        logger.info("="*70)

        classif_df = load_csv_with_encoding(classif_path, "classification")

        ner_df = load_csv_with_encoding(ner_path, "NER")

        features_df = load_csv_with_encoding(features_path, "engineered features")
        logger.info(f"  Features: {len(features_df)} papers × {len(features_df.columns)} columns")

        logger.info("Loading feature transformers...")
        transformers = load_pickle_file(transformers_path)
        logger.info(f"✓ Loaded {len(transformers)} transformers: {list(transformers.keys())}")

        # Initialize augmenter
        logger.info("\n" + "="*70)
        logger.info("Initializing augmenter...")
        logger.info("="*70)
        augmenter = DatasetAugmenter(features_df, transformers)

        # Augment classification dataset
        classif_augmented, classif_stats = augmenter.augment_dataset(
            classif_df,
            'classification'
        )

        # Augment NER dataset
        ner_augmented, ner_stats = augmenter.augment_dataset(
            ner_df,
            'NER'
        )

        # Save results (unless validate-only mode)
        if args.validate_only:
            logger.info("\n" + "="*70)
            logger.info("VALIDATE-ONLY MODE: Skipping file saves")
            logger.info("="*70)
        else:
            logger.info("\n" + "="*70)
            logger.info("Saving augmented datasets...")
            logger.info("="*70)

            classif_output = output_dir / 'classif_train_with_metadata.csv'
            save_augmented_data(classif_augmented, classif_output, 'classification')

            ner_output = output_dir / 'ner_train_with_metadata.csv'
            save_augmented_data(ner_augmented, ner_output, 'NER')

            # Generate report
            report_output = output_dir / 'augmentation_report.json'
            generate_report(classif_stats, ner_stats, report_output)

        # Print summary
        logger.info("\n" + "="*70)
        logger.info("AUGMENTATION SUMMARY")
        logger.info("="*70)
        logger.info(f"\nClassification Dataset:")
        logger.info(f"  Original rows:     {classif_stats['original_rows']}")
        logger.info(f"  Augmented rows:    {classif_stats['augmented_rows']}")
        logger.info(f"  Features added:    {classif_stats['features_added']}")
        logger.info(f"  Coverage:          {classif_stats['feature_coverage_percent']:.1f}%")
        logger.info(f"  Missing values:    {classif_stats['total_missing_values']}")

        logger.info(f"\nNER Dataset:")
        logger.info(f"  Original rows:     {ner_stats['original_rows']}")
        logger.info(f"  Augmented rows:    {ner_stats['augmented_rows']}")
        logger.info(f"  Features added:    {ner_stats['features_added']}")
        logger.info(f"  Coverage:          {ner_stats['feature_coverage_percent']:.1f}%")
        logger.info(f"  Missing values:    {ner_stats['total_missing_values']}")

        # Final validation check
        success = (
            classif_stats['row_count_preserved'] and
            ner_stats['row_count_preserved'] and
            classif_stats['total_missing_values'] == 0 and
            ner_stats['total_missing_values'] == 0 and
            classif_stats['features_added'] >= 20 and  # At least 20 features
            ner_stats['features_added'] >= 20 and
            classif_stats['feature_coverage_percent'] >= 80.0 and  # 80% coverage
            ner_stats['feature_coverage_percent'] >= 80.0
        )

        if success:
            logger.info("\n" + "="*70)
            logger.info("✓ AUGMENTATION COMPLETED SUCCESSFULLY")
            logger.info("="*70)
            logger.info("All validation criteria passed:")
            logger.info("  ✓ Row counts preserved")
            logger.info("  ✓ No missing values in features")
            logger.info("  ✓ Sufficient features added")
            logger.info("  ✓ Feature coverage ≥80%")
            return 0
        else:
            logger.warning("\n" + "="*70)
            logger.warning("⚠ AUGMENTATION COMPLETED WITH WARNINGS")
            logger.warning("="*70)
            if not (classif_stats['row_count_preserved'] and ner_stats['row_count_preserved']):
                logger.warning("  ⚠ Row count not preserved")
            if classif_stats['total_missing_values'] > 0 or ner_stats['total_missing_values'] > 0:
                logger.warning("  ⚠ Missing values remain in features")
            if classif_stats['features_added'] < 20 or ner_stats['features_added'] < 20:
                logger.warning("  ⚠ Insufficient features added")
            if classif_stats['feature_coverage_percent'] < 80.0 or ner_stats['feature_coverage_percent'] < 80.0:
                logger.warning("  ⚠ Feature coverage below 80%")
            return 1

    except Exception as e:
        logger.error("\n" + "="*70)
        logger.error("ERROR: Augmentation failed")
        logger.error("="*70)
        logger.error(f"{type(e).__name__}: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == '__main__':
    sys.exit(main())
