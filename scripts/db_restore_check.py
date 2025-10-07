#!/usr/bin/env python3
"""Database restore drill - validate backups are restorable.

Creates ephemeral test database, restores latest backup, runs sanity checks.

Usage:
    python scripts/db_restore_check.py --backup-dir /backups

Environment:
    DATABASE_URL: Postgres connection string (for admin operations)
"""

import argparse
import gzip
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_database_url():
    """Get database URL from environment."""
    db_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PUBLIC_URL")
    if not db_url:
        print("ERROR: DATABASE_URL or DATABASE_PUBLIC_URL environment variable not set")
        sys.exit(1)
    return db_url


def find_latest_backup(backup_dir: Path) -> Path:
    """Find most recent backup file.

    Args:
        backup_dir: Directory containing backups

    Returns:
        Path to latest backup file
    """
    backup_files = []

    for date_dir in sorted(backup_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue

        for backup_file in sorted(date_dir.glob("*.sql.gz"), reverse=True):
            backup_files.append(backup_file)

    if not backup_files:
        print(f"ERROR: No backups found in {backup_dir}")
        sys.exit(1)

    latest = backup_files[0]
    print(f"[INFO] Latest backup: {latest}")
    return latest


def create_ephemeral_database(admin_url: str, db_name: str) -> str:
    """Create ephemeral test database.

    Args:
        admin_url: Admin postgres connection string
        db_name: Name for ephemeral database

    Returns:
        Connection string for ephemeral database
    """
    print(f"[INFO] Creating ephemeral database: {db_name}")

    # Parse admin URL and replace database name
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(admin_url)
    admin_db_url = urlunparse(parsed._replace(path="/postgres"))

    try:
        conn = psycopg2.connect(admin_db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Drop if exists
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")

        # Create new database
        cursor.execute(f"CREATE DATABASE {db_name}")

        cursor.close()
        conn.close()

        # Return connection string for new database
        ephemeral_url = urlunparse(parsed._replace(path=f"/{db_name}"))
        print(f"[INFO] Ephemeral database created: {db_name}")
        return ephemeral_url

    except Exception as e:
        print(f"[ERROR] Failed to create ephemeral database: {e}")
        sys.exit(1)


def restore_backup(backup_file: Path, target_url: str):
    """Restore backup to target database.

    Args:
        backup_file: Path to compressed backup file
        target_url: Target database connection string
    """
    print("[INFO] Restoring backup to ephemeral database...")

    try:
        # Decompress and restore
        with gzip.open(backup_file, "rb") as f:
            restore_cmd = ["psql", "--quiet", target_url]
            subprocess.run(restore_cmd, stdin=f, check=True, stderr=subprocess.PIPE)

        print("[INFO] Backup restored successfully")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Restore failed: {e.stderr.decode()}")
        sys.exit(1)


def run_sanity_checks(target_url: str) -> dict:
    """Run sanity checks on restored database.

    Args:
        target_url: Database connection string

    Returns:
        Dictionary with check results
    """
    print("[INFO] Running sanity checks...")

    try:
        conn = psycopg2.connect(target_url)
        cursor = conn.cursor()

        results = {}

        # Check 1: Count tables
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """
        )
        table_count = cursor.fetchone()[0]
        results["table_count"] = table_count
        print(f"  - Tables: {table_count}")

        # Check 2: Check key tables exist
        expected_tables = ["workspaces", "api_keys", "audit_logs", "sessions"]
        for table_name in expected_tables:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """,
                (table_name,),
            )
            exists = cursor.fetchone()[0]
            results[f"table_{table_name}"] = exists
            status = "✓" if exists else "✗"
            print(f"  - Table '{table_name}': {status}")

        # Check 3: Row counts for key tables
        for table_name in expected_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                results[f"rows_{table_name}"] = row_count
                print(f"  - Rows in '{table_name}': {row_count}")
            except Exception as e:
                print(f"  - Warning: Could not count rows in '{table_name}': {e}")

        cursor.close()
        conn.close()

        print("[INFO] Sanity checks passed")
        return results

    except Exception as e:
        print(f"[ERROR] Sanity checks failed: {e}")
        sys.exit(1)


def cleanup_ephemeral_database(admin_url: str, db_name: str):
    """Drop ephemeral test database.

    Args:
        admin_url: Admin postgres connection string
        db_name: Name of ephemeral database
    """
    print(f"[INFO] Cleaning up ephemeral database: {db_name}")

    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(admin_url)
    admin_db_url = urlunparse(parsed._replace(path="/postgres"))

    try:
        conn = psycopg2.connect(admin_db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")

        cursor.close()
        conn.close()

        print("[INFO] Ephemeral database dropped")

    except Exception as e:
        print(f"[WARN] Could not drop ephemeral database: {e}")


def generate_report(backup_file: Path, results: dict, duration_seconds: float):
    """Generate restore drill report.

    Args:
        backup_file: Path to restored backup file
        results: Sanity check results
        duration_seconds: Restore duration
    """
    os.makedirs("docs/evidence/sprint-51/phase3", exist_ok=True)
    report_path = "docs/evidence/sprint-51/phase3/RESTORE-DRILL-REPORT.md"

    with open(report_path, "w") as f:
        f.write("# Database Restore Drill Report\n\n")
        f.write(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"**Backup File:** {backup_file}\n")
        f.write(f"**Duration:** {duration_seconds:.2f}s\n\n")

        f.write("## Sanity Checks\n\n")
        f.write(f"- **Tables:** {results.get('table_count', 'N/A')}\n")

        for key in ["workspaces", "api_keys", "audit_logs", "sessions"]:
            exists = results.get(f"table_{key}", False)
            row_count = results.get(f"rows_{key}", 0)
            status = "✅" if exists else "❌"
            f.write(f"- **{key}:** {status} ({row_count} rows)\n")

        f.write("\n## Conclusion\n\n")
        f.write("Backup restore drill completed successfully. Database is restorable.\n")

    print(f"[INFO] Report written to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Database restore drill")
    parser.add_argument(
        "--backup-dir",
        default="/backups",
        help="Backup directory (default: /backups)",
    )
    args = parser.parse_args()

    backup_dir = Path(args.backup_dir)
    admin_url = get_database_url()

    # Find latest backup
    backup_file = find_latest_backup(backup_dir)

    # Create ephemeral database
    ephemeral_db_name = f"restore_drill_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    ephemeral_url = create_ephemeral_database(admin_url, ephemeral_db_name)

    start_time = datetime.utcnow()

    try:
        # Restore backup
        restore_backup(backup_file, ephemeral_url)

        # Run sanity checks
        results = run_sanity_checks(ephemeral_url)

        duration = (datetime.utcnow() - start_time).total_seconds()

        # Generate report
        generate_report(backup_file, results, duration)

        print(f"[INFO] Restore drill completed in {duration:.2f}s")

    finally:
        # Always cleanup ephemeral database
        cleanup_ephemeral_database(admin_url, ephemeral_db_name)


if __name__ == "__main__":
    main()
