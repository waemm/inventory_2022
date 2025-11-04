"""
Test script to verify the NaN cartesian product fix in InferenceDataset

This script simulates the exact data loading and merge process to verify
that the fix prevents the 13.5x result multiplication.

Expected behavior AFTER fix:
- Input: ~21,429 papers
- Filter out: ~540 papers with NaN IDs
- Output: ~20,889 papers (NOT 288,730!)
"""

import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from transformers import AutoTokenizer
from multitask_predict import InferenceDataset

def test_inference_dataset_no_multiplication():
    """Test that InferenceDataset does not multiply results"""

    print("="*80)
    print("TESTING INFERENCE DATASET FIX")
    print("="*80)

    # Load actual data files
    print("\n📥 Loading data files...")
    papers_df = pd.read_csv('data/epmc_query_results_2022.csv')
    metadata_df = pd.read_csv('data/metadata/features_engineered.csv')

    print(f"✅ Loaded papers: {len(papers_df):,} rows")
    print(f"✅ Loaded metadata: {len(metadata_df):,} rows")

    # Count NaN IDs before
    papers_nan = papers_df['id'].isna().sum()
    metadata_nan = metadata_df['id'].isna().sum()

    print(f"\n📊 Data quality check:")
    print(f"   Papers with NaN ID: {papers_nan} ({papers_nan/len(papers_df)*100:.1f}%)")
    print(f"   Metadata with NaN ID: {metadata_nan} ({metadata_nan/len(metadata_df)*100:.1f}%)")
    print(f"   Expected cartesian product if not fixed: {papers_nan} × {metadata_nan} = {papers_nan * metadata_nan:,} rows")

    # Load tokenizer
    print("\n📚 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500'
    )

    # Create InferenceDataset (this should trigger the fix)
    print("\n🔄 Creating InferenceDataset (fix will log warnings)...")
    print("-" * 80)

    dataset = InferenceDataset(
        papers_df=papers_df,
        metadata_df=metadata_df,
        tokenizer=tokenizer,
        max_length=256,
        n_expected_features=28
    )

    print("-" * 80)

    # Check results
    dataset_size = len(dataset)
    expected_size = len(papers_df) - papers_nan  # Papers minus NaN rows

    print(f"\n📊 Results:")
    print(f"   Input papers: {len(papers_df):,}")
    print(f"   Papers with NaN ID (filtered): {papers_nan:,}")
    print(f"   Expected output size: ~{expected_size:,}")
    print(f"   Actual dataset size: {dataset_size:,}")

    # Verify no multiplication
    multiplication_ratio = dataset_size / len(papers_df)

    print(f"\n🔍 Verification:")
    print(f"   Multiplication ratio: {multiplication_ratio:.2f}x")

    if multiplication_ratio > 1.5:
        print("\n❌ FAIL: Result multiplication detected!")
        print(f"   Expected: ~1.0x (or slightly less due to NaN filtering)")
        print(f"   Actual: {multiplication_ratio:.2f}x")
        print("\n   The fix did NOT work. Dataset still multiplying results.")
        return False
    elif dataset_size > len(papers_df) * 0.95 and dataset_size <= len(papers_df):
        print("\n✅ PASS: No multiplication, expected filtering detected")
        print(f"   Dataset correctly filtered {len(papers_df) - dataset_size:,} papers with NaN IDs")
        return True
    elif dataset_size < len(papers_df) * 0.95:
        print("\n⚠️  WARNING: Dataset smaller than expected")
        print(f"   This could be correct if many papers have NaN IDs")
        print(f"   Filtered: {len(papers_df) - dataset_size:,} papers")

        # Check if this matches NaN count
        if abs(dataset_size - expected_size) < 100:
            print("   ✅ Size matches expected (papers - NaN count)")
            return True
        else:
            print(f"   ❌ Size mismatch: expected ~{expected_size:,}, got {dataset_size:,}")
            return False
    else:
        print("\n❓ UNEXPECTED: Dataset size exactly matches input")
        print("   This could mean:")
        print("   1. No NaN IDs in the data (unlikely)")
        print("   2. Filter is not working")
        return False

if __name__ == '__main__':
    success = test_inference_dataset_no_multiplication()

    print("\n" + "="*80)
    if success:
        print("🎉 TEST PASSED: Fix successfully prevents result multiplication")
        print("="*80)
        sys.exit(0)
    else:
        print("❌ TEST FAILED: Fix did not work as expected")
        print("="*80)
        sys.exit(1)
