# DISPATCH.md

## Active

- task_md_holds: `report_revenue_noise_fsm_20260610`
- status: `complete`
- owner_request:
  - Check why May revenue is missing from the v21.0 report.
  - Reasonably reduce Telegram report noise.
  - Make the v21 unheld trade state machine useful.
  - No live Telegram delivery.

## Current Result

- Version remains `v21.0`.
- TWSE/TPEX bulk OpenAPI revenue was found stale at ROC `11504`; MOPS company monthly revenue fallback now refreshes stale target rows to ROC `11505` when available.
- MOPS fallback was further optimized after slow dry-run: it skips the slow/stale TWSE listed-revenue bulk endpoint, uses 3-second MOPS target fetches with limited concurrency, and runs a 2-second small retry for missed priority rows.
- Closing/after-hours unheld cards no longer show cross-day history noise like `歷史：前次 observe｜連續觀察 1 天`.
- Unheld FSM line now shows missing confirmation event, e.g. `還差：量能確認` or `還差：回測確認`.
- Official dry-run generated 4 messages in about 55-59 seconds and did not run live Telegram delivery.
- Latest dry-run refreshed May revenue for all holding names; a few candidate rows may show EPS only if MOPS times out.
- Commit `182d26d` pushed to `origin/main`; equivalent git completion check passed (`HEAD == origin/main`).
- WSL shell gate could not run because local WSL reports `HCS_E_HYPERV_NOT_INSTALLED`; PowerShell git checks were used as the equivalent gate.

## Recently Done

- `report_revenue_noise_fsm_20260610`: MOPS revenue freshness fallback, closing-card denoise, and unheld FSM visible-line improvement.
- `render_git_tg_db_pipeline_check_20260609`: Render dispatch fixed, daily evidence workflow unblocked, market-theme DB freshness backfilled/verified, dry-run and guard tests passed, no live Telegram delivery.
- `unheld_transition_table_replay_20260608`: v21.0 unheld transition-table FSM implemented, replayed locally, regression-tested, dry-run verified, no live Telegram delivery.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
```

Result: `198 passed, 145 warnings, 44 subtests passed`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print(len(messages)); print('歷史噪音', '歷史：前次 observe' in '\\n'.join(messages) or '連續觀察 1 天' in '\\n'.join(messages))"
```

Result: `4`, `歷史噪音 False`.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n--- MESSAGE ---\\n'.join(messages))"
```

## Next Action

- Owner review of v21.0 report freshness/noise/FSM patch.
