"""Metrics extraction and analysis for DJP workflow runs."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


def load_runs(path: str = "runs") -> pd.DataFrame:
    """
    Load all workflow run artifacts and flatten into a DataFrame.

    Args:
        path: Directory containing JSON artifact files

    Returns:
        DataFrame with one row per run containing key metrics
    """
    runs_path = Path(path)
    if not runs_path.exists():
        return pd.DataFrame()

    artifacts = list(runs_path.glob("*.json"))
    if not artifacts:
        return pd.DataFrame()

    rows = []

    for artifact_file in artifacts:
        try:
            with open(artifact_file, encoding="utf-8") as f:
                artifact = json.load(f)

            # Extract basic metadata
            metadata = artifact.get("run_metadata", {})
            parameters = metadata.get("parameters", {})
            debate = artifact.get("debate", {})
            judge = artifact.get("judge", {})
            publish = artifact.get("publish", {})
            provenance = artifact.get("provenance", {})
            grounding = artifact.get("grounding", {})

            # Calculate token totals
            model_usage = provenance.get("model_usage", {})
            total_tokens_in = sum(usage.get("tokens_in", 0) for usage in model_usage.values())
            total_tokens_out = sum(usage.get("tokens_out", 0) for usage in model_usage.values())
            total_tokens = total_tokens_in + total_tokens_out

            # Calculate estimated cost
            estimated_costs = provenance.get("estimated_costs", {})
            total_cost = sum(estimated_costs.values())

            # Check citations compliance
            citations_required = parameters.get("require_citations", 0)
            citations_ok = True
            if citations_required > 0:
                for draft in judge.get("ranked_drafts", []):
                    if len(draft.get("evidence", [])) < citations_required:
                        citations_ok = False
                        break

            # Determine advisory reason
            advisory_reason = ""
            status = publish.get("status", "none")
            if status == "advisory_only":
                advisory_reason = publish.get("reason", "not_from_allowed_provider")
            elif status == "none":
                advisory_reason = publish.get("reason", "no_valid_content")

            # Grounding metrics
            grounded = grounding.get("enabled", False)
            grounded_required = grounding.get("required_citations", 0)
            citations_count = len(grounding.get("citations", []))

            # Redaction metrics
            redacted = publish.get("redacted", False)
            redaction_events = publish.get("redaction_events", [])
            redaction_count = sum(event.get("count", 0) for event in redaction_events)
            redaction_types = (
                ",".join(sorted(set(event.get("type", "") for event in redaction_events))) if redaction_events else ""
            )

            row = {
                "artifact_file": artifact_file.name,
                "timestamp": pd.to_datetime(metadata.get("timestamp", "")),
                "task": metadata.get("task", ""),
                "trace_name": metadata.get("trace_name", ""),
                "preset_name": parameters.get("preset_name", "manual"),
                "status": status,
                "provider": publish.get("provider", ""),
                "winner_provider": judge.get("winner_provider", ""),
                "tokens_in": total_tokens_in,
                "tokens_out": total_tokens_out,
                "total_tokens": total_tokens,
                "est_cost": total_cost,
                "duration": provenance.get("duration_seconds", 0.0),
                "num_drafts": debate.get("total_drafts", 0),
                "num_ranked": judge.get("total_ranked", 0),
                "citations_required": citations_required,
                "citations_ok": citations_ok,
                "grounded": grounded,
                "grounded_required": grounded_required,
                "citations_count": citations_count,
                "redacted": redacted,
                "redaction_count": redaction_count,
                "redaction_types": redaction_types,
                "advisory_reason": advisory_reason,
                "max_tokens": parameters.get("max_tokens", 0),
                "temperature": parameters.get("temperature", 0.0),
                "fastpath": parameters.get("fastpath", False),
                "text_length": publish.get("text_length", 0),
                "schema_version": artifact.get("schema_version", "unknown"),
            }

            rows.append(row)

        except Exception as e:
            # Skip malformed artifacts but log the issue
            print(f"Warning: Could not parse artifact {artifact_file.name}: {e}")
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Sort by timestamp descending (most recent first)
    df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)

    return df


def summarize_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """
    Calculate key performance indicators from the runs DataFrame.

    Args:
        df: DataFrame from load_runs()

    Returns:
        Dictionary of KPI values
    """
    if df.empty:
        return {
            "total_runs": 0,
            "advisory_rate": 0.0,
            "avg_cost": 0.0,
            "avg_tokens": 0.0,
            "avg_duration": 0.0,
            "provider_mix": {},
            "top_failure_reasons": {},
            "citations_compliance_rate": 0.0,
        }

    total_runs = len(df)
    advisory_runs = len(df[df["status"] == "advisory_only"])
    published_runs = len(df[df["status"] == "published"])
    failed_runs = len(df[df["status"] == "none"])

    # Calculate rates
    advisory_rate = advisory_runs / total_runs if total_runs > 0 else 0.0
    publish_rate = published_runs / total_runs if total_runs > 0 else 0.0
    failure_rate = failed_runs / total_runs if total_runs > 0 else 0.0

    # Cost and token averages
    avg_cost = df["est_cost"].mean() if not df["est_cost"].isna().all() else 0.0
    avg_tokens = df["total_tokens"].mean() if not df["total_tokens"].isna().all() else 0.0
    avg_duration = df["duration"].mean() if not df["duration"].isna().all() else 0.0

    # Provider mix (for published content)
    published_df = df[df["status"] == "published"]
    if not published_df.empty:
        provider_counts = published_df["provider"].value_counts()
        provider_mix = (provider_counts / provider_counts.sum()).to_dict()
    else:
        provider_mix = {}

    # Top failure reasons
    advisory_df = df[df["status"].isin(["advisory_only", "none"])]
    if not advisory_df.empty:
        reason_counts = advisory_df["advisory_reason"].value_counts()
        top_failure_reasons = reason_counts.head(5).to_dict()
    else:
        top_failure_reasons = {}

    # Citations compliance
    citation_runs = df[df["citations_required"] > 0]
    if not citation_runs.empty:
        citations_compliance_rate = citation_runs["citations_ok"].mean()
    else:
        citations_compliance_rate = 1.0  # No citation requirements

    return {
        "total_runs": total_runs,
        "published_runs": published_runs,
        "advisory_runs": advisory_runs,
        "failed_runs": failed_runs,
        "advisory_rate": advisory_rate,
        "publish_rate": publish_rate,
        "failure_rate": failure_rate,
        "avg_cost": avg_cost,
        "avg_tokens": avg_tokens,
        "avg_duration": avg_duration,
        "provider_mix": provider_mix,
        "top_failure_reasons": top_failure_reasons,
        "citations_compliance_rate": citations_compliance_rate,
    }


def filter_runs_by_date(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """
    Filter runs to only include those within the last N days.

    Args:
        df: DataFrame from load_runs()
        days: Number of days to include

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    cutoff_date = datetime.now() - timedelta(days=days)
    return df[df["timestamp"] >= cutoff_date]


def filter_runs_by_preset(df: pd.DataFrame, preset: str) -> pd.DataFrame:
    """
    Filter runs by preset name.

    Args:
        df: DataFrame from load_runs()
        preset: Preset name to filter by

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    return df[df["preset_name"] == preset]


def filter_runs_by_provider(df: pd.DataFrame, provider: str) -> pd.DataFrame:
    """
    Filter runs by provider.

    Args:
        df: DataFrame from load_runs()
        provider: Provider to filter by

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    return df[df["provider"] == provider]


def export_metrics(df: pd.DataFrame, path: str = "metrics.csv") -> None:
    """
    Export metrics DataFrame to CSV file.

    Args:
        df: DataFrame from load_runs()
        path: Output CSV file path
    """
    if df.empty:
        # Create empty CSV with headers
        empty_df = pd.DataFrame(
            columns=[
                "artifact_file",
                "timestamp",
                "task",
                "trace_name",
                "preset_name",
                "status",
                "provider",
                "winner_provider",
                "tokens_in",
                "tokens_out",
                "total_tokens",
                "est_cost",
                "duration",
                "num_drafts",
                "num_ranked",
                "citations_required",
                "citations_ok",
                "grounded",
                "grounded_required",
                "citations_count",
                "redacted",
                "redaction_count",
                "redaction_types",
                "advisory_reason",
                "max_tokens",
                "temperature",
                "fastpath",
                "text_length",
                "schema_version",
            ]
        )
        empty_df.to_csv(path, index=False)
    else:
        df.to_csv(path, index=False)

    print(f"Metrics exported to {path}")


def get_recent_runs(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """
    Get the N most recent runs.

    Args:
        df: DataFrame from load_runs()
        n: Number of recent runs to return

    Returns:
        DataFrame with recent runs
    """
    return df.head(n) if not df.empty else df


if __name__ == "__main__":
    # Test metrics extraction
    df = load_runs()
    print(f"Loaded {len(df)} runs")

    if not df.empty:
        kpis = summarize_kpis(df)
        print("\nKey Performance Indicators:")
        for key, value in kpis.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")

        print("\nRecent runs:")
        recent = get_recent_runs(df, 5)
        for _, run in recent.iterrows():
            print(
                f"  {run['timestamp']:%Y-%m-%d %H:%M} | {run['preset_name']} | {run['status']} | ${run['est_cost']:.4f}"
            )
    else:
        print("No runs found")
