# Agent Prompt: best_name Quality Control Analysis

## Task Overview

You are analyzing the `final_inventory.csv` file to identify and investigate suspicious values in the `best_name` column. Your goal is to find incorrect, incomplete, or suspicious resource names and determine the correct name using available data.

## Input File

**File:** `unified_bioresource_pipeline/results/2025-12-01-104909-sa4r9/finalization/final_inventory.csv`

**Scope:** First 500 rows

**Key columns to analyze:**
- `ID` - PMID(s) for the resource
- `best_name` - Current resource name (INVESTIGATE THIS)
- `best_common` - Alternative name candidate
- `best_full` - Alternative name candidate
- `extracted_url` - URL may contain correct name
- `paper_titles` - Paper title(s) may contain correct name
- `name_modification_flags` - Shows what modifications were already applied

## Detection Patterns

Flag entries matching ANY of these patterns:

### Category 1: Empty or Missing Names
- `best_name` is empty, null, or whitespace only
- **Priority: HIGH** - These resources have no name at all

### Category 2: Numeric-Only Names
- Names consisting only of numbers (e.g., "265", "123")
- **Priority: HIGH** - Numbers alone are never valid resource names

### Category 3: Very Short Names (1-2 characters)
- Names like "h", "x", "2d", "ab"
- **Priority: HIGH** - Usually NER extraction errors
- **Exception:** Some valid acronyms exist - check URL/title to verify

### Category 4: Short Lowercase Names (3-4 chars, all lowercase)
- Names like "load", "data", "gene"
- **Priority: MEDIUM** - Often generic words extracted incorrectly
- Check if URL/title has a more specific name

### Category 5: Names with Brackets
- Pattern: "Something (something else)"
- Examples: "Melanoma (khaos)", "GXB (breastcancer)"
- **Priority: MEDIUM** - Analyze bracket content:
  - Is the bracketed part a disambiguation suffix we added? (check URL domain)
  - Is it an alternative name from NER?
  - Is it incorrect/should be removed?
  - What is the BEST single name for this resource?

### Category 6: Suspicious Patterns
- Contains HTML fragments: `<`, `>`, `</`
- Contains pipe characters: `|`
- Starts/ends with punctuation
- **Priority: HIGH** - Clear data quality issues

## Investigation Process

For EACH flagged entry:

1. **Check `paper_titles`**: Does the title contain a clear resource name?
   - Look for capitalized terms, database names, tool names
   - Example: Title "VIGLA-M: A database for..." suggests name should be "VIGLA-M"

2. **Check `extracted_url`**: Can we derive the name from the URL?
   - Domain name often matches resource name
   - Path segments may contain resource name
   - Example: `http://2d-page.org` suggests "2D-PAGE"

3. **Check `best_common` and `best_full`**: Are these better alternatives?
   - Sometimes the correct name is in an alternative field

4. **Determine best name**: What SHOULD this resource be called?
   - Use evidence from title, URL, and alternatives
   - Prefer the most specific, recognizable name

## Output Format

Generate a CSV file with these columns:

```
pmid,current_best_name,issue_category,evidence_from_title,evidence_from_url,best_common,best_full,suggested_name,confidence,notes
```

**Column definitions:**
- `pmid`: The ID value
- `current_best_name`: Current value in best_name column
- `issue_category`: One of: EMPTY, NUMERIC_ONLY, VERY_SHORT, SHORT_LOWERCASE, HAS_BRACKETS, SUSPICIOUS_CHARS
- `evidence_from_title`: Resource name found in paper_titles (if any)
- `evidence_from_url`: Resource name derived from URL (if any)
- `best_common`: Value from best_common column
- `best_full`: Value from best_full column
- `suggested_name`: Your recommended correct name
- `confidence`: HIGH, MEDIUM, or LOW
- `notes`: Brief explanation of your reasoning

**Confidence levels:**
- **HIGH**: Clear evidence from title/URL, high certainty
- **MEDIUM**: Reasonable inference, but not 100% certain
- **LOW**: Best guess, needs manual verification

## Example Output Rows

```csv
pmid,current_best_name,issue_category,evidence_from_title,evidence_from_url,best_common,best_full,suggested_name,confidence,notes
34292965,265,NUMERIC_ONLY,ToolName mentioned in title,toolname.org,,,ToolName,HIGH,Title clearly states resource is ToolName
21841810,2d,VERY_SHORT,2D-PAGE database,2d-page.org,,,2D-PAGE,HIGH,URL and title both confirm 2D-PAGE
30999846,Melanoma (khaos),HAS_BRACKETS,VIGLA-M database,khaos.org/vigla-m,,,VIGLA-M,HIGH,Title says VIGLA-M - current name is completely wrong
```

## Summary Statistics

After analyzing all rows, provide counts:
- Total rows analyzed: X
- Rows with issues found: X
- By category: EMPTY (X), NUMERIC_ONLY (X), VERY_SHORT (X), etc.
- By confidence: HIGH (X), MEDIUM (X), LOW (X)

## Instructions

1. Read the first 500 rows of the CSV file
2. Apply detection patterns to flag suspicious entries
3. For each flagged entry, investigate using title/URL/alternatives
4. Determine the best name and confidence level
5. Output findings to CSV format
6. Provide summary statistics

**Output file:** `unified_bioresource_pipeline/post_processing/results/best_name_qc_report.csv`
