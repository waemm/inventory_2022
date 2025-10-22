#!/bin/bash
# Full Production Training Script
# Trains biomed_roberta_rct500 model with full datasets and production parameters
# Runs directly in the current repository with comprehensive logging

set -e  # Exit on any error

# Configuration
MODEL_NAME="biomed_roberta_rct500"
HF_MODEL="allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500"
ENV_PATH="biodata_modern_env"
EPOCHS=10
BATCH_SIZE=16
LEARNING_RATE="2e-5"
WEIGHT_DECAY=0

# Directories
CLASSIF_SPLITS_DIR="data/classif_splits_full"
NER_SPLITS_DIR="data/ner_splits_full"
CLASSIF_OUTPUT_DIR="out/classif_train_full"
NER_OUTPUT_DIR="out/ner_train_full"
LOG_DIR="logs"
BACKUP_DIR="model_backups"

# Data files
CLASSIF_DATA="data/manual_classifications.csv"
NER_DATA="data/manual_ner_extraction.csv"

# Create log file with timestamp
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_FILE="$LOG_DIR/full_training_${TIMESTAMP}.log"

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
    print_status "Checking prerequisites..."
    
    # Check environment
    if [ ! -d "$ENV_PATH" ]; then
        print_error "Environment $ENV_PATH not found"
        print_status "Please create it with: python3.11 -m venv $ENV_PATH"
        exit 1
    fi
    
    # Check data files
    if [ ! -f "$CLASSIF_DATA" ]; then
        print_error "Classification data not found: $CLASSIF_DATA"
        exit 1
    fi
    
    if [ ! -f "$NER_DATA" ]; then
        print_error "NER data not found: $NER_DATA"
        exit 1
    fi
    
    # Check data sizes
    local classif_lines=$(wc -l < "$CLASSIF_DATA")
    local ner_lines=$(wc -l < "$NER_DATA")
    
    print_status "Dataset sizes:"
    print_status "  Classification: $classif_lines lines"
    print_status "  NER: $ner_lines lines"
    
    if [ "$classif_lines" -lt 1600 ]; then
        print_warning "Classification dataset smaller than expected (expected ~1,634)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success "Prerequisites check passed"
}

setup_environment() {
    print_status "Setting up environment..."
    
    # Create directories
    mkdir -p "$LOG_DIR" "$BACKUP_DIR"
    mkdir -p "$CLASSIF_SPLITS_DIR" "$NER_SPLITS_DIR"
    mkdir -p "$CLASSIF_OUTPUT_DIR" "$NER_OUTPUT_DIR"
    
    # Activate environment
    source "$ENV_PATH/bin/activate"
    export PYTHONPATH="src:$PYTHONPATH"
    
    print_status "Environment activated: $ENV_PATH"
    print_status "Python path set: $PYTHONPATH"
    
    # Verify packages
    print_status "Verifying package versions..."
    python -c "
import torch, transformers, datasets, evaluate
print(f'PyTorch: {torch.__version__}')
print(f'Transformers: {transformers.__version__}')
print(f'Datasets: {datasets.__version__}')
print(f'Evaluate: {evaluate.__version__}')
" | tee -a "$LOG_FILE"
    
    print_success "Environment setup complete"
}

backup_existing_models() {
    print_status "Checking for existing models to backup..."
    
    local backup_created=false
    
    # Check classification models
    if [ -f "out/classif_train_out/article_classifier.pt" ]; then
        local backup_file="$BACKUP_DIR/article_classifier_backup_${TIMESTAMP}.pt"
        cp "out/classif_train_out/article_classifier.pt" "$backup_file"
        print_success "Backed up classification model to: $backup_file"
        backup_created=true
    fi
    
    # Check NER models
    if [ -f "out/ner_train_out/named_entity_recognition.pt" ]; then
        local backup_file="$BACKUP_DIR/named_entity_recognition_backup_${TIMESTAMP}.pt"
        cp "out/ner_train_out/named_entity_recognition.pt" "$backup_file"
        print_success "Backed up NER model to: $backup_file"
        backup_created=true
    fi
    
    # Check for existing full training outputs
    if [ -d "$CLASSIF_OUTPUT_DIR" ] && [ "$(ls -A $CLASSIF_OUTPUT_DIR)" ]; then
        print_warning "Previous full training outputs found in $CLASSIF_OUTPUT_DIR"
        read -p "Remove previous outputs? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$CLASSIF_OUTPUT_DIR"/*
            print_status "Removed previous classification training outputs"
        fi
    fi
    
    if [ -d "$NER_OUTPUT_DIR" ] && [ "$(ls -A $NER_OUTPUT_DIR)" ]; then
        print_warning "Previous full training outputs found in $NER_OUTPUT_DIR"
        read -p "Remove previous outputs? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$NER_OUTPUT_DIR"/*
            print_status "Removed previous NER training outputs"
        fi
    fi
    
    if [ "$backup_created" = true ]; then
        print_success "Existing models backed up successfully"
    else
        print_status "No existing models found to backup"
    fi
}

estimate_training_time() {
    print_status "Estimating training time..."
    
    local classif_lines=$(wc -l < "$CLASSIF_DATA")
    local ner_lines=$(wc -l < "$NER_DATA")
    
    # Rough estimates based on dataset size and epochs
    local classif_minutes=$((classif_lines * EPOCHS / 40))  # ~40 samples per minute
    local ner_minutes=$((ner_lines * EPOCHS / 60))          # ~60 samples per minute
    local total_minutes=$((classif_minutes + ner_minutes + 20)) # +20 for overhead
    
    local hours=$((total_minutes / 60))
    local mins=$((total_minutes % 60))
    
    print_status "Estimated training time:"
    print_status "  Classification: ~${classif_minutes} minutes"
    print_status "  NER: ~${ner_minutes} minutes"
    print_status "  Total: ~${hours}h ${mins}m"
    
    local end_time=$(date -d "+${total_minutes} minutes" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || \
                     date -v "+${total_minutes}M" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || \
                     echo "Unable to calculate")
    print_status "  Estimated completion: $end_time"
    
    print_status ""
    print_warning "This will run for approximately ${hours}h ${mins}m"
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Training cancelled by user"
        exit 0
    fi
}

split_classification_data() {
    print_progress "Step 1/6: Splitting classification data..."
    local start_time=$(date +%s)
    
    python src/class_data_generator.py \
        -o "$CLASSIF_SPLITS_DIR" \
        --splits 0.7 0.15 0.15 \
        -r \
        "$CLASSIF_DATA"
    
    if [ $? -eq 0 ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "Classification data splits generated (${duration}s)"
        
        # Verify splits
        local train_lines=$(wc -l < "$CLASSIF_SPLITS_DIR/train_paper_classif.csv")
        local val_lines=$(wc -l < "$CLASSIF_SPLITS_DIR/val_paper_classif.csv")
        local test_lines=$(wc -l < "$CLASSIF_SPLITS_DIR/test_paper_classif.csv")
        
        print_status "Split sizes: Train=$train_lines, Val=$val_lines, Test=$test_lines"
    else
        print_error "Failed to generate classification data splits"
        exit 1
    fi
}

split_ner_data() {
    print_progress "Step 2/6: Splitting NER data..."
    local start_time=$(date +%s)
    
    python src/ner_data_generator.py \
        -o "$NER_SPLITS_DIR" \
        --splits 0.7 0.15 0.15 \
        -r \
        "$NER_DATA"
    
    if [ $? -eq 0 ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "NER data splits generated (${duration}s)"
        
        # Verify splits
        local train_lines=$(wc -l < "$NER_SPLITS_DIR/train_ner.csv")
        local val_lines=$(wc -l < "$NER_SPLITS_DIR/val_ner.csv")
        local test_lines=$(wc -l < "$NER_SPLITS_DIR/test_ner.csv")
        
        print_status "Split sizes: Train=$train_lines, Val=$val_lines, Test=$test_lines"
    else
        print_error "Failed to generate NER data splits"
        exit 1
    fi
}

train_classification_model() {
    print_progress "Step 3/6: Training classification model ($EPOCHS epochs)..."
    local start_time=$(date +%s)
    
    print_status "Model: $MODEL_NAME ($HF_MODEL)"
    print_status "Epochs: $EPOCHS, Batch size: $BATCH_SIZE, Learning rate: $LEARNING_RATE"
    
    python src/class_train.py \
        -t "$CLASSIF_SPLITS_DIR/train_paper_classif.csv" \
        -v "$CLASSIF_SPLITS_DIR/val_paper_classif.csv" \
        -m "$HF_MODEL" \
        -ne $EPOCHS \
        -batch $BATCH_SIZE \
        -rate $LEARNING_RATE \
        -decay $WEIGHT_DECAY \
        -o "$CLASSIF_OUTPUT_DIR" \
        -r
    
    if [ $? -eq 0 ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        print_success "Classification training completed (${minutes}m ${seconds}s)"
        
        # Check output files
        if [ -f "$CLASSIF_OUTPUT_DIR/checkpt.pt" ]; then
            local model_size=$(du -h "$CLASSIF_OUTPUT_DIR/checkpt.pt" | cut -f1)
            print_status "Model saved: $CLASSIF_OUTPUT_DIR/checkpt.pt ($model_size)"
        fi
    else
        print_error "Classification training failed"
        exit 1
    fi
}

train_ner_model() {
    print_progress "Step 4/6: Training NER model ($EPOCHS epochs)..."
    local start_time=$(date +%s)
    
    print_status "Model: $MODEL_NAME ($HF_MODEL)"
    print_status "Epochs: $EPOCHS, Batch size: $BATCH_SIZE, Learning rate: $LEARNING_RATE"
    
    python src/ner_train.py \
        -c f1 \
        -m "$HF_MODEL" \
        -ne $EPOCHS \
        -t "$NER_SPLITS_DIR/train_ner.pkl" \
        -v "$NER_SPLITS_DIR/val_ner.pkl" \
        -o "$NER_OUTPUT_DIR" \
        -batch $BATCH_SIZE \
        -rate $LEARNING_RATE \
        -decay $WEIGHT_DECAY \
        -r
    
    if [ $? -eq 0 ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        print_success "NER training completed (${minutes}m ${seconds}s)"
        
        # Check output files
        if [ -f "$NER_OUTPUT_DIR/checkpt.pt" ]; then
            local model_size=$(du -h "$NER_OUTPUT_DIR/checkpt.pt" | cut -f1)
            print_status "Model saved: $NER_OUTPUT_DIR/checkpt.pt ($model_size)"
        fi
    else
        print_error "NER training failed"
        exit 1
    fi
}

evaluate_models() {
    print_progress "Step 5/6: Evaluating models on test sets..."
    local start_time=$(date +%s)
    
    # Evaluate classification model
    print_status "Evaluating classification model..."
    python src/class_final_eval.py \
        -o "$CLASSIF_OUTPUT_DIR/test_evaluation" \
        -t "$CLASSIF_SPLITS_DIR/test_paper_classif.csv" \
        -c "$CLASSIF_OUTPUT_DIR/checkpt.pt"
    
    # Evaluate NER model
    print_status "Evaluating NER model..."
    python src/ner_final_eval.py \
        -o "$NER_OUTPUT_DIR/test_evaluation" \
        -t "$NER_SPLITS_DIR/test_ner.pkl" \
        -c "$NER_OUTPUT_DIR/checkpt.pt"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    print_success "Model evaluation completed (${duration}s)"
}

finalize_models() {
    print_progress "Step 6/7: Finalizing trained models..."
    
    # Copy models to standard locations
    mkdir -p "out/classif_train_out" "out/ner_train_out"
    
    if [ -f "$CLASSIF_OUTPUT_DIR/checkpt.pt" ]; then
        cp "$CLASSIF_OUTPUT_DIR/checkpt.pt" "out/classif_train_out/article_classifier.pt"
        print_success "Classification model copied to: out/classif_train_out/article_classifier.pt"
    fi
    
    if [ -f "$NER_OUTPUT_DIR/checkpt.pt" ]; then
        cp "$NER_OUTPUT_DIR/checkpt.pt" "out/ner_train_out/named_entity_recognition.pt"
        print_success "NER model copied to: out/ner_train_out/named_entity_recognition.pt"
    fi
    
    # Create best model references
    mkdir -p "out/classif_train_out/best" "out/ner_train_out/best"
    echo "out/classif_train_out/article_classifier.pt" > "out/classif_train_out/best/best_checkpt.txt"
    echo "out/ner_train_out/named_entity_recognition.pt" > "out/ner_train_out/best/best_checkpt.txt"
    
    print_success "Model references updated"
}

archive_models() {
    print_progress "Step 7/7: Archiving trained models..."
    local start_time=$(date +%s)
    
    # Create archive directory with date
    local archive_date=$(date '+%Y-%m-%d')
    local archive_dir="trained_models_25/${archive_date}_full_production_training"
    
    # Handle existing archive for same date
    local counter=1
    local base_archive_dir="$archive_dir"
    while [ -d "$archive_dir" ]; do
        archive_dir="${base_archive_dir}_run${counter}"
        counter=$((counter + 1))
    done
    
    mkdir -p "$archive_dir"
    print_status "Creating archive: $archive_dir"
    
    # Archive models
    if [ -f "$CLASSIF_OUTPUT_DIR/checkpt.pt" ]; then
        cp "$CLASSIF_OUTPUT_DIR/checkpt.pt" "$archive_dir/classification_model.pt"
        print_success "Archived classification model"
    fi
    
    if [ -f "$NER_OUTPUT_DIR/checkpt.pt" ]; then
        cp "$NER_OUTPUT_DIR/checkpt.pt" "$archive_dir/ner_model.pt"
        print_success "Archived NER model"
    fi
    
    # Archive training statistics
    if [ -f "$CLASSIF_OUTPUT_DIR/train_stats.csv" ]; then
        cp "$CLASSIF_OUTPUT_DIR/train_stats.csv" "$archive_dir/classification_training_stats.csv"
    fi
    
    if [ -f "$NER_OUTPUT_DIR/train_stats.csv" ]; then
        cp "$NER_OUTPUT_DIR/train_stats.csv" "$archive_dir/ner_training_stats.csv"
    fi
    
    # Archive evaluation results
    if [ -d "$CLASSIF_OUTPUT_DIR/test_evaluation" ]; then
        cp -r "$CLASSIF_OUTPUT_DIR/test_evaluation" "$archive_dir/classification_test_evaluation"
    fi
    
    if [ -d "$NER_OUTPUT_DIR/test_evaluation" ]; then
        cp -r "$NER_OUTPUT_DIR/test_evaluation" "$archive_dir/ner_test_evaluation"
    fi
    
    # Archive training log
    if [ -f "$LOG_FILE" ]; then
        cp "$LOG_FILE" "$archive_dir/training_log.log"
    fi
    
    # Create archive documentation
    cat > "$archive_dir/README.md" << EOF
# Training Run: $(date '+%B %d, %Y') - Full Production Training

**Training Date**: $(date '+%Y-%m-%d')  
**Training Duration**: Auto-generated during training  
**Status**: ✅ **COMPLETED SUCCESSFULLY**  
**Training Type**: Full Production Training with Complete Datasets

---

## Model Information

### Classification Model
- **File**: \`classification_model.pt\`
- **Model Architecture**: RobertaForSequenceClassification
- **Base Model**: \`$HF_MODEL\`
- **Task**: Binary classification (bio-resource vs non-bio-resource papers)

### NER Model  
- **File**: \`ner_model.pt\`
- **Model Architecture**: RobertaForTokenClassification
- **Base Model**: \`$HF_MODEL\`
- **Task**: Named Entity Recognition (resource name extraction)

---

## Training Configuration

\`\`\`yaml
Model Name: $MODEL_NAME
HuggingFace Model: $HF_MODEL
Epochs: $EPOCHS
Batch Size: $BATCH_SIZE
Learning Rate: $LEARNING_RATE
Weight Decay: $WEIGHT_DECAY
Optimizer: AdamW
\`\`\`

---

## Files in This Archive

### Core Model Files
- **\`classification_model.pt\`** - Trained classification model
- **\`ner_model.pt\`** - Trained NER model

### Training Statistics
- **\`classification_training_stats.csv\`** - Epoch-by-epoch training metrics for classification
- **\`ner_training_stats.csv\`** - Epoch-by-epoch training metrics for NER

### Evaluation Results  
- **\`classification_test_evaluation/\`** - Test set evaluation for classification model
- **\`ner_test_evaluation/\`** - Test set evaluation for NER model

### Training Log
- **\`training_log.log\`** - Complete training log with timestamps and progress

### Documentation
- **\`README.md\`** - This documentation file

---

## Usage Instructions

### Loading Models
\`\`\`python
import torch

# Load classification model
classif_model = torch.load('classification_model.pt', map_location='cpu')

# Load NER model  
ner_model = torch.load('ner_model.pt', map_location='cpu')
\`\`\`

### Integration with Pipeline
These models can be directly used with the existing prediction pipeline:
- Copy \`classification_model.pt\` to \`out/classif_train_out/article_classifier.pt\`
- Copy \`ner_model.pt\` to \`out/ner_train_out/named_entity_recognition.pt\`

---

**Archive Created**: $(date '+%Y-%m-%d %H:%M:%S')  
**Training Script**: run_full_training.sh  
**Archive Location**: $archive_dir
EOF
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    print_success "Models archived successfully (${duration}s)"
    print_status "Archive location: $archive_dir"
    
    # Update the master index
    update_archive_index "$archive_dir"
}

update_archive_index() {
    local new_archive="$1"
    local index_file="trained_models_25/README.md"
    local archive_name=$(basename "$new_archive")
    
    # Create master index if it doesn't exist
    if [ ! -f "$index_file" ]; then
        cat > "$index_file" << 'EOF'
# Trained Models Archive - 2025

This directory contains archived trained models for the biodata inventory ML pipeline, organized by training date and run type.

## Training Runs

EOF
    fi
    
    # Add new archive to index (simple append - could be enhanced with proper parsing)
    local date_part=$(echo "$archive_name" | cut -d'_' -f1)
    cat >> "$index_file" << EOF

### $archive_name
**Date**: $date_part  
**Type**: Full Production Training  
**Status**: ✅ Complete  
**Description**: Complete training on full datasets with $EPOCHS epochs  
**Archive**: $new_archive/

EOF
    
    print_status "Updated archive index: $index_file"
}

print_summary() {
    local total_end_time=$(date +%s)
    local total_duration=$((total_end_time - SCRIPT_START_TIME))
    local total_hours=$((total_duration / 3600))
    local total_minutes=$(((total_duration % 3600) / 60))
    local total_seconds=$((total_duration % 60))
    
    print_header "TRAINING PIPELINE COMPLETE"
    print_success "Total training time: ${total_hours}h ${total_minutes}m ${total_seconds}s"
    print_success "Log file: $LOG_FILE"
    
    print_status "Trained models:"
    print_status "  Classification: out/classif_train_out/article_classifier.pt"
    print_status "  NER: out/ner_train_out/named_entity_recognition.pt"
    
    print_status "Training outputs:"
    print_status "  Classification: $CLASSIF_OUTPUT_DIR/"
    print_status "  NER: $NER_OUTPUT_DIR/"
    
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR 2>/dev/null)" ]; then
        print_status "Backup models: $BACKUP_DIR/"
    fi
    
    print_status "Models are ready for production use!"
}

# Main execution
main() {
    SCRIPT_START_TIME=$(date +%s)
    
    # Create log directory and start logging
    mkdir -p "$LOG_DIR"
    
    print_header "FULL PRODUCTION TRAINING PIPELINE"
    print_status "Model: $MODEL_NAME"
    print_status "HuggingFace Model: $HF_MODEL"
    print_status "Log file: $LOG_FILE"
    
    # Execute pipeline steps
    check_prerequisites
    setup_environment
    backup_existing_models
    estimate_training_time
    
    print_status ""
    print_warning "Starting training pipeline..."
    print_status ""
    
    # Main training pipeline
    split_classification_data
    split_ner_data
    train_classification_model
    train_ner_model
    evaluate_models
    finalize_models
    archive_models
    
    print_summary
    
    deactivate
}

# Run main function
main "$@"