#!/bin/bash
# Training Launcher Script
# Launches the full training pipeline in the worktree environment

WORKTREE_PATH="/Users/warren/development/GBC-training"
SCRIPT_PATH="$WORKTREE_PATH/run_full_single_model_training.sh"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}[LAUNCHER]${NC} Starting full training pipeline..."

# Check if worktree exists
if [ ! -d "$WORKTREE_PATH" ]; then
    echo -e "${RED}[ERROR]${NC} Worktree not found. Run ./setup_training_worktree.sh first"
    exit 1
fi

# Copy the training script if needed
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${BLUE}[LAUNCHER]${NC} Copying training script to worktree..."
    cp run_full_single_model_training.sh "$SCRIPT_PATH"
    chmod +x "$SCRIPT_PATH"
fi

# Launch training in worktree
echo -e "${GREEN}[LAUNCHER]${NC} Launching training in: $WORKTREE_PATH"
echo -e "${BLUE}[LAUNCHER]${NC} You can monitor progress with: ./monitor_training.sh"
echo ""

# Execute the training script in the worktree directory
(cd "$WORKTREE_PATH" && ./run_full_single_model_training.sh)