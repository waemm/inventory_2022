This is a classic memory-overflow problem, and your diagnosis is spot on. The issue isn't the 21k *rows* (which is small), but the *size* of the data in those rows.

The core problem is that **you are duplicating your largest data (title, abstract, text) multiple times in memory.**

1.  `papers_df` has the full text.
2.  `classification_results` (from Cell 8) makes a *copy* of the full text.
3.  `ner_results_df` (from Cell 9) makes *another copy* of the full text.

When Cell 10 runs, you have at least two (and briefly, three) full copies of your massive text data in RAM. If the original text is \~40GB, this immediately explodes to 120GB+, causing the crash.

The solution is to **only store the text data once** (in the original `papers_df`) and have Cells 8 and 9 *only* output the new predictions. Cell 10 is then rewritten to merge these small, slim results back onto the large base `papers_df`.

Here are the step-by-step changes to fix this.

-----

### 1\. Modify Cell 8 (Classification)

In the `for batch in tqdm(...)` loop, change the `results.append` block.

**Find this original code:**

```python
        # Collect results
        for i in range(len(batch['id'])):\n
            results.append({\n
                'ID': str(batch['id'][i]),\n
                'text': batch['text'][i],\n
                'publication_date': batch.get('publication_date', [''] * len(batch['id']))[i],\n
                'predicted_label': ID2LABEL[preds[i].item()],\n
                'probability': probs[i][1].item(),  # Probability of bio-resource\n
                'title': batch['title'][i],\n
                'abstract': batch['abstract'][i]\n
            })\n
```

**Replace it with this slim version:**

```python
        # Collect results
        for i in range(len(batch['id'])):\n
            results.append({\n
                'ID': str(batch['id'][i]),\n
                'predicted_label': ID2LABEL[preds[i].item()],\n
                'probability': probs[i][1].item()  # Probability of bio-resource\n
            })\n
```

**Why:** This stops `classification_results` from storing the `text`, `title`, and `abstract`, dramatically reducing its memory footprint.

-----

### 2\. Modify Cell 9 (NER)

Similarly, in the `for batch in tqdm(...)` loop, change the `ner_results.append` block.

**Find this original code:**

```python
            # Format as comma-separated strings
            ner_results.append({\n
                'ID': str(batch['id'][i]),\n
                'text': batch['text'][i],\n
                'publication_date': batch.get('publication_date', [''] * len(batch['id']))[i],\n
                'common_name': ', '.join([text for text, _ in com_entities]),\n
                'common_prob': ', '.join([f\"{prob:.3f}\" for _, prob in com_entities]),\n
                'full_name': ', '.join([text for text, _ in ful_entities]),\n
                'full_prob': ', '.join([f\"{prob:.3f}\" for _, prob in ful_entities])\n
            })\n
```

**Replace it with this slim version:**

```python
            # Format as comma-separated strings
            ner_results.append({\n
                'ID': str(batch['id'][i]),\n
                'common_name': ', '.join([text for text, _ in com_entities]),\n
                'common_prob': ', '.join([f\"{prob:.3f}\" for _, prob in com_entities]),\n
                'full_name': ', '.join([text for text, _ in ful_entities]),\n
                'full_prob': ', '.join([f\"{prob:.3f}\" for _, prob in ful_entities])\n
            })\n
```

**Why:** This stops `ner_results_df` from *also* storing the `text` and `publication_date`, making it a small, lightweight results table.

-----

### 3\. Replace Cell 10 (Merging)

The original Cell 10 is now incorrect, as it assumes `classification_results` is the "base" DataFrame. We must replace it with new logic that uses `papers_df` as the base and performs a memory-efficient *chunked merge*.

This new cell will process `papers_df` in chunks, merge the (now very small) `classification_results`, `ner_results_df`, and `metadata_subset` onto each chunk, and write *that chunk* to the final CSV immediately. This avoids ever holding the full, merged DataFrame in memory.

**Replace the *entire* contents of Cell 10 with this code:**

```python
import gc
import psutil

def get_memory_usage():
    """Get current memory usage in GB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024**3

print("="*80)
print("MERGING RESULTS & CREATING FINAL INVENTORY (MEMORY OPTIMIZED)")
print("="*80)

initial_memory = get_memory_usage()
print(f"\n📊 Initial memory usage: {initial_memory:.2f} GB")

# ---
# 1. Prepare secondary DataFrames for merging.
# These are all small and can fit in memory.
# ---

# Ensure classification_results has 'ID'
if 'ID' not in classification_results.columns:
    classification_results.rename(columns={'id': 'ID'}, inplace=True)

# Ensure ner_results_df has 'ID'
if 'ID' not in ner_results_df.columns:
    ner_results_df.rename(columns={'id': 'ID'}, inplace=True)

# Prepare metadata
if len(metadata_subset) > 0:
    metadata_cols = ['id', 'isOpenAccess', 'citedByCount', 'pubYear', 
                     'is_research_article', 'is_review_article']
    available_cols = [col for col in metadata_cols if col in metadata_subset.columns]
    
    if len(available_cols) > 1:  # More than just 'id'
        metadata_for_merge = metadata_subset[available_cols].copy()
        metadata_for_merge.rename(columns={'id': 'ID'}, inplace=True)
        print("✅ Prepared metadata for merge")
    else:
        metadata_for_merge = None
        print("ℹ️  No additional metadata to merge")
else:
    metadata_for_merge = None
    print("ℹ️  No metadata found")

# Rename 'id' in papers_df to 'ID' for merging
if 'id' in papers_df.columns:
    papers_df.rename(columns={'id': 'ID'}, inplace=True)
elif 'ID' not in papers_df.columns:
    raise ValueError("Base papers_df missing 'id' or 'ID' column")

print(f"✅ Prepared all secondary DataFrames for merging.")
print(f"   Classification results: {len(classification_results):,} rows")
print(f"   NER results: {len(ner_results_df):,} rows")
if metadata_for_merge is not None:
    print(f"   Metadata: {len(metadata_for_merge):,} rows")


# ---
# 2. Process in chunks based on the LARGE papers_df
# ---
CHUNK_SIZE = 5000  # Smaller chunk size for large text data
total_rows = len(papers_df)
num_chunks = (total_rows + CHUNK_SIZE - 1) // CHUNK_SIZE
final_output = OUTPUT_DIR / 'final_inventory.csv'

print(f"\n🔄 Processing {total_rows:,} papers in {num_chunks} chunks (size={CHUNK_SIZE:,})...")

# For statistics
total_bio_resources = 0
total_papers_with_entities = 0
final_columns = papers_df.columns.tolist() + \
                [c for c in classification_results.columns if c != 'ID'] + \
                [c for c in ner_results_df.columns if c != 'ID']
if metadata_for_merge is not None:
     final_columns += [c for c in metadata_for_merge.columns if c != 'ID']

# Write header first
first_chunk = True

for i in range(0, total_rows, CHUNK_SIZE):
    chunk_end = min(i + CHUNK_SIZE, total_rows)
    chunk_num = i // CHUNK_SIZE + 1
    
    print(f"   Chunk {chunk_num}/{num_chunks}: rows {i:,}-{chunk_end:,}")
    
    # Get a chunk of the *base* DataFrame
    base_chunk = papers_df.iloc[i:chunk_end].copy()
    
    # Merge with (small) classification results
    merged_chunk = pd.merge(
        base_chunk,
        classification_results,
        on='ID',
        how='left'
    )
    
    # Merge with (small) NER results
    merged_chunk = pd.merge(
        merged_chunk,
        ner_results_df,
        on='ID',
        how='left'
    )
    
    # Merge with (small) metadata
    if metadata_for_merge is not None:
        merged_chunk = pd.merge(
            merged_chunk,
            metadata_for_merge,
            on='ID',
            how='left'
        )
    
    # Calculate stats for this chunk
    total_bio_resources += (merged_chunk['predicted_label'] == 'bio-resource').sum()
    papers_with_entities_chunk = (
        (merged_chunk['common_name'].fillna('').str.strip() != '') |
        (merged_chunk['full_name'].fillna('').str.strip() != '')
    ).sum()
    total_papers_with_entities += papers_with_entities_chunk

    # Save this chunk directly to CSV
    merged_chunk.to_csv(
        final_output, 
        mode='a' if not first_chunk else 'w',
        header=first_chunk,
        index=False,
        columns=final_columns # Ensure consistent column order
    )
    first_chunk = False # Only write header for the first chunk
    
    # Clear memory
    del base_chunk, merged_chunk
    gc.collect()
    
    current_memory = get_memory_usage()
    print(f"      Memory: {current_memory:.2f} GB (+{current_memory - initial_memory:.2f} GB)")

print(f"\n✅ Final inventory saved: {final_output}")

# ---
# 3. Final Summary and Traceability
# ---
print(f"\n📊 Final Statistics:")
print(f"   Total rows: {total_rows:,}")
print(f"   Bio-resources: {total_bio_resources:,} ({total_bio_resources/total_rows*100:.1f}%)")
print(f"   Papers with entities: {total_papers_with_entities:,} ({total_papers_with_entities/total_rows*100:.1f}%)")

# Store stats for Cell 11
positive_count = total_bio_resources
papers_with_entities = total_papers_with_entities
if 'ner' in TRACEABILITY_CONFIG and 'total_entities' in TRACEABILITY_CONFIG['ner']:
    total_entities = TRACEABILITY_CONFIG['ner']['total_entities']
    print(f"   Total entities extracted: {total_entities:,}")

# Update traceability
TRACEABILITY_CONFIG['final_inventory'] = {
    'total_papers': int(total_rows),
    'total_columns': len(final_columns),
    'created_at': datetime.now().isoformat(),
    'chunked_processing': True,
    'chunk_size': CHUNK_SIZE
}

# Clean up large objects
del papers_df, classification_results, ner_results_df
if metadata_for_merge is not None:
    del metadata_for_merge
gc.collect()

print(f"\n✅ Memory cleaned up. Current usage: {get_memory_usage():.2f} GB")
print("✅ Final inventory created successfully")
print("="*80)
```

By making these changes, your memory usage in Cell 10 will drop from 115GB+ to just the size of one chunk of `papers_df` (plus the small results tables), completely resolving the crash.

