#!/usr/bin/env python3
"""
Script 22: Filter Novel Resources

Purpose: Filter set_c_final.csv to only include resources from
         FINAL_novel_bioresources_with_urls.csv

Authors: AI Assistant
Date: 2025-11-27
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import NamedTuple, Optional

import pandas as pd


class Args(NamedTuple):
    """Command-line arguments"""
    set_c_file: str
    final_file: str
    output_dir: str
    session_id: Optional[str]


def get_args() -> Args:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Filter set_c to novel resources only'
    )

    parser.add_argument(
        '--set-c',
        required=True,
        help='Path to set_c_final.csv (full pipeline output)'
    )
    parser.add_argument(
        '--final',
        required=True,
        help='Path to FINAL_novel_bioresources_with_urls.csv (filtered list)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='unified_bioresource_pipeline/results',
        help='Output directory base'
    )
    parser.add_argument(
        '--session-id',
        help='Session ID for output directory (default: auto-generated)'
    )

    args = parser.parse_args()

    return Args(
        set_c_file=args.set_c,
        final_file=args.final,
        output_dir=args.output_dir,
        session_id=args.session_id
    )


def generate_session_id() -> str:
    """Generate a session ID in format: YYYY-MM-DD-HHMMSS-xxxxx"""
    import random
    import string

    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{timestamp}-{suffix}"


def extract_first_pmid(pmid_str) -> Optional[str]:
    """Extract the first PMID from a comma-separated string"""
    if pd.isna(pmid_str):
        return None
    # Handle potential quoting issues
    pmid_str = str(pmid_str).strip('"').strip()
    first = pmid_str.split(',')[0].strip().strip('"')
    return first if first else None


def filter_resources(set_c_df: pd.DataFrame, final_df: pd.DataFrame) -> tuple:
    """
    Filter set_c to only include resources present in final_df.
    Also backfills URLs from FINAL when set_c is missing them.

    Uses first PMID as join key since it's the most reliable match.

    Returns:
        tuple: (filtered_df, backfill_stats)
    """
    # Extract first PMID from each dataframe
    set_c_df = set_c_df.copy()
    final_df = final_df.copy()

    set_c_df['_first_pmid'] = set_c_df['pmid'].apply(extract_first_pmid)
    final_df['_first_pmid'] = final_df['pmid'].apply(extract_first_pmid)

    # Get set of valid first PMIDs from FINAL
    valid_pmids = set(final_df['_first_pmid'].dropna())

    print(f"  Valid PMIDs from FINAL file: {len(valid_pmids)}")

    # Filter set_c to only rows matching valid PMIDs
    filtered = set_c_df[set_c_df['_first_pmid'].isin(valid_pmids)].copy()

    # Count URLs before backfill
    urls_before = filtered['resource_url'].notna().sum()

    # Backfill URLs from FINAL where set_c is missing them
    print(f"\nBackfilling URLs from FINAL file...")
    print(f"  set_c URLs before backfill: {urls_before}")

    # Create lookup from FINAL: first_pmid -> resource_url
    final_urls = final_df[['_first_pmid', 'resource_url']].dropna(subset=['resource_url'])
    final_url_map = dict(zip(final_urls['_first_pmid'], final_urls['resource_url']))
    print(f"  FINAL file has URLs for: {len(final_url_map)} PMIDs")

    # Backfill missing URLs
    def backfill_url(row):
        if pd.isna(row['resource_url']) or row['resource_url'] == '':
            return final_url_map.get(row['_first_pmid'], row['resource_url'])
        return row['resource_url']

    filtered['resource_url'] = filtered.apply(backfill_url, axis=1)

    # Count URLs after backfill
    urls_after = filtered['resource_url'].notna().sum()
    urls_backfilled = urls_after - urls_before

    print(f"  set_c URLs after backfill: {urls_after}")
    print(f"  URLs backfilled from FINAL: {urls_backfilled}")

    backfill_stats = {
        'urls_before': int(urls_before),
        'urls_after': int(urls_after),
        'urls_backfilled': int(urls_backfilled),
        'final_urls_available': len(final_url_map)
    }

    # Drop helper column
    filtered.drop('_first_pmid', axis=1, inplace=True)

    return filtered, backfill_stats


def main() -> None:
    """Main function"""
    args = get_args()

    # Generate or use provided session ID
    session_id = args.session_id or generate_session_id()

    # Create output directory
    output_dir = os.path.join(args.output_dir, session_id, 'finalization')
    os.makedirs(output_dir, exist_ok=True)

    print(f"Phase 9 - Script 22: Filter Novel Resources")
    print(f"=" * 50)
    print(f"Session ID: {session_id}")
    print(f"Output directory: {output_dir}")
    print()

    # Load input files
    print("Loading input files...")
    set_c_df = pd.read_csv(args.set_c_file)
    final_df = pd.read_csv(args.final_file)

    print(f"  set_c_final.csv: {len(set_c_df)} rows")
    print(f"  FINAL_novel_bioresources: {len(final_df)} rows")
    print()

    # Filter resources and backfill URLs
    print("Filtering to novel resources only...")
    filtered_df, backfill_stats = filter_resources(set_c_df, final_df)

    print(f"  Filtered result: {len(filtered_df)} rows")
    print()

    # Calculate statistics
    stats = {
        'session_id': session_id,
        'script': '22_filter_novel_resources',
        'timestamp': datetime.now().isoformat(),
        'input': {
            'set_c_rows': len(set_c_df),
            'final_rows': len(final_df)
        },
        'output': {
            'filtered_rows': len(filtered_df),
            'filter_rate': round(len(filtered_df) / len(set_c_df) * 100, 2)
        },
        'url_backfill': backfill_stats
    }

    # Save outputs
    output_file = os.path.join(output_dir, 'filtered_novel_resources.csv')
    filtered_df.to_csv(output_file, index=False)
    print(f"Saved filtered resources to: {output_file}")

    # Save session metadata
    metadata_file = os.path.join(output_dir, 'session_metadata.json')
    with open(metadata_file, 'w') as f:
        json.dump({
            'session_id': session_id,
            'created': datetime.now().isoformat(),
            'phase': 'phase9_finalization',
            'input_files': {
                'set_c': args.set_c_file,
                'final': args.final_file
            }
        }, f, indent=2)
    print(f"Saved session metadata to: {metadata_file}")

    # Save statistics
    stats_file = os.path.join(output_dir, 'script_22_stats.json')
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Saved statistics to: {stats_file}")

    print()
    print(f"Done! Filtered {len(set_c_df)} -> {len(filtered_df)} resources ({stats['output']['filter_rate']}%)")

    # Return session_id for downstream scripts
    print(f"\nSession ID for downstream scripts: {session_id}")


if __name__ == '__main__':
    main()
