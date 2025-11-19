# Pipeline Synthesis Scripts - Complete Guide

**Date**: 2025-11-18

---

## File Locations

### Main Directories

- **Input Data**: `pipeline_synthesis_2025-11-18/data/union/`
- **Filtered Datasets**: `pipeline_synthesis_2025-11-18/data/filtered/`
- **Results**: `pipeline_synthesis_2025-11-18/results/`
- **Scripts**: `pipeline_synthesis_2025-11-18/scripts/`

---

## Scripts Overview

### Script 09: Primary Resource Identification
**File**: `scripts/09_create_primary_resource_csv.py`

**Purpose**: Create unified dataset with ONE primary resource per paper

**What it does**:
1. Loads union of Linguistic + SetFit papers (16,605 total)
2. Identifies ONE primary bioresource per paper using multi-factor scoring:
   - Title mention (+10 points)
   - Abstract mention (+5 points)
   - Consensus detection (+3 points)
   - NER confidence (0-1 points)
   - Mention frequency (count)
3. Classifies entities as long/short form
4. Assigns status: ok, conflict, low_score, no_entities

**Input**:
- Union dataset from previous pipeline phases

**Output**:
- `data/union/union_papers_with_primary_resources.csv` (16,605 papers, 16 columns)

**Key Columns Added**:
- `primary_entity_long` - Main long-form resource name
- `primary_entity_short` - Main short-form resource name
- `primary_score` - Confidence score
- `status` - Quality indicator

---

### Script 10: Create Filtered Datasets
**File**: `scripts/10_create_filtered_datasets.py`

**Purpose**: Split union into 4 filtered datasets based on baseline matching

**What it does**:
1. Loads baseline inventory (3,112 resources)
2. Creates 4 separate CSV files:
   - **File 1a**: Baseline by PMID match
   - **File 1b**: Baseline by entity name match
   - **File 2**: Linguistic papers (excluding baseline)
   - **File 3**: SetFit papers (excluding baseline)
3. Adds quality indicators to ALL files:
   - `db_keyword_found` - Database/Server/Portal keywords in title
   - `title_matches_primary` or `title_entity_in_ner` - Title extraction validation
   - `very_high_conf` - Both previous conditions true
4. Extracts entity from title (text before ":")

**Inputs**:
- `data/union/union_papers_with_primary_resources.csv`
- `data/final_inventory_2022.csv` (baseline)

**Outputs** (in `data/filtered/`):
- `baseline_by_pmid.csv` - 2,660 papers (59% very high confidence)
- `baseline_by_entity_match.csv` - 4,750 papers (40% very high confidence)
- `linguistic_excluding_baseline.csv` - 6,609 papers (14% very high confidence)
- `setfit_excluding_baseline.csv` - 7,351 papers (12% very high confidence)
- `filtering_statistics.txt` - Stats report

**Key Insight**: Baseline papers have much higher confidence scores than novel papers

---

### Script 11: URL Extraction
**File**: `scripts/11_extract_urls.py`

**Purpose**: Extract bioresource websites from abstracts with smart filtering

**What it does**:
1. Extracts ALL URLs from abstracts using multiple patterns:
   - Full URLs with protocol (http://, https://, ftp://)
   - URLs starting with www
   - Context-based domain detection
2. Filters out non-bioresource URLs (40+ domains):
   - Code repos (GitHub, GitLab)
   - Publishers (DOI, PubMed, Nature)
   - Social media (Twitter, LinkedIn)
   - File sharing (Dropbox, Figshare)
3. Scores URLs based on:
   - Context phrases (+10): "available at", "web server"
   - Resource keywords (+8): database, bio, genomic, tool
   - Academic domains (+5): .edu, .gov, .ac.uk
   - Resource subdomains (+3): db., data., tools.
   - Prominence (+2): appears in first half of abstract
4. Selects highest-scoring URL as primary resource URL

**Inputs**:
- All 4 filtered CSV files from Script 10

**Outputs**:
- Updates all 4 CSV files in-place with 4 new columns:
  - `all_urls` - All URLs detected (pipe-separated)
  - `resource_url` - Primary bioresource URL
  - `has_resource_url` - Boolean flag
  - `url_context` - Text surrounding URL (±50 chars)
- `scripts/11_extract_urls_run.log` - Run log

**Coverage**:
- Baseline PMID: 99.3% have resource URLs
- Baseline Entity: 81.9%
- Linguistic Novel: 72.2%
- SetFit Novel: 24.5%

---

### Script 12: Deduplication (v1 - Original)
**File**: `scripts/12_deduplicate_linguistic.py`

**Purpose**: Deduplicate high-confidence linguistic papers using exact URL matching

**What it does**:
1. Filters linguistic papers for high confidence:
   - `db_keyword_found == True`
   - `has_resource_url == True`
   - `baseline_entity_match` is empty (novel only)
2. Normalizes URLs and entity names
3. Groups by (clean_url, normalized_entity)
4. Merges duplicates:
   - Keeps earliest paper
   - Joins PMIDs
   - Adds article_count
5. Identifies unclear cases:
   - Same URL, different entities
   - Same entity, different URLs

**Input**:
- `data/filtered/linguistic_excluding_baseline.csv`

**Outputs** (in `results/`):
- `linguistic_high_conf_dedup.csv` - **974 unique resources**
- `linguistic_dedup_unclear_cases.csv` - 121 unclear cases
- `linguistic_dedup_statistics.txt` - Stats

**Results**:
- Started: 1,007 filtered papers
- Final: 974 unique resources
- Removed: 33 duplicates (3.3% reduction)

---

### Script 13: URL Similarity Analysis
**File**: `scripts/13_url_similarity_analysis.py`

**Purpose**: Analyze URL variations to identify similar URLs that should be merged

**What it does**:
1. Loads unclear cases from Script 12
2. Computes URL similarity scores (0.0 to 1.0):
   - Exact match after normalization → 1.0
   - Same domain + TLD → 0.8 base
   - Similar domain (>85%) → 0.5 base
   - Adds bonuses for path/subdomain similarity
3. Groups URLs with similarity ≥ 0.85
4. Generates merge suggestions

**Input**:
- `results/linguistic_dedup_unclear_cases.csv`

**Outputs** (in `results/`):
- `url_similarity_report.txt` - Detailed examples with scores
- `url_suggested_merges.csv` - Canonical URL mappings
- `url_similarity_groups.csv` - Groups to merge

**Findings**:
- 29 URLs can be merged (13 groups)
- Successfully detects: http/https, trailing slashes, subdomains

---

### Script 14: Improved Deduplication (v2 - ABANDONED)
**File**: `scripts/14_deduplicate_linguistic_improved.py`

**Status**: ⚠️ NOT RECOMMENDED - Too aggressive

**What it does**:
- Applies URL similarity clustering BEFORE deduplication
- Automatically merges URLs with similarity ≥ 0.85
- Then deduplicates by (canonical_url, entity)

**Why abandoned**:
- Changes the core deduplication logic too much
- Creates 267 unclear cases (vs 121 in v1)
- User wanted similarity as decision support, not automatic merging

**Outputs** (in `results/`):
- `linguistic_high_conf_dedup_v2.csv` - 963 resources
- `linguistic_dedup_unclear_cases_v2.csv` - 267 unclear cases

---

### Script 15: Analyze Unclear Cases (CURRENT APPROACH)
**File**: `scripts/15_analyze_unclear_cases.py`

**Purpose**: Apply URL similarity to Script 12's unclear cases for merge suggestions

**What it does**:
1. Takes 121 unclear cases from Script 12
2. For each group (same URL or same entity):
   - Computes URL similarity matrix
   - Clusters similar URLs (≥0.85)
   - Assigns unique merge_group_id (MG001, MG002, etc.)
3. Adds columns:
   - `similarity_score` - Max similarity to other URLs in group
   - `merge_group_id` - Unique ID for potential merges
   - `merge_recommendation` - MERGE / REVIEW / KEEP_SEPARATE

**Input**:
- `results/linguistic_dedup_unclear_cases.csv` (from Script 12)

**Outputs** (in `results/`):
- `linguistic_unclear_cases_with_similarity.csv` - Enhanced unclear cases with merge IDs
- `unclear_cases_merge_summary.txt` - Summary stats

**Current Results** (partial - only "Same URL" cases):
- 40 cases analyzed
- 20 papers recommended to merge (6 groups: MG001-MG006)
- 20 papers to keep separate (genuinely different)

**Note**: Only processed "Same URL, different entities" cases so far. Still need to process "Same entity, different URLs" cases (81 remaining).

---

## Recommended Workflow

### For Deduplication:

1. **Run Scripts 12, 15, and 16** (original approach):
   - Script 12: Creates `linguistic_high_conf_dedup.csv` - 974 unique resources
   - Script 15: Analyzes unclear cases, adds merge suggestions
   - Manual review: Edit `linguistic_unclear_cases_with_similarity.csv` with merge decisions
   - Script 16: Applies merges → **`linguistic_high_conf_dedup_final.csv` - 964 unique resources** ✅

2. **RECOMMENDED**: Use final deduplicated dataset:
   - `linguistic_high_conf_dedup_final.csv` - 964 unique resources ✅ FINAL
   - Includes all manual merge decisions applied
   - Ready for validation and downstream analysis

### For Novel Resources:

**High Confidence** (recommended for manual validation):
```python
df = pd.read_csv('linguistic_high_conf_dedup_final.csv')
high_conf = df[df['very_high_conf'] == True]
# Resources with db_keyword AND title_match
```

**All with URLs**:
```python
df = pd.read_csv('linguistic_high_conf_dedup_final.csv')
with_urls = df[df['has_resource_url'] == True]
# Resources with bioresource URLs
```

**Multi-paper resources** (higher confidence):
```python
df = pd.read_csv('linguistic_high_conf_dedup_final.csv')
multi_paper = df[df['article_count'] > 1]
# 30 resources from multiple papers (2-6 papers each)
```

---

## Quick Reference: Where to Find What

### Primary Resource Dataset
- **Location**: `data/union/union_papers_with_primary_resources.csv`
- **Papers**: 16,605
- **Created by**: Script 09

### Filtered Datasets (by category)
- **Location**: `data/filtered/`
- **Files**: 4 CSV files (baseline PMID, baseline entity, linguistic, setfit)
- **Created by**: Script 10
- **Enhanced by**: Script 11 (URL extraction)

### Deduplicated Novel Resources (RECOMMENDED) ✅
- **Location**: `results/linguistic_high_conf_dedup_final.csv` ✅ **USE THIS**
- **Resources**: 964 unique high-confidence novel resources
- **Created by**: Script 16 (final merges applied)

### Intermediate Deduplication (for reference)
- **Location**: `results/linguistic_high_conf_dedup.csv`
- **Resources**: 974 unique high-confidence novel resources
- **Created by**: Script 12

### Merge Analysis
- **Location**: `results/linguistic_unclear_cases_with_similarity.csv`
- **Cases**: 40 analyzed (20 merged, 20 kept separate)
- **Created by**: Script 15
- **Merge Report**: `results/manual_merge_report.txt` (Script 16)

---

## Column Schema Reference

### All Filtered Files (Scripts 10 & 11)

**Base Columns (1-20)**:
- pmid, title, abstract
- in_linguistic, in_setfit
- ling_score, setfit_confidence
- primary_entity_long, primary_entity_short, primary_score
- status, matched_long_short
- all_long, all_short
- ner_source, ner_confidence
- entity_from_title
- db_keyword_found
- very_high_conf

**URL Columns (21-24)** - added by Script 11:
- all_urls
- resource_url
- has_resource_url
- url_context

**File-specific**:
- File 1b: +baseline_entity_matched
- Files 2 & 3: +title_entity_in_ner, +baseline_entity_match

### Deduplicated File (Script 12)

Same as filtered files PLUS:
- `article_count` - Number of papers merged for this resource
- Multiple PMIDs joined with ", " if duplicates were merged

### Unclear Cases with Similarity (Script 15)

Original unclear case columns PLUS:
- `similarity_score` - Max similarity score (0.0-1.0)
- `max_similarity` - Same as similarity_score
- `merge_group_id` - Unique ID (MG001, MG002, etc.) or empty
- `merge_recommendation` - MERGE / REVIEW / KEEP_SEPARATE / SINGLE_URL

---

## Summary Statistics

### Dataset Sizes
- Union papers: 16,605
- Baseline PMID matches: 2,660
- Baseline entity matches: 4,750
- Linguistic excluding baseline: 6,609
- SetFit excluding baseline: 7,351

### URL Extraction Success
- Baseline PMID: 99.3%
- Baseline entity: 81.9%
- Linguistic novel: 72.2%
- SetFit novel: 24.5%

### Deduplication Results
- High-confidence filtered: 1,007 papers
- After Script 12 deduplication: 974 resources
- Duplicates removed (Script 12): 33 (3.3%)
- Unclear cases: 121
  - 40 "same URL" cases analyzed
  - 20 papers in 6 merge groups
  - 20 papers kept separate
  - 81 "same entity" cases not processed
- **After Script 16 (final)**: 964 resources ✅
- **Total duplicates removed**: 43 (4.3%)
- **Additional merges (Script 16)**: 10 (1.0%)

### Script 16: Apply Manual Merges (FINAL)
**File**: `scripts/16_apply_manual_merges.py`

**Purpose**: Apply user's manual merge group assignments to create final deduplicated dataset

**What it does**:
1. Loads `linguistic_unclear_cases_with_similarity.csv` (user-edited with merge assignments)
2. Groups papers by `merge_group_id` column
3. For papers with same merge_group_id:
   - Gets full data from filtered dataset
   - Creates merged record (joins PMIDs, keeps earliest, adds article_count)
   - Combines unique values from all_long and all_short fields
4. For papers without merge_group_id: keeps as singles
5. Removes merged PMIDs from original dedup file (Script 12 output)
6. Combines remaining + newly merged resources
7. Sorts by article_count and primary_score

**Merge Group ID Format**: Flexible - works with any identifier:
- Single letters: "A", "B", "C"
- MG codes: "MG001", "MG002"
- Custom: "group1", "merge_a", etc.

**Inputs**:
- `results/linguistic_unclear_cases_with_similarity.csv` (user-edited)
- `results/linguistic_high_conf_dedup.csv` (974 resources from Script 12)
- `data/filtered/linguistic_excluding_baseline.csv` (full data for merging)

**Outputs** (in `results/`):
- `linguistic_high_conf_dedup_final.csv` - **964 unique resources** ✅ FINAL
- `manual_merge_report.txt` - Detailed merge report

**Results**:
- Original deduplicated resources: 974
- Merge groups applied: 6 (MG001-MG006)
- Papers merged: 20 papers → 6 resources
- Final unique resources: 964
- Additional merges: 10 (1.0% reduction)

**Merge Groups Applied**:
- MG001: TCSBN + iNetModels (2 papers)
- MG002: MS2PIP + MS²PIP (2 papers)
- MG003: Medical Data Models (3 papers)
- MG004: MIRIAM Registry (2 papers)
- MG005: NCBI Database (5 papers)
- MG006: Nucleic Acids Research Database (6 papers)

---

**Last Updated**: 2025-11-19
**Scripts Location**: `pipeline_synthesis_2025-11-18/scripts/`
**Results Location**: `pipeline_synthesis_2025-11-18/results/`
**Final Output**: `results/linguistic_high_conf_dedup_final.csv` - 964 unique resources ✅
