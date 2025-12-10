#!/usr/bin/env python3
"""
Script 01: Filter Live URLs

Filters both bioresource inventory batches to only include resources
with live URLs (extracted_url_status == "200").

Input:
- 2010-2022 batch: unified_bioresource_pipeline/post_processing/results/final_inventory_QC_FIXED.csv
- 2022-2025 batch: unified_bioresource_pipeline/2025-12-04-111420-z381s/post_processing/final_inventory_QC_FIXED.csv

Output:
- data/filtered/batch_2010_2022_live.csv
- data/filtered/batch_2022_2025_live.csv
- docs/01_FILTER_SUMMARY.md
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"

# Input files (relative to inventory_2022 root)
INVENTORY_ROOT = BASE_DIR.parent
BATCH_2010_2022 = INVENTORY_ROOT / "post_processing/results/final_inventory_QC_FIXED.csv"
BATCH_2022_2025 = INVENTORY_ROOT / "2025-12-04-111420-z381s/post_processing/final_inventory_QC_FIXED.csv"

# Output files
OUTPUT_2010_2022 = DATA_DIR / "filtered/batch_2010_2022_live.csv"
OUTPUT_2022_2025 = DATA_DIR / "filtered/batch_2022_2025_live.csv"
SUMMARY_FILE = DOCS_DIR / "01_FILTER_SUMMARY.md"


def filter_live_urls(df: pd.DataFrame, batch_name: str) -> tuple[pd.DataFrame, dict]:
    """
    Filter dataframe to only include rows with extracted_url_status == "200".

    Returns:
        tuple: (filtered_df, stats_dict)
    """
    original_count = len(df)

    # Filter for live URLs only (status == "200")
    # Handle both string and numeric comparisons
    df['extracted_url_status'] = df['extracted_url_status'].astype(str)
    live_df = df[df['extracted_url_status'] == '200'].copy()

    # Add source batch column
    live_df['source_batch'] = batch_name

    # Calculate filtered records
    filtered_df = df[df['extracted_url_status'] != '200'].copy()

    # Get status distribution of filtered records
    status_counts = filtered_df['extracted_url_status'].value_counts().head(10).to_dict()

    stats = {
        'original_count': original_count,
        'live_count': len(live_df),
        'filtered_count': original_count - len(live_df),
        'retention_pct': (len(live_df) / original_count * 100) if original_count > 0 else 0,
        'status_distribution': status_counts,
        'sample_filtered': filtered_df[['best_name', 'extracted_url', 'extracted_url_status']].head(10).to_dict('records')
    }

    return live_df, stats


def generate_summary(stats_2010_2022: dict, stats_2022_2025: dict) -> str:
    """Generate markdown summary of filtering results."""

    total_input = stats_2010_2022['original_count'] + stats_2022_2025['original_count']
    total_live = stats_2010_2022['live_count'] + stats_2022_2025['live_count']
    total_filtered = stats_2010_2022['filtered_count'] + stats_2022_2025['filtered_count']
    total_retention = (total_live / total_input * 100) if total_input > 0 else 0

    summary = f"""# Step 1: URL Filtering Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

Filtering both bioresource inventory batches to include only resources with live URLs (HTTP status 200).

---

## Results

| Batch | Input | Live URLs | Filtered Out | Retention |
|-------|-------|-----------|--------------|-----------|
| 2010-2022 | {stats_2010_2022['original_count']:,} | {stats_2010_2022['live_count']:,} | {stats_2010_2022['filtered_count']:,} | {stats_2010_2022['retention_pct']:.1f}% |
| 2022-2025 | {stats_2022_2025['original_count']:,} | {stats_2022_2025['live_count']:,} | {stats_2022_2025['filtered_count']:,} | {stats_2022_2025['retention_pct']:.1f}% |
| **Total** | **{total_input:,}** | **{total_live:,}** | **{total_filtered:,}** | **{total_retention:.1f}%** |

---

## Filtered Records by Status (2010-2022 batch)

| Status | Count |
|--------|-------|
"""

    for status, count in stats_2010_2022['status_distribution'].items():
        summary += f"| {status} | {count} |\n"

    summary += """
---

## Sample Filtered Records (2010-2022 batch - first 10)

| best_name | extracted_url | status |
|-----------|---------------|--------|
"""

    for record in stats_2010_2022['sample_filtered']:
        name = record.get('best_name', 'N/A')[:40]
        url = str(record.get('extracted_url', 'N/A'))[:50]
        status = record.get('extracted_url_status', 'N/A')
        summary += f"| {name} | {url} | {status} |\n"

    summary += f"""
---

## Output Files

- `data/filtered/batch_2010_2022_live.csv` ({stats_2010_2022['live_count']:,} records)
- `data/filtered/batch_2022_2025_live.csv` ({stats_2022_2025['live_count']:,} records)

---

## Ready for Step 2?

Review the above statistics. If satisfied with the filtering results, proceed to deduplication:

```bash
python scripts/02_identify_duplicates.py
```
"""

    return summary


def main():
    print("=" * 60)
    print("Step 1: Filter Live URLs")
    print("=" * 60)

    # Load 2010-2022 batch
    print(f"\nLoading 2010-2022 batch from: {BATCH_2010_2022}")
    df_2010_2022 = pd.read_csv(BATCH_2010_2022)
    print(f"  Loaded {len(df_2010_2022):,} records")

    # Load 2022-2025 batch
    print(f"\nLoading 2022-2025 batch from: {BATCH_2022_2025}")
    df_2022_2025 = pd.read_csv(BATCH_2022_2025)
    print(f"  Loaded {len(df_2022_2025):,} records")

    # Filter both batches
    print("\nFiltering 2010-2022 batch...")
    live_2010_2022, stats_2010_2022 = filter_live_urls(df_2010_2022, "2010-2022")
    print(f"  Live URLs: {stats_2010_2022['live_count']:,} ({stats_2010_2022['retention_pct']:.1f}%)")

    print("\nFiltering 2022-2025 batch...")
    live_2022_2025, stats_2022_2025 = filter_live_urls(df_2022_2025, "2022-2025")
    print(f"  Live URLs: {stats_2022_2025['live_count']:,} ({stats_2022_2025['retention_pct']:.1f}%)")

    # Save filtered files
    print(f"\nSaving filtered files...")
    OUTPUT_2010_2022.parent.mkdir(parents=True, exist_ok=True)
    live_2010_2022.to_csv(OUTPUT_2010_2022, index=False)
    print(f"  Saved: {OUTPUT_2010_2022}")

    live_2022_2025.to_csv(OUTPUT_2022_2025, index=False)
    print(f"  Saved: {OUTPUT_2022_2025}")

    # Generate and save summary
    print(f"\nGenerating summary...")
    summary = generate_summary(stats_2010_2022, stats_2022_2025)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(summary)
    print(f"  Saved: {SUMMARY_FILE}")

    # Print summary to console
    print("\n" + "=" * 60)
    print("FILTERING COMPLETE")
    print("=" * 60)
    total_live = stats_2010_2022['live_count'] + stats_2022_2025['live_count']
    total_input = stats_2010_2022['original_count'] + stats_2022_2025['original_count']
    print(f"\nTotal: {total_live:,} live URLs from {total_input:,} input records")
    print(f"\nReview the summary at: {SUMMARY_FILE}")
    print("\nWhen ready, proceed to Step 2:")
    print("  python scripts/02_identify_duplicates.py")


if __name__ == "__main__":
    main()
