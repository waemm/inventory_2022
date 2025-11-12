#!/usr/bin/env python3
"""
Enrich Missing Full Names (Phase 1.2)

Uses pattern matching on paper titles/abstracts to extract full names
for resources that only have short names.

Input:
    - data/bioresource_dictionary_raw.json
    - /Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv

Output:
    - data/bioresource_dictionary_enriched.json
    - data/enrichment_review.csv (ambiguous cases for manual review)

Target: 70-80% coverage (up from ~40%)
"""

import pandas as pd
import json
import re
from collections import Counter
from pathlib import Path
import sys


# Configuration
INPUT_DICT = 'data/bioresource_dictionary_raw.json'
INPUT_CSV = '/Users/warren/development/GBC/gbc-publication-analysis/bioresource_papers_latest.csv'
OUTPUT_DICT = 'data/bioresource_dictionary_enriched.json'
OUTPUT_REVIEW = 'data/enrichment_review.csv'


def create_patterns(short_name):
    """
    Create regex patterns to find full names for a short name.

    Args:
        short_name: Short name/acronym to search for

    Returns:
        list: List of compiled regex patterns
    """
    # Escape special regex characters
    short_escaped = re.escape(short_name)

    # Pattern templates (non-greedy with word boundaries)
    pattern_templates = [
        # "Full Name (SHORT)" - Non-greedy, starts with capital letter
        r'\b([A-Z][\w\s\-]+?)\s+\(' + short_escaped + r'\)',

        # "SHORT (Full Name)" - Non-greedy
        short_escaped + r'\s+\(([\w\s\-]+?)\)',

        # "the Full Name database ... SHORT" - Non-greedy with stricter context
        r'(?:the|a|an)\s+([\w\s\-]+?)\s+(?:database|resource|tool|platform|repository|collection|archive|portal)\b[^.]{0,50}?\b' + short_escaped + r'\b',

        # "SHORT is a Full Name database" - Non-greedy
        r'\b' + short_escaped + r'\b\s+is\s+(?:a|an)\s+([\w\s\-]+?)\s+(?:database|resource|tool|platform|repository)',

        # At start of sentence: "SHORT: Full Name" - Sentence-aware
        r'(?:^|\.\s+)' + short_escaped + r':\s+([\w\s\-]+?)(?:\.|,)',
    ]

    # Compile patterns
    patterns = []
    for template in pattern_templates:
        try:
            patterns.append(re.compile(template, re.IGNORECASE | re.MULTILINE))
        except re.error as e:
            print(f"⚠️  Warning: Failed to compile pattern for '{short_name}': {e}")

    return patterns


def extract_candidates(text, patterns):
    """
    Extract candidate full names from text using patterns.

    Args:
        text: Text to search (title + abstract)
        patterns: List of compiled regex patterns

    Returns:
        list: List of candidate full names
    """
    candidates = []

    # Common words that are not valid full names
    STOPWORDS = {'the', 'a', 'an', 'database', 'resource', 'tool', 'platform',
                 'repository', 'collection', 'archive', 'portal', 'website'}

    for pattern in patterns:
        matches = pattern.findall(text)
        for match in matches:
            # Clean up the match
            candidate = match.strip()

            # Enhanced filtering
            word_count = len(candidate.split())

            # Require at least 2 words for full names
            if word_count < 2:
                continue

            # Length checks
            if len(candidate) < 5:  # Stricter minimum length
                continue
            if word_count > 10:  # Too long (probably caught too much)
                continue

            # Check if it's just a stopword
            if candidate.lower() in STOPWORDS:
                continue

            candidates.append(candidate)

    return candidates


def enrich_dictionary(dictionary, df):
    """
    Enrich dictionary with full names extracted from papers.

    Args:
        dictionary: Dictionary from Phase 1.1
        df: DataFrame with paper text

    Returns:
        tuple: (enriched_dictionary, ambiguous_cases)
    """
    enriched_count = 0
    skipped_count = 0
    ambiguous_cases = []

    # Get resources missing full names
    missing_full = [
        (rid, data) for rid, data in dictionary.items()
        if not data['full_name']
    ]

    print(f"\n🔄 Processing {len(missing_full)} resources without full names...")

    for i, (resource_id, data) in enumerate(missing_full, 1):
        short_name = data['short_name']
        pmids = data['pmids']

        if i % 100 == 0:
            print(f"  Progress: {i}/{len(missing_full)} ({i/len(missing_full)*100:.1f}%)")

        # Create patterns for this short name
        patterns = create_patterns(short_name)

        # Get papers with this resource
        # Convert PMIDs to int to match CSV column type
        try:
            pmids_int = [int(p) for p in pmids if p]
        except (ValueError, TypeError):
            skipped_count += 1
            continue

        papers = df[df['pubmed_id'].isin(pmids_int)]

        if len(papers) == 0:
            skipped_count += 1
            continue

        # Extract candidates from all papers
        all_candidates = []
        for _, paper in papers.iterrows():
            # Handle title
            title = paper.get('title', '')
            if pd.isna(title):
                title = ''
            else:
                title = str(title)

            # Handle abstract (column may not exist)
            abstract = paper.get('abstract', '')
            if pd.isna(abstract) or abstract is None:
                abstract = ''
            else:
                abstract = str(abstract)

            # Combine text (only title if no abstract)
            text = f"{title} {abstract}".strip()

            if not text:
                continue

            candidates = extract_candidates(text, patterns)
            all_candidates.extend(candidates)

        if not all_candidates:
            skipped_count += 1
            continue

        # Find consensus (most frequent match)
        candidate_counts = Counter(all_candidates)
        most_common = candidate_counts.most_common()

        # Take the most frequent candidate
        best_candidate, best_count = most_common[0]

        # Check if ambiguous (multiple strong candidates)
        is_ambiguous = False
        if len(most_common) > 1:
            second_count = most_common[1][1]
            # Ambiguous if second candidate has >30% of top frequency
            if second_count / best_count > 0.3:
                is_ambiguous = True

        if is_ambiguous:
            # Record for manual review
            ambiguous_cases.append({
                'resource_id': resource_id,
                'short_name': short_name,
                'top_candidate': best_candidate,
                'top_count': best_count,
                'alternatives': str(most_common[:3])
            })

        # Update dictionary
        dictionary[resource_id]['full_name'] = best_candidate
        dictionary[resource_id]['enriched'] = True
        dictionary[resource_id]['enrichment_confidence'] = 'ambiguous' if is_ambiguous else 'high'
        dictionary[resource_id]['candidate_count'] = len(all_candidates)
        enriched_count += 1

    print(f"\n✓ Enrichment complete!")
    print(f"  Enriched: {enriched_count}")
    print(f"  Ambiguous: {len(ambiguous_cases)}")
    print(f"  Skipped (no candidates): {skipped_count}")

    return dictionary, ambiguous_cases


def print_statistics(dictionary):
    """Print before/after statistics."""
    total = len(dictionary)
    with_full = sum(1 for v in dictionary.values() if v['full_name'])
    enriched = sum(1 for v in dictionary.values() if v.get('enriched', False))

    print("\n" + "="*60)
    print("ENRICHMENT RESULTS")
    print("="*60)
    print(f"\nTotal resources: {total}")
    print(f"With full names: {with_full} ({with_full/total*100:.1f}%)")
    print(f"  - Original: {with_full - enriched}")
    print(f"  - Enriched: {enriched}")
    print(f"\nCoverage improvement: {enriched/total*100:.1f} percentage points")
    print("="*60 + "\n")


def main():
    """Main execution function."""
    print("="*60)
    print("Phase 1.2: Enrich Missing Full Names")
    print("="*60)

    # Load dictionary from Phase 1.1
    print(f"\n📖 Loading dictionary from: {INPUT_DICT}")
    if not Path(INPUT_DICT).exists():
        print(f"❌ ERROR: Dictionary not found. Run 01_extract_bioresource_dictionary.py first.")
        sys.exit(1)

    with open(INPUT_DICT, 'r', encoding='utf-8') as f:
        dictionary = json.load(f)
    print(f"✓ Loaded {len(dictionary)} resources")

    # Load CSV
    print(f"\n📖 Loading papers from: {INPUT_CSV}")
    if not Path(INPUT_CSV).exists():
        print(f"❌ ERROR: CSV file not found: {INPUT_CSV}")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    print(f"✓ Loaded {len(df)} papers")

    # Enrich dictionary
    dictionary, ambiguous_cases = enrich_dictionary(dictionary, df)

    # Print statistics
    print_statistics(dictionary)

    # Save enriched dictionary
    Path(OUTPUT_DICT).parent.mkdir(parents=True, exist_ok=True)
    print(f"💾 Saving enriched dictionary to: {OUTPUT_DICT}")
    with open(OUTPUT_DICT, 'w', encoding='utf-8') as f:
        json.dump(dictionary, f, indent=2, ensure_ascii=False)
    print("✓ Dictionary saved!")

    # Save ambiguous cases for manual review
    if ambiguous_cases:
        print(f"\n⚠️  Saving {len(ambiguous_cases)} ambiguous cases for review: {OUTPUT_REVIEW}")
        pd.DataFrame(ambiguous_cases).to_csv(OUTPUT_REVIEW, index=False)
        print("✓ Review file saved!")
        print("\nRecommendation: Manually review ambiguous cases and update dictionary if needed.")

    print(f"\n📊 Next step: Run 03_generate_patterns_jsonl.py to create EntityRuler patterns")

    return 0


if __name__ == "__main__":
    sys.exit(main())
