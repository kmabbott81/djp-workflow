#!/usr/bin/env python3
"""
Task Generator: Create multiple task files from preset templates.

This script reads a preset template and generates multiple copies with
unique timestamps and trace names for queue processing.
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path


def generate_trace_name(base_name: str, timestamp: str, index: int) -> str:
    """Generate a unique trace name."""
    return f"{base_name}-{timestamp}-{index:03d}"


def generate_task_content(preset_path: Path, timestamp: str, trace_name: str, task_index: int) -> str:
    """Generate task content from preset template."""

    # Read preset template
    with open(preset_path, encoding="utf-8") as f:
        content = f.read()

    # Replace placeholder variables
    content = content.replace("{timestamp}", timestamp)
    content = content.replace("{trace_name}", trace_name)
    content = content.replace("{task_index}", str(task_index))

    # Add task generation metadata
    metadata_section = f"""

---
**GENERATED TASK METADATA:**
- Source preset: {preset_path.name}
- Generated at: {datetime.now().isoformat()}
- Task index: {task_index}
- Trace name: {trace_name}
---
"""

    return content + metadata_section


def create_task_files(preset_path: Path, count: int, output_dir: Path, base_timestamp: str = None) -> list[Path]:
    """Create multiple task files from a preset template."""

    if base_timestamp is None:
        base_timestamp = datetime.now().strftime("%Y.%m.%d-%H%M")

    # Extract base name from preset filename
    preset_name = preset_path.stem.replace(".task", "")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    created_files = []

    for i in range(1, count + 1):
        # Create unique timestamp with slight offset
        task_timestamp = datetime.now() + timedelta(seconds=i)
        task_timestamp_str = task_timestamp.strftime("%Y.%m.%d-%H%M%S")

        # Generate trace name
        trace_name = generate_trace_name(preset_name, base_timestamp, i)

        # Generate content
        task_content = generate_task_content(preset_path, task_timestamp_str, trace_name, i)

        # Create output filename
        output_filename = f"{trace_name}.task.md"
        output_path = output_dir / output_filename

        # Write task file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(task_content)

        created_files.append(output_path)
        print(f"Created: {output_path}")

    return created_files


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate multiple task files from preset templates")
    parser.add_argument("--preset", required=True, type=Path, help="Path to preset template file")
    parser.add_argument("--count", type=int, default=3, help="Number of task files to generate (default: 3)")
    parser.add_argument(
        "--out", type=Path, default=Path("tasks"), help="Output directory for generated tasks (default: tasks)"
    )
    parser.add_argument("--timestamp", help="Base timestamp for task naming (default: current time)")

    args = parser.parse_args()

    # Validate preset file exists
    if not args.preset.exists():
        print(f"ERROR: Preset file not found: {args.preset}")
        return 1

    print(f"Generating {args.count} tasks from preset: {args.preset}")
    print(f"Output directory: {args.out}")

    try:
        created_files = create_task_files(args.preset, args.count, args.out, args.timestamp)

        print(f"\nSuccessfully created {len(created_files)} task files:")
        for file_path in created_files:
            print(f"  - {file_path}")

        return 0

    except Exception as e:
        print(f"ERROR: Failed to generate tasks: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
