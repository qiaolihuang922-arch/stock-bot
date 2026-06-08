# DISPATCH.md

## Active

- task_md_holds: `telegram_denoise_and_deployment_docs_20260608`
- status: `qa_passed`
- owner_request:
  1. Delete `【先看結論】`.
  2. Do real denoise, not blind dedupe.
  3. Clean invalid files.
  4. Improve process and deployment docs with problems encountered so far.

## Current Result

- `.cao_agent_context/` runtime output removed.
- `tools/cao_agent/DEPLOYMENT.md` rewritten for Windows + WSL current path.
- `tools/cao_agent/README.md` rewritten and linked to deployment doc.
- Product patch implemented:
  - removed first-read preface.
  - afterhours holding cards are shorter but keep per-stock decision/risk/action.
  - afterhours rejected unheld cards are shorter but keep blocker/gap/trigger/price.
  - version `v20.4.49`.

## Next Action

- Use the local dry-run command below for report preview.
- No live Telegram delivery was run in this task.

## Fixed Commands

Local dry-run only, no live Telegram:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```

WSL CAO service check:

```bash
export PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/mnt/d/reserch/stock-bot/tools/cao_agent/bin
export STOCK_BOT_REPO=/mnt/d/reserch/stock-bot
export CODEX_APP_BIN=/root/.local/bin/codex-real
cd /mnt/d/reserch/stock-bot
bash tools/cao_agent/ensure_cao_services.sh
```
