"""
Experimental Training Utilities for Biodata Inventory ML Pipeline
================================================================

This module contains utilities for experimental training workflows, including
early stopping, experiment tracking, and performance optimization tools.

Created: 2025-10-29
Purpose: Support systematic hyperparameter tuning and experimental training pipelines
"""

import os
import csv
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import torch
import matplotlib.pyplot as plt
import seaborn as sns


# ==========================================
# EARLY STOPPING
# ==========================================

class EarlyStopping:
    """
    Early stopping mechanism for training based on validation metrics.

    Monitors validation F1 score and stops training when performance
    stops improving, preventing overfitting.

    Example:
        early_stopping = EarlyStopping(patience=3, min_delta=0.001)

        for epoch in range(num_epochs):
            train_model()
            val_f1 = evaluate_model()

            if early_stopping(epoch, val_f1, model):
                print(f"Stopped at epoch {early_stopping.best_epoch}")
                model = early_stopping.best_model
                break
    """

    def __init__(
        self,
        patience: int = 3,
        min_delta: float = 0.0,
        output_dir: Optional[str] = None
    ):
        """
        Initialize early stopping.

        Args:
            patience: Number of epochs with no improvement before stopping
            min_delta: Minimum change in metric to qualify as improvement
            output_dir: Directory to save best model checkpoint
        """
        self.patience = patience
        self.min_delta = min_delta
        self.output_dir = output_dir

        self.best_score = -float('inf')
        self.best_epoch = 0
        self.best_model = None
        self.counter = 0
        self.should_stop = False
        self.stop_reason = None

    def __call__(
        self,
        epoch: int,
        val_metric: float,
        model: Any
    ) -> bool:
        """
        Check if training should stop.

        Args:
            epoch: Current epoch number
            val_metric: Validation metric value (F1 score)
            model: Current model state

        Returns:
            True if training should stop, False otherwise
        """
        # FIX M1: Add input validation to prevent silent failures
        import math
        if not isinstance(epoch, int) or epoch < 0:
            raise ValueError(f"epoch must be non-negative integer, got {epoch}")
        if not isinstance(val_metric, (int, float)) or math.isnan(val_metric) or math.isinf(val_metric):
            raise ValueError(f"val_metric must be valid finite number, got {val_metric}")

        # FIX H1: Use >= for proper threshold handling with min_delta
        # This ensures that improvements exactly equal to min_delta are counted
        if val_metric >= self.best_score + self.min_delta:
            self.best_score = val_metric
            self.best_epoch = epoch

            # FIX H2: Store state_dict instead of model reference to avoid mutation issues
            # We save to disk and rely on checkpoint loading rather than in-memory storage
            # This prevents issues where the stored model reference gets mutated during training
            import copy
            self.best_model = copy.deepcopy(model.state_dict())
            self.counter = 0

            # Save checkpoint if output directory specified
            if self.output_dir:
                checkpoint_path = os.path.join(
                    self.output_dir,
                    f"best_model_epoch{epoch}_f1{val_metric:.4f}.pt"
                )
                torch.save(model.state_dict(), checkpoint_path)

            return False
        else:
            self.counter += 1

            if self.counter >= self.patience:
                self.should_stop = True
                self.stop_reason = f"No improvement for {self.patience} epochs"
                return True

        return False

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of early stopping results.

        Returns:
            Dictionary with best epoch, score, and stopping reason
        """
        return {
            'best_epoch': self.best_epoch,
            'best_score': self.best_score,
            'stopped_early': self.should_stop,
            'stop_reason': self.stop_reason,
            'epochs_waited': self.counter
        }


# ==========================================
# EXPERIMENT TRACKING
# ==========================================

class ExperimentTracker:
    """
    Track and manage multiple training experiments.

    Records training configurations, metrics, and results across different
    hyperparameter settings for easy comparison and analysis.

    Example:
        tracker = ExperimentTracker(session_id="2025-10-29-abc123")

        for config in configs:
            tracker.start_experiment(config)
            results = train_model(config)
            tracker.record_results(results)

        tracker.save_results()
        tracker.generate_comparison_report()
    """

    def __init__(self, session_id: str, output_dir: str = "experiments"):
        """
        Initialize experiment tracker.

        Args:
            session_id: Unique identifier for this experimental session
            output_dir: Base directory for experiment outputs
        """
        self.session_id = session_id
        self.output_dir = Path(output_dir) / session_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.experiments = []
        self.current_experiment = None
        self.start_time = datetime.now()

    def start_experiment(self, config: Dict[str, Any]) -> None:
        """
        Start tracking a new experiment.

        Args:
            config: Configuration dictionary for this experiment
        """
        self.current_experiment = {
            'config': config.copy(),
            'experiment_id': f"{self.session_id}_exp{len(self.experiments) + 1}",
            'start_time': datetime.now().isoformat(),
            'metrics': {},
            'status': 'running'
        }

        print(f"\n{'='*60}")
        print(f"Starting Experiment {len(self.experiments) + 1}")
        print(f"Config: {config}")
        print(f"{'='*60}\n")

    def record_results(
        self,
        classif_results: Dict[str, Any],
        ner_results: Dict[str, Any],
        training_time: float
    ) -> None:
        """
        Record results from a completed experiment.

        Args:
            classif_results: Classification training results
            ner_results: NER training results
            training_time: Total training time in seconds
        """
        if self.current_experiment is None:
            raise ValueError("No active experiment. Call start_experiment() first.")

        self.current_experiment['metrics'] = {
            'classification': classif_results,
            'ner': ner_results,
            'training_time_seconds': training_time
        }
        self.current_experiment['end_time'] = datetime.now().isoformat()
        self.current_experiment['status'] = 'completed'

        self.experiments.append(self.current_experiment)
        self.current_experiment = None

    def record_failure(self, error: Exception) -> None:
        """
        Record a failed experiment (legacy method for backward compatibility).

        Args:
            error: Exception that caused the failure
        """
        if self.current_experiment is None:
            raise ValueError("No active experiment. Call start_experiment() first.")

        self.current_experiment['status'] = 'failed'
        self.current_experiment['error'] = str(error)
        self.current_experiment['end_time'] = datetime.now().isoformat()

        self.experiments.append(self.current_experiment)
        self.current_experiment = None

    def record_experiment_failure(
        self,
        exp_id: str,
        config: Dict[str, Any],
        error_msg: str,
        full_traceback: Optional[str] = None,
        log_file: Optional[Path] = None
    ) -> None:
        """
        Record failed experiment with enhanced error details.

        Args:
            exp_id: Experiment identifier
            config: Configuration dictionary for this experiment
            error_msg: Error message string
            full_traceback: Optional full traceback string for detailed debugging
            log_file: Optional path to log file with training output
        """
        result = {
            'experiment_id': exp_id,
            'status': 'failed',
            **{f'config_{k}': v for k, v in config.items()},
            'error': error_msg,
            'end_time': datetime.now().isoformat()
        }

        # Save full traceback to error details file
        if full_traceback:
            error_file = self.output_dir / f"{exp_id}_error_details.txt"
            with open(error_file, 'w') as f:
                f.write(f"Experiment: {exp_id}\n")
                f.write(f"Error: {error_msg}\n\n")
                f.write("Full Traceback:\n" + "=" * 80 + "\n")
                f.write(full_traceback)
            result['error_file'] = str(error_file.relative_to(self.output_dir.parent))

        # Add log file reference if it exists
        if log_file and log_file.exists():
            result['log_file'] = str(log_file.relative_to(self.output_dir.parent))

        self.experiments.append(result)

    def save_results(self) -> str:
        """
        Save all experiment results to CSV.

        Returns:
            Path to saved results file
        """
        results_file = self.output_dir / "experiment_results.csv"

        rows = []
        for exp in self.experiments:
            row = {
                'experiment_id': exp['experiment_id'],
                'status': exp['status']
            }

            # Add config (handles both completed and failed experiments)
            if 'config' in exp:
                # Completed experiments have nested config
                row.update({f"config_{k}": v for k, v in exp['config'].items()})
            else:
                # Failed experiments have flattened config_* keys
                row.update({k: v for k, v in exp.items() if k.startswith('config_')})

            if exp['status'] == 'completed':
                # Classification metrics
                classif = exp['metrics']['classification']
                row.update({
                    'classif_val_f1': classif.get('val_f1', None),
                    'classif_val_precision': classif.get('val_precision', None),
                    'classif_val_recall': classif.get('val_recall', None),
                    'classif_train_f1': classif.get('train_f1', None),
                    'classif_epochs': classif.get('total_epochs', None),
                    'classif_best_epoch': classif.get('best_epoch', None)
                })

                # NER metrics
                ner = exp['metrics']['ner']
                row.update({
                    'ner_val_f1': ner.get('val_f1', None),
                    'ner_val_precision': ner.get('val_precision', None),
                    'ner_val_recall': ner.get('val_recall', None),
                    'ner_train_f1': ner.get('train_f1', None),
                    'ner_epochs': ner.get('total_epochs', None),
                    'ner_best_epoch': ner.get('best_epoch', None)
                })

                row['training_time_seconds'] = exp['metrics']['training_time_seconds']
            else:
                row['error'] = exp.get('error', 'Unknown error')
                row['error_file'] = exp.get('error_file', None)
                row['log_file'] = exp.get('log_file', None)

            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(results_file, index=False)

        print(f"\nExperiment results saved to: {results_file}")
        return str(results_file)

    def generate_comparison_summary(self) -> str:
        """
        Generate a markdown summary comparing all experiments.

        Returns:
            Path to summary file
        """
        summary_file = self.output_dir / "comparison_summary.md"

        with open(summary_file, 'w') as f:
            f.write(f"# Experiment Session: {self.session_id}\n\n")
            f.write(f"**Date**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Experiments**: {len(self.experiments)}\n\n")

            # Summary statistics
            completed = [e for e in self.experiments if e['status'] == 'completed']
            failed = [e for e in self.experiments if e['status'] == 'failed']

            f.write(f"## Summary\n\n")
            f.write(f"- Completed: {len(completed)}\n")
            f.write(f"- Failed: {len(failed)}\n\n")

            if completed:
                f.write("## Results Comparison\n\n")
                f.write("### Classification Model\n\n")
                f.write("| Experiment | Learning Rate | Val F1 | Val Precision | Val Recall | Best Epoch |\n")
                f.write("|------------|---------------|--------|---------------|------------|------------|\n")

                for exp in completed:
                    config = exp['config']
                    metrics = exp['metrics']['classification']
                    f.write(f"| {exp['experiment_id']} | "
                           f"{config.get('learning_rate', 'N/A')} | "
                           f"{metrics.get('val_f1', 0):.4f} | "
                           f"{metrics.get('val_precision', 0):.4f} | "
                           f"{metrics.get('val_recall', 0):.4f} | "
                           f"{metrics.get('best_epoch', 'N/A')} |\n")

                f.write("\n### NER Model\n\n")
                f.write("| Experiment | Learning Rate | Val F1 | Val Precision | Val Recall | Best Epoch |\n")
                f.write("|------------|---------------|--------|---------------|------------|------------|\n")

                for exp in completed:
                    config = exp['config']
                    metrics = exp['metrics']['ner']
                    f.write(f"| {exp['experiment_id']} | "
                           f"{config.get('learning_rate', 'N/A')} | "
                           f"{metrics.get('val_f1', 0):.4f} | "
                           f"{metrics.get('val_precision', 0):.4f} | "
                           f"{metrics.get('val_recall', 0):.4f} | "
                           f"{metrics.get('best_epoch', 'N/A')} |\n")

                # Best configurations
                f.write("\n## Best Configurations\n\n")

                best_classif = max(completed,
                                  key=lambda x: x['metrics']['classification'].get('val_f1', 0))
                f.write(f"### Best Classification Model\n\n")
                f.write(f"- **Experiment**: {best_classif['experiment_id']}\n")
                f.write(f"- **Config**: {best_classif['config']}\n")
                f.write(f"- **Val F1**: {best_classif['metrics']['classification']['val_f1']:.4f}\n\n")

                best_ner = max(completed,
                              key=lambda x: x['metrics']['ner'].get('val_f1', 0))
                f.write(f"### Best NER Model\n\n")
                f.write(f"- **Experiment**: {best_ner['experiment_id']}\n")
                f.write(f"- **Config**: {best_ner['config']}\n")
                f.write(f"- **Val F1**: {best_ner['metrics']['ner']['val_f1']:.4f}\n\n")

        print(f"Comparison summary saved to: {summary_file}")
        return str(summary_file)

    def create_session_archive(self, archive_base: str = "experiment_archives") -> str:
        """
        Create complete archive of experimental session.

        Args:
            archive_base: Base directory for archives

        Returns:
            Path to archive directory
        """
        archive_dir = Path(archive_base) / self.session_id
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Copy experiment results and summaries
        if (self.output_dir / "experiment_results.csv").exists():
            shutil.copy2(
                self.output_dir / "experiment_results.csv",
                archive_dir / "experiment_results.csv"
            )

        if (self.output_dir / "comparison_summary.md").exists():
            shutil.copy2(
                self.output_dir / "comparison_summary.md",
                archive_dir / "comparison_summary.md"
            )

        # Save experiment metadata
        metadata = {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_experiments': len(self.experiments),
            'completed_experiments': len([e for e in self.experiments if e['status'] == 'completed']),
            'failed_experiments': len([e for e in self.experiments if e['status'] == 'failed'])
        }

        with open(archive_dir / "session_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\nSession archive created: {archive_dir}")
        return str(archive_dir)


# ==========================================
# VISUALIZATION UTILITIES
# ==========================================

def plot_training_curves(
    train_stats: pd.DataFrame,
    output_path: str,
    title: str = "Training Curves"
) -> None:
    """
    Plot training and validation curves.

    Args:
        train_stats: DataFrame with training statistics
        output_path: Path to save plot
        title: Plot title
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(title, fontsize=16)

    # F1 Score
    axes[0, 0].plot(train_stats['epoch'], train_stats['train_f1'],
                    label='Train F1', marker='o')
    axes[0, 0].plot(train_stats['epoch'], train_stats['val_f1'],
                    label='Val F1', marker='s')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('F1 Score')
    axes[0, 0].set_title('F1 Score')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Precision
    axes[0, 1].plot(train_stats['epoch'], train_stats['train_precision'],
                    label='Train Precision', marker='o')
    axes[0, 1].plot(train_stats['epoch'], train_stats['val_precision'],
                    label='Val Precision', marker='s')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Precision')
    axes[0, 1].set_title('Precision')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Recall
    axes[1, 0].plot(train_stats['epoch'], train_stats['train_recall'],
                    label='Train Recall', marker='o')
    axes[1, 0].plot(train_stats['epoch'], train_stats['val_recall'],
                    label='Val Recall', marker='s')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('Recall')
    axes[1, 0].set_title('Recall')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Loss
    axes[1, 1].plot(train_stats['epoch'], train_stats['train_loss'],
                    label='Train Loss', marker='o')
    axes[1, 1].plot(train_stats['epoch'], train_stats['val_loss'],
                    label='Val Loss', marker='s')
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('Loss')
    axes[1, 1].set_title('Loss')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Training curves saved to: {output_path}")


# ==========================================
# REPORTING UTILITIES
# ==========================================

def generate_experiment_report(
    experiment_id: str,
    config: Dict[str, Any],
    classif_stats: pd.DataFrame,
    ner_stats: pd.DataFrame,
    classif_metrics: Dict[str, float],
    ner_metrics: Dict[str, float],
    output_dir: str
) -> str:
    """
    Generate comprehensive markdown report for a single experiment.

    Args:
        experiment_id: Unique experiment identifier
        config: Configuration used for this experiment
        classif_stats: Classification training statistics
        ner_stats: NER training statistics
        classif_metrics: Final classification metrics
        ner_metrics: Final NER metrics
        output_dir: Directory to save report

    Returns:
        Path to generated report
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / f"{experiment_id}_report.md"

    with open(report_path, 'w') as f:
        f.write(f"# Experiment Report: {experiment_id}\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Configuration\n\n")
        f.write("```yaml\n")
        for key, value in config.items():
            f.write(f"{key}: {value}\n")
        f.write("```\n\n")

        f.write("## Classification Model Results\n\n")
        f.write("### Final Metrics\n\n")
        f.write("| Metric | Train | Validation |\n")
        f.write("|--------|-------|------------|\n")
        f.write(f"| F1 Score | {classif_metrics.get('train_f1', 0):.4f} | "
               f"{classif_metrics.get('val_f1', 0):.4f} |\n")
        f.write(f"| Precision | {classif_metrics.get('train_precision', 0):.4f} | "
               f"{classif_metrics.get('val_precision', 0):.4f} |\n")
        f.write(f"| Recall | {classif_metrics.get('train_recall', 0):.4f} | "
               f"{classif_metrics.get('val_recall', 0):.4f} |\n")
        f.write(f"\n**Best Epoch**: {classif_metrics.get('best_epoch', 'N/A')}\n")
        f.write(f"**Total Epochs**: {len(classif_stats)}\n\n")

        f.write("## NER Model Results\n\n")
        f.write("### Final Metrics\n\n")
        f.write("| Metric | Train | Validation |\n")
        f.write("|--------|-------|------------|\n")
        f.write(f"| F1 Score | {ner_metrics.get('train_f1', 0):.4f} | "
               f"{ner_metrics.get('val_f1', 0):.4f} |\n")
        f.write(f"| Precision | {ner_metrics.get('train_precision', 0):.4f} | "
               f"{ner_metrics.get('val_precision', 0):.4f} |\n")
        f.write(f"| Recall | {ner_metrics.get('train_recall', 0):.4f} | "
               f"{ner_metrics.get('val_recall', 0):.4f} |\n")
        f.write(f"\n**Best Epoch**: {ner_metrics.get('best_epoch', 'N/A')}\n")
        f.write(f"**Total Epochs**: {len(ner_stats)}\n\n")

        # Add training curves
        f.write("## Training Curves\n\n")
        f.write("See accompanying PNG files for visualizations.\n\n")

    print(f"Experiment report saved to: {report_path}")
    return str(report_path)


# ==========================================
# GPU OPTIMIZATION UTILITIES
# ==========================================

def calculate_optimal_batch_size(
    model_size_mb: float = 500,
    test_mode: bool = False
) -> int:
    """
    Calculate optimal batch size based on available GPU memory.

    Args:
        model_size_mb: Estimated model size in MB
        test_mode: If True, use smaller batch sizes for testing

    Returns:
        Recommended batch size
    """
    if test_mode:
        return 4  # Small batch size for quick testing

    if not torch.cuda.is_available():
        return 8  # CPU fallback

    # Get available GPU memory
    gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)

    # Reserve memory for model and optimizer states (~3x model size)
    reserved_gb = (model_size_mb * 3) / 1024
    available_gb = gpu_memory_gb - reserved_gb

    # Estimate batch size (conservative estimate)
    if available_gb >= 12:
        return 32
    elif available_gb >= 8:
        return 24
    elif available_gb >= 6:
        return 16
    elif available_gb >= 4:
        return 12
    else:
        return 8
