# Documentation Index - GBC Biodata Inventory ML Pipeline

**Last Updated**: 2025-10-29
**Purpose**: Complete index of all documentation files with descriptions

---

## 📋 Quick Reference

- **Getting Started**: Read `starting_doc.md` first
- **Latest Progress**: See `EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md`
- **Full Implementation Plan**: See `COMPREHENSIVE_IMPLEMENTATION_PLAN.md`
- **Research Findings**: See `research/RESEARCH_FINDINGS_CONSOLIDATED.md`

---

## Core Documentation

### `starting_doc.md` ⭐ START HERE
**Primary AI agent reference guide**
- System architecture and pipeline flow
- Current production status and models
- Quick start commands and common tasks
- Critical file locations and references
- Model training quality investigation results
- Best practices and safety procedures
- **Status**: ✅ Current (Updated 2025-10-29)

### `README.md`
**Project overview and workflow**
- High-level project description
- Team information and contacts
- Project goals and objectives
- Repository structure
- **Status**: ✅ Current

### `modernization-python311.md`
**Complete Python 3.11 modernization documentation**
- Migration from Python 3.8 to 3.11.9
- Package updates and compatibility
- Environment setup procedures
- Testing and validation results
- **Status**: ✅ Current

### `training_ML_explanation.md`
**Detailed ML pipeline technical documentation**
- BIO tagging scheme explanation
- Model architecture details
- Training procedures and parameters
- Data processing workflows
- **Status**: ✅ Current

---

## Infrastructure & Setup

### `MODERN_ENVIRONMENT_SETUP.md`
**Environment setup and troubleshooting**
- Virtual environment creation
- Dependency installation
- Common issues and solutions
- Platform-specific notes
- **Status**: ✅ Current

### `FULL_TRAINING_README.md`
**Training pipeline user guide**
- Full training execution instructions
- Script parameters and options
- Expected outputs and artifacts
- Monitoring and validation
- **Status**: ✅ Current

### `PIPELINE_GUIDES.md`
**Comprehensive pipeline execution guides**
- Inventory update pipeline guide
- 2022 rerun pipeline guide
- Workflow options and choices
- Troubleshooting common issues
- **Status**: ✅ Current

---

## Recent Work & Implementation (2025-10-29)

### `EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md` ⭐ NEW
**Complete progress report on experimental infrastructure**
- Research phase summary (4 comprehensive reports)
- Infrastructure implementation details
- Code fixes and verification
- 3-phase roadmap and timeline
- Cost and resource analysis
- Success criteria and next steps
- **Status**: ✅ Current
- **Length**: ~500 lines
- **Importance**: Critical for understanding current work

### `COMPREHENSIVE_IMPLEMENTATION_PLAN.md` ⭐ NEW
**Detailed 3-phase model improvement roadmap**
- Phase 1: Quick wins (Week 1) → NER F1 0.80-0.82
- Phase 2: Data & transfer (Weeks 2-3) → NER F1 0.85-0.87
- Phase 3: Advanced techniques (Weeks 4-6) → NER F1 0.86-0.88
- Implementation guides for each phase
- Resource requirements and costs
- Risk assessment and mitigation
- **Status**: ✅ Current
- **Length**: ~500 lines
- **Importance**: Critical roadmap document

### `CODE_FIXES_VERIFICATION_2025-10-29.md`
**Verification of critical code fixes**
- 5 critical/high-priority fixes detailed
- Code snippets showing implementations
- Verification status for each fix
- Impact summary and benefits
- **Status**: ✅ Current
- **Importance**: Confirms infrastructure quality

### `UPDATE_SUMMARY_2025-10-29.md`
**Summary of October 29 work**
- Research completion overview
- Infrastructure implementation summary
- Quick reference to key documents
- **Status**: ✅ Current

---

## Research & Analysis (2025-10-29)

### Research Briefs (research/ directory)

#### `research/BASE_RESEARCH_BRIEF.md`
**Comprehensive project context for research agents**
- Complete system architecture
- Current performance metrics
- Dataset limitations (554 NER samples)
- Constraints and requirements
- Success criteria
- **Length**: 10 pages
- **Status**: ✅ Complete

#### `research/MODERN_ML_ALTERNATIVES_BRIEF.md`
**Research questions on modern ML techniques**
- 2023-2025 biomedical language models
- Parameter-efficient fine-tuning (LoRA/QLoRA)
- Modern optimizers and schedulers
- Mixed precision training
- **Status**: ✅ Complete

#### `research/DATA_AUGMENTATION_NER_BRIEF.md`
**Research questions on data augmentation**
- Entity-preserving augmentation techniques
- UMLS-EDA, back-translation, LLM generation
- Goal: 554 → 1,000-1,500 samples
- Quality validation strategies
- **Status**: ✅ Complete

#### `research/FEW_SHOT_META_LEARNING_BRIEF.md`
**Research questions on few-shot learning**
- SetFit, MAML, meta-learning approaches
- Task-adaptive pre-training (TAPT)
- Self-training and pseudo-labeling
- Contrastive learning methods
- **Status**: ✅ Complete

#### `research/ENSEMBLE_MULTITASK_BRIEF.md`
**Research questions on ensemble methods**
- Ensemble strategies for classification and NER
- Multi-task learning architectures
- Cost-benefit analysis
- Production feasibility
- **Status**: ✅ Complete

### Research Reports (research/ directory)

#### `research/RESEARCH_FINDINGS_CONSOLIDATED.md` ⭐ MASTER DOCUMENT
**Consolidation of all research findings**
- Executive summary of all 4 reports
- Consensus recommendations
- 3-phase implementation roadmap
- Expected outcomes and costs
- Prioritized action items
- **Length**: ~150 pages
- **Status**: ✅ Complete
- **Importance**: Master research reference

#### `research/MODERN_ML_ALTERNATIVES_RESEARCH_REPORT.md`
**Comprehensive modern ML techniques research**
- BioLinkBERT-base recommended (2023)
- LoRA for parameter-efficient training
- Mixed precision training guide
- Early stopping implementation
- Modern optimizers comparison
- **Length**: 100+ pages
- **Status**: ✅ Complete

#### `research/DATA_AUGMENTATION_NER_RESEARCH_REPORT.md`
**Data augmentation strategies and implementations**
- #1 Recommendation: UMLS-EDA (+5-17% F1 proven)
- GPT-4 synthetic generation guide
- Back-translation with entity protection
- Implementation code examples
- Quality validation methods
- **Status**: ✅ Complete

#### `research/FEW_SHOT_META_LEARNING_RESEARCH_REPORT.md`
**Few-shot learning and meta-learning approaches**
- TAPT on 21,677 papers (+3-8% F1)
- Self-training with pseudo-labels
- SetFit for few-shot scenarios
- Layer-wise learning rate decay
- **Status**: ✅ Complete

#### `research/ENSEMBLE_MULTITASK_RESEARCH_REPORT.md`
**Ensemble and multi-task learning evaluation**
- Verdict: NOT RECOMMENDED
- 3-5x cost for +1-3% F1
- Focus on single model improvements
- Detailed cost-benefit analysis
- **Status**: ✅ Complete

---

## Technical Investigations & Diagnostics

### `PYTORCH_CHECKPOINT_FIX.md`
**PyTorch 2.8 compatibility resolution**
- NamedTuple deserialization issue
- Checkpoint conversion to dict format
- weights_only=True implementation
- 99.97% prediction match verification
- Checkpoint corruption investigation
- **Date**: 2025-10-27
- **Status**: ✅ Complete (Issue resolved)

### `FINAL_DIAGNOSIS_SUMMARY.md`
**Model training quality investigation summary**
- Oct 28 training degradation analysis
- Root cause: LR too high, no weight decay
- Training quality validation checklist
- Recommended hyperparameters
- V2 models validated for production
- **Date**: 2025-10-29
- **Status**: ✅ Complete

### `MODEL_DEGRADATION_ROOT_CAUSE_ANALYSIS.md`
**Detailed technical analysis of training issues**
- Training curve analysis
- Hyperparameter investigation
- Overfitting diagnosis
- Comparison with baseline models
- Technical recommendations
- **Date**: 2025-10-29
- **Status**: ✅ Complete

### `CRITICAL_INVESTIGATION_2025-10-28.md`
**Investigation process and diagnostic methodology**
- Step-by-step investigation approach
- Evidence gathering and analysis
- Hypothesis testing methodology
- Diagnostic best practices
- **Date**: 2025-10-28
- **Status**: ✅ Complete

### `COLAB_PROBABILITY_INVESTIGATION.md`
**Investigation of Colab probability discrepancies**
- Checkpoint corruption analysis
- Data contamination diagnosis
- Resolution: Removed checkpoints
- **Date**: 2025-10-28
- **Status**: ✅ Complete (Deprecated checkpoints)

---

## Comparison & Validation

### `INVENTORY_COMPARISON_ANALYSIS.md`
**Quality validation and comparison methodology**
- Comparison methodology description
- Statistical analysis approach
- Quality metrics and thresholds
- Validation best practices
- **Status**: ✅ Current

### `INVENTORY_COMPARISON_REPORT_2025-10-28.md`
**Detailed comparison of model outputs**
- Specific comparison results
- Statistical summaries
- Quality assessment
- Recommendations
- **Date**: 2025-10-28
- **Status**: ✅ Complete

### `COMPARISON_SUMMARY.txt`
**Quick reference summary**
- Key comparison statistics
- High-level findings
- Model performance summaries
- **Status**: ✅ Current

---

## System Architecture & Features

### `MODEL_ARCHIVAL_SYSTEM.md`
**Model archival system implementation**
- Archive structure and organization
- Session ID management
- Traceability system
- Recovery procedures
- **Status**: ✅ Current

### `RERUN_NOTEBOOK_SIMPLIFICATION_SUMMARY.md`
**Rerun notebook simplification**
- Checkpoint system removal rationale
- Simplified architecture benefits
- Data integrity improvements
- **Date**: 2025-10-28
- **Status**: ✅ Complete

### `TRAINING_NOTEBOOK_SIMPLIFICATION.md`
**Training notebook improvements**
- Session isolation implementation
- Utility function separation
- Architecture simplification
- **Status**: ✅ Current

---

## Historical Reference

### `HISTORICAL_UPDATES.md`
**Session-by-session changelog**
- Technical evolution timeline
- Architecture decisions and rationale
- Refactoring work summaries
- Major milestones
- **Status**: ✅ Maintained

### `full_training_21_10_25_doc.md`
**October 21 training session documentation**
- Specific training run details
- Results and metrics
- Artifacts produced
- Lessons learned
- **Date**: 2025-10-21
- **Status**: ✅ Historical reference

---

## Legacy & Deprecated

### `CODE_REVIEW_FIXES_2025-10-29.md`
**Deprecated - See CODE_FIXES_VERIFICATION instead**
- Initial report from code-reviewer agent
- Contained inaccurate information (fixes were actually applied)
- Superseded by verification document
- **Status**: ⚠️ Deprecated

### `EXPERIMENTAL_TRAINING_IMPLEMENTATION.md`
**Deprecated - See EXPERIMENTAL_INFRASTRUCTURE_PROGRESS instead**
- Initial implementation documentation
- Superseded by comprehensive progress report
- **Status**: ⚠️ Deprecated

---

## Plans (plans/ directory)

### `plans/2025-10-22_2022_inventory_rerun_plan.md`
**2022 rerun implementation plan**
- Objectives and requirements
- Implementation approach
- Timeline and milestones
- **Date**: 2025-10-22
- **Status**: ✅ Implemented

### `plans/2025-10-23_colab_conversion_plan.md`
**Colab notebook conversion plan**
- Conversion requirements
- Architecture decisions
- Implementation steps
- **Date**: 2025-10-23
- **Status**: ✅ Implemented

### `plans/2025-10-28_rerun_notebook_simplification_plan.md`
**Rerun simplification implementation plan**
- Simplification objectives
- Checkpoint removal rationale
- Implementation approach
- **Date**: 2025-10-28
- **Status**: ✅ Implemented

### `plans/2025-10-28_model_traceability_plan.md`
**Model traceability implementation plan**
- Traceability requirements
- Session linking design
- Implementation details
- **Date**: 2025-10-28
- **Status**: ✅ Implemented

---

## Research Docs (research_docs/ directory)

### `research_docs/pipeline_improvement.md`
**Pipeline improvement research**
- Historical improvement research
- Optimization opportunities
- **Status**: Historical reference

### `research_docs/pmc_attributes_research.md`
**PubMed Central attributes research**
- EuropePMC data analysis
- Available attributes and fields
- **Status**: Historical reference

### `research_docs/tpm_GBC_paper_pipeline_overview.md`
**Original pipeline overview**
- Historical pipeline documentation
- Legacy architecture reference
- **Status**: Historical reference

---

## Pipeline Steps (Legacy)

### `pipeline_modern_steps.md`
**Modern pipeline execution steps**
- Step-by-step pipeline guide
- Python 3.11 environment
- **Status**: Superseded by PIPELINE_GUIDES.md

### `pipeline_python38_steps.md`
**Legacy Python 3.8 pipeline steps**
- Historical reference only
- **Status**: ⚠️ Deprecated (Python 3.8 no longer used)

---

## Document Categories Summary

### Critical Documents (Read These First)
1. **starting_doc.md** - Start here for everything
2. **EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md** - Current work status
3. **COMPREHENSIVE_IMPLEMENTATION_PLAN.md** - Roadmap forward
4. **research/RESEARCH_FINDINGS_CONSOLIDATED.md** - All research findings

### Technical References
- PYTORCH_CHECKPOINT_FIX.md
- MODEL_DEGRADATION_ROOT_CAUSE_ANALYSIS.md
- FINAL_DIAGNOSIS_SUMMARY.md
- CRITICAL_INVESTIGATION_2025-10-28.md

### Implementation Guides
- FULL_TRAINING_README.md
- PIPELINE_GUIDES.md
- MODERN_ENVIRONMENT_SETUP.md
- training_ML_explanation.md

### Research Materials
- All files in research/ directory
- RESEARCH_FINDINGS_CONSOLIDATED.md is the master

### Historical Reference
- HISTORICAL_UPDATES.md
- full_training_21_10_25_doc.md
- All files in research_docs/ directory
- All files in plans/ directory

---

## Total Documentation Statistics

**Total Files**: 42 markdown files
**Research Documents**: 11 files (5 briefs + 5 reports + 1 consolidated)
**Core Documentation**: 9 files
**Technical Investigations**: 6 files
**Plans**: 4 files
**Historical**: 3 files
**Research Docs**: 3 files
**Deprecated**: 3 files

**Total Documentation Size**: ~1,000+ pages
**Research Reports Alone**: ~400+ pages
**Implementation Guides**: ~200+ pages

---

## Maintenance Status

### ✅ Current & Maintained
- starting_doc.md
- EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md
- COMPREHENSIVE_IMPLEMENTATION_PLAN.md
- All research documents (completed 2025-10-29)
- CODE_FIXES_VERIFICATION_2025-10-29.md

### ⚠️ Deprecated / Superseded
- CODE_REVIEW_FIXES_2025-10-29.md → Use CODE_FIXES_VERIFICATION
- EXPERIMENTAL_TRAINING_IMPLEMENTATION.md → Use EXPERIMENTAL_INFRASTRUCTURE_PROGRESS
- pipeline_python38_steps.md → Python 3.8 no longer used

### 📚 Historical Reference Only
- All files in research_docs/ directory
- full_training_21_10_25_doc.md
- All implemented plans in plans/ directory

---

## Quick Navigation by Topic

### Want to understand the current system?
→ Read **starting_doc.md**

### Want to know what was just built?
→ Read **EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md**

### Want to know what's next?
→ Read **COMPREHENSIVE_IMPLEMENTATION_PLAN.md**

### Want to see all the research?
→ Read **research/RESEARCH_FINDINGS_CONSOLIDATED.md**

### Want to understand model training issues?
→ Read **FINAL_DIAGNOSIS_SUMMARY.md**

### Want to know about PyTorch compatibility?
→ Read **PYTORCH_CHECKPOINT_FIX.md**

### Want to run the training pipeline?
→ Read **FULL_TRAINING_README.md**

### Want to run prediction pipelines?
→ Read **PIPELINE_GUIDES.md**

### Want to set up the environment?
→ Read **MODERN_ENVIRONMENT_SETUP.md**

---

**Document Status**: ✅ Complete
**Last Updated**: 2025-10-29
**Purpose**: Master index of all documentation
**Location**: docs/DOCUMENTATION_INDEX.md
