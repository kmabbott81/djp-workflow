# Best‑of‑Best Agents Playbook (Debate → Judge → Publish)

**Prepared for:** Kyle  
**Date:** 2025-09-28 20:30 UTC

This file captures the essence and detailed nuance of our conversation so you can hand it to a command‑line coding agent (Claude Code, or an alternative) to **build** the system locally and later scale it into a product. It includes:

- The architecture pattern (Debate → Judge → Publish, “DJP”) and why it matters.
- Guardrails for legal/IP peace of mind.
- A builder‑grade prompt (copy/paste) for your CLI agent to implement the workflow using the **OpenAI Agents Python SDK**.
- Exact commands to run on Windows and macOS/Linux.
- Optional: an alternative CLI coding agent you can try if you want something Git‑first.

---

## 0) Where you left off (project state)

Your working project is:  
`C:\\Users\\kylem\\openai-agents-workflows-2025.09.28-v1`  
You’ve already installed **OpenAI Agents SDK v0.3.2** in a Python 3.13 environment, verified the `agents` import, and set up timestamped project logs. See: *2025.09.28-1630-PROJECT-SETUP.md* and *README.md*.

**Restore tip (Claude Code):**  
```
cd C:\\Users\\kylem\\openai-agents-workflows-2025.09.28-v1
Read the latest YYYY.MM.DD-HHMM-*.md log and continue.
```
The repo uses the log pattern `YYYY.MM.DD-HHMM-NAME.md`.

---

## 1) The core idea, distilled

**Goal:** get “best‑of‑the‑best” results by having several models attempt a task, a **judge** score and rank the drafts, and your app **publish** the **verbatim** text from a provider you allow (for legal/IP safety).

**Why DJP works:**
- **Debate (fan‑out):** multiple models = diverse reasoning styles; you’ll often surface better answers than any single run.
- **Judge (fan‑in):** a rubric turns tastes into scores (task fit, factual grounding, clarity, safety).
- **Publish:** the final, unedited text comes from a **single allowed provider**. This simplifies IP posture because the published output is exactly what that provider produced, not a derivative blend.

**Working theory disclaimer:** This pattern reduces—not eliminates—risk and sets you up to align with vendor policies later. Treat it as a principled starting point you can adapt as requirements harden.

---

## 2) Legal/IP guardrails you’ll wire in from day one

- **Verbatim publish rule:** Only publish the **exact** text from a draft produced by a provider on your “allowed list” (e.g., a provider you plan to rely on for output protections). If the top‑ranked draft isn’t allowed, fall back to the highest‑ranked allowed provider.  
- **Label edits:** If a user or your app edits the published text, flip status to **“user‑edited draft (no provider indemnity)”**.
- **Quote throttle:** Reject outputs that contain long verbatim quotes (e.g., >75 contiguous words) to avoid accidental reproduction.
- **Provenance:** Store provider, model ID, parameters, scores, and timestamps for every run. Export a Markdown log per run.
- **Grounding (optional but recommended):** When tasks are factual, require sources or connect a permissions‑safe RAG corpus.

---

## 3) What you’ll build right now (MVP scope)

- **Four debater agents**: two using OpenAI models; two via the SDK’s LiteLLM extension to call other vendors (you’ll still *publish* only from your allowed list for now).
- **One judge agent** using a strict rubric (0–10 scale).
- **Publisher** that enforces the **verbatim** rule with an `ALLOWED_PUBLISH_MODELS` list.
- **Guardrails** (simple output checks) and **logs** (timestamped Markdown).

You’ll start as a **pure Python CLI** and later wrap it in a small web UI.

---

## 4) Environment & installs

### Windows PowerShell
```powershell
# 4.1 – (If not already) ensure Python 3.11+ is available
python --version

# 4.2 – Activate your project venv (if you have one)
# Example:
# .\.venv\Scripts\Activate.ps1

# 4.3 – Keys (temporary shell vars; use a secrets manager later)
$env:OPENAI_API_KEY = "sk-..."
# Optional: other vendors for debate via LiteLLM (not required for first run)
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:GOOGLE_API_KEY    = "AIza..."
# Add Bedrock or others later if desired

# 4.4 – Packages
pip install "openai-agents[litellm]" pydantic python-dotenv
```

### macOS/Linux
```bash
python3 --version
# source .venv/bin/activate   # if using a venv
export OPENAI_API_KEY="sk-..."
# Optional for multi-vendor debate:
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."
pip install "openai-agents[litellm]" pydantic python-dotenv
```

---

## 5) **Builder Prompt** (copy/paste into your CLI coding agent)

> Paste the block below into Claude Code (or another CLI agent). It gives concrete file targets, schemas, and acceptance tests. The agent will create code **inside your existing repo** at `openai-agents-workflows-2025.09.28-v1`.

```
You are operating inside the repository:
C:\Users\kylem\openai-agents-workflows-2025.09.28-v1

Mission: Implement a minimal "Debate → Judge → Publish (Indemnified)" workflow using the OpenAI Agents **Python** SDK.

=== Constraints & principles ===
- Orchestrate with **code**, not LLM planning. Use asyncio to fan-out debaters, then judge, then publish.
- The published report MUST be the exact verbatim text from one draft written by a provider in ALLOWED_PUBLISH_MODELS.
- Keep code readable; use type hints and Pydantic models for all structured IO.
- Use the SDK’s tracing defaults; write a per-run Markdown log in the repo root: YYYY.MM.DD-HHMM-DEBATE-JUDGE-RUN.md.
- Do not leak secrets to logs.

=== Dependencies ===
Run (if not already installed):
    pip install "openai-agents[litellm]" pydantic python-dotenv

=== Create files ===
/src/config.py
    - Read env vars via os.getenv: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY.
    - ALLOWED_PUBLISH_MODELS = [
        "openai/gpt-4.1",
        "openai/gpt-4o",
        "openai/gpt-4o-mini"
      ]
    - Provide a helper to fetch per-provider API keys for LiteLLM models.

/src/schemas.py
    from pydantic import BaseModel, Field
    from typing import List

    class Draft(BaseModel):
        provider: str
        answer: str
        evidence: List[str] = []
        confidence: float = 0.0
        safety_flags: List[str] = []

    class ScoredDraft(Draft):
        score: float = 0.0
        reasons: str = ""

    class Judgment(BaseModel):
        ranked: List[ScoredDraft]
        winner_provider: str

/src/debate.py
    - Define function: async def run_debate(task: str, max_tokens: int = 1200, temperature: float = 0.3) -> list[Draft]
    - Create four Agents:
        1) OpenAI model "openai/gpt-4.1"
        2) OpenAI model "openai/gpt-4o-mini"
        3) LiteLLM model "anthropic/claude-3-5-sonnet-20240620" (only if ANTHROPIC_API_KEY set; else skip)
        4) LiteLLM model "google/gemini-1.5-pro" (only if GOOGLE_API_KEY set; else skip)
    - Each agent gets instructions:
        "Solve the task. Provide an 'answer' (<= ~250 words unless told otherwise).
         List 2–5 'evidence' bullet points (citations, sources, or reasoning steps).
         Give 'confidence' [0,1]. Add any 'safety_flags'."
    - Run all enabled debaters in parallel using asyncio.gather + the Agents SDK runner.
    - Return list[Draft] with provider names set appropriately.

/src/judge.py
    - Define function: async def judge_drafts(task: str, drafts: list[Draft]) -> Judgment
    - Create a Judge Agent (OpenAI model, e.g., "openai/gpt-4.1") with a strict rubric:
        Scoring per draft:
          * Task Fit (0–4): directly answers the user’s task and respects constraints (length, format).
          * Factual Support (0–4): claims are supported by evidence/sources given.
          * Clarity (0–2): coherent, concise, free of fluff or hedging.
        Disqualify (score = 0) if: policy concerns or obvious hallucinations.
      The judge must output a JSON object matching Judgment, with a 'ranked' list (best → worst) and 'winner_provider' chosen from the input drafts.

/src/guardrails.py
    - Implement function: def has_long_verbatim_quote(text: str, limit: int = 75) -> bool
      Return True if any substring of length >= limit appears in quotes or looks like a block quote.
    - Add: def validate_publish_text(text: str) -> None that raises ValueError if has_long_verbatim_quote(text).

/src/publish.py
    - Define function: def select_publish_text(judgment: Judgment, drafts: list[Draft], allowed: list[str]) -> tuple[str, str, str]
      Returns (status, provider, text). Status is one of: "published", "advisory_only", "none".
      Logic:
        * Find the highest-ranked draft whose provider is in allowed. If found → status="published", provider=<that>, text=<exact draft text>.
        * Else if there is at least one draft → status="advisory_only", provider=<top-ranked provider>, text=<that draft>.
        * Else → status="none".
      Call validate_publish_text(text) before returning "published".

/src/run_workflow.py
    - Implement CLI with argparse:
        --task (required)
        --max_tokens (default 1200)
        --temperature (default 0.3)
        --trace_name (default "debate-judge")
    - Steps:
        1) drafts = await run_debate(task, max_tokens, temperature)
        2) judgment = await judge_drafts(task, drafts)
        3) (status, provider, text) = select_publish_text(judgment, drafts, ALLOWED_PUBLISH_MODELS)
        4) Write Markdown log: YYYY.MM.DD-HHMM-DEBATE-JUDGE-RUN.md including:
             - task
             - table of providers, scores, reasons
             - winner_provider
             - published status and provider
             - published text (if published)
        5) Print a console summary: provider + first 300 chars.

=== Acceptance tests ===
1) OpenAI-only run:
   python -m src.run_workflow --task "Give a 180-word market brief on electric VTOL in 2025 with 3 sources."
   Expect: at least two drafts; judge ranks; publisher selects an OpenAI provider; a new log file is written; console shows provider.
2) Allowed-provider filter:
   Edit ALLOWED_PUBLISH_MODELS to only ["openai/gpt-4o-mini"], re-run. Publisher should select gpt-4o-mini even if judge #1 is another provider.
3) Verbatim publish:
   Assert the published text is byte-for-byte identical to the selected draft.
4) Guardrail:
   If the selected draft contains a quote of >=75 contiguous words, publishing should fail with a clear message.
5) No external keys:
   If ANTHROPIC/GOOGLE keys are unset, run should still succeed with the OpenAI debaters.

=== Output ===
Reply only with created/modified files and a concise summary of what you implemented. Do not include secrets.
```

---

## 6) Commands to run (end‑to‑end)

**Windows PowerShell**
```powershell
# Go to the project
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1

# Install (if needed)
pip install "openai-agents[litellm]" pydantic python-dotenv

# Set your key(s) for this shell
$env:OPENAI_API_KEY = "sk-..."

# First test run
python -m src.run_workflow --task "Write a 200-word brief on the hydrogen aviation market in 2025 with 3 sources." --trace_name "hydrogen-brief"

# Inspect the new log file in the repo root:
dir *.md
```

**macOS/Linux**
```bash
cd ~/openai-agents-workflows-2025.09.28-v1
pip install "openai-agents[litellm]" pydantic python-dotenv
export OPENAI_API_KEY="sk-..."
python -m src.run_workflow --task "Write a 200-word brief on the hydrogen aviation market in 2025 with 3 sources." --trace_name "hydrogen-brief"
ls -1 *.md
```

---

## 7) Optional: alternate CLI coding agent (Git‑first)

If you want a strictly **terminal‑native, repo‑aware** coding assistant, try a Git‑centric CLI agent. These tools work in a plain terminal, commit their changes, and propose diffs you can review. They’re great companions to Claude Code.

- **Why consider one:** tight integration with Git, patch‑style edits, and easy rollback.  
- **How to try (generic flow):**
  1. Install via `pipx` or `pip` (tool‑specific).
  2. Provide your model/provider key via env var.
  3. Run the agent from the repo root and give it the **Builder Prompt** above.
  4. Review diffs, run tests, commit when satisfied.

If you’re happy with Claude Code, you don’t need to change; this is just a toolbox upgrade for heavy terminal workflows.

---

## 8) What to build next (after MVP)
- **Grounded mode:** add a web/file search tool to one debater and require citations.  
- **Streamlit/Next.js UI:** show side‑by‑side drafts, judge scores, and a **“Publish (verbatim)”** badge.  
- **Multi‑tenant posture:** add per‑workspace logs and provider policy packs.  
- **Provenance:** attach provider/model/timestamp metadata to every export.

---

## 9) Quick FAQ

- **“Which API key do I use?”** Use a project‑scoped OpenAI API key from the developer console; you pick the model **in code** per request.  
- **“Why publish verbatim from one provider?”** It makes provenance crystal‑clear and lets you align the final step with a provider you trust for output protections.  
- **“Can I blend drafts?”** Yes—for exploratory drafts. But treat blended/edited outputs as **“user‑edited”** (different risk profile).  
- **“Do I need other vendor keys right now?”** No. Start with OpenAI; add others later for diversity in the *debate* stage.

---

## 10) Drop‑in reminder for Claude Code (or any CLI agent)

When asked “what type of workflow to start building,” answer:  
> “Build the **Debate → Judge → Publish** workflow from the ‘Builder Prompt’ in *Best‑of‑Best Agents Playbook*. Create the files under `/src`, run the acceptance tests, and write a timestamped run log.”

And you’re off.
