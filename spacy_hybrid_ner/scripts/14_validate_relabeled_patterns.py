#!/usr/bin/env python3
"""Validate the relabeled patterns."""

import json
from pathlib import Path
from collections import Counter

PATTERNS_FILE = Path("spacy_hybrid_ner/data/patterns_com_ful.jsonl")

def validate_patterns():
    """Validate the relabeled patterns."""
    print("="*70)
    print("VALIDATING RELABELED PATTERNS")
    print("="*70)

    # Load patterns
    patterns = []
    with open(PATTERNS_FILE) as f:
        for line in f:
            patterns.append(json.loads(line))

    print(f"\nTotal patterns: {len(patterns):,}")

    # Check 1: Only COM/FUL labels
    labels = Counter(p['label'] for p in patterns)
    print(f"\nLabel distribution:")
    for label, count in labels.most_common():
        print(f"  {label}: {count:,} ({count/len(patterns)*100:.1f}%)")

    invalid_labels = set(labels.keys()) - {'COM', 'FUL'}
    if invalid_labels:
        print(f"\n❌ ERROR: Invalid labels found: {invalid_labels}")
        return False
    else:
        print(f"\n✓ All labels valid (COM/FUL only)")

    # Check 2: Distribution reasonable (expect 60-70% COM, 30-40% FUL)
    com_pct = labels['COM'] / len(patterns)
    ful_pct = labels['FUL'] / len(patterns)

    if not (0.50 <= com_pct <= 0.80):
        print(f"\n⚠ WARNING: COM percentage {com_pct:.1%} outside expected range (50-80%)")
    else:
        print(f"\n✓ COM percentage {com_pct:.1%} within expected range")

    # Check 3: Canonical IDs preserved
    id_label_pairs = {}
    for p in patterns:
        cid = p.get('id', 'UNKNOWN')
        label = p['label']
        if cid not in id_label_pairs:
            id_label_pairs[cid] = set()
        id_label_pairs[cid].add(label)

    both_forms = sum(1 for labels in id_label_pairs.values() if len(labels) == 2)
    one_form = sum(1 for labels in id_label_pairs.values() if len(labels) == 1)

    print(f"\nCanonical ID coverage:")
    print(f"  Resources with both COM and FUL forms: {both_forms:,}")
    print(f"  Resources with only one form: {one_form:,}")
    print(f"  Total unique resources: {len(id_label_pairs):,}")

    # Check 4: Sample validation
    print(f"\nSample patterns:")
    com_samples = [p for p in patterns if p['label'] == 'COM'][:5]
    ful_samples = [p for p in patterns if p['label'] == 'FUL'][:5]

    print(f"\n  COM samples:")
    for p in com_samples:
        pattern_text = p['pattern'] if isinstance(p['pattern'], str) else str(p['pattern'])
        print(f"    '{pattern_text}' (id={p.get('id', 'N/A')})")

    print(f"\n  FUL samples:")
    for p in ful_samples:
        pattern_text = p['pattern'] if isinstance(p['pattern'], str) else str(p['pattern'])
        print(f"    '{pattern_text}' (id={p.get('id', 'N/A')})")

    print("\n" + "="*70)
    print("✓ VALIDATION COMPLETE")
    print("="*70)

    return True

if __name__ == "__main__":
    validate_patterns()
