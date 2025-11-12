#!/usr/bin/env python3
"""
Phase 4 Validation: Test Statistical NER Model
==============================================

Tests the trained statistical NER model for generalization to NEW entities
not seen in the training dictionary.

Key Test: Can the model discover NEW/unknown bioresources beyond the 3,761 in dictionary?

Input:
  - models/ner_statistical/ (trained spaCy model)

Output:
  - Console report on generalization capability

Usage:
    python scripts/08_validate_statistical_ner.py [--model-path PATH]

Author: Claude (Sonnet 4.5)
Date: 2025-11-12
"""

import spacy
import sys
from pathlib import Path
import argparse

# Project paths
SCRIPT_DIR = Path(__file__).parent
SPACY_ROOT = SCRIPT_DIR.parent
DEFAULT_MODEL_PATH = SPACY_ROOT / 'models' / 'ner_statistical'


def load_model(model_path):
    """Load trained spaCy model."""
    print(f"\nLoading model from: {model_path}")

    if not model_path.exists():
        print(f"❌ Error: Model not found at {model_path}")
        print("   Train the model first using the Colab notebook:")
        print("   notebooks/spacy_ner_training.ipynb")
        sys.exit(1)

    try:
        nlp = spacy.load(model_path)
        print(f"✓ Model loaded successfully")
        return nlp
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        sys.exit(1)


def test_generalization(nlp):
    """Test model's ability to generalize to NEW entities."""

    # Test cases: Mix of KNOWN (in dictionary) and NEW (not in dictionary)
    test_cases = [
        {
            'text': "We created the Genomics Knowledge Base (GKB) for this study.",
            'type': 'NEW',
            'expected_entities': ['Genomics Knowledge Base', 'GKB'],
            'description': 'NEW resource with full name + acronym pattern'
        },
        {
            'text': "The Cell Atlas Repository contains single-cell RNA-seq data.",
            'type': 'NEW',
            'expected_entities': ['Cell Atlas Repository'],
            'description': 'NEW repository-type resource'
        },
        {
            'text': "Data from PDB and UniProt were integrated for analysis.",
            'type': 'KNOWN',
            'expected_entities': ['PDB', 'UniProt'],
            'description': 'KNOWN resources from dictionary'
        },
        {
            'text': "The Proteomics Data Commons (PDC) was recently launched by NCI.",
            'type': 'NEW',
            'expected_entities': ['Proteomics Data Commons', 'PDC'],
            'description': 'NEW commons-type resource'
        },
        {
            'text': "We used MGI and FlyBase for comparative genomics analysis.",
            'type': 'KNOWN',
            'expected_entities': ['MGI', 'FlyBase'],
            'description': 'KNOWN model organism databases'
        },
        {
            'text': "The BioImage Archive stores microscopy imaging data.",
            'type': 'NEW',
            'expected_entities': ['BioImage Archive'],
            'description': 'NEW archive-type resource'
        },
        {
            'text': "Clinical Genome Resource (ClinGen) provides curated genetic information.",
            'type': 'KNOWN',
            'expected_entities': ['Clinical Genome Resource', 'ClinGen'],
            'description': 'KNOWN resource from manual additions'
        },
        {
            'text': "The Open Microscopy Environment (OME) develops imaging software.",
            'type': 'NEW',
            'expected_entities': ['Open Microscopy Environment', 'OME'],
            'description': 'NEW environment-type resource'
        },
    ]

    print("\n" + "=" * 70)
    print("TESTING GENERALIZATION TO NEW ENTITIES")
    print("=" * 70)

    results = {
        'KNOWN': {'total': 0, 'detected': 0, 'missed': 0},
        'NEW': {'total': 0, 'detected': 0, 'missed': 0}
    }

    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        case_type = test_case['type']
        description = test_case['description']

        # Process text
        doc = nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        # Update counts
        results[case_type]['total'] += 1
        if entities:
            results[case_type]['detected'] += 1
        else:
            results[case_type]['missed'] += 1

        # Display results
        print(f"\nTest {i} [{case_type}]: {description}")
        print(f"  Text: {text}")

        if entities:
            print(f"  ✓ Entities detected: {entities}")
        else:
            print(f"  ✗ No entities found")
            print(f"    Expected: {test_case['expected_entities']}")

    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)

    for case_type in ['KNOWN', 'NEW']:
        total = results[case_type]['total']
        detected = results[case_type]['detected']
        missed = results[case_type]['missed']

        if total > 0:
            detection_rate = detected / total * 100
            print(f"\n{case_type} Resources:")
            print(f"  Total test cases: {total}")
            print(f"  Detected: {detected} ({detection_rate:.1f}%)")
            print(f"  Missed: {missed}")

    # Generalization assessment
    print("\n" + "=" * 70)
    print("GENERALIZATION ASSESSMENT")
    print("=" * 70)

    new_detection_rate = results['NEW']['detected'] / results['NEW']['total'] * 100
    known_detection_rate = results['KNOWN']['detected'] / results['KNOWN']['total'] * 100

    print(f"\n✓ KNOWN resource detection: {known_detection_rate:.1f}%")
    print(f"  (Baseline - should be high as these are in training dictionary)")

    print(f"\n{'✓' if new_detection_rate >= 50 else '⚠️'} NEW resource detection: {new_detection_rate:.1f}%")
    print(f"  (Generalization - measures ability to find unseen resources)")

    if new_detection_rate >= 50:
        print(f"\n🎯 SUCCESS: Model generalizes well to NEW entities!")
        print(f"   The statistical NER has learned patterns beyond the dictionary.")
    else:
        print(f"\n⚠️  WARNING: Low generalization to NEW entities")
        print(f"   Consider:")
        print(f"   - Training longer (more epochs)")
        print(f"   - Improving annotation quality")
        print(f"   - Adding more diverse training examples")

    print("=" * 70)

    return results


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description='Validate statistical NER model')
    parser.add_argument(
        '--model-path',
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help='Path to trained spaCy model'
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Phase 4: Statistical NER Model Validation")
    print("=" * 70)

    # Load model
    nlp = load_model(args.model_path)

    # Test generalization
    results = test_generalization(nlp)

    return 0


if __name__ == '__main__':
    sys.exit(main())
