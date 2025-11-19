#!/usr/bin/env python3
"""
analyze_gbc_results.py - Comprehensive analysis of GBC scan results

Usage: python scripts/analyze_gbc_results.py <results_file>
Example: python scripts/analyze_gbc_results.py data/gbc_scan_results_20251119_150000.csv
"""

import pandas as pd
import numpy as np
import sys
import json
from pathlib import Path

# Get results file from command line or find most recent
if len(sys.argv) > 1:
    results_file = sys.argv[1]
else:
    # Find most recent gbc_scan_results file
    data_dir = Path('data')
    gbc_files = list(data_dir.glob('gbc_scan_results_*.csv'))
    if not gbc_files:
        print("❌ No GBC scan results found. Run scan_gbc_full.py first.")
        sys.exit(1)
    results_file = max(gbc_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Using most recent results: {results_file}\n")

# Load results
df = pd.read_csv(results_file)

print("=" * 80)
print(f"GBC PUBLICATION ANALYSIS - SCAN RESULTS ({len(df)} URLs)")
print("=" * 80)

# Basic stats
print(f"\n📊 OVERALL STATISTICS:")
print(f"   Total URLs scanned: {len(df)}")
print(f"   Live URLs: {df['is_live'].sum()} ({df['is_live'].sum()/len(df)*100:.1f}%)")
print(f"   Failed URLs: {(~df['is_live']).sum()} ({(~df['is_live']).sum()/len(df)*100:.1f}%)")

# Likelihood distribution
print(f"\n📈 LIKELIHOOD DISTRIBUTION:")
for likelihood in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'VERY LOW']:
    count = (df['likelihood'] == likelihood).sum()
    pct = count / len(df) * 100
    print(f"   {likelihood:12s}: {count:4d} ({pct:5.1f}%)")

# High quality detection
high_quality = ((df['likelihood'] == 'CRITICAL') | (df['likelihood'] == 'HIGH')).sum()
print(f"\n🎯 HIGH QUALITY DETECTION (CRITICAL + HIGH):")
print(f"   Count: {high_quality}/{len(df)} ({high_quality/len(df)*100:.1f}%)")

# Score statistics (live only)
live_df = df[df['is_live'] == True]
print(f"\n💯 SCORE STATISTICS (Live URLs only, n={len(live_df)}):")
if len(live_df) > 0:
    print(f"   Mean: {live_df['total_score'].mean():.1f}")
    print(f"   Median: {live_df['total_score'].median():.1f}")
    print(f"   Std Dev: {live_df['total_score'].std():.1f}")
    print(f"   Min: {live_df['total_score'].min():.0f}")
    print(f"   Max: {live_df['total_score'].max():.0f}")

    print(f"\n   Quartiles:")
    print(f"   25th percentile: {live_df['total_score'].quantile(0.25):.1f}")
    print(f"   50th percentile: {live_df['total_score'].quantile(0.50):.1f}")
    print(f"   75th percentile: {live_df['total_score'].quantile(0.75):.1f}")

# Wayback Machine stats
if 'wayback_used' in df.columns:
    wayback_rescued = df[df['wayback_used'] == True]
    print(f"\n🕰️  WAYBACK MACHINE RESCUE:")
    print(f"   Rescued via Wayback: {len(wayback_rescued)} ({len(wayback_rescued)/len(df)*100:.1f}%)")
    if len(wayback_rescued) > 0:
        print(f"   Mean score (Wayback): {wayback_rescued['total_score'].mean():.1f}")
        print(f"   CRITICAL+HIGH (Wayback): {((wayback_rescued['likelihood'] == 'CRITICAL') | (wayback_rescued['likelihood'] == 'HIGH')).sum()}")

        # Show top Wayback rescues
        print(f"\n   Top 10 Wayback rescues:")
        top_wayback = wayback_rescued.nlargest(10, 'total_score')
        for idx, (_, row) in enumerate(top_wayback.iterrows(), 1):
            entity = str(row.get('primary_entity_long', 'Unknown'))[:40] if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))[:40]
            date = row.get('wayback_snapshot_date', 'Unknown')
            print(f"   {idx:2d}. {row['total_score']:3.0f} pts | {date} | {entity}")

# Meta redirects
meta_redirected = df[df['meta_redirects'] > 0]
print(f"\n🔀 META REFRESH REDIRECTS:")
print(f"   Sites with meta redirects: {len(meta_redirected)} ({len(meta_redirected)/len(df)*100:.1f}%)")
if len(meta_redirected) > 0:
    print(f"   Total redirect hops: {meta_redirected['meta_redirects'].sum():.0f}")

# Error analysis
failed_df = df[~df['is_live']]
print(f"\n❌ FAILED URLS ANALYSIS ({len(failed_df)} sites):")
if len(failed_df) > 0:
    # Group by error type
    error_types = {}
    for _, row in failed_df.iterrows():
        error = str(row.get('error_message', 'Unknown'))
        if 'Timeout' in error:
            error_type = 'Timeout'
        elif 'HTTP 404' in error:
            error_type = 'HTTP 404 Not Found'
        elif 'HTTP 502' in error:
            error_type = 'HTTP 502 Bad Gateway'
        elif 'HTTP 503' in error:
            error_type = 'HTTP 503 Service Unavailable'
        elif 'HTTPConnectionPool' in error or 'HTTPSConnectionPool' in error:
            error_type = 'Connection Error'
        elif 'SSL' in error:
            error_type = 'SSL Error'
        else:
            error_type = 'Other Error'

        error_types[error_type] = error_types.get(error_type, 0) + 1

    for error_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
        print(f"   {error_type:30s}: {count:4d} ({count/len(failed_df)*100:.1f}%)")

# Zero scorers (live but scored 0)
zero_scorers = live_df[live_df['total_score'] == 0]
print(f"\n🔍 ZERO SCORERS (Live sites with score = 0):")
print(f"   Count: {len(zero_scorers)} ({len(zero_scorers)/len(live_df)*100:.1f}% of live sites)")
if len(zero_scorers) > 0 and len(zero_scorers) <= 20:
    print(f"\n   Sample sites:")
    for _, row in zero_scorers.head(20).iterrows():
        entity = str(row.get('primary_entity_long', 'Unknown'))[:40] if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))[:40]
        print(f"   - {entity:45s} | {row['url'][:50]}")

# Low scorers (1-4)
low_scorers = live_df[(live_df['total_score'] > 0) & (live_df['total_score'] < 5)]
print(f"\n⚠️  LOW SCORERS (Live sites with score 1-4):")
print(f"   Count: {len(low_scorers)} ({len(low_scorers)/len(live_df)*100:.1f}% of live sites)")

# Top 30 scorers
print(f"\n🏆 TOP 30 HIGHEST SCORING SITES:")
top_30 = df.nlargest(30, 'total_score')
for idx, (_, row) in enumerate(top_30.iterrows(), 1):
    entity = str(row.get('primary_entity_long', 'Unknown'))[:40] if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))[:40]
    status = "✅" if row['is_live'] else "❌"
    meta = f" [META:{row['meta_redirects']:.0f}]" if row['meta_redirects'] > 0 else ""
    print(f"   {idx:2d}. {row['total_score']:3.0f} pts | {status}{meta} | {entity}")

# Domain analysis
print(f"\n🌐 DOMAIN ANALYSIS:")
print(f"   Unique domains: {df['domain'].nunique()}")
top_domains = df['domain'].value_counts().head(15)
print(f"\n   Top 15 domains by URL count:")
for domain, count in top_domains.items():
    domain_df = df[df['domain'] == domain]
    avg_score = domain_df[domain_df['is_live']]['total_score'].mean() if domain_df['is_live'].any() else 0
    live_count = domain_df['is_live'].sum()
    print(f"   {domain:45s}: {count:3d} URLs ({live_count:3d} live, avg: {avg_score:.1f})")

# GCBR analysis
if 'is_gcbr' in df.columns:
    gcbr_df = df[df['is_gcbr'] == True]
    print(f"\n⭐ GLOBAL CORE BIODATA RESOURCE (GCBR) ANALYSIS:")
    print(f"   GCBR resources: {len(gcbr_df)} ({len(gcbr_df)/len(df)*100:.1f}%)")
    if len(gcbr_df) > 0:
        gcbr_live = gcbr_df[gcbr_df['is_live'] == True]
        print(f"   Live: {len(gcbr_live)} ({len(gcbr_live)/len(gcbr_df)*100:.1f}%)")
        if len(gcbr_live) > 0:
            print(f"   Mean score (live): {gcbr_live['total_score'].mean():.1f}")
            gcbr_critical = gcbr_df[gcbr_df['likelihood'] == 'CRITICAL']
            gcbr_high = gcbr_df[(gcbr_df['likelihood'] == 'CRITICAL') | (gcbr_df['likelihood'] == 'HIGH')]
            print(f"   CRITICAL: {len(gcbr_critical)} ({len(gcbr_critical)/len(gcbr_df)*100:.1f}%)")
            print(f"   CRITICAL+HIGH: {len(gcbr_high)} ({len(gcbr_high)/len(gcbr_df)*100:.1f}%)")

# Response time analysis
print(f"\n⏱️  RESPONSE TIME ANALYSIS (Live URLs):")
response_times = live_df['response_time_ms'].dropna()
if len(response_times) > 0:
    print(f"   Mean: {response_times.mean():.0f}ms")
    print(f"   Median: {response_times.median():.0f}ms")
    print(f"   Min: {response_times.min():.0f}ms")
    print(f"   Max: {response_times.max():.0f}ms")

    # Slow sites (>5 seconds)
    slow_sites = live_df[live_df['response_time_ms'] > 5000]
    print(f"   Slow sites (>5s): {len(slow_sites)} ({len(slow_sites)/len(live_df)*100:.1f}%)")

print(f"\n{'=' * 80}")
print(f"✅ ANALYSIS COMPLETE")
print(f"{'=' * 80}")

# Save summary stats
summary = {
    'total_urls': len(df),
    'live_urls': int(df['is_live'].sum()),
    'failed_urls': int((~df['is_live']).sum()),
    'critical_high_count': int(high_quality),
    'critical_high_percent': float(high_quality/len(df)*100),
    'mean_score': float(live_df['total_score'].mean()) if len(live_df) > 0 else 0,
    'median_score': float(live_df['total_score'].median()) if len(live_df) > 0 else 0,
    'zero_scorers': int(len(zero_scorers)),
    'low_scorers': int(len(low_scorers)),
    'meta_redirects': int(len(meta_redirected))
}

# Add Wayback stats if available
if 'wayback_used' in df.columns:
    wayback_rescued = df[df['wayback_used'] == True]
    summary['wayback_rescued'] = int(len(wayback_rescued))
    summary['wayback_rescued_percent'] = float(len(wayback_rescued)/len(df)*100)
    if len(wayback_rescued) > 0:
        summary['wayback_mean_score'] = float(wayback_rescued['total_score'].mean())

# Extract timestamp from filename
filename = Path(results_file).stem
summary_path = f"data/{filename}_summary.json"
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n📁 Summary saved to: {summary_path}")
