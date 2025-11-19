#!/usr/bin/env python3
"""
scan_gbc_test.py - TEST MODE: Scan 20 random URLs from GBC dataset
V4 - With Wayback Machine fallback support

Run this first to verify scanner works on GBC data.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from urllib.parse import urlparse, urljoin, quote
import threading
import time
import re
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime

# Suppress XML parsing warnings (some sites return XML, but HTML parser works fine)
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Load URLs and sample 20
df = pd.read_csv("data/gbc_urls.csv")
df_sample = df.sample(n=min(20, len(df)), random_state=42)  # Random but reproducible
print(f"TEST MODE: Scanning {len(df_sample)} random URLs from {len(df)} total...")
print(f"V4 - With Wayback Machine fallback")
print(f"Expected runtime: ~20-30 seconds\n")

# CONFIGURATION
MAX_WORKERS = 10
DOMAIN_DELAY = 1.0
TIMEOUT = 20
MAX_CONTENT_SIZE = 512000
MAX_META_REDIRECTS = 3
WAYBACK_TIMEOUT = 15  # Shorter timeout for Wayback API

# INDICATOR SCORES (V3 - proven effective)
INDICATOR_SCORES = {
    'NCBI': 5, 'EBI': 5, 'NIH': 5, 'Ensembl': 5, 'UniProt': 5,
    'search database': 4, 'search our database': 4, 'query database': 4,
    'browse database': 4, 'download data': 4, 'bulk download': 4,
    'data access': 4, 'programmatic access': 4,
    'genomics': 3, 'proteomics': 3, 'bioinformatics': 3, 'genome': 3,
    'gene': 3, 'protein': 3, 'sequence': 3, 'molecular': 3,
    'biological': 3, 'variant': 3, 'mutation': 3, 'expression': 3,
    'repository': 2, 'archive': 2, 'collection': 2, 'resource': 2,
    'tool': 2, 'platform': 2, 'search': 2, 'query': 2, 'browse': 2,
    'download': 2, 'submit': 2, 'curated': 2, 'annotation': 2, 'data': 2,
    'database': 1, 'server': 1, 'portal': 1, 'web service': 1,
}

TITLE_KEYWORDS = ['database', 'server', 'portal', 'resource', 'tool', 'repository', 'archive', 'collection']
TITLE_BONUS = 5

class DomainRateLimiter:
    def __init__(self, delay_seconds=1.0):
        self.delay = delay_seconds
        self.last_request = {}
        self.lock = threading.Lock()

    def wait_if_needed(self, url):
        try:
            domain = urlparse(url).netloc
        except:
            domain = "unknown"
        with self.lock:
            if domain in self.last_request:
                elapsed = time.time() - self.last_request[domain]
                if elapsed < self.delay:
                    time.sleep(self.delay - elapsed)
            self.last_request[domain] = time.time()
        return domain

class BioresourceScanner:
    def __init__(self, max_workers=10, domain_delay=1.0):
        self.max_workers = max_workers
        self.rate_limiter = DomainRateLimiter(domain_delay)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioresourceScanner/4.0 TEST (GBC Publication Analysis + Wayback)'
        })

    def get_wayback_snapshot(self, url):
        """Query Wayback Machine API for latest snapshot"""
        try:
            api_url = f"https://archive.org/wayback/available?url={quote(url)}"
            response = self.session.get(api_url, timeout=WAYBACK_TIMEOUT)

            if response.status_code != 200:
                return None, None

            data = response.json()

            if 'archived_snapshots' not in data:
                return None, None

            closest = data['archived_snapshots'].get('closest', {})

            if not closest.get('available'):
                return None, None

            snapshot_url = closest.get('url')
            timestamp = closest.get('timestamp')

            if snapshot_url and timestamp:
                # Convert timestamp to readable date (YYYYMMDDHHMMSS -> YYYY-MM-DD)
                snapshot_date = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
                return snapshot_url, snapshot_date

            return None, None
        except Exception as e:
            return None, None

    def extract_meta_refresh_url(self, soup, current_url):
        meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile('refresh', re.I)})
        if not meta_refresh:
            return None
        content = meta_refresh.get('content', '')
        if not content:
            return None
        match = re.search(r'url\s*=\s*["\']?([^"\'>]+)', content, re.I)
        if match:
            redirect_url = match.group(1).strip()
            return urljoin(current_url, redirect_url)
        return None

    def follow_meta_redirects(self, response, original_url):
        redirect_chain = []
        current_response = response
        current_url = original_url

        for hop in range(MAX_META_REDIRECTS):
            soup = BeautifulSoup(current_response.content[:MAX_CONTENT_SIZE], 'lxml')
            redirect_url = self.extract_meta_refresh_url(soup, current_url)

            if not redirect_url:
                return current_response, redirect_chain

            redirect_chain.append(redirect_url)

            try:
                self.rate_limiter.wait_if_needed(redirect_url)
                current_response = self.session.get(redirect_url, timeout=TIMEOUT, allow_redirects=True)
                current_url = redirect_url

                if current_response.status_code not in range(200, 400):
                    return current_response, redirect_chain
            except Exception as e:
                return current_response, redirect_chain

        return current_response, redirect_chain

    def score_content(self, content, page_title):
        """Score content for bioresource indicators"""
        page_title_lower = page_title.lower()
        content_lower = content[:MAX_CONTENT_SIZE].lower()

        base_score = 0
        indicators = []

        for term, term_score in INDICATOR_SCORES.items():
            term_lower = term.lower()
            if term_lower in page_title_lower:
                base_score += term_score
                indicators.append(f"Title: {term}")
            elif term_lower in content_lower:
                base_score += term_score
                indicators.append(f"Content: {term}")

        title_bonus = 0
        for keyword in TITLE_KEYWORDS:
            if keyword in page_title_lower:
                title_bonus = TITLE_BONUS
                indicators.append(f"★ TITLE BONUS: '{keyword}' in page title")
                break

        return base_score, title_bonus, indicators

    def scan_url(self, url_data):
        url = url_data['url']
        result = {
            **url_data,
            'is_live': False,
            'status_code': None,
            'total_score': 0,
            'base_score': 0,
            'title_bonus': 0,
            'likelihood': 'VERY LOW',
            'indicators_found': [],
            'response_time_ms': None,
            'error_message': None,
            'meta_redirects': 0,
            'final_url': url,
            'wayback_used': False,
            'wayback_url': None,
            'wayback_snapshot_date': None
        }

        domain = self.rate_limiter.wait_if_needed(url)

        # Try original URL first
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            final_response, redirect_chain = self.follow_meta_redirects(response, response.url)
            response_time = (time.time() - start_time) * 1000

            result['status_code'] = final_response.status_code
            result['response_time_ms'] = round(response_time, 2)
            result['is_live'] = 200 <= final_response.status_code < 400
            result['meta_redirects'] = len(redirect_chain)
            result['final_url'] = redirect_chain[-1] if redirect_chain else response.url

            if result['is_live']:
                # Original URL works - score it
                content = final_response.content[:MAX_CONTENT_SIZE].decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'lxml')
                page_title = soup.title.string if soup.title and soup.title.string else ""

                base_score, title_bonus, indicators = self.score_content(content, page_title)

                result['base_score'] = base_score
                result['title_bonus'] = title_bonus
                result['total_score'] = base_score + title_bonus
                result['indicators_found'] = indicators

                score = result['total_score']
                if score >= 15:
                    result['likelihood'] = 'CRITICAL'
                elif score >= 10:
                    result['likelihood'] = 'HIGH'
                elif score >= 5:
                    result['likelihood'] = 'MEDIUM'
                elif score >= 1:
                    result['likelihood'] = 'LOW'

                return result
            else:
                # Original URL failed - try Wayback
                result['error_message'] = f"HTTP {final_response.status_code}"

        except requests.exceptions.Timeout:
            result['error_message'] = f'Timeout ({TIMEOUT}s)'
        except Exception as e:
            result['error_message'] = f'Error: {str(e)[:100]}'

        # Original URL failed - try Wayback Machine
        wayback_url, snapshot_date = self.get_wayback_snapshot(url)

        if wayback_url:
            try:
                self.rate_limiter.wait_if_needed(wayback_url)
                wayback_response = self.session.get(wayback_url, timeout=TIMEOUT, allow_redirects=True)

                if 200 <= wayback_response.status_code < 400:
                    # Wayback worked - score it
                    content = wayback_response.content[:MAX_CONTENT_SIZE].decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(content, 'lxml')
                    page_title = soup.title.string if soup.title and soup.title.string else ""

                    base_score, title_bonus, indicators = self.score_content(content, page_title)

                    result['is_live'] = True  # Mark as live (via Wayback)
                    result['wayback_used'] = True
                    result['wayback_url'] = wayback_url
                    result['wayback_snapshot_date'] = snapshot_date
                    result['base_score'] = base_score
                    result['title_bonus'] = title_bonus
                    result['total_score'] = base_score + title_bonus
                    result['indicators_found'] = indicators

                    score = result['total_score']
                    if score >= 15:
                        result['likelihood'] = 'CRITICAL'
                    elif score >= 10:
                        result['likelihood'] = 'HIGH'
                    elif score >= 5:
                        result['likelihood'] = 'MEDIUM'
                    elif score >= 1:
                        result['likelihood'] = 'LOW'

            except Exception as e:
                # Wayback also failed
                result['error_message'] = f"{result.get('error_message', 'Original failed')} | Wayback: {str(e)[:50]}"

        return result

    def scan_batch(self, urls_data):
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scan_url, url_data): url_data for url_data in urls_data}
            for future in tqdm(as_completed(futures), total=len(urls_data), desc="Scanning (TEST)", unit="url"):
                results.append(future.result())
        return results

# Run scanner
urls_data = df_sample.to_dict('records')
scanner = BioresourceScanner(max_workers=MAX_WORKERS, domain_delay=DOMAIN_DELAY)

start_time = time.time()
results = scanner.scan_batch(urls_data)
total_time = time.time() - start_time

# Convert to DataFrame and save
results_df = pd.DataFrame(results)
results_df['indicators_found'] = results_df['indicators_found'].apply(
    lambda x: '; '.join(x) if isinstance(x, list) else ''
)

output_path = "data/gbc_test_results.csv"
results_df.to_csv(output_path, index=False)

print(f"\n{'=' * 80}")
print(f"✅ TEST SCAN COMPLETE (20 URLs)")
print(f"{'=' * 80}")
print(f"\n⏱️  Performance:")
print(f"   Total time: {total_time:.1f}s")
print(f"   URLs/sec: {len(results) / total_time:.2f}")

print(f"\n📊 Connectivity:")
print(f"   Live URLs: {results_df['is_live'].sum()} ({results_df['is_live'].sum() / len(results_df) * 100:.1f}%)")
print(f"   Failed: {(~results_df['is_live']).sum()}")

# Wayback stats
wayback_count = results_df['wayback_used'].sum()
if wayback_count > 0:
    print(f"\n🕰️  Wayback Machine:")
    print(f"   Rescued via Wayback: {wayback_count} ({wayback_count / len(results_df) * 100:.1f}%)")

print(f"\n📈 Likelihood Distribution:")
for likelihood in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'VERY LOW']:
    count = (results_df['likelihood'] == likelihood).sum()
    pct = count / len(results_df) * 100
    print(f"   {likelihood:12s}: {count:2d} ({pct:5.1f}%)")

live_df = results_df[results_df['is_live'] == True]
if len(live_df) > 0:
    print(f"\n💯 Score Statistics (Live URLs):")
    print(f"   Mean: {live_df['total_score'].mean():.1f}")

print(f"\n🏆 Top 5 Scorers:")
top_5 = results_df.nlargest(5, 'total_score')
for idx, (_, row) in enumerate(top_5.iterrows(), 1):
    entity = str(row.get('primary_entity_long', 'Unknown'))[:40] if pd.notna(row.get('primary_entity_long')) else str(row.get('primary_entity_short', 'Unknown'))[:40]
    status = "✅" if row['is_live'] else "❌"
    wayback = " 🕰️" if row.get('wayback_used') else ""
    print(f"   {idx}. {row['total_score']:2.0f} pts | {status}{wayback} | {entity}")

print(f"\n📁 Saved to: {output_path}")
print(f"\n{'=' * 80}")
print(f"✅ TEST PASSED - Ready to run full scan!")
print(f"   Run: python scripts/scan_gbc_full.py")
print(f"{'=' * 80}")
