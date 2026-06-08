# CAO Local Deployment

This document records the current working local deployment path for the stock-bot CAO runner. It is intentionally practical: follow this before trying to run Architect / PM / Tech / QA agents.

## Current Status

- Windows native CAO is not the supported path for this repo. The CAO Python package imports Unix-only modules such as `fcntl`.
- The supported local path is WSL Ubuntu.
- CAO API and UI can run from WSL and are reachable from Windows:
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- Live Telegram delivery remains forbidden unless Owner gives separate approval for that exact action.

## Required Runtime

Install or verify these inside WSL Ubuntu:

```bash
sudo apt update
sudo apt install -y git tmux nodejs npm python3 python3-venv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install "git+https://github.com/awslabs/cli-agent-orchestrator.git@main"
```

The Codex desktop app on Windows contains a Linux Codex binary at the app resource path. Copy it into WSL and make it executable:

```bash
mkdir -p /root/.local/bin
cp "/mnt/c/Program Files/WindowsApps/OpenAI.Codex_*/app/resources/codex" /root/.local/bin/codex-real
chmod +x /root/.local/bin/codex-real
/root/.local/bin/codex-real --version
```

Copy Codex auth/config from Windows to WSL root. Do not print file contents.

```bash
mkdir -p /root/.codex
cp /mnt/c/Users/smms0/.codex/auth.json /root/.codex/auth.json
cp /mnt/c/Users/smms0/.codex/config.toml /root/.codex/config.toml
chmod 600 /root/.codex/auth.json /root/.codex/config.toml
```

## Standard Env

Use this shell environment for CAO commands:

```bash
export PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/mnt/d/reserch/stock-bot/tools/cao_agent/bin
export STOCK_BOT_REPO=/mnt/d/reserch/stock-bot
export CODEX_APP_BIN=/root/.local/bin/codex-real
cd /mnt/d/reserch/stock-bot
```

## Bootstrap / Services

```bash
bash tools/cao_agent/bootstrap_local.sh
bash tools/cao_agent/ensure_cao_services.sh
```

Expected service output:

```text
CAO API: http://127.0.0.1:9889/
CAO UI: http://127.0.0.1:5173/
```

Verify from Windows PowerShell:

```powershell
Invoke-WebRequest http://127.0.0.1:9889/docs
Invoke-WebRequest http://127.0.0.1:5173/
```

## Daily Entry

Architect entry points:

```bash
bash tools/cao_agent/run_architect_task.sh research "<research question>"
bash tools/cao_agent/run_architect_task.sh plan "<technical planning question>"
bash tools/cao_agent/run_architect_task.sh auto "<Owner task>"
```

If CAO TUI automation hangs, do not live-deliver Telegram as a workaround. Use local dry-run/log/artifact evidence and record the runner gap in `DISPATCH.md` / `CURRENT_STATE.md`.

## Known Problems And Fixes

- `ModuleNotFoundError: No module named 'fcntl'`
  - Cause: trying to run CAO natively on Windows.
  - Fix: use WSL Ubuntu.
- `set: pipefail\r: invalid option name`
  - Cause: shell scripts checked out with CRLF.
  - Fix: `.gitattributes` keeps `tools/cao_agent/*.sh`, `tools/cao_agent/bin/*`, and sandbox profiles as LF.
- `/usr/bin/arch -arm64 /usr/local/bin/npm` fails
  - Cause: old macOS-only command in service launcher.
  - Fix: `ensure_cao_services.sh` uses `NPM_BIN` / `npm`.
- WindowsApps Codex cannot be executed directly from WSL path reliably
  - Fix: copy the binary to `/root/.local/bin/codex-real` and set `CODEX_APP_BIN`.
- Codex CLI shows login screen inside CAO
  - Fix: copy Windows Codex auth/config into `/root/.codex` with `chmod 600`.
- Codex CLI shows workspace trust prompt
  - Fix: start Codex once in the repo root from WSL and accept trust.
- CAO/Codex TUI prompt send can hang
  - Current status: unresolved runner automation gap. Use dry-run/log/artifact evidence until fixed.

## Cleanup

`.cao_agent_context/` is runtime output and is ignored by git. It can be removed when stale:

```powershell
cd D:\reserch\stock-bot
Remove-Item -LiteralPath .\.cao_agent_context -Recurse -Force
```
