#!/usr/bin/env python3
"""
Compare Baseline Inventory (2022) to Validation Inventories (2011-2021)

Compare 3,112 baseline resources from 2022 to validation entity inventories
from Phase 2 analysis, and track baseline through filtering stages.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

# Paths
BASE_DIR = Path("/Users/warren/development/GBC/inventory_2022")
BASELINE_FILE = BASE_DIR / "data/final_inventory_2022.csv"

# Validation entity inventories from Phase 2
ENTITY_INVENTORIES_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/data/entity_inventories"

# Output directory
OUTPUT_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/results/baseline_comparison"

def normalize_name(name):
    """Normalize resource name for matching"""
    if pd.isna(name):
        return None
    return str(name).strip().lower()

def fuzzy_match_score(name1, name2):
    """Calculate fuzzy match score between two names (0-100)"""
    if pd.isna(name1) or pd.isna(name2):
        return 0
    s1 = str(name1).lower()
    s2 = str(name2).lower()
    return int(SequenceMatcher(None, s1, s2).ratio() * 100)

def main():
    print("=" * 80)
    print("BASELINE INVENTORY (2022) vs VALIDATION INVENTORIES (2011-2021)")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # LOAD BASELINE INVENTORY (2022)
    # ========================================================================
    print("Loading baseline inventory (2022)...")
    df_baseline = pd.read_csv(BASELINE_FILE)
    print(f"  Total resources: {len(df_baseline):,}")

    # Extract resource names
    baseline_resources = []
    for _, row in df_baseline.iterrows():
        name = row.get('best_name', '')
        if pd.notna(name) and name != '':
            baseline_resources.append({
                'baseline_name': name,
                'normalized_name': normalize_name(name),
                'pmid': row.get('ID', ''),
                'article_count': row.get('article_count', 0)
            })

    df_baseline_ref = pd.DataFrame(baseline_resources)
    print(f"  Valid resource names: {len(df_baseline_ref):,}")

    # ========================================================================
    # LOAD VALIDATION ENTITY INVENTORIES
    # ========================================================================
    print("\nLoading validation entity inventories...")

    # Load Set A (Linguistic)
    df_set_a = pd.read_csv(ENTITY_INVENTORIES_DIR / "set_a_entity_inventory.csv")
    print(f"  Set A (Linguistic): {len(df_set_a):,} entities")

    # Load Set B (SetFit)
    df_set_b = pd.read_csv(ENTITY_INVENTORIES_DIR / "set_b_entity_inventory.csv")
    print(f"  Set B (SetFit): {len(df_set_b):,} entities")

    # Load Set C (Union)
    df_set_c = pd.read_csv(ENTITY_INVENTORIES_DIR / "set_c_entity_inventory.csv")
    print(f"  Set C (Union): {len(df_set_c):,} entities")

    # ========================================================================
    # EXACT MATCHING
    # ========================================================================
    print("\nPerforming exact name matching...")

    # Create normalized lookup dicts
    set_a_entities = {normalize_name(name): name for name in df_set_a['entity_name']}
    set_b_entities = {normalize_name(name): name for name in df_set_b['entity_name']}
    set_c_entities = {normalize_name(name): name for name in df_set_c['entity_name']}

    # Match baseline to each set
    matches = []
    for _, baseline in df_baseline_ref.iterrows():
        norm_name = baseline['normalized_name']

        # Check exact matches
        in_set_a = norm_name in set_a_entities
        in_set_b = norm_name in set_b_entities
        in_set_c = norm_name in set_c_entities

        matches.append({
            'baseline_name': baseline['baseline_name'],
            'normalized_name': norm_name,
            'in_set_a': in_set_a,
            'in_set_b': in_set_b,
            'in_set_c': in_set_c,
            'match_count': sum([in_set_a, in_set_b, in_set_c]),
            'match_type': 'exact' if (in_set_a or in_set_b or in_set_c) else 'none'
        })

    df_matches = pd.DataFrame(matches)

    # Calculate coverage stats
    exact_in_a = len(df_matches[df_matches['in_set_a']])
    exact_in_b = len(df_matches[df_matches['in_set_b']])
    exact_in_c = len(df_matches[df_matches['in_set_c']])
    exact_in_any = len(df_matches[df_matches['match_count'] > 0])

    print(f"  Exact matches in Set A: {exact_in_a:,} ({exact_in_a/len(df_matches)*100:.1f}%)")
    print(f"  Exact matches in Set B: {exact_in_b:,} ({exact_in_b/len(df_matches)*100:.1f}%)")
    print(f"  Exact matches in Set C: {exact_in_c:,} ({exact_in_c/len(df_matches)*100:.1f}%)")
    print(f"  Exact matches in ANY:   {exact_in_any:,} ({exact_in_any/len(df_matches)*100:.1f}%)")

    # ========================================================================
    # FUZZY MATCHING FOR UNMATCHED
    # ========================================================================
    print("\nPerforming fuzzy matching for unmatched resources...")

    unmatched = df_matches[df_matches['match_count'] == 0]
    print(f"  Unmatched resources: {len(unmatched):,}")

    fuzzy_matches = []
    threshold = 90  # 90% similarity for fuzzy match

    for _, resource in unmatched.iterrows():
        name = resource['baseline_name']
        best_match = None
        best_score = 0
        best_set = None

        # Check Set C (union) for fuzzy matches
        for entity in df_set_c['entity_name']:
            score = fuzzy_match_score(name, entity)
            if score > best_score:
                best_score = score
                best_match = entity
                best_set = 'set_c'

        if best_score >= threshold:
            fuzzy_matches.append({
                'baseline_name': name,
                'matched_entity': best_match,
                'fuzzy_score': best_score,
                'match_set': best_set
            })

    print(f"  Fuzzy matches (≥{threshold}%): {len(fuzzy_matches):,}")

    # ========================================================================
    # NOVEL RESOURCE ANALYSIS
    # ========================================================================
    print("\nAnalyzing novel resources...")

    # Baseline-only resources (not in validation)
    baseline_only = df_matches[df_matches['match_count'] == 0]
    print(f"  Baseline-only resources: {len(baseline_only):,}")

    # Validation-only resources (not in baseline)
    baseline_names = set(df_baseline_ref['normalized_name'])
    validation_only = []

    for entity in df_set_c['entity_name']:
        norm = normalize_name(entity)
        if norm not in baseline_names:
            # Get entity info from Set C
            entity_info = df_set_c[df_set_c['entity_name'] == entity].iloc[0]
            validation_only.append({
                'entity_name': entity,
                'total_papers': entity_info['total_papers'],
                'source': entity_info['source']
            })

    df_validation_only = pd.DataFrame(validation_only)
    print(f"  Validation-only entities: {len(df_validation_only):,}")

    # ========================================================================
    # SAVE RESULTS
    # ========================================================================
    print("\nSaving comparison results...")

    # Main comparison file
    comparison_file = OUTPUT_DIR / "baseline_vs_validation.csv"
    df_matches.to_csv(comparison_file, index=False)
    print(f"  Saved: {comparison_file}")

    # Coverage stats
    coverage_stats = {
        'timestamp': datetime.now().isoformat(),
        'baseline_total': len(df_baseline_ref),
        'validation_total': len(df_set_c),
        'exact_matches': {
            'set_a': int(exact_in_a),
            'set_b': int(exact_in_b),
            'set_c': int(exact_in_c),
            'any_set': int(exact_in_any)
        },
        'exact_coverage_percent': {
            'set_a': round(exact_in_a / len(df_matches) * 100, 2),
            'set_b': round(exact_in_b / len(df_matches) * 100, 2),
            'set_c': round(exact_in_c / len(df_matches) * 100, 2),
            'any_set': round(exact_in_any / len(df_matches) * 100, 2)
        },
        'fuzzy_matches': len(fuzzy_matches),
        'baseline_only': int(len(baseline_only)),
        'validation_only': int(len(df_validation_only))
    }

    stats_file = OUTPUT_DIR / "baseline_coverage_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(coverage_stats, f, indent=2)
    print(f"  Saved: {stats_file}")

    # Baseline-only resources
    baseline_only_file = OUTPUT_DIR / "baseline_novel_resources.csv"
    baseline_only.to_csv(baseline_only_file, index=False)
    print(f"  Saved: {baseline_only_file}")

    # Validation-only resources
    validation_only_file = OUTPUT_DIR / "validation_novel_resources.csv"
    df_validation_only.to_csv(validation_only_file, index=False)
    print(f"  Saved: {validation_only_file}")

    # Fuzzy matches
    if len(fuzzy_matches) > 0:
        df_fuzzy = pd.DataFrame(fuzzy_matches)
        fuzzy_file = OUTPUT_DIR / "fuzzy_matches.csv"
        df_fuzzy.to_csv(fuzzy_file, index=False)
        print(f"  Saved: {fuzzy_file}")

    # ========================================================================
    # SUMMARY REPORT
    # ========================================================================
    print("\n" + "=" * 80)
    print("BASELINE vs VALIDATION COMPARISON SUMMARY")
    print("=" * 80)
    print(f"Baseline (2022):    {len(df_baseline_ref):,} resources")
    print(f"Validation (2011-2021): {len(df_set_c):,} entities")
    print()
    print("EXACT MATCH COVERAGE:")
    print(f"  Set A (Linguistic): {exact_in_a:,} / {len(df_matches):,} ({exact_in_a/len(df_matches)*100:.1f}%)")
    print(f"  Set B (SetFit):     {exact_in_b:,} / {len(df_matches):,} ({exact_in_b/len(df_matches)*100:.1f}%)")
    print(f"  Set C (Union):      {exact_in_c:,} / {len(df_matches):,} ({exact_in_c/len(df_matches)*100:.1f}%)")
    print(f"  ANY set:            {exact_in_any:,} / {len(df_matches):,} ({exact_in_any/len(df_matches)*100:.1f}%)")
    print()
    print("FUZZY MATCHING:")
    print(f"  Fuzzy matches (≥90%): {len(fuzzy_matches):,}")
    print()
    print("NOVEL RESOURCES:")
    print(f"  Baseline-only (2022):      {len(baseline_only):,} resources")
    print(f"  Validation-only (2011-2021): {len(df_validation_only):,} entities")
    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
