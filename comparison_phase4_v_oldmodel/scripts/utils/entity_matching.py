"""
Entity matching utilities for NER comparison.

This module provides various strategies for matching entities between datasets:
- Exact matching (case-insensitive)
- Partial matching (substring)
- Fuzzy matching (Levenshtein distance)
- Token overlap (Jaccard similarity)

The main `match_entities()` function tries all strategies and returns the best match.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


def exact_match(entity1: str, entity2: str) -> bool:
    """
    Check if two entities match exactly (case-insensitive).

    Normalizes entities by:
    1. Converting to lowercase
    2. Stripping leading/trailing whitespace
    3. Normalizing internal whitespace to single spaces

    Args:
        entity1: First entity string
        entity2: Second entity string

    Returns:
        True if entities match exactly after normalization, False otherwise

    Examples:
        >>> exact_match("Protein A", "protein a")
        True

        >>> exact_match("Gene  B", "Gene B")  # Multiple spaces normalized
        True

        >>> exact_match("Protein A", "Protein B")
        False
    """
    if not entity1 or not entity2:
        return False

    # Normalize: lowercase, strip, and collapse whitespace
    norm1 = ' '.join(str(entity1).lower().strip().split())
    norm2 = ' '.join(str(entity2).lower().strip().split())

    return norm1 == norm2


def partial_match(entity1: str, entity2: str, min_length: int = 3) -> bool:
    """
    Check if one entity is a substring of the other (case-insensitive).

    Useful for matching entities where one is an abbreviation or partial form
    of the other, e.g., "IL-6" and "Interleukin 6".

    Args:
        entity1: First entity string
        entity2: Second entity string
        min_length: Minimum length for the shorter entity to avoid spurious matches

    Returns:
        True if one entity is contained in the other, False otherwise

    Examples:
        >>> partial_match("IL-6", "Interleukin 6")
        False  # IL-6 not in "interleukin 6"

        >>> partial_match("protein", "protein kinase A")
        True

        >>> partial_match("a", "protein a")
        False  # Too short (< min_length)
    """
    if not entity1 or not entity2:
        return False

    # Normalize
    norm1 = str(entity1).lower().strip()
    norm2 = str(entity2).lower().strip()

    # Check minimum length
    shorter = min(norm1, norm2, key=len)
    if len(shorter) < min_length:
        return False

    # Check substring relationship
    return norm1 in norm2 or norm2 in norm1


def fuzzy_match(entity1: str, entity2: str, max_distance: int = 2) -> bool:
    """
    Check if two entities match within a Levenshtein distance threshold.

    Uses a simple implementation of Levenshtein distance to measure similarity.
    Useful for matching entities with minor typos, formatting differences, or
    tokenization artifacts.

    Args:
        entity1: First entity string
        entity2: Second entity string
        max_distance: Maximum allowed Levenshtein distance (default: 2)

    Returns:
        True if Levenshtein distance <= max_distance, False otherwise

    Examples:
        >>> fuzzy_match("protein A", "protein a")  # Case difference
        True

        >>> fuzzy_match("IL-6", "IL-6 ")  # Trailing space
        True

        >>> fuzzy_match("protein", "protien")  # Typo (distance=1)
        True

        >>> fuzzy_match("protein", "proteins")  # One char diff
        True

        >>> fuzzy_match("protein A", "protein XYZ")  # Too different
        False
    """
    if not entity1 or not entity2:
        return False

    # Normalize
    s1 = str(entity1).lower().strip()
    s2 = str(entity2).lower().strip()

    # Identical after normalization
    if s1 == s2:
        return True

    # Calculate Levenshtein distance using dynamic programming
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    # Early termination if length difference exceeds threshold
    if len(s1) - len(s2) > max_distance:
        return False

    # Initialize distance matrix
    prev_row = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (0 if c1 == c2 else 1)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    distance = prev_row[-1]
    return distance <= max_distance


def token_overlap(entity1: str, entity2: str, threshold: float = 0.5) -> bool:
    """
    Check if two entities have sufficient token overlap (Jaccard similarity).

    Computes Jaccard similarity of word tokens:
    J(A, B) = |A ∩ B| / |A ∪ B|

    Useful for matching multi-word entities that may have different word orders
    or additional words, e.g., "protein kinase A" vs "kinase A protein".

    Args:
        entity1: First entity string
        entity2: Second entity string
        threshold: Minimum Jaccard similarity score (0.0 to 1.0)

    Returns:
        True if Jaccard similarity >= threshold, False otherwise

    Examples:
        >>> token_overlap("protein kinase A", "kinase A protein")
        True  # All tokens match

        >>> token_overlap("protein kinase A", "protein kinase")
        True  # 2/3 = 0.67 > 0.5

        >>> token_overlap("protein A", "protein B")
        False  # 1/3 = 0.33 < 0.5 threshold

        >>> token_overlap("IL-6", "Interleukin 6")
        False  # No token overlap
    """
    if not entity1 or not entity2:
        return False

    # Normalize and tokenize
    tokens1 = set(str(entity1).lower().strip().split())
    tokens2 = set(str(entity2).lower().strip().split())

    # Remove empty tokens
    tokens1 = {t for t in tokens1 if t}
    tokens2 = {t for t in tokens2 if t}

    # Calculate Jaccard similarity
    if not tokens1 or not tokens2:
        return False

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    jaccard = len(intersection) / len(union) if union else 0.0

    return jaccard >= threshold


def match_entities(
    entities1: List[str],
    entities2: List[str],
    strategies: Optional[List[str]] = None,
    return_details: bool = False
) -> Dict:
    """
    Match entities from two lists using multiple strategies.

    Uses a multi-pass approach to prioritize higher-quality matches:
    1. First pass: Find all exact matches
    2. Second pass: Find all partial matches (from remaining unmatched)
    3. Third pass: Find all fuzzy matches (from remaining unmatched)
    4. Fourth pass: Find all token_overlap matches (from remaining unmatched)

    This ensures better quality matches are found first, avoiding suboptimal
    greedy matches that could block better matches later.

    Args:
        entities1: First list of entity strings
        entities2: Second list of entity strings
        strategies: List of strategy names to use. If None, uses all strategies.
                   Options: ['exact', 'partial', 'fuzzy', 'token_overlap']
        return_details: If True, includes detailed match information per entity

    Returns:
        Dictionary with keys:
        - 'matched_pairs': List of (entity1, entity2, strategy) tuples
        - 'unmatched_1': List of entities from entities1 with no match
        - 'unmatched_2': List of entities from entities2 with no match
        - 'match_count': Total number of matches
        - 'strategy_counts': Dict of match counts per strategy
        - 'details': (if return_details=True) Dict with per-entity match info

    Examples:
        >>> ents1 = ["protein A", "gene B"]
        >>> ents2 = ["protein a", "gene C"]
        >>> results = match_entities(ents1, ents2)
        >>> print(results['match_count'])
        1
        >>> print(results['matched_pairs'])
        [('protein A', 'protein a', 'exact')]
    """
    if strategies is None:
        strategies = ['exact', 'partial', 'fuzzy', 'token_overlap']

    # Initialize results
    matched_pairs = []
    matched_1 = set()
    matched_2 = set()
    strategy_counts = {s: 0 for s in strategies}
    details = {} if return_details else None

    # Map strategy names to functions
    strategy_funcs = {
        'exact': exact_match,
        'fuzzy': fuzzy_match,
        'partial': partial_match,
        'token_overlap': token_overlap,
    }

    # Validate strategies
    valid_strategies = []
    for s in strategies:
        if s in strategy_funcs:
            valid_strategies.append(s)
        else:
            logger.warning(f"Unknown strategy '{s}', skipping")

    # Pre-normalize entities once to avoid repeated normalization
    # Store normalized versions with original indices
    def normalize_entity(entity: str) -> str:
        """Normalize entity for comparison."""
        if not entity:
            return ""
        return ' '.join(str(entity).lower().strip().split())

    normalized_entities1 = {
        i: (ent, normalize_entity(ent))
        for i, ent in enumerate(entities1)
        if ent and str(ent).strip()
    }
    normalized_entities2 = {
        j: (ent, normalize_entity(ent))
        for j, ent in enumerate(entities2)
        if ent and str(ent).strip()
    }

    # Multi-pass matching: prioritize exact matches before fuzzy ones
    for strategy in valid_strategies:
        if strategy not in strategy_funcs:
            continue

        match_func = strategy_funcs[strategy]

        # Try to match each unmatched entity from list 1
        for i, (ent1, norm1) in normalized_entities1.items():
            if i in matched_1:  # Already matched in previous pass
                continue

            # Try to match against each unmatched entity in list 2
            for j, (ent2, norm2) in normalized_entities2.items():
                if j in matched_2:  # Already matched in previous pass
                    continue

                # Try this matching strategy
                if match_func(ent1, ent2):
                    matched_pairs.append((ent1, ent2, strategy))
                    matched_1.add(i)
                    matched_2.add(j)
                    strategy_counts[strategy] += 1

                    if return_details:
                        details[ent1] = {
                            'matched_to': ent2,
                            'strategy': strategy,
                            'index_1': i,
                            'index_2': j,
                        }

                    break  # Found a match for ent1, move to next entity

    # Collect unmatched entities
    unmatched_1 = [ent for i, ent in enumerate(entities1) if i not in matched_1 and ent and str(ent).strip()]
    unmatched_2 = [ent for j, ent in enumerate(entities2) if j not in matched_2 and ent and str(ent).strip()]

    # Build results dictionary
    results = {
        'matched_pairs': matched_pairs,
        'unmatched_1': unmatched_1,
        'unmatched_2': unmatched_2,
        'match_count': len(matched_pairs),
        'strategy_counts': strategy_counts,
        'total_1': len([e for e in entities1 if e and str(e).strip()]),
        'total_2': len([e for e in entities2 if e and str(e).strip()]),
    }

    if return_details:
        results['details'] = details

    return results


def get_match_statistics(match_results: Dict) -> Dict:
    """
    Calculate summary statistics from match results.

    Args:
        match_results: Output from match_entities()

    Returns:
        Dictionary with match statistics including percentages and strategy breakdown

    Example:
        >>> results = match_entities(ents1, ents2)
        >>> stats = get_match_statistics(results)
        >>> print(f"Match rate: {stats['match_rate_1']:.1%}")
    """
    total_1 = match_results['total_1']
    total_2 = match_results['total_2']
    match_count = match_results['match_count']

    stats = {
        'match_count': match_count,
        'match_rate_1': match_count / total_1 if total_1 > 0 else 0.0,
        'match_rate_2': match_count / total_2 if total_2 > 0 else 0.0,
        'unmatched_1_count': len(match_results['unmatched_1']),
        'unmatched_2_count': len(match_results['unmatched_2']),
        'strategy_counts': match_results['strategy_counts'],
    }

    # Add strategy percentages
    if match_count > 0:
        stats['strategy_percentages'] = {
            strategy: count / match_count
            for strategy, count in match_results['strategy_counts'].items()
        }
    else:
        stats['strategy_percentages'] = {
            strategy: 0.0
            for strategy in match_results['strategy_counts'].keys()
        }

    return stats
