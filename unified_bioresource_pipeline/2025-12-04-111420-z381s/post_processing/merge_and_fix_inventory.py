#!/usr/bin/env python3
"""
Merge QC results and create fixed inventory with applied corrections.
"""

import pandas as pd
import os

# Paths
BASE_DIR = "/Users/warren/development/GBC/inventory_2022/unified_bioresource_pipeline/2025-12-04-111420-z381s"
POST_PROC_DIR = os.path.join(BASE_DIR, "post_processing")
INPUT_INVENTORY = os.path.join(BASE_DIR, "09_finalization", "final_inventory.csv")

# QC chunk files
QC_FILES = [
    os.path.join(POST_PROC_DIR, "best_name_qc_rows_1_500.csv"),
    os.path.join(POST_PROC_DIR, "best_name_qc_rows_501_1000.csv"),
    os.path.join(POST_PROC_DIR, "best_name_qc_rows_1001_1510.csv"),
]

# Output files
MERGED_QC = os.path.join(POST_PROC_DIR, "best_name_qc_ALL.csv")
FIXED_INVENTORY = os.path.join(POST_PROC_DIR, "final_inventory_QC_FIXED.csv")
FIXES_LOG = os.path.join(POST_PROC_DIR, "fixes_applied.csv")

def main():
    print("=" * 60)
    print("MERGING QC RESULTS AND CREATING FIXED INVENTORY")
    print("=" * 60)

    # Step 1: Merge QC results
    print("\n1. Merging QC chunk files...")
    qc_dfs = []
    for qc_file in QC_FILES:
        if os.path.exists(qc_file):
            df = pd.read_csv(qc_file)
            print(f"   - {os.path.basename(qc_file)}: {len(df)} issues")
            qc_dfs.append(df)
        else:
            print(f"   - WARNING: {qc_file} not found!")

    qc_merged = pd.concat(qc_dfs, ignore_index=True)
    qc_merged.to_csv(MERGED_QC, index=False)
    print(f"\n   Merged QC file saved: {MERGED_QC}")
    print(f"   Total issues found: {len(qc_merged)}")

    # Step 2: Load original inventory
    print("\n2. Loading original inventory...")
    inventory = pd.read_csv(INPUT_INVENTORY)
    print(f"   Total rows: {len(inventory)}")

    # Step 3: Create lookup dict from QC results
    # Handle both single and multiple PMIDs
    print("\n3. Building fix lookup...")
    fix_lookup = {}
    for _, row in qc_merged.iterrows():
        pmid_str = str(row['pmid'])
        # Handle multiple PMIDs (e.g., "34893873, 38015436")
        pmids = [p.strip() for p in pmid_str.split(',')]
        for pmid in pmids:
            fix_lookup[pmid] = {
                'suggested_name': row['suggested_name'],
                'confidence': row['confidence'],
                'issue_category': row['issue_category'],
                'notes': row.get('notes', '')
            }
    print(f"   Fixes available for {len(fix_lookup)} PMIDs")

    # Step 4: Apply fixes to inventory
    print("\n4. Applying fixes to inventory...")

    # Add new columns
    inventory['best_name_original'] = inventory['best_name'].copy()
    inventory['qc_manual_review'] = ''
    inventory['qc_fix_applied'] = ''
    inventory['qc_confidence'] = ''
    inventory['qc_issue_category'] = ''

    fixes_applied = []

    for idx, row in inventory.iterrows():
        pmid_str = str(row['ID'])
        # Check each PMID in the ID field
        pmids = [p.strip() for p in pmid_str.split(',')]

        for pmid in pmids:
            if pmid in fix_lookup:
                fix = fix_lookup[pmid]
                old_name = row['best_name']
                new_name = fix['suggested_name']
                confidence = fix['confidence']

                # Apply the fix
                inventory.at[idx, 'best_name'] = new_name
                inventory.at[idx, 'qc_fix_applied'] = 'YES'
                inventory.at[idx, 'qc_confidence'] = confidence
                inventory.at[idx, 'qc_issue_category'] = fix['issue_category']

                # Flag for manual review if LOW confidence
                if confidence == 'LOW':
                    inventory.at[idx, 'qc_manual_review'] = 'YES'
                else:
                    inventory.at[idx, 'qc_manual_review'] = 'NO'

                # Log the fix
                fixes_applied.append({
                    'pmid': pmid,
                    'original_name': old_name,
                    'new_name': new_name,
                    'confidence': confidence,
                    'issue_category': fix['issue_category'],
                    'notes': fix['notes']
                })
                break  # Only apply once per row

    # Step 5: Save outputs
    print("\n5. Saving output files...")

    # Save fixed inventory
    inventory.to_csv(FIXED_INVENTORY, index=False)
    print(f"   Fixed inventory: {FIXED_INVENTORY}")

    # Save fixes log
    if fixes_applied:
        fixes_df = pd.DataFrame(fixes_applied)
        fixes_df.to_csv(FIXES_LOG, index=False)
        print(f"   Fixes log: {FIXES_LOG}")

    # Step 6: Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nTotal inventory rows: {len(inventory)}")
    print(f"Total QC issues found: {len(qc_merged)}")
    print(f"Fixes applied: {len(fixes_applied)}")

    # By confidence
    print("\nFixes by confidence:")
    for conf in ['HIGH', 'MEDIUM', 'LOW']:
        count = sum(1 for f in fixes_applied if f['confidence'] == conf)
        print(f"  {conf}: {count}")

    # By category
    print("\nFixes by category:")
    categories = {}
    for f in fixes_applied:
        cat = f['issue_category']
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # Manual review needed
    manual_review = sum(1 for f in fixes_applied if f['confidence'] == 'LOW')
    print(f"\nManual review flagged: {manual_review}")

    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
