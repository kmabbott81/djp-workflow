#!/usr/bin/env python3
"""Generate GitHub release notes from CHANGELOG.md.

Usage:
    python scripts/release_notes.py 1.0.0
    python scripts/release_notes.py --latest
"""

import argparse
import re
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def read_changelog() -> str:
    """Read CHANGELOG.md contents."""
    changelog_file = get_project_root() / "CHANGELOG.md"
    if not changelog_file.exists():
        raise FileNotFoundError("CHANGELOG.md not found")
    return changelog_file.read_text(encoding="utf-8")


def extract_version_notes(changelog: str, version: str | None = None) -> tuple[str, str]:
    """Extract release notes for a specific version or the latest.

    Returns:
        Tuple of (version, notes)
    """
    # Split by version headers
    version_pattern = r"## \[([^\]]+)\] - (\d{4}-\d{2}-\d{2})"
    sections = re.split(version_pattern, changelog)

    # sections will be: [header, version1, date1, content1, version2, date2, content2, ...]
    if len(sections) < 4:
        raise ValueError("No version sections found in CHANGELOG.md")

    # Parse versions
    versions = []
    for i in range(1, len(sections), 3):
        if i + 2 < len(sections):
            versions.append({"version": sections[i], "date": sections[i + 1], "content": sections[i + 2].strip()})

    if not versions:
        raise ValueError("No versions found in CHANGELOG.md")

    # Get requested version or latest
    if version:
        for v in versions:
            if v["version"] == version:
                return v["version"], v["content"]
        raise ValueError(f"Version {version} not found in CHANGELOG.md")
    else:
        # Return latest
        return versions[0]["version"], versions[0]["content"]


def format_github_release(version: str, notes: str) -> str:
    """Format release notes for GitHub release."""
    # Clean up empty bullet points
    lines = notes.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip empty bullet points
        if stripped in ["- ", "-"]:
            continue
        # Skip empty sections
        if stripped.startswith("###") and not any(
            lines[i].strip().startswith("-") and lines[i].strip() not in ["- ", "-"]
            for i in range(lines.index(line) + 1, min(lines.index(line) + 10, len(lines)))
            if not lines[i].strip().startswith("###")
        ):
            continue
        cleaned.append(line)

    formatted = "\n".join(cleaned)

    # Add footer
    footer = f"""

---

**Full Changelog**: See [CHANGELOG.md](./CHANGELOG.md)

**Installation**:
```bash
pip install djp-workflow=={version}
```

**Documentation**: [docs/OPERATIONS.md](./docs/OPERATIONS.md)
"""

    return formatted + footer


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate GitHub release notes from CHANGELOG")
    parser.add_argument("version", nargs="?", help="Version to extract (e.g., 1.0.0)")
    parser.add_argument("--latest", action="store_true", help="Extract latest version")
    parser.add_argument("--output", help="Output file (default: stdout)")

    args = parser.parse_args()

    if not args.version and not args.latest:
        parser.error("Either provide a version or use --latest")

    try:
        # Read changelog
        changelog = read_changelog()

        # Extract notes
        version, notes = extract_version_notes(changelog, version=args.version if not args.latest else None)

        # Format for GitHub
        formatted = format_github_release(version, notes)

        # Output
        if args.output:
            output_file = Path(args.output)
            output_file.write_text(formatted, encoding="utf-8")
            print(f"✓ Release notes written to {output_file}", file=sys.stderr)
        else:
            print(formatted)

        # Print version to stderr for scripting
        print(f"Version: {version}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
