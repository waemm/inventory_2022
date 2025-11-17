#!/usr/bin/env python3
"""Verify label alignment in hybrid pipeline."""

import spacy

HYBRID_MODEL = "spacy_hybrid_ner/models/ner_hybrid_v2_com_ful"
STATISTICAL_MODEL = "collab_results/experiment_archives/2025-11-12-3uubs8/spacy_model/model-best"

def verify_alignment():
    """Verify label indices match between components."""
    print("="*70)
    print("VERIFYING LABEL ALIGNMENT")
    print("="*70)

    # Load models
    print(f"\nLoading hybrid model: {HYBRID_MODEL}")
    nlp_hybrid = spacy.load(HYBRID_MODEL)

    print(f"Loading statistical model: {STATISTICAL_MODEL}")
    nlp_stat = spacy.load(STATISTICAL_MODEL)

    # Get NER components
    ner_hybrid = nlp_hybrid.get_pipe("ner")
    ner_stat = nlp_stat.get_pipe("ner")
    ruler = nlp_hybrid.get_pipe("entity_ruler")

    # Check labels
    print(f"\n" + "-"*70)
    print("LABEL COMPARISON")
    print("-"*70)

    print(f"\nEntityRuler labels: {ruler.labels}")
    print(f"Hybrid NER labels:  {ner_hybrid.labels}")
    print(f"Statistical labels: {ner_stat.labels}")

    # Check alignment
    print(f"\n" + "-"*70)
    print("LABEL INDEX MAPPING")
    print("-"*70)

    print(f"\nStatistical NER (trained):")
    for i, label in enumerate(ner_stat.labels):
        print(f"  Index {i} → '{label}'")

    print(f"\nHybrid NER (merged):")
    for i, label in enumerate(ner_hybrid.labels):
        print(f"  Index {i} → '{label}'")

    # Verify alignment
    print(f"\n" + "-"*70)
    print("VERIFICATION")
    print("-"*70)

    if ner_hybrid.labels == ner_stat.labels:
        print("\n✅ SUCCESS: Labels are perfectly aligned!")
        print("   Statistical model's predictions will be interpreted correctly.")
    else:
        print("\n❌ ERROR: Labels are NOT aligned!")
        print("   This will cause the same issue we're trying to fix.")
        return False

    # Check expected alignment
    if ner_hybrid.labels == ('COM', 'FUL'):
        print("\n✅ SUCCESS: Label order is correct (COM, FUL)")
    else:
        print(f"\n⚠ WARNING: Unexpected label order: {ner_hybrid.labels}")

    # Check EntityRuler
    if set(ruler.labels) <= set(ner_hybrid.labels):
        print(f"\n✅ SUCCESS: EntityRuler labels {ruler.labels} are subset of NER labels")
    else:
        print(f"\n❌ ERROR: EntityRuler has labels not in NER: {set(ruler.labels) - set(ner_hybrid.labels)}")
        return False

    print("\n" + "="*70)
    print("✅ LABEL ALIGNMENT VERIFIED")
    print("="*70)

    return True

if __name__ == "__main__":
    success = verify_alignment()
    exit(0 if success else 1)
