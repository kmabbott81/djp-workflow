"""FastAPI web API for templates and triage endpoints.

Sprint 46: Added /metrics endpoint and telemetry middleware.
"""

import os
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
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

# CORS for local Outlook/VS Code development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "name": "DJP Workflow API",
        "version": "1.0.0",
        "endpoints": {
            "templates": "/api/templates",
            "render": "/api/render",
            "triage": "/api/triage",
            "health": "/_stcore/health",
            "metrics": "/metrics",
        },
    }


@app.get("/_stcore/health")
def health():
    """Health check endpoint."""
    return {"ok": True}


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
