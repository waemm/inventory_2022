#!/usr/bin/env python3
"""
Upload files to Google Drive via rclone, maintaining directory structure.

Usage:
    python upload_to_drive.py file1.py src/file2.py docs/file3.md
    python upload_to_drive.py --force src/experimental_utils.py

Features:
- Preserves directory structure (src/file.py -> gdrive:inventory_2022/src/file.py)
- Files without paths go to root (file.py -> gdrive:inventory_2022/file.py)
- Change detection via MD5 checksums (skip if unchanged)
- CSV logging with timestamp, file, size, status, checksum
- Stops on first error
"""

import argparse
import csv
import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# Configuration
REMOTE_NAME = "gdrive"
REMOTE_BASE = "inventory_2022"
LOG_DIR = Path("upload_logs")
PROJECT_ROOT = Path(__file__).parent.resolve()


def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


def get_remote_checksum(remote_path: str) -> Optional[str]:
    """Get MD5 checksum of remote file via rclone."""
    try:
        result = subprocess.run(
            ['rclone', 'md5sum', remote_path],
            capture_output=True,
            text=True,
            check=True
        )
        # Output format: "checksum  filename"
        if result.stdout.strip():
            return result.stdout.split()[0]
        return None
    except subprocess.CalledProcessError:
        # File doesn't exist remotely
        return None


def file_needs_upload(local_path: Path, remote_path: str, force: bool) -> Tuple[bool, str]:
    """
    Determine if file needs uploading.

    Returns:
        (needs_upload, reason)
    """
    if force:
        return True, "forced"

    local_checksum = calculate_md5(local_path)
    remote_checksum = get_remote_checksum(remote_path)

    if remote_checksum is None:
        return True, "new_file"
    elif local_checksum != remote_checksum:
        return True, "changed"
    else:
        return False, "unchanged"


def upload_file(local_path: Path, remote_path: str, force: bool) -> dict:
    """
    Upload a single file to Google Drive.

    Returns:
        dict with upload metadata for logging
    """
    # Check if file needs upload
    needs_upload, reason = file_needs_upload(local_path, remote_path, force)

    if not needs_upload:
        print(f"⏭️  Skipping {local_path} ({reason})")
        return {
            'timestamp': datetime.now().isoformat(),
            'file_path': str(local_path.relative_to(PROJECT_ROOT)),
            'size_bytes': local_path.stat().st_size,
            'status': 'skipped',
            'checksum': calculate_md5(local_path)
        }

    # Upload file
    print(f"📤 Uploading {local_path} -> {remote_path} ({reason})...")

    try:
        # Use copyto to upload single file to exact destination
        subprocess.run(
            ['rclone', 'copyto', str(local_path), remote_path],
            check=True,
            capture_output=True,
            text=True
        )

        checksum = calculate_md5(local_path)
        print(f"✅ Success: {local_path}")

        return {
            'timestamp': datetime.now().isoformat(),
            'file_path': str(local_path.relative_to(PROJECT_ROOT)),
            'size_bytes': local_path.stat().st_size,
            'status': 'success',
            'checksum': checksum
        }

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        print(f"❌ Failed: {local_path}")
        print(f"   Error: {error_msg}")

        return {
            'timestamp': datetime.now().isoformat(),
            'file_path': str(local_path.relative_to(PROJECT_ROOT)),
            'size_bytes': local_path.stat().st_size,
            'status': f'failed: {error_msg}',
            'checksum': ''
        }


def construct_remote_path(local_path: Path) -> str:
    """
    Construct remote path from local path, preserving directory structure.

    Examples:
        src/file.py -> gdrive:inventory_2022/src/file.py
        file.py -> gdrive:inventory_2022/file.py
        docs/guide.md -> gdrive:inventory_2022/docs/guide.md
    """
    try:
        # Get path relative to project root
        rel_path = local_path.relative_to(PROJECT_ROOT)
    except ValueError:
        # File is outside project root, use just filename
        rel_path = local_path.name

    # Construct remote path
    return f"{REMOTE_NAME}:{REMOTE_BASE}/{rel_path}"


def validate_files(file_paths: List[str]) -> List[Path]:
    """
    Validate that all files exist and are readable.

    Returns:
        List of validated Path objects

    Raises:
        SystemExit if any file is invalid
    """
    validated = []
    errors = []

    for file_str in file_paths:
        file_path = Path(file_str)

        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
        elif not file_path.is_file():
            errors.append(f"Not a file: {file_path}")
        elif not file_path.stat().st_size > 0:
            errors.append(f"Empty file: {file_path}")
        else:
            # Resolve to absolute path
            validated.append(file_path.resolve())

    if errors:
        print("❌ Validation errors:", file=sys.stderr)
        for error in errors:
            print(f"   {error}", file=sys.stderr)
        sys.exit(1)

    return validated


def write_log(log_entries: List[dict]) -> None:
    """Write upload log to CSV file."""
    LOG_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = LOG_DIR / f"{timestamp}_upload.csv"

    with open(log_file, 'w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['timestamp', 'file_path', 'size_bytes', 'status', 'checksum']
        )
        writer.writeheader()
        writer.writerows(log_entries)

    print(f"\n📋 Log written to: {log_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload files to Google Drive via rclone",
        epilog="Examples:\n"
               "  %(prog)s src/file.py docs/guide.md\n"
               "  %(prog)s --force experimental_training_pipeline.ipynb\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'files',
        nargs='+',
        help='Files to upload (paths relative to project root or absolute)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip change detection, always upload'
    )

    args = parser.parse_args()

    # Validate files
    print(f"🔍 Validating {len(args.files)} file(s)...")
    validated_files = validate_files(args.files)
    print(f"✅ All files valid\n")

    # Upload files
    log_entries = []

    for local_path in validated_files:
        remote_path = construct_remote_path(local_path)

        result = upload_file(local_path, remote_path, args.force)
        log_entries.append(result)

        # Stop on first error
        if result['status'].startswith('failed'):
            print(f"\n❌ Upload failed, stopping")
            write_log(log_entries)
            sys.exit(1)

    # Write log
    write_log(log_entries)

    # Summary
    successful = sum(1 for e in log_entries if e['status'] == 'success')
    skipped = sum(1 for e in log_entries if e['status'] == 'skipped')

    print(f"\n✅ Upload complete:")
    print(f"   Uploaded: {successful}")
    print(f"   Skipped: {skipped}")
    print(f"   Total: {len(log_entries)}")


if __name__ == '__main__':
    main()
