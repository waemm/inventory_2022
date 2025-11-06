#!/usr/bin/env python3
"""
Complete verification script for all bug fixes.

This script performs end-to-end verification that:
1. All bug fixes are properly implemented
2. Data integrity is maintained
3. The pipeline is ready for use

Author: Claude Code
Date: 2025-11-05
"""

import sys
from pathlib import Path

import pandas as pd

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import load_aligned_papers, parse_entity_list


def verify_bug_fixes():
    """Verify all three bug fixes are working."""
    print("=" * 80)
    print("VERIFICATION: Bug Fixes Implementation")
    print("=" * 80)

    all_passed = True

    # Bug #1: NaN Handling
    print("\n[Bug #1] NaN Handling:")
    nan_tests = [
        (None, []),
        (float('nan'), []),
        (pd.NA, []),
        ("nan", []),
    ]
    for input_val, expected in nan_tests:
        result = parse_entity_list(input_val)
        if result == expected:
            print(f"  ✓ {type(input_val).__name__} → {result}")
        else:
            print(f"  ✗ FAIL: {type(input_val).__name__} → {result} (expected {expected})")
            all_passed = False

    # Bug #2: JSON Serialization (verify file exists and format)
    print("\n[Bug #2] JSON Serialization:")
    aligned_path = Path(__file__).parent.parent / "data" / "aligned_papers.csv"
    if aligned_path.exists():
        print(f"  ✓ aligned_papers.csv exists")
        print(f"  ✓ File size: {aligned_path.stat().st_size / 1024 / 1024:.2f} MB")

        # Check format - read a few rows to find one with data
        df = pd.read_csv(aligned_path, nrows=100)
        # Find first row with non-null true_com
        samples = df['true_com'].dropna()
        if len(samples) > 0:
            sample = samples.iloc[0]
            if sample.startswith('["') and sample.endswith('"]'):
                print(f"  ✓ Entity format is JSON: {sample}")
            else:
                print(f"  ✗ FAIL: Entity format is not JSON: {sample}")
                all_passed = False
        else:
            # Try p4_com_raw instead
            samples = df['p4_com_raw'].dropna()
            if len(samples) > 0:
                sample = samples.iloc[0]
                if sample.startswith('["') and sample.endswith('"]'):
                    print(f"  ✓ Entity format is JSON: {sample}")
                else:
                    print(f"  ✗ FAIL: Entity format is not JSON: {sample}")
                    all_passed = False
            else:
                print(f"  ⚠ WARNING: No non-null entities found in first 100 rows")
    else:
        print(f"  ✗ FAIL: aligned_papers.csv not found at {aligned_path}")
        all_passed = False

    # Bug #3: Python List Repr Parsing
    print("\n[Bug #3] Python List Repr Parsing:")
    repr_tests = [
        ("['sc-PDB']", ['sc-PDB']),
        ('["sc-PDB"]', ['sc-PDB']),
        ("['UniProt-KB', 'PDB']", ['UniProt-KB', 'PDB']),
    ]
    for input_val, expected in repr_tests:
        result = parse_entity_list(input_val)
        if result == expected:
            print(f"  ✓ {input_val} → {result}")
        else:
            print(f"  ✗ FAIL: {input_val} → {result} (expected {expected})")
            all_passed = False

    return all_passed


def verify_data_integrity():
    """Verify data integrity in aligned_papers.csv."""
    print("\n" + "=" * 80)
    print("VERIFICATION: Data Integrity")
    print("=" * 80)

    try:
        # Load data
        print("\nLoading aligned_papers.csv...")
        aligned_path = Path(__file__).parent.parent / "data" / "aligned_papers.csv"
        df = load_aligned_papers(aligned_path)
        print(f"  ✓ Loaded {len(df):,} papers")

        # Check entity columns are lists
        print("\nVerifying entity columns are lists...")
        entity_cols = ['true_com', 'true_ful', 'v2_com', 'v2_ful', 'p4_com_raw', 'p4_com_clean']
        all_passed = True

        for col in entity_cols:
            non_list_count = df[col].apply(lambda x: not isinstance(x, list)).sum()
            if non_list_count == 0:
                print(f"  ✓ {col}: All values are lists")
            else:
                print(f"  ✗ FAIL: {col}: {non_list_count} non-list values")
                all_passed = False

        # Check sample data
        print("\nVerifying sample entities...")
        sample = df[df['true_com'].apply(lambda x: len(x) > 0)].iloc[0]
        print(f"  Paper ID: {sample['paper_id']}")
        print(f"  Ground truth: {sample['true_com']} (type: {type(sample['true_com']).__name__})")
        print(f"  V2 predicted: {sample['v2_com']} (type: {type(sample['v2_com']).__name__})")
        print(f"  Phase 4 predicted: {sample['p4_com_raw']} (type: {type(sample['p4_com_raw']).__name__})")

        if isinstance(sample['true_com'], list) and isinstance(sample['v2_com'], list) and isinstance(sample['p4_com_raw'], list):
            print("  ✓ All sample entities are lists")
        else:
            print("  ✗ FAIL: Sample entities are not all lists")
            all_passed = False

        # Check for NaN contamination
        print("\nChecking for NaN contamination...")
        nan_count = 0
        for col in entity_cols:
            for entities in df[col]:
                if isinstance(entities, list):
                    nan_count += sum(1 for e in entities if str(e).lower() == 'nan')

        if nan_count == 0:
            print(f"  ✓ No 'nan' string contamination found")
        else:
            print(f"  ✗ FAIL: Found {nan_count} 'nan' strings in entity lists")
            all_passed = False

        return all_passed

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_pipeline_ready():
    """Verify pipeline is ready for use."""
    print("\n" + "=" * 80)
    print("VERIFICATION: Pipeline Readiness")
    print("=" * 80)

    all_passed = True

    # Check files exist
    print("\nChecking output files...")
    files_to_check = [
        ("aligned_papers.csv", "../data/aligned_papers.csv"),
        ("bpe_artifact_report.json", "../data/bpe_artifact_report.json"),
        ("entity_counts.csv", "../data/entity_counts.csv"),
    ]

    for name, path in files_to_check:
        file_path = Path(__file__).parent.parent / path.replace('../', '')
        if file_path.exists():
            print(f"  ✓ {name} exists ({file_path.stat().st_size / 1024:.2f} KB)")
        else:
            print(f"  ✗ FAIL: {name} not found at {file_path}")
            all_passed = False

    # Check utils exports
    print("\nChecking utils exports...")
    try:
        from utils import (
            load_aligned_papers,
            parse_entity_list,
            load_v2_results,
            load_phase4_results,
        )
        print("  ✓ All required functions imported successfully")
    except ImportError as e:
        print(f"  ✗ FAIL: Import error: {e}")
        all_passed = False

    return all_passed


def main():
    """Run all verification checks."""
    print("=" * 80)
    print("COMPLETE VERIFICATION - BUG FIXES AND DATA INTEGRITY")
    print("=" * 80)
    print("Date: 2025-11-05")
    print("=" * 80)

    results = {
        "Bug Fixes": verify_bug_fixes(),
        "Data Integrity": verify_data_integrity(),
        "Pipeline Readiness": verify_pipeline_ready(),
    }

    print("\n" + "=" * 80)
    print("FINAL VERIFICATION RESULTS")
    print("=" * 80)

    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL VERIFICATIONS PASSED")
        print("=" * 80)
        print("\nThe pipeline is ready for use!")
        print("\nNext steps:")
        print("  1. Run Script 02: python 02_entity_level_comparison.py")
        print("  2. Review comparison results")
        print("  3. Generate final reports")
        print("\n" + "=" * 80)
        return 0
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        print("=" * 80)
        print("\nPlease review the failures above and re-run fixes if needed.")
        print("\n" + "=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
