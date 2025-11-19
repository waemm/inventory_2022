#!/usr/bin/env python3
"""
02_scan_urls.py - Multi-threaded Bioresource Website Scanner

Scans URLs with domain-based rate limiting to identify bioresource websites
using weighted indicator scoring system.

Features:
- Multi-threaded scanning (10-20 workers)
- Domain-based rate limiting (1 req/sec per domain)
- 3-step analysis: connectivity, URL path, content scanning
- Weighted scoring: 5 (CRITICAL) to 1 (LOWEST)

Author: Warren
Date: 2025-11-19
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Configuration
MAX_WORKERS = 10  # Threads for pilot (increase to 20 for full dataset)
DOMAIN_DELAY = 1.0  # Seconds between requests to same domain
TIMEOUT = 10  # Request timeout in seconds
MAX_CONTENT_SIZE = 512000  # First 500KB of content

# Indicator dictionary with weighted scores
INDICATOR_SCORES = {
    # CRITICAL: Structural/Metadata & Regulatory (Score: 5)
    'schema.org/Dataset': 5,
    'itemtype="https://schema.org/Dataset': 5,
    'REST API': 5,
    'data-api': 5,
    'Swagger': 5,
    'GraphQL': 5,
    'OpenAPI': 5,
    'IRB': 5,
    'Ethics Committee': 5,

    # HIGH: Intentional Database Text (Score: 4)
    'search our database': 4,
    'query tool': 4,
    'query interface': 4,
    'programmatic access': 4,
    'download full dataset': 4,
    'NIH-funded': 4,
    'HIPAA': 4,
    'EBI': 4,
    'NCBI': 4,

    # MEDIUM: Format Specificity (Score: 3)
    'FASTA': 3,
    'VCF': 3,
    'GFF': 3,
    'PDB': 3,
    'ClinicalTrial': 3,
    'Accession': 3,
    'Identifier': 3,
    'cram': 3,
    'bed file': 3,

    # LOW: Bulk Access (Score: 2)
    '/ftp/': 2,
    '/download/': 2,
    '/datasets/': 2,
    '/api/': 2,
    'Data Submission': 2,
    'Deposit Data': 2,
    'Curation': 2,

    # LOWEST: General Terms (Score: 1)
    'Data Repository': 1,
    'Bioresource': 1,
    'Knowledgebase': 1,
    'Genomics': 1,
    'Proteomics': 1,
    'Metabolomics': 1,
}


class DomainRateLimiter:
    """Thread-safe per-domain rate limiting"""

    def __init__(self, delay_seconds=1.0):
        self.delay = delay_seconds
        self.last_request = {}  # domain -> timestamp
        self.lock = threading.Lock()

    def wait_if_needed(self, url):
        """Block until enough time has passed for this domain"""
        try:
            domain = urlparse(url).netloc
        except Exception:
            domain = "unknown"

        with self.lock:
            if domain in self.last_request:
                elapsed = time.time() - self.last_request[domain]
                if elapsed < self.delay:
                    sleep_time = self.delay - elapsed
                    time.sleep(sleep_time)
            self.last_request[domain] = time.time()

        return domain


class BioresourceScanner:
    """Multi-threaded bioresource website scanner"""

    def __init__(self, max_workers=10, domain_delay=1.0):
        self.max_workers = max_workers
        self.rate_limiter = DomainRateLimiter(domain_delay)

        # Session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioresourceScanner/1.0 (Biodata Inventory Project; contact@example.com)'
        })

    def scan_url(self, url_data):
        """
        Scan single URL with 3-step analysis

        Args:
            url_data: dict with 'url' and metadata

        Returns:
            dict with all scoring data
        """
        url = url_data['url']

        # Initialize result
        result = {
            **url_data,  # Include all input metadata
            'is_live': False,
            'status_code': None,
            'total_score': 0,
            'likelihood': 'VERY LOW',
            'indicators_found': [],
            'title_indicators': [],
            'content_indicators': [],
            'url_indicators': [],
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0,
            'lowest_count': 0,
            'response_time_ms': None,
            'content_length_bytes': None,
            'error_message': None,
            'scanned_at': datetime.now().isoformat(),
        }

        # Rate limit for this domain
        domain = self.rate_limiter.wait_if_needed(url)

        try:
            # 1. Connectivity Check
            start_time = time.time()
            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            response_time = (time.time() - start_time) * 1000  # ms

            result['status_code'] = response.status_code
            result['response_time_ms'] = round(response_time, 2)
            result['is_live'] = 200 <= response.status_code < 400

            if not result['is_live']:
                result['error_message'] = f"HTTP {response.status_code}"
                return result

            # Get content
            content = response.content[:MAX_CONTENT_SIZE].decode('utf-8', errors='ignore')
            result['content_length_bytes'] = len(content)

            # 2. URL Path Scanning
            url_score, url_indicators = self._scan_url_path(url)

            # 3. Content Scanning
            soup = BeautifulSoup(content, 'lxml')
            title_score, content_score, title_indicators, content_indicators = self._scan_content(soup, content)

            # 4. Calculate total score
            result['total_score'] = url_score + title_score + content_score
            result['likelihood'] = self._classify_score(result['total_score'])

            # Combine indicators
            result['url_indicators'] = url_indicators
            result['title_indicators'] = title_indicators
            result['content_indicators'] = content_indicators
            result['indicators_found'] = url_indicators + title_indicators + content_indicators

            # Count by score level
            result = self._count_by_level(result)

        except requests.exceptions.Timeout:
            result['error_message'] = 'Timeout (10s)'
        except requests.exceptions.ConnectionError as e:
            result['error_message'] = f'Connection Error: {str(e)[:50]}'
        except Exception as e:
            result['error_message'] = f'Error: {str(e)[:100]}'

        return result

    def _scan_url_path(self, url):
        """Scan URL path for indicators"""
        score = 0
        indicators = []
        url_lower = url.lower()

        for term, term_score in INDICATOR_SCORES.items():
            if term.startswith('/') and term in url_lower:
                # File extension gets 2x score
                if any(ext in term for ext in ['.fasta', '.vcf', '.gff', '.cram', '.bed']):
                    score += term_score * 2
                    indicators.append(f"{term.strip('/')} (2x)")
                else:
                    score += term_score
                    indicators.append(term.strip('/'))

        return score, indicators

    def _scan_content(self, soup, content):
        """Scan HTML content and title for indicators"""
        title_score = 0
        content_score = 0
        title_indicators = []
        content_indicators = []

        # Extract title and content
        page_title = soup.title.string.lower() if soup.title and soup.title.string else ""
        content_lower = content[:MAX_CONTENT_SIZE].lower()

        for term, term_score in INDICATOR_SCORES.items():
            if term.startswith('/'):  # Skip path indicators
                continue

            term_lower = term.lower()

            # Check title (higher weight)
            if term_lower in page_title:
                title_score += term_score
                title_indicators.append(term)
            # Check content (don't double-count if in title)
            elif term_lower in content_lower:
                content_score += term_score
                content_indicators.append(term)

        return title_score, content_score, title_indicators, content_indicators

    def _classify_score(self, score):
        """Map score to likelihood category"""
        if score >= 15:
            return 'CRITICAL'
        elif score >= 10:
            return 'HIGH'
        elif score >= 5:
            return 'MEDIUM'
        elif score >= 1:
            return 'LOW'
        else:
            return 'VERY LOW'

    def _count_by_level(self, result):
        """Count indicators by score level"""
        for indicator in result['indicators_found']:
            # Remove " (2x)" suffix for lookup
            clean_indicator = indicator.replace(" (2x)", "")

            # Find indicator in dictionary (handle both path and content)
            for term, score in INDICATOR_SCORES.items():
                # Match path indicators
                if term.startswith('/') and clean_indicator == term.strip('/'):
                    self._increment_level_count(result, score)
                    break
                # Match content indicators
                elif not term.startswith('/') and clean_indicator == term:
                    self._increment_level_count(result, score)
                    break

        return result

    def _increment_level_count(self, result, score):
        """Increment appropriate level counter"""
        if score == 5:
            result['critical_count'] += 1
        elif score == 4:
            result['high_count'] += 1
        elif score == 3:
            result['medium_count'] += 1
        elif score == 2:
            result['low_count'] += 1
        elif score == 1:
            result['lowest_count'] += 1

    def scan_batch(self, urls_data):
        """Scan multiple URLs with ThreadPoolExecutor"""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scan_url, url_data): url_data
                      for url_data in urls_data}

            for future in tqdm(as_completed(futures), total=len(urls_data),
                             desc="Scanning URLs", unit="url"):
                results.append(future.result())

        return results


def main():
    """Main scanning workflow"""
    print("=" * 70)
    print("Bioresource URL Scanner - Multi-threaded Scanning")
    print("=" * 70)

    # Load pilot URLs
    input_path = DATA_DIR / "pilot_urls.csv"

    if not input_path.exists():
        print(f"\n❌ Input file not found: {input_path}")
        print("   Run 01_sample_urls.py first to generate pilot URLs")
        sys.exit(1)

    print(f"\n📂 Loading URLs from: {input_path.name}")
    df = pd.read_csv(input_path)
    print(f"   Total URLs: {len(df)}")

    # Convert to list of dicts
    urls_data = df.to_dict('records')

    # Initialize scanner
    print(f"\n⚙️  Configuration:")
    print(f"   Workers: {MAX_WORKERS}")
    print(f"   Domain delay: {DOMAIN_DELAY}s")
    print(f"   Timeout: {TIMEOUT}s")
    print(f"   Indicators: {len(INDICATOR_SCORES)}")

    # Scan
    print(f"\n🔍 Scanning...")
    scanner = BioresourceScanner(max_workers=MAX_WORKERS, domain_delay=DOMAIN_DELAY)

    start_time = time.time()
    results = scanner.scan_batch(urls_data)
    total_time = time.time() - start_time

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    # Format indicators as semicolon-separated
    results_df['indicators_found'] = results_df['indicators_found'].apply(
        lambda x: '; '.join(x) if isinstance(x, list) else ''
    )
    results_df['url_indicators'] = results_df['url_indicators'].apply(
        lambda x: '; '.join(x) if isinstance(x, list) else ''
    )
    results_df['title_indicators'] = results_df['title_indicators'].apply(
        lambda x: '; '.join(x) if isinstance(x, list) else ''
    )
    results_df['content_indicators'] = results_df['content_indicators'].apply(
        lambda x: '; '.join(x) if isinstance(x, list) else ''
    )

    # Save results
    output_path = DATA_DIR / "pilot_results.csv"
    results_df.to_csv(output_path, index=False)

    # Summary statistics
    print(f"\n✅ Scan Complete!")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   URLs/sec: {len(results) / total_time:.2f}")

    print(f"\n📊 Results:")
    print(f"   Live URLs: {results_df['is_live'].sum()} ({results_df['is_live'].sum() / len(results_df) * 100:.1f}%)")
    print(f"   Failed URLs: {(~results_df['is_live']).sum()}")

    print(f"\n📈 Likelihood Distribution:")
    for likelihood in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'VERY LOW']:
        count = (results_df['likelihood'] == likelihood).sum()
        pct = count / len(results_df) * 100
        print(f"   {likelihood:12s}: {count:3d} ({pct:5.1f}%)")

    print(f"\n💯 Score Statistics:")
    print(f"   Mean: {results_df['total_score'].mean():.1f}")
    print(f"   Median: {results_df['total_score'].median():.1f}")
    print(f"   Min: {results_df['total_score'].min():.0f}")
    print(f"   Max: {results_df['total_score'].max():.0f}")

    print(f"\n💾 Saved to: {output_path}")
    print(f"   Columns: {len(results_df.columns)}")
    print("=" * 70)

    # Create log
    log_path = LOGS_DIR / f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_path, 'w') as f:
        f.write(f"Bioresource URL Scanner Log\n")
        f.write(f"{'=' * 70}\n\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Input: {input_path}\n")
        f.write(f"Output: {output_path}\n")
        f.write(f"Total URLs: {len(results)}\n")
        f.write(f"Scan time: {total_time:.1f}s\n")
        f.write(f"URLs/sec: {len(results) / total_time:.2f}\n")
        f.write(f"Workers: {MAX_WORKERS}\n")
        f.write(f"Domain delay: {DOMAIN_DELAY}s\n\n")
        f.write(f"Live URLs: {results_df['is_live'].sum()}\n")
        f.write(f"Failed URLs: {(~results_df['is_live']).sum()}\n\n")
        f.write(f"Likelihood Distribution:\n")
        for likelihood in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'VERY LOW']:
            count = (results_df['likelihood'] == likelihood).sum()
            f.write(f"  {likelihood}: {count}\n")

    print(f"📋 Log saved to: {log_path}")


if __name__ == "__main__":
    main()
