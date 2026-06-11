# DISPATCH.md

## Active

- task_md_holds: `entry_distance_strategy_v21_0_4_20260611`
- status: `complete`
- owner_request:
  - Research why every distance-to-breakout gate is `<=4%`.
  - Fix the lack of strategy separation.
  - Keep no live Telegram delivery.

## Current Result

- Visible version is now `v21.0.4`.
- Breakout/pivot distance gate is strategy-specific and uses `<=5%`.
- Pullback reclaim and trend continuation no longer fail solely because breakout distance is above the pivot buy zone.
- Far stocks without a valid setup still wait for approach/setup.
- Telegram gap wording no longer says `突破策略需<=4%`.
- Rejected/source-failed cards no longer show a conflicting data-wait trade-state line.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_market_theme_evidence.py -q --tb=short
```

Result: `246 passed, 145 warnings, 57 subtests passed`.

Official dry-run check:

```powershell
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```

Checked:
- `v21.0.4` present.
- old `需<=4%` / `突破策略需<=4%` absent.
- old `今日盤中交易執行` absent.
- no rejected/data-state conflict in unheld cards.

## Next Action

- After push, observe the next Render/GitHub report run if Owner wants live external confirmation.
