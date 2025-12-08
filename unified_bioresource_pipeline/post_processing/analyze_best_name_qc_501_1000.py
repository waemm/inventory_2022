#!/usr/bin/env python3
"""
Quality control analysis for best_name column in bioresource inventory.
Analyzes rows 501-1000.
"""

import pandas as pd
import re
import os
from urllib.parse import urlparse

def detect_issue_category(name):
    """Detect what type of issue exists with the name."""
    if pd.isna(name) or str(name).strip() == '':
        return 'EMPTY'

    name_str = str(name).strip()

    # Check for numeric only
    if name_str.isdigit():
        return 'NUMERIC_ONLY'

    # Check for very short (1-2 chars)
    if len(name_str) <= 2:
        return 'VERY_SHORT'

    # Check for short lowercase generic (3-4 chars, all lowercase)
    if len(name_str) in [3, 4] and name_str.islower() and name_str.isalpha():
        # Common generic words to flag
        generic_words = ['load', 'data', 'base', 'site', 'page', 'home', 'main', 'tool', 'file']
        if name_str in generic_words:
            return 'SHORT_LOWERCASE'

    # Check for brackets/parentheses
    if '(' in name_str or ')' in name_str:
        return 'HAS_BRACKETS'

    # Check for suspicious characters
    if any(char in name_str for char in ['<', '>', '|', '{', '}', '[', ']']):
        return 'SUSPICIOUS_CHARS'

    # Check for HTML-like content
    if '<' in name_str and '>' in name_str:
        return 'SUSPICIOUS_CHARS'

    return None

def extract_domain_from_url(url):
    """Extract domain name from URL."""
    if pd.isna(url) or str(url).strip() == '':
        return ''
    try:
        parsed = urlparse(str(url))
        domain = parsed.netloc or parsed.path.split('/')[0]
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ''

def extract_path_clues(url):
    """Extract meaningful parts from URL path."""
    if pd.isna(url) or str(url).strip() == '':
        return ''
    try:
        parsed = urlparse(str(url))
        path = parsed.path
        # Get last meaningful part of path
        parts = [p for p in path.split('/') if p and not p.endswith('.html') and not p.endswith('.php')]
        if parts:
            return parts[-1]
        return ''
    except:
        return ''

def analyze_brackets_content(name):
    """Analyze if bracket content helps or hurts the name."""
    if '(' not in name:
        return None, None

    # Extract content before and inside brackets
    match = re.match(r'^([^(]+)\(([^)]+)\)', name)
    if match:
        before = match.group(1).strip()
        inside = match.group(2).strip()

        # Check if inside content is helpful
        unhelpful_patterns = [
            r'^\d+$',  # Just numbers
            r'^[a-z]{1,3}$',  # Short lowercase
            r'^http',  # URLs
            r'www\.',  # URLs
        ]

        for pattern in unhelpful_patterns:
            if re.match(pattern, inside, re.IGNORECASE):
                return before, 'REMOVE_BRACKETS'

        # If inside content seems helpful (like abbreviation, version, etc.)
        if len(inside) > 0 and len(inside) < 50:
            return name, 'KEEP_BRACKETS'

    return name, 'UNCERTAIN'

def extract_title_clues(title_str):
    """Extract potential resource names from paper title."""
    if pd.isna(title_str) or str(title_str).strip() == '':
        return []

    title = str(title_str)
    clues = []

    # Look for patterns like "NAME: description" or "NAME - description"
    if ':' in title:
        before_colon = title.split(':')[0].strip()
        if len(before_colon) < 100 and len(before_colon) > 2:
            clues.append(before_colon)

    # Look for quoted names
    quoted = re.findall(r'"([^"]+)"', title)
    clues.extend([q for q in quoted if len(q) < 100 and len(q) > 2])

    # Look for capitalized phrases (potential acronyms or names)
    caps_words = re.findall(r'\b[A-Z][A-Z0-9]+\b', title)
    clues.extend([c for c in caps_words if len(c) > 2 and len(c) < 30])

    return clues

def determine_suggested_name(row):
    """Determine the best suggested name based on available evidence."""
    current_name = row['best_name']
    best_common = row['best_common']
    best_full = row['best_full']
    title = row['paper_titles']
    url = row['extracted_url']

    # Priority 1: Check best_common if it looks better
    if pd.notna(best_common) and str(best_common).strip():
        common_str = str(best_common).strip()
        if len(common_str) > 2 and not common_str.isdigit():
            return common_str, 'HIGH'

    # Priority 2: Check best_full if it looks better
    if pd.notna(best_full) and str(best_full).strip():
        full_str = str(best_full).strip()
        if len(full_str) > 2 and not full_str.isdigit():
            return full_str, 'MEDIUM'

    # Priority 3: Extract from title
    title_clues = extract_title_clues(title)
    if title_clues:
        return title_clues[0], 'MEDIUM'

    # Priority 4: Extract from URL
    domain = extract_domain_from_url(url)
    path = extract_path_clues(url)
    if path and len(path) > 2:
        return path, 'LOW'
    elif domain and len(domain) > 2:
        return domain, 'LOW'

    return '', 'LOW'

def main():
    # Read the extracted rows
    input_file = '/tmp/rows_501_1000.csv'
    df = pd.read_csv(input_file)

    print(f"Loaded {len(df)} rows for analysis")
    print(f"Columns: {df.columns.tolist()}")

    # Analyze each row
    results = []
    issue_counts = {}

    for idx, row in df.iterrows():
        pmid = row.get('ID', '')
        current_name = row['best_name']

        # Detect issue
        issue = detect_issue_category(current_name)

        if issue:
            # Collect evidence
            title = row.get('paper_titles', '')
            url = row.get('extracted_url', '')
            best_common = row.get('best_common', '')
            best_full = row.get('best_full', '')

            # Extract clues
            title_clues = extract_title_clues(title)
            domain = extract_domain_from_url(url)
            path = extract_path_clues(url)

            # Handle bracket analysis if applicable
            if issue == 'HAS_BRACKETS':
                suggested, bracket_action = analyze_brackets_content(str(current_name))
                notes = f"Bracket analysis: {bracket_action}"
                if bracket_action == 'REMOVE_BRACKETS':
                    suggested_name, confidence = suggested, 'HIGH'
                elif bracket_action == 'KEEP_BRACKETS':
                    suggested_name, confidence = suggested, 'HIGH'
                else:
                    suggested_name, confidence = determine_suggested_name(row)
            else:
                suggested_name, confidence = determine_suggested_name(row)
                notes = ""

            # Track counts
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

            results.append({
                'pmid': pmid,
                'current_best_name': current_name,
                'issue_category': issue,
                'evidence_from_title': '; '.join(title_clues[:3]) if title_clues else '',
                'evidence_from_url': f"{domain} / {path}" if domain or path else '',
                'best_common': best_common,
                'best_full': best_full,
                'suggested_name': suggested_name,
                'confidence': confidence,
                'notes': notes
            })

    # Create output dataframe
    results_df = pd.DataFrame(results)

    # Create output directory if needed
    output_dir = '/Users/warren/development/GBC/inventory_2022/unified_bioresource_pipeline/post_processing/results'
    os.makedirs(output_dir, exist_ok=True)

    # Save results
    output_file = os.path.join(output_dir, 'best_name_qc_rows_501_1000.csv')
    results_df.to_csv(output_file, index=False)

    print(f"\n{'='*80}")
    print("QUALITY CONTROL ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"\nRows analyzed: {len(df)}")
    print(f"Issues found: {len(results)}")
    print(f"Clean rows: {len(df) - len(results)}")
    print(f"\nIssue breakdown:")
    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue:20s}: {count:4d} ({count/len(df)*100:.1f}%)")

    print(f"\nConfidence breakdown:")
    if len(results_df) > 0:
        conf_counts = results_df['confidence'].value_counts()
        for conf in ['HIGH', 'MEDIUM', 'LOW']:
            count = conf_counts.get(conf, 0)
            print(f"  {conf:10s}: {count:4d} ({count/len(results_df)*100:.1f}%)")

    print(f"\nOutput saved to:")
    print(f"  {output_file}")

    # Show some examples
    if len(results_df) > 0:
        print(f"\n{'='*80}")
        print("SAMPLE ISSUES (first 10)")
        print(f"{'='*80}")
        sample = results_df.head(10)
        for idx, row in sample.iterrows():
            print(f"\nPMID: {row['pmid']}")
            print(f"  Current: {row['current_best_name']}")
            print(f"  Issue: {row['issue_category']}")
            print(f"  Suggested: {row['suggested_name']} (confidence: {row['confidence']})")
            if row['evidence_from_title']:
                print(f"  Title clues: {row['evidence_from_title'][:100]}")

if __name__ == '__main__':
    main()
