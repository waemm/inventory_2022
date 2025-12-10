#!/usr/bin/env python3
"""
Script 03: Identify Baseline Matches

Compares deduplicated inventory against the GBC baseline database to identify
resources already in the baseline. Generates review file for user verification.

Input:
- data/deduplicated/merged_inventory.csv
- GBC baseline: /Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv

Output:
- review/baseline_matches.csv (for user review)
- docs/03_BASELINE_SUMMARY.md

Usage:
    python scripts/03_identify_baseline.py
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data"
REVIEW_DIR = BASE_DIR / "review"
DOCS_DIR = BASE_DIR / "docs"

# Input files
INVENTORY_INPUT = DATA_DIR / "deduplicated/merged_inventory.csv"
GBC_BASELINE = Path("/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv")

# Output files
BASELINE_MATCHES = REVIEW_DIR / "baseline_matches.csv"
SUMMARY_FILE = DOCS_DIR / "03_BASELINE_SUMMARY.md"

# Matching thresholds
NAME_SIMILARITY_THRESHOLD = 0.85


def normalize_name(name):
    """Normalize resource name for matching."""
    if pd.isna(name) or name == '':
        return ''

    name = str(name).lower().strip()
    name = re.sub(r'[_\-\.]', ' ', name)
    name = ' '.join(name.split())

    return name


def compute_name_similarity(name1, name2):
    """Compute similarity between two names."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    if not n1 or not n2:
        return 0.0

    if n1 == n2:
        return 1.0

    return SequenceMatcher(None, n1, n2).ratio()


def find_baseline_matches(inventory_df: pd.DataFrame, baseline_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Find matches between inventory and GBC baseline.

    Matching criteria:
    1. Exact PMID match (highest confidence)
    2. Resource name similarity (requires manual review)

    Returns:
        tuple: (matches_df, stats_dict)
    """
    print("\n  Preparing baseline for matching...")

    # Extract unique resources from baseline
    baseline_resources = baseline_df[['resource_id', 'resource_short_name', 'resource_full_name',
                                       'is_global_core_biodata_resource']].drop_duplicates()

    # Create PMID lookup from baseline
    baseline_pmids = set(baseline_df['pubmed_id'].dropna().astype(str).unique())
    print(f"    Baseline PMIDs: {len(baseline_pmids):,}")
    print(f"    Baseline resources: {len(baseline_resources):,}")

    # Create resource name lookup (normalized)
    baseline_names = {}
    for _, row in baseline_resources.iterrows():
        short_name = normalize_name(row.get('resource_short_name', ''))
        full_name = normalize_name(row.get('resource_full_name', ''))

        if short_name:
            baseline_names[short_name] = {
                'resource_id': row['resource_id'],
                'short_name': row.get('resource_short_name', ''),
                'full_name': row.get('resource_full_name', ''),
                'is_gcbr': row.get('is_global_core_biodata_resource', 0)
            }
        if full_name and full_name != short_name:
            baseline_names[full_name] = {
                'resource_id': row['resource_id'],
                'short_name': row.get('resource_short_name', ''),
                'full_name': row.get('resource_full_name', ''),
                'is_gcbr': row.get('is_global_core_biodata_resource', 0)
            }

    print(f"    Baseline name variants: {len(baseline_names):,}")

    # Match inventory against baseline
    print("\n  Matching inventory against baseline...")

    matches = []
    pmid_matches = 0
    name_matches = 0
    no_match = 0

    for idx, row in inventory_df.iterrows():
        inventory_pmid = str(row.get('ID', ''))
        inventory_name = row.get('best_name', '')
        inventory_url = row.get('extracted_url', '')
        source_batch = row.get('source_batch', '')

        match_type = None
        confidence = 0.0
        baseline_info = None

        # Method 1: PMID match
        if inventory_pmid and inventory_pmid != 'nan' and inventory_pmid in baseline_pmids:
            # Find the baseline resource for this PMID
            baseline_row = baseline_df[baseline_df['pubmed_id'].astype(str) == inventory_pmid].iloc[0]
            match_type = 'PMID'
            confidence = 1.0
            baseline_info = {
                'resource_id': baseline_row.get('resource_id', ''),
                'short_name': baseline_row.get('resource_short_name', ''),
                'full_name': baseline_row.get('resource_full_name', ''),
                'is_gcbr': baseline_row.get('is_global_core_biodata_resource', 0)
            }
            pmid_matches += 1

        # Method 2: Name match (only if no PMID match)
        if not match_type:
            normalized_inv_name = normalize_name(inventory_name)
            if normalized_inv_name:
                # Check exact name match first
                if normalized_inv_name in baseline_names:
                    match_type = 'NAME_EXACT'
                    confidence = 0.95
                    baseline_info = baseline_names[normalized_inv_name]
                    name_matches += 1
                else:
                    # Check fuzzy name match
                    best_sim = 0.0
                    best_match = None
                    for baseline_name, info in baseline_names.items():
                        sim = compute_name_similarity(inventory_name, baseline_name)
                        if sim > best_sim and sim >= NAME_SIMILARITY_THRESHOLD:
                            best_sim = sim
                            best_match = info

                    if best_match:
                        match_type = 'NAME_FUZZY'
                        confidence = best_sim
                        baseline_info = best_match
                        name_matches += 1

        if not match_type:
            no_match += 1

        # Build match record
        match_record = {
            'inventory_row_id': idx,
            'best_name': inventory_name,
            'extracted_url': inventory_url,
            'source_batch': source_batch,
            'inventory_pmid': inventory_pmid,
            'match_type': match_type if match_type else 'NO_MATCH',
            'confidence': round(confidence, 3),
            'baseline_resource_id': baseline_info['resource_id'] if baseline_info else '',
            'baseline_short_name': baseline_info['short_name'] if baseline_info else '',
            'baseline_full_name': baseline_info['full_name'] if baseline_info else '',
            'is_gcbr': baseline_info['is_gcbr'] if baseline_info else '',
            'recommendation': '',
            'user_decision': ''
        }

        # Set recommendation
        if match_type == 'PMID':
            match_record['recommendation'] = 'IN_BASELINE'
        elif match_type == 'NAME_EXACT':
            match_record['recommendation'] = 'LIKELY_IN_BASELINE'
        elif match_type == 'NAME_FUZZY':
            match_record['recommendation'] = 'REVIEW'
        else:
            match_record['recommendation'] = 'NEW_RESOURCE'

        matches.append(match_record)

    matches_df = pd.DataFrame(matches)

    stats = {
        'inventory_total': len(inventory_df),
        'pmid_matches': pmid_matches,
        'name_matches': name_matches,
        'no_match': no_match,
        'in_baseline_pct': ((pmid_matches + name_matches) / len(inventory_df) * 100) if len(inventory_df) > 0 else 0,
        'new_resources': no_match,
        'baseline_resources': len(baseline_resources),
        'baseline_pmids': len(baseline_pmids)
    }

    return matches_df, stats


def generate_summary(stats: dict) -> str:
    """Generate markdown summary of baseline comparison."""

    summary = f"""# Step 3: Baseline Comparison Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

Compared deduplicated inventory against the GBC baseline database to identify
resources already in the baseline vs new discoveries.

---

## Baseline Database

| Metric | Value |
|--------|-------|
| Unique resources | {stats['baseline_resources']:,} |
| Papers (PMIDs) | {stats['baseline_pmids']:,} |

---

## Match Results

| Match Type | Count | Description |
|------------|-------|-------------|
| PMID Match | {stats['pmid_matches']:,} | Exact paper match in baseline |
| Name Match | {stats['name_matches']:,} | Resource name match |
| No Match | {stats['no_match']:,} | Potentially new resources |
| **Total** | **{stats['inventory_total']:,}** | |

---

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| In Baseline | {stats['pmid_matches'] + stats['name_matches']:,} | {stats['in_baseline_pct']:.1f}% |
| New Resources | {stats['new_resources']:,} | {100 - stats['in_baseline_pct']:.1f}% |

---

## Output Files

- `review/baseline_matches.csv` ({stats['inventory_total']:,} records)

---

## Next Steps

1. **Review the baseline matches:**
   ```
   review/baseline_matches.csv
   ```

2. **Edit the `user_decision` column:**
   - `IN_BASELINE` - Confirm this is in the baseline
   - `NEW_RESOURCE` - Confirm this is a new resource
   - Leave blank to accept recommendation

3. **When ready, apply baseline flags:**
   ```bash
   python scripts/03b_apply_baseline.py
   ```
"""

    return summary


def main():
    print("=" * 60)
    print("Step 3: Identify Baseline Matches")
    print("=" * 60)

    # Check inputs exist
    if not INVENTORY_INPUT.exists():
        print(f"\nERROR: Inventory input not found: {INVENTORY_INPUT}")
        print("Run Steps 2 and 2b first")
        return

    if not GBC_BASELINE.exists():
        print(f"\nERROR: GBC baseline not found: {GBC_BASELINE}")
        return

    # Load data
    print(f"\nLoading inventory: {INVENTORY_INPUT}")
    inventory_df = pd.read_csv(INVENTORY_INPUT)
    print(f"  Loaded {len(inventory_df):,} records")

    print(f"\nLoading GBC baseline: {GBC_BASELINE}")
    baseline_df = pd.read_csv(GBC_BASELINE)
    print(f"  Loaded {len(baseline_df):,} records")

    # Find matches
    print("\nFinding baseline matches...")
    matches_df, stats = find_baseline_matches(inventory_df, baseline_df)

    # Save matches for review
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    matches_df.to_csv(BASELINE_MATCHES, index=False)
    print(f"\n  Saved: {BASELINE_MATCHES}")

    # Generate summary
    summary = generate_summary(stats)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(summary)
    print(f"  Saved summary: {SUMMARY_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("BASELINE COMPARISON COMPLETE")
    print("=" * 60)
    print(f"\nInventory records: {stats['inventory_total']:,}")
    print(f"  PMID matches: {stats['pmid_matches']:,}")
    print(f"  Name matches: {stats['name_matches']:,}")
    print(f"  No match (new): {stats['no_match']:,}")
    print(f"\nIn baseline: {stats['pmid_matches'] + stats['name_matches']:,} ({stats['in_baseline_pct']:.1f}%)")
    print(f"New resources: {stats['new_resources']:,} ({100 - stats['in_baseline_pct']:.1f}%)")
    print(f"\nReview the baseline matches at: {BASELINE_MATCHES}")
    print("\nWhen ready, proceed to Step 3b:")
    print("  python scripts/03b_apply_baseline.py")


if __name__ == "__main__":
    main()
