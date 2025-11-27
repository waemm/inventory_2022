#!/usr/bin/env python3
"""
Generate a validation sample for manual QC of the fuzzy match review.
"""

import pandas as pd
import random

def main():
    df = pd.read_csv('fuzzy_match_reviewed.csv')

    # Create stratified sample
    samples = []

    # 10 HIGH confidence TRUE matches
    high_true = df[(df['confidence'] == 'HIGH') & (df['is_match'] == 'Y')].sample(min(10, len(df[(df['confidence'] == 'HIGH') & (df['is_match'] == 'Y')])))
    samples.append(('HIGH_TRUE', high_true))

    # 10 HIGH confidence FALSE matches
    high_false = df[(df['confidence'] == 'HIGH') & (df['is_match'] == 'N')].sample(min(10, len(df[(df['confidence'] == 'HIGH') & (df['is_match'] == 'N')])))
    samples.append(('HIGH_FALSE', high_false))

    # 10 MEDIUM confidence TRUE matches
    med_true = df[(df['confidence'] == 'MEDIUM') & (df['is_match'] == 'Y')].sample(min(10, len(df[(df['confidence'] == 'MEDIUM') & (df['is_match'] == 'Y')])))
    samples.append(('MEDIUM_TRUE', med_true))

    # 10 MEDIUM confidence FALSE matches
    med_false = df[(df['confidence'] == 'MEDIUM') & (df['is_match'] == 'N')].sample(min(10, len(df[(df['confidence'] == 'MEDIUM') & (df['is_match'] == 'N')])))
    samples.append(('MEDIUM_FALSE', med_false))

    # Combine and save
    validation_df = pd.concat([s[1] for s in samples], ignore_index=True)

    # Add category column
    categories = []
    for name, sdf in samples:
        categories.extend([name] * len(sdf))
    validation_df['sample_category'] = categories

    # Add empty manual_review column
    validation_df['manual_review'] = ''
    validation_df['manual_notes'] = ''

    # Reorder columns for readability
    cols = ['sample_category', 'extracted_name', 'baseline_name', 'extracted_long', 'baseline_full',
            'edit_distance', 'long_sim', 'confidence', 'is_match', 'reasoning', 'manual_review', 'manual_notes']
    validation_df = validation_df[cols]

    # Save
    output_path = 'fuzzy_match_validation_sample.csv'
    validation_df.to_csv(output_path, index=False)

    print(f"Validation sample saved to: {output_path}")
    print(f"\nTotal samples: {len(validation_df)}")
    print("\nBreakdown:")
    for name, sdf in samples:
        print(f"  {name}: {len(sdf)}")

    print("\n" + "="*80)
    print("VALIDATION INSTRUCTIONS")
    print("="*80)
    print("""
1. Open fuzzy_match_validation_sample.csv
2. For each row, review the match and fill in:
   - manual_review: Y (agree with is_match) or N (disagree)
   - manual_notes: Any observations or corrections

3. Look for:
   - Incorrect TRUE matches (should be FALSE)
   - Incorrect FALSE matches (should be TRUE)
   - Edge cases where reasoning could be improved

4. Calculate agreement rate:
   - Agreement = (rows where manual_review = Y) / total rows
   - Target: >90% agreement indicates good automated review

5. Report findings and update review logic if needed
""")

if __name__ == '__main__':
    random.seed(42)  # For reproducibility
    main()
