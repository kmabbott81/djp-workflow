from __future__ import annotations

import json
import time
from datetime import date as date_type
from pathlib import Path
from typing import Any

import streamlit as st

from src.config_ui import to_allowed_models
from src.templates import (
    InputDef,
    TemplateRenderError,
    export_docx,
    export_markdown,
    list_templates,
    render_template,
    to_slug,
    validate_inputs,
)


# Optional: import real path; fallback to select() mock if not available
def _run_once_real(draft_text: str, grounded: bool, local_corpus, cfg: dict[str, Any]):
    """Try real DJP; fallback to select(). Returns (status, provider, text, reason, redaction, usage_rows)."""
    try:
        from src.corpus import load_corpus
        from src.debate import run_debate
        from src.judge import judge_drafts
        from src.publish import select_publish_text

        corpus_docs = load_corpus(local_corpus) if grounded else None
        drafts = run_debate(
            task=draft_text,
            max_tokens=int(cfg.get("max_tokens", 1000)),
            temperature=float(cfg.get("temperature", 0.3)),
            corpus_docs=corpus_docs,
            allowed_models=to_allowed_models(cfg),
        )
        if hasattr(drafts, "__await__"):
            import asyncio

            drafts = asyncio.get_event_loop().run_until_complete(drafts)
        judgment = judge_drafts(
            drafts=drafts, task=draft_text, require_citations=2 if grounded else 0, corpus_docs=corpus_docs
        )
        if hasattr(judgment, "__await__"):
            import asyncio

            judgment = asyncio.get_event_loop().run_until_complete(judgment)
        status, provider, text, reason, redaction = select_publish_text(judgment)
        usage_rows = []
        try:
            for d in drafts:
                pr = getattr(d, "provider", "")
                pt = int(getattr(d, "prompt_tokens", 0))
                ct = int(getattr(d, "completion_tokens", 0))
                usage_rows.append(
                    {"phase": "debate", "provider": pr, "prompt_tokens": pt, "completion_tokens": ct, "latency_s": 0}
                )
            pr = getattr(judgment, "provider", provider or "")
            pt = int(getattr(judgment, "prompt_tokens", 0))
            ct = int(getattr(judgment, "completion_tokens", 0))
            usage_rows.append(
                {"phase": "judge", "provider": pr, "prompt_tokens": pt, "completion_tokens": ct, "latency_s": 0}
            )
            usage_rows.append(
                {
                    "phase": "select",
                    "provider": provider or "",
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "latency_s": 0,
                }
            )
        except Exception:
            pass
        return status, provider, text, reason, redaction, usage_rows
    except Exception:
        from src.publish import select_publish_text

        status, provider, text, reason, redaction = select_publish_text({"text": draft_text, "grounded": grounded})
        return status, provider, text, reason, redaction, []


def _render_input_widget(inp: InputDef) -> Any:
    """
    Render appropriate Streamlit widget based on input type.

    Args:
        inp: InputDef describing the input field

    Returns:
        User input value
    """
    help_text = inp.help if inp.help else None
    label = f"{inp.label}{'*' if inp.required else ''}"

    # String type
    if inp.type == "string":
        return st.text_input(label, value=str(inp.default or ""), help=help_text, placeholder=inp.placeholder or "")

    # Text type (multiline)
    elif inp.type == "text":
        return st.text_area(
            label, value=str(inp.default or ""), help=help_text, height=100, placeholder=inp.placeholder or ""
        )

    # Integer type
    elif inp.type == "int":
        min_val = inp.validators.get("min", 0)
        max_val = inp.validators.get("max", 1000000)
        default_val = int(inp.default) if inp.default is not None else min_val
        return st.number_input(label, min_value=min_val, max_value=max_val, value=default_val, step=1, help=help_text)

    # Float type
    elif inp.type == "float":
        min_val = float(inp.validators.get("min", 0.0))
        max_val = float(inp.validators.get("max", 1000000.0))
        default_val = float(inp.default) if inp.default is not None else min_val
        return st.number_input(
            label, min_value=min_val, max_value=max_val, value=default_val, step=0.1, format="%.2f", help=help_text
        )

    # Boolean type
    elif inp.type == "bool":
        default_val = bool(inp.default) if inp.default is not None else False
        return st.checkbox(label, value=default_val, help=help_text)

    # Enum type (single select)
    elif inp.type == "enum":
        choices = inp.validators.get("choices", [])
        if not choices:
            st.error(f"Enum field '{inp.label}' has no choices defined")
            return None
        default_idx = 0
        if inp.default and inp.default in choices:
            default_idx = choices.index(inp.default)
        return st.selectbox(label, choices, index=default_idx, help=help_text)

    # Multiselect type
    elif inp.type == "multiselect":
        choices = inp.validators.get("choices", [])
        if not choices:
            st.error(f"Multiselect field '{inp.label}' has no choices defined")
            return []
        default_val = inp.default if isinstance(inp.default, list) else []
        return st.multiselect(label, choices, default=default_val, help=help_text)

    # Date type
    elif inp.type == "date":
        try:
            if inp.default:
                from datetime import datetime

                default_val = datetime.strptime(str(inp.default), "%Y-%m-%d").date()
            else:
                default_val = date_type.today()
        except Exception:
            default_val = date_type.today()
        return st.date_input(label, value=default_val, help=help_text)

    # Email type (text input with validation)
    elif inp.type == "email":
        return st.text_input(label, value=str(inp.default or ""), help=help_text, placeholder="user@example.com")

    # URL type (text input with validation)
    elif inp.type == "url":
        return st.text_input(label, value=str(inp.default or ""), help=help_text, placeholder="https://example.com")

    # Fallback
    else:
        st.warning(f"Unknown input type: {inp.type}")
        return st.text_input(label, value=str(inp.default or ""), help=help_text)


def render_templates_tab():
    """Render the Templates tab with type-aware widgets and inline validation."""
    st.subheader("Template Library")
    st.caption("Pick a template, edit variables, preview, run via DJP, and export results.")

    # Load templates
    tdefs = list_templates()
    if not tdefs:
        st.info("No templates found. Add YAML files to ./templates/")
        st.info("Templates must conform to schemas/template.json")
        return

    # Template selector
    tkeys = [f"{t.name} (v{t.version}) · {t.key}" for t in tdefs]
    idx = st.selectbox("Choose template", list(range(len(tdefs))), format_func=lambda i: tkeys[i])
    template = tdefs[idx]

    # Display template info
    st.write(f"**Description:** {template.description}")
    st.caption(f"Context: {template.context} | Version: {template.version} | Path: {template.path.name}")
    st.markdown("---")

    # Input form
    st.markdown("#### Input Variables")
    vars_state: dict[str, Any] = {}

    for inp in template.inputs:
        value = _render_input_widget(inp)
        vars_state[inp.id] = value

    st.markdown("---")

    # Validate inputs
    validation_errors = validate_inputs(template, vars_state)
    if validation_errors:
        st.error("**Validation Errors:**")
        for err in validation_errors:
            st.error(f"• {err}")

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    grounded = col1.toggle("Grounded mode", value=False)
    preview_btn = col2.button("Preview", disabled=bool(validation_errors))
    run_btn = col3.button("Run via DJP", disabled=bool(validation_errors))
    export_section = col4.expander("Export")

    with export_section:
        export_md = st.button("Export Markdown")
        export_dx = st.button("Export DOCX")

    # Preview section
    if preview_btn:
        st.markdown("#### Preview")
        try:
            preview_text = render_template(template, vars_state)
            st.code(preview_text, language="markdown")
        except TemplateRenderError as e:
            st.error(f"**Render Error:** {e}")
        except Exception as e:
            st.error(f"**Unexpected Error:** {e}")

    # Export handlers
    if export_md and not validation_errors:
        try:
            preview_text = render_template(template, vars_state)
            fname = f"{to_slug(template.name)}-{int(time.time())}"
            p = export_markdown(preview_text, fname)
            st.success(f"Saved Markdown: {p}")
        except Exception as e:
            st.error(f"Export failed: {e}")

    if export_dx and not validation_errors:
        try:
            preview_text = render_template(template, vars_state)
            fname = f"{to_slug(template.name)}-{int(time.time())}"
            p = export_docx(preview_text, fname, heading=template.name)
            st.success(f"Saved DOCX: {p}")
        except Exception as e:
            st.error(f"Export failed: {e}")

    # Run via DJP
    if run_btn and not validation_errors:
        st.markdown("#### DJP Result")

        # Corpus upload
        up = st.file_uploader("Optional corpus (.txt/.md/.pdf)", type=["txt", "md", "pdf"], accept_multiple_files=True)
        local_corpus = []
        if up and grounded:
            cdir = Path("runs/ui/templates/corpus")
            cdir.mkdir(parents=True, exist_ok=True)
            for f in up:
                p = cdir / f.name
                p.write_bytes(f.read())
                local_corpus.append(str(p))

        try:
            # Render template first
            draft_text = render_template(template, vars_state)

            # Run DJP
            cfg = st.session_state.get("cfg", {})
            status, provider, text, reason, redaction, usage_rows = _run_once_real(
                draft_text, grounded, local_corpus, cfg
            )

            st.markdown(f"**Status:** `{status}`  **Provider:** `{provider}`")
            if reason:
                st.caption(f"Reason: {reason}")
            st.text_area("Output", text, height=240)
            if redaction:
                st.json(redaction)

            # Save artifact
            out_dir = Path("runs/ui/templates")
            out_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "template": template.key,
                "template_version": template.version,
                "vars": vars_state,
                "grounded": grounded,
                "provider": provider,
                "status": status,
                "reason": reason,
                "text": text,
                "usage": usage_rows,
                "ts": int(time.time()),
            }
            fp = out_dir / f"{to_slug(template.key)}-run-{payload['ts']}.json"
            fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            st.success(f"Saved run artifact: {fp}")

        except TemplateRenderError as e:
            st.error(f"**Render Error:** {e}")
        except Exception as e:
            st.error(f"**Error:** {e}")
