#!/usr/bin/env python3
"""
Test script for 01_preprocess_and_align.py

This script performs quick validation tests on the preprocessing script
without running the full dataset.

Tests:
1. Module imports work correctly
2. Utility functions are accessible
3. Data loading functions work
4. BPE cleaning functions work correctly
5. Entity parsing handles various formats

Usage:
    python test_01_preprocess.py
"""

import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    try:
        from utils import (
            load_v2_results,
            load_phase4_results,
            load_ner_test_split,
            load_inventory,
            parse_entity_list,
            detect_bpe_artifacts,
            clean_bpe_entity,
            clean_bpe_dataframe,
            generate_bpe_report,
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_entity_parsing():
    """Test entity parsing with various formats."""
    print("\nTesting entity parsing...")
    from utils import parse_entity_list

    test_cases = [
        ("protein A, gene B, compound C", 3),
        ('["protein A", "gene B"]', 2),
        (["protein A", "gene B"], 2),
        ("", 0),
        (None, 0),
        ("[]", 0),
    ]

    all_passed = True
    for input_val, expected_count in test_cases:
        result = parse_entity_list(input_val)
        if len(result) != expected_count:
            print(f"✗ Failed: {input_val} -> expected {expected_count}, got {len(result)}")
            all_passed = False
        else:
            print(f"✓ Passed: {input_val} -> {expected_count} entities")

    return all_passed


def test_bpe_detection():
    """Test BPE artifact detection."""
    print("\nTesting BPE artifact detection...")
    from utils import detect_bpe_artifacts

    test_cases = [
        ("Ġprotein", True),
        ("ĠIL-6", True),
        ("protein A", False),
        ("IL-6", False),
        ("T cell", False),
        ("ĠRat ĠGen ome", True),
    ]

    all_passed = True
    for entity, expected in test_cases:
        result = detect_bpe_artifacts(entity)
        if result != expected:
            print(f"✗ Failed: '{entity}' -> expected {expected}, got {result}")
            all_passed = False
        else:
            print(f"✓ Passed: '{entity}' -> {expected}")

    return all_passed


def test_bpe_cleaning():
    """Test BPE artifact cleaning."""
    print("\nTesting BPE artifact cleaning...")
    from utils import clean_bpe_entity

    test_cases = [
        ("Ġprotein", "protein"),
        ("ĠIL-6", "IL-6"),
        ("Ġprotein ĠA", "protein A"),
        ("T cell", "T cell"),  # Should preserve T
        ("ĠRat ĠGen ome ĠDatabase", "Rat Gen ome Database"),  # Gen/ome are 3-letter, kept separate
    ]

    all_passed = True
    for original, expected in test_cases:
        result = clean_bpe_entity(original)
        if result != expected:
            print(f"✗ Failed: '{original}' -> expected '{expected}', got '{result}'")
            all_passed = False
        else:
            print(f"✓ Passed: '{original}' -> '{expected}'")

    return all_passed


def test_data_paths():
    """Test that required data files exist."""
    print("\nTesting data file paths...")

    project_root = Path(__file__).parent.parent.parent

    files_to_check = [
        project_root / "collab_results" / "2025-10-28-ulgfhi_oldmodel_2022_rerun" / "ner_results.csv",
        project_root / "collab_results" / "experiment_archives" / "2025-11-05-poq5i4_phase4_2022_rerun" / "ner_results.csv",
        project_root / "data" / "ner_splits_full" / "test_ner.csv",
        project_root / "data" / "final_inventory_2022.csv",
    ]

    all_exist = True
    for file_path in files_to_check:
        if file_path.exists():
            size_mb = file_path.stat().st_size / 1024 / 1024
            print(f"✓ Found: {file_path.name} ({size_mb:.2f} MB)")
        else:
            print(f"✗ Missing: {file_path}")
            all_exist = False

    return all_exist


def test_output_directory():
    """Test that output directory can be created."""
    print("\nTesting output directory...")

    output_dir = Path(__file__).parent.parent / "data"

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Output directory ready: {output_dir}")
        return True
    except Exception as e:
        print(f"✗ Cannot create output directory: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("Testing 01_preprocess_and_align.py")
    print("=" * 80)

    tests = [
        ("Imports", test_imports),
        ("Entity Parsing", test_entity_parsing),
        ("BPE Detection", test_bpe_detection),
        ("BPE Cleaning", test_bpe_cleaning),
        ("Data Paths", test_data_paths),
        ("Output Directory", test_output_directory),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results[test_name] = False

    print("\n" + "=" * 80)
    print("Test Results Summary")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All tests passed! Script is ready to run.")
        print("   Run: python 01_preprocess_and_align.py")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before running.")
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"   Failed tests: {', '.join(failed_tests)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
