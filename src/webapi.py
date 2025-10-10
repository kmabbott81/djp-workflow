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
from .limits.limiter import RateLimitExceeded, get_rate_limiter
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
            if path.startswith("/actions/preview") or path.startswith("/actions/execute") or path.startswith("/audit"):
                openapi_schema["paths"][path][method]["security"] = [{"ApiKeyBearer": []}]
                # Add scope hints for documentation
                if path.startswith("/audit"):
                    openapi_schema["paths"][path][method]["description"] = (
                        openapi_schema["paths"][path][method].get("description", "")
                        + "\n\n**Required scope:** `audit:read` (admin only)"
                    )

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
    expose_headers=[
        "X-Request-ID",
        "X-Trace-Link",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After",
    ],  # Sprint 51 P2: +Rate limit headers
    max_age=600,  # Cache preflight for 10 minutes
)


# Sprint 51 Phase 2: Rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded exceptions with proper headers."""
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


# Sprint 51 Phase 2: Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # HSTS: Force HTTPS for 180 days, include subdomains, preload
    response.headers["Strict-Transport-Security"] = "max-age=15552000; includeSubDomains; preload"

    # CSP: Strict content security policy
    csp_directives = [
        "default-src 'self'",
        "connect-src 'self' https://relay-production-f2a6.up.railway.app https://*.vercel.app",
        "img-src 'self' data:",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",  # unsafe-inline needed for some UI frameworks
        "frame-ancestors 'none'",  # Prevent clickjacking
        "base-uri 'self'",
        "form-action 'self'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

    # Referrer policy: Don't leak referrer information
    response.headers["Referrer-Policy"] = "no-referrer"

    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # XSS protection (legacy, but doesn't hurt)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response


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
        "redis": False,
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

    # Check Redis connection (optional - used for rate limiting and OAuth caching)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis

            client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            client.ping()
            checks["redis"] = True
        except Exception:
            # Redis is optional - service can run without it (uses in-process fallback)
            checks["redis"] = False
    else:
        # Redis not configured - mark as true since it's optional
        checks["redis"] = True

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

        # Get actor_id from auth context
        actor_id = request.state.actor_id if hasattr(request.state, "actor_id") else "system"

        # Get request ID from telemetry middleware
        request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid4())

        # Check rate limit (per workspace)
        limiter = get_rate_limiter()
        limiter.check_limit(workspace_id)

        # Execute
        executor = get_executor()
        result = await executor.execute(
            preview_id=preview_id,
            idempotency_key=final_idempotency_key,
            workspace_id=workspace_id,
            actor_id=actor_id,
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


@app.get("/audit")
@require_scopes(["audit:read"])
async def get_audit_logs(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    provider: Optional[str] = None,
    action_id: Optional[str] = None,
    status: Optional[str] = None,
    actor_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """
    Query audit logs (admin only).

    Requires scope: audit:read

    Args:
        limit: Number of records to return (1-200, default 50)
        offset: Offset for pagination (>=0, default 0)
        provider: Filter by provider (e.g., 'independent')
        action_id: Filter by action ID (e.g., 'webhook.save')
        status: Filter by status ('ok' or 'error')
        actor_type: Filter by actor type ('user' or 'api_key')
        from_date: Start date (ISO8601)
        to_date: End date (ISO8601)

    Returns:
        List of audit log entries (redacted, no secrets)
    """
    from datetime import datetime

    from src.db.connection import get_connection

    # Validate limit
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")

    # Validate offset
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")

    # Validate status enum
    if status and status not in ["ok", "error"]:
        raise HTTPException(status_code=400, detail="status must be 'ok' or 'error'")

    # Validate actor_type enum
    if actor_type and actor_type not in ["user", "api_key"]:
        raise HTTPException(status_code=400, detail="actor_type must be 'user' or 'api_key'")

    # Get workspace_id from auth context
    workspace_id = request.state.workspace_id if hasattr(request.state, "workspace_id") else None
    if not workspace_id:
        raise HTTPException(status_code=403, detail="workspace_id not found in auth context")

    # Build query
    query = """
        SELECT
            id,
            run_id,
            request_id,
            workspace_id,
            actor_type,
            actor_id,
            provider,
            action_id,
            preview_id,
            signature_present,
            params_prefix64,
            status,
            error_reason,
            http_status,
            duration_ms,
            created_at
        FROM action_audit
        WHERE workspace_id = $1
    """
    params = [workspace_id]
    param_idx = 2

    # Add filters
    if provider:
        query += f" AND provider = ${param_idx}"
        params.append(provider)
        param_idx += 1

    if action_id:
        query += f" AND action_id = ${param_idx}"
        params.append(action_id)
        param_idx += 1

    if status:
        query += f" AND status = ${param_idx}::audit_status_enum"
        params.append(status)
        param_idx += 1

    if actor_type:
        query += f" AND actor_type = ${param_idx}::actor_type_enum"
        params.append(actor_type)
        param_idx += 1

    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            query += f" AND created_at >= ${param_idx}"
            params.append(from_dt)
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="from_date must be valid ISO8601") from None

    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            query += f" AND created_at <= ${param_idx}"
            params.append(to_dt)
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="to_date must be valid ISO8601") from None

    # Order by created_at DESC (uses index)
    query += " ORDER BY created_at DESC"

    # Pagination
    query += f" LIMIT ${param_idx} OFFSET ${param_idx + 1}"
    params.append(limit)
    params.append(offset)

    # Execute query
    async with get_connection() as conn:
        rows = await conn.fetch(query, *params)

    # Convert to dict list (redacted - no params_hash, no idempotency_key_hash)
    items = [
        {
            "id": str(row["id"]),
            "run_id": row["run_id"],
            "request_id": row["request_id"],
            "workspace_id": str(row["workspace_id"]),
            "actor_type": row["actor_type"],
            "actor_id": row["actor_id"],
            "provider": row["provider"],
            "action_id": row["action_id"],
            "preview_id": row["preview_id"],
            "signature_present": row["signature_present"],
            "params_prefix64": row["params_prefix64"],
            "status": row["status"],
            "error_reason": row["error_reason"],
            "http_status": row["http_status"],
            "duration_ms": row["duration_ms"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]

    # Calculate next_offset
    next_offset = offset + len(items) if len(items) == limit else None

    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "next_offset": next_offset,
        "count": len(items),
    }


# ============================================================================
# OAuth Endpoints - Sprint 53 Phase B
# ============================================================================


@app.get("/oauth/google/authorize")
async def oauth_google_authorize(
    request: Request,
    workspace_id: str,
    redirect_uri: Optional[str] = None,
):
    """
    Initiate Google OAuth flow.

    Args:
        workspace_id: Workspace UUID
        redirect_uri: Optional redirect URI (defaults to RELAY_PUBLIC_BASE_URL/oauth/google/callback)

    Returns:
        authorize_url: Google OAuth authorization URL with state parameter
    """
    import urllib.parse

    from src.auth.oauth.state import OAuthStateManager

    # Get environment variables
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=501, detail="Google OAuth not configured (GOOGLE_CLIENT_ID missing)")

    # Default redirect URI
    if not redirect_uri:
        base_url = os.getenv("RELAY_PUBLIC_BASE_URL", "https://relay-production-f2a6.up.railway.app")
        redirect_uri = f"{base_url}/oauth/google/callback"

    # Create state with PKCE
    state_mgr = OAuthStateManager()
    state_data = state_mgr.create_state(
        workspace_id=workspace_id, provider="google", redirect_uri=redirect_uri, use_pkce=True
    )

    # Build Google OAuth URL
    auth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/gmail.send",
        "state": state_data["state"],
        "code_challenge": state_data["code_challenge"],
        "code_challenge_method": "S256",
        "access_type": "offline",  # Request refresh token
        "prompt": "consent",  # Force consent screen to get refresh token
    }

    authorize_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(auth_params)}"

    # Emit metric
    from src.telemetry import oauth_events

    oauth_events.labels(provider="google", event="authorize_started").inc()

    return {
        "authorize_url": authorize_url,
        "state": state_data["state"],
        "expires_in": 600,  # State valid for 10 minutes
    }


@app.get("/oauth/google/callback")
async def oauth_google_callback(
    request: Request,
    code: str,
    state: str,
    workspace_id: str,
    error: Optional[str] = None,
):
    """
    Handle Google OAuth callback.

    Args:
        code: Authorization code from Google
        state: State token for CSRF protection
        workspace_id: Workspace UUID
        error: Optional error from Google

    Returns:
        success: True if tokens stored successfully
        scopes: Granted OAuth scopes
    """
    import httpx

    from src.auth.oauth.state import OAuthStateManager
    from src.auth.oauth.tokens import OAuthTokenCache

    # Check for OAuth error
    if error:
        from src.telemetry import oauth_events

        oauth_events.labels(provider="google", event="callback_error").inc()
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    # Validate state
    state_mgr = OAuthStateManager()
    state_data = state_mgr.validate_state(workspace_id=workspace_id, state=state)
    if not state_data:
        from src.telemetry import oauth_events

        oauth_events.labels(provider="google", event="invalid_state").inc()
        raise HTTPException(status_code=400, detail="Invalid or expired state token")

    # Get environment variables
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": state_data["redirect_uri"],
        "grant_type": "authorization_code",
        "code_verifier": state_data.get("code_verifier"),  # PKCE
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(token_url, data=token_data)
            if response.status_code != 200:
                from src.telemetry import oauth_events

                oauth_events.labels(provider="google", event="token_exchange_failed").inc()
                raise HTTPException(
                    status_code=502, detail=f"Token exchange failed: {response.status_code} {response.text[:200]}"
                )

            token_response = response.json()
    except httpx.TimeoutException as e:
        from src.telemetry import oauth_events

        oauth_events.labels(provider="google", event="token_exchange_timeout").inc()
        raise HTTPException(status_code=504, detail="Token exchange timeout") from e

    # Extract tokens
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    expires_in = token_response.get("expires_in")
    scope = token_response.get("scope")

    if not access_token:
        from src.telemetry import oauth_events

        oauth_events.labels(provider="google", event="missing_access_token").inc()
        raise HTTPException(status_code=502, detail="No access token in response")

    # Store tokens (encrypted)
    # TODO: Get actor_id from request context (for now using placeholder)
    actor_id = "user_temp_001"  # Will be replaced with actual user ID from auth context

    token_cache = OAuthTokenCache()
    await token_cache.store_tokens(
        provider="google",
        workspace_id=workspace_id,
        actor_id=actor_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        scope=scope,
    )

    # Emit metric
    from src.telemetry import oauth_events

    oauth_events.labels(provider="google", event="tokens_stored").inc()

    return {"success": True, "scopes": scope, "has_refresh_token": bool(refresh_token)}


@app.get("/oauth/google/status")
async def oauth_google_status(
    request: Request,
    workspace_id: str,
):
    """
    Check if workspace has Google OAuth connection.

    Args:
        workspace_id: Workspace UUID

    Returns:
        linked: True if OAuth tokens exist for this workspace
        scopes: Granted OAuth scopes (if linked)
    """
    from src.auth.oauth.tokens import OAuthTokenCache

    # TODO: Get actor_id from request context
    actor_id = "user_temp_001"

    token_cache = OAuthTokenCache()
    tokens = await token_cache.get_tokens(provider="google", workspace_id=workspace_id, actor_id=actor_id)

    if tokens:
        return {"linked": True, "scopes": tokens.get("scope", "")}
    else:
        return {"linked": False, "scopes": None}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
