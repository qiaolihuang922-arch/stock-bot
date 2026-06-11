# DISPATCH.md

## Active

- task_md_holds: `report_noise_conflict_v21_0_3_20260611`
- status: `complete`
- owner_request:
  - Analyze the pasted `06/11` intraday report.
  - Fix visible conflicts and unnecessary noise.
  - Keep no live Telegram delivery.

## Current Result

- Visible version is now `v21.0.3`.
- Intraday summary no longer says `今日盤中交易執行`; it says `今日盤中風控建議`.
- Detail index now uses `風控建議 N`.
- Stop-loss / reduce / profit direct-action holding cards suppress low-signal `條件` and `數據` lines.
- Unheld data-wait handling is narrow:
  - `等資料` is used only when the state machine already says data recovery is the blocker.
  - Normal states such as `等接近`, `等回測`, `等量能`, `隔日確認` are preserved.
- Historical analogy now states medium confidence when volume data is unavailable.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_market_theme_evidence.py -q --tb=short
```

Result: `244 passed, 145 warnings, 57 subtests passed`.

Official dry-run:

```powershell
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```

Checked:
- `v21.0.3` present.
- `今日盤中風控建議` present.
- old `今日盤中交易執行` absent.
- historical confidence note present.

## Next Action

- After push, observe the next Render/GitHub report run if Owner wants live external confirmation.
