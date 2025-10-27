#!/usr/bin/env python3
"""
Convert PyTorch checkpoints from NamedTuple format to dict-only format.

This script converts existing model checkpoints that contain Metrics NamedTuple
objects to a format that uses only dicts, making them compatible with
PyTorch's weights_only=True loading mode.

CRITICAL: This script MUST be run in the environment where the checkpoints
load correctly (biodata_modern_env with PyTorch 2.0.0). Running in PyTorch 2.8
will convert already-corrupted weights!

Usage:
    source biodata_modern_env/bin/activate
    python convert_checkpoints_to_weights_only.py

Author: Claude Code
Date: 2025-10-27
"""

import hashlib
import sys
from pathlib import Path
from typing import Any, Dict

import torch


def compute_parameter_checksum(state_dict: Dict[str, Any]) -> str:
    """
    Compute MD5 checksum of model parameters.

    Parameters:
    state_dict: Model state dictionary

    Return: 16-character MD5 hex digest
    """
    param_bytes = b''.join([
        p.detach().cpu().numpy().tobytes()
        for p in state_dict.values()
        if isinstance(p, torch.Tensor)
    ])
    return hashlib.md5(param_bytes).hexdigest()[:16]


def convert_checkpoint(
    old_checkpoint_path: str,
    new_checkpoint_path: str,
    expected_checksum: str = None
) -> bool:
    """
    Convert checkpoint from NamedTuple format to dict-only format.

    MUST run in environment where checkpoint loads correctly (PyTorch 2.0)!

    Parameters:
    old_checkpoint_path: Path to existing checkpoint (.pt file)
    new_checkpoint_path: Path to save converted checkpoint
    expected_checksum: Optional expected parameter checksum (for verification)

    Return: True if conversion successful, False otherwise
    """

    print(f"\n{'='*70}")
    print(f"Converting: {old_checkpoint_path}")
    print(f"{'='*70}")

    # Check if old checkpoint exists
    if not Path(old_checkpoint_path).exists():
        print(f"❌ ERROR: File not found: {old_checkpoint_path}")
        return False

    # Get file size
    file_size_mb = Path(old_checkpoint_path).stat().st_size / (1024 * 1024)
    print(f"Original file size: {file_size_mb:.1f} MB")

    # Load with PyTorch 2.0 (weights_only=False is OK here)
    print(f"\nLoading checkpoint with PyTorch {torch.__version__}...")
    try:
        checkpoint = torch.load(
            old_checkpoint_path,
            map_location='cpu',
            weights_only=False
        )
    except Exception as e:
        print(f"❌ ERROR: Failed to load checkpoint: {e}")
        return False

    # Verify we got the expected keys
    expected_keys = {'model_state_dict', 'model_name', 'train_metrics', 'val_metrics'}
    actual_keys = set(checkpoint.keys())

    if not expected_keys.issubset(actual_keys):
        print(f"❌ ERROR: Unexpected checkpoint structure")
        print(f"Expected keys: {expected_keys}")
        print(f"Actual keys: {actual_keys}")
        return False

    print(f"✓ Checkpoint keys: {list(checkpoint.keys())}")
    print(f"✓ Model name: {checkpoint['model_name']}")

    # Compute checksum of original weights
    print(f"\nComputing parameter checksum...")
    original_checksum = compute_parameter_checksum(checkpoint['model_state_dict'])
    print(f"Original checksum: {original_checksum}")

    if expected_checksum:
        print(f"Expected checksum: {expected_checksum}")
        if original_checksum == expected_checksum:
            print(f"✓ Checksum matches expected value")
        else:
            print(f"⚠️  Note: Checksum differs from expected (this is OK if models differ)")

    print(f"✓ This checksum will be preserved in conversion")

    # Convert NamedTuple metrics to dicts
    print(f"\nConverting metrics to dict format...")
    train_metrics = checkpoint['train_metrics']
    val_metrics = checkpoint['val_metrics']

    # Check if already NamedTuple
    if not hasattr(train_metrics, 'precision'):
        print(f"⚠️  WARNING: Metrics don't appear to be NamedTuples")
        print(f"train_metrics type: {type(train_metrics)}")
        print(f"This checkpoint may already be in the new format")
        return False

    print(f"Original train_metrics: {train_metrics}")
    print(f"Original val_metrics: {val_metrics}")

    # Create new checkpoint with only primitives and tensors
    new_checkpoint = {
        'model_state_dict': checkpoint['model_state_dict'],  # Tensors (safe)
        'model_name': checkpoint['model_name'],              # String (safe)
        'train_metrics': {                                   # Dict (safe)
            'precision': float(train_metrics.precision),
            'recall': float(train_metrics.recall),
            'f1': float(train_metrics.f1),
            'loss': float(train_metrics.loss)
        },
        'val_metrics': {                                     # Dict (safe)
            'precision': float(val_metrics.precision),
            'recall': float(val_metrics.recall),
            'f1': float(val_metrics.f1),
            'loss': float(val_metrics.loss)
        }
    }

    # Verify parameter checksum hasn't changed
    print(f"\nVerifying converted checkpoint...")
    new_checksum = compute_parameter_checksum(new_checkpoint['model_state_dict'])
    print(f"Converted checksum: {new_checksum}")

    if new_checksum != original_checksum:
        print(f"❌ ERROR: Checksum changed during conversion!")
        print(f"Conversion has altered the weights somehow.")
        return False
    else:
        print(f"✓ Checksums match - weights preserved correctly")

    # Save in new format
    print(f"\nSaving converted checkpoint to: {new_checkpoint_path}")
    try:
        torch.save(new_checkpoint, new_checkpoint_path)
    except Exception as e:
        print(f"❌ ERROR: Failed to save checkpoint: {e}")
        return False

    # Verify new checkpoint can be loaded with weights_only=True
    print(f"\nVerifying new checkpoint loads with weights_only=True...")
    try:
        test_load = torch.load(
            new_checkpoint_path,
            map_location='cpu',
            weights_only=True
        )
        print(f"✓ Success! New checkpoint keys: {list(test_load.keys())}")
    except Exception as e:
        print(f"❌ ERROR: New checkpoint cannot be loaded with weights_only=True: {e}")
        return False

    # Final checksum verification
    final_checksum = compute_parameter_checksum(test_load['model_state_dict'])
    print(f"\nFinal verification:")
    print(f"  Original checksum: {original_checksum}")
    print(f"  Final checksum:    {final_checksum}")

    if final_checksum == original_checksum:
        print(f"✅ Checksums match! Weights preserved correctly.")
    else:
        print(f"❌ ERROR: Checksums differ! Conversion corrupted weights.")
        return False

    # Report file sizes
    new_file_size_mb = Path(new_checkpoint_path).stat().st_size / (1024 * 1024)
    print(f"\nFile sizes:")
    print(f"  Original: {file_size_mb:.1f} MB")
    print(f"  Converted: {new_file_size_mb:.1f} MB")

    # Show new metrics format
    print(f"\nNew metrics format (dict):")
    print(f"  train_metrics: {test_load['train_metrics']}")
    print(f"  val_metrics: {test_load['val_metrics']}")

    print(f"\n{'='*70}")
    print(f"✅ Conversion successful!")
    print(f"{'='*70}\n")

    return True


def main():
    """Main conversion routine."""

    print(f"\n{'#'*70}")
    print(f"# PyTorch Checkpoint Conversion Script")
    print(f"# Converting NamedTuple format to dict-only format")
    print(f"{'#'*70}\n")

    # Verify PyTorch version
    print(f"Environment check:")
    print(f"  Python version: {sys.version.split()[0]}")
    print(f"  PyTorch version: {torch.__version__}")

    if not torch.__version__.startswith('2.0'):
        print(f"\n⚠️  WARNING: Expected PyTorch 2.0.x, got {torch.__version__}")
        print(f"This script should be run in biodata_modern_env with PyTorch 2.0.0")
        print(f"where the checkpoints load correctly!")

        response = input("\nContinue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Conversion cancelled.")
            return 1

    # Define models to convert
    models = [
        {
            'name': 'Classification Model',
            'old_path': 'out/classif_train_out/article_classifier.pt',
            'new_path': 'out/classif_train_out/article_classifier_v2.pt',
        },
        {
            'name': 'NER Model',
            'old_path': 'out/ner_train_out/named_entity_recognition.pt',
            'new_path': 'out/ner_train_out/named_entity_recognition_v2.pt',
        }
    ]

    # Convert each model
    results = []
    for model in models:
        print(f"\n{'*'*70}")
        print(f"* {model['name']}")
        print(f"{'*'*70}")

        success = convert_checkpoint(
            old_checkpoint_path=model['old_path'],
            new_checkpoint_path=model['new_path']
        )

        results.append({'name': model['name'], 'success': success})

    # Summary
    print(f"\n{'#'*70}")
    print(f"# Conversion Summary")
    print(f"{'#'*70}\n")

    for result in results:
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"{status}: {result['name']}")

    # Overall status
    all_success = all(r['success'] for r in results)

    if all_success:
        print(f"\n🎉 All conversions successful!")
        print(f"\nNext steps:")
        print(f"  1. Test locally with: python -m pytest tests/ (if applicable)")
        print(f"  2. Upload *_v2.pt files to Google Drive")
        print(f"  3. Test in Colab with PyTorch 2.8")
        print(f"  4. Verify parameter checksums match: a6d0f62fc239a626")
        print(f"  5. Verify predictions match local environment")
        return 0
    else:
        print(f"\n❌ Some conversions failed. Please review errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
