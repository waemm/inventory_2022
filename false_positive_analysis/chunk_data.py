#!/usr/bin/env python3
"""
Chunk the aggressive set_c data into 500-paper segments for agent review.
Extracts only the columns needed for title-based review.
"""

import pandas as pd
import os

# Input file
INPUT_FILE = "/Users/warren/development/GBC/inventory_2022/pipeline_synthesis_2025-11-18/results/baseline_comparison/aggressive/set_c_with_baseline.csv"
OUTPUT_DIR = "/Users/warren/development/GBC/inventory_2022/false_positive_analysis/chunks"
CHUNK_SIZE = 500

def main():
    # Read the data
    print(f"Reading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    print(f"Total papers: {len(df)}")

    # Select only relevant columns for review
    # pmid, title, has_resource_url, resource_url
    review_cols = ['pmid', 'title', 'has_resource_url', 'resource_url']
    df_review = df[review_cols].copy()

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Create chunks
    num_chunks = (len(df_review) + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"Creating {num_chunks} chunks of up to {CHUNK_SIZE} papers each...")

    for i in range(num_chunks):
        start_idx = i * CHUNK_SIZE
        end_idx = min((i + 1) * CHUNK_SIZE, len(df_review))
        chunk = df_review.iloc[start_idx:end_idx]

        output_file = os.path.join(OUTPUT_DIR, f"chunk_{i+1:02d}.csv")
        chunk.to_csv(output_file, index=False)
        print(f"  Chunk {i+1}: papers {start_idx+1}-{end_idx} -> {output_file}")

    print(f"\nDone! Created {num_chunks} chunk files in {OUTPUT_DIR}")
    return num_chunks

if __name__ == "__main__":
    main()
