#!/usr/bin/env python3
"""
Script 06: Generate Side-by-Side Comparison

Purpose: Create human-readable side-by-side comparison for 100 sampled papers.

Output formats:
- HTML with interactive styling
- Markdown for easy reading
- JSON with category breakdown

Author: Analysis Pipeline
Date: 2025-11-05
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.comparison_utils import (
    load_comparison_results,
    load_ground_truth,
    clean_entity_name,
)


def setup_logging(output_dir: Path) -> logging.Logger:
    """Setup logging configuration."""
    log_file = output_dir / "06_side_by_side.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phase 4 vs V2 NER Comparison - 100 Papers</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}

        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}

        .stat-card .label {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 8px;
        }}

        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}

        .paper {{
            background: #fafafa;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 25px;
            margin-bottom: 30px;
        }}

        .paper-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .paper-id {{
            font-weight: bold;
            color: #2980b9;
            font-size: 1.1em;
        }}

        .category-badge {{
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}

        .category-AGREEMENT {{
            background: #2ecc71;
            color: white;
        }}

        .category-PHASE4_BETTER {{
            background: #3498db;
            color: white;
        }}

        .category-V2_BETTER {{
            background: #e74c3c;
            color: white;
        }}

        .category-DISAGREEMENT {{
            background: #f39c12;
            color: white;
        }}

        .paper-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 12px;
            line-height: 1.4;
        }}

        .paper-abstract {{
            color: #555;
            font-size: 0.95em;
            line-height: 1.6;
            margin-bottom: 20px;
            padding: 12px;
            background: white;
            border-left: 3px solid #3498db;
        }}

        .predictions {{
            display: grid;
            gap: 15px;
            margin-top: 20px;
        }}

        .prediction-row {{
            display: grid;
            grid-template-columns: 150px 1fr;
            gap: 15px;
            padding: 12px;
            background: white;
            border-radius: 4px;
        }}

        .prediction-label {{
            font-weight: bold;
            color: #7f8c8d;
            align-self: start;
        }}

        .prediction-value {{
            font-family: 'Courier New', monospace;
            color: #2c3e50;
        }}

        .entity-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .entity {{
            padding: 4px 10px;
            border-radius: 3px;
            font-size: 0.9em;
            display: inline-block;
        }}

        .entity-correct {{
            background: #d5f4e6;
            color: #27ae60;
            border: 1px solid #27ae60;
        }}

        .entity-incorrect {{
            background: #fadbd8;
            color: #c0392b;
            border: 1px solid #c0392b;
        }}

        .entity-partial {{
            background: #fff3cd;
            color: #856404;
            border: 1px solid #856404;
        }}

        .entity-neutral {{
            background: #e9ecef;
            color: #495057;
            border: 1px solid #6c757d;
        }}

        .checkmark {{
            color: #27ae60;
            font-weight: bold;
        }}

        .crossmark {{
            color: #c0392b;
            font-weight: bold;
        }}

        .metadata {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #7f8c8d;
        }}

        .metadata-item {{
            display: flex;
            gap: 5px;
        }}

        .metadata-label {{
            font-weight: 600;
        }}

        .toc {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 30px;
        }}

        .toc ul {{
            list-style: none;
            padding-left: 20px;
        }}

        .toc li {{
            margin: 8px 0;
        }}

        .toc a {{
            color: #2980b9;
            text-decoration: none;
        }}

        .toc a:hover {{
            text-decoration: underline;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Phase 4 vs V2 NER System Comparison</h1>
        <p><strong>100 Sampled Papers for Qualitative Analysis</strong></p>
        <p>Generated: {timestamp}</p>

        <div class="stats">
            <div class="stat-card">
                <div class="label">Total Papers</div>
                <div class="value">{total_papers}</div>
            </div>
            <div class="stat-card">
                <div class="label">Agreement</div>
                <div class="value">{agreement_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">Phase 4 Better</div>
                <div class="value">{phase4_better_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">V2 Better</div>
                <div class="value">{v2_better_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">Disagreement</div>
                <div class="value">{disagreement_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">With Ground Truth</div>
                <div class="value">{ground_truth_count}</div>
            </div>
        </div>

        <div class="toc">
            <h3>Table of Contents</h3>
            <ul>
                <li><a href="#agreement">Agreement ({agreement_count} papers)</a></li>
                <li><a href="#phase4-better">Phase 4 Better ({phase4_better_count} papers)</a></li>
                <li><a href="#v2-better">V2 Better ({v2_better_count} papers)</a></li>
                <li><a href="#disagreement">Disagreement ({disagreement_count} papers)</a></li>
            </ul>
        </div>

        {papers_html}
    </div>
</body>
</html>
"""


def create_paper_html(
    paper: Dict[str, Any],
    ground_truth: Dict[str, List[str]],
) -> str:
    """Create HTML for a single paper comparison."""
    pmid = str(paper["pmid"])
    title = paper.get("title", "No title available")
    abstract = paper.get("abstract", "No abstract available")

    # Truncate abstract to first 300 characters
    if len(abstract) > 300:
        abstract = abstract[:297] + "..."

    # Parse entities
    v2_entities = eval(paper["v2_entities"]) if isinstance(paper["v2_entities"], str) else paper["v2_entities"]
    phase4_entities = eval(paper["phase4_entities"]) if isinstance(paper["phase4_entities"], str) else paper["phase4_entities"]
    gt_entities = ground_truth.get(pmid, [])

    # Clean entities
    v2_clean = [clean_entity_name(e) for e in v2_entities]
    phase4_raw = phase4_entities  # Keep raw for display
    phase4_clean = [clean_entity_name(e) for e in phase4_entities]

    category = paper["category"]
    has_gt = len(gt_entities) > 0

    # Create entity displays
    def format_entity_list(entities: List[str], correct_set: set = None, style: str = "neutral") -> str:
        if not entities:
            return '<span class="entity-neutral">(none)</span>'

        html_parts = []
        for entity in entities:
            if correct_set is not None:
                if entity in correct_set:
                    html_parts.append(f'<span class="entity entity-correct">{entity} ✓</span>')
                else:
                    html_parts.append(f'<span class="entity entity-incorrect">{entity} ✗</span>')
            else:
                html_parts.append(f'<span class="entity entity-{style}">{entity}</span>')

        return '<div class="entity-list">' + "".join(html_parts) + "</div>"

    # Determine correctness
    gt_set = set(gt_entities)

    gt_html = format_entity_list(gt_entities, style="correct") if has_gt else '<span class="entity-neutral">(not available)</span>'
    v2_html = format_entity_list(v2_clean, gt_set if has_gt else None, style="neutral")
    phase4_raw_html = format_entity_list(phase4_raw, style="neutral")
    phase4_clean_html = format_entity_list(phase4_clean, gt_set if has_gt else None, style="neutral")

    html = f"""
    <div class="paper">
        <div class="paper-header">
            <div class="paper-id">PMID: {pmid}</div>
            <div class="category-badge category-{category}">{category.replace('_', ' ')}</div>
        </div>

        <div class="paper-title">{title}</div>

        <div class="paper-abstract">
            <strong>Abstract:</strong> {abstract}
        </div>

        <div class="predictions">
            <div class="prediction-row">
                <div class="prediction-label">Ground Truth:</div>
                <div class="prediction-value">{gt_html}</div>
            </div>

            <div class="prediction-row">
                <div class="prediction-label">V2 Prediction:</div>
                <div class="prediction-value">{v2_html}</div>
            </div>

            <div class="prediction-row">
                <div class="prediction-label">Phase 4 (Raw):</div>
                <div class="prediction-value">{phase4_raw_html}</div>
            </div>

            <div class="prediction-row">
                <div class="prediction-label">Phase 4 (Clean):</div>
                <div class="prediction-value">{phase4_clean_html}</div>
            </div>
        </div>

        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">V2 Count:</span>
                <span>{len(v2_clean)}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Phase 4 Count:</span>
                <span>{len(phase4_clean)}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Ground Truth:</span>
                <span>{'Yes' if has_gt else 'No'}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Interest Score:</span>
                <span>{paper.get('interest_score', 0):.1f}</span>
            </div>
        </div>
    </div>
    """

    return html


def create_paper_markdown(
    paper: Dict[str, Any],
    ground_truth: Dict[str, List[str]],
) -> str:
    """Create Markdown for a single paper comparison."""
    pmid = str(paper["pmid"])
    title = paper.get("title", "No title available")
    abstract = paper.get("abstract", "No abstract available")

    # Truncate abstract
    if len(abstract) > 300:
        abstract = abstract[:297] + "..."

    # Parse entities
    v2_entities = eval(paper["v2_entities"]) if isinstance(paper["v2_entities"], str) else paper["v2_entities"]
    phase4_entities = eval(paper["phase4_entities"]) if isinstance(paper["phase4_entities"], str) else paper["phase4_entities"]
    gt_entities = ground_truth.get(pmid, [])

    # Clean entities
    v2_clean = [clean_entity_name(e) for e in v2_entities]
    phase4_raw = phase4_entities
    phase4_clean = [clean_entity_name(e) for e in phase4_entities]

    category = paper["category"]
    has_gt = len(gt_entities) > 0

    md = f"""
---

## Paper: {pmid}

**Category:** {category.replace('_', ' ')}

**Title:** {title}

**Abstract:** {abstract}

### Predictions

**Ground Truth:** {', '.join(gt_entities) if has_gt else '(not available)'}

**V2 Prediction:** {', '.join(v2_clean) if v2_clean else '(none)'}

**Phase 4 (Raw):** {', '.join(phase4_raw) if phase4_raw else '(none)'}

**Phase 4 (Clean):** {', '.join(phase4_clean) if phase4_clean else '(none)'}

### Metadata

- V2 Count: {len(v2_clean)}
- Phase 4 Count: {len(phase4_clean)}
- Ground Truth: {'Yes' if has_gt else 'No'}
- Interest Score: {paper.get('interest_score', 0):.1f}

"""

    return md


def generate_side_by_side_comparison(
    sample_file: Path,
    ground_truth_file: Path,
    output_dir: Path,
    logger: logging.Logger = None,
) -> Dict[str, Any]:
    """
    Generate side-by-side comparison for sampled papers.

    Args:
        sample_file: Path to sampled papers CSV
        ground_truth_file: Path to ground truth data
        output_dir: Output directory
        logger: Logger instance

    Returns:
        Dictionary with generation metadata
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("SCRIPT 06: GENERATE SIDE-BY-SIDE COMPARISON")
    logger.info("=" * 80)

    # Load data
    logger.info(f"Loading sampled papers from {sample_file}")
    sample_df = pd.read_csv(sample_file)

    logger.info(f"Loading ground truth from {ground_truth_file}")
    ground_truth = load_ground_truth(ground_truth_file)

    logger.info(f"Total papers to process: {len(sample_df)}")

    # Sort by category for organized display
    category_order = ["AGREEMENT", "PHASE4_BETTER", "V2_BETTER", "DISAGREEMENT"]
    sample_df["category_order"] = sample_df["category"].map(
        {cat: i for i, cat in enumerate(category_order)}
    )
    sample_df = sample_df.sort_values(["category_order", "interest_score"], ascending=[True, False])

    # Generate HTML
    logger.info("\nGenerating HTML comparison...")
    papers_html_parts = []
    current_category = None

    for _, paper in tqdm(sample_df.iterrows(), total=len(sample_df), desc="Creating HTML"):
        category = paper["category"]

        # Add category header
        if category != current_category:
            category_id = category.lower().replace("_", "-")
            papers_html_parts.append(
                f'<h2 id="{category_id}">{category.replace("_", " ")}</h2>'
            )
            current_category = category

        papers_html_parts.append(create_paper_html(paper.to_dict(), ground_truth))

    papers_html = "\n".join(papers_html_parts)

    # Calculate statistics
    category_counts = sample_df["category"].value_counts()
    stats = {
        "total_papers": len(sample_df),
        "agreement_count": category_counts.get("AGREEMENT", 0),
        "phase4_better_count": category_counts.get("PHASE4_BETTER", 0),
        "v2_better_count": category_counts.get("V2_BETTER", 0),
        "disagreement_count": category_counts.get("DISAGREEMENT", 0),
        "ground_truth_count": int(sample_df["has_ground_truth"].sum()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "papers_html": papers_html,
    }

    # Write HTML file
    html_output = output_dir / "100_paper_comparison.html"
    logger.info(f"Writing HTML to {html_output}")
    with open(html_output, "w", encoding="utf-8") as f:
        f.write(HTML_TEMPLATE.format(**stats))

    # Generate Markdown
    logger.info("\nGenerating Markdown comparison...")
    md_parts = [
        "# Phase 4 vs V2 NER System Comparison",
        "",
        "**100 Sampled Papers for Qualitative Analysis**",
        "",
        f"Generated: {stats['timestamp']}",
        "",
        "## Summary Statistics",
        "",
        f"- **Total Papers:** {stats['total_papers']}",
        f"- **Agreement:** {stats['agreement_count']}",
        f"- **Phase 4 Better:** {stats['phase4_better_count']}",
        f"- **V2 Better:** {stats['v2_better_count']}",
        f"- **Disagreement:** {stats['disagreement_count']}",
        f"- **With Ground Truth:** {stats['ground_truth_count']}",
        "",
        "## Papers",
        "",
    ]

    current_category = None
    for _, paper in tqdm(sample_df.iterrows(), total=len(sample_df), desc="Creating Markdown"):
        category = paper["category"]

        # Add category header
        if category != current_category:
            md_parts.append(f"\n# {category.replace('_', ' ')}\n")
            current_category = category

        md_parts.append(create_paper_markdown(paper.to_dict(), ground_truth))

    markdown_content = "\n".join(md_parts)

    # Write Markdown file
    md_output = output_dir / "100_paper_comparison.md"
    logger.info(f"Writing Markdown to {md_output}")
    with open(md_output, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    # Create category breakdown JSON
    logger.info("\nGenerating category breakdown...")
    category_breakdown = {
        "total_papers": len(sample_df),
        "categories": {},
        "timestamp": datetime.now().isoformat(),
    }

    for category in category_order:
        cat_df = sample_df[sample_df["category"] == category]
        if len(cat_df) > 0:
            category_breakdown["categories"][category] = {
                "count": len(cat_df),
                "with_ground_truth": int(cat_df["has_ground_truth"].sum()),
                "mean_entities": float(cat_df["total_entities"].mean()),
                "mean_interest_score": float(cat_df["interest_score"].mean()),
                "pmids": cat_df["pmid"].astype(str).tolist(),
            }

    # Write category breakdown
    json_output = output_dir / "category_breakdown.json"
    logger.info(f"Writing category breakdown to {json_output}")
    with open(json_output, "w") as f:
        json.dump(category_breakdown, f, indent=2)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("GENERATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Papers processed: {len(sample_df)}")
    logger.info(f"HTML output: {html_output}")
    logger.info(f"Markdown output: {md_output}")
    logger.info(f"JSON output: {json_output}")

    logger.info("\n✓ Side-by-side comparison generated!")

    return {
        "papers_processed": len(sample_df),
        "html_file": str(html_output),
        "markdown_file": str(md_output),
        "json_file": str(json_output),
        "category_breakdown": category_breakdown,
    }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Generate side-by-side comparison for 100 papers (Script 06)"
    )
    parser.add_argument(
        "--sample-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "sample_100_papers.csv",
        help="Path to sampled papers (default: ../data/sample_100_papers.csv)",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "ground_truth.json",
        help="Path to ground truth data (default: ../data/ground_truth.json)",
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
        # Generate comparison
        metadata = generate_side_by_side_comparison(
            sample_file=args.sample_file,
            ground_truth_file=args.ground_truth,
            output_dir=args.output_dir,
            logger=logger,
        )

        logger.info(f"\n{'=' * 80}")
        logger.info("SUCCESS: Side-by-side comparison generated successfully!")
        logger.info(f"{'=' * 80}\n")

        return 0

    except Exception as e:
        logger.error(f"\n{'=' * 80}")
        logger.error(f"ERROR: Generation failed!")
        logger.error(f"{'=' * 80}")
        logger.error(f"Error details: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
