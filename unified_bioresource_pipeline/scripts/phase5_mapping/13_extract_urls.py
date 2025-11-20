#!/usr/bin/env python3
"""
Extract URLs from abstracts and identify bioresource websites.

Adds 4 columns to each filtered dataset:
1. all_urls - All URLs detected (comma-separated)
2. resource_url - Primary bioresource URL (filtered, scored)
3. has_resource_url - Boolean (True if resource_url exists)
4. url_context - Text surrounding primary URL (for validation)
"""

import pandas as pd
import re
from pathlib import Path
from urllib.parse import urlparse

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
FILTERED_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/data/filtered'

# Input files
FILES = [
    'baseline_by_pmid.csv',
    'baseline_by_entity_match.csv',
    'linguistic_excluding_baseline.csv',
    'setfit_excluding_baseline.csv'
]

print("="*80)
print("URL Extraction and Bioresource Website Identification")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Domains to exclude (not bioresources)
EXCLUDE_DOMAINS = [
    # Code repositories
    'github.com', 'gitlab.com', 'bitbucket.org', 'sourceforge.net',

    # DOI and reference systems
    'doi.org', 'dx.doi.org', 'pubmed', 'europepmc.org', 'ncbi.nlm.nih.gov/pubmed',
    'sciencedirect.com', 'springer.com', 'nature.com', 'cell.com', 'wiley.com',
    'plos.org', 'frontiersin.org', 'mdpi.com', 'biorxiv.org', 'arxiv.org',

    # Social media and professional networks
    'twitter.com', 'facebook.com', 'linkedin.com', 'instagram.com',
    'researchgate.net', 'academia.edu', 'orcid.org',

    # File sharing and cloud storage
    'dropbox.com', 'google.com/drive', 'drive.google.com', 'onedrive.com',
    'figshare.com', 'zenodo.org', 'dryad.org', 'mendeley.com',

    # Video/media platforms
    'youtube.com', 'vimeo.com',

    # Generic
    'wikipedia.org', 'google.com', 'yahoo.com', 'bing.com',

    # Email domains (common false positives)
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
]

# Keywords that suggest bioresource in domain name
RESOURCE_KEYWORDS = [
    'database', 'db', 'bio', 'genom', 'protein', 'gene',
    'tool', 'portal', 'server', 'resource', 'data',
    'omics', 'seq', 'transcriptom', 'proteom', 'metabolom',
    'repository', 'archive', 'catalog', 'registry',
]

# Academic/government TLDs (boost confidence)
ACADEMIC_TLDS = ['.edu', '.gov', '.ac.uk', '.ac.jp', '.ac.cn', '.org']

# Context phrases that suggest resource URL nearby
CONTEXT_PHRASES = [
    'available at', 'accessible at', 'can be accessed',
    'hosted at', 'found at', 'visit', 'web server',
    'online at', 'website:', 'freely available',
    'public resource', 'can be downloaded', 'deposited at',
    'available from', 'accessible through', 'available via',
]

# ============================================================================
# URL EXTRACTION FUNCTIONS
# ============================================================================

def extract_urls(text):
    """Extract all URLs from text using comprehensive patterns"""
    if pd.isna(text):
        return []

    text = str(text)
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

    # Pattern 4: Domain-like patterns (more aggressive)
    # Only if they appear in context of "available at", "visit", etc.
    for phrase in CONTEXT_PHRASES:
        if phrase.lower() in text.lower():
            # Look for domain patterns after these phrases
            phrase_pattern = re.escape(phrase) + r'\s+([a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}(?:/[^\s<>"\',)]*)?)'
            urls.extend(re.findall(phrase_pattern, text, re.IGNORECASE))

    # Clean URLs
    cleaned_urls = []
    for url in urls:
        # Remove trailing punctuation
        url = re.sub(r'[.,;:)\]]+$', '', url)

        # Remove markdown artifacts
        url = url.strip('[](){}')

        # Skip if it's likely an email address
        if '@' in url and not url.startswith('http'):
            continue

        # Skip very short URLs (likely false positives)
        if len(url) < 8:
            continue

        # Add http:// if missing and starts with www
        if url.startswith('www.') and not url.startswith('http'):
            url = 'http://' + url

        cleaned_urls.append(url)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in cleaned_urls:
        url_lower = url.lower()
        if url_lower not in seen:
            seen.add(url_lower)
            unique_urls.append(url)

    return unique_urls

def is_excluded_domain(url):
    """Check if URL is in exclusion list"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower() if parsed.netloc else url.lower()

        # Remove www. prefix for matching
        domain = re.sub(r'^www\.', '', domain)

        for excluded in EXCLUDE_DOMAINS:
            if excluded in domain:
                return True

        return False
    except:
        return False

def has_resource_keywords(url):
    """Check if URL contains bioresource keywords"""
    url_lower = url.lower()

    for keyword in RESOURCE_KEYWORDS:
        if keyword in url_lower:
            return True

    return False

def has_academic_tld(url):
    """Check if URL has academic/government TLD"""
    url_lower = url.lower()

    for tld in ACADEMIC_TLDS:
        if tld in url_lower:
            return True

    return False

def get_url_context(text, url, window=50):
    """Extract text surrounding URL for context"""
    if pd.isna(text):
        return ''

    text = str(text)
    url_pos = text.lower().find(url.lower())

    if url_pos == -1:
        return ''

    # Get text before and after URL
    start = max(0, url_pos - window)
    end = min(len(text), url_pos + len(url) + window)

    context = text[start:end].strip()

    # Add ellipsis if truncated
    if start > 0:
        context = '...' + context
    if end < len(text):
        context = context + '...'

    return context

def score_url(url, context, abstract):
    """Score URL to determine if it's likely a bioresource"""
    score = 0.0

    # Check for exclusions first
    if is_excluded_domain(url):
        return -1000  # Exclude completely

    # +10: Near context phrases ("available at", etc.)
    context_lower = context.lower()
    for phrase in CONTEXT_PHRASES:
        if phrase in context_lower:
            score += 10
            break

    # +8: Contains resource keywords in domain
    if has_resource_keywords(url):
        score += 8

    # +5: Academic/government domain
    if has_academic_tld(url):
        score += 5

    # +3: Has subdomain suggesting resource (db., data., tools., portal.)
    parsed = urlparse(url)
    domain = parsed.netloc.lower() if parsed.netloc else url.lower()
    if any(sub in domain for sub in ['db.', 'data.', 'tools.', 'portal.', 'www.']):
        score += 3

    # +2: URL appears in first half of abstract (more prominent)
    if pd.notna(abstract):
        abstract_str = str(abstract)
        url_pos = abstract_str.lower().find(url.lower())
        if url_pos != -1 and url_pos < len(abstract_str) / 2:
            score += 2

    return score

def process_urls(row):
    """Extract and score URLs for a single paper"""
    abstract = row.get('abstract', '')

    # Extract all URLs
    all_urls = extract_urls(abstract)

    if not all_urls:
        return {
            'all_urls': '',
            'resource_url': '',
            'has_resource_url': False,
            'url_context': ''
        }

    # Score each URL
    scored_urls = []
    for url in all_urls:
        context = get_url_context(abstract, url)
        score = score_url(url, context, abstract)
        scored_urls.append({
            'url': url,
            'score': score,
            'context': context
        })

    # Filter out excluded URLs (score < 0)
    resource_urls = [u for u in scored_urls if u['score'] >= 0]

    # Sort by score descending
    resource_urls.sort(key=lambda x: x['score'], reverse=True)

    # Get primary resource URL (highest scoring)
    if resource_urls:
        primary = resource_urls[0]
        return {
            'all_urls': ' | '.join([u['url'] for u in scored_urls if u['score'] >= 0]),
            'resource_url': primary['url'],
            'has_resource_url': True,
            'url_context': primary['context']
        }
    else:
        # No resource URLs (all were excluded) - just show all URLs found
        return {
            'all_urls': ' | '.join(all_urls),
            'resource_url': '',
            'has_resource_url': False,
            'url_context': ''
        }

# ============================================================================
# PROCESS FILES
# ============================================================================

print(f"\nProcessing {len(FILES)} files...\n")

for filename in FILES:
    print(f"Processing: {filename}")

    filepath = FILTERED_DIR / filename

    # Load file
    df = pd.read_csv(filepath)
    print(f"  Loaded: {len(df)} papers")

    # Process URLs for each row
    url_results = df.apply(process_urls, axis=1)

    # Convert to DataFrame and merge
    url_df = pd.DataFrame(url_results.tolist())

    # Add new columns
    df['all_urls'] = url_df['all_urls']
    df['resource_url'] = url_df['resource_url']
    df['has_resource_url'] = url_df['has_resource_url']
    df['url_context'] = url_df['url_context']

    # Save updated file
    df.to_csv(filepath, index=False)

    # Stats
    total_with_urls = (df['all_urls'] != '').sum()
    total_with_resource = df['has_resource_url'].sum()

    print(f"  URLs found: {total_with_urls}")
    print(f"  Resource URLs: {total_with_resource}")
    print(f"  Saved: {filepath}")
    print()

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("="*80)
print("SUMMARY")
print("="*80)

summary_data = []

for filename in FILES:
    filepath = FILTERED_DIR / filename
    df = pd.read_csv(filepath)

    summary_data.append({
        'File': filename,
        'Total Papers': len(df),
        'Papers with URLs': (df['all_urls'] != '').sum(),
        'Papers with Resource URLs': df['has_resource_url'].sum(),
        'Resource URL %': f"{(df['has_resource_url'].sum() / len(df) * 100):.1f}%"
    })

summary_df = pd.DataFrame(summary_data)
print("\n" + summary_df.to_string(index=False))

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print("\nAll files updated with 4 new columns:")
print("  - all_urls")
print("  - resource_url")
print("  - has_resource_url")
print("  - url_context")
