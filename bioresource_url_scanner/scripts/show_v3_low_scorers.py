#!/usr/bin/env python3
"""
show_v3_low_scorers.py - Show all low scorers from V3 results
"""

import pandas as pd

df = pd.read_csv('data/dedup_results_v3.csv')

print("=" * 80)
print("ALL LOW SCORERS IN V3 RESULTS (WITH META REFRESH SUPPORT)")
print("=" * 80)

# Group by likelihood
print("\n📊 BREAKDOWN BY CATEGORY:")
print(f"   VERY LOW (score 0):     {(df['likelihood'] == 'VERY LOW').sum()} sites")
print(f"   LOW (score 1-4):        {(df['likelihood'] == 'LOW').sum()} sites")
print(f"   MEDIUM (score 5-9):     {(df['likelihood'] == 'MEDIUM').sum()} sites")
print(f"   Total low scorers:      {(df['likelihood'].isin(['VERY LOW', 'LOW', 'MEDIUM'])).sum()} sites")

# Show VERY LOW scorers
very_low = df[df['likelihood'] == 'VERY LOW'].sort_values('total_score', ascending=False)
print(f"\n{'=' * 80}")
print(f"VERY LOW SCORERS: {len(very_low)} sites")
print(f"{'=' * 80}")

for idx, (_, row) in enumerate(very_low.iterrows(), 1):
    entity = str(row.get('primary_entity_long')) if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))
    status = "✅ LIVE" if row['is_live'] else "❌ FAILED"
    score = row['total_score']
    meta_redirects = row.get('meta_redirects', 0)

    print(f"\n{idx}. {entity[:60]}")
    print(f"   URL: {row['url'][:75]}")
    print(f"   Status: {status} | Score: {score}")

    if meta_redirects > 0:
        print(f"   🔀 Meta redirects: {meta_redirects}")
        print(f"   Final URL: {row['final_url'][:75]}")

    if row['is_live']:
        indicators = str(row.get('indicators_found', ''))
        if indicators and indicators != 'nan' and len(indicators) > 0:
            print(f"   Indicators: {indicators[:150]}...")
        else:
            print(f"   Indicators: None found")
        print(f"   Response: {row['response_time_ms']:.0f}ms")
    else:
        print(f"   Error: {row.get('error_message', 'Unknown')}")

# Show LOW scorers
low = df[df['likelihood'] == 'LOW'].sort_values('total_score', ascending=False)
if len(low) > 0:
    print(f"\n{'=' * 80}")
    print(f"LOW SCORERS: {len(low)} sites")
    print(f"{'=' * 80}")

    for idx, (_, row) in enumerate(low.iterrows(), 1):
        entity = str(row.get('primary_entity_long')) if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))
        status = "✅ LIVE" if row['is_live'] else "❌ FAILED"
        score = row['total_score']
        meta_redirects = row.get('meta_redirects', 0)

        print(f"\n{idx}. {entity[:60]}")
        print(f"   URL: {row['url'][:75]}")
        print(f"   Status: {status} | Score: {score} (base:{row['base_score']:.0f} + bonus:{row['title_bonus']:.0f})")

        if meta_redirects > 0:
            print(f"   🔀 Meta redirects: {meta_redirects}")
            print(f"   Final URL: {row['final_url'][:75]}")

        if row['is_live']:
            indicators = str(row.get('indicators_found', ''))
            if indicators and indicators != 'nan' and len(indicators) > 0:
                print(f"   Indicators: {indicators}")
            print(f"   Response: {row['response_time_ms']:.0f}ms")
        else:
            print(f"   Error: {row.get('error_message', 'Unknown')}")

# Show MEDIUM scorers
medium = df[df['likelihood'] == 'MEDIUM'].sort_values('total_score', ascending=False)
if len(medium) > 0:
    print(f"\n{'=' * 80}")
    print(f"MEDIUM SCORERS: {len(medium)} sites")
    print(f"{'=' * 80}")

    for idx, (_, row) in enumerate(medium.iterrows(), 1):
        entity = str(row.get('primary_entity_long')) if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))
        status = "✅ LIVE" if row['is_live'] else "❌ FAILED"
        score = row['total_score']
        meta_redirects = row.get('meta_redirects', 0)

        print(f"\n{idx}. {entity[:60]}")
        print(f"   URL: {row['url'][:75]}")
        print(f"   Status: {status} | Score: {score} (base:{row['base_score']:.0f} + bonus:{row['title_bonus']:.0f})")

        if meta_redirects > 0:
            print(f"   🔀 Meta redirects: {meta_redirects}")
            print(f"   Final URL: {row['final_url'][:75]}")

        if row['is_live']:
            indicators = str(row.get('indicators_found', ''))
            if indicators and indicators != 'nan' and len(indicators) > 0:
                ind_list = [i.strip() for i in indicators.split(';')]
                print(f"   Indicators ({len(ind_list)}): {'; '.join(ind_list[:6])}...")
            print(f"   Response: {row['response_time_ms']:.0f}ms")

print(f"\n{'=' * 80}")
print("SUMMARY:")
print(f"   VERY LOW: {len(very_low)} ({len(very_low)/len(df)*100:.1f}%)")
print(f"   LOW: {len(low)} ({len(low)/len(df)*100:.1f}%)")
print(f"   MEDIUM: {len(medium)} ({len(medium)/len(df)*100:.1f}%)")
print(f"   Total low/medium: {len(very_low) + len(low) + len(medium)} ({(len(very_low) + len(low) + len(medium))/len(df)*100:.1f}%)")

# Compare to V2
print(f"\n{'=' * 80}")
print("IMPROVEMENT FROM V2:")
v2 = pd.read_csv('data/dedup_results_v2.csv')
v2_low_total = len(v2[v2['likelihood'].isin(['VERY LOW', 'LOW', 'MEDIUM'])])
v3_low_total = len(df[df['likelihood'].isin(['VERY LOW', 'LOW', 'MEDIUM'])])
print(f"   V2 low/medium scorers: {v2_low_total} ({v2_low_total/len(v2)*100:.1f}%)")
print(f"   V3 low/medium scorers: {v3_low_total} ({v3_low_total/len(df)*100:.1f}%)")
print(f"   Improvement: {v2_low_total - v3_low_total} fewer low scorers")
print(f"{'=' * 80}")
