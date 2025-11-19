#!/usr/bin/env python3
"""
Create consolidated CSV with Union papers and primary resource identification.

Scores entities based on:
1. Title mention (+10)
2. NER confidence/probability (+0-1)
3. Abstract mention (+5)
4. Consensus (both spaCy + V2) (+3)
5. Mention frequency (+count)

Output: One row per paper with primary resource and all metadata.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from collections import defaultdict
import re

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
SYNTHESIS_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18'

# Input files
UNION_PAPERS = SYNTHESIS_DIR / 'data/paper_sets/set_c_union.csv'
FULL_PAPERS = BASE_DIR / 'validation_spacy_v_BERT/data/v5.1_cleaned.csv'
SPACY_NER = BASE_DIR / 'validation_spacy_v_BERT/results/phase2/ner/spacy_ner_results_2025-11-15-h728fg.csv'
V2_NER = BASE_DIR / 'validation_spacy_v_BERT/results/phase2/ner/v2_ner_results_2025-11-15-icond7.csv'

# Output
OUTPUT_CSV = SYNTHESIS_DIR / 'data/union_papers_with_primary_resources.csv'

print("="*80)
print("Creating Union Papers with Primary Resource Identification")
print("="*80)

# Load Union papers
print("\n1. Loading Union paper set (16,605 papers)...")
df_union = pd.read_csv(UNION_PAPERS)
print(f"   Loaded {len(df_union)} papers")
print(f"   Columns: {list(df_union.columns)}")

# Create flags
df_union['in_linguistic'] = df_union['source'].isin(['linguistic', 'linguistic_only', 'both'])
df_union['in_setfit'] = df_union['source'].isin(['setfit', 'setfit_only', 'both'])

# Load paper metadata (title, abstract)
print("\n2. Loading paper metadata (title, abstract)...")
df_papers = pd.read_csv(FULL_PAPERS)
print(f"   Loaded {len(df_papers)} papers from full dataset")

# Rename id to pmid if needed
if 'id' in df_papers.columns and 'pmid' not in df_papers.columns:
    df_papers = df_papers.rename(columns={'id': 'pmid'})

# Merge metadata
df_merged = df_union.merge(
    df_papers[['pmid', 'title', 'abstract']],
    on='pmid',
    how='left'
)
print(f"   Merged: {len(df_merged)} papers with metadata")

# Load NER results
print("\n3. Loading NER results...")
df_spacy = pd.read_csv(SPACY_NER)
print(f"   spaCy NER: {len(df_spacy)} entity mentions")
print(f"   Columns: {list(df_spacy.columns)}")

df_v2 = pd.read_csv(V2_NER)
print(f"   V2 NER: {len(df_v2)} entity mentions")
print(f"   Columns: {list(df_v2.columns)}")

# Build entity index per paper
print("\n4. Building entity index per paper...")

def normalize_entity(name):
    """Normalize entity name for matching"""
    if pd.isna(name):
        return ''
    return str(name).lower().strip()

def is_short_form(entity):
    """Heuristic: short forms are usually uppercase acronyms or short words"""
    if not entity:
        return False
    # Short if: all uppercase, or length <= 6 chars
    return entity.isupper() or len(entity) <= 6

# Index: pmid -> {entity_name: {spacy: count, v2: {count, max_prob}, total_mentions}}
entity_index = defaultdict(lambda: defaultdict(lambda: {
    'spacy_count': 0,
    'v2_count': 0,
    'v2_max_prob': 0.0,
    'total_mentions': 0,
    'is_short': False
}))

# Process spaCy NER
for _, row in df_spacy.iterrows():
    pmid = str(row['ID'])
    mention = row.get('mention', '')
    if pd.notna(mention) and mention:
        entity = normalize_entity(mention)
        entity_index[pmid][entity]['spacy_count'] += 1
        entity_index[pmid][entity]['total_mentions'] += 1
        entity_index[pmid][entity]['is_short'] = is_short_form(mention)

# Process V2 NER
for _, row in df_v2.iterrows():
    pmid = str(row['ID'])
    mention = row.get('mention', '')
    prob = row.get('prob', 0.0)
    if pd.notna(mention) and mention:
        entity = normalize_entity(mention)
        entity_index[pmid][entity]['v2_count'] += 1
        entity_index[pmid][entity]['total_mentions'] += 1
        # Track max probability
        if pd.notna(prob):
            entity_index[pmid][entity]['v2_max_prob'] = max(
                entity_index[pmid][entity]['v2_max_prob'],
                float(prob)
            )
        entity_index[pmid][entity]['is_short'] = is_short_form(mention)

print(f"   Indexed entities for {len(entity_index)} papers")

# Define long/short matching patterns
def find_long_short_matches(entities):
    """Find potential long/short form pairs"""
    matches = []
    entity_list = list(entities)

    for i, e1 in enumerate(entity_list):
        for e2 in entity_list[i+1:]:
            # Check if one is acronym of the other
            # Simple heuristic: short form chars appear in long form
            if len(e1) < len(e2):
                short, long = e1, e2
            else:
                short, long = e2, e1

            # Check if short could be acronym of long
            if len(short) <= 6 and len(long) > 6:
                # Check if first letters match
                long_words = long.split()
                if len(long_words) >= len(short):
                    acronym = ''.join([w[0] for w in long_words if w])
                    if acronym == short:
                        matches.append(f"{short} | {long}")

    return matches

# Score entities for primary resource
print("\n5. Scoring entities for primary resource identification...")

def score_entity(entity, entity_data, title, abstract):
    """Score entity based on multiple signals"""
    score = 0.0

    # Title mention (+10)
    if title and pd.notna(title):
        if entity in normalize_entity(title):
            score += 10.0

    # Abstract mention (+5)
    if abstract and pd.notna(abstract):
        if entity in normalize_entity(abstract):
            score += 5.0

    # Consensus (both spaCy and V2) (+3)
    if entity_data['spacy_count'] > 0 and entity_data['v2_count'] > 0:
        score += 3.0

    # V2 probability (0-1)
    score += entity_data['v2_max_prob']

    # Mention frequency
    score += entity_data['total_mentions']

    return score

results = []

for idx, row in df_merged.iterrows():
    if idx % 1000 == 0:
        print(f"   Processing paper {idx+1}/{len(df_merged)}...")

    pmid = str(row['pmid'])
    title = row.get('title', '')
    abstract = row.get('abstract', '')

    # Get entities for this paper
    entities = entity_index.get(pmid, {})

    if not entities:
        # No entities found
        results.append({
            'pmid': pmid,
            'title': title,
            'abstract': abstract,
            'in_linguistic': row['in_linguistic'],
            'in_setfit': row['in_setfit'],
            'ling_score': row.get('ling_score', ''),
            'setfit_confidence': row.get('setfit_confidence', ''),
            'primary_entity_long': '',
            'primary_entity_short': '',
            'primary_score': 0.0,
            'status': 'no_entities',
            'matched_long_short': '',
            'all_long': '',
            'all_short': '',
            'ner_source': '',
            'ner_confidence': ''
        })
        continue

    # Score all entities
    entity_scores = {}
    for entity, data in entities.items():
        entity_scores[entity] = score_entity(entity, data, title, abstract)

    # Find top scoring entity/entities
    if entity_scores:
        max_score = max(entity_scores.values())
        top_entities = [e for e, s in entity_scores.items() if s == max_score]

        # Categorize entities as long/short
        long_entities = [e for e in entities.keys() if not entities[e]['is_short']]
        short_entities = [e for e in entities.keys() if entities[e]['is_short']]

        # Find matched pairs
        matched_pairs = find_long_short_matches(entities.keys())

        # Determine primary long/short
        primary_long = ''
        primary_short = ''
        for e in top_entities:
            if entities[e]['is_short']:
                primary_short = e if not primary_short else primary_short + ' | ' + e
            else:
                primary_long = e if not primary_long else primary_long + ' | ' + e

        # Determine status
        status = 'ok'
        if len(top_entities) > 1:
            status = 'conflict'
        elif max_score < 5.0:
            status = 'low_score'

        # Determine NER source
        primary_entity = top_entities[0]
        ner_source = []
        if entities[primary_entity]['spacy_count'] > 0:
            ner_source.append('spacy')
        if entities[primary_entity]['v2_count'] > 0:
            ner_source.append('v2')

        ner_confidence = entities[primary_entity]['v2_max_prob']

        # Remove primary from all_long/all_short
        other_long = [e for e in long_entities if e not in top_entities]
        other_short = [e for e in short_entities if e not in top_entities]

        results.append({
            'pmid': pmid,
            'title': title,
            'abstract': abstract,
            'in_linguistic': row['in_linguistic'],
            'in_setfit': row['in_setfit'],
            'ling_score': row.get('ling_score', ''),
            'setfit_confidence': row.get('setfit_confidence', ''),
            'primary_entity_long': primary_long,
            'primary_entity_short': primary_short,
            'primary_score': max_score,
            'status': status,
            'matched_long_short': ' ; '.join(matched_pairs),
            'all_long': ' | '.join(other_long) if other_long else '',
            'all_short': ' | '.join(other_short) if other_short else '',
            'ner_source': '+'.join(ner_source),
            'ner_confidence': ner_confidence
        })

# Create output dataframe
print("\n6. Creating output CSV...")
df_output = pd.DataFrame(results)

# Save
df_output.to_csv(OUTPUT_CSV, index=False)
print(f"   Saved to: {OUTPUT_CSV}")
print(f"   Total rows: {len(df_output)}")

# Summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nTotal papers: {len(df_output)}")
print(f"  In Linguistic: {df_output['in_linguistic'].sum()}")
print(f"  In SetFit: {df_output['in_setfit'].sum()}")

print(f"\nStatus breakdown:")
for status in df_output['status'].value_counts().items():
    print(f"  {status[0]}: {status[1]} ({status[1]/len(df_output)*100:.1f}%)")

print(f"\nPrimary entity assignment:")
print(f"  Has primary_long: {(df_output['primary_entity_long'] != '').sum()}")
print(f"  Has primary_short: {(df_output['primary_entity_short'] != '').sum()}")
print(f"  Has both: {((df_output['primary_entity_long'] != '') & (df_output['primary_entity_short'] != '')).sum()}")
print(f"  Has neither: {((df_output['primary_entity_long'] == '') & (df_output['primary_entity_short'] == '')).sum()}")

print(f"\nScore distribution:")
print(df_output['primary_score'].describe())

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print(f"\nOutput file: {OUTPUT_CSV}")
print(f"Columns: {', '.join(df_output.columns)}")
