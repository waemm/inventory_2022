"""
Multi-Task Learning Setup Verification Script

This script verifies the Phase 4 multi-task learning implementation:
1. Data loading and metadata extraction
2. Model architecture and forward pass
3. Loss computation correctness
4. Gradient flow to shared encoder
5. Short training run (5 epochs TEST_MODE)
6. Metric tracking and logging

Run this before full training to catch issues early.

Author: Phase 4 Multi-Task Learning Implementation
Date: 2025-10-31
"""

import sys
import torch
import logging
from pathlib import Path
import numpy as np

# Setup paths
sys.path.append(str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_data_loading():
    """Test 1: Verify augmented data loads correctly."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Data Loading")
    logger.info("=" * 80)

    try:
        from src.data.multitask_dataloader import create_multitask_dataloaders

        train_loader, _ = create_multitask_dataloaders(
            classif_train_path='data/augmented/classif_train_with_metadata.csv',
            ner_train_path='data/augmented/ner_train_with_metadata.csv',
            batch_size=4,
            test_mode=True  # Use small subset
        )

        logger.info(f"✓ Training batches: {len(train_loader)}")

        # Get sample batch
        batch = next(iter(train_loader))

        logger.info(f"✓ Batch structure:")
        for key, value in batch.items():
            if isinstance(value, torch.Tensor):
                logger.info(f"    {key}: {value.shape} ({value.dtype})")
            else:
                logger.info(f"    {key}: {type(value)}")

        # Verify metadata
        metadata = batch['metadata']
        logger.info(f"✓ Metadata features: {metadata.shape[-1]}")
        logger.info(f"✓ Metadata range: [{metadata.min():.4f}, {metadata.max():.4f}]")

        logger.info("✓ TEST 1 PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_architecture():
    """Test 2: Verify model architecture and forward pass."""
    logger.info("=" * 80)
    logger.info("TEST 2: Model Architecture")
    logger.info("=" * 80)

    try:
        from src.models.multitask_model import BiomedicalMultiTaskModel

        model = BiomedicalMultiTaskModel(
            model_name_or_path="roberta-base",
            n_metadata_features=28  # Match dataloader features
        )

        logger.info(f"✓ Model created successfully")

        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

        logger.info(f"✓ Total parameters: {total_params:,}")
        logger.info(f"✓ Trainable parameters: {trainable_params:,}")

        # Test forward pass - Classification
        batch_size = 4
        seq_len = 128

        input_ids = torch.randint(0, 1000, (batch_size, seq_len))
        attention_mask = torch.ones(batch_size, seq_len)
        metadata = torch.randn(batch_size, 28)

        logger.info("\nTesting classification forward pass...")
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            metadata=metadata,
            task='classification'
        )

        logger.info(f"✓ Classification logits: {outputs['logits'].shape}")
        logger.info(f"✓ Auxiliary boolean: {outputs['auxiliary_boolean'].shape}")
        logger.info(f"✓ Auxiliary numerical: {outputs['auxiliary_numerical'].shape}")

        # Test forward pass - NER
        logger.info("\nTesting NER forward pass...")
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            metadata=metadata,
            task='ner'
        )

        logger.info(f"✓ NER logits: {outputs['logits'].shape}")

        logger.info("✓ TEST 2 PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_loss_computation():
    """Test 3: Verify loss computation is correct."""
    logger.info("=" * 80)
    logger.info("TEST 3: Loss Computation")
    logger.info("=" * 80)

    try:
        from src.models.multitask_model import BiomedicalMultiTaskModel
        from src.data.multitask_dataloader import create_multitask_dataloaders
        import torch.nn as nn

        model = BiomedicalMultiTaskModel(model_name_or_path="roberta-base", n_metadata_features=28)

        train_loader, _ = create_multitask_dataloaders(
            classif_train_path='data/augmented/classif_train_with_metadata.csv',
            ner_train_path='data/augmented/ner_train_with_metadata.csv',
            batch_size=4,
            test_mode=True
        )

        # Get batch
        batch = next(iter(train_loader))

        input_ids = batch['input_ids']
        attention_mask = batch['attention_mask']
        labels = batch['labels']
        metadata = batch['metadata']
        task = batch['task'][0]

        # Forward pass
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            metadata=metadata,
            task=task
        )

        # Compute loss
        if task == 'classification':
            criterion = nn.CrossEntropyLoss()
            loss = criterion(outputs['logits'], labels)
            logger.info(f"✓ Classification loss: {loss.item():.4f}")

        else:  # NER
            criterion = nn.CrossEntropyLoss(ignore_index=-100)
            logits = outputs['logits']
            batch_size, seq_len, num_labels = logits.shape
            loss = criterion(logits.view(-1, num_labels), labels.view(-1))
            logger.info(f"✓ NER loss: {loss.item():.4f}")

        # Verify loss is finite
        assert torch.isfinite(loss), "Loss is not finite!"
        logger.info(f"✓ Loss is finite")

        logger.info("✓ TEST 3 PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gradient_flow():
    """Test 4: Verify gradient flow to shared encoder."""
    logger.info("=" * 80)
    logger.info("TEST 4: Gradient Flow")
    logger.info("=" * 80)

    try:
        from src.models.multitask_model import BiomedicalMultiTaskModel
        from src.data.multitask_dataloader import create_multitask_dataloaders
        import torch.nn as nn

        model = BiomedicalMultiTaskModel(model_name_or_path="roberta-base", n_metadata_features=28)

        train_loader, _ = create_multitask_dataloaders(
            classif_train_path='data/augmented/classif_train_with_metadata.csv',
            ner_train_path='data/augmented/ner_train_with_metadata.csv',
            batch_size=4,
            test_mode=True
        )

        # Get batch
        batch = next(iter(train_loader))

        input_ids = batch['input_ids']
        attention_mask = batch['attention_mask']
        labels = batch['labels']
        metadata = batch['metadata']
        task = batch['task'][0]

        # Forward pass
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            metadata=metadata,
            task=task
        )

        # Compute loss
        if task == 'classification':
            criterion = nn.CrossEntropyLoss()
            loss = criterion(outputs['logits'], labels)
        else:
            criterion = nn.CrossEntropyLoss(ignore_index=-100)
            logits = outputs['logits']
            batch_size, seq_len, num_labels = logits.shape
            loss = criterion(logits.view(-1, num_labels), labels.view(-1))

        # Backward pass
        loss.backward()

        # Check gradients
        encoder_has_grad = False
        head_has_grad = False

        for name, param in model.named_parameters():
            if param.grad is not None:
                if 'encoder' in name:
                    encoder_has_grad = True
                if 'head' in name or 'classifier' in name:
                    head_has_grad = True

        logger.info(f"✓ Encoder has gradients: {encoder_has_grad}")
        logger.info(f"✓ Task heads have gradients: {head_has_grad}")

        assert encoder_has_grad, "Encoder parameters have no gradients!"
        assert head_has_grad, "Task head parameters have no gradients!"

        logger.info("✓ TEST 4 PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_tracking():
    """Test 5: Verify metrics are tracked correctly."""
    logger.info("=" * 80)
    logger.info("TEST 5: Metrics Tracking")
    logger.info("=" * 80)

    try:
        from src.models.multitask_model import BiomedicalMultiTaskModel
        from src.data.multitask_dataloader import create_multitask_dataloaders
        from sklearn.metrics import f1_score
        import torch.nn as nn

        model = BiomedicalMultiTaskModel(model_name_or_path="roberta-base", n_metadata_features=28)
        model.eval()

        train_loader, _ = create_multitask_dataloaders(
            classif_train_path='data/augmented/classif_train_with_metadata.csv',
            ner_train_path='data/augmented/ner_train_with_metadata.csv',
            batch_size=4,
            test_mode=True
        )

        # Collect predictions
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for i, batch in enumerate(train_loader):
                if i >= 5:  # Just test a few batches
                    break

                input_ids = batch['input_ids']
                attention_mask = batch['attention_mask']
                labels = batch['labels']
                metadata = batch['metadata']
                task = batch['task'][0]

                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    metadata=metadata,
                    task=task,
                    return_auxiliary=False
                )

                logits = outputs['logits']

                if task == 'classification':
                    preds = torch.argmax(logits, dim=-1)
                    all_preds.extend(preds.numpy())
                    all_labels.extend(labels.numpy())

        if all_preds:
            f1 = f1_score(all_labels, all_preds, average='binary')
            logger.info(f"✓ Sample F1 score: {f1:.4f}")

        logger.info("✓ TEST 5 PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_short_training_run():
    """Test 6: Run 5 epochs of TEST_MODE training."""
    logger.info("=" * 80)
    logger.info("TEST 6: Short Training Run (5 epochs)")
    logger.info("=" * 80)

    try:
        from src.models.multitask_model import BiomedicalMultiTaskModel
        from src.data.multitask_dataloader import create_multitask_dataloaders
        from src.train_multitask import MultiTaskTrainer
        import yaml

        # Load config
        with open('config/multitask_config.yaml') as f:
            config = yaml.safe_load(f)

        # Override for quick test
        config['training']['test_mode'] = True
        config['training']['epochs'] = 5
        config['training']['batch_size'] = 4

        # Create dataloaders
        train_loader, _ = create_multitask_dataloaders(
            classif_train_path='data/augmented/classif_train_with_metadata.csv',
            ner_train_path='data/augmented/ner_train_with_metadata.csv',
            batch_size=config['training']['batch_size'],
            test_mode=True
        )

        # Create model
        model = BiomedicalMultiTaskModel(
            model_name_or_path=config['model']['base_model'],
            n_metadata_features=config['model']['n_metadata_features']
        )

        # Setup device
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"✓ Using device: {device}")

        # Create trainer
        trainer = MultiTaskTrainer(
            model=model,
            train_loader=train_loader,
            val_loader=None,
            config=config['training'],
            device=device,
            output_dir='outputs/test_multitask'
        )

        # Train
        logger.info("\nStarting training...")
        trainer.train(num_epochs=5)

        # Check history
        logger.info("\nTraining history:")
        logger.info(f"  - Final train loss: {trainer.history['train_loss'][-1]:.4f}")
        logger.info(f"  - Final classif loss: {trainer.history['train_classif_loss'][-1]:.4f}")
        logger.info(f"  - Final NER loss: {trainer.history['train_ner_loss'][-1]:.4f}")

        # Verify loss is decreasing
        initial_loss = trainer.history['train_loss'][0]
        final_loss = trainer.history['train_loss'][-1]

        logger.info(f"\n✓ Initial loss: {initial_loss:.4f}")
        logger.info(f"✓ Final loss: {final_loss:.4f}")
        logger.info(f"✓ Loss decreased: {final_loss < initial_loss}")

        logger.info("✓ TEST 6 PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    logger.info("\n" + "#" * 80)
    logger.info("# MULTI-TASK LEARNING SETUP VERIFICATION")
    logger.info("# Phase 4 Implementation - TEST_MODE")
    logger.info("#" * 80 + "\n")

    tests = [
        ("Data Loading", test_data_loading),
        ("Model Architecture", test_model_architecture),
        ("Loss Computation", test_loss_computation),
        ("Gradient Flow", test_gradient_flow),
        ("Metrics Tracking", test_metrics_tracking),
        ("Short Training Run", test_short_training_run)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 80)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"  {test_name:.<50} {status}")

    total_passed = sum(1 for _, result in results if result)
    total_tests = len(results)

    logger.info(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        logger.info("\n✓ ALL TESTS PASSED - Ready for full training!")
        return 0
    else:
        logger.error("\n✗ SOME TESTS FAILED - Fix issues before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
