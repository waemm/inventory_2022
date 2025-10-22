#!/bin/bash
# Git Worktree Setup Script for Full Training Pipeline
# Creates an isolated training environment for running full model training
# while allowing continued development in the main repository

set -e  # Exit on any error

# Configuration
MAIN_REPO_PATH="/Users/warren/development/GBC/inventory_2022"
WORKTREE_PATH="/Users/warren/development/GBC-training"
WORKTREE_BRANCH="full-training-run"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}===================================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}===================================================${NC}"
}

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

# Start setup
print_header "GIT WORKTREE SETUP FOR FULL TRAINING"
print_status "Setting up isolated training environment..."

# Check if we're in the right directory
if [ "$(pwd)" != "$MAIN_REPO_PATH" ]; then
    print_status "Changing to main repository directory: $MAIN_REPO_PATH"
    cd "$MAIN_REPO_PATH"
fi

# Verify we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a git repository. Please run this script from the inventory_2022 directory."
    exit 1
fi

# Show current git status
print_status "Current git status:"
git status --short

# Check if worktree path already exists
if [ -d "$WORKTREE_PATH" ]; then
    print_warning "Worktree path $WORKTREE_PATH already exists."
    read -p "Do you want to remove it and create a fresh one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing existing worktree..."
        rm -rf "$WORKTREE_PATH"
        # Also remove the git worktree reference if it exists
        git worktree remove "$WORKTREE_PATH" 2>/dev/null || true
    else
        print_status "Using existing worktree. Verifying setup..."
        if [ ! -d "$WORKTREE_PATH/.git" ]; then
            print_error "Existing directory is not a git worktree. Please remove it manually."
            exit 1
        fi
    fi
fi

# Create worktree if it doesn't exist
if [ ! -d "$WORKTREE_PATH" ]; then
    print_status "Creating git worktree at: $WORKTREE_PATH"
    
    # Create a new branch based on current branch for training
    CURRENT_BRANCH=$(git branch --show-current)
    print_status "Current branch: $CURRENT_BRANCH"
    
    # Delete branch if it exists
    git branch -D "$WORKTREE_BRANCH" 2>/dev/null || true
    
    # Create worktree with new branch
    git worktree add -b "$WORKTREE_BRANCH" "$WORKTREE_PATH" "$CURRENT_BRANCH"
    
    if [ $? -eq 0 ]; then
        print_success "Git worktree created successfully"
    else
        print_error "Failed to create git worktree"
        exit 1
    fi
fi

# Set up the training environment in the worktree
print_status "Setting up training environment in worktree..."
cd "$WORKTREE_PATH"

# Verify critical files exist
critical_files=(
    "src/class_train.py"
    "src/ner_train.py"
    "src/class_data_generator.py"
    "src/ner_data_generator.py"
    "data/manual_classifications.csv"
    "data/manual_ner_extraction.csv"
    "config/train_predict.yml"
    "config/models_info.tsv"
)

print_status "Verifying critical files..."
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "✓ $file"
    else
        print_error "✗ Missing: $file"
        exit 1
    fi
done

# Check data file sizes to ensure they're the full datasets
classif_lines=$(wc -l < "data/manual_classifications.csv")
ner_lines=$(wc -l < "data/manual_ner_extraction.csv")

print_status "Dataset verification:"
print_status "  Classification data: $classif_lines lines"
print_status "  NER data: $ner_lines lines"

if [ "$classif_lines" -lt 1600 ]; then
    print_warning "Classification dataset seems small (expected ~1,634 lines)"
fi

# Create logs directory
mkdir -p logs
print_success "Created logs directory"

# Create backup directory for existing models
mkdir -p model_backups
print_success "Created model_backups directory"

# Check if modern environment exists
if [ -d "biodata_modern_env" ]; then
    print_success "Modern Python environment found"
else
    print_warning "Modern Python environment not found"
    print_status "You may need to create it by running:"
    print_status "  python3.11 -m venv biodata_modern_env"
    print_status "  source biodata_modern_env/bin/activate"
    print_status "  pip install -r requirements_frozen.txt"
fi

# Test environment activation
if [ -d "biodata_modern_env" ]; then
    print_status "Testing environment activation..."
    source biodata_modern_env/bin/activate
    
    # Quick package check
    python -c "
import sys
print(f'Python: {sys.version}')
try:
    import torch; print(f'✓ PyTorch: {torch.__version__}')
except ImportError: print('✗ PyTorch not found')
try:
    import transformers; print(f'✓ Transformers: {transformers.__version__}')
except ImportError: print('✗ Transformers not found')
" 2>/dev/null || print_warning "Environment test had issues"
    
    deactivate
fi

# Create a quick status file
cat > worktree_info.txt << EOF
Git Worktree Training Environment
=================================
Created: $(date)
Main Repo: $MAIN_REPO_PATH
Worktree Path: $WORKTREE_PATH
Branch: $WORKTREE_BRANCH
Base Branch: $CURRENT_BRANCH

To start training:
1. cd $WORKTREE_PATH
2. ./run_full_single_model_training.sh

To monitor from main repo:
1. cd $MAIN_REPO_PATH  
2. ./monitor_training.sh
EOF

print_success "Created worktree_info.txt with setup details"

# Final summary
print_header "WORKTREE SETUP COMPLETE"
print_success "Training environment ready at: $WORKTREE_PATH"
print_success "Branch: $WORKTREE_BRANCH"
print_status ""
print_status "Next steps:"
print_status "1. cd $WORKTREE_PATH"
print_status "2. ./run_full_single_model_training.sh"
print_status ""
print_status "From main repo, you can monitor with:"
print_status "1. cd $MAIN_REPO_PATH"
print_status "2. ./monitor_training.sh"
print_status ""
print_warning "Remember: The training will run in isolation."
print_warning "You can continue development in the main repo without interference."

# Return to main repo
cd "$MAIN_REPO_PATH"