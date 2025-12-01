#!/usr/bin/env python3
"""
Script 25: Fetch EuropePMC Metadata

Purpose: Get metadata from EuropePMC API for all PMIDs
         - publication_date
         - affiliation
         - authors
         - grant_ids
         - grant_agencies
         - num_citations

Authors: AI Assistant
Date: 2025-11-27
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, NamedTuple, Optional

import pandas as pd
import requests


class Args(NamedTuple):
    """Command-line arguments"""
    input_file: str
    output_dir: str
    chunk_size: int


def get_args() -> Args:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Fetch metadata from EuropePMC API'
    )

    parser.add_argument(
        '--input',
        required=True,
        help='Path to url_checked_resources.csv'
    )
    parser.add_argument(
        '-o', '--output-dir',
        required=True,
        help='Output directory (finalization folder)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=20,
        help='Number of PMIDs per API request (default: 20)'
    )

    args = parser.parse_args()

    return Args(
        input_file=args.input,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size
    )


def extract_all_pmids(pmid_str) -> List[str]:
    """Extract all PMIDs from a comma-separated string"""
    if pd.isna(pmid_str):
        return []
    pmid_str = str(pmid_str).strip('"').strip()
    pmids = [p.strip().strip('"') for p in pmid_str.split(',')]
    return [p for p in pmids if p]


def query_epmc(pmids: List[str]) -> Dict[str, dict]:
    """
    Query EuropePMC API for metadata.

    Returns dict mapping PMID -> metadata
    """
    if not pmids:
        return {}

    # Build query
    query = ' OR '.join(set(pmids))
    url = (
        'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
        f'?query={query}&resultType=core&format=json&pageSize=1000'
    )

    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            print(f"    Warning: API returned status {r.status_code}")
            return {}

        data = r.json()
        results = data.get('resultList', {}).get('result', [])

        metadata = {}
        for paper in results:
            pmid = paper.get('id', '')
            if not pmid:
                continue

            # Extract authors
            authors = []
            for author in paper.get('authorList', {}).get('author', []):
                if author:
                    authors.append(author.get('fullName', ''))

            # Extract grants
            grant_ids = []
            agencies = []
            for grant in paper.get('grantsList', {}).get('grant', []):
                if grant:
                    grant_id = grant.get('grantId', '')
                    agency = grant.get('agency', '')
                    if grant_id:
                        grant_ids.append(grant_id)
                    if agency:
                        agencies.append(agency)

            metadata[pmid] = {
                'publication_date': paper.get('firstPublicationDate', ''),
                'affiliation': paper.get('affiliation', ''),
                'authors': ', '.join([a for a in authors if a]),
                'grant_ids': ', '.join([g for g in grant_ids if g]),
                'grant_agencies': ', '.join([a for a in agencies if a]),
                'num_citations': paper.get('citedByCount', 0)
            }

        return metadata

    except Exception as e:
        print(f"    Warning: API error - {str(e)[:50]}")
        return {}


def fetch_all_metadata(all_pmids: List[str], chunk_size: int) -> Dict[str, dict]:
    """Fetch metadata for all PMIDs in batches"""
    unique_pmids = list(set(all_pmids))
    print(f"  Fetching metadata for {len(unique_pmids)} unique PMIDs...")

    all_metadata = {}

    # Process in chunks
    for i in range(0, len(unique_pmids), chunk_size):
        chunk = unique_pmids[i:i + chunk_size]
        chunk_metadata = query_epmc(chunk)
        all_metadata.update(chunk_metadata)

        if (i + chunk_size) % 100 == 0 or i + chunk_size >= len(unique_pmids):
            print(f"    Processed {min(i + chunk_size, len(unique_pmids))}/{len(unique_pmids)} PMIDs...")

        # Rate limiting
        time.sleep(0.2)

    return all_metadata


def aggregate_metadata(pmid_str, metadata_dict: Dict[str, dict]) -> dict:
    """
    Aggregate metadata for a resource with multiple PMIDs.

    For resources with multiple papers:
    - publication_date: earliest date
    - affiliation: join with semicolons
    - authors: join unique authors
    - grant_ids: join unique
    - grant_agencies: join unique
    - num_citations: sum
    """
    pmids = extract_all_pmids(pmid_str)

    if not pmids:
        return {
            'publication_date': '',
            'affiliation': '',
            'authors': '',
            'grant_ids': '',
            'grant_agencies': '',
            'num_citations': ''
        }

    # Collect metadata for all PMIDs
    dates = []
    affiliations = []
    all_authors = set()
    all_grants = set()
    all_agencies = set()
    total_citations = 0

    for pmid in pmids:
        meta = metadata_dict.get(pmid, {})

        date = meta.get('publication_date', '')
        if date:
            dates.append(date)

        affil = meta.get('affiliation', '')
        if affil:
            affiliations.append(affil)

        authors = meta.get('authors', '')
        if authors:
            for a in authors.split(', '):
                if a.strip():
                    all_authors.add(a.strip())

        grants = meta.get('grant_ids', '')
        if grants:
            for g in grants.split(', '):
                if g.strip():
                    all_grants.add(g.strip())

        agencies = meta.get('grant_agencies', '')
        if agencies:
            for a in agencies.split(', '):
                if a.strip():
                    all_agencies.add(a.strip())

        citations = meta.get('num_citations', 0)
        if citations:
            try:
                total_citations += int(citations)
            except (ValueError, TypeError):
                pass

    # Aggregate
    earliest_date = min(dates) if dates else ''

    return {
        'publication_date': earliest_date,
        'affiliation': '; '.join(affiliations),
        'authors': ', '.join(sorted(all_authors)),
        'grant_ids': ', '.join(sorted(all_grants)),
        'grant_agencies': ', '.join(sorted(all_agencies)),
        'num_citations': total_citations if total_citations > 0 else ''
    }


def main() -> None:
    """Main function"""
    args = get_args()

    print(f"Phase 9 - Script 25: Fetch EuropePMC Metadata")
    print(f"=" * 50)
    print(f"Input: {args.input_file}")
    print(f"Output directory: {args.output_dir}")
    print(f"Chunk size: {args.chunk_size}")
    print()

    # Load input
    print("Loading URL-checked resources...")
    df = pd.read_csv(args.input_file)
    print(f"  Loaded {len(df)} rows")
    print()

    # Extract all PMIDs
    print("Extracting PMIDs...")
    all_pmids = []
    for pmid_str in df['ID']:
        all_pmids.extend(extract_all_pmids(pmid_str))
    print(f"  Found {len(all_pmids)} total PMIDs ({len(set(all_pmids))} unique)")
    print()

    # Fetch metadata from API
    print("Querying EuropePMC API...")
    start_time = time.time()
    metadata_dict = fetch_all_metadata(all_pmids, args.chunk_size)
    elapsed = time.time() - start_time
    print(f"  Fetched metadata for {len(metadata_dict)} PMIDs in {elapsed:.1f} seconds")
    print()

    # Apply aggregated metadata to each row
    print("Applying metadata to resources...")

    def apply_metadata(row):
        return aggregate_metadata(row['ID'], metadata_dict)

    metadata_results = df.apply(apply_metadata, axis=1)

    df['publication_date'] = metadata_results.apply(lambda x: x['publication_date'])
    df['affiliation'] = metadata_results.apply(lambda x: x['affiliation'])
    df['authors'] = metadata_results.apply(lambda x: x['authors'])
    df['grant_ids'] = metadata_results.apply(lambda x: x['grant_ids'])
    df['grant_agencies'] = metadata_results.apply(lambda x: x['grant_agencies'])
    df['num_citations'] = metadata_results.apply(lambda x: x['num_citations'])

    # Statistics
    stats = {
        'script': '25_fetch_epmc_metadata',
        'timestamp': datetime.now().isoformat(),
        'runtime_seconds': round(elapsed, 1),
        'input_rows': len(df),
        'total_pmids': len(all_pmids),
        'unique_pmids': len(set(all_pmids)),
        'metadata_fetched': len(metadata_dict),
        'fields_populated': {
            'publication_date': int((df['publication_date'] != '').sum()),
            'affiliation': int((df['affiliation'] != '').sum()),
            'authors': int((df['authors'] != '').sum()),
            'grant_ids': int((df['grant_ids'] != '').sum()),
            'grant_agencies': int((df['grant_agencies'] != '').sum()),
            'num_citations': int((df['num_citations'] != '').sum())
        }
    }

    print(f"  Fields populated:")
    for field, count in stats['fields_populated'].items():
        pct = count / len(df) * 100 if len(df) > 0 else 0
        print(f"    - {field}: {count} ({pct:.1f}%)")
    print()

    # Save outputs
    output_file = os.path.join(args.output_dir, 'metadata_enriched_resources.csv')
    df.to_csv(output_file, index=False)
    print(f"Saved metadata-enriched resources to: {output_file}")

    # Save raw metadata for reference
    metadata_file = os.path.join(args.output_dir, 'epmc_metadata.csv')
    metadata_list = [
        {'pmid': pmid, **meta}
        for pmid, meta in metadata_dict.items()
    ]
    pd.DataFrame(metadata_list).to_csv(metadata_file, index=False)
    print(f"Saved raw EPMC metadata to: {metadata_file}")

    stats_file = os.path.join(args.output_dir, 'script_25_stats.json')
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Saved statistics to: {stats_file}")

    print()
    print(f"Done! Enriched {len(df)} resources with metadata from {len(metadata_dict)} PMIDs")


if __name__ == '__main__':
    main()
