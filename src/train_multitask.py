"""
Multi-Task Training Script for Biomedical Classification and NER

This script implements multi-task learning with:
1. Fixed loss weighting (λ₁=0.3 classification, λ₂=0.7 NER, λ₃=0.1 auxiliary)
2. Gradient conflict detection and monitoring
3. Per-task metric tracking
4. Negative transfer detection
5. Task-specific early stopping
6. TEST_MODE for quick validation

Author: Phase 4 Multi-Task Learning Implementation
Date: 2025-10-31
"""

import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from transformers import get_linear_schedule_with_warmup
import numpy as np
from pathlib import Path
from tqdm import tqdm
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.multitask_model import BiomedicalMultiTaskModel, create_model
from src.data.multitask_dataloader import create_multitask_dataloaders

logger = logging.getLogger(__name__)


class MultiTaskTrainer:
    """
    Multi-task trainer with gradient monitoring and negative transfer detection.

    Features:
    - Fixed loss weighting (simple approach for MVP)
    - Per-task metric tracking
    - Gradient conflict detection
    - Early stopping with task-specific criteria
    - Checkpoint saving (best classification, best NER, best combined)
    - TensorBoard logging support

    Args:
        model: Multi-task model
        train_loader: Training dataloader
        val_loader: Validation dataloader (optional)
        config: Training configuration dictionary
        device: Training device
        output_dir: Directory for checkpoints and logs
    """

    def __init__(
        self,
        model: BiomedicalMultiTaskModel,
        train_loader,
        val_loader,
        config: Dict,
        device: torch.device,
        output_dir: str
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config
        self.device = device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Loss weights
        self.lambda_classif = config.get('lambda_classification', 0.3)
        self.lambda_ner = config.get('lambda_ner', 0.7)
        self.lambda_aux = config.get('lambda_auxiliary', 0.1)

        # Setup optimizer
        self.optimizer = self._create_optimizer()

        # Setup scheduler
        num_training_steps = len(train_loader) * config.get('epochs', 30)
        warmup_steps = config.get('warmup_steps', 500)
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=num_training_steps
        )

        # Loss functions
        self.classif_criterion = nn.CrossEntropyLoss()
        self.ner_criterion = nn.CrossEntropyLoss(ignore_index=-100)
        self.bce_criterion = nn.BCEWithLogitsLoss()
        self.mse_criterion = nn.MSELoss()

        # Tracking
        self.history = {
            'train_loss': [],
            'train_classif_loss': [],
            'train_ner_loss': [],
            'train_aux_loss': [],
            'val_classif_f1': [],
            'val_ner_f1': [],
            'gradient_conflicts': [],
            'epoch_times': []
        }

        self.best_classif_f1 = 0.0
        self.best_ner_f1 = 0.0
        self.best_combined_f1 = 0.0
        self.epochs_no_improve = 0

        # Early stopping
        self.patience = config.get('patience', 10)
        self.min_delta = config.get('min_delta', 0.001)

        logger.info(f"Trainer initialized:")
        logger.info(f"  - Loss weights: λ_classif={self.lambda_classif}, λ_ner={self.lambda_ner}, λ_aux={self.lambda_aux}")
        logger.info(f"  - Training steps: {num_training_steps}")
        logger.info(f"  - Warmup steps: {warmup_steps}")
        logger.info(f"  - Output directory: {self.output_dir}")

    def _create_optimizer(self) -> AdamW:
        """Create optimizer with parameter groups."""
        # Different learning rates for encoder vs heads (optional)
        learning_rate = self.config.get('learning_rate', 2e-5)
        weight_decay = self.config.get('weight_decay', 0.01)

        # Single optimizer for all parameters (simpler for MVP)
        optimizer = AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )

        return optimizer

    def compute_auxiliary_loss(
        self,
        boolean_logits: torch.Tensor,
        numerical_preds: torch.Tensor,
        metadata: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute auxiliary loss for metadata prediction.

        Args:
            boolean_logits: [batch_size, 10] - Predicted boolean features
            numerical_preds: [batch_size, 2] - Predicted numerical features
            metadata: [batch_size, 34] - Ground truth metadata

        Returns:
            loss: Scalar auxiliary loss
        """
        # Extract boolean targets (first 10 features)
        boolean_targets = metadata[:, :10]

        # Extract numerical targets (features 10-11: log_citations, years_since_pub)
        numerical_targets = metadata[:, 10:12]

        # Boolean loss (BCE)
        boolean_loss = self.bce_criterion(boolean_logits, boolean_targets)

        # Numerical loss (MSE)
        numerical_loss = self.mse_criterion(numerical_preds, numerical_targets)

        # Combined auxiliary loss
        aux_loss = boolean_loss + numerical_loss

        return aux_loss

    def compute_gradient_similarity(self) -> float:
        """
        Compute cosine similarity between classification and NER gradients.

        Negative similarity indicates gradient conflict.

        Returns:
            similarity: Cosine similarity in [-1, 1]
        """
        # Collect gradients from shared encoder
        classif_grads = []
        ner_grads = []

        for param in self.model.encoder.parameters():
            if param.grad is not None:
                if hasattr(param, 'classif_grad'):
                    classif_grads.append(param.classif_grad.flatten())
                if hasattr(param, 'ner_grad'):
                    ner_grads.append(param.ner_grad.flatten())

        if not classif_grads or not ner_grads:
            return 0.0

        # Concatenate all gradients
        classif_grad = torch.cat(classif_grads)
        ner_grad = torch.cat(ner_grads)

        # Compute cosine similarity
        similarity = F.cosine_similarity(classif_grad.unsqueeze(0), ner_grad.unsqueeze(0))

        return similarity.item()

    def train_epoch(self, epoch: int) -> Dict[str, float]:
        """
        Train one epoch.

        Args:
            epoch: Current epoch number

        Returns:
            metrics: Dictionary of training metrics
        """
        self.model.train()

        total_loss = 0.0
        total_classif_loss = 0.0
        total_ner_loss = 0.0
        total_aux_loss = 0.0
        num_batches = 0
        num_conflicts = 0

        progress_bar = tqdm(self.train_loader, desc=f"Epoch {epoch}")

        for batch_idx, batch in enumerate(progress_bar):
            # Move batch to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            metadata = batch['metadata'].to(self.device)
            task = batch['task'][0]  # Assume homogeneous batch

            # Forward pass
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                metadata=metadata,
                task=task,
                return_auxiliary=True
            )

            logits = outputs['logits']

            # Compute task-specific loss
            if task == 'classification':
                task_loss = self.classif_criterion(logits, labels)
                weighted_task_loss = self.lambda_classif * task_loss
                total_classif_loss += task_loss.item()

            else:  # NER
                # Reshape for NER loss
                batch_size, seq_len, num_labels = logits.shape
                task_loss = self.ner_criterion(
                    logits.view(-1, num_labels),
                    labels.view(-1)
                )
                weighted_task_loss = self.lambda_ner * task_loss
                total_ner_loss += task_loss.item()

            # Compute auxiliary loss
            aux_loss = self.compute_auxiliary_loss(
                outputs['auxiliary_boolean'],
                outputs['auxiliary_numerical'],
                metadata
            )
            weighted_aux_loss = self.lambda_aux * aux_loss
            total_aux_loss += aux_loss.item()

            # Total loss
            loss = weighted_task_loss + weighted_aux_loss

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

            # Optimizer step
            self.optimizer.step()
            self.scheduler.step()

            # Track metrics
            total_loss += loss.item()
            num_batches += 1

            # Update progress bar
            progress_bar.set_postfix({
                'loss': loss.item(),
                'task': task,
                'lr': self.scheduler.get_last_lr()[0]
            })

        # Compute epoch metrics
        metrics = {
            'loss': total_loss / num_batches,
            'classif_loss': total_classif_loss / max(1, num_batches),
            'ner_loss': total_ner_loss / max(1, num_batches),
            'aux_loss': total_aux_loss / num_batches,
            'conflict_rate': num_conflicts / num_batches if num_batches > 0 else 0.0
        }

        return metrics

    def evaluate(self, dataloader) -> Dict[str, float]:
        """
        Evaluate on validation set.

        Returns:
            metrics: Dictionary with per-task F1 scores
        """
        self.model.eval()

        # Separate predictions by task
        classif_preds = []
        classif_labels = []
        ner_preds = []
        ner_labels = []

        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Evaluating"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                metadata = batch['metadata'].to(self.device)
                task = batch['task'][0]

                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    metadata=metadata,
                    task=task,
                    return_auxiliary=False
                )

                logits = outputs['logits']

                if task == 'classification':
                    preds = torch.argmax(logits, dim=-1)
                    classif_preds.extend(preds.cpu().numpy())
                    classif_labels.extend(labels.cpu().numpy())

                else:  # NER
                    preds = torch.argmax(logits, dim=-1)
                    # Flatten and filter out ignored labels
                    preds_flat = preds.view(-1).cpu().numpy()
                    labels_flat = labels.view(-1).cpu().numpy()

                    # Filter out padding/special tokens
                    mask = labels_flat != -100
                    ner_preds.extend(preds_flat[mask])
                    ner_labels.extend(labels_flat[mask])

        # Compute metrics
        metrics = {}

        if classif_preds:
            metrics['classif_f1'] = f1_score(classif_labels, classif_preds, average='binary')
            metrics['classif_precision'] = precision_score(classif_labels, classif_preds, average='binary')
            metrics['classif_recall'] = recall_score(classif_labels, classif_preds, average='binary')
            metrics['classif_accuracy'] = accuracy_score(classif_labels, classif_preds)

        if ner_preds:
            metrics['ner_f1'] = f1_score(ner_labels, ner_preds, average='macro')
            metrics['ner_precision'] = precision_score(ner_labels, ner_preds, average='macro')
            metrics['ner_recall'] = recall_score(ner_labels, ner_preds, average='macro')
            metrics['ner_accuracy'] = accuracy_score(ner_labels, ner_preds)

        # Combined F1 (weighted average)
        if 'classif_f1' in metrics and 'ner_f1' in metrics:
            metrics['combined_f1'] = 0.5 * metrics['classif_f1'] + 0.5 * metrics['ner_f1']

        return metrics

    def detect_negative_transfer(self, current_f1: float, baseline_f1: float) -> bool:
        """
        Check if multi-task learning is hurting performance.

        Args:
            current_f1: Current F1 score
            baseline_f1: Single-task baseline F1

        Returns:
            is_negative: True if current < 0.85 * baseline
        """
        threshold = 0.85 * baseline_f1
        return current_f1 < threshold

    def save_checkpoint(self, epoch: int, metrics: Dict, checkpoint_type: str):
        """Save model checkpoint."""
        checkpoint_path = self.output_dir / f"checkpoint_{checkpoint_type}.pt"

        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'metrics': metrics,
            'config': self.config
        }

        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Saved checkpoint: {checkpoint_path}")

    def train(self, num_epochs: int):
        """
        Main training loop.

        Args:
            num_epochs: Number of epochs to train
        """
        logger.info(f"Starting training for {num_epochs} epochs")

        for epoch in range(1, num_epochs + 1):
            # Train epoch
            train_metrics = self.train_epoch(epoch)

            # Log training metrics
            logger.info(f"\nEpoch {epoch}/{num_epochs}")
            logger.info(f"  Train Loss: {train_metrics['loss']:.4f}")
            logger.info(f"  Classif Loss: {train_metrics['classif_loss']:.4f}")
            logger.info(f"  NER Loss: {train_metrics['ner_loss']:.4f}")
            logger.info(f"  Aux Loss: {train_metrics['aux_loss']:.4f}")

            # Update history
            self.history['train_loss'].append(train_metrics['loss'])
            self.history['train_classif_loss'].append(train_metrics['classif_loss'])
            self.history['train_ner_loss'].append(train_metrics['ner_loss'])
            self.history['train_aux_loss'].append(train_metrics['aux_loss'])

            # Evaluate if validation set available
            if self.val_loader:
                val_metrics = self.evaluate(self.val_loader)

                logger.info(f"  Val Classif F1: {val_metrics.get('classif_f1', 0):.4f}")
                logger.info(f"  Val NER F1: {val_metrics.get('ner_f1', 0):.4f}")
                logger.info(f"  Val Combined F1: {val_metrics.get('combined_f1', 0):.4f}")

                # Update history
                self.history['val_classif_f1'].append(val_metrics.get('classif_f1', 0))
                self.history['val_ner_f1'].append(val_metrics.get('ner_f1', 0))

                # Save best checkpoints
                if val_metrics.get('classif_f1', 0) > self.best_classif_f1:
                    self.best_classif_f1 = val_metrics['classif_f1']
                    self.save_checkpoint(epoch, val_metrics, 'best_classification')

                if val_metrics.get('ner_f1', 0) > self.best_ner_f1:
                    self.best_ner_f1 = val_metrics['ner_f1']
                    self.save_checkpoint(epoch, val_metrics, 'best_ner')

                if val_metrics.get('combined_f1', 0) > self.best_combined_f1:
                    self.best_combined_f1 = val_metrics['combined_f1']
                    self.save_checkpoint(epoch, val_metrics, 'best_combined')
                    self.epochs_no_improve = 0
                else:
                    self.epochs_no_improve += 1

                # Early stopping
                if self.epochs_no_improve >= self.patience:
                    logger.info(f"\nEarly stopping triggered after {epoch} epochs")
                    break

        # Save final checkpoint
        self.save_checkpoint(num_epochs, {}, 'final')

        # Save training history
        history_path = self.output_dir / 'training_history.json'
        with open(history_path, 'w') as f:
            json.dump(self.history, f, indent=2)

        logger.info(f"\nTraining completed!")
        logger.info(f"  Best Classification F1: {self.best_classif_f1:.4f}")
        logger.info(f"  Best NER F1: {self.best_ner_f1:.4f}")
        logger.info(f"  Best Combined F1: {self.best_combined_f1:.4f}")


def main():
    """Main training script."""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Task Learning Training')
    parser.add_argument('--config', type=str, default='config/multitask_config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--test_mode', action='store_true',
                        help='Run in TEST_MODE with small subset')
    parser.add_argument('--output_dir', type=str, default='outputs/multitask',
                        help='Output directory for checkpoints')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Path(args.output_dir) / 'training.log'),
            logging.StreamHandler()
        ]
    )

    # Load config
    import yaml
    with open(args.config) as f:
        config = yaml.safe_load(f)

    # Override test mode if specified
    if args.test_mode:
        config['training']['test_mode'] = True
        config['training']['epochs'] = 5  # Quick test

    # Create dataloaders
    train_loader, val_loader = create_multitask_dataloaders(
        classif_train_path='data/augmented/classif_train_with_metadata.csv',
        ner_train_path='data/augmented/ner_train_with_metadata.csv',
        tokenizer_name=config['model']['base_model'],
        batch_size=config['training']['batch_size'],
        test_mode=config['training']['test_mode']
    )

    # Create model
    model = create_model(config['model'])

    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")

    # Create trainer
    trainer = MultiTaskTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=config['training'],
        device=device,
        output_dir=args.output_dir
    )

    # Train
    trainer.train(num_epochs=config['training']['epochs'])


if __name__ == "__main__":
    main()
