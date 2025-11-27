#!/usr/bin/env python3
"""
Bioresource classification reviewer for chunk_02.csv
Classifies papers as true bioresources (N) or false positives (Y) based on titles
"""

import csv
import re

def classify_paper(title, has_url):
    """
    Classify a paper based on its title.
    Returns (is_false_positive, confidence, reason)
    """
    title_lower = title.lower()

    # Strong database indicators (TRUE BIORESOURCE)
    database_keywords = [
        'database', 'knowledgebase', 'repository', 'archive', 'atlas',
        'resource', 'collection', 'catalogue', 'catalog', 'portal',
        'data bank', 'databank'
    ]

    # Check for database patterns
    has_db_keyword = any(kw in title_lower for kw in database_keywords)

    # Check for [Name]DB pattern
    has_db_suffix = bool(re.search(r'\w+db\b', title_lower))

    # Check for update patterns (database updates)
    has_update = 'update' in title_lower or 'version' in title_lower

    # FALSE POSITIVE indicators (methodology/tool papers)
    method_keywords = [
        'tool for', 'method for', 'approach for', 'algorithm for',
        'pipeline for', 'framework for', 'platform for',
        'predicting', 'prediction of', 'detection of', 'identification of',
        'computational tool', 'computational approach', 'computational method',
        'software for', 'package for', 'web server for'
    ]

    has_method_keyword = any(kw in title_lower for kw in method_keywords)

    # Analysis/Study indicators
    analysis_keywords = [
        'analysis of', 'study of', 'investigation of', 'review of',
        'genome-wide association', 'gwas', 'comprehensive analysis'
    ]

    has_analysis_keyword = any(kw in title_lower for kw in analysis_keywords)

    # Decision logic

    # Strong TRUE BIORESOURCE indicators
    if has_db_keyword or has_db_suffix:
        # Even with database keyword, check if it's a methodology paper
        if has_method_keyword and not has_url:
            return ('Y', 'medium', 'Contains database keyword but also methodology pattern and no URL')
        elif 'platform for' in title_lower and not ('data' in title_lower or 'genomic' in title_lower):
            # Some platforms are analysis tools, not data resources
            if not has_url:
                return ('Y', 'medium', 'Analysis platform without URL')
            else:
                return ('N', 'medium', 'Platform that may house data with URL')
        else:
            return ('N', 'high', 'Contains database/repository keyword indicating data resource')

    # Strong FALSE POSITIVE indicators
    if has_method_keyword:
        if has_url:
            return ('Y', 'medium', 'Methodology/tool paper despite having URL')
        else:
            return ('Y', 'high', 'Methodology/tool paper with no URL')

    # Analysis papers
    if has_analysis_keyword:
        if has_url:
            return ('Y', 'medium', 'Analysis/study paper despite having URL')
        else:
            return ('Y', 'high', 'Analysis/study paper with no URL')

    # No URL is a strong indicator of FALSE POSITIVE
    if not has_url:
        return ('Y', 'high', 'No URL provided - unlikely to be a data resource')

    # Default case with URL but unclear title
    # Look for other positive indicators
    positive_terms = ['data', 'genomic', 'gene', 'protein', 'sequence']
    has_positive_terms = any(term in title_lower for term in positive_terms)

    if has_positive_terms:
        return ('N', 'low', 'Has URL and biological data terms but title unclear')
    else:
        return ('Y', 'low', 'Unclear from title but likely not a primary data resource')


def process_chunk():
    """Process the chunk_02.csv file and generate review results"""

    input_file = '/Users/warren/development/GBC/inventory_2022/false_positive_analysis/chunks/chunk_02.csv'
    output_file = '/Users/warren/development/GBC/inventory_2022/false_positive_analysis/agent_reviews/chunk_02_review.csv'

    results = []

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            pmid = row['pmid']
            title = row['title']
            has_url_str = row['has_resource_url']
            resource_url = row.get('resource_url', '')

            # Convert has_resource_url to boolean
            has_url = (has_url_str == 'True')

            # Classify the paper
            is_false_positive, confidence, reason = classify_paper(title, has_url)

            results.append({
                'pmid': pmid,
                'title': title,
                'has_url': has_url,
                'is_false_positive': is_false_positive,
                'confidence': confidence,
                'reason': reason
            })

    # Write results
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['pmid', 'title', 'has_url', 'is_false_positive', 'confidence', 'reason']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Print summary statistics
    total = len(results)
    false_positives = sum(1 for r in results if r['is_false_positive'] == 'Y')
    true_bioresources = total - false_positives
    high_conf = sum(1 for r in results if r['confidence'] == 'high')
    medium_conf = sum(1 for r in results if r['confidence'] == 'medium')
    low_conf = sum(1 for r in results if r['confidence'] == 'low')

    print(f"\n=== Chunk 02 Review Summary ===")
    print(f"Total papers reviewed: {total}")
    print(f"True bioresources (N): {true_bioresources} ({true_bioresources/total*100:.1f}%)")
    print(f"False positives (Y): {false_positives} ({false_positives/total*100:.1f}%)")
    print(f"\nConfidence distribution:")
    print(f"  High: {high_conf} ({high_conf/total*100:.1f}%)")
    print(f"  Medium: {medium_conf} ({medium_conf/total*100:.1f}%)")
    print(f"  Low: {low_conf} ({low_conf/total*100:.1f}%)")
    print(f"\nResults written to: {output_file}")


if __name__ == '__main__':
    process_chunk()
