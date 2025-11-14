#!/usr/bin/env python3
"""
Script 02: Fetch Abstracts from EuropePMC
==========================================

Purpose:
    Fetch abstracts from EPMC API for all papers in validation sample.
    Re-fetches ALL abstracts for consistency (Option B).

Usage:
    cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT
    source ../biodata_modern_env/bin/activate
    python scripts/02_fetch_abstracts.py

    For testing with small sample:
    TEST_MODE=True python scripts/02_fetch_abstracts.py

Inputs:
    - results/validation/sample/validation_sample.csv (or validation_sample_test.csv in TEST_MODE)

Outputs:
    - results/validation/sample/validation_sample_with_abstracts.csv (or *_test.csv in TEST_MODE)
    - logs/02_fetch_abstracts.log

Author: Phase 1 Validation Study
Date: 2025-11-13
"""

import os
import pandas as pd
import requests
import time
from pathlib import Path
import logging
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# TEST_MODE: Set to True to process test sample (_test files)
TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'

if TEST_MODE:
    print("\n🧪 TEST MODE ENABLED")
    print("   Will fetch abstracts for test sample\n")
else:
    print("\n🚀 PRODUCTION MODE")
    print("   Will fetch abstracts for full validation sample\n")

# Paths (relative to validation_spacy_v_BERT/)
# NO session ID - these are INPUT files that don't change between runs
output_suffix = "_test" if TEST_MODE else ""
SAMPLE_FILE = Path(f"results/validation/sample/validation_sample{output_suffix}.csv")
OUTPUT_FILE = Path(f"results/validation/sample/validation_sample_with_abstracts{output_suffix}.csv")
LOG_FILE = Path("logs/02_fetch_abstracts.log")

# EPMC API
EPMC_API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# Rate limiting (max ~6-7 requests/sec)
SLEEP_BETWEEN_REQUESTS = 0.15  # seconds

# ============================================================================
# LOGGING SETUP
# ============================================================================

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# FUNCTIONS
# ============================================================================

def fetch_abstract(pmid, retry=True):
    """
    Fetch abstract for a single PMID from EPMC API.

    Args:
        pmid: PubMed ID
        retry: Whether to retry on failure

    Returns:
        str: Abstract text, or None if not found
    """
    params = {
        'query': f'ext_id:{pmid}',
        'resultType': 'core',
        'format': 'json'
    }

    try:
        response = requests.get(EPMC_API_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = data.get('resultList', {}).get('result', [])

        if results:
            abstract = results[0].get('abstractText', '')
            if abstract:
                return abstract
            else:
                logger.info(f"  PMID {pmid}: No abstract in EPMC")
                return None
        else:
            logger.warning(f"  PMID {pmid}: No results from EPMC")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"  PMID {pmid}: Timeout")
        if retry:
            logger.info(f"  PMID {pmid}: Retrying with longer timeout...")
            time.sleep(1)
            try:
                response = requests.get(EPMC_API_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                results = data.get('resultList', {}).get('result', [])
                if results:
                    return results[0].get('abstractText', '')
            except Exception as e:
                logger.error(f"  PMID {pmid}: Retry failed - {e}")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"  PMID {pmid}: Request error - {e}")
        if retry:
            logger.info(f"  PMID {pmid}: Retrying once...")
            time.sleep(1)
            return fetch_abstract(pmid, retry=False)
        return None

    except Exception as e:
        logger.error(f"  PMID {pmid}: Unexpected error - {e}")
        return None


def identify_pmid_column(df):
    """
    Identify which column contains PMIDs.

    Args:
        df: DataFrame

    Returns:
        str: Column name containing PMIDs

    Raises:
        ValueError: If no PMID column found
    """
    possible_names = ['pubmed_id', 'PMID', 'pmid', 'publication_id', 'id']

    for col in possible_names:
        if col in df.columns:
            logger.info(f"✓ Using ID column: {col}")
            return col

    raise ValueError(
        f"No PMID column found. Columns available: {list(df.columns)}\n"
        f"Expected one of: {possible_names}"
    )


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("SCRIPT 02: FETCH ABSTRACTS FROM EPMC")
    logger.info("=" * 70)

    start_time = datetime.now()

    # ------------------------------------------------------------------------
    # 1. Load validation sample
    # ------------------------------------------------------------------------
    logger.info("\n📚 Loading validation sample...")

    if not SAMPLE_FILE.exists():
        logger.error(f"❌ Sample file not found: {SAMPLE_FILE}")
        logger.error("Please run script 01 first: python scripts/01_select_validation_sample.py")
        return 1

    df = pd.read_csv(SAMPLE_FILE)
    logger.info(f"✓ Loaded {len(df)} papers")

    # ------------------------------------------------------------------------
    # 2. Identify PMID column
    # ------------------------------------------------------------------------
    try:
        pmid_col = identify_pmid_column(df)
    except ValueError as e:
        logger.error(f"❌ {e}")
        return 1

    # ------------------------------------------------------------------------
    # 3. Fetch abstracts for ALL papers (re-fetch for consistency)
    # ------------------------------------------------------------------------
    logger.info(f"\n🔍 Fetching abstracts from EPMC for ALL papers...")
    logger.info(f"   (Re-fetching all abstracts for consistency)")
    logger.info(f"   Rate limit: ~6-7 requests/sec")
    logger.info(f"   Estimated time: {int(len(df) * SLEEP_BETWEEN_REQUESTS / 60)} minutes")
    logger.info("")

    abstracts = []
    success_count = 0
    no_abstract_count = 0
    error_count = 0

    for idx, row in df.iterrows():
        pmid = row[pmid_col]

        # Log progress every 10 papers
        if (idx + 1) % 10 == 0:
            logger.info(f"Progress: [{idx+1}/{len(df)}] papers processed...")
        else:
            logger.debug(f"[{idx+1}/{len(df)}] Fetching PMID {pmid}...")

        # Fetch abstract
        abstract = fetch_abstract(pmid)

        if abstract:
            abstracts.append(abstract)
            success_count += 1
        elif abstract == '':
            abstracts.append('')
            no_abstract_count += 1
        else:
            abstracts.append('')
            error_count += 1

        # Rate limiting
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    # ------------------------------------------------------------------------
    # 4. Add abstracts to DataFrame
    # ------------------------------------------------------------------------
    logger.info(f"\n📝 Adding abstracts to DataFrame...")

    # Add or replace abstract column
    df['abstract'] = abstracts

    # ------------------------------------------------------------------------
    # 5. Summary statistics
    # ------------------------------------------------------------------------
    has_abstract = df['abstract'].notna() & (df['abstract'] != '')

    logger.info(f"\n{'=' * 70}")
    logger.info("SUMMARY")
    logger.info(f"{'=' * 70}")
    logger.info(f"Total papers:              {len(df)}")
    logger.info(f"Successfully fetched:      {success_count}")
    logger.info(f"No abstract in EPMC:       {no_abstract_count}")
    logger.info(f"Errors/not found:          {error_count}")
    logger.info(f"Final papers with abstract: {has_abstract.sum()}/{len(df)} ({100*has_abstract.sum()/len(df):.1f}%)")

    # ------------------------------------------------------------------------
    # 6. Save output
    # ------------------------------------------------------------------------
    logger.info(f"\n💾 Saving output...")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    logger.info(f"✓ Saved to: {OUTPUT_FILE}")

    # ------------------------------------------------------------------------
    # 7. Final report
    # ------------------------------------------------------------------------
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ SCRIPT 02 COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Log saved to: {LOG_FILE}")
    logger.info(f"Output saved to: {OUTPUT_FILE}")
    logger.info(f"\nNext step: Run classification comparison scripts")
    logger.info(f"{'=' * 70}")

    return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
