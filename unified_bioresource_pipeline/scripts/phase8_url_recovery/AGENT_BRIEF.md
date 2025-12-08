# URL Recovery Agent Brief

## Your Task
Search the web to find URLs for bioresource databases listed in your assigned chunk file.

---

## CRITICAL: Output File Specification

Your output file **MUST** follow this exact format for automated merging.

### Required Filename Pattern
```
websearch_results_chunk_XX.csv
```
Where `XX` matches your input chunk number (e.g., `websearch_results_chunk_01.csv`)

### Required Columns (in order)
| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `original_record_num` | integer | YES | Copy from input - DO NOT MODIFY |
| `database_name` | string | YES | Copy from input - DO NOT MODIFY |
| `long_database_name` | string | YES | Copy from input - DO NOT MODIFY |
| `found_urls` | string | YES | URL found OR `NOT_FOUND` |
| `url_source` | string | YES | Must be `web_search` or `not_available` |
| `match_quality` | string | YES | `HIGH`, `MEDIUM`, `LOW`, or empty |
| `notes` | string | NO | Optional explanation |

### Column Value Rules

**found_urls:**
- Single URL: `https://example.org/database`
- Multiple URLs: `https://example1.org|https://example2.org` (pipe-separated)
- Not found: `NOT_FOUND` (exact string, all caps)

**url_source:**
- If URL found: `web_search`
- If not found: `not_available`

**match_quality:**
- `HIGH` - URL contains database name/abbreviation
- `MEDIUM` - URL found in clear context
- `LOW` - URL found but connection uncertain
- Empty if `found_urls` is `NOT_FOUND`

### Example Output Row
```csv
original_record_num,database_name,long_database_name,found_urls,url_source,match_quality,notes
123,BioDB,Biological Database,https://biodb.org,web_search,HIGH,Official website found
124,MyData,My Data Resource,NOT_FOUND,not_available,,No dedicated website found
```

---

## What We're Looking For

**WANT:** Dedicated web interfaces for biological databases
- Example: `genome.ucsc.edu`, `www.proteinatlas.org`, `biocyc.org`
- These are websites where users can query, browse, or interact with data

---

## MANDATORY EXCLUSIONS - DO NOT RETURN THESE URLs

**These URL types will be AUTOMATICALLY REJECTED by the merge script.**
If you only find these types of URLs for a database, mark it as `NOT_FOUND`.

### Code Repositories
| Pattern | Example | Why Excluded |
|---------|---------|--------------|
| `github.com/*` | `github.com/user/repo` | Code repository, not web interface |
| `*.github.io/*` | `mydb.github.io` | GitHub Pages hosted |
| `gitlab.com/*` | `gitlab.com/user/repo` | Code repository |
| `bitbucket.org/*` | `bitbucket.org/user/repo` | Code repository |
| `sourceforge.net/*` | `sourceforge.net/projects/x` | Software hosting |

### Data Archives & DOIs
| Pattern | Example | Why Excluded |
|---------|---------|--------------|
| `zenodo.org/*` | `zenodo.org/record/123` | File archive |
| `doi.org/*` | `doi.org/10.1234/xyz` | DOI resolver (not direct interface) |
| `datadryad.org/*` | `datadryad.org/stash/dataset/...` | Data archive |
| `dryad.*/` | `doi.org/10.5061/dryad.xyz` | Dryad DOI |
| `figshare.com/*` | `figshare.com/articles/...` | File sharing |
| `osf.io/*` | `osf.io/abc123` | Open Science Framework |

### File Servers
| Pattern | Example | Why Excluded |
|---------|---------|--------------|
| `ftp://*` | `ftp://ftp.ncbi.nih.gov` | FTP server |
| `ftp.*` | `ftp.ebi.ac.uk` | FTP server |

### Package Repositories
| Pattern | Example | Why Excluded |
|---------|---------|--------------|
| `cran.r-project.org/*` | `cran.r-project.org/package=x` | R package |
| `bioconductor.org/packages/*` | `bioconductor.org/packages/x` | Bioconductor package |
| `pypi.org/*` | `pypi.org/project/x` | Python package |

### Generic Institutional (without specific path)
| Pattern | Example | Why Excluded |
|---------|---------|--------------|
| `*.edu` (root only) | `stanford.edu`, `mit.edu` | Generic institution |
| `*.ac.uk` (root only) | `cam.ac.uk` | Generic institution |

**Note:** Institutional URLs WITH specific database paths ARE acceptable:
- ✅ `genome.ucsc.edu` - specific database
- ✅ `www.ebi.ac.uk/chebi` - specific database path
- ❌ `stanford.edu` - just institution root

---

## Search Strategy
For each record:
1. Search: `"{database_name}" database`
2. Search: `"{long_database_name}" bioinformatics`
3. Look for dedicated web interface in results
4. **If only GitHub/Zenodo/DOI found → mark as `NOT_FOUND`**

## Important Notes
- Dead URLs are OK to record (we track them separately)
- When uncertain, include the URL with LOW quality
- One URL per database is sufficient
- **Preserve original_record_num exactly** - this is the merge key!
- **If the database only exists as code on GitHub, mark `NOT_FOUND`** - we want web interfaces

---

## Checklist Before Submitting
- [ ] File named `websearch_results_chunk_XX.csv`
- [ ] All required columns present
- [ ] `original_record_num` values unchanged from input
- [ ] `url_source` is `web_search` for found URLs
- [ ] No spaces in URLs (use pipe `|` to separate multiple)
- [ ] **NO GitHub, Zenodo, DOI, Dryad, or Figshare URLs included**
