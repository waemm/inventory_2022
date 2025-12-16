# Bioresource Removal Patterns

**Purpose:** Document patterns used to identify non-database resources for removal from the bioresource inventory.

**Last Updated:** 2025-12-16

---

## Overview

These patterns help identify resources that are **not online databases** but rather:
- Code repositories
- Software packages
- File downloads
- Documentation sites

---

## URL Patterns

Check the `extracted_url` column for these patterns (case-insensitive unless noted):

### Code Repositories
| Pattern | Description | Example |
|---------|-------------|---------|
| `github` | GitHub repositories | github.com/user/repo |
| `gitlab` | GitLab repositories | gitlab.com/user/repo |
| `bitbucket` | Bitbucket repositories | bitbucket.org/user/repo |
| `sourceforge` | SourceForge projects | sourceforge.net/projects/x |

### Package Managers / Software Distribution
| Pattern | Description | Example |
|---------|-------------|---------|
| `cran.r-project` | R packages (CRAN) | cran.r-project.org/package=X |
| `bioconductor` | Bioconductor R packages | bioconductor.org/packages/X |
| `pypi` | Python packages | pypi.org/project/X |
| `anaconda` | Anaconda packages | anaconda.org/conda-forge/X |
| `conda-forge` | Conda-forge packages | conda-forge.org |
| `npm` | Node.js packages | npmjs.com/package/X |
| `docker` | Docker containers | hub.docker.com/r/X |

### AI/ML Platforms
| Pattern | Description | Example |
|---------|-------------|---------|
| `huggingface` | HuggingFace models/datasets | huggingface.co/X |

### Data Archives (Not Databases)
| Pattern | Description | Example |
|---------|-------------|---------|
| `zenodo` | Zenodo data deposits | zenodo.org/record/X |
| `figshare` | Figshare data deposits | figshare.com/articles/X |
| `datashare` | Data sharing platforms | ctndatashare.org |

### Documentation Sites
| Pattern | Description | Example |
|---------|-------------|---------|
| `readthedocs.io` | ReadTheDocs documentation | X.readthedocs.io |

### Download/FTP Links
| Pattern | Description | Example |
|---------|-------------|---------|
| `download` | Download pages | site.com/download.html |
| `ftp` | FTP file servers | ftp.ncbi.nlm.nih.gov |

### Pathway/Wiki Sites
| Pattern | Description | Example |
|---------|-------------|---------|
| `wikipathways` | WikiPathways entries | wikipathways.org/index.php/Pathway:X |

---

## Title Keywords

Check the `paper_titles` column for these keywords (case-insensitive):

| Keyword | Indicates | Action |
|---------|-----------|--------|
| `python library` | Software tool | Flag for removal |
| `package` | Software package | Review - may be valid database |
| `standardized set` | Measurement instrument | Flag for removal |

---

## Pattern Match Counts (as of 2025-12-16)

### URL Patterns
| Pattern | Matches |
|---------|---------|
| github | 50 |
| readthedocs.io | 11 |
| bioconductor | 11 |
| cran.r-project | 11 |
| download | 8 |
| pypi | 7 |
| gitlab | 6 |
| anaconda | 4 |
| huggingface | 3 |
| docker | 2 |
| wikipathways | 1 |
| ftp | 1 |
| datashare | 1 |

### Title Keywords
| Keyword | Matches |
|---------|---------|
| package | 17 |
| python library | 1 |

---

## Implementation

The `grep_remove` column in the processed files is set to `TRUE` when any URL pattern matches.

### Python Code Example
```python
url_patterns = [
    'github', 'gitlab', 'bitbucket', 'sourceforge',
    'cran.r-project', 'bioconductor', 'pypi', 'anaconda',
    'conda-forge', 'npm', 'docker', 'huggingface',
    'zenodo', 'figshare', 'datashare',
    'readthedocs.io', 'download', 'ftp', 'wikipathways'
]

def check_url(url):
    if pd.isna(url):
        return None
    url_lower = str(url).lower()
    for pattern in url_patterns:
        if pattern in url_lower:
            return True
    return None

df['grep_remove'] = df['extracted_url'].apply(check_url)
```

---

## Results Summary

| Metric | Count |
|--------|-------|
| Total resources | 1,597 |
| Flagged by URL patterns | 92 |
| Manually reviewed & removed | 227 |
| Final filtered inventory | 1,370 |

---

## Files

| File | Description |
|------|-------------|
| `new_resources_with_naming_review_fixed_with_grep_v2.csv` | With grep_remove column |
| `new_resources_final_filtered.csv` | Final filtered inventory (1,370 resources) |
