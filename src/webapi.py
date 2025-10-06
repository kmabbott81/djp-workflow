"""FastAPI web API for templates and triage endpoints.

Sprint 46: Added /metrics endpoint and telemetry middleware.
Sprint 49 Phase B: Added /actions endpoints with preview/confirm workflow.
"""

import os
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from .auth.security import require_scopes
from .telemetry import init_telemetry
from .telemetry.middleware import TelemetryMiddleware
from .templates import list_templates
from .templates import render_template as render_template_content

app = FastAPI(
    title="DJP Workflow API",
    version="1.0.0",
    openapi_tags=[
        {"name": "actions", "description": "Action preview and execution endpoints"},
        {"name": "audit", "description": "Audit log queries (admin only)"},
        {"name": "health", "description": "Health and status endpoints"},
    ],
)

# Sprint 51: Add security scheme for API key authentication
app.openapi_schema = None  # Force regeneration


def custom_openapi():
    """Custom OpenAPI schema with security definitions."""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="""
DJP Workflow API with Sprint 51 Phase 1 security.

## Authentication

All `/actions/*` endpoints require authentication via API key:

```
Authorization: Bearer relay_sk_<key>
```

## Scopes

- `actions:preview` - Preview actions before execution
- `actions:execute` - Execute actions
- `audit:read` - Query audit logs (admin only)

## Roles

- **viewer**: Can preview actions only
- **developer**: Can preview and execute actions
- **admin**: Full access including audit logs

## Error Codes

- `401` - Missing or invalid API key
- `403` - Insufficient permissions (scope check failed)
- `409` - Idempotency conflict (duplicate request)
- `501` - Provider not configured
- `504` - Execution timeout
        """,
        routes=app.routes,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API-Key",
            "description": "API key in format: relay_sk_<random>",
        }
    }

    # Mark endpoints that require auth
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if path.startswith("/actions/preview") or path.startswith("/actions/execute"):
                openapi_schema["paths"][path][method]["security"] = [{"ApiKeyBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Sprint 46: Initialize telemetry and add middleware
init_telemetry()
app.add_middleware(TelemetryMiddleware)

# CORS configuration (Sprint 50: Hardened headers + expose X-Request-ID/X-Trace-Link)
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://relay-studio-one.vercel.app",  # Production Studio
]

# Allow all origins in development
if os.getenv("RELAY_ENV") != "production":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # No cookies needed
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Signature", "Authorization"],  # Sprint 50: +Authorization
    expose_headers=["X-Request-ID", "X-Trace-Link"],  # Sprint 50: Expose for observability
    max_age=600,  # Cache preflight for 10 minutes
)


class TemplateInfo(BaseModel):
    """Template metadata for listing."""

    name: str
    version: str
    description: str
    inputs: list[dict[str, Any]]


class RenderRequest(BaseModel):
    """Request to render a template."""

    template_name: str
    inputs: dict[str, Any]
    output_format: str = "html"  # html, docx, both


class RenderResponse(BaseModel):
    """Response from rendering a template."""

    success: bool
    html: Optional[str] = None
    docx_base64: Optional[str] = None
    artifact_path: Optional[str] = None
    error: Optional[str] = None


class TriageRequest(BaseModel):
    """Request to triage email content via DJP."""

    content: str
    subject: Optional[str] = None
    from_email: Optional[str] = None


class TriageResponse(BaseModel):
    """Response from triaging content."""

    success: bool
    artifact_id: str
    status: str
    provider: str
    preview: str
    artifact_path: str
    error: Optional[str] = None


# Sprint 49 Phase B: Actions feature flag
ACTIONS_ENABLED = os.getenv("ACTIONS_ENABLED", "false").lower() == "true"


@app.get("/")
def root():
    """API root endpoint."""
    endpoints = {
        "templates": "/api/templates",
        "render": "/api/render",
        "triage": "/api/triage",
        "health": "/_stcore/health",
        "ready": "/ready",
        "version": "/version",
        "metrics": "/metrics",
    }

    # Add actions endpoints if enabled
    if ACTIONS_ENABLED:
        endpoints["actions"] = "/actions"
        endpoints["actions_preview"] = "/actions/preview"
        endpoints["actions_execute"] = "/actions/execute"

    return {
        "name": "DJP Workflow API",
        "version": "1.0.0",
        "endpoints": endpoints,
        "features": {
            "actions": ACTIONS_ENABLED,
        },
    }


@app.get("/_stcore/health")
def health():
    """Health check endpoint."""
    return {"ok": True}


@app.get("/version")
def version():
    """
    Version and build metadata endpoint.

    Returns git SHA, version, and build timestamp.
    """
    import subprocess

    git_sha = "unknown"
    git_branch = "unknown"

    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        pass

    try:
        git_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        pass

    return {
        "version": app.version,
        "git_sha": git_sha,
        "git_branch": git_branch,
        "build_time": os.environ.get("BUILD_TIME", "unknown"),
        "environment": os.environ.get("RAILWAY_ENVIRONMENT", "local"),
    }


@app.get("/ready")
def ready():
    """
    Readiness check endpoint.

    Returns 200 if service is ready to accept traffic.
    Checks filesystem and basic dependencies.
    """
    checks = {
        "telemetry": False,
        "templates": False,
        "filesystem": False,
    }

    # Check telemetry initialized
    try:
        from .telemetry.prom import generate_metrics_text

        metrics = generate_metrics_text()
        checks["telemetry"] = len(metrics) > 0
    except Exception:
        pass

    # Check templates loadable
    try:
        templates = list_templates()
        checks["templates"] = len(templates) > 0
    except Exception:
        pass

    # Check filesystem writable
    try:
        artifact_dir = Path("runs/api")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        test_file = artifact_dir / ".readiness_check"
        test_file.write_text("ok")
        test_file.unlink()
        checks["filesystem"] = True
    except Exception:
        pass

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks,
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text exposition format.
    If telemetry is disabled or prometheus-client is not installed,
    returns empty response.

    Sprint 46: Phase 1 (Metrics) implementation.
    """
    from .telemetry.prom import generate_metrics_text

    return generate_metrics_text()


@app.get("/api/templates", response_model=list[TemplateInfo])
def get_templates():
    """
    List available templates.

    Returns:
        List of template metadata with inputs schema
    """
    try:
        templates = list_templates()

        return [
            TemplateInfo(
                name=t.name,
                version=t.version,
                description=t.description,
                inputs=[
                    {
                        "id": inp.id,
                        "label": inp.label,
                        "type": inp.type,
                        "required": inp.required,
                        "help": getattr(inp, "help", ""),
                        "enum": getattr(inp, "enum", None),
                    }
                    for inp in t.inputs
                ],
            )
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}") from e


@app.post("/api/render", response_model=RenderResponse)
def render_template(request: RenderRequest):
    """
    Render a template with provided inputs.

    Args:
        request: Template name, inputs, and output format

    Returns:
        Rendered HTML and/or DOCX (base64 encoded)
    """
    try:
        # Get template
        templates = list_templates()
        template = next((t for t in templates if t.name == request.template_name), None)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{request.template_name}' not found")

        # Render template
        rendered = render_template_content(template, request.inputs)

        # Generate HTML
        html_content = None
        if request.output_format in ("html", "both"):
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 4px; }}
    </style>
</head>
<body>
{rendered}
</body>
</html>
"""

        # Generate DOCX (stub - would use python-docx in production)
        docx_base64 = None
        if request.output_format in ("docx", "both"):
            # Placeholder: In production, use python-docx to create proper DOCX
            # For now, return base64-encoded text content
            docx_base64 = b64encode(rendered.encode("utf-8")).decode("ascii")

        # Save dry-run artifact
        artifact_dir = Path("runs/api")
        artifact_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        artifact_path = artifact_dir / f"render-{timestamp}.html"

        if html_content:
            artifact_path.write_text(html_content, encoding="utf-8")

        return RenderResponse(
            success=True,
            html=html_content,
            docx_base64=docx_base64,
            artifact_path=str(artifact_path),
        )

    except HTTPException:
        raise
    except Exception as e:
        return RenderResponse(success=False, error=str(e))


@app.post("/api/triage", response_model=TriageResponse)
async def triage_content(request: TriageRequest):
    """
    Triage email content via DJP workflow.

    Args:
        request: Email content and metadata

    Returns:
        DJP result with artifact path
    """
    try:
        # Check if real mode is available
        real_mode = bool(os.environ.get("OPENAI_API_KEY"))

        if real_mode:
            # Run real DJP workflow
            from .debate import run_debate
            from .judge import judge_drafts
            from .publish import select_publish_text

            # Construct task prompt
            task = f"Analyze and summarize this email:\n\n{request.content}"
            if request.subject:
                task = f"Subject: {request.subject}\n\n" + task

            # Run workflow
            drafts = await run_debate(
                task=task,
                max_tokens=1000,
                temperature=0.3,
                corpus_docs=None,
                allowed_models=["openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022"],
            )

            judgment = await judge_drafts(drafts=drafts, task=task, require_citations=0)

            status, provider, text, reason, redaction_meta = select_publish_text(
                judgment, drafts, allowed_models=["openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022"]
            )

        else:
            # Mock mode
            status = "published"
            provider = "mock/gpt-4o"
            text = f"[Mock analysis]\n\nThis email appears to be about: {request.subject or 'general inquiry'}\n\nKey points:\n1. Content received\n2. Analysis pending\n3. Mock response generated"
            reason = ""

        # Save artifact
        artifact_dir = Path("runs/api/triage")
        artifact_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        artifact_id = f"triage-{timestamp}"
        artifact_path = artifact_dir / f"{artifact_id}.json"

        import json

        artifact_data = {
            "artifact_id": artifact_id,
            "timestamp": datetime.now().isoformat(),
            "request": {
                "content": request.content[:500],  # Truncate for storage
                "subject": request.subject,
                "from_email": request.from_email,
            },
            "result": {"status": status, "provider": provider, "text": text, "reason": reason},
        }

        artifact_path.write_text(json.dumps(artifact_data, indent=2), encoding="utf-8")

        return TriageResponse(
            success=True,
            artifact_id=artifact_id,
            status=status,
            provider=provider,
            preview=text[:300] + "..." if len(text) > 300 else text,
            artifact_path=str(artifact_path),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage failed: {str(e)}") from e


# ============================================================================
# Sprint 49 Phase B: Actions Endpoints
# ============================================================================


@app.get("/actions")
def list_actions(request: Request):
    """
    List available actions.

    Returns list of action definitions with schemas.
    Requires ACTIONS_ENABLED=true.
    """
    if not ACTIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Actions feature not enabled")

    from .actions import get_executor

    executor = get_executor()
    actions = executor.list_actions()

    return {
        "actions": actions,
        "request_id": request.state.request_id if hasattr(request.state, "request_id") else str(uuid4()),
    }


@app.post("/actions/preview")
@require_scopes(["actions:preview"])
async def preview_action(
    request: Request,
    body: dict[str, Any],
):
    """
    Preview an action before execution.

    Returns preview_id for use in /actions/execute.
    Requires ACTIONS_ENABLED=true.
    Requires scope: actions:preview
    """
    import time

    from .actions import PreviewRequest, get_executor
    from .audit.logger import write_audit

    if not ACTIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Actions feature not enabled")

    start_time = time.time()
    status = "ok"
    error_reason = "none"
    http_status = 200
    preview_result = None

    try:
        preview_req = PreviewRequest(**body)
        executor = get_executor()
        preview = executor.preview(preview_req.action, preview_req.params)
        preview_result = preview

        return {
            **preview.model_dump(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else str(uuid4()),
        }

    except ValueError as e:
        status = "error"
        error_reason = "validation"
        http_status = 400
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        status = "error"
        error_reason = "other"
        http_status = 500
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}") from e
    finally:
        # Write audit log
        duration_ms = int((time.time() - start_time) * 1000)

        # Extract action details
        try:
            action = body.get("action", "unknown")
            params = body.get("params", {})

            # Parse provider and action_id
            if "." in action:
                parts = action.split(".", 1)
                provider = parts[0]
                action_id = parts[1] if len(parts) > 1 else action
            else:
                provider = "unknown"
                action_id = action

            request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid4())
            workspace_id = request.state.workspace_id if hasattr(request.state, "workspace_id") else uuid4()
            actor_type = request.state.actor_type if hasattr(request.state, "actor_type") else "user"
            actor_id = request.state.actor_id if hasattr(request.state, "actor_id") else "unknown"
            signature_present = "X-Signature" in request.headers

            await write_audit(
                run_id=None,  # Preview has no run_id
                request_id=request_id,
                workspace_id=workspace_id,
                actor_type=actor_type,
                actor_id=actor_id,
                provider=provider,
                action_id=action_id,
                preview_id=preview_result.preview_id if preview_result else None,
                idempotency_key=None,  # Preview doesn't use idempotency
                signature_present=signature_present,
                params=params,
                status=status,
                error_reason=error_reason,
                http_status=http_status,
                duration_ms=duration_ms,
            )
        except Exception:
            # Audit logging failure should not break the request
            pass


@app.post("/actions/execute")
@require_scopes(["actions:execute"])
async def execute_action(
    request: Request,
    body: dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """
    Execute a previewed action.

    Requires preview_id from /actions/preview.
    Optionally accepts Idempotency-Key header for deduplication.
    Requires ACTIONS_ENABLED=true.
    Requires scope: actions:execute
    """
    import time

    from .actions import get_executor
    from .audit.logger import write_audit

    if not ACTIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Actions feature not enabled")

    start_time = time.time()
    status = "ok"
    error_reason = "none"
    http_status = 200
    execute_result = None
    preview_id = body.get("preview_id")
    final_idempotency_key = idempotency_key or body.get("idempotency_key")

    try:
        # Parse request
        if not preview_id:
            status = "error"
            error_reason = "validation"
            http_status = 400
            raise HTTPException(status_code=400, detail="preview_id required")

        # Get workspace_id from auth context
        workspace_id = request.state.workspace_id if hasattr(request.state, "workspace_id") else "default"

        # Get request ID from telemetry middleware
        request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid4())

        # Execute
        executor = get_executor()
        result = await executor.execute(
            preview_id=preview_id,
            idempotency_key=final_idempotency_key,
            workspace_id=workspace_id,
            request_id=request_id,
        )
        execute_result = result

        return result.model_dump()

    except ValueError as e:
        status = "error"
        error_reason = "validation"
        http_status = 400
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NotImplementedError as e:
        status = "error"
        error_reason = "provider_unconfigured"
        http_status = 501
        raise HTTPException(status_code=501, detail=str(e)) from e
    except TimeoutError as e:
        status = "error"
        error_reason = "timeout"
        http_status = 504
        raise HTTPException(status_code=504, detail=f"Execution timeout: {str(e)}") from e
    except Exception as e:
        status = "error"
        # Check if it's a 5xx from downstream
        if "5" in str(e) and "xx" in str(e).lower():
            error_reason = "downstream_5xx"
        else:
            error_reason = "other"
        http_status = 500
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}") from e
    finally:
        # Write audit log
        duration_ms = int((time.time() - start_time) * 1000)

        # Extract action details from execute result or preview store
        try:
            # Get action info from result or try to extract from body
            if execute_result:
                provider = execute_result.provider
                action_id = execute_result.action
                run_id = execute_result.run_id
            else:
                # Fallback if result not available
                provider = "unknown"
                action_id = "unknown"
                run_id = None

            # Reconstruct params (not available in execute, use empty dict)
            params = body.copy()
            params.pop("preview_id", None)
            params.pop("idempotency_key", None)

            request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid4())
            workspace_id = request.state.workspace_id if hasattr(request.state, "workspace_id") else uuid4()
            actor_type = request.state.actor_type if hasattr(request.state, "actor_type") else "user"
            actor_id = request.state.actor_id if hasattr(request.state, "actor_id") else "unknown"
            signature_present = "X-Signature" in request.headers

            await write_audit(
                run_id=run_id,
                request_id=request_id,
                workspace_id=workspace_id,
                actor_type=actor_type,
                actor_id=actor_id,
                provider=provider,
                action_id=action_id,
                preview_id=preview_id,
                idempotency_key=final_idempotency_key,
                signature_present=signature_present,
                params=params if params else {},
                status=status,
                error_reason=error_reason,
                http_status=http_status,
                duration_ms=duration_ms,
            )
        except Exception:
            # Audit logging failure should not break the request
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
