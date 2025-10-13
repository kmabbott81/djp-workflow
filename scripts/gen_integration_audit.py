#!/usr/bin/env python3
"""Generate monthly integration docs audit report.

This script creates a checklist-based audit report for reviewing
integration documentation drift. It checks for the existence and
recent changes to integration-critical files.
"""
import subprocess
from datetime import datetime
from pathlib import Path

# Paths to monitor for integration changes
INTEGRATION_PATHS = [
    "Dockerfile",
    ".github/workflows",
    "src/webapi.py",
    "src/telemetry",
    "src/actions/adapters",
    "src/db",
    "src/auth",
    "requirements.txt",
    "requirements.in",
    "pyproject.toml",
    "observability",
    "prometheus.yml",
    "docs/ops/INTEGRATIONS.md",
    "docs/ops/integrations",
]


def get_last_commit_info(path: str) -> str:
    """Get last commit info for a path using git."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h %ai", "--", path],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return "(no commits)"
    except Exception:
        return "(git unavailable)"


def path_exists(path: str) -> bool:
    """Check if path exists."""
    return Path(path).exists()


def main():
    """Generate and print audit report."""
    print("# Monthly Integrations Audit\n")
    print(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n")

    print("## Quick Checklist\n")
    print("Please review the following items:\n")
    print("- [ ] **INTEGRATIONS.md** - Updated if any integration changed")
    print("- [ ] **One-pagers** - Reflect current env vars, secrets, and config")
    print("- [ ] **Observability** - Dashboards/alerts match recording rules")
    print("- [ ] **Railway** - Environment variables in docs match service settings")
    print("- [ ] **GitHub Actions** - Workflow var gates documented correctly")
    print("- [ ] **Docker** - Dockerfile changes reflected in DOCKER.md")
    print("- [ ] **Dependencies** - requirements.txt changes noted if relevant\n")

    print("## File Change Signals\n")
    print("Integration-critical files and their last changes:\n")

    for path in INTEGRATION_PATHS:
        exists = "✅ present" if path_exists(path) else "❌ missing"
        last_change = get_last_commit_info(path)
        print(f"- **`{path}`**: {exists}")
        print(f"  - Last change: `{last_change}`")

    print("\n## Integration-Specific Review Points\n")

    print("### Docker")
    print("- [ ] `EXPOSE` port matches docs")
    print("- [ ] Health check configuration documented")
    print("- [ ] Multi-stage build steps explained\n")

    print("### GitHub Actions")
    print("- [ ] New workflows have var gates documented")
    print("- [ ] Secrets usage updated in GITHUB_ACTIONS.md")
    print("- [ ] Cron schedules match documentation\n")

    print("### Railway")
    print("- [ ] All environment variables in table")
    print("- [ ] New services added to architecture diagram")
    print("- [ ] Health endpoint path current\n")

    print("### Redis")
    print("- [ ] Usage patterns documented (rate limit, OAuth state, etc.)")
    print("- [ ] Connection URL format correct\n")

    print("### Postgres")
    print("- [ ] Table schema changes noted")
    print("- [ ] Backup strategy current\n")

    print("### OpenAI")
    print("- [ ] Model name current (gpt-4o)")
    print("- [ ] Cost estimates updated")
    print("- [ ] API key security practices correct\n")

    print("### Observability")
    print("- [ ] New metrics added to examples")
    print("- [ ] PromQL queries tested and accurate")
    print("- [ ] Alert rules match prometheus-alerts.yml\n")

    print("### Codespaces")
    print("- [ ] Dev UI instructions current")
    print("- [ ] Port forwarding setup documented\n")

    print("## Suggested Actions\n")
    print("1. **Review changed files** - If any file above changed without docs update, create PR")
    print("2. **Test verify commands** - Run 60-second verification steps from one-pagers")
    print("3. **Check Railway dashboard** - Ensure env vars match RAILWAY.md table")
    print("4. **Run PromQL samples** - Verify Observability examples still work")
    print("5. **Update architecture diagram** - If new services added to Railway\n")

    print("## How to Update Docs\n")
    print("```bash")
    print("# Edit the relevant one-pager")
    print("vim docs/ops/integrations/DOCKER.md  # or RAILWAY.md, etc.")
    print("")
    print("# Update the master index if needed")
    print("vim docs/ops/INTEGRATIONS.md")
    print("")
    print("# Create PR")
    print("git checkout -b docs/update-integrations-audit-YYYY-MM")
    print("git add docs/ops/")
    print('git commit -m "docs: update integration docs per monthly audit"')
    print("git push origin docs/update-integrations-audit-YYYY-MM")
    print("```\n")

    print("---")
    print("*This audit is generated automatically by `.github/workflows/integration-docs-audit.yml`*")


if __name__ == "__main__":
    main()
