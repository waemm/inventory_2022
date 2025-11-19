# Filtered Datasets with URL Extraction - Complete

**Date**: 2025-11-18
**Status**: ✅ COMPLETE

---

## Overview

Created 4 filtered datasets from the Union set (16,605 papers) with:
- Primary resource identification
- Quality indicators (title matching, database keywords)
- **NEW**: Comprehensive URL extraction with bioresource filtering

---

## Files Created

| File | Papers | Columns | Size | Description |
|------|--------|---------|------|-------------|
| `baseline_by_pmid.csv` | 2,660 | 24 | 4.2M | Baseline inventory (matched by PMID) |
| `baseline_by_entity_match.csv` | 4,750 | 25 | 7.3M | Papers discussing baseline resources (entity match) |
| `linguistic_excluding_baseline.csv` | 6,609 | 25 | 11M | High-quality linguistic papers (novel resources) |
| `setfit_excluding_baseline.csv` | 7,351 | 25 | 11M | SetFit-identified papers (novel resources) |

**Location**: `pipeline_synthesis_2025-11-18/data/filtered/`

---

## Column Schema

### Base Columns (1-20)

1. `pmid` - PubMed ID
2. `title` - Paper title
3. `abstract` - Full abstract text
4. `in_linguistic` - Boolean (in Linguistic set)
5. `in_setfit` - Boolean (in SetFit set)
6. `ling_score` - Linguistic classifier score
7. `setfit_confidence` - SetFit confidence
8. `primary_entity_long` - Main long-form resource name
9. `primary_entity_short` - Main short-form resource name
10. `primary_score` - Primary resource confidence score
11. `status` - ok | conflict | low_score | no_entities
12. `matched_long_short` - Paired long/short entities
13. `all_long` - Other long-form entities
14. `all_short` - Other short-form entities
15. `ner_source` - spacy | v2 | spacy+v2
16. `ner_confidence` - V2 NER probability
17. `entity_from_title` - Extracted from title (before ":")
18. `db_keyword_found` - Boolean (Database/Server/Portal/Resource in title)
19. `title_matches_primary` - Boolean (title entity matches primary)
20. `very_high_conf` - Boolean (db_keyword AND title_matches)

### URL Extraction Columns (21-24) - NEW

21. **`all_urls`** - All URLs detected in abstract (pipe-separated)
22. **`resource_url`** - Primary bioresource URL (filtered, scored)
23. **`has_resource_url`** - Boolean (True if resource URL exists)
24. **`url_context`** - Text surrounding primary URL (±50 chars)

### File-Specific Columns

**File 1b only** (+1 = 25 total):
- `baseline_entity_matched` - Which baseline entity was matched

**Files 2 & 3** (+1 = 25 total):
- `title_entity_in_ner` - Boolean (title entity in NER results)
- `baseline_entity_match` - Matched baseline entity (if any)

---

## URL Extraction Strategy

### Extraction Patterns

Captures URLs with/without protocol:
- `https?://domain.com/path`
- `www.domain.com/path`
- `ftp://domain.com/path`
- Domain patterns near context phrases ("available at", "accessible at")

### Exclusion List (Not Bioresources)

**Code Repositories**:
- github.com, gitlab.com, bitbucket.org, sourceforge.net

**Publisher/Reference Sites**:
- doi.org, pubmed, europepmc.org, sciencedirect.com, springer.com, nature.com

**Social Media/Professional**:
- twitter.com, linkedin.com, facebook.com, researchgate.net, academia.edu, orcid.org

**File Sharing**:
- dropbox.com, google.com/drive, figshare.com, zenodo.org, dryad.org

### Scoring Algorithm

URL scored based on:
- **+10**: Near context phrases ("available at", "accessible at", "web server")
- **+8**: Contains resource keywords (database, bio, genom, tool, portal)
- **+5**: Academic/government domain (.edu, .gov, .ac.uk, .org)
- **+3**: Resource subdomain (db., data., tools., portal.)
- **+2**: Appears in first half of abstract (prominence)
- **-1000**: Excluded domain (GitHub, DOI, social media) → filtered out

Highest-scoring non-excluded URL becomes `resource_url`.

---

## Results by File

### Quality Indicators Summary

| File | Total | DB Keyword | Title Match | Very High Conf |
|------|-------|------------|-------------|----------------|
| **1a: Baseline PMID** | 2,660 | 82.9% | 68.8% | **59.0%** 🟢 |
| **1b: Baseline Entity** | 4,750 | 69.9% | 48.2% | **39.8%** |
| **2: Linguistic (Novel)** | 6,609 | 31.3% | 46.9% | **14.4%** |
| **3: SetFit (Novel)** | 7,351 | 46.7% | 24.4% | **12.3%** |

### URL Extraction Summary

| File | Papers with URLs | Resource URLs Found | Resource URL % |
|------|-----------------|---------------------|----------------|
| **1a: Baseline PMID** | 2,660 | 2,641 | **99.3%** 🟢 |
| **1b: Baseline Entity** | 4,750 | 3,891 | **81.9%** |
| **2: Linguistic (Novel)** | 6,609 | 4,771 | **72.2%** |
| **3: SetFit (Novel)** | 7,351 | 1,802 | **24.5%** |

**Key Insight**: Baseline papers have near-perfect URL coverage (99.3%), while novel papers show variable coverage. Linguistic papers have better URL extraction (72%) vs SetFit (25%), suggesting SetFit may capture more conceptual/review papers.

---

## Example Output

### Sample 1: Resource URL Found

```
PMID: 33882119
Title: BC-TFdb: a database of transcription factor drivers in breast cancer

All URLs: https://www.dqweilab-sjtu.com/index.php | http://www.dqweilab-sjtu.com/index.php
Resource URL: https://www.dqweilab-sjtu.com/index.php
Has Resource URL: True
Context: ...methods for drug designing against BC. Database URL: https://www.dqweilab-sjtu.com/index.php...
```

### Sample 2: GitHub Excluded

```
PMID: 29949953
Title: MARSI: metabolite analogues for rational strain improvement

All URLs: https://github.com/biosustain/marsi
Resource URL: (none)
Has Resource URL: False
```

---

## Validation Checks ✅

1. **No PMID overlap** between baseline (1a) and novel files (2, 3)
2. **File 1a ⊂ baseline inventory** (85.5% coverage: 2,660 / 3,112)
3. **Total unique PMIDs** = 16,605 (perfect)
4. **URL extraction** applied to all papers successfully
5. **GitHub exclusion** working correctly

---

## Scripts Used

1. **Script 09**: `09_create_primary_resource_csv.py`
   Created union dataset with primary resource identification

2. **Script 10**: `10_create_filtered_datasets.py`
   Split into 4 filtered files with quality indicators

3. **Script 11**: `11_extract_urls.py` ⭐ NEW
   Added comprehensive URL extraction with bioresource filtering

**Run logs**: `pipeline_synthesis_2025-11-18/scripts/*_run.log`

---

## Statistics Files

- `filtering_statistics.txt` - Quality indicator stats per file
- `11_extract_urls_run.log` - URL extraction run log

---

## Use Cases

### High-Confidence Baseline Resources
```python
df = pd.read_csv('baseline_by_pmid.csv')
high_conf = df[df['very_high_conf'] == True]
# 1,569 papers (59%) with database keyword AND title match
```

### Novel Resources with URLs
```python
df = pd.read_csv('linguistic_excluding_baseline.csv')
novel_with_urls = df[df['has_resource_url'] == True]
# 4,771 papers (72%) with bioresource URLs
```

### Papers with Conflicting Entities
```python
df = pd.read_csv('setfit_excluding_baseline.csv')
conflicts = df[df['status'] == 'conflict']
# 130 papers with tied primary entities (need review)
```

### Extract All Bioresource URLs
```python
import pandas as pd

all_urls = []
for file in ['baseline_by_pmid.csv', 'baseline_by_entity_match.csv',
             'linguistic_excluding_baseline.csv', 'setfit_excluding_baseline.csv']:
    df = pd.read_csv(file)
    urls = df[df['has_resource_url'] == True][['pmid', 'resource_url', 'url_context']]
    all_urls.append(urls)

combined = pd.concat(all_urls)
# Total: 13,105 resource URLs across all papers
```

---

## Next Steps (Optional)

1. **Manual validation**: Sample papers with `very_high_conf = True` to verify accuracy
2. **URL validation**: Test if `resource_url` links are still active
3. **Entity consolidation**: Group papers by `resource_url` to find duplicate resources
4. **Baseline comparison**: Match novel resources to baseline by URL (not just name)
5. **Export for curation**: Create review CSV with high-confidence novel resources

---

**Created**: 2025-11-18
**Last Updated**: 2025-11-18
**Total Papers Processed**: 16,605
**Resource URLs Identified**: 13,105 (78.9%)
