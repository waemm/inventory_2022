#!/usr/bin/env python3
"""
Complete Bioresource Discovery Pipeline - Master Orchestrator

Runs the entire pipeline from entity mapping through final URL-validated datasets,
with session-based execution, baseline comparison, and visualization generation.

================================================================================
PIPELINE FLOW
================================================================================

Step 1: Entity Mapping (03_map_papers_to_entities.py)
    - Maps papers from Sets A, B, C to entities
    - Duration: ~30-45 min

Step 2: Filtered Datasets (10_create_filtered_datasets.py)
    - Creates filtered datasets with baseline entity matching
    - Duration: ~20-30 min

Step 3: Deduplication (17_deduplicate_all_sets.py)
    - Deduplicates Sets A (Linguistic), B (SetFit), C (Union)
    - Uses union-find algorithm for URL clustering
    - Duration: ~15-25 min

Step 4: URL Scanning [OPTIONAL] (18_scan_urls_set_c.py)
    - Scans URLs in Set C using bioresource_url_scanner
    - Tests URL validity and bioresource likelihood
    - Duration: ~75-90 min
    - Can be skipped if URL validation not needed

Step 5: Backfill URL Data (19_backfill_url_data.py)
    - Copies URL scan data from Set C to Sets A and B
    - Ensures consistent column structure across all sets
    - Duration: ~2-3 min

Step 6: Baseline Comparison [OPTIONAL] (20_baseline_comparison.py)
    - Compares against 2022 baseline inventory (1,948 resources)
    - Dual-method matching: PMID + entity name
    - Adds 3 columns: in_baseline_pmid, in_baseline_entity, in_baseline
    - Generates report, stats JSON, and visualization data
    - Duration: ~3-5 min
    - Skip with --skip-baseline if not needed

Step 7: Generate Visualizations [OPTIONAL] (21_generate_visualizations.py)
    - Creates PNG and HTML charts from baseline comparison
    - 4 chart types: coverage, match types, counts, score distribution
    - Requires matplotlib and/or plotly
    - Duration: ~1-2 min
    - Skip with --skip-baseline if not needed

================================================================================
SESSION MANAGEMENT (2025-11-21)
================================================================================

Session ID Format: YYYY-MM-DD-HHMMSS-xxxxx
    Example: 2025-11-21-143022-a7k3f

Session Directory Structure:
    results/sessions/{session-id}/
    ├── session_metadata.json          # Progress tracking
    ├── deduplicated/                  # Step 3 output
    ├── url_scanned/                   # Step 4 output
    ├── final/                         # Step 5 output
    ├── baseline_comparison/           # Step 6 output
    └── visualizations/                # Step 7 output

Features:
    - Unique session ID per run prevents file collisions
    - Automatic resume from last completed step
    - Selective step rerun with --from-step
    - Progress tracking in session_metadata.json
    - List all sessions with --list-sessions

================================================================================
USAGE EXAMPLES
================================================================================

Basic Usage:
-----------

1. New Run (Full Pipeline)
    $ python run_complete_pipeline.py

    Creates new session with auto-generated ID
    Runs all 7 steps
    Output: results/sessions/{session-id}/

2. New Run (Skip Baseline Steps)
    $ python run_complete_pipeline.py --skip-baseline

    Runs steps 1-5 only
    Faster for testing or when baseline comparison not needed

3. List Available Sessions
    $ python run_complete_pipeline.py --list-sessions

    Shows all sessions with:
    - Session ID
    - Creation timestamp
    - Completion status
    - Completed steps

Advanced Usage:
--------------

4. Resume Interrupted Run
    $ python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f

    Scenario: Pipeline crashed or was interrupted (Ctrl+C)
    Behavior: Automatically skips completed steps, continues from where it stopped

    Example output:
        [✅] Step 1 already complete: Entity mapping
        [✅] Step 2 already complete: Filtered datasets
        [✅] Step 3 already complete: Deduplication
        [▶] Step 4/7: URL scanning (Set C) [OPTIONAL]
            Running: python scripts/18_scan_urls_set_c.py ...

5. Rerun from Specific Step
    $ python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f --from-step 3

    Use cases:
    - Rerun deduplication with different parameters
    - Regenerate visualizations after manual edits
    - Test specific pipeline steps

    Behavior: Ignores completion status, reruns from step 3 onward

6. Rerun Only Baseline Comparison
    $ python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f --from-step 6

    Use case: Regenerate baseline comparison and visualizations
    Duration: ~5-7 min (steps 6-7 only)

Common Workflows:
----------------

Workflow A: Development/Testing
    1. Run pipeline without baseline (faster):
       $ python run_complete_pipeline.py --skip-baseline

    2. Verify deduplication results

    3. Add baseline comparison later:
       $ python run_complete_pipeline.py --session-id {id} --from-step 6

Workflow B: Production Run
    1. Run full pipeline:
       $ python run_complete_pipeline.py

    2. If interrupted, resume:
       $ python run_complete_pipeline.py --session-id {id}

    3. Review outputs in results/sessions/{id}/

Workflow C: Iterative Refinement
    1. Initial run:
       $ python run_complete_pipeline.py

    2. Manually edit deduplication parameters in script 17

    3. Rerun from deduplication:
       $ python run_complete_pipeline.py --session-id {id} --from-step 3

Workflow D: Regenerate Visualizations
    1. Edit baseline comparison logic

    2. Rerun baseline+viz only (fast):
       $ python run_complete_pipeline.py --session-id {id} --from-step 6

================================================================================
OUTPUT LOCATIONS
================================================================================

New Session (Auto-Generated ID):
    results/sessions/2025-11-21-143022-a7k3f/

Legacy Mode (Backward Compatible):
    Individual scripts without --session-dir still output to:
    results/deduplicated/
    results/url_scanned/
    results/final/
    results/baseline_comparison/
    results/visualizations/

================================================================================
REQUIREMENTS
================================================================================

Required Dependencies:
    - Python 3.8+
    - pandas
    - numpy
    - pathlib
    - json
    - datetime
    - argparse
    - subprocess

Optional Dependencies (for visualizations):
    - matplotlib (for PNG charts)
    - plotly (for HTML interactive charts)

    Install with: pip install matplotlib plotly

External Scripts:
    - bioresource_url_scanner (for URL scanning step)
    - Must be configured separately

================================================================================
TROUBLESHOOTING
================================================================================

Issue: "Session ID not found"
    Solution: Use --list-sessions to see available sessions
              Ensure session ID is typed correctly

Issue: "Step already complete" but want to rerun
    Solution: Use --from-step N to force rerun from step N

Issue: URL scanner not found
    Solution: Either skip URL scanning (--skip-baseline) or
              configure bioresource_url_scanner in ../bioresource_url_scanner/

Issue: "matplotlib/plotly not available"
    Solution: pip install matplotlib plotly
              Or skip visualizations (--skip-baseline)

Issue: Out of memory during deduplication
    Solution: Run deduplication script standalone with increased memory:
              python -Xmx8g scripts/17_deduplicate_all_sets.py --session-dir ...

Issue: Session directory already exists
    Solution: This is normal - resume uses existing directory
              For fresh run, use new auto-generated session ID (don't specify --session-id)

================================================================================
EXIT CODES
================================================================================

0 - Success: All steps completed successfully
1 - Error: One or more steps failed
2 - User interrupted: Ctrl+C (can resume with same session ID)

================================================================================
CHANGELOG
================================================================================

2025-11-21: Added session management, baseline comparison, visualizations
2025-11-20: Created master orchestrator
2025-11-18: Pipeline synthesis project initiated

================================================================================
RELATED DOCUMENTATION
================================================================================

- PIPELINE_CHANGES_2025-11-21.md - Detailed implementation documentation
- results/sessions/README.md - Session directory structure explanation
- plans/2025-11-21_session_based_pipeline_with_baseline.md - Original plan

For questions or issues, see documentation in pipeline_synthesis_2025-11-18/
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Import session management functions
from scripts.utils.session_manager import (
    generate_session_id,
    create_session_dirs,
    load_session_metadata,
    save_session_metadata,
    mark_step_complete,
    is_step_complete,
    list_sessions
)

# Paths
BASE_DIR = Path('/Users/warren/development/GBC/inventory_2022/pipeline_synthesis_2025-11-18')
SCRIPTS_DIR = BASE_DIR / 'scripts'

# Pipeline scripts in order
PIPELINE_SCRIPTS = [
    ('03_map_papers_to_entities.py', 'Entity mapping', False),
    ('10_create_filtered_datasets.py', 'Filtered datasets (with baseline)', False),
    ('17_deduplicate_all_sets.py', 'Deduplication (A, B, C)', False),
    ('18_scan_urls_set_c.py', 'URL scanning (Set C)', True),  # Optional
    ('19_backfill_url_data.py', 'Backfill URL data', False),
    ('20_baseline_comparison.py', 'Baseline comparison', True),  # Optional
    ('21_generate_visualizations.py', 'Generate visualizations', True),  # Optional
]

# Parse command-line arguments
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run complete bioresource discovery pipeline with session management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # New run (auto-generated session ID)
  python run_complete_pipeline.py

  # Resume interrupted run
  python run_complete_pipeline.py --session-id 2025-11-21-095430-a3f9b

  # Rerun from step 6 (baseline comparison)
  python run_complete_pipeline.py --session-id 2025-11-21-095430-a3f9b --from-step 6

  # Skip baseline comparison steps
  python run_complete_pipeline.py --skip-baseline

  # List available sessions
  python run_complete_pipeline.py --list-sessions
        """
    )

    parser.add_argument(
        '--session-id',
        type=str,
        help='Use existing session ID (for resume or rerun)'
    )

    parser.add_argument(
        '--from-step',
        type=int,
        choices=range(1, 8),
        metavar='N',
        help='Rerun from step N (ignores completion status, choices: 1-7)'
    )

    parser.add_argument(
        '--skip-baseline',
        action='store_true',
        help='Skip baseline comparison steps (6-7)'
    )

    parser.add_argument(
        '--list-sessions',
        action='store_true',
        help='List available sessions and exit'
    )

    return parser.parse_args()

def display_sessions():
    """Display available sessions."""
    print("="*80)
    print("AVAILABLE SESSIONS")
    print("="*80)

    sessions = list_sessions(BASE_DIR)

    if not sessions:
        print("\nNo sessions found.")
        print(f"\nSessions directory: {BASE_DIR / 'results' / 'sessions'}")
        return

    print(f"\nFound {len(sessions)} session(s):\n")

    for session in sessions:
        session_id = session['session_id']
        created_at = session['created_at']
        completed = session['completed_steps']
        total = session['total_steps']
        progress_pct = (completed / total * 100) if total > 0 else 0

        print(f"Session: {session_id}")
        print(f"  Created: {created_at}")
        print(f"  Progress: {completed}/{total} steps ({progress_pct:.0f}%)")

        # Show status indicator
        if completed == total:
            print(f"  Status: ✅ Complete")
        elif completed > 0:
            print(f"  Status: ⏸️  In Progress")
        else:
            print(f"  Status: 🆕 New")

        print()

    print("="*80)
    print("To resume a session:")
    print("  python run_complete_pipeline.py --session-id <SESSION_ID>")
    print()


def run_script(script_name, description, optional, session_id, session_dirs):
    """
    Run a pipeline script with session support.

    Args:
        script_name: Name of script to run
        description: Human-readable description
        optional: If True, don't exit on failure
        session_id: Session ID for this run
        session_dirs: Dictionary of session directories

    Returns:
        bool: True if successful, False otherwise
    """
    script_path = SCRIPTS_DIR / script_name

    print(f"\n{'='*80}")
    print(f"RUNNING: {description}")
    print(f"Script: {script_name}")
    print(f"Session: {session_id}")
    print(f"{'='*80}\n")

    # Build command with session arguments
    cmd = [sys.executable, str(script_path)]

    # Add session directory arguments for scripts that need them
    if script_name in ['17_deduplicate_all_sets.py', '19_backfill_url_data.py',
                       '20_baseline_comparison.py', '21_generate_visualizations.py']:
        cmd.extend(['--session-dir', str(session_dirs['session'])])

    # Add session ID for URL scanner
    if script_name == '18_scan_urls_set_c.py':
        cmd.extend(['--session-id', session_id])
        cmd.extend(['--session-dir', str(session_dirs['session'])])

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
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
    """Run complete pipeline with session management."""
    # Parse arguments
    args = parse_arguments()

    # Handle --list-sessions
    if args.list_sessions:
        display_sessions()
        sys.exit(0)

    print("="*80)
    print("COMPLETE BIORESOURCE DISCOVERY PIPELINE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Get or generate session ID
    if args.session_id:
        session_id = args.session_id
        print(f"📂 Resuming session: {session_id}")
    else:
        session_id = generate_session_id()
        print(f"🆕 New session: {session_id}")

    # Create session directories
    session_dirs = create_session_dirs(session_id, BASE_DIR)
    print(f"📁 Session directory: {session_dirs['session']}\n")

    # Load metadata
    metadata = load_session_metadata(session_id, BASE_DIR)

    # Determine starting step
    start_step = args.from_step if args.from_step else 1

    if args.from_step:
        print(f"🔄 Rerunning from step {args.from_step}")
    elif metadata['completed_steps']:
        print(f"⏭️  Resuming - {len(metadata['completed_steps'])} steps already complete")

    print(f"\nTotal pipeline steps: {len(PIPELINE_SCRIPTS)}")

    # Show pipeline overview
    print("\n⚠️  Pipeline steps:")
    for i, (script, desc, optional) in enumerate(PIPELINE_SCRIPTS, 1):
        status = ""
        if i in metadata['completed_steps'] and not args.from_step:
            status = " ✅ (complete)"
        elif optional:
            status = " (optional)"

        # Check if will be skipped
        skip_reason = ""
        if i < start_step:
            skip_reason = " [SKIP: before start]"
        elif args.skip_baseline and i >= 6:
            skip_reason = " [SKIP: --skip-baseline]"
        elif i in metadata['completed_steps'] and not args.from_step:
            skip_reason = " [SKIP: complete]"

        print(f"   {i}. {desc}{status}{skip_reason}")

    # Estimate time
    print(f"\n⏱️  Estimated time:")
    print(f"   - Steps 1-3: ~10-15 minutes")
    print(f"   - Step 4 (URL scan): 75-90 minutes (optional)")
    print(f"   - Step 5 (Backfill): ~2 minutes")
    print(f"   - Steps 6-7 (Baseline + Viz): ~20-30 minutes (optional)")

    # Ask for confirmation (unless resuming)
    if not args.session_id and not args.from_step:
        response = input("\nContinue? (y/n): ")
        if response.lower() != 'y':
            print("\nPipeline cancelled.")
            sys.exit(0)

    # Run pipeline
    print(f"\n{'='*80}")
    print("STARTING PIPELINE EXECUTION")
    print(f"{'='*80}\n")

    completed_count = 0
    for step_num, (script, description, optional) in enumerate(PIPELINE_SCRIPTS, 1):
        # Skip if before start_step
        if step_num < start_step:
            print(f"⏭️  Skipping step {step_num}: {description} (before start step)")
            continue

        # Skip if already complete (unless --from-step specified)
        if not args.from_step and is_step_complete(metadata, step_num):
            print(f"✅ Step {step_num} already complete: {description}")
            completed_count += 1
            continue

        # Skip baseline steps if --skip-baseline
        if args.skip_baseline and step_num >= 6:
            print(f"⏭️  Skipping step {step_num}: {description} (--skip-baseline)")
            continue

        # Run step
        success = run_script(script, description, optional, session_id, session_dirs)

        if success:
            # Mark complete
            metadata = mark_step_complete(metadata, step_num, description)
            save_session_metadata(session_id, metadata, BASE_DIR)
            completed_count += 1
        elif not optional:
            # Non-optional step failed - exit
            print(f"\n❌ Pipeline stopped at step {step_num}")
            sys.exit(1)

    # Final summary
    print(f"\n{'='*80}")
    print("PIPELINE EXECUTION COMPLETE!")
    print(f"{'='*80}\n")

    print(f"Session: {session_id}")
    print(f"Completed steps: {completed_count}/{len(PIPELINE_SCRIPTS)}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n📁 Output Files:")
    print(f"   Session directory: {session_dirs['session']}")
    print(f"\n   Final datasets:")
    final_dir = session_dirs['final']
    print(f"     {final_dir}/set_a_linguistic_final.csv")
    print(f"     {final_dir}/set_b_setfit_final.csv")
    print(f"     {final_dir}/set_c_union_final.csv")

    if completed_count >= 6:
        baseline_dir = session_dirs['baseline_comparison']
        print(f"\n   Baseline comparison:")
        print(f"     {baseline_dir}/baseline_comparison_report.txt")
        print(f"     {baseline_dir}/baseline_comparison_stats.json")

    if completed_count >= 7:
        viz_dir = session_dirs['visualizations']
        print(f"\n   Visualizations:")
        print(f"     {viz_dir}/baseline_coverage.png")
        print(f"     {viz_dir}/baseline_coverage.html")
        print(f"     {viz_dir}/match_types.png")
        print(f"     {viz_dir}/match_types.html")

    print(f"\n✅ All datasets have identical column structure with URL validation data")

    if completed_count < len(PIPELINE_SCRIPTS):
        print(f"\n💡 To resume or rerun:")
        print(f"   python run_complete_pipeline.py --session-id {session_id}")
        print(f"   python run_complete_pipeline.py --session-id {session_id} --from-step N")

    print(f"\n🎉 Ready for analysis!")


if __name__ == "__main__":
    main()
