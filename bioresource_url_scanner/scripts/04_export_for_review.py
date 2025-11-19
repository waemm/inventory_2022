#!/usr/bin/env python3
"""
04_export_for_review.py - Export URLs for Manual Review

Exports curated sample for human validation:
- Top 10: Highest scores (should be bioresources)
- Bottom 10: Lowest scores (should NOT be bioresources)
- Middle 10: Medium scores (ambiguous cases)

Author: Warren
Date: 2025-11-19
"""

import pandas as pd
from pathlib import Path
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure results directory exists
RESULTS_DIR.mkdir(exist_ok=True)


def load_results():
    """Load scan results"""
    results_path = DATA_DIR / "pilot_results.csv"

    if not results_path.exists():
        print(f"❌ Results file not found: {results_path}")
        print("   Run 02_scan_urls.py first")
        sys.exit(1)

    df = pd.read_csv(results_path)
    return df


def extract_page_title(row):
    """Extract page title from title_indicators or construct from URL"""
    # This is a placeholder - in real implementation we'd store page title
    # For now, use primary_entity as proxy
    if pd.notna(row.get('primary_entity_long')):
        return row['primary_entity_long']
    elif pd.notna(row.get('primary_entity_short')):
        return row['primary_entity_short']
    else:
        return row['url'].split('/')[-1][:50]


def create_content_snippet(row):
    """Create a content snippet from indicators"""
    indicators = []

    if pd.notna(row.get('title_indicators')) and row['title_indicators'] != '':
        indicators.append(f"Title: {row['title_indicators']}")

    if pd.notna(row.get('url_indicators')) and row['url_indicators'] != '':
        indicators.append(f"URL: {row['url_indicators']}")

    if pd.notna(row.get('content_indicators')) and row['content_indicators'] != '':
        content = row['content_indicators']
        # Limit content indicators to first 100 chars
        if len(content) > 100:
            content = content[:100] + "..."
        indicators.append(f"Content: {content}")

    if indicators:
        return " | ".join(indicators)
    else:
        return "(No indicators found)"


def main():
    """Main export workflow"""
    print("=" * 70)
    print("Bioresource URL Scanner - Manual Review Export")
    print("=" * 70)

    # Load results
    df = load_results()
    print(f"\n📂 Loaded results: {len(df)} URLs")

    # Filter to live URLs only (can't review dead links)
    live_df = df[df['is_live'] == True].copy()
    print(f"   Live URLs: {len(live_df)}")

    if len(live_df) < 30:
        print(f"\n⚠️  Warning: Only {len(live_df)} live URLs (need 30 for full sample)")
        print(f"   Will export all available live URLs")

    # Sort by score
    live_df = live_df.sort_values('total_score', ascending=False)

    # Select samples
    n_top = min(10, len(live_df))
    n_bottom = min(10, len(live_df) - n_top)
    n_middle = min(10, len(live_df) - n_top - n_bottom)

    samples = []

    # Top 10 (highest scores)
    if n_top > 0:
        top_sample = live_df.head(n_top).copy()
        top_sample['review_category'] = 'HIGH_SCORE'
        samples.append(top_sample)
        print(f"\n📊 Top {n_top} URLs (highest scores):")
        for idx, row in top_sample.iterrows():
            print(f"   {row['total_score']:2.0f} | {row['likelihood']:10s} | {row['url'][:50]}...")

    # Bottom 10 (lowest scores)
    if n_bottom > 0:
        bottom_sample = live_df.tail(n_bottom).copy()
        bottom_sample['review_category'] = 'LOW_SCORE'
        samples.append(bottom_sample)
        print(f"\n📊 Bottom {n_bottom} URLs (lowest scores):")
        for idx, row in bottom_sample.tail(5).iterrows():  # Show last 5
            print(f"   {row['total_score']:2.0f} | {row['likelihood']:10s} | {row['url'][:50]}...")

    # Middle 10 (medium scores)
    if n_middle > 0:
        # Get middle section
        start_idx = n_top
        end_idx = len(live_df) - n_bottom
        middle_section = live_df.iloc[start_idx:end_idx]

        if len(middle_section) > 0:
            # Sample from middle
            if len(middle_section) <= n_middle:
                middle_sample = middle_section.copy()
            else:
                # Evenly spaced sampling
                indices = [int(i * len(middle_section) / n_middle) for i in range(n_middle)]
                middle_sample = middle_section.iloc[indices].copy()

            middle_sample['review_category'] = 'MEDIUM_SCORE'
            samples.append(middle_sample)
            print(f"\n📊 Middle {len(middle_sample)} URLs (medium scores):")
            for idx, row in middle_sample.head(5).iterrows():  # Show first 5
                print(f"   {row['total_score']:2.0f} | {row['likelihood']:10s} | {row['url'][:50]}...")

    # Combine all samples
    if not samples:
        print(f"\n❌ No live URLs to export")
        sys.exit(1)

    review_df = pd.concat(samples, ignore_index=True)

    # Create review columns
    review_df['page_title'] = review_df.apply(extract_page_title, axis=1)
    review_df['content_snippet'] = review_df.apply(create_content_snippet, axis=1)
    review_df['manual_label'] = ''  # Empty for human to fill
    review_df['manual_notes'] = ''  # Empty for human to fill

    # Select columns for export
    export_cols = [
        'url',
        'review_category',
        'total_score',
        'likelihood',
        'indicators_found',
        'page_title',
        'content_snippet',
        'primary_entity_long',
        'primary_entity_short',
        'source_file',
        'manual_label',
        'manual_notes',
    ]

    # Only include columns that exist
    available_cols = [col for col in export_cols if col in review_df.columns]
    export_df = review_df[available_cols]

    # Save
    output_path = RESULTS_DIR / "manual_review.csv"
    export_df.to_csv(output_path, index=False)

    print(f"\n✅ Manual Review Export Complete!")
    print(f"   Total URLs: {len(export_df)}")
    print(f"   - High score: {(export_df['review_category'] == 'HIGH_SCORE').sum()}")
    print(f"   - Medium score: {(export_df['review_category'] == 'MEDIUM_SCORE').sum()}")
    print(f"   - Low score: {(export_df['review_category'] == 'LOW_SCORE').sum()}")

    print(f"\n💾 Saved to: {output_path}")
    print(f"   Columns: {', '.join(export_df.columns)}")

    print(f"\n📋 Instructions for Manual Review:")
    print(f"   1. Open: {output_path}")
    print(f"   2. For each URL, fill in 'manual_label' column:")
    print(f"      - YES: This is a genuine bioresource")
    print(f"      - NO: This is NOT a bioresource")
    print(f"      - UNSURE: Cannot determine")
    print(f"   3. Add notes in 'manual_notes' if needed")
    print(f"   4. Focus on HIGH_SCORE and LOW_SCORE categories first")
    print("=" * 70)


if __name__ == "__main__":
    main()
