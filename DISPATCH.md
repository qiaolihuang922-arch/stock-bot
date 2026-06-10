# DISPATCH.md

## Active

- task_md_holds: `render_dispatch_writeback_logic_20260610`
- status: `complete`
- owner_request:
  - Correct the writeback analysis to the actual Render five-minute dispatch model.
  - Fix the logic that prevented post-close market/theme freshness writes.
  - Update Markdown so the execution model is clear.
  - No live Telegram delivery.

## Current Result

- Corrected root cause:
  - Production timing is Render -> GitHub `workflow_dispatch`, not GitHub native cron.
  - Previous GitHub schedule change was the wrong layer.
  - Render close dispatch previously started at `13:20`, but freshness safe-write default is `14:00`; after `14:00`, Render route skipped, so market/theme preflight could miss the write window.
- Fix:
  - Removed GitHub native cron schedule.
  - Render intraday buckets now use five-minute cadence.
  - Render close dispatch now runs during `14:00..14:29 Asia/Taipei`.
  - Render dispatch payload explicitly sends `run_mode=bot`.
  - Existing market/theme freshness preflight remains before GitHub dispatch.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_render_preflight.py tests/test_workflow_runtime_config.py tests/test_phase3_evidence_automation.py -q --tb=short
```

Result: `27 passed, 8 skipped`.

## Fixed Commands

Local Render/dispatch contract tests:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest tests/test_app_render_preflight.py tests/test_workflow_runtime_config.py tests/test_phase3_evidence_automation.py -q --tb=short
```

## Next Action

- Observe the next live Render ping / GitHub workflow dispatch after push to prove external scheduler execution.
