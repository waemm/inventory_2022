#!/usr/bin/env python3
"""
extract_urls_from_fulltext.py

Extracts URLs from EPMC full text for bioresources that lack URLs.
Processes papers marked as potential bioresources but missing resource URLs.

Usage:
    python extract_urls_from_fulltext.py [--input INPUT_CSV] [--output OUTPUT_CSV]

Author: Claude Code
Date: 2025-11-26
"""

import pandas as pd
import requests
import re
import json
import time
import argparse
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent.parent
DEFAULT_INPUT = BASE_DIR / "fp_bioresources_need_url_refined.csv"
DEFAULT_OUTPUT = BASE_DIR / "fulltext_url_results.csv"

# EPMC API endpoints
EPMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EPMC_FULLTEXT_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/{id}/fullTextXML"

# Rate limiting
REQUEST_DELAY = 1.0  # seconds between EPMC requests
VALIDATION_TIMEOUT = 10  # seconds for URL validation

# URL extraction patterns (from 11_extract_urls.py)
EXCLUDE_DOMAINS = [
    # Code repositories
    'github.com', 'gitlab.com', 'bitbucket.org', 'sourceforge.net',
    # DOI and reference systems
    'doi.org', 'dx.doi.org', 'pubmed', 'europepmc.org', 'ncbi.nlm.nih.gov/pubmed',
    'sciencedirect.com', 'springer.com', 'nature.com', 'cell.com', 'wiley.com',
    'plos.org', 'frontiersin.org', 'mdpi.com', 'biorxiv.org', 'arxiv.org',
    # Social media
    'twitter.com', 'facebook.com', 'linkedin.com', 'instagram.com',
    'researchgate.net', 'academia.edu', 'orcid.org',
    # File sharing
    'dropbox.com', 'google.com/drive', 'drive.google.com', 'onedrive.com',
    'figshare.com', 'zenodo.org', 'dryad.org', 'mendeley.com',
    # Generic
    'wikipedia.org', 'google.com', 'yahoo.com', 'bing.com',
    'gmail.com', 'hotmail.com', 'outlook.com',
]

RESOURCE_KEYWORDS = [
    'database', 'db', 'bio', 'genom', 'protein', 'gene',
    'tool', 'portal', 'server', 'resource', 'data',
    'omics', 'seq', 'transcriptom', 'proteom', 'metabolom',
    'repository', 'archive', 'catalog', 'registry',
]

ACADEMIC_TLDS = ['.edu', '.gov', '.ac.uk', '.ac.jp', '.ac.cn', '.org']

CONTEXT_PHRASES = [
    'available at', 'accessible at', 'can be accessed',
    'hosted at', 'found at', 'visit', 'web server',
    'online at', 'website:', 'freely available',
    'public resource', 'can be downloaded', 'deposited at',
    'available from', 'accessible through', 'available via',
]

# Stopwords to exclude from title keyword extraction
STOPWORDS = {
    'a', 'an', 'the', 'of', 'for', 'and', 'or', 'in', 'to', 'with', 'from',
    'by', 'on', 'at', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'that', 'this', 'which', 'who', 'whom', 'whose', 'what', 'where', 'when',
    'database', 'resource', 'atlas', 'repository', 'archive', 'tool', 'server',
    'web', 'online', 'new', 'novel', 'comprehensive', 'integrated', 'curated',
    'analysis', 'study', 'research', 'based', 'using', 'approach', 'method',
    'data', 'information', 'knowledge', 'base', 'system', 'platform',
}

# =============================================================================
# TITLE KEYWORD EXTRACTION
# =============================================================================

def extract_title_keywords(title: str) -> list:
    """
    Extract meaningful keywords from paper title for URL matching.

    Returns keywords that are likely to appear in the database URL/domain.
    """
    if not title:
        return []

    keywords = []
    title_clean = title.lower()

    # Remove HTML tags like <i>...</i>
    title_clean = re.sub(r'<[^>]+>', '', title_clean)

    # Extract database names with specific patterns (highest priority)
    # Pattern 1: Names ending in DB/Base/KB (e.g., VIPERdb, WormBase, OncoKB)
    db_patterns = re.findall(r'\b([a-z]+(?:db|base|kb))\b', title_clean, re.IGNORECASE)
    keywords.extend([p.lower() for p in db_patterns])

    # Pattern 2: Capitalized names/acronyms in original title (before lowercasing)
    acronyms = re.findall(r'\b([A-Z][A-Za-z0-9]{2,})\b', title)
    for acr in acronyms:
        if acr.lower() not in STOPWORDS and len(acr) >= 3:
            keywords.append(acr.lower())

    # Pattern 3: Names in parentheses (e.g., "Mouse Genome Database (MGD)")
    parens = re.findall(r'\(([A-Za-z0-9]+)\)', title)
    for p in parens:
        if p.lower() not in STOPWORDS and len(p) >= 2:
            keywords.append(p.lower())

    # Pattern 4: Names before colon (e.g., "Neurotree: a collaborative database")
    if ':' in title:
        before_colon = title.split(':')[0].strip()
        # Get significant words before colon
        words = re.findall(r'\b([A-Za-z0-9]+)\b', before_colon)
        for w in words:
            if w.lower() not in STOPWORDS and len(w) >= 4:
                keywords.append(w.lower())

    # Pattern 5: Specific organism/domain names (often in database names)
    specific_terms = re.findall(r'\b((?:[A-Z][a-z]+){2,})\b', title)  # CamelCase
    for term in specific_terms:
        if term.lower() not in STOPWORDS:
            keywords.append(term.lower())

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen and len(kw) >= 3:
            seen.add(kw)
            unique.append(kw)

    return unique

def check_title_url_match(title: str, url: str) -> tuple:
    """
    Check if keywords from the title appear in the URL.

    Returns:
        (bool, list): (is_match, list of matched keywords)
    """
    keywords = extract_title_keywords(title)
    if not keywords:
        return False, []

    # Parse URL to get domain and path
    try:
        parsed = urlparse(url)
        url_text = (parsed.netloc + parsed.path).lower()
    except:
        url_text = url.lower()

    matched = []
    for kw in keywords:
        # Check if keyword appears in URL (domain or path)
        if kw in url_text:
            matched.append(kw)

    return len(matched) > 0, matched

# =============================================================================
# EPMC FULL TEXT FETCHER
# =============================================================================

class EPMCFullTextFetcher:
    """Fetches full text from Europe PMC API"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioresourceURLExtractor/1.0 (GBC Inventory Project)'
        })
        self.last_request_time = 0

    def _rate_limit(self):
        """Ensure minimum delay between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def get_pmc_id(self, pmid: str) -> str | None:
        """Get PMC ID from PMID using EPMC search API"""
        self._rate_limit()

        try:
            params = {
                'query': f'EXT_ID:{pmid} AND SRC:MED',
                'format': 'json',
                'resultType': 'core'
            }
            response = self.session.get(EPMC_SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            results = data.get('resultList', {}).get('result', [])

            if results:
                # Look for PMC ID in the result
                result = results[0]
                pmcid = result.get('pmcid')
                if pmcid:
                    return pmcid

            return None

        except Exception as e:
            print(f"  Error getting PMC ID for {pmid}: {e}")
            return None

    def fetch_fulltext(self, pmcid: str) -> str | None:
        """Fetch full text XML from EPMC"""
        self._rate_limit()

        try:
            url = EPMC_FULLTEXT_URL.format(id=pmcid)
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                # Parse XML and extract text content
                soup = BeautifulSoup(response.content, 'lxml-xml')

                # Extract all text from body
                text_parts = []

                # Get abstract
                abstract = soup.find('abstract')
                if abstract:
                    text_parts.append(abstract.get_text(separator=' ', strip=True))

                # Get body text
                body = soup.find('body')
                if body:
                    text_parts.append(body.get_text(separator=' ', strip=True))

                # Get back matter (often contains URLs)
                back = soup.find('back')
                if back:
                    text_parts.append(back.get_text(separator=' ', strip=True))

                return ' '.join(text_parts)

            return None

        except Exception as e:
            print(f"  Error fetching full text for {pmcid}: {e}")
            return None

# =============================================================================
# URL EXTRACTION (adapted from 11_extract_urls.py)
# =============================================================================

class URLExtractor:
    """Extracts and scores URLs from text"""

    def extract_urls(self, text: str) -> list:
        """Extract all URLs from text using comprehensive patterns"""
        if not text:
            return []

        urls = []

        # Pattern 1: Full URLs with protocol
        pattern1 = r'https?://[^\s<>"\',)]+(?:[^\s<>"\',.]|(?<=/))'
        urls.extend(re.findall(pattern1, text, re.IGNORECASE))

        # Pattern 2: URLs starting with www
        pattern2 = r'www\.[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}(?:/[^\s<>"\',)]*)?'
        urls.extend(re.findall(pattern2, text, re.IGNORECASE))

        # Pattern 3: FTP URLs
        pattern3 = r'ftp://[^\s<>"\',)]+(?:[^\s<>"\',.]|(?<=/))'
        urls.extend(re.findall(pattern3, text, re.IGNORECASE))

        # Pattern 4: Domain-like patterns after context phrases
        for phrase in CONTEXT_PHRASES:
            if phrase.lower() in text.lower():
                phrase_pattern = re.escape(phrase) + r'\s+([a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}(?:/[^\s<>"\',)]*)?)'
                urls.extend(re.findall(phrase_pattern, text, re.IGNORECASE))

        # Clean URLs
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation
            url = re.sub(r'[.,;:)\]]+$', '', url)
            url = url.strip('[](){}')

            # Skip emails
            if '@' in url and not url.startswith('http'):
                continue

            # Skip very short URLs
            if len(url) < 8:
                continue

            # Add http:// if missing
            if url.startswith('www.') and not url.startswith('http'):
                url = 'http://' + url

            cleaned_urls.append(url)

        # Remove duplicates preserving order
        seen = set()
        unique_urls = []
        for url in cleaned_urls:
            url_lower = url.lower()
            if url_lower not in seen:
                seen.add(url_lower)
                unique_urls.append(url)

        return unique_urls

    def is_excluded(self, url: str) -> bool:
        """Check if URL is in exclusion list"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower() if parsed.netloc else url.lower()
            domain = re.sub(r'^www\.', '', domain)

            for excluded in EXCLUDE_DOMAINS:
                if excluded in domain:
                    return True
            return False
        except:
            return False

    def score_url(self, url: str, text: str, title: str = '') -> tuple:
        """
        Score URL to determine if it's likely a bioresource.

        Returns:
            tuple: (score, title_match, matched_keywords)
        """
        if self.is_excluded(url):
            return -1000, False, []

        score = 0.0
        title_match = False
        matched_keywords = []

        # TITLE KEYWORD MATCHING (highest priority - +50 bonus)
        if title:
            title_match, matched_keywords = check_title_url_match(title, url)
            if title_match:
                score += 50  # Large bonus for title-URL match

        # Check context
        context = self.get_context(text, url)
        context_lower = context.lower()
        for phrase in CONTEXT_PHRASES:
            if phrase in context_lower:
                score += 10
                break

        # Resource keywords in URL
        url_lower = url.lower()
        for keyword in RESOURCE_KEYWORDS:
            if keyword in url_lower:
                score += 8
                break

        # Academic TLD
        for tld in ACADEMIC_TLDS:
            if tld in url_lower:
                score += 5
                break

        # Subdomain suggesting resource
        parsed = urlparse(url)
        domain = parsed.netloc.lower() if parsed.netloc else url_lower
        if any(sub in domain for sub in ['db.', 'data.', 'tools.', 'portal.']):
            score += 3

        return score, title_match, matched_keywords

    def get_context(self, text: str, url: str, window: int = 100) -> str:
        """Extract text surrounding URL"""
        if not text:
            return ''

        url_pos = text.lower().find(url.lower())
        if url_pos == -1:
            return ''

        start = max(0, url_pos - window)
        end = min(len(text), url_pos + len(url) + window)

        context = text[start:end].strip()
        if start > 0:
            context = '...' + context
        if end < len(text):
            context = context + '...'

        return context

# =============================================================================
# URL VALIDATION (adapted from 02_scan_urls.py)
# =============================================================================

class URLValidator:
    """Validates URLs by checking HTTP status"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioresourceURLExtractor/1.0 (GBC Inventory Project)'
        })

    def validate(self, url: str) -> dict:
        """Check if URL is live and return status"""
        result = {
            'is_live': False,
            'status_code': None,
            'error': None,
            'response_time_ms': None
        }

        try:
            start_time = time.time()
            response = self.session.get(url, timeout=VALIDATION_TIMEOUT, allow_redirects=True)
            response_time = (time.time() - start_time) * 1000

            result['status_code'] = response.status_code
            result['response_time_ms'] = round(response_time, 2)
            result['is_live'] = 200 <= response.status_code < 400

            if not result['is_live']:
                result['error'] = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            result['error'] = 'Timeout'
        except requests.exceptions.ConnectionError as e:
            result['error'] = f'Connection error: {str(e)[:50]}'
        except Exception as e:
            result['error'] = f'Error: {str(e)[:50]}'

        return result

# =============================================================================
# MAIN WORKFLOW
# =============================================================================

def process_papers(input_file: Path, output_file: Path):
    """Main processing workflow"""

    print("=" * 70)
    print("Full Text URL Extraction for False Positive Bioresources")
    print("=" * 70)

    # Load input
    print(f"\nLoading: {input_file}")
    df = pd.read_csv(input_file)

    # Filter to bioresources only
    if 'is_bioresource' in df.columns:
        df = df[df['is_bioresource'] == 'Y'].copy()
        print(f"Filtered to bioresources: {len(df)} papers")
    else:
        print(f"Total papers: {len(df)}")

    # Initialize components
    fetcher = EPMCFullTextFetcher()
    extractor = URLExtractor()
    validator = URLValidator()

    results = []

    print(f"\nProcessing {len(df)} papers...")

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing"):
        pmid = str(row['pmid'])
        title = row.get('title', '')

        result = {
            'pmid': pmid,
            'title': title,
            'category': row.get('category', ''),
            'has_fulltext': False,
            'fulltext_source': None,
            'fulltext_length': 0,
            'urls_found': '',
            'urls_count': 0,
            'best_url': '',
            'best_url_score': 0,
            'best_url_title_match': False,
            'best_url_matched_keywords': '',
            'best_url_context': '',
            'best_url_is_live': False,
            'best_url_status': None,
            'best_url_error': '',
            'all_url_details': ''
        }

        # Step 1: Get PMC ID
        pmc_id = fetcher.get_pmc_id(pmid)

        if pmc_id:
            # Step 2: Fetch full text
            fulltext = fetcher.fetch_fulltext(pmc_id)

            if fulltext:
                result['has_fulltext'] = True
                result['fulltext_source'] = 'PMC'
                result['fulltext_length'] = len(fulltext)

                # Step 3: Extract URLs
                all_urls = extractor.extract_urls(fulltext)

                # Score and filter URLs (with title matching)
                scored_urls = []
                for url in all_urls:
                    score, title_match, matched_kws = extractor.score_url(url, fulltext, title)
                    if score >= 0:  # Not excluded
                        context = extractor.get_context(fulltext, url, window=50)
                        scored_urls.append({
                            'url': url,
                            'score': score,
                            'title_match': title_match,
                            'matched_keywords': matched_kws,
                            'context': context
                        })

                # Sort by score
                scored_urls.sort(key=lambda x: x['score'], reverse=True)

                if scored_urls:
                    result['urls_found'] = ' | '.join([u['url'] for u in scored_urls])
                    result['urls_count'] = len(scored_urls)

                    # Get best URL
                    best = scored_urls[0]
                    result['best_url'] = best['url']
                    result['best_url_score'] = best['score']
                    result['best_url_title_match'] = best['title_match']
                    result['best_url_matched_keywords'] = ', '.join(best['matched_keywords'])
                    result['best_url_context'] = best['context']

                    # Step 4: Validate best URL
                    validation = validator.validate(best['url'])
                    result['best_url_is_live'] = validation['is_live']
                    result['best_url_status'] = validation['status_code']
                    result['best_url_error'] = validation['error'] or ''

                    # Store all URL details as JSON (convert matched_keywords to string)
                    url_details = [{**u, 'matched_keywords': ', '.join(u['matched_keywords'])} for u in scored_urls[:10]]
                    result['all_url_details'] = json.dumps(url_details)

        results.append(result)

    # Create output DataFrame
    results_df = pd.DataFrame(results)

    # Save results
    results_df.to_csv(output_file, index=False)
    print(f"\nSaved results to: {output_file}")

    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total = len(results_df)
    with_fulltext = results_df['has_fulltext'].sum()
    with_urls = (results_df['urls_count'] > 0).sum()
    with_live_urls = results_df['best_url_is_live'].sum()
    with_title_match = results_df['best_url_title_match'].sum()

    print(f"\nTotal papers processed: {total}")
    print(f"Papers with full text:  {with_fulltext} ({with_fulltext/total*100:.1f}%)")
    print(f"Papers with URLs found: {with_urls} ({with_urls/total*100:.1f}%)")
    print(f"Papers with live URLs:  {with_live_urls} ({with_live_urls/total*100:.1f}%)")
    print(f"Papers with TITLE MATCH: {with_title_match} ({with_title_match/total*100:.1f}%)")

    if with_urls > 0:
        print(f"\n--- URLs with TITLE MATCH (high confidence) ---")
        title_match_results = results_df[(results_df['best_url'] != '') & (results_df['best_url_title_match'] == True)]
        if len(title_match_results) > 0:
            for _, row in title_match_results.iterrows():
                status = "LIVE" if row['best_url_is_live'] else "DEAD"
                print(f"  [{status}] {row['best_url'][:60]}...")
                print(f"         Paper: {row['title'][:50]}...")
                print(f"         Matched: {row['best_url_matched_keywords']}")
        else:
            print("  (none)")

        print(f"\n--- URLs WITHOUT title match (lower confidence) ---")
        no_match_results = results_df[(results_df['best_url'] != '') & (results_df['best_url_title_match'] == False)]
        if len(no_match_results) > 0:
            for _, row in no_match_results.head(5).iterrows():
                status = "LIVE" if row['best_url_is_live'] else "DEAD"
                print(f"  [{status}] {row['best_url'][:60]}...")
                print(f"         Paper: {row['title'][:50]}...")
        else:
            print("  (none)")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Extract URLs from EPMC full text')
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT,
                        help='Input CSV file with papers to process')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT,
                        help='Output CSV file for results')

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    process_papers(args.input, args.output)
    return 0


if __name__ == "__main__":
    exit(main())
