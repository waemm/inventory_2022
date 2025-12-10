#!/usr/bin/env python3
"""
Script 03b: Apply Baseline Flags

Applies user-reviewed baseline decisions to add baseline status flags
to the merged inventory.

Input:
- data/deduplicated/merged_inventory.csv
- review/baseline_matches.csv (edited by user)

Output:
- data/final/final_inventory.csv
- docs/03b_BASELINE_APPLIED_SUMMARY.md

Usage:
    python scripts/03b_apply_baseline.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data"
REVIEW_DIR = BASE_DIR / "review"
DOCS_DIR = BASE_DIR / "docs"

# Input files
INVENTORY_INPUT = DATA_DIR / "deduplicated/merged_inventory.csv"
BASELINE_DECISIONS = REVIEW_DIR / "baseline_matches.csv"

# Output files
FINAL_OUTPUT = DATA_DIR / "final/final_inventory.csv"
SUMMARY_FILE = DOCS_DIR / "03b_BASELINE_APPLIED_SUMMARY.md"


def apply_baseline_flags(inventory_df: pd.DataFrame, baseline_decisions: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Apply baseline decisions to inventory.

    Adds columns:
    - in_baseline: Boolean flag
    - baseline_resource_id: ID from GBC if matched
    - baseline_short_name: Name from GBC if matched
    - is_gcbr: Global Core Biodata Resource flag

    Returns:
        tuple: (flagged_df, stats_dict)
    """
    # Initialize new columns
    inventory_df = inventory_df.copy()
    inventory_df['in_baseline'] = False
    inventory_df['baseline_resource_id'] = ''
    inventory_df['baseline_short_name'] = ''
    inventory_df['is_gcbr'] = False
    inventory_df['baseline_match_type'] = ''

    in_baseline_count = 0
    new_resource_count = 0
    gcbr_count = 0

    for _, row in baseline_decisions.iterrows():
        inventory_idx = row['inventory_row_id']
        user_decision = str(row.get('user_decision', '')).strip().upper()
        recommendation = row['recommendation']

        # Determine final status
        if user_decision == 'IN_BASELINE':
            is_in_baseline = True
        elif user_decision == 'NEW_RESOURCE':
            is_in_baseline = False
        elif user_decision == '':
            # Use recommendation
            is_in_baseline = recommendation in ['IN_BASELINE', 'LIKELY_IN_BASELINE']
        else:
            is_in_baseline = user_decision == 'IN_BASELINE'

        # Apply to inventory
        if inventory_idx in inventory_df.index:
            inventory_df.loc[inventory_idx, 'in_baseline'] = is_in_baseline
            inventory_df.loc[inventory_idx, 'baseline_match_type'] = row.get('match_type', '')

            if is_in_baseline:
                inventory_df.loc[inventory_idx, 'baseline_resource_id'] = row.get('baseline_resource_id', '')
                inventory_df.loc[inventory_idx, 'baseline_short_name'] = row.get('baseline_short_name', '')
                is_gcbr = row.get('is_gcbr', 0) == 1
                inventory_df.loc[inventory_idx, 'is_gcbr'] = is_gcbr
                in_baseline_count += 1
                if is_gcbr:
                    gcbr_count += 1
            else:
                new_resource_count += 1

    stats = {
        'total_records': len(inventory_df),
        'in_baseline': in_baseline_count,
        'new_resources': new_resource_count,
        'gcbr_count': gcbr_count,
        'in_baseline_pct': (in_baseline_count / len(inventory_df) * 100) if len(inventory_df) > 0 else 0,
        'new_resources_pct': (new_resource_count / len(inventory_df) * 100) if len(inventory_df) > 0 else 0
    }

    return inventory_df, stats


def generate_summary(stats: dict) -> str:
    """Generate markdown summary of baseline flag application."""

    summary = f"""# Step 3b: Baseline Flags Applied Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

Applied user-reviewed baseline decisions to flag resources as in-baseline or new.

---

## Results

| Status | Count | Percentage |
|--------|-------|------------|
| In Baseline | {stats['in_baseline']:,} | {stats['in_baseline_pct']:.1f}% |
| New Resources | {stats['new_resources']:,} | {stats['new_resources_pct']:.1f}% |
| **Total** | **{stats['total_records']:,}** | 100% |

---

## Global Core Biodata Resources (GCBR)

Resources flagged as GCBR: **{stats['gcbr_count']:,}**

---

## New Columns Added

| Column | Description |
|--------|-------------|
| `in_baseline` | True if resource is in GBC baseline |
| `baseline_resource_id` | GBC resource ID if matched |
| `baseline_short_name` | GBC resource name if matched |
| `is_gcbr` | True if Global Core Biodata Resource |
| `baseline_match_type` | How match was determined (PMID/NAME) |

---

## Output Files

- `data/final/final_inventory.csv` ({stats['total_records']:,} records)

---

## Next Steps

Generate final report:

```bash
python scripts/04_generate_report.py
```
"""

    return summary


def main():
    print("=" * 60)
    print("Step 3b: Apply Baseline Flags")
    print("=" * 60)

    # Check inputs exist
    if not INVENTORY_INPUT.exists():
        print(f"\nERROR: Inventory input not found: {INVENTORY_INPUT}")
        print("Run Steps 2 and 2b first")
        return

    if not BASELINE_DECISIONS.exists():
        print(f"\nERROR: Baseline decisions not found: {BASELINE_DECISIONS}")
        print("Run Step 3 first and review baseline_matches.csv")
        return

    # Load data
    print(f"\nLoading inventory: {INVENTORY_INPUT}")
    inventory_df = pd.read_csv(INVENTORY_INPUT)
    print(f"  Loaded {len(inventory_df):,} records")

    print(f"\nLoading baseline decisions: {BASELINE_DECISIONS}")
    baseline_decisions = pd.read_csv(BASELINE_DECISIONS)
    print(f"  Loaded {len(baseline_decisions):,} decision records")

    # Check if any decisions were made
    if 'user_decision' in baseline_decisions.columns:
        user_decisions = baseline_decisions['user_decision'].dropna()
        user_decisions = user_decisions[user_decisions != '']
        print(f"  User decisions found: {len(user_decisions):,}")
    else:
        print("  No user_decision column found - using recommendations")

    # Apply baseline flags
    print("\nApplying baseline flags...")
    flagged_df, stats = apply_baseline_flags(inventory_df, baseline_decisions)

    # Save output
    FINAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    flagged_df.to_csv(FINAL_OUTPUT, index=False)
    print(f"\n  Saved: {FINAL_OUTPUT}")

    # Generate summary
    summary = generate_summary(stats)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(summary)
    print(f"  Saved summary: {SUMMARY_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("BASELINE FLAGS APPLIED")
    print("=" * 60)
    print(f"\nTotal records: {stats['total_records']:,}")
    print(f"  In baseline: {stats['in_baseline']:,} ({stats['in_baseline_pct']:.1f}%)")
    print(f"  New resources: {stats['new_resources']:,} ({stats['new_resources_pct']:.1f}%)")
    print(f"  GCBR flagged: {stats['gcbr_count']:,}")
    print(f"\nFinal inventory saved to: {FINAL_OUTPUT}")
    print("\nWhen ready, generate final report:")
    print("  python scripts/04_generate_report.py")


if __name__ == "__main__":
    main()
