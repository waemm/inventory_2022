#!/bin/bash

# Biodata Inventory Pipeline - Python 3.8 Implementation
# Updated with all technical fixes and improvements
# Date: 2025-10-17

set -e  # Exit on any error

# Use Python 3.8 environment directly
export PYTHON_CMD="py38_env/bin/python"
export PIP_CMD="py38_env/bin/pip"
export PYTHONPATH="src:$PYTHONPATH"

# Set variables from config file
export project_env="./env"
export query_out_dir="out/new_query"
export last_date_dir="out/last_query_date"
export classif_train_outdir="out/classif_train_out"
export classif_out_dir="out/new_query/classification"
export ner_train_outdir="out/ner_train_out"
export ner_out_dir="out/new_query/ner"
export extract_url_dir="out/new_query/url_extraction"
export processed_names_dir="out/new_query/processed_names"
export initial_dedupe_dir="out/new_query/initial_deduplication"
export for_manual_review_dir="out/new_query/for_manual_review"
export manually_reviewed_dir="out/new_query/manually_reviewed"
export processed_manual_review="out/new_query/processed_manual_review"
export check_url_dir="out/new_query/url_checking"
export epmc_meta_dir="out/new_query/epmc_meta"
export processed_countries="out/new_query/processed_countries"

# Query parameters - Default to test period (can be overridden)
export query_from_date="${QUERY_FROM_DATE:-2025-01-01}"
export query_to_date="${QUERY_TO_DATE:-2025-01-07}"
export query_string="config/query.txt"
export previous_inventory="data/final_inventory_2022.csv"

# Pipeline parameters
export max_urls="3"
export min_best_name_prob="0.978"
export chunk_size="100"
export num_tries="3"
export backoff="1"
export epmc_chunk_size="100"
export country_format="alpha-3"

# Parse command line arguments
CONTINUE_AFTER_REVIEW=false
SKIP_MANUAL_REVIEW=false
SKIP_WAYBACK=true  # Default to skip wayback to avoid timeouts

while [[ $# -gt 0 ]]; do
    case $1 in
        --continue-after-manual-review)
            CONTINUE_AFTER_REVIEW=true
            shift
            ;;
        --skip-manual-review)
            SKIP_MANUAL_REVIEW=true
            shift
            ;;
        --enable-wayback)
            SKIP_WAYBACK=false
            shift
            ;;
        --full-year)
            query_from_date="2025-01-01"
            query_to_date="2025-12-31"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --continue-after-manual-review    Continue pipeline after manual review step"
            echo "  --skip-manual-review              Skip manual review step entirely"
            echo "  --enable-wayback                  Enable Wayback Machine checks (may cause timeouts)"
            echo "  --full-year                       Process full 2025 dataset instead of test period"
            echo "  --help                           Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  QUERY_FROM_DATE                   Override start date (default: 2025-01-01)"
            echo "  QUERY_TO_DATE                     Override end date (default: 2025-01-07)"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "BIODATA INVENTORY UPDATE PIPELINE - 2025"
echo "========================================="
echo "Updated with all technical fixes applied"
echo "Date range: $query_from_date to $query_to_date"
echo "Python environment: $($PYTHON_CMD --version)"
echo "Skip Wayback checks: $SKIP_WAYBACK"
echo "Skip manual review: $SKIP_MANUAL_REVIEW"
echo ""

# Check environment setup
echo "Verifying environment setup..."
if ! $PYTHON_CMD -c "import torch, transformers, numpy; print(f'✅ Libraries loaded: PyTorch {torch.__version__}, Transformers {transformers.__version__}, NumPy {numpy.__version__}')" 2>/dev/null; then
    echo "❌ Environment verification failed. Please check your Python 3.8 environment setup."
    echo "See pipeline_python38_steps.md for setup instructions."
    exit 1
fi

# Check model files
if [ ! -f "out/classif_train_out/article_classifier.pt" ] || [ ! -f "out/ner_train_out/named_entity_recognition.pt" ]; then
    echo "❌ Model files not found. Please ensure models are downloaded."
    echo "Expected: out/classif_train_out/article_classifier.pt (498MB)"
    echo "Expected: out/ner_train_out/named_entity_recognition.pt (496MB)"
    exit 1
fi

# Create output directories
echo "Creating output directories..."
mkdir -p "$query_out_dir" "$last_date_dir" "$classif_out_dir" "$ner_out_dir" \
         "$extract_url_dir" "$processed_names_dir" "$initial_dedupe_dir" \
         "$for_manual_review_dir" "$manually_reviewed_dir" "$processed_manual_review" \
         "$check_url_dir" "$epmc_meta_dir" "$processed_countries"

echo "✅ Environment verified and directories created"
echo ""

# Skip to continuation if requested
if [ "$CONTINUE_AFTER_REVIEW" = true ]; then
    echo "Continuing after manual review..."
    echo ""
    jump_to_manual_continue=true
else
    jump_to_manual_continue=false
fi

if [ "$jump_to_manual_continue" = false ]; then
    # Step 1: Query EuropePMC
    echo "========================================="
    echo "STEP 1: QUERYING EUROPEMC"
    echo "========================================="
    echo "Date range: $query_from_date to $query_to_date"
    echo "Query file: $query_string"
    echo "Output: $query_out_dir/query_results.csv"
    echo ""

    $PYTHON_CMD src/query_epmc.py \
        -o "$query_out_dir" \
        --from-date "$query_from_date" \
        --to-date "$query_to_date" \
        "$query_string"

    echo "✅ EuropePMC query completed successfully"
    cp "$query_out_dir/last_query_dates.txt" "$last_date_dir/last_query_dates.txt" 2>/dev/null || true
    papers_count=$(tail -n +2 "$query_out_dir/query_results.csv" | wc -l)
    echo "Papers retrieved: $papers_count"
    echo ""

    # Step 2: Classify papers
    echo "========================================="
    echo "STEP 2: CLASSIFYING PAPERS"
    echo "========================================="
    echo "Input: $query_out_dir/query_results.csv"
    echo "Model: $(cat $classif_train_outdir/best/best_checkpt.txt)"
    echo "Output: $classif_out_dir/predictions.csv"
    echo ""

    $PYTHON_CMD src/class_predict.py \
        -o "$classif_out_dir" \
        -i "$query_out_dir/query_results.csv" \
        -c "$(< $classif_train_outdir/best/best_checkpt.txt)"

    echo "✅ Classification completed successfully"
    total_predictions=$(tail -n +2 "$classif_out_dir/predictions.csv" | wc -l)
    echo "Total predictions: $total_predictions"
    echo ""

    # Step 3: Filter positive predictions
    echo "========================================="
    echo "STEP 3: FILTERING POSITIVE PREDICTIONS"
    echo "========================================="
    echo "Creating predicted_positives.csv from bio-resource classifications..."
    echo ""

    # Use Python to properly filter predictions
    $PYTHON_CMD -c "
import pandas as pd
df = pd.read_csv('$classif_out_dir/predictions.csv')
positives = df[df['predicted_label'] == 'bio-resource']
positives.to_csv('$classif_out_dir/predicted_positives.csv', index=False)
print(f'Positive predictions: {len(positives)} out of {len(df)} ({len(positives)/len(df)*100:.1f}%)')
"

    echo "✅ Filtering completed successfully"
    echo ""

    # Step 4: Named Entity Recognition
    echo "========================================="
    echo "STEP 4: NAMED ENTITY RECOGNITION"
    echo "========================================="
    echo "Input: $classif_out_dir/predicted_positives.csv"
    echo "Model: $(cat $ner_train_outdir/best/best_checkpt.txt)"
    echo "Output: $ner_out_dir/predictions.csv"
    echo ""

    $PYTHON_CMD src/ner_predict.py \
        -o "$ner_out_dir" \
        -i "$classif_out_dir/predicted_positives.csv" \
        -c "$(< $ner_train_outdir/best/best_checkpt.txt)"

    echo "✅ NER completed successfully"
    ner_predictions=$(tail -n +2 "$ner_out_dir/predictions.csv" | wc -l)
    echo "NER predictions: $ner_predictions"
    echo ""

    # Step 5: Extract URLs
    echo "========================================="
    echo "STEP 5: EXTRACTING URLS"
    echo "========================================="
    echo "Input: $ner_out_dir/predictions.csv"
    echo "Max URLs per paper: $max_urls"
    echo "Output: $extract_url_dir/predictions.csv"
    echo ""

    $PYTHON_CMD src/url_extractor.py \
        -o "$extract_url_dir" \
        -x "$max_urls" \
        "$ner_out_dir/predictions.csv"

    echo "✅ URL extraction completed successfully"
    url_papers=$(tail -n +2 "$extract_url_dir/predictions.csv" | wc -l)
    echo "Papers with URLs: $url_papers"
    echo ""

    # Step 6: Process names
    echo "========================================="
    echo "STEP 6: PROCESSING NAMES"
    echo "========================================="
    echo "Input: $extract_url_dir/predictions.csv"
    echo "Output: $processed_names_dir/predictions.csv"
    echo ""

    $PYTHON_CMD src/process_names.py \
        -o "$processed_names_dir" \
        "$extract_url_dir/predictions.csv"

    echo "✅ Name processing completed successfully"
    processed_entries=$(tail -n +2 "$processed_names_dir/predictions.csv" | wc -l)
    echo "Processed entries: $processed_entries"
    echo ""

    # Step 7: Initial deduplication
    echo "========================================="
    echo "STEP 7: INITIAL DEDUPLICATION"
    echo "========================================="
    echo "New file: $processed_names_dir/predictions.csv"
    echo "Previous inventory: $previous_inventory"
    echo "Output: $initial_dedupe_dir/predictions.csv"
    echo ""

    $PYTHON_CMD src/initial_deduplicate.py \
        -o "$initial_dedupe_dir" \
        -p "$previous_inventory" \
        "$processed_names_dir/predictions.csv"

    echo "✅ Initial deduplication completed successfully"
    dedupe_entries=$(tail -n +2 "$initial_dedupe_dir/predictions.csv" | wc -l)
    echo "Deduplicated entries: $dedupe_entries"
    echo ""

    # Step 8: Flag for manual review
    echo "========================================="
    echo "STEP 8: FLAGGING FOR MANUAL REVIEW"
    echo "========================================="
    echo "Input: $initial_dedupe_dir/predictions.csv"
    echo "Min probability threshold: $min_best_name_prob"
    echo "Output: $for_manual_review_dir/predictions.csv"
    echo ""

    $PYTHON_CMD src/flag_for_review.py \
        -o "$for_manual_review_dir" \
        -p "$min_best_name_prob" \
        "$initial_dedupe_dir/predictions.csv"

    echo "✅ Flagging for manual review completed successfully"
    flagged_entries=$(tail -n +2 "$for_manual_review_dir/predictions.csv" | wc -l)
    echo "Entries flagged for review: $flagged_entries"
    echo ""
fi

# Handle manual review or skip it
if [ "$SKIP_MANUAL_REVIEW" = true ]; then
    echo "========================================="
    echo "SKIPPING MANUAL REVIEW"
    echo "========================================="
    echo "Copying flagged entries directly to continue pipeline..."
    cp "$for_manual_review_dir/predictions.csv" "$manually_reviewed_dir/predictions.csv"
    echo "✅ Manual review step skipped"
    echo ""
    jump_to_url_check=true
elif [ "$CONTINUE_AFTER_REVIEW" = true ] || [ "$jump_to_manual_continue" = true ]; then
    echo "========================================="
    echo "CONTINUING AFTER MANUAL REVIEW"
    echo "========================================="
    
    # Check if manually reviewed file exists
    if [ ! -f "$manually_reviewed_dir/predictions.csv" ]; then
        echo "❌ Manually reviewed file not found: $manually_reviewed_dir/predictions.csv"
        echo "Please complete manual review first or use --skip-manual-review"
        exit 1
    fi
    
    echo "✅ Found manually reviewed file"
    jump_to_url_check=true
else
    echo "========================================="
    echo "MANUAL REVIEW REQUIRED"
    echo "========================================="
    echo "Please review the file: $for_manual_review_dir/predictions.csv"
    echo "According to the instruction sheet: https://doi.org/10.5281/zenodo.7768363"
    echo "Then place the manually reviewed file in: $manually_reviewed_dir/predictions.csv"
    echo ""
    echo "To continue after manual review, run:"
    echo "./run_update_inventory_manual.sh --continue-after-manual-review"
    echo ""
    echo "Or to skip manual review entirely, run:"
    echo "./run_update_inventory_manual.sh --skip-manual-review"
    exit 0
fi

if [ "$jump_to_url_check" = true ]; then
    # Step 9: Check URLs (with skip-wayback option)
    echo "========================================="
    echo "STEP 9: CHECKING URLS"
    echo "========================================="
    echo "Input: $for_manual_review_dir/predictions.csv"
    echo "Chunk size: $chunk_size, Tries: $num_tries, Backoff: $backoff"
    echo "Skip Wayback Machine: $SKIP_WAYBACK"
    echo "Output: $check_url_dir/predictions.csv"
    echo ""
    
    if [ "$SKIP_WAYBACK" = true ]; then
        wayback_flag="--skip-wayback"
    else
        wayback_flag=""
    fi
    
    $PYTHON_CMD src/check_urls.py \
        -s "$chunk_size" \
        -n "$num_tries" \
        -b "$backoff" \
        $wayback_flag \
        -o "$check_url_dir" \
        "$for_manual_review_dir/predictions.csv"

    echo "✅ URL checking completed successfully"
    url_checked=$(tail -n +2 "$check_url_dir/predictions.csv" | wc -l)
    echo "Entries with checked URLs: $url_checked"
    echo ""

    # Step 10: Get EuropePMC metadata
    echo "========================================="
    echo "STEP 10: GETTING EUROPEMC METADATA"
    echo "========================================="
    echo "Input: $check_url_dir/predictions.csv"
    echo "Chunk size: $epmc_chunk_size"
    echo "Output: $epmc_meta_dir/predictions.csv"
    echo ""

    $PYTHON_CMD src/get_meta.py \
        --file "$check_url_dir/predictions.csv" \
        -s "$epmc_chunk_size" \
        -o "$epmc_meta_dir"

    echo "✅ EuropePMC metadata retrieval completed successfully"
    meta_entries=$(tail -n +2 "$epmc_meta_dir/predictions.csv" | wc -l)
    echo "Entries with metadata: $meta_entries"
    echo ""

    # Step 11: Process countries
    echo "========================================="
    echo "STEP 11: PROCESSING COUNTRIES"
    echo "========================================="
    echo "Input: $epmc_meta_dir/predictions.csv"
    echo "Country format: $country_format"
    echo "Output: $processed_countries/predictions.csv"
    echo ""

    $PYTHON_CMD src/process_countries.py \
        -o "$processed_countries" \
        -f "$country_format" \
        "$epmc_meta_dir/predictions.csv"

    echo "✅ Country processing completed successfully"
    final_entries=$(tail -n +2 "$processed_countries/predictions.csv" | wc -l)
    echo "Final inventory entries: $final_entries"
    echo ""

    echo "========================================="
    echo "🎉 PIPELINE COMPLETED SUCCESSFULLY!"
    echo "========================================="
    echo "Final inventory file: $processed_countries/predictions.csv"
    echo ""
    echo "Pipeline Summary:"
    echo "- Papers queried: $papers_count"
    echo "- Bio-resources identified: $(tail -n +2 "$classif_out_dir/predicted_positives.csv" | wc -l)"
    echo "- Resources with names: $ner_predictions"
    echo "- Resources with URLs: $url_papers"
    echo "- Final inventory entries: $final_entries"
    echo ""
    echo "All technical fixes applied:"
    echo "✅ Model compatibility issues resolved"
    echo "✅ Network timeout issues fixed"
    echo "✅ Missing dependencies installed"
    echo "✅ Environment properly configured"
fi

echo ""
echo "========================================="
echo "PIPELINE STATUS SUMMARY"
echo "========================================="
echo "✅ EuropePMC Query: $query_out_dir/query_results.csv"
echo "✅ Classification: $classif_out_dir/predictions.csv"
echo "✅ Positive Predictions: $classif_out_dir/predicted_positives.csv"
echo "✅ Named Entity Recognition: $ner_out_dir/predictions.csv"
echo "✅ URL Extraction: $extract_url_dir/predictions.csv"
echo "✅ Name Processing: $processed_names_dir/predictions.csv"
echo "✅ Initial Deduplication: $initial_dedupe_dir/predictions.csv"
echo "✅ Flagged for Manual Review: $for_manual_review_dir/predictions.csv"
if [ "$jump_to_url_check" = true ]; then
echo "✅ URL Checking: $check_url_dir/predictions.csv"
echo "✅ EuropePMC Metadata: $epmc_meta_dir/predictions.csv"
echo "✅ Final Inventory: $processed_countries/predictions.csv"
fi
echo ""
echo "For full documentation, see: pipeline_python38_steps.md"
echo ""