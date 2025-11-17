#!/usr/bin/env python3
"""
Phase 5.3: Benchmark Hybrid Pipeline Speed
===========================================

Benchmarks speed of:
1. EntityRuler only
2. Statistical NER only
3. Hybrid pipeline

Expected:
- EntityRuler only: 150-200 papers/sec (very fast)
- Statistical NER only: 30-50 papers/sec (slower)
- Hybrid: 40-60 papers/sec (statistical component is bottleneck)
"""

import spacy
import pandas as pd
import time
import os
from pathlib import Path

# Configuration
PATTERNS_PATH = "spacy_hybrid_ner/data/patterns.jsonl"
STATISTICAL_MODEL_PATH = "collab_results/experiment_archives/2025-11-12-3uubs8/spacy_model/model-best"
HYBRID_MODEL_PATH = "spacy_hybrid_ner/models/ner_hybrid_v2_com_ful"
TEST_DATA_PATH = "spacy_hybrid_ner/data/ner_corpus_splits/test.csv"
OUTPUT_DIR = "spacy_hybrid_ner/results/phase5_speed_benchmark"

# Benchmark size (use subset for speed)
BENCHMARK_SIZE = 100


def load_models():
    """
    Load all three models for benchmarking.

    Returns:
        Tuple of (ruler_only, statistical_only, hybrid)
    """
    print("Loading models...")

    # 1. EntityRuler only
    print("  1. EntityRuler only...")
    nlp_ruler = spacy.blank("en")
    nlp_ruler.add_pipe("entity_ruler").from_disk(PATTERNS_PATH)
    print(f"     ✓ {len(nlp_ruler.get_pipe('entity_ruler').patterns):,} patterns")

    # 2. Statistical NER only
    print("  2. Statistical NER only...")
    nlp_statistical = spacy.load(STATISTICAL_MODEL_PATH)
    print(f"     ✓ Loaded")

    # 3. Hybrid
    print("  3. Hybrid pipeline...")
    nlp_hybrid = spacy.load(HYBRID_MODEL_PATH)
    print(f"     ✓ Components: {nlp_hybrid.pipe_names}")

    return nlp_ruler, nlp_statistical, nlp_hybrid


def benchmark_model(nlp, name: str, texts: list):
    """
    Benchmark a model on test texts.

    Args:
        nlp: spaCy pipeline
        name: Model name
        texts: List of text strings

    Returns:
        Dictionary with benchmark results
    """
    print(f"\nBenchmarking {name}...")

    # Warmup
    for text in texts[:5]:
        _ = nlp(text)

    # Benchmark
    start = time.time()
    entity_count = 0

    for text in texts:
        doc = nlp(text)
        entity_count += len(doc.ents)

    end = time.time()

    elapsed = end - start
    papers_per_sec = len(texts) / elapsed
    ms_per_paper = (elapsed / len(texts)) * 1000

    results = {
        'model': name,
        'papers': len(texts),
        'time_sec': round(elapsed, 2),
        'papers_per_sec': round(papers_per_sec, 2),
        'ms_per_paper': round(ms_per_paper, 2),
        'total_entities': entity_count,
        'entities_per_paper': round(entity_count / len(texts), 2)
    }

    print(f"  ✓ {papers_per_sec:.2f} papers/sec ({ms_per_paper:.2f} ms/paper)")
    print(f"    Total entities: {entity_count:,} ({results['entities_per_paper']:.2f} per paper)")

    return results


def print_benchmark_report(results: list):
    """
    Print benchmark comparison report.

    Args:
        results: List of benchmark result dictionaries
    """
    df = pd.DataFrame(results)

    print("\n" + "="*80)
    print("SPEED BENCHMARK COMPARISON (PHASE 5.3)")
    print("="*80)

    print(f"\nBenchmark Size: {df['papers'].iloc[0]} papers")

    print(f"\n{'-'*80}")
    print(f"{'Model':<30} {'Time (s)':<12} {'Papers/sec':<15} {'ms/paper':<15}")
    print(f"{'-'*80}")

    for _, row in df.iterrows():
        print(f"{row['model']:<30} {row['time_sec']:<12.2f} {row['papers_per_sec']:<15.2f} {row['ms_per_paper']:<15.2f}")

    print(f"{'-'*80}")

    # Calculate speedup
    hybrid_speed = df[df['model'] == 'Hybrid Pipeline']['papers_per_sec'].iloc[0]
    ruler_speed = df[df['model'] == 'EntityRuler Only']['papers_per_sec'].iloc[0]
    statistical_speed = df[df['model'] == 'Statistical NER Only']['papers_per_sec'].iloc[0]

    print(f"\nSpeedup Analysis:")
    print(f"  EntityRuler vs Hybrid: {ruler_speed / hybrid_speed:.2f}x faster")
    print(f"  Hybrid vs Statistical: {hybrid_speed / statistical_speed:.2f}x faster")

    print(f"\nℹ️  Interpretation:")
    print(f"  - EntityRuler is very fast (rule-based matching)")
    print(f"  - Statistical NER is slower (neural network inference)")
    print(f"  - Hybrid speed ≈ Statistical speed (NER is bottleneck)")

    # Expected ranges
    print(f"\n{'-'*80}")
    print("TARGET ASSESSMENT:")
    print(f"{'-'*80}")

    targets = [
        ("EntityRuler", ruler_speed, 150, 200),
        ("Statistical NER", statistical_speed, 30, 50),
        ("Hybrid", hybrid_speed, 40, 60),
    ]

    for name, value, min_val, max_val in targets:
        # Be flexible with targets (allow 50% deviation)
        if min_val * 0.5 <= value <= max_val * 1.5:
            status = "✓"
        else:
            status = "~"
        print(f"{status} {name}: {value:.1f} papers/sec (Expected: {min_val}-{max_val})")


def save_results(results: list, output_dir: str):
    """
    Save benchmark results.

    Args:
        results: List of benchmark results
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)

    df = pd.DataFrame(results)

    # Save CSV
    csv_path = os.path.join(output_dir, 'speed_benchmark.csv')
    df.to_csv(csv_path, index=False)
    print(f"\n✓ Results saved to: {csv_path}")


def main():
    """Main execution function."""
    print("="*80)
    print("PHASE 5.3: BENCHMARK HYBRID PIPELINE SPEED")
    print("="*80)

    # Load test data
    print(f"\nLoading test data from: {TEST_DATA_PATH}")
    test_df = pd.read_csv(TEST_DATA_PATH).head(BENCHMARK_SIZE)

    # Get texts
    if 'text' in test_df.columns:
        texts = test_df['text'].tolist()
    else:
        texts = (test_df['title'].fillna('') + ' ' + test_df['abstract'].fillna('')).tolist()

    print(f"  ✓ Loaded {len(texts)} texts for benchmarking")

    # Load models
    nlp_ruler, nlp_statistical, nlp_hybrid = load_models()

    # Benchmark each model
    results = []
    results.append(benchmark_model(nlp_ruler, 'EntityRuler Only', texts))
    results.append(benchmark_model(nlp_statistical, 'Statistical NER Only', texts))
    results.append(benchmark_model(nlp_hybrid, 'Hybrid Pipeline', texts))

    # Print report
    print_benchmark_report(results)

    # Save results
    save_results(results, OUTPUT_DIR)

    print("\n" + "="*80)
    print("✓ PHASE 5.3 COMPLETE")
    print("="*80)
    print(f"\nResults saved to: {OUTPUT_DIR}/")
    print("\nNext: Phase 5.4 - Analyze alias resolution")


if __name__ == "__main__":
    main()
