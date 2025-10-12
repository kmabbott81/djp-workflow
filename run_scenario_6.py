#!/usr/bin/env python3
"""Run only Scenario 6 (validation tests) with environment from .env.e2e"""
import os
import subprocess
import sys
from pathlib import Path

# Load .env.e2e
env_file = Path(__file__).parent / ".env.e2e"
if not env_file.exists():
    print(f"ERROR: {env_file} not found")
    sys.exit(1)

print(f"Loading environment from {env_file}")
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key] = value
            if key in ["E2E_WORKSPACE_ID", "E2E_ACTOR_ID", "E2E_RECIPIENT_EMAIL"]:
                print(f"  {key}={value}")

print("\nRunning Scenario 6 (validation tests)...")
print("=" * 70)

# Run only Scenario 6
result = subprocess.run(
    [sys.executable, "scripts/e2e_gmail_test.py", "--scenarios", "6", "--verbose"],
    env=os.environ,
)

sys.exit(result.returncode)
