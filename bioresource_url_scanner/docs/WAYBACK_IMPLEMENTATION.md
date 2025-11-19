# Wayback Machine Implementation - V4 Scanner

## Overview

The V4 scanner implements automatic fallback to the Wayback Machine (Internet Archive) when original URLs fail. This significantly increases the number of bioresources that can be analyzed, even if their original websites are offline.

## How It Works

### 1. **Primary Scan**
- Scanner attempts to fetch the original URL
- Follows HTTP redirects and meta refresh redirects
- If successful (HTTP 200-399), scores the live content

### 2. **Wayback Fallback (on failure)**
If the original URL fails (timeout, 404, connection error, etc.):
1. Query Wayback Availability API:
   ```
   https://archive.org/wayback/available?url={original_url}
   ```
2. API returns most recent snapshot URL and timestamp
3. Scanner fetches archived page
4. Scores archived content using same indicators
5. Marks result with `wayback_used=True`

### 3. **Scoring**
- Wayback content scored identically to live content
- Same indicator system (NCBI, EBI, genomics, database, etc.)
- Same likelihood classification (CRITICAL, HIGH, MEDIUM, LOW, VERY LOW)

## New Columns

Three new columns added to results:

| Column | Type | Description |
|--------|------|-------------|
| `wayback_used` | Boolean | True if URL was rescued via Wayback Machine |
| `wayback_url` | String | Full Wayback snapshot URL (e.g., `https://web.archive.org/web/20240212.../`) |
| `wayback_snapshot_date` | String | Date of snapshot in YYYY-MM-DD format |

## Test Results

### Without Wayback (V3)
- **Live URLs**: 14/20 (70%)
- **Failed**: 6/20 (30%)

### With Wayback (V4)
- **Live URLs**: 18/20 (90%)
- **Failed**: 2/20 (10%)
- **Rescued**: 4/20 (20%)

### Rescued Resources

| Resource | Score | Snapshot Date | Status |
|----------|-------|---------------|--------|
| Tetrahymena functional genomics database | 53 pts | 2025-01-15 | CRITICAL |
| Rice Expression Database | 37 pts | 2024-02-12 | CRITICAL |
| TOMATOMICS | 32 pts | 2016-11-11 | CRITICAL |
| ANTISTAPHYBASE | 8 pts | 2018-05-30 | MEDIUM |

**Impact**: 20% improvement in URL recovery rate

## Implementation Details

### Rate Limiting
- Wayback API queries respect same domain rate limiting (1 req/sec)
- Wayback content fetches also rate limited
- Shorter timeout for API queries (15s vs 20s for content)

### Error Handling
```python
# Original URL failed - try Wayback
wayback_url, snapshot_date = self.get_wayback_snapshot(url)

if wayback_url:
    try:
        # Fetch and score archived content
        result['wayback_used'] = True
        result['wayback_url'] = wayback_url
        result['wayback_snapshot_date'] = snapshot_date
    except Exception as e:
        # Both original and Wayback failed
        result['error_message'] = f"{original_error} | Wayback: {wayback_error}"
```

### Wayback API Response

Example API response:
```json
{
  "archived_snapshots": {
    "closest": {
      "available": true,
      "url": "https://web.archive.org/web/20240212120000/http://red.dna.affrc.go.jp",
      "timestamp": "20240212120000",
      "status": "200"
    }
  }
}
```

## Scripts Updated

1. **scan_gbc_test.py** - Test scanner with Wayback support
2. **scan_gbc_full.py** - Production scanner with Wayback support
3. **analyze_gbc_results.py** - Analysis script with Wayback statistics

## Usage

### Run Test Scan (20 URLs)
```bash
source venv/bin/activate
python scripts/scan_gbc_test.py
```

### Run Full Scan (4,559 URLs)
```bash
source venv/bin/activate
python scripts/scan_gbc_full.py
```

### Analyze Results
```bash
python scripts/analyze_gbc_results.py
```

## Performance Impact

- **Additional latency**: ~1-2 seconds per failed URL (Wayback API + fetch)
- **Success rate increase**: +20% (test dataset)
- **No impact on live URLs**: Wayback only attempted when original fails

## Benefits

1. **Higher recovery rate**: Rescue offline bioresources
2. **Historical access**: Analyze resources that no longer exist
3. **Same quality**: Wayback content scored identically to live content
4. **Transparent tracking**: Clear indication via `wayback_used` column
5. **Snapshot dates**: Know when resource was last captured

## Limitations

1. **Not all URLs archived**: Some URLs have no Wayback snapshots
2. **Older snapshots**: Content may be outdated (months/years old)
3. **JavaScript limitations**: Wayback may not execute all JS (same as live scan)
4. **Additional latency**: Adds 1-2 seconds per failed URL

## Future Enhancements

1. **Timestamp selection**: Allow fetching specific snapshot dates
2. **Multiple snapshots**: Compare current vs historical content
3. **Snapshot quality scoring**: Penalize very old snapshots
4. **CDX API**: Use CDX API for faster availability checks

---

**Version**: V4
**Date**: 2025-11-19
**Author**: BioresourceScanner Team
