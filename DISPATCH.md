# DISPATCH.md

## Active

- task_md_holds: `future_watch_source_and_card_denoise_20260610`
- status: `complete`
- owner_request:
  - Analyze the pasted v21.0.1 report.
  - Fix source/fundamental/card noise issues where clear.
  - No live Telegram delivery.

## Current Result

- Version bumped to `v21.0.2`.
- TWSE historical source now retries transient failures and fails closed with a clearer source-error line.
- TWSE listed monthly revenue OpenAPI is loaded, fixing EPS-only listed stock rows when source data is available.
- Compact `等接近` cards remove low-signal repeated rows while staying non-actionable.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
```

Result: `206 passed, 145 warnings, 44 subtests passed`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_market_theme_evidence.py tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_volume_calibration.py tests/test_market_theme_evidence.py -q --tb=short
```

Result: `94 passed, 1 warning, 13 subtests passed`.

Official dry-run returned `messages 4`; checked `v21.0.2`, compact unheld card, historical source line, and 2303/2301 2026/05 revenue. No live Telegram delivery.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n--- MESSAGE ---\n'.join(messages))"
```

## Next Action

- Owner review of v21.0.2 output.
