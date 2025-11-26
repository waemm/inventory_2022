#!/usr/bin/env python3
"""
Unified Bioresource Pipeline - Master Orchestrator

Executes the complete end-to-end pipeline from EPMC query to deduplicated bioresources.

Usage:
    python run_pipeline.py --full                 # Run complete pipeline
    python run_pipeline.py --from phase3          # Resume from PMID extraction
    python run_pipeline.py --phase phase1         # Run only classification
    python run_pipeline.py --status               # Check pipeline status
    python run_pipeline.py --full --dry-run       # Preview without execution

Phases:
    phase1 - Classification (V2 RoBERTa + PyCaret)
    phase2 - NER (V2 RoBERTa + spaCy Hybrid)
    phase3 - PMID Extraction (NER union)
    phase4 - Linguistic Filtering
    phase5 - SetFit Classification
    phase6 - Entity Mapping & Resource Creation (includes 02b data fix)
    phase7 - URL Scanning & Validation (includes backfill)
    phase8 - Deduplication (multi-profile support)
    phase9 - Baseline Comparison & Visualization

Author: Pipeline Consolidation Team
Date: 2025-11-20
Updated: 2025-11-26 (Synced critical fixes from pipeline_synthesis)
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import shutil


# Terminal colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@dataclass
class PhaseDefinition:
    """Definition of a pipeline phase."""
    id: str
    name: str
    scripts: List[str]
    notebooks: List[str]
    required_inputs: List[str]
    outputs: List[str]
    estimated_time: str
    gpu_required: bool
    manual_steps: bool


# Phase definitions
PHASES = [
    PhaseDefinition(
        id="phase1",
        name="Classification (V2 RoBERTa + PyCaret)",
        scripts=[
            "validation_spacy_v_BERT/scripts/03a_run_v2_classification.py",
            "validation_spacy_v_BERT/scripts/03b_run_pycaret_classification.py",
        ],
        notebooks=[
            "validation_spacy_v_BERT/notebooks/phase2_v2_classification_150k_VB.ipynb",
            "validation_spacy_v_BERT/notebooks/phase2_pycaret_classification_150k_VB.ipynb",
        ],
        required_inputs=[
            "data/final_query_v5.1_2011_2021/v5.1_cleaned.csv"
        ],
        outputs=[
            "validation_spacy_v_BERT/results/phase2/classification/v2_classification_*.csv",
            "validation_spacy_v_BERT/results/phase2/classification/pycaret_classification_*.csv",
        ],
        estimated_time="2-4 hours (GPU)",
        gpu_required=True,
        manual_steps=False
    ),
    PhaseDefinition(
        id="phase2",
        name="NER (V2 RoBERTa + spaCy Hybrid)",
        scripts=[
            "validation_spacy_v_BERT/scripts/07a_run_phase2_v2_ner.py",
            "validation_spacy_v_BERT/scripts/09b_run_spacy_full_hybrid_ner.py",
        ],
        notebooks=[
            "validation_spacy_v_BERT/notebooks/phase2_v2_ner_150k_VB.ipynb",
            "validation_spacy_v_BERT/notebooks/phase2_spacy_ner_150k_VB.ipynb",
        ],
        required_inputs=[
            "validation_spacy_v_BERT/results/phase2/classification/union_*.csv",
        ],
        outputs=[
            "validation_spacy_v_BERT/results/phase2/ner/v2_ner_results_*.csv",
            "validation_spacy_v_BERT/results/phase2/ner/spacy_ner_full_hybrid_results_*.csv",
        ],
        estimated_time="5-10 hours (GPU + CPU)",
        gpu_required=True,
        manual_steps=False
    ),
    PhaseDefinition(
        id="phase3",
        name="PMID Extraction (NER Union)",
        scripts=[
            "extract_ner_union_papers.py",
        ],
        notebooks=[],
        required_inputs=[
            "validation_spacy_v_BERT/results/phase2/ner/v2_ner_results_*.csv",
            "validation_spacy_v_BERT/results/phase2/ner/spacy_ner_full_hybrid_results_*.csv",
        ],
        outputs=[
            "advanced_paper_filtering/data/input/all_paper_pmids.txt"
        ],
        estimated_time="<1 minute",
        gpu_required=False,
        manual_steps=False
    ),
    PhaseDefinition(
        id="phase4",
        name="Linguistic Filtering",
        scripts=[
            "advanced_paper_filtering/scripts/03_linguistic_scoring.py",
        ],
        notebooks=[],
        required_inputs=[
            "advanced_paper_filtering/data/input/all_paper_pmids.txt"
        ],
        outputs=[
            "advanced_paper_filtering/data/linguistic_scores.csv",
        ],
        estimated_time="~30 seconds",
        gpu_required=False,
        manual_steps=False
    ),
    PhaseDefinition(
        id="phase5",
        name="SetFit Classification",
        scripts=[
            "advanced_filtering_pipeline/scripts/setup/01_setfit_inference.py",
        ],
        notebooks=[
            "advanced_paper_filtering/notebooks/setfit_inference_colab.ipynb",
        ],
        required_inputs=[
            "advanced_paper_filtering/data/linguistic_scores.csv"
        ],
        outputs=[
            "advanced_paper_filtering/results/setfit_*/setfit_classified_introductions.csv"
        ],
        estimated_time="10-15 minutes (GPU)",
        gpu_required=True,
        manual_steps=True  # Requires Colab
    ),
    PhaseDefinition(
        id="phase6",
        name="Entity Mapping & Resource Creation",
        scripts=[
            # Create paper sets and map entities
            "unified_bioresource_pipeline/scripts/phase5_mapping/09_create_paper_sets.py",
            "unified_bioresource_pipeline/scripts/phase5_mapping/10_map_to_entities.py",
            "unified_bioresource_pipeline/scripts/phase5_mapping/11_create_primary_resources.py",
            "unified_bioresource_pipeline/scripts/phase5_mapping/12_add_quality_indicators.py",
            "unified_bioresource_pipeline/scripts/phase5_mapping/13_extract_urls.py",
            # CRITICAL: Merge entity/URL data back into set_c_union (fixes 1,247 paper data loss)
            "unified_bioresource_pipeline/scripts/phase5_mapping/02b_update_set_c_with_entities.py",
        ],
        notebooks=[],
        required_inputs=[
            "advanced_paper_filtering/results/setfit_*/setfit_classified_introductions.csv"
        ],
        outputs=[
            "unified_bioresource_pipeline/data/phase5_mapping/papers_with_urls.csv"
        ],
        estimated_time="5-10 minutes",
        gpu_required=False,
        manual_steps=False
    ),
    PhaseDefinition(
        id="phase7",
        name="URL Scanning & Validation",
        scripts=[
            "unified_bioresource_pipeline/scripts/phase6_scanning/14_prepare_urls.py",
            "unified_bioresource_pipeline/scripts/phase6_scanning/15_scan_urls.py",
            "unified_bioresource_pipeline/scripts/phase6_scanning/16_merge_scan_scores.py",
            # NEW: Set C URL scanning with session support
            "unified_bioresource_pipeline/scripts/phase6_scanning/18_scan_urls_set_c.py",
            # NEW: Backfill URL data to sets A/B
            "unified_bioresource_pipeline/scripts/phase6_scanning/19_backfill_url_data.py",
        ],
        notebooks=[],
        required_inputs=[
            "unified_bioresource_pipeline/data/phase5_mapping/papers_with_urls.csv"
        ],
        outputs=[
            "unified_bioresource_pipeline/data/phase6_scanning/papers_with_url_scores.csv"
        ],
        estimated_time="75-90 minutes",
        gpu_required=False,
        manual_steps=False
    ),
    PhaseDefinition(
        id="phase8",
        name="Deduplication (Multi-Profile)",
        scripts=[
            # NEW: Multi-profile deduplication with title-based FP reduction
            "unified_bioresource_pipeline/scripts/phase7_deduplication/17_deduplicate_all_sets.py",
        ],
        notebooks=[],
        required_inputs=[
            "unified_bioresource_pipeline/data/phase6_scanning/papers_with_url_scores.csv"
        ],
        outputs=[
            "unified_bioresource_pipeline/data/phase7_deduplication/deduplicated_resources.csv"
        ],
        estimated_time="5 minutes + manual review",
        gpu_required=False,
        manual_steps=True  # Requires manual merge review for unclear cases
    ),
    PhaseDefinition(
        id="phase9",
        name="Baseline Comparison & Visualization",
        scripts=[
            # NEW: Compare against 2022 baseline (1,948 resources)
            "unified_bioresource_pipeline/scripts/phase8_baseline/20_baseline_comparison.py",
            # NEW: Generate PNG/HTML charts and reports
            "unified_bioresource_pipeline/scripts/phase8_baseline/21_generate_visualizations.py",
        ],
        notebooks=[],
        required_inputs=[
            "unified_bioresource_pipeline/data/phase7_deduplication/deduplicated_resources.csv"
        ],
        outputs=[
            "unified_bioresource_pipeline/data/phase8_baseline/baseline_comparison_report.md",
            "unified_bioresource_pipeline/data/phase8_baseline/visualizations/"
        ],
        estimated_time="5-10 minutes",
        gpu_required=False,
        manual_steps=False
    ),
]


class PipelineOrchestrator:
    """Master orchestrator for the unified bioresource pipeline."""

    def __init__(self, project_root: Path, dry_run: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.checkpoint_file = project_root / ".pipeline_checkpoint.json"
        self.log_dir = project_root / "logs" / "pipeline"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

    def print_phase(self, phase: PhaseDefinition):
        """Print phase information."""
        print(f"{Colors.OKCYAN}{Colors.BOLD}Phase: {phase.id.upper()}{Colors.ENDC}")
        print(f"{Colors.BOLD}Name:{Colors.ENDC} {phase.name}")
        print(f"{Colors.BOLD}Time:{Colors.ENDC} {phase.estimated_time}")
        if phase.gpu_required:
            print(f"{Colors.WARNING}⚠ GPU Required{Colors.ENDC}")
        if phase.manual_steps:
            print(f"{Colors.WARNING}⚠ Manual Steps Required{Colors.ENDC}")
        print()

    def print_success(self, text: str):
        """Print success message."""
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} {text}")

    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Colors.WARNING}⚠{Colors.ENDC} {text}")

    def print_error(self, text: str):
        """Print error message."""
        print(f"{Colors.FAIL}✗{Colors.ENDC} {text}")

    def check_file_exists(self, file_pattern: str) -> Tuple[bool, Optional[Path]]:
        """Check if a file matching the pattern exists."""
        # Handle wildcards
        if '*' in file_pattern:
            parent = self.project_root / Path(file_pattern).parent
            pattern = Path(file_pattern).name
            if parent.exists():
                matches = list(parent.glob(pattern))
                if matches:
                    return True, matches[0]
        else:
            path = self.project_root / file_pattern
            if path.exists():
                return True, path
        return False, None

    def check_phase_inputs(self, phase: PhaseDefinition) -> bool:
        """Check if all required inputs exist."""
        missing = []
        for input_file in phase.required_inputs:
            exists, _ = self.check_file_exists(input_file)
            if not exists:
                missing.append(input_file)

        if missing:
            self.print_error(f"Missing required inputs for {phase.id}:")
            for file in missing:
                print(f"  - {file}")
            return False

        self.print_success(f"All inputs verified for {phase.id}")
        return True

    def execute_script(self, script_path: str, phase_id: str) -> bool:
        """Execute a Python script."""
        full_path = self.project_root / script_path

        if not full_path.exists():
            self.print_error(f"Script not found: {script_path}")
            return False

        if self.dry_run:
            self.print_warning(f"[DRY RUN] Would execute: {script_path}")
            return True

        print(f"{Colors.OKBLUE}Executing:{Colors.ENDC} {script_path}")

        # Create log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"{phase_id}_{Path(script_path).stem}_{timestamp}.log"

        try:
            with open(log_file, 'w') as log:
                result = subprocess.run(
                    [sys.executable, str(full_path)],
                    cwd=str(self.project_root),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True
                )

            if result.returncode == 0:
                self.print_success(f"Completed: {script_path}")
                print(f"  Log: {log_file}")
                return True
            else:
                self.print_error(f"Failed: {script_path} (exit code {result.returncode})")
                print(f"  Check log: {log_file}")
                return False

        except Exception as e:
            self.print_error(f"Error executing {script_path}: {e}")
            return False

    def execute_phase(self, phase: PhaseDefinition) -> bool:
        """Execute a single phase."""
        self.print_phase(phase)

        # Check inputs
        if not self.check_phase_inputs(phase):
            return False

        # Execute notebooks (manual)
        if phase.notebooks:
            self.print_warning(f"Phase {phase.id} requires running notebooks:")
            for notebook in phase.notebooks:
                print(f"  - {notebook}")
            if not self.dry_run:
                response = input(f"\n{Colors.BOLD}Have you completed the notebook execution? (yes/no): {Colors.ENDC}")
                if response.lower() not in ['yes', 'y']:
                    self.print_error("User indicated notebooks not completed")
                    return False

        # Execute scripts
        for script in phase.scripts:
            if not self.execute_script(script, phase.id):
                return False

        # Manual steps
        if phase.manual_steps and not self.dry_run:
            self.print_warning(f"Phase {phase.id} requires manual review")
            response = input(f"\n{Colors.BOLD}Have you completed manual review? (yes/no): {Colors.ENDC}")
            if response.lower() not in ['yes', 'y']:
                self.print_error("User indicated manual review not completed")
                return False

        self.print_success(f"Phase {phase.id} completed successfully!")
        return True

    def save_checkpoint(self, completed_phase: str):
        """Save pipeline checkpoint."""
        checkpoint = {
            'last_completed_phase': completed_phase,
            'timestamp': datetime.now().isoformat(),
        }
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        print(f"\n{Colors.OKCYAN}Checkpoint saved: {completed_phase}{Colors.ENDC}")

    def load_checkpoint(self) -> Optional[str]:
        """Load pipeline checkpoint."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            return checkpoint.get('last_completed_phase')
        return None

    def show_status(self):
        """Show pipeline status."""
        self.print_header("PIPELINE STATUS")

        checkpoint = self.load_checkpoint()
        if checkpoint:
            print(f"{Colors.OKGREEN}Last completed phase:{Colors.ENDC} {checkpoint}")
        else:
            print(f"{Colors.WARNING}No checkpoint found{Colors.ENDC}")

        print(f"\n{Colors.BOLD}Phase Status:{Colors.ENDC}\n")

        for phase in PHASES:
            # Check inputs
            inputs_exist = True
            for input_file in phase.required_inputs:
                exists, _ = self.check_file_exists(input_file)
                if not exists:
                    inputs_exist = False
                    break

            # Check outputs
            outputs_exist = True
            for output_file in phase.outputs:
                exists, _ = self.check_file_exists(output_file)
                if not exists:
                    outputs_exist = False
                    break

            # Determine status
            if outputs_exist:
                status = f"{Colors.OKGREEN}✓ Complete{Colors.ENDC}"
            elif inputs_exist:
                status = f"{Colors.WARNING}⧗ Ready{Colors.ENDC}"
            else:
                status = f"{Colors.FAIL}✗ Blocked{Colors.ENDC}"

            print(f"{phase.id}: {status} - {phase.name}")

    def run_pipeline(self, start_phase: Optional[str] = None, end_phase: Optional[str] = None):
        """Run the complete pipeline or a subset."""
        self.print_header("UNIFIED BIORESOURCE PIPELINE")

        # Determine phase range
        start_idx = 0
        end_idx = len(PHASES)

        if start_phase:
            try:
                start_idx = next(i for i, p in enumerate(PHASES) if p.id == start_phase)
            except StopIteration:
                self.print_error(f"Unknown phase: {start_phase}")
                return False

        if end_phase:
            try:
                end_idx = next(i for i, p in enumerate(PHASES) if p.id == end_phase) + 1
            except StopIteration:
                self.print_error(f"Unknown phase: {end_phase}")
                return False

        phases_to_run = PHASES[start_idx:end_idx]

        # Show execution plan
        print(f"{Colors.BOLD}Execution Plan:{Colors.ENDC}")
        for phase in phases_to_run:
            print(f"  {phase.id} - {phase.name} ({phase.estimated_time})")

        if self.dry_run:
            self.print_warning("\n[DRY RUN MODE] - No scripts will be executed")

        print()

        # Execute phases
        for phase in phases_to_run:
            if not self.execute_phase(phase):
                self.print_error(f"Pipeline stopped at phase {phase.id}")
                return False

            if not self.dry_run:
                self.save_checkpoint(phase.id)

        # Success
        self.print_header("PIPELINE COMPLETE")
        self.print_success("All phases executed successfully!")

        # Show final output
        final_phase = phases_to_run[-1]
        print(f"\n{Colors.BOLD}Final Output:{Colors.ENDC}")
        for output in final_phase.outputs:
            exists, path = self.check_file_exists(output)
            if exists:
                print(f"  ✓ {path}")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Bioresource Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --full                 # Run complete pipeline
  python run_pipeline.py --from phase3          # Resume from PMID extraction
  python run_pipeline.py --phase phase1         # Run only classification
  python run_pipeline.py --status               # Check pipeline status
  python run_pipeline.py --full --dry-run       # Preview without execution

Phases:
  phase1 - Classification (V2 RoBERTa + PyCaret)
  phase2 - NER (V2 RoBERTa + spaCy Hybrid)
  phase3 - PMID Extraction (NER union)
  phase4 - Linguistic Filtering
  phase5 - SetFit Classification
  phase6 - Entity Mapping & Resource Creation (includes 02b data fix)
  phase7 - URL Scanning & Validation (includes backfill)
  phase8 - Deduplication (multi-profile support)
  phase9 - Baseline Comparison & Visualization
        """
    )

    parser.add_argument('--full', action='store_true',
                       help='Run the complete pipeline')
    parser.add_argument('--from', dest='start_phase',
                       help='Resume from specified phase (e.g., phase3)')
    parser.add_argument('--to', dest='end_phase',
                       help='Run until specified phase (e.g., phase5)')
    parser.add_argument('--phase', dest='single_phase',
                       help='Run only the specified phase')
    parser.add_argument('--status', action='store_true',
                       help='Show pipeline status')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview execution without running scripts')
    parser.add_argument('--list-phases', action='store_true',
                       help='List all available phases')

    args = parser.parse_args()

    # Project root
    project_root = Path(__file__).resolve().parent

    # Initialize orchestrator
    orchestrator = PipelineOrchestrator(project_root, dry_run=args.dry_run)

    # Handle commands
    if args.list_phases:
        orchestrator.print_header("AVAILABLE PHASES")
        for phase in PHASES:
            print(f"\n{Colors.BOLD}{phase.id}{Colors.ENDC}")
            print(f"  Name: {phase.name}")
            print(f"  Time: {phase.estimated_time}")
            print(f"  GPU: {'Yes' if phase.gpu_required else 'No'}")
            print(f"  Manual: {'Yes' if phase.manual_steps else 'No'}")
        return 0

    if args.status:
        orchestrator.show_status()
        return 0

    # Execute pipeline
    success = False

    if args.full:
        success = orchestrator.run_pipeline()
    elif args.single_phase:
        success = orchestrator.run_pipeline(
            start_phase=args.single_phase,
            end_phase=args.single_phase
        )
    elif args.start_phase:
        success = orchestrator.run_pipeline(
            start_phase=args.start_phase,
            end_phase=args.end_phase
        )
    else:
        parser.print_help()
        return 0

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
