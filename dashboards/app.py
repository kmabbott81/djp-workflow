"""Streamlit UI for DJP Workflow v1.1.0-dev

Interactive interface for Debate-Judge-Publish workflow with:
- Config panel (YAML load/save, model toggles, parameters)
- Run workflow tab with grounded mode
- Run history with filters and diff viewer
- Real-mode auto-detect (uses agents if available)
"""

import asyncio
import glob
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_ui import DEFAULTS, load_config, save_config, to_allowed_models  # noqa: E402
from src.corpus import load_corpus  # noqa: E402
from src.publish import select_publish_text  # noqa: E402
from src.schemas import Draft, Judgment  # noqa: E402

# Real-mode autodetect: try imports + check env keys
REAL_MODE = False
try:
    import src.debate  # noqa: E402, F401
    import src.judge  # noqa: E402, F401

    REAL_MODE = bool(os.environ.get("OPENAI_API_KEY"))
except ImportError:
    REAL_MODE = False

APP_TITLE = "DJP Workflow UI — v1.1.0-dev"
RUN_DIR = Path("runs/ui")
RUN_DIR.mkdir(parents=True, exist_ok=True)


def save_ui_artifact(payload: dict) -> Path:
    """Save UI run artifact to disk."""
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    fp = RUN_DIR / f"ui-run-{ts}.json"
    fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return fp


def render_citations(citations):
    """Render citation list."""
    if not citations:
        st.info("No citations returned.")
        return

    for i, c in enumerate(citations, 1):
        if isinstance(c, str):
            st.markdown(f"{i}. {c}")
        elif isinstance(c, dict):
            title = c.get("title") or "Untitled"
            snippet = c.get("snippet") or ""
            url = c.get("url")
            st.markdown(f"**{i}. {title}**")
            if snippet:
                st.caption(snippet)
            if url:
                st.write(url)


def render_redaction_metadata(meta):
    """Render redaction metadata."""
    if not isinstance(meta, dict) or not meta:
        st.info("No redaction metadata.")
        return

    if meta.get("redacted"):
        st.warning(f"**Redacted:** {meta.get('redacted')}")
        events = meta.get("events", [])
        if events:
            st.write(f"**Redaction Events:** {len(events)}")
            for evt in events:
                st.json(evt)
    else:
        st.success("No redactions applied")


async def run_djp_workflow_mock(
    task: str, grounded: bool, corpus_paths: list, allowed_models: list, enable_redaction: bool
):
    """Run mock DJP workflow (no agents package needed)."""
    # Load corpus if grounded mode
    corpus_docs = None
    if grounded and corpus_paths:
        corpus_docs = load_corpus(corpus_paths)
        _ = corpus_docs  # Mark as intentionally unused in mock mode

    # Create mock drafts
    drafts = [
        Draft(
            provider="openai/gpt-4o",
            answer=f"Mock response to: {task}",
            evidence=["Source 1", "Source 2"] if grounded else [],
            confidence=0.9,
            safety_flags=[],
        ),
        Draft(
            provider="anthropic/claude-3-5-sonnet-20241022",
            answer=f"Alternative response to: {task}",
            evidence=["Source A", "Source B"] if grounded else [],
            confidence=0.85,
            safety_flags=[],
        ),
    ]

    # Mock judgment
    from src.schemas import ScoredDraft

    scored_drafts = [
        ScoredDraft(
            provider=d.provider,
            answer=d.answer,
            evidence=d.evidence,
            confidence=d.confidence,
            safety_flags=d.safety_flags,
            score=9.0 if i == 0 else 8.5,
            reasons="Good response" if i == 0 else "Also good",
            subscores=(
                {"task_fit": 4, "support": 3, "clarity": 2} if i == 0 else {"task_fit": 3, "support": 3, "clarity": 2.5}
            ),
        )
        for i, d in enumerate(drafts)
    ]

    judgment = Judgment(ranked=scored_drafts, winner_provider=scored_drafts[0].provider)

    # Select publish text
    status, provider, text, reason, redaction_metadata = select_publish_text(
        judgment, drafts, allowed_models, enable_redaction=enable_redaction
    )

    return {
        "status": status,
        "provider": provider,
        "text": text,
        "reason": reason,
        "redaction_metadata": redaction_metadata,
        "citations": drafts[0].evidence if grounded else [],
        "drafts": [{"provider": d.provider, "answer": d.answer} for d in drafts],
    }


async def run_djp_workflow_real(
    task: str,
    grounded: bool,
    corpus_paths: list,
    allowed_models: list,
    enable_redaction: bool,
    max_tokens: int,
    temperature: float,
):
    """Run real DJP workflow with agents package."""
    from src.debate import run_debate
    from src.judge import judge_drafts

    # Load corpus if grounded
    corpus_docs = None
    if grounded and corpus_paths:
        corpus_docs = load_corpus(corpus_paths)

    # Run debate
    drafts = await run_debate(
        task=task,
        max_tokens=max_tokens,
        temperature=temperature,
        corpus_docs=corpus_docs,
        allowed_models=allowed_models,
    )

    # Run judge
    judgment = await judge_drafts(
        drafts=drafts,
        task=task,
        require_citations=2 if grounded else 0,
    )

    # Select publish text
    status, provider, text, reason, redaction_metadata = select_publish_text(
        judgment, drafts, allowed_models, enable_redaction=enable_redaction
    )

    return {
        "status": status,
        "provider": provider,
        "text": text,
        "reason": reason,
        "redaction_metadata": redaction_metadata,
        "citations": (
            [{"title": e, "snippet": ""} for d in drafts for e in getattr(d, "evidence", [])] if grounded else []
        ),
        "drafts": [{"provider": d.provider, "answer": d.answer} for d in drafts],
    }


def main():
    """Streamlit app main entry point."""
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    # Mode indicator
    mode_label = "🟢 REAL MODE" if REAL_MODE else "🔵 MOCK MODE"
    st.caption(f"{mode_label} | Switch by setting OPENAI_API_KEY env var")

    # Initialize session state
    if "cfg" not in st.session_state:
        st.session_state["cfg"] = load_config(None)

    # Create tabs
    tabs = st.tabs(["▶️ Run", "📊 History", "⚙️ Config"])

    # ========== CONFIG TAB ==========
    with tabs[2]:
        st.subheader("⚙️ Configuration")

        cfg_path = st.text_input("YAML config path", value=str(Path("runs/ui/config.yaml")))

        col_a, col_b, col_c = st.columns(3)
        if col_a.button("Load", use_container_width=True):
            st.session_state["cfg"] = load_config(cfg_path)
            st.success("Config loaded")
        if col_b.button("Save", use_container_width=True):
            save_config(cfg_path, st.session_state["cfg"])
            st.success(f"Config saved to {cfg_path}")
        if col_c.button("Reset to defaults", use_container_width=True):
            st.session_state["cfg"] = DEFAULTS.copy()
            st.info("Defaults restored (not saved)")

        cfg = st.session_state["cfg"]

        # Basic settings
        st.markdown("#### Basic Settings")
        cfg["policy"] = st.selectbox(
            "Policy",
            ["none", "openai_only", "openai_preferred"],
            index=["none", "openai_only", "openai_preferred"].index(cfg.get("policy", "openai_preferred")),
        )
        cfg["temperature"] = st.slider("Temperature", 0.0, 1.0, float(cfg.get("temperature", 0.3)), 0.05)
        cfg["max_tokens"] = st.slider("Max tokens", 256, 4000, int(cfg.get("max_tokens", 1000)), 64)
        cfg["redaction_rules_path"] = st.text_input("Redaction rules path", value=cfg.get("redaction_rules_path", ""))

        # Model allowlist
        st.markdown("#### Model Allowlist by Provider")
        with st.expander("Configure allowed models"):
            cfg.setdefault("allowed_models", {})
            for provider in ["openai", "anthropic", "google"]:
                models = cfg["allowed_models"].get(provider, [])
                models_str = ",".join(models) if models else ""
                new_models_str = st.text_input(f"{provider}", value=models_str, key=f"models_{provider}")
                cfg["allowed_models"][provider] = [m.strip() for m in new_models_str.split(",") if m.strip()]

        st.session_state["cfg"] = cfg

    # ========== RUN TAB ==========
    with tabs[0]:
        st.subheader("▶️ Run Workflow")

        with st.sidebar:
            st.header("⚙️ Run Settings")

            task = st.text_area(
                "Task / Prompt",
                value="Summarize the key features of the DJP workflow in two sentences.",
                height=120,
                help="The task or question for the debate agents",
            )

            grounded = st.toggle(
                "Grounded Mode",
                value=False,
                help="Enable corpus-based grounding with uploaded documents",
            )

            uploaded_files = []
            if grounded:
                uploaded_files = st.file_uploader(
                    "Upload Corpus Files",
                    type=["txt", "md", "pdf"],
                    accept_multiple_files=True,
                    help="Upload .txt, .md, or .pdf files for grounding",
                )

            enable_redaction = st.toggle(
                "Enable Redaction",
                value=True,
                help="Apply PII/sensitive data redaction to published text",
            )

            run_btn = st.button("🚀 Run Workflow", type="primary")

        # Handle corpus file uploads
        local_corpus = []
        if uploaded_files and grounded:
            corpus_dir = RUN_DIR / "corpus"
            corpus_dir.mkdir(exist_ok=True, parents=True)
            with st.spinner("Uploading corpus files..."):
                for f in uploaded_files:
                    p = corpus_dir / f.name
                    p.write_bytes(f.read())
                    local_corpus.append(str(p))
            st.success(f"Uploaded {len(local_corpus)} corpus files")

        if run_btn:
            if not task.strip():
                st.error("Please provide a task/prompt")
            else:
                start_time = time.time()

                with st.spinner("Running DJP workflow..."):
                    try:
                        cfg = st.session_state.get("cfg", {})
                        allowed_models = to_allowed_models(cfg)
                        max_tokens = int(cfg.get("max_tokens", 1000))
                        temperature = float(cfg.get("temperature", 0.3))

                        # Run workflow (real or mock)
                        if REAL_MODE:
                            result = asyncio.run(
                                run_djp_workflow_real(
                                    task=task,
                                    grounded=grounded,
                                    corpus_paths=local_corpus,
                                    allowed_models=allowed_models,
                                    enable_redaction=enable_redaction,
                                    max_tokens=max_tokens,
                                    temperature=temperature,
                                )
                            )
                        else:
                            result = asyncio.run(
                                run_djp_workflow_mock(
                                    task=task,
                                    grounded=grounded,
                                    corpus_paths=local_corpus,
                                    allowed_models=allowed_models,
                                    enable_redaction=enable_redaction,
                                )
                            )

                        duration = time.time() - start_time

                        # Display results
                        st.success(f"✅ Workflow completed in {duration:.2f}s")

                        # Status and provider
                        col1, col2 = st.columns(2)
                        with col1:
                            status_emoji = "✅" if result["status"] == "published" else "⚠️"
                            st.metric("Status", f"{status_emoji} {result['status']}")
                        with col2:
                            st.metric("Provider", result["provider"])

                        if result.get("reason"):
                            st.warning(f"**Reason:** {result['reason']}")

                        # Published text
                        st.subheader("📝 Published Text")
                        st.text_area(
                            "Output",
                            value=result["text"],
                            height=200,
                            label_visibility="collapsed",
                        )

                        # Two-column layout for citations and redaction
                        col_left, col_right = st.columns(2)

                        with col_left:
                            st.subheader("📚 Citations")
                            render_citations(result.get("citations", []))

                        with col_right:
                            st.subheader("🔒 Redaction Metadata")
                            render_redaction_metadata(result.get("redaction_metadata", {}))

                        # Drafts section (collapsible)
                        with st.expander("View All Drafts"):
                            for i, draft in enumerate(result.get("drafts", []), 1):
                                st.markdown(f"**Draft {i} ({draft['provider']})**")
                                st.write(draft["answer"])
                                st.divider()

                        # Save artifact
                        payload = {
                            "ts": datetime.utcnow().isoformat(),
                            "task": task,
                            "settings": {
                                "grounded": grounded,
                                "corpus_paths": local_corpus,
                                "policy": cfg.get("policy"),
                                "allowed_models": allowed_models,
                                "enable_redaction": enable_redaction,
                                "temperature": temperature,
                                "max_tokens": max_tokens,
                                "mode": "real" if REAL_MODE else "mock",
                            },
                            "result": result,
                            "latency_s": round(duration, 3),
                        }
                        fp = save_ui_artifact(payload)
                        st.info(f"💾 Artifact saved: `{fp.name}`")

                    except Exception as e:
                        st.error(f"❌ Workflow failed: {str(e)}")
                        st.exception(e)
        else:
            # Show instructions when not running
            st.info(
                """
            **Instructions:**
            1. Enter your task/prompt in the sidebar
            2. Toggle grounded mode and upload corpus files if needed
            3. Configure settings in the Config tab (optional)
            4. Click "Run Workflow" to start

            Results will show published text, citations, and redaction metadata.
            """
            )

    # ========== HISTORY TAB ==========
    with tabs[1]:
        st.subheader("📊 Run History")

        # Load all run artifacts
        rows = []
        for fn in sorted(glob.glob(str(RUN_DIR / "ui-run-*.json")))[-500:]:
            try:
                data = json.load(open(fn, encoding="utf-8"))
                ts = data.get("ts", "")
                prov = data.get("result", {}).get("provider", "")
                stat = data.get("result", {}).get("status", "")
                mode = data.get("settings", {}).get("mode", "unknown")
                rows.append({"file": fn, "ts": ts, "provider": prov, "status": stat, "mode": mode})
            except Exception:
                pass

        if not rows:
            st.info("No runs found yet. Run a workflow to see history.")
        else:
            import pandas as pd

            df = pd.DataFrame(rows)

            # Filters
            st.markdown("#### Filters")
            c1, c2, c3, c4 = st.columns(4)
            prov_f = c1.multiselect("Provider", sorted(df["provider"].dropna().unique().tolist()))
            stat_f = c2.multiselect("Status", sorted(df["status"].dropna().unique().tolist()))
            mode_f = c3.multiselect("Mode", sorted(df["mode"].dropna().unique().tolist()))

            # Date range filter (simplified for now)
            show_last_n = c4.slider("Show last N runs", 5, 100, 20)

            # Apply filters
            dfv = df.copy()
            if prov_f:
                dfv = dfv[dfv["provider"].isin(prov_f)]
            if stat_f:
                dfv = dfv[dfv["status"].isin(stat_f)]
            if mode_f:
                dfv = dfv[dfv["mode"].isin(mode_f)]

            dfv = dfv.tail(show_last_n)

            st.dataframe(dfv, use_container_width=True, hide_index=True)

            # Diff viewer
            st.markdown("#### 🔍 Diff Viewer")
            st.caption("Select two runs to compare published text and redaction metadata")

            col1, col2 = st.columns(2)
            file_list = dfv["file"].tolist() if not dfv.empty else []
            f1 = col1.selectbox("Left run", file_list, index=0 if file_list else None, key="diff_left")
            f2 = col2.selectbox(
                "Right run", file_list, index=1 if len(file_list) > 1 else 0 if file_list else None, key="diff_right"
            )

            if f1 and f2 and f1 != f2:
                d1 = json.load(open(f1, encoding="utf-8"))
                d2 = json.load(open(f2, encoding="utf-8"))

                st.write("##### 📝 Published Text Diff")
                import difflib

                left = (d1.get("result", {}) or {}).get("text", "").splitlines()
                right = (d2.get("result", {}) or {}).get("text", "").splitlines()
                diff = difflib.unified_diff(left, right, fromfile=f1, tofile=f2, lineterm="")
                diff_text = "\n".join(diff)
                st.code(diff_text or "(no textual diff)", language="diff")

                st.write("##### 🔒 Redaction Metadata (Left vs Right)")
                col_a, col_b = st.columns(2)
                col_a.json((d1.get("result", {}) or {}).get("redaction_metadata", {}))
                col_b.json((d2.get("result", {}) or {}).get("redaction_metadata", {}))

                st.write("##### ⚙️ Settings Comparison")
                col_c, col_d = st.columns(2)
                col_c.json(d1.get("settings", {}))
                col_d.json(d2.get("settings", {}))
            elif f1 and f2 and f1 == f2:
                st.warning("Please select two different runs to compare")


if __name__ == "__main__":
    main()
