# Google Drive Sync Scripts

**Created**: 2025-10-29
**Purpose**: Automated upload/download scripts for Google Drive via rclone
**Status**: ✅ Production Ready

---

## Overview

Two Python scripts for managing file synchronization between local project and Google Drive:

1. **upload_to_drive.py** - Upload specific files to Google Drive, preserving directory structure
2. **download_from_drive.py** - Download new experimental/training archives from Google Drive

Both scripts:
- Log all operations to CSV files for audit trail
- Stop on first error (fail-fast)
- Use token-efficient rclone commands (no `--progress`)
- Provide clear status messages

---

## Installation

**Prerequisites**:
- Python 3.7+
- rclone installed and configured with "gdrive" remote
- Google Drive access to inventory_2022 directory

**Verify setup**:
```bash
# Check rclone is installed
which rclone

# Check remote is configured
rclone listremotes
# Should show: gdrive:

# Test access
rclone lsd gdrive:inventory_2022
```

---

## Upload Script

### Basic Usage

```bash
# Upload specific files (preserves directory structure)
python upload_to_drive.py src/class_train.py src/experimental_utils.py

# Upload notebook to root
python upload_to_drive.py experimental_training_pipeline.ipynb

# Upload multiple files with mixed paths
python upload_to_drive.py \
  experimental_training_pipeline.ipynb \
  src/experimental_utils.py \
  src/class_train.py \
  src/ner_train.py
```

### Advanced Options

```bash
# Force upload (skip change detection)
python upload_to_drive.py --force src/rerun_utils.py

# Get help
python upload_to_drive.py --help
```

### How It Works

1. **Validates files** - Checks all files exist and are readable
2. **Calculates checksums** - MD5 hash of local file
3. **Checks remote** - Gets MD5 of remote file (if exists)
4. **Compares** - Skips upload if checksums match (unless `--force`)
5. **Uploads** - Uses `rclone copyto` for individual files
6. **Logs** - Writes CSV log to `upload_logs/`

### Path Preservation

Local path structure is automatically preserved on Google Drive:

- `src/file.py` → `gdrive:inventory_2022/src/file.py`
- `docs/guide.md` → `gdrive:inventory_2022/docs/guide.md`
- `file.py` → `gdrive:inventory_2022/file.py` (root)

### Output

```
🔍 Validating 4 file(s)...
✅ All files valid

📤 Uploading experimental_training_pipeline.ipynb -> gdrive:... (changed)...
✅ Success: experimental_training_pipeline.ipynb
📤 Uploading src/experimental_utils.py -> gdrive:... (changed)...
✅ Success: src/experimental_utils.py
⏭️  Skipping src/class_train.py (unchanged)
⏭️  Skipping src/ner_train.py (unchanged)

📋 Log written to: upload_logs/2025-10-29_16-04-15_upload.csv

✅ Upload complete:
   Uploaded: 2
   Skipped: 2
   Total: 4
```

### Log Format

CSV file: `upload_logs/YYYY-MM-DD_HH-MM-SS_upload.csv`

| Column | Description | Example |
|--------|-------------|---------|
| timestamp | ISO 8601 timestamp | 2025-10-29T16:04:01.112516 |
| file_path | Relative path from project root | src/experimental_utils.py |
| size_bytes | File size in bytes | 23704 |
| status | Upload status | success / skipped / failed: error |
| checksum | MD5 hash | 04be34d18b5e79d6d295f3f5c8edc985 |

---

## Download Script

### Basic Usage

```bash
# Download new experimental sessions (auto-download)
python download_from_drive.py --archive-type experiment_archives

# Download new training archives
python download_from_drive.py --archive-type training_archives

# Download from custom location
python download_from_drive.py --archive-type path/to/custom/archives
```

### Advanced Options

```bash
# Interactive mode (ask before downloading)
python download_from_drive.py --archive-type experiment_archives --interactive

# Get help
python download_from_drive.py --help
```

### How It Works

1. **Lists remote sessions** - Uses `rclone lsd` to get session directories
2. **Checks local** - Determines which sessions don't exist locally
3. **Downloads new** - Uses `rclone copy` for each new session
4. **Creates marker** - Creates empty directory even if remote is empty
5. **Logs** - Writes CSV log to `download_logs/`

### Output

```
🔍 Listing sessions in experiment_archives...
✅ Found 3 total session(s)

🔍 Checking for new sessions...
✅ Found 1 new session(s)

📥 Downloading 1 session(s)...

📥 Downloading 2025-10-29-abc123...
✅ Success: 2025-10-29-abc123

📋 Log written to: download_logs/2025-10-29_16-04-46_download.csv

✅ Download complete:
   Sessions: 1
   Total size: 45.32 MB
   Location: collab_results/experiment_archives
```

If all sessions already exist:
```
🔍 Listing sessions in experiment_archives...
✅ Found 3 total session(s)

🔍 Checking for new sessions...
ℹ️  No new sessions to download (all 3 already exist locally)
```

### Interactive Mode

When using `--interactive`, the script lists new sessions and asks for confirmation:

```
New sessions found:
  1. 2025-10-29-abc123
  2. 2025-10-29-def456

Download all new sessions? (y/n): y
```

### Log Format

CSV file: `download_logs/YYYY-MM-DD_HH-MM-SS_download.csv`

| Column | Description | Example |
|--------|-------------|---------|
| timestamp | ISO 8601 timestamp | 2025-10-29T16:04:46.380530 |
| session_id | Session directory name | 2025-10-29-abc123 |
| archive_type | Archive directory | experiment_archives |
| size_bytes | Total size in bytes | 47523840 (45.3 MB) |
| status | Download status | success / failed: error |

---

## Common Workflows

### Upload Files for Colab Testing

```bash
# Upload the 4 critical files for experimental training
python upload_to_drive.py \
  experimental_training_pipeline.ipynb \
  src/experimental_utils.py \
  src/class_train.py \
  src/ner_train.py
```

### Download Latest Experimental Results

```bash
# Download any new experimental sessions
python download_from_drive.py --archive-type experiment_archives

# Analyze results
ls -lh collab_results/experiment_archives/
```

### Check What Would Be Uploaded

Since change detection is automatic, just run the upload command - unchanged files will be skipped:

```bash
python upload_to_drive.py src/file.py
# If unchanged, shows: ⏭️  Skipping src/file.py (unchanged)
```

### Force Re-upload

```bash
# Re-upload even if unchanged
python upload_to_drive.py --force src/file.py
```

---

## Error Handling

Both scripts **stop on first error**:

```bash
❌ Failed: src/missing_file.py
   Error: file not found

❌ Upload failed, stopping
📋 Log written to: upload_logs/2025-10-29_16-10-30_upload.csv
```

Exit codes:
- `0` - Success (all operations completed)
- `1` - Error (validation failed, upload/download failed, or user cancelled)

---

## Directory Structure

```
inventory_2022/
├── upload_to_drive.py          # Upload script
├── download_from_drive.py      # Download script
├── upload_logs/                # Upload operation logs (CSV)
│   └── YYYY-MM-DD_HH-MM-SS_upload.csv
├── download_logs/              # Download operation logs (CSV)
│   └── YYYY-MM-DD_HH-MM-SS_download.csv
└── collab_results/             # Downloaded archives
    ├── experiment_archives/    # Experimental sessions
    │   └── YYYY-MM-DD-xxxxxx/
    └── training_archives/      # Production training sessions
        └── YYYY-MM-DD-xxxxxx_full_training/
```

---

## Audit Trail

All operations are logged to CSV files for complete audit trail:

```bash
# View recent uploads
ls -lht upload_logs/ | head

# View upload history
cat upload_logs/2025-10-29_16-04-15_upload.csv

# View recent downloads
ls -lht download_logs/ | head

# View download history
cat download_logs/2025-10-29_16-04-46_download.csv
```

---

## Troubleshooting

### "Failed to list remote sessions"

**Problem**: Cannot access Google Drive
```bash
❌ Failed to list remote sessions: directory not found
```

**Solution**:
1. Check rclone remote: `rclone listremotes`
2. Verify access: `rclone lsd gdrive:inventory_2022`
3. Reconfigure if needed: `rclone config`

### "File not found"

**Problem**: Local file doesn't exist
```bash
❌ Validation errors:
   File not found: src/missing_file.py
```

**Solution**: Check file path, ensure it exists:
```bash
ls -la src/missing_file.py
```

### "Rate limit exceeded"

**Problem**: Too many requests to Google Drive

**Solution**: Wait 60 seconds and retry

### Upload shows "changed" when file unchanged

**Problem**: Remote file has different checksum

**Solution**: This is normal if:
- File was edited directly in Google Drive
- File was uploaded from different location
- Remote file is corrupted

Force re-upload to sync:
```bash
python upload_to_drive.py --force src/file.py
```

---

## Performance

### Upload Performance

- **Change detection**: ~3 seconds per file (MD5 calculation + remote check)
- **Upload speed**: Depends on file size and connection
  - Small files (<1 MB): ~5-10 seconds
  - Medium files (1-10 MB): ~10-30 seconds
  - Large files (>10 MB): ~1-2 minutes

**Example**: 4 files (87 KB total) uploaded in ~15 seconds

### Download Performance

- **Session listing**: ~2-3 seconds
- **Download speed**: Depends on session size
  - Empty sessions: <1 second (creates marker directory)
  - Small sessions (<10 MB): ~5-15 seconds
  - Medium sessions (10-100 MB): ~30-60 seconds
  - Large sessions (>100 MB): Several minutes

---

## Best Practices

### For Uploads

1. **Upload only changed files** - Let checksum detection skip unchanged files
2. **Use relative paths** - Easier to read: `src/file.py` vs `/Users/.../src/file.py`
3. **Batch uploads** - Upload multiple files in one command
4. **Check logs** - Review upload logs after operations
5. **Force only when needed** - `--force` bypasses safety checks

### For Downloads

1. **Run regularly** - Download new results after Colab sessions
2. **Use auto-download** - Interactive mode only for selective downloads
3. **Archive type specific** - Download from specific archives to reduce clutter
4. **Check local first** - Use `ls collab_results/` to see what you have
5. **Review logs** - Check download logs for any failures

---

## Integration with Workflow

### Before Colab Training

Upload latest code to Google Drive:
```bash
python upload_to_drive.py \
  experimental_training_pipeline.ipynb \
  src/experimental_utils.py
```

### After Colab Training

Download results for local analysis:
```bash
python download_from_drive.py --archive-type experiment_archives
```

### Regular Sync

Download all new results:
```bash
# Download experimental results
python download_from_drive.py --archive-type experiment_archives

# Download production training results
python download_from_drive.py --archive-type training_archives
```

---

## Advanced Tips

### Check What's New Without Downloading

```bash
# List remote sessions
rclone lsd gdrive:inventory_2022/experiment_archives

# Check specific session contents
rclone tree gdrive:inventory_2022/experiment_archives/2025-10-29-abc123 --level 2
```

### Manual Upload (Outside Script)

```bash
# Upload single file
rclone copyto src/file.py gdrive:inventory_2022/src/file.py

# Upload entire directory
rclone copy src/ gdrive:inventory_2022/src/
```

### Manual Download (Outside Script)

```bash
# Download single session
rclone copy gdrive:inventory_2022/experiment_archives/2025-10-29-abc123 \
  collab_results/experiment_archives/2025-10-29-abc123
```

---

## Related Documentation

- **docs/RCLONE_USAGE_GUIDE.md** - Complete rclone usage guide for AI agents
- **docs/starting_doc.md** - Main project documentation
- **docs/EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md** - Experimental training infrastructure

---

## Changelog

### 2025-10-29 - Initial Release

**Features**:
- Upload script with MD5 checksum-based change detection
- Download script with folder existence checking
- CSV logging for both operations
- Fail-fast error handling
- Token-efficient rclone usage (no `--progress`)
- Auto-preserve directory structure
- Interactive download mode

**Testing**:
- ✅ Uploaded 4 files to Google Drive (2 changed, 2 skipped)
- ✅ Downloaded 1 new experimental session
- ✅ Verified no re-download of existing sessions
- ✅ CSV logs created successfully

---

**Status**: ✅ Production Ready
**Last Updated**: 2025-10-29
**Maintained By**: Biodata Inventory ML Team
