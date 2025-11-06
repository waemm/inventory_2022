#!/usr/bin/env python3
"""
Test script to verify critical bug fixes in entity parsing and serialization.

Tests:
1. Bug #1: NaN handling in parse_entity_list()
2. Bug #2: Double JSON serialization in CSV
3. Bug #3: Comma parsing logic and ast.literal_eval for Python list repr

Author: Claude Code
Date: 2025-11-05
"""

import json
import sys
from pathlib import Path

import pandas as pd

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import parse_entity_list


def test_nan_handling():
    """Test Bug Fix #1: NaN handling."""
    print("\n" + "=" * 80)
    print("TEST 1: NaN Handling in parse_entity_list()")
    print("=" * 80)

    test_cases = [
        (None, [], "None input"),
        (float('nan'), [], "float('nan') input"),
        (pd.NA, [], "pd.NA input"),
        ("nan", [], "String 'nan'"),
        ("NaN", [], "String 'NaN'"),
        ("", [], "Empty string"),
        ("[]", [], "Empty JSON array"),
    ]

    all_passed = True
    for input_val, expected, description in test_cases:
        result = parse_entity_list(input_val)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {description}")
        if not passed:
            print(f"  Expected: {expected}")
            print(f"  Got: {result}")
            all_passed = False

    return all_passed


def test_python_list_repr_parsing():
    """Test Bug Fix #3: Python list repr parsing with ast.literal_eval."""
    print("\n" + "=" * 80)
    print("TEST 2: Python List Repr Parsing")
    print("=" * 80)

    test_cases = [
        ("['sc-PDB']", ['sc-PDB'], "Single-quoted Python list with hyphen"),
        ("['protein A', 'gene B']", ['protein A', 'gene B'], "Single-quoted Python list multiple items"),
        ('["protein A", "gene B"]', ['protein A', 'gene B'], "Double-quoted JSON list"),
        ("['PDB', 'RCSB']", ['PDB', 'RCSB'], "Single-quoted Python list abbreviations"),
        ("['UniProt-KB']", ['UniProt-KB'], "Single-quoted with hyphen"),
    ]

    all_passed = True
    for input_val, expected, description in test_cases:
        result = parse_entity_list(input_val)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {description}")
        print(f"  Input: {input_val}")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        if not passed:
            all_passed = False

    return all_passed


def test_json_serialization_roundtrip():
    """Test Bug Fix #2: JSON serialization/deserialization roundtrip."""
    print("\n" + "=" * 80)
    print("TEST 3: JSON Serialization Roundtrip")
    print("=" * 80)

    test_data = {
        'entities_1': [['sc-PDB'], ['UniProt-KB', 'PDB'], []],
        'entities_2': [['protein A', 'gene B'], ['compound C'], ['enzyme D', 'receptor E']],
    }

    df = pd.DataFrame(test_data)
    print(f"\nOriginal DataFrame:")
    print(df)
    print(f"\nOriginal data types:")
    for col in df.columns:
        print(f"  {col}: {type(df[col].iloc[0])} - Sample: {df[col].iloc[0]}")

    # Serialize to JSON strings (simulating save to CSV)
    df_serialized = df.copy()
    for col in df_serialized.columns:
        df_serialized[col] = df_serialized[col].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else x
        )

    print(f"\nSerialized DataFrame (as would be saved to CSV):")
    print(df_serialized)
    print(f"\nSerialized data types:")
    for col in df_serialized.columns:
        print(f"  {col}: {type(df_serialized[col].iloc[0])} - Sample: {df_serialized[col].iloc[0]}")

    # Deserialize back to lists (simulating load from CSV)
    df_deserialized = df_serialized.copy()
    for col in df_deserialized.columns:
        df_deserialized[col] = df_deserialized[col].apply(parse_entity_list)

    print(f"\nDeserialized DataFrame (after loading from CSV):")
    print(df_deserialized)
    print(f"\nDeserialized data types:")
    for col in df_deserialized.columns:
        print(f"  {col}: {type(df_deserialized[col].iloc[0])} - Sample: {df_deserialized[col].iloc[0]}")

    # Verify roundtrip
    all_passed = True
    for col in df.columns:
        for idx in range(len(df)):
            original = df[col].iloc[idx]
            roundtrip = df_deserialized[col].iloc[idx]
            if original != roundtrip:
                print(f"\n✗ FAIL: Roundtrip failed for {col}[{idx}]")
                print(f"  Original: {original} (type: {type(original)})")
                print(f"  Roundtrip: {roundtrip} (type: {type(roundtrip)})")
                all_passed = False

    if all_passed:
        print(f"\n✓ PASS: All roundtrip tests passed")
        print(f"  - Lists preserved correctly through serialization")
        print(f"  - No data corruption detected")

    return all_passed


def test_edge_cases():
    """Test edge cases and malformed input."""
    print("\n" + "=" * 80)
    print("TEST 4: Edge Cases and Malformed Input")
    print("=" * 80)

    test_cases = [
        ("entity1, entity2, entity3", ['entity1', 'entity2', 'entity3'], "Comma-separated string"),
        ("entity1,entity2,entity3", ['entity1', 'entity2', 'entity3'], "Comma-separated no spaces"),
        ("  entity1  ,  entity2  ", ['entity1', 'entity2'], "Extra whitespace"),
        (["already", "a", "list"], ['already', 'a', 'list'], "Already a list"),
        (["item1", "", "item2"], ['item1', 'item2'], "List with empty string"),
        # Note: 'nan' string is filtered out to prevent NaN contamination (by design)
        ('["item1", "nan", "item2"]', ['item1', 'item2'], "JSON with 'nan' string (filtered)"),
        (["item1", "nan", "item2"], ['item1', 'item2'], "List with 'nan' string (filtered)"),
        ('["item1", "NaN", "item2"]', ['item1', 'item2'], "JSON with 'NaN' string (filtered)"),
    ]

    all_passed = True
    for input_val, expected, description in test_cases:
        result = parse_entity_list(input_val)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {description}")
        if not passed:
            print(f"  Input: {input_val}")
            print(f"  Expected: {expected}")
            print(f"  Got: {result}")
            all_passed = False

    return all_passed


def main():
    """Run all tests."""
    print("=" * 80)
    print("CRITICAL BUG FIXES VERIFICATION TESTS")
    print("=" * 80)

    results = {
        "NaN Handling": test_nan_handling(),
        "Python List Repr Parsing": test_python_list_repr_parsing(),
        "JSON Serialization Roundtrip": test_json_serialization_roundtrip(),
        "Edge Cases": test_edge_cases(),
    }

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED - Bug fixes verified successfully!")
        print("=" * 80)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please review failures above")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
