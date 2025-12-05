# URL Scanner - Quick Start Guide

## Integration Complete (2025-12-05)

The bioresource URL scanner is now integrated into `lib/url_scanner/`.

## Most Common Usage

### Within Pipeline (Script 18)

```bash
# Session mode (RECOMMENDED)
python scripts/phase6_scanning/18_scan_urls_set_c.py \
    --session-dir results/2025-12-04-143052-a3f9b

# With specific dedup profile
python scripts/phase6_scanning/18_scan_urls_set_c.py \
    --session-dir results/2025-12-04-143052-a3f9b \
    --profile balanced

# Adjust scanner performance
python scripts/phase6_scanning/18_scan_urls_set_c.py \
    --session-dir results/2025-12-04-143052-a3f9b \
    --workers 20 \
    --timeout 30
```

## Key Parameters

- `--workers N` - Concurrent workers (default: 10)
- `--timeout N` - Request timeout in seconds (default: 20)
- `--domain-delay N.N` - Delay between requests to same domain (default: 1.0)
- `--profile {conservative,balanced,aggressive}` - Dedup profile (default: aggressive)

## Output Location

For session mode:
- Scan results: `{session}/06_scanning/scan_results_{session_id}.csv`
- Merged data: `{session}/06_scanning/set_c_with_url_scan.csv`
- Statistics: `{session}/06_scanning/url_scan_statistics.txt`

## Performance

- **Runtime**: ~75-90 minutes for 4,500 URLs
- **Throughput**: ~1 URL/second (default settings)
- **Memory**: Low (streaming results)

## Features

- Validates URL accessibility
- Scores bioresource indicators
- Wayback Machine fallback for dead links
- Meta-refresh redirect following
- Domain-based rate limiting
- Session-aware output

## Quick Test

```bash
# Test import
python -c "from lib.url_scanner import BioresourceScanner; print('OK')"

# Check Script 18 syntax
python -m py_compile scripts/phase6_scanning/18_scan_urls_set_c.py
```

## Programmatic Use

```python
from lib.url_scanner import BioresourceScanner
import pandas as pd

# Load URLs
df = pd.read_csv('urls.csv')  # needs 'url' column
urls_data = df.to_dict('records')

# Scan
scanner = BioresourceScanner(max_workers=10, timeout=20)
results = scanner.scan_batch(urls_data)
results_df = pd.DataFrame(results)
```

## Help

```bash
# Script 18 help
python scripts/phase6_scanning/18_scan_urls_set_c.py --help

# Full documentation
cat lib/url_scanner/README.md
```

## Status: READY FOR USE

All integration testing complete. Original `bioresource_url_scanner` directory remains unchanged at parent level.
