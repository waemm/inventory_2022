#!/usr/bin/env python3
"""
Unit tests for Scripts 02-04 of the Phase 4 vs V2 NER comparison project.

Tests cover:
- Data loading and validation
- Metric calculations
- Matching strategies
- Statistical tests
- Report generation
- Edge cases and error handling

Run with:
    python test_scripts_02_03_04.py
    pytest test_scripts_02_03_04.py -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Try to import mcnemar, but continue if not available
try:
    from scipy.stats import mcnemar
    HAS_MCNEMAR = True
except ImportError:
    HAS_MCNEMAR = False

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import functions to test
from utils.data_loading import parse_entity_list
from utils.entity_matching import exact_match, fuzzy_match, match_entities
from utils.metrics import (
    bootstrap_confidence_interval,
    calculate_precision_recall_f1,
    entity_level_metrics,
)


class TestScript02Functions(unittest.TestCase):
    """Tests for Script 02: Evaluate on Test Split"""

    def setUp(self):
        """Set up test data"""
        self.sample_entities = ['protein A', 'gene B', 'compound C']
        self.ground_truth = ['protein A', 'gene B', 'gene D']

    def test_entity_level_metrics(self):
        """Test entity-level metrics calculation"""
        metrics = entity_level_metrics(
            self.sample_entities,
            self.ground_truth,
            match_strategy='exact'
        )

        self.assertEqual(metrics['tp'], 2)  # protein A, gene B
        self.assertEqual(metrics['fp'], 1)  # compound C
        self.assertEqual(metrics['fn'], 1)  # gene D

        # Check F1 calculation
        expected_precision = 2 / 3  # 2 correct out of 3 predicted
        expected_recall = 2 / 3     # 2 found out of 3 true
        expected_f1 = 2 * (expected_precision * expected_recall) / (expected_precision + expected_recall)

        self.assertAlmostEqual(metrics['precision'], expected_precision, places=4)
        self.assertAlmostEqual(metrics['recall'], expected_recall, places=4)
        self.assertAlmostEqual(metrics['f1'], expected_f1, places=4)

    def test_entity_level_metrics_empty_predictions(self):
        """Test metrics with empty predictions"""
        metrics = entity_level_metrics([], self.ground_truth)

        self.assertEqual(metrics['tp'], 0)
        self.assertEqual(metrics['fp'], 0)
        self.assertEqual(metrics['fn'], 3)
        self.assertEqual(metrics['precision'], 0.0)
        self.assertEqual(metrics['recall'], 0.0)
        self.assertEqual(metrics['f1'], 0.0)

    def test_entity_level_metrics_empty_ground_truth(self):
        """Test metrics with empty ground truth"""
        metrics = entity_level_metrics(self.sample_entities, [])

        self.assertEqual(metrics['tp'], 0)
        self.assertEqual(metrics['fp'], 3)
        self.assertEqual(metrics['fn'], 0)
        self.assertEqual(metrics['precision'], 0.0)
        # Recall is 0 when there are no true entities (0/0 = 0 by convention)
        self.assertEqual(metrics['recall'], 0.0)

    def test_entity_level_metrics_perfect_match(self):
        """Test metrics with perfect predictions"""
        metrics = entity_level_metrics(
            self.ground_truth,
            self.ground_truth
        )

        self.assertEqual(metrics['tp'], 3)
        self.assertEqual(metrics['fp'], 0)
        self.assertEqual(metrics['fn'], 0)
        self.assertEqual(metrics['precision'], 1.0)
        self.assertEqual(metrics['recall'], 1.0)
        self.assertEqual(metrics['f1'], 1.0)

    def test_bootstrap_confidence_interval(self):
        """Test bootstrap CI calculation"""
        scores = [0.8, 0.85, 0.82, 0.88, 0.83]
        ci = bootstrap_confidence_interval(scores, confidence=0.95, random_state=42)

        self.assertAlmostEqual(ci['mean'], np.mean(scores), places=4)
        self.assertLess(ci['lower'], ci['mean'])
        self.assertGreater(ci['upper'], ci['mean'])
        self.assertEqual(ci['confidence'], 0.95)
        self.assertEqual(ci['n_samples'], 5)

    def test_bootstrap_ci_single_value(self):
        """Test bootstrap CI with single value"""
        scores = [0.8]
        ci = bootstrap_confidence_interval(scores, random_state=42)

        self.assertEqual(ci['mean'], 0.8)
        # CI should be tight around single value
        self.assertAlmostEqual(ci['lower'], 0.8, places=1)
        self.assertAlmostEqual(ci['upper'], 0.8, places=1)

    @unittest.skipIf(not HAS_MCNEMAR, "scipy.stats.mcnemar not available")
    def test_mcnemar_test_wrapper(self):
        """Test McNemar's test calculation"""
        # Create contingency table
        # System 1 correct: 50, System 2 correct: 55
        # Both correct: 45, Both incorrect: 40
        # System 1 only: 5, System 2 only: 10

        system1_correct = [True] * 50 + [False] * 50
        system2_correct = [True] * 55 + [False] * 45

        # Build contingency table manually
        both_correct = sum([s1 and s2 for s1, s2 in zip(system1_correct, system2_correct)])
        both_incorrect = sum([not s1 and not s2 for s1, s2 in zip(system1_correct, system2_correct)])
        s1_only = sum([s1 and not s2 for s1, s2 in zip(system1_correct, system2_correct)])
        s2_only = sum([not s1 and s2 for s1, s2 in zip(system1_correct, system2_correct)])

        table = [[both_correct, s1_only],
                 [s2_only, both_incorrect]]

        result = mcnemar(table, exact=False, correction=True)

        self.assertIsNotNone(result.statistic)
        self.assertIsNotNone(result.pvalue)
        self.assertGreaterEqual(result.pvalue, 0.0)
        self.assertLessEqual(result.pvalue, 1.0)


class TestScript03Functions(unittest.TestCase):
    """Tests for Script 03: Evaluate on Inventory"""

    def setUp(self):
        """Set up test data"""
        self.entity = "protein kinase A"
        self.resource_names = [
            "Protein Kinase A",
            "PKA",
            "protein kinase alpha"
        ]

    def test_exact_match(self):
        """Test exact matching"""
        self.assertTrue(exact_match("protein A", "Protein A"))
        self.assertTrue(exact_match("protein A", "protein a"))
        self.assertTrue(exact_match("protein  A", "protein A"))  # Multiple spaces
        self.assertFalse(exact_match("protein A", "protein B"))

    def test_fuzzy_match(self):
        """Test fuzzy matching"""
        self.assertTrue(fuzzy_match("protein", "protien"))  # Typo (distance=1)
        self.assertTrue(fuzzy_match("IL-6", "IL-6 "))  # Trailing space (distance=1)
        self.assertTrue(fuzzy_match("protein A", "protein a"))  # Case (distance=0)
        # "protein" vs "proteins" has distance=1 (one insertion), so it matches with default max_distance=2
        self.assertTrue(fuzzy_match("protein", "proteins"))  # Distance=1, within threshold

    def test_match_entities(self):
        """Test multi-strategy entity matching"""
        entities1 = ["protein A", "gene B", "compound C"]
        entities2 = ["Protein A", "gene b", "gene D"]

        results = match_entities(entities1, entities2)

        self.assertEqual(results['match_count'], 2)  # protein A, gene B
        self.assertEqual(len(results['unmatched_1']), 1)  # compound C
        self.assertEqual(len(results['unmatched_2']), 1)  # gene D

    def test_match_entities_empty(self):
        """Test matching with empty lists"""
        results = match_entities([], ["entity1", "entity2"])

        self.assertEqual(results['match_count'], 0)
        self.assertEqual(len(results['unmatched_1']), 0)
        self.assertEqual(len(results['unmatched_2']), 2)

    def test_match_entities_all_match(self):
        """Test matching where all entities match"""
        entities = ["protein A", "gene B", "compound C"]

        results = match_entities(entities, entities)

        self.assertEqual(results['match_count'], 3)
        self.assertEqual(len(results['unmatched_1']), 0)
        self.assertEqual(len(results['unmatched_2']), 0)


class TestScript04Functions(unittest.TestCase):
    """Tests for Script 04: Analyze BPE Artifacts"""

    def test_detect_bpe_artifacts(self):
        """Test BPE artifact detection"""
        from utils.bpe_cleaning import detect_bpe_artifacts

        # Should detect Ġ marker
        self.assertTrue(detect_bpe_artifacts("Ġprotein"))
        self.assertTrue(detect_bpe_artifacts("ĠIL-6"))

        # Should not detect clean entities
        self.assertFalse(detect_bpe_artifacts("protein A"))
        self.assertFalse(detect_bpe_artifacts("IL-6"))

    def test_clean_bpe_entity(self):
        """Test BPE entity cleaning"""
        from utils.bpe_cleaning import clean_bpe_entity

        # Clean Ġ markers
        self.assertEqual(clean_bpe_entity("Ġprotein"), "protein")
        self.assertEqual(clean_bpe_entity("ĠIL-6"), "IL-6")
        self.assertEqual(clean_bpe_entity("Ġprotein ĠA"), "protein A")

        # Don't modify clean entities
        self.assertEqual(clean_bpe_entity("protein A"), "protein A")
        self.assertEqual(clean_bpe_entity("IL-6"), "IL-6")

    def test_clean_bpe_entity_whitelist(self):
        """Test that whitelisted tokens are preserved"""
        from utils.bpe_cleaning import clean_bpe_entity

        # These should NOT be merged (valid biological tokens)
        self.assertEqual(clean_bpe_entity("T cell"), "T cell")
        self.assertEqual(clean_bpe_entity("B lymphocyte"), "B lymphocyte")
        self.assertEqual(clean_bpe_entity("IL-6"), "IL-6")

    def test_calculate_precision_recall_f1(self):
        """Test basic P/R/F1 calculation"""
        metrics = calculate_precision_recall_f1(tp=80, fp=10, fn=10)

        expected_precision = 80 / 90  # 80 / (80 + 10)
        expected_recall = 80 / 90     # 80 / (80 + 10)
        expected_f1 = 2 * (expected_precision * expected_recall) / (expected_precision + expected_recall)

        self.assertAlmostEqual(metrics['precision'], expected_precision, places=4)
        self.assertAlmostEqual(metrics['recall'], expected_recall, places=4)
        self.assertAlmostEqual(metrics['f1'], expected_f1, places=4)

    def test_calculate_precision_recall_f1_edge_cases(self):
        """Test P/R/F1 with edge cases"""
        # All zeros
        metrics = calculate_precision_recall_f1(tp=0, fp=0, fn=0)
        self.assertEqual(metrics['precision'], 0.0)
        self.assertEqual(metrics['recall'], 0.0)
        self.assertEqual(metrics['f1'], 0.0)

        # Perfect score
        metrics = calculate_precision_recall_f1(tp=100, fp=0, fn=0)
        self.assertEqual(metrics['precision'], 1.0)
        self.assertEqual(metrics['recall'], 1.0)
        self.assertEqual(metrics['f1'], 1.0)

        # Only false positives
        metrics = calculate_precision_recall_f1(tp=0, fp=100, fn=0)
        self.assertEqual(metrics['precision'], 0.0)


class TestDataLoading(unittest.TestCase):
    """Tests for data loading utilities"""

    def test_parse_entity_list_comma_separated(self):
        """Test parsing comma-separated entities"""
        result = parse_entity_list("protein A, gene B, compound C")
        self.assertEqual(result, ['protein A', 'gene B', 'compound C'])

    def test_parse_entity_list_json(self):
        """Test parsing JSON array"""
        result = parse_entity_list('["protein A", "gene B", "compound C"]')
        self.assertEqual(result, ['protein A', 'gene B', 'compound C'])

    def test_parse_entity_list_already_list(self):
        """Test parsing when already a list"""
        result = parse_entity_list(['protein A', 'gene B', 'compound C'])
        self.assertEqual(result, ['protein A', 'gene B', 'compound C'])

    def test_parse_entity_list_empty(self):
        """Test parsing empty values"""
        self.assertEqual(parse_entity_list(None), [])
        self.assertEqual(parse_entity_list(""), [])
        self.assertEqual(parse_entity_list("[]"), [])

    def test_parse_entity_list_with_whitespace(self):
        """Test parsing with extra whitespace"""
        result = parse_entity_list("  protein A  ,  gene B  ,  compound C  ")
        self.assertEqual(result, ['protein A', 'gene B', 'compound C'])


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""

    def test_end_to_end_evaluation(self):
        """Test complete evaluation workflow"""
        # Create sample data
        predicted = ['protein A', 'gene B', 'compound C']
        ground_truth = ['protein A', 'gene B', 'gene D']

        # Calculate metrics
        metrics = entity_level_metrics(predicted, ground_truth)

        # Verify workflow
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1', metrics)
        self.assertIn('tp', metrics)
        self.assertIn('fp', metrics)
        self.assertIn('fn', metrics)

        # Verify metrics are in valid range
        self.assertGreaterEqual(metrics['precision'], 0.0)
        self.assertLessEqual(metrics['precision'], 1.0)
        self.assertGreaterEqual(metrics['recall'], 0.0)
        self.assertLessEqual(metrics['recall'], 1.0)
        self.assertGreaterEqual(metrics['f1'], 0.0)
        self.assertLessEqual(metrics['f1'], 1.0)

    def test_contamination_workflow(self):
        """Test BPE contamination detection and cleaning workflow"""
        from utils.bpe_cleaning import clean_bpe_entity, detect_bpe_artifacts

        entities = [
            "Ġprotein A",
            "gene B",
            "ĠIL-6",
            "compound C"
        ]

        # Detect contaminated entities
        contaminated = [e for e in entities if detect_bpe_artifacts(e)]
        self.assertEqual(len(contaminated), 2)  # Ġprotein A, ĠIL-6

        # Clean all entities
        cleaned = [clean_bpe_entity(e) for e in entities]

        # Verify cleaning
        self.assertEqual(cleaned[0], "protein A")
        self.assertEqual(cleaned[1], "gene B")
        self.assertEqual(cleaned[2], "IL-6")
        self.assertEqual(cleaned[3], "compound C")

        # Verify no contamination after cleaning
        still_contaminated = [e for e in cleaned if detect_bpe_artifacts(e)]
        self.assertEqual(len(still_contaminated), 0)

    def test_dataframe_operations(self):
        """Test DataFrame-based operations"""
        # Create sample DataFrame
        df = pd.DataFrame({
            'paper_id': ['PMC1', 'PMC2', 'PMC3'],
            'entities': [
                "protein A, gene B",
                "Ġprotein C, gene D",
                "gene E"
            ]
        })

        # Parse entities
        df['entities_parsed'] = df['entities'].apply(parse_entity_list)

        # Check parsing
        self.assertEqual(len(df.loc[0, 'entities_parsed']), 2)
        self.assertEqual(len(df.loc[1, 'entities_parsed']), 2)
        self.assertEqual(len(df.loc[2, 'entities_parsed']), 1)

    def test_statistical_comparison(self):
        """Test statistical comparison between systems"""
        # Create sample F1 scores
        system1_f1 = [0.8, 0.85, 0.82, 0.88, 0.83]
        system2_f1 = [0.75, 0.80, 0.78, 0.82, 0.79]

        # Calculate bootstrap CIs
        ci1 = bootstrap_confidence_interval(system1_f1, random_state=42)
        ci2 = bootstrap_confidence_interval(system2_f1, random_state=42)

        # System 1 should have higher mean
        self.assertGreater(ci1['mean'], ci2['mean'])

        # CIs should not be degenerate
        self.assertLess(ci1['lower'], ci1['upper'])
        self.assertLess(ci2['lower'], ci2['upper'])


class TestErrorHandling(unittest.TestCase):
    """Tests for error handling and edge cases"""

    def test_invalid_match_strategy(self):
        """Test handling of invalid match strategy"""
        # Should log warning but not crash
        results = match_entities(
            ['protein A'],
            ['protein A'],
            strategies=['invalid_strategy']
        )

        # Should still return valid structure
        self.assertIn('match_count', results)
        self.assertIn('matched_pairs', results)

    def test_malformed_json_entities(self):
        """Test parsing malformed JSON"""
        # Should fall back to comma-separated parsing
        result = parse_entity_list('[protein A, gene B')  # Malformed JSON
        self.assertIsInstance(result, list)

    def test_none_entities_in_metrics(self):
        """Test metrics calculation with None values"""
        metrics = entity_level_metrics(
            [None, 'protein A', None],
            ['protein A', None, 'gene B']
        )

        # Should filter out None values and still calculate
        self.assertGreaterEqual(metrics['f1'], 0.0)
        self.assertLessEqual(metrics['f1'], 1.0)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestScript02Functions))
    suite.addTests(loader.loadTestsFromTestCase(TestScript03Functions))
    suite.addTests(loader.loadTestsFromTestCase(TestScript04Functions))
    suite.addTests(loader.loadTestsFromTestCase(TestDataLoading))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
