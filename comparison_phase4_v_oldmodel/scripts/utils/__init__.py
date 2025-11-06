"""
Utility library for Phase 4 vs V2 NER comparison project.

This package provides utilities for:
- Loading data from various sources (V2, Phase 4, test splits, inventory)
- Matching entities between datasets using multiple strategies
- Calculating evaluation metrics (precision, recall, F1)
- Detecting and cleaning BPE tokenization artifacts

Example:
    >>> from utils import load_v2_results, match_entities, calculate_precision_recall_f1
    >>> v2_data = load_v2_results()
    >>> matches = match_entities(entities1, entities2)
    >>> metrics = calculate_precision_recall_f1(tp=100, fp=10, fn=5)
"""

# Data loading utilities
from .data_loading import (
    load_v2_results,
    load_phase4_results,
    load_ner_test_split,
    load_inventory,
    load_aligned_papers,
    parse_entity_list,
)

# Entity matching utilities
from .entity_matching import (
    exact_match,
    partial_match,
    fuzzy_match,
    token_overlap,
    match_entities,
)

# Metrics calculation utilities
from .metrics import (
    calculate_precision_recall_f1,
    entity_level_metrics,
    confusion_matrix,
    bootstrap_confidence_interval,
)

# BPE cleaning utilities
from .bpe_cleaning import (
    detect_bpe_artifacts,
    clean_bpe_entity,
    clean_bpe_dataframe,
    generate_bpe_report,
)

__all__ = [
    # Data loading
    "load_v2_results",
    "load_phase4_results",
    "load_ner_test_split",
    "load_inventory",
    "load_aligned_papers",
    "parse_entity_list",
    # Entity matching
    "exact_match",
    "partial_match",
    "fuzzy_match",
    "token_overlap",
    "match_entities",
    # Metrics
    "calculate_precision_recall_f1",
    "entity_level_metrics",
    "confusion_matrix",
    "bootstrap_confidence_interval",
    # BPE cleaning
    "detect_bpe_artifacts",
    "clean_bpe_entity",
    "clean_bpe_dataframe",
    "generate_bpe_report",
]

__version__ = "1.0.0"
