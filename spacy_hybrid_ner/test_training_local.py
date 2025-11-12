#!/usr/bin/env python3
"""
Local spaCy Training Test Script

Tests the spaCy training configuration locally before running in Colab.
Validates config, data files, and runs a quick training test (1 epoch).

Usage:
    python spacy_hybrid_ner/test_training_local.py
    python spacy_hybrid_ner/test_training_local.py --quick  # Skip training test
"""

import sys
import subprocess
from pathlib import Path
import argparse
import json

# Color output for better readability
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def check_spacy_version():
    """Check spaCy installation and version."""
    print_header("1. CHECKING SPACY INSTALLATION")

    try:
        import spacy
        version = spacy.__version__
        print_success(f"spaCy installed: version {version}")

        if version < "3.7.0":
            print_warning(f"spaCy {version} is older than recommended (3.7.0)")
            print_info("Consider upgrading: pip install -U spacy")

        return True
    except ImportError:
        print_error("spaCy not installed")
        print_info("Install with: pip install spacy")
        return False


def validate_config(config_path):
    """Validate spaCy config file."""
    print_header("2. VALIDATING CONFIG FILE")

    if not config_path.exists():
        print_error(f"Config file not found: {config_path}")
        return False

    print_info(f"Config file: {config_path}")

    # Run spacy debug config
    try:
        result = subprocess.run(
            ['python', '-m', 'spacy', 'debug', 'config', str(config_path)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print_success("Config validation passed")
            return True
        else:
            print_error("Config validation failed")
            print("\nError output:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False

    except FileNotFoundError:
        print_error("spaCy CLI not found. Is spaCy installed?")
        return False


def check_data_files(config_path):
    """Check that training data files exist."""
    print_header("3. CHECKING TRAINING DATA FILES")

    base_dir = config_path.parent.parent.parent  # Go up to project root

    files = {
        'config': config_path,
        'train': config_path.parent / 'train.spacy',
        'dev': config_path.parent / 'dev.spacy',
        'test': config_path.parent / 'test.spacy'
    }

    all_exist = True
    for name, path in files.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024*1024)
            print_success(f"{name:10s}: {path.name} ({size_mb:.2f} MB)")
        else:
            print_error(f"{name:10s}: NOT FOUND - {path}")
            all_exist = False

    return all_exist


def inspect_data(data_path):
    """Inspect .spacy data file."""
    print_header("4. INSPECTING DATA STRUCTURE")

    try:
        import spacy
        from spacy.tokens import DocBin

        nlp = spacy.blank("en")

        for split_name in ['train', 'dev', 'test']:
            split_path = data_path / f'{split_name}.spacy'

            if not split_path.exists():
                print_warning(f"Skipping {split_name} (not found)")
                continue

            db = DocBin().from_disk(split_path)
            docs = list(db.get_docs(nlp.vocab))

            n_docs = len(docs)
            n_ents = sum(len(doc.ents) for doc in docs)

            # Check for issues
            issues = []

            # Sample first doc
            if docs:
                first_doc = docs[0]

                # Check entity format
                if first_doc.ents:
                    first_ent = first_doc.ents[0]
                    print_info(f"{split_name}: {n_docs} docs, {n_ents} entities")
                    print_info(f"  Sample entity: '{first_ent.text}' [{first_ent.label_}]")

                    # Check labels
                    labels = set(ent.label_ for doc in docs for ent in doc.ents)
                    print_info(f"  Labels found: {sorted(labels)}")

                    if not labels:
                        issues.append("No labels found")

                    # Check for overlapping entities
                    for doc in docs[:100]:  # Check first 100
                        ents = sorted(doc.ents, key=lambda e: e.start)
                        for i in range(len(ents)-1):
                            if ents[i].end > ents[i+1].start:
                                issues.append(f"Overlapping entities detected")
                                break
                        if issues:
                            break

                if issues:
                    for issue in issues:
                        print_error(f"  Issue: {issue}")
                else:
                    print_success(f"  {split_name} data looks good")

        return True

    except Exception as e:
        print_error(f"Error inspecting data: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_training(config_path, output_dir):
    """Run a quick training test (1 epoch)."""
    print_header("5. RUNNING QUICK TRAINING TEST (1 epoch)")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data_dir = config_path.parent

    # Build training command
    train_cmd = [
        'python', '-m', 'spacy', 'train',
        str(config_path),
        '--output', str(output_dir),
        '--paths.train', str(data_dir / 'train.spacy'),
        '--paths.dev', str(data_dir / 'dev.spacy'),
        '--training.max_epochs', '1',  # Just 1 epoch for testing
        '--gpu-id', '-1'  # Use CPU for testing
    ]

    print_info("Running command:")
    print(f"  {' '.join(train_cmd)}")
    print_info("\nThis will take 1-2 minutes for 1 epoch...")

    try:
        result = subprocess.run(
            train_cmd,
            check=False,
            text=True
        )

        if result.returncode == 0:
            print_success("Training test completed successfully!")

            # Check output
            model_last = output_dir / 'model-last'
            if model_last.exists():
                print_success(f"Model saved to: {model_last}")

                # Try to load model
                try:
                    import spacy
                    nlp = spacy.load(model_last)
                    print_success(f"Model loads successfully")
                    print_info(f"  Pipeline: {nlp.pipe_names}")

                    # Test prediction
                    doc = nlp("The Protein Data Bank (PDB) contains protein structures.")
                    if doc.ents:
                        print_info(f"  Test prediction: found {len(doc.ents)} entities")
                        for ent in doc.ents:
                            print_info(f"    - '{ent.text}' [{ent.label_}]")
                    else:
                        print_warning("  Test prediction: no entities found (model may need more training)")

                except Exception as e:
                    print_error(f"Error loading model: {e}")
                    return False

            return True
        else:
            print_error(f"Training test failed with exit code {result.returncode}")
            return False

    except Exception as e:
        print_error(f"Error running training test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Test spaCy training configuration locally')
    parser.add_argument('--quick', action='store_true', help='Skip training test (validation only)')
    parser.add_argument('--config', type=str,
                       default='spacy_hybrid_ner/data/ner_training/config.cfg',
                       help='Path to config file')
    parser.add_argument('--output', type=str,
                       default='spacy_hybrid_ner/test_output',
                       help='Output directory for test training')

    args = parser.parse_args()

    print(f"{Colors.BOLD}")
    print("=" * 80)
    print("SPACY TRAINING LOCAL TEST")
    print("=" * 80)
    print(f"{Colors.END}")

    # Get paths
    config_path = Path(args.config)
    output_dir = Path(args.output)

    # Run checks
    checks = [
        ("spaCy Installation", lambda: check_spacy_version()),
        ("Config Validation", lambda: validate_config(config_path)),
        ("Data Files", lambda: check_data_files(config_path)),
        ("Data Structure", lambda: inspect_data(config_path.parent)),
    ]

    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print_error(f"Unexpected error in {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Training test (optional)
    if not args.quick and all(results.values()):
        try:
            results["Training Test"] = test_training(config_path, output_dir)
        except Exception as e:
            print_error(f"Unexpected error in training test: {e}")
            import traceback
            traceback.print_exc()
            results["Training Test"] = False

    # Summary
    print_header("SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        if result:
            print_success(f"{name:25s}: PASSED")
        else:
            print_error(f"{name:25s}: FAILED")

    print(f"\n{Colors.BOLD}Overall: {passed}/{total} checks passed{Colors.END}")

    if all(results.values()):
        print_success("\n✅ All checks passed! Configuration is ready for Colab training.")
        return 0
    else:
        print_error("\n❌ Some checks failed. Fix issues before running in Colab.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
