#!/usr/bin/env python3
"""
Baseline Comparison - Add baseline tracking columns and generate reports

Compares final deduplicated sets against 2022 baseline inventory using:
1. PMID matching (same paper)
2. Entity name matching (same resource)

Adds 3 columns to each set:
- in_baseline_pmid: Boolean (PMID match)
- in_baseline_entity: Boolean (entity match)
- in_baseline: Boolean (either match)

Generated outputs:
- Updated CSV files with baseline columns
- baseline_comparison_report.txt
- baseline_comparison_stats.json
- baseline_comparison_data.csv (for visualization)

Created: 2025-11-21
"""

import argparse
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Compare datasets against 2022 baseline')
parser.add_argument('--session-dir', type=str, required=True,
                    help='Session directory containing final/ subdirectory')
args = parser.parse_args()

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
SESSION_DIR = Path(args.session_dir)
FINAL_DIR = SESSION_DIR / 'final'
BASELINE_DIR = SESSION_DIR / 'baseline_comparison'
BASELINE_DIR.mkdir(parents=True, exist_ok=True)

# Input files
INPUT_SET_A = FINAL_DIR / 'set_a_linguistic_final.csv'
INPUT_SET_B = FINAL_DIR / 'set_b_setfit_final.csv'
INPUT_SET_C = FINAL_DIR / 'set_c_union_final.csv'
BASELINE_FILE = BASE_DIR / 'data/final_inventory_2022.csv'

# Output files
OUTPUT_SET_A = FINAL_DIR / 'set_a_linguistic_final.csv'  # Overwrite
OUTPUT_SET_B = FINAL_DIR / 'set_b_setfit_final.csv'
OUTPUT_SET_C = FINAL_DIR / 'set_c_union_final.csv'
REPORT_FILE = BASELINE_DIR / 'baseline_comparison_report.txt'
STATS_FILE = BASELINE_DIR / 'baseline_comparison_stats.json'
DATA_FILE = BASELINE_DIR / 'baseline_comparison_data.csv'


def normalize_text(text):
    """Normalize text for entity matching"""
    if pd.isna(text):
        return None
    return str(text).strip().lower()


def main():
    print("="*80)
    print("BASELINE COMPARISON")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Session: {SESSION_DIR.name}\n")

    # ========================================================================
    # STEP 1: LOAD BASELINE INVENTORY
    # ========================================================================

    print("1. Loading baseline inventory...")

    if not BASELINE_FILE.exists():
        print(f"   ❌ ERROR: Baseline file not found: {BASELINE_FILE}")
        print(f"   Please ensure data/final_inventory_2022.csv exists")
        return 1

    df_baseline = pd.read_csv(BASELINE_FILE)

    # Get baseline PMIDs (ID column)
    baseline_pmids = set(df_baseline['ID'].astype(str).unique())

    # Get baseline entities (best_name column)
    baseline_entities = {}
    for name in df_baseline['best_name'].dropna().unique():
        norm_name = normalize_text(name)
        if norm_name:
            baseline_entities[norm_name] = name

    print(f"   Baseline PMIDs: {len(baseline_pmids)}")
    print(f"   Baseline entities: {len(baseline_entities)}")

    # ========================================================================
    # STEP 2: PROCESS EACH SET
    # ========================================================================

    sets = [
        ('A', INPUT_SET_A, OUTPUT_SET_A, 'Linguistic'),
        ('B', INPUT_SET_B, OUTPUT_SET_B, 'SetFit'),
        ('C', INPUT_SET_C, OUTPUT_SET_C, 'Union')
    ]

    results = {}

    for set_name, input_file, output_file, description in sets:
        print(f"\n2. Processing Set {set_name} ({description})...")

        if not input_file.exists():
            print(f"   ⚠️  WARNING: Input file not found: {input_file}")
            print(f"   Skipping Set {set_name}")
            continue

        df = pd.read_csv(input_file)
        print(f"   Loaded: {len(df)} resources")

        # ====================================================================
        # 2a. Check PMID matches
        # ====================================================================

        def check_pmid_match(pmid_str):
            if pd.isna(pmid_str):
                return False
            # Handle comma-separated PMIDs from deduplication
            pmids = [p.strip() for p in str(pmid_str).split(',')]
            return any(pmid in baseline_pmids for pmid in pmids)

        df['in_baseline_pmid'] = df['pmid'].apply(check_pmid_match)

        # ====================================================================
        # 2b. Check entity matches (use existing baseline_entity_match column)
        # ====================================================================

        df['in_baseline_entity'] = df['baseline_entity_match'].notna()

        # ====================================================================
        # 2c. Combined flag
        # ====================================================================

        df['in_baseline'] = df['in_baseline_pmid'] | df['in_baseline_entity']

        # ====================================================================
        # 2d. Save updated file
        # ====================================================================

        df.to_csv(output_file, index=False)
        print(f"   Saved: {output_file}")

        # ====================================================================
        # 2e. Collect statistics
        # ====================================================================

        total = len(df)
        in_baseline = df['in_baseline'].sum()
        in_baseline_pmid = df['in_baseline_pmid'].sum()
        in_baseline_entity = df['in_baseline_entity'].sum()
        both = (df['in_baseline_pmid'] & df['in_baseline_entity']).sum()
        pmid_only = in_baseline_pmid - both
        entity_only = in_baseline_entity - both
        novel = total - in_baseline

        results[set_name] = {
            'name': f"Set {set_name} ({description})",
            'total_resources': total,
            'in_baseline': in_baseline,
            'in_baseline_pct': (in_baseline / total * 100) if total > 0 else 0,
            'novel_discoveries': novel,
            'novel_pct': (novel / total * 100) if total > 0 else 0,
            'pmid_only': pmid_only,
            'entity_only': entity_only,
            'both_match': both,
            'in_baseline_pmid': in_baseline_pmid,
            'in_baseline_entity': in_baseline_entity
        }

        print(f"   Total resources: {total}")
        print(f"   In baseline: {in_baseline} ({in_baseline/total*100:.1f}%)")
        print(f"   Novel discoveries: {novel} ({novel/total*100:.1f}%)")
        print(f"   Match breakdown:")
        print(f"     - PMID only: {pmid_only}")
        print(f"     - Entity only: {entity_only}")
        print(f"     - Both: {both}")

    # ========================================================================
    # STEP 3: CALCULATE BASELINE COVERAGE
    # ========================================================================

    print("\n3. Calculating baseline coverage...")

    # Load all sets to check baseline coverage
    def count_baseline_coverage(filepath):
        if not filepath.exists():
            return 0

        df = pd.read_csv(filepath)
        covered_pmids = set()

        for _, row in df.iterrows():
            # Check PMIDs
            if pd.notna(row['pmid']):
                pmids = [p.strip() for p in str(row['pmid']).split(',')]
                covered_pmids.update(p for p in pmids if p in baseline_pmids)

        return len(covered_pmids)

    coverage_a = count_baseline_coverage(OUTPUT_SET_A)
    coverage_b = count_baseline_coverage(OUTPUT_SET_B)
    coverage_c = count_baseline_coverage(OUTPUT_SET_C)
    total_baseline = len(baseline_pmids)

    print(f"   Set A coverage: {coverage_a}/{total_baseline} ({coverage_a/total_baseline*100:.1f}%)")
    print(f"   Set B coverage: {coverage_b}/{total_baseline} ({coverage_b/total_baseline*100:.1f}%)")
    print(f"   Set C coverage: {coverage_c}/{total_baseline} ({coverage_c/total_baseline*100:.1f}%)")

    # ========================================================================
    # STEP 4: GENERATE REPORT
    # ========================================================================

    print("\n4. Generating report...")
    report = []
    report.append("="*80)
    report.append("BASELINE COMPARISON REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Session: {SESSION_DIR.name}")
    report.append("="*80)
    report.append("")

    report.append("BASELINE INVENTORY:")
    report.append(f"  Total resources: {total_baseline}")
    report.append("")

    report.append("RESOURCE COUNTS BY SET:")
    for set_name, stats in results.items():
        report.append(f"  {stats['name']}:")
        report.append(f"    Total resources: {stats['total_resources']}")
        report.append(f"    In baseline: {stats['in_baseline']} ({stats['in_baseline_pct']:.1f}%)")
        report.append(f"    Novel discoveries: {stats['novel_discoveries']} ({stats['novel_pct']:.1f}%)")
        report.append("")

    report.append("BASELINE COVERAGE (% of baseline resources found):")
    report.append(f"  Set A: {coverage_a}/{total_baseline} ({coverage_a/total_baseline*100:.1f}%)")
    report.append(f"  Set B: {coverage_b}/{total_baseline} ({coverage_b/total_baseline*100:.1f}%)")
    report.append(f"  Set C: {coverage_c}/{total_baseline} ({coverage_c/total_baseline*100:.1f}%)")
    report.append("")

    report.append("MATCH TYPE BREAKDOWN:")
    for set_name, stats in results.items():
        report.append(f"  {stats['name']}:")
        report.append(f"    PMID only: {stats['pmid_only']}")
        report.append(f"    Entity only: {stats['entity_only']}")
        report.append(f"    Both: {stats['both_match']}")
        report.append("")

    report_text = '\n'.join(report)
    with open(REPORT_FILE, 'w') as f:
        f.write(report_text)
    print(report_text)

    # ========================================================================
    # STEP 5: SAVE STATISTICS JSON
    # ========================================================================

    print("\n5. Saving statistics...")
    stats = {
        'baseline': {
            'total_resources': total_baseline,
            'coverage_set_a': coverage_a,
            'coverage_set_b': coverage_b,
            'coverage_set_c': coverage_c,
            'coverage_pct_a': coverage_a / total_baseline * 100 if total_baseline > 0 else 0,
            'coverage_pct_b': coverage_b / total_baseline * 100 if total_baseline > 0 else 0,
            'coverage_pct_c': coverage_c / total_baseline * 100 if total_baseline > 0 else 0
        },
        'sets': results
    }

    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"   Saved: {STATS_FILE}")

    # ========================================================================
    # STEP 6: CREATE DATA FILE FOR VISUALIZATION
    # ========================================================================

    print("\n6. Creating visualization data...")
    viz_data = []
    for set_name, set_stats in results.items():
        viz_data.append({
            'set': set_name,
            'set_name': set_stats['name'],
            'total': set_stats['total_resources'],
            'in_baseline': set_stats['in_baseline'],
            'novel': set_stats['novel_discoveries'],
            'pmid_only': set_stats['pmid_only'],
            'entity_only': set_stats['entity_only'],
            'both_match': set_stats['both_match']
        })

    df_viz = pd.DataFrame(viz_data)
    df_viz.to_csv(DATA_FILE, index=False)
    print(f"   Saved: {DATA_FILE}")

    print("\n" + "="*80)
    print("BASELINE COMPARISON COMPLETE!")
    print("="*80)
    print(f"\nOutputs:")
    print(f"  Report: {REPORT_FILE}")
    print(f"  Statistics: {STATS_FILE}")
    print(f"  Visualization data: {DATA_FILE}")
    print(f"\nUpdated files with baseline columns:")
    for set_name, input_file, output_file, description in sets:
        if output_file.exists():
            print(f"  {output_file}")

    return 0


if __name__ == "__main__":
    exit(main())
