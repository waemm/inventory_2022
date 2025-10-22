#!/bin/bash
# Training Monitoring Script
# Monitor the progress of training running in the git worktree
# Can be run from the main repository while training continues

# Configuration
WORKTREE_PATH="/Users/warren/development/GBC-training"
MAIN_REPO_PATH="/Users/warren/development/GBC/inventory_2022"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  -s, --status     Show current training status (default)"
    echo "  -l, --logs       Show recent log entries"
    echo "  -f, --follow     Follow log file in real-time"
    echo "  -p, --progress   Show detailed progress information"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0               # Show status"
    echo "  $0 --logs        # Show recent logs"
    echo "  $0 --follow      # Follow logs (Ctrl+C to exit)"
}

check_worktree() {
    if [ ! -d "$WORKTREE_PATH" ]; then
        print_error "Worktree not found at: $WORKTREE_PATH"
        print_status "Create it by running: ./setup_training_worktree.sh"
        exit 1
    fi
    
    if [ ! -d "$WORKTREE_PATH/.git" ]; then
        print_error "Invalid worktree (no .git directory)"
        exit 1
    fi
    
    return 0
}

get_latest_log() {
    local log_pattern="$WORKTREE_PATH/logs/full_training_*.log"
    local latest_log=$(ls -t $log_pattern 2>/dev/null | head -n 1)
    echo "$latest_log"
}

show_status() {
    print_header "TRAINING STATUS MONITOR"
    
    # Check if worktree exists
    if [ ! -d "$WORKTREE_PATH" ]; then
        print_error "Training worktree not found"
        print_status "Run ./setup_training_worktree.sh to create it"
        return 1
    fi
    
    print_success "Worktree found at: $WORKTREE_PATH"
    
    # Check if training script exists
    if [ ! -f "$WORKTREE_PATH/run_full_single_model_training.sh" ]; then
        print_warning "Training script not found in worktree"
        return 1
    fi
    
    # Look for active processes
    local training_pid=$(pgrep -f "run_full_single_model_training.sh" 2>/dev/null)
    if [ -n "$training_pid" ]; then
        print_success "Training is RUNNING (PID: $training_pid)"
        
        # Show process info
        local process_time=$(ps -o etime= -p "$training_pid" 2>/dev/null | tr -d ' ')
        print_status "Running time: $process_time"
        
        # Show CPU and memory usage
        local cpu_mem=$(ps -o %cpu,%mem -p "$training_pid" 2>/dev/null | tail -n 1)
        print_status "CPU/Memory: $cpu_mem"
    else
        print_warning "No training process detected"
    fi
    
    # Check for log files
    local latest_log=$(get_latest_log)
    if [ -n "$latest_log" ] && [ -f "$latest_log" ]; then
        print_status "Latest log: $(basename "$latest_log")"
        local log_size=$(du -h "$latest_log" | cut -f1)
        local log_lines=$(wc -l < "$latest_log")
        print_status "Log size: $log_size ($log_lines lines)"
        
        # Show last few entries
        print_status ""
        print_status "Recent log entries:"
        echo -e "${CYAN}$(tail -n 5 "$latest_log")${NC}"
    else
        print_warning "No log files found"
    fi
    
    # Check output directories
    print_status ""
    print_status "Output directories:"
    
    local classif_dir="$WORKTREE_PATH/out/classif_train_full"
    local ner_dir="$WORKTREE_PATH/out/ner_train_full"
    
    if [ -d "$classif_dir" ]; then
        if [ -f "$classif_dir/checkpt.pt" ]; then
            local model_size=$(du -h "$classif_dir/checkpt.pt" | cut -f1)
            print_success "  Classification model: $model_size"
        else
            print_status "  Classification: In progress..."
        fi
    else
        print_status "  Classification: Not started"
    fi
    
    if [ -d "$ner_dir" ]; then
        if [ -f "$ner_dir/checkpt.pt" ]; then
            local model_size=$(du -h "$ner_dir/checkpt.pt" | cut -f1)
            print_success "  NER model: $model_size"
        else
            print_status "  NER: In progress..."
        fi
    else
        print_status "  NER: Not started"
    fi
    
    # Check for completion
    if [ -f "$WORKTREE_PATH/out/classif_train_out/article_classifier.pt" ] && \
       [ -f "$WORKTREE_PATH/out/ner_train_out/named_entity_recognition.pt" ]; then
        print_success ""
        print_success "TRAINING COMPLETED!"
        print_status "Models available at:"
        print_status "  $WORKTREE_PATH/out/classif_train_out/article_classifier.pt"
        print_status "  $WORKTREE_PATH/out/ner_train_out/named_entity_recognition.pt"
    fi
}

show_logs() {
    local latest_log=$(get_latest_log)
    if [ -z "$latest_log" ] || [ ! -f "$latest_log" ]; then
        print_error "No log file found"
        return 1
    fi
    
    print_header "RECENT LOG ENTRIES"
    print_status "Log file: $(basename "$latest_log")"
    print_status ""
    
    # Show last 20 lines with color coding
    tail -n 20 "$latest_log" | while IFS= read -r line; do
        if [[ $line == *"[ERROR]"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ $line == *"[SUCCESS]"* ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ $line == *"[WARNING]"* ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ $line == *"[PROGRESS]"* ]]; then
            echo -e "${CYAN}$line${NC}"
        else
            echo "$line"
        fi
    done
}

follow_logs() {
    local latest_log=$(get_latest_log)
    if [ -z "$latest_log" ] || [ ! -f "$latest_log" ]; then
        print_error "No log file found"
        return 1
    fi
    
    print_header "FOLLOWING LOG FILE (Ctrl+C to exit)"
    print_status "Log file: $(basename "$latest_log")"
    print_status ""
    
    # Follow the log file with color coding
    tail -f "$latest_log" | while IFS= read -r line; do
        if [[ $line == *"[ERROR]"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ $line == *"[SUCCESS]"* ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ $line == *"[WARNING]"* ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ $line == *"[PROGRESS]"* ]]; then
            echo -e "${CYAN}$line${NC}"
        else
            echo "$line"
        fi
    done
}

show_progress() {
    print_header "DETAILED PROGRESS INFORMATION"
    
    local latest_log=$(get_latest_log)
    if [ -z "$latest_log" ] || [ ! -f "$latest_log" ]; then
        print_error "No log file found"
        return 1
    fi
    
    # Extract progress information from log
    print_status "Training pipeline steps:"
    
    if grep -q "Step 1/6: Splitting classification data" "$latest_log"; then
        if grep -q "Classification data splits generated" "$latest_log"; then
            print_success "  ✓ Step 1: Classification data split"
        else
            print_status "  ⏳ Step 1: Splitting classification data..."
        fi
    else
        print_status "  ⏸ Step 1: Split classification data"
    fi
    
    if grep -q "Step 2/6: Splitting NER data" "$latest_log"; then
        if grep -q "NER data splits generated" "$latest_log"; then
            print_success "  ✓ Step 2: NER data split"
        else
            print_status "  ⏳ Step 2: Splitting NER data..."
        fi
    else
        print_status "  ⏸ Step 2: Split NER data"
    fi
    
    if grep -q "Step 3/6: Training classification model" "$latest_log"; then
        if grep -q "Classification training completed" "$latest_log"; then
            local duration=$(grep "Classification training completed" "$latest_log" | tail -n 1 | sed 's/.*(\(.*\))/\1/')
            print_success "  ✓ Step 3: Classification training ($duration)"
        else
            print_status "  ⏳ Step 3: Training classification model..."
        fi
    else
        print_status "  ⏸ Step 3: Train classification model"
    fi
    
    if grep -q "Step 4/6: Training NER model" "$latest_log"; then
        if grep -q "NER training completed" "$latest_log"; then
            local duration=$(grep "NER training completed" "$latest_log" | tail -n 1 | sed 's/.*(\(.*\))/\1/')
            print_success "  ✓ Step 4: NER training ($duration)"
        else
            print_status "  ⏳ Step 4: Training NER model..."
        fi
    else
        print_status "  ⏸ Step 4: Train NER model"
    fi
    
    if grep -q "Step 5/6: Evaluating models" "$latest_log"; then
        if grep -q "Model evaluation completed" "$latest_log"; then
            local duration=$(grep "Model evaluation completed" "$latest_log" | tail -n 1 | sed 's/.*(\(.*\))/\1/')
            print_success "  ✓ Step 5: Model evaluation ($duration)"
        else
            print_status "  ⏳ Step 5: Evaluating models..."
        fi
    else
        print_status "  ⏸ Step 5: Evaluate models"
    fi
    
    if grep -q "Step 6/6: Finalizing trained models" "$latest_log"; then
        if grep -q "Model references updated" "$latest_log"; then
            print_success "  ✓ Step 6: Finalize models"
        else
            print_status "  ⏳ Step 6: Finalizing models..."
        fi
    else
        print_status "  ⏸ Step 6: Finalize models"
    fi
    
    # Show timing information
    if grep -q "Estimated training time:" "$latest_log"; then
        print_status ""
        print_status "Time estimates:"
        grep "Estimated training time:" -A 4 "$latest_log" | tail -n 4 | while read line; do
            print_status "  $line"
        done
    fi
    
    # Show disk usage
    if [ -d "$WORKTREE_PATH/out" ]; then
        print_status ""
        local disk_usage=$(du -sh "$WORKTREE_PATH/out" | cut -f1)
        print_status "Disk usage: $disk_usage (output directory)"
    fi
}

# Main execution
main() {
    case "${1:-}" in
        -l|--logs)
            check_worktree && show_logs
            ;;
        -f|--follow)
            check_worktree && follow_logs
            ;;
        -p|--progress)
            check_worktree && show_progress
            ;;
        -h|--help)
            show_usage
            ;;
        -s|--status|"")
            show_status
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"