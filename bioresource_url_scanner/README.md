# Bioresource URL Scanner V4

A high-performance, multi-threaded web scanner for detecting and classifying bioresource websites with automatic Wayback Machine fallback support.

**Status**: ✅ Production Ready
**Version**: V4
**Date**: 2025-11-19

---

## Overview

The Bioresource URL Scanner analyzes websites to determine if they are genuine bioresource databases/portals by scanning for specific indicators (keywords, content patterns, institutional affiliations). When original URLs fail, it automatically falls back to the Wayback Machine to rescue offline resources.

### Key Features

- ✅ **Multi-threaded scanning** - 10 concurrent workers
- ✅ **Domain-based rate limiting** - 1 req/sec per domain (polite crawling)
- ✅ **Meta refresh redirect support** - Follows JavaScript-free redirects
- ✅ **Wayback Machine fallback** - Automatically rescues offline URLs
- ✅ **Weighted indicator scoring** - 5-tier classification system
- ✅ **Comprehensive analysis** - Detailed statistics and reporting

---

## Quick Start

### 1. Setup

```bash
# Navigate to project
cd bioresource_url_scanner

# Activate virtual environment
source venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

### 2. Prepare URLs

```bash
# Extract URLs from GBC publication analysis dataset
python scripts/prepare_gbc_urls.py
```

**Output**: `data/gbc_urls.csv` (4,559 URLs ready for scanning)

### 3. Test Scanner (Optional)

```bash
# Run test on 20 random URLs (~40 seconds)
python scripts/scan_gbc_test.py
```

### 4. Full Scan

```bash
# Scan all URLs (75-90 minutes)
python scripts/scan_gbc_full.py
```

**Output**: `data/gbc_scan_results_YYYYMMDD_HHMMSS.csv`

### 5. Analyze Results

```bash
# Generate comprehensive analysis
python scripts/analyze_gbc_results.py
```

---

## Project Structure

```
bioresource_url_scanner/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── venv/                             # Virtual environment
│
├── data/                             # Data directory
│   ├── gbc_urls.csv                 # Prepared URLs for scanning
│   ├── gbc_test_results.csv         # Test scan results (20 URLs)
│   └── gbc_scan_results_*.csv       # Full scan results
│
├── scripts/                          # Scanner scripts
│   ├── prepare_gbc_urls.py          # Extract URLs from GBC dataset
│   ├── scan_gbc_test.py             # Test scanner (20 URLs)
│   ├── scan_gbc_full.py             # Production scanner (all URLs)
│   └── analyze_gbc_results.py       # Results analysis
│
├── docs/                             # Documentation
│   ├── WAYBACK_IMPLEMENTATION.md    # Wayback Machine details
│   └── url_spec/                    # Original specifications
│
└── plans/                            # Planning documents
    └── 2025-11-19_bioresource_url_scanner_integration.md
```

---

## Indicator Scoring System

### High-Value Indicators (Score: 3-5)

| Indicator | Score | Description |
|-----------|-------|-------------|
| NCBI, EBI, NIH, Ensembl, UniProt | 5 | Major institutional affiliations |
| search database, query database | 4 | Database functionality keywords |
| download data, bulk download | 4 | Data access indicators |
| genomics, proteomics, bioinformatics | 3 | Domain-specific terms |
| gene, protein, sequence, genome | 3 | Core biological terms |

### Medium-Value Indicators (Score: 2)

- repository, archive, collection, resource
- tool, platform, search, query, browse
- download, submit, curated, annotation, data

### Low-Value Indicators (Score: 1)

- database, server, portal, web service

### Title Bonus (+5)

Sites with these keywords in page title: database, server, portal, resource, tool, repository, archive, collection

## Likelihood Classification

Based on total score:

| Score Range | Likelihood | Description |
|-------------|-----------|-------------|
| ≥15 | **CRITICAL** | Very high confidence bioresource |
| 10-14 | **HIGH** | High confidence bioresource |
| 5-9 | **MEDIUM** | Moderate confidence |
| 1-4 | **LOW** | Low confidence |
| 0 | **VERY LOW** | No indicators found |

---

## Wayback Machine Support (V4)

When a URL fails (timeout, 404, connection error):

1. **Query Wayback API**: Check for archived snapshots
2. **Fetch Archive**: Retrieve most recent snapshot
3. **Score Content**: Apply same indicator system
4. **Track Rescue**: Mark with `wayback_used=True`

### Wayback Output Columns

- `wayback_used` - Boolean flag
- `wayback_url` - Full Wayback snapshot URL
- `wayback_snapshot_date` - Snapshot date (YYYY-MM-DD)

### Wayback Performance

**Test Results (20 URLs)**:
- Without Wayback: 70% live
- With Wayback: 90% live
- **Rescue rate: 20%**

**Expected Full Scan**:
- ~400-600 additional URLs recovered
- ~15-20% of failed URLs rescued

---

## Performance

### Test Scan (20 URLs)
- **Runtime**: 40 seconds
- **Throughput**: 0.5 URLs/sec
- **Live rate**: 90% (with Wayback)

### Full Scan (4,559 URLs)
- **Runtime**: 75-90 minutes
- **Throughput**: ~1 URL/sec
- **Expected live rate**: 60-65%

### Results (Production Scan with Wayback - V4)
- **Live URLs**: 3,716/4,559 (81.5%)
- **CRITICAL+HIGH**: 3,118/4,559 (68.4%)
- **Mean score**: 28.6
- **Wayback rescued**: 1,258 (27.6% of total, 62.9% of failures)
- **Runtime**: 75-90 minutes

---

## Output Format

Results saved as CSV with columns:

### Core Columns
- `url` - Original URL
- `is_live` - Boolean (True if accessible)
- `status_code` - HTTP status code
- `total_score` - Combined indicator score
- `likelihood` - Classification (CRITICAL/HIGH/MEDIUM/LOW/VERY LOW)

### Scoring Details
- `base_score` - Score from indicators
- `title_bonus` - Bonus from title keywords
- `indicators_found` - List of matched indicators

### Performance Metrics
- `response_time_ms` - Response time in milliseconds
- `meta_redirects` - Number of meta refresh redirects followed
- `final_url` - Final URL after redirects

### Wayback Columns
- `wayback_used` - Boolean (True if rescued via Wayback)
- `wayback_url` - Wayback snapshot URL
- `wayback_snapshot_date` - Snapshot date

### Metadata
- `pmid` - PubMed ID
- `primary_entity_long` - Full resource name
- `primary_entity_short` - Short resource name
- `is_gcbr` - Boolean (Global Core Biodata Resource)
- `domain` - Domain name

---

## Analysis Features

The `analyze_gbc_results.py` script provides:

- **Overall statistics**: Live/failed counts, percentages
- **Likelihood distribution**: Breakdown by classification
- **Score statistics**: Mean, median, quartiles, std dev
- **Wayback rescue analysis**: Count, scores, top rescues
- **Error breakdown**: Categorized failure reasons
- **Domain analysis**: Top domains with performance metrics
- **GCBR performance**: Uptime and detection rates
- **Zero/low scorer identification**: Quality checks
- **Top performers**: Highest scoring resources
- **JSON summary**: Machine-readable statistics

---

## Configuration

Edit configuration constants in scanner scripts:

```python
# Performance tuning
MAX_WORKERS = 10          # Concurrent threads (1-20)
DOMAIN_DELAY = 1.0        # Seconds between requests per domain
TIMEOUT = 20              # Request timeout in seconds
WAYBACK_TIMEOUT = 15      # Wayback API timeout

# Content limits
MAX_CONTENT_SIZE = 512000  # Max bytes to analyze (512KB)
MAX_META_REDIRECTS = 3     # Max meta refresh hops

# Scoring thresholds
CRITICAL_THRESHOLD = 15
HIGH_THRESHOLD = 10
MEDIUM_THRESHOLD = 5
LOW_THRESHOLD = 1
```

---

## Version History

### V4 (2025-11-19) - Current
- Added Wayback Machine fallback support
- Added `wayback_used`, `wayback_url`, `wayback_snapshot_date` columns
- Improved recovery rate from 70% → 90% (test set)
- Suppressed XML parsing warnings
- Full production scan: 4,559 URLs, 46.5% high-quality

### V3 (2025-11-19)
- Added meta refresh redirect support
- Rescued BloodSpot, RiPPMiner, SFLD
- Improved detection from 64% → 66% high-quality

### V2 (2025-11-19)
- Complete redesign of indicator system
- Removed non-working indicators
- Added practical terms (genomics, proteomics, etc.)
- Increased timeout to 20 seconds
- Improved detection from 12% → 64% high-quality

### V1 (2025-11-19)
- Initial release
- Multi-threaded scanning
- Domain-based rate limiting
- Basic indicator system

---

## Known Limitations

1. **JavaScript-heavy sites**: Cannot execute JavaScript, may miss dynamic content
2. **Authentication required**: Cannot access sites requiring login
3. **CAPTCHA protected**: Cannot bypass CAPTCHA challenges
4. **Rate limiting impact**: Conservative rate limiting may increase scan time
5. **Wayback availability**: Not all URLs are archived in Wayback Machine
6. **Snapshot age**: Wayback snapshots may be months/years old

---

## Troubleshooting

### High failure rate
- Check network connectivity
- Verify domain rate limiting isn't too aggressive
- Consider increasing timeout values

### Low scores for known bioresources
- Review indicator list for missing keywords
- Check if site uses non-standard terminology
- Consider adjusting title bonus keywords

### Slow performance
- Reduce MAX_WORKERS if network is bottleneck
- Increase DOMAIN_DELAY if being rate limited
- Check for slow DNS resolution

### Wayback not rescuing
- Verify internet connectivity to archive.org
- Check if Wayback is being rate limited
- Some URLs may not be archived

---

## References

### Documentation
- [Wayback Implementation Details](docs/WAYBACK_IMPLEMENTATION.md)
- [Original URL Specification](docs/url_spec/README.md)
- [Planning Document](plans/2025-11-19_bioresource_url_scanner_integration.md)

### External Resources
- [Wayback Machine API](https://archive.org/help/wayback_api.php)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Library](https://requests.readthedocs.io/)

---

## License

Internal use for GBC Biodata Inventory Project.

---

**Version**: V4
**Last Updated**: 2025-11-19
**Author**: GBC Biodata Inventory Team
