#!/usr/bin/env python3
"""
Test script to verify the comma-separated ID fix in load_inventory().
"""

import pandas as pd
import tempfile
import logging
from pathlib import Path

# Add parent directory to path to import utils
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils.data_loading import load_inventory

# Configure logging to see warnings
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_comma_separated_ids():
    """Test that load_inventory() correctly handles comma-separated IDs."""

    # Create a test CSV with comma-separated IDs
    test_data = {
        'pmid': ['12345678', '27924021, 32162267', '98765432', '11111111, 22222222, 33333333'],
        'title': ['Paper 1', 'Paper 2', 'Paper 3', 'Paper 4'],
        'abstract': ['Abstract 1', 'Abstract 2', 'Abstract 3', 'Abstract 4']
    }

    df_test = pd.DataFrame(test_data)

    # Write to temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        df_test.to_csv(tmp.name, index=False)
        tmp_path = Path(tmp.name)

    try:
        print("Test data created:")
        print(df_test)
        print("\n" + "="*70 + "\n")

        # Load with our fixed function
        print("Loading inventory with comma-separated ID fix...")
        df_loaded = load_inventory(file_path=tmp_path)

        print("\n" + "="*70 + "\n")
        print("Loaded data:")
        print(df_loaded)

        # Verify results
        print("\n" + "="*70 + "\n")
        print("Verification:")
        print(f"  Original first comma-separated ID: '27924021, 32162267'")
        print(f"  Loaded as: '{df_loaded.loc[1, 'pmid']}'")
        print(f"  Expected: '27924021'")
        print(f"  Match: {df_loaded.loc[1, 'pmid'] == '27924021'}")

        print(f"\n  Original second comma-separated ID: '11111111, 22222222, 33333333'")
        print(f"  Loaded as: '{df_loaded.loc[3, 'pmid']}'")
        print(f"  Expected: '11111111'")
        print(f"  Match: {df_loaded.loc[3, 'pmid'] == '11111111'}")

        # Check all IDs are strings without .0 suffix
        print(f"\n  All PMIDs are strings: {df_loaded['pmid'].dtype == 'object'}")
        print(f"  No .0 suffixes: {not any('.0' in str(x) for x in df_loaded['pmid'])}")

        if df_loaded.loc[1, 'pmid'] == '27924021' and df_loaded.loc[3, 'pmid'] == '11111111':
            print("\n✓ TEST PASSED: Comma-separated IDs handled correctly!")
        else:
            print("\n✗ TEST FAILED: IDs not processed correctly")

    finally:
        # Clean up temp file
        tmp_path.unlink()
        print(f"\nCleaned up temporary file: {tmp_path}")

if __name__ == '__main__':
    test_comma_separated_ids()
