#!/usr/bin/env python3
"""
Review fuzzy matches and determine which are true matches vs false positives.
"""

import pandas as pd
import re
from difflib import SequenceMatcher

def normalize_name(name):
    """Normalize database name for comparison."""
    if pd.isna(name):
        return ""
    return str(name).lower().strip()

def is_version_difference(extracted, baseline):
    """Check if the difference is just a version number."""
    # Remove common suffixes
    extracted_base = re.sub(r'[0-9]+$', '', extracted.lower())
    baseline_base = re.sub(r'[0-9]+$', '', baseline.lower())

    # If bases are identical, it's a version difference
    if extracted_base == baseline_base and extracted_base:
        return True

    return False

def is_db_suffix_difference(extracted, baseline):
    """Check if difference is just db/database/base suffix."""
    suffixes = ['db', 'database', 'base']

    extracted_lower = extracted.lower()
    baseline_lower = baseline.lower()

    # Remove suffixes and compare
    for suffix in suffixes:
        extracted_clean = re.sub(f'{suffix}$', '', extracted_lower)
        baseline_clean = re.sub(f'{suffix}$', '', baseline_lower)

        if extracted_clean == baseline_clean and extracted_clean:
            return True

    return False

def is_acronym_match(extracted, baseline, extracted_long, baseline_full):
    """Check if it's a legitimate acronym match."""
    # If edit distance is 1-2 and they're both short acronyms
    # but the long forms are very different, it's likely a false match

    if len(extracted) <= 5 and len(baseline) <= 5:
        # Both are acronyms - check long forms
        if extracted_long and baseline_full:
            long_sim = SequenceMatcher(None,
                                      extracted_long.lower(),
                                      baseline_full.lower()).ratio()
            if long_sim < 0.7:  # Long forms are quite different
                return False

    return True

def is_substring_only(extracted, baseline):
    """Check if it's just a common substring match."""
    common_substrings = ['map', 'db', 'bio', 'gen', 'pro', 'data', 'base']

    extracted_lower = extracted.lower()
    baseline_lower = baseline.lower()

    # If the shorter one is just a common substring in the longer
    if len(extracted_lower) <= 3 or len(baseline_lower) <= 3:
        shorter = extracted_lower if len(extracted_lower) < len(baseline_lower) else baseline_lower
        if shorter in common_substrings:
            return True

    return False

def check_legitimate_expansion(extracted, baseline, extracted_long, baseline_full):
    """Check if extracted is a legitimate longer form of baseline."""
    extracted_lower = extracted.lower()
    baseline_lower = baseline.lower()

    # Case 1: baseline is contained in extracted (e.g., GOA in UniProt-GOA)
    if baseline_lower in extracted_lower and len(baseline_lower) >= 3:
        # Make sure it's not just a substring coincidence
        if not is_substring_only(extracted, baseline):
            # Check if long forms also align
            if extracted_long and baseline_full:
                long_sim = SequenceMatcher(None,
                                          extracted_long.lower(),
                                          baseline_full.lower()).ratio()
                if long_sim > 0.6:
                    return True
            else:
                # No long form to verify, but short form looks good
                return True

    return False

def review_match(row):
    """Review a single match and determine if it's true or false."""
    extracted = normalize_name(row['extracted_name'])
    baseline = normalize_name(row['baseline_name'])
    extracted_long = str(row['extracted_long']) if pd.notna(row['extracted_long']) else ""
    baseline_full = str(row['baseline_full']) if pd.notna(row['baseline_full']) else ""

    edit_distance = row['edit_distance']
    confidence = row['confidence']
    contains = row['contains']
    long_sim = row['long_sim']

    # HIGH confidence matches (edit_dist <= 2)
    if confidence == 'HIGH':
        # Version difference - TRUE
        if is_version_difference(extracted, baseline):
            return 'Y', f"Version difference: {extracted} vs {baseline}"

        # DB suffix difference - TRUE
        if is_db_suffix_difference(extracted, baseline):
            return 'Y', f"DB suffix difference: {extracted} vs {baseline}"

        # Check if it's a false acronym match
        if not is_acronym_match(extracted, baseline, extracted_long, baseline_full):
            return 'N', f"Different databases with similar acronyms (long_sim={long_sim:.2f})"

        # If long form similarity is very high (>0.85), it's likely the same
        if long_sim and long_sim > 0.85:
            return 'Y', f"High long form similarity ({long_sim:.2f})"

        # If long form similarity is low (<0.75) and they're different acronyms
        if long_sim and long_sim < 0.75:
            return 'N', f"Low long form similarity ({long_sim:.2f}), likely different databases"

        # Medium similarity - need to check more carefully
        if long_sim and 0.75 <= long_sim <= 0.85:
            # If names are very similar (edit dist 1) and contains is True
            if edit_distance == 1 and contains:
                return 'Y', f"Edit distance 1 with contains match, long_sim={long_sim:.2f}"
            else:
                return 'N', f"Borderline case with long_sim={long_sim:.2f}, likely different"

        # Default for HIGH without long_sim data
        if edit_distance == 1:
            return 'Y', f"Edit distance 1, assumed version/variant"
        else:
            return 'N', f"Edit distance {edit_distance}, uncertain match"

    # MEDIUM confidence (contains)
    elif confidence == 'MEDIUM':
        # Check if it's a legitimate expansion
        if check_legitimate_expansion(extracted, baseline, extracted_long, baseline_full):
            return 'Y', f"Legitimate expansion: {extracted} contains {baseline}"

        # Check if it's just a common substring
        if is_substring_only(extracted, baseline):
            return 'N', f"Common substring match only"

        # If long form similarity is high, might be related
        if long_sim and long_sim > 0.8:
            return 'Y', f"Contains match with high long_sim={long_sim:.2f}"

        # Default for contains-only matches
        return 'N', f"Substring match, likely different databases"

    # LOW confidence
    else:
        return 'N', f"Low confidence match"

def main():
    # Read the fuzzy match file
    df = pd.read_csv('/Users/warren/development/GBC/inventory_2022/false_positive_analysis/fuzzy_match_review.csv')

    print(f"Total matches to review: {len(df)}")
    print(f"\nConfidence breakdown:")
    print(df['confidence'].value_counts())

    # Review each match
    results = []
    for idx, row in df.iterrows():
        is_match, reasoning = review_match(row)
        results.append({
            'is_match': is_match,
            'reasoning': reasoning
        })

    # Add results to dataframe
    results_df = pd.DataFrame(results)
    df['is_match'] = results_df['is_match']
    df['reasoning'] = results_df['reasoning']

    # Save reviewed file
    output_path = '/Users/warren/development/GBC/inventory_2022/false_positive_analysis/fuzzy_match_reviewed.csv'
    df.to_csv(output_path, index=False)
    print(f"\nSaved reviewed matches to: {output_path}")

    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    true_matches = df[df['is_match'] == 'Y']
    false_positives = df[df['is_match'] == 'N']

    print(f"\nTotal matches analyzed: {len(df)}")
    print(f"TRUE matches (should be filtered): {len(true_matches)} ({len(true_matches)/len(df)*100:.1f}%)")
    print(f"FALSE positives (keep as novel): {len(false_positives)} ({len(false_positives)/len(df)*100:.1f}%)")

    print("\n\nBreakdown by confidence level:")
    for conf in ['HIGH', 'MEDIUM', 'LOW']:
        conf_df = df[df['confidence'] == conf]
        if len(conf_df) > 0:
            true_count = len(conf_df[conf_df['is_match'] == 'Y'])
            print(f"\n{conf} confidence:")
            print(f"  Total: {len(conf_df)}")
            print(f"  TRUE: {true_count} ({true_count/len(conf_df)*100:.1f}%)")
            print(f"  FALSE: {len(conf_df) - true_count} ({(len(conf_df)-true_count)/len(conf_df)*100:.1f}%)")

    # Top 20 confirmed TRUE matches
    print("\n" + "="*80)
    print("TOP 20 CONFIRMED TRUE MATCHES (to filter from novel dataset)")
    print("="*80)

    true_high_conf = true_matches[true_matches['confidence'] == 'HIGH'].head(20)
    print("\nExtracted Name | Baseline Name | Edit Dist | Long Sim | Reasoning")
    print("-" * 120)
    for _, row in true_high_conf.iterrows():
        print(f"{row['extracted_name']:20s} | {row['baseline_name']:20s} | {row['edit_distance']:9d} | {row['long_sim']:8.2f} | {row['reasoning'][:50]}")

    # Export list of extracted names to filter
    true_match_names = true_matches['extracted_name'].unique().tolist()
    filter_list_path = '/Users/warren/development/GBC/inventory_2022/false_positive_analysis/true_matches_to_filter.txt'
    with open(filter_list_path, 'w') as f:
        f.write('\n'.join(sorted(true_match_names)))

    print(f"\n\nList of {len(true_match_names)} unique extracted names to filter saved to:")
    print(filter_list_path)

    # Save summary stats
    summary_path = '/Users/warren/development/GBC/inventory_2022/false_positive_analysis/fuzzy_match_review_summary.txt'
    with open(summary_path, 'w') as f:
        f.write("FUZZY MATCH REVIEW SUMMARY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total matches analyzed: {len(df)}\n")
        f.write(f"TRUE matches (to filter): {len(true_matches)} ({len(true_matches)/len(df)*100:.1f}%)\n")
        f.write(f"FALSE positives (keep as novel): {len(false_positives)} ({len(false_positives)/len(df)*100:.1f}%)\n\n")

        f.write("Breakdown by confidence level:\n")
        for conf in ['HIGH', 'MEDIUM', 'LOW']:
            conf_df = df[df['confidence'] == conf]
            if len(conf_df) > 0:
                true_count = len(conf_df[conf_df['is_match'] == 'Y'])
                f.write(f"\n{conf} confidence:\n")
                f.write(f"  Total: {len(conf_df)}\n")
                f.write(f"  TRUE: {true_count} ({true_count/len(conf_df)*100:.1f}%)\n")
                f.write(f"  FALSE: {len(conf_df) - true_count} ({(len(conf_df)-true_count)/len(conf_df)*100:.1f}%)\n")

    print(f"\nSummary saved to: {summary_path}")

if __name__ == '__main__':
    main()
