# Session-Based Pipeline Outputs

This directory contains outputs from session-based pipeline runs. Each session is isolated in its own subdirectory with a unique session ID.

---

## Quick Reference

**Session ID Format**: `YYYY-MM-DD-HHMMSS-xxxxx`
- Example: `2025-11-21-143022-a7k3f`
- Timestamp: `2025-11-21` at `14:30:22`
- Random suffix: `a7k3f` (prevents collisions)

**List Sessions**:
```bash
python run_complete_pipeline.py --list-sessions
```

**Resume Session**:
```bash
python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f
```

---

## Directory Structure

Each session directory follows this structure:

```
sessions/{session-id}/
├── session_metadata.json          # Session tracking and progress
├── deduplicated/                  # Step 3: Deduplication outputs
│   ├── set_a_linguistic_dedup.csv
│   ├── set_b_setfit_dedup.csv
│   ├── set_c_union_dedup.csv
│   ├── deduplication_report.txt
│   └── deduplication_statistics.json
├── url_scanned/                   # Step 4: URL scanning outputs
│   ├── set_c_with_url_scan.csv
│   └── url_scan_statistics.txt
├── final/                         # Step 5: Backfill outputs
│   ├── set_a_linguistic_final.csv
│   ├── set_b_setfit_final.csv
│   ├── set_c_union_final.csv
│   └── backfill_statistics.txt
├── baseline_comparison/           # Step 6: Baseline comparison outputs
│   ├── baseline_comparison_report.txt
│   ├── baseline_comparison_stats.json
│   └── baseline_comparison_data.csv
└── visualizations/                # Step 7: Visualization outputs
    ├── baseline_coverage.png
    ├── baseline_coverage.html
    ├── match_types.png
    ├── match_types.html
    ├── resource_counts.png
    ├── resource_counts.html
    ├── score_distributions.png  (optional)
    └── score_distributions.html (optional)
```

---

## File Descriptions

### Session Metadata

#### `session_metadata.json`
**Purpose**: Tracks session progress and completion status

**Format**:
```json
{
  "session_id": "2025-11-21-143022-a7k3f",
  "created_at": "2025-11-21 14:30:22",
  "last_updated": "2025-11-21 15:45:10",
  "completed_steps": [1, 2, 3, 5, 6, 7],
  "step_details": {
    "1": {
      "name": "Entity mapping",
      "completed_at": "2025-11-21 14:35:10"
    },
    "2": {
      "name": "Filtered datasets (with baseline)",
      "completed_at": "2025-11-21 14:42:33"
    },
    "3": {
      "name": "Deduplication (A, B, C)",
      "completed_at": "2025-11-21 14:58:15"
    },
    "5": {
      "name": "Backfill URL data",
      "completed_at": "2025-11-21 15:01:22"
    },
    "6": {
      "name": "Baseline comparison",
      "completed_at": "2025-11-21 15:05:18"
    },
    "7": {
      "name": "Generate visualizations",
      "completed_at": "2025-11-21 15:07:45"
    }
  }
}
```

**Usage**:
- Automatically updated by pipeline orchestrator
- Used to determine which steps to skip during resume
- Manually editable if needed (to force rerun)

---

### Deduplication Outputs (`deduplicated/`)

#### `set_a_linguistic_dedup.csv`, `set_b_setfit_dedup.csv`, `set_c_union_dedup.csv`
**Purpose**: Deduplicated resource datasets

**Key Columns**:
- `pmid`: Paper PMID (may be comma-separated if merged)
- `primary_entity_long`: Full entity name (representative from group)
- `primary_entity_short`: Short entity name
- `resource_url`: Resource URL (representative from group)
- `cluster_id`: Deduplication cluster identifier
- `cluster_size`: Number of resources merged into this entry
- `baseline_entity_match`: Matched entity from 2022 baseline (if any)

**Important Notes**:
- Comma-separated PMIDs indicate merged entries
- `cluster_size > 1` means this row represents multiple original resources
- Set C (Union) is superset of Sets A and B

#### `deduplication_report.txt`
**Purpose**: Human-readable deduplication summary

**Contents**:
- Total resources before/after deduplication
- Reduction percentage per set
- URL clustering statistics
- Entity name similarity groups

#### `deduplication_statistics.json`
**Purpose**: Machine-readable deduplication metrics

**Usage**:
- Programmatic analysis of deduplication effectiveness
- Trend tracking across sessions
- Input for comparison reports

---

### URL Scanning Outputs (`url_scanned/`)

#### `set_c_with_url_scan.csv`
**Purpose**: Set C with URL validation results

**Additional Columns** (added to Set C):
- `url_status`: HTTP status code (200, 404, etc.)
- `url_final`: Final URL after redirects
- `url_score`: Bioresource likelihood score (0.0-1.0)
- `url_is_live`: Boolean - URL is accessible
- `url_likelihood`: Category (Very High, High, Medium, Low)
- `url_indicators_found`: Count of bioresource indicators detected
- `url_wayback_used`: Boolean - Retrieved from Wayback Machine

**Score Interpretation**:
- ≥ 0.8: Very High confidence (likely bioresource)
- 0.6-0.8: High confidence
- 0.4-0.6: Medium confidence
- < 0.4: Low confidence (possibly not a bioresource)

**URL Scanner**: Uses `bioresource_url_scanner` V4 with Wayback Machine fallback

#### `url_scan_statistics.txt`
**Purpose**: Summary of URL scanning results

**Contents**:
- Total URLs scanned
- Status code distribution
- Score distribution
- Wayback Machine usage count

---

### Final Outputs (`final/`)

#### `set_a_linguistic_final.csv`, `set_b_setfit_final.csv`, `set_c_union_final.csv`
**Purpose**: Final datasets with URL scan data backfilled

**Key Changes from Deduplication**:
- All three sets now have identical column structure
- URL scan columns backfilled from Set C where URLs match
- Ready for baseline comparison and analysis

**Column Structure** (all sets):
- Original deduplication columns
- `url_status`, `url_final`, `url_score`, etc. (from URL scanning)
- `in_baseline_pmid`, `in_baseline_entity`, `in_baseline` (from baseline comparison)

**Important**: These are the **primary outputs** for downstream analysis

#### `backfill_statistics.txt`
**Purpose**: Summary of URL data backfill process

**Contents**:
- Backfill coverage per set
- Column consistency validation
- Data quality checks

---

### Baseline Comparison Outputs (`baseline_comparison/`)

#### `baseline_comparison_report.txt`
**Purpose**: Human-readable comparison against 2022 baseline

**Example**:
```
================================================================================
BASELINE COMPARISON REPORT
Generated: 2025-11-21 15:45:10
Session: 2025-11-21-143022-a7k3f
================================================================================

BASELINE INVENTORY:
  Total resources: 1948

RESOURCE COUNTS BY SET:
  Set A (Linguistic):
    Total resources: 3,524
    In baseline: 1,721 (48.8%)
    Novel discoveries: 1,803 (51.2%)

  Set B (SetFit):
    Total resources: 3,892
    In baseline: 1,834 (47.1%)
    Novel discoveries: 2,058 (52.9%)

  Set C (Union):
    Total resources: 4,156
    In baseline: 1,892 (45.5%)
    Novel discoveries: 2,264 (54.5%)

BASELINE COVERAGE (% of baseline resources found):
  Set A: 1,721/1,948 (88.3%)
  Set B: 1,834/1,948 (94.1%)
  Set C: 1,892/1,948 (97.1%)

MATCH TYPE BREAKDOWN:
  Set A (Linguistic):
    PMID only: 523
    Entity only: 412
    Both: 786
```

**Interpretation**:
- **In Baseline**: Resources that match 2022 inventory
- **Novel Discoveries**: New resources not in 2022 inventory
- **Baseline Coverage**: What % of 2022 inventory was recovered
- **Match Types**:
  - PMID only: Same paper, different entity name
  - Entity only: Different paper, same resource name
  - Both: Perfect match (same paper and resource)

#### `baseline_comparison_stats.json`
**Purpose**: Machine-readable baseline statistics

**Usage**:
- Automated quality monitoring
- Session-to-session comparison
- Input for visualization generation

#### `baseline_comparison_data.csv`
**Purpose**: Pre-processed data for visualization generation

**Format**:
```csv
set,set_name,total,in_baseline,novel,pmid_only,entity_only,both_match
A,Set A (Linguistic),3524,1721,1803,523,412,786
B,Set B (SetFit),3892,1834,2058,587,456,791
C,Set C (Union),4156,1892,2264,634,478,780
```

**New Columns in Final CSVs**:
- `in_baseline_pmid`: Boolean - PMID matches baseline
- `in_baseline_entity`: Boolean - Entity name matches baseline
- `in_baseline`: Boolean - Either PMID or entity matches baseline

---

### Visualization Outputs (`visualizations/`)

All visualizations are generated in two formats:
- **PNG**: Static images (300 DPI, publication quality)
- **HTML**: Interactive Plotly charts (open in browser)

#### Chart 1: Baseline Coverage
**Files**: `baseline_coverage.png`, `baseline_coverage.html`

**Shows**: % of 2022 baseline resources found in each set

**Use Case**: Evaluate how well each method recovers known resources

#### Chart 2: Match Type Distribution
**Files**: `match_types.png`, `match_types.html`

**Shows**: Stacked bar chart of match types per set
- Blue: PMID only matches
- Orange: Entity only matches
- Green: Both PMID and entity matches
- Red: Novel discoveries

**Use Case**: Understand how resources relate to baseline

#### Chart 3: Resource Counts
**Files**: `resource_counts.png`, `resource_counts.html`

**Shows**: Grouped bar chart comparing in-baseline vs novel resources

**Use Case**: Quick visual comparison of discovery rates

#### Chart 4: URL Score Distribution (Optional)
**Files**: `score_distributions.png`, `score_distributions.html`

**Shows**: Overlapping histograms of URL validation scores
- Blue: Baseline resources
- Orange: Novel resources

**Use Case**: Assess quality of novel discoveries vs known resources

**Note**: Only generated if URL scanning was performed

---

## Common Use Cases

### 1. Reviewing Session Results

```bash
# List all sessions
python run_complete_pipeline.py --list-sessions

# Navigate to session directory
cd results/sessions/2025-11-21-143022-a7k3f

# View baseline comparison report
cat baseline_comparison/baseline_comparison_report.txt

# Open interactive charts
open visualizations/baseline_coverage.html
open visualizations/match_types.html
```

### 2. Extracting Final Datasets

The **primary outputs** for analysis are in `final/`:

```bash
# Copy final datasets to working directory
cp results/sessions/2025-11-21-143022-a7k3f/final/set_c_union_final.csv ./my_analysis/

# Or access directly
python my_analysis.py --input results/sessions/2025-11-21-143022-a7k3f/final/set_c_union_final.csv
```

### 3. Comparing Across Sessions

```bash
# Compare deduplication effectiveness
diff -y \
  sessions/2025-11-21-143022-a7k3f/deduplicated/deduplication_report.txt \
  sessions/2025-11-20-093045-b5n7p/deduplicated/deduplication_report.txt

# Compare baseline coverage
diff -y \
  sessions/2025-11-21-143022-a7k3f/baseline_comparison/baseline_comparison_report.txt \
  sessions/2025-11-20-093045-b5n7p/baseline_comparison/baseline_comparison_report.txt
```

### 4. Extracting Novel Discoveries

```python
import pandas as pd

# Load final Set C
df = pd.read_csv('results/sessions/2025-11-21-143022-a7k3f/final/set_c_union_final.csv')

# Filter for novel discoveries only
novel = df[df['in_baseline'] == False]

# High-confidence novel discoveries
high_conf_novel = novel[novel['url_score'] >= 0.8]

print(f"Total novel discoveries: {len(novel)}")
print(f"High-confidence novel: {len(high_conf_novel)}")

# Save to file
high_conf_novel.to_csv('novel_high_confidence.csv', index=False)
```

### 5. Quality Assessment

Check data quality by reviewing:

1. **Deduplication Effectiveness**:
   - Review `deduplicated/deduplication_report.txt`
   - Look for reasonable reduction rates (30-50% typical)

2. **URL Validation Coverage**:
   - Check `url_scanned/url_scan_statistics.txt`
   - High percentage of live URLs is good sign

3. **Baseline Recovery**:
   - Review `baseline_comparison/baseline_comparison_report.txt`
   - Coverage > 90% indicates good recall

4. **Novel Discovery Quality**:
   - View `visualizations/score_distributions.html`
   - Novel resources should have similar score distribution to baseline

---

## Session Management

### Resuming a Session

If pipeline was interrupted:

```bash
# Resume from last completed step
python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f
```

The orchestrator automatically:
- Reads `session_metadata.json`
- Identifies completed steps
- Continues from next incomplete step

### Rerunning Specific Steps

To regenerate specific outputs:

```bash
# Rerun from deduplication onward
python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f --from-step 3

# Rerun only baseline comparison and visualizations
python run_complete_pipeline.py --session-id 2025-11-21-143022-a7k3f --from-step 6
```

### Archiving Old Sessions

```bash
# Compress old session
tar -czf 2025-11-20-093045-b5n7p.tar.gz sessions/2025-11-20-093045-b5n7p/

# Move to archive directory
mkdir -p ../archived_sessions/
mv 2025-11-20-093045-b5n7p.tar.gz ../archived_sessions/

# Remove original
rm -r sessions/2025-11-20-093045-b5n7p/
```

---

## Data Flow Through Pipeline

```
[Input Data]
    ↓
Step 3: Deduplication
    → deduplicated/set_*_dedup.csv
    ↓
Step 4: URL Scanning
    → url_scanned/set_c_with_url_scan.csv
    ↓
Step 5: Backfill URL Data
    → final/set_*_final.csv  ← PRIMARY OUTPUTS
    ↓
Step 6: Baseline Comparison
    → final/set_*_final.csv (with in_baseline_* columns)
    → baseline_comparison/reports
    ↓
Step 7: Visualizations
    → visualizations/*.png + *.html
```

**Key Insight**: Each step builds on previous step's outputs, culminating in the `final/` directory containing analysis-ready datasets.

---

## File Size Expectations

Typical session directory size (Set C with ~4,000 resources):

```
deduplicated/       ~5-8 MB   (3 CSV files + reports)
url_scanned/       ~2-3 MB   (1 CSV + statistics)
final/            ~12-15 MB  (3 CSV files + statistics)
baseline_comp/     ~100 KB   (reports + JSON)
visualizations/     ~2-3 MB  (4 PNG + 4 HTML files)
session_metadata    ~2 KB    (JSON)

Total:            ~22-30 MB per session
```

**Recommendation**: Keep last 5-10 sessions, archive older ones

---

## Troubleshooting

### Missing Files

**Issue**: Expected files not present in session directory

**Causes**:
1. Pipeline step was skipped (check `session_metadata.json`)
2. Step failed (check console output)
3. Optional step not run (URL scanning, baseline comparison)

**Solution**:
```bash
# Check which steps completed
cat sessions/{session-id}/session_metadata.json

# Rerun missing steps
python run_complete_pipeline.py --session-id {session-id} --from-step {N}
```

### Inconsistent Column Structure

**Issue**: Sets A, B, C have different columns

**Cause**: URL backfill (Step 5) not completed

**Solution**:
```bash
# Rerun backfill step
python scripts/19_backfill_url_data.py --session-dir sessions/{session-id}
```

### Large File Sizes

**Issue**: Session directory larger than expected

**Causes**:
1. Large number of resources in datasets
2. Many duplicate resources before deduplication
3. Verbose logging enabled

**Solution**:
- Compress old sessions: `tar -czf session.tar.gz sessions/{id}/`
- Archive to external storage
- Clean up intermediate files if rerun not needed

### Visualization Not Generated

**Issue**: PNG or HTML files missing

**Causes**:
1. matplotlib/plotly not installed
2. Baseline comparison not run (Step 6)
3. Visualization step skipped

**Solution**:
```bash
# Install visualization dependencies
pip install matplotlib plotly

# Rerun baseline + visualization
python run_complete_pipeline.py --session-id {session-id} --from-step 6
```

---

## Best Practices

1. **Naming Conventions**:
   - Use session IDs as provided (don't rename directories)
   - Preserves metadata linkage and orchestrator compatibility

2. **Data Backups**:
   - Keep at least last 3 sessions uncompressed
   - Archive older sessions weekly
   - Back up critical results before cleanup

3. **Quality Checks**:
   - Always review deduplication_report.txt after Step 3
   - Check URL scan statistics after Step 4
   - Verify baseline coverage after Step 6

4. **Documentation**:
   - Add notes to session_metadata.json if needed:
     ```json
     "notes": "Rerun with updated deduplication threshold 0.9"
     ```

5. **Comparative Analysis**:
   - Run same input data with different parameters in separate sessions
   - Compare baseline_comparison reports to evaluate parameter changes

---

## Related Documentation

- **Pipeline Overview**: `../PIPELINE_CHANGES_2025-11-21.md`
- **Orchestrator Usage**: `../run_complete_pipeline.py` (see docstring)
- **Implementation Plan**: `../../plans/2025-11-21_session_based_pipeline_with_baseline.md`

---

*Document created: 2025-11-21*
*Last updated: 2025-11-21*
*Maintained by: Pipeline Orchestrator*
