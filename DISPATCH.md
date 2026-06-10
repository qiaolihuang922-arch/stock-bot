# DISPATCH.md

## Active

- task_md_holds: `report_state_denoise_followup_20260610`
- status: `complete`
- owner_request:
  - Analyze and fix the remaining v21.0.1 report problems.
  - Optimize where reasonable.
  - No live Telegram delivery.

## Current Result

- Unheld far-from-trigger symbols now render as `等接近`, not generic `等型態`.
- `買點`, title, state line, gap, unlock, trigger, and summary bucket are aligned.
- Distance gate now says the `<=4%` rule is for breakout strategy; other setups need separate evidence.
- TWSE historical analogy below 60% is downgraded to `低相似，不作主結論`.
- Fundamentals block has blank line between stocks.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
```

Result: `203 passed, 145 warnings, 44 subtests passed`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_volume_calibration.py tests/test_market_theme_evidence.py -q --tb=short
```

Result: `94 passed, 1 warning, 13 subtests passed`.

Official dry-run returned `messages 4` and confirmed the visible report route; no live Telegram delivery.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n--- MESSAGE ---\n'.join(messages))"
```

## Next Action

- Owner review of v21.0.1 report/state denoise output.
