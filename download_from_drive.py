#!/usr/bin/env python3
"""
Download new session archives from Google Drive via rclone.

Usage:
    python download_from_drive.py --archive-type experiment_archives
    python download_from_drive.py --archive-type training_archives --interactive
    python download_from_drive.py --archive-type path/to/custom/archives

Features:
- Lists sessions in specified archive directory on Google Drive
- Downloads only NEW sessions (folders that don't exist locally)
- Interactive mode for confirmation before download
- CSV logging with timestamp, session_id, archive_type, size, status
- Stops on first error
"""

import argparse
import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Configuration
REMOTE_NAME = "gdrive"
REMOTE_BASE = "inventory_2022"
LOCAL_BASE = Path("collab_results")
LOG_DIR = Path("download_logs")


def list_remote_sessions(archive_type: str) -> List[str]:
    """
    List session directories in remote archive.

    Returns:
        List of session directory names (e.g., ['2025-10-29-abc123', ...])
    """
    remote_path = f"{REMOTE_NAME}:{REMOTE_BASE}/{archive_type}"

    try:
        result = subprocess.run(
            ['rclone', 'lsd', remote_path],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse lsd output (format: "          -1 2025-10-29 12:34:56        -1 session_name")
        sessions = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Session name is the last field
                parts = line.split()
                if parts:
                    sessions.append(parts[-1])

        return sessions

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        print(f"❌ Failed to list remote sessions: {error_msg}", file=sys.stderr)
        sys.exit(1)


def get_new_sessions(archive_type: str, remote_sessions: List[str]) -> List[str]:
    """
    Filter remote sessions to only those that don't exist locally.

    Returns:
        List of new session names
    """
    local_archive_dir = LOCAL_BASE / archive_type
    local_archive_dir.mkdir(parents=True, exist_ok=True)

    new_sessions = []
    for session in remote_sessions:
        local_session_dir = local_archive_dir / session
        if not local_session_dir.exists():
            new_sessions.append(session)

    return new_sessions


def get_remote_size(remote_path: str) -> int:
    """
    Get total size of remote directory in bytes.

    Returns:
        Size in bytes, or 0 if unable to determine
    """
    try:
        result = subprocess.run(
            ['rclone', 'size', remote_path, '--json'],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse JSON output
        import json
        data = json.loads(result.stdout)
        return data.get('bytes', 0)

    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return 0


def download_session(session_id: str, archive_type: str) -> dict:
    """
    Download a single session from Google Drive.

    Returns:
        dict with download metadata for logging
    """
    remote_path = f"{REMOTE_NAME}:{REMOTE_BASE}/{archive_type}/{session_id}"
    local_path = LOCAL_BASE / archive_type / session_id

    # Ensure local directory exists
    local_path.parent.mkdir(parents=True, exist_ok=True)

    # Get size before download
    size_bytes = get_remote_size(remote_path)

    print(f"📥 Downloading {session_id}...")

    try:
        # Create local directory (even if remote is empty)
        local_path.mkdir(parents=True, exist_ok=True)

        # Use rclone copy to download entire session directory
        subprocess.run(
            ['rclone', 'copy', remote_path, str(local_path)],
            check=True,
            capture_output=True,
            text=True
        )

        print(f"✅ Success: {session_id}")

        return {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'archive_type': archive_type,
            'size_bytes': size_bytes,
            'status': 'success'
        }

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        print(f"❌ Failed: {session_id}")
        print(f"   Error: {error_msg}")

        return {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'archive_type': archive_type,
            'size_bytes': size_bytes,
            'status': f'failed: {error_msg}'
        }


def write_log(log_entries: List[dict]) -> None:
    """Write download log to CSV file."""
    LOG_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = LOG_DIR / f"{timestamp}_download.csv"

    with open(log_file, 'w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['timestamp', 'session_id', 'archive_type', 'size_bytes', 'status']
        )
        writer.writeheader()
        writer.writerows(log_entries)

    print(f"\n📋 Log written to: {log_file}")


def confirm_download(sessions: List[str]) -> bool:
    """
    Ask user to confirm download in interactive mode.

    Returns:
        True if user confirms, False otherwise
    """
    print("\nNew sessions found:")
    for i, session in enumerate(sessions, 1):
        print(f"  {i}. {session}")

    response = input("\nDownload all new sessions? (y/n): ").strip().lower()
    return response in ['y', 'yes']


def main():
    parser = argparse.ArgumentParser(
        description="Download new session archives from Google Drive via rclone",
        epilog="Examples:\n"
               "  %(prog)s --archive-type experiment_archives\n"
               "  %(prog)s --archive-type training_archives --interactive\n"
               "  %(prog)s --archive-type path/to/custom\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--archive-type',
        required=True,
        help='Archive directory to download from (e.g., experiment_archives, training_archives)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Ask for confirmation before downloading'
    )

    args = parser.parse_args()

    # List remote sessions
    print(f"🔍 Listing sessions in {args.archive_type}...")
    remote_sessions = list_remote_sessions(args.archive_type)

    if not remote_sessions:
        print(f"ℹ️  No sessions found in remote archive")
        sys.exit(0)

    print(f"✅ Found {len(remote_sessions)} total session(s)")

    # Find new sessions
    print(f"\n🔍 Checking for new sessions...")
    new_sessions = get_new_sessions(args.archive_type, remote_sessions)

    if not new_sessions:
        print(f"ℹ️  No new sessions to download (all {len(remote_sessions)} already exist locally)")
        sys.exit(0)

    print(f"✅ Found {len(new_sessions)} new session(s)")

    # Interactive confirmation
    if args.interactive:
        if not confirm_download(new_sessions):
            print("❌ Download cancelled")
            sys.exit(0)

    # Download sessions
    print(f"\n📥 Downloading {len(new_sessions)} session(s)...\n")
    log_entries = []

    for session_id in new_sessions:
        result = download_session(session_id, args.archive_type)
        log_entries.append(result)

        # Stop on first error
        if result['status'].startswith('failed'):
            print(f"\n❌ Download failed, stopping")
            write_log(log_entries)
            sys.exit(1)

    # Write log
    write_log(log_entries)

    # Summary
    total_size = sum(e['size_bytes'] for e in log_entries if e['status'] == 'success')
    size_mb = total_size / (1024 * 1024)

    print(f"\n✅ Download complete:")
    print(f"   Sessions: {len(log_entries)}")
    print(f"   Total size: {size_mb:.2f} MB")
    print(f"   Location: {LOCAL_BASE / args.archive_type}")


if __name__ == '__main__':
    main()
