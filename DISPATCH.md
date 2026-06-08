# DISPATCH.md

## Active

- task_md_holds: `trade_state_machine_v21_20260608`
- status: `conditional_pass`
- owner_request:
  - 版本號 `21.0`。
  - 開始做交易狀態機。
  - 不先擴 DB 欄位。

## Current Result

- Version implemented: `v21.0`.
- Added read-only `core/trade_state_machine.py`.
- Official TG cards now show `交易狀態`:
  - holding example: `交易狀態：停損｜動作：停損｜觸發：清出後等重新買點`。
  - unheld example: `交易狀態：等量能｜動作：等待｜觸發：量能回升且重新接近買點`。
- State machine artifact is read-only: no DB write, no schema change.
- No live Telegram delivery was run.

## Verification

- `py_compile` passed。
- `tests/test_trade_state_machine.py` passed: 4 passed。
- focused generator/state-machine replay passed: 7 passed。
- market theme tests passed: 38 passed, 13 subtests passed。
- official `generate_report(dry_run=True)` passed with v21.0 messages。
- Full generator regression is conditional, not clean: 160 passed / 39 failed due legacy exact-message assertions and v21 visible-state insertion.

## Fixed Commands

Local dry-run only, no live Telegram:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```
