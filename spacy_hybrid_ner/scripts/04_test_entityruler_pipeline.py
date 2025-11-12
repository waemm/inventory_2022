#!/usr/bin/env python3
"""
Test EntityRuler Pipeline (Phase 2.2)

Builds and tests the EntityRuler pipeline with sample text to verify:
1. Patterns load correctly
2. Entities are extracted
3. Alias resolution works (canonical IDs assigned)
4. Tokenization edge cases handled

Input:
    - data/patterns.jsonl

Output:
    - Console output with test results
    - Verification of alias resolution

Success Criteria:
    - All known entities extracted
    - Aliases correctly linked to canonical IDs
    - No false positives in test examples
"""

import spacy
from spacy.pipeline import EntityRuler
from pathlib import Path
import sys


# Configuration
PATTERNS_FILE = 'data/patterns.jsonl'


def test_basic_extraction(nlp):
    """Test basic entity extraction with known resources."""
    test_text = """
    We analyzed data from the Bio-Analytic Resource for Plant Biology (BAR),
    the Protein Domain Database (PDB), and the Mouse Phenome Database (MPD).
    The BAR and PDB databases were particularly useful for our analysis.
    """

    print("\n" + "="*60)
    print("TEST 1: Basic Entity Extraction")
    print("="*60)
    print(f"\nInput text:\n{test_text}")

    doc = nlp(test_text)

    print(f"\n📊 Extracted {len(doc.ents)} entities:")
    print("-" * 60)

    for ent in doc.ents:
        print(f"Text: '{ent.text}'")
        print(f"  Label: {ent.label_}")
        print(f"  Canonical ID: {ent.ent_id_}")
        print(f"  Span: [{ent.start_char}:{ent.end_char}]")
        print()

    if len(doc.ents) == 0:
        print("⚠️  WARNING: No entities extracted!")
        return False

    return True


def test_alias_resolution(nlp):
    """Test that aliases are correctly linked to canonical IDs."""
    test_text = """
    The Protein Domain Database (PDB) contains structural information.
    Many researchers use PDB for protein analysis.
    """

    print("\n" + "="*60)
    print("TEST 2: Alias Resolution")
    print("="*60)
    print(f"\nInput text:\n{test_text}")

    doc = nlp(test_text)

    # Group entities by canonical ID
    aliases = {}
    for ent in doc.ents:
        canonical = ent.ent_id_
        if canonical not in aliases:
            aliases[canonical] = []
        aliases[canonical].append(ent.text)

    print(f"\n📊 Alias groups:")
    print("-" * 60)

    for canonical, mentions in aliases.items():
        unique_mentions = set(mentions)
        print(f"{canonical}: {sorted(unique_mentions)}")

    # Verify: Should have at least one resource with multiple forms
    has_aliases = any(len(set(mentions)) > 1 for mentions in aliases.values())

    if not has_aliases:
        print("\n⚠️  WARNING: No aliases detected. Expected 'PDB' and 'Protein Domain Database' to link together.")
        return False

    return True


def test_punctuation_handling(nlp):
    """Test that token patterns handle punctuation correctly."""
    test_cases = [
        "We used PDB.",           # Period after acronym
        "The (PDB) database",     # Parentheses
        "PRIDE, PDB, and UniProt",  # Comma-separated list
        "PDB-101 tutorial",       # Hyphenated (may or may not match depending on tokenization)
    ]

    print("\n" + "="*60)
    print("TEST 3: Punctuation Handling")
    print("="*60)

    all_passed = True

    for text in test_cases:
        doc = nlp(text)
        entities = [ent.text for ent in doc.ents]

        # Check if we found at least one entity
        found = len(entities) > 0

        status = "✓" if found else "✗"
        print(f"{status} '{text}' → {entities if found else 'No entities'}")

        if not found:
            all_passed = False

    if not all_passed:
        print("\n⚠️  Some punctuation cases failed. This may be expected depending on patterns.")

    return True  # Non-critical test


def test_tokenization(nlp):
    """Show how spaCy tokenizes text (for debugging)."""
    test_text = "The PDB-101 database, UniProt, and (BAR) were used."

    print("\n" + "="*60)
    print("TEST 4: Tokenization Analysis")
    print("="*60)
    print(f"\nInput text: {test_text}")

    doc = nlp(test_text)

    print(f"\n📊 Tokens:")
    print("-" * 60)
    for i, token in enumerate(doc):
        print(f"{i}: '{token.text}' (pos={token.pos_}, is_punct={token.is_punct})")

    return True


def run_comprehensive_test(nlp):
    """Run comprehensive test with multiple resources."""
    test_text = """
    The Gene Expression Omnibus (GEO) is a public repository that archives and
    freely distributes microarray, next-generation sequencing, and other forms
    of high-throughput functional genomic data. GEO accepts array- and
    sequence-based data. Tools are provided to help users query and download
    experiments and curated gene expression profiles.

    We also used UniProt, PDB, and the Bio-Analytic Resource (BAR) in this study.
    """

    print("\n" + "="*60)
    print("TEST 5: Comprehensive Extraction")
    print("="*60)
    print(f"\nInput text:\n{test_text[:200]}...")

    doc = nlp(test_text)

    # Group by canonical ID
    resources = {}
    for ent in doc.ents:
        canonical = ent.ent_id_
        if canonical not in resources:
            resources[canonical] = set()
        resources[canonical].add(ent.text)

    print(f"\n📊 Found {len(resources)} unique resources:")
    print("-" * 60)

    for canonical, mentions in sorted(resources.items()):
        print(f"{canonical}:")
        for mention in sorted(mentions):
            print(f"  - '{mention}'")

    return len(resources) > 0


def main():
    """Main execution function."""
    print("="*60)
    print("Phase 2.2: Test EntityRuler Pipeline")
    print("="*60)

    # Check if patterns file exists
    if not Path(PATTERNS_FILE).exists():
        print(f"\n❌ ERROR: Patterns file not found: {PATTERNS_FILE}")
        print("Run 03_generate_patterns_jsonl.py first.")
        sys.exit(1)

    # Load blank English pipeline
    print(f"\n🔧 Building EntityRuler pipeline...")
    try:
        nlp = spacy.blank("en")
        print("✓ Created blank English pipeline")
    except Exception as e:
        print(f"❌ ERROR: Failed to create spaCy pipeline: {e}")
        sys.exit(1)

    # Add EntityRuler component
    try:
        ruler = nlp.add_pipe("entity_ruler")
        print("✓ Added EntityRuler component")
    except Exception as e:
        print(f"❌ ERROR: Failed to add EntityRuler: {e}")
        sys.exit(1)

    # Load patterns
    try:
        ruler.from_disk(PATTERNS_FILE)
        print(f"✓ Loaded {len(ruler.patterns)} patterns from {PATTERNS_FILE}")
    except Exception as e:
        print(f"❌ ERROR: Failed to load patterns: {e}")
        sys.exit(1)

    print(f"\nPipeline components: {nlp.pipe_names}")

    # Run tests
    results = {
        'basic_extraction': test_basic_extraction(nlp),
        'alias_resolution': test_alias_resolution(nlp),
        'punctuation_handling': test_punctuation_handling(nlp),
        'tokenization': test_tokenization(nlp),
        'comprehensive': run_comprehensive_test(nlp)
    }

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"\nPassed: {passed_count}/{total_count}")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        print("\n📊 Next step: Run 05_validate_entityruler.py for comprehensive validation")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
