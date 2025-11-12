#!/usr/bin/env python3
"""Test pattern matching on known examples."""

import re

def create_patterns(short_name):
    """Create regex patterns to find full names."""
    short_escaped = re.escape(short_name)

    pattern_templates = [
        # "Full Name (SHORT)"
        r'\b([A-Z][\w\s\-]+?)\s+\(' + short_escaped + r'\)',
        # "SHORT (Full Name)"
        short_escaped + r'\s+\(([\w\s\-]+?)\)',
        # "the Full Name database ... SHORT"
        r'(?:the|a|an)\s+([\w\s\-]+?)\s+(?:database|resource|tool|platform|repository|collection|archive|portal)\b[^.]{0,50}?\b' + short_escaped + r'\b',
        # "SHORT is a Full Name database"
        r'\b' + short_escaped + r'\b\s+is\s+(?:a|an)\s+([\w\s\-]+?)\s+(?:database|resource|tool|platform|repository)',
        # "SHORT: Full Name"
        r'(?:^|\.\s+)' + short_escaped + r':\s+([\w\s\-]+?)(?:\.|,)',
    ]

    patterns = []
    for template in pattern_templates:
        try:
            patterns.append(re.compile(template, re.IGNORECASE | re.MULTILINE))
        except re.error as e:
            print(f"Error compiling pattern: {e}")

    return patterns

# Test cases from the CSV
test_cases = [
    {
        'short': 'ClinGen',
        'full': 'Clinical Genome Resource',
        'title': 'The Clinical Genome Resource (ClinGen): Advancing genomic knowledge through global curation.'
    },
    {
        'short': 'BAR',
        'full': 'Bio-Analytic Resource for Plant Biology',
        'title': '20 years of the Bio-Analytic Resource for Plant Biology.'
    },
    {
        'short': 'SCInter',
        'full': 'comprehensive Single-Cell transcriptome integration database for human and mouse',
        'title': 'SCInter: A comprehensive single-cell transcriptome integration database for human and mouse.'
    }
]

print("="*60)
print("PATTERN MATCHING TEST")
print("="*60)

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. Testing: {test['short']}")
    print(f"   Expected: {test['full']}")
    print(f"   Title: {test['title']}")

    patterns = create_patterns(test['short'])

    all_matches = []
    for j, pattern in enumerate(patterns, 1):
        matches = pattern.findall(test['title'])
        if matches:
            print(f"   Pattern {j} matched: {matches}")
            all_matches.extend(matches)

    if not all_matches:
        print(f"   ❌ NO MATCHES FOUND!")
    else:
        print(f"   ✓ Total matches: {all_matches}")
