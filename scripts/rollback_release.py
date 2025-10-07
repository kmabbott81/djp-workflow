#!/usr/bin/env python3
"""Rollback Railway deployment to previous image.

Usage:
    python scripts/rollback_release.py --deployment-id <deployment_id>

Environment:
    RAILWAY_TOKEN: Railway API token
"""

import argparse
import os
import sys
from datetime import datetime


def get_railway_token():
    """Get Railway token from environment."""
    token = os.getenv("RAILWAY_TOKEN")
    if not token:
        print("ERROR: RAILWAY_TOKEN environment variable not set")
        sys.exit(1)
    return token


def rollback_deployment(deployment_id: str, token: str):
    """Rollback to previous deployment via Railway API.

    Note: Railway doesn't have a direct rollback API. This script
    documents the failed deployment and provides rollback instructions.
    """
    print(f"[INFO] Recording rollback event for deployment: {deployment_id}")

    # Create rollback notes document
    os.makedirs("docs/evidence/sprint-51/phase3", exist_ok=True)
    rollback_path = "docs/evidence/sprint-51/phase3/ROLLBACK-NOTES.md"

    with open(rollback_path, "w") as f:
        f.write("# Rollback Notes\n\n")
        f.write(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"**Failed Deployment ID:** {deployment_id}\n\n")
        f.write("## Reason\n\n")
        f.write("Deployment failed smoke tests. Automated rollback triggered.\n\n")
        f.write("## Manual Rollback Steps\n\n")
        f.write("1. Go to Railway dashboard: https://railway.app/project/relay-backend\n")
        f.write("2. Navigate to Deployments tab\n")
        f.write(f"3. Find deployment ID: {deployment_id}\n")
        f.write("4. Click 'Redeploy' on the previous successful deployment\n\n")
        f.write("## Verification\n\n")
        f.write("After rollback:\n")
        f.write("```bash\n")
        f.write("curl -s https://relay-production-f2a6.up.railway.app/_stcore/health\n")
        f.write('# Expected: {"ok":true}\n')
        f.write("```\n\n")
        f.write("## Railway CLI Rollback\n\n")
        f.write("```bash\n")
        f.write("# List recent deployments\n")
        f.write("railway status\n\n")
        f.write("# Redeploy previous version\n")
        f.write("railway redeploy --previous\n")
        f.write("```\n")

    print(f"[INFO] Rollback notes written to: {rollback_path}")

    # In a real implementation, you would call Railway API here
    # For now, we document and exit with error to fail the CI pipeline
    print("[ERROR] Deployment failed. Manual rollback required.")
    print(f"[ERROR] See: {rollback_path}")

    return False


def main():
    parser = argparse.ArgumentParser(description="Rollback Railway deployment")
    parser.add_argument("--deployment-id", required=True, help="Deployment ID to rollback")
    args = parser.parse_args()

    token = get_railway_token()
    success = rollback_deployment(args.deployment_id, token)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
