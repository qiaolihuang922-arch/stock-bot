# CAO / Local Deployment

This is the practical local runbook for `D:\reserch\stock-bot`.

## Policy

- Windows C drive may be unreliable or freshly reinstalled.
- Put every non-system development dependency on D drive by default.
- Do not assume global Git, Bash, Python launcher, Node, npm, uv, or CAO tools exist in C-drive PATH.
- WSL itself is a Windows system feature; if it is required, keep distro files, repo, worktrees, artifacts, and runner output on D drive where feasible.
- Live Telegram delivery still needs separate Owner approval.

## Current Local Baseline

- Repo: `D:\reserch\stock-bot`
- Tool root: `D:\tools`
- Portable Git/Bash: `D:\tools\git`
- Repo Python venv: `D:\reserch\stock-bot\.venv`
- D-drive config/cache:
  - `D:\tools\gitconfig`
  - `D:\tools\home`
  - `D:\tools\cache\pip`
  - `D:\tools\cache\pytest`
  - `D:\tools\cache\npm`
  - `D:\tools\cache\uv`

## Daily Local Shell

PowerShell:

```powershell
cd D:\reserch\stock-bot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .\tools\cao_agent\local_env.ps1
```

cmd:

```cmd
cd /d D:\reserch\stock-bot
call tools\cao_agent\local_env.cmd
```

The bootstrap sets PATH, `GIT_CONFIG_GLOBAL`, `HOME`, `USERPROFILE`, `PIP_CACHE_DIR`, `PYTEST_ADDOPTS`, `NPM_CONFIG_CACHE`, `UV_CACHE_DIR`, `STOCK_BOT_REPO`, `STOCK_BOT_TOOLS`, and `STOCK_BOT_AGENT_CONTEXT`. It does not write Git config during normal startup, so parallel shells do not fight over lock files.

First-time Git config repair after a Windows reinstall:

```powershell
$env:STOCK_BOT_WRITE_GIT_CONFIG = "1"
. .\tools\cao_agent\local_env.ps1
Remove-Item Env:\STOCK_BOT_WRITE_GIT_CONFIG
```

## Local Verification

After bootstrap:

```powershell
git --version
bash --version
python --version
python -m pytest tests/test_generator_report.py -k "low_repair or failed_breakout or rr_blocker or actionability or reclaim or chase_risk or breakout_with_low_rr" -q
python -c "from app import app; from core.generator import generate_report; r=generate_report(dry_run=True); msgs=r[0] if isinstance(r, tuple) else r; print(app.name); print(len(msgs) if isinstance(msgs, list) else 1)"
```

Expected current smoke:

```text
git version 2.54.0.windows.1
GNU bash, version 5.3.9...
Python 3.12.13
12 passed, 219 deselected
app
4
```

## Rebuild D-Drive Portable Git

Use this only if `D:\tools\git` is missing.

```powershell
New-Item -ItemType Directory -Force -Path D:\tools\downloads,D:\tools\git | Out-Null
$api = Invoke-RestMethod -Uri "https://api.github.com/repos/git-for-windows/git/releases/latest" -Headers @{ "User-Agent" = "stock-bot-local-bootstrap" }
$asset = $api.assets | Where-Object { $_.name -like "PortableGit-*-64-bit.7z.exe" } | Select-Object -First 1
$dest = Join-Path "D:\tools\downloads" $asset.name
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $dest -Headers @{ "User-Agent" = "stock-bot-local-bootstrap" }
& $dest -y -o"D:\tools\git"
```

## Python / venv

Current repo `.venv` works. If it breaks, rebuild on D drive:

```powershell
cd D:\reserch\stock-bot
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
```

If global `python` is unavailable, install a portable/standalone Python under `D:\tools\python*` and add it through a local bootstrap rather than C-drive PATH.

## Known Local Issues

- `.pytest_cache` may be locked by old Windows ownership after C-drive reinstall. The bootstrap redirects pytest cache to `D:\tools\cache\pytest`, so normal tests do not need the locked folder.
- Windows `py` launcher is not required.
- Node, WSL, CAO API, and CAO UI are not restored by the current D-drive Git/Python bootstrap.

## Optional WSL / CAO Restoration

Windows native CAO is not the supported path because CAO imports Unix-only modules such as `fcntl`. Use WSL Ubuntu when CAO PM/Tech/QA orchestration is needed.

Inside WSL Ubuntu:

```bash
sudo apt update
sudo apt install -y git tmux nodejs npm python3 python3-venv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install "git+https://github.com/awslabs/cli-agent-orchestrator.git@main"
```

Standard WSL environment:

```bash
export PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/mnt/d/reserch/stock-bot/tools/cao_agent/bin
export STOCK_BOT_REPO=/mnt/d/reserch/stock-bot
export CODEX_APP_BIN=/root/.local/bin/codex-real
cd /mnt/d/reserch/stock-bot
```

Codex binary/auth, if needed:

```bash
mkdir -p /root/.local/bin /root/.codex
cp "/mnt/c/Program Files/WindowsApps/OpenAI.Codex_*/app/resources/codex" /root/.local/bin/codex-real
chmod +x /root/.local/bin/codex-real
cp /mnt/c/Users/smms0/.codex/auth.json /root/.codex/auth.json
cp /mnt/c/Users/smms0/.codex/config.toml /root/.codex/config.toml
chmod 600 /root/.codex/auth.json /root/.codex/config.toml
```

Bootstrap services:

```bash
bash tools/cao_agent/bootstrap_local.sh
bash tools/cao_agent/ensure_cao_services.sh
```

Expected URLs:

```text
CAO API: http://127.0.0.1:9889/
CAO UI: http://127.0.0.1:5173/
```

## Architect Entry

```bash
bash tools/cao_agent/run_architect_task.sh research "<research question>"
bash tools/cao_agent/run_architect_task.sh plan "<technical planning question>"
bash tools/cao_agent/run_architect_task.sh auto "<Owner task>"
```

If CAO TUI automation hangs, use local dry-run/log/artifact evidence and record the runner gap. Do not live-deliver Telegram as a workaround.

## Cleanup

`.cao_agent_context/` is local runtime output and is ignored by git:

```powershell
cd D:\reserch\stock-bot
Remove-Item -LiteralPath .\.cao_agent_context -Recurse -Force
```
