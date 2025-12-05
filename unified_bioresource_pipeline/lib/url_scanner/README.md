# URL Scanner Module

Integrated bioresource URL scanner for validating and scoring resource URLs.

## Overview

This module scans URLs to:
- Validate URL accessibility (live vs failed)
- Score pages for bioresource indicators
- Provide likelihood classification (CRITICAL, HIGH, MEDIUM, LOW, VERY LOW)
- Support Wayback Machine fallback for failed URLs
- Handle meta-refresh redirects

## Features

- **Multi-threaded scanning**: Concurrent URL processing with configurable workers
- **Domain rate limiting**: Respectful crawling with per-domain delays
- **Wayback Machine fallback**: Automatically tries archived versions for failed URLs
- **Content scoring**: Scores pages based on bioresource indicators (keywords, patterns)
- **Session-based output**: Integrates with unified pipeline session directories

## Integration

Originally from: `bioresource_url_scanner/scripts/scan_gbc_full.py`
Integrated: 2025-12-05
Location: `lib/url_scanner/`

## Usage

### Within Pipeline (Script 18)

```bash
# Session mode
python scripts/phase6_scanning/18_scan_urls_set_c.py --session-dir results/2025-12-04-143052-a3f9b

# With custom scanner parameters
python scripts/phase6_scanning/18_scan_urls_set_c.py \
    --session-dir results/2025-12-04-143052-a3f9b \
    --workers 20 \
    --timeout 30 \
    --domain-delay 1.5
```

### Standalone CLI

```bash
cd lib/url_scanner

# Basic scan (looks for data/gbc_urls.csv)
python scan_urls.py

# Custom input
python scan_urls.py --input-file /path/to/urls.csv

# Session-based output
python scan_urls.py --input-file urls.csv --session-dir /path/to/session
```

### Programmatic API

```python
from lib.url_scanner import BioresourceScanner
import pandas as pd

# Load URLs
df = pd.read_csv('urls.csv')  # Must have 'url' column
urls_data = df.to_dict('records')

# Create scanner
scanner = BioresourceScanner(
    max_workers=10,
    domain_delay=1.0,
    timeout=20
)

# Scan URLs
results = scanner.scan_batch(urls_data, show_progress=True)
results_df = pd.DataFrame(results)
```

## Input Format

CSV file with at minimum a `url` column. Optional columns:
- `id`: Identifier (e.g., PMID)
- `domain`: Domain name (auto-calculated if not provided)
- `entity_long`: Resource name (long form)
- `entity_short`: Resource name (short form)

## Output Format

Results include:
- `is_live`: Boolean - URL is accessible
- `status_code`: HTTP status code
- `total_score`: Combined score for bioresource indicators
- `base_score`: Score from content indicators
- `title_bonus`: Bonus points for title keywords
- `likelihood`: Classification (CRITICAL, HIGH, MEDIUM, LOW, VERY LOW)
- `indicators_found`: List of matched indicators
- `wayback_used`: Boolean - Result from Wayback Machine
- `wayback_url`: Wayback snapshot URL (if used)
- `wayback_snapshot_date`: Date of Wayback snapshot
- `meta_redirects`: Number of meta-refresh redirects followed
- `final_url`: Final URL after redirects
- `response_time_ms`: Response time in milliseconds
- `error_message`: Error details (if failed)

## Configuration

### Scanner Parameters

- `max_workers`: Concurrent workers (default: 10)
- `domain_delay`: Delay between requests to same domain (default: 1.0s)
- `timeout`: Request timeout per URL (default: 20s)
- `max_content_size`: Max content to analyze (default: 512KB)
- `max_meta_redirects`: Max meta-refresh hops (default: 3)
- `wayback_timeout`: Wayback API timeout (default: 15s)

### Scoring System

**Indicator Scores** (V3 - proven on 964 URLs: 47.2% HIGH+CRITICAL):
- Authority sites (NCBI, EBI, NIH, etc.): 5 points
- Database features (search, query, browse): 4 points
- Domain keywords (genomics, proteomics, etc.): 3 points
- Generic resources (repository, archive, etc.): 2 points
- Basic database terms: 1 point
- Title bonus: 5 points if database keyword in page title

**Likelihood Thresholds**:
- CRITICAL: score >= 15
- HIGH: score >= 10
- MEDIUM: score >= 5
- LOW: score >= 1
- VERY LOW: score < 1

## Performance

- **Typical runtime**: 75-90 minutes for ~4,500 URLs
- **Throughput**: ~1 URL/second with 10 workers
- **Rate limiting**: 1 request/second per domain
- **Timeout**: 20 seconds per request (configurable)

## Dependencies

See `requirements.txt`:
- requests (HTTP client)
- beautifulsoup4 + lxml (HTML parsing)
- pandas (data handling)
- tqdm (progress tracking)

## Notes

- The original `bioresource_url_scanner` directory remains unchanged
- All scanner functionality is now available within the unified pipeline
- Session-based workflows automatically organize scanner outputs
- Backward compatible with existing pipeline scripts
