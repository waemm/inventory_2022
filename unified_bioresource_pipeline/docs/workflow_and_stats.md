# Unified Bioresource Pipeline: Complete Workflow & Statistics

**Generated:** 2025-11-27
**Updated:** 2025-11-29 (Phase 10 data quality improvements: URL blocking, name disambiguation, character sanitization)
**Session ID:** 2025-11-28-180950-wyaty

---

## Overview

This document describes the complete end-to-end pipeline for discovering, extracting, validating, and finalizing bioresource mentions from scientific literature.

### Complete Data Flow

```
149,943 EPMC Papers (2011-2021, Query V5.1)
          ↓
    [10 Phases]
          ↓
1,365+ Final Bioresources (final_inventory.csv)
```

---

## Phase 1: Classification

**Scripts:**
- `01_run_v2_classification.py`
- `02_run_pycaret_classification.py`

**Purpose:** Identify papers that potentially introduce bioresources using two complementary ML approaches.

| Step | Description | Output |
|------|-------------|--------|
| V2 RoBERTa | Fine-tuned transformer classifier on paper abstracts | 12,285 positives (8.2%) |
| PyCaret | Metadata-based classifier (journal, MeSH terms, etc.) | 45,766 positives (30.6%) |
| Union | Combine both for high recall | **50,192 candidate papers (33.5%)** |

**Time:** 2-4 hours (GPU)

---

## Phase 2: Named Entity Recognition (NER)

**Scripts:**
- `04_run_v2_ner.py`
- `05_run_spacy_ner.py`
- `06_extract_pmid_union.py`

**Purpose:** Extract bioresource entity names from paper text using two NER systems.

| Step | Description | Output |
|------|-------------|--------|
| V2 RoBERTa NER | Transformer-based sequence labeling | 18,319 papers, 67,187 entities |
| spaCy Hybrid NER | Statistical model + EntityRuler patterns | 32,317 papers, 117,491 entities |
| Union | Papers with hits from either system | **34,279 unique papers** |

**Time:** 5-10 hours (GPU + CPU)

---

## Phase 3: Linguistic Filtering

**Script:** `07_linguistic_scoring.py`

**Purpose:** Score papers based on linguistic patterns that distinguish "resource introduction" from "resource usage" papers.

| Score Range | Interpretation | Count |
|-------------|----------------|-------|
| High (≥3) | Definitively introduces a resource | 8,648 papers (25.2%) |
| Medium (0-2) | Ambiguous, needs ML verification | 20,816 papers (60.7%) |
| Low (<0) | Usage paper, filter out | 4,796 papers (14.0%) |

**Time:** ~30 seconds

---

## Phase 4: SetFit Classification

**Script:** `08_setfit_inference.py`

**Purpose:** Use few-shot learning (SetFit) to classify medium-confidence papers.

| Step | Description | Output |
|------|-------------|--------|
| Input | Medium-score papers from Phase 3 | 20,816 papers |
| SetFit Model | Few-shot sentence transformer classifier | ~7,800 additional introductions |
| **Total Introductions** | High linguistic + SetFit positives | **~16,605 papers** |

**Time:** 10-15 minutes (GPU on Colab)

---

## Phase 5: Entity Mapping & Resource Creation

**Scripts:**
- `09_create_paper_sets.py`
- `10_map_to_entities.py`
- `11_create_primary_resources.py`
- `12_add_quality_indicators.py`
- `13_extract_urls.py`

**Purpose:** Map papers to entities and create structured resource records.

| Step | Description | Output |
|------|-------------|--------|
| Create Paper Sets | A=high confidence, B=SetFit, C=all NER | 3 paper sets |
| Map to Entities | Link papers to their extracted NER entities | Paper↔Entity mapping |
| Primary Resources | One record per unique resource (by entity name) | Primary resource CSV |
| Quality Indicators | Add confidence scores, article counts | Enriched resources |
| Extract URLs | Parse URLs from abstracts/fulltext | **set_c with URLs** |

**Time:** 5-10 minutes

---

## Phase 6: URL Scanning & Validation

**Scripts:**
- `14_prepare_urls.py`
- `15_scan_urls.py`
- `16_merge_scan_scores.py`
- `18_scan_urls_set_c.py`
- `19_backfill_url_data.py`

**Purpose:** Validate URLs and gather quality metadata.

| Step | Description | Output |
|------|-------------|--------|
| Prepare URLs | Deduplicate, normalize, format | Clean URL list |
| Scan URLs | Multi-threaded HTTP HEAD requests | Status codes |
| Wayback Fallback | Check Internet Archive for dead URLs | Archive URLs |
| Domain Scoring | Reputation and content-type scoring | Quality scores |
| Backfill | Merge URL data back to resources | **URL-enriched resources** |

**Time:** 75-90 minutes

---

## Phase 7: Deduplication

**Scripts:**
- `17_deduplicate_all_sets.py`
- `18_analyze_unclear_cases.py`
- `19_apply_manual_merges.py`

**Purpose:** Identify and merge duplicate resource entries.

| Step | Description | Output |
|------|-------------|--------|
| Fuzzy Matching | Compare resource names + URLs | Duplicate groups |
| Similarity Scoring | Linguistic similarity metrics | Confidence scores |
| Manual Review | Human review of unclear cases | Merge decisions |
| Apply Merges | Execute merge decisions | **set_c_final.csv** |

**Output:** ~10,810 deduplicated resources

**Time:** 5 minutes + manual review time

---

## Phase 8: URL Recovery (NEW)

**Scripts:**
- `28_identify_missing_urls.py`
- `29_fetch_abstracts.py`
- `30_search_abstracts_urls.py`
- `31_fetch_fulltext.py`
- `32_search_fulltext_urls.py`
- `33_consolidate_recovery.py`
- `34_merge_websearch_results.py` (supports merged or separate input modes)
- `run_phase8.py` (orchestrator)
- `Orchestrator_prompt.md` (AI agent orchestration guide)

**Purpose:** Recover URLs for bioresources that are missing URLs after initial extraction (~25% of records).

### Why URL Recovery?

Investigation revealed URLs were missed due to:
- Bare domains without `http://` prefix (e.g., `biocyc.org`)
- URLs in brackets without spaces
- Multiple PMIDs per resource (only first was checked)
- URLs only in fulltext, not abstracts

### Process

| Step | Description | Output |
|------|-------------|--------|
| Identify Missing | Find records without URLs, extract all PMIDs | `missing_urls_prepared.csv` |
| Fetch Abstracts | EPMC API for all unique PMIDs | `abstracts_cache.json` |
| Search Abstracts | Enhanced regex patterns with exclusion rules | ~17% recovery |
| Fetch Fulltext | EPMC fulltext XML for PMCIDs available | `fulltext_cache.json` |
| Search Fulltext | Same patterns on fulltext | ~24% additional recovery |
| Consolidate | Merge results, prepare web search chunks | `recovered_urls.csv` |
| Web Search (agents) | Manual/agent search for remaining | `websearch_results_*.csv` |
| Filter & Merge | Apply URL exclusions, combine all sources | `final_url_recovery.csv` |

### URL Filtering (Script 34)

Script 34 automatically filters unwanted URLs from web search results:
- Code repositories (GitHub, GitLab, Bitbucket)
- Data archives (Zenodo, Dryad, Figshare, OSF)
- DOI links and FTP servers
- Package repositories (CRAN, Bioconductor, PyPI)

Filtered URLs are saved to `excluded_urls.csv` for review.

### Agent Orchestration

For AI-based web search, see `Orchestrator_prompt.md` which guides:
- Dispatching sub-agents with chunk files
- Collecting and merging results
- Running final filtering

### URL Exclusion Rules

| Excluded Type | Example | Reason |
|--------------|---------|--------|
| GitHub repos | `github.com/user/repo` | Code repository |
| GitHub Pages | `mydb.github.io` | GitHub-hosted site |
| GitLab/Bitbucket | `gitlab.com/user/repo` | Code repository |
| Zenodo archives | `zenodo.org/record/123` | File archive |
| DOI links | `doi.org/10.1234/xyz` | DOI resolver |
| Dryad archives | `datadryad.org/...` | Data archive |
| Figshare | `figshare.com/...` | File sharing |
| OSF | `osf.io/...` | Open Science Framework |
| FTP servers | `ftp://...` | File download |
| Generic institutional | `stanford.edu` | Not database-specific |
| Package repos | `cran.r-project.org`, `pypi.org` | Software packages |

### Expected Results

| Stage | Recovery Rate |
|-------|--------------|
| Abstract search | ~17% |
| Fulltext search | ~24% of remaining |
| **Combined (automated)** | **~37%** |
| Web search (agents) | TBD |

**Time:** ~5 minutes (automated) + agent web search time

---

## Phase 9: Baseline Comparison

**Scripts:**
- `20_baseline_comparison.py`
- `21_generate_visualizations.py`

**Purpose:** Compare against existing inventory and identify novel discoveries.

| Step | Description | Output |
|------|-------------|--------|
| Baseline Match | Compare with 2022 inventory | Known vs novel |
| False Positive ID | Flag likely false positives | FP candidates |
| Visualizations | Generate comparison charts | Reports & charts |
| **Manual Review** | Human curation of novel candidates | **FINAL_novel_bioresources.csv** |

**Output:** 2,594 novel bioresources (after manual FP removal)

---

## Phase 10: Finalization

**Scripts:**
- `22_filter_novel_resources.py`
- `23_transform_columns.py`
- `24_check_urls_with_geo.py`
- `25_fetch_epmc_metadata.py`
- `26_process_countries.py`
- `27_generate_final_inventory.py`
- `run_phase9.py` (convenience wrapper)

**Purpose:** Transform novel bioresources into final database-ready format with data quality improvements.

| Script | Description | Output |
|--------|-------------|--------|
| **22** | Filter set_c_final to only FINAL novel resources | Filtered rows |
| **23** | Map columns + name sanitization + disambiguation | Column transformation |
| **24** | Check URL status + IP geolocation + Wayback + URL blocking | Valid URLs only |
| **25** | Fetch EuropePMC metadata (authors, grants, citations) | Rich metadata |
| **26** | Extract ISO country codes from affiliations | Country standardization |
| **27** | Generate final inventory CSV | **final_inventory.csv** |

### Phase 10 Data Quality Features (2025-11-29)

**Script 23 - Name Processing:**
- Auto-capitalize short names (≤6 chars all lowercase)
- Clean pipe-separated names (use first)
- Remove HTML tags from names
- Sanitize non-ASCII characters (ø→o, é→e, μ→mu, etc.)
- **Disambiguate duplicate names** using URL subdomain (e.g., GXB → GXB (breastcancer))
- Recover names from URL when original name had encoding issues

**Script 24 - URL Validation:**
- Block repository hosting URLs (bitbucket.org, gitlab.com, sourceforge.net)
- Block file download URLs (.pdf, .xlsx, .zip, .tar.gz, etc.)
- Block aggregator pages (oxfordjournals.org, mozilla.org)
- Mark github.io URLs for review

### Phase 10 Detailed Statistics (Latest Run: 2025-11-28)

**URL Checking (Script 24):**
- Total unique URLs processed: 1,995
- Processing time: ~19 minutes
- Live URLs (HTTP 200): 1,139 (57.1%)
- Wayback rescued: 805 (40.4%)
- URLs blocked (repos/files): 21
- Total included: 1,945 resources
- Excluded (no valid URL): 648 resources

**Name Modifications (Script 23):**
| Modification | Count |
|--------------|-------|
| CAPITALIZED | 657 |
| POPULATED_FROM_URL | 153 |
| SHORT_NAME_REPLACED | 18 |
| SHORT_NAME_FLAGGED | 13 |
| CHARS_SANITIZED | 10 |
| PIPE_CLEANED | 7 |
| HTML_REMOVED | 5 |
| **DISAMBIGUATED** | 65 |

**Metadata Coverage (Script 25):**
| Field | Coverage |
|-------|----------|
| publication_date | 100.0% |
| authors | 99.5% |
| affiliation | 96.9% |
| num_citations | 97.6% |
| has_affiliation_countries | 91.7% |
| has_url_country | 46.2% |
| grant_agencies | ~55% |
| grant_ids | ~55% |

**Time:** ~20 minutes total (mostly URL checking)

---

## Final Output Summary

### Output Files

| File | Description | Rows |
|------|-------------|------|
| `final_inventory.csv` | Main output for database upload | 1,945 |
| `excluded_no_url.csv` | Resources without valid URLs | 648 |
| `statistics.json` | Coverage and quality metrics | - |
| `finalization.log` | Processing log | - |

### Final Column Format (23 columns)

```
ID, best_name, best_name_prob, best_common, best_common_prob,
best_full, best_full_prob, article_count, extracted_url,
extracted_url_status, extracted_url_country, extracted_url_coordinates,
wayback_url, publication_date, affiliation, authors, grant_ids,
grant_agencies, num_citations, affiliation_countries,
best_name_original, name_modification_flags, url_validation
```

**New Data Quality Columns:**
- `best_name_original`: Original name before sanitization/disambiguation
- `name_modification_flags`: Audit trail (CAPITALIZED, DISAMBIGUATED, CHARS_SANITIZED, etc.)
- `url_validation`: 'ok' or 'review' based on URL pattern checking

### Pipeline Funnel Statistics

| Stage | Records | Retention |
|-------|---------|-----------|
| Raw EPMC papers | 149,943 | 100% |
| After classification (union) | 50,192 | 33.5% |
| After NER union | 34,279 | 22.9% |
| After linguistic + SetFit | ~16,605 | 11.1% |
| After deduplication (set_c_final) | 10,810 | 7.2% |
| Novel bioresources (after FP review) | 2,594 | 1.7% |
| **Final with valid URLs** | **1,945** | **1.30%** |

### Citation Statistics (Final Inventory)

| Metric | Value |
|--------|-------|
| Total citations | 213,195 |
| Mean citations | 112.3 |
| Median citations | 21.0 |
| Max citations | 13,020 |

### Top Countries by Affiliation

| Country | Count |
|---------|-------|
| United States | 367 |
| China | 131 |
| United Kingdom | 126 |
| Germany | 89 |
| India | 65 |
| France | 54 |
| Italy | 40 |
| Canada | 40 |
| Japan | 38 |

---

## Running the Pipeline

### Full Pipeline
```bash
cd unified_bioresource_pipeline
python run_pipeline.py --full
```

### Phase 10 Only (Finalization)
```bash
python unified_bioresource_pipeline/scripts/phase9_finalization/run_phase9.py \
    --set-c pipeline_synthesis_2025-11-18/results/deduplicated/aggressive/set_c_final.csv \
    --final false_positive_analysis/FINAL_novel_bioresources_with_urls.csv
```

### Phase 10 Options
- `--skip-urls`: Skip URL checking (for testing)
- `--skip-epmc`: Skip EPMC API calls (for testing)
- `--session-id ID`: Use custom session ID

---

## Output Location

All Phase 9 outputs are saved to:
```
unified_bioresource_pipeline/results/{session_id}/finalization/
```

Example: `unified_bioresource_pipeline/results/2025-11-27-162941-wasc8/finalization/`
