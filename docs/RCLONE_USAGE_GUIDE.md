# Rclone Usage Guide for Biodata Inventory Pipeline

**Created**: 2025-10-29
**Purpose**: Guidelines for AI agents using rclone to access Google Drive storage
**Status**: Active - Follow these rules for all rclone operations

---

## Overview

Rclone is used to access Google Drive storage for the biodata inventory ML pipeline. This guide establishes rules and best practices for AI agents to use rclone efficiently and safely.

### Remote Configuration

- **Remote Name**: `gdrive` (configured and verified)
- **Provider**: Google Drive
- **Access Level**: Full read/write access to inventory_2022 directory
- **Status**: ✅ Configured and tested (2025-10-29)

---

## Usage Rules for AI Agents

### Rule 1: Token Efficiency (CRITICAL)

**❌ AVOID** these flags unless explicitly requested by user:
- `--progress` - Generates excessive output, wastes tokens
- `--dry-run` - Useful for humans, but AI can preview with `lsf` or `tree` instead
- `-P` - Short form of `--progress`, avoid

**✅ USE** these efficient alternatives:
- `rclone lsf` - List files only, minimal output
- `rclone tree --level N` - Preview directory structure
- Direct operations without progress tracking

**Example - AVOID**:
```bash
# ❌ Wastes tokens with progress output
rclone copy gdrive:path /local/path --progress --dry-run
```

**Example - PREFER**:
```bash
# ✅ Efficient preview
rclone tree gdrive:path --level 2

# ✅ Direct copy without progress
rclone copy gdrive:path /local/path
```

### Rule 2: Read-Only Operations (Default)

**Always prefer read-only operations** unless user explicitly requests modifications:

**✅ Safe Operations** (use freely):
- `rclone ls` / `rclone lsf` / `rclone lsd` - List files/directories
- `rclone tree` - Show directory structure
- `rclone cat` - View file contents
- `rclone copy gdrive:remote /local` - Download from Drive to local
- `rclone size` - Check directory sizes

**⚠️ Requires User Confirmation**:
- `rclone copy /local gdrive:remote` - Upload to Drive
- `rclone move` - Moves files (deletes source)
- `rclone sync` - Mirrors directory (can delete files)
- `rclone delete` - Deletes files
- `rclone purge` - Deletes directory and contents

### Rule 3: Project-Specific Paths

**Primary Google Drive Paths**:
```
gdrive:inventory_2022/
├── experiment_archives/          # Experimental training results (TEST_MODE)
│   └── YYYY-MM-DD-xxxxxx/       # Session-specific archives
├── training_archives/            # Production training results
│   └── YYYY-MM-DD-xxxxxx_full_training/
├── data/                         # Training datasets
├── out/                          # Model outputs
├── docs/                         # Documentation
└── config/                       # Configuration files
```

**Local Mirror Paths**:
```
/Users/warren/development/GBC/inventory_2022/
├── collab_results/
│   ├── experiment_archives/     # Downloaded experimental results
│   └── training_archives/       # Downloaded production results
├── data/
├── out/
├── docs/
└── config/
```

### Rule 4: Common Operations

#### List Directory Contents
```bash
# List subdirectories only
rclone lsd gdrive:inventory_2022/experiment_archives

# List all files (names only, efficient)
rclone lsf gdrive:inventory_2022/experiment_archives/2025-10-29-abc123

# Show directory tree (limit depth to save tokens)
rclone tree gdrive:inventory_2022/experiment_archives --level 2
```

#### Download Files/Directories
```bash
# Download entire experimental session
rclone copy gdrive:inventory_2022/experiment_archives/2025-10-29-abc123 \
  collab_results/experiment_archives/2025-10-29-abc123

# Download specific file
rclone copy gdrive:inventory_2022/experiment_archives/2025-10-29-abc123/session_metadata.json \
  collab_results/experiment_archives/2025-10-29-abc123/
```

#### View File Contents
```bash
# View JSON metadata without downloading
rclone cat gdrive:inventory_2022/experiment_archives/2025-10-29-abc123/session_metadata.json

# View CSV results
rclone cat gdrive:inventory_2022/experiment_archives/2025-10-29-abc123/experiment_results.csv
```

#### Upload Files/Directories (Requires Confirmation)
```bash
# Upload experimental results (ask user first!)
rclone copy collab_results/experiment_archives/2025-10-29-abc123 \
  gdrive:inventory_2022/experiment_archives/2025-10-29-abc123
```

### Rule 5: Error Handling

**If rclone command fails**:
1. Check remote is configured: `rclone listremotes`
2. Verify path exists: `rclone lsd gdrive:inventory_2022`
3. Check connectivity: `rclone about gdrive:`
4. Report error to user with clear message

**Common Errors**:
- `directory not found` - Path may be incorrect or doesn't exist
- `rate limit exceeded` - Wait 1 minute and retry
- `authentication failed` - Remote needs reconfiguration (ask user)

### Rule 6: Optimization

**For Large Transfers** (only when needed):
```bash
# Multiple parallel transfers (faster)
rclone copy gdrive:path /local/path --transfers=8

# Faster directory listing
rclone copy gdrive:path /local/path --fast-list

# Larger chunks for big files
rclone copy gdrive:path /local/path --drive-chunk-size=64M
```

**Note**: Only use optimization flags when user reports slow performance.

---

## Use Cases for Biodata Inventory Pipeline

### Use Case 1: Retrieve Experimental Results

**Scenario**: User wants to analyze completed experimental training runs

**Steps**:
1. List available sessions: `rclone lsd gdrive:inventory_2022/experiment_archives`
2. Preview session contents: `rclone tree gdrive:inventory_2022/experiment_archives/SESSION_ID --level 2`
3. Download to local: `rclone copy gdrive:inventory_2022/experiment_archives/SESSION_ID collab_results/experiment_archives/SESSION_ID`
4. Analyze local files with Read tool

### Use Case 2: Check Archive Contents

**Scenario**: User wants to see what's in an archive without downloading

**Steps**:
1. Show structure: `rclone tree gdrive:inventory_2022/experiment_archives/SESSION_ID --level 2`
2. View metadata: `rclone cat gdrive:inventory_2022/experiment_archives/SESSION_ID/session_metadata.json`
3. View results: `rclone cat gdrive:inventory_2022/experiment_archives/SESSION_ID/experiment_results.csv`

### Use Case 3: Upload New Experimental Results

**Scenario**: Local experimental run completed, need to backup to Drive

**Steps**:
1. **Ask user for confirmation first**
2. Preview: `rclone tree collab_results/experiment_archives/SESSION_ID --level 2`
3. Upload: `rclone copy collab_results/experiment_archives/SESSION_ID gdrive:inventory_2022/experiment_archives/SESSION_ID`
4. Verify: `rclone lsf gdrive:inventory_2022/experiment_archives/SESSION_ID`

### Use Case 4: Retrieve Production Models

**Scenario**: User needs to download specific trained models

**Steps**:
1. List training archives: `rclone lsd gdrive:inventory_2022/training_archives`
2. Check archive contents: `rclone tree gdrive:inventory_2022/training_archives/SESSION_ID --level 2`
3. Download models: `rclone copy gdrive:inventory_2022/training_archives/SESSION_ID/models out/`
4. Verify checksums from metadata

---

## Safety Guidelines

### Before Any Write Operation

1. **Confirm with user** - Always ask before modifying Drive
2. **Verify paths** - Double-check source and destination
3. **Check conflicts** - Ensure not overwriting important files
4. **Document action** - Note what was uploaded/modified

### Never Do Without Explicit Permission

- ❌ Delete any files or directories
- ❌ Sync from local to Drive (could delete Drive files)
- ❌ Move files (deletes source)
- ❌ Modify production model directories
- ❌ Overwrite existing archives

### Always Safe to Do

- ✅ List directory contents
- ✅ Download files from Drive to local
- ✅ View file contents with `cat`
- ✅ Check directory sizes
- ✅ Preview directory structures

---

## Quick Reference

### Most Common Commands

```bash
# List experimental sessions
rclone lsd gdrive:inventory_2022/experiment_archives

# Show session structure
rclone tree gdrive:inventory_2022/experiment_archives/SESSION_ID --level 2

# View session metadata
rclone cat gdrive:inventory_2022/experiment_archives/SESSION_ID/session_metadata.json

# Download session results
rclone copy gdrive:inventory_2022/experiment_archives/SESSION_ID \
  collab_results/experiment_archives/SESSION_ID

# List all remotes (verify configuration)
rclone listremotes

# Check Google Drive space
rclone about gdrive:
```

### Efficient Token Usage

**Instead of `--dry-run`**:
```bash
# Preview with tree
rclone tree SOURCE_PATH --level 2

# List files that would be copied
rclone lsf SOURCE_PATH
```

**Instead of `--progress`**:
```bash
# Just run the command directly
rclone copy SOURCE DEST

# Check completion with ls
rclone lsf DEST
```

---

## Troubleshooting

### Command Fails Silently

**Problem**: Rclone command returns "Tool ran without output or errors" but nothing happened

**Solutions**:
- Check if source path exists: `rclone lsd gdrive:path/to/parent`
- Verify remote: `rclone listremotes`
- Add `2>&1` to capture stderr: `rclone copy ... 2>&1`

### Path Not Found

**Problem**: "directory not found" error

**Solutions**:
- Use `rclone tree gdrive:inventory_2022 --level 1` to see available paths
- Check for typos in path
- Verify using Google Drive web interface

### Rate Limiting

**Problem**: "rate limit exceeded" error

**Solutions**:
- Wait 60 seconds and retry
- Reduce `--transfers` value
- Spread operations over time

---

## Integration with Project Workflow

### Experimental Training Workflow

1. **Before Training**: Check existing archives
   ```bash
   rclone lsd gdrive:inventory_2022/experiment_archives
   ```

2. **After Training** (in Colab notebook):
   - Notebook automatically uploads to `gdrive:inventory_2022/experiment_archives/SESSION_ID`

3. **Analysis** (local):
   ```bash
   rclone copy gdrive:inventory_2022/experiment_archives/SESSION_ID \
     collab_results/experiment_archives/SESSION_ID
   ```

### Production Training Workflow

1. **Before Training**: Verify no conflicts
2. **After Training**: Archive uploaded by notebook
3. **Deployment**: Download models from archives as needed

---

## Document Maintenance

**Update this guide when**:
- New archive types are added
- Directory structure changes
- New use cases emerge
- Best practices evolve
- User feedback suggests improvements

**Last Updated**: 2025-10-29
**Status**: Active
**Owned by**: Biodata Inventory ML Team

---

## Related Documentation

- `docs/starting_doc.md` - Main project reference
- `docs/EXPERIMENTAL_INFRASTRUCTURE_PROGRESS.md` - Experimental training infrastructure
- `docs/COMPREHENSIVE_IMPLEMENTATION_PLAN.md` - 3-phase improvement roadmap
- Rclone skill documentation in `.claude/commands/rclone/`

---

**Remember**: Efficiency is key. Avoid `--progress` and `--dry-run` to minimize token usage. Use `tree`, `lsf`, and direct operations instead.
