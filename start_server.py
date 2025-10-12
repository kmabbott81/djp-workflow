"""Start OAuth server with environment from .env.e2e"""
import os
from pathlib import Path

import uvicorn

# Load .env.e2e
env_file = Path(__file__).parent / ".env.e2e"
if env_file.exists():
    print(f"Loading environment from {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
                if key in ["GOOGLE_CLIENT_ID", "REDIS_URL", "DATABASE_URL"]:
                    print(f"  {key}={'*' * 20}...")
else:
    print(f"ERROR: {env_file} not found")
    exit(1)

print("\nStarting OAuth server on port 8003...")
print(
    "Visit: http://localhost:8003/oauth/google/authorize?workspace_id=test-workspace-e2e&redirect_uri=http://localhost:8003/oauth/google/callback\n"
)

uvicorn.run("src.webapi:app", host="127.0.0.1", port=8003, log_level="info")
