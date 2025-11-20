# Pipeline Synthesis Scripts - Detailed Explanations

**Last Updated**: 2025-11-19

This document provides a clear explanation of what each script does in the Pipeline Synthesis project.

---

## Table of Contents

1. [Supporting Scripts (01-08)](#supporting-scripts-01-08)
2. [Primary Deduplication Pipeline (09-16)](#primary-deduplication-pipeline-09-16)
3. [Script Execution Order](#script-execution-order)
4. [Quick Reference](#quick-reference)

---

## Supporting Scripts (01-08)

These scripts handle preliminary analysis, comparison, and reporting tasks.

### Script 01: SetFit Inference
**File**: `scripts/01_setfit_inference.py`

**What it does:**
- Runs SetFit classification model on papers to identify bioresource announcements
- Uses a trained SetFit model to predict which papers are likely introducing new bioresources
- Outputs classification results with confidence scores

**Input:**
- Paper dataset with titles and abstracts
- Trained SetFit model

**Output:**
- CSV file with SetFit predictions and confidence scores
- Papers classified as "positive" (bioresource announcement) or "negative"

**When to use:** When you need to classify a large set of papers using the SetFit approach

---

### Script 02: Create Paper Sets
**File**: `scripts/02_create_paper_sets.py`

**What it does:**
- Creates logical groupings of papers based on detection method
- Organizes papers into sets: Linguistic-only, SetFit-only, Both (union)
- Generates Venn diagram statistics

**Input:**
- Papers detected by Linguistic pipeline
- Papers detected by SetFit pipeline

**Output:**
- Multiple CSV files for different paper sets
- Statistics on overlap and unique papers

**When to use:** To understand how Linguistic and SetFit pipelines overlap and differ

---

### Script 03: Map Papers to Entities
**File**: `scripts/03_map_papers_to_entities.py`

**What it does:**
- Maps each paper to its detected bioresource entities
- Extracts all entity mentions from NER results
- Creates paper-entity relationship data

**Input:**
- Papers with NER results
- Entity extraction data

**Output:**
- CSV mapping papers to all detected entities
- Entity frequency statistics

**When to use:** When you need to see all entities detected in each paper

---

### Script 04: Track GCBRs
**File**: `scripts/04_track_gcbrs.py`

**What it does:**
- Tracks papers from the GCBR (Gold Coast Bioresource Repository) inventory
- Identifies which GCBR papers appear in the new pipeline results
- Calculates recall/coverage statistics

**Input:**
- GCBR inventory (baseline/gold standard)
- Pipeline results

**Output:**
- CSV showing which GCBR papers were found
- Coverage statistics and analysis

**When to use:** To validate that your pipeline captures known bioresources

---

### Script 05: Compare Baseline
**File**: `scripts/05_compare_baseline.py`

**What it does:**
- Compares new pipeline results against baseline inventory (2022)
- Identifies papers that match baseline by PMID or entity name
- Separates novel discoveries from baseline matches

**Input:**
- Pipeline results
- Baseline inventory (final_inventory_2022.csv)

**Output:**
- Baseline matches (by PMID and entity)
- Novel papers (not in baseline)
- Comparison statistics

**When to use:** To identify which papers are truly novel vs already in inventory

---

### Script 06: Compare Strategies
**File**: `scripts/06_compare_strategies.py`

**What it does:**
- Compares different detection strategies (Linguistic vs SetFit)
- Analyzes agreement and disagreement between methods
- Identifies papers unique to each approach

**Input:**
- Linguistic pipeline results
- SetFit pipeline results

**Output:**
- Comparison analysis
- Papers where methods agree/disagree
- Strategy performance metrics

**When to use:** To understand strengths/weaknesses of each detection method

---

### Script 07: Generate Visualizations
**File**: `scripts/07_generate_visualizations.py`

**What it does:**
- Creates visual charts and graphs from pipeline results
- Generates Venn diagrams, bar charts, confusion matrices
- Produces publication-ready figures

**Input:**
- Pipeline statistics and results
- Comparison data

**Output:**
- PNG/PDF visualizations
- Charts showing overlap, coverage, performance

**When to use:** For presentations, papers, or visual analysis of results

---

### Script 08: Generate Final Report
**File**: `scripts/08_generate_final_report.py`

**What it does:**
- Creates comprehensive markdown report of entire pipeline
- Aggregates statistics from all analysis steps
- Produces executive summary with key findings

**Input:**
- All pipeline results and statistics
- Comparison analyses

**Output:**
- Detailed markdown report (EXECUTIVE_SUMMARY.md)
- Complete pipeline performance overview

**When to use:** To generate final documentation of pipeline run

---

## Primary Deduplication Pipeline (09-16)

These scripts form the core deduplication workflow, processing papers from initial detection through final deduplicated resources.

### Script 09: Create Primary Resource CSV ✅
**File**: `scripts/09_create_primary_resource_csv.py`

**What it does:**
- Takes union of Linguistic + SetFit papers (16,605 total)
- Identifies **ONE primary bioresource per paper** using multi-factor scoring
- Eliminates papers with multiple competing resources

**How it works:**
1. **Scoring System** (higher = more confident):
   - Title mention: +10 points
   - Abstract mention: +5 points  
   - Consensus (both long & short form detected): +3 points
   - NER confidence score: 0-1 points
   - Mention frequency: count of mentions

2. **Entity Classification**:
   - **Long form**: >5 chars AND (has spaces OR has uppercase) → "Gene Expression Omnibus"
   - **Short form**: ≤5 chars OR all lowercase → "geo", "ncbi"

3. **Status Assignment**:
   - `ok`: Single clear primary resource
   - `conflict`: Multiple resources with similar scores
   - `low_score`: Score below threshold
   - `no_entities`: No entities detected

**Input:**
- Union dataset from Linguistic + SetFit pipelines

**Output:**
- `data/union/union_papers_with_primary_resources.csv` (16,605 papers)

**Key Columns Created:**
- `primary_entity_long` / `primary_entity_short` - The ONE main resource
- `primary_score` - Confidence score
- `status` - Quality indicator
- `all_long` / `all_short` - All detected entities (pipe-separated)

**Example:**
```
Paper: "GEO: Gene Expression Omnibus database for microarray data"
→ primary_entity_long: "gene expression omnibus"
→ primary_entity_short: "geo"
→ primary_score: 18.5 (title mention + abstract + NER confidence)
→ status: ok
```

---

### Script 10: Create Filtered Datasets ✅
**File**: `scripts/10_create_filtered_datasets.py`

**What it does:**
- Splits 16,605 papers into 4 filtered datasets based on baseline matching
- Adds quality indicator flags to ALL papers
- Separates baseline (known) from novel (new discoveries)

**How it works:**

1. **Baseline Matching** (against 3,112 existing resources):
   - **PMID Match**: Direct PMID appears in baseline inventory
   - **Entity Match**: Normalized entity name matches baseline (case-insensitive, no punctuation)

2. **Creates 4 Files**:
   - **File 1a - Baseline by PMID**: 2,660 papers (direct PMID match)
   - **File 1b - Baseline by Entity**: 4,750 papers (entity name match)
   - **File 2 - Linguistic Novel**: 6,609 papers (NOT in baseline, from Linguistic)
   - **File 3 - SetFit Novel**: 7,351 papers (NOT in baseline, from SetFit)

3. **Quality Indicators Added** (to ALL 4 files):
   - `db_keyword_found`: Title contains "database", "server", "portal", "repository"
   - `entity_from_title`: Entity extracted from title (text before ":")
   - `title_entity_in_ner`: Title entity found in NER results (validation)
   - `very_high_conf`: BOTH db_keyword AND title_entity match (highest quality)

**Input:**
- `data/union/union_papers_with_primary_resources.csv`
- `data/final_inventory_2022.csv` (baseline inventory)

**Output Files** (in `data/filtered/`):
- `baseline_by_pmid.csv` - 2,660 papers (59% very high conf)
- `baseline_by_entity_match.csv` - 4,750 papers (40% very high conf)
- `linguistic_excluding_baseline.csv` - 6,609 papers (14% very high conf)
- `setfit_excluding_baseline.csv` - 7,351 papers (12% very high conf)
- `filtering_statistics.txt` - Statistics report

**Key Insight:** Baseline papers have MUCH higher confidence than novel papers (59% vs 14%)

**Example:**
```
Paper PMID: 12345678
Title: "PubMed: A database of biomedical literature"
Entity: "pubmed"

→ Checks baseline: PMID 12345678 found in baseline
→ Goes to: baseline_by_pmid.csv
→ Flags: db_keyword_found=True, very_high_conf=True
```

---

### Script 11: Extract URLs ✅
**File**: `scripts/11_extract_urls.py`

**What it does:**
- Extracts bioresource website URLs from paper abstracts
- Filters out non-bioresource URLs (publishers, code repos, social media)
- Scores URLs based on context and selects primary resource URL

**How it works:**

1. **URL Detection** (3 patterns):
   - Full URLs: `http://www.ncbi.nlm.nih.gov/geo`
   - WWW URLs: `www.example.org/database`
   - Context-based: "available at example.edu/tool"

2. **Filtering** (excludes 40+ domains):
   - Code repositories: github.com, gitlab.com, bitbucket.org
   - Publishers: doi.org, pubmed.gov, nature.com, science.org
   - Social media: twitter.com, linkedin.com
   - File sharing: dropbox.com, figshare.com, zenodo.org
   - Generic: wikipedia.org, google.com

3. **URL Scoring**:
   - **Context phrases** (+10): "available at", "accessible at", "web server"
   - **Resource keywords** (+8): database, bio, genomic, tool, server, portal
   - **Academic domains** (+5): .edu, .gov, .ac.uk, .org
   - **Resource subdomains** (+3): db., data., tools., bio.
   - **Prominence** (+2): appears in first half of abstract

4. **Selection**: Highest-scoring URL becomes primary resource URL

**Input:**
- All 4 filtered CSV files from Script 10

**Output:**
- Updates all 4 files IN-PLACE with 4 new columns:
  - `all_urls` - All URLs detected (pipe-separated)
  - `resource_url` - Primary bioresource URL
  - `has_resource_url` - Boolean flag
  - `url_context` - Text surrounding URL (±50 chars)

**Coverage Results:**
- Baseline PMID: 99.3% have resource URLs
- Baseline Entity: 81.9%
- Linguistic Novel: 72.2%
- SetFit Novel: 24.5%

**Example:**
```
Abstract: "...The database is available at http://www.ncbi.nlm.nih.gov/geo 
and provides access to..."

→ Detected URLs: ["http://www.ncbi.nlm.nih.gov/geo"]
→ Not filtered (not in exclusion list)
→ Score: 10 (context "available at") + 8 (keyword "database") + 2 (prominence) = 20
→ resource_url: "http://www.ncbi.nlm.nih.gov/geo"
→ url_context: "...database is available at http://www.ncbi.nlm.nih.gov/geo and provides..."
```

---

### Script 12: Deduplicate Linguistic (v1) ✅
**File**: `scripts/12_deduplicate_linguistic.py`

**What it does:**
- Deduplicates high-confidence linguistic papers using **exact URL + entity matching**
- Removes duplicate papers describing the same resource
- Identifies "unclear cases" needing manual review

**How it works:**

1. **Filtering** (high-confidence only):
   - `db_keyword_found == True` (has database-related keywords)
   - `has_resource_url == True` (has valid bioresource URL)
   - `baseline_entity_match` is empty (novel resources only)
   - **Result**: 1,007 papers filtered from 6,609 total

2. **Normalization**:
   - **URLs**: 
     - Lowercase
     - Remove protocol (http:// → https://)
     - Remove www prefix
     - Strip trailing slashes
     - Example: `HTTP://WWW.NCBI.NLM.NIH.GOV/GEO/` → `ncbi.nlm.nih.gov/geo`
   
   - **Entities**:
     - Lowercase
     - Remove punctuation
     - Strip whitespace
     - Example: "Gene Expression Omnibus (GEO)" → "gene expression omnibus geo"

3. **Grouping & Merging**:
   - Group by `(normalized_url, normalized_entity)`
   - For each group:
     - Keep earliest paper (lowest PMID)
     - Join all PMIDs with ", "
     - Add `article_count` field
     - Combine unique values from `all_long` and `all_short`

4. **Unclear Cases Detection**:
   - **Same URL, different entities**: Could be name variations or different resources
   - **Same entity, different URLs**: Could be URL variations or mirror sites
   - Exports these for manual review

**Input:**
- `data/filtered/linguistic_excluding_baseline.csv`

**Output:**
- `results/linguistic_high_conf_dedup.csv` - **974 unique resources** ✅
- `results/linguistic_dedup_unclear_cases.csv` - 121 unclear cases
- `results/linguistic_dedup_statistics.txt` - Statistics

**Results:**
- Started: 1,007 high-confidence papers
- Final: 974 unique resources
- Duplicates removed: 33 (3.3%)
- Unclear cases: 121 (need manual review)

**Example:**
```
Papers:
  PMID 12345: "GEO database" → http://www.ncbi.nlm.nih.gov/geo
  PMID 12346: "Gene Expression Omnibus" → https://ncbi.nlm.nih.gov/geo/

→ Normalized: Both → (ncbi.nlm.nih.gov/geo, gene expression omnibus)
→ Merged: PMID "12345, 12346", article_count=2
→ Keep: Earliest PMID (12345) for title/abstract
```

---

### Script 13: URL Similarity Analysis
**File**: `scripts/13_url_similarity_analysis.py`

**What it does:**
- Analyzes URL variations in unclear cases from Script 12
- Computes similarity scores between URLs (0.0 to 1.0)
- Identifies which URLs represent the same resource

**How it works:**

1. **URL Parsing**:
   - Breaks URL into components: protocol, subdomain, domain, TLD, path
   - Handles compound TLDs: .ac.uk, .co.uk, .edu.cn
   - Example: `https://db.example.ac.uk/tools/search` →
     - Protocol: https
     - Subdomain: db
     - Domain: example
     - TLD: .ac.uk
     - Path: /tools/search

2. **Similarity Scoring**:

   **Case 1: Same domain + TLD**
   - Base score: 0.8
   - Same path: +0.2 → **1.0** (exact match)
   - Similar path (>80%): +0.15 → 0.95
   - Different path, similar subdomain: +0.1 → 0.9
   
   **Case 2: Very similar domain (>85% string match)**
   - Base score: 0.5
   - Same TLD: +0.2 → 0.7
   - Similar path: +0.2 → 0.9
   
   **Case 3: Different domains**
   - Subdomain relationship: 0.6 + path_similarity × 0.3
   - Unrelated: domain_similarity × 0.4

3. **Clustering**:
   - Groups URLs with similarity ≥ 0.85
   - Creates merge suggestions

**Input:**
- `results/linguistic_dedup_unclear_cases.csv` (from Script 12)

**Output:**
- `results/url_similarity_report.txt` - Detailed examples with scores
- `results/url_suggested_merges.csv` - Canonical URL mappings
- `results/url_similarity_groups.csv` - Groups to merge

**Findings:**
- 29 URLs identified for merging (13 groups)
- Successfully detects: http/https, trailing slashes, www variations

**Example:**
```
URL1: http://www.ncbi.nlm.nih.gov
URL2: https://ncbi.nlm.nih.gov/

→ Same domain: ncbi.nlm.nih.gov ✓
→ Same TLD: .gov ✓
→ Same path: / (empty) ✓
→ Different protocol: http vs https
→ Different www: with vs without

→ Score: 1.0 (exact match after normalization)
→ Recommendation: MERGE
```

---

### Script 14: Improved Deduplication (v2) ⚠️ ABANDONED
**File**: `scripts/14_deduplicate_linguistic_improved.py`

**Status**: NOT RECOMMENDED - Too aggressive

**What it does:**
- Applies URL similarity clustering BEFORE deduplication
- Automatically merges similar URLs (≥0.85)
- Then deduplicates by (canonical_url, entity)

**Why abandoned:**
- Changed core deduplication logic too much
- Created 267 unclear cases (vs 121 in v1)
- User feedback: "this doesn't work, lets stick with our previous algorithm"
- User wanted similarity as **decision support**, not automatic merging

**Output** (for reference only):
- `results/linguistic_high_conf_dedup_v2.csv` - 963 resources
- `results/linguistic_dedup_unclear_cases_v2.csv` - 267 unclear cases

**Lesson learned:** Human judgment needed for ambiguous merges

---

### Script 15: Analyze Unclear Cases ✅
**File**: `scripts/15_analyze_unclear_cases.py`

**What it does:**
- Takes 121 unclear cases from Script 12 (preserves original logic)
- Applies URL similarity scoring to identify merge candidates
- Assigns merge group IDs but DOESN'T auto-merge
- Provides suggestions for manual review

**How it works:**

1. **Load Unclear Cases**:
   - "Same URL, different entities" (40 cases)
   - "Same entity, different URLs" (81 cases)

2. **For Each Group**:
   - Compute URL similarity matrix (all pairs)
   - Cluster similar URLs using union-find algorithm
   - URLs with similarity ≥ 0.85 go in same cluster

3. **Assign Merge Group IDs**:
   - Each cluster gets unique ID: MG001, MG002, etc.
   - Papers in same cluster get same merge_group_id

4. **Add Recommendation Columns**:
   - `similarity_score`: Max similarity to other URLs
   - `merge_group_id`: Unique ID (MG001, MG002, etc.) or empty
   - `merge_recommendation`: 
     - "MERGE - High similarity (0.XX)" if ≥ 0.85
     - "REVIEW - Moderate similarity (0.XX)" if 0.70-0.84
     - "KEEP_SEPARATE - Low similarity (0.XX)" if < 0.70
     - "SINGLE_URL" if only one URL in group

**Input:**
- `results/linguistic_dedup_unclear_cases.csv` (from Script 12)

**Output:**
- `results/linguistic_unclear_cases_with_similarity.csv` - Enhanced with merge suggestions
- `results/unclear_cases_merge_summary.txt` - Summary statistics

**Results** (partial - only "Same URL" cases processed):
- 40 cases analyzed
- 20 papers in 6 merge groups (MG001-MG006)
- 20 papers to keep separate (genuinely different)
- 81 "Same entity, different URLs" cases not yet processed

**Example:**
```
Group: Same URL cases
Papers:
  PMID 12345: entity="ms2pip", URL="http://iomics.ugent.be/ms2pip"
  PMID 12346: entity="ms²pip", URL="https://iomics.ugent.be/ms2pip/"

→ URL similarity: 1.0 (same after normalization)
→ Assigned: merge_group_id="MG002"
→ Recommendation: "MERGE - High similarity (1.00)"
→ User reviews and confirms merge
```

---

### Script 16: Apply Manual Merges ✅ FINAL
**File**: `scripts/16_apply_manual_merges.py`

**What it does:**
- Reads user's manual merge decisions from edited CSV
- Merges papers assigned the same merge_group_id
- Keeps papers without merge_group_id as singles
- Creates final deduplicated dataset

**How it works:**

1. **Load Data**:
   - User-edited `linguistic_unclear_cases_with_similarity.csv`
   - Original dedup file from Script 12 (974 resources)
   - Full filtered data (for getting all columns)

2. **Identify Merge Groups**:
   - Papers with `merge_group_id` filled in → merge these
   - Papers with empty `merge_group_id` → keep as singles

3. **Create Merged Records**:
   - For each merge group:
     - Join PMIDs: "12345, 12346, 12347"
     - Keep earliest paper's title/abstract
     - Take MAX of scores (primary_score, ner_confidence)
     - Add article_count = number of papers merged
     - Combine unique values from all_long and all_short

4. **Remove Merged PMIDs**:
   - From original 974 resources
   - Remove any resources that contain PMIDs now merged
   - Example: If resource has PMID "12345" and 12345 is now merged with 12346,
     remove the old "12345" resource

5. **Combine**:
   - Remaining resources from original dedup (not involved in merges)
   - + Newly merged resources
   - Sort by article_count (descending), then primary_score

**Merge Group ID Format**: Flexible - works with ANY identifier:
- Single letters: "A", "B", "C"
- MG codes: "MG001", "MG002"
- Custom: "group1", "merge_a", "same_resource", etc.

**Input:**
- `results/linguistic_unclear_cases_with_similarity.csv` (user-edited)
- `results/linguistic_high_conf_dedup.csv` (974 resources from Script 12)
- `data/filtered/linguistic_excluding_baseline.csv` (full data)

**Output:**
- `results/linguistic_high_conf_dedup_final.csv` - **964 unique resources** ✅ **FINAL**
- `results/manual_merge_report.txt` - Detailed merge report

**Results:**
- Original: 974 resources
- Merge groups applied: 6 (MG001-MG006)
- Papers merged: 20 papers → 6 resources
- **Final**: 964 unique resources
- Additional reduction: 10 resources (1.0%)

**Merge Groups Applied:**
1. **MG001**: TCSBN + iNetModels (2 papers) → http://inetmodels.com
2. **MG002**: MS2PIP + MS²PIP (2 papers) → http://iomics.ugent.be/ms2pip
3. **MG003**: Medical Data Models (3 papers) → http://medical-data-models.org
4. **MG004**: MIRIAM Registry (2 papers) → http://www.ebi.ac.uk/miriam
5. **MG005**: NCBI Database (5 papers) → http://www.ncbi.nlm.nih.gov
6. **MG006**: Nucleic Acids Research DB (6 papers) → http://www.oxfordjournals.org/nar/database/c

**Example:**
```
Before (Script 12 - 974 resources):
  Resource 1: PMID "12345", entity="ms2pip", article_count=1
  Resource 2: PMID "12346", entity="ms²pip", article_count=1

User edits CSV:
  Both assigned merge_group_id="MG002"

After (Script 16 - 964 resources):
  Merged Resource: PMID "12345, 12346", entity="ms2pip", article_count=2
  (Resource 1 and 2 removed, new merged resource added)
```

---

## Script Execution Order

### Complete Pipeline (All Scripts)

**Phase 1: Initial Analysis** (Scripts 01-08)
```bash
01_setfit_inference.py          # Run SetFit classification
02_create_paper_sets.py         # Create paper groupings
03_map_papers_to_entities.py   # Map papers to entities
04_track_gcbrs.py               # Track baseline papers
05_compare_baseline.py          # Compare to baseline inventory
06_compare_strategies.py        # Compare detection methods
07_generate_visualizations.py  # Create charts/graphs
08_generate_final_report.py    # Generate summary report
```

**Phase 2: Deduplication Pipeline** (Scripts 09-16) ✅ **RECOMMENDED**
```bash
09_create_primary_resource_csv.py    # ONE resource per paper → 16,605 papers
10_create_filtered_datasets.py       # Split baseline vs novel → 4 datasets
11_extract_urls.py                    # Extract URLs → adds URL columns
12_deduplicate_linguistic.py          # Deduplicate → 974 resources
15_analyze_unclear_cases.py           # Similarity analysis → merge suggestions

# MANUAL STEP: Edit linguistic_unclear_cases_with_similarity.csv
# Assign merge_group_id to papers that should be merged

16_apply_manual_merges.py            # Apply merges → 964 resources ✅ FINAL
```

**Note**: Script 13 (URL similarity analysis) was used for development but Script 15 supersedes it.  
Script 14 (improved deduplication) was ABANDONED.

---

### Quick Start (Deduplication Only)

If you already have the union dataset, run just the deduplication pipeline:

```bash
# Navigate to directory
cd pipeline_synthesis_2025-11-18

# Run deduplication pipeline
python scripts/09_create_primary_resource_csv.py
python scripts/10_create_filtered_datasets.py
python scripts/11_extract_urls.py
python scripts/12_deduplicate_linguistic.py
python scripts/15_analyze_unclear_cases.py

# Manual review:
# Open: results/linguistic_unclear_cases_with_similarity.csv
# For papers you want to merge: assign same merge_group_id (e.g., "A", "B", "MG001")
# For papers to keep separate: leave merge_group_id empty
# Save the file

# Apply manual merges
python scripts/16_apply_manual_merges.py

# Final result:
# results/linguistic_high_conf_dedup_final.csv (964 unique resources) ✅
```

---

## Quick Reference

### Input Files Needed

**For Full Pipeline:**
- Union dataset (Linguistic + SetFit papers)
- Baseline inventory: `data/final_inventory_2022.csv`
- Trained SetFit model (for Script 01)

**For Deduplication Only:**
- Union dataset with NER results
- Baseline inventory: `data/final_inventory_2022.csv`

### Output Files Generated

**Key Outputs:**
- `data/union/union_papers_with_primary_resources.csv` - 16,605 papers with ONE resource each
- `data/filtered/linguistic_excluding_baseline.csv` - 6,609 novel linguistic papers
- `results/linguistic_high_conf_dedup.csv` - 974 deduplicated resources (Script 12)
- `results/linguistic_high_conf_dedup_final.csv` - **964 final resources** ✅ (Script 16)

**Analysis Files:**
- `results/linguistic_unclear_cases_with_similarity.csv` - Merge suggestions
- `results/manual_merge_report.txt` - Final merge statistics
- `results/url_similarity_report.txt` - URL similarity analysis

### Data Flow Summary

```
16,605 papers (Union)
    ↓ Script 09: Identify ONE primary resource
16,605 papers with primary resources
    ↓ Script 10: Split baseline vs novel
6,609 novel linguistic papers
    ↓ Script 11: Extract URLs
6,609 papers with URLs (72% have resource URL)
    ↓ Script 12: Filter high-confidence & deduplicate
974 unique resources (33 duplicates removed)
    ↓ Script 15: Analyze unclear cases
121 unclear cases → 40 analyzed → 6 merge groups
    ↓ Manual review: Assign merge groups
20 papers assigned to 6 merge groups
    ↓ Script 16: Apply manual merges
964 unique resources ✅ FINAL (10 additional merges)
```

---

**Last Updated**: 2025-11-19  
**Pipeline Status**: COMPLETE ✅  
**Final Output**: 964 unique high-confidence novel bioresources
