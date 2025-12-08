#!/usr/bin/env python3
"""
Quality Control Analysis for best_name column
Rows 1001-1500 from final_inventory.csv
"""

import csv
import re
from pathlib import Path
from collections import defaultdict

# File paths
INPUT_FILE = "/Users/warren/development/GBC/inventory_2022/unified_bioresource_pipeline/results/2025-12-01-104909-sa4r9/finalization/final_inventory.csv"
OUTPUT_DIR = Path("/Users/warren/development/GBC/inventory_2022/unified_bioresource_pipeline/post_processing/results")
OUTPUT_FILE = OUTPUT_DIR / "best_name_qc_rows_1001_1500.csv"

# Create output directory if needed
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Detection patterns
def is_empty(name):
    """Check if name is empty, null, or whitespace"""
    return not name or name.strip() == ""

def is_numeric_only(name):
    """Check if name is only numbers"""
    return name and re.match(r'^\d+$', name.strip())

def is_very_short(name):
    """Check if name is 1-2 characters"""
    return name and len(name.strip()) <= 2

def is_short_lowercase(name):
    """Check if name is 3-4 char all-lowercase generic"""
    if not name:
        return False
    stripped = name.strip()
    if len(stripped) >= 3 and len(stripped) <= 4:
        return stripped.islower()
    return False

def has_brackets(name):
    """Check if name contains parentheses"""
    return name and ('(' in name or ')' in name)

def has_suspicious_chars(name):
    """Check for HTML tags, pipes, special characters"""
    if not name:
        return False
    # HTML tags
    if re.search(r'<[^>]+>', name):
        return True
    # Pipes
    if '|' in name:
        return True
    # Other suspicious patterns
    if re.search(r'[<>\{\}\[\]]', name):
        return True
    return False

def extract_title_evidence(title, best_name):
    """Extract potential resource name from title"""
    if not title or not best_name:
        return ""

    # Look for the best_name in the title
    if best_name.lower() in title.lower():
        return f"'{best_name}' found in title"

    # Look for common patterns in titles
    # e.g., "Database: The Resource Name" or "Resource Name: a database for..."
    patterns = [
        r'^([A-Z][A-Za-z0-9\s\-]+):\s',  # Start with capitalized name before colon
        r':\s+([A-Z][A-Za-z0-9\s\-]+)$',  # End with capitalized name after colon
        r'the\s+([A-Z][A-Za-z0-9\s\-]+)\s+(?:database|resource|portal|platform)',
    ]

    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            return f"Potential: '{match.group(1).strip()}'"

    return ""

def extract_url_evidence(url):
    """Extract potential resource name from URL"""
    if not url:
        return ""

    # Extract domain and path
    domain_match = re.search(r'://([^/]+)', url)
    if domain_match:
        domain = domain_match.group(1)
        # Remove common prefixes
        domain_clean = re.sub(r'^www\.', '', domain)
        # Extract meaningful part
        parts = domain_clean.split('.')
        if len(parts) > 1:
            main = parts[0]
            return f"Domain: {main}"

    return ""

def determine_best_name(current_name, title, url, best_common, best_full, flags):
    """Determine the best suggested name"""
    suggestions = []
    confidence = "MEDIUM"

    # If best_common is different and looks better
    if best_common and best_common != current_name:
        if len(best_common) > len(current_name) or not any(flags):
            suggestions.append(("best_common", best_common))

    # If best_full is different and looks better
    if best_full and best_full != current_name:
        if len(best_full) > len(current_name) or not any(flags):
            suggestions.append(("best_full", best_full))

    # Extract from title
    if title:
        # Look for capitalized words that might be the name
        title_words = re.findall(r'\b[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*\b', title)
        for word in title_words[:3]:  # First 3 capitalized phrases
            if len(word) > 3 and word.lower() != current_name.lower():
                suggestions.append(("title", word))

    if not suggestions:
        return current_name, "LOW", "No better alternative found"

    # Choose the best suggestion
    # Prefer best_common/best_full over title extraction
    for source, suggestion in suggestions:
        if source in ["best_common", "best_full"]:
            confidence = "HIGH"
            return suggestion, confidence, f"From {source}"

    # Use title extraction
    return suggestions[0][1], "MEDIUM", "Extracted from title"

def analyze_row(row):
    """Analyze a single row and return issues if any"""
    best_name = row.get('best_name', '')
    pmid = row.get('ID', '')
    paper_titles = row.get('paper_titles', '')
    extracted_url = row.get('extracted_url', '')
    best_common = row.get('best_common', '')
    best_full = row.get('best_full', '')

    issues = []

    # Check all patterns
    if is_empty(best_name):
        issues.append('EMPTY')
    if is_numeric_only(best_name):
        issues.append('NUMERIC_ONLY')
    if is_very_short(best_name):
        issues.append('VERY_SHORT')
    if is_short_lowercase(best_name):
        issues.append('SHORT_LOWERCASE')
    if has_brackets(best_name):
        issues.append('HAS_BRACKETS')
    if has_suspicious_chars(best_name):
        issues.append('SUSPICIOUS_CHARS')

    if not issues:
        return None

    # Extract evidence
    title_evidence = extract_title_evidence(paper_titles, best_name)
    url_evidence = extract_url_evidence(extracted_url)

    # Determine best name
    suggested_name, confidence, notes = determine_best_name(
        best_name, paper_titles, extracted_url, best_common, best_full, issues
    )

    return {
        'pmid': pmid,
        'current_best_name': best_name,
        'issue_category': '|'.join(issues),
        'evidence_from_title': title_evidence,
        'evidence_from_url': url_evidence,
        'best_common': best_common,
        'best_full': best_full,
        'suggested_name': suggested_name,
        'confidence': confidence,
        'notes': notes
    }

def main():
    """Main analysis function"""
    print("Starting QC analysis for rows 1001-1500...")

    flagged_rows = []
    stats = defaultdict(int)

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Skip to row 1001 (accounting for header)
        for i, row in enumerate(reader, start=1):
            if i < 1001:
                continue
            if i > 1500:
                break

            stats['total_analyzed'] += 1

            result = analyze_row(row)
            if result:
                flagged_rows.append(result)
                stats['flagged'] += 1

                # Count issue types
                for issue in result['issue_category'].split('|'):
                    stats[f'issue_{issue}'] += 1

    # Write output
    if flagged_rows:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['pmid', 'current_best_name', 'issue_category',
                         'evidence_from_title', 'evidence_from_url',
                         'best_common', 'best_full', 'suggested_name',
                         'confidence', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flagged_rows)

        print(f"\nWrote {len(flagged_rows)} flagged entries to {OUTPUT_FILE}")
    else:
        print("\nNo issues found!")

    # Print statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(f"Total rows analyzed: {stats['total_analyzed']}")
    print(f"Total flagged: {stats['flagged']}")
    print(f"Clean rows: {stats['total_analyzed'] - stats['flagged']}")
    print(f"\nIssue Breakdown:")

    issue_types = ['EMPTY', 'NUMERIC_ONLY', 'VERY_SHORT', 'SHORT_LOWERCASE',
                   'HAS_BRACKETS', 'SUSPICIOUS_CHARS']
    for issue_type in issue_types:
        count = stats.get(f'issue_{issue_type}', 0)
        if count > 0:
            pct = (count / stats['flagged'] * 100) if stats['flagged'] > 0 else 0
            print(f"  {issue_type:20s}: {count:4d} ({pct:5.1f}%)")

    print("\n" + "="*60)
    print(f"Output file: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()
