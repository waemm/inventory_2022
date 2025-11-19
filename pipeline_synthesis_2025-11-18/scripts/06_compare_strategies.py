#!/usr/bin/env python3
"""
Compare Three Filtering Strategies

Compare performance of three paper filtering approaches:
- Set A (Linguistic): Rule-based linguistic features (ling_score >= 3)
- Set B (SetFit): ML-based confidence filtering (confidence >= 0.60)
- Set C (Union): Combined approach (A + B)

Analyze overlap patterns, unique contributions, and entity coverage.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Paths
BASE_DIR = Path("/Users/warren/development/GBC/inventory_2022")
PAPER_SETS_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/data/paper_sets"
ENTITY_INVENTORIES_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/data/entity_inventories"
BASELINE_COMPARISON_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/results/baseline_comparison"
GCBR_TRACKING_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/results/gcbr_tracking"

# Output directory
OUTPUT_DIR = BASE_DIR / "pipeline_synthesis_2025-11-18/results/strategy_comparison"

def load_paper_sets():
    """Load all three paper sets"""
    print("Loading paper sets...")

    df_a = pd.read_csv(PAPER_SETS_DIR / "set_a_linguistic.csv")
    df_b = pd.read_csv(PAPER_SETS_DIR / "set_b_setfit.csv")
    df_c = pd.read_csv(PAPER_SETS_DIR / "set_c_union.csv")

    print(f"  Set A (Linguistic): {len(df_a):,} papers")
    print(f"  Set B (SetFit):     {len(df_b):,} papers")
    print(f"  Set C (Union):      {len(df_c):,} papers")

    return df_a, df_b, df_c

def load_entity_inventories():
    """Load entity inventories for all three sets"""
    print("\nLoading entity inventories...")

    df_a = pd.read_csv(ENTITY_INVENTORIES_DIR / "set_a_entity_inventory.csv")
    df_b = pd.read_csv(ENTITY_INVENTORIES_DIR / "set_b_entity_inventory.csv")
    df_c = pd.read_csv(ENTITY_INVENTORIES_DIR / "set_c_entity_inventory.csv")

    print(f"  Set A entities: {len(df_a):,}")
    print(f"  Set B entities: {len(df_b):,}")
    print(f"  Set C entities: {len(df_c):,}")

    return df_a, df_b, df_c

def load_baseline_comparison():
    """Load baseline comparison results"""
    print("\nLoading baseline comparison...")

    with open(BASELINE_COMPARISON_DIR / "baseline_coverage_stats.json", 'r') as f:
        stats = json.load(f)

    print(f"  Baseline total: {stats['baseline_total']:,}")
    print(f"  Set A coverage: {stats['exact_coverage_percent']['set_a']:.1f}%")
    print(f"  Set B coverage: {stats['exact_coverage_percent']['set_b']:.1f}%")
    print(f"  Set C coverage: {stats['exact_coverage_percent']['set_c']:.1f}%")

    return stats

def load_gcbr_tracking():
    """Load GCBR tracking results"""
    print("\nLoading GCBR tracking...")

    df_gcbr = pd.read_csv(GCBR_TRACKING_DIR / "gcbr_tracking_complete.csv")

    with open(GCBR_TRACKING_DIR / "gcbr_tracking_summary.json", 'r') as f:
        stats = json.load(f)

    print(f"  Total GCBRs: {len(df_gcbr)}")
    print(f"  Captured in final: {stats['capture_stats']['full_capture']}")

    return df_gcbr, stats

def analyze_paper_overlap(df_a, df_b, df_c):
    """Analyze overlap patterns between paper sets"""
    print("\n" + "="*80)
    print("PAPER SET OVERLAP ANALYSIS")
    print("="*80)

    # Create PMID sets
    pmids_a = set(df_a['pmid'])
    pmids_b = set(df_b['pmid'])
    pmids_c = set(df_c['pmid'])

    # Calculate overlaps
    both_ab = pmids_a & pmids_b
    only_a = pmids_a - pmids_b
    only_b = pmids_b - pmids_a

    overlap_stats = {
        'set_a_total': len(pmids_a),
        'set_b_total': len(pmids_b),
        'set_c_total': len(pmids_c),
        'both_ab': len(both_ab),
        'only_a': len(only_a),
        'only_b': len(only_b),
        'overlap_percent': round(len(both_ab) / len(pmids_c) * 100, 2),
        'a_only_percent': round(len(only_a) / len(pmids_c) * 100, 2),
        'b_only_percent': round(len(only_b) / len(pmids_c) * 100, 2)
    }

    print(f"\nOverlap Analysis:")
    print(f"  Both methods (A ∩ B):     {len(both_ab):,} ({overlap_stats['overlap_percent']}%)")
    print(f"  Linguistic only (A - B):  {len(only_a):,} ({overlap_stats['a_only_percent']}%)")
    print(f"  SetFit only (B - A):      {len(only_b):,} ({overlap_stats['b_only_percent']}%)")
    print(f"  Union (A ∪ B):            {len(pmids_c):,} (100.0%)")

    return overlap_stats, both_ab, only_a, only_b

def analyze_entity_coverage(df_a_ent, df_b_ent, df_c_ent):
    """Analyze entity coverage across strategies"""
    print("\n" + "="*80)
    print("ENTITY COVERAGE ANALYSIS")
    print("="*80)

    # Create entity name sets
    entities_a = set(df_a_ent['entity_name'])
    entities_b = set(df_b_ent['entity_name'])
    entities_c = set(df_c_ent['entity_name'])

    # Calculate overlaps
    both_ab = entities_a & entities_b
    only_a = entities_a - entities_b
    only_b = entities_b - entities_a

    entity_stats = {
        'set_a_entities': len(entities_a),
        'set_b_entities': len(entities_b),
        'set_c_entities': len(entities_c),
        'both_ab_entities': len(both_ab),
        'only_a_entities': len(only_a),
        'only_b_entities': len(only_b),
        'overlap_percent': round(len(both_ab) / len(entities_c) * 100, 2),
        'a_only_percent': round(len(only_a) / len(entities_c) * 100, 2),
        'b_only_percent': round(len(only_b) / len(entities_c) * 100, 2)
    }

    print(f"\nEntity Overlap:")
    print(f"  Both methods (A ∩ B):     {len(both_ab):,} ({entity_stats['overlap_percent']}%)")
    print(f"  Linguistic only (A - B):  {len(only_a):,} ({entity_stats['a_only_percent']}%)")
    print(f"  SetFit only (B - A):      {len(only_b):,} ({entity_stats['b_only_percent']}%)")
    print(f"  Union (A ∪ B):            {len(entities_c):,} (100.0%)")

    # Top entities by paper count
    top_a = df_a_ent.nlargest(10, 'total_papers')[['entity_name', 'total_papers']]
    top_b = df_b_ent.nlargest(10, 'total_papers')[['entity_name', 'total_papers']]
    top_c = df_c_ent.nlargest(10, 'total_papers')[['entity_name', 'total_papers']]

    print(f"\nTop 10 Entities (by paper count):")
    print(f"\n  Set A (Linguistic):")
    for idx, (_, row) in enumerate(top_a.iterrows(), 1):
        print(f"    {idx}. {row['entity_name']} ({row['total_papers']} papers)")

    print(f"\n  Set B (SetFit):")
    for idx, (_, row) in enumerate(top_b.iterrows(), 1):
        print(f"    {idx}. {row['entity_name']} ({row['total_papers']} papers)")

    print(f"\n  Set C (Union):")
    for idx, (_, row) in enumerate(top_c.iterrows(), 1):
        print(f"    {idx}. {row['entity_name']} ({row['total_papers']} papers)")

    return entity_stats

def analyze_baseline_performance(baseline_stats):
    """Analyze baseline coverage performance"""
    print("\n" + "="*80)
    print("BASELINE COVERAGE PERFORMANCE")
    print("="*80)

    coverage_a = baseline_stats['exact_coverage_percent']['set_a']
    coverage_b = baseline_stats['exact_coverage_percent']['set_b']
    coverage_c = baseline_stats['exact_coverage_percent']['set_c']

    # Calculate improvement
    improvement_c_over_a = coverage_c - coverage_a
    improvement_c_over_b = coverage_c - coverage_b

    print(f"\nBaseline Coverage (2022 → 2011-2021):")
    print(f"  Set A (Linguistic): {coverage_a:.1f}%")
    print(f"  Set B (SetFit):     {coverage_b:.1f}%")
    print(f"  Set C (Union):      {coverage_c:.1f}%")

    print(f"\nImprovement from Union:")
    print(f"  vs Linguistic: +{improvement_c_over_a:.1f}% ({baseline_stats['exact_matches']['set_c'] - baseline_stats['exact_matches']['set_a']} more resources)")
    print(f"  vs SetFit:     +{improvement_c_over_b:.1f}% ({baseline_stats['exact_matches']['set_c'] - baseline_stats['exact_matches']['set_b']} more resources)")

    baseline_performance = {
        'coverage_a': coverage_a,
        'coverage_b': coverage_b,
        'coverage_c': coverage_c,
        'improvement_c_over_a': round(improvement_c_over_a, 2),
        'improvement_c_over_b': round(improvement_c_over_b, 2),
        'additional_resources_vs_a': baseline_stats['exact_matches']['set_c'] - baseline_stats['exact_matches']['set_a'],
        'additional_resources_vs_b': baseline_stats['exact_matches']['set_c'] - baseline_stats['exact_matches']['set_b']
    }

    return baseline_performance

def analyze_gcbr_performance(df_gcbr, gcbr_stats):
    """Analyze GCBR capture performance"""
    print("\n" + "="*80)
    print("GCBR CAPTURE PERFORMANCE")
    print("="*80)

    # Count GCBRs captured in each set
    gcbrs_in_a = len(df_gcbr[df_gcbr['s8_linguistic'] > 0])
    gcbrs_in_b = len(df_gcbr[df_gcbr['s9_setfit'] > 0])
    gcbrs_in_c = len(df_gcbr[df_gcbr['s10_union'] > 0])

    # Total papers for captured GCBRs
    papers_a = df_gcbr['s8_linguistic'].sum()
    papers_b = df_gcbr['s9_setfit'].sum()
    papers_c = df_gcbr['s10_union'].sum()

    print(f"\nGCBRs Captured (>0 papers):")
    print(f"  Set A (Linguistic): {gcbrs_in_a} / 52 ({gcbrs_in_a/52*100:.1f}%)")
    print(f"  Set B (SetFit):     {gcbrs_in_b} / 52 ({gcbrs_in_b/52*100:.1f}%)")
    print(f"  Set C (Union):      {gcbrs_in_c} / 52 ({gcbrs_in_c/52*100:.1f}%)")

    print(f"\nTotal GCBR Papers:")
    print(f"  Set A (Linguistic): {papers_a:,} papers")
    print(f"  Set B (SetFit):     {papers_b:,} papers")
    print(f"  Set C (Union):      {papers_c:,} papers")

    # GCBRs unique to each set
    gcbrs_only_a = df_gcbr[(df_gcbr['s8_linguistic'] > 0) & (df_gcbr['s9_setfit'] == 0)]
    gcbrs_only_b = df_gcbr[(df_gcbr['s9_setfit'] > 0) & (df_gcbr['s8_linguistic'] == 0)]
    gcbrs_both = df_gcbr[(df_gcbr['s8_linguistic'] > 0) & (df_gcbr['s9_setfit'] > 0)]

    print(f"\nGCBR Overlap:")
    print(f"  Both methods:        {len(gcbrs_both)} GCBRs")
    print(f"  Linguistic only:     {len(gcbrs_only_a)} GCBRs")
    print(f"  SetFit only:         {len(gcbrs_only_b)} GCBRs")

    gcbr_performance = {
        'gcbrs_in_a': gcbrs_in_a,
        'gcbrs_in_b': gcbrs_in_b,
        'gcbrs_in_c': gcbrs_in_c,
        'papers_a': int(papers_a),
        'papers_b': int(papers_b),
        'papers_c': int(papers_c),
        'gcbrs_both': len(gcbrs_both),
        'gcbrs_only_a': len(gcbrs_only_a),
        'gcbrs_only_b': len(gcbrs_only_b)
    }

    return gcbr_performance

def generate_strategy_recommendations(paper_overlap, entity_coverage, baseline_perf, gcbr_perf):
    """Generate strategic recommendations based on analysis"""
    print("\n" + "="*80)
    print("STRATEGIC RECOMMENDATIONS")
    print("="*80)

    recommendations = []

    # Recommendation 1: Union approach
    if baseline_perf['coverage_c'] > 95:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Strategy Selection',
            'recommendation': 'Adopt Union (Set C) approach as primary filtering strategy',
            'justification': f"Achieves {baseline_perf['coverage_c']:.1f}% baseline coverage, " +
                           f"capturing {baseline_perf['improvement_c_over_a']:.1f}% more resources than Linguistic alone " +
                           f"and {baseline_perf['improvement_c_over_b']:.1f}% more than SetFit alone."
        })

    # Recommendation 2: Low overlap
    if paper_overlap['overlap_percent'] < 1.0:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Method Complementarity',
            'recommendation': 'Leverage complementary nature of Linguistic and SetFit methods',
            'justification': f"Only {paper_overlap['overlap_percent']:.1f}% overlap indicates methods capture " +
                           "fundamentally different types of introduction papers. Union maximizes coverage."
        })

    # Recommendation 3: GCBR performance
    if gcbr_perf['gcbrs_in_c'] > gcbr_perf['gcbrs_in_a']:
        additional_gcbrs = gcbr_perf['gcbrs_in_c'] - gcbr_perf['gcbrs_in_a']
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'High-Priority Resources',
            'recommendation': 'Union approach captures more GCBRs than either method alone',
            'justification': f"Union captures {additional_gcbrs} additional GCBRs compared to Linguistic only, " +
                           f"improving high-priority resource detection by {additional_gcbrs/52*100:.1f}%."
        })

    # Recommendation 4: Entity diversity
    if entity_coverage['set_c_entities'] > entity_coverage['set_a_entities'] * 1.5:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Resource Discovery',
            'recommendation': 'Union approach discovers significantly more unique resources',
            'justification': f"Union identifies {entity_coverage['set_c_entities']:,} unique entities, " +
                           f"{entity_coverage['set_c_entities'] - entity_coverage['set_a_entities']:,} more than Linguistic alone."
        })

    # Print recommendations
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec['priority']}] {rec['category']}")
        print(f"   Recommendation: {rec['recommendation']}")
        print(f"   Justification: {rec['justification']}")

    return recommendations

def main():
    print("=" * 80)
    print("STRATEGY COMPARISON: LINGUISTIC vs SETFIT vs UNION")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load all data
    df_a, df_b, df_c = load_paper_sets()
    df_a_ent, df_b_ent, df_c_ent = load_entity_inventories()
    baseline_stats = load_baseline_comparison()
    df_gcbr, gcbr_stats = load_gcbr_tracking()

    # Perform analyses
    paper_overlap, both_papers, only_a_papers, only_b_papers = analyze_paper_overlap(df_a, df_b, df_c)
    entity_coverage = analyze_entity_coverage(df_a_ent, df_b_ent, df_c_ent)
    baseline_perf = analyze_baseline_performance(baseline_stats)
    gcbr_perf = analyze_gcbr_performance(df_gcbr, gcbr_stats)
    recommendations = generate_strategy_recommendations(paper_overlap, entity_coverage, baseline_perf, gcbr_perf)

    # Save comprehensive comparison
    comparison_summary = {
        'timestamp': datetime.now().isoformat(),
        'paper_overlap': paper_overlap,
        'entity_coverage': entity_coverage,
        'baseline_performance': baseline_perf,
        'gcbr_performance': gcbr_perf,
        'recommendations': recommendations
    }

    summary_file = OUTPUT_DIR / "strategy_comparison_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(comparison_summary, f, indent=2)
    print(f"\n\nSaved: {summary_file}")

    # Save overlap details
    overlap_details = {
        'both_papers': len(both_papers),
        'only_a_papers': len(only_a_papers),
        'only_b_papers': len(only_b_papers)
    }

    overlap_file = OUTPUT_DIR / "paper_overlap_details.json"
    with open(overlap_file, 'w') as f:
        json.dump(overlap_details, f, indent=2)
    print(f"Saved: {overlap_file}")

    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
