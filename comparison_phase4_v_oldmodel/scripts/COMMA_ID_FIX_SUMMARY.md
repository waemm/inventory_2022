# Comma-Separated ID Fix for load_inventory()

**Date**: 2025-11-05
**File**: `comparison_phase4_v_oldmodel/scripts/utils/data_loading.py`
**Function**: `load_inventory()`

## Problem

The `load_inventory()` function was failing when processing inventory CSV files that contained comma-separated IDs in the PMID column. For example:
- `'27924021, 32162267'`
- `'11111111, 22222222, 33333333'`

When attempting to convert these values directly to float, Python would raise a `ValueError`:
```
ValueError: could not convert string to float: '27924021, 32162267'
```

## Solution

Modified the ID normalization logic in `load_inventory()` (lines 225-243) to:

1. **Detect string columns**: Check if the ID column has dtype 'object' (string type)
2. **Count affected rows**: Count how many rows have comma-separated values
3. **Log warning**: Inform the user that comma-separated IDs were found and only the first ID will be used
4. **Split and extract**: Use `.str.split(',').str[0].str.strip()` to:
   - Split by comma
   - Take the first ID (`[0]`)
   - Remove leading/trailing whitespace (`.strip()`)
5. **Convert normally**: Proceed with the standard float → int → string conversion

## Code Changes

### Before:
```python
# Normalize ID columns: convert float -> int -> string to avoid .0 suffix
for id_col in ['pmid', 'PMID', 'id', 'ID']:
    if id_col in df.columns:
        df[id_col] = df[id_col].astype(float).astype(int).astype(str)
        logger.debug(f"Normalized '{id_col}' column to string format...")
        break
```

### After:
```python
# Normalize ID columns: convert float -> int -> string to avoid .0 suffix
for id_col in ['pmid', 'PMID', 'id', 'ID']:
    if id_col in df.columns:
        # Handle comma-separated IDs by taking the first one
        if df[id_col].dtype == 'object':  # String column
            # Check if any values contain commas
            has_commas = df[id_col].astype(str).str.contains(',', na=False).any()
            if has_commas:
                num_affected = df[id_col].astype(str).str.contains(',', na=False).sum()
                logger.warning(f"Found {num_affected} rows with comma-separated IDs in '{id_col}' column. "
                              f"Using only the first ID from each comma-separated value.")

            # Split by comma and take first ID, then strip whitespace
            df[id_col] = df[id_col].astype(str).str.split(',').str[0].str.strip()

        # Now convert: string -> float -> int -> string
        df[id_col] = df[id_col].astype(float).astype(int).astype(str)
        logger.debug(f"Normalized '{id_col}' column to string format...")
        break
```

## Example Output

When loading an inventory file with comma-separated IDs:

```
INFO: Loading inventory from: data/final_inventory_2022.csv
WARNING: Found 2 rows with comma-separated IDs in 'pmid' column. Using only the first ID from each comma-separated value.
INFO: Successfully loaded 10000 papers with columns: ['pmid', 'title', 'abstract', ...]
```

## Testing

Created test script `test_comma_id_fix.py` that verifies:
- ✓ Comma-separated IDs are split correctly
- ✓ Only the first ID is used
- ✓ Whitespace is properly trimmed
- ✓ Final IDs are strings without `.0` suffix
- ✓ Warning message is logged

Test output:
```
✓ TEST PASSED: Comma-separated IDs handled correctly!
WARNING: Found 2 rows with comma-separated IDs in 'pmid' column. Using only the first ID from each comma-separated value.
```

## Impact

- **Backwards compatible**: Works with both single IDs and comma-separated IDs
- **User transparency**: Warning message informs users when IDs are processed
- **Data integrity**: Only uses the first ID from comma-separated values
- **No breaking changes**: Existing functionality remains unchanged

## Related Functions

This same pattern could be applied to other data loading functions if needed:
- `load_v2_results()` (lines 66-68)
- `load_phase4_results()` (lines 119-121)
- `load_ner_test_split()` (lines 172-174)

Currently, these functions don't have the comma-separated ID handling, but the fix can be added if similar issues arise.
