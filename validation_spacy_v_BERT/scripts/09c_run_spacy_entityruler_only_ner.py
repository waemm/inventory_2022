#!/usr/bin/env python3
"""
Script 09c: Run spaCy EntityRuler-Only NER on Phase 2 Dataset

Purpose: Extract biodata resource entities using ONLY EntityRuler (Statistical NER DISABLED)
Input: Phase 2 union classification results (~50k papers)
Output: EntityRuler-only NER results CSV and benchmark JSON

Usage:
    python validation_spacy_v_BERT/scripts/09c_run_spacy_entityruler_only_ner.py

Requirements:
    - spaCy environment: source spacy_hybrid_ner/venv/bin/activate
    - Input file: validation_spacy_v_BERT/results/phase2/classification/union_v2_pycaret_150k_2025-11-14-wi1hs6_with_abstracts.csv
    - Model: spacy_hybrid_ner/models/ner_hybrid_v2_com_ful

Runtime: ~0.5-2 hours (CPU, 100-200 papers/sec)
"""

import pandas as pd
import spacy
from tqdm import tqdm
import json
import time
import datetime
import random
import string
from pathlib import Path
import sys

# Configuration
INPUT_FILE = "validation_spacy_v_BERT/results/phase2/classification/union_v2_pycaret_150k_2025-11-14-wi1hs6_with_abstracts.csv"
MODEL_PATH = "spacy_hybrid_ner/models/ner_hybrid_v2_com_ful"
OUTPUT_DIR = "validation_spacy_v_BERT/results/phase2/ner"
BENCHMARK_DIR = "validation_spacy_v_BERT/results/phase2/benchmarks"

# Processing parameters
BATCH_SIZE = 64
PROGRESS_INTERVAL = 1000

# Generate session ID
SESSION_ID = f"{datetime.datetime.now().strftime('%Y-%m-%d')}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"

# Output files
OUTPUT_FILE = f"{OUTPUT_DIR}/spacy_ner_entityruler_only_results_{SESSION_ID}.csv"
BENCHMARK_FILE = f"{BENCHMARK_DIR}/spacy_ner_entityruler_only_benchmark_{SESSION_ID}.json"


def load_spacy_entityruler_only(model_path):
    """Load spaCy model with Statistical NER disabled for EntityRuler-only extraction"""
    print("Loading spaCy model (EntityRuler-only mode)...")

    # Check model exists
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    # Load model
    nlp = spacy.load(model_path)

    # Disable Statistical NER components (tok2vec and ner)
    stat_components = ['tok2vec', 'ner']
    disabled_count = 0

    for comp in stat_components:
        if comp in nlp.pipe_names:
            nlp.disable_pipe(comp)
            print(f"  ✓ Disabled: {comp}")
            disabled_count += 1

    if disabled_count == 0:
        print("  ⚠ Warning: No Statistical NER components found in pipeline")
    else:
        print("  ✓ EntityRuler-only mode ACTIVE")

    # Verify active and disabled components
    print(f"\nActive pipeline: {nlp.pipe_names}")
    print(f"Disabled components: {list(nlp.disabled)}")

    # Verify EntityRuler component is present
    if 'entity_ruler' not in nlp.pipe_names:
        raise ValueError("EntityRuler component not found in pipeline!")

    print("✓ Model ready for EntityRuler-only extraction\n")

    return nlp


def main():
    print("=" * 70)
    print("SPACY ENTITYRULER-ONLY NER EXTRACTION")
    print("=" * 70)
    print(f"Session ID: {SESSION_ID}")
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 70)
    print()

    # Load input data
    print("Loading input file...")
    df = pd.read_csv(INPUT_FILE)
    print(f"✓ Loaded {len(df):,} papers")

    # Detect ID column
    id_col = None
    for col in ['id', 'publication_id', 'pubmed_id', 'PMID', 'pmid']:
        if col in df.columns:
            id_col = col
            break

    if not id_col:
        raise ValueError(f"No ID column found. Available: {list(df.columns)}")

    print(f"✓ Using ID column: {id_col}")

    # Check for title and abstract
    if 'title' not in df.columns or 'abstract' not in df.columns:
        raise ValueError("Missing 'title' or 'abstract' columns")

    # Combine title + abstract
    df['text'] = df['title'].fillna('') + ' ' + df['abstract'].fillna('')
    print(f"✓ Prepared text for {len(df):,} papers\n")

    # Load model with Statistical NER disabled
    nlp = load_spacy_entityruler_only(MODEL_PATH)

    # Create output directories
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(BENCHMARK_DIR).mkdir(parents=True, exist_ok=True)

    # Extract entities
    print(f"Extracting entities from {len(df):,} papers...")
    print("=" * 70)

    all_entities = []
    papers_with_entities = 0

    start_time = time.time()

    # Process with batch pipeline
    for i, doc in enumerate(tqdm(nlp.pipe(df['text'], batch_size=BATCH_SIZE),
                                  total=len(df),
                                  desc="Extracting entities")):

        paper_id = df.iloc[i][id_col]
        text = df.iloc[i]['text']

        # Extract entities from document
        doc_entities = []
        for ent in doc.ents:
            # In EntityRuler-only mode, all entities should have canonical IDs (ent_id_)
            source = 'ruler' if ent.ent_id_ else 'statistical'
            canonical_id = ent.ent_id_ if ent.ent_id_ else None

            entity = {
                'ID': str(paper_id),
                'text': text,
                'mention': ent.text,
                'label': ent.label_,
                'canonical_id': canonical_id,
                'source': source,
                'start_char': ent.start_char,
                'end_char': ent.end_char
            }
            doc_entities.append(entity)

        if doc_entities:
            papers_with_entities += 1

        all_entities.extend(doc_entities)

    # Calculate stats
    elapsed = time.time() - start_time
    speed = len(df) / elapsed

    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Papers processed: {len(df):,}")
    print(f"Total entities: {len(all_entities):,}")
    print(f"Papers with entities: {papers_with_entities:,} ({100*papers_with_entities/len(df):.1f}%)")
    print(f"Avg entities/paper: {len(all_entities)/len(df):.2f}")
    print(f"\nProcessing time: {elapsed/60:.2f} minutes")
    print(f"Speed: {speed:.1f} papers/second")
    print("=" * 70)
    print()

    # Save results
    df_results = pd.DataFrame(all_entities)

    print("Saving results...")
    df_results.to_csv(OUTPUT_FILE, index=False)
    print(f"✓ Saved: {OUTPUT_FILE}")
    print(f"  Rows: {len(df_results):,}")

    # Display statistics
    if len(df_results) > 0:
        print("\nEntity source breakdown:")
        for source, count in df_results['source'].value_counts().items():
            print(f"  {source}: {count:,} ({100*count/len(df_results):.1f}%)")

        # Canonical IDs
        with_canonical = df_results['canonical_id'].notna().sum()
        print(f"\nEntities with canonical IDs: {with_canonical:,} ({100*with_canonical/len(df_results):.1f}%)")

        # Top entities
        print("\nTop 10 most frequent entities:")
        for i, (mention, count) in enumerate(df_results['mention'].value_counts().head(10).items(), 1):
            print(f"  {i:2d}. {mention}: {count:,}")
    else:
        print("\n⚠ WARNING: No entities extracted!")
        print("This suggests the EntityRuler component is non-functional.")

    print()

    # Create benchmark
    benchmark = {
        "session_id": SESSION_ID,
        "timestamp": datetime.datetime.now().isoformat(),
        "model": {
            "name": "spacy_hybrid_ner_entityruler_only",
            "path": MODEL_PATH,
            "components": nlp.pipe_names,
            "disabled": list(nlp.disabled),
            "mode": "entityruler_only"
        },
        "input": {
            "file": INPUT_FILE,
            "papers": len(df)
        },
        "processing": {
            "batch_size": BATCH_SIZE,
            "time_seconds": round(elapsed, 2),
            "time_minutes": round(elapsed/60, 2),
            "speed_papers_per_sec": round(speed, 2)
        },
        "results": {
            "papers_processed": len(df),
            "papers_with_entities": papers_with_entities,
            "coverage_percent": round(100*papers_with_entities/len(df), 2),
            "total_entities": len(all_entities),
            "avg_entities_per_paper": round(len(all_entities)/len(df), 2),
            "unique_canonical_ids": int(df_results['canonical_id'].nunique()) if len(df_results) > 0 else 0,
            "entities_with_canonical_id": int(df_results['canonical_id'].notna().sum()) if len(df_results) > 0 else 0
        },
        "output": {
            "file": OUTPUT_FILE,
            "rows": len(df_results)
        }
    }

    # Save benchmark
    with open(BENCHMARK_FILE, 'w') as f:
        json.dump(benchmark, f, indent=2)

    print(f"✓ Saved benchmark: {BENCHMARK_FILE}")

    print("\n" + "=" * 70)
    print("✓ ENTITYRULER-ONLY NER COMPLETE")
    print("=" * 70)
    print(f"Session: {SESSION_ID}")
    print(f"Entities extracted: {len(df_results):,}")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
