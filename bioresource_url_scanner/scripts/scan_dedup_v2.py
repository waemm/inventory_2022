#!/usr/bin/env python3
"""
scan_dedup_v2.py - Redesigned Scanner with Practical Indicators

Based on analysis: Focus on indicators that ACTUALLY appear in bioresource websites.
Removed theoretical indicators that don't work in practice.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime

# Load URLs
df = pd.read_csv("data/dedup_urls.csv")
print(f"Scanning {len(df)} URLs with REDESIGNED indicators...")
print(f"Key changes: Practical signals, title bonuses, 20s timeout\n")

# REDESIGNED CONFIGURATION
MAX_WORKERS = 10
DOMAIN_DELAY = 1.0
TIMEOUT = 20  # Increased from 10s to recover slow sites
MAX_CONTENT_SIZE = 512000

# REDESIGNED INDICATOR SCORES - Focus on what ACTUALLY works
INDICATOR_SCORES = {
    # === CRITICAL (5): Major bioinformatics organizations ===
    'NCBI': 5,
    'EBI': 5,
    'NIH': 5,
    'Ensembl': 5,
    'UniProt': 5,

    # === HIGH (4): Clear database functionality ===
    'search database': 4,
    'search our database': 4,
    'query database': 4,
    'browse database': 4,
    'download data': 4,
    'bulk download': 4,
    'data access': 4,
    'programmatic access': 4,

    # === MEDIUM (3): Domain-specific terms that appear frequently ===
    'genomics': 3,
    'proteomics': 3,
    'bioinformatics': 3,
    'genome': 3,
    'gene': 3,
    'protein': 3,
    'sequence': 3,
    'molecular': 3,
    'biological': 3,
    'variant': 3,
    'mutation': 3,
    'expression': 3,

    # === LOW (2): Common database features ===
    'repository': 2,
    'archive': 2,
    'collection': 2,
    'resource': 2,
    'tool': 2,
    'platform': 2,
    'search': 2,
    'query': 2,
    'browse': 2,
    'download': 2,
    'submit': 2,
    'curated': 2,
    'annotation': 2,
    'data': 2,

    # === LOWEST (1): Basic indicators ===
    'database': 1,
    'server': 1,
    'portal': 1,
    'web service': 1,
}

# Title keywords that get a BONUS
TITLE_KEYWORDS = ['database', 'server', 'portal', 'resource', 'tool', 'repository', 'archive', 'collection']
TITLE_BONUS = 5  # Extra points if these appear in page title

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
            'User-Agent': 'BioresourceScanner/2.0 (Biodata Inventory Project; contact@example.com)'
        })

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
            'error_message': None
        }

        domain = self.rate_limiter.wait_if_needed(url)

        try:
            start_time = time.time()
            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            response_time = (time.time() - start_time) * 1000

            result['status_code'] = response.status_code
            result['response_time_ms'] = round(response_time, 2)
            result['is_live'] = 200 <= response.status_code < 400

            if not result['is_live']:
                result['error_message'] = f"HTTP {response.status_code}"
                return result

            # Parse content
            content = response.content[:MAX_CONTENT_SIZE].decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'lxml')
            page_title = soup.title.string if soup.title and soup.title.string else ""

            # Lowercase for matching
            page_title_lower = page_title.lower()
            content_lower = content[:MAX_CONTENT_SIZE].lower()

            # Score calculation
            base_score = 0
            indicators = []

            # Check indicators in content
            for term, term_score in INDICATOR_SCORES.items():
                term_lower = term.lower()

                # Check in title (higher priority)
                if term_lower in page_title_lower:
                    base_score += term_score
                    indicators.append(f"Title: {term}")
                # Check in content (don't double-count)
                elif term_lower in content_lower:
                    base_score += term_score
                    indicators.append(f"Content: {term}")

            # TITLE BONUS: Extra points if page title contains database keywords
            title_bonus = 0
            for keyword in TITLE_KEYWORDS:
                if keyword in page_title_lower:
                    title_bonus = TITLE_BONUS
                    indicators.append(f"★ TITLE BONUS: '{keyword}' in page title")
                    break

            result['base_score'] = base_score
            result['title_bonus'] = title_bonus
            result['total_score'] = base_score + title_bonus
            result['indicators_found'] = indicators

            # Classification (adjusted thresholds)
            score = result['total_score']
            if score >= 15:
                result['likelihood'] = 'CRITICAL'
            elif score >= 10:
                result['likelihood'] = 'HIGH'
            elif score >= 5:
                result['likelihood'] = 'MEDIUM'
            elif score >= 1:
                result['likelihood'] = 'LOW'

        except requests.exceptions.Timeout:
            result['error_message'] = f'Timeout ({TIMEOUT}s)'
        except Exception as e:
            result['error_message'] = f'Error: {str(e)[:100]}'

        return result

    def scan_batch(self, urls_data):
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scan_url, url_data): url_data for url_data in urls_data}
            for future in tqdm(as_completed(futures), total=len(urls_data), desc="Scanning", unit="url"):
                results.append(future.result())
        return results

# Run scanner
urls_data = df.to_dict('records')
scanner = BioresourceScanner(max_workers=MAX_WORKERS, domain_delay=DOMAIN_DELAY)

start_time = time.time()
results = scanner.scan_batch(urls_data)
total_time = time.time() - start_time

# Convert to DataFrame and save
results_df = pd.DataFrame(results)
results_df['indicators_found'] = results_df['indicators_found'].apply(
    lambda x: '; '.join(x) if isinstance(x, list) else ''
)

output_path = "data/dedup_results_v2.csv"
results_df.to_csv(output_path, index=False)

print(f"\n{'=' * 80}")
print(f"✅ SCAN COMPLETE (v2 - Redesigned Indicators)")
print(f"{'=' * 80}")
print(f"\n⏱️  Performance:")
print(f"   Total time: {total_time:.1f}s")
print(f"   URLs/sec: {len(results) / total_time:.2f}")
print(f"   Avg response: {results_df[results_df['is_live']==True]['response_time_ms'].mean():.0f}ms")

print(f"\n📊 Connectivity:")
print(f"   Live URLs: {results_df['is_live'].sum()} ({results_df['is_live'].sum() / len(results_df) * 100:.1f}%)")
print(f"   Failed: {(~results_df['is_live']).sum()} ({(~results_df['is_live']).sum() / len(results_df) * 100:.1f}%)")

print(f"\n📈 Likelihood Distribution:")
for likelihood in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'VERY LOW']:
    count = (results_df['likelihood'] == likelihood).sum()
    pct = count / len(results_df) * 100
    print(f"   {likelihood:12s}: {count:3d} ({pct:5.1f}%)")

print(f"\n💯 Score Statistics (Live URLs):")
live_df = results_df[results_df['is_live'] == True]
if len(live_df) > 0:
    print(f"   Mean: {live_df['total_score'].mean():.1f}")
    print(f"   Median: {live_df['total_score'].median():.1f}")
    print(f"   Max: {live_df['total_score'].max():.0f}")
    print(f"   Min: {live_df['total_score'].min():.0f}")

print(f"\n🏆 Top 5 Scorers:")
top_5 = results_df.nlargest(5, 'total_score')
for _, row in top_5.iterrows():
    entity = row.get('primary_entity_long') or row.get('primary_entity_short', 'Unknown')
    status = "✅" if row['is_live'] else "❌"
    print(f"   {row['total_score']:2.0f} (base:{row['base_score']:2.0f} + bonus:{row['title_bonus']:1.0f}) | {status} | {entity[:40]}")

print(f"\n📁 Saved to: {output_path}")
print(f"{'=' * 80}")
