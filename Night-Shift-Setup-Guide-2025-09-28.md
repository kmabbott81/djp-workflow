# Night Shift Kit — Keep Your Agents Project Moving After Claude Code’s Limit

**Prepared for:** Kyle  
**Updated:** 2025-09-28 20:47 UTC

This kit gives you two practical “night shift” options that can access the **same repo** and keep work going:

1. **Aider (CLI coding agent)** — a terminal-native, Git-first coding agent you can swap in when Claude Code is rate-limited.  
2. **NightShift Runner (queue processor)** — a tiny Python daemon that watches a `tasks/` folder and runs your **Agents SDK** workflow on queued task files, logging results. No coding agent required.

Both options operate in your existing project:  
`C:\\Users\\kylem\\openai-agents-workflows-2025.09.28-v1`

Your repo already has the log naming convention `YYYY.MM.DD-HHMM-NAME.md` and notes on how to restore a session. Use those to resume context at any time.  

---

## Option A — Aider: a Git‑first CLI coding agent (night shift replacement for Claude Code)

**Why Aider:** It runs in your terminal, edits files patch‑by‑patch, and auto‑commits changes with clear messages, which makes merges safe and reviewable. It can add specific files to the chat on the command line or via `/add`, and has an `/architect` mode for higher‑level refactors. Note: install & usage details summarized below; see citations in the response for the official docs.

### Install (Windows PowerShell)

```powershell
python -m pip install --user pipx   # if pipx isn't installed
pipx install aider-chat
```

### Launch on a dedicated branch

```powershell
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1
git checkout -b night-shift-2025.09.28-2047
$env:OPENAI_API_KEY = "sk-..."   # reuse your existing key
# Start aider, preloading the playbook so it knows the plan:
aider --model gpt-4.1 Best-of-Best-Agents-Playbook-2025-09-28.md README.md
```

Inside Aider, paste:
```
Read "Best-of-Best-Agents-Playbook-2025-09-28.md".
Implement the **Builder Prompt**: create /src files, run the acceptance tests, and write a timestamped run log.
```
Tips:
- Add/remove files with `/add` or by naming them on the CLI.
- Aider auto‑commits by default; review diffs as you go. Use `git log` to inspect changes.
- When Claude Code is back, either continue on this branch or merge into main.

---

## Option B — NightShift Runner (queue processor)

This is a simple loop that watches a `tasks/` folder for `*.task.md` files and runs your **Agents SDK** CLI (`python -m src.run_workflow ...`) for each task. It renames processed tasks into `tasks/done/` with a timestamp.

### Files in this kit
- `nightshift_runner.py` — the watcher/runner (drop into your repo root).
- `run-nightshift.ps1` — starts the runner with your repo and tasks directory.
- `tasks/2025.09.28-2200-sample.task.md` — a sample task file & a schema you can copy.

### How to install

1) Copy these files into your repo root:
```
nightshift_runner.py
run-nightshift.ps1
tasks\2025.09.28-2200-sample.task.md
```
2) Ensure your project is installed per the playbook (Agents SDK + python-dotenv).  
3) Create a `.env` in the repo root (optional) with your keys, or set `OPENAI_API_KEY` in your shell/session.

### Run once (manual test)

```powershell
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1
# (optional) create more tasks by copying the sample and editing the TASK line
python nightshift_runner.py --repo . --tasks-dir .\tasks --interval 0 --oneshot
```

### Run in the background (scheduled)

**Option 1: Task Scheduler GUI**  
- Open **Task Scheduler** → **Create Basic Task…** → Name: *Agents Night Shift*  
- Trigger: **Daily** at 1:00 AM (or your preference)  
- Action: **Start a program** → `powershell.exe`  
  - **Add arguments:** `-ExecutionPolicy Bypass -File "C:\Users\kylem\openai-agents-workflows-2025.09.28-v1\run-nightshift.ps1"`  
- Finish. Test **Run** once to verify.

**Option 2: PowerShell (scripted)**
```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-ExecutionPolicy Bypass -File "C:\Users\kylem\openai-agents-workflows-2025.09.28-v1\run-nightshift.ps1"'
$trigger = New-ScheduledTaskTrigger -Daily -At 1am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "Agents Night Shift" -Description "Run Agents night shift queue"
```

### Task file schema

Each task file can be very simple; the runner supports two formats:

**A) YAML front matter**
```yaml
---
task: "Write a 200-word brief on the hydrogen aviation market in 2025 with 3 sources."
max_tokens: 1200
temperature: 0.3
trace_name: hydrogen-brief
---
# Optional extra context below
```

**B) Minimal text format**
```
TASK: Write a 200-word brief on the hydrogen aviation market in 2025 with 3 sources.
MAX_TOKENS: 1200
TEMPERATURE: 0.3
TRACE_NAME: hydrogen-brief
```

Processed files are moved to `tasks/done/` with a timestamp suffix.

---

## Suggested workflow (how these pieces cooperate)

- **Day shift (Claude Code):** use the playbook to build/extend the Agents workflow.  
- **Night shift (Aider):** continue coding on a `night-shift-*` branch; it will auto‑commit patch‑sized changes.  
- **Night shift (Runner):** in parallel, keep producing reports by dropping `*.task.md` files into `tasks/`.  
- **Morning:** diff & merge code changes from `night-shift-*` into your main branch; review the nightly report logs written by the workflow.

Your repo’s existing logs and setup notes make resuming work easy if a process stops. fileciteturn0file0 fileciteturn0file1

---

## Safety & hygiene

- Keep API keys in `.env` (loaded by `python-dotenv`) or your user environment.  
- Git‑ignore `tasks/done/*.md` if tasks contain sensitive prompts.  
- The publish step in your workflow should output **verbatim** from an allowed provider; flagged outputs should not publish.

---

## Ready-made commands (copy/paste)

**Start Aider on a fresh branch:**
```powershell
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1
git checkout -b night-shift-2025.09.28-2047
$env:OPENAI_API_KEY = "sk-..."
aider --model gpt-4.1 Best-of-Best-Agents-Playbook-2025-09-28.md README.md
```

**Kick off the runner manually:**
```powershell
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1
python nightshift_runner.py --repo . --tasks-dir .\tasks --interval 0 --oneshot
```
