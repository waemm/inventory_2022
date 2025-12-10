#!/usr/bin/env python3
"""
Script 02b: Apply Merge Decisions (v2)

Applies user-reviewed merge decisions from proposed_merges.csv to create
the deduplicated combined inventory.

User Marking System:
- 'y' = Primary record - use this best_name, merge others into it
- 'x' = Merge these rows together (for 3+ row groups)
- 'qw' = URL mismatch error - export to separate file for review
- blank = For MERGE recommendation: auto-merge. For REVIEW: keep separate.

Input:
- data/combined/combined_batches.csv
- review/proposed_merges.csv (edited by user)

Output:
- data/deduplicated/merged_inventory.csv
- data/deduplicated/url_mismatch_review.csv (qw cases)
- docs/02b_MERGE_APPLIED_SUMMARY.md

Usage:
    python scripts/02b_apply_merges.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data"
REVIEW_DIR = BASE_DIR / "review"
DOCS_DIR = BASE_DIR / "docs"

# Input files
COMBINED_INPUT = DATA_DIR / "combined/combined_batches.csv"
MERGE_DECISIONS = REVIEW_DIR / "proposed_merges.csv"

# Output files
DEDUPED_OUTPUT = DATA_DIR / "deduplicated/merged_inventory.csv"
QW_REVIEW_OUTPUT = DATA_DIR / "deduplicated/url_mismatch_review.csv"
SUMMARY_FILE = DOCS_DIR / "02b_MERGE_APPLIED_SUMMARY.md"


def apply_merges(combined_df: pd.DataFrame, merge_decisions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Apply merge decisions to combined dataframe.

    Marking system:
    - 'y' = Primary record, use this best_name
    - 'x' = Merge these together
    - 'qw' = URL mismatch, separate file
    - blank + MERGE recommendation = auto-merge
    - blank + REVIEW/LIKELY_MERGE = keep separate

    Returns:
        tuple: (merged_df, qw_df, stats_dict)
    """
    # Track rows to remove and metadata to merge
    rows_to_remove = set()
    rows_to_update_name = {}  # row_id -> new_best_name
    qw_row_ids = set()

    # Group decisions by merge_group_id
    groups = merge_decisions.groupby('merge_group_id')

    merge_count = 0
    kept_separate_count = 0
    qw_count = 0

    for group_id, group_df in groups:
        decisions = group_df['user_decision'].fillna('').tolist()
        row_ids = group_df['row_id'].tolist()
        names = group_df['best_name'].tolist()
        rec = group_df['recommendation'].iloc[0]

        has_y = any(d == 'y' for d in decisions)
        has_x = any(d == 'x' for d in decisions)
        has_qw = any(d == 'qw' for d in decisions)
        all_blank = all(d == '' for d in decisions)

        # Handle qw cases - extract to separate file
        if has_qw:
            for i, decision in enumerate(decisions):
                if decision == 'qw':
                    qw_row_ids.add(row_ids[i])
                    qw_count += 1

        # Determine merge action
        should_merge = False
        primary_row_id = None
        primary_name = None
        rows_to_merge = []

        if has_y:
            # Merge into the y-marked row
            should_merge = True
            for i, decision in enumerate(decisions):
                if decision == 'y':
                    primary_row_id = row_ids[i]
                    primary_name = names[i]
                elif decision != 'qw':
                    rows_to_merge.append(row_ids[i])

        elif has_x:
            # Merge all x-marked rows
            should_merge = True
            x_rows = [(row_ids[i], names[i]) for i, d in enumerate(decisions) if d == 'x']
            if x_rows:
                # Pick the best name (longest, most descriptive)
                # Special cases handled
                primary_row_id = x_rows[0][0]
                primary_name = max([n for _, n in x_rows], key=len)

                # Special overrides based on user feedback
                name_set = set(n for _, n in x_rows)
                if 'GenBank' in name_set:
                    primary_name = 'GenBank'
                elif 'UCSC' in name_set:
                    primary_name = 'UCSC'
                elif 'Gene Ontology Consortium' in name_set:
                    primary_name = 'Gene Ontology Consortium'

                for rid, _ in x_rows[1:]:
                    rows_to_merge.append(rid)

        elif all_blank and rec == 'MERGE':
            # Auto-merge for MERGE recommendation with no marks
            should_merge = True
            primary_row_id = row_ids[0]
            # Pick best name
            unique_names = list(dict.fromkeys(names))
            if len(unique_names) == 1:
                primary_name = unique_names[0]
            else:
                # Prefer non-truncated, longer names
                primary_name = max(unique_names, key=lambda n: (not n.startswith('irtual'), len(n)))

            for rid in row_ids[1:]:
                rows_to_merge.append(rid)

        else:
            # Keep separate
            kept_separate_count += 1

        if should_merge and primary_row_id is not None:
            merge_count += 1

            # Update primary row name if needed
            if primary_name:
                rows_to_update_name[primary_row_id] = primary_name

            # Mark other rows for removal
            for rid in rows_to_merge:
                if rid not in qw_row_ids:
                    rows_to_remove.add(rid)

    # Apply changes to dataframe
    deduped_df = combined_df.copy()

    # Update names
    for row_id, new_name in rows_to_update_name.items():
        if row_id in deduped_df.index:
            deduped_df.loc[row_id, 'best_name'] = new_name

    # Extract qw rows to separate dataframe
    qw_df = deduped_df.loc[deduped_df.index.isin(qw_row_ids)].copy()

    # Remove merged rows and qw rows from main dataframe
    all_rows_to_remove = rows_to_remove | qw_row_ids
    deduped_df = deduped_df.drop(index=list(all_rows_to_remove), errors='ignore')

    # Add merge tracking columns
    deduped_df['was_merged'] = deduped_df.index.isin(rows_to_update_name.keys())

    stats = {
        'input_records': len(combined_df),
        'output_records': len(deduped_df),
        'records_merged_away': len(rows_to_remove),
        'qw_records': len(qw_row_ids),
        'merge_groups_applied': merge_count,
        'groups_kept_separate': kept_separate_count,
        'reduction_pct': ((len(rows_to_remove) + len(qw_row_ids)) / len(combined_df) * 100) if len(combined_df) > 0 else 0
    }

    return deduped_df, qw_df, stats


def generate_summary(stats: dict) -> str:
    """Generate markdown summary of merge application."""

    summary = f"""# Step 2b: Merge Application Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

Applied user-reviewed merge decisions to deduplicate the combined inventory.

---

## Results

| Metric | Value |
|--------|-------|
| Input records | {stats['input_records']:,} |
| Output records | {stats['output_records']:,} |
| Records merged away | {stats['records_merged_away']:,} |
| URL mismatch cases (qw) | {stats['qw_records']:,} |
| Total reduction | {stats['reduction_pct']:.1f}% |

---

## Merge Statistics

| Action | Count |
|--------|-------|
| Merge groups applied | {stats['merge_groups_applied']:,} |
| Groups kept separate | {stats['groups_kept_separate']:,} |

---

## Output Files

- `data/deduplicated/merged_inventory.csv` ({stats['output_records']:,} records)
- `data/deduplicated/url_mismatch_review.csv` ({stats['qw_records']:,} records for later review)

---

## URL Mismatch Cases

Records marked with 'qw' have been exported to a separate file for manual review.
These are cases where the URL doesn't match the resource name and need investigation.

---

## Next Steps

Proceed to baseline comparison:

```bash
python scripts/03_identify_baseline.py
```
"""

    return summary


def main():
    print("=" * 60)
    print("Step 2b: Apply Merge Decisions")
    print("=" * 60)

    # Check inputs exist
    if not COMBINED_INPUT.exists():
        print(f"\nERROR: Combined input not found: {COMBINED_INPUT}")
        print("Run Step 2 first: python scripts/02_identify_duplicates.py")
        return

    if not MERGE_DECISIONS.exists():
        print(f"\nERROR: Merge decisions not found: {MERGE_DECISIONS}")
        print("Run Step 2 first and review proposed_merges.csv")
        return

    # Load data
    print(f"\nLoading combined inventory: {COMBINED_INPUT}")
    combined_df = pd.read_csv(COMBINED_INPUT)
    print(f"  Loaded {len(combined_df):,} records")

    print(f"\nLoading merge decisions: {MERGE_DECISIONS}")
    merge_decisions = pd.read_csv(MERGE_DECISIONS)
    print(f"  Loaded {len(merge_decisions):,} merge records")

    # Count user decisions
    if 'user_decision' in merge_decisions.columns:
        decisions = merge_decisions['user_decision'].fillna('')
        y_count = (decisions == 'y').sum()
        x_count = (decisions == 'x').sum()
        qw_count = (decisions == 'qw').sum()
        print(f"  User marks: y={y_count}, x={x_count}, qw={qw_count}")

    # Apply merges
    print("\nApplying merge decisions...")
    deduped_df, qw_df, stats = apply_merges(combined_df, merge_decisions)

    # Save outputs
    DEDUPED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    deduped_df.to_csv(DEDUPED_OUTPUT, index=False)
    print(f"\n  Saved: {DEDUPED_OUTPUT} ({len(deduped_df):,} records)")

    if len(qw_df) > 0:
        qw_df.to_csv(QW_REVIEW_OUTPUT, index=False)
        print(f"  Saved: {QW_REVIEW_OUTPUT} ({len(qw_df):,} records)")

    # Generate summary
    summary = generate_summary(stats)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(summary)
    print(f"  Saved summary: {SUMMARY_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("MERGE APPLICATION COMPLETE")
    print("=" * 60)
    print(f"\nInput: {stats['input_records']:,} records")
    print(f"Output: {stats['output_records']:,} records")
    print(f"Merged away: {stats['records_merged_away']:,}")
    print(f"URL mismatch (qw): {stats['qw_records']:,}")
    print(f"Reduction: {stats['reduction_pct']:.1f}%")
    print(f"\nMerge groups applied: {stats['merge_groups_applied']:,}")
    print(f"Groups kept separate: {stats['groups_kept_separate']:,}")
    print(f"\nOutput saved to: {DEDUPED_OUTPUT}")
    print("\nWhen ready, proceed to Step 3:")
    print("  python scripts/03_identify_baseline.py")


if __name__ == "__main__":
    main()
