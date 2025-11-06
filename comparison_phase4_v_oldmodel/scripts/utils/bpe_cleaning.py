"""
BPE (Byte-Pair Encoding) cleaning utilities for NER results.

This module provides functions to detect and clean BPE tokenization artifacts
that may contaminate NER results. Common artifacts include:
- "Ġ" prefix markers (e.g., "Ġprotein" instead of "protein")
- Subword tokens split incorrectly (e.g., "pro", "te", "in")
- Mixed clean and contaminated entities in the same dataset

The cleaning process:
1. Detects BPE artifacts using pattern matching
2. Removes "Ġ" prefixes and merges subword tokens
3. Generates statistics on contamination levels
4. Preserves original data while creating cleaned versions
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

# BPE marker pattern (Ġ is the standard GPT-2 style space marker)
BPE_MARKER_PATTERN = re.compile(r'Ġ')

# Additional patterns for detecting BPE artifacts
SUBWORD_PATTERN = re.compile(r'\b\w{1,2}\b')  # Very short tokens may be subwords


def detect_bpe_artifacts(entity: str) -> bool:
    """
    Detect if an entity string contains BPE tokenization artifacts.

    Checks for:
    1. "Ġ" prefix markers (primary indicator)
    2. Multiple consecutive very short tokens (possible subwords)

    Args:
        entity: Entity string to check

    Returns:
        True if BPE artifacts detected, False otherwise

    Examples:
        >>> detect_bpe_artifacts("Ġprotein")
        True

        >>> detect_bpe_artifacts("ĠIL-6")
        True

        >>> detect_bpe_artifacts("protein A")
        False

        >>> detect_bpe_artifacts("IL-6")
        False
    """
    if not entity or not isinstance(entity, str):
        return False

    # Check for Ġ marker (primary indicator)
    if BPE_MARKER_PATTERN.search(entity):
        return True

    # Secondary check: multiple consecutive very short tokens
    # This catches cases like "pro te in" which should be "protein"
    tokens = entity.strip().split()
    if len(tokens) >= 3:
        short_tokens = [t for t in tokens if len(t) <= 2 and t.isalpha()]
        if len(short_tokens) >= 2:
            # Be conservative - only flag if many short tokens
            return len(short_tokens) / len(tokens) > 0.5

    return False


def clean_bpe_entity(entity: str) -> str:
    """
    Clean BPE tokenization artifacts from an entity string.

    Performs the following cleaning steps:
    1. Remove "Ġ" prefix markers
    2. Merge consecutive short tokens (likely subwords) - EXCEPT for valid biological tokens
    3. Normalize whitespace
    4. Preserve hyphens and special characters

    Valid short biological tokens that should NOT be merged:
    - Single letter cell types: "T", "B" (e.g., "T cell", "B lymphocyte")
    - Interleukin prefixes: "IL" (e.g., "IL-6", "IL-10")
    - Other common biological abbreviations: "A", "C", "G", "E"

    When merging short tokens, uses spaces not concatenation to preserve readability.

    Args:
        entity: Entity string to clean

    Returns:
        Cleaned entity string

    Examples:
        >>> clean_bpe_entity("Ġprotein")
        'protein'

        >>> clean_bpe_entity("ĠIL-6")
        'IL-6'

        >>> clean_bpe_entity("Ġprotein ĠA")
        'protein A'

        >>> clean_bpe_entity("pro te in")
        'protein'

        >>> clean_bpe_entity("T cell")
        'T cell'  # Preserves valid "T" token

        >>> clean_bpe_entity("IL-Ġ6")
        'IL-6'
    """
    if not entity or not isinstance(entity, str):
        return entity

    original = entity

    # Whitelist of valid short biological tokens that should NOT be merged
    BIOLOGICAL_TOKEN_WHITELIST = {"T", "B", "IL", "A", "C", "G", "E"}

    # Step 1: Remove Ġ markers
    cleaned = BPE_MARKER_PATTERN.sub('', entity)

    # Step 2: Merge consecutive short tokens (likely subwords)
    # EXCEPT for tokens in the whitelist
    tokens = cleaned.split()
    merged_tokens = []
    buffer = []

    for token in tokens:
        # Check if this is a short token (likely subword)
        is_short = len(token) <= 2 and token.isalpha()
        is_whitelisted = token.upper() in BIOLOGICAL_TOKEN_WHITELIST

        if is_short and not is_whitelisted:
            # Short token not in whitelist - might be a subword fragment
            buffer.append(token)
        else:
            # Flush buffer if we have accumulated short tokens
            if buffer:
                # Only merge if we have multiple consecutive short tokens
                if len(buffer) >= 2:
                    # Merge with spaces, not concatenation, for readability
                    merged = ' '.join(buffer)
                    merged_tokens.append(merged)
                else:
                    # Single short token - keep it separate (might be valid)
                    merged_tokens.extend(buffer)
                buffer = []

            # Add current token (either long or whitelisted)
            merged_tokens.append(token)

    # Flush remaining buffer
    if buffer:
        if len(buffer) >= 2:
            # Merge with spaces, not concatenation
            merged = ' '.join(buffer)
            merged_tokens.append(merged)
        else:
            merged_tokens.extend(buffer)

    # Step 3: Join and normalize whitespace
    cleaned = ' '.join(merged_tokens)
    cleaned = ' '.join(cleaned.split())  # Normalize whitespace

    # Log if significant cleaning occurred
    if cleaned != original:
        logger.debug(f"Cleaned entity: '{original}' -> '{cleaned}'")

    return cleaned


def clean_bpe_dataframe(
    df: pd.DataFrame,
    entity_column: str = 'entities',
    create_new_column: bool = True,
    new_column_name: Optional[str] = None
) -> pd.DataFrame:
    """
    Clean BPE artifacts from entity column in DataFrame.

    Can either:
    1. Create a new column with cleaned entities (preserves original)
    2. Modify the existing column in-place

    Args:
        df: DataFrame containing entity data
        entity_column: Name of column containing entities
        create_new_column: If True, creates new column; if False, modifies in-place
        new_column_name: Name for new column (default: '{entity_column}_cleaned')

    Returns:
        DataFrame with cleaned entities (copy if create_new_column=True, else original)

    Examples:
        >>> df = pd.DataFrame({'entities': ['Ġprotein', 'gene A', 'ĠIL-6']})
        >>> cleaned_df = clean_bpe_dataframe(df)
        >>> print(cleaned_df['entities_cleaned'].tolist())
        ['protein', 'gene A', 'IL-6']
    """
    if entity_column not in df.columns:
        logger.error(f"Column '{entity_column}' not found in DataFrame")
        return df

    # Determine output column name
    if create_new_column:
        if new_column_name is None:
            new_column_name = f"{entity_column}_cleaned"
        output_col = new_column_name
        df = df.copy()
    else:
        output_col = entity_column

    # Clean entities
    logger.info(f"Cleaning BPE artifacts from column: {entity_column}")

    def clean_entity_value(value):
        """Clean a single entity value (handles various formats)."""
        if pd.isna(value) or value == "":
            return value

        # Handle lists of entities
        if isinstance(value, list):
            return [clean_bpe_entity(e) for e in value]

        # Handle comma-separated strings
        if isinstance(value, str) and ',' in value:
            entities = [e.strip() for e in value.split(',')]
            cleaned = [clean_bpe_entity(e) for e in entities]
            return ', '.join(cleaned)

        # Handle single entity string
        return clean_bpe_entity(str(value))

    df[output_col] = df[entity_column].apply(clean_entity_value)

    logger.info(f"Cleaned entities stored in column: {output_col}")

    return df


def generate_bpe_report(
    df: pd.DataFrame,
    entity_column: str = 'entities'
) -> Dict:
    """
    Generate comprehensive report on BPE contamination in DataFrame.

    Analyzes:
    1. Number and percentage of rows with BPE artifacts
    2. Number and percentage of individual entities with artifacts
    3. Most common artifact patterns
    4. Examples of contaminated entities

    Args:
        df: DataFrame containing entity data
        entity_column: Name of column containing entities

    Returns:
        Dictionary with contamination statistics and examples

    Example:
        >>> df = pd.DataFrame({'entities': ['Ġprotein', 'gene A', 'ĠIL-6', 'protein B']})
        >>> report = generate_bpe_report(df)
        >>> print(f"Contamination: {report['contamination_rate']:.1%}")
        Contamination: 50.0%
    """
    if entity_column not in df.columns:
        logger.error(f"Column '{entity_column}' not found in DataFrame")
        return {}

    total_rows = len(df)
    contaminated_rows = 0
    total_entities = 0
    contaminated_entities = 0
    contaminated_examples = []

    # Analyze each row
    for idx, value in df[entity_column].items():
        if pd.isna(value) or value == "":
            continue

        row_contaminated = False

        # Parse entities
        if isinstance(value, list):
            entities = value
        elif isinstance(value, str) and ',' in value:
            entities = [e.strip() for e in value.split(',')]
        else:
            entities = [str(value)]

        # Check each entity
        for entity in entities:
            if not entity:
                continue

            total_entities += 1

            if detect_bpe_artifacts(entity):
                contaminated_entities += 1
                row_contaminated = True

                # Collect examples (limit to 20)
                if len(contaminated_examples) < 20:
                    contaminated_examples.append({
                        'index': idx,
                        'original': entity,
                        'cleaned': clean_bpe_entity(entity)
                    })

        if row_contaminated:
            contaminated_rows += 1

    # Calculate rates
    row_contamination_rate = contaminated_rows / total_rows if total_rows > 0 else 0.0
    entity_contamination_rate = contaminated_entities / total_entities if total_entities > 0 else 0.0

    # Count artifact types
    artifact_counts = {
        'with_G_marker': 0,
        'short_tokens': 0,
    }

    for example in contaminated_examples:
        entity = example['original']
        if BPE_MARKER_PATTERN.search(entity):
            artifact_counts['with_G_marker'] += 1
        if len(entity.split()) >= 3:
            short_tokens = [t for t in entity.split() if len(t) <= 2 and t.isalpha()]
            if len(short_tokens) >= 2:
                artifact_counts['short_tokens'] += 1

    # Build report
    report = {
        'total_rows': total_rows,
        'contaminated_rows': contaminated_rows,
        'row_contamination_rate': row_contamination_rate,
        'total_entities': total_entities,
        'contaminated_entities': contaminated_entities,
        'entity_contamination_rate': entity_contamination_rate,
        'artifact_counts': artifact_counts,
        'examples': contaminated_examples,
    }

    # Log summary
    logger.info(f"BPE Contamination Report:")
    logger.info(f"  Rows: {contaminated_rows}/{total_rows} ({row_contamination_rate:.1%})")
    logger.info(f"  Entities: {contaminated_entities}/{total_entities} ({entity_contamination_rate:.1%})")
    logger.info(f"  Ġ markers: {artifact_counts['with_G_marker']}")
    logger.info(f"  Short tokens: {artifact_counts['short_tokens']}")

    return report


def compare_before_after_cleaning(
    df: pd.DataFrame,
    entity_column: str = 'entities',
    n_samples: int = 10
) -> pd.DataFrame:
    """
    Generate side-by-side comparison of entities before and after cleaning.

    Useful for visual inspection and validation of cleaning process.

    Args:
        df: DataFrame containing entity data
        entity_column: Name of column containing entities
        n_samples: Number of samples to show (prioritizes contaminated entities)

    Returns:
        DataFrame with 'original' and 'cleaned' columns showing comparison

    Example:
        >>> df = pd.DataFrame({'entities': ['Ġprotein', 'gene A', 'ĠIL-6']})
        >>> comparison = compare_before_after_cleaning(df, n_samples=3)
        >>> print(comparison)
    """
    if entity_column not in df.columns:
        logger.error(f"Column '{entity_column}' not found in DataFrame")
        return pd.DataFrame()

    comparisons = []

    # Collect contaminated entities first
    for idx, value in df[entity_column].items():
        if pd.isna(value) or value == "":
            continue

        # Parse entities
        if isinstance(value, list):
            entities = value
        elif isinstance(value, str) and ',' in value:
            entities = [e.strip() for e in value.split(',')]
        else:
            entities = [str(value)]

        # Check each entity
        for entity in entities:
            if not entity:
                continue

            if detect_bpe_artifacts(entity):
                comparisons.append({
                    'index': idx,
                    'original': entity,
                    'cleaned': clean_bpe_entity(entity),
                    'contaminated': True
                })

            if len(comparisons) >= n_samples:
                break

        if len(comparisons) >= n_samples:
            break

    # Add clean entities if we don't have enough samples
    if len(comparisons) < n_samples:
        for idx, value in df[entity_column].items():
            if pd.isna(value) or value == "" or len(comparisons) >= n_samples:
                continue

            # Parse entities
            if isinstance(value, list):
                entities = value
            elif isinstance(value, str) and ',' in value:
                entities = [e.strip() for e in value.split(',')]
            else:
                entities = [str(value)]

            # Check each entity
            for entity in entities:
                if not entity:
                    continue

                if not detect_bpe_artifacts(entity):
                    comparisons.append({
                        'index': idx,
                        'original': entity,
                        'cleaned': clean_bpe_entity(entity),
                        'contaminated': False
                    })

                if len(comparisons) >= n_samples:
                    break

    comparison_df = pd.DataFrame(comparisons)

    return comparison_df
