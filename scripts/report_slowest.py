#!/usr/bin/env python3
"""Parse pytest --durations output and generate a markdown report.

Usage:
    python scripts/report_slowest.py durations.txt slowest-tests.md

Reads pytest output with --durations=N flag and produces a sorted
markdown table of the slowest tests for performance tracking.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def parse_durations(lines: list[str]) -> list[tuple[float, str]]:
    """Extract (duration_seconds, test_name) from pytest --durations output."""
    durations = []
    in_section = False

    for line in lines:
        # Start of durations section
        if "slowest durations" in line.lower():
            in_section = True
            continue

        if not in_section:
            continue

        # End of section (blank line or next section)
        if not line.strip() or line.startswith("="):
            break

        # Parse line like: "1.23s call     tests/test_foo.py::test_bar"
        match = re.match(r"^\s*([\d.]+)s\s+\w+\s+(.+)$", line)
        if match:
            duration = float(match.group(1))
            test_name = match.group(2).strip()
            durations.append((duration, test_name))

    return durations


def generate_markdown(durations: list[tuple[float, str]], output_path: Path) -> None:
    """Write markdown table of slowest tests."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Slowest Tests Report\n\n")
        f.write(f"Total tests analyzed: {len(durations)}\n\n")

        if not durations:
            f.write("_No duration data found._\n")
            return

        f.write("| Duration (s) | Test |\n")
        f.write("|--------------|------|\n")

        for duration, test_name in sorted(durations, reverse=True):
            f.write(f"| {duration:.2f} | `{test_name}` |\n")

        f.write("\n_Generated from pytest --durations output_\n")


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <durations.txt> <output.md>", file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        return 1

    with open(input_path, encoding="utf-8") as f:
        lines = f.readlines()

    durations = parse_durations(lines)
    generate_markdown(durations, output_path)

    print(f"Generated {output_path} with {len(durations)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
