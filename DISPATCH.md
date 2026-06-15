# DISPATCH.md

## Active

- task_md_holds: `premarket_phase_report_v21_0_6_20260615`
- status: `complete`
- owner_request:
  - Analyze pasted `06/15 非交易｜v21.0.5` report.
  - Resolve visible conflict where a trading-day report mixed non-trading, today, and tomorrow wording.
  - No live Telegram delivery.

## Current Result

- Visible version is now `v21.0.6`.
- Trading weekday before 09:00 now renders as `盤前`, not `非交易`.
- `盤前` is treated as a today-action phase for summary routing.
- `盤前` does not append `明日計畫`.
- Existing `盤中` wording remains unchanged.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py -q --tb=short
```

Result: `248 passed, 147 warnings, 57 subtests passed`.

Official patched-time dry-run:
- simulated time: `2026-06-15 08:00` Taipei.
- headers: `【06/15 盤前｜v21.0.6】`.
- phase: `盤前`.
- no `06/15 非交易`.
- no `明日計畫`.

## Next Action

- Observe the next Render/GitHub scheduled report if external confirmation is needed.
