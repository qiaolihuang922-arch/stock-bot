# CAO Agent Runners

This directory contains the Architect-controlled runner scripts and agent profile templates for stock-bot.

## What Lives Here

- `run_architect_task.sh`: Owner-facing Architect entry.
- `run_project_research.sh`, `run_tech_plan.sh`, `run_tech_write.sh`, `run_qa_code.sh`, `run_online_agent.sh`: lower-level runner scripts used by Architect.
- `env.sh`: repo-relative paths and overridable runtime variables.
- `bin/codex`: Codex wrapper; uses `sandbox-exec` on macOS and direct `CODEX_APP_BIN` on Linux/WSL.
- `profiles/stock_*.md.template`: PM / Tech / QA / research / security agent profiles.
- `bootstrap_local.sh`: installs profiles and prepares agent worktree.
- `ensure_cao_services.sh`: starts or checks CAO API and UI.

## Required Reading

Before running CAO locally, read:

```text
tools/cao_agent/DEPLOYMENT.md
```

That file is the source of truth for the current D-drive-first Windows bootstrap, optional WSL/CAO path, and known runner issues.

## Standard WSL Environment

```bash
export PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/mnt/d/reserch/stock-bot/tools/cao_agent/bin
export STOCK_BOT_REPO=/mnt/d/reserch/stock-bot
export CODEX_APP_BIN=/root/.local/bin/codex-real
cd /mnt/d/reserch/stock-bot
```

## Setup

For normal local Python/Git work on Windows, start with:

```powershell
cd D:\reserch\stock-bot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .\tools\cao_agent\local_env.ps1
```

Only use the WSL setup below when CAO orchestration is needed:

```bash
bash tools/cao_agent/bootstrap_local.sh
bash tools/cao_agent/ensure_cao_services.sh
```

Expected URLs:

```text
CAO API: http://127.0.0.1:9889/
CAO UI: http://127.0.0.1:5173/
```

## Daily Entry

```bash
bash tools/cao_agent/run_architect_task.sh research "<research question>"
bash tools/cao_agent/run_architect_task.sh plan "<technical planning question>"
bash tools/cao_agent/run_architect_task.sh auto "<Owner task>"
```

## Safety

- Agents do not commit, push, live Telegram, live Supabase write, or production backfill.
- Product/report/strategy changes still need PM -> Tech -> QA evidence unless Owner explicitly grants direct-code authority for the current task.
- If CAO automation hangs, fall back to dry-run/log/artifact evidence and record the runner gap. Do not bypass with live delivery.

## Runtime Cleanup

`.cao_agent_context/` contains local runner context/output and is ignored by git. Remove it when stale or misleading:

```powershell
cd D:\reserch\stock-bot
Remove-Item -LiteralPath .\.cao_agent_context -Recurse -Force
```
