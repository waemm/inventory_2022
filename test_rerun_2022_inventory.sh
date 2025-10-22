#!/bin/bash

# TEST VERSION - 2022 Inventory Rerun Script
# Tests with small dataset (~40 articles) to validate functionality
# Date: 2025-10-22

set -e  # Exit on any error

# Script configuration
SCRIPT_START_TIME=$(date +%s)
RUN_DATE=$(date '+%Y-%m-%d')
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')

# Environment and paths
ENV_PATH="biodata_modern_env"
PYTHONPATH="src:$PYTHONPATH"

# Input data - TESTING WITH SMALL DATASET
INPUT_DATA="data/epmc_query_results_2022_test.csv"

# Models (latest production models from October 21, 2025)
CLASSIF_MODEL="out/classif_train_out/article_classifier.pt"
NER_MODEL="out/ner_train_out/named_entity_recognition.pt"

# Output directories  
BASE_OUTPUT_DIR="inventory_classification_results"
RUN_OUTPUT_DIR="$BASE_OUTPUT_DIR/${RUN_DATE}_test_run"
CLASSIF_DIR="$RUN_OUTPUT_DIR/classification"
NER_DIR="$RUN_OUTPUT_DIR/ner"
URL_DIR="$RUN_OUTPUT_DIR/url_extraction"
NAMES_DIR="$RUN_OUTPUT_DIR/processed_names"
FINAL_DIR="$RUN_OUTPUT_DIR/final_results"
LOGS_DIR="$RUN_OUTPUT_DIR/logs"

# Pipeline parameters
MAX_URLS="3"

# Log file
LOG_FILE="$LOGS_DIR/processing_log_${TIMESTAMP}.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function definitions
print_header() {
    local msg="$1"
    echo -e "${PURPLE}===================================================${NC}"
    echo -e "${PURPLE}$msg${NC}"
    echo -e "${PURPLE}===================================================${NC}"
    log_message "HEADER" "$msg"
}

print_status() {
    local msg="$1"
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $msg"
    log_message "INFO" "$msg"
}

print_success() {
    local msg="$1"
    echo -e "${GREEN}[SUCCESS]${NC} $msg"
    log_message "SUCCESS" "$msg"
}

print_warning() {
    local msg="$1"
    echo -e "${YELLOW}[WARNING]${NC} $msg"
    log_message "WARNING" "$msg"
}

print_error() {
    local msg="$1"
    echo -e "${RED}[ERROR]${NC} $msg"
    log_message "ERROR" "$msg"
}

print_progress() {
    local msg="$1"
    echo -e "${CYAN}[PROGRESS]${NC} $msg"
    log_message "PROGRESS" "$msg"
}

log_message() {
    local level="$1"
    local msg="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $msg" >> "$LOG_FILE"
}

check_prerequisites() {
    print_status "Checking prerequisites for TEST RUN..."
    
    # Check environment
    if [ ! -d "$ENV_PATH" ]; then
        print_error "Environment $ENV_PATH not found"
        print_status "Please ensure the modern environment is created"
        exit 1
    fi
    
    # Check input data
    if [ ! -f "$INPUT_DATA" ]; then
        print_error "Test input data not found: $INPUT_DATA"
        exit 1
    fi
    
    # Check data size
    local data_lines=$(wc -l < "$INPUT_DATA")
    print_status "TEST INPUT: $INPUT_DATA"
    print_status "Test papers to process: $((data_lines - 1))"
    
    # Check models
    if [ ! -f "$CLASSIF_MODEL" ]; then
        print_error "Classification model not found: $CLASSIF_MODEL"
        exit 1
    fi
    
    if [ ! -f "$NER_MODEL" ]; then
        print_error "NER model not found: $NER_MODEL"
        exit 1
    fi
    
    # Check model sizes (approximate verification)
    local classif_size=$(du -m "$CLASSIF_MODEL" | cut -f1)
    local ner_size=$(du -m "$NER_MODEL" | cut -f1)
    
    print_status "Model verification:"
    print_status "  Classification model: ${classif_size}MB"
    print_status "  NER model: ${ner_size}MB"
    
    print_success "Prerequisites check passed for TEST RUN"
}

setup_environment() {
    print_status "Setting up environment and directories for TEST..."
    
    # Create all output directories
    mkdir -p "$BASE_OUTPUT_DIR" "$RUN_OUTPUT_DIR" "$CLASSIF_DIR" "$NER_DIR" \
             "$URL_DIR" "$NAMES_DIR" "$FINAL_DIR" "$LOGS_DIR"
    
    # Activate environment
    source "$ENV_PATH/bin/activate"
    export PYTHONPATH="src:$PYTHONPATH"
    
    print_status "Environment activated: $ENV_PATH"
    print_status "TEST output directory: $RUN_OUTPUT_DIR"
    
    # Verify environment
    print_status "Verifying environment setup..."
    python -c "
import torch, transformers, datasets, evaluate
print(f'PyTorch: {torch.__version__}')
print(f'Transformers: {transformers.__version__}')
print(f'Datasets: {datasets.__version__}')
print(f'Evaluate: {evaluate.__version__}')
" | tee -a "$LOG_FILE"
    
    print_success "Environment setup complete for TEST"
}

run_classification() {
    print_progress "TEST Step 1/5: Running classification on test papers..."
    local start_time=$(date +%s)
    
    print_status "Input: $INPUT_DATA"
    print_status "Model: $CLASSIF_MODEL"
    print_status "Output: $CLASSIF_DIR/predictions.csv"
    
    python src/class_predict.py \
        -o "$CLASSIF_DIR" \
        -i "$INPUT_DATA" \
        -c "$CLASSIF_MODEL"
    
    if [ $? -eq 0 ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "Classification completed (${duration}s)"
        
        # Verify output and get counts
        local total_predictions=$(tail -n +2 "$CLASSIF_DIR/predictions.csv" | wc -l)
        print_status "Total predictions: $total_predictions"
        
        # Show first few predictions for verification
        print_status "Sample predictions:"
        head -6 "$CLASSIF_DIR/predictions.csv" | tee -a "$LOG_FILE"
        
        # Filter positive predictions
        print_status "Filtering bio-resource papers..."
        python -c "
import pandas as pd
df = pd.read_csv('$CLASSIF_DIR/predictions.csv')
positives = df[df['predicted_label'] == 'bio-resource']
positives.to_csv('$CLASSIF_DIR/predicted_positives.csv', index=False)
print(f'Bio-resource papers: {len(positives)} out of {len(df)} ({len(positives)/len(df)*100:.1f}%)')
if len(positives) > 0:
    print('Sample bio-resource papers:')
    print(positives[['id', 'predicted_label', 'predicted_prob']].head(3).to_string(index=False))
else:
    print('No bio-resource papers found in test set')
" | tee -a "$LOG_FILE"
        
        print_success "Positive predictions filtered successfully"
    else
        print_error "Classification failed"
        exit 1
    fi
}

run_ner() {
    print_progress "TEST Step 2/5: Running NER on bio-resource papers..."
    local start_time=$(date +%s)
    
    # Check if we have any positive predictions
    local positive_count=$(tail -n +2 "$CLASSIF_DIR/predicted_positives.csv" | wc -l)
    if [ "$positive_count" -eq 0 ]; then
        print_warning "No bio-resource papers found, creating empty NER output"
        cp "$CLASSIF_DIR/predicted_positives.csv" "$NER_DIR/predictions.csv"
        return 0
    fi
    
    print_status "Input: $CLASSIF_DIR/predicted_positives.csv"
    print_status "Model: $NER_MODEL"
    print_status "Output: $NER_DIR/predictions.csv"
    print_status "Processing $positive_count bio-resource papers"
    
    python src/ner_predict.py \
        -o "$NER_DIR" \
        -i "$CLASSIF_DIR/predicted_positives.csv" \
        -c "$NER_MODEL"
    
    if [ $? -eq 0 ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "NER completed (${duration}s)"
        
        local ner_predictions=$(tail -n +2 "$NER_DIR/predictions.csv" | wc -l)
        print_status "Papers with NER results: $ner_predictions"
        
        # Show sample NER results
        if [ "$ner_predictions" -gt 0 ]; then
            print_status "Sample NER results:"
            head -3 "$NER_DIR/predictions.csv" | tee -a "$LOG_FILE"
        fi
    else
        print_error "NER failed"
        exit 1
    fi
}

extract_urls() {
    print_progress "TEST Step 3/5: Extracting URLs..."
    local start_time=$(date +%s)
    
    print_status "Input: $NER_DIR/predictions.csv"
    print_status "Max URLs per paper: $MAX_URLS"
    print_status "Output: $URL_DIR/predictions.csv"
    
    python src/url_extractor.py \
        -o "$URL_DIR" \
        -x "$MAX_URLS" \
        "$NER_DIR/predictions.csv"
    
    if [ $? -eq 0 ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "URL extraction completed (${duration}s)"
        
        local url_papers=$(tail -n +2 "$URL_DIR/predictions.csv" | wc -l)
        print_status "Papers with URLs: $url_papers"
        
        # Show sample URL results
        if [ "$url_papers" -gt 0 ]; then
            print_status "Sample URL results:"
            head -3 "$URL_DIR/predictions.csv" | cut -d',' -f1-3 | tee -a "$LOG_FILE"
        fi
    else
        print_error "URL extraction failed"
        exit 1
    fi
}

process_names() {
    print_progress "TEST Step 4/5: Processing names..."
    local start_time=$(date +%s)
    
    print_status "Input: $URL_DIR/predictions.csv"
    print_status "Output: $NAMES_DIR/predictions.csv"
    
    python src/process_names.py \
        -o "$NAMES_DIR" \
        "$URL_DIR/predictions.csv"
    
    if [ $? -eq 0 ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "Name processing completed (${duration}s)"
        
        local processed_entries=$(tail -n +2 "$NAMES_DIR/predictions.csv" | wc -l)
        print_status "Processed entries: $processed_entries"
        
        # Show sample processed results
        if [ "$processed_entries" -gt 0 ]; then
            print_status "Sample processed names:"
            head -3 "$NAMES_DIR/predictions.csv" | cut -d',' -f1-4 | tee -a "$LOG_FILE"
        fi
    else
        print_error "Name processing failed"
        exit 1
    fi
}

create_final_results() {
    print_progress "TEST Step 5/5: Creating final results..."
    local start_time=$(date +%s)
    
    print_status "Input: $NAMES_DIR/predictions.csv"
    print_status "Output: $FINAL_DIR/biodata_inventory_2022_test.csv"
    
    # Copy processed names as final results
    cp "$NAMES_DIR/predictions.csv" "$FINAL_DIR/biodata_inventory_2022_test.csv"
    
    if [ $? -eq 0 ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "Final results created (${duration}s)"
        
        local final_entries=$(tail -n +2 "$FINAL_DIR/biodata_inventory_2022_test.csv" | wc -l)
        print_status "Final inventory entries: $final_entries"
        
        # Show final results summary
        if [ "$final_entries" -gt 0 ]; then
            print_status "Final results preview:"
            head -3 "$FINAL_DIR/biodata_inventory_2022_test.csv" | tee -a "$LOG_FILE"
        fi
    else
        print_error "Failed to create final results"
        exit 1
    fi
}

print_test_summary() {
    local total_end_time=$(date +%s)
    local total_duration=$((total_end_time - SCRIPT_START_TIME))
    local total_minutes=$((total_duration / 60))
    local total_seconds=$((total_duration % 60))
    
    print_header "TEST RUN COMPLETE"
    
    print_success "Total test time: ${total_minutes}m ${total_seconds}s"
    print_success "Test output: $RUN_OUTPUT_DIR"
    
    print_status "Test results summary:"
    local input_papers=$(($(wc -l < "$INPUT_DATA") - 1))
    local total_predictions=$(tail -n +2 "$CLASSIF_DIR/predictions.csv" 2>/dev/null | wc -l || echo "0")
    local bio_papers=$(tail -n +2 "$CLASSIF_DIR/predicted_positives.csv" 2>/dev/null | wc -l || echo "0")
    local final_results=$(tail -n +2 "$FINAL_DIR/biodata_inventory_2022_test.csv" 2>/dev/null | wc -l || echo "0")
    
    print_status "  Input papers: $input_papers"
    print_status "  Total predictions: $total_predictions"
    print_status "  Bio-resource papers: $bio_papers"
    print_status "  Final inventory: $final_results resources"
    
    print_status "Key test files:"
    print_status "  Final inventory: $FINAL_DIR/biodata_inventory_2022_test.csv"
    print_status "  Processing log: $LOG_FILE"
    print_status "  Test directory: $RUN_OUTPUT_DIR"
    
    if [ "$total_predictions" -eq "$input_papers" ] && [ "$final_results" -eq "$bio_papers" ]; then
        print_success "✅ TEST PASSED - All pipeline steps completed successfully!"
        print_status "The script is ready for full dataset processing."
    else
        print_warning "⚠️  TEST ISSUES DETECTED"
        print_status "Please review the results before running on full dataset."
    fi
}

# Main execution
main() {
    # Create initial log directory for early logging
    mkdir -p "$LOGS_DIR"
    
    print_header "TEST RUN - 2022 INVENTORY RERUN"
    print_status "🧪 TESTING WITH SMALL DATASET (~40 papers)"
    print_status "Start time: $(date '+%Y-%m-%d %H:%M:%S')"
    print_status "Test input: $INPUT_DATA"
    print_status "Test output: $RUN_OUTPUT_DIR"
    print_status "Log file: $LOG_FILE"
    
    # Execute test pipeline
    check_prerequisites
    setup_environment
    
    print_status ""
    print_warning "Starting TEST processing pipeline..."
    print_status ""
    
    # Main processing pipeline
    run_classification
    run_ner
    extract_urls
    process_names
    create_final_results
    
    print_test_summary
    
    deactivate
}

# Run main function
main "$@"