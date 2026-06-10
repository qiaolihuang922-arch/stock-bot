# DISPATCH.md

## Active

- task_md_holds: `setup_aware_volume_fsm_20260610`
- status: `complete`
- owner_request:
  - Global code scan and best fix for volume handling, trade state machine usefulness, and far-distance buyable contexts.
  - Use DB history where possible.
  - No live Telegram delivery.

## Current Result

- Version remains `v21.0`.
- Unheld state is now gate-specific: `等市場`, `等型態`, `等量能`, `等回測`, `等RR修復`, `等冷卻`.
- Low volume is primary only for breakout / pre-breakout contexts; far weak-market names no longer become volume-only waits.
- Current official dry-run unheld summary: `未持倉 7｜僅追蹤 7（等市場）`.
- Added read-only volume calibration artifact from `daily_signal_snapshot + daily_price`; no DB write or schema change.

## Recently Done

- `setup_aware_volume_fsm_20260610`: setup-aware volume gate, market/setup state split, read-only volume calibration artifact.
- `revenue_fallback_no_downgrade_20260610`: fixed stale revenue downgrade and amount-as-YoY errors.
- `report_revenue_noise_fsm_20260610`: MOPS revenue freshness fallback, closing-card denoise, and unheld FSM visible-line improvement.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_volume_calibration.py -q --tb=short
```

Result: `258 passed, 145 warnings, 44 subtests passed`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print('messages',len(messages)); print('\n--- MESSAGE ---\n'.join(messages))"
```

Result: `messages 4`; no live Telegram delivery.

Read-only DB calibration result:

- `source=daily_signal_snapshot+daily_price`
- `db_write=false`
- `schema_change=false`
- `source_status=available`
- contexts: `near_breakout`, `pullback`, `far_weak_market`, `far_no_breakout_setup`

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n--- MESSAGE ---\n'.join(messages))"
```

## Next Action

- Commit/push current patch and run git completion check.
