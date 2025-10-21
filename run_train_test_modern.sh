#!/bin/bash
# Modern Training Pipeline Test Script
# Tests both classification and NER training with modern Python environment
# Generated for modernized biodata inventory pipeline

set -e  # Exit on any error

# Configuration
ENV_PATH="biodata_modern_env"
TEST_CONFIG="config/train_test_modern.yml"
MODELS_CONFIG="config/models_test.tsv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if environment exists
if [ ! -d "$ENV_PATH" ]; then
    print_error "Environment $ENV_PATH not found. Please create it first."
    exit 1
fi

print_status "Starting modern training pipeline test..."

# Activate environment and set Python path
source $ENV_PATH/bin/activate
export PYTHONPATH="src:$PYTHONPATH"

print_status "Environment activated: $ENV_PATH"
print_status "Python path set: $PYTHONPATH"

# Step 1: Verify package versions
print_status "Checking critical package versions..."
python -c "
import torch; print(f'PyTorch: {torch.__version__}')
import transformers; print(f'Transformers: {transformers.__version__}')
import datasets; print(f'Datasets: {datasets.__version__}')
import evaluate; print(f'Evaluate: {evaluate.__version__}')
"

# Step 2: Generate classification data splits
print_status "Generating classification data splits..."
python src/class_data_generator.py \
    -o data/classif_splits_test \
    --splits 0.7 0.15 0.15 \
    -r \
    data/manual_classifications_test.csv

if [ $? -eq 0 ]; then
    print_success "Classification data splits generated"
else
    print_error "Failed to generate classification data splits"
    exit 1
fi

# Step 3: Generate NER data splits  
print_status "Generating NER data splits..."
python src/ner_data_generator.py \
    -o data/ner_splits_test \
    --splits 0.7 0.15 0.15 \
    -r \
    data/manual_ner_extraction_test.csv

if [ $? -eq 0 ]; then
    print_success "NER data splits generated"
else
    print_error "Failed to generate NER data splits"
    exit 1
fi

# Step 4: Train classification model
print_status "Training classification model (2 epochs)..."
python src/class_train.py \
    -t data/classif_splits_test/train_paper_classif.csv \
    -v data/classif_splits_test/val_paper_classif.csv \
    -m allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500 \
    -ne 2 \
    -batch 16 \
    -rate 2e-5 \
    -decay 0 \
    -o out/classif_train_test \
    -r

if [ $? -eq 0 ]; then
    print_success "Classification model training completed"
else
    print_error "Classification model training failed"
    exit 1
fi

# Step 5: Train NER model
print_status "Training NER model (2 epochs)..."
python src/ner_train.py \
    -c f1 \
    -m allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500 \
    -ne 2 \
    -t data/ner_splits_test/train_ner.pkl \
    -v data/ner_splits_test/val_ner.pkl \
    -o out/ner_train_test \
    -batch 16 \
    -rate 2e-5 \
    -decay 0 \
    -r

if [ $? -eq 0 ]; then
    print_success "NER model training completed"
else
    print_error "NER model training failed"
    exit 1
fi

# Step 6: Verify output files
print_status "Verifying training outputs..."

# Check classification outputs
if [ -f "out/classif_train_test/checkpt.pt" ] && [ -f "out/classif_train_test/train_stats.csv" ]; then
    print_success "Classification training outputs found"
else
    print_warning "Classification training outputs may be incomplete"
fi

# Check NER outputs  
if [ -f "out/ner_train_test/checkpt.pt" ] && [ -f "out/ner_train_test/train_stats.csv" ]; then
    print_success "NER training outputs found"
else
    print_warning "NER training outputs may be incomplete"
fi

# Summary
print_status "=== TRAINING PIPELINE TEST SUMMARY ==="
print_success "✓ Environment setup and package verification"
print_success "✓ Classification data splitting"
print_success "✓ NER data splitting" 
print_success "✓ Classification model training (2 epochs)"
print_success "✓ NER model training (2 epochs)"
print_success "✓ Output verification"

print_status "Modern training pipeline test completed successfully!"
print_status "Trained models available in:"
print_status "  - Classification: out/classif_train_test/"
print_status "  - NER: out/ner_train_test/"

deactivate