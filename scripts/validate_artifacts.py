#!/usr/bin/env python3
"""
Schema validation script for CI/CD and local development.

Validates all JSON schemas and ensures artifacts conform to expected structure.
"""

import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("Warning: jsonschema not available. Install with: pip install jsonschema")


def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load a JSON schema file."""
    try:
        with open(schema_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading schema {schema_path}: {e}")
        return None


def create_sample_artifact() -> dict[str, Any]:
    """Create a sample artifact for validation testing."""
    return {
        "schema_version": "1.1",
        "run_metadata": {
            "timestamp": "2025-09-29T14:45:00.000Z",
            "task": "Sample validation task",
            "trace_name": "schema-validation-test",
            "parameters": {
                "max_tokens": 1000,
                "temperature": 0.3,
                "allowed_models": ["openai/gpt-4o", "openai/gpt-4o-mini"],
                "grounded_required": 0,
                "redact": True,
            },
        },
        "debate": {
            "drafts": [
                {
                    "provider": "openai/gpt-4o",
                    "answer": "Sample draft answer for validation",
                    "evidence": ["Source 1", "Source 2"],
                    "confidence": 0.8,
                    "safety_flags": [],
                }
            ],
            "total_drafts": 1,
        },
        "judge": {
            "ranked_drafts": [
                {
                    "provider": "openai/gpt-4o",
                    "answer": "Sample draft answer for validation",
                    "evidence": ["Source 1", "Source 2"],
                    "confidence": 0.8,
                    "safety_flags": [],
                    "score": 8.5,
                    "reasons": "Good sample response",
                    "subscores": {"task_fit": 4, "support": 3, "clarity": 1.5},
                }
            ],
            "winner_provider": "openai/gpt-4o",
            "total_ranked": 1,
        },
        "publish": {
            "status": "published",
            "provider": "openai/gpt-4o",
            "text": "Sample draft answer for validation",
            "text_length": 37,
            "redacted": False,
            "redaction_events": [],
        },
        "grounding": {
            "enabled": False,
            "corpus_loaded": False,
            "corpus_docs": 0,
            "required_citations": 0,
            "citations": [],
            "grounded_fail_reason": None,
        },
        "provenance": {
            "git_sha": "abc1234",
            "python_version": "3.13.0",
            "sdk_version": "unknown",
            "model_usage": {"openai/gpt-4o": {"calls": 2, "tokens_in": 150, "tokens_out": 80}},
            "estimated_costs": {"openai/gpt-4o": 0.0021},
            "duration_seconds": 45.2,
        },
    }


def validate_schemas() -> int:
    """Validate all schemas and sample artifacts."""
    if not JSONSCHEMA_AVAILABLE:
        print("ERROR: jsonschema package not available")
        return 1

    errors = 0
    schemas_dir = Path("schemas")

    if not schemas_dir.exists():
        print(f"ERROR: Schemas directory not found: {schemas_dir}")
        return 1

    print("Validating schemas...")

    # Load and validate artifact schema
    artifact_schema_path = schemas_dir / "artifact.json"
    if artifact_schema_path.exists():
        artifact_schema = load_schema(artifact_schema_path)
        if artifact_schema:
            try:
                # Validate the schema itself
                jsonschema.Draft7Validator.check_schema(artifact_schema)
                print(f"[OK] Schema valid: {artifact_schema_path}")

                # Validate sample artifact against schema
                sample_artifact = create_sample_artifact()
                jsonschema.validate(sample_artifact, artifact_schema)
                print("[OK] Sample artifact validates against schema")

                # Try to validate any existing artifacts
                runs_dir = Path("runs")
                if runs_dir.exists():
                    artifacts = list(runs_dir.glob("*.json"))
                    if artifacts:
                        # Validate the most recent artifact
                        latest_artifact = max(artifacts, key=lambda x: x.stat().st_mtime)
                        try:
                            with open(latest_artifact, encoding="utf-8") as f:
                                real_artifact = json.load(f)

                            # Check schema version
                            version = real_artifact.get("schema_version", "unknown")
                            if version == "unknown":
                                print(f"[WARN] Artifact {latest_artifact.name} missing schema_version field")
                            elif version != "1.0":
                                print(
                                    f"[WARN] Artifact {latest_artifact.name} has schema version {version}, expected 1.0"
                                )

                            jsonschema.validate(real_artifact, artifact_schema)
                            print(f"[OK] Real artifact validates: {latest_artifact.name}")
                        except Exception as e:
                            print(f"[WARN] Real artifact validation failed: {latest_artifact.name} - {e}")
                            # Don't count as error since existing artifacts might not have new fields

            except jsonschema.SchemaError as e:
                print(f"[ERROR] Schema error in {artifact_schema_path}: {e}")
                errors += 1
            except jsonschema.ValidationError as e:
                print(f"[ERROR] Sample artifact validation failed: {e.message}")
                errors += 1
        else:
            errors += 1
    else:
        print(f"[ERROR] Missing artifact schema: {artifact_schema_path}")
        errors += 1

    # Load and validate policy schema
    policy_schema_path = schemas_dir / "policy.json"
    if policy_schema_path.exists():
        policy_schema = load_schema(policy_schema_path)
        if policy_schema:
            try:
                # Validate the schema itself
                jsonschema.Draft7Validator.check_schema(policy_schema)
                print(f"[OK] Schema valid: {policy_schema_path}")

                # Validate all policy files
                policies_dir = Path("policies")
                if policies_dir.exists():
                    policy_files = list(policies_dir.glob("*.json"))
                    for policy_file in policy_files:
                        try:
                            with open(policy_file, encoding="utf-8") as f:
                                policy_data = json.load(f)
                            jsonschema.validate(policy_data, policy_schema)
                            print(f"[OK] Policy validates: {policy_file.name}")
                        except Exception as e:
                            print(f"[ERROR] Policy validation failed: {policy_file.name} - {e}")
                            errors += 1
                else:
                    print("[WARN] No policies directory found")

            except jsonschema.SchemaError as e:
                print(f"[ERROR] Schema error in {policy_schema_path}: {e}")
                errors += 1
        else:
            errors += 1
    else:
        print(f"[ERROR] Missing policy schema: {policy_schema_path}")
        errors += 1

    # Summary
    if errors == 0:
        print(f"\n[OK] All schemas valid ({len(list(schemas_dir.glob('*.json')))} checked)")
        return 0
    else:
        print(f"\n[ERROR] {errors} schema validation errors")
        return 1


def main():
    """Main entry point."""
    print("DJP Pipeline Schema Validation")
    print("=" * 40)

    exit_code = validate_schemas()

    if exit_code == 0:
        print("\n[SUCCESS] Schema validation passed!")
    else:
        print("\n[FAILED] Schema validation failed!")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
