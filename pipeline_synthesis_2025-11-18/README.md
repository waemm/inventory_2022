# Pipeline Synthesis 2025-11-18

**Complete Pipeline for Bioresource Discovery & Deduplication**

This directory contains scripts for synthesizing results from the Linguistic and SetFit pipelines, identifying primary bioresources, extracting URLs, and performing intelligent deduplication with URL similarity analysis.

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Pipeline Architecture](#pipeline-architecture)
4. [Scripts Documentation](#scripts-documentation)
5. [Running the Pipeline](#running-the-pipeline)
6. [Results & Statistics](#results--statistics)
7. [Column Schema Reference](#column-schema-reference)
8. [Workflow Recommendations](#workflow-recommendations)

---

## Overview

This pipeline processes 16,605 papers from the union of Linguistic and SetFit detection pipelines to:

1. **Identify ONE primary bioresource per paper** using multi-factor scoring
2. **Classify resources as baseline vs novel** using existing inventory
3. **Extract bioresource URLs** from abstracts with smart filtering
4. **Deduplicate resources** using URL and entity matching
5. **Apply URL similarity analysis** to identify merge candidates
6. **Apply manual merge decisions** to create final deduplicated dataset

**Key Achievement**: Reduced 1,007 high-confidence novel papers to **964 unique bioresources** through intelligent deduplication.

---

## Directory Structure

```
pipeline_synthesis_2025-11-18/
├── README.md                    # This file
├── SCRIPT_GUIDE.md             # Quick reference guide
├── data/
│   ├── union/
│   │   └── union_papers_with_primary_resources.csv    # 16,605 papers with primary resources
│   └── filtered/
│       ├── baseline_by_pmid.csv                       # 2,660 baseline papers (PMID match)
│       ├── baseline_by_entity_match.csv               # 4,750 baseline papers (entity match)
│       ├── linguistic_excluding_baseline.csv          # 6,609 novel linguistic papers
│       └── setfit_excluding_baseline.csv              # 7,351 novel setfit papers
├── scripts/
│   ├── 09_create_primary_resource_csv.py             # Primary resource identification
│   ├── 10_create_filtered_datasets.py                # Split baseline vs novel
│   ├── 11_extract_urls.py                            # Extract bioresource URLs
│   ├── 12_deduplicate_linguistic.py                  # Deduplication v1 (RECOMMENDED)
│   ├── 13_url_similarity_analysis.py                 # URL similarity scoring
│   ├── 14_deduplicate_linguistic_improved.py         # Deduplication v2 (ABANDONED)
│   ├── 15_analyze_unclear_cases.py                   # Similarity-based merge suggestions
│   └── 16_apply_manual_merges.py                     # Apply manual merge decisions
└── results/
    ├── linguistic_high_conf_dedup.csv                 # 974 resources (Script 12)
    ├── linguistic_high_conf_dedup_final.csv           # 964 resources (Script 16) ✅ FINAL
    ├── linguistic_unclear_cases_with_similarity.csv   # Unclear cases with merge suggestions
    ├── manual_merge_report.txt                        # Final merge report
    └── [other analysis files]
```

---

## Pipeline Architecture

See full architecture diagram and detailed documentation in the file.

---

## Key Results

**Final Output**: 964 unique high-confidence novel bioresources

**Deduplication Impact**:
- Started with 1,007 high-confidence papers
- Script 12 reduced to 974 resources (33 duplicates removed)
- Script 16 reduced to 964 resources (10 additional merges)

**Coverage**:
- 96.9% are single-paper resources (934)
- 3.1% are multi-paper resources (30)

---

For complete documentation, see the full README content.

**Last Updated**: 2025-11-19
