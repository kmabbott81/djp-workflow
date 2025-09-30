"""Streamlit UI for DJP Workflow v1.1.0-dev

Interactive interface for Debate-Judge-Publish workflow with:
- Grounded mode toggle (corpus upload)
- Provider selection
- Real-time results display
- Citations and redaction metadata viewer
- Artifact saving to runs/ui/
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_policy  # noqa: E402
from src.corpus import load_corpus  # noqa: E402
from src.publish import select_publish_text  # noqa: E402
from src.schemas import Draft, Judgment  # noqa: E402

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


async def run_djp_workflow(task: str, grounded: bool, corpus_paths: list, policy: str, enable_redaction: bool):
    """Run the full DJP workflow asynchronously."""

    # Load policy
    allowed_models = load_policy(policy)

    # Load corpus if grounded mode
    corpus_docs = None
    if grounded and corpus_paths:
        corpus_docs = load_corpus(corpus_paths)
        # TODO: Use corpus_docs for actual grounding when agents package is available

    # Run debate (mock for now - would need agents package)
    # For UI demo, we'll create mock drafts
    _ = corpus_docs  # Mark as intentionally unused in mock mode
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


def main():
    """Streamlit app main entry point."""
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    st.markdown(
        """
    Interactive UI for the Debate-Judge-Publish (DJP) workflow.
    Run debates, judge drafts, and publish with citations and redaction metadata.
    """
    )

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

        policy = st.selectbox(
            "Policy",
            ["none", "openai_only", "openai_preferred"],
            index=2,
            help="Provider allow list policy",
        )

        enable_redaction = st.toggle(
            "Enable Redaction",
            value=True,
            help="Apply PII/sensitive data redaction to published text",
        )

        run_btn = st.button("🚀 Run Workflow", type="primary")

    # Main content area
    if run_btn:
        if not task.strip():
            st.error("Please provide a task/prompt")
            return

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

        # Run workflow
        start_time = time.time()

        with st.spinner("Running DJP workflow..."):
            try:
                # Run async workflow
                result = asyncio.run(
                    run_djp_workflow(
                        task=task,
                        grounded=grounded,
                        corpus_paths=local_corpus,
                        policy=policy,
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
                        "policy": policy,
                        "corpus_paths": local_corpus,
                        "enable_redaction": enable_redaction,
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
        3. Select provider policy
        4. Click "Run Workflow" to start

        Results will show published text, citations, and redaction metadata.
        """
        )

        # Show recent runs
        st.subheader("📁 Recent Runs")
        artifacts = sorted(RUN_DIR.glob("ui-run-*.json"), reverse=True)[:5]
        if artifacts:
            for artifact in artifacts:
                with st.expander(f"Run: {artifact.stem}"):
                    data = json.loads(artifact.read_text())
                    st.json(data)
        else:
            st.write("No runs yet")


if __name__ == "__main__":
    main()
