#!/usr/bin/env python3
"""
Script 04b: Run spaCy Hybrid NER
==================================

Purpose:
    Run spaCy Hybrid NER (EntityRuler + Statistical NER) on validation sample.
    Extracts biodata resource entities from both dictionary and learned patterns.

Models:
    - EntityRuler: Dictionary-based exact matching (752 resources)
    - Statistical NER: Learned patterns for new resource discovery

Usage:
    cd /Users/warren/development/GBC/inventory_2022/validation_spacy_v_BERT
    source ../spacy_hybrid_ner/venv/bin/activate
    python scripts/04b_run_spacy_ner.py

    For testing with small sample:
    TEST_MODE=True python scripts/04b_run_spacy_ner.py

Inputs:
    - results/validation/sample/validation_sample_with_abstracts.csv
    - ../../spacy_hybrid_ner/models/ner_hybrid_v2_com_ful/

Outputs:
    - results/validation/ner/spacy_ner_results.csv
    - logs/04b_run_spacy_ner.log

Environment: spacy_hybrid_ner/venv/ (Python 3.11.9, spaCy 3.7.0)

Author: Phase 1 Validation Study
Date: 2025-11-13
"""

import sys
import os
import pandas as pd
import spacy
from pathlib import Path
import logging
from datetime import datetime
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

# TEST_MODE: Set to True for quick testing (10-15 papers)
#            Set to False for full validation (all papers in sample)
TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
SESSION_ID = os.environ.get('SESSION_ID', '')
if not SESSION_ID:
    # Generate session ID if not provided
    import random
    import string
    from datetime import datetime
    mode_suffix = "_test" if TEST_MODE else ""
    SESSION_ID = f"{datetime.now().strftime('%Y-%m-%d')}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}{mode_suffix}"

TEST_SIZE = 15 if TEST_MODE else None

if TEST_MODE:
    print("\n🧪 TEST MODE ENABLED")
    print(f"   Will process first {TEST_SIZE} papers\n")
else:
    print("\n🚀 PRODUCTION MODE")
    print("   Will process all papers in validation sample\n")

# Paths (relative to validation_spacy_v_BERT/) - use _test suffix in TEST_MODE
VALIDATION_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = VALIDATION_ROOT.parent

output_suffix = f"_{SESSION_ID}" if SESSION_ID else ("_test" if TEST_MODE else "")
SAMPLE_FILE = VALIDATION_ROOT / f"results/validation/sample/validation_sample_with_abstracts{output_suffix}.csv"
OUTPUT_DIR = VALIDATION_ROOT / "results/validation/ner"
OUTPUT_FILE = OUTPUT_DIR / f"spacy_ner_results{output_suffix}.csv"
LOG_FILE = VALIDATION_ROOT / "logs/04b_run_spacy_ner.log"

# Model path (relative to project root)
MODEL_PATH = PROJECT_ROOT / "spacy_hybrid_ner/models/ner_hybrid_v2_com_ful"

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

def run_spacy_ner(nlp, sample_df):
    """
    Run spaCy Hybrid NER on validation sample.

    Args:
        nlp: Loaded spaCy hybrid pipeline
        sample_df: DataFrame with validation sample

    Returns:
        DataFrame with entity extractions
    """
    logger.info(f"🔮 Running spaCy Hybrid NER on {len(sample_df)} papers...")
    logger.info(f"   This may take several minutes...")

    # Identify columns
    id_col = None
    for col in ['publication_id', 'pubmed_id', 'PMID', 'pmid', 'id']:
        if col in sample_df.columns:
            id_col = col
            break

    if not id_col:
        raise ValueError(f"No ID column found. Available: {list(sample_df.columns)}")

    title_col = None
    for col in ['title', 'title_test', 'title_meta']:
        if col in sample_df.columns:
            title_col = col
            break

    abstract_col = 'abstract' if 'abstract' in sample_df.columns else None

    # Track results
    all_extractions = []
    papers_with_entities = 0
    ruler_entity_count = 0
    statistical_entity_count = 0
    unique_ruler_resources = set()
    unique_statistical_resources = set()

    # Process each paper
    for idx, paper in sample_df.iterrows():
        # Get text
        title = str(paper[title_col]) if title_col and pd.notna(paper.get(title_col)) else ''
        abstract = str(paper[abstract_col]) if abstract_col and pd.notna(paper.get(abstract_col)) else ''
        text = f"{title} {abstract}".strip()

        if len(text) < 10:
            logger.warning(f"  Paper {paper[id_col]}: Text too short, skipping")
            continue

        # Run spaCy NER
        doc = nlp(text)

        paper_entities = []

        for ent in doc.ents:
            # Determine source: EntityRuler (has ent_id_) or Statistical NER (no ent_id_)
            if ent.ent_id_:  # From EntityRuler (dictionary)
                source = 'ruler'
                canonical_id = ent.ent_id_
                unique_ruler_resources.add(canonical_id)
                ruler_entity_count += 1
            else:  # From Statistical NER (learned patterns)
                source = 'statistical'
                canonical_id = None
                unique_statistical_resources.add(ent.text.lower())
                statistical_entity_count += 1

            paper_entities.append({
                'ID': str(paper[id_col]),
                'text': text,
                'mention': ent.text,
                'label': ent.label_,
                'canonical_id': canonical_id,
                'source': source,
                'start_char': ent.start_char,
                'end_char': ent.end_char
            })

        if len(paper_entities) > 0:
            papers_with_entities += 1

        all_extractions.extend(paper_entities)

        # Progress logging
        if (idx + 1) % 10 == 0:
            logger.info(f"  Progress: [{idx+1}/{len(sample_df)}] papers processed...")

    # Create results DataFrame
    predictions_df = pd.DataFrame(all_extractions)

    logger.info(f"✓ spaCy NER predictions complete")
    logger.info(f"  Total entities extracted: {len(predictions_df)}")
    logger.info(f"  Papers with entities: {papers_with_entities}/{len(sample_df)}")
    logger.info(f"  Entity sources:")
    logger.info(f"    - EntityRuler (dictionary): {ruler_entity_count} ({100*ruler_entity_count/(ruler_entity_count+statistical_entity_count):.1f}%)")
    logger.info(f"    - Statistical NER (learned): {statistical_entity_count} ({100*statistical_entity_count/(ruler_entity_count+statistical_entity_count):.1f}%)")
    logger.info(f"  Unique resources:")
    logger.info(f"    - Known (ruler): {len(unique_ruler_resources)}")
    logger.info(f"    - Discovered (statistical): {len(unique_statistical_resources)}")

    return predictions_df

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("SCRIPT 04b: SPACY HYBRID NER")
    logger.info("=" * 70)

    start_time = datetime.now()

    # ------------------------------------------------------------------------
    # 1. Validate inputs
    # ------------------------------------------------------------------------
    logger.info("\n🔍 Validating inputs...")

    if not SAMPLE_FILE.exists():
        logger.error(f"❌ Sample file not found: {SAMPLE_FILE}")
        logger.error("Please run script 02 first: python scripts/02_fetch_abstracts.py")
        return 1

    if not MODEL_PATH.exists():
        logger.error(f"❌ Model not found: {MODEL_PATH}")
        logger.error("Expected spaCy Hybrid NER model directory")
        return 1

    logger.info(f"✓ Sample file: {SAMPLE_FILE}")
    logger.info(f"✓ Model: {MODEL_PATH}")

    # ------------------------------------------------------------------------
    # 2. Load validation sample
    # ------------------------------------------------------------------------
    logger.info("\n📚 Loading validation sample...")
    df_sample = pd.read_csv(SAMPLE_FILE)
    logger.info(f"✓ Loaded {len(df_sample)} papers")

    # Apply TEST_MODE if enabled
    if TEST_MODE:
        logger.info(f"🧪 TEST_MODE: Using first {TEST_SIZE} papers")
        df_sample = df_sample.head(TEST_SIZE)
        logger.info(f"✓ Test sample size: {len(df_sample)} papers")

    # Check for abstracts
    has_abstract = df_sample['abstract'].notna() & (df_sample['abstract'] != '')
    logger.info(f"  - Papers with abstracts: {has_abstract.sum()}/{len(df_sample)} ({100*has_abstract.sum()/len(df_sample):.1f}%)")

    # ------------------------------------------------------------------------
    # 3. Load spaCy Hybrid NER model
    # ------------------------------------------------------------------------
    logger.info(f"\n🤖 Loading spaCy Hybrid NER model...")
    logger.info(f"   Model: {MODEL_PATH}")

    try:
        nlp = spacy.load(str(MODEL_PATH))
        logger.info(f"✓ spaCy model loaded successfully")

        # Show pipeline components
        logger.info(f"  Pipeline components: {nlp.pipe_names}")

        # Check for expected components
        expected_components = ['entityruler', 'ner']
        for comp in expected_components:
            if comp in nlp.pipe_names:
                logger.info(f"    ✓ {comp}")
            else:
                logger.warning(f"    ⚠️  {comp} not found (may affect results)")

    except Exception as e:
        logger.error(f"❌ Failed to load spaCy model: {e}")
        logger.error(f"   Please ensure spacy_hybrid_ner environment is activated")
        logger.error(f"   source ../spacy_hybrid_ner/venv/bin/activate")
        return 1

    # ------------------------------------------------------------------------
    # 4. Run spaCy NER
    # ------------------------------------------------------------------------
    predictions_df = run_spacy_ner(nlp, df_sample)

    # ------------------------------------------------------------------------
    # 5. Calculate summary statistics
    # ------------------------------------------------------------------------
    logger.info(f"\n{'=' * 70}")
    logger.info("SUMMARY STATISTICS")
    logger.info(f"{'=' * 70}")
    logger.info(f"Total papers:              {len(df_sample)}")
    logger.info(f"Total entities extracted:  {len(predictions_df)}")
    logger.info(f"Papers with entities:      {predictions_df['ID'].nunique()}/{len(df_sample)}")
    logger.info(f"Avg entities per paper:    {len(predictions_df)/len(df_sample):.2f}")

    # Entity type breakdown
    if 'label' in predictions_df.columns:
        logger.info(f"\nEntity types:")
        for label, count in predictions_df['label'].value_counts().items():
            logger.info(f"  - {label}: {count} ({100*count/len(predictions_df):.1f}%)")

    # Source breakdown
    if 'source' in predictions_df.columns:
        logger.info(f"\nEntity sources:")
        for source, count in predictions_df['source'].value_counts().items():
            logger.info(f"  - {source}: {count} ({100*count/len(predictions_df):.1f}%)")

    # ------------------------------------------------------------------------
    # 6. Save results
    # ------------------------------------------------------------------------
    logger.info(f"\n💾 Saving results...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clean results
    predictions_df = predictions_df.replace(r'\n', ' ', regex=True)
    predictions_df.to_csv(OUTPUT_FILE, index=False)

    logger.info(f"✓ Saved to: {OUTPUT_FILE}")
    logger.info(f"  Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    logger.info(f"  Columns: {list(predictions_df.columns)}")

    # ------------------------------------------------------------------------
    # 7. Final report
    # ------------------------------------------------------------------------
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ SCRIPT 04b COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Log saved to: {LOG_FILE}")
    logger.info(f"Results saved to: {OUTPUT_FILE}")
    logger.info(f"\nNext step: Compare NER results")
    logger.info(f"  python scripts/04c_compare_ner.py")
    logger.info(f"{'=' * 70}")

    return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
