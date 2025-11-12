#!/bin/bash
# Quick Start Script for spaCy Hybrid NER (Phase 1-2)
# Runs all Phase 1-2 scripts in sequence to build and validate EntityRuler

set -e  # Exit on error

echo "========================================"
echo "spaCy Hybrid NER - Phase 1-2 Quick Start"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -d "scripts" ]; then
    echo "❌ ERROR: scripts/ directory not found"
    echo "Please run this script from the spacy_hybrid_ner/ directory:"
    echo "  cd /Users/warren/development/GBC/inventory_2022/spacy_hybrid_ner"
    echo "  ./run_phase1_2.sh"
    exit 1
fi

# Check if spaCy is installed
if ! python -c "import spacy" 2>/dev/null; then
    echo "⚠️  spaCy not found. Installing..."
    pip install spacy==3.7.0
    echo "✓ spaCy installed"
fi

echo "Starting Phase 1-2 pipeline..."
echo ""

# Phase 1.1: Extract dictionary
echo "========================================"
echo "Phase 1.1: Extract Bioresource Dictionary"
echo "========================================"
python scripts/01_extract_bioresource_dictionary.py
if [ $? -ne 0 ]; then
    echo "❌ Phase 1.1 failed. Exiting."
    exit 1
fi
echo ""

# Phase 1.2: Enrich missing full names
echo "========================================"
echo "Phase 1.2: Enrich Missing Full Names"
echo "========================================"
python scripts/02_enrich_missing_fullnames.py
if [ $? -ne 0 ]; then
    echo "❌ Phase 1.2 failed. Exiting."
    exit 1
fi
echo ""

# Phase 1.3: Generate patterns
echo "========================================"
echo "Phase 1.3: Generate EntityRuler Patterns"
echo "========================================"
python scripts/03_generate_patterns_jsonl.py
if [ $? -ne 0 ]; then
    echo "❌ Phase 1.3 failed. Exiting."
    exit 1
fi
echo ""

# Phase 2.2: Test pipeline
echo "========================================"
echo "Phase 2.2: Test EntityRuler Pipeline"
echo "========================================"
python scripts/04_test_entityruler_pipeline.py
if [ $? -ne 0 ]; then
    echo "⚠️  Phase 2.2 had issues. Review output above."
fi
echo ""

# Phase 2.3: Validate on papers
echo "========================================"
echo "Phase 2.3: Validate on Bioresource Papers"
echo "========================================"
python scripts/05_validate_entityruler.py
if [ $? -ne 0 ]; then
    echo "⚠️  Phase 2.3 validation below targets. Review metrics above."
fi
echo ""

echo "========================================"
echo "Phase 1-2 Complete!"
echo "========================================"
echo ""
echo "📁 Generated files:"
echo "  - data/bioresource_dictionary_raw.json"
echo "  - data/bioresource_dictionary_enriched.json"
echo "  - data/patterns.jsonl"
echo "  - results/phase2_entityruler_validation.json"
echo "  - data/entityruler_precision_review.csv"
echo ""
echo "📊 Next steps:"
echo "  1. Review validation metrics in results/phase2_entityruler_validation.json"
echo "  2. Manually annotate data/entityruler_precision_review.csv to verify precision"
echo "  3. Proceed to Phase 3 (Distant Supervision Training Data)"
echo ""
