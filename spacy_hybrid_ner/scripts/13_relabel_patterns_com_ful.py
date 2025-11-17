#!/usr/bin/env python3
"""
Relabel EntityRuler patterns from BIO_RESOURCE to COM/FUL labels.

This fixes the label index misalignment in the hybrid NER pipeline.

Input:  spacy_hybrid_ner/data/patterns.jsonl (BIO_RESOURCE labels)
Output: spacy_hybrid_ner/data/patterns_com_ful.jsonl (COM/FUL labels)
        spacy_hybrid_ner/data/relabeling_stats.json (statistics)
        spacy_hybrid_ner/data/relabeling_report.txt (human-readable)
"""

import json
import re
from pathlib import Path
from collections import Counter

# Paths
PATTERNS_INPUT = Path("spacy_hybrid_ner/data/patterns.jsonl")
DICTIONARY_PATH = Path("spacy_hybrid_ner/data/bioresource_dictionary_enriched.json")
PATTERNS_OUTPUT = Path("spacy_hybrid_ner/data/patterns_com_ful.jsonl")
STATS_OUTPUT = Path("spacy_hybrid_ner/data/relabeling_stats.json")
REPORT_OUTPUT = Path("spacy_hybrid_ner/data/relabeling_report.txt")


def extract_pattern_text(pattern) -> str:
    """Extract text from pattern (handles both string and token patterns)."""
    if isinstance(pattern, str):
        return pattern
    elif isinstance(pattern, list):
        # Token-based pattern: [{"TEXT": "PDB"}]
        tokens = []
        for token_dict in pattern:
            if 'TEXT' in token_dict:
                tokens.append(token_dict['TEXT'])
            elif 'LOWER' in token_dict:
                tokens.append(token_dict['LOWER'])
        return ' '.join(tokens) if tokens else ''
    else:
        return str(pattern)


def classify_pattern(pattern_text: str, pattern_obj: dict, dictionary: dict) -> tuple:
    """
    Classify a pattern as COM or FUL.

    Args:
        pattern_text: String representation of pattern
        pattern_obj: Full pattern object (contains 'id' and 'pattern' fields)
        dictionary: Full dictionary from bioresource_dictionary_enriched.json

    Returns:
        (label, confidence) where label is 'COM' or 'FUL' and confidence is 0-1
    """
    # 1. Dictionary lookup using the pattern's own resource ID (highest confidence)
    resource_id = pattern_obj.get('id', '')
    if resource_id in dictionary:
        resource_info = dictionary[resource_id]
        short_name = resource_info.get('short_name', '')
        full_name = resource_info.get('full_name', '')

        # Check if pattern matches this resource's names
        if pattern_text == short_name:
            return ('COM', 1.0)
        elif pattern_text == full_name:
            return ('FUL', 1.0)

    # 2. Token-based pattern (very high confidence for COM)
    if isinstance(pattern_obj.get('pattern'), list):
        return ('COM', 0.95)

    # 3. Orthographic features
    words = pattern_text.split()

    # All caps single word
    if len(words) == 1 and pattern_text.isupper() and len(pattern_text) <= 10:
        return ('COM', 0.90)

    # CamelCase or mixed case single word
    if len(words) == 1 and len(pattern_text) <= 20:
        if any(c.isupper() for c in pattern_text[1:]):  # Has internal caps
            return ('COM', 0.85)

    # Multiple words with title case
    if len(words) >= 3:
        return ('FUL', 0.85)

    # 4. Length heuristic
    if len(pattern_text) <= 10:
        return ('COM', 0.75)
    elif len(pattern_text) <= 15:
        return ('COM', 0.65)  # Less confident
    elif len(pattern_text) > 25:
        return ('FUL', 0.85)

    # 5. Default based on word count
    if len(words) == 1:
        return ('COM', 0.60)  # Low confidence
    else:
        return ('FUL', 0.70)


def relabel_patterns(input_path: Path, dict_path: Path, output_path: Path):
    """Main relabeling function."""
    print("="*70)
    print("RELABELING ENTITYRULER PATTERNS: BIO_RESOURCE → COM/FUL")
    print("="*70)

    # Load dictionary
    print(f"\nLoading dictionary from: {dict_path}")
    with open(dict_path) as f:
        dictionary = json.load(f)
    print(f"  Resources in dictionary: {len(dictionary):,}")

    # Load patterns
    print(f"\nLoading patterns from: {input_path}")
    patterns = []
    with open(input_path) as f:
        for line in f:
            patterns.append(json.loads(line))
    print(f"  Loaded {len(patterns):,} patterns")

    # Classify and relabel
    print("\nClassifying patterns...")
    stats = {
        'total': len(patterns),
        'COM': 0,
        'FUL': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0,
        'manual_review': []
    }

    relabeled = []
    confidence_threshold = 0.80

    for p in patterns:
        pattern_text = extract_pattern_text(p['pattern'])

        # Classify
        label, confidence = classify_pattern(pattern_text, p, dictionary)

        # Update stats
        stats[label] += 1
        if confidence >= 0.90:
            stats['high_confidence'] += 1
        elif confidence >= 0.75:
            stats['medium_confidence'] += 1
        else:
            stats['low_confidence'] += 1

        # Flag for manual review if low confidence
        if confidence < confidence_threshold:
            stats['manual_review'].append({
                'pattern': pattern_text,
                'suggested_label': label,
                'confidence': confidence,
                'canonical_id': p.get('id', 'N/A')
            })

        # Update pattern
        p['label'] = label
        relabeled.append(p)

    # Save relabeled patterns
    print(f"\nSaving relabeled patterns to: {output_path}")
    with open(output_path, 'w') as f:
        for p in relabeled:
            f.write(json.dumps(p) + '\n')

    print(f"  ✓ Saved {len(relabeled):,} patterns")

    return stats, relabeled


def generate_report(stats: dict, report_path: Path):
    """Generate human-readable report."""
    report = []
    report.append("="*70)
    report.append("ENTITYRULER PATTERN RELABELING REPORT")
    report.append("="*70)
    report.append("")
    report.append("SUMMARY")
    report.append("-"*70)
    report.append(f"Total patterns:     {stats['total']:,}")
    report.append(f"COM (short) labels: {stats['COM']:,} ({stats['COM']/stats['total']*100:.1f}%)")
    report.append(f"FUL (full) labels:  {stats['FUL']:,} ({stats['FUL']/stats['total']*100:.1f}%)")
    report.append("")
    report.append("CONFIDENCE DISTRIBUTION")
    report.append("-"*70)
    report.append(f"High confidence (≥90%):   {stats['high_confidence']:,} ({stats['high_confidence']/stats['total']*100:.1f}%)")
    report.append(f"Medium confidence (75-90%): {stats['medium_confidence']:,} ({stats['medium_confidence']/stats['total']*100:.1f}%)")
    report.append(f"Low confidence (<75%):    {stats['low_confidence']:,} ({stats['low_confidence']/stats['total']*100:.1f}%)")
    report.append("")
    report.append("MANUAL REVIEW NEEDED")
    report.append("-"*70)
    report.append(f"Cases flagged: {len(stats['manual_review'])}")

    if stats['manual_review']:
        report.append("")
        report.append("Top 20 cases for review:")
        report.append("")
        for i, case in enumerate(sorted(stats['manual_review'], key=lambda x: x['confidence'])[:20], 1):
            report.append(f"{i:2d}. '{case['pattern']}' → {case['suggested_label']} (conf={case['confidence']:.2f}, id={case['canonical_id']})")

    report.append("")
    report.append("="*70)

    # Save report
    with open(report_path, 'w') as f:
        f.write('\n'.join(report))

    # Also print to console
    print('\n'.join(report))


def main():
    """Main execution."""
    # Relabel patterns
    stats, relabeled = relabel_patterns(PATTERNS_INPUT, DICTIONARY_PATH, PATTERNS_OUTPUT)

    # Save statistics
    print(f"\nSaving statistics to: {STATS_OUTPUT}")
    with open(STATS_OUTPUT, 'w') as f:
        json.dump(stats, f, indent=2)

    # Generate report
    print(f"\nGenerating report: {REPORT_OUTPUT}")
    generate_report(stats, REPORT_OUTPUT)

    print("\n" + "="*70)
    print("✓ RELABELING COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Review manual_review cases in relabeling_stats.json")
    print("  2. Apply corrections if needed")
    print("  3. Validate label distribution")
    print("  4. Rebuild hybrid pipeline")
    print("="*70)


if __name__ == "__main__":
    main()
