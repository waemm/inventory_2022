"""
Quick test to verify all utils modules import correctly.
Run this to ensure there are no syntax errors or import issues.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing utils library imports...")
print("=" * 60)

# Test 1: Import main package
print("\n1. Testing main package import...")
try:
    import utils
    print("   ✓ utils package imported successfully")
    print(f"   Version: {utils.__version__}")
    print(f"   Exports: {len(utils.__all__)} functions")
except Exception as e:
    print(f"   ✗ Failed to import utils: {e}")
    sys.exit(1)

# Test 2: Import data_loading module
print("\n2. Testing data_loading module...")
try:
    from utils import data_loading
    functions = ['load_v2_results', 'load_phase4_results', 'load_ner_test_split',
                 'load_inventory', 'parse_entity_list']
    for func_name in functions:
        assert hasattr(data_loading, func_name), f"Missing function: {func_name}"
    print(f"   ✓ data_loading module OK ({len(functions)} functions)")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 3: Import entity_matching module
print("\n3. Testing entity_matching module...")
try:
    from utils import entity_matching
    functions = ['exact_match', 'partial_match', 'fuzzy_match',
                 'token_overlap', 'match_entities']
    for func_name in functions:
        assert hasattr(entity_matching, func_name), f"Missing function: {func_name}"
    print(f"   ✓ entity_matching module OK ({len(functions)} functions)")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 4: Import metrics module
print("\n4. Testing metrics module...")
try:
    from utils import metrics
    functions = ['calculate_precision_recall_f1', 'entity_level_metrics',
                 'confusion_matrix', 'bootstrap_confidence_interval']
    for func_name in functions:
        assert hasattr(metrics, func_name), f"Missing function: {func_name}"
    print(f"   ✓ metrics module OK ({len(functions)} functions)")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 5: Import bpe_cleaning module
print("\n5. Testing bpe_cleaning module...")
try:
    from utils import bpe_cleaning
    functions = ['detect_bpe_artifacts', 'clean_bpe_entity',
                 'clean_bpe_dataframe', 'generate_bpe_report']
    for func_name in functions:
        assert hasattr(bpe_cleaning, func_name), f"Missing function: {func_name}"
    print(f"   ✓ bpe_cleaning module OK ({len(functions)} functions)")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 6: Test direct imports from package
print("\n6. Testing direct imports from utils package...")
try:
    from utils import (
        load_v2_results, exact_match, calculate_precision_recall_f1,
        detect_bpe_artifacts, parse_entity_list
    )
    print("   ✓ Direct imports working correctly")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 7: Quick functional tests
print("\n7. Running quick functional tests...")
try:
    # Test parse_entity_list
    from utils import parse_entity_list
    result = parse_entity_list("entity1, entity2, entity3")
    assert result == ['entity1', 'entity2', 'entity3'], "parse_entity_list failed"
    print("   ✓ parse_entity_list() works")

    # Test exact_match
    from utils import exact_match
    assert exact_match("Protein A", "protein a") == True, "exact_match failed"
    print("   ✓ exact_match() works")

    # Test calculate_precision_recall_f1
    from utils import calculate_precision_recall_f1
    metrics = calculate_precision_recall_f1(80, 10, 10)
    assert 0.88 < metrics['f1'] < 0.90, "calculate_precision_recall_f1 failed"
    print("   ✓ calculate_precision_recall_f1() works")

    # Test detect_bpe_artifacts
    from utils import detect_bpe_artifacts
    assert detect_bpe_artifacts("Ġprotein") == True, "detect_bpe_artifacts failed"
    assert detect_bpe_artifacts("protein") == False, "detect_bpe_artifacts failed"
    print("   ✓ detect_bpe_artifacts() works")

    # Test clean_bpe_entity
    from utils import clean_bpe_entity
    assert clean_bpe_entity("Ġprotein") == "protein", "clean_bpe_entity failed"
    print("   ✓ clean_bpe_entity() works")

except AssertionError as e:
    print(f"   ✗ Functional test failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Error during functional tests: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All tests passed! Utils library is ready to use.")
print("=" * 60)
