"""
Multi-Task Model Evaluation Utilities

This module provides evaluation functions for multi-task learning:
1. Single-task performance evaluation
2. Comparison to single-task baselines
3. Negative transfer detection
4. Detailed per-task metrics and analysis

Author: Phase 4 Multi-Task Learning Implementation
Date: 2025-10-31
"""

import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from tqdm import tqdm
from sklearn.metrics import (
    f1_score, precision_score, recall_score, accuracy_score,
    classification_report, confusion_matrix
)
import json

logger = logging.getLogger(__name__)


class MultiTaskEvaluator:
    """
    Comprehensive evaluator for multi-task models.

    Features:
    - Task-specific metrics (F1, precision, recall, accuracy)
    - Confusion matrices
    - Per-class performance
    - Negative transfer detection
    - Comparison to baselines

    Args:
        model: Multi-task model
        device: Evaluation device
    """

    def __init__(self, model, device: torch.device):
        self.model = model
        self.device = device
        self.model.to(device)
        self.model.eval()

    def evaluate_classification(self, dataloader) -> Dict[str, float]:
        """
        Evaluate classification task.

        Args:
            dataloader: DataLoader with classification samples

        Returns:
            metrics: Dictionary of classification metrics
        """
        all_preds = []
        all_labels = []
        all_probs = []

        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Evaluating Classification"):
                # Skip if not classification task
                if batch['task'][0] != 'classification':
                    continue

                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                metadata = batch['metadata'].to(self.device)

                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    metadata=metadata,
                    task='classification',
                    return_auxiliary=False
                )

                logits = outputs['logits']
                probs = torch.softmax(logits, dim=-1)
                preds = torch.argmax(logits, dim=-1)

                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_probs.extend(probs.cpu().numpy())

        if not all_preds:
            logger.warning("No classification samples found in dataloader")
            return {}

        # Compute metrics
        metrics = {
            'f1': f1_score(all_labels, all_preds, average='binary'),
            'precision': precision_score(all_labels, all_preds, average='binary'),
            'recall': recall_score(all_labels, all_preds, average='binary'),
            'accuracy': accuracy_score(all_labels, all_preds)
        }

        # Confusion matrix
        cm = confusion_matrix(all_labels, all_preds)
        metrics['confusion_matrix'] = cm.tolist()

        # Classification report
        report = classification_report(
            all_labels,
            all_preds,
            labels=[0, 1],  # Explicitly specify expected labels
            target_names=['Non-Resource', 'Resource'],
            output_dict=True,
            zero_division=0
        )
        metrics['classification_report'] = report

        return metrics

    def evaluate_ner(self, dataloader) -> Dict[str, float]:
        """
        Evaluate NER task.

        Args:
            dataloader: DataLoader with NER samples

        Returns:
            metrics: Dictionary of NER metrics
        """
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Evaluating NER"):
                # Skip if not NER task
                if batch['task'][0] != 'ner':
                    continue

                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                metadata = batch['metadata'].to(self.device)

                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    metadata=metadata,
                    task='ner',
                    return_auxiliary=False
                )

                logits = outputs['logits']
                preds = torch.argmax(logits, dim=-1)

                # Flatten and filter out ignored labels
                preds_flat = preds.view(-1).cpu().numpy()
                labels_flat = labels.view(-1).cpu().numpy()

                # Filter out padding/special tokens
                mask = labels_flat != -100
                all_preds.extend(preds_flat[mask])
                all_labels.extend(labels_flat[mask])

        if not all_preds:
            logger.warning("No NER samples found in dataloader")
            return {}

        # Compute metrics
        metrics = {
            'f1_macro': f1_score(all_labels, all_preds, average='macro'),
            'f1_micro': f1_score(all_labels, all_preds, average='micro'),
            'precision_macro': precision_score(all_labels, all_preds, average='macro'),
            'recall_macro': recall_score(all_labels, all_preds, average='macro'),
            'accuracy': accuracy_score(all_labels, all_preds)
        }

        # Per-class metrics
        label_names = ['O', 'B-RESOURCE', 'I-RESOURCE']
        report = classification_report(
            all_labels,
            all_preds,
            labels=[0, 1, 2],  # Explicitly specify expected labels
            target_names=label_names,
            output_dict=True,
            zero_division=0
        )
        metrics['classification_report'] = report

        # Confusion matrix
        cm = confusion_matrix(all_labels, all_preds)
        metrics['confusion_matrix'] = cm.tolist()

        return metrics

    def evaluate_both_tasks(self, dataloader) -> Dict[str, Dict]:
        """
        Evaluate both classification and NER tasks.

        Args:
            dataloader: DataLoader with both task types

        Returns:
            results: Dictionary with 'classification' and 'ner' metrics
        """
        results = {
            'classification': self.evaluate_classification(dataloader),
            'ner': self.evaluate_ner(dataloader)
        }

        # Compute combined metrics
        if results['classification'] and results['ner']:
            results['combined'] = {
                'avg_f1': 0.5 * results['classification']['f1'] + 0.5 * results['ner']['f1_macro'],
                'weighted_f1': 0.3 * results['classification']['f1'] + 0.7 * results['ner']['f1_macro']
            }

        return results


def compare_to_baseline(
    mtl_metrics: Dict,
    baseline_metrics: Dict,
    task: str = 'classification'
) -> Dict:
    """
    Compare multi-task learning results to single-task baseline.

    Args:
        mtl_metrics: Metrics from multi-task model
        baseline_metrics: Metrics from single-task baseline
        task: Task name ('classification' or 'ner')

    Returns:
        comparison: Dictionary with comparison results
    """
    if task not in mtl_metrics or task not in baseline_metrics:
        logger.warning(f"Task '{task}' not found in metrics")
        return {}

    mtl = mtl_metrics[task]
    baseline = baseline_metrics[task]

    # Determine primary metric
    f1_key = 'f1' if task == 'classification' else 'f1_macro'

    mtl_f1 = mtl.get(f1_key, 0)
    baseline_f1 = baseline.get(f1_key, 0)

    comparison = {
        'task': task,
        'mtl_f1': mtl_f1,
        'baseline_f1': baseline_f1,
        'improvement': mtl_f1 - baseline_f1,
        'improvement_pct': ((mtl_f1 - baseline_f1) / baseline_f1 * 100) if baseline_f1 > 0 else 0,
        'mtl_better': mtl_f1 > baseline_f1
    }

    return comparison


def detect_negative_transfer(
    mtl_f1: float,
    baseline_f1: float,
    threshold: float = 0.85
) -> Tuple[bool, Dict]:
    """
    Detect if multi-task learning is hurting performance (negative transfer).

    Negative transfer occurs when MTL performance is significantly worse
    than single-task baseline.

    Args:
        mtl_f1: F1 score from multi-task model
        baseline_f1: F1 score from single-task baseline
        threshold: Acceptable ratio (default: 0.85 = 15% degradation allowed)

    Returns:
        is_negative: True if negative transfer detected
        analysis: Dictionary with detailed analysis
    """
    ratio = mtl_f1 / baseline_f1 if baseline_f1 > 0 else 0
    is_negative = ratio < threshold

    analysis = {
        'mtl_f1': mtl_f1,
        'baseline_f1': baseline_f1,
        'ratio': ratio,
        'threshold': threshold,
        'negative_transfer': is_negative,
        'degradation_pct': (1 - ratio) * 100 if ratio > 0 else 100,
        'status': 'NEGATIVE TRANSFER DETECTED' if is_negative else 'OK'
    }

    return is_negative, analysis


def generate_evaluation_report(
    results: Dict,
    baseline_metrics: Optional[Dict] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate comprehensive evaluation report.

    Args:
        results: Evaluation results from MultiTaskEvaluator
        baseline_metrics: Optional baseline metrics for comparison
        output_path: Optional path to save report

    Returns:
        report: Formatted report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("MULTI-TASK LEARNING EVALUATION REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Classification results
    if 'classification' in results and results['classification']:
        classif = results['classification']
        lines.append("CLASSIFICATION TASK")
        lines.append("-" * 80)
        lines.append(f"  F1 Score:       {classif['f1']:.4f}")
        lines.append(f"  Precision:      {classif['precision']:.4f}")
        lines.append(f"  Recall:         {classif['recall']:.4f}")
        lines.append(f"  Accuracy:       {classif['accuracy']:.4f}")
        lines.append("")

        if 'classification_report' in classif:
            lines.append("  Per-Class Metrics:")
            report = classif['classification_report']
            for label in ['Non-Resource', 'Resource']:
                if label in report:
                    lines.append(f"    {label}:")
                    lines.append(f"      Precision: {report[label]['precision']:.4f}")
                    lines.append(f"      Recall:    {report[label]['recall']:.4f}")
                    lines.append(f"      F1:        {report[label]['f1-score']:.4f}")
        lines.append("")

    # NER results
    if 'ner' in results and results['ner']:
        ner = results['ner']
        lines.append("NER TASK")
        lines.append("-" * 80)
        lines.append(f"  F1 Score (Macro):  {ner['f1_macro']:.4f}")
        lines.append(f"  F1 Score (Micro):  {ner['f1_micro']:.4f}")
        lines.append(f"  Precision (Macro): {ner['precision_macro']:.4f}")
        lines.append(f"  Recall (Macro):    {ner['recall_macro']:.4f}")
        lines.append(f"  Accuracy:          {ner['accuracy']:.4f}")
        lines.append("")

        if 'classification_report' in ner:
            lines.append("  Per-Label Metrics:")
            report = ner['classification_report']
            for label in ['O', 'B-RESOURCE', 'I-RESOURCE']:
                if label in report:
                    lines.append(f"    {label}:")
                    lines.append(f"      Precision: {report[label]['precision']:.4f}")
                    lines.append(f"      Recall:    {report[label]['recall']:.4f}")
                    lines.append(f"      F1:        {report[label]['f1-score']:.4f}")
        lines.append("")

    # Combined metrics
    if 'combined' in results:
        combined = results['combined']
        lines.append("COMBINED METRICS")
        lines.append("-" * 80)
        lines.append(f"  Average F1:          {combined['avg_f1']:.4f}")
        lines.append(f"  Weighted F1 (0.3/0.7): {combined['weighted_f1']:.4f}")
        lines.append("")

    # Baseline comparison
    if baseline_metrics:
        lines.append("COMPARISON TO BASELINE")
        lines.append("-" * 80)

        if 'classification' in results and 'classification' in baseline_metrics:
            comparison = compare_to_baseline(results, baseline_metrics, 'classification')
            lines.append("  Classification:")
            lines.append(f"    MTL F1:        {comparison['mtl_f1']:.4f}")
            lines.append(f"    Baseline F1:   {comparison['baseline_f1']:.4f}")
            lines.append(f"    Improvement:   {comparison['improvement']:+.4f} ({comparison['improvement_pct']:+.2f}%)")
            lines.append(f"    Status:        {'✓ BETTER' if comparison['mtl_better'] else '✗ WORSE'}")
            lines.append("")

        if 'ner' in results and 'ner' in baseline_metrics:
            comparison = compare_to_baseline(results, baseline_metrics, 'ner')
            lines.append("  NER:")
            lines.append(f"    MTL F1:        {comparison['mtl_f1']:.4f}")
            lines.append(f"    Baseline F1:   {comparison['baseline_f1']:.4f}")
            lines.append(f"    Improvement:   {comparison['improvement']:+.4f} ({comparison['improvement_pct']:+.2f}%)")
            lines.append(f"    Status:        {'✓ BETTER' if comparison['mtl_better'] else '✗ WORSE'}")
            lines.append("")

    lines.append("=" * 80)

    report = "\n".join(lines)

    # Save to file if specified
    if output_path:
        with open(output_path, 'w') as f:
            f.write(report)
        logger.info(f"Report saved to: {output_path}")

    return report


def load_checkpoint_and_evaluate(
    checkpoint_path: str,
    dataloader,
    device: torch.device,
    baseline_metrics: Optional[Dict] = None
) -> Dict:
    """
    Load checkpoint and evaluate model.

    Args:
        checkpoint_path: Path to model checkpoint
        dataloader: Evaluation dataloader
        device: Evaluation device
        baseline_metrics: Optional baseline for comparison

    Returns:
        results: Evaluation results
    """
    from src.models.multitask_model import BiomedicalMultiTaskModel

    logger.info(f"Loading checkpoint: {checkpoint_path}")

    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)

    # Create model (need config from checkpoint)
    config = checkpoint.get('config', {})
    model = BiomedicalMultiTaskModel(
        model_name_or_path=config.get('model_name_or_path', 'roberta-base'),
        n_metadata_features=config.get('n_metadata_features', 34)
    )

    # Load state dict
    model.load_state_dict(checkpoint['model_state_dict'])

    # Evaluate
    evaluator = MultiTaskEvaluator(model, device)
    results = evaluator.evaluate_both_tasks(dataloader)

    # Generate report
    report = generate_evaluation_report(results, baseline_metrics)
    print(report)

    return results


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description='Evaluate Multi-Task Model')
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to model checkpoint')
    parser.add_argument('--data_classif', type=str, required=True,
                        help='Path to classification test data')
    parser.add_argument('--data_ner', type=str, required=True,
                        help='Path to NER test data')
    parser.add_argument('--output', type=str, default='evaluation_report.txt',
                        help='Output report path')
    parser.add_argument('--baseline', type=str, default=None,
                        help='Path to baseline metrics JSON (optional)')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Load baseline if provided
    baseline_metrics = None
    if args.baseline:
        with open(args.baseline) as f:
            baseline_metrics = json.load(f)

    # Create dataloader
    from src.data.multitask_dataloader import create_multitask_dataloaders

    _, test_loader = create_multitask_dataloaders(
        classif_train_path=args.data_classif,
        ner_train_path=args.data_ner,
        batch_size=16,
        test_mode=False
    )

    # Evaluate
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    results = load_checkpoint_and_evaluate(
        checkpoint_path=args.checkpoint,
        dataloader=test_loader,
        device=device,
        baseline_metrics=baseline_metrics
    )

    # Save results
    results_path = Path(args.output).parent / 'evaluation_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to: {results_path}")
