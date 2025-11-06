"""
Metrics calculation utilities for NER evaluation.

This module provides functions to calculate various evaluation metrics:
- Precision, Recall, F1-score
- Entity-level metrics
- Confusion matrices
- Bootstrap confidence intervals

All functions handle edge cases (division by zero, empty inputs) gracefully.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


def calculate_precision_recall_f1(
    tp: int,
    fp: int,
    fn: int,
    beta: float = 1.0
) -> Dict[str, float]:
    """
    Calculate precision, recall, and F-score from confusion matrix counts.

    Formulas:
    - Precision = TP / (TP + FP)
    - Recall = TP / (TP + FN)
    - F_β = (1 + β²) × (Precision × Recall) / (β² × Precision + Recall)

    Args:
        tp: True Positives count
        fp: False Positives count
        fn: False Negatives count
        beta: Beta parameter for F-score (default: 1.0 for F1-score)
              β > 1 weights recall higher, β < 1 weights precision higher

    Returns:
        Dictionary with keys: 'precision', 'recall', 'f1', 'tp', 'fp', 'fn'

    Examples:
        >>> metrics = calculate_precision_recall_f1(tp=80, fp=10, fn=10)
        >>> print(f"F1: {metrics['f1']:.3f}")
        F1: 0.889

        >>> metrics = calculate_precision_recall_f1(tp=0, fp=0, fn=0)
        >>> print(metrics['f1'])
        0.0
    """
    # Calculate precision (handle division by zero)
    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0.0

    # Calculate recall (handle division by zero)
    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0.0

    # Calculate F-score (handle division by zero)
    if precision + recall > 0:
        beta_squared = beta ** 2
        f_score = (1 + beta_squared) * (precision * recall) / (beta_squared * precision + recall)
    else:
        f_score = 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f_score,
        'f_beta': f_score,
        'tp': tp,
        'fp': fp,
        'fn': fn,
    }


def entity_level_metrics(
    predicted_entities: List[str],
    true_entities: List[str],
    match_strategy: str = 'exact'
) -> Dict[str, float]:
    """
    Calculate entity-level precision, recall, and F1-score.

    Compares predicted entities against ground truth using specified matching strategy.

    Args:
        predicted_entities: List of predicted entity strings
        true_entities: List of ground truth entity strings
        match_strategy: How to match entities ('exact', 'fuzzy', 'partial', 'token_overlap')

    Returns:
        Dictionary with precision, recall, F1, and confusion matrix counts

    Examples:
        >>> predicted = ["protein A", "gene B", "compound C"]
        >>> true = ["protein A", "gene B", "gene D"]
        >>> metrics = entity_level_metrics(predicted, true)
        >>> print(f"F1: {metrics['f1']:.3f}")
        F1: 0.667
    """
    # Import here to avoid circular dependency
    from .entity_matching import match_entities

    # Handle empty inputs
    if not predicted_entities and not true_entities:
        metrics = calculate_precision_recall_f1(0, 0, 0)
        metrics['total_predicted'] = 0
        metrics['total_true'] = 0
        metrics['match_strategy'] = match_strategy
        return metrics

    if not predicted_entities:
        metrics = calculate_precision_recall_f1(0, 0, len(true_entities))
        metrics['total_predicted'] = 0
        metrics['total_true'] = len(true_entities)
        metrics['match_strategy'] = match_strategy
        return metrics

    if not true_entities:
        metrics = calculate_precision_recall_f1(0, len(predicted_entities), 0)
        metrics['total_predicted'] = len(predicted_entities)
        metrics['total_true'] = 0
        metrics['match_strategy'] = match_strategy
        return metrics

    # Normalize and deduplicate entities
    predicted_set = [str(e).strip() for e in predicted_entities if e and str(e).strip()]
    true_set = [str(e).strip() for e in true_entities if e and str(e).strip()]

    # Match entities
    match_results = match_entities(
        predicted_set,
        true_set,
        strategies=[match_strategy]
    )

    # Calculate confusion matrix counts
    tp = match_results['match_count']  # Correctly predicted entities
    fp = len(match_results['unmatched_1'])  # Predicted but not in ground truth
    fn = len(match_results['unmatched_2'])  # In ground truth but not predicted

    # Calculate metrics
    metrics = calculate_precision_recall_f1(tp, fp, fn)

    # Add additional information
    metrics['total_predicted'] = len(predicted_set)
    metrics['total_true'] = len(true_set)
    metrics['match_strategy'] = match_strategy

    return metrics


def confusion_matrix(
    y_true: List[int],
    y_pred: List[int],
    labels: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Create confusion matrix for binary or multi-class classification.

    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        labels: Optional list of label values. If None, inferred from data.

    Returns:
        DataFrame with confusion matrix (rows=true, columns=predicted)

    Examples:
        >>> y_true = [1, 1, 0, 0, 1]
        >>> y_pred = [1, 0, 0, 0, 1]
        >>> cm = confusion_matrix(y_true, y_pred)
        >>> print(cm)
           0  1
        0  2  0
        1  1  2
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"y_true and y_pred must have same length: {len(y_true)} vs {len(y_pred)}")

    if not y_true or not y_pred:
        logger.warning("Empty input to confusion_matrix")
        return pd.DataFrame()

    # Convert to numpy arrays
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # Determine labels
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))

    # Initialize confusion matrix
    n_labels = len(labels)
    cm = np.zeros((n_labels, n_labels), dtype=int)

    # Create label to index mapping
    label_to_idx = {label: idx for idx, label in enumerate(labels)}

    # Populate confusion matrix
    for true_label, pred_label in zip(y_true, y_pred):
        true_idx = label_to_idx.get(true_label)
        pred_idx = label_to_idx.get(pred_label)

        if true_idx is not None and pred_idx is not None:
            cm[true_idx, pred_idx] += 1

    # Create DataFrame with labels
    df = pd.DataFrame(cm, index=labels, columns=labels)
    df.index.name = 'True'
    df.columns.name = 'Predicted'

    return df


def bootstrap_confidence_interval(
    scores: List[float],
    confidence: float = 0.95,
    n_bootstrap: int = 10000,
    random_state: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate bootstrap confidence interval for metric scores.

    Uses bootstrap resampling to estimate confidence intervals for F1 or other scores.
    Useful when you have scores from multiple samples and want to estimate uncertainty.

    Args:
        scores: List of metric scores (e.g., F1 scores from different papers)
        confidence: Confidence level (default: 0.95 for 95% CI)
        n_bootstrap: Number of bootstrap samples (default: 10000)
        random_state: Random seed for reproducibility

    Returns:
        Dictionary with keys: 'mean', 'std', 'lower', 'upper', 'confidence'

    Examples:
        >>> f1_scores = [0.85, 0.87, 0.83, 0.89, 0.86]
        >>> ci = bootstrap_confidence_interval(f1_scores)
        >>> print(f"F1: {ci['mean']:.3f} [{ci['lower']:.3f}, {ci['upper']:.3f}]")
        F1: 0.860 [0.834, 0.886]
    """
    if not scores:
        logger.warning("Empty scores list for bootstrap CI")
        return {
            'mean': 0.0,
            'std': 0.0,
            'lower': 0.0,
            'upper': 0.0,
            'confidence': confidence,
        }

    # Convert to numpy array
    scores = np.array(scores)

    # Set random seed
    if random_state is not None:
        np.random.seed(random_state)

    # Generate bootstrap samples
    bootstrap_means = []
    n_samples = len(scores)

    for _ in range(n_bootstrap):
        # Resample with replacement
        bootstrap_sample = np.random.choice(scores, size=n_samples, replace=True)
        bootstrap_means.append(np.mean(bootstrap_sample))

    bootstrap_means = np.array(bootstrap_means)

    # Calculate percentiles for confidence interval
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    lower_bound = np.percentile(bootstrap_means, lower_percentile)
    upper_bound = np.percentile(bootstrap_means, upper_percentile)

    return {
        'mean': np.mean(scores),
        'std': np.std(scores, ddof=1),
        'lower': lower_bound,
        'upper': upper_bound,
        'confidence': confidence,
        'n_samples': len(scores),
        'n_bootstrap': n_bootstrap,
    }


def micro_average_metrics(metrics_list: List[Dict[str, int]]) -> Dict[str, float]:
    """
    Calculate micro-averaged metrics across multiple samples.

    Micro-averaging sums TP, FP, FN across all samples before calculating metrics.
    This gives equal weight to each entity regardless of which sample it came from.

    Args:
        metrics_list: List of dictionaries, each with 'tp', 'fp', 'fn' keys

    Returns:
        Dictionary with micro-averaged precision, recall, F1

    Examples:
        >>> sample1 = {'tp': 10, 'fp': 2, 'fn': 1}
        >>> sample2 = {'tp': 8, 'fp': 1, 'fn': 2}
        >>> metrics = micro_average_metrics([sample1, sample2])
        >>> print(f"Micro F1: {metrics['f1']:.3f}")
        Micro F1: 0.857
    """
    if not metrics_list:
        return calculate_precision_recall_f1(0, 0, 0)

    # Sum counts across all samples
    total_tp = sum(m['tp'] for m in metrics_list)
    total_fp = sum(m['fp'] for m in metrics_list)
    total_fn = sum(m['fn'] for m in metrics_list)

    # Calculate micro-averaged metrics
    return calculate_precision_recall_f1(total_tp, total_fp, total_fn)


def macro_average_metrics(metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Calculate macro-averaged metrics across multiple samples.

    Macro-averaging calculates metrics for each sample first, then averages them.
    This gives equal weight to each sample regardless of size.

    Args:
        metrics_list: List of dictionaries, each with 'precision', 'recall', 'f1' keys

    Returns:
        Dictionary with macro-averaged precision, recall, F1, and standard deviations

    Examples:
        >>> sample1 = {'precision': 0.9, 'recall': 0.85, 'f1': 0.87}
        >>> sample2 = {'precision': 0.8, 'recall': 0.9, 'f1': 0.85}
        >>> metrics = macro_average_metrics([sample1, sample2])
        >>> print(f"Macro F1: {metrics['f1']:.3f}")
        Macro F1: 0.860
    """
    if not metrics_list:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'precision_std': 0.0,
            'recall_std': 0.0,
            'f1_std': 0.0,
        }

    # Extract metric values
    precisions = [m['precision'] for m in metrics_list if 'precision' in m]
    recalls = [m['recall'] for m in metrics_list if 'recall' in m]
    f1s = [m['f1'] for m in metrics_list if 'f1' in m]

    # Calculate macro averages
    return {
        'precision': np.mean(precisions) if precisions else 0.0,
        'recall': np.mean(recalls) if recalls else 0.0,
        'f1': np.mean(f1s) if f1s else 0.0,
        'precision_std': np.std(precisions, ddof=1) if len(precisions) > 1 else 0.0,
        'recall_std': np.std(recalls, ddof=1) if len(recalls) > 1 else 0.0,
        'f1_std': np.std(f1s, ddof=1) if len(f1s) > 1 else 0.0,
        'n_samples': len(metrics_list),
    }


def aggregate_metrics(
    per_sample_metrics: List[Dict],
    include_ci: bool = True,
    confidence: float = 0.95
) -> Dict[str, Dict[str, float]]:
    """
    Aggregate per-sample metrics into micro, macro, and confidence intervals.

    Convenience function that calculates both micro and macro averages,
    plus optional bootstrap confidence intervals.

    Args:
        per_sample_metrics: List of per-sample metric dictionaries
        include_ci: Whether to calculate confidence intervals
        confidence: Confidence level for CI (default: 0.95)

    Returns:
        Dictionary with 'micro', 'macro', and optionally 'ci' keys

    Example:
        >>> metrics = [
        ...     {'tp': 10, 'fp': 2, 'fn': 1, 'precision': 0.83, 'recall': 0.91, 'f1': 0.87},
        ...     {'tp': 8, 'fp': 1, 'fn': 2, 'precision': 0.89, 'recall': 0.80, 'f1': 0.84}
        ... ]
        >>> agg = aggregate_metrics(metrics)
        >>> print(f"Micro F1: {agg['micro']['f1']:.3f}")
        >>> print(f"Macro F1: {agg['macro']['f1']:.3f}")
    """
    results = {}

    # Micro-averaged metrics
    results['micro'] = micro_average_metrics(per_sample_metrics)

    # Macro-averaged metrics
    results['macro'] = macro_average_metrics(per_sample_metrics)

    # Confidence intervals (if requested)
    if include_ci:
        f1_scores = [m['f1'] for m in per_sample_metrics if 'f1' in m]
        if f1_scores:
            results['ci'] = bootstrap_confidence_interval(
                f1_scores,
                confidence=confidence
            )

    return results
