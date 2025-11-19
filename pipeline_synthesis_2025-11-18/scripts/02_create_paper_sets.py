#!/usr/bin/env python3
"""
Create Three Paper Sets for Filtering Strategy Comparison

Set A: Linguistic Only (ling_score >= 3)
Set B: SetFit Only (confidence >= 0.60, high + medium)
Set C: Union of A + B (deduplicated)
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path("/Users/warren/development/GBC/inventory_2022")
LINGUISTIC_FILE = BASE_DIR / "advanced_paper_filtering/data/results/final_classified_introductions.csv"
SETFIT_INTRO_FILE = BASE_DIR / "pipeline_synthesis_2025-11-18/results/setfit_inference/setfit_classified_introductions.csv"
OUTPUT_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/data/paper_sets"

def main():
    print("=" * 80)
    print("CREATING THREE PAPER SETS FOR FILTERING STRATEGY COMPARISON")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # SET A: LINGUISTIC ONLY
    # ========================================================================
    print("Loading Set A: Linguistic Only (ling_score >= 3)...")
    df_linguistic = pd.read_csv(LINGUISTIC_FILE)
    print(f"  Loaded: {len(df_linguistic):,} papers")

    # Keep only pmid and source info
    set_a = df_linguistic[['pmid']].copy()
    set_a['source'] = 'linguistic'
    set_a['ling_score'] = df_linguistic['ling_score']

    print(f"  Set A papers: {len(set_a):,}")

    # ========================================================================
    # SET B: SETFIT ONLY (confidence >= 0.60)
    # ========================================================================
    print("\nLoading Set B: SetFit (confidence >= 0.60)...")
    df_setfit_all = pd.read_csv(SETFIT_INTRO_FILE)
    print(f"  Loaded: {len(df_setfit_all):,} SetFit introductions")

    # Filter for confidence >= 0.60 (high + medium)
    df_setfit_filtered = df_setfit_all[df_setfit_all['setfit_confidence'] >= 0.60].copy()
    print(f"  After confidence filter (>= 0.60): {len(df_setfit_filtered):,} papers")

    # Breakdown by tier
    high_conf = len(df_setfit_filtered[df_setfit_filtered['setfit_confidence'] >= 0.70])
    medium_conf = len(df_setfit_filtered[(df_setfit_filtered['setfit_confidence'] >= 0.60) &
                                         (df_setfit_filtered['setfit_confidence'] < 0.70)])
    print(f"    High (>= 0.70): {high_conf:,}")
    print(f"    Medium (0.60-0.69): {medium_conf:,}")

    # Keep only pmid and source info
    set_b = df_setfit_filtered[['pmid']].copy()
    set_b['source'] = 'setfit'
    set_b['setfit_confidence'] = df_setfit_filtered['setfit_confidence']

    print(f"  Set B papers: {len(set_b):,}")

    # ========================================================================
    # SET C: UNION OF A + B
    # ========================================================================
    print("\nCreating Set C: Union of A + B...")

    # Mark papers in each set
    set_a_pmids = set(set_a['pmid'])
    set_b_pmids = set(set_b['pmid'])

    # Calculate overlaps
    both_sets = set_a_pmids & set_b_pmids
    only_a = set_a_pmids - set_b_pmids
    only_b = set_b_pmids - set_a_pmids
    union_pmids = set_a_pmids | set_b_pmids

    print(f"  Papers in A only: {len(only_a):,}")
    print(f"  Papers in B only: {len(only_b):,}")
    print(f"  Papers in both A and B: {len(both_sets):,}")
    print(f"  Union total: {len(union_pmids):,}")

    # Create Set C with source tracking
    set_c_data = []

    for pmid in union_pmids:
        in_a = pmid in set_a_pmids
        in_b = pmid in set_b_pmids

        row = {'pmid': pmid}

        if in_a and in_b:
            row['source'] = 'both'
            row['ling_score'] = set_a[set_a['pmid'] == pmid]['ling_score'].iloc[0]
            row['setfit_confidence'] = set_b[set_b['pmid'] == pmid]['setfit_confidence'].iloc[0]
        elif in_a:
            row['source'] = 'linguistic_only'
            row['ling_score'] = set_a[set_a['pmid'] == pmid]['ling_score'].iloc[0]
            row['setfit_confidence'] = None
        else:  # in_b
            row['source'] = 'setfit_only'
            row['ling_score'] = None
            row['setfit_confidence'] = set_b[set_b['pmid'] == pmid]['setfit_confidence'].iloc[0]

        set_c_data.append(row)

    set_c = pd.DataFrame(set_c_data)
    print(f"  Set C papers: {len(set_c):,}")

    # ========================================================================
    # SAVE PAPER SETS
    # ========================================================================
    print("\nSaving paper sets...")

    set_a_path = OUTPUT_DIR / "set_a_linguistic.csv"
    set_b_path = OUTPUT_DIR / "set_b_setfit.csv"
    set_c_path = OUTPUT_DIR / "set_c_union.csv"

    set_a.to_csv(set_a_path, index=False)
    print(f"  Saved Set A: {set_a_path}")

    set_b.to_csv(set_b_path, index=False)
    print(f"  Saved Set B: {set_b_path}")

    set_c.to_csv(set_c_path, index=False)
    print(f"  Saved Set C: {set_c_path}")

    # ========================================================================
    # GENERATE SUMMARY STATISTICS
    # ========================================================================
    print("\nGenerating summary statistics...")

    summary = {
        'timestamp': datetime.now().isoformat(),
        'set_a': {
            'name': 'Linguistic Only',
            'criteria': 'ling_score >= 3',
            'paper_count': len(set_a),
            'source_file': str(LINGUISTIC_FILE.name)
        },
        'set_b': {
            'name': 'SetFit High+Medium',
            'criteria': 'confidence >= 0.60',
            'paper_count': len(set_b),
            'high_confidence': high_conf,
            'medium_confidence': medium_conf,
            'source_file': str(SETFIT_INTRO_FILE.name)
        },
        'set_c': {
            'name': 'Union (A + B)',
            'criteria': 'Linguistic OR SetFit',
            'paper_count': len(set_c),
            'linguistic_only': len(only_a),
            'setfit_only': len(only_b),
            'both': len(both_sets)
        },
        'overlap_analysis': {
            'linguistic_only': int(len(only_a)),
            'setfit_only': int(len(only_b)),
            'both_methods': int(len(both_sets)),
            'union_total': int(len(union_pmids)),
            'overlap_rate': round(len(both_sets) / len(union_pmids) * 100, 2)
        }
    }

    summary_path = OUTPUT_DIR / "paper_sets_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved summary: {summary_path}")

    # ========================================================================
    # SUMMARY REPORT
    # ========================================================================
    print("\n" + "=" * 80)
    print("PAPER SETS SUMMARY")
    print("=" * 80)
    print(f"Set A (Linguistic):     {len(set_a):,} papers")
    print(f"Set B (SetFit):         {len(set_b):,} papers")
    print(f"Set C (Union):          {len(set_c):,} papers")
    print()
    print("OVERLAP ANALYSIS:")
    print(f"  Linguistic only:      {len(only_a):,} papers ({len(only_a)/len(union_pmids)*100:.1f}%)")
    print(f"  SetFit only:          {len(only_b):,} papers ({len(only_b)/len(union_pmids)*100:.1f}%)")
    print(f"  Both methods:         {len(both_sets):,} papers ({len(both_sets)/len(union_pmids)*100:.1f}%)")
    print(f"  Agreement rate:       {len(both_sets)/len(union_pmids)*100:.1f}%")
    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
