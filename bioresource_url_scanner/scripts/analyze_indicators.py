#!/usr/bin/env python3
"""
analyze_indicators.py - Analyze which indicators are most commonly detected
"""

import pandas as pd
from collections import Counter

df = pd.read_csv('data/dedup_results_v2.csv')
live_with_score = df[(df['is_live'] == True) & (df['total_score'] > 0)]

print('=' * 80)
print(f'MOST COMMON INDICATORS IN V2 ({len(live_with_score)} live sites with score > 0)')
print('=' * 80)

# Parse all indicators
all_indicators = []
for _, row in live_with_score.iterrows():
    indicators = str(row.get('indicators_found', ''))
    if indicators and indicators != 'nan':
        parts = [i.strip() for i in indicators.split(';')]
        all_indicators.extend(parts)

# Count them
counter = Counter(all_indicators)

print('\nTop 30 Most Detected Indicators:')
for indicator, count in counter.most_common(30):
    pct = count / len(live_with_score) * 100
    print(f'{count:3d} ({pct:5.1f}%) | {indicator}')

# Count title bonuses
title_bonus_count = sum(1 for ind in all_indicators if 'TITLE BONUS' in ind)
print(f'\n✨ TITLE BONUS awarded to {title_bonus_count}/{len(live_with_score)} sites ({title_bonus_count/len(live_with_score)*100:.1f}%)')

# Count content vs title detections
content_count = sum(1 for ind in all_indicators if ind.startswith('Content:'))
title_count = sum(1 for ind in all_indicators if ind.startswith('Title:'))
print(f'\n📊 Detection Location:')
print(f'   Content detections: {content_count}')
print(f'   Title detections: {title_count}')
print(f'   Title bonus detections: {title_bonus_count}')
