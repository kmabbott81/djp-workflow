from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import streamlit as st

from src.config_ui import to_allowed_models
from src.templates import export_docx, export_markdown, list_templates, render_template


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


def render_templates_tab():
    st.subheader("Template Library")
    st.caption("Pick a template, edit variables, preview, run via DJP, and export results.")

    # Left: template chooser
    tdefs = list_templates()
    if not tdefs:
        st.info("No templates found. Add YAML files to ./templates/")
        return
    tkeys = [f"{t.name} · ({t.key})" for t in tdefs]
    idx = st.selectbox("Choose template", list(range(len(tdefs))), format_func=lambda i: tkeys[i])
    tdef = tdefs[idx]

    st.write(f"**Description:** {tdef.description}")
    st.markdown("---")
    st.markdown("#### Variables")

    # Editable variable form
    vars_state: dict[str, Any] = {}
    for k, v in (tdef.variables or {}).items():
        if isinstance(v, bool):
            vars_state[k] = st.checkbox(k, value=v)
        elif isinstance(v, int):
            vars_state[k] = st.number_input(k, value=int(v))
        elif isinstance(v, float):
            vars_state[k] = st.number_input(k, value=float(v), format="%.2f")
        elif isinstance(v, list):
            vars_state[k] = st.text_area(k, value="\n".join(map(str, v)), height=100)
        elif isinstance(v, dict):
            vars_state[k] = st.text_area(k, value=json.dumps(v, indent=2))
        else:
            vars_state[k] = st.text_input(k, value=str(v))

    # Normalize list/dict textareas back to Python structures
    def _normalize(v):
        if isinstance(v, str) and v.strip().startswith("{"):
            try:
                return json.loads(v)
            except Exception:
                return v
        if isinstance(v, str) and "\n" in v:
            return [ln.strip() for ln in v.splitlines() if ln.strip()]
        return v

    vars_state = {k: _normalize(v) for k, v in vars_state.items()}

    colA, colB, colC = st.columns(3)
    grounded = colA.toggle("Grounded mode", value=False)
    run_btn = colB.button("Run via DJP")
    export_md = colC.button("Export Markdown")
    export_dx = st.button("Export DOCX")

    st.markdown("#### Preview")
    preview_text = ""
    error_text = None
    try:
        preview_text = render_template(tdef.prompt, vars_state)
        st.code(preview_text or "(empty draft)")
    except Exception as e:
        error_text = f"{e}"
        st.error(error_text)

    # Save artifacts here
    out_dir = Path("runs/ui/templates")
    out_dir.mkdir(parents=True, exist_ok=True)

    if export_md and preview_text:
        fname = f"{tdef.key}-{int(time.time())}"
        p = export_markdown(preview_text, fname)
        st.success(f"Saved Markdown: {p}")

    if export_dx and preview_text:
        fname = f"{tdef.key}-{int(time.time())}"
        p = export_docx(preview_text, fname, heading=tdef.name)
        st.success(f"Saved DOCX: {p}")

    if run_btn and preview_text and not error_text:
        st.markdown("#### DJP Result")
        # reuse corpus from History/Run style: let user upload here too
        up = st.file_uploader("Optional corpus (.txt/.md/.pdf)", type=["txt", "md", "pdf"], accept_multiple_files=True)
        local_corpus = []
        if up and grounded:
            cdir = Path("runs/ui/templates/corpus")
            cdir.mkdir(parents=True, exist_ok=True)
            for f in up:
                p = cdir / f.name
                p.write_bytes(f.read())
                local_corpus.append(str(p))

        cfg = st.session_state.get("cfg", {})
        status, provider, text, reason, redaction, usage_rows = _run_once_real(
            preview_text, grounded, local_corpus, cfg
        )

        st.markdown(f"**Status:** `{status}`  **Provider:** `{provider}`")
        if reason:
            st.caption(f"Reason: {reason}")
        st.text_area("Output", text, height=240)
        if redaction:
            st.json(redaction)

        # Save a JSON artifact
        payload = {
            "template": tdef.key,
            "vars": vars_state,
            "grounded": grounded,
            "provider": provider,
            "status": status,
            "reason": reason,
            "text": text,
            "usage": usage_rows,
            "ts": int(time.time()),
        }
        fp = out_dir / f"{tdef.key}-run-{payload['ts']}.json"
        fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        st.success(f"Saved run artifact: {fp}")
