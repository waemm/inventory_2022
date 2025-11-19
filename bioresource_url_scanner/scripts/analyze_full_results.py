#!/usr/bin/env python3
"""
analyze_full_results.py - Comprehensive analysis of full scan results
"""

import pandas as pd
import numpy as np

# Load results
df = pd.read_csv('data/full_scan_results_20251119_142017.csv')

print("=" * 80)
print("FULL SCAN RESULTS ANALYSIS (964 URLs)")
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
    print(f"   {likelihood:12s}: {count:3d} ({pct:5.1f}%)")

# High quality detection
high_quality = ((df['likelihood'] == 'CRITICAL') | (df['likelihood'] == 'HIGH')).sum()
print(f"\n🎯 HIGH QUALITY DETECTION (CRITICAL + HIGH):")
print(f"   Count: {high_quality}/964 ({high_quality/964*100:.1f}%)")

# Score statistics
live_df = df[df['is_live'] == True]
print(f"\n💯 SCORE STATISTICS (Live URLs only, n={len(live_df)}):")
print(f"   Mean: {live_df['total_score'].mean():.1f}")
print(f"   Median: {live_df['total_score'].median():.1f}")
print(f"   Std Dev: {live_df['total_score'].std():.1f}")
print(f"   Min: {live_df['total_score'].min():.0f}")
print(f"   Max: {live_df['total_score'].max():.0f}")

# Quartiles
print(f"\n   Quartiles:")
print(f"   25th percentile: {live_df['total_score'].quantile(0.25):.1f}")
print(f"   50th percentile: {live_df['total_score'].quantile(0.50):.1f}")
print(f"   75th percentile: {live_df['total_score'].quantile(0.75):.1f}")

# Meta redirects
meta_redirected = df[df['meta_redirects'] > 0]
print(f"\n🔀 META REFRESH REDIRECTS:")
print(f"   Sites with meta redirects: {len(meta_redirected)} ({len(meta_redirected)/len(df)*100:.1f}%)")
if len(meta_redirected) > 0:
    print(f"   Total redirect hops: {meta_redirected['meta_redirects'].sum():.0f}")
    print(f"\n   Top meta-redirected sites:")
    for _, row in meta_redirected.nlargest(5, 'meta_redirects').iterrows():
        entity = str(row.get('primary_entity_long', 'Unknown'))[:50] if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))[:50]
        print(f"   - {entity:50s} | {row['meta_redirects']:.0f} hops | Score: {row['total_score']:.0f}")

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
        elif 'HTTPConnectionPool' in error or 'HTTPSConnectionPool' in error:
            error_type = 'Connection Error'
        elif 'SSL' in error:
            error_type = 'SSL Error'
        else:
            error_type = 'Other Error'

        error_types[error_type] = error_types.get(error_type, 0) + 1

    for error_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
        print(f"   {error_type:25s}: {count:3d} ({count/len(failed_df)*100:.1f}%)")

# Zero scorers (live but scored 0)
zero_scorers = live_df[live_df['total_score'] == 0]
print(f"\n🔍 ZERO SCORERS (Live sites with score = 0):")
print(f"   Count: {len(zero_scorers)} ({len(zero_scorers)/len(live_df)*100:.1f}% of live sites)")
if len(zero_scorers) > 0:
    print(f"\n   Sites:")
    for _, row in zero_scorers.iterrows():
        entity = str(row.get('primary_entity_long', 'Unknown'))[:50] if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))[:50]
        print(f"   - {entity:50s} | {row['url'][:60]}")

# Low scorers (1-4)
low_scorers = live_df[(live_df['total_score'] > 0) & (live_df['total_score'] < 5)]
print(f"\n⚠️  LOW SCORERS (Live sites with score 1-4):")
print(f"   Count: {len(low_scorers)} ({len(low_scorers)/len(live_df)*100:.1f}% of live sites)")

# Top 20 scorers
print(f"\n🏆 TOP 20 HIGHEST SCORING SITES:")
top_20 = df.nlargest(20, 'total_score')
for idx, (_, row) in enumerate(top_20.iterrows(), 1):
    entity = str(row.get('primary_entity_long', 'Unknown'))[:45] if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))[:45]
    status = "✅" if row['is_live'] else "❌"
    meta = f" [META:{row['meta_redirects']:.0f}]" if row['meta_redirects'] > 0 else ""
    print(f"   {idx:2d}. {row['total_score']:3.0f} pts | {status}{meta} | {entity}")

# Domain analysis
print(f"\n🌐 DOMAIN ANALYSIS:")
print(f"   Unique domains: {df['domain'].nunique()}")
top_domains = df['domain'].value_counts().head(10)
print(f"\n   Top 10 domains by URL count:")
for domain, count in top_domains.items():
    avg_score = df[df['domain'] == domain]['total_score'].mean()
    print(f"   {domain:40s}: {count:2d} URLs (avg score: {avg_score:.1f})")

# Very high confidence sites
very_high_conf = df[df['very_high_conf'] == True]
print(f"\n⭐ VERY HIGH CONFIDENCE SITES (from original dataset):")
print(f"   Count: {len(very_high_conf)} ({len(very_high_conf)/len(df)*100:.1f}%)")
if len(very_high_conf) > 0:
    very_high_live = very_high_conf[very_high_conf['is_live'] == True]
    print(f"   Live: {len(very_high_live)} ({len(very_high_live)/len(very_high_conf)*100:.1f}%)")
    print(f"   Mean score (live): {very_high_live['total_score'].mean():.1f}")

    very_high_critical = very_high_conf[very_high_conf['likelihood'] == 'CRITICAL']
    print(f"   Scored CRITICAL: {len(very_high_critical)} ({len(very_high_critical)/len(very_high_conf)*100:.1f}%)")

# Article count correlation
print(f"\n📚 ARTICLE COUNT ANALYSIS:")
articles_df = df[df['article_count'] > 0]
if len(articles_df) > 0:
    print(f"   Sites with article count: {len(articles_df)}")
    print(f"   Mean articles per site: {articles_df['article_count'].mean():.1f}")
    print(f"   Median articles: {articles_df['article_count'].median():.0f}")

    # Correlation between article count and score
    live_with_articles = articles_df[articles_df['is_live'] == True]
    if len(live_with_articles) > 1:
        correlation = live_with_articles[['article_count', 'total_score']].corr().iloc[0, 1]
        print(f"   Correlation (articles vs score): {correlation:.3f}")

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
    'live_urls': df['is_live'].sum(),
    'failed_urls': (~df['is_live']).sum(),
    'critical_high_count': high_quality,
    'critical_high_percent': high_quality/len(df)*100,
    'mean_score': live_df['total_score'].mean(),
    'median_score': live_df['total_score'].median(),
    'zero_scorers': len(zero_scorers),
    'low_scorers': len(low_scorers),
    'meta_redirects': len(meta_redirected)
}

import json
with open('data/full_scan_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n📁 Summary saved to: data/full_scan_summary.json")
