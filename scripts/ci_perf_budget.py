"""CI performance budget script - compares test durations vs baseline."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
dur_file = ROOT / "durations.txt"  # default; caller can copy CI output here
ci_out = ROOT / "perf-report.md"
baseline_file = ROOT / "dashboards" / "ci" / "baseline.json"


def parse_durations_text(path: Path) -> list[tuple[float, str]]:
    """Parse pytest durations.txt format.

    Args:
        path: Path to durations.txt file

    Returns:
        List of (duration_seconds, test_name) tuples
    """
    rows = []
    if not path.exists():
        return rows
    pat = re.compile(r"^\s*(\d+\.\d+)\s*s\s+(.+)$")
    for ln in path.read_text(encoding="utf-8").splitlines():
        m = pat.search(ln)
        if m:
            rows.append((float(m.group(1)), m.group(2).strip()))
    return rows


def load_baseline(path: Path) -> dict:
    """Load baseline performance metrics.

    Args:
        path: Path to baseline.json

    Returns:
        Dict with total_seconds, top25_seconds, generated_at
    """
    if not path.exists():
        return {"total_seconds": 0.0, "top25_seconds": 0.0, "generated_at": "N/A"}
    return json.loads(path.read_text(encoding="utf-8"))


def save_report(md: str) -> None:
    """Save markdown report to file and print path.

    Args:
        md: Markdown content to save
    """
    ci_out.write_text(md, encoding="utf-8")
    print(f"Report saved to: {ci_out}")


def main() -> int:
    """Main entry point for CI perf budget script.

    Returns:
        Exit code (always 0 - soft gate via report only)
    """
    rows = parse_durations_text(dur_file)
    total = sum(s for s, _ in rows)
    rows.sort(reverse=True)
    top25 = sum(s for s, _ in rows[:25])

    base = load_baseline(baseline_file)
    b_total = base.get("total_seconds", 0.0)
    b_top25 = base.get("top25_seconds", 0.0)

    def pct(cur: float, base: float) -> float:
        """Calculate percentage change."""
        if base <= 0:
            return 0.0 if cur == 0 else 100.0
        return ((cur - base) / base) * 100.0

    d_total = pct(total, b_total)
    d_top25 = pct(top25, b_top25)

    # soft thresholds
    WARN_PCT = float(os.getenv("PERF_WARN_PCT", "10"))  # warn if >10% slower
    FAIL_PCT = float(os.getenv("PERF_FAIL_PCT", "25"))  # soft "needs attention" if >25%

    status = "✅ within budget"
    attention = False
    if d_total > WARN_PCT or d_top25 > WARN_PCT:
        status = "⚠️ slower than budget"
    if d_total > FAIL_PCT or d_top25 > FAIL_PCT:
        status = "🚨 performance regression"
        attention = True

    lines = []
    lines.append("# PR Performance Report")
    lines.append("")
    lines.append(f"- **Status:** {status}")
    lines.append(f"- Baseline total: **{b_total:.2f}s** → PR total: **{total:.2f}s** (**{d_total:+.1f}%**)")
    lines.append(f"- Baseline top-25: **{b_top25:.2f}s** → PR top-25: **{top25:.2f}s** (**{d_top25:+.1f}%**)")
    lines.append("")
    lines.append("## Notes")
    lines.append("- Baseline comes from `dashboards/ci/baseline.json` on `main` (refreshed by nightly).")
    lines.append("- Thresholds: warn if >10% slower; attention if >25% slower.")
    lines.append("")
    lines.append("## Top 10 (this PR run)")
    for i, (s, name) in enumerate(rows[:10], 1):
        lines.append(f"{i:>2}. `{name}` — {s:.3f}s")
    save_report("\n".join(lines))

    # Exit code stays 0; CI gate is social (comment + check-run)
    # Print a small JSON for workflow consumers
    print(
        json.dumps(
            {
                "status": status,
                "total_seconds": total,
                "top25_seconds": top25,
                "delta_total_pct": d_total,
                "delta_top25_pct": d_top25,
                "attention": attention,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
