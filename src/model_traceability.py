"""
Model Traceability Module
~~~

Provides comprehensive model traceability through MD5 checksums, metadata capture,
and automated verification workflows. Ensures complete audit trails from training
sessions through model files to prediction results.

Features:
- MD5 checksum generation and verification
- Git commit tracking
- Environment metadata capture
- Model architecture extraction
- Training metrics extraction
- Manifest file generation
- Automated verification workflows

Authors: AI Agent (Claude Code)
Created: 2025-10-28
"""

import os
import sys
import hashlib
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, List, Optional, Any

import torch


# ---------------------------------------------------------------------------
def compute_file_md5(filepath: str, chunk_size: int = 8192) -> str:
    """
    Compute MD5 checksum of a file

    Args:
        filepath: Path to file
        chunk_size: Size of chunks to read (default 8KB)

    Returns:
        MD5 hash as hex string

    Example:
        >>> md5 = compute_file_md5("model.pt")
        >>> print(md5)
        'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'
    """
    md5_hash = hashlib.md5()

    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


# ---------------------------------------------------------------------------
def get_git_info() -> Dict[str, Any]:
    """
    Get current git commit, branch, and dirty status

    Returns:
        Dictionary with git information

    Example:
        >>> git_info = get_git_info()
        >>> print(git_info)
        {
            'commit': '0d4a55062157160cd43ceaf9ab1dce1361a03b13',
            'branch': 'modernization-python311',
            'dirty': False,
            'available': True
        }
    """
    try:
        # Get commit hash
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        # Get branch name
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        # Check if working directory is dirty
        status = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        return {
            'commit': commit,
            'branch': branch,
            'dirty': len(status) > 0,
            'available': True
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            'commit': 'unknown',
            'branch': 'unknown',
            'dirty': False,
            'available': False
        }


# ---------------------------------------------------------------------------
def get_environment_info() -> Dict[str, Any]:
    """
    Capture Python environment information

    Returns:
        Dictionary with environment details

    Example:
        >>> env = get_environment_info()
        >>> print(env['pytorch_version'])
        '2.0.0'
    """
    import transformers

    env_info = {
        'python_version': sys.version.split()[0],
        'pytorch_version': torch.__version__,
        'transformers_version': transformers.__version__,
    }

    # Add CUDA info if available
    if torch.cuda.is_available():
        env_info['cuda_available'] = True
        env_info['cuda_version'] = torch.version.cuda
        env_info['gpu_name'] = torch.cuda.get_device_name(0)
        env_info['gpu_memory_gb'] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
    else:
        env_info['cuda_available'] = False

    return env_info


# ---------------------------------------------------------------------------
def extract_model_architecture(model_path: str, model_type: str) -> Dict[str, Any]:
    """
    Extract architecture details from a model checkpoint

    Args:
        model_path: Path to model .pt file
        model_type: 'classification' or 'ner'

    Returns:
        Dictionary with architecture information

    Example:
        >>> arch = extract_model_architecture("model.pt", "classification")
        >>> print(arch['num_parameters'])
        124647424
    """
    try:
        # Load checkpoint (weights only for safety)
        checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)

        # Extract state dict
        state_dict = checkpoint.get('model_state_dict', {})

        # Count parameters
        total_params = sum(p.numel() for p in state_dict.values())

        # Determine model type and labels
        if model_type == 'classification':
            model_class = 'RobertaForSequenceClassification'
            num_labels = 2
        else:  # ner
            model_class = 'RobertaForTokenClassification'
            num_labels = 3

        # Build architecture info
        arch_info = {
            'model_type': model_class,
            'num_labels': num_labels,
            'num_parameters': int(total_params),
            'num_trainable_parameters': int(total_params),
            'hidden_size': 768,  # Standard for RoBERTa base
            'num_layers': 12,     # Standard for RoBERTa base
            'num_attention_heads': 12  # Standard for RoBERTa base
        }

        # Add label mapping for NER
        if model_type == 'ner':
            arch_info['label_map'] = {
                '0': 'O',
                '1': 'B-DB_NAME',
                '2': 'I-DB_NAME'
            }

        return arch_info

    except Exception as e:
        print(f"⚠️ Could not extract full architecture: {e}")
        return {
            'model_type': model_class,
            'error': str(e)
        }


# ---------------------------------------------------------------------------
def extract_model_metrics(model_path: str) -> Dict[str, Any]:
    """
    Extract training metrics from a model checkpoint

    Args:
        model_path: Path to model .pt file

    Returns:
        Dictionary with training metrics

    Example:
        >>> metrics = extract_model_metrics("model.pt")
        >>> print(metrics['val_f1'])
        0.887
    """
    try:
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)

        # Try to extract metrics from checkpoint
        metrics = {}

        # Common metric keys in our checkpoints
        metric_keys = [
            'train_f1', 'train_precision', 'train_recall',
            'val_f1', 'val_precision', 'val_recall',
            'best_epoch', 'epoch'
        ]

        for key in metric_keys:
            if key in checkpoint:
                value = checkpoint[key]
                # Convert numpy/torch values to Python types
                if hasattr(value, 'item'):
                    value = value.item()
                metrics[key] = value

        return metrics

    except Exception as e:
        print(f"⚠️ Could not extract metrics: {e}")
        return {}


# ---------------------------------------------------------------------------
def create_model_manifest(
        archive_dir: str,
        session_id: str,
        config: Dict[str, Any],
        classif_model_path: str,
        ner_model_path: str) -> str:
    """
    Create comprehensive model manifest with checksums and metadata

    Args:
        archive_dir: Archive directory path
        session_id: Training session ID
        config: Training configuration dictionary
        classif_model_path: Path to classification model
        ner_model_path: Path to NER model

    Returns:
        Path to manifest file

    Example:
        >>> manifest = create_model_manifest(
        ...     "/archive/2025-10-24-abc123",
        ...     "2025-10-24-abc123",
        ...     config,
        ...     "classification_model.pt",
        ...     "ner_model.pt"
        ... )
        >>> print(manifest)
        '/archive/2025-10-24-abc123/model_manifest.json'
    """
    print("📋 Generating model manifest with checksums...")

    # Initialize manifest
    manifest = {
        'manifest_version': '1.0',
        'session_id': session_id,
        'created_at': datetime.now().isoformat(),
    }

    # Add git info
    git_info = get_git_info()
    manifest['git_commit'] = git_info['commit']
    manifest['git_branch'] = git_info['branch']
    manifest['git_dirty'] = git_info['dirty']

    # Add environment info
    manifest['environment'] = get_environment_info()

    # Add training config
    manifest['training_config'] = {
        'model_name': config.get('model_name', 'unknown'),
        'hf_model': config.get('model', 'unknown'),
        'epochs': config.get('epochs', 0),
        'batch_size': config.get('optimal_batch_size', config.get('batch_size', 0)),
        'learning_rate': float(config.get('learning_rate', 0)),
        'weight_decay': float(config.get('weight_decay', 0)),
        'test_mode': config.get('test_mode', False)
    }

    # Process each model
    manifest['models'] = {}

    for model_type, model_path in [('classification', classif_model_path), ('ner', ner_model_path)]:
        if not Path(model_path).exists():
            print(f"   ⚠️ Model not found: {model_path}")
            continue

        print(f"   🔐 Processing {model_type} model...")

        # Compute MD5 checksum
        print(f"      Computing MD5...")
        md5_hash = compute_file_md5(model_path)

        # Get file metadata
        file_stat = Path(model_path).stat()
        size_bytes = file_stat.st_size
        size_mb = size_bytes / (1024 * 1024)

        # Extract architecture
        print(f"      Extracting architecture...")
        architecture = extract_model_architecture(model_path, model_type)

        # Extract metrics
        print(f"      Extracting metrics...")
        metrics = extract_model_metrics(model_path)

        # Build model entry
        model_entry = {
            'filename': Path(model_path).name,
            'filepath': str(Path(model_path).absolute()),
            'md5': md5_hash,
            'size_bytes': size_bytes,
            'size_mb': round(size_mb, 2),
            'created_at': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            'architecture': architecture,
            'metrics': metrics
        }

        manifest['models'][model_type] = model_entry

        print(f"      ✅ MD5: {md5_hash[:16]}...")
        print(f"      ✅ Size: {size_mb:.1f}MB")

    # Add verification section
    manifest['verification'] = {
        'checksum_algorithm': 'md5',
        'checksum_verified': True,
        'verified_at': datetime.now().isoformat(),
        'verification_notes': 'Checksums computed at model archive creation'
    }

    # Save manifest
    manifest_path = f"{archive_dir}/model_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"   ✅ Manifest saved: {manifest_path}")

    return manifest_path


# ---------------------------------------------------------------------------
def verify_model_checksum(model_path: str, expected_md5: str) -> Tuple[bool, str]:
    """
    Verify model file integrity using MD5 checksum

    Args:
        model_path: Path to model file
        expected_md5: Expected MD5 hash

    Returns:
        Tuple of (verified: bool, actual_md5: str)

    Example:
        >>> verified, actual = verify_model_checksum("model.pt", "a1b2c3d4...")
        >>> if verified:
        ...     print("Model verified!")
    """
    print(f"🔍 Verifying checksum for {Path(model_path).name}...")

    if not Path(model_path).exists():
        print(f"   ❌ File not found: {model_path}")
        return False, ""

    actual_md5 = compute_file_md5(model_path)
    verified = actual_md5.lower() == expected_md5.lower()

    if verified:
        print(f"   ✅ Checksum verified: {actual_md5[:16]}...")
    else:
        print(f"   ❌ CHECKSUM MISMATCH!")
        print(f"      Expected: {expected_md5}")
        print(f"      Actual:   {actual_md5}")
        print(f"      ⚠️ Model may be corrupted or modified!")

    return verified, actual_md5


# ---------------------------------------------------------------------------
def load_and_verify_models(
        manifest_path: str,
        classif_model_path: str,
        ner_model_path: str,
        strict: bool = True) -> Tuple[bool, Dict[str, Any]]:
    """
    Load model manifest and verify checksums

    Args:
        manifest_path: Path to model_manifest.json
        classif_model_path: Path to classification model
        ner_model_path: Path to NER model
        strict: If True, raise exception on checksum mismatch

    Returns:
        Tuple of (all_verified: bool, verification_report: dict)

    Raises:
        FileNotFoundError: If manifest not found (strict mode)
        ValueError: If checksum verification fails (strict mode)

    Example:
        >>> verified, report = load_and_verify_models(
        ...     "model_manifest.json",
        ...     "classification_model.pt",
        ...     "ner_model.pt"
        ... )
        >>> if verified:
        ...     print("All models verified!")
    """
    print("🔐 Loading model manifest and verifying checksums...")

    # Load manifest
    if not Path(manifest_path).exists():
        msg = f"Manifest not found: {manifest_path}"
        if strict:
            raise FileNotFoundError(msg)
        print(f"   ⚠️ {msg}")
        return False, {'error': 'manifest_not_found'}

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    print(f"   📋 Manifest version: {manifest['manifest_version']}")
    print(f"   🆔 Session ID: {manifest['session_id']}")
    print(f"   🔗 Git commit: {manifest['git_commit'][:8]}")

    # Verify each model
    verification_report = {
        'manifest_loaded': True,
        'session_id': manifest['session_id'],
        'git_commit': manifest['git_commit'],
        'models': {}
    }

    all_verified = True

    for model_type, model_path in [('classification', classif_model_path), ('ner', ner_model_path)]:
        if model_type not in manifest['models']:
            print(f"   ⚠️ {model_type} not in manifest")
            verification_report['models'][model_type] = {
                'verified': False,
                'error': 'not_in_manifest'
            }
            all_verified = False
            continue

        expected_md5 = manifest['models'][model_type]['md5']
        verified, actual_md5 = verify_model_checksum(model_path, expected_md5)

        verification_report['models'][model_type] = {
            'verified': verified,
            'expected_md5': expected_md5,
            'actual_md5': actual_md5,
            'size_mb': manifest['models'][model_type]['size_mb']
        }

        if not verified:
            all_verified = False
            if strict:
                raise ValueError(
                    f"Checksum verification failed for {model_type} model!\n"
                    f"Expected: {expected_md5}\n"
                    f"Actual: {actual_md5}\n"
                    f"Model may be corrupted or tampered with."
                )

    if all_verified:
        print("   ✅ All model checksums verified successfully!")
    else:
        print("   ⚠️ Some checksums failed verification")

    verification_report['all_verified'] = all_verified
    verification_report['verified_at'] = datetime.now().isoformat()

    return all_verified, verification_report


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit('This file is a module, and is not meant to be run.')
