#!/usr/bin/env python3
"""
Generate spaCy EntityRuler Patterns (Phase 1.3)

Creates JSONL pattern file for spaCy EntityRuler from enriched dictionary.
Uses token patterns for short names (handles punctuation) and phrase patterns
for full names (faster matching).

Input:
    - data/bioresource_dictionary_enriched.json

Output:
    - data/patterns.jsonl (~3,000-5,000 patterns)

Pattern Format:
    - Short names: Token pattern [{"TEXT": "PDB"}]
    - Full names: Phrase pattern "Protein Domain Database"
    - Each pattern includes canonical ID for alias resolution
"""

import json
from pathlib import Path
import sys


# Configuration
INPUT_DICT = 'data/bioresource_dictionary_enriched.json'
OUTPUT_JSONL = 'data/patterns.jsonl'


def generate_patterns(dictionary):
    """
    Generate EntityRuler patterns from dictionary.

    Args:
        dictionary: Dictionary with resource data

    Returns:
        list: List of pattern dictionaries
    """
    patterns = []

    for resource_id, data in dictionary.items():
        short_name = data['short_name']
        full_name = data.get('full_name')

        # Pattern 1: Short name (token pattern for punctuation handling)
        # Token pattern matches the token itself, ignoring surrounding punctuation
        patterns.append({
            "label": "BIO_RESOURCE",
            "pattern": [{"TEXT": short_name}],
            "id": resource_id
        })

        # Pattern 2: Full name (if available)
        if full_name:
            # Phrase pattern for exact string matching (faster)
            patterns.append({
                "label": "BIO_RESOURCE",
                "pattern": full_name,
                "id": resource_id
            })

            # Pattern 3: Plural form (conservative - only single words)
            # Only pluralize single-word names to avoid "Mouse Phenome Databases"
            words = full_name.split()
            if len(words) == 1 and not full_name.endswith('s'):
                patterns.append({
                    "label": "BIO_RESOURCE",
                    "pattern": full_name + "s",
                    "id": resource_id
                })

            # Pattern 4: "the X" variation (removed - too generic)
            # Commented out to avoid overgenerating unlikely patterns
            # Only add if proven needed for specific resources

    return patterns


def validate_patterns(patterns):
    """
    Validate pattern format and detect potential issues.

    Args:
        patterns: List of pattern dictionaries

    Returns:
        tuple: (is_valid, warnings)
    """
    warnings = []

    # Check for required fields
    for i, pattern in enumerate(patterns):
        if 'label' not in pattern:
            warnings.append(f"Pattern {i}: Missing 'label' field")
        if 'pattern' not in pattern:
            warnings.append(f"Pattern {i}: Missing 'pattern' field")
        if 'id' not in pattern:
            warnings.append(f"Pattern {i}: Missing 'id' field")

    # Check for very long patterns (might be errors)
    for i, pattern in enumerate(patterns):
        if isinstance(pattern['pattern'], str) and len(pattern['pattern']) > 100:
            warnings.append(f"Pattern {i}: Unusually long pattern ({len(pattern['pattern'])} chars): {pattern['pattern'][:50]}...")

    # Check for duplicate patterns (same text, different IDs - potential alias conflict)
    pattern_texts = {}
    for pattern in patterns:
        if isinstance(pattern['pattern'], str):
            text = pattern['pattern'].lower()
        else:
            # Token pattern
            text = ' '.join([t.get('TEXT', '').lower() for t in pattern['pattern']])

        if text in pattern_texts:
            if pattern_texts[text] != pattern['id']:
                warnings.append(f"Duplicate pattern with different IDs: '{text}' -> {pattern_texts[text]}, {pattern['id']}")
        else:
            pattern_texts[text] = pattern['id']

    is_valid = len(warnings) == 0
    return is_valid, warnings


def print_statistics(patterns):
    """Print pattern statistics."""
    # Count pattern types
    token_patterns = sum(1 for p in patterns if isinstance(p['pattern'], list))
    phrase_patterns = len(patterns) - token_patterns

    # Count by resource
    unique_ids = len(set(p['id'] for p in patterns))

    # Patterns per resource
    patterns_per_resource = len(patterns) / unique_ids

    print("\n" + "="*60)
    print("PATTERN GENERATION SUMMARY")
    print("="*60)
    print(f"\nTotal patterns: {len(patterns)}")
    print(f"  - Token patterns (short names): {token_patterns}")
    print(f"  - Phrase patterns (full names): {phrase_patterns}")
    print(f"\nUnique resources: {unique_ids}")
    print(f"Avg patterns per resource: {patterns_per_resource:.2f}")
    print("="*60 + "\n")

    # Show examples
    print("Example patterns:")
    print("-" * 60)
    for i, pattern in enumerate(patterns[:5]):
        pattern_str = pattern['pattern'] if isinstance(pattern['pattern'], str) else f"[TOKEN: {pattern['pattern'][0].get('TEXT')}]"
        print(f"{i+1}. ID={pattern['id']}: {pattern_str}")
    print("-" * 60)


def save_jsonl(patterns, output_path):
    """
    Save patterns to JSONL file.

    Args:
        patterns: List of pattern dictionaries
        output_path: Output file path
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for pattern in patterns:
            f.write(json.dumps(pattern, ensure_ascii=False) + '\n')


def main():
    """Main execution function."""
    print("="*60)
    print("Phase 1.3: Generate EntityRuler Patterns")
    print("="*60)

    # Load enriched dictionary
    print(f"\n📖 Loading enriched dictionary from: {INPUT_DICT}")
    if not Path(INPUT_DICT).exists():
        print(f"❌ ERROR: Dictionary not found. Run 02_enrich_missing_fullnames.py first.")
        sys.exit(1)

    with open(INPUT_DICT, 'r', encoding='utf-8') as f:
        dictionary = json.load(f)
    print(f"✓ Loaded {len(dictionary)} resources")

    # Generate patterns
    print("\n🔄 Generating EntityRuler patterns...")
    patterns = generate_patterns(dictionary)
    print(f"✓ Generated {len(patterns)} patterns")

    # Validate patterns
    print("\n🔍 Validating patterns...")
    is_valid, warnings = validate_patterns(patterns)

    if warnings:
        print(f"\n⚠️  Found {len(warnings)} warnings:")
        for warning in warnings[:10]:  # Show first 10
            print(f"  - {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")

        if not is_valid:
            print("\n⚠️  Some validation warnings found (continuing anyway).")
            print("   Note: Duplicate patterns are expected for resources with aliases.")
        else:
            print("✓ Warnings are informational only - continuing.")
    else:
        print("✓ All patterns valid!")

    # Print statistics
    print_statistics(patterns)

    # Save to JSONL
    Path(OUTPUT_JSONL).parent.mkdir(parents=True, exist_ok=True)
    print(f"💾 Saving patterns to: {OUTPUT_JSONL}")
    save_jsonl(patterns, OUTPUT_JSONL)
    print("✓ Patterns saved!")

    # Test loading with spaCy (if installed)
    print("\n🧪 Testing pattern loading with spaCy...")
    try:
        import spacy
        from spacy.pipeline import EntityRuler

        nlp = spacy.blank("en")
        ruler = nlp.add_pipe("entity_ruler")
        ruler.from_disk(OUTPUT_JSONL)

        print(f"✓ spaCy successfully loaded {len(ruler.patterns)} patterns!")
        print(f"\n📊 Next step: Run 04_test_entityruler_pipeline.py to test the EntityRuler")

    except ImportError:
        print("⚠️  spaCy not installed. Skipping load test.")
        print("   Install with: pip install spacy==3.7.0")
        print(f"\n📊 Next step: Install spaCy, then run 04_test_entityruler_pipeline.py")
    except Exception as e:
        print(f"⚠️  Warning: Failed to load patterns in spaCy: {e}")
        print("   Patterns file created successfully, but may need debugging.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
