#!/usr/bin/env python3
"""
Analyze URL extraction results to identify suspicious/incorrect cases.
"""

import pandas as pd
import re
from collections import defaultdict
import json

# Common reference URLs that are NOT the database being announced
REFERENCE_URLS = {
    'ncbi.nlm.nih.gov',
    'uniprot.org',
    'ensembl.org',
    'ebi.ac.uk',
    'expasy.org',
    'rcsb.org',
    'genome.ucsc.edu',
    'biomart.org',
    'string-db.org',
    'reactome.org',
    'kegg.jp',
    'pfam.xfam.org',
    'interpro.ebi.ac.uk',
    'genecards.org',
    'omim.org',
    'genome.jp',
    'bioconductor.org',
    'cran.r-project.org',
    'github.com',
    'sourceforge.net',
    'apache.org',
    'python.org',
    'pubmed',
    'europepmc.org',
    'doi.org',
    'pmc/articles',
    'nar.oxfordjournals.org',
    'academic.oup.com',
    'nature.com',
    'sciencedirect.com',
    'springer.com',
    'wiley.com'
}

def is_reference_url(url):
    """Check if URL is likely a reference rather than the announced database."""
    if not url or pd.isna(url):
        return False
    url_lower = url.lower()
    return any(ref in url_lower for ref in REFERENCE_URLS)

def extract_domain(url):
    """Extract domain from URL."""
    if not url or pd.isna(url):
        return ""
    match = re.search(r'https?://([^/]+)', url)
    return match.group(1) if match else ""

def analyze_extraction_results(input_file):
    """Analyze URL extraction results and identify issues."""

    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)

    print(f"Total records: {len(df)}")

    # Convert urls_found to boolean, handling various formats
    def parse_urls_found(val):
        if pd.isna(val) or val == '' or val == '0' or val == 0 or val == 'False':
            return False
        return True

    df['urls_found'] = df['urls_found'].apply(parse_urls_found)
    print(f"Records with URLs: {df['urls_found'].sum()}")

    issues = []
    issue_counts = defaultdict(int)

    for idx, row in df.iterrows():
        if not row['urls_found']:
            continue

        pmid = row['pmid']
        title = row['title']
        best_url = row['best_url']
        score = row['best_url_score']
        title_match = row['best_url_title_match']
        matched_keywords = row['best_url_matched_keywords']
        is_live = row['best_url_is_live']
        url_context = row['best_url_context']

        # Check for issues

        # 1. FALSE POSITIVE - Reference URLs
        if is_reference_url(best_url):
            issue_type = 'FALSE_POSITIVE_URL'
            domain = extract_domain(best_url)
            description = f"Reference URL detected ({domain}) - likely not the announced database"
            issues.append({
                'pmid': pmid,
                'title': title,
                'issue_type': issue_type,
                'best_url': best_url,
                'best_url_score': score,
                'best_url_title_match': title_match,
                'best_url_matched_keywords': matched_keywords,
                'issue_description': description
            })
            issue_counts[issue_type] += 1
            continue  # Don't double-count

        # 2. SUSPICIOUS TITLE MATCH
        if title_match and matched_keywords:
            # Check for very generic keywords
            try:
                keywords = json.loads(matched_keywords) if isinstance(matched_keywords, str) else matched_keywords
                if isinstance(keywords, list):
                    keywords_lower = [k.lower() for k in keywords]
                    generic_keywords = ['database', 'data', 'server', 'tool', 'resource', 'web', 'online']
                    if all(k in generic_keywords for k in keywords_lower):
                        issue_type = 'SUSPICIOUS_TITLE_MATCH'
                        description = f"Only generic keywords matched: {keywords}"
                        issues.append({
                            'pmid': pmid,
                            'title': title,
                            'issue_type': issue_type,
                            'best_url': best_url,
                            'best_url_score': score,
                            'best_url_title_match': title_match,
                            'best_url_matched_keywords': matched_keywords,
                            'issue_description': description
                        })
                        issue_counts[issue_type] += 1
                        continue
            except:
                pass

        # 3. LOW SCORE
        if score < 20:
            issue_type = 'LOW_SCORE'
            description = f"Low score ({score}) - URL may be incorrect"
            issues.append({
                'pmid': pmid,
                'title': title,
                'issue_type': issue_type,
                'best_url': best_url,
                'best_url_score': score,
                'best_url_title_match': title_match,
                'best_url_matched_keywords': matched_keywords,
                'issue_description': description
            })
            issue_counts[issue_type] += 1
            continue

        # 4. DEAD URL WITH HIGH SCORE
        if not is_live and score >= 30:
            issue_type = 'DEAD_HIGH_SCORE'
            description = f"Dead URL with high score ({score}) - may need investigation"
            issues.append({
                'pmid': pmid,
                'title': title,
                'issue_type': issue_type,
                'best_url': best_url,
                'best_url_score': score,
                'best_url_title_match': title_match,
                'best_url_matched_keywords': matched_keywords,
                'issue_description': description
            })
            issue_counts[issue_type] += 1

    # Save issues to CSV
    issues_df = pd.DataFrame(issues)
    output_file = 'review_extraction_issues.csv'
    issues_df.to_csv(output_file, index=False)
    print(f"\nSaved {len(issues)} issues to {output_file}")

    # Generate summary report
    generate_summary(df, issues_df, issue_counts)

    return issues_df, issue_counts

def generate_summary(full_df, issues_df, issue_counts):
    """Generate markdown summary report."""

    summary = []
    summary.append("# URL Extraction Results Review\n")
    summary.append(f"**Analysis Date**: 2025-11-27\n")
    summary.append(f"**Input File**: novel_fulltext_url_results.csv\n\n")

    summary.append("## Overall Statistics\n")
    summary.append(f"- **Total records analyzed**: {len(full_df)}\n")
    summary.append(f"- **Records with URLs found**: {full_df['urls_found'].sum()}\n")
    summary.append(f"- **Total issues flagged**: {len(issues_df)}\n")
    summary.append(f"- **Issue rate**: {len(issues_df) / full_df['urls_found'].sum() * 100:.1f}% of records with URLs\n\n")

    summary.append("## Issues by Type\n\n")
    for issue_type, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
        summary.append(f"- **{issue_type}**: {count} cases\n")

    summary.append("\n## Examples by Issue Type\n\n")

    for issue_type in sorted(issue_counts.keys()):
        summary.append(f"### {issue_type.replace('_', ' ').title()}\n\n")
        examples = issues_df[issues_df['issue_type'] == issue_type].head(5)

        for idx, row in examples.iterrows():
            summary.append(f"**PMID {row['pmid']}**\n")
            summary.append(f"- Title: {row['title'][:100]}...\n")
            summary.append(f"- URL: {row['best_url']}\n")
            summary.append(f"- Score: {row['best_url_score']}\n")
            summary.append(f"- Title Match: {row['best_url_title_match']}\n")
            summary.append(f"- Issue: {row['issue_description']}\n\n")

    summary.append("## Recommendations\n\n")

    if issue_counts.get('FALSE_POSITIVE_URL', 0) > 0:
        summary.append(f"### 1. False Positive URLs ({issue_counts['FALSE_POSITIVE_URL']} cases)\n")
        summary.append("**Critical Issue**: These papers have reference URLs (NCBI, UniProt, etc.) instead of their announced database URLs.\n\n")
        summary.append("**Action Required**:\n")
        summary.append("- Manual review of each case to find correct URL\n")
        summary.append("- Update scoring logic to penalize common reference domains\n")
        summary.append("- Consider filtering out known reference URLs before scoring\n\n")

    if issue_counts.get('SUSPICIOUS_TITLE_MATCH', 0) > 0:
        summary.append(f"### 2. Suspicious Title Matches ({issue_counts['SUSPICIOUS_TITLE_MATCH']} cases)\n")
        summary.append("**Issue**: Title matching used only generic keywords that don't validate the URL.\n\n")
        summary.append("**Action Required**:\n")
        summary.append("- Review these cases manually\n")
        summary.append("- Improve keyword extraction to require specific terms\n")
        summary.append("- Add minimum specificity threshold for title matching\n\n")

    if issue_counts.get('LOW_SCORE', 0) > 0:
        summary.append(f"### 3. Low Score URLs ({issue_counts['LOW_SCORE']} cases)\n")
        summary.append("**Issue**: URLs found with low confidence scores (<20).\n\n")
        summary.append("**Action Required**:\n")
        summary.append("- Manual review to verify correctness\n")
        summary.append("- Consider increasing minimum score threshold\n")
        summary.append("- May indicate weak signals that need human verification\n\n")

    if issue_counts.get('DEAD_HIGH_SCORE', 0) > 0:
        summary.append(f"### 4. Dead URLs with High Scores ({issue_counts['DEAD_HIGH_SCORE']} cases)\n")
        summary.append("**Issue**: High-confidence URLs that are no longer accessible.\n\n")
        summary.append("**Action Required**:\n")
        summary.append("- Check Internet Archive for archived versions\n")
        summary.append("- Look for updated URLs in recent citations\n")
        summary.append("- May be temporary outages - recheck later\n\n")

    summary.append("## Priority for Manual Review\n\n")
    summary.append("1. **FALSE_POSITIVE_URL** - Highest priority, these are likely wrong\n")
    summary.append("2. **SUSPICIOUS_TITLE_MATCH** - Medium priority, may be correct but need verification\n")
    summary.append("3. **LOW_SCORE** - Medium priority, uncertain matches\n")
    summary.append("4. **DEAD_HIGH_SCORE** - Lower priority, likely correct but need URL updates\n\n")

    # Write summary
    with open('review_extraction_summary.md', 'w') as f:
        f.write(''.join(summary))

    print("Saved summary to review_extraction_summary.md")

if __name__ == '__main__':
    analyze_extraction_results('novel_fulltext_url_results.csv')
