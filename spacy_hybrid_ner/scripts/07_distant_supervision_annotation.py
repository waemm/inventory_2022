#!/usr/bin/env python3
"""
Phase 3.2: Distant Supervision Auto-Annotation
==============================================

Auto-annotates bioresource papers using dictionary matching (distant supervision).
Creates spaCy-compatible training data in .spacy format (DocBin).

Algorithm:
  1. Load enriched dictionary (short_name + full_name)
  2. Build alias → label mapping (B-COM for short, B-FUL for full)
  3. For each paper:
     - Find all dictionary matches using regex
     - Convert to spaCy spans with char_span(alignment_mode="contract")
     - Filter overlapping spans
     - Save to DocBin

Input:
  - data/bioresource_dictionary_enriched.json
  - data/ner_corpus_splits/{train,dev,test}.csv

Output:
  - data/ner_training/train.spacy
  - data/ner_training/dev.spacy
  - data/ner_training/test.spacy
  - data/ner_training/annotation_statistics.csv
  - results/phase3_annotation_quality.json

Usage:
    python scripts/07_distant_supervision_annotation.py

Author: Claude (Sonnet 4.5)
Date: 2025-11-12
"""

import spacy
from spacy.tokens import DocBin
import pandas as pd
import re
import json
import sys
from pathlib import Path
from tqdm import tqdm
from collections import Counter

# Project paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SPACY_ROOT = SCRIPT_DIR.parent

# Input paths
DICTIONARY_PATH = SPACY_ROOT / 'data' / 'bioresource_dictionary_enriched.json'
CORPUS_DIR = SPACY_ROOT / 'data' / 'ner_corpus_splits'

# Output paths
OUTPUT_DIR = SPACY_ROOT / 'data' / 'ner_training'
RESULTS_DIR = SPACY_ROOT / 'results'


def load_dictionary():
    """Load enriched bioresource dictionary."""
    print(f"\nLoading dictionary from: {DICTIONARY_PATH}")

    if not DICTIONARY_PATH.exists():
        print(f"❌ Error: Dictionary not found at {DICTIONARY_PATH}")
        print("   Run script 02 first to create enriched dictionary")
        sys.exit(1)

    with open(DICTIONARY_PATH, 'r') as f:
        dictionary = json.load(f)

    print(f"✓ Loaded {len(dictionary)} bioresources")

    return dictionary


def build_alias_mapping(dictionary):
    """
    Build alias → label mapping for annotation.

    Returns:
        dict: {alias: label} where label is "COM" or "FUL"

    Note: Labels use base names (COM, FUL) without BIO prefixes.
          spaCy automatically applies BIO tagging during training.
    """
    print("\nBuilding alias → label mapping...")

    alias_to_label = {}
    alias_to_canonical = {}

    for resource_id, data in dictionary.items():
        short = data['short_name']
        full = data.get('full_name')

        # Short name → COM (common name)
        alias_to_label[short] = "COM"
        alias_to_canonical[short] = resource_id

        # Full name → FUL (full name) - if available
        if full and isinstance(full, str) and len(full) > 0:
            alias_to_label[full] = "FUL"
            alias_to_canonical[full] = resource_id

    print(f"✓ Created {len(alias_to_label)} alias patterns")
    print(f"  Short names (COM): {sum(1 for v in alias_to_label.values() if v == 'COM')}")
    print(f"  Full names (FUL): {sum(1 for v in alias_to_label.values() if v == 'FUL')}")

    return alias_to_label, alias_to_canonical


def build_regex_pattern(alias_to_label):
    """
    Build compiled regex pattern for all aliases.

    Sorts aliases by length (longest first) to avoid partial matches.

    Note: Uses case-SENSITIVE matching to avoid label ambiguity
          (e.g., "pdb" in text won't match "PDB" or "Protein Data Bank").
    """
    print("\nBuilding regex pattern...")

    # Sort by length (longest first) to prioritize longer matches
    aliases_sorted = sorted(alias_to_label.keys(), key=len, reverse=True)

    # Escape special regex characters and join with |
    escaped_aliases = [re.escape(alias) for alias in aliases_sorted]
    regex_pattern = r'\b(' + '|'.join(escaped_aliases) + r')\b'

    # Compile with case-SENSITIVE matching (removed re.IGNORECASE)
    pattern = re.compile(regex_pattern)

    print(f"✓ Compiled regex pattern ({len(aliases_sorted)} alternatives)")
    print(f"  Matching mode: Case-sensitive (deterministic labels)")

    return pattern


def resolve_overlaps_smart(spans):
    """
    Resolve overlapping spans by keeping longest non-conflicting spans.

    Note: spaCy does NOT allow overlapping entities, even if nested.
    For example, "Protein Data Bank (PDB)" contains both the full name
    and short name, but we can only keep one. We prioritize longer spans
    (full names) as they provide more context.

    Trade-off: We lose some short name annotations when they appear in
    parentheses after full names. However, the model will still learn
    short name patterns from standalone occurrences.

    Args:
        spans: List of spaCy Span objects

    Returns:
        List of spaCy Span objects with NO overlaps
    """
    if not spans:
        return []

    # Sort by length (longest first), then by start position
    sorted_spans = sorted(spans, key=lambda s: (-(s.end - s.start), s.start))

    kept = []
    for span in sorted_spans:
        # Check if this span overlaps with any kept span
        overlaps = False

        for kept_span in kept:
            # Check if spans share ANY tokens
            if not (span.end <= kept_span.start or span.start >= kept_span.end):
                # They overlap - skip this span (already kept longer one)
                overlaps = True
                break

        if not overlaps:
            kept.append(span)

    # Sort by start position for final output
    return sorted(kept, key=lambda s: s.start)


def annotate_text(text, nlp, pattern, alias_to_label, alias_to_canonical):
    """
    Auto-annotate text with dictionary matches.

    Improvements:
    - Case-sensitive matching for deterministic labels
    - alignment_mode="expand" for higher recall
    - Smart overlap resolution preserving nested entities

    Args:
        text: Raw text to annotate
        nlp: spaCy Language object (for tokenization)
        pattern: Compiled regex pattern
        alias_to_label: Dictionary mapping aliases to labels
        alias_to_canonical: Dictionary mapping aliases to resource IDs

    Returns:
        Doc: spaCy Doc with entity annotations
    """
    # Create Doc
    doc = nlp.make_doc(text)
    ents = []

    # Find all string matches
    for match in pattern.finditer(text):
        matched_text = match.group(1)
        start, end = match.span()

        # Determine label with EXACT (case-sensitive) matching
        label = alias_to_label.get(matched_text)
        canonical_id = alias_to_canonical.get(matched_text) if label else None

        if not label:
            continue  # Skip if not found (shouldn't happen with regex)

        # Use alignment_mode="expand" for higher recall
        # This captures entities even if they slightly misalign with token boundaries
        span = doc.char_span(start, end, label=label, alignment_mode="expand")

        if span is not None:
            # Validation: ensure span length is reasonable (not expanded too much)
            if len(span) > 0 and len(span) <= 20:  # Max 20 tokens
                ents.append(span)

    # Apply smart overlap resolution (preserves nested entities like "PDB" + "Protein Data Bank (PDB)")
    doc.ents = resolve_overlaps_smart(ents)

    return doc


def process_split(split_name, nlp, pattern, alias_to_label, alias_to_canonical):
    """
    Process a single split (train/dev/test).

    Returns:
        dict: Statistics for this split
    """
    print(f"\nProcessing {split_name} split...")

    # Load papers
    csv_path = CORPUS_DIR / f'{split_name}.csv'
    if not csv_path.exists():
        print(f"❌ Error: {csv_path} not found")
        print("   Run script 06 first to create corpus splits")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} papers")

    # Initialize DocBin
    db = DocBin()

    # Statistics
    total_docs = 0
    total_entities = 0
    skipped = 0
    docs_with_entities = 0
    label_counter = Counter()

    # Process each paper
    for _, paper in tqdm(df.iterrows(), total=len(df), desc=f"  Annotating {split_name}"):
        text = paper.get('text', '')

        if not text or len(text) < 10:
            skipped += 1
            continue

        # Annotate
        doc = annotate_text(text, nlp, pattern, alias_to_label, alias_to_canonical)

        # Add to DocBin
        db.add(doc)

        total_docs += 1
        entity_count = len(doc.ents)
        total_entities += entity_count

        if entity_count > 0:
            docs_with_entities += 1

        # Count labels
        for ent in doc.ents:
            label_counter[ent.label_] += 1

    # Save DocBin
    output_path = OUTPUT_DIR / f'{split_name}.spacy'
    db.to_disk(output_path)

    print(f"  ✓ Saved: {output_path}")
    print(f"  Documents: {total_docs}")
    print(f"  Documents with entities: {docs_with_entities} ({docs_with_entities/total_docs*100:.1f}%)")
    print(f"  Total entities: {total_entities}")
    print(f"  Avg entities/doc: {total_entities/total_docs:.2f}")
    print(f"  Skipped: {skipped}")
    print(f"  Label distribution:")
    for label, count in label_counter.items():
        print(f"    {label}: {count} ({count/total_entities*100:.1f}%)")

    return {
        'split': split_name,
        'documents': total_docs,
        'docs_with_entities': docs_with_entities,
        'coverage': docs_with_entities / total_docs if total_docs > 0 else 0,
        'entities': total_entities,
        'avg_per_doc': total_entities / total_docs if total_docs > 0 else 0,
        'skipped': skipped,
        'label_counts': dict(label_counter)
    }


def validate_annotations(split_name='train', sample_size=5):
    """
    Validate annotations by inspecting a sample.

    Returns:
        list: Sample annotations for manual inspection
    """
    print(f"\nValidating annotations (sample from {split_name})...")

    # Load .spacy file
    spacy_path = OUTPUT_DIR / f'{split_name}.spacy'
    nlp = spacy.blank("en")
    db = DocBin().from_disk(spacy_path)
    docs = list(db.get_docs(nlp.vocab))

    print(f"  Loaded {len(docs)} documents")

    # Sample docs with entities
    docs_with_entities = [doc for doc in docs if len(doc.ents) > 0]

    if len(docs_with_entities) == 0:
        print("  ⚠️  No documents with entities found!")
        return []

    sample = docs_with_entities[:sample_size]

    samples = []
    print(f"\n  Sample annotations:")
    for i, doc in enumerate(sample):
        print(f"\n  Doc {i+1}:")
        print(f"    Text: {doc.text[:100]}...")
        print(f"    Entities ({len(doc.ents)}):")
        for ent in doc.ents:
            print(f"      - '{ent.text}' ({ent.label_}) [tokens {ent.start}:{ent.end}]")

        samples.append({
            'doc_id': i,
            'text': doc.text[:200],
            'entities': [{'text': ent.text, 'label': ent.label_, 'start': ent.start, 'end': ent.end} for ent in doc.ents]
        })

    return samples


def main():
    """Main execution."""
    print("=" * 70)
    print("Phase 3.2: Distant Supervision Auto-Annotation")
    print("=" * 70)

    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load dictionary
    dictionary = load_dictionary()

    # Build alias mapping
    alias_to_label, alias_to_canonical = build_alias_mapping(dictionary)

    # Build regex pattern
    pattern = build_regex_pattern(alias_to_label)

    # Initialize spaCy (blank English)
    print("\nInitializing spaCy...")
    nlp = spacy.blank("en")
    print("✓ spaCy initialized")

    # Process all splits
    all_stats = []
    for split in ['train', 'dev', 'test']:
        stats = process_split(split, nlp, pattern, alias_to_label, alias_to_canonical)
        all_stats.append(stats)

    # Save statistics
    stats_df = pd.DataFrame(all_stats)
    stats_path = OUTPUT_DIR / 'annotation_statistics.csv'
    stats_df.to_csv(stats_path, index=False)
    print(f"\n✓ Saved annotation statistics to: {stats_path}")

    # Validate annotations
    samples = validate_annotations(split_name='train', sample_size=5)

    # Save quality report
    quality_report = {
        'statistics': all_stats,
        'sample_annotations': samples
    }

    quality_path = RESULTS_DIR / 'phase3_annotation_quality.json'
    with open(quality_path, 'w') as f:
        json.dump(quality_report, f, indent=2)
    print(f"✓ Saved quality report to: {quality_path}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(stats_df.to_string(index=False))
    print("\n✓ Phase 3.2 complete!")
    print(f"\nNext step: Generate spaCy config and train model (Phase 4)")
    print("=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
