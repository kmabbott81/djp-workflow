#!/usr/bin/env python3
"""Version bump script for djp-workflow.

Usage:
    python scripts/version.py --major  # 1.0.0 -> 2.0.0
    python scripts/version.py --minor  # 1.0.0 -> 1.1.0
    python scripts/version.py --patch  # 1.0.0 -> 1.0.1
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def read_version_from_init() -> str:
    """Read current version from src/__init__.py."""
    init_file = get_project_root() / "src" / "__init__.py"
    content = init_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Could not find __version__ in src/__init__.py")
    return match.group(1)


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse version string into (major, minor, patch) tuple."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(current: str, bump_type: str) -> str:
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch = parse_version(current)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def update_init_version(new_version: str) -> None:
    """Update version in src/__init__.py."""
    init_file = get_project_root() / "src" / "__init__.py"
    content = init_file.read_text(encoding="utf-8")
    updated = re.sub(r'__version__\s*=\s*["\'][^"\']+["\']', f'__version__ = "{new_version}"', content)
    init_file.write_text(updated, encoding="utf-8")
    print("✓ Updated src/__init__.py")


def update_pyproject_version(new_version: str) -> None:
    """Update version in pyproject.toml."""
    pyproject_file = get_project_root() / "pyproject.toml"
    content = pyproject_file.read_text(encoding="utf-8")
    updated = re.sub(
        r'version\s*=\s*["\'][^"\']+["\']',
        f'version = "{new_version}"',
        content,
        count=1,  # Only replace the first occurrence (in [project] section)
    )
    pyproject_file.write_text(updated, encoding="utf-8")
    print("✓ Updated pyproject.toml")


def update_changelog(new_version: str) -> None:
    """Add new version heading to CHANGELOG.md."""
    changelog_file = get_project_root() / "CHANGELOG.md"

    if not changelog_file.exists():
        print("⚠ CHANGELOG.md not found, skipping")
        return

    content = changelog_file.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # Find the insertion point (after the header and before first version)
    lines = content.split("\n")
    insert_index = 0

    # Skip header lines
    for i, line in enumerate(lines):
        if line.startswith("## ["):
            insert_index = i
            break

    if insert_index == 0:
        # No existing versions, add after header
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith("#"):
                insert_index = i
                break

    # Insert new version section
    new_section = [
        f"## [{new_version}] - {today}",
        "",
        "### Added",
        "- ",
        "",
        "### Changed",
        "- ",
        "",
        "### Fixed",
        "- ",
        "",
    ]

    lines[insert_index:insert_index] = new_section
    updated = "\n".join(lines)

    changelog_file.write_text(updated, encoding="utf-8")
    print("✓ Updated CHANGELOG.md")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bump version for djp-workflow")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--major", action="store_true", help="Bump major version")
    group.add_argument("--minor", action="store_true", help="Bump minor version")
    group.add_argument("--patch", action="store_true", help="Bump patch version")

    args = parser.parse_args()

    # Determine bump type
    if args.major:
        bump_type = "major"
    elif args.minor:
        bump_type = "minor"
    else:
        bump_type = "patch"

    try:
        # Read current version
        current_version = read_version_from_init()
        print(f"Current version: {current_version}")

        # Calculate new version
        new_version = bump_version(current_version, bump_type)
        print(f"New version: {new_version}")

        # Update files
        update_init_version(new_version)
        update_pyproject_version(new_version)
        update_changelog(new_version)

        print(f"\n✓ Version bumped successfully: {current_version} -> {new_version}")
        print("\nNext steps:")
        print("1. Edit CHANGELOG.md to add release notes")
        print(f"2. Commit changes: git add -A && git commit -m 'Bump version to {new_version}'")
        print(f"3. Tag release: git tag v{new_version}")
        print("4. Push: git push && git push --tags")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
