#!/bin/bash
################################################################################
# Master Script: Run Scripts 05-08
#
# Purpose: Execute the final phase of the comparison pipeline:
#   - Sample 100 papers for qualitative analysis
#   - Generate side-by-side comparison
#   - Create comprehensive report
#   - Generate all visualizations
#
# Usage:
#   bash run_scripts_05_08.sh [OPTIONS]
#
# Options:
#   --n-per-category N     Number of papers per category (default: 25)
#   --skip-sampling        Skip Script 05 (use existing sample)
#   --skip-viz             Skip Script 08 (visualizations)
#   --help                 Show this help message
#
# Author: Analysis Pipeline
# Date: 2025-11-05
################################################################################

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error
set -o pipefail  # Pipeline fails if any command fails

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
N_PER_CATEGORY=25
SKIP_SAMPLING=false
SKIP_VIZ=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --n-per-category)
            N_PER_CATEGORY="$2"
            shift 2
            ;;
        --skip-sampling)
            SKIP_SAMPLING=true
            shift
            ;;
        --skip-viz)
            SKIP_VIZ=true
            shift
            ;;
        --help)
            head -n 25 "$0" | tail -n 18
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print section headers
print_header() {
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warnings
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print errors
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to check if file exists
check_file() {
    if [ ! -f "$1" ]; then
        print_error "Required file not found: $1"
        return 1
    fi
    return 0
}

# Start timestamp
START_TIME=$(date +%s)

print_header "SCRIPTS 05-08: ANALYSIS & REPORTING PIPELINE"
echo "Configuration:"
echo "  - Papers per category: $N_PER_CATEGORY"
echo "  - Skip sampling: $SKIP_SAMPLING"
echo "  - Skip visualizations: $SKIP_VIZ"
echo ""

# Check prerequisites
print_header "Checking Prerequisites"

PREREQ_FAILED=false

if ! check_file "../results/04_merged_comparison.csv"; then
    PREREQ_FAILED=true
fi

if ! check_file "../data/ground_truth.json"; then
    PREREQ_FAILED=true
fi

if ! check_file "../results/02_quantitative_metrics.json"; then
    PREREQ_FAILED=true
fi

if ! check_file "../results/03_qualitative_analysis.json"; then
    PREREQ_FAILED=true
fi

if ! check_file "../results/04_bpe_analysis.json"; then
    PREREQ_FAILED=true
fi

if [ "$PREREQ_FAILED" = true ]; then
    print_error "Prerequisites not met!"
    echo ""
    echo "Please run Scripts 01-04 first:"
    echo "  python 01_compute_quantitative_metrics.py"
    echo "  python 02_qualitative_error_analysis.py"
    echo "  python 03_analyze_bpe_artifacts.py"
    echo "  python 04_merge_all_results.py"
    exit 1
fi

print_success "All prerequisites satisfied"

# =============================================================================
# Script 05: Sample 100 Papers
# =============================================================================

if [ "$SKIP_SAMPLING" = false ]; then
    print_header "SCRIPT 05: Sample 100 Papers for Qualitative Analysis"

    python 05_sample_100_papers.py --n-per-category "$N_PER_CATEGORY"

    if [ $? -eq 0 ]; then
        print_success "Script 05 completed successfully"

        # Verify outputs
        if check_file "../data/sample_100_papers.csv" && check_file "../data/sample_stratification.json"; then
            print_success "Output files verified"

            # Show sample statistics
            echo ""
            echo "Sample statistics:"
            python -c "import pandas as pd; df=pd.read_csv('../data/sample_100_papers.csv'); print('  Total papers:', len(df)); print('  Category breakdown:'); print(df['category'].value_counts().to_string().replace('\n', '\n  '))" 2>/dev/null || echo "  (Statistics unavailable)"
        else
            print_error "Output files not found"
            exit 1
        fi
    else
        print_error "Script 05 failed"
        exit 1
    fi
else
    print_warning "Skipping Script 05 (sampling)"

    # Verify existing sample
    if ! check_file "../data/sample_100_papers.csv"; then
        print_error "No existing sample found! Cannot skip sampling."
        exit 1
    fi
    print_success "Using existing sample"
fi

# =============================================================================
# Script 06: Generate Side-by-Side Comparison
# =============================================================================

print_header "SCRIPT 06: Generate Side-by-Side Comparison"

python 06_generate_side_by_side.py

if [ $? -eq 0 ]; then
    print_success "Script 06 completed successfully"

    # Verify outputs
    if check_file "../results/100_paper_comparison.html" && \
       check_file "../results/100_paper_comparison.md" && \
       check_file "../results/category_breakdown.json"; then
        print_success "Output files verified"

        echo ""
        echo "Key output: ../results/100_paper_comparison.html"
        echo "  Open in browser for interactive review"
    else
        print_error "Output files not found"
        exit 1
    fi
else
    print_error "Script 06 failed"
    exit 1
fi

# =============================================================================
# Script 07: Generate Final Report
# =============================================================================

print_header "SCRIPT 07: Generate Final Comprehensive Report"

python 07_generate_final_report.py

if [ $? -eq 0 ]; then
    print_success "Script 07 completed successfully"

    # Verify outputs
    if check_file "../results/PHASE4_VS_V2_COMPREHENSIVE_REPORT.md" && \
       check_file "../results/EXECUTIVE_SUMMARY.md" && \
       check_file "../results/report_metadata.json"; then
        print_success "Output files verified"

        echo ""
        echo "Key outputs:"
        echo "  - Executive Summary: ../results/EXECUTIVE_SUMMARY.md"
        echo "  - Full Report: ../results/PHASE4_VS_V2_COMPREHENSIVE_REPORT.md"
    else
        print_error "Output files not found"
        exit 1
    fi
else
    print_error "Script 07 failed"
    exit 1
fi

# =============================================================================
# Script 08: Create Visualizations
# =============================================================================

if [ "$SKIP_VIZ" = false ]; then
    print_header "SCRIPT 08: Create Visualizations"

    python 08_create_visualizations.py

    if [ $? -eq 0 ]; then
        print_success "Script 08 completed successfully"

        # Verify outputs
        EXPECTED_FIGURES=(
            "01_performance_comparison.png"
            "02_confusion_matrices.png"
            "03_entity_distribution.png"
            "04_bpe_contamination.png"
            "05_coverage_analysis.png"
            "06_entity_length_distribution.png"
        )

        ALL_FOUND=true
        for fig in "${EXPECTED_FIGURES[@]}"; do
            if ! check_file "../figures/$fig"; then
                ALL_FOUND=false
            fi
        done

        if [ "$ALL_FOUND" = true ]; then
            print_success "All 6 figures generated"

            echo ""
            echo "Figures saved to: ../figures/"
            ls -lh ../figures/*.png | awk '{print "  -", $9, "(" $5 ")"}'
        else
            print_error "Some figures missing"
            exit 1
        fi
    else
        print_error "Script 08 failed"
        exit 1
    fi
else
    print_warning "Skipping Script 08 (visualizations)"
fi

# =============================================================================
# Summary
# =============================================================================

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

print_header "PIPELINE COMPLETE"

echo -e "${GREEN}All scripts executed successfully!${NC}"
echo ""
echo "Execution time: ${MINUTES}m ${SECONDS}s"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "                              KEY DELIVERABLES"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 EXECUTIVE SUMMARY (start here):"
echo "   ../results/EXECUTIVE_SUMMARY.md"
echo ""
echo "📄 COMPREHENSIVE REPORT:"
echo "   ../results/PHASE4_VS_V2_COMPREHENSIVE_REPORT.md"
echo ""
echo "🌐 INTERACTIVE COMPARISON (100 papers):"
echo "   ../results/100_paper_comparison.html"
echo ""
echo "📈 VISUALIZATIONS (6 figures):"
echo "   ../figures/"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Review executive summary for high-level findings"
echo "  2. Open HTML comparison in browser for detailed inspection"
echo "  3. Read full report for comprehensive analysis"
echo "  4. Use figures in presentations/publications"
echo "  5. Make informed decision: Deploy Phase 4 or continue with V2?"
echo ""
print_success "Analysis pipeline complete!"
