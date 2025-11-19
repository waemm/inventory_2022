#!/usr/bin/env python3
"""
Track 52 GCBRs Through Complete Pipeline

Track high-priority bioresources through 10 pipeline stages:
1. EPMC Query (149,943 papers)
2. V2 Classification (12,285 papers)
3. PyCaret Classification (46,766 papers)
4. Classification Union (50,192 papers)
5. spaCy NER (32,317 papers)
6. V2 NER (18,319 papers)
7. NER Union (34,279 papers)
8. Linguistic Filtering (8,683 papers)
9. SetFit Filtering (7,938 papers)
10. Union Filtering (16,605 papers)
"""

import pandas as pd
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Paths
BASE_DIR = Path("/Users/warren/development/GBC/inventory_2022")
GCBR_FILE = BASE_DIR / "GCBR_tagging_sheet_validated.csv"

# Data files
EPMC_QUERY_FILE = BASE_DIR / "validation_spacy_v_BERT/data/v5.1_cleaned.csv"
V2_CLASSIF_DIR = BASE_DIR / "validation_spacy_v_BERT/results/phase2/classification"
SPACY_NER_FILE = BASE_DIR / "validation_spacy_v_BERT/results/phase2/ner/spacy_ner_full_hybrid_results_2025-11-16-q9tnzj.csv"
V2_NER_FILE = BASE_DIR / "validation_spacy_v_BERT/results/phase2/ner/v2_ner_results_2025-11-15-icond7.csv"

# Paper sets from Phase 2
PAPER_SETS_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/data/paper_sets"

# Entity inventories from Phase 2
ENTITY_INVENTORIES_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/data/entity_inventories"

# Output directory
OUTPUT_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/results/gcbr_tracking"

def normalize_name(name):
    """Normalize resource name for matching"""
    if pd.isna(name):
        return None
    return str(name).strip().lower()

def load_gcbr_reference():
    """Load GCBR reference data"""
    print("Loading GCBR reference data...")
    df = pd.read_csv(GCBR_FILE)

    gcbrs = []
    for _, row in df.iterrows():
        name = row.get('GCBR name (GBC website)', '')
        if pd.isna(name) or name == '':
            continue

        gcbrs.append({
            'gcbr_name': name,
            'normalized_name': normalize_name(name),
            'validation_status': row.get('match_validation_status', 'UNKNOWN'),
            'validated_pmids': str(row.get('validated_pmids_about', '')),
            'in_2022_epmc': row.get('in_2022_epmc_query_validated', False)
        })

    print(f"  Loaded {len(gcbrs)} GCBRs")
    return pd.DataFrame(gcbrs)

def text_contains_gcbr(text, gcbr_name):
    """Check if text contains GCBR name (case-insensitive, word boundary)"""
    if pd.isna(text) or pd.isna(gcbr_name):
        return False

    # Escape special regex characters in GCBR name
    pattern = re.escape(gcbr_name)
    return bool(re.search(pattern, str(text), re.IGNORECASE))

def track_stage_1_epmc_query(gcbrs_df):
    """Stage 1: EPMC Query (149,943 papers)"""
    print("\nStage 1: EPMC Query...")
    df_epmc = pd.read_csv(EPMC_QUERY_FILE)
    print(f"  Total papers: {len(df_epmc):,}")

    results = {}
    for _, gcbr in gcbrs_df.iterrows():
        name = gcbr['gcbr_name']
        # Search in title and abstract
        matching_papers = df_epmc[
            df_epmc['title'].apply(lambda x: text_contains_gcbr(x, name)) |
            df_epmc['abstract'].apply(lambda x: text_contains_gcbr(x, name))
        ]
        results[name] = {
            'paper_count': len(matching_papers),
            'pmids': set(matching_papers['id'])  # Column is 'id', not 'pmid'
        }

    print(f"  Tracked {len(results)} GCBRs")
    return results

def track_stage_classification(gcbrs_df, stage_name, file_pattern):
    """Track classification stages (V2, PyCaret, Union)"""
    print(f"\n{stage_name}...")

    # Find classification file
    files = list(V2_CLASSIF_DIR.glob(file_pattern))
    if not files:
        print(f"  WARNING: No files found matching {file_pattern}")
        return {}

    df_classif = pd.read_csv(files[0])
    print(f"  Total papers: {len(df_classif):,}")

    # Check column name (might be 'id', 'pmid', or 'publication_id')
    if 'publication_id' in df_classif.columns:
        id_col = 'publication_id'
    elif 'id' in df_classif.columns:
        id_col = 'id'
    else:
        id_col = 'pmid'

    results = {}
    for _, gcbr in gcbrs_df.iterrows():
        name = gcbr['gcbr_name']
        # Search in title and abstract (if available)
        if 'abstract' in df_classif.columns:
            matching_papers = df_classif[
                df_classif['title'].apply(lambda x: text_contains_gcbr(x, name)) |
                df_classif['abstract'].apply(lambda x: text_contains_gcbr(x, name))
            ]
        else:
            # Only search in title if abstract not available
            matching_papers = df_classif[
                df_classif['title'].apply(lambda x: text_contains_gcbr(x, name))
            ]

        results[name] = {
            'paper_count': len(matching_papers),
            'pmids': set(matching_papers[id_col])
        }

    print(f"  Tracked {len(results)} GCBRs")
    return results

def track_stage_ner(gcbrs_df, stage_name, ner_file):
    """Track NER stages (spaCy, V2, Union)"""
    print(f"\n{stage_name}...")
    df_ner = pd.read_csv(ner_file)
    print(f"  Total entity mentions: {len(df_ner):,}")
    unique_papers = df_ner['ID'].nunique()
    print(f"  Unique papers: {unique_papers:,}")

    results = {}
    for _, gcbr in gcbrs_df.iterrows():
        name = gcbr['gcbr_name']
        normalized = gcbr['normalized_name']

        # Match by entity mention (case-insensitive)
        matching_entities = df_ner[
            df_ner['mention'].apply(lambda x: normalize_name(x) == normalized if pd.notna(x) else False)
        ]

        unique_pmids = set(matching_entities['ID'].astype(str))
        results[name] = {
            'paper_count': len(unique_pmids),
            'pmids': unique_pmids,
            'entity_count': len(matching_entities)
        }

    print(f"  Tracked {len(results)} GCBRs")
    return results

def track_stage_ner_union(gcbrs_df, spacy_results, v2_results):
    """Stage 7: NER Union (combine spaCy + V2)"""
    print("\nStage 7: NER Union...")

    results = {}
    for _, gcbr in gcbrs_df.iterrows():
        name = gcbr['gcbr_name']

        spacy_pmids = spacy_results.get(name, {}).get('pmids', set())
        v2_pmids = v2_results.get(name, {}).get('pmids', set())
        union_pmids = spacy_pmids | v2_pmids

        results[name] = {
            'paper_count': len(union_pmids),
            'pmids': union_pmids,
            'spacy_count': len(spacy_pmids),
            'v2_count': len(v2_pmids)
        }

    print(f"  Tracked {len(results)} GCBRs")
    return results

def track_stage_filtering(gcbrs_df, stage_name, paper_set_file, entity_inventory_file):
    """Track filtering stages (Linguistic, SetFit, Union)"""
    print(f"\n{stage_name}...")

    # Load paper set
    df_papers = pd.read_csv(paper_set_file)
    print(f"  Total papers in set: {len(df_papers):,}")

    # Load entity inventory
    df_inventory = pd.read_csv(entity_inventory_file)
    print(f"  Total entities: {len(df_inventory):,}")

    results = {}
    for _, gcbr in gcbrs_df.iterrows():
        name = gcbr['gcbr_name']
        normalized = gcbr['normalized_name']

        # Find entity in inventory
        matching_entities = df_inventory[
            df_inventory['entity_name'] == normalized
        ]

        if len(matching_entities) > 0:
            # Get PMIDs from inventory
            pmids_str = matching_entities.iloc[0]['pmids']
            pmids = set(str(pmids_str).split(',')) if pd.notna(pmids_str) else set()
            paper_count = len(pmids)
        else:
            pmids = set()
            paper_count = 0

        results[name] = {
            'paper_count': paper_count,
            'pmids': pmids
        }

    print(f"  Tracked {len(results)} GCBRs")
    return results

def main():
    print("=" * 80)
    print("TRACKING 52 GCBRs THROUGH COMPLETE PIPELINE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load GCBR reference
    gcbrs_df = load_gcbr_reference()

    # Track through all stages
    tracking_results = {}

    # Stage 1: EPMC Query
    tracking_results['stage_1_epmc'] = track_stage_1_epmc_query(gcbrs_df)

    # Stage 2: V2 Classification
    tracking_results['stage_2_v2_classif'] = track_stage_classification(
        gcbrs_df, "Stage 2: V2 Classification", "v2_classification_150k_*.csv"
    )

    # Stage 3: PyCaret Classification
    tracking_results['stage_3_pycaret_classif'] = track_stage_classification(
        gcbrs_df, "Stage 3: PyCaret Classification", "pycaret_classification_150k_*.csv"
    )

    # Stage 4: Classification Union
    tracking_results['stage_4_classif_union'] = track_stage_classification(
        gcbrs_df, "Stage 4: Classification Union", "union_v2_pycaret_150k_*.csv"
    )

    # Stage 5: spaCy NER
    tracking_results['stage_5_spacy_ner'] = track_stage_ner(
        gcbrs_df, "Stage 5: spaCy NER", SPACY_NER_FILE
    )

    # Stage 6: V2 NER
    tracking_results['stage_6_v2_ner'] = track_stage_ner(
        gcbrs_df, "Stage 6: V2 NER", V2_NER_FILE
    )

    # Stage 7: NER Union
    tracking_results['stage_7_ner_union'] = track_stage_ner_union(
        gcbrs_df,
        tracking_results['stage_5_spacy_ner'],
        tracking_results['stage_6_v2_ner']
    )

    # Stage 8: Linguistic Filtering
    tracking_results['stage_8_linguistic'] = track_stage_filtering(
        gcbrs_df,
        "Stage 8: Linguistic Filtering",
        PAPER_SETS_DIR / "set_a_linguistic.csv",
        ENTITY_INVENTORIES_DIR / "set_a_entity_inventory.csv"
    )

    # Stage 9: SetFit Filtering
    tracking_results['stage_9_setfit'] = track_stage_filtering(
        gcbrs_df,
        "Stage 9: SetFit Filtering",
        PAPER_SETS_DIR / "set_b_setfit.csv",
        ENTITY_INVENTORIES_DIR / "set_b_entity_inventory.csv"
    )

    # Stage 10: Union Filtering
    tracking_results['stage_10_union'] = track_stage_filtering(
        gcbrs_df,
        "Stage 10: Union Filtering",
        PAPER_SETS_DIR / "set_c_union.csv",
        ENTITY_INVENTORIES_DIR / "set_c_entity_inventory.csv"
    )

    # ========================================================================
    # CREATE TRACKING MATRIX
    # ========================================================================
    print("\n" + "=" * 80)
    print("Creating tracking matrix...")

    tracking_matrix = []
    for _, gcbr in gcbrs_df.iterrows():
        name = gcbr['gcbr_name']
        row = {
            'gcbr_name': name,
            'validation_status': gcbr['validation_status'],
            'in_2022_epmc': gcbr['in_2022_epmc']
        }

        # Add counts for each stage
        for stage_key, stage_data in tracking_results.items():
            stage_name = stage_key.replace('stage_', 's').replace('_', '_')
            row[stage_name] = stage_data.get(name, {}).get('paper_count', 0)

        # Calculate retention rate
        epmc_count = row.get('s1_epmc', 0)
        final_count = row.get('s10_union', 0)
        retention_rate = (final_count / epmc_count * 100) if epmc_count > 0 else 0
        row['retention_rate'] = round(retention_rate, 2)

        tracking_matrix.append(row)

    df_matrix = pd.DataFrame(tracking_matrix)

    # Save tracking matrix
    matrix_file = OUTPUT_DIR / "gcbr_tracking_complete.csv"
    df_matrix.to_csv(matrix_file, index=False)
    print(f"  Saved: {matrix_file}")

    # ========================================================================
    # CALCULATE SUMMARY STATISTICS
    # ========================================================================
    print("\nCalculating summary statistics...")

    # Capture patterns
    capture_stats = {
        'full_capture': len(df_matrix[df_matrix['s10_union'] > 0]),
        'zero_capture': len(df_matrix[df_matrix['s10_union'] == 0]),
        'high_retention': len(df_matrix[df_matrix['retention_rate'] >= 75]),
        'medium_retention': len(df_matrix[(df_matrix['retention_rate'] >= 25) & (df_matrix['retention_rate'] < 75)]),
        'low_retention': len(df_matrix[df_matrix['retention_rate'] < 25])
    }

    # Stage totals
    stage_totals = {}
    for col in df_matrix.columns:
        if col.startswith('s') and col not in ['gcbr_name', 'validation_status']:
            stage_totals[col] = int(df_matrix[col].sum())

    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_gcbrs': len(gcbrs_df),
        'capture_stats': capture_stats,
        'stage_totals': stage_totals,
        'avg_retention_rate': round(df_matrix['retention_rate'].mean(), 2),
        'median_retention_rate': round(df_matrix['retention_rate'].median(), 2)
    }

    summary_file = OUTPUT_DIR / "gcbr_tracking_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved: {summary_file}")

    # ========================================================================
    # SUMMARY REPORT
    # ========================================================================
    print("\n" + "=" * 80)
    print("GCBR TRACKING SUMMARY")
    print("=" * 80)
    print(f"Total GCBRs tracked: {len(gcbrs_df)}")
    print()
    print("CAPTURE PATTERNS:")
    print(f"  Full capture (>0 papers in final): {capture_stats['full_capture']} ({capture_stats['full_capture']/len(gcbrs_df)*100:.1f}%)")
    print(f"  Zero capture (0 papers in final):  {capture_stats['zero_capture']} ({capture_stats['zero_capture']/len(gcbrs_df)*100:.1f}%)")
    print()
    print("RETENTION RATES:")
    print(f"  High (≥75%):   {capture_stats['high_retention']} GCBRs")
    print(f"  Medium (25-74%): {capture_stats['medium_retention']} GCBRs")
    print(f"  Low (<25%):    {capture_stats['low_retention']} GCBRs")
    print(f"  Average:       {summary['avg_retention_rate']:.1f}%")
    print(f"  Median:        {summary['median_retention_rate']:.1f}%")
    print()
    print("STAGE TOTALS (sum of all GCBR papers):")
    for stage, total in sorted(stage_totals.items()):
        print(f"  {stage}: {total:,} papers")
    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
