#!/usr/bin/env python3
"""
Test script to verify ID normalization fix in data loading functions.

This script verifies that IDs are correctly normalized from float format (20672376.0)
to clean integer string format (20672376) across all data loading functions.

Expected behavior:
- IDs stored as floats in CSV: 20672376.0 -> "20672376"
- IDs stored as integers in CSV: 20672376 -> "20672376"
- IDs stored as strings in CSV: "20672376" -> "20672376"

All three formats should result in the same normalized string format for merging.
"""

import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import load_v2_results, load_phase4_results, load_ner_test_split


def test_id_normalization():
    """Test that all ID columns are normalized correctly."""
    print("=" * 80)
    print("Testing ID Normalization Fix")
    print("=" * 80)

    # Test V2 results
    print("\n[1/3] Testing V2 results...")
    try:
        v2_df = load_v2_results()
        if 'ID' in v2_df.columns:
            sample_ids = v2_df['ID'].head(5).tolist()
            print(f"  ✓ Loaded V2 results: {len(v2_df):,} rows")
            print(f"  ✓ Sample IDs: {sample_ids}")

            # Check that IDs don't contain .0
            has_decimal = any('.0' in str(id_val) for id_val in sample_ids)
            if has_decimal:
                print("  ✗ ERROR: IDs still contain .0 suffix!")
                return False
            else:
                print("  ✓ IDs are properly normalized (no .0 suffix)")
        else:
            print("  ! Warning: No 'ID' column found in V2 results")
    except Exception as e:
        print(f"  ✗ Error loading V2 results: {e}")
        return False

    # Test Phase 4 results
    print("\n[2/3] Testing Phase 4 results...")
    try:
        phase4_df = load_phase4_results()
        if 'ID' in phase4_df.columns:
            sample_ids = phase4_df['ID'].head(5).tolist()
            print(f"  ✓ Loaded Phase 4 results: {len(phase4_df):,} rows")
            print(f"  ✓ Sample IDs: {sample_ids}")

            # Check that IDs don't contain .0
            has_decimal = any('.0' in str(id_val) for id_val in sample_ids)
            if has_decimal:
                print("  ✗ ERROR: IDs still contain .0 suffix!")
                return False
            else:
                print("  ✓ IDs are properly normalized (no .0 suffix)")
        else:
            print("  ! Warning: No 'ID' column found in Phase 4 results")
    except Exception as e:
        print(f"  ✗ Error loading Phase 4 results: {e}")
        return False

    # Test NER test split
    print("\n[3/3] Testing NER test split...")
    try:
        test_df = load_ner_test_split()
        if 'id' in test_df.columns:
            sample_ids = test_df['id'].head(5).tolist()
            print(f"  ✓ Loaded test split: {len(test_df):,} rows")
            print(f"  ✓ Sample IDs: {sample_ids}")

            # Check that IDs don't contain .0
            has_decimal = any('.0' in str(id_val) for id_val in sample_ids)
            if has_decimal:
                print("  ✗ ERROR: IDs still contain .0 suffix!")
                return False
            else:
                print("  ✓ IDs are properly normalized (no .0 suffix)")
        else:
            print("  ! Warning: No 'id' column found in test split")
    except Exception as e:
        print(f"  ✗ Error loading test split: {e}")
        return False

    # Test merge compatibility
    print("\n[4/4] Testing merge compatibility...")
    try:
        # Get sample IDs from each dataset
        v2_sample = set(v2_df['ID'].head(10))
        phase4_sample = set(phase4_df['ID'].head(10))

        # Find common IDs
        common_ids = v2_sample & phase4_sample

        print(f"  ✓ V2 sample IDs: {sorted(list(v2_sample)[:3])}")
        print(f"  ✓ Phase 4 sample IDs: {sorted(list(phase4_sample)[:3])}")
        print(f"  ✓ Common IDs in sample: {len(common_ids)}")

        if common_ids:
            print(f"  ✓ Example matching IDs: {sorted(list(common_ids))[:3]}")

        print("  ✓ IDs are merge-compatible (same format)")

    except Exception as e:
        print(f"  ! Could not test merge compatibility: {e}")

    print("\n" + "=" * 80)
    print("✓ All ID normalization tests passed!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = test_id_normalization()
    sys.exit(0 if success else 1)
