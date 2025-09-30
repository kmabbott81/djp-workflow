#!/usr/bin/env python3
"""
NightShift Runner
- Watches a `tasks/` directory for *.task.md files.
- Parses minimal YAML front matter or KEY: VALUE lines.
- Calls your Agents SDK CLI: `python -m src.run_workflow --task ...`.
- Moves processed tasks into tasks/done/ with a timestamp suffix.
"""
import argparse
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv  # optional

    load_dotenv()
except Exception:
    pass


def parse_task_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    data = {
        "task": None,
        "max_tokens": 1200,
        "temperature": 0.3,
        "trace_name": "nightshift",
        "require_citations": 0,
        "policy": "openai_only",
        "fastpath": False,
        "max_debaters": None,
        "timeout_s": None,
        "margin_threshold": None,
    }

    # YAML front matter
    if text.lstrip().startswith("---"):
        # very light-weight parse to avoid pyyaml dependency
        fm_end = text.find("\n---", 3)
        if fm_end != -1:
            fm = text[3:fm_end].strip()
            body = text[fm_end + 4 :]
            for line in fm.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    key = k.strip().lower()
                    val = v.strip().strip('"').strip("'")
                    if key in ("task", "trace_name", "policy"):
                        data[key] = val
                    elif key in ("max_tokens", "require_citations", "max_debaters", "timeout_s", "margin_threshold"):
                        try:
                            data[key] = int(val)
                        except:
                            pass
                    elif key in ("temperature"):
                        try:
                            data["temperature"] = float(val)
                        except:
                            pass
                    elif key in ("fastpath"):
                        data["fastpath"] = val.lower() in ("true", "1", "yes")

    # KEY: VALUE fallback
    # Matches lines like TASK: something
    for m in re.finditer(
        r"(?im)^(TASK|MAX_TOKENS|TEMPERATURE|TRACE_NAME|REQUIRE_CITATIONS|POLICY|FASTPATH|MAX_DEBATERS|TIMEOUT_S|MARGIN_THRESHOLD)\s*:\s*(.+)$",
        text,
    ):
        key = m.group(1).upper()
        val = m.group(2).strip()
        if key == "TASK":
            data["task"] = val
        elif key in ("MAX_TOKENS", "REQUIRE_CITATIONS", "MAX_DEBATERS", "TIMEOUT_S", "MARGIN_THRESHOLD"):
            try:
                data[key.lower()] = int(val)
            except:
                pass
        elif key == "TEMPERATURE":
            try:
                data["temperature"] = float(val)
            except:
                pass
        elif key in ("TRACE_NAME", "POLICY"):
            data[key.lower()] = val
        elif key == "FASTPATH":
            data["fastpath"] = val.lower() in ("true", "1", "yes")

    return data


def run_once(repo: Path, tasks_dir: Path) -> int:
    tasks = sorted(tasks_dir.glob("*.task.md"))
    if not tasks:
        return 0
    done_dir = tasks_dir / "done"
    done_dir.mkdir(exist_ok=True, parents=True)

    processed = 0
    for task_file in tasks:
        spec = parse_task_file(task_file)
        if not spec.get("task"):
            # Move invalid to done with note
            ts = datetime.now().strftime("%Y.%m.%d-%H%M%S")
            task_file.rename(done_dir / f"{task_file.stem}.{ts}.invalid.md")
            continue

        cmd = [
            sys.executable,
            "-m",
            "src.run_workflow",
            "--task",
            spec["task"],
            "--max_tokens",
            str(spec.get("max_tokens", 1200)),
            "--temperature",
            str(spec.get("temperature", 0.3)),
            "--trace_name",
            spec.get("trace_name", "nightshift"),
        ]

        # Add optional parameters if specified
        if spec.get("require_citations", 0) > 0:
            cmd.extend(["--require_citations", str(spec["require_citations"])])

        if spec.get("policy") and spec["policy"] != "openai_only":
            cmd.extend(["--policy", spec["policy"]])

        if spec.get("fastpath"):
            cmd.append("--fastpath")

        if spec.get("max_debaters"):
            cmd.extend(["--max_debaters", str(spec["max_debaters"])])

        if spec.get("timeout_s"):
            cmd.extend(["--timeout_s", str(spec["timeout_s"])])

        if spec.get("margin_threshold"):
            cmd.extend(["--margin_threshold", str(spec["margin_threshold"])])
        print(f"[NightShift] Running: {' '.join(cmd)} in {repo}")
        try:
            subprocess.run(cmd, cwd=str(repo), check=True)
            status = "ok"
        except subprocess.CalledProcessError as e:
            print(f"[NightShift] ERROR: {e}")
            status = "error"

        ts = datetime.now().strftime("%Y.%m.%d-%H%M%S")
        dest = done_dir / f"{task_file.stem}.{ts}.{status}.md"
        try:
            task_file.rename(dest)
        except Exception:
            # if rename fails across volumes, copy+remove
            dest.write_text(task_file.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            task_file.unlink(missing_ok=True)

        processed += 1
    return processed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Path to the repo containing src/run_workflow.py")
    ap.add_argument("--tasks-dir", required=True, help="Folder with *.task.md files")
    ap.add_argument("--interval", type=int, default=60, help="Polling interval in seconds (0 = process once and exit)")
    ap.add_argument("--oneshot", action="store_true", help="Process existing tasks and exit")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    tasks_dir = Path(args.tasks_dir).resolve()

    if args.oneshot or args.interval == 0:
        run_once(repo, tasks_dir)
        return

    print(f"[NightShift] Watching {tasks_dir} every {args.interval}s...")
    while True:
        run_once(repo, tasks_dir)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
