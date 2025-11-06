"""
Data loading utilities for Phase 4 vs V2 NER comparison.

This module provides functions to load data from various sources:
- V2 NER results (old model)
- Phase 4 NER results (new model)
- NER test split ground truth
- Final inventory data

All functions handle common data issues like missing files, encoding errors,
and malformed data with appropriate error messages.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

# Base paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
COLLAB_RESULTS_DIR = PROJECT_ROOT / "collab_results"
EXPERIMENT_ARCHIVES_DIR = COLLAB_RESULTS_DIR / "experiment_archives"
DATA_DIR = PROJECT_ROOT / "data"


def load_v2_results(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load V2 (old model) NER results from CSV file.

    V2 results are from the original model trained with the legacy pipeline.
    Default location: collab_results/2025-10-28-ulgfhi_oldmodel_2022_rerun/ner_results.csv

    Args:
        file_path: Optional custom path to V2 results file. If None, uses default path.

    Returns:
        DataFrame with columns typically including:
        - pmid: PubMed ID
        - entities: Extracted entities (comma-separated or JSON)
        - text: Original text
        - Other model-specific columns

    Raises:
        FileNotFoundError: If the results file doesn't exist
        pd.errors.EmptyDataError: If the file is empty
        Exception: For other pandas reading errors

    Example:
        >>> v2_df = load_v2_results()
        >>> print(f"Loaded {len(v2_df)} V2 results")
        >>> print(v2_df.columns.tolist())
    """
    if file_path is None:
        file_path = COLLAB_RESULTS_DIR / "2025-10-28-ulgfhi_oldmodel_2022_rerun" / "ner_results.csv"

    try:
        logger.info(f"Loading V2 results from: {file_path}")
        df = pd.read_csv(file_path, encoding='utf-8')

        # Normalize ID column: convert float -> int -> string to avoid .0 suffix
        if 'ID' in df.columns:
            df['ID'] = df['ID'].astype(float).astype(int).astype(str)
            logger.debug(f"Normalized 'ID' column to string format (sample: {df['ID'].iloc[0] if len(df) > 0 else 'N/A'})")

        logger.info(f"Successfully loaded {len(df)} V2 results with columns: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        logger.error(f"V2 results file not found: {file_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"V2 results file is empty: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading V2 results from {file_path}: {str(e)}")
        raise


def load_phase4_results(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load Phase 4 (new model) NER results from CSV file.

    Phase 4 results are from the improved model with enhanced post-processing.
    Default location: experiment_archives/2025-11-05-ygnr9f_phase4_2022_rerun/ner_results.csv

    Args:
        file_path: Optional custom path to Phase 4 results file. If None, uses default path.

    Returns:
        DataFrame with columns typically including:
        - pmid: PubMed ID
        - entities: Extracted entities (comma-separated or JSON)
        - text: Original text
        - confidence: Entity confidence scores (if available)
        - Other model-specific columns

    Raises:
        FileNotFoundError: If the results file doesn't exist
        pd.errors.EmptyDataError: If the file is empty
        Exception: For other pandas reading errors

    Example:
        >>> phase4_df = load_phase4_results()
        >>> print(f"Loaded {len(phase4_df)} Phase 4 results")
        >>> print(phase4_df.columns.tolist())
    """
    if file_path is None:
        file_path = EXPERIMENT_ARCHIVES_DIR / "2025-11-05-ygnr9f_phase4_2022_rerun" / "ner_results.csv"

    try:
        logger.info(f"Loading Phase 4 results from: {file_path}")
        df = pd.read_csv(file_path, encoding='utf-8')

        # Normalize ID column: convert float -> int -> string to avoid .0 suffix
        if 'ID' in df.columns:
            df['ID'] = df['ID'].astype(float).astype(int).astype(str)
            logger.debug(f"Normalized 'ID' column to string format (sample: {df['ID'].iloc[0] if len(df) > 0 else 'N/A'})")

        logger.info(f"Successfully loaded {len(df)} Phase 4 results with columns: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        logger.error(f"Phase 4 results file not found: {file_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Phase 4 results file is empty: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading Phase 4 results from {file_path}: {str(e)}")
        raise


def load_ner_test_split(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load NER test split ground truth data from CSV file.

    The test split contains manually annotated ground truth entities for evaluation.
    Default location: data/ner_splits_full/test_ner.csv

    Args:
        file_path: Optional custom path to test split file. If None, uses default path.

    Returns:
        DataFrame with columns typically including:
        - pmid: PubMed ID
        - text: Original text
        - entities: Ground truth entities (annotated)
        - labels: Entity labels/types (if available)
        - Other annotation metadata

    Raises:
        FileNotFoundError: If the test split file doesn't exist
        pd.errors.EmptyDataError: If the file is empty
        Exception: For other pandas reading errors

    Example:
        >>> test_df = load_ner_test_split()
        >>> print(f"Loaded {len(test_df)} test samples")
        >>> print(test_df['entities'].head())
    """
    if file_path is None:
        file_path = DATA_DIR / "ner_splits_full" / "test_ner.csv"

    try:
        logger.info(f"Loading NER test split from: {file_path}")
        df = pd.read_csv(file_path, encoding='utf-8')

        # Normalize id column: convert float -> int -> string to avoid .0 suffix
        if 'id' in df.columns:
            df['id'] = df['id'].astype(float).astype(int).astype(str)
            logger.debug(f"Normalized 'id' column to string format (sample: {df['id'].iloc[0] if len(df) > 0 else 'N/A'})")

        logger.info(f"Successfully loaded {len(df)} test samples with columns: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        logger.error(f"NER test split file not found: {file_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"NER test split file is empty: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading NER test split from {file_path}: {str(e)}")
        raise


def load_inventory(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load final inventory data from CSV file.

    The inventory contains metadata for all papers in the dataset.
    Default location: data/final_inventory_2022.csv

    Args:
        file_path: Optional custom path to inventory file. If None, uses default path.

    Returns:
        DataFrame with columns typically including:
        - pmid: PubMed ID
        - title: Paper title
        - abstract: Paper abstract
        - year: Publication year
        - journal: Journal name
        - Other paper metadata

    Raises:
        FileNotFoundError: If the inventory file doesn't exist
        pd.errors.EmptyDataError: If the file is empty
        Exception: For other pandas reading errors

    Example:
        >>> inventory_df = load_inventory()
        >>> print(f"Loaded {len(inventory_df)} papers")
        >>> print(inventory_df[['pmid', 'title']].head())
    """
    if file_path is None:
        file_path = DATA_DIR / "final_inventory_2022.csv"

    try:
        logger.info(f"Loading inventory from: {file_path}")
        df = pd.read_csv(file_path, encoding='utf-8')

        # Normalize ID columns: convert float -> int -> string to avoid .0 suffix
        for id_col in ['pmid', 'PMID', 'id', 'ID']:
            if id_col in df.columns:
                # Handle comma-separated IDs by taking the first one
                if df[id_col].dtype == 'object':  # String column
                    # Check if any values contain commas
                    has_commas = df[id_col].astype(str).str.contains(',', na=False).any()
                    if has_commas:
                        num_affected = df[id_col].astype(str).str.contains(',', na=False).sum()
                        logger.warning(f"Found {num_affected} rows with comma-separated IDs in '{id_col}' column. "
                                      f"Using only the first ID from each comma-separated value.")

                    # Split by comma and take first ID, then strip whitespace
                    df[id_col] = df[id_col].astype(str).str.split(',').str[0].str.strip()

                # Now convert: string -> float -> int -> string
                df[id_col] = df[id_col].astype(float).astype(int).astype(str)
                logger.debug(f"Normalized '{id_col}' column to string format (sample: {df[id_col].iloc[0] if len(df) > 0 else 'N/A'})")
                break  # Only normalize one ID column

        logger.info(f"Successfully loaded {len(df)} papers with columns: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        logger.error(f"Inventory file not found: {file_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Inventory file is empty: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading inventory from {file_path}: {str(e)}")
        raise


def parse_entity_list(entity_str: Union[str, List[str], None]) -> List[str]:
    """
    Parse entity string into a list of individual entities.

    Handles multiple formats:
    1. Comma-separated strings: "entity1, entity2, entity3"
    2. JSON array strings: '["entity1", "entity2"]'
    3. Python list repr strings: "['entity1', 'entity2']"
    4. Already parsed lists: ["entity1", "entity2"]
    5. Empty/null values: None, "", "[]", NaN

    Args:
        entity_str: Entity string in various formats, list, or None

    Returns:
        List of individual entity strings (empty list if input is None/empty)

    Examples:
        >>> parse_entity_list("protein A, gene B, compound C")
        ['protein A', 'gene B', 'compound C']

        >>> parse_entity_list('["protein A", "gene B"]')
        ['protein A', 'gene B']

        >>> parse_entity_list("['sc-PDB']")
        ['sc-PDB']

        >>> parse_entity_list(["protein A", "gene B"])
        ['protein A', 'gene B']

        >>> parse_entity_list(None)
        []

        >>> parse_entity_list("")
        []

        >>> parse_entity_list(float('nan'))
        []
    """
    # Already a list - handle this FIRST before pd.isna() check
    if isinstance(entity_str, list):
        return [str(e).strip() for e in entity_str if e and str(e).strip() and str(e).strip().lower() != 'nan']

    # BUG FIX #1: Handle NaN/None - check for NaN BEFORE processing
    # Note: pd.isna() doesn't work well with lists, so check isinstance first
    if pd.isna(entity_str):
        return []

    if entity_str is None or str(entity_str).strip().lower() in ['nan', 'none', '']:
        return []

    if entity_str == "" or entity_str == "[]":
        return []

    # Convert to string if not already
    entity_str = str(entity_str).strip()

    # Empty after stripping
    if not entity_str or entity_str == "[]":
        return []

    # Try parsing as JSON first
    if entity_str.startswith('[') and entity_str.endswith(']'):
        # Try JSON parsing
        try:
            entities = json.loads(entity_str)
            if isinstance(entities, list):
                return [str(e).strip() for e in entities if e and str(e).strip() and str(e).strip().lower() != 'nan']
        except json.JSONDecodeError:
            logger.debug(f"JSON parsing failed, trying Python literal eval: {entity_str[:100]}")

            # BUG FIX #3: Try ast.literal_eval for Python list repr like "['item']"
            try:
                import ast
                entities = ast.literal_eval(entity_str)
                if isinstance(entities, list):
                    return [str(e).strip() for e in entities if e and str(e).strip() and str(e).strip().lower() != 'nan']
            except (ValueError, SyntaxError):
                logger.warning(f"Failed to parse as Python literal, trying comma-separated: {entity_str[:100]}")

    # Parse as comma-separated string
    entities = [e.strip() for e in entity_str.split(',') if e.strip()]

    # Filter out empty strings, 'nan' values, and clean up
    return [e for e in entities if e and e.lower() != 'nan']


def load_aligned_papers(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load aligned papers CSV with proper JSON deserialization.

    This function loads the aligned_papers.csv file and properly deserializes
    all entity list columns from JSON strings back to Python lists.

    Args:
        file_path: Optional custom path to aligned papers file. If None, uses default path.

    Returns:
        DataFrame with entity columns properly deserialized as lists

    Raises:
        FileNotFoundError: If the aligned papers file doesn't exist
        pd.errors.EmptyDataError: If the file is empty

    Example:
        >>> aligned_df = load_aligned_papers()
        >>> print(f"Loaded {len(aligned_df)} aligned papers")
        >>> print(aligned_df['v2_com'].iloc[0])  # Should be a list, not a string
    """
    if file_path is None:
        file_path = Path(__file__).parent.parent / "data" / "aligned_papers.csv"

    try:
        logger.info(f"Loading aligned papers from: {file_path}")
        df = pd.read_csv(file_path, encoding='utf-8')

        # List of entity columns that need deserialization
        entity_columns = [
            'true_com', 'true_ful',
            'v2_com', 'v2_ful',
            'p4_com_raw', 'p4_com_clean',
            'p4_ful_raw', 'p4_ful_clean'
        ]

        # BUG FIX #2: Properly deserialize JSON strings back to lists
        logger.info("Deserializing entity columns from JSON...")
        for col in entity_columns:
            if col in df.columns:
                df[col] = df[col].apply(parse_entity_list)
                logger.debug(f"Deserialized '{col}' column")

        logger.info(f"Successfully loaded {len(df)} aligned papers with columns: {df.columns.tolist()}")

        # Validation: Check that entity columns are actually lists
        logger.info("Validating entity columns...")
        for col in entity_columns:
            if col in df.columns:
                non_list_count = df[col].apply(lambda x: not isinstance(x, list)).sum()
                if non_list_count > 0:
                    logger.warning(f"Column '{col}' has {non_list_count} non-list values")
                else:
                    logger.debug(f"Column '{col}': All values are properly formatted lists")

        # Log sample entities to catch corruption early
        logger.info("\nSample entities (first paper with data):")
        for col in entity_columns:
            if col in df.columns:
                # Find first non-empty entity list
                sample_idx = df[col].apply(lambda x: isinstance(x, list) and len(x) > 0).idxmax()
                if pd.notna(sample_idx):
                    sample_entities = df[col].iloc[sample_idx]
                    logger.info(f"  {col}: {sample_entities[:3] if len(sample_entities) > 3 else sample_entities}")

        return df

    except FileNotFoundError:
        logger.error(f"Aligned papers file not found: {file_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Aligned papers file is empty: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading aligned papers from {file_path}: {str(e)}")
        raise


def load_all_datasets() -> Dict[str, pd.DataFrame]:
    """
    Convenience function to load all datasets at once.

    Returns:
        Dictionary with keys: 'v2', 'phase4', 'test_split', 'inventory'
        Each value is the corresponding DataFrame.

    Example:
        >>> datasets = load_all_datasets()
        >>> v2_df = datasets['v2']
        >>> phase4_df = datasets['phase4']
        >>> test_df = datasets['test_split']
        >>> inventory_df = datasets['inventory']
    """
    logger.info("Loading all datasets...")

    datasets = {
        'v2': load_v2_results(),
        'phase4': load_phase4_results(),
        'test_split': load_ner_test_split(),
        'inventory': load_inventory(),
    }

    logger.info(f"Successfully loaded all datasets: "
                f"V2={len(datasets['v2'])}, "
                f"Phase4={len(datasets['phase4'])}, "
                f"Test={len(datasets['test_split'])}, "
                f"Inventory={len(datasets['inventory'])}")

    return datasets
