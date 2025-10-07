#!/usr/bin/env python3
"""Automated Postgres backup script.

Creates compressed pg_dump backups and stores them with 30-day retention.

Usage:
    python scripts/db_backup.py --output-dir /backups

Environment:
    DATABASE_URL: Postgres connection string (or DATABASE_PUBLIC_URL for Railway)
"""

import argparse
import gzip
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_database_url():
    """Get database URL from environment."""
    db_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
    if not db_url:
        print("ERROR: DATABASE_URL or DATABASE_PUBLIC_URL environment variable not set")
        sys.exit(1)
    return db_url


def create_backup(output_dir: Path, database_url: str) -> Path:
    """Create compressed pg_dump backup.

    Args:
        output_dir: Directory to store backup
        database_url: Postgres connection string

    Returns:
        Path to created backup file
    """
    # Create output directory with date
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    backup_dir = output_dir / date_str
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Backup filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"relay_backup_{timestamp}.sql.gz"

    print(f"[INFO] Creating backup: {backup_file}")

    # Run pg_dump with compression
    try:
        # Use pg_dump with --clean --if-exists for schema+data
        dump_cmd = ["pg_dump", "--clean", "--if-exists", "--no-owner", "--no-acl", database_url]

        with gzip.open(backup_file, "wb") as f:
            subprocess.run(dump_cmd, stdout=f, check=True, stderr=subprocess.PIPE)

        file_size_mb = backup_file.stat().st_size / (1024 * 1024)
        print(f"[INFO] Backup created: {backup_file} ({file_size_mb:.2f} MB)")

        return backup_file

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] pg_dump failed: {e.stderr.decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        sys.exit(1)


def cleanup_old_backups(output_dir: Path, retention_days: int = 30):
    """Remove backups older than retention period.

    Args:
        output_dir: Directory containing backups
        retention_days: Number of days to retain backups
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")

    print(f"[INFO] Cleaning up backups older than {cutoff_str}")

    removed_count = 0
    for backup_date_dir in output_dir.iterdir():
        if not backup_date_dir.is_dir():
            continue

        # Check if directory name is a date string older than cutoff
        try:
            dir_date = datetime.strptime(backup_date_dir.name, "%Y-%m-%d")
            if dir_date < cutoff_date:
                print(f"[INFO] Removing old backup: {backup_date_dir}")
                for backup_file in backup_date_dir.iterdir():
                    backup_file.unlink()
                backup_date_dir.rmdir()
                removed_count += 1
        except ValueError:
            # Not a date directory, skip
            pass

    print(f"[INFO] Removed {removed_count} old backup(s)")


def main():
    parser = argparse.ArgumentParser(description="Backup Postgres database")
    parser.add_argument(
        "--output-dir",
        default="/backups",
        help="Output directory for backups (default: /backups)",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Number of days to retain backups (default: 30)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    database_url = get_database_url()

    # Create backup
    backup_file = create_backup(output_dir, database_url)

    # Cleanup old backups
    cleanup_old_backups(output_dir, args.retention_days)

    print(f"[INFO] Backup complete: {backup_file}")
    print(f"[INFO] Retention: {args.retention_days} days")


if __name__ == "__main__":
    main()
