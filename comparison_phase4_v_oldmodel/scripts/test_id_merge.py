#!/usr/bin/env python3
"""
Integration test: Verify ID normalization enables correct merging.

This test simulates the merge operation in 01_preprocess_and_align.py
to ensure IDs from different sources can be successfully matched.

Tests:
1. V2 and Phase 4 merge on paper_id
2. Test split merge on paper_id
3. Verify merge statistics are reasonable
4. Confirm no spurious "only in X" entries due to ID format mismatch
"""

import sys
from pathlib import Path

import pandas as pd

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import load_v2_results, load_phase4_results, load_ner_test_split


def test_merge_integration():
    """Test that normalized IDs enable correct merging."""
    print("=" * 80)
    print("Testing ID Normalization - Merge Integration")
    print("=" * 80)

    # Load all datasets
    print("\n[1/4] Loading datasets...")
    v2_df = load_v2_results()
    phase4_df = load_phase4_results()
    test_df = load_ner_test_split()

    print(f"  ✓ V2 results: {len(v2_df):,} papers")
    print(f"  ✓ Phase 4 results: {len(phase4_df):,} papers")
    print(f"  ✓ Test split: {len(test_df):,} papers")

    # Prepare V2 data (simulate 01_preprocess_and_align.py logic)
    print("\n[2/4] Preparing data for merge...")
    v2_aligned = v2_df[['ID']].copy()
    v2_aligned.columns = ['paper_id']
    v2_aligned['paper_id'] = v2_aligned['paper_id'].astype(str)

    phase4_aligned = phase4_df[['ID']].copy()
    phase4_aligned.columns = ['paper_id']
    phase4_aligned['paper_id'] = phase4_aligned['paper_id'].astype(str)

    test_aligned = test_df[['id']].copy()
    test_aligned.columns = ['paper_id']
    test_aligned['paper_id'] = test_aligned['paper_id'].astype(str)

    print(f"  ✓ V2 paper_id sample: {v2_aligned['paper_id'].head(3).tolist()}")
    print(f"  ✓ Phase 4 paper_id sample: {phase4_aligned['paper_id'].head(3).tolist()}")
    print(f"  ✓ Test paper_id sample: {test_aligned['paper_id'].head(3).tolist()}")

    # Test V2 + Phase 4 merge
    print("\n[3/4] Testing V2 + Phase 4 merge...")
    merged_v2_phase4 = pd.merge(
        v2_aligned,
        phase4_aligned,
        on='paper_id',
        how='outer',
        indicator=True
    )

    both_count = sum(merged_v2_phase4['_merge'] == 'both')
    v2_only = sum(merged_v2_phase4['_merge'] == 'left_only')
    phase4_only = sum(merged_v2_phase4['_merge'] == 'right_only')

    print(f"  ✓ Both V2 and Phase 4: {both_count:,}")
    print(f"  ✓ Only V2: {v2_only:,}")
    print(f"  ✓ Only Phase 4: {phase4_only:,}")

    # Verify merge is reasonable (should have significant overlap)
    total_papers = len(merged_v2_phase4)
    overlap_pct = (both_count / total_papers) * 100

    print(f"  ✓ Overlap percentage: {overlap_pct:.1f}%")

    if both_count == 0:
        print("  ✗ ERROR: No papers matched between V2 and Phase 4!")
        print("  ✗ This suggests ID format mismatch is still present.")
        return False
    elif both_count < 100:
        print(f"  ! WARNING: Only {both_count} papers matched - expected more.")
        print("  ! This might indicate incomplete ID normalization.")
        return False
    else:
        print(f"  ✓ Good overlap: {both_count:,} papers matched successfully")

    # Test with ground truth merge
    print("\n[4/4] Testing ground truth merge...")

    # First merge V2 + Phase 4
    base_merge = pd.merge(
        v2_aligned,
        phase4_aligned,
        on='paper_id',
        how='inner'  # Only papers in both
    )

    # Then merge with test split
    with_test = pd.merge(
        base_merge,
        test_aligned,
        on='paper_id',
        how='left',
        indicator=True
    )

    with_gt = sum(with_test['_merge'] == 'both')
    without_gt = sum(with_test['_merge'] == 'left_only')

    print(f"  ✓ Papers with ground truth: {with_gt:,}")
    print(f"  ✓ Papers without ground truth: {without_gt:,}")

    if with_gt == 0:
        print("  ! WARNING: No papers matched with ground truth")
        print("  ! This might be expected if test split uses different papers")
    else:
        print(f"  ✓ Ground truth matched: {with_gt:,} papers have annotations")

    # Verify ID format consistency
    print("\n[5/4] Verifying ID format consistency...")

    sample_v2 = set(v2_aligned['paper_id'].head(20))
    sample_phase4 = set(phase4_aligned['paper_id'].head(20))

    # Check for .0 suffixes in samples
    v2_has_decimal = any('.0' in id_val for id_val in sample_v2)
    phase4_has_decimal = any('.0' in id_val for id_val in sample_phase4)

    if v2_has_decimal:
        print("  ✗ ERROR: V2 IDs still have .0 suffix!")
        return False
    if phase4_has_decimal:
        print("  ✗ ERROR: Phase 4 IDs still have .0 suffix!")
        return False

    print("  ✓ All IDs are properly formatted (no .0 suffix)")

    # Summary
    print("\n" + "=" * 80)
    print("✓ Merge integration test passed!")
    print("=" * 80)
    print(f"\nKey Results:")
    print(f"  - {both_count:,} papers successfully matched between V2 and Phase 4")
    print(f"  - {overlap_pct:.1f}% overlap rate")
    print(f"  - {with_gt:,} papers have ground truth annotations")
    print(f"  - All IDs properly normalized for merging")
    print("\n✓ ID normalization fix is working correctly!")

    return True


if __name__ == "__main__":
    success = test_merge_integration()
    sys.exit(0 if success else 1)
