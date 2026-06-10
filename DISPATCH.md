# DISPATCH.md

## Active

- task_md_holds: `unheld_market_overlay_version_20260610`
- status: `complete`
- owner_request:
  - Analyze why the v21 report still looked wrong.
  - Bump visible version to `v21.0.1`.
  - No live Telegram delivery.

## Current Result

- Version is now `v21.0.1`.
- Root cause: `市場弱` short-circuited unheld card state before stock-specific gates.
- Fix: market weakness stays as blocker/background, while card primary state shows stock-specific gate such as `等型態`.
- Current official dry-run unheld summary: `未持倉 7｜僅追蹤 7（等型態）`.
- No DB schema/write/live Telegram behavior changed.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v21_0_1_far_low_volume_weak_market_waits_setup_not_market_or_volume tests/test_trade_state_machine.py::TradeStateMachineTest::test_report_cards_include_trade_state_line -q --tb=short
```

Result: `2 passed, 5 warnings`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_volume_calibration.py tests/test_market_theme_evidence.py -q --tb=short
```

Result: `296 passed, 145 warnings, 57 subtests passed`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print('messages',len(messages)); print('\n--- MESSAGE ---\n'.join(messages))"
```

Result: `messages 4`; headers show `v21.0.1`; no live Telegram delivery.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n--- MESSAGE ---\n'.join(messages))"
```

## Next Action

- Owner review of `v21.0.1` report output.
