#!/usr/bin/env python3
"""
Quality control analysis for best_name column in final_inventory.csv
Analyzes rows 501-1000 to identify suspicious values
"""

import csv
import re
from pathlib import Path
from urllib.parse import urlparse

# Input/output paths
INPUT_FILE = "/Users/warren/development/GBC/inventory_2022/unified_bioresource_pipeline/2025-12-04-111420-z381s/09_finalization/final_inventory.csv"
OUTPUT_FILE = "/Users/warren/development/GBC/inventory_2022/unified_bioresource_pipeline/2025-12-04-111420-z381s/post_processing/best_name_qc_rows_501_1000.csv"

# Ensure output directory exists
Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)

def extract_name_from_url(url):
    """Extract potential resource name from URL"""
    if not url or url.strip() == '':
        return None

    try:
        parsed = urlparse(url)
        domain = parsed.netloc

        # Remove common prefixes
        domain = re.sub(r'^(www\.|web\.)', '', domain)

        # Extract main domain name
        parts = domain.split('.')
        if len(parts) >= 2:
            name = parts[0]
            # Capitalize first letter
            if name:
                return name.capitalize()
    except:
        pass

    return None

def extract_name_from_title(title):
    """Extract potential resource name from paper title"""
    if not title or title.strip() == '':
        return None

    # Look for common patterns
    # Pattern 1: "ResourceName: description"
    match = re.search(r'^([A-Z][A-Za-z0-9\-]+):\s+', title)
    if match:
        return match.group(1)

    # Pattern 2: Resource names in quotes
    match = re.search(r'"([A-Z][A-Za-z0-9\-]+)"', title)
    if match:
        return match.group(1)

    # Pattern 3: All caps words (likely acronyms)
    match = re.search(r'\b([A-Z]{3,})\b', title)
    if match:
        return match.group(1)

    return None

def categorize_issue(best_name):
    """Categorize the type of issue with best_name"""
    if not best_name or best_name.strip() == '':
        return 'EMPTY'

    name = best_name.strip()

    # Check for HTML or suspicious characters
    if any(char in name for char in ['<', '>', '|']) or name.startswith('/') or name.endswith('/'):
        return 'SUSPICIOUS_CHARS'

    # Check for numeric only
    if name.isdigit():
        return 'NUMERIC_ONLY'

    # Check for very short (1-2 chars)
    if len(name) <= 2:
        return 'VERY_SHORT'

    # Check for short lowercase (3-4 chars)
    if 3 <= len(name) <= 4 and name.islower():
        return 'SHORT_LOWERCASE'

    # Check for brackets
    if '(' in name and ')' in name:
        return 'HAS_BRACKETS'

    return None

def analyze_row(row):
    """Analyze a single row and return issue details if found"""
    best_name = row.get('best_name', '').strip()
    issue = categorize_issue(best_name)

    if not issue:
        return None

    # Gather evidence
    pmid = row.get('ID', '').strip()
    paper_titles = row.get('paper_titles', '').strip()
    extracted_url = row.get('extracted_url', '').strip()
    best_common = row.get('best_common', '').strip()
    best_full = row.get('best_full', '').strip()
    name_flags = row.get('name_modification_flags', '').strip()

    # Extract evidence
    evidence_from_title = extract_name_from_title(paper_titles)
    evidence_from_url = extract_name_from_url(extracted_url)

    # Determine suggested name and confidence
    suggested_name = ''
    confidence = 'LOW'
    notes = ''

    # Priority 1: Clear evidence from title
    if evidence_from_title and len(evidence_from_title) > 2:
        suggested_name = evidence_from_title
        confidence = 'HIGH'
        notes = 'Clear resource name found in paper title'

    # Priority 2: best_common if it looks better
    elif best_common and len(best_common) > 2 and not categorize_issue(best_common):
        suggested_name = best_common
        confidence = 'MEDIUM'
        notes = 'best_common appears more appropriate'

    # Priority 3: best_full if it looks better
    elif best_full and len(best_full) > 2 and not categorize_issue(best_full):
        suggested_name = best_full
        confidence = 'MEDIUM'
        notes = 'best_full appears more appropriate'

    # Priority 4: URL-derived name
    elif evidence_from_url and len(evidence_from_url) > 2:
        suggested_name = evidence_from_url
        confidence = 'MEDIUM'
        notes = 'Name derived from URL domain'

    # No good alternative found
    else:
        suggested_name = best_name  # Keep current
        confidence = 'LOW'
        notes = 'No clear alternative found - manual review needed'

    return {
        'pmid': pmid,
        'current_best_name': best_name,
        'issue_category': issue,
        'evidence_from_title': evidence_from_title or '',
        'evidence_from_url': evidence_from_url or '',
        'best_common': best_common,
        'best_full': best_full,
        'suggested_name': suggested_name,
        'confidence': confidence,
        'notes': notes
    }

def main():
    """Main analysis function"""
    print("Starting best_name QC analysis for rows 501-1000...")

    issues_found = []
    rows_analyzed = 0

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Skip first 500 data rows (rows 1-500)
        for i in range(500):
            try:
                next(reader)
            except StopIteration:
                print(f"Warning: File has fewer than 500 rows")
                break

        # Analyze rows 501-1000
        for i, row in enumerate(reader, start=501):
            if i > 1000:
                break

            rows_analyzed += 1
            issue = analyze_row(row)

            if issue:
                issues_found.append(issue)

    # Write results
    if issues_found:
        with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['pmid', 'current_best_name', 'issue_category',
                         'evidence_from_title', 'evidence_from_url',
                         'best_common', 'best_full', 'suggested_name',
                         'confidence', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(issues_found)

        print(f"\n✓ Analysis complete!")
        print(f"  Output written to: {OUTPUT_FILE}")
    else:
        print("\n✓ No issues found in the analyzed rows!")

    # Summary statistics
    print(f"\n{'='*60}")
    print("SUMMARY STATISTICS")
    print(f"{'='*60}")
    print(f"Total rows analyzed: {rows_analyzed}")
    print(f"Rows with issues found: {len(issues_found)}")
    print(f"Percentage with issues: {len(issues_found)/rows_analyzed*100:.1f}%")

    if issues_found:
        # Count by category
        print(f"\n{'Issue Categories:':<30}")
        print(f"{'-'*40}")
        category_counts = {}
        for issue in issues_found:
            cat = issue['issue_category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat:<25} {count:>4}")

        # Count by confidence
        print(f"\n{'Confidence Levels:':<30}")
        print(f"{'-'*40}")
        confidence_counts = {}
        for issue in issues_found:
            conf = issue['confidence']
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

        for conf in ['HIGH', 'MEDIUM', 'LOW']:
            count = confidence_counts.get(conf, 0)
            if count > 0:
                print(f"  {conf:<25} {count:>4}")

    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
