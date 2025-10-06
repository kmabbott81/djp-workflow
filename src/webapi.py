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

from .telemetry import init_telemetry
from .telemetry.middleware import TelemetryMiddleware
from .templates import list_templates
from .templates import render_template as render_template_content

app = FastAPI(title="DJP Workflow API", version="1.0.0")

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
async def preview_action(
    request: Request,
    body: dict[str, Any],
):
    """
    Preview an action before execution.

    Returns preview_id for use in /actions/execute.
    Requires ACTIONS_ENABLED=true.
    """
    if not ACTIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Actions feature not enabled")

    from .actions import PreviewRequest, get_executor

    try:
        preview_req = PreviewRequest(**body)
        executor = get_executor()
        preview = executor.preview(preview_req.action, preview_req.params)

        return {
            **preview.model_dump(),
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else str(uuid4()),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}") from e


@app.post("/actions/execute")
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
    """
    if not ACTIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Actions feature not enabled")

    from .actions import get_executor

    try:
        # Parse request
        preview_id = body.get("preview_id")
        if not preview_id:
            raise HTTPException(status_code=400, detail="preview_id required")

        # Use Idempotency-Key header if provided, otherwise from body
        final_idempotency_key = idempotency_key or body.get("idempotency_key")

        # Get request ID from telemetry middleware
        request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid4())

        # Execute
        executor = get_executor()
        result = await executor.execute(
            preview_id=preview_id,
            idempotency_key=final_idempotency_key,
            workspace_id="default",  # TODO: Get from auth
            request_id=request_id,
        )

        return result.model_dump()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
