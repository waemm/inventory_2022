#!/usr/bin/env python3
"""
Complete Bioresource Discovery Pipeline - Master Orchestrator

Runs the entire pipeline from entity mapping through final URL-validated datasets.

Pipeline Flow:
1. Create paper sets (linguistic, SetFit, union)
2. Map entities to papers
3. Create filtered datasets (INCLUDING baseline - changed 2025-11-20)
4. Deduplicate Sets A, B, and C
5. URL scan Set C (optional, 75-90 min)
6. Backfill URL data to Sets A & B

Created: 2025-11-20
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022')
SCRIPTS_DIR = BASE_DIR / 'pipeline_synthesis_2025-11-18/scripts'

# Pipeline scripts in order
PIPELINE_SCRIPTS = [
    ('03_map_papers_to_entities.py', 'Entity mapping'),
    ('10_create_filtered_datasets.py', 'Filtered datasets (with baseline)'),
    ('17_deduplicate_all_sets.py', 'Deduplication (A, B, C)'),
    ('18_scan_urls_set_c.py', 'URL scanning (Set C) - OPTIONAL'),
    ('19_backfill_url_data.py', 'Backfill URL data'),
]

def run_script(script_name, description, optional=False):
    """Run a pipeline script and handle errors."""
    script_path = SCRIPTS_DIR / script_name

    print(f"\n{'='*80}")
    print(f"RUNNING: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*80}\n")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False
        )
        print(f"\n✅ Completed: {description}")
        return True
    except subprocess.CalledProcessError as e:
        if optional:
            print(f"\n⚠️  Optional step failed: {description}")
            print(f"   Continuing with pipeline...")
            return False
        else:
            print(f"\n❌ ERROR in {description}")
            print(f"   Script: {script_name}")
            print(f"   Error code: {e.returncode}")
            sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ Script not found: {script_path}")
        sys.exit(1)

def main():
    """Run complete pipeline."""
    print("="*80)
    print("COMPLETE BIORESOURCE DISCOVERY PIPELINE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nPipeline directory: {SCRIPTS_DIR}")
    print(f"\nTotal steps: {len(PIPELINE_SCRIPTS)}")

    # Ask for confirmation
    print("\n⚠️  This will run the complete pipeline:")
    for i, (script, desc) in enumerate(PIPELINE_SCRIPTS, 1):
        optional_tag = " (OPTIONAL - will skip if fails)" if 'scan_urls' in script else ""
        print(f"   {i}. {desc}{optional_tag}")

    print(f"\n⏱️  Estimated time:")
    print(f"   - Steps 1-3: ~10-15 minutes")
    print(f"   - Step 4 (URL scan): 75-90 minutes (OPTIONAL)")
    print(f"   - Step 5: ~2 minutes")
    print(f"   Total: ~12-17 minutes (or 87-107 min with URL scanning)")

    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("\nPipeline cancelled.")
        sys.exit(0)

    # Run pipeline
    print(f"\n{'='*80}")
    print("STARTING PIPELINE")
    print(f"{'='*80}\n")

    completed = 0
    for script, description in PIPELINE_SCRIPTS:
        optional = 'scan_urls' in script
        success = run_script(script, description, optional=optional)
        if success:
            completed += 1

    # Final summary
    print(f"\n{'='*80}")
    print("PIPELINE COMPLETE!")
    print(f"{'='*80}\n")

    print(f"Completed steps: {completed}/{len(PIPELINE_SCRIPTS)}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n📁 Final Output Files:")
    final_dir = BASE_DIR / 'pipeline_synthesis_2025-11-18/results/final'
    print(f"   {final_dir}/set_a_linguistic_final.csv")
    print(f"   {final_dir}/set_b_setfit_final.csv")
    print(f"   {final_dir}/set_c_union_final.csv")

    print(f"\n✅ All three sets have identical column structure with URL validation data")
    print(f"\n🎉 Ready for analysis and comparison!")

if __name__ == "__main__":
    main()
