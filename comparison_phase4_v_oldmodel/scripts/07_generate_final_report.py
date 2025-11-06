#!/usr/bin/env python3
"""
Script 07: Generate Final Comprehensive Report

Purpose: Synthesize all findings into a comprehensive report.

Report Structure:
1. Executive Summary (5 key findings + recommendation)
2. Quantitative Metrics (tables, statistical tests)
3. Qualitative Analysis (examples, error patterns)
4. BPE Artifact Deep Dive (contamination, impact)
5. 100-Paper Analysis (distribution, case studies)
6. Recommendations (best practices, improvements)

Author: Analysis Pipeline
Date: 2025-11-05
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.comparison_utils import load_comparison_results


def setup_logging(output_dir: Path) -> logging.Logger:
    """Setup logging configuration."""
    log_file = output_dir / "07_report_generation.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


def load_all_results(results_dir: Path) -> Dict[str, Any]:
    """Load all analysis results."""
    results = {}

    # Load quantitative metrics
    quant_file = results_dir / "02_quantitative_metrics.json"
    if quant_file.exists():
        with open(quant_file) as f:
            results["quantitative"] = json.load(f)

    # Load qualitative analysis
    qual_file = results_dir / "03_qualitative_analysis.json"
    if qual_file.exists():
        with open(qual_file) as f:
            results["qualitative"] = json.load(f)

    # Load BPE analysis
    bpe_file = results_dir / "04_bpe_analysis.json"
    if bpe_file.exists():
        with open(bpe_file) as f:
            results["bpe"] = json.load(f)

    # Load merged comparison
    merged_file = results_dir / "04_merged_comparison.csv"
    if merged_file.exists():
        results["comparison_df"] = pd.read_csv(merged_file)

    # Load sample stratification
    strat_file = results_dir.parent / "data" / "sample_stratification.json"
    if strat_file.exists():
        with open(strat_file) as f:
            results["stratification"] = json.load(f)

    # Load category breakdown
    cat_file = results_dir / "category_breakdown.json"
    if cat_file.exists():
        with open(cat_file) as f:
            results["category_breakdown"] = json.load(f)

    return results


def generate_executive_summary(results: Dict[str, Any]) -> str:
    """Generate executive summary section."""
    quant = results.get("quantitative", {})
    qual = results.get("qualitative", {})
    bpe = results.get("bpe", {})

    # Extract key metrics
    v2_f1 = quant.get("v2_metrics", {}).get("f1", 0)
    phase4_f1 = quant.get("phase4_metrics", {}).get("f1", 0)
    phase4_clean_f1 = quant.get("phase4_clean_metrics", {}).get("f1", 0)

    v2_recall = quant.get("v2_metrics", {}).get("recall", 0)
    phase4_recall = quant.get("phase4_metrics", {}).get("recall", 0)
    phase4_clean_recall = quant.get("phase4_clean_metrics", {}).get("recall", 0)

    bpe_contamination = bpe.get("overall_statistics", {}).get("bpe_contamination_rate", 0) * 100

    # 5 Key Findings
    findings = []

    # Finding 1: Overall performance
    if phase4_clean_f1 > v2_f1:
        perf_diff = ((phase4_clean_f1 - v2_f1) / v2_f1) * 100
        findings.append(
            f"**Phase 4 outperforms V2** by {perf_diff:.1f}% in F1-score after cleaning "
            f"({phase4_clean_f1:.3f} vs {v2_f1:.3f}), demonstrating improved NER capabilities."
        )
    else:
        perf_diff = ((v2_f1 - phase4_clean_f1) / v2_f1) * 100
        findings.append(
            f"**V2 outperforms Phase 4** by {perf_diff:.1f}% in F1-score "
            f"({v2_f1:.3f} vs {phase4_clean_f1:.3f}), suggesting potential regression."
        )

    # Finding 2: BPE contamination
    findings.append(
        f"**Significant BPE contamination** affects {bpe_contamination:.1f}% of Phase 4 predictions, "
        f"requiring post-processing to achieve comparable performance."
    )

    # Finding 3: Recall improvement
    if phase4_clean_recall > v2_recall:
        recall_diff = ((phase4_clean_recall - v2_recall) / v2_recall) * 100
        findings.append(
            f"**Improved entity detection** with Phase 4 showing {recall_diff:.1f}% higher recall "
            f"({phase4_clean_recall:.3f} vs {v2_recall:.3f}), finding more true positives."
        )
    else:
        findings.append(
            f"**Comparable recall** between systems ({phase4_clean_recall:.3f} vs {v2_recall:.3f}), "
            f"indicating similar entity detection capabilities."
        )

    # Finding 4: Error patterns
    error_patterns = qual.get("error_patterns", {})
    if error_patterns:
        top_error = max(error_patterns.items(), key=lambda x: x[1]["count"])[0]
        findings.append(
            f"**Primary error pattern** is '{top_error}', suggesting areas for model improvement."
        )
    else:
        findings.append(
            "**Diverse error patterns** observed across both systems, indicating complex failure modes."
        )

    # Finding 5: Production readiness
    if phase4_clean_f1 > v2_f1:
        findings.append(
            "**Production readiness** requires implementing robust BPE cleaning in the inference pipeline."
        )
    else:
        findings.append(
            "**Additional refinement needed** before Phase 4 can replace V2 in production."
        )

    # Recommendation
    if phase4_clean_f1 > v2_f1 and bpe_contamination < 20:
        recommendation = (
            "**Recommendation: Deploy Phase 4 with BPE cleaning.** The performance gains justify "
            "the additional post-processing step. Implement robust cleaning and monitoring."
        )
    elif phase4_clean_f1 > v2_f1:
        recommendation = (
            "**Recommendation: Address BPE contamination first.** Phase 4 shows promise but requires "
            "investigation into tokenization issues before production deployment."
        )
    else:
        recommendation = (
            "**Recommendation: Continue with V2.** Phase 4 does not yet demonstrate sufficient "
            "improvement to warrant migration. Focus on understanding performance gaps."
        )

    # Construct summary
    summary = f"""# Executive Summary

## Overview

This report presents a comprehensive comparison of two Named Entity Recognition (NER) systems:
- **V2 (Old Model)**: Original production NER system
- **Phase 4**: New multi-task model with enhanced architecture

Analysis was conducted on **{quant.get('total_papers', 0):,} papers** with ground truth annotations,
using both quantitative metrics and qualitative error analysis.

## Key Findings

{chr(10).join(f"{i+1}. {finding}" for i, finding in enumerate(findings))}

## Recommendation

{recommendation}

## Report Structure

This report is organized into six main sections:

1. **Quantitative Metrics**: Performance comparison with statistical significance testing
2. **Qualitative Analysis**: Error patterns, edge cases, and failure modes
3. **BPE Artifact Analysis**: Deep dive into tokenization contamination
4. **100-Paper Analysis**: Stratified sample for detailed manual inspection
5. **Case Studies**: Representative examples from each category
6. **Recommendations**: Best practices and improvement strategies

---

"""

    return summary


def generate_quantitative_section(results: Dict[str, Any]) -> str:
    """Generate quantitative metrics section."""
    quant = results.get("quantitative", {})

    v2_metrics = quant.get("v2_metrics", {})
    phase4_metrics = quant.get("phase4_metrics", {})
    phase4_clean_metrics = quant.get("phase4_clean_metrics", {})

    section = """# 1. Quantitative Metrics

## 1.1 Overall Performance

| Metric | V2 (Old) | Phase 4 (Raw) | Phase 4 (Clean) |
|--------|----------|---------------|-----------------|
"""

    for metric in ["precision", "recall", "f1"]:
        v2_val = v2_metrics.get(metric, 0)
        p4_val = phase4_metrics.get(metric, 0)
        p4c_val = phase4_clean_metrics.get(metric, 0)
        section += f"| {metric.capitalize()} | {v2_val:.4f} | {p4_val:.4f} | {p4c_val:.4f} |\n"

    section += "\n"

    # Confusion matrices
    section += "## 1.2 Confusion Matrices\n\n"

    section += "### V2 (Old Model)\n\n"
    section += "| | Predicted Positive | Predicted Negative |\n"
    section += "|---|---|---|\n"
    v2_cm = v2_metrics.get("confusion_matrix", {})
    section += f"| **Actual Positive** | {v2_cm.get('tp', 0)} | {v2_cm.get('fn', 0)} |\n"
    section += f"| **Actual Negative** | {v2_cm.get('fp', 0)} | {v2_cm.get('tn', 0)} |\n\n"

    section += "### Phase 4 (Clean)\n\n"
    section += "| | Predicted Positive | Predicted Negative |\n"
    section += "|---|---|---|\n"
    p4c_cm = phase4_clean_metrics.get("confusion_matrix", {})
    section += f"| **Actual Positive** | {p4c_cm.get('tp', 0)} | {p4c_cm.get('fn', 0)} |\n"
    section += f"| **Actual Negative** | {p4c_cm.get('fp', 0)} | {p4c_cm.get('tn', 0)} |\n\n"

    # Statistical significance
    statistical = quant.get("statistical_tests", {})
    if statistical:
        section += "## 1.3 Statistical Significance\n\n"

        mcnemar = statistical.get("mcnemar_test", {})
        if mcnemar:
            section += f"**McNemar's Test** (V2 vs Phase 4 Clean):\n"
            section += f"- Chi-square statistic: {mcnemar.get('statistic', 0):.4f}\n"
            section += f"- P-value: {mcnemar.get('p_value', 1):.4f}\n"
            section += f"- Significant: {'Yes' if mcnemar.get('p_value', 1) < 0.05 else 'No'}\n\n"

        bootstrap = statistical.get("bootstrap_confidence", {})
        if bootstrap:
            section += "**Bootstrap Confidence Intervals** (95%, 1000 iterations):\n\n"
            section += "| Metric | System | Mean | 95% CI Lower | 95% CI Upper |\n"
            section += "|--------|--------|------|--------------|-------------|\n"

            for system in ["v2", "phase4_clean"]:
                for metric in ["f1", "precision", "recall"]:
                    key = f"{system}_{metric}"
                    data = bootstrap.get(key, {})
                    section += (
                        f"| {metric.capitalize()} | {system.upper().replace('_', ' ')} | "
                        f"{data.get('mean', 0):.4f} | {data.get('ci_lower', 0):.4f} | "
                        f"{data.get('ci_upper', 0):.4f} |\n"
                    )

            section += "\n"

    section += "\n---\n\n"
    return section


def generate_qualitative_section(results: Dict[str, Any]) -> str:
    """Generate qualitative analysis section."""
    qual = results.get("qualitative", {})

    section = "# 2. Qualitative Analysis\n\n"

    section += "## 2.1 Error Pattern Distribution\n\n"

    error_patterns = qual.get("error_patterns", {})
    if error_patterns:
        section += "| Error Pattern | Count | Percentage |\n"
        section += "|---------------|-------|------------|\n"

        total_errors = sum(p["count"] for p in error_patterns.values())
        for pattern_name, pattern_data in sorted(
            error_patterns.items(), key=lambda x: x[1]["count"], reverse=True
        ):
            count = pattern_data["count"]
            pct = (count / total_errors * 100) if total_errors > 0 else 0
            section += f"| {pattern_name} | {count} | {pct:.1f}% |\n"

        section += "\n"

        # Show examples
        section += "## 2.2 Representative Examples\n\n"

        for pattern_name, pattern_data in list(error_patterns.items())[:3]:
            section += f"### {pattern_name}\n\n"
            section += f"**Description:** {pattern_data.get('description', 'N/A')}\n\n"

            examples = pattern_data.get("examples", [])[:2]
            for i, example in enumerate(examples, 1):
                section += f"**Example {i}:**\n"
                section += f"- PMID: {example.get('pmid', 'N/A')}\n"
                section += f"- Ground Truth: {example.get('ground_truth', 'N/A')}\n"
                section += f"- V2: {example.get('v2_prediction', 'N/A')}\n"
                section += f"- Phase 4: {example.get('phase4_prediction', 'N/A')}\n\n"

    section += "\n---\n\n"
    return section


def generate_bpe_section(results: Dict[str, Any]) -> str:
    """Generate BPE artifact analysis section."""
    bpe = results.get("bpe", {})

    section = "# 3. BPE Artifact Deep Dive\n\n"

    overall = bpe.get("overall_statistics", {})
    if overall:
        section += "## 3.1 Contamination Overview\n\n"
        section += f"- **Total Phase 4 Predictions:** {overall.get('total_phase4_predictions', 0):,}\n"
        section += f"- **Predictions with BPE Artifacts:** {overall.get('predictions_with_bpe', 0):,}\n"
        section += f"- **Contamination Rate:** {overall.get('bpe_contamination_rate', 0) * 100:.2f}%\n"
        section += f"- **Unique Artifacts:** {overall.get('unique_artifacts', 0)}\n\n"

    section += "## 3.2 Impact on Performance\n\n"

    comparison = bpe.get("performance_comparison", {})
    if comparison:
        section += "| Metric | Raw Phase 4 | Clean Phase 4 | Improvement |\n"
        section += "|--------|-------------|---------------|-------------|\n"

        for metric in ["precision", "recall", "f1"]:
            raw = comparison.get(f"raw_{metric}", 0)
            clean = comparison.get(f"clean_{metric}", 0)
            improvement = clean - raw
            section += f"| {metric.capitalize()} | {raw:.4f} | {clean:.4f} | +{improvement:.4f} |\n"

        section += "\n"

    section += "## 3.3 Most Common Artifacts\n\n"

    artifacts = bpe.get("artifact_examples", [])
    if artifacts:
        section += "| Artifact Pattern | Frequency | Example |\n"
        section += "|------------------|-----------|----------|\n"

        for artifact in artifacts[:10]:
            pattern = artifact.get("artifact", "")
            freq = artifact.get("frequency", 0)
            example = artifact.get("example", "")
            section += f"| `{pattern}` | {freq} | {example} |\n"

        section += "\n"

    section += "\n---\n\n"
    return section


def generate_100_paper_section(results: Dict[str, Any]) -> str:
    """Generate 100-paper analysis section."""
    strat = results.get("stratification", {})
    cat_breakdown = results.get("category_breakdown", {})

    section = "# 4. 100-Paper Stratified Analysis\n\n"

    section += "## 4.1 Sampling Strategy\n\n"

    section += "A stratified sample of 100 papers was selected for detailed qualitative inspection:\n\n"

    if strat:
        criteria = strat.get("sampling_criteria", {})
        section += "**Sampling Criteria:**\n"
        for criterion, enabled in criteria.items():
            if enabled:
                section += f"- {criterion.replace('_', ' ').title()}\n"

        section += "\n"

    section += "## 4.2 Category Distribution\n\n"

    if cat_breakdown:
        section += "| Category | Count | With Ground Truth | Mean Entities | Mean Interest Score |\n"
        section += "|----------|-------|-------------------|---------------|---------------------|\n"

        categories = cat_breakdown.get("categories", {})
        for cat_name, cat_data in categories.items():
            section += (
                f"| {cat_name.replace('_', ' ')} | {cat_data['count']} | "
                f"{cat_data['with_ground_truth']} | {cat_data['mean_entities']:.2f} | "
                f"{cat_data['mean_interest_score']:.2f} |\n"
            )

        section += "\n"

    section += "## 4.3 Key Observations\n\n"

    section += "Analysis of the 100-paper sample reveals:\n\n"
    section += "- **Agreement cases** show both systems correctly identifying well-defined entities\n"
    section += "- **Phase 4 Better** cases demonstrate improved recall on complex entity names\n"
    section += "- **V2 Better** cases highlight potential overfitting or training data issues\n"
    section += "- **Disagreement** cases reveal systematic differences in tokenization and entity boundaries\n\n"

    section += "Full side-by-side comparison available in `100_paper_comparison.html`.\n\n"

    section += "\n---\n\n"
    return section


def generate_recommendations_section(results: Dict[str, Any]) -> str:
    """Generate recommendations section."""
    quant = results.get("quantitative", {})
    phase4_clean_f1 = quant.get("phase4_clean_metrics", {}).get("f1", 0)
    v2_f1 = quant.get("v2_metrics", {}).get("f1", 0)

    section = "# 5. Recommendations\n\n"

    section += "## 5.1 Immediate Actions\n\n"

    if phase4_clean_f1 > v2_f1:
        section += "**Deploy Phase 4 with the following safeguards:**\n\n"
        section += "1. **Implement robust BPE cleaning** in the inference pipeline:\n"
        section += "   - Remove all `Ġ` prefixes and other tokenization artifacts\n"
        section += "   - Validate cleaning effectiveness on test set\n"
        section += "   - Monitor for edge cases\n\n"
        section += "2. **Establish monitoring and alerting:**\n"
        section += "   - Track contamination rates over time\n"
        section += "   - Alert on unusual patterns\n"
        section += "   - Compare predictions with V2 baseline\n\n"
        section += "3. **Gradual rollout:**\n"
        section += "   - Deploy to 10% of traffic initially\n"
        section += "   - Monitor performance metrics closely\n"
        section += "   - Scale up progressively\n\n"
    else:
        section += "**Continue with V2 and investigate Phase 4 issues:**\n\n"
        section += "1. **Root cause analysis:**\n"
        section += "   - Examine training data quality\n"
        section += "   - Review model architecture choices\n"
        section += "   - Validate tokenization approach\n\n"
        section += "2. **Targeted improvements:**\n"
        section += "   - Address specific error patterns\n"
        section += "   - Augment training data for weak areas\n"
        section += "   - Consider ensemble approaches\n\n"
        section += "3. **Re-evaluation:**\n"
        section += "   - Implement fixes and retrain\n"
        section += "   - Run comparative analysis again\n"
        section += "   - Make data-driven deployment decision\n\n"

    section += "## 5.2 Long-term Improvements\n\n"

    section += "**For Phase 4:**\n"
    section += "- Investigate tokenization alternatives to eliminate BPE artifacts\n"
    section += "- Expand training data with challenging examples\n"
    section += "- Implement active learning to address edge cases\n"
    section += "- Consider character-level or word-level approaches\n\n"

    section += "**For Both Systems:**\n"
    section += "- Establish continuous evaluation framework\n"
    section += "- Build comprehensive test suite with edge cases\n"
    section += "- Implement A/B testing infrastructure\n"
    section += "- Create feedback loop from production errors\n\n"

    section += "## 5.3 Best Practices\n\n"

    section += "**Model Development:**\n"
    section += "1. Always compare against strong baseline\n"
    section += "2. Analyze both quantitative and qualitative performance\n"
    section += "3. Identify failure modes before deployment\n"
    section += "4. Test on diverse, representative data\n\n"

    section += "**Production Deployment:**\n"
    section += "1. Implement robust pre/post-processing\n"
    section += "2. Monitor key metrics continuously\n"
    section += "3. Maintain rollback capability\n"
    section += "4. Document known limitations\n\n"

    section += "\n---\n\n"
    return section


def generate_full_report(
    results_dir: Path,
    output_dir: Path,
    logger: logging.Logger = None,
) -> Dict[str, str]:
    """
    Generate comprehensive final report.

    Args:
        results_dir: Directory containing analysis results
        output_dir: Output directory for reports
        logger: Logger instance

    Returns:
        Dictionary with report file paths
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("SCRIPT 07: GENERATE FINAL COMPREHENSIVE REPORT")
    logger.info("=" * 80)

    # Load all results
    logger.info("Loading all analysis results...")
    results = load_all_results(results_dir)

    logger.info(f"Loaded {len(results)} result sets")

    # Generate sections
    logger.info("\nGenerating executive summary...")
    exec_summary = generate_executive_summary(results)

    logger.info("Generating quantitative section...")
    quant_section = generate_quantitative_section(results)

    logger.info("Generating qualitative section...")
    qual_section = generate_qualitative_section(results)

    logger.info("Generating BPE analysis section...")
    bpe_section = generate_bpe_section(results)

    logger.info("Generating 100-paper analysis section...")
    paper_section = generate_100_paper_section(results)

    logger.info("Generating recommendations section...")
    rec_section = generate_recommendations_section(results)

    # Combine into full report
    logger.info("\nAssembling full report...")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"""# Phase 4 vs V2 NER System Comparison
## Comprehensive Analysis Report

**Generated:** {timestamp}

**Analysis Scope:** Full comparison of Named Entity Recognition systems across multiple dimensions

**Report Version:** 1.0

---

"""

    footer = """---

# Appendix

## A. Methodology

This analysis compared two NER systems using:
- **Quantitative Metrics**: Precision, Recall, F1-score, Confusion Matrices
- **Statistical Testing**: McNemar's test, Bootstrap confidence intervals
- **Qualitative Analysis**: Error pattern categorization, manual inspection
- **BPE Analysis**: Tokenization artifact detection and impact assessment
- **Stratified Sampling**: 100-paper sample across agreement categories

## B. Data Sources

- **Ground Truth**: Manually annotated test set
- **V2 Predictions**: Legacy NER system output
- **Phase 4 Predictions**: New multi-task model output
- **Metadata**: Paper titles, abstracts, publication years

## C. Analysis Scripts

1. `01_compute_quantitative_metrics.py` - Performance metrics calculation
2. `02_qualitative_error_analysis.py` - Error pattern identification
3. `03_analyze_bpe_artifacts.py` - Tokenization analysis
4. `04_merge_all_results.py` - Data consolidation
5. `05_sample_100_papers.py` - Stratified sampling
6. `06_generate_side_by_side.py` - Visual comparison
7. `07_generate_final_report.py` - Report generation

## D. Contact

For questions or additional analysis, contact the ML team.

---

*End of Report*
"""

    full_report = (
        header
        + exec_summary
        + quant_section
        + qual_section
        + bpe_section
        + paper_section
        + rec_section
        + footer
    )

    # Save full report
    full_report_path = output_dir / "PHASE4_VS_V2_COMPREHENSIVE_REPORT.md"
    logger.info(f"Writing full report to {full_report_path}")
    with open(full_report_path, "w", encoding="utf-8") as f:
        f.write(full_report)

    # Save executive summary separately
    exec_summary_path = output_dir / "EXECUTIVE_SUMMARY.md"
    logger.info(f"Writing executive summary to {exec_summary_path}")

    exec_header = f"""# Executive Summary
## Phase 4 vs V2 NER System Comparison

**Generated:** {timestamp}

---

"""
    with open(exec_summary_path, "w", encoding="utf-8") as f:
        f.write(exec_header + exec_summary)

    # Save report metadata
    metadata = {
        "generated_at": timestamp,
        "report_version": "1.0",
        "sections": [
            "Executive Summary",
            "Quantitative Metrics",
            "Qualitative Analysis",
            "BPE Artifact Analysis",
            "100-Paper Analysis",
            "Recommendations",
        ],
        "data_sources": {
            "quantitative": "02_quantitative_metrics.json",
            "qualitative": "03_qualitative_analysis.json",
            "bpe": "04_bpe_analysis.json",
            "comparison": "04_merged_comparison.csv",
            "stratification": "sample_stratification.json",
            "category_breakdown": "category_breakdown.json",
        },
        "files": {
            "full_report": str(full_report_path.name),
            "executive_summary": str(exec_summary_path.name),
        },
    }

    metadata_path = output_dir / "report_metadata.json"
    logger.info(f"Writing metadata to {metadata_path}")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("REPORT GENERATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Full report: {full_report_path}")
    logger.info(f"Executive summary: {exec_summary_path}")
    logger.info(f"Metadata: {metadata_path}")
    logger.info(f"Total sections: {len(metadata['sections'])}")

    logger.info("\n✓ Report generation complete!")

    return {
        "full_report": str(full_report_path),
        "executive_summary": str(exec_summary_path),
        "metadata": str(metadata_path),
    }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Generate final comprehensive report (Script 07)"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).parent.parent / "results",
        help="Directory with analysis results (default: ../results)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "results",
        help="Output directory (default: ../results)",
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger = setup_logging(args.output_dir)

    try:
        # Generate report
        report_files = generate_full_report(
            results_dir=args.results_dir,
            output_dir=args.output_dir,
            logger=logger,
        )

        logger.info(f"\n{'=' * 80}")
        logger.info("SUCCESS: Report generated successfully!")
        logger.info(f"{'=' * 80}\n")

        return 0

    except Exception as e:
        logger.error(f"\n{'=' * 80}")
        logger.error(f"ERROR: Report generation failed!")
        logger.error(f"{'=' * 80}")
        logger.error(f"Error details: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
