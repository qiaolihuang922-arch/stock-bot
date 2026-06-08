# DISPATCH.md

## Active

- task_md_holds: `unheld_volume_tracking_reclassification_20260608`
- status: `qa_passed`
- owner_request:
  - v20.4.54 未持倉 `量能不足` 不應全部打成 `淘汰`。
  - 上網查突破/量能確認口徑後修改。
  - 不做 live Telegram delivery。

## Current Result

- Version implemented: `v20.4.55`.
- 未持倉重分類：
  - `量能不足` 且非結構性失敗 -> `等量能`。
  - 遠離突破且量能不足 -> 觸發 `量能回升且重新接近買點`。
  - 弱反彈、突破失敗、派發、明確 FAIL -> 仍 `淘汰`。
- Official dry-run replay:
  - `未持倉 7｜僅追蹤 7（等回測1/等量能6）`。
  - no `淘汰 7`。
- No live Telegram delivery was run.

## Verification

- focused pytest passed: 3 passed。
- broader focused pytest passed: 9 passed。
- `py_compile` passed。
- market theme tests passed: 38 passed, 13 subtests passed。
- official `generate_report(dry_run=True)` passed with 4 local preview messages。

## Fixed Commands

Local dry-run only, no live Telegram:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```
