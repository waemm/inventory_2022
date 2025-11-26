#!/usr/bin/env python3
"""
Baseline Comparison - Add baseline tracking columns and generate reports

Compares final deduplicated sets against 2022 baseline inventory using:
1. PMID matching (same paper)
2. Entity name matching (same resource)

Supports multi-profile comparison:
- Detects profile subdirectories (conservative, balanced, aggressive)
- Generates comparison table across all profiles
- Produces profile_comparison_report.md

Adds 3 columns to each set:
- in_baseline_pmid: Boolean (PMID match)
- in_baseline_entity: Boolean (entity match)
- in_baseline: Boolean (either match)

Generated outputs:
- Updated CSV files with baseline columns
- baseline_comparison_report.txt
- baseline_comparison_stats.json
- baseline_comparison_data.csv (for visualization)
- profile_comparison_report.md (multi-profile summary)

Created: 2025-11-21
Updated: 2025-11-25 (Added multi-profile support)
"""

import argparse
import pandas as pd
import json
import yaml
from pathlib import Path
from datetime import datetime

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Compare datasets against 2022 baseline')
parser.add_argument('--session-dir', type=str, required=True,
                    help='Session directory containing deduplicated/ subdirectory')
parser.add_argument('--profiles', type=str, default='auto',
                    help='Profiles to compare: conservative, balanced, aggressive, all, or auto (detect)')
parser.add_argument('--config', type=str, required=False,
                    help='Path to config file with profile definitions')
args = parser.parse_args()

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
SESSION_DIR = Path(args.session_dir)
DEDUP_DIR = SESSION_DIR / 'deduplicated'
BASELINE_DIR = SESSION_DIR / 'baseline_comparison'
BASELINE_DIR.mkdir(parents=True, exist_ok=True)
BASELINE_FILE = BASE_DIR / 'data/final_inventory_2022.csv'

# Load config for profile descriptions
CONFIG_PATH = Path(args.config) if args.config else BASE_DIR / 'unified_bioresource_pipeline/config/pipeline_config.yaml'
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    FILTERING_PROFILES = config.get('filtering_profiles', {})
else:
    FILTERING_PROFILES = {}

# Detect profiles to process
KNOWN_PROFILES = ['conservative', 'balanced', 'aggressive']
if args.profiles == 'auto':
    # Auto-detect profile directories
    detected_profiles = []
    for profile in KNOWN_PROFILES:
        profile_dir = DEDUP_DIR / profile
        if profile_dir.exists() and (profile_dir / 'set_c_final.csv').exists():
            detected_profiles.append(profile)
    PROFILES_TO_COMPARE = detected_profiles if detected_profiles else []

    # Also check for legacy single-profile structure
    if not PROFILES_TO_COMPARE:
        # Look for files in deduplicated/ or final/ directly
        for suffix in ['_dedup.csv', '_final.csv', '.csv']:
            if (DEDUP_DIR / f'set_c_union{suffix}').exists():
                PROFILES_TO_COMPARE = ['default']
                break

elif args.profiles == 'all':
    PROFILES_TO_COMPARE = KNOWN_PROFILES
else:
    PROFILES_TO_COMPARE = [p.strip() for p in args.profiles.split(',')]

print(f"Profiles to compare: {PROFILES_TO_COMPARE}")


def normalize_text(text):
    """Normalize text for entity matching"""
    if pd.isna(text):
        return None
    return str(text).strip().lower()


def process_single_profile(profile_name, input_dir, output_dir, baseline_pmids, baseline_entities):
    """
    Process a single profile's datasets and generate baseline comparison.

    Returns dict with comparison statistics.
    """
    print(f"\n{'='*80}")
    print(f"PROCESSING PROFILE: {profile_name.upper()}")
    print(f"{'='*80}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine input files based on profile structure
    if profile_name == 'default':
        # Legacy single-profile structure
        for suffix in ['_dedup.csv', '_final.csv', '.csv']:
            if (input_dir / f'set_c_union{suffix}').exists():
                input_set_c = input_dir / f'set_c_union{suffix}'
                input_set_a = input_dir / f'set_a_linguistic{suffix}'
                input_set_b = input_dir / f'set_b_setfit{suffix}'
                break
    else:
        # Multi-profile structure: deduplicated/{profile}/set_c_final.csv
        input_set_a = input_dir / 'set_a_linguistic.csv'
        input_set_b = input_dir / 'set_b_setfit.csv'
        input_set_c = input_dir / 'set_c_final.csv'

    sets = [
        ('A', input_set_a, output_dir / 'set_a_with_baseline.csv', 'Linguistic'),
        ('B', input_set_b, output_dir / 'set_b_with_baseline.csv', 'SetFit'),
        ('C', input_set_c, output_dir / 'set_c_with_baseline.csv', 'Union (Final)')
    ]

    results = {}
    covered_pmids = set()

    for set_name, input_file, output_file, description in sets:
        print(f"\n  Processing Set {set_name} ({description})...")

        if not input_file.exists():
            print(f"   ⚠️  WARNING: Input file not found: {input_file}")
            print(f"   Skipping Set {set_name}")
            continue

        df = pd.read_csv(input_file)
        print(f"   Loaded: {len(df)} resources")

        # Check PMID matches
        def check_pmid_match(pmid_str):
            if pd.isna(pmid_str):
                return False
            pmids = [p.strip() for p in str(pmid_str).split(',')]
            return any(pmid in baseline_pmids for pmid in pmids)

        df['in_baseline_pmid'] = df['pmid'].apply(check_pmid_match)

        # Check entity matches (use existing baseline_entity_match column if exists)
        if 'baseline_entity_match' in df.columns:
            df['in_baseline_entity'] = df['baseline_entity_match'].notna()
        else:
            df['in_baseline_entity'] = False

        # Combined flag
        df['in_baseline'] = df['in_baseline_pmid'] | df['in_baseline_entity']

        # Save updated file
        df.to_csv(output_file, index=False)
        print(f"   Saved: {output_file}")

        # Collect statistics
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
            'total_resources': int(total),
            'in_baseline': int(in_baseline),
            'in_baseline_pct': float(in_baseline / total * 100) if total > 0 else 0.0,
            'novel_discoveries': int(novel),
            'novel_pct': float(novel / total * 100) if total > 0 else 0.0,
            'pmid_only': int(pmid_only),
            'entity_only': int(entity_only),
            'both_match': int(both),
            'in_baseline_pmid': int(in_baseline_pmid),
            'in_baseline_entity': int(in_baseline_entity)
        }

        # Track baseline coverage for Set C
        if set_name == 'C':
            for _, row in df.iterrows():
                if pd.notna(row['pmid']):
                    pmids = [p.strip() for p in str(row['pmid']).split(',')]
                    covered_pmids.update(p for p in pmids if p in baseline_pmids)

        print(f"   Total resources: {total}")
        print(f"   In baseline: {in_baseline} ({in_baseline/total*100:.1f}%)")
        print(f"   Novel discoveries: {novel} ({novel/total*100:.1f}%)")

    return {
        'results': results,
        'covered_pmids': covered_pmids,
        'output_dir': output_dir
    }


def main():
    print("="*80)
    print("BASELINE COMPARISON - MULTI-PROFILE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Session: {SESSION_DIR.name}")
    print(f"Profiles: {', '.join(PROFILES_TO_COMPARE)}\n")

    if not PROFILES_TO_COMPARE:
        print("❌ ERROR: No profiles found to compare")
        print(f"   Checked: {DEDUP_DIR}")
        return 1

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
    # STEP 2: PROCESS EACH PROFILE
    # ========================================================================

    all_profile_results = {}
    total_baseline = len(baseline_pmids)

    for profile_name in PROFILES_TO_COMPARE:
        if profile_name == 'default':
            input_dir = DEDUP_DIR
        else:
            input_dir = DEDUP_DIR / profile_name

        output_dir = BASELINE_DIR / profile_name

        profile_data = process_single_profile(
            profile_name, input_dir, output_dir,
            baseline_pmids, baseline_entities
        )

        all_profile_results[profile_name] = profile_data

    # ========================================================================
    # STEP 3: GENERATE PROFILE COMPARISON REPORT
    # ========================================================================

    print(f"\n{'='*80}")
    print("GENERATING PROFILE COMPARISON REPORT")
    print(f"{'='*80}")

    # Build comparison table
    comparison_lines = []
    comparison_lines.append("# Profile Comparison Report")
    comparison_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    comparison_lines.append(f"**Session**: {SESSION_DIR.name}")
    comparison_lines.append(f"**Baseline**: {total_baseline} PMIDs")
    comparison_lines.append("")
    comparison_lines.append("## Summary Table")
    comparison_lines.append("")
    comparison_lines.append("| Profile | Baseline Recovery | Novel | Total | Recovery % |")
    comparison_lines.append("|---------|------------------|-------|-------|------------|")

    for profile_name in PROFILES_TO_COMPARE:
        profile_data = all_profile_results.get(profile_name)
        if not profile_data:
            continue

        covered = len(profile_data['covered_pmids'])
        results = profile_data['results']
        total_resources = results.get('C', {}).get('total_resources', 0)
        novel = results.get('C', {}).get('novel_discoveries', 0)
        recovery_pct = (covered / total_baseline * 100) if total_baseline > 0 else 0.0

        comparison_lines.append(
            f"| {profile_name} | {covered} | {novel} | {total_resources} | {recovery_pct:.1f}% |"
        )

    comparison_lines.append("")
    comparison_lines.append("## Profile Descriptions")
    comparison_lines.append("")

    for profile_name in PROFILES_TO_COMPARE:
        profile_config = FILTERING_PROFILES.get(profile_name, {})
        description = profile_config.get('description', 'N/A')
        keywords_count = len(profile_config.get('db_keywords', []))
        bypass_threshold = profile_config.get('linguistic_bypass_threshold', 6)
        setfit_threshold = profile_config.get('setfit_threshold', 0.58)
        require_url = profile_config.get('require_url', True)

        comparison_lines.append(f"### {profile_name.title()}")
        comparison_lines.append(f"- **Description**: {description}")
        comparison_lines.append(f"- **Keywords**: {keywords_count} terms")
        comparison_lines.append(f"- **Linguistic bypass**: ling_score >= {bypass_threshold}")
        comparison_lines.append(f"- **SetFit threshold**: >= {setfit_threshold}")
        comparison_lines.append(f"- **Require URL**: {require_url}")
        comparison_lines.append("")

    comparison_lines.append("## Output Directories")
    comparison_lines.append("")
    for profile_name, profile_data in all_profile_results.items():
        comparison_lines.append(f"- **{profile_name}**: `{profile_data['output_dir']}`")

    comparison_lines.append("")
    comparison_lines.append("## Detailed Statistics by Profile")
    comparison_lines.append("")

    for profile_name, profile_data in all_profile_results.items():
        comparison_lines.append(f"### {profile_name.title()}")
        comparison_lines.append("")
        results = profile_data['results']

        for set_name, stats in results.items():
            comparison_lines.append(f"**{stats['name']}**:")
            comparison_lines.append(f"- Total: {stats['total_resources']}")
            comparison_lines.append(f"- In baseline: {stats['in_baseline']} ({stats['in_baseline_pct']:.1f}%)")
            comparison_lines.append(f"- Novel: {stats['novel_discoveries']} ({stats['novel_pct']:.1f}%)")
            comparison_lines.append("")

    comparison_text = '\n'.join(comparison_lines)

    # Save comparison report
    COMPARISON_REPORT = BASELINE_DIR / 'profile_comparison_report.md'
    with open(COMPARISON_REPORT, 'w') as f:
        f.write(comparison_text)

    print(comparison_text)
    print(f"\n✓ Saved: {COMPARISON_REPORT}")

    # ========================================================================
    # STEP 4: SAVE COMBINED STATISTICS JSON
    # ========================================================================

    print("\n4. Saving combined statistics...")

    combined_stats = {
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'session': SESSION_DIR.name,
        'baseline_total': int(total_baseline),
        'profiles': {}
    }

    for profile_name, profile_data in all_profile_results.items():
        covered = len(profile_data['covered_pmids'])
        combined_stats['profiles'][profile_name] = {
            'baseline_coverage': int(covered),
            'baseline_coverage_pct': float(covered / total_baseline * 100) if total_baseline > 0 else 0.0,
            'sets': profile_data['results']
        }

    COMBINED_STATS = BASELINE_DIR / 'combined_stats.json'
    with open(COMBINED_STATS, 'w') as f:
        json.dump(combined_stats, f, indent=2)

    print(f"   Saved: {COMBINED_STATS}")

    # ========================================================================
    # STEP 5: CREATE VISUALIZATION DATA
    # ========================================================================

    print("\n5. Creating visualization data...")

    viz_data = []
    for profile_name, profile_data in all_profile_results.items():
        covered = len(profile_data['covered_pmids'])
        results = profile_data['results']

        for set_name, stats in results.items():
            viz_data.append({
                'profile': profile_name,
                'set': set_name,
                'set_name': stats['name'],
                'total': stats['total_resources'],
                'in_baseline': stats['in_baseline'],
                'novel': stats['novel_discoveries'],
                'baseline_coverage': covered if set_name == 'C' else None,
                'baseline_coverage_pct': (covered / total_baseline * 100) if set_name == 'C' else None
            })

    df_viz = pd.DataFrame(viz_data)
    VIZ_DATA = BASELINE_DIR / 'visualization_data.csv'
    df_viz.to_csv(VIZ_DATA, index=False)
    print(f"   Saved: {VIZ_DATA}")

    # ========================================================================
    # COMPLETE
    # ========================================================================

    print("\n" + "="*80)
    print("BASELINE COMPARISON COMPLETE!")
    print("="*80)
    print(f"\nOutputs:")
    print(f"  Profile comparison: {COMPARISON_REPORT}")
    print(f"  Combined statistics: {COMBINED_STATS}")
    print(f"  Visualization data: {VIZ_DATA}")
    print(f"\nProfile directories:")
    for profile_name, profile_data in all_profile_results.items():
        print(f"  {profile_name}: {profile_data['output_dir']}")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0


if __name__ == "__main__":
    exit(main())
